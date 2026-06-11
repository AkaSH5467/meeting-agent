from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


class BriefStatus(str, Enum):
    pending = "pending"
    done = "done"
    no_company = "no_company"
    error = "error"


class Meeting(SQLModel, table=True):
    __tablename__ = "meetings"

    id: str = Field(primary_key=True)
    title: str
    start_time: datetime
    end_time: datetime
    attendees: List[str] = Field(default_factory=list, sa_column=Column(JSONB))
    company_name: Optional[str] = None
    domain: Optional[str] = None
    brief_status: BriefStatus = Field(default=BriefStatus.pending)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Brief(SQLModel, table=True):
    __tablename__ = "briefs"

    id: Optional[int] = Field(default=None, primary_key=True)
    meeting_id: str = Field(foreign_key="meetings.id", index=True)
    data: dict = Field(sa_column=Column(JSONB))
    confidence: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RecentNews(BaseModel):
    headline: str
    date: Optional[str] = None
    source: Optional[str] = None


class TechSignals(BaseModel):
    frontend: List[str] = Field(default_factory=list)
    backend: List[str] = Field(default_factory=list)
    infra: List[str] = Field(default_factory=list)
    data_tools: List[str] = Field(default_factory=list)
    oss_activity: str = ""


class TalkingPoint(BaseModel):
    point: str
    rationale: Optional[str] = None


class BriefOutput(BaseModel):
    company_name: str
    domain: str
    what_they_do: str
    company_stage: Optional[str] = None
    founded: Optional[str] = None
    headcount_range: Optional[str] = None
    recent_news: List[RecentNews] = Field(default_factory=list)
    funding: Optional[str] = None
    tech_signals: TechSignals = Field(default_factory=TechSignals)
    pain_points: List[str] = Field(default_factory=list)
    talking_points: List[TalkingPoint] = Field(default_factory=list)
    confidence: str
    data_gaps: List[str] = Field(default_factory=list)


class MeetingBriefStatus(BaseModel):
    meeting_id: str
    status: BriefStatus
    brief: Optional[BriefOutput] = None
    error_message: Optional[str] = None