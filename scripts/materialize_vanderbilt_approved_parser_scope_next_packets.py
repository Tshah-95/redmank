#!/usr/bin/env python3
"""Materialize approved non-mutating Vanderbilt parser/scope next-packet lanes."""

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

SOURCE_JSON = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_approved_parser_scope_next_packets.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_approved_parser_scope_next_packets.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_approved_parser_scope_next_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-approved-parser-scope-next-packets-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3"
APPROVAL_LINE = (
    "APPROVE vanderbilt_targeted_route_observation_parser_scope_packet_approved PACKET_ROWS 20 "
    "PARSER_BUILD_REVIEW_ROWS 15 SCOPE_DISPOSITION_ROWS 3 GENERAL_SURGERY_ROWS 1 RECOURSE_ROWS 1 "
    "ROWSET_SHA256 9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3"
)

MUTATION_POLICY = (
    "Approved non-mutating Vanderbilt parser/scope next-packet lane. The exact GBrain approval allows only "
    "source-specific parser-build review packets, linked-route scope-disposition packets, a General Surgery "
    "rendered-review packet, and route retry/recourse handling. It does not approve parser output as people, "
    "person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, "
    "unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse."
)

FIELDS = [
    "next_packet_key",
    "source_packet_key",
    "program_key",
    "program_name",
    "fetch_url",
    "final_url",
    "http_status",
    "approval_request_lane",
    "approved_next_artifact_lane",
    "next_packet_status",
    "non_mutating_parser_build_review_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "required_operator_action",
    "required_evidence_boundary",
    "content_sha256",
    "visible_text_sha256",
    "source_route_signal_json",
    "gbrain_approval_line",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_packet_key",
    "program_key",
    "program_name",
    "fetch_url",
    "final_url",
    "http_status",
    "approval_request_lane",
    "approved_next_artifact_lane",
    "next_packet_status",
    "non_mutating_parser_build_review_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "required_operator_action",
    "required_evidence_boundary",
    "content_sha256",
    "visible_text_sha256",
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


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt parser/scope packet summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "packet_rows": summary.get("packet_rows") == 20,
        "approval_status": summary.get("gbrain_approval_status") == "approved_exact_non_mutating_next_artifact_lane",
        "approval_line": summary.get("required_approval_line") == APPROVAL_LINE,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected Vanderbilt approved parser/scope packet boundary: {checks}")
    return summary


def classify(source: dict[str, object]) -> tuple[str, str, str, str]:
    lane = str(source.get("approval_request_lane") or "")
    if lane == "exact_parser_build_review":
        return (
            "source_specific_parser_build_review_packet",
            "approved_non_mutating_parser_build_review_packet_ready",
            "Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people.",
            "Route metadata, hashes, coarse signals, parser selectors/patterns, candidate-only extraction counts, and explicit no-ingestion boundary.",
        )
    if lane == "linked_route_scope_disposition_review":
        return (
            "linked_route_scope_disposition_packet",
            "approved_non_mutating_scope_disposition_packet_ready",
            "Classify shared or ambiguous linked-route evidence as same-program parser candidate, context, or recourse.",
            "Route metadata, hashes, coarse signals, program-scope rationale, and explicit no-url-rewrite/no-denominator-closure boundary.",
        )
    if lane == "rendered_general_surgery_parser_scope_review":
        return (
            "general_surgery_rendered_parser_scope_packet",
            "approved_non_mutating_general_surgery_rendered_review_packet_ready",
            "Run rendered/DOM review for General Surgery current-residents evidence before parser-build or recourse.",
            "Rendered observation metadata, hashes, current-resident signal rationale, and explicit no-ingestion boundary.",
        )
    return (
        "route_retry_or_recourse_packet",
        "approved_non_mutating_route_recourse_packet_ready",
        "Retry or replace the failed official route and carry recourse evidence without parser acceptance.",
        "HTTP status/final URL evidence, retry target, source-discovery recourse, and explicit no-parser-acceptance boundary.",
    )


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("next_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Approved Parser Scope Next Packets",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Approved Parser Scope Next Packets",
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
        "## Next Packet Rows",
        "",
        "| program | approved lane | status | fetch url | required action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {program_name} | {approved_next_artifact_lane} | {next_packet_status} | {fetch_url} | {required_operator_action} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected Vanderbilt route parser/scope packet JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        artifact_lane, status, action, evidence_boundary = classify(source)
        parser_build_allowed = artifact_lane == "source_specific_parser_build_review_packet"
        rows.append(
            {
                "next_packet_key": stable_key("vanderbilt_approved_parser_scope_next", source.get("packet_key"), artifact_lane),
                "source_packet_key": source.get("packet_key"),
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "fetch_url": source.get("fetch_url"),
                "final_url": source.get("final_url"),
                "http_status": source.get("http_status"),
                "approval_request_lane": source.get("approval_request_lane"),
                "approved_next_artifact_lane": artifact_lane,
                "next_packet_status": status,
                "non_mutating_parser_build_review_allowed": "true" if parser_build_allowed else "false",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "required_operator_action": action,
                "required_evidence_boundary": evidence_boundary,
                "content_sha256": source.get("content_sha256"),
                "visible_text_sha256": source.get("visible_text_sha256"),
                "source_route_signal_json": source.get("route_signal_json"),
                "gbrain_approval_line": APPROVAL_LINE,
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (str(item["approved_next_artifact_lane"]), str(item["program_name"]), str(item["fetch_url"])))
    by_lane = Counter(str(row["approved_next_artifact_lane"]) for row in rows)
    by_status = Counter(str(row["next_packet_status"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_parser_scope_packet": str(SOURCE_JSON.relative_to(ROOT)),
        "source_parser_scope_packet_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_parser_scope_packet_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_parser_scope_packet_rows": source_summary.get("packet_rows"),
        "gbrain_approval_line": APPROVAL_LINE,
        "next_packet_rows": len(rows),
        "by_approved_next_artifact_lane": dict(sorted(by_lane.items())),
        "by_next_packet_status": dict(sorted(by_status.items())),
        "mutation_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["next_packet_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
