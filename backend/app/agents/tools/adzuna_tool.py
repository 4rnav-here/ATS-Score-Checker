"""
Adzuna Job Search Tool — searches the Adzuna job board API.
Used by the LangChain job search agent.
"""

import httpx

from app.core.config import ADZUNA_APP_ID, ADZUNA_API_KEY
from app.core.logger import logger


async def search_adzuna(
    query: str,
    location: str = "india",
    results_per_page: int = 20,
    max_days_old: int = 3,
) -> list[dict]:
    """
    Search Adzuna job board for matching positions.

    Args:
        query: Search query (e.g., "senior python developer")
        location: Country/region for job search
        results_per_page: Max results to return
        max_days_old: Only return jobs posted within this many days

    Returns:
        List of normalized job dicts.
    """
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        logger.warning("Adzuna API keys not configured — skipping search.")
        return []

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "what": query,
        "where": location,
        "results_per_page": results_per_page,
        "max_days_old": max_days_old,
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            jobs = r.json().get("results", [])

        return [
            {
                "title": j.get("title", ""),
                "company": j.get("company", {}).get("display_name", ""),
                "location": j.get("location", {}).get("display_name", ""),
                "description": j.get("description", "")[:500],
                "url": j.get("redirect_url", ""),
                "salary_min": j.get("salary_min"),
                "salary_max": j.get("salary_max"),
                "source": "adzuna",
            }
            for j in jobs
        ]
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            logger.warning(f"Adzuna rate limited: {query}")
        else:
            logger.error(f"Adzuna API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Adzuna search failed: {e}")
        return []
