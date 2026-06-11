import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
if not os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

from app.database import create_tables, get_session, ping_db, close_connector
from app.models import Meeting, Brief, MeetingBriefStatus, BriefStatus
from app.websocket_manager import ws_manager
from app.calendar_listener import start_calendar_listener, stop_calendar_listener
from agent.orchestrator import run_research   # FIXED import path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    await create_tables()
    db_ok = await ping_db()
    logger.info(f"Database connection: {'ok' if db_ok else 'failed'}")
    await start_calendar_listener()
    yield
    logger.info("Application shutting down")
    await stop_calendar_listener()
    await close_connector()


app = FastAPI(title="Meeting Intel Agent", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    db_ok = await ping_db()
    return {"status": "ok", "db": "ok" if db_ok else "error"}


@app.get("/meetings")
async def list_meetings():
    async for session in get_session():
        result = await session.execute(select(Meeting).order_by(Meeting.start_time))
        meetings = result.scalars().all()
        return [
            {
                "id": m.id,
                "title": m.title,
                "start_time": m.start_time.isoformat(),
                "end_time": m.end_time.isoformat(),
                "attendees": m.attendees,
                "company_name": m.company_name,
                "domain": m.domain,
                "brief_status": m.brief_status.value,
                "created_at": m.created_at.isoformat(),
            }
            for m in meetings
        ]


@app.get("/meetings/{meeting_id}")
async def get_meeting(meeting_id: str):
    async for session in get_session():
        meeting = await session.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        return {
            "id": meeting.id,
            "title": meeting.title,
            "start_time": meeting.start_time.isoformat(),
            "end_time": meeting.end_time.isoformat(),
            "attendees": meeting.attendees,
            "company_name": meeting.company_name,
            "domain": meeting.domain,
            "brief_status": meeting.brief_status.value,
            "created_at": meeting.created_at.isoformat(),
        }


@app.get("/meetings/{meeting_id}/brief")
async def get_brief(meeting_id: str):
    async for session in get_session():
        result = await session.execute(select(Brief).where(Brief.meeting_id == meeting_id))
        brief = result.scalars().first()
        if not brief:
            raise HTTPException(status_code=404, detail="Brief not found")
        return {
            "id": brief.id,
            "meeting_id": brief.meeting_id,
            "data": brief.data,
            "confidence": brief.confidence,
            "created_at": brief.created_at.isoformat(),
        }


@app.post("/research/{meeting_id}")
async def trigger_research(meeting_id: str):
    async for session in get_session():
        meeting = await session.get(Meeting, meeting_id)
        if not meeting:
            raise HTTPException(status_code=404, detail="Meeting not found")
        if not meeting.company_name or not meeting.domain:
            raise HTTPException(status_code=400, detail="No company associated with this meeting")
        asyncio.create_task(_research_and_broadcast(
            meeting.id, meeting.company_name, meeting.domain,
            meeting.title, meeting.attendees,
        ))
        return {"status": "research_started", "meeting_id": meeting_id}


async def _research_and_broadcast(meeting_id: str, company_name: str, domain: str, meeting_title: str, attendees: list):
    try:
        await ws_manager.broadcast(MeetingBriefStatus(
            meeting_id=meeting_id, status=BriefStatus.pending,
            brief=None, error_message=None,
        ).model_dump_json())

        brief = await run_research(company_name, domain, meeting_title, attendees)

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
                await ws_manager.broadcast(MeetingBriefStatus(
                    meeting_id=meeting_id, status=BriefStatus.done,
                    brief=brief, error_message=None,
                ).model_dump_json())
            else:
                meeting = await session.get(Meeting, meeting_id)
                if meeting:
                    meeting.brief_status = BriefStatus.error
                    meeting.updated_at = datetime.utcnow()
                await session.commit()
                await ws_manager.broadcast(MeetingBriefStatus(
                    meeting_id=meeting_id, status=BriefStatus.error,
                    brief=None, error_message="Research failed",
                ).model_dump_json())

    except Exception as e:
        logger.error(f"_research_and_broadcast failed: {e}")
        await ws_manager.broadcast(MeetingBriefStatus(
            meeting_id=meeting_id, status=BriefStatus.error,
            brief=None, error_message=str(e),
        ).model_dump_json())


@app.websocket("/ws/meetings")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)