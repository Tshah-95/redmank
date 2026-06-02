#!/usr/bin/env python3
"""Write warehouse summary counts for the current SQLite database."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    tables = [
        "people",
        "sources",
        "source_utilities",
        "program_lifecycle_rules",
        "programs",
        "organizations",
        "organization_aliases",
        "organization_identifiers",
        "organization_identifier_candidates",
        "medical_student_source_audit",
        "person_training_events",
        "person_training_states",
        "person_evidence_review_packets",
        "person_evidence_reviewer_decisions",
        "person_evidence_reviewer_decision_queue",
        "person_evidence_reviewer_decision_audit",
        "training_state_snapshots",
        "training_state_snapshot_rows",
        "training_state_transition_events",
        "training_state_transition_rollups",
        "person_enrichment_coverage",
        "program_enrichment_coverage",
        "person_enrichment_dossiers",
        "person_enrichment_work_queue",
        "person_enrichment_execution_readiness",
        "person_enrichment_execution_readiness_rollups",
        "person_enrichment_execution_batches",
        "training_state_machine_audit",
        "person_training_state_machine_audit",
        "program_training_state_machine_audit",
        "training_state_refresh_expectations",
        "person_refresh_expectations",
        "program_refresh_expectations",
        "category_refresh_expectations",
        "training_lifecycle_assurance_rollups",
        "training_state_transition_plan",
        "training_state_transition_plan_rollups",
        "training_temporal_contracts",
        "training_temporal_contract_rollups",
        "trainee_profile_search_queries",
        "trainee_profile_search_observations",
        "trainee_profile_discovery_candidates",
        "prior_training_search_queries",
        "prior_training_search_observations",
        "prior_training_discovery_candidates",
        "career_events",
        "attending_biosketch_bridge_candidates",
        "attending_trend_reconciliation",
        "attending_trend_review_claims",
        "attending_trend_acceptance_audit",
        "attending_trend_reviewer_decisions",
        "attending_trend_reviewer_decision_queue",
        "attending_trend_reviewer_decision_audit",
        "accepted_attending_trend_facts",
        "attending_trend_dossiers",
        "attending_trend_review_rollups",
        "npi_candidate_claims",
        "npi_source_observations",
        "person_contacts",
        "contact_assurance_audit",
        "contact_verification_contracts",
        "contact_verification_reviewer_decisions",
        "contact_verification_reviewer_decision_queue",
        "contact_verification_reviewer_decision_audit",
        "accepted_verified_contact_facts",
        "evidence_claims",
        "evidence_reconciliation_decisions",
        "person_reconciliation_decisions",
        "enrichment_acceptance_audit",
        "accepted_enrichment_claims",
        "warehouse_reproducibility_audit",
        "source_quality_observations",
        "source_utility_scorecard",
        "search_utility_assurance",
        "corpus_action_worklist",
        "official_program_universe",
        "official_program_coverage_audit",
        "official_program_source_probes",
        "official_program_source_search_queries",
        "official_program_source_search_observations",
        "official_program_source_candidates",
        "official_program_gap_reason_audit",
        "official_gap_roster_reconciliation",
        "official_gap_roster_program_resolution",
        "official_program_coverage_assurance_audit",
        "official_program_coverage_action_queue",
        "official_program_coverage_dossiers",
        "official_program_alias_review_packets",
        "official_program_alias_reviewer_decisions",
        "official_program_alias_reviewer_decision_queue",
        "official_program_alias_reviewer_decision_audit",
        "accepted_official_program_alias_mappings",
        "official_program_alias_reconciliation_candidates",
        "program_identifier_source_observations",
        "program_identifier_candidates",
        "program_identifier_reconciliation",
        "official_program_identifiers",
        "program_lifecycle_consistency_audit",
        "program_lifecycle_duration_source_observations",
        "program_lifecycle_duration_evidence",
        "program_lifecycle_duration_reviewer_decisions",
        "program_lifecycle_duration_reviewer_decision_queue",
        "program_lifecycle_duration_reviewer_decision_audit",
        "accepted_program_lifecycle_duration_mappings",
    ]
    counts = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
    resolver_counts = {
        row["resolver_status"]: row["count"]
        for row in conn.execute(
            "SELECT resolver_status, COUNT(*) AS count FROM person_training_events GROUP BY resolver_status"
        )
    }
    evidence_status_counts = {
        row["status"]: row["count"]
        for row in conn.execute("SELECT status, COUNT(*) AS count FROM evidence_claims GROUP BY status")
    }
    evidence_source_counts = {
        row["source_key"]: row["count"]
        for row in conn.execute("SELECT source_key, COUNT(*) AS count FROM evidence_claims GROUP BY source_key")
    }
    role_counts = {
        row["role"]: row["count"]
        for row in conn.execute("SELECT role, COUNT(*) AS count FROM people GROUP BY role")
    }
    generic_program_label_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM person_program_memberships m
        JOIN programs p ON p.program_key = m.program_key
        WHERE p.program_name IN ('Residents', 'Fellows')
        """
    ).fetchone()[0]
    training_state_family_counts = {
        row["stage_family"]: row["count"]
        for row in conn.execute("SELECT stage_family, COUNT(*) AS count FROM person_training_states GROUP BY stage_family")
    }
    normalized_stage_counts = {
        row["normalized_stage"]: row["count"]
        for row in conn.execute(
            "SELECT normalized_stage, COUNT(*) AS count FROM person_training_states GROUP BY normalized_stage"
        )
    }
    lifecycle_code_counts = {
        row["lifecycle_code"] or "none": row["count"]
        for row in conn.execute(
            "SELECT lifecycle_code, COUNT(*) AS count FROM person_training_states GROUP BY lifecycle_code"
        )
    }
    expected_transition_type_counts = {
        row["expected_transition_type"] or "none": row["count"]
        for row in conn.execute(
            """
            SELECT expected_transition_type, COUNT(*) AS count
            FROM person_training_states
            GROUP BY expected_transition_type
            """
        )
    }
    stale_by_next_august_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM person_training_states
        WHERE stale_after_date IS NOT NULL
          AND stale_after_date <= date('now', '+14 months')
        """
    ).fetchone()[0]
    career_event_counts = {
        row["event_type"]: row["count"]
        for row in conn.execute("SELECT event_type, COUNT(*) AS count FROM career_events GROUP BY event_type")
    }
    attending_biosketch_bridge_counts = {
        row["bridge_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT bridge_status, COUNT(*) AS count
            FROM attending_biosketch_bridge_candidates
            GROUP BY bridge_status
            """
        )
    }
    attending_trend_reconciliation_counts = {
        row["trend_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT trend_status, COUNT(*) AS count
            FROM attending_trend_reconciliation
            GROUP BY trend_status
            """
        )
    }
    attending_trend_review_claim_counts = {
        row["trend_claim_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT trend_claim_type, COUNT(*) AS count
            FROM attending_trend_review_claims
            GROUP BY trend_claim_type
            """
        )
    }
    attending_trend_acceptance_counts = {
        row["acceptance_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT acceptance_status, COUNT(*) AS count
            FROM attending_trend_acceptance_audit
            GROUP BY acceptance_status
            """
        )
    }
    attending_trend_acceptance_fact_counts = {
        str(row["accepted_trend_fact"]): row["count"]
        for row in conn.execute(
            """
            SELECT accepted_trend_fact, COUNT(*) AS count
            FROM attending_trend_acceptance_audit
            GROUP BY accepted_trend_fact
            """
        )
    }
    attending_trend_reviewer_decision_counts = {
        row["decision_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT decision_status, COUNT(*) AS count
            FROM attending_trend_reviewer_decision_audit
            GROUP BY decision_status
            """
        )
    }
    accepted_attending_trend_fact_counts = {
        row["trend_fact_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT trend_fact_type, COUNT(*) AS count
            FROM accepted_attending_trend_facts
            GROUP BY trend_fact_type
            """
        )
    }
    attending_trend_dossier_status_counts = {
        row["dossier_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT dossier_status, COUNT(*) AS count
            FROM attending_trend_dossiers
            GROUP BY dossier_status
            """
        )
    }
    attending_trend_dossier_safety_counts = {
        row["display_safety_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT display_safety_status, COUNT(*) AS count
            FROM attending_trend_dossiers
            GROUP BY display_safety_status
            """
        )
    }
    attending_trend_review_end_year_counts = {
        str(row["training_end_year"]): row["count"]
        for row in conn.execute(
            """
            SELECT training_end_year, COUNT(*) AS count
            FROM attending_trend_review_claims
            GROUP BY training_end_year
            """
        )
    }
    attending_trend_review_rollup_scope_counts = {
        row["rollup_scope"]: row["count"]
        for row in conn.execute(
            """
            SELECT rollup_scope, COUNT(*) AS count
            FROM attending_trend_review_rollups
            GROUP BY rollup_scope
            """
        )
    }
    npi_candidate_counts = {
        row["candidate_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT candidate_status, COUNT(*) AS count
            FROM npi_candidate_claims
            GROUP BY candidate_status
            """
        )
    }
    npi_primary_taxonomy_counts = {
        row["primary_taxonomy"] or "none": row["count"]
        for row in conn.execute(
            """
            SELECT primary_taxonomy, COUNT(*) AS count
            FROM npi_candidate_claims
            GROUP BY primary_taxonomy
            ORDER BY count DESC, primary_taxonomy
            LIMIT 30
            """
        )
    }
    evidence_reconciliation_queue_counts = {
        f"{row['record_type']}:{row['status']}": row["count"]
        for row in conn.execute(
            """
            SELECT record_type, status, COUNT(*) AS count
            FROM v_evidence_reconciliation_queue
            GROUP BY record_type, status
            """
        )
    }
    evidence_reconciliation_top_claim_counts = {
        row["claim_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT claim_type, COUNT(*) AS count
            FROM v_evidence_reconciliation_queue
            GROUP BY claim_type
            ORDER BY count DESC
            LIMIT 20
            """
        )
    }
    evidence_reconciliation_decision_counts = {
        row["decision"]: row["count"]
        for row in conn.execute(
            """
            SELECT decision, COUNT(*) AS count
            FROM evidence_reconciliation_decisions
            GROUP BY decision
            """
        )
    }
    person_reconciliation_decision_counts = {
        row["top_decision"]: row["count"]
        for row in conn.execute(
            """
            SELECT top_decision, COUNT(*) AS count
            FROM person_reconciliation_decisions
            GROUP BY top_decision
            """
        )
    }
    person_evidence_review_packet_counts = {
        row["packet_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT packet_status, COUNT(*) AS count
            FROM person_evidence_review_packets
            GROUP BY packet_status
            """
        )
    }
    enrichment_acceptance_counts = {
        row["acceptance_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT acceptance_status, COUNT(*) AS count
            FROM enrichment_acceptance_audit
            GROUP BY acceptance_status
            """
        )
    }
    accepted_enrichment_counts = {
        row["enrichment_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT enrichment_type, COUNT(*) AS count
            FROM accepted_enrichment_claims
            GROUP BY enrichment_type
            """
        )
    }
    accepted_enrichment_role_counts = {
        row["role"]: row["count"]
        for row in conn.execute(
            """
            SELECT role, COUNT(*) AS count
            FROM accepted_enrichment_claims
            GROUP BY role
            """
        )
    }
    warehouse_reproducibility_counts = {
        row["row_count_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT row_count_status, COUNT(*) AS count
            FROM warehouse_reproducibility_audit
            GROUP BY row_count_status
            """
        )
    }
    state_machine_status_counts = {
        row["state_machine_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT state_machine_status, COUNT(*) AS count
            FROM training_state_machine_audit
            GROUP BY state_machine_status
            """
        )
    }
    transition_rollup_scope_counts = {
        row["rollup_scope"]: row["count"]
        for row in conn.execute(
            """
            SELECT rollup_scope, COUNT(*) AS count
            FROM training_state_transition_rollups
            GROUP BY rollup_scope
            """
        )
    }
    refresh_readiness_counts = {
        row["readiness_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT readiness_status, COUNT(*) AS count
            FROM training_state_refresh_expectations
            GROUP BY readiness_status
            """
        )
    }
    lifecycle_assurance_counts = {
        row["assurance_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT assurance_status, COUNT(*) AS count
            FROM training_lifecycle_assurance_rollups
            GROUP BY assurance_status
            """
        )
    }
    lifecycle_assurance_diff_counts = {
        row["diff_readiness_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT diff_readiness_status, COUNT(*) AS count
            FROM training_lifecycle_assurance_rollups
            GROUP BY diff_readiness_status
            """
        )
    }
    transition_plan_policy_counts = {
        row["policy_lane"]: row["count"]
        for row in conn.execute(
            """
            SELECT policy_lane, COUNT(*) AS count
            FROM training_state_transition_plan
            GROUP BY policy_lane
            """
        )
    }
    transition_plan_diff_counts = {
        row["diff_readiness_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT diff_readiness_status, COUNT(*) AS count
            FROM training_state_transition_plan
            GROUP BY diff_readiness_status
            """
        )
    }
    transition_plan_rollup_scope_counts = {
        row["rollup_scope"]: row["count"]
        for row in conn.execute(
            """
            SELECT rollup_scope, COUNT(*) AS count
            FROM training_state_transition_plan_rollups
            GROUP BY rollup_scope
            """
        )
    }
    temporal_contract_counts = {
        row["next_refresh_contract"]: row["count"]
        for row in conn.execute(
            """
            SELECT next_refresh_contract, COUNT(*) AS count
            FROM training_temporal_contracts
            GROUP BY next_refresh_contract
            """
        )
    }
    temporal_contract_state_counts = {
        row["current_temporal_state_code"]: row["count"]
        for row in conn.execute(
            """
            SELECT current_temporal_state_code, COUNT(*) AS count
            FROM training_temporal_contracts
            GROUP BY current_temporal_state_code
            """
        )
    }
    temporal_contract_guardrail_counts = {
        row["guardrail_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT guardrail_status, COUNT(*) AS count
            FROM training_temporal_contract_rollups
            GROUP BY guardrail_status
            """
        )
    }
    temporal_contract_rollup_scope_counts = {
        row["rollup_scope"]: row["count"]
        for row in conn.execute(
            """
            SELECT rollup_scope, COUNT(*) AS count
            FROM training_temporal_contract_rollups
            GROUP BY rollup_scope
            """
        )
    }
    trainee_profile_discovery_candidate_counts = {
        row["candidate_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT candidate_status, COUNT(*) AS count
            FROM trainee_profile_discovery_candidates
            GROUP BY candidate_status
            """
        )
    }
    trainee_profile_search_status_counts = {
        str(row["search_http_status"]): row["count"]
        for row in conn.execute(
            """
            SELECT search_http_status, COUNT(*) AS count
            FROM trainee_profile_search_observations
            GROUP BY search_http_status
            """
        )
    }
    prior_training_discovery_candidate_counts = {
        row["candidate_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT candidate_status, COUNT(*) AS count
            FROM prior_training_discovery_candidates
            GROUP BY candidate_status
            """
        )
    }
    prior_training_search_status_counts = {
        str(row["search_http_status"]): row["count"]
        for row in conn.execute(
            """
            SELECT search_http_status, COUNT(*) AS count
            FROM prior_training_search_observations
            GROUP BY search_http_status
            """
        )
    }
    person_dossier_status_counts = {
        row["dossier_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT dossier_status, COUNT(*) AS count
            FROM person_enrichment_dossiers
            GROUP BY dossier_status
            """
        )
    }
    person_dossier_display_safety_counts = {
        row["display_safety_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT display_safety_status, COUNT(*) AS count
            FROM person_enrichment_dossiers
            GROUP BY display_safety_status
            """
        )
    }
    contact_counts = {
        row["contact_type"]: row["count"]
        for row in conn.execute("SELECT contact_type, COUNT(*) AS count FROM person_contacts GROUP BY contact_type")
    }
    contact_assurance_counts = {
        row["assurance_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT assurance_status, COUNT(*) AS count
            FROM contact_assurance_audit
            GROUP BY assurance_status
            """
        )
    }
    contact_display_safety_counts = {
        row["display_safety_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT display_safety_status, COUNT(*) AS count
            FROM contact_assurance_audit
            GROUP BY display_safety_status
            """
        )
    }
    contact_verification_lane_counts = {
        row["verification_lane"]: row["count"]
        for row in conn.execute(
            """
            SELECT verification_lane, COUNT(*) AS count
            FROM contact_verification_contracts
            GROUP BY verification_lane
            """
        )
    }
    contact_operational_use_counts = {
        row["operational_use_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT operational_use_status, COUNT(*) AS count
            FROM contact_verification_contracts
            GROUP BY operational_use_status
            """
        )
    }
    contact_reviewer_decision_counts = {
        row["decision_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT decision_status, COUNT(*) AS count
            FROM contact_verification_reviewer_decision_audit
            GROUP BY decision_status
            """
        )
    }
    contact_reviewer_queue_counts = {
        row["queue_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT queue_status, COUNT(*) AS count
            FROM contact_verification_reviewer_decision_queue
            GROUP BY queue_status
            """
        )
    }
    accepted_contact_counts = {
        row["contact_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT contact_type, COUNT(*) AS count
            FROM accepted_verified_contact_facts
            GROUP BY contact_type
            """
        )
    }
    official_program_coverage_counts = {
        row["coverage_status"]: row["count"]
        for row in conn.execute(
            "SELECT coverage_status, COUNT(*) AS count FROM official_program_coverage_audit GROUP BY coverage_status"
        )
    }
    official_program_source_candidate_counts = {
        row["candidate_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT candidate_status, COUNT(*) AS count
            FROM official_program_source_candidates
            GROUP BY candidate_status
            """
        )
    }
    official_program_gap_reason_counts = {
        row["gap_reason_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT gap_reason_status, COUNT(*) AS count
            FROM official_program_gap_reason_audit
            GROUP BY gap_reason_status
            """
        )
    }
    official_gap_roster_reconciliation_counts = {
        row["denominator_link_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT denominator_link_status, COUNT(*) AS count
            FROM official_gap_roster_reconciliation
            GROUP BY denominator_link_status
            """
        )
    }
    official_gap_roster_reconciliation_extracted_counts = {
        row["denominator_link_status"]: row["records"]
        for row in conn.execute(
            """
            SELECT denominator_link_status, COALESCE(SUM(records_extracted), 0) AS records
            FROM official_gap_roster_reconciliation
            GROUP BY denominator_link_status
            """
        )
    }
    official_gap_roster_program_resolution_counts = {
        row["resolution_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT resolution_status, COUNT(*) AS count
            FROM official_gap_roster_program_resolution
            GROUP BY resolution_status
            """
        )
    }
    official_gap_roster_program_resolution_record_counts = {
        row["resolution_status"]: row["records"]
        for row in conn.execute(
            """
            SELECT resolution_status, COALESCE(SUM(records_extracted), 0) AS records
            FROM official_gap_roster_program_resolution
            GROUP BY resolution_status
            """
        )
    }
    official_program_coverage_assurance_counts = {
        row["assurance_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT assurance_status, COUNT(*) AS count
            FROM official_program_coverage_assurance_audit
            GROUP BY assurance_status
            """
        )
    }
    official_program_coverage_assurance_level_counts = {
        str(row["assurance_level"]): row["count"]
        for row in conn.execute(
            """
            SELECT assurance_level, COUNT(*) AS count
            FROM official_program_coverage_assurance_audit
            GROUP BY assurance_level
            """
        )
    }
    official_program_coverage_assurance_evidence_counts = {
        row["denominator_evidence_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT denominator_evidence_status, COUNT(*) AS count
            FROM official_program_coverage_assurance_audit
            GROUP BY denominator_evidence_status
            """
        )
    }
    official_program_coverage_action_lane_counts = {
        row["action_lane"]: row["count"]
        for row in conn.execute(
            """
            SELECT action_lane, COUNT(*) AS count
            FROM official_program_coverage_action_queue
            GROUP BY action_lane
            """
        )
    }
    official_program_coverage_action_blocker_counts = {
        row["blocker_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT blocker_status, COUNT(*) AS count
            FROM official_program_coverage_action_queue
            GROUP BY blocker_status
            """
        )
    }
    official_program_coverage_action_level_counts = {
        str(row["assurance_level"]): row["count"]
        for row in conn.execute(
            """
            SELECT assurance_level, COUNT(*) AS count
            FROM official_program_coverage_action_queue
            GROUP BY assurance_level
            """
        )
    }
    official_program_coverage_dossier_status_counts = {
        row["denominator_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT denominator_status, COUNT(*) AS count
            FROM official_program_coverage_dossiers
            GROUP BY denominator_status
            """
        )
    }
    official_program_coverage_dossier_safety_counts = {
        row["display_safety_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT display_safety_status, COUNT(*) AS count
            FROM official_program_coverage_dossiers
            GROUP BY display_safety_status
            """
        )
    }
    official_program_coverage_dossier_level_counts = {
        str(row["assurance_level"]): row["count"]
        for row in conn.execute(
            """
            SELECT assurance_level, COUNT(*) AS count
            FROM official_program_coverage_dossiers
            GROUP BY assurance_level
            """
        )
    }
    official_program_alias_review_packet_counts = {
        row["alias_decision_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT alias_decision_status, COUNT(*) AS count
            FROM official_program_alias_review_packets
            GROUP BY alias_decision_status
            """
        )
    }
    official_program_alias_review_packet_reviewer_ready_counts = {
        str(row["reviewer_ready"]): row["count"]
        for row in conn.execute(
            """
            SELECT reviewer_ready, COUNT(*) AS count
            FROM official_program_alias_review_packets
            GROUP BY reviewer_ready
            """
        )
    }
    official_program_alias_reviewer_decision_counts = {
        row["decision_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT decision_status, COUNT(*) AS count
            FROM official_program_alias_reviewer_decision_audit
            GROUP BY decision_status
            """
        )
    }
    accepted_official_program_alias_mapping_counts = {
        row["alias_decision_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT alias_decision_status, COUNT(*) AS count
            FROM accepted_official_program_alias_mappings
            GROUP BY alias_decision_status
            """
        )
    }
    official_program_alias_reconciliation_counts = {
        row["relation_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT relation_status, COUNT(*) AS count
            FROM official_program_alias_reconciliation_candidates
            GROUP BY relation_status
            """
        )
    }
    program_identifier_candidate_counts = {
        row["candidate_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT candidate_status, COUNT(*) AS count
            FROM program_identifier_candidates
            GROUP BY candidate_status
            """
        )
    }
    program_identifier_source_counts = {
        row["identifier_source"]: row["count"]
        for row in conn.execute(
            """
            SELECT identifier_source, COUNT(*) AS count
            FROM program_identifier_candidates
            GROUP BY identifier_source
            """
        )
    }
    program_identifier_reconciliation_counts = {
        row["reconciliation_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT reconciliation_status, COUNT(*) AS count
            FROM program_identifier_reconciliation
            GROUP BY reconciliation_status
            """
        )
    }
    official_program_identifier_counts = {
        row["identifier_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT identifier_type, COUNT(*) AS count
            FROM official_program_identifiers
            GROUP BY identifier_type
            """
        )
    }
    program_lifecycle_consistency_counts = {
        row["lifecycle_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT lifecycle_status, COUNT(*) AS count
            FROM program_lifecycle_consistency_audit
            GROUP BY lifecycle_status
            """
        )
    }
    program_lifecycle_duration_counts = {
        row["duration_evidence_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT duration_evidence_status, COUNT(*) AS count
            FROM program_lifecycle_duration_evidence
            GROUP BY duration_evidence_status
            """
        )
    }
    program_lifecycle_duration_source_counts = {
        row["source_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT source_status, COUNT(*) AS count
            FROM program_lifecycle_duration_source_observations
            GROUP BY source_status
            """
        )
    }
    program_lifecycle_duration_reviewer_decision_counts = {
        row["decision_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT decision_status, COUNT(*) AS count
            FROM program_lifecycle_duration_reviewer_decision_audit
            GROUP BY decision_status
            """
        )
    }
    program_lifecycle_duration_reviewer_queue_counts = {
        row["queue_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT queue_status, COUNT(*) AS count
            FROM program_lifecycle_duration_reviewer_decision_queue
            GROUP BY queue_status
            """
        )
    }
    source_utility_scorecard_counts = {
        row["quality_band"]: row["count"]
        for row in conn.execute(
            """
            SELECT quality_band, COUNT(*) AS count
            FROM source_utility_scorecard
            GROUP BY quality_band
            """
        )
    }
    person_enrichment_queue_priority_counts = {
        row["priority_band"]: row["count"]
        for row in conn.execute(
            """
            SELECT priority_band, COUNT(*) AS count
            FROM person_enrichment_work_queue
            GROUP BY priority_band
            """
        )
    }
    person_enrichment_queue_task_counts = {
        row["task_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT task_type, COUNT(*) AS count
            FROM person_enrichment_work_queue
            GROUP BY task_type
            """
        )
    }
    person_enrichment_queue_source_counts = {
        row["source_family"]: row["count"]
        for row in conn.execute(
            """
            SELECT source_family, COUNT(*) AS count
            FROM person_enrichment_work_queue
            GROUP BY source_family
            """
        )
    }
    person_enrichment_queue_policy_lane_counts = {
        row["policy_lane"] or "none": row["count"]
        for row in conn.execute(
            """
            SELECT policy_lane, COUNT(*) AS count
            FROM person_enrichment_work_queue
            GROUP BY policy_lane
            """
        )
    }
    person_enrichment_execution_lane_counts = {
        row["execution_lane"]: row["count"]
        for row in conn.execute(
            """
            SELECT execution_lane, COUNT(*) AS count
            FROM person_enrichment_execution_readiness
            GROUP BY execution_lane
            """
        )
    }
    person_enrichment_automation_status_counts = {
        row["automation_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT automation_status, COUNT(*) AS count
            FROM person_enrichment_execution_readiness
            GROUP BY automation_status
            """
        )
    }
    person_enrichment_execution_requirement_counts = {
        "requires_network": conn.execute(
            "SELECT COUNT(*) FROM person_enrichment_execution_readiness WHERE requires_network = 1"
        ).fetchone()[0],
        "requires_manual_review": conn.execute(
            "SELECT COUNT(*) FROM person_enrichment_execution_readiness WHERE requires_manual_review = 1"
        ).fetchone()[0],
        "requires_script_extension": conn.execute(
            "SELECT COUNT(*) FROM person_enrichment_execution_readiness WHERE requires_script_extension = 1"
        ).fetchone()[0],
        "requires_new_parser": conn.execute(
            "SELECT COUNT(*) FROM person_enrichment_execution_readiness WHERE requires_new_parser = 1"
        ).fetchone()[0],
    }
    person_enrichment_execution_batch_status_counts = {
        row["batch_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT batch_status, COUNT(*) AS count
            FROM person_enrichment_execution_batches
            GROUP BY batch_status
            """
        )
    }
    person_enrichment_execution_batch_task_counts = {
        row["task_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT task_type, COUNT(*) AS count
            FROM person_enrichment_execution_batches
            GROUP BY task_type
            """
        )
    }
    person_enrichment_execution_batch_lane_counts = {
        row["execution_lane"]: row["count"]
        for row in conn.execute(
            """
            SELECT execution_lane, COUNT(*) AS count
            FROM person_enrichment_execution_batches
            GROUP BY execution_lane
            """
        )
    }
    category_counts = {
        row["category"]: row["count"]
        for row in conn.execute("SELECT category, COUNT(*) AS count FROM organizations GROUP BY category")
    }
    organization_identifier_candidate_counts = {
        row["match_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT match_status, COUNT(*) AS count
            FROM organization_identifier_candidates
            GROUP BY match_status
            """
        )
    }
    medical_student_source_audit_counts = {
        row["capture_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT capture_status, COUNT(*) AS count
            FROM medical_student_source_audit
            GROUP BY capture_status
            """
        )
    }
    conn.close()
    state_machine_summary_path = ARTIFACTS / "training_state_machine_summary.json"
    if state_machine_summary_path.exists():
        state_machine_summary = json.loads(state_machine_summary_path.read_text(encoding="utf-8"))
    else:
        state_machine_summary = {}
    enrichment_coverage_summary_path = ARTIFACTS / "enrichment_coverage_summary.json"
    if enrichment_coverage_summary_path.exists():
        enrichment_coverage_summary = json.loads(enrichment_coverage_summary_path.read_text(encoding="utf-8"))
    else:
        enrichment_coverage_summary = {}
    reconciliation_decision_summary_path = ARTIFACTS / "evidence_reconciliation_decision_summary.json"
    if reconciliation_decision_summary_path.exists():
        reconciliation_decision_summary = json.loads(reconciliation_decision_summary_path.read_text(encoding="utf-8"))
    else:
        reconciliation_decision_summary = {}
    longitudinal_readiness_summary_path = ARTIFACTS / "longitudinal_change_readiness_summary.json"
    if longitudinal_readiness_summary_path.exists():
        longitudinal_readiness_summary = json.loads(longitudinal_readiness_summary_path.read_text(encoding="utf-8"))
    else:
        longitudinal_readiness_summary = {}
    training_state_snapshot_summary_path = ARTIFACTS / "training_state_snapshot_summary.json"
    if training_state_snapshot_summary_path.exists():
        training_state_snapshot_summary = json.loads(training_state_snapshot_summary_path.read_text(encoding="utf-8"))
    else:
        training_state_snapshot_summary = {}
    training_lifecycle_assurance_summary_path = ARTIFACTS / "training_lifecycle_assurance_summary.json"
    if training_lifecycle_assurance_summary_path.exists():
        training_lifecycle_assurance_summary = json.loads(
            training_lifecycle_assurance_summary_path.read_text(encoding="utf-8")
        )
    else:
        training_lifecycle_assurance_summary = {}
    training_state_transition_plan_summary_path = ARTIFACTS / "training_state_transition_plan_summary.json"
    if training_state_transition_plan_summary_path.exists():
        training_state_transition_plan_summary = json.loads(
            training_state_transition_plan_summary_path.read_text(encoding="utf-8")
        )
    else:
        training_state_transition_plan_summary = {}
    training_temporal_contract_summary_path = ARTIFACTS / "training_temporal_contract_summary.json"
    if training_temporal_contract_summary_path.exists():
        training_temporal_contract_summary = json.loads(
            training_temporal_contract_summary_path.read_text(encoding="utf-8")
        )
    else:
        training_temporal_contract_summary = {}
    trainee_profile_discovery_summary_path = ARTIFACTS / "trainee_profile_discovery_summary.json"
    if trainee_profile_discovery_summary_path.exists():
        trainee_profile_discovery_summary = json.loads(
            trainee_profile_discovery_summary_path.read_text(encoding="utf-8")
        )
    else:
        trainee_profile_discovery_summary = {}
    prior_training_discovery_summary_path = ARTIFACTS / "prior_training_discovery_summary.json"
    if prior_training_discovery_summary_path.exists():
        prior_training_discovery_summary = json.loads(
            prior_training_discovery_summary_path.read_text(encoding="utf-8")
        )
    else:
        prior_training_discovery_summary = {}
    attending_trend_linkage_summary_path = ARTIFACTS / "attending_trend_linkage_summary.json"
    if attending_trend_linkage_summary_path.exists():
        attending_trend_linkage_summary = json.loads(attending_trend_linkage_summary_path.read_text(encoding="utf-8"))
    else:
        attending_trend_linkage_summary = {}
    attending_historical_link_summary_path = ARTIFACTS / "attending_historical_link_discovery_summary.json"
    if attending_historical_link_summary_path.exists():
        attending_historical_link_summary = json.loads(
            attending_historical_link_summary_path.read_text(encoding="utf-8")
        )
    else:
        attending_historical_link_summary = {}
    attending_biosketch_bridge_summary_path = ARTIFACTS / "attending_biosketch_bridge_summary.json"
    if attending_biosketch_bridge_summary_path.exists():
        attending_biosketch_bridge_summary = json.loads(
            attending_biosketch_bridge_summary_path.read_text(encoding="utf-8")
        )
    else:
        attending_biosketch_bridge_summary = {}
    attending_trend_reconciliation_summary_path = ARTIFACTS / "attending_trend_reconciliation_summary.json"
    if attending_trend_reconciliation_summary_path.exists():
        attending_trend_reconciliation_summary = json.loads(
            attending_trend_reconciliation_summary_path.read_text(encoding="utf-8")
        )
    else:
        attending_trend_reconciliation_summary = {}
    attending_trend_review_claims_summary_path = ARTIFACTS / "attending_trend_review_claims_summary.json"
    if attending_trend_review_claims_summary_path.exists():
        attending_trend_review_claims_summary = json.loads(
            attending_trend_review_claims_summary_path.read_text(encoding="utf-8")
        )
    else:
        attending_trend_review_claims_summary = {}
    attending_trend_acceptance_summary_path = ARTIFACTS / "attending_trend_acceptance_summary.json"
    if attending_trend_acceptance_summary_path.exists():
        attending_trend_acceptance_summary = json.loads(
            attending_trend_acceptance_summary_path.read_text(encoding="utf-8")
        )
    else:
        attending_trend_acceptance_summary = {}
    attending_trend_reviewer_decision_summary_path = ARTIFACTS / "attending_trend_reviewer_decision_summary.json"
    if attending_trend_reviewer_decision_summary_path.exists():
        attending_trend_reviewer_decision_summary = json.loads(
            attending_trend_reviewer_decision_summary_path.read_text(encoding="utf-8")
        )
    else:
        attending_trend_reviewer_decision_summary = {}
    attending_trend_dossier_summary_path = ARTIFACTS / "attending_trend_dossier_summary.json"
    if attending_trend_dossier_summary_path.exists():
        attending_trend_dossier_summary = json.loads(
            attending_trend_dossier_summary_path.read_text(encoding="utf-8")
        )
    else:
        attending_trend_dossier_summary = {}
    npi_candidate_summary_path = ARTIFACTS / "npi_candidate_summary.json"
    if npi_candidate_summary_path.exists():
        npi_candidate_summary = json.loads(npi_candidate_summary_path.read_text(encoding="utf-8"))
    else:
        npi_candidate_summary = {}
    person_evidence_packet_summary_path = ARTIFACTS / "person_evidence_review_packet_summary.json"
    if person_evidence_packet_summary_path.exists():
        person_evidence_packet_summary = json.loads(person_evidence_packet_summary_path.read_text(encoding="utf-8"))
    else:
        person_evidence_packet_summary = {}
    enrichment_acceptance_summary_path = ARTIFACTS / "enrichment_acceptance_summary.json"
    if enrichment_acceptance_summary_path.exists():
        enrichment_acceptance_summary = json.loads(enrichment_acceptance_summary_path.read_text(encoding="utf-8"))
    else:
        enrichment_acceptance_summary = {}
    accepted_enrichment_summary_path = ARTIFACTS / "accepted_enrichment_summary.json"
    if accepted_enrichment_summary_path.exists():
        accepted_enrichment_summary = json.loads(accepted_enrichment_summary_path.read_text(encoding="utf-8"))
    else:
        accepted_enrichment_summary = {}
    contact_assurance_summary_path = ARTIFACTS / "contact_assurance_summary.json"
    if contact_assurance_summary_path.exists():
        contact_assurance_summary = json.loads(contact_assurance_summary_path.read_text(encoding="utf-8"))
    else:
        contact_assurance_summary = {}
    contact_verification_contract_summary_path = ARTIFACTS / "contact_verification_contract_summary.json"
    if contact_verification_contract_summary_path.exists():
        contact_verification_contract_summary = json.loads(
            contact_verification_contract_summary_path.read_text(encoding="utf-8")
        )
    else:
        contact_verification_contract_summary = {}
    contact_reviewer_decision_summary_path = ARTIFACTS / "contact_verification_reviewer_decision_summary.json"
    if contact_reviewer_decision_summary_path.exists():
        contact_reviewer_decision_summary = json.loads(
            contact_reviewer_decision_summary_path.read_text(encoding="utf-8")
        )
    else:
        contact_reviewer_decision_summary = {}
    person_enrichment_dossier_summary_path = ARTIFACTS / "person_enrichment_dossier_summary.json"
    if person_enrichment_dossier_summary_path.exists():
        person_enrichment_dossier_summary = json.loads(
            person_enrichment_dossier_summary_path.read_text(encoding="utf-8")
        )
    else:
        person_enrichment_dossier_summary = {}
    person_enrichment_execution_readiness_summary_path = ARTIFACTS / "person_enrichment_execution_readiness_summary.json"
    if person_enrichment_execution_readiness_summary_path.exists():
        person_enrichment_execution_readiness_summary = json.loads(
            person_enrichment_execution_readiness_summary_path.read_text(encoding="utf-8")
        )
    else:
        person_enrichment_execution_readiness_summary = {}
    person_enrichment_execution_batch_summary_path = ARTIFACTS / "person_enrichment_execution_batch_summary.json"
    if person_enrichment_execution_batch_summary_path.exists():
        person_enrichment_execution_batch_summary = json.loads(
            person_enrichment_execution_batch_summary_path.read_text(encoding="utf-8")
        )
    else:
        person_enrichment_execution_batch_summary = {}
    warehouse_reproducibility_summary_path = ARTIFACTS / "warehouse_reproducibility_summary.json"
    if warehouse_reproducibility_summary_path.exists():
        warehouse_reproducibility_summary = json.loads(
            warehouse_reproducibility_summary_path.read_text(encoding="utf-8")
        )
    else:
        warehouse_reproducibility_summary = {}
    source_utility_scorecard_summary_path = ARTIFACTS / "source_utility_scorecard_summary.json"
    if source_utility_scorecard_summary_path.exists():
        source_utility_scorecard_summary = json.loads(source_utility_scorecard_summary_path.read_text(encoding="utf-8"))
    else:
        source_utility_scorecard_summary = {}
    corpus_action_worklist_summary_path = ARTIFACTS / "corpus_action_worklist_summary.json"
    if corpus_action_worklist_summary_path.exists():
        corpus_action_worklist_summary = json.loads(corpus_action_worklist_summary_path.read_text(encoding="utf-8"))
    else:
        corpus_action_worklist_summary = {}
    organization_identifier_candidate_summary_path = ARTIFACTS / "organization_identifier_candidate_summary.json"
    if organization_identifier_candidate_summary_path.exists():
        organization_identifier_candidate_summary = json.loads(
            organization_identifier_candidate_summary_path.read_text(encoding="utf-8")
        )
    else:
        organization_identifier_candidate_summary = {}
    medical_student_source_audit_summary_path = ARTIFACTS / "penn_med_student_source_audit_summary.json"
    if medical_student_source_audit_summary_path.exists():
        medical_student_source_audit_summary = json.loads(
            medical_student_source_audit_summary_path.read_text(encoding="utf-8")
        )
    else:
        medical_student_source_audit_summary = {}
    program_identifier_candidate_summary_path = ARTIFACTS / "program_identifier_candidate_summary.json"
    if program_identifier_candidate_summary_path.exists():
        program_identifier_candidate_summary = json.loads(
            program_identifier_candidate_summary_path.read_text(encoding="utf-8")
        )
    else:
        program_identifier_candidate_summary = {}
    program_identifier_reconciliation_summary_path = ARTIFACTS / "program_identifier_reconciliation_summary.json"
    if program_identifier_reconciliation_summary_path.exists():
        program_identifier_reconciliation_summary = json.loads(
            program_identifier_reconciliation_summary_path.read_text(encoding="utf-8")
        )
    else:
        program_identifier_reconciliation_summary = {}
    program_lifecycle_consistency_summary_path = ARTIFACTS / "program_lifecycle_consistency_summary.json"
    if program_lifecycle_consistency_summary_path.exists():
        program_lifecycle_consistency_summary = json.loads(
            program_lifecycle_consistency_summary_path.read_text(encoding="utf-8")
        )
    else:
        program_lifecycle_consistency_summary = {}
    program_lifecycle_duration_summary_path = ARTIFACTS / "program_lifecycle_duration_evidence_summary.json"
    if program_lifecycle_duration_summary_path.exists():
        program_lifecycle_duration_summary = json.loads(
            program_lifecycle_duration_summary_path.read_text(encoding="utf-8")
        )
    else:
        program_lifecycle_duration_summary = {}
    program_lifecycle_duration_reviewer_decision_summary_path = (
        ARTIFACTS / "program_lifecycle_duration_reviewer_decision_summary.json"
    )
    if program_lifecycle_duration_reviewer_decision_summary_path.exists():
        program_lifecycle_duration_reviewer_decision_summary = json.loads(
            program_lifecycle_duration_reviewer_decision_summary_path.read_text(encoding="utf-8")
        )
    else:
        program_lifecycle_duration_reviewer_decision_summary = {}
    official_gap_roster_reconciliation_summary_path = ARTIFACTS / "official_gap_roster_reconciliation_summary.json"
    if official_gap_roster_reconciliation_summary_path.exists():
        official_gap_roster_reconciliation_summary = json.loads(
            official_gap_roster_reconciliation_summary_path.read_text(encoding="utf-8")
        )
    else:
        official_gap_roster_reconciliation_summary = {}
    official_gap_roster_program_resolution_summary_path = ARTIFACTS / "official_gap_roster_program_resolution_summary.json"
    if official_gap_roster_program_resolution_summary_path.exists():
        official_gap_roster_program_resolution_summary = json.loads(
            official_gap_roster_program_resolution_summary_path.read_text(encoding="utf-8")
        )
    else:
        official_gap_roster_program_resolution_summary = {}
    official_program_coverage_assurance_summary_path = ARTIFACTS / "official_program_coverage_assurance_summary.json"
    if official_program_coverage_assurance_summary_path.exists():
        official_program_coverage_assurance_summary = json.loads(
            official_program_coverage_assurance_summary_path.read_text(encoding="utf-8")
        )
    else:
        official_program_coverage_assurance_summary = {}
    official_program_coverage_action_queue_summary_path = ARTIFACTS / "official_program_coverage_action_queue_summary.json"
    if official_program_coverage_action_queue_summary_path.exists():
        official_program_coverage_action_queue_summary = json.loads(
            official_program_coverage_action_queue_summary_path.read_text(encoding="utf-8")
        )
    else:
        official_program_coverage_action_queue_summary = {}
    official_program_coverage_dossier_summary_path = ARTIFACTS / "official_program_coverage_dossier_summary.json"
    if official_program_coverage_dossier_summary_path.exists():
        official_program_coverage_dossier_summary = json.loads(
            official_program_coverage_dossier_summary_path.read_text(encoding="utf-8")
        )
    else:
        official_program_coverage_dossier_summary = {}
    official_program_alias_review_packets_summary_path = ARTIFACTS / "official_program_alias_review_packets_summary.json"
    if official_program_alias_review_packets_summary_path.exists():
        official_program_alias_review_packets_summary = json.loads(
            official_program_alias_review_packets_summary_path.read_text(encoding="utf-8")
        )
    else:
        official_program_alias_review_packets_summary = {}
    official_program_alias_reviewer_decision_summary_path = ARTIFACTS / "official_program_alias_reviewer_decision_summary.json"
    if official_program_alias_reviewer_decision_summary_path.exists():
        official_program_alias_reviewer_decision_summary = json.loads(
            official_program_alias_reviewer_decision_summary_path.read_text(encoding="utf-8")
        )
    else:
        official_program_alias_reviewer_decision_summary = {}
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": str(DB.relative_to(ROOT)),
        "counts": counts,
        "resolver_counts": resolver_counts,
        "role_counts": role_counts,
        "generic_program_label_count": generic_program_label_count,
        "training_state_family_counts": training_state_family_counts,
        "normalized_stage_counts": normalized_stage_counts,
        "lifecycle_code_counts": lifecycle_code_counts,
        "expected_transition_type_counts": expected_transition_type_counts,
        "stale_by_next_august_count": stale_by_next_august_count,
        "evidence_status_counts": evidence_status_counts,
        "evidence_source_counts": evidence_source_counts,
        "career_event_counts": career_event_counts,
        "attending_biosketch_bridge_counts": attending_biosketch_bridge_counts,
        "attending_trend_reconciliation_counts": attending_trend_reconciliation_counts,
        "attending_trend_review_claim_counts": attending_trend_review_claim_counts,
        "attending_trend_acceptance_counts": attending_trend_acceptance_counts,
        "attending_trend_acceptance_fact_counts": attending_trend_acceptance_fact_counts,
        "attending_trend_reviewer_decision_counts": attending_trend_reviewer_decision_counts,
        "accepted_attending_trend_fact_counts": accepted_attending_trend_fact_counts,
        "attending_trend_dossier_status_counts": attending_trend_dossier_status_counts,
        "attending_trend_dossier_safety_counts": attending_trend_dossier_safety_counts,
        "attending_trend_review_end_year_counts": attending_trend_review_end_year_counts,
        "attending_trend_review_rollup_scope_counts": attending_trend_review_rollup_scope_counts,
        "npi_candidate_counts": npi_candidate_counts,
        "npi_primary_taxonomy_counts": npi_primary_taxonomy_counts,
        "evidence_reconciliation_queue_counts": evidence_reconciliation_queue_counts,
        "evidence_reconciliation_top_claim_counts": evidence_reconciliation_top_claim_counts,
        "evidence_reconciliation_decision_counts": evidence_reconciliation_decision_counts,
        "person_reconciliation_decision_counts": person_reconciliation_decision_counts,
        "person_evidence_review_packet_counts": person_evidence_review_packet_counts,
        "enrichment_acceptance_counts": enrichment_acceptance_counts,
        "accepted_enrichment_counts": accepted_enrichment_counts,
        "accepted_enrichment_role_counts": accepted_enrichment_role_counts,
        "warehouse_reproducibility_counts": warehouse_reproducibility_counts,
        "state_machine_status_counts": state_machine_status_counts,
        "training_state_transition_rollup_scope_counts": transition_rollup_scope_counts,
        "refresh_readiness_counts": refresh_readiness_counts,
        "lifecycle_assurance_counts": lifecycle_assurance_counts,
        "lifecycle_assurance_diff_counts": lifecycle_assurance_diff_counts,
        "transition_plan_policy_counts": transition_plan_policy_counts,
        "transition_plan_diff_counts": transition_plan_diff_counts,
        "transition_plan_rollup_scope_counts": transition_plan_rollup_scope_counts,
        "temporal_contract_counts": temporal_contract_counts,
        "temporal_contract_state_counts": temporal_contract_state_counts,
        "temporal_contract_guardrail_counts": temporal_contract_guardrail_counts,
        "temporal_contract_rollup_scope_counts": temporal_contract_rollup_scope_counts,
        "trainee_profile_discovery_candidate_counts": trainee_profile_discovery_candidate_counts,
        "trainee_profile_search_status_counts": trainee_profile_search_status_counts,
        "prior_training_discovery_candidate_counts": prior_training_discovery_candidate_counts,
        "prior_training_search_status_counts": prior_training_search_status_counts,
        "person_dossier_status_counts": person_dossier_status_counts,
        "person_dossier_display_safety_counts": person_dossier_display_safety_counts,
        "contact_counts": contact_counts,
        "contact_assurance_counts": contact_assurance_counts,
        "contact_display_safety_counts": contact_display_safety_counts,
        "contact_verification_lane_counts": contact_verification_lane_counts,
        "contact_operational_use_counts": contact_operational_use_counts,
        "contact_reviewer_decision_counts": contact_reviewer_decision_counts,
        "contact_reviewer_queue_counts": contact_reviewer_queue_counts,
        "accepted_verified_contact_counts": accepted_contact_counts,
        "official_program_coverage_counts": official_program_coverage_counts,
        "official_program_source_candidate_counts": official_program_source_candidate_counts,
        "official_program_gap_reason_counts": official_program_gap_reason_counts,
        "official_gap_roster_reconciliation_counts": official_gap_roster_reconciliation_counts,
        "official_gap_roster_reconciliation_extracted_counts": official_gap_roster_reconciliation_extracted_counts,
        "official_gap_roster_program_resolution_counts": official_gap_roster_program_resolution_counts,
        "official_gap_roster_program_resolution_record_counts": official_gap_roster_program_resolution_record_counts,
        "official_program_coverage_assurance_counts": official_program_coverage_assurance_counts,
        "official_program_coverage_assurance_level_counts": official_program_coverage_assurance_level_counts,
        "official_program_coverage_assurance_evidence_counts": official_program_coverage_assurance_evidence_counts,
        "official_program_coverage_action_lane_counts": official_program_coverage_action_lane_counts,
        "official_program_coverage_action_blocker_counts": official_program_coverage_action_blocker_counts,
        "official_program_coverage_action_level_counts": official_program_coverage_action_level_counts,
        "official_program_coverage_dossier_status_counts": official_program_coverage_dossier_status_counts,
        "official_program_coverage_dossier_safety_counts": official_program_coverage_dossier_safety_counts,
        "official_program_coverage_dossier_level_counts": official_program_coverage_dossier_level_counts,
        "official_program_alias_review_packet_counts": official_program_alias_review_packet_counts,
        "official_program_alias_review_packet_reviewer_ready_counts": official_program_alias_review_packet_reviewer_ready_counts,
        "official_program_alias_reviewer_decision_counts": official_program_alias_reviewer_decision_counts,
        "accepted_official_program_alias_mapping_counts": accepted_official_program_alias_mapping_counts,
        "official_program_alias_reconciliation_counts": official_program_alias_reconciliation_counts,
        "program_identifier_candidate_counts": program_identifier_candidate_counts,
        "program_identifier_source_counts": program_identifier_source_counts,
        "program_identifier_reconciliation_counts": program_identifier_reconciliation_counts,
        "official_program_identifier_counts": official_program_identifier_counts,
        "program_lifecycle_consistency_counts": program_lifecycle_consistency_counts,
        "program_lifecycle_duration_counts": program_lifecycle_duration_counts,
        "program_lifecycle_duration_source_counts": program_lifecycle_duration_source_counts,
        "program_lifecycle_duration_reviewer_decision_counts": program_lifecycle_duration_reviewer_decision_counts,
        "program_lifecycle_duration_reviewer_queue_counts": program_lifecycle_duration_reviewer_queue_counts,
        "source_utility_scorecard_counts": source_utility_scorecard_counts,
        "person_enrichment_queue_priority_counts": person_enrichment_queue_priority_counts,
        "person_enrichment_queue_task_counts": person_enrichment_queue_task_counts,
        "person_enrichment_queue_source_counts": person_enrichment_queue_source_counts,
        "person_enrichment_queue_policy_lane_counts": person_enrichment_queue_policy_lane_counts,
        "person_enrichment_execution_lane_counts": person_enrichment_execution_lane_counts,
        "person_enrichment_automation_status_counts": person_enrichment_automation_status_counts,
        "person_enrichment_execution_requirement_counts": person_enrichment_execution_requirement_counts,
        "person_enrichment_execution_batch_status_counts": person_enrichment_execution_batch_status_counts,
        "person_enrichment_execution_batch_task_counts": person_enrichment_execution_batch_task_counts,
        "person_enrichment_execution_batch_lane_counts": person_enrichment_execution_batch_lane_counts,
        "organization_identifier_candidate_counts": organization_identifier_candidate_counts,
        "medical_student_source_audit_counts": medical_student_source_audit_counts,
        "organization_category_counts": category_counts,
        "training_state_machine_summary": state_machine_summary,
        "enrichment_coverage_summary": enrichment_coverage_summary,
        "evidence_reconciliation_decision_summary": reconciliation_decision_summary,
        "longitudinal_change_readiness_summary": longitudinal_readiness_summary,
        "training_state_snapshot_summary": training_state_snapshot_summary,
        "training_lifecycle_assurance_summary": training_lifecycle_assurance_summary,
        "training_state_transition_plan_summary": training_state_transition_plan_summary,
        "training_temporal_contract_summary": training_temporal_contract_summary,
        "trainee_profile_discovery_summary": trainee_profile_discovery_summary,
        "prior_training_discovery_summary": prior_training_discovery_summary,
        "attending_trend_linkage_summary": attending_trend_linkage_summary,
        "attending_historical_link_discovery_summary": attending_historical_link_summary,
        "attending_biosketch_bridge_summary": attending_biosketch_bridge_summary,
        "attending_trend_reconciliation_summary": attending_trend_reconciliation_summary,
        "attending_trend_review_claims_summary": attending_trend_review_claims_summary,
        "attending_trend_acceptance_summary": attending_trend_acceptance_summary,
        "attending_trend_reviewer_decision_summary": attending_trend_reviewer_decision_summary,
        "attending_trend_dossier_summary": attending_trend_dossier_summary,
        "npi_candidate_summary": npi_candidate_summary,
        "person_evidence_review_packet_summary": person_evidence_packet_summary,
        "enrichment_acceptance_summary": enrichment_acceptance_summary,
        "accepted_enrichment_summary": accepted_enrichment_summary,
        "contact_assurance_summary": contact_assurance_summary,
        "contact_verification_contract_summary": contact_verification_contract_summary,
        "contact_verification_reviewer_decision_summary": contact_reviewer_decision_summary,
        "person_enrichment_dossier_summary": person_enrichment_dossier_summary,
        "person_enrichment_execution_readiness_summary": person_enrichment_execution_readiness_summary,
        "person_enrichment_execution_batch_summary": person_enrichment_execution_batch_summary,
        "warehouse_reproducibility_summary": warehouse_reproducibility_summary,
        "source_utility_scorecard_summary": source_utility_scorecard_summary,
        "corpus_action_worklist_summary": corpus_action_worklist_summary,
        "organization_identifier_candidate_summary": organization_identifier_candidate_summary,
        "medical_student_source_audit_summary": medical_student_source_audit_summary,
        "program_identifier_candidate_summary": program_identifier_candidate_summary,
        "program_identifier_reconciliation_summary": program_identifier_reconciliation_summary,
        "program_lifecycle_consistency_summary": program_lifecycle_consistency_summary,
        "program_lifecycle_duration_summary": program_lifecycle_duration_summary,
        "program_lifecycle_duration_reviewer_decision_summary": program_lifecycle_duration_reviewer_decision_summary,
        "official_gap_roster_reconciliation_summary": official_gap_roster_reconciliation_summary,
        "official_gap_roster_program_resolution_summary": official_gap_roster_program_resolution_summary,
        "official_program_coverage_assurance_summary": official_program_coverage_assurance_summary,
        "official_program_coverage_action_queue_summary": official_program_coverage_action_queue_summary,
        "official_program_coverage_dossier_summary": official_program_coverage_dossier_summary,
        "official_program_alias_review_packets_summary": official_program_alias_review_packets_summary,
        "official_program_alias_reviewer_decision_summary": official_program_alias_reviewer_decision_summary,
    }
    (ARTIFACTS / "warehouse_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
