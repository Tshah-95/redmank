#!/usr/bin/env python3
"""Materialize explicit temporal contracts for future trainee-state refreshes."""

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

CSV_PATH = ARTIFACTS / "training_temporal_contracts.csv"
JSON_PATH = ARTIFACTS / "training_temporal_contracts.json"
ROLLUP_CSV_PATH = ARTIFACTS / "training_temporal_contract_rollups.csv"
ROLLUP_JSON_PATH = ARTIFACTS / "training_temporal_contract_rollups.json"
SUMMARY_PATH = ARTIFACTS / "training_temporal_contract_summary.json"

CONTRACT_FIELDS = [
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
    "expected_next_stage",
    "expected_next_date",
    "expected_exit_date",
    "stale_after_date",
    "clock_model",
    "current_temporal_state_code",
    "temporal_validity_status",
    "policy_lane",
    "diff_readiness_status",
    "next_refresh_contract",
    "if_missing_change_type",
    "if_same_stage_change_type",
    "if_expected_next_stage_change_type",
    "allowed_auto_diff_outcomes_json",
    "review_trigger_json",
    "evidence_required_to_retain",
    "evidence_required_to_advance",
    "evidence_required_to_complete",
    "stale_information_policy",
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
    "projected_refresh_date",
    "contract_count",
    "person_count",
    "program_count",
    "expected_advancement_contract_count",
    "expected_completion_contract_count",
    "source_refresh_contract_count",
    "manual_review_contract_count",
    "carry_forward_contract_count",
    "stale_by_refresh_count",
    "fresh_observation_required_count",
    "auto_classifiable_transition_count",
    "dominant_next_refresh_contract",
    "dominant_diff_readiness_status",
    "guardrail_status",
    "stale_information_policy",
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


def read_plan_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM training_state_transition_plan
            ORDER BY role, trainee_category, program_name, display_name, plan_key
            """
        )
    ]


def canonical_person_program_key(row: dict) -> str:
    return key_for(
        "person_program",
        (
            row.get("person_key") or "",
            row.get("program_name") or "",
            row.get("role") or "",
            row.get("trainee_category") or "",
        ),
    )


def current_temporal_state_code(row: dict) -> str:
    lane = row.get("policy_lane") or ""
    state_status = row.get("state_machine_status") or ""
    if lane == "deterministic_expected_advancement":
        return "ANNUAL_CLOCK_EXPECTED_ADVANCEMENT"
    if lane == "deterministic_expected_completion":
        return "TERMINAL_STAGE_EXPECTED_COMPLETION"
    if lane == "source_refresh_required":
        return "VARIABLE_DURATION_SOURCE_REFRESH"
    if lane == "manual_review_required":
        return "AMBIGUOUS_OR_OUT_OF_RULE_REVIEW"
    if state_status == "terminal_year_active":
        return "TERMINAL_STAGE_ACTIVE"
    if state_status == "annual_clock_active":
        return "ANNUAL_CLOCK_ACTIVE"
    return "CURRENT_OBSERVATION"


def temporal_validity_status(row: dict) -> str:
    if as_int(row.get("stale_by_refresh")):
        return "stale_by_projected_refresh"
    if row.get("stale_after_date"):
        return "valid_until_stale_after"
    return "valid_until_fresh_source_contradiction"


def next_refresh_contract(row: dict) -> str:
    return {
        "deterministic_expected_advancement": "advance_only_if_fresh_expected_stage_observed",
        "deterministic_expected_completion": "complete_or_alumni_only_if_absent_after_stale_or_endpoint_observed",
        "source_refresh_required": "retain_only_if_fresh_source_reobserves",
        "manual_review_required": "do_not_mutate_without_review",
        "pending_annual_advancement": "retain_until_expected_next_date_or_fresh_contradiction",
        "pending_terminal_completion": "retain_until_stale_after_or_fresh_contradiction",
        "carry_forward_no_change": "retain_until_fresh_source_contradiction",
    }.get(row.get("policy_lane") or "", "review_before_mutation")


def stale_information_policy(row: dict) -> str:
    return {
        "deterministic_expected_advancement": "time opens advancement window; stale same-stage rows require fresh roster evidence",
        "deterministic_expected_completion": "absence after stale-after may be expected completion only after source refresh",
        "source_refresh_required": "time makes the row stale; do not carry forward without fresh public source",
        "manual_review_required": "time cannot resolve this state; keep in review until lifecycle/source label is resolved",
        "pending_annual_advancement": "not stale for advancement yet; retain unless contradicted by fresh source",
        "pending_terminal_completion": "not stale for completion yet; retain unless contradicted by fresh source",
        "carry_forward_no_change": "retain unless contradicted by fresh public source",
    }.get(row.get("policy_lane") or "", "review before treating old observation as current")


def allowed_auto_outcomes(row: dict) -> list[str]:
    lane = row.get("policy_lane") or ""
    if lane == "deterministic_expected_advancement":
        return ["advanced_expected_with_fresh_observation"]
    if lane == "deterministic_expected_completion":
        return ["removed_expected_completion_candidate", "completed_or_alumni_with_endpoint"]
    if lane == "carry_forward_no_change":
        return ["unchanged_expected"]
    return []


def review_triggers(row: dict) -> list[str]:
    lane = row.get("policy_lane") or ""
    triggers = []
    if lane == "deterministic_expected_advancement":
        triggers.extend(
            [
                "same_stage_after_expected_transition_without_fresh_observation",
                "missing_before_terminal_completion",
                "stage_regression",
                "different_program_family",
            ]
        )
    elif lane == "deterministic_expected_completion":
        triggers.extend(
            [
                "terminal_stage_still_present_without_new_source_date",
                "non_terminal_stage_after_expected_completion",
                "identity_or_program_conflict",
            ]
        )
    elif lane == "source_refresh_required":
        triggers.extend(
            [
                "missing_or_unchanged_without_fresh_source",
                "stage_change_outside_source_label_semantics",
            ]
        )
    elif lane == "manual_review_required":
        triggers.extend(["any_mutation_before_reviewer_resolution"])
    else:
        triggers.extend(["fresh_source_contradiction", "duplicate_person_program_state"])
    return triggers


def retain_evidence(row: dict) -> str:
    lane = row.get("policy_lane") or ""
    if lane == "source_refresh_required":
        return "fresh public source observation for the same person/program/state label"
    if lane == "manual_review_required":
        return "reviewer-resolved lifecycle/source-label decision plus fresh public source evidence"
    return "fresh public source observation if the row is stale or contradicted"


def advance_evidence(row: dict) -> str:
    if row.get("expected_next_stage") and row.get("policy_lane") == "deterministic_expected_advancement":
        return f"fresh same-person/same-program observation showing {row['expected_next_stage']}"
    if row.get("expected_next_stage"):
        return "fresh source evidence plus review because expected next stage is outside the active window"
    return "not auto-advanceable from this state"


def complete_evidence(row: dict) -> str:
    if row.get("policy_lane") == "deterministic_expected_completion":
        return "fresh source refresh showing absence after stale-after or a public alumni/completion endpoint"
    return "not auto-completable from this state"


def build_contracts(rows: list[dict]) -> list[dict]:
    contracts = []
    for row in rows:
        canonical_key = canonical_person_program_key(row)
        contract = {
            "contract_key": key_for("training_temporal_contract", (canonical_key, row.get("plan_key") or "")),
            "canonical_person_program_key": canonical_key,
            "person_key": row.get("person_key"),
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
            "current_stage_label": row.get("raw_stage_label"),
            "current_stage_code": row.get("normalized_stage"),
            "stage_family": row.get("stage_family"),
            "stage_index": row.get("stage_index"),
            "stage_rank": row.get("stage_rank"),
            "lifecycle_rule_key": row.get("lifecycle_rule_key"),
            "lifecycle_code": row.get("lifecycle_code"),
            "lifecycle_stage": row.get("lifecycle_stage"),
            "academic_year": row.get("academic_year"),
            "expected_next_stage": row.get("expected_next_stage"),
            "expected_next_date": row.get("expected_next_date"),
            "expected_exit_date": row.get("expected_exit_date"),
            "stale_after_date": row.get("stale_after_date"),
            "clock_model": row.get("clock_model"),
            "current_temporal_state_code": current_temporal_state_code(row),
            "temporal_validity_status": temporal_validity_status(row),
            "policy_lane": row.get("policy_lane"),
            "diff_readiness_status": row.get("diff_readiness_status"),
            "next_refresh_contract": next_refresh_contract(row),
            "if_missing_change_type": row.get("if_missing_change_type"),
            "if_same_stage_change_type": row.get("if_same_stage_change_type"),
            "if_expected_next_stage_change_type": row.get("if_expected_next_stage_change_type"),
            "allowed_auto_diff_outcomes_json": dumps(allowed_auto_outcomes(row)),
            "review_trigger_json": dumps(review_triggers(row)),
            "evidence_required_to_retain": retain_evidence(row),
            "evidence_required_to_advance": advance_evidence(row),
            "evidence_required_to_complete": complete_evidence(row),
            "stale_information_policy": stale_information_policy(row),
            "recommended_operator_action": row.get("recommended_operator_action"),
            "stale_by_refresh": as_int(row.get("stale_by_refresh")),
            "advance_due_by_refresh": as_int(row.get("advance_due_by_refresh")),
            "completion_window_by_refresh": as_int(row.get("completion_window_by_refresh")),
            "source_refresh_required_by_refresh": as_int(row.get("source_refresh_required_by_refresh")),
            "human_review_required_by_refresh": as_int(row.get("human_review_required_by_refresh")),
            "auto_classifiable_transition": as_int(row.get("auto_classifiable_transition")),
            "fresh_observation_required": as_int(row.get("fresh_observation_required")),
            "confidence": row.get("confidence"),
            "evidence_json": dumps(
                {
                    "derived_from": ["training_state_transition_plan"],
                    "plan_key": row.get("plan_key"),
                    "state_machine_status": row.get("state_machine_status"),
                    "readiness_status": row.get("readiness_status"),
                    "transition_classification_policy": row.get("transition_classification_policy"),
                    "base_evidence_requirement": row.get("evidence_requirement"),
                }
            ),
        }
        contracts.append({field: contract[field] for field in CONTRACT_FIELDS})
    return contracts


def scope_pairs(row: dict) -> list[tuple[str, str]]:
    role = row.get("role") or ""
    category = row.get("trainee_category") or role or "unknown"
    program = row.get("program_name") or ""
    lifecycle = row.get("lifecycle_code") or "none"
    institution = row.get("institution") or ""
    country_code = row.get("country_code") or ""
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
        ("temporal_state", row.get("current_temporal_state_code") or ""),
        ("next_refresh_contract", row.get("next_refresh_contract") or ""),
        ("diff_readiness_status", row.get("diff_readiness_status") or ""),
    ]
    return [(scope, value) for scope, value in pairs if value]


def guardrail_status(stats: Counter) -> str:
    if stats["manual_review_contract_count"]:
        return "review_bound"
    if stats["source_refresh_contract_count"]:
        return "source_refresh_bound"
    if stats["expected_advancement_contract_count"] or stats["expected_completion_contract_count"]:
        return "deterministic_with_fresh_evidence"
    return "carry_forward_until_contradicted"


def rollup_policy(stats: Counter) -> str:
    if stats["manual_review_contract_count"]:
        return "do_not_auto_mutate_rows_in_this_scope_until_review_queue_is_resolved"
    if stats["source_refresh_contract_count"]:
        return "do_not_carry_forward_stale_rows_without_fresh_source_observations"
    if stats["expected_completion_contract_count"]:
        return "completion_absence_is_classifiable_after_stale_after_with_fresh_refresh"
    if stats["expected_advancement_contract_count"]:
        return "expected_advancement_is_classifiable_only_when_freshly_observed"
    return "retain_until_fresh_public_source_contradiction"


def rollup_action(stats: Counter) -> str:
    if stats["manual_review_contract_count"]:
        return "resolve_review_bound_lifecycle_or_source_labels"
    if stats["source_refresh_contract_count"]:
        return "refresh_sources_before_next_diff"
    if stats["expected_completion_contract_count"] and stats["expected_advancement_contract_count"]:
        return "reconcile_expected_advancements_and_completion_absences"
    if stats["expected_completion_contract_count"]:
        return "reconcile_expected_completion_absences"
    if stats["expected_advancement_contract_count"]:
        return "reconcile_expected_advancements"
    return "monitor_for_fresh_source_contradictions"


def build_rollups(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        for scope, value in scope_pairs(row):
            grouped[(scope, value)].append(row)

    rollups = []
    for (scope, value), group in grouped.items():
        stats = Counter()
        contracts = Counter(row.get("next_refresh_contract") or "" for row in group)
        diff = Counter(row.get("diff_readiness_status") or "" for row in group)
        roles = Counter(row.get("role") or "" for row in group)
        categories = Counter(row.get("trainee_category") or "" for row in group)
        programs = {row.get("program_name") or "" for row in group if row.get("program_name")}
        people = {row.get("person_key") or "" for row in group if row.get("person_key")}
        institutions = Counter(row.get("institution") or "" for row in group)
        countries = Counter(row.get("country") or "" for row in group)
        country_codes = Counter(row.get("country_code") or "" for row in group)
        lifecycle_codes = Counter(row.get("lifecycle_code") or "none" for row in group)
        refresh_dates = sorted({row.get("projected_refresh_date") or "" for row in group if row.get("projected_refresh_date")})
        for row in group:
            lane = row.get("policy_lane") or ""
            stats["expected_advancement_contract_count"] += int(lane == "deterministic_expected_advancement")
            stats["expected_completion_contract_count"] += int(lane == "deterministic_expected_completion")
            stats["source_refresh_contract_count"] += int(lane == "source_refresh_required")
            stats["manual_review_contract_count"] += int(lane == "manual_review_required")
            stats["carry_forward_contract_count"] += int(
                lane in {"pending_annual_advancement", "pending_terminal_completion", "carry_forward_no_change"}
            )
            stats["stale_by_refresh_count"] += as_int(row.get("stale_by_refresh"))
            stats["fresh_observation_required_count"] += as_int(row.get("fresh_observation_required"))
            stats["auto_classifiable_transition_count"] += as_int(row.get("auto_classifiable_transition"))
        status = guardrail_status(stats)
        program_name = value if scope == "program" else value.split("::", 1)[0] if scope == "program_role" else ""
        rollup = {
            "rollup_key": key_for("training_temporal_contract_rollup", (scope, value, refresh_dates[-1] if refresh_dates else "")),
            "rollup_scope": scope,
            "rollup_value": value,
            "institution": value if scope == "institution" else institutions.most_common(1)[0][0],
            "country": countries.most_common(1)[0][0],
            "country_code": value if scope == "country" else country_codes.most_common(1)[0][0],
            "role": value if scope == "role" else value.split("::", 1)[1] if scope in {"program_role", "institution_role"} else roles.most_common(1)[0][0],
            "trainee_category": value if scope == "trainee_category" else categories.most_common(1)[0][0],
            "program_name": program_name,
            "lifecycle_code": value if scope == "lifecycle_code" else lifecycle_codes.most_common(1)[0][0],
            "projected_refresh_date": refresh_dates[-1] if refresh_dates else "",
            "contract_count": len(group),
            "person_count": len(people),
            "program_count": len(programs),
            "expected_advancement_contract_count": stats["expected_advancement_contract_count"],
            "expected_completion_contract_count": stats["expected_completion_contract_count"],
            "source_refresh_contract_count": stats["source_refresh_contract_count"],
            "manual_review_contract_count": stats["manual_review_contract_count"],
            "carry_forward_contract_count": stats["carry_forward_contract_count"],
            "stale_by_refresh_count": stats["stale_by_refresh_count"],
            "fresh_observation_required_count": stats["fresh_observation_required_count"],
            "auto_classifiable_transition_count": stats["auto_classifiable_transition_count"],
            "dominant_next_refresh_contract": contracts.most_common(1)[0][0],
            "dominant_diff_readiness_status": diff.most_common(1)[0][0],
            "guardrail_status": status,
            "stale_information_policy": rollup_policy(stats),
            "recommended_operator_action": rollup_action(stats),
            "evidence_json": dumps(
                {
                    "next_refresh_contract_counts": dict(sorted(contracts.items())),
                    "diff_readiness_status_counts": dict(sorted(diff.items())),
                    "derived_from": ["training_temporal_contracts"],
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
    if table == "training_temporal_contracts":
        conn.execute("DELETE FROM training_temporal_contract_batch_packets")
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    field_sql = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    conn.executemany(
        f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def summary_payload(contracts: list[dict], rollups: list[dict], generated_at: str) -> dict:
    lanes = Counter(row["policy_lane"] for row in contracts)
    current_states = Counter(row["current_temporal_state_code"] for row in contracts)
    next_contracts = Counter(row["next_refresh_contract"] for row in contracts)
    guardrails = Counter(row["guardrail_status"] for row in rollups)
    rollup_scopes = Counter(row["rollup_scope"] for row in rollups)
    corpus = next((row for row in rollups if row["rollup_scope"] == "corpus"), {})
    return {
        "generated_at": generated_at,
        "projected_refresh_date": corpus.get("projected_refresh_date", ""),
        "contract_rows": len(contracts),
        "rollup_rows": len(rollups),
        "person_count": len({row["person_key"] for row in contracts}),
        "program_count": len({row.get("program_name") or "" for row in contracts if row.get("program_name")}),
        "by_policy_lane": dict(sorted(lanes.items())),
        "by_current_temporal_state_code": dict(sorted(current_states.items())),
        "by_next_refresh_contract": dict(sorted(next_contracts.items())),
        "by_rollup_guardrail_status": dict(sorted(guardrails.items())),
        "by_rollup_scope": dict(sorted(rollup_scopes.items())),
        "auto_classifiable_transition_rows": sum(row["auto_classifiable_transition"] for row in contracts),
        "fresh_observation_required_rows": sum(row["fresh_observation_required"] for row in contracts),
        "stale_by_refresh_rows": sum(row["stale_by_refresh"] for row in contracts),
        "source_refresh_required_rows": sum(row["source_refresh_required_by_refresh"] for row in contracts),
        "human_review_required_rows": sum(row["human_review_required_by_refresh"] for row in contracts),
        "corpus_guardrail_status": corpus.get("guardrail_status", ""),
        "corpus_stale_information_policy": corpus.get("stale_information_policy", ""),
        "corpus_recommended_operator_action": corpus.get("recommended_operator_action", ""),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "rollup_csv": str(ROLLUP_CSV_PATH.relative_to(ROOT)),
        "rollup_json": str(ROLLUP_JSON_PATH.relative_to(ROOT)),
        "policy": "Temporal contracts are non-mutating. They define how future fresh observations, absences, unchanged stages, and expected next stages can be classified before any person/program truth is updated.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(args.db)
    contracts = build_contracts(read_plan_rows(conn))
    rollups = build_rollups(contracts)

    write_csv(CSV_PATH, contracts, CONTRACT_FIELDS)
    write_json(JSON_PATH, contracts)
    write_csv(ROLLUP_CSV_PATH, rollups, ROLLUP_FIELDS)
    write_json(ROLLUP_JSON_PATH, rollups)
    with conn:
        write_db(conn, "training_temporal_contracts", contracts, CONTRACT_FIELDS)
        write_db(conn, "training_temporal_contract_rollups", rollups, ROLLUP_FIELDS)
    conn.close()

    summary = summary_payload(contracts, rollups, generated_at)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
