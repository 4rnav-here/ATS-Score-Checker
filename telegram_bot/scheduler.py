"""
Job Alert Scheduler — separate process that sends daily job digests.

Runs as: python -m telegram_bot.scheduler

Every morning at ALERT_HOUR (default 9AM UTC):
    1. Query PostgreSQL for users with active alerts
    2. Re-run job search for each user's latest analysis
    3. Compare with already-sent jobs (prevent duplicates)
    4. Deliver fresh matches via Telegram
"""

import asyncio

import asyncpg
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Bot

from telegram_bot.config import config
from telegram_bot.core.alert_sender import send_daily_digest

# ── Structured logging (Section 10.3) ────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(0),
)
log = structlog.get_logger()


async def run_daily_alerts(bot: Bot, db_pool: asyncpg.Pool) -> None:
    """Fetch all active alert subscribers and send digests."""
    log.info("scheduler.run_started")

    async with db_pool.acquire() as conn:
        users = await conn.fetch(
            "SELECT chat_id, analysis_id FROM user_alerts WHERE alert_enabled = TRUE"
        )

    log.info("scheduler.subscribers_found", count=len(users))

    if not users:
        return

    # Run all digests concurrently with throttling
    sem = asyncio.Semaphore(10)  # Telegram rate limit: 30 msg/sec

    async def throttled(chat_id: int, analysis_id: str):
        async with sem:
            await send_daily_digest(bot, chat_id, str(analysis_id), db_pool)

    await asyncio.gather(
        *[throttled(row["chat_id"], row["analysis_id"]) for row in users],
        return_exceptions=True,
    )

    log.info("scheduler.run_completed")


async def main():
    """Entry point for the scheduler process."""
    if not config.TELEGRAM_BOT_TOKEN:
        log.error("scheduler.no_token", msg="TELEGRAM_BOT_TOKEN not set")
        return

    bot = Bot(token=config.TELEGRAM_BOT_TOKEN)

    # Use raw asyncpg for the scheduler (lighter than SQLAlchemy)
    # Convert SQLAlchemy URL to asyncpg format
    db_url = config.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    db_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)

    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        run_daily_alerts,
        trigger="cron",
        hour=config.ALERT_HOUR,
        minute=0,
        args=[bot, db_pool],
    )
    scheduler.start()

    log.info("scheduler.started", alert_hour=config.ALERT_HOUR)

    try:
        await asyncio.Event().wait()  # Run forever
    finally:
        scheduler.shutdown()
        await db_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
