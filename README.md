# 📄 ATS Resume Analyzer

An **AI-powered Applicant Tracking System (ATS) Resume Analyzer** that scores resumes against job descriptions using NLP, TF-IDF keyword matching, and Sentence-BERT semantic similarity. The system features a **FastAPI backend**, a **Next.js frontend**, and a **Telegram bot** for on-the-go resume analysis and intelligent job search alerts.

---

## 🏗️ Architecture Overview

```
┌──────────────────────┐     ┌──────────────────────┐
│   Next.js Frontend   │────▶│   FastAPI Backend     │
│   (Port 3000)        │     │   (Port 8000)         │
└──────────────────────┘     └────────┬──────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                  ▼
             ┌────────────┐   ┌────────────┐   ┌──────────────┐
             │ PostgreSQL │   │   Redis    │   │   Ollama     │
             │  (5432)    │   │  (6379)    │   │  LLM Server  │
             └────────────┘   └────────────┘   └──────────────┘
                                      │
                              ┌───────┴────────┐
                              ▼                ▼
                     ┌──────────────┐  ┌──────────────┐
                     │ Telegram Bot │  │Job Scheduler │
                     └──────────────┘  └──────────────┘
```

## ✨ Features

### Core — ATS Scoring Engine
- **PDF Resume Parsing** — Extracts text, sections, and metadata from uploaded resumes via `pdfplumber`
- **Section-Aware NLP** — Detects resume sections (Experience, Education, Skills, etc.) using spaCy
- **Keyword Matching** — TF-IDF based keyword extraction and matching against job descriptions
- **Semantic Similarity** — Sentence-BERT embeddings for deep meaning comparison
- **Improvement Suggestions** — AI-generated recommendations to boost your ATS score
- **Format Penalty Detection** — Flags formatting issues that ATS systems penalize

### Authentication
- **Passwordless OTP Login** — Email-based one-time password authentication
- **2FA / TOTP Support** — Optional two-factor authentication via authenticator apps
- **JWT Token Auth** — Access + refresh token flow with secure session management

### Telegram Bot
- **Resume Analysis** — Upload PDFs directly in Telegram for instant ATS scoring
- **Intelligent Job Search** — AI-powered job matching using Adzuna API
- **Scheduled Job Alerts** — Daily job notifications based on your resume profile
- **Interactive Feedback** — Rate and review analysis results

### Frontend
- **Modern UI** — Next.js 16 with React 19 and Tailwind CSS 4
- **Resume Upload & Analysis** — Drag-and-drop PDF upload with real-time scoring
- **Results Dashboard** — Detailed score breakdown with visual charts
- **Auth Flow** — Login, OTP verification, and 2FA setup pages

---

## 📋 Prerequisites

Before running the application, ensure you have the following installed:

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Backend & Telegram Bot |
| **Node.js** | 18+ | Frontend (Next.js) |
| **PostgreSQL** | 15+ | Primary database |
| **Redis** | 7+ | Caching, rate limiting, session store |
| **Ollama** | Latest | Local LLM for AI-powered suggestions |
| **Docker** *(optional)* | Latest | Run everything via `docker-compose` |

### External API Keys (Optional)

