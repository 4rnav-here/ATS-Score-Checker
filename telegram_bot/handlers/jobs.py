"""
/jobs handler — job search with paginated inline keyboards.
Also handles callback queries for pagination navigation.
"""

import math

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.api_client import get_job_matches
from telegram_bot.keyboards.inline import jobs_keyboard
from telegram_bot.formatters.job_card import format_job_page
from telegram_bot.config import config


async def jobs_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /jobs command — fetch and display job matches."""
    analysis_id = ctx.user_data.get("analysis_id")

    if not analysis_id:
        await update.message.reply_text(
            "Please run /analyze first to get job recommendations."
        )
        return

    msg = await update.message.reply_text("🔍 Searching for matching jobs...")

    try:
        jobs = await get_job_matches(analysis_id)
    except Exception as e:
        await msg.edit_text(f"❌ Job search failed. Please try again.\nError: {str(e)[:100]}")
        return

    if not jobs:
        await msg.edit_text(
            "No matching jobs found. Try a different job description with /analyze."
        )
        return

    # Store for pagination
    ctx.user_data["jobs"] = jobs
    total_pages = math.ceil(len(jobs) / config.JOB_PAGE_SIZE)

    text = format_job_page(jobs, page=0, page_size=config.JOB_PAGE_SIZE)
    keyboard = jobs_keyboard(analysis_id, page=0, total_pages=total_pages)

    await msg.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def jobs_page_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination callback: jobs_page:{analysis_id}:{page}"""
    query = update.callback_query
    await query.answer()  # Dismiss loading spinner immediately

    parts = query.data.split(":")
    if len(parts) != 3:
        return

    _, analysis_id, page_str = parts
    page = int(page_str)

    jobs = ctx.user_data.get("jobs")
    if not jobs:
        # User restarted bot — re-fetch from cache/API
        try:
            jobs = await get_job_matches(analysis_id)
            ctx.user_data["jobs"] = jobs
        except Exception:
            await query.edit_message_text("❌ Could not load jobs. Try /jobs again.")
            return

    total_pages = math.ceil(len(jobs) / config.JOB_PAGE_SIZE)
    text = format_job_page(jobs, page=page, page_size=config.JOB_PAGE_SIZE)
    keyboard = jobs_keyboard(analysis_id, page=page, total_pages=total_pages)

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
