from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.database import Base, engine
from app.core.logger import logger
from app.models import auth_models  # noqa: F401 — ensure auth tables are registered
from app.routers import alerts, analyze, auth, feedback, interview, jobs, rewrite


# ── Lifespan: create tables on startup, dispose engine on shutdown ────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized (create_all).")
    yield
    await engine.dispose()
    logger.info("Database engine disposed.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="ATS Analyzer API",
    description="AI-powered resume ATS scoring engine — Phase 1",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,      prefix="/api", tags=["Auth"])
app.include_router(analyze.router,   prefix="/api", tags=["Analyze"])
app.include_router(feedback.router,  prefix="/api", tags=["Feedback"])
app.include_router(jobs.router,      prefix="/api", tags=["Jobs"])
app.include_router(alerts.router,    prefix="/api", tags=["Alerts"])
app.include_router(interview.router, prefix="/api", tags=["Interview"])
app.include_router(rewrite.router,   prefix="/api", tags=["Rewrite"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "2.0.0"}
