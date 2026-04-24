# Product Requirements Document
## NYC AI Accountability Portal
**Track:** AI for Justice, Policy & Equity
**Hackathon:** [Event Name]
**Date:** April 24–25, 2026
**Team:** Beatrice (D) · Saul (A) · William (C) · Sonia (B)

---

## 1. Problem Statement

New York City agencies use AI systems to make consequential decisions about child welfare, housing, benefits, and public safety — decisions that disproportionately affect low-income communities and communities of color. Despite legal mandates requiring agencies to disclose their use of automated decision systems, these disclosures are:

- Published as unstructured PDFs with no standardized format
- Incomplete — systems documented in external research are absent from official filings
- Not cross-referenced against outcome data that would reveal disparate impact
- Inaccessible to the residents most affected by these decisions

The NYC GUARD Act (November 2025) created the Office of Algorithmic Data Accountability and mandated a public registry of AI systems used by city agencies. That registry does not yet exist.

**We are building it.**

---

## 2. Solution Overview

A public-facing web application that:

1. **Ingests** government AI disclosure documents (PDFs) and extracts structured data using an LLM pipeline
2. **Cross-references** extracted disclosures against NYC Open Data outcome statistics to surface demographic disparities
3. **Flags** gaps between what agencies have officially disclosed and what is externally documented
4. **Surfaces** findings through a clean, accessible public dashboard — no login required
5. **Accepts** anonymous bias complaints from residents with full privacy preservation

**Demo scope:** Administration for Children's Services (ACS) and the Severe Harm Predictive Risk Model — a documented, controversial AI tool absent from official ACS disclosures.

---

## 3. Goals

### Primary Goals
- Demonstrate a fully working, end-to-end application that ingests real documents, runs real analysis, and surfaces real findings
- Show a verifiable, auditable chain from source document to public-facing claim
- Deploy a live, accessible URL for judges to interact with

### Hackathon Success Criteria
- [ ] PDF upload → LLM extraction → database → API → UI working end to end
- [ ] At least one real bias signal generated from NYC Open Data
- [ ] At least one real disclosure gap surfaced (ACS Severe Harm PRM)
- [ ] Complaint form functional with token return
- [ ] All CI checks passing on `main`
- [ ] Security scan clean
- [ ] Live deployed URL

---

## 4. User Personas

### Persona 1: The Affected Resident
**Name:** Maria
**Situation:** ACS opened an investigation after a school report. The case closed, but she suspects a scoring model influenced how investigators treated her family before they arrived.
**Goal:** Understand what AI systems exist, whether they've been audited, and file a report about her experience.
**Needs:** No login. Plain language. Mobile-friendly. No PII required to report.

### Persona 2: The Researcher / Journalist
**Name:** Devon
**Situation:** Writing a report on predictive risk tools in child welfare. Needs structured, citable data.
**Goal:** Access disclosure data and bias signals via API, verify sources, cite findings.
**Needs:** JSON API access, source URLs on every claim, reproducible methodology.

### Persona 3: The Advocate / Organizer
**Name:** Priya
**Situation:** Works at a legal aid org. Wants to share findings with clients and track complaints across cases.
**Goal:** Share agency overview pages, file multiple complaints, track by token.
**Needs:** Shareable URLs, complaint status lookup, no account required.

---

## 5. Features & Requirements

### 5.1 Core Features (Must Ship)

#### F1 — PDF Ingestion & Extraction
- Admin upload form accepts a PDF, agency name, and source URL
- Backend extracts text with `pdfplumber`
- Text passed to Grok API with structured extraction prompt
- Returns: agency name, system names, purpose, vendor, data sources, audit date, audit findings, extraction confidence score
- Result inserted into `ai_disclosures` table
- **Acceptance:** ACS LL35 PDF ingests and returns at minimum 1 structured system record

#### F2 — Disclosure Gap Detection
- `known_systems.json` contains hand-curated list of externally documented AI systems with citation URLs
- After each ingestion, system cross-references extracted disclosures against known systems for the same agency
- Missing matches generate a `disclosure_gap` bias signal with `severity: high`
- **Acceptance:** ACS Severe Harm PRM appears as a disclosure gap with at minimum 2 source citations

#### F3 — Outcome Disparity Analysis
- Backend ingests ACS-relevant datasets from NYC Open Data via Socrata API
- Calculates disparity ratios by race/ethnicity vs. White Non-Hispanic baseline
- Signals generated for ratios ≥ 1.2x (low), ≥ 1.5x (medium), ≥ 2.0x (high)
- Results stored in `bias_signals` table
- **Acceptance:** At least 1 disparity signal generated from real Socrata data with ratio, description, and dataset URL

