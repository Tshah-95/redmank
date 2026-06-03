#!/usr/bin/env python3
"""Materialize reviewer decision dossiers for recent-attending trend claims."""

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

CSV_PATH = ARTIFACTS / "attending_trend_reviewer_decision_dossiers.csv"
JSON_PATH = ARTIFACTS / "attending_trend_reviewer_decision_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "attending_trend_reviewer_decision_dossier_summary.json"

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

FIELDS = [
    "dossier_key",
    "reviewer_decision_key",
    "trend_acceptance_key",
    "trend_claim_key",
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "trend_claim_type",
    "queue_status",
    "decision_status",
    "decision_blocker",
    "accepted_trend_fact",
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
    "reviewer_decision",
    "reviewer_name",
    "decided_at",
    "identity_confirmed",
    "endpoint_confirmed",
    "training_line_confirmed",
    "date_window_confirmed",
    "allowed_decisions",
    "required_confirmation_fields",
    "manual_decision_template_json",
    "required_reviewer_action",
    "recommended_next_action",
    "acceptance_boundary",
    "display_safety_status",
    "claim_fingerprint",
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


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


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


def load_rows(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT q.*,
               a.decision_status,
               a.decision_blocker,
               a.reviewer_decision,
               a.accepted_trend_fact,
               a.decision_claim_fingerprint,
               a.identity_confirmed,
               a.endpoint_confirmed,
               a.training_line_confirmed,
               a.date_window_confirmed,
               a.reviewer_name,
               a.decided_at,
               a.recommended_next_action AS audit_recommended_next_action,
               a.evidence_json AS audit_evidence_json,
               ac.acceptance_status,
               ac.acceptance_blocker,
               ac.identity_check_status,
               ac.endpoint_check_status,
               ac.training_line_check_status,
               ac.date_window_check_status,
               ac.evidence_json AS acceptance_evidence_json
        FROM attending_trend_reviewer_decision_queue q
        LEFT JOIN attending_trend_reviewer_decision_audit a
          ON a.reviewer_decision_key = q.reviewer_decision_key
        LEFT JOIN attending_trend_acceptance_audit ac
          ON ac.trend_acceptance_key = q.trend_acceptance_key
        ORDER BY
          CASE COALESCE(a.decision_status, '')
            WHEN 'pending_reviewer_decision' THEN 0
            WHEN 'stale_decision_evidence_mismatch' THEN 1
            WHEN 'invalid_acceptance_missing_confirmations' THEN 2
            WHEN 'invalid_reviewer_decision' THEN 3
            WHEN 'deferred_needs_more_evidence' THEN 4
            WHEN 'rejected_by_reviewer' THEN 5
            WHEN 'accepted_reviewer_decision' THEN 6
            ELSE 7
          END,
          q.training_end_year DESC,
          q.display_name,
          q.reviewer_decision_key
        """,
    )


def dossier_key(row: dict) -> str:
    return "attending_trend_reviewer_decision_dossier_" + sha256_text(row["reviewer_decision_key"])[:20]


def manual_decision_template(row: dict) -> dict:
    template = {
        "reviewer_decision_key": row.get("reviewer_decision_key") or "",
        "trend_acceptance_key": row.get("trend_acceptance_key") or "",
        "trend_claim_key": row.get("trend_claim_key") or "",
        "claim_fingerprint": row.get("claim_fingerprint") or "",
        "reviewer_decision": "",
        "reviewer_name": "",
        "decided_at": "",
        "decision_notes": "",
    }
    for field in CONFIRMATION_FIELDS:
        template[field] = 0
    return template


def acceptance_boundary(row: dict) -> str:
    if row.get("queue_status") == "accepted_fact_already_materialized":
        return (
            "Accepted trend fact already materialized from an explicit reviewer decision. Retain the claim "
            "fingerprint, source URL, bridge candidate key, and confirmation fields for provenance monitoring."
        )
    if row.get("queue_status") != "ready_for_reviewer_decision":
        return (
            "Do not accept this trend claim until queue_status is ready_for_reviewer_decision; resolve the "
            "acceptance blocker or collect stronger endpoint, identity, training-line, or date-window evidence."
        )
    return (
        "Acceptance requires reviewer_decision=accept_trend_fact, the current claim_fingerprint, same-person "
        "identity, current Penn attending endpoint, Penn training line, and ten-year date-window confirmations. "
        "Accepted facts remain non-mutating trend facts and do not rewrite current trainee rosters."
    )


def build_dossiers(rows: list[dict], generated_at: str) -> list[dict]:
    existing = read_existing()
    dossiers = []
    for item in rows:
        decision_status = item.get("decision_status") or "pending_reviewer_decision"
        decision_blocker = item.get("decision_blocker") or "manual_reviewer_decision_missing"
        queue_evidence = parse_json(item.get("evidence_json"), {})
        audit_evidence = parse_json(item.get("audit_evidence_json"), {})
        acceptance_evidence = parse_json(item.get("acceptance_evidence_json"), {})
        row = {
            "dossier_key": dossier_key(item),
            "reviewer_decision_key": item.get("reviewer_decision_key") or "",
            "trend_acceptance_key": item.get("trend_acceptance_key") or "",
            "trend_claim_key": item.get("trend_claim_key") or "",
            "trend_key": item.get("trend_key") or "",
            "event_group_key": item.get("event_group_key") or "",
            "display_name": item.get("display_name") or "",
            "normalized_name": item.get("normalized_name") or "",
            "trend_claim_type": item.get("trend_claim_type") or "",
            "queue_status": item.get("queue_status") or "",
            "decision_status": decision_status,
            "decision_blocker": decision_blocker,
            "accepted_trend_fact": as_int(item.get("accepted_trend_fact")),
            "ten_year_trend_window": item.get("ten_year_trend_window") or "",
            "training_type": item.get("training_type") or "",
            "training_line": item.get("training_line") or "",
            "training_organization": item.get("training_organization") or "",
            "training_start_year": item.get("training_start_year") or "",
            "training_end_year": item.get("training_end_year") or "",
            "source_key": item.get("source_key") or "",
            "source_url": item.get("source_url") or "",
            "source_scope": item.get("source_scope") or "",
            "bridge_candidate_key": item.get("bridge_candidate_key") or "",
            "reviewer_decision": item.get("reviewer_decision") or "pending",
            "reviewer_name": item.get("reviewer_name") or "",
            "decided_at": item.get("decided_at") or "",
            "identity_confirmed": as_int(item.get("identity_confirmed")),
            "endpoint_confirmed": as_int(item.get("endpoint_confirmed")),
            "training_line_confirmed": as_int(item.get("training_line_confirmed")),
            "date_window_confirmed": as_int(item.get("date_window_confirmed")),
            "allowed_decisions": item.get("allowed_decisions") or "; ".join(ALLOWED_DECISIONS),
            "required_confirmation_fields": item.get("required_confirmation_fields") or "; ".join(CONFIRMATION_FIELDS),
            "manual_decision_template_json": dumps(manual_decision_template(item)),
            "required_reviewer_action": item.get("required_reviewer_action") or "",
            "recommended_next_action": item.get("audit_recommended_next_action") or "",
            "acceptance_boundary": acceptance_boundary(item),
            "display_safety_status": item.get("display_safety_status") or "",
            "claim_fingerprint": item.get("claim_fingerprint") or "",
            "evidence_json": dumps(
                {
                    "queue_row": {
                        "reviewer_decision_key": item.get("reviewer_decision_key"),
                        "trend_acceptance_key": item.get("trend_acceptance_key"),
                        "trend_claim_key": item.get("trend_claim_key"),
                        "trend_key": item.get("trend_key"),
                        "display_name": item.get("display_name"),
                        "training_line": item.get("training_line"),
                        "training_end_year": item.get("training_end_year"),
                        "source_url": item.get("source_url"),
                        "bridge_candidate_key": item.get("bridge_candidate_key"),
                        "claim_fingerprint": item.get("claim_fingerprint"),
                    },
                    "decision_audit": {
                        "decision_status": decision_status,
                        "decision_blocker": decision_blocker,
                        "reviewer_decision": item.get("reviewer_decision") or "pending",
                        "decision_claim_fingerprint": item.get("decision_claim_fingerprint") or "",
                        "accepted_trend_fact": as_int(item.get("accepted_trend_fact")),
                    },
                    "acceptance_audit": {
                        "acceptance_status": item.get("acceptance_status"),
                        "acceptance_blocker": item.get("acceptance_blocker"),
                        "identity_check_status": item.get("identity_check_status"),
                        "endpoint_check_status": item.get("endpoint_check_status"),
                        "training_line_check_status": item.get("training_line_check_status"),
                        "date_window_check_status": item.get("date_window_check_status"),
                    },
                    "queue_evidence": queue_evidence,
                    "decision_audit_evidence": audit_evidence,
                    "acceptance_evidence": acceptance_evidence,
                    "manual_decision_template": manual_decision_template(item),
                }
            ),
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        dossiers.append({field: row[field] for field in FIELDS})
    return dossiers


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM attending_trend_reviewer_decision_dossiers")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO attending_trend_reviewer_decision_dossiers ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_status = Counter(row["decision_status"] for row in rows)
    by_queue = Counter(row["queue_status"] for row in rows)
    by_window = Counter(row["ten_year_trend_window"] for row in rows)
    by_source_scope = Counter(row["source_scope"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "dossier_rows": len(rows),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "accepted_reviewer_decision_rows": by_status.get("accepted_reviewer_decision", 0),
        "accepted_trend_fact_rows": sum(1 for row in rows if as_int(row["accepted_trend_fact"]) == 1),
        "manual_decision_template_rows": sum(1 for row in rows if "claim_fingerprint" in row["manual_decision_template_json"]),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_queue_status": dict(sorted(by_queue.items())),
        "by_ten_year_trend_window": dict(sorted(by_window.items())),
        "by_source_scope": dict(sorted(by_source_scope.items())),
        "acceptance_policy": (
            "Dossiers are non-mutating. Accepted recent-attending trend facts require an explicit reviewer "
            "decision with the current claim_fingerprint and all identity, endpoint, training-line, and date-window "
            "confirmations set to 1."
        ),
        "dossier_csv": str(CSV_PATH.relative_to(ROOT)),
        "manual_decision_csv": "artifacts/data/attending_trend_reviewer_decisions.csv",
        "accepted_facts_csv": "artifacts/data/accepted_attending_trend_facts.csv",
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = build_dossiers(load_rows(conn), generated_at)
    write_csv(CSV_PATH, rows)
    write_json(JSON_PATH, rows)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"attending_trend_reviewer_decision_dossiers": len(rows), "generated_at": generated_at}))


if __name__ == "__main__":
    main()
