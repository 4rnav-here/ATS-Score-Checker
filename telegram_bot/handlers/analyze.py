"""
/analyze ConversationHandler — multi-step resume analysis flow.

States:
    WAITING_FOR_PDF → User uploads PDF
    WAITING_FOR_JD  → User pastes job description text
    (Processing)    → Bot calls /api/analyze, sends score card

The ConversationHandler manages state transitions automatically.
"""

import io

from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from telegram_bot.api_client import analyze_resume
from telegram_bot.keyboards.inline import result_keyboard
from telegram_bot.formatters.score_card import format_score_card
from telegram_bot.config import config

# State constants
WAITING_FOR_PDF, WAITING_FOR_JD = range(2)


async def cmd_analyze(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Entry point: ask user to upload PDF."""
    await update.message.reply_text(
        "📄 Please upload your resume as a *PDF* file.\n"
        f"Make sure it is under {config.MAX_PDF_SIZE_MB} MB and not password-protected.",
        parse_mode="Markdown",
    )
    return WAITING_FOR_PDF


async def receive_pdf(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle PDF upload: validate and store bytes."""
    doc = update.message.document

    # Validate MIME type
    if doc.mime_type != "application/pdf":
        await update.message.reply_text("⚠️ Please send a PDF file, not another format.")
        return WAITING_FOR_PDF

    # Validate file size
    if doc.file_size > config.MAX_PDF_SIZE_MB * 1024 * 1024:
        await update.message.reply_text(
            f"⚠️ File too large. Max size is {config.MAX_PDF_SIZE_MB} MB."
        )
        return WAITING_FOR_PDF

    # Download file bytes
    tg_file = await doc.get_file()
    buf = io.BytesIO()
    await tg_file.download_to_memory(buf)
    ctx.user_data["pdf_bytes"] = buf.getvalue()

    await update.message.reply_text(
        "✅ Resume received!\n\n"
        "📋 Now paste the *job description* text below.\n"
        "It should be at least 20 words for accurate matching.",
        parse_mode="Markdown",
    )
    return WAITING_FOR_JD


async def receive_jd(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle JD text: call API and send score card."""
    jd_text = update.message.text

    if len(jd_text.split()) < 20:
        await update.message.reply_text(
            "⚠️ Job description too short. Paste the full JD text (minimum 20 words)."
        )
        return WAITING_FOR_JD

    # Show typing indicator while API processes
    await update.message.chat.send_action("typing")
    status_msg = await update.message.reply_text(
        "⏳ Analyzing your resume... this takes 10-20 seconds."
    )

    try:
        result = await analyze_resume(ctx.user_data["pdf_bytes"], jd_text)
    except Exception as e:
        await status_msg.edit_text(
            "❌ Analysis failed. Please try again in a moment.\n"
            f"Error: {str(e)[:100]}"
        )
        return ConversationHandler.END

    # Store analysis for other handlers
    ctx.user_data["analysis_id"] = result["analysis_id"]
    ctx.user_data["analysis"] = result

    # Send formatted score card with action buttons
    card_text = format_score_card(result)
    keyboard = result_keyboard(result["analysis_id"])

    await status_msg.delete()
    await update.message.reply_text(
        card_text,
        reply_markup=keyboard,
        parse_mode="Markdown",
    )

    # Clean up large bytes from memory immediately
    ctx.user_data.pop("pdf_bytes", None)

    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the current conversation."""
    ctx.user_data.clear()
    await update.message.reply_text("Analysis cancelled. Send /analyze to start again.")
    return ConversationHandler.END


def build_analyze_conversation() -> ConversationHandler:
    """Build and return the ConversationHandler for /analyze."""
    return ConversationHandler(
        entry_points=[CommandHandler("analyze", cmd_analyze)],
        states={
            WAITING_FOR_PDF: [
                MessageHandler(filters.Document.PDF, receive_pdf),
            ],
            WAITING_FOR_JD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_jd),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=600,  # 10 minutes — auto-cancel if user goes silent
        per_user=True,
        per_chat=True,
    )
