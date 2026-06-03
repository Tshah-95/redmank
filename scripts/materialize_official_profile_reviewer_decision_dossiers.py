#!/usr/bin/env python3
"""Materialize reviewer decision dossiers for official profile URL candidates."""

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

CSV_PATH = ARTIFACTS / "official_profile_reviewer_decision_dossiers.csv"
JSON_PATH = ARTIFACTS / "official_profile_reviewer_decision_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "official_profile_reviewer_decision_dossier_summary.json"

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

FIELDS = [
    "dossier_key",
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
    "decision_status",
    "decision_blocker",
    "reobservation_status",
    "reobservation_evidence_strength",
    "reobserved_at",
    "reobserved_title",
    "canonical_url",
    "name_present",
    "program_context_present",
    "role_or_training_context_present",
    "official_domain_confirmed",
    "profile_path_confirmed",
    "display_safety_status",
    "allowed_decisions",
    "required_confirmation_fields",
    "manual_decision_template_json",
    "required_reviewer_action",
    "recommended_next_action",
    "acceptance_boundary",
    "profile_fingerprint",
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
               a.accepted_official_profile_url,
               a.recommended_next_action AS audit_recommended_next_action
        FROM official_profile_reviewer_decision_queue q
        LEFT JOIN official_profile_reviewer_decision_audit a
          ON a.reviewer_decision_key = q.reviewer_decision_key
        ORDER BY
          CASE COALESCE(a.decision_status, '')
            WHEN 'pending_reviewer_decision' THEN 0
            WHEN 'deferred_needs_more_evidence' THEN 1
            WHEN 'invalid_acceptance_missing_confirmations' THEN 2
            WHEN 'invalid_reviewer_decision' THEN 3
            WHEN 'stale_decision_evidence_mismatch' THEN 4
            WHEN 'accepted_reviewer_decision' THEN 5
            ELSE 6
          END,
          q.role,
          q.display_name,
          q.profile_workbench_key
        """,
    )


def dossier_key(row: dict) -> str:
    return "official_profile_reviewer_decision_dossier_" + sha256_text(row["reviewer_decision_key"])[:20]


def manual_decision_template(row: dict) -> dict:
    template = {
        "reviewer_decision_key": row.get("reviewer_decision_key") or "",
        "profile_workbench_key": row.get("profile_workbench_key") or "",
        "profile_fingerprint": row.get("profile_fingerprint") or "",
        "reviewer_decision": "",
        "reviewer_name": "",
        "decided_at": "",
        "decision_notes": "",
    }
    for field in CONFIRMATION_FIELDS:
        template[field] = 0
    return template


def acceptance_boundary(row: dict, reobservation: dict) -> str:
    status = reobservation.get("reobservation_status") or ""
    if status == "fresh_source_resolved_to_generic_academic_departments_page":
        return (
            "Do not accept this profile URL until the candidate is reprobed or replaced; current reobservation "
            "resolves to a generic academic-departments page rather than a person-specific profile."
        )
    return (
        "Acceptance requires reviewer_decision=accept_official_profile_url, the current profile_fingerprint, "
        "same-person identity, official source ownership, profile context, source hash, and display-safety "
        "confirmations. Accepted profile URLs do not mutate current roster truth."
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
            "profile_workbench_key": item.get("profile_workbench_key") or "",
            "person_key": item.get("person_key") or "",
            "display_name": item.get("display_name") or "",
            "role": item.get("role") or "",
            "program_name": item.get("program_name") or "",
            "task_key": item.get("task_key") or "",
            "candidate_url": item.get("candidate_url") or "",
            "candidate_title": item.get("candidate_title") or "",
            "candidate_domain": item.get("candidate_domain") or "",
            "candidate_confidence": as_float(item.get("candidate_confidence")),
            "candidate_http_status": item.get("candidate_http_status") or "",
            "candidate_features": item.get("candidate_features") or "",
            "source_sha256": item.get("source_sha256") or "",
            "queue_status": item.get("queue_status") or "",
            "decision_status": decision_status,
            "decision_blocker": decision_blocker,
            "reobservation_status": reobservation.get("reobservation_status") or "",
            "reobservation_evidence_strength": as_int(reobservation.get("evidence_strength")),
            "reobserved_at": reobservation.get("reobserved_at") or "",
            "reobserved_title": reobservation.get("title") or "",
            "canonical_url": reobservation.get("canonical_url") or "",
            "name_present": as_int(reobservation.get("name_present")),
            "program_context_present": as_int(reobservation.get("program_context_present")),
            "role_or_training_context_present": as_int(reobservation.get("role_or_training_context_present")),
            "official_domain_confirmed": as_int(reobservation.get("official_domain_confirmed")),
            "profile_path_confirmed": as_int(reobservation.get("profile_path_confirmed")),
            "display_safety_status": item.get("display_safety_status") or "",
            "allowed_decisions": item.get("allowed_decisions") or "; ".join(ALLOWED_DECISIONS),
            "required_confirmation_fields": item.get("required_confirmation_fields") or "; ".join(CONFIRMATION_FIELDS),
            "manual_decision_template_json": dumps(manual_decision_template(item)),
            "required_reviewer_action": item.get("required_reviewer_action") or "",
            "recommended_next_action": item.get("audit_recommended_next_action")
            or item.get("recommended_next_action")
            or "",
            "acceptance_boundary": acceptance_boundary(item, reobservation),
            "profile_fingerprint": item.get("profile_fingerprint") or "",
            "evidence_json": dumps(
                {
                    "queue_row": {
                        "reviewer_decision_key": item.get("reviewer_decision_key"),
                        "profile_workbench_key": item.get("profile_workbench_key"),
                        "person_key": item.get("person_key"),
                        "display_name": item.get("display_name"),
                        "role": item.get("role"),
                        "program_name": item.get("program_name"),
                        "candidate_url": item.get("candidate_url"),
                        "profile_fingerprint": item.get("profile_fingerprint"),
                    },
                    "decision_audit": {
                        "decision_status": decision_status,
                        "decision_blocker": decision_blocker,
                        "reviewer_decision": item.get("reviewer_decision") or "pending",
                        "accepted_official_profile_url": as_int(item.get("accepted_official_profile_url")),
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
    conn.execute("DELETE FROM official_profile_reviewer_decision_dossiers")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if db_row.get("candidate_http_status") == "":
            db_row["candidate_http_status"] = None
        db_rows.append(db_row)
    conn.executemany(
        f"INSERT OR REPLACE INTO official_profile_reviewer_decision_dossiers ({field_sql}) VALUES ({placeholders})",
        db_rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_status = Counter(row["decision_status"] for row in rows)
    by_reobservation = Counter(row["reobservation_status"] for row in rows)
    by_role = Counter(row["role"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "dossier_rows": len(rows),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "manual_decision_template_rows": sum(1 for row in rows if "profile_fingerprint" in row["manual_decision_template_json"]),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_reobservation_status": dict(sorted(by_reobservation.items())),
        "by_role": dict(sorted(by_role.items())),
        "acceptance_policy": (
            "Dossiers are non-mutating. Accepted official profile URL facts still require explicit reviewer "
            "acceptance against the current profile_fingerprint and all required confirmation fields."
        ),
        "roster_truth_policy": "Accepted profile URLs do not mutate current roster truth.",
        "dossier_csv": str(CSV_PATH.relative_to(ROOT)),
        "manual_decision_csv": "artifacts/data/official_profile_reviewer_decisions.csv",
        "accepted_facts_csv": "artifacts/data/accepted_official_profile_url_facts.csv",
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
    print(dumps({"official_profile_reviewer_decision_dossiers": len(rows), "generated_at": generated_at}))


if __name__ == "__main__":
    main()
