"""
Feedback API — generates AI improvement recommendations from a stored analysis.

Called by the Telegram bot /feedback command.
Supports two modes:
    1. analysis_id only → looks up stored analysis from DB
    2. Full data payload → uses provided scores/gaps directly (for external callers)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.analysis import AnalysisRecord
from app.services import recommendation_service

router = APIRouter()


class FeedbackRequest(BaseModel):
    """Input for recommendation generation — accepts analysis_id OR full data."""
    analysis_id: Optional[str] = None

    # Optional: provide data directly (used by external callers)
    scores: Optional[dict] = None
    section_scores: Optional[dict] = None
    skill_gaps: Optional[list[str]] = None
    format_issues: Optional[list[str]] = None
    quality_issues: Optional[list[str]] = None
    sections_found: Optional[list[str]] = None
    sections_missing: Optional[list[str]] = None


class FeedbackResponse(BaseModel):
    recommendations: list[dict]
    summary: dict


@router.post("/feedback", response_model=FeedbackResponse, summary="Generate improvement recommendations")
async def generate_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackResponse:
    """
    Generate prioritized, actionable recommendations.

    If analysis_id is provided, fetches stored analysis from DB.
    Otherwise, uses the provided data directly.
    """
    # ── Mode 1: Lookup from DB by analysis_id ─────────────────────────────────
    if request.analysis_id:
        stmt = select(AnalysisRecord).where(
            AnalysisRecord.id == request.analysis_id
        )
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise HTTPException(status_code=404, detail="Analysis not found.")

        score_data = record.score_json or {}
        sections_data = record.sections_json or {}
        gaps_data = record.skill_gaps_json or {}

        scores = {
            "semantic": score_data.get("semantic", 0),
            "keyword": score_data.get("keyword", 0),
            "format_penalty": score_data.get("format_penalty", 0),
            "final": score_data.get("final", 0),
        }
        section_scores = sections_data.get("section_scores", {})
        skill_gaps = gaps_data.get("gaps", [])
        format_issues = sections_data.get("format_issues", [])
        quality_issues = sections_data.get("quality_issues", [])
        sections_found = sections_data.get("found", [])
        sections_missing = sections_data.get("missing", [])

        logger.info(f"Generating feedback from analysis_id={request.analysis_id}")

    # ── Mode 2: Use provided data directly ────────────────────────────────────
    elif request.scores is not None:
        scores = request.scores
        section_scores = request.section_scores or {}
        skill_gaps = request.skill_gaps or []
        format_issues = request.format_issues or []
        quality_issues = request.quality_issues or []
        sections_found = request.sections_found or []
        sections_missing = request.sections_missing or []

        logger.info("Generating feedback from direct data payload")

    else:
        raise HTTPException(
            status_code=422,
            detail="Provide either 'analysis_id' or full analysis data (scores, section_scores, etc.)",
        )

    recs = recommendation_service.generate_recommendations(
        scores=scores,
        section_scores=section_scores,
        skill_gaps=skill_gaps,
        format_issues=format_issues,
        quality_issues=quality_issues,
        sections_found=sections_found,
        sections_missing=sections_missing,
    )
    summary = recommendation_service.summarize_recommendations(recs)

    return FeedbackResponse(recommendations=recs, summary=summary)
