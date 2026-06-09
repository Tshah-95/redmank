#!/usr/bin/env python3
"""Materialize verification documentation for the Vanderbilt route parser/scope packet."""

from __future__ import annotations

import csv
import hashlib
import json
import argparse
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

TARGET_CSV = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet.csv"
TARGET_JSON = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet.json"
TARGET_SUMMARY = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet_summary.json"
TARGET_MD = RESEARCH / "vanderbilt-targeted-route-parser-scope-packet-2026-06-09.md"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_targeted_route_observation_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_route_parser_scope_verification_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_route_parser_scope_verification_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_route_parser_scope_verification_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-route-parser-scope-verification-packet-2026-06-09.md"

TARGET_ROWSET_SHA256 = "9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3"
SOURCE_ROWSET_SHA256 = "f547a298bf0efdaba630aa9d184ecd85979d0356039bbbd92d3c2fd026745258"
APPROVAL_EFFECT = "vanderbilt_targeted_route_parser_scope_verification_registration_approved"
DENIAL_EFFECT = "vanderbilt_targeted_route_parser_scope_verification_registration_denied"

MUTATION_POLICY = (
    "Non-mutating verification documentation for the Vanderbilt route parser/scope packet. It registers checks, "
    "counts, rowsets, and public-safety evidence for a previously denied approval request. It does not approve "
    "parser acceptance, parser-build execution, person ingestion, training-state mutation, denominator closure, "
    "Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump "
    "publication, or unique-person identity collapse."
)

FIELDS = [
    "verification_key",
    "check_name",
    "check_status",
    "expected_value",
    "observed_value",
    "evidence",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = ["check_name", "check_status", "expected_value", "observed_value", "evidence"]

NAMEISH_RE = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")

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


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("verification_key", "")))
    ]
    return sha256_text(dumps(material))


