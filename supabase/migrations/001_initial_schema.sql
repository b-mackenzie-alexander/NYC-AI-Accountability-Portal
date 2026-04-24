-- Migration: 001_initial_schema
-- Run this against your Railway Postgres instance.
-- Connect via: psql $DATABASE_URL -f supabase/migrations/001_initial_schema.sql
-- Or paste into any Postgres SQL client.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- AI system disclosures extracted from agency PDFs
CREATE TABLE IF NOT EXISTS ai_disclosures (
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency_name           TEXT NOT NULL,
  system_name           TEXT NOT NULL,
  purpose               TEXT,
  vendor                TEXT,
  data_sources          TEXT[],
  audit_date            DATE,
  audit_findings        TEXT,
  disclosure_source_url TEXT,
  extracted_at          TIMESTAMPTZ DEFAULT now(),
  extraction_confidence FLOAT CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1)
);

-- Outcome statistics from NYC Open Data (Socrata)
CREATE TABLE IF NOT EXISTS outcome_data (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agency         TEXT NOT NULL,
  dataset_id     TEXT NOT NULL,
  year           INT NOT NULL,
  race_ethnicity TEXT,
  outcome_type   TEXT NOT NULL,
  count          INT,
  rate           FLOAT,
  ingested_at    TIMESTAMPTZ DEFAULT now(),
  UNIQUE (agency, dataset_id, year, race_ethnicity, outcome_type)
);

-- Generated bias signals from analysis pipelines
CREATE TABLE IF NOT EXISTS bias_signals (
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

-- Anonymous complaint intake — no PII fields by design
CREATE TABLE IF NOT EXISTS complaints (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  complaint_token      TEXT UNIQUE NOT NULL,
  complaint_nonce      TEXT NOT NULL,
  agency               TEXT NOT NULL,
  system_name          TEXT,
  incident_description TEXT NOT NULL,
  affected_service     TEXT,
  submitted_at         TIMESTAMPTZ DEFAULT now()
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_disclosures_agency ON ai_disclosures (agency_name);
CREATE INDEX IF NOT EXISTS idx_signals_agency ON bias_signals (agency);
CREATE INDEX IF NOT EXISTS idx_signals_severity ON bias_signals (severity);
CREATE INDEX IF NOT EXISTS idx_outcome_agency_year ON outcome_data (agency, year);
CREATE INDEX IF NOT EXISTS idx_complaints_token ON complaints (complaint_token);

-- Row Level Security
-- complaints: no client access at all (backend service key only)
ALTER TABLE complaints ENABLE ROW LEVEL SECURITY;

-- Other tables: public read, no client writes
ALTER TABLE ai_disclosures ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public read ai_disclosures"
  ON ai_disclosures FOR SELECT USING (true);

ALTER TABLE bias_signals ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public read bias_signals"
  ON bias_signals FOR SELECT USING (true);

ALTER TABLE outcome_data ENABLE ROW LEVEL SECURITY;
CREATE POLICY "public read outcome_data"
  ON outcome_data FOR SELECT USING (true);
