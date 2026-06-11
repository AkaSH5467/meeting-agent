import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

from app.database import get_session
from app.models import Meeting, Brief, BriefStatus
from app.parser import extract_company
from app.websocket_manager import ws_manager
from agent.orchestrator import run_research

logger = logging.getLogger(__name__)

POLL_INTERVAL = 60
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

_calendar_task: Optional[asyncio.Task] = None


def _to_naive_utc(dt: datetime) -> datetime:
    """Convert any datetime to naive UTC — required for TIMESTAMP WITHOUT TIME ZONE columns."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def get_google_credentials() -> Optional[Credentials]:
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    refresh_token = os.getenv("GOOGLE_REFRESH_TOKEN")

    logger.info(f"[CREDS] client_id={'SET' if client_id else 'MISSING'}, "
                f"client_secret={'SET' if client_secret else 'MISSING'}, "
                f"refresh_token={'SET' if refresh_token else 'MISSING'}")

    if not all([client_id, client_secret, refresh_token]):
        logger.error("[CREDS] Missing OAuth credentials — calendar listener cannot start")
        return None

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        client_id=client_id,
        client_secret=client_secret,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )

    logger.info("[CREDS] Refreshing access token...")
    try:
        creds.refresh(Request())
        logger.info(f"[CREDS] Token refreshed. Valid={creds.valid}, Expiry={creds.expiry}")
    except Exception as e:
        logger.error(f"[CREDS] Token refresh failed: {e}")
        return None

    return creds


async def fetch_events(service) -> list:
    now = datetime.now(timezone.utc).isoformat()
    week_later = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
    logger.info(f"[CALENDAR] Fetching events {now} → {week_later}")
    try:
        loop = asyncio.get_event_loop()
        events_result = await loop.run_in_executor(
            None,
            lambda: service.events().list(
                calendarId="primary",
                timeMin=now,
                timeMax=week_later,
                singleEvents=True,
                orderBy="startTime",
                maxResults=100,
            ).execute()
        )
        items = events_result.get("items", [])
        logger.info(f"[CALENDAR] Fetched {len(items)} events")
        for item in items:
            logger.info(f"[CALENDAR] '{item.get('summary')}' | "
                       f"Attendees: {[a.get('email') for a in item.get('attendees', [])]}")
        return items
    except Exception as e:
        logger.error(f"[CALENDAR] Fetch failed: {e}", exc_info=True)
        return []


async def save_meeting(session, event: dict, company_name, domain, status: BriefStatus) -> Meeting:
    start = event["start"].get("dateTime", event["start"].get("date"))
    end = event["end"].get("dateTime", event["end"].get("date"))

    # Parse and convert to naive UTC — DB column is TIMESTAMP WITHOUT TIME ZONE
    start_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) if isinstance(start, str) else start
    end_dt = datetime.fromisoformat(end.replace("Z", "+00:00")) if isinstance(end, str) else end
    start_dt = _to_naive_utc(start_dt)
    end_dt = _to_naive_utc(end_dt)

    attendees = []
    for a in event.get("attendees", []):
        if isinstance(a, dict):
            attendees.append(a.get("email", ""))
        else:
            attendees.append(str(a))

    meeting = Meeting(
        id=event["id"],
        title=event.get("summary", "Untitled Meeting"),
        start_time=start_dt,
        end_time=end_dt,
        attendees=attendees,
        company_name=company_name,
        domain=domain,
        brief_status=status,
    )
    session.add(meeting)
    await session.flush()
    logger.info(f"[DB] Saved '{meeting.title}' status={status.value} "
               f"start={start_dt} company={company_name}")
    return meeting


async def research_and_broadcast(
    meeting_id: str,
    company_name: str,
    domain: str,
    meeting_title: str,
    attendees: list,
):
    logger.info(f"[RESEARCH] Starting for {company_name} ({domain})")
    try:
        await ws_manager.broadcast(json.dumps({
            "meeting_id": meeting_id,
            "status": "pending",
            "brief": None,
            "error_message": None,
        }))

        brief = await run_research(company_name, domain, meeting_title, attendees)
        logger.info(f"[RESEARCH] Result: {'BriefOutput received' if brief else 'None returned'}")

        async for session in get_session():
            if brief:
                brief_record = Brief(
                    meeting_id=meeting_id,
                    data=brief.model_dump(),
                    confidence=brief.confidence,
                )
                session.add(brief_record)
                meeting = await session.get(Meeting, meeting_id)
                if meeting:
                    meeting.brief_status = BriefStatus.done
                    meeting.updated_at = datetime.utcnow()
                await session.commit()
                logger.info(f"[RESEARCH] Brief saved for {meeting_id}")
                await ws_manager.broadcast(json.dumps({
                    "meeting_id": meeting_id,
                    "status": "done",
                    "brief": brief.model_dump(),
                    "error_message": None,
                }))
            else:
                logger.error(f"[RESEARCH] Agent returned None for {company_name}")
                meeting = await session.get(Meeting, meeting_id)
                if meeting:
                    meeting.brief_status = BriefStatus.error
                    meeting.updated_at = datetime.utcnow()
                await session.commit()
                await ws_manager.broadcast(json.dumps({
                    "meeting_id": meeting_id,
                    "status": "error",
                    "brief": None,
                    "error_message": "Research failed to produce results",
                }))

    except Exception as e:
        logger.error(f"[RESEARCH] Failed for {company_name}: {e}", exc_info=True)
        try:
            async for session in get_session():
                meeting = await session.get(Meeting, meeting_id)
                if meeting:
                    meeting.brief_status = BriefStatus.error
                    meeting.updated_at = datetime.utcnow()
                await session.commit()
        except Exception as db_err:
            logger.error(f"[RESEARCH] DB update failed: {db_err}")
        await ws_manager.broadcast(json.dumps({
            "meeting_id": meeting_id,
            "status": "error",
            "brief": None,
            "error_message": str(e),
        }))


async def calendar_poll_loop():
    logger.info("[POLL] Starting calendar poll loop")
    loop = asyncio.get_event_loop()
    creds = await loop.run_in_executor(None, get_google_credentials)
    if not creds:
        logger.error("[POLL] Cannot start — credentials invalid")
        return

    service = await loop.run_in_executor(None, lambda: build("calendar", "v3", credentials=creds))
    logger.info("[POLL] Calendar service ready")

    poll_count = 0
    while True:
        poll_count += 1
        logger.info(f"[POLL] #{poll_count} starting...")
        try:
            events = await fetch_events(service)
            async for session in get_session():
                new_count = 0
                skip_count = 0
                for event in events:
                    existing = await session.get(Meeting, event.get("id", ""))
                    if existing:
                        skip_count += 1
                        continue

                    company_info = extract_company(event)
                    logger.info(f"[POLL] '{event.get('summary')}' → {company_info}")

                    if company_info:
                        company_name, domain = company_info
                        meeting = await save_meeting(
                            session, event, company_name, domain, BriefStatus.pending
                        )
                        await session.commit()
                        new_count += 1
                        asyncio.create_task(research_and_broadcast(
                            meeting.id, company_name, domain,
                            meeting.title, meeting.attendees,
                        ))
                    else:
                        await save_meeting(session, event, None, None, BriefStatus.no_company)
                        await session.commit()
                        new_count += 1

                logger.info(f"[POLL] #{poll_count} done — new={new_count}, skipped={skip_count}")

        except Exception as e:
            logger.error(f"[POLL] #{poll_count} error: {e}", exc_info=True)

        logger.info(f"[POLL] Sleeping {POLL_INTERVAL}s...")
        await asyncio.sleep(POLL_INTERVAL)


async def start_calendar_listener():
    global _calendar_task
    _calendar_task = asyncio.create_task(calendar_poll_loop())
    logger.info("Calendar listener started")


async def stop_calendar_listener():
    global _calendar_task
    if _calendar_task:
        _calendar_task.cancel()
        try:
            await _calendar_task
        except asyncio.CancelledError:
            pass
        logger.info("Calendar listener stopped")