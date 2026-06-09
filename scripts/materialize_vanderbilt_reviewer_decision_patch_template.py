#!/usr/bin/env python3
"""Materialize a helper-compatible blank Vanderbilt reviewer patch template."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import apply_vanderbilt_reviewer_decision_patch as patch_helper


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SCAFFOLD_JSON = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.json"
SCAFFOLD_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json"
OPERATOR_SUMMARY = ARTIFACTS / "vanderbilt_public_reviewer_operator_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_reviewer_decision_patch_template.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_reviewer_decision_patch_template.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_template_summary.json"
OUT_MD = RESEARCH / "vanderbilt-reviewer-decision-patch-template-2026-06-09.md"

EXPECTED_SCAFFOLD_ROWSET = "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"
EXPECTED_OPERATOR_PACKET_ROWSET = "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"
EXPECTED_TEMPLATE_ROWS = 159

MUTATION_POLICY = (
    "Non-mutating Vanderbilt reviewer decision patch template. It materializes only helper-compatible blank patch "
    "rows keyed by manual_decision_row_key. It does not fill reviewer decisions, include reviewer notes, publish raw "
    "candidate names or URLs, approve people, ingest people, close denominators, verify Vanderbilt as a school, "
    "rewrite URLs, accept enrichment facts, or collapse identities."
)

FIELDS = list(patch_helper.PATCH_FIELDS)
ROWSET_FIELDS = list(patch_helper.PATCH_FIELDS)

csv.field_size_limit(sys.maxsize)


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def rowset_sha256(rows: list[dict[str, str]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: item["manual_decision_row_key"])
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, str]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Reviewer Decision Patch Template",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Reviewer Decision Patch Template",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Template Rows",
        "",
        "| row | manual_decision_row_key | reviewer_action |",
        "| ---: | --- | --- |",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            "| {index} | {manual_decision_row_key} | {reviewer_action} |".format(
                index=index,
                manual_decision_row_key=row["manual_decision_row_key"],
                reviewer_action=row["reviewer_action"],
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    scaffold_summary = read_json(SCAFFOLD_SUMMARY)
    operator_summary = read_json(OPERATOR_SUMMARY)
    scaffold_rows = read_json(SCAFFOLD_JSON)
    if not isinstance(scaffold_summary, dict) or not isinstance(operator_summary, dict) or not isinstance(scaffold_rows, list):
        raise SystemExit("Expected Vanderbilt scaffold and operator summary artifacts.")

    source_checks = {
        "scaffold_rowset": scaffold_summary.get("rowset_sha256") == EXPECTED_SCAFFOLD_ROWSET,
        "scaffold_rows": scaffold_summary.get("decision_scaffold_rows") == EXPECTED_TEMPLATE_ROWS,
        "operator_rowset": operator_summary.get("rowset_sha256") == EXPECTED_OPERATOR_PACKET_ROWSET,
        "operator_rows": operator_summary.get("decision_row_count") == EXPECTED_TEMPLATE_ROWS,
        "scaffold_non_mutating": scaffold_summary.get("mutation_allowed") is False,
        "operator_non_mutating": operator_summary.get("mutation_allowed") is False,
    }
    if not all(source_checks.values()):
        raise SystemExit("Unexpected Vanderbilt patch-template source boundary: " + dumps(source_checks))

    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    source_lanes: Counter[str] = Counter()
    for scaffold in sorted(
        scaffold_rows,
        key=lambda item: (
            str(item.get("review_queue_lane", "")),
            str(item.get("program_key", "")),
            str(item.get("manual_decision_row_key", "")),
        ),
    ):
        manual_key = str(scaffold.get("manual_decision_row_key", "")).strip()
        if not manual_key:
            raise SystemExit("Scaffold row is missing manual_decision_row_key.")
        if manual_key in seen:
            raise SystemExit("Duplicate manual_decision_row_key in scaffold: " + manual_key)
        seen.add(manual_key)
        source_lanes[str(scaffold.get("review_queue_lane", ""))] += 1
        rows.append({field: "" for field in FIELDS} | {"manual_decision_row_key": manual_key})

    blank_fields = [field for field in FIELDS if field != "manual_decision_row_key"]
    blank_counts = {field: sum(1 for row in rows if not row.get(field, "").strip()) for field in blank_fields}
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_scaffold_summary": str(SCAFFOLD_SUMMARY.relative_to(ROOT)),
        "source_scaffold_rowset_sha256": EXPECTED_SCAFFOLD_ROWSET,
        "source_operator_packet_summary": str(OPERATOR_SUMMARY.relative_to(ROOT)),
        "source_operator_packet_rowset_sha256": EXPECTED_OPERATOR_PACKET_ROWSET,
        "template_rows": len(rows),
        "helper_patch_fields": FIELDS,
        "blank_action_rows": blank_counts["reviewer_action"],
        "blank_confirmation_rows": {field: blank_counts[field] for field in blank_fields if field.startswith("confirm_")},
        "by_source_review_queue_lane": dict(sorted(source_lanes.items())),
        "helper_accepts_template_shape": True,
        "template_intentionally_invalid_until_filled": True,
        "valid_non_mutating_rows": 0,
        "reviewer_note_column_committed": False,
        "raw_candidate_names_committed": False,
        "raw_person_urls_committed": False,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    if len(rows) != EXPECTED_TEMPLATE_ROWS or any(value != EXPECTED_TEMPLATE_ROWS for value in blank_counts.values()):
        raise SystemExit("Patch template must contain only blank action/confirmation fields.")

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["template_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
