#!/usr/bin/env python3
"""Materialize row-level next-refresh transition policies for trainee states."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "training_state_transition_plan.csv"
JSON_PATH = ARTIFACTS / "training_state_transition_plan.json"
ROLLUP_CSV_PATH = ARTIFACTS / "training_state_transition_plan_rollups.csv"
ROLLUP_JSON_PATH = ARTIFACTS / "training_state_transition_plan_rollups.json"
SUMMARY_PATH = ARTIFACTS / "training_state_transition_plan_summary.json"

DEFAULT_INSTITUTION = "University of Pennsylvania Health System / Perelman School of Medicine"
DEFAULT_COUNTRY = "United States"
DEFAULT_COUNTRY_CODE = "US"

PLAN_FIELDS = [
    "plan_key",
    "state_id",
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
    "raw_stage_label",
    "normalized_stage",
    "stage_family",
    "stage_index",
    "stage_rank",
    "academic_year",
    "lifecycle_rule_key",
    "lifecycle_code",
    "lifecycle_stage",
    "expected_next_stage",
    "expected_next_date",
    "expected_exit_date",
    "expected_transition_type",
    "stale_after_date",
    "refresh_policy",
    "readiness_status",
    "state_machine_status",
    "clock_model",
    "policy_lane",
    "diff_readiness_status",
    "if_missing_change_type",
    "if_same_stage_change_type",
    "if_expected_next_stage_change_type",
    "evidence_requirement",
    "transition_classification_policy",
    "recommended_operator_action",
    "stale_by_refresh",
    "advance_due_by_refresh",
    "completion_window_by_refresh",
    "source_refresh_required_by_refresh",
    "human_review_required_by_refresh",
    "auto_classifiable_transition",
    "fresh_observation_required",
    "confidence",
    "evidence_json",
]

ROLLUP_FIELDS = [
    "rollup_key",
    "rollup_scope",
    "rollup_value",
    "institution",
    "country",
    "country_code",
    "role",
    "trainee_category",
    "program_name",
    "lifecycle_code",
    "policy_lane",
    "diff_readiness_status",
    "projected_refresh_date",
    "state_observation_count",
    "person_count",
    "program_count",
    "deterministic_advancement_count",
    "deterministic_completion_count",
    "source_refresh_required_count",
    "human_review_required_count",
    "no_change_expected_count",
    "stale_by_refresh_count",
    "auto_classifiable_transition_count",
    "fresh_observation_required_count",
    "dominant_policy_lane",
    "dominant_diff_readiness_status",
    "recommended_operator_action",
    "evidence_json",
]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key_for(prefix: str, parts: tuple[str, ...]) -> str:
    return f"{prefix}_{sha256_text(json.dumps(parts, sort_keys=True))[:20]}"


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def read_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT r.state_id, r.person_key, r.display_name, r.role,
                   r.trainee_category, r.program_name, r.source_key,
                   r.observed_at, r.as_of_date, r.projected_refresh_date,
                   r.raw_stage_label, r.normalized_stage, r.stage_family,
                   r.stage_index, r.stage_rank, r.academic_year,
                   r.lifecycle_rule_key, r.lifecycle_code, r.lifecycle_stage,
                   r.expected_next_stage, r.expected_next_date,
                   r.expected_exit_date, r.expected_transition_type,
                   r.stale_after_date, r.refresh_policy, r.readiness_status,
                   r.expected_if_missing_on_refresh,
                   r.expected_if_same_stage_on_refresh,
                   r.expected_if_next_stage_on_refresh,
                   r.advance_due_by_refresh, r.stale_by_refresh,
                   r.completion_window_by_refresh,
                   r.requires_source_refresh_by_refresh,
                   r.requires_human_review_by_refresh, r.confidence,
                   a.state_machine_status, a.clock_model,
                   a.state_machine_reason, a.recommended_action AS state_machine_action
            FROM training_state_refresh_expectations r
            LEFT JOIN training_state_machine_audit a
              ON a.state_id = r.state_id
             AND a.person_key = r.person_key
             AND COALESCE(a.program_name, '') = COALESCE(r.program_name, '')
            ORDER BY r.role, r.trainee_category, r.program_name, r.display_name, r.state_id
            """
        )
    ]