def add_check(
    rows: list[dict[str, object]],
    generated_at: str,
    check_name: str,
    passed: bool,
    expected_value: object,
    observed_value: object,
    evidence: object,
) -> None:
    rows.append(
        {
            "verification_key": stable_key("vanderbilt_route_parser_scope_verification", check_name, expected_value, observed_value),
            "check_name": check_name,
            "check_status": "pass" if passed else "fail",
            "expected_value": dumps(expected_value),
            "observed_value": dumps(observed_value),
            "evidence": dumps(evidence),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
    )


def approval_line(summary: dict[str, object]) -> str:
    return (
        "APPROVE "
        + APPROVAL_EFFECT
        + " VERIFICATION_ROWS "
        + str(summary["verification_rows"])
        + " PASS_ROWS "
        + str(summary["by_check_status"].get("pass", 0))
        + " TARGET_PACKET_ROWS "
        + str(summary["target_packet_rows"])
        + " TARGET_ROWSET_SHA256 "
        + TARGET_ROWSET_SHA256
        + " ROWSET_SHA256 "
        + str(summary["rowset_sha256"])
    )


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Route Parser Scope Verification Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Route Parser Scope Verification Packet",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Required Approval Line",
        "",
        "`" + str(summary["required_approval_line"]) + "`",
        "",
        "This registration only verifies the parser/scope packet artifact and rowset. It does not approve parser-build execution or any person/denominator mutation.",
        "",
        "GBrain registration status: `" + str(summary["gbrain_registration_status"]) + "`.",
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
        "## Checks",
        "",
        "| check | status | observed |",
        "| --- | --- | --- |",
        ]
    )
    for row in rows:
        lines.append("| {check_name} | {check_status} | {observed_value} |".format(**row))
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-line", default="", help="Exact GBrain approval line, if returned.")
    parser.add_argument("--denial-line", default="", help="Exact GBrain denial line, if returned.")
    parser.add_argument("--denial-recourse", default="", help="Concise recourse extracted from the GBrain denial.")
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    target_summary = read_json(TARGET_SUMMARY)
    source_summary = read_json(SOURCE_SUMMARY)
    target_rows = read_json(TARGET_JSON)
    if not isinstance(target_summary, dict) or not isinstance(source_summary, dict) or not isinstance(target_rows, list):
        raise SystemExit("Expected target/source summaries and target packet JSON.")

    by_lane = Counter(str(row.get("approval_request_lane", "")) for row in target_rows)
    by_signal = Counter(str(row.get("candidate_route_signal", "")) for row in target_rows)
    route_signal_name_hits = []
    for row in target_rows:
        hits = NAMEISH_RE.findall(str(row.get("route_signal_json", "")))
        if hits:
            route_signal_name_hits.append({"program_name": row.get("program_name"), "hits": hits[:5]})

    rows: list[dict[str, object]] = []
    add_check(
        rows,
        generated_at,
        "target_packet_rowset_matches_summary",
        target_summary.get("rowset_sha256") == TARGET_ROWSET_SHA256,
        TARGET_ROWSET_SHA256,
        target_summary.get("rowset_sha256"),
        {"summary": str(TARGET_SUMMARY.relative_to(ROOT))},
    )
    add_check(
        rows,
        generated_at,
        "source_route_observation_rowset_matches_summary",
        target_summary.get("source_route_observation_rowset_sha256") == SOURCE_ROWSET_SHA256
        and source_summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        SOURCE_ROWSET_SHA256,
        {
            "target_summary_source_rowset": target_summary.get("source_route_observation_rowset_sha256"),
            "source_summary_rowset": source_summary.get("rowset_sha256"),
        },
        {"source_summary": str(SOURCE_SUMMARY.relative_to(ROOT))},
    )
    add_check(
        rows,
        generated_at,
        "target_packet_rows_and_lanes_match",
        target_summary.get("packet_rows") == 20
        and by_lane == Counter(
            {
                "exact_parser_build_review": 15,
                "linked_route_scope_disposition_review": 3,
                "rendered_general_surgery_parser_scope_review": 1,
                "route_recourse_review": 1,
            }
        ),
        {"packet_rows": 20, "by_lane": {"exact_parser_build_review": 15, "linked_route_scope_disposition_review": 3, "rendered_general_surgery_parser_scope_review": 1, "route_recourse_review": 1}},
        {"packet_rows": target_summary.get("packet_rows"), "by_lane": dict(sorted(by_lane.items()))},
        {"target_packet": str(TARGET_CSV.relative_to(ROOT))},
    )
    add_check(
        rows,
        generated_at,
        "route_signal_counts_match",
        by_signal
        == Counter(
            {
                "official_route_current_roster_signal_needs_parser_scope_packet": 19,
                "http_error_needs_retry_or_recourse": 1,
            }
        ),
        {"official_route_current_roster_signal_needs_parser_scope_packet": 19, "http_error_needs_retry_or_recourse": 1},
        dict(sorted(by_signal.items())),
        {"target_packet": str(TARGET_JSON.relative_to(ROOT))},
    )
    add_check(
        rows,
        generated_at,
        "mutation_boundary_preserved",
        target_summary.get("mutation_allowed") is False and source_summary.get("mutation_allowed") is False,
        {"target_mutation_allowed": False, "source_mutation_allowed": False},
        {"target_mutation_allowed": target_summary.get("mutation_allowed"), "source_mutation_allowed": source_summary.get("mutation_allowed")},
        {"not_approved": target_summary.get("not_approved", [])},
    )
    add_check(
        rows,
        generated_at,
        "public_safety_no_raw_signal_names_in_route_signal_json",
        not route_signal_name_hits,
        [],
        route_signal_name_hits,
        {"scan": "NAMEISH_RE over route_signal_json only; program names are not treated as fetched person evidence"},
    )
    add_check(
        rows,
        generated_at,
        "gbrain_denial_recourse_recorded",
        target_summary.get("gbrain_approval_status") == "denied_needs_verification_documentation",
        "denied_needs_verification_documentation",
        target_summary.get("gbrain_approval_status"),
        {
            "denial_line": target_summary.get("gbrain_denial_line"),
            "denial_recourse": target_summary.get("gbrain_denial_recourse"),
        },
    )

    rows.sort(key=lambda item: str(item["check_name"]))
    by_status = Counter(str(row["check_status"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "target_packet_csv": str(TARGET_CSV.relative_to(ROOT)),
        "target_packet_json": str(TARGET_JSON.relative_to(ROOT)),
        "target_packet_summary": str(TARGET_SUMMARY.relative_to(ROOT)),
        "target_packet_markdown": str(TARGET_MD.relative_to(ROOT)),
        "target_packet_rows": target_summary.get("packet_rows"),
        "target_packet_rowset_sha256": TARGET_ROWSET_SHA256,
        "source_route_observation_rowset_sha256": SOURCE_ROWSET_SHA256,
        "verification_rows": len(rows),
        "by_check_status": dict(sorted(by_status.items())),
        "mutation_allowed": False,
        "gbrain_registration_status": "pending_exact_approval_line",
        "gbrain_approval_effect": APPROVAL_EFFECT,
        "gbrain_denial_effect": DENIAL_EFFECT,
        "gbrain_denial_line": "",
        "gbrain_denial_recourse": "",
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    summary["required_approval_line"] = approval_line(summary)
    if args.approval_line == summary["required_approval_line"]:
        summary["gbrain_registration_status"] = "approved_exact_verification_registration"
    elif DENIAL_EFFECT in args.denial_line:
        summary["gbrain_registration_status"] = "denied_needs_brain_capture"
        summary["gbrain_denial_line"] = args.denial_line
        summary["gbrain_denial_recourse"] = args.denial_recourse or (
            "Capture the target parser/scope packet, verification packet, and prior denial record into GBrain, then "
            "resubmit the same verification registration boundary."
        )

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["verification_rows", "by_check_status", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
