#!/usr/bin/env python3
"""Bridge parser/scope coverage to candidate-only Vanderbilt parser outputs."""

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

BRIDGE_CSV = ARTIFACTS / "school_gap_resolution_parser_scope_bridge.csv"
BRIDGE_SUMMARY = ARTIFACTS / "school_gap_resolution_parser_scope_bridge_summary.json"
APPROVAL_CSV = ARTIFACTS / "vanderbilt_parser_scope_implementation_approval_packet.csv"
APPROVAL_SUMMARY = ARTIFACTS / "vanderbilt_parser_scope_implementation_approval_packet_summary.json"
OUTPUT_CSV = ARTIFACTS / "vanderbilt_candidate_only_parser_outputs.csv"
OUTPUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_only_parser_output_summary.json"
VERIFICATION_SUMMARY = ARTIFACTS / "vanderbilt_candidate_parser_output_verification_summary.json"

OUT_CSV = ARTIFACTS / "school_gap_resolution_candidate_output_bridge.csv"
OUT_JSON = ARTIFACTS / "school_gap_resolution_candidate_output_bridge.json"
OUT_SUMMARY = ARTIFACTS / "school_gap_resolution_candidate_output_bridge_summary.json"
OUT_MD = RESEARCH / "school-gap-resolution-candidate-output-bridge-2026-06-09.md"

PARSER_SCOPE_BRIDGE_ROWSET = "942d131072d56524c9e19832c084b9e2520e43e783e3a9c0c6e2ae30c0f06912"
IMPLEMENTATION_APPROVAL_ROWSET = "0ce935b64a7eb2153b4fb4b5a8cca47034bab839aa932c8951c29d3bda363b40"
CANDIDATE_OUTPUT_ROWSET = "2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba"
CANDIDATE_OUTPUT_VERIFICATION_ROWSET = "918556f5b5a33b5d8e7181ed6654a9b7773b8c8a24f09f9a23b06c7157d39fe2"

MUTATION_POLICY = (
    "Non-mutating bridge from Vanderbilt parser/scope bridge rows to approved candidate-only parser diagnostics. "
    "It records implementation approval coverage, candidate fingerprint counts, scope metadata, recourse rows, "
    "and verification status only. It does not accept parser outputs as people, ingest people, close denominators, "
    "verify Vanderbilt, rewrite URLs, accept enrichment facts, publish raw names, or collapse identities."
)

FIELDS = [
    "candidate_output_bridge_key",
    "gap_key",
    "program_key",
    "program_name",
    "parser_scope_bridge_status",
    "implementation_approval_rows",
    "candidate_output_rows",
    "candidate_fingerprint_rows",
    "scope_metadata_rows",
    "route_recourse_rows",
    "candidate_output_status",
    "candidate_output_coverage_status",
    "next_required_approval",
    "accepted_person_rows",
    "parser_acceptance_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]
ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"candidate_output_bridge_key", "evidence_json", "mutation_policy", "generated_at"}
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
        for row in sorted(rows, key=lambda item: str(item.get("candidate_output_bridge_key", "")))
    ]
    return sha256_text(dumps(material))


