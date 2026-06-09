#!/usr/bin/env python3
"""Materialize a public-safe index of Vanderbilt reviewer workbook slices."""

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

OPERATOR_CSV = ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.csv"
OPERATOR_SUMMARY = ARTIFACTS / "vanderbilt_public_reviewer_operator_packet_summary.json"
WORKBOOK_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index_summary.json"
OUT_MD = RESEARCH / "vanderbilt-reviewer-decision-patch-workbook-slice-index-2026-06-09.md"

EXPECTED_OPERATOR_PACKET_ROWSET = "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"
EXPECTED_WORKBOOK_ROWSET = "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3"
EXPECTED_SLICE_ROWS = 20
EXPECTED_DECISION_ROWS = 159

MUTATION_POLICY = (
    "Non-mutating Vanderbilt reviewer workbook slice index. It lists one bounded slice command per public reviewer "
    "operator packet and writes slices to /tmp by default. It does not fill reviewer decisions, include reviewer "
    "notes, publish raw candidate names or URLs, approve people, ingest people, close denominators, verify "
    "Vanderbilt as a school, rewrite URLs, accept enrichment facts, or collapse identities."
)

FIELDS = [
    "slice_index_key",
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
    "apply_decisions_command",
    "verification_command",
    "approval_required_for",
    "prohibited_mutations",
    "source_operator_packet_rowset_sha256",
    "source_workbook_rowset_sha256",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
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
    "apply_decisions_command",
    "verification_command",
    "approval_required_for",
    "prohibited_mutations",
    "source_operator_packet_rowset_sha256",
    "source_workbook_rowset_sha256",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
]

PROHIBITED_MUTATIONS = [
    "fill_reviewer_decisions_without_operator_action",
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
        for row in sorted(rows, key=lambda item: str(item.get("slice_index_key", "")))
    ]
    return sha256_text(dumps(material))


def verify_no_public_leaks(rows: list[dict[str, object]]) -> None:
    text = dumps(rows)
    if URL_RE.search(text):
        raise SystemExit("Slice index rows contain URL-like text.")
    if "reviewer_note" in text:
        raise SystemExit("Slice index rows must not contain reviewer_note text.")


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Reviewer Decision Patch Workbook Slice Index",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Reviewer Decision Patch Workbook Slice Index",
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
        "## Slices",
        "",
        "| order | program | lane | rows | slice command |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {execution_order} | {program_name} | {review_queue_lane} | {workbook_row_count} | `{slice_command}` |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    operator_summary = read_json(OPERATOR_SUMMARY)
    workbook_summary = read_json(WORKBOOK_SUMMARY)
    if not isinstance(operator_summary, dict) or not isinstance(workbook_summary, dict):
        raise SystemExit("Expected Vanderbilt operator and workbook summary JSON objects.")
    source_checks = {
        "operator_rowset": operator_summary.get("rowset_sha256") == EXPECTED_OPERATOR_PACKET_ROWSET,
        "operator_rows": operator_summary.get("operator_packet_rows") == EXPECTED_SLICE_ROWS,
        "operator_decision_rows": operator_summary.get("decision_row_count") == EXPECTED_DECISION_ROWS,
        "workbook_rowset": workbook_summary.get("rowset_sha256") == EXPECTED_WORKBOOK_ROWSET,
        "workbook_rows": workbook_summary.get("workbook_rows") == EXPECTED_DECISION_ROWS,
        "mutation_false": operator_summary.get("mutation_allowed") is False and workbook_summary.get("mutation_allowed") is False,
    }
    if not all(source_checks.values()):
        raise SystemExit("Unexpected Vanderbilt workbook slice-index source boundary: " + dumps(source_checks))

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    by_lane: Counter[str] = Counter()
    for operator in sorted(read_csv_rows(OPERATOR_CSV), key=lambda row: int(row.get("execution_order", 0))):
        execution_order = int(operator.get("execution_order", 0))
        workbook_count = int(operator.get("decision_row_count", 0))
        slice_output = f"/tmp/vanderbilt_reviewer_workbook_order_{execution_order}.csv"
        patch_output = f"/tmp/vanderbilt_reviewer_patch_order_{execution_order}.csv"
        slice_command = (
            "python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py "
            f"--execution-order {execution_order} --output {slice_output}"
        )
        extract_command = (
            "python3 scripts/extract_vanderbilt_reviewer_decision_patch.py "
            f"--workbook {slice_output} --output {patch_output}"
        )
        patch_dry_run_command = f"python3 scripts/apply_vanderbilt_reviewer_decision_patch.py --patch {patch_output}"
        by_lane[operator.get("review_queue_lane", "")] += 1
        rows.append(
            {
                "slice_index_key": stable_key(
                    "vanderbilt_reviewer_workbook_slice_index",
                    operator.get("operator_packet_key", ""),
                    EXPECTED_WORKBOOK_ROWSET,
                ),
                "execution_order": execution_order,
                "operator_packet_key": operator.get("operator_packet_key", ""),
                "review_queue_lane": operator.get("review_queue_lane", ""),
                "program_key": operator.get("program_key", ""),
                "program_name": operator.get("program_name", ""),
                "workbook_row_count": workbook_count,
                "slice_output_path": slice_output,
                "patch_output_path": patch_output,
                "slice_command": slice_command,
                "extract_command": extract_command,
                "patch_dry_run_command": patch_dry_run_command,
                "apply_decisions_command": patch_dry_run_command + " --apply",
                "verification_command": (
                    "python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py && "
                    "python3 scripts/materialize_vanderbilt_candidate_review_batch_packets.py && "
                    "python3 scripts/materialize_vanderbilt_public_reviewer_operator_packets.py && "
                    "python3 scripts/materialize_vanderbilt_reviewer_decision_patch_workbook.py"
                ),
                "approval_required_for": (
                    "accepted_person_rows; person_ingestion; denominator_closure; parser_acceptance; "
                    "scope_closure; url_rewrite; enrichment_acceptance; identity_collapse"
                ),
                "prohibited_mutations": "; ".join(PROHIBITED_MUTATIONS),
                "source_operator_packet_rowset_sha256": EXPECTED_OPERATOR_PACKET_ROWSET,
                "source_workbook_rowset_sha256": EXPECTED_WORKBOOK_ROWSET,
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "raw_candidate_names_committed": "false",
                "raw_person_urls_committed": "false",
                "evidence_json": dumps(
                    {
                        "operator_packet_key": operator.get("operator_packet_key", ""),
                        "decision_row_count": workbook_count,
                        "slice_output_policy": "tmp_only_default",
                        "raw_candidate_names_committed": False,
                        "raw_person_urls_committed": False,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    verify_no_public_leaks(rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_operator_packet_summary": str(OPERATOR_SUMMARY.relative_to(ROOT)),
        "source_operator_packet_rowset_sha256": EXPECTED_OPERATOR_PACKET_ROWSET,
        "source_workbook_summary": str(WORKBOOK_SUMMARY.relative_to(ROOT)),
        "source_workbook_rowset_sha256": EXPECTED_WORKBOOK_ROWSET,
        "slice_index_rows": len(rows),
        "workbook_rows_represented": sum(int(row["workbook_row_count"]) for row in rows),
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "slice_outputs_default_tmp_only": True,
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
    if len(rows) != EXPECTED_SLICE_ROWS or summary["workbook_rows_represented"] != EXPECTED_DECISION_ROWS:
        raise SystemExit("Vanderbilt workbook slice index failed completeness checks.")

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["slice_index_rows", "workbook_rows_represented", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
