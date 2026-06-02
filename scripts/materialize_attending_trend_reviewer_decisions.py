#!/usr/bin/env python3
"""Materialize attending trend reviewer decision queues, audits, and accepted facts."""

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

QUEUE_CSV = ARTIFACTS / "attending_trend_reviewer_decision_queue.csv"
QUEUE_JSON = ARTIFACTS / "attending_trend_reviewer_decision_queue.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "attending_trend_reviewer_decisions.csv"
AUDIT_CSV = ARTIFACTS / "attending_trend_reviewer_decision_audit.csv"
AUDIT_JSON = ARTIFACTS / "attending_trend_reviewer_decision_audit.json"
FACTS_CSV = ARTIFACTS / "accepted_attending_trend_facts.csv"
FACTS_JSON = ARTIFACTS / "accepted_attending_trend_facts.json"
SUMMARY_JSON = ARTIFACTS / "attending_trend_reviewer_decision_summary.json"

ALLOWED_DECISIONS = [
    "accept_trend_fact",
    "reject_identity_mismatch",
    "reject_not_current_penn_endpoint",
    "reject_training_line_or_date",
    "needs_more_evidence",
]
CONFIRMATION_FIELDS = [
    "identity_confirmed",
    "endpoint_confirmed",
    "training_line_confirmed",
    "date_window_confirmed",
]
TREND_FACT_TYPE = "accepted_recent_penn_trained_current_attending"
DISPLAY_SAFETY_STATUS = "accepted_trend_fact_public_source_backed"

QUEUE_FIELDS = [
    "reviewer_decision_key",
    "trend_acceptance_key",
    "trend_claim_key",
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "trend_claim_type",
    "queue_status",
    "allowed_decisions",
    "claim_fingerprint",
    "ten_year_trend_window",
    "training_type",
    "training_line",
    "training_organization",
    "training_start_year",
    "training_end_year",
    "source_key",
    "source_url",
    "source_scope",
    "bridge_candidate_key",
    "required_confirmation_fields",
    "required_reviewer_action",
    "display_safety_status",
    "evidence_json",
    "generated_at",
]

MANUAL_FIELDS = [
    "reviewer_decision_key",
    "trend_acceptance_key",
    "trend_claim_key",
    "claim_fingerprint",
    "reviewer_decision",
    "reviewer_name",
    "decided_at",
    "identity_confirmed",
    "endpoint_confirmed",
    "training_line_confirmed",
    "date_window_confirmed",
    "decision_notes",
]

AUDIT_FIELDS = [
    "reviewer_decision_key",
    "trend_acceptance_key",
    "trend_claim_key",
    "display_name",
    "normalized_name",
    "reviewer_decision",
    "decision_status",
    "accepted_trend_fact",
    "decision_blocker",
    "claim_fingerprint",
    "decision_claim_fingerprint",
    "identity_confirmed",
    "endpoint_confirmed",
    "training_line_confirmed",
    "date_window_confirmed",
    "reviewer_name",
    "decided_at",
    "training_type",
    "training_line",
    "training_organization",
    "training_start_year",
    "training_end_year",
    "source_key",
    "source_url",
    "source_scope",
    "bridge_candidate_key",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]

