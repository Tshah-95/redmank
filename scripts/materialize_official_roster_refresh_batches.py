#!/usr/bin/env python3
"""Materialize resumable execution batches for official roster refresh work."""

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
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "official_roster_refresh_batches.csv"
JSON_PATH = ARTIFACTS / "official_roster_refresh_batches.json"
SUMMARY_PATH = ARTIFACTS / "official_roster_refresh_batch_summary.json"

MAX_SOURCE_PROGRAMS_PER_BATCH = 12

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "roster_batch_key",
    "execution_order",
    "collector_hint",
    "parser_status",
    "batch_lane",
    "batch_status",
    "ready_to_execute",
    "blocked_reason",
    "source_domain",
    "source_count",
    "source_program_count",
    "program_count",
    "contract_count",
    "person_count",
    "role_counts_json",
    "program_counts_json",
    "refresh_lane_counts_json",
    "parser_status_counts_json",
    "expected_advancement_count",
    "expected_completion_count",
    "source_refresh_required_count",
    "manual_review_required_count",
    "stale_by_refresh_count",
    "fresh_observation_required_count",
    "auto_classifiable_transition_count",
    "max_refresh_priority",
    "min_refresh_priority",
    "command_hint",
    "execution_notes",
    "input_artifacts_json",
    "output_artifacts_json",
    "source_urls_json",
    "top_refresh_rows_json",
    "evidence_required",
    "acceptance_rule",
    "recency_policy",
    "provenance_policy",
    "recommended_next_action",
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


