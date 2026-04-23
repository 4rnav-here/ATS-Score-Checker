import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.job_search_agent import run_job_search
from app.core.database import get_db
from app.core.logger import logger
from app.models.analysis import AnalysisRecord

router = APIRouter()


class JobSearchRequest(BaseModel):
    analysis_id: str
    max_days_old: int = 3


class JobSearchResponse(BaseModel):
    analysis_id: str
    jobs: list[dict]
    total: int


@router.post("/jobs/search", response_model=JobSearchResponse, summary="Search for jobs matching an analysis")
async def search_jobs(
    request: JobSearchRequest,
    db: AsyncSession = Depends(get_db),
) -> JobSearchResponse:
    """
    Run the job search agent for a given analysis_id.

    Fetches the stored analysis result from PostgreSQL, then runs
    experience-aware job search across Adzuna + Remotive, scores
    each job against the resume, and returns ranked results.
    """
    from sqlalchemy import select

    # Fetch the analysis record
    stmt = select(AnalysisRecord).where(
        AnalysisRecord.id == request.analysis_id
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    # Build the analysis dict the agent expects
    analysis_data = {
        "resume_text": record.resume_text,
        "jd_text": record.jd_text,
        "skill_gaps": record.skill_gaps_json.get("gaps", []),
        "experience": record.score_json.get("experience", {"level": "mid"}),
    }

    logger.info(f"Job search requested for analysis_id={request.analysis_id}")

    try:
        jobs = await run_job_search(analysis_data, max_days_old=request.max_days_old)
    except Exception as e:
        logger.error(f"Job search failed: {e}")
        raise HTTPException(status_code=500, detail="Job search failed. Try again.")

    return JobSearchResponse(
        analysis_id=request.analysis_id,
        jobs=jobs,
        total=len(jobs),
    )