def verify_boundaries() -> None:
    bridge = read_json(BRIDGE_SUMMARY)
    approval = read_json(APPROVAL_SUMMARY)
    output = read_json(OUTPUT_SUMMARY)
    verification = read_json(VERIFICATION_SUMMARY)
    if not all(isinstance(item, dict) for item in [bridge, approval, output, verification]):
        raise SystemExit("Expected candidate-output bridge source summaries to be JSON objects.")
    checks = {
        "bridge_rowset": bridge.get("rowset_sha256") == PARSER_SCOPE_BRIDGE_ROWSET
        and bridge.get("bridge_rows") == 19
        and bridge.get("mutation_allowed") is False
        and bridge.get("parser_acceptance_allowed") is False,
        "implementation_approval_rowset": approval.get("rowset_sha256") == IMPLEMENTATION_APPROVAL_ROWSET
        and approval.get("approval_rows") == 20
        and approval.get("gbrain_approval_status") == "approved_exact_candidate_only_implementation_scope_recourse"
        and approval.get("mutation_allowed") is False
        and approval.get("person_ingestion_allowed") is False,
        "candidate_output_rowset": output.get("rowset_sha256") == CANDIDATE_OUTPUT_ROWSET
        and output.get("parser_output_rows") == 159
        and output.get("candidate_fingerprint_rows") == 155
        and output.get("accepted_person_rows") == 0
        and output.get("person_ingestion_allowed") is False,
        "candidate_output_verification": verification.get("rowset_sha256") == CANDIDATE_OUTPUT_VERIFICATION_ROWSET
        and verification.get("verification_rows") == 9
        and verification.get("pass_rows") == 9
        and verification.get("fail_rows") == 0
        and verification.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected candidate-output bridge source boundary: " + dumps(checks))


def index_by_program(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_program: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_program[row.get("program_key", "")].append(row)
    return dict(by_program)


def semicolon(values: list[str]) -> str:
    return "; ".join(value for value in values if value)


def output_status(output_rows: list[dict[str, str]], approval_rows: list[dict[str, str]]) -> tuple[str, str, str]:
    if not approval_rows:
        return (
            "missing_implementation_approval_rows",
            "not_covered_by_candidate_output_chain",
            "exact_candidate_only_implementation_approval_required",
        )
    if not output_rows:
        return (
            "implementation_approved_no_candidate_outputs",
            "approval_present_without_candidate_outputs",
            "candidate_only_parser_output_or_recourse_required",
        )
    output_kinds = sorted({row.get("output_kind", "") for row in output_rows})
    if "candidate_fingerprint" in output_kinds:
        return (
            "candidate_fingerprints_verified",
            "covered_by_verified_candidate_only_outputs",
            "exact_candidate_review_queue_or_acceptance_packet_required",
        )
    if "scope_metadata" in output_kinds:
        return (
            "scope_metadata_verified",
            "covered_by_verified_scope_metadata",
            "exact_scope_disposition_acceptance_or_parser_build_approval_required",
        )
    return (
        "recourse_or_diagnostic_verified",
        "covered_by_verified_recourse_or_diagnostic_output",
        "exact_route_recourse_or_unresolved_gap_packet_required",
    )


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    lines = [
        "---",
        "type: research-checkpoint",
        "title: School Gap Resolution Candidate Output Bridge",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# School Gap Resolution Candidate Output Bridge",
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
        "| program | output status | candidates | scope | recourse | next approval |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {program_name} | {candidate_output_status} | {candidate_fingerprint_rows} | {scope_metadata_rows} | {route_recourse_rows} | {next_required_approval} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    verify_boundaries()
    bridge_rows = read_csv_rows(BRIDGE_CSV)
    approval_by_program = index_by_program(read_csv_rows(APPROVAL_CSV))
    output_by_program = index_by_program(read_csv_rows(OUTPUT_CSV))
    if len(bridge_rows) != 19:
        raise SystemExit("Expected exactly 19 parser/scope bridge rows.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for bridge in sorted(bridge_rows, key=lambda item: (item.get("program_name", ""), item.get("gap_key", ""))):
        program_key = bridge.get("program_key", "")
        approval_rows = approval_by_program.get(program_key, [])
        output_rows = output_by_program.get(program_key, [])
        fingerprint_rows = [row for row in output_rows if row.get("output_kind") == "candidate_fingerprint"]
        scope_rows = [row for row in output_rows if row.get("output_kind") == "scope_metadata"]
        recourse_rows = [row for row in output_rows if row.get("output_kind") == "route_recourse"]
        status, coverage, next_approval = output_status(output_rows, approval_rows)
        output_kinds = sorted({row.get("output_kind", "") for row in output_rows if row.get("output_kind")})
        parser_families = sorted({row.get("parser_family", "") for row in output_rows if row.get("parser_family")})
        rows.append(
            {
                "candidate_output_bridge_key": stable_key(
                    "school_gap_resolution_candidate_output_bridge",
                    bridge.get("bridge_key", ""),
                    program_key,
                ),
                "gap_key": bridge.get("gap_key", ""),
                "program_key": program_key,
                "program_name": bridge.get("program_name", ""),
                "parser_scope_bridge_status": bridge.get("bridge_status", ""),
                "implementation_approval_rows": len(approval_rows),
                "candidate_output_rows": len(output_rows),
                "candidate_fingerprint_rows": len(fingerprint_rows),
                "scope_metadata_rows": len(scope_rows),
                "route_recourse_rows": len(recourse_rows),
                "candidate_output_status": status,
                "candidate_output_coverage_status": coverage,
                "next_required_approval": next_approval,
                "accepted_person_rows": 0,
                "parser_acceptance_allowed": "false",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "evidence_json": dumps(
                    {
                        "source_parser_scope_bridge_rowset_sha256": PARSER_SCOPE_BRIDGE_ROWSET,
                        "source_implementation_approval_rowset_sha256": IMPLEMENTATION_APPROVAL_ROWSET,
                        "source_candidate_output_rowset_sha256": CANDIDATE_OUTPUT_ROWSET,
                        "source_candidate_output_verification_rowset_sha256": CANDIDATE_OUTPUT_VERIFICATION_ROWSET,
                        "implementation_approval_keys": [row.get("approval_packet_key", "") for row in approval_rows],
                        "candidate_output_keys": [row.get("parser_output_key", "") for row in output_rows],
                        "output_kinds": output_kinds,
                        "parser_families": parser_families,
                        "candidate_evidence_only": True,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    by_status = Counter(str(row["candidate_output_status"]) for row in rows)
    by_coverage = Counter(str(row["candidate_output_coverage_status"]) for row in rows)
    by_next = Counter(str(row["next_required_approval"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_parser_scope_bridge_rowset_sha256": PARSER_SCOPE_BRIDGE_ROWSET,
        "source_implementation_approval_rowset_sha256": IMPLEMENTATION_APPROVAL_ROWSET,
        "source_candidate_output_rowset_sha256": CANDIDATE_OUTPUT_ROWSET,
        "source_candidate_output_verification_rowset_sha256": CANDIDATE_OUTPUT_VERIFICATION_ROWSET,
        "bridge_rows": len(rows),
        "implementation_approval_rows_represented": sum(int(row["implementation_approval_rows"]) for row in rows),
        "candidate_output_rows_represented": sum(int(row["candidate_output_rows"]) for row in rows),
        "candidate_fingerprint_rows_represented": sum(int(row["candidate_fingerprint_rows"]) for row in rows),
        "scope_metadata_rows_represented": sum(int(row["scope_metadata_rows"]) for row in rows),
        "route_recourse_rows_represented": sum(int(row["route_recourse_rows"]) for row in rows),
        "by_candidate_output_status": dict(sorted(by_status.items())),
        "by_candidate_output_coverage_status": dict(sorted(by_coverage.items())),
        "by_next_required_approval": dict(sorted(by_next.items())),
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
        or summary["implementation_approval_rows_represented"] != 20
        or summary["candidate_output_rows_represented"] != 159
        or summary["candidate_fingerprint_rows_represented"] != 155
    ):
        raise SystemExit("Candidate-output bridge failed coverage checks: " + dumps(summary))

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["bridge_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
