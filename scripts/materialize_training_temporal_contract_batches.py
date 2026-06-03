#!/usr/bin/env python3
"""Materialize bounded operator batches for training temporal contracts."""

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

CSV_PATH = ARTIFACTS / "training_temporal_contract_batches.csv"
JSON_PATH = ARTIFACTS / "training_temporal_contract_batches.json"
SUMMARY_PATH = ARTIFACTS / "training_temporal_contract_batch_summary.json"

MAX_CONTRACTS_PER_BATCH = 50

FIELDS = [
    "temporal_contract_batch_key",
    "execution_order",
    "policy_lane",
    "batch_status",
    "ready_to_execute",
    "role",
    "trainee_category",
    "program_name",
    "lifecycle_code",
    "next_refresh_contract",
    "diff_readiness_status_signature",
    "temporal_state_signature",
    "contract_count",
    "person_count",
    "program_count",
    "source_count",
    "stale_by_refresh_count",
    "fresh_observation_required_count",
    "source_refresh_required_count",
    "human_review_required_count",
    "auto_classifiable_transition_count",
    "expected_advancement_count",
    "expected_completion_count",
    "max_confidence",
    "min_confidence",
    "top_people",
    "top_sources",
    "diff_readiness_counts_json",
    "temporal_state_counts_json",
    "stage_code_counts_json",
    "recommended_operator_action",
    "execution_instructions",
    "required_next_evidence",
    "target_artifact",
    "top_contracts_json",
    "review_triggers_json",
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


def parse_json(value: str | None, default):
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
        return {row["temporal_contract_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["temporal_contract_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def batch_key(parts: tuple[object, ...]) -> str:
    return "training_temporal_contract_batch_" + sha256_text(dumps(parts))[:20]


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def batch_status(policy_lane: str) -> str:
    return {
        "manual_review_required": "temporal_manual_review_ready",
        "source_refresh_required": "temporal_source_refresh_ready",
    }.get(policy_lane, "temporal_contract_review_ready")


def recommended_action(policy_lane: str) -> str:
    return {
        "manual_review_required": "review_lifecycle_or_source_label_contract_batch_before_mutation",
        "source_refresh_required": "refresh_source_observations_for_temporal_contract_batch",
    }.get(policy_lane, "review_temporal_contract_batch")


def execution_instructions(policy_lane: str) -> str:
    if policy_lane == "manual_review_required":
        return "Resolve lifecycle/source-label ambiguity before any retain, advance, complete, or remove mutation is allowed."
    if policy_lane == "source_refresh_required":
        return "Collect fresh public roster/profile observations for the same person/program/state label before retaining, advancing, or removing the state."
    return "Review the temporal contract batch without mutating person/program state outside the transition-plan and diff ledgers."


def required_next_evidence(rows: list[dict], policy_lane: str) -> str:
    if policy_lane == "manual_review_required":
        return "Reviewer-resolved lifecycle/source-label decision plus fresh public source evidence."
    evidence = Counter(row.get("evidence_required_to_retain") or "" for row in rows)
    if evidence:
        return evidence.most_common(1)[0][0]
    return "Fresh public source observation or explicit reviewer decision tied to the temporal contract key."


def target_artifact(policy_lane: str) -> str:
    if policy_lane == "manual_review_required":
        return "artifacts/data/training_state_transition_plan.csv"
    return "artifacts/data/training_states_current.csv"


def top_contracts(rows: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in sorted(
        rows,
        key=lambda item: (
            -as_int(item.get("human_review_required_by_refresh")),
            -as_int(item.get("source_refresh_required_by_refresh")),
            item.get("display_name") or "",
            item.get("contract_key") or "",
        ),
    )[:limit]:
        output.append(
            {
                "contract_key": row.get("contract_key"),
                "person_key": row.get("person_key"),
                "display_name": row.get("display_name"),
                "role": row.get("role"),
                "program_name": row.get("program_name"),
                "current_stage_code": row.get("current_stage_code"),
                "policy_lane": row.get("policy_lane"),
                "diff_readiness_status": row.get("diff_readiness_status"),
                "next_refresh_contract": row.get("next_refresh_contract"),
                "stale_after_date": row.get("stale_after_date"),
                "confidence": as_float(row.get("confidence")),
            }
        )
    return output


def merged_review_triggers(rows: list[dict]) -> list[str]:
    triggers: Counter = Counter()
    for row in rows:
        for trigger in parse_json(row.get("review_trigger_json"), []):
            triggers[str(trigger)] += 1
    return [trigger for trigger, _ in triggers.most_common(20)]


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    contract_rows = sqlite_rows(
        conn,
        """
        SELECT *
        FROM training_temporal_contracts
        WHERE policy_lane IN ('manual_review_required', 'source_refresh_required')
        ORDER BY human_review_required_by_refresh DESC,
                 source_refresh_required_by_refresh DESC,
                 role,
                 program_name,
                 lifecycle_code,
                 display_name,
                 contract_key
        """,
    )
    grouped: dict[tuple[str, str, str, str, str, str], list[dict]] = defaultdict(list)
    for row in contract_rows:
        grouped[
            (
                row.get("policy_lane") or "",
                row.get("role") or "",
                row.get("trainee_category") or "",
                row.get("program_name") or "",
                row.get("lifecycle_code") or "",
                row.get("next_refresh_contract") or "",
            )
        ].append(row)

    output = []
    for (lane, role, category, program, lifecycle, contract), rows in grouped.items():
        ordered = sorted(
            rows,
            key=lambda item: (
                -as_int(item.get("human_review_required_by_refresh")),
                -as_int(item.get("source_refresh_required_by_refresh")),
                item.get("display_name") or "",
                item.get("contract_key") or "",
            ),
        )
        for chunk_index, offset in enumerate(range(0, len(ordered), MAX_CONTRACTS_PER_BATCH), start=1):
            chunk = ordered[offset : offset + MAX_CONTRACTS_PER_BATCH]
            contract_keys = [row.get("contract_key") for row in chunk]
            confidences = [as_float(row.get("confidence")) for row in chunk]
            diff_counts = Counter(row.get("diff_readiness_status") or "" for row in chunk)
            temporal_counts = Counter(row.get("current_temporal_state_code") or "" for row in chunk)
            stage_counts = Counter(row.get("current_stage_code") or "" for row in chunk)
            source_counts = Counter(row.get("source_key") or "" for row in chunk if row.get("source_key"))
            status = batch_status(lane)
            row = {
                "temporal_contract_batch_key": batch_key(
                    (lane, role, category, program, lifecycle, contract, chunk_index, contract_keys)
                ),
                "execution_order": 0,
                "policy_lane": lane,
                "batch_status": status,
                "ready_to_execute": 1,
                "role": role,
                "trainee_category": category,
                "program_name": program,
                "lifecycle_code": lifecycle,
                "next_refresh_contract": contract,
                "diff_readiness_status_signature": diff_counts.most_common(1)[0][0] if diff_counts else "",
                "temporal_state_signature": temporal_counts.most_common(1)[0][0] if temporal_counts else "",
                "contract_count": len(chunk),
                "person_count": len({row.get("person_key") for row in chunk if row.get("person_key")}),
                "program_count": len({row.get("program_name") for row in chunk if row.get("program_name")}),
                "source_count": len(source_counts),
                "stale_by_refresh_count": sum(as_int(row.get("stale_by_refresh")) for row in chunk),
                "fresh_observation_required_count": sum(as_int(row.get("fresh_observation_required")) for row in chunk),
                "source_refresh_required_count": sum(as_int(row.get("source_refresh_required_by_refresh")) for row in chunk),
                "human_review_required_count": sum(as_int(row.get("human_review_required_by_refresh")) for row in chunk),
                "auto_classifiable_transition_count": sum(as_int(row.get("auto_classifiable_transition")) for row in chunk),
                "expected_advancement_count": sum(as_int(row.get("advance_due_by_refresh")) for row in chunk),
                "expected_completion_count": sum(as_int(row.get("completion_window_by_refresh")) for row in chunk),
                "max_confidence": max(confidences) if confidences else 0.0,
                "min_confidence": min(confidences) if confidences else 0.0,
                "top_people": "; ".join(row.get("display_name") or "" for row in chunk[:12]),
                "top_sources": "; ".join(source for source, _ in source_counts.most_common(12)),
                "diff_readiness_counts_json": dumps(dict(sorted(diff_counts.items()))),
                "temporal_state_counts_json": dumps(dict(sorted(temporal_counts.items()))),
                "stage_code_counts_json": dumps(dict(sorted(stage_counts.items()))),
                "recommended_operator_action": recommended_action(lane),
                "execution_instructions": execution_instructions(lane),
                "required_next_evidence": required_next_evidence(chunk, lane),
                "target_artifact": target_artifact(lane),
                "top_contracts_json": dumps(top_contracts(chunk)),
                "review_triggers_json": dumps(merged_review_triggers(chunk)),
                "evidence_json": dumps(
                    {
                        "contract_keys": contract_keys,
                        "policy_lane": lane,
                        "next_refresh_contract": contract,
                        "diff_readiness_counts": dict(sorted(diff_counts.items())),
                        "temporal_state_counts": dict(sorted(temporal_counts.items())),
                        "stage_code_counts": dict(sorted(stage_counts.items())),
                        "review_triggers": merged_review_triggers(chunk),
                        "policy": {
                            "non_mutating": True,
                            "truth_changes_require": [
                                "fresh public source observation",
                                "transition-plan diff classification",
                                "reviewer resolution for manual-review lanes",
                            ],
                        },
                    }
                ),
                "generated_at": generated_at,
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            output.append({field: row[field] for field in FIELDS})

    output.sort(
        key=lambda item: (
            0 if item["policy_lane"] == "manual_review_required" else 1,
            -as_int(item["human_review_required_count"]),
            -as_int(item["source_refresh_required_count"]),
            item["role"],
            item["program_name"],
            item["temporal_contract_batch_key"],
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
    conn.execute("DROP TABLE IF EXISTS training_temporal_contract_batches")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO training_temporal_contract_batches ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "contract_count": sum(as_int(row["contract_count"]) for row in rows),
        "person_count": sum(as_int(row["person_count"]) for row in rows),
        "stale_by_refresh_count": sum(as_int(row["stale_by_refresh_count"]) for row in rows),
        "fresh_observation_required_count": sum(as_int(row["fresh_observation_required_count"]) for row in rows),
        "source_refresh_required_count": sum(as_int(row["source_refresh_required_count"]) for row in rows),
        "human_review_required_count": sum(as_int(row["human_review_required_count"]) for row in rows),
        "auto_classifiable_transition_count": sum(as_int(row["auto_classifiable_transition_count"]) for row in rows),
        "by_policy_lane": dict(sorted(Counter(row["policy_lane"] for row in rows).items())),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "by_lifecycle_code": dict(sorted(Counter(row["lifecycle_code"] for row in rows).items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "policy_lane": row["policy_lane"],
                "batch_status": row["batch_status"],
                "role": row["role"],
                "program_name": row["program_name"],
                "lifecycle_code": row["lifecycle_code"],
                "contract_count": row["contract_count"],
                "person_count": row["person_count"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Temporal contract batches are non-mutating operator sessions. They batch stale/source-refresh and manual-review contracts before any state diff can retain, advance, complete, or remove a trainee state.",
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
    print(dumps({"training_temporal_contract_batches": len(rows)}))


if __name__ == "__main__":
    main()
