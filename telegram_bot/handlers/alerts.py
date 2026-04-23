"""
/alert handler — toggle daily job alert subscriptions.

Usage:
    /alert on  — subscribe to daily job alerts
    /alert off — unsubscribe from alerts
"""

from telegram import Update
from telegram.ext import ContextTypes

from telegram_bot.api_client import get_client


async def alert_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /alert on|off command."""
    text = update.message.text.strip().lower()
    parts = text.split()

    if len(parts) < 2 or parts[1] not in ("on", "off"):
        await update.message.reply_text(
            "Usage: /alert on or /alert off\n\n"
            "• /alert on — Get daily job matches at 9AM UTC\n"
            "• /alert off — Stop daily alerts"
        )
        return

    action = parts[1]
    analysis_id = ctx.user_data.get("analysis_id")

    if action == "on":
        if not analysis_id:
            await update.message.reply_text(
                "Please run /analyze first so I know what jobs to look for."
            )
            return

        # Call backend to enable alert
        try:
            client = await get_client()
            response = await client.post(
                "/api/alerts",
                json={
                    "chat_id": update.effective_chat.id,
                    "analysis_id": analysis_id,
                    "enabled": True,
                },
            )
            response.raise_for_status()
            await update.message.reply_text(
                "🔔 *Daily job alert enabled!*\n"
                "You'll receive fresh job matches every morning at 9AM UTC.\n\n"
                "Send /alert off to unsubscribe.",
                parse_mode="Markdown",
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to set alert: {str(e)[:100]}")

    else:  # off
        try:
            client = await get_client()
            response = await client.post(
                "/api/alerts",
                json={
                    "chat_id": update.effective_chat.id,
                    "analysis_id": analysis_id or "",
                    "enabled": False,
                },
            )
            response.raise_for_status()
            await update.message.reply_text(
                "🔕 Daily job alert *disabled*. You won't receive further alerts.\n"
                "Send /alert on to re-subscribe.",
                parse_mode="Markdown",
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Failed to disable alert: {str(e)[:100]}")


async def alert_on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle alert_on:{analysis_id} callback from inline button."""
    query = update.callback_query
    await query.answer()

    parts = query.data.split(":")
    if len(parts) != 2:
        return

    analysis_id = parts[1]
    chat_id = update.effective_chat.id

    try:
        client = await get_client()
        response = await client.post(
            "/api/alerts",
            json={
                "chat_id": chat_id,
                "analysis_id": analysis_id,
                "enabled": True,
            },
        )
        response.raise_for_status()
        await query.edit_message_text(
            "🔔 *Daily job alert enabled!*\n"
            "You'll receive fresh job matches every morning at 9AM UTC.\n\n"
            "Send /alert off to unsubscribe.",
            parse_mode="Markdown",
        )
    except Exception as e:
        await query.edit_message_text(f"❌ Failed to set alert: {str(e)[:100]}")
