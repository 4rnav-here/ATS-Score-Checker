import io
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.logger import logger
from app.models.analysis import (
    AnalysisRecord,
    AnalysisResponse,
    ExperienceInfo,
    Recommendation,
    RecommendationSummary,
    ScoreBreakdown,
    SectionScores,
    SuggestedContent,
)
from app.services import (
    embedding_service,
    experience_service,
    improvement_service,
    nlp_service,
    pdf_service,
    recommendation_service,
    scoring_service,
)

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse, summary="Analyze a resume against a job description")
async def analyze_resume(
    file: UploadFile = File(..., description="Resume PDF file"),
    jd_text: str = Form(..., description="Job description text"),
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """
    Full ATS analysis pipeline:

    1. Validate inputs
    2. Extract PDF text + layout metadata
    3. Parse resume into sections
    4. Extract & normalize keywords
    5. Generate per-section embeddings
    6. Compute semantic score (section-weighted) + TF-IDF keyword score
    7. Apply format penalty
    8. Detect quality issues & missing sections
    9. Persist result to PostgreSQL
    10. Return structured AnalysisResponse
    """

    # ── 1. Validate ───────────────────────────────────────────────────────────
    if len(jd_text.split()) < 20:
        raise HTTPException(
            status_code=422,
            detail="Job description is too short (minimum 20 words).",
        )

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF files are accepted.")

    # ── 2. Read PDF ───────────────────────────────────────────────────────────
    pdf_bytes = await file.read()
    pdf_io = io.BytesIO(pdf_bytes)

    resume_text = pdf_service.extract_text(pdf_io)
    if not resume_text.strip():
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from the PDF. Ensure it is not scanned/image-only.",
        )

    pdf_io.seek(0)
    layout_metadata = pdf_service.extract_layout_metadata(pdf_io)

    logger.info(f"PDF extracted: {len(resume_text)} chars, layout={layout_metadata}")

    # ── 3. Section parsing ────────────────────────────────────────────────────
    sections = nlp_service.parse_sections(resume_text)
    logger.info(f"Sections detected: {list(sections.keys())}")

    # ── 4. Keyword extraction (with skill normalization) ──────────────────────
    resume_keys = nlp_service.extract_keywords(resume_text)
    jd_keys = nlp_service.extract_keywords(jd_text)
    skill_gaps = improvement_service.compute_skill_gaps(
        resume_keywords=resume_keys,
        jd_keywords=jd_keys,
        resume_raw_text=resume_text,
    )

    # ── 5. Embeddings ─────────────────────────────────────────────────────────
    jd_clean = nlp_service.preprocess(jd_text)
    jd_embedding = embedding_service.embed(jd_clean)
    section_embeddings = embedding_service.embed_sections(sections)

    # ── 6. Scoring ────────────────────────────────────────────────────────────
    semantic, section_scores_raw = scoring_service.semantic_score_sections(
        section_embeddings, jd_embedding
    )
    keyword = scoring_service.tfidf_keyword_score(resume_text, jd_text)

    # ── 7. Format penalty ─────────────────────────────────────────────────────
    format_penalty, format_issues = improvement_service.compute_format_penalty(
        layout_metadata
    )

    scores = scoring_service.final_score_breakdown(
        semantic=semantic,
        keyword=keyword,
        format_penalty=format_penalty,
        resume_raw=resume_text,
        jd_raw=jd_text,
    )
    final = scores["final"]

    logger.info(
        f"Scores — semantic={semantic}, keyword={keyword}, "
        f"bonus={scores['skill_bonus']}, penalty={format_penalty}, final={final}"
    )

    # ── 8. Improvement analysis ───────────────────────────────────────────────
    expected_sections = {"skills", "experience", "education", "projects", "summary"}
    found_sections = set(sections.keys())
    sections_found = list(found_sections)
    sections_missing = list(expected_sections - found_sections)
    
    quality_issues = improvement_service.detect_quality_issues(resume_text)
    alignment_warning = improvement_service.jd_alignment_warning(final)

    # ── 8b. Experience extraction ─────────────────────────────────────────────
    experience_data = experience_service.extract_experience(resume_text)

    # ── 9. Build section scores model ─────────────────────────────────────────
    section_scores = SectionScores(
        skills=section_scores_raw.get("skills", 0.0),
        experience=section_scores_raw.get("experience", 0.0),
        projects=section_scores_raw.get("projects"),
        education=section_scores_raw.get("education", 0.0),
        summary=section_scores_raw.get("summary"),
    )

    # ── 9b. Generate recommendations ──────────────────────────────────────────
    raw_recs = recommendation_service.generate_recommendations(
        scores={"semantic": semantic, "keyword": keyword,
                "format_penalty": format_penalty, "final": final},
        section_scores=section_scores_raw,
        skill_gaps=skill_gaps,
        format_issues=format_issues,
        quality_issues=quality_issues,
        sections_found=sections_found,
        sections_missing=sections_missing,
        resume_sections=sections,   # pass parsed sections for content generation
    )
    rec_summary = recommendation_service.summarize_recommendations(raw_recs)
    recommendations = [
        Recommendation(
            priority=r["priority"],
            category=r["category"],
            title=r["title"],
            description=r["description"],
            impact=r["impact"],
            suggested_content=[SuggestedContent(**sc) for sc in r.get("suggested_content", [])],
        )
        for r in raw_recs
    ]

    logger.info(
        f"Recommendations generated: {rec_summary['total']} total "
        f"({rec_summary['critical']} critical, {rec_summary['high']} high)"
    )

    # ── 10. Persist to DB ─────────────────────────────────────────────────────
    analysis_id = str(uuid.uuid4())
    record = AnalysisRecord(
        id=uuid.UUID(analysis_id),
        resume_text=resume_text,
        jd_text=jd_text,
        score_json={
            **scores,
            "experience": experience_data,
        },
        sections_json={
            "found": sections_found,
            "missing": sections_missing,
            "section_scores": section_scores_raw,
            "format_issues": format_issues,
            "quality_issues": quality_issues,
        },
        skill_gaps_json={"gaps": skill_gaps},
    )
    db.add(record)
    await db.commit()

    logger.info(f"Analysis persisted: id={analysis_id}")

    # ── 11. Return response ───────────────────────────────────────────────────
    return AnalysisResponse(
        analysis_id=analysis_id,
        scores=ScoreBreakdown(**scores),
        sections_found=sections_found,
        sections_missing=sections_missing,
        section_scores=section_scores,
        skill_gaps=skill_gaps,
        format_issues=format_issues,
        quality_issues=quality_issues,
        jd_alignment_warning=alignment_warning,
        recommendations=recommendations,
        recommendation_summary=RecommendationSummary(**rec_summary),
        experience=ExperienceInfo(**experience_data),
        resume_text=resume_text,
    )
