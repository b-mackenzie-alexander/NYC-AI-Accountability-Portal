# CLAUDE.md
## NYC AI Accountability Portal

This file tells Claude Code how to work in this repository.

---

## Project Summary

A public-facing transparency tool that ingests NYC agency AI disclosure PDFs, cross-references them against NYC Open Data outcome statistics, and surfaces bias signals and disclosure gaps. Demo focused on ACS (Administration for Children's Services).

Full context: see `PRD.md`, `ARCHITECTURE.md`, `ROADMAP.md`.

---

## Repository Structure

```
/
├── backend/          Python 3.11 + FastAPI
├── frontend/         Next.js 14 (App Router)
├── supabase/         Migration SQL files
└── .github/          CI workflows + CODEOWNERS
```

---

## Running the Project

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in real values
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local    # fill in real values
npm run dev
```
App: http://localhost:3000

### Running Tests
```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm run test
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, pdfplumber, openai SDK (pointed at xAI Grok) |
| Frontend | Next.js 14 App Router, TypeScript, Recharts, Tailwind CSS |
| Database | Supabase (Postgres + Storage) |
| LLM | Grok API (xAI) — OpenAI-compatible, free tier |
| Data | NYC Open Data via Socrata REST API |
| Analysis | pandas, scipy |

---

## Code Conventions

### Python (backend)
- Formatter: `ruff format` (runs in CI)
- Linter: `ruff check` (runs in CI)
- Type checker: `mypy` (strict mode where possible)
- All route handlers must be `async`
- Pydantic models for all request/response bodies
- No raw SQL — use the Supabase Python client
- Environment variables via `python-dotenv`; never hardcode values

### TypeScript (frontend)
- Formatter/linter: ESLint + Prettier (configured in `frontend/.eslintrc`)
- Type checker: `tsc --noEmit` (runs in CI)
- Server components by default; add `'use client'` only when required
- Fetch helpers in `lib/api.ts` — never call `fetch()` directly in components
- No `any` types — use `unknown` and narrow

### General
- No comments explaining what code does — only why when it's non-obvious
- No console.log/print statements in committed code
- Feature branches: `feat/[name]/[feature]` — PRs target `develop`, not `main`

---

## Security Rules

These are non-negotiable. Do not work around them:

1. **No secrets in code.** All API keys, tokens, and connection strings go in `.env` / `.env.local`. These files are gitignored. `.env.example` contains only placeholder names.
2. **No PII in the complaints table.** The form has no name/email/phone fields. No IP addresses are logged. Do not add these fields.
3. **Supabase service key is backend-only.** Never reference `SUPABASE_SERVICE_KEY` in frontend code.
4. **Input sanitization on all text fields before DB insert.** Strip HTML. Use the sanitization utility in `backend/app/services/sanitize.py`.
5. **Rate limiting on mutating endpoints.** `slowapi` is configured in `main.py`. Do not remove rate limit decorators from `/complaints` POST or `/disclosures/upload`.
6. **File upload validation.** PDF only, 10MB max. These checks live in `backend/app/routes/disclosures.py` — do not weaken them.

---

## LLM Integration

The Grok client is initialized in `backend/app/services/grok_client.py`. It uses the `openai` SDK:

```python
from openai import AsyncOpenAI
client = AsyncOpenAI(
    api_key=os.environ["GROK_API_KEY"],
    base_url="https://api.x.ai/v1",
)
```

The extraction prompt is in `backend/app/services/extraction_prompt.py`. Do not modify the prompt schema without updating the Pydantic model in `backend/app/models/disclosure.py`.

If the Grok API returns a non-JSON response or fails validation, raise `HTTPException(status_code=422)` — do not silently store malformed data.

---

## Data Provenance Rules

Every `bias_signal` row must have at least one entry in `source_urls`. The signal generation service enforces this — do not bypass it.

`extraction_confidence < 0.7` must surface a warning badge in the UI. The threshold is defined in `frontend/lib/constants.ts`.

---

## Branch & Review Rules

```
main     ← requires 2 approvals + all CI green
develop  ← requires 1 approval + all CI green
feat/*   ← open PRs against develop only
```

CODEOWNERS:
- `/backend/` → @saul, @beatrice
- `/frontend/` → @william, @beatrice
- `/supabase/` → @sonia, @beatrice
- `/.github/` → @beatrice

Do not merge your own PRs.

---

## CI Checks (must all pass before merge)

**On backend changes:**
- `ruff check backend/`
- `mypy backend/app/`
- `pytest backend/tests/ -v`
- `bandit -r backend/app/`

**On frontend changes:**
- `eslint frontend/`
- `tsc --noEmit` (from `frontend/`)
- `vitest run` (from `frontend/`)
- `npm audit --audit-level=high` (from `frontend/`)

**On all PRs:**
- `gitleaks detect`
- `trivy fs .`

---

## Known Constraints

- **Grok free tier rate limits:** If extraction fails with a 429, retry once with `grok-3-mini`. The model is configurable via `GROK_MODEL` env var.
- **Scanned PDFs:** `pdfplumber` cannot extract text from image-only PDFs. If extracted text is < 100 characters, return HTTP 422 with message `"PDF appears to be scanned. Text extraction not supported."`
- **Socrata dataset IDs:** IDs are stored in `backend/app/data/socrata_datasets.json`. Verify these against live data.cityofnewyork.us before running ingest.
- **Disparity reference group:** Always `"White Non-Hispanic"`. If this group is absent from a dataset, skip ratio calculation and log a warning — do not use a different reference group.

---

## Team

| Person | Role | Owns |
|---|---|---|
| Beatrice | CI/CD, Security, Testing | `.github/`, integration |
| Saul | Python Backend | `backend/` |
| Sonia | Supabase, Data | `supabase/`, seed data |
| William | Next.js Frontend | `frontend/` |
