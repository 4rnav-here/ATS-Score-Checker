"""
Job Search Agent — orchestrates multi-source India-focused job searching with
experience-level filtering, company tier boosting, and per-job match scoring.

v2 changes (recommendationsystemimprovement.md):
    - Replaced Remotive (US-remote) with LinkedIn India via JSearch (RapidAPI)
    - Adzuna now queries India endpoint across multiple cities
    - Added company tier score boost (+15 for Tier 1, +7 for Tier 2)
    - city_filter parameter for location-specific searches
    - Returns company_tier and tier_label fields on each job
"""

import asyncio

from app.agents.tools.adzuna_tool import search_adzuna_multi_city
from app.agents.tools.linkedin_jobs_tool import search_linkedin_india
from app.agents.tools.scoring_tool import score_job_match
from app.agents.tools.company_tier_filter import get_company_tier, tier_score_boost, tier_label
from app.core.config import MAX_JOB_RESULTS
from app.core.logger import logger
from app.services.nlp_service import extract_keywords


# ── Experience-aware query templates ──────────────────────────────────────────
EXPERIENCE_QUERY_MAP: dict[str, list[str]] = {
    "intern":  ["internship", "student developer", "trainee software engineer"],
    "junior":  ["junior software engineer", "entry level developer", "associate engineer"],
    "mid":     ["software engineer", "full stack developer", "backend developer"],
    "senior":  ["senior software engineer", "lead developer", "tech lead"],
    "staff":   ["staff engineer", "principal engineer", "engineering manager"],
}

# ── Title keywords to EXCLUDE per level ───────────────────────────────────────
EXPERIENCE_TITLE_FILTERS: dict[str, list[str]] = {
    "intern":  ["senior", "lead", "principal", "staff", "manager"],
    "junior":  ["senior", "lead", "principal", "staff", "manager"],
    "mid":     ["intern", "trainee", "principal", "staff", "manager"],
    "senior":  ["intern", "trainee", "junior", "entry"],
    "staff":   ["intern", "trainee", "junior", "entry"],
}


def _filter_by_experience(jobs: list[dict], level: str) -> list[dict]:
    """Remove jobs whose titles contain excluded keywords for this level."""
    exclusions = EXPERIENCE_TITLE_FILTERS.get(level, [])
    return [
        job for job in jobs
        if not any(ex in job["title"].lower() for ex in exclusions)
    ]


def _deduplicate(jobs: list[dict]) -> list[dict]:
    """Deduplicate by URL — keeps first occurrence."""
    seen: set[str] = set()
    result: list[dict] = []
    for job in jobs:
        url = job.get("url", "")
        if url and url not in seen:
            seen.add(url)
            result.append(job)
    return result


async def run_job_search(
    analysis: dict,
    max_days_old: int = 30,
    city_filter: list[str] | None = None,
) -> list[dict]:
    """
    Main entry point for job search. Called by POST /api/jobs/search.

    Args:
        analysis:    Full dict from ATS pipeline (experience, skill_gaps, resume_text)
        max_days_old: Recency filter for Adzuna (days)
        city_filter: Optional list of Indian cities to restrict results

    Returns:
        List of job dicts sorted by adjusted match_score descending,
        capped at MAX_JOB_RESULTS. Each job includes:
          match_score, company_tier, tier_label fields.
    """
    experience = analysis.get("experience", {})
    level = experience.get("level", "mid")
    skill_gaps = analysis.get("skill_gaps", [])
    resume_text = analysis.get("resume_text", "")

    resume_keys = list(extract_keywords(resume_text))

    # Build search queries
    level_queries = EXPERIENCE_QUERY_MAP.get(level, ["software engineer"])
    skill_queries = [f"{level_queries[0]} {s}" for s in skill_gaps[:3]]
    all_queries = (level_queries + skill_queries)[:4]  # cap to avoid rate limits

    logger.info(f"Job search v2: level={level}, queries={all_queries}, cities={city_filter}")

    # ── Run Adzuna (India, multi-city) + LinkedIn India in parallel ───────────
    adzuna_tasks = [
        search_adzuna_multi_city(q, cities=city_filter, max_days_old=max_days_old)
        for q in all_queries[:2]
    ]
    linkedin_tasks = [
        search_linkedin_india(q)
        for q in all_queries[:2]
    ]

    all_results = await asyncio.gather(
        *adzuna_tasks, *linkedin_tasks,
        return_exceptions=True,
    )

    # Flatten + skip failed tasks
    raw_jobs: list[dict] = []
    for result in all_results:
        if isinstance(result, Exception):
            logger.warning(f"Job search task failed: {result}")
            continue
        raw_jobs.extend(result)

    logger.info(f"Raw job results: {len(raw_jobs)}")

    # ── Dedup + experience filter ─────────────────────────────────────────────
    unique_jobs = _deduplicate(raw_jobs)
    filtered_jobs = _filter_by_experience(unique_jobs, level)
    logger.info(f"After dedup + experience filter: {len(filtered_jobs)} jobs")

    # ── Score each job against resume (CPU-bound → thread pool) ───────────────
    semaphore = asyncio.Semaphore(10)

    async def score_one(job: dict) -> dict:
        async with semaphore:
            loop = asyncio.get_event_loop()
            raw_score = await loop.run_in_executor(
                None,
                score_job_match,
                job.get("description", ""),
                resume_text,
                resume_keys,
            )
            job["match_score"] = raw_score
            return job

    scored_jobs = await asyncio.gather(
        *[score_one(j) for j in filtered_jobs],
        return_exceptions=True,
    )
    valid_jobs = [j for j in scored_jobs if isinstance(j, dict)]

    # ── Apply company tier boost ───────────────────────────────────────────────
    for job in valid_jobs:
        tier = get_company_tier(job.get("company", ""))
        boost = tier_score_boost(tier)
        job["match_score"] = min(100.0, round(job["match_score"] + boost, 1))
        job["company_tier"] = tier
        job["tier_label"] = tier_label(tier)

    # ── Sort and return top N ──────────────────────────────────────────────────
    sorted_jobs = sorted(valid_jobs, key=lambda j: j.get("match_score", 0), reverse=True)
    result = sorted_jobs[:MAX_JOB_RESULTS]

    logger.info(f"Job search complete: {len(result)} results returned")
    return result