def policy_lane(status: str) -> str:
    if status == "expected_advancement_window":
        return "deterministic_expected_advancement"
    if status == "expected_completion_window":
        return "deterministic_expected_completion"
    if status == "source_refresh_required_window":
        return "source_refresh_required"
    if status in {"review_required_window", "stale_without_transition_review"}:
        return "manual_review_required"
    if status == "annual_clock_active_before_transition":
        return "pending_annual_advancement"
    if status == "terminal_active_before_completion":
        return "pending_terminal_completion"
    return "carry_forward_no_change"


def diff_readiness(lane: str) -> str:
    if lane in {"deterministic_expected_advancement", "deterministic_expected_completion"}:
        return "diff_expected_change_classifiable"
    if lane == "source_refresh_required":
        return "diff_source_refresh_bound"
    if lane == "manual_review_required":
        return "diff_review_bound"
    return "diff_no_change_expected"


def missing_change_type(value: str) -> str:
    return {
        "expected_absence_after_completion": "removed_expected_completion_candidate",
        "absence_requires_source_reconciliation": "removed_requires_source_reconciliation",
        "unexpected_absence_review": "removed_unexpected_review",
    }.get(value or "", "removed_review")


def same_stage_change_type(value: str) -> str:
    return {
        "same_stage_expected": "unchanged_expected",
        "same_stage_after_expected_transition_review": "unchanged_after_expected_transition_review",
        "same_terminal_stage_after_completion_review": "unchanged_terminal_after_completion_review",
        "same_stage_requires_fresh_source": "unchanged_requires_fresh_source",
    }.get(value or "", "unchanged_review")


def next_stage_change_type(value: str) -> str:
    return {
        "expected_next_stage_accept_candidate": "advanced_expected_with_fresh_observation",
        "early_expected_next_stage_review": "advanced_early_review",
        "no_expected_next_stage": "advanced_without_expected_stage_review",
    }.get(value or "", "advanced_review")


def evidence_requirement(lane: str) -> str:
    return {
        "deterministic_expected_advancement": "Fresh same-person, same-program roster observation must show expected_next_stage before accepting advancement.",
        "deterministic_expected_completion": "Fresh source refresh must show absence after stale_after_date or an alumni/completion endpoint before classifying completion.",
        "source_refresh_required": "Fresh source observation is required before retaining, advancing, or removing this state.",
        "manual_review_required": "Human review is required because lifecycle duration, source label, or transition semantics are ambiguous.",
        "pending_annual_advancement": "No mutation before expected_next_date; retain unless contradicted by a fresh public source.",
        "pending_terminal_completion": "No completion classification before stale_after_date; retain unless contradicted by a fresh public source.",
        "carry_forward_no_change": "Retain until contradicted by a fresh public source.",
    }.get(lane, "Review transition policy before mutation.")


def transition_policy(lane: str) -> str:
    return {
        "deterministic_expected_advancement": "classify_expected_advancement_only_with_fresh_expected_stage_observation",
        "deterministic_expected_completion": "classify_expected_completion_only_after_fresh_absence_or_alumni_evidence",
        "source_refresh_required": "do_not_carry_forward_without_fresh_source",
        "manual_review_required": "do_not_mutate_without_manual_review",
        "pending_annual_advancement": "retain_before_expected_transition_window",
        "pending_terminal_completion": "retain_before_completion_window",
        "carry_forward_no_change": "retain_until_fresh_source_contradiction",
    }.get(lane, "manual_review_required")


