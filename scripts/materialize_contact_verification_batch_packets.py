#!/usr/bin/env python3
"""Materialize contact-level packets for contact verification batches."""

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

BATCH_CSV = ARTIFACTS / "contact_verification_batches.csv"
DOSSIER_CSV = ARTIFACTS / "contact_verification_reviewer_decision_dossiers.csv"
CSV_PATH = ARTIFACTS / "contact_verification_batch_packets.csv"
JSON_PATH = ARTIFACTS / "contact_verification_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "contact_verification_batch_packet_summary.json"

MAX_CONTACTS_PER_BATCH = 50

FIELDS = [
    "contact_verification_batch_packet_key",
    "contact_verification_batch_key",
    "execution_order",
    "packet_order",
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
    "packet_status",
    "support_status",
    "required_confirmation_fields",
    "required_reviewer_action",
    "recommended_next_action",
    "acceptance_boundary",
    "target_artifact",
    "allowed_decisions",
    "manual_decision_template_json",
    "dossier_evidence_json",
    "batch_evidence_json",
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


def stable_key(*parts: object) -> str:
    return sha256_text(dumps(parts))[:20]


def batch_key(parts: tuple[object, ...]) -> str:
    return "contact_verification_batch_" + sha256_text(dumps(parts))[:20]


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {row["contact_verification_batch_packet_key"]: row for row in read_csv(CSV_PATH)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["contact_verification_batch_packet_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def dossier_sort_key(row: dict) -> tuple:
    return (
        row.get("display_name") or "",
        row.get("contact_type") or "",
        row.get("dossier_key") or "",
    )


def group_sort_key(row: dict) -> tuple:
    return (
        0 if row.get("queue_status") == "domain_review_required_before_decision" else 1 if row.get("queue_status") == "ready_for_reviewer_verification" else 2,
        0 if row.get("reobservation_status") == "fresh_official_same_value_reobserved" else 1 if row.get("reobservation_status") == "fresh_official_value_absent" else 2,
        row.get("role") or "",
        row.get("display_name") or "",
        row.get("dossier_key") or "",
    )


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


def packet_status(batch_status_value: str) -> str:
    return {
        "blocked_before_contact_review": "blocked_contact_verification_packet",
        "same_value_contact_review_ready": "same_value_contact_verification_packet",
        "missing_value_contact_review_ready": "missing_value_contact_verification_packet",
    }.get(batch_status_value, "contact_verification_review_packet")


def support_status(row: dict, batch_status_value: str) -> str:
    if batch_status_value == "blocked_before_contact_review":
        return "blocked_before_contact_review"
    if row.get("reobservation_status") == "fresh_official_same_value_reobserved":
        return "ready_for_same_value_contact_review"
    if row.get("reobservation_status") == "fresh_official_value_absent":
        return "ready_for_missing_value_contact_review"
    return "ready_for_contact_review"


def batch_lookup(dossiers: list[dict]) -> dict[str, str]:
    grouped: dict[tuple[str, str, str, str, str, str], list[dict]] = defaultdict(list)
    for row in sorted(dossiers, key=group_sort_key):
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

    output: dict[str, str] = {}
    for (queue_status, lane, reobs, role, domain, source_class), rows in grouped.items():
        ordered = sorted(rows, key=dossier_sort_key)
        for chunk_index, offset in enumerate(range(0, len(ordered), MAX_CONTACTS_PER_BATCH), start=1):
            chunk = ordered[offset : offset + MAX_CONTACTS_PER_BATCH]
            keys = [item.get("dossier_key") for item in chunk]
            key = batch_key((queue_status, lane, reobs, role, domain, source_class, chunk_index, keys))
            for item in chunk:
                output[item.get("dossier_key") or ""] = key
    return output


def build_rows(generated_at: str) -> list[dict]:
    existing = read_existing()
    batches = read_csv(BATCH_CSV)
    dossiers = read_csv(DOSSIER_CSV)
    batch_by_key = {row["contact_verification_batch_key"]: row for row in batches}
    dossier_to_batch = batch_lookup(dossiers)

    missing_batch_keys = sorted(set(dossier_to_batch.values()) - set(batch_by_key))
    if missing_batch_keys:
        raise SystemExit(f"missing contact batch rows for {len(missing_batch_keys)} computed keys")

    output = []
    packet_orders: Counter[str] = Counter()
    for dossier in sorted(dossiers, key=group_sort_key):
        dossier_key = dossier.get("dossier_key") or ""
        batch_id = dossier_to_batch.get(dossier_key)
        if not batch_id:
            raise SystemExit(f"missing contact batch membership for dossier {dossier_key}")
        batch = batch_by_key[batch_id]
        packet_orders[batch_id] += 1
        status = packet_status(batch.get("batch_status") or "")
        evidence = {
            "contact_verification_batch_key": batch_id,
            "dossier_key": dossier_key,
            "reviewer_decision_key": dossier.get("reviewer_decision_key"),
            "contact_contract_key": dossier.get("contact_contract_key"),
            "queue_status": dossier.get("queue_status"),
            "reobservation_status": dossier.get("reobservation_status"),
            "accepted_contact_fact_requires": [
                "contact_verification_reviewer_decisions.csv row",
                "matching contact_fingerprint",
                "current official source reobservation URL/date",
                "identity, same-value, domain, and scope confirmations",
            ],
            "non_mutating_policy": {
                "packet_role": "row-level evidence for a bounded contact verification batch",
                "does_not_imply": "outreach_permission",
            },
        }
        row = {
            "contact_verification_batch_packet_key": "contact_verification_batch_packet_" + stable_key(batch_id, dossier_key),
            "contact_verification_batch_key": batch_id,
            "execution_order": batch.get("execution_order") or "0",
            "packet_order": packet_orders[batch_id],
            "dossier_key": dossier_key,
            "reviewer_decision_key": dossier.get("reviewer_decision_key") or "",
            "contact_contract_key": dossier.get("contact_contract_key") or "",
            "contact_assurance_key": dossier.get("contact_assurance_key") or "",
            "contact_key": dossier.get("contact_key") or "",
            "person_key": dossier.get("person_key") or "",
            "display_name": dossier.get("display_name") or "",
            "role": dossier.get("role") or "",
            "contact_type": dossier.get("contact_type") or "",
            "normalized_contact_value": dossier.get("normalized_contact_value") or "",
            "contact_domain": dossier.get("contact_domain") or "",
            "canonical_contact_domain": dossier.get("canonical_contact_domain") or "",
            "domain_status": dossier.get("domain_status") or "",
            "source_key": dossier.get("source_key") or "",
            "source_url": dossier.get("source_url") or "",
            "source_type": dossier.get("source_type") or "",
            "source_assurance_class": dossier.get("source_assurance_class") or "",
            "verification_lane": dossier.get("verification_lane") or "",
            "queue_status": dossier.get("queue_status") or "",
            "decision_status": dossier.get("decision_status") or "",
            "decision_blocker": dossier.get("decision_blocker") or "",
            "verification_confidence": as_float(dossier.get("verification_confidence")),
            "operational_use_status": dossier.get("operational_use_status") or "",
            "reobservation_status": dossier.get("reobservation_status") or "",
            "reobserved_same_value": as_int(dossier.get("reobserved_same_value")),
            "reobserved_at": dossier.get("reobserved_at") or "",
            "reobservation_evidence_strength": as_int(dossier.get("reobservation_evidence_strength")),
            "packet_status": status,
            "support_status": support_status(dossier, batch.get("batch_status") or ""),
            "required_confirmation_fields": dossier.get("required_confirmation_fields") or batch.get("required_confirmation_fields") or "",
            "required_reviewer_action": dossier.get("required_reviewer_action") or "",
            "recommended_next_action": dossier.get("recommended_next_action") or batch.get("recommended_operator_action") or "",
            "acceptance_boundary": dossier.get("acceptance_boundary") or batch.get("acceptance_boundary") or "",
            "target_artifact": batch.get("target_artifact") or "artifacts/data/contact_verification_reviewer_decisions.csv",
            "allowed_decisions": dossier.get("allowed_decisions") or "",
            "manual_decision_template_json": dumps(parse_json(dossier.get("manual_decision_template_json"), {})),
            "dossier_evidence_json": dumps(parse_json(dossier.get("evidence_json"), {})),
            "batch_evidence_json": dumps(parse_json(batch.get("evidence_json"), {})),
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        output.append({field: row[field] for field in FIELDS})

    expected_counts = Counter(dossier_to_batch.values())
    actual_counts = Counter(row["contact_verification_batch_key"] for row in output)
    mismatches = [
        key
        for key, batch in batch_by_key.items()
        if expected_counts[key] != as_int(batch.get("contact_count")) or actual_counts[key] != as_int(batch.get("contact_count"))
    ]
    if mismatches:
        raise SystemExit(f"contact batch packet count mismatch for {len(mismatches)} batches")

    output.sort(key=lambda row: (as_int(row["execution_order"]), as_int(row["packet_order"]), row["dossier_key"]))
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DELETE FROM contact_verification_batch_packets")
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO contact_verification_batch_packets ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "batch_rows": len({row["contact_verification_batch_key"] for row in rows}),
        "contact_count": len({row["contact_key"] for row in rows if row["contact_key"]}),
        "person_count": len({row["person_key"] or row["display_name"] for row in rows if row["display_name"]}),
        "same_value_reobserved_count": sum(as_int(row["reobserved_same_value"]) for row in rows),
        "value_absent_count": sum(1 for row in rows if row["reobservation_status"] == "fresh_official_value_absent"),
        "pending_decision_count": sum(1 for row in rows if row["decision_status"] == "pending_reviewer_decision"),
        "blocked_packet_count": sum(1 for row in rows if row["support_status"] == "blocked_before_contact_review"),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_reobservation_status": dict(sorted(Counter(row["reobservation_status"] for row in rows).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "top_packets": [
            {
                "execution_order": row["execution_order"],
                "packet_order": row["packet_order"],
                "display_name": row["display_name"],
                "role": row["role"],
                "contact_type": row["contact_type"],
                "canonical_contact_domain": row["canonical_contact_domain"],
                "support_status": row["support_status"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Contact verification batch packets are non-mutating row-level evidence. Accepted contact facts still require explicit reviewer decisions with current fingerprints and confirmation fields.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    rows = build_rows(generated_at)
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    conn = sqlite3.connect(args.db)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"contact_verification_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
