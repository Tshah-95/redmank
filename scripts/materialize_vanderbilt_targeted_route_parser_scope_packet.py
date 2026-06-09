#!/usr/bin/env python3
"""Materialize a non-mutating Vanderbilt route parser/scope approval-request packet."""

from __future__ import annotations

import csv
import hashlib
import json
import argparse
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SOURCE_JSON = ARTIFACTS / "vanderbilt_targeted_route_observations.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_targeted_route_observation_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-targeted-route-parser-scope-packet-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "f547a298bf0efdaba630aa9d184ecd85979d0356039bbbd92d3c2fd026745258"
APPROVAL_EFFECT = "vanderbilt_targeted_route_observation_parser_scope_packet_approved"
DENIAL_EFFECT = "vanderbilt_targeted_route_observation_parser_scope_packet_denied"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt route parser/scope approval-request packet. It asks whether route observations may "
    "advance into exact parser-build review, linked-scope disposition, or recourse handling. It authorizes no "
    "parser acceptance unless the exact approval line is returned, and it never authorizes person ingestion, "
    "training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label "
    "ingestion, profile/contact/research-fact acceptance, or unique-person identity collapse."
)

NOT_APPROVED = [
    "parser_acceptance_without_exact_gbrain_line",
    "person_ingestion",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "profile_contact_research_fact_acceptance",
    "unique_person_identity_collapse",
]

FIELDS = [
    "packet_key",
    "observation_key",
    "execution_key",
    "program_key",
    "program_name",
    "fetch_url",
    "final_url",
    "http_status",
    "candidate_route_signal",
    "source_recommended_next_packet",
    "approval_request_lane",
    "packet_status",
    "approval_scope_requested",
    "prohibited_after_approval",
    "required_next_artifact_if_approved",
    "required_next_artifact_if_denied",
    "content_sha256",
    "visible_text_sha256",
    "route_signal_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "observation_key",
    "execution_key",
    "program_key",
    "program_name",
    "fetch_url",
    "final_url",
    "http_status",
    "candidate_route_signal",
    "source_recommended_next_packet",
    "approval_request_lane",
    "packet_status",
    "approval_scope_requested",
    "required_next_artifact_if_approved",
    "required_next_artifact_if_denied",
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
        raise SystemExit("Expected Vanderbilt targeted route-observation summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "observation_rows": summary.get("observation_rows") == 20,
        "unique_observed_urls": summary.get("unique_observed_urls") == 16,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected Vanderbilt route-observation boundary: {checks}")
    return summary


def classify(row: dict[str, object]) -> dict[str, str]:
    signal = str(row.get("candidate_route_signal") or "")
    next_packet = str(row.get("recommended_next_packet") or "")
    if signal == "http_error_needs_retry_or_recourse":
        return {
            "approval_request_lane": "route_recourse_review",
            "packet_status": "recourse_row_not_parser_eligible",
            "approval_scope_requested": (
                "Approve recourse handling only: retry route, prefer stronger official source, or carry as unresolved "
                "route failure. No parser acceptance."
            ),
            "required_next_artifact_if_approved": "route_retry_or_recourse_disposition_packet",
            "required_next_artifact_if_denied": "retain_in_active_gap_manifest_with_http_error_evidence",
        }
    if next_packet == "linked_route_parser_acceptance_or_scope_disposition_packet":
        return {
            "approval_request_lane": "exact_parser_build_review",
            "packet_status": "parser_build_candidate_needs_exact_gbrain_approval",
            "approval_scope_requested": (
                "Approve exact parser-build review for this official current-roster route. Approval would allow "
                "source-specific parser tests and candidate-only extraction evidence, but not person ingestion or "
                "denominator closure."
            ),
            "required_next_artifact_if_approved": "source_specific_parser_build_packet",
            "required_next_artifact_if_denied": "scope_disposition_or_source_discovery_recourse_packet",
        }
    if next_packet == "general_surgery_rendered_review_disposition_packet":
        return {
            "approval_request_lane": "rendered_general_surgery_parser_scope_review",
            "packet_status": "general_surgery_parser_scope_candidate_needs_exact_gbrain_approval",
            "approval_scope_requested": (
                "Approve rendered parser/scope review for the official General Surgery current-residents route. "
                "Approval would allow parser-test design or recourse disposition only."
            ),
            "required_next_artifact_if_approved": "general_surgery_rendered_parser_scope_packet",
            "required_next_artifact_if_denied": "general_surgery_recourse_or_unresolved_gap_packet",
        }
    return {
        "approval_request_lane": "linked_route_scope_disposition_review",
        "packet_status": "scope_disposition_candidate_needs_exact_gbrain_approval",
        "approval_scope_requested": (
            "Approve linked-route scope disposition for shared or ambiguous official roster evidence. Approval "
            "would allow classifying this route as same-program parser candidate, shared-source context, or recourse."
        ),
        "required_next_artifact_if_approved": "linked_route_scope_disposition_packet",
        "required_next_artifact_if_denied": "retain_as_context_or_source_discovery_evidence",
    }


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("packet_key", "")))
    ]
    return sha256_text(dumps(material))


