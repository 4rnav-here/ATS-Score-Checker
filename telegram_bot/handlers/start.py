"""
/start handler — welcome message and help text.
"""

from telegram import Update
from telegram.ext import ContextTypes


async def start_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message with available commands."""
    welcome = (
        "*🎯 ATS Resume Analyzer Bot*\n\n"
        "I analyze your resume against job descriptions and help you:\n"
        "• Get an ATS compatibility score\n"
        "• Find matching jobs at your experience level\n"
        "• Get AI-powered improvement feedback\n"
        "• Generate interview questions\n"
        "• Set daily job alerts\n\n"
        "*Commands:*\n"
        "/analyze — Analyze resume vs job description\n"
        "/jobs — Find matching jobs\n"
        "/feedback — Get AI feedback on your resume\n"
        "/interview — Generate interview questions\n"
        "/alert on|off — Toggle daily job alerts\n"
        "/status — Show your last analysis\n\n"
        "_Start with /analyze to upload your resume!_"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")
