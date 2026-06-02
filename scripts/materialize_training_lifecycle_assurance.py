#!/usr/bin/env python3
"""Materialize compact lifecycle assurance rollups for longitudinal trainee diffs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "training_lifecycle_assurance_rollups.csv"
SUMMARY_PATH = ARTIFACTS / "training_lifecycle_assurance_summary.json"

FIELDS = [
    "rollup_key",
    "rollup_scope",
    "rollup_value",
    "role",
    "trainee_category",
    "program_name",
    "lifecycle_code",
    "projected_refresh_date",
    "state_observation_count",
    "person_count",
    "program_count",
    "annual_clock_count",
    "expected_advancement_count",
    "expected_completion_count",
    "source_refresh_required_count",
    "human_review_required_count",
    "stale_by_refresh_count",
    "unexpected_absence_review_count",
    "deterministic_transition_count",
    "source_bound_transition_count",
    "review_bound_transition_count",
    "assurance_status",
    "diff_readiness_status",
    "stale_information_policy",
    "recommended_operator_action",
    "evidence_json",
]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def rollup_key(parts: tuple[str, ...]) -> str:
    return f"lifecycle_assurance_{sha256_text(json.dumps(parts, sort_keys=True))[:20]}"


def read_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT r.state_id, r.person_key, r.display_name, r.role, r.program_name,
                   r.trainee_category, r.lifecycle_code, r.refresh_policy,
                   r.expected_transition_type, r.stale_after_date,
                   r.projected_refresh_date, r.readiness_status,
                   r.expected_if_missing_on_refresh,
                   r.expected_if_same_stage_on_refresh,
                   r.expected_if_next_stage_on_refresh,
                   r.advance_due_by_refresh, r.stale_by_refresh,
                   r.completion_window_by_refresh,
                   r.requires_source_refresh_by_refresh,
                   r.requires_human_review_by_refresh,
                   a.clock_model, a.state_machine_status,
                   a.recommended_action AS state_machine_action
            FROM training_state_refresh_expectations r
            LEFT JOIN training_state_machine_audit a
              ON a.state_id = r.state_id
             AND a.person_key = r.person_key
             AND COALESCE(a.program_name, '') = COALESCE(r.program_name, '')
            ORDER BY r.role, r.trainee_category, r.program_name, r.lifecycle_code, r.person_key
            """
        )
    ]


def scope_pairs(row: dict) -> list[tuple[str, str]]:
    role = row.get("role") or ""
    category = row.get("trainee_category") or role or "unknown"
    program = row.get("program_name") or ""
    lifecycle = row.get("lifecycle_code") or "none"
    scopes = [
        ("corpus", "penn_medical_trainees"),
        ("role", role),
        ("trainee_category", category),
        ("program", program),
        ("program_role", f"{program}::{role}" if program and role else ""),
        ("lifecycle_code", lifecycle),
        ("role_lifecycle_code", f"{role}::{lifecycle}" if role and lifecycle else ""),
        ("readiness_status", row.get("readiness_status") or ""),
    ]
    return [(scope, value) for scope, value in scopes if value]


def assurance_status(stats: Counter) -> str:
    if stats["human_review_required_count"]:
        return "mixed_with_human_review"
    if stats["source_refresh_required_count"]:
        return "source_refresh_bound"
    if stats["expected_advancement_count"] or stats["expected_completion_count"]:
        return "deterministic_clock_supported"
    return "stable_or_no_change_expected"


def diff_readiness_status(stats: Counter) -> str:
    if stats["human_review_required_count"]:
        return "diff_requires_review_queue"
    if stats["unexpected_absence_review_count"]:
        return "diff_can_classify_but_missing_rows_need_review"
    if stats["source_refresh_required_count"]:
        return "diff_requires_fresh_source_before_retention"
    if stats["expected_advancement_count"] or stats["expected_completion_count"]:
        return "diff_expected_change_supported"
    return "diff_no_expected_change"


def stale_information_policy(stats: Counter) -> str:
    if stats["human_review_required_count"]:
        return "do_not_auto_mutate; stale rows enter review"
    if stats["source_refresh_required_count"]:
        return "stale only when source refresh fails to reconfirm"
    if stats["expected_completion_count"]:
        return "absence after stale-after is expected completion/alumni candidate"
    if stats["expected_advancement_count"]:
        return "same stage after expected-next-date requires fresh source evidence"
    return "retain unless contradicted by fresh public source"


def recommended_action(stats: Counter) -> str:
    if stats["human_review_required_count"]:
        return "review_lifecycle_rule_source_label_or_identity_before_mutation"
    if stats["source_refresh_required_count"]:
        return "refresh_source_before_carrying_forward_state"
    if stats["expected_completion_count"] and stats["expected_advancement_count"]:
        return "accept_expected_advancements_and_completion_absences_with_fresh_observation"
    if stats["expected_completion_count"]:
        return "allow_completion_absence_or_confirm_alumni_endpoint"
    if stats["expected_advancement_count"]:
        return "accept_expected_stage_advancement_only_when_freshly_observed"
    return "monitor_next_refresh"


