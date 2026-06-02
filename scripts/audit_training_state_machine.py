#!/usr/bin/env python3
"""Audit lifecycle/staleness semantics for current training-state observations."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"


STATUS_PRIORITY = {
    "stale_now": 100,
    "ready_for_expected_advancement": 90,
    "review_required": 80,
    "source_refresh_required": 60,
    "terminal_year_active": 50,
    "annual_clock_active": 30,
    "current_observation": 10,
}


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def days_between(left: date | None, right: date) -> int | None:
    if left is None:
        return None
    return (left - right).days


def clock_model(row: dict) -> str:
    role = row.get("role") or ""
    stage_family = row.get("stage_family") or ""
    refresh_policy = row.get("refresh_policy") or ""
    transition_type = row.get("expected_transition_type") or ""
    if refresh_policy == "review_required" or transition_type.endswith("_review"):
        return "review_required"
    if refresh_policy == "source_refresh_required":
        return "source_refresh_required"
    if role in {"resident", "fellow"} and refresh_policy == "annual_clock":
        return "annual_gme_july"
    if role == "medical_student" or stage_family == "medical_school":
        return "annual_medical_school_august"
    return refresh_policy or "refresh_from_source"


def classify(row: dict, as_of: date) -> tuple[str, str, str]:
    stale_after = parse_date(row.get("stale_after_date"))
    expected_next = parse_date(row.get("expected_next_date"))
    transition_type = row.get("expected_transition_type") or ""
    refresh_policy = row.get("refresh_policy") or ""
    if stale_after and stale_after <= as_of:
        return (
            "stale_now",
            "Source observation has passed stale_after_date; rerun source before retaining, advancing, or removing.",
            "refresh_source_and_reconcile",
        )
    if transition_type == "expected_annual_advancement" and expected_next and expected_next <= as_of:
        return (
            "ready_for_expected_advancement",
            "Annual-clock state is past expected_next_date but not yet stale.",
            "advance_if_same_person_program_is_still_observed",
        )
    if refresh_policy == "review_required" or transition_type.endswith("_review"):
        return (
            "review_required",
            "Stage does not fit nominal lifecycle assumptions and should not be auto-mutated.",
            "review_lifecycle_rule_or_source_label",
        )
    if transition_type == "expected_completion":
        return (
            "terminal_year_active",
            "Terminal-year state can disappear after stale_after_date as expected completion.",
            "mark_completion_or_alumni_if_absent_after_stale_after",
        )
    if refresh_policy == "source_refresh_required":
        return (
            "source_refresh_required",
            "State duration is individualized or source-ambiguous; refresh source instead of auto-advancing.",
            "refresh_source_before_mutation",
        )
    if transition_type == "expected_annual_advancement":
        return (
            "annual_clock_active",
            "State has an annual clock and a known expected next stage/date.",
            "wait_until_expected_next_date_then_reconcile",
        )
    return (
        "current_observation",
        "Current state has no special clock action due today.",
        "retain_until_next_refresh",
    )


def health_rank(status: str) -> int:
    return STATUS_PRIORITY.get(status, 0)


def read_state_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT state_id, person_key, display_name, role, program_name,
                   observed_at, as_of_date, raw_stage_label, normalized_stage,
                   stage_family, stage_index, stage_rank, trainee_category,
                   lifecycle_rule_key, lifecycle_code, lifecycle_stage,
                   academic_year, estimated_start_date, estimated_end_date,
                   expected_next_stage, expected_next_date, expected_exit_date,
                   expected_transition_type, stale_after_date, refresh_policy,
                   transition_rule, status, confidence, source_key
            FROM v_current_training_states
            ORDER BY display_name, program_name, stage_rank, raw_stage_label
            """
        )
    ]


def enrich_state_rows(rows: list[dict], as_of: date) -> list[dict]:
    enriched = []
    for row in rows:
        status, reason, action = classify(row, as_of)
        stale_after = parse_date(row.get("stale_after_date"))
        expected_next = parse_date(row.get("expected_next_date"))
        enriched.append(
            {
                **row,
                "audit_as_of_date": as_of.isoformat(),
                "clock_model": clock_model(row),
                "state_machine_status": status,
                "state_machine_reason": reason,
                "recommended_action": action,
                "days_until_expected_next": days_between(expected_next, as_of),
                "days_until_stale": days_between(stale_after, as_of),
                "auto_advance_candidate": int(
                    status in {"annual_clock_active", "ready_for_expected_advancement"}
                    and bool(row.get("expected_next_stage"))
                ),
                "completion_candidate": int(row.get("expected_transition_type") == "expected_completion"),
            }
        )
    return enriched


def choose_worst(rows: list[dict]) -> dict:
    return max(rows, key=lambda row: (health_rank(row["state_machine_status"]), row.get("stage_rank") or 0))


