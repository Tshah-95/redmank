#!/usr/bin/env python3
"""Materialize per-readiness packet support for person enrichment execution batches."""

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

CSV_PATH = ARTIFACTS / "person_enrichment_execution_batch_packets.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_execution_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_execution_batch_packet_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "person_enrichment_execution_batch_packet_key",
    "batch_key",
    "execution_order",
    "batch_packet_order",
    "readiness_key",
    "task_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "task_type",
    "source_family",
    "priority",
    "priority_band",
    "execution_lane",
    "automation_status",
    "batch_status",
    "packet_status",
    "support_status",
    "requires_network",
    "requires_manual_review",
    "requires_script_extension",
    "requires_new_parser",
    "existing_collector",
    "command_hint",
    "input_artifacts_json",
    "output_artifacts_json",
    "expected_claim_types_json",
    "evidence_requirement",
    "next_system_action",
    "readiness_reason",
    "target_artifact",
    "recommended_packet_action",
    "source_row_json",
    "batch_evidence_json",
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


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {
        row["person_enrichment_execution_batch_packet_key"]: row
        for row in read_csv(CSV_PATH)
        if row.get("person_enrichment_execution_batch_packet_key")
    }


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["person_enrichment_execution_batch_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def packet_key(batch_key: str, readiness_key: str, task_key: str) -> str:
    return "person_enrichment_execution_batch_packet_" + sha256_text(
        f"{batch_key}|{readiness_key}|{task_key}"
    )[:20]


def packet_status(row: dict) -> str:
    if as_int(row.get("requires_new_parser")):
        return "blocked_new_parser_packet"
    if as_int(row.get("requires_script_extension")):
        return "blocked_script_extension_packet"
    if as_int(row.get("requires_network")) and as_int(row.get("requires_manual_review")):
        return "network_collection_then_manual_review_packet"
    if as_int(row.get("requires_network")):
        return "network_collection_packet"
    if as_int(row.get("requires_manual_review")):
        return "manual_review_packet"
    return "local_rebuild_or_monitor_packet"


def support_status(row: dict) -> str:
    if as_int(row.get("requires_new_parser")):
        return "blocked_requires_new_parser"
    if as_int(row.get("requires_script_extension")):
        return "blocked_requires_script_extension"
    if as_int(row.get("requires_network")) and as_int(row.get("requires_manual_review")):
        return "ready_for_collection_then_reviewer_decision"
    if as_int(row.get("requires_network")):
        return "ready_for_collection"
    if as_int(row.get("requires_manual_review")):
        return "ready_for_reviewer_decision"
    return "ready_for_local_rebuild_or_monitor"


def recommended_packet_action(row: dict) -> str:
    status = support_status(row)
    return {
        "blocked_requires_new_parser": "add_parser_before_execution",
        "blocked_requires_script_extension": "extend_collector_before_execution",
        "ready_for_collection_then_reviewer_decision": "run_collector_then_route_output_to_reviewer_ledger",
        "ready_for_collection": "run_collector_and_record_source_observation",
        "ready_for_reviewer_decision": "record_reviewer_decision_with_current_fingerprint",
        "ready_for_local_rebuild_or_monitor": "rebuild_or_monitor_without_accepting_new_facts",
    }[status]


def target_artifact(row: dict) -> str:
    if row.get("task_type") == "public_contact_verification":
        return "artifacts/data/contact_verification_reviewer_decisions.csv"
    if row.get("task_type") == "research_identity_search":
        return "artifacts/data/research_identity_reviewer_decisions.csv"
    if row.get("task_type") == "organization_alias_review":
        return "artifacts/data/official_program_alias_reviewer_decisions.csv"
    if row.get("task_type") in {"source_medical_school_background", "source_residency_background"}:
        return "artifacts/data/evidence_reconciliation_decisions.csv"
    if row.get("task_type") == "official_profile_search":
        return "artifacts/data/official_profile_reviewer_decisions.csv"
    if row.get("task_type") == "evidence_reconciliation_review":
        return "artifacts/data/person_evidence_reviewer_decisions.csv"
    if row.get("task_type") == "current_roster_state_reconciliation":
        return "artifacts/data/training_states_current.csv"
    return "artifacts/data/person_enrichment_execution_readiness.csv"


def compact_source_row(row: dict) -> dict:
    return {
        "readiness_key": row.get("readiness_key") or "",
        "task_key": row.get("task_key") or "",
        "person_key": row.get("person_key") or "",
        "display_name": row.get("display_name") or "",
        "role": row.get("role") or "",
        "program_name": row.get("program_name") or "",
        "task_type": row.get("task_type") or "",
        "source_family": row.get("source_family") or "",
        "priority": as_int(row.get("priority")),
        "priority_band": row.get("priority_band") or "",
        "batch_key": row.get("batch_key") or "",
        "batch_rank": as_int(row.get("batch_rank")),
        "readiness_reason": row.get("readiness_reason") or "",
        "next_system_action": row.get("next_system_action") or "",
    }


def compact_batch_evidence(batch: dict) -> dict:
    return {
        "batch_key": batch.get("batch_key") or "",
        "execution_order": as_int(batch.get("execution_order")),
        "task_type": batch.get("task_type") or "",
        "source_family": batch.get("source_family") or "",
        "priority_band": batch.get("priority_band") or "",
        "execution_lane": batch.get("execution_lane") or "",
        "automation_status": batch.get("automation_status") or "",
        "batch_status": batch.get("batch_status") or "",
        "task_count": as_int(batch.get("task_count")),
        "person_count": as_int(batch.get("person_count")),
        "network_required_count": as_int(batch.get("network_required_count")),
        "manual_review_required_count": as_int(batch.get("manual_review_required_count")),
        "ready_to_execute": as_int(batch.get("ready_to_execute")),
        "blocked_reason": batch.get("blocked_reason") or "",
    }


def build_packet(batch: dict, readiness: dict, order: int, generated_at: str, existing: dict[str, dict]) -> dict:
    out = {
        "person_enrichment_execution_batch_packet_key": packet_key(
            batch["batch_key"],
            readiness.get("readiness_key") or "",
            readiness.get("task_key") or "",
        ),
        "batch_key": batch["batch_key"],
        "execution_order": as_int(batch.get("execution_order")),
        "batch_packet_order": order,
        "readiness_key": readiness.get("readiness_key") or "",
        "task_key": readiness.get("task_key") or "",
        "person_key": readiness.get("person_key") or "",
        "display_name": readiness.get("display_name") or "",
        "role": readiness.get("role") or "",
        "program_name": readiness.get("program_name") or "",
        "task_type": readiness.get("task_type") or "",
        "source_family": readiness.get("source_family") or "",
        "priority": as_int(readiness.get("priority")),
        "priority_band": readiness.get("priority_band") or "",
        "execution_lane": readiness.get("execution_lane") or "",
        "automation_status": readiness.get("automation_status") or "",
        "batch_status": batch.get("batch_status") or "",
        "packet_status": packet_status(readiness),
        "support_status": support_status(readiness),
        "requires_network": as_int(readiness.get("requires_network")),
        "requires_manual_review": as_int(readiness.get("requires_manual_review")),
        "requires_script_extension": as_int(readiness.get("requires_script_extension")),
        "requires_new_parser": as_int(readiness.get("requires_new_parser")),
        "existing_collector": readiness.get("existing_collector") or "",
        "command_hint": readiness.get("command_hint") or "",
        "input_artifacts_json": readiness.get("input_artifacts_json") or "[]",
        "output_artifacts_json": readiness.get("output_artifacts_json") or "[]",
        "expected_claim_types_json": batch.get("expected_claim_types_json") or "[]",
        "evidence_requirement": batch.get("evidence_requirement") or "",
        "next_system_action": readiness.get("next_system_action") or batch.get("next_system_action") or "",
        "readiness_reason": readiness.get("readiness_reason") or "",
        "target_artifact": target_artifact(readiness),
        "recommended_packet_action": recommended_packet_action(readiness),
        "source_row_json": dumps(compact_source_row(readiness)),
        "batch_evidence_json": dumps(compact_batch_evidence(batch)),
        "evidence_json": dumps(
            {
                "policy": "Execution packets are non-mutating. Collector and reviewer outputs must route through downstream assurance ledgers before any accepted fact or display state changes.",
                "batch_key": batch.get("batch_key") or "",
                "readiness_key": readiness.get("readiness_key") or "",
                "task_key": readiness.get("task_key") or "",
                "person_key": readiness.get("person_key") or "",
                "support_status": support_status(readiness),
                "target_artifact": target_artifact(readiness),
            }
        ),
        "generated_at": generated_at,
    }
    out["generated_at"] = stable_generated_at(existing, out, generated_at)
    return {field: out[field] for field in FIELDS}


def build_rows(generated_at: str) -> list[dict]:
    existing = read_existing()
    batches = {row["batch_key"]: row for row in read_csv(ARTIFACTS / "person_enrichment_execution_batches.csv")}
    readiness_by_batch: dict[str, list[dict]] = {}
    for row in read_csv(ARTIFACTS / "person_enrichment_execution_readiness.csv"):
        readiness_by_batch.setdefault(row.get("batch_key") or "", []).append(row)
    output = []
    for batch_key, batch in sorted(batches.items(), key=lambda item: as_int(item[1].get("execution_order"))):
        readiness_rows = sorted(
            readiness_by_batch.get(batch_key, []),
            key=lambda item: (-as_int(item.get("priority")), as_int(item.get("batch_rank")), item.get("task_key") or ""),
        )
        for index, readiness in enumerate(readiness_rows, start=1):
            output.append(build_packet(batch, readiness, index, generated_at, existing))
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DROP TABLE IF EXISTS person_enrichment_execution_batch_packets")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO person_enrichment_execution_batch_packets ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "batch_count": len({row["batch_key"] for row in rows}),
        "person_count": len({row["person_key"] for row in rows}),
        "by_task_type": dict(sorted(Counter(row["task_type"] for row in rows).items())),
        "by_source_family": dict(sorted(Counter(row["source_family"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_execution_lane": dict(sorted(Counter(row["execution_lane"] for row in rows).items())),
        "top_packets": [
            {
                "execution_order": row["execution_order"],
                "batch_packet_order": row["batch_packet_order"],
                "task_type": row["task_type"],
                "source_family": row["source_family"],
                "display_name": row["display_label"] if "display_label" in row else row["display_name"],
                "support_status": row["support_status"],
                "recommended_packet_action": row["recommended_packet_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Person enrichment execution batch packets expose per-readiness execution work without accepting collector or reviewer outputs as facts.",
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
    print(dumps({"person_enrichment_execution_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