def source_domain(url: str) -> str:
    if not url:
        return "missing_source_url"
    parsed = urlparse(url)
    return parsed.netloc.lower() or "missing_source_url"


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["roster_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["roster_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def load_workbench(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM official_roster_refresh_workbench
            ORDER BY refresh_priority DESC, contract_count DESC, source_key, program_name, role
            """
        )
    ]


def batch_key(parts: tuple[object, ...]) -> str:
    return "official_roster_batch_" + sha256_text(dumps(parts))[:20]


def batch_lane(rows: list[dict]) -> str:
    lane_counts = Counter(row.get("refresh_lane") or "" for row in rows)
    if len(lane_counts) == 1:
        return next(iter(lane_counts))
    if any("manual" in lane for lane in lane_counts):
        return "mixed_refresh_with_manual_review"
    if any("source" in lane for lane in lane_counts) and any("expected" in lane for lane in lane_counts):
        return "mixed_expected_and_source_refresh"
    return "mixed_roster_refresh"


def status(rows: list[dict]) -> tuple[str, int, str]:
    if any(not (row.get("source_url") or "") for row in rows):
        return "blocked_missing_source_url", 0, "missing_source_url"
    parser_values = {row.get("parser_status") or "" for row in rows}
    if "parser_support_review_required" in parser_values:
        return "blocked_needs_parser_support_review", 0, "parser_support_review_required"
    if any(as_int(row.get("requires_manual_review")) for row in rows):
        return "network_refresh_then_manual_lifecycle_review", 1, ""
    return "network_refresh_ready", 1, ""


def recommended_action(batch_status: str, lane: str) -> str:
    if batch_status == "blocked_needs_parser_support_review":
        return "review_or_extend_parser_support_before_refreshing_this_batch"
    if batch_status == "blocked_missing_source_url":
        return "recover_official_source_url_before_refreshing_this_batch"
    if "manual" in lane:
        return "run_roster_collector_then_route_lifecycle_label_changes_to_review"
    if "expected_transition" in lane:
        return "run_roster_collector_then_compare_against_expected_advancement_or_completion"
    if "source_reobservation" in lane or "source_refresh" in lane:
        return "run_roster_collector_then_reconfirm_or_retire_source_bound_states"
    return "run_roster_collector_then_rebuild_state_machine_diff"


def command_hint(collector_hint: str) -> str:
    return collector_hint or "review_collector_for_batch"


def execution_notes(rows: list[dict], collector_hint: str) -> str:
    source_count = len({row.get("source_url") for row in rows if row.get("source_url")})
    return (
        f"Refresh {source_count} public source URL(s) with `{collector_hint}`. "
        "Current collectors are corpus-level unless extended with URL filtering, so this batch is an execution scope and audit packet, not a truth mutation. "
        "After collection, rebuild SQLite, rematerialize temporal contracts, and classify changes through snapshots/transition events."
    )


def top_refresh_rows(rows: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("refresh_priority")), item.get("program_name") or ""))[
        :limit
    ]:
        output.append(
            {
                "refresh_key": row.get("refresh_key"),
                "source_key": row.get("source_key"),
                "source_url": row.get("source_url"),
                "program_name": row.get("program_name"),
                "role": row.get("role"),
                "refresh_lane": row.get("refresh_lane"),
                "contract_count": as_int(row.get("contract_count")),
                "person_count": as_int(row.get("person_count")),
                "expected_change_summary": row.get("expected_change_summary"),
                "recommended_next_action": row.get("recommended_next_action"),
            }
        )
    return output


def build_batch_rows(workbench_rows: list[dict], generated_at: str) -> list[dict]:
    existing = read_existing()
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in workbench_rows:
        grouped[
            (
                row.get("collector_hint") or "",
                row.get("parser_status") or "",
                source_domain(row.get("source_url") or ""),
            )
        ].append(row)

    output = []
    for (collector, parser, domain), rows in grouped.items():
        sorted_rows = sorted(rows, key=lambda item: (-as_int(item.get("refresh_priority")), item.get("program_name") or ""))
        for chunk_index, offset in enumerate(range(0, len(sorted_rows), MAX_SOURCE_PROGRAMS_PER_BATCH), start=1):
            chunk = sorted_rows[offset : offset + MAX_SOURCE_PROGRAMS_PER_BATCH]
            lane = batch_lane(chunk)
            batch_status, ready, blocked = status(chunk)
            priorities = [as_int(row.get("refresh_priority")) for row in chunk]
            source_urls = sorted({row.get("source_url") or "" for row in chunk if row.get("source_url")})
            role_counts = Counter(row.get("role") or "" for row in chunk)
            program_counts = Counter(row.get("program_name") or "" for row in chunk if row.get("program_name"))
            refresh_lane_counts = Counter(row.get("refresh_lane") or "" for row in chunk)
            parser_counts = Counter(row.get("parser_status") or "" for row in chunk)
            evidence = {
                "derived_from": "official_roster_refresh_workbench",
                "batch_policy": (
                    "This is an execution scope for fresh public-source observation. It never mutates "
                    "person_training_states without a later state-machine diff, expected-transition policy, or reviewer gate."
                ),
                "collector_scope": {
                    "collector_hint": collector,
                    "parser_status": parser,
                    "source_domain": domain,
                    "source_program_limit": MAX_SOURCE_PROGRAMS_PER_BATCH,
                    "chunk_index": chunk_index,
                },
                "refresh_lane_counts": dict(sorted(refresh_lane_counts.items())),
                "parser_status_counts": dict(sorted(parser_counts.items())),
            }
            row = {
                "roster_batch_key": batch_key((collector, parser, domain, chunk_index, [item.get("refresh_key") for item in chunk])),
                "execution_order": 0,
                "collector_hint": collector,
                "parser_status": parser,
                "batch_lane": lane,
                "batch_status": batch_status,
                "ready_to_execute": ready,
                "blocked_reason": blocked,
                "source_domain": domain,
                "source_count": len(source_urls),
                "source_program_count": len(chunk),
                "program_count": len(program_counts),
                "contract_count": sum(as_int(item.get("contract_count")) for item in chunk),
                "person_count": sum(as_int(item.get("person_count")) for item in chunk),
                "role_counts_json": dumps(dict(sorted(role_counts.items()))),
                "program_counts_json": dumps(dict(program_counts.most_common(30))),
                "refresh_lane_counts_json": dumps(dict(sorted(refresh_lane_counts.items()))),
                "parser_status_counts_json": dumps(dict(sorted(parser_counts.items()))),
                "expected_advancement_count": sum(as_int(item.get("expected_advancement_count")) for item in chunk),
                "expected_completion_count": sum(as_int(item.get("expected_completion_count")) for item in chunk),
                "source_refresh_required_count": sum(as_int(item.get("source_refresh_required_count")) for item in chunk),
                "manual_review_required_count": sum(as_int(item.get("manual_review_required_count")) for item in chunk),
                "stale_by_refresh_count": sum(as_int(item.get("stale_by_refresh_count")) for item in chunk),
                "fresh_observation_required_count": sum(as_int(item.get("fresh_observation_required_count")) for item in chunk),
                "auto_classifiable_transition_count": sum(as_int(item.get("auto_classifiable_transition_count")) for item in chunk),
                "max_refresh_priority": max(priorities) if priorities else 0,
                "min_refresh_priority": min(priorities) if priorities else 0,
                "command_hint": command_hint(collector),
                "execution_notes": execution_notes(chunk, collector),
                "input_artifacts_json": dumps(["artifacts/data/official_roster_refresh_workbench.csv"]),
                "output_artifacts_json": dumps(
                    [
                        "artifacts/data/penn_training_people.csv",
                        "artifacts/data/penn_gme_gap_roster_people.csv",
                        "artifacts/data/penn_mstp_students.csv",
                        "artifacts/data/training_state_transition_events.csv",
                    ]
                ),
                "source_urls_json": dumps(source_urls),
                "top_refresh_rows_json": dumps(top_refresh_rows(chunk)),
                "evidence_required": "Fresh official roster observation, source URL, fetch/probe status, parser output, and state-machine transition classification before retaining, advancing, completing, or removing states.",
                "acceptance_rule": "Roster refresh output is accepted only through rebuilt people/states, temporal contracts, snapshot diff events, expected-transition policy, or explicit reviewer decisions for manual lifecycle/source-label changes.",
                "recency_policy": "Use fresh public source observation for the current refresh date; do not infer absence from transport errors, endpoint throttling, or parser structure loss.",
                "provenance_policy": "Preserve source URL, source key, fetch timestamp/status, parser status, prior source hash where available, and row-level transition evidence.",
                "recommended_next_action": recommended_action(batch_status, lane),
                "evidence_json": dumps(evidence),
                "generated_at": "",
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            output.append(row)

    output.sort(
        key=lambda item: (
            -as_int(item["ready_to_execute"]),
            -as_int(item["max_refresh_priority"]),
            -as_int(item["contract_count"]),
            item["collector_hint"],
            item["source_domain"],
            item["roster_batch_key"],
        )
    )
    for index, row in enumerate(output, start=1):
        row["execution_order"] = index
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_roster_refresh_batch_packets")
    conn.execute("DELETE FROM official_roster_refresh_batches")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO official_roster_refresh_batches ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_status = Counter(row["batch_status"] for row in rows)
    by_collector = Counter(row["collector_hint"] for row in rows)
    by_lane = Counter(row["batch_lane"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "ready_batch_rows": sum(as_int(row["ready_to_execute"]) for row in rows),
        "blocked_batch_rows": sum(1 for row in rows if not as_int(row["ready_to_execute"])),
        "source_count": sum(as_int(row["source_count"]) for row in rows),
        "source_program_count": sum(as_int(row["source_program_count"]) for row in rows),
        "contract_count": sum(as_int(row["contract_count"]) for row in rows),
        "person_count_policy": "Summed source/program person counts, not deduplicated unique people.",
        "expected_advancement_count": sum(as_int(row["expected_advancement_count"]) for row in rows),
        "expected_completion_count": sum(as_int(row["expected_completion_count"]) for row in rows),
        "source_refresh_required_count": sum(as_int(row["source_refresh_required_count"]) for row in rows),
        "manual_review_required_count": sum(as_int(row["manual_review_required_count"]) for row in rows),
        "by_batch_status": dict(sorted(by_status.items())),
        "by_collector": dict(sorted(by_collector.items())),
        "by_batch_lane": dict(sorted(by_lane.items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "collector_hint": row["collector_hint"],
                "batch_status": row["batch_status"],
                "batch_lane": row["batch_lane"],
                "source_domain": row["source_domain"],
                "source_program_count": row["source_program_count"],
                "contract_count": row["contract_count"],
                "max_refresh_priority": row["max_refresh_priority"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:20]
        ],
        "policy": (
            "This artifact batches official roster refresh work for execution. It is non-mutating and must feed "
            "fresh observations back through the state-machine diff and review gates before changing trainee state."
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
    rows = build_batch_rows(load_workbench(conn), generated_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"roster_refresh_batches": len(rows), "contract_count": sum(as_int(row["contract_count"]) for row in rows)}))


if __name__ == "__main__":
    main()