def recommended_action(lane: str) -> str:
    return {
        "deterministic_expected_advancement": "reconcile_fresh_roster_against_expected_next_stage",
        "deterministic_expected_completion": "allow_expected_completion_absence_or_confirm_alumni_endpoint",
        "source_refresh_required": "refresh_source_before_retaining_state",
        "manual_review_required": "review_lifecycle_or_source_before_mutation",
        "pending_annual_advancement": "monitor_until_expected_next_date",
        "pending_terminal_completion": "monitor_until_stale_after_date",
        "carry_forward_no_change": "retain_until_contradicted",
    }.get(lane, "review_before_mutation")


def plan_rows(rows: list[dict]) -> list[dict]:
    planned = []
    for row in rows:
        lane = policy_lane(row.get("readiness_status") or "")
        plan = {
            "plan_key": key_for(
                "training_transition_plan",
                (
                    str(row.get("state_id") or ""),
                    row.get("person_key") or "",
                    row.get("program_name") or "",
                    row.get("projected_refresh_date") or "",
                    row.get("readiness_status") or "",
                ),
            ),
            "state_id": row.get("state_id"),
            "person_key": row.get("person_key"),
            "display_name": row.get("display_name"),
            "role": row.get("role"),
            "trainee_category": row.get("trainee_category"),
            "program_name": row.get("program_name"),
            "institution": DEFAULT_INSTITUTION,
            "country": DEFAULT_COUNTRY,
            "country_code": DEFAULT_COUNTRY_CODE,
            "source_key": row.get("source_key"),
            "observed_at": row.get("observed_at"),
            "as_of_date": row.get("as_of_date"),
            "projected_refresh_date": row.get("projected_refresh_date"),
            "raw_stage_label": row.get("raw_stage_label"),
            "normalized_stage": row.get("normalized_stage"),
            "stage_family": row.get("stage_family"),
            "stage_index": row.get("stage_index"),
            "stage_rank": row.get("stage_rank"),
            "academic_year": row.get("academic_year"),
            "lifecycle_rule_key": row.get("lifecycle_rule_key"),
            "lifecycle_code": row.get("lifecycle_code"),
            "lifecycle_stage": row.get("lifecycle_stage"),
            "expected_next_stage": row.get("expected_next_stage"),
            "expected_next_date": row.get("expected_next_date"),
            "expected_exit_date": row.get("expected_exit_date"),
            "expected_transition_type": row.get("expected_transition_type"),
            "stale_after_date": row.get("stale_after_date"),
            "refresh_policy": row.get("refresh_policy"),
            "readiness_status": row.get("readiness_status"),
            "state_machine_status": row.get("state_machine_status"),
            "clock_model": row.get("clock_model"),
            "policy_lane": lane,
            "diff_readiness_status": diff_readiness(lane),
            "if_missing_change_type": missing_change_type(row.get("expected_if_missing_on_refresh") or ""),
            "if_same_stage_change_type": same_stage_change_type(row.get("expected_if_same_stage_on_refresh") or ""),
            "if_expected_next_stage_change_type": next_stage_change_type(row.get("expected_if_next_stage_on_refresh") or ""),
            "evidence_requirement": evidence_requirement(lane),
            "transition_classification_policy": transition_policy(lane),
            "recommended_operator_action": recommended_action(lane),
            "stale_by_refresh": as_int(row.get("stale_by_refresh")),
            "advance_due_by_refresh": as_int(row.get("advance_due_by_refresh")),
            "completion_window_by_refresh": as_int(row.get("completion_window_by_refresh")),
            "source_refresh_required_by_refresh": as_int(row.get("requires_source_refresh_by_refresh")),
            "human_review_required_by_refresh": as_int(row.get("requires_human_review_by_refresh")),
            "auto_classifiable_transition": int(
                lane in {"deterministic_expected_advancement", "deterministic_expected_completion"}
            ),
            "fresh_observation_required": int(
                lane
                in {
                    "deterministic_expected_advancement",
                    "deterministic_expected_completion",
                    "source_refresh_required",
                    "manual_review_required",
                }
            ),
            "confidence": row.get("confidence"),
            "evidence_json": dumps(
                {
                    "source_readiness_status": row.get("readiness_status"),
                    "state_machine_status": row.get("state_machine_status"),
                    "state_machine_reason": row.get("state_machine_reason"),
                    "state_machine_action": row.get("state_machine_action"),
                    "expected_if_missing_on_refresh": row.get("expected_if_missing_on_refresh"),
                    "expected_if_same_stage_on_refresh": row.get("expected_if_same_stage_on_refresh"),
                    "expected_if_next_stage_on_refresh": row.get("expected_if_next_stage_on_refresh"),
                    "derived_from": [
                        "training_state_refresh_expectations",
                        "training_state_machine_audit",
                    ],
                    "scope_defaults": {
                        "institution": DEFAULT_INSTITUTION,
                        "country_code": DEFAULT_COUNTRY_CODE,
                    },
                }
            ),
        }
        planned.append({field: plan[field] for field in PLAN_FIELDS})
    return planned


