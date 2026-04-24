# KNOWLEDGE.md
## NYC AI Accountability Portal — Domain Knowledge Base

This file captures the domain knowledge the team needs to build and present this project accurately. It is the source of truth for policy context, methodology rationale, and key terminology. Update it as you learn more.

---

## 1. NYC AI Governance — Legal Landscape

### Local Law 35 of 2022 (AI Inventory Requirement)
- Requires NYC agencies to publish an annual report inventorying their automated systems
- Covers any system that "uses machine learning, statistical modeling, data analytics, or artificial intelligence" to make or support decisions affecting individuals
- Reports are due annually but are published as PDFs and web pages — no machine-readable format required
- **The gap this project addresses:** The disclosures are unstructured, inconsistent across agencies, and do not name all systems in use. External documentation reveals systems absent from official filings.
- **Where reports live:** Published on individual agency websites and the NYC Mayor's Office of Operations site

### Local Law 144 of 2021 (Automated Employment Decision Tools — AEDT)
- Requires companies using automated tools in NYC hiring or promotion decisions to conduct annual bias audits
- Audit results must be published on the company's website
- Covers selection rate disparities by sex, race/ethnicity, and intersectional categories
- **Relevance to this project:** Establishes the audit disclosure precedent we extend to public agencies. The enforcement gap (state auditors found 17 violations where city found 1) is a concrete example of the accountability problem.

### NYC GUARD Act (November 2025)
- **Full name:** Governing and Reforming the Use of Algorithmic Resources by the Department (GUARD) Act — exact official title may vary
- **Key provision:** Created the Office of Algorithmic Data Accountability (OADA), an independent watchdog
- **OADA mandate:** Review and audit AI tools before and after agency deployment, investigate public complaints, publish a directory of every AI system it evaluates
- **The gap:** OADA exists on paper. The directory it is mandated to publish does not yet exist. This project builds a public version of it.
- **Why this matters for the pitch:** We are not building a nice-to-have dashboard. We are building infrastructure the law requires but the city hasn't delivered.

### NYC Administrative Code — Relevant Sections
- Section 23-501 through 23-506: defines automated decision systems subject to LL35
- Key definition: "automated decision system" includes systems that generate "assessments, predictions, recommendations, or decisions"

---

## 2. ACS and the Severe Harm Predictive Risk Model

### What ACS Is
The Administration for Children's Services (ACS) is the NYC agency responsible for child welfare: investigating abuse and neglect reports, providing preventive services to at-risk families, and overseeing foster care placements. It receives approximately 60,000 reports per year.

### What the Severe Harm Predictive Risk Model Is
- A machine learning model deployed by ACS to score families at the time of an abuse/neglect report
- The score predicts the likelihood of a child in the household experiencing severe harm (defined as injury serious enough to require hospitalization, or death)
- Scores are generated before an investigation begins and are visible to investigators
- **The concern:** The model uses historical ACS data, which reflects historical patterns of racially disparate surveillance and intervention. If Black families are over-investigated historically (independent of actual harm rates), the model learns that pattern and perpetuates it.

### Why It Doesn't Appear in Official Disclosures
- ACS has not named the Severe Harm PRM by name in its LL35 annual reports
- The model is documented in academic literature, advocacy reports, and news coverage
- This absence is the central demonstration of our disclosure gap detection feature
- **Auditable claim:** Compare the ACS LL35 annual report PDF against external documentation. The system is named in external sources but not in official filings.

### Key External Documentation Sources (for `known_systems.json`)
These are the citations that give our disclosure gap signal credibility:
1. Administration for Children and Families (federal) — published documentation of the model's design
2. ACLU of New York — published analysis of ACS algorithmic tools and disparate impact concerns
3. The Chronicle of Social Change — investigative coverage of predictive tools in child welfare
4. Academic literature: Eubanks, Virginia. *Automating Inequality* (2018) — Chapter on child welfare prediction tools (broader context)
5. Center for Court Innovation — research on ACS intervention patterns

