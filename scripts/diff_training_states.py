#!/usr/bin/env python3
"""Diff two exported training-state snapshots."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path


def read_rows(path: Path) -> tuple[dict[tuple[str, str], dict], int, int]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    result = {}
    duplicate_keys = 0
    for row in rows:
        key = (row["person_key"], row.get("program_name") or "")
        if key in result:
            duplicate_keys += 1
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
        return {
            "change_type": "removed_expected_stale" if expected else "removed_unexpected",
            "old_stage": old.get("normalized_stage"),
            "new_stage": "",
            "old_stale_after_date": old.get("stale_after_date", ""),
            "notes": "Old state had passed stale-after date." if expected else "Old state disappeared before expected stale-after date.",
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
            "old_stale_after_date",
            "new_as_of_date",
            "notes",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(diff_rows)

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
    }
    for row in diff_rows:
        summary["by_change_type"][row["change_type"]] = summary["by_change_type"].get(row["change_type"], 0) + 1
    args.out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
