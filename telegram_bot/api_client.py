"""
API Client — the ONLY place in the bot codebase that knows the FastAPI base URL.
All handlers call these functions, never httpx directly.

Uses a shared httpx.AsyncClient with keep-alive for performance:
    - First request: ~80ms (TCP + TLS)
    - Subsequent requests: ~2ms (connection reused)
"""

import json

import httpx

from telegram_bot.config import config
from telegram_bot.redis_client import cache_get, cache_set

# Shared async client — created once, reused across all requests
_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    """Get or create the shared HTTP client."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(
            base_url=config.API_BASE_URL,
            timeout=httpx.Timeout(config.REQUEST_TIMEOUT_S),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _client


async def analyze_resume(pdf_bytes: bytes, jd_text: str) -> dict:
    """POST /api/analyze with multipart PDF + JD text."""
    client = await get_client()
    response = await client.post(
        "/api/analyze",
        files={"file": ("resume.pdf", pdf_bytes, "application/pdf")},
        data={"jd_text": jd_text},
    )
    response.raise_for_status()
    return response.json()


async def get_job_matches(
    analysis_id: str,
    force_refresh: bool = False,
    city_filter: list[str] | None = None,
) -> list[dict]:
    """POST /api/jobs/search — cached in Redis for 4 hours.

    Args:
        city_filter: Optional list of Indian cities (e.g. ["Bangalore"]).
                     Cache key includes city so different filters are cached separately.
    """
    city_key = "_".join(sorted(city_filter)) if city_filter else "all"
    cache_key = f"jobs:{analysis_id}:{city_key}"

    if not force_refresh:
        cached = await cache_get(cache_key)
        if cached:
            return json.loads(cached)

    client = await get_client()
    payload: dict = {"analysis_id": analysis_id, "max_days_old": 30}
    if city_filter:
        payload["cities"] = city_filter

    response = await client.post("/api/jobs/search", json=payload)
    response.raise_for_status()
    jobs = response.json().get("jobs", [])

    # Cache for 4 hours
    await cache_set(cache_key, json.dumps(jobs), ttl_seconds=14400)
    return jobs


async def get_ai_feedback(analysis_id: str) -> dict:
    """POST /api/feedback — returns recommendations."""
    client = await get_client()
    response = await client.post(
        "/api/feedback",
        json={"analysis_id": analysis_id},
    )
    response.raise_for_status()
    return response.json()


async def get_interview_questions(analysis_id: str) -> dict:
    """POST /api/interview — returns interview questions."""
    client = await get_client()
    response = await client.post(
        "/api/interview",
        json={"analysis_id": analysis_id},
    )
    response.raise_for_status()
    return response.json()
