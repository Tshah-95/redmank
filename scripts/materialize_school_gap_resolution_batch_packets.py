#!/usr/bin/env python3
"""Expand school gap-resolution batches back to row-level packets."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"

MANIFEST_CSV = ARTIFACTS / "school_gap_resolution_manifest.csv"
BATCH_CSV = ARTIFACTS / "school_gap_resolution_batches.csv"
CSV_OUT = ARTIFACTS / "school_gap_resolution_batch_packets.csv"
JSON_OUT = ARTIFACTS / "school_gap_resolution_batch_packets.json"
SUMMARY_OUT = ARTIFACTS / "school_gap_resolution_batch_packet_summary.json"

MAX_GAPS_PER_BATCH = 25

FIELDS = [
    "school_gap_resolution_batch_packet_key",
    "school_gap_resolution_batch_key",
    "execution_order",
    "batch_packet_order",
    "gap_key",
    "school_key",
    "school_name",
    "sponsoring_institution",
    "program_key",
    "program_name",
    "program_type",
    "department_or_group",
    "gap_status",
    "coverage_status",
    "action_lane",
    "blocker_status",
    "resolution_category",
    "resolution_priority",
    "batch_status",
    "packet_status",
    "support_status",
    "denominator_url",
    "best_evidence_url",
    "best_evidence_title",
    "best_evidence_status",
    "supported_person_rows",
    "candidate_source_count",
    "approved_non_mutating_disposition_count",
    "recommended_next_action",
    "recommended_packet_action",
    "next_operator_lane",
    "target_artifact",
    "required_next_evidence",
    "mutation_policy",
    "gbrain_strategy_effect",
    "gbrain_packet_required_for",
    "source_artifacts_json",
    "gap_evidence_json",
    "batch_evidence_json",
    "evidence_json",
    "generated_at",
]

csv.field_size_limit(sys.maxsize)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def packet_key(batch_key: str, gap_key: str) -> str:
    return "school_gap_resolution_batch_packet_" + sha256_text(f"{batch_key}|{gap_key}")[:20]


def school_rank(school_name: str) -> int:
    if school_name == "STANFORD UNIVERSITY SCH OF MEDICINE":
        return 0
    if school_name == "VANDERBILT UNIVERSITY SCH OF MEDICINE":
        return 1
    return 9


def batch_key(parts: object) -> str:
    return "school_gap_resolution_batch_" + sha256_text(dumps(parts))[:20]


def batch_lookup(manifest_rows: list[dict[str, str]]) -> dict[str, str]:
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in manifest_rows:
        grouped[(row.get("school_name", ""), row.get("next_operator_lane", ""), row.get("resolution_category", ""))].append(row)

    lookup: dict[str, str] = {}
    for (school_name, lane, category), rows in grouped.items():
        ordered = sorted(rows, key=lambda item: (-as_int(item.get("resolution_priority")), item.get("program_name", ""), item.get("gap_key", "")))
        for chunk_index, offset in enumerate(range(0, len(ordered), MAX_GAPS_PER_BATCH), start=1):
            chunk = ordered[offset : offset + MAX_GAPS_PER_BATCH]
            gap_keys = [row["gap_key"] for row in chunk]
            key = batch_key((school_name, lane, category, chunk_index, gap_keys))
            for row in chunk:
                lookup[row["gap_key"]] = key
    return lookup


def packet_status(row: dict[str, str]) -> str:
    category = row.get("resolution_category", "")
    if "parser" in category:
        return "parser_or_manual_review_gap_packet"
    if "shared_source" in category:
        return "shared_source_gap_packet"
    if "related_scope" in category:
        return "related_scope_gap_packet"
    if "source_discovery" in category:
        return "source_discovery_gap_packet"
    if "url" in category:
        return "url_repair_gap_packet"
    if "route" in category:
        return "route_inspection_gap_packet"
    return "school_gap_resolution_packet"


def support_status(row: dict[str, str]) -> str:
    if as_int(row.get("supported_person_rows")) > 0:
        return "has_supported_person_structure_but_mutation_blocked"
    if as_int(row.get("candidate_source_count")) > 0:
        return "has_candidate_source_needs_probe_or_review"
    if as_int(row.get("approved_non_mutating_disposition_count")) > 0:
        return "has_non_mutating_disposition_evidence_but_closure_blocked"
    return "needs_source_discovery_or_closure_evidence"


def recommended_packet_action(row: dict[str, str], batch: dict[str, str]) -> str:
    return row.get("recommended_next_action") or batch.get("recommended_operator_action") or "review_gap_resolution_packet"


def build_rows(generated_at: str) -> list[dict[str, object]]:
    manifest_rows = read_csv(MANIFEST_CSV)
    batches = {row["school_gap_resolution_batch_key"]: row for row in read_csv(BATCH_CSV)}
    lookup = batch_lookup(manifest_rows)
    missing = sorted(set(lookup.values()) - set(batches))
    if missing:
        raise SystemExit(f"missing school gap resolution batches: {len(missing)}")

    packet_orders: Counter[str] = Counter()
    output: list[dict[str, object]] = []
    for row in sorted(manifest_rows, key=lambda item: (school_rank(item.get("school_name", "")), -as_int(item.get("resolution_priority")), item.get("program_name", ""), item.get("gap_key", ""))):
        gap_key = row["gap_key"]
        batch_id = lookup.get(gap_key)
        if not batch_id:
            raise SystemExit(f"missing batch for gap {gap_key}")
        batch = batches[batch_id]
        packet_orders[batch_id] += 1
        evidence = {
            "gap_key": gap_key,
            "school_gap_resolution_batch_key": batch_id,
            "manifest_source": "artifacts/data/school_gap_resolution_manifest.csv",
            "batch_source": "artifacts/data/school_gap_resolution_batches.csv",
            "non_mutating_boundary": {
                "person_ingestion_allowed": False,
                "training_state_mutation_allowed": False,
                "denominator_closure_allowed": False,
                "school_verification_allowed": False,
                "url_rewrite_allowed": False,
                "identity_collapse_allowed": False,
            },
        }
        output.append(
            {
                "school_gap_resolution_batch_packet_key": packet_key(batch_id, gap_key),
                "school_gap_resolution_batch_key": batch_id,
                "execution_order": batch.get("execution_order", ""),
                "batch_packet_order": packet_orders[batch_id],
                "gap_key": gap_key,
                "school_key": row.get("school_key", ""),
                "school_name": row.get("school_name", ""),
                "sponsoring_institution": row.get("sponsoring_institution", ""),
                "program_key": row.get("program_key", ""),
                "program_name": row.get("program_name", ""),
                "program_type": row.get("program_type", ""),
                "department_or_group": row.get("department_or_group", ""),
                "gap_status": row.get("gap_status", ""),
                "coverage_status": row.get("coverage_status", ""),
                "action_lane": row.get("action_lane", ""),
                "blocker_status": row.get("blocker_status", ""),
                "resolution_category": row.get("resolution_category", ""),
                "resolution_priority": row.get("resolution_priority", ""),
                "batch_status": batch.get("batch_status", ""),
                "packet_status": packet_status(row),
                "support_status": support_status(row),
                "denominator_url": row.get("denominator_url", ""),
                "best_evidence_url": row.get("best_evidence_url", ""),
                "best_evidence_title": row.get("best_evidence_title", ""),
                "best_evidence_status": row.get("best_evidence_status", ""),
                "supported_person_rows": row.get("supported_person_rows", ""),
                "candidate_source_count": row.get("candidate_source_count", ""),
                "approved_non_mutating_disposition_count": row.get("approved_non_mutating_disposition_count", ""),
                "recommended_next_action": row.get("recommended_next_action", ""),
                "recommended_packet_action": recommended_packet_action(row, batch),
                "next_operator_lane": row.get("next_operator_lane", ""),
                "target_artifact": batch.get("target_artifact", ""),
                "required_next_evidence": batch.get("required_next_evidence", ""),
                "mutation_policy": row.get("mutation_policy", ""),
                "gbrain_strategy_effect": row.get("gbrain_strategy_effect", ""),
                "gbrain_packet_required_for": row.get("gbrain_packet_required_for", ""),
                "source_artifacts_json": row.get("source_artifacts_json", "[]"),
                "gap_evidence_json": row.get("evidence_json", "{}"),
                "batch_evidence_json": batch.get("evidence_json", "{}"),
                "evidence_json": dumps(evidence),
                "generated_at": generated_at,
            }
        )
    return output


def build_summary(rows: list[dict[str, object]], generated_at: str) -> dict[str, object]:
    return {
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "generated_at": generated_at,
        "rows": len(rows),
        "batch_rows": len({row["school_gap_resolution_batch_key"] for row in rows}),
        "by_school": dict(Counter(str(row["school_name"]) for row in rows)),
        "by_packet_status": dict(Counter(str(row["packet_status"]) for row in rows)),
        "by_support_status": dict(Counter(str(row["support_status"]) for row in rows)),
        "mutation_allowed": False,
        "policy": "Row-level packets for non-mutating school gap-resolution batches. They carry exact gap evidence and mutation prohibitions forward to operator work.",
    }


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows(generated_at)
    summary = build_summary(rows, generated_at)
    write_csv(CSV_OUT, rows)
    write_json(JSON_OUT, rows)
    write_json(SUMMARY_OUT, summary)
    print(json.dumps({"school_gap_resolution_batch_packets": len(rows), "batch_rows": summary["batch_rows"], "by_school": summary["by_school"]}, sort_keys=True))


if __name__ == "__main__":
    main()