def approval_line(summary: dict[str, object]) -> str:
    return (
        "APPROVE "
        + APPROVAL_EFFECT
        + " PACKET_ROWS "
        + str(summary["packet_rows"])
        + " PARSER_BUILD_REVIEW_ROWS "
        + str(summary["by_approval_request_lane"].get("exact_parser_build_review", 0))
        + " SCOPE_DISPOSITION_ROWS "
        + str(summary["by_approval_request_lane"].get("linked_route_scope_disposition_review", 0))
        + " GENERAL_SURGERY_ROWS "
        + str(summary["by_approval_request_lane"].get("rendered_general_surgery_parser_scope_review", 0))
        + " RECOURSE_ROWS "
        + str(summary["by_approval_request_lane"].get("route_recourse_review", 0))
        + " ROWSET_SHA256 "
        + str(summary["rowset_sha256"])
    )


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Targeted Route Parser Scope Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Targeted Route Parser Scope Packet",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Required Approval Line",
        "",
        "`" + str(summary["required_approval_line"]) + "`",
        "",
        "If GBrain does not return that exact line, this packet remains a non-mutating request artifact only.",
        "",
        "GBrain approval status: `" + str(summary["gbrain_approval_status"]) + "`.",
    ]
    if summary.get("gbrain_denial_line"):
        lines.extend(
            [
                "",
                "## Denial Recourse",
                "",
                str(summary.get("gbrain_denial_line")),
                "",
                str(summary.get("gbrain_denial_recourse")),
            ]
        )
    lines.extend(
        [
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Packet Rows",
        "",
        "| program | lane | status | http | signal | fetch url |",
        "| --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {program_name} | {approval_request_lane} | {packet_status} | {http_status} | {candidate_route_signal} | {fetch_url} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-line", default="", help="Exact GBrain approval line, if returned.")
    parser.add_argument("--denial-line", default="", help="Exact GBrain denial line, if returned.")
    parser.add_argument("--denial-recourse", default="", help="Concise recourse extracted from the GBrain denial.")
    args = parser.parse_args()

    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected Vanderbilt targeted route-observation JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        classification = classify(source)
        rows.append(
            {
                "packet_key": stable_key("vanderbilt_targeted_route_parser_scope", source.get("observation_key"), classification["approval_request_lane"]),
                "observation_key": source.get("observation_key"),
                "execution_key": source.get("execution_key"),
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "fetch_url": source.get("fetch_url"),
                "final_url": source.get("final_url"),
                "http_status": source.get("http_status"),
                "candidate_route_signal": source.get("candidate_route_signal"),
                "source_recommended_next_packet": source.get("recommended_next_packet"),
                "approval_request_lane": classification["approval_request_lane"],
                "packet_status": classification["packet_status"],
                "approval_scope_requested": classification["approval_scope_requested"],
                "prohibited_after_approval": "; ".join(NOT_APPROVED[1:]),
                "required_next_artifact_if_approved": classification["required_next_artifact_if_approved"],
                "required_next_artifact_if_denied": classification["required_next_artifact_if_denied"],
                "content_sha256": source.get("content_sha256"),
                "visible_text_sha256": source.get("visible_text_sha256"),
                "route_signal_json": dumps(
                    {
                        "source_route_observation_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "fetch_status": source.get("fetch_status"),
                        "same_domain_final_url": source.get("same_domain_final_url"),
                        "title_current_signal": source.get("title_current_signal"),
                        "heading_current_signal": source.get("heading_current_signal"),
                        "heading_signal_count": source.get("heading_signal_count"),
                        "current_term_count": source.get("current_term_count"),
                        "resident_term_count": source.get("resident_term_count"),
                        "fellow_term_count": source.get("fellow_term_count"),
                        "person_anchor_count": source.get("person_anchor_count"),
                        "roster_anchor_count": source.get("roster_anchor_count"),
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (str(item["approval_request_lane"]), str(item["program_name"]), str(item["fetch_url"])))
    by_lane = Counter(str(row["approval_request_lane"]) for row in rows)
    by_status = Counter(str(row["packet_status"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_route_observations": str(SOURCE_JSON.relative_to(ROOT)),
        "source_route_observation_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_route_observation_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_observation_rows": source_summary.get("observation_rows"),
        "packet_rows": len(rows),
        "by_approval_request_lane": dict(sorted(by_lane.items())),
        "by_packet_status": dict(sorted(by_status.items())),
        "mutation_allowed": False,
        "gbrain_approval_status": "pending_exact_approval_line",
        "gbrain_approval_effect": APPROVAL_EFFECT,
        "gbrain_denial_effect": DENIAL_EFFECT,
        "gbrain_denial_line": "",
        "gbrain_denial_recourse": "",
        "not_approved": NOT_APPROVED,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    summary["required_approval_line"] = approval_line(summary)
    if args.approval_line == summary["required_approval_line"]:
        summary["gbrain_approval_status"] = "approved_exact_non_mutating_next_artifact_lane"
    elif DENIAL_EFFECT in args.denial_line:
        summary["gbrain_approval_status"] = "denied_needs_verification_documentation"
        summary["gbrain_denial_line"] = args.denial_line
        summary["gbrain_denial_recourse"] = args.denial_recourse or (
            "Build verification documentation for this exact packet artifact and rowset, then resubmit the same "
            "approval boundary. Do not build parser-acceptance artifacts while denied."
        )

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["packet_rows", "gbrain_approval_status", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
