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
    alias_review_packets_summary = read_json(
        ARTIFACTS / "official_program_alias_review_packets_summary.json",
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

    attending_profile_events = scalar(conn, "SELECT COUNT(*) FROM career_events WHERE source_key LIKE 'penn_attending_profile_%'")
    attending_profile_review_ready = decision_counts.get("attending_training_claim_review_ready", 0)
    attending_profile_context = decision_counts.get("profile_context_candidate", 0)
    current_attending_endpoint = decision_counts.get("current_attending_endpoint_candidate", 0)
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
    trend_review_claim_rows = int(trend_review_claims_summary.get("trend_review_claim_rows") or 0)
    trend_review_rollup_rows = int(trend_review_claims_summary.get("trend_review_rollup_rows") or 0)
    accepted_trend_fact_rows = int(trend_acceptance_summary.get("accepted_trend_fact_rows") or 0)
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
    contact_assurance_status = contact_assurance_summary.get("by_assurance_status") or {}
    contact_review_required = int(contact_assurance_summary.get("review_required_rows") or 0)
    contact_verified = int(contact_assurance_summary.get("verified_contact_fact_rows") or 0)

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
                "alias_review_packets_summary": alias_review_packets_summary,
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
            ],
            limitations=[
                "Review-ready rows still need explicit reviewer acceptance before becoming accepted trend facts",
                "Current recall is bounded by attending profile and biosketch discovery",
                "Historical web search remains rate-limit and ranking sensitive",
            ],
            recommended_next_action="review_ready_trend_rows_then_record_explicit_acceptance_decisions",
            evidence={
                "summary": trend_reconciliation_summary,
                "trend_rows": trend_reconciliation_rows,
                "review_ready_rows": trend_reconciliation_review_ready,
                "trend_review_claim_rows": trend_review_claim_rows,
                "trend_review_rollup_rows": trend_review_rollup_rows,
                "trend_review_claims_summary": trend_review_claims_summary,
                "trend_acceptance_summary": trend_acceptance_summary,
                "accepted_trend_fact_rows": accepted_trend_fact_rows,
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
            needs_review_records=contact_review_required,
            score=69.0,
            strengths=[
                "Stores contact channels separately from person identity truth",
                "Retains source, scope, verification status, confidence, and candidate status",
                "Classifies public contacts into display-safety and verification-required tiers without dropping public data",
            ],
            limitations=[
                "Current contacts are public-directory/profile unverified candidates, not verified contact facts",
                "Contact channels can be stale or role-specific",
                "Current captured contacts are email-only; phone-support assurance is schema-ready but not populated",
            ],
            recommended_next_action="verify_current_source_before_display_or_outreach_and_review_domain_anomalies",
            evidence={
                "contact_count": contact_count,
                "by_verification_status": contact_by_verification,
                "contact_assurance_summary": contact_assurance_summary,
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
