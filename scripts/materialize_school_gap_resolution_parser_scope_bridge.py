#!/usr/bin/env python3
"""Bridge the targeted gap review packet to existing Vanderbilt parser/scope packets."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

TARGETED_REVIEW_CSV = ARTIFACTS / "school_gap_resolution_targeted_review_packet.csv"
TARGETED_REVIEW_SUMMARY = ARTIFACTS / "school_gap_resolution_targeted_review_packet_summary.json"
TARGETED_REVIEW_VALIDATION = ARTIFACTS / "school_gap_resolution_targeted_review_packet_validation_summary.json"

PARSER_SCOPE_REVIEW_CSV = ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet.csv"
PARSER_SCOPE_REVIEW_SUMMARY = ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet_summary.json"
ROUTE_PACKET_CSV = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet.csv"
ROUTE_PACKET_SUMMARY = ARTIFACTS / "vanderbilt_targeted_route_parser_scope_packet_summary.json"
DECISION_PACKET_CSV = ARTIFACTS / "vanderbilt_parser_scope_decision_packets.csv"
DECISION_PACKET_SUMMARY = ARTIFACTS / "vanderbilt_parser_scope_decision_packet_summary.json"

OUT_CSV = ARTIFACTS / "school_gap_resolution_parser_scope_bridge.csv"
OUT_JSON = ARTIFACTS / "school_gap_resolution_parser_scope_bridge.json"
OUT_SUMMARY = ARTIFACTS / "school_gap_resolution_parser_scope_bridge_summary.json"
OUT_MD = RESEARCH / "school-gap-resolution-parser-scope-bridge-2026-06-09.md"

TARGETED_REVIEW_ROWSET = "d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607"
PARSER_SCOPE_REVIEW_ROWSET = "dd7ba52cefcec632da434810653bce1b106696ca9a9d94fe3e517f206ae50785"
ROUTE_PACKET_ROWSET = "9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3"
DECISION_PACKET_ROWSET = "aa94351eae7a7309d2b760a891f69538d8a8998058fc1ceb24af3d2b918644b8"

MUTATION_POLICY = (
    "Non-mutating bridge from the public targeted Vanderbilt gap review packet to existing parser/scope packets. "
    "It records coverage, expansion, and remaining approval gates only. It does not regenerate parser/scope "
    "approval packets, accept parsers, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept "
    "enrichment facts, or collapse identities."
)

FIELDS = [
    "bridge_key",
    "gap_key",
    "program_key",
    "program_name",
    "targeted_review_action",
    "targeted_candidate_url",
    "targeted_review_status",
    "parser_scope_review_rows",
    "route_packet_rows",
    "decision_packet_rows",
    "bridge_status",
    "coverage_status",
    "downstream_scope_summary",
    "next_required_approval",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "parser_acceptance_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"bridge_key", "evidence_json", "mutation_policy", "generated_at"}
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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("bridge_key", "")))
    ]
    return sha256_text(dumps(material))


def verify_boundaries() -> None:
    targeted_summary = read_json(TARGETED_REVIEW_SUMMARY)
    targeted_validation = read_json(TARGETED_REVIEW_VALIDATION)
    parser_summary = read_json(PARSER_SCOPE_REVIEW_SUMMARY)
    route_summary = read_json(ROUTE_PACKET_SUMMARY)
    decision_summary = read_json(DECISION_PACKET_SUMMARY)
    if not all(isinstance(item, dict) for item in [targeted_summary, targeted_validation, parser_summary, route_summary, decision_summary]):
        raise SystemExit("Expected bridge source summaries to be JSON objects.")
    checks = {
        "targeted_rowset": targeted_summary.get("rowset_sha256") == TARGETED_REVIEW_ROWSET,
        "targeted_rows": targeted_summary.get("review_packet_rows") == 113
        and targeted_summary.get("filled_review_rows") == 19
        and targeted_summary.get("mutation_allowed") is False,
        "targeted_validation": targeted_validation.get("rowset_sha256") == TARGETED_REVIEW_ROWSET
        and targeted_validation.get("valid_non_mutating_rows") == 19
        and targeted_validation.get("invalid_rows") == 0
        and targeted_validation.get("mutation_allowed") is False,
        "parser_scope_review_rowset": parser_summary.get("rowset_sha256") == PARSER_SCOPE_REVIEW_ROWSET
        and parser_summary.get("review_rows") == 20
        and parser_summary.get("mutation_allowed") is False,
        "route_packet_rowset": route_summary.get("rowset_sha256") == ROUTE_PACKET_ROWSET
        and route_summary.get("packet_rows") == 20
        and route_summary.get("gbrain_approval_status") == "approved_exact_non_mutating_next_artifact_lane"
        and route_summary.get("mutation_allowed") is False,
        "decision_packet_rowset": decision_summary.get("rowset_sha256") == DECISION_PACKET_ROWSET
        and decision_summary.get("decision_rows") == 20
        and decision_summary.get("mutation_allowed") is False
        and decision_summary.get("parser_acceptance_allowed") is False
        and decision_summary.get("person_ingestion_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected parser/scope bridge source boundary: " + dumps(checks))


def index_by_program(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_program: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_program[row.get("program_key", "")].append(row)
    return dict(by_program)


def semicolon(values: list[str]) -> str:
    return "; ".join(value for value in values if value)


def bridge_status(parser_rows: list[dict[str, str]], route_rows: list[dict[str, str]], decision_rows: list[dict[str, str]]) -> tuple[str, str]:
    if not parser_rows:
        return "missing_parser_scope_review_rows", "not_covered_by_existing_parser_scope_chain"
    if not route_rows:
        return "parser_scope_review_only", "needs_route_observation_or_approval_request"
    if not decision_rows:
        return "route_packet_only", "needs_parser_scope_decision_packet"
    if len(route_rows) > len(parser_rows) or len(decision_rows) > len(parser_rows):
        return "covered_with_downstream_expansion", "covered_by_existing_parser_scope_chain_with_expansion"
    return "covered_exact", "covered_by_existing_parser_scope_chain"


def next_approval(decision_rows: list[dict[str, str]]) -> str:
    approvals = sorted({row.get("next_required_approval", "") for row in decision_rows if row.get("next_required_approval")})
    return semicolon(approvals) or "exact_parser_scope_review_packet_required"


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    lines = [
        "---",
        "type: research-checkpoint",
        "title: School Gap Resolution Parser Scope Bridge",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# School Gap Resolution Parser Scope Bridge",
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
        "## Bridge Rows",
        "",
        "| program | bridge status | parser rows | route rows | decision rows | next approval |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {program_name} | {bridge_status} | {parser_scope_review_rows} | {route_packet_rows} | {decision_packet_rows} | {next_required_approval} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    verify_boundaries()
    targeted_rows = [
        row for row in read_csv_rows(TARGETED_REVIEW_CSV) if row.get("proposed_non_mutating_review_action")
    ]
    parser_by_program = index_by_program(read_csv_rows(PARSER_SCOPE_REVIEW_CSV))
    route_by_program = index_by_program(read_csv_rows(ROUTE_PACKET_CSV))
    decision_by_program = index_by_program(read_csv_rows(DECISION_PACKET_CSV))
    if len(targeted_rows) != 19:
        raise SystemExit("Expected exactly 19 filled targeted review rows.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for target in sorted(targeted_rows, key=lambda item: (item.get("program_name", ""), item.get("gap_key", ""))):
        program_key = target.get("program_key", "")
        parser_rows = parser_by_program.get(program_key, [])
        route_rows = route_by_program.get(program_key, [])
        decision_rows = decision_by_program.get(program_key, [])
        status, coverage = bridge_status(parser_rows, route_rows, decision_rows)
        decision_lanes = sorted({row.get("decision_lane", "") for row in decision_rows if row.get("decision_lane")})
        route_lanes = sorted({row.get("approval_request_lane", "") for row in route_rows if row.get("approval_request_lane")})
        rows.append(
            {
                "bridge_key": stable_key("school_gap_resolution_parser_scope_bridge", target.get("review_template_key"), program_key),
                "gap_key": target.get("gap_key", ""),
                "program_key": program_key,
                "program_name": target.get("program_name", ""),
                "targeted_review_action": target.get("proposed_non_mutating_review_action", ""),
                "targeted_candidate_url": target.get("proposed_candidate_official_url", ""),
                "targeted_review_status": target.get("template_row_status", ""),
                "parser_scope_review_rows": len(parser_rows),
                "route_packet_rows": len(route_rows),
                "decision_packet_rows": len(decision_rows),
                "bridge_status": status,
                "coverage_status": coverage,
                "downstream_scope_summary": semicolon(decision_lanes or route_lanes),
                "next_required_approval": next_approval(decision_rows),
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "parser_acceptance_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "evidence_json": dumps(
                    {
                        "source_targeted_review_rowset_sha256": TARGETED_REVIEW_ROWSET,
                        "source_parser_scope_review_rowset_sha256": PARSER_SCOPE_REVIEW_ROWSET,
                        "source_route_packet_rowset_sha256": ROUTE_PACKET_ROWSET,
                        "source_decision_packet_rowset_sha256": DECISION_PACKET_ROWSET,
                        "parser_scope_review_keys": [row.get("review_packet_key", "") for row in parser_rows],
                        "route_packet_keys": [row.get("packet_key", "") for row in route_rows],
                        "decision_packet_keys": [row.get("decision_packet_key", "") for row in decision_rows],
                        "candidate_evidence_only": True,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    by_bridge_status = Counter(str(row["bridge_status"]) for row in rows)
    by_coverage_status = Counter(str(row["coverage_status"]) for row in rows)
    by_next_required_approval = Counter(str(row["next_required_approval"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_targeted_review_rowset_sha256": TARGETED_REVIEW_ROWSET,
        "source_parser_scope_review_rowset_sha256": PARSER_SCOPE_REVIEW_ROWSET,
        "source_route_packet_rowset_sha256": ROUTE_PACKET_ROWSET,
        "source_decision_packet_rowset_sha256": DECISION_PACKET_ROWSET,
        "bridge_rows": len(rows),
        "targeted_review_rows_represented": len(targeted_rows),
        "parser_scope_review_rows_represented": sum(int(row["parser_scope_review_rows"]) for row in rows),
        "route_packet_rows_represented": sum(int(row["route_packet_rows"]) for row in rows),
        "decision_packet_rows_represented": sum(int(row["decision_packet_rows"]) for row in rows),
        "by_bridge_status": dict(sorted(by_bridge_status.items())),
        "by_coverage_status": dict(sorted(by_coverage_status.items())),
        "by_next_required_approval": dict(sorted(by_next_required_approval.items())),
        "mutation_allowed": False,
        "parser_acceptance_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    if (
        summary["bridge_rows"] != 19
        or summary["parser_scope_review_rows_represented"] != 20
        or summary["route_packet_rows_represented"] != 20
        or summary["decision_packet_rows_represented"] != 20
    ):
        raise SystemExit("Parser/scope bridge failed coverage checks: " + dumps(summary))

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["bridge_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
