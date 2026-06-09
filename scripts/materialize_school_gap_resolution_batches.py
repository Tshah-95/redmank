#!/usr/bin/env python3
"""Materialize bounded operator batches for school gap-resolution rows."""

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

MANIFEST_CSV = ARTIFACTS / "school_gap_resolution_manifest.csv"
CSV_OUT = ARTIFACTS / "school_gap_resolution_batches.csv"
JSON_OUT = ARTIFACTS / "school_gap_resolution_batches.json"
SUMMARY_OUT = ARTIFACTS / "school_gap_resolution_batch_summary.json"

MAX_GAPS_PER_BATCH = 25

FIELDS = [
    "school_gap_resolution_batch_key",
    "execution_order",
    "school_key",
    "school_name",
    "sponsoring_institution",
    "next_operator_lane",
    "resolution_category",
    "batch_status",
    "ready_to_execute",
    "gap_count",
    "program_count",
    "max_resolution_priority",
    "min_resolution_priority",
    "supported_person_gap_count",
    "candidate_source_gap_count",
    "approved_non_mutating_disposition_gap_count",
    "program_type_counts_json",
    "best_evidence_status_counts_json",
    "top_programs",
    "top_evidence_urls",
    "recommended_operator_action",
    "execution_instructions",
    "required_next_evidence",
    "target_artifact",
    "top_gap_rows_json",
    "evidence_json",
    "generated_at",
]

