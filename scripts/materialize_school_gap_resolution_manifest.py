#!/usr/bin/env python3
"""Materialize non-mutating gap-resolution manifests for open school lanes."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"

CSV_OUT = ARTIFACTS / "school_gap_resolution_manifest.csv"
JSON_OUT = ARTIFACTS / "school_gap_resolution_manifest.json"
SUMMARY_OUT = ARTIFACTS / "school_gap_resolution_manifest_summary.json"

STANFORD_SCHOOL = "STANFORD UNIVERSITY SCH OF MEDICINE"
STANFORD_SPONSOR = "Stanford Health Care / Stanford University Medical Center"
VANDERBILT_SCHOOL = "VANDERBILT UNIVERSITY SCH OF MEDICINE"
VANDERBILT_SPONSOR = "Vanderbilt University Medical Center"

GAP_STRATEGY_EFFECT = "top50_gap_resolution_manifest_strategy_non_mutating_stanford_first_vanderbilt_second"
STANFORD_SCHOOL_READINESS_SUMMARY = ARTIFACTS / "stanford_school_readiness_packet_summary.json"
STANFORD_SCHOOL_VERIFICATION_EFFECT = "stanford_school_verified_next_lane_approved"
STANFORD_SCHOOL_VERIFICATION_ROWSET_SHA256 = "25f821b23c74710d3c7f1290e880c5d6d57e25c7818749d49a00e44b188086e1"
STANFORD_SCHOOL_VERIFICATION_ROWS = 1
STANFORD_BATCH2_DISPOSITION_RECONCILIATION_CSV = ARTIFACTS / "stanford_gap_batch2_disposition_reconciliation_packet.csv"
STANFORD_BATCH2_DISPOSITION_RECONCILIATION_SUMMARY = ARTIFACTS / "stanford_gap_batch2_disposition_reconciliation_packet_summary.json"
STANFORD_BATCH2_DISPOSITION_RECONCILIATION_EFFECT = "stanford_gap_batch2_disposition_reconciliation_manifest_consumption_non_mutating"
STANFORD_BATCH2_DISPOSITION_RECONCILIATION_ROWSET_SHA256 = "9f9b5f7d512238e3f6045a67889da6bb75771adf69c9ecf6cf5872358c9a8395"
STANFORD_BATCH2_DISPOSITION_RECONCILIATION_ROWS = 25
STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_CSV = ARTIFACTS / "stanford_remaining_manual_scope_review_packet.csv"
STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_SUMMARY = ARTIFACTS / "stanford_remaining_manual_scope_review_packet_summary.json"
STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_EFFECT = "stanford_manual_scope_review_packet_non_mutating"
STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_ROWSET_SHA256 = "ff6734a99a71aef2f73f38d241dd77ba8d118550f8c0e4f00630b3ec4746d791"
STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_ROWS = 4
STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_CSV = ARTIFACTS / "stanford_shared_source_crosswalk_disposition_packet.csv"
STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_SUMMARY = ARTIFACTS / "stanford_shared_source_crosswalk_disposition_packet_summary.json"
STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_EFFECT = "stanford_shared_source_crosswalk_disposition_packet_non_mutating"
STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_ROWSET_SHA256 = "4dc90ea60fcdd1d2b034c2fde4246731c6c5e1028315384b0ebc9a8831cfa3e9"
STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_ROWS = 4
STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_CSV = ARTIFACTS / "stanford_flat_text_parser_manual_review_packet.csv"
STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_SUMMARY = ARTIFACTS / "stanford_flat_text_parser_manual_review_packet_summary.json"
STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_EFFECT = "stanford_flat_text_parser_manual_review_packet_non_mutating"
STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_ROWSET_SHA256 = "91737c7f88f032bd69e08da28db65722467627cf3d3ac100158dced154029132"
STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_ROWS = 5
VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_CSV = ARTIFACTS / "vanderbilt_execution_order9_remainder_disposition_packet.csv"
VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_SUMMARY = ARTIFACTS / "vanderbilt_execution_order9_remainder_disposition_packet_summary.json"
VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_EFFECT = "vanderbilt_execution_order9_remainder_disposition_2_non_mutating_approved"
VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_ROWSET_SHA256 = "955d47784d5d645875f70d9fb8cf7a92cf1ad6d5bef51b91e0fa6a43fe4d7dc1"
VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_ROWS = 2
VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_CSV = ARTIFACTS / "vanderbilt_related_scope_source_discovery_disposition_packet.csv"
VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_SUMMARY = ARTIFACTS / "vanderbilt_related_scope_source_discovery_disposition_packet_summary.json"
VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_EFFECT = "vanderbilt_related_scope_source_discovery_disposition_21_non_mutating_approved"
VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_ROWSET_SHA256 = "825f93d30829daaa4e30543e372b88e7826fd5de165532f02788897a9ce9e06a"
VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_ROWS = 21
ALLOW_EMPTY_ENV = "ALLOW_EMPTY_GAP_MANIFEST"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "gap_key",
    "school_key",
    "school_name",
    "sponsoring_institution",
    "program_key",
    "program_name",
    "program_type",
    "department_or_group",
    "gap_status",
    "coverage_status",
    "captured_people_count",
    "action_lane",
    "blocker_status",
    "resolution_category",
    "resolution_priority",
    "denominator_url",
    "best_evidence_url",
    "best_evidence_title",
    "best_evidence_status",
    "supported_person_rows",
    "candidate_source_count",
    "approved_non_mutating_disposition_count",
    "recommended_next_action",
    "next_operator_lane",
    "mutation_policy",
    "gbrain_strategy_effect",
    "gbrain_packet_required_for",
    "source_artifacts_json",
    "evidence_json",
    "generated_at",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_key(*parts: object) -> str:
    return hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:20]


def int_value(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def missing_core_inputs() -> list[str]:
    required = [
        ARTIFACTS / "vanderbilt_gme_program_coverage.json",
    ]
    if not stanford_school_verification_approved():
        required.extend(
            [
                ARTIFACTS / "top50_next_school_discovery_manifest.csv",
                ARTIFACTS / "stanford_training_summary.json",
                ARTIFACTS / "stanford_gap_drain_queue.csv",
            ]
        )
    return [str(path.relative_to(ROOT)) for path in required if not path.exists()]


def guard_nonempty_manifest(rows: list[dict[str, object]], previous_summary: object) -> None:
    if rows or os.environ.get(ALLOW_EMPTY_ENV) == "1":
        return
    previous_rows = int_value(previous_summary.get("rows") if isinstance(previous_summary, dict) else 0)
    missing = missing_core_inputs()
    details = {
        "refused_rows": 0,
        "previous_summary_rows": previous_rows,
        "missing_core_inputs": missing,
        "override_env": ALLOW_EMPTY_ENV + "=1",
    }
    raise SystemExit(
        "Refusing to write an empty school gap-resolution manifest from an incomplete checkout: "
        + json.dumps(details, ensure_ascii=True, sort_keys=True)
    )


def stanford_school_verification_approved() -> bool:
    summary = read_json(STANFORD_SCHOOL_READINESS_SUMMARY, {})
    if not isinstance(summary, dict):
        return False
    return (
        summary.get("gbrain_approval_verified") is True
        and summary.get("approval_effect_requested") == STANFORD_SCHOOL_VERIFICATION_EFFECT
        and summary.get("packet_status") == "approved_stanford_school_verified_next_lane"
        and summary.get("rowset_sha256") == STANFORD_SCHOOL_VERIFICATION_ROWSET_SHA256
        and int_value(summary.get("rows")) == STANFORD_SCHOOL_VERIFICATION_ROWS
        and int_value(summary.get("gap_drain_active_batch_rows")) == 0
    )


def rows_by(rows: list[dict[str, str]], key: str) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key, "")].append(row)
    return grouped


def approved_stanford_batch2_disposition_reconciliations_by_gap() -> dict[str, dict[str, str]]:
    summary = read_json(STANFORD_BATCH2_DISPOSITION_RECONCILIATION_SUMMARY, {})
    if not isinstance(summary, dict):
        return {}
    if not summary.get("gbrain_approval_verified"):
        return {}
    if summary.get("approval_effect_requested") != STANFORD_BATCH2_DISPOSITION_RECONCILIATION_EFFECT:
        return {}
    if summary.get("rowset_sha256") != STANFORD_BATCH2_DISPOSITION_RECONCILIATION_ROWSET_SHA256:
        return {}
    if int_value(summary.get("rows")) != STANFORD_BATCH2_DISPOSITION_RECONCILIATION_ROWS:
        return {}

    rows = read_csv(STANFORD_BATCH2_DISPOSITION_RECONCILIATION_CSV)
    if len(rows) != STANFORD_BATCH2_DISPOSITION_RECONCILIATION_ROWS:
        return {}
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("approval_effect_if_approved") != STANFORD_BATCH2_DISPOSITION_RECONCILIATION_EFFECT:
            return {}
        if row.get("gbrain_approval_verified") != "true":
            return {}
        if row.get("manifest_consumption_allowed_after_approval") != "true":
            return {}
        for flag in [
            "person_ingestion_allowed",
            "training_state_mutation_allowed",
            "denominator_closure_allowed",
            "school_verification_allowed",
            "url_rewrite_allowed",
            "identity_collapse_allowed",
        ]:
            if row.get(flag) != "false":
                return {}
        gap_key = row.get("gap_key", "")
        if not gap_key or gap_key in output:
            return {}
        output[gap_key] = row
    return output


def approved_stanford_remaining_manual_scope_reviews_by_gap() -> dict[str, dict[str, str]]:
    summary = read_json(STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_SUMMARY, {})
    if not isinstance(summary, dict):
        return {}
    if not summary.get("gbrain_approval_verified"):
        return {}
    if summary.get("approval_effect_requested") != STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_EFFECT:
        return {}
    if summary.get("rowset_sha256") != STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_ROWSET_SHA256:
        return {}
    if int_value(summary.get("rows")) != STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_ROWS:
        return {}

    rows = read_csv(STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_CSV)
    if len(rows) != STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_ROWS:
        return {}
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("approval_effect_if_approved") != STANFORD_REMAINING_MANUAL_SCOPE_REVIEW_EFFECT:
            return {}
        if row.get("gbrain_approval_verified") != "true":
            return {}
        for flag in [
            "person_ingestion_allowed",
            "training_state_mutation_allowed",
            "denominator_closure_allowed",
            "school_verification_allowed",
            "url_rewrite_allowed",
            "identity_collapse_allowed",
        ]:
            if row.get(flag) != "false":
                return {}
        gap_key = row.get("gap_key", "")
        if not gap_key or gap_key in output:
            return {}
        output[gap_key] = row
    return output


def approved_stanford_shared_source_crosswalk_dispositions_by_gap() -> dict[str, dict[str, str]]:
    summary = read_json(STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_SUMMARY, {})
    if not isinstance(summary, dict):
        return {}
    if not summary.get("gbrain_approval_verified"):
        return {}
    if summary.get("approval_effect_requested") != STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_EFFECT:
        return {}
    if summary.get("rowset_sha256") != STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_ROWSET_SHA256:
        return {}
    if int_value(summary.get("rows")) != STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_ROWS:
        return {}

    rows = read_csv(STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_CSV)
    if len(rows) != STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_ROWS:
        return {}
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("approval_effect_if_approved") != STANFORD_SHARED_SOURCE_CROSSWALK_DISPOSITION_EFFECT:
            return {}
        if row.get("gbrain_approval_verified") != "true":
            return {}
        for flag in [
            "person_ingestion_allowed",
            "training_state_mutation_allowed",
            "denominator_closure_allowed",
            "school_verification_allowed",
            "url_rewrite_allowed",
            "identity_collapse_allowed",
        ]:
            if row.get(flag) != "false":
                return {}
        gap_key = row.get("gap_key", "")
        if not gap_key or gap_key in output:
            return {}
        output[gap_key] = row
    return output


def approved_stanford_flat_text_parser_manual_reviews_by_gap() -> dict[str, dict[str, str]]:
    summary = read_json(STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_SUMMARY, {})
    if not isinstance(summary, dict):
        return {}
    if not summary.get("gbrain_approval_verified"):
        return {}
    if summary.get("approval_effect_requested") != STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_EFFECT:
        return {}
    if summary.get("rowset_sha256") != STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_ROWSET_SHA256:
        return {}
    if int_value(summary.get("rows")) != STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_ROWS:
        return {}

    rows = read_csv(STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_CSV)
    if len(rows) != STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_ROWS:
        return {}
    output: dict[str, dict[str, str]] = {}
    for row in rows:
        if row.get("approval_effect_if_approved") != STANFORD_FLAT_TEXT_PARSER_MANUAL_REVIEW_EFFECT:
            return {}
        if row.get("gbrain_approval_verified") != "true":
            return {}
        for flag in [
            "person_ingestion_allowed",
            "training_state_mutation_allowed",
            "denominator_closure_allowed",
            "school_verification_allowed",
            "url_rewrite_allowed",
            "identity_collapse_allowed",
        ]:
            if row.get(flag) != "false":
                return {}
        gap_key = row.get("gap_key", "")
        if not gap_key or gap_key in output:
            return {}
        output[gap_key] = row
    return output


def best_stanford_route(rows: list[dict[str, str]]) -> dict[str, str]:
    if not rows:
        return {}
    rank = {
        "current_page_supported_person_rows": 0,
        "shared_current_page_supported_person_rows": 1,
        "second_hop_roster_route_candidate_found": 2,
        "person_structure_without_current_roster_context": 3,
        "candidate_text_context_without_supported_people": 4,
        "faculty_or_leadership_person_structure": 5,
        "related_scope_mismatch": 6,
        "blocked_or_rate_limited": 7,
        "fetch_failed": 8,
        "source_page_http_error": 9,
    }
    return sorted(
        rows,
        key=lambda row: (
            rank.get(row.get("inspection_status", ""), 50),
            -int_value(row.get("supported_person_rows")),
            row.get("program_name", ""),
        ),
    )[0]


def classify_stanford_gap(
    denominator: dict[str, str],
    probe: dict[str, str],
    route_rows: list[dict[str, str]],
    source_rows: list[dict[str, str]],
) -> tuple[str, str, str]:
    route = best_stanford_route(route_rows)
    inspection_status = route.get("inspection_status", "")
    probe_status = probe.get("probe_status", "")
    if inspection_status == "current_page_supported_person_rows":
        return (
            "parser_acceptance_packet_needed",
            "build_exact_parser_acceptance_packet",
            "Extract the current roster rows into an exact non-mutating packet, submit it to GBrain, and only then consider membership ingestion.",
        )
    if inspection_status == "shared_current_page_supported_person_rows":
        return (
            "shared_source_crosswalk_or_residual_scope_needed",
            "build_shared_source_crosswalk_or_disposition_packet",
            "Map shared current-source rows to explicit program sections, or retain the row as non-mutating residual disposition evidence before any person or closure mutation.",
        )
    if inspection_status == "second_hop_roster_route_candidate_found":
        return (
            "second_hop_route_inspection_needed",
            "run_headed_second_hop_route_inspection",
            "Inspect the second-hop candidate and keep outputs non-mutating until exact parser or disposition packets are approved.",
        )
    if inspection_status == "related_scope_mismatch":
        return (
            "related_scope_disposition_needed",
            "build_related_scope_disposition_packet",
            "Packetize the related residency/fellowship mismatch as non-mutating scope evidence; do not close the target denominator row without GBrain approval.",
        )
    if inspection_status in {"person_structure_without_current_roster_context", "candidate_text_context_without_supported_people", "faculty_or_leadership_person_structure"}:
        return (
            "manual_scope_or_exclusion_review_needed",
            "build_manual_scope_review_packet",
            "Review rendered page context and either create a supported current-trainee parser packet or a non-mutating exclusion/disposition packet.",
        )
    if inspection_status in {"blocked_or_rate_limited", "fetch_failed", "source_page_http_error"}:
        return (
            "refetch_or_browser_repair_needed",
            "rerun_headed_fetch_or_source_repair",
            "Repair fetch/source access through headed browser or source search, then rerun route inspection before any closure.",
        )
    if probe_status == "roster_link_candidate" or source_rows:
        return (
            "first_hop_route_inspection_needed",
            "run_headed_route_inspection",
            "Fetch candidate roster links and classify current-person evidence before any parser acceptance or denominator closure.",
        )
    if probe_status == "roster_text_signal_without_link":
        return (
            "flat_text_parser_or_manual_scope_needed",
            "build_flat_text_parser_or_manual_review",
            "Inspect rendered roster text for current named trainees; if supported, build an exact parser packet, otherwise retain non-mutating no-public-roster evidence.",
        )
    if probe_status == "http_error":
        return (
            "program_url_repair_or_source_search_needed",
            "repair_program_url_or_run_source_search",
            "Repair stale/blocked program URLs or find an official replacement source before considering closure.",
        )
    if probe_status == "official_program_context_no_roster_signal":
        return (
            "source_discovery_or_no_public_roster_closure_needed",
            "run_targeted_source_discovery",
            "Run targeted official source discovery; if no public current roster exists, build a closure packet instead of inferring people.",
        )
    return (
        "source_discovery_needed",
        "run_targeted_source_discovery",
        "Continue official source discovery and keep the gap open until a roster source or approved closure packet exists.",
    )


def materialize_stanford(generated_at: str) -> list[dict[str, object]]:
    denominator_rows = [
        row for row in read_csv(ARTIFACTS / "top50_next_school_discovery_manifest.csv")
        if row.get("school_name") == STANFORD_SCHOOL
    ]
    training_summary = read_json(ARTIFACTS / "stanford_training_summary.json", {})
    accepted_programs = set((training_summary if isinstance(training_summary, dict) else {}).get("program_counts", {}).keys())
    probes = {row.get("manifest_key", ""): row for row in read_csv(ARTIFACTS / "stanford_program_page_probe.csv")}
    source_rows = rows_by(read_csv(ARTIFACTS / "stanford_source_candidates.csv"), "manifest_key")
    route_rows = rows_by(read_csv(ARTIFACTS / "stanford_roster_route_inspection.csv"), "manifest_key")
    repair_rows = rows_by(read_csv(ARTIFACTS / "stanford_program_url_repair_probe.csv"), "manifest_key")
    related_scope_dispositions_by_gap = rows_by(
        [
            row
            for row in read_csv(ARTIFACTS / "stanford_gap_drain_queue.csv")
            if row.get("drain_status") == "completed_non_mutating_related_scope_disposition_verified"
        ],
        "gap_key",
    )
    batch2_reconciliations_by_gap = approved_stanford_batch2_disposition_reconciliations_by_gap()
    remaining_manual_scope_reviews_by_gap = approved_stanford_remaining_manual_scope_reviews_by_gap()
    shared_source_crosswalk_dispositions_by_gap = approved_stanford_shared_source_crosswalk_dispositions_by_gap()
    flat_text_parser_manual_reviews_by_gap = approved_stanford_flat_text_parser_manual_reviews_by_gap()

    rows: list[dict[str, object]] = []
    seen_program_names: set[str] = set()
    for denominator in denominator_rows:
        program_name = denominator.get("program_name", "")
        if not program_name or program_name in accepted_programs or program_name in seen_program_names:
            continue
        seen_program_names.add(program_name)
        manifest_key = denominator.get("manifest_key", "")
        probe = probes.get(manifest_key, {})
        routes = route_rows.get(manifest_key, [])
        sources = source_rows.get(manifest_key, [])
        repairs = repair_rows.get(manifest_key, [])
        route = best_stanford_route(routes)
        category, lane, action = classify_stanford_gap(denominator, probe, routes, sources)
        gap_key = "school_gap_resolution_" + stable_key(STANFORD_SCHOOL, manifest_key, program_name)
        approved_related_scope_dispositions = related_scope_dispositions_by_gap.get(gap_key, [])
        approved_batch2_reconciliation = batch2_reconciliations_by_gap.get(gap_key, {})
        approved_remaining_manual_scope_review = remaining_manual_scope_reviews_by_gap.get(gap_key, {})
        approved_shared_source_crosswalk_disposition = shared_source_crosswalk_dispositions_by_gap.get(gap_key, {})
        approved_flat_text_parser_manual_review = flat_text_parser_manual_reviews_by_gap.get(gap_key, {})
        if category == "related_scope_disposition_needed" and approved_related_scope_dispositions:
            category = "related_scope_disposition_recorded_source_discovery_needed"
            lane = "target_program_source_discovery_after_related_scope_exclusion"
            action = (
                "Related-scope evidence is recorded as an approved non-mutating disposition; continue target-program "
                "official source discovery or build a later explicit no-public-roster closure packet."
            )
        if approved_batch2_reconciliation:
            category = "manual_scope_disposition_recorded_followup_needed"
            lane = "target_program_followup_after_manual_scope_disposition"
            prior_action = approved_batch2_reconciliation.get("prior_disposition_recommended_next_action", "")
            action = (
                "Prior approved non-mutating manual-scope disposition is recorded for this gap. "
                f"{prior_action} "
                "This approval does not authorize people, training-state mutation, denominator closure, "
                "Stanford verification, URL rewrite, accepted-source mapping, or identity collapse."
            ).strip()
        if approved_remaining_manual_scope_review:
            category = "manual_scope_review_recorded_followup_needed"
            lane = "target_program_followup_after_manual_scope_review"
            action = (
                "Approved non-mutating manual-scope review recourse is recorded for this gap. "
                f"{approved_remaining_manual_scope_review.get('recourse', '')} "
                "This approval does not authorize people, training-state mutation, denominator closure, "
                "Stanford verification, URL rewrite, unsupported-label ingestion, blocked-row ingestion, "
                "accepted-source mapping, or identity collapse."
            ).strip()
        if approved_shared_source_crosswalk_disposition:
            category = "shared_source_crosswalk_disposition_recorded_source_discovery_needed"
            lane = "target_program_source_discovery_after_shared_source_crosswalk_disposition"
            action = (
                "Approved non-mutating shared-source crosswalk/disposition recourse is recorded for this gap. "
                f"{approved_shared_source_crosswalk_disposition.get('recourse', '')} "
                "This approval does not authorize people, training-state mutation, denominator closure, "
                "Stanford verification, URL rewrite, unsupported-label ingestion, blocked-row ingestion, "
                "accepted-source mapping, or identity collapse."
            ).strip()
        if approved_flat_text_parser_manual_review:
            category = "flat_text_parser_manual_review_recorded_followup_needed"
            lane = "target_program_followup_after_flat_text_parser_manual_review"
            action = (
                "Approved non-mutating flat-text parser/manual-review recourse is recorded for this gap. "
                f"{approved_flat_text_parser_manual_review.get('recourse', '')} "
                "This approval does not authorize people, training-state mutation, denominator closure, "
                "Stanford verification, URL rewrite, unsupported-label ingestion, blocked-row ingestion, "
                "accepted-source mapping, or identity collapse."
            ).strip()
        best_url = (
            approved_batch2_reconciliation.get("prior_disposition_source_url")
            or
            route.get("effective_url")
            or route.get("target_url")
            or probe.get("top_candidate_url")
            or probe.get("effective_url")
            or denominator.get("candidate_program_url")
        )
        best_title = route.get("title") or route.get("target_text") or probe.get("title") or ""
        supported_people = sum(int_value(row.get("supported_person_rows")) for row in routes)
        priority = 900 if category == "parser_acceptance_packet_needed" else 850 if "shared_source" in category else 800 if "second_hop" in category else 700 if sources else 500
        rows.append(
            {
                "gap_key": gap_key,
                "school_key": denominator.get("school_key", ""),
                "school_name": STANFORD_SCHOOL,
                "sponsoring_institution": STANFORD_SPONSOR,
                "program_key": manifest_key,
                "program_name": program_name,
                "program_type": denominator.get("program_type", ""),
                "department_or_group": denominator.get("department_or_group", ""),
                "gap_status": "open_denominator_gap_not_school_verified",
                "coverage_status": "seeded_denominator_no_approved_current_roster_or_closure",
                "captured_people_count": 0,
                "action_lane": lane,
                "blocker_status": category,
                "resolution_category": category,
                "resolution_priority": priority,
                "denominator_url": denominator.get("candidate_program_url", ""),
                "best_evidence_url": best_url,
                "best_evidence_title": best_title,
                "best_evidence_status": (
                    approved_batch2_reconciliation.get("prior_disposition_source_scope_status")
                    or route.get("inspection_status")
                    or probe.get("probe_status")
                    or "not_yet_inspected"
                ),
                "supported_person_rows": supported_people,
                "candidate_source_count": len(sources),
                "approved_non_mutating_disposition_count": (
                    len(approved_related_scope_dispositions)
                    + (1 if approved_batch2_reconciliation else 0)
                    + (1 if approved_remaining_manual_scope_review else 0)
                    + (1 if approved_shared_source_crosswalk_disposition else 0)
                    + (1 if approved_flat_text_parser_manual_review else 0)
                ),
                "recommended_next_action": action,
                "next_operator_lane": lane,
                "mutation_policy": "non_mutating_gap_resolution_manifest; no people, training states, denominator closure, school verification, URL rewrite, or identity collapse without exact GBrain approval",
                "gbrain_strategy_effect": GAP_STRATEGY_EFFECT,
                "gbrain_packet_required_for": "person_ingestion|denominator_closure|stanford_school_verification|url_rewrite|unique_person_collapse",
                "source_artifacts_json": dumps([
                    "artifacts/data/top50_next_school_discovery_manifest.csv",
                    "artifacts/data/stanford_program_page_probe.csv",
                    "artifacts/data/stanford_source_candidates.csv",
                    "artifacts/data/stanford_roster_route_inspection.csv",
                    "artifacts/data/stanford_program_url_repair_probe.csv",
                    "artifacts/data/stanford_gap_drain_queue.csv",
                    "artifacts/data/stanford_related_scope_disposition_packet.csv",
                    "artifacts/data/stanford_gap_batch2_disposition_reconciliation_packet.csv",
                    "artifacts/data/stanford_gap_batch2_disposition_reconciliation_packet_summary.json",
                    "artifacts/data/stanford_remaining_manual_scope_review_packet.csv",
                    "artifacts/data/stanford_remaining_manual_scope_review_packet_summary.json",
                    "artifacts/data/stanford_shared_source_crosswalk_disposition_packet.csv",
                    "artifacts/data/stanford_shared_source_crosswalk_disposition_packet_summary.json",
                    "artifacts/data/stanford_flat_text_parser_manual_review_packet.csv",
                    "artifacts/data/stanford_flat_text_parser_manual_review_packet_summary.json",
                    "artifacts/data/stanford_training_summary.json",
                ]),
                "evidence_json": dumps({
                    "manifest_key": manifest_key,
                    "probe_status": probe.get("probe_status", ""),
                    "route_status_counts": dict(Counter(row.get("inspection_status", "") for row in routes)),
                    "source_candidate_count": len(sources),
                    "repair_status_counts": dict(Counter(row.get("repair_status", "") for row in repairs)),
                    "approved_related_scope_disposition_count": len(approved_related_scope_dispositions),
                    "approved_related_scope_disposition_effects": dict(
                        Counter(row.get("gbrain_decision_effect", "") for row in approved_related_scope_dispositions)
                    ),
                    "approved_related_scope_disposition_status_counts": dict(
                        Counter(row.get("drain_status", "") for row in approved_related_scope_dispositions)
                    ),
                    "approved_batch2_disposition_reconciliation": {
                        "reconciliation_row_key": approved_batch2_reconciliation.get("reconciliation_row_key", ""),
                        "approval_effect": approved_batch2_reconciliation.get("gbrain_decision_effect", ""),
                        "prior_disposition_source_packet": approved_batch2_reconciliation.get("prior_disposition_source_packet", ""),
                        "prior_disposition_packet_row_key": approved_batch2_reconciliation.get("prior_disposition_packet_row_key", ""),
                        "prior_disposition_packet_status": approved_batch2_reconciliation.get("prior_disposition_packet_status", ""),
                        "prior_disposition_source_scope_status": approved_batch2_reconciliation.get("prior_disposition_source_scope_status", ""),
                        "prior_disposition_source_url": approved_batch2_reconciliation.get("prior_disposition_source_url", ""),
                        "manifest_consumption_allowed_after_approval": approved_batch2_reconciliation.get("manifest_consumption_allowed_after_approval", ""),
                    },
                    "approved_remaining_manual_scope_review": {
                        "review_packet_key": approved_remaining_manual_scope_review.get("review_packet_key", ""),
                        "approval_effect": approved_remaining_manual_scope_review.get("gbrain_decision_effect", ""),
                        "manual_review_status": approved_remaining_manual_scope_review.get("manual_review_status", ""),
                        "proposed_gap_disposition": approved_remaining_manual_scope_review.get("proposed_gap_disposition", ""),
                        "proposed_gap_status": approved_remaining_manual_scope_review.get("proposed_gap_status", ""),
                        "required_next_evidence": approved_remaining_manual_scope_review.get("required_next_evidence", ""),
                    },
                    "approved_shared_source_crosswalk_disposition": {
                        "packet_row_key": approved_shared_source_crosswalk_disposition.get("packet_row_key", ""),
                        "approval_effect": approved_shared_source_crosswalk_disposition.get("gbrain_decision_effect", ""),
                        "shared_source_disposition": approved_shared_source_crosswalk_disposition.get("shared_source_disposition", ""),
                        "proposed_gap_status": approved_shared_source_crosswalk_disposition.get("proposed_gap_status", ""),
                        "prior_review_effect": approved_shared_source_crosswalk_disposition.get("prior_review_effect", ""),
                        "required_next_evidence": approved_shared_source_crosswalk_disposition.get("required_next_evidence", ""),
                    },
                    "approved_flat_text_parser_manual_review": {
                        "review_packet_key": approved_flat_text_parser_manual_review.get("review_packet_key", ""),
                        "approval_effect": approved_flat_text_parser_manual_review.get("gbrain_decision_effect", ""),
                        "flat_text_review_status": approved_flat_text_parser_manual_review.get("flat_text_review_status", ""),
                        "parser_work_required": approved_flat_text_parser_manual_review.get("parser_work_required", ""),
                        "proposed_gap_disposition": approved_flat_text_parser_manual_review.get("proposed_gap_disposition", ""),
                        "proposed_gap_status": approved_flat_text_parser_manual_review.get("proposed_gap_status", ""),
                        "required_next_evidence": approved_flat_text_parser_manual_review.get("required_next_evidence", ""),
                    },
                    "accepted_programs_reference": "artifacts/data/stanford_training_summary.json:program_counts",
                }),
                "generated_at": generated_at,
            }
        )
    return rows


def best_vanderbilt_closure(rows: list[dict[str, str]]) -> dict[str, str]:
    if not rows:
        return {}
    rank = {
        "parser_or_manual_review": 0,
        "route_probe_needed": 1,
        "manual_scope_review": 2,
        "source_search_needed": 3,
        "official_url_resolution_needed": 4,
        "candidate_not_current_trainee_exclusion_evidence": 5,
        "retry_or_refetch_needed": 6,
    }
    return sorted(rows, key=lambda row: (rank.get(row.get("closure_status", ""), 50), row.get("program_name", "")))[0]


def classify_vanderbilt_route_packet(packet: dict[str, str]) -> tuple[str, str, str]:
    route_status = packet.get("route_resolution_status", "")
    disposition = packet.get("requested_disposition", "")
    action = packet.get("recommended_next_action", "")
    if route_status == "route_inspected_recursive_or_third_hop_candidate_open":
        return (
            "third_hop_or_directory_route_review_needed",
            "third_hop_route_or_directory_parser_review",
            action or "Inspect recursive/third-hop directory evidence with a page-specific strategy; keep outputs non-mutating.",
        )
    if route_status == "route_inspected_second_hop_chain_open":
        return (
            "second_hop_chain_manual_review_needed",
            "second_hop_chain_manual_or_rendered_review",
            action or "Continue second-hop route review or manual rendered inspection before any person or closure packet.",
        )
    if "related_scope" in disposition:
        return (
            "related_scope_disposition_recorded_source_discovery_needed",
            "target_program_source_discovery_after_related_scope_exclusion",
            action or "Related-scope evidence is recorded; continue searching for a target-program current roster.",
        )
    if "faculty_leadership" in disposition:
        return (
            "faculty_leadership_exclusion_recorded_source_discovery_needed",
            "target_program_source_discovery_after_exclusion",
            action or "Faculty/leadership evidence is recorded; continue target-program source discovery.",
        )
    if "no_supported_person" in disposition:
        return (
            "negative_route_evidence_recorded_manual_or_source_discovery_needed",
            "manual_rendered_review_or_targeted_source_discovery",
            action or "Negative route evidence is recorded; perform rendered/manual review or broader official source discovery before closure.",
        )
    if "mixed_negative_route" in disposition:
        return (
            "mixed_negative_route_evidence_recorded_source_discovery_needed",
            "target_program_source_discovery_after_mixed_negative_evidence",
            action or "Mixed negative route evidence is recorded; continue target-program source discovery.",
        )
    return (
        "approved_route_inspection_recorded_manual_review_needed",
        "manual_route_packet_recourse_review",
        action or "Review approved route-inspection recourse before any closure or mutation packet.",
    )


def classify_vanderbilt_parser_manual_packet(packet: dict[str, str]) -> tuple[str, str, str]:
    classification = packet.get("review_classification", "")
    action = packet.get("recommended_next_action", "")
    if classification == "shared_or_related_program_scope_manual_review_needed":
        return (
            "shared_or_related_program_scope_review_needed",
            "shared_source_program_scope_review_packet",
            action or "Review shared-source section/program scope before any exact acceptance or exclusion packet.",
        )
    if classification == "manual_current_scope_review_needed":
        return (
            "manual_current_scope_review_needed_after_parser_probe",
            "manual_current_scope_review_packet",
            action or "Review rendered current-scope context before any exact acceptance or exclusion packet.",
        )
    if classification == "rendered_page_no_current_named_roster_candidates":
        return (
            "no_current_roster_probe_recorded_source_discovery_or_closure_needed",
            "targeted_source_discovery_or_no_public_roster_closure_packet",
            action or "Use rendered no-current-roster evidence for targeted source discovery or a later no-public-roster closure packet.",
        )
    if classification == "faculty_or_leadership_context_only":
        return (
            "faculty_leadership_parser_exclusion_recorded_source_discovery_needed",
            "target_program_source_discovery_after_parser_exclusion",
            action or "Record faculty/leadership parser hits as exclusions and continue target-program source discovery.",
        )
    if classification == "non_current_context_only":
        return (
            "non_current_parser_exclusion_recorded_source_discovery_needed",
            "target_program_source_discovery_after_non_current_exclusion",
            action or "Record non-current parser hits as exclusions and continue target-program source discovery.",
        )
    return (
        "approved_parser_manual_review_recorded_recourse_needed",
        "manual_parser_recourse_review",
        action or "Review approved parser/manual classification before any closure or mutation packet.",
    )


def classify_vanderbilt_official_url_resolution(packet: dict[str, str]) -> tuple[str, str, str]:
    status = packet.get("resolution_status", "")
    action = packet.get("recommended_next_action", "")
    if status == "verified_exact_program_url":
        return (
            "official_url_resolution_recorded_program_probe_needed",
            "program_page_probe_after_official_url_resolution",
            action or "Probe the approved exact official program URL for current roster routes; keep outputs non-mutating.",
        )
    if status == "verified_parent_or_alias_program_url":
        return (
            "official_parent_url_resolution_recorded_source_discovery_needed",
            "targeted_source_discovery_after_parent_url_resolution",
            action or "Use the approved parent/alias official URL for source discovery and route probing before any closure.",
        )
    if status in {
        "related_or_parent_url_requires_manual_confirmation",
        "official_news_evidence_requires_program_root_confirmation",
    }:
        return (
            "official_context_url_resolution_recorded_manual_confirmation_needed",
            "manual_url_confirmation_after_official_context_resolution",
            action or "Treat the approved URL as official context only and manually confirm target program root before probing.",
        )
    return (
        "official_url_resolution_needed",
        "official_url_repair_or_source_search",
        action or "Resolve the official program URL, then rerun route probing before closure.",
    )


def classify_vanderbilt_official_url_program_page_probe(packet: dict[str, str]) -> tuple[str, str, str]:
    status = packet.get("probe_status", "")
    action = packet.get("recommended_next_action", "")
    if status == "roster_link_candidate":
        return (
            "official_url_probe_roster_route_inspection_needed",
            "active_source_route_inspection_after_official_url_probe",
            action or "Inspect official-page roster-link candidates and build an exact parser/disposition packet before any mutation.",
        )
    if status == "roster_text_signal_without_link":
        return (
            "official_url_probe_rendered_parser_manual_needed",
            "rendered_parser_manual_repair_after_official_url_probe",
            action or "Inspect rendered page text for current named trainees; build exact parser evidence or retain non-mutating no-roster evidence.",
        )
    if status == "official_program_context_no_roster_signal":
        return (
            "official_url_probe_no_roster_signal_source_discovery_or_closure_needed",
            "targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe",
            action or "Record official context evidence, then run targeted source discovery or build a no-public-roster closure packet.",
        )
    if status in {"blocked_or_forbidden", "fetch_failed"}:
        return (
            "official_url_probe_refetch_or_browser_repair_needed",
            "headed_refetch_after_official_url_probe",
            action or "Retry with a headed session or alternate official URL before any parser or closure decision.",
        )
    if status == "http_error":
        return (
            "official_url_probe_http_error_repair_needed",
            "official_url_repair_or_source_search",
            action or "Repair stale/blocked official URL or find a replacement official source.",
        )
    return (
        "official_url_probe_manual_review_or_source_discovery_needed",
        "manual_rendered_review_or_targeted_source_discovery_after_official_url_probe",
        action or "Review the official page probe manually and continue source discovery before any closure.",
    )


def classify_vanderbilt_official_url_probe_route_packet(packet: dict[str, str]) -> tuple[str, str, str]:
    status = packet.get("route_resolution_status", "")
    action = packet.get("recommended_next_action", "")
    if status == "route_inspected_parser_candidate_open":
        return (
            "official_url_probe_route_parser_acceptance_packet_needed",
            "build_exact_parser_acceptance_packet_after_official_url_probe",
            action or "Build an exact parser acceptance packet from the target-scope current roster route before any person ingestion.",
        )
    if status == "route_inspected_flat_text_parser_candidate_open":
        return (
            "official_url_probe_route_flat_text_parser_packet_needed",
            "build_rendered_or_flat_text_parser_packet_after_official_url_probe",
            action or "Build a rendered/flat-text parser packet if names are current target-program trainees.",
        )
    if status == "route_inspected_second_hop_candidate_open":
        return (
            "official_url_probe_route_second_hop_inspection_needed",
            "second_hop_route_inspection_after_official_url_probe",
            action or "Fetch second-hop route candidates and keep output non-mutating until a later exact packet.",
        )
    if status == "route_inspected_related_scope_only_open":
        return (
            "official_url_probe_route_related_scope_recorded_source_discovery_needed",
            "target_program_source_discovery_after_official_url_probe_related_scope",
            action or "Record related-scope route evidence and continue target-program source discovery.",
        )
    if status == "route_inspected_faculty_or_leadership_only_open":
        return (
            "official_url_probe_route_faculty_leadership_recorded_source_discovery_needed",
            "target_program_source_discovery_after_official_url_probe_exclusion",
            action or "Record faculty/leadership route evidence as exclusion evidence and continue target-program source discovery.",
        )
    if status == "route_inspected_context_without_supported_people_open":
        return (
            "official_url_probe_route_negative_context_recorded_manual_or_source_discovery_needed",
            "manual_rendered_review_or_targeted_source_discovery_after_official_url_probe_route",
            action or "Record no-supported-person route evidence and continue manual/rendered review or source discovery.",
        )
    return (
        "official_url_probe_route_manual_review_needed",
        "manual_route_packet_recourse_review_after_official_url_probe",
        action or "Review approved route-inspection recourse before any closure or mutation packet.",
    )


def official_url_resolution_approval_verified(summary: dict, response: dict) -> bool:
    row_count = str(summary.get("rows", ""))
    rowset = str(summary.get("rowset_sha256", ""))
    effect = str(summary.get("approval_effect_requested", ""))
    text = dumps(response)
    return bool(effect and row_count and rowset and effect in text and row_count in text and rowset in text and "APPROVE" in text)


def official_url_probe_route_approval_verified(summary: dict, response: dict) -> bool:
    row_count = str(summary.get("packet_rows", ""))
    rowset = str(summary.get("rowset_sha256", ""))
    effect = str(summary.get("approval_effect_requested", ""))
    text = dumps(response)
    return bool(effect and row_count and rowset and effect in text and row_count in text and rowset in text and "APPROVE" in text)


def classify_vanderbilt_gap(
    coverage: dict[str, str],
    closure: dict[str, str],
    active_targets: list[dict[str, str]],
    route_packet: dict[str, str],
    parser_manual_packet: dict[str, str],
    official_url_resolution_packet: dict[str, str],
    official_url_program_page_probe: dict[str, str],
    official_url_probe_route_packet: dict[str, str],
) -> tuple[str, str, str]:
    closure_status = closure.get("closure_status", "")
    closure_decision = closure.get("closure_decision", "")
    if parser_manual_packet:
        return classify_vanderbilt_parser_manual_packet(parser_manual_packet)
    if route_packet:
        return classify_vanderbilt_route_packet(route_packet)
    if official_url_probe_route_packet:
        return classify_vanderbilt_official_url_probe_route_packet(official_url_probe_route_packet)
    if official_url_program_page_probe:
        return classify_vanderbilt_official_url_program_page_probe(official_url_program_page_probe)
    if official_url_resolution_packet:
        return classify_vanderbilt_official_url_resolution(official_url_resolution_packet)
    if closure_status == "parser_or_manual_review":
        return (
            "parser_or_manual_review_needed",
            "rendered_parser_manual_repair",
            closure.get("recommended_next_action") or "Inspect rendered current-roster text and create an exact GBrain packet only for evidence-ready person rows.",
        )
    if closure_status == "route_probe_needed" or active_targets:
        return (
            "active_source_or_second_hop_route_probe_needed",
            "active_source_route_inspection",
            closure.get("recommended_next_action") or "Inspect active candidate URLs and second-hop routes; keep parser outputs non-mutating until exact GBrain approval.",
        )
    if closure_status == "manual_scope_review":
        return (
            "scope_mapping_or_exclusion_packet_needed",
            "scope_mapping_disposition_packet",
            closure.get("recommended_next_action") or "Packetize related-scope or faculty/context evidence as non-mutating disposition before any closure.",
        )
    if closure_status == "official_url_resolution_needed":
        return (
            "official_url_resolution_needed",
            "official_url_repair_or_source_search",
            closure.get("recommended_next_action") or "Resolve the official program URL, then rerun route probing before closure.",
        )
    if closure_status == "source_search_needed":
        return (
            "broad_source_discovery_needed",
            "targeted_official_source_search",
            closure.get("recommended_next_action") or "Run targeted official source discovery; do not infer people from context pages.",
        )
    if closure_status == "candidate_not_current_trainee_exclusion_evidence":
        return (
            "non_mutating_exclusion_or_no_public_roster_packet_needed",
            "closure_disposition_packet",
            closure.get("recommended_next_action") or "Use candidate-source exclusion only as non-mutating evidence unless GBrain approves denominator closure.",
        )
    if closure_status == "retry_or_refetch_needed":
        return (
            "retry_or_refetch_needed",
            "headed_refetch",
            closure.get("recommended_next_action") or "Retry/refetch the candidate source before deciding parser or closure posture.",
        )
    if coverage.get("discovery_url"):
        return (
            "first_hop_program_probe_needed",
            "program_page_probe",
            "Probe the linked official Vanderbilt program URL for current roster routes before person ingestion or closure.",
        )
    return (
        "official_source_discovery_needed",
        "targeted_official_source_search",
        "Find an official Vanderbilt program/current-roster source or build explicit no-public-roster closure evidence.",
    )


def materialize_vanderbilt(generated_at: str) -> list[dict[str, object]]:
    coverage_rows = read_json(ARTIFACTS / "vanderbilt_gme_program_coverage.json", [])
    coverage = coverage_rows if isinstance(coverage_rows, list) else []
    closures_by_program = rows_by(read_csv(ARTIFACTS / "vanderbilt_candidate_closure_audit.csv"), "official_program_key")
    residuals = {row.get("official_program_key", ""): row for row in read_csv(ARTIFACTS / "vanderbilt_residual_drain_log.csv")}
    active_targets_by_program = rows_by(read_csv(ARTIFACTS / "vanderbilt_active_source_candidate_targets.csv"), "official_program_key")
    active_inspections_by_program = rows_by(read_csv(ARTIFACTS / "vanderbilt_active_source_candidate_route_inspection.csv"), "official_program_key")
    approved_route_packet_by_program = {
        row.get("program_key", ""): row
        for row in read_csv(ARTIFACTS / "vanderbilt_active_source_route_inspection_packet.csv")
        if row.get("approval_effect_if_approved") == "vanderbilt_active_source_route_inspection_76_non_mutating_approved"
    }
    approved_parser_manual_packet_by_program = {
        row.get("program_key", ""): row
        for row in read_csv(ARTIFACTS / "vanderbilt_parser_manual_review_35_packet.csv")
        if row.get("approval_effect_if_approved") == "vanderbilt_parser_manual_review_35_non_mutating_approved"
    }
    official_url_resolution_summary = read_json(ARTIFACTS / "vanderbilt_official_url_resolution_packet_summary.json", {})
    official_url_resolution_response = read_json(ARTIFACTS / "gbrain_vanderbilt_official_url_resolution_24_http_mcp_response.json", {})
    official_url_resolution_approved = (
        isinstance(official_url_resolution_summary, dict)
        and isinstance(official_url_resolution_response, dict)
        and official_url_resolution_approval_verified(official_url_resolution_summary, official_url_resolution_response)
    )
    approved_official_url_resolution_by_program = {
        row.get("program_key", ""): row
        for row in read_csv(ARTIFACTS / "vanderbilt_official_url_resolution_packet.csv")
        if official_url_resolution_approved
        and row.get("approval_effect_if_approved") == "vanderbilt_official_url_resolution_24_non_mutating_approved"
    }
    official_url_program_page_probe_by_program = {
        row.get("program_key", ""): row
        for row in read_csv(ARTIFACTS / "vanderbilt_official_url_program_page_probe.csv")
        if row.get("probe_effect_if_recorded") == "vanderbilt_official_url_program_page_probe_12_non_mutating_recorded"
        and row.get("person_ingestion_allowed") == "false"
        and row.get("denominator_closure_allowed") == "false"
        and row.get("school_verification_allowed") == "false"
        and row.get("url_rewrite_allowed") == "false"
        and row.get("identity_collapse_allowed") == "false"
    }
    official_url_probe_route_summary = read_json(ARTIFACTS / "vanderbilt_official_url_probe_route_inspection_packet_summary.json", {})
    official_url_probe_route_response = read_json(ARTIFACTS / "gbrain_vanderbilt_official_url_probe_route_inspection_7_http_mcp_response.json", {})
    official_url_probe_route_approved = (
        isinstance(official_url_probe_route_summary, dict)
        and isinstance(official_url_probe_route_response, dict)
        and official_url_probe_route_approval_verified(official_url_probe_route_summary, official_url_probe_route_response)
    )
    official_url_probe_route_packet_by_program = {
        row.get("program_key", ""): row
        for row in read_csv(ARTIFACTS / "vanderbilt_official_url_probe_route_inspection_packet.csv")
        if official_url_probe_route_approved
        and row.get("approval_effect_if_approved") == "vanderbilt_official_url_probe_route_inspection_7_non_mutating_approved"
        and row.get("person_ingestion_allowed") == "false"
        and row.get("denominator_closure_allowed") == "false"
        and row.get("school_verification_allowed") == "false"
        and row.get("url_rewrite_allowed") == "false"
        and row.get("identity_collapse_allowed") == "false"
    }
    dispositions_by_program = rows_by(read_csv(ARTIFACTS / "vanderbilt_approved_candidate_source_dispositions.csv"), "official_program_key")
    mixed_negative_summary = read_json(
        ARTIFACTS / "vanderbilt_mixed_negative_source_discovery_disposition_packet_summary.json", {}
    )
    mixed_negative_approved = (
        isinstance(mixed_negative_summary, dict)
        and mixed_negative_summary.get("packet_status")
        == "approved_exact_gbrain_non_mutating_mixed_negative_disposition"
        and mixed_negative_summary.get("gbrain_approval_verified") is True
        and mixed_negative_summary.get("approval_effect_requested")
        == "vanderbilt_mixed_negative_source_discovery_disposition_approved"
        and mixed_negative_summary.get("rows") == 9
        and mixed_negative_summary.get("rowset_sha256")
        == "ef617a52aea162611c40a00bd294ea1aacb27d88f5e1928635544ab4f090092a"
    )
    mixed_negative_dispositions_by_program = rows_by(
        [
            row
            for row in read_csv(ARTIFACTS / "vanderbilt_mixed_negative_source_discovery_disposition_packet.csv")
            if mixed_negative_approved
            and row.get("approval_effect_if_approved") == "vanderbilt_mixed_negative_source_discovery_disposition_approved"
            and row.get("person_ingestion_allowed") == "false"
            and row.get("denominator_closure_allowed") == "false"
            and row.get("school_verification_allowed") == "false"
            and row.get("url_rewrite_allowed") == "false"
            and row.get("identity_collapse_allowed") == "false"
        ],
        "program_key",
    )
    execution_order8_summary = read_json(
        ARTIFACTS / "vanderbilt_execution_order8_negative_route_manual_review_disposition_packet_summary.json", {}
    )
    execution_order8_approved = (
        isinstance(execution_order8_summary, dict)
        and execution_order8_summary.get("packet_status")
        == "approved_exact_gbrain_non_mutating_execution_order8_disposition"
        and execution_order8_summary.get("gbrain_approval_verified") is True
        and execution_order8_summary.get("approval_effect_requested")
        == "vanderbilt_execution_order_8_negative_route_manual_review_disposition_non_mutating_approved"
        and execution_order8_summary.get("rows") == 23
        and execution_order8_summary.get("rowset_sha256")
        == "892f3765ecae9792f3e872a30265d50866763f84efbbdda6c814039adad5ded9"
    )
    execution_order8_dispositions_by_program = rows_by(
        [
            row
            for row in read_csv(ARTIFACTS / "vanderbilt_execution_order8_negative_route_manual_review_disposition_packet.csv")
            if execution_order8_approved
            and row.get("approval_effect_if_approved")
            == "vanderbilt_execution_order_8_negative_route_manual_review_disposition_non_mutating_approved"
            and row.get("person_ingestion_allowed") == "false"
            and row.get("denominator_closure_allowed") == "false"
            and row.get("school_verification_allowed") == "false"
            and row.get("url_rewrite_allowed") == "false"
            and row.get("identity_collapse_allowed") == "false"
        ],
        "program_key",
    )
    execution_order9_summary = read_json(
        ARTIFACTS / "vanderbilt_execution_order9_second_hop_manual_review_disposition_packet_summary.json", {}
    )
    execution_order9_approved = (
        isinstance(execution_order9_summary, dict)
        and execution_order9_summary.get("packet_status")
        == "approved_exact_gbrain_non_mutating_execution_order9_disposition"
        and execution_order9_summary.get("gbrain_approval_verified") is True
        and execution_order9_summary.get("approval_effect_requested")
        == "vanderbilt_execution_order_9_second_hop_manual_review_disposition_non_mutating_approved"
        and execution_order9_summary.get("rows") == 3
        and execution_order9_summary.get("rowset_sha256")
        == "60124e7d3699f82a3f30b16aad8dc48b828f6fd84d5f83be9534a9524f9acb41"
    )
    execution_order9_dispositions_by_program = rows_by(
        [
            row
            for row in read_csv(ARTIFACTS / "vanderbilt_execution_order9_second_hop_manual_review_disposition_packet.csv")
            if execution_order9_approved
            and row.get("approval_effect_if_approved")
            == "vanderbilt_execution_order_9_second_hop_manual_review_disposition_non_mutating_approved"
            and row.get("person_ingestion_allowed") == "false"
            and row.get("denominator_closure_allowed") == "false"
            and row.get("school_verification_allowed") == "false"
            and row.get("url_rewrite_allowed") == "false"
            and row.get("identity_collapse_allowed") == "false"
        ],
        "program_key",
    )
    execution_order9_remainder_summary = read_json(VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_SUMMARY, {})
    execution_order9_remainder_approved = (
        isinstance(execution_order9_remainder_summary, dict)
        and execution_order9_remainder_summary.get("packet_status")
        == "approved_exact_gbrain_non_mutating_execution_order9_remainder_disposition"
        and execution_order9_remainder_summary.get("gbrain_approval_verified") is True
        and execution_order9_remainder_summary.get("approval_effect_requested")
        == VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_EFFECT
        and execution_order9_remainder_summary.get("rows") == VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_ROWS
        and execution_order9_remainder_summary.get("rowset_sha256")
        == VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_ROWSET_SHA256
    )
    execution_order9_remainder_dispositions_by_program = rows_by(
        [
            row
            for row in read_csv(VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_CSV)
            if execution_order9_remainder_approved
            and row.get("approval_effect_if_approved") == VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_EFFECT
            and row.get("person_ingestion_allowed") == "false"
            and row.get("training_state_mutation_allowed") == "false"
            and row.get("denominator_closure_allowed") == "false"
            and row.get("school_verification_allowed") == "false"
            and row.get("url_rewrite_allowed") == "false"
            and row.get("identity_collapse_allowed") == "false"
        ],
        "program_key",
    )
    related_scope_source_discovery_summary = read_json(VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_SUMMARY, {})
    related_scope_source_discovery_approved = (
        isinstance(related_scope_source_discovery_summary, dict)
        and related_scope_source_discovery_summary.get("packet_status")
        == "approved_exact_gbrain_non_mutating_related_scope_source_discovery_disposition"
        and related_scope_source_discovery_summary.get("gbrain_approval_verified") is True
        and related_scope_source_discovery_summary.get("approval_effect_requested")
        == VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_EFFECT
        and related_scope_source_discovery_summary.get("rows") == VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_ROWS
        and related_scope_source_discovery_summary.get("rowset_sha256")
        == VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_ROWSET_SHA256
    )
    related_scope_source_discovery_dispositions_by_program = rows_by(
        [
            row
            for row in read_csv(VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_CSV)
            if related_scope_source_discovery_approved
            and row.get("approval_effect_if_approved") == VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_EFFECT
            and row.get("person_ingestion_allowed") == "false"
            and row.get("training_state_mutation_allowed") == "false"
            and row.get("denominator_closure_allowed") == "false"
            and row.get("school_verification_allowed") == "false"
            and row.get("url_rewrite_allowed") == "false"
            and row.get("identity_collapse_allowed") == "false"
        ],
        "program_key",
    )
    execution_order11_blocked_summary = read_json(
        ARTIFACTS / "vanderbilt_execution_order11_blocked_shared_source_disposition_packet_summary.json", {}
    )
    execution_order11_blocked_approved = (
        isinstance(execution_order11_blocked_summary, dict)
        and execution_order11_blocked_summary.get("packet_status")
        == "approved_exact_gbrain_execution_order11_blocked_shared_source_disposition"
        and execution_order11_blocked_summary.get("gbrain_approval_verified") is True
        and execution_order11_blocked_summary.get("approval_effect_requested")
        == "vanderbilt_execution_order11_blocked_shared_source_disposition_5_non_mutating_approved"
        and execution_order11_blocked_summary.get("rows") == 5
        and execution_order11_blocked_summary.get("rowset_sha256")
        == "ae90c3183969729970e6d67adb017255e5a3f3287c4a654875ab9ee06abcd261"
    )
    execution_order11_blocked_dispositions_by_program = rows_by(
        [
            row
            for row in read_csv(ARTIFACTS / "vanderbilt_execution_order11_blocked_shared_source_disposition_packet.csv")
            if execution_order11_blocked_approved
            and row.get("approval_effect_if_approved")
            == "vanderbilt_execution_order11_blocked_shared_source_disposition_5_non_mutating_approved"
            and row.get("person_ingestion_allowed") == "false"
            and row.get("denominator_closure_allowed") == "false"
            and row.get("school_verification_allowed") == "false"
            and row.get("url_rewrite_allowed") == "false"
            and row.get("identity_collapse_allowed") == "false"
        ],
        "program_key",
    )

    rows: list[dict[str, object]] = []
    for row in coverage:
        program_key = row.get("entry_key", "")
        if str(row.get("coverage_status", "")).startswith("covered_"):
            continue
        closure = best_vanderbilt_closure(closures_by_program.get(program_key, []))
        active_targets = active_targets_by_program.get(program_key, [])
        active_inspections = active_inspections_by_program.get(program_key, [])
        approved_route_packet = approved_route_packet_by_program.get(program_key, {})
        approved_parser_manual_packet = approved_parser_manual_packet_by_program.get(program_key, {})
        approved_official_url_resolution = approved_official_url_resolution_by_program.get(program_key, {})
        official_url_program_page_probe = official_url_program_page_probe_by_program.get(program_key, {})
        official_url_probe_route_packet = official_url_probe_route_packet_by_program.get(program_key, {})
        dispositions = (
            dispositions_by_program.get(program_key, [])
            + mixed_negative_dispositions_by_program.get(program_key, [])
            + execution_order8_dispositions_by_program.get(program_key, [])
            + execution_order9_dispositions_by_program.get(program_key, [])
            + execution_order9_remainder_dispositions_by_program.get(program_key, [])
            + related_scope_source_discovery_dispositions_by_program.get(program_key, [])
            + execution_order11_blocked_dispositions_by_program.get(program_key, [])
        )
        approved_execution_order9_remainder_disposition = (
            execution_order9_remainder_dispositions_by_program.get(program_key, [{}])[0]
            if execution_order9_remainder_dispositions_by_program.get(program_key)
            else {}
        )
        approved_related_scope_source_discovery_disposition = (
            related_scope_source_discovery_dispositions_by_program.get(program_key, [{}])[0]
            if related_scope_source_discovery_dispositions_by_program.get(program_key)
            else {}
        )
        residual = residuals.get(program_key, {})
        category, lane, action = classify_vanderbilt_gap(
            row,
            closure,
            active_targets,
            approved_route_packet,
            approved_parser_manual_packet,
            approved_official_url_resolution,
            official_url_program_page_probe,
            official_url_probe_route_packet,
        )
        if approved_execution_order9_remainder_disposition:
            category = approved_execution_order9_remainder_disposition.get("proposed_gap_status", "") or category
            lane = approved_execution_order9_remainder_disposition.get("proposed_next_operator_lane", "") or lane
            action = approved_execution_order9_remainder_disposition.get("recommended_next_action", "") or action
        if approved_related_scope_source_discovery_disposition:
            category = approved_related_scope_source_discovery_disposition.get("proposed_gap_status", "") or category
            lane = approved_related_scope_source_discovery_disposition.get("proposed_next_operator_lane", "") or lane
            action = approved_related_scope_source_discovery_disposition.get("recommended_next_action", "") or action
        best_url = (
            approved_related_scope_source_discovery_disposition.get("target_effective_url")
            or
            approved_execution_order9_remainder_disposition.get("source_url")
            or
            approved_parser_manual_packet.get("best_evidence_url")
            or approved_parser_manual_packet.get("denominator_url")
            or
            approved_route_packet.get("best_evidence_url")
            or approved_route_packet.get("denominator_url")
            or official_url_probe_route_packet.get("source_probe_url")
            or official_url_program_page_probe.get("top_candidate_url")
            or official_url_program_page_probe.get("effective_url")
            or official_url_program_page_probe.get("target_url")
            or approved_official_url_resolution.get("proposed_effective_url")
            or approved_official_url_resolution.get("proposed_official_url")
            or
            closure.get("effective_url")
            or closure.get("target_url")
            or residual.get("candidate_url")
            or row.get("discovery_url")
        )
        best_title = (
            approved_related_scope_source_discovery_disposition.get("target_source_title")
            or
            approved_execution_order9_remainder_disposition.get("source_title")
            or
            approved_parser_manual_packet.get("best_evidence_title")
            or approved_route_packet.get("best_evidence_title")
            or official_url_probe_route_packet.get("source_probe_title")
            or official_url_program_page_probe.get("top_candidate_text")
            or official_url_program_page_probe.get("title")
            or approved_official_url_resolution.get("title")
            or closure.get("title")
            or residual.get("candidate_url")
            or row.get("discovery_title")
            or ""
        )
        probe_candidate_count = int_value(official_url_program_page_probe.get("candidate_roster_link_count"))
        route_packet_candidate_count = int_value(official_url_probe_route_packet.get("route_rows"))
        priority = (
            int_value(residual.get("priority"))
            or (
                840
                if official_url_probe_route_packet.get("route_resolution_status") == "route_inspected_parser_candidate_open"
                else 800 if official_url_probe_route_packet else 780 if probe_candidate_count else 720 if official_url_program_page_probe else 760 if active_targets else 650 if closure else 500
            )
        )
        rows.append(
            {
                "gap_key": "school_gap_resolution_" + stable_key(VANDERBILT_SCHOOL, program_key),
                "school_key": "brimr_2024_school_005",
                "school_name": VANDERBILT_SCHOOL,
                "sponsoring_institution": VANDERBILT_SPONSOR,
                "program_key": program_key,
                "program_name": row.get("discovery_title", "") or closure.get("program_name", ""),
                "program_type": closure.get("program_type", "") or "",
                "department_or_group": closure.get("department", "") or "",
                "gap_status": "open_denominator_gap_not_school_verified",
                "coverage_status": row.get("coverage_status", ""),
                "captured_people_count": row.get("captured_people_count", 0),
                "action_lane": lane if (approved_execution_order9_remainder_disposition or approved_related_scope_source_discovery_disposition) else residual.get("action_lane", "") or lane,
                "blocker_status": category if (approved_execution_order9_remainder_disposition or approved_related_scope_source_discovery_disposition) else residual.get("blocker_status", "") or category,
                "resolution_category": category,
                "resolution_priority": priority,
                "denominator_url": row.get("discovery_url", ""),
                "best_evidence_url": best_url,
                "best_evidence_title": best_title,
                "best_evidence_status": (
                    approved_related_scope_source_discovery_disposition.get("target_candidate_status")
                    or
                    approved_execution_order9_remainder_disposition.get("workbench_scope_status")
                    or approved_execution_order9_remainder_disposition.get("workbench_classification")
                    or
                    official_url_probe_route_packet.get("route_resolution_status")
                    or
                    official_url_program_page_probe.get("probe_status")
                    or closure.get("closure_status")
                    or closure.get("closure_decision")
                    or "not_yet_audited"
                ),
                "supported_person_rows": closure.get("supported_person_rows", 0),
                "candidate_source_count": len(active_targets) + (route_packet_candidate_count or probe_candidate_count),
                "approved_non_mutating_disposition_count": len(dispositions),
                "recommended_next_action": action,
                "next_operator_lane": lane,
                "mutation_policy": "non_mutating_gap_resolution_manifest; no people, training states, denominator closure, Vanderbilt school verification, or identity collapse without exact GBrain approval",
                "gbrain_strategy_effect": GAP_STRATEGY_EFFECT,
                "gbrain_packet_required_for": "person_ingestion|denominator_closure|vanderbilt_school_verification|unique_person_collapse",
                "source_artifacts_json": dumps([
                    "artifacts/data/vanderbilt_gme_program_coverage.json",
                    "artifacts/data/vanderbilt_residual_drain_log.csv",
                    "artifacts/data/vanderbilt_candidate_closure_audit.csv",
                    "artifacts/data/vanderbilt_active_source_candidate_targets.csv",
                    "artifacts/data/vanderbilt_active_source_candidate_route_inspection.csv",
                    "artifacts/data/vanderbilt_active_source_route_inspection_packet.csv",
                    "artifacts/data/vanderbilt_parser_manual_review_35_packet.csv",
                    "artifacts/data/vanderbilt_official_url_resolution_packet.csv",
                    "artifacts/data/vanderbilt_official_url_program_page_probe.csv",
                    "artifacts/data/vanderbilt_official_url_probe_route_inspection_packet.csv",
                    "artifacts/data/gbrain_vanderbilt_official_url_probe_route_inspection_7_http_mcp_response.json",
                    "artifacts/data/gbrain_vanderbilt_official_url_resolution_24_http_mcp_response.json",
                    "artifacts/data/vanderbilt_approved_candidate_source_dispositions.csv",
                    "artifacts/data/vanderbilt_mixed_negative_source_discovery_disposition_packet.csv",
                    "artifacts/data/vanderbilt_mixed_negative_source_discovery_disposition_packet_summary.json",
                    "artifacts/data/vanderbilt_execution_order8_negative_route_manual_review_disposition_packet.csv",
                    "artifacts/data/vanderbilt_execution_order8_negative_route_manual_review_disposition_packet_summary.json",
                    "artifacts/data/vanderbilt_execution_order9_second_hop_manual_review_disposition_packet.csv",
                    "artifacts/data/vanderbilt_execution_order9_second_hop_manual_review_disposition_packet_summary.json",
                    "artifacts/data/vanderbilt_execution_order9_remainder_disposition_packet.csv",
                    "artifacts/data/vanderbilt_execution_order9_remainder_disposition_packet_summary.json",
                    "artifacts/data/vanderbilt_related_scope_source_discovery_workbench.csv",
                    "artifacts/data/vanderbilt_related_scope_source_discovery_workbench_summary.json",
                    "artifacts/data/vanderbilt_related_scope_source_discovery_disposition_packet.csv",
                    "artifacts/data/vanderbilt_related_scope_source_discovery_disposition_packet_summary.json",
                    "artifacts/data/vanderbilt_execution_order11_blocked_shared_source_disposition_packet.csv",
                    "artifacts/data/vanderbilt_execution_order11_blocked_shared_source_disposition_packet_summary.json",
                ]),
                "evidence_json": dumps({
                    "coverage": {
                        "coverage_status": row.get("coverage_status", ""),
                        "match_method": row.get("match_method", ""),
                        "notes": row.get("notes", ""),
                    },
                    "closure": {
                        "closure_status": closure.get("closure_status", ""),
                        "closure_decision": closure.get("closure_decision", ""),
                        "target_kind": closure.get("target_kind", ""),
                    },
                    "active_source_target_count": len(active_targets),
                    "active_source_inspection_status_counts": dict(Counter(item.get("inspection_status", "") for item in active_inspections)),
                    "approved_route_inspection_packet": {
                        "packet_row_key": approved_route_packet.get("packet_row_key", ""),
                        "approval_effect": approved_route_packet.get("approval_effect_if_approved", ""),
                        "route_resolution_status": approved_route_packet.get("route_resolution_status", ""),
                        "requested_disposition": approved_route_packet.get("requested_disposition", ""),
                    },
                    "approved_parser_manual_review_packet": {
                        "packet_row_key": approved_parser_manual_packet.get("packet_row_key", ""),
                        "approval_effect": approved_parser_manual_packet.get("approval_effect_if_approved", ""),
                        "review_classification": approved_parser_manual_packet.get("review_classification", ""),
                        "requested_disposition": approved_parser_manual_packet.get("requested_disposition", ""),
                    },
                    "approved_official_url_resolution_packet": {
                        "official_url_resolution_key": approved_official_url_resolution.get("official_url_resolution_key", ""),
                        "approval_effect": approved_official_url_resolution.get("approval_effect_if_approved", ""),
                        "proposed_url_role": approved_official_url_resolution.get("proposed_url_role", ""),
                        "resolution_status": approved_official_url_resolution.get("resolution_status", ""),
                        "resolution_confidence": approved_official_url_resolution.get("resolution_confidence", ""),
                        "proposed_effective_url": approved_official_url_resolution.get("proposed_effective_url", ""),
                    },
                    "official_url_program_page_probe": {
                        "probe_key": official_url_program_page_probe.get("official_url_program_page_probe_key", ""),
                        "probe_effect": official_url_program_page_probe.get("probe_effect_if_recorded", ""),
                        "probe_status": official_url_program_page_probe.get("probe_status", ""),
                        "candidate_roster_link_count": official_url_program_page_probe.get("candidate_roster_link_count", ""),
                        "top_candidate_url": official_url_program_page_probe.get("top_candidate_url", ""),
                        "html_dump_path": official_url_program_page_probe.get("html_dump_path", ""),
                        "capture_json_path": official_url_program_page_probe.get("capture_json_path", ""),
                    },
                    "official_url_probe_route_packet": {
                        "packet_row_key": official_url_probe_route_packet.get("packet_row_key", ""),
                        "approval_effect": official_url_probe_route_packet.get("approval_effect_if_approved", ""),
                        "route_resolution_status": official_url_probe_route_packet.get("route_resolution_status", ""),
                        "requested_disposition": official_url_probe_route_packet.get("requested_disposition", ""),
                        "route_rows": official_url_probe_route_packet.get("route_rows", ""),
                        "inspection_statuses_json": official_url_probe_route_packet.get("inspection_statuses_json", ""),
                        "scope_statuses_json": official_url_probe_route_packet.get("scope_statuses_json", ""),
                    },
                    "approved_disposition_count": len(dispositions),
                    "approved_disposition_denominator_closure_allowed": dict(Counter(item.get("denominator_closure_allowed", "") for item in dispositions)),
                    "approved_mixed_negative_source_discovery_disposition": {
                        "approval_effect": (
                            "vanderbilt_mixed_negative_source_discovery_disposition_approved"
                            if mixed_negative_dispositions_by_program.get(program_key)
                            else ""
                        ),
                        "packet_rows": len(mixed_negative_dispositions_by_program.get(program_key, [])),
                        "packet_status": mixed_negative_summary.get("packet_status", "") if mixed_negative_dispositions_by_program.get(program_key) else "",
                    },
                    "approved_execution_order8_negative_route_manual_review_disposition": {
                        "approval_effect": (
                            "vanderbilt_execution_order_8_negative_route_manual_review_disposition_non_mutating_approved"
                            if execution_order8_dispositions_by_program.get(program_key)
                            else ""
                        ),
                        "packet_rows": len(execution_order8_dispositions_by_program.get(program_key, [])),
                        "packet_status": (
                            execution_order8_summary.get("packet_status", "")
                            if execution_order8_dispositions_by_program.get(program_key)
                            else ""
                        ),
                    },
                    "approved_execution_order9_second_hop_manual_review_disposition": {
                        "approval_effect": (
                            "vanderbilt_execution_order_9_second_hop_manual_review_disposition_non_mutating_approved"
                            if execution_order9_dispositions_by_program.get(program_key)
                            else ""
                        ),
                        "packet_rows": len(execution_order9_dispositions_by_program.get(program_key, [])),
                        "packet_status": (
                            execution_order9_summary.get("packet_status", "")
                            if execution_order9_dispositions_by_program.get(program_key)
                            else ""
                        ),
                    },
                    "approved_execution_order9_remainder_disposition": {
                        "approval_effect": (
                            VANDERBILT_EXECUTION_ORDER9_REMAINDER_DISPOSITION_EFFECT
                            if approved_execution_order9_remainder_disposition
                            else ""
                        ),
                        "packet_row_key": approved_execution_order9_remainder_disposition.get("packet_row_key", ""),
                        "packet_rows": len(execution_order9_remainder_dispositions_by_program.get(program_key, [])),
                        "packet_status": (
                            execution_order9_remainder_summary.get("packet_status", "")
                            if approved_execution_order9_remainder_disposition
                            else ""
                        ),
                        "proposed_disposition": approved_execution_order9_remainder_disposition.get("proposed_disposition", ""),
                        "proposed_gap_status": approved_execution_order9_remainder_disposition.get("proposed_gap_status", ""),
                        "proposed_next_operator_lane": approved_execution_order9_remainder_disposition.get("proposed_next_operator_lane", ""),
                        "required_next_evidence": approved_execution_order9_remainder_disposition.get("required_next_evidence", ""),
                    },
                    "approved_related_scope_source_discovery_disposition": {
                        "approval_effect": (
                            VANDERBILT_RELATED_SCOPE_SOURCE_DISCOVERY_DISPOSITION_EFFECT
                            if approved_related_scope_source_discovery_disposition
                            else ""
                        ),
                        "packet_row_key": approved_related_scope_source_discovery_disposition.get("packet_row_key", ""),
                        "packet_rows": len(related_scope_source_discovery_dispositions_by_program.get(program_key, [])),
                        "packet_status": (
                            related_scope_source_discovery_summary.get("packet_status", "")
                            if approved_related_scope_source_discovery_disposition
                            else ""
                        ),
                        "target_candidate_status": approved_related_scope_source_discovery_disposition.get("target_candidate_status", ""),
                        "target_effective_url": approved_related_scope_source_discovery_disposition.get("target_effective_url", ""),
                        "related_scope_exclusion_url": approved_related_scope_source_discovery_disposition.get("related_scope_exclusion_url", ""),
                        "proposed_disposition": approved_related_scope_source_discovery_disposition.get("proposed_disposition", ""),
                        "proposed_gap_status": approved_related_scope_source_discovery_disposition.get("proposed_gap_status", ""),
                        "proposed_next_operator_lane": approved_related_scope_source_discovery_disposition.get("proposed_next_operator_lane", ""),
                        "required_next_evidence": approved_related_scope_source_discovery_disposition.get("required_next_evidence", ""),
                    },
                    "approved_execution_order11_blocked_shared_source_disposition": {
                        "approval_effect": (
                            "vanderbilt_execution_order11_blocked_shared_source_disposition_5_non_mutating_approved"
                            if execution_order11_blocked_dispositions_by_program.get(program_key)
                            else ""
                        ),
                        "packet_rows": len(execution_order11_blocked_dispositions_by_program.get(program_key, [])),
                        "packet_status": (
                            execution_order11_blocked_summary.get("packet_status", "")
                            if execution_order11_blocked_dispositions_by_program.get(program_key)
                            else ""
                        ),
                    },
                }),
                "generated_at": generated_at,
            }
        )
    return rows


def build_summary(
    rows: list[dict[str, object]],
    generated_at: str,
    suppressed_verified_school_rows: dict[str, int],
) -> dict[str, object]:
    by_school = Counter(str(row["school_name"]) for row in rows)
    by_school_category: dict[str, dict[str, int]] = {}
    for school in sorted(by_school):
        school_rows = [row for row in rows if row["school_name"] == school]
        by_school_category[school] = dict(Counter(str(row["resolution_category"]) for row in school_rows))
    return {
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "generated_at": generated_at,
        "rows": len(rows),
        "open_gap_rows": len(rows),
        "by_school": dict(by_school),
        "by_school_resolution_category": by_school_category,
        "by_next_operator_lane": dict(Counter(str(row["next_operator_lane"]) for row in rows)),
        "supported_person_gap_rows": sum(1 for row in rows if int_value(row.get("supported_person_rows")) > 0),
        "candidate_source_gap_rows": sum(1 for row in rows if int_value(row.get("candidate_source_count")) > 0),
        "approved_non_mutating_disposition_gap_rows": sum(1 for row in rows if int_value(row.get("approved_non_mutating_disposition_count")) > 0),
        "suppressed_verified_school_raw_gap_rows_by_school": suppressed_verified_school_rows,
        "policy": "Non-mutating gap-resolution manifest requested by GBrain after Stanford lifecycle repair. It maps remaining unverified-school denominator gaps to evidence and recourse, but it cannot mutate roster truth, denominator closure, school verification, training states, URL rewrites, or unique-person identity collapse. A verified school's raw denominator gap rows are suppressed only when an exact approved school-readiness packet and drained queue are present.",
        "gbrain_strategy_effect": GAP_STRATEGY_EFFECT,
        "school_priority_order": [STANFORD_SCHOOL, VANDERBILT_SCHOOL],
        "mutation_allowed": False,
    }


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    previous_summary = read_json(SUMMARY_OUT, {})
    stanford_rows = materialize_stanford(generated_at)
    suppressed_verified_school_rows: dict[str, int] = {}
    if stanford_school_verification_approved():
        suppressed_verified_school_rows[STANFORD_SCHOOL] = len(stanford_rows)
        stanford_rows = []
    rows = stanford_rows + materialize_vanderbilt(generated_at)
    guard_nonempty_manifest(rows, previous_summary)
    rows.sort(
        key=lambda row: (
            0 if row["school_name"] == STANFORD_SCHOOL else 1,
            -int_value(row.get("resolution_priority")),
            str(row.get("program_name") or ""),
        )
    )
    summary = build_summary(rows, generated_at, suppressed_verified_school_rows)
    write_csv(CSV_OUT, rows)
    write_json(JSON_OUT, rows)
    write_json(SUMMARY_OUT, summary)
    print(json.dumps({"school_gap_resolution_manifest_rows": len(rows), "by_school": summary["by_school"]}, sort_keys=True))


if __name__ == "__main__":
    main()
