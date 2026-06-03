#!/usr/bin/env python3
"""Materialize reviewer decision dossiers for public contact verification."""

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

CSV_PATH = ARTIFACTS / "contact_verification_reviewer_decision_dossiers.csv"
JSON_PATH = ARTIFACTS / "contact_verification_reviewer_decision_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "contact_verification_reviewer_decision_dossier_summary.json"

ALLOWED_DECISIONS = [
    "accept_verified_contact",
    "reject_identity_mismatch",
    "reject_contact_value_changed",
    "reject_not_person_specific",
    "reject_domain_or_format_problem",
    "needs_more_evidence",
]

CONFIRMATION_FIELDS = [
    "person_identity_confirmed",
    "current_official_source_confirmed",
    "same_contact_value_confirmed",
    "domain_confirmed",
    "contact_scope_confirmed",
]

FIELDS = [
    "dossier_key",
    "reviewer_decision_key",
    "contact_contract_key",
    "contact_assurance_key",
    "contact_key",
    "person_key",
    "display_name",
    "role",
    "contact_type",
    "normalized_contact_value",
    "contact_domain",
    "canonical_contact_domain",
    "domain_status",
    "source_key",
    "source_url",
    "source_type",
    "source_assurance_class",
    "verification_lane",
    "queue_status",
    "decision_status",
    "decision_blocker",
    "verification_confidence",
    "operational_use_status",
    "reobservation_status",
    "reobserved_same_value",
    "reobserved_at",
    "reobservation_evidence_strength",
    "review_question",
    "allowed_decisions",
    "required_confirmation_fields",
    "manual_decision_template_json",
    "required_reviewer_action",
    "recommended_next_action",
    "acceptance_boundary",
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
               a.accepted_verified_contact,
               a.recommended_next_action AS audit_recommended_next_action
        FROM contact_verification_reviewer_decision_queue q
        LEFT JOIN contact_verification_reviewer_decision_audit a
          ON a.reviewer_decision_key = q.reviewer_decision_key
        ORDER BY
          CASE COALESCE(a.decision_status, '')
            WHEN 'pending_reviewer_decision' THEN 0
            WHEN 'not_ready_for_reviewer_decision' THEN 1
            WHEN 'deferred_needs_more_evidence' THEN 2
            WHEN 'invalid_acceptance_missing_confirmations' THEN 3
            WHEN 'invalid_reviewer_decision' THEN 4
            WHEN 'stale_decision_evidence_mismatch' THEN 5
            WHEN 'accepted_reviewer_decision' THEN 6
            ELSE 7
          END,
          CASE q.queue_status
            WHEN 'ready_for_reviewer_verification' THEN 0
            WHEN 'domain_review_required_before_decision' THEN 1
            ELSE 2
          END,
          q.display_name,
          q.contact_type,
          q.normalized_contact_value,
          q.reviewer_decision_key
        """,
    )


def dossier_key(row: dict) -> str:
    return "contact_verification_reviewer_decision_dossier_" + sha256_text(row["reviewer_decision_key"])[:20]


def manual_decision_template(row: dict) -> dict:
    template = {
        "reviewer_decision_key": row.get("reviewer_decision_key") or "",
        "contact_contract_key": row.get("contact_contract_key") or "",
        "contact_fingerprint": row.get("contact_fingerprint") or "",
        "reviewer_decision": "",
        "reviewer_name": "",
        "decided_at": "",
        "reobserved_source_url": "",
        "reobserved_at": "",
        "decision_notes": "",
    }
    for field in CONFIRMATION_FIELDS:
        template[field] = 0
    return template


def acceptance_boundary(row: dict) -> str:
    if row.get("queue_status") != "ready_for_reviewer_verification":
        return (
            "Do not accept this contact until the queue_status is ready_for_reviewer_verification; "
            "resolve the blocker or collect current official source/scope evidence first."
        )
    return (
        "Acceptance requires reviewer_decision=accept_verified_contact, the current contact_fingerprint, "
        "a reobserved_source_url/date, and all confirmation fields set to 1. Accepted facts do not overwrite "
        "raw person_contacts and do not imply outreach permission."
    )


def build_dossiers(rows: list[dict], generated_at: str) -> list[dict]:
    existing = read_existing()
    dossiers = []
    for item in rows:
        queue_evidence = parse_json(item.get("evidence_json"), {})
        reobservation = queue_evidence.get("current_source_reobservation") or {}
        decision_status = item.get("decision_status") or "pending_reviewer_decision"
        decision_blocker = item.get("decision_blocker") or "manual_reviewer_decision_missing"
        row = {
            "dossier_key": dossier_key(item),
            "reviewer_decision_key": item.get("reviewer_decision_key") or "",
            "contact_contract_key": item.get("contact_contract_key") or "",
            "contact_assurance_key": item.get("contact_assurance_key") or "",
            "contact_key": item.get("contact_key") or "",
            "person_key": item.get("person_key") or "",
            "display_name": item.get("display_name") or "",
            "role": item.get("role") or "",
            "contact_type": item.get("contact_type") or "",
            "normalized_contact_value": item.get("normalized_contact_value") or "",
            "contact_domain": item.get("contact_domain") or "",
            "canonical_contact_domain": item.get("canonical_contact_domain") or "",
            "domain_status": item.get("domain_status") or "",
            "source_key": item.get("source_key") or "",
            "source_url": item.get("source_url") or "",
            "source_type": item.get("source_type") or "",
            "source_assurance_class": item.get("source_assurance_class") or "",
            "verification_lane": item.get("verification_lane") or "",
            "queue_status": item.get("queue_status") or "",
            "decision_status": decision_status,
            "decision_blocker": decision_blocker,
            "verification_confidence": as_float(item.get("verification_confidence")),
            "operational_use_status": item.get("operational_use_status") or "",
            "reobservation_status": reobservation.get("reobservation_status") or "",
            "reobserved_same_value": as_int(reobservation.get("reobserved_same_value")),
            "reobserved_at": reobservation.get("reobserved_at") or "",
            "reobservation_evidence_strength": as_int(reobservation.get("evidence_strength")),
            "review_question": item.get("review_question") or "",
            "allowed_decisions": item.get("allowed_decisions") or "; ".join(ALLOWED_DECISIONS),
            "required_confirmation_fields": item.get("required_confirmation_fields") or "; ".join(CONFIRMATION_FIELDS),
            "manual_decision_template_json": dumps(manual_decision_template(item)),
            "required_reviewer_action": item.get("required_reviewer_action") or "",
            "recommended_next_action": item.get("audit_recommended_next_action")
            or item.get("recommended_next_action")
            or "",
            "acceptance_boundary": acceptance_boundary(item),
            "evidence_json": dumps(
                {
                    "queue_row": {
                        "reviewer_decision_key": item.get("reviewer_decision_key"),
                        "contact_contract_key": item.get("contact_contract_key"),
                        "contact_key": item.get("contact_key"),
                        "person_key": item.get("person_key"),
                        "display_name": item.get("display_name"),
                        "contact_type": item.get("contact_type"),
                        "domain_status": item.get("domain_status"),
                        "source_url": item.get("source_url"),
                        "queue_status": item.get("queue_status"),
                        "contact_fingerprint": item.get("contact_fingerprint"),
                    },
                    "decision_audit": {
                        "decision_status": decision_status,
                        "decision_blocker": decision_blocker,
                        "reviewer_decision": item.get("reviewer_decision") or "pending",
                        "accepted_verified_contact": as_int(item.get("accepted_verified_contact")),
                    },
                    "current_source_reobservation": reobservation,
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
    conn.execute("DELETE FROM contact_verification_reviewer_decision_dossiers")
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if not db_row.get("person_key"):
            db_row["person_key"] = None
        db_rows.append(db_row)
    conn.executemany(
        f"INSERT OR REPLACE INTO contact_verification_reviewer_decision_dossiers ({fields_sql}) VALUES ({placeholders})",
        db_rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_status = Counter(row["decision_status"] for row in rows)
    by_queue = Counter(row["queue_status"] for row in rows)
    by_lane = Counter(row["verification_lane"] for row in rows)
    by_reobservation = Counter(row["reobservation_status"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "dossier_rows": len(rows),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "ready_for_reviewer_verification_rows": by_queue.get("ready_for_reviewer_verification", 0),
        "manual_decision_template_rows": sum(1 for row in rows if "contact_fingerprint" in row["manual_decision_template_json"]),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_queue_status": dict(sorted(by_queue.items())),
        "by_verification_lane": dict(sorted(by_lane.items())),
        "by_reobservation_status": dict(sorted(by_reobservation.items())),
        "acceptance_policy": (
            "Dossiers are non-mutating. A verified contact fact still requires an explicit reviewer decision "
            "with the current contact_fingerprint, current official reobservation URL/date, and all confirmation fields."
        ),
        "dossier_csv": str(CSV_PATH.relative_to(ROOT)),
        "manual_decision_csv": "artifacts/data/contact_verification_reviewer_decisions.csv",
        "accepted_contacts_csv": "artifacts/data/accepted_verified_contact_facts.csv",
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
    print(dumps({"contact_verification_reviewer_decision_dossiers": len(rows), "generated_at": generated_at}))


if __name__ == "__main__":
    main()
