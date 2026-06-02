#!/usr/bin/env python3
"""Materialize resumable batches over person enrichment action packets."""

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

CSV_PATH = ARTIFACTS / "person_enrichment_action_batches.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_action_batches.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_action_batch_summary.json"

MAX_BATCH_SIZE = 50

FIELDS = [
    "action_batch_key",
    "primary_action_lane",
    "packet_status",
    "priority_band",
    "role",
    "batch_number",
    "execution_order",
    "batch_status",
    "ready_to_execute",
    "blocked_reason",
    "packet_count",
    "person_count",
    "max_priority",
    "min_priority",
    "total_task_count",
    "total_review_packet_count",
    "total_evidence_record_count",
    "total_profile_workbench_count",
    "total_contact_contract_count",
    "top_programs",
    "top_packet_keys_json",
    "top_people_json",
    "command_hints_json",
    "next_actions_json",
    "required_next_evidence",
    "downstream_artifacts_json",
    "execution_notes",
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


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def compact_values(values: list[str], limit: int = 12) -> list[str]:
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return seen[:limit]


def compact_join(values: list[str], limit: int = 12) -> str:
    values = compact_values(values, limit + 1)
    if len(values) <= limit:
        return "; ".join(values)
    return "; ".join(values[:limit]) + f"; +{len(values) - limit} more"


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["action_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["action_batch_key"])
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


def chunk_rows(rows: list[dict], size: int) -> list[list[dict]]:
    return [rows[index : index + size] for index in range(0, len(rows), size)]


def status_for(lane: str, packet_status: str) -> tuple[str, int, str]:
    if packet_status == "search_endpoint_retry_required":
        return "blocked_retry_or_replace_search_endpoint", 0, "search_endpoint_retry_required"
    if lane == "person_evidence_review":
        return "manual_packet_review_ready", 1, ""
    if lane == "official_profile_review":
        return "profile_reviewer_decision_ready", 1, ""
    if lane == "official_profile_discovery":
        return "profile_discovery_execution_ready", 1, ""
    if lane == "enrichment_collector_execution":
        return "collector_execution_ready", 1, ""
    if lane == "contact_verification":
        return "contact_reverification_ready", 1, ""
    return "operator_review_ready", 1, ""


def top_people(rows: list[dict], limit: int = 15) -> list[dict]:
    output = []
    for row in rows[:limit]:
        output.append(
            {
                "action_packet_key": row.get("action_packet_key") or "",
                "person_key": row.get("person_key") or "",
                "display_name": row.get("display_name") or "",
                "role": row.get("role") or "",
                "programs": row.get("programs") or "",
                "priority": as_int(row.get("priority")),
                "packet_status": row.get("packet_status") or "",
                "recommended_next_action": row.get("recommended_next_action") or "",
            }
        )
    return output


def next_actions(rows: list[dict]) -> list[dict]:
    counter = Counter(row.get("recommended_next_action") or "" for row in rows)
    return [{"action": action, "count": count} for action, count in counter.most_common(8) if action]


def command_hints(rows: list[dict]) -> list[str]:
    hints: list[str] = []
    for row in rows:
        hints.extend(load_json(row.get("command_hints_json"), []))
    return compact_values([str(hint) for hint in hints if hint], 8)


def downstream_artifacts(rows: list[dict]) -> list[str]:
    artifacts: list[str] = []
    for row in rows:
        artifacts.extend(load_json(row.get("downstream_artifacts_json"), []))
    artifacts.append("artifacts/data/person_enrichment_action_batches.csv")
    return compact_values([str(path) for path in artifacts if path], 14)


def required_evidence(rows: list[dict]) -> str:
    values: list[str] = []
    for row in rows:
        values.extend(split_semicolon(row.get("required_next_evidence")))
    return "; ".join(compact_values(values, 10))


def execution_notes(lane: str, status: str, ready: int, rows: list[dict]) -> str:
    if not ready:
        return "Resolve the blocker before treating this batch as executable. The batch is retained for audit visibility."
    if lane == "person_evidence_review":
        return "Review packet fingerprints and record explicit reviewer decisions before any enrichment fact is accepted."
    if lane == "official_profile_review":
        return "Review official profile candidate identity/currentness and record an explicit profile reviewer decision."
    if lane == "official_profile_discovery":
        return "Run or retry official profile discovery, then rebuild profile reviewer queues and action packets."
    if lane == "enrichment_collector_execution":
        return "Run queued collectors for these people, then feed outputs through source-specific reconciliation and acceptance ledgers."
    return f"Execute {status} for {len(rows)} person packets, preserving source-specific acceptance gates."


def materialize(conn: sqlite3.Connection) -> list[dict]:
    existing = read_existing()
    timestamp = now_utc()
    packets = sqlite_rows(
        conn,
        """
        SELECT *
        FROM person_enrichment_action_packets
        ORDER BY
          CASE priority_band
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            ELSE 4
          END,
          priority DESC,
          display_name,
          person_key
        """,
    )
    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for packet in packets:
        key = (
            packet.get("primary_action_lane") or "",
            packet.get("packet_status") or "",
            packet.get("priority_band") or "",
            packet.get("role") or "",
        )
        grouped[key].append(packet)

    rows = []
    for (lane, packet_status, band, role), group_rows in grouped.items():
        chunks = chunk_rows(group_rows, MAX_BATCH_SIZE)
        for batch_number, chunk in enumerate(chunks, start=1):
            priorities = [as_int(row.get("priority")) for row in chunk]
            batch_status, ready, blocked_reason = status_for(lane, packet_status)
            programs = []
            for row in chunk:
                programs.extend(split_semicolon(row.get("programs")))
            evidence = {
                "policy": {
                    "batch": "Non-mutating execution batch over person enrichment action packets.",
                    "acceptance": "Executing a batch does not accept facts; outputs must flow through the relevant profile, contact, evidence, temporal, or acceptance ledger.",
                    "chunking": f"Batches are grouped by lane/status/priority/role and split at {MAX_BATCH_SIZE} packets for resumability.",
                },
                "packet_status": packet_status,
                "primary_action_lane": lane,
                "priority_band": band,
                "role": role,
                "packet_keys": [row.get("action_packet_key") for row in chunk],
                "status_counts": dict(Counter(row.get("packet_status") or "" for row in chunk)),
                "action_counts": dict(Counter(row.get("recommended_next_action") or "" for row in chunk)),
            }
            row = {
                "action_batch_key": key_for(
                    "person_enrichment_action_batch",
                    [lane, packet_status, band, role, batch_number],
                ),
                "primary_action_lane": lane,
                "packet_status": packet_status,
                "priority_band": band,
                "role": role,
                "batch_number": batch_number,
                "execution_order": 0,
                "batch_status": batch_status,
                "ready_to_execute": ready,
                "blocked_reason": blocked_reason,
                "packet_count": len(chunk),
                "person_count": len({row.get("person_key") for row in chunk}),
                "max_priority": max(priorities) if priorities else 0,
                "min_priority": min(priorities) if priorities else 0,
                "total_task_count": sum(as_int(row.get("task_count")) for row in chunk),
                "total_review_packet_count": sum(as_int(row.get("review_packet_count")) for row in chunk),
                "total_evidence_record_count": sum(as_int(row.get("evidence_record_count")) for row in chunk),
                "total_profile_workbench_count": sum(as_int(row.get("profile_workbench_count")) for row in chunk),
                "total_contact_contract_count": sum(as_int(row.get("contact_contract_count")) for row in chunk),
                "top_programs": compact_join(programs, 10),
                "top_packet_keys_json": dumps([row.get("action_packet_key") for row in chunk[:20]]),
                "top_people_json": dumps(top_people(chunk)),
                "command_hints_json": dumps(command_hints(chunk)),
                "next_actions_json": dumps(next_actions(chunk)),
                "required_next_evidence": required_evidence(chunk),
                "downstream_artifacts_json": dumps(downstream_artifacts(chunk)),
                "execution_notes": execution_notes(lane, batch_status, ready, chunk),
                "evidence_json": dumps(evidence),
                "generated_at": "",
            }
            rows.append(row)

    rows = sorted(
        rows,
        key=lambda row: (
            -row["ready_to_execute"],
            {"critical": 1, "high": 2, "medium": 3, "low": 4}.get(row["priority_band"], 5),
            -row["max_priority"],
            row["primary_action_lane"],
            row["role"] or "",
            row["batch_number"],
        ),
    )
    for index, row in enumerate(rows, start=1):
        row["execution_order"] = index
        row["generated_at"] = stable_generated_at(existing, row, timestamp)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_enrichment_action_batches")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    fields = ", ".join(FIELDS)
    conn.executemany(f"INSERT INTO person_enrichment_action_batches ({fields}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict]) -> None:
    payload = {
        "action_batch_rows": len(rows),
        "ready_batch_rows": sum(row["ready_to_execute"] for row in rows),
        "blocked_batch_rows": sum(1 for row in rows if not row["ready_to_execute"]),
        "packet_rows": sum(row["packet_count"] for row in rows),
        "person_impact_count": sum(row["person_count"] for row in rows),
        "impact_count_policy": "Summed across batches; each person packet appears in exactly one action batch.",
        "max_batch_size": MAX_BATCH_SIZE,
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_primary_action_lane": dict(sorted(Counter(row["primary_action_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_priority_band": dict(sorted(Counter(row["priority_band"] for row in rows).items())),
        "top_batches": [
            {
                "action_batch_key": row["action_batch_key"],
                "execution_order": row["execution_order"],
                "primary_action_lane": row["primary_action_lane"],
                "packet_status": row["packet_status"],
                "priority_band": row["priority_band"],
                "role": row["role"],
                "packet_count": row["packet_count"],
                "person_count": row["person_count"],
                "batch_status": row["batch_status"],
                "execution_notes": row["execution_notes"],
            }
            for row in rows[:20]
        ],
        "policy": "Action batches are non-mutating. They make per-person action packets resumable and auditable while preserving source-specific acceptance gates.",
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
        rows = materialize(conn)
        write_db(conn, rows)
        write_csv(CSV_PATH, rows)
        JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
    conn.close()
    print(dumps({"person_enrichment_action_batches": len(rows)}))


if __name__ == "__main__":
    main()
