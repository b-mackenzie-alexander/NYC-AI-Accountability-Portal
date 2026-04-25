# Roadmap
## NYC AI Accountability Portal
**Hackathon:** April 24–25, 2026 | **Track:** AI for Justice, Policy & Equity

**Team:** Beatrice (CI/CD, Security) · Saul (Backend) · Sonia (Data/DB) · William (Frontend)

---

## Phase 0 — Bootstrap (Day 1, Hours 1–2)
*Unblocks everyone. Nothing merges until this is done.*

| Status | Owner | Task | Done When |
|---|---|---|---|
| ✅ | **Beatrice** | Create GitHub repo, configure branch protection on `main` and `develop` | Branch rules enforced, direct push blocked |
| ✅ | **Beatrice** | Commit CI workflow files to `main` as bootstrap commit | `backend-ci.yml`, `frontend-ci.yml`, `security-scan.yml` in `.github/workflows/` |
| ✅ | **Beatrice** | Add `CODEOWNERS` | File committed, owners assigned by directory |
| ✅ | **Beatrice** | Create `.env.example` (backend) and `.env.local.example` (frontend) | All required env var names present, no real values |
| ✅ | **Saul** | FastAPI skeleton app with health check endpoint | `GET /health` returns `{"status": "ok"}` |
| ✅ | **Sonia** | Deploy schema migration to Railway Postgres | All 4 tables created, RLS enabled on `complaints` |
| ✅ | **Beatrice** | Create Cloudflare R2 bucket for PDFs | `disclosure-pdfs` bucket exists, R2 credentials set in Railway |
| ✅ | **Sonia** | Seed `known_systems.json` with ACS Severe Harm PRM entry | Entry has ≥2 citation URLs |
| ✅ | **William** | Next.js app scaffolded, connected to API via env var | `npm run dev` starts without errors |

---

## Phase 1 — Core Data Pipeline (Day 1, Hours 3–6)
*The backbone. Everything the UI renders comes from here.*

| Status | Owner | Task | Done When |
|---|---|---|---|
| ✅ | **Saul** | `pdfplumber` text extraction service | Extracts text from ACS LL35 PDF without errors |
| ✅ | **Saul** | Grok API extraction service with structured prompt | Returns valid JSON matching `ai_disclosures` schema |
| ✅ | **Saul** | `POST /disclosures/upload` endpoint | PDF upload → extraction → R2 upload → DB insert in one request |
| ⬜ | **Saul** | `GET /disclosures` endpoint with `?agency=` filter | Returns JSON array of disclosure records |
| ✅ | **Saul** | `POST /ingest/socrata` endpoint | Triggers ingest job, returns row count |
| ⬜ | **Sonia** | Socrata ingest service (ACS datasets) | Pulls foster care placement data, upserts into `outcome_data` |
| ⬜ | **Sonia** | Verify ACS dataset IDs on Socrata | 3 dataset IDs confirmed and documented in NOTES.md |
| ✅ | **Beatrice** | Security middleware: rate limiting, CORS, input sanitization | `slowapi` configured; CORS restricted to localhost + Cloudflare Pages domain |
| ⬜ | **Beatrice** | Backend integration tests (upload, disclosures, ingest) | `pytest tests/ -v` passes with real Railway Postgres test schema |
| ✅ | **Beatrice** | All backend CI checks green on first PR to `develop` | `ruff`, `mypy`, `pytest`, `bandit`, `gitleaks`, `trivy` all pass |

---

## Phase 2 — Analysis & Signals (Day 1, Hour 6 – Day 2, Hour 2)
*Turns raw data into findings. The core value proposition.*

| Status | Owner | Task | Done When |
|---|---|---|---|
| ⬜ | **Saul** | Disparity ratio calculation service | Returns signal dicts for ratios ≥ 1.2x with severity classification |
| ✅ | **Saul** | Disclosure gap detection (cross-reference `known_systems.json`) | ACS Severe Harm PRM appears as `disclosure_gap` signal |
| ✅ | **Saul** | `POST /signals/check-gaps/{agency}` endpoint | Runs gap analysis for an agency, upserts to `bias_signals` |
| ⬜ | **Saul** | `GET /signals` endpoint with filters | Filters by `agency`, `signal_type`, `severity` |
| ✅ | **Saul** | Complaint intake endpoint with HMAC token | `POST /complaints` returns token; no PII stored |
| ⬜ | **Saul** | Complaint status endpoint | `GET /complaints/{token}` returns status without exposing complaint content |
| ⬜ | **Sonia** | Verify disparity ratios against raw Socrata numbers manually | Spot-check 3 race/ethnicity groups; ratios match hand calculation |
| ⬜ | **Beatrice** | Analysis pipeline integration tests | Signal generation tested with fixture data |

