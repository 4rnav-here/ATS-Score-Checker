from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import DATABASE_URL

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

# ── Session factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── FastAPI dependency ────────────────────────────────────────────────────────
async def get_db():
    """Yield an async DB session, closed automatically after request."""
    async with AsyncSessionLocal() as session:
        yield session
