import json

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.agents.job_search_agent import run_job_search
from app.core.database import get_db
from app.core.logger import logger
from app.models.analysis import AnalysisRecord

router = APIRouter()


class JobSearchRequest(BaseModel):
    analysis_id: str
    max_days_old: int = 30
    cities: Optional[list[str]] = None   # e.g. ["Bangalore", "Hyderabad"]


class JobSearchResponse(BaseModel):
    analysis_id: str
    jobs: list[dict]
    total: int


@router.post("/jobs/search", response_model=JobSearchResponse, summary="Search for India-based jobs matching an analysis")
async def search_jobs(
    request: JobSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> JobSearchResponse:
    """
    Run the India-focused job search agent for a given analysis_id.

    Fetches the stored analysis result from PostgreSQL, then runs
    experience-aware job search across Adzuna India + LinkedIn India (JSearch),
    applies company-tier score boosts, and returns ranked results.

    Optional fields in request body:
        cities      — list of Indian cities to filter (default: all major hubs)
        max_days_old — recency filter (default: 30 days)
    """
    from sqlalchemy import select

    stmt = select(AnalysisRecord).where(
        AnalysisRecord.id == request.analysis_id
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    analysis_data = {
        "resume_text": record.resume_text,
        "jd_text": record.jd_text,
        "skill_gaps": record.skill_gaps_json.get("gaps", []),
        "experience": record.score_json.get("experience", {"level": "mid"}),
    }

    logger.info(
        f"Job search v2 requested — analysis_id={request.analysis_id}, "
        f"cities={request.cities}, max_days_old={request.max_days_old}"
    )

    try:
        jobs = await run_job_search(
            analysis_data,
            max_days_old=request.max_days_old,
            city_filter=request.cities or None,
        )
    except Exception as e:
        logger.error(f"Job search failed: {e}")
        raise HTTPException(status_code=500, detail="Job search failed. Try again.")

    return JobSearchResponse(
        analysis_id=request.analysis_id,
        jobs=jobs,
        total=len(jobs),
    )
