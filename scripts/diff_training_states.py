#!/usr/bin/env python3
"""Diff two exported training-state snapshots."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path


DEFAULT_CONTRACTS = Path("artifacts/data/training_temporal_contracts.csv")
DEFAULT_SNAPSHOT_SUMMARY = Path("artifacts/data/training_state_snapshot_summary.json")

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


def contract_lookup_key(row: dict) -> tuple[str, str, str, str]:
    return (
        row.get("person_key") or "",
        row.get("program_name") or "",
        row.get("role") or "",
        row.get("trainee_category") or "",
    )


def read_contracts(path: Path | None) -> dict[tuple[str, str, str, str], dict]:
    if not path or not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return {contract_lookup_key(row): row for row in rows}


def previous_snapshot_csv(summary_path: Path) -> Path:
    if not summary_path.exists():
        raise FileNotFoundError(f"Snapshot summary not found: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    previous_snapshot_id = summary.get("previous_snapshot_id")
    if not previous_snapshot_id:
        raise ValueError(f"Snapshot summary has no previous_snapshot_id: {summary_path}")
    return summary_path.parent / "training_state_snapshots" / f"{previous_snapshot_id}.csv"


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def fresh_observation(old: dict | None, new: dict | None) -> bool:
    if not old or not new:
        return bool(new)
    return any(
        (new.get(field) or "") != (old.get(field) or "")
        for field in ["observed_at", "as_of_date", "source_key", "state_key"]
    )


def contract_policy_fields(contract: dict | None) -> dict:
    if not contract:
        return {
            "temporal_contract_key": "",
            "temporal_policy_lane": "",
            "temporal_validity_status": "",
            "next_refresh_contract": "",
            "diff_readiness_status": "",
            "evidence_required": "",
            "review_triggers": "[]",
        }
    return {
        "temporal_contract_key": contract.get("contract_key", ""),
        "temporal_policy_lane": contract.get("policy_lane", ""),
        "temporal_validity_status": contract.get("temporal_validity_status", ""),
        "next_refresh_contract": contract.get("next_refresh_contract", ""),
        "diff_readiness_status": contract.get("diff_readiness_status", ""),
        "evidence_required": contract.get("evidence_required_to_retain", ""),
        "review_triggers": contract.get("review_trigger_json", "[]"),
    }


def contract_due(old: dict | None, contract: dict | None, compare_date: date) -> bool:
    if not old or not contract:
        return False
    lane = contract.get("policy_lane") or ""
    expected_next_date = parse_date(old.get("expected_next_date"))
    stale_after = parse_date(old.get("stale_after_date"))
    if lane == "deterministic_expected_advancement":
        return bool(expected_next_date and expected_next_date <= compare_date)
    if lane in {"deterministic_expected_completion", "source_refresh_required", "manual_review_required"}:
        return bool(stale_after and stale_after <= compare_date)
    return False


def classify_change(old: dict | None, new: dict | None, compare_date: date, contract: dict | None = None) -> dict:
    contract_fields = contract_policy_fields(contract)
    if old and not new:
        if contract and contract_due(old, contract, compare_date):
            change_type = contract.get("if_missing_change_type") or ""
            is_expected_completion = change_type == "removed_expected_completion_candidate"
            return {
                **contract_fields,
                "change_type": "removed_expected_completion" if is_expected_completion else change_type or "removed_review",
                "old_stage": old.get("normalized_stage"),
                "new_stage": "",
                "old_stale_after_date": old.get("stale_after_date", ""),
                "expected_by_state_machine": "1" if is_expected_completion else "0",
                "transition_assurance": "expected" if is_expected_completion else "review",
                "notes": (
                    contract.get("evidence_required_to_complete")
                    if is_expected_completion
                    else f"Missing row is contract-bound review: {contract.get('stale_information_policy') or ''}"
                ),
            }
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
            "expected_by_state_machine": "1" if expected else "0",
            "transition_assurance": "expected" if expected else "review",
            **contract_fields,
            "notes": notes,
        }
    if new and not old:
        return {
            "change_type": "added",
            "old_stage": "",
            "new_stage": new.get("normalized_stage"),
            "old_stale_after_date": "",
            "expected_by_state_machine": "0",
            "transition_assurance": "new_observation",
            **contract_policy_fields(contract),
            "notes": "New person/program state observation.",
        }
    assert old and new
    if old.get("normalized_stage") != new.get("normalized_stage"):
        expected_next = old.get("expected_next_stage")
        expected = bool(expected_next and expected_next == new.get("normalized_stage"))
        if contract:
            contract_change = contract.get("if_expected_next_stage_change_type") or ""
            expected = (
                expected
                and contract_change == "advanced_expected_with_fresh_observation"
                and fresh_observation(old, new)
                and contract_due(old, contract, compare_date)
            )
        return {
            "change_type": "advanced_expected" if expected else "stage_changed_review",
            "old_stage": old.get("normalized_stage"),
            "new_stage": new.get("normalized_stage"),
            "old_stale_after_date": old.get("stale_after_date", ""),
            "expected_by_state_machine": "1" if expected else "0",
            "transition_assurance": "expected" if expected else "review",
            **contract_fields,
            "notes": "New stage matches prior expected_next_stage." if expected else "Stage changed outside the prior expected transition.",
        }
    if contract and contract_due(old, contract, compare_date):
        same_stage_contract = contract.get("if_same_stage_change_type") or ""
        if same_stage_contract == "unchanged_expected":
            assurance = "same_state"
            expected = "1"
            notes = "Same stage is allowed by the temporal contract."
        elif same_stage_contract == "unchanged_requires_fresh_source" and fresh_observation(old, new):
            assurance = "same_stage_fresh_source"
            expected = "1"
            notes = contract.get("evidence_required_to_retain") or "Same stage retained because the later snapshot reobserved it."
        else:
            assurance = "review"
            expected = "0"
            notes = f"Same stage is contract-bound review: {same_stage_contract or 'no same-stage contract'}."
        return {
            "change_type": same_stage_contract or "unchanged",
            "old_stage": old.get("normalized_stage"),
            "new_stage": new.get("normalized_stage"),
            "old_stale_after_date": old.get("stale_after_date", ""),
            "expected_by_state_machine": expected,
            "transition_assurance": assurance,
            **contract_fields,
            "notes": notes,
        }
    return {
        "change_type": "unchanged",
        "old_stage": old.get("normalized_stage"),
        "new_stage": new.get("normalized_stage"),
        "old_stale_after_date": old.get("stale_after_date", ""),
        "expected_by_state_machine": "1",
        "transition_assurance": "same_state",
        **contract_fields,
        "notes": "Same normalized state.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--old", type=Path)
    parser.add_argument("--new", required=True, type=Path)
    parser.add_argument("--out-csv", type=Path, default=Path("artifacts/data/training_state_diff.csv"))
    parser.add_argument("--out-json", type=Path, default=Path("artifacts/data/training_state_diff_summary.json"))
    parser.add_argument("--out-rollup-csv", type=Path, default=Path("artifacts/data/training_state_diff_rollups.csv"))
    parser.add_argument("--contracts", type=Path, default=DEFAULT_CONTRACTS)
    parser.add_argument("--compare-date", default=date.today().isoformat())
    args = parser.parse_args()

    old_path = args.old or previous_snapshot_csv(DEFAULT_SNAPSHOT_SUMMARY)
    old_rows, old_input_rows, old_duplicate_keys = read_rows(old_path)
    new_rows, new_input_rows, new_duplicate_keys = read_rows(args.new)
    contracts = read_contracts(args.contracts)
    compare_date = date.fromisoformat(args.compare_date)
    all_keys = sorted(set(old_rows) | set(new_rows))
    diff_rows = []
    for person_key, program_name in all_keys:
        old = old_rows.get((person_key, program_name))
        new = new_rows.get((person_key, program_name))
        contract_source = old or new or {}
        contract = contracts.get(contract_lookup_key(contract_source))
        change = classify_change(old, new, compare_date, contract)
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
            "expected_by_state_machine",
            "transition_assurance",
            "temporal_contract_key",
            "temporal_policy_lane",
            "temporal_validity_status",
            "next_refresh_contract",
            "diff_readiness_status",
            "evidence_required",
            "review_triggers",
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
            row.get("temporal_policy_lane", ""),
            row["change_type"],
        )
        rollups[key] = rollups.get(key, 0) + 1
    with args.out_rollup_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["program_name", "role", "lifecycle_code", "temporal_policy_lane", "change_type", "count"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for key, count in sorted(rollups.items()):
            program_name, role, lifecycle_code, temporal_policy_lane, change_type = key
            writer.writerow(
                {
                    "program_name": program_name,
                    "role": role,
                    "lifecycle_code": lifecycle_code,
                    "temporal_policy_lane": temporal_policy_lane,
                    "change_type": change_type,
                    "count": count,
                }
            )

    summary = {
        "old": str(old_path),
        "new": str(args.new),
        "compare_date": compare_date.isoformat(),
        "rows": len(diff_rows),
        "old_input_rows": old_input_rows,
        "new_input_rows": new_input_rows,
        "old_canonical_keys": len(old_rows),
        "new_canonical_keys": len(new_rows),
        "old_duplicate_keys_collapsed": old_duplicate_keys,
        "new_duplicate_keys_collapsed": new_duplicate_keys,
        "contracts": str(args.contracts) if args.contracts else "",
        "contract_rows_loaded": len(contracts),
        "diff_rows_with_contract": sum(1 for row in diff_rows if row.get("temporal_contract_key")),
        "by_change_type": {},
        "rollup_csv": str(args.out_rollup_csv),
        "by_role_and_change_type": {},
        "by_lifecycle_code_and_change_type": {},
        "by_temporal_policy_lane_and_change_type": {},
    }
    for row in diff_rows:
        summary["by_change_type"][row["change_type"]] = summary["by_change_type"].get(row["change_type"], 0) + 1
        role_key = f"{row.get('role', '')}:{row['change_type']}"
        lifecycle_key = f"{row.get('new_lifecycle_code') or row.get('old_lifecycle_code', '')}:{row['change_type']}"
        policy_key = f"{row.get('temporal_policy_lane', '')}:{row['change_type']}"
        summary["by_role_and_change_type"][role_key] = summary["by_role_and_change_type"].get(role_key, 0) + 1
        summary["by_lifecycle_code_and_change_type"][lifecycle_key] = (
            summary["by_lifecycle_code_and_change_type"].get(lifecycle_key, 0) + 1
        )
        summary["by_temporal_policy_lane_and_change_type"][policy_key] = (
            summary["by_temporal_policy_lane_and_change_type"].get(policy_key, 0) + 1
        )
    args.out_json.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
