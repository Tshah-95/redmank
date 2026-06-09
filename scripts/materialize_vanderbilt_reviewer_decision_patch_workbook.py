#!/usr/bin/env python3
"""Materialize public-safe Vanderbilt reviewer patch workbook rows."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import apply_vanderbilt_reviewer_decision_patch as patch_helper


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SCAFFOLD_CSV = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.csv"
SCAFFOLD_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json"
OPERATOR_CSV = ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.csv"
OPERATOR_SUMMARY = ARTIFACTS / "vanderbilt_public_reviewer_operator_packet_summary.json"
PATCH_TEMPLATE_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_template_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_summary.json"
OUT_MD = RESEARCH / "vanderbilt-reviewer-decision-patch-workbook-2026-06-09.md"

EXPECTED_SCAFFOLD_ROWSET = "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"
EXPECTED_OPERATOR_PACKET_ROWSET = "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"
EXPECTED_PATCH_TEMPLATE_ROWSET = "5532d007555997f54d25884baba2f4e594d4ff1fa286301bfa6f87fc64caaa8d"
EXPECTED_WORKBOOK_ROWS = 159

MUTATION_POLICY = (
    "Non-mutating Vanderbilt reviewer decision patch workbook. It joins operator-packet context, current decision "
    "fingerprints, allowed actions, required confirmation fields, and blank patch columns so a reviewer can fill a "
    "bounded workbook and extract helper-compatible patch rows. It does not include reviewer notes, publish raw "
    "candidate names or URLs, approve people, ingest people, close denominators, verify Vanderbilt as a school, "
    "rewrite URLs, accept enrichment facts, or collapse identities."
)

CONTEXT_FIELDS = [
    "workbook_row_key",
    "operator_packet_key",
    "operator_execution_order",
    "source_batch_packet_key",
    "review_queue_lane",
    "program_key",
    "program_name",
    "decision_scaffold_key",
    "manual_decision_row_key",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "decision_fingerprint",
    "workbook_row_status",
    "helper_patch_output_columns_json",
    "source_scaffold_rowset_sha256",
    "source_operator_packet_rowset_sha256",
    "source_patch_template_rowset_sha256",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]
FIELDS = CONTEXT_FIELDS[:14] + list(patch_helper.PATCH_FIELDS[1:]) + CONTEXT_FIELDS[14:]
ROWSET_FIELDS = [
    "operator_packet_key",
    "operator_execution_order",
    "source_batch_packet_key",
    "review_queue_lane",
    "program_key",
    "program_name",
    "decision_scaffold_key",
    "manual_decision_row_key",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "decision_fingerprint",
    "workbook_row_status",
    "helper_patch_output_columns_json",
    "source_scaffold_rowset_sha256",
    "source_operator_packet_rowset_sha256",
    "source_patch_template_rowset_sha256",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
]

URL_RE = re.compile(r"https?://", re.I)

csv.field_size_limit(sys.maxsize)


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("workbook_row_key", "")))
    ]
    return sha256_text(dumps(material))


def load_operator_index() -> dict[str, dict[str, str]]:
    by_manual_key: dict[str, dict[str, str]] = {}
    for operator in read_csv_rows(OPERATOR_CSV):
        keys = json.loads(operator.get("manual_decision_row_keys_json", "[]"))
        if not isinstance(keys, list):
            raise SystemExit("Operator packet manual_decision_row_keys_json must be a list.")
        for manual_key in keys:
            key = str(manual_key)
            if key in by_manual_key:
                raise SystemExit("Manual decision row appears in multiple operator packets: " + key)
            by_manual_key[key] = operator
    return by_manual_key


def verify_no_public_leaks(rows: list[dict[str, object]]) -> None:
    text = dumps(rows)
    if URL_RE.search(text):
        raise SystemExit("Workbook rows contain URL-like text.")
    if "reviewer_note" in text:
        raise SystemExit("Workbook rows must not contain reviewer_note text.")


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Reviewer Decision Patch Workbook",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Reviewer Decision Patch Workbook",
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
        "## Workbook Rows",
        "",
        "| order | program | lane | manual_decision_row_key | action |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {operator_execution_order} | {program_name} | {review_queue_lane} | {manual_decision_row_key} | {reviewer_action} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    scaffold_summary = read_json(SCAFFOLD_SUMMARY)
    operator_summary = read_json(OPERATOR_SUMMARY)
    patch_template_summary = read_json(PATCH_TEMPLATE_SUMMARY)
    if not all(isinstance(item, dict) for item in [scaffold_summary, operator_summary, patch_template_summary]):
        raise SystemExit("Expected Vanderbilt workbook source summaries to be JSON objects.")
    source_checks = {
        "scaffold_rowset": scaffold_summary.get("rowset_sha256") == EXPECTED_SCAFFOLD_ROWSET,
        "operator_rowset": operator_summary.get("rowset_sha256") == EXPECTED_OPERATOR_PACKET_ROWSET,
        "patch_template_rowset": patch_template_summary.get("rowset_sha256") == EXPECTED_PATCH_TEMPLATE_ROWSET,
        "scaffold_rows": scaffold_summary.get("decision_scaffold_rows") == EXPECTED_WORKBOOK_ROWS,
        "operator_decision_rows": operator_summary.get("decision_row_count") == EXPECTED_WORKBOOK_ROWS,
        "patch_template_rows": patch_template_summary.get("template_rows") == EXPECTED_WORKBOOK_ROWS,
        "mutation_false": scaffold_summary.get("mutation_allowed") is False
        and operator_summary.get("mutation_allowed") is False
        and patch_template_summary.get("mutation_allowed") is False,
    }
    if not all(source_checks.values()):
        raise SystemExit("Unexpected Vanderbilt patch-workbook source boundary: " + dumps(source_checks))

    operator_by_manual_key = load_operator_index()
    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    by_lane: Counter[str] = Counter()
    by_operator: Counter[str] = Counter()
    for scaffold in sorted(
        read_csv_rows(SCAFFOLD_CSV),
        key=lambda item: (
            int(operator_by_manual_key.get(item.get("manual_decision_row_key", ""), {}).get("execution_order", 0)),
            item.get("program_key", ""),
            item.get("manual_decision_row_key", ""),
        ),
    ):
        manual_key = scaffold.get("manual_decision_row_key", "")
        operator = operator_by_manual_key.get(manual_key)
        if not operator:
            raise SystemExit("Missing operator packet for manual decision row: " + manual_key)
        by_lane[scaffold.get("review_queue_lane", "")] += 1
        by_operator[operator.get("operator_packet_key", "")] += 1
        patch_blanks = {field: "" for field in patch_helper.PATCH_FIELDS[1:]}
        row = {
            "workbook_row_key": stable_key("vanderbilt_reviewer_patch_workbook_row", manual_key, EXPECTED_PATCH_TEMPLATE_ROWSET),
            "operator_packet_key": operator.get("operator_packet_key", ""),
            "operator_execution_order": operator.get("execution_order", ""),
            "source_batch_packet_key": operator.get("source_batch_packet_key", ""),
            "review_queue_lane": scaffold.get("review_queue_lane", ""),
            "program_key": scaffold.get("program_key", ""),
            "program_name": scaffold.get("program_name", ""),
            "decision_scaffold_key": scaffold.get("decision_scaffold_key", ""),
            "manual_decision_row_key": manual_key,
            "candidate_fingerprint_sha256": scaffold.get("candidate_fingerprint_sha256", ""),
            "candidate_source_kind": scaffold.get("candidate_source_kind", ""),
            "allowed_reviewer_actions": scaffold.get("allowed_reviewer_actions", ""),
            "required_confirmation_fields": scaffold.get("required_confirmation_fields", ""),
            "decision_fingerprint": scaffold.get("decision_fingerprint", ""),
            **patch_blanks,
            "workbook_row_status": "blank_pending_reviewer_input",
            "helper_patch_output_columns_json": dumps(patch_helper.PATCH_FIELDS),
            "source_scaffold_rowset_sha256": EXPECTED_SCAFFOLD_ROWSET,
            "source_operator_packet_rowset_sha256": EXPECTED_OPERATOR_PACKET_ROWSET,
            "source_patch_template_rowset_sha256": EXPECTED_PATCH_TEMPLATE_ROWSET,
            "accepted_person_rows": 0,
            "person_ingestion_allowed": "false",
            "denominator_closure_allowed": "false",
            "raw_candidate_names_committed": "false",
            "raw_person_urls_committed": "false",
            "evidence_json": dumps(
                {
                    "manual_decision_required": True,
                    "operator_packet_key": operator.get("operator_packet_key", ""),
                    "decision_fingerprint_present": bool(scaffold.get("decision_fingerprint", "")),
                    "raw_candidate_names_committed": False,
                    "raw_person_urls_committed": False,
                }
            ),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
        rows.append(row)

    blank_counts = {
        field: sum(1 for row in rows if not str(row.get(field, "")).strip())
        for field in patch_helper.PATCH_FIELDS[1:]
    }
    verify_no_public_leaks(rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_scaffold_summary": str(SCAFFOLD_SUMMARY.relative_to(ROOT)),
        "source_scaffold_rowset_sha256": EXPECTED_SCAFFOLD_ROWSET,
        "source_operator_packet_summary": str(OPERATOR_SUMMARY.relative_to(ROOT)),
        "source_operator_packet_rowset_sha256": EXPECTED_OPERATOR_PACKET_ROWSET,
        "source_patch_template_summary": str(PATCH_TEMPLATE_SUMMARY.relative_to(ROOT)),
        "source_patch_template_rowset_sha256": EXPECTED_PATCH_TEMPLATE_ROWSET,
        "workbook_rows": len(rows),
        "operator_packet_rows_represented": len(by_operator),
        "decision_fingerprint_present_rows": sum(1 for row in rows if row.get("decision_fingerprint")),
        "blank_action_rows": blank_counts["reviewer_action"],
        "blank_confirmation_rows": {field: blank_counts[field] for field in patch_helper.PATCH_FIELDS if field.startswith("confirm_")},
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "helper_patch_output_columns": patch_helper.PATCH_FIELDS,
        "helper_patch_extraction_required": True,
        "workbook_intentionally_invalid_as_direct_patch": True,
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

    if (
        len(rows) != EXPECTED_WORKBOOK_ROWS
        or summary["operator_packet_rows_represented"] != 20
        or summary["decision_fingerprint_present_rows"] != EXPECTED_WORKBOOK_ROWS
        or any(value != EXPECTED_WORKBOOK_ROWS for value in blank_counts.values())
    ):
        raise SystemExit("Vanderbilt patch workbook failed completeness or blank-field checks.")

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["workbook_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
