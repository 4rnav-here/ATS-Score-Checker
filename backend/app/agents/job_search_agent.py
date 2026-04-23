"""
Job Search Agent — orchestrates multi-source job searching with
experience-level filtering and per-job match scoring.

This is NOT a LangChain ReAct agent (to avoid LLM dependency for job search).
It uses deterministic orchestration: parallel API calls → dedup → filter → score → rank.
"""

import asyncio

from app.agents.tools.adzuna_tool import search_adzuna
from app.agents.tools.remotive_tool import search_remotive
from app.agents.tools.scoring_tool import score_job_match
from app.core.config import MAX_JOB_RESULTS
from app.core.logger import logger
from app.services.nlp_service import extract_keywords


# ── Experience-aware query templates ──────────────────────────────────────────
EXPERIENCE_QUERY_MAP: dict[str, list[str]] = {
    "intern": ["internship", "student developer", "trainee"],
    "junior": ["junior", "entry level", "graduate developer"],
    "mid": ["software engineer", "developer", "engineer"],
    "senior": ["senior engineer", "lead developer", "tech lead"],
    "staff": ["staff engineer", "principal engineer", "engineering manager"],
}

# ── Title keywords to EXCLUDE per level ───────────────────────────────────────
EXPERIENCE_TITLE_FILTERS: dict[str, list[str]] = {
    "intern": ["senior", "lead", "principal", "staff", "manager"],
    "junior": ["senior", "lead", "principal", "staff", "manager"],
    "mid": ["intern", "trainee", "principal", "staff", "manager"],
    "senior": ["intern", "trainee", "junior", "entry"],
    "staff": ["intern", "trainee", "junior", "entry"],
}


def _filter_by_experience(jobs: list[dict], level: str) -> list[dict]:
    """Remove jobs whose titles contain excluded keywords for this level."""
    exclusions = EXPERIENCE_TITLE_FILTERS.get(level, [])
    filtered = []
    for job in jobs:
        title_lower = job["title"].lower()
        if not any(ex in title_lower for ex in exclusions):
            filtered.append(job)
    return filtered


async def run_job_search(analysis: dict, max_days_old: int = 3) -> list[dict]:
    """
    Main entry point called by POST /api/jobs/search.

    Args:
        analysis: The full dict from the ATS scoring pipeline,
                  including experience, skill_gaps, etc.

    Returns:
        List of job dicts sorted by match_score descending,
        capped at MAX_JOB_RESULTS.
    """
    experience = analysis.get("experience", {})
    level = experience.get("level", "mid")
    skill_gaps = analysis.get("skill_gaps", [])
    resume_text = analysis.get("resume_text", "")

    # Extract resume keywords for matching
    resume_keys = list(extract_keywords(resume_text))

    # Build search queries from experience level + top skills
    level_queries = EXPERIENCE_QUERY_MAP.get(level, ["software engineer"])
    skill_queries = [f"{level_queries[0]} {s}" for s in skill_gaps[:3]]
    all_queries = level_queries + skill_queries

    logger.info(f"Job search: level={level}, queries={all_queries[:5]}")

    # ── Run Adzuna + Remotive in parallel for speed ───────────────────────────
    adzuna_tasks = [search_adzuna(q, max_days_old=max_days_old) for q in all_queries[:3]]
    remotive_tasks = [search_remotive(q) for q in all_queries[:2]]

    all_results = await asyncio.gather(
        *adzuna_tasks, *remotive_tasks, return_exceptions=True
    )

    # Flatten results, skip failed tasks
    raw_jobs: list[dict] = []
    for result in all_results:
        if isinstance(result, Exception):
            logger.warning(f"Job search task failed: {result}")
            continue
        raw_jobs.extend(result)

    logger.info(f"Raw job results: {len(raw_jobs)}")

    # ── Deduplicate by URL ────────────────────────────────────────────────────
    seen_urls: set[str] = set()
    unique_jobs: list[dict] = []
    for job in raw_jobs:
        url = job.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_jobs.append(job)

    # ── Filter by experience level ────────────────────────────────────────────
    filtered_jobs = _filter_by_experience(unique_jobs, level)
    logger.info(f"After experience filter: {len(filtered_jobs)} jobs")

    # ── Score each job against the resume ──────────────────────────────────────
    # Use a semaphore to limit concurrent scoring (CPU-bound embedding)
    semaphore = asyncio.Semaphore(10)

    async def score_one(job: dict) -> dict:
        async with semaphore:
            # Run synchronous scoring in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            job["match_score"] = await loop.run_in_executor(
                None,
                score_job_match,
                job.get("description", ""),
                resume_text,
                resume_keys,
            )
            return job

    scored_jobs = await asyncio.gather(
        *[score_one(j) for j in filtered_jobs],
        return_exceptions=True,
    )

    # Filter out any failed scoring attempts
    valid_jobs = [j for j in scored_jobs if isinstance(j, dict)]

    # ── Sort by match score, return top N ─────────────────────────────────────
    sorted_jobs = sorted(valid_jobs, key=lambda j: j.get("match_score", 0), reverse=True)
    result = sorted_jobs[:MAX_JOB_RESULTS]

    logger.info(f"Job search complete: {len(result)} results returned")
    return result
