#!/usr/bin/env python3
"""Project current training states into expected next-refresh change semantics."""

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


READINESS_PRIORITY = {
    "review_required_window": 100,
    "stale_without_transition_review": 95,
    "source_refresh_required_window": 85,
    "expected_completion_window": 70,
    "expected_advancement_window": 60,
    "terminal_active_before_completion": 40,
    "annual_clock_active_before_transition": 30,
    "active_no_change_expected": 10,
}


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def bool_int(value: bool) -> int:
    return 1 if value else 0


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
            ORDER BY role, program_name, display_name, stage_rank, raw_stage_label
            """
        )
    ]


def read_program_coverage(conn: sqlite3.Connection) -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    result = {}
    for row in conn.execute(
        """
        SELECT matched_program_name, coverage_status, captured_people_count,
               discovery_classification, discovery_url, notes
        FROM official_program_coverage_audit
        WHERE matched_program_name IS NOT NULL
          AND matched_program_name != ''
        """
    ):
        result[row["matched_program_name"]] = dict(row)
    return result


def readiness_status(row: dict, refresh_date: date) -> tuple[str, str]:
    expected_next = parse_date(row.get("expected_next_date"))
    stale_after = parse_date(row.get("stale_after_date"))
    transition_type = row.get("expected_transition_type") or ""
    refresh_policy = row.get("refresh_policy") or ""

    if refresh_policy == "review_required" or transition_type.endswith("_review"):
        return (
            "review_required_window",
            "Current stage is individualized or ambiguous; a future run should not mutate it without source review.",
        )
    if transition_type == "expected_completion":
        if stale_after and stale_after <= refresh_date:
            return (
                "expected_completion_window",
                "Terminal observation should be allowed to disappear after stale-after as expected completion.",
            )
        return (
            "terminal_active_before_completion",
            "Terminal observation is still inside the active window at the projected refresh date.",
        )
    if transition_type == "expected_annual_advancement" and expected_next and expected_next <= refresh_date:
        return (
            "expected_advancement_window",
            "Annual-clock observation should be reconciled against the expected next stage on refresh.",
        )
    if refresh_policy == "source_refresh_required":
        if stale_after and stale_after <= refresh_date:
            return (
                "source_refresh_required_window",
                "State duration is source-dependent and stale by refresh; only a fresh source should retain it.",
            )
        return (
            "active_no_change_expected",
            "Source-dependent state is not yet stale at the projected refresh date.",
        )
    if stale_after and stale_after <= refresh_date:
        return (
            "stale_without_transition_review",
            "Observation will be stale by refresh but has no safe expected transition.",
        )
    if transition_type == "expected_annual_advancement":
        return (
            "annual_clock_active_before_transition",
            "Annual-clock observation is not yet due to advance by the projected refresh date.",
        )
    return (
        "active_no_change_expected",
        "No transition is expected by the projected refresh date.",
    )


def missing_expectation(row: dict, status: str) -> tuple[str, str]:
    if status == "expected_completion_window":
        return (
            "expected_absence_after_completion",
            "If absent on the next refresh, treat as likely completion/alumni movement until contradicted.",
        )
    if status in {"source_refresh_required_window", "stale_without_transition_review", "review_required_window"}:
        return (
            "absence_requires_source_reconciliation",
            "If absent on the next refresh, reconcile source availability before marking departure.",
        )
    return (
        "unexpected_absence_review",
        "If absent on the next refresh, review for scraper miss, program-page change, duplicate identity, or early departure.",
    )


def same_stage_expectation(row: dict, status: str) -> tuple[str, str]:
    if status == "expected_advancement_window":
        return (
            "same_stage_after_expected_transition_review",
            "Same normalized stage after the expected transition date is plausible only if a fresh source repeats it.",
        )
    if status == "expected_completion_window":
        return (
            "same_terminal_stage_after_completion_review",
            "Same terminal stage after stale-after should be treated as a new source observation, not old-state carryover.",
        )
    if status in {"source_refresh_required_window", "stale_without_transition_review", "review_required_window"}:
        return (
            "same_stage_requires_fresh_source",
            "Same stage is acceptable only if the next run records a fresh public observation.",
        )
    return (
        "same_stage_expected",
        "Same normalized stage is consistent with the current lifecycle clock.",
    )


def next_stage_expectation(row: dict, status: str) -> tuple[str, str]:
    expected_next_stage = row.get("expected_next_stage") or ""
    if expected_next_stage and status == "expected_advancement_window":
        return (
            "expected_next_stage_accept_candidate",
            f"Expected next stage is {expected_next_stage}; accept only when the same person/program is freshly observed.",
        )
    if expected_next_stage:
        return (
            "early_expected_next_stage_review",
            f"Expected next stage is {expected_next_stage}, but the projected refresh date is before the expected transition.",
        )
    return (
        "no_expected_next_stage",
        "No deterministic next stage exists for this observation.",
    )


def enrich_rows(rows: list[dict], coverage: dict[str, dict], refresh_date: date) -> list[dict]:
    enriched = []
    for row in rows:
        status, rationale = readiness_status(row, refresh_date)
        missing_class, missing_notes = missing_expectation(row, status)
        same_class, same_notes = same_stage_expectation(row, status)
        next_class, next_notes = next_stage_expectation(row, status)
        coverage_row = coverage.get(row.get("program_name") or "", {})
        expected_next_date = parse_date(row.get("expected_next_date"))
        stale_after = parse_date(row.get("stale_after_date"))
        enriched.append(
            {
                **row,
                "projected_refresh_date": refresh_date.isoformat(),
                "readiness_status": status,
                "readiness_priority": READINESS_PRIORITY[status],
                "readiness_rationale": rationale,
                "program_coverage_status": coverage_row.get("coverage_status", "not_in_official_hup_audit"),
                "program_discovery_classification": coverage_row.get("discovery_classification", ""),
                "expected_if_missing_on_refresh": missing_class,
                "missing_on_refresh_notes": missing_notes,
                "expected_if_same_stage_on_refresh": same_class,
                "same_stage_on_refresh_notes": same_notes,
                "expected_if_next_stage_on_refresh": next_class,
                "next_stage_on_refresh_notes": next_notes,
                "advance_due_by_refresh": bool_int(bool(expected_next_date and expected_next_date <= refresh_date)),
                "stale_by_refresh": bool_int(bool(stale_after and stale_after <= refresh_date)),
                "completion_window_by_refresh": bool_int(status == "expected_completion_window"),
                "requires_source_refresh_by_refresh": bool_int(status == "source_refresh_required_window"),
                "requires_human_review_by_refresh": bool_int(
                    status in {"review_required_window", "stale_without_transition_review"}
                ),
            }
        )
    return enriched


def choose_worst(rows: list[dict]) -> dict:
    return max(rows, key=lambda row: (row["readiness_priority"], row.get("stage_rank") or 0))


def rollup_rows(rows: list[dict], keys: list[str], identity_fields: list[str]) -> list[dict]:
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[tuple(row.get(key) or "" for key in keys)].append(row)

    result = []
    for key, group in grouped.items():
        worst = choose_worst(group)
        statuses = Counter(row["readiness_status"] for row in group)
        missing = Counter(row["expected_if_missing_on_refresh"] for row in group)
        coverage = Counter(row["program_coverage_status"] for row in group)
        people = {row["person_key"] for row in group}
        programs = {row.get("program_name") or "" for row in group if row.get("program_name")}
        row = {field: worst.get(field, "") for field in identity_fields}
        for field, value in zip(keys, key, strict=True):
            row[field] = value
        row.update(
            {
                "person_count": len(people),
                "program_count": len(programs),
                "state_observation_count": len(group),
                "worst_readiness_status": worst["readiness_status"],
                "worst_readiness_priority": worst["readiness_priority"],
                "dominant_program_coverage_status": coverage.most_common(1)[0][0],
                "expected_advancement_window_count": statuses.get("expected_advancement_window", 0),
                "expected_completion_window_count": statuses.get("expected_completion_window", 0),
                "source_refresh_required_window_count": statuses.get("source_refresh_required_window", 0),
                "review_required_window_count": statuses.get("review_required_window", 0),
                "stale_without_transition_review_count": statuses.get("stale_without_transition_review", 0),
                "unexpected_absence_review_count": missing.get("unexpected_absence_review", 0),
                "absence_requires_source_reconciliation_count": missing.get(
                    "absence_requires_source_reconciliation", 0
                ),
                "expected_absence_after_completion_count": missing.get("expected_absence_after_completion", 0),
                "recommended_refresh_action": refresh_action(worst["readiness_status"]),
            }
        )
        result.append(row)
    return sorted(result, key=lambda row: (-row["worst_readiness_priority"], *(row.get(key, "") for key in keys)))


def refresh_action(status: str) -> str:
    if status == "expected_advancement_window":
        return "reconcile_expected_stage_advancement"
    if status == "expected_completion_window":
        return "allow_completion_absence_or_confirm_alumni_endpoint"
    if status == "source_refresh_required_window":
        return "refresh_source_before_retaining_state"
    if status in {"review_required_window", "stale_without_transition_review"}:
        return "review_lifecycle_or_source_before_mutation"
    return "monitor_next_refresh"


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def summary_payload(
    state_rows: list[dict],
    person_rows: list[dict],
    program_rows: list[dict],
    category_rows: list[dict],
    refresh_date: date,
) -> dict:
    statuses = Counter(row["readiness_status"] for row in state_rows)
    missing = Counter(row["expected_if_missing_on_refresh"] for row in state_rows)
    same = Counter(row["expected_if_same_stage_on_refresh"] for row in state_rows)
    next_stage = Counter(row["expected_if_next_stage_on_refresh"] for row in state_rows)
    role_status = Counter(f"{row.get('role') or ''}:{row['readiness_status']}" for row in state_rows)
    category_status = Counter(
        f"{row.get('trainee_category') or 'none'}:{row['readiness_status']}" for row in state_rows
    )
    return {
        "projected_refresh_date": refresh_date.isoformat(),
        "state_rows": len(state_rows),
        "person_rows": len(person_rows),
        "program_rows": len(program_rows),
        "category_rows": len(category_rows),
        "by_readiness_status": dict(sorted(statuses.items())),
        "by_missing_expectation": dict(sorted(missing.items())),
        "by_same_stage_expectation": dict(sorted(same.items())),
        "by_next_stage_expectation": dict(sorted(next_stage.items())),
        "by_role_and_readiness_status": dict(sorted(role_status.items())),
        "by_category_and_readiness_status": dict(sorted(category_status.items())),
        "advance_due_by_refresh_rows": sum(row["advance_due_by_refresh"] for row in state_rows),
        "stale_by_refresh_rows": sum(row["stale_by_refresh"] for row in state_rows),
        "completion_window_by_refresh_rows": sum(row["completion_window_by_refresh"] for row in state_rows),
        "requires_source_refresh_by_refresh_rows": sum(row["requires_source_refresh_by_refresh"] for row in state_rows),
        "requires_human_review_by_refresh_rows": sum(row["requires_human_review_by_refresh"] for row in state_rows),
        "state_csv": "artifacts/data/training_state_refresh_expectations.csv",
        "person_csv": "artifacts/data/person_refresh_expectations.csv",
        "program_csv": "artifacts/data/program_refresh_expectations.csv",
        "category_csv": "artifacts/data/category_refresh_expectations.csv",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--refresh-date", default=date.today().isoformat())
    args = parser.parse_args()

    refresh_date = date.fromisoformat(args.refresh_date)
    conn = sqlite3.connect(args.db)
    rows = read_state_rows(conn)
    coverage = read_program_coverage(conn)
    conn.close()

    state_rows = enrich_rows(rows, coverage, refresh_date)
    person_rows = rollup_rows(state_rows, ["person_key"], ["display_name", "role"])
    program_rows = rollup_rows(state_rows, ["program_name", "role"], [])
    category_rows = rollup_rows(state_rows, ["trainee_category", "role"], [])
    summary = summary_payload(state_rows, person_rows, program_rows, category_rows, refresh_date)

    write_csv(ARTIFACTS / "training_state_refresh_expectations.csv", state_rows)
    write_csv(ARTIFACTS / "person_refresh_expectations.csv", person_rows)
    write_csv(ARTIFACTS / "program_refresh_expectations.csv", program_rows)
    write_csv(ARTIFACTS / "category_refresh_expectations.csv", category_rows)
    (ARTIFACTS / "longitudinal_change_readiness_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