def scope_pairs(row: dict) -> list[tuple[str, str]]:
    role = row.get("role") or ""
    category = row.get("trainee_category") or role or "unknown"
    program = row.get("program_name") or ""
    lifecycle = row.get("lifecycle_code") or "none"
    lane = row.get("policy_lane") or ""
    diff = row.get("diff_readiness_status") or ""
    pairs = [
        ("corpus", "all_penn_affiliated_medical_trainees"),
        ("institution", row.get("institution") or DEFAULT_INSTITUTION),
        ("country", row.get("country_code") or DEFAULT_COUNTRY_CODE),
        ("role", role),
        ("trainee_category", category),
        ("program", program),
        ("program_role", f"{program}::{role}" if program and role else ""),
        ("institution_role", f"{row.get('institution') or DEFAULT_INSTITUTION}::{role}" if role else ""),
        ("lifecycle_code", lifecycle),
        ("policy_lane", lane),
        ("diff_readiness_status", diff),
    ]
    return [(scope, value) for scope, value in pairs if value]


def rollup_action(stats: Counter) -> str:
    if stats["human_review_required_count"]:
        return "review_lifecycle_or_source_before_mutation"
    if stats["source_refresh_required_count"]:
        return "refresh_sources_before_carry_forward"
    if stats["deterministic_completion_count"] and stats["deterministic_advancement_count"]:
        return "classify_expected_advancements_and_completion_absences_with_fresh_evidence"
    if stats["deterministic_completion_count"]:
        return "classify_expected_completion_absences_with_fresh_source_refresh"
    if stats["deterministic_advancement_count"]:
        return "classify_expected_advancements_with_fresh_roster_observations"
    return "monitor_or_retain_until_fresh_source_contradiction"


