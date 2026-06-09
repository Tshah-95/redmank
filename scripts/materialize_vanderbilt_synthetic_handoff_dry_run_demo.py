#!/usr/bin/env python3
"""Run a synthetic end-to-end Vanderbilt reviewer handoff dry-run demo."""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import materialize_vanderbilt_candidate_review_decision_scaffold as scaffold_materializer
import materialize_vanderbilt_reviewer_decision_patch_workbook as workbook_materializer


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"
TMP_DIR = Path("/tmp/redmank_vanderbilt_synthetic_handoff_dry_run_demo")

OUT_CSV = ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo_summary.json"
OUT_MD = RESEARCH / "vanderbilt-synthetic-handoff-dry-run-demo-2026-06-09.md"

GBRAIN_APPROVAL_LINE = "APPROVE vanderbilt_synthetic_handoff_dry_run_demo_non_mutating_increment"

MUTATION_POLICY = (
    "Synthetic-only Vanderbilt handoff dry-run demonstration. It writes fabricated scaffold, decision, and workbook "
    "rows under /tmp, runs the public slice, extract, and dry-run patch helper commands against those fabricated "
    "inputs, then removes the temporary tree. It does not read or write real Vanderbilt reviewer decisions, fill "
    "real decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, "
    "rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities."
)

FIELDS = [
    "demo_check_key",
    "execution_order",
    "demo_surface",
    "check_name",
    "check_status",
    "expected_behavior",
    "observed_behavior",
    "command",
    "synthetic_rows_written",
    "slice_rows",
    "extracted_patch_rows",
    "valid_non_mutating_rows",
    "apply_executed",
    "tmp_outputs_removed",
    "mutation_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "accepted_person_rows",
    "synthetic_fixture_only",
    "real_vanderbilt_rows_used",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"demo_check_key", "evidence_json", "mutation_policy", "generated_at"}
]


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("demo_check_key", "")))
    ]
    return sha256_text(dumps(material))


