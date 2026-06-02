#!/usr/bin/env python3
"""Materialize reviewer decisions for public contact verification contracts."""

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

QUEUE_CSV = ARTIFACTS / "contact_verification_reviewer_decision_queue.csv"
QUEUE_JSON = ARTIFACTS / "contact_verification_reviewer_decision_queue.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "contact_verification_reviewer_decisions.csv"
AUDIT_CSV = ARTIFACTS / "contact_verification_reviewer_decision_audit.csv"
AUDIT_JSON = ARTIFACTS / "contact_verification_reviewer_decision_audit.json"
ACCEPTED_CSV = ARTIFACTS / "accepted_verified_contact_facts.csv"
ACCEPTED_JSON = ARTIFACTS / "accepted_verified_contact_facts.json"
SUMMARY_JSON = ARTIFACTS / "contact_verification_reviewer_decision_summary.json"

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

DISPLAY_SAFETY_STATUS = "accepted_verified_public_contact"
OPERATIONAL_USE_STATUS = "verified_contact_fact"
REQUIRED_REVIEWER_ACTION = (
    "Confirm same-person identity, a current official source, same contact value, institutional domain, "
    "and person-specific contact scope before accepting a verified contact fact."
)

QUEUE_FIELDS = [
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
    "verification_confidence",
    "operational_use_status",
    "queue_status",
    "allowed_decisions",
    "contact_fingerprint",
    "required_confirmation_fields",
    "required_reviewer_action",
    "recommended_next_action",
    "review_question",
    "evidence_json",
    "generated_at",
]

MANUAL_FIELDS = [
    "reviewer_decision_key",
    "contact_contract_key",
    "contact_fingerprint",
    "reviewer_decision",
    "reviewer_name",
    "decided_at",
    "person_identity_confirmed",
    "current_official_source_confirmed",
    "same_contact_value_confirmed",
    "domain_confirmed",
    "contact_scope_confirmed",
    "reobserved_source_url",
    "reobserved_at",
    "decision_notes",
]

AUDIT_FIELDS = [
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
    "source_url",
    "verification_lane",
    "reviewer_decision",
    "decision_status",
    "accepted_verified_contact",
    "decision_blocker",
    "contact_fingerprint",
    "decision_contact_fingerprint",
    "person_identity_confirmed",
    "current_official_source_confirmed",
    "same_contact_value_confirmed",
    "domain_confirmed",
    "contact_scope_confirmed",
    "reobserved_source_url",
    "reobserved_at",
    "reviewer_name",
    "decided_at",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]

