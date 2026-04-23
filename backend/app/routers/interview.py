"""
Interview Questions API — generates interview prep questions from a stored analysis.

Called by the Telegram bot /interview command.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.analysis import AnalysisRecord
from app.services.interview_service import generate_interview_questions

router = APIRouter()


class InterviewRequest(BaseModel):
    analysis_id: str


class InterviewResponse(BaseModel):
    analysis_id: str
    questions: str


@router.post("/interview", response_model=InterviewResponse, summary="Generate interview questions from analysis")
async def generate_interview(
    request: InterviewRequest,
    db: AsyncSession = Depends(get_db),
) -> InterviewResponse:
    """
    Generate interview prep questions based on a stored analysis.

    Fetches the analysis record from PostgreSQL, extracts resume text,
    JD text, and skill gaps, then calls the LLM to generate targeted
    interview questions.
    """
    stmt = select(AnalysisRecord).where(
        AnalysisRecord.id == request.analysis_id
    )
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")

    skill_gaps = record.skill_gaps_json.get("gaps", [])

    logger.info(f"Generating interview questions for analysis_id={request.analysis_id}")

    try:
        questions = generate_interview_questions(
            resume_text=record.resume_text,
            jd_text=record.jd_text,
            skill_gaps=skill_gaps,
        )
    except Exception as e:
        logger.error(f"Interview generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate interview questions.")

    return InterviewResponse(
        analysis_id=request.analysis_id,
        questions=questions,
    )
