#!/usr/bin/env python3
"""Verify Vanderbilt patch helpers with synthetic fixtures only."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

import apply_vanderbilt_reviewer_decision_patch as patch_helper
import extract_vanderbilt_reviewer_decision_patch as extractor
import materialize_vanderbilt_reviewer_decision_patch_workbook as workbook_materializer


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

OUT_CSV = ARTIFACTS / "vanderbilt_patch_helper_fixture_verification.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_patch_helper_fixture_verification.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_patch_helper_fixture_verification_summary.json"
OUT_MD = RESEARCH / "vanderbilt-patch-helper-fixture-verification-2026-06-09.md"

GBRAIN_APPROVAL_LINE = "APPROVE vanderbilt_patch_helper_fixture_verification_non_mutating_increment"

MUTATION_POLICY = (
    "Synthetic-only Vanderbilt patch-helper fixture verification. It imports helper functions and exercises fabricated "
    "keys, fingerprints, workbook rows, patch rows, and confirmation fields in memory. It writes only verification "
    "artifacts and does not read or write real reviewer decisions, extract real filled patches, run apply, approve "
    "people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, "
    "publish raw candidate labels or person URLs, or collapse identities."
)

FIELDS = [
    "fixture_check_key",
    "execution_order",
    "helper_surface",
    "check_name",
    "check_status",
    "expected_behavior",
    "observed_behavior",
    "mutation_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "apply_executed",
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
    if field not in {"fixture_check_key", "evidence_json", "mutation_policy", "generated_at"}
]

csv.field_size_limit(sys.maxsize)


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


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
        for row in sorted(rows, key=lambda item: str(item.get("fixture_check_key", "")))
    ]
    return sha256_text(dumps(material))


def synthetic_scaffold() -> dict[str, object]:
    return {
        "manual_decision_row_key": "fixture_manual_decision_row_alpha",
        "decision_scaffold_key": "fixture_decision_scaffold_alpha",
        "review_batch_key": "fixture_review_batch_alpha",
        "review_queue_lane": "candidate_fingerprint_review",
        "program_key": "fixture_program_key_alpha",
        "program_name": "Fixture Program",
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
        "decision_fingerprint": "fixture_decision_fingerprint_alpha",
    }


def synthetic_decision() -> dict[str, str]:
    return {
        "manual_decision_row_key": "fixture_manual_decision_row_alpha",
        "decision_scaffold_key": "fixture_decision_scaffold_alpha",
        "review_batch_key": "fixture_review_batch_alpha",
        "review_queue_lane": "candidate_fingerprint_review",
        "program_key": "fixture_program_key_alpha",
        "program_name": "Fixture Program",
        "candidate_fingerprint_sha256": "f" * 64,
        "candidate_source_kind": "fixture_source_kind",
        "decision_fingerprint": "fixture_decision_fingerprint_alpha",
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


def valid_patch(action: str = "mark_for_later_exact_person_review") -> dict[str, str]:
    return {
        "manual_decision_row_key": "fixture_manual_decision_row_alpha",
        "reviewer_action": action,
        "confirm_decision_fingerprint": "fixture_decision_fingerprint_alpha",
        "confirm_no_person_ingestion": "true",
        "confirm_no_denominator_closure": "true",
        "confirm_no_raw_name_added": "true",
        "confirm_no_url_rewrite": "true",
        "confirm_candidate_fingerprint_only": "true",
        "confirm_scope_metadata_only": "",
        "confirm_recourse_only": "",
    }


def workbook_row(**overrides: str) -> dict[str, str]:
    row = {
        "workbook_row_key": "fixture_workbook_row_alpha",
        "operator_packet_key": "fixture_operator_packet_alpha",
        "operator_execution_order": "1",
        "source_batch_packet_key": "fixture_batch_packet_alpha",
        "review_queue_lane": "candidate_fingerprint_review",
        "program_key": "fixture_program_key_alpha",
        "program_name": "Fixture Program",
        "decision_scaffold_key": "fixture_decision_scaffold_alpha",
        "manual_decision_row_key": "fixture_manual_decision_row_alpha",
        "candidate_fingerprint_sha256": "f" * 64,
        "candidate_source_kind": "fixture_source_kind",
        "allowed_reviewer_actions": synthetic_scaffold()["allowed_reviewer_actions"],
        "required_confirmation_fields": synthetic_scaffold()["required_confirmation_fields"],
        "decision_fingerprint": "fixture_decision_fingerprint_alpha",
        "reviewer_action": "",
        "confirm_decision_fingerprint": "",
        "confirm_no_person_ingestion": "",
        "confirm_no_denominator_closure": "",
        "confirm_no_raw_name_added": "",
        "confirm_no_url_rewrite": "",
        "confirm_candidate_fingerprint_only": "",
        "confirm_scope_metadata_only": "",
        "confirm_recourse_only": "",
        "workbook_row_status": "fixture_blank",
        "helper_patch_output_columns_json": dumps(patch_helper.PATCH_FIELDS),
        "source_scaffold_rowset_sha256": "fixture_scaffold_rowset",
        "source_operator_packet_rowset_sha256": "fixture_operator_rowset",
        "source_patch_template_rowset_sha256": "fixture_template_rowset",
        "accepted_person_rows": "0",
        "person_ingestion_allowed": "false",
        "denominator_closure_allowed": "false",
        "raw_candidate_names_committed": "false",
        "raw_person_urls_committed": "false",
        "evidence_json": dumps({"fixture": True}),
        "mutation_policy": "synthetic fixture row",
        "generated_at": "fixture_generated_at",
    }
    row.update(overrides)
    return row


def expect_success(fn: Callable[[], object]) -> tuple[bool, str, object]:
    try:
        observed = fn()
    except SystemExit as exc:
        return False, str(exc), {}
    return True, "success", observed


def expect_failure(fn: Callable[[], object], expected_fragment: str) -> tuple[bool, str, object]:
    try:
        fn()
    except SystemExit as exc:
        message = str(exc)
        return expected_fragment in message, message, {"expected_fragment": expected_fragment}
    return False, "unexpected_success", {"expected_fragment": expected_fragment}


def validate_patch_rows(patch_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, object]]]:
    return patch_helper.validate_patch_rows(
        patch_rows,
        {"fixture_manual_decision_row_alpha": synthetic_scaffold()},
        {"fixture_manual_decision_row_alpha": synthetic_decision()},
    )


def validate_context(rows: list[dict[str, str]]) -> None:
    extractor.validate_context_rows(rows, {"fixture_manual_decision_row_alpha": synthetic_scaffold()})


def add_check(
    rows: list[dict[str, object]],
    generated_at: str,
    execution_order: int,
    helper_surface: str,
    check_name: str,
    passed: bool,
    observed_behavior: str,
    evidence: object,
    expected_behavior: str = "",
) -> None:
    rows.append(
        {
            "fixture_check_key": stable_key("vanderbilt_patch_helper_fixture_check", execution_order, check_name),
            "execution_order": execution_order,
            "helper_surface": helper_surface,
            "check_name": check_name,
            "check_status": "pass" if passed else "fail",
            "expected_behavior": expected_behavior or check_name,
            "observed_behavior": observed_behavior,
            "mutation_allowed": "false",
            "person_ingestion_allowed": "false",
            "denominator_closure_allowed": "false",
            "apply_executed": "false",
            "accepted_person_rows": 0,
            "synthetic_fixture_only": "true",
            "real_vanderbilt_rows_used": 0,
            "evidence_json": dumps(evidence),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
    )


def build_checks(generated_at: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    passed, observed, evidence = expect_success(
        lambda: patch_helper.validate_patch_header(patch_helper.PATCH_FIELDS)
    )
    add_check(rows, generated_at, 1, "patch_header", "valid header accepted", passed, observed, evidence)

    passed, observed, evidence = expect_failure(
        lambda: patch_helper.validate_patch_header(patch_helper.PATCH_FIELDS[:-1]),
        "Patch is missing required columns",
    )
    add_check(rows, generated_at, 2, "patch_header", "missing patch column rejected", passed, observed, evidence)

    passed, observed, evidence = expect_failure(
        lambda: patch_helper.validate_patch_header(patch_helper.PATCH_FIELDS + ["unsupported_fixture_column"]),
        "Patch contains unsupported columns",
    )
    add_check(rows, generated_at, 3, "patch_header", "extra patch column rejected", passed, observed, evidence)

    passed, observed, evidence = expect_success(lambda: validate_patch_rows([valid_patch()]))
    add_check(
        rows,
        generated_at,
        4,
        "patch_rows",
        "valid non-mutating synthetic patch accepted",
        passed,
        observed,
        {"validated_rows": len(evidence[0]) if passed else 0, "audit_rows": len(evidence[1]) if passed else 0},
    )

    bad = valid_patch("unsupported_fixture_action")
    passed, observed, evidence = expect_failure(lambda: validate_patch_rows([bad]), "reviewer_action_not_allowed")
    add_check(rows, generated_at, 5, "patch_rows", "unsupported action rejected", passed, observed, evidence)

    bad = dict(valid_patch())
    bad["confirm_decision_fingerprint"] = "stale_fixture_fingerprint"
    passed, observed, evidence = expect_failure(
        lambda: validate_patch_rows([bad]), "decision_fingerprint_confirmation_missing_or_mismatched"
    )
    add_check(rows, generated_at, 6, "patch_rows", "stale fingerprint rejected", passed, observed, evidence)

    bad = dict(valid_patch())
    bad["confirm_scope_metadata_only"] = "true"
    passed, observed, evidence = expect_failure(
        lambda: validate_patch_rows([bad]), "Patch sets confirmation fields outside this row's lane"
    )
    add_check(rows, generated_at, 7, "patch_rows", "irrelevant lane confirmation rejected", passed, observed, evidence)

    passed, observed, evidence = expect_failure(
        lambda: validate_patch_rows([valid_patch(), valid_patch()]), "Patch contains duplicate manual_decision_row_key"
    )
    add_check(rows, generated_at, 8, "patch_rows", "duplicate patch key rejected", passed, observed, evidence)

    passed, observed, evidence = expect_success(
        lambda: extractor.validate_workbook_header(workbook_materializer.FIELDS)
    )
    add_check(rows, generated_at, 9, "workbook_header", "valid workbook header accepted", passed, observed, evidence)

    passed, observed, evidence = expect_failure(
        lambda: extractor.validate_workbook_header(workbook_materializer.FIELDS + ["unsupported_fixture_column"]),
        "Workbook contains unsupported columns",
    )
    add_check(rows, generated_at, 10, "workbook_header", "extra workbook column rejected", passed, observed, evidence)

    passed, observed, evidence = expect_success(lambda: validate_context([workbook_row()]))
    add_check(rows, generated_at, 11, "workbook_context", "blank synthetic workbook row accepted", passed, observed, evidence)

    passed, observed, evidence = expect_failure(
        lambda: validate_context([workbook_row(confirm_decision_fingerprint="fixture_decision_fingerprint_alpha")]),
        "Workbook row has confirmations without reviewer_action",
    )
    add_check(rows, generated_at, 12, "workbook_context", "partial blank action rejected", passed, observed, evidence)

    passed, observed, evidence = expect_failure(
        lambda: validate_context([workbook_row(decision_fingerprint="stale_fixture_fingerprint")]),
        "Workbook decision_fingerprint is stale",
    )
    add_check(rows, generated_at, 13, "workbook_context", "stale workbook fingerprint rejected", passed, observed, evidence)

    blank_rows = extractor.extract_patch_rows([workbook_row()], include_blank=False)
    add_check(
        rows,
        generated_at,
        14,
        "patch_extraction",
        "blank workbook extracts zero filled patch rows",
        len(blank_rows) == 0,
        "extracted_rows=" + str(len(blank_rows)),
        {"include_blank": False},
    )

    filled_workbook = workbook_row(**valid_patch())
    extracted = extractor.extract_patch_rows([filled_workbook], include_blank=False)
    passed, observed, evidence = expect_success(lambda: validate_patch_rows(extracted))
    add_check(
        rows,
        generated_at,
        15,
        "patch_extraction",
        "filled synthetic workbook extracts valid patch row",
        passed and len(extracted) == 1,
        observed + "; extracted_rows=" + str(len(extracted)),
        {"extracted_rows": len(extracted), "validated_rows": len(evidence[0]) if passed else 0},
    )

    included_blank = extractor.extract_patch_rows([workbook_row()], include_blank=True)
    add_check(
        rows,
        generated_at,
        16,
        "patch_extraction",
        "include_blank preserves blank patch shape",
        len(included_blank) == 1 and list(included_blank[0]) == patch_helper.PATCH_FIELDS,
        "extracted_rows=" + str(len(included_blank)),
        {"include_blank": True, "patch_fields": list(included_blank[0]) if included_blank else []},
    )

    return rows


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Patch Helper Fixture Verification",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Patch Helper Fixture Verification",
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
            "| {execution_order} | {helper_surface} | {check_name} | {check_status} | {observed_behavior} |".format(
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
        "fixture_check_rows": len(rows),
        "pass_rows": pass_rows,
        "fail_rows": fail_rows,
        "synthetic_fixture_only": True,
        "real_vanderbilt_rows_used": 0,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "accepted_person_rows": 0,
        "apply_executed": False,
        "gbrain_approval_status": "approved_non_mutating_vanderbilt_patch_helper_fixture_verification_increment",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["fixture_check_rows", "pass_rows", "fail_rows", "rowset_sha256"]}, sort_keys=True))
    if fail_rows:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