csv.field_size_limit(sys.maxsize)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_int(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def read_existing() -> dict[str, dict[str, str]]:
    return {row["school_gap_resolution_batch_key"]: row for row in read_csv(CSV_OUT)}


def stable_generated_at(existing: dict[str, dict[str, str]], row: dict[str, object], generated_at: str) -> str:
    prior = existing.get(str(row["school_gap_resolution_batch_key"]))
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def school_rank(school_name: str) -> int:
    if school_name == "STANFORD UNIVERSITY SCH OF MEDICINE":
        return 0
    if school_name == "VANDERBILT UNIVERSITY SCH OF MEDICINE":
        return 1
    return 9


def batch_key(parts: object) -> str:
    return "school_gap_resolution_batch_" + sha256_text(dumps(parts))[:20]


def batch_status(lane: str) -> str:
    return {
        "build_shared_source_crosswalk_or_disposition_packet": "shared_source_crosswalk_batch_ready",
        "run_headed_second_hop_route_inspection": "second_hop_route_inspection_batch_ready",
        "build_related_scope_disposition_packet": "related_scope_disposition_batch_ready",
        "build_manual_scope_review_packet": "manual_scope_review_batch_ready",
        "build_flat_text_parser_or_manual_review": "flat_text_parser_review_batch_ready",
        "run_targeted_source_discovery": "source_discovery_batch_ready",
        "target_program_source_discovery_after_related_scope_exclusion": "source_discovery_after_related_scope_batch_ready",
        "rendered_parser_manual_review_after_related_scope_source_discovery": "rendered_parser_manual_after_related_scope_source_discovery_batch_ready",
        "linked_route_inspection_after_related_scope_source_discovery": "linked_route_inspection_after_related_scope_source_discovery_batch_ready",
        "targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery": "source_discovery_or_closure_after_related_scope_source_discovery_batch_ready",
        "repair_program_url_or_run_source_search": "program_url_repair_batch_ready",
        "active_source_route_inspection": "active_source_route_inspection_batch_ready",
        "rendered_parser_manual_repair": "rendered_parser_manual_repair_batch_ready",
        "official_url_repair_or_source_search": "official_url_repair_batch_ready",
        "program_page_probe_after_official_url_resolution": "program_page_probe_after_url_resolution_batch_ready",
        "active_source_route_inspection_after_official_url_probe": "official_url_probe_route_inspection_batch_ready",
        "rendered_parser_manual_repair_after_official_url_probe": "official_url_probe_rendered_parser_manual_batch_ready",
        "targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe": "official_url_probe_source_discovery_or_closure_batch_ready",
        "headed_refetch_after_official_url_probe": "official_url_probe_refetch_batch_ready",
        "manual_rendered_review_or_targeted_source_discovery_after_official_url_probe": "official_url_probe_manual_review_batch_ready",
        "build_exact_parser_acceptance_packet_after_official_url_probe": "official_url_probe_parser_acceptance_packet_batch_ready",
        "build_rendered_or_flat_text_parser_packet_after_official_url_probe": "official_url_probe_flat_text_parser_packet_batch_ready",
        "second_hop_route_inspection_after_official_url_probe": "official_url_probe_second_hop_inspection_batch_ready",
        "target_program_source_discovery_after_official_url_probe_related_scope": "official_url_probe_related_scope_source_discovery_batch_ready",
        "target_program_source_discovery_after_official_url_probe_exclusion": "official_url_probe_exclusion_source_discovery_batch_ready",
        "manual_rendered_review_or_targeted_source_discovery_after_official_url_probe_route": "official_url_probe_route_manual_or_source_discovery_batch_ready",
        "manual_route_packet_recourse_review_after_official_url_probe": "official_url_probe_route_manual_recourse_batch_ready",
        "targeted_source_discovery_after_parent_url_resolution": "source_discovery_after_parent_url_resolution_batch_ready",
        "manual_url_confirmation_after_official_context_resolution": "manual_url_confirmation_batch_ready",
        "program_page_probe": "program_page_probe_batch_ready",
        "headed_refetch": "headed_refetch_batch_ready",
    }.get(lane, "gap_resolution_batch_ready")


def recommended_action(lane: str) -> str:
    return {
        "build_shared_source_crosswalk_or_disposition_packet": "build_exact_shared_source_crosswalk_or_residual_disposition_packet",
        "run_headed_second_hop_route_inspection": "run_headed_second_hop_route_inspection_non_mutating",
        "build_related_scope_disposition_packet": "build_exact_related_scope_disposition_packet",
        "build_manual_scope_review_packet": "review_manual_scope_and_build_exclusion_or_parser_packet",
        "build_flat_text_parser_or_manual_review": "inspect_flat_text_and_build_parser_or_no_public_roster_packet",
        "run_targeted_source_discovery": "run_targeted_official_source_discovery",
        "target_program_source_discovery_after_related_scope_exclusion": "run_targeted_official_source_discovery_after_related_scope_disposition",
        "rendered_parser_manual_review_after_related_scope_source_discovery": "run_rendered_parser_manual_review_after_related_scope_source_discovery",
        "linked_route_inspection_after_related_scope_source_discovery": "inspect_linked_roster_routes_after_related_scope_source_discovery",
        "targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery": "continue_targeted_source_discovery_or_prepare_no_public_roster_closure_packet",
        "repair_program_url_or_run_source_search": "repair_program_url_or_find_official_replacement_source",
        "active_source_route_inspection": "inspect_active_source_and_second_hop_routes_non_mutating",
        "rendered_parser_manual_repair": "run_rendered_parser_manual_repair_and_packet_evidence_ready_rows",
        "official_url_repair_or_source_search": "resolve_official_program_url_then_rerun_route_probe",
        "program_page_probe_after_official_url_resolution": "probe_approved_exact_official_program_url",
        "active_source_route_inspection_after_official_url_probe": "inspect_official_url_probe_roster_links_non_mutating",
        "rendered_parser_manual_repair_after_official_url_probe": "inspect_official_url_probe_rendered_roster_text_non_mutating",
        "targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe": "run_source_discovery_or_prepare_no_public_roster_closure_packet",
        "headed_refetch_after_official_url_probe": "rerun_headed_fetch_for_official_url_probe",
        "manual_rendered_review_or_targeted_source_discovery_after_official_url_probe": "review_official_url_probe_or_continue_source_discovery",
        "build_exact_parser_acceptance_packet_after_official_url_probe": "build_exact_parser_acceptance_packet_from_approved_route_candidate",
        "build_rendered_or_flat_text_parser_packet_after_official_url_probe": "build_rendered_or_flat_text_parser_packet_from_approved_route_candidate",
        "second_hop_route_inspection_after_official_url_probe": "inspect_second_hop_routes_from_approved_official_url_probe",
        "target_program_source_discovery_after_official_url_probe_related_scope": "run_target_program_source_discovery_after_related_scope_route_evidence",
        "target_program_source_discovery_after_official_url_probe_exclusion": "run_target_program_source_discovery_after_faculty_leadership_route_evidence",
        "manual_rendered_review_or_targeted_source_discovery_after_official_url_probe_route": "review_approved_route_negative_context_or_continue_source_discovery",
        "manual_route_packet_recourse_review_after_official_url_probe": "review_approved_route_packet_recourse",
        "targeted_source_discovery_after_parent_url_resolution": "run_targeted_source_discovery_from_parent_or_alias_url",
        "manual_url_confirmation_after_official_context_resolution": "manually_confirm_official_context_url_before_source_discovery",
        "program_page_probe": "probe_program_page_for_current_roster_routes",
        "headed_refetch": "rerun_headed_refetch_before_scope_or_parser_decision",
    }.get(lane, "execute_gap_resolution_batch_non_mutating")


def execution_instructions(lane: str) -> str:
    if "packet" in lane or "review" in lane or "repair" in lane:
        return "Produce an exact non-mutating packet with row keys and source evidence; no people, denominator closure, school verification, URL rewrite, or identity collapse may occur without later GBrain approval."
    if "inspection" in lane or "probe" in lane or "discovery" in lane or "refetch" in lane:
        return "Collect or classify source evidence only; route/parser output remains candidate evidence until an exact GBrain-approved packet permits mutation."
    return "Resolve gap evidence while preserving the non-mutating boundary from the manifest."


def required_next_evidence(rows: list[dict[str, str]]) -> str:
    actions = Counter(row.get("recommended_next_action") or "" for row in rows)
    if actions:
        return actions.most_common(1)[0][0]
    return "Official current-roster source evidence or exact GBrain-approved disposition packet."


def target_artifact(lane: str) -> str:
    if lane.startswith("build_"):
        return "artifacts/data/school_gap_resolution_batch_packets.csv"
    if lane == "second_hop_route_inspection_after_official_url_probe":
        return "artifacts/data/vanderbilt_official_url_probe_route_inspection.csv"
    if lane in {
        "target_program_source_discovery_after_official_url_probe_related_scope",
        "target_program_source_discovery_after_official_url_probe_exclusion",
        "manual_rendered_review_or_targeted_source_discovery_after_official_url_probe_route",
        "manual_route_packet_recourse_review_after_official_url_probe",
    }:
        return "artifacts/data/vanderbilt_official_url_probe_route_inspection_packet.csv"
    if lane == "active_source_route_inspection_after_official_url_probe":
        return "artifacts/data/vanderbilt_active_source_candidate_route_inspection.csv"
    if lane in {
        "rendered_parser_manual_review_after_related_scope_source_discovery",
        "linked_route_inspection_after_related_scope_source_discovery",
        "targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery",
    }:
        return "artifacts/data/vanderbilt_related_scope_source_discovery_disposition_packet.csv"
    if lane in {
        "rendered_parser_manual_repair_after_official_url_probe",
        "targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe",
        "headed_refetch_after_official_url_probe",
        "manual_rendered_review_or_targeted_source_discovery_after_official_url_probe",
    }:
        return "artifacts/data/vanderbilt_official_url_program_page_probe.csv"
    if "vanderbilt" in lane:
        return "artifacts/data/vanderbilt_active_source_candidate_route_inspection.csv"
    if "stanford" in lane:
        return "artifacts/data/stanford_roster_route_inspection.csv"
    return "artifacts/data/school_gap_resolution_manifest.csv"


def top_gap_rows(rows: list[dict[str, str]], limit: int = 12) -> list[dict[str, object]]:
    output = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("resolution_priority")), item.get("program_name", "")))[:limit]:
        output.append(
            {
                "gap_key": row.get("gap_key"),
                "program_name": row.get("program_name"),
                "program_type": row.get("program_type"),
                "department_or_group": row.get("department_or_group"),
                "resolution_category": row.get("resolution_category"),
                "resolution_priority": as_int(row.get("resolution_priority")),
                "best_evidence_status": row.get("best_evidence_status"),
                "best_evidence_url": row.get("best_evidence_url"),
                "supported_person_rows": as_int(row.get("supported_person_rows")),
                "candidate_source_count": as_int(row.get("candidate_source_count")),
            }
        )
    return output


