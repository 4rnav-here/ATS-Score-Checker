"""
Inline Keyboard builders — all InlineKeyboardMarkup construction lives here.
Centralized so button patterns and callback_data formats are consistent.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def result_keyboard(analysis_id: str) -> InlineKeyboardMarkup:
    """Post-analysis action buttons."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🤖 AI Feedback", callback_data=f"feedback:{analysis_id}"),
            InlineKeyboardButton("💼 Find Jobs", callback_data=f"jobs_page:{analysis_id}:0"),
        ],
        [
            InlineKeyboardButton("🎯 Interview Prep", callback_data=f"interview:{analysis_id}"),
            InlineKeyboardButton("🔔 Set Alert", callback_data=f"alert_on:{analysis_id}"),
        ],
    ])


def jobs_keyboard(analysis_id: str, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Paginated job navigation buttons."""
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("◀ Prev", callback_data=f"jobs_page:{analysis_id}:{page - 1}"))

    nav.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))

    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ▶", callback_data=f"jobs_page:{analysis_id}:{page + 1}"))

    return InlineKeyboardMarkup([nav])
