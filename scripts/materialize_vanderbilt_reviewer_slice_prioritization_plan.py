#!/usr/bin/env python3
"""Materialize a public-safe Vanderbilt reviewer slice prioritization plan."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SLICE_INDEX_CSV = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.csv"
SLICE_INDEX_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index_summary.json"
EXECUTION_READINESS_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge_summary.json"
BLANK_EXECUTION_CSV = ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification.csv"
BLANK_EXECUTION_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification_summary.json"
DECISION_AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan_summary.json"
OUT_MD = RESEARCH / "vanderbilt-reviewer-slice-prioritization-plan-2026-06-09.md"

SLICE_INDEX_ROWSET = "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4"
EXECUTION_READINESS_ROWSET = "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa"
BLANK_EXECUTION_ROWSET = "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e"
DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"

GBRAIN_APPROVAL_LINE = "APPROVE vanderbilt_reviewer_slice_prioritization_plan_non_mutating_increment"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt reviewer slice prioritization plan. It ranks the 20 fail-closed reviewer slices using "
    "only public-safe lane, row-count, command-surface, and blank-execution verification metrics. It does not fill "
    "reviewer decisions, extract filled patches, run apply, approve people, ingest people, close denominators, verify "
    "Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or "
    "collapse identities."
)

PROHIBITED_MUTATIONS = [
    "fill_reviewer_decisions_without_operator_action",
    "extract_filled_patch_without_review",
    "apply_reviewer_patch",
    "accept_person",
    "ingest_person",
    "close_denominator",
    "verify_vanderbilt_school",
    "rewrite_url",
    "publish_raw_candidate_label",
    "publish_raw_person_url",
    "accept_enrichment",
    "collapse_identity",
]

APPROVAL_REQUIRED_FOR = [
    "person_ingestion",
    "denominator_closure",
    "parser_acceptance",
    "scope_closure",
    "url_rewrite",
    "identity_collapse",
]

FIELDS = [
    "prioritization_key",
    "priority_rank",
    "priority_score",
    "assignment_band",
    "assignment_status",
    "execution_order",
    "operator_packet_key",
    "review_queue_lane",
    "program_key",
    "program_name",
    "workbook_row_count",
    "slice_output_path",
    "patch_output_path",
    "slice_command",
    "extract_command",
    "patch_dry_run_command",
    "blank_verification_status",
    "blank_extract_failed_closed",
    "dry_run_patch_rows",
    "tmp_outputs_removed",
    "recommended_reviewer_action",
    "success_condition",
    "approval_required_for",
    "prohibited_mutations",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "apply_executed",
    "source_slice_index_rowset_sha256",
    "source_execution_readiness_rowset_sha256",
    "source_blank_execution_rowset_sha256",
    "source_decision_audit_rowset_sha256",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"prioritization_key", "evidence_json", "mutation_policy", "generated_at"}
]

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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("prioritization_key", "")))
    ]
    return sha256_text(dumps(material))


def semicolon(values: list[str]) -> str:
    return "; ".join(values)


def as_bool(value: str) -> bool:
    return str(value).strip().lower() == "true"


def as_int(value: object) -> int:
    return int(str(value or "0"))


def assignment_group(row: dict[str, str]) -> tuple[int, int, int]:
    lane = row.get("review_queue_lane", "")
    count = as_int(row.get("workbook_row_count"))
    execution_order = as_int(row.get("execution_order"))
    if lane == "candidate_fingerprint_review" and count <= 4:
        return (1, count, execution_order)
    if lane in {"linked_scope_metadata_review", "route_recourse_review"} and count <= 1:
        return (2, count, execution_order)
    if lane == "candidate_fingerprint_review" and count <= 12:
        return (3, count, execution_order)
    if lane == "candidate_fingerprint_review":
        return (4, count, execution_order)
    return (5, count, execution_order)


def assignment_band(group: int, count: int) -> str:
    if group == 1:
        return "first_pass_small_candidate_slice"
    if group == 2:
        return "scope_or_recourse_micro_slice"
    if group == 3:
        return "standard_candidate_slice"
    if group == 4:
        return "large_candidate_slice"
    return "other_slice"


def priority_score(group: int, count: int, execution_order: int) -> int:
    return 10000 - (group * 1000) - (count * 10) - execution_order


def verify_source_boundary() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    slice_summary = read_json(SLICE_INDEX_SUMMARY)
    readiness_summary = read_json(EXECUTION_READINESS_SUMMARY)
    blank_summary = read_json(BLANK_EXECUTION_SUMMARY)
    audit_summary = read_json(DECISION_AUDIT_SUMMARY)
    if not all(isinstance(item, dict) for item in [slice_summary, readiness_summary, blank_summary, audit_summary]):
        raise SystemExit("Expected Vanderbilt prioritization source summaries to be JSON objects.")
    checks = {
        "slice_index": slice_summary.get("rowset_sha256") == SLICE_INDEX_ROWSET
        and slice_summary.get("slice_index_rows") == 20
        and slice_summary.get("workbook_rows_represented") == 159
        and slice_summary.get("slice_outputs_default_tmp_only") is True
        and slice_summary.get("mutation_allowed") is False,
        "readiness": readiness_summary.get("rowset_sha256") == EXECUTION_READINESS_ROWSET
        and readiness_summary.get("bridge_rows") == 19
        and readiness_summary.get("ready_program_rows") == 19
        and readiness_summary.get("slice_index_rows_represented") == 20
        and readiness_summary.get("workbook_rows_represented") == 159
        and readiness_summary.get("mutation_allowed") is False
        and readiness_summary.get("person_ingestion_allowed") is False,
        "blank_execution": blank_summary.get("rowset_sha256") == BLANK_EXECUTION_ROWSET
        and blank_summary.get("verification_rows") == 20
        and blank_summary.get("pass_rows") == 20
        and blank_summary.get("fail_rows") == 0
        and blank_summary.get("slice_rows_represented") == 159
        and blank_summary.get("blank_extract_fail_closed_rows") == 20
        and blank_summary.get("dry_run_patch_rows_represented") == 0
        and blank_summary.get("tmp_outputs_removed_rows") == 20
        and blank_summary.get("apply_executed") is False,
        "decision_audit": audit_summary.get("rowset_sha256") == DECISION_AUDIT_ROWSET
        and audit_summary.get("audit_rows") == 159
        and audit_summary.get("pending_rows") == 159
        and audit_summary.get("valid_non_mutating_rows") == 0
        and audit_summary.get("invalid_rows") == 0
        and audit_summary.get("accepted_person_rows") == 0
        and audit_summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected Vanderbilt prioritization source boundary: " + dumps(checks))

    slice_rows = read_csv_rows(SLICE_INDEX_CSV)
    blank_rows = read_csv_rows(BLANK_EXECUTION_CSV)
    if len(slice_rows) != 20 or len(blank_rows) != 20:
        raise SystemExit("Expected 20 slice-index rows and 20 blank-execution rows.")
    return slice_rows, blank_rows, {
        "slice_summary": slice_summary,
        "readiness_summary": readiness_summary,
        "blank_summary": blank_summary,
        "audit_summary": audit_summary,
    }


def build_rows(generated_at: str) -> list[dict[str, object]]:
    slice_rows, blank_rows, summaries = verify_source_boundary()
    blank_by_order = {row["execution_order"]: row for row in blank_rows}
    ranked_source_rows = sorted(slice_rows, key=assignment_group)
    rows: list[dict[str, object]] = []
    for rank, source in enumerate(ranked_source_rows, start=1):
        blank = blank_by_order.get(source["execution_order"], {})
        if not blank:
            raise SystemExit("Missing blank execution verification for execution_order=" + source["execution_order"])
        group, count, execution_order = assignment_group(source)
        score = priority_score(group, count, execution_order)
        blank_ok = (
            blank.get("verification_status") == "blank_slice_fail_closed_verified"
            and as_bool(blank.get("blank_extract_failed_closed", ""))
            and as_int(blank.get("dry_run_patch_rows")) == 0
            and as_bool(blank.get("tmp_outputs_removed", ""))
            and blank.get("apply_executed") == "false"
        )
        if not blank_ok:
            raise SystemExit("Blank execution verification is not passing for execution_order=" + source["execution_order"])
        recommended_action = (
            "Slice this workbook to /tmp, fill only the allowed non-mutating reviewer-action fields for this bounded "
            "slice, extract a strict patch, run the patch helper as a dry run, and do not run --apply until reviewed."
        )
        success_condition = (
            "Strict patch extraction succeeds only after filled reviewer rows are present; dry-run apply reports "
            "valid_non_mutating_rows for the slice while accepted_person_rows remains 0 and apply_executed remains false."
        )
        rows.append(
            {
                "prioritization_key": stable_key(
                    "vanderbilt_reviewer_slice_prioritization",
                    rank,
                    source.get("execution_order"),
                    source.get("operator_packet_key"),
                    BLANK_EXECUTION_ROWSET,
                ),
                "priority_rank": rank,
                "priority_score": score,
                "assignment_band": assignment_band(group, count),
                "assignment_status": "ready_for_bounded_human_reviewer_input",
                "execution_order": source.get("execution_order", ""),
                "operator_packet_key": source.get("operator_packet_key", ""),
                "review_queue_lane": source.get("review_queue_lane", ""),
                "program_key": source.get("program_key", ""),
                "program_name": source.get("program_name", ""),
                "workbook_row_count": count,
                "slice_output_path": source.get("slice_output_path", ""),
                "patch_output_path": source.get("patch_output_path", ""),
                "slice_command": source.get("slice_command", ""),
                "extract_command": source.get("extract_command", ""),
                "patch_dry_run_command": source.get("patch_dry_run_command", ""),
                "blank_verification_status": blank.get("verification_status", ""),
                "blank_extract_failed_closed": blank.get("blank_extract_failed_closed", ""),
                "dry_run_patch_rows": as_int(blank.get("dry_run_patch_rows")),
                "tmp_outputs_removed": blank.get("tmp_outputs_removed", ""),
                "recommended_reviewer_action": recommended_action,
                "success_condition": success_condition,
                "approval_required_for": semicolon(APPROVAL_REQUIRED_FOR),
                "prohibited_mutations": semicolon(PROHIBITED_MUTATIONS),
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "apply_executed": "false",
                "source_slice_index_rowset_sha256": SLICE_INDEX_ROWSET,
                "source_execution_readiness_rowset_sha256": EXECUTION_READINESS_ROWSET,
                "source_blank_execution_rowset_sha256": BLANK_EXECUTION_ROWSET,
                "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
                "evidence_json": dumps(
                    {
                        "assignment_group": group,
                        "rank_basis": ["assignment_group", "workbook_row_count", "execution_order"],
                        "blank_execution_verification_key": blank.get("blank_execution_verification_key"),
                        "blank_execution_rowset_sha256": BLANK_EXECUTION_ROWSET,
                        "decision_audit_pending_rows": summaries["audit_summary"].get("pending_rows"),
                        "decision_audit_valid_non_mutating_rows": summaries["audit_summary"].get(
                            "valid_non_mutating_rows"
                        ),
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )
    return rows


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Reviewer Slice Prioritization Plan",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Reviewer Slice Prioritization Plan",
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
        "## Priority Rows",
        "",
        "| rank | order | band | lane | program | rows | status |",
        "| ---: | ---: | --- | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {priority_rank} | {execution_order} | {assignment_band} | {review_queue_lane} | {program_name} | {workbook_row_count} | {assignment_status} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows(generated_at)
    band_counts = Counter(str(row["assignment_band"]) for row in rows)
    lane_counts = Counter(str(row["review_queue_lane"]) for row in rows)
    first = rows[0] if rows else {}
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "prioritization_rows": len(rows),
        "slice_rows_represented": sum(as_int(row["workbook_row_count"]) for row in rows),
        "ready_for_bounded_human_reviewer_input_rows": sum(
            1 for row in rows if row["assignment_status"] == "ready_for_bounded_human_reviewer_input"
        ),
        "blank_execution_pass_rows_represented": sum(
            1 for row in rows if row["blank_verification_status"] == "blank_slice_fail_closed_verified"
        ),
        "dry_run_patch_rows_represented": sum(as_int(row["dry_run_patch_rows"]) for row in rows),
        "accepted_person_rows": 0,
        "apply_executed": False,
        "first_priority_execution_order": first.get("execution_order", ""),
        "first_priority_program_name": first.get("program_name", ""),
        "first_priority_workbook_row_count": first.get("workbook_row_count", 0),
        "by_assignment_band": dict(sorted(band_counts.items())),
        "by_review_queue_lane": dict(sorted(lane_counts.items())),
        "source_slice_index_rowset_sha256": SLICE_INDEX_ROWSET,
        "source_execution_readiness_rowset_sha256": EXECUTION_READINESS_ROWSET,
        "source_blank_execution_rowset_sha256": BLANK_EXECUTION_ROWSET,
        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
        "gbrain_approval_status": "approved_non_mutating_vanderbilt_reviewer_slice_prioritization_plan_increment",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["prioritization_rows", "slice_rows_represented", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
