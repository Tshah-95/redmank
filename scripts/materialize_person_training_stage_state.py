#!/usr/bin/env python3
"""Materialize an ergonomic state-machine ledger for person/program stages."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "person_training_stage_state.csv"
JSON_PATH = ARTIFACTS / "person_training_stage_state.json"
ROLLUP_CSV_PATH = ARTIFACTS / "training_stage_state_rollups.csv"
ROLLUP_JSON_PATH = ARTIFACTS / "training_stage_state_rollups.json"
SUMMARY_PATH = ARTIFACTS / "person_training_stage_state_summary.json"

STAGE_FIELDS = [
    "stage_state_key",
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
    "current_stage_label",
    "current_stage_code",
    "stage_family",
    "stage_index",
    "stage_rank",
    "lifecycle_rule_key",
    "lifecycle_code",
    "lifecycle_stage",
    "academic_year",
    "current_temporal_state_code",
    "temporal_validity_status",
    "stage_state_status",
    "staleness_bucket",
    "expected_next_stage",
    "expected_next_date",
    "expected_exit_date",
    "stale_after_date",
    "clock_model",
    "policy_lane",
    "diff_readiness_status",
    "next_refresh_contract",
    "next_refresh_expected_behavior",
    "expected_if_missing_on_next_refresh",
    "expected_if_same_stage_on_next_refresh",
    "expected_if_expected_next_stage_on_next_refresh",
    "allowed_auto_diff_outcomes_json",
    "review_trigger_json",
    "evidence_required_to_retain",
    "evidence_required_to_advance",
    "evidence_required_to_complete",
    "stale_information_policy",
    "recommended_operator_action",
    "duplicate_contract_count_for_canonical_key",
    "stale_by_refresh",
    "advance_due_by_refresh",
    "completion_window_by_refresh",
    "source_refresh_required_by_refresh",
    "human_review_required_by_refresh",
    "auto_classifiable_transition",
    "fresh_observation_required",
    "confidence",
    "state_machine_evidence_json",
    "generated_at",
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
    "projected_refresh_date",
    "stage_state_count",
    "canonical_person_program_count",
    "person_count",
    "program_count",
    "deterministic_advancement_count",
    "deterministic_completion_count",
    "source_refresh_required_count",
    "manual_review_required_count",
    "carry_forward_count",
    "duplicate_contract_count",
    "stale_by_refresh_count",
    "fresh_observation_required_count",
    "auto_classifiable_transition_count",
    "dominant_stage_state_status",
    "dominant_staleness_bucket",
    "dominant_policy_lane",
    "dominant_diff_readiness_status",
    "recommended_operator_action",
    "stale_information_policy",
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


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def read_contracts(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM training_temporal_contracts
            ORDER BY role, trainee_category, program_name, display_name, contract_key
            """
        )
    ]


def staleness_bucket(row: dict, refresh_date: date) -> str:
    stale_after = parse_date(row.get("stale_after_date"))
    expected_next = parse_date(row.get("expected_next_date"))
    expected_exit = parse_date(row.get("expected_exit_date"))
    if as_int(row.get("human_review_required_by_refresh")):
        return "review_bound_not_time_classifiable"
    if stale_after and stale_after <= refresh_date:
        return "stale_by_projected_refresh"
    if expected_exit and expected_exit <= refresh_date:
        return "completion_window_by_projected_refresh"
    if expected_next and expected_next <= refresh_date:
        return "advancement_window_by_projected_refresh"
    if row.get("next_refresh_contract") == "retain_until_fresh_source_contradiction":
        return "fresh_contradiction_only"
    return "valid_through_projected_refresh"


def stage_state_status(row: dict) -> str:
    lane = row.get("policy_lane") or ""
    if lane == "deterministic_expected_advancement":
        return "expected_to_advance_if_fresh_next_stage_observed"
    if lane == "deterministic_expected_completion":
        return "expected_to_complete_if_absent_or_alumni_after_refresh"
    if lane == "source_refresh_required":
        return "must_refresh_source_before_retention_or_change"
    if lane == "manual_review_required":
        return "manual_review_required_before_any_stage_mutation"
    if lane == "carry_forward_no_change":
        return "carry_forward_until_fresh_source_contradiction"
    return "monitor_until_clock_or_source_changes"


def expected_behavior(row: dict) -> str:
    lane = row.get("policy_lane") or ""
    if lane == "deterministic_expected_advancement":
        return "On next refresh, classify as expected advancement only if a fresh roster observes the expected next stage; otherwise review unchanged/missing rows."
    if lane == "deterministic_expected_completion":
        return "On next refresh, classify absence after stale-after as expected completion only with a fresh source refresh or alumni/completion endpoint."
    if lane == "source_refresh_required":
        return "On next refresh, do not carry forward this state unless the source is freshly reobserved."
    if lane == "manual_review_required":
        return "Do not mutate this state from elapsed time; resolve lifecycle/source-label ambiguity first."
    if lane == "carry_forward_no_change":
        return "Carry forward unless a fresh public source contradicts the state."
    return "Monitor until a clock rule, fresh source, or reviewer decision gives a classifiable transition."


