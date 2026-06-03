#!/usr/bin/env python3
"""Materialize contract-level packets for temporal contract batches."""

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

BATCH_CSV = ARTIFACTS / "training_temporal_contract_batches.csv"
CONTRACT_CSV = ARTIFACTS / "training_temporal_contracts.csv"
CSV_PATH = ARTIFACTS / "training_temporal_contract_batch_packets.csv"
JSON_PATH = ARTIFACTS / "training_temporal_contract_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "training_temporal_contract_batch_packet_summary.json"

MAX_CONTRACTS_PER_BATCH = 50

FIELDS = [
    "training_temporal_contract_batch_packet_key",
    "temporal_contract_batch_key",
    "execution_order",
    "packet_order",
    "contract_key",
    "canonical_person_program_key",
    "person_key",
    "display_name",
    "role",
    "trainee_category",
    "program_name",
    "institution",
    "country",
    "country_code",
    "source_key",
    "observed_at",
    "as_of_date",
    "projected_refresh_date",
    "lifecycle_code",
    "current_stage_label",
    "current_stage_code",
    "stage_family",
    "stage_index",
    "stage_rank",
    "current_temporal_state_code",
    "temporal_validity_status",
    "policy_lane",
    "diff_readiness_status",
    "next_refresh_contract",
    "if_missing_change_type",
    "if_same_stage_change_type",
    "if_expected_next_stage_change_type",
    "stale_after_date",
    "stale_by_refresh",
    "advance_due_by_refresh",
    "completion_window_by_refresh",
    "source_refresh_required_by_refresh",
    "human_review_required_by_refresh",
    "auto_classifiable_transition",
    "fresh_observation_required",
    "confidence",
    "packet_status",
    "support_status",
    "recommended_operator_action",
    "required_next_evidence",
    "target_artifact",
    "allowed_auto_diff_outcomes_json",
    "review_trigger_json",
    "evidence_required_to_retain",
    "evidence_required_to_advance",
    "evidence_required_to_complete",
    "stale_information_policy",
    "contract_evidence_json",
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
    return "training_temporal_contract_batch_" + sha256_text(dumps(parts))[:20]


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
    return {row["training_temporal_contract_batch_packet_key"]: row for row in read_csv(CSV_PATH)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["training_temporal_contract_batch_packet_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def contract_sort_key(row: dict) -> tuple:
    return (
        -as_int(row.get("human_review_required_by_refresh")),
        -as_int(row.get("source_refresh_required_by_refresh")),
        row.get("display_name") or "",
        row.get("contract_key") or "",
    )


def batch_lookup(contract_rows: list[dict]) -> dict[str, str]:
    grouped: dict[tuple[str, str, str, str, str, str], list[dict]] = defaultdict(list)
    for row in contract_rows:
        lane = row.get("policy_lane") or ""
        if lane not in {"manual_review_required", "source_refresh_required"}:
            continue
        grouped[
            (
                lane,
                row.get("role") or "",
                row.get("trainee_category") or "",
                row.get("program_name") or "",
                row.get("lifecycle_code") or "",
                row.get("next_refresh_contract") or "",
            )
        ].append(row)

    output: dict[str, str] = {}
    for (lane, role, category, program, lifecycle, contract), rows in grouped.items():
        ordered = sorted(rows, key=contract_sort_key)
        for chunk_index, offset in enumerate(range(0, len(ordered), MAX_CONTRACTS_PER_BATCH), start=1):
            chunk = ordered[offset : offset + MAX_CONTRACTS_PER_BATCH]
            contract_keys = [row.get("contract_key") for row in chunk]
            key = batch_key((lane, role, category, program, lifecycle, contract, chunk_index, contract_keys))
            for row in chunk:
                output[row.get("contract_key") or ""] = key
    return output


def packet_status(policy_lane: str) -> str:
    if policy_lane == "manual_review_required":
        return "manual_temporal_contract_review_packet"
    return "source_refresh_temporal_contract_packet"


def support_status(policy_lane: str) -> str:
    if policy_lane == "manual_review_required":
        return "ready_for_lifecycle_or_source_label_review"
    return "ready_for_fresh_source_reobservation"


def required_next_evidence(contract: dict, batch: dict) -> str:
    if contract.get("evidence_required_to_retain"):
        return contract["evidence_required_to_retain"]
    return batch.get("required_next_evidence") or "Fresh public source observation or reviewer decision."


def target_artifact(contract: dict, batch: dict) -> str:
    if batch.get("target_artifact"):
        return batch["target_artifact"]
    if contract.get("policy_lane") == "manual_review_required":
        return "artifacts/data/training_state_transition_plan.csv"
    return "artifacts/data/training_states_current.csv"


def build_rows(generated_at: str) -> list[dict]:
    existing = read_existing()
    batches = read_csv(BATCH_CSV)
    contracts = read_csv(CONTRACT_CSV)
    batch_by_key = {row["temporal_contract_batch_key"]: row for row in batches}
    contract_to_batch = batch_lookup(contracts)

    missing_batch_keys = sorted(set(contract_to_batch.values()) - set(batch_by_key))
    if missing_batch_keys:
        raise SystemExit(f"missing batch rows for {len(missing_batch_keys)} computed temporal batch keys")

    output = []
    packet_orders: Counter[str] = Counter()
    for contract in sorted(contracts, key=contract_sort_key):
        lane = contract.get("policy_lane") or ""
        if lane not in {"manual_review_required", "source_refresh_required"}:
            continue
        contract_key = contract.get("contract_key") or ""
        batch_id = contract_to_batch.get(contract_key)
        if not batch_id:
            raise SystemExit(f"missing temporal batch membership for contract {contract_key}")
        batch = batch_by_key[batch_id]
        packet_orders[batch_id] += 1
        evidence = {
            "temporal_contract_batch_key": batch_id,
            "contract_key": contract_key,
            "policy_lane": lane,
            "next_refresh_contract": contract.get("next_refresh_contract"),
            "allowed_auto_diff_outcomes": parse_json(contract.get("allowed_auto_diff_outcomes_json"), []),
            "review_triggers": parse_json(contract.get("review_trigger_json"), []),
            "non_mutating_policy": {
                "truth_changes_require": [
                    "fresh public source observation",
                    "transition-plan diff classification",
                    "reviewer resolution for manual-review lanes",
                ],
                "packet_role": "row-level evidence for a bounded temporal contract batch",
            },
        }
        row = {
            "training_temporal_contract_batch_packet_key": "training_temporal_contract_batch_packet_"
            + stable_key(batch_id, contract_key),
            "temporal_contract_batch_key": batch_id,
            "execution_order": batch.get("execution_order") or "0",
            "packet_order": packet_orders[batch_id],
            "contract_key": contract_key,
            "canonical_person_program_key": contract.get("canonical_person_program_key") or "",
            "person_key": contract.get("person_key") or "",
            "display_name": contract.get("display_name") or "",
            "role": contract.get("role") or "",
            "trainee_category": contract.get("trainee_category") or "",
            "program_name": contract.get("program_name") or "",
            "institution": contract.get("institution") or "",
            "country": contract.get("country") or "",
            "country_code": contract.get("country_code") or "",
            "source_key": contract.get("source_key") or "",
            "observed_at": contract.get("observed_at") or "",
            "as_of_date": contract.get("as_of_date") or "",
            "projected_refresh_date": contract.get("projected_refresh_date") or "",
            "lifecycle_code": contract.get("lifecycle_code") or "",
            "current_stage_label": contract.get("current_stage_label") or "",
            "current_stage_code": contract.get("current_stage_code") or "",
            "stage_family": contract.get("stage_family") or "",
            "stage_index": contract.get("stage_index") or "",
            "stage_rank": contract.get("stage_rank") or "",
            "current_temporal_state_code": contract.get("current_temporal_state_code") or "",
            "temporal_validity_status": contract.get("temporal_validity_status") or "",
            "policy_lane": lane,
            "diff_readiness_status": contract.get("diff_readiness_status") or "",
            "next_refresh_contract": contract.get("next_refresh_contract") or "",
            "if_missing_change_type": contract.get("if_missing_change_type") or "",
            "if_same_stage_change_type": contract.get("if_same_stage_change_type") or "",
            "if_expected_next_stage_change_type": contract.get("if_expected_next_stage_change_type") or "",
            "stale_after_date": contract.get("stale_after_date") or "",
            "stale_by_refresh": as_int(contract.get("stale_by_refresh")),
            "advance_due_by_refresh": as_int(contract.get("advance_due_by_refresh")),
            "completion_window_by_refresh": as_int(contract.get("completion_window_by_refresh")),
            "source_refresh_required_by_refresh": as_int(contract.get("source_refresh_required_by_refresh")),
            "human_review_required_by_refresh": as_int(contract.get("human_review_required_by_refresh")),
            "auto_classifiable_transition": as_int(contract.get("auto_classifiable_transition")),
            "fresh_observation_required": as_int(contract.get("fresh_observation_required")),
            "confidence": as_float(contract.get("confidence")),
            "packet_status": packet_status(lane),
            "support_status": support_status(lane),
            "recommended_operator_action": contract.get("recommended_operator_action") or batch.get("recommended_operator_action") or "",
            "required_next_evidence": required_next_evidence(contract, batch),
            "target_artifact": target_artifact(contract, batch),
            "allowed_auto_diff_outcomes_json": dumps(parse_json(contract.get("allowed_auto_diff_outcomes_json"), [])),
            "review_trigger_json": dumps(parse_json(contract.get("review_trigger_json"), [])),
            "evidence_required_to_retain": contract.get("evidence_required_to_retain") or "",
            "evidence_required_to_advance": contract.get("evidence_required_to_advance") or "",
            "evidence_required_to_complete": contract.get("evidence_required_to_complete") or "",
            "stale_information_policy": contract.get("stale_information_policy") or "",
            "contract_evidence_json": dumps(parse_json(contract.get("evidence_json"), {})),
            "batch_evidence_json": dumps(parse_json(batch.get("evidence_json"), {})),
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        output.append({field: row[field] for field in FIELDS})

    expected_counts = Counter(contract_to_batch.values())
    actual_counts = Counter(row["temporal_contract_batch_key"] for row in output)
    mismatches = [
        key
        for key, batch in batch_by_key.items()
        if expected_counts[key] != as_int(batch.get("contract_count")) or actual_counts[key] != as_int(batch.get("contract_count"))
    ]
    if mismatches:
        raise SystemExit(f"temporal batch packet count mismatch for {len(mismatches)} batches")

    output.sort(key=lambda row: (as_int(row["execution_order"]), as_int(row["packet_order"]), row["contract_key"]))
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DELETE FROM training_temporal_contract_batch_packets")
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO training_temporal_contract_batch_packets ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "batch_rows": len({row["temporal_contract_batch_key"] for row in rows}),
        "contract_rows": len({row["contract_key"] for row in rows}),
        "person_count": len({row["person_key"] for row in rows if row["person_key"]}),
        "source_count": len({row["source_key"] for row in rows if row["source_key"]}),
        "stale_by_refresh_count": sum(as_int(row["stale_by_refresh"]) for row in rows),
        "fresh_observation_required_count": sum(as_int(row["fresh_observation_required"]) for row in rows),
        "source_refresh_required_count": sum(as_int(row["source_refresh_required_by_refresh"]) for row in rows),
        "human_review_required_count": sum(as_int(row["human_review_required_by_refresh"]) for row in rows),
        "by_policy_lane": dict(sorted(Counter(row["policy_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "top_packets": [
            {
                "execution_order": row["execution_order"],
                "packet_order": row["packet_order"],
                "contract_key": row["contract_key"],
                "display_name": row["display_name"],
                "program_name": row["program_name"],
                "role": row["role"],
                "policy_lane": row["policy_lane"],
                "support_status": row["support_status"],
            }
            for row in rows[:25]
        ],
        "policy": "Temporal contract batch packets are non-mutating row-level evidence. They expose every source-refresh and manual-review contract that belongs to each bounded operator batch before any training-state mutation.",
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
    print(dumps({"training_temporal_contract_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
