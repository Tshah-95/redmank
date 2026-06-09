#!/usr/bin/env python3
"""Materialize Vanderbilt parser/scope implementation approval-request packet."""

from __future__ import annotations

import argparse
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

SOURCE_JSON = ARTIFACTS / "vanderbilt_parser_scope_decision_packets.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_parser_scope_decision_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_parser_scope_implementation_approval_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_parser_scope_implementation_approval_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_parser_scope_implementation_approval_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-parser-scope-implementation-approval-packet-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "aa94351eae7a7309d2b760a891f69538d8a8998058fc1ceb24af3d2b918644b8"
APPROVAL_EFFECT = "vanderbilt_parser_scope_candidate_only_implementation_approved"
DENIAL_EFFECT = "vanderbilt_parser_scope_candidate_only_implementation_denied"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt parser/scope implementation approval request. It asks whether candidate-only parser "
    "implementation, scope-disposition recording, General Surgery parser-build review, and Orthopaedic route "
    "recourse work may proceed from the verified decision rowset. It does not approve person ingestion, parser "
    "output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL "
    "rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity "
    "collapse."
)

FIELDS = [
    "approval_packet_key",
    "source_decision_packet_key",
    "program_key",
    "program_name",
    "fetch_url",
    "decision_lane",
    "decision_status",
    "approval_request_lane",
    "approval_scope_requested",
    "implementation_allowed_if_approved",
    "person_ingestion_allowed_if_approved",
    "required_output_boundary_if_approved",
    "next_artifact_if_approved",
    "next_artifact_if_denied",
    "content_sha256",
    "visible_text_sha256",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_decision_packet_key",
    "program_key",
    "program_name",
    "fetch_url",
    "decision_lane",
    "decision_status",
    "approval_request_lane",
    "approval_scope_requested",
    "implementation_allowed_if_approved",
    "person_ingestion_allowed_if_approved",
    "required_output_boundary_if_approved",
    "next_artifact_if_approved",
    "next_artifact_if_denied",
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
        raise SystemExit("Expected Vanderbilt parser/scope decision packet summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "decision_rows": summary.get("decision_rows") == 20,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
        "parser_implementation_false": summary.get("parser_implementation_allowed") is False,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected parser/scope decision boundary: {checks}")
    return summary


def classify(row: dict[str, object]) -> dict[str, str]:
    lane = str(row.get("decision_lane") or "")
    if lane == "parser_family_spec":
        return {
            "approval_request_lane": "candidate_only_parser_implementation_review",
            "approval_scope_requested": "Allow implementation of source-family parsers that emit candidate-only counts, hashes, parser diagnostics, and review queues, not accepted people.",
            "implementation_allowed_if_approved": "candidate_only_parser_code_and_tests",
            "required_output_boundary_if_approved": "No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only.",
            "next_artifact_if_approved": "candidate_only_vanderbilt_parser_implementation_and_review_outputs",
            "next_artifact_if_denied": "retain_parser_family_spec_without_implementation",
        }
    if lane == "linked_route_scope_decision":
        return {
            "approval_request_lane": "linked_route_scope_disposition_acceptance",
            "approval_scope_requested": "Allow non-mutating acceptance of linked-route scope dispositions as routing metadata only.",
            "implementation_allowed_if_approved": "scope_metadata_and_parser_queue_routing",
            "required_output_boundary_if_approved": "No URL rewrite, denominator closure, or person ingestion; scope decisions only route future parser/source-discovery work.",
            "next_artifact_if_approved": "accepted_linked_route_scope_disposition_metadata",
            "next_artifact_if_denied": "retain_scope_decision_packet_pending_approval",
        }
    if lane == "general_surgery_rendered_decision":
        return {
            "approval_request_lane": "general_surgery_candidate_only_parser_review",
            "approval_scope_requested": "Allow General Surgery rendered parser-build review and candidate-only diagnostics.",
            "implementation_allowed_if_approved": "general_surgery_candidate_only_parser_review",
            "required_output_boundary_if_approved": "No accepted General Surgery people; rendered parser evidence must remain counts/hashes/diagnostics.",
            "next_artifact_if_approved": "general_surgery_candidate_only_parser_review_outputs",
            "next_artifact_if_denied": "retain_general_surgery_rendered_decision_pending_approval",
        }
    return {
        "approval_request_lane": "orthopaedic_route_recourse_or_replacement_review",
        "approval_scope_requested": "Allow non-mutating route retry/replacement review for the retired Orthopaedic match route.",
        "implementation_allowed_if_approved": "route_recourse_probe_and_replacement_queue",
        "required_output_boundary_if_approved": "No unresolved-gap closure or URL rewrite; recourse outputs must remain source-discovery evidence.",
        "next_artifact_if_approved": "orthopaedic_route_recourse_or_replacement_packet",
        "next_artifact_if_denied": "retain_orthopaedic_http_error_recourse_pending_approval",
    }


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("approval_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def approval_line(summary: dict[str, object]) -> str:
    return (
        "APPROVE "
        + APPROVAL_EFFECT
        + " APPROVAL_ROWS "
        + str(summary["approval_rows"])
        + " PARSER_IMPLEMENTATION_ROWS "
        + str(summary["by_approval_request_lane"].get("candidate_only_parser_implementation_review", 0))
        + " SCOPE_ACCEPTANCE_ROWS "
        + str(summary["by_approval_request_lane"].get("linked_route_scope_disposition_acceptance", 0))
        + " GENERAL_SURGERY_ROWS "
        + str(summary["by_approval_request_lane"].get("general_surgery_candidate_only_parser_review", 0))
        + " RECOURSE_ROWS "
        + str(summary["by_approval_request_lane"].get("orthopaedic_route_recourse_or_replacement_review", 0))
        + " ROWSET_SHA256 "
        + str(summary["rowset_sha256"])
    )


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Parser Scope Implementation Approval Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Parser Scope Implementation Approval Packet",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Required Approval Line",
        "",
        "`" + str(summary["required_approval_line"]) + "`",
        "",
        "GBrain approval status: `" + str(summary["gbrain_approval_status"]) + "`.",
    ]
    if summary.get("gbrain_denial_line"):
        lines.extend(["", "## Denial Recourse", "", str(summary["gbrain_denial_line"]), "", str(summary["gbrain_denial_recourse"])])
    lines.extend(
        [
            "",
            "## Summary",
            "",
            "```json",
            json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
            "```",
            "",
            "## Approval Rows",
            "",
            "| program | request lane | if approved | output boundary |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {program_name} | {approval_request_lane} | {implementation_allowed_if_approved} | {required_output_boundary_if_approved} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-line", default="", help="Exact GBrain approval line, if returned.")
    parser.add_argument("--denial-line", default="", help="Exact GBrain denial line, if returned.")
    parser.add_argument("--denial-recourse", default="", help="Concise recourse extracted from a GBrain denial.")
    args = parser.parse_args()

    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected Vanderbilt parser/scope decision packet JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        request = classify(source)
        rows.append(
            {
                "approval_packet_key": stable_key("vanderbilt_parser_scope_implementation_approval", source.get("decision_packet_key"), request["approval_request_lane"]),
                "source_decision_packet_key": source.get("decision_packet_key"),
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "fetch_url": source.get("fetch_url"),
                "decision_lane": source.get("decision_lane"),
                "decision_status": source.get("decision_status"),
                "approval_request_lane": request["approval_request_lane"],
                "approval_scope_requested": request["approval_scope_requested"],
                "implementation_allowed_if_approved": request["implementation_allowed_if_approved"],
                "person_ingestion_allowed_if_approved": "false",
                "required_output_boundary_if_approved": request["required_output_boundary_if_approved"],
                "next_artifact_if_approved": request["next_artifact_if_approved"],
                "next_artifact_if_denied": request["next_artifact_if_denied"],
                "content_sha256": source.get("content_sha256"),
                "visible_text_sha256": source.get("visible_text_sha256"),
                "evidence_json": dumps(
                    {
                        "source_decision_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "source_decision_packet_key": source.get("decision_packet_key"),
                        "parser_spec_family": source.get("parser_spec_family"),
                        "scope_decision": source.get("scope_decision"),
                        "recourse_decision": source.get("recourse_decision"),
                        "candidate_entity_count": source.get("candidate_entity_count"),
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (str(item["approval_request_lane"]), str(item["program_name"]), str(item["fetch_url"])))
    by_lane = Counter(str(row["approval_request_lane"]) for row in rows)
    by_next = Counter(str(row["next_artifact_if_approved"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_decision_packets": str(SOURCE_JSON.relative_to(ROOT)),
        "source_decision_packet_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_decision_packet_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_decision_rows": source_summary.get("decision_rows"),
        "approval_rows": len(rows),
        "by_approval_request_lane": dict(sorted(by_lane.items())),
        "by_next_artifact_if_approved": dict(sorted(by_next.items())),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "url_rewrite_allowed": False,
        "gbrain_approval_status": "pending_exact_approval_line",
        "gbrain_approval_effect": APPROVAL_EFFECT,
        "gbrain_denial_effect": DENIAL_EFFECT,
        "gbrain_denial_line": "",
        "gbrain_denial_recourse": "",
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    summary["required_approval_line"] = approval_line(summary)
    if args.approval_line == summary["required_approval_line"]:
        summary["gbrain_approval_status"] = "approved_exact_candidate_only_implementation_scope_recourse"
    elif DENIAL_EFFECT in args.denial_line:
        summary["gbrain_approval_status"] = "denied"
        summary["gbrain_denial_line"] = args.denial_line
        summary["gbrain_denial_recourse"] = args.denial_recourse or "Resolve the concrete GBrain blocker and resubmit this exact boundary."

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["approval_rows", "gbrain_approval_status", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
