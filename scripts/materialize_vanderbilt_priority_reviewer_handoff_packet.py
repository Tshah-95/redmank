#!/usr/bin/env python3
"""Materialize the public-safe Vanderbilt priority reviewer handoff packet."""

from __future__ import annotations

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
RESEARCH = ROOT / "artifacts" / "research"

PRIORITY_INSTRUCTION_CSV = ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet.csv"
PRIORITY_INSTRUCTION_JSON = ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet.json"
PRIORITY_INSTRUCTION_SUMMARY = ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet_summary.json"
PATCH_HELPER_FIXTURE_SUMMARY = ARTIFACTS / "vanderbilt_patch_helper_fixture_verification_summary.json"
SLICE_PRIORITIZATION_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan_summary.json"
BLANK_EXECUTION_VERIFICATION_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification_summary.json"
DECISION_AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-priority-reviewer-handoff-packet-2026-06-09.md"

PRIORITY_INSTRUCTION_ROWSET = "dfe6c7081ac7c3c28ac6e8afcb736a2d16bc8a6cbd8cba1cbc38b420064ddd65"
PATCH_HELPER_FIXTURE_ROWSET = "9d87181804d6ade23ea3bd7fd322cdc7fdeab7b3078aade0921c8d2b2cab2825"
SLICE_PRIORITIZATION_ROWSET = "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c"
BLANK_EXECUTION_VERIFICATION_ROWSET = "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e"
DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
GBRAIN_APPROVAL_LINE = "APPROVE vanderbilt_priority_reviewer_handoff_packet_non_mutating_increment"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt priority reviewer handoff packet. It bundles the General Surgery priority_rank=1 "
    "instruction packet, synthetic patch-helper fixture status, slice command, extract command, dry-run command, "
    "and explicit no-apply boundary for local reviewer execution. It does not fill reviewer decisions, extract "
    "filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, "
    "rewrite URLs, publish raw candidate labels or person URLs, accept enrichment facts, or collapse identities."
)

PROHIBITED_MUTATIONS = [
    "fill_reviewer_decisions_in_repo",
    "extract_filled_patch_in_repo",
    "run_apply",
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
    "filled_reviewer_decision_commit",
    "patch_apply",
    "person_ingestion",
    "denominator_closure",
    "parser_acceptance",
    "scope_closure",
    "url_rewrite",
    "identity_collapse",
]

FIELDS = [
    "handoff_packet_key",
    "priority_rank",
    "execution_order",
    "program_key",
    "program_name",
    "review_queue_lane",
    "handoff_status",
    "instruction_rows_represented",
    "pending_blank_instruction_rows",
    "candidate_source_kind_counts",
    "fixture_check_rows",
    "fixture_pass_rows",
    "fixture_fail_rows",
    "blank_execution_pass_rows",
    "blank_extract_fail_closed_rows",
    "decision_audit_pending_rows",
    "decision_audit_valid_non_mutating_rows",
    "decision_audit_invalid_rows",
    "slice_command",
    "extract_command",
    "patch_dry_run_command",
    "apply_command_allowed",
    "reviewer_handoff_action",
    "success_condition",
    "approval_required_for",
    "prohibited_mutations",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "parser_acceptance_allowed",
    "apply_executed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
    "free_text_note_column_committed",
    "source_priority_instruction_rowset_sha256",
    "source_patch_helper_fixture_rowset_sha256",
    "source_slice_prioritization_rowset_sha256",
    "source_blank_execution_verification_rowset_sha256",
    "source_decision_audit_rowset_sha256",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"handoff_packet_key", "evidence_json", "mutation_policy", "generated_at"}
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


