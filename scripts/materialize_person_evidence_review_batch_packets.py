#!/usr/bin/env python3
"""Materialize all-packet decision support rows for person evidence review batches."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "person_evidence_review_batch_packets.csv"
JSON_PATH = ARTIFACTS / "person_evidence_review_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "person_evidence_review_batch_packet_summary.json"

DECISION_ARTIFACT = "artifacts/data/person_evidence_reviewer_decisions.csv"

FIELDS = [
    "batch_packet_key",
    "review_batch_key",
    "execution_order",
    "batch_packet_order",
    "reviewer_decision_key",
    "packet_key",
    "person_or_name_key",
    "person_key",
    "display_name",
    "role",
    "triage_lane",
    "decision_difficulty",
    "risk_level",
    "packet_status",
    "review_kind",
    "triage_priority",
    "review_ready_record_count",
    "evidence_record_count",
    "source_count",
    "claim_type_count",
    "evidence_density_score",
    "best_decision",
    "likely_next_action",
    "reviewer_prompt",
    "automation_boundary",
    "acceptance_blocker",
    "required_reviewer_action",
    "packet_fingerprint",
    "allowed_decisions",
    "decision_artifact",
    "top_source_urls",
    "top_source_domains",
    "top_claim_types",
    "top_match_features",
    "decision_counts_json",
    "top_review_records_json",
    "support_status",
    "recommended_reviewer_action",
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


def key_for(prefix: str, parts: tuple[str, ...]) -> str:
    return f"{prefix}_{sha256_text(dumps(parts))[:20]}"


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def load_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def index_by(rows: list[dict], key: str) -> dict[str, dict]:
    return {row[key]: row for row in rows if row.get(key)}


def packet_keys_for_batch(batch: dict) -> list[str]:
    evidence = load_json(batch.get("evidence_json"), {})
    keys = evidence.get("packet_keys") if isinstance(evidence, dict) else []
    if isinstance(keys, list):
        return [str(key) for key in keys if key]
    return []


def compact_review_records(packet: dict, limit: int = 8) -> list[dict]:
    evidence = load_json(packet.get("evidence_json"), {})
    records = evidence.get("top_records") if isinstance(evidence, dict) else []
    if not isinstance(records, list):
        return []
    output = []
    for record in records[:limit]:
        if not isinstance(record, dict):
            continue
        output.append(
            {
                "record_type": record.get("record_type") or "",
                "record_id": record.get("record_id") or "",
                "claim_type": record.get("claim_type") or "",
                "decision": record.get("decision") or "",
                "confidence": record.get("confidence") or "",
                "priority": record.get("priority") or "",
                "source_url": record.get("source_url") or "",
                "match_features": record.get("match_features") or "",
                "required_next_evidence": record.get("required_next_evidence") or "",
            }
        )
    return output


def decision_counts(packet: dict) -> dict:
    evidence = load_json(packet.get("evidence_json"), {})
    counts = evidence.get("decision_counts") if isinstance(evidence, dict) else {}
    return counts if isinstance(counts, dict) else {}


def support_status(batch: dict, triage: dict, queue: dict) -> str:
    if batch.get("batch_status") != "ready_for_reviewer_decision_batch":
        return "blocked_batch_not_ready"
    if not triage:
        return "blocked_missing_triage_row"
    if not queue:
        return "blocked_missing_reviewer_queue_row"
    if not triage.get("packet_fingerprint") or triage.get("packet_fingerprint") != queue.get("packet_fingerprint"):
        return "blocked_packet_fingerprint_mismatch"
    return "ready_for_packet_review"


def recommended_action(row_status: str, triage: dict) -> str:
    if row_status == "ready_for_packet_review":
        return triage.get("likely_next_action") or "record_packet_reviewer_decision"
    if row_status == "blocked_packet_fingerprint_mismatch":
        return "regenerate_review_queue_before_decision"
    return "resolve_batch_packet_support_blocker"


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    batches = sqlite_rows(conn, "SELECT * FROM person_evidence_review_batches ORDER BY execution_order")
    triage_by_packet = index_by(sqlite_rows(conn, "SELECT * FROM person_evidence_review_triage"), "packet_key")
    queue_by_key = index_by(sqlite_rows(conn, "SELECT * FROM person_evidence_reviewer_decision_queue"), "reviewer_decision_key")
    packets_by_key = index_by(sqlite_rows(conn, "SELECT * FROM person_evidence_review_packets"), "packet_key")

    rows = []
    for batch in batches:
        for index, packet_key in enumerate(packet_keys_for_batch(batch), start=1):
            triage = triage_by_packet.get(packet_key, {})
            queue = queue_by_key.get(triage.get("reviewer_decision_key") or "", {})
            packet = packets_by_key.get(packet_key, {})
            row_status = support_status(batch, triage, queue)
            top_review_records = compact_review_records(packet)
            evidence = {
                "batch": {
                    "review_batch_key": batch.get("review_batch_key"),
                    "execution_order": batch.get("execution_order"),
                    "triage_lane": batch.get("triage_lane"),
                    "decision_difficulty": batch.get("decision_difficulty"),
                    "risk_level": batch.get("risk_level"),
                    "batch_status": batch.get("batch_status"),
                },
                "triage": {
                    key: triage.get(key, "")
                    for key in [
                        "triage_key",
                        "reviewer_decision_key",
                        "packet_key",
                        "display_name",
                        "triage_priority",
                        "reviewer_prompt",
                        "automation_boundary",
                        "acceptance_blocker",
                        "required_reviewer_action",
                        "packet_fingerprint",
                    ]
                },
                "queue": {
                    "queue_status": queue.get("queue_status", ""),
                    "allowed_decisions": queue.get("allowed_decisions", ""),
                    "packet_fingerprint": queue.get("packet_fingerprint", ""),
                    "display_safety_status": queue.get("display_safety_status", ""),
                },
                "packet_summary": {
                    "decision_counts": decision_counts(packet),
                    "top_review_records": top_review_records,
                },
                "policy": {
                    "non_mutating": True,
                    "accepted_fact_requires": [
                        "person_evidence_reviewer_decisions.csv row",
                        "matching packet_fingerprint",
                        "identity/source/non-name-anchor/display confirmations",
                    ],
                },
            }
            row = {
                "batch_packet_key": key_for("person_evidence_batch_packet", (batch["review_batch_key"], packet_key)),
                "review_batch_key": batch["review_batch_key"],
                "execution_order": as_int(batch.get("execution_order")),
                "batch_packet_order": index,
                "reviewer_decision_key": triage.get("reviewer_decision_key") or "",
                "packet_key": packet_key,
                "person_or_name_key": triage.get("person_or_name_key") or packet.get("person_or_name_key") or "",
                "person_key": triage.get("person_key") or packet.get("person_key") or "",
                "display_name": triage.get("display_name") or packet.get("display_name") or "",
                "role": triage.get("role") or packet.get("role") or "",
                "triage_lane": batch.get("triage_lane") or triage.get("triage_lane") or "",
                "decision_difficulty": batch.get("decision_difficulty") or triage.get("decision_difficulty") or "",
                "risk_level": batch.get("risk_level") or triage.get("risk_level") or "",
                "packet_status": triage.get("packet_status") or packet.get("packet_status") or "",
                "review_kind": triage.get("review_kind") or packet.get("review_kind") or "",
                "triage_priority": as_int(triage.get("triage_priority")),
                "review_ready_record_count": as_int(triage.get("review_ready_record_count") or packet.get("review_ready_record_count")),
                "evidence_record_count": as_int(triage.get("evidence_record_count") or packet.get("evidence_record_count")),
                "source_count": as_int(triage.get("source_count")),
                "claim_type_count": as_int(triage.get("claim_type_count")),
                "evidence_density_score": round(as_float(triage.get("evidence_density_score")), 3),
                "best_decision": triage.get("best_decision") or packet.get("best_decision") or "",
                "likely_next_action": triage.get("likely_next_action") or "",
                "reviewer_prompt": triage.get("reviewer_prompt") or "",
                "automation_boundary": triage.get("automation_boundary") or "",
                "acceptance_blocker": triage.get("acceptance_blocker") or packet.get("acceptance_blocker") or "",
                "required_reviewer_action": triage.get("required_reviewer_action") or "",
                "packet_fingerprint": triage.get("packet_fingerprint") or queue.get("packet_fingerprint") or "",
                "allowed_decisions": queue.get("allowed_decisions") or "",
                "decision_artifact": DECISION_ARTIFACT,
                "top_source_urls": packet.get("top_source_urls") or "",
                "top_source_domains": triage.get("top_source_domains") or "",
                "top_claim_types": packet.get("top_claim_types") or "",
                "top_match_features": packet.get("top_match_features") or "",
                "decision_counts_json": dumps(decision_counts(packet)),
                "top_review_records_json": dumps(top_review_records),
                "support_status": row_status,
                "recommended_reviewer_action": recommended_action(row_status, triage),
                "evidence_json": dumps(evidence),
                "generated_at": generated_at,
            }
            rows.append({field: row[field] for field in FIELDS})
    rows.sort(key=lambda item: (as_int(item["execution_order"]), as_int(item["batch_packet_order"]), item["packet_key"]))
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_evidence_review_batch_packets")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO person_evidence_review_batch_packets ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_packet_rows": len(rows),
        "batch_count": len({row["review_batch_key"] for row in rows}),
        "packet_count": len({row["packet_key"] for row in rows}),
        "person_count": len({row["person_or_name_key"] for row in rows if row.get("person_or_name_key")}),
        "review_ready_record_count": sum(as_int(row["review_ready_record_count"]) for row in rows),
        "evidence_record_count": sum(as_int(row["evidence_record_count"]) for row in rows),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_triage_lane": dict(sorted(Counter(row["triage_lane"] for row in rows).items())),
        "by_decision_difficulty": dict(sorted(Counter(row["decision_difficulty"] for row in rows).items())),
        "by_risk_level": dict(sorted(Counter(row["risk_level"] for row in rows).items())),
        "top_packet_support_rows": [
            {
                "execution_order": row["execution_order"],
                "batch_packet_order": row["batch_packet_order"],
                "display_name": row["display_name"],
                "triage_lane": row["triage_lane"],
                "triage_priority": row["triage_priority"],
                "review_ready_record_count": row["review_ready_record_count"],
                "best_decision": row["best_decision"],
                "recommended_reviewer_action": row["recommended_reviewer_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Batch packet support rows are non-mutating reviewer aids. Accepted facts still require explicit reviewer decisions with matching packet fingerprints and confirmations.",
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
    print(dumps({"person_evidence_review_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
