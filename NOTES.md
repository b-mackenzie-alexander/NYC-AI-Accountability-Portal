# Working Notes
## NYC AI Accountability Portal

*Running log of decisions, findings, blockers, and things to verify. Add entries with date/time and your name.*

---

## Architecture Decisions

### ADR-001: Grok API over Claude for LLM extraction
**Decision:** Use xAI Grok API for PDF extraction.
**Reason:** Free tier available for hackathon; OpenAI-compatible API means minimal code change if we swap providers post-demo.
**How to swap back:** Change `base_url` in the OpenAI client and update `model` env var. Prompt works as-is.

### ADR-002: White Non-Hispanic as disparity ratio baseline
**Decision:** All disparity ratios calculated against White Non-Hispanic as the reference group.
**Reason:** Standard in civil rights disparate impact analysis; matches how existing academic literature frames ACS data.
**Caveat:** If White Non-Hispanic rate is 0 in a dataset, skip the ratio (division by zero guard in code).

### ADR-003: No authentication on public-facing routes
**Decision:** All GET endpoints and the complaint form are fully public, no login.
**Reason:** The tool's value is accessibility to affected residents. Auth friction kills the persona-1 use case.
**Security tradeoff:** Rate limiting on complaint POST; RLS on Supabase blocks any client-side writes to sensitive tables.

### ADR-004: Synchronous PDF extraction for hackathon
**Decision:** `POST /disclosures/upload` is synchronous — waits for Grok response before returning.
**Reason:** Async job queue (Celery, etc.) adds complexity we don't need for a demo with one PDF.
**Frontend implication:** Show loading state; expect 3–8 second response time.

### ADR-005: Monorepo with `/backend` and `/frontend` subdirectories

### ADR-006: Pivot from Supabase to Railway Postgres + Cloudflare R2
**Decision:** Replace Supabase with Railway Postgres (database) and Cloudflare R2 (PDF storage).
**Reason:** Hit Supabase free tier usage cap during the hackathon. Railway Postgres is already in the project's infrastructure; R2 has a generous free tier and an S3-compatible API.
**Impact:**
- `supabase` Python package replaced with `asyncpg` + `boto3`
- Supabase JS client removed from frontend entirely — all data flows through FastAPI API
- RLS policies unchanged — they are standard Postgres, not Supabase-specific
- `DATABASE_URL` replaces `SUPABASE_URL` + `SUPABASE_SERVICE_KEY` in backend env
- `R2_*` vars replace storage bucket config
- Frontend env simplified: only `API_BASE_URL` and `NEXT_PUBLIC_API_BASE_URL` needed
**How to apply:** Use `app.services.database` (asyncpg pool) for all DB access. Use `app.services.storage` (boto3 → R2) for PDF uploads. Never import the `supabase` package.
**Decision:** Single GitHub repo, two top-level directories.
**Reason:** Simplifies CI (path-based triggers), keeps team in one place, easier cross-referencing.

---

## Data Notes

### ACS Datasets to Verify on Day 1

These Socrata dataset IDs need to be confirmed before Sonia starts the ingest service.
Visit `data.cityofnewyork.us` and search "ACS" to verify current IDs.

| Dataset | Expected ID | Status |
|---|---|---|
| Foster care placements by demographic | TBD | [ ] Verified |
| Child welfare service requests | TBD | [ ] Verified |
| Preventive services enrollment | TBD | [ ] Verified |

**Socrata base URL:** `https://data.cityofnewyork.us/resource/{dataset_id}.json`
**No API key required** for public datasets. Add `$$app_token` header if rate limited.

### ACS LL35 PDF Source
✅ **Resolved** — Most recent report published March 2026:
https://www.nyc.gov/assets/oti/downloads/pdf/reports/LL35%20Report%202025%20-%20Final%20-%202026-03-27.pdf

### Severe Harm Predictive Risk Model — Citation Sources
✅ **Resolved** — 5 verified URLs added to `backend/app/data/known_systems.json`:
1. https://themarkup.org/investigations/2025/05/20/the-nyc-algorithm-deciding-which-families-are-under-watch-for-child-abuse
2. https://aspe.hhs.gov/reports/child-welfare-predictive-risk-models
3. https://www.aclu.org/news/womens-rights/family-surveillance-by-algorithm-the-rapidly-spreading-tools-few-have-heard-of
4. https://mcsilver.nyu.edu/predictive-risk-tools-in-child-welfare-practice/
5. https://www.nyc.gov/assets/oti/downloads/pdf/reports/2024-algorithmic-tools-report.pdf

