#!/usr/bin/env python3
"""Materialize a public-safe Vanderbilt open-gap triage packet."""

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

BATCH_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_summary.json"
BATCH_CSV = ARTIFACTS / "school_gap_resolution_batches.csv"
PACKET_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_packet_summary.json"
SLICE_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_slice_index_summary.json"
SLICE_CSV = ARTIFACTS / "school_gap_resolution_batch_slice_index.csv"
MANIFEST_SUMMARY = ARTIFACTS / "school_gap_resolution_manifest_summary.json"

TRIAGE_CSV = ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.csv"
TRIAGE_JSON = ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.json"
TRIAGE_SUMMARY = ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet_summary.json"
TRIAGE_MD = RESEARCH / "vanderbilt-open-gap-manifest-triage-packet-2026-06-09.md"

CONTRACT_CSV = ARTIFACTS / "vanderbilt_triage_slice_definition_contract.csv"
CONTRACT_JSON = ARTIFACTS / "vanderbilt_triage_slice_definition_contract.json"
CONTRACT_SUMMARY = ARTIFACTS / "vanderbilt_triage_slice_definition_contract_summary.json"
CONTRACT_MD = RESEARCH / "vanderbilt-triage-slice-definition-contract-2026-06-09.md"

EXPECTED_BATCH_ROWS = 21
EXPECTED_GAP_ROWS = 113
EXPECTED_SLICE_INDEX_ROWSET = "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75"
GBRAIN_ADVISORY_EFFECT = "gbrain_selected_vanderbilt_open_gap_manifest_triage_packet_option_b"

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
    "person_ingestion",
    "denominator_closure",
    "vanderbilt_school_verification",
    "parser_acceptance",
    "scope_closure",
    "url_rewrite",
    "identity_collapse",
]

MUTATION_POLICY = (
    "Non-mutating Vanderbilt open-gap manifest triage packet. It ranks the committed 21 Vanderbilt gap-resolution "
    "batch slices covering 113 open gaps and records slice-definition boundaries for contributor execution. It does "
    "not fetch web pages, fill reviewer decisions, apply patches, approve people, ingest people, close denominators, "
    "verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw dumps, or collapse identities."
)

