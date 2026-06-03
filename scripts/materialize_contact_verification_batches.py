#!/usr/bin/env python3
"""Materialize bounded reviewer batches for public contact verification dossiers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "contact_verification_batches.csv"
JSON_PATH = ARTIFACTS / "contact_verification_batches.json"
SUMMARY_PATH = ARTIFACTS / "contact_verification_batch_summary.json"

MAX_CONTACTS_PER_BATCH = 50

FIELDS = [
    "contact_verification_batch_key",
    "execution_order",
    "queue_status",
    "verification_lane",
    "reobservation_status",
    "role",
    "canonical_contact_domain",
    "source_assurance_class",
    "batch_status",
    "ready_to_review",
    "contact_count",
    "person_count",
    "same_value_reobserved_count",
    "value_absent_count",
    "pending_decision_count",
    "not_ready_count",
    "domain_review_count",
    "min_verification_confidence",
    "max_verification_confidence",
    "contact_type_counts_json",
    "source_key_counts_json",
    "domain_status_counts_json",
    "top_display_names",
    "top_source_urls",
    "required_confirmation_fields",
    "recommended_operator_action",
    "review_instructions",
    "acceptance_boundary",
    "target_artifact",
    "top_dossiers_json",
    "evidence_json",
    "generated_at",
]

csv.field_size_limit(sys.maxsize)


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


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["contact_verification_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["contact_verification_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def batch_key(parts: tuple[object, ...]) -> str:
    return "contact_verification_batch_" + sha256_text(dumps(parts))[:20]


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def batch_status(rows: list[dict], queue_status: str, reobservation_status: str) -> str:
    if not rows:
        return "empty_batch"
    if queue_status != "ready_for_reviewer_verification":
        return "blocked_before_contact_review"
    if reobservation_status == "fresh_official_same_value_reobserved":
        return "same_value_contact_review_ready"
    if reobservation_status == "fresh_official_value_absent":
        return "missing_value_contact_review_ready"
    return "contact_review_ready"


def recommended_action(status: str) -> str:
    return {
        "same_value_contact_review_ready": "review_same_value_contact_batch_and_record_decisions",
        "missing_value_contact_review_ready": "review_missing_contact_batch_and_reject_or_defer",
        "blocked_before_contact_review": "resolve_contact_domain_or_scope_blocker_before_review",
        "contact_review_ready": "review_contact_batch_and_record_decisions",
    }.get(status, "review_contact_verification_batch")


def review_instructions(status: str) -> str:
    if status == "same_value_contact_review_ready":
        return "Confirm person identity, current official source, same contact value, institutional domain, and person-specific scope before accepting verified contact facts."
    if status == "missing_value_contact_review_ready":
        return "The current official source no longer shows the value; reject as changed/stale or defer only if another current official source is supplied."
    if status == "blocked_before_contact_review":
        return "Resolve domain, source, or contact-scope blockers before any contact can be accepted."
    return "Review public contact candidates only through the reviewer decision and accepted-contact ledgers."


def acceptance_boundary(status: str) -> str:
    if status == "blocked_before_contact_review":
        return "Do not accept contacts from this batch until queue_status is ready_for_reviewer_verification and domain/scope blockers are resolved."
    return (
        "Acceptance requires reviewer_decision=accept_verified_contact, current contact_fingerprint, "
        "current official source URL/date, and all identity/value/domain/scope confirmation fields."
    )


def compact_source_urls(rows: list[dict], limit: int = 8) -> str:
    counts = Counter(row.get("source_url") or "" for row in rows if row.get("source_url"))
    return "; ".join(url for url, _ in counts.most_common(limit))


def top_dossiers(rows: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in rows[:limit]:
        output.append(
            {
                "dossier_key": row.get("dossier_key"),
                "reviewer_decision_key": row.get("reviewer_decision_key"),
                "contact_contract_key": row.get("contact_contract_key"),
                "person_key": row.get("person_key"),
                "display_name": row.get("display_name"),
                "role": row.get("role"),
                "contact_type": row.get("contact_type"),
                "canonical_contact_domain": row.get("canonical_contact_domain"),
                "queue_status": row.get("queue_status"),
                "decision_status": row.get("decision_status"),
                "reobservation_status": row.get("reobservation_status"),
                "reobserved_same_value": as_int(row.get("reobserved_same_value")),
                "verification_confidence": as_float(row.get("verification_confidence")),
                "source_key": row.get("source_key"),
                "source_assurance_class": row.get("source_assurance_class"),
            }
        )
    return output


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    dossiers = sqlite_rows(
        conn,
        """
        SELECT *
        FROM contact_verification_reviewer_decision_dossiers
        ORDER BY
          CASE queue_status
            WHEN 'domain_review_required_before_decision' THEN 0
            WHEN 'ready_for_reviewer_verification' THEN 1
            ELSE 2
          END,
          CASE reobservation_status
            WHEN 'fresh_official_same_value_reobserved' THEN 0
            WHEN 'fresh_official_value_absent' THEN 1
            ELSE 2
          END,
          role,
          display_name,
          dossier_key
        """,
    )
    grouped: dict[tuple[str, str, str, str, str, str], list[dict]] = defaultdict(list)
    for row in dossiers:
        grouped[
            (
                row.get("queue_status") or "",
                row.get("verification_lane") or "",
                row.get("reobservation_status") or "",
                row.get("role") or "",
                row.get("canonical_contact_domain") or "",
                row.get("source_assurance_class") or "",
            )
        ].append(row)

    output = []
    for (queue_status, lane, reobs, role, domain, source_class), rows in grouped.items():
        rows = sorted(
            rows,
            key=lambda item: (
                item.get("display_name") or "",
                item.get("contact_type") or "",
                item.get("dossier_key") or "",
            ),
        )
        for chunk_index, offset in enumerate(range(0, len(rows), MAX_CONTACTS_PER_BATCH), start=1):
            chunk = rows[offset : offset + MAX_CONTACTS_PER_BATCH]
            keys = [item.get("dossier_key") for item in chunk]
            confidences = [as_float(item.get("verification_confidence")) for item in chunk]
            status = batch_status(chunk, queue_status, reobs)
            contact_types = Counter(item.get("contact_type") or "" for item in chunk)
            source_keys = Counter(item.get("source_key") or "" for item in chunk)
            domain_statuses = Counter(item.get("domain_status") or "" for item in chunk)
            required_fields = Counter(item.get("required_confirmation_fields") or "" for item in chunk)
            row = {
                "contact_verification_batch_key": batch_key(
                    (queue_status, lane, reobs, role, domain, source_class, chunk_index, keys)
                ),
                "execution_order": 0,
                "queue_status": queue_status,
                "verification_lane": lane,
                "reobservation_status": reobs,
                "role": role,
                "canonical_contact_domain": domain,
                "source_assurance_class": source_class,
                "batch_status": status,
                "ready_to_review": 1 if status in {"same_value_contact_review_ready", "missing_value_contact_review_ready", "contact_review_ready"} else 0,
                "contact_count": len(chunk),
                "person_count": len({item.get("person_key") or item.get("display_name") for item in chunk}),
                "same_value_reobserved_count": sum(as_int(item.get("reobserved_same_value")) for item in chunk),
                "value_absent_count": sum(1 for item in chunk if item.get("reobservation_status") == "fresh_official_value_absent"),
                "pending_decision_count": sum(1 for item in chunk if item.get("decision_status") == "pending_reviewer_decision"),
                "not_ready_count": sum(1 for item in chunk if item.get("queue_status") != "ready_for_reviewer_verification"),
                "domain_review_count": sum(1 for item in chunk if item.get("domain_status") != "institutional_domain"),
                "min_verification_confidence": min(confidences) if confidences else 0.0,
                "max_verification_confidence": max(confidences) if confidences else 0.0,
                "contact_type_counts_json": dumps(dict(sorted(contact_types.items()))),
                "source_key_counts_json": dumps(dict(source_keys.most_common(10))),
                "domain_status_counts_json": dumps(dict(sorted(domain_statuses.items()))),
                "top_display_names": "; ".join(item.get("display_name") or "" for item in chunk[:12]),
                "top_source_urls": compact_source_urls(chunk),
                "required_confirmation_fields": required_fields.most_common(1)[0][0] if required_fields else "",
                "recommended_operator_action": recommended_action(status),
                "review_instructions": review_instructions(status),
                "acceptance_boundary": acceptance_boundary(status),
                "target_artifact": "artifacts/data/contact_verification_reviewer_decisions.csv",
                "top_dossiers_json": dumps(top_dossiers(chunk)),
                "evidence_json": dumps(
                    {
                        "dossier_keys": keys,
                        "contact_type_counts": dict(sorted(contact_types.items())),
                        "source_key_counts": dict(source_keys.most_common(10)),
                        "domain_status_counts": dict(sorted(domain_statuses.items())),
                        "top_dossiers": top_dossiers(chunk),
                        "policy": {
                            "non_mutating": True,
                            "accepted_contact_fact_requires": [
                                "contact_verification_reviewer_decisions.csv row",
                                "matching contact_fingerprint",
                                "current official source reobservation URL/date",
                                "identity, same-value, domain, and scope confirmations",
                            ],
                            "does_not_imply": "outreach_permission",
                        },
                    }
                ),
                "generated_at": generated_at,
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            output.append({field: row[field] for field in FIELDS})

    output.sort(
        key=lambda item: (
            0 if item["batch_status"] == "blocked_before_contact_review" else 1,
            item["reobservation_status"] != "fresh_official_same_value_reobserved",
            item["role"],
            item["canonical_contact_domain"],
            item["source_assurance_class"],
            item["contact_verification_batch_key"],
        )
    )
    for index, row in enumerate(output, start=1):
        row["execution_order"] = index
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM contact_verification_batch_packets")
    conn.execute("DELETE FROM contact_verification_batches")
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO contact_verification_batches ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "contact_count": sum(as_int(row["contact_count"]) for row in rows),
        "person_count": sum(as_int(row["person_count"]) for row in rows),
        "same_value_reobserved_count": sum(as_int(row["same_value_reobserved_count"]) for row in rows),
        "value_absent_count": sum(as_int(row["value_absent_count"]) for row in rows),
        "pending_decision_count": sum(as_int(row["pending_decision_count"]) for row in rows),
        "not_ready_count": sum(as_int(row["not_ready_count"]) for row in rows),
        "domain_review_count": sum(as_int(row["domain_review_count"]) for row in rows),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_reobservation_status": dict(sorted(Counter(row["reobservation_status"] for row in rows).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "batch_status": row["batch_status"],
                "role": row["role"],
                "canonical_contact_domain": row["canonical_contact_domain"],
                "source_assurance_class": row["source_assurance_class"],
                "contact_count": row["contact_count"],
                "same_value_reobserved_count": row["same_value_reobserved_count"],
                "value_absent_count": row["value_absent_count"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Contact batches are non-mutating reviewer sessions. Accepted contact facts still require explicit reviewer decisions with current fingerprints and confirmations.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = build_rows(conn, generated_at)
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"contact_verification_batches": len(rows)}))


if __name__ == "__main__":
    main()