| Service | Purpose | Get it at |
|---------|---------|-----------|
| **Adzuna API** | Job search integration | [developer.adzuna.com](https://developer.adzuna.com) |
| **Telegram Bot Token** | Telegram bot | [@BotFather](https://t.me/BotFather) |

---

## 🚀 Getting Started

### Option A — Docker Compose (Recommended)

The easiest way to get everything running with a single command.

#### 1. Clone the repository

```bash
git clone https://github.com/4rnav-here/ATS-Score-Checker.git
cd ATS-Score-Checker
```

#### 2. Create the environment file

```bash
cp .env .env.local   # or create a new .env in the project root
```

Edit `.env` and fill in the required values:

```env
# ── Required ──────────────────────────────────
DATABASE_URL=postgresql+asyncpg://postgres:database@postgres:5432/ats_db
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=your-secret-key-run-openssl-rand-hex-32

# ── Optional (for Telegram Bot) ──────────────
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_API_KEY=your_adzuna_api_key

# ── LLM Model ────────────────────────────────
LLM_MODEL=mistral:latest
```

#### 3. Start all services

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port `5432`
- **Redis** on port `6379`
- **FastAPI Backend** on port `8000`
- **Mailpit** (dev email) — Web UI on port `8025`, SMTP on port `1025`
- **Telegram Bot** (if token provided)
- **Job Scheduler** (daily job alerts)

#### 4. Access the application

| Service | URL |
|---------|-----|
| Backend API | [http://localhost:8000](http://localhost:8000) |
| API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| Mailpit (dev emails) | [http://localhost:8025](http://localhost:8025) |
| Health Check | [http://localhost:8000/health](http://localhost:8000/health) |

> **Note:** The frontend needs to be run separately (see below) as it is not yet containerized.

---

### Option B — Manual Setup (Development)

Run each component individually for local development with hot-reload.

#### 1. Clone the repository

```bash
git clone https://github.com/4rnav-here/ATS-Score-Checker.git
cd ATS-Score-Checker
```

---

#### 2. Start Infrastructure Services

Start PostgreSQL and Redis. You can use Docker for just these services:

```bash
docker run -d --name ats-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=database \
  -e POSTGRES_DB=ats_db \
  -p 5432:5432 \
  postgres:15-alpine

docker run -d --name ats-redis \
  -p 6379:6379 \
  redis:7-alpine
```

Or install and run them natively on your system.

---

#### 3. Start Ollama (LLM Server)

Install Ollama from [ollama.com](https://ollama.com) and pull the model:

```bash
ollama pull mistral:latest
ollama serve   # starts on port 11434 by default
```

---

#### 4. Backend Setup

```bash
cd backend
```

**Create and activate a virtual environment:**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Download spaCy language model:**

```bash
python -m spacy download en_core_web_sm
```

**Set up environment variables:**

Create a `backend/.env` file (or copy from the root `.env`):

```env
DATABASE_URL=postgresql+asyncpg://postgres:database@localhost:5432/ats_db
MODEL_NAME=all-MiniLM-L6-v2
LLM_MODEL=mistral:latest
SEMANTIC_WEIGHT=0.7
KEYWORD_WEIGHT=0.3

# Auth / JWT
JWT_SECRET_KEY=dev-secret-change-me-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# SMTP (Mailpit for dev)
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_FROM=noreply@ats-analyzer.local

# Redis
REDIS_URL=redis://localhost:6379/0

# OTP Settings
OTP_EXPIRE_MINUTES=10
OTP_MAX_ATTEMPTS=5
```

**Run the backend server:**

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000` with Swagger docs at `http://localhost:8000/docs`.

> **Note:** On the first run, the Sentence-BERT model (`all-MiniLM-L6-v2`) will be downloaded automatically (~90 MB). This is a one-time download.

---

#### 5. Frontend Setup

```bash
cd frontend
```

**Install dependencies:**

```bash
npm install
```

**Run the development server:**

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

---

#### 6. Telegram Bot Setup (Optional)

```bash
cd telegram_bot
```

**Install dependencies:**

```bash
pip install -r requirements-bot.txt
```

**Set environment variables** (in root `.env` or export them):

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
API_BASE_URL=http://localhost:8000
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql+asyncpg://postgres:database@localhost:5432/ats_db
```

**Run the bot:**

```bash
python -m telegram_bot.bot
```

**Run the job scheduler** (in a separate terminal):

```bash
python -m telegram_bot.scheduler
```

---

#### 7. Mailpit Setup (Optional — Dev Email Testing)

For testing OTP emails locally:

```bash
docker run -d --name mailpit \
  -p 1025:1025 \
  -p 8025:8025 \
  axllent/mailpit:latest
```

View sent emails at [http://localhost:8025](http://localhost:8025).

---

## 📁 Project Structure

```
ATS-Score-Checker/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── agents/             # AI job search agent + tools
│   │   ├── core/               # Database, config, logger
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── routers/            # API route handlers
│   │   │   ├── analyze.py      #   POST /api/analyze
│   │   │   ├── auth.py         #   Auth endpoints (OTP, 2FA)
│   │   │   ├── feedback.py     #   User feedback
│   │   │   ├── jobs.py         #   Job search
│   │   │   ├── alerts.py       #   Job alerts CRUD
│   │   │   ├── interview.py    #   Interview prep
│   │   │   └── rewrite.py      #   Resume rewriting
│   │   ├── services/           # Business logic
│   │   │   ├── scoring_service.py
│   │   │   ├── nlp_service.py
│   │   │   ├── pdf_service.py
│   │   │   ├── embedding_service.py
│   │   │   ├── auth_service.py
│   │   │   ├── jwt_service.py
│   │   │   └── ...
│   │   └── main.py             # App entrypoint
│   ├── requirements.txt
│   └── .env
│
├── frontend/                   # Next.js 16 frontend
│   ├── app/
│   │   ├── analyze/            # Upload & analyze page
│   │   ├── results/            # Score results dashboard
│   │   ├── login/              # Auth pages
│   │   ├── verify-otp/
│   │   ├── verify-2fa/
│   │   ├── settings/
│   │   └── components/         # Reusable UI components
│   ├── middleware.ts            # Auth middleware
│   └── package.json
│
├── telegram_bot/               # Telegram bot (Phase 2)
│   ├── bot.py                  # Bot entrypoint
│   ├── scheduler.py            # APScheduler job alerts
│   ├── api_client.py           # HTTP client for backend
│   ├── config.py               # Bot configuration
│   ├── handlers/               # Command & message handlers
│   ├── keyboards/              # Inline keyboard builders
│   ├── formatters/             # Message formatting
│   ├── core/                   # Shared bot utilities
│   ├── Dockerfile
│   └── requirements-bot.txt
│
├── docker-compose.yml          # Full-stack orchestration
├── .env                        # Environment variables
├── .gitignore
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/auth/request-otp` | Request OTP login email |
| `POST` | `/api/auth/verify-otp` | Verify OTP and get JWT |
| `POST` | `/api/auth/setup-2fa` | Enable TOTP 2FA |
| `POST` | `/api/auth/verify-2fa` | Verify TOTP code |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `POST` | `/api/analyze` | Upload resume PDF + job description for ATS scoring |
| `POST` | `/api/feedback` | Submit feedback on analysis |
| `GET` | `/api/jobs/search` | Search jobs via Adzuna |
| `POST` | `/api/alerts` | Create a job alert |
| `GET` | `/api/alerts` | List user's job alerts |
| `POST` | `/api/interview/prep` | Generate interview prep questions |

Full interactive API documentation available at `/docs` (Swagger UI) when the backend is running.

---

## ⚙️ Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | — | PostgreSQL async connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `JWT_SECRET_KEY` | — | Secret key for JWT signing (use `openssl rand -hex 32`) |
| `LLM_MODEL` | `mistral:latest` | Ollama model for AI suggestions |
| `MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence-BERT model for embeddings |
| `SEMANTIC_WEIGHT` | `0.7` | Weight for semantic similarity score |
| `KEYWORD_WEIGHT` | `0.3` | Weight for keyword matching score |
| `SMTP_HOST` | `localhost` | SMTP server for OTP emails |
| `SMTP_PORT` | `1025` | SMTP port |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token from BotFather |
| `ADZUNA_APP_ID` | — | Adzuna API application ID |
| `ADZUNA_API_KEY` | — | Adzuna API key |
| `ALERT_HOUR` | `9` | Hour (UTC) for daily job alert emails |

---

## 🧪 Running Tests

```bash
cd backend

# Run unit tests
python -m pytest test_internal.py -v

# Run end-to-end tests (requires running backend)
python -m pytest e2e_test.py -v
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, FastAPI, SQLAlchemy 2 (async), Uvicorn |
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| **Database** | PostgreSQL 15 |
| **Cache / Broker** | Redis 7 |
| **NLP** | spaCy, NLTK, Sentence-Transformers, scikit-learn |
| **LLM** | Ollama (Mistral, Llama 3, etc.) |
| **Auth** | JWT + OTP (pyotp) + TOTP 2FA |
| **Bot** | python-telegram-bot 21, APScheduler |
| **Jobs API** | Adzuna |
| **Email (dev)** | Mailpit |
| **Containerization** | Docker, Docker Compose |

---

## 📝 License

This project is for academic / capstone purposes.
