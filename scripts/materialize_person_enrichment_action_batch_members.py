#!/usr/bin/env python3
"""Materialize exact person packet membership for enrichment action batches."""

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

CSV_PATH = ARTIFACTS / "person_enrichment_action_batch_members.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_action_batch_members.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_action_batch_member_summary.json"

FIELDS = [
    "action_batch_member_key",
    "action_batch_key",
    "action_packet_key",
    "execution_order",
    "member_order",
    "primary_action_lane",
    "packet_status",
    "priority_band",
    "batch_status",
    "ready_to_execute",
    "blocked_reason",
    "person_key",
    "display_name",
    "role",
    "current_status",
    "programs",
    "coverage_score",
    "coverage_band",
    "dossier_status",
    "display_safety_status",
    "packet_priority",
    "task_count",
    "review_packet_count",
    "profile_workbench_count",
    "contact_contract_count",
    "evidence_record_count",
    "source_count",
    "recommended_next_action",
    "required_next_evidence",
    "primary_blocker",
    "command_hints_json",
    "next_action_sequence_json",
    "top_source_urls",
    "downstream_artifacts_json",
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


def key_for(prefix: str, parts: list[object]) -> str:
    return f"{prefix}_{sha256_text(dumps(parts))[:20]}"


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def load_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["action_batch_member_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["action_batch_member_key"])
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


def packet_keys_for_batch(batch: dict) -> list[str]:
    evidence = load_json(batch.get("evidence_json"), {})
    keys = evidence.get("packet_keys") if isinstance(evidence, dict) else []
    if isinstance(keys, list):
        return [str(key) for key in keys if key]
    return []


def build_rows(conn: sqlite3.Connection) -> list[dict]:
    existing = read_existing()
    timestamp = now_utc()
    batches = sqlite_rows(conn, "SELECT * FROM person_enrichment_action_batches ORDER BY execution_order")
    packets = {
        row["action_packet_key"]: row
        for row in sqlite_rows(conn, "SELECT * FROM person_enrichment_action_packets")
        if row.get("action_packet_key")
    }
    rows = []
    for batch in batches:
        packet_keys = packet_keys_for_batch(batch)
        for member_order, packet_key in enumerate(packet_keys, start=1):
            packet = packets.get(packet_key, {})
            evidence = {
                "policy": {
                    "member": "Non-mutating exact membership row for a person enrichment action batch.",
                    "acceptance": "Executing this member does not accept facts; outputs must flow through source-specific reviewer/acceptance ledgers.",
                },
                "batch": {
                    key: batch.get(key, "")
                    for key in [
                        "action_batch_key",
                        "execution_order",
                        "primary_action_lane",
                        "packet_status",
                        "priority_band",
                        "batch_status",
                        "ready_to_execute",
                        "blocked_reason",
                    ]
                },
                "packet": {
                    key: packet.get(key, "")
                    for key in [
                        "action_packet_key",
                        "person_key",
                        "display_name",
                        "role",
                        "programs",
                        "packet_status",
                        "priority",
                        "recommended_next_action",
                        "primary_blocker",
                    ]
                },
            }
            row = {
                "action_batch_member_key": key_for(
                    "person_enrichment_action_batch_member",
                    [batch.get("action_batch_key"), packet_key],
                ),
                "action_batch_key": batch.get("action_batch_key") or "",
                "action_packet_key": packet_key,
                "execution_order": as_int(batch.get("execution_order")),
                "member_order": member_order,
                "primary_action_lane": batch.get("primary_action_lane") or packet.get("primary_action_lane") or "",
                "packet_status": batch.get("packet_status") or packet.get("packet_status") or "",
                "priority_band": batch.get("priority_band") or packet.get("priority_band") or "",
                "batch_status": batch.get("batch_status") or "",
                "ready_to_execute": as_int(batch.get("ready_to_execute")),
                "blocked_reason": batch.get("blocked_reason") or "",
                "person_key": packet.get("person_key") or "",
                "display_name": packet.get("display_name") or "",
                "role": packet.get("role") or "",
                "current_status": packet.get("current_status") or "",
                "programs": packet.get("programs") or "",
                "coverage_score": as_int(packet.get("coverage_score")),
                "coverage_band": packet.get("coverage_band") or "",
                "dossier_status": packet.get("dossier_status") or "",
                "display_safety_status": packet.get("display_safety_status") or "",
                "packet_priority": as_int(packet.get("priority")),
                "task_count": as_int(packet.get("task_count")),
                "review_packet_count": as_int(packet.get("review_packet_count")),
                "profile_workbench_count": as_int(packet.get("profile_workbench_count")),
                "contact_contract_count": as_int(packet.get("contact_contract_count")),
                "evidence_record_count": as_int(packet.get("evidence_record_count")),
                "source_count": as_int(packet.get("source_count")),
                "recommended_next_action": packet.get("recommended_next_action") or "",
                "required_next_evidence": packet.get("required_next_evidence") or "",
                "primary_blocker": packet.get("primary_blocker") or "",
                "command_hints_json": packet.get("command_hints_json") or "[]",
                "next_action_sequence_json": packet.get("next_action_sequence_json") or "[]",
                "top_source_urls": packet.get("top_source_urls") or "",
                "downstream_artifacts_json": packet.get("downstream_artifacts_json") or "[]",
                "evidence_json": dumps(evidence),
                "generated_at": "",
            }
            row["generated_at"] = stable_generated_at(existing, row, timestamp)
            rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_enrichment_action_batch_members")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    fields = ", ".join(FIELDS)
    conn.executemany(
        f"INSERT INTO person_enrichment_action_batch_members ({fields}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict]) -> None:
    payload = {
        "action_batch_member_rows": len(rows),
        "batch_count": len({row["action_batch_key"] for row in rows}),
        "packet_count": len({row["action_packet_key"] for row in rows}),
        "person_count": len({row["person_key"] for row in rows}),
        "ready_member_rows": sum(row["ready_to_execute"] for row in rows),
        "blocked_member_rows": sum(1 for row in rows if not row["ready_to_execute"]),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_primary_action_lane": dict(sorted(Counter(row["primary_action_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_priority_band": dict(sorted(Counter(row["priority_band"] for row in rows).items())),
        "top_members": [
            {
                "execution_order": row["execution_order"],
                "member_order": row["member_order"],
                "display_name": row["display_name"],
                "role": row["role"],
                "primary_action_lane": row["primary_action_lane"],
                "packet_status": row["packet_status"],
                "packet_priority": row["packet_priority"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:20]
        ],
        "policy": "Batch members are non-mutating exact membership rows. They make each person packet in each action batch addressable for execution, review, and diffing.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    with conn:
        rows = build_rows(conn)
        write_db(conn, rows)
        write_csv(CSV_PATH, rows)
        JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
    conn.close()
    print(dumps({"person_enrichment_action_batch_members": len(rows)}))


if __name__ == "__main__":
    main()
