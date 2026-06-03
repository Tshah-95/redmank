#!/usr/bin/env python3
"""Materialize compact dossiers for research identity reviewer decisions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "research_identity_reviewer_decision_dossiers.csv"
JSON_PATH = ARTIFACTS / "research_identity_reviewer_decision_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "research_identity_reviewer_decision_dossier_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "dossier_key",
    "reviewer_decision_key",
    "review_batch_member_key",
    "review_batch_key",
    "corroboration_key",
    "person_key",
    "display_name",
    "role",
    "programs",
    "current_training_states",
    "review_lane",
    "research_identity_status",
    "decision_status",
    "queue_status",
    "review_priority",
    "decision_complexity",
    "dossier_status",
    "identity_risk_level",
    "research_candidate_count",
    "research_review_ready_count",
    "scholarly_source_count",
    "non_name_anchor_count",
    "secondary_anchor_count",
    "conflicting_identifier_count",
    "best_confidence",
    "top_source_keys",
    "top_claim_types",
    "required_confirmation_fields",
    "allowed_decisions",
    "manual_decision_template_json",
    "top_claims_json",
    "source_family_counts_json",
    "identifier_summary_json",
    "missing_evidence_summary",
    "recommended_reviewer_action",
    "acceptance_boundary",
    "member_fingerprint",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    seen = set()
    output = []
    for raw in str(value).split(";"):
        item = raw.strip()
        if item and item not in seen:
            output.append(item)
            seen.add(item)
    return output


def domain_for(url: str | None) -> str:
    if not url:
        return ""
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def source_family_for(source_identifier: str | None, source_url: str | None, claim_type: str | None) -> str:
    source = (source_identifier or "").lower()
    domain = domain_for(source_url)
    claim = (claim_type or "").lower()
    if "pubmed" in source or "pubmed" in domain or "pubmed" in claim:
        return "pubmed_publication"
    if "openalex" in source or "openalex.org" in domain or "research_author" in claim:
        return "openalex_author_context"
    if "orcid" in source or "orcid.org" in domain or "orcid" in claim:
        return "orcid_identity"
    if "npi" in source or "npiregistry.cms.hhs.gov" in domain or "npi" in claim:
        return "npi_identity"
    if "penn" in domain or "upenn.edu" in domain or "pennmedicine.org" in domain:
        return "official_penn_context"
    if "doi.org" in domain or "doi:" in str(claim_type or "").lower():
        return "publication_identifier"
    return "other_public_source"


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["dossier_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["dossier_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def dossier_key(row: dict) -> str:
    return "research_identity_reviewer_decision_dossier_" + sha256_text(row["reviewer_decision_key"])[:20]


def top_claims(row: dict, limit: int = 14) -> list[dict]:
    evidence = parse_json(row.get("member_evidence_json"), {})
    corroboration = evidence.get("corroboration_evidence") if isinstance(evidence, dict) else {}
    claims = corroboration.get("top_claims") if isinstance(corroboration, dict) else []
    output = []
    if not isinstance(claims, list):
        return output
    for claim in claims[:limit]:
        if not isinstance(claim, dict):
            continue
        source_identifier = claim.get("source_identifier") or ""
        source_url = claim.get("source_url") or ""
        claim_type = claim.get("claim_type") or ""
        output.append(
            {
                "claim_type": claim_type,
                "claim_value": claim.get("claim_value") or "",
                "status": claim.get("status") or "",
                "confidence": as_float(claim.get("confidence")),
                "source_family": source_family_for(source_identifier, source_url, claim_type),
                "source_identifier": source_identifier,
                "source_domain": domain_for(source_url),
                "source_url": source_url,
                "match_features": claim.get("match_features") or [],
                "provider_name": claim.get("provider_name") or "",
                "primary_taxonomy": claim.get("primary_taxonomy") or "",
            }
        )
    return output


def source_family_counts(claims: list[dict]) -> dict[str, int]:
    counts = Counter(claim.get("source_family") or "" for claim in claims)
    return dict(sorted(counts.items()))


def identifier_summary(row: dict, claims: list[dict]) -> dict[str, int]:
    counts = Counter()
    for claim in claims:
        claim_type = (claim.get("claim_type") or "").lower()
        value = str(claim.get("claim_value") or "").lower()
        if "orcid" in claim_type or "orcid.org" in value:
            counts["orcid"] += 1
        if "pmid" in claim_type or claim_type.endswith("article_candidate"):
            counts["publication_identifier"] += 1
        if "doi:" in value or "doi.org" in value:
            counts["doi"] += 1
        if "npi" in claim_type:
            counts["npi"] += 1
        if "openalex" in value or "research_author" in claim_type:
            counts["openalex_author"] += 1
    counts["persistent_identifier_metric"] = as_int(row.get("persistent_identifier_count"))
    counts["publication_identifier_metric"] = as_int(row.get("publication_identifier_count"))
    counts["conflicting_identifier_metric"] = as_int(row.get("conflicting_identifier_count"))
    return dict(sorted(counts.items()))


def decision_complexity(row: dict) -> str:
    if as_int(row.get("conflicting_identifier_count")) > 0:
        return "conflict_high"
    if as_int(row.get("research_review_ready_count")) >= 10 or as_int(row.get("research_candidate_count")) >= 25:
        return "high_volume_review"
    if as_int(row.get("research_review_ready_count")) > 0:
        return "review_ready"
    if as_int(row.get("secondary_anchor_count")) > 0:
        return "secondary_anchor_collection"
    return "low_signal_collection"


def dossier_status(row: dict) -> str:
    status = row.get("decision_status") or ""
    if status == "accepted_research_identity_review_decision":
        return "accepted_review_decision_monitor_downstream_acceptance"
    if status.startswith("rejected"):
        return "reviewer_rejected_identity_candidate"
    if status.startswith("quarantined"):
        return "conflicting_identifier_quarantined"
    if status.startswith("stale"):
        return "stale_reviewer_decision_recheck_required"
    if as_int(row.get("conflicting_identifier_count")) > 0:
        return "pending_conflict_reconciliation"
    if as_int(row.get("research_review_ready_count")) > 0:
        return "pending_review_ready_identity_decision"
    if row.get("review_lane") == "research_relevance_decision":
        return "pending_research_relevance_decision"
    return "pending_evidence_collection_decision"


def identity_risk_level(row: dict) -> str:
    if as_int(row.get("conflicting_identifier_count")) > 0:
        return "identifier_conflict"
    if as_int(row.get("non_name_anchor_count")) == 0:
        return "name_only_or_low_anchor"
    if as_int(row.get("scholarly_source_count")) >= 2 and as_int(row.get("non_name_anchor_count")) >= 2:
        return "multi_source_with_non_name_anchors"
    return "partial_anchor"


def missing_evidence(row: dict, claims: list[dict]) -> str:
    missing = []
    families = Counter(claim.get("source_family") or "" for claim in claims)
    if as_int(row.get("conflicting_identifier_count")) > 0:
        missing.append("resolve_or_quarantine_conflicting_identifier")
    if as_int(row.get("non_name_anchor_count")) == 0:
        missing.append("non_name_identity_anchor")
    if not (families.get("orcid_identity") or families.get("npi_identity") or families.get("official_penn_context")):
        missing.append("secondary_identity_or_official_profile_anchor")
    if as_int(row.get("research_review_ready_count")) == 0 and row.get("review_lane") != "research_relevance_decision":
        missing.append("review_ready_publication_or_author_evidence")
    if row.get("decision_status") == "pending_reviewer_decision":
        missing.append("manual_reviewer_decision")
    if not missing:
        return "none"
    return "; ".join(missing)


def recommended_action(row: dict) -> str:
    if row.get("decision_status") == "stale_decision_evidence_mismatch":
        return "re_review_current_member_and_update_decision_fingerprint"
    if as_int(row.get("conflicting_identifier_count")) > 0:
        return "resolve_or_quarantine_conflicting_identifier_before_acceptance"
    if row.get("review_lane") == "multi_source_identity_review":
        return "confirm_same_person_research_identity_or_reject_collision"
    if row.get("review_lane") == "single_source_publication_review":
        return "confirm_publication_identity_or_request_more_anchors"
    if row.get("review_lane") == "secondary_anchor_review":
        return "confirm_secondary_anchor_before_accepting_research_identity"
    if row.get("review_lane") == "secondary_anchor_collection":
        return "collect_or_record_secondary_anchor_evidence"
    if row.get("review_lane") == "research_relevance_decision":
        return "record_research_relevance_decision"
    return "record_research_identity_reviewer_decision"


def manual_template(row: dict) -> dict:
    return {
        "reviewer_decision_key": row.get("reviewer_decision_key") or "",
        "review_batch_member_key": row.get("review_batch_member_key") or "",
        "member_fingerprint": row.get("member_fingerprint") or "",
        "reviewer_decision": "",
        "reviewer_name": "",
        "decided_at": "",
        "identity_confirmed": 0,
        "source_context_confirmed": 0,
        "non_name_anchors_confirmed": 0,
        "conflict_resolved": 0,
        "display_safety_confirmed": 0,
        "decision_notes": "",
    }


def load_rows(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT q.*,
               a.decision_status,
               a.reviewer_decision,
               a.recommended_next_action AS audit_recommended_next_action,
               m.current_training_states,
               m.persistent_identifier_count,
               m.publication_identifier_count,
               m.evidence_json AS member_evidence_json
        FROM research_identity_reviewer_decision_queue q
        JOIN research_identity_reviewer_decision_audit a
          ON a.reviewer_decision_key = q.reviewer_decision_key
        JOIN research_identity_review_batch_members m
          ON m.review_batch_member_key = q.review_batch_member_key
        ORDER BY q.conflicting_identifier_count DESC,
                 q.review_priority DESC,
                 q.research_review_ready_count DESC,
                 q.display_name,
                 q.reviewer_decision_key
        """,
    )


