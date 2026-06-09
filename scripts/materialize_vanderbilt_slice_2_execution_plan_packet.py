#!/usr/bin/env python3
"""Materialize a no-fetch Vanderbilt slice-2 execution-plan packet."""

from __future__ import annotations

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

TRIAGE_CSV = ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.csv"
TRIAGE_SUMMARY = ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet_summary.json"
TRIAGE_CONTRACT_SUMMARY = ARTIFACTS / "vanderbilt_triage_slice_definition_contract_summary.json"
PACKET_CSV = ARTIFACTS / "school_gap_resolution_batch_packets.csv"
PACKET_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_packet_summary.json"
TARGETED_REVIEW_CSV = ARTIFACTS / "school_gap_resolution_targeted_review_packet.csv"
TARGETED_REVIEW_SUMMARY = ARTIFACTS / "school_gap_resolution_targeted_review_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-slice-2-execution-plan-packet-2026-06-09.md"

EXPECTED_TRIAGE_ROWSET = "b89f2278c96c18c70403099be2b18542bb0f59a4c50a53921f17fe83864b1391"
EXPECTED_TRIAGE_CONTRACT_ROWSET = "b8559206ae9341dae7c9136ddb6d83651ff84905feb74ec133992e822534416f"
EXPECTED_TARGETED_REVIEW_ROWSET = "d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607"
EXPECTED_TRIAGE_ORDER = "2"
EXPECTED_EXECUTION_ORDER = "1"
EXPECTED_BATCH_KEY = "school_gap_resolution_batch_e81d6de09bb3a988757d"
EXPECTED_PLAN_ROWS = 9
GBRAIN_ADVISORY_EFFECT = "gbrain_selected_vanderbilt_slice_2_execution_plan_packet_option_a_no_web_fetch"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt slice-2 execution-plan packet. It converts committed gap packet rows for triage "
    "order 2 / execution order 1 into no-fetch query, route-review, and packet-preparation instructions. It does "
    "not fetch web pages, fill reviewer decisions, apply patches, approve people, ingest people, close denominators, "
    "verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw dumps, or collapse identities."
)

PROHIBITED_MUTATIONS = [
    "person_ingestion",
    "parser_output_as_accepted_people",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "enrichment_acceptance",
    "raw_dump_publication",
    "unique_person_identity_collapse",
]

APPROVAL_REQUIRED_FOR = [
    "live_web_fetch_or_probe",
    "parser_acceptance",
    "person_ingestion",
    "denominator_closure",
    "vanderbilt_school_verification",
    "source_url_rewrite",
    "scope_closure",
    "identity_collapse",
]

FIELDS = [
    "execution_plan_key",
    "plan_order",
    "triage_order",
    "execution_order",
    "school_gap_resolution_batch_key",
    "gap_key",
    "program_key",
    "program_name",
    "program_type",
    "resolution_priority",
    "plan_lane",
    "plan_status",
    "denominator_url",
    "candidate_context_url",
    "candidate_context_title",
    "candidate_context_status",
    "supported_person_rows",
    "candidate_source_count",
    "approved_non_mutating_disposition_count",
    "targeted_packet_status",
    "source_discovery_query",
    "route_review_instruction",
    "packet_preparation_instruction",
    "recommended_output_artifact",
    "verification_command",
    "required_next_evidence",
    "web_fetch_allowed",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "approval_required_for",
    "prohibited_mutations",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"execution_plan_key", "evidence_json", "mutation_policy", "generated_at"}
]

PRIVATE_PATH_MARKERS = [
    "artifacts/data/gbrain_",
    "artifacts/data/browser_page_dumps/",
    "artifacts/data/debug_",
    "artifacts/data/raw/",
    ".playwright-mcp/",
    "inbox/",
    "reports/",
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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def int_value(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def semicolon(values: list[str]) -> str:
    return "; ".join(values)


def domain(url: str) -> str:
    return urlparse(url or "").netloc.lower()


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("execution_plan_key", "")))
    ]
    return sha256_text(dumps(material))


