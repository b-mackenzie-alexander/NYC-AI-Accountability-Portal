# Architecture
## NYC AI Accountability Portal

---

## Overview

The application is a public-facing transparency tool with three data pipelines feeding a read-heavy web frontend. All pipelines converge in Supabase (Postgres), which serves as the single source of truth. The frontend never writes to the database directly.

```
┌─────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                              │
│                                                                     │
│  [Agency PDFs]   [NYC Open Data / Socrata]   [known_systems.json]  │
└────────┬─────────────────────┬──────────────────────┬──────────────┘
         │                     │                      │
         ▼                     ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                            │
│                                                                     │
│  Ingestion Layer        Analysis Layer         API Layer            │
│  ─────────────────      ───────────────────    ──────────────────   │
│  pdfplumber             disparity_service      /disclosures         │
│  grok_client            gap_detection          /signals             │
│  socrata_client         signal_builder         /complaints          │
│                                                /ingest/socrata      │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      DATABASE (Supabase / Postgres)                 │
│                                                                     │
│   ai_disclosures    outcome_data    bias_signals    complaints      │
│                                                                     │
│   [PDF Storage bucket — raw PDFs retained for audit trail]         │
└─────────────────────────────────────┬───────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Next.js 14)                         │
│                                                                     │
│   /                     Homepage                                    │
│   /agencies             Agency Directory                            │
│   /agency/[slug]        Agency Overview (server component)          │
│   /signals/[id]         Signal Detail                               │
│   /complaint            Complaint Portal (client component)         │
│   /complaint/status     Token Lookup                                │
│   /about                Methodology                                 │
│   /admin/upload         PDF Upload (internal, no auth)              │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline 1: PDF Ingestion & Extraction

**Trigger:** Admin POSTs to `/disclosures/upload` with a PDF file, agency name, and source URL.

```
POST /disclosures/upload
        │
        ▼
  [Validation]
  - MIME type must be application/pdf
  - Size must be ≤ 10MB
  - agency and source_url required
        │
        ▼
  [pdfplumber]
  - Extract raw text from all pages
  - If len(text) < 100: return 422 (likely scanned PDF)
        │
        ▼
  [Grok API call]
  - Model: grok-3 (fallback: grok-3-mini)
  - System prompt: structured extraction schema
  - response_format: json_object
  - Returns: { agency_name, systems[], extraction_confidence, missing_fields_note }
        │
        ▼
  [Supabase insert]
  - One row per system in systems[]
  - Store extraction_confidence per row
  - Store source_url from request
  - Upload original PDF to Storage bucket
        │
        ▼
  [Gap detection trigger]
  - Cross-reference extracted system names against known_systems.json
  - Generate disclosure_gap bias_signal rows for any matches not found
        │
        ▼
  Return: list of inserted ai_disclosure records
```

---

## Pipeline 2: Outcome Data Ingestion

**Trigger:** POST to `/ingest/socrata` (called at startup or manually). Idempotent — safe to re-run.

```
POST /ingest/socrata
        │
        ▼
  [Socrata API call]
  - Base URL: https://data.cityofnewyork.us/resource/{dataset_id}.json
  - SoQL query with year filter
  - No auth required; App-Token header if rate limited
        │
        ▼
  [Normalization]
  - Map Socrata field names to outcome_data schema
  - Cast types (count → int, rate → float)
  - Validate race_ethnicity values against known set
        │
        ▼
  [Supabase upsert]
  - ON CONFLICT (agency, dataset_id, year, race_ethnicity, outcome_type)
  - DO UPDATE SET count, rate, ingested_at
        │
        ▼
  Return: { rows_upserted: int, dataset_id: str }
```

---

## Pipeline 3: Signal Generation

**Trigger:** POST to `/signals/generate` after ingestion, or called on-demand.

```
POST /signals/generate?agency=ACS
        │
        ▼
  [Load outcome_data for agency]
  - Pull all rows for the agency from outcome_data
  - Group by outcome_type and year
        │
        ▼
  [Disparity ratio calculation]
  - Reference group: White Non-Hispanic
  - For each (outcome_type, year, race_ethnicity):
      ratio = group_rate / reference_rate
      if ratio ≥ 1.2: generate disparity signal with severity
        │
        ▼
  [Gap detection]
  - Load known_systems.json for agency
  - Load ai_disclosures for agency
  - For each known system not found in disclosures:
      generate disclosure_gap signal (severity: high)
        │
        ▼
  [Supabase upsert]
  - Delete existing signals for agency before insert (re-generation is clean)
  - Insert all new signals
        │
        ▼
  Return: list of generated bias_signal records
