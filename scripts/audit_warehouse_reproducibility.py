#!/usr/bin/env python3
"""Audit whether the SQLite warehouse agrees with generated flat-file artifacts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "warehouse_reproducibility_audit.csv"
JSON_PATH = ARTIFACTS / "warehouse_reproducibility_audit.json"
SUMMARY_PATH = ARTIFACTS / "warehouse_reproducibility_summary.json"
SQLITE_MANIFEST_PATH = ARTIFACTS / "redmank_sqlite_manifest.json"

GITHUB_RECOMMENDED_FILE_LIMIT_BYTES = 50 * 1024 * 1024

csv.field_size_limit(sys.maxsize)

ARTIFACT_SPECS = [
    ("artifacts/data/redmank.sqlite", "sqlite_warehouse_binary", "sqlite", None, True),
    ("artifacts/data/people_resolved.csv", "warehouse_export", "csv", "people", True),
    ("artifacts/data/training_events_resolved.csv", "warehouse_export", "csv", "person_training_events", True),
    ("artifacts/data/training_states_current.csv", "warehouse_export", "csv", "person_training_states", True),
    (
        "artifacts/data/penn_gme_program_coverage.csv",
        "official_program_denominator_ledger",
        "csv",
        "official_program_coverage_audit",
        True,
    ),
    (
        "artifacts/data/penn_gme_gap_source_probes.json",
        "official_program_gap_probe_ledger",
        "json_array",
        "official_program_source_probes",
        True,
    ),
    (
        "artifacts/data/penn_gme_gap_source_candidates.csv",
        "official_program_gap_source_ledger",
        "csv",
        "official_program_source_candidates",
        True,
    ),
    (
        "artifacts/data/penn_gme_gap_source_search_queries.csv",
        "official_program_gap_source_search_ledger",
        "csv",
        "official_program_source_search_queries",
        True,
    ),
    (
        "artifacts/data/penn_gme_gap_source_search_observations.csv",
        "official_program_gap_source_search_ledger",
        "csv",
        "official_program_source_search_observations",
        True,
    ),
    (
        "artifacts/data/hup_gap_reason_audit.csv",
        "official_program_gap_reason_ledger",
        "csv",
        "official_program_gap_reason_audit",
        True,
    ),
    (
        "artifacts/data/official_gap_roster_reconciliation.csv",
        "official_program_gap_roster_reconciliation_ledger",
        "csv",
        "official_gap_roster_reconciliation",
        True,
    ),
    (
        "artifacts/data/official_gap_roster_program_resolution.csv",
        "official_program_gap_roster_resolution_ledger",
        "csv",
        "official_gap_roster_program_resolution",
        True,
    ),
    (
        "artifacts/data/official_program_coverage_assurance_audit.csv",
        "official_program_coverage_assurance_ledger",
        "csv",
        "official_program_coverage_assurance_audit",
        True,
    ),
    (
        "artifacts/data/official_program_coverage_action_queue.csv",
        "official_program_coverage_action_queue",
        "csv",
        "official_program_coverage_action_queue",
        True,
    ),
    (
        "artifacts/data/official_program_coverage_dossiers.csv",
        "official_program_coverage_dossier_ledger",
        "csv",
        "official_program_coverage_dossiers",
        True,
    ),
    (
        "artifacts/data/official_program_coverage_batches.csv",
        "official_program_coverage_batch_ledger",
        "csv",
        "official_program_coverage_batches",
        True,
    ),
    (
        "artifacts/data/official_program_coverage_batch_packets.csv",
        "official_program_coverage_batch_packet_ledger",
        "csv",
        "official_program_coverage_batch_packets",
        True,
    ),
    (
        "artifacts/data/official_program_alias_review_packets.csv",
        "official_program_alias_review_packets",
        "csv",
        "official_program_alias_review_packets",
        True,
    ),
    (
        "artifacts/data/official_program_alias_reviewer_decisions.csv",
        "official_program_alias_reviewer_decision_input",
        "csv",
        "official_program_alias_reviewer_decisions",
        True,
    ),
    (
        "artifacts/data/official_program_alias_reviewer_decision_queue.csv",
        "official_program_alias_reviewer_decision_ledger",
        "csv",
        "official_program_alias_reviewer_decision_queue",
        True,
    ),
    (
        "artifacts/data/official_program_alias_reviewer_decision_audit.csv",
        "official_program_alias_reviewer_decision_ledger",
        "csv",
        "official_program_alias_reviewer_decision_audit",
        True,
    ),
    (
        "artifacts/data/accepted_official_program_alias_mappings.csv",
        "official_program_alias_accepted_mapping_ledger",
        "csv",
        "accepted_official_program_alias_mappings",
        True,
    ),
    (
        "artifacts/data/official_program_denominator_closure_audit.csv",
        "official_program_denominator_closure_ledger",
        "csv",
        "official_program_denominator_closure_audit",
        True,
    ),
    (
        "artifacts/data/official_program_alias_reconciliation_candidates.csv",
        "official_program_alias_ledger",
        "csv",
        "official_program_alias_reconciliation_candidates",
        True,
    ),
    ("artifacts/data/training_state_machine_audit.csv", "state_machine_ledger", "csv", "training_state_machine_audit", True),
    (
        "artifacts/data/person_training_state_machine_audit.csv",
        "state_machine_ledger",
        "csv",
        "person_training_state_machine_audit",
        True,
    ),
    (
        "artifacts/data/program_training_state_machine_audit.csv",
        "state_machine_ledger",
        "csv",
        "program_training_state_machine_audit",
        True,
    ),
    (
        "artifacts/data/training_state_refresh_expectations.csv",
        "longitudinal_readiness_ledger",
        "csv",
        "training_state_refresh_expectations",
        True,
    ),
    (
        "artifacts/data/person_refresh_expectations.csv",
        "longitudinal_readiness_ledger",
        "csv",
        "person_refresh_expectations",
        True,
    ),
    (
        "artifacts/data/program_refresh_expectations.csv",
        "longitudinal_readiness_ledger",
        "csv",
        "program_refresh_expectations",
        True,
    ),
    (
        "artifacts/data/category_refresh_expectations.csv",
        "longitudinal_readiness_ledger",
        "csv",
        "category_refresh_expectations",
        True,
    ),
    (
        "artifacts/data/training_lifecycle_assurance_rollups.csv",
        "longitudinal_lifecycle_assurance_ledger",
        "csv",
        "training_lifecycle_assurance_rollups",
        True,
    ),
    (
        "artifacts/data/training_state_transition_plan.csv",
        "longitudinal_transition_plan_ledger",
        "csv",
        "training_state_transition_plan",
        True,
    ),
    (
        "artifacts/data/training_state_transition_plan_rollups.csv",
        "longitudinal_transition_plan_ledger",
        "csv",
        "training_state_transition_plan_rollups",
        True,
    ),
    (
        "artifacts/data/training_temporal_contracts.csv",
        "longitudinal_temporal_contract_ledger",
        "csv",
        "training_temporal_contracts",
        True,
    ),
    (
        "artifacts/data/training_temporal_contract_rollups.csv",
        "longitudinal_temporal_contract_ledger",
        "csv",
        "training_temporal_contract_rollups",
        True,
    ),
    (
        "artifacts/data/training_temporal_contract_batches.csv",
        "longitudinal_temporal_contract_batch_ledger",
        "csv",
        "training_temporal_contract_batches",
        True,
    ),
    (
        "artifacts/data/training_temporal_contract_batch_packets.csv",
        "longitudinal_temporal_contract_batch_packet_ledger",
        "csv",
        "training_temporal_contract_batch_packets",
        True,
    ),
    (
        "artifacts/data/person_training_stage_state.csv",
        "longitudinal_stage_state_ledger",
        "csv",
        "person_training_stage_state",
        True,
    ),
    (
        "artifacts/data/training_stage_state_rollups.csv",
        "longitudinal_stage_state_ledger",
        "csv",
        "training_stage_state_rollups",
        True,
    ),
    (
        "artifacts/data/official_roster_refresh_workbench.csv",
        "official_roster_refresh_workbench_ledger",
        "csv",
        "official_roster_refresh_workbench",
        True,
    ),
    (
        "artifacts/data/official_roster_refresh_batches.csv",
        "official_roster_refresh_batch_ledger",
        "csv",
        "official_roster_refresh_batches",
        True,
    ),
    (
        "artifacts/data/official_roster_refresh_batch_packets.csv",
        "official_roster_refresh_batch_packet_ledger",
        "csv",
        "official_roster_refresh_batch_packets",
        True,
    ),
    (
        "artifacts/data/official_roster_refresh_execution_audit.csv",
        "official_roster_refresh_execution_ledger",
        "csv",
        "official_roster_refresh_execution_audit",
        True,
    ),
    (
        "artifacts/data/training_state_diff.csv",
        "longitudinal_contract_aware_diff_example",
        "csv",
        None,
        True,
    ),
    (
        "artifacts/data/training_state_diff_rollups.csv",
        "longitudinal_contract_aware_diff_example",
        "csv",
        None,
        True,
    ),
    (
        "artifacts/data/training_state_diff_summary.json",
        "longitudinal_contract_aware_diff_example",
        "json_object",
        None,
        True,
    ),
    (
        "artifacts/data/trainee_profile_search_queries.csv",
        "trainee_profile_discovery_ledger",
        "csv",
        "trainee_profile_search_queries",
        True,
    ),
    (
        "artifacts/data/trainee_profile_search_observations.csv",
        "trainee_profile_discovery_ledger",
        "csv",
        "trainee_profile_search_observations",
        True,
    ),
    (
        "artifacts/data/trainee_profile_discovery_candidates.csv",
        "trainee_profile_discovery_ledger",
        "csv",
        "trainee_profile_discovery_candidates",
        True,
    ),
    (
        "artifacts/data/official_profile_discovery_workbench.csv",
        "official_profile_discovery_workbench_ledger",
        "csv",
        "official_profile_discovery_workbench",
        True,
    ),
    (
        "artifacts/data/official_profile_discovery_batches.csv",
        "official_profile_discovery_batch_ledger",
        "csv",
        "official_profile_discovery_batches",
        True,
    ),
    (
        "artifacts/data/official_profile_discovery_batch_packets.csv",
        "official_profile_discovery_batch_packet_ledger",
        "csv",
        "official_profile_discovery_batch_packets",
        True,
    ),
    (
        "artifacts/data/official_profile_reobservation_audit.csv",
        "official_profile_reobservation_ledger",
        "csv",
        "official_profile_reobservation_audit",
        True,
    ),
    (
        "artifacts/data/official_profile_reviewer_decisions.csv",
        "official_profile_reviewer_decision_input",
        "csv",
        "official_profile_reviewer_decisions",
        True,
    ),
    (
        "artifacts/data/official_profile_reviewer_decision_queue.csv",
        "official_profile_reviewer_decision_ledger",
        "csv",
        "official_profile_reviewer_decision_queue",
        True,
    ),
    (
        "artifacts/data/official_profile_reviewer_decision_audit.csv",
        "official_profile_reviewer_decision_ledger",
        "csv",
        "official_profile_reviewer_decision_audit",
        True,
    ),
    (
        "artifacts/data/official_profile_reviewer_decision_dossiers.csv",
        "official_profile_reviewer_decision_dossier_ledger",
        "csv",
        "official_profile_reviewer_decision_dossiers",
        True,
    ),
    (
        "artifacts/data/accepted_official_profile_url_facts.csv",
        "accepted_official_profile_url_ledger",
        "csv",
        "accepted_official_profile_url_facts",
        True,
    ),
    (
        "artifacts/data/evidence_temporal_contracts.csv",
        "evidence_temporal_contract_ledger",
        "csv",
        "evidence_temporal_contracts",
        True,
    ),
    (
        "artifacts/data/evidence_temporal_contract_rollups.csv",
        "evidence_temporal_contract_ledger",
        "csv",
        "evidence_temporal_contract_rollups",
        True,
    ),
    (
        "artifacts/data/prior_training_search_queries.csv",
        "prior_training_discovery_ledger",
        "csv",
        "prior_training_search_queries",
        True,
    ),
    (
        "artifacts/data/prior_training_search_observations.csv",
        "prior_training_discovery_ledger",
        "csv",
        "prior_training_search_observations",
        True,
    ),
    (
        "artifacts/data/prior_training_discovery_candidates.csv",
        "prior_training_discovery_ledger",
        "csv",
        "prior_training_discovery_candidates",
        True,
    ),
    (
        "artifacts/data/training_state_snapshots/*.json",
        "longitudinal_snapshot_ledger",
        "json_object_glob",
        "training_state_snapshots",
        True,
    ),
    (
        "artifacts/data/training_state_snapshots/*.csv",
        "longitudinal_snapshot_ledger",
        "csv_glob",
        "training_state_snapshot_rows",
        True,
    ),
    (
        "artifacts/data/training_state_transition_events.csv",
        "longitudinal_snapshot_ledger",
        "csv",
        "training_state_transition_events",
        True,
    ),
    (
        "artifacts/data/training_state_transition_rollups.csv",
        "longitudinal_snapshot_ledger",
        "csv",
        "training_state_transition_rollups",
        True,
    ),
    (
        "artifacts/data/person_enrichment_coverage.csv",
        "person_enrichment_coverage_ledger",
        "csv",
        "person_enrichment_coverage",
        True,
    ),
    (
        "artifacts/data/program_enrichment_coverage.csv",
        "person_enrichment_coverage_ledger",
        "csv",
        "program_enrichment_coverage",
        True,
    ),
    (
        "artifacts/data/person_enrichment_dossiers.csv",
        "person_enrichment_dossier_ledger",
        "csv",
        "person_enrichment_dossiers",
        True,
    ),
    (
        "artifacts/data/person_enrichment_queue.csv",
        "person_enrichment_work_queue",
        "csv",
        "person_enrichment_work_queue",
        True,
    ),
    (
        "artifacts/data/person_enrichment_execution_readiness.csv",
        "person_enrichment_execution_readiness_ledger",
        "csv",
        "person_enrichment_execution_readiness",
        True,
    ),
    (
        "artifacts/data/person_enrichment_execution_readiness_rollups.csv",
        "person_enrichment_execution_readiness_ledger",
        "csv",
        "person_enrichment_execution_readiness_rollups",
        True,
    ),
    (
        "artifacts/data/person_enrichment_execution_batches.csv",
        "person_enrichment_execution_batch_ledger",
        "csv",
        "person_enrichment_execution_batches",
        True,
    ),
    (
        "artifacts/data/person_enrichment_execution_batch_packets.csv",
        "person_enrichment_execution_batch_packet_ledger",
        "csv",
        "person_enrichment_execution_batch_packets",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_packets.csv",
        "person_enrichment_action_packet_ledger",
        "csv",
        "person_enrichment_action_packets",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_batches.csv",
        "person_enrichment_action_batch_ledger",
        "csv",
        "person_enrichment_action_batches",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_batch_members.csv",
        "person_enrichment_action_batch_member_ledger",
        "csv",
        "person_enrichment_action_batch_members",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_member_execution_decisions.csv",
        "person_enrichment_action_member_execution_input",
        "csv",
        "person_enrichment_action_member_execution_decisions",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_member_execution_queue.csv",
        "person_enrichment_action_member_execution_ledger",
        "csv",
        "person_enrichment_action_member_execution_queue",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_member_execution_audit.csv",
        "person_enrichment_action_member_execution_ledger",
        "csv",
        "person_enrichment_action_member_execution_audit",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_member_execution_dossiers.csv",
        "person_enrichment_action_member_execution_dossier_ledger",
        "csv",
        "person_enrichment_action_member_execution_dossiers",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_member_execution_packets.csv",
        "person_enrichment_action_member_execution_packet_ledger",
        "csv",
        "person_enrichment_action_member_execution_packets",
        True,
    ),
    (
        "artifacts/data/person_enrichment_action_execution_plan.csv",
        "person_enrichment_action_execution_plan_ledger",
        "csv",
        "person_enrichment_action_execution_plan",
        True,
    ),
    (
        "artifacts/data/research_identity_corroboration.csv",
        "research_identity_corroboration_ledger",
        "csv",
        "research_identity_corroboration",
        True,
    ),
    (
        "artifacts/data/research_identity_review_batches.csv",
        "research_identity_review_batch_ledger",
        "csv",
        "research_identity_review_batches",
        True,
    ),
    (
        "artifacts/data/research_identity_review_batch_members.csv",
        "research_identity_review_batch_member_ledger",
        "csv",
        "research_identity_review_batch_members",
        True,
    ),
    (
        "artifacts/data/research_identity_reviewer_decisions.csv",
        "research_identity_reviewer_decision_input",
        "csv",
        "research_identity_reviewer_decisions",
        True,
    ),
    (
        "artifacts/data/research_identity_reviewer_decision_queue.csv",
        "research_identity_reviewer_decision_ledger",
        "csv",
        "research_identity_reviewer_decision_queue",
        True,
    ),
    (
        "artifacts/data/research_identity_reviewer_decision_audit.csv",
        "research_identity_reviewer_decision_ledger",
        "csv",
        "research_identity_reviewer_decision_audit",
        True,
    ),
    (
        "artifacts/data/research_identity_reviewer_decision_dossiers.csv",
        "research_identity_reviewer_decision_dossier_ledger",
        "csv",
        "research_identity_reviewer_decision_dossiers",
        True,
    ),
    (
        "artifacts/data/research_identity_conflict_resolution_packets.csv",
        "research_identity_conflict_resolution_packet_ledger",
        "csv",
        "research_identity_conflict_resolution_packets",
        True,
    ),
    (
        "artifacts/data/research_identity_conflict_identifier_evidence.csv",
        "research_identity_conflict_identifier_evidence_ledger",
        "csv",
        "research_identity_conflict_identifier_evidence",
        True,
    ),
    (
        "artifacts/data/research_identity_review_batch_packets.csv",
        "research_identity_review_batch_packet_ledger",
        "csv",
        "research_identity_review_batch_packets",
        True,
    ),
    (
        "artifacts/data/research_identity_review_batch_member_packets.csv",
        "research_identity_review_batch_member_packet_ledger",
        "csv",
        "research_identity_review_batch_member_packets",
        True,
    ),
    (
        "artifacts/data/penn_trainee_profile_claims.csv",
        "trainee_profile_enrichment_ledger",
        "csv",
        None,
        True,
    ),
    (
        "artifacts/data/penn_trainee_profile_claims.json",
        "trainee_profile_enrichment_ledger",
        "json_array",
        None,
        True,
    ),
    (
        "artifacts/data/penn_trainee_profile_sources.json",
        "trainee_profile_enrichment_ledger",
        "json_array",
        None,
        True,
    ),
    (
        "artifacts/data/penn_trainee_profile_summary.json",
        "trainee_profile_enrichment_ledger",
        "json_object",
        None,
        True,
    ),
    ("artifacts/data/evidence_claims.csv", "warehouse_export", "csv", "evidence_claims", True),
    (
        "artifacts/data/orcid_pubmed_article_candidate_claims.json",
        "research_enrichment_source_artifact",
        "json_array",
        None,
        True,
    ),
    (
        "artifacts/data/orcid_pubmed_article_candidate_summary.json",
        "research_enrichment_source_artifact",
        "json_object",
        None,
        True,
    ),
    ("artifacts/data/evidence_reconciliation_decisions.csv", "reconciliation_ledger", "csv", "evidence_reconciliation_decisions", True),
    ("artifacts/data/person_reconciliation_decisions.csv", "reconciliation_ledger", "csv", "person_reconciliation_decisions", True),
    ("artifacts/data/person_evidence_review_packets.csv", "reconciliation_ledger", "csv", "person_evidence_review_packets", True),
    ("artifacts/data/person_evidence_reviewer_decisions.csv", "person_evidence_reviewer_decision_input", "csv", "person_evidence_reviewer_decisions", True),
    ("artifacts/data/person_evidence_reviewer_decision_queue.csv", "person_evidence_reviewer_decision_ledger", "csv", "person_evidence_reviewer_decision_queue", True),
    ("artifacts/data/person_evidence_reviewer_decision_audit.csv", "person_evidence_reviewer_decision_ledger", "csv", "person_evidence_reviewer_decision_audit", True),
    ("artifacts/data/person_evidence_review_triage.csv", "person_evidence_review_triage_ledger", "csv", "person_evidence_review_triage", True),
    ("artifacts/data/person_evidence_review_dossiers.csv", "person_evidence_review_dossier_ledger", "csv", "person_evidence_review_dossiers", True),
    ("artifacts/data/person_evidence_review_batches.csv", "person_evidence_review_batch_ledger", "csv", "person_evidence_review_batches", True),
    ("artifacts/data/person_evidence_review_batch_packets.csv", "person_evidence_review_batch_packet_ledger", "csv", "person_evidence_review_batch_packets", True),
    ("artifacts/data/enrichment_acceptance_audit.csv", "acceptance_ledger", "csv", "enrichment_acceptance_audit", True),
    ("artifacts/data/accepted_enrichment_claims.csv", "accepted_enrichment_ledger", "csv", "accepted_enrichment_claims", True),
    ("artifacts/data/npi_candidate_claims.csv", "identity_enrichment_ledger", "csv", "npi_candidate_claims", True),
    ("artifacts/data/npi_source_observations.csv", "source_observation_ledger", "csv", "npi_source_observations", True),
    ("artifacts/data/person_contacts.csv", "contact_ledger", "csv", "person_contacts", True),
    ("artifacts/data/contact_assurance_audit.csv", "contact_assurance_ledger", "csv", "contact_assurance_audit", True),
    ("artifacts/data/contact_verification_contracts.csv", "contact_verification_contract_ledger", "csv", "contact_verification_contracts", True),
    (
        "artifacts/data/contact_reobservation_audit.csv",
        "contact_reobservation_ledger",
        "csv",
        "contact_reobservation_audit",
        True,
    ),
    (
        "artifacts/data/contact_verification_reviewer_decisions.csv",
        "contact_verification_reviewer_decision_input",
        "csv",
        "contact_verification_reviewer_decisions",
        True,
    ),
    (
        "artifacts/data/contact_verification_reviewer_decision_queue.csv",
        "contact_verification_reviewer_decision_ledger",
        "csv",
        "contact_verification_reviewer_decision_queue",
        True,
    ),
    (
        "artifacts/data/contact_verification_reviewer_decision_audit.csv",
        "contact_verification_reviewer_decision_ledger",
        "csv",
        "contact_verification_reviewer_decision_audit",
        True,
    ),
    (
        "artifacts/data/contact_verification_reviewer_decision_dossiers.csv",
        "contact_verification_reviewer_decision_dossier_ledger",
        "csv",
        "contact_verification_reviewer_decision_dossiers",
        True,
    ),
    (
        "artifacts/data/contact_verification_batches.csv",
        "contact_verification_batch_ledger",
        "csv",
        "contact_verification_batches",
        True,
    ),
    (
        "artifacts/data/contact_verification_batch_packets.csv",
        "contact_verification_batch_packet_ledger",
        "csv",
        "contact_verification_batch_packets",
        True,
    ),
    (
        "artifacts/data/accepted_verified_contact_facts.csv",
        "accepted_verified_contact_ledger",
        "csv",
        "accepted_verified_contact_facts",
        True,
    ),
    ("artifacts/data/career_events.csv", "attending_trend_input", "csv", "career_events", True),
    ("artifacts/data/attending_trend_reconciliation.csv", "attending_trend_ledger", "csv", "attending_trend_reconciliation", True),
    ("artifacts/data/attending_trend_review_claims.csv", "attending_trend_ledger", "csv", "attending_trend_review_claims", True),
    ("artifacts/data/attending_trend_acceptance_audit.csv", "attending_trend_acceptance_ledger", "csv", "attending_trend_acceptance_audit", True),
    ("artifacts/data/attending_trend_reviewer_decisions.csv", "attending_trend_reviewer_decision_input", "csv", "attending_trend_reviewer_decisions", True),
    ("artifacts/data/attending_trend_reviewer_decision_queue.csv", "attending_trend_reviewer_decision_ledger", "csv", "attending_trend_reviewer_decision_queue", True),
    ("artifacts/data/attending_trend_reviewer_decision_audit.csv", "attending_trend_reviewer_decision_ledger", "csv", "attending_trend_reviewer_decision_audit", True),
    ("artifacts/data/attending_trend_reviewer_decision_dossiers.csv", "attending_trend_reviewer_decision_dossier_ledger", "csv", "attending_trend_reviewer_decision_dossiers", True),
    ("artifacts/data/accepted_attending_trend_facts.csv", "attending_trend_accepted_fact_ledger", "csv", "accepted_attending_trend_facts", True),
    ("artifacts/data/attending_trend_dossiers.csv", "attending_trend_dossier_ledger", "csv", "attending_trend_dossiers", True),
    ("artifacts/data/attending_trend_review_rollups.csv", "attending_trend_ledger", "csv", "attending_trend_review_rollups", True),
    ("artifacts/data/attending_biosketch_bridge_candidates.csv", "attending_trend_ledger", "csv", "attending_biosketch_bridge_candidates", True),
    ("artifacts/data/attending_historical_link_search_queries.csv", "attending_trend_historical_discovery_ledger", "csv", "attending_historical_link_search_queries", True),
    (
        "artifacts/data/attending_historical_link_search_observations.csv",
        "attending_trend_historical_discovery_ledger",
        "csv",
        "attending_historical_link_search_observations",
        True,
    ),
    ("artifacts/data/attending_historical_link_candidates.csv", "attending_trend_historical_discovery_ledger", "csv", "attending_historical_link_candidates", True),
    ("artifacts/data/attending_trend_discovery_workbench.csv", "attending_trend_discovery_workbench_ledger", "csv", "attending_trend_discovery_workbench", True),
    ("artifacts/data/attending_trend_discovery_batches.csv", "attending_trend_discovery_batch_ledger", "csv", "attending_trend_discovery_batches", True),
    ("artifacts/data/attending_trend_discovery_packets.csv", "attending_trend_discovery_packet_ledger", "csv", "attending_trend_discovery_packets", True),
    ("artifacts/data/program_identifier_candidates.csv", "program_identifier_ledger", "csv", "program_identifier_candidates", True),
    ("artifacts/data/program_identifier_reconciliation.csv", "program_identifier_ledger", "csv", "program_identifier_reconciliation", True),
    ("artifacts/data/official_program_identifiers.csv", "program_identifier_ledger", "csv", "official_program_identifiers", True),
    ("artifacts/data/program_lifecycle_consistency_audit.csv", "program_lifecycle_ledger", "csv", "program_lifecycle_consistency_audit", True),
    (
        "artifacts/data/program_lifecycle_duration_source_observations.csv",
        "program_lifecycle_duration_ledger",
        "csv",
        "program_lifecycle_duration_source_observations",
        True,
    ),
    (
        "artifacts/data/program_lifecycle_duration_evidence.csv",
        "program_lifecycle_duration_ledger",
        "csv",
        "program_lifecycle_duration_evidence",
        True,
    ),
    (
        "artifacts/data/program_lifecycle_duration_reviewer_decisions.csv",
        "program_lifecycle_duration_reviewer_decision_input",
        "csv",
        "program_lifecycle_duration_reviewer_decisions",
        True,
    ),
    (
        "artifacts/data/program_lifecycle_duration_reviewer_decision_queue.csv",
        "program_lifecycle_duration_reviewer_decision_ledger",
        "csv",
        "program_lifecycle_duration_reviewer_decision_queue",
        True,
    ),
    (
        "artifacts/data/program_lifecycle_duration_reviewer_decision_audit.csv",
        "program_lifecycle_duration_reviewer_decision_ledger",
        "csv",
        "program_lifecycle_duration_reviewer_decision_audit",
        True,
    ),
    (
        "artifacts/data/program_lifecycle_duration_review_batches.csv",
        "program_lifecycle_duration_review_batch_ledger",
        "csv",
        "program_lifecycle_duration_review_batches",
        True,
    ),
    (
        "artifacts/data/accepted_program_lifecycle_duration_mappings.csv",
        "program_lifecycle_duration_accepted_mapping_ledger",
        "csv",
        "accepted_program_lifecycle_duration_mappings",
        True,
    ),
    ("artifacts/data/source_utility_scorecard.csv", "source_quality_ledger", "csv", "source_utility_scorecard", True),
    ("artifacts/data/search_utility_assurance.csv", "source_quality_ledger", "csv", "search_utility_assurance", True),
    (
        "artifacts/data/source_quality_policy_recommendations.csv",
        "source_quality_policy_ledger",
        "csv",
        "source_quality_policy_recommendations",
        True,
    ),
    (
        "artifacts/data/search_utility_execution_batches.csv",
        "source_quality_execution_batch_ledger",
        "csv",
        "search_utility_execution_batches",
        True,
    ),
    (
        "artifacts/data/search_utility_execution_batch_packets.csv",
        "source_quality_execution_batch_packet_ledger",
        "csv",
        "search_utility_execution_batch_packets",
        True,
    ),
    ("artifacts/data/corpus_action_worklist.csv", "operator_worklist", "csv", "corpus_action_worklist", True),
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def csv_rows(path: Path) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration:
            return 0
        return sum(1 for _ in reader)


def json_rows(path: Path, artifact_format: str) -> int | None:
    value = json.loads(path.read_text(encoding="utf-8"))
    if artifact_format == "json_array" and isinstance(value, list):
        return len(value)
    if artifact_format == "json_object" and isinstance(value, dict):
        return 1
    return None


def glob_paths(rel_pattern: str) -> list[Path]:
    return sorted(ROOT.glob(rel_pattern))


def sha256_paths(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path.relative_to(ROOT)).encode("utf-8"))
        h.update(b"\0")
        h.update(sha256_file(path).encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def sqlite_count(conn: sqlite3.Connection, table: str | None) -> int | None:
    if not table:
        return None
    return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def is_git_tracked(rel_path: str) -> bool:
    result = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel_path],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def classify_row(spec: tuple, conn: sqlite3.Connection, audited_at: str) -> dict:
    rel_path, role, artifact_format, table, required = spec
    path = ROOT / rel_path
    is_glob = artifact_format.endswith("_glob")
    paths = glob_paths(rel_path) if is_glob else [path]
    exists = bool(paths) if is_glob else path.exists()
    git_tracked = all(is_git_tracked(str(item.relative_to(ROOT))) for item in paths) if is_glob and paths else is_git_tracked(rel_path)
    byte_size = sum(item.stat().st_size for item in paths) if is_glob else path.stat().st_size if exists else 0
    file_hash = "" if rel_path == "artifacts/data/redmank.sqlite" else sha256_paths(paths) if is_glob and paths else sha256_file(path) if exists else ""
    artifact_rows = None
    if exists and artifact_format == "csv":
        artifact_rows = csv_rows(path)
    elif exists and artifact_format == "csv_glob":
        artifact_rows = sum(csv_rows(item) for item in paths)
    elif exists and artifact_format.startswith("json"):
        if artifact_format == "json_object_glob":
            artifact_rows = sum(1 for item in paths if json_rows(item, "json_object") == 1)
        else:
            artifact_rows = json_rows(path, artifact_format)
    sqlite_rows = sqlite_count(conn, table)

    if not exists and required:
        row_status = "missing_required_artifact"
        freshness_status = "blocked"
        action = "regenerate_required_artifact_before_claiming_reproducible_warehouse"
    elif table and artifact_rows != sqlite_rows:
        row_status = "row_count_mismatch"
        freshness_status = "review_required"
        action = "rerun_source_script_or_investigate_csv_sqlite_count_drift"
    elif (
        rel_path == "artifacts/data/redmank.sqlite"
        and byte_size > GITHUB_RECOMMENDED_FILE_LIMIT_BYTES
        and git_tracked
    ):
        row_status = "binary_size_warning"
        freshness_status = "reproducible_with_repository_pressure"
        action = "move_sqlite_to_lfs_or_treat_as_generated_artifact_before_growth_continues"
    elif exists:
        row_status = "ok"
        freshness_status = "artifact_present"
        action = "retain_and_refresh_when_upstream_inputs_change"
    else:
        row_status = "optional_artifact_missing"
        freshness_status = "not_required"
        action = "no_action_required"

    evidence = {
        "github_recommended_file_limit_bytes": GITHUB_RECOMMENDED_FILE_LIMIT_BYTES,
        "path": rel_path,
        "globbed_paths": [str(item.relative_to(ROOT)) for item in paths] if is_glob else [],
        "sqlite_table": table,
        "artifact_rows": artifact_rows,
        "sqlite_rows": sqlite_rows,
        "git_tracked": git_tracked,
        "sha256_omitted_reason": "self_referential_sqlite_audit_table" if rel_path == "artifacts/data/redmank.sqlite" else "",
    }
    return {
        "audit_key": "warehouse_reproducibility_" + hashlib.sha1(rel_path.encode("utf-8")).hexdigest()[:16],
        "artifact_path": rel_path,
        "artifact_role": role,
        "artifact_format": artifact_format,
        "required": 1 if required else 0,
        "exists_on_disk": 1 if exists else 0,
        "byte_size": byte_size,
        "sha256": file_hash,
        "sqlite_table": table or "",
        "artifact_rows": artifact_rows if artifact_rows is not None else "",
        "sqlite_rows": sqlite_rows if sqlite_rows is not None else "",
        "row_count_status": row_status,
        "freshness_status": freshness_status,
        "recommended_action": action,
        "evidence_json": dumps(evidence),
        "audited_at": audited_at,
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DROP TABLE IF EXISTS warehouse_reproducibility_audit")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM warehouse_reproducibility_audit")
    db_rows = []
    for row in rows:
        db_row = dict(row)
        for key in ["artifact_rows", "sqlite_rows"]:
            if db_row[key] == "":
                db_row[key] = None
        db_rows.append(db_row)
    conn.executemany(
        """
        INSERT INTO warehouse_reproducibility_audit
        (audit_key, artifact_path, artifact_role, artifact_format, required,
         exists_on_disk, byte_size, sha256, sqlite_table, artifact_rows,
         sqlite_rows, row_count_status, freshness_status, recommended_action,
         evidence_json, audited_at)
        VALUES
        (:audit_key, :artifact_path, :artifact_role, :artifact_format, :required,
         :exists_on_disk, :byte_size, :sha256, :sqlite_table, :artifact_rows,
         :sqlite_rows, :row_count_status, :freshness_status, :recommended_action,
         :evidence_json, :audited_at)
        """,
        db_rows,
    )


def write_outputs(rows: list[dict], audited_at: str) -> dict:
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    by_status = Counter(row["row_count_status"] for row in rows)
    by_role = Counter(row["artifact_role"] for row in rows)
    required_missing = sum(1 for row in rows if row["required"] and not row["exists_on_disk"])
    mismatches = by_status.get("row_count_mismatch", 0)
    binary_warnings = by_status.get("binary_size_warning", 0)
    sqlite_row = next((row for row in rows if row["artifact_path"] == "artifacts/data/redmank.sqlite"), None)
    sqlite_evidence = json.loads(sqlite_row["evidence_json"]) if sqlite_row else {}
    sqlite_git_tracked = bool(sqlite_evidence.get("git_tracked"))
    sqlite_storage_policy = "tracked_git_blob" if sqlite_git_tracked else "generated_untracked_sqlite_warehouse"
    sqlite_path = ROOT / "artifacts/data/redmank.sqlite"
    sqlite_sha256 = sha256_file(sqlite_path) if sqlite_path.exists() else ""
    summary = {
        "audited_at": audited_at,
        "artifact_rows": len(rows),
        "required_missing_artifacts": required_missing,
        "row_count_mismatch_rows": mismatches,
        "binary_size_warning_rows": binary_warnings,
        "sqlite_byte_size": sqlite_row["byte_size"] if sqlite_row else 0,
        "sqlite_sha256": sqlite_sha256,
        "sqlite_git_tracked": sqlite_git_tracked,
        "sqlite_storage_policy": sqlite_storage_policy,
        "sqlite_manifest": "artifacts/data/redmank_sqlite_manifest.json",
        "github_recommended_file_limit_bytes": GITHUB_RECOMMENDED_FILE_LIMIT_BYTES,
        "by_row_count_status": dict(sorted(by_status.items())),
        "by_artifact_role": dict(sorted(by_role.items())),
        "csv": "artifacts/data/warehouse_reproducibility_audit.csv",
        "json": "artifacts/data/warehouse_reproducibility_audit.json",
        "acceptance_rule": "A warehouse is reproducible only when required artifacts exist and row counts match their SQLite tables; binary size warnings do not invalidate data, but they require repository storage action.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    if sqlite_row:
        manifest = {
            "generated_at": audited_at,
            "artifact_path": sqlite_row["artifact_path"],
            "storage_policy": sqlite_storage_policy,
            "git_tracked": sqlite_git_tracked,
            "byte_size": sqlite_row["byte_size"],
            "sha256": sqlite_sha256,
            "row_count_status": sqlite_row["row_count_status"],
            "sha256_scope": "post_reproducibility_audit_sqlite_file",
            "rebuild_command": "python3 scripts/rebuild_local_warehouse.py",
            "validation_commands": [
                "sqlite3 artifacts/data/redmank.sqlite 'PRAGMA integrity_check;'",
                "python3 scripts/audit_warehouse_reproducibility.py",
                "python3 scripts/rebuild_local_warehouse.py --dry-run",
            ],
            "notes": "The SQLite warehouse is generated locally from committed flat artifacts and is intentionally ignored by Git once it exceeds normal repository blob size. Committed CSV/JSON artifacts plus this manifest preserve provenance and rebuild verification without pushing the binary.",
        }
        SQLITE_MANIFEST_PATH.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()
    audited_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = [classify_row(spec, conn, audited_at) for spec in ARTIFACT_SPECS]
    with conn:
        write_db(conn, rows)
    conn.close()
    print(dumps(write_outputs(rows, audited_at)))


if __name__ == "__main__":
    main()
