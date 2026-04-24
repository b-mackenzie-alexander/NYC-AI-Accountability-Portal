# AGENTS.md
## NYC AI Accountability Portal

This file has two sections:

1. **Coding Agent Guidelines** — instructions for AI coding agents (Claude Code, Cursor, Copilot, etc.) working on this codebase
2. **Application Agent Pipeline** — documentation of the LLM-powered agents built into the app itself

---

# Part 1: Coding Agent Guidelines

## Who Is Working on This Project

Four humans, each potentially using an AI coding agent:

| Person | Role | Branch prefix | Owns |
|---|---|---|---|
| Beatrice | CI/CD, Security, Testing | `feat/beatrice/` | `.github/`, `backend/tests/` |
| Saul | Python Backend | `feat/saul/` | `backend/app/` |
| Sonia | Supabase, Data | `feat/sonia/` | `supabase/`, `backend/app/data/` |
| William | Next.js Frontend | `feat/william/` | `frontend/` |

If you are an agent working for one of these people, stay within their ownership boundary. Do not modify files owned by another team member without explicit instruction.

## Critical Distinction: Two Upload Flows

This is the most common point of confusion. Do not conflate these two features.

### Admin PDF Upload — INTERNAL ONLY
- **Route:** `/admin/upload`
- **User:** Beatrice / Sonia (team members seeding the database)
- **API call:** `POST /disclosures/upload`
- **Purpose:** Load government disclosure PDFs so the extraction pipeline can process them
- **UI:** Minimal, no shared layout, no public nav link, never linked from any public page
- **Styling:** Functional only — judges never see this page
- **This is not a feature for residents. Do not treat it as one.**

### Resident Complaint Form — PUBLIC FACING
- **Route:** `/complaint`
- **User:** Everyday residents (Maria persona)
- **API call:** `POST /complaints`
- **Purpose:** Anonymous reporting of AI-influenced decisions
- **UI:** Full app layout, linked from Agency Overview, polished, mobile-friendly
- **No file upload.** Residents fill out a text form. They never upload documents.

## Public Navigation (Exact List)

Only these routes appear in any nav component or shared layout:
```
/                   Homepage
/agencies           Agency Directory
/agency/[slug]      Agency Overview
/complaint          Complaint Portal
/about              Methodology
```

`/admin/upload` must never appear in a nav component, footer, sitemap, or layout.

## Key Architecture Rules for Agents

- **Never call `fetch()` directly in components.** All API calls go through `frontend/lib/api.ts`.
- **Never reference `SUPABASE_SERVICE_KEY` in frontend code.** That key is backend-only.
- **Never add PII fields to the complaints table or complaint form.** No name, email, phone, or IP.
- **Never remove rate limit decorators** from `POST /complaints` or `POST /disclosures/upload`.
- **Never store malformed LLM output.** If Grok returns non-JSON or fails Pydantic validation, raise `HTTPException(422)`.
- **All PRs target `develop`, never `main` directly.**
- **Do not merge your own PRs.** Open the PR and stop.

## Before You Write Frontend Code

Ask: is this page public-facing or internal tooling? The answer determines layout, nav, styling level, and whether it appears in any sitemap or link.

## Before You Write Backend Code

Ask: does this endpoint mutate data? If yes, it needs rate limiting via `slowapi` and input sanitization before any DB write.

## Source of Truth for Each Area

| Question | Read this file |
|---|---|
| What are we building and why? | `PRD.md` |
| What does the full system look like? | `ARCHITECTURE.md` |
| What tasks are in progress? | `ROADMAP.md` |
| What decisions have been made and why? | `NOTES.md` |
| What domain knowledge underlies the product? | `KNOWLEDGE.md` |
| How does the LLM extraction pipeline work? | Part 2 of this file (below) |

---

# Part 2: Application Agent Pipeline Documentation

This section documents the LLM-powered agentic workflows built into the application itself. It covers the multi-step agent chain used for PDF extraction, the design rationale for each step, and how to extend or debug the pipeline.

---

## Overview

The application uses a sequential multi-agent pipeline for PDF document processing. Each agent has a single, scoped responsibility. Output from one agent becomes input to the next. No agent has access to state from previous pipeline runs — each invocation is stateless.

```
[PDF Text]
    │
    ▼
┌─────────────────────┐
│  Classifier Agent   │  → Determines document type and extraction strategy
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Extraction Agent   │  → Pulls structured AI system data from document text
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Validation Agent   │  → Checks extracted data for completeness and flags gaps
└─────────┬───────────┘
          │
          ▼
   [Structured JSON → Supabase]
```

All agents use the Grok API (xAI) via the OpenAI-compatible client. Model: `grok-3` (fallback: `grok-3-mini`).