```

---

## Database Schema

```sql
-- Extracted from agency PDF disclosures
CREATE TABLE ai_disclosures (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_name          TEXT NOT NULL,
  system_name          TEXT NOT NULL,
  purpose              TEXT,
  vendor               TEXT,
  data_sources         TEXT[],
  audit_date           DATE,
  audit_findings       TEXT,
  disclosure_source_url TEXT,
  extracted_at         TIMESTAMPTZ DEFAULT now(),
  extraction_confidence FLOAT           -- 0.0–1.0, Grok self-reported
);

-- Outcome statistics from NYC Open Data
CREATE TABLE outcome_data (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency       TEXT NOT NULL,
  dataset_id   TEXT NOT NULL,
  year         INT NOT NULL,
  race_ethnicity TEXT,
  outcome_type TEXT NOT NULL,           -- 'placement', 'removal', 'preventive_service'
  count        INT,
  rate         FLOAT,
  ingested_at  TIMESTAMPTZ DEFAULT now(),
  UNIQUE (agency, dataset_id, year, race_ethnicity, outcome_type)
);

-- Generated signals from analysis pipelines
CREATE TABLE bias_signals (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency          TEXT NOT NULL,
  system_name     TEXT,
  signal_type     TEXT NOT NULL CHECK (signal_type IN ('disparity', 'disclosure_gap', 'audit_missing')),
  severity        TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high')),
  disparity_ratio FLOAT,
  description     TEXT,
  source_urls     TEXT[],
  generated_at    TIMESTAMPTZ DEFAULT now()
);

-- Anonymous complaint intake
CREATE TABLE complaints (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  complaint_token      TEXT UNIQUE NOT NULL,  -- shown to user for status lookup
  complaint_nonce      TEXT NOT NULL,         -- used to verify token server-side
  agency               TEXT NOT NULL,
  system_name          TEXT,
  incident_description TEXT NOT NULL,
  affected_service     TEXT,
  submitted_at         TIMESTAMPTZ DEFAULT now()
  -- No name, no email, no IP, no PII fields
);
```

### Row Level Security

```sql
-- complaints: no client access at all
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;
-- No policies = deny all (default Supabase behavior with RLS enabled)

-- Other tables: public read, no client writes
ALTER TABLE ai_disclosures ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public read" ON ai_disclosures FOR SELECT USING (true);

ALTER TABLE bias_signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public read" ON bias_signals FOR SELECT USING (true);

ALTER TABLE outcome_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public read" ON outcome_data FOR SELECT USING (true);
```

---

## API Surface

All routes served from FastAPI. Swagger docs auto-generated at `/docs`.

### Disclosures
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/disclosures` | None | List disclosures. `?agency=` filter. |
| POST | `/disclosures/upload` | None (rate limited) | Upload PDF → extract → insert |

### Signals
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/signals` | None | List signals. `?agency=`, `?signal_type=`, `?severity=` filters. |
| POST | `/signals/generate` | None | Run analysis pipeline for `?agency=` |

### Complaints
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/complaints` | None (rate limited) | Submit anonymous complaint. Returns token. |
| GET | `/complaints/{token}` | None | Get complaint status by token. |

### Ingest
| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/ingest/socrata` | None | Pull Socrata data for `?agency=` and `?dataset_id=` |

### Meta
| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Health check. Returns `{"status": "ok"}` |
| GET | `/docs` | None | Swagger UI (FastAPI auto-generated) |

---

## Frontend Component Map

```
app/
├── page.tsx                        Homepage
├── agencies/
│   └── page.tsx                    Agency Directory
├── agency/
│   └── [slug]/
│       └── page.tsx                Agency Overview (server component)
├── signals/
│   └── [id]/
│       └── page.tsx                Signal Detail
├── complaint/
│   ├── page.tsx                    Complaint Portal
│   └── status/
│       └── page.tsx                Token Status Lookup
├── about/
│   └── page.tsx                    Methodology
└── admin/
    └── upload/
        └── page.tsx                PDF Upload (internal)

