#!/usr/bin/env python3
"""Validate filled school gap-resolution review-template rows without mutating state."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DEFAULT_INPUT = ARTIFACTS / "school_gap_resolution_review_template.csv"
DEFAULT_SUMMARY = ARTIFACTS / "school_gap_resolution_review_template_validation_summary.json"

EXPECTED_TEMPLATE_ROWSET = "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782"
EXPECTED_TEMPLATE_ROWS = 113
EXPECTED_BATCH_ROWS = 21

ALLOWED_REVIEW_ACTIONS = {
    "candidate_official_source_for_later_probe",
    "source_discovery_query_only",
    "route_inspection_needed",
    "rendered_or_manual_review_needed",
    "scope_disposition_packet_needed",
    "no_public_roster_closure_packet_needed",
    "defer_needs_more_context",
}
CONFIRMATION_FIELDS = [
    "confirm_no_person_ingestion",
    "confirm_no_denominator_closure",
    "confirm_no_school_verification",
    "confirm_no_url_rewrite",
    "confirm_no_identity_collapse",
    "confirm_candidate_evidence_only",
]
MUST_BE_FALSE_FIELDS = [
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "private_artifact_paths_committed",
]
FILLABLE_FIELDS = [
    "proposed_non_mutating_review_action",
    "proposed_source_discovery_query",
    "proposed_candidate_official_url",
    "proposed_evidence_summary",
    "proposed_output_artifact",
    *CONFIRMATION_FIELDS,
]
TEMPLATE_FIELDS = [
    "review_template_key",
    "school_gap_resolution_batch_packet_key",
    "school_gap_resolution_batch_key",
    "execution_order",
    "batch_packet_order",
    "gap_key",
    "school_name",
    "program_key",
    "program_name",
    "program_type",
    "department_or_group",
    "next_operator_lane",
    "resolution_category",
    "packet_status",
    "support_status",
    "denominator_url",
    "best_evidence_url",
    "best_evidence_title",
    "best_evidence_status",
    "recommended_packet_action",
    "required_next_evidence",
    "target_artifact",
    "allowed_review_actions",
    "proposed_non_mutating_review_action",
    "proposed_source_discovery_query",
    "proposed_candidate_official_url",
    "proposed_evidence_summary",
    "proposed_output_artifact",
    "confirm_no_person_ingestion",
    "confirm_no_denominator_closure",
    "confirm_no_school_verification",
    "confirm_no_url_rewrite",
    "confirm_no_identity_collapse",
    "confirm_candidate_evidence_only",
    "template_row_status",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "private_artifact_paths_committed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]
ROWSET_FIELDS = [
    field
    for field in TEMPLATE_FIELDS
    if field not in {"review_template_key", "evidence_json", "mutation_policy", "generated_at"}
]
PRIVATE_PATH_MARKERS = [
    "artifacts/data/gbrain_",
    "artifacts/data/browser_page_dumps/",
    "artifacts/data/debug_",
    "artifacts/data/raw/",
    ".playwright-mcp/",
    "inbox/",
    "reports/",
]
PROHIBITED_TEXT_RE = re.compile(
    r"\b(accept(?:ed)?(?:_|\s+)?person|ingest(?:ion)?|close(?:d)?(?:_|\s+)?denominator|"
    r"school(?:_|\s+)?verified|rewrite(?:_|\s+)?url|identity(?:_|\s+)?collapse|"
    r"accepted(?:_|\s+)?enrichment|profile(?:_|\s+)?accepted|contact(?:_|\s+)?accepted)\b",
    re.I,
)
URL_RE = re.compile(r"^https://[^\s]+$", re.I)

csv.field_size_limit(sys.maxsize)


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_csv_rows(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def rowset_sha256(rows: list[dict[str, str]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("review_template_key", "")))
    ]
    return sha256_text(dumps(material))


def normalize_bool(value: str) -> str:
    return value.strip().lower()


def has_private_marker(row: dict[str, str]) -> list[str]:
    text = dumps(row)
    return [marker for marker in PRIVATE_PATH_MARKERS if marker in text]


def row_has_fill(row: dict[str, str]) -> bool:
    return any(row.get(field, "").strip() for field in FILLABLE_FIELDS)


def validate_row(row: dict[str, str], row_number: int) -> tuple[str, list[str]]:
    errors: list[str] = []
    private_markers = has_private_marker(row)
    if private_markers:
        errors.append("private_artifact_marker:" + ",".join(private_markers))
    if row.get("accepted_person_rows", "").strip() not in {"0", ""}:
        errors.append("accepted_person_rows_must_be_0")
    for field in MUST_BE_FALSE_FIELDS:
        if normalize_bool(row.get(field, "")) != "false":
            errors.append(field + "_must_be_false")
    for field in ["template_row_status", "evidence_json"]:
        if PROHIBITED_TEXT_RE.search(row.get(field, "")):
            errors.append(field + "_contains_mutation_acceptance_language")

    filled = row_has_fill(row)
    if not filled:
        return ("invalid" if errors else "pending", errors)

    action = row.get("proposed_non_mutating_review_action", "").strip()
    if action not in ALLOWED_REVIEW_ACTIONS:
        errors.append("proposed_non_mutating_review_action_not_allowed")
    for field in CONFIRMATION_FIELDS:
        if normalize_bool(row.get(field, "")) != "true":
            errors.append(field + "_must_be_true_for_filled_row")
    if action in {"candidate_official_source_for_later_probe", "route_inspection_needed"}:
        candidate_url = row.get("proposed_candidate_official_url", "").strip()
        if candidate_url and not URL_RE.match(candidate_url):
            errors.append("proposed_candidate_official_url_must_be_https")
    if row.get("proposed_output_artifact", "").strip():
        output_path = row["proposed_output_artifact"].strip()
        if not output_path.startswith("/tmp/"):
            errors.append("proposed_output_artifact_must_be_tmp_path")
    for field in [
        "proposed_non_mutating_review_action",
        "proposed_source_discovery_query",
        "proposed_candidate_official_url",
        "proposed_evidence_summary",
        "proposed_output_artifact",
    ]:
        if PROHIBITED_TEXT_RE.search(row.get(field, "")):
            errors.append(field + "_contains_mutation_acceptance_language")

    return ("invalid" if errors else "valid_non_mutating", errors)


def write_summary(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--summary", type=Path, default=None)
    args = parser.parse_args()

    rows, fieldnames = read_csv_rows(args.input)
    errors: list[dict[str, object]] = []
    by_status: Counter[str] = Counter()
    by_action: Counter[str] = Counter()
    if fieldnames != TEMPLATE_FIELDS:
        errors.append({"row_number": 0, "errors": ["template_header_mismatch"]})

    template_rowset = rowset_sha256(rows)
    if args.input == DEFAULT_INPUT and template_rowset != EXPECTED_TEMPLATE_ROWSET:
        errors.append(
            {
                "row_number": 0,
                "errors": ["committed_template_rowset_mismatch"],
                "expected": EXPECTED_TEMPLATE_ROWSET,
                "observed": template_rowset,
            }
        )
    if len(rows) != EXPECTED_TEMPLATE_ROWS:
        errors.append({"row_number": 0, "errors": ["template_row_count_mismatch"], "observed": len(rows)})
    batch_rows = {row.get("school_gap_resolution_batch_key", "") for row in rows}
    if len(batch_rows) != EXPECTED_BATCH_ROWS:
        errors.append({"row_number": 0, "errors": ["batch_count_mismatch"], "observed": len(batch_rows)})

    for index, row in enumerate(rows, start=2):
        status, row_errors = validate_row(row, index)
        by_status[status] += 1
        action = row.get("proposed_non_mutating_review_action", "").strip()
        if action:
            by_action[action] += 1
        if row_errors:
            errors.append({"row_number": index, "review_template_key": row.get("review_template_key", ""), "errors": row_errors})

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "input": str(args.input),
        "template_rows": len(rows),
        "batch_rows_represented": len(batch_rows),
        "rowset_sha256": template_rowset,
        "expected_rowset_sha256": EXPECTED_TEMPLATE_ROWSET if args.input == DEFAULT_INPUT else None,
        "pending_rows": by_status.get("pending", 0),
        "valid_non_mutating_rows": by_status.get("valid_non_mutating", 0),
        "invalid_rows": by_status.get("invalid", 0) + len([error for error in errors if error.get("row_number") == 0]),
        "by_status": dict(sorted(by_status.items())),
        "by_action": dict(sorted(by_action.items())),
        "error_rows": len(errors),
        "errors": errors[:50],
        "allowed_review_actions": sorted(ALLOWED_REVIEW_ACTIONS),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "candidate_evidence_only": True,
    }

    if args.summary is not None:
        write_summary(args.summary, summary)
    elif args.input == DEFAULT_INPUT:
        write_summary(DEFAULT_SUMMARY, summary)

    print(json.dumps({key: summary[key] for key in ["template_rows", "pending_rows", "valid_non_mutating_rows", "invalid_rows", "rowset_sha256"]}, sort_keys=True))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
