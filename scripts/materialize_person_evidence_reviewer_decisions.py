#!/usr/bin/env python3
"""Materialize reviewer decision scaffolding for person evidence packets."""

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

PACKETS_CSV = ARTIFACTS / "person_evidence_review_packets.csv"
QUEUE_CSV = ARTIFACTS / "person_evidence_reviewer_decision_queue.csv"
QUEUE_JSON = ARTIFACTS / "person_evidence_reviewer_decision_queue.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "person_evidence_reviewer_decisions.csv"
AUDIT_CSV = ARTIFACTS / "person_evidence_reviewer_decision_audit.csv"
AUDIT_JSON = ARTIFACTS / "person_evidence_reviewer_decision_audit.json"
SUMMARY_JSON = ARTIFACTS / "person_evidence_reviewer_decision_summary.json"

ALLOWED_DECISIONS = [
    "accept_publication_enrichment",
    "accept_profile_background_fact",
    "accept_secondary_identity_anchor",
    "reject_identity_mismatch",
    "reject_insufficient_anchors",
    "reject_stale_source",
    "needs_more_evidence",
]
CONFIRMATION_FIELDS = [
    "identity_confirmed",
    "source_context_confirmed",
    "non_name_anchors_confirmed",
    "display_safety_confirmed",
]

QUEUE_FIELDS = [
    "reviewer_decision_key",
    "packet_key",
    "person_or_name_key",
    "person_key",
    "display_name",
    "role",
    "packet_status",
    "review_kind",
    "queue_status",
    "allowed_decisions",
    "packet_fingerprint",
    "review_priority",
    "review_ready_record_count",
    "evidence_record_count",
    "best_decision",
    "best_source_url",
    "top_source_urls",
    "top_claim_types",
    "top_match_features",
    "required_reviewer_action",
    "acceptance_blocker",
    "display_safety_status",
    "evidence_json",
    "generated_at",
]

MANUAL_FIELDS = [
    "reviewer_decision_key",
    "packet_key",
    "packet_fingerprint",
    "reviewer_decision",
    "reviewer_name",
    "decided_at",
    "identity_confirmed",
    "source_context_confirmed",
    "non_name_anchors_confirmed",
    "display_safety_confirmed",
    "decision_notes",
]

