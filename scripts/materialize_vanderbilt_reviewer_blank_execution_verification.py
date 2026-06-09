#!/usr/bin/env python3
"""Verify blank Vanderbilt reviewer execution slices fail closed."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"
TMP_ROOT = Path("/tmp/redmank_vanderbilt_blank_execution")

EXECUTION_READINESS_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge_summary.json"
SLICE_INDEX_CSV = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.csv"
SLICE_INDEX_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index_summary.json"
DECISION_AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification_summary.json"
OUT_MD = RESEARCH / "vanderbilt-reviewer-blank-execution-verification-2026-06-09.md"

EXECUTION_READINESS_ROWSET = "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa"
SLICE_INDEX_ROWSET = "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4"
DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"

EXPECTED_BLANK_EXTRACT_MESSAGE = "No filled workbook rows to extract."

MUTATION_POLICY = (
    "Non-mutating verification that blank Vanderbilt reviewer execution slices fail closed. It runs bounded "
    "slice commands only to /tmp, proves extraction without filled reviewer decisions fails with the expected "
    "empty-patch message, proves an explicit allow-empty dry run validates zero rows without --apply, and removes "
    "temporary outputs. It does not fill reviewer decisions, apply patches, write committed decision files, accept "
    "people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, publish "
    "raw candidate labels or URLs, or collapse identities."
)

FIELDS = [
    "blank_execution_verification_key",
    "execution_order",
    "operator_packet_key",
    "review_queue_lane",
    "program_key",
    "program_name",
    "workbook_row_count",
    "slice_output_path",
    "patch_output_path",
    "slice_exit_code",
    "slice_row_count",
    "blank_extract_exit_code",
    "blank_extract_failed_closed",
    "allow_empty_extract_exit_code",
    "allow_empty_patch_rows",
    "dry_run_exit_code",
    "dry_run_patch_rows",
    "dry_run_valid_non_mutating_rows",
    "tmp_outputs_removed",
    "verification_status",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "apply_executed",
    "source_execution_readiness_rowset_sha256",
    "source_slice_index_rowset_sha256",
    "source_decision_audit_rowset_sha256",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"blank_execution_verification_key", "evidence_json", "mutation_policy", "generated_at"}
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


def read_csv_fields_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


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
        for row in sorted(rows, key=lambda item: str(item.get("blank_execution_verification_key", "")))
    ]
    return sha256_text(dumps(material))


def verify_boundaries() -> None:
    readiness = read_json(EXECUTION_READINESS_SUMMARY)
    slice_index = read_json(SLICE_INDEX_SUMMARY)
    decision_audit = read_json(DECISION_AUDIT_SUMMARY)
    if not all(isinstance(item, dict) for item in [readiness, slice_index, decision_audit]):
        raise SystemExit("Expected blank execution source summaries to be JSON objects.")
    checks = {
        "execution_readiness": readiness.get("rowset_sha256") == EXECUTION_READINESS_ROWSET
        and readiness.get("bridge_rows") == 19
        and readiness.get("ready_program_rows") == 19
        and readiness.get("slice_index_rows_represented") == 20
        and readiness.get("pending_decision_rows_represented") == 159
        and readiness.get("valid_non_mutating_decision_rows_represented") == 0
        and readiness.get("invalid_decision_rows_represented") == 0
        and readiness.get("mutation_allowed") is False
        and readiness.get("person_ingestion_allowed") is False,
        "slice_index": slice_index.get("rowset_sha256") == SLICE_INDEX_ROWSET
        and slice_index.get("slice_index_rows") == 20
        and slice_index.get("workbook_rows_represented") == 159
        and slice_index.get("slice_outputs_default_tmp_only") is True
        and slice_index.get("mutation_allowed") is False,
        "decision_audit": decision_audit.get("rowset_sha256") == DECISION_AUDIT_ROWSET
        and decision_audit.get("audit_rows") == 159
        and decision_audit.get("pending_rows") == 159
        and decision_audit.get("valid_non_mutating_rows") == 0
        and decision_audit.get("invalid_rows") == 0
        and decision_audit.get("accepted_person_rows") == 0,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected blank execution source boundary: " + dumps(checks))


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def parse_json_stdout(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise SystemExit("Expected JSON stdout from command: " + result.stdout) from exc
    if not isinstance(parsed, dict):
        raise SystemExit("Expected JSON object stdout from command.")
    return parsed


def cleanup_path(path: Path) -> bool:
    if path.exists():
        path.unlink()
    return not path.exists()


def verify_one_slice(index_row: dict[str, str], generated_at: str) -> dict[str, object]:
    execution_order = int(index_row.get("execution_order", "0"))
    slice_output = TMP_ROOT / f"vanderbilt_reviewer_workbook_order_{execution_order}.csv"
    patch_output = TMP_ROOT / f"vanderbilt_reviewer_patch_order_{execution_order}.csv"
    cleanup_path(slice_output)
    cleanup_path(patch_output)

    slice_result = run_command(
        [
            "python3",
            "scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py",
            "--execution-order",
            str(execution_order),
            "--output",
            str(slice_output),
        ]
    )
    slice_summary = parse_json_stdout(slice_result) if slice_result.returncode == 0 else {}
    slice_fields, slice_rows = read_csv_fields_rows(slice_output) if slice_output.exists() else ([], [])

    blank_extract_result = run_command(
        [
            "python3",
            "scripts/extract_vanderbilt_reviewer_decision_patch.py",
            "--workbook",
            str(slice_output),
            "--output",
            str(patch_output),
        ]
    )
    blank_output = (blank_extract_result.stdout + blank_extract_result.stderr).strip()
    blank_failed_closed = (
        blank_extract_result.returncode != 0
        and EXPECTED_BLANK_EXTRACT_MESSAGE in blank_output
        and not patch_output.exists()
    )

    allow_empty_result = run_command(
        [
            "python3",
            "scripts/extract_vanderbilt_reviewer_decision_patch.py",
            "--workbook",
            str(slice_output),
            "--output",
            str(patch_output),
            "--allow-empty",
        ]
    )
    allow_empty_summary = parse_json_stdout(allow_empty_result) if allow_empty_result.returncode == 0 else {}
    patch_fields, patch_rows = read_csv_fields_rows(patch_output) if patch_output.exists() else ([], [])

    dry_run_result = run_command(
        [
            "python3",
            "scripts/apply_vanderbilt_reviewer_decision_patch.py",
            "--patch",
            str(patch_output),
        ]
    )
    dry_run_summary = parse_json_stdout(dry_run_result) if dry_run_result.returncode == 0 else {}

    slice_removed = cleanup_path(slice_output)
    patch_removed = cleanup_path(patch_output)
    row_ok = (
        slice_result.returncode == 0
        and int(slice_summary.get("slice_rows", -1)) == int(index_row.get("workbook_row_count", -2))
        and len(slice_rows) == int(index_row.get("workbook_row_count", -2))
        and blank_failed_closed
        and allow_empty_result.returncode == 0
        and allow_empty_summary.get("extracted_patch_rows") == 0
        and len(patch_rows) == 0
        and dry_run_result.returncode == 0
        and dry_run_summary.get("patch_rows") == 0
        and dry_run_summary.get("valid_non_mutating_rows") == 0
        and dry_run_summary.get("apply") is False
        and slice_removed
        and patch_removed
    )
    return {
        "blank_execution_verification_key": stable_key(
            "vanderbilt_blank_execution_verification",
            index_row.get("slice_index_key", ""),
            SLICE_INDEX_ROWSET,
        ),
        "execution_order": execution_order,
        "operator_packet_key": index_row.get("operator_packet_key", ""),
        "review_queue_lane": index_row.get("review_queue_lane", ""),
        "program_key": index_row.get("program_key", ""),
        "program_name": index_row.get("program_name", ""),
        "workbook_row_count": int(index_row.get("workbook_row_count", 0)),
        "slice_output_path": str(slice_output),
        "patch_output_path": str(patch_output),
        "slice_exit_code": slice_result.returncode,
        "slice_row_count": len(slice_rows),
        "blank_extract_exit_code": blank_extract_result.returncode,
        "blank_extract_failed_closed": str(blank_failed_closed).lower(),
        "allow_empty_extract_exit_code": allow_empty_result.returncode,
        "allow_empty_patch_rows": len(patch_rows),
        "dry_run_exit_code": dry_run_result.returncode,
        "dry_run_patch_rows": int(dry_run_summary.get("patch_rows", -1)),
        "dry_run_valid_non_mutating_rows": int(dry_run_summary.get("valid_non_mutating_rows", -1)),
        "tmp_outputs_removed": str(slice_removed and patch_removed).lower(),
        "verification_status": "blank_slice_fail_closed_verified" if row_ok else "verification_failed",
        "accepted_person_rows": 0,
        "person_ingestion_allowed": "false",
        "denominator_closure_allowed": "false",
        "apply_executed": "false",
        "source_execution_readiness_rowset_sha256": EXECUTION_READINESS_ROWSET,
        "source_slice_index_rowset_sha256": SLICE_INDEX_ROWSET,
        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
        "evidence_json": dumps(
            {
                "slice_stdout_json_keys": sorted(slice_summary.keys()),
                "slice_fields_count": len(slice_fields),
                "blank_extract_expected_message": EXPECTED_BLANK_EXTRACT_MESSAGE,
                "blank_extract_observed_tail": blank_output[-120:],
                "allow_empty_extract_stdout_json_keys": sorted(allow_empty_summary.keys()),
                "patch_fields": patch_fields,
                "dry_run_stdout_json_keys": sorted(dry_run_summary.keys()),
                "tmp_root": str(TMP_ROOT),
            }
        ),
        "mutation_policy": MUTATION_POLICY,
        "generated_at": generated_at,
    }


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Reviewer Blank Execution Verification",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Reviewer Blank Execution Verification",
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
        "## Slice Checks",
        "",
        "| order | program | lane | rows | status |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {execution_order} | {program_name} | {review_queue_lane} | {workbook_row_count} | {verification_status} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    verify_boundaries()
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)
    TMP_ROOT.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat()
    slice_index_rows = sorted(read_csv_rows(SLICE_INDEX_CSV), key=lambda row: int(row.get("execution_order", 0)))
    if len(slice_index_rows) != 20:
        raise SystemExit("Expected exactly 20 Vanderbilt reviewer slice-index rows.")
    rows = [verify_one_slice(row, generated_at) for row in slice_index_rows]
    if TMP_ROOT.exists() and not any(TMP_ROOT.iterdir()):
        TMP_ROOT.rmdir()

    by_status = Counter(str(row["verification_status"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_execution_readiness_rowset_sha256": EXECUTION_READINESS_ROWSET,
        "source_slice_index_rowset_sha256": SLICE_INDEX_ROWSET,
        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
        "verification_rows": len(rows),
        "pass_rows": by_status.get("blank_slice_fail_closed_verified", 0),
        "fail_rows": by_status.get("verification_failed", 0),
        "slice_rows_represented": sum(int(row["slice_row_count"]) for row in rows),
        "blank_extract_fail_closed_rows": sum(1 for row in rows if row["blank_extract_failed_closed"] == "true"),
        "allow_empty_patch_rows_represented": sum(int(row["allow_empty_patch_rows"]) for row in rows),
        "dry_run_patch_rows_represented": sum(int(row["dry_run_patch_rows"]) for row in rows),
        "dry_run_valid_non_mutating_rows_represented": sum(
            int(row["dry_run_valid_non_mutating_rows"]) for row in rows
        ),
        "tmp_outputs_removed_rows": sum(1 for row in rows if row["tmp_outputs_removed"] == "true"),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "apply_executed": False,
        "accepted_person_rows": 0,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    if (
        summary["verification_rows"] != 20
        or summary["pass_rows"] != 20
        or summary["fail_rows"] != 0
        or summary["slice_rows_represented"] != 159
        or summary["blank_extract_fail_closed_rows"] != 20
        or summary["allow_empty_patch_rows_represented"] != 0
        or summary["dry_run_patch_rows_represented"] != 0
        or summary["dry_run_valid_non_mutating_rows_represented"] != 0
        or summary["tmp_outputs_removed_rows"] != 20
    ):
        raise SystemExit("Blank execution verification failed coverage checks: " + dumps(summary))

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["verification_rows", "pass_rows", "fail_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
