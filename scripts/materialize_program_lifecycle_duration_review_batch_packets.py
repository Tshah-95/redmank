#!/usr/bin/env python3
"""Materialize row-level packets for lifecycle-duration review batches."""

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

BATCH_CSV = ARTIFACTS / "program_lifecycle_duration_review_batches.csv"
CSV_PATH = ARTIFACTS / "program_lifecycle_duration_review_batch_packets.csv"
JSON_PATH = ARTIFACTS / "program_lifecycle_duration_review_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "program_lifecycle_duration_review_batch_packet_summary.json"

MAX_ROWS_PER_BATCH = 25

FIELDS = [
    "duration_review_packet_key",
    "duration_review_batch_key",
    "execution_order",
    "packet_order",
    "reviewer_decision_key",
    "duration_evidence_key",
    "evidence_fingerprint",
    "official_program_key",
    "official_program_type",
    "official_program_name",
    "matched_program_key",
    "matched_program_name",
    "source_url",
    "page_title",
    "explicit_duration_years",
    "duration_confidence",
    "queue_status",
    "decision_status",
    "decision_blocker",
    "duration_evidence_status",
    "batch_status",
    "packet_status",
    "support_status",
    "recommended_operator_action",
    "required_next_evidence",
    "target_artifact",
    "review_question",
    "manual_decision_template_json",
    "review_row_evidence_json",
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
    return "program_lifecycle_duration_review_batch_" + sha256_text(dumps(parts))[:20]


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {row["duration_review_packet_key"]: row for row in read_csv(CSV_PATH)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["duration_review_packet_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def read_unresolved_rows(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT
          q.*,
          a.decision_status,
          a.decision_blocker,
          a.reviewer_decision,
          a.recommended_next_action AS audit_recommended_next_action
        FROM program_lifecycle_duration_reviewer_decision_queue q
        JOIN program_lifecycle_duration_reviewer_decision_audit a
          ON a.reviewer_decision_key = q.reviewer_decision_key
        WHERE a.decision_status NOT IN ('accepted_reviewer_decision', 'rejected_by_reviewer')
        ORDER BY
          CASE q.queue_status
            WHEN 'ready_for_reviewer_decision' THEN 0
            WHEN 'context_review_required_before_decision' THEN 1
            WHEN 'not_ready_for_reviewer_decision' THEN 2
            ELSE 3
          END,
          q.official_program_type,
          q.duration_evidence_status,
          q.official_program_name,
          q.reviewer_decision_key
        """,
    )


def batch_status(queue_status: str) -> str:
    if queue_status == "ready_for_reviewer_decision":
        return "duration_manual_decision_ready"
    if queue_status == "context_review_required_before_decision":
        return "duration_context_review_ready"
    if queue_status == "not_ready_for_reviewer_decision":
        return "duration_evidence_collection_required"
    return "duration_review_repair_required"


def row_sort_key(row: dict) -> tuple:
    return (
        row.get("official_program_name") or "",
        row.get("matched_program_name") or "",
        row.get("reviewer_decision_key") or "",
    )


def batch_lookup(unresolved: list[dict]) -> dict[str, str]:
    grouped: dict[tuple[str, str, str, str, str], list[dict]] = defaultdict(list)
    for row in unresolved:
        key = (
            row.get("queue_status") or "",
            row.get("decision_blocker") or "",
            row.get("official_program_type") or "",
            row.get("duration_evidence_status") or "",
            row.get("audit_recommended_next_action") or row.get("recommended_next_action") or "",
        )
        grouped[key].append(row)

    output: dict[str, str] = {}
    for (queue_status, decision_blocker, program_type, evidence_status, action), group_rows in grouped.items():
        ordered = sorted(group_rows, key=row_sort_key)
        for chunk_index, offset in enumerate(range(0, len(ordered), MAX_ROWS_PER_BATCH), start=1):
            chunk = ordered[offset : offset + MAX_ROWS_PER_BATCH]
            reviewer_keys = [row.get("reviewer_decision_key") for row in chunk]
            key = batch_key((queue_status, decision_blocker, program_type, evidence_status, action, chunk_index, reviewer_keys))
            for row in chunk:
                output[row.get("reviewer_decision_key") or ""] = key
    return output


def manual_decision_template(row: dict) -> dict:
    return {
        "reviewer_decision_key": row.get("reviewer_decision_key"),
        "duration_evidence_key": row.get("duration_evidence_key"),
        "evidence_fingerprint": row.get("evidence_fingerprint"),
        "reviewer_decision": "",
        "reviewer_name": "",
        "decided_at": "",
        "official_program_confirmed": "",
        "duration_phrase_confirmed": "",
        "duration_years_confirmed": "",
        "role_family_confirmed": "",
        "lifecycle_scope_confirmed": "",
        "decision_notes": "",
    }


def packet_status(batch_status_value: str) -> str:
    return {
        "duration_manual_decision_ready": "duration_manual_decision_packet",
        "duration_context_review_ready": "duration_context_review_packet",
        "duration_evidence_collection_required": "duration_evidence_collection_packet",
    }.get(batch_status_value, "duration_review_repair_packet")


def support_status(row: dict, batch_status_value: str) -> str:
    if batch_status_value == "duration_manual_decision_ready":
        return "ready_for_duration_manual_decision"
    if batch_status_value == "duration_context_review_ready":
        return "ready_for_duration_context_review"
    if batch_status_value == "duration_evidence_collection_required":
        return "needs_stronger_duration_source_evidence"
    return row.get("decision_blocker") or row.get("decision_status") or "duration_review_repair_required"


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    batches = read_csv(BATCH_CSV)
    batch_by_key = {row["duration_review_batch_key"]: row for row in batches}
    unresolved = read_unresolved_rows(conn)
    row_to_batch = batch_lookup(unresolved)

    missing_batch_keys = sorted(set(row_to_batch.values()) - set(batch_by_key))
    if missing_batch_keys:
        raise SystemExit(f"missing lifecycle-duration batch rows for {len(missing_batch_keys)} computed keys")

    output = []
    packet_orders: Counter[str] = Counter()
    for item in sorted(unresolved, key=lambda row: (row_to_batch.get(row.get("reviewer_decision_key") or "", ""), row_sort_key(row))):
        reviewer_key = item.get("reviewer_decision_key") or ""
        batch_id = row_to_batch.get(reviewer_key)
        if not batch_id:
            raise SystemExit(f"missing lifecycle-duration batch membership for reviewer decision {reviewer_key}")
        batch = batch_by_key[batch_id]
        packet_orders[batch_id] += 1
        batch_status_value = batch.get("batch_status") or batch_status(item.get("queue_status") or "")
        review_evidence = {
            "reviewer_decision_key": reviewer_key,
            "duration_evidence_key": item.get("duration_evidence_key"),
            "official_program_key": item.get("official_program_key"),
            "matched_program_key": item.get("matched_program_key"),
            "source_url": item.get("source_url"),
            "page_title": item.get("page_title"),
            "explicit_duration_years": item.get("explicit_duration_years"),
            "duration_confidence": item.get("duration_confidence"),
            "duration_evidence_status": item.get("duration_evidence_status"),
            "queue_status": item.get("queue_status"),
            "decision_status": item.get("decision_status"),
            "decision_blocker": item.get("decision_blocker"),
            "reviewer_decision": item.get("reviewer_decision"),
            "review_question": item.get("review_question"),
        }
        boundary = {
            "non_mutating": True,
            "accepted_duration_mapping_requires": [
                "program_lifecycle_duration_reviewer_decisions.csv row",
                "matching evidence_fingerprint",
                "ready_for_reviewer_decision queue status",
                "official program, phrase, years, role family, and lifecycle scope confirmations",
            ],
            "lifecycle_rule_mutation_requires": [
                "accepted_program_lifecycle_duration_mappings row",
                "later config/training_lifecycle_rules.json change citing the accepted mapping",
            ],
        }
        row = {
            "duration_review_packet_key": "program_lifecycle_duration_review_packet_" + stable_key(batch_id, reviewer_key),
            "duration_review_batch_key": batch_id,
            "execution_order": batch.get("execution_order") or "0",
            "packet_order": packet_orders[batch_id],
            "reviewer_decision_key": reviewer_key,
            "duration_evidence_key": item.get("duration_evidence_key") or "",
            "evidence_fingerprint": item.get("evidence_fingerprint") or "",
            "official_program_key": item.get("official_program_key") or "",
            "official_program_type": item.get("official_program_type") or "",
            "official_program_name": item.get("official_program_name") or "",
            "matched_program_key": item.get("matched_program_key") or "",
            "matched_program_name": item.get("matched_program_name") or "",
            "source_url": item.get("source_url") or "",
            "page_title": item.get("page_title") or "",
            "explicit_duration_years": as_int(item.get("explicit_duration_years")),
            "duration_confidence": as_float(item.get("duration_confidence")),
            "queue_status": item.get("queue_status") or "",
            "decision_status": item.get("decision_status") or "",
            "decision_blocker": item.get("decision_blocker") or "",
            "duration_evidence_status": item.get("duration_evidence_status") or "",
            "batch_status": batch_status_value,
            "packet_status": packet_status(batch_status_value),
            "support_status": support_status(item, batch_status_value),
            "recommended_operator_action": batch.get("recommended_operator_action") or "",
            "required_next_evidence": batch.get("required_next_evidence") or "",
            "target_artifact": batch.get("target_artifact") or "artifacts/data/program_lifecycle_duration_reviewer_decisions.csv",
            "review_question": item.get("review_question") or "",
            "manual_decision_template_json": dumps(manual_decision_template(item)),
            "review_row_evidence_json": dumps(review_evidence),
            "batch_evidence_json": batch.get("evidence_json") or "{}",
            "evidence_json": dumps(
                {
                    "duration_review_batch_key": batch_id,
                    "duration_review_packet_key": "program_lifecycle_duration_review_packet_" + stable_key(batch_id, reviewer_key),
                    "review_row": review_evidence,
                    "manual_decision_template": manual_decision_template(item),
                    "acceptance_boundary": boundary,
                    "batch": {
                        "execution_order": batch.get("execution_order"),
                        "batch_status": batch_status_value,
                        "queue_status": batch.get("queue_status"),
                        "duration_evidence_status": batch.get("duration_evidence_status"),
                    },
                }
            ),
            "generated_at": generated_at,
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        output.append({field: row[field] for field in FIELDS})

    output.sort(key=lambda row: (as_int(row["execution_order"]), as_int(row["packet_order"]), row["duration_review_packet_key"]))
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM program_lifecycle_duration_review_batch_packets")
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO program_lifecycle_duration_review_batch_packets ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], batches: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "batch_rows": len(batches),
        "review_row_count": len(rows),
        "distinct_reviewer_decisions": len({row["reviewer_decision_key"] for row in rows}),
        "distinct_duration_evidence": len({row["duration_evidence_key"] for row in rows if row["duration_evidence_key"]}),
        "distinct_official_programs": len({row["official_program_key"] for row in rows if row["official_program_key"]}),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_queue_status": dict(sorted(Counter(row["queue_status"] for row in rows).items())),
        "by_duration_evidence_status": dict(sorted(Counter(row["duration_evidence_status"] for row in rows).items())),
        "top_packets": [
            {
                "execution_order": row["execution_order"],
                "packet_order": row["packet_order"],
                "reviewer_decision_key": row["reviewer_decision_key"],
                "official_program_name": row["official_program_name"],
                "matched_program_name": row["matched_program_name"],
                "queue_status": row["queue_status"],
                "support_status": row["support_status"],
                "source_url": row["source_url"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": (
            "Lifecycle-duration batch packets are row-level evidence envelopes. They do not mutate program "
            "lifecycle rules; they only support reviewer decisions and later accepted-mapping evidence."
        ),
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
    write_summary(rows, read_csv(BATCH_CSV), generated_at)
    print(dumps({"program_lifecycle_duration_review_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