def build_rows(generated_at: str) -> list[dict[str, object]]:
    existing = read_existing()
    manifest_rows = read_csv(MANIFEST_CSV)
    grouped: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in manifest_rows:
        grouped[(row.get("school_name", ""), row.get("next_operator_lane", ""), row.get("resolution_category", ""))].append(row)

    output: list[dict[str, object]] = []
    for (school_name, lane, category), rows in sorted(grouped.items(), key=lambda item: (school_rank(item[0][0]), item[0][1], item[0][2])):
        ordered = sorted(rows, key=lambda item: (-as_int(item.get("resolution_priority")), item.get("program_name", ""), item.get("gap_key", "")))
        for chunk_index, offset in enumerate(range(0, len(ordered), MAX_GAPS_PER_BATCH), start=1):
            chunk = ordered[offset : offset + MAX_GAPS_PER_BATCH]
            gap_keys = [row["gap_key"] for row in chunk]
            priorities = [as_int(row.get("resolution_priority")) for row in chunk]
            batch = {
                "school_gap_resolution_batch_key": batch_key((school_name, lane, category, chunk_index, gap_keys)),
                "execution_order": 0,
                "school_key": chunk[0].get("school_key", ""),
                "school_name": school_name,
                "sponsoring_institution": chunk[0].get("sponsoring_institution", ""),
                "next_operator_lane": lane,
                "resolution_category": category,
                "batch_status": batch_status(lane),
                "ready_to_execute": "true",
                "gap_count": len(chunk),
                "program_count": len({row.get("program_key") for row in chunk}),
                "max_resolution_priority": max(priorities) if priorities else 0,
                "min_resolution_priority": min(priorities) if priorities else 0,
                "supported_person_gap_count": sum(1 for row in chunk if as_int(row.get("supported_person_rows")) > 0),
                "candidate_source_gap_count": sum(1 for row in chunk if as_int(row.get("candidate_source_count")) > 0),
                "approved_non_mutating_disposition_gap_count": sum(1 for row in chunk if as_int(row.get("approved_non_mutating_disposition_count")) > 0),
                "program_type_counts_json": dumps(dict(Counter(row.get("program_type", "") for row in chunk))),
                "best_evidence_status_counts_json": dumps(dict(Counter(row.get("best_evidence_status", "") for row in chunk))),
                "top_programs": "; ".join(row.get("program_name", "") for row in chunk[:10]),
                "top_evidence_urls": "; ".join(dict.fromkeys(row.get("best_evidence_url", "") for row in chunk if row.get("best_evidence_url")))[:1000],
                "recommended_operator_action": recommended_action(lane),
                "execution_instructions": execution_instructions(lane),
                "required_next_evidence": required_next_evidence(chunk),
                "target_artifact": target_artifact(lane),
                "top_gap_rows_json": dumps(top_gap_rows(chunk)),
                "evidence_json": dumps({
                    "gap_keys": gap_keys,
                    "source_manifest": "artifacts/data/school_gap_resolution_manifest.csv",
                    "non_mutating_policy": "Batch rows are operator work surfaces only; mutation requires exact GBrain approval.",
                }),
                "generated_at": generated_at,
            }
            batch["generated_at"] = stable_generated_at(existing, batch, generated_at)
            output.append(batch)

    output.sort(key=lambda row: (school_rank(str(row["school_name"])), -as_int(row["max_resolution_priority"]), str(row["next_operator_lane"]), str(row["resolution_category"]), str(row["school_gap_resolution_batch_key"])))
    for index, row in enumerate(output, start=1):
        row["execution_order"] = index
    return output


