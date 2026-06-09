#!/usr/bin/env python3
"""Bridge Vanderbilt review queues to bounded reviewer execution commands."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

REVIEW_QUEUE_BRIDGE_CSV = ARTIFACTS / "school_gap_resolution_review_queue_bridge.csv"
REVIEW_QUEUE_BRIDGE_SUMMARY = ARTIFACTS / "school_gap_resolution_review_queue_bridge_summary.json"
SLICE_INDEX_CSV = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.csv"
SLICE_INDEX_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index_summary.json"
WORKBOOK_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_summary.json"
OPERATOR_SUMMARY = ARTIFACTS / "vanderbilt_public_reviewer_operator_packet_summary.json"
DECISION_AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge_summary.json"
OUT_MD = RESEARCH / "vanderbilt-reviewer-execution-readiness-bridge-2026-06-09.md"

REVIEW_QUEUE_BRIDGE_ROWSET = "46c2b215f28819df10913fa35f7dff6e7f4afc4ec6c3598e7432088c3f34e10d"
SLICE_INDEX_ROWSET = "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4"
WORKBOOK_ROWSET = "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3"
OPERATOR_PACKET_ROWSET = "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"
DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"

MUTATION_POLICY = (
    "Non-mutating bridge from Vanderbilt pending review queues to bounded reviewer execution commands. It verifies "
    "that each review-queue bridge program is represented by /tmp-only slice, extraction, dry-run, and explicit "
    "apply commands from the public slice index. It does not run commands, fill reviewer decisions, apply patches, "
    "accept people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, "
    "publish raw candidate labels or URLs, or collapse identities."
)

FIELDS = [
    "execution_readiness_bridge_key",
    "program_key",
    "program_name",
    "review_queue_bridge_status",
    "review_queue_rows",
    "pending_decision_rows",
    "slice_index_rows",
    "workbook_rows",
    "slice_output_paths_tmp_only",
    "patch_output_paths_tmp_only",
    "extract_commands_present",
    "patch_dry_run_commands_present",
    "apply_commands_present",
    "execution_readiness_status",
    "next_required_action",
    "accepted_person_rows",
    "valid_non_mutating_decision_rows",
    "invalid_decision_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "source_review_queue_bridge_rowset_sha256",
    "source_slice_index_rowset_sha256",
    "source_workbook_rowset_sha256",
    "source_operator_packet_rowset_sha256",
    "source_decision_audit_rowset_sha256",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"execution_readiness_bridge_key", "evidence_json", "mutation_policy", "generated_at"}
]

PROHIBITED_MUTATIONS = [
    "fill_reviewer_decisions_without_operator_action",
    "apply_reviewer_patch_without_explicit_apply",
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
        for row in sorted(rows, key=lambda item: str(item.get("execution_readiness_bridge_key", "")))
    ]
    return sha256_text(dumps(material))


def verify_boundaries() -> None:
    review_queue_bridge = read_json(REVIEW_QUEUE_BRIDGE_SUMMARY)
    slice_index = read_json(SLICE_INDEX_SUMMARY)
    workbook = read_json(WORKBOOK_SUMMARY)
    operator = read_json(OPERATOR_SUMMARY)
    decision_audit = read_json(DECISION_AUDIT_SUMMARY)
    if not all(isinstance(item, dict) for item in [review_queue_bridge, slice_index, workbook, operator, decision_audit]):
        raise SystemExit("Expected execution-readiness source summaries to be JSON objects.")
    checks = {
        "review_queue_bridge": review_queue_bridge.get("rowset_sha256") == REVIEW_QUEUE_BRIDGE_ROWSET
        and review_queue_bridge.get("bridge_rows") == 19
        and review_queue_bridge.get("pending_decision_rows_represented") == 159
        and review_queue_bridge.get("valid_non_mutating_decision_rows_represented") == 0
        and review_queue_bridge.get("invalid_decision_rows_represented") == 0
        and review_queue_bridge.get("mutation_allowed") is False
        and review_queue_bridge.get("person_ingestion_allowed") is False,
        "slice_index": slice_index.get("rowset_sha256") == SLICE_INDEX_ROWSET
        and slice_index.get("slice_index_rows") == 20
        and slice_index.get("workbook_rows_represented") == 159
        and slice_index.get("slice_outputs_default_tmp_only") is True
        and slice_index.get("mutation_allowed") is False
        and slice_index.get("person_ingestion_allowed") is False,
        "workbook": workbook.get("rowset_sha256") == WORKBOOK_ROWSET
        and workbook.get("workbook_rows") == 159
        and workbook.get("blank_action_rows") == 159
        and workbook.get("valid_non_mutating_rows") == 0
        and workbook.get("helper_patch_extraction_required") is True
        and workbook.get("mutation_allowed") is False,
        "operator": operator.get("rowset_sha256") == OPERATOR_PACKET_ROWSET
        and operator.get("operator_packet_rows") == 20
        and operator.get("decision_row_count") == 159
        and operator.get("valid_non_mutating_decision_rows") == 0
        and operator.get("invalid_decision_rows") == 0
        and operator.get("mutation_allowed") is False,
        "decision_audit": decision_audit.get("rowset_sha256") == DECISION_AUDIT_ROWSET
        and decision_audit.get("audit_rows") == 159
        and decision_audit.get("pending_rows") == 159
        and decision_audit.get("valid_non_mutating_rows") == 0
        and decision_audit.get("invalid_rows") == 0
        and decision_audit.get("accepted_person_rows") == 0,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected execution-readiness source boundary: " + dumps(checks))


def index_by_program(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_program: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_program[row.get("program_key", "")].append(row)
    return dict(by_program)


def tmp_only(values: list[str]) -> bool:
    return bool(values) and all(value.startswith("/tmp/") for value in values)


def command_present(rows: list[dict[str, str]], field: str) -> bool:
    return bool(rows) and all(row.get(field, "").startswith("python3 scripts/") for row in rows)


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Reviewer Execution Readiness Bridge",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Reviewer Execution Readiness Bridge",
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
        "## Program Readiness",
        "",
        "| program | status | slices | workbook rows | pending decisions | next action |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {program_name} | {execution_readiness_status} | {slice_index_rows} | {workbook_rows} | {pending_decision_rows} | {next_required_action} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    verify_boundaries()
    bridge_rows = read_csv_rows(REVIEW_QUEUE_BRIDGE_CSV)
    slice_rows_by_program = index_by_program(read_csv_rows(SLICE_INDEX_CSV))
    if len(bridge_rows) != 19:
        raise SystemExit("Expected exactly 19 review-queue bridge rows.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for bridge in sorted(bridge_rows, key=lambda item: (item.get("program_name", ""), item.get("program_key", ""))):
        program_key = bridge.get("program_key", "")
        slice_rows = sorted(slice_rows_by_program.get(program_key, []), key=lambda item: int(item.get("execution_order", 0)))
        slice_paths = [row.get("slice_output_path", "") for row in slice_rows]
        patch_paths = [row.get("patch_output_path", "") for row in slice_rows]
        slice_tmp = tmp_only(slice_paths)
        patch_tmp = tmp_only(patch_paths)
        extract_present = command_present(slice_rows, "extract_command")
        dry_run_present = command_present(slice_rows, "patch_dry_run_command")
        apply_present = command_present(slice_rows, "apply_decisions_command")
        workbook_rows = sum(int(row.get("workbook_row_count", 0)) for row in slice_rows)
        pending_decision_rows = int(bridge.get("pending_decision_rows", 0))
        review_queue_rows = int(bridge.get("review_queue_rows", 0))
        ready = (
            bridge.get("review_queue_bridge_status") == "pending_reviewer_decisions_ready"
            and pending_decision_rows == workbook_rows
            and review_queue_rows == workbook_rows
            and slice_tmp
            and patch_tmp
            and extract_present
            and dry_run_present
            and apply_present
            and int(bridge.get("valid_non_mutating_decision_rows", 0)) == 0
            and int(bridge.get("invalid_decision_rows", 0)) == 0
        )
        rows.append(
            {
                "execution_readiness_bridge_key": stable_key(
                    "vanderbilt_reviewer_execution_readiness_bridge",
                    bridge.get("review_queue_bridge_key", ""),
                    program_key,
                    SLICE_INDEX_ROWSET,
                ),
                "program_key": program_key,
                "program_name": bridge.get("program_name", ""),
                "review_queue_bridge_status": bridge.get("review_queue_bridge_status", ""),
                "review_queue_rows": review_queue_rows,
                "pending_decision_rows": pending_decision_rows,
                "slice_index_rows": len(slice_rows),
                "workbook_rows": workbook_rows,
                "slice_output_paths_tmp_only": str(slice_tmp).lower(),
                "patch_output_paths_tmp_only": str(patch_tmp).lower(),
                "extract_commands_present": str(extract_present).lower(),
                "patch_dry_run_commands_present": str(dry_run_present).lower(),
                "apply_commands_present": str(apply_present).lower(),
                "execution_readiness_status": "ready_for_bounded_reviewer_slice_execution" if ready else "not_ready",
                "next_required_action": (
                    "choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run"
                    if ready
                    else "repair_review_queue_or_slice_index_mapping"
                ),
                "accepted_person_rows": 0,
                "valid_non_mutating_decision_rows": bridge.get("valid_non_mutating_decision_rows", "0"),
                "invalid_decision_rows": bridge.get("invalid_decision_rows", "0"),
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "source_review_queue_bridge_rowset_sha256": REVIEW_QUEUE_BRIDGE_ROWSET,
                "source_slice_index_rowset_sha256": SLICE_INDEX_ROWSET,
                "source_workbook_rowset_sha256": WORKBOOK_ROWSET,
                "source_operator_packet_rowset_sha256": OPERATOR_PACKET_ROWSET,
                "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
                "evidence_json": dumps(
                    {
                        "slice_index_keys": [row.get("slice_index_key", "") for row in slice_rows],
                        "execution_orders": [row.get("execution_order", "") for row in slice_rows],
                        "review_queue_lanes": sorted({row.get("review_queue_lane", "") for row in slice_rows}),
                        "slice_commands": [row.get("slice_command", "") for row in slice_rows],
                        "extract_commands": [row.get("extract_command", "") for row in slice_rows],
                        "patch_dry_run_commands": [row.get("patch_dry_run_command", "") for row in slice_rows],
                        "apply_commands_are_explicit": True,
                        "prohibited_mutations": PROHIBITED_MUTATIONS,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    text = dumps(rows)
    if URL_RE.search(text):
        raise SystemExit("Execution-readiness bridge rows contain URL-like text.")
    if "reviewer_note" in text:
        raise SystemExit("Execution-readiness bridge rows must not contain reviewer_note text.")

    by_status = Counter(str(row["execution_readiness_status"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_review_queue_bridge_rowset_sha256": REVIEW_QUEUE_BRIDGE_ROWSET,
        "source_slice_index_rowset_sha256": SLICE_INDEX_ROWSET,
        "source_workbook_rowset_sha256": WORKBOOK_ROWSET,
        "source_operator_packet_rowset_sha256": OPERATOR_PACKET_ROWSET,
        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
        "bridge_rows": len(rows),
        "ready_program_rows": by_status.get("ready_for_bounded_reviewer_slice_execution", 0),
        "not_ready_program_rows": by_status.get("not_ready", 0),
        "slice_index_rows_represented": sum(int(row["slice_index_rows"]) for row in rows),
        "workbook_rows_represented": sum(int(row["workbook_rows"]) for row in rows),
        "pending_decision_rows_represented": sum(int(row["pending_decision_rows"]) for row in rows),
        "review_queue_rows_represented": sum(int(row["review_queue_rows"]) for row in rows),
        "valid_non_mutating_decision_rows_represented": sum(int(row["valid_non_mutating_decision_rows"]) for row in rows),
        "invalid_decision_rows_represented": sum(int(row["invalid_decision_rows"]) for row in rows),
        "slice_output_paths_tmp_only": all(row["slice_output_paths_tmp_only"] == "true" for row in rows),
        "patch_output_paths_tmp_only": all(row["patch_output_paths_tmp_only"] == "true" for row in rows),
        "extract_commands_present": all(row["extract_commands_present"] == "true" for row in rows),
        "patch_dry_run_commands_present": all(row["patch_dry_run_commands_present"] == "true" for row in rows),
        "apply_commands_present": all(row["apply_commands_present"] == "true" for row in rows),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    if (
        summary["bridge_rows"] != 19
        or summary["ready_program_rows"] != 19
        or summary["not_ready_program_rows"] != 0
        or summary["slice_index_rows_represented"] != 20
        or summary["workbook_rows_represented"] != 159
        or summary["pending_decision_rows_represented"] != 159
        or summary["review_queue_rows_represented"] != 159
        or summary["valid_non_mutating_decision_rows_represented"] != 0
        or summary["invalid_decision_rows_represented"] != 0
        or summary["slice_output_paths_tmp_only"] is not True
        or summary["patch_output_paths_tmp_only"] is not True
        or summary["extract_commands_present"] is not True
        or summary["patch_dry_run_commands_present"] is not True
        or summary["apply_commands_present"] is not True
    ):
        raise SystemExit("Execution-readiness bridge failed coverage checks: " + dumps(summary))

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["bridge_rows", "ready_program_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
