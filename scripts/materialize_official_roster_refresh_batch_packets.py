#!/usr/bin/env python3
"""Materialize per-refresh-contract packet support for official roster refresh batches."""

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

CSV_PATH = ARTIFACTS / "official_roster_refresh_batch_packets.csv"
JSON_PATH = ARTIFACTS / "official_roster_refresh_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "official_roster_refresh_batch_packet_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "official_roster_refresh_batch_packet_key",
    "roster_batch_key",
    "execution_order",
    "batch_packet_order",
    "refresh_key",
    "source_key",
    "source_url",
    "source_title",
    "source_type",
    "source_domain",
    "program_name",
    "role",
    "trainee_category",
    "refresh_lane",
    "refresh_priority",
    "refresh_difficulty",
    "parser_status",
    "batch_status",
    "packet_status",
    "support_status",
    "contract_count",
    "person_count",
    "expected_advancement_count",
    "expected_completion_count",
    "source_refresh_required_count",
    "manual_review_required_count",
    "stale_by_refresh_count",
    "fresh_observation_required_count",
    "auto_classifiable_transition_count",
    "requires_manual_review",
    "collector_hint",
    "command_hint",
    "target_artifact",
    "evidence_required",
    "recommended_next_action",
    "recommended_packet_action",
    "source_metadata_json",
    "sample_people_json",
    "source_row_json",
    "batch_evidence_json",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


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