def verify_sources() -> tuple[dict[str, str], list[dict[str, str]], dict[str, str]]:
    triage_summary = read_json(TRIAGE_SUMMARY)
    triage_contract = read_json(TRIAGE_CONTRACT_SUMMARY)
    packet_summary = read_json(PACKET_SUMMARY)
    targeted_summary = read_json(TARGETED_REVIEW_SUMMARY)
    if not all(isinstance(item, dict) for item in [triage_summary, triage_contract, packet_summary, targeted_summary]):
        raise SystemExit("Expected slice-2 source summaries to be JSON objects.")
    checks = {
        "triage_rowset": triage_summary.get("rowset_sha256") == EXPECTED_TRIAGE_ROWSET,
        "triage_rows": triage_summary.get("triage_rows") == 21,
        "triage_mutation_false": triage_summary.get("mutation_allowed") is False,
        "triage_contract_rowset": triage_contract.get("rowset_sha256") == EXPECTED_TRIAGE_CONTRACT_ROWSET,
        "triage_contract_rows": triage_contract.get("contract_rows") == 4,
        "triage_contract_mutation_false": triage_contract.get("mutation_allowed") is False,
        "packet_rows": packet_summary.get("rows") == 113,
        "packet_batch_rows": packet_summary.get("batch_rows") == 21,
        "packet_mutation_false": packet_summary.get("mutation_allowed") is False,
        "targeted_review_rowset": targeted_summary.get("rowset_sha256") == EXPECTED_TARGETED_REVIEW_ROWSET,
        "targeted_review_mutation_false": targeted_summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected Vanderbilt slice-2 execution-plan source boundary: " + dumps(checks))

    triage_rows = read_csv_rows(TRIAGE_CSV)
    selected_triage = [
        row
        for row in triage_rows
        if row.get("triage_order") == EXPECTED_TRIAGE_ORDER and row.get("execution_order") == EXPECTED_EXECUTION_ORDER
    ]
    if len(selected_triage) != 1:
        raise SystemExit("Expected exactly one Vanderbilt triage row for slice 2 / execution order 1.")
    triage_row = selected_triage[0]
    if triage_row.get("school_gap_resolution_batch_key") != EXPECTED_BATCH_KEY or int_value(triage_row.get("gap_count")) != EXPECTED_PLAN_ROWS:
        raise SystemExit("Unexpected Vanderbilt slice-2 triage row boundary.")

    packet_rows = [
        row
        for row in read_csv_rows(PACKET_CSV)
        if row.get("execution_order") == EXPECTED_EXECUTION_ORDER
        and row.get("school_gap_resolution_batch_key") == EXPECTED_BATCH_KEY
    ]
    if len(packet_rows) != EXPECTED_PLAN_ROWS:
        raise SystemExit("Expected 9 committed packet rows for Vanderbilt slice 2.")
    targeted_by_gap = {row.get("gap_key", ""): row for row in read_csv_rows(TARGETED_REVIEW_CSV)}
    return triage_row, packet_rows, targeted_by_gap


def plan_lane(row: dict[str, str]) -> str:
    if row.get("best_evidence_status") == "manual_scope_review" and int_value(row.get("supported_person_rows")) > 0:
        return "related_scope_exclusion_then_target_program_source_discovery"
    if row.get("best_evidence_status") == "secondary_source_search_needed":
        return "broader_official_search_plan"
    return "manual_context_review_then_source_discovery"


def source_query(row: dict[str, str]) -> str:
    program = row.get("program_name", "")
    denom_domain = domain(row.get("denominator_url", ""))
    evidence_domain = domain(row.get("best_evidence_url", ""))
    domains = [value for value in [denom_domain, evidence_domain] if value]
    unique_domains = []
    for value in domains:
        if value not in unique_domains:
            unique_domains.append(value)
    domain_part = " OR ".join(f"site:{value}" for value in unique_domains) or "site:vumc.org"
    return f'({domain_part}) "{program}" current fellows residents roster Vanderbilt'


def route_instruction(row: dict[str, str]) -> str:
    lane = plan_lane(row)
    if lane == "related_scope_exclusion_then_target_program_source_discovery":
        return (
            "Treat the committed best-evidence URL as related-scope/context evidence only; do not reuse listed people "
            "for target-program truth. Search or inspect official target-program pages for a same-program current roster."
        )
    if lane == "broader_official_search_plan":
        return (
            "Use the denominator and existing context URLs as search anchors. Look for official current trainee roster "
            "routes before considering any no-public-roster recourse packet."
        )
    return "Review committed context and prepare a narrower official-source discovery packet for the target program."


def packet_instruction(row: dict[str, str]) -> str:
    lane = plan_lane(row)
    if lane == "broader_official_search_plan":
        return "If a candidate official route is found later, materialize a non-mutating source-discovery workbench row before any parser or acceptance packet."
    return "Preserve exclusion evidence and prepare a target-program source-discovery or scope-disposition packet; acceptance remains prohibited."


def output_path(row: dict[str, str]) -> str:
    safe = "".join(ch if ch.isalnum() else "_" for ch in row.get("program_name", "").lower()).strip("_")
    return f"/tmp/vanderbilt_slice_2_{safe[:64]}_execution_evidence.csv"


def build_rows(generated_at: str) -> list[dict[str, object]]:
    triage_row, packet_rows, targeted_by_gap = verify_sources()
    output: list[dict[str, object]] = []
    for row in sorted(packet_rows, key=lambda item: int_value(item.get("batch_packet_order"))):
        targeted = targeted_by_gap.get(row.get("gap_key", ""), {})
        lane = plan_lane(row)
        target_action = targeted.get("proposed_non_mutating_review_action", "")
        targeted_status = "already_in_targeted_review_packet" if target_action else "not_in_targeted_review_packet"
        output.append(
            {
                "execution_plan_key": stable_key(
                    "vanderbilt_slice_2_execution_plan",
                    row.get("gap_key"),
                    EXPECTED_TRIAGE_ROWSET,
                    GBRAIN_ADVISORY_EFFECT,
                ),
                "plan_order": int_value(row.get("batch_packet_order")),
                "triage_order": EXPECTED_TRIAGE_ORDER,
                "execution_order": EXPECTED_EXECUTION_ORDER,
                "school_gap_resolution_batch_key": EXPECTED_BATCH_KEY,
                "gap_key": row.get("gap_key", ""),
                "program_key": row.get("program_key", ""),
                "program_name": row.get("program_name", ""),
                "program_type": row.get("program_type", ""),
                "resolution_priority": int_value(row.get("resolution_priority")),
                "plan_lane": lane,
                "plan_status": "ready_for_no_fetch_execution_planning",
                "denominator_url": row.get("denominator_url", ""),
                "candidate_context_url": row.get("best_evidence_url", ""),
                "candidate_context_title": row.get("best_evidence_title", ""),
                "candidate_context_status": row.get("best_evidence_status", ""),
                "supported_person_rows": int_value(row.get("supported_person_rows")),
                "candidate_source_count": int_value(row.get("candidate_source_count")),
                "approved_non_mutating_disposition_count": int_value(
                    row.get("approved_non_mutating_disposition_count")
                ),
                "targeted_packet_status": targeted_status,
                "source_discovery_query": source_query(row),
                "route_review_instruction": route_instruction(row),
                "packet_preparation_instruction": packet_instruction(row),
                "recommended_output_artifact": output_path(row),
                "verification_command": "python3 scripts/materialize_vanderbilt_slice_2_execution_plan_packet.py",
                "required_next_evidence": row.get("required_next_evidence", ""),
                "web_fetch_allowed": "false",
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "approval_required_for": semicolon(APPROVAL_REQUIRED_FOR),
                "prohibited_mutations": semicolon(PROHIBITED_MUTATIONS),
                "evidence_json": dumps(
                    {
                        "gbrain_advisory_effect": GBRAIN_ADVISORY_EFFECT,
                        "source_triage_rowset_sha256": EXPECTED_TRIAGE_ROWSET,
                        "source_triage_contract_rowset_sha256": EXPECTED_TRIAGE_CONTRACT_ROWSET,
                        "source_targeted_review_rowset_sha256": EXPECTED_TARGETED_REVIEW_ROWSET,
                        "triage_row_key": triage_row.get("triage_packet_key", ""),
                        "source_batch_packet_key": row.get("school_gap_resolution_batch_packet_key", ""),
                        "targeted_packet_action": target_action,
                        "targeted_packet_candidate_url": targeted.get("proposed_candidate_official_url", ""),
                        "no_web_fetch_increment": True,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )
    return output


def private_marker_hits(rows: list[dict[str, object]]) -> list[str]:
    text = dumps(rows)
    return [marker for marker in PRIVATE_PATH_MARKERS if marker in text]


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Slice 2 Execution Plan Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Slice 2 Execution Plan Packet",
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
        "## Plan Rows",
        "",
        "| order | program | lane | context status | web fetch |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {plan_order} | {program_name} | {plan_lane} | {candidate_context_status} | {web_fetch_allowed} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows(generated_at)
    hits = private_marker_hits(rows)
    if hits:
        raise SystemExit("Vanderbilt slice-2 execution plan contains private artifact markers: " + ", ".join(hits))
    by_lane = Counter(str(row["plan_lane"]) for row in rows)
    by_context = Counter(str(row["candidate_context_status"]) for row in rows)
    by_targeted = Counter(str(row["targeted_packet_status"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "plan_rows": len(rows),
        "triage_order": int(EXPECTED_TRIAGE_ORDER),
        "execution_order": int(EXPECTED_EXECUTION_ORDER),
        "school_gap_resolution_batch_key": EXPECTED_BATCH_KEY,
        "gap_rows_represented": sum(1 for _ in rows),
        "by_plan_lane": dict(sorted(by_lane.items())),
        "by_candidate_context_status": dict(sorted(by_context.items())),
        "by_targeted_packet_status": dict(sorted(by_targeted.items())),
        "supported_person_rows_represented": sum(int_value(row.get("supported_person_rows")) for row in rows),
        "candidate_source_rows_represented": sum(int_value(row.get("candidate_source_count")) for row in rows),
        "approved_non_mutating_disposition_rows_represented": sum(
            int_value(row.get("approved_non_mutating_disposition_count")) for row in rows
        ),
        "source_triage_rowset_sha256": EXPECTED_TRIAGE_ROWSET,
        "source_triage_contract_rowset_sha256": EXPECTED_TRIAGE_CONTRACT_ROWSET,
        "source_targeted_review_rowset_sha256": EXPECTED_TARGETED_REVIEW_ROWSET,
        "web_fetch_allowed": False,
        "private_artifact_paths_committed": False,
        "raw_dump_publication_allowed": False,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "accepted_person_rows": 0,
        "gbrain_advisory_effect": GBRAIN_ADVISORY_EFFECT,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    if len(rows) != EXPECTED_PLAN_ROWS:
        raise SystemExit("Vanderbilt slice-2 execution plan failed row count checks.")

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(
        json.dumps(
            {
                "plan_rows": summary["plan_rows"],
                "gap_rows_represented": summary["gap_rows_represented"],
                "rowset_sha256": summary["rowset_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
