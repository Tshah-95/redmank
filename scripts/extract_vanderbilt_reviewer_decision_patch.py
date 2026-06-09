#!/usr/bin/env python3
"""Extract a strict Vanderbilt reviewer patch from a filled workbook."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

import apply_vanderbilt_reviewer_decision_patch as patch_helper
import materialize_vanderbilt_reviewer_decision_patch_workbook as workbook_materializer


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"

DEFAULT_WORKBOOK = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.csv"
DEFAULT_OUTPUT = Path("/tmp/vanderbilt_reviewer_decision_patch_extracted.csv")
SCAFFOLD_JSON = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.json"
DECISIONS_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.csv"

URL_RE = re.compile(r"https?://", re.I)


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


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def resolved(value: str) -> Path:
    return Path(value).expanduser().resolve()


def is_blank_patch_row(row: dict[str, str]) -> bool:
    return not any(str(row.get(field, "")).strip() for field in patch_helper.PATCH_FIELDS[1:])


def contains_partial_blank_action(row: dict[str, str]) -> bool:
    return not str(row.get("reviewer_action", "")).strip() and any(
        str(row.get(field, "")).strip() for field in patch_helper.PATCH_FIELDS[2:]
    )


def validate_workbook_header(fields: list[str]) -> None:
    expected = set(workbook_materializer.FIELDS)
    missing = [field for field in workbook_materializer.FIELDS if field not in fields]
    extras = [field for field in fields if field not in expected]
    if missing:
        raise SystemExit("Workbook is missing required columns: " + ", ".join(missing))
    if extras:
        raise SystemExit("Workbook contains unsupported columns: " + ", ".join(extras))
    if any("reviewer_note" in field for field in fields):
        raise SystemExit("Workbook must not contain reviewer_note columns.")


def validate_context_rows(rows: list[dict[str, str]], scaffold_by_manual_key: dict[str, dict[str, object]]) -> None:
    seen: set[str] = set()
    for row in rows:
        if URL_RE.search(json.dumps(row, ensure_ascii=True, sort_keys=True)):
            raise SystemExit("Workbook row contains URL-like text.")
        manual_key = row.get("manual_decision_row_key", "").strip()
        if not manual_key:
            raise SystemExit("Workbook row missing manual_decision_row_key.")
        if manual_key in seen:
            raise SystemExit("Workbook contains duplicate manual_decision_row_key: " + manual_key)
        seen.add(manual_key)
        scaffold = scaffold_by_manual_key.get(manual_key)
        if not scaffold:
            raise SystemExit("Workbook references unknown manual_decision_row_key: " + manual_key)
        expected_fingerprint = str(scaffold.get("decision_fingerprint", ""))
        if row.get("decision_fingerprint", "").strip() != expected_fingerprint:
            raise SystemExit("Workbook decision_fingerprint is stale for: " + manual_key)
        if row.get("confirm_decision_fingerprint", "").strip() and row.get(
            "confirm_decision_fingerprint", ""
        ).strip() != expected_fingerprint:
            raise SystemExit("Workbook confirm_decision_fingerprint does not match current fingerprint for: " + manual_key)
        if contains_partial_blank_action(row):
            raise SystemExit("Workbook row has confirmations without reviewer_action: " + manual_key)


def extract_patch_rows(rows: list[dict[str, str]], include_blank: bool) -> list[dict[str, str]]:
    patch_rows: list[dict[str, str]] = []
    for row in rows:
        if is_blank_patch_row(row) and not include_blank:
            continue
        patch_rows.append({field: row.get(field, "").strip() for field in patch_helper.PATCH_FIELDS})
    return patch_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", default=str(DEFAULT_WORKBOOK), help="Filled Vanderbilt reviewer patch workbook CSV.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Strict helper-compatible patch CSV to write.")
    parser.add_argument("--scaffold", default=str(SCAFFOLD_JSON), help="Decision scaffold JSON context.")
    parser.add_argument("--decisions", default=str(DECISIONS_CSV), help="Reviewer decision template CSV context.")
    parser.add_argument("--include-blank", action="store_true", help="Extract blank rows too; mainly useful for shape tests.")
    parser.add_argument("--allow-empty", action="store_true", help="Allow writing an empty patch CSV.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook_path = resolved(args.workbook)
    output_path = resolved(args.output)
    scaffold_path = resolved(args.scaffold)
    decisions_path = resolved(args.decisions)
    if not workbook_path.exists():
        raise SystemExit("Workbook file does not exist: " + str(workbook_path))
    if not scaffold_path.exists():
        raise SystemExit("Scaffold file does not exist: " + str(scaffold_path))
    if not decisions_path.exists():
        raise SystemExit("Decisions file does not exist: " + str(decisions_path))

    fields, workbook_rows = read_csv_rows(workbook_path)
    validate_workbook_header(fields)
    scaffold_rows = read_json(scaffold_path)
    decision_fields, decision_rows = read_csv_rows(decisions_path)
    if not isinstance(scaffold_rows, list):
        raise SystemExit("Expected Vanderbilt decision scaffold JSON array.")
    scaffold_by_manual_key = {str(row.get("manual_decision_row_key")): row for row in scaffold_rows}
    decisions_by_manual_key = {row.get("manual_decision_row_key", ""): row for row in decision_rows}
    validate_context_rows(workbook_rows, scaffold_by_manual_key)

    patch_rows = extract_patch_rows(workbook_rows, args.include_blank)
    if not patch_rows and not args.allow_empty:
        raise SystemExit("No filled workbook rows to extract.")
    if patch_rows:
        patch_helper.validate_patch_rows(patch_rows, scaffold_by_manual_key, decisions_by_manual_key)
    write_csv(output_path, patch_helper.PATCH_FIELDS, patch_rows)

    by_lane = Counter(scaffold_by_manual_key[row["manual_decision_row_key"]].get("review_queue_lane", "") for row in patch_rows)
    summary = {
        "workbook": str(workbook_path),
        "output": str(output_path),
        "workbook_rows": len(workbook_rows),
        "extracted_patch_rows": len(patch_rows),
        "include_blank": bool(args.include_blank),
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "accepted_person_rows": 0,
        "output_columns": patch_helper.PATCH_FIELDS,
        "decision_template_columns": decision_fields,
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