**Action item for Sonia:** Find the current, direct URLs for items 1–3 and add to `known_systems.json`. These must be real, clickable URLs — do not use placeholder links in the demo.

### Known Disparities in ACS Data
Published research and ACS administrative data show:
- Black children are referred to ACS at significantly higher rates than white children at equivalent income levels
- Black families are more likely to have children removed to foster care than white families with similar risk profiles
- These disparities are documented in multiple peer-reviewed studies and are not disputed by ACS
- **This is what our disparity signals surface** — the question our tool raises is whether the Severe Harm PRM amplifies these patterns

---

## 3. Disparity Analysis Methodology

### What Disparate Impact Means
Disparate impact occurs when a facially neutral policy or practice produces outcomes that are disproportionately negative for members of a protected class (race, sex, national origin, etc.), regardless of intent. This is a legal standard rooted in civil rights law (Griggs v. Duke Power Co., 1971).

Our tool surfaces statistical signals of potential disparate impact. It does not make legal findings. The Methodology page must state this clearly.

### The 4/5ths Rule (EEOC Uniform Guidelines)
The EEOC uses an 80% rule as a practical test: if the selection rate for a protected group is less than 4/5ths (80%) of the rate for the group with the highest rate, adverse impact is indicated. Equivalently: if the disparity ratio exceeds 1.25x, it warrants investigation.

**How we adapt this:**
- We calculate over-representation ratios (higher rate = worse outcome in child welfare context)
- Our threshold: 1.2x = low, 1.5x = medium, 2.0x = high
- The 1.2x threshold is slightly more conservative than the EEOC's 1.25x, which is a defensible choice — we surface more, not fewer, signals

### Disparity Ratio Calculation
```
disparity_ratio = group_rate / reference_group_rate
```
- Reference group: White Non-Hispanic (standard in published literature on ACS disparities)
- If reference group is absent from dataset: skip calculation, log warning, do not substitute another group
- If reference group rate = 0: skip calculation (division by zero)
- Round ratio to 2 decimal places for display

### Why Disparity Ratio, Not Raw Counts
Raw counts are misleading because population sizes differ. A rate (count / eligible population) normalizes for group size. We use rates from the Socrata dataset directly — we do not recalculate rates from counts, which avoids errors from incomplete population denominators.

### What We Cannot Claim
The methodology page must state all of the following:
1. Statistical disparity does not prove causation
2. We cannot determine from this data alone whether the AI system causes the disparity or reflects pre-existing patterns
3. Our analysis uses aggregate public data — individual case outcomes are not accessible
4. The tool surfaces signals for investigation, not conclusions

These caveats are not weakness — they are what makes the tool credible to researchers and journalists.

---

## 4. NYC Open Data / Socrata

### How Socrata Works
- Base URL: `https://data.cityofnewyork.us/resource/{dataset_id}.json`
- Query language: SoQL (Socrata Query Language) — SQL-like, passed as URL parameters
- No authentication required for public datasets
- Rate limits: generous without a token; register a free App Token at data.cityofnewyork.us to increase limits
- Response format: JSON array of objects

### Useful SoQL Patterns
```
# Filter by field value
?$where=agency='ACS'

# Limit results
?$limit=1000

# Order by field
?$order=year DESC

# Select specific columns
?$select=race_ethnicity,count,rate,year

# Combine
?$where=year=2023&$select=race_ethnicity,count,rate&$limit=500
```

### Dataset ID Verification Process
Dataset IDs change when agencies re-publish datasets under new names. Before running ingest:
1. Go to `data.cityofnewyork.us`
2. Search for the dataset by name
3. Open the dataset, click "API" — the dataset ID is in the endpoint URL
4. Update `backend/app/data/socrata_datasets.json` with the verified ID and date verified

### Data Quality Notes
- Race/ethnicity field names are not standardized across datasets — map to a canonical set before storing
- Some datasets suppress values for small counts (privacy protection) — these appear as null or "*"
- Foster care placement data may have a 1–2 year lag — use the most recent available year
- Rate fields may be expressed as percentages (0–100) or proportions (0–1) — verify and normalize before storing