def build_summary(rows: list[dict[str, object]], generated_at: str) -> dict[str, object]:
    return {
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "generated_at": generated_at,
        "rows": len(rows),
        "gap_rows": sum(as_int(row.get("gap_count")) for row in rows),
        "by_school": dict(Counter(str(row["school_name"]) for row in rows)),
        "gap_rows_by_school": dict(defaultdict(int, {
            school: sum(as_int(row.get("gap_count")) for row in rows if row["school_name"] == school)
            for school in sorted({str(row["school_name"]) for row in rows})
        })),
        "by_next_operator_lane": dict(Counter(str(row["next_operator_lane"]) for row in rows)),
        "ready_to_execute_rows": sum(1 for row in rows if row.get("ready_to_execute") == "true"),
        "mutation_allowed": False,
        "policy": "Non-mutating bounded operator batches over school_gap_resolution_manifest rows. These batches do not approve people, denominator closure, school verification, URL rewrites, training-state mutation, or identity collapse.",
    }


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_rows(generated_at)
    summary = build_summary(rows, generated_at)
    write_csv(CSV_OUT, rows)
    write_json(JSON_OUT, rows)
    write_json(SUMMARY_OUT, summary)
    print(json.dumps({"school_gap_resolution_batches": len(rows), "gap_rows": summary["gap_rows"], "by_school": summary["gap_rows_by_school"]}, sort_keys=True))


if __name__ == "__main__":
    main()
