import os
from dotenv import load_dotenv, find_dotenv

# find_dotenv() walks UP from this file's location until it finds .env,
# so it works regardless of which directory uvicorn is launched from.
load_dotenv(find_dotenv(usecwd=False), override=True)

# ── Sentence-BERT model ──────────────────────────────────────────────────────
MODEL_NAME: str = os.getenv("MODEL_NAME", "all-MiniLM-L6-v2")

# ── Local LLM ────────────────────────────────────────────────────────────────
LLM_MODEL: str = os.getenv("LLM_MODEL", "mistral:latest")

# ── Database ─────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:database@localhost:5432/ats_db",
)

# ── Scoring weights (import these — never hardcode in services) ──────────────
SEMANTIC_WEIGHT: float = float(os.getenv("SEMANTIC_WEIGHT", "0.7"))
KEYWORD_WEIGHT: float = float(os.getenv("KEYWORD_WEIGHT", "0.3"))

SECTION_WEIGHTS: dict[str, float] = {
    "skills": 0.35,
    "experience": 0.30,
    "projects": 0.20,
    "education": 0.10,
    "summary": 0.05,
}

# ── Format penalty ───────────────────────────────────────────────────────────
FORMAT_PENALTY_MAX: float = 15.0

# ── Adzuna Job Search API ────────────────────────────────────────────────────
ADZUNA_APP_ID: str = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_API_KEY: str = os.getenv("ADZUNA_API_KEY", "")

# ── RapidAPI (JSearch — LinkedIn/Indeed India aggregator) ────────────────────
RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY", "")

# ── Job search settings ──────────────────────────────────────────────────────
MAX_JOB_RESULTS: int = int(os.getenv("MAX_JOB_RESULTS", "15"))

# ── JWT / Auth ───────────────────────────────────────────────────────────────
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE-ME-in-production-use-openssl-rand-hex-32")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# ── SMTP (Email OTP Delivery) ────────────────────────────────────────────────
SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))  # Mailpit default
SMTP_USER: str = os.getenv("SMTP_USER", "")
SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@ats-analyzer.local")
SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "false").lower() == "true"

# ── Redis ────────────────────────────────────────────────────────────────────
REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# ── OTP Settings ─────────────────────────────────────────────────────────────
OTP_EXPIRE_MINUTES: int = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
OTP_MAX_ATTEMPTS: int = int(os.getenv("OTP_MAX_ATTEMPTS", "5"))

# ── Rate Limiting ────────────────────────────────────────────────────────────
OTP_RATE_LIMIT_PER_HOUR: int = int(os.getenv("OTP_RATE_LIMIT_PER_HOUR", "5"))
VERIFY_RATE_LIMIT_PER_HOUR: int = int(os.getenv("VERIFY_RATE_LIMIT_PER_HOUR", "10"))