#### F4 — Agency Overview Page
- Public page at `/agency/[slug]`
- Displays: disclosed AI systems table, active bias signals (severity-sorted), disclosure gaps highlighted in red
- Server-side rendered, no login, shareable URL
- **Acceptance:** ACS page renders with real data from all three sources above

#### F5 — Complaint Portal
- Form at `/complaint` — no required PII fields
- Fields: agency (dropdown), system name (optional), affected service (optional), incident description (required)
- On submit: HMAC-SHA256 token generated, complaint stored without PII linkage, token returned to user
- Status lookup at `/complaint/status` by token
- **Acceptance:** Complaint submits, token returned, status lookup works

#### F6 — Public API
- FastAPI auto-generates `/docs` (Swagger UI)
- All GET endpoints publicly accessible, no auth
- POST endpoints (upload, complaint) have rate limiting
- **Acceptance:** `/docs` renders, all endpoints documented

### 5.2 Supporting Features (Ship If Time Allows)

#### F7 — Homepage
- Search bar with agency name
- Featured ACS card with signal badge
- One-paragraph plain-language explainer
- "How it works" section

#### F8 — Agency Directory
- `/agencies` table: name, disclosed system count, active signal count, highest severity
- ACS fully populated; other agencies stubbed with "data pending"

#### F9 — Signal Detail Page
- `/signals/[id]` — full plain-language explanation, underlying data, source documents, "What can I do?" section

#### F10 — Methodology Page
- `/about` — data sources, calculation method, what we don't claim

