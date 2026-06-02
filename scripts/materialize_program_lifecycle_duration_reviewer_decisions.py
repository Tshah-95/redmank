#!/usr/bin/env python3
"""Materialize reviewer decisions for program lifecycle-duration evidence."""

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

QUEUE_CSV = ARTIFACTS / "program_lifecycle_duration_reviewer_decision_queue.csv"
QUEUE_JSON = ARTIFACTS / "program_lifecycle_duration_reviewer_decision_queue.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "program_lifecycle_duration_reviewer_decisions.csv"
AUDIT_CSV = ARTIFACTS / "program_lifecycle_duration_reviewer_decision_audit.csv"
AUDIT_JSON = ARTIFACTS / "program_lifecycle_duration_reviewer_decision_audit.json"
ACCEPTED_CSV = ARTIFACTS / "accepted_program_lifecycle_duration_mappings.csv"
ACCEPTED_JSON = ARTIFACTS / "accepted_program_lifecycle_duration_mappings.json"
SUMMARY_JSON = ARTIFACTS / "program_lifecycle_duration_reviewer_decision_summary.json"

ALLOWED_DECISIONS = [
    "accept_lifecycle_duration",
    "reject_page_scope_mismatch",
    "reject_duration_context",
    "reject_wrong_program_or_track",
    "needs_more_evidence",
]

CONFIRMATION_FIELDS = [
    "official_program_confirmed",
    "duration_phrase_confirmed",
    "duration_years_confirmed",
    "role_family_confirmed",
    "lifecycle_scope_confirmed",
]

DISPLAY_SAFETY_STATUS = "accepted_public_program_duration_evidence"
REQUIRED_REVIEWER_ACTION = (
    "Confirm the official program page, duration phrase, explicit duration years, trainee role family, "
    "and lifecycle scope before accepting a duration mapping."
)

QUEUE_FIELDS = [
    "reviewer_decision_key",
    "duration_evidence_key",
    "observation_key",
    "audit_key",
    "official_program_key",
    "matched_program_key",
    "official_program_type",
    "official_program_name",
    "matched_program_name",
    "identifier_value",
    "source_program_specialty",
    "source_url",
    "page_title",
    "explicit_duration_years",
    "duration_evidence_status",
    "duration_confidence",
    "queue_status",
    "allowed_decisions",
    "evidence_fingerprint",
    "required_confirmation_fields",
    "required_reviewer_action",
    "recommended_next_action",
    "review_question",
    "evidence_json",
    "generated_at",
]

MANUAL_FIELDS = [
    "reviewer_decision_key",
    "duration_evidence_key",
    "evidence_fingerprint",
    "reviewer_decision",
    "reviewer_name",
    "decided_at",
    "official_program_confirmed",
    "duration_phrase_confirmed",
    "duration_years_confirmed",
    "role_family_confirmed",
    "lifecycle_scope_confirmed",
    "decision_notes",
]

AUDIT_FIELDS = [
    "reviewer_decision_key",
    "duration_evidence_key",
    "observation_key",
    "audit_key",
    "official_program_key",
    "matched_program_key",
    "official_program_type",
    "official_program_name",
    "matched_program_name",
    "identifier_value",
    "source_program_specialty",
    "explicit_duration_years",
    "reviewer_decision",
    "decision_status",
    "accepted_duration_mapping",
    "decision_blocker",
    "evidence_fingerprint",
    "decision_evidence_fingerprint",
    "official_program_confirmed",
    "duration_phrase_confirmed",
    "duration_years_confirmed",
    "role_family_confirmed",
    "lifecycle_scope_confirmed",
    "reviewer_name",
    "decided_at",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]

