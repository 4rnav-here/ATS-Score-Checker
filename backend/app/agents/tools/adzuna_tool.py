"""
Adzuna Job Search Tool — searches Adzuna's India job board API.

v2 changes (recommendationsystemimprovement.md):
    - Switched from `us`/`gb` endpoint to `in` (India)
    - Cycles across 4 major Indian tech hubs for broader coverage
    - Normalises results to the standard job dict schema
"""

import asyncio

import httpx

from app.core.config import ADZUNA_APP_ID, ADZUNA_API_KEY
from app.core.logger import logger

BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search/1"

# Major Indian tech hubs to query in rotation
INDIA_TECH_HUBS = [
    "Bangalore",
    "Hyderabad",
    "Pune",
    "Chennai",
    "Mumbai",
    "Delhi",
    "Noida",
    "Gurgaon",
]


async def search_adzuna(
    query: str,
    city: str = "Bangalore",
    results_per_page: int = 20,
    max_days_old: int = 30,
) -> list[dict]:
    """
    Search the Adzuna India job board for matching positions.

    Args:
        query:            Search query (e.g. "junior python developer")
        city:             Indian city to bias the search
        results_per_page: Max results to return per call
        max_days_old:     Only return jobs posted within this many days

    Returns:
        List of normalised job dicts.
    """
    if not ADZUNA_APP_ID or not ADZUNA_API_KEY:
        logger.warning("Adzuna API keys not configured — skipping search.")
        return []

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_API_KEY,
        "what": query,
        "where": city,
        "results_per_page": results_per_page,
        "max_days_old": max_days_old,
        "sort_by": "relevance",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(BASE_URL, params=params)
            r.raise_for_status()
            jobs = r.json().get("results", [])

        return [
            {
                "title": j.get("title", ""),
                "company": j.get("company", {}).get("display_name", ""),
                "location": j.get("location", {}).get("display_name", city),
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
            logger.warning(f"Adzuna rate limited: {query} / {city}")
        elif e.response.status_code == 403:
            logger.warning("Adzuna 403 — check ADZUNA_APP_ID / ADZUNA_API_KEY.")
        else:
            logger.error(f"Adzuna API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Adzuna search failed: {e}")
        return []


async def search_adzuna_multi_city(
    query: str,
    cities: list[str] | None = None,
    results_per_page: int = 10,
    max_days_old: int = 30,
) -> list[dict]:
    """
    Run Adzuna search across multiple Indian cities concurrently.

    Deduplicates results by URL before returning.
    """
    target_cities = cities or INDIA_TECH_HUBS[:4]  # default: top 4 hubs

    tasks = [
        search_adzuna(query, city=city, results_per_page=results_per_page, max_days_old=max_days_old)
        for city in target_cities
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for batch in results:
        if isinstance(batch, Exception):
            continue
        for job in batch:
            url = job.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduped.append(job)

    return deduped
