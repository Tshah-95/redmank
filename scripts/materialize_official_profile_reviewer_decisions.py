#!/usr/bin/env python3
"""Materialize reviewer decisions for official trainee profile URL candidates."""

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

QUEUE_CSV = ARTIFACTS / "official_profile_reviewer_decision_queue.csv"
QUEUE_JSON = ARTIFACTS / "official_profile_reviewer_decision_queue.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "official_profile_reviewer_decisions.csv"
AUDIT_CSV = ARTIFACTS / "official_profile_reviewer_decision_audit.csv"
AUDIT_JSON = ARTIFACTS / "official_profile_reviewer_decision_audit.json"
ACCEPTED_CSV = ARTIFACTS / "accepted_official_profile_url_facts.csv"
ACCEPTED_JSON = ARTIFACTS / "accepted_official_profile_url_facts.json"
SUMMARY_JSON = ARTIFACTS / "official_profile_reviewer_decision_summary.json"
REOBSERVATION_CSV = ARTIFACTS / "official_profile_reobservation_audit.csv"

ALLOWED_DECISIONS = [
    "accept_official_profile_url",
    "reject_identity_mismatch",
    "reject_not_official_source",
    "reject_wrong_or_stale_context",
    "needs_more_evidence",
]
CONFIRMATION_FIELDS = [
    "person_identity_confirmed",
    "official_source_confirmed",
    "profile_context_confirmed",
    "source_hash_confirmed",
    "display_safety_confirmed",
]
DISPLAY_SAFETY_STATUS = "accepted_official_profile_url_public_source_backed"
ROSTER_TRUTH_STATUS = "profile_url_fact_not_current_roster_truth"
REQUIRED_REVIEWER_ACTION = (
    "Confirm same-person identity, official Penn/Penn Medicine/CHOP source ownership, profile context, "
    "content hash/source observation, and display-safety scope before accepting the profile URL fact."
)

QUEUE_FIELDS = [
    "reviewer_decision_key",
    "profile_workbench_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "task_key",
    "candidate_url",
    "candidate_title",
    "candidate_domain",
    "candidate_confidence",
    "candidate_http_status",
    "candidate_features",
    "source_sha256",
    "queue_status",
    "allowed_decisions",
    "profile_fingerprint",
    "required_confirmation_fields",
    "required_reviewer_action",
    "recommended_next_action",
    "display_safety_status",
    "evidence_json",
    "generated_at",
]

MANUAL_FIELDS = [
    "reviewer_decision_key",
    "profile_workbench_key",
    "profile_fingerprint",
    "reviewer_decision",
    "reviewer_name",
    "decided_at",
    "person_identity_confirmed",
    "official_source_confirmed",
    "profile_context_confirmed",
    "source_hash_confirmed",
    "display_safety_confirmed",
    "decision_notes",
]

AUDIT_FIELDS = [
    "reviewer_decision_key",
    "profile_workbench_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "candidate_url",
    "reviewer_decision",
    "decision_status",
    "accepted_official_profile_url",
    "decision_blocker",
    "profile_fingerprint",
    "decision_profile_fingerprint",
    "person_identity_confirmed",
    "official_source_confirmed",
    "profile_context_confirmed",
    "source_hash_confirmed",
    "display_safety_confirmed",
    "reviewer_name",
    "decided_at",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]

