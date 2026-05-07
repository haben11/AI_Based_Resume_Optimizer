# AI-Based Resume Optimizer

A production-grade, full-stack AI application that transforms a generic resume into a precisely tailored, ATS-optimized document for any job description — in real time.

Built with a **FastAPI** backend powered by a multi-phase RAG pipeline (Google Gemini + ChromaDB + PostgreSQL) and a **Next.js 16** frontend with live streaming output.

---

## Table of Contents

- [What It Does](#what-it-does)
- [System Architecture](#system-architecture)
- [Feature Breakdown](#feature-breakdown)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Local Setup](#local-setup)
  - [Prerequisites](#prerequisites)
  - [1 — Clone the Repository](#1--clone-the-repository)
  - [2 — Backend Setup](#2--backend-setup)
  - [3 — Database Setup](#3--database-setup)
  - [4 — Seed the Knowledge Base](#4--seed-the-knowledge-base)
  - [5 — Frontend Setup](#5--frontend-setup)
  - [6 — Run the Application](#6--run-the-application)
- [Environment Variables Reference](#environment-variables-reference)
- [API Reference](#api-reference)
- [Authentication Flow](#authentication-flow)
- [RAG Pipeline Deep Dive](#rag-pipeline-deep-dive)
- [Semantic Caching](#semantic-caching)
- [Knowledge Base](#knowledge-base)
- [Resume Templates](#resume-templates)
- [Running Tests](#running-tests)
- [Production Deployment Notes](#production-deployment-notes)

---

## What It Does

1. **Upload** your current resume (PDF or DOCX).
2. **Paste** a job description for the role you want.
3. The system **streams** a fully rewritten, ATS-optimized resume back to you in real time — tailored to that specific job.
4. **Choose** from 8 professional resume templates, pick an accent color, and **download** as PDF or DOCX.

Under the hood the system:

- Semantically chunks and indexes your resume into a vector store.
- Extracts structured requirements from the job description (skills, years of experience, seniority).
- Runs a hybrid BM25 + semantic search to retrieve the most relevant resume sections.
- Re-ranks results with a cross-encoder model.
- Grounds the generation with live data from a 80 000-row knowledge base (ESCO skills, job titles, ATS keywords, action verbs, industry metrics).
- Generates the optimized resume via Google Gemini with streaming tokens.
- Validates the output (word count, action verbs, quantifiable metrics, quality score).
- Detects hallucinations — fabricated claims not present in the original resume.
- Scrubs PII before sending context to the LLM, then restores it in the final output.
- Caches semantically similar requests (exact hash + cosine similarity) to cut LLM costs by 30–60 %.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Next.js 16 Frontend                       │
│  Upload → Job Description → Live SSE Stream → Template Picker   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / SSE
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend  (/api/v1)                  │
│                                                                  │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │   Auth   │  │  CV Optimizer│  │   Structured Resume API  │  │
│  │  /auth   │  │  /optimize   │  │        /resumes          │  │
│  └──────────┘  └──────┬───────┘  └──────────────────────────┘  │
│                        │                                         │
│  ┌─────────────────────▼──────────────────────────────────────┐ │
│  │                  RAG Pipeline (v3)                          │ │
│  │                                                             │ │
│  │  Semantic Chunker → Hybrid Search (BM25 + Vector)          │ │
│  │  → Cross-Encoder Re-rank → Dynamic Grounding               │ │
│  │  → PII Scrub → Gemini Generation (streaming)               │ │
│  │  → PII Restore → Validation → Hallucination Detection      │ │
│  │  → Semantic Cache Store                                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  PostgreSQL  │  │   ChromaDB   │  │   Google Gemini API  │  │
│  │  (metadata,  │  │  (vectors)   │  │  (embeddings + LLM)  │  │
│  │  cache, KB)  │  │              │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature Breakdown

### AI & RAG Pipeline

| Feature | Description |
|---|---|
| Semantic chunking | Splits resumes into meaningful sections (experience, skills, education, etc.) with overlap |
| Hybrid search | Combines BM25 keyword search (40 %) + semantic vector search (60 %) for best recall |
| Cross-encoder re-ranking | `ms-marco-MiniLM-L-6-v2` re-scores top candidates for precision |
| Multi-vector embeddings | Aspect-aware embeddings (skills, experience, achievements) for 15–25 % better matching |
| Dynamic grounding | Enriches prompts with live ATS keywords, action verbs, salary data, and certifications from the knowledge base |
| PII scrubbing | Masks names, emails, and phone numbers before sending to Google; restores them in the final output |
| Output validation | Checks word count, section completeness, action verb density, and quantifiable metrics |
| Hallucination detection | Flags claims in the generated resume that cannot be traced back to the original |
| Streaming output | Server-Sent Events (SSE) stream tokens to the browser in real time with progress stages |

### Semantic Caching

| Feature | Description |
|---|---|
| Exact match | SHA-256 hash lookup — sub-millisecond response for identical queries |
| Semantic match | Cosine similarity on Gemini embeddings — cache hit if similarity ≥ 0.85 |
| TTL | 7-day default, configurable up to 30 days |
| Statistics | Hit rate, cost savings, time savings tracked per day |
| Replay protection | Revoked tokens cannot be reused; all user tokens revoked on replay detection |

### Authentication

| Feature | Description |
|---|---|
| Access token | 1-day JWT, returned in response body, stored in memory + localStorage |
| Refresh token | 30-day opaque token, stored as HttpOnly cookie (SHA-256 hash in DB) |
| Token rotation | Every `/refresh` call issues a new token and revokes the old one |
| Auto-refresh | Frontend interceptor silently refreshes on `401 token_expired` and retries the original request |
| Logout | Revokes the refresh token in the database and clears the cookie |

### Resume Templates

8 professionally designed HTML/CSS templates rendered to PDF via Playwright:

| Template | Style |
|---|---|
| Vienna Luxury | Executive serif, prestige layout |
| Tokyo Minimal | Tech-focused grid, clean whitespace |
| Modern Sidebar | Two-column with colored sidebar |
| Modern Split | Bold header, impactful layout |
| Executive Serif | Classic leadership style |
| Creative Vision | Dark mode, bold typography |
| Compact Pro | High information density |
| Centered | Editorial, minimal |

Each template supports 8 accent colors and exports to both PDF and DOCX.

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.110 + Uvicorn |
| LLM | Google Gemini 2.5 Flash Lite |
| Embeddings | Google `gemini-embedding-001` |
| Vector store | ChromaDB 0.4 |
| Hybrid search | BM25 (`rank-bm25`) + ChromaDB |
| Re-ranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` (sentence-transformers) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Database | PostgreSQL 15 |
| Auth | python-jose (JWT) + passlib (bcrypt) |
| PDF generation | Playwright (headless Chromium) |
| DOCX generation | python-docx |
| Logging | structlog |
| Validation | Pydantic v2 |

### Frontend

| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript 5 |
| Styling | Tailwind CSS v4 |
| Animations | Framer Motion |
| Icons | Lucide React |
| Notifications | Sonner |
| Drag & drop | dnd-kit |
| Markdown | react-markdown |

---

## Project Structure

```
cv_optimizer/
├── cv-optimizer-backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py                  # Auth dependency (get_current_user)
│   │   │   └── v1/
│   │   │       ├── api.py               # Router registration
│   │   │       └── endpoints/
│   │   │           ├── auth.py          # Login, refresh, logout, register
│   │   │           ├── cv_optimizer.py  # Upload, optimize, stream, download
│   │   │           ├── structured_resume.py
│   │   │           └── users.py
│   │   ├── core/
│   │   │   ├── config.py               # Settings (env vars)
│   │   │   ├── security.py             # JWT + refresh token helpers
│   │   │   ├── logging.py              # structlog setup
│   │   │   └── rag_config.py           # RAG pipeline configuration
│   │   ├── db/
│   │   │   ├── base.py                 # Model registry for Alembic
│   │   │   ├── session.py              # SQLAlchemy engine + SessionLocal
│   │   │   └── vector_store_manager.py # ChromaDB manager
│   │   ├── ml/
│   │   │   ├── embedding_manager.py    # Fine-tuned embedding wrapper
│   │   │   ├── multi_vector_embeddings.py
│   │   │   └── hallucination_detector.py
│   │   ├── models/
│   │   │   ├── user.py
│   │   │   ├── resume.py
│   │   │   ├── refresh_token.py        # HttpOnly cookie token store
│   │   │   ├── knowledge_base.py       # ATS keywords, skills, job titles, etc.
│   │   │   └── semantic_cache.py
│   │   ├── schemas/                    # Pydantic request/response models
│   │   ├── scripts/
│   │   │   ├── seed_knowledge_base.py  # Basic seed data
│   │   │   └── seed_kb_esco.py         # ESCO + HuggingFace dataset seeder
│   │   ├── services/
│   │   │   ├── rag_service_v3.py       # Core RAG pipeline
│   │   │   ├── streaming_rag_service.py # SSE streaming wrapper
│   │   │   ├── semantic_cache_service.py
│   │   │   ├── dynamic_grounding_service.py
│   │   │   └── resume_service.py
│   │   ├── templates/                  # HTML resume templates (8 designs)
│   │   └── utils/
│   │       ├── semantic_chunker.py
│   │       ├── hybrid_search.py
│   │       ├── cross_encoder_reranker.py
│   │       ├── query_processor.py
│   │       ├── output_validator.py
│   │       ├── pii_scrubber.py
│   │       ├── pdf_generator.py        # Playwright PDF renderer
│   │       ├── docx_generator.py
│   │       └── template_factory.py
│   ├── alembic/
│   │   └── versions/                   # Database migrations
│   ├── evals/                          # RAGAS evaluation suite
│   ├── tests/
│   ├── .env.example
│   ├── requirements.txt
│   └── docker-compose.yml
│
└── cv-opt-frontend/
    ├── app/
    │   ├── dashboard/
    │   │   ├── page.tsx                # Main optimizer UI
    │   │   ├── history/page.tsx        # Optimization history
    │   │   └── profile/page.tsx
    │   ├── login/page.tsx
    │   ├── signup/page.tsx
    │   └── layout.tsx
    ├── components/
    │   ├── DashboardShell.tsx
    │   ├── Navbar.tsx
    │   └── TemplateCard.tsx
    └── lib/
        ├── api.ts                      # API client with auto token refresh
        ├── auth-context.tsx            # React auth state
        └── streaming-api.ts            # SSE streaming hook
```

---

## Local Setup

### Prerequisites

Make sure you have the following installed:

| Tool | Version | Notes |
|---|---|---|
| Python | 3.11+ | Use `pyenv` or the official installer |
| Node.js | 18+ | Use `nvm` or the official installer |
| PostgreSQL | 15+ | Running locally on port 5432 |
| Git | any | |

You also need a **Google AI API key** with access to Gemini models. Get one free at [aistudio.google.com](https://aistudio.google.com).

---

### 1 — Clone the Repository

```bash
git clone https://github.com/your-username/AI_Based_Resume_Optimizer.git
cd AI_Based_Resume_Optimizer
```

---

### 2 — Backend Setup

```bash
cd cv-optimizer-backend

# Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright's headless browser (required for PDF generation)
playwright install chromium
```

**Create your environment file:**

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```env
# ── AI ────────────────────────────────────────────────────────────
GOOGLE_API_KEY=your_google_ai_api_key_here

# ── Security ──────────────────────────────────────────────────────
# Generate a strong secret: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256

# ── Token lifetimes ───────────────────────────────────────────────
ACCESS_TOKEN_EXPIRE_MINUTES=1440    # 1 day
REFRESH_TOKEN_EXPIRE_DAYS=30

# ── Environment ───────────────────────────────────────────────────
# "development" = cookie without Secure flag (works over HTTP)
# "production"  = cookie with Secure + SameSite=None (requires HTTPS)
ENVIRONMENT=development

# ── Database ──────────────────────────────────────────────────────
POSTGRES_SERVER=127.0.0.1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_postgres_password
POSTGRES_DB=cv_optimizer

# ── Storage ───────────────────────────────────────────────────────
CHROMA_DB_DIR=data/chroma_db
UPLOAD_DIR=data/uploads
```

---

### 3 — Database Setup

Create the PostgreSQL database:

```bash
# Connect to PostgreSQL
psql -U postgres

# Inside psql
CREATE DATABASE cv_optimizer;
\q
```

Run all Alembic migrations to create the schema:

```bash
# Make sure your .venv is active and you are in cv-optimizer-backend/
python -m alembic upgrade head
```

This creates the following tables:

- `users` — registered accounts
- `resumes` — uploaded resume files
- `optimization_histories` — past optimization results
- `refresh_tokens` — HttpOnly cookie token store
- `industry_skills` — ESCO skill taxonomy
- `job_title_data` — 67 000+ job titles
- `ats_keywords` — 13 000+ ATS-optimized keywords
- `action_verbs`, `industry_metrics`, `certifications`, `company_data`, `education_data`
- `semantic_cache_entries`, `cache_statistics`
- `structured_resumes`, `resume_sections`, `bullet_points`, etc.

---

### 4 — Seed the Knowledge Base

The RAG pipeline uses a knowledge base to ground its output. Seed it with ESCO taxonomy data and 65 000 real-world job titles from HuggingFace:

```bash
# This downloads ~3 datasets from HuggingFace and inserts ~80 000 rows.
# Takes 3–5 minutes depending on your internet connection.
python -m app.scripts.seed_kb_esco
```

Expected output:

```
============================================================
ESCO Knowledge Base Seeder v2.0
============================================================

[1/3] Seeding ESCO skills...
      ✓ 13,824 new skills inserted

[2/3] Seeding ESCO occupations...
      ✓ 2,409 new occupations inserted

[3/3] Seeding job titles (65k)...
      ✓ 65,245 new job titles inserted

============================================================
Seeding complete!  Total new rows: 81,478
============================================================
```

> **Note:** You only need to run this once. Re-running it is safe — it skips existing entries.

---

### 5 — Frontend Setup

```bash
cd ../cv-opt-frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local
```

If `.env.example` doesn't exist, create `.env.local` manually:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

### 6 — Run the Application

Open **two terminals**.

**Terminal 1 — Backend:**

```bash
cd cv-optimizer-backend
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

**Terminal 2 — Frontend:**

```bash
cd cv-opt-frontend
npm run dev
```

You should see:

```
▲ Next.js 16.2.4
- Local:        http://localhost:3000
- Ready in 2.1s
```

**Open your browser at [http://localhost:3000](http://localhost:3000)**

The API documentation (Swagger UI) is available at [http://localhost:8000/api/v1/openapi.json](http://localhost:8000/docs).

---

## Environment Variables Reference

### Backend (`cv-optimizer-backend/.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `GOOGLE_API_KEY` | ✅ | — | Google AI Studio API key |
| `SECRET_KEY` | ✅ | — | JWT signing secret (min 32 chars) |
| `ALGORITHM` | | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | | `1440` | Access token lifetime (1 day) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | | `30` | Refresh token lifetime |
| `ENVIRONMENT` | | `development` | `development` or `production` |
| `REFRESH_COOKIE_NAME` | | `refresh_token` | HttpOnly cookie name |
| `POSTGRES_SERVER` | ✅ | `db` | PostgreSQL host |
| `POSTGRES_USER` | ✅ | `postgres` | PostgreSQL user |
| `POSTGRES_PASSWORD` | ✅ | — | PostgreSQL password |
| `POSTGRES_DB` | ✅ | `cv_optimizer` | Database name |
| `SQLALCHEMY_DATABASE_URI` | | — | Full DB URI (overrides individual fields) |
| `CHROMA_DB_DIR` | | `data/chroma_db` | ChromaDB persistence directory |
| `UPLOAD_DIR` | | `data/uploads` | Resume upload directory |

### Frontend (`cv-opt-frontend/.env.local`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL` | | `http://localhost:8000` | Backend base URL |

---

## API Reference

All endpoints are prefixed with `/api/v1`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/login/access-token` | Login — returns JWT, sets refresh cookie |
| `POST` | `/auth/refresh` | Exchange refresh cookie for new access token |
| `POST` | `/auth/logout` | Revoke refresh token, clear cookie |
| `POST` | `/auth/register` | Create new account |
| `POST` | `/auth/password-recovery/{email}` | Request password reset |
| `POST` | `/auth/reset-password/` | Reset password with token |

### Users

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/me` | Get current user profile |
| `PUT` | `/users/me` | Update profile |

### CV Optimizer

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/optimize/upload` | Upload resume (PDF/DOCX) |
| `POST` | `/optimize/optimize` | Optimize resume (non-streaming) |
| `POST` | `/optimize/optimize/stream` | Optimize resume (SSE streaming) |
| `POST` | `/optimize/snippet` | Regenerate a selected text snippet |
| `GET` | `/optimize/history` | Get optimization history |
| `GET` | `/optimize/resume/{id}` | Get resume details |
| `GET` | `/optimize/resume/{id}/preview` | Get HTML preview for a template |
| `GET` | `/optimize/resume/{id}/download` | Download PDF or DOCX |
| `GET` | `/optimize/cache/statistics` | View cache metrics |
| `POST` | `/optimize/cache/cleanup` | Manually expire old cache entries |
| `DELETE` | `/optimize/cache/clear` | Clear all cache entries |

---

## Authentication Flow

```
Login
  │
  ├─► POST /auth/login/access-token
  │     Body: { username, password }
  │     Response: { access_token }  +  Set-Cookie: refresh_token (HttpOnly)
  │
  └─► Store access_token in memory + localStorage

Every API request
  │
  ├─► Authorization: Bearer <access_token>
  │
  └─► If 401 + detail:"token_expired"
        │
        ├─► POST /auth/refresh  (cookie sent automatically)
        │     Response: { access_token }  +  new Set-Cookie
        │
        └─► Retry original request with new token

Logout
  │
  └─► POST /auth/logout  (cookie sent automatically)
        Backend revokes token in DB, clears cookie
        Frontend clears localStorage
```

---

## RAG Pipeline Deep Dive

The optimization pipeline runs in 9 stages, each reported as a progress event to the frontend:

```
1. Cache check        — exact hash + semantic similarity lookup
2. Grounding          — fetch ATS keywords, skills, action verbs from KB
3. Query processing   — extract requirements, skills, experience years
4. Retrieval          — hybrid BM25 + vector search (top 10 candidates)
5. Re-ranking         — cross-encoder scores top 5 final chunks
6. Context building   — assemble prompt context from ranked chunks
7. PII scrubbing      — mask names/emails before sending to Google
8. Generation         — Gemini streams tokens back to the browser
9. Validation         — quality score, hallucination check, PII restore
```

### Configuration Presets

The pipeline ships with four presets you can switch in `rag_config.py`:

| Preset | Use case |
|---|---|
| `balanced` (default) | Good quality and speed |
| `high_precision` | Maximum quality, slower |
| `high_recall` | Maximum coverage, more context |
| `fast` | Minimum latency, skips hallucination check |

---

## Semantic Caching

Every optimization result is cached by:

1. **Exact match** — SHA-256 hash of the job description. Identical queries return instantly.
2. **Semantic match** — Cosine similarity of Gemini embeddings. Queries that are ≥ 85 % similar return the cached result.

Cache entries expire after 7 days by default. Statistics are tracked daily:

```
GET /api/v1/optimize/cache/statistics

{
  "total_queries": 1240,
  "cache_hits": 743,
  "hit_rate": 59.9,
  "exact_matches": 312,
  "semantic_matches": 431,
  "avg_similarity_score": 0.91,
  "total_cost_saved": 7.43,
  "total_time_saved_hours": 6.2
}
```

---

## Knowledge Base

The knowledge base is seeded from three public datasets:

| Table | Source | Rows |
|---|---|---|
| `industry_skills` | TechWolf/Synthetic-ESCO-skill-sentences | ~13 800 |
| `job_title_data` | danieldux/ESCO + gpriday/job-titles | ~67 600 |
| `ats_keywords` | Derived from ESCO skills | ~13 800 |

Re-seed at any time:

```bash
python -m app.scripts.seed_kb_esco
```

---

## Resume Templates

Templates are Jinja2 HTML files rendered to PDF by Playwright (headless Chromium). Each template:

- Accepts a `color` parameter (8 options: blue, slate, emerald, indigo, rose, amber, violet, cyan)
- Renders to a pixel-perfect A4 PDF
- Also exports to DOCX via `python-docx`

To add a new template, create an HTML file in `app/templates/` and register it in `app/utils/template_factory.py`.

---

## Running Tests

```bash
cd cv-optimizer-backend
.venv\Scripts\activate

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run semantic cache tests specifically
pytest tests/test_semantic_cache.py -v
```

---

## Production Deployment Notes

### Environment

Set `ENVIRONMENT=production` in your `.env`. This enables:

- `Secure=True` on the refresh token cookie
- `SameSite=None` for cross-origin cookie support
- Explicit CORS origin list (update `ALLOWED_ORIGINS` in `main.py`)

### Security checklist

- [ ] Generate a strong `SECRET_KEY`: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Set `ENVIRONMENT=production`
- [ ] Replace `allow_origins=["*"]` with your actual frontend domain in `main.py`
- [ ] Use a managed PostgreSQL instance (RDS, Supabase, Neon, etc.)
- [ ] Store `GOOGLE_API_KEY` in a secrets manager, not in `.env`
- [ ] Enable HTTPS on both frontend and backend
- [ ] Set up a periodic job to call `POST /optimize/cache/cleanup` to expire old cache entries

### Docker

A `docker-compose.yml` is included in `cv-optimizer-backend/` for running the backend + PostgreSQL together:

```bash
cd cv-optimizer-backend
docker compose up -d
```

---

## License

MIT
