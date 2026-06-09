#!/usr/bin/env python3
"""Materialize a Vanderbilt slice-2 route parser/scope approval-request packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SOURCE_CSV = ARTIFACTS / "vanderbilt_slice_2_live_route_observations.csv"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_live_route_observation_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-slice-2-route-parser-scope-approval-packet-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0"
SOURCE_APPROVAL_ROWSET_SHA256 = "98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d"
SOURCE_PLAN_ROWSET_SHA256 = "c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b"
APPROVAL_EFFECT = "vanderbilt_slice_2_route_parser_scope_approval_packet_approved"
DENIAL_EFFECT = "vanderbilt_slice_2_route_parser_scope_approval_packet_denied"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt slice-2 route parser/scope approval-request packet. It classifies the 18 approved "
    "live route observations into target-route parser-build review, related-scope/context disposition, broader "
    "official-context recourse, or denominator-redirect recourse lanes. It requests exact future approval only; it "
    "does not allow web fetching, parser implementation, parser acceptance, person ingestion, training-state "
    "mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, "
    "enrichment/profile/contact/research-fact acceptance, raw dump publication, or identity collapse."
)

NOT_APPROVED = [
    "live_web_fetch",
    "parser_implementation",
    "parser_acceptance",
    "person_ingestion",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "enrichment_acceptance",
    "profile_fact_acceptance",
    "contact_fact_acceptance",
    "research_fact_acceptance",
    "raw_dump_publication",
    "unique_person_identity_collapse",
]

FIELDS = [
    "packet_key",
    "observation_key",
    "approval_request_key",
    "request_order",
    "source_execution_plan_key",
    "gap_key",
    "program_key",
    "program_name",
    "program_type",
    "plan_lane",
    "route_role",
    "fetch_url",
    "final_url",
    "http_status",
    "candidate_route_signal",
    "source_recommended_next_packet",
    "approval_request_lane",
    "packet_status",
    "approval_scope_requested",
    "permitted_if_exactly_approved",
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
    field
    for field in FIELDS
    if field not in {"packet_key", "route_signal_json", "mutation_policy", "generated_at"}
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


def is_root_redirect(row: dict[str, str]) -> bool:
    fetch = urlparse(row.get("fetch_url", ""))
    final = urlparse(row.get("final_url", ""))
    if not final.netloc:
        return False
    final_path = final.path.rstrip("/")
    return fetch.netloc != final.netloc and final_path in {"", "/"}


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt slice-2 route observation summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "approval_rowset": summary.get("source_approval_request_rowset_sha256") == SOURCE_APPROVAL_ROWSET_SHA256,
        "plan_rowset": summary.get("source_execution_plan_rowset_sha256") == SOURCE_PLAN_ROWSET_SHA256,
        "observation_rows": summary.get("observation_rows") == 18,
        "request_rows_represented": summary.get("request_rows_represented") == 9,
        "unique_observed_urls": summary.get("unique_observed_urls") == 12,
        "web_fetch_executed": summary.get("web_fetch_executed") is True,
        "web_fetch_approved": summary.get("web_fetch_approved_by_gbrain") is True,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
        "parser_acceptance_false": summary.get("parser_acceptance_allowed") is False,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
        "denominator_closure_false": summary.get("denominator_closure_allowed") is False,
        "school_verification_false": summary.get("school_verification_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected Vanderbilt slice-2 route parser/scope source boundary: " + dumps(checks))
    return summary


def classify(row: dict[str, str]) -> dict[str, str]:
    if row.get("route_role") == "denominator" and is_root_redirect(row):
        return {
            "approval_request_lane": "denominator_redirect_recourse_review",
            "packet_status": "redirect_recourse_candidate_needs_exact_gbrain_approval",
            "approval_scope_requested": (
                "Approve non-mutating recourse for denominator routes that redirect away from the requested program "
                "path, including stronger official-source discovery or route replacement review only."
            ),
            "permitted_if_exactly_approved": "route_recourse_or_replacement_review_only",
            "required_next_artifact_if_approved": "vanderbilt_slice_2_denominator_redirect_recourse_packet",
            "required_next_artifact_if_denied": "retain_denominator_redirect_as_context_evidence_without_parser_review",
        }
    if row.get("route_role") == "denominator":
        return {
            "approval_request_lane": "target_route_parser_build_review",
            "packet_status": "target_route_parser_scope_candidate_needs_exact_gbrain_approval",
            "approval_scope_requested": (
                "Approve target-route parser-build review for this official denominator route. Approval would allow "
                "parser-test design and candidate-only diagnostics for this route, not parser implementation or "
                "accepted people."
            ),
            "permitted_if_exactly_approved": "parser_build_review_and_candidate_only_test_design",
            "required_next_artifact_if_approved": "vanderbilt_slice_2_target_route_parser_build_review_packet",
            "required_next_artifact_if_denied": "retain_target_route_as_source_discovery_evidence",
        }
    if row.get("plan_lane") == "related_scope_exclusion_then_target_program_source_discovery":
        return {
            "approval_request_lane": "related_scope_context_disposition_review",
            "packet_status": "related_scope_context_needs_exact_gbrain_approval",
            "approval_scope_requested": (
                "Approve non-mutating scope disposition for related-scope/person-list context routes. Approval would "
                "allow classifying the route as target-supporting, related-context-only, exclusion evidence, or "
                "recourse input."
            ),
            "permitted_if_exactly_approved": "scope_disposition_metadata_only",
            "required_next_artifact_if_approved": "vanderbilt_slice_2_related_scope_disposition_packet",
            "required_next_artifact_if_denied": "retain_related_context_without_scope_disposition",
        }
    return {
        "approval_request_lane": "broader_context_recourse_review",
        "packet_status": "broader_context_recourse_candidate_needs_exact_gbrain_approval",
        "approval_scope_requested": (
            "Approve non-mutating recourse review for broader official context or graduation/outcome pages. Approval "
            "would allow route-context classification and stronger current-roster source discovery only."
        ),
        "permitted_if_exactly_approved": "broader_context_classification_and_source_discovery_recourse",
        "required_next_artifact_if_approved": "vanderbilt_slice_2_broader_context_recourse_packet",
        "required_next_artifact_if_denied": "retain_broader_context_as_non_roster_source_discovery_evidence",
    }


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("packet_key", "")))
    ]
    return sha256_text(dumps(material))


def approval_line(summary: dict[str, object]) -> str:
    lanes = summary["by_approval_request_lane"]
    return (
        f"APPROVE {APPROVAL_EFFECT} "
        f"PACKET_ROWS {summary['packet_rows']} "
        f"TARGET_ROUTE_REVIEW_ROWS {lanes.get('target_route_parser_build_review', 0)} "
        f"RELATED_SCOPE_ROWS {lanes.get('related_scope_context_disposition_review', 0)} "
        f"BROADER_CONTEXT_RECOURSE_ROWS {lanes.get('broader_context_recourse_review', 0)} "
        f"DENOMINATOR_REDIRECT_RECOURSE_ROWS {lanes.get('denominator_redirect_recourse_review', 0)} "
        f"SOURCE_ROWSET_SHA256 {SOURCE_ROWSET_SHA256} "
        f"ROWSET_SHA256 {summary['rowset_sha256']}"
    )


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Slice 2 Route Parser Scope Approval Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Slice 2 Route Parser Scope Approval Packet",
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
            "## Packet Rows",
            "",
            "| request | role | program | request lane | status | next artifact if approved |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {request_order} | {route_role} | {program_name} | {approval_request_lane} | {packet_status} | {required_next_artifact_if_approved} |".format(
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
    source_rows = read_csv_rows(SOURCE_CSV)
    if len(source_rows) != 18:
        raise SystemExit("Expected 18 Vanderbilt slice-2 route observation rows.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        request = classify(source)
        rows.append(
            {
                "packet_key": stable_key(
                    "vanderbilt_slice_2_route_parser_scope_approval",
                    source.get("observation_key"),
                    request["approval_request_lane"],
                ),
                "observation_key": source.get("observation_key", ""),
                "approval_request_key": source.get("approval_request_key", ""),
                "request_order": int_value(source.get("request_order")),
                "source_execution_plan_key": source.get("source_execution_plan_key", ""),
                "gap_key": source.get("gap_key", ""),
                "program_key": source.get("program_key", ""),
                "program_name": source.get("program_name", ""),
                "program_type": source.get("program_type", ""),
                "plan_lane": source.get("plan_lane", ""),
                "route_role": source.get("route_role", ""),
                "fetch_url": source.get("fetch_url", ""),
                "final_url": source.get("final_url", ""),
                "http_status": source.get("http_status", ""),
                "candidate_route_signal": source.get("candidate_route_signal", ""),
                "source_recommended_next_packet": source.get("recommended_next_packet", ""),
                "approval_request_lane": request["approval_request_lane"],
                "packet_status": request["packet_status"],
                "approval_scope_requested": request["approval_scope_requested"],
                "permitted_if_exactly_approved": request["permitted_if_exactly_approved"],
                "prohibited_after_approval": "; ".join(NOT_APPROVED),
                "required_next_artifact_if_approved": request["required_next_artifact_if_approved"],
                "required_next_artifact_if_denied": request["required_next_artifact_if_denied"],
                "content_sha256": source.get("content_sha256", ""),
                "visible_text_sha256": source.get("visible_text_sha256", ""),
                "route_signal_json": dumps(
                    {
                        "source_route_observation_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "source_approval_request_rowset_sha256": SOURCE_APPROVAL_ROWSET_SHA256,
                        "source_execution_plan_rowset_sha256": SOURCE_PLAN_ROWSET_SHA256,
                        "route_role": source.get("route_role"),
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
                        "root_redirect_recourse": is_root_redirect(source),
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (int(item["request_order"]), str(item["route_role"]), str(item["approval_request_lane"])))
    by_lane = Counter(str(row["approval_request_lane"]) for row in rows)
    by_status = Counter(str(row["packet_status"]) for row in rows)
    by_role = Counter(str(row["route_role"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_route_observations": str(SOURCE_CSV.relative_to(ROOT)),
        "source_route_observation_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_route_observation_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_approval_request_rowset_sha256": SOURCE_APPROVAL_ROWSET_SHA256,
        "source_execution_plan_rowset_sha256": SOURCE_PLAN_ROWSET_SHA256,
        "source_observation_rows": source_summary.get("observation_rows"),
        "packet_rows": len(rows),
        "request_rows_represented": len({str(row["approval_request_key"]) for row in rows}),
        "by_route_role": dict(sorted(by_role.items())),
        "by_approval_request_lane": dict(sorted(by_lane.items())),
        "by_packet_status": dict(sorted(by_status.items())),
        "mutation_allowed": False,
        "web_fetch_allowed": False,
        "parser_implementation_allowed": False,
        "parser_acceptance_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "accepted_person_rows": 0,
        "raw_dump_publication_allowed": False,
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
        summary["gbrain_approval_status"] = "approved_exact_non_mutating_route_parser_scope_next_artifact_lane"
    elif DENIAL_EFFECT in args.denial_line:
        summary["gbrain_approval_status"] = "denied_needs_verification_documentation"
        summary["gbrain_denial_line"] = args.denial_line
        summary["gbrain_denial_recourse"] = args.denial_recourse or (
            "Build verification documentation for this exact packet artifact and rowset, then resubmit the same "
            "approval boundary. Do not build parser implementation, parser acceptance, person-ingestion, scope "
            "closure, or denominator-closure artifacts while denied."
        )

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(
        json.dumps(
            {key: summary[key] for key in ["packet_rows", "gbrain_approval_status", "rowset_sha256"]},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
