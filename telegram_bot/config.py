"""
Telegram Bot Configuration — loaded from environment variables.
All bot settings are centralized here. Never hardcode values in handlers.

Change LLM_MODEL to any Ollama model: mistral:latest, llama3, codellama, gemma2, etc.
"""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    TELEGRAM_BOT_TOKEN: str = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    API_BASE_URL: str = os.environ.get("API_BASE_URL", "http://localhost:8000")
    REDIS_URL: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    DATABASE_URL: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:database@localhost:5432/ats_db",
    )

    # Bot behavior settings
    MAX_PDF_SIZE_MB: int = int(os.environ.get("MAX_PDF_SIZE_MB", "5"))
    JOB_PAGE_SIZE: int = int(os.environ.get("JOB_PAGE_SIZE", "5"))
    ALERT_HOUR: int = int(os.environ.get("ALERT_HOUR", "9"))  # 9AM UTC
    REQUEST_TIMEOUT_S: int = int(os.environ.get("REQUEST_TIMEOUT_S", "60"))
    MAX_JOB_RESULTS: int = int(os.environ.get("MAX_JOB_RESULTS", "50"))


config = Config()