def add_check(
    rows: list[dict[str, object]],
    generated_at: str,
    execution_order: int,
    demo_surface: str,
    check_name: str,
    passed: bool,
    observed_behavior: str,
    *,
    command: str = "",
    expected_behavior: str = "",
    synthetic_rows_written: int = 0,
    slice_rows: int = 0,
    extracted_patch_rows: int = 0,
    valid_non_mutating_rows: int = 0,
    apply_executed: bool = False,
    tmp_outputs_removed: bool = False,
    evidence: object | None = None,
) -> None:
    rows.append(
        {
            "demo_check_key": stable_key("vanderbilt_synthetic_handoff_dry_run_demo", execution_order, check_name),
            "execution_order": execution_order,
            "demo_surface": demo_surface,
            "check_name": check_name,
            "check_status": "pass" if passed else "fail",
            "expected_behavior": expected_behavior or check_name,
            "observed_behavior": observed_behavior,
            "command": command,
            "synthetic_rows_written": synthetic_rows_written,
            "slice_rows": slice_rows,
            "extracted_patch_rows": extracted_patch_rows,
            "valid_non_mutating_rows": valid_non_mutating_rows,
            "apply_executed": "true" if apply_executed else "false",
            "tmp_outputs_removed": "true" if tmp_outputs_removed else "false",
            "mutation_allowed": "false",
            "person_ingestion_allowed": "false",
            "denominator_closure_allowed": "false",
            "accepted_person_rows": 0,
            "synthetic_fixture_only": "true",
            "real_vanderbilt_rows_used": 0,
            "evidence_json": dumps(evidence or {}),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
    )


def synthetic_scaffold_rows(generated_at: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for suffix, source_kind in [("alpha", "fixture_heading_signal"), ("beta", "fixture_profile_anchor")]:
        rows.append(
            {
                "decision_scaffold_key": f"fixture_decision_scaffold_{suffix}",
                "source_review_queue_key": f"fixture_review_queue_{suffix}",
                "review_batch_key": "fixture_review_batch_general_surgery",
                "review_queue_lane": "candidate_fingerprint_review",
                "decision_status": "pending_manual_review",
                "decision_priority": "1",
                "program_key": "fixture_program_general_surgery",
                "program_name": "Synthetic General Surgery",
                "candidate_fingerprint_sha256": sha256_text("synthetic-candidate-" + suffix),
                "candidate_source_kind": source_kind,
                "content_sha256": sha256_text("synthetic-content-" + suffix),
                "visible_text_sha256": sha256_text("synthetic-visible-text-" + suffix),
                "allowed_reviewer_actions": (
                    "mark_for_later_exact_person_review; "
                    "mark_duplicate_hash_for_reconciliation; "
                    "reject_candidate_hash_as_parser_noise"
                ),
                "required_confirmation_fields": (
                    "confirm_decision_fingerprint; "
                    "confirm_no_person_ingestion; "
                    "confirm_no_denominator_closure; "
                    "confirm_no_raw_name_added; "
                    "confirm_no_url_rewrite; "
                    "confirm_candidate_fingerprint_only"
                ),
                "decision_fingerprint": f"fixture_decision_fingerprint_{suffix}",
                "manual_decision_file": "synthetic_tmp_only",
                "manual_decision_row_key": f"fixture_manual_decision_row_{suffix}",
                "accepted_person_row": "false",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "evidence_json": dumps({"synthetic_fixture_only": True, "source_kind": source_kind}),
                "mutation_policy": "synthetic fixture row",
                "generated_at": generated_at,
            }
        )
    return rows


def synthetic_decision_rows(scaffold_rows: list[dict[str, object]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for scaffold in scaffold_rows:
        rows.append(
            {
                "manual_decision_row_key": str(scaffold["manual_decision_row_key"]),
                "decision_scaffold_key": str(scaffold["decision_scaffold_key"]),
                "review_batch_key": str(scaffold["review_batch_key"]),
                "review_queue_lane": str(scaffold["review_queue_lane"]),
                "program_key": str(scaffold["program_key"]),
                "program_name": str(scaffold["program_name"]),
                "candidate_fingerprint_sha256": str(scaffold["candidate_fingerprint_sha256"]),
                "candidate_source_kind": str(scaffold["candidate_source_kind"]),
                "decision_fingerprint": str(scaffold["decision_fingerprint"]),
                "reviewer_action": "",
                "reviewer_note": "",
                "confirm_decision_fingerprint": "",
                "confirm_no_person_ingestion": "",
                "confirm_no_denominator_closure": "",
                "confirm_no_raw_name_added": "",
                "confirm_no_url_rewrite": "",
                "confirm_candidate_fingerprint_only": "",
                "confirm_scope_metadata_only": "",
                "confirm_recourse_only": "",
            }
        )
    return rows


def synthetic_workbook_rows(scaffold_rows: list[dict[str, object]], generated_at: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, scaffold in enumerate(scaffold_rows, start=1):
        is_filled = index == 1
        rows.append(
            {
                "workbook_row_key": f"fixture_workbook_row_{index}",
                "operator_packet_key": "fixture_operator_packet_general_surgery",
                "operator_execution_order": "4",
                "source_batch_packet_key": "fixture_batch_packet_general_surgery",
                "review_queue_lane": str(scaffold["review_queue_lane"]),
                "program_key": str(scaffold["program_key"]),
                "program_name": str(scaffold["program_name"]),
                "decision_scaffold_key": str(scaffold["decision_scaffold_key"]),
                "manual_decision_row_key": str(scaffold["manual_decision_row_key"]),
                "candidate_fingerprint_sha256": str(scaffold["candidate_fingerprint_sha256"]),
                "candidate_source_kind": str(scaffold["candidate_source_kind"]),
                "allowed_reviewer_actions": str(scaffold["allowed_reviewer_actions"]),
                "required_confirmation_fields": str(scaffold["required_confirmation_fields"]),
                "decision_fingerprint": str(scaffold["decision_fingerprint"]),
                "reviewer_action": "mark_for_later_exact_person_review" if is_filled else "",
                "confirm_decision_fingerprint": str(scaffold["decision_fingerprint"]) if is_filled else "",
                "confirm_no_person_ingestion": "true" if is_filled else "",
                "confirm_no_denominator_closure": "true" if is_filled else "",
                "confirm_no_raw_name_added": "true" if is_filled else "",
                "confirm_no_url_rewrite": "true" if is_filled else "",
                "confirm_candidate_fingerprint_only": "true" if is_filled else "",
                "confirm_scope_metadata_only": "",
                "confirm_recourse_only": "",
                "workbook_row_status": "synthetic_filled" if is_filled else "synthetic_blank",
                "helper_patch_output_columns_json": dumps(
                    [
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
                ),
                "source_scaffold_rowset_sha256": "synthetic_scaffold_rowset",
                "source_operator_packet_rowset_sha256": "synthetic_operator_rowset",
                "source_patch_template_rowset_sha256": "synthetic_patch_template_rowset",
                "accepted_person_rows": "0",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "raw_candidate_names_committed": "false",
                "raw_person_urls_committed": "false",
                "evidence_json": dumps({"synthetic_fixture_only": True, "filled": is_filled}),
                "mutation_policy": "synthetic fixture row",
                "generated_at": generated_at,
            }
        )
    return rows


def run_command(command: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def command_text(command: list[str]) -> str:
    return " ".join(command)


def parse_json_stdout(stdout: str) -> dict[str, object]:
    return json.loads(stdout) if stdout else {}


def pick(summary: dict[str, object], keys: list[str]) -> dict[str, object]:
    return {key: summary.get(key) for key in keys}


def build_checks(generated_at: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)

    scaffold_path = TMP_DIR / "synthetic_scaffold.json"
    decisions_path = TMP_DIR / "synthetic_decisions.csv"
    workbook_path = TMP_DIR / "synthetic_workbook.csv"
    slice_path = TMP_DIR / "synthetic_workbook_order_4.csv"
    patch_path = TMP_DIR / "synthetic_patch_order_4.csv"
    dry_run_output = TMP_DIR / "dry_run_decisions.csv"
    dry_run_json_output = TMP_DIR / "dry_run_decisions.json"

    scaffold_rows = synthetic_scaffold_rows(generated_at)
    decision_rows = synthetic_decision_rows(scaffold_rows)
    workbook_rows = synthetic_workbook_rows(scaffold_rows, generated_at)
    write_json(scaffold_path, scaffold_rows)
    write_csv(decisions_path, scaffold_materializer.DECISION_FIELDS, decision_rows)
    write_csv(workbook_path, workbook_materializer.FIELDS, workbook_rows)
    add_check(
        rows,
        generated_at,
        1,
        "synthetic_inputs",
        "fabricated tmp inputs written",
        scaffold_path.exists() and decisions_path.exists() and workbook_path.exists(),
        "scaffold_rows=2; decision_rows=2; workbook_rows=2",
        synthetic_rows_written=6,
        evidence={
            "tmp_dir": str(TMP_DIR),
            "scaffold_rows": len(scaffold_rows),
            "decision_rows": len(decision_rows),
            "workbook_rows": len(workbook_rows),
        },
    )

    slice_command = [
        "python3",
        "scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py",
        "--execution-order",
        "4",
        "--workbook",
        str(workbook_path),
        "--output",
        str(slice_path),
    ]
    code, stdout, stderr = run_command(slice_command)
    slice_summary = parse_json_stdout(stdout) if code == 0 else {}
    sliced_rows = read_csv_rows(slice_path) if slice_path.exists() else []
    add_check(
        rows,
        generated_at,
        2,
        "slice_command",
        "synthetic handoff slice command writes two rows",
        code == 0 and slice_summary.get("slice_rows") == 2 and len(sliced_rows) == 2,
        f"exit={code}; slice_rows={slice_summary.get('slice_rows')}; stderr={stderr}",
        command=command_text(slice_command),
        slice_rows=len(sliced_rows),
        evidence=pick(
            slice_summary,
            [
                "execution_order",
                "slice_rows",
                "mutation_allowed",
                "person_ingestion_allowed",
                "denominator_closure_allowed",
                "raw_candidate_names_committed",
                "raw_person_urls_committed",
            ],
        ),
    )

    extract_command = [
        "python3",
        "scripts/extract_vanderbilt_reviewer_decision_patch.py",
        "--workbook",
        str(slice_path),
        "--output",
        str(patch_path),
        "--scaffold",
        str(scaffold_path),
        "--decisions",
        str(decisions_path),
    ]
    code, stdout, stderr = run_command(extract_command)
    extract_summary = parse_json_stdout(stdout) if code == 0 else {}
    patch_rows = read_csv_rows(patch_path) if patch_path.exists() else []
    add_check(
        rows,
        generated_at,
        3,
        "extract_command",
        "synthetic extract command emits one filled patch row",
        code == 0 and extract_summary.get("extracted_patch_rows") == 1 and len(patch_rows) == 1,
        f"exit={code}; extracted_patch_rows={extract_summary.get('extracted_patch_rows')}; stderr={stderr}",
        command=command_text(extract_command),
        slice_rows=int(extract_summary.get("workbook_rows", 0) or 0),
        extracted_patch_rows=len(patch_rows),
        evidence=pick(
            extract_summary,
            [
                "workbook_rows",
                "extracted_patch_rows",
                "include_blank",
                "mutation_allowed",
                "person_ingestion_allowed",
                "denominator_closure_allowed",
                "accepted_person_rows",
            ],
        )
        | {"output_columns_count": len(extract_summary.get("output_columns", []) or [])},
    )

    dry_run_command = [
        "python3",
        "scripts/apply_vanderbilt_reviewer_decision_patch.py",
        "--patch",
        str(patch_path),
        "--scaffold",
        str(scaffold_path),
        "--decisions",
        str(decisions_path),
        "--output",
        str(dry_run_output),
        "--json-output",
        str(dry_run_json_output),
    ]
    code, stdout, stderr = run_command(dry_run_command)
    dry_run_summary = parse_json_stdout(stdout) if code == 0 else {}
    output_absent = not dry_run_output.exists() and not dry_run_json_output.exists()
    add_check(
        rows,
        generated_at,
        4,
        "dry_run_command",
        "synthetic dry-run validates patch without writing outputs",
        code == 0
        and dry_run_summary.get("patch_rows") == 1
        and dry_run_summary.get("valid_non_mutating_rows") == 1
        and dry_run_summary.get("apply") is False
        and output_absent,
        (
            f"exit={code}; patch_rows={dry_run_summary.get('patch_rows')}; "
            f"valid_non_mutating_rows={dry_run_summary.get('valid_non_mutating_rows')}; "
            f"outputs_absent={output_absent}; stderr={stderr}"
        ),
        command=command_text(dry_run_command),
        extracted_patch_rows=int(dry_run_summary.get("patch_rows", 0) or 0),
        valid_non_mutating_rows=int(dry_run_summary.get("valid_non_mutating_rows", 0) or 0),
        apply_executed=False,
        evidence=pick(
            dry_run_summary,
            [
                "apply",
                "patch_rows",
                "valid_non_mutating_rows",
                "mutation_allowed",
                "person_ingestion_allowed",
                "denominator_closure_allowed",
                "accepted_person_rows",
            ],
        )
        | {"dry_run_outputs_absent": output_absent},
    )

    shutil.rmtree(TMP_DIR, ignore_errors=True)
    tmp_removed = not TMP_DIR.exists()
    add_check(
        rows,
        generated_at,
        5,
        "cleanup",
        "synthetic tmp tree removed",
        tmp_removed,
        "tmp_outputs_removed=" + str(tmp_removed).lower(),
        tmp_outputs_removed=tmp_removed,
        evidence={"tmp_dir": str(TMP_DIR)},
    )
    return rows


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Synthetic Handoff Dry Run Demo",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Synthetic Handoff Dry Run Demo",
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
        "## Checks",
        "",
        "| order | surface | check | status | observed |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {execution_order} | {demo_surface} | {check_name} | {check_status} | {observed_behavior} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_checks(generated_at)
    pass_rows = sum(1 for row in rows if row["check_status"] == "pass")
    fail_rows = len(rows) - pass_rows
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "demo_check_rows": len(rows),
        "pass_rows": pass_rows,
        "fail_rows": fail_rows,
        "synthetic_fixture_only": True,
        "real_vanderbilt_rows_used": 0,
        "tmp_dir": str(TMP_DIR),
        "tmp_outputs_removed": True,
        "synthetic_input_rows_written": 6,
        "slice_rows": 2,
        "extracted_patch_rows": 1,
        "valid_non_mutating_rows": 1,
        "dry_run_patch_rows": 1,
        "dry_run_outputs_written": 0,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "accepted_person_rows": 0,
        "apply_executed": False,
        "gbrain_approval_status": "approved_non_mutating_vanderbilt_synthetic_handoff_dry_run_demo_increment",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, FIELDS, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["demo_check_rows", "pass_rows", "fail_rows", "rowset_sha256"]}, sort_keys=True))
    if fail_rows:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
