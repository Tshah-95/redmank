#!/usr/bin/env python3
"""Materialize a public-safe Vanderbilt priority reviewer instruction packet."""

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

PRIORITIZATION_CSV = ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan.csv"
PRIORITIZATION_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan_summary.json"
WORKBOOK_CSV = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.csv"
WORKBOOK_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_summary.json"
DECISION_AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-priority-reviewer-instruction-packet-2026-06-09.md"

PRIORITIZATION_ROWSET = "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c"
WORKBOOK_ROWSET = "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3"
DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
GBRAIN_APPROVAL_LINE = "APPROVE vanderbilt_priority_1_reviewer_instruction_packet_non_mutating_increment"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt priority reviewer instruction packet. It materializes the priority_rank=1 General "
    "Surgery reviewer slice scaffold from public-safe hashes, keys, allowed actions, required confirmations, and "
    "helper commands only. It does not fill reviewer decisions, include reviewer notes, publish raw candidate labels "
    "or URLs, extract filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt "
    "as a school, rewrite URLs, accept enrichment facts, or collapse identities."
)

PROHIBITED_MUTATIONS = [
    "fill_reviewer_decisions",
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
    "instruction_packet_key",
    "priority_rank",
    "execution_order",
    "instruction_row_order",
    "assignment_band",
    "review_queue_lane",
    "program_key",
    "program_name",
    "workbook_row_key",
    "manual_decision_row_key",
    "decision_scaffold_key",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "decision_fingerprint",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "reviewer_action",
    "confirm_decision_fingerprint",
    "confirm_no_person_ingestion",
    "confirm_no_denominator_closure",
    "confirm_no_raw_name_added",
    "confirm_no_url_rewrite",
    "confirm_candidate_fingerprint_only",
    "confirm_scope_metadata_only",
    "confirm_recourse_only",
    "instruction_status",
    "slice_command",
    "extract_command",
    "patch_dry_run_command",
    "recommended_reviewer_action",
    "success_condition",
    "approval_required_for",
    "prohibited_mutations",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "apply_executed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
    "source_prioritization_rowset_sha256",
    "source_workbook_rowset_sha256",
    "source_decision_audit_rowset_sha256",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"instruction_packet_key", "evidence_json", "mutation_policy", "generated_at"}
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
        for row in sorted(rows, key=lambda item: str(item.get("instruction_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def as_int(value: object) -> int:
    return int(str(value or "0"))


def semicolon(values: list[str]) -> str:
    return "; ".join(values)


def verify_source_boundary() -> tuple[dict[str, str], list[dict[str, str]]]:
    prioritization_summary = read_json(PRIORITIZATION_SUMMARY)
    workbook_summary = read_json(WORKBOOK_SUMMARY)
    decision_audit_summary = read_json(DECISION_AUDIT_SUMMARY)
    if not all(isinstance(item, dict) for item in [prioritization_summary, workbook_summary, decision_audit_summary]):
        raise SystemExit("Expected priority instruction source summaries to be JSON objects.")

    checks = {
        "prioritization": prioritization_summary.get("rowset_sha256") == PRIORITIZATION_ROWSET
        and prioritization_summary.get("prioritization_rows") == 20
        and prioritization_summary.get("first_priority_execution_order") == "4"
        and prioritization_summary.get("first_priority_program_name") == "General Surgery"
        and prioritization_summary.get("first_priority_workbook_row_count") == 2
        and prioritization_summary.get("mutation_allowed") is False
        and prioritization_summary.get("person_ingestion_allowed") is False,
        "workbook": workbook_summary.get("rowset_sha256") == WORKBOOK_ROWSET
        and workbook_summary.get("workbook_rows") == 159
        and workbook_summary.get("blank_action_rows") == 159
        and workbook_summary.get("valid_non_mutating_rows") == 0
        and workbook_summary.get("raw_candidate_names_committed") is False
        and workbook_summary.get("raw_person_urls_committed") is False
        and workbook_summary.get("mutation_allowed") is False,
        "decision_audit": decision_audit_summary.get("rowset_sha256") == DECISION_AUDIT_ROWSET
        and decision_audit_summary.get("pending_rows") == 159
        and decision_audit_summary.get("valid_non_mutating_rows") == 0
        and decision_audit_summary.get("invalid_rows") == 0
        and decision_audit_summary.get("accepted_person_rows") == 0
        and decision_audit_summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected priority instruction source boundary: " + dumps(checks))

    priority_rows = [row for row in read_csv_rows(PRIORITIZATION_CSV) if row.get("priority_rank") == "1"]
    if len(priority_rows) != 1:
        raise SystemExit("Expected exactly one priority_rank=1 row.")
    priority = priority_rows[0]
    if (
        priority.get("execution_order") != "4"
        or priority.get("program_name") != "General Surgery"
        or priority.get("workbook_row_count") != "2"
    ):
        raise SystemExit("Unexpected priority_rank=1 selector: " + dumps(priority))
    workbook_rows = [
        row for row in read_csv_rows(WORKBOOK_CSV) if row.get("operator_execution_order") == priority["execution_order"]
    ]
    if len(workbook_rows) != 2:
        raise SystemExit("Expected exactly two priority workbook rows.")
    return priority, workbook_rows


def validate_no_public_leak(rows: list[dict[str, object]]) -> None:
    for row in rows:
        text = dumps(row)
        if URL_RE.search(text):
            raise SystemExit("Priority instruction packet contains URL-like text.")
        if "reviewer_note" in text:
            raise SystemExit("Priority instruction packet must not contain reviewer_note text.")


def build_rows(generated_at: str) -> list[dict[str, object]]:
    priority, workbook_rows = verify_source_boundary()
    rows: list[dict[str, object]] = []
    for index, workbook in enumerate(workbook_rows, start=1):
        rows.append(
            {
                "instruction_packet_key": stable_key(
                    "vanderbilt_priority_reviewer_instruction",
                    priority.get("priority_rank"),
                    workbook.get("manual_decision_row_key"),
                    PRIORITIZATION_ROWSET,
                ),
                "priority_rank": priority.get("priority_rank", ""),
                "execution_order": priority.get("execution_order", ""),
                "instruction_row_order": index,
                "assignment_band": priority.get("assignment_band", ""),
                "review_queue_lane": priority.get("review_queue_lane", ""),
                "program_key": priority.get("program_key", ""),
                "program_name": priority.get("program_name", ""),
                "workbook_row_key": workbook.get("workbook_row_key", ""),
                "manual_decision_row_key": workbook.get("manual_decision_row_key", ""),
                "decision_scaffold_key": workbook.get("decision_scaffold_key", ""),
                "candidate_fingerprint_sha256": workbook.get("candidate_fingerprint_sha256", ""),
                "candidate_source_kind": workbook.get("candidate_source_kind", ""),
                "decision_fingerprint": workbook.get("decision_fingerprint", ""),
                "allowed_reviewer_actions": workbook.get("allowed_reviewer_actions", ""),
                "required_confirmation_fields": workbook.get("required_confirmation_fields", ""),
                "reviewer_action": "",
                "confirm_decision_fingerprint": "",
                "confirm_no_person_ingestion": "",
                "confirm_no_denominator_closure": "",
                "confirm_no_raw_name_added": "",
                "confirm_no_url_rewrite": "",
                "confirm_candidate_fingerprint_only": "",
                "confirm_scope_metadata_only": "",
                "confirm_recourse_only": "",
                "instruction_status": "pending_blank_reviewer_instruction",
                "slice_command": priority.get("slice_command", ""),
                "extract_command": priority.get("extract_command", ""),
                "patch_dry_run_command": priority.get("patch_dry_run_command", ""),
                "recommended_reviewer_action": (
                    "Fill only reviewer_action plus the required confirmation fields for this row, then extract a "
                    "strict patch and run the patch helper without --apply."
                ),
                "success_condition": (
                    "Dry-run patch validation reports this row as valid_non_mutating while accepted_person_rows "
                    "remains 0 and apply_executed remains false."
                ),
                "approval_required_for": semicolon(APPROVAL_REQUIRED_FOR),
                "prohibited_mutations": semicolon(PROHIBITED_MUTATIONS),
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "apply_executed": "false",
                "raw_candidate_names_committed": "false",
                "raw_person_urls_committed": "false",
                "source_prioritization_rowset_sha256": PRIORITIZATION_ROWSET,
                "source_workbook_rowset_sha256": WORKBOOK_ROWSET,
                "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
                "evidence_json": dumps(
                    {
                        "candidate_source_kind": workbook.get("candidate_source_kind"),
                        "operator_packet_key": workbook.get("operator_packet_key"),
                        "source_batch_packet_key": workbook.get("source_batch_packet_key"),
                        "priority_assignment_band": priority.get("assignment_band"),
                        "blank_decision_fields": [
                            "reviewer_action",
                            "confirm_decision_fingerprint",
                            "confirm_no_person_ingestion",
                            "confirm_no_denominator_closure",
                            "confirm_no_raw_name_added",
                            "confirm_no_url_rewrite",
                            "confirm_candidate_fingerprint_only",
                            "confirm_scope_metadata_only",
                            "confirm_recourse_only",
                        ],
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )
    validate_no_public_leak(rows)
    return rows


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Priority Reviewer Instruction Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Priority Reviewer Instruction Packet",
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
        "## Instruction Rows",
        "",
        "| order | priority | execution | lane | program | source kind | status |",
        "| ---: | ---: | ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {instruction_row_order} | {priority_rank} | {execution_order} | {review_queue_lane} | {program_name} | {candidate_source_kind} | {instruction_status} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows(generated_at)
    by_status = Counter(str(row["instruction_status"]) for row in rows)
    by_kind = Counter(str(row["candidate_source_kind"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "instruction_rows": len(rows),
        "priority_rank": "1",
        "execution_order": "4",
        "program_name": "General Surgery",
        "review_queue_lane": "candidate_fingerprint_review",
        "pending_blank_instruction_rows": by_status.get("pending_blank_reviewer_instruction", 0),
        "by_candidate_source_kind": dict(sorted(by_kind.items())),
        "free_text_note_column_committed": False,
        "raw_candidate_names_committed": False,
        "raw_person_urls_committed": False,
        "accepted_person_rows": 0,
        "apply_executed": False,
        "source_prioritization_rowset_sha256": PRIORITIZATION_ROWSET,
        "source_workbook_rowset_sha256": WORKBOOK_ROWSET,
        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
        "gbrain_approval_status": "approved_non_mutating_vanderbilt_priority_1_reviewer_instruction_packet_increment",
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
    print(json.dumps({key: summary[key] for key in ["instruction_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
