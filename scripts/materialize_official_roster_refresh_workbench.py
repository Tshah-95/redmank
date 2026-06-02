#!/usr/bin/env python3
"""Materialize source/program-level refresh contracts for official trainee rosters."""

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

CSV_PATH = ARTIFACTS / "official_roster_refresh_workbench.csv"
JSON_PATH = ARTIFACTS / "official_roster_refresh_workbench.json"
SUMMARY_PATH = ARTIFACTS / "official_roster_refresh_workbench_summary.json"

FIELDS = [
    "refresh_key",
    "source_key",
    "source_url",
    "source_title",
    "source_type",
    "http_status",
    "source_classification",
    "quality_tier",
    "program_name",
    "role",
    "trainee_category",
    "projected_refresh_date",
    "contract_count",
    "person_count",
    "lifecycle_codes",
    "policy_lane_counts_json",
    "diff_readiness_counts_json",
    "expected_advancement_count",
    "expected_completion_count",
    "source_refresh_required_count",
    "manual_review_required_count",
    "stale_by_refresh_count",
    "fresh_observation_required_count",
    "auto_classifiable_transition_count",
    "refresh_lane",
    "refresh_priority",
    "refresh_difficulty",
    "requires_manual_review",
    "expected_change_summary",
    "evidence_required",
    "recommended_next_action",
    "collector_hint",
    "parser_status",
    "source_metadata_json",
    "sample_people_json",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key_for(parts: tuple[str, ...]) -> str:
    return "official_roster_refresh_" + sha256_text(dumps(parts))[:20]


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def read_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT t.*, s.source_url, s.title AS source_title, s.source_type,
                   s.http_status, s.classification AS source_classification,
                   s.quality_tier, s.metadata_json AS source_metadata_json
            FROM training_temporal_contracts t
            LEFT JOIN sources s ON s.source_key = t.source_key
            WHERE t.fresh_observation_required = 1
              AND COALESCE(t.source_key, '') <> ''
            ORDER BY t.source_key, t.program_name, t.role, t.display_name
            """
        )
    ]


def refresh_lane(policy_counts: Counter) -> str:
    expected = policy_counts.get("deterministic_expected_advancement", 0) + policy_counts.get(
        "deterministic_expected_completion", 0
    )
    source_bound = policy_counts.get("source_refresh_required", 0)
    review_bound = policy_counts.get("manual_review_required", 0)
    if review_bound and expected:
        return "mixed_expected_transition_and_manual_review"
    if review_bound:
        return "manual_lifecycle_or_source_label_review"
    if source_bound and expected:
        return "mixed_expected_transition_and_source_refresh"
    if source_bound:
        return "source_reobservation_required"
    if expected:
        return "expected_transition_reconciliation"
    return "fresh_reobservation_monitor"


def refresh_difficulty(contract_count: int, policy_counts: Counter, program_count: int) -> str:
    if policy_counts.get("manual_review_required", 0):
        return "manual_review_required"
    if program_count > 3:
        return "multi_program_source_refresh"
    if policy_counts.get("source_refresh_required", 0) and (
        policy_counts.get("deterministic_expected_advancement", 0)
        or policy_counts.get("deterministic_expected_completion", 0)
    ):
        return "mixed_source_and_expected_transition"
    if contract_count >= 50:
        return "large_roster_expected_transition"
    return "standard_roster_refresh"


def recommended_action(lane: str) -> str:
    return {
        "mixed_expected_transition_and_manual_review": "refresh_source_then_review_lifecycle_labels_before_state_mutation",
        "manual_lifecycle_or_source_label_review": "refresh_source_and_resolve_lifecycle_or_stage_label_review",
        "mixed_expected_transition_and_source_refresh": "refresh_source_then_classify_expected_transitions_and_source_bound_reobservations",
        "source_reobservation_required": "refresh_source_before_retaining_or_removing_source_bound_states",
        "expected_transition_reconciliation": "refresh_source_and_compare_against_expected_next_stage_or_completion",
        "fresh_reobservation_monitor": "refresh_source_and_retain_until_fresh_contradiction",
    }.get(lane, "refresh_source_then_review_before_mutation")


def evidence_required(lane: str) -> str:
    if "manual" in lane:
        return "Fresh official roster observation plus reviewer-resolved lifecycle/source-label semantics before mutating states."
    if "source_refresh" in lane or "source_reobservation" in lane:
        return "Fresh official source observation for the same person/program/state label before retaining, advancing, or removing source-bound rows."
    return "Fresh official roster observation showing expected next stage, terminal absence after stale-after, or an explicit alumni/completion endpoint."


def collector_hint(source_url: str, source_type: str) -> str:
    if "mstp" in (source_url or "").lower():
        return "python3 scripts/scrape_penn_mstp_students.py"
    if source_type == "penn_affiliated_source_discovery":
        return "python3 scripts/scrape_penn_affiliated_rosters.py"
    if "penn_gme_gap" in (source_url or "") or "med.upenn.edu" in (source_url or "") or "dental.upenn.edu" in (source_url or ""):
        return "python3 scripts/scrape_penn_gme_gap_rosters.py"
    return "python3 scripts/scrape_penn_training.py"


def parser_status(source_type: str, source_classification: str, source_url: str) -> str:
    text = " ".join([source_type or "", source_classification or "", source_url or ""]).lower()
    if "mstp" in text:
        return "mstp_directory_parser_available"
    if "penn_affiliated" in text:
        return "affiliated_roster_parser_available_or_preserved"
    if "penn_gme_gap" in text or "med.upenn.edu" in text or "dental.upenn.edu" in text:
        return "gap_roster_parser_available_or_review_queued"
    if "pennmedicine" in text or "chop.edu" in text:
        return "core_roster_parser_available"
    return "parser_support_review_required"


def summarize_expected(policy_counts: Counter) -> str:
    parts = []
    if policy_counts.get("deterministic_expected_advancement", 0):
        parts.append(f"{policy_counts['deterministic_expected_advancement']} expected advancement")
    if policy_counts.get("deterministic_expected_completion", 0):
        parts.append(f"{policy_counts['deterministic_expected_completion']} expected completion")
    if policy_counts.get("source_refresh_required", 0):
        parts.append(f"{policy_counts['source_refresh_required']} source-bound retention/removal")
    if policy_counts.get("manual_review_required", 0):
        parts.append(f"{policy_counts['manual_review_required']} lifecycle/source-label review")
    return "; ".join(parts) if parts else "fresh reobservation required"


def build_rows(raw_rows: list[dict], generated_at: str) -> list[dict]:
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in raw_rows:
        grouped[(row.get("source_key") or "", row.get("program_name") or "", row.get("role") or "")].append(row)
    output = []
    for (source_key, program_name, role), rows in grouped.items():
        first = rows[0]
        policy_counts = Counter(row.get("policy_lane") or "" for row in rows)
        diff_counts = Counter(row.get("diff_readiness_status") or "" for row in rows)
        lifecycle_codes = sorted({row.get("lifecycle_code") or "none" for row in rows})
        trainee_categories = Counter(row.get("trainee_category") or "" for row in rows)
        projected_dates = sorted({row.get("projected_refresh_date") or "" for row in rows if row.get("projected_refresh_date")})
        person_keys = {row.get("person_key") or "" for row in rows if row.get("person_key")}
        program_names = {row.get("program_name") or "" for row in rows if row.get("program_name")}
        lane = refresh_lane(policy_counts)
        difficulty = refresh_difficulty(len(rows), policy_counts, len(program_names))
        manual_review = 1 if policy_counts.get("manual_review_required", 0) else 0
        priority = 700 + min(len(rows), 250)
        if policy_counts.get("manual_review_required", 0):
            priority += 80
        if policy_counts.get("source_refresh_required", 0):
            priority += 45
        if policy_counts.get("deterministic_expected_advancement", 0) or policy_counts.get(
            "deterministic_expected_completion", 0
        ):
            priority += 60
        source_url = first.get("source_url") or ""
        source_type = first.get("source_type") or ""
        source_classification = first.get("source_classification") or ""
        metadata = {}
        try:
            metadata = json.loads(first.get("source_metadata_json") or "{}")
        except json.JSONDecodeError:
            metadata = {"raw_metadata_parse_error": True}
        sample_people = [
            {
                "person_key": row.get("person_key"),
                "display_name": row.get("display_name"),
                "current_stage_code": row.get("current_stage_code"),
                "current_stage_label": row.get("current_stage_label"),
                "expected_next_stage": row.get("expected_next_stage"),
                "next_refresh_contract": row.get("next_refresh_contract"),
                "stale_after_date": row.get("stale_after_date"),
            }
            for row in sorted(rows, key=lambda item: item.get("display_name") or "")[:8]
        ]
        evidence = {
            "derived_from": ["training_temporal_contracts", "sources"],
            "policy_lane_counts": dict(sorted(policy_counts.items())),
            "diff_readiness_counts": dict(sorted(diff_counts.items())),
            "source": {
                "source_key": source_key,
                "source_url": source_url,
                "source_title": first.get("source_title"),
                "http_status": first.get("http_status"),
                "source_classification": source_classification,
                "quality_tier": first.get("quality_tier"),
            },
            "non_mutating_policy": (
                "Refresh workbench rows plan source refresh and transition classification only; "
                "person_training_states mutate only through fresh observations, expected terminal absence, or reviewer decisions."
            ),
        }
        output.append(
            {
                "refresh_key": key_for((source_key, program_name, role)),
                "source_key": source_key,
                "source_url": source_url,
                "source_title": first.get("source_title") or "",
                "source_type": source_type,
                "http_status": as_int(first.get("http_status")),
                "source_classification": source_classification,
                "quality_tier": first.get("quality_tier") or "",
                "program_name": program_name,
                "role": role,
                "trainee_category": trainee_categories.most_common(1)[0][0] if trainee_categories else "",
                "projected_refresh_date": projected_dates[-1] if projected_dates else "",
                "contract_count": len(rows),
                "person_count": len(person_keys),
                "lifecycle_codes": "; ".join(lifecycle_codes),
                "policy_lane_counts_json": dumps(dict(sorted(policy_counts.items()))),
                "diff_readiness_counts_json": dumps(dict(sorted(diff_counts.items()))),
                "expected_advancement_count": policy_counts.get("deterministic_expected_advancement", 0),
                "expected_completion_count": policy_counts.get("deterministic_expected_completion", 0),
                "source_refresh_required_count": policy_counts.get("source_refresh_required", 0),
                "manual_review_required_count": policy_counts.get("manual_review_required", 0),
                "stale_by_refresh_count": sum(as_int(row.get("stale_by_refresh")) for row in rows),
                "fresh_observation_required_count": sum(as_int(row.get("fresh_observation_required")) for row in rows),
                "auto_classifiable_transition_count": sum(as_int(row.get("auto_classifiable_transition")) for row in rows),
                "refresh_lane": lane,
                "refresh_priority": priority,
                "refresh_difficulty": difficulty,
                "requires_manual_review": manual_review,
                "expected_change_summary": summarize_expected(policy_counts),
                "evidence_required": evidence_required(lane),
                "recommended_next_action": recommended_action(lane),
                "collector_hint": collector_hint(source_url, source_type),
                "parser_status": parser_status(source_type, source_classification, source_url),
                "source_metadata_json": dumps(metadata),
                "sample_people_json": dumps(sample_people),
                "evidence_json": dumps(evidence),
                "generated_at": generated_at,
            }
        )
    return sorted(output, key=lambda item: (-as_int(item["refresh_priority"]), -as_int(item["contract_count"]), item["source_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_roster_refresh_workbench")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO official_roster_refresh_workbench ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_lane = Counter(row["refresh_lane"] for row in rows)
    by_difficulty = Counter(row["refresh_difficulty"] for row in rows)
    by_role_lane = Counter(f"{row['role']}:{row['refresh_lane']}" for row in rows)
    payload = {
        "generated_at": generated_at,
        "refresh_rows": len(rows),
        "source_count": len({row["source_key"] for row in rows}),
        "program_count": len({row["program_name"] for row in rows}),
        "source_program_person_count": sum(as_int(row["person_count"]) for row in rows),
        "person_count_policy": "Summed source/program person counts, not deduplicated unique people; one trainee can correctly appear in multiple source/program refresh contracts.",
        "contract_count": sum(as_int(row["contract_count"]) for row in rows),
        "fresh_observation_required_count": sum(as_int(row["fresh_observation_required_count"]) for row in rows),
        "by_refresh_lane": dict(sorted(by_lane.items())),
        "by_refresh_difficulty": dict(sorted(by_difficulty.items())),
        "by_role_and_refresh_lane": dict(sorted(by_role_lane.items())),
        "top_refresh_rows": [
            {
                "source_key": row["source_key"],
                "program_name": row["program_name"],
                "role": row["role"],
                "refresh_lane": row["refresh_lane"],
                "refresh_priority": row["refresh_priority"],
                "contract_count": row["contract_count"],
                "expected_change_summary": row["expected_change_summary"],
                "recommended_next_action": row["recommended_next_action"],
                "source_url": row["source_url"],
            }
            for row in rows[:25]
        ],
        "policy": (
            "This artifact is non-mutating. It turns person-level temporal contracts into source/program refresh "
            "contracts so official roster collectors can refresh the right public URL and classify changes through the state machine."
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
    rows = build_rows(read_rows(conn), generated_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"refresh_rows": len(rows), "contract_count": sum(as_int(row["contract_count"]) for row in rows)}))


if __name__ == "__main__":
    main()
