"""
/feedback and /interview handlers — deliver AI-generated content.
Also handles inline keyboard callbacks for these actions.
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.api_client import get_ai_feedback, get_interview_questions


async def feedback_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /feedback command or callback — get AI recommendations."""
    analysis_id = ctx.user_data.get("analysis_id")
    analysis = ctx.user_data.get("analysis")

    if not analysis_id:
        await update.message.reply_text("Please run /analyze first.")
        return

    msg = await update.message.reply_text("🤖 Generating AI feedback...")

    try:
        # Use locally stored recommendations if available
        recs = analysis.get("recommendations", []) if analysis else []

        if recs:
            text = _format_recommendations(recs)
        else:
            # Fall back to API call
            result = await get_ai_feedback(analysis_id)
            recs = result.get("recommendations", [])
            text = _format_recommendations(recs) if recs else "No recommendations available."

        await msg.edit_text(text, parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(f"❌ Failed to get feedback. Try again.\nError: {str(e)[:100]}")


async def feedback_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle feedback:{analysis_id} callback from inline button."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 2:
        return

    analysis_id = parts[1]
    analysis = ctx.user_data.get("analysis")

    await query.edit_message_text("🤖 Generating AI feedback...")

    try:
        recs = analysis.get("recommendations", []) if analysis else []

        if recs:
            text = _format_recommendations(recs)
        else:
            result = await get_ai_feedback(analysis_id)
            recs = result.get("recommendations", [])
            text = _format_recommendations(recs) if recs else "No recommendations available."

        await query.edit_message_text(text, parse_mode="Markdown")
    except Exception as e:
        await query.edit_message_text(f"❌ Feedback failed: {str(e)[:100]}")


async def interview_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /interview command — generate interview questions."""
    analysis_id = ctx.user_data.get("analysis_id")

    if not analysis_id:
        await update.message.reply_text("Please run /analyze first.")
        return

    msg = await update.message.reply_text("🎯 Generating interview questions...")

    try:
        result = await get_interview_questions(analysis_id)
        questions = result.get("questions", "No questions generated.")
        await msg.edit_text(f"*🎯 Interview Questions*\n\n{questions}", parse_mode="Markdown")
    except Exception as e:
        await msg.edit_text(
            f"❌ Failed to generate questions.\nError: {str(e)[:100]}"
        )


async def interview_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle interview:{analysis_id} callback from inline button."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 2:
        return

    analysis_id = parts[1]

    await query.edit_message_text("🎯 Generating interview questions...")

    try:
        result = await get_interview_questions(analysis_id)
        questions = result.get("questions", "No questions generated.")
        await query.edit_message_text(
            f"*🎯 Interview Questions*\n\n{questions}",
            parse_mode="Markdown",
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Failed: {str(e)[:100]}")


# ── Private helpers ───────────────────────────────────────────────────────────

PRIORITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "⚪",
}


def _format_recommendations(recs: list[dict]) -> str:
    """Format recommendation list for Telegram."""
    if not recs:
        return "✅ No recommendations — your resume looks great!"

    lines = ["*🤖 AI Recommendations*\n"]

    for i, rec in enumerate(recs[:8], 1):  # Limit to 8 to avoid message size limits
        emoji = PRIORITY_EMOJI.get(rec.get("priority", "low"), "⚪")
        title = rec.get("title", "")
        desc = rec.get("description", "")
        impact = rec.get("impact", "")

        lines.append(f"{emoji} *{i}. {title}*")
        lines.append(f"  {desc[:200]}")
        if impact:
            lines.append(f"  _Impact: {impact}_")
        lines.append("")

    return "\n".join(lines)
