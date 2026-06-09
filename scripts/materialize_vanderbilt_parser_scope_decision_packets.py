#!/usr/bin/env python3
"""Materialize Vanderbilt parser-family specs and scope/recourse decision packets."""

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

SOURCE_JSON = ARTIFACTS / "vanderbilt_parser_scope_execution_evidence.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_parser_scope_execution_evidence_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_parser_scope_decision_packets.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_parser_scope_decision_packets.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_parser_scope_decision_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-parser-scope-decision-packets-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "db7e7c7b03c31c20a6b3b9c2a17da2d24cbf0c725f97872452db63a2e5942812"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt parser-family spec and scope/recourse decision packet. It turns approved execution "
    "evidence into parser-family specifications, scope dispositions, General Surgery rendered-review disposition, "
    "and route recourse decisions. It does not approve parser implementation as accepted people, person ingestion, "
    "training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label "
    "ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse."
)

FIELDS = [
    "decision_packet_key",
    "source_execution_evidence_key",
    "program_key",
    "program_name",
    "fetch_url",
    "parser_family",
    "approved_followup_artifact",
    "decision_lane",
    "decision_status",
    "parser_spec_family",
    "parser_spec_contract",
    "scope_decision",
    "recourse_decision",
    "candidate_entity_count",
    "candidate_group_count",
    "content_sha256",
    "visible_text_sha256",
    "parser_implementation_allowed",
    "parser_acceptance_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "next_required_approval",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_execution_evidence_key",
    "program_key",
    "program_name",
    "fetch_url",
    "parser_family",
    "approved_followup_artifact",
    "decision_lane",
    "decision_status",
    "parser_spec_family",
    "parser_spec_contract",
    "scope_decision",
    "recourse_decision",
    "candidate_entity_count",
    "candidate_group_count",
    "content_sha256",
    "visible_text_sha256",
    "parser_implementation_allowed",
    "parser_acceptance_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "next_required_approval",
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
        raise SystemExit("Expected Vanderbilt parser/scope execution evidence summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "execution_evidence_rows": summary.get("execution_evidence_rows") == 20,
        "hash_matches": summary.get("by_route_hash_matches_prior_observation", {}).get("true") == 20,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected parser/scope execution evidence boundary: {checks}")
    return summary


def parser_contract(row: dict[str, object]) -> str:
    family = str(row.get("parser_family") or "")
    if family == "vumc_pediatrics_person_listing_page":
        return "Candidate-only parser spec: count /person/ anchors and current/fellow signal sections; emit hashed candidate fingerprints only until person-ingestion approval."
    if family == "vumc_pediatrics_node_listing_page":
        return "Candidate-only parser spec: parse VUMC Pediatrics node roster region by current/fellow signals and profile anchors; emit counts/hashes only."
    if family == "vumc_medicine_division_fellows_shared_page":
        return "Shared-page parser spec: separate GI/Hepatology/Nutrition fellow sections from subspecialty scope before any source-specific parser implementation."
    if family == "vumc_pgy_listing_page":
        return "Candidate-only parser spec: parse PGY sections and person/profile anchors into counts and hashed candidate fingerprints only."
    if family == "vumc_general_surgery_current_residents_rendered_review":
        return "Rendered-review parser spec: inspect current-residents route for resident cards/sections and preserve candidate-only counts/hashes."
    if family == "vumc_orthopaedics_current_residents_page":
        return "Scope-disposition parser spec: confirm Orthopaedic current-residents same-program scope before parser-build review."
    return "Recourse/manual spec: preserve HTTP evidence and source-discovery route without parser implementation."


def classify_decision(row: dict[str, object]) -> dict[str, str]:
    followup = str(row.get("approved_followup_artifact") or "")
    family = str(row.get("parser_family") or "")
    program_name = str(row.get("program_name") or "")
    if followup == "source_specific_parser_build_review_packet":
        return {
            "decision_lane": "parser_family_spec",
            "decision_status": "candidate_only_parser_spec_ready_for_exact_implementation_approval",
            "parser_spec_family": family,
            "parser_spec_contract": parser_contract(row),
            "scope_decision": "same_program_current_roster_signal_for_parser_spec",
            "recourse_decision": "not_recourse",
            "next_required_approval": "exact_parser_implementation_or_candidate_extraction_approval_required",
        }
    if followup == "linked_route_scope_disposition_packet":
        if "orthopaedic" in program_name.lower():
            scope_decision = "same_program_current_residents_route_candidate_for_parser_build_review"
            status = "same_program_scope_disposition_ready"
        else:
            scope_decision = "shared_gastroenterology_fellows_route_requires_subscope_before_parser_build"
            status = "shared_source_scope_disposition_ready"
        return {
            "decision_lane": "linked_route_scope_decision",
            "decision_status": status,
            "parser_spec_family": family,
            "parser_spec_contract": parser_contract(row),
            "scope_decision": scope_decision,
            "recourse_decision": "not_recourse",
            "next_required_approval": "exact_scope_disposition_acceptance_or_parser_build_approval_required",
        }
    if followup == "general_surgery_rendered_parser_scope_packet":
        return {
            "decision_lane": "general_surgery_rendered_decision",
            "decision_status": "rendered_current_residents_parser_scope_ready",
            "parser_spec_family": family,
            "parser_spec_contract": parser_contract(row),
            "scope_decision": "general_surgery_current_residents_route_has_current_resident_signal",
            "recourse_decision": "not_recourse",
            "next_required_approval": "exact_general_surgery_parser_build_or_candidate_extraction_approval_required",
        }
    return {
        "decision_lane": "route_recourse_decision",
        "decision_status": "http_error_recourse_ready",
        "parser_spec_family": family,
        "parser_spec_contract": parser_contract(row),
        "scope_decision": "not_parser_scope_candidate",
        "recourse_decision": "retry_or_replace_retired_orthopaedic_match_route",
        "next_required_approval": "exact_route_replacement_or_unresolved_gap_closure_approval_required",
    }


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("decision_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Parser Scope Decision Packets",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Parser Scope Decision Packets",
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
        "## Decision Rows",
        "",
        "| program | lane | status | parser family | scope decision | next approval |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {program_name} | {decision_lane} | {decision_status} | {parser_spec_family} | {scope_decision} | {next_required_approval} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected Vanderbilt parser/scope execution evidence JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        decision = classify_decision(source)
        rows.append(
            {
                "decision_packet_key": stable_key("vanderbilt_parser_scope_decision", source.get("execution_evidence_key"), decision["decision_lane"]),
                "source_execution_evidence_key": source.get("execution_evidence_key"),
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "fetch_url": source.get("fetch_url"),
                "parser_family": source.get("parser_family"),
                "approved_followup_artifact": source.get("approved_followup_artifact"),
                "decision_lane": decision["decision_lane"],
                "decision_status": decision["decision_status"],
                "parser_spec_family": decision["parser_spec_family"],
                "parser_spec_contract": decision["parser_spec_contract"],
                "scope_decision": decision["scope_decision"],
                "recourse_decision": decision["recourse_decision"],
                "candidate_entity_count": source.get("candidate_entity_count"),
                "candidate_group_count": source.get("candidate_group_count"),
                "content_sha256": source.get("content_sha256"),
                "visible_text_sha256": source.get("visible_text_sha256"),
                "parser_implementation_allowed": "false",
                "parser_acceptance_allowed": "false",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "next_required_approval": decision["next_required_approval"],
                "evidence_json": dumps(
                    {
                        "source_execution_evidence_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "source_execution_evidence_key": source.get("execution_evidence_key"),
                        "parser_probe_status": source.get("parser_probe_status"),
                        "route_hash_matches_prior_observation": source.get("route_hash_matches_prior_observation"),
                        "current_signal_count": source.get("current_signal_count"),
                        "resident_signal_count": source.get("resident_signal_count"),
                        "fellow_signal_count": source.get("fellow_signal_count"),
                        "pgy_signal_count": source.get("pgy_signal_count"),
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (str(item["decision_lane"]), str(item["program_name"]), str(item["fetch_url"])))
    by_lane = Counter(str(row["decision_lane"]) for row in rows)
    by_status = Counter(str(row["decision_status"]) for row in rows)
    by_next_approval = Counter(str(row["next_required_approval"]) for row in rows)
    by_parser_family = Counter(str(row["parser_spec_family"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_execution_evidence": str(SOURCE_JSON.relative_to(ROOT)),
        "source_execution_evidence_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_execution_evidence_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_execution_evidence_rows": source_summary.get("execution_evidence_rows"),
        "decision_rows": len(rows),
        "by_decision_lane": dict(sorted(by_lane.items())),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_next_required_approval": dict(sorted(by_next_approval.items())),
        "by_parser_family": dict(sorted(by_parser_family.items())),
        "mutation_allowed": False,
        "parser_implementation_allowed": False,
        "parser_acceptance_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["decision_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