ACCEPTED_FIELDS = [
    "accepted_profile_key",
    "reviewer_decision_key",
    "profile_workbench_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "profile_url",
    "profile_title",
    "source_domain",
    "source_sha256",
    "profile_fingerprint",
    "accepted_by",
    "accepted_at",
    "display_safety_status",
    "roster_truth_status",
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


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def replay_reobservations(conn: sqlite3.Connection) -> None:
    if not REOBSERVATION_CSV.exists():
        return
    rows = read_csv(REOBSERVATION_CSV)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    columns = {row[1] for row in conn.execute("PRAGMA table_info(official_profile_reobservation_audit)")}
    if "canonical_url" not in columns:
        conn.execute("ALTER TABLE official_profile_reobservation_audit ADD COLUMN canonical_url TEXT")
        columns.add("canonical_url")
    conn.execute("DELETE FROM official_profile_reobservation_audit")
    if not rows:
        return
    row_columns = [column for column in rows[0].keys() if column in columns]
    fields = ", ".join(row_columns)
    placeholders = ", ".join(f":{field}" for field in row_columns)
    db_rows = []
    for row in rows:
        db_row = {field: row.get(field, "") for field in row_columns}
        if "http_status" in db_row and db_row.get("http_status") == "":
            db_row["http_status"] = None
        db_rows.append(db_row)
    conn.executemany(
        f"INSERT OR REPLACE INTO official_profile_reobservation_audit ({fields}) VALUES ({placeholders})",
        db_rows,
    )


def candidate_records(row: dict) -> list[dict]:
    try:
        records = json.loads(row.get("candidate_evidence_json") or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(records, list):
        return []
    return [record for record in records if isinstance(record, dict)]


def best_candidate_record(row: dict) -> dict:
    target_url = row.get("best_candidate_url") or ""
    records = candidate_records(row)
    for record in records:
        if record.get("candidate_url") == target_url:
            return record
    return records[0] if records else {}


def profile_fingerprint(row: dict, source_sha256: str) -> str:
    stable = {
        "profile_workbench_key": row.get("profile_workbench_key"),
        "person_key": row.get("person_key"),
        "display_name": row.get("display_name"),
        "role": row.get("role"),
        "program_name": row.get("program_name"),
        "candidate_url": row.get("best_candidate_url"),
        "candidate_title": row.get("best_candidate_title"),
        "candidate_domain": row.get("best_candidate_domain"),
        "candidate_http_status": row.get("best_candidate_http_status"),
        "candidate_features": row.get("best_candidate_features"),
        "source_sha256": source_sha256,
    }
    return sha256_text(dumps(stable))


def decision_key(row: dict) -> str:
    return "official_profile_reviewer_decision_" + sha256_text(row["profile_workbench_key"])[:20]


def read_workbench(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM official_profile_discovery_workbench
        WHERE discovery_lane = 'review_official_profile_candidate'
        ORDER BY discovery_priority DESC, display_name, profile_workbench_key
        """,
    )


def read_candidate_index(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = sqlite_rows(
        conn,
        """
        SELECT
          candidate_key,
          source_key,
          sha256,
          probed_at,
          text_length,
          content_type,
          evidence_json
        FROM trainee_profile_discovery_candidates
        WHERE candidate_status = 'official_profile_candidate'
        """,
    )
    return {row["candidate_key"]: row for row in rows}


def read_reobservations(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = sqlite_rows(
        conn,
        """
        SELECT *
        FROM official_profile_reobservation_audit
        ORDER BY profile_workbench_key, reobserved_at DESC, evidence_strength DESC
        """,
    )
    latest = {}
    for row in rows:
        latest.setdefault(row["profile_workbench_key"], row)
    return latest


def candidate_detail(candidate: dict, candidate_index: dict[str, dict]) -> dict:
    candidate_key = candidate.get("candidate_key") or ""
    if not candidate_key:
        return {}
    detail = candidate_index.get(candidate_key, {})
    if not detail:
        return {}
    try:
        evidence = json.loads(detail.get("evidence_json") or "{}")
    except json.JSONDecodeError:
        evidence = {}
    return {
        "candidate_key": detail.get("candidate_key") or "",
        "source_key": detail.get("source_key") or "",
        "sha256": detail.get("sha256") or "",
        "probed_at": detail.get("probed_at") or "",
        "text_length": detail.get("text_length") or "",
        "content_type": detail.get("content_type") or "",
        "probe_sha256": evidence.get("probe_sha256") if isinstance(evidence, dict) else "",
        "probe_http_status": evidence.get("probe_http_status") if isinstance(evidence, dict) else "",
        "probe_title": evidence.get("probe_title") if isinstance(evidence, dict) else "",
    }


def candidate_source_sha256(candidate: dict, detail: dict) -> str:
    return (
        detail.get("sha256")
        or detail.get("probe_sha256")
        or candidate.get("sha256")
        or candidate.get("probe_sha256")
        or ""
    )


def compact_workbench(row: dict, candidate: dict) -> dict:
    return {
        "profile_workbench_key": row.get("profile_workbench_key"),
        "person_key": row.get("person_key"),
        "display_name": row.get("display_name"),
        "role": row.get("role"),
        "program_name": row.get("program_name"),
        "task_key": row.get("task_key"),
        "best_candidate_status": row.get("best_candidate_status"),
        "best_candidate_url": row.get("best_candidate_url"),
        "best_candidate_title": row.get("best_candidate_title"),
        "best_candidate_domain": row.get("best_candidate_domain"),
        "best_candidate_confidence": row.get("best_candidate_confidence"),
        "best_candidate_http_status": row.get("best_candidate_http_status"),
        "best_candidate_features": row.get("best_candidate_features"),
        "evidence_required": row.get("evidence_required"),
        "candidate_record": candidate,
    }


def recommended_action(reobservation: dict | None = None) -> str:
    if (
        reobservation
        and reobservation.get("reobservation_status") == "fresh_source_resolved_to_generic_academic_departments_page"
    ):
        return "replace_or_reprobe_stale_profile_candidate_before_reviewer_acceptance"
    if (
        reobservation
        and reobservation.get("reobservation_status") == "fresh_official_profile_context_reobserved"
    ):
        return "record_accept_reject_or_needs_more_evidence_decision_using_fresh_profile_reobservation"
    if (
        reobservation
        and reobservation.get("reobservation_status") == "fresh_official_profile_identity_reobserved_context_review"
    ):
        return "review_profile_context_then_record_accept_reject_or_needs_more_evidence_decision"
    return "record_accept_reject_or_needs_more_evidence_decision"


def build_queue(
    workbench_rows: list[dict],
    candidate_index: dict[str, dict],
    reobservations: dict[str, dict],
    generated_at: str,
) -> list[dict]:
    queue = []
    for row in workbench_rows:
        candidate = best_candidate_record(row)
        detail = candidate_detail(candidate, candidate_index)
        reobservation = reobservations.get(row["profile_workbench_key"])
        source_sha256 = (reobservation or {}).get("source_hash") or candidate_source_sha256(candidate, detail)
        fingerprint = profile_fingerprint(row, source_sha256)
        evidence = {
            "official_profile_discovery_workbench": compact_workbench(row, candidate),
            "trainee_profile_candidate_source_observation": detail,
            "current_source_reobservation": {
                "profile_reobservation_key": (reobservation or {}).get("profile_reobservation_key", ""),
                "reobservation_status": (reobservation or {}).get("reobservation_status", ""),
                "evidence_strength": (reobservation or {}).get("evidence_strength", ""),
                "source_hash": (reobservation or {}).get("source_hash", ""),
                "http_status": (reobservation or {}).get("http_status", ""),
                "title": (reobservation or {}).get("title", ""),
                "canonical_url": (reobservation or {}).get("canonical_url", ""),
                "name_present": (reobservation or {}).get("name_present", ""),
                "program_context_present": (reobservation or {}).get("program_context_present", ""),
                "role_or_training_context_present": (reobservation or {}).get("role_or_training_context_present", ""),
                "official_domain_confirmed": (reobservation or {}).get("official_domain_confirmed", ""),
                "profile_path_confirmed": (reobservation or {}).get("profile_path_confirmed", ""),
                "match_context": (reobservation or {}).get("match_context", ""),
                "reobserved_at": (reobservation or {}).get("reobserved_at", ""),
            },
            "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
            "decision_policy": {
                "accepted_profile_url_requires": [
                    "reviewer_decision=accept_official_profile_url",
                    "profile_fingerprint matches the current queue fingerprint",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                ],
                "allowed_decisions": ALLOWED_DECISIONS,
                "roster_truth_policy": (
                    "Accepted official profile URL facts do not prove current trainee status; current roster "
                    "truth remains governed by official roster and training-state evidence."
                ),
            },
        }
        item = {
            "reviewer_decision_key": decision_key(row),
            "profile_workbench_key": row["profile_workbench_key"],
            "person_key": row["person_key"],
            "display_name": row["display_name"],
            "role": row.get("role") or "",
            "program_name": row.get("program_name") or "",
            "task_key": row.get("task_key") or "",
            "candidate_url": row.get("best_candidate_url") or "",
            "candidate_title": row.get("best_candidate_title") or "",
            "candidate_domain": row.get("best_candidate_domain") or "",
            "candidate_confidence": row.get("best_candidate_confidence") or 0,
            "candidate_http_status": row.get("best_candidate_http_status") or "",
            "candidate_features": row.get("best_candidate_features") or "",
            "source_sha256": source_sha256,
            "queue_status": "ready_for_reviewer_decision",
            "allowed_decisions": "; ".join(ALLOWED_DECISIONS),
            "profile_fingerprint": fingerprint,
            "required_confirmation_fields": "; ".join(CONFIRMATION_FIELDS),
            "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
            "recommended_next_action": recommended_action(reobservation),
            "display_safety_status": "review_ready_not_accepted_profile_url",
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        queue.append({field: item[field] for field in QUEUE_FIELDS})
    return queue


def ensure_manual_decisions_file() -> None:
    if not MANUAL_DECISIONS_CSV.exists():
        write_csv(MANUAL_DECISIONS_CSV, [], MANUAL_FIELDS)


def manual_decisions_by_key() -> dict[str, dict]:
    ensure_manual_decisions_file()
    return {row["reviewer_decision_key"]: row for row in read_csv(MANUAL_DECISIONS_CSV) if row.get("reviewer_decision_key")}


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
            queue_row.get("recommended_next_action") or "record_accept_reject_or_needs_more_evidence_decision",
        )
    reviewer_decision = decision.get("reviewer_decision") or ""
    if reviewer_decision not in ALLOWED_DECISIONS:
        return ("invalid_reviewer_decision", 0, "reviewer_decision_not_in_allowed_decisions", "correct_manual_decision_value")
    if decision.get("profile_fingerprint") != queue_row.get("profile_fingerprint"):
        return (
            "stale_decision_evidence_mismatch",
            0,
            "manual_decision_profile_fingerprint_does_not_match_current_candidate",
            "re_review_current_candidate_and_update_fingerprint",
        )
    if reviewer_decision == "accept_official_profile_url":
        missing = [field for field in CONFIRMATION_FIELDS if as_int(decision.get(field)) != 1]
        if missing:
            return (
                "invalid_acceptance_missing_confirmations",
                0,
                "missing_required_confirmations:" + ";".join(missing),
                "confirm_all_required_fields_or_change_decision",
            )
        return ("accepted_reviewer_decision", 1, "none", "materialize_accepted_official_profile_url_fact")
    if reviewer_decision.startswith("reject_"):
        return ("rejected_by_reviewer", 0, reviewer_decision, "retain_rejection_for_audit")
    return (
        "deferred_needs_more_evidence",
        0,
        "reviewer_requested_more_evidence",
        "collect_additional_profile_identity_or_context_evidence",
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
                "accepted_profile_url_requires": [
                    "matching profile_fingerprint",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                    "reviewer_decision=accept_official_profile_url",
                ],
                "roster_truth_policy": ROSTER_TRUTH_STATUS,
            },
        }
        row = {
            "reviewer_decision_key": item["reviewer_decision_key"],
            "profile_workbench_key": item["profile_workbench_key"],
            "person_key": item["person_key"],
            "display_name": item["display_name"],
            "role": item["role"],
            "program_name": item["program_name"],
            "candidate_url": item["candidate_url"],
            "reviewer_decision": (decision or {}).get("reviewer_decision", "pending") or "pending",
            "decision_status": status,
            "accepted_official_profile_url": accepted,
            "decision_blocker": blocker,
            "profile_fingerprint": item["profile_fingerprint"],
            "decision_profile_fingerprint": (decision or {}).get("profile_fingerprint", ""),
            "person_identity_confirmed": as_int((decision or {}).get("person_identity_confirmed")),
            "official_source_confirmed": as_int((decision or {}).get("official_source_confirmed")),
            "profile_context_confirmed": as_int((decision or {}).get("profile_context_confirmed")),
            "source_hash_confirmed": as_int((decision or {}).get("source_hash_confirmed")),
            "display_safety_confirmed": as_int((decision or {}).get("display_safety_confirmed")),
            "reviewer_name": (decision or {}).get("reviewer_name", ""),
            "decided_at": (decision or {}).get("decided_at", ""),
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": audited_at,
        }
        rows.append({field: row[field] for field in AUDIT_FIELDS})
    return rows


def accepted_key(audit_row: dict) -> str:
    return "accepted_official_profile_url_" + sha256_text(dumps([audit_row["person_key"], audit_row["candidate_url"]]))[:20]


def queue_by_key(queue: list[dict]) -> dict[str, dict]:
    return {row["reviewer_decision_key"]: row for row in queue}


def build_accepted_facts(queue: list[dict], audit: list[dict], materialized_at: str) -> list[dict]:
    queue_index = queue_by_key(queue)
    facts = []
    for row in audit:
        if as_int(row.get("accepted_official_profile_url")) != 1:
            continue
        item = queue_index[row["reviewer_decision_key"]]
        evidence = {
            "audit_row": {field: row.get(field, "") for field in AUDIT_FIELDS if field != "evidence_json"},
            "queue_row": {field: item.get(field, "") for field in QUEUE_FIELDS if field != "evidence_json"},
            "roster_truth_policy": ROSTER_TRUTH_STATUS,
        }
        fact = {
            "accepted_profile_key": accepted_key(row),
            "reviewer_decision_key": row["reviewer_decision_key"],
            "profile_workbench_key": row["profile_workbench_key"],
            "person_key": row["person_key"],
            "display_name": row["display_name"],
            "role": row["role"],
            "program_name": row["program_name"],
            "profile_url": row["candidate_url"],
            "profile_title": item["candidate_title"],
            "source_domain": item["candidate_domain"],
            "source_sha256": item["source_sha256"],
            "profile_fingerprint": row["profile_fingerprint"],
            "accepted_by": row["reviewer_name"],
            "accepted_at": row["decided_at"],
            "display_safety_status": DISPLAY_SAFETY_STATUS,
            "roster_truth_status": ROSTER_TRUTH_STATUS,
            "evidence_json": dumps(evidence),
            "materialized_at": materialized_at,
        }
        facts.append({field: fact[field] for field in ACCEPTED_FIELDS})
    return facts


def write_db_table(conn: sqlite3.Connection, table: str, rows: list[dict], fields: list[str]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    field_sql = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    conn.executemany(f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(queue: list[dict], audit: list[dict], accepted: list[dict], generated_at: str) -> None:
    by_status = Counter(row["decision_status"] for row in audit)
    payload = {
        "generated_at": generated_at,
        "queue_rows": len(queue),
        "manual_decision_rows": len(read_csv(MANUAL_DECISIONS_CSV)),
        "audit_rows": len(audit),
        "accepted_official_profile_url_rows": len(accepted),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_reviewer_decision": dict(sorted(Counter(row["reviewer_decision"] for row in audit).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in queue).items())),
        "acceptance_policy": (
            "Accepted official profile URL facts require an explicit reviewer decision, matching profile fingerprint, "
            "and confirmation of identity, official source ownership, profile context, source hash, and display safety. "
            "They do not mutate current roster truth."
        ),
        "manual_decision_csv": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
        "queue_csv": str(QUEUE_CSV.relative_to(ROOT)),
        "audit_csv": str(AUDIT_CSV.relative_to(ROOT)),
        "accepted_facts_csv": str(ACCEPTED_CSV.relative_to(ROOT)),
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    with conn:
        replay_reobservations(conn)
    workbench_rows = read_workbench(conn)
    candidate_index = read_candidate_index(conn)
    queue = build_queue(workbench_rows, candidate_index, read_reobservations(conn), generated_at)
    audit = build_audit(queue, generated_at)
    accepted = build_accepted_facts(queue, audit, generated_at)

    write_csv(QUEUE_CSV, queue, QUEUE_FIELDS)
    write_json(QUEUE_JSON, queue)
    ensure_manual_decisions_file()
    write_csv(AUDIT_CSV, audit, AUDIT_FIELDS)
    write_json(AUDIT_JSON, audit)
    write_csv(ACCEPTED_CSV, accepted, ACCEPTED_FIELDS)
    write_json(ACCEPTED_JSON, accepted)
    with conn:
        write_db_table(conn, "official_profile_reviewer_decisions", read_csv(MANUAL_DECISIONS_CSV), MANUAL_FIELDS)
        write_db_table(conn, "official_profile_reviewer_decision_queue", queue, QUEUE_FIELDS)
        write_db_table(conn, "official_profile_reviewer_decision_audit", audit, AUDIT_FIELDS)
        write_db_table(conn, "accepted_official_profile_url_facts", accepted, ACCEPTED_FIELDS)
    conn.close()
    write_summary(queue, audit, accepted, generated_at)
    print(dumps({"queue_rows": len(queue), "audit_rows": len(audit), "accepted_official_profile_url_rows": len(accepted)}))


if __name__ == "__main__":
    main()
