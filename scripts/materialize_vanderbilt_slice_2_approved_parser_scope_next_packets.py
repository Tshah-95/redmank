#!/usr/bin/env python3
"""Materialize approved non-mutating Vanderbilt slice-2 parser/scope next-packet lanes."""

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

SOURCE_CSV = ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet.csv"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_slice_2_approved_parser_scope_next_packets.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_slice_2_approved_parser_scope_next_packets.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_approved_parser_scope_next_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-slice-2-approved-parser-scope-next-packets-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "bb0c69694a411c386964d1b7ae523a65a31452e5d62db227d4469044bd109672"
SOURCE_ROUTE_OBSERVATION_ROWSET_SHA256 = "c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0"
APPROVAL_LINE = (
    "APPROVE vanderbilt_slice_2_route_parser_scope_approval_packet_approved PACKET_ROWS 18 "
    "TARGET_ROUTE_REVIEW_ROWS 5 RELATED_SCOPE_ROWS 5 BROADER_CONTEXT_RECOURSE_ROWS 4 "
    "DENOMINATOR_REDIRECT_RECOURSE_ROWS 4 SOURCE_ROWSET_SHA256 "
    "c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0 ROWSET_SHA256 "
    "bb0c69694a411c386964d1b7ae523a65a31452e5d62db227d4469044bd109672"
)

MUTATION_POLICY = (
    "Approved non-mutating Vanderbilt slice-2 parser/scope next-packet lane. The exact GBrain approval allows only "
    "next-packet preparation for target-route parser-build review, related-scope/context disposition, broader-context "
    "recourse, and denominator-redirect recourse. It does not approve web fetching, parser implementation, parser "
    "acceptance, parser output as accepted people, person ingestion, training-state mutation, denominator closure, "
    "Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment/profile/contact/research-"
    "fact acceptance, raw dump publication, or unique-person identity collapse."
)