---

## 5. LLM Extraction — Prompt Engineering Notes

### Why Structured Output Matters
The Extraction Agent must return valid JSON every time. Inconsistent output breaks the pipeline. Key techniques:

1. **Use `response_format: {"type": "json_object"}`** — forces JSON mode on Grok (same as OpenAI). The model cannot output prose.
2. **Define the schema explicitly in the system prompt** — do not rely on the model inferring it
3. **Use null, not absence** — instruct the model to include all fields and use `null` for unknown values, rather than omitting fields. Omitted fields break Pydantic validation.
4. **Calibrate confidence** — ask the model to rate its own confidence honestly. A confident model returning empty results is more useful than a low-confidence model hallucinating.

### What Government PDFs Look Like
Agency LL35 reports are typically:
- 10–40 pages, mostly prose
- Tables are rare; when present, pdfplumber extracts them as tab-separated text
- System names are often buried in paragraphs, not highlighted
- Vendors are frequently not named
- Audit information is usually absent or vague

This means `extraction_confidence` will often be 0.5–0.7 for real documents. That is expected and honest.

### Common Extraction Failures and Fixes
| Failure | Cause | Fix |
|---|---|---|
| Empty `systems` array with high confidence | Document genuinely has no disclosures | Expected — store as legitimate empty disclosure |
| System name is "N/A" or "None" | Model confused by document structure | Caught by Validation Agent's vague name check |
| `audit_date` is a year string ("2023") not a date | Model outputs partial date | Normalize to "2023-01-01" before storing; log warning |
| `data_sources` is a string, not array | Model wraps single source in string | Pydantic coerces; add union type to model |
| Duplicate systems extracted | System mentioned multiple times in doc | Dedup by `system_name` before insert |

### Grok-Specific Notes
- Grok 3 is highly capable at structured extraction from government documents
- `grok-3-mini` is faster (~2s vs ~6s) and adequate for shorter documents; use as rate-limit fallback
- Grok respects the `null` instruction reliably — better than some models that hallucinate values
- Max context: well above the text length of any realistic LL35 PDF (no chunking needed for typical documents)

---

## 6. Security & Privacy Domain Knowledge

### Why No PII on Complaint Forms
Beyond our design choice, there are legal reasons to avoid collecting PII:
- NYC Local Law 49 of 2022 requires agencies (and arguably tools serving city residents) to publish privacy policies for any personal data collection
- CCPA/state privacy law compliance adds complexity we don't need for a hackathon
- The ACLU and advocacy orgs that would use this tool are sensitive to any surveillance risk for their clients
- **Practical:** A complaint without a name is still useful for aggregation. Patterns across anonymous complaints (same agency, same system, same time period) are analytically meaningful.

### HMAC Token Design Rationale
We use HMAC-SHA256 for complaint tokens rather than a simple UUID because:
- UUIDs are guessable in sequence — an attacker could enumerate complaint IDs
- HMAC tokens are not guessable without the secret key
- The nonce + token design means the token is unforgeable: someone who sees your token cannot generate a different valid token
- This is not cryptographically necessary for a hackathon — it's a story we can tell judges about principled security design

### Rate Limiting Rationale
10 requests/IP/hour on the complaint endpoint is not primarily a DoS concern (Supabase free tier handles writes comfortably). It's a data quality concern: we want complaint aggregation to reflect real community experience, not a bot campaign. Frame it this way to judges.

---

## 7. Key Terminology

