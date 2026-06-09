#!/usr/bin/env python3
"""Materialize the combined non-mutating Vanderbilt slice-2 follow-up packet set."""

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

SOURCE_CSV = ARTIFACTS / "vanderbilt_slice_2_approved_parser_scope_next_packets.csv"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_approved_parser_scope_next_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_slice_2_followup_packet_set.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_slice_2_followup_packet_set.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_followup_packet_set_summary.json"
OUT_MD = RESEARCH / "vanderbilt-slice-2-followup-packet-set-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "c59c9c4fe4b09f4d225676cdb12566eaeafadd1e3bc2f5049aa24745130a6362"
SOURCE_ROUTE_PARSER_SCOPE_APPROVAL_ROWSET_SHA256 = "bb0c69694a411c386964d1b7ae523a65a31452e5d62db227d4469044bd109672"
SOURCE_ROUTE_OBSERVATION_ROWSET_SHA256 = "c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0"
GBRAIN_ADVISORY_LINE = "APPROVE option_a_combined_followup_packet_set"

MUTATION_POLICY = (
    "Combined non-mutating Vanderbilt slice-2 follow-up packet set. It converts the approved parser/scope "
    "next-packet ledger into row-level packet families and required evidence boundaries for target-route "
    "parser-build review, related-scope disposition, broader-context recourse, and denominator-redirect recourse. "
    "It does not fetch web pages, execute parsers, accept parser output, ingest people, mutate training states, "
    "close denominators, verify Vanderbilt as a school, rewrite URLs, accept unsupported labels or enrichment "
    "facts, publish raw dumps, or collapse unique-person identities."
)

FIELDS = [
    "followup_packet_key",
    "source_next_packet_key",
    "source_packet_key",
    "observation_key",
    "approval_request_key",
    "request_order",
    "program_key",
    "program_name",
    "program_type",
    "route_role",
    "fetch_url",
    "final_url",
    "http_status",
    "packet_family",
    "followup_lane",
    "followup_packet_status",
    "parser_test_design_allowed",
    "scope_disposition_review_allowed",
    "route_recourse_review_allowed",
    "web_fetch_allowed",
    "parser_execution_allowed",
    "parser_implementation_allowed",
    "parser_acceptance_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "accepted_person_rows",
    "required_operator_action",
    "required_evidence_boundary",
    "required_evidence_fields_json",
    "next_required_approval",
    "source_content_sha256",
    "source_visible_text_sha256",
    "gbrain_advisory_line",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"followup_packet_key", "required_evidence_fields_json", "mutation_policy", "generated_at"}
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
    if not path.exists():
        return []
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


