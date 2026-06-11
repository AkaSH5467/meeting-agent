import json
import logging
import uuid
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.genai import types as genai_types

from agent.agents.news_agent import news_agent
from agent.agents.tech_agent import tech_agent
from agent.agents.pain_point_agent import pain_point_agent
from agent.agents.synthesis_agent import synthesis_agent
from agent.prompts import ORCHESTRATOR_PROMPT
from app.models import BriefOutput

logger = logging.getLogger(__name__)


def _make_agent_tool(agent):
    try:
        from google.adk.agents import AgentTool
        return AgentTool(agent)
    except ImportError:
        pass
    try:
        from google.adk.tools import AgentTool
        return AgentTool(agent)
    except ImportError:
        pass
    try:
        from google.adk.tools.agent_tool import AgentTool
        return AgentTool(agent)
    except ImportError:
        pass
    raise ImportError("AgentTool not found in google.adk")


root_agent = LlmAgent(
    name="orchestrator",
    model="gemini-2.5-flash",
    instruction=ORCHESTRATOR_PROMPT,
    tools=[
        _make_agent_tool(news_agent),
        _make_agent_tool(tech_agent),
        _make_agent_tool(pain_point_agent),
        _make_agent_tool(synthesis_agent),
    ],
)


async def run_research(
    company_name: str,
    domain: str,
    meeting_title: str,
    attendees: list,
) -> Optional[BriefOutput]:
    try:
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="meeting_intel",
            session_service=session_service,
        )

        session_id = f"research_{domain}_{uuid.uuid4().hex}"
        user_id = "system"

        await session_service.create_session(
            app_name="meeting_intel",
            user_id=user_id,
            session_id=session_id,
        )

        user_message = (
            f"Research {company_name} ({domain}) for meeting: {meeting_title}. "
            f"Attendees: {', '.join(attendees)}"
        )

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=user_message)],
        )

        final_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.is_final_response() and event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text
                break

        if not final_text:
            logger.error(f"No response from orchestrator for {domain}")
            return None

        return _parse_brief(final_text, company_name, domain)

    except Exception as e:
        logger.error(f"run_research failed for {company_name} ({domain}): {e}")
        return None


def _sanitize_tech_signals(ts: dict) -> dict:
    """Ensure all tech_signals fields are correct types — Gemini sometimes returns null."""
    return {
        "frontend":    ts.get("frontend") or [],
        "backend":     ts.get("backend") or [],
        "infra":       ts.get("infra") or [],
        "data_tools":  ts.get("data_tools") or [],
        "oss_activity": ts.get("oss_activity") or "",
    }


def _parse_brief(raw: str, company_name: str, domain: str) -> Optional[BriefOutput]:
    text = raw.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        logger.error(f"No JSON in agent response for {domain}. Raw: {raw[:300]}")
        return None

    try:
        data = json.loads(text[start:end])

        # Sanitize fields that Gemini occasionally returns as null instead of correct type
        data.setdefault("company_name", company_name)
        data.setdefault("domain", domain)
        data.setdefault("what_they_do", "No description available.")
        data.setdefault("confidence", "low")
        data.setdefault("pain_points", [])
        data.setdefault("talking_points", [])
        data.setdefault("recent_news", [])
        data.setdefault("data_gaps", [])

        # Fix tech_signals — normalize nulls to correct empty types
        raw_ts = data.get("tech_signals", {}) or {}
        data["tech_signals"] = _sanitize_tech_signals(raw_ts)

        # Fix any other nullable list/string fields
        if not isinstance(data.get("pain_points"), list):
            data["pain_points"] = []
        if not isinstance(data.get("recent_news"), list):
            data["recent_news"] = []
        if not isinstance(data.get("talking_points"), list):
            data["talking_points"] = []
        if not isinstance(data.get("data_gaps"), list):
            data["data_gaps"] = []

        return BriefOutput(**data)

    except Exception as e:
        logger.error(f"Failed to parse BriefOutput for {domain}: {e}")
        return None