def semicolon(values: list[str]) -> str:
    return "; ".join(values)


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("handoff_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def verify_source_boundary() -> tuple[
    dict[str, object],
    list[dict[str, str]],
    dict[str, object],
    dict[str, object],
    dict[str, object],
    dict[str, object],
]:
    instruction_summary = read_json(PRIORITY_INSTRUCTION_SUMMARY)
    instruction_json = read_json(PRIORITY_INSTRUCTION_JSON)
    fixture_summary = read_json(PATCH_HELPER_FIXTURE_SUMMARY)
    prioritization_summary = read_json(SLICE_PRIORITIZATION_SUMMARY)
    blank_execution_summary = read_json(BLANK_EXECUTION_VERIFICATION_SUMMARY)
    decision_audit_summary = read_json(DECISION_AUDIT_SUMMARY)
    instruction_rows = read_csv_rows(PRIORITY_INSTRUCTION_CSV)

    if not all(
        isinstance(item, dict)
        for item in [
            instruction_summary,
            fixture_summary,
            prioritization_summary,
            blank_execution_summary,
            decision_audit_summary,
        ]
    ):
        raise SystemExit("Expected handoff source summaries to be JSON objects.")
    if not isinstance(instruction_json, list):
        raise SystemExit("Expected priority instruction JSON to be an array.")

    checks = {
        "instruction_rowset": instruction_summary.get("rowset_sha256") == PRIORITY_INSTRUCTION_ROWSET,
        "instruction_boundary": instruction_summary.get("instruction_rows") == 2
        and instruction_summary.get("priority_rank") == "1"
        and instruction_summary.get("execution_order") == "4"
        and instruction_summary.get("program_name") == "General Surgery"
        and instruction_summary.get("pending_blank_instruction_rows") == 2
        and instruction_summary.get("raw_candidate_names_committed") is False
        and instruction_summary.get("raw_person_urls_committed") is False
        and instruction_summary.get("accepted_person_rows") == 0
        and instruction_summary.get("apply_executed") is False
        and instruction_summary.get("mutation_allowed") is False
        and len(instruction_rows) == 2
        and len(instruction_json) == 2,
        "fixture_rowset": fixture_summary.get("rowset_sha256") == PATCH_HELPER_FIXTURE_ROWSET,
        "fixture_boundary": fixture_summary.get("fixture_check_rows") == 16
        and fixture_summary.get("pass_rows") == 16
        and fixture_summary.get("fail_rows") == 0
        and fixture_summary.get("synthetic_fixture_only") is True
        and fixture_summary.get("real_vanderbilt_rows_used") == 0
        and fixture_summary.get("accepted_person_rows") == 0
        and fixture_summary.get("apply_executed") is False
        and fixture_summary.get("mutation_allowed") is False,
        "prioritization_rowset": prioritization_summary.get("rowset_sha256") == SLICE_PRIORITIZATION_ROWSET,
        "prioritization_boundary": prioritization_summary.get("first_priority_execution_order") == "4"
        and prioritization_summary.get("first_priority_program_name") == "General Surgery"
        and prioritization_summary.get("first_priority_workbook_row_count") == 2
        and prioritization_summary.get("accepted_person_rows") == 0
        and prioritization_summary.get("apply_executed") is False
        and prioritization_summary.get("mutation_allowed") is False,
        "blank_execution_rowset": blank_execution_summary.get("rowset_sha256") == BLANK_EXECUTION_VERIFICATION_ROWSET,
        "blank_execution_boundary": blank_execution_summary.get("pass_rows") == 20
        and blank_execution_summary.get("fail_rows") == 0
        and blank_execution_summary.get("blank_extract_fail_closed_rows") == 20
        and blank_execution_summary.get("dry_run_patch_rows_represented") == 0
        and blank_execution_summary.get("apply_executed") is False
        and blank_execution_summary.get("mutation_allowed") is False,
        "decision_audit_rowset": decision_audit_summary.get("rowset_sha256") == DECISION_AUDIT_ROWSET,
        "decision_audit_boundary": decision_audit_summary.get("pending_rows") == 159
        and decision_audit_summary.get("valid_non_mutating_rows") == 0
        and decision_audit_summary.get("invalid_rows") == 0
        and decision_audit_summary.get("accepted_person_rows") == 0
        and decision_audit_summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected handoff source boundary: " + dumps(checks))

    required_blank_fields = [
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
    for row in instruction_rows:
        if any(row.get(field) for field in required_blank_fields):
            raise SystemExit("Priority handoff source instruction rows must remain blank.")

    return (
        instruction_summary,
        instruction_rows,
        fixture_summary,
        prioritization_summary,
        blank_execution_summary,
        decision_audit_summary,
    )


def validate_no_public_leak(rows: list[dict[str, object]]) -> None:
    for row in rows:
        text = dumps(row)
        if URL_RE.search(text):
            raise SystemExit("Priority handoff packet contains URL-like text.")
        if "reviewer_note" in text:
            raise SystemExit("Priority handoff packet must not contain reviewer_note text.")


def build_rows(generated_at: str) -> list[dict[str, object]]:
    (
        instruction_summary,
        instruction_rows,
        fixture_summary,
        prioritization_summary,
        blank_execution_summary,
        decision_audit_summary,
    ) = verify_source_boundary()
    by_kind = Counter(row.get("candidate_source_kind", "") for row in instruction_rows)
    first = instruction_rows[0]
    slice_command = first.get("slice_command", "")
    extract_command = first.get("extract_command", "")
    patch_dry_run_command = first.get("patch_dry_run_command", "")
    if not (slice_command and extract_command and patch_dry_run_command):
        raise SystemExit("Priority handoff requires slice, extract, and dry-run commands.")

    rows = [
        {
            "handoff_packet_key": stable_key(
                "vanderbilt_priority_reviewer_handoff",
                instruction_summary.get("priority_rank"),
                instruction_summary.get("execution_order"),
                PRIORITY_INSTRUCTION_ROWSET,
            ),
            "priority_rank": instruction_summary.get("priority_rank", ""),
            "execution_order": instruction_summary.get("execution_order", ""),
            "program_key": first.get("program_key", ""),
            "program_name": instruction_summary.get("program_name", ""),
            "review_queue_lane": instruction_summary.get("review_queue_lane", ""),
            "handoff_status": "ready_for_local_reviewer_handoff_execution",
            "instruction_rows_represented": len(instruction_rows),
            "pending_blank_instruction_rows": instruction_summary.get("pending_blank_instruction_rows", 0),
            "candidate_source_kind_counts": dumps(dict(sorted(by_kind.items()))),
            "fixture_check_rows": fixture_summary.get("fixture_check_rows", 0),
            "fixture_pass_rows": fixture_summary.get("pass_rows", 0),
            "fixture_fail_rows": fixture_summary.get("fail_rows", 0),
            "blank_execution_pass_rows": blank_execution_summary.get("pass_rows", 0),
            "blank_extract_fail_closed_rows": blank_execution_summary.get("blank_extract_fail_closed_rows", 0),
            "decision_audit_pending_rows": decision_audit_summary.get("pending_rows", 0),
            "decision_audit_valid_non_mutating_rows": decision_audit_summary.get("valid_non_mutating_rows", 0),
            "decision_audit_invalid_rows": decision_audit_summary.get("invalid_rows", 0),
            "slice_command": slice_command,
            "extract_command": extract_command,
            "patch_dry_run_command": patch_dry_run_command,
            "apply_command_allowed": "false",
            "reviewer_handoff_action": (
                "Run the slice command locally, fill only the blank action and confirmation fields for the two "
                "General Surgery rows, extract a strict patch, run the dry-run command, and keep apply disabled "
                "until a future exact approval packet exists."
            ),
            "success_condition": (
                "A local dry run reports valid non-mutating rows for this two-row slice while accepted_person_rows "
                "remains 0, invalid_rows remains 0, and apply_executed remains false."
            ),
            "approval_required_for": semicolon(APPROVAL_REQUIRED_FOR),
            "prohibited_mutations": semicolon(PROHIBITED_MUTATIONS),
            "accepted_person_rows": 0,
            "person_ingestion_allowed": "false",
            "denominator_closure_allowed": "false",
            "school_verification_allowed": "false",
            "parser_acceptance_allowed": "false",
            "apply_executed": "false",
            "raw_candidate_names_committed": "false",
            "raw_person_urls_committed": "false",
            "free_text_note_column_committed": "false",
            "source_priority_instruction_rowset_sha256": PRIORITY_INSTRUCTION_ROWSET,
            "source_patch_helper_fixture_rowset_sha256": PATCH_HELPER_FIXTURE_ROWSET,
            "source_slice_prioritization_rowset_sha256": SLICE_PRIORITIZATION_ROWSET,
            "source_blank_execution_verification_rowset_sha256": BLANK_EXECUTION_VERIFICATION_ROWSET,
            "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
            "evidence_json": dumps(
                {
                    "source_instruction_summary": str(PRIORITY_INSTRUCTION_SUMMARY.relative_to(ROOT)),
                    "source_fixture_summary": str(PATCH_HELPER_FIXTURE_SUMMARY.relative_to(ROOT)),
                    "source_prioritization_summary": str(SLICE_PRIORITIZATION_SUMMARY.relative_to(ROOT)),
                    "source_blank_execution_summary": str(BLANK_EXECUTION_VERIFICATION_SUMMARY.relative_to(ROOT)),
                    "source_decision_audit_summary": str(DECISION_AUDIT_SUMMARY.relative_to(ROOT)),
                    "candidate_source_kind_counts": dict(sorted(by_kind.items())),
                    "no_apply_boundary": True,
                    "local_reviewer_slice_only": True,
                }
            ),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
    ]
    validate_no_public_leak(rows)
    return rows


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Priority Reviewer Handoff Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Priority Reviewer Handoff Packet",
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
        "## Handoff Rows",
        "",
        "| priority | execution | program | status | instruction rows | fixture | apply allowed |",
        "| ---: | ---: | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        fixture = f"{row['fixture_pass_rows']}/{row['fixture_check_rows']} pass"
        lines.append(
            (
                "| {priority_rank} | {execution_order} | {program_name} | {handoff_status} | "
                "{instruction_rows_represented} | "
                + fixture
                + " | {apply_command_allowed} |"
            ).format(**row)
        )
    lines.extend(
        [
            "",
            "## Commands",
            "",
            "| command | value |",
            "| --- | --- |",
        ]
    )
    for row in rows:
        lines.append("| slice | `{slice_command}` |".format(**row))
        lines.append("| extract | `{extract_command}` |".format(**row))
        lines.append("| dry run | `{patch_dry_run_command}` |".format(**row))
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows(generated_at)
    row = rows[0]
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "handoff_rows": len(rows),
        "priority_rank": "1",
        "execution_order": "4",
        "program_name": "General Surgery",
        "review_queue_lane": row["review_queue_lane"],
        "handoff_status": row["handoff_status"],
        "instruction_rows_represented": int(row["instruction_rows_represented"]),
        "pending_blank_instruction_rows": int(row["pending_blank_instruction_rows"]),
        "candidate_source_kind_counts": json.loads(str(row["candidate_source_kind_counts"])),
        "fixture_check_rows": int(row["fixture_check_rows"]),
        "fixture_pass_rows": int(row["fixture_pass_rows"]),
        "fixture_fail_rows": int(row["fixture_fail_rows"]),
        "blank_execution_pass_rows": int(row["blank_execution_pass_rows"]),
        "blank_extract_fail_closed_rows": int(row["blank_extract_fail_closed_rows"]),
        "decision_audit_pending_rows": int(row["decision_audit_pending_rows"]),
        "decision_audit_valid_non_mutating_rows": int(row["decision_audit_valid_non_mutating_rows"]),
        "decision_audit_invalid_rows": int(row["decision_audit_invalid_rows"]),
        "slice_command_present": bool(row["slice_command"]),
        "extract_command_present": bool(row["extract_command"]),
        "patch_dry_run_command_present": bool(row["patch_dry_run_command"]),
        "apply_command_allowed": False,
        "free_text_note_column_committed": False,
        "raw_candidate_names_committed": False,
        "raw_person_urls_committed": False,
        "accepted_person_rows": 0,
        "apply_executed": False,
        "source_priority_instruction_rowset_sha256": PRIORITY_INSTRUCTION_ROWSET,
        "source_patch_helper_fixture_rowset_sha256": PATCH_HELPER_FIXTURE_ROWSET,
        "source_slice_prioritization_rowset_sha256": SLICE_PRIORITIZATION_ROWSET,
        "source_blank_execution_verification_rowset_sha256": BLANK_EXECUTION_VERIFICATION_ROWSET,
        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
        "gbrain_approval_status": "approved_non_mutating_vanderbilt_priority_reviewer_handoff_packet_increment",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "parser_acceptance_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["handoff_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
