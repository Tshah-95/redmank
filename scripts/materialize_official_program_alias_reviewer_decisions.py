#!/usr/bin/env python3
"""Materialize reviewer decisions for official-program alias packets."""

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

QUEUE_CSV = ARTIFACTS / "official_program_alias_reviewer_decision_queue.csv"
QUEUE_JSON = ARTIFACTS / "official_program_alias_reviewer_decision_queue.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "official_program_alias_reviewer_decisions.csv"
AUDIT_CSV = ARTIFACTS / "official_program_alias_reviewer_decision_audit.csv"
AUDIT_JSON = ARTIFACTS / "official_program_alias_reviewer_decision_audit.json"
ACCEPTED_CSV = ARTIFACTS / "accepted_official_program_alias_mappings.csv"
ACCEPTED_JSON = ARTIFACTS / "accepted_official_program_alias_mappings.json"
SUMMARY_JSON = ARTIFACTS / "official_program_alias_reviewer_decision_summary.json"

ALLOWED_DECISIONS = [
    "accept_alias_mapping",
    "reject_not_same_program",
    "reject_wrong_role_or_track",
    "reject_not_current_roster",
    "needs_more_evidence",
]
CONFIRMATION_FIELDS = [
    "official_program_confirmed",
    "loaded_source_scope_confirmed",
    "role_scope_confirmed",
    "current_roster_confirmed",
]
DISPLAY_SAFETY_STATUS = "accepted_alias_mapping_public_source_backed"
REQUIRED_REVIEWER_ACTION = (
    "Confirm the official denominator row, loaded source scope, trainee role/track, and current roster "
    "status before accepting an alias mapping."
)

QUEUE_FIELDS = [
    "reviewer_decision_key",
    "packet_key",
    "queue_key",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "loaded_program_name",
    "loaded_role",
    "loaded_person_count",
    "loaded_source_url",
    "alias_decision_status",
    "alias_confidence",
    "queue_status",
    "allowed_decisions",
    "packet_fingerprint",
    "required_confirmation_fields",
    "required_reviewer_action",
    "recommended_next_action",
    "review_question",
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
    "official_program_confirmed",
    "loaded_source_scope_confirmed",
    "role_scope_confirmed",
    "current_roster_confirmed",
    "decision_notes",
]

AUDIT_FIELDS = [
    "reviewer_decision_key",
    "packet_key",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "loaded_program_name",
    "loaded_role",
    "loaded_person_count",
    "reviewer_decision",
    "decision_status",
    "accepted_alias_mapping",
    "decision_blocker",
    "packet_fingerprint",
    "decision_packet_fingerprint",
    "official_program_confirmed",
    "loaded_source_scope_confirmed",
    "role_scope_confirmed",
    "current_roster_confirmed",
    "reviewer_name",
    "decided_at",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]

