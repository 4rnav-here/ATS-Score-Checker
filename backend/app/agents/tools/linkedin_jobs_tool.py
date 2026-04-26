"""
LinkedIn India Job Search Tool — uses the JSearch API (RapidAPI) which
aggregates LinkedIn, Indeed, and Glassdoor listings, filtered to India.

No scraping. Uses the official JSearch REST API.
Requires: RAPIDAPI_KEY in environment / config.
"""

import httpx

from app.core.config import RAPIDAPI_KEY
from app.core.logger import logger

JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"

JSEARCH_HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
}

INDIA_TECH_HUBS = [
    "Bangalore India",
    "Hyderabad India",
    "Pune India",
    "Chennai India",
    "Mumbai India",
    "Gurgaon India",
    "Noida India",
]


async def search_linkedin_india(
    query: str,
    location: str = "India",
    num_pages: int = 2,
) -> list[dict]:
    """
    Search JSearch (LinkedIn/Indeed/Glassdoor aggregator) for Indian job listings.

    Args:
        query:     Search query e.g. "software engineer React"
        location:  Location string (default "India")
        num_pages: Pages of results to fetch (20 results/page)

    Returns:
        List of normalized job dicts matching the standard schema used
        by the rest of the job search pipeline.
    """
    if not RAPIDAPI_KEY:
        logger.warning("RAPIDAPI_KEY not configured — skipping LinkedIn/JSearch.")
        return []

    params = {
        "query": f"{query} in {location}",
        "page": "1",
        "num_pages": str(num_pages),
        "date_posted": "month",
        "employment_types": "FULLTIME",
        "remote_jobs_only": "false",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(JSEARCH_URL, headers=JSEARCH_HEADERS, params=params)
            r.raise_for_status()
            jobs = r.json().get("data", [])

        return [
            {
                "title": j.get("job_title", ""),
                "company": j.get("employer_name", ""),
                "location": _format_location(j),
                "description": j.get("job_description", "")[:500],
                "url": j.get("job_apply_link") or j.get("job_google_link", ""),
                "salary_min": j.get("job_min_salary"),
                "salary_max": j.get("job_max_salary"),
                "source": "linkedin",
            }
            for j in jobs
            if j.get("job_apply_link") or j.get("job_google_link")
        ]

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning(f"JSearch rate limited for query: {query}")
        elif e.response.status_code == 403:
            logger.warning("JSearch 403 — check RAPIDAPI_KEY validity.")
        else:
            logger.error(f"JSearch API error ({e.response.status_code}): {e}")
        return []
    except Exception as e:
        logger.error(f"JSearch search failed: {e}")
        return []


def _format_location(job: dict) -> str:
    """Build a human-readable location string from JSearch job fields."""
    city = job.get("job_city", "")
    state = job.get("job_state", "")
    country = job.get("job_country", "India")
    parts = [p for p in [city, state] if p]
    if parts:
        return f"{', '.join(parts)}, {country}"
    return country
