#!/usr/bin/env python3
"""Materialize reviewer decision scaffolding for research identity batch members."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

QUEUE_CSV = ARTIFACTS / "research_identity_reviewer_decision_queue.csv"
QUEUE_JSON = ARTIFACTS / "research_identity_reviewer_decision_queue.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "research_identity_reviewer_decisions.csv"
AUDIT_CSV = ARTIFACTS / "research_identity_reviewer_decision_audit.csv"
AUDIT_JSON = ARTIFACTS / "research_identity_reviewer_decision_audit.json"
SUMMARY_JSON = ARTIFACTS / "research_identity_reviewer_decision_summary.json"

ALLOWED_DECISIONS = [
    "accept_same_person_research_identity",
    "accept_secondary_anchor_only",
    "accept_publication_identity",
    "reject_identity_mismatch",
    "reject_identifier_collision",
    "reject_insufficient_anchors",
    "needs_more_evidence",
    "quarantine_conflicting_identifier",
]
CONFIRMATION_FIELDS = [
    "identity_confirmed",
    "source_context_confirmed",
    "non_name_anchors_confirmed",
    "display_safety_confirmed",
]
CONFLICT_CONFIRMATION_FIELD = "conflict_resolved"

QUEUE_FIELDS = [
    "reviewer_decision_key",
    "review_batch_member_key",
    "review_batch_key",
    "corroboration_key",
    "person_key",
    "display_name",
    "role",
    "programs",
    "research_identity_status",
    "recommended_review_route",
    "review_lane",
    "queue_status",
    "allowed_decisions",
    "member_fingerprint",
    "review_priority",
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
    "required_reviewer_action",
    "acceptance_boundary",
    "evidence_json",
    "generated_at",
]

MANUAL_FIELDS = [
    "reviewer_decision_key",
    "review_batch_member_key",
    "member_fingerprint",
    "reviewer_decision",
    "reviewer_name",
    "decided_at",
    "identity_confirmed",
    "source_context_confirmed",
    "non_name_anchors_confirmed",
    "conflict_resolved",
    "display_safety_confirmed",
    "decision_notes",
]

AUDIT_FIELDS = [
    "reviewer_decision_key",
    "review_batch_member_key",
    "review_batch_key",
    "corroboration_key",
    "person_key",
    "display_name",
    "role",
    "research_identity_status",
    "recommended_review_route",
    "review_lane",
    "reviewer_decision",
    "decision_status",
    "accepted_research_identity_review",
    "decision_blocker",
    "member_fingerprint",
    "decision_member_fingerprint",
    "identity_confirmed",
    "source_context_confirmed",
    "non_name_anchors_confirmed",
    "conflict_resolved",
    "display_safety_confirmed",
    "reviewer_name",
    "decided_at",
    "review_priority",
    "research_candidate_count",
    "research_review_ready_count",
    "conflicting_identifier_count",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
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


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def reviewer_decision_key(row: dict) -> str:
    return "research_identity_reviewer_decision_" + sha256_text(row["review_batch_member_key"])[:20]


def secondary_anchor_count(row: dict) -> int:
    return (
        as_int(row.get("npi_candidate_count"))
        + as_int(row.get("profile_candidate_count"))
        + as_int(row.get("contact_candidate_count"))
        + as_int(row.get("persistent_identifier_count"))
    )


def queue_status(row: dict) -> str:
    lane = row.get("review_lane") or ""
    if lane == "conflict_reconciliation":
        return "ready_for_conflict_reviewer_decision"
    if lane in {"multi_source_identity_review", "secondary_anchor_review", "single_source_publication_review"}:
        return "ready_for_research_identity_reviewer_decision"
    if lane == "secondary_anchor_collection":
        return "ready_for_secondary_anchor_collection_decision"
    if lane == "research_relevance_decision":
        return "ready_for_research_relevance_decision"
    return "ready_for_research_identity_review"


def required_confirmation_fields(row: dict) -> list[str]:
    fields = list(CONFIRMATION_FIELDS)
    if as_int(row.get("conflicting_identifier_count")) > 0:
        fields.insert(3, CONFLICT_CONFIRMATION_FIELD)
    return fields


def required_reviewer_action(row: dict) -> str:
    lane = row.get("review_lane") or ""
    if lane == "conflict_reconciliation":
        return "Resolve conflicting identifiers or quarantine the candidate before any research identity acceptance."
    if lane == "multi_source_identity_review":
        return "Confirm same-person scholarly identity across source families, non-name anchors, and source context."
    if lane == "secondary_anchor_review":
        return "Confirm whether NPI, ORCID, profile, contact, or persistent identifiers are valid secondary anchors."
    if lane == "single_source_publication_review":
        return "Confirm publication identity with non-name anchors or request additional evidence."
    if lane == "secondary_anchor_collection":
        return "Decide whether collected evidence is sufficient for review or still needs another non-name anchor."
    if lane == "research_relevance_decision":
        return "Decide whether this trainee should remain in the research identity search lane."
    return row.get("recommended_reviewer_action") or "Record a research identity reviewer decision with the current member fingerprint."


def compact_member(row: dict) -> dict:
    return {
        key: row.get(key, "")
        for key in [
            "review_batch_member_key",
            "review_batch_key",
            "corroboration_key",
            "person_key",
            "display_name",
            "role",
            "programs",
            "research_identity_status",
            "recommended_review_route",
            "review_lane",
            "review_priority",
            "research_candidate_count",
            "research_review_ready_count",
            "scholarly_source_count",
            "non_name_anchor_count",
            "conflicting_identifier_count",
            "best_confidence",
            "top_source_keys",
            "top_claim_types",
            "required_next_evidence",
            "recommended_reviewer_action",
        ]
    }


def build_queue(members: list[dict], generated_at: str) -> list[dict]:
    rows = []
    for member in members:
        confirmation_fields = required_confirmation_fields(member)
        evidence = {
            "research_identity_review_batch_member": compact_member(member),
            "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
            "decision_policy": {
                "allowed_decisions": ALLOWED_DECISIONS,
                "accepted_research_identity_review_requires": [
                    "member_fingerprint matches the current queue fingerprint",
                    *[f"{field}=1" for field in confirmation_fields],
                    "reviewer_decision is one of the accept_* decisions",
                    "accepted review decisions still do not mutate accepted person facts directly",
                ],
            },
        }
        row = {
            "reviewer_decision_key": reviewer_decision_key(member),
            "review_batch_member_key": member["review_batch_member_key"],
            "review_batch_key": member["review_batch_key"],
            "corroboration_key": member["corroboration_key"],
            "person_key": member["person_key"],
            "display_name": member["display_name"],
            "role": member.get("role") or "",
            "programs": member.get("programs") or "",
            "research_identity_status": member["research_identity_status"],
            "recommended_review_route": member["recommended_review_route"],
            "review_lane": member.get("review_lane") or "",
            "queue_status": queue_status(member),
            "allowed_decisions": "; ".join(ALLOWED_DECISIONS),
            "member_fingerprint": member["member_fingerprint"],
            "review_priority": as_int(member.get("review_priority")),
            "research_candidate_count": as_int(member.get("research_candidate_count")),
            "research_review_ready_count": as_int(member.get("research_review_ready_count")),
            "scholarly_source_count": as_int(member.get("scholarly_source_count")),
            "non_name_anchor_count": as_int(member.get("non_name_anchor_count")),
            "secondary_anchor_count": secondary_anchor_count(member),
            "conflicting_identifier_count": as_int(member.get("conflicting_identifier_count")),
            "best_confidence": round(as_float(member.get("best_confidence")), 3),
            "top_source_keys": member.get("top_source_keys") or "",
            "top_claim_types": member.get("top_claim_types") or "",
            "required_confirmation_fields": "; ".join(confirmation_fields),
            "required_reviewer_action": required_reviewer_action(member),
            "acceptance_boundary": member.get("acceptance_boundary") or "",
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        rows.append({field: row[field] for field in QUEUE_FIELDS})
    return sorted(
        rows,
        key=lambda row: (
            -as_int(row["conflicting_identifier_count"]),
            -as_int(row["review_priority"]),
            -as_int(row["research_review_ready_count"]),
            row["display_name"],
            row["review_batch_member_key"],
        ),
    )


def ensure_manual_decisions_file() -> None:
    if MANUAL_DECISIONS_CSV.exists():
        return
    write_csv(MANUAL_DECISIONS_CSV, [], MANUAL_FIELDS)


def manual_decisions_by_key() -> dict[str, dict]:
    ensure_manual_decisions_file()
    rows = {}
    for row in read_csv(MANUAL_DECISIONS_CSV):
        key = row.get("reviewer_decision_key") or ""
        if key:
            rows[key] = row
    return rows


def compact_manual_decision(decision: dict | None) -> dict:
    if not decision:
        return {}
    return {field: decision.get(field, "") for field in MANUAL_FIELDS}


def classify_decision(queue_row: dict, decision: dict | None) -> tuple[str, int, str, str]:
    if not decision:
        return (
            "pending_reviewer_decision",
            0,
            "manual_research_identity_decision_missing",
            "record_research_identity_accept_reject_or_needs_more_evidence_decision",
        )
    reviewer_decision = decision.get("reviewer_decision") or ""
    if reviewer_decision not in ALLOWED_DECISIONS:
        return ("invalid_reviewer_decision", 0, "reviewer_decision_not_in_allowed_decisions", "correct_manual_decision_value")
    if decision.get("member_fingerprint") != queue_row.get("member_fingerprint"):
        return (
            "stale_decision_evidence_mismatch",
            0,
            "manual_decision_member_fingerprint_does_not_match_current_member",
            "re_review_current_research_identity_member_and_update_fingerprint",
        )
    if reviewer_decision.startswith("accept_"):
        missing = [field for field in required_confirmation_fields(queue_row) if as_int(decision.get(field)) != 1]
        if missing:
            return (
                "invalid_acceptance_missing_confirmations",
                0,
                "missing_required_confirmations:" + ";".join(missing),
                "confirm_all_required_fields_or_change_decision",
            )
        return (
            "accepted_research_identity_review_decision",
            1,
            "none",
            "route_accepted_research_identity_review_to_source_specific_acceptance_ledgers",
        )
    if reviewer_decision.startswith("reject_"):
        return ("rejected_by_reviewer", 0, reviewer_decision, "retain_rejection_for_audit_and_suppress_matching_candidate")
    if reviewer_decision == "quarantine_conflicting_identifier":
        return (
            "quarantined_conflicting_identifier",
            0,
            "conflicting_identifier_quarantined_by_reviewer",
            "retain_quarantine_until_source_specific_evidence_changes",
        )
    return (
        "deferred_needs_more_evidence",
        0,
        "reviewer_requested_more_evidence",
        "collect_additional_source_context_non_name_anchor_or_identifier_evidence",
    )


def build_audit(queue: list[dict], audited_at: str) -> list[dict]:
    decisions = manual_decisions_by_key()
    rows = []
    for item in queue:
        decision = decisions.get(item["reviewer_decision_key"])
        status, accepted, blocker, action = classify_decision(item, decision)
        evidence = {
            "queue_row": {field: item.get(field, "") for field in QUEUE_FIELDS if field != "evidence_json"},
            "manual_decision": compact_manual_decision(decision),
            "decision_policy": {
                "non_mutating": True,
                "accepted_review_decision_requires": [
                    "matching member_fingerprint",
                    *[f"{field}=1" for field in required_confirmation_fields(item)],
                    "reviewer_decision starts with accept_",
                ],
                "accepted_person_fact_requires_downstream_ledgers": [
                    "evidence_reconciliation_decisions",
                    "person_evidence_reviewer_decisions",
                    "enrichment_acceptance_audit",
                    "accepted_enrichment_claims",
                ],
            },
        }
        row = {
            "reviewer_decision_key": item["reviewer_decision_key"],
            "review_batch_member_key": item["review_batch_member_key"],
            "review_batch_key": item["review_batch_key"],
            "corroboration_key": item["corroboration_key"],
            "person_key": item["person_key"],
            "display_name": item["display_name"],
            "role": item["role"],
            "research_identity_status": item["research_identity_status"],
            "recommended_review_route": item["recommended_review_route"],
            "review_lane": item["review_lane"],
            "reviewer_decision": (decision or {}).get("reviewer_decision", "pending") or "pending",
            "decision_status": status,
            "accepted_research_identity_review": accepted,
            "decision_blocker": blocker,
            "member_fingerprint": item["member_fingerprint"],
            "decision_member_fingerprint": (decision or {}).get("member_fingerprint", ""),
            "identity_confirmed": as_int((decision or {}).get("identity_confirmed")),
            "source_context_confirmed": as_int((decision or {}).get("source_context_confirmed")),
            "non_name_anchors_confirmed": as_int((decision or {}).get("non_name_anchors_confirmed")),
            "conflict_resolved": as_int((decision or {}).get("conflict_resolved")),
            "display_safety_confirmed": as_int((decision or {}).get("display_safety_confirmed")),
            "reviewer_name": (decision or {}).get("reviewer_name", ""),
            "decided_at": (decision or {}).get("decided_at", ""),
            "review_priority": item["review_priority"],
            "research_candidate_count": item["research_candidate_count"],
            "research_review_ready_count": item["research_review_ready_count"],
            "conflicting_identifier_count": item["conflicting_identifier_count"],
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": audited_at,
        }
        rows.append({field: row[field] for field in AUDIT_FIELDS})
    return rows


def write_db_table(conn: sqlite3.Connection, table: str, rows: list[dict], fields: list[str]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    field_sql = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    conn.executemany(f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(queue: list[dict], audit: list[dict], generated_at: str) -> None:
    by_status = Counter(row["decision_status"] for row in audit)
    by_lane = Counter(row["review_lane"] for row in queue)
    by_identity_status = Counter(row["research_identity_status"] for row in queue)
    by_queue_status = Counter(row["queue_status"] for row in queue)
    by_action = Counter(row["recommended_next_action"] for row in audit)
    payload = {
        "generated_at": generated_at,
        "queue_rows": len(queue),
        "manual_decision_rows": len(read_csv(MANUAL_DECISIONS_CSV)),
        "audit_rows": len(audit),
        "accepted_research_identity_review_rows": sum(as_int(row["accepted_research_identity_review"]) for row in audit),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "conflict_queue_rows": sum(1 for row in queue if as_int(row["conflicting_identifier_count"]) > 0),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_queue_status": dict(sorted(by_queue_status.items())),
        "by_review_lane": dict(sorted(by_lane.items())),
        "by_research_identity_status": dict(sorted(by_identity_status.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "acceptance_policy": (
            "Research identity decisions do not mutate accepted person facts. Acceptance requires an explicit reviewer "
            "decision, a matching member fingerprint, required confirmations, and downstream source-specific acceptance ledgers."
        ),
        "manual_decision_csv": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
        "queue_csv": str(QUEUE_CSV.relative_to(ROOT)),
        "audit_csv": str(AUDIT_CSV.relative_to(ROOT)),
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    members = sqlite_rows(
        conn,
        """
        SELECT m.*, b.review_lane
        FROM research_identity_review_batch_members m
        JOIN research_identity_review_batches b
          ON b.review_batch_key = m.review_batch_key
        ORDER BY m.review_priority DESC, m.display_name, m.review_batch_member_key
        """,
    )
    queue = build_queue(members, generated_at)
    audit = build_audit(queue, generated_at)

    write_csv(QUEUE_CSV, queue, QUEUE_FIELDS)
    write_json(QUEUE_JSON, queue)
    ensure_manual_decisions_file()
    write_csv(AUDIT_CSV, audit, AUDIT_FIELDS)
    write_json(AUDIT_JSON, audit)
    with conn:
        write_db_table(conn, "research_identity_reviewer_decisions", read_csv(MANUAL_DECISIONS_CSV), MANUAL_FIELDS)
        write_db_table(conn, "research_identity_reviewer_decision_queue", queue, QUEUE_FIELDS)
        write_db_table(conn, "research_identity_reviewer_decision_audit", audit, AUDIT_FIELDS)
    conn.close()
    write_summary(queue, audit, generated_at)
    print(
        dumps(
            {
                "queue_rows": len(queue),
                "audit_rows": len(audit),
                "pending_reviewer_decision_rows": len(audit),
            }
        )
    )


if __name__ == "__main__":
    main()
