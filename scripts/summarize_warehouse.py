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
        "training_state_snapshots",
        "training_state_snapshot_rows",
        "training_state_transition_events",
        "training_state_transition_rollups",
        "training_state_machine_audit",
        "person_training_state_machine_audit",
        "program_training_state_machine_audit",
        "training_state_refresh_expectations",
        "person_refresh_expectations",
        "program_refresh_expectations",
        "category_refresh_expectations",
        "training_lifecycle_assurance_rollups",
        "career_events",
        "attending_biosketch_bridge_candidates",
        "attending_trend_reconciliation",
        "attending_trend_review_claims",
        "attending_trend_review_rollups",
        "npi_candidate_claims",
        "npi_source_observations",
        "person_contacts",
        "evidence_claims",
        "evidence_reconciliation_decisions",
        "person_reconciliation_decisions",
        "enrichment_acceptance_audit",
        "accepted_enrichment_claims",
        "warehouse_reproducibility_audit",
        "source_quality_observations",
        "source_utility_scorecard",
        "official_program_universe",
        "official_program_coverage_audit",
        "official_program_source_probes",
        "official_program_source_candidates",
        "official_program_gap_reason_audit",
        "official_gap_roster_reconciliation",
        "official_program_alias_reconciliation_candidates",
        "program_identifier_source_observations",
        "program_identifier_candidates",
        "program_identifier_reconciliation",
        "official_program_identifiers",
        "program_lifecycle_consistency_audit",
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
    contact_counts = {
        row["contact_type"]: row["count"]
        for row in conn.execute("SELECT contact_type, COUNT(*) AS count FROM person_contacts GROUP BY contact_type")
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
    official_gap_roster_reconciliation_summary_path = ARTIFACTS / "official_gap_roster_reconciliation_summary.json"
    if official_gap_roster_reconciliation_summary_path.exists():
        official_gap_roster_reconciliation_summary = json.loads(
            official_gap_roster_reconciliation_summary_path.read_text(encoding="utf-8")
        )
    else:
        official_gap_roster_reconciliation_summary = {}
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
        "contact_counts": contact_counts,
        "official_program_coverage_counts": official_program_coverage_counts,
        "official_program_source_candidate_counts": official_program_source_candidate_counts,
        "official_program_gap_reason_counts": official_program_gap_reason_counts,
        "official_gap_roster_reconciliation_counts": official_gap_roster_reconciliation_counts,
        "official_gap_roster_reconciliation_extracted_counts": official_gap_roster_reconciliation_extracted_counts,
        "official_program_alias_reconciliation_counts": official_program_alias_reconciliation_counts,
        "program_identifier_candidate_counts": program_identifier_candidate_counts,
        "program_identifier_source_counts": program_identifier_source_counts,
        "program_identifier_reconciliation_counts": program_identifier_reconciliation_counts,
        "official_program_identifier_counts": official_program_identifier_counts,
        "program_lifecycle_consistency_counts": program_lifecycle_consistency_counts,
        "source_utility_scorecard_counts": source_utility_scorecard_counts,
        "organization_identifier_candidate_counts": organization_identifier_candidate_counts,
        "medical_student_source_audit_counts": medical_student_source_audit_counts,
        "organization_category_counts": category_counts,
        "training_state_machine_summary": state_machine_summary,
        "enrichment_coverage_summary": enrichment_coverage_summary,
        "evidence_reconciliation_decision_summary": reconciliation_decision_summary,
        "longitudinal_change_readiness_summary": longitudinal_readiness_summary,
        "training_state_snapshot_summary": training_state_snapshot_summary,
        "training_lifecycle_assurance_summary": training_lifecycle_assurance_summary,
        "attending_trend_linkage_summary": attending_trend_linkage_summary,
        "attending_historical_link_discovery_summary": attending_historical_link_summary,
        "attending_biosketch_bridge_summary": attending_biosketch_bridge_summary,
        "attending_trend_reconciliation_summary": attending_trend_reconciliation_summary,
        "attending_trend_review_claims_summary": attending_trend_review_claims_summary,
        "npi_candidate_summary": npi_candidate_summary,
        "person_evidence_review_packet_summary": person_evidence_packet_summary,
        "enrichment_acceptance_summary": enrichment_acceptance_summary,
        "accepted_enrichment_summary": accepted_enrichment_summary,
        "warehouse_reproducibility_summary": warehouse_reproducibility_summary,
        "source_utility_scorecard_summary": source_utility_scorecard_summary,
        "organization_identifier_candidate_summary": organization_identifier_candidate_summary,
        "medical_student_source_audit_summary": medical_student_source_audit_summary,
        "program_identifier_candidate_summary": program_identifier_candidate_summary,
        "program_identifier_reconciliation_summary": program_identifier_reconciliation_summary,
        "program_lifecycle_consistency_summary": program_lifecycle_consistency_summary,
        "official_gap_roster_reconciliation_summary": official_gap_roster_reconciliation_summary,
    }
    (ARTIFACTS / "warehouse_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
