#!/usr/bin/env python3
"""Diff two exported training-state snapshots."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path


STAGE_FAMILY_PRIORITY = {
    "clinical_postgraduate": 90,
    "fellowship": 80,
    "medical_school": 70,
    "research_phase": 60,
    "clinical_postgraduate_research": 55,
    "post_training_or_alumni": 20,
    "unknown": 0,
}


def canonical_rank(row: dict) -> tuple[int, int, float, str]:
    stage_rank = int(row.get("stage_rank") or 999)
    has_stage_index = int(bool(row.get("stage_index")))
    family_rank = STAGE_FAMILY_PRIORITY.get(row.get("stage_family") or "", 0)
    confidence = float(row.get("confidence") or 0.0)
    observed = row.get("observed_at") or ""
    return (has_stage_index, confidence, family_rank, stage_rank, observed)


def read_rows(path: Path) -> tuple[dict[tuple[str, str], dict], int, int]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    result = {}
    duplicate_keys = 0
    for row in rows:
        key = (row["person_key"], row.get("program_name") or "")
        if key in result:
            duplicate_keys += 1
            if canonical_rank(row) <= canonical_rank(result[key]):
                continue
        result[key] = row
    return result, len(rows), duplicate_keys


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def classify_change(old: dict | None, new: dict | None, compare_date: date) -> dict:
    if old and not new:
        stale_after = parse_date(old.get("stale_after_date"))
        expected = bool(stale_after and stale_after <= compare_date)
        transition_type = old.get("expected_transition_type", "")
        if expected and transition_type == "expected_completion":
            notes = "Terminal state passed stale-after date; disappearance is consistent with completion."
        elif expected:
            notes = "Old state had passed stale-after date."
        else:
            notes = "Old state disappeared before expected stale-after date."
        return {
            "change_type": "removed_expected_stale" if expected else "removed_unexpected",
            "old_stage": old.get("normalized_stage"),
            "new_stage": "",
            "old_stale_after_date": old.get("stale_after_date", ""),
            "notes": notes,
        }
    if new and not old:
        return {
            "change_type": "added",
            "old_stage": "",
            "new_stage": new.get("normalized_stage"),
            "old_stale_after_date": "",
            "notes": "New person/program state observation.",
        }
    assert old and new
    if old.get("normalized_stage") != new.get("normalized_stage"):
        expected_next = old.get("expected_next_stage")
        expected = bool(expected_next and expected_next == new.get("normalized_stage"))
        return {
            "change_type": "advanced_expected" if expected else "stage_changed_review",
            "old_stage": old.get("normalized_stage"),
            "new_stage": new.get("normalized_stage"),
            "old_stale_after_date": old.get("stale_after_date", ""),
            "notes": "New stage matches prior expected_next_stage." if expected else "Stage changed outside the prior expected transition.",
        }
    return {
        "change_type": "unchanged",
        "old_stage": old.get("normalized_stage"),
        "new_stage": new.get("normalized_stage"),
        "old_stale_after_date": old.get("stale_after_date", ""),
        "notes": "Same normalized state.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", required=True, type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--out-csv", type=Path, default=Path("artifacts/data/training_state_diff.csv"))
    parser.add_argument("--out-json", type=Path, default=Path("artifacts/data/training_state_diff_summary.json"))
    parser.add_argument("--out-rollup-csv", type=Path, default=Path("artifacts/data/training_state_diff_rollups.csv"))
    parser.add_argument("--compare-date", default=date.today().isoformat())
    args = parser.parse_args()

    old_rows, old_input_rows, old_duplicate_keys = read_rows(args.old)
    new_rows, new_input_rows, new_duplicate_keys = read_rows(args.new)
    compare_date = date.fromisoformat(args.compare_date)
    all_keys = sorted(set(old_rows) | set(new_rows))
    diff_rows = []
    for person_key, program_name in all_keys:
        old = old_rows.get((person_key, program_name))
        new = new_rows.get((person_key, program_name))
        change = classify_change(old, new, compare_date)
        source = new or old or {}
        diff_rows.append(
            {
                "person_key": person_key,
                "display_name": source.get("display_name", ""),
                "program_name": program_name,
                "role": source.get("role", ""),
                **change,
                "old_expected_next_stage": (old or {}).get("expected_next_stage", ""),
                "old_expected_next_date": (old or {}).get("expected_next_date", ""),
                "old_expected_exit_date": (old or {}).get("expected_exit_date", ""),
                "old_expected_transition_type": (old or {}).get("expected_transition_type", ""),
                "old_lifecycle_code": (old or {}).get("lifecycle_code", ""),
                "new_lifecycle_code": (new or {}).get("lifecycle_code", ""),
                "new_as_of_date": (new or {}).get("as_of_date", ""),
            }
        )

    args.out_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "person_key",
            "display_name",
            "program_name",
            "role",
            "change_type",
            "old_stage",
            "new_stage",
            "old_expected_next_stage",
            "old_expected_next_date",
            "old_expected_exit_date",
            "old_expected_transition_type",
            "old_lifecycle_code",
            "new_lifecycle_code",
            "old_stale_after_date",
            "new_as_of_date",
            "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(diff_rows)

    rollups: dict[tuple[str, str, str, str], int] = {}
    for row in diff_rows:
        key = (
            row.get("program_name", ""),
            row.get("role", ""),
            row.get("new_lifecycle_code") or row.get("old_lifecycle_code", ""),
            row["change_type"],
        )
        rollups[key] = rollups.get(key, 0) + 1
    with args.out_rollup_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["program_name", "role", "lifecycle_code", "change_type", "count"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for key, count in sorted(rollups.items()):
            program_name, role, lifecycle_code, change_type = key
            writer.writerow(
                {
                    "program_name": program_name,
                    "role": role,
                    "lifecycle_code": lifecycle_code,
                    "change_type": change_type,
                    "count": count,
                }
            )

    summary = {
        "old": str(args.old),
        "new": str(args.new),
        "compare_date": compare_date.isoformat(),
        "rows": len(diff_rows),
        "old_input_rows": old_input_rows,
        "new_input_rows": new_input_rows,
        "old_canonical_keys": len(old_rows),
        "new_canonical_keys": len(new_rows),
        "old_duplicate_keys_collapsed": old_duplicate_keys,
        "new_duplicate_keys_collapsed": new_duplicate_keys,
        "by_change_type": {},
        "rollup_csv": str(args.out_rollup_csv),
        "by_role_and_change_type": {},
        "by_lifecycle_code_and_change_type": {},
    }
    for row in diff_rows:
        summary["by_change_type"][row["change_type"]] = summary["by_change_type"].get(row["change_type"], 0) + 1
        role_key = f"{row.get('role', '')}:{row['change_type']}"
        lifecycle_key = f"{row.get('new_lifecycle_code') or row.get('old_lifecycle_code', '')}:{row['change_type']}"
        summary["by_role_and_change_type"][role_key] = summary["by_role_and_change_type"].get(role_key, 0) + 1
        summary["by_lifecycle_code_and_change_type"][lifecycle_key] = (
            summary["by_lifecycle_code_and_change_type"].get(lifecycle_key, 0) + 1
        )
    args.out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
