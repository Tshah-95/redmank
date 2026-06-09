#!/usr/bin/env python3
"""Materialize Vanderbilt candidate review-queue approval request."""

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

SOURCE_JSON = ARTIFACTS / "vanderbilt_candidate_only_parser_outputs.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_candidate_only_parser_output_summary.json"
VERIFICATION_SUMMARY = ARTIFACTS / "vanderbilt_candidate_parser_output_verification_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_candidate_review_queue_approval_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_candidate_review_queue_approval_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_queue_approval_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-candidate-review-queue-approval-packet-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba"
VERIFICATION_ROWSET_SHA256 = "918556f5b5a33b5d8e7181ed6654a9b7773b8c8a24f09f9a23b06c7157d39fe2"
APPROVAL_EFFECT = "vanderbilt_candidate_review_queue_materialization_approved"
DENIAL_EFFECT = "vanderbilt_candidate_review_queue_materialization_denied"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt candidate review-queue approval request. It asks whether verified candidate "
    "fingerprints, linked-route scope metadata, and route recourse rows may become review queues. It does not "
    "approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, "
    "Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump "
    "publication, or unique-person identity collapse."
)

FIELDS = [
    "approval_packet_key",
    "source_parser_output_key",
    "program_key",
    "program_name",
    "output_kind",
    "approval_request_lane",
    "approval_scope_requested",
    "queue_materialization_allowed_if_approved",
    "person_ingestion_allowed_if_approved",
    "accepted_person_row_allowed_if_approved",
    "required_queue_boundary_if_approved",
    "next_artifact_if_approved",
    "next_artifact_if_denied",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "content_sha256",
    "visible_text_sha256",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_parser_output_key",
    "program_key",
    "program_name",
    "output_kind",
    "approval_request_lane",
    "approval_scope_requested",
    "queue_materialization_allowed_if_approved",
    "person_ingestion_allowed_if_approved",
    "accepted_person_row_allowed_if_approved",
    "required_queue_boundary_if_approved",
    "next_artifact_if_approved",
    "next_artifact_if_denied",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
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


def verify_source_boundary() -> tuple[dict[str, object], dict[str, object]]:
    source_summary = read_json(SOURCE_SUMMARY)
    verification_summary = read_json(VERIFICATION_SUMMARY)
    if not isinstance(source_summary, dict) or not isinstance(verification_summary, dict):
        raise SystemExit("Expected candidate parser output and verification summaries.")
    checks = {
        "source_rowset": source_summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "source_fingerprints": source_summary.get("candidate_fingerprint_rows") == 155,
        "source_accepted_zero": source_summary.get("accepted_person_rows") == 0,
        "verification_rowset": verification_summary.get("rowset_sha256") == VERIFICATION_ROWSET_SHA256,
        "verification_approved": verification_summary.get("gbrain_registration_status")
        == "approved_exact_candidate_output_verification",
        "verification_pass": verification_summary.get("pass_rows") == 9 and verification_summary.get("fail_rows") == 0,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected candidate review-queue approval boundary: {checks}")
    return source_summary, verification_summary


def classify(row: dict[str, object]) -> dict[str, str]:
    output_kind = str(row.get("output_kind") or "")
    if output_kind == "candidate_fingerprint":
        return {
            "approval_request_lane": "candidate_fingerprint_review_queue",
            "approval_scope_requested": "Allow verified hashed candidate fingerprints to become reviewer queue rows without raw names or accepted people.",
            "required_queue_boundary_if_approved": "Queue rows may include candidate/program/source hashes, source kind, and route hashes only; no raw candidate labels or raw person URLs.",
            "next_artifact_if_approved": "vanderbilt_candidate_fingerprint_review_queue",
            "next_artifact_if_denied": "retain_verified_candidate_fingerprints_without_queue_materialization",
        }
    if output_kind == "scope_metadata":
        return {
            "approval_request_lane": "linked_scope_metadata_review_queue",
            "approval_scope_requested": "Allow linked-route scope metadata to become reviewer queue rows for same-program/shared-source routing.",
            "required_queue_boundary_if_approved": "Queue rows may include program/source hashes and scope status only; no URL rewrites or denominator closure.",
            "next_artifact_if_approved": "vanderbilt_linked_scope_metadata_review_queue",
            "next_artifact_if_denied": "retain_scope_metadata_without_queue_materialization",
        }
    return {
        "approval_request_lane": "route_recourse_review_queue",
        "approval_scope_requested": "Allow Orthopaedic route recourse row to become a non-mutating source-replacement review queue item.",
        "required_queue_boundary_if_approved": "Queue rows may include route hashes and recourse status only; no unresolved-gap closure or URL rewrite.",
        "next_artifact_if_approved": "vanderbilt_route_recourse_review_queue",
        "next_artifact_if_denied": "retain_route_recourse_without_queue_materialization",
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
        + " CANDIDATE_QUEUE_ROWS "
        + str(summary["by_approval_request_lane"].get("candidate_fingerprint_review_queue", 0))
        + " SCOPE_QUEUE_ROWS "
        + str(summary["by_approval_request_lane"].get("linked_scope_metadata_review_queue", 0))
        + " RECOURSE_QUEUE_ROWS "
        + str(summary["by_approval_request_lane"].get("route_recourse_review_queue", 0))
        + " SOURCE_ROWSET_SHA256 "
        + SOURCE_ROWSET_SHA256
        + " VERIFICATION_ROWSET_SHA256 "
        + VERIFICATION_ROWSET_SHA256
        + " ROWSET_SHA256 "
        + str(summary["rowset_sha256"])
    )


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Candidate Review Queue Approval Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Candidate Review Queue Approval Packet",
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
            "| program | output kind | request lane | queue if approved |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows[:200]:
        lines.append(
            "| {program_name} | {output_kind} | {approval_request_lane} | {next_artifact_if_approved} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-line", default="", help="Exact GBrain approval line, if returned.")
    parser.add_argument("--denial-line", default="", help="Exact GBrain denial line, if returned.")
    parser.add_argument("--denial-recourse", default="", help="Concise recourse extracted from GBrain denial.")
    args = parser.parse_args()

    source_summary, verification_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected candidate parser output JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        request = classify(source)
        rows.append(
            {
                "approval_packet_key": stable_key("vanderbilt_candidate_review_queue_approval", source.get("parser_output_key"), request["approval_request_lane"]),
                "source_parser_output_key": source.get("parser_output_key"),
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "output_kind": source.get("output_kind"),
                "approval_request_lane": request["approval_request_lane"],
                "approval_scope_requested": request["approval_scope_requested"],
                "queue_materialization_allowed_if_approved": "true",
                "person_ingestion_allowed_if_approved": "false",
                "accepted_person_row_allowed_if_approved": "false",
                "required_queue_boundary_if_approved": request["required_queue_boundary_if_approved"],
                "next_artifact_if_approved": request["next_artifact_if_approved"],
                "next_artifact_if_denied": request["next_artifact_if_denied"],
                "candidate_fingerprint_sha256": source.get("candidate_fingerprint_sha256"),
                "candidate_source_kind": source.get("candidate_source_kind"),
                "content_sha256": source.get("content_sha256"),
                "visible_text_sha256": source.get("visible_text_sha256"),
                "evidence_json": dumps(
                    {
                        "source_candidate_output_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "verification_rowset_sha256": VERIFICATION_ROWSET_SHA256,
                        "accepted_person_row": source.get("accepted_person_row"),
                        "raw_candidate_names_committed": False,
                        "raw_candidate_hrefs_committed": False,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (str(item["approval_request_lane"]), str(item["program_name"]), str(item["source_parser_output_key"])))
    by_lane = Counter(str(row["approval_request_lane"]) for row in rows)
    by_next = Counter(str(row["next_artifact_if_approved"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_candidate_parser_outputs": str(SOURCE_JSON.relative_to(ROOT)),
        "source_candidate_parser_output_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_candidate_parser_output_rowset_sha256": SOURCE_ROWSET_SHA256,
        "verification_summary": str(VERIFICATION_SUMMARY.relative_to(ROOT)),
        "verification_rowset_sha256": VERIFICATION_ROWSET_SHA256,
        "source_parser_output_rows": source_summary.get("parser_output_rows"),
        "source_candidate_fingerprint_rows": source_summary.get("candidate_fingerprint_rows"),
        "approval_rows": len(rows),
        "by_approval_request_lane": dict(sorted(by_lane.items())),
        "by_next_artifact_if_approved": dict(sorted(by_next.items())),
        "mutation_allowed": False,
        "queue_materialization_allowed": False,
        "person_ingestion_allowed": False,
        "accepted_person_row_allowed": False,
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
        summary["gbrain_approval_status"] = "approved_exact_non_mutating_review_queue_materialization"
        summary["queue_materialization_allowed"] = True
    elif DENIAL_EFFECT in args.denial_line:
        summary["gbrain_approval_status"] = "denied"
        summary["gbrain_denial_line"] = args.denial_line
        summary["gbrain_denial_recourse"] = args.denial_recourse or "Resolve the GBrain blocker and resubmit this exact review-queue boundary."

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["approval_rows", "gbrain_approval_status", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
