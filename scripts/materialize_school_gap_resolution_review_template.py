#!/usr/bin/env python3
"""Materialize a public-safe review template for school gap-resolution packets."""

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

PACKET_CSV = ARTIFACTS / "school_gap_resolution_batch_packets.csv"
PACKET_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_packet_summary.json"
SLICE_INDEX_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_slice_index_summary.json"

OUT_CSV = ARTIFACTS / "school_gap_resolution_review_template.csv"
OUT_JSON = ARTIFACTS / "school_gap_resolution_review_template.json"
OUT_SUMMARY = ARTIFACTS / "school_gap_resolution_review_template_summary.json"
OUT_MD = RESEARCH / "school-gap-resolution-review-template-2026-06-09.md"

EXPECTED_PACKET_ROWS = 113
EXPECTED_BATCH_ROWS = 21
EXPECTED_SLICE_INDEX_ROWSET = "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75"

ALLOWED_REVIEW_ACTIONS = [
    "candidate_official_source_for_later_probe",
    "source_discovery_query_only",
    "route_inspection_needed",
    "rendered_or_manual_review_needed",
    "scope_disposition_packet_needed",
    "no_public_roster_closure_packet_needed",
    "defer_needs_more_context",
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

MUTATION_POLICY = (
    "Non-mutating school gap-resolution review template. It gives public contributors blank fields for source-"
    "discovery planning and packet-prep notes over committed Vanderbilt gap packets. It does not fetch pages, accept "
    "candidate URLs as official truth, ingest people, close denominators, verify schools, rewrite URLs, accept "
    "enrichment facts, or collapse identities."
)

FIELDS = [
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
    for field in FIELDS
    if field not in {"review_template_key", "evidence_json", "mutation_policy", "generated_at"}
]
BLANK_FIELDS = [
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
        for row in sorted(rows, key=lambda item: str(item.get("review_template_key", "")))
    ]
    return sha256_text(dumps(material))


def private_marker_hits(rows: list[dict[str, object]]) -> list[str]:
    text = dumps(rows)
    return [marker for marker in PRIVATE_PATH_MARKERS if marker in text]


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: School Gap Resolution Review Template",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# School Gap Resolution Review Template",
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
        "## Template Rows",
        "",
        "| order | program | lane | status | action |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {execution_order} | {program_name} | {next_operator_lane} | {template_row_status} | {proposed_non_mutating_review_action} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    packet_summary = read_json(PACKET_SUMMARY)
    slice_summary = read_json(SLICE_INDEX_SUMMARY)
    if not isinstance(packet_summary, dict) or not isinstance(slice_summary, dict):
        raise SystemExit("Expected gap packet and slice-index summary JSON objects.")
    source_checks = {
        "packet_rows": packet_summary.get("rows") == EXPECTED_PACKET_ROWS,
        "packet_batch_rows": packet_summary.get("batch_rows") == EXPECTED_BATCH_ROWS,
        "packet_mutation_false": packet_summary.get("mutation_allowed") is False,
        "slice_index_rowset": slice_summary.get("rowset_sha256") == EXPECTED_SLICE_INDEX_ROWSET,
        "slice_index_rows": slice_summary.get("slice_index_rows") == EXPECTED_BATCH_ROWS,
        "slice_gap_rows": slice_summary.get("gap_rows_represented") == EXPECTED_PACKET_ROWS,
        "slice_mutation_false": slice_summary.get("mutation_allowed") is False,
    }
    if not all(source_checks.values()):
        raise SystemExit("Unexpected school gap review template source boundary: " + dumps(source_checks))

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    by_lane: Counter[str] = Counter()
    by_status: Counter[str] = Counter()
    for packet in sorted(
        read_csv_rows(PACKET_CSV),
        key=lambda row: (int(row.get("execution_order", 0)), int(row.get("batch_packet_order", 0))),
    ):
        by_lane[packet.get("next_operator_lane", "")] += 1
        by_status[packet.get("packet_status", "")] += 1
        rows.append(
            {
                "review_template_key": stable_key(
                    "school_gap_resolution_review_template",
                    packet.get("school_gap_resolution_batch_packet_key", ""),
                    EXPECTED_SLICE_INDEX_ROWSET,
                ),
                "school_gap_resolution_batch_packet_key": packet.get("school_gap_resolution_batch_packet_key", ""),
                "school_gap_resolution_batch_key": packet.get("school_gap_resolution_batch_key", ""),
                "execution_order": packet.get("execution_order", ""),
                "batch_packet_order": packet.get("batch_packet_order", ""),
                "gap_key": packet.get("gap_key", ""),
                "school_name": packet.get("school_name", ""),
                "program_key": packet.get("program_key", ""),
                "program_name": packet.get("program_name", ""),
                "program_type": packet.get("program_type", ""),
                "department_or_group": packet.get("department_or_group", ""),
                "next_operator_lane": packet.get("next_operator_lane", ""),
                "resolution_category": packet.get("resolution_category", ""),
                "packet_status": packet.get("packet_status", ""),
                "support_status": packet.get("support_status", ""),
                "denominator_url": packet.get("denominator_url", ""),
                "best_evidence_url": packet.get("best_evidence_url", ""),
                "best_evidence_title": packet.get("best_evidence_title", ""),
                "best_evidence_status": packet.get("best_evidence_status", ""),
                "recommended_packet_action": packet.get("recommended_packet_action", ""),
                "required_next_evidence": packet.get("required_next_evidence", ""),
                "target_artifact": packet.get("target_artifact", ""),
                "allowed_review_actions": "; ".join(ALLOWED_REVIEW_ACTIONS),
                "proposed_non_mutating_review_action": "",
                "proposed_source_discovery_query": "",
                "proposed_candidate_official_url": "",
                "proposed_evidence_summary": "",
                "proposed_output_artifact": "",
                "confirm_no_person_ingestion": "",
                "confirm_no_denominator_closure": "",
                "confirm_no_school_verification": "",
                "confirm_no_url_rewrite": "",
                "confirm_no_identity_collapse": "",
                "confirm_candidate_evidence_only": "",
                "template_row_status": "blank_pending_non_mutating_review_input",
                "accepted_person_rows": "0",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "private_artifact_paths_committed": "false",
                "evidence_json": dumps(
                    {
                        "source_packet_key": packet.get("school_gap_resolution_batch_packet_key", ""),
                        "source_slice_index_rowset_sha256": EXPECTED_SLICE_INDEX_ROWSET,
                        "blank_template_row": True,
                        "public_urls_may_be_present": True,
                        "private_artifact_paths_committed": False,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    blank_counts = {field: sum(1 for row in rows if not str(row.get(field, "")).strip()) for field in BLANK_FIELDS}
    hits = private_marker_hits(rows)
    if hits:
        raise SystemExit("Review template rows contain private artifact markers: " + ", ".join(hits))
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_packet_summary": str(PACKET_SUMMARY.relative_to(ROOT)),
        "source_slice_index_summary": str(SLICE_INDEX_SUMMARY.relative_to(ROOT)),
        "source_slice_index_rowset_sha256": EXPECTED_SLICE_INDEX_ROWSET,
        "review_template_rows": len(rows),
        "batch_rows_represented": len({row["school_gap_resolution_batch_key"] for row in rows}),
        "blank_action_rows": blank_counts["proposed_non_mutating_review_action"],
        "blank_review_fields": blank_counts,
        "allowed_review_actions": ALLOWED_REVIEW_ACTIONS,
        "by_next_operator_lane": dict(sorted(by_lane.items())),
        "by_packet_status": dict(sorted(by_status.items())),
        "public_urls_may_be_present": True,
        "private_artifact_paths_committed": False,
        "reviewer_note_column_committed": False,
        "valid_non_mutating_review_rows": 0,
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
        len(rows) != EXPECTED_PACKET_ROWS
        or summary["batch_rows_represented"] != EXPECTED_BATCH_ROWS
        or any(value != EXPECTED_PACKET_ROWS for value in blank_counts.values())
    ):
        raise SystemExit("School gap review template failed completeness or blank-field checks.")

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["review_template_rows", "batch_rows_represented", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
