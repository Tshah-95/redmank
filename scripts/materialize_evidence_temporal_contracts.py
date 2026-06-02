#!/usr/bin/env python3
"""Materialize temporal contracts for enrichment and evidence facts."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "evidence_temporal_contracts.csv"
JSON_PATH = ARTIFACTS / "evidence_temporal_contracts.json"
ROLLUP_CSV_PATH = ARTIFACTS / "evidence_temporal_contract_rollups.csv"
ROLLUP_JSON_PATH = ARTIFACTS / "evidence_temporal_contract_rollups.json"
SUMMARY_PATH = ARTIFACTS / "evidence_temporal_contract_summary.json"

AS_OF_DATE = date(2026, 6, 2)

CONTRACT_FIELDS = [
    "contract_key",
    "subject_type",
    "subject_key",
    "person_key",
    "display_name",
    "role",
    "record_type",
    "record_id",
    "fact_family",
    "claim_type",
    "claim_value",
    "source_key",
    "source_url",
    "source_type",
    "source_observed_at",
    "source_sha256",
    "source_freshness_class",
    "fact_temporality",
    "currentness_dependency",
    "identity_assurance_requirement",
    "refresh_interval_days",
    "stale_after_date",
    "next_refresh_contract",
    "invalidation_triggers_json",
    "stale_information_policy",
    "display_safety_status",
    "acceptance_status",
    "assurance_level",
    "confidence",
    "current_contract_status",
    "recommended_operator_action",
    "evidence_json",
    "generated_at",
]

ROLLUP_FIELDS = [
    "rollup_key",
    "rollup_scope",
    "rollup_value",
    "fact_family",
    "record_type",
    "contract_count",
    "person_count",
    "source_count",
    "accepted_count",
    "candidate_or_review_count",
    "stale_count",
    "refresh_required_count",
    "durable_count",
    "review_bound_count",
    "dominant_next_refresh_contract",
    "guardrail_status",
    "recommended_operator_action",
    "evidence_json",
    "generated_at",
]


csv.field_size_limit(sys.maxsize)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key_for(prefix: str, parts: tuple[str, ...]) -> str:
    return f"{prefix}_{sha256_text(dumps(parts))[:20]}"


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def add_days(value: str | None, days: int | None) -> str:
    if days is None:
        return ""
    observed = parse_date(value)
    if not observed:
        return ""
    return (observed + timedelta(days=days)).isoformat()


def is_stale(stale_after_date: str) -> bool:
    stale_after = parse_date(stale_after_date)
    return stale_after is not None and stale_after < AS_OF_DATE


def load_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def people_index(conn: sqlite3.Connection) -> dict[str, dict]:
    return {
        row["person_key"]: row
        for row in sqlite_rows(conn, "SELECT person_key, display_name, role FROM people")
    }


def sources_index(conn: sqlite3.Connection) -> dict[str, dict]:
    return {
        row["source_key"]: row
        for row in sqlite_rows(
            conn,
            """
            SELECT source_key, source_url, source_type, fetched_at, sha256, classification, quality_tier
            FROM sources
            """,
        )
    }


def source_context(row: dict, sources: dict[str, dict]) -> dict:
    source_key = row.get("source_key") or ""
    source = sources.get(source_key, {})
    source_url = row.get("source_url") or source.get("source_url") or ""
    return {
        "source_key": source_key,
        "source_url": source_url,
        "source_type": row.get("source_type") or source.get("source_type") or "",
        "source_observed_at": source.get("fetched_at") or row.get("accepted_at") or row.get("materialized_at") or "",
        "source_sha256": row.get("source_sha256") or source.get("sha256") or "",
        "source_classification": source.get("classification") or "",
        "source_quality_tier": source.get("quality_tier") or "",
    }


def policy_for(record_type: str, claim_type: str, status: str, display_safety_status: str) -> dict:
    text = " ".join([record_type, claim_type, status, display_safety_status]).lower()
    accepted = status == "accepted" or status.startswith("accepted") or "accepted_" in status

    if "contact" in text or "email" in text:
        return {
            "fact_family": "contact",
            "fact_temporality": "current_contact_channel",
            "currentness_dependency": "fresh_official_directory_or_profile_reobservation",
            "identity_assurance_requirement": "same_person_current_official_source_and_same_contact_value",
            "refresh_interval_days": 90,
            "next_refresh_contract": "verify_same_contact_value_on_current_official_source_before_use",
            "invalidation_triggers": [
                "contact_value_missing_from_fresh_official_source",
                "contact_value_changed",
                "domain_anomaly",
                "person_identity_mismatch",
            ],
            "stale_information_policy": "do_not_treat_public_contact_candidate_as_verified_or_outreach-ready without fresh official reobservation or explicit reviewer acceptance",
            "recommended_operator_action": "refresh_public_contact_source_or_record_explicit_contact_review",
            "source_freshness_class": "short_lived_current_contact",
        }

    if "current_penn_attending" in text or record_type == "accepted_attending_trend_fact":
        return {
            "fact_family": "attending_trend",
            "fact_temporality": "mixed_current_endpoint_and_historical_training",
            "currentness_dependency": "current_penn_endpoint_requires_periodic_refresh; historical_training_line_is_durable_once_identity_confirmed",
            "identity_assurance_requirement": "same_person_current_endpoint_and_penn_training_bridge",
            "refresh_interval_days": 180,
            "next_refresh_contract": "refresh_current_attending_endpoint_before_using_as_current_trend_fact",
            "invalidation_triggers": [
                "current_penn_endpoint_absent_or_changed",
                "training_bridge_date_or_organization_conflicts",
                "same_person_identity_conflict",
            ],
            "stale_information_policy": "retain historical training evidence, but reobserve current Penn endpoint before trend-line currentness claims",
            "recommended_operator_action": "refresh_current_attending_endpoint_and_preserve_training_bridge_provenance",
            "source_freshness_class": "current_endpoint_plus_durable_history",
        }

    if "official_profile_url" in text:
        return {
            "fact_family": "official_profile",
            "fact_temporality": "profile_location",
            "currentness_dependency": "profile_url_and_page_hash_require_periodic_reobservation; not roster truth",
            "identity_assurance_requirement": "same_person_official_source_profile_context_and_matching_source_hash",
            "refresh_interval_days": 180,
            "next_refresh_contract": "reobserve_profile_url_hash_before_promoting_or_reusing_profile_context",
            "invalidation_triggers": [
                "profile_url_404_or_redirects_to_unrelated_page",
                "source_hash_changed",
                "official_source_ownership_changed",
                "profile_context_no_longer_matches_person",
            ],
            "stale_information_policy": "profile URL facts do not prove current trainee status and must be reobserved before reuse as current profile context",
            "recommended_operator_action": "refresh_official_profile_url_or_keep_as_historical_profile_locator",
            "source_freshness_class": "medium_lived_profile_locator",
        }

    if "pubmed" in text or "orcid" in text or "research_author" in text or "publication" in text:
        return {
            "fact_family": "research",
            "fact_temporality": "durable_scholarly_work_identity_link",
            "currentness_dependency": "published work does not expire; author identity and corpus completeness require review or refresh",
            "identity_assurance_requirement": "same_person_publication_author_position_topic_affiliation_or_identifier_anchor",
            "refresh_interval_days": None,
            "next_refresh_contract": "retain_publication_fact_but_refresh_research_search_for_new_outputs",
            "invalidation_triggers": [
                "same_name_different_author_conflict",
                "author_position_or_identifier_conflict",
                "retracted_or_duplicate_article_context",
            ],
            "stale_information_policy": "accepted publication facts are durable; candidate publication links remain review-bound until identity is confirmed",
            "recommended_operator_action": "review_identity_anchors_then_periodically_collect_new_publications",
            "source_freshness_class": "durable_fact_with_periodic_collection_gap",
        }

    if any(token in text for token in ["medical_school", "education_history", "undergraduate", "graduate_school", "residency_program", "prior_training"]):
        return {
            "fact_family": "prior_training_or_education",
            "fact_temporality": "historical_background",
            "currentness_dependency": "historical once verified; source profile may change but completed training should not time-expire",
            "identity_assurance_requirement": "same_person_profile_or_corroborating_training_source",
            "refresh_interval_days": None if accepted else 365,
            "next_refresh_contract": "retain_historical_fact_once_verified; refresh_candidate_source_before_acceptance",
            "invalidation_triggers": [
                "source_removes_or_changes_training_line",
                "conflicting_corroborated_background_source",
                "same_person_identity_conflict",
            ],
            "stale_information_policy": "do not treat profile-derived background candidates as accepted history without review or corroboration",
            "recommended_operator_action": "confirm_background_field_or_collect_corroborating_source",
            "source_freshness_class": "durable_history_after_acceptance",
        }

    if "personal_profile" in text or "career_interest" in text or "research_interest" in text:
        return {
            "fact_family": "profile_context",
            "fact_temporality": "self_described_context_at_source_time",
            "currentness_dependency": "profile context can change and has display-safety constraints",
            "identity_assurance_requirement": "same_person_official_profile_context_and_display_policy_review",
            "refresh_interval_days": 365,
            "next_refresh_contract": "reobserve_profile_context_before_default_display_or_current-interest_claim",
            "invalidation_triggers": [
                "profile_context_changed",
                "display_safety_policy_changes",
                "same_person_identity_conflict",
            ],
            "stale_information_policy": "personal/profile context is candidate context only unless display policy and source recency are satisfied",
            "recommended_operator_action": "reobserve_profile_context_and_apply_display_safety_review",
            "source_freshness_class": "display_policy_bound_profile_context",
        }

    return {
        "fact_family": "general_evidence",
        "fact_temporality": "source_observed_claim",
        "currentness_dependency": "depends_on_source_family_and_claim_type",
        "identity_assurance_requirement": "claim_specific_identity_and_source_context_review",
        "refresh_interval_days": 365,
        "next_refresh_contract": "review_source_family_before_mutation",
        "invalidation_triggers": ["source_changed", "identity_conflict", "claim_context_conflict"],
        "stale_information_policy": "do not mutate person truth from stale or unclassified evidence without review",
        "recommended_operator_action": "classify_claim_family_and_record_review_decision",
        "source_freshness_class": "unclassified_review_bound",
    }


def contract_status(policy: dict, stale_after_date: str, status: str) -> str:
    normalized_status = (status or "").lower()
    if is_stale(stale_after_date):
        return "stale_refresh_required"
    if (
        normalized_status in {"candidate", "needs_review", "pending", "public_unverified"}
        or "review" in normalized_status
        or "unverified" in normalized_status
        or "low_signal" in normalized_status
        or "partial_anchor" in normalized_status
    ):
        return "review_bound_not_accepted_truth"
    if policy["refresh_interval_days"] is None:
        return "durable_until_contradicted"
    return "fresh_until_stale_after"


def build_contract(base: dict, sources: dict[str, dict], generated_at: str) -> dict:
    context = source_context(base, sources)
    policy = policy_for(
        base["record_type"],
        base["claim_type"],
        base.get("acceptance_status") or base.get("status") or "",
        base.get("display_safety_status") or "",
    )
    stale_after = add_days(context["source_observed_at"], policy["refresh_interval_days"])
    status = contract_status(policy, stale_after, base.get("acceptance_status") or base.get("status") or "")
    evidence = {
        "record": {key: base.get(key, "") for key in sorted(base) if key != "evidence_json"},
        "source_context": context,
        "contract_policy": {
            "as_of_date": AS_OF_DATE.isoformat(),
            "refresh_interval_days": policy["refresh_interval_days"],
            "invalidation_triggers": policy["invalidation_triggers"],
            "next_refresh_contract": policy["next_refresh_contract"],
        },
    }
    row = {
        "contract_key": key_for("evidence_contract", (base["record_type"], str(base["record_id"]), base["claim_type"])),
        "subject_type": base.get("subject_type") or "person",
        "subject_key": base.get("subject_key") or base.get("person_key") or base["record_id"],
        "person_key": base.get("person_key") or None,
        "display_name": base.get("display_name") or "",
        "role": base.get("role") or "",
        "record_type": base["record_type"],
        "record_id": str(base["record_id"]),
        "fact_family": policy["fact_family"],
        "claim_type": base["claim_type"],
        "claim_value": base.get("claim_value") or "",
        "source_key": context["source_key"],
        "source_url": context["source_url"],
        "source_type": context["source_type"],
        "source_observed_at": context["source_observed_at"],
        "source_sha256": context["source_sha256"],
        "source_freshness_class": policy["source_freshness_class"],
        "fact_temporality": policy["fact_temporality"],
        "currentness_dependency": policy["currentness_dependency"],
        "identity_assurance_requirement": policy["identity_assurance_requirement"],
        "refresh_interval_days": "" if policy["refresh_interval_days"] is None else policy["refresh_interval_days"],
        "stale_after_date": stale_after,
        "next_refresh_contract": policy["next_refresh_contract"],
        "invalidation_triggers_json": dumps(policy["invalidation_triggers"]),
        "stale_information_policy": policy["stale_information_policy"],
        "display_safety_status": base.get("display_safety_status") or "",
        "acceptance_status": base.get("acceptance_status") or base.get("status") or "",
        "assurance_level": base.get("assurance_level") or 0,
        "confidence": base.get("confidence") or 0,
        "current_contract_status": status,
        "recommended_operator_action": policy["recommended_operator_action"],
        "evidence_json": dumps(evidence),
        "generated_at": generated_at,
    }
    return {field: row[field] for field in CONTRACT_FIELDS}


def evidence_claim_bases(conn: sqlite3.Connection, people: dict[str, dict]) -> list[dict]:
    rows = sqlite_rows(conn, "SELECT * FROM evidence_claims")
    bases = []
    for row in rows:
        person = people.get(row.get("person_key") or "", {})
        bases.append(
            {
                "subject_type": "person",
                "subject_key": row.get("person_key") or f"evidence_claim:{row['evidence_id']}",
                "person_key": row.get("person_key") or "",
                "display_name": person.get("display_name") or "",
                "role": person.get("role") or "",
                "record_type": "evidence_claim",
                "record_id": row["evidence_id"],
                "claim_type": row["claim_type"],
                "claim_value": row["claim_value"],
                "source_key": row.get("source_key") or "",
                "source_url": row.get("source_url") or "",
                "source_type": row.get("source_type") or "",
                "confidence": row.get("confidence") or 0,
                "status": row.get("status") or "",
                "evidence_json": row.get("evidence_json") or "",
            }
        )
    return bases


def contact_bases(conn: sqlite3.Connection, people: dict[str, dict]) -> list[dict]:
    rows = sqlite_rows(conn, "SELECT * FROM person_contacts")
    bases = []
    for row in rows:
        person = people.get(row.get("person_key") or "", {})
        bases.append(
            {
                "subject_type": row.get("subject_type") or "person",
                "subject_key": row.get("person_key") or row["contact_key"],
                "person_key": row.get("person_key") or "",
                "display_name": row.get("display_name") or person.get("display_name") or "",
                "role": person.get("role") or "",
                "record_type": "person_contact",
                "record_id": row["contact_key"],
                "claim_type": row["contact_type"],
                "claim_value": row["contact_value"],
                "source_key": row.get("source_key") or "",
                "source_url": row.get("source_url") or "",
                "source_type": row.get("source_type") or "",
                "confidence": row.get("confidence") or 0,
                "status": row.get("verification_status") or row.get("status") or "",
                "display_safety_status": row.get("status") or "",
                "evidence_json": row.get("evidence_json") or "",
            }
        )
    return bases


def accepted_enrichment_bases(conn: sqlite3.Connection) -> list[dict]:
    return [
        {
            "subject_type": "person",
            "subject_key": row.get("person_key") or row["accepted_enrichment_key"],
            "person_key": row.get("person_key") or "",
            "display_name": row.get("display_name") or "",
            "role": row.get("role") or "",
            "record_type": "accepted_enrichment_claim",
            "record_id": row["accepted_enrichment_key"],
            "claim_type": row.get("claim_type") or row.get("enrichment_type") or "",
            "claim_value": row.get("claim_value") or "",
            "source_key": row.get("source_key") or "",
            "source_url": row.get("source_url") or "",
            "source_type": "",
            "confidence": row.get("confidence") or 0,
            "acceptance_status": row.get("acceptance_status") or "accepted",
            "assurance_level": row.get("assurance_level") or 0,
            "display_safety_status": row.get("display_safety_status") or "",
            "accepted_at": row.get("accepted_at") or "",
            "evidence_json": row.get("evidence_json") or "",
        }
        for row in sqlite_rows(conn, "SELECT * FROM accepted_enrichment_claims")
    ]


def accepted_profile_bases(conn: sqlite3.Connection) -> list[dict]:
    return [
        {
            "subject_type": "person",
            "subject_key": row.get("person_key") or row["accepted_profile_key"],
            "person_key": row.get("person_key") or "",
            "display_name": row.get("display_name") or "",
            "role": row.get("role") or "",
            "record_type": "accepted_official_profile_url_fact",
            "record_id": row["accepted_profile_key"],
            "claim_type": "official_profile_url",
            "claim_value": row.get("profile_url") or "",
            "source_key": "",
            "source_url": row.get("profile_url") or "",
            "source_type": "official_profile",
            "source_sha256": row.get("source_sha256") or "",
            "confidence": 1,
            "acceptance_status": "accepted",
            "assurance_level": 4,
            "display_safety_status": row.get("display_safety_status") or "",
            "accepted_at": row.get("accepted_at") or row.get("materialized_at") or "",
            "materialized_at": row.get("materialized_at") or "",
            "evidence_json": row.get("evidence_json") or "",
        }
        for row in sqlite_rows(conn, "SELECT * FROM accepted_official_profile_url_facts")
    ]


def accepted_contact_bases(conn: sqlite3.Connection) -> list[dict]:
    return [
        {
            "subject_type": "person",
            "subject_key": row.get("person_key") or row["accepted_contact_key"],
            "person_key": row.get("person_key") or "",
            "display_name": row.get("display_name") or "",
            "role": row.get("role") or "",
            "record_type": "accepted_verified_contact_fact",
            "record_id": row["accepted_contact_key"],
            "claim_type": row.get("contact_type") or "contact",
            "claim_value": row.get("normalized_contact_value") or "",
            "source_key": "",
            "source_url": row.get("reobserved_source_url") or row.get("source_url") or "",
            "source_type": "official_contact_reobservation",
            "confidence": 1,
            "acceptance_status": "accepted",
            "assurance_level": 4,
            "display_safety_status": row.get("display_safety_status") or "",
            "accepted_at": row.get("accepted_at") or row.get("materialized_at") or "",
            "materialized_at": row.get("materialized_at") or "",
            "evidence_json": row.get("evidence_json") or "",
        }
        for row in sqlite_rows(conn, "SELECT * FROM accepted_verified_contact_facts")
    ]


def accepted_trend_bases(conn: sqlite3.Connection) -> list[dict]:
    return [
        {
            "subject_type": "attending_trend_group",
            "subject_key": row.get("event_group_key") or row["trend_fact_key"],
            "person_key": "",
            "display_name": row.get("display_name") or "",
            "role": "current_penn_attending_candidate",
            "record_type": "accepted_attending_trend_fact",
            "record_id": row["trend_fact_key"],
            "claim_type": row.get("trend_fact_type") or "recent_penn_trained_current_attending",
            "claim_value": row.get("training_line") or "",
            "source_key": row.get("source_key") or "",
            "source_url": row.get("source_url") or "",
            "source_type": row.get("source_scope") or "",
            "confidence": 1,
            "acceptance_status": "accepted",
            "assurance_level": 4,
            "display_safety_status": row.get("display_safety_status") or "",
            "accepted_at": row.get("accepted_at") or row.get("materialized_at") or "",
            "materialized_at": row.get("materialized_at") or "",
            "evidence_json": row.get("evidence_json") or "",
        }
        for row in sqlite_rows(conn, "SELECT * FROM accepted_attending_trend_facts")
    ]


def all_contracts(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    people = people_index(conn)
    sources = sources_index(conn)
    bases = []
    bases.extend(evidence_claim_bases(conn, people))
    bases.extend(contact_bases(conn, people))
    bases.extend(accepted_enrichment_bases(conn))
    bases.extend(accepted_profile_bases(conn))
    bases.extend(accepted_contact_bases(conn))
    bases.extend(accepted_trend_bases(conn))
    for base in bases:
        if base.get("person_key") and base["person_key"] not in people:
            base["person_key"] = ""
    return [build_contract(base, sources, generated_at) for base in bases]


def guardrail_status(rows: list[dict]) -> str:
    statuses = Counter(row["current_contract_status"] for row in rows)
    if statuses.get("stale_refresh_required"):
        return "stale_refresh_required"
    if statuses.get("review_bound_not_accepted_truth"):
        return "review_bound"
    if any(row["refresh_interval_days"] not in ("", None) for row in rows):
        return "refresh_bound"
    return "durable_until_contradicted"


def dominant(rows: list[dict], field: str) -> str:
    counts = Counter(row[field] for row in rows if row.get(field))
    if not counts:
        return ""
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def rollup_rows(contracts: list[dict], generated_at: str) -> list[dict]:
    groups: dict[tuple[str, str, str, str], list[dict]] = {}
    for row in contracts:
        specs = [
            ("corpus", "all", "", ""),
            ("fact_family", row["fact_family"], row["fact_family"], ""),
            ("record_type", row["record_type"], "", row["record_type"]),
            ("current_contract_status", row["current_contract_status"], "", ""),
            ("next_refresh_contract", row["next_refresh_contract"], row["fact_family"], ""),
            ("role", row["role"] or "unknown", "", ""),
        ]
        for scope, value, family, record_type in specs:
            groups.setdefault((scope, value, family, record_type), []).append(row)

    rollups = []
    for (scope, value, family, record_type), rows in sorted(groups.items()):
        status = guardrail_status(rows)
        evidence = {
            "by_current_contract_status": dict(sorted(Counter(row["current_contract_status"] for row in rows).items())),
            "by_fact_family": dict(sorted(Counter(row["fact_family"] for row in rows).items())),
            "by_record_type": dict(sorted(Counter(row["record_type"] for row in rows).items())),
            "by_next_refresh_contract": dict(sorted(Counter(row["next_refresh_contract"] for row in rows).items())),
        }
        rollup = {
            "rollup_key": key_for("evidence_contract_rollup", (scope, value, family, record_type)),
            "rollup_scope": scope,
            "rollup_value": value,
            "fact_family": family,
            "record_type": record_type,
            "contract_count": len(rows),
            "person_count": len({row["person_key"] for row in rows if row.get("person_key")}),
            "source_count": len({row["source_key"] or row["source_url"] for row in rows if row.get("source_key") or row.get("source_url")}),
            "accepted_count": sum(1 for row in rows if row.get("acceptance_status") == "accepted" or row.get("acceptance_status") == "accepted_for_enrichment_not_roster_truth"),
            "candidate_or_review_count": sum(1 for row in rows if row["current_contract_status"] == "review_bound_not_accepted_truth"),
            "stale_count": sum(1 for row in rows if row["current_contract_status"] == "stale_refresh_required"),
            "refresh_required_count": sum(1 for row in rows if row["refresh_interval_days"] not in ("", None)),
            "durable_count": sum(1 for row in rows if row["current_contract_status"] == "durable_until_contradicted"),
            "review_bound_count": sum(1 for row in rows if row["current_contract_status"] == "review_bound_not_accepted_truth"),
            "dominant_next_refresh_contract": dominant(rows, "next_refresh_contract"),
            "guardrail_status": status,
            "recommended_operator_action": dominant(rows, "recommended_operator_action"),
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        rollups.append({field: rollup[field] for field in ROLLUP_FIELDS})
    return rollups


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_db(conn: sqlite3.Connection, table: str, rows: list[dict], fields: list[str]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    field_sql = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    conn.executemany(f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(contracts: list[dict], rollups: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "as_of_date": AS_OF_DATE.isoformat(),
        "contract_rows": len(contracts),
        "rollup_rows": len(rollups),
        "person_count": len({row["person_key"] for row in contracts if row.get("person_key")}),
        "source_count": len({row["source_key"] or row["source_url"] for row in contracts if row.get("source_key") or row.get("source_url")}),
        "by_fact_family": dict(sorted(Counter(row["fact_family"] for row in contracts).items())),
        "by_record_type": dict(sorted(Counter(row["record_type"] for row in contracts).items())),
        "by_current_contract_status": dict(sorted(Counter(row["current_contract_status"] for row in contracts).items())),
        "by_next_refresh_contract": dict(sorted(Counter(row["next_refresh_contract"] for row in contracts).items())),
        "stale_refresh_required_rows": sum(1 for row in contracts if row["current_contract_status"] == "stale_refresh_required"),
        "review_bound_rows": sum(1 for row in contracts if row["current_contract_status"] == "review_bound_not_accepted_truth"),
        "durable_until_contradicted_rows": sum(1 for row in contracts if row["current_contract_status"] == "durable_until_contradicted"),
        "refresh_bound_rows": sum(1 for row in contracts if row["refresh_interval_days"] not in ("", None)),
        "policy": "Evidence temporal contracts are non-mutating. They describe when enrichment facts can be retained, refreshed, reviewed, or invalidated before any person truth or display surface is updated.",
        "contracts_csv": str(CSV_PATH.relative_to(ROOT)),
        "rollups_csv": str(ROLLUP_CSV_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    contracts = all_contracts(conn, generated_at)
    rollups = rollup_rows(contracts, generated_at)
    write_csv(CSV_PATH, contracts, CONTRACT_FIELDS)
    write_json(JSON_PATH, contracts)
    write_csv(ROLLUP_CSV_PATH, rollups, ROLLUP_FIELDS)
    write_json(ROLLUP_JSON_PATH, rollups)
    with conn:
        write_db(conn, "evidence_temporal_contracts", contracts, CONTRACT_FIELDS)
        write_db(conn, "evidence_temporal_contract_rollups", rollups, ROLLUP_FIELDS)
    conn.close()
    write_summary(contracts, rollups, generated_at)
    print(dumps({"evidence_temporal_contracts": len(contracts), "evidence_temporal_contract_rollups": len(rollups)}))


if __name__ == "__main__":
    main()
