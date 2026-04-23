"""
Redis client — async connection pool with cache helpers.

Used for:
    - Caching API responses (job search results, 4h TTL)
    - Conversation state (ConversationHandler persistence)
    - Distributed lock for scheduler (prevent duplicate runs)
"""

import redis.asyncio as aioredis

from telegram_bot.config import config

_pool: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    """Get or create the shared Redis connection pool."""
    global _pool
    if _pool is None:
        _pool = await aioredis.from_url(
            config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def cache_set(key: str, value: str, ttl_seconds: int = 300) -> None:
    """Set a cached value with TTL."""
    try:
        r = await get_redis()
        await r.setex(key, ttl_seconds, value)
    except Exception:
        pass  # Cache failures are non-fatal — fall through to API


async def cache_get(key: str) -> str | None:
    """Get a cached value, or None if missing/expired."""
    try:
        r = await get_redis()
        return await r.get(key)
    except Exception:
        return None  # Cache miss — caller will fetch from API


async def cache_delete(key: str) -> None:
    """Delete a cached value."""
    try:
        r = await get_redis()
        await r.delete(key)
    except Exception:
        pass