def read_existing() -> dict[str, dict]:
    return {
        row["official_roster_refresh_batch_packet_key"]: row
        for row in read_csv(CSV_PATH)
        if row.get("official_roster_refresh_batch_packet_key")
    }


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["official_roster_refresh_batch_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def packet_key(batch_key: str, refresh_key: str) -> str:
    return "official_roster_refresh_batch_packet_" + sha256_text(f"{batch_key}|{refresh_key}")[:20]


def packet_status(row: dict) -> str:
    if row.get("parser_status", "").startswith("missing") or "missing" in (row.get("parser_status") or ""):
        return "blocked_missing_parser_packet"
    if as_int(row.get("requires_manual_review")):
        return "fresh_roster_observation_then_manual_review_packet"
    return "fresh_roster_observation_packet"


def support_status(row: dict) -> str:
    parser = row.get("parser_status") or ""
    if "missing" in parser or "not_available" in parser:
        return "blocked_requires_parser_support"
    if as_int(row.get("requires_manual_review")):
        return "ready_for_refresh_then_lifecycle_review"
    return "ready_for_fresh_roster_refresh"


def recommended_packet_action(row: dict) -> str:
    if support_status(row) == "blocked_requires_parser_support":
        return "add_or_repair_roster_parser_before_refresh"
    if as_int(row.get("requires_manual_review")):
        return "refresh_source_then_route_state_change_through_reviewer_gate"
    return "refresh_source_then_reclassify_through_temporal_contracts"


def compact_source_row(row: dict) -> dict:
    return {
        "refresh_key": row.get("refresh_key") or "",
        "source_key": row.get("source_key") or "",
        "source_url": row.get("source_url") or "",
        "program_name": row.get("program_name") or "",
        "role": row.get("role") or "",
        "refresh_lane": row.get("refresh_lane") or "",
        "refresh_priority": as_int(row.get("refresh_priority")),
        "contract_count": as_int(row.get("contract_count")),
        "person_count": as_int(row.get("person_count")),
        "recommended_next_action": row.get("recommended_next_action") or "",
    }


def compact_batch_evidence(batch: dict) -> dict:
    return {
        "roster_batch_key": batch.get("roster_batch_key") or "",
        "execution_order": as_int(batch.get("execution_order")),
        "collector_hint": batch.get("collector_hint") or "",
        "parser_status": batch.get("parser_status") or "",
        "batch_lane": batch.get("batch_lane") or "",
        "batch_status": batch.get("batch_status") or "",
        "source_domain": batch.get("source_domain") or "",
        "source_program_count": as_int(batch.get("source_program_count")),
        "contract_count": as_int(batch.get("contract_count")),
        "person_count": as_int(batch.get("person_count")),
        "ready_to_execute": as_int(batch.get("ready_to_execute")),
        "blocked_reason": batch.get("blocked_reason") or "",
    }


def source_domain(url: str) -> str:
    if "://" in url:
        return url.split("://", 1)[1].split("/", 1)[0].lower()
    return ""


def build_packet(batch: dict, refresh: dict, order: int, generated_at: str, existing: dict[str, dict]) -> dict:
    out = {
        "official_roster_refresh_batch_packet_key": packet_key(batch["roster_batch_key"], refresh["refresh_key"]),
        "roster_batch_key": batch["roster_batch_key"],
        "execution_order": as_int(batch.get("execution_order")),
        "batch_packet_order": order,
        "refresh_key": refresh.get("refresh_key") or "",
        "source_key": refresh.get("source_key") or "",
        "source_url": refresh.get("source_url") or "",
        "source_title": refresh.get("source_title") or "",
        "source_type": refresh.get("source_type") or "",
        "source_domain": source_domain(refresh.get("source_url") or ""),
        "program_name": refresh.get("program_name") or "",
        "role": refresh.get("role") or "",
        "trainee_category": refresh.get("trainee_category") or "",
        "refresh_lane": refresh.get("refresh_lane") or "",
        "refresh_priority": as_int(refresh.get("refresh_priority")),
        "refresh_difficulty": refresh.get("refresh_difficulty") or "",
        "parser_status": refresh.get("parser_status") or batch.get("parser_status") or "",
        "batch_status": batch.get("batch_status") or "",
        "packet_status": packet_status(refresh),
        "support_status": support_status(refresh),
        "contract_count": as_int(refresh.get("contract_count")),
        "person_count": as_int(refresh.get("person_count")),
        "expected_advancement_count": as_int(refresh.get("expected_advancement_count")),
        "expected_completion_count": as_int(refresh.get("expected_completion_count")),
        "source_refresh_required_count": as_int(refresh.get("source_refresh_required_count")),
        "manual_review_required_count": as_int(refresh.get("manual_review_required_count")),
        "stale_by_refresh_count": as_int(refresh.get("stale_by_refresh_count")),
        "fresh_observation_required_count": as_int(refresh.get("fresh_observation_required_count")),
        "auto_classifiable_transition_count": as_int(refresh.get("auto_classifiable_transition_count")),
        "requires_manual_review": as_int(refresh.get("requires_manual_review")),
        "collector_hint": refresh.get("collector_hint") or batch.get("collector_hint") or "",
        "command_hint": batch.get("command_hint") or refresh.get("collector_hint") or "",
        "target_artifact": "artifacts/data/training_state_transition_events.csv",
        "evidence_required": refresh.get("evidence_required") or batch.get("evidence_required") or "",
        "recommended_next_action": refresh.get("recommended_next_action") or batch.get("recommended_next_action") or "",
        "recommended_packet_action": recommended_packet_action(refresh),
        "source_metadata_json": refresh.get("source_metadata_json") or "{}",
        "sample_people_json": refresh.get("sample_people_json") or "[]",
        "source_row_json": dumps(compact_source_row(refresh)),
        "batch_evidence_json": dumps(compact_batch_evidence(batch)),
        "evidence_json": dumps(
            {
                "policy": "Roster refresh packets are non-mutating. Fresh source observations must be rebuilt through training states, temporal contracts, snapshots, transition events, and reviewer gates before status changes.",
                "roster_batch_key": batch.get("roster_batch_key") or "",
                "refresh_key": refresh.get("refresh_key") or "",
                "source_url": refresh.get("source_url") or "",
                "support_status": support_status(refresh),
                "target_artifact": "artifacts/data/training_state_transition_events.csv",
            }
        ),
        "generated_at": generated_at,
    }
    out["generated_at"] = stable_generated_at(existing, out, generated_at)
    return {field: out[field] for field in FIELDS}


def build_rows(generated_at: str) -> list[dict]:
    existing = read_existing()
    workbench = {row["refresh_key"]: row for row in read_csv(ARTIFACTS / "official_roster_refresh_workbench.csv")}
    output = []
    for batch in sorted(
        read_csv(ARTIFACTS / "official_roster_refresh_batches.csv"),
        key=lambda item: as_int(item.get("execution_order")),
    ):
        refresh_keys = [
            row.get("refresh_key")
            for row in parse_json(batch.get("top_refresh_rows_json"), [])
            if row.get("refresh_key")
        ]
        for index, refresh_key in enumerate(refresh_keys, start=1):
            refresh = workbench.get(refresh_key)
            if refresh:
                output.append(build_packet(batch, refresh, index, generated_at, existing))
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DROP TABLE IF EXISTS official_roster_refresh_batch_packets")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO official_roster_refresh_batch_packets ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "batch_count": len({row["roster_batch_key"] for row in rows}),
        "source_count": len({row["source_key"] for row in rows}),
        "program_count": len({row["program_name"] for row in rows}),
        "person_impact_count": sum(as_int(row["person_count"]) for row in rows),
        "contract_count": sum(as_int(row["contract_count"]) for row in rows),
        "by_refresh_lane": dict(sorted(Counter(row["refresh_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_parser_status": dict(sorted(Counter(row["parser_status"] for row in rows).items())),
        "top_packets": [
            {
                "execution_order": row["execution_order"],
                "batch_packet_order": row["batch_packet_order"],
                "program_name": row["program_name"],
                "role": row["role"],
                "refresh_lane": row["refresh_lane"],
                "person_count": row["person_count"],
                "support_status": row["support_status"],
                "source_url": row["source_url"],
            }
            for row in rows[:25]
        ],
        "policy": "Official roster refresh packets expose source/program refresh contracts without mutating training state.",
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
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"official_roster_refresh_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