def rollup_rows(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        for scope, value in scope_pairs(row):
            grouped[(scope, value)].append(row)

    rollups = []
    for (scope, value), group in grouped.items():
        lane_counts = Counter(row["policy_lane"] for row in group)
        diff_counts = Counter(row["diff_readiness_status"] for row in group)
        roles = Counter(row.get("role") or "" for row in group)
        categories = Counter(row.get("trainee_category") or "" for row in group)
        lifecycle_codes = Counter(row.get("lifecycle_code") or "none" for row in group)
        institutions = Counter(row.get("institution") or DEFAULT_INSTITUTION for row in group)
        countries = Counter(row.get("country") or DEFAULT_COUNTRY for row in group)
        country_codes = Counter(row.get("country_code") or DEFAULT_COUNTRY_CODE for row in group)
        people = {row["person_key"] for row in group}
        programs = {row.get("program_name") or "" for row in group if row.get("program_name")}
        refresh_dates = sorted({row.get("projected_refresh_date") or "" for row in group if row.get("projected_refresh_date")})
        stats = Counter()
        for row in group:
            lane = row["policy_lane"]
            stats["deterministic_advancement_count"] += int(lane == "deterministic_expected_advancement")
            stats["deterministic_completion_count"] += int(lane == "deterministic_expected_completion")
            stats["source_refresh_required_count"] += int(lane == "source_refresh_required")
            stats["human_review_required_count"] += int(lane == "manual_review_required")
            stats["no_change_expected_count"] += int(
                lane in {"pending_annual_advancement", "pending_terminal_completion", "carry_forward_no_change"}
            )
            stats["stale_by_refresh_count"] += int(row.get("stale_by_refresh") or 0)
            stats["auto_classifiable_transition_count"] += int(row.get("auto_classifiable_transition") or 0)
            stats["fresh_observation_required_count"] += int(row.get("fresh_observation_required") or 0)
        dominant_lane = lane_counts.most_common(1)[0][0]
        dominant_diff = diff_counts.most_common(1)[0][0]
        program_name = value if scope == "program" else value.split("::", 1)[0] if scope == "program_role" else ""
        row = {
            "rollup_key": key_for("training_transition_plan_rollup", (scope, value, refresh_dates[-1] if refresh_dates else "")),
            "rollup_scope": scope,
            "rollup_value": value,
            "institution": value if scope == "institution" else institutions.most_common(1)[0][0],
            "country": countries.most_common(1)[0][0],
            "country_code": value if scope == "country" else country_codes.most_common(1)[0][0],
            "role": value if scope == "role" else value.split("::", 1)[1] if scope in {"program_role", "institution_role"} else roles.most_common(1)[0][0],
            "trainee_category": value if scope == "trainee_category" else categories.most_common(1)[0][0],
            "program_name": program_name,
            "lifecycle_code": value if scope == "lifecycle_code" else lifecycle_codes.most_common(1)[0][0],
            "policy_lane": value if scope == "policy_lane" else dominant_lane,
            "diff_readiness_status": value if scope == "diff_readiness_status" else dominant_diff,
            "projected_refresh_date": refresh_dates[-1] if refresh_dates else "",
            "state_observation_count": len(group),
            "person_count": len(people),
            "program_count": len(programs),
            "deterministic_advancement_count": stats["deterministic_advancement_count"],
            "deterministic_completion_count": stats["deterministic_completion_count"],
            "source_refresh_required_count": stats["source_refresh_required_count"],
            "human_review_required_count": stats["human_review_required_count"],
            "no_change_expected_count": stats["no_change_expected_count"],
            "stale_by_refresh_count": stats["stale_by_refresh_count"],
            "auto_classifiable_transition_count": stats["auto_classifiable_transition_count"],
            "fresh_observation_required_count": stats["fresh_observation_required_count"],
            "dominant_policy_lane": dominant_lane,
            "dominant_diff_readiness_status": dominant_diff,
            "recommended_operator_action": rollup_action(stats),
            "evidence_json": dumps(
                {
                    "policy_lane_counts": dict(sorted(lane_counts.items())),
                    "diff_readiness_status_counts": dict(sorted(diff_counts.items())),
                    "role_counts": dict(sorted(roles.items())),
                    "trainee_category_counts": dict(sorted(categories.items())),
                    "lifecycle_code_counts": dict(sorted(lifecycle_codes.items())),
                    "derived_from": ["training_state_transition_plan"],
                }
            ),
        }
        rollups.append({field: row[field] for field in ROLLUP_FIELDS})
    return sorted(rollups, key=lambda row: (row["rollup_scope"], row["rollup_value"]))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_db(conn: sqlite3.Connection, table: str, rows: list[dict], fields: list[str]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    field_sql = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    conn.executemany(
        f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def summary_payload(plans: list[dict], rollups: list[dict], generated_at: str) -> dict:
    lanes = Counter(row["policy_lane"] for row in plans)
    diff = Counter(row["diff_readiness_status"] for row in plans)
    actions = Counter(row["recommended_operator_action"] for row in plans)
    role_lane = Counter(f"{row.get('role') or ''}:{row['policy_lane']}" for row in plans)
    rollup_scopes = Counter(row["rollup_scope"] for row in rollups)
    corpus = next((row for row in rollups if row["rollup_scope"] == "corpus"), {})
    if lanes.get("manual_review_required"):
        corpus_guardrail_policy_lane = "mixed_with_manual_review"
        corpus_guardrail_diff_readiness_status = "diff_review_bound"
    elif lanes.get("source_refresh_required"):
        corpus_guardrail_policy_lane = "mixed_with_source_refresh_required"
        corpus_guardrail_diff_readiness_status = "diff_source_refresh_bound"
    elif lanes.get("deterministic_expected_advancement") or lanes.get("deterministic_expected_completion"):
        corpus_guardrail_policy_lane = "deterministic_expected_changes_only"
        corpus_guardrail_diff_readiness_status = "diff_expected_change_classifiable"
    else:
        corpus_guardrail_policy_lane = "no_change_expected"
        corpus_guardrail_diff_readiness_status = "diff_no_change_expected"
    return {
        "generated_at": generated_at,
        "projected_refresh_date": corpus.get("projected_refresh_date", ""),
        "plan_rows": len(plans),
        "rollup_rows": len(rollups),
        "person_count": len({row["person_key"] for row in plans}),
        "program_count": len({row.get("program_name") or "" for row in plans if row.get("program_name")}),
        "by_policy_lane": dict(sorted(lanes.items())),
        "by_diff_readiness_status": dict(sorted(diff.items())),
        "by_recommended_operator_action": dict(sorted(actions.items())),
        "by_role_and_policy_lane": dict(sorted(role_lane.items())),
        "by_rollup_scope": dict(sorted(rollup_scopes.items())),
        "auto_classifiable_transition_rows": sum(row["auto_classifiable_transition"] for row in plans),
        "fresh_observation_required_rows": sum(row["fresh_observation_required"] for row in plans),
        "stale_by_refresh_rows": sum(row["stale_by_refresh"] for row in plans),
        "human_review_required_rows": sum(row["human_review_required_by_refresh"] for row in plans),
        "source_refresh_required_rows": sum(row["source_refresh_required_by_refresh"] for row in plans),
        "corpus_dominant_policy_lane": corpus.get("dominant_policy_lane", ""),
        "corpus_dominant_diff_readiness_status": corpus.get("dominant_diff_readiness_status", ""),
        "corpus_guardrail_policy_lane": corpus_guardrail_policy_lane,
        "corpus_guardrail_diff_readiness_status": corpus_guardrail_diff_readiness_status,
        "corpus_recommended_operator_action": corpus.get("recommended_operator_action", ""),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "rollup_csv": str(ROLLUP_CSV_PATH.relative_to(ROOT)),
        "rollup_json": str(ROLLUP_JSON_PATH.relative_to(ROOT)),
        "policy": "This ledger is non-mutating. Expected transitions are classifiable only with fresh source evidence or explicit terminal absence after stale-after; review/source-bound states are not carried forward silently.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(args.db)
    plans = plan_rows(read_rows(conn))
    rollups = rollup_rows(plans)

    write_csv(CSV_PATH, plans, PLAN_FIELDS)
    write_json(JSON_PATH, plans)
    write_csv(ROLLUP_CSV_PATH, rollups, ROLLUP_FIELDS)
    write_json(ROLLUP_JSON_PATH, rollups)
    with conn:
        write_db(conn, "training_state_transition_plan", plans, PLAN_FIELDS)
        write_db(conn, "training_state_transition_plan_rollups", rollups, ROLLUP_FIELDS)
    conn.close()

    summary = summary_payload(plans, rollups, generated_at)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