def stage_rows(contracts: list[dict], generated_at: str) -> list[dict]:
    duplicate_counts = Counter(row["canonical_person_program_key"] for row in contracts)
    rows = []
    for row in contracts:
        refresh_date = parse_date(row.get("projected_refresh_date")) or date.today()
        state = {
            "stage_state_key": key_for("person_training_stage_state", (row["contract_key"], row["canonical_person_program_key"])),
            "contract_key": row["contract_key"],
            "canonical_person_program_key": row["canonical_person_program_key"],
            "person_key": row["person_key"],
            "display_name": row.get("display_name"),
            "role": row.get("role"),
            "trainee_category": row.get("trainee_category"),
            "program_name": row.get("program_name"),
            "institution": row.get("institution"),
            "country": row.get("country"),
            "country_code": row.get("country_code"),
            "source_key": row.get("source_key"),
            "observed_at": row.get("observed_at"),
            "as_of_date": row.get("as_of_date"),
            "projected_refresh_date": row.get("projected_refresh_date"),
            "current_stage_label": row.get("current_stage_label"),
            "current_stage_code": row.get("current_stage_code"),
            "stage_family": row.get("stage_family"),
            "stage_index": row.get("stage_index"),
            "stage_rank": row.get("stage_rank"),
            "lifecycle_rule_key": row.get("lifecycle_rule_key"),
            "lifecycle_code": row.get("lifecycle_code"),
            "lifecycle_stage": row.get("lifecycle_stage"),
            "academic_year": row.get("academic_year"),
            "current_temporal_state_code": row.get("current_temporal_state_code"),
            "temporal_validity_status": row.get("temporal_validity_status"),
            "stage_state_status": stage_state_status(row),
            "staleness_bucket": staleness_bucket(row, refresh_date),
            "expected_next_stage": row.get("expected_next_stage"),
            "expected_next_date": row.get("expected_next_date"),
            "expected_exit_date": row.get("expected_exit_date"),
            "stale_after_date": row.get("stale_after_date"),
            "clock_model": row.get("clock_model"),
            "policy_lane": row.get("policy_lane"),
            "diff_readiness_status": row.get("diff_readiness_status"),
            "next_refresh_contract": row.get("next_refresh_contract"),
            "next_refresh_expected_behavior": expected_behavior(row),
            "expected_if_missing_on_next_refresh": row.get("if_missing_change_type"),
            "expected_if_same_stage_on_next_refresh": row.get("if_same_stage_change_type"),
            "expected_if_expected_next_stage_on_next_refresh": row.get("if_expected_next_stage_change_type"),
            "allowed_auto_diff_outcomes_json": row.get("allowed_auto_diff_outcomes_json"),
            "review_trigger_json": row.get("review_trigger_json"),
            "evidence_required_to_retain": row.get("evidence_required_to_retain"),
            "evidence_required_to_advance": row.get("evidence_required_to_advance"),
            "evidence_required_to_complete": row.get("evidence_required_to_complete"),
            "stale_information_policy": row.get("stale_information_policy"),
            "recommended_operator_action": row.get("recommended_operator_action"),
            "duplicate_contract_count_for_canonical_key": duplicate_counts[row["canonical_person_program_key"]],
            "stale_by_refresh": as_int(row.get("stale_by_refresh")),
            "advance_due_by_refresh": as_int(row.get("advance_due_by_refresh")),
            "completion_window_by_refresh": as_int(row.get("completion_window_by_refresh")),
            "source_refresh_required_by_refresh": as_int(row.get("source_refresh_required_by_refresh")),
            "human_review_required_by_refresh": as_int(row.get("human_review_required_by_refresh")),
            "auto_classifiable_transition": as_int(row.get("auto_classifiable_transition")),
            "fresh_observation_required": as_int(row.get("fresh_observation_required")),
            "confidence": row.get("confidence"),
            "state_machine_evidence_json": dumps(
                {
                    "derived_from": ["training_temporal_contracts", "training_state_transition_plan", "training_state_machine_audit"],
                    "contract_key": row.get("contract_key"),
                    "policy_lane": row.get("policy_lane"),
                    "next_refresh_contract": row.get("next_refresh_contract"),
                    "duplicate_contract_count_for_canonical_key": duplicate_counts[row["canonical_person_program_key"]],
                }
            ),
            "generated_at": generated_at,
        }
        rows.append({field: state[field] for field in STAGE_FIELDS})
    return rows


