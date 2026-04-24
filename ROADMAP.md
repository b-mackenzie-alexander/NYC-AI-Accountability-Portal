# Roadmap
## NYC AI Accountability Portal
**Hackathon:** April 24–25, 2026 | **Track:** AI for Justice, Policy & Equity

---

## Phase 0 — Bootstrap (Day 1, Hours 1–2)
*Unblocks everyone. Nothing merges until this is done.*

| Task | Owner | Done When |
|---|---|---|
| Create GitHub repo, configure branch protection on `main` and `develop` | Beatrice | Branch rules enforced, direct push blocked |
| Commit CI workflow files to `main` as bootstrap commit | Beatrice | `backend-ci.yml`, `frontend-ci.yml`, `security-scan.yml` in `.github/workflows/` |
| Add `CODEOWNERS` | Beatrice | File committed, owners assigned by directory |
| Create `.env.example` (backend) and `.env.local.example` (frontend) | Beatrice | All required env var names present, no real values |
| Deploy Supabase schema migration | Sonia | All 4 tables created, RLS enabled on `complaints` |
| Create Supabase Storage bucket for PDFs | Sonia | Bucket exists, backend service key has write access |
| Seed `known_systems.json` with ACS Severe Harm PRM entry | Sonia | Entry has ≥2 citation URLs |
| FastAPI skeleton app with health check endpoint | Saul | `GET /health` returns `{"status": "ok"}` |
| Next.js app scaffolded, connected to API via env var | William | `npm run dev` starts without errors |

---

## Phase 1 — Core Data Pipeline (Day 1, Hours 3–6)
*The backbone. Everything the UI renders comes from here.*

| Task | Owner | Done When |
|---|---|---|
| `pdfplumber` text extraction service | Saul | Extracts text from ACS LL35 PDF without errors |
| Grok API extraction service with structured prompt | Saul | Returns valid JSON matching `ai_disclosures` schema |
| `POST /disclosures/upload` endpoint | Saul | PDF upload → extraction → Supabase insert in one request |
| `GET /disclosures` endpoint with `?agency=` filter | Saul | Returns JSON array of disclosure records |
| Socrata ingest service (ACS datasets) | Sonia | Pulls foster care placement data, upserts into `outcome_data` |
| `POST /ingest/socrata` endpoint | Saul | Triggers ingest job, returns row count |
| Verify dataset IDs on Socrata at runtime | Sonia | 3 ACS dataset IDs confirmed and documented in NOTES.md |
| Backend integration tests (upload, disclosures, ingest) | Beatrice | `pytest tests/ -v` passes with real Supabase test schema |
| Security middleware: rate limiting, CORS, input sanitization | Beatrice | `slowapi` configured; CORS restricted to localhost + Vercel domain |
| All backend CI checks green on first PR to `develop` | Beatrice | `ruff`, `mypy`, `pytest`, `bandit`, `gitleaks`, `trivy` all pass |

---

## Phase 2 — Analysis & Signals (Day 1, Hour 6 – Day 2, Hour 2)
*Turns raw data into findings. The core value proposition.*

| Task | Owner | Done When |
|---|---|---|
| Disparity ratio calculation service | Saul | Returns signal dicts for ratios ≥ 1.2x with severity classification |
| Disclosure gap detection (cross-reference `known_systems.json`) | Saul | ACS Severe Harm PRM appears as `disclosure_gap` signal |
| `POST /signals/generate` endpoint | Saul | Runs full analysis pipeline for an agency, upserts to `bias_signals` |
| `GET /signals` endpoint with filters | Saul | Filters by `agency`, `signal_type`, `severity` |
| Verify disparity ratios against raw Socrata numbers manually | Sonia | Spot-check 3 race/ethnicity groups; ratios match hand calculation |
| Complaint intake endpoint with HMAC token | Saul | `POST /complaints` returns token; no PII stored |
| Complaint status endpoint | Saul | `GET /complaints/{token}` returns status without exposing complaint content |
| Analysis pipeline integration tests | Beatrice | Signal generation tested with fixture data |