components/
├── SignalCard.tsx                   Severity-coded signal display
├── DisclosureTable.tsx             Systems table with gap rows
├── DisparityChart.tsx              Horizontal bar chart (Recharts)
├── ComplaintForm.tsx               Client component, calls /complaints
├── ComplaintStatusWidget.tsx       Token lookup widget
└── AgencyCard.tsx                  Card used on homepage and directory

lib/
├── api.ts                          Typed fetch helpers for all endpoints
└── utils.ts                        Slug generation, severity colors, etc.
```

### Data Fetching Strategy

- **Agency Overview, Signal Detail, Agency Directory:** Server components. Fetch at request time (`cache: 'no-store'`). Data stays server-side; no API keys exposed to browser.
- **Complaint Form:** Client component (`'use client'`). Calls backend directly from browser using `NEXT_PUBLIC_API_BASE_URL`.
- **Homepage:** Server component for featured agency data; no client-side fetching needed.

---

## Security Architecture

### Threat Model
The app is public-facing with no user accounts. The primary risks are:

| Threat | Control |
|---|---|
| Spam/abuse via complaint endpoint | Rate limiting: 10 req/IP/hour (`slowapi`) |
| Malicious PDF upload | MIME validation, 10MB cap, pdfplumber runs in isolated context |
| XSS via extracted PDF content | All LLM output stored as plain text; rendered via React (auto-escapes) |
| SQL injection | Supabase client uses parameterized queries; no raw SQL with user input |
| Secret exposure in code | `gitleaks` in CI; `.env` files gitignored; `.env.example` has no real values |
| Client-side database writes | Supabase RLS blocks all client writes; anon key has read-only access |
| Complaint PII linkage | No PII fields on form; no IP logged; HMAC token is opaque |

### HMAC Token Flow
```python
import hmac, hashlib, secrets

# At complaint submission:
nonce = secrets.token_hex(16)                              # random, stored in DB
token = hmac.new(
    COMPLAINT_HMAC_SECRET.encode(),
    nonce.encode(),
    hashlib.sha256
).hexdigest()                                              # returned to user

# At status lookup:
# Fetch row by token (indexed), return status fields only
# Never return nonce, never return complaint content
```

---

## Infrastructure

| Component | Service | Tier | Notes |
|---|---|---|---|
| Frontend | Vercel | Free | Auto-deploys from `main` |
| Backend | Railway | Free | Persistent service, not serverless |
| Database | Supabase | Free | Postgres + Storage + RLS |
| LLM | xAI Grok API | Free | Rate limits TBD |
| NYC Open Data | Socrata | Free | No auth for public datasets |

### Environment Variables

**Backend (Railway)**
```
GROK_API_KEY
GROK_MODEL=grok-3
SUPABASE_URL
SUPABASE_SERVICE_KEY
COMPLAINT_HMAC_SECRET
ALLOWED_ORIGINS=https://[vercel-domain]
```

**Frontend (Vercel)**
```
API_BASE_URL=https://[railway-domain]          # server-side only
NEXT_PUBLIC_API_BASE_URL=https://[railway-domain]   # client-side
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

---

## Key Design Constraints

1. **No auth.** The complaint form and all read routes are fully public. This is intentional — auth friction kills the resident use case.
2. **Every claim has a source.** `source_urls` is a required field on bias signals. The UI must render at least one clickable citation per signal.
3. **Grok output is not trusted.** `extraction_confidence < 0.7` surfaces a warning in the UI. Extracted data is stored as-is; the UI labels it as LLM-extracted and links to the source PDF.
4. **The analysis layer surfaces signals, not conclusions.** The methodology page and signal descriptions must state: disparity does not prove causation.
5. **Supabase Storage retains source PDFs.** Original documents are not deleted. This is the audit trail.