def scope_pairs(row: dict) -> list[tuple[str, str]]:
    role = row.get("role") or ""
    category = row.get("trainee_category") or role or "unknown"
    program = row.get("program_name") or ""
    institution = row.get("institution") or ""
    country_code = row.get("country_code") or ""
    lifecycle = row.get("lifecycle_code") or "none"
    pairs = [
        ("corpus", "all_penn_affiliated_medical_trainees"),
        ("institution", institution),
        ("country", country_code),
        ("role", role),
        ("trainee_category", category),
        ("program", program),
        ("program_role", f"{program}::{role}" if program and role else ""),
        ("institution_role", f"{institution}::{role}" if institution and role else ""),
        ("lifecycle_code", lifecycle),
        ("policy_lane", row.get("policy_lane") or ""),
        ("diff_readiness_status", row.get("diff_readiness_status") or ""),
        ("staleness_bucket", row.get("staleness_bucket") or ""),
    ]
    return [(scope, value) for scope, value in pairs if value]


def rollup_action(stats: Counter) -> str:
    if stats["manual_review_required_count"]:
        return "resolve_review_bound_states_before_mutating_this_scope"
    if stats["source_refresh_required_count"]:
        return "refresh_sources_before_retaining_or_diffing_this_scope"
    if stats["deterministic_completion_count"] and stats["deterministic_advancement_count"]:
        return "reconcile_expected_advancements_and_completion_absences"
    if stats["deterministic_completion_count"]:
        return "reconcile_expected_completion_absences"
    if stats["deterministic_advancement_count"]:
        return "reconcile_expected_advancements"
    return "carry_forward_until_fresh_source_contradiction"


def rollup_policy(stats: Counter) -> str:
    if stats["manual_review_required_count"]:
        return "do_not_auto_mutate_review_bound_stage_states"
    if stats["source_refresh_required_count"]:
        return "do_not_carry_forward_stale_stage_states_without_fresh_source"
    if stats["deterministic_completion_count"]:
        return "classify_completion_absence_only_after_fresh_refresh"
    if stats["deterministic_advancement_count"]:
        return "classify_advancement_only_when_expected_next_stage_is_freshly_observed"
    return "retain_until_fresh_public_source_contradiction"


def build_rollups(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        for pair in scope_pairs(row):
            grouped[pair].append(row)

    rollups = []
    for (scope, value), group in grouped.items():
        stats = Counter()
        policies = Counter(row["policy_lane"] for row in group)
        statuses = Counter(row["stage_state_status"] for row in group)
        staleness = Counter(row["staleness_bucket"] for row in group)
        diff = Counter(row["diff_readiness_status"] for row in group)
        institutions = Counter(row.get("institution") or "" for row in group)
        countries = Counter(row.get("country") or "" for row in group)
        country_codes = Counter(row.get("country_code") or "" for row in group)
        roles = Counter(row.get("role") or "" for row in group)
        categories = Counter(row.get("trainee_category") or "" for row in group)
        lifecycles = Counter(row.get("lifecycle_code") or "none" for row in group)
        refresh_dates = sorted({row.get("projected_refresh_date") or "" for row in group if row.get("projected_refresh_date")})
        canonical_links = {row["canonical_person_program_key"] for row in group}
        people = {row["person_key"] for row in group}
        programs = {row.get("program_name") or "" for row in group if row.get("program_name")}
        duplicate_rows = sum(1 for row in group if as_int(row.get("duplicate_contract_count_for_canonical_key")) > 1)
        for row in group:
            lane = row["policy_lane"]
            stats["deterministic_advancement_count"] += int(lane == "deterministic_expected_advancement")
            stats["deterministic_completion_count"] += int(lane == "deterministic_expected_completion")
            stats["source_refresh_required_count"] += int(lane == "source_refresh_required")
            stats["manual_review_required_count"] += int(lane == "manual_review_required")
            stats["carry_forward_count"] += int(lane == "carry_forward_no_change")
            stats["stale_by_refresh_count"] += as_int(row.get("stale_by_refresh"))
            stats["fresh_observation_required_count"] += as_int(row.get("fresh_observation_required"))
            stats["auto_classifiable_transition_count"] += as_int(row.get("auto_classifiable_transition"))
        program_name = value if scope == "program" else value.split("::", 1)[0] if scope == "program_role" else ""
        rollup = {
            "rollup_key": key_for("training_stage_state_rollup", (scope, value, refresh_dates[-1] if refresh_dates else "")),
            "rollup_scope": scope,
            "rollup_value": value,
            "institution": value if scope == "institution" else institutions.most_common(1)[0][0],
            "country": countries.most_common(1)[0][0],
            "country_code": value if scope == "country" else country_codes.most_common(1)[0][0],
            "role": value if scope == "role" else value.split("::", 1)[1] if scope in {"program_role", "institution_role"} else roles.most_common(1)[0][0],
            "trainee_category": value if scope == "trainee_category" else categories.most_common(1)[0][0],
            "program_name": program_name,
            "lifecycle_code": value if scope == "lifecycle_code" else lifecycles.most_common(1)[0][0],
            "projected_refresh_date": refresh_dates[-1] if refresh_dates else "",
            "stage_state_count": len(group),
            "canonical_person_program_count": len(canonical_links),
            "person_count": len(people),
            "program_count": len(programs),
            "deterministic_advancement_count": stats["deterministic_advancement_count"],
            "deterministic_completion_count": stats["deterministic_completion_count"],
            "source_refresh_required_count": stats["source_refresh_required_count"],
            "manual_review_required_count": stats["manual_review_required_count"],
            "carry_forward_count": stats["carry_forward_count"],
            "duplicate_contract_count": duplicate_rows,
            "stale_by_refresh_count": stats["stale_by_refresh_count"],
            "fresh_observation_required_count": stats["fresh_observation_required_count"],
            "auto_classifiable_transition_count": stats["auto_classifiable_transition_count"],
            "dominant_stage_state_status": statuses.most_common(1)[0][0],
            "dominant_staleness_bucket": staleness.most_common(1)[0][0],
            "dominant_policy_lane": policies.most_common(1)[0][0],
            "dominant_diff_readiness_status": diff.most_common(1)[0][0],
            "recommended_operator_action": rollup_action(stats),
            "stale_information_policy": rollup_policy(stats),
            "evidence_json": dumps(
                {
                    "derived_from": ["person_training_stage_state"],
                    "policy_lane_counts": dict(sorted(policies.items())),
                    "stage_state_status_counts": dict(sorted(statuses.items())),
                    "staleness_bucket_counts": dict(sorted(staleness.items())),
                    "diff_readiness_status_counts": dict(sorted(diff.items())),
                }
            ),
        }
        rollups.append({field: rollup[field] for field in ROLLUP_FIELDS})
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
    conn.executemany(f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})", rows)


