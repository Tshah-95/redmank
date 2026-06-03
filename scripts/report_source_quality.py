#!/usr/bin/env python3
"""Render source-quality learnings from the warehouse."""

from __future__ import annotations

import json
import sqlite3
import csv
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
REPORTS = ROOT / "artifacts" / "research"
DB = ARTIFACTS / "redmank.sqlite"


def rows(conn: sqlite3.Connection, query: str):
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def md_table(items: list[dict], columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for item in items:
        lines.append("| " + " | ".join(str(item.get(col, "")).replace("|", "\\|") for col in columns) + " |")
    return lines


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path, limit: int | None = None) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        data = list(csv.DictReader(f))
    return data[:limit] if limit else data


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    source_counts = rows(
        conn,
        """
        SELECT source_type, classification, COUNT(*) AS count
        FROM sources
        GROUP BY source_type, classification
        ORDER BY source_type, classification
        """,
    )
    evidence_counts = rows(
        conn,
        """
        SELECT source_key, status, claim_type, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        GROUP BY source_key, status, claim_type
        ORDER BY source_key, status, claim_type
        """,
    )
    utility_observations = rows(
        conn,
        """
        SELECT utility_key, sample_size, candidate_claims, accepted_claims,
               rejected_claims, ambiguous_claims, metrics_json
        FROM source_quality_observations
        ORDER BY utility_key
        """,
    )
    openalex_features = rows(
        conn,
        """
        SELECT match_features_json, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_key = 'openalex_author_search'
        GROUP BY match_features_json
        ORDER BY count DESC
        LIMIT 20
        """,
    )
    orcid_features = rows(
        conn,
        """
        SELECT match_features_json, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_key = 'orcid_public_api'
          AND claim_type = 'orcid_profile_candidate'
        GROUP BY match_features_json
        ORDER BY count DESC
        LIMIT 20
        """,
    )
    orcid_work_features = rows(
        conn,
        """
        SELECT match_features_json, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_key = 'orcid_public_api'
          AND claim_type = 'orcid_work_candidate'
        GROUP BY match_features_json
        ORDER BY count DESC
        LIMIT 20
        """,
    )
    pubmed_features = rows(
        conn,
        """
        SELECT match_features_json, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'pubmed_author_query_candidate'
        GROUP BY match_features_json
        ORDER BY count DESC
        """,
    )
    pubmed_article_features = rows(
        conn,
        """
        SELECT match_features_json, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'pubmed_article_candidate'
        GROUP BY match_features_json
        ORDER BY count DESC
        LIMIT 30
        """,
    )
    orcid_pubmed_article_features = rows(
        conn,
        """
        SELECT match_features_json, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'orcid_pubmed_article_candidate'
        GROUP BY match_features_json
        ORDER BY count DESC
        LIMIT 30
        """,
    )
    trainee_profile_counts = rows(
        conn,
        """
        SELECT status, claim_type, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_type = 'official_trainee_profile'
        GROUP BY status, claim_type
        ORDER BY status, claim_type
        """,
    )
    trainee_profile_safety_counts = rows(
        conn,
        """
        SELECT json_extract(evidence_json, '$.display_safety_status') AS display_safety_status,
               COUNT(*) AS count
        FROM evidence_claims
        WHERE source_type = 'official_trainee_profile'
        GROUP BY display_safety_status
        ORDER BY count DESC, display_safety_status
        """,
    )
    broad_discovery = rows(
        conn,
        """
        SELECT classification, COUNT(*) AS count
        FROM sources
        WHERE source_type = 'penn_affiliated_source_discovery'
        GROUP BY classification
        ORDER BY count DESC
        """,
    )
    career_events = rows(
        conn,
        """
        SELECT event_type, status, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM career_events
        GROUP BY event_type, status
        ORDER BY event_type, status
        """,
    )
    broad_program_counts = rows(
        conn,
        """
        SELECT pr.program_name, p.role, COUNT(*) AS count
        FROM person_program_memberships m
        JOIN programs pr ON pr.program_key = m.program_key
        JOIN people p ON p.person_key = m.person_key
        WHERE m.population = 'penn_affiliated_current_trainees'
        GROUP BY pr.program_name, p.role
        ORDER BY count DESC, pr.program_name, p.role
        LIMIT 40
        """,
    )
    generic_program_labels = rows(
        conn,
        """
        SELECT pr.program_name, COUNT(*) AS count
        FROM person_program_memberships m
        JOIN programs pr ON pr.program_key = m.program_key
        WHERE pr.program_name IN ('Residents', 'Fellows')
        GROUP BY pr.program_name
        ORDER BY pr.program_name
        """,
    )
    training_state_counts = rows(
        conn,
        """
        SELECT stage_family, normalized_stage, status, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM person_training_states
        GROUP BY stage_family, normalized_stage, status
        ORDER BY stage_family, normalized_stage, status
        """,
    )
    transition_rule_counts = rows(
        conn,
        """
        SELECT transition_rule, COUNT(*) AS count
        FROM person_training_states
        GROUP BY transition_rule
        ORDER BY count DESC, transition_rule
        """,
    )
    lifecycle_code_counts = rows(
        conn,
        """
        SELECT lifecycle_code, expected_transition_type, refresh_policy,
               COUNT(*) AS count, ROUND(AVG(confidence), 3) AS avg_confidence
        FROM person_training_states
        GROUP BY lifecycle_code, expected_transition_type, refresh_policy
        ORDER BY lifecycle_code, expected_transition_type, refresh_policy
        """,
    )
    contact_counts = rows(
        conn,
        """
        SELECT contact_type, contact_scope, verification_status, status,
               COUNT(*) AS count, ROUND(AVG(confidence), 3) AS avg_confidence
        FROM person_contacts
        GROUP BY contact_type, contact_scope, verification_status, status
        ORDER BY contact_type, contact_scope, verification_status, status
        """,
    )
    contact_assurance_counts = rows(
        conn,
        """
        SELECT assurance_status, display_safety_status, required_next_check,
               COUNT(*) AS count, ROUND(AVG(confidence), 3) AS avg_confidence
        FROM contact_assurance_audit
        GROUP BY assurance_status, display_safety_status, required_next_check
        ORDER BY count DESC, assurance_status
        """,
    )
    contact_reviewer_decision_counts = rows(
        conn,
        """
        SELECT decision_status, reviewer_decision, COUNT(*) AS count
        FROM contact_verification_reviewer_decision_audit
        GROUP BY decision_status, reviewer_decision
        ORDER BY count DESC, decision_status, reviewer_decision
        """,
    )
    accepted_contact_counts = rows(
        conn,
        """
        SELECT contact_type, display_safety_status, operational_use_status, COUNT(*) AS count
        FROM accepted_verified_contact_facts
        GROUP BY contact_type, display_safety_status, operational_use_status
        ORDER BY count DESC, contact_type
        """,
    )
    reconciliation_queue_counts = rows(
        conn,
        """
        SELECT record_type, status, claim_type, COUNT(*) AS count,
               ROUND(AVG(priority), 1) AS avg_priority,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM v_evidence_reconciliation_queue
        GROUP BY record_type, status, claim_type
        ORDER BY avg_priority DESC, count DESC, record_type, status, claim_type
        LIMIT 40
        """,
    )
    top_reconciliation_queue = rows(
        conn,
        """
        SELECT record_type, display_name, role, claim_type, status, confidence,
               priority, source_key, source_url, review_action
        FROM v_evidence_reconciliation_queue
        ORDER BY priority DESC, confidence DESC, display_name
        LIMIT 30
        """,
    )
    conn.close()
    hup_coverage_summary = read_json(ARTIFACTS / "penn_gme_program_coverage_summary.json", {})
    hup_coverage_rows = read_json(ARTIFACTS / "penn_gme_program_coverage.json", [])
    hup_gap_probe_summary = read_json(ARTIFACTS / "penn_gme_gap_source_probe_summary.json", {})
    hup_gap_candidates = read_json(ARTIFACTS / "penn_gme_gap_source_candidates.json", [])
    hup_gap_roster_summary = read_json(ARTIFACTS / "penn_gme_gap_roster_summary.json", {})
    official_gap_roster_reconciliation_summary = read_json(
        ARTIFACTS / "official_gap_roster_reconciliation_summary.json",
        {},
    )
    official_gap_roster_program_resolution_summary = read_json(
        ARTIFACTS / "official_gap_roster_program_resolution_summary.json",
        {},
    )
    official_program_coverage_assurance_summary = read_json(
        ARTIFACTS / "official_program_coverage_assurance_summary.json",
        {},
    )
    official_program_coverage_action_queue_summary = read_json(
        ARTIFACTS / "official_program_coverage_action_queue_summary.json",
        {},
    )
    official_program_alias_review_packets_summary = read_json(
        ARTIFACTS / "official_program_alias_review_packets_summary.json",
        {},
    )
    official_program_alias_reviewer_decision_summary = read_json(
        ARTIFACTS / "official_program_alias_reviewer_decision_summary.json",
        {},
    )
    pubmed_article_summary = read_json(ARTIFACTS / "pubmed_article_candidate_summary.json", {})
    orcid_pubmed_article_summary = read_json(ARTIFACTS / "orcid_pubmed_article_candidate_summary.json", {})
    orcid_profile_summary = read_json(ARTIFACTS / "orcid_profile_candidate_summary.json", {})
    orcid_work_summary = read_json(ARTIFACTS / "orcid_work_candidate_summary.json", {})
    trainee_profile_summary = read_json(ARTIFACTS / "penn_trainee_profile_summary.json", {})
    attending_profile_summary = read_json(ARTIFACTS / "penn_attending_profile_summary.json", {})
    state_machine_summary = read_json(ARTIFACTS / "training_state_machine_summary.json", {})
    enrichment_coverage_summary = read_json(ARTIFACTS / "enrichment_coverage_summary.json", {})
    reconciliation_decision_summary = read_json(ARTIFACTS / "evidence_reconciliation_decision_summary.json", {})
    person_evidence_reviewer_decision_summary = read_json(
        ARTIFACTS / "person_evidence_reviewer_decision_summary.json",
        {},
    )
    person_evidence_review_dossier_summary = read_json(
        ARTIFACTS / "person_evidence_review_dossier_summary.json",
        {},
    )
    person_evidence_review_batch_packet_summary = read_json(
        ARTIFACTS / "person_evidence_review_batch_packet_summary.json",
        {},
    )
    longitudinal_readiness_summary = read_json(ARTIFACTS / "longitudinal_change_readiness_summary.json", {})
    transition_plan_summary = read_json(ARTIFACTS / "training_state_transition_plan_summary.json", {})
    program_lifecycle_duration_summary = read_json(ARTIFACTS / "program_lifecycle_duration_evidence_summary.json", {})
    program_lifecycle_duration_reviewer_decision_summary = read_json(
        ARTIFACTS / "program_lifecycle_duration_reviewer_decision_summary.json",
        {},
    )
    attending_trend_linkage_summary = read_json(ARTIFACTS / "attending_trend_linkage_summary.json", {})
    attending_historical_link_summary = read_json(ARTIFACTS / "attending_historical_link_discovery_summary.json", {})
    attending_biosketch_bridge_summary = read_json(ARTIFACTS / "attending_biosketch_bridge_summary.json", {})
    attending_trend_reconciliation_summary = read_json(ARTIFACTS / "attending_trend_reconciliation_summary.json", {})
    attending_trend_review_claims_summary = read_json(ARTIFACTS / "attending_trend_review_claims_summary.json", {})
    attending_trend_acceptance_summary = read_json(ARTIFACTS / "attending_trend_acceptance_summary.json", {})
    attending_trend_reviewer_decision_summary = read_json(
        ARTIFACTS / "attending_trend_reviewer_decision_summary.json",
        {},
    )
    npi_candidate_summary = read_json(ARTIFACTS / "npi_candidate_summary.json", {})
    source_utility_scorecard_summary = read_json(ARTIFACTS / "source_utility_scorecard_summary.json", {})
    person_enrichment_action_execution_plan_summary = read_json(
        ARTIFACTS / "person_enrichment_action_execution_plan_summary.json",
        {},
    )
    person_enrichment_action_member_execution_dossier_summary = read_json(
        ARTIFACTS / "person_enrichment_action_member_execution_dossier_summary.json",
        {},
    )
    research_identity_review_batch_summary = read_json(ARTIFACTS / "research_identity_review_batch_summary.json", {})
    research_identity_review_batch_packet_summary = read_json(
        ARTIFACTS / "research_identity_review_batch_packet_summary.json",
        {},
    )
    research_identity_reviewer_decision_summary = read_json(
        ARTIFACTS / "research_identity_reviewer_decision_summary.json",
        {},
    )
    research_identity_reviewer_dossier_summary = read_json(
        ARTIFACTS / "research_identity_reviewer_decision_dossier_summary.json",
        {},
    )
    search_utility_assurance_summary = read_json(ARTIFACTS / "search_utility_assurance_summary.json", {})
    official_profile_discovery_batch_summary = read_json(
        ARTIFACTS / "official_profile_discovery_batch_summary.json",
        {},
    )
    official_profile_reviewer_dossier_summary = read_json(
        ARTIFACTS / "official_profile_reviewer_decision_dossier_summary.json",
        {},
    )
    attending_trend_reviewer_decision_dossier_summary = read_json(
        ARTIFACTS / "attending_trend_reviewer_decision_dossier_summary.json",
        {},
    )
    corpus_action_worklist_summary = read_json(ARTIFACTS / "corpus_action_worklist_summary.json", {})
    med_student_source_audit_summary = read_json(ARTIFACTS / "penn_med_student_source_audit_summary.json", {})
    med_student_source_audit = read_csv(ARTIFACTS / "penn_med_student_source_audit.csv")
    weakest_program_coverage = read_csv(ARTIFACTS / "program_enrichment_coverage.csv", limit=25)
    top_attending_linkage_groups = read_csv(ARTIFACTS / "attending_trend_linkage_groups.csv", limit=20)
    top_attending_historical_candidates = read_csv(ARTIFACTS / "attending_historical_link_candidates.csv", limit=20)
    top_attending_biosketch_bridges = read_csv(ARTIFACTS / "attending_biosketch_bridge_candidates.csv", limit=25)
    top_attending_trend_reconciliation = read_csv(ARTIFACTS / "attending_trend_reconciliation.csv", limit=25)
    top_attending_trend_review_claims = read_csv(ARTIFACTS / "attending_trend_review_claims.csv", limit=25)
    top_attending_trend_acceptance = read_csv(ARTIFACTS / "attending_trend_acceptance_audit.csv", limit=25)
    top_attending_trend_reviewer_decisions = read_csv(
        ARTIFACTS / "attending_trend_reviewer_decision_audit.csv",
        limit=25,
    )
    top_attending_trend_reviewer_decision_dossiers = read_csv(
        ARTIFACTS / "attending_trend_reviewer_decision_dossiers.csv",
        limit=25,
    )
    top_person_evidence_reviewer_decisions = read_csv(
        ARTIFACTS / "person_evidence_reviewer_decision_audit.csv",
        limit=25,
    )
    top_person_evidence_review_dossiers = read_csv(
        ARTIFACTS / "person_evidence_review_dossiers.csv",
        limit=25,
    )
    top_person_evidence_review_batch_packets = read_csv(
        ARTIFACTS / "person_evidence_review_batch_packets.csv",
        limit=25,
    )
    contact_reviewer_dossier_summary = read_json(
        ARTIFACTS / "contact_verification_reviewer_decision_dossier_summary.json",
        {},
    )
    top_contact_reviewer_dossiers = read_csv(
        ARTIFACTS / "contact_verification_reviewer_decision_dossiers.csv",
        limit=25,
    )
    top_official_profile_reviewer_dossiers = read_csv(
        ARTIFACTS / "official_profile_reviewer_decision_dossiers.csv",
        limit=25,
    )
    top_official_profile_discovery_batches = read_csv(
        ARTIFACTS / "official_profile_discovery_batches.csv",
        limit=25,
    )
    top_attending_trend_review_rollups = read_csv(ARTIFACTS / "attending_trend_review_rollups.csv", limit=25)
    top_npi_candidates = read_csv(ARTIFACTS / "npi_candidate_claims.csv", limit=30)
    source_utility_scorecard = read_csv(ARTIFACTS / "source_utility_scorecard.csv")
    top_person_enrichment_action_member_execution_dossiers = read_csv(
        ARTIFACTS / "person_enrichment_action_member_execution_dossiers.csv",
        limit=25,
    )
    top_person_enrichment_action_execution_plans = read_csv(
        ARTIFACTS / "person_enrichment_action_execution_plan.csv",
        limit=25,
    )
    top_research_identity_review_batches = read_csv(ARTIFACTS / "research_identity_review_batches.csv", limit=25)
    top_research_identity_review_batch_packets = read_csv(
        ARTIFACTS / "research_identity_review_batch_packets.csv",
        limit=25,
    )
    top_research_identity_reviewer_decisions = read_csv(
        ARTIFACTS / "research_identity_reviewer_decision_audit.csv",
        limit=25,
    )
    top_research_identity_reviewer_dossiers = read_csv(
        ARTIFACTS / "research_identity_reviewer_decision_dossiers.csv",
        limit=25,
    )
    search_utility_assurance = read_csv(ARTIFACTS / "search_utility_assurance.csv")
    program_lifecycle_duration_evidence = read_csv(
        ARTIFACTS / "program_lifecycle_duration_evidence.csv",
        limit=25,
    )
    top_program_lifecycle_duration_reviewer_decisions = read_csv(
        ARTIFACTS / "program_lifecycle_duration_reviewer_decision_audit.csv",
        limit=25,
    )
    corpus_action_worklist = read_csv(ARTIFACTS / "corpus_action_worklist.csv", limit=40)
    top_alias_reviewer_decisions = read_csv(ARTIFACTS / "official_program_alias_reviewer_decision_audit.csv", limit=25)
    top_reconciliation_decisions = [
        row
        for row in read_csv(ARTIFACTS / "evidence_reconciliation_decisions.csv")
        if row.get("decision", "").startswith("review_ready")
        or row.get("decision", "").startswith("attending_training_claim_review_ready")
    ][:30]
    hup_coverage_counts = [
        {"coverage_status": status, "count": count}
        for status, count in sorted((hup_coverage_summary.get("by_coverage_status") or {}).items())
    ]
    state_machine_status_counts = [
        {"state_machine_status": status, "count": count}
        for status, count in sorted((state_machine_summary.get("by_state_machine_status") or {}).items())
    ]
    state_machine_clock_counts = [
        {"clock_model": clock, "count": count}
        for clock, count in sorted((state_machine_summary.get("by_clock_model") or {}).items())
    ]
    longitudinal_readiness_counts = [
        {"readiness_status": status, "count": count}
        for status, count in sorted((longitudinal_readiness_summary.get("by_readiness_status") or {}).items())
    ]
    longitudinal_missing_counts = [
        {"missing_expectation": expectation, "count": count}
        for expectation, count in sorted((longitudinal_readiness_summary.get("by_missing_expectation") or {}).items())
    ]
    longitudinal_same_stage_counts = [
        {"same_stage_expectation": expectation, "count": count}
        for expectation, count in sorted(
            (longitudinal_readiness_summary.get("by_same_stage_expectation") or {}).items()
        )
    ]
    transition_policy_lane_counts = [
        {"policy_lane": lane, "count": count}
        for lane, count in sorted((transition_plan_summary.get("by_policy_lane") or {}).items())
    ]
    transition_diff_readiness_counts = [
        {"diff_readiness_status": status, "count": count}
        for status, count in sorted((transition_plan_summary.get("by_diff_readiness_status") or {}).items())
    ]
    program_lifecycle_duration_status_counts = [
        {"duration_evidence_status": status, "count": count}
        for status, count in sorted((program_lifecycle_duration_summary.get("by_duration_evidence_status") or {}).items())
    ]
    program_lifecycle_duration_year_counts = [
        {"explicit_duration_years": years, "count": count}
        for years, count in sorted((program_lifecycle_duration_summary.get("by_explicit_duration_years") or {}).items())
    ]
    program_lifecycle_duration_reviewer_decision_counts = [
        {"decision_status": status, "count": count}
        for status, count in sorted(
            (program_lifecycle_duration_reviewer_decision_summary.get("by_decision_status") or {}).items()
        )
    ]
    enrichment_coverage_bands = [
        {"coverage_band": band, "count": count}
        for band, count in sorted((enrichment_coverage_summary.get("by_coverage_band") or {}).items())
    ]
    enrichment_next_actions = [
        {"recommended_next_action": action, "count": count}
        for action, count in sorted((enrichment_coverage_summary.get("by_recommended_next_action") or {}).items())
    ]
    reconciliation_decision_counts = [
        {"decision": decision, "count": count}
        for decision, count in sorted((reconciliation_decision_summary.get("by_decision") or {}).items())
    ]
    trend_window_counts = [
        {"ten_year_trend_window": window, "count": count}
        for window, count in sorted((reconciliation_decision_summary.get("by_ten_year_trend_window") or {}).items())
    ]
    person_evidence_reviewer_status_counts = [
        {"decision_status": status, "count": count}
        for status, count in sorted(
            (person_evidence_reviewer_decision_summary.get("by_decision_status") or {}).items()
        )
    ]
    person_evidence_reviewer_kind_counts = [
        {"review_kind": kind, "count": count}
        for kind, count in sorted((person_evidence_reviewer_decision_summary.get("by_review_kind") or {}).items())
    ]
    attending_linkage_counts = [
        {"linkage_status": status, "count": count}
        for status, count in sorted((attending_trend_linkage_summary.get("by_linkage_status") or {}).items())
    ]
    attending_assurance_counts = [
        {"assurance_level": level, "count": count}
        for level, count in sorted((attending_trend_linkage_summary.get("by_assurance_level") or {}).items())
    ]
    attending_historical_status_counts = [
        {"candidate_status": status, "count": count}
        for status, count in sorted((attending_historical_link_summary.get("by_candidate_status") or {}).items())
    ]
    attending_biosketch_status_counts = [
        {"bridge_status": status, "count": count}
        for status, count in sorted((attending_biosketch_bridge_summary.get("by_bridge_status") or {}).items())
    ]
    attending_trend_reconciliation_counts = [
        {"trend_status": status, "count": count}
        for status, count in sorted((attending_trend_reconciliation_summary.get("by_trend_status") or {}).items())
    ]
    attending_trend_reviewer_decision_counts = [
        {"decision_status": status, "count": count}
        for status, count in sorted(
            (attending_trend_reviewer_decision_summary.get("by_decision_status") or {}).items()
        )
    ]
    attending_trend_reviewer_decision_dossier_counts = [
        {"decision_status": status, "count": count}
        for status, count in sorted(
            (attending_trend_reviewer_decision_dossier_summary.get("by_decision_status") or {}).items()
        )
    ]
    npi_candidate_status_counts = [
        {"candidate_status": status, "count": count}
        for status, count in sorted((npi_candidate_summary.get("by_candidate_status") or {}).items())
    ]
    npi_taxonomy_counts = [
        {"primary_taxonomy": taxonomy, "count": count}
        for taxonomy, count in list((npi_candidate_summary.get("by_primary_taxonomy") or {}).items())[:20]
    ]
    hup_gap_candidate_counts = [
        {"candidate_status": status, "count": count}
        for status, count in sorted((hup_gap_probe_summary.get("by_candidate_status") or {}).items())
    ]
    alias_reviewer_decision_counts = [
        {"decision_status": status, "count": count}
        for status, count in sorted(
            (official_program_alias_reviewer_decision_summary.get("by_decision_status") or {}).items()
        )
    ]
    top_hup_gap_candidates = [
        {
            "program_name": row.get("program_name", ""),
            "department": row.get("department", ""),
            "candidate_status": row.get("candidate_status", ""),
            "priority": row.get("priority", ""),
            "candidate_title": row.get("candidate_title", ""),
            "candidate_url": row.get("candidate_url", ""),
        }
        for row in hup_gap_candidates
        if row.get("candidate_status") == "roster_source_candidate"
    ][:25]
    hup_not_covered = [
        {
            "program_type": row.get("program_type", ""),
            "department": row.get("department", ""),
            "program_name": row.get("program_name", ""),
            "coverage_status": row.get("coverage_status", ""),
            "match_method": row.get("match_method", ""),
        }
        for row in hup_coverage_rows
        if row.get("coverage_status") != "covered_current_roster"
    ][:35]

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_counts": source_counts,
        "evidence_counts": evidence_counts,
        "utility_observations": utility_observations,
        "openalex_feature_distribution": openalex_features,
        "orcid_feature_distribution": orcid_features,
        "orcid_profile_candidate_summary": orcid_profile_summary,
        "orcid_work_feature_distribution": orcid_work_features,
        "orcid_work_candidate_summary": orcid_work_summary,
        "pubmed_feature_distribution": pubmed_features,
        "pubmed_article_feature_distribution": pubmed_article_features,
        "pubmed_article_candidate_summary": pubmed_article_summary,
        "orcid_pubmed_article_feature_distribution": orcid_pubmed_article_features,
        "orcid_pubmed_article_candidate_summary": orcid_pubmed_article_summary,
        "penn_affiliated_discovery": broad_discovery,
        "career_event_counts": career_events,
        "attending_profile_summary": attending_profile_summary,
        "broad_program_counts": broad_program_counts,
        "generic_program_labels": generic_program_labels,
        "training_state_counts": training_state_counts,
        "transition_rule_counts": transition_rule_counts,
        "lifecycle_code_counts": lifecycle_code_counts,
        "training_state_machine_summary": state_machine_summary,
        "longitudinal_change_readiness_summary": longitudinal_readiness_summary,
        "training_state_transition_plan_summary": transition_plan_summary,
        "program_lifecycle_duration_evidence_summary": program_lifecycle_duration_summary,
        "program_lifecycle_duration_reviewer_decision_summary": program_lifecycle_duration_reviewer_decision_summary,
        "program_lifecycle_duration_evidence": program_lifecycle_duration_evidence,
        "top_program_lifecycle_duration_reviewer_decisions": top_program_lifecycle_duration_reviewer_decisions,
        "enrichment_coverage_summary": enrichment_coverage_summary,
        "weakest_program_enrichment_coverage": weakest_program_coverage,
        "reconciliation_decision_summary": reconciliation_decision_summary,
        "person_evidence_reviewer_decision_summary": person_evidence_reviewer_decision_summary,
        "person_evidence_review_dossier_summary": person_evidence_review_dossier_summary,
        "person_evidence_review_batch_packet_summary": person_evidence_review_batch_packet_summary,
        "top_reconciliation_decisions": top_reconciliation_decisions,
        "attending_trend_linkage_summary": attending_trend_linkage_summary,
        "top_attending_trend_linkage_groups": top_attending_linkage_groups,
        "attending_historical_link_discovery_summary": attending_historical_link_summary,
        "top_attending_historical_link_candidates": top_attending_historical_candidates,
        "attending_biosketch_bridge_summary": attending_biosketch_bridge_summary,
        "top_attending_biosketch_bridges": top_attending_biosketch_bridges,
        "attending_trend_reconciliation_summary": attending_trend_reconciliation_summary,
        "top_attending_trend_reconciliation": top_attending_trend_reconciliation,
        "attending_trend_review_claims_summary": attending_trend_review_claims_summary,
        "top_attending_trend_review_claims": top_attending_trend_review_claims,
        "attending_trend_acceptance_summary": attending_trend_acceptance_summary,
        "top_attending_trend_acceptance": top_attending_trend_acceptance,
        "attending_trend_reviewer_decision_summary": attending_trend_reviewer_decision_summary,
        "top_attending_trend_reviewer_decisions": top_attending_trend_reviewer_decisions,
        "attending_trend_reviewer_decision_dossier_summary": attending_trend_reviewer_decision_dossier_summary,
        "top_attending_trend_reviewer_decision_dossiers": top_attending_trend_reviewer_decision_dossiers,
        "top_attending_trend_review_rollups": top_attending_trend_review_rollups,
        "npi_candidate_summary": npi_candidate_summary,
        "top_npi_candidates": top_npi_candidates,
        "source_utility_scorecard_summary": source_utility_scorecard_summary,
        "source_utility_scorecard": source_utility_scorecard,
        "person_enrichment_action_execution_plan_summary": person_enrichment_action_execution_plan_summary,
        "top_person_enrichment_action_execution_plans": top_person_enrichment_action_execution_plans,
        "person_enrichment_action_member_execution_dossier_summary": person_enrichment_action_member_execution_dossier_summary,
        "top_person_enrichment_action_member_execution_dossiers": top_person_enrichment_action_member_execution_dossiers,
        "research_identity_review_batch_summary": research_identity_review_batch_summary,
        "top_research_identity_review_batches": top_research_identity_review_batches,
        "research_identity_review_batch_packet_summary": research_identity_review_batch_packet_summary,
        "top_research_identity_review_batch_packets": top_research_identity_review_batch_packets,
        "research_identity_reviewer_decision_summary": research_identity_reviewer_decision_summary,
        "top_research_identity_reviewer_decisions": top_research_identity_reviewer_decisions,
        "research_identity_reviewer_dossier_summary": research_identity_reviewer_dossier_summary,
        "top_research_identity_reviewer_dossiers": top_research_identity_reviewer_dossiers,
        "search_utility_assurance_summary": search_utility_assurance_summary,
        "search_utility_assurance": search_utility_assurance,
        "official_profile_discovery_batch_summary": official_profile_discovery_batch_summary,
        "top_official_profile_discovery_batches": top_official_profile_discovery_batches,
        "official_profile_reviewer_dossier_summary": official_profile_reviewer_dossier_summary,
        "top_official_profile_reviewer_dossiers": top_official_profile_reviewer_dossiers,
        "corpus_action_worklist_summary": corpus_action_worklist_summary,
        "top_corpus_action_worklist": corpus_action_worklist,
        "medical_student_source_audit_summary": med_student_source_audit_summary,
        "medical_student_source_audit": med_student_source_audit,
        "reconciliation_queue_counts": reconciliation_queue_counts,
        "top_reconciliation_queue": top_reconciliation_queue,
        "top_person_evidence_reviewer_decisions": top_person_evidence_reviewer_decisions,
        "top_person_evidence_review_dossiers": top_person_evidence_review_dossiers,
        "top_person_evidence_review_batch_packets": top_person_evidence_review_batch_packets,
        "contact_counts": contact_counts,
        "contact_assurance_counts": contact_assurance_counts,
        "contact_reviewer_decision_counts": contact_reviewer_decision_counts,
        "contact_reviewer_dossier_summary": contact_reviewer_dossier_summary,
        "top_contact_reviewer_dossiers": top_contact_reviewer_dossiers,
        "accepted_contact_counts": accepted_contact_counts,
        "hup_gme_program_coverage_summary": hup_coverage_summary,
        "hup_gme_program_coverage_gaps_sample": hup_not_covered,
        "hup_gme_gap_source_probe_summary": hup_gap_probe_summary,
        "hup_gme_top_gap_source_candidates": top_hup_gap_candidates,
        "hup_gme_gap_roster_summary": hup_gap_roster_summary,
        "official_gap_roster_reconciliation_summary": official_gap_roster_reconciliation_summary,
        "official_gap_roster_program_resolution_summary": official_gap_roster_program_resolution_summary,
        "official_program_coverage_assurance_summary": official_program_coverage_assurance_summary,
        "official_program_coverage_action_queue_summary": official_program_coverage_action_queue_summary,
        "official_program_alias_review_packets_summary": official_program_alias_review_packets_summary,
        "official_program_alias_reviewer_decision_summary": official_program_alias_reviewer_decision_summary,
        "top_official_program_alias_reviewer_decisions": top_alias_reviewer_decisions,
    }
    if openalex_features:
        openalex_learning = "Learning: OpenAlex is useful for generating review candidates when name, Penn affiliation, prior institution, and ORCID features cluster. It is not safe as a direct profile mutator because author disambiguation and stale affiliations remain real risks."
    else:
        openalex_learning = "Learning: OpenAlex remains a promising author-disambiguation utility, but the current full-corpus run hit sustained 429 throttling. Record that as source availability/operations evidence, not as rejected person identity evidence."
    (ARTIFACTS / "source_quality_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Penn Source Quality Learnings",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## What This Pass Did",
        "",
        "This pass widened Penn source discovery beyond Department of Medicine, then ran candidate-only scholarly enrichment across the current resident/fellow corpus. No scholarly claims were accepted automatically.",
        "",
        "## Penn-Wide Source Discovery",
        "",
        *md_table(broad_discovery, ["classification", "count"]),
        "",
        "Interpretation: `trainee_roster_candidate` is a review queue, not a canonical roster count. Program-context pages can mention residents/fellows without listing people, and some faculty pages share the same bio components as trainee pages.",
        "",
        "## Official HUP GME Program Universe",
        "",
        f"Official denominator source: {hup_coverage_summary.get('source_url', 'not generated')}",
        "",
        f"Official HUP programs parsed: {hup_coverage_summary.get('programs', 0)}.",
        "",
        *md_table(hup_coverage_counts, ["coverage_status", "count"]),
        "",
        "Coverage assurance tiers:",
        "",
        f"Level-4 supported programs: {official_program_coverage_assurance_summary.get('level_4_program_rows', 0)} covering {official_program_coverage_assurance_summary.get('level_4_people_count', 0)} people. Alias/count-review programs: {official_program_coverage_assurance_summary.get('alias_review_program_rows', 0)}. Open denominator gaps: {official_program_coverage_assurance_summary.get('open_gap_rows', 0)}.",
        "",
        *md_table(
            [
                {"assurance_status": status, "count": count}
                for status, count in sorted(
                    (official_program_coverage_assurance_summary.get("by_assurance_status") or {}).items()
                )
            ],
            ["assurance_status", "count"],
        ),
        "",
        "Coverage action queue:",
        "",
        f"Action rows: {official_program_coverage_action_queue_summary.get('queue_rows', 0)}. Person-impact count: {official_program_coverage_action_queue_summary.get('total_person_impact_count', 0)}.",
        "",
        *md_table(
            [
                {"action_lane": lane, "count": count}
                for lane, count in sorted(
                    (official_program_coverage_action_queue_summary.get("by_action_lane") or {}).items()
                )
            ],
            ["action_lane", "count"],
        ),
        "",
        "Top coverage actions:",
        "",
        *md_table(
            official_program_coverage_action_queue_summary.get("top_actions") or [],
            ["official_program_name", "official_program_type", "action_lane", "priority", "person_impact_count", "recommended_next_action"],
        ),
        "",
        "Alias review packets:",
        "",
        f"Alias packet rows: {official_program_alias_review_packets_summary.get('packet_rows', 0)}. Reviewer-ready rows: {official_program_alias_review_packets_summary.get('reviewer_ready_rows', 0)}. Reviewer-ready person count: {official_program_alias_review_packets_summary.get('reviewer_ready_person_count', 0)}.",
        "",
        *md_table(
            [
                {"alias_decision_status": status, "count": count}
                for status, count in sorted(
                    (official_program_alias_review_packets_summary.get("by_alias_decision_status") or {}).items()
                )
            ],
            ["alias_decision_status", "count"],
        ),
        "",
        "Top alias packets:",
        "",
        *md_table(
            official_program_alias_review_packets_summary.get("top_packets") or [],
            ["official_program_name", "loaded_program_name", "loaded_person_count", "alias_decision_status", "reviewer_ready", "recommended_next_action"],
        ),
        "",
        "Alias reviewer decisions:",
        "",
        f"Queue rows: {official_program_alias_reviewer_decision_summary.get('queue_rows', 0)}. Ready rows: {official_program_alias_reviewer_decision_summary.get('ready_queue_rows', 0)}. Manual decision rows: {official_program_alias_reviewer_decision_summary.get('manual_decision_rows', 0)}. Accepted alias mappings: {official_program_alias_reviewer_decision_summary.get('accepted_alias_mapping_rows', 0)}. Pending reviewer decisions: {official_program_alias_reviewer_decision_summary.get('pending_reviewer_decision_rows', 0)}.",
        "",
        *md_table(alias_reviewer_decision_counts, ["decision_status", "count"]),
        "",
        *md_table(
            top_alias_reviewer_decisions,
            [
                "official_program_name",
                "loaded_program_name",
                "loaded_person_count",
                "reviewer_decision",
                "decision_status",
                "accepted_alias_mapping",
                "recommended_next_action",
            ],
        ),
        "",
        "Sample uncovered or partially covered official programs:",
        "",
        *md_table(
            hup_not_covered,
            ["program_type", "department", "program_name", "coverage_status", "match_method"],
        ),
        "",
        "Learning: source discovery is not coverage. An official program-universe table gives the denominator needed for gap accounting, annual recrawls, and institution-level diff views. `covered_current_roster` means we have current people attached; `discovered_no_current_roster` means a program page is known but no current roster people are captured; `not_discovered` names crawl gaps.",
        "",
        "## HUP Gap Source Queue",
        "",
        f"Gap programs probed: {hup_gap_probe_summary.get('gap_programs', 0)}. Source pages probed: {hup_gap_probe_summary.get('source_pages_probed', 0)}. Search query rows: {hup_gap_probe_summary.get('search_query_rows', 0)}. Search observations: {hup_gap_probe_summary.get('search_observation_rows', 0)}. Candidate URLs queued: {hup_gap_probe_summary.get('candidate_urls', 0)}.",
        "",
        f"Search scope: {hup_gap_probe_summary.get('search_scope', '')}. Search enabled: {hup_gap_probe_summary.get('search_enabled', False)}.",
        "",
        *md_table(hup_gap_candidate_counts, ["candidate_status", "count"]),
        "",
        "Top roster-source candidates:",
        "",
        *md_table(
            top_hup_gap_candidates,
            ["program_name", "department", "candidate_status", "priority", "candidate_title", "candidate_url"],
        ),
        "",
        "Learning: coverage gaps need their own crawl state. Official program URLs, discovered context pages, and linked roster-like pages should be queued separately so the next scraper can attack high-priority roster candidates without conflating them with verified person records.",
        "",
        "## HUP Gap Roster Extraction",
        "",
        f"Supported gap roster sources attempted: {hup_gap_roster_summary.get('sources_attempted', 0)}. Sources with records: {hup_gap_roster_summary.get('sources_with_records', 0)}. Person records extracted: {hup_gap_roster_summary.get('person_records', 0)}.",
        "",
        "Records by role:",
        "",
        *md_table(
            [
                {"role": role, "count": count}
                for role, count in sorted((hup_gap_roster_summary.get("by_role") or {}).items())
            ],
            ["role", "count"],
        ),
        "",
        "Extraction statuses:",
        "",
        *md_table(
            [
                {"extraction_status": status, "count": count}
                for status, count in sorted((hup_gap_roster_summary.get("by_extraction_status") or {}).items())
            ],
            ["extraction_status", "count"],
        ),
        "",
        "Denominator-link reconciliation:",
        "",
        f"Official-linked extracted records: {official_gap_roster_reconciliation_summary.get('official_linked_records_extracted', 0)}. Seed records still missing denominator keys: {official_gap_roster_reconciliation_summary.get('seed_without_denominator_key_records', 0)}. Loaded memberships from reconciled sources: {official_gap_roster_reconciliation_summary.get('loaded_membership_count', 0)}.",
        "",
        *md_table(
            [
                {"denominator_link_status": status, "count": count}
                for status, count in sorted(
                    (official_gap_roster_reconciliation_summary.get("by_denominator_link_status") or {}).items()
                )
            ],
            ["denominator_link_status", "count"],
        ),
        "",
        "Seed roster program-resolution audit:",
        "",
        f"Resolution rows reviewed: {official_gap_roster_program_resolution_summary.get('resolution_rows', 0)}. Reviewer-ready exact-resolution records: {official_gap_roster_program_resolution_summary.get('denominator_mutation_allowed_records', 0)}. Review-required records: {official_gap_roster_program_resolution_summary.get('review_required_records', 0)}.",
        "",
        *md_table(
            [
                {
                    "resolution_status": status,
                    "records": records,
                }
                for status, records in sorted(
                    (official_gap_roster_program_resolution_summary.get("records_by_resolution_status") or {}).items()
                )
            ],
            ["resolution_status", "records"],
        ),
        "",
        "Learning: queue-driven extraction should stay template-aware. Pages without supported person structure remain source candidates; this avoids converting program context, generic people directories, or ambiguous student-fellow pages into trainee records. Extracted people and denominator coverage closure are separate claims: seed-derived records need an official program key or alias reconciliation before they can close an official HUP program gap.",
        "",
        "## Penn-Wide Program Categorization",
        "",
        *md_table(broad_program_counts, ["program_name", "role", "count"]),
        "",
        f"Generic `Residents`/`Fellows` program labels remaining: {sum(row['count'] for row in generic_program_labels)}.",
        "",
        "Learning: program names often require URL-plus-section inference. Page titles alone are too weak because official pages can be titled `Residents` or `Fellows`, while one source page can contain multiple program sections.",
        "",
        "## Penn Medical Student Public-Source Audit",
        "",
        f"Student-source audit rows: {med_student_source_audit_summary.get('audit_rows', 0)}. Public MSTP loaded people: {med_student_source_audit_summary.get('public_mstp_loaded_people', 0)}. Protected MD-directory rows: {med_student_source_audit_summary.get('protected_md_directory_rows', 0)}. Graduate cross-check rows: {med_student_source_audit_summary.get('graduate_crosscheck_rows', 0)}.",
        "",
        "Capture statuses:",
        "",
        *md_table(
            [
                {"capture_status": status, "count": count}
                for status, count in sorted((med_student_source_audit_summary.get("by_capture_status") or {}).items())
            ],
            ["capture_status", "count"],
        ),
        "",
        "Audited student source surfaces:",
        "",
        *md_table(
            med_student_source_audit,
            [
                "source_scope",
                "access_status",
                "capture_status",
                "public_person_count_observed",
                "loaded_person_count",
                "source_url",
            ],
        ),
        "",
        "Learning: the public medical-student universe is not the same as the full medical-student universe. The official MSTP directory is a public current MD-PhD roster and remains accepted as a partial student truth anchor. The official MD student directory is PennKey protected, so it should be recorded as unavailable to public scraping and monitored for access changes. Graduate-program student directories can cross-check or enrich MD-PhD students, but they overlap MSTP and broader PhD populations and should not mutate the MD-student denominator.",
        "",
        "## Training State Machine",
        "",
        *md_table(training_state_counts, ["stage_family", "normalized_stage", "status", "count", "avg_confidence"]),
        "",
        "Transition rules observed:",
        "",
        *md_table(transition_rule_counts, ["transition_rule", "count"]),
        "",
        "Lifecycle semantics observed:",
        "",
        *md_table(
            lifecycle_code_counts,
            ["lifecycle_code", "expected_transition_type", "refresh_policy", "count", "avg_confidence"],
        ),
        "",
        "State-machine audit status:",
        "",
        *md_table(state_machine_status_counts, ["state_machine_status", "count"]),
        "",
        "Clock models:",
        "",
        *md_table(state_machine_clock_counts, ["clock_model", "count"]),
        "",
        f"Auto-advance candidate rows: {state_machine_summary.get('auto_advance_candidate_rows', 0)}. Completion candidate rows: {state_machine_summary.get('completion_candidate_rows', 0)}. Stale/review rows: {state_machine_summary.get('stale_or_review_state_rows', 0)}.",
        "",
        "Learning: roster strings should become normalized state observations with explicit clocks and program lifecycle semantics. PGY and fellowship-year states can be annual-clock states, but terminal-year, unknown-duration, research, chief, and source-ambiguous states need different refresh/exit behavior. Lifecycle codes are local `redmank` codes until external ACGME/ERAS/NRMP identifiers are source-backed. The audit layer makes that operational: a row is only stale, advanceable, or removable when its lifecycle rule says so.",
        "",
        "### Program Duration Evidence",
        "",
        f"Target rows: {program_lifecycle_duration_summary.get('target_rows', 0)}. Reviewer-ready duration candidates: {program_lifecycle_duration_summary.get('reviewer_ready_duration_candidates', 0)}. Context-review rows: {(program_lifecycle_duration_summary.get('conflicting_duration_review_rows', 0) or 0) + (program_lifecycle_duration_summary.get('source_mismatch_review_rows', 0) or 0)}. No-explicit-duration rows: {program_lifecycle_duration_summary.get('no_explicit_duration_rows', 0)}.",
        "",
        *md_table(program_lifecycle_duration_status_counts, ["duration_evidence_status", "count"]),
        "",
        *md_table(program_lifecycle_duration_year_counts, ["explicit_duration_years", "count"]),
        "",
        f"Reviewer queue rows: {program_lifecycle_duration_reviewer_decision_summary.get('queue_rows', 0)}. Ready rows: {program_lifecycle_duration_reviewer_decision_summary.get('ready_queue_rows', 0)}. Context-review rows: {program_lifecycle_duration_reviewer_decision_summary.get('context_review_rows', 0)}. Manual decision rows: {program_lifecycle_duration_reviewer_decision_summary.get('manual_decision_rows', 0)}. Accepted duration mappings: {program_lifecycle_duration_reviewer_decision_summary.get('accepted_duration_mapping_rows', 0)}.",
        "",
        *md_table(program_lifecycle_duration_reviewer_decision_counts, ["decision_status", "count"]),
        "",
        *md_table(
            top_program_lifecycle_duration_reviewer_decisions,
            [
                "official_program_name",
                "matched_program_name",
                "explicit_duration_years",
                "reviewer_decision",
                "decision_status",
                "recommended_next_action",
            ],
        ),
        "",
        *md_table(
            program_lifecycle_duration_evidence,
            [
                "official_program_name",
                "page_title",
                "explicit_duration_years",
                "duration_evidence_status",
                "recommended_action",
            ],
        ),
        "",
        "Learning: ACGME identifiers are useful program anchors but not duration proof. Official Penn pages can provide explicit duration evidence for some unknown-duration rows, but stale URLs, title mismatches, and multiple duration-like phrases must stay in review before lifecycle rules are updated. Reviewer-accepted duration mappings remain non-mutating until a later lifecycle-rule edit cites them.",
        "",
        "## Longitudinal Change Readiness",
        "",
        f"Projected refresh date: {longitudinal_readiness_summary.get('projected_refresh_date', 'not generated')}. State rows: {longitudinal_readiness_summary.get('state_rows', 0)}. Person rows: {longitudinal_readiness_summary.get('person_rows', 0)}. Program rows: {longitudinal_readiness_summary.get('program_rows', 0)}.",
        "",
        "Readiness statuses:",
        "",
        *md_table(longitudinal_readiness_counts, ["readiness_status", "count"]),
        "",
        "Missing-on-refresh expectations:",
        "",
        *md_table(longitudinal_missing_counts, ["missing_expectation", "count"]),
        "",
        "Same-stage-on-refresh expectations:",
        "",
        *md_table(longitudinal_same_stage_counts, ["same_stage_expectation", "count"]),
        "",
        f"Advancement due rows: {longitudinal_readiness_summary.get('advance_due_by_refresh_rows', 0)}. Completion-window rows: {longitudinal_readiness_summary.get('completion_window_by_refresh_rows', 0)}. Source-refresh-required rows: {longitudinal_readiness_summary.get('requires_source_refresh_by_refresh_rows', 0)}. Human-review rows: {longitudinal_readiness_summary.get('requires_human_review_by_refresh_rows', 0)}.",
        "",
        "Learning: annual diffs should be state-machine informed before they are person-table mutations. A missing terminal-year fellow after the stale-after date is likely completion; a missing PGY-2 before the expected exit is a review item; an unchanged MSTP PhD-phase student needs a fresh source rather than an inferred clock advancement.",
        "",
        "## Transition Plan Ledger",
        "",
        f"Plan rows: {transition_plan_summary.get('plan_rows', 0)}. Rollup rows: {transition_plan_summary.get('rollup_rows', 0)}. Auto-classifiable transition rows: {transition_plan_summary.get('auto_classifiable_transition_rows', 0)}. Fresh-observation-required rows: {transition_plan_summary.get('fresh_observation_required_rows', 0)}.",
        "",
        "Policy lanes:",
        "",
        *md_table(transition_policy_lane_counts, ["policy_lane", "count"]),
        "",
        "Diff readiness:",
        "",
        *md_table(transition_diff_readiness_counts, ["diff_readiness_status", "count"]),
        "",
        f"Corpus action: {transition_plan_summary.get('corpus_recommended_operator_action', 'not generated')}. Policy: {transition_plan_summary.get('policy', '')}",
        "",
        "Learning: the transition plan is the executable state-machine contract for future refreshes. It keeps expected advancement/completion, source-bound retention, and manual-review lanes separate, so a next-year run can produce individual, program, institution, category, and country diff views without silently carrying stale trainee states forward.",
        "",
        "## Evidence Counts",
        "",
        *md_table(evidence_counts, ["source_key", "status", "claim_type", "count", "avg_confidence"]),
        "",
        "## Source Utility Scorecard",
        "",
        f"Scorecard rows: {source_utility_scorecard_summary.get('scorecard_rows', 0)}.",
        "",
        *md_table(
            source_utility_scorecard,
            [
                "utility_label",
                "claim_surface",
                "input_records",
                "output_records",
                "score",
                "quality_band",
                "recommended_next_action",
            ],
        ),
        "",
        "Learning: a source utility should be judged by the claim surface it supports, not by whether it exists. Official rosters are current-membership truth anchors; PubMed author-query rows are discovery only; PubMed article rows become review-ready only with non-name anchors; current attending profiles are endpoint and training-history candidates until a historical identity bridge exists; and broad search/crawler outputs should feed probe and parser queues before becoming person evidence.",
        "",
        "## Person Enrichment Action Execution",
        "",
        f"Execution-plan rows: {person_enrichment_action_execution_plan_summary.get('execution_plan_rows', 0)}. Ready plans: {person_enrichment_action_execution_plan_summary.get('ready_plan_rows', 0)}. Pending members: {person_enrichment_action_execution_plan_summary.get('pending_member_count', 0)}. Blocked members: {person_enrichment_action_execution_plan_summary.get('blocked_member_count', 0)}.",
        "",
        *md_table(
            top_person_enrichment_action_execution_plans,
            [
                "execution_order",
                "primary_action_lane",
                "role",
                "priority_band",
                "batch_status",
                "pending_member_count",
                "blocker_status",
                "recommended_operator_action",
            ],
        ),
        "",
        f"Dossier rows: {person_enrichment_action_member_execution_dossier_summary.get('dossier_rows', 0)}. Ready dossiers: {person_enrichment_action_member_execution_dossier_summary.get('ready_dossier_rows', 0)}. Pending dossiers: {person_enrichment_action_member_execution_dossier_summary.get('pending_dossier_rows', 0)}. Manual-review dossiers: {person_enrichment_action_member_execution_dossier_summary.get('manual_review_dossier_rows', 0)}. Collector-execution dossiers: {person_enrichment_action_member_execution_dossier_summary.get('collector_execution_dossier_rows', 0)}.",
        "",
        *md_table(
            top_person_enrichment_action_member_execution_dossiers,
            [
                "display_name",
                "role",
                "primary_action_lane",
                "decision_complexity",
                "dossier_status",
                "execution_risk_level",
                "missing_execution_summary",
                "recommended_operator_action",
            ],
        ),
        "",
        "Learning: batch execution needs the same fingerprint and routing discipline as reviewer decisions. A worked action member is not an accepted fact; it is only complete when the current member fingerprint is recorded and outputs are routed to source-specific profile, evidence, contact, or acceptance ledgers.",
        "",
        "## Research Identity Review Batches",
        "",
        f"Batch rows: {research_identity_review_batch_summary.get('batch_rows', 0)}. Member rows: {research_identity_review_batch_summary.get('member_rows', 0)}. Ready batches: {research_identity_review_batch_summary.get('ready_batch_rows', 0)}. Conflict-member rows: {research_identity_review_batch_summary.get('conflict_member_rows', 0)}.",
        "",
        "Review lanes:",
        "",
        *md_table(
            [
                {"review_lane": lane, "count": count}
                for lane, count in sorted((research_identity_review_batch_summary.get("by_review_lane") or {}).items())
            ],
            ["review_lane", "count"],
        ),
        "",
        "Top batches:",
        "",
        *md_table(
            top_research_identity_review_batches,
            [
                "execution_order",
                "research_identity_status",
                "review_lane",
                "role",
                "person_count",
                "review_ready_record_count",
                "conflict_count",
                "target_decision_artifact",
            ],
        ),
        "",
        "Batch packets:",
        "",
        f"Packet rows: {research_identity_review_batch_packet_summary.get('batch_packet_rows', 0)}. Pending member decisions: {research_identity_review_batch_packet_summary.get('pending_decision_count', 0)}. Conflict packets: {research_identity_review_batch_packet_summary.get('conflict_packet_rows', 0)}. Conflict members: {research_identity_review_batch_packet_summary.get('conflict_member_count', 0)}.",
        "",
        *md_table(
            top_research_identity_review_batch_packets,
            [
                "execution_order",
                "review_lane",
                "role",
                "person_count",
                "pending_decision_count",
                "conflict_member_count",
                "packet_status",
                "recommended_reviewer_action",
            ],
        ),
        "",
        "Reviewer decisions:",
        "",
        f"Queue rows: {research_identity_reviewer_decision_summary.get('queue_rows', 0)}. Audit rows: {research_identity_reviewer_decision_summary.get('audit_rows', 0)}. Pending rows: {research_identity_reviewer_decision_summary.get('pending_reviewer_decision_rows', 0)}. Conflict queue rows: {research_identity_reviewer_decision_summary.get('conflict_queue_rows', 0)}. Accepted review rows: {research_identity_reviewer_decision_summary.get('accepted_research_identity_review_rows', 0)}.",
        "",
        *md_table(
            top_research_identity_reviewer_decisions,
            [
                "display_name",
                "role",
                "review_lane",
                "research_identity_status",
                "decision_status",
                "conflicting_identifier_count",
                "recommended_next_action",
            ],
        ),
        "",
        "Decision dossiers:",
        "",
        f"Dossier rows: {research_identity_reviewer_dossier_summary.get('dossier_rows', 0)}. Pending dossiers: {research_identity_reviewer_dossier_summary.get('pending_dossier_rows', 0)}. Conflict dossiers: {research_identity_reviewer_dossier_summary.get('conflict_dossier_rows', 0)}. Dossier review-ready records: {research_identity_reviewer_dossier_summary.get('review_ready_record_count', 0)}.",
        "",
        *md_table(
            top_research_identity_reviewer_dossiers,
            [
                "display_name",
                "role",
                "review_lane",
                "decision_complexity",
                "dossier_status",
                "identity_risk_level",
                "missing_evidence_summary",
                "recommended_reviewer_action",
            ],
        ),
        "",
        "Learning: research identity corroboration becomes operational only when it is bounded into review sessions with member fingerprints, paired with an auditable reviewer-decision input, reduced into compact dossiers, and rolled into batch packets. The packets preserve the non-mutating acceptance boundary while making conflict reconciliation, multi-source scholarly identity review, secondary-anchor collection, and research-relevance decisions executable without opening every nested evidence JSON file.",
        "",
        "## Search Utility Assurance",
        "",
        f"Utility rows: {search_utility_assurance_summary.get('utility_rows', 0)}. Query rows: {search_utility_assurance_summary.get('query_rows', 0)}. Search observations: {search_utility_assurance_summary.get('search_observation_rows', 0)}. Search candidates: {search_utility_assurance_summary.get('search_candidate_rows', 0)}. Non-200 search rows: {search_utility_assurance_summary.get('non_200_search_rows', 0)}.",
        "",
        *md_table(
            search_utility_assurance,
            [
                "utility_name",
                "query_rows",
                "search_observation_rows",
                "search_candidate_rows",
                "result_rows",
                "search_execution_status",
                "recommended_next_action",
            ],
        ),
        "",
        "Learning: query manifests, endpoint observations, and discovered candidates are separate evidence classes. A skipped or blocked search lane cannot be interpreted as evidence that no public page exists; it only tells us which discovery utility still needs execution, retry, or replacement.",
        "",
        "## Official Profile Discovery Batches",
        "",
        f"Batch rows: {official_profile_discovery_batch_summary.get('batch_rows', 0)}. Workbench rows covered: {official_profile_discovery_batch_summary.get('workbench_count', 0)}. Queries: {official_profile_discovery_batch_summary.get('query_count', 0)}. Unsearched queries: {official_profile_discovery_batch_summary.get('unsearched_query_count', 0)}. Blocked queries: {official_profile_discovery_batch_summary.get('blocked_query_count', 0)}. Official candidates: {official_profile_discovery_batch_summary.get('official_candidate_count', 0)}.",
        "",
        *md_table(
            top_official_profile_discovery_batches,
            [
                "execution_order",
                "discovery_lane",
                "role",
                "batch_status",
                "workbench_count",
                "query_count",
                "recommended_operator_action",
            ],
        ),
        "",
        "## Official Profile Reviewer Dossiers",
        "",
        f"Dossier rows: {official_profile_reviewer_dossier_summary.get('dossier_rows', 0)}. Pending decisions: {official_profile_reviewer_dossier_summary.get('pending_reviewer_decision_rows', 0)}. Manual templates: {official_profile_reviewer_dossier_summary.get('manual_decision_template_rows', 0)}.",
        "",
        *md_table(
            top_official_profile_reviewer_dossiers,
            [
                "display_name",
                "role",
                "program_name",
                "decision_status",
                "reobservation_status",
                "decision_blocker",
                "recommended_next_action",
            ],
        ),
        "",
        "Learning: official profile URLs are strong identity/context anchors only after the current profile fingerprint and source hash survive explicit reviewer confirmation. Stale route drift, including generic academic-department redirects, stays as review work rather than accepted profile truth.",
        "",
        "## Corpus Action Worklist",
        "",
        f"Worklist rows: {corpus_action_worklist_summary.get('worklist_rows', 0)}. Summed impact count: {corpus_action_worklist_summary.get('total_impact_count', 0)}. Critical rows: {corpus_action_worklist_summary.get('critical_rows', 0)}. High rows: {corpus_action_worklist_summary.get('high_rows', 0)}.",
        "",
        *md_table(
            corpus_action_worklist,
            [
                "action_surface",
                "action_scope",
                "display_label",
                "role",
                "priority",
                "impact_count",
                "recommended_next_action",
            ],
        ),
        "",
        "Learning: unresolved evidence should be ranked as operator work, not inferred away. Program gaps, search execution, person evidence packets, contact verification, temporal-state refreshes, enrichment collectors, and attending-trend bridges all have different acceptance gates, so the worklist keeps their required next evidence explicit.",
        "",
        "## Evidence Reconciliation Queue",
        "",
        *md_table(
            reconciliation_queue_counts,
            ["record_type", "status", "claim_type", "count", "avg_priority", "avg_confidence"],
        ),
        "",
        "Top queued records:",
        "",
        *md_table(
            top_reconciliation_queue,
            ["record_type", "display_name", "role", "claim_type", "status", "confidence", "priority", "review_action"],
        ),
        "",
        "Learning: candidate evidence needs a ranked reconciliation surface. The queue separates review-ready items, such as article-level PubMed candidates with non-name anchors and official attending profile Penn-training claims, from low-value discovery signals like name-only PubMed query counts.",
        "",
        "## Reconciliation Decision Ledger",
        "",
        f"Decision rows: {reconciliation_decision_summary.get('decision_rows', 0)}. Review-ready rows: {reconciliation_decision_summary.get('review_ready_rows', 0)}. Person/name rollups: {reconciliation_decision_summary.get('person_or_name_rows', 0)}.",
        "",
        "Decision counts:",
        "",
        *md_table(reconciliation_decision_counts, ["decision", "count"]),
        "",
        "Ten-year attending trend window:",
        "",
        *md_table(trend_window_counts, ["ten_year_trend_window", "count"]),
        "",
        "Top review-ready decisions:",
        "",
        *md_table(
            top_reconciliation_decisions,
            [
                "record_type",
                "display_name",
                "role",
                "claim_type",
                "decision",
                "confidence",
                "priority",
                "ten_year_trend_window",
                "source_url",
            ],
        ),
        "",
        "Learning: reconciliation should be an explicit decision ledger, not a side effect of queue priority. Review-ready means enough anchors exist for efficient review; accepted truth still requires a manual or stronger automated identity verifier.",
        "",
        "## Person Evidence Reviewer Decisions",
        "",
        f"Queue rows: {person_evidence_reviewer_decision_summary.get('queue_rows', 0)}. Audit rows: {person_evidence_reviewer_decision_summary.get('audit_rows', 0)}. Pending reviewer decisions: {person_evidence_reviewer_decision_summary.get('pending_reviewer_decision_rows', 0)}. Accepted candidate facts: {person_evidence_reviewer_decision_summary.get('accepted_candidate_fact_rows', 0)}.",
        "",
        "Decision statuses:",
        "",
        *md_table(person_evidence_reviewer_status_counts, ["decision_status", "count"]),
        "",
        "Review kinds:",
        "",
        *md_table(person_evidence_reviewer_kind_counts, ["review_kind", "count"]),
        "",
        "Top packet-level reviewer rows:",
        "",
        *md_table(
            top_person_evidence_reviewer_decisions,
            [
                "display_name",
                "role",
                "packet_status",
                "review_kind",
                "decision_status",
                "review_priority",
                "best_decision",
                "best_source_url",
            ],
        ),
        "",
        "Batch packet support:",
        "",
        f"Batch packet rows: {person_evidence_review_batch_packet_summary.get('batch_packet_rows', 0)}. Batches covered: {person_evidence_review_batch_packet_summary.get('batch_count', 0)}. Review-ready records: {person_evidence_review_batch_packet_summary.get('review_ready_record_count', 0)}. Evidence records: {person_evidence_review_batch_packet_summary.get('evidence_record_count', 0)}.",
        "",
        *md_table(
            top_person_evidence_review_batch_packets,
            [
                "execution_order",
                "batch_packet_order",
                "display_name",
                "role",
                "triage_lane",
                "support_status",
                "recommended_reviewer_action",
            ],
        ),
        "",
        "Reviewer decision dossiers:",
        "",
        f"Dossier rows: {person_evidence_review_dossier_summary.get('dossier_rows', 0)}. Pending decisions: {person_evidence_review_dossier_summary.get('pending_reviewer_decision_rows', 0)}. Review-ready evidence rows: {person_evidence_review_dossier_summary.get('review_ready_record_count', 0)}.",
        "",
        *md_table(
            top_person_evidence_review_dossiers,
            [
                "display_name",
                "role",
                "review_route",
                "decision_status",
                "risk_level",
                "missing_evidence_summary",
                "recommended_reviewer_action",
            ],
        ),
        "",
        "Learning: packet-level reviewer decisions are now a first-class ledger. The system can separate candidate evidence that is merely review-ready from evidence that a reviewer explicitly accepted, rejected, or deferred against a stable packet fingerprint.",
        "",
        "## Attending Trend Linkage Assurance",
        "",
        f"Career-event rows audited: {attending_trend_linkage_summary.get('event_rows', 0)}. Person/source groups: {attending_trend_linkage_summary.get('event_group_rows', 0)}. Groups with current attending endpoints: {attending_trend_linkage_summary.get('groups_with_current_endpoint', 0)}. Groups with Penn-training profile claims: {attending_trend_linkage_summary.get('groups_with_penn_training_claim', 0)}. Groups with current trainee name matches: {attending_trend_linkage_summary.get('groups_with_current_trainee_name_match', 0)}.",
        "",
        "Linkage statuses:",
        "",
        *md_table(attending_linkage_counts, ["linkage_status", "count"]),
        "",
        "Assurance levels:",
        "",
        *md_table(attending_assurance_counts, ["assurance_level", "count"]),
        "",
        "Top linkage groups:",
        "",
        *md_table(
            top_attending_linkage_groups,
            [
                "display_name",
                "event_count",
                "best_linkage_status",
                "best_trend_link_assurance_level",
                "has_current_attending_endpoint",
                "has_penn_training_claim",
                "has_current_trainee_name_match",
                "event_years",
            ],
        ),
        "",
        "Learning: current Penn attending pages are endpoint evidence, not trend-line facts. The current corpus has endpoint-plus-Penn-training groups but no linked historical trainee identity yet, so recent-attending trend claims should remain candidates until a historical roster, alumni page, CV, or independent profile supplies the missing dated Penn trainee link.",
        "",
        "## Attending Historical Link Discovery",
        "",
        f"Groups considered: {attending_historical_link_summary.get('groups_considered', 0)}. Seeded source rows: {attending_historical_link_summary.get('seeded_source_rows', 0)}. Search observations: {attending_historical_link_summary.get('search_observations', 0)}. Search skipped: {attending_historical_link_summary.get('search_skipped', '')}. Candidate rows: {attending_historical_link_summary.get('candidate_rows', 0)}.",
        "",
        "Candidate statuses:",
        "",
        *md_table(attending_historical_status_counts, ["candidate_status", "count"]),
        "",
        "Top historical-link candidates:",
        "",
        *md_table(
            top_attending_historical_candidates,
            [
                "display_name",
                "query_kind",
                "candidate_status",
                "confidence",
                "priority",
                "result_domain",
                "probe_title",
                "required_next_evidence",
            ],
        ),
        "",
        "Learning: seeded official Penn/provider URLs give a deterministic baseline for trend-link discovery, while broad web search is an optional, rate-limited enrichment utility. Even strong official profile candidates remain review candidates until the page text supplies explicit same-person, Penn-training, program, and date anchors.",
        "",
        "## Official Faculty Biosketch Bridge Audit",
        "",
        f"Target Penn-training current-attending groups: {attending_biosketch_bridge_summary.get('target_groups', 0)}. Source observations: {attending_biosketch_bridge_summary.get('source_observation_rows', 0)}. Candidate rows: {attending_biosketch_bridge_summary.get('candidate_rows', 0)}. Groups with recent dated bridge candidates: {attending_biosketch_bridge_summary.get('groups_with_recent_dated_bridge_candidates', 0)}.",
        "",
        "Bridge statuses:",
        "",
        *md_table(attending_biosketch_status_counts, ["bridge_status", "count"]),
        "",
        "Top biosketch bridge candidates:",
        "",
        *md_table(
            top_attending_biosketch_bridges,
            [
                "display_name",
                "bridge_status",
                "training_type",
                "start_year",
                "end_year",
                "ten_year_trend_window",
                "training_line",
                "source_url",
            ],
        ),
        "",
        "Learning: official Penn Faculty Biosketch pages are a high-quality bridge utility when they provide dated Penn residency/fellowship lines for current faculty. They still remain review candidates rather than accepted trend facts because a profile training line is not the same evidence class as a historical roster or alumni record. Postdoctoral research lines are retained as context, not counted as GME trainee-flow bridges.",
        "",
        "## Attending Trend Reconciliation Ledger",
        "",
        f"Trend groups reconciled: {attending_trend_reconciliation_summary.get('trend_rows', 0)}. Review-ready recent bridge rows: {attending_trend_reconciliation_summary.get('review_ready_recent_bridge_rows', 0)}. Groups with current endpoints: {attending_trend_reconciliation_summary.get('groups_with_current_endpoint', 0)}. Groups with Penn-training claims: {attending_trend_reconciliation_summary.get('groups_with_penn_training_claim', 0)}.",
        "",
        "Trend statuses:",
        "",
        *md_table(attending_trend_reconciliation_counts, ["trend_status", "count"]),
        "",
        "Top trend reconciliation rows:",
        "",
        *md_table(
            top_attending_trend_reconciliation,
            [
                "display_name",
                "trend_status",
                "trend_assurance_level",
                "ten_year_trend_window",
                "best_training_type",
                "best_training_end_year",
                "best_source_url",
                "required_next_evidence",
            ],
        ),
        "",
        "Review-ready trend claims:",
        "",
        f"Materialized review-ready trend claims: {attending_trend_review_claims_summary.get('trend_review_claim_rows', 0)}. People: {attending_trend_review_claims_summary.get('trend_review_people', 0)}. Rollup rows: {attending_trend_review_claims_summary.get('trend_review_rollup_rows', 0)}. Display status: {attending_trend_review_claims_summary.get('display_safety_status', '')}.",
        "",
        *md_table(
            top_attending_trend_review_claims,
            [
                "display_name",
                "trend_claim_type",
                "training_type",
                "training_start_year",
                "training_end_year",
                "source_scope",
                "source_url",
                "display_safety_status",
            ],
        ),
        "",
        "Trend acceptance audit:",
        "",
        f"Pre-review acceptance rows: {attending_trend_acceptance_summary.get('trend_acceptance_rows', 0)}. Pre-review accepted facts: {attending_trend_acceptance_summary.get('accepted_trend_fact_rows', 0)}. Reviewer-accepted trend facts: {attending_trend_reviewer_decision_summary.get('accepted_trend_fact_rows', 0)}. Pending reviewer decisions: {attending_trend_reviewer_decision_summary.get('pending_reviewer_decision_rows', 0)}.",
        "",
        *md_table(
            top_attending_trend_acceptance,
            [
                "display_name",
                "training_end_year",
                "acceptance_status",
                "accepted_trend_fact",
                "acceptance_blocker",
                "recommended_next_action",
            ],
        ),
        "",
        "Reviewer decision queue:",
        "",
        f"Queue rows: {attending_trend_reviewer_decision_summary.get('queue_rows', 0)}. Manual decision rows: {attending_trend_reviewer_decision_summary.get('manual_decision_rows', 0)}. Accepted trend facts: {attending_trend_reviewer_decision_summary.get('accepted_trend_fact_rows', 0)}. Pending reviewer decisions: {attending_trend_reviewer_decision_summary.get('pending_reviewer_decision_rows', 0)}.",
        "",
        *md_table(attending_trend_reviewer_decision_counts, ["decision_status", "count"]),
        "",
        *md_table(
            top_attending_trend_reviewer_decisions,
            [
                "display_name",
                "reviewer_decision",
                "decision_status",
                "accepted_trend_fact",
                "decision_blocker",
                "recommended_next_action",
            ],
        ),
        "",
        "Reviewer decision dossiers:",
        "",
        f"Dossier rows: {attending_trend_reviewer_decision_dossier_summary.get('dossier_rows', 0)}. Pending reviewer decisions: {attending_trend_reviewer_decision_dossier_summary.get('pending_reviewer_decision_rows', 0)}. Accepted trend facts: {attending_trend_reviewer_decision_dossier_summary.get('accepted_trend_fact_rows', 0)}. Manual decision templates: {attending_trend_reviewer_decision_dossier_summary.get('manual_decision_template_rows', 0)}.",
        "",
        *md_table(attending_trend_reviewer_decision_dossier_counts, ["decision_status", "count"]),
        "",
        *md_table(
            top_attending_trend_reviewer_decision_dossiers,
            [
                "display_name",
                "decision_status",
                "queue_status",
                "ten_year_trend_window",
                "training_end_year",
                "source_scope",
                "reviewer_decision_key",
                "recommended_next_action",
            ],
        ),
        "",
        "Trend review rollups:",
        "",
        *md_table(
            top_attending_trend_review_rollups,
            [
                "rollup_scope",
                "rollup_value",
                "training_type",
                "training_end_year",
                "claim_count",
                "person_count",
            ],
        ),
        "",
        "Learning: trend analysis needs its own non-mutating acceptance lane. Endpoint evidence plus a Penn-training profile claim is still not enough. Endpoint plus profile claim plus dated official Penn biosketch GME bridge is review-ready for trend acceptance. Accepted trend facts now require a separate reviewer decision row with a matching claim fingerprint and all confirmation fields set, so stale or partial decisions cannot silently promote changed claims.",
        "",
        "## NPPES NPI Registry Candidate Enrichment",
        "",
        f"NPI queries run: {npi_candidate_summary.get('target_queries', 0)}. Candidate rows: {npi_candidate_summary.get('candidate_rows', 0)}. Queries with candidates: {npi_candidate_summary.get('queries_with_candidates', 0)}. Queries with no results: {npi_candidate_summary.get('queries_with_no_results', 0)}. Query errors: {npi_candidate_summary.get('queries_with_error', 0)}.",
        "",
        "Candidate statuses:",
        "",
        *md_table(npi_candidate_status_counts, ["candidate_status", "count"]),
        "",
        "Top NPI primary taxonomies:",
        "",
        *md_table(npi_taxonomy_counts, ["primary_taxonomy", "count"]),
        "",
        "Sample NPI candidates:",
        "",
        *md_table(
            top_npi_candidates,
            [
                "display_name",
                "role",
                "candidate_status",
                "confidence",
                "provider_name",
                "primary_taxonomy",
                "practice_city",
                "practice_state",
                "source_url",
            ],
        ),
        "",
        "Learning: NPPES is an official provider registry and useful as a secondary identity anchor, especially when exact name, PA/Philadelphia location, physician or trainee taxonomy, and program specialty agree. It is not roster truth. Residents and fellows may have missing, stale, student-training, or non-Penn practice data, and name collisions are expected.",
        "",
        "## Enrichment Coverage Audit",
        "",
        f"People audited: {enrichment_coverage_summary.get('person_rows', 0)}. Program/role groups audited: {enrichment_coverage_summary.get('program_rows', 0)}. Average coverage score: {enrichment_coverage_summary.get('avg_coverage_score', 0)}.",
        "",
        "Coverage bands:",
        "",
        *md_table(enrichment_coverage_bands, ["coverage_band", "count"]),
        "",
        "Recommended next actions:",
        "",
        *md_table(enrichment_next_actions, ["recommended_next_action", "count"]),
        "",
        "Lowest-scoring program/role surfaces:",
        "",
        *md_table(
            weakest_program_coverage,
            [
                "program_name",
                "role",
                "person_count",
                "avg_coverage_score",
                "profile_coverage_rate",
                "medical_school_coverage_rate",
                "article_candidate_coverage_rate",
                "npi_candidate_coverage_rate",
                "npi_needs_review_coverage_rate",
                "top_recommended_next_action",
            ],
        ),
        "",
        "Learning: coverage needs to be audited separately from evidence acceptance. This pass shows where the recursive loop should work next: official profile search, organization alias review, article-level research collection, and high-priority reconciliation.",
        "",
        "## Utility Observations",
        "",
        *md_table(utility_observations, ["utility_key", "sample_size", "candidate_claims", "accepted_claims", "rejected_claims", "ambiguous_claims", "metrics_json"]),
        "",
        "## OpenAlex Feature Distribution",
        "",
        *md_table(openalex_features, ["match_features_json", "count", "avg_confidence"]),
        "",
        openalex_learning,
        "",
        "## ORCID Public Profile Reconciliation",
        "",
        f"ORCID profiles considered: {orcid_profile_summary.get('orcids_considered', 0)}. Profile candidates: {orcid_profile_summary.get('durable_claim_rows', 0)}. People with candidates: {orcid_profile_summary.get('people_with_durable_claims', 0)}.",
        "",
        "ORCID candidate statuses:",
        "",
        *md_table(
            [
                {"status": status, "count": count}
                for status, count in sorted((orcid_profile_summary.get("by_status") or {}).items())
            ],
            ["status", "count"],
        ),
        "",
        "ORCID feature distribution:",
        "",
        *md_table(orcid_features, ["match_features_json", "count", "avg_confidence"]),
        "",
        "ORCID work candidate statuses:",
        "",
        *md_table(
            [
                {"status": status, "count": count}
                for status, count in sorted((orcid_work_summary.get("by_status") or {}).items())
            ],
            ["status", "count"],
        ),
        "",
        "ORCID work feature distribution:",
        "",
        *md_table(orcid_work_features, ["match_features_json", "count", "avg_confidence"]),
        "",
        "Learning: ORCID is useful as a secondary identity and publication-corroboration layer when it is linked from a high-confidence author candidate. In this Penn sample it exposed public works far more often than public education/employment; DOI/PMID-level ORCID works should seed PubMed/OpenAlex/Crossref article-metadata reconciliation rather than replace official profile/background sources.",
        "",
        "## PubMed Feature Distribution",
        "",
        *md_table(pubmed_features, ["match_features_json", "count", "avg_confidence"]),
        "",
        "Learning: PubMed E-utilities is a strong article database, but author-query search is a weak identity resolver. It should be used after candidate author identity is constrained by OpenAlex/ORCID/profile context, or at article-level with affiliation/coauthor checks.",
        "",
        "## PubMed Article-Level Reconciliation",
        "",
        f"Bounded query claims considered: {pubmed_article_summary.get('query_claims_considered', 0)}. Unique PMIDs fetched: {pubmed_article_summary.get('unique_pmids_fetched', 0)}. Article candidates: {pubmed_article_summary.get('article_claims', 0)}.",
        "",
        "Article candidate statuses:",
        "",
        *md_table(
            [
                {"status": status, "count": count}
                for status, count in sorted((pubmed_article_summary.get("by_status") or {}).items())
            ],
            ["status", "count"],
        ),
        "",
        "Article candidate feature distribution:",
        "",
        *md_table(pubmed_article_features, ["match_features_json", "count", "avg_confidence"]),
        "",
        "Learning: article-level PubMed XML is materially better than author-query counts because it exposes the target author, affiliation strings, publication year, journal/title, and topic hints. It is still candidate evidence: many records have one strong non-name anchor, but acceptance should require at least two independent anchors or a human review step.",
        "",
        "## ORCID-Seeded PubMed Article Reconciliation",
        "",
        f"ORCID work claims considered: {orcid_pubmed_article_summary.get('orcid_work_claims_considered', 0)}. Unique PMIDs fetched: {orcid_pubmed_article_summary.get('unique_pmids_fetched', 0)}. Article candidates: {orcid_pubmed_article_summary.get('article_claims', 0)}. People with candidates: {orcid_pubmed_article_summary.get('people_with_article_claims', 0)}.",
        "",
        "ORCID-seeded article statuses:",
        "",
        *md_table(
            [
                {"status": status, "count": count}
                for status, count in sorted((orcid_pubmed_article_summary.get("by_status") or {}).items())
            ],
            ["status", "count"],
        ),
        "",
        "ORCID-seeded article feature distribution:",
        "",
        *md_table(orcid_pubmed_article_features, ["match_features_json", "count", "avg_confidence"]),
        "",
        "Learning: ORCID-seeded PubMed reconciliation is higher precision than name-only PubMed search because each article starts with a stable ORCID work identifier, then checks PubMed author names, author position, DOI/PMID consistency, affiliations, and topic context. It remains review-only because ORCID ownership and same-person linkage can still be wrong or stale.",
        "",
        "## Official Trainee Profile Enrichment",
        "",
        f"Roster-linked trainee profiles with text: {trainee_profile_summary.get('profiles_with_text', 0)}. Claims extracted: {trainee_profile_summary.get('claims', 0)}. People with profile claims: {trainee_profile_summary.get('people_with_claims', 0)}.",
        "",
        "Profile claim counts:",
        "",
        *md_table(trainee_profile_counts, ["status", "claim_type", "count", "avg_confidence"]),
        "",
        "Display-safety policy counts:",
        "",
        *md_table(trainee_profile_safety_counts, ["display_safety_status", "count"]),
        "",
        "Learning: roster-linked official profile pages are strong identity/profile-location anchors and can expose education, residency background, research or career interests, and personal context. The URL fact is accepted when linked from an official roster, but extracted profile fields remain candidate enrichment with display-safety metadata, especially hobbies, home-state, family, and free-text personal snippets.",
        "",
        "## Career / Attending Trend Candidates",
        "",
        *md_table(career_events, ["event_type", "status", "count", "avg_confidence"]),
        "",
        "Attending profile enrichment:",
        "",
        f"Profiles attempted: {attending_profile_summary.get('profiles_attempted', 0)}. Usable profiles: {attending_profile_summary.get('usable_profiles', 0)}. Claims extracted: {attending_profile_summary.get('claims', 0)}.",
        "",
        *md_table(
            [
                {"claim_type": claim_type, "count": count}
                for claim_type, count in sorted((attending_profile_summary.get("by_claim_type") or {}).items())
            ],
            ["claim_type", "count"],
        ),
        "",
        "Learning: current faculty pages, provider profiles, and alumni/outcome pages should feed a career-event layer, not the core current-trainee roster. Official profile training-history claims are stronger than source-level outcome prose, but they still remain candidates until reconciled to a prior Penn trainee identity or another independent anchor.",
        "",
        "## Public Contact Evidence",
        "",
        *md_table(contact_counts, ["contact_type", "contact_scope", "verification_status", "status", "count", "avg_confidence"]),
        "",
        *md_table(contact_assurance_counts, ["assurance_status", "display_safety_status", "required_next_check", "count", "avg_confidence"]),
        "",
        *md_table(contact_reviewer_decision_counts, ["decision_status", "reviewer_decision", "count"]),
        "",
        "Reviewer decision dossiers:",
        "",
        f"Dossier rows: {contact_reviewer_dossier_summary.get('dossier_rows', 0)}. Pending decisions: {contact_reviewer_dossier_summary.get('pending_reviewer_decision_rows', 0)}. Review-ready rows: {contact_reviewer_dossier_summary.get('ready_for_reviewer_verification_rows', 0)}.",
        "",
        *md_table(
            top_contact_reviewer_dossiers,
            [
                "display_name",
                "role",
                "contact_type",
                "domain_status",
                "queue_status",
                "decision_status",
                "decision_blocker",
                "recommended_next_action",
            ],
        ),
        "",
        *md_table(accepted_contact_counts, ["contact_type", "display_safety_status", "operational_use_status", "count"]),
        "",
        "Learning: public contact channels belong in a separate evidence table because a person can have multiple public contacts from sources with different assurance levels. The assurance layer keeps public contacts as candidates until current-source verification, and it catches domain or format anomalies before display or outreach use. Verified contact facts require explicit reviewer acceptance, current official reobservation, and matching contact fingerprints.",
        "",
        "## Reconciliation Rule Update",
        "",
        "For the next pass, accept research enrichment only when at least two non-name anchors agree. Examples: official profile link plus ORCID; OpenAlex Penn affiliation plus specialty-topic match; PubMed affiliation plus coauthor cluster; NPI specialty/location plus official profile.",
        "",
        "## Source References",
        "",
        "- OpenAlex institutions documentation notes that all OpenAlex institutions have ROR IDs and that parsing author affiliations is nontrivial: https://docs.openalex.org/api-entities/institutions",
        "- NCBI E-utilities are the public API for Entrez databases including PubMed: https://www.ncbi.nlm.nih.gov/home/develop/api/",
        "- ORCID supports organization identifiers including ROR for affiliations: https://info.orcid.org/documentation/integration-guide/working-with-organization-identifiers/",
        "- NPPES provides an official public read API for NPI Registry data: https://npiregistry.cms.hhs.gov/api-page",
        "- ClinicalTrials.gov provides an official API and OpenAPI specification: https://clinicaltrials.gov/data-about-studies/learn-about-api",
        "- WDOMS is a searchable directory of undergraduate medical education programs; listing confirms existence but not accreditation or endorsement unless stated: https://wfme.org/world-directory/",
    ]
    (REPORTS / "penn-source-quality-learnings-2026-06-02.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print("wrote source quality report")


if __name__ == "__main__":
    main()