FACT_FIELDS = [
    "trend_fact_key",
    "reviewer_decision_key",
    "trend_acceptance_key",
    "trend_claim_key",
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "trend_fact_type",
    "training_type",
    "training_line",
    "training_organization",
    "training_start_year",
    "training_end_year",
    "ten_year_trend_window",
    "source_key",
    "source_url",
    "source_scope",
    "bridge_candidate_key",
    "claim_fingerprint",
    "accepted_by",
    "accepted_at",
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
    if MANUAL_DECISIONS_CSV.exists():
        return
    write_csv(MANUAL_DECISIONS_CSV, [], MANUAL_FIELDS)


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def compact_acceptance_evidence(row: dict) -> dict:
    return {
        "trend_acceptance_key": row.get("trend_acceptance_key", ""),
        "trend_claim_key": row.get("trend_claim_key", ""),
        "trend_key": row.get("trend_key", ""),
        "display_name": row.get("display_name", ""),
        "normalized_name": row.get("normalized_name", ""),
        "acceptance_status": row.get("acceptance_status", ""),
        "acceptance_blocker": row.get("acceptance_blocker", ""),
        "acceptance_level": row.get("acceptance_level", ""),
        "training_type": row.get("training_type", ""),
        "training_line": row.get("training_line", ""),
        "training_organization": row.get("training_organization", ""),
        "training_start_year": row.get("training_start_year", ""),
        "training_end_year": row.get("training_end_year", ""),
        "ten_year_trend_window": row.get("ten_year_trend_window", ""),
        "source_key": row.get("source_key", ""),
        "source_url": row.get("source_url", ""),
        "source_scope": row.get("source_scope", ""),
        "bridge_candidate_key": row.get("bridge_candidate_key", ""),
        "endpoint_check_status": row.get("endpoint_check_status", ""),
        "training_line_check_status": row.get("training_line_check_status", ""),
        "date_window_check_status": row.get("date_window_check_status", ""),
        "required_reviewer_action": row.get("required_reviewer_action", ""),
    }


def compact_queue_evidence(row: dict) -> dict:
    return {
        "reviewer_decision_key": row.get("reviewer_decision_key", ""),
        "trend_acceptance_key": row.get("trend_acceptance_key", ""),
        "trend_claim_key": row.get("trend_claim_key", ""),
        "trend_key": row.get("trend_key", ""),
        "display_name": row.get("display_name", ""),
        "normalized_name": row.get("normalized_name", ""),
        "queue_status": row.get("queue_status", ""),
        "claim_fingerprint": row.get("claim_fingerprint", ""),
        "training_type": row.get("training_type", ""),
        "training_line": row.get("training_line", ""),
        "training_organization": row.get("training_organization", ""),
        "training_start_year": row.get("training_start_year", ""),
        "training_end_year": row.get("training_end_year", ""),
        "ten_year_trend_window": row.get("ten_year_trend_window", ""),
        "source_key": row.get("source_key", ""),
        "source_url": row.get("source_url", ""),
        "source_scope": row.get("source_scope", ""),
        "bridge_candidate_key": row.get("bridge_candidate_key", ""),
        "required_confirmation_fields": row.get("required_confirmation_fields", ""),
        "required_reviewer_action": row.get("required_reviewer_action", ""),
    }


def compact_manual_decision(decision: dict | None) -> dict:
    if not decision:
        return {}
    return {
        field: decision.get(field, "")
        for field in [
            "reviewer_decision_key",
            "trend_acceptance_key",
            "trend_claim_key",
            "claim_fingerprint",
            "reviewer_decision",
            "reviewer_name",
            "decided_at",
            "identity_confirmed",
            "endpoint_confirmed",
            "training_line_confirmed",
            "date_window_confirmed",
            "decision_notes",
        ]
    }


def compact_decision_audit(audit: dict) -> dict:
    return {
        "reviewer_decision_key": audit.get("reviewer_decision_key", ""),
        "trend_acceptance_key": audit.get("trend_acceptance_key", ""),
        "trend_claim_key": audit.get("trend_claim_key", ""),
        "display_name": audit.get("display_name", ""),
        "normalized_name": audit.get("normalized_name", ""),
        "reviewer_decision": audit.get("reviewer_decision", ""),
        "decision_status": audit.get("decision_status", ""),
        "accepted_trend_fact": audit.get("accepted_trend_fact", ""),
        "decision_blocker": audit.get("decision_blocker", ""),
        "claim_fingerprint": audit.get("claim_fingerprint", ""),
        "identity_confirmed": audit.get("identity_confirmed", ""),
        "endpoint_confirmed": audit.get("endpoint_confirmed", ""),
        "training_line_confirmed": audit.get("training_line_confirmed", ""),
        "date_window_confirmed": audit.get("date_window_confirmed", ""),
        "reviewer_name": audit.get("reviewer_name", ""),
        "decided_at": audit.get("decided_at", ""),
        "recommended_next_action": audit.get("recommended_next_action", ""),
        "audited_at": audit.get("audited_at", ""),
    }


def claim_fingerprint(row: dict) -> str:
    stable = {
        "trend_acceptance_key": row.get("trend_acceptance_key"),
        "trend_claim_key": row.get("trend_claim_key"),
        "trend_key": row.get("trend_key"),
        "display_name": row.get("display_name"),
        "normalized_name": row.get("normalized_name"),
        "training_type": row.get("training_type"),
        "training_line": row.get("training_line"),
        "training_organization": row.get("training_organization"),
        "training_start_year": row.get("training_start_year"),
        "training_end_year": row.get("training_end_year"),
        "source_url": row.get("source_url"),
        "bridge_candidate_key": row.get("bridge_candidate_key"),
    }
    return sha256_text(dumps(stable))


def read_acceptance_rows(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM attending_trend_acceptance_audit
        ORDER BY training_end_year DESC, display_name, trend_acceptance_key
        """,
    )


def queue_key(row: dict) -> str:
    return f"attending_trend_reviewer_decision_{sha256_text(row['trend_acceptance_key'])[:20]}"


def build_queue(rows: list[dict], generated_at: str) -> list[dict]:
    queue = []
    for row in rows:
        fingerprint = claim_fingerprint(row)
        queue_status = (
            "ready_for_reviewer_decision"
            if row.get("acceptance_status") == "review_ready_requires_explicit_reviewer_acceptance"
            else "not_ready_for_reviewer_decision"
        )
        evidence = {
            "acceptance_audit": compact_acceptance_evidence(row),
            "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
            "decision_policy": {
                "accepted_fact_requires": [
                    "reviewer_decision=accept_trend_fact",
                    "claim_fingerprint matches the current queue fingerprint",
                    "identity_confirmed=1",
                    "endpoint_confirmed=1",
                    "training_line_confirmed=1",
                    "date_window_confirmed=1",
                ],
                "allowed_decisions": ALLOWED_DECISIONS,
            },
        }
        item = {
            "reviewer_decision_key": queue_key(row),
            "trend_acceptance_key": row["trend_acceptance_key"],
            "trend_claim_key": row["trend_claim_key"],
            "trend_key": row["trend_key"],
            "event_group_key": row["event_group_key"],
            "display_name": row["display_name"],
            "normalized_name": row["normalized_name"],
            "trend_claim_type": row["trend_claim_type"],
            "queue_status": queue_status,
            "allowed_decisions": "; ".join(ALLOWED_DECISIONS),
            "claim_fingerprint": fingerprint,
            "ten_year_trend_window": row["ten_year_trend_window"],
            "training_type": row.get("training_type") or "",
            "training_line": row.get("training_line") or "",
            "training_organization": row.get("training_organization") or "",
            "training_start_year": row.get("training_start_year") or "",
            "training_end_year": row.get("training_end_year") or "",
            "source_key": row.get("source_key") or "",
            "source_url": row.get("source_url") or "",
            "source_scope": row.get("source_scope") or "",
            "bridge_candidate_key": row.get("bridge_candidate_key") or "",
            "required_confirmation_fields": "; ".join(CONFIRMATION_FIELDS),
            "required_reviewer_action": row.get("required_reviewer_action") or "",
            "display_safety_status": row.get("display_safety_status") or "",
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        queue.append({field: item[field] for field in QUEUE_FIELDS})
    return queue


def manual_decisions_by_key() -> dict[str, dict]:
    ensure_manual_decisions_file()
    decisions = {}
    for row in read_csv(MANUAL_DECISIONS_CSV):
        key = row.get("reviewer_decision_key") or ""
        if not key:
            continue
        decisions[key] = row
    return decisions


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
        return (
            "invalid_reviewer_decision",
            0,
            "reviewer_decision_not_in_allowed_decisions",
            "correct_manual_decision_value",
        )
    if decision.get("claim_fingerprint") != queue_row.get("claim_fingerprint"):
        return (
            "stale_decision_evidence_mismatch",
            0,
            "manual_decision_claim_fingerprint_does_not_match_current_claim",
            "re_review_current_claim_and_update_fingerprint",
        )
    if reviewer_decision == "accept_trend_fact":
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
            "materialize_accepted_trend_fact",
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
        "collect_additional_endpoint_training_identity_or_date_evidence",
    )


def audit_rows(queue: list[dict], audited_at: str) -> list[dict]:
    decisions = manual_decisions_by_key()
    result = []
    for row in queue:
        decision = decisions.get(row["reviewer_decision_key"])
        status, accepted, blocker, action = classify_decision(row, decision)
        reviewer_decision = decision.get("reviewer_decision") if decision else "pending"
        evidence = {
            "queue_row": compact_queue_evidence(row),
            "manual_decision": compact_manual_decision(decision),
            "decision_policy": {
                "accepted_fact_requires": [
                    "matching claim_fingerprint",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                    "reviewer_decision=accept_trend_fact",
                ],
            },
        }
        audit = {
            "reviewer_decision_key": row["reviewer_decision_key"],
            "trend_acceptance_key": row["trend_acceptance_key"],
            "trend_claim_key": row["trend_claim_key"],
            "display_name": row["display_name"],
            "normalized_name": row["normalized_name"],
            "reviewer_decision": reviewer_decision or "pending",
            "decision_status": status,
            "accepted_trend_fact": accepted,
            "decision_blocker": blocker,
            "claim_fingerprint": row["claim_fingerprint"],
            "decision_claim_fingerprint": (decision or {}).get("claim_fingerprint", ""),
            "identity_confirmed": as_int((decision or {}).get("identity_confirmed")),
            "endpoint_confirmed": as_int((decision or {}).get("endpoint_confirmed")),
            "training_line_confirmed": as_int((decision or {}).get("training_line_confirmed")),
            "date_window_confirmed": as_int((decision or {}).get("date_window_confirmed")),
            "reviewer_name": (decision or {}).get("reviewer_name", ""),
            "decided_at": (decision or {}).get("decided_at", ""),
            "training_type": row.get("training_type") or "",
            "training_line": row.get("training_line") or "",
            "training_organization": row.get("training_organization") or "",
            "training_start_year": row.get("training_start_year") or "",
            "training_end_year": row.get("training_end_year") or "",
            "source_key": row.get("source_key") or "",
            "source_url": row.get("source_url") or "",
            "source_scope": row.get("source_scope") or "",
            "bridge_candidate_key": row.get("bridge_candidate_key") or "",
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": audited_at,
        }
        result.append({field: audit[field] for field in AUDIT_FIELDS})
    return result


def fact_key(row: dict) -> str:
    return f"accepted_attending_trend_fact_{sha256_text(row['reviewer_decision_key'])[:20]}"


def accepted_facts(queue: list[dict], audits: list[dict], materialized_at: str) -> list[dict]:
    queue_by_key = {row["reviewer_decision_key"]: row for row in queue}
    facts = []
    for audit in audits:
        if as_int(audit["accepted_trend_fact"]) != 1:
            continue
        queue_row = queue_by_key[audit["reviewer_decision_key"]]
        fact = {
            "trend_fact_key": fact_key(audit),
            "reviewer_decision_key": audit["reviewer_decision_key"],
            "trend_acceptance_key": audit["trend_acceptance_key"],
            "trend_claim_key": audit["trend_claim_key"],
            "trend_key": queue_row["trend_key"],
            "event_group_key": queue_row["event_group_key"],
            "display_name": audit["display_name"],
            "normalized_name": audit["normalized_name"],
            "trend_fact_type": TREND_FACT_TYPE,
            "training_type": audit["training_type"],
            "training_line": audit["training_line"],
            "training_organization": audit["training_organization"],
            "training_start_year": audit["training_start_year"],
            "training_end_year": audit["training_end_year"],
            "ten_year_trend_window": queue_row["ten_year_trend_window"],
            "source_key": audit["source_key"],
            "source_url": audit["source_url"],
            "source_scope": audit["source_scope"],
            "bridge_candidate_key": audit["bridge_candidate_key"],
            "claim_fingerprint": audit["claim_fingerprint"],
            "accepted_by": audit["reviewer_name"],
            "accepted_at": audit["decided_at"],
            "display_safety_status": DISPLAY_SAFETY_STATUS,
            "evidence_json": dumps(
                {
                    "decision_audit": compact_decision_audit(audit),
                    "queue_row": compact_queue_evidence(queue_row),
                    "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
                    "provenance_policy": (
                        "Accepted trend facts retain compact provenance pointers in CSV; "
                        "the source URL, bridge candidate key, claim fingerprint, and reviewer "
                        "audit files are the replayable evidence chain."
                    ),
                }
            ),
            "materialized_at": materialized_at,
        }
        facts.append({field: fact[field] for field in FACT_FIELDS})
    return facts


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
    write_db_table(conn, "attending_trend_reviewer_decisions", rows, MANUAL_FIELDS)


def write_summary(queue: list[dict], audits: list[dict], facts: list[dict], generated_at: str) -> None:
    by_status = Counter(row["decision_status"] for row in audits)
    by_decision = Counter(row["reviewer_decision"] for row in audits)
    by_action = Counter(row["recommended_next_action"] for row in audits)
    by_end_year = Counter(str(row["training_end_year"]) for row in audits if row["training_end_year"])
    payload = {
        "generated_at": generated_at,
        "queue_rows": len(queue),
        "manual_decision_rows": len(read_csv(MANUAL_DECISIONS_CSV)),
        "audit_rows": len(audits),
        "accepted_trend_fact_rows": len(facts),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_reviewer_decision": dict(sorted(by_decision.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "by_training_end_year": dict(sorted(by_end_year.items())),
        "acceptance_policy": (
            "Accepted attending-trend facts require an explicit manual reviewer decision, "
            "a matching claim fingerprint, and all required confirmation fields set to 1."
        ),
        "manual_decision_csv": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
        "queue_csv": str(QUEUE_CSV.relative_to(ROOT)),
        "audit_csv": str(AUDIT_CSV.relative_to(ROOT)),
        "accepted_facts_csv": str(FACTS_CSV.relative_to(ROOT)),
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    queue = build_queue(read_acceptance_rows(conn), generated_at)
    audits = audit_rows(queue, generated_at)
    facts = accepted_facts(queue, audits, generated_at)

    write_csv(QUEUE_CSV, queue, QUEUE_FIELDS)
    write_json(QUEUE_JSON, queue)
    write_csv(AUDIT_CSV, audits, AUDIT_FIELDS)
    write_json(AUDIT_JSON, audits)
    write_csv(FACTS_CSV, facts, FACT_FIELDS)
    write_json(FACTS_JSON, facts)
    with conn:
        replay_manual_decisions(conn)
        write_db_table(conn, "attending_trend_reviewer_decision_queue", queue, QUEUE_FIELDS)
        write_db_table(conn, "attending_trend_reviewer_decision_audit", audits, AUDIT_FIELDS)
        write_db_table(conn, "accepted_attending_trend_facts", facts, FACT_FIELDS)
    conn.close()
    write_summary(queue, audits, facts, generated_at)
    print(dumps({"queue_rows": len(queue), "audit_rows": len(audits), "accepted_trend_fact_rows": len(facts)}))


if __name__ == "__main__":
    main()