### 5.3 Out of Scope
- User authentication or accounts
- Real-time data updates (batch ingestion is sufficient)
- Coverage beyond ACS for the demo
- Mobile-native app
- OCR for scanned PDFs (flag gracefully, don't block)
- Legal advice or case outcomes

---

## 6. Technical Architecture

### Stack
| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Next.js 14 (App Router) | Server components, shareable URLs, Vercel deploy |
| Backend | Python 3.11 + FastAPI | Async, typed, auto-docs |
| Database | Supabase (Postgres) | Free tier, RLS, JS + Python clients |
| LLM | Grok API (xAI) | Free tier, OpenAI-compatible |
| Data | NYC Open Data (Socrata) | No auth required, REST API |
| PDF | pdfplumber | Handles government PDFs well |
| Analysis | pandas + scipy | Disparity ratio + chi-square |
| Deploy | Vercel (frontend) + Railway (backend) | Free tiers, fast setup |

### Repository Structure
```
nyc-ai-accountability/
├── .github/
│   ├── workflows/
│   │   ├── backend-ci.yml
│   │   ├── frontend-ci.yml
│   │   └── security-scan.yml
│   └── CODEOWNERS
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── models/
│   │   └── data/
│   │       └── known_systems.json
│   ├── tests/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   └── .env.local.example
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql
└── PRD.md
```

### Data Flow
```
[ACS PDF] ──────────────────────────────────────────────────────────────────┐
                                                                              ▼
[Admin Upload] → FastAPI /disclosures/upload → pdfplumber → Grok API → ai_disclosures table
                                                                              │
[NYC Open Data] → FastAPI /ingest/socrata → Socrata API → outcome_data table │
                                                                              ▼
[known_systems.json] ──────────────────────────────────── Analysis Service → bias_signals table
                                                                              │
                                                                              ▼
                                                              FastAPI GET /signals, /disclosures
                                                                              │
                                                                              ▼
                                                              Next.js Agency Overview Page
```

---

## 7. Database Schema

```sql
-- AI system disclosures extracted from agency PDFs
CREATE TABLE ai_disclosures (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_name TEXT NOT NULL,
  system_name TEXT NOT NULL,
  purpose TEXT,
  vendor TEXT,
  data_sources TEXT[],
  audit_date DATE,
  audit_findings TEXT,
  disclosure_source_url TEXT,
  extracted_at TIMESTAMPTZ DEFAULT now(),
  extraction_confidence FLOAT
);

-- Outcome data from NYC Open Data (Socrata)
CREATE TABLE outcome_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency TEXT NOT NULL,
  dataset_id TEXT NOT NULL,
  year INT NOT NULL,
  race_ethnicity TEXT,
  outcome_type TEXT NOT NULL,
  count INT,
  rate FLOAT,
  ingested_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE (agency, dataset_id, year, race_ethnicity, outcome_type)
);

-- Generated bias signals
CREATE TABLE bias_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency TEXT NOT NULL,
  system_name TEXT,
  signal_type TEXT NOT NULL CHECK (signal_type IN ('disparity', 'disclosure_gap', 'audit_missing')),
  severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
  disparity_ratio FLOAT,
  description TEXT,
  source_urls TEXT[],
  generated_at TIMESTAMPTZ DEFAULT now()
);

-- Anonymous complaint intake
CREATE TABLE complaints (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  complaint_token TEXT UNIQUE NOT NULL,
  complaint_nonce TEXT NOT NULL,
  agency TEXT NOT NULL,
  system_name TEXT,
  incident_description TEXT NOT NULL,
  affected_service TEXT,
  submitted_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 8. API Contract

| Method | Endpoint | Description |
|---|---|---|
| GET | `/disclosures` | List disclosures, filter by `?agency=` |
| POST | `/disclosures/upload` | Upload PDF for extraction |
| GET | `/signals` | List signals, filter by `?agency=`, `?signal_type=`, `?severity=` |
| POST | `/signals/generate` | Run analysis pipeline for an agency |
| POST | `/complaints` | Submit anonymous complaint |
| GET | `/complaints/{token}` | Get complaint status by token |
| POST | `/ingest/socrata` | Trigger Socrata data pull |

All responses: `application/json`. All errors: `{ "detail": "..." }` with appropriate HTTP status.

---

## 9. Security Requirements

### Must Implement
- Rate limiting: 10 requests/IP/hour on `/complaints` POST (via `slowapi`)
- File upload validation: PDF mime type only, 10MB max size cap
- Input sanitization: strip HTML from all text fields before DB insert
- CORS: whitelist deployed Vercel domain only
- HMAC-SHA256 tokens for complaint IDs (random nonce, secret from env)
- Supabase RLS: `complaints` table inaccessible from client; other tables read-only
- `.env` never committed; `gitleaks` in CI catches accidental exposure
- Supabase service key backend-only; anon key frontend-only

### Data Privacy
- No PII fields on complaint form
- No IP addresses stored
- No session tracking
- No third-party analytics

---

## 10. Data Provenance & Accuracy Standards

Every public-facing claim must have a verifiable source chain:

| Claim type | Source stored |
|---|---|
| AI system exists | PDF stored in Supabase Storage + source URL |
| Disclosure gap | Citation URLs in `known_systems.json` (minimum 2 per entry) |
| Disparity ratio | Socrata dataset ID + query URL + year |
| Extraction | Confidence score + missing fields note shown in UI |

The tool surfaces signals, not conclusions. The Methodology page must state: statistical disparity does not prove causation; this is a transparency tool, not a legal finding.

---

## 11. CI/CD Pipeline

### Branch Strategy
```
main     ← protected; 2 approvals required; all CI must pass
develop  ← integration; 1 approval required; all CI must pass
feat/*   ← feature branches; open PRs against develop
```

### GitHub Actions Workflows

**backend-ci.yml** (triggers on PRs touching `backend/**`)
- `ruff check .` — linting
- `mypy app/` — type checking
- `pytest tests/ -v` — unit tests
- `bandit -r app/` — security scan

**frontend-ci.yml** (triggers on PRs touching `frontend/**`)
- `npm run lint` — ESLint
- `npm run type-check` — TypeScript
- `npm run test` — Vitest
- `npm audit --audit-level=high` — dependency vulnerabilities

**security-scan.yml** (triggers on all PRs)
- `gitleaks detect` — secret scanning
- `trivy fs .` — filesystem vulnerability scan

### CODEOWNERS
```
/backend/   @saul @beatrice
/frontend/  @william @beatrice
/supabase/  @sonia @beatrice
/.github/   @beatrice
```

---

## 12. Team Assignments & Timeline

### Beatrice (Person D) — CI/CD, Security, Testing, Integration
**Hour 1:** Create GitHub repo, configure branch protection, commit CI workflows to `main`, create `.env.example` files
**Day 1:** Get all CI checks green on first real PR; implement security middleware (rate limiting, CORS, input sanitization); write backend integration tests
**Day 2:** Security scan passing clean; end-to-end testing of full data flow; deployment verification; demo dry-run support

### Saul (Person A) — Python Backend & LLM Pipeline
**Hour 1:** Branch `feat/saul/backend-scaffold`; FastAPI app skeleton; Grok client setup
**Day 1:** PDF upload endpoint → pdfplumber → Grok extraction → Supabase insert working; `/disclosures` GET endpoint
**Day 2:** Disparity analysis service; `/signals` endpoints; Socrata ingest job; gap detection logic

### Sonia (Person B) — Supabase Schema & Data
**Hour 1:** Branch `feat/sonia/schema`; deploy schema migration to Supabase; seed `known_systems.json` with ACS Severe Harm PRM entry (minimum 2 citation URLs)
**Day 1:** Supabase RLS policies configured; outcome data tables seeded with ACS Socrata data; Supabase Storage bucket for PDFs
**Day 2:** Data QA — verify all seeded data has source URLs; verify disparity calculations against raw Socrata numbers; support signal generation testing

### William (Person C) — Next.js Frontend
**Hour 1:** Branch `feat/william/frontend-scaffold`; Next.js app init; connect to backend API
**Day 1:** Agency Overview page rendering with real data; SignalCard and DisclosureTable components; basic navigation
**Day 2:** Complaint form + token confirmation; Homepage; responsive layout polish; deploy to Vercel

---

## 13. Milestones

| Time | Milestone |
|---|---|
| Day 1, Hour 1 | Repo live, CI green, everyone branched and coding |
| Day 1, Hour 4 | PDF → extraction → database working (Saul + Sonia) |
| Day 1, Hour 6 | Agency Overview page rendering with seeded data (William) |
| Day 1, EOD | Full data flow end to end; complaint form working; all CI passing |
| Day 2, Hour 2 | Disparity signals live from real Socrata data |
| Day 2, Hour 4 | Live deployment on Vercel + Railway |
| Day 2, Hour 6 | Demo dry-run with full team |
| Day 2, EOD | Presentation delivered |

---

## 14. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Grok free tier rate limits hit during demo | Medium | Pre-run extraction before demo; cache results in DB; have `grok-3-mini` as fallback |
| ACS PDF has scanned (image-only) pages | Low | `pdfplumber` check; surface clear error; have pre-extracted JSON as fallback |
| Socrata dataset IDs changed or unavailable | Low | Verify dataset IDs on Day 1 Hour 1; have static seed data as fallback |
| Supabase free tier connection limits | Low | Use connection pooling; Supabase free tier handles ~50 concurrent connections |
| Merge conflicts slow down integration | Medium | PRs small and frequent; Beatrice reviews within 30 min; daily sync at noon |
| Demo environment differs from dev | Medium | Deploy early (Day 2 morning); test on production URL before presentation |

---

## 15. Presentation Outline

**Slide 1 — Hook (30 seconds)**
"NYC uses AI to decide if your children are taken away. Most of it is undisclosed. We built the registry the city was supposed to."

**Slide 2 — The Problem**
- LL35 requires disclosure. The disclosures are unreadable PDFs.
- The GUARD Act created a watchdog office. The tools don't exist yet.
- The Severe Harm Predictive Risk Model is documented in academic papers and ACLU reports. It does not appear in ACS's official disclosures.

**Slide 3 — The Solution**
- [Screenshot: Agency Overview page with red "Disclosure Gap" banner]
- Plain-language bias signals tied to real data
- Anonymous complaint intake
- Public API — journalists and researchers can query it directly

**Slide 4 — Technical Architecture**
- Diagram: PDF → Grok → Supabase → FastAPI → Next.js
- Provenance chain: every claim links to its source
- Security: HMAC tokens, no PII, RLS, rate limiting

**Slide 5 — Live Demo**
- Upload ACS LL35 PDF → watch extraction run → see Severe Harm PRM appear as disclosure gap
- Show disparity signal: Black families referred at [X]x rate
- File a complaint → receive token → look up status

**Slide 6 — Impact & Next Steps**
- This is the public AI registry the GUARD Act mandated
- Expandable to all NYC agencies
- Complaint data aggregates into a public accountability signal
- Open source — the city's Office of Algorithmic Data Accountability could adopt it

**Slide 7 — Team**
Beatrice · Saul · William · Sonia

---

## 16. Definition of Done

The project is complete when:
- [ ] A judge can visit a live URL and see ACS's disclosure gap without any setup
- [ ] A judge can file a complaint and receive a token
- [ ] A judge can call `/docs` and see all API endpoints documented
- [ ] All GitHub CI checks are green on `main`
- [ ] The security scan (`gitleaks`, `trivy`, `bandit`) shows no high-severity findings
- [ ] Every bias signal on the page has at least one clickable source URL
- [ ] The methodology page explains what we don't claim

---

*This document is the source of truth for the project. Any scope changes must be discussed as a team and reflected here before implementation.*
