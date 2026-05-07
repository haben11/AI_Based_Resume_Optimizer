# CV Optimizer AI

A production-ready resume optimization system using FastAPI and RAG (Retrieval-Augmented Generation).

## Features
- **PDF/DOCX Parsing**: Extract text from common resume formats.
- **RAG Pipeline**: Uses ChromaDB and Gemini 1.5 Pro to tailor resumes based on specific job descriptions.
- **Structured Logging**: Production-grade observability with `structlog`.
- **Async API**: High-performance endpoints built with FastAPI.

## Tech Stack
- **Backend**: FastAPI, Pydantic
- **AI/LLM**: LangChain, Google Gemini (GenAI)
- **Vector Store**: ChromaDB
- **Parsing**: PyPDF, docx2txt

## Setup

1. **Install Dependencies** (using `uv`):
   ```bash
   uv pip install -r requirements.txt
   ```

2. **Configuration**:
   - Copy `.env.example` to `.env`
   - Add your `GOOGLE_API_KEY` and PostgreSQL credentials to `.env`

3. **Database Migrations**:
   ```bash
   # Initialize migrations
   uv run alembic revision --autogenerate -m "Initial migration"
   # Apply migrations
   uv run alembic upgrade head
   ```

4. **Run the Application**:
   ```bash
   uv run uvicorn app.main:app --reload
   ```

## API Usage

### 1. Upload Resume
`POST /api/v1/optimize/upload`
- Body: `file` (Multipart)
- Returns: `resume_id`

### 2. Optimize Resume
`POST /api/v1/optimize/optimize`
- Body:
  ```json
  {
    "resume_id": "uuid-here",
    "job_description": "Paste the job description here"
  }
  ```
- Returns: `optimized_cv` (Markdown)