def build_rows(source_rows: list[dict], generated_at: str) -> list[dict]:
    existing = read_existing()
    output = []
    for source_row in source_rows:
        claims = top_claims(source_row)
        family_counts = source_family_counts(claims)
        identifiers = identifier_summary(source_row, claims)
        row = {
            "dossier_key": dossier_key(source_row),
            "reviewer_decision_key": source_row["reviewer_decision_key"],
            "review_batch_member_key": source_row["review_batch_member_key"],
            "review_batch_key": source_row["review_batch_key"],
            "corroboration_key": source_row["corroboration_key"],
            "person_key": source_row["person_key"],
            "display_name": source_row["display_name"],
            "role": source_row.get("role") or "",
            "programs": source_row.get("programs") or "",
            "current_training_states": source_row.get("current_training_states") or "",
            "review_lane": source_row["review_lane"],
            "research_identity_status": source_row["research_identity_status"],
            "decision_status": source_row.get("decision_status") or "",
            "queue_status": source_row.get("queue_status") or "",
            "review_priority": as_int(source_row.get("review_priority")),
            "decision_complexity": decision_complexity(source_row),
            "dossier_status": dossier_status(source_row),
            "identity_risk_level": identity_risk_level(source_row),
            "research_candidate_count": as_int(source_row.get("research_candidate_count")),
            "research_review_ready_count": as_int(source_row.get("research_review_ready_count")),
            "scholarly_source_count": as_int(source_row.get("scholarly_source_count")),
            "non_name_anchor_count": as_int(source_row.get("non_name_anchor_count")),
            "secondary_anchor_count": as_int(source_row.get("secondary_anchor_count")),
            "conflicting_identifier_count": as_int(source_row.get("conflicting_identifier_count")),
            "best_confidence": round(as_float(source_row.get("best_confidence")), 3),
            "top_source_keys": source_row.get("top_source_keys") or "",
            "top_claim_types": source_row.get("top_claim_types") or "",
            "required_confirmation_fields": source_row.get("required_confirmation_fields") or "",
            "allowed_decisions": source_row.get("allowed_decisions") or "",
            "manual_decision_template_json": dumps(manual_template(source_row)),
            "top_claims_json": dumps(claims),
            "source_family_counts_json": dumps(family_counts),
            "identifier_summary_json": dumps(identifiers),
            "missing_evidence_summary": missing_evidence(source_row, claims),
            "recommended_reviewer_action": recommended_action(source_row),
            "acceptance_boundary": source_row.get("acceptance_boundary") or "",
            "member_fingerprint": source_row.get("member_fingerprint") or "",
            "evidence_json": dumps(
                {
                    "derived_from": "research_identity_reviewer_decision_queue",
                    "reviewer_decision_key": source_row["reviewer_decision_key"],
                    "review_batch_member_key": source_row["review_batch_member_key"],
                    "manual_decision_template": manual_template(source_row),
                    "top_claims": claims,
                    "source_family_counts": family_counts,
                    "identifier_summary": identifiers,
                    "policy": {
                        "non_mutating": True,
                        "accepted_review_decision_requires_current_member_fingerprint": True,
                        "accepted_person_fact_requires_downstream_acceptance_ledgers": True,
                    },
                }
            ),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        output.append({field: row[field] for field in FIELDS})
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM research_identity_reviewer_decision_dossiers")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO research_identity_reviewer_decision_dossiers ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_status = Counter(row["dossier_status"] for row in rows)
    by_lane = Counter(row["review_lane"] for row in rows)
    by_complexity = Counter(row["decision_complexity"] for row in rows)
    by_risk = Counter(row["identity_risk_level"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "dossier_rows": len(rows),
        "pending_dossier_rows": sum(1 for row in rows if str(row["dossier_status"]).startswith("pending")),
        "conflict_dossier_rows": sum(1 for row in rows if as_int(row["conflicting_identifier_count"]) > 0),
        "review_ready_record_count": sum(as_int(row["research_review_ready_count"]) for row in rows),
        "by_dossier_status": dict(sorted(by_status.items())),
        "by_review_lane": dict(sorted(by_lane.items())),
        "by_decision_complexity": dict(sorted(by_complexity.items())),
        "by_identity_risk_level": dict(sorted(by_risk.items())),
        "top_dossiers": [
            {
                "dossier_key": row["dossier_key"],
                "display_name": row["display_name"],
                "role": row["role"],
                "review_lane": row["review_lane"],
                "decision_complexity": row["decision_complexity"],
                "conflicting_identifier_count": row["conflicting_identifier_count"],
                "research_review_ready_count": row["research_review_ready_count"],
                "recommended_reviewer_action": row["recommended_reviewer_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Research identity reviewer decision dossiers are non-mutating templates over the decision queue; accepted person facts still require downstream acceptance ledgers.",
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
    rows = build_rows(load_rows(conn), generated_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"research_identity_reviewer_decision_dossiers": len(rows)}))


if __name__ == "__main__":
    main()