### Disparity Ratio Thresholds (for reference)
```
≥ 2.0x  → high severity
≥ 1.5x  → medium severity
≥ 1.2x  → low severity
< 1.2x  → not surfaced
```
These match EEOC 80% rule (4/5ths rule) framing, adapted for over-representation rather than under-selection.

---

## API & Integration Notes

### Grok API
- **Base URL:** `https://api.x.ai/v1`
- **Auth:** `Authorization: Bearer $GROK_API_KEY`
- **Models:** `grok-3` (default), `grok-3-mini` (faster, use as fallback)
- **Rate limits:** Verify free tier limits on day 1. If hit during demo, switch to `grok-3-mini`.
- **Response format:** Set `response_format={"type": "json_object"}` to guarantee JSON output.

### Supabase
- **Service key** (backend only): Has full DB access, bypasses RLS. Never expose to frontend.
- **Anon key** (frontend): Obeys RLS. Safe to expose (it's public by design).
- **RLS policy for `complaints`:** DENY all client access. All complaint reads/writes go through FastAPI.
- **Connection pooling:** Supabase free tier uses PgBouncer by default. Use the connection pooler URL for the backend, not the direct connection.

### Socrata API
- **No auth required** for public datasets.
- **Query format:** SoQL — `?$where=agency='ACS'&$limit=1000`
- **If rate limited:** Add header `X-App-Token: $SOCRATA_APP_TOKEN` (register a free token at data.cityofnewyork.us)

---

## Blockers & Open Questions

| # | Question | Owner | Status |
|---|---|---|---|
| 1 | Exact Socrata dataset IDs for ACS foster care data | Sonia | Open |
| 2 | URL for most recent ACS LL35 annual report PDF | Sonia | ✅ Resolved — see Reference Links |
| 3 | Citation URLs for Severe Harm PRM in `known_systems.json` | Sonia | ✅ Resolved — 5 URLs in `known_systems.json` |
| 4 | Grok free tier rate limits (requests/min, tokens/day) | Saul | Open |
| 5 | Vercel domain for CORS allowlist (known after first deploy) | William | Open |
| 6 | Railway service URL (known after first deploy) | Saul | Open |
| 7 | Sonia: deploy migration + create storage bucket in Supabase | Sonia | Open — needs credentials |
| 8 | William: push Next.js scaffold to `william-frontend-branch` | William | Open — branch exists, no code yet |

---

## Environment Variables

### Backend (`backend/.env`)
```
GROK_API_KEY=
GROK_MODEL=grok-3
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
COMPLAINT_HMAC_SECRET=        # generate: python -c "import secrets; print(secrets.token_hex(32))"
ALLOWED_ORIGINS=http://localhost:3000  # add Vercel domain after deploy
```

### Frontend (`frontend/.env.local`)
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000   # public: used client-side
API_BASE_URL=http://localhost:8000               # server-side fetches
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

---

## Demo Script (Rough Order)

1. Open `/agency/administration-for-children-s-services`
2. Point to red "Disclosure Gap" banner — ACS Severe Harm PRM not in official disclosures
3. Point to disparity signal — Black families referred at Xx rate
4. Scroll to disclosures table — gap row highlighted red
5. Click source URL on disclosure gap — shows external documentation
6. Navigate to `/complaint` — fill form live, submit, show token
7. Navigate to `/complaint/status` — look up token
8. Navigate to `/docs` — show API is public and documented
9. Optional: show admin upload — drag in PDF, watch extraction run

**Target time:** Under 4 minutes for the demo portion.

---

## Post-Hackathon Notes (Add After Presentation)

*To be filled in after judging.*

---

## Change Log

| Date | Author | Note |
|---|---|---|
| 2026-04-24 | Beatrice | Initial NOTES.md created |
| 2026-04-24 | Beatrice | PR #1 merged — `known_systems.json` seeded, NOTES blockers #2 and #3 resolved |
| 2026-04-24 | Beatrice | PR #2 merged — CI fixed: mypy types, python-multipart CVEs, Gitleaks permissions |
| 2026-04-24 | Beatrice | `develop` is clean and green; `william-frontend-branch` exists but has no code yet |
| 2026-04-24 | Beatrice | Pivoted from Supabase to Railway Postgres + Cloudflare R2 (ADR-006) — hit Supabase cap |
