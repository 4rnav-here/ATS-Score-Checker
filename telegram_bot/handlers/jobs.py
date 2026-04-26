"""
/jobs handler — job search with paginated inline keyboards.
Also handles callback queries for pagination navigation and city filtering.

v2 changes:
    - Job cards now show tier_label (⭐ Top Company / ✅ Quality Employer)
    - City filter inline keyboard added
    - Passes cities parameter to api_client.get_job_matches()
"""

import math

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from telegram_bot.api_client import get_job_matches
from telegram_bot.keyboards.inline import jobs_keyboard
from telegram_bot.formatters.job_card import format_job_page
from telegram_bot.config import config

# Available city filters
CITY_OPTIONS = [
    ("All India", "all"),
    ("Bangalore", "Bangalore"),
    ("Hyderabad", "Hyderabad"),
    ("Pune", "Pune"),
    ("Chennai", "Chennai"),
    ("Mumbai", "Mumbai"),
    ("Delhi NCR", "Delhi"),
    ("Remote", "remote"),
]


def _city_filter_keyboard(analysis_id: str, active_city: str = "all") -> InlineKeyboardMarkup:
    """Inline keyboard for city filtering."""
    buttons = []
    row = []
    for label, value in CITY_OPTIONS:
        marker = "● " if value == active_city else ""
        row.append(
            InlineKeyboardButton(
                f"{marker}{label}",
                callback_data=f"jobs_city:{analysis_id}:{value}",
            )
        )
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


async def jobs_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /jobs command — show city filter, then fetch job matches."""
    analysis_id = ctx.user_data.get("analysis_id")

    if not analysis_id:
        await update.message.reply_text(
            "Please run /analyze first to get job recommendations."
        )
        return

    # Show city filter first
    await update.message.reply_text(
        "🌏 *Select your preferred location:*\n"
        "Choose a city to filter job results, or select All India.",
        parse_mode="Markdown",
        reply_markup=_city_filter_keyboard(analysis_id, active_city="all"),
    )


async def jobs_page_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle pagination callback: jobs_page:{analysis_id}:{page}"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3:
        return

    _, analysis_id, page_str = parts
    page = int(page_str)

    jobs = ctx.user_data.get("jobs")
    if not jobs:
        try:
            city_filter = ctx.user_data.get("city_filter")
            jobs = await get_job_matches(analysis_id, city_filter=city_filter)
            ctx.user_data["jobs"] = jobs
        except Exception:
            await query.edit_message_text("❌ Could not load jobs. Try /jobs again.")
            return

    total_pages = math.ceil(len(jobs) / config.JOB_PAGE_SIZE)
    text = format_job_page(jobs, page=page, page_size=config.JOB_PAGE_SIZE)
    keyboard = jobs_keyboard(analysis_id, page=page, total_pages=total_pages)

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")


async def jobs_city_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle city filter selection: jobs_city:{analysis_id}:{city}"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 3:
        return

    _, analysis_id, city = parts

    # Store city filter for pagination continuity
    city_filter = None if city in ("all", "remote") else [city]
    ctx.user_data["city_filter"] = city_filter
    ctx.user_data["jobs"] = None  # Force re-fetch with new filter

    await query.edit_message_text(
        f"🔍 Searching jobs in *{dict(CITY_OPTIONS).get(city, city)}*...",
        parse_mode="Markdown",
    )

    try:
        jobs = await get_job_matches(analysis_id, city_filter=city_filter)
    except Exception as e:
        await query.edit_message_text(f"❌ Job search failed: {str(e)[:100]}")
        return

    if not jobs:
        await query.edit_message_text(
            f"No jobs found in {dict(CITY_OPTIONS).get(city, city)}. "
            "Try a different city or All India."
        )
        return

    ctx.user_data["jobs"] = jobs
    total_pages = math.ceil(len(jobs) / config.JOB_PAGE_SIZE)

    text = format_job_page(jobs, page=0, page_size=config.JOB_PAGE_SIZE)
    keyboard = jobs_keyboard(analysis_id, page=0, total_pages=total_pages)

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")
