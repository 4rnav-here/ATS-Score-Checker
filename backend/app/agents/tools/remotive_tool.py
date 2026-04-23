"""
Remotive Job Search Tool — searches the Remotive API (no API key required).
Used by the LangChain job search agent.
"""

import httpx

from app.core.logger import logger


async def search_remotive(query: str) -> list[dict]:
    """
    Search Remotive for remote tech jobs.
    No API key required — free open API.

    Args:
        query: Search query (e.g., "python developer")

    Returns:
        List of normalized job dicts.
    """
    url = "https://remotive.com/api/remote-jobs"

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(url, params={"search": query, "limit": 20})
            r.raise_for_status()
            jobs = r.json().get("jobs", [])

        return [
            {
                "title": j.get("title", ""),
                "company": j.get("company_name", ""),
                "location": "Remote - " + j.get("candidate_required_location", "Worldwide"),
                "description": j.get("description", "")[:500],
                "url": j.get("url", ""),
                "salary_min": None,
                "salary_max": None,
                "source": "remotive",
            }
            for j in jobs
        ]
    except Exception as e:
        logger.error(f"Remotive search failed: {e}")
        return []