ACCEPTED_FIELDS = [
    "accepted_alias_key",
    "reviewer_decision_key",
    "packet_key",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "loaded_program_name",
    "loaded_role",
    "loaded_person_count",
    "loaded_source_url",
    "alias_decision_status",
    "packet_fingerprint",
    "accepted_by",
    "accepted_at",
    "coverage_mutation_allowed",
    "display_safety_status",
    "evidence_json",
    "materialized_at",
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


def ensure_manual_decisions_file() -> None:
    if not MANUAL_DECISIONS_CSV.exists():
        write_csv(MANUAL_DECISIONS_CSV, [], MANUAL_FIELDS)


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def packet_fingerprint(row: dict) -> str:
    stable = {
        "packet_key": row.get("packet_key"),
        "official_program_key": row.get("official_program_key"),
        "official_program_name": row.get("official_program_name"),
        "official_program_type": row.get("official_program_type"),
        "official_department": row.get("official_department"),
        "loaded_program_name": row.get("loaded_program_name"),
        "loaded_role": row.get("loaded_role"),
        "loaded_person_count": row.get("loaded_person_count"),
        "loaded_source_url": row.get("loaded_source_url"),
        "alias_decision_status": row.get("alias_decision_status"),
        "alias_confidence": row.get("alias_confidence"),
    }
    return sha256_text(dumps(stable))


def read_packets(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM official_program_alias_review_packets
        ORDER BY reviewer_ready DESC, loaded_person_count DESC, official_program_name, packet_key
        """,
    )


def decision_key(packet: dict) -> str:
    return f"official_program_alias_reviewer_decision_{sha256_text(packet['packet_key'])[:20]}"


def build_queue(packets: list[dict], generated_at: str) -> list[dict]:
    queue = []
    for packet in packets:
        fingerprint = packet_fingerprint(packet)
        queue_status = "ready_for_reviewer_decision" if as_int(packet.get("reviewer_ready")) == 1 else "not_ready_for_reviewer_decision"
        evidence = {
            "alias_review_packet": {
                "packet_key": packet.get("packet_key"),
                "queue_key": packet.get("queue_key"),
                "official_program_key": packet.get("official_program_key"),
                "official_program_name": packet.get("official_program_name"),
                "official_program_type": packet.get("official_program_type"),
                "loaded_program_name": packet.get("loaded_program_name"),
                "loaded_role": packet.get("loaded_role"),
                "loaded_person_count": packet.get("loaded_person_count"),
                "alias_decision_status": packet.get("alias_decision_status"),
                "alias_confidence": packet.get("alias_confidence"),
                "reviewer_ready": packet.get("reviewer_ready"),
                "recommended_next_action": packet.get("recommended_next_action"),
                "review_question": packet.get("review_question"),
                "rationale": packet.get("rationale"),
            },
            "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
            "decision_policy": {
                "accepted_mapping_requires": [
                    "reviewer_decision=accept_alias_mapping",
                    "packet_fingerprint matches the current queue fingerprint",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                ],
                "allowed_decisions": ALLOWED_DECISIONS,
                "coverage_policy": (
                    "Accepted alias mappings are explicit facts, but downstream denominator coverage still "
                    "must decide how and when to mutate coverage counts."
                ),
            },
        }
        row = {
            "reviewer_decision_key": decision_key(packet),
            "packet_key": packet["packet_key"],
            "queue_key": packet.get("queue_key") or "",
            "official_program_key": packet.get("official_program_key") or "",
            "official_program_name": packet.get("official_program_name") or "",
            "official_program_type": packet.get("official_program_type") or "",
            "official_department": packet.get("official_department") or "",
            "loaded_program_name": packet.get("loaded_program_name") or "",
            "loaded_role": packet.get("loaded_role") or "",
            "loaded_person_count": as_int(packet.get("loaded_person_count")),
            "loaded_source_url": packet.get("loaded_source_url") or "",
            "alias_decision_status": packet.get("alias_decision_status") or "",
            "alias_confidence": packet.get("alias_confidence") or 0,
            "queue_status": queue_status,
            "allowed_decisions": "; ".join(ALLOWED_DECISIONS),
            "packet_fingerprint": fingerprint,
            "required_confirmation_fields": "; ".join(CONFIRMATION_FIELDS),
            "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
            "recommended_next_action": packet.get("recommended_next_action") or "",
            "review_question": packet.get("review_question") or "",
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        queue.append({field: row[field] for field in QUEUE_FIELDS})
    return queue


def manual_decisions_by_key() -> dict[str, dict]:
    ensure_manual_decisions_file()
    decisions = {}
    for row in read_csv(MANUAL_DECISIONS_CSV):
        key = row.get("reviewer_decision_key") or ""
        if key:
            decisions[key] = row
    return decisions


def classify_decision(queue_row: dict, decision: dict | None) -> tuple[str, int, str, str]:
    if queue_row.get("queue_status") != "ready_for_reviewer_decision":
        return (
            "not_ready_for_reviewer_decision",
            0,
            "packet_not_reviewer_ready",
            "collect_stronger_alias_or_scope_evidence",
        )
    if not decision:
        return (
            "pending_reviewer_decision",
            0,
            "manual_reviewer_decision_missing",
            "record_accept_reject_or_needs_more_evidence_decision",
        )
    reviewer_decision = decision.get("reviewer_decision") or ""
    if reviewer_decision not in ALLOWED_DECISIONS:
        return (
            "invalid_reviewer_decision",
            0,
            "reviewer_decision_not_in_allowed_decisions",
            "correct_manual_decision_value",
        )
    if decision.get("packet_fingerprint") != queue_row.get("packet_fingerprint"):
        return (
            "stale_decision_evidence_mismatch",
            0,
            "manual_decision_packet_fingerprint_does_not_match_current_packet",
            "re_review_current_packet_and_update_fingerprint",
        )
    if reviewer_decision == "accept_alias_mapping":
        missing = [field for field in CONFIRMATION_FIELDS if as_int(decision.get(field)) != 1]
        if missing:
            return (
                "invalid_acceptance_missing_confirmations",
                0,
                "missing_required_confirmations:" + ";".join(missing),
                "confirm_all_required_fields_or_change_decision",
            )
        return (
            "accepted_reviewer_decision",
            1,
            "none",
            "materialize_accepted_alias_mapping",
        )
    if reviewer_decision.startswith("reject_"):
        return (
            "rejected_by_reviewer",
            0,
            reviewer_decision,
            "retain_rejection_for_audit",
        )
    return (
        "deferred_needs_more_evidence",
        0,
        "reviewer_requested_more_evidence",
        "collect_additional_program_role_track_or_current_roster_evidence",
    )


def audit_rows(queue: list[dict], audited_at: str) -> list[dict]:
    decisions = manual_decisions_by_key()
    audits = []
    for row in queue:
        decision = decisions.get(row["reviewer_decision_key"])
        status, accepted, blocker, action = classify_decision(row, decision)
        reviewer_decision = (decision or {}).get("reviewer_decision") or "pending"
        evidence = {
            "queue_row": {
                "reviewer_decision_key": row.get("reviewer_decision_key"),
                "packet_key": row.get("packet_key"),
                "official_program_key": row.get("official_program_key"),
                "official_program_name": row.get("official_program_name"),
                "official_program_type": row.get("official_program_type"),
                "loaded_program_name": row.get("loaded_program_name"),
                "loaded_role": row.get("loaded_role"),
                "loaded_person_count": row.get("loaded_person_count"),
                "alias_decision_status": row.get("alias_decision_status"),
                "queue_status": row.get("queue_status"),
                "packet_fingerprint": row.get("packet_fingerprint"),
            },
            "manual_decision": decision or {},
            "decision_policy": {
                "accepted_mapping_requires": [
                    "matching packet_fingerprint",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                    "reviewer_decision=accept_alias_mapping",
                ],
            },
        }
        audit = {
            "reviewer_decision_key": row["reviewer_decision_key"],
            "packet_key": row["packet_key"],
            "official_program_key": row["official_program_key"],
            "official_program_name": row["official_program_name"],
            "official_program_type": row["official_program_type"],
            "official_department": row["official_department"],
            "loaded_program_name": row["loaded_program_name"],
            "loaded_role": row["loaded_role"],
            "loaded_person_count": row["loaded_person_count"],
            "reviewer_decision": reviewer_decision,
            "decision_status": status,
            "accepted_alias_mapping": accepted,
            "decision_blocker": blocker,
            "packet_fingerprint": row["packet_fingerprint"],
            "decision_packet_fingerprint": (decision or {}).get("packet_fingerprint", ""),
            "official_program_confirmed": as_int((decision or {}).get("official_program_confirmed")),
            "loaded_source_scope_confirmed": as_int((decision or {}).get("loaded_source_scope_confirmed")),
            "role_scope_confirmed": as_int((decision or {}).get("role_scope_confirmed")),
            "current_roster_confirmed": as_int((decision or {}).get("current_roster_confirmed")),
            "reviewer_name": (decision or {}).get("reviewer_name", ""),
            "decided_at": (decision or {}).get("decided_at", ""),
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": audited_at,
        }
        audits.append({field: audit[field] for field in AUDIT_FIELDS})
    return audits


def accepted_key(row: dict) -> str:
    return f"accepted_official_program_alias_{sha256_text(row['reviewer_decision_key'])[:20]}"


def accepted_mappings(queue: list[dict], audits: list[dict], materialized_at: str) -> list[dict]:
    queue_by_key = {row["reviewer_decision_key"]: row for row in queue}
    accepted = []
    for audit in audits:
        if as_int(audit["accepted_alias_mapping"]) != 1:
            continue
        queue_row = queue_by_key[audit["reviewer_decision_key"]]
        row = {
            "accepted_alias_key": accepted_key(audit),
            "reviewer_decision_key": audit["reviewer_decision_key"],
            "packet_key": audit["packet_key"],
            "official_program_key": audit["official_program_key"],
            "official_program_name": audit["official_program_name"],
            "official_program_type": audit["official_program_type"],
            "official_department": audit["official_department"],
            "loaded_program_name": audit["loaded_program_name"],
            "loaded_role": audit["loaded_role"],
            "loaded_person_count": audit["loaded_person_count"],
            "loaded_source_url": queue_row["loaded_source_url"],
            "alias_decision_status": queue_row["alias_decision_status"],
            "packet_fingerprint": audit["packet_fingerprint"],
            "accepted_by": audit["reviewer_name"],
            "accepted_at": audit["decided_at"],
            "coverage_mutation_allowed": 0,
            "display_safety_status": DISPLAY_SAFETY_STATUS,
            "evidence_json": dumps(
                {
                    "decision_audit": {
                        "reviewer_decision_key": audit.get("reviewer_decision_key"),
                        "packet_key": audit.get("packet_key"),
                        "decision_status": audit.get("decision_status"),
                        "accepted_alias_mapping": audit.get("accepted_alias_mapping"),
                        "packet_fingerprint": audit.get("packet_fingerprint"),
                    },
                    "queue_row": {
                        "official_program_key": queue_row.get("official_program_key"),
                        "official_program_name": queue_row.get("official_program_name"),
                        "loaded_program_name": queue_row.get("loaded_program_name"),
                        "loaded_person_count": queue_row.get("loaded_person_count"),
                        "alias_decision_status": queue_row.get("alias_decision_status"),
                    },
                }
            ),
            "materialized_at": materialized_at,
        }
        accepted.append({field: row[field] for field in ACCEPTED_FIELDS})
    return accepted


def write_db_table(conn: sqlite3.Connection, table: str, rows: list[dict], fields: list[str]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    field_sql = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    conn.executemany(f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})", rows)


def replay_manual_decisions(conn: sqlite3.Connection) -> None:
    rows = read_csv(MANUAL_DECISIONS_CSV)
    write_db_table(conn, "official_program_alias_reviewer_decisions", rows, MANUAL_FIELDS)


def write_summary(queue: list[dict], audits: list[dict], accepted: list[dict], generated_at: str) -> None:
    by_queue = Counter(row["queue_status"] for row in queue)
    by_status = Counter(row["decision_status"] for row in audits)
    by_decision = Counter(row["reviewer_decision"] for row in audits)
    by_action = Counter(row["recommended_next_action"] for row in audits)
    payload = {
        "generated_at": generated_at,
        "queue_rows": len(queue),
        "ready_queue_rows": by_queue.get("ready_for_reviewer_decision", 0),
        "manual_decision_rows": len(read_csv(MANUAL_DECISIONS_CSV)),
        "audit_rows": len(audits),
        "accepted_alias_mapping_rows": len(accepted),
        "accepted_alias_mapping_person_count": sum(as_int(row["loaded_person_count"]) for row in accepted),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "not_ready_rows": by_status.get("not_ready_for_reviewer_decision", 0),
        "by_queue_status": dict(sorted(by_queue.items())),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_reviewer_decision": dict(sorted(by_decision.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "acceptance_policy": (
            "Accepted official-program alias mappings require an explicit reviewer decision, "
            "a matching packet fingerprint, and all required confirmation fields set to 1. "
            "Accepted mappings do not mutate denominator coverage by themselves."
        ),
        "manual_decision_csv": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
        "queue_csv": str(QUEUE_CSV.relative_to(ROOT)),
        "audit_csv": str(AUDIT_CSV.relative_to(ROOT)),
        "accepted_mappings_csv": str(ACCEPTED_CSV.relative_to(ROOT)),
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    queue = build_queue(read_packets(conn), generated_at)
    audits = audit_rows(queue, generated_at)
    accepted = accepted_mappings(queue, audits, generated_at)

    write_csv(QUEUE_CSV, queue, QUEUE_FIELDS)
    write_json(QUEUE_JSON, queue)
    write_csv(AUDIT_CSV, audits, AUDIT_FIELDS)
    write_json(AUDIT_JSON, audits)
    write_csv(ACCEPTED_CSV, accepted, ACCEPTED_FIELDS)
    write_json(ACCEPTED_JSON, accepted)
    with conn:
        replay_manual_decisions(conn)
        write_db_table(conn, "official_program_alias_reviewer_decision_queue", queue, QUEUE_FIELDS)
        write_db_table(conn, "official_program_alias_reviewer_decision_audit", audits, AUDIT_FIELDS)
        write_db_table(conn, "accepted_official_program_alias_mappings", accepted, ACCEPTED_FIELDS)
    conn.close()
    write_summary(queue, audits, accepted, generated_at)
    print(dumps({"queue_rows": len(queue), "audit_rows": len(audits), "accepted_alias_mapping_rows": len(accepted)}))


if __name__ == "__main__":
    main()
