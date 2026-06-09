#!/usr/bin/env python3
"""Validate or apply a public-safe Vanderbilt reviewer decision patch."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import materialize_vanderbilt_candidate_reviewer_decision_audit as audit


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"

SCAFFOLD_JSON = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.json"
DECISIONS_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.csv"
DECISIONS_JSON = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.json"

PATCH_FIELDS = [
    "manual_decision_row_key",
    "reviewer_action",
    "confirm_decision_fingerprint",
    "confirm_no_person_ingestion",
    "confirm_no_denominator_closure",
    "confirm_no_raw_name_added",
    "confirm_no_url_rewrite",
    "confirm_candidate_fingerprint_only",
    "confirm_scope_metadata_only",
    "confirm_recourse_only",
]

BOOLEAN_CONFIRMATION_FIELDS = [
    "confirm_no_person_ingestion",
    "confirm_no_denominator_closure",
    "confirm_no_raw_name_added",
    "confirm_no_url_rewrite",
    "confirm_candidate_fingerprint_only",
    "confirm_scope_metadata_only",
    "confirm_recourse_only",
]


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def write_json(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def patch_path(value: str) -> Path:
    return Path(value).expanduser().resolve()


def validate_patch_header(fields: list[str]) -> None:
    missing = [field for field in PATCH_FIELDS if field not in fields]
    extras = [field for field in fields if field not in PATCH_FIELDS]
    if missing:
        raise SystemExit("Patch is missing required columns: " + ", ".join(missing))
    if extras:
        raise SystemExit("Patch contains unsupported columns: " + ", ".join(extras))


def merged_decision(decision: dict[str, str], patch: dict[str, str]) -> dict[str, str]:
    merged = dict(decision)
    merged["reviewer_action"] = patch.get("reviewer_action", "").strip()
    merged["reviewer_note"] = ""
    merged["confirm_decision_fingerprint"] = patch.get("confirm_decision_fingerprint", "").strip()
    for field in BOOLEAN_CONFIRMATION_FIELDS:
        if field in merged:
            merged[field] = patch.get(field, "").strip().lower()
    return merged


def validate_patch_rows(
    patch_rows: list[dict[str, str]],
    scaffold_by_manual_key: dict[str, dict[str, object]],
    decisions_by_manual_key: dict[str, dict[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    seen: set[str] = set()
    merged_rows: list[dict[str, str]] = []
    audit_rows: list[dict[str, object]] = []
    for row in patch_rows:
        manual_key = row.get("manual_decision_row_key", "").strip()
        if not manual_key:
            raise SystemExit("Patch row is missing manual_decision_row_key.")
        if manual_key in seen:
            raise SystemExit("Patch contains duplicate manual_decision_row_key: " + manual_key)
        seen.add(manual_key)
        scaffold_row = scaffold_by_manual_key.get(manual_key)
        decision_row = decisions_by_manual_key.get(manual_key)
        if not scaffold_row or not decision_row:
            raise SystemExit("Patch references unknown manual_decision_row_key: " + manual_key)
        required_fields = set(audit.required_confirmation_fields(scaffold_row))
        irrelevant_filled = [
            field
            for field in BOOLEAN_CONFIRMATION_FIELDS
            if field not in required_fields and str(row.get(field, "")).strip()
        ]
        if irrelevant_filled:
            raise SystemExit(
                "Patch sets confirmation fields outside this row's lane for "
                + manual_key
                + ": "
                + ", ".join(irrelevant_filled)
            )
        if any(str(row.get(field, "")).strip() for field in BOOLEAN_CONFIRMATION_FIELDS if field not in decision_row):
            raise SystemExit("Patch sets confirmation fields absent from the decision template for: " + manual_key)
        merged = merged_decision(decision_row, row)
        audited = audit.audit_decision(scaffold_row, merged, "patch_validation")
        if audited.get("audit_status") != "valid_non_mutating":
            raise SystemExit(
                "Patch row is not a valid non-mutating decision for "
                + manual_key
                + ": "
                + str(audited.get("audit_blocker") or audited.get("decision_state"))
            )
        merged_rows.append(merged)
        audit_rows.append(audited)
    return merged_rows, audit_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch", required=True, help="CSV patch with non-mutating reviewer decisions.")
    parser.add_argument("--scaffold", default=str(SCAFFOLD_JSON), help="Decision scaffold JSON context.")
    parser.add_argument("--decisions", default=str(DECISIONS_CSV), help="Reviewer decision template CSV context.")
    parser.add_argument("--apply", action="store_true", help="Write the validated decisions to the output files.")
    parser.add_argument("--output", default=str(DECISIONS_CSV), help="Decision CSV output path. Defaults to the committed template.")
    parser.add_argument("--json-output", default=str(DECISIONS_JSON), help="Decision JSON output path. Defaults to the committed template JSON.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    patch = patch_path(args.patch)
    scaffold_path = patch_path(args.scaffold)
    decisions_path = patch_path(args.decisions)
    output = patch_path(args.output)
    json_output = patch_path(args.json_output)
    if not patch.exists():
        raise SystemExit("Patch file does not exist: " + str(patch))
    if not scaffold_path.exists():
        raise SystemExit("Scaffold file does not exist: " + str(scaffold_path))
    if not decisions_path.exists():
        raise SystemExit("Decisions file does not exist: " + str(decisions_path))

    scaffold_rows = read_json(scaffold_path)
    decision_fields, decision_rows = read_csv_rows(decisions_path)
    patch_fields, patch_rows = read_csv_rows(patch)
    if not isinstance(scaffold_rows, list):
        raise SystemExit("Expected Vanderbilt decision scaffold JSON array.")
    validate_patch_header(patch_fields)

    scaffold_by_manual_key = {str(row.get("manual_decision_row_key")): row for row in scaffold_rows}
    decisions_by_manual_key = {row.get("manual_decision_row_key", ""): row for row in decision_rows}
    merged_rows, audit_rows = validate_patch_rows(patch_rows, scaffold_by_manual_key, decisions_by_manual_key)
    merged_by_key = {row["manual_decision_row_key"]: row for row in merged_rows}
    next_decisions = [merged_by_key.get(row.get("manual_decision_row_key", ""), row) for row in decision_rows]

    by_lane = Counter(row.get("review_queue_lane", "") for row in merged_rows)
    summary = {
        "patch": str(patch),
        "apply": bool(args.apply),
        "patch_rows": len(patch_rows),
        "valid_non_mutating_rows": len(audit_rows),
        "output": str(output),
        "json_output": str(json_output),
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "accepted_person_rows": 0,
    }
    if args.apply:
        write_csv(output, decision_fields, next_decisions)
        write_json(json_output, next_decisions)
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