---

## Agent 1: Classifier Agent

**File:** `backend/app/services/agents/classifier.py`

**Purpose:** Determine what kind of government document has been uploaded and select the appropriate extraction strategy.

**Input:** Raw text extracted from PDF (string)

**Output:**
```json
{
  "document_type": "ll35_annual_report" | "ll144_bias_audit" | "agency_policy" | "unknown",
  "agency_name": "string or null",
  "confidence": 0.0–1.0,
  "extraction_strategy": "full" | "partial" | "skip",
  "notes": "string — why this classification was chosen"
}
```

**System Prompt:**
```
You are a government document classifier specializing in NYC agency AI disclosure filings.

Given raw text from a government PDF, identify:
1. The document type (LL35 annual AI system report, LL144 bias audit, agency policy document, or unknown)
2. The agency name if present
3. Whether the document contains extractable AI system disclosure data

Return ONLY a valid JSON object matching this schema:
{
  "document_type": "ll35_annual_report" | "ll144_bias_audit" | "agency_policy" | "unknown",
  "agency_name": "string or null",
  "confidence": 0.0,
  "extraction_strategy": "full" | "partial" | "skip",
  "notes": "string"
}

Use extraction_strategy "skip" if the document contains no AI system disclosure data.
Use "partial" if disclosure data is present but incomplete or ambiguous.
Use "full" if the document is a clear AI system disclosure filing.
```

**Downstream behavior:**
- If `extraction_strategy == "skip"`: pipeline halts, returns empty systems array with note
- If `confidence < 0.5`: pipeline halts, returns HTTP 422 with classifier note
- Otherwise: passes `document_type` and `agency_name` to Extraction Agent

---

## Agent 2: Extraction Agent

**File:** `backend/app/services/agents/extractor.py`

**Purpose:** Extract structured AI system records from the classified document.

**Input:**
- Raw document text (string)
- `document_type` from Classifier Agent
- `agency_name` from Classifier Agent (or from request if classifier returned null)

**Output:**
```json
{
  "agency_name": "string",
  "systems": [
    {
      "system_name": "string",
      "purpose": "string or null",
      "vendor": "string or null",
      "data_sources": ["array of strings"],
      "audit_date": "YYYY-MM-DD or null",
      "audit_findings": "string or null",
      "population_affected": "string or null",
      "decision_type": "string or null"
    }
  ],
  "extraction_confidence": 0.0–1.0,
  "missing_fields_note": "string"
}
```

**System Prompt:**
```
You are an AI governance analyst specializing in public sector algorithmic accountability.

You will receive raw text from a government agency AI disclosure document. Extract structured information about every AI or automated decision system mentioned.

Return ONLY a valid JSON object. Use null for fields you cannot confidently extract.

Rules:
- Extract ALL systems mentioned, even if details are sparse.
- Do not infer or hallucinate information not present in the text.
- extraction_confidence reflects your confidence that you captured all systems (0.0 = uncertain, 1.0 = confident).
- If the document has no AI disclosures, return an empty systems array with extraction_confidence 1.0 and an explanatory note.
- Do not merge multiple systems into one record.
```

**Validation rules applied to output:**
- `system_name` must be non-null and non-empty for every record — records missing this are dropped
- `extraction_confidence` must be a float 0.0–1.0 — if absent, default to 0.5 and log warning
- If `systems` is empty and `extraction_confidence > 0.8`: store as legitimate empty disclosure
- If `systems` is empty and `extraction_confidence < 0.8`: flag for human review

---

## Agent 3: Validation Agent

**File:** `backend/app/services/agents/validator.py`

**Purpose:** Review extracted records for internal consistency and flag potential issues before database insert.

**Input:** Full Extraction Agent output (JSON)

**Output:**
```json
{
  "validated_systems": [
    {
      "system_name": "string",
      "...(all extraction fields)": "...",
      "validation_flags": ["array of flag strings — empty if clean"]
    }
  ],
  "overall_quality": "high" | "medium" | "low",
  "review_recommended": true | false,
  "validation_notes": "string"
}
```

**Validation checks (deterministic, not LLM-based):**

The Validation Agent is **not an LLM call**. It is a Python function that applies deterministic rules to the Extraction Agent's output:

