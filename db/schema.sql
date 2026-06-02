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

CREATE TABLE IF NOT EXISTS source_utilities (
  utility_key TEXT PRIMARY KEY,
  display_name TEXT NOT NULL,
  source_family TEXT NOT NULL,
  default_tier TEXT NOT NULL,
  default_status TEXT NOT NULL,
  default_confidence REAL NOT NULL DEFAULT 0.0,
  claim_types_json TEXT NOT NULL,
  strengths_json TEXT NOT NULL,
  limitations_json TEXT NOT NULL,
  acceptance_rule TEXT NOT NULL,
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

CREATE TABLE IF NOT EXISTS program_lifecycle_rules (
  rule_key TEXT PRIMARY KEY,
  role TEXT NOT NULL,
  match_type TEXT NOT NULL,
  pattern TEXT,
  lifecycle_code TEXT NOT NULL,
  lifecycle_family TEXT NOT NULL,
  nominal_years INTEGER,
  entry_stage TEXT,
  terminal_stage TEXT,
  clock_rollover_month INTEGER NOT NULL,
  auto_advance INTEGER NOT NULL DEFAULT 0,
  source TEXT,
  confidence REAL NOT NULL DEFAULT 0.0,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS official_program_universe (
  official_program_key TEXT PRIMARY KEY,
  source_key TEXT,
  source_url TEXT NOT NULL,
  sponsoring_institution TEXT,
  department TEXT,
  program_type TEXT NOT NULL,
  program_name TEXT NOT NULL,
  program_url TEXT,
  source_type TEXT,
  confidence REAL NOT NULL DEFAULT 0.0,
  evidence_json TEXT
);

CREATE TABLE IF NOT EXISTS official_program_coverage_audit (
  official_program_key TEXT PRIMARY KEY REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  coverage_status TEXT NOT NULL,
  matched_program_key TEXT REFERENCES programs(program_key) ON DELETE SET NULL,
  matched_program_name TEXT,
  captured_people_count INTEGER NOT NULL DEFAULT 0,
  match_method TEXT,
  match_confidence REAL NOT NULL DEFAULT 0.0,
  discovery_classification TEXT,
  discovery_title TEXT,
  discovery_url TEXT,
  notes TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_program_source_probes (
  probe_id INTEGER PRIMARY KEY,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  program_name TEXT,
  coverage_status TEXT,
  source_role TEXT,
  requested_url TEXT NOT NULL,
  effective_url TEXT,
  http_status INTEGER,
  title TEXT,
  content_type TEXT,
  text_length INTEGER NOT NULL DEFAULT 0,
  roster_term_count INTEGER NOT NULL DEFAULT 0,
  context_term_count INTEGER NOT NULL DEFAULT 0,
  sha256 TEXT,
  fetched_at TEXT,
  error TEXT
);

CREATE TABLE IF NOT EXISTS official_program_source_candidates (
  candidate_key TEXT PRIMARY KEY,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  department TEXT,
  program_type TEXT,
  program_name TEXT,
  coverage_status TEXT,
  source_role TEXT,
  candidate_status TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0.0,
  candidate_title TEXT,
  candidate_url TEXT NOT NULL,
  http_status INTEGER,
  roster_term_count INTEGER NOT NULL DEFAULT 0,
  context_term_count INTEGER NOT NULL DEFAULT 0,
  reasons_json TEXT,
  evidence_json TEXT
);

CREATE TABLE IF NOT EXISTS official_program_gap_reason_audit (
  official_program_key TEXT PRIMARY KEY REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  department TEXT,
  program_type TEXT NOT NULL,
  program_name TEXT NOT NULL,
  coverage_status TEXT NOT NULL,
  gap_reason_status TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL,
  reason_confidence REAL NOT NULL DEFAULT 0.0,
  candidate_count INTEGER NOT NULL DEFAULT 0,
  roster_candidate_count INTEGER NOT NULL DEFAULT 0,
  context_candidate_count INTEGER NOT NULL DEFAULT 0,
  low_value_candidate_count INTEGER NOT NULL DEFAULT 0,
  probed_url_count INTEGER NOT NULL DEFAULT 0,
  reachable_probe_count INTEGER NOT NULL DEFAULT 0,
  low_content_probe_count INTEGER NOT NULL DEFAULT 0,
  max_roster_term_count INTEGER NOT NULL DEFAULT 0,
  max_context_term_count INTEGER NOT NULL DEFAULT 0,
  related_loaded_source_count INTEGER NOT NULL DEFAULT 0,
  related_loaded_person_count INTEGER NOT NULL DEFAULT 0,
  top_candidate_url TEXT,
  top_candidate_title TEXT,
  top_candidate_status TEXT,
  top_candidate_priority INTEGER,
  top_candidate_confidence REAL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_program_alias_reconciliation_candidates (
  reconciliation_key TEXT PRIMARY KEY,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_department TEXT,
  official_program_type TEXT NOT NULL,
  official_program_name TEXT NOT NULL,
  loaded_program_name TEXT,
  loaded_role TEXT,
  loaded_source_url TEXT,
  loaded_person_count INTEGER NOT NULL DEFAULT 0,
  loaded_training_labels TEXT,
  relation_status TEXT NOT NULL,
  suggested_mapping_action TEXT NOT NULL,
  relation_confidence REAL NOT NULL DEFAULT 0.0,
  coverage_mutation_allowed INTEGER NOT NULL DEFAULT 0,
  rationale TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_gap_roster_reconciliation (
  reconciliation_key TEXT PRIMARY KEY,
  source_key TEXT,
  candidate_key TEXT,
  source_url TEXT NOT NULL,
  effective_url TEXT,
  source_program_name TEXT,
  source_department TEXT,
  extraction_status TEXT NOT NULL,
  records_extracted INTEGER NOT NULL DEFAULT 0,
  loaded_membership_count INTEGER NOT NULL DEFAULT 0,
  loaded_person_count INTEGER NOT NULL DEFAULT 0,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE SET NULL,
  official_program_name TEXT,
  official_coverage_status TEXT,
  gap_reason_status TEXT,
  source_candidate_status TEXT,
  denominator_link_status TEXT NOT NULL,
  denominator_link_confidence REAL NOT NULL DEFAULT 0.0,
  recommended_next_action TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_gap_roster_program_resolution (
  resolution_key TEXT PRIMARY KEY,
  reconciliation_key TEXT REFERENCES official_gap_roster_reconciliation(reconciliation_key) ON DELETE CASCADE,
  source_key TEXT,
  source_url TEXT NOT NULL,
  source_program_name TEXT,
  source_department TEXT,
  inferred_source_role TEXT,
  records_extracted INTEGER NOT NULL DEFAULT 0,
  loaded_person_count INTEGER NOT NULL DEFAULT 0,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE SET NULL,
  official_program_name TEXT,
  official_program_type TEXT,
  official_department TEXT,
  resolution_status TEXT NOT NULL,
  resolution_confidence REAL NOT NULL DEFAULT 0.0,
  denominator_mutation_allowed INTEGER NOT NULL DEFAULT 0,
  recommended_next_action TEXT NOT NULL,
  match_features_json TEXT,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_program_coverage_assurance_audit (
  assurance_key TEXT PRIMARY KEY,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_program_name TEXT NOT NULL,
  official_program_type TEXT NOT NULL,
  official_department TEXT,
  coverage_status TEXT NOT NULL,
  captured_people_count INTEGER NOT NULL DEFAULT 0,
  matched_program_key TEXT,
  matched_program_name TEXT,
  match_method TEXT,
  match_confidence REAL NOT NULL DEFAULT 0.0,
  resolution_source_count INTEGER NOT NULL DEFAULT 0,
  resolution_record_count INTEGER NOT NULL DEFAULT 0,
  resolution_review_record_count INTEGER NOT NULL DEFAULT 0,
  alias_review_count INTEGER NOT NULL DEFAULT 0,
  alias_review_person_count INTEGER NOT NULL DEFAULT 0,
  assurance_status TEXT NOT NULL,
  assurance_level INTEGER NOT NULL DEFAULT 0,
  denominator_evidence_status TEXT NOT NULL,
  coverage_mutation_allowed INTEGER NOT NULL DEFAULT 0,
  recommended_next_action TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_program_coverage_action_queue (
  queue_key TEXT PRIMARY KEY,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_program_name TEXT NOT NULL,
  official_program_type TEXT NOT NULL,
  official_department TEXT,
  assurance_status TEXT NOT NULL,
  assurance_level INTEGER NOT NULL DEFAULT 0,
  coverage_status TEXT NOT NULL,
  action_lane TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  person_impact_count INTEGER NOT NULL DEFAULT 0,
  candidate_source_count INTEGER NOT NULL DEFAULT 0,
  candidate_url TEXT,
  official_program_url TEXT,
  blocker_status TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL,
  review_question TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_program_alias_review_packets (
  packet_key TEXT PRIMARY KEY,
  queue_key TEXT REFERENCES official_program_coverage_action_queue(queue_key) ON DELETE CASCADE,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_program_name TEXT NOT NULL,
  official_program_type TEXT NOT NULL,
  official_department TEXT,
  loaded_program_name TEXT,
  loaded_role TEXT,
  loaded_person_count INTEGER NOT NULL DEFAULT 0,
  loaded_source_url TEXT,
  action_lane TEXT NOT NULL,
  blocker_status TEXT NOT NULL,
  alias_decision_status TEXT NOT NULL,
  alias_confidence REAL NOT NULL DEFAULT 0.0,
  reviewer_ready INTEGER NOT NULL DEFAULT 0,
  coverage_mutation_allowed INTEGER NOT NULL DEFAULT 0,
  recommended_next_action TEXT NOT NULL,
  review_question TEXT NOT NULL,
  rationale TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_program_alias_reviewer_decision_queue (
  reviewer_decision_key TEXT PRIMARY KEY,
  packet_key TEXT NOT NULL REFERENCES official_program_alias_review_packets(packet_key) ON DELETE CASCADE,
  queue_key TEXT REFERENCES official_program_coverage_action_queue(queue_key) ON DELETE CASCADE,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_program_name TEXT NOT NULL,
  official_program_type TEXT NOT NULL,
  official_department TEXT,
  loaded_program_name TEXT,
  loaded_role TEXT,
  loaded_person_count INTEGER NOT NULL DEFAULT 0,
  loaded_source_url TEXT,
  alias_decision_status TEXT NOT NULL,
  alias_confidence REAL NOT NULL DEFAULT 0.0,
  queue_status TEXT NOT NULL,
  allowed_decisions TEXT NOT NULL,
  packet_fingerprint TEXT NOT NULL,
  required_confirmation_fields TEXT NOT NULL,
  required_reviewer_action TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL,
  review_question TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_program_alias_reviewer_decisions (
  reviewer_decision_key TEXT PRIMARY KEY,
  packet_key TEXT NOT NULL,
  packet_fingerprint TEXT NOT NULL,
  reviewer_decision TEXT NOT NULL,
  reviewer_name TEXT,
  decided_at TEXT,
  official_program_confirmed INTEGER NOT NULL DEFAULT 0,
  loaded_source_scope_confirmed INTEGER NOT NULL DEFAULT 0,
  role_scope_confirmed INTEGER NOT NULL DEFAULT 0,
  current_roster_confirmed INTEGER NOT NULL DEFAULT 0,
  decision_notes TEXT
);

CREATE TABLE IF NOT EXISTS official_program_alias_reviewer_decision_audit (
  reviewer_decision_key TEXT PRIMARY KEY,
  packet_key TEXT NOT NULL REFERENCES official_program_alias_review_packets(packet_key) ON DELETE CASCADE,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_program_name TEXT NOT NULL,
  official_program_type TEXT NOT NULL,
  official_department TEXT,
  loaded_program_name TEXT,
  loaded_role TEXT,
  loaded_person_count INTEGER NOT NULL DEFAULT 0,
  reviewer_decision TEXT NOT NULL,
  decision_status TEXT NOT NULL,
  accepted_alias_mapping INTEGER NOT NULL DEFAULT 0,
  decision_blocker TEXT NOT NULL,
  packet_fingerprint TEXT NOT NULL,
  decision_packet_fingerprint TEXT,
  official_program_confirmed INTEGER NOT NULL DEFAULT 0,
  loaded_source_scope_confirmed INTEGER NOT NULL DEFAULT 0,
  role_scope_confirmed INTEGER NOT NULL DEFAULT 0,
  current_roster_confirmed INTEGER NOT NULL DEFAULT 0,
  reviewer_name TEXT,
  decided_at TEXT,
  recommended_next_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accepted_official_program_alias_mappings (
  accepted_alias_key TEXT PRIMARY KEY,
  reviewer_decision_key TEXT NOT NULL REFERENCES official_program_alias_reviewer_decision_audit(reviewer_decision_key) ON DELETE CASCADE,
  packet_key TEXT NOT NULL REFERENCES official_program_alias_review_packets(packet_key) ON DELETE CASCADE,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_program_name TEXT NOT NULL,
  official_program_type TEXT NOT NULL,
  official_department TEXT,
  loaded_program_name TEXT NOT NULL,
  loaded_role TEXT,
  loaded_person_count INTEGER NOT NULL DEFAULT 0,
  loaded_source_url TEXT,
  alias_decision_status TEXT NOT NULL,
  packet_fingerprint TEXT NOT NULL,
  accepted_by TEXT,
  accepted_at TEXT,
  coverage_mutation_allowed INTEGER NOT NULL DEFAULT 0,
  display_safety_status TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  materialized_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS program_identifier_source_observations (
  observation_key TEXT PRIMARY KEY,
  identifier_source TEXT NOT NULL,
  query_scope TEXT NOT NULL,
  query_url TEXT NOT NULL,
  query_params_json TEXT NOT NULL,
  http_status INTEGER,
  result_count INTEGER NOT NULL DEFAULT 0,
  relevant_result_count INTEGER NOT NULL DEFAULT 0,
  content_sha256 TEXT,
  fetched_at TEXT NOT NULL,
  source_status TEXT NOT NULL,
  error_text TEXT
);

CREATE TABLE IF NOT EXISTS program_identifier_candidates (
  candidate_key TEXT PRIMARY KEY,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_program_type TEXT NOT NULL,
  official_program_name TEXT NOT NULL,
  official_department TEXT,
  identifier_type TEXT NOT NULL,
  identifier_value TEXT,
  identifier_source TEXT NOT NULL,
  source_program_specialty TEXT,
  source_program_name TEXT,
  source_city TEXT,
  source_state TEXT,
  source_status_json TEXT,
  source_url TEXT,
  candidate_status TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.0,
  match_reasons_json TEXT,
  evidence_json TEXT,
  observed_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS official_program_identifiers (
  identifier_key TEXT PRIMARY KEY,
  official_program_key TEXT NOT NULL REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  identifier_type TEXT NOT NULL,
  identifier_value TEXT NOT NULL,
  identifier_source TEXT NOT NULL,
  source_url TEXT,
  acceptance_status TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.0,
  accepted_from_candidate_key TEXT REFERENCES program_identifier_candidates(candidate_key) ON DELETE SET NULL,
  accepted_at TEXT NOT NULL,
  evidence_json TEXT,
  UNIQUE(official_program_key, identifier_type, identifier_value)
);

CREATE TABLE IF NOT EXISTS program_identifier_reconciliation (
  reconciliation_key TEXT PRIMARY KEY,
  candidate_key TEXT REFERENCES program_identifier_candidates(candidate_key) ON DELETE CASCADE,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  official_program_type TEXT NOT NULL,
  official_program_name TEXT NOT NULL,
  identifier_type TEXT NOT NULL,
  identifier_value TEXT,
  identifier_source TEXT NOT NULL,
  source_program_specialty TEXT,
  source_program_name TEXT,
  source_city TEXT,
  candidate_status TEXT NOT NULL,
  reconciliation_status TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  reconciliation_confidence REAL NOT NULL DEFAULT 0.0,
  rank_in_official_program INTEGER NOT NULL DEFAULT 0,
  candidate_count_for_program INTEGER NOT NULL DEFAULT 0,
  close_candidate_count INTEGER NOT NULL DEFAULT 0,
  rationale TEXT NOT NULL,
  evidence_json TEXT,
  reconciled_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS program_lifecycle_consistency_audit (
  audit_key TEXT PRIMARY KEY,
  official_program_key TEXT REFERENCES official_program_universe(official_program_key) ON DELETE CASCADE,
  matched_program_key TEXT REFERENCES programs(program_key) ON DELETE SET NULL,
  identifier_key TEXT REFERENCES official_program_identifiers(identifier_key) ON DELETE SET NULL,
  official_program_type TEXT NOT NULL,
  official_program_name TEXT NOT NULL,
  matched_program_name TEXT,
  identifier_type TEXT,
  identifier_value TEXT,
  source_program_specialty TEXT,
  coverage_status TEXT,
  lifecycle_status TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  lifecycle_confidence REAL NOT NULL DEFAULT 0.0,
  state_row_count INTEGER NOT NULL DEFAULT 0,
  coded_state_row_count INTEGER NOT NULL DEFAULT 0,
  unclassified_state_row_count INTEGER NOT NULL DEFAULT 0,
  lifecycle_code_count INTEGER NOT NULL DEFAULT 0,
  lifecycle_codes_json TEXT NOT NULL,
  rule_keys_json TEXT NOT NULL,
  rationale TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS person_evidence_review_packets (
  packet_key TEXT PRIMARY KEY,
  person_or_name_key TEXT NOT NULL,
  person_key TEXT,
  display_name TEXT NOT NULL,
  role TEXT,
  packet_status TEXT NOT NULL,
  review_kind TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL,
  acceptance_blocker TEXT NOT NULL,
  review_priority INTEGER NOT NULL DEFAULT 0,
  review_ready_record_count INTEGER NOT NULL DEFAULT 0,
  secondary_anchor_needed_count INTEGER NOT NULL DEFAULT 0,
  low_signal_record_count INTEGER NOT NULL DEFAULT 0,
  discovery_only_count INTEGER NOT NULL DEFAULT 0,
  publication_candidate_count INTEGER NOT NULL DEFAULT 0,
  attending_candidate_count INTEGER NOT NULL DEFAULT 0,
  current_attending_endpoint_count INTEGER NOT NULL DEFAULT 0,
  evidence_record_count INTEGER NOT NULL DEFAULT 0,
  best_decision TEXT,
  best_source_url TEXT,
  top_source_urls TEXT,
  top_claim_types TEXT,
  top_match_features TEXT,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
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

CREATE TABLE IF NOT EXISTS person_training_states (
  state_id INTEGER PRIMARY KEY,
  state_key TEXT NOT NULL UNIQUE,
  person_key TEXT NOT NULL REFERENCES people(person_key) ON DELETE CASCADE,
  program_key TEXT REFERENCES programs(program_key) ON DELETE SET NULL,
  source_key TEXT REFERENCES sources(source_key) ON DELETE SET NULL,
  observed_at TEXT NOT NULL,
  as_of_date TEXT NOT NULL,
  raw_stage_label TEXT,
  normalized_stage TEXT NOT NULL,
  stage_family TEXT NOT NULL,
  stage_index INTEGER,
  stage_rank INTEGER,
  trainee_category TEXT,
  lifecycle_rule_key TEXT REFERENCES program_lifecycle_rules(rule_key) ON DELETE SET NULL,
  lifecycle_code TEXT,
  lifecycle_stage TEXT,
  academic_year TEXT,
  estimated_start_date TEXT,
  estimated_end_date TEXT,
  expected_next_stage TEXT,
  expected_next_date TEXT,
  expected_exit_date TEXT,
  expected_transition_type TEXT,
  stale_after_date TEXT,
  refresh_policy TEXT,
  transition_rule TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'current',
  confidence REAL NOT NULL DEFAULT 0.0,
  evidence_json TEXT
);

CREATE TABLE IF NOT EXISTS training_state_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL,
  as_of_date TEXT NOT NULL,
  source_export_path TEXT NOT NULL,
  corpus_fingerprint TEXT NOT NULL,
  row_count INTEGER NOT NULL DEFAULT 0,
  canonical_key_count INTEGER NOT NULL DEFAULT 0,
  duplicate_canonical_key_count INTEGER NOT NULL DEFAULT 0,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS training_state_snapshot_rows (
  snapshot_id TEXT NOT NULL REFERENCES training_state_snapshots(snapshot_id) ON DELETE CASCADE,
  state_key TEXT NOT NULL,
  canonical_person_program_key TEXT NOT NULL,
  person_key TEXT NOT NULL,
  display_name TEXT,
  role TEXT,
  program_name TEXT,
  observed_at TEXT,
  as_of_date TEXT,
  raw_stage_label TEXT,
  normalized_stage TEXT NOT NULL,
  stage_family TEXT NOT NULL,
  stage_index INTEGER,
  stage_rank INTEGER,
  trainee_category TEXT,
  lifecycle_rule_key TEXT,
  lifecycle_code TEXT,
  lifecycle_stage TEXT,
  academic_year TEXT,
  estimated_start_date TEXT,
  estimated_end_date TEXT,
  expected_next_stage TEXT,
  expected_next_date TEXT,
  expected_exit_date TEXT,
  expected_transition_type TEXT,
  stale_after_date TEXT,
  refresh_policy TEXT,
  transition_rule TEXT,
  status TEXT,
  confidence REAL NOT NULL DEFAULT 0.0,
  source_key TEXT,
  state_fingerprint TEXT NOT NULL,
  PRIMARY KEY (snapshot_id, state_key)
);

CREATE INDEX IF NOT EXISTS idx_training_state_snapshot_rows_canonical
ON training_state_snapshot_rows(snapshot_id, canonical_person_program_key);

CREATE TABLE IF NOT EXISTS training_state_transition_events (
  transition_id INTEGER PRIMARY KEY,
  old_snapshot_id TEXT REFERENCES training_state_snapshots(snapshot_id) ON DELETE CASCADE,
  new_snapshot_id TEXT NOT NULL REFERENCES training_state_snapshots(snapshot_id) ON DELETE CASCADE,
  canonical_person_program_key TEXT NOT NULL,
  person_key TEXT,
  display_name TEXT,
  program_name TEXT,
  role TEXT,
  old_state_key TEXT,
  new_state_key TEXT,
  change_type TEXT NOT NULL,
  transition_assurance TEXT NOT NULL,
  expected_by_state_machine INTEGER NOT NULL DEFAULT 0,
  old_stage TEXT,
  new_stage TEXT,
  old_expected_next_stage TEXT,
  old_expected_next_date TEXT,
  old_expected_exit_date TEXT,
  old_expected_transition_type TEXT,
  old_stale_after_date TEXT,
  review_action TEXT NOT NULL,
  notes TEXT,
  evidence_json TEXT,
  UNIQUE(old_snapshot_id, new_snapshot_id, canonical_person_program_key)
);

CREATE TABLE IF NOT EXISTS training_state_transition_rollups (
  rollup_key TEXT PRIMARY KEY,
  old_snapshot_id TEXT,
  new_snapshot_id TEXT NOT NULL,
  rollup_scope TEXT NOT NULL,
  rollup_value TEXT NOT NULL,
  institution TEXT,
  role TEXT,
  trainee_category TEXT,
  program_name TEXT,
  lifecycle_code TEXT,
  change_type TEXT NOT NULL,
  transition_assurance TEXT NOT NULL,
  expected_by_state_machine INTEGER NOT NULL DEFAULT 0,
  event_count INTEGER NOT NULL DEFAULT 0,
  review_event_count INTEGER NOT NULL DEFAULT 0,
  expected_event_count INTEGER NOT NULL DEFAULT 0,
  evidence_json TEXT
);

CREATE TABLE IF NOT EXISTS training_state_machine_audit (
  state_id INTEGER,
  person_key TEXT NOT NULL,
  display_name TEXT,
  role TEXT,
  program_name TEXT,
  observed_at TEXT,
  as_of_date TEXT,
  raw_stage_label TEXT,
  normalized_stage TEXT,
  stage_family TEXT,
  stage_index INTEGER,
  stage_rank INTEGER,
  trainee_category TEXT,
  lifecycle_rule_key TEXT,
  lifecycle_code TEXT,
  lifecycle_stage TEXT,
  academic_year TEXT,
  estimated_start_date TEXT,
  estimated_end_date TEXT,
  expected_next_stage TEXT,
  expected_next_date TEXT,
  expected_exit_date TEXT,
  expected_transition_type TEXT,
  stale_after_date TEXT,
  refresh_policy TEXT,
  transition_rule TEXT,
  status TEXT,
  confidence REAL,
  source_key TEXT,
  audit_as_of_date TEXT NOT NULL,
  clock_model TEXT NOT NULL,
  state_machine_status TEXT NOT NULL,
  state_machine_reason TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  days_until_expected_next INTEGER,
  days_until_stale INTEGER,
  auto_advance_candidate INTEGER NOT NULL DEFAULT 0,
  completion_candidate INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS person_training_state_machine_audit (
  person_key TEXT PRIMARY KEY,
  display_name TEXT,
  role TEXT,
  program_count INTEGER NOT NULL DEFAULT 0,
  programs TEXT,
  state_observation_count INTEGER NOT NULL DEFAULT 0,
  canonical_diff_key_count INTEGER NOT NULL DEFAULT 0,
  duplicate_state_key_count INTEGER NOT NULL DEFAULT 0,
  worst_state_machine_status TEXT NOT NULL,
  worst_clock_model TEXT,
  worst_program_name TEXT,
  worst_normalized_stage TEXT,
  stale_state_count INTEGER NOT NULL DEFAULT 0,
  ready_for_expected_advancement_count INTEGER NOT NULL DEFAULT 0,
  review_required_count INTEGER NOT NULL DEFAULT 0,
  source_refresh_required_count INTEGER NOT NULL DEFAULT 0,
  annual_clock_active_count INTEGER NOT NULL DEFAULT 0,
  terminal_year_active_count INTEGER NOT NULL DEFAULT 0,
  recommended_action TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS program_training_state_machine_audit (
  program_name TEXT NOT NULL,
  role TEXT,
  person_count INTEGER NOT NULL DEFAULT 0,
  state_observation_count INTEGER NOT NULL DEFAULT 0,
  dominant_lifecycle_code TEXT,
  dominant_clock_model TEXT,
  worst_state_machine_status TEXT NOT NULL,
  stale_state_count INTEGER NOT NULL DEFAULT 0,
  ready_for_expected_advancement_count INTEGER NOT NULL DEFAULT 0,
  review_required_count INTEGER NOT NULL DEFAULT 0,
  source_refresh_required_count INTEGER NOT NULL DEFAULT 0,
  annual_clock_active_count INTEGER NOT NULL DEFAULT 0,
  terminal_year_active_count INTEGER NOT NULL DEFAULT 0,
  recommended_action TEXT NOT NULL,
  PRIMARY KEY (program_name, role)
);

CREATE TABLE IF NOT EXISTS training_state_refresh_expectations (
  state_id INTEGER,
  person_key TEXT NOT NULL,
  display_name TEXT,
  role TEXT,
  program_name TEXT,
  observed_at TEXT,
  as_of_date TEXT,
  raw_stage_label TEXT,
  normalized_stage TEXT,
  stage_family TEXT,
  stage_index INTEGER,
  stage_rank INTEGER,
  trainee_category TEXT,
  lifecycle_rule_key TEXT,
  lifecycle_code TEXT,
  lifecycle_stage TEXT,
  academic_year TEXT,
  estimated_start_date TEXT,
  estimated_end_date TEXT,
  expected_next_stage TEXT,
  expected_next_date TEXT,
  expected_exit_date TEXT,
  expected_transition_type TEXT,
  stale_after_date TEXT,
  refresh_policy TEXT,
  transition_rule TEXT,
  status TEXT,
  confidence REAL,
  source_key TEXT,
  projected_refresh_date TEXT NOT NULL,
  readiness_status TEXT NOT NULL,
  readiness_priority INTEGER NOT NULL,
  readiness_rationale TEXT NOT NULL,
  program_coverage_status TEXT,
  program_discovery_classification TEXT,
  expected_if_missing_on_refresh TEXT NOT NULL,
  missing_on_refresh_notes TEXT NOT NULL,
  expected_if_same_stage_on_refresh TEXT NOT NULL,
  same_stage_on_refresh_notes TEXT NOT NULL,
  expected_if_next_stage_on_refresh TEXT NOT NULL,
  next_stage_on_refresh_notes TEXT NOT NULL,
  advance_due_by_refresh INTEGER NOT NULL DEFAULT 0,
  stale_by_refresh INTEGER NOT NULL DEFAULT 0,
  completion_window_by_refresh INTEGER NOT NULL DEFAULT 0,
  requires_source_refresh_by_refresh INTEGER NOT NULL DEFAULT 0,
  requires_human_review_by_refresh INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS person_refresh_expectations (
  display_name TEXT,
  role TEXT,
  person_key TEXT PRIMARY KEY,
  person_count INTEGER NOT NULL DEFAULT 0,
  program_count INTEGER NOT NULL DEFAULT 0,
  state_observation_count INTEGER NOT NULL DEFAULT 0,
  worst_readiness_status TEXT NOT NULL,
  worst_readiness_priority INTEGER NOT NULL,
  dominant_program_coverage_status TEXT,
  expected_advancement_window_count INTEGER NOT NULL DEFAULT 0,
  expected_completion_window_count INTEGER NOT NULL DEFAULT 0,
  source_refresh_required_window_count INTEGER NOT NULL DEFAULT 0,
  review_required_window_count INTEGER NOT NULL DEFAULT 0,
  stale_without_transition_review_count INTEGER NOT NULL DEFAULT 0,
  unexpected_absence_review_count INTEGER NOT NULL DEFAULT 0,
  absence_requires_source_reconciliation_count INTEGER NOT NULL DEFAULT 0,
  expected_absence_after_completion_count INTEGER NOT NULL DEFAULT 0,
  recommended_refresh_action TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS program_refresh_expectations (
  program_name TEXT NOT NULL,
  role TEXT,
  person_count INTEGER NOT NULL DEFAULT 0,
  program_count INTEGER NOT NULL DEFAULT 0,
  state_observation_count INTEGER NOT NULL DEFAULT 0,
  worst_readiness_status TEXT NOT NULL,
  worst_readiness_priority INTEGER NOT NULL,
  dominant_program_coverage_status TEXT,
  expected_advancement_window_count INTEGER NOT NULL DEFAULT 0,
  expected_completion_window_count INTEGER NOT NULL DEFAULT 0,
  source_refresh_required_window_count INTEGER NOT NULL DEFAULT 0,
  review_required_window_count INTEGER NOT NULL DEFAULT 0,
  stale_without_transition_review_count INTEGER NOT NULL DEFAULT 0,
  unexpected_absence_review_count INTEGER NOT NULL DEFAULT 0,
  absence_requires_source_reconciliation_count INTEGER NOT NULL DEFAULT 0,
  expected_absence_after_completion_count INTEGER NOT NULL DEFAULT 0,
  recommended_refresh_action TEXT NOT NULL,
  PRIMARY KEY (program_name, role)
);

CREATE TABLE IF NOT EXISTS category_refresh_expectations (
  trainee_category TEXT NOT NULL,
  role TEXT,
  person_count INTEGER NOT NULL DEFAULT 0,
  program_count INTEGER NOT NULL DEFAULT 0,
  state_observation_count INTEGER NOT NULL DEFAULT 0,
  worst_readiness_status TEXT NOT NULL,
  worst_readiness_priority INTEGER NOT NULL,
  dominant_program_coverage_status TEXT,
  expected_advancement_window_count INTEGER NOT NULL DEFAULT 0,
  expected_completion_window_count INTEGER NOT NULL DEFAULT 0,
  source_refresh_required_window_count INTEGER NOT NULL DEFAULT 0,
  review_required_window_count INTEGER NOT NULL DEFAULT 0,
  stale_without_transition_review_count INTEGER NOT NULL DEFAULT 0,
  unexpected_absence_review_count INTEGER NOT NULL DEFAULT 0,
  absence_requires_source_reconciliation_count INTEGER NOT NULL DEFAULT 0,
  expected_absence_after_completion_count INTEGER NOT NULL DEFAULT 0,
  recommended_refresh_action TEXT NOT NULL,
  PRIMARY KEY (trainee_category, role)
);

CREATE TABLE IF NOT EXISTS training_lifecycle_assurance_rollups (
  rollup_key TEXT PRIMARY KEY,
  rollup_scope TEXT NOT NULL,
  rollup_value TEXT NOT NULL,
  role TEXT,
  trainee_category TEXT,
  program_name TEXT,
  lifecycle_code TEXT,
  projected_refresh_date TEXT NOT NULL,
  state_observation_count INTEGER NOT NULL DEFAULT 0,
  person_count INTEGER NOT NULL DEFAULT 0,
  program_count INTEGER NOT NULL DEFAULT 0,
  annual_clock_count INTEGER NOT NULL DEFAULT 0,
  expected_advancement_count INTEGER NOT NULL DEFAULT 0,
  expected_completion_count INTEGER NOT NULL DEFAULT 0,
  source_refresh_required_count INTEGER NOT NULL DEFAULT 0,
  human_review_required_count INTEGER NOT NULL DEFAULT 0,
  stale_by_refresh_count INTEGER NOT NULL DEFAULT 0,
  unexpected_absence_review_count INTEGER NOT NULL DEFAULT 0,
  deterministic_transition_count INTEGER NOT NULL DEFAULT 0,
  source_bound_transition_count INTEGER NOT NULL DEFAULT 0,
  review_bound_transition_count INTEGER NOT NULL DEFAULT 0,
  assurance_status TEXT NOT NULL,
  diff_readiness_status TEXT NOT NULL,
  stale_information_policy TEXT NOT NULL,
  recommended_operator_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS training_state_transition_plan (
  plan_key TEXT PRIMARY KEY,
  state_id INTEGER,
  person_key TEXT NOT NULL,
  display_name TEXT,
  role TEXT,
  trainee_category TEXT,
  program_name TEXT,
  institution TEXT NOT NULL,
  country TEXT NOT NULL,
  country_code TEXT NOT NULL,
  source_key TEXT,
  observed_at TEXT,
  as_of_date TEXT,
  projected_refresh_date TEXT NOT NULL,
  raw_stage_label TEXT,
  normalized_stage TEXT,
  stage_family TEXT,
  stage_index INTEGER,
  stage_rank INTEGER,
  academic_year TEXT,
  lifecycle_rule_key TEXT,
  lifecycle_code TEXT,
  lifecycle_stage TEXT,
  expected_next_stage TEXT,
  expected_next_date TEXT,
  expected_exit_date TEXT,
  expected_transition_type TEXT,
  stale_after_date TEXT,
  refresh_policy TEXT,
  readiness_status TEXT NOT NULL,
  state_machine_status TEXT,
  clock_model TEXT,
  policy_lane TEXT NOT NULL,
  diff_readiness_status TEXT NOT NULL,
  if_missing_change_type TEXT NOT NULL,
  if_same_stage_change_type TEXT NOT NULL,
  if_expected_next_stage_change_type TEXT NOT NULL,
  evidence_requirement TEXT NOT NULL,
  transition_classification_policy TEXT NOT NULL,
  recommended_operator_action TEXT NOT NULL,
  stale_by_refresh INTEGER NOT NULL DEFAULT 0,
  advance_due_by_refresh INTEGER NOT NULL DEFAULT 0,
  completion_window_by_refresh INTEGER NOT NULL DEFAULT 0,
  source_refresh_required_by_refresh INTEGER NOT NULL DEFAULT 0,
  human_review_required_by_refresh INTEGER NOT NULL DEFAULT 0,
  auto_classifiable_transition INTEGER NOT NULL DEFAULT 0,
  fresh_observation_required INTEGER NOT NULL DEFAULT 0,
  confidence REAL,
  evidence_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS training_state_transition_plan_rollups (
  rollup_key TEXT PRIMARY KEY,
  rollup_scope TEXT NOT NULL,
  rollup_value TEXT NOT NULL,
  institution TEXT,
  country TEXT,
  country_code TEXT,
  role TEXT,
  trainee_category TEXT,
  program_name TEXT,
  lifecycle_code TEXT,
  policy_lane TEXT,
  diff_readiness_status TEXT,
  projected_refresh_date TEXT NOT NULL,
  state_observation_count INTEGER NOT NULL DEFAULT 0,
  person_count INTEGER NOT NULL DEFAULT 0,
  program_count INTEGER NOT NULL DEFAULT 0,
  deterministic_advancement_count INTEGER NOT NULL DEFAULT 0,
  deterministic_completion_count INTEGER NOT NULL DEFAULT 0,
  source_refresh_required_count INTEGER NOT NULL DEFAULT 0,
  human_review_required_count INTEGER NOT NULL DEFAULT 0,
  no_change_expected_count INTEGER NOT NULL DEFAULT 0,
  stale_by_refresh_count INTEGER NOT NULL DEFAULT 0,
  auto_classifiable_transition_count INTEGER NOT NULL DEFAULT 0,
  fresh_observation_required_count INTEGER NOT NULL DEFAULT 0,
  dominant_policy_lane TEXT NOT NULL,
  dominant_diff_readiness_status TEXT NOT NULL,
  recommended_operator_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL
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

CREATE TABLE IF NOT EXISTS organization_identifier_candidates (
  candidate_key TEXT PRIMARY KEY,
  organization_key TEXT NOT NULL REFERENCES organizations(organization_key) ON DELETE CASCADE,
  canonical_name TEXT NOT NULL,
  category TEXT,
  mention_count INTEGER NOT NULL DEFAULT 0,
  source_name TEXT NOT NULL,
  query TEXT NOT NULL,
  identifier_type TEXT NOT NULL,
  identifier_value TEXT NOT NULL,
  candidate_name TEXT NOT NULL,
  candidate_types TEXT,
  candidate_country TEXT,
  candidate_links TEXT,
  match_status TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.0,
  match_reasons TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS medical_student_source_audit (
  audit_key TEXT PRIMARY KEY,
  source_url TEXT NOT NULL,
  source_title TEXT,
  source_scope TEXT NOT NULL,
  access_status TEXT NOT NULL,
  capture_status TEXT NOT NULL,
  source_role TEXT NOT NULL,
  observed_http_status INTEGER,
  effective_url TEXT,
  public_person_count_observed INTEGER NOT NULL DEFAULT 0,
  loaded_person_count INTEGER NOT NULL DEFAULT 0,
  md_phd_signal_count INTEGER NOT NULL DEFAULT 0,
  current_student_signal_count INTEGER NOT NULL DEFAULT 0,
  directory_signal_count INTEGER NOT NULL DEFAULT 0,
  recommended_next_action TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.0,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attending_biosketch_bridge_candidates (
  candidate_key TEXT PRIMARY KEY,
  event_group_key TEXT NOT NULL,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  source_url TEXT NOT NULL,
  source_title TEXT,
  source_scope TEXT NOT NULL,
  bridge_status TEXT NOT NULL,
  bridge_assurance_level INTEGER NOT NULL DEFAULT 0,
  training_line TEXT NOT NULL,
  training_type TEXT,
  organization_name TEXT,
  start_year INTEGER,
  end_year INTEGER,
  ten_year_trend_window TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.0,
  required_next_evidence TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attending_trend_reconciliation (
  trend_key TEXT PRIMARY KEY,
  event_group_key TEXT NOT NULL,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  trend_status TEXT NOT NULL,
  trend_assurance_level INTEGER NOT NULL DEFAULT 0,
  ten_year_trend_window TEXT NOT NULL,
  has_current_attending_endpoint INTEGER NOT NULL DEFAULT 0,
  has_penn_training_claim INTEGER NOT NULL DEFAULT 0,
  has_recent_dated_biosketch_bridge INTEGER NOT NULL DEFAULT 0,
  has_historical_link_candidate INTEGER NOT NULL DEFAULT 0,
  has_current_trainee_name_match INTEGER NOT NULL DEFAULT 0,
  bridge_candidate_keys TEXT,
  historical_candidate_keys TEXT,
  best_training_type TEXT,
  best_training_line TEXT,
  best_training_start_year INTEGER,
  best_training_end_year INTEGER,
  best_source_url TEXT,
  required_next_evidence TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attending_trend_review_claims (
  trend_claim_key TEXT PRIMARY KEY,
  trend_key TEXT NOT NULL REFERENCES attending_trend_reconciliation(trend_key) ON DELETE CASCADE,
  event_group_key TEXT NOT NULL,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  trend_claim_type TEXT NOT NULL,
  trend_status TEXT NOT NULL,
  trend_assurance_level INTEGER NOT NULL DEFAULT 0,
  ten_year_trend_window TEXT NOT NULL,
  training_type TEXT,
  training_line TEXT,
  training_organization TEXT,
  training_start_year INTEGER,
  training_end_year INTEGER,
  source_key TEXT,
  source_url TEXT,
  source_scope TEXT,
  bridge_candidate_key TEXT,
  has_current_attending_endpoint INTEGER NOT NULL DEFAULT 0,
  has_penn_training_claim INTEGER NOT NULL DEFAULT 0,
  has_recent_dated_biosketch_bridge INTEGER NOT NULL DEFAULT 0,
  acceptance_policy TEXT NOT NULL,
  display_safety_status TEXT NOT NULL,
  required_reviewer_action TEXT NOT NULL,
  evidence_json TEXT,
  materialized_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attending_trend_acceptance_audit (
  trend_acceptance_key TEXT PRIMARY KEY,
  trend_claim_key TEXT NOT NULL REFERENCES attending_trend_review_claims(trend_claim_key) ON DELETE CASCADE,
  trend_key TEXT NOT NULL REFERENCES attending_trend_reconciliation(trend_key) ON DELETE CASCADE,
  event_group_key TEXT NOT NULL,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  trend_claim_type TEXT NOT NULL,
  acceptance_status TEXT NOT NULL,
  accepted_trend_fact INTEGER NOT NULL DEFAULT 0,
  acceptance_level INTEGER NOT NULL DEFAULT 0,
  ten_year_trend_window TEXT NOT NULL,
  training_type TEXT,
  training_line TEXT,
  training_organization TEXT,
  training_start_year INTEGER,
  training_end_year INTEGER,
  source_key TEXT,
  source_url TEXT,
  source_scope TEXT,
  bridge_candidate_key TEXT,
  identity_check_status TEXT NOT NULL,
  endpoint_check_status TEXT NOT NULL,
  training_line_check_status TEXT NOT NULL,
  date_window_check_status TEXT NOT NULL,
  acceptance_blocker TEXT NOT NULL,
  display_safety_status TEXT NOT NULL,
  required_reviewer_action TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attending_trend_reviewer_decision_queue (
  reviewer_decision_key TEXT PRIMARY KEY,
  trend_acceptance_key TEXT NOT NULL REFERENCES attending_trend_acceptance_audit(trend_acceptance_key) ON DELETE CASCADE,
  trend_claim_key TEXT NOT NULL REFERENCES attending_trend_review_claims(trend_claim_key) ON DELETE CASCADE,
  trend_key TEXT NOT NULL,
  event_group_key TEXT NOT NULL,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  trend_claim_type TEXT NOT NULL,
  queue_status TEXT NOT NULL,
  allowed_decisions TEXT NOT NULL,
  claim_fingerprint TEXT NOT NULL,
  ten_year_trend_window TEXT NOT NULL,
  training_type TEXT,
  training_line TEXT,
  training_organization TEXT,
  training_start_year INTEGER,
  training_end_year INTEGER,
  source_key TEXT,
  source_url TEXT,
  source_scope TEXT,
  bridge_candidate_key TEXT,
  required_confirmation_fields TEXT NOT NULL,
  required_reviewer_action TEXT NOT NULL,
  display_safety_status TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attending_trend_reviewer_decisions (
  reviewer_decision_key TEXT PRIMARY KEY,
  trend_acceptance_key TEXT NOT NULL,
  trend_claim_key TEXT NOT NULL,
  claim_fingerprint TEXT NOT NULL,
  reviewer_decision TEXT NOT NULL,
  reviewer_name TEXT,
  decided_at TEXT,
  identity_confirmed INTEGER NOT NULL DEFAULT 0,
  endpoint_confirmed INTEGER NOT NULL DEFAULT 0,
  training_line_confirmed INTEGER NOT NULL DEFAULT 0,
  date_window_confirmed INTEGER NOT NULL DEFAULT 0,
  decision_notes TEXT
);

CREATE TABLE IF NOT EXISTS attending_trend_reviewer_decision_audit (
  reviewer_decision_key TEXT PRIMARY KEY,
  trend_acceptance_key TEXT NOT NULL REFERENCES attending_trend_acceptance_audit(trend_acceptance_key) ON DELETE CASCADE,
  trend_claim_key TEXT NOT NULL REFERENCES attending_trend_review_claims(trend_claim_key) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  reviewer_decision TEXT NOT NULL,
  decision_status TEXT NOT NULL,
  accepted_trend_fact INTEGER NOT NULL DEFAULT 0,
  decision_blocker TEXT NOT NULL,
  claim_fingerprint TEXT NOT NULL,
  decision_claim_fingerprint TEXT,
  identity_confirmed INTEGER NOT NULL DEFAULT 0,
  endpoint_confirmed INTEGER NOT NULL DEFAULT 0,
  training_line_confirmed INTEGER NOT NULL DEFAULT 0,
  date_window_confirmed INTEGER NOT NULL DEFAULT 0,
  reviewer_name TEXT,
  decided_at TEXT,
  training_type TEXT,
  training_line TEXT,
  training_organization TEXT,
  training_start_year INTEGER,
  training_end_year INTEGER,
  source_key TEXT,
  source_url TEXT,
  source_scope TEXT,
  bridge_candidate_key TEXT,
  recommended_next_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accepted_attending_trend_facts (
  trend_fact_key TEXT PRIMARY KEY,
  reviewer_decision_key TEXT NOT NULL REFERENCES attending_trend_reviewer_decision_audit(reviewer_decision_key) ON DELETE CASCADE,
  trend_acceptance_key TEXT NOT NULL REFERENCES attending_trend_acceptance_audit(trend_acceptance_key) ON DELETE CASCADE,
  trend_claim_key TEXT NOT NULL REFERENCES attending_trend_review_claims(trend_claim_key) ON DELETE CASCADE,
  trend_key TEXT NOT NULL,
  event_group_key TEXT NOT NULL,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  trend_fact_type TEXT NOT NULL,
  training_type TEXT,
  training_line TEXT,
  training_organization TEXT,
  training_start_year INTEGER,
  training_end_year INTEGER,
  ten_year_trend_window TEXT NOT NULL,
  source_key TEXT,
  source_url TEXT,
  source_scope TEXT,
  bridge_candidate_key TEXT,
  claim_fingerprint TEXT NOT NULL,
  accepted_by TEXT,
  accepted_at TEXT,
  display_safety_status TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  materialized_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS attending_trend_review_rollups (
  trend_rollup_key TEXT PRIMARY KEY,
  rollup_scope TEXT NOT NULL,
  rollup_value TEXT NOT NULL,
  training_type TEXT,
  training_end_year INTEGER,
  ten_year_trend_window TEXT,
  source_scope TEXT,
  claim_count INTEGER NOT NULL DEFAULT 0,
  person_count INTEGER NOT NULL DEFAULT 0,
  evidence_json TEXT,
  materialized_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS npi_candidate_claims (
  candidate_key TEXT PRIMARY KEY,
  person_key TEXT NOT NULL REFERENCES people(person_key) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  normalized_name TEXT NOT NULL,
  role TEXT,
  program_names TEXT,
  npi TEXT NOT NULL,
  provider_name TEXT NOT NULL,
  provider_credential TEXT,
  enumeration_type TEXT,
  primary_taxonomy TEXT,
  taxonomy_descriptions TEXT,
  practice_city TEXT,
  practice_state TEXT,
  practice_postal_code TEXT,
  result_rank INTEGER NOT NULL DEFAULT 0,
  total_results INTEGER NOT NULL DEFAULT 0,
  candidate_status TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.0,
  source_url TEXT NOT NULL,
  match_features_json TEXT,
  evidence_json TEXT,
  queried_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS npi_source_observations (
  query_key TEXT PRIMARY KEY,
  person_key TEXT REFERENCES people(person_key) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  state_filter TEXT,
  request_url TEXT NOT NULL,
  queried_at TEXT NOT NULL,
  http_status INTEGER NOT NULL DEFAULT 0,
  total_results INTEGER NOT NULL DEFAULT 0,
  candidate_rows INTEGER NOT NULL DEFAULT 0,
  error TEXT,
  sha256 TEXT
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

CREATE TABLE IF NOT EXISTS career_events (
  career_event_id INTEGER PRIMARY KEY,
  person_key TEXT REFERENCES people(person_key) ON DELETE SET NULL,
  display_name TEXT NOT NULL,
  event_type TEXT NOT NULL,
  role_title TEXT,
  organization_name TEXT,
  department TEXT,
  program_context TEXT,
  event_year INTEGER,
  source_key TEXT REFERENCES sources(source_key) ON DELETE SET NULL,
  source_url TEXT,
  confidence REAL NOT NULL DEFAULT 0.0,
  status TEXT NOT NULL DEFAULT 'candidate',
  match_features_json TEXT,
  evidence_json TEXT
);

CREATE TABLE IF NOT EXISTS person_contacts (
  contact_id INTEGER PRIMARY KEY,
  contact_key TEXT NOT NULL UNIQUE,
  person_key TEXT REFERENCES people(person_key) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  subject_type TEXT NOT NULL DEFAULT 'person',
  contact_type TEXT NOT NULL,
  contact_value TEXT NOT NULL,
  contact_label TEXT,
  contact_scope TEXT NOT NULL DEFAULT 'institutional',
  source_key TEXT REFERENCES sources(source_key) ON DELETE SET NULL,
  source_url TEXT,
  source_type TEXT,
  verification_status TEXT NOT NULL DEFAULT 'public_unverified',
  confidence REAL NOT NULL DEFAULT 0.0,
  status TEXT NOT NULL DEFAULT 'candidate',
  match_features_json TEXT,
  evidence_json TEXT,
  UNIQUE (person_key, display_name, subject_type, contact_type, contact_value, source_key)
);

CREATE TABLE IF NOT EXISTS contact_assurance_audit (
  contact_assurance_key TEXT PRIMARY KEY,
  contact_key TEXT NOT NULL REFERENCES person_contacts(contact_key) ON DELETE CASCADE,
  contact_id INTEGER,
  person_key TEXT REFERENCES people(person_key) ON DELETE SET NULL,
  display_name TEXT NOT NULL,
  role TEXT,
  subject_type TEXT,
  contact_type TEXT NOT NULL,
  contact_value TEXT NOT NULL,
  contact_domain TEXT,
  contact_label TEXT,
  contact_scope TEXT,
  source_key TEXT,
  source_url TEXT,
  source_type TEXT,
  source_assurance_class TEXT NOT NULL,
  verification_status TEXT NOT NULL,
  prior_status TEXT NOT NULL,
  assurance_status TEXT NOT NULL,
  assurance_level INTEGER NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0.0,
  display_safety_status TEXT NOT NULL,
  freshness_policy TEXT NOT NULL,
  required_next_check TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  audited_at TEXT NOT NULL
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
  match_features_json TEXT,
  reconciliation_notes TEXT,
  evidence_json TEXT
);

CREATE TABLE IF NOT EXISTS evidence_reconciliation_decisions (
  decision_key TEXT PRIMARY KEY,
  record_type TEXT NOT NULL,
  record_id TEXT NOT NULL,
  person_key TEXT REFERENCES people(person_key) ON DELETE SET NULL,
  display_name TEXT NOT NULL,
  role TEXT,
  claim_type TEXT,
  event_type TEXT,
  status TEXT,
  confidence REAL NOT NULL DEFAULT 0.0,
  priority INTEGER NOT NULL DEFAULT 0,
  decision TEXT NOT NULL,
  decision_rationale TEXT NOT NULL,
  required_next_evidence TEXT NOT NULL,
  non_name_anchor_count INTEGER NOT NULL DEFAULT 0,
  matched_current_person_count INTEGER NOT NULL DEFAULT 0,
  matched_current_person_keys TEXT,
  ten_year_trend_window TEXT,
  source_key TEXT,
  source_url TEXT,
  match_features TEXT,
  evidence_json TEXT,
  decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS person_reconciliation_decisions (
  rollup_key TEXT PRIMARY KEY,
  person_or_name_key TEXT NOT NULL,
  person_key TEXT REFERENCES people(person_key) ON DELETE SET NULL,
  display_name TEXT NOT NULL,
  record_count INTEGER NOT NULL DEFAULT 0,
  max_priority INTEGER NOT NULL DEFAULT 0,
  review_ready_records INTEGER NOT NULL DEFAULT 0,
  top_decision TEXT NOT NULL,
  decision_counts_json TEXT NOT NULL,
  decided_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enrichment_acceptance_audit (
  acceptance_key TEXT PRIMARY KEY,
  record_type TEXT NOT NULL,
  record_id TEXT NOT NULL,
  person_key TEXT REFERENCES people(person_key) ON DELETE SET NULL,
  display_name TEXT NOT NULL,
  role TEXT,
  claim_type TEXT NOT NULL,
  accepted_claim_type TEXT,
  accepted_claim_value TEXT,
  source_key TEXT,
  source_url TEXT,
  prior_decision TEXT NOT NULL,
  acceptance_status TEXT NOT NULL,
  assurance_level INTEGER NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0.0,
  non_name_anchor_count INTEGER NOT NULL DEFAULT 0,
  corroborating_source_count INTEGER NOT NULL DEFAULT 0,
  corroborating_sources_json TEXT NOT NULL,
  anchor_features_json TEXT NOT NULL,
  acceptance_blocker TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS accepted_enrichment_claims (
  accepted_enrichment_key TEXT PRIMARY KEY,
  acceptance_key TEXT NOT NULL,
  person_key TEXT REFERENCES people(person_key) ON DELETE SET NULL,
  display_name TEXT NOT NULL,
  role TEXT,
  enrichment_type TEXT NOT NULL,
  claim_type TEXT NOT NULL,
  claim_value TEXT NOT NULL,
  source_key TEXT,
  source_url TEXT,
  acceptance_status TEXT NOT NULL,
  assurance_level INTEGER NOT NULL DEFAULT 0,
  confidence REAL NOT NULL DEFAULT 0.0,
  non_name_anchor_count INTEGER NOT NULL DEFAULT 0,
  corroborating_source_count INTEGER NOT NULL DEFAULT 0,
  corroborating_sources_json TEXT NOT NULL,
  anchor_features_json TEXT NOT NULL,
  acceptance_policy TEXT NOT NULL,
  display_safety_status TEXT NOT NULL,
  required_final_check TEXT NOT NULL,
  evidence_json TEXT,
  accepted_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS person_enrichment_coverage (
  person_key TEXT PRIMARY KEY REFERENCES people(person_key) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  role TEXT,
  current_status TEXT,
  program_count INTEGER NOT NULL DEFAULT 0,
  programs TEXT,
  has_profile_url INTEGER NOT NULL DEFAULT 0,
  has_headshot_url INTEGER NOT NULL DEFAULT 0,
  contact_count INTEGER NOT NULL DEFAULT 0,
  medical_school_count INTEGER NOT NULL DEFAULT 0,
  residency_program_count INTEGER NOT NULL DEFAULT 0,
  undergraduate_school_count INTEGER NOT NULL DEFAULT 0,
  graduate_school_count INTEGER NOT NULL DEFAULT 0,
  seeded_training_org_count INTEGER NOT NULL DEFAULT 0,
  cleaned_training_org_count INTEGER NOT NULL DEFAULT 0,
  pubmed_author_query_count INTEGER NOT NULL DEFAULT 0,
  pubmed_article_candidate_count INTEGER NOT NULL DEFAULT 0,
  pubmed_article_needs_review_count INTEGER NOT NULL DEFAULT 0,
  career_event_candidate_count INTEGER NOT NULL DEFAULT 0,
  npi_candidate_count INTEGER NOT NULL DEFAULT 0,
  npi_needs_review_count INTEGER NOT NULL DEFAULT 0,
  npi_candidate_status_count INTEGER NOT NULL DEFAULT 0,
  npi_low_signal_count INTEGER NOT NULL DEFAULT 0,
  reconciliation_queue_count INTEGER NOT NULL DEFAULT 0,
  max_reconciliation_priority INTEGER NOT NULL DEFAULT 0,
  worst_state_machine_status TEXT,
  coverage_score INTEGER NOT NULL DEFAULT 0,
  coverage_band TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS program_enrichment_coverage (
  program_name TEXT NOT NULL,
  role TEXT,
  person_count INTEGER NOT NULL DEFAULT 0,
  avg_coverage_score REAL NOT NULL DEFAULT 0.0,
  broad_enrichment_surface_count INTEGER NOT NULL DEFAULT 0,
  moderate_enrichment_surface_count INTEGER NOT NULL DEFAULT 0,
  thin_enrichment_surface_count INTEGER NOT NULL DEFAULT 0,
  profile_coverage_rate REAL NOT NULL DEFAULT 0.0,
  contact_coverage_rate REAL NOT NULL DEFAULT 0.0,
  medical_school_coverage_rate REAL NOT NULL DEFAULT 0.0,
  residency_coverage_rate REAL NOT NULL DEFAULT 0.0,
  article_candidate_coverage_rate REAL NOT NULL DEFAULT 0.0,
  npi_candidate_coverage_rate REAL NOT NULL DEFAULT 0.0,
  npi_needs_review_coverage_rate REAL NOT NULL DEFAULT 0.0,
  cleaned_org_review_count INTEGER NOT NULL DEFAULT 0,
  reconciliation_queue_count INTEGER NOT NULL DEFAULT 0,
  top_recommended_next_action TEXT NOT NULL,
  PRIMARY KEY (program_name, role)
);

CREATE TABLE IF NOT EXISTS person_enrichment_work_queue (
  task_key TEXT PRIMARY KEY,
  person_key TEXT NOT NULL REFERENCES people(person_key) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  role TEXT,
  current_status TEXT,
  program_name TEXT,
  trainee_category TEXT,
  coverage_score INTEGER NOT NULL DEFAULT 0,
  coverage_band TEXT,
  recommended_next_action TEXT,
  state_machine_status TEXT,
  policy_lane TEXT,
  diff_readiness_status TEXT,
  stale_by_refresh INTEGER NOT NULL DEFAULT 0,
  fresh_observation_required INTEGER NOT NULL DEFAULT 0,
  task_type TEXT NOT NULL,
  source_family TEXT NOT NULL,
  source_strategy TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  priority_band TEXT NOT NULL,
  query TEXT NOT NULL,
  source_targets_json TEXT NOT NULL,
  expected_claim_types_json TEXT NOT NULL,
  evidence_requirement TEXT NOT NULL,
  acceptance_rule TEXT NOT NULL,
  recency_policy TEXT NOT NULL,
  provenance_policy TEXT NOT NULL,
  blocking_risk TEXT NOT NULL,
  operator_action TEXT NOT NULL,
  evidence_json TEXT,
  generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS person_enrichment_execution_readiness (
  readiness_key TEXT PRIMARY KEY,
  task_key TEXT NOT NULL REFERENCES person_enrichment_work_queue(task_key) ON DELETE CASCADE,
  person_key TEXT NOT NULL REFERENCES people(person_key) ON DELETE CASCADE,
  display_name TEXT NOT NULL,
  role TEXT,
  program_name TEXT,
  task_type TEXT NOT NULL,
  source_family TEXT NOT NULL,
  priority INTEGER NOT NULL DEFAULT 0,
  priority_band TEXT NOT NULL,
  execution_lane TEXT NOT NULL,
  automation_status TEXT NOT NULL,
  existing_collector TEXT NOT NULL,
  command_hint TEXT NOT NULL,
  input_artifacts_json TEXT NOT NULL,
  output_artifacts_json TEXT NOT NULL,
  requires_network INTEGER NOT NULL DEFAULT 0,
  requires_manual_review INTEGER NOT NULL DEFAULT 0,
  requires_script_extension INTEGER NOT NULL DEFAULT 0,
  requires_new_parser INTEGER NOT NULL DEFAULT 0,
  batch_key TEXT NOT NULL,
  batch_rank INTEGER NOT NULL DEFAULT 0,
  readiness_reason TEXT NOT NULL,
  next_system_action TEXT NOT NULL,
  evidence_json TEXT,
  generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS person_enrichment_execution_readiness_rollups (
  rollup_key TEXT PRIMARY KEY,
  rollup_scope TEXT NOT NULL,
  rollup_value TEXT NOT NULL,
  task_type TEXT,
  source_family TEXT,
  priority_band TEXT,
  execution_lane TEXT,
  automation_status TEXT,
  task_count INTEGER NOT NULL DEFAULT 0,
  person_count INTEGER NOT NULL DEFAULT 0,
  critical_task_count INTEGER NOT NULL DEFAULT 0,
  network_required_count INTEGER NOT NULL DEFAULT 0,
  manual_review_required_count INTEGER NOT NULL DEFAULT 0,
  script_extension_required_count INTEGER NOT NULL DEFAULT 0,
  new_parser_required_count INTEGER NOT NULL DEFAULT 0,
  top_command_hint TEXT NOT NULL,
  next_system_action TEXT NOT NULL,
  evidence_json TEXT,
  generated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_quality_observations (
  observation_id INTEGER PRIMARY KEY,
  utility_key TEXT REFERENCES source_utilities(utility_key) ON DELETE SET NULL,
  observed_at TEXT NOT NULL,
  sample_size INTEGER NOT NULL DEFAULT 0,
  candidate_claims INTEGER NOT NULL DEFAULT 0,
  accepted_claims INTEGER NOT NULL DEFAULT 0,
  rejected_claims INTEGER NOT NULL DEFAULT 0,
  ambiguous_claims INTEGER NOT NULL DEFAULT 0,
  notes TEXT,
  metrics_json TEXT
);

CREATE TABLE IF NOT EXISTS source_utility_scorecard (
  scorecard_key TEXT PRIMARY KEY,
  utility_key TEXT REFERENCES source_utilities(utility_key) ON DELETE SET NULL,
  utility_label TEXT NOT NULL,
  source_family TEXT NOT NULL,
  claim_surface TEXT NOT NULL,
  input_records INTEGER NOT NULL DEFAULT 0,
  output_records INTEGER NOT NULL DEFAULT 0,
  accepted_records INTEGER NOT NULL DEFAULT 0,
  candidate_records INTEGER NOT NULL DEFAULT 0,
  needs_review_records INTEGER NOT NULL DEFAULT 0,
  review_ready_records INTEGER NOT NULL DEFAULT 0,
  discovery_only_records INTEGER NOT NULL DEFAULT 0,
  low_signal_records INTEGER NOT NULL DEFAULT 0,
  coverage_gap_records INTEGER NOT NULL DEFAULT 0,
  blocked_records INTEGER NOT NULL DEFAULT 0,
  score REAL NOT NULL DEFAULT 0.0,
  quality_band TEXT NOT NULL,
  strengths TEXT NOT NULL,
  limitations TEXT NOT NULL,
  recommended_next_action TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse_reproducibility_audit (
  audit_key TEXT PRIMARY KEY,
  artifact_path TEXT NOT NULL,
  artifact_role TEXT NOT NULL,
  artifact_format TEXT NOT NULL,
  required INTEGER NOT NULL DEFAULT 1,
  exists_on_disk INTEGER NOT NULL DEFAULT 0,
  byte_size INTEGER NOT NULL DEFAULT 0,
  sha256 TEXT,
  sqlite_table TEXT,
  artifact_rows INTEGER,
  sqlite_rows INTEGER,
  row_count_status TEXT NOT NULL,
  freshness_status TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  evidence_json TEXT,
  audited_at TEXT NOT NULL
);

DROP VIEW IF EXISTS v_public_person_contacts;
DROP VIEW IF EXISTS v_evidence_reconciliation_queue;
DROP VIEW IF EXISTS v_review_ready_attending_trends;
DROP VIEW IF EXISTS v_recent_attending_trend_candidates;
DROP VIEW IF EXISTS v_official_program_source_queue;
DROP VIEW IF EXISTS v_official_program_coverage_gaps;
DROP VIEW IF EXISTS v_current_training_states;
DROP VIEW IF EXISTS v_organization_review_queue;
DROP VIEW IF EXISTS v_person_training;

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

CREATE VIEW IF NOT EXISTS v_current_training_states AS
SELECT
  s.state_id,
  s.state_key,
  s.person_key,
  p.display_name,
  p.role,
  pr.program_name,
  s.observed_at,
  s.as_of_date,
  s.raw_stage_label,
  s.normalized_stage,
  s.stage_family,
  s.stage_index,
  s.stage_rank,
  s.trainee_category,
  s.lifecycle_rule_key,
  s.lifecycle_code,
  s.lifecycle_stage,
  s.academic_year,
  s.estimated_start_date,
  s.estimated_end_date,
  s.expected_next_stage,
  s.expected_next_date,
  s.expected_exit_date,
  s.expected_transition_type,
  s.stale_after_date,
  s.refresh_policy,
  s.transition_rule,
  s.status,
  s.confidence,
  s.source_key
FROM person_training_states s
JOIN people p ON p.person_key = s.person_key
LEFT JOIN programs pr ON pr.program_key = s.program_key
ORDER BY p.display_name, pr.program_name, s.stage_rank, s.raw_stage_label;

CREATE VIEW IF NOT EXISTS v_official_program_coverage_gaps AS
SELECT
  u.sponsoring_institution,
  u.department,
  u.program_type,
  u.program_name,
  u.program_url,
  a.coverage_status,
  a.match_method,
  a.discovery_url,
  a.captured_people_count,
  a.match_confidence,
  a.notes
FROM official_program_universe u
JOIN official_program_coverage_audit a ON a.official_program_key = u.official_program_key
WHERE a.coverage_status != 'covered_current_roster'
ORDER BY
  CASE a.coverage_status
    WHEN 'discovered_no_current_roster' THEN 0
    WHEN 'not_discovered' THEN 1
    ELSE 2
  END,
  u.department,
  u.program_type,
  u.program_name;

CREATE VIEW IF NOT EXISTS v_official_program_source_queue AS
SELECT
  c.candidate_key,
  c.official_program_key,
  c.department,
  c.program_type,
  c.program_name,
  c.coverage_status,
  c.source_role,
  c.candidate_status,
  c.priority,
  c.confidence,
  c.candidate_title,
  c.candidate_url,
  c.http_status,
  c.roster_term_count,
  c.context_term_count,
  c.reasons_json
FROM official_program_source_candidates c
WHERE c.candidate_status IN ('roster_source_candidate', 'program_context_candidate')
ORDER BY c.priority DESC, c.department, c.program_name, c.candidate_url;

CREATE VIEW IF NOT EXISTS v_recent_attending_trend_candidates AS
SELECT
  career_event_id,
  person_key,
  display_name,
  event_type,
  role_title,
  organization_name,
  department,
  program_context,
  event_year,
  source_url,
  confidence,
  status
FROM career_events
WHERE event_type IN (
  'current_penn_attending_candidate',
  'penn_alumni_outcome_candidate',
  'attending_profile_training_history_candidate'
)
ORDER BY
  event_year DESC,
  confidence DESC,
  display_name;

CREATE VIEW IF NOT EXISTS v_review_ready_attending_trends AS
SELECT
  trend_key,
  event_group_key,
  display_name,
  normalized_name,
  trend_status,
  trend_assurance_level,
  ten_year_trend_window,
  best_training_type,
  best_training_line,
  best_training_start_year,
  best_training_end_year,
  best_source_url,
  required_next_evidence
FROM attending_trend_reconciliation
WHERE trend_status = 'review_ready_official_biosketch_bridge'
ORDER BY best_training_end_year DESC, display_name;

CREATE VIEW IF NOT EXISTS v_evidence_reconciliation_queue AS
SELECT
  'evidence_claim' AS record_type,
  e.evidence_id AS record_id,
  e.person_key,
  p.display_name,
  p.role,
  e.claim_type,
  e.claim_value,
  '' AS event_type,
  '' AS organization_name,
  NULL AS event_year,
  e.source_key,
  e.source_url,
  e.source_type,
  e.status,
  e.confidence,
  e.match_features_json,
  e.reconciliation_notes,
  CASE
    WHEN e.status = 'needs_review' THEN 50 ELSE 10
  END
  + CASE
      WHEN e.claim_type = 'pubmed_article_candidate' THEN 30
      WHEN e.claim_type = 'research_author_candidate' THEN 20
      WHEN e.claim_type = 'pubmed_author_query_candidate' THEN 2
      ELSE 5
    END
  + CASE WHEN e.match_features_json LIKE '%penn_affiliation%' THEN 15 ELSE 0 END
  + CASE WHEN e.match_features_json LIKE '%prior_training_or_education_affiliation%' THEN 12 ELSE 0 END
  + CASE WHEN e.match_features_json LIKE '%program_topic_match%' THEN 8 ELSE 0 END
  + CASE WHEN e.match_features_json LIKE '%orcid_present%' THEN 15 ELSE 0 END
  + CASE WHEN e.match_features_json LIKE '%bounded_author_query%' THEN 5 ELSE 0 END
  + CAST(e.confidence * 10 AS INTEGER) AS priority,
  CASE
    WHEN e.claim_type = 'pubmed_article_candidate' THEN 'Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment.'
    WHEN e.claim_type = 'pubmed_author_query_candidate' THEN 'Use only as discovery input; fetch/review article-level evidence before accepting.'
    WHEN e.claim_type = 'research_author_candidate' THEN 'Review OpenAlex/ORCID/affiliation anchors before accepting author identity.'
    ELSE 'Review candidate evidence against person identity before accepting.'
  END AS review_action
FROM evidence_claims e
LEFT JOIN people p ON p.person_key = e.person_key
WHERE e.status IN ('candidate', 'needs_review')
  AND e.claim_type IN (
    'pubmed_article_candidate',
    'pubmed_author_query_candidate',
    'research_author_candidate',
    'research_author_candidate_error'
  )
UNION ALL
SELECT
  'career_event' AS record_type,
  c.career_event_id AS record_id,
  c.person_key,
  c.display_name,
  COALESCE(p.role, 'attending_or_outcome_candidate') AS role,
  CASE WHEN c.role_title IS NOT NULL AND c.role_title != '' THEN c.role_title ELSE c.event_type END AS claim_type,
  CASE WHEN c.role_title IS NOT NULL AND c.role_title != '' THEN c.role_title ELSE c.event_type END
    || CASE WHEN c.organization_name IS NOT NULL AND c.organization_name != '' THEN ': ' || c.organization_name ELSE '' END AS claim_value,
  c.event_type,
  c.organization_name,
  c.event_year,
  c.source_key,
  c.source_url,
  'career_event' AS source_type,
  c.status,
  c.confidence,
  c.match_features_json,
  'Career-event candidate; link to prior Penn trainee identity only after source/profile evidence agrees.' AS reconciliation_notes,
  CASE
    WHEN c.status = 'needs_review' THEN 50 ELSE 10
  END
  + CASE
      WHEN c.event_type = 'attending_profile_training_history_candidate'
           AND c.role_title = 'penn_training_history_candidate' THEN 40
      WHEN c.event_type = 'attending_profile_training_history_candidate' THEN 25
      WHEN c.event_type = 'current_penn_attending_candidate' THEN 20
      WHEN c.event_type = 'penn_alumni_outcome_candidate' THEN 10
      ELSE 5
    END
  + CASE WHEN c.match_features_json LIKE '%penn_training_language%' THEN 15 ELSE 0 END
  + CASE WHEN c.match_features_json LIKE '%structured_provider_training_field%' THEN 10 ELSE 0 END
  + CAST(c.confidence * 10 AS INTEGER) AS priority,
  CASE
    WHEN c.event_type = 'attending_profile_training_history_candidate' THEN 'Review official profile training-history claim and reconcile to a Penn trainee identity or independent public anchor.'
    WHEN c.event_type = 'current_penn_attending_candidate' THEN 'Use as current Penn endpoint candidate; seek profile/training/history anchors.'
    WHEN c.event_type = 'penn_alumni_outcome_candidate' THEN 'Source-level outcome context only; resolve named person before linking.'
    ELSE 'Review career-event evidence before linking.'
  END AS review_action
FROM career_events c
LEFT JOIN people p ON p.person_key = c.person_key
WHERE c.status IN ('candidate', 'needs_review')
UNION ALL
SELECT
  'npi_candidate' AS record_type,
  n.candidate_key AS record_id,
  n.person_key,
  n.display_name,
  p.role,
  'npi_candidate' AS claim_type,
  n.npi || ': ' || n.provider_name
    || CASE WHEN n.primary_taxonomy IS NOT NULL AND n.primary_taxonomy != '' THEN ' / ' || n.primary_taxonomy ELSE '' END
    || CASE WHEN n.practice_state IS NOT NULL AND n.practice_state != '' THEN ' / ' || n.practice_state ELSE '' END AS claim_value,
  '' AS event_type,
  '' AS organization_name,
  NULL AS event_year,
  'nppes_npi_registry' AS source_key,
  n.source_url,
  'licensure_api' AS source_type,
  n.candidate_status AS status,
  n.confidence,
  n.match_features_json,
  'NPPES/NPI candidate; use as secondary identity anchor only after name, location, taxonomy, and source context agree.' AS reconciliation_notes,
  CASE
    WHEN n.candidate_status = 'needs_review' THEN 70
    WHEN n.candidate_status = 'candidate' THEN 45
    ELSE 15
  END
  + CASE WHEN n.match_features_json LIKE '%exact_first_last_name%' THEN 10 ELSE 0 END
  + CASE WHEN n.match_features_json LIKE '%state_location_match%' THEN 8 ELSE 0 END
  + CASE WHEN n.match_features_json LIKE '%philadelphia_location%' THEN 5 ELSE 0 END
  + CASE WHEN n.match_features_json LIKE '%physician_specialty_taxonomy%' THEN 5 ELSE 0 END
  + CASE WHEN n.match_features_json LIKE '%student_or_training_taxonomy%' THEN 5 ELSE 0 END
  + CASE WHEN n.match_features_json LIKE '%program_taxonomy_topic_match%' THEN 6 ELSE 0 END
  + CAST(n.confidence * 10 AS INTEGER) AS priority,
  CASE
    WHEN n.candidate_status = 'needs_review' THEN 'Review NPI name, taxonomy, PA/location, and official profile or roster context before using as an identity anchor.'
    WHEN n.candidate_status = 'candidate' THEN 'Keep as NPI candidate; seek stronger location, taxonomy, profile, or publication corroboration.'
    ELSE 'Low-signal NPI candidate; do not use without stronger non-name anchors.'
  END AS review_action
FROM npi_candidate_claims n
JOIN people p ON p.person_key = n.person_key
WHERE n.candidate_status IN ('needs_review', 'candidate', 'low_signal_npi_candidate')
ORDER BY priority DESC, confidence DESC, display_name, record_type, record_id;

CREATE VIEW IF NOT EXISTS v_public_person_contacts AS
SELECT
  c.contact_id,
  c.person_key,
  COALESCE(p.display_name, c.display_name) AS display_name,
  COALESCE(p.role, c.subject_type) AS role,
  c.contact_type,
  c.contact_value,
  c.contact_label,
  c.contact_scope,
  c.source_key,
  c.source_url,
  c.verification_status,
  c.confidence,
  c.status
FROM person_contacts c
LEFT JOIN people p ON p.person_key = c.person_key
WHERE c.status IN ('accepted', 'candidate', 'needs_review')
ORDER BY COALESCE(p.display_name, c.display_name), c.contact_type, c.confidence DESC;