---

## Phase 3 — Frontend (Day 1, Hour 4 – Day 2, Hour 3)
*Runs in parallel with Phase 2. Unblocks on Phase 1 completion.*

| Status | Owner | Task | Done When |
|---|---|---|---|
| ⬜ | **William** | `lib/api.ts` — typed fetch helpers for all endpoints | All API calls typed; error handling consistent |
| ⬜ | **William** | Agency Overview page (`/agency/[slug]`) | Renders disclosures table, signal cards, disclosure gaps |
| ⬜ | **William** | `SignalCard` component | Severity color coding, signal type label, source URL links |
| ⬜ | **William** | `DisclosureTable` component | Disclosed systems + gap rows in red; no data state handled |
| ⬜ | **William** | Disparity bar chart (Recharts) | Horizontal bars by race/ethnicity, colored by severity |
| ⬜ | **William** | Complaint form (`/complaint`) | Submits to backend, renders token confirmation |
| ⬜ | **William** | Complaint status lookup widget | Token input → status display |
| ⬜ | **William** | Homepage (`/`) | Search bar, ACS featured card with signal badge, explainer |
| ⬜ | **William** | Agency Directory (`/agencies`) | ACS row with real data; other agencies stubbed |
| ⬜ | **William** | Methodology page (`/about`) | Data sources, calculation method, what we don't claim |
| ⬜ | **William** | Admin upload page (`/admin/upload`) | PDF upload form, calls `POST /disclosures/upload` |
| ⬜ | **William** | Responsive layout pass | Readable on mobile; no broken layouts at 375px |

---

## Phase 4 — Deployment & Hardening (Day 2, Hours 3–5)
*Everything must be on a live URL before the demo dry-run.*

| Status | Owner | Task | Done When |
|---|---|---|---|
| ✅ | **Saul** | Deploy backend to Railway | Live URL returns `GET /health` 200 |
| ⬜ | **Saul** | Trigger signal generation on production | Bias signals appear on live ACS page |
| ⬜ | **William** | Deploy frontend to Cloudflare Pages | Live URL renders ACS Agency Overview with real data |
| ⬜ | **Sonia** | Load ACS LL35 PDF via admin upload on production | Disclosure gap appears on live ACS page |
| ⬜ | **Sonia** | Final check: all source URLs on bias signals are clickable | Manual spot-check on live URL |
| ✅ | **Beatrice** | Set all production env vars in Railway | `DATABASE_URL`, R2 credentials set; app redeploying |
| ⬜ | **Beatrice** | Update CORS allowlist to production Cloudflare Pages domain | API accepts requests from production frontend |
| ⬜ | **Beatrice** | Run `gitleaks`, `trivy`, `bandit` against production branch | Zero high-severity findings |
| ⬜ | **Beatrice** | End-to-end smoke test on live URL | All Definition of Done criteria verified |
| ⬜ | **All** | Demo dry-run with full team | Each member can explain their component; demo flows under 5 minutes |

---

## Phase 5 — Presentation (Day 2, Hours 5–6)
*Polish, not new features.*

| Status | Owner | Task | Done When |
|---|---|---|---|
| ⬜ | **Beatrice** | Finalize 7-slide deck (see PRD §15) | Deck reviewed by all team members |
| ⬜ | **William** | Record fallback demo video (insurance if live demo breaks) | 3-minute screen recording of full flow |
| ⬜ | **Sonia** | Final check: all source URLs on bias signals are clickable | Manual spot-check on live URL |
| ⬜ | **All** | Prepare judge Q&A answers (methodology, privacy, accuracy) | Team aligned on answers to top 5 likely questions |

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