def build_rollups(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        for scope, value in scope_pairs(row):
            grouped[(scope, value)].append(row)

    result = []
    for (scope, value), group in grouped.items():
        stats = Counter()
        people = {row["person_key"] for row in group}
        programs = {row.get("program_name") or "" for row in group if row.get("program_name")}
        roles = Counter(row.get("role") or "" for row in group)
        categories = Counter(row.get("trainee_category") or "" for row in group)
        lifecycle_codes = Counter(row.get("lifecycle_code") or "none" for row in group)
        readiness = Counter(row.get("readiness_status") or "" for row in group)
        missing_expectations = Counter(row.get("expected_if_missing_on_refresh") or "" for row in group)
        for row in group:
            stats["annual_clock_count"] += int((row.get("clock_model") or "") == "annual_gme_july")
            stats["expected_advancement_count"] += int(row.get("readiness_status") == "expected_advancement_window")
            stats["expected_completion_count"] += int(row.get("readiness_status") == "expected_completion_window")
            stats["source_refresh_required_count"] += int(row.get("requires_source_refresh_by_refresh") or 0)
            stats["human_review_required_count"] += int(row.get("requires_human_review_by_refresh") or 0)
            stats["stale_by_refresh_count"] += int(row.get("stale_by_refresh") or 0)
            stats["unexpected_absence_review_count"] += int(
                row.get("expected_if_missing_on_refresh") == "unexpected_absence_review"
            )
        stats["deterministic_transition_count"] = stats["expected_advancement_count"] + stats["expected_completion_count"]
        stats["source_bound_transition_count"] = stats["source_refresh_required_count"]
        stats["review_bound_transition_count"] = stats["human_review_required_count"]
        projected_dates = sorted({row.get("projected_refresh_date") or "" for row in group if row.get("projected_refresh_date")})
        role = roles.most_common(1)[0][0] if scope in {"role", "program_role", "role_lifecycle_code"} else ""
        category = categories.most_common(1)[0][0] if scope == "trainee_category" else ""
        program = value if scope == "program" else value.split("::", 1)[0] if scope == "program_role" else ""
        lifecycle_code = value if scope == "lifecycle_code" else value.split("::", 1)[1] if scope == "role_lifecycle_code" else ""
        row = {
            "rollup_key": rollup_key((scope, value, projected_dates[-1] if projected_dates else "")),
            "rollup_scope": scope,
            "rollup_value": value,
            "role": role,
            "trainee_category": category,
            "program_name": program,
            "lifecycle_code": lifecycle_code,
            "projected_refresh_date": projected_dates[-1] if projected_dates else date.today().isoformat(),
            "state_observation_count": len(group),
            "person_count": len(people),
            "program_count": len(programs),
            "annual_clock_count": stats["annual_clock_count"],
            "expected_advancement_count": stats["expected_advancement_count"],
            "expected_completion_count": stats["expected_completion_count"],
            "source_refresh_required_count": stats["source_refresh_required_count"],
            "human_review_required_count": stats["human_review_required_count"],
            "stale_by_refresh_count": stats["stale_by_refresh_count"],
            "unexpected_absence_review_count": stats["unexpected_absence_review_count"],
            "deterministic_transition_count": stats["deterministic_transition_count"],
            "source_bound_transition_count": stats["source_bound_transition_count"],
            "review_bound_transition_count": stats["review_bound_transition_count"],
            "assurance_status": assurance_status(stats),
            "diff_readiness_status": diff_readiness_status(stats),
            "stale_information_policy": stale_information_policy(stats),
            "recommended_operator_action": recommended_action(stats),
            "evidence_json": json.dumps(
                {
                    "readiness_status_counts": dict(sorted(readiness.items())),
                    "missing_expectation_counts": dict(sorted(missing_expectations.items())),
                    "dominant_role_counts": dict(sorted(roles.items())),
                    "dominant_trainee_category_counts": dict(sorted(categories.items())),
                    "dominant_lifecycle_code_counts": dict(sorted(lifecycle_codes.items())),
                    "derived_from": [
                        "training_state_machine_audit",
                        "training_state_refresh_expectations",
                    ],
                },
                sort_keys=True,
            ),
        }
        result.append({field: row[field] for field in FIELDS})
    return sorted(result, key=lambda row: (row["rollup_scope"], row["rollup_value"]))


def write_csv(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM training_lifecycle_assurance_rollups")
    if not rows:
        return
    fields = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO training_lifecycle_assurance_rollups ({fields}) VALUES ({placeholders})",
        rows,
    )


def summary_payload(rows: list[dict], source_rows: list[dict]) -> dict:
    assurance = Counter(row["assurance_status"] for row in rows)
    diff = Counter(row["diff_readiness_status"] for row in rows)
    scope = Counter(row["rollup_scope"] for row in rows)
    corpus = next((row for row in rows if row["rollup_scope"] == "corpus"), {})
    return {
        "rollup_rows": len(rows),
        "source_state_rows": len(source_rows),
        "projected_refresh_date": corpus.get("projected_refresh_date", ""),
        "corpus_assurance_status": corpus.get("assurance_status", ""),
        "corpus_diff_readiness_status": corpus.get("diff_readiness_status", ""),
        "corpus_stale_information_policy": corpus.get("stale_information_policy", ""),
        "corpus_recommended_operator_action": corpus.get("recommended_operator_action", ""),
        "corpus_counts": {
            "state_observation_count": corpus.get("state_observation_count", 0),
            "person_count": corpus.get("person_count", 0),
            "program_count": corpus.get("program_count", 0),
            "expected_advancement_count": corpus.get("expected_advancement_count", 0),
            "expected_completion_count": corpus.get("expected_completion_count", 0),
            "source_refresh_required_count": corpus.get("source_refresh_required_count", 0),
            "human_review_required_count": corpus.get("human_review_required_count", 0),
            "stale_by_refresh_count": corpus.get("stale_by_refresh_count", 0),
        },
        "by_assurance_status": dict(sorted(assurance.items())),
        "by_diff_readiness_status": dict(sorted(diff.items())),
        "by_rollup_scope": dict(sorted(scope.items())),
        "csv": str(CSV_PATH.relative_to(ROOT)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    rows = read_rows(conn)
    rollups = build_rollups(rows)
    write_csv(rollups)
    with conn:
        write_db(conn, rollups)
    conn.close()
    summary = summary_payload(rollups, rows)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
