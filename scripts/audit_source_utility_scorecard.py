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
    gap_roster_people = read_json(ARTIFACTS / "penn_gme_gap_roster_summary.json", {})
    roster_extracted = int(gap_roster_people.get("person_records") or 0)
    roster_sources_attempted = int(gap_roster_people.get("sources_attempted") or 0)
    roster_sources_with_records = int(gap_roster_people.get("sources_with_records") or 0)

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

    contact_count = scalar(conn, "SELECT COUNT(*) FROM person_contacts")
    contact_by_verification = counter_query(
        conn,
        "SELECT verification_status, COUNT(*) FROM person_contacts GROUP BY verification_status",
    )

    org_count = scalar(conn, "SELECT COUNT(*) FROM organizations")
    org_review = scalar(conn, "SELECT COUNT(*) FROM organizations WHERE resolver_status = 'cleaned_label'")
    org_seeded = scalar(conn, "SELECT COUNT(*) FROM organizations WHERE resolver_status = 'seeded_alias'")
    org_aliases = scalar(conn, "SELECT COUNT(*) FROM organization_aliases")
    org_identifiers = scalar(conn, "SELECT COUNT(*) FROM organization_identifiers")

    state_rows = scalar(conn, "SELECT COUNT(*) FROM person_training_states")
    state_machine_summary = read_json(ARTIFACTS / "training_state_machine_summary.json", {})
    machine_status = state_machine_summary.get("by_state_machine_status") or {}
    longitudinal_summary = read_json(ARTIFACTS / "longitudinal_change_readiness_summary.json", {})
    readiness_status = longitudinal_summary.get("by_readiness_status") or {}

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
            accepted_records=official_covered,
            coverage_gap_records=official_gaps,
            needs_review_records=alias_rows,
            score=86.0,
            strengths=[
                "Separates denominator coverage from person extraction",
                "Makes missing programs auditable instead of invisible",
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
                "coverage_gaps": official_gaps,
                "gap_reasons": gap_reasons,
                "alias_candidate_rows": alias_rows,
                "coverage_mutation_allowed_rows": alias_mutations,
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
            accepted_records=roster_extracted,
            candidate_records=gap_sources,
            needs_review_records=roster_candidates,
            blocked_records=roster_sources_attempted - roster_sources_with_records,
            score=81.0,
            strengths=[
                "Consumes only high-priority roster-like candidate URLs",
                "Keeps unsupported page structures queued instead of fabricating weak people",
                "Adds non-Medicine coverage from official public pages",
            ],
            limitations=[
                "Parser coverage is page-template specific",
                "Some candidate pages are related tracks rather than the official denominator row",
                "Unsupported structures need parser or manual review",
            ],
            recommended_next_action="add_supported_parsers_for_roster_candidate_gaps_then_rerun_coverage",
            evidence={
                "candidate_source_rows": gap_sources,
                "roster_source_candidates": roster_candidates,
                "sources_attempted": roster_sources_attempted,
                "sources_with_records": roster_sources_with_records,
                "person_records": roster_extracted,
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
            scorecard_key="public_contact_candidate_extraction",
            utility_key="official_profile",
            utility_label="Public contact candidate extraction",
            source_family="official_institutional_web",
            claim_surface="public email/contact channels with scope and verification status",
            input_records=contact_count,
            output_records=contact_count,
            candidate_records=contact_count,
            needs_review_records=contact_count,
            score=66.0,
            strengths=[
                "Stores contact channels separately from person identity truth",
                "Retains source, scope, verification status, confidence, and candidate status",
                "Supports future email/phone assurance without dropping public data",
            ],
            limitations=[
                "Current contacts are public-directory/profile unverified candidates",
                "Contact channels can be stale or role-specific",
                "No phone-support assurance layer exists yet",
            ],
            recommended_next_action="verify_contact_channels_against_current_official_source_before_use",
            evidence={"contact_count": contact_count, "by_verification_status": contact_by_verification},
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
                "Supports person, program, institution, and category diff views",
            ],
            limitations=[
                "Lifecycle codes are local until external program identifiers are verified",
                "Unknown-duration, research, chief, postdoc, and PhD states require fresh source evidence",
                "Annual clocks are assumptions attached to program lifecycle rules, not source facts",
            ],
            recommended_next_action="use_state_machine_expectations_before_mutating_next_year_roster_diffs",
            evidence={
                "state_rows": state_rows,
                "machine_status": machine_status,
                "longitudinal_readiness_status": readiness_status,
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
