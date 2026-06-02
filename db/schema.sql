PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS load_runs (
  load_run_id INTEGER PRIMARY KEY,
  loaded_at TEXT NOT NULL,
  input_fingerprint TEXT NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS sources (
  source_key TEXT PRIMARY KEY,
  source_url TEXT,
  source_type TEXT,
  title TEXT,
  fetched_at TEXT,
  http_status INTEGER,
  sha256 TEXT,
  classification TEXT,
  quality_tier TEXT,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS people (
  person_key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  role TEXT,
  current_status TEXT,
  institution TEXT,
  profile_url TEXT,
  headshot_url TEXT,
  quality_tier TEXT,
  quality_notes_json TEXT,
  source_json TEXT,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS programs (
  program_key TEXT PRIMARY KEY,
  program_name TEXT NOT NULL,
  role TEXT,
  unit TEXT,
  institution TEXT,
  normalized_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS person_program_memberships (
  person_key TEXT NOT NULL REFERENCES people(person_key) ON DELETE CASCADE,
  program_key TEXT NOT NULL REFERENCES programs(program_key) ON DELETE CASCADE,
  source_key TEXT REFERENCES sources(source_key) ON DELETE SET NULL,
  population TEXT,
  training_year_label TEXT,
  current_status TEXT,
  role TEXT,
  PRIMARY KEY (person_key, program_key, source_key, population, training_year_label)
);

CREATE TABLE IF NOT EXISTS organizations (
  organization_id INTEGER PRIMARY KEY,
  organization_key TEXT NOT NULL UNIQUE,
  canonical_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  category TEXT,
  parent_name TEXT,
  resolver_status TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.0,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS organization_aliases (
  alias_id INTEGER PRIMARY KEY,
  organization_id INTEGER NOT NULL REFERENCES organizations(organization_id) ON DELETE CASCADE,
  alias TEXT NOT NULL,
  normalized_alias TEXT NOT NULL,
  source_context TEXT,
  confidence REAL NOT NULL DEFAULT 0.0,
  UNIQUE (organization_id, normalized_alias, source_context)
);

CREATE TABLE IF NOT EXISTS organization_identifiers (
  organization_id INTEGER NOT NULL REFERENCES organizations(organization_id) ON DELETE CASCADE,
  identifier_type TEXT NOT NULL,
  identifier_value TEXT NOT NULL,
  source TEXT,
  PRIMARY KEY (organization_id, identifier_type, identifier_value)
);

CREATE TABLE IF NOT EXISTS person_training_events (
  training_event_id INTEGER PRIMARY KEY,
  person_key TEXT NOT NULL REFERENCES people(person_key) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  raw_value TEXT NOT NULL,
  organization_id INTEGER REFERENCES organizations(organization_id) ON DELETE SET NULL,
  source_key TEXT REFERENCES sources(source_key) ON DELETE SET NULL,
  resolver_status TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.0,
  evidence_json TEXT
);

CREATE TABLE IF NOT EXISTS evidence_claims (
  evidence_id INTEGER PRIMARY KEY,
  person_key TEXT REFERENCES people(person_key) ON DELETE CASCADE,
  claim_type TEXT NOT NULL,
  claim_value TEXT NOT NULL,
  source_key TEXT REFERENCES sources(source_key) ON DELETE SET NULL,
  source_url TEXT,
  source_type TEXT,
  confidence REAL NOT NULL DEFAULT 0.0,
  status TEXT NOT NULL DEFAULT 'accepted',
  evidence_json TEXT
);

CREATE VIEW IF NOT EXISTS v_person_training AS
SELECT
  p.person_key,
  p.display_name,
  p.role,
  e.event_type,
  e.raw_value,
  o.canonical_name,
  o.category,
  e.resolver_status,
  e.confidence
FROM person_training_events e
JOIN people p ON p.person_key = e.person_key
LEFT JOIN organizations o ON o.organization_id = e.organization_id;

CREATE VIEW IF NOT EXISTS v_organization_review_queue AS
SELECT
  e.raw_value,
  e.event_type,
  COUNT(*) AS mention_count,
  e.resolver_status,
  o.canonical_name
FROM person_training_events e
LEFT JOIN organizations o ON o.organization_id = e.organization_id
GROUP BY e.raw_value, e.event_type, e.resolver_status, o.canonical_name
ORDER BY
  CASE e.resolver_status WHEN 'unresolved' THEN 0 WHEN 'cleaned_label' THEN 1 ELSE 2 END,
  mention_count DESC,
  e.raw_value;
