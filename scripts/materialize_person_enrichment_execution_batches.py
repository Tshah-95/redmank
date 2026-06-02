#!/usr/bin/env python3
"""Materialize resumable execution batches for person enrichment work."""

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

CSV_PATH = ARTIFACTS / "person_enrichment_execution_batches.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_execution_batches.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_execution_batch_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDNAMES = [
    "batch_key",
    "task_type",
    "source_family",
    "priority_band",
    "execution_lane",
    "automation_status",
    "execution_order",
    "batch_status",
    "task_count",
    "person_count",
    "role_counts_json",
    "program_count",
    "top_programs",
    "max_priority",
    "min_priority",
    "critical_task_count",
    "network_required_count",
    "manual_review_required_count",
    "script_extension_required_count",
    "new_parser_required_count",
    "existing_collector",
    "command_hint",
    "input_artifacts_json",
    "output_artifacts_json",
    "expected_claim_types_json",
    "evidence_requirement",
    "acceptance_rule",
    "recency_policy",
    "provenance_policy",
    "next_system_action",
    "top_people_json",
    "ready_to_execute",
    "blocked_reason",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def compact_join(values: list[str], limit: int = 12) -> str:
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= limit:
        return "; ".join(seen)
    return "; ".join(seen[:limit]) + f"; +{len(seen) - limit} more"


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["batch_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def read_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT r.*,
                   q.source_strategy,
                   q.query,
                   q.source_targets_json,
                   q.expected_claim_types_json,
                   q.evidence_requirement,
                   q.acceptance_rule,
                   q.recency_policy,
                   q.provenance_policy,
                   q.blocking_risk,
                   q.operator_action
            FROM person_enrichment_execution_readiness r
            JOIN person_enrichment_work_queue q ON q.task_key = r.task_key
            ORDER BY r.batch_key, r.priority DESC, r.batch_rank
            """
        )
    ]


def batch_status(rows: list[dict]) -> tuple[str, int, str]:
    network = sum(as_int(row.get("requires_network")) for row in rows)
    manual = sum(as_int(row.get("requires_manual_review")) for row in rows)
    script = sum(as_int(row.get("requires_script_extension")) for row in rows)
    parser = sum(as_int(row.get("requires_new_parser")) for row in rows)
    if parser:
        return "blocked_needs_new_parser", 0, "requires_new_parser"
    if script:
        return "blocked_needs_script_extension", 0, "requires_script_extension"
    if network and manual:
        return "network_collection_then_manual_review_ready", 1, ""
    if network:
        return "network_collection_ready", 1, ""
    if manual:
        return "manual_review_ready", 1, ""
    return "local_rebuild_or_monitor_ready", 1, ""


def top_people(rows: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("priority")), as_int(item.get("batch_rank"))))[:limit]:
        output.append(
            {
                "task_key": row.get("task_key") or "",
                "person_key": row.get("person_key") or "",
                "display_name": row.get("display_name") or "",
                "role": row.get("role") or "",
                "program_name": row.get("program_name") or "",
                "priority": as_int(row.get("priority")),
                "batch_rank": as_int(row.get("batch_rank")),
            }
        )
    return output


def materialize(conn: sqlite3.Connection) -> list[dict]:
    existing = read_existing()
    timestamp = now_utc()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in read_rows(conn):
        grouped[row["batch_key"]].append(row)

    rows = []
    for batch_key, group_rows in grouped.items():
        first = group_rows[0]
        status, ready, blocked_reason = batch_status(group_rows)
        priorities = [as_int(row.get("priority")) for row in group_rows]
        role_counts = Counter(row.get("role") or "" for row in group_rows)
        program_counts = Counter(row.get("program_name") or "" for row in group_rows if row.get("program_name"))
        command_counts = Counter(row.get("command_hint") or "" for row in group_rows)
        collector_counts = Counter(row.get("existing_collector") or "" for row in group_rows)
        input_counts = Counter(row.get("input_artifacts_json") or "" for row in group_rows)
        output_counts = Counter(row.get("output_artifacts_json") or "" for row in group_rows)
        expected_claim_counts = Counter(row.get("expected_claim_types_json") or "" for row in group_rows)
        evidence_requirement_counts = Counter(row.get("evidence_requirement") or "" for row in group_rows)
        acceptance_rule_counts = Counter(row.get("acceptance_rule") or "" for row in group_rows)
        recency_policy_counts = Counter(row.get("recency_policy") or "" for row in group_rows)
        provenance_policy_counts = Counter(row.get("provenance_policy") or "" for row in group_rows)
        next_action_counts = Counter(row.get("next_system_action") or "" for row in group_rows)
        evidence = {
            "policy": {
                "batch": "Non-mutating execution manifest. It describes collection/review work and gates before accepted facts may change.",
                "ready_to_execute": "Ready means existing scripts or manual review packets are available; it does not mean candidate evidence is accepted.",
                "acceptance": "Outputs must flow back through reconciliation, acceptance, contact, state-machine, or denominator ledgers before display/truth mutation.",
            },
            "by_priority_band": dict(Counter(row.get("priority_band") or "" for row in group_rows)),
            "by_role": dict(role_counts),
            "by_program": dict(program_counts.most_common(20)),
            "top_blocking_risks": dict(Counter(row.get("blocking_risk") or "" for row in group_rows).most_common(5)),
            "source_strategies": sorted({row.get("source_strategy") or "" for row in group_rows if row.get("source_strategy")}),
        }
        row = {
            "batch_key": batch_key,
            "task_type": first.get("task_type") or "",
            "source_family": first.get("source_family") or "",
            "priority_band": first.get("priority_band") or "",
            "execution_lane": first.get("execution_lane") or "",
            "automation_status": first.get("automation_status") or "",
            "execution_order": 0,
            "batch_status": status,
            "task_count": len(group_rows),
            "person_count": len({row.get("person_key") for row in group_rows}),
            "role_counts_json": dumps(dict(sorted(role_counts.items()))),
            "program_count": len(program_counts),
            "top_programs": compact_join([value for value, _ in program_counts.most_common(12)]),
            "max_priority": max(priorities) if priorities else 0,
            "min_priority": min(priorities) if priorities else 0,
            "critical_task_count": sum(1 for row in group_rows if row.get("priority_band") == "critical"),
            "network_required_count": sum(as_int(row.get("requires_network")) for row in group_rows),
            "manual_review_required_count": sum(as_int(row.get("requires_manual_review")) for row in group_rows),
            "script_extension_required_count": sum(as_int(row.get("requires_script_extension")) for row in group_rows),
            "new_parser_required_count": sum(as_int(row.get("requires_new_parser")) for row in group_rows),
            "existing_collector": collector_counts.most_common(1)[0][0],
            "command_hint": command_counts.most_common(1)[0][0],
            "input_artifacts_json": input_counts.most_common(1)[0][0],
            "output_artifacts_json": output_counts.most_common(1)[0][0],
            "expected_claim_types_json": expected_claim_counts.most_common(1)[0][0],
            "evidence_requirement": evidence_requirement_counts.most_common(1)[0][0],
            "acceptance_rule": acceptance_rule_counts.most_common(1)[0][0],
            "recency_policy": recency_policy_counts.most_common(1)[0][0],
            "provenance_policy": provenance_policy_counts.most_common(1)[0][0],
            "next_system_action": next_action_counts.most_common(1)[0][0],
            "top_people_json": dumps(top_people(group_rows)),
            "ready_to_execute": ready,
            "blocked_reason": blocked_reason,
            "evidence_json": dumps(evidence),
            "generated_at": "",
        }
        rows.append(row)

    rows = sorted(
        rows,
        key=lambda row: (
            -row["ready_to_execute"],
            -row["max_priority"],
            -row["task_count"],
            row["task_type"],
            row["priority_band"],
        ),
    )
    for index, row in enumerate(rows, start=1):
        row["execution_order"] = index
        row["generated_at"] = stable_generated_at(existing, row, timestamp)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_enrichment_execution_batches")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    field_sql = ", ".join(FIELDNAMES)
    conn.executemany(
        f"INSERT INTO person_enrichment_execution_batches ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict]) -> None:
    payload = {
        "batch_rows": len(rows),
        "ready_batch_rows": sum(row["ready_to_execute"] for row in rows),
        "blocked_batch_rows": sum(1 for row in rows if not row["ready_to_execute"]),
        "task_rows": sum(row["task_count"] for row in rows),
        "total_batch_person_impact_count": sum(row["person_count"] for row in rows),
        "impact_count_policy": "Summed across batches, not deduplicated unique people; a person can correctly appear in multiple enrichment batches.",
        "network_batch_rows": sum(1 for row in rows if row["network_required_count"] > 0),
        "manual_review_batch_rows": sum(1 for row in rows if row["manual_review_required_count"] > 0),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_task_type": dict(sorted(Counter(row["task_type"] for row in rows).items())),
        "by_source_family": dict(sorted(Counter(row["source_family"] for row in rows).items())),
        "by_priority_band": dict(sorted(Counter(row["priority_band"] for row in rows).items())),
        "by_execution_lane": dict(sorted(Counter(row["execution_lane"] for row in rows).items())),
        "top_batches": [
            {
                "batch_key": row["batch_key"],
                "execution_order": row["execution_order"],
                "task_type": row["task_type"],
                "source_family": row["source_family"],
                "priority_band": row["priority_band"],
                "batch_status": row["batch_status"],
                "task_count": row["task_count"],
                "person_count": row["person_count"],
                "max_priority": row["max_priority"],
                "next_system_action": row["next_system_action"],
                "command_hint": row["command_hint"],
            }
            for row in rows[:15]
        ],
        "policy": "Execution batches are non-mutating. They make collection and review work resumable; accepted facts only change through downstream assurance ledgers.",
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
    print(dumps({"person_enrichment_execution_batches": len(rows)}))


if __name__ == "__main__":
    main()