---

## Phase 3 — Frontend (Day 1, Hour 4 – Day 2, Hour 3)
*Runs in parallel with Phase 2. Unblocks on Phase 1 completion.*

| Task | Owner | Done When |
|---|---|---|
| `lib/api.ts` — typed fetch helpers for all endpoints | William | All API calls typed; error handling consistent |
| Agency Overview page (`/agency/[slug]`) | William | Renders disclosures table, signal cards, disclosure gaps |
| `SignalCard` component | William | Severity color coding, signal type label, source URL links |
| `DisclosureTable` component | William | Disclosed systems + gap rows in red; no data state handled |
| Disparity bar chart (Recharts) | William | Horizontal bars by race/ethnicity, colored by severity |
| Complaint form (`/complaint`) | William | Submits to backend, renders token confirmation |
| Complaint status lookup widget | William | Token input → status display |
| Homepage (`/`) | William | Search bar, ACS featured card with signal badge, explainer |
| Agency Directory (`/agencies`) | William | ACS row with real data; other agencies stubbed |
| Methodology page (`/about`) | William | Data sources, calculation method, what we don't claim |
| Admin upload page (`/admin/upload`) | William | PDF upload form, calls `POST /disclosures/upload` |
| Responsive layout pass | William | Readable on mobile; no broken layouts at 375px |

---

## Phase 4 — Deployment & Hardening (Day 2, Hours 3–5)
*Everything must be on a live URL before the demo dry-run.*

| Task | Owner | Done When |
|---|---|---|
| Deploy backend to Railway | Saul | Live URL returns `GET /health` 200 |
| Deploy frontend to Vercel | William | Live URL renders ACS Agency Overview with real data |
| Set all production env vars in Railway and Vercel | Beatrice | No hardcoded values; app boots cleanly from env |
| Update CORS allowlist to production Vercel domain | Beatrice | API accepts requests from production frontend |
| Run `gitleaks`, `trivy`, `bandit` against production branch | Beatrice | Zero high-severity findings |
| Load ACS LL35 PDF via admin upload on production | Sonia | Disclosure gap appears on live ACS page |
| Trigger signal generation on production | Saul | Bias signals appear on live ACS page |
| End-to-end smoke test on live URL | Beatrice | All 7 Definition of Done criteria verified |
| Demo dry-run with full team | All | Each team member can explain their component; demo flows in under 5 minutes |

---

## Phase 5 — Presentation (Day 2, Hours 5–6)
*Polish, not new features.*

| Task | Owner | Done When |
|---|---|---|
| Finalize 7-slide deck (see PRD §15) | Beatrice | Deck reviewed by all team members |
| Record fallback demo video (insurance if live demo breaks) | William | 3-minute screen recording of full flow |
| Prepare judge Q&A answers (methodology, privacy, accuracy) | All | Team aligned on answers to top 5 likely questions |
| Final check: all source URLs on bias signals are clickable | Sonia | Manual spot-check on live URL |

---

## Stretch Goals (Only If Phase 3 Complete Early)

- Signal Detail page (`/signals/[id]`) with full source chain display
- `grok-3-mini` fallback with automatic retry on rate limit
- Chi-square significance test alongside disparity ratio
- Admin upload page protected with a simple passphrase (not full auth)
- Complaint aggregation count on Agency Overview (k-anonymized)

---

## Definition of Done (Pre-Presentation Checklist)

- [ ] Live URL accessible without any setup
- [ ] ACS disclosure gap visible with ≥2 source citations
- [ ] At least 1 disparity signal with real Socrata data and ratio shown
- [ ] Complaint form submits and returns token
- [ ] `/docs` Swagger UI shows all endpoints
- [ ] All GitHub CI checks green on `main`
- [ ] Security scan: zero high-severity findings
- [ ] Every bias signal has at least 1 clickable source URL
- [ ] Methodology page live and accurate
- [ ] Fallback demo video recorded