def int_value(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt slice-2 approved parser/scope next-packet summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "source_route_parser_scope_rowset": summary.get("source_route_parser_scope_approval_packet_rowset_sha256")
        == SOURCE_ROUTE_PARSER_SCOPE_APPROVAL_ROWSET_SHA256,
        "source_route_observation_rowset": summary.get("source_route_observation_rowset_sha256")
        == SOURCE_ROUTE_OBSERVATION_ROWSET_SHA256,
        "next_packet_rows": summary.get("next_packet_rows") == 18,
        "gbrain_status": summary.get("gbrain_approval_status") == "approved_exact_non_mutating_next_packet_lane",
        "web_fetch_false": summary.get("web_fetch_allowed") is False,
        "parser_implementation_false": summary.get("parser_implementation_allowed") is False,
        "parser_acceptance_false": summary.get("parser_acceptance_allowed") is False,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
        "denominator_closure_false": summary.get("denominator_closure_allowed") is False,
        "school_verification_false": summary.get("school_verification_allowed") is False,
        "url_rewrite_false": summary.get("url_rewrite_allowed") is False,
        "identity_collapse_false": summary.get("identity_collapse_allowed") is False,
        "accepted_person_rows_zero": summary.get("accepted_person_rows") == 0,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected Vanderbilt slice-2 follow-up source boundary: " + dumps(checks))
    return summary


def classify(source: dict[str, str]) -> dict[str, object]:
    packet_family = source.get("approved_next_artifact_lane", "")
    if packet_family == "target_route_parser_build_review_packet":
        return {
            "followup_lane": "target_route_parser_build_review",
            "followup_packet_status": "non_mutating_parser_test_design_packet_ready",
            "parser_test_design_allowed": "true",
            "scope_disposition_review_allowed": "false",
            "route_recourse_review_allowed": "false",
            "required_operator_action": (
                "Draft route-specific parser-test design evidence: route sections, selector hypotheses, "
                "candidate-only count assertions, fixture boundaries, and no-execution/no-ingestion gates."
            ),
            "required_evidence_boundary": (
                "Use only committed route metadata, content hashes, prior coarse signals, selector hypotheses, "
                "and test-design expectations. Do not fetch, execute a parser, extract candidate rows, or accept people."
            ),
            "required_evidence_fields": [
                "route_section_hypotheses",
                "selector_hypotheses",
                "candidate_count_assertion_plan",
                "fixture_boundary",
                "no_parser_execution_confirmation",
            ],
            "next_required_approval": "exact_parser_execution_or_candidate_only_extraction_approval_required",
        }
    if packet_family == "related_scope_context_disposition_packet":
        return {
            "followup_lane": "related_scope_context_disposition_review",
            "followup_packet_status": "non_mutating_scope_disposition_packet_ready",
            "parser_test_design_allowed": "false",
            "scope_disposition_review_allowed": "true",
            "route_recourse_review_allowed": "false",
            "required_operator_action": (
                "Draft scope-disposition evidence for the related/context route: same-target support, related-context "
                "only, exclusion, or recourse routing, with no URL rewrite or denominator closure."
            ),
            "required_evidence_boundary": (
                "Use committed route metadata, route role, hashes, and scope rationale options only. Do not fetch, "
                "rewrite source URLs, close gaps, or ingest people."
            ),
            "required_evidence_fields": [
                "scope_classification_options",
                "target_support_rationale",
                "related_context_rationale",
                "exclusion_or_recourse_rationale",
                "no_url_rewrite_confirmation",
            ],
            "next_required_approval": "exact_scope_disposition_acceptance_or_recourse_approval_required",
        }
    if packet_family == "broader_context_source_discovery_recourse_packet":
        return {
            "followup_lane": "broader_context_source_discovery_recourse",
            "followup_packet_status": "non_mutating_broader_context_recourse_packet_ready",
            "parser_test_design_allowed": "false",
            "scope_disposition_review_allowed": "true",
            "route_recourse_review_allowed": "true",
            "required_operator_action": (
                "Draft broader-context recourse evidence: why the observed page is not sufficient current-roster "
                "evidence, stronger official source anchors to seek later, and unresolved-gap handling."
            ),
            "required_evidence_boundary": (
                "Use committed route metadata, route role, hashes, and source-discovery anchor planning only. Do not "
                "fetch, accept context as roster truth, close denominators, or ingest people."
            ),
            "required_evidence_fields": [
                "context_not_current_roster_rationale",
                "stronger_source_anchor_plan",
                "future_source_discovery_query_plan",
                "unresolved_gap_disposition_options",
                "no_denominator_closure_confirmation",
            ],
            "next_required_approval": "exact_source_discovery_fetch_or_unresolved_gap_disposition_approval_required",
        }
    return {
        "followup_lane": "denominator_redirect_recourse",
        "followup_packet_status": "non_mutating_denominator_redirect_recourse_packet_ready",
        "parser_test_design_allowed": "false",
        "scope_disposition_review_allowed": "false",
        "route_recourse_review_allowed": "true",
        "required_operator_action": (
            "Draft redirect recourse evidence: requested URL, observed final URL, hash evidence, replacement-route "
            "anchors to seek later, and unresolved-route disposition."
        ),
        "required_evidence_boundary": (
            "Use committed URL/final-URL/hash evidence and replacement-anchor planning only. Do not fetch, rewrite "
            "URLs, close gaps, or accept route replacement without exact approval."
        ),
        "required_evidence_fields": [
            "requested_route",
            "observed_final_route",
            "redirect_or_mismatch_rationale",
            "replacement_route_anchor_plan",
            "no_source_url_rewrite_confirmation",
        ],
        "next_required_approval": "exact_route_replacement_or_unresolved_gap_disposition_approval_required",
    }


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("followup_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Slice 2 Follow-Up Packet Set",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Slice 2 Follow-Up Packet Set",
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
        "## Packet Rows",
        "",
        "| request | program | packet family | follow-up lane | status | next approval |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {request_order} | {program_name} | {packet_family} | {followup_lane} | {followup_packet_status} | {next_required_approval} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_csv_rows(SOURCE_CSV)
    if len(source_rows) != 18:
        raise SystemExit("Expected 18 Vanderbilt slice-2 approved parser/scope next-packet rows.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        packet = classify(source)
        rows.append(
            {
                "followup_packet_key": stable_key(
                    "vanderbilt_slice_2_followup_packet",
                    source.get("next_packet_key"),
                    packet["followup_lane"],
                ),
                "source_next_packet_key": source.get("next_packet_key", ""),
                "source_packet_key": source.get("source_packet_key", ""),
                "observation_key": source.get("observation_key", ""),
                "approval_request_key": source.get("approval_request_key", ""),
                "request_order": int_value(source.get("request_order")),
                "program_key": source.get("program_key", ""),
                "program_name": source.get("program_name", ""),
                "program_type": source.get("program_type", ""),
                "route_role": source.get("route_role", ""),
                "fetch_url": source.get("fetch_url", ""),
                "final_url": source.get("final_url", ""),
                "http_status": source.get("http_status", ""),
                "packet_family": source.get("approved_next_artifact_lane", ""),
                "followup_lane": packet["followup_lane"],
                "followup_packet_status": packet["followup_packet_status"],
                "parser_test_design_allowed": packet["parser_test_design_allowed"],
                "scope_disposition_review_allowed": packet["scope_disposition_review_allowed"],
                "route_recourse_review_allowed": packet["route_recourse_review_allowed"],
                "web_fetch_allowed": "false",
                "parser_execution_allowed": "false",
                "parser_implementation_allowed": "false",
                "parser_acceptance_allowed": "false",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "accepted_person_rows": 0,
                "required_operator_action": packet["required_operator_action"],
                "required_evidence_boundary": packet["required_evidence_boundary"],
                "required_evidence_fields_json": dumps(packet["required_evidence_fields"]),
                "next_required_approval": packet["next_required_approval"],
                "source_content_sha256": source.get("content_sha256", ""),
                "source_visible_text_sha256": source.get("visible_text_sha256", ""),
                "gbrain_advisory_line": GBRAIN_ADVISORY_LINE,
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (str(item["packet_family"]), int(item["request_order"]), str(item["route_role"])))
    by_family = Counter(str(row["packet_family"]) for row in rows)
    by_lane = Counter(str(row["followup_lane"]) for row in rows)
    by_status = Counter(str(row["followup_packet_status"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_approved_parser_scope_next_packets": str(SOURCE_CSV.relative_to(ROOT)),
        "source_approved_parser_scope_next_packet_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_approved_parser_scope_next_packet_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_route_parser_scope_approval_packet_rowset_sha256": SOURCE_ROUTE_PARSER_SCOPE_APPROVAL_ROWSET_SHA256,
        "source_route_observation_rowset_sha256": SOURCE_ROUTE_OBSERVATION_ROWSET_SHA256,
        "source_next_packet_rows": source_summary.get("next_packet_rows"),
        "followup_packet_rows": len(rows),
        "request_rows_represented": len({str(row["approval_request_key"]) for row in rows}),
        "by_packet_family": dict(sorted(by_family.items())),
        "by_followup_lane": dict(sorted(by_lane.items())),
        "by_followup_packet_status": dict(sorted(by_status.items())),
        "gbrain_advisory_status": "approved_option_a_combined_followup_packet_set",
        "gbrain_advisory_line": GBRAIN_ADVISORY_LINE,
        "web_fetch_allowed": False,
        "parser_execution_allowed": False,
        "parser_implementation_allowed": False,
        "parser_acceptance_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "accepted_person_rows": 0,
        "raw_dump_publication_allowed": False,
        "mutation_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["followup_packet_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
