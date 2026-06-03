#!/usr/bin/env python3
"""Build an empirical scorecard for source utilities and evidence surfaces."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"
SCORECARD_CSV = ARTIFACTS / "source_utility_scorecard.csv"
SCORECARD_JSON = ARTIFACTS / "source_utility_scorecard.json"
SCORECARD_SUMMARY = ARTIFACTS / "source_utility_scorecard_summary.json"

FIELDNAMES = [
    "scorecard_key",
    "utility_key",
    "utility_label",
    "source_family",
    "claim_surface",
    "input_records",
    "output_records",
    "accepted_records",
    "candidate_records",
    "needs_review_records",
    "review_ready_records",
    "discovery_only_records",
    "low_signal_records",
    "coverage_gap_records",
    "blocked_records",
    "score",
    "quality_band",
    "strengths",
    "limitations",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def existing_rows() -> dict[str, dict]:
    if not SCORECARD_CSV.exists():
        return {}
    with SCORECARD_CSV.open(newline="", encoding="utf-8") as f:
        return {row["scorecard_key"]: row for row in csv.DictReader(f)}


def stable_audited_at(existing: dict[str, dict], row: dict, new_value: str) -> str:
    prior = existing.get(row["scorecard_key"])
    if not prior:
        return new_value
    stable_fields = [field for field in FIELDNAMES if field != "audited_at"]
    for field in stable_fields:
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return new_value
    return prior.get("audited_at") or new_value


def scalar(conn: sqlite3.Connection, query: str, params: tuple = ()) -> int:
    value = conn.execute(query, params).fetchone()[0]
    return int(value or 0)


def counter_query(conn: sqlite3.Connection, query: str) -> dict[str, int]:
    return {str(row[0] or ""): int(row[1] or 0) for row in conn.execute(query)}


def quality_band(score: float) -> str:
    if score >= 85:
        return "high_utility"
    if score >= 70:
        return "strong_with_known_limits"
    if score >= 55:
        return "useful_candidate_layer"
    if score >= 35:
        return "discovery_or_review_only"
    return "blocked_or_low_current_utility"


def make_row(
    *,
    scorecard_key: str,
    utility_key: str | None,
    utility_label: str,
    source_family: str,
    claim_surface: str,
    input_records: int,
    output_records: int,
    accepted_records: int = 0,
    candidate_records: int = 0,
    needs_review_records: int = 0,
    review_ready_records: int = 0,
    discovery_only_records: int = 0,
    low_signal_records: int = 0,
    coverage_gap_records: int = 0,
    blocked_records: int = 0,
    score: float = 0.0,
    strengths: list[str] | None = None,
    limitations: list[str] | None = None,
    recommended_next_action: str = "",
    evidence: dict | None = None,
) -> dict:
    return {
        "scorecard_key": scorecard_key,
        "utility_key": utility_key or "",
        "utility_label": utility_label,
        "source_family": source_family,
        "claim_surface": claim_surface,
        "input_records": input_records,
        "output_records": output_records,
        "accepted_records": accepted_records,
        "candidate_records": candidate_records,
        "needs_review_records": needs_review_records,
        "review_ready_records": review_ready_records,
        "discovery_only_records": discovery_only_records,
        "low_signal_records": low_signal_records,
        "coverage_gap_records": coverage_gap_records,
        "blocked_records": blocked_records,
        "score": round(score, 1),
        "quality_band": quality_band(score),
        "strengths": "; ".join(strengths or []),
        "limitations": "; ".join(limitations or []),
        "recommended_next_action": recommended_next_action,
        "evidence_json": dumps(evidence or {}),
        "audited_at": "",
    }


def score_rows(conn: sqlite3.Connection) -> list[dict]:
    people = scalar(conn, "SELECT COUNT(*) FROM people")
    memberships = scalar(conn, "SELECT COUNT(*) FROM person_program_memberships")
    accepted_training_claims = scalar(conn, "SELECT COUNT(*) FROM evidence_claims WHERE status = 'accepted'")
    official_sources = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM sources
        WHERE source_type IN (
          'official_affiliated_roster',
          'official_gap_roster',
          'official_public_student_directory',
          'official_roster_or_context'
        )
        """,
    )
    official_programs = scalar(conn, "SELECT COUNT(*) FROM official_program_universe")
    official_covered = scalar(
        conn,
        "SELECT COUNT(*) FROM official_program_coverage_audit WHERE coverage_status = 'covered_current_roster'",
    )
    official_gaps = scalar(
        conn,
        "SELECT COUNT(*) FROM official_program_coverage_audit WHERE coverage_status != 'covered_current_roster'",
    )
    coverage_assurance_summary = read_json(
        ARTIFACTS / "official_program_coverage_assurance_summary.json",
        {},
    )
    coverage_action_queue_summary = read_json(
        ARTIFACTS / "official_program_coverage_action_queue_summary.json",
        {},
    )
    coverage_dossier_summary = read_json(
        ARTIFACTS / "official_program_coverage_dossier_summary.json",
        {},
    )
    alias_review_packets_summary = read_json(
        ARTIFACTS / "official_program_alias_review_packets_summary.json",
        {},
    )
    alias_reviewer_decision_summary = read_json(
        ARTIFACTS / "official_program_alias_reviewer_decision_summary.json",
        {},
    )
    level_4_covered_programs = int(coverage_assurance_summary.get("level_4_program_rows") or 0)
    level_4_covered_people = int(coverage_assurance_summary.get("level_4_people_count") or 0)
    alias_review_programs = int(coverage_assurance_summary.get("alias_review_program_rows") or 0)
    assurance_open_gaps = int(coverage_assurance_summary.get("open_gap_rows") or official_gaps)
    gap_reasons = counter_query(
        conn,
        "SELECT gap_reason_status, COUNT(*) FROM official_program_gap_reason_audit GROUP BY gap_reason_status",
    )
    alias_rows = scalar(conn, "SELECT COUNT(*) FROM official_program_alias_reconciliation_candidates")
    alias_mutations = scalar(
        conn,
        "SELECT COUNT(*) FROM official_program_alias_reconciliation_candidates WHERE coverage_mutation_allowed = 1",
    )
    gap_sources = scalar(conn, "SELECT COUNT(*) FROM official_program_source_candidates")
    roster_candidates = scalar(
        conn,
        "SELECT COUNT(*) FROM official_program_source_candidates WHERE candidate_status = 'roster_source_candidate'",
    )
    program_identifier_candidates = scalar(conn, "SELECT COUNT(*) FROM program_identifier_candidates")
    accepted_program_identifiers = scalar(conn, "SELECT COUNT(*) FROM official_program_identifiers")
    review_program_identifiers = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM program_identifier_reconciliation
        WHERE reconciliation_status != 'accepted_official_program_identifier'
        """,
    )
    no_acgme_identifiers = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM program_identifier_candidates
        WHERE candidate_status = 'no_acgme_identifier_found'
        """,
    )
    acgme_observation_summary = read_json(ARTIFACTS / "program_identifier_candidate_summary.json", {})
    acgme_reconciliation_summary = read_json(ARTIFACTS / "program_identifier_reconciliation_summary.json", {})
    program_lifecycle_consistency_summary = read_json(
        ARTIFACTS / "program_lifecycle_consistency_summary.json",
        {},
    )
    program_lifecycle_duration_summary = read_json(
        ARTIFACTS / "program_lifecycle_duration_evidence_summary.json",
        {},
    )
    program_lifecycle_duration_reviewer_summary = read_json(
        ARTIFACTS / "program_lifecycle_duration_reviewer_decision_summary.json",
        {},
    )
    program_lifecycle_duration_rows = scalar(conn, "SELECT COUNT(*) FROM program_lifecycle_duration_evidence")
    accepted_program_lifecycle_duration_rows = scalar(
        conn,
        "SELECT COUNT(*) FROM accepted_program_lifecycle_duration_mappings",
    )
    rejected_program_lifecycle_duration_rows = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM program_lifecycle_duration_reviewer_decision_audit
        WHERE decision_status = 'rejected_by_reviewer'
        """,
    )
    program_lifecycle_duration_ready = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM program_lifecycle_duration_evidence
        WHERE duration_evidence_status = 'reviewer_ready_duration_lifecycle_candidate'
        """,
    )
    program_lifecycle_duration_review = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM program_lifecycle_duration_evidence
        WHERE duration_evidence_status IN (
          'conflicting_duration_evidence_review',
          'duration_source_program_mismatch_review'
        )
        """,
    )
    program_lifecycle_duration_blocked = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM program_lifecycle_duration_evidence
        WHERE duration_evidence_status IN (
          'duration_source_unavailable',
          'no_explicit_duration_evidence_found'
        )
        """,
    )
    gap_roster_people = read_json(ARTIFACTS / "penn_gme_gap_roster_summary.json", {})
    roster_extracted = int(gap_roster_people.get("person_records") or 0)
    roster_sources_attempted = int(gap_roster_people.get("sources_attempted") or 0)
    roster_sources_with_records = int(gap_roster_people.get("sources_with_records") or 0)
    gap_roster_reconciliation_summary = read_json(ARTIFACTS / "official_gap_roster_reconciliation_summary.json", {})
    denominator_linked_records = int(gap_roster_reconciliation_summary.get("official_linked_records_extracted") or 0)
    seed_without_denominator_records = int(gap_roster_reconciliation_summary.get("seed_without_denominator_key_records") or 0)
    gap_roster_program_resolution_summary = read_json(
        ARTIFACTS / "official_gap_roster_program_resolution_summary.json",
        {},
    )
    denominator_resolution_records = int(
        gap_roster_program_resolution_summary.get("denominator_mutation_allowed_records") or 0
    )
    denominator_resolution_review_records = int(
        gap_roster_program_resolution_summary.get("review_required_records") or 0
    )

    discovery_by_class = counter_query(
        conn,
        """
        SELECT classification, COUNT(*)
        FROM sources
        WHERE source_type = 'penn_affiliated_source_discovery'
        GROUP BY classification
        """,
    )
    discovery_total = sum(discovery_by_class.values())
    broad_trainee_candidates = discovery_by_class.get("trainee_roster_candidate", 0)
    broad_context = discovery_by_class.get("program_context", 0)

    med_student_source_rows = scalar(conn, "SELECT COUNT(*) FROM medical_student_source_audit")
    med_student_loaded = scalar(
        conn,
        """
        SELECT COALESCE(SUM(loaded_person_count), 0)
        FROM medical_student_source_audit
        WHERE capture_status = 'accepted_public_mstp_roster'
        """,
    )
    med_student_protected = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM medical_student_source_audit
        WHERE capture_status = 'protected_no_public_roster_records'
        """,
    )
    med_student_crosscheck = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM medical_student_source_audit
        WHERE capture_status = 'public_md_phd_crosscheck_candidate'
        """,
    )
    med_student_review = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM medical_student_source_audit
        WHERE capture_status IN ('unreachable_review', 'review_required')
        """,
    )
    med_student_audit_summary = read_json(ARTIFACTS / "penn_med_student_source_audit_summary.json", {})

    pubmed_author_claims = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'pubmed_author_query_candidate'
        """,
    )
    pubmed_article_claims = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'pubmed_article_candidate'
        """,
    )
    pubmed_article_needs_review = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'pubmed_article_candidate'
          AND status = 'needs_review'
        """,
    )
    pubmed_article_candidate = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'pubmed_article_candidate'
          AND status = 'candidate'
        """,
    )
    orcid_pubmed_article_claims = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'orcid_pubmed_article_candidate'
        """,
    )
    orcid_pubmed_article_needs_review = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'orcid_pubmed_article_candidate'
          AND status = 'needs_review'
        """,
    )
    orcid_pubmed_article_candidate = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
          AND claim_type = 'orcid_pubmed_article_candidate'
          AND status = 'candidate'
        """,
    )

    decisions = read_csv(ARTIFACTS / "evidence_reconciliation_decisions.csv")
    decision_counts = Counter(row.get("decision", "") for row in decisions)
    pubmed_review_ready = sum(
        1
        for row in decisions
        if row.get("claim_type") == "pubmed_article_candidate"
        and row.get("decision") in {"review_ready_high_anchor", "review_ready_training_topic_anchor"}
    )
    pubmed_secondary = sum(
        1
        for row in decisions
        if row.get("claim_type") == "pubmed_article_candidate"
        and row.get("decision") == "needs_secondary_identity_anchor"
    )
    pubmed_low_signal = sum(
        1
        for row in decisions
        if row.get("claim_type") == "pubmed_article_candidate"
        and row.get("decision") == "low_signal_candidate"
    )
    pubmed_discovery_only = decision_counts.get("discovery_only", 0)
    orcid_pubmed_review_ready = sum(
        1
        for row in decisions
        if row.get("claim_type") == "orcid_pubmed_article_candidate"
        and row.get("decision")
        in {"review_ready_orcid_seeded_article", "review_ready_high_anchor", "review_ready_training_topic_anchor"}
    )
    orcid_pubmed_secondary = sum(
        1
        for row in decisions
        if row.get("claim_type") == "orcid_pubmed_article_candidate"
        and row.get("decision") == "needs_secondary_identity_anchor"
    )
    orcid_pubmed_low_signal = sum(
        1
        for row in decisions
        if row.get("claim_type") == "orcid_pubmed_article_candidate"
        and row.get("decision") == "low_signal_candidate"
    )

    packets_summary = read_json(ARTIFACTS / "person_evidence_review_packet_summary.json", {})
    packets_by_status = packets_summary.get("by_packet_status") or {}
    review_ready_packets = int(packets_summary.get("review_ready_packets") or 0)
    secondary_packets = int(packets_summary.get("needs_secondary_anchor_packets") or 0)
    enrichment_acceptance_summary = read_json(ARTIFACTS / "enrichment_acceptance_summary.json", {})
    machine_acceptance_candidate_rows = int(enrichment_acceptance_summary.get("machine_acceptance_candidate_rows") or 0)
    machine_acceptance_candidate_people = int(enrichment_acceptance_summary.get("machine_acceptance_candidate_people") or 0)
    acceptance_review_ready_publications = int(enrichment_acceptance_summary.get("review_ready_publication_rows") or 0)
    acceptance_secondary_identity_anchors = int(enrichment_acceptance_summary.get("secondary_identity_anchor_rows") or 0)
    accepted_enrichment_summary = read_json(ARTIFACTS / "accepted_enrichment_summary.json", {})
    accepted_enrichment_rows = int(accepted_enrichment_summary.get("accepted_enrichment_rows") or 0)
    accepted_enrichment_people = int(accepted_enrichment_summary.get("accepted_people") or 0)
    warehouse_reproducibility_summary = read_json(ARTIFACTS / "warehouse_reproducibility_summary.json", {})
    reproducibility_artifact_rows = int(warehouse_reproducibility_summary.get("artifact_rows") or 0)
    reproducibility_mismatch_rows = int(warehouse_reproducibility_summary.get("row_count_mismatch_rows") or 0)
    reproducibility_missing_rows = int(warehouse_reproducibility_summary.get("required_missing_artifacts") or 0)
    reproducibility_binary_warnings = int(warehouse_reproducibility_summary.get("binary_size_warning_rows") or 0)
    reproducibility_sqlite_git_tracked = bool(warehouse_reproducibility_summary.get("sqlite_git_tracked"))
    reproducibility_sqlite_storage_policy = warehouse_reproducibility_summary.get("sqlite_storage_policy") or ""
    evidence_temporal_contract_summary = read_json(ARTIFACTS / "evidence_temporal_contract_summary.json", {})
    evidence_contract_rows = scalar(conn, "SELECT COUNT(*) FROM evidence_temporal_contracts")
    evidence_contract_rollups = scalar(conn, "SELECT COUNT(*) FROM evidence_temporal_contract_rollups")
    evidence_contract_status = counter_query(
        conn,
        "SELECT current_contract_status, COUNT(*) FROM evidence_temporal_contracts GROUP BY current_contract_status",
    )
    evidence_contract_families = counter_query(
        conn,
        "SELECT fact_family, COUNT(*) FROM evidence_temporal_contracts GROUP BY fact_family",
    )
    evidence_contract_stale = evidence_contract_status.get("stale_refresh_required", 0)
    evidence_contract_review_bound = evidence_contract_status.get("review_bound_not_accepted_truth", 0)
    evidence_contract_durable = evidence_contract_status.get("durable_until_contradicted", 0)
    evidence_contract_refresh_bound = evidence_contract_status.get("fresh_until_stale_after", 0)

    openalex_obs = conn.execute(
        """
        SELECT sample_size, candidate_claims, accepted_claims, ambiguous_claims, metrics_json
        FROM source_quality_observations
        WHERE utility_key = 'openalex_author_search'
        ORDER BY observed_at DESC
        LIMIT 1
        """
    ).fetchone()
    openalex_blocked = 1 if openalex_obs and json.loads(openalex_obs["metrics_json"] or "{}").get("rate_limit_observed") else 0
    orcid_obs = conn.execute(
        """
        SELECT sample_size, candidate_claims, accepted_claims, ambiguous_claims, metrics_json
        FROM source_quality_observations
        WHERE utility_key = 'orcid_public_api'
        ORDER BY observed_at DESC
        LIMIT 1
        """
    ).fetchone()
    orcid_claims = scalar(conn, "SELECT COUNT(*) FROM evidence_claims WHERE source_key = 'orcid_public_api'")
    orcid_candidate = scalar(conn, "SELECT COUNT(*) FROM evidence_claims WHERE source_key = 'orcid_public_api' AND status = 'candidate'")
    orcid_needs_review = scalar(conn, "SELECT COUNT(*) FROM evidence_claims WHERE source_key = 'orcid_public_api' AND status = 'needs_review'")
    orcid_secondary_anchor = decision_counts.get("orcid_secondary_identity_anchor_review", 0)
    orcid_partial_anchor = decision_counts.get("orcid_profile_with_partial_anchor", 0)
    orcid_low_signal = decision_counts.get("orcid_low_signal_candidate", 0)
    orcid_work_review = decision_counts.get("orcid_work_publication_review", 0)
    orcid_work_candidate = decision_counts.get("orcid_work_publication_candidate", 0)
    orcid_work_low_signal = decision_counts.get("orcid_work_low_signal_candidate", 0)

    attending_profile_events = scalar(conn, "SELECT COUNT(*) FROM career_events WHERE source_key LIKE 'penn_attending_profile_%'")
    attending_profile_review_ready = decision_counts.get("attending_training_claim_review_ready", 0)
    attending_profile_context = decision_counts.get("profile_context_candidate", 0)
    current_attending_endpoint = decision_counts.get("current_attending_endpoint_candidate", 0)
    trainee_profile_summary = read_json(ARTIFACTS / "penn_trainee_profile_summary.json", {})
    trainee_profile_claims = scalar(
        conn,
        "SELECT COUNT(*) FROM evidence_claims WHERE source_type = 'official_trainee_profile'",
    )
    trainee_profile_accepted = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_type = 'official_trainee_profile'
          AND status = 'accepted'
        """,
    )
    trainee_profile_candidate = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE source_type = 'official_trainee_profile'
          AND status = 'candidate'
        """,
    )
    trainee_profile_discovery_summary = read_json(ARTIFACTS / "trainee_profile_discovery_summary.json", {})
    official_profile_reobservation_summary = read_json(ARTIFACTS / "official_profile_reobservation_summary.json", {})
    official_profile_reviewer_decision_summary = read_json(ARTIFACTS / "official_profile_reviewer_decision_summary.json", {})
    official_profile_generic_route_rows = int(
        official_profile_reobservation_summary.get("generic_page_resolution_rows") or 0
    )
    official_profile_fresh_context_rows = int(
        official_profile_reobservation_summary.get("fresh_profile_context_rows") or 0
    )
    trainee_profile_discovery_claims = scalar(
        conn,
        "SELECT COUNT(*) FROM evidence_claims WHERE claim_type = 'official_profile_url_candidate'",
    )
    trainee_profile_discovery_needs_review = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM evidence_claims
        WHERE claim_type = 'official_profile_url_candidate'
          AND status = 'needs_review'
        """,
    )
    trainee_profile_discovery_candidates = scalar(conn, "SELECT COUNT(*) FROM trainee_profile_discovery_candidates")
    trainee_profile_discovery_low_signal = int(
        (trainee_profile_discovery_summary.get("by_candidate_status") or {}).get("low_signal_search_result") or 0
    )
    prior_training_discovery_summary = read_json(ARTIFACTS / "prior_training_discovery_summary.json", {})
    prior_training_tasks = int(prior_training_discovery_summary.get("tasks_considered") or 0)
    prior_training_queries = int(prior_training_discovery_summary.get("query_rows") or 0)
    prior_training_candidates = int(prior_training_discovery_summary.get("candidate_rows") or 0)
    prior_training_claims = scalar(
        conn,
        "SELECT COUNT(*) FROM evidence_claims WHERE source_type = 'prior_training_background_discovery'",
    )
    trend_summary = read_json(ARTIFACTS / "attending_trend_linkage_summary.json", {})
    trend_linkage = trend_summary.get("by_linkage_status") or {}
    historical_summary = read_json(ARTIFACTS / "attending_historical_link_discovery_summary.json", {})
    historical_candidates = int(historical_summary.get("candidate_rows") or 0)
    historical_actionable = sum(
        int(value or 0)
        for key, value in (historical_summary.get("by_candidate_status") or {}).items()
        if key
        in {
            "historical_link_source_candidate",
            "historical_roster_or_alumni_candidate",
            "historical_training_search_candidate",
            "identity_bridge_candidate",
            "profile_or_cv_candidate",
            "profile_or_cv_bridge_candidate",
        }
    )
    current_context_only = sum(
        int(value or 0)
        for key, value in (historical_summary.get("by_candidate_status") or {}).items()
        if key in {"current_profile_training_context_candidate", "current_profile_context_candidate"}
    )
    biosketch_summary = read_json(ARTIFACTS / "attending_biosketch_bridge_summary.json", {})
    biosketch_rows = scalar(conn, "SELECT COUNT(*) FROM attending_biosketch_bridge_candidates")
    biosketch_recent_bridge = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM attending_biosketch_bridge_candidates
        WHERE bridge_status = 'dated_recent_official_biosketch_training_bridge_candidate'
        """,
    )
    biosketch_gme_context = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM attending_biosketch_bridge_candidates
        WHERE training_type IN ('fellowship', 'residency', 'internship')
        """,
    )
    biosketch_groups = scalar(
        conn,
        "SELECT COUNT(DISTINCT event_group_key) FROM attending_biosketch_bridge_candidates",
    )
    trend_reconciliation_rows = scalar(conn, "SELECT COUNT(*) FROM attending_trend_reconciliation")
    trend_reconciliation_review_ready = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM attending_trend_reconciliation
        WHERE trend_status = 'review_ready_official_biosketch_bridge'
        """,
    )
    trend_reconciliation_needs_bridge = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM attending_trend_reconciliation
        WHERE trend_status IN (
          'profile_claim_still_needs_dated_bridge',
          'current_endpoint_needs_training_claim'
        )
        """,
    )
    trend_reconciliation_summary = read_json(ARTIFACTS / "attending_trend_reconciliation_summary.json", {})
    trend_review_claims_summary = read_json(ARTIFACTS / "attending_trend_review_claims_summary.json", {})
    trend_acceptance_summary = read_json(ARTIFACTS / "attending_trend_acceptance_summary.json", {})
    trend_reviewer_decision_summary = read_json(ARTIFACTS / "attending_trend_reviewer_decision_summary.json", {})
    trend_dossier_summary = read_json(ARTIFACTS / "attending_trend_dossier_summary.json", {})
    trend_review_claim_rows = int(trend_review_claims_summary.get("trend_review_claim_rows") or 0)
    trend_review_rollup_rows = int(trend_review_claims_summary.get("trend_review_rollup_rows") or 0)
    accepted_trend_fact_rows = int(trend_reviewer_decision_summary.get("accepted_trend_fact_rows") or 0)
    pending_trend_reviewer_decisions = int(trend_reviewer_decision_summary.get("pending_reviewer_decision_rows") or 0)
    npi_summary = read_json(ARTIFACTS / "npi_candidate_summary.json", {})
    npi_observations = scalar(conn, "SELECT COUNT(*) FROM npi_source_observations")
    npi_candidate_rows = scalar(conn, "SELECT COUNT(*) FROM npi_candidate_claims")
    npi_review_ready = scalar(
        conn,
        "SELECT COUNT(*) FROM npi_candidate_claims WHERE candidate_status = 'needs_review'",
    )
    npi_candidate = scalar(
        conn,
        "SELECT COUNT(*) FROM npi_candidate_claims WHERE candidate_status = 'candidate'",
    )
    npi_low_signal = scalar(
        conn,
        "SELECT COUNT(*) FROM npi_candidate_claims WHERE candidate_status = 'low_signal_npi_candidate'",
    )

    contact_count = scalar(conn, "SELECT COUNT(*) FROM person_contacts")
    contact_by_verification = counter_query(
        conn,
        "SELECT verification_status, COUNT(*) FROM person_contacts GROUP BY verification_status",
    )
    contact_assurance_summary = read_json(ARTIFACTS / "contact_assurance_summary.json", {})
    contact_verification_contract_summary = read_json(ARTIFACTS / "contact_verification_contract_summary.json", {})
    contact_reobservation_summary = read_json(ARTIFACTS / "contact_reobservation_summary.json", {})
    contact_reviewer_decision_summary = read_json(
        ARTIFACTS / "contact_verification_reviewer_decision_summary.json",
        {},
    )
    contact_assurance_status = contact_assurance_summary.get("by_assurance_status") or {}
    contact_review_required = int(contact_assurance_summary.get("review_required_rows") or 0)
    contact_fresh_reobserved = int(contact_reobservation_summary.get("fresh_same_value_rows") or 0)
    contact_value_absent = int(contact_reobservation_summary.get("value_absent_rows") or 0)
    contact_source_fetch_problem = int(contact_reobservation_summary.get("source_fetch_problem_rows") or 0)
    contact_verified = scalar(conn, "SELECT COUNT(*) FROM accepted_verified_contact_facts")

    org_count = scalar(conn, "SELECT COUNT(*) FROM organizations")
    org_review = scalar(conn, "SELECT COUNT(*) FROM organizations WHERE resolver_status = 'cleaned_label'")
    org_seeded = scalar(conn, "SELECT COUNT(*) FROM organizations WHERE resolver_status = 'seeded_alias'")
    org_aliases = scalar(conn, "SELECT COUNT(*) FROM organization_aliases")
    org_identifiers = scalar(conn, "SELECT COUNT(*) FROM organization_identifiers")
    org_identifier_candidates = scalar(conn, "SELECT COUNT(*) FROM organization_identifier_candidates")
    org_identifier_candidate_summary = read_json(ARTIFACTS / "organization_identifier_candidate_summary.json", {})

    state_rows = scalar(conn, "SELECT COUNT(*) FROM person_training_states")
    state_machine_summary = read_json(ARTIFACTS / "training_state_machine_summary.json", {})
    machine_status = state_machine_summary.get("by_state_machine_status") or {}
    longitudinal_summary = read_json(ARTIFACTS / "longitudinal_change_readiness_summary.json", {})
    readiness_status = longitudinal_summary.get("by_readiness_status") or {}
    lifecycle_assurance_summary = read_json(ARTIFACTS / "training_lifecycle_assurance_summary.json", {})
    transition_plan_summary = read_json(ARTIFACTS / "training_state_transition_plan_summary.json", {})
    transition_policy_lanes = transition_plan_summary.get("by_policy_lane") or {}
    enrichment_queue_summary = read_json(ARTIFACTS / "person_enrichment_queue_summary.json", {})
    enrichment_queue_rows = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_work_queue")
    enrichment_queue_people = scalar(conn, "SELECT COUNT(DISTINCT person_key) FROM person_enrichment_work_queue")
    enrichment_queue_high = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_work_queue WHERE priority_band IN ('critical', 'high')",
    )
    enrichment_queue_review_or_refresh = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM person_enrichment_work_queue
        WHERE fresh_observation_required = 1
           OR policy_lane IN ('manual_review_required', 'source_refresh_required')
        """,
    )
    execution_readiness_summary = read_json(ARTIFACTS / "person_enrichment_execution_readiness_summary.json", {})
    execution_batch_summary = read_json(ARTIFACTS / "person_enrichment_execution_batch_summary.json", {})
    readiness_rows = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_execution_readiness")
    execution_batch_rows = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_execution_batches")
    readiness_existing_collector = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM person_enrichment_execution_readiness
        WHERE automation_status IN (
          'collector_available_partial_source_coverage',
          'collector_available_review_required',
          'collector_available_only_when_source_exposes_contact',
          'collector_available_partial_role_coverage'
        )
        """,
    )
    readiness_manual = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_execution_readiness WHERE requires_manual_review = 1",
    )
    readiness_script_extension = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_execution_readiness WHERE requires_script_extension = 1",
    )
    readiness_new_parser = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_execution_readiness WHERE requires_new_parser = 1",
    )
    dossier_summary = read_json(ARTIFACTS / "person_enrichment_dossier_summary.json", {})
    dossier_rows = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_dossiers")
    dossier_review_ready = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_dossiers WHERE review_ready_evidence_count > 0",
    )
    dossier_accepted = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_dossiers WHERE accepted_enrichment_count > 0",
    )
    dossier_candidate_only = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM person_enrichment_dossiers
        WHERE accepted_enrichment_count = 0
          AND review_ready_evidence_count = 0
          AND candidate_evidence_count > 0
        """,
    )
    action_packet_summary = read_json(ARTIFACTS / "person_enrichment_action_packet_summary.json", {})
    action_packet_rows = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_action_packets")
    action_packet_review_ready = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM person_enrichment_action_packets
        WHERE packet_status IN (
          'review_packet_ready',
          'official_profile_candidate_ready',
          'manual_review_ready'
        )
        """,
    )
    action_packet_collector_ready = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM person_enrichment_action_packets
        WHERE packet_status IN (
          'collector_execution_ready',
          'profile_search_ready',
          'contact_reobservation_ready'
        )
        """,
    )
    action_batch_summary = read_json(ARTIFACTS / "person_enrichment_action_batch_summary.json", {})
    action_batch_rows = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_action_batches")
    action_batch_ready = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_action_batches WHERE ready_to_execute = 1")
    action_batch_blocked = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_action_batches WHERE ready_to_execute = 0")
    action_batch_member_summary = read_json(ARTIFACTS / "person_enrichment_action_batch_member_summary.json", {})
    action_batch_member_rows = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_action_batch_members")
    action_batch_member_ready = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_action_batch_members WHERE ready_to_execute = 1",
    )
    action_batch_member_blocked = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_action_batch_members WHERE ready_to_execute = 0",
    )
    action_member_execution_summary = read_json(
        ARTIFACTS / "person_enrichment_action_member_execution_summary.json",
        {},
    )
    action_member_execution_dossier_summary = read_json(
        ARTIFACTS / "person_enrichment_action_member_execution_dossier_summary.json",
        {},
    )
    action_member_execution_queue_rows = scalar(conn, "SELECT COUNT(*) FROM person_enrichment_action_member_execution_queue")
    action_member_execution_dossier_rows = scalar(
        conn,
        "SELECT COUNT(*) FROM person_enrichment_action_member_execution_dossiers",
    )
    action_member_execution_pending = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM person_enrichment_action_member_execution_audit
        WHERE execution_status = 'pending_execution_decision'
        """,
    )
    action_member_execution_blocked = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM person_enrichment_action_member_execution_audit
        WHERE execution_status = 'blocked_upstream_not_ready'
        """,
    )
    action_member_execution_routed = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM person_enrichment_action_member_execution_audit
        WHERE execution_status = 'executed_outputs_routed'
        """,
    )
    research_corroboration_summary = read_json(ARTIFACTS / "research_identity_corroboration_summary.json", {})
    research_review_batch_summary = read_json(ARTIFACTS / "research_identity_review_batch_summary.json", {})
    research_reviewer_decision_summary = read_json(ARTIFACTS / "research_identity_reviewer_decision_summary.json", {})
    research_reviewer_dossier_summary = read_json(
        ARTIFACTS / "research_identity_reviewer_decision_dossier_summary.json",
        {},
    )
    research_corroboration_rows = scalar(conn, "SELECT COUNT(*) FROM research_identity_corroboration")
    research_review_batch_rows = scalar(conn, "SELECT COUNT(*) FROM research_identity_review_batches")
    research_review_batch_member_rows = scalar(conn, "SELECT COUNT(*) FROM research_identity_review_batch_members")
    research_reviewer_queue_rows = scalar(conn, "SELECT COUNT(*) FROM research_identity_reviewer_decision_queue")
    research_reviewer_audit_rows = scalar(conn, "SELECT COUNT(*) FROM research_identity_reviewer_decision_audit")
    research_reviewer_dossier_rows = scalar(conn, "SELECT COUNT(*) FROM research_identity_reviewer_decision_dossiers")
    research_reviewer_decision_rows = scalar(conn, "SELECT COUNT(*) FROM research_identity_reviewer_decisions")
    research_reviewer_pending_rows = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_reviewer_decision_audit
        WHERE decision_status = 'pending_reviewer_decision'
        """,
    )
    research_reviewer_accepted_rows = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_reviewer_decision_audit
        WHERE accepted_research_identity_review = 1
        """,
    )
    research_review_batch_ready = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_review_batches
        WHERE ready_to_review = 1
        """,
    )
    research_review_batch_conflict_members = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_review_batch_members
        WHERE conflicting_identifier_count > 0
        """,
    )
    research_signal_people = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_corroboration
        WHERE research_candidate_count > 0
        """,
    )
    research_review_ready_people = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_corroboration
        WHERE research_review_ready_count > 0
        """,
    )
    research_multi_source_people = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_corroboration
        WHERE scholarly_source_count >= 2
        """,
    )
    research_conflict_people = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_corroboration
        WHERE conflicting_identifier_count > 0
        """,
    )
    research_secondary_anchor_people = scalar(
        conn,
        """
        SELECT COUNT(*)
        FROM research_identity_corroboration
        WHERE npi_candidate_count > 0 OR profile_candidate_count > 0 OR contact_candidate_count > 0
        """,
    )
    research_review_ready_records = scalar(
        conn,
        """
        SELECT COALESCE(SUM(research_review_ready_count), 0)
        FROM research_identity_corroboration
        """,
    )

    return [
        make_row(
            scorecard_key="official_roster_current_membership",
            utility_key="official_roster",
            utility_label="Official roster current-membership extraction",
            source_family="official_institutional_web",
            claim_surface="current trainee identity, role, program, stage, and source-backed background",
            input_records=official_sources,
            output_records=memberships,
            accepted_records=people + accepted_training_claims,
            score=92.0,
            strengths=[
                "Highest precision source for current trainee membership",
                "Preserves source URL, role, program, and stage labels",
                "Supports deterministic annual refresh and diff views",
            ],
            limitations=[
                "Roster richness varies by department",
                "Some official pages expose people without full education or year labels",
                "Coverage is bounded by discovered official pages",
            ],
            recommended_next_action="keep_as_truth_anchor_and_refresh_on_program_clock",
            evidence={
                "people": people,
                "memberships": memberships,
                "accepted_training_claims": accepted_training_claims,
                "official_sources": official_sources,
            },
        ),
        make_row(
            scorecard_key="official_program_denominator_coverage",
            utility_key="official_roster",
            utility_label="Official HUP program denominator coverage",
            source_family="official_institutional_web",
            claim_surface="institution program universe, coverage gaps, and denominator drift",
            input_records=official_programs,
            output_records=official_covered,
            accepted_records=level_4_covered_programs,
            coverage_gap_records=assurance_open_gaps,
            needs_review_records=alias_rows + alias_review_programs,
            score=86.0,
            strengths=[
                "Separates denominator coverage from person extraction",
                "Makes missing programs auditable instead of invisible",
                "Assigns assurance tiers to coverage claims instead of treating all covered rows equally",
                "Adds all-program dossiers so closed, review-ready, accepted-alias, candidate-source, and open-gap programs are comparable",
                "Supports institution and category-level annual diffs",
            ],
            limitations=[
                "Official list does not guarantee a public current roster",
                "Track aliases and section-level splits need explicit reconciliation",
                "Coverage mutations are intentionally blocked until evidence is stronger",
            ],
            recommended_next_action="resolve_gap_reason_and_alias_candidates_before_count_mutation",
            evidence={
                "official_programs": official_programs,
                "covered_current_roster": official_covered,
                "level_4_covered_programs": level_4_covered_programs,
                "level_4_covered_people": level_4_covered_people,
                "coverage_gaps": official_gaps,
                "assurance_open_gaps": assurance_open_gaps,
                "gap_reasons": gap_reasons,
                "alias_candidate_rows": alias_rows,
                "coverage_mutation_allowed_rows": alias_mutations,
                "coverage_assurance_summary": coverage_assurance_summary,
                "coverage_action_queue_summary": coverage_action_queue_summary,
                "coverage_dossier_summary": coverage_dossier_summary,
                "alias_review_packets_summary": alias_review_packets_summary,
                "alias_reviewer_decision_summary": alias_reviewer_decision_summary,
            },
        ),
        make_row(
            scorecard_key="acgme_program_identifier_candidates",
            utility_key="external_program_identifier",
            utility_label="ACGME public program identifier candidates",
            source_family="acgme_public_data",
            claim_surface="program accreditation code, specialty, sponsoring program name, city, and accreditation-row context",
            input_records=official_programs,
            output_records=program_identifier_candidates,
            accepted_records=accepted_program_identifiers,
            candidate_records=program_identifier_candidates,
            needs_review_records=review_program_identifiers,
            blocked_records=no_acgme_identifiers,
            score=82.0,
            strengths=[
                "Uses the official ACGME public program search as the identifier source",
                "Adds source-backed ACGME codes for many Penn/HUP denominator programs",
                "Separates strong, ambiguous, review, no-ACGME-found, and lifecycle-consistency outcomes before mutation",
            ],
            limitations=[
                "ACGME is not trainee roster truth and does not identify individual residents or fellows",
                "UPHS has duplicate or facility-specific rows for some specialties",
                "Accepted identifiers still need roster coverage and lifecycle-rule agreement before annual roll-forward use",
                "Non-ACGME, dental, selective, and locally named fellowship programs legitimately have no ACGME code",
            ],
            recommended_next_action="use_accepted_program_identifiers_and_review_remaining_acgme_ambiguities",
            evidence={
                "candidate_rows": program_identifier_candidates,
                "accepted_identifier_rows": accepted_program_identifiers,
                "review_or_no_code_rows": review_program_identifiers,
                "no_acgme_identifier_rows": no_acgme_identifiers,
                "candidate_summary": acgme_observation_summary,
                "reconciliation_summary": acgme_reconciliation_summary,
                "program_lifecycle_consistency_summary": program_lifecycle_consistency_summary,
                "program_lifecycle_duration_summary": program_lifecycle_duration_summary,
            },
        ),
        make_row(
            scorecard_key="program_lifecycle_duration_evidence",
            utility_key="official_program_lifecycle_duration",
            utility_label="Official program-page lifecycle duration evidence",
            source_family="official_institutional_web",
            claim_surface="explicit duration phrases on official Penn program pages for ACGME-linked unknown-duration programs",
            input_records=int(program_lifecycle_duration_summary.get("target_rows") or program_lifecycle_duration_rows),
            output_records=program_lifecycle_duration_rows,
            accepted_records=accepted_program_lifecycle_duration_rows,
            candidate_records=program_lifecycle_duration_rows,
            needs_review_records=program_lifecycle_duration_review,
            review_ready_records=program_lifecycle_duration_ready,
            blocked_records=program_lifecycle_duration_blocked,
            score=72.0 if accepted_program_lifecycle_duration_rows else 67.0,
            strengths=[
                "Targets only accepted ACGME-linked programs blocked by default/unknown lifecycle rules",
                "Captures official-page duration phrases and page hashes before proposing rule changes",
                "Detects source-page mismatches and conflicting duration contexts instead of mutating lifecycle rules",
                "Reviewer decisions now separate accepted lifecycle-duration evidence from duration-context false positives",
            ],
            limitations=[
                "Official pages may omit duration even when a program has a known standard length",
                "Duration phrases can refer to prerequisites or alternate tracks and need review",
                "This audit proposes lifecycle-rule candidates only; it does not update trainee states",
            ],
            recommended_next_action="review_duration_candidates_before_extending_lifecycle_rules",
            evidence={
                "duration_summary": program_lifecycle_duration_summary,
                "duration_evidence_rows": program_lifecycle_duration_rows,
                "accepted_duration_mapping_rows": accepted_program_lifecycle_duration_rows,
                "rejected_duration_context_rows": rejected_program_lifecycle_duration_rows,
                "reviewer_decision_summary": program_lifecycle_duration_reviewer_summary,
                "reviewer_ready_duration_candidates": program_lifecycle_duration_ready,
                "review_or_mismatch_rows": program_lifecycle_duration_review,
                "blocked_or_no_explicit_duration_rows": program_lifecycle_duration_blocked,
            },
        ),
        make_row(
            scorecard_key="medical_student_public_source_audit",
            utility_key="official_roster",
            utility_label="Penn medical-student public-source audit",
            source_family="official_institutional_web",
            claim_surface="public MSTP directory, protected MD directory, MD program context, and MD-PhD graduate-directory cross-checks",
            input_records=med_student_source_rows,
            output_records=med_student_source_rows,
            accepted_records=med_student_loaded,
            candidate_records=med_student_crosscheck,
            needs_review_records=med_student_review,
            blocked_records=med_student_protected,
            score=78.0,
            strengths=[
                "Separates public MD-PhD roster truth from protected MD-only directory access",
                "Uses official PSOM/MSTP pages as source-access evidence",
                "Keeps graduate-program directories as cross-check/enrichment candidates without inflating the MD denominator",
            ],
            limitations=[
                "The official MD-only medical student directory is PennKey protected and must not be scraped",
                "Graduate directories overlap MSTP and broader PhD populations, so they are not accepted denominator records",
                "A small number of linked graduate directories are unreachable and need periodic recheck",
            ],
            recommended_next_action="monitor_protected_md_directory_and_use_grad_directories_only_for_mstp_crosscheck",
            evidence={
                "medical_student_source_rows": med_student_source_rows,
                "public_mstp_loaded_people": med_student_loaded,
                "protected_md_directory_rows": med_student_protected,
                "graduate_crosscheck_rows": med_student_crosscheck,
                "review_rows": med_student_review,
                "summary": med_student_audit_summary,
            },
        ),
        make_row(
            scorecard_key="official_gap_roster_queue_extraction",
            utility_key="official_roster",
            utility_label="Official gap roster queue extraction",
            source_family="official_institutional_web",
            claim_surface="named resident/fellow extraction from prioritized uncovered-program pages",
            input_records=roster_sources_attempted,
            output_records=roster_extracted,
            accepted_records=denominator_linked_records,
            candidate_records=gap_sources,
            needs_review_records=roster_candidates + denominator_resolution_records + denominator_resolution_review_records,
            blocked_records=roster_sources_attempted - roster_sources_with_records,
            score=76.0,
            strengths=[
                "Consumes only high-priority roster-like candidate URLs",
                "Keeps unsupported page structures queued instead of fabricating weak people",
                "Adds non-Medicine coverage from official public pages",
            ],
            limitations=[
                "Parser coverage is page-template specific",
                "Some candidate pages are related tracks rather than the official denominator row",
                "Seed-extracted records need reviewer confirmation even when program-resolution evidence is exact",
                "Unsupported structures need parser or manual review",
            ],
            recommended_next_action="review_denominator_resolution_candidates_then_rerun_coverage",
            evidence={
                "candidate_source_rows": gap_sources,
                "roster_source_candidates": roster_candidates,
                "sources_attempted": roster_sources_attempted,
                "sources_with_records": roster_sources_with_records,
                "person_records": roster_extracted,
                "denominator_linked_records": denominator_linked_records,
                "seed_without_denominator_key_records": seed_without_denominator_records,
                "denominator_resolution_records": denominator_resolution_records,
                "denominator_resolution_review_records": denominator_resolution_review_records,
                "gap_roster_reconciliation_summary": gap_roster_reconciliation_summary,
                "gap_roster_program_resolution_summary": gap_roster_program_resolution_summary,
                "by_extraction_status": gap_roster_people.get("by_extraction_status") or {},
            },
        ),
        make_row(
            scorecard_key="penn_wide_source_discovery",
            utility_key="general_web_search",
            utility_label="Penn-wide source discovery crawler",
            source_family="web_search",
            claim_surface="candidate roster, program context, alumni/outcome, and attending/faculty sources",
            input_records=discovery_total,
            output_records=broad_trainee_candidates,
            candidate_records=discovery_total,
            needs_review_records=broad_trainee_candidates + broad_context,
            low_signal_records=discovery_total - broad_trainee_candidates - broad_context,
            score=58.0,
            strengths=[
                "Finds long-tail Penn pages outside the seed Department of Medicine corpus",
                "Provides recall-oriented queue for scraper and denominator audits",
                "Useful for source discovery before person mutation",
            ],
            limitations=[
                "Classification is source-level, not person-level truth",
                "Search rank and page titles are not evidence",
                "Program context pages often lack current trainee rosters",
            ],
            recommended_next_action="treat_as_queue_then_probe_and_parse_only_source_backed_rosters",
            evidence={"by_classification": discovery_by_class, "source_rows": discovery_total},
        ),
        make_row(
            scorecard_key="pubmed_author_query_discovery",
            utility_key="pubmed_eutilities",
            utility_label="PubMed author-query discovery",
            source_family="scholarly_api",
            claim_surface="name-bounded publication discovery seeds",
            input_records=pubmed_author_claims,
            output_records=pubmed_author_claims,
            candidate_records=pubmed_author_claims,
            discovery_only_records=pubmed_discovery_only,
            score=39.0,
            strengths=[
                "Fast biomedical-publication recall using stable NCBI APIs",
                "Good seed layer for article-level fetches",
                "Durable replay artifact avoids repeating expensive query work",
            ],
            limitations=[
                "Name-only author counts collide heavily",
                "No publication claim is accepted from this layer",
                "Needs article XML, affiliation, topic, and identity anchors",
            ],
            recommended_next_action="use_only_to_seed_article_level_reconciliation",
            evidence={
                "author_query_claims": pubmed_author_claims,
                "discovery_only_decisions": pubmed_discovery_only,
            },
        ),
        make_row(
            scorecard_key="pubmed_article_reconciliation",
            utility_key="pubmed_article_reconciliation",
            utility_label="PubMed article-level reconciliation",
            source_family="scholarly_api",
            claim_surface="PMID-level publication candidates with author, affiliation, topic, and recency anchors",
            input_records=pubmed_article_claims,
            output_records=pubmed_article_claims,
            candidate_records=pubmed_article_candidate,
            needs_review_records=pubmed_article_needs_review + pubmed_secondary,
            review_ready_records=pubmed_review_ready,
            low_signal_records=pubmed_low_signal,
            score=69.0,
            strengths=[
                "Stable PMIDs and article XML create durable review evidence",
                "Non-name anchors separate review-ready records from discovery noise",
                "Person packets make manual or automated review tractable",
            ],
            limitations=[
                "Still cannot accept publications without identity reconciliation",
                "Affiliation metadata is incomplete or author-position dependent",
                "Prior-training and topic anchors are suggestive rather than dispositive",
            ],
            recommended_next_action="prioritize_review_ready_packets_then_collect_secondary_identity_anchors",
            evidence={
                "article_claims": pubmed_article_claims,
                "status_candidate": pubmed_article_candidate,
                "status_needs_review": pubmed_article_needs_review,
                "review_ready_records": pubmed_review_ready,
                "needs_secondary_identity_anchor_records": pubmed_secondary,
                "low_signal_records": pubmed_low_signal,
                "packet_status_counts": packets_by_status,
                "review_ready_packets": review_ready_packets,
                "needs_secondary_anchor_packets": secondary_packets,
            },
        ),
        make_row(
            scorecard_key="orcid_pubmed_article_reconciliation",
            utility_key="orcid_pubmed_article_reconciliation",
            utility_label="ORCID-seeded PubMed article reconciliation",
            source_family="scholarly_api",
            claim_surface="ORCID public DOI/PMID works resolved to PubMed XML with author-position and DOI/PMID consistency checks",
            input_records=orcid_work_review + orcid_work_candidate,
            output_records=orcid_pubmed_article_claims,
            candidate_records=orcid_pubmed_article_candidate,
            needs_review_records=orcid_pubmed_article_needs_review + orcid_pubmed_secondary,
            review_ready_records=orcid_pubmed_review_ready,
            low_signal_records=orcid_pubmed_low_signal,
            score=72.0 if orcid_pubmed_article_claims else 52.0,
            strengths=[
                "Starts from stable ORCID DOI/PMID work identifiers instead of name-only publication search",
                "PubMed XML adds author position, affiliation text, journal/title, year, and DOI consistency",
                "Separate claim type allows utility comparison without changing strict PubMed acceptance policy",
            ],
            limitations=[
                "Only ORCID works with PubMed-resolvable PMIDs/DOIs produce rows",
                "ORCID ownership remains self-asserted or third-party asserted unless corroborated",
                "Review-ready status still requires same-person and author-position confirmation",
            ],
            recommended_next_action="use_review_ready_orcid_seeded_articles_as_high_priority_publication_review_packets_not_machine_acceptance",
            evidence={
                "article_claims": orcid_pubmed_article_claims,
                "status_candidate": orcid_pubmed_article_candidate,
                "status_needs_review": orcid_pubmed_article_needs_review,
                "review_ready_records": orcid_pubmed_review_ready,
                "needs_secondary_identity_anchor_records": orcid_pubmed_secondary,
                "low_signal_records": orcid_pubmed_low_signal,
            },
        ),
        make_row(
            scorecard_key="enrichment_acceptance_assurance_ledger",
            utility_key="",
            utility_label="Enrichment acceptance assurance ledger",
            source_family="evidence_reconciliation",
            claim_surface="non-mutating acceptance tiers for publications, NPI anchors, and profile/trend evidence",
            input_records=int(enrichment_acceptance_summary.get("acceptance_rows") or 0),
            output_records=int(enrichment_acceptance_summary.get("acceptance_rows") or 0),
            accepted_records=accepted_enrichment_rows,
            candidate_records=int(enrichment_acceptance_summary.get("acceptance_rows") or 0),
            needs_review_records=acceptance_review_ready_publications,
            review_ready_records=machine_acceptance_candidate_rows,
            low_signal_records=int((enrichment_acceptance_summary.get("by_acceptance_status") or {}).get("low_signal_or_discovery_only") or 0),
            score=77.0,
            strengths=[
                "Separates machine-acceptance candidates from review-ready and low-signal evidence",
                "Requires cross-source PubMed plus NPI corroboration for the strictest publication tier",
                "Keeps accepted-enrichment eligibility non-mutating and fully provenance-backed",
            ],
            limitations=[
                "Machine-acceptance candidates still need final author-position and same-name sanity checks before display",
                "Current strict tier is intentionally narrow and mostly publication-focused",
                "NPI remains secondary identity evidence and can be stale",
            ],
            recommended_next_action="promote_cross_source_publication_candidates_after_final_duplicate_author_position_check",
            evidence={
                "summary": enrichment_acceptance_summary,
                "accepted_enrichment_summary": accepted_enrichment_summary,
                "accepted_enrichment_rows": accepted_enrichment_rows,
                "accepted_enrichment_people": accepted_enrichment_people,
                "machine_acceptance_candidate_rows": machine_acceptance_candidate_rows,
                "machine_acceptance_candidate_people": machine_acceptance_candidate_people,
                "review_ready_publication_rows": acceptance_review_ready_publications,
                "secondary_identity_anchor_rows": acceptance_secondary_identity_anchors,
            },
        ),
        make_row(
            scorecard_key="warehouse_reproducibility_provenance_audit",
            utility_key="",
            utility_label="Warehouse reproducibility provenance audit",
            source_family="warehouse_provenance",
            claim_surface="artifact existence, row-count parity, content hashes, and repository-size pressure",
            input_records=reproducibility_artifact_rows,
            output_records=reproducibility_artifact_rows,
            accepted_records=max(
                reproducibility_artifact_rows
                - reproducibility_mismatch_rows
                - reproducibility_missing_rows
                - reproducibility_binary_warnings,
                0,
            ),
            needs_review_records=reproducibility_mismatch_rows + reproducibility_missing_rows,
            blocked_records=reproducibility_binary_warnings,
            score=88.0
            if not (
                reproducibility_mismatch_rows
                or reproducibility_missing_rows
                or reproducibility_binary_warnings
                or reproducibility_sqlite_git_tracked
            )
            else 83.0
            if not (reproducibility_mismatch_rows or reproducibility_missing_rows)
            else 60.0,
            strengths=[
                "Compares major flat artifacts to SQLite table counts",
                "Stores artifact hashes and byte sizes for provenance review",
                "Separates data mismatches from repository storage policy",
            ],
            limitations=[
                "Row-count parity does not prove semantic equivalence for every field",
                "SQLite must be rebuilt locally from committed artifacts",
                "Network-sourced artifacts still need source-specific refresh audits",
            ],
            recommended_next_action="retain_sqlite_as_generated_untracked_artifact_and_refresh_manifest"
            if reproducibility_sqlite_storage_policy == "generated_untracked_sqlite_warehouse"
            else "move_sqlite_to_lfs_or_generated_artifact_after_preserving_rebuild_manifest",
            evidence=warehouse_reproducibility_summary,
        ),
        make_row(
            scorecard_key="evidence_temporal_contracts",
            utility_key="",
            utility_label="Evidence temporal contracts",
            source_family="warehouse_provenance",
            claim_surface="refresh, invalidation, display-safety, and currentness contracts for enrichment evidence",
            input_records=scalar(conn, "SELECT COUNT(*) FROM evidence_claims")
            + contact_count
            + accepted_enrichment_rows
            + accepted_trend_fact_rows,
            output_records=evidence_contract_rows,
            accepted_records=evidence_contract_durable + evidence_contract_refresh_bound,
            candidate_records=evidence_contract_rows,
            needs_review_records=evidence_contract_review_bound,
            blocked_records=evidence_contract_stale,
            score=85.0 if evidence_contract_rows and not evidence_contract_stale else 72.0 if evidence_contract_rows else 20.0,
            strengths=[
                "Applies explicit stale/refresh semantics to contacts, profiles, research, prior training, and trend facts",
                "Separates durable historical evidence from current endpoint/contact/profile claims",
                "Materializes rollups so source, family, role, and contract-status drift can be audited",
            ],
            limitations=[
                "Contracts describe safe mutation behavior; they do not by themselves refresh stale sources",
                "Some source-observed dates are inherited from source artifacts and need source-specific freshness improvements",
                "Candidate evidence remains review-bound even when a temporal contract exists",
            ],
            recommended_next_action="use_contract_status_before_display_or_mutation_and_refresh_stale_currentness_bound_sources",
            evidence={
                "summary": evidence_temporal_contract_summary,
                "contract_rows": evidence_contract_rows,
                "rollup_rows": evidence_contract_rollups,
                "by_current_contract_status": evidence_contract_status,
                "by_fact_family": evidence_contract_families,
            },
        ),
        make_row(
            scorecard_key="openalex_author_search",
            utility_key="openalex_author_search",
            utility_label="OpenAlex author search",
            source_family="scholarly_api",
            claim_surface="author-disambiguation, works, affiliations, ORCID, and citation features",
            input_records=int(openalex_obs["sample_size"] if openalex_obs else 0),
            output_records=int(openalex_obs["candidate_claims"] if openalex_obs else 0),
            candidate_records=int(openalex_obs["candidate_claims"] if openalex_obs else 0),
            blocked_records=openalex_blocked,
            score=24.0 if openalex_blocked else 46.0,
            strengths=[
                "Can connect authors, institutions, works, topics, ORCID, and citation counts",
                "Useful as a higher-resolution research enrichment lane when available",
                "Collector is resumable and polite-run friendly",
            ],
            limitations=[
                "Latest full-corpus pass hit sustained 429 throttling",
                "Author disambiguation remains unsafe without non-name anchors",
                "Should not block reproducible warehouse rebuilds",
            ],
            recommended_next_action="run_as_resumable_optional_lane_with_rate_limit_backoff",
            evidence={
                "rate_limit_observed": bool(openalex_blocked),
                "observation": dict(openalex_obs) if openalex_obs else {},
            },
        ),
        make_row(
            scorecard_key="orcid_public_profile_reconciliation",
            utility_key="orcid_public_api",
            utility_label="ORCID public profile and work reconciliation",
            source_family="scholarly_api",
            claim_surface="persistent ORCID identifier plus DOI/PMID-level public works, external identifiers, keywords, researcher URLs, and affiliations when exposed",
            input_records=int(orcid_obs["sample_size"] if orcid_obs else 0),
            output_records=orcid_claims,
            candidate_records=orcid_candidate,
            needs_review_records=orcid_needs_review,
            review_ready_records=orcid_secondary_anchor + orcid_work_review,
            low_signal_records=orcid_low_signal + orcid_work_low_signal,
            score=68.0,
            strengths=[
                "Persistent person identifier is valuable when linked from another high-confidence source",
                "Public works often include DOI/PMID/date/title evidence for publication reconciliation",
                "Can add a secondary identity anchor without relying on name-only PubMed queries",
                "Work-level rows can seed exact DOI/PMID follow-up against PubMed, OpenAlex, or Crossref",
            ],
            limitations=[
                "Public education and employment sections are sparse in the current Penn trainee sample",
                "ORCID records are self-asserted or third-party asserted and still need independent linkage",
                "Name match plus works is not enough to mutate accepted person truth",
                "Current work candidates still need author-position and article-metadata reconciliation before acceptance",
            ],
            recommended_next_action="use_orcid_work_ids_to_fetch_pubmed_openalex_crossref_metadata_then_reconcile_author_position",
            evidence={
                "observation": dict(orcid_obs) if orcid_obs else {},
                "claims": orcid_claims,
                "candidate": orcid_candidate,
                "needs_review": orcid_needs_review,
                "secondary_anchor_decisions": orcid_secondary_anchor,
                "partial_anchor_decisions": orcid_partial_anchor,
                "low_signal_decisions": orcid_low_signal,
                "work_publication_review_decisions": orcid_work_review,
                "work_publication_candidate_decisions": orcid_work_candidate,
                "work_low_signal_decisions": orcid_work_low_signal,
            },
        ),
        make_row(
            scorecard_key="official_trainee_profile_claims",
            utility_key="official_trainee_profile",
            utility_label="Official Penn trainee profile claims",
            source_family="official_institutional_web",
            claim_surface="roster-linked profile URLs, education, prior training, research/career interests, and personal-context snippets",
            input_records=int(trainee_profile_summary.get("profiles_with_text") or 0),
            output_records=trainee_profile_claims,
            accepted_records=trainee_profile_accepted,
            candidate_records=trainee_profile_candidate,
            score=81.0,
            strengths=[
                "Profile links are anchored by official trainee rosters",
                "Structured profile fields add education, prior-training, research/career-interest, and personal-context enrichment",
                "Display-safety metadata separates default-safe background from personal or sensitive snippets",
                "The missing-profile lane now has a queue-driven query/provenance collector for uncovered trainees",
            ],
            limitations=[
                "Profile field richness is concentrated in Department of Medicine pages",
                "Free-text pages can contain narrative bleed and require parser audits",
                "Personal fields should not be default-display or outreach signals without explicit product policy",
                "Search-discovered profile URLs remain candidate evidence until official ownership, same-person identity, and current trainee/program context are reconciled",
            ],
            recommended_next_action="run_official_trainee_profile_discovery_then_reconcile_candidates",
            evidence={
                "summary": trainee_profile_summary,
                "discovery_summary": trainee_profile_discovery_summary,
                "claims": trainee_profile_claims,
                "accepted_profile_url_facts": trainee_profile_accepted,
                "candidate_profile_fields": trainee_profile_candidate,
            },
        ),
        make_row(
            scorecard_key="official_trainee_profile_discovery",
            utility_key="official_trainee_profile_discovery",
            utility_label="Official trainee profile discovery",
            source_family="official_institutional_web",
            claim_surface="candidate official profile URLs for trainees missing roster-linked profile URLs",
            input_records=int(trainee_profile_discovery_summary.get("direct_probe_rows") or 0),
            output_records=trainee_profile_discovery_candidates,
            candidate_records=trainee_profile_discovery_claims,
            needs_review_records=trainee_profile_discovery_needs_review + official_profile_generic_route_rows,
            review_ready_records=official_profile_fresh_context_rows,
            low_signal_records=trainee_profile_discovery_low_signal,
            score=52.0 if official_profile_generic_route_rows else 58.0,
            strengths=[
                "Deterministic sibling probes reuse observed same-program official profile bases",
                "Candidate URLs are now independently reobserved before reviewer acceptance",
                "All discovered URLs remain review-only and do not mutate roster truth",
            ],
            limitations=[
                "Sparse route: most probed sibling slugs return 404",
                "Only exact program-role profile bases are used, so programs without known profile bases are not helped",
                "Current reobservation shows review-ready profile candidates resolving to generic Academic Departments pages",
                "Candidate URLs still need same-person/current-trainee review before acceptance",
            ],
            recommended_next_action="reprobe_or_replace_generic_profile_routes_before_accepting_profile_url_candidates",
            evidence={
                "summary": trainee_profile_discovery_summary,
                "official_profile_reobservation_summary": official_profile_reobservation_summary,
                "official_profile_reviewer_decision_summary": official_profile_reviewer_decision_summary,
                "candidate_rows": trainee_profile_discovery_candidates,
                "review_candidate_claims": trainee_profile_discovery_claims,
                "needs_review_claims": trainee_profile_discovery_needs_review,
                "low_signal_rows": trainee_profile_discovery_low_signal,
            },
        ),
        make_row(
            scorecard_key="prior_training_background_discovery",
            utility_key="prior_training_background_discovery",
            utility_label="Prior training background discovery",
            source_family="broad_web_search",
            claim_surface="medical-school and prior-residency background candidates for trainee enrichment gaps",
            input_records=prior_training_tasks,
            output_records=prior_training_queries,
            candidate_records=prior_training_candidates + prior_training_claims,
            discovery_only_records=prior_training_queries,
            score=58.0,
            strengths=[
                "Queue-driven collector now covers all medical-school and prior-residency background tasks",
                "Committed no-network query manifest makes rebuilds reproducible",
                "Optional probing records URL, status, content hash, title, term hits, and required next evidence",
            ],
            limitations=[
                "Broad search availability is rate-limit sensitive and is not a default rebuild dependency",
                "Prior education and residency facts are name-collision and stale-biosketch prone",
                "Candidate pages require same-person corroboration or reviewer acceptance before facts are promoted",
            ],
            recommended_next_action="run_prior_training_background_discovery_then_reconcile_candidates",
            evidence={
                "summary": prior_training_discovery_summary,
                "tasks_considered": prior_training_tasks,
                "query_rows": prior_training_queries,
                "candidate_rows": prior_training_candidates,
                "claim_rows": prior_training_claims,
            },
        ),
        make_row(
            scorecard_key="official_attending_profile_claims",
            utility_key="official_profile",
            utility_label="Official Penn attending/profile claims",
            source_family="official_institutional_web",
            claim_surface="current attending endpoints, structured education/training, research interests, and personal profile snippets",
            input_records=attending_profile_events,
            output_records=attending_profile_events,
            candidate_records=attending_profile_events,
            needs_review_records=attending_profile_events,
            review_ready_records=attending_profile_review_ready,
            low_signal_records=attending_profile_context,
            score=73.0,
            strengths=[
                "Official profile pages are strong current-identity and training-history sources",
                "Structured provider fields expose medical school, residency, fellowship, and Penn training language",
                "Creates the endpoint side of a ten-year Penn attending trend line",
            ],
            limitations=[
                "Current attending endpoint is not proof of prior Penn trainee identity",
                "Profile claims need dated historical roster, CV, alumni, or independent bridge evidence",
                "Profile richness varies by department",
            ],
            recommended_next_action="seek_historical_identity_bridge_before_accepting_trend_links",
            evidence={
                "profile_career_events": attending_profile_events,
                "current_attending_endpoint_decisions": current_attending_endpoint,
                "attending_training_claim_review_ready": attending_profile_review_ready,
                "profile_context_candidate": attending_profile_context,
                "trend_linkage_status": trend_linkage,
            },
        ),
        make_row(
            scorecard_key="attending_historical_link_discovery",
            utility_key="general_web_search",
            utility_label="Attending historical-link discovery",
            source_family="web_search",
            claim_surface="source candidates that may bridge current Penn attending endpoints to historical trainee records",
            input_records=historical_candidates,
            output_records=historical_actionable,
            candidate_records=historical_candidates,
            needs_review_records=historical_actionable,
            blocked_records=max(historical_candidates - historical_actionable - current_context_only, 0),
            score=47.0,
            strengths=[
                "Makes the exact missing bridge evidence explicit",
                "Produces deterministic queries and probed source candidates",
                "Can expand to CV, alumni, roster archive, and profile evidence without mutating people",
            ],
            limitations=[
                "Seeded mode is reproducible but low-recall",
                "Broad search availability and ranking are source-quality concerns",
                "Most candidates still need manual or parser review",
            ],
            recommended_next_action="run_polite_broad_search_and_prioritize_dated_historical_roster_or_cv_hits",
            evidence=historical_summary,
        ),
        make_row(
            scorecard_key="official_faculty_biosketch_training_bridges",
            utility_key="official_profile",
            utility_label="Official Penn faculty biosketch training bridges",
            source_family="official_institutional_web",
            claim_surface="dated post-graduate training lines from official Penn Faculty Biosketch pages",
            input_records=int(biosketch_summary.get("source_observation_rows") or 0),
            output_records=biosketch_rows,
            candidate_records=biosketch_rows,
            needs_review_records=biosketch_rows,
            review_ready_records=biosketch_recent_bridge,
            low_signal_records=max(biosketch_rows - biosketch_gme_context, 0),
            score=79.0,
            strengths=[
                "Official Penn Faculty Biosketch pages expose structured post-graduate training sections",
                "Date ranges make ten-year attending-flow timing auditable",
                "Bridges current Penn attending endpoints to explicit Penn training claims without relying on search snippets",
            ],
            limitations=[
                "Biosketch lines are profile evidence, not historical roster membership by themselves",
                "Faculty index recall is bounded by matched current-attending groups",
                "Postdoctoral research lines are useful context but should not count as GME trainee-flow bridges",
            ],
            recommended_next_action="review_dated_biosketch_bridges_before_accepting_recent_attending_trends",
            evidence={
                "summary": biosketch_summary,
                "candidate_rows": biosketch_rows,
                "groups_with_candidates": biosketch_groups,
                "recent_dated_gme_bridge_rows": biosketch_recent_bridge,
                "gme_context_rows": biosketch_gme_context,
            },
        ),
        make_row(
            scorecard_key="attending_trend_reconciliation_ledger",
            utility_key="official_profile",
            utility_label="Attending trend reconciliation ledger",
            source_family="evidence_reconciliation",
            claim_surface="non-mutating policy ledger for current-attending endpoint, Penn-training, biosketch, and historical-link evidence",
            input_records=trend_reconciliation_rows,
            output_records=trend_reconciliation_rows,
            accepted_records=accepted_trend_fact_rows,
            candidate_records=trend_reconciliation_rows,
            needs_review_records=trend_reconciliation_needs_bridge,
            review_ready_records=trend_review_claim_rows or trend_reconciliation_review_ready,
            score=82.0,
            strengths=[
                "Combines endpoint, Penn-training profile, official biosketch, and historical-link evidence without mutating rosters",
                "Separates review-ready recent attending trend candidates from profile claims that still need dated bridges",
                "Produces queryable person/group-level trend assurance, review-claim rows, rollups, and ten-year-window labels",
                "Adds group-level dossiers that make accepted facts, review-ready bridges, endpoint-only cases, and missing evidence explicit",
            ],
            limitations=[
                (
                    "Future review-ready rows still need explicit reviewer acceptance before becoming accepted trend facts"
                    if pending_trend_reviewer_decisions == 0 and accepted_trend_fact_rows > 0
                    else "Review-ready rows still need explicit reviewer acceptance before becoming accepted trend facts"
                ),
                "Current recall is bounded by attending profile and biosketch discovery",
                "Historical web search remains rate-limit and ranking sensitive",
            ],
            recommended_next_action=(
                "expand_attending_profile_and_historical_bridge_discovery_for_more_trend_facts"
                if pending_trend_reviewer_decisions == 0 and accepted_trend_fact_rows > 0
                else "review_ready_trend_rows_then_record_explicit_acceptance_decisions"
            ),
            evidence={
                "summary": trend_reconciliation_summary,
                "trend_rows": trend_reconciliation_rows,
                "review_ready_rows": trend_reconciliation_review_ready,
                "trend_review_claim_rows": trend_review_claim_rows,
                "trend_review_rollup_rows": trend_review_rollup_rows,
                "trend_review_claims_summary": trend_review_claims_summary,
                "trend_acceptance_summary": trend_acceptance_summary,
                "trend_reviewer_decision_summary": trend_reviewer_decision_summary,
                "trend_dossier_summary": trend_dossier_summary,
                "accepted_trend_fact_rows": accepted_trend_fact_rows,
                "pending_reviewer_decision_rows": pending_trend_reviewer_decisions,
                "needs_bridge_or_training_rows": trend_reconciliation_needs_bridge,
            },
        ),
        make_row(
            scorecard_key="nppes_npi_registry_candidates",
            utility_key="nppes_npi_registry",
            utility_label="NPPES NPI Registry candidates",
            source_family="licensure_api",
            claim_surface="candidate NPI, taxonomy, and PA practice-location anchors for current resident/fellow identity review",
            input_records=npi_observations,
            output_records=npi_candidate_rows,
            candidate_records=npi_candidate_rows,
            needs_review_records=npi_review_ready + npi_candidate,
            review_ready_records=npi_review_ready,
            low_signal_records=npi_low_signal,
            score=62.0,
            strengths=[
                "Official CMS/NPPES public provider registry",
                "Adds durable NPI, taxonomy, and location anchors for physician identity review",
                "Useful corroborating evidence alongside official profile, publication, and roster context",
            ],
            limitations=[
                "Name collisions remain common and NPI locations can lag training status",
                "Residents/fellows may use student/training taxonomy or older practice locations",
                "No NPI candidate is accepted without non-name source corroboration",
            ],
            recommended_next_action="use_npi_candidates_as_secondary_identity_anchors_only",
            evidence={
                "summary": npi_summary,
                "source_observations": npi_observations,
                "candidate_rows": npi_candidate_rows,
                "review_ready_rows": npi_review_ready,
                "candidate_rows_by_status": {
                    "needs_review": npi_review_ready,
                    "candidate": npi_candidate,
                    "low_signal_npi_candidate": npi_low_signal,
                },
            },
        ),
        make_row(
            scorecard_key="public_contact_candidate_extraction",
            utility_key="official_profile",
            utility_label="Public contact candidate extraction",
            source_family="official_institutional_web",
            claim_surface="public email/contact channels with scope and verification status",
            input_records=contact_count,
            output_records=contact_count,
            accepted_records=contact_verified,
            candidate_records=max(contact_count - contact_review_required, 0),
            needs_review_records=contact_review_required + contact_value_absent + contact_source_fetch_problem,
            review_ready_records=contact_fresh_reobserved,
            score=74.0 if contact_fresh_reobserved else 69.0,
            strengths=[
                "Stores contact channels separately from person identity truth",
                "Retains source, scope, verification status, confidence, and candidate status",
                "Classifies public contacts into display-safety and verification-required tiers without dropping public data",
                "Adds non-mutating verification contracts with stale dates and future refresh outcomes",
                "Adds current-source reobservation evidence before reviewer acceptance",
                "Gates verified contact facts through explicit reviewer decisions and current-source reobservation",
            ],
            limitations=[
                "Current contacts are public-directory/profile unverified candidates, not verified contact facts",
                "Contact channels can be stale or role-specific",
                "Some historical contact candidates are absent from freshly fetched official pages and require source reconciliation",
                "Current captured contacts are email-only; phone-support assurance is schema-ready but not populated",
            ],
            recommended_next_action="verify_current_source_before_display_or_outreach_and_review_domain_anomalies",
            evidence={
                "contact_count": contact_count,
                "by_verification_status": contact_by_verification,
                "contact_assurance_summary": contact_assurance_summary,
                "contact_verification_contract_summary": contact_verification_contract_summary,
                "contact_reobservation_summary": contact_reobservation_summary,
                "contact_verification_reviewer_decision_summary": contact_reviewer_decision_summary,
                "contact_assurance_status": contact_assurance_status,
            },
        ),
        make_row(
            scorecard_key="organization_normalization_resolver",
            utility_key="",
            utility_label="Organization normalization resolver",
            source_family="normalization",
            claim_surface="medical school, residency, undergraduate, graduate, institution, and program labels",
            input_records=org_count,
            output_records=org_aliases,
            accepted_records=org_seeded,
            candidate_records=org_identifier_candidates,
            needs_review_records=org_review,
            score=74.0,
            strengths=[
                "Preserves raw labels while resolving category-specific aliases",
                "Separates schools, hospitals, programs, and undergraduate institutions",
                "Schema supports ROR, OpenAlex, IPEDS, WDOMS, ACGME, ERAS, and NRMP identifiers",
            ],
            limitations=[
                "Many cleaned labels still need alias and identifier review",
                "External codes should not be inferred by name alone",
                "Program-track identifiers need source-backed verification",
            ],
            recommended_next_action="append_alias_and_identifier_candidates_with_source_backed_evidence",
            evidence={
                "organizations": org_count,
                "seeded_alias_rows": org_seeded,
                "cleaned_label_review_rows": org_review,
                "aliases": org_aliases,
                "identifiers": org_identifiers,
                "identifier_candidate_rows": org_identifier_candidates,
                "identifier_candidate_summary": org_identifier_candidate_summary,
            },
        ),
        make_row(
            scorecard_key="training_state_machine_longitudinal_readiness",
            utility_key="official_roster",
            utility_label="Training state machine and longitudinal readiness",
            source_family="state_machine",
            claim_surface="normalized stages, lifecycle rules, stale-after semantics, and annual diff expectations",
            input_records=state_rows,
            output_records=state_rows,
            accepted_records=state_rows,
            needs_review_records=int(machine_status.get("review_required") or 0),
            blocked_records=int(machine_status.get("source_refresh_required") or 0),
            score=84.0,
            strengths=[
                "Turns PGY/MS/fellowship labels into explicit lifecycle states",
                "Separates expected advancement, expected completion, source refresh, and review-required changes",
                "Materializes non-mutating transition policies for future refresh runs",
                "Supports person, program, institution, country, and category diff views",
                "Audits accepted external program identifiers against local lifecycle state coverage before program-level rollups",
            ],
            limitations=[
                "Lifecycle codes are local until external program identifiers are verified",
                "Unknown-duration, research, chief, postdoc, and PhD states require fresh source evidence",
                "Annual clocks are assumptions attached to program lifecycle rules, not source facts",
                "Program-level auto-advancement is withheld when accepted identifiers lack current roster validation or complete lifecycle mapping",
            ],
            recommended_next_action="use_state_machine_expectations_before_mutating_next_year_roster_diffs",
            evidence={
                "state_rows": state_rows,
                "machine_status": machine_status,
                "longitudinal_readiness_status": readiness_status,
                "lifecycle_assurance_summary": lifecycle_assurance_summary,
                "transition_plan_summary": transition_plan_summary,
                "transition_policy_lanes": transition_policy_lanes,
                "program_lifecycle_consistency_summary": program_lifecycle_consistency_summary,
            },
        ),
        make_row(
            scorecard_key="recursive_enrichment_work_queue",
            utility_key="",
            utility_label="Recursive enrichment work queue",
            source_family="orchestration",
            claim_surface="person-level next-source tasks with state-machine urgency and evidence gates",
            input_records=people,
            output_records=enrichment_queue_rows,
            candidate_records=enrichment_queue_rows,
            needs_review_records=enrichment_queue_review_or_refresh,
            review_ready_records=enrichment_queue_high,
            score=81.0,
            strengths=[
                "Covers residents, fellows, and medical students in one source-aware work queue",
                "Prioritizes source tasks using enrichment coverage, evidence queues, and lifecycle/diff risk",
                "Stores acceptance, provenance, and recency policy per task before any future scraper mutates facts",
            ],
            limitations=[
                "Queue quality depends on current coverage and transition-plan inputs",
                "Queries are candidate search plans, not evidence facts",
                "Human/reviewer decision loops are still required before accepting ambiguous enrichment",
            ],
            recommended_next_action="run_high_priority_queue_tasks_and_feed_results_back_through_acceptance_ledgers",
            evidence={
                "queue_rows": enrichment_queue_rows,
                "person_count": enrichment_queue_people,
                "high_or_critical_rows": enrichment_queue_high,
                "review_or_refresh_rows": enrichment_queue_review_or_refresh,
                "queue_summary": enrichment_queue_summary,
            },
        ),
        make_row(
            scorecard_key="person_enrichment_dossier_ledger",
            utility_key="",
            utility_label="Person enrichment dossier ledger",
            source_family="orchestration",
            claim_surface="person-level accepted facts, candidate surfaces, contact contracts, training state, and provenance URLs",
            input_records=people,
            output_records=dossier_rows,
            accepted_records=dossier_accepted,
            candidate_records=dossier_candidate_only,
            review_ready_records=dossier_review_ready,
            score=83.0,
            strengths=[
                "Summarizes every warehouse person in one stable row",
                "Separates accepted enrichment from review-ready and candidate evidence",
                "Includes contact verification contracts, temporal training state, missing surfaces, and top provenance URLs",
            ],
            limitations=[
                "Dossiers are summaries and do not replace source-specific evidence ledgers",
                "Accepted enrichment remains intentionally sparse until review gates are satisfied",
                "Attending outcome candidates without person keys remain in attending trend ledgers rather than trainee dossiers",
            ],
            recommended_next_action="use_dossiers_for_person_level_review_then_feed_acceptance_decisions_back_to_ledgers",
            evidence={
                "dossier_rows": dossier_rows,
                "accepted_enrichment_people": dossier_accepted,
                "review_ready_people": dossier_review_ready,
                "candidate_only_people": dossier_candidate_only,
                "dossier_summary": dossier_summary,
            },
        ),
        make_row(
            scorecard_key="enrichment_execution_readiness",
            utility_key="",
            utility_label="Enrichment execution readiness",
            source_family="orchestration",
            claim_surface="mapping from queued enrichment tasks to collectors, commands, parser gaps, and review requirements",
            input_records=enrichment_queue_rows,
            output_records=readiness_rows,
            candidate_records=readiness_existing_collector,
            needs_review_records=readiness_manual,
            blocked_records=readiness_new_parser,
            score=78.0,
            strengths=[
                "Makes collector availability and parser gaps explicit per queued person task",
                "Separates network collection, manual review, script-extension, and new-parser requirements",
                "Rolls execution readiness up by task type, source family, automation status, and priority band",
                "Adds resumable execution batches with command hints, evidence gates, recency policy, provenance policy, and top people samples",
            ],
            limitations=[
                "Readiness is an execution map, not collected evidence",
                "Profile and prior-training lanes are now collector-backed, but network search can be slow and still yields candidate evidence only",
                "Research collection is queue-driven, but article-level reconciliation and acceptance review remain downstream",
            ],
            recommended_next_action="execute_queue_driven_research_profile_prior_training_and_roster_lanes_then_reconcile",
            evidence={
                "readiness_rows": readiness_rows,
                "execution_batch_rows": execution_batch_rows,
                "existing_collector_or_partial_collector_rows": readiness_existing_collector,
                "manual_review_required_rows": readiness_manual,
                "script_extension_required_rows": readiness_script_extension,
                "new_parser_required_rows": readiness_new_parser,
                "execution_readiness_summary": execution_readiness_summary,
                "execution_batch_summary": execution_batch_summary,
            },
        ),
        make_row(
            scorecard_key="person_enrichment_action_packet_ledger",
            utility_key="",
            utility_label="Person enrichment action packet ledger",
            source_family="orchestration",
            claim_surface="per-person recursive enrichment next action, provenance, blocker, and downstream artifact routing",
            input_records=dossier_rows,
            output_records=action_packet_rows,
            candidate_records=action_packet_collector_ready,
            needs_review_records=action_packet_review_ready,
            review_ready_records=action_packet_review_ready,
            score=84.0,
            strengths=[
                "Creates one operational packet per person dossier so recursive enrichment can run person-by-person",
                "Combines dossier state, execution readiness, official profile discovery, contact contracts, and evidence-review packets",
                "Keeps next evidence, blockers, command hints, source URLs, and downstream artifacts together without accepting facts",
            ],
            limitations=[
                "Packets summarize source-specific ledgers and must not replace the underlying evidence records",
                "Recommended actions are prioritization aids, not proof that a source is complete or correct",
                "Packet quality depends on existing queues and currently observed profile/contact/review surfaces",
            ],
            recommended_next_action="execute_high_priority_action_packets_then_feed_results_back_through_source_specific_acceptance_ledgers",
            evidence={
                "action_packet_rows": action_packet_rows,
                "review_ready_packets": action_packet_review_ready,
                "collector_ready_packets": action_packet_collector_ready,
                "action_packet_summary": action_packet_summary,
            },
        ),
        make_row(
            scorecard_key="person_enrichment_action_batch_ledger",
            utility_key="",
            utility_label="Person enrichment action batch ledger",
            source_family="orchestration",
            claim_surface="resumable execution batches over per-person enrichment action packets",
            input_records=action_packet_rows,
            output_records=action_batch_rows,
            candidate_records=action_batch_ready,
            blocked_records=action_batch_blocked,
            score=82.0,
            strengths=[
                "Splits per-person action packets into lane/status/priority/role batches that can be worked incrementally",
                "Preserves command hints, next evidence requirements, downstream artifacts, and top people samples per batch",
                "Makes blocked retry batches visible instead of mixing them with executable review or collector work",
            ],
            limitations=[
                "Batch execution still depends on source-specific collectors or reviewer decisions",
                "Large evidence-review batches remain human-review constrained until decision artifacts are recorded",
                "Chunking optimizes operator flow and does not prove source completeness",
            ],
            recommended_next_action="execute_ready_action_batches_and_feed_outputs_back_to_source_specific_ledgers",
            evidence={
                "action_packet_rows": action_packet_rows,
                "action_batch_rows": action_batch_rows,
                "ready_batch_rows": action_batch_ready,
                "blocked_batch_rows": action_batch_blocked,
                "action_batch_summary": action_batch_summary,
            },
        ),
        make_row(
            scorecard_key="person_enrichment_action_batch_member_ledger",
            utility_key="",
            utility_label="Person enrichment action batch member ledger",
            source_family="orchestration",
            claim_surface="exact per-person membership rows for resumable enrichment action batches",
            input_records=action_batch_rows,
            output_records=action_batch_member_rows,
            candidate_records=action_batch_member_ready,
            blocked_records=action_batch_member_blocked,
            score=83.0,
            strengths=[
                "Expands each action batch into exact person-packet rows for joins, execution tracking, and diffing",
                "Carries packet priority, blocker, required evidence, source URLs, command hints, and downstream artifacts per member",
                "Removes reliance on embedded JSON membership when auditing whether every person packet is covered",
            ],
            limitations=[
                "Member rows are operational pointers, not source observations or accepted facts",
                "Executing a member still requires source-specific reviewer decisions or collector output",
                "Batch membership follows current packet prioritization and should be regenerated after queue or evidence changes",
            ],
            recommended_next_action="work_batch_members_in_execution_order_and_record_outputs_in_source_specific_ledgers",
            evidence={
                "action_batch_rows": action_batch_rows,
                "action_batch_member_rows": action_batch_member_rows,
                "ready_member_rows": action_batch_member_ready,
                "blocked_member_rows": action_batch_member_blocked,
                "action_batch_member_summary": action_batch_member_summary,
            },
        ),
        make_row(
            scorecard_key="person_enrichment_action_member_execution_ledger",
            utility_key="",
            utility_label="Person enrichment action member execution ledger",
            source_family="orchestration",
            claim_surface="fingerprinted per-member execution outcomes and downstream routing audit",
            input_records=action_batch_member_rows,
            output_records=action_member_execution_queue_rows,
            candidate_records=action_member_execution_pending,
            accepted_records=action_member_execution_routed,
            blocked_records=action_member_execution_blocked,
            score=82.0,
            strengths=[
                "Adds a fingerprinted decision surface for every action-batch member",
                "Separates execution outcomes from accepted facts so collector output must still pass source-specific gates",
                "Flags stale, invalid, unrouted, blocked, and pending execution decisions",
            ],
            limitations=[
                "Manual execution decisions are empty until operators run or review members",
                "Does not execute collectors by itself",
                "Outcome quality depends on downstream ledgers being rebuilt after execution",
            ],
            recommended_next_action="execute_or_review_ready_members_then_record_routed_outputs_with_matching_fingerprints",
            evidence={
                "action_batch_member_rows": action_batch_member_rows,
                "execution_queue_rows": action_member_execution_queue_rows,
                "pending_execution_decision_rows": action_member_execution_pending,
                "blocked_execution_rows": action_member_execution_blocked,
                "executed_outputs_routed_rows": action_member_execution_routed,
                "execution_summary": action_member_execution_summary,
                "execution_dossier_rows": action_member_execution_dossier_rows,
                "execution_dossier_summary": action_member_execution_dossier_summary,
            },
        ),
        make_row(
            scorecard_key="research_identity_corroboration_ledger",
            utility_key="",
            utility_label="Research identity corroboration ledger",
            source_family="evidence_reconciliation",
            claim_surface="person-level cross-source agreement, secondary anchors, conflicts, and review routing for scholarly identity enrichment",
            input_records=scalar(conn, "SELECT COUNT(*) FROM evidence_claims")
            + scalar(conn, "SELECT COUNT(*) FROM npi_candidate_claims")
            + scalar(conn, "SELECT COUNT(*) FROM trainee_profile_discovery_candidates")
            + scalar(conn, "SELECT COUNT(*) FROM person_contacts"),
            output_records=research_corroboration_rows,
            candidate_records=research_signal_people,
            needs_review_records=research_review_ready_people + research_conflict_people,
            review_ready_records=research_multi_source_people,
            blocked_records=research_conflict_people,
            score=83.0 if research_corroboration_rows and not research_conflict_people else 76.0 if research_corroboration_rows else 25.0,
            strengths=[
                "Rolls PubMed, OpenAlex, ORCID, NPI, official profile, contact, and training-state context into one person-level review surface",
                "Separates multi-source agreement, non-name anchors, persistent identifiers, secondary anchors, and conflicts",
                "Ranks review routes without accepting person facts from corroboration alone",
            ],
            limitations=[
                "Corroboration is only as current as the upstream candidate collectors and profile/contact artifacts",
                "Multi-source evidence can still share upstream name-collision risk and needs reviewer acceptance",
                "Conflicts are intentionally review-blocking until source-specific evidence is resolved",
            ],
            recommended_next_action="prioritize_multi_source_research_identity_reviews_and_resolve_conflicts_before_acceptance",
            evidence={
                "summary": research_corroboration_summary,
                "corroboration_rows": research_corroboration_rows,
                "review_batch_rows": research_review_batch_rows,
                "review_batch_member_rows": research_review_batch_member_rows,
                "people_with_research_signal": research_signal_people,
                "people_with_review_ready_research": research_review_ready_people,
                "people_with_multi_source_research": research_multi_source_people,
                "people_with_secondary_anchor": research_secondary_anchor_people,
                "conflict_people": research_conflict_people,
                "research_review_ready_records": research_review_ready_records,
            },
        ),
        make_row(
            scorecard_key="research_identity_review_batch_ledger",
            utility_key="",
            utility_label="Research identity review batch ledger",
            source_family="evidence_reconciliation",
            claim_surface="bounded reviewer sessions and member fingerprints for cross-source scholarly identity work",
            input_records=research_corroboration_rows,
            output_records=research_review_batch_rows,
            candidate_records=research_review_batch_member_rows,
            needs_review_records=research_review_batch_member_rows,
            review_ready_records=research_review_batch_ready,
            blocked_records=research_review_batch_conflict_members,
            score=82.0 if research_review_batch_rows else 25.0,
            strengths=[
                "Turns person-level research corroboration into bounded reviewer sessions",
                "Adds stable member fingerprints so decisions can be checked against the evidence actually reviewed",
                "Keeps acceptance non-mutating and routed through source-specific reviewer and acceptance ledgers",
            ],
            limitations=[
                "Batching does not resolve conflicts or accept research identity facts by itself",
                "Manual decisions must still be recorded against the current member fingerprint",
                "Collector freshness depends on upstream PubMed, OpenAlex, ORCID, profile, contact, and NPI artifacts",
            ],
            recommended_next_action="work_research_identity_batches_and_record_source_specific_decisions",
            evidence={
                "summary": research_review_batch_summary,
                "corroboration_rows": research_corroboration_rows,
                "batch_rows": research_review_batch_rows,
                "member_rows": research_review_batch_member_rows,
                "reviewer_queue_rows": research_reviewer_queue_rows,
                "reviewer_audit_rows": research_reviewer_audit_rows,
                "ready_batch_rows": research_review_batch_ready,
                "conflict_member_rows": research_review_batch_conflict_members,
            },
        ),
        make_row(
            scorecard_key="research_identity_reviewer_decision_ledger",
            utility_key="",
            utility_label="Research identity reviewer decision ledger",
            source_family="evidence_reconciliation",
            claim_surface="manual research identity decisions audited against current member fingerprints and required confirmations",
            input_records=research_review_batch_member_rows,
            output_records=research_reviewer_audit_rows,
            candidate_records=research_reviewer_queue_rows,
            needs_review_records=research_reviewer_pending_rows,
            review_ready_records=research_reviewer_queue_rows,
            accepted_records=research_reviewer_accepted_rows,
            blocked_records=research_review_batch_conflict_members,
            score=84.0 if research_reviewer_audit_rows else 25.0,
            strengths=[
                "Creates an explicit decision input ledger for research identity review batches",
                "Audits decisions against current member fingerprints and source/non-name-anchor confirmations",
                "Separates accepted review decisions from downstream accepted person facts",
            ],
            limitations=[
                "Manual decisions are currently pending until reviewers populate the decision input file",
                "Accepted review decisions still need downstream evidence reconciliation and acceptance ledgers",
                "Conflict rows remain blocked until conflicting identifiers are resolved or quarantined",
            ],
            recommended_next_action="record_research_identity_reviewer_decisions_with_current_member_fingerprints",
            evidence={
                "summary": research_reviewer_decision_summary,
                "dossier_summary": research_reviewer_dossier_summary,
                "batch_member_rows": research_review_batch_member_rows,
                "queue_rows": research_reviewer_queue_rows,
                "manual_decision_rows": research_reviewer_decision_rows,
                "audit_rows": research_reviewer_audit_rows,
                "dossier_rows": research_reviewer_dossier_rows,
                "pending_reviewer_decision_rows": research_reviewer_pending_rows,
                "accepted_research_identity_review_rows": research_reviewer_accepted_rows,
                "conflict_member_rows": research_review_batch_conflict_members,
            },
        ),
    ]


def write_outputs(conn: sqlite3.Connection, rows: list[dict]) -> None:
    existing = existing_rows()
    audited_at = datetime.now(timezone.utc).isoformat()
    for row in rows:
        row["audited_at"] = stable_audited_at(existing, row, audited_at)

    with SCORECARD_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    SCORECARD_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    conn.execute("DELETE FROM source_utility_scorecard")
    for row in rows:
        conn.execute(
            """
            INSERT INTO source_utility_scorecard
            (scorecard_key, utility_key, utility_label, source_family, claim_surface,
             input_records, output_records, accepted_records, candidate_records,
             needs_review_records, review_ready_records, discovery_only_records,
             low_signal_records, coverage_gap_records, blocked_records, score,
             quality_band, strengths, limitations, recommended_next_action,
             evidence_json, audited_at)
            VALUES (?, NULLIF(?, ''), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row[field] for field in FIELDNAMES),
        )
    conn.commit()

    summary = {
        "generated_at": audited_at,
        "csv": str(SCORECARD_CSV.relative_to(ROOT)),
        "json": str(SCORECARD_JSON.relative_to(ROOT)),
        "scorecard_rows": len(rows),
        "by_quality_band": dict(Counter(row["quality_band"] for row in rows)),
        "by_source_family": dict(Counter(row["source_family"] for row in rows)),
        "by_recommended_next_action": dict(Counter(row["recommended_next_action"] for row in rows)),
        "high_utility_rows": sum(1 for row in rows if row["quality_band"] == "high_utility"),
        "candidate_or_discovery_rows": sum(
            1
            for row in rows
            if row["quality_band"] in {"useful_candidate_layer", "discovery_or_review_only"}
        ),
        "blocked_or_low_current_utility_rows": sum(
            1 for row in rows if row["quality_band"] == "blocked_or_low_current_utility"
        ),
        "top_rows": [
            {
                "scorecard_key": row["scorecard_key"],
                "utility_label": row["utility_label"],
                "score": row["score"],
                "quality_band": row["quality_band"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in sorted(rows, key=lambda item: (-float(item["score"]), item["scorecard_key"]))[:8]
        ],
    }
    SCORECARD_SUMMARY.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"scorecard_rows": len(rows), "by_quality_band": summary["by_quality_band"]}, sort_keys=True))


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    write_outputs(conn, score_rows(conn))
    conn.close()


if __name__ == "__main__":
    main()