TRIAGE_FIELDS = [
    "triage_packet_key",
    "triage_order",
    "execution_order",
    "school_gap_resolution_batch_key",
    "school_name",
    "triage_family",
    "triage_status",
    "urgency_score",
    "priority_band",
    "next_operator_lane",
    "resolution_category",
    "gap_count",
    "program_count",
    "supported_person_gap_count",
    "candidate_source_gap_count",
    "approved_non_mutating_disposition_gap_count",
    "slice_output_path",
    "slice_command",
    "verification_command",
    "target_artifact",
    "required_next_evidence",
    "recommended_next_action",
    "success_condition",
    "approval_required_for",
    "prohibited_mutations",
    "source_gap_rows",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

TRIAGE_ROWSET_FIELDS = [
    field
    for field in TRIAGE_FIELDS
    if field not in {"triage_packet_key", "evidence_json", "mutation_policy", "generated_at"}
]

CONTRACT_FIELDS = [
    "slice_contract_key",
    "triage_family",
    "slice_count",
    "gap_count",
    "allowed_evidence_actions",
    "required_slice_output_policy",
    "permitted_output_path_prefix",
    "verification_command",
    "success_condition",
    "approval_required_for",
    "prohibited_mutations",
    "public_url_policy",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

CONTRACT_ROWSET_FIELDS = [
    field
    for field in CONTRACT_FIELDS
    if field not in {"slice_contract_key", "evidence_json", "mutation_policy", "generated_at"}
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


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def rowset_sha256(rows: list[dict[str, object]], fields: list[str], key_field: str) -> str:
    material = [
        {field: row.get(field, "") for field in fields}
        for row in sorted(rows, key=lambda item: str(item.get(key_field, "")))
    ]
    return sha256_text(dumps(material))


def int_value(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def semicolon(values: list[str]) -> str:
    return "; ".join(values)


def priority_band(score: int) -> str:
    if score >= 800:
        return "critical"
    if score >= 740:
        return "high"
    if score >= 680:
        return "medium"
    return "low"


def triage_family(lane: str) -> str:
    if "source_discovery" in lane or lane == "program_page_probe":
        return "source_discovery_or_program_probe"
    if "scope" in lane or "shared_source" in lane:
        return "scope_or_shared_source_review"
    if "url_confirmation" in lane:
        return "official_url_confirmation"
    if "route" in lane or "rendered_parser" in lane or "manual" in lane or "refetch" in lane:
        return "route_parser_or_rendered_review"
    return "other_gap_triage"


def allowed_actions_for_family(family: str) -> str:
    return {
        "source_discovery_or_program_probe": (
            "prepare search/query plans; inspect public official program pages; classify whether candidate source "
            "evidence supports a later exact packet"
        ),
        "route_parser_or_rendered_review": (
            "inspect committed route/parser evidence; prepare rendered-review or parser-scope packets; record recourse"
        ),
        "scope_or_shared_source_review": (
            "compare shared or related-scope evidence against target program scope; prepare non-mutating disposition packets"
        ),
        "official_url_confirmation": (
            "confirm official-context URL fit before any later source-discovery or no-public-roster packet"
        ),
        "other_gap_triage": "classify gap evidence into a bounded non-mutating next packet",
    }.get(family, "classify gap evidence into a bounded non-mutating next packet")


def urgency_score(batch: dict[str, str], family: str) -> int:
    score = int_value(batch.get("max_resolution_priority"))
    score += min(int_value(batch.get("gap_count")), 25)
    if family == "source_discovery_or_program_probe":
        score += 35
    if family == "route_parser_or_rendered_review":
        score += 25
    if int_value(batch.get("supported_person_gap_count")) > 0:
        score += 20
    if int_value(batch.get("candidate_source_gap_count")) > 0:
        score += 12
    if int_value(batch.get("gap_count")) <= 2:
        score += 10
    return score


def verify_sources() -> tuple[list[dict[str, str]], list[dict[str, str]], dict[str, object]]:
    batch_summary = read_json(BATCH_SUMMARY)
    packet_summary = read_json(PACKET_SUMMARY)
    slice_summary = read_json(SLICE_SUMMARY)
    manifest_summary = read_json(MANIFEST_SUMMARY)
    if not all(isinstance(item, dict) for item in [batch_summary, packet_summary, slice_summary, manifest_summary]):
        raise SystemExit("Expected Vanderbilt gap manifest, batch, packet, and slice summaries to be JSON objects.")
    checks = {
        "manifest_rows": manifest_summary.get("rows") == EXPECTED_GAP_ROWS,
        "manifest_school": manifest_summary.get("by_school") == {"VANDERBILT UNIVERSITY SCH OF MEDICINE": EXPECTED_GAP_ROWS},
        "manifest_mutation_false": manifest_summary.get("mutation_allowed") is False,
        "batch_rows": batch_summary.get("rows") == EXPECTED_BATCH_ROWS,
        "batch_gap_rows": batch_summary.get("gap_rows") == EXPECTED_GAP_ROWS,
        "batch_mutation_false": batch_summary.get("mutation_allowed") is False,
        "packet_rows": packet_summary.get("rows") == EXPECTED_GAP_ROWS,
        "packet_batch_rows": packet_summary.get("batch_rows") == EXPECTED_BATCH_ROWS,
        "packet_mutation_false": packet_summary.get("mutation_allowed") is False,
        "slice_rowset": slice_summary.get("rowset_sha256") == EXPECTED_SLICE_INDEX_ROWSET,
        "slice_rows": slice_summary.get("slice_index_rows") == EXPECTED_BATCH_ROWS,
        "slice_gap_rows": slice_summary.get("gap_rows_represented") == EXPECTED_GAP_ROWS,
        "slice_tmp_only": slice_summary.get("slice_outputs_default_tmp_only") is True,
        "slice_mutation_false": slice_summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected Vanderbilt open-gap triage source boundary: " + dumps(checks))
    return read_csv_rows(BATCH_CSV), read_csv_rows(SLICE_CSV), checks


def build_triage_rows(generated_at: str) -> list[dict[str, object]]:
    batches, slices, source_checks = verify_sources()
    slices_by_order = {row.get("execution_order", ""): row for row in slices}
    rows: list[dict[str, object]] = []
    for batch in batches:
        execution_order = int_value(batch.get("execution_order"))
        slice_row = slices_by_order.get(str(execution_order), {})
        family = triage_family(batch.get("next_operator_lane", ""))
        score = urgency_score(batch, family)
        rows.append(
            {
                "triage_packet_key": stable_key(
                    "vanderbilt_open_gap_manifest_triage_packet",
                    batch.get("school_gap_resolution_batch_key", ""),
                    EXPECTED_GAP_ROWS,
                    GBRAIN_ADVISORY_EFFECT,
                ),
                "triage_order": 0,
                "execution_order": execution_order,
                "school_gap_resolution_batch_key": batch.get("school_gap_resolution_batch_key", ""),
                "school_name": batch.get("school_name", ""),
                "triage_family": family,
                "triage_status": "ready_for_non_mutating_gap_slice_execution",
                "urgency_score": score,
                "priority_band": priority_band(score),
                "next_operator_lane": batch.get("next_operator_lane", ""),
                "resolution_category": batch.get("resolution_category", ""),
                "gap_count": int_value(batch.get("gap_count")),
                "program_count": int_value(batch.get("program_count")),
                "supported_person_gap_count": int_value(batch.get("supported_person_gap_count")),
                "candidate_source_gap_count": int_value(batch.get("candidate_source_gap_count")),
                "approved_non_mutating_disposition_gap_count": int_value(
                    batch.get("approved_non_mutating_disposition_gap_count")
                ),
                "slice_output_path": slice_row.get("slice_output_path", f"/tmp/school_gap_resolution_batch_order_{execution_order}.csv"),
                "slice_command": slice_row.get(
                    "slice_command",
                    "python3 scripts/slice_school_gap_resolution_batch_packets.py "
                    f"--execution-order {execution_order} --output /tmp/school_gap_resolution_batch_order_{execution_order}.csv",
                ),
                "verification_command": (
                    "python3 scripts/materialize_school_gap_resolution_batches.py && "
                    "python3 scripts/materialize_school_gap_resolution_batch_packets.py && "
                    "python3 scripts/materialize_school_gap_resolution_batch_slice_index.py && "
                    "python3 scripts/materialize_vanderbilt_open_gap_manifest_triage_packet.py"
                ),
                "target_artifact": "artifacts/data/vanderbilt_open_gap_manifest_triage_packet.csv",
                "required_next_evidence": batch.get("required_next_evidence", ""),
                "recommended_next_action": batch.get("recommended_operator_action", ""),
                "success_condition": (
                    "A contributor can select one /tmp slice, collect or classify non-mutating source evidence, "
                    "and stop at packet preparation without accepting people or closing denominators."
                ),
                "approval_required_for": semicolon(APPROVAL_REQUIRED_FOR),
                "prohibited_mutations": semicolon(PROHIBITED_MUTATIONS),
                "source_gap_rows": EXPECTED_GAP_ROWS,
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "evidence_json": dumps(
                    {
                        "gbrain_advisory_effect": GBRAIN_ADVISORY_EFFECT,
                        "source_checks": source_checks,
                        "source_batch_summary": str(BATCH_SUMMARY.relative_to(ROOT)),
                        "source_slice_summary": str(SLICE_SUMMARY.relative_to(ROOT)),
                        "slice_definition_contract": str(CONTRACT_SUMMARY.relative_to(ROOT)),
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(
        key=lambda row: (
            -int_value(row.get("urgency_score")),
            -int_value(row.get("gap_count")),
            str(row.get("next_operator_lane", "")),
            int_value(row.get("execution_order")),
        )
    )
    for order, row in enumerate(rows, start=1):
        row["triage_order"] = order
    return rows


def build_contract_rows(triage_rows: list[dict[str, object]], generated_at: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    families = sorted({str(row["triage_family"]) for row in triage_rows})
    for family in families:
        family_rows = [row for row in triage_rows if row["triage_family"] == family]
        rows.append(
            {
                "slice_contract_key": stable_key("vanderbilt_triage_slice_definition_contract", family, EXPECTED_GAP_ROWS),
                "triage_family": family,
                "slice_count": len(family_rows),
                "gap_count": sum(int_value(row.get("gap_count")) for row in family_rows),
                "allowed_evidence_actions": allowed_actions_for_family(family),
                "required_slice_output_policy": "slice outputs must be written under /tmp by default",
                "permitted_output_path_prefix": "/tmp/",
                "verification_command": "python3 scripts/materialize_vanderbilt_open_gap_manifest_triage_packet.py",
                "success_condition": (
                    "Every slice in this family remains a non-mutating evidence or packet-preparation surface."
                ),
                "approval_required_for": semicolon(APPROVAL_REQUIRED_FOR),
                "prohibited_mutations": semicolon(PROHIBITED_MUTATIONS),
                "public_url_policy": (
                    "Triage packet rows omit raw URLs; downstream /tmp packet slices may contain already committed "
                    "public official-source URLs."
                ),
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "evidence_json": dumps(
                    {
                        "triage_orders": [row["triage_order"] for row in family_rows],
                        "execution_orders": [row["execution_order"] for row in family_rows],
                        "source_triage_packet": str(TRIAGE_SUMMARY.relative_to(ROOT)),
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )
    return rows


def private_marker_hits(rows: list[dict[str, object]]) -> list[str]:
    text = dumps(rows)
    return [marker for marker in PRIVATE_PATH_MARKERS if marker in text]


def write_triage_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    TRIAGE_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Open Gap Manifest Triage Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Open Gap Manifest Triage Packet",
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
        "## Triage Slices",
        "",
        "| triage | source order | family | lane | gaps | command |",
        "| ---: | ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {triage_order} | {execution_order} | {triage_family} | {next_operator_lane} | {gap_count} | `{slice_command}` |".format(
                **row
            )
        )
    lines.append("")
    TRIAGE_MD.write_text("\n".join(lines), encoding="utf-8")


def write_contract_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    CONTRACT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Triage Slice Definition Contract",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Triage Slice Definition Contract",
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
        "## Families",
        "",
        "| family | slices | gaps | allowed evidence actions |",
        "| --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {triage_family} | {slice_count} | {gap_count} | {allowed_evidence_actions} |".format(**row)
        )
    lines.append("")
    CONTRACT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    triage_rows = build_triage_rows(generated_at)
    contract_rows = build_contract_rows(triage_rows, generated_at)
    hits = private_marker_hits(triage_rows + contract_rows)
    if hits:
        raise SystemExit("Vanderbilt open-gap triage rows contain private artifact markers: " + ", ".join(hits))

    by_family = Counter(str(row["triage_family"]) for row in triage_rows)
    gaps_by_family = {
        family: sum(int_value(row.get("gap_count")) for row in triage_rows if row["triage_family"] == family)
        for family in sorted(by_family)
    }
    critical_rows = sum(1 for row in triage_rows if row.get("priority_band") == "critical")
    high_rows = sum(1 for row in triage_rows if row.get("priority_band") == "high")
    medium_rows = sum(1 for row in triage_rows if row.get("priority_band") == "medium")
    low_rows = sum(1 for row in triage_rows if row.get("priority_band") == "low")
    triage_summary = {
        "generated_at": generated_at,
        "csv": str(TRIAGE_CSV.relative_to(ROOT)),
        "json": str(TRIAGE_JSON.relative_to(ROOT)),
        "markdown": str(TRIAGE_MD.relative_to(ROOT)),
        "source_manifest_summary": str(MANIFEST_SUMMARY.relative_to(ROOT)),
        "source_batch_summary": str(BATCH_SUMMARY.relative_to(ROOT)),
        "source_packet_summary": str(PACKET_SUMMARY.relative_to(ROOT)),
        "source_slice_summary": str(SLICE_SUMMARY.relative_to(ROOT)),
        "source_slice_index_rowset_sha256": EXPECTED_SLICE_INDEX_ROWSET,
        "slice_definition_contract_summary": str(CONTRACT_SUMMARY.relative_to(ROOT)),
        "triage_rows": len(triage_rows),
        "gap_rows_represented": sum(int_value(row.get("gap_count")) for row in triage_rows),
        "by_triage_family": dict(sorted(by_family.items())),
        "gap_rows_by_triage_family": gaps_by_family,
        "critical_rows": critical_rows,
        "high_rows": high_rows,
        "medium_rows": medium_rows,
        "low_rows": low_rows,
        "slice_outputs_default_tmp_only": True,
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
    triage_summary["rowset_sha256"] = rowset_sha256(triage_rows, TRIAGE_ROWSET_FIELDS, "triage_packet_key")

    contract_summary = {
        "generated_at": generated_at,
        "csv": str(CONTRACT_CSV.relative_to(ROOT)),
        "json": str(CONTRACT_JSON.relative_to(ROOT)),
        "markdown": str(CONTRACT_MD.relative_to(ROOT)),
        "source_triage_summary": str(TRIAGE_SUMMARY.relative_to(ROOT)),
        "contract_rows": len(contract_rows),
        "slice_rows_represented": len(triage_rows),
        "gap_rows_represented": triage_summary["gap_rows_represented"],
        "by_triage_family": dict(sorted(by_family.items())),
        "slice_outputs_default_tmp_only": True,
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
    contract_summary["rowset_sha256"] = rowset_sha256(
        contract_rows, CONTRACT_ROWSET_FIELDS, "slice_contract_key"
    )

    if triage_summary["triage_rows"] != EXPECTED_BATCH_ROWS or triage_summary["gap_rows_represented"] != EXPECTED_GAP_ROWS:
        raise SystemExit("Vanderbilt open-gap triage packet failed completeness checks.")
    if contract_summary["slice_rows_represented"] != EXPECTED_BATCH_ROWS:
        raise SystemExit("Vanderbilt triage slice contract failed slice coverage checks.")

    write_csv(TRIAGE_CSV, triage_rows, TRIAGE_FIELDS)
    write_json(TRIAGE_JSON, triage_rows)
    write_json(TRIAGE_SUMMARY, triage_summary)
    write_csv(CONTRACT_CSV, contract_rows, CONTRACT_FIELDS)
    write_json(CONTRACT_JSON, contract_rows)
    write_json(CONTRACT_SUMMARY, contract_summary)
    write_triage_markdown(triage_rows, triage_summary)
    write_contract_markdown(contract_rows, contract_summary)
    print(
        json.dumps(
            {
                "triage_rows": triage_summary["triage_rows"],
                "gap_rows_represented": triage_summary["gap_rows_represented"],
                "triage_rowset_sha256": triage_summary["rowset_sha256"],
                "contract_rows": contract_summary["contract_rows"],
                "contract_rowset_sha256": contract_summary["rowset_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