ACCEPTED_FIELDS = [
    "accepted_contact_key",
    "reviewer_decision_key",
    "contact_contract_key",
    "contact_key",
    "person_key",
    "display_name",
    "role",
    "contact_type",
    "normalized_contact_value",
    "canonical_contact_domain",
    "source_url",
    "reobserved_source_url",
    "reobserved_at",
    "contact_fingerprint",
    "accepted_by",
    "accepted_at",
    "operational_use_status",
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


def read_contracts(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM contact_verification_contracts
        ORDER BY
          CASE verification_lane
            WHEN 'fresh_official_reobservation_required' THEN 0
            WHEN 'domain_review_before_contact_use' THEN 1
            WHEN 'official_source_low_confidence_review' THEN 2
            ELSE 3
          END,
          role,
          display_name,
          contact_type,
          normalized_contact_value,
          contact_contract_key
        """,
    )


def read_reobservations(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = sqlite_rows(
        conn,
        """
        SELECT *
        FROM contact_reobservation_audit
        ORDER BY contact_contract_key, reobserved_at DESC, evidence_strength DESC
        """,
    )
    latest = {}
    for row in rows:
        latest.setdefault(row["contact_contract_key"], row)
    return latest


def contact_fingerprint(row: dict) -> str:
    stable = {
        "contact_contract_key": row.get("contact_contract_key"),
        "contact_assurance_key": row.get("contact_assurance_key"),
        "contact_key": row.get("contact_key"),
        "person_key": row.get("person_key"),
        "display_name": row.get("display_name"),
        "role": row.get("role"),
        "contact_type": row.get("contact_type"),
        "normalized_contact_value": row.get("normalized_contact_value"),
        "contact_domain": row.get("contact_domain"),
        "canonical_contact_domain": row.get("canonical_contact_domain"),
        "domain_status": row.get("domain_status"),
        "source_url": row.get("source_url"),
        "source_type": row.get("source_type"),
        "source_assurance_class": row.get("source_assurance_class"),
        "verification_lane": row.get("verification_lane"),
        "operational_use_status": row.get("operational_use_status"),
        "stale_after_date": row.get("stale_after_date"),
    }
    return sha256_text(dumps(stable))


def decision_key(row: dict) -> str:
    return f"contact_verification_reviewer_decision_{sha256_text(row['contact_contract_key'])[:20]}"


def queue_status(row: dict) -> str:
    lane = row.get("verification_lane") or ""
    if lane == "fresh_official_reobservation_required":
        return "ready_for_reviewer_verification"
    if lane == "domain_review_before_contact_use":
        return "domain_review_required_before_decision"
    if lane in {"official_source_low_confidence_review", "public_source_reverification_required"}:
        return "source_or_scope_review_required_before_decision"
    return "not_ready_for_reviewer_decision"


def recommended_action(status: str, reobservation: dict | None = None) -> str:
    if (
        status == "ready_for_reviewer_verification"
        and reobservation
        and str(reobservation.get("reobserved_same_value") or "0") == "1"
        and reobservation.get("reobservation_status") == "fresh_official_same_value_reobserved"
    ):
        return "record_accept_reject_or_needs_more_evidence_decision_using_fresh_reobservation"
    if status == "ready_for_reviewer_verification":
        return "record_accept_reject_or_needs_more_evidence_decision"
    if status == "domain_review_required_before_decision":
        return "resolve_domain_anomaly_before_contact_acceptance"
    return "collect_current_official_source_or_scope_evidence"


def review_question(row: dict) -> str:
    return (
        f"Does a current official Penn source verify {row.get('display_name') or 'this person'} has this "
        f"{row.get('contact_type') or 'contact'} value for person-specific use?"
    )


def build_queue(rows: list[dict], reobservations: dict[str, dict], generated_at: str) -> list[dict]:
    queue = []
    for item in rows:
        fingerprint = contact_fingerprint(item)
        status = queue_status(item)
        reobservation = reobservations.get(item["contact_contract_key"])
        evidence = {
            "contact_contract": {
                "contact_contract_key": item.get("contact_contract_key"),
                "contact_assurance_key": item.get("contact_assurance_key"),
                "contact_key": item.get("contact_key"),
                "person_key": item.get("person_key"),
                "display_name": item.get("display_name"),
                "role": item.get("role"),
                "contact_type": item.get("contact_type"),
                "normalized_contact_value": item.get("normalized_contact_value"),
                "domain_status": item.get("domain_status"),
                "canonical_contact_domain": item.get("canonical_contact_domain"),
                "source_url": item.get("source_url"),
                "source_type": item.get("source_type"),
                "source_assurance_class": item.get("source_assurance_class"),
                "verification_lane": item.get("verification_lane"),
                "operational_use_status": item.get("operational_use_status"),
                "evidence_required_to_verify": item.get("evidence_required_to_verify"),
                "evidence_required_to_reject": item.get("evidence_required_to_reject"),
                "review_trigger_json": item.get("review_trigger_json"),
            },
            "current_source_reobservation": {
                "contact_reobservation_key": (reobservation or {}).get("contact_reobservation_key", ""),
                "reobservation_status": (reobservation or {}).get("reobservation_status", ""),
                "reobserved_same_value": (reobservation or {}).get("reobserved_same_value", ""),
                "evidence_strength": (reobservation or {}).get("evidence_strength", ""),
                "source_hash": (reobservation or {}).get("source_hash", ""),
                "http_status": (reobservation or {}).get("http_status", ""),
                "reobserved_at": (reobservation or {}).get("reobserved_at", ""),
                "match_context": (reobservation or {}).get("match_context", ""),
            },
            "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
            "decision_policy": {
                "accepted_contact_requires": [
                    "reviewer_decision=accept_verified_contact",
                    "contact_fingerprint matches the current queue fingerprint",
                    "queue_status=ready_for_reviewer_verification",
                    "reobserved_source_url is present",
                    "reobserved_at is present",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                ],
                "allowed_decisions": ALLOWED_DECISIONS,
                "mutation_policy": (
                    "Accepted contact facts are verified public contact facts, but they do not overwrite "
                    "raw person_contacts candidates or imply outreach permission."
                ),
            },
        }
        row = {
            "reviewer_decision_key": decision_key(item),
            "contact_contract_key": item["contact_contract_key"],
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
            "verification_confidence": item.get("verification_confidence") or 0,
            "operational_use_status": item.get("operational_use_status") or "",
            "queue_status": status,
            "allowed_decisions": "; ".join(ALLOWED_DECISIONS),
            "contact_fingerprint": fingerprint,
            "required_confirmation_fields": "; ".join(CONFIRMATION_FIELDS),
            "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
            "recommended_next_action": recommended_action(status, reobservation),
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
    if queue_row.get("queue_status") != "ready_for_reviewer_verification":
        return (
            "not_ready_for_reviewer_decision",
            0,
            queue_row.get("queue_status") or "contact_not_ready_for_acceptance",
            recommended_action(queue_row.get("queue_status") or ""),
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
    if decision.get("contact_fingerprint") != queue_row.get("contact_fingerprint"):
        return (
            "stale_decision_evidence_mismatch",
            0,
            "manual_decision_contact_fingerprint_does_not_match_current_contract",
            "re_review_current_contact_contract_and_update_fingerprint",
        )
    if reviewer_decision == "accept_verified_contact":
        missing = [field for field in CONFIRMATION_FIELDS if as_int(decision.get(field)) != 1]
        if not decision.get("reobserved_source_url"):
            missing.append("reobserved_source_url")
        if not decision.get("reobserved_at"):
            missing.append("reobserved_at")
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
            "materialize_verified_contact_fact",
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
        "collect_additional_current_official_contact_evidence",
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
                "contact_contract_key": row.get("contact_contract_key"),
                "contact_key": row.get("contact_key"),
                "person_key": row.get("person_key"),
                "display_name": row.get("display_name"),
                "contact_type": row.get("contact_type"),
                "domain_status": row.get("domain_status"),
                "source_url": row.get("source_url"),
                "verification_lane": row.get("verification_lane"),
                "queue_status": row.get("queue_status"),
                "contact_fingerprint": row.get("contact_fingerprint"),
            },
            "manual_decision": decision or {},
            "decision_policy": {
                "accepted_contact_requires": [
                    "matching contact_fingerprint",
                    "queue_status=ready_for_reviewer_verification",
                    "reobserved_source_url present",
                    "reobserved_at present",
                    *[f"{field}=1" for field in CONFIRMATION_FIELDS],
                    "reviewer_decision=accept_verified_contact",
                ],
            },
        }
        audit = {
            "reviewer_decision_key": row["reviewer_decision_key"],
            "contact_contract_key": row["contact_contract_key"],
            "contact_assurance_key": row["contact_assurance_key"],
            "contact_key": row["contact_key"],
            "person_key": row["person_key"],
            "display_name": row["display_name"],
            "role": row["role"],
            "contact_type": row["contact_type"],
            "normalized_contact_value": row["normalized_contact_value"],
            "contact_domain": row["contact_domain"],
            "canonical_contact_domain": row["canonical_contact_domain"],
            "domain_status": row["domain_status"],
            "source_url": row["source_url"],
            "verification_lane": row["verification_lane"],
            "reviewer_decision": (decision or {}).get("reviewer_decision", "pending"),
            "decision_status": status,
            "accepted_verified_contact": accepted,
            "decision_blocker": blocker,
            "contact_fingerprint": row["contact_fingerprint"],
            "decision_contact_fingerprint": (decision or {}).get("contact_fingerprint", ""),
            "person_identity_confirmed": as_int((decision or {}).get("person_identity_confirmed")),
            "current_official_source_confirmed": as_int((decision or {}).get("current_official_source_confirmed")),
            "same_contact_value_confirmed": as_int((decision or {}).get("same_contact_value_confirmed")),
            "domain_confirmed": as_int((decision or {}).get("domain_confirmed")),
            "contact_scope_confirmed": as_int((decision or {}).get("contact_scope_confirmed")),
            "reobserved_source_url": (decision or {}).get("reobserved_source_url", ""),
            "reobserved_at": (decision or {}).get("reobserved_at", ""),
            "reviewer_name": (decision or {}).get("reviewer_name", ""),
            "decided_at": (decision or {}).get("decided_at", ""),
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": audited_at,
        }
        audits.append({field: audit[field] for field in AUDIT_FIELDS})
    return audits


def accepted_key(row: dict) -> str:
    return f"accepted_verified_contact_{sha256_text(row['reviewer_decision_key'])[:20]}"


def accepted_contacts(queue: list[dict], audits: list[dict], materialized_at: str) -> list[dict]:
    queue_by_key = {row["reviewer_decision_key"]: row for row in queue}
    accepted = []
    for audit in audits:
        if as_int(audit["accepted_verified_contact"]) != 1:
            continue
        queue_row = queue_by_key[audit["reviewer_decision_key"]]
        row = {
            "accepted_contact_key": accepted_key(audit),
            "reviewer_decision_key": audit["reviewer_decision_key"],
            "contact_contract_key": audit["contact_contract_key"],
            "contact_key": audit["contact_key"],
            "person_key": audit["person_key"],
            "display_name": audit["display_name"],
            "role": audit["role"],
            "contact_type": audit["contact_type"],
            "normalized_contact_value": audit["normalized_contact_value"],
            "canonical_contact_domain": audit["canonical_contact_domain"],
            "source_url": audit["source_url"],
            "reobserved_source_url": audit["reobserved_source_url"],
            "reobserved_at": audit["reobserved_at"],
            "contact_fingerprint": audit["contact_fingerprint"],
            "accepted_by": audit["reviewer_name"],
            "accepted_at": audit["decided_at"],
            "operational_use_status": OPERATIONAL_USE_STATUS,
            "display_safety_status": DISPLAY_SAFETY_STATUS,
            "evidence_json": dumps(
                {
                    "decision_audit": {
                        "reviewer_decision_key": audit.get("reviewer_decision_key"),
                        "contact_contract_key": audit.get("contact_contract_key"),
                        "decision_status": audit.get("decision_status"),
                        "accepted_verified_contact": audit.get("accepted_verified_contact"),
                        "contact_fingerprint": audit.get("contact_fingerprint"),
                    },
                    "queue_row": {
                        "contact_key": queue_row.get("contact_key"),
                        "person_key": queue_row.get("person_key"),
                        "display_name": queue_row.get("display_name"),
                        "contact_type": queue_row.get("contact_type"),
                        "domain_status": queue_row.get("domain_status"),
                        "source_url": queue_row.get("source_url"),
                        "verification_lane": queue_row.get("verification_lane"),
                    },
                    "display_policy": (
                        "Verified contact facts remain public-source facts with display/use policy; acceptance "
                        "does not imply outreach permission or private contact discovery."
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
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if "person_key" in db_row and not db_row.get("person_key"):
            db_row["person_key"] = None
        db_rows.append(db_row)
    conn.executemany(f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})", db_rows)


def replay_manual_decisions(conn: sqlite3.Connection) -> None:
    rows = read_csv(MANUAL_DECISIONS_CSV)
    write_db_table(conn, "contact_verification_reviewer_decisions", rows, MANUAL_FIELDS)


def write_summary(queue: list[dict], audits: list[dict], accepted: list[dict], generated_at: str) -> None:
    by_queue = Counter(row["queue_status"] for row in queue)
    by_status = Counter(row["decision_status"] for row in audits)
    by_decision = Counter(row["reviewer_decision"] for row in audits)
    by_lane = Counter(row["verification_lane"] for row in queue)
    by_action = Counter(row["recommended_next_action"] for row in audits)
    payload = {
        "generated_at": generated_at,
        "queue_rows": len(queue),
        "ready_queue_rows": by_queue.get("ready_for_reviewer_verification", 0),
        "domain_review_rows": by_queue.get("domain_review_required_before_decision", 0),
        "manual_decision_rows": len(read_csv(MANUAL_DECISIONS_CSV)),
        "audit_rows": len(audits),
        "accepted_verified_contact_rows": len(accepted),
        "accepted_verified_contact_people": len({row["person_key"] for row in accepted if row.get("person_key")}),
        "pending_reviewer_decision_rows": by_status.get("pending_reviewer_decision", 0),
        "by_queue_status": dict(sorted(by_queue.items())),
        "by_verification_lane": dict(sorted(by_lane.items())),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_reviewer_decision": dict(sorted(by_decision.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "acceptance_policy": (
            "Accepted verified contact facts require explicit reviewer acceptance, a matching contact fingerprint, "
            "a current official reobserved source URL/date, and all required confirmation fields set to 1."
        ),
        "display_policy": "Public contacts are not private contact discovery and do not imply outreach permission.",
        "manual_decision_csv": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
        "queue_csv": str(QUEUE_CSV.relative_to(ROOT)),
        "audit_csv": str(AUDIT_CSV.relative_to(ROOT)),
        "accepted_contacts_csv": str(ACCEPTED_CSV.relative_to(ROOT)),
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    queue = build_queue(read_contracts(conn), read_reobservations(conn), generated_at)
    audits = audit_rows(queue, generated_at)
    accepted = accepted_contacts(queue, audits, generated_at)

    write_csv(QUEUE_CSV, queue, QUEUE_FIELDS)
    write_json(QUEUE_JSON, queue)
    write_csv(AUDIT_CSV, audits, AUDIT_FIELDS)
    write_json(AUDIT_JSON, audits)
    write_csv(ACCEPTED_CSV, accepted, ACCEPTED_FIELDS)
    write_json(ACCEPTED_JSON, accepted)
    with conn:
        replay_manual_decisions(conn)
        write_db_table(conn, "contact_verification_reviewer_decision_queue", queue, QUEUE_FIELDS)
        write_db_table(conn, "contact_verification_reviewer_decision_audit", audits, AUDIT_FIELDS)
        write_db_table(conn, "accepted_verified_contact_facts", accepted, ACCEPTED_FIELDS)
    conn.close()
    write_summary(queue, audits, accepted, generated_at)
    print(dumps({"queue_rows": len(queue), "audit_rows": len(audits), "accepted_verified_contact_rows": len(accepted)}))


if __name__ == "__main__":
    main()