```python
def validate_extraction(extraction: ExtractionResult) -> ValidationResult:
    flags_by_system = {}
    for system in extraction.systems:
        flags = []
        if not system.purpose:
            flags.append("missing_purpose")
        if not system.data_sources:
            flags.append("missing_data_sources")
        if not system.audit_date and not system.audit_findings:
            flags.append("no_audit_information")
        if system.system_name.lower() in VAGUE_NAMES:  # ["system", "tool", "model", "algorithm"]
            flags.append("vague_system_name")
        flags_by_system[system.system_name] = flags

    quality = "high" if extraction.extraction_confidence > 0.8 else \
              "medium" if extraction.extraction_confidence > 0.5 else "low"

    return ValidationResult(
        validated_systems=[...],
        overall_quality=quality,
        review_recommended=quality == "low" or any(flags_by_system.values()),
        validation_notes=f"{len(extraction.systems)} systems extracted. Quality: {quality}."
    )
```

**Why deterministic validation instead of a third LLM call:**
LLM-based validation introduces latency and cost for checks that are better handled by rules. The Validation Agent adds no API cost and runs in < 1ms.

---

## Pipeline Orchestration

**File:** `backend/app/services/extraction_pipeline.py`

```python
async def run_extraction_pipeline(
    pdf_text: str,
    agency_name: str,
    source_url: str,
) -> PipelineResult:

    # Step 1: Classify
    classification = await classifier_agent.run(pdf_text)
    if classification.extraction_strategy == "skip":
        return PipelineResult(systems=[], skipped=True, reason=classification.notes)
    if classification.confidence < 0.5:
        raise HTTPException(status_code=422, detail=classification.notes)

    # Step 2: Extract
    resolved_agency = classification.agency_name or agency_name
    extraction = await extractor_agent.run(
        text=pdf_text,
        document_type=classification.document_type,
        agency_name=resolved_agency,
    )

    # Step 3: Validate (deterministic)
    validation = validate_extraction(extraction)

    # Step 4: Persist
    records = await supabase.insert_disclosures(
        validated_systems=validation.validated_systems,
        agency_name=resolved_agency,
        source_url=source_url,
        extraction_confidence=extraction.extraction_confidence,
    )

    # Step 5: Trigger gap detection (synchronous, uses known_systems.json)
    gaps = detect_disclosure_gaps(
        disclosures=records,
        agency=resolved_agency,
    )
    await supabase.upsert_signals(gaps)

    return PipelineResult(
        systems=records,
        gaps=gaps,
        validation=validation,
        extraction_confidence=extraction.extraction_confidence,
    )
```

---

## Error Handling

| Error | Cause | Response |
|---|---|---|
| `422 Unprocessable Entity` | PDF is scanned (no text layer) | `"PDF appears to be scanned. Text extraction not supported."` |
| `422 Unprocessable Entity` | Classifier confidence < 0.5 | Classifier's `notes` field returned to caller |
| `429 Too Many Requests` | Grok rate limit hit | Retry once with `grok-3-mini`; if still 429, return `503` |
| `500 Internal Server Error` | Grok returns non-JSON | Log raw response; return `"LLM extraction failed. Try again."` |
| Partial extraction | Some fields null | Stored as-is with `extraction_confidence` score; UI shows warning badge |

---

## Debugging the Pipeline

To test the pipeline against a specific PDF without going through the HTTP endpoint:

```bash
cd backend
python -m app.services.extraction_pipeline --pdf path/to/file.pdf --agency "ACS"
```

This runs the full pipeline and prints the `PipelineResult` as JSON to stdout. Useful for verifying a new PDF before loading it into the demo.

To inspect what the Classifier Agent sees:

```bash
python -m app.services.agents.classifier --pdf path/to/file.pdf
```

---

## Extending the Pipeline

**To add a new document type:**
1. Add the type string to `document_type` enum in `backend/app/models/pipeline.py`
2. Update the Classifier Agent's system prompt to recognize it
3. Add any type-specific extraction instructions to the Extractor Agent's prompt via a `document_type_hint` parameter

**To add a new agency's known systems:**
Edit `backend/app/data/known_systems.json`. Each entry requires:
```json
{
  "agency": "Full official agency name",
  "system_name": "Exact system name as it appears in external documentation",
  "description": "Brief description",
  "source_urls": ["url1", "url2"]  // minimum 2 URLs required
}
```

**To swap the LLM provider:**
Change `GROK_API_KEY` and `base_url` in `backend/app/services/grok_client.py`. The prompts are provider-agnostic. If switching to a provider without OpenAI-compatible API, update the client initialization only — prompts do not change.

---

## Claude Code Integration Notes

When working with this pipeline in Claude Code:

- The Grok API client in `grok_client.py` uses `AsyncOpenAI` — all agent calls must be `await`ed
- Extraction results are validated against Pydantic models before any database operation — do not bypass validation
- The `known_systems.json` file is the source of truth for disclosure gap detection — do not hardcode agency/system names in the analysis service
- Agent prompts live in `extraction_prompt.py` and `classifier_prompt.py` — changes to prompt schema must be reflected in the corresponding Pydantic models
