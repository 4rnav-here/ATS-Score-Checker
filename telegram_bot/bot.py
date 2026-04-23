"""
Telegram Bot Entry Point — registers all handlers and starts long-polling.

Run as: python -m telegram_bot.bot

This file does NOT contain handler logic — that lives in handlers/.
"""

import traceback

import structlog
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from telegram_bot.config import config
from telegram_bot.handlers.start import start_handler
from telegram_bot.handlers.analyze import build_analyze_conversation
from telegram_bot.handlers.jobs import jobs_handler, jobs_page_callback
from telegram_bot.handlers.feedback import (
    feedback_handler,
    feedback_callback,
    interview_handler,
    interview_callback,
)
from telegram_bot.handlers.alerts import alert_handler, alert_on_callback

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


async def post_init(app: Application) -> None:
    """Set bot commands menu visible in Telegram."""
    await app.bot.set_my_commands([
        ("start", "Welcome and help"),
        ("analyze", "Analyze a resume against a job description"),
        ("jobs", "Find jobs matching your last analysis"),
        ("feedback", "Get AI feedback on your resume"),
        ("interview", "Generate interview questions"),
        ("alert", "Toggle daily job alert: /alert on or /alert off"),
    ])
    log.info("bot.started", msg="Commands registered")


async def global_error_handler(update: object, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch all unhandled errors — never let an exception silently drop."""
    log.error(
        "bot.unhandled_error",
        error=str(ctx.error),
        traceback=traceback.format_exc(),
    )

    if isinstance(update, Update) and update.message:
        await update.message.reply_text(
            "⚠️ An unexpected error occurred. The issue has been logged.\n"
            "Please try again or use /start to reset."
        )


def main():
    """Build the Application, register handlers, start polling."""
    if not config.TELEGRAM_BOT_TOKEN:
        log.error("bot.no_token", msg="TELEGRAM_BOT_TOKEN is not set")
        print("\n❌ TELEGRAM_BOT_TOKEN not found in .env file.")
        print("   Get a token from @BotFather on Telegram and add it to .env\n")
        return

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── Register handlers ─────────────────────────────────────────────────────
    # Order matters: ConversationHandler first, then command handlers,
    # then callback query handlers

    app.add_handler(build_analyze_conversation())  # /analyze (ConversationHandler)
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("jobs", jobs_handler))
    app.add_handler(CommandHandler("feedback", feedback_handler))
    app.add_handler(CommandHandler("interview", interview_handler))
    app.add_handler(CommandHandler("alert", alert_handler))

    # Callback query handlers for inline buttons
    app.add_handler(CallbackQueryHandler(jobs_page_callback, pattern=r"^jobs_page:"))
    app.add_handler(CallbackQueryHandler(feedback_callback, pattern=r"^feedback:"))
    app.add_handler(CallbackQueryHandler(interview_callback, pattern=r"^interview:"))
    app.add_handler(CallbackQueryHandler(alert_on_callback, pattern=r"^alert_on:"))

    # Global error handler — catches all unhandled exceptions
    app.add_error_handler(global_error_handler)

    log.info("bot.polling_started")
    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