AUDIT_FIELDS = [
    "reviewer_decision_key",
    "packet_key",
    "person_or_name_key",
    "person_key",
    "display_name",
    "role",
    "packet_status",
    "review_kind",
    "reviewer_decision",
    "decision_status",
    "accepted_candidate_fact",
    "decision_blocker",
    "packet_fingerprint",
    "decision_packet_fingerprint",
    "identity_confirmed",
    "source_context_confirmed",
    "non_name_anchors_confirmed",
    "display_safety_confirmed",
    "reviewer_name",
    "decided_at",
    "review_priority",
    "review_ready_record_count",
    "evidence_record_count",
    "best_decision",
    "best_source_url",
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


def packet_fingerprint(packet: dict) -> str:
    stable = {
        "packet_key": packet.get("packet_key", ""),
        "person_or_name_key": packet.get("person_or_name_key", ""),
        "person_key": packet.get("person_key", ""),
        "display_name": packet.get("display_name", ""),
        "packet_status": packet.get("packet_status", ""),
        "review_kind": packet.get("review_kind", ""),
        "review_ready_record_count": packet.get("review_ready_record_count", ""),
        "evidence_record_count": packet.get("evidence_record_count", ""),
        "best_decision": packet.get("best_decision", ""),
        "best_source_url": packet.get("best_source_url", ""),
        "top_claim_types": packet.get("top_claim_types", ""),
        "top_match_features": packet.get("top_match_features", ""),
    }
    return sha256_text(dumps(stable))


def reviewer_decision_key(packet: dict) -> str:
    return "person_evidence_reviewer_decision_" + sha256_text(packet["packet_key"])[:20]


def required_action(packet: dict) -> str:
    if packet.get("review_kind") == "publication_identity_review":
        return "Confirm same-person author identity, non-name anchors, source context, and display safety before accepting publication enrichment."
    if packet.get("review_kind") == "mixed_identity_anchor_review":
        return "Confirm which candidate facts are accepted, rejected, or still need independent anchors before mutating enrichment ledgers."
    return "Record accept, reject, or needs-more-evidence decision with source-context and display-safety confirmation."


def queue_status(packet: dict) -> str:
    if packet.get("recommended_next_action") == "manual_review_for_candidate_acceptance":
        return "ready_for_reviewer_decision"
    return "not_ready_for_reviewer_decision"


def display_safety_status(packet: dict) -> str:
    if packet.get("packet_status", "").startswith("review_ready"):
        return "review_ready_not_accepted_enrichment_fact"
    return "not_ready_for_default_display"


def compact_packet(packet: dict) -> dict:
    return {
        key: packet.get(key, "")
        for key in [
            "packet_key",
            "person_or_name_key",
            "person_key",
            "display_name",
            "role",
            "packet_status",
            "review_kind",
            "recommended_next_action",
            "acceptance_blocker",
            "review_priority",
            "review_ready_record_count",
            "evidence_record_count",
            "best_decision",
            "best_source_url",
            "top_source_urls",
            "top_claim_types",
            "top_match_features",
        ]
    }


def build_queue(packets: list[dict], generated_at: str) -> list[dict]:
    rows = []
    for packet in packets:
        if queue_status(packet) != "ready_for_reviewer_decision":
            continue
        fingerprint = packet_fingerprint(packet)
        evidence = {
            "person_evidence_review_packet": compact_packet(packet),
            "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
            "decision_policy": {
                "allowed_decisions": ALLOWED_DECISIONS,
                "accepted_candidate_fact_requires": [
                    "packet_fingerprint matches the current queue fingerprint",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                    "reviewer_decision is one of the accept_* decisions",
                ],
            },
        }
        row = {
            "reviewer_decision_key": reviewer_decision_key(packet),
            "packet_key": packet["packet_key"],
            "person_or_name_key": packet["person_or_name_key"],
            "person_key": packet.get("person_key") or "",
            "display_name": packet["display_name"],
            "role": packet.get("role") or "",
            "packet_status": packet["packet_status"],
            "review_kind": packet["review_kind"],
            "queue_status": queue_status(packet),
            "allowed_decisions": "; ".join(ALLOWED_DECISIONS),
            "packet_fingerprint": fingerprint,
            "review_priority": as_int(packet.get("review_priority")),
            "review_ready_record_count": as_int(packet.get("review_ready_record_count")),
            "evidence_record_count": as_int(packet.get("evidence_record_count")),
            "best_decision": packet.get("best_decision") or "",
            "best_source_url": packet.get("best_source_url") or "",
            "top_source_urls": packet.get("top_source_urls") or "",
            "top_claim_types": packet.get("top_claim_types") or "",
            "top_match_features": packet.get("top_match_features") or "",
            "required_reviewer_action": required_action(packet),
            "acceptance_blocker": packet.get("acceptance_blocker") or "",
            "display_safety_status": display_safety_status(packet),
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        rows.append({field: row[field] for field in QUEUE_FIELDS})
    return sorted(rows, key=lambda row: (-as_int(row["review_priority"]), row["display_name"], row["packet_key"]))


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
            "manual_reviewer_decision_missing",
            "record_accept_reject_or_needs_more_evidence_decision",
        )
    reviewer_decision = decision.get("reviewer_decision") or ""
    if reviewer_decision not in ALLOWED_DECISIONS:
        return ("invalid_reviewer_decision", 0, "reviewer_decision_not_in_allowed_decisions", "correct_manual_decision_value")
    if decision.get("packet_fingerprint") != queue_row.get("packet_fingerprint"):
        return (
            "stale_decision_evidence_mismatch",
            0,
            "manual_decision_packet_fingerprint_does_not_match_current_packet",
            "re_review_current_packet_and_update_fingerprint",
        )
    if reviewer_decision.startswith("accept_"):
        missing = [field for field in CONFIRMATION_FIELDS if as_int(decision.get(field)) != 1]
        if missing:
            return (
                "invalid_acceptance_missing_confirmations",
                0,
                "missing_required_confirmations:" + ";".join(missing),
                "confirm_all_required_fields_or_change_decision",
            )
        return ("accepted_reviewer_decision", 1, "none", "materialize_or_route_accepted_candidate_fact")
    if reviewer_decision.startswith("reject_"):
        return ("rejected_by_reviewer", 0, reviewer_decision, "retain_rejection_for_audit")
    return (
        "deferred_needs_more_evidence",
        0,
        "reviewer_requested_more_evidence",
        "collect_additional_identity_source_or_display_safety_evidence",
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
                "accepted_candidate_fact_requires": [
                    "matching packet_fingerprint",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                    "reviewer_decision starts with accept_",
                ],
            },
        }
        row = {
            "reviewer_decision_key": item["reviewer_decision_key"],
            "packet_key": item["packet_key"],
            "person_or_name_key": item["person_or_name_key"],
            "person_key": item["person_key"],
            "display_name": item["display_name"],
            "role": item["role"],
            "packet_status": item["packet_status"],
            "review_kind": item["review_kind"],
            "reviewer_decision": (decision or {}).get("reviewer_decision", "pending") or "pending",
            "decision_status": status,
            "accepted_candidate_fact": accepted,
            "decision_blocker": blocker,
            "packet_fingerprint": item["packet_fingerprint"],
            "decision_packet_fingerprint": (decision or {}).get("packet_fingerprint", ""),
            "identity_confirmed": as_int((decision or {}).get("identity_confirmed")),
            "source_context_confirmed": as_int((decision or {}).get("source_context_confirmed")),
            "non_name_anchors_confirmed": as_int((decision or {}).get("non_name_anchors_confirmed")),
            "display_safety_confirmed": as_int((decision or {}).get("display_safety_confirmed")),
            "reviewer_name": (decision or {}).get("reviewer_name", ""),
            "decided_at": (decision or {}).get("decided_at", ""),
            "review_priority": item["review_priority"],
            "review_ready_record_count": item["review_ready_record_count"],
            "evidence_record_count": item["evidence_record_count"],
            "best_decision": item["best_decision"],
            "best_source_url": item["best_source_url"],
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
    by_kind = Counter(row["review_kind"] for row in queue)
    by_packet_status = Counter(row["packet_status"] for row in queue)
    by_action = Counter(row["recommended_next_action"] for row in audit)
    payload = {
        "generated_at": generated_at,
        "queue_rows": len(queue),
        "manual_decision_rows": len(read_csv(MANUAL_DECISIONS_CSV)),
        "audit_rows": len(audit),
        "accepted_candidate_fact_rows": sum(as_int(row["accepted_candidate_fact"]) for row in audit),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_review_kind": dict(sorted(by_kind.items())),
        "by_packet_status": dict(sorted(by_packet_status.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "acceptance_policy": (
            "Person evidence packets do not mutate accepted enrichment facts without an explicit reviewer decision, "
            "a matching packet fingerprint, and all required confirmation fields set to 1."
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
    packets = sqlite_rows(
        conn,
        """
        SELECT *
        FROM person_evidence_review_packets
        WHERE recommended_next_action = 'manual_review_for_candidate_acceptance'
        ORDER BY review_priority DESC, display_name, packet_key
        """,
    )
    queue = build_queue(packets, generated_at)
    audit = build_audit(queue, generated_at)

    write_csv(QUEUE_CSV, queue, QUEUE_FIELDS)
    write_json(QUEUE_JSON, queue)
    ensure_manual_decisions_file()
    write_csv(AUDIT_CSV, audit, AUDIT_FIELDS)
    write_json(AUDIT_JSON, audit)
    with conn:
        write_db_table(conn, "person_evidence_reviewer_decisions", read_csv(MANUAL_DECISIONS_CSV), MANUAL_FIELDS)
        write_db_table(conn, "person_evidence_reviewer_decision_queue", queue, QUEUE_FIELDS)
        write_db_table(conn, "person_evidence_reviewer_decision_audit", audit, AUDIT_FIELDS)
    conn.close()
    write_summary(queue, audit, generated_at)
    print(dumps({"queue_rows": len(queue), "audit_rows": len(audit), "pending_reviewer_decision_rows": len(audit)}))


if __name__ == "__main__":
    main()