ACCEPTED_FIELDS = [
    "accepted_duration_key",
    "reviewer_decision_key",
    "duration_evidence_key",
    "official_program_key",
    "matched_program_key",
    "official_program_type",
    "official_program_name",
    "matched_program_name",
    "identifier_value",
    "source_program_specialty",
    "source_url",
    "page_title",
    "explicit_duration_years",
    "proposed_rule_action",
    "evidence_fingerprint",
    "accepted_by",
    "accepted_at",
    "lifecycle_rule_mutation_allowed",
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


def read_duration_evidence(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM program_lifecycle_duration_evidence
        ORDER BY
          CASE duration_evidence_status
            WHEN 'reviewer_ready_duration_lifecycle_candidate' THEN 0
            WHEN 'conflicting_duration_evidence_review' THEN 1
            WHEN 'duration_source_program_mismatch_review' THEN 2
            ELSE 3
          END,
          official_program_type,
          official_program_name,
          duration_evidence_key
        """,
    )


def evidence_fingerprint(row: dict) -> str:
    stable = {
        "duration_evidence_key": row.get("duration_evidence_key"),
        "observation_key": row.get("observation_key"),
        "official_program_key": row.get("official_program_key"),
        "matched_program_key": row.get("matched_program_key"),
        "official_program_type": row.get("official_program_type"),
        "official_program_name": row.get("official_program_name"),
        "matched_program_name": row.get("matched_program_name"),
        "identifier_value": row.get("identifier_value"),
        "source_program_specialty": row.get("source_program_specialty"),
        "source_url": row.get("source_url"),
        "page_title": row.get("page_title"),
        "explicit_duration_years": row.get("explicit_duration_years"),
        "duration_phrase": row.get("duration_phrase"),
        "duration_context": row.get("duration_context"),
        "duration_evidence_status": row.get("duration_evidence_status"),
        "match_reasons_json": row.get("match_reasons_json"),
    }
    return sha256_text(dumps(stable))


def decision_key(row: dict) -> str:
    return f"program_lifecycle_duration_reviewer_decision_{sha256_text(row['duration_evidence_key'])[:20]}"


def queue_status(row: dict) -> str:
    status = row.get("duration_evidence_status") or ""
    if status == "reviewer_ready_duration_lifecycle_candidate" and row.get("explicit_duration_years"):
        return "ready_for_reviewer_decision"
    if status in {"conflicting_duration_evidence_review", "duration_source_program_mismatch_review"}:
        return "context_review_required_before_decision"
    return "not_ready_for_reviewer_decision"


def review_question(row: dict) -> str:
    years = row.get("explicit_duration_years") or "unknown"
    return (
        f"Does the official page for {row.get('official_program_name') or 'this program'} support a "
        f"{years}-year lifecycle duration for the matched Penn trainee program?"
    )


def build_queue(rows: list[dict], generated_at: str) -> list[dict]:
    queue = []
    for item in rows:
        fingerprint = evidence_fingerprint(item)
        evidence = {
            "duration_evidence": {
                "duration_evidence_key": item.get("duration_evidence_key"),
                "official_program_key": item.get("official_program_key"),
                "official_program_name": item.get("official_program_name"),
                "matched_program_name": item.get("matched_program_name"),
                "identifier_value": item.get("identifier_value"),
                "source_program_specialty": item.get("source_program_specialty"),
                "source_url": item.get("source_url"),
                "page_title": item.get("page_title"),
                "explicit_duration_years": item.get("explicit_duration_years"),
                "duration_phrase": item.get("duration_phrase"),
                "duration_context": item.get("duration_context"),
                "duration_evidence_status": item.get("duration_evidence_status"),
                "recommended_action": item.get("recommended_action"),
                "confidence": item.get("confidence"),
                "match_reasons_json": item.get("match_reasons_json"),
            },
            "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
            "decision_policy": {
                "accepted_mapping_requires": [
                    "reviewer_decision=accept_lifecycle_duration",
                    "evidence_fingerprint matches the current queue fingerprint",
                    "queue_status=ready_for_reviewer_decision",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                ],
                "allowed_decisions": ALLOWED_DECISIONS,
                "mutation_policy": (
                    "Accepted duration mappings are evidence-backed lifecycle candidates. They do not mutate "
                    "training lifecycle rules until a later config/rule change cites the accepted mapping."
                ),
            },
        }
        row = {
            "reviewer_decision_key": decision_key(item),
            "duration_evidence_key": item["duration_evidence_key"],
            "observation_key": item.get("observation_key") or "",
            "audit_key": item.get("audit_key") or "",
            "official_program_key": item.get("official_program_key") or "",
            "matched_program_key": item.get("matched_program_key") or "",
            "official_program_type": item.get("official_program_type") or "",
            "official_program_name": item.get("official_program_name") or "",
            "matched_program_name": item.get("matched_program_name") or "",
            "identifier_value": item.get("identifier_value") or "",
            "source_program_specialty": item.get("source_program_specialty") or "",
            "source_url": item.get("source_url") or "",
            "page_title": item.get("page_title") or "",
            "explicit_duration_years": item.get("explicit_duration_years") or "",
            "duration_evidence_status": item.get("duration_evidence_status") or "",
            "duration_confidence": item.get("confidence") or 0,
            "queue_status": queue_status(item),
            "allowed_decisions": "; ".join(ALLOWED_DECISIONS),
            "evidence_fingerprint": fingerprint,
            "required_confirmation_fields": "; ".join(CONFIRMATION_FIELDS),
            "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
            "recommended_next_action": item.get("recommended_action") or "",
            "review_question": review_question(item),
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
            queue_row.get("queue_status") or "evidence_not_reviewer_ready",
            "resolve_duration_context_or_collect_stronger_official_duration_evidence",
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
    if decision.get("evidence_fingerprint") != queue_row.get("evidence_fingerprint"):
        return (
            "stale_decision_evidence_mismatch",
            0,
            "manual_decision_evidence_fingerprint_does_not_match_current_evidence",
            "re_review_current_duration_evidence_and_update_fingerprint",
        )
    if reviewer_decision == "accept_lifecycle_duration":
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
            "materialize_accepted_duration_mapping",
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
        "collect_additional_official_duration_or_scope_evidence",
    )


def audit_rows(queue: list[dict], audited_at: str) -> list[dict]:
    decisions = manual_decisions_by_key()
    audits = []
    for row in queue:
        decision = decisions.get(row["reviewer_decision_key"])
        status, accepted, blocker, action = classify_decision(row, decision)
        evidence = {
            "queue_row": {
                "reviewer_decision_key": row.get("reviewer_decision_key"),
                "duration_evidence_key": row.get("duration_evidence_key"),
                "official_program_key": row.get("official_program_key"),
                "official_program_name": row.get("official_program_name"),
                "matched_program_name": row.get("matched_program_name"),
                "source_url": row.get("source_url"),
                "page_title": row.get("page_title"),
                "explicit_duration_years": row.get("explicit_duration_years"),
                "duration_evidence_status": row.get("duration_evidence_status"),
                "queue_status": row.get("queue_status"),
                "evidence_fingerprint": row.get("evidence_fingerprint"),
            },
            "manual_decision": decision or {},
            "decision_policy": {
                "accepted_mapping_requires": [
                    "matching evidence_fingerprint",
                    "queue_status=ready_for_reviewer_decision",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                    "reviewer_decision=accept_lifecycle_duration",
                ],
            },
        }
        audit = {
            "reviewer_decision_key": row["reviewer_decision_key"],
            "duration_evidence_key": row["duration_evidence_key"],
            "observation_key": row["observation_key"],
            "audit_key": row["audit_key"],
            "official_program_key": row["official_program_key"],
            "matched_program_key": row["matched_program_key"],
            "official_program_type": row["official_program_type"],
            "official_program_name": row["official_program_name"],
            "matched_program_name": row["matched_program_name"],
            "identifier_value": row["identifier_value"],
            "source_program_specialty": row["source_program_specialty"],
            "explicit_duration_years": row["explicit_duration_years"],
            "reviewer_decision": (decision or {}).get("reviewer_decision", "pending"),
            "decision_status": status,
            "accepted_duration_mapping": accepted,
            "decision_blocker": blocker,
            "evidence_fingerprint": row["evidence_fingerprint"],
            "decision_evidence_fingerprint": (decision or {}).get("evidence_fingerprint", ""),
            "official_program_confirmed": as_int((decision or {}).get("official_program_confirmed")),
            "duration_phrase_confirmed": as_int((decision or {}).get("duration_phrase_confirmed")),
            "duration_years_confirmed": as_int((decision or {}).get("duration_years_confirmed")),
            "role_family_confirmed": as_int((decision or {}).get("role_family_confirmed")),
            "lifecycle_scope_confirmed": as_int((decision or {}).get("lifecycle_scope_confirmed")),
            "reviewer_name": (decision or {}).get("reviewer_name", ""),
            "decided_at": (decision or {}).get("decided_at", ""),
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": audited_at,
        }
        audits.append({field: audit[field] for field in AUDIT_FIELDS})
    return audits


def accepted_key(row: dict) -> str:
    return f"accepted_program_lifecycle_duration_{sha256_text(row['reviewer_decision_key'])[:20]}"


def accepted_mappings(queue: list[dict], audits: list[dict], materialized_at: str) -> list[dict]:
    queue_by_key = {row["reviewer_decision_key"]: row for row in queue}
    accepted = []
    for audit in audits:
        if as_int(audit["accepted_duration_mapping"]) != 1:
            continue
        queue_row = queue_by_key[audit["reviewer_decision_key"]]
        row = {
            "accepted_duration_key": accepted_key(audit),
            "reviewer_decision_key": audit["reviewer_decision_key"],
            "duration_evidence_key": audit["duration_evidence_key"],
            "official_program_key": audit["official_program_key"],
            "matched_program_key": audit["matched_program_key"],
            "official_program_type": audit["official_program_type"],
            "official_program_name": audit["official_program_name"],
            "matched_program_name": audit["matched_program_name"],
            "identifier_value": audit["identifier_value"],
            "source_program_specialty": audit["source_program_specialty"],
            "source_url": queue_row["source_url"],
            "page_title": queue_row["page_title"],
            "explicit_duration_years": as_int(audit["explicit_duration_years"]),
            "proposed_rule_action": "add_or_update_specific_lifecycle_rule_after_config_review",
            "evidence_fingerprint": audit["evidence_fingerprint"],
            "accepted_by": audit["reviewer_name"],
            "accepted_at": audit["decided_at"],
            "lifecycle_rule_mutation_allowed": 0,
            "display_safety_status": DISPLAY_SAFETY_STATUS,
            "evidence_json": dumps(
                {
                    "decision_audit": {
                        "reviewer_decision_key": audit.get("reviewer_decision_key"),
                        "duration_evidence_key": audit.get("duration_evidence_key"),
                        "decision_status": audit.get("decision_status"),
                        "accepted_duration_mapping": audit.get("accepted_duration_mapping"),
                        "evidence_fingerprint": audit.get("evidence_fingerprint"),
                    },
                    "queue_row": {
                        "official_program_key": queue_row.get("official_program_key"),
                        "official_program_name": queue_row.get("official_program_name"),
                        "matched_program_name": queue_row.get("matched_program_name"),
                        "source_url": queue_row.get("source_url"),
                        "page_title": queue_row.get("page_title"),
                        "explicit_duration_years": queue_row.get("explicit_duration_years"),
                    },
                    "mutation_policy": (
                        "Accepted mapping is a public-source-backed lifecycle candidate. It does not mutate "
                        "config/training_lifecycle_rules.json without a later rule change."
                    ),
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
    write_db_table(conn, "program_lifecycle_duration_reviewer_decisions", rows, MANUAL_FIELDS)


def write_summary(queue: list[dict], audits: list[dict], accepted: list[dict], generated_at: str) -> None:
    by_queue = Counter(row["queue_status"] for row in queue)
    by_status = Counter(row["decision_status"] for row in audits)
    by_decision = Counter(row["reviewer_decision"] for row in audits)
    by_action = Counter(row["recommended_next_action"] for row in audits)
    payload = {
        "generated_at": generated_at,
        "queue_rows": len(queue),
        "ready_queue_rows": by_queue.get("ready_for_reviewer_decision", 0),
        "context_review_rows": by_queue.get("context_review_required_before_decision", 0),
        "not_ready_rows": by_queue.get("not_ready_for_reviewer_decision", 0),
        "manual_decision_rows": len(read_csv(MANUAL_DECISIONS_CSV)),
        "audit_rows": len(audits),
        "accepted_duration_mapping_rows": len(accepted),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "by_queue_status": dict(sorted(by_queue.items())),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_reviewer_decision": dict(sorted(by_decision.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "acceptance_policy": (
            "Accepted lifecycle-duration mappings require an explicit reviewer decision, a matching evidence "
            "fingerprint, queue readiness, and all required confirmation fields set to 1. Accepted mappings "
            "do not mutate lifecycle rules by themselves."
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
    queue = build_queue(read_duration_evidence(conn), generated_at)
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
        write_db_table(conn, "program_lifecycle_duration_reviewer_decision_queue", queue, QUEUE_FIELDS)
        write_db_table(conn, "program_lifecycle_duration_reviewer_decision_audit", audits, AUDIT_FIELDS)
        write_db_table(conn, "accepted_program_lifecycle_duration_mappings", accepted, ACCEPTED_FIELDS)
    conn.close()
    write_summary(queue, audits, accepted, generated_at)
    print(dumps({"queue_rows": len(queue), "audit_rows": len(audits), "accepted_duration_mapping_rows": len(accepted)}))


if __name__ == "__main__":
    main()