FIELDS = [
    "next_packet_key",
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
    "approval_request_lane",
    "approved_next_artifact_lane",
    "next_packet_status",
    "non_mutating_parser_build_review_allowed",
    "scope_disposition_review_allowed",
    "route_recourse_review_allowed",
    "web_fetch_allowed",
    "parser_implementation_allowed",
    "parser_acceptance_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "required_operator_action",
    "required_evidence_boundary",
    "required_next_approval",
    "content_sha256",
    "visible_text_sha256",
    "source_route_signal_json",
    "gbrain_approval_line",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"next_packet_key", "source_route_signal_json", "mutation_policy", "generated_at"}
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
        raise SystemExit("Expected Vanderbilt slice-2 route parser/scope approval packet summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "route_observation_rowset": summary.get("source_route_observation_rowset_sha256")
        == SOURCE_ROUTE_OBSERVATION_ROWSET_SHA256,
        "packet_rows": summary.get("packet_rows") == 18,
        "request_rows_represented": summary.get("request_rows_represented") == 9,
        "approval_line": summary.get("required_approval_line") == APPROVAL_LINE,
        "pending_status": summary.get("gbrain_approval_status") == "pending_exact_approval_line",
        "web_fetch_allowed_false": summary.get("web_fetch_allowed") is False,
        "parser_implementation_false": summary.get("parser_implementation_allowed") is False,
        "parser_acceptance_false": summary.get("parser_acceptance_allowed") is False,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
        "denominator_closure_false": summary.get("denominator_closure_allowed") is False,
        "school_verification_false": summary.get("school_verification_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected Vanderbilt slice-2 approved next-packet source boundary: " + dumps(checks))
    return summary


def classify(source: dict[str, str]) -> dict[str, str]:
    lane = source.get("approval_request_lane", "")
    if lane == "target_route_parser_build_review":
        return {
            "approved_next_artifact_lane": "target_route_parser_build_review_packet",
            "next_packet_status": "approved_non_mutating_target_route_parser_build_review_ready",
            "non_mutating_parser_build_review_allowed": "true",
            "scope_disposition_review_allowed": "false",
            "route_recourse_review_allowed": "false",
            "required_operator_action": (
                "Prepare parser-build review evidence for this target denominator route: selectors, route sections, "
                "candidate-only count strategy, and test fixtures. Do not implement parser extraction as accepted people."
            ),
            "required_evidence_boundary": (
                "Route metadata, hashes, coarse signals, parser-test design, candidate-only count/fingerprint plan, "
                "and explicit no-parser-implementation/no-ingestion boundary."
            ),
            "required_next_approval": "exact_parser_implementation_or_candidate_only_extraction_approval_required",
        }
    if lane == "related_scope_context_disposition_review":
        return {
            "approved_next_artifact_lane": "related_scope_context_disposition_packet",
            "next_packet_status": "approved_non_mutating_related_scope_disposition_ready",
            "non_mutating_parser_build_review_allowed": "false",
            "scope_disposition_review_allowed": "true",
            "route_recourse_review_allowed": "false",
            "required_operator_action": (
                "Prepare scope disposition evidence for related person-list/context routes: target-supporting, "
                "related-context-only, exclusion evidence, or recourse input."
            ),
            "required_evidence_boundary": (
                "Route metadata, hashes, route-role rationale, scope classification options, and explicit no-url-"
                "rewrite/no-denominator-closure/no-ingestion boundary."
            ),
            "required_next_approval": "exact_scope_disposition_acceptance_or_parser_build_approval_required",
        }
    if lane == "broader_context_recourse_review":
        return {
            "approved_next_artifact_lane": "broader_context_source_discovery_recourse_packet",
            "next_packet_status": "approved_non_mutating_broader_context_recourse_ready",
            "non_mutating_parser_build_review_allowed": "false",
            "scope_disposition_review_allowed": "true",
            "route_recourse_review_allowed": "true",
            "required_operator_action": (
                "Prepare broader-context recourse evidence for official graduation/outcome/context pages and define "
                "stronger current-roster source-discovery requirements."
            ),
            "required_evidence_boundary": (
                "Route metadata, hashes, context-vs-current-roster rationale, stronger-source search anchors, and "
                "explicit no-parser-acceptance/no-denominator-closure boundary."
            ),
            "required_next_approval": "exact_source_discovery_recourse_or_scope_disposition_acceptance_required",
        }
    return {
        "approved_next_artifact_lane": "denominator_redirect_recourse_packet",
        "next_packet_status": "approved_non_mutating_denominator_redirect_recourse_ready",
        "non_mutating_parser_build_review_allowed": "false",
        "scope_disposition_review_allowed": "false",
        "route_recourse_review_allowed": "true",
        "required_operator_action": (
            "Prepare recourse evidence for denominator routes that redirected away from the requested program path; "
            "identify replacement-route search anchors or unresolved-route disposition."
        ),
        "required_evidence_boundary": (
            "Original URL, final URL, hashes, redirect/domain evidence, replacement-route search anchors, and explicit "
            "no-source-url-rewrite/no-gap-closure boundary."
        ),
        "required_next_approval": "exact_route_replacement_or_unresolved_gap_disposition_approval_required",
    }


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
        "title: Vanderbilt Slice 2 Approved Parser Scope Next Packets",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Slice 2 Approved Parser Scope Next Packets",
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
        "| request | role | program | approved lane | status | required action |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {request_order} | {route_role} | {program_name} | {approved_next_artifact_lane} | {next_packet_status} | {required_operator_action} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_csv_rows(SOURCE_CSV)
    if len(source_rows) != 18:
        raise SystemExit("Expected 18 Vanderbilt slice-2 parser/scope approval packet rows.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        next_packet = classify(source)
        rows.append(
            {
                "next_packet_key": stable_key(
                    "vanderbilt_slice_2_approved_parser_scope_next",
                    source.get("packet_key"),
                    next_packet["approved_next_artifact_lane"],
                ),
                "source_packet_key": source.get("packet_key", ""),
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
                "approval_request_lane": source.get("approval_request_lane", ""),
                "approved_next_artifact_lane": next_packet["approved_next_artifact_lane"],
                "next_packet_status": next_packet["next_packet_status"],
                "non_mutating_parser_build_review_allowed": next_packet["non_mutating_parser_build_review_allowed"],
                "scope_disposition_review_allowed": next_packet["scope_disposition_review_allowed"],
                "route_recourse_review_allowed": next_packet["route_recourse_review_allowed"],
                "web_fetch_allowed": "false",
                "parser_implementation_allowed": "false",
                "parser_acceptance_allowed": "false",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "required_operator_action": next_packet["required_operator_action"],
                "required_evidence_boundary": next_packet["required_evidence_boundary"],
                "required_next_approval": next_packet["required_next_approval"],
                "content_sha256": source.get("content_sha256", ""),
                "visible_text_sha256": source.get("visible_text_sha256", ""),
                "source_route_signal_json": source.get("route_signal_json", ""),
                "gbrain_approval_line": APPROVAL_LINE,
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(
        key=lambda item: (
            str(item["approved_next_artifact_lane"]),
            int(item["request_order"]),
            str(item["route_role"]),
        )
    )
    by_lane = Counter(str(row["approved_next_artifact_lane"]) for row in rows)
    by_status = Counter(str(row["next_packet_status"]) for row in rows)
    by_role = Counter(str(row["route_role"]) for row in rows)
    parser_build_rows = sum(1 for row in rows if row["non_mutating_parser_build_review_allowed"] == "true")
    scope_rows = sum(1 for row in rows if row["scope_disposition_review_allowed"] == "true")
    recourse_rows = sum(1 for row in rows if row["route_recourse_review_allowed"] == "true")
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_route_parser_scope_approval_packet": str(SOURCE_CSV.relative_to(ROOT)),
        "source_route_parser_scope_approval_packet_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_route_parser_scope_approval_packet_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_route_observation_rowset_sha256": SOURCE_ROUTE_OBSERVATION_ROWSET_SHA256,
        "source_packet_rows": source_summary.get("packet_rows"),
        "gbrain_approval_line": APPROVAL_LINE,
        "gbrain_approval_status": "approved_exact_non_mutating_next_packet_lane",
        "next_packet_rows": len(rows),
        "request_rows_represented": len({str(row["approval_request_key"]) for row in rows}),
        "parser_build_review_rows": parser_build_rows,
        "scope_disposition_review_rows": scope_rows,
        "route_recourse_review_rows": recourse_rows,
        "by_route_role": dict(sorted(by_role.items())),
        "by_approved_next_artifact_lane": dict(sorted(by_lane.items())),
        "by_next_packet_status": dict(sorted(by_status.items())),
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
        "mutation_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["next_packet_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
