#!/usr/bin/env python3
"""Materialize person-level research identity corroboration and conflict routing."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "research_identity_corroboration.csv"
JSON_PATH = ARTIFACTS / "research_identity_corroboration.json"
SUMMARY_PATH = ARTIFACTS / "research_identity_corroboration_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "corroboration_key",
    "person_key",
    "display_name",
    "role",
    "programs",
    "current_training_states",
    "research_identity_status",
    "review_priority",
    "scholarly_source_count",
    "research_candidate_count",
    "research_review_ready_count",
    "accepted_research_count",
    "pubmed_article_candidate_count",
    "pubmed_review_ready_count",
    "openalex_author_candidate_count",
    "openalex_review_ready_count",
    "orcid_profile_candidate_count",
    "orcid_work_candidate_count",
    "orcid_pubmed_article_candidate_count",
    "npi_candidate_count",
    "profile_candidate_count",
    "contact_candidate_count",
    "non_name_anchor_count",
    "name_only_candidate_count",
    "penn_affiliation_anchor_count",
    "prior_training_anchor_count",
    "persistent_identifier_count",
    "publication_identifier_count",
    "conflicting_identifier_count",
    "best_confidence",
    "top_source_keys",
    "top_claim_types",
    "recommended_review_route",
    "required_next_evidence",
    "acceptance_boundary",
    "evidence_json",
    "generated_at",
]

RESEARCH_CLAIM_TYPES = {
    "pubmed_author_query_candidate",
    "pubmed_article_candidate",
    "research_author_candidate",
    "orcid_profile_candidate",
    "orcid_work_candidate",
    "orcid_pubmed_article_candidate",
    "openalex_work_candidate",
}

SCHOLARLY_SOURCE_KEYS = {
    "pubmed_eutilities",
    "openalex_author_search",
    "openalex_work_search",
    "orcid_public_api",
}

NON_NAME_FEATURES = {
    "bounded_author_query",
    "doi_present",
    "pmid_present",
    "orcid_external_ids_present",
    "orcid_from_openalex_author_candidate",
    "orcid_penn_affiliation",
    "orcid_profile_public",
    "orcid_record_public",
    "orcid_researcher_urls_present",
    "orcid_works_present",
    "penn_affiliation",
    "penn_affiliation_from_author_candidate",
    "prior_training_or_education_affiliation",
    "program_topic_match",
    "recent_publication",
    "ten_year_publication_window",
    "work_penn_affiliation",
}

PENN_FEATURES = {
    "orcid_penn_affiliation",
    "penn_affiliation",
    "penn_affiliation_from_author_candidate",
    "work_penn_affiliation",
}

PRIOR_FEATURES = {"prior_training_or_education_affiliation"}
PERSISTENT_ID_FEATURES = {"doi_present", "pmid_present", "orcid_external_ids_present"}
PUBLICATION_ID_CLAIMS = {"pubmed_article_candidate", "orcid_pubmed_article_candidate", "orcid_work_candidate", "openalex_work_candidate"}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key_for(person_key: str) -> str:
    return "research_identity_corroboration_" + sha256_text(person_key)[:20]


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["corroboration_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["corroboration_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def people(conn: sqlite3.Connection) -> list[dict]:
    rows = sqlite_rows(conn, "SELECT person_key, display_name, role, raw_json FROM people ORDER BY display_name, person_key")
    for row in rows:
        raw = parse_json(row.get("raw_json"), {})
        programs = raw.get("program_memberships") or []
        if not programs and raw.get("program"):
            programs = [raw["program"]]
        row["programs"] = "; ".join(str(program) for program in programs if str(program).strip())
    return rows


def stage_states(conn: sqlite3.Connection) -> dict[str, str]:
    by_person: dict[str, list[str]] = defaultdict(list)
    for row in sqlite_rows(
        conn,
        """
        SELECT person_key, program_name, current_stage_code, current_temporal_state_code,
               policy_lane, diff_readiness_status
        FROM person_training_stage_state
        ORDER BY person_key, program_name, current_stage_code
        """,
    ):
        state = " | ".join(
            part
            for part in [
                row.get("program_name") or "",
                row.get("current_stage_code") or "",
                row.get("current_temporal_state_code") or "",
                row.get("policy_lane") or "",
                row.get("diff_readiness_status") or "",
            ]
            if part
        )
        if state and state not in by_person[row["person_key"]]:
            by_person[row["person_key"]].append(state)
    return {person_key: "; ".join(values[:8]) for person_key, values in by_person.items()}


def evidence_claims(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    by_person: dict[str, list[dict]] = defaultdict(list)
    for row in sqlite_rows(
        conn,
        """
        SELECT evidence_id, person_key, claim_type, claim_value, source_key, source_url,
               source_type, confidence, status, match_features_json, reconciliation_notes, evidence_json
        FROM evidence_claims
        WHERE person_key IS NOT NULL
        ORDER BY person_key, confidence DESC, evidence_id
        """,
    ):
        claim_type = row.get("claim_type") or ""
        source_key = row.get("source_key") or ""
        if claim_type not in RESEARCH_CLAIM_TYPES and source_key not in SCHOLARLY_SOURCE_KEYS:
            continue
        row["match_features"] = parse_json(row.get("match_features_json"), [])
        row["evidence"] = parse_json(row.get("evidence_json"), {})
        by_person[row["person_key"]].append(row)
    return by_person


def npi_candidates(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    by_person: dict[str, list[dict]] = defaultdict(list)
    for row in sqlite_rows(
        conn,
        """
        SELECT person_key, npi, provider_name, provider_credential, primary_taxonomy,
               practice_city, practice_state, candidate_status, confidence, source_url,
               match_features_json, evidence_json
        FROM npi_candidate_claims
        ORDER BY person_key, confidence DESC, result_rank
        """,
    ):
        row["match_features"] = parse_json(row.get("match_features_json"), [])
        row["evidence"] = parse_json(row.get("evidence_json"), {})
        by_person[row["person_key"]].append(row)
    return by_person


def profile_candidates(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    by_person: dict[str, list[dict]] = defaultdict(list)
    for row in sqlite_rows(
        conn,
        """
        SELECT person_key, candidate_status, priority, confidence, candidate_title,
               candidate_url, result_domain, match_features_json, required_next_evidence,
               evidence_json
        FROM trainee_profile_discovery_candidates
        WHERE person_key IS NOT NULL
        ORDER BY person_key, confidence DESC, priority DESC
        """,
    ):
        row["match_features"] = parse_json(row.get("match_features_json"), [])
        row["evidence"] = parse_json(row.get("evidence_json"), {})
        by_person[row["person_key"]].append(row)
    return by_person


def contact_candidates(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    by_person: dict[str, list[dict]] = defaultdict(list)
    for row in sqlite_rows(
        conn,
        """
        SELECT person_key, contact_type, contact_value, contact_scope, source_key,
               source_url, verification_status, confidence, status, match_features_json,
               evidence_json
        FROM person_contacts
        WHERE person_key IS NOT NULL
        ORDER BY person_key, confidence DESC, contact_type
        """,
    ):
        row["match_features"] = parse_json(row.get("match_features_json"), [])
        row["evidence"] = parse_json(row.get("evidence_json"), {})
        by_person[row["person_key"]].append(row)
    return by_person


def feature_counts(claims: list[dict]) -> Counter:
    return Counter(feature for claim in claims for feature in claim.get("match_features", []))


def unique_values(claims: list[dict], claim_types: set[str]) -> set[str]:
    return {
        str(claim.get("claim_value") or "").strip()
        for claim in claims
        if claim.get("claim_type") in claim_types and str(claim.get("claim_value") or "").strip()
    }


def status_for(metrics: dict) -> str:
    if metrics["conflicting_identifier_count"]:
        return "conflict_review_required"
    if metrics["scholarly_source_count"] >= 3 and metrics["non_name_anchor_count"] >= 3 and metrics["research_review_ready_count"]:
        return "strong_multi_source_research_identity_review"
    if metrics["scholarly_source_count"] >= 2 and metrics["non_name_anchor_count"] >= 2:
        return "multi_source_candidate_review"
    if metrics["research_review_ready_count"] and metrics["npi_candidate_count"]:
        return "research_plus_secondary_identity_anchor_review"
    if metrics["research_review_ready_count"]:
        return "single_source_research_review_ready"
    if metrics["research_candidate_count"]:
        return "research_candidate_only"
    if metrics["npi_candidate_count"] or metrics["profile_candidate_count"] or metrics["contact_candidate_count"]:
        return "secondary_anchor_without_research_signal"
    return "no_public_research_identity_signal"


def review_route(status: str) -> tuple[str, str, int]:
    if status == "conflict_review_required":
        return (
            "manual_conflict_reconciliation_before_any_acceptance",
            "Resolve conflicting persistent identifiers or candidate identities with official profile, ORCID/PMID/DOI author position, and non-name institutional anchors.",
            100,
        )
    if status == "strong_multi_source_research_identity_review":
        return (
            "prioritize_publication_identity_review",
            "Review article-level authorship plus ORCID/OpenAlex/source profile anchors; promote only after reviewer records accepted same-person evidence.",
            95,
        )
    if status == "multi_source_candidate_review":
        return (
            "review_cross_source_identity_agreement",
            "Confirm independent source agreement across scholarly APIs and at least one non-name anchor before accepting research enrichment.",
            85,
        )
    if status == "research_plus_secondary_identity_anchor_review":
        return (
            "review_research_with_secondary_identity_anchor",
            "Use NPI/profile/contact evidence as a secondary anchor; do not accept publications from secondary anchors alone.",
            80,
        )
    if status == "single_source_research_review_ready":
        return (
            "review_single_source_publication_candidate",
            "Find an independent non-name anchor or official profile before accepting same-person publication identity.",
            70,
        )
    if status == "research_candidate_only":
        return (
            "collect_secondary_identity_anchors_before_review",
            "Collect ORCID/OpenAlex/PubMed article detail, official profile, or prior-training anchors before reviewer acceptance.",
            50,
        )
    if status == "secondary_anchor_without_research_signal":
        return (
            "run_research_identity_search_if_research_relevant",
            "Secondary anchors exist but no scholarly identity signal is present; run research collectors only if the program/person surface warrants publication enrichment.",
            35,
        )
    return (
        "no_research_action_until_higher_priority_sources_complete",
        "No public research identity signal is present in current artifacts; avoid interpreting absence as negative evidence.",
        0,
    )


def top_claims(claims: list[dict], npis: list[dict], profiles: list[dict], contacts: list[dict], limit: int = 12) -> list[dict]:
    rows = []
    for claim in claims:
        rows.append(
            {
                "surface": "research_claim",
                "claim_type": claim.get("claim_type"),
                "source_identifier": claim.get("source_key"),
                "status": claim.get("status"),
                "confidence": as_float(claim.get("confidence")),
                "claim_value": claim.get("claim_value"),
                "source_url": claim.get("source_url"),
                "match_features": claim.get("match_features", []),
            }
        )
    for row in npis:
        rows.append(
            {
                "surface": "npi_candidate",
                "claim_type": "npi_candidate",
                "source_identifier": "nppes_npi_registry",
                "status": row.get("candidate_status"),
                "confidence": as_float(row.get("confidence")),
                "claim_value": row.get("npi"),
                "source_url": row.get("source_url"),
                "match_features": row.get("match_features", []),
                "provider_name": row.get("provider_name"),
                "primary_taxonomy": row.get("primary_taxonomy"),
            }
        )
    for row in profiles[:4]:
        rows.append(
            {
                "surface": "profile_discovery_candidate",
                "claim_type": "profile_candidate",
                "source_identifier": row.get("result_domain") or "trainee_profile_discovery",
                "status": row.get("candidate_status"),
                "confidence": as_float(row.get("confidence")),
                "claim_value": row.get("candidate_url"),
                "source_url": row.get("candidate_url"),
                "match_features": row.get("match_features", []),
                "candidate_title": row.get("candidate_title"),
            }
        )
    for row in contacts[:2]:
        rows.append(
            {
                "surface": "contact_candidate",
                "claim_type": row.get("contact_type"),
                "source_identifier": row.get("source_key"),
                "status": row.get("verification_status"),
                "confidence": as_float(row.get("confidence")),
                "claim_value": row.get("contact_value"),
                "source_url": row.get("source_url"),
                "match_features": row.get("match_features", []),
                "contact_scope": row.get("contact_scope"),
            }
        )
    rows.sort(key=lambda item: (item["confidence"], item.get("status") == "needs_review"), reverse=True)
    return rows[:limit]


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    people_rows = people(conn)
    states = stage_states(conn)
    claims_by_person = evidence_claims(conn)
    npi_by_person = npi_candidates(conn)
    profile_by_person = profile_candidates(conn)
    contact_by_person = contact_candidates(conn)
    rows = []
    for person in people_rows:
        person_key = person["person_key"]
        claims = claims_by_person.get(person_key, [])
        npis = npi_by_person.get(person_key, [])
        profiles = profile_by_person.get(person_key, [])
        contacts = contact_by_person.get(person_key, [])
        counts = Counter(claim.get("claim_type") or "" for claim in claims)
        source_keys = sorted({claim.get("source_key") or "" for claim in claims if claim.get("source_key")})
        scholarly_source_count = len({source for source in source_keys if source in SCHOLARLY_SOURCE_KEYS})
        review_ready = [claim for claim in claims if claim.get("status") == "needs_review"]
        accepted = [claim for claim in claims if claim.get("status") == "accepted"]
        features = feature_counts(claims)
        publication_ids = unique_values(claims, PUBLICATION_ID_CLAIMS)
        orcids = unique_values(claims, {"orcid_profile_candidate"})
        openalex_authors = unique_values(claims, {"research_author_candidate"})
        conflict_count = 0
        conflict_count += 1 if len(orcids) > 1 else 0
        conflict_count += 1 if len(openalex_authors) > max(2, scholarly_source_count) and review_ready else 0

        metrics = {
            "scholarly_source_count": scholarly_source_count,
            "research_candidate_count": len(claims),
            "research_review_ready_count": len(review_ready),
            "accepted_research_count": len(accepted),
            "pubmed_article_candidate_count": counts["pubmed_article_candidate"],
            "pubmed_review_ready_count": sum(
                1 for claim in claims if claim.get("claim_type") == "pubmed_article_candidate" and claim.get("status") == "needs_review"
            ),
            "openalex_author_candidate_count": counts["research_author_candidate"],
            "openalex_review_ready_count": sum(
                1 for claim in claims if claim.get("claim_type") == "research_author_candidate" and claim.get("status") == "needs_review"
            ),
            "orcid_profile_candidate_count": counts["orcid_profile_candidate"],
            "orcid_work_candidate_count": counts["orcid_work_candidate"],
            "orcid_pubmed_article_candidate_count": counts["orcid_pubmed_article_candidate"],
            "npi_candidate_count": len(npis),
            "profile_candidate_count": len(profiles),
            "contact_candidate_count": len(contacts),
            "non_name_anchor_count": sum(features[feature] for feature in NON_NAME_FEATURES),
            "name_only_candidate_count": sum(1 for claim in claims if set(claim.get("match_features", [])) <= {"name_match", "article_author_name_match"}),
            "penn_affiliation_anchor_count": sum(features[feature] for feature in PENN_FEATURES),
            "prior_training_anchor_count": sum(features[feature] for feature in PRIOR_FEATURES),
            "persistent_identifier_count": len(orcids) + sum(features[feature] for feature in PERSISTENT_ID_FEATURES),
            "publication_identifier_count": len(publication_ids),
            "conflicting_identifier_count": conflict_count,
            "best_confidence": round(max([as_float(claim.get("confidence")) for claim in claims] + [as_float(row.get("confidence")) for row in npis] + [as_float(row.get("confidence")) for row in profiles] + [0.0]), 3),
        }
        status = status_for(metrics)
        route, required, base_priority = review_route(status)
        priority = base_priority
        priority += min(metrics["research_review_ready_count"], 10)
        priority += min(metrics["non_name_anchor_count"], 10)
        priority += 5 if metrics["npi_candidate_count"] else 0
        priority = min(priority, 100)
        evidence = {
            "policy": {
                "non_mutating": True,
                "corroboration_is_not_acceptance": True,
                "reviewer_decision_required_for_person_fact_acceptance": True,
            },
            "source_agreement": {
                "source_identifiers": source_keys,
                "claim_type_counts": dict(sorted(counts.items())),
                "feature_counts": dict(features.most_common(30)),
                "publication_identifier_count": metrics["publication_identifier_count"],
                "orcid_identifier_count": len(orcids),
                "openalex_author_candidate_count": len(openalex_authors),
            },
            "top_claims": top_claims(claims, npis, profiles, contacts),
        }
        row = {
            "corroboration_key": key_for(person_key),
            "person_key": person_key,
            "display_name": person.get("display_name") or "",
            "role": person.get("role") or "",
            "programs": person.get("programs") or "",
            "current_training_states": states.get(person_key, ""),
            "research_identity_status": status,
            "review_priority": priority,
            "top_source_keys": "; ".join(source_keys[:12]),
            "top_claim_types": "; ".join(f"{claim_type}:{count}" for claim_type, count in counts.most_common(12)),
            "recommended_review_route": route,
            "required_next_evidence": required,
            "acceptance_boundary": (
                "Research identity corroboration is non-mutating. Multi-source agreement can prioritize review, "
                "but accepted person facts require source-specific reviewer and acceptance ledgers."
            ),
            "evidence_json": dumps(evidence),
            "generated_at": "",
            **metrics,
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        rows.append({field: row[field] for field in FIELDS})
    return sorted(rows, key=lambda item: (-int(item["review_priority"]), item["display_name"], item["person_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM research_identity_corroboration")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO research_identity_corroboration ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_status = Counter(row["research_identity_status"] for row in rows)
    by_role = Counter(row["role"] for row in rows)
    by_route = Counter(row["recommended_review_route"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "corroboration_rows": len(rows),
        "people_with_research_signal": sum(1 for row in rows if int(row["research_candidate_count"]) > 0),
        "people_with_review_ready_research": sum(1 for row in rows if int(row["research_review_ready_count"]) > 0),
        "people_with_multi_source_research": sum(1 for row in rows if int(row["scholarly_source_count"]) >= 2),
        "people_with_npi_secondary_anchor": sum(1 for row in rows if int(row["npi_candidate_count"]) > 0),
        "people_with_profile_candidate": sum(1 for row in rows if int(row["profile_candidate_count"]) > 0),
        "by_research_identity_status": dict(sorted(by_status.items())),
        "by_role": dict(sorted(by_role.items())),
        "by_recommended_review_route": dict(sorted(by_route.items())),
        "top_review_priorities": [
            {
                "display_name": row["display_name"],
                "role": row["role"],
                "research_identity_status": row["research_identity_status"],
                "review_priority": row["review_priority"],
                "scholarly_source_count": row["scholarly_source_count"],
                "research_review_ready_count": row["research_review_ready_count"],
                "non_name_anchor_count": row["non_name_anchor_count"],
                "recommended_review_route": row["recommended_review_route"],
            }
            for row in rows[:25]
        ],
        "policy": "Corroboration ranks review and conflict routing only; no person fact is accepted from this ledger.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = build_rows(conn, generated_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"generated_at": generated_at, "research_identity_corroboration": len(rows)}))


if __name__ == "__main__":
    main()