| Term | Definition |
|---|---|
| **Automated Decision System (ADS)** | Any system using ML, statistics, or AI to generate assessments, predictions, recommendations, or decisions affecting people (NYC LL35 definition) |
| **Automated Employment Decision Tool (AEDT)** | Narrower: tools used specifically in hiring/promotion decisions (NYC LL144 definition) |
| **Predictive Risk Model (PRM)** | A specific type of ADS that outputs a risk score predicting a future outcome — the Severe Harm PRM is an example |
| **Disparate Impact** | When a neutral policy produces disproportionately negative outcomes for a protected class, regardless of intent |
| **Disparity Ratio** | group_rate / reference_group_rate — our primary measure. > 1.0 = over-representation |
| **Disclosure Gap** | A system documented in external sources but absent from official agency disclosures |
| **LL35** | Local Law 35 of 2022 — NYC AI inventory requirement |
| **LL144** | Local Law 144 of 2021 — NYC AEDT bias audit requirement |
| **GUARD Act** | NYC law (November 2025) creating the Office of Algorithmic Data Accountability |
| **OADA** | Office of Algorithmic Data Accountability — the new watchdog created by the GUARD Act |
| **Socrata** | The open data platform NYC uses. Exposes a REST API with SoQL query language |
| **SoQL** | Socrata Query Language — SQL-like query syntax for Socrata APIs |
| **RLS** | Row Level Security — Supabase/Postgres feature that controls data access at the row level |
| **Extraction Confidence** | A 0.0–1.0 score the LLM assigns to its own extraction, reflecting how complete and reliable it believes the output is |

---

## 8. Judge Q&A Preparation

Likely questions and defensible answers:

**"How do you know the disparity ratios are accurate?"**
Every signal links to the source Socrata dataset and year. The calculation is documented in ARCHITECTURE.md and on our Methodology page. Judges can reproduce it manually with the dataset ID we publish. We spot-checked 3 groups against hand calculations — see NOTES.md.

**"How do you handle the fact that LLMs hallucinate?"**
The Extraction Agent is instructed to return null rather than guess. Every extracted record shows its confidence score. Low-confidence extractions are flagged in the UI. The original PDF is retained in Supabase Storage — anyone can verify the extraction against the source document.

**"Isn't this just showing correlation, not causation?"**
Yes, and we say so explicitly on the Methodology page. The tool surfaces signals for investigation, not legal conclusions. A 2x disparity ratio is a question, not an answer. The disclosure gap feature is about transparency accountability, not causal attribution.

**"What stops bad actors from filing fake complaints?"**
Rate limiting (10/IP/hour). No PII collected means there's no data worth stealing. The complaint data is used for aggregation, not individual action — a bot campaign would skew the distribution in ways a human reviewer would notice.

**"Why ACS specifically?"**
The Severe Harm PRM is one of the most documented and contested AI systems in NYC government. It affects a vulnerable population. The gap between what external researchers have documented and what ACS officially discloses is concrete and verifiable. It's the strongest possible demo of the disclosure gap feature.

**"What happens after the hackathon?"**
The OADA needs tools. This is open source. The complaint intake directly mirrors the public complaint process the GUARD Act mandates. We're building the de facto registry while the official one is being built.

---

## 9. Reference Links

*Fill in with verified URLs during the hackathon. Do not use placeholder URLs in the demo.*

| Resource | URL | Notes |
|---|---|---|
| NYC LL35 ACS Annual Report | [TO BE FOUND] | Most recent year; this is the PDF we ingest |
| NYC GUARD Act text | [TO BE FOUND] | Official legislation |
| OADA official page | [TO BE FOUND] | If it exists yet |
| ACS Severe Harm PRM — federal documentation | [TO BE FOUND] | For known_systems.json |
| ACS Severe Harm PRM — ACLU report | [TO BE FOUND] | For known_systems.json |
| NYC Open Data — ACS foster care dataset | [TO BE FOUND] | Verify Socrata ID |
| NYC Open Data — ACS service requests dataset | [TO BE FOUND] | Verify Socrata ID |
| Socrata App Token registration | https://data.cityofnewyork.us/profile/app_tokens | Register to avoid rate limits |
| Grok API documentation | https://docs.x.ai/api | Rate limits, models, pricing |
| Supabase RLS documentation | https://supabase.com/docs/guides/auth/row-level-security | RLS policy reference |