def summary_payload(rows: list[dict], rollups: list[dict], generated_at: str) -> dict:
    policies = Counter(row["policy_lane"] for row in rows)
    statuses = Counter(row["stage_state_status"] for row in rows)
    staleness = Counter(row["staleness_bucket"] for row in rows)
    diff = Counter(row["diff_readiness_status"] for row in rows)
    rollup_scopes = Counter(row["rollup_scope"] for row in rollups)
    return {
        "generated_at": generated_at,
        "stage_state_rows": len(rows),
        "person_count": len({row["person_key"] for row in rows}),
        "program_count": len({row.get("program_name") or "" for row in rows if row.get("program_name")}),
        "canonical_person_program_count": len({row["canonical_person_program_key"] for row in rows}),
        "duplicate_contract_rows": sum(1 for row in rows if as_int(row.get("duplicate_contract_count_for_canonical_key")) > 1),
        "rollup_rows": len(rollups),
        "by_policy_lane": dict(sorted(policies.items())),
        "by_stage_state_status": dict(sorted(statuses.items())),
        "by_staleness_bucket": dict(sorted(staleness.items())),
        "by_diff_readiness_status": dict(sorted(diff.items())),
        "by_rollup_scope": dict(sorted(rollup_scopes.items())),
        "auto_classifiable_transition_rows": sum(as_int(row["auto_classifiable_transition"]) for row in rows),
        "fresh_observation_required_rows": sum(as_int(row["fresh_observation_required"]) for row in rows),
        "stale_by_refresh_rows": sum(as_int(row["stale_by_refresh"]) for row in rows),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "rollup_csv": str(ROLLUP_CSV_PATH.relative_to(ROOT)),
        "rollup_json": str(ROLLUP_JSON_PATH.relative_to(ROOT)),
        "policy": "Person training stage state is a non-mutating front door over temporal contracts. It describes current stage, staleness, permitted next-refresh classifications, and required evidence before any annual update changes person/program truth.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(args.db)
    rows = stage_rows(read_contracts(conn), generated_at)
    rollups = build_rollups(rows)
    write_csv(CSV_PATH, rows, STAGE_FIELDS)
    write_json(JSON_PATH, rows)
    write_csv(ROLLUP_CSV_PATH, rollups, ROLLUP_FIELDS)
    write_json(ROLLUP_JSON_PATH, rollups)
    with conn:
        write_db(conn, "person_training_stage_state", rows, STAGE_FIELDS)
        write_db(conn, "training_stage_state_rollups", rollups, ROLLUP_FIELDS)
    conn.close()

    summary = summary_payload(rows, rollups, generated_at)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
