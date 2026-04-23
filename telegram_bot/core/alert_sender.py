"""
Alert Sender — reusable daily digest delivery logic.
Used by the scheduler process to send fresh job matches to subscribed users.
"""

import structlog
from telegram import Bot

from telegram_bot.api_client import get_job_matches
from telegram_bot.formatters.job_card import format_single_job

log = structlog.get_logger()


async def send_daily_digest(
    bot: Bot,
    chat_id: int,
    analysis_id: str,
    db_pool,
) -> None:
    """
    Send a daily job digest to a single user.

    1. Fetch fresh job matches (bypasses cache)
    2. Filter out jobs already sent to this user
    3. Send top 5 new matches
    4. Record sent jobs in DB to prevent future duplicates
    """
    try:
        # Force refresh — don't use cache for daily alerts
        all_jobs = await get_job_matches(analysis_id, force_refresh=True)

        if not all_jobs:
            log.info("alert.no_jobs", chat_id=chat_id)
            return

        # Find which URLs we've already sent
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT job_url FROM sent_jobs WHERE chat_id = $1", chat_id
            )
            sent_urls = {r["job_url"] for r in rows}

        # Only send jobs the user hasn't seen
        new_jobs = [j for j in all_jobs if j.get("url") not in sent_urls][:5]

        if not new_jobs:
            await bot.send_message(
                chat_id=chat_id,
                text="🔍 Daily job check: no new matches today. Check back tomorrow!",
            )
            return

        # Format and send
        count = len(new_jobs)
        header = f"*🌅 Daily Job Alert — {count} new match{'es' if count > 1 else ''}*\n\n"
        cards = "\n\n".join(
            format_single_job(j, i + 1) for i, j in enumerate(new_jobs)
        )

        await bot.send_message(
            chat_id=chat_id,
            text=header + cards,
            parse_mode="Markdown",
        )

        # Record sent jobs to prevent duplicates
        async with db_pool.acquire() as conn:
            await conn.executemany(
                "INSERT INTO sent_jobs(chat_id, job_url) VALUES($1, $2) ON CONFLICT DO NOTHING",
                [(chat_id, j["url"]) for j in new_jobs],
            )

        log.info("alert.sent", chat_id=chat_id, jobs_sent=count)

    except Exception as e:
        log.error("alert.delivery_failed", chat_id=chat_id, error=str(e))
