"""
Rate Limiting Service — Redis-backed brute force protection.

Rules:
    - 5 OTP requests / hour / email
    - 10 verify attempts / hour / email

Uses Redis key expiry for automatic cleanup.
"""

import redis.asyncio as aioredis

from app.core.config import (
    REDIS_URL,
    OTP_RATE_LIMIT_PER_HOUR,
    VERIFY_RATE_LIMIT_PER_HOUR,
)
from app.core.logger import logger

_pool: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    """Get or create the shared Redis connection."""
    global _pool
    if _pool is None:
        _pool = await aioredis.from_url(
            REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10,
        )
    return _pool


async def check_otp_rate_limit(email: str) -> bool:
    """
    Check if the email has exceeded OTP request rate limit.

    Returns True if ALLOWED, False if rate limited.
    """
    key = f"rate:otp:{email}"
    try:
        r = await _get_redis()
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 3600)  # 1 hour TTL

        if count > OTP_RATE_LIMIT_PER_HOUR:
            logger.warning(f"OTP rate limit exceeded for {email}: {count} requests")
            return False
        return True
    except Exception as e:
        logger.error(f"Redis rate limit check failed: {e}")
        return True  # Fail open — don't block users if Redis is down


async def check_verify_rate_limit(email: str) -> bool:
    """
    Check if the email has exceeded verification attempt rate limit.

    Returns True if ALLOWED, False if rate limited.
    """
    key = f"rate:verify:{email}"
    try:
        r = await _get_redis()
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 3600)  # 1 hour TTL

        if count > VERIFY_RATE_LIMIT_PER_HOUR:
            logger.warning(f"Verify rate limit exceeded for {email}: {count} requests")
            return False
        return True
    except Exception as e:
        logger.error(f"Redis rate limit check failed: {e}")
        return True  # Fail open