def person_rollups(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["person_key"]].append(row)
    result = []
    for person_key, person_rows in grouped.items():
        worst = choose_worst(person_rows)
        programs = sorted({row.get("program_name") or "" for row in person_rows if row.get("program_name")})
        statuses = Counter(row["state_machine_status"] for row in person_rows)
        comparison_keys = {(row["person_key"], row.get("program_name") or "") for row in person_rows}
        concurrent_stage_keys = Counter((row["person_key"], row.get("program_name") or "") for row in person_rows)
        result.append(
            {
                "person_key": person_key,
                "display_name": worst.get("display_name", ""),
                "role": worst.get("role", ""),
                "program_count": len(programs),
                "programs": "; ".join(programs),
                "state_observation_count": len(person_rows),
                "canonical_diff_key_count": len(comparison_keys),
                "duplicate_state_key_count": sum(1 for count in concurrent_stage_keys.values() if count > 1),
                "worst_state_machine_status": worst["state_machine_status"],
                "worst_clock_model": worst["clock_model"],
                "worst_program_name": worst.get("program_name", ""),
                "worst_normalized_stage": worst.get("normalized_stage", ""),
                "stale_state_count": statuses.get("stale_now", 0),
                "ready_for_expected_advancement_count": statuses.get("ready_for_expected_advancement", 0),
                "review_required_count": statuses.get("review_required", 0),
                "source_refresh_required_count": statuses.get("source_refresh_required", 0),
                "annual_clock_active_count": statuses.get("annual_clock_active", 0),
                "terminal_year_active_count": statuses.get("terminal_year_active", 0),
                "recommended_action": worst["recommended_action"],
            }
        )
    return sorted(result, key=lambda row: (-health_rank(row["worst_state_machine_status"]), row["role"], row["display_name"]))


def program_rollups(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("program_name") or "Unassigned Program", row.get("role") or "")].append(row)
    result = []
    for (program_name, role), program_rows in grouped.items():
        worst = choose_worst(program_rows)
        statuses = Counter(row["state_machine_status"] for row in program_rows)
        clocks = Counter(row["clock_model"] for row in program_rows)
        lifecycle_codes = Counter(row.get("lifecycle_code") or "none" for row in program_rows)
        people = {row["person_key"] for row in program_rows}
        result.append(
            {
                "program_name": program_name,
                "role": role,
                "person_count": len(people),
                "state_observation_count": len(program_rows),
                "dominant_lifecycle_code": lifecycle_codes.most_common(1)[0][0],
                "dominant_clock_model": clocks.most_common(1)[0][0],
                "worst_state_machine_status": worst["state_machine_status"],
                "stale_state_count": statuses.get("stale_now", 0),
                "ready_for_expected_advancement_count": statuses.get("ready_for_expected_advancement", 0),
                "review_required_count": statuses.get("review_required", 0),
                "source_refresh_required_count": statuses.get("source_refresh_required", 0),
                "annual_clock_active_count": statuses.get("annual_clock_active", 0),
                "terminal_year_active_count": statuses.get("terminal_year_active", 0),
                "recommended_action": worst["recommended_action"],
            }
        )
    return sorted(result, key=lambda row: (-health_rank(row["worst_state_machine_status"]), row["role"], row["program_name"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db_table(conn: sqlite3.Connection, table: str, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    columns = list(rows[0].keys())
    placeholders = ", ".join(f":{column}" for column in columns)
    column_sql = ", ".join(columns)
    conn.executemany(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        rows,
    )


def summary_payload(state_rows: list[dict], person_rows: list[dict], program_rows: list[dict], as_of: date) -> dict:
    status_counts = Counter(row["state_machine_status"] for row in state_rows)
    clock_counts = Counter(row["clock_model"] for row in state_rows)
    role_status_counts = Counter(f"{row.get('role') or ''}:{row['state_machine_status']}" for row in state_rows)
    lifecycle_status_counts = Counter(
        f"{row.get('lifecycle_code') or 'none'}:{row['state_machine_status']}" for row in state_rows
    )
    next_actions = Counter(row["recommended_action"] for row in state_rows)
    return {
        "generated_as_of_date": as_of.isoformat(),
        "state_rows": len(state_rows),
        "person_rows": len(person_rows),
        "program_rows": len(program_rows),
        "by_state_machine_status": dict(sorted(status_counts.items())),
        "by_clock_model": dict(sorted(clock_counts.items())),
        "by_role_and_status": dict(sorted(role_status_counts.items())),
        "by_lifecycle_code_and_status": dict(sorted(lifecycle_status_counts.items())),
        "by_recommended_action": dict(sorted(next_actions.items())),
        "stale_or_review_state_rows": sum(
            status_counts[status] for status in ["stale_now", "ready_for_expected_advancement", "review_required"]
        ),
        "auto_advance_candidate_rows": sum(row["auto_advance_candidate"] for row in state_rows),
        "completion_candidate_rows": sum(row["completion_candidate"] for row in state_rows),
        "person_rollup_csv": "artifacts/data/person_training_state_machine_audit.csv",
        "program_rollup_csv": "artifacts/data/program_training_state_machine_audit.csv",
        "state_audit_csv": "artifacts/data/training_state_machine_audit.csv",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--as-of-date", default=date.today().isoformat())
    args = parser.parse_args()

    as_of = date.fromisoformat(args.as_of_date)
    conn = sqlite3.connect(args.db)
    state_rows = enrich_state_rows(read_state_rows(conn), as_of)
    people = person_rollups(state_rows)
    programs = program_rollups(state_rows)
    summary = summary_payload(state_rows, people, programs, as_of)

    write_csv(ARTIFACTS / "training_state_machine_audit.csv", state_rows)
    write_csv(ARTIFACTS / "person_training_state_machine_audit.csv", people)
    write_csv(ARTIFACTS / "program_training_state_machine_audit.csv", programs)
    with conn:
        write_db_table(conn, "training_state_machine_audit", state_rows)
        write_db_table(conn, "person_training_state_machine_audit", people)
        write_db_table(conn, "program_training_state_machine_audit", programs)
    conn.close()
    (ARTIFACTS / "training_state_machine_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
