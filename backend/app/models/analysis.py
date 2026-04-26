import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel
from sqlalchemy import Column, Text, DateTime, JSON, Boolean, BigInteger, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


# ─────────────────────────────────────────────────────────────────────────────
# SQLAlchemy ORM models
# ─────────────────────────────────────────────────────────────────────────────

class AnalysisRecord(Base):
    """Persisted analysis result in PostgreSQL."""

    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    resume_text = Column(Text, nullable=False)
    jd_text = Column(Text, nullable=False)
    score_json = Column(JSON, nullable=False)
    sections_json = Column(JSON, nullable=False)
    skill_gaps_json = Column(JSON, nullable=False)


class UserAlert(Base):
    """Telegram user alert subscription."""

    __tablename__ = "user_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False, unique=True)
    analysis_id = Column(UUID(as_uuid=True), nullable=False)
    alert_enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)


class SentJob(Base):
    """Tracks jobs already sent to a user to prevent duplicates."""

    __tablename__ = "sent_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, nullable=False)
    job_url = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("chat_id", "job_url", name="uq_sent_jobs_chat_url"),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic response models
# ─────────────────────────────────────────────────────────────────────────────

class ScoreBreakdown(BaseModel):
    semantic: float
    keyword: float
    skill_bonus: float = 0.0
    format_penalty: float
    content_score: float = 0.0
    final: float


class SectionScores(BaseModel):
    skills: float
    experience: float
    projects: Optional[float] = None
    education: float
    summary: Optional[float] = None


class SuggestedContent(BaseModel):
    """A single ready-to-paste content suggestion for one resume section."""
    section: str        # "Skills", "Experience", "Projects", "New Projects Section"
    label: str          # e.g. "Add to Skills section"
    content: str        # The exact text to paste
    content_type: Literal["bullet", "skill_keyword", "summary_sentence"] = "bullet"


class Recommendation(BaseModel):
    priority: str       # "critical" | "high" | "medium" | "low"
    category: str       # e.g. "keyword_alignment", "semantic_alignment", etc.
    title: str          # short headline
    description: str    # actionable detail
    impact: str         # estimated score improvement description
    suggested_content: list[SuggestedContent] = []  # ready-to-paste fix


class RecommendationSummary(BaseModel):
    critical: int
    high: int
    medium: int
    low: int
    total: int


class ExperienceInfo(BaseModel):
    total_years: float
    level: str              # "intern" | "junior" | "mid" | "senior" | "staff"
    titles: list[str] = []
    level_confidence: float


class AnalysisResponse(BaseModel):
    analysis_id: str

    scores: ScoreBreakdown

    sections_found: list[str]
    sections_missing: list[str]

    section_scores: SectionScores

    skill_gaps: list[str]
    format_issues: list[str]
    quality_issues: list[str]
    jd_alignment_warning: Optional[str] = None

    recommendations: list[Recommendation] = []
    recommendation_summary: Optional[RecommendationSummary] = None

    experience: Optional[ExperienceInfo] = None
    resume_text: Optional[str] = None  # included for job-search agent context


