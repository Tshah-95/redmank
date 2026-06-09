#!/usr/bin/env python3
"""Materialize per-school capability manifests for top-50 expansion."""

from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
CSV_OUT = ARTIFACTS / "school_capability_manifest.csv"
JSON_OUT = ARTIFACTS / "school_capability_manifest.json"
SUMMARY_OUT = ARTIFACTS / "school_capability_manifest_summary.json"

csv.field_size_limit(sys.maxsize)


FIELDS = [
    "capability_key",
    "school_key",
    "school_name",
    "sponsoring_institution",
    "capability_lane",
    "capability_status",
    "maturity_level",
    "maturity_level_definition",
    "evidence_count",
    "blocker_count",
    "candidate_count",
    "automation_status",
    "route_hop_policy",
    "parser_policy",
    "identity_policy",
    "freshness_policy",
    "recommended_next_action",
    "target_artifacts_json",
    "evidence_json",
    "generated_at",
]

MATURITY_LEVELS = {
    0: "not_started_or_unobserved",
    1: "raw_source_or_manual_seed_only",
    2: "workpaper_triaged_with_explicit_blockers",
    3: "repeatable_artifact_or_scripted_lane_with_known_limits",
    4: "school_verification_ready_runtime_lane",
}

TERMINAL_CLOSURE_STATUSES = {
    "closed_candidate_not_current_trainees",
    "closed_candidate_not_roster",
    "closed_related_source",
    "closed_if_no_alternate_official_url",
    "closed_no_public_current_roster_after_probe",
    "closed_source_thin_but_current_roster_covered",
    "closed_current_fellowship_page_no_named_fellows",
    "closed_candidate_route_scope_mismatch_current_resident_page_for_fellowship",
    "closed_by_gbrain_denominator_alias_context",
    "closed_by_gbrain_canonical_accepted_current_roster",
    "closed_by_gbrain_duplicate_alias_context_blocked",
    "closed_by_gbrain_special_pathway_no_public_current_roster",
}


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha_key(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def read_json(path: Path, default: object) -> object:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def school_gbrain_status(gbrain: dict, school_name: str) -> str:
    attempts = gbrain.get("attempts", []) if isinstance(gbrain, dict) else []
    effects = {row.get("approval_effect", "") for row in attempts}
    if "HOPKINS" in school_name:
        if effects & {
            "hopkins_school_verified_next_lane_approved",
            "ucsf_school_verified_next_lane_approved",
            "washu_school_verified_next_lane_approved",
        }:
            return "hopkins_school_verified_next_lane_approved"
    if "CALIFORNIA SAN FRAN" in school_name:
        if effects & {"ucsf_school_verified_next_lane_approved", "washu_school_verified_next_lane_approved"}:
            return "ucsf_school_verified_next_lane_approved"
    if "WASHINGTON UNIVERSITY" in school_name and "washu_school_verified_next_lane_approved" in effects:
        return "washu_school_verified_next_lane_approved"
    if "YALE" in school_name and "yale_school_verified_after_cardiac_surgery_delta_approved" in effects:
        return "yale_school_verified_after_cardiac_surgery_delta_approved"
    if "VANDERBILT" in school_name and "vanderbilt_primary_lane_opening_approved_school_not_verified" in effects:
        return "vanderbilt_primary_lane_opening_approved_school_not_verified"
    if "STANFORD" in school_name and "stanford_school_verified_next_lane_approved" in effects:
        return "stanford_school_verified_next_lane_approved"
    return "not_submitted"


def is_covered_status(status: str | None) -> bool:
    return bool(status and status.startswith("covered_current_roster"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sqlite_rows(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query, params)]


def target_by_name() -> dict[str, dict]:
    payload = read_json(ARTIFACTS / "top50_medical_school_targets.json", {"targets": []})
    return {row.get("school_name", ""): row for row in payload.get("targets", [])}


def row(
    *,
    school_key: str,
    school_name: str,
    sponsoring_institution: str,
    capability_lane: str,
    capability_status: str,
    maturity_level: int,
    evidence_count: int,
    blocker_count: int,
    candidate_count: int,
    automation_status: str,
    route_hop_policy: str,
    parser_policy: str,
    identity_policy: str,
    freshness_policy: str,
    recommended_next_action: str,
    target_artifacts: list[str],
    evidence: dict,
    generated_at: str,
) -> dict[str, str]:
    capability_key = "school_capability_" + sha_key(f"{school_key}|{sponsoring_institution}|{capability_lane}")
    return {
        "capability_key": capability_key,
        "school_key": school_key,
        "school_name": school_name,
        "sponsoring_institution": sponsoring_institution,
        "capability_lane": capability_lane,
        "capability_status": capability_status,
        "maturity_level": str(maturity_level),
        "maturity_level_definition": MATURITY_LEVELS.get(maturity_level, "unknown"),
        "evidence_count": str(evidence_count),
        "blocker_count": str(blocker_count),
        "candidate_count": str(candidate_count),
        "automation_status": automation_status,
        "route_hop_policy": route_hop_policy,
        "parser_policy": parser_policy,
        "identity_policy": identity_policy,
        "freshness_policy": freshness_policy,
        "recommended_next_action": recommended_next_action,
        "target_artifacts_json": dumps(target_artifacts),
        "evidence_json": dumps(evidence),
        "generated_at": generated_at,
    }


def school_program_stats(conn: sqlite3.Connection, sponsoring_institution: str) -> dict:
    coverage = sqlite_rows(
        conn,
        """
        SELECT a.*, u.program_name, u.program_type, u.department
        FROM official_program_coverage_audit a
        JOIN official_program_universe u ON u.official_program_key = a.official_program_key
        WHERE u.sponsoring_institution = ?
        """,
        (sponsoring_institution,),
    )
    queue = sqlite_rows(
        conn,
        """
        SELECT q.*
        FROM official_program_coverage_action_queue q
        JOIN official_program_universe u ON u.official_program_key = q.official_program_key
        WHERE u.sponsoring_institution = ?
        """,
        (sponsoring_institution,),
    )
    closures = sqlite_rows(
        conn,
        """
        SELECT c.*
        FROM official_program_denominator_closure_audit c
        JOIN official_program_universe u ON u.official_program_key = c.official_program_key
        WHERE u.sponsoring_institution = ?
          AND c.closure_status IN (
            'closed_no_public_current_roster_after_probe',
            'closed_source_thin_but_current_roster_covered',
            'closed_current_fellowship_page_no_named_fellows',
            'closed_candidate_route_scope_mismatch_current_resident_page_for_fellowship',
            'closed_by_gbrain_denominator_alias_context',
            'closed_by_gbrain_canonical_accepted_current_roster',
            'closed_by_gbrain_duplicate_alias_context_blocked',
            'closed_by_gbrain_special_pathway_no_public_current_roster',
            'closed_candidate_not_current_trainees',
            'closed_candidate_not_roster',
            'closed_related_source',
            'closed_if_no_alternate_official_url'
          )
        """,
        (sponsoring_institution,),
    )
    terminal_closure_keys = {
        row["official_program_key"]
        for row in closures
        if row.get("closure_status") in TERMINAL_CLOSURE_STATUSES
    }
    closed_no_roster_keys = {
        row["official_program_key"]
        for row in closures
        if row.get("closure_status") == "closed_no_public_current_roster_after_probe"
    }
    unresolved_open_gap_rows = sum(
        1
        for row in coverage
        if not is_covered_status(row.get("coverage_status"))
        and row.get("official_program_key") not in terminal_closure_keys
    )
    return {
        "coverage_rows": len(coverage),
        "coverage_status": dict(Counter(row.get("coverage_status") for row in coverage)),
        "covered_people": sum(int(row.get("captured_people_count") or 0) for row in coverage),
        "terminal_closure_rows": len(closures),
        "closed_no_public_roster_rows": len(closed_no_roster_keys),
        "closed_source_thin_covered_rows": sum(
            1 for row in closures if row.get("closure_status") == "closed_source_thin_but_current_roster_covered"
        ),
        "closed_empty_current_fellowship_rows": sum(
            1 for row in closures if row.get("closure_status") == "closed_current_fellowship_page_no_named_fellows"
        ),
        "closed_scope_mismatch_rows": sum(
            1 for row in closures if row.get("closure_status") == "closed_candidate_route_scope_mismatch_current_resident_page_for_fellowship"
        ),
        "unresolved_open_gap_rows": unresolved_open_gap_rows,
        "queue_rows": len(queue),
        "queue_lanes": dict(Counter(row.get("action_lane") for row in queue)),
        "queue_blockers": dict(Counter(row.get("blocker_status") for row in queue)),
        "candidate_urls": sum(1 for row in queue if row.get("candidate_url")),
    }


def build_hopkins_rows(conn: sqlite3.Connection, generated_at: str, target: dict) -> list[dict[str, str]]:
    school_key = target.get("school_key", "brimr_2024_school_006")
    school_name = target.get("school_name", "JOHNS HOPKINS UNIVERSITY SCH OF MEDICINE")
    sponsoring = "Johns Hopkins University School of Medicine"
    stats = school_program_stats(conn, sponsoring)
    queue_blockers = stats.get("queue_blockers", {})
    training_summary = read_json(ARTIFACTS / "hopkins_training_summary.json", {})
    probe_summary = read_json(ARTIFACTS / "hopkins_program_page_probe_summary.json", {})
    route_summary = read_json(ARTIFACTS / "hopkins_roster_route_inspection_summary.json", {})
    closure_summary = read_json(ARTIFACTS / "hopkins_candidate_closure_summary.json", {})
    gbrain = read_json(ARTIFACTS / "gbrain_consultation_ledger.json", {})
    active_route_blockers = sum(
        int(queue_blockers.get(key) or 0)
        for key in [
            "second_hop_person_structure_needs_section_review",
            "second_hop_roster_route_candidate_needs_probe",
            "program_site_candidate_needs_route_probe",
            "candidate_section_needs_parser_or_manual_review",
        ]
    )

    common_identity = (
        "Preserve raw roster observations; normalize source labels and organization forms before identity merge; "
        "merge people only with same-source/current-program anchors or explicit reviewer decisions."
    )
    rows: list[dict[str, str]] = []
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="target_registry",
        capability_status="materialized_top50_target",
        maturity_level=3,
        evidence_count=1,
        blocker_count=0,
        candidate_count=0,
        automation_status="scripted_from_brimr_workbook",
        route_hop_policy="not_applicable",
        parser_policy="not_applicable",
        identity_policy="canonical school target remains separate from sponsoring-institution aliases",
        freshness_policy="refresh when BRIMR target basis changes or user/gbrain changes top-50 definition",
        recommended_next_action="normalize BRIMR school aliases to canonical school and GME sponsoring institutions",
        target_artifacts=["artifacts/data/top50_medical_school_targets.json"],
        evidence={"target_rank": target.get("target_rank"), "target_basis": target.get("target_basis")},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="denominator_discovery",
        capability_status=(
            "repeatable_with_terminal_no_roster_closures"
            if int(stats["unresolved_open_gap_rows"]) == 0 and int(stats["closed_no_public_roster_rows"]) > 0
            else "repeatable_with_open_gaps"
        ),
        maturity_level=3,
        evidence_count=int(stats["coverage_rows"]),
        blocker_count=int(stats["unresolved_open_gap_rows"]),
        candidate_count=int(training_summary.get("browser_discovered_fellowship_programs") or 0),
        automation_status="headed_browser_finder_plus_seeded_official_hubs",
        route_hop_policy="official index, fellowship A-Z, cardiology hub, residency finder, and program pages feed one denominator table",
        parser_policy="denominator rows do not create people; coverage requires accepted current roster observations",
        identity_policy=common_identity,
        freshness_policy="refresh A-Z, GME/finder pages, and source hashes before school verification and on scheduled school refresh",
        recommended_next_action=(
            "retain terminal no-public-roster closures and refresh denominator evidence before school verification"
            if int(stats["unresolved_open_gap_rows"]) == 0
            else "keep no-roster rows explicit and close broad source-discovery rows for covered/source-thin programs"
        ),
        target_artifacts=[
            "artifacts/data/hopkins_gme_program_universe.json",
            "artifacts/data/hopkins_gme_program_coverage.json",
            "artifacts/data/hopkins_fellowship_az_browser_discovery.json",
        ],
        evidence={"coverage": stats, "training_summary": training_summary},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="official_roster_capture",
        capability_status="repeatable_for_loaded_sources",
        maturity_level=3,
        evidence_count=int(training_summary.get("roster_observations") or 0),
        blocker_count=int(stats["queue_rows"]),
        candidate_count=int(training_summary.get("sources") or 0),
        automation_status="repeatable_playwright_fetcher_for_known_roster_pages",
        route_hop_policy="use official roster URLs and browser captures; do not infer rosters from program context pages",
        parser_policy="accept current trainees only from supported official roster sections with person-card/name structure",
        identity_policy=common_identity,
        freshness_policy="retain source hashes and rerun browser fetchers before annual state mutation",
        recommended_next_action="extend parsers only where route evidence confirms a current-trainee section",
        target_artifacts=[
            "artifacts/data/hopkins_training_people.json",
            "artifacts/data/hopkins_training_sources.json",
            "artifacts/data/hopkins_browser_roster_dumps/",
        ],
        evidence={"captured_programs": training_summary.get("captured_programs", {})},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="route_inspection",
        capability_status=(
            "candidate_routes_closed_by_cumulative_closure_loop"
            if active_route_blockers == 0 and int(closure_summary.get("rows") or 0) > 0
            else "second_hop_triaged_not_closed"
        ),
        maturity_level=3 if active_route_blockers == 0 and int(closure_summary.get("rows") or 0) > 0 else 2,
        evidence_count=int(route_summary.get("rows") or 0),
        blocker_count=active_route_blockers,
        candidate_count=int(route_summary.get("candidate_route_rows") or 0),
        automation_status="scripted_first_and_second_hop_probe",
        route_hop_policy="follow roster-text pages at least one hop; second-hop person cards require section review before acceptance",
        parser_policy="person-card structure is candidate evidence, not roster truth, until scoped to current trainees",
        identity_policy=common_identity,
        freshness_policy="rerun after denominator or program-page probe changes",
        recommended_next_action=(
            "retain terminal candidate-closure dispositions and rerun the closure loop when probe evidence changes"
            if active_route_blockers == 0 and int(closure_summary.get("rows") or 0) > 0
            else (
                "resolve "
                f"{int(queue_blockers.get('second_hop_person_structure_needs_section_review') or 0)} "
                "second-hop person-structure reviews, "
                f"{int(queue_blockers.get('second_hop_roster_route_candidate_needs_probe') or 0)} "
                "second-hop roster-route probes, "
                f"{int(queue_blockers.get('program_site_candidate_needs_route_probe') or 0)} "
                "program-site route probes, and "
                f"{int(queue_blockers.get('candidate_section_needs_parser_or_manual_review') or 0)} "
                "candidate-section parser/manual reviews"
            )
        ),
        target_artifacts=[
            "artifacts/data/hopkins_program_page_probe.csv",
            "artifacts/data/hopkins_roster_route_inspection.csv",
            "artifacts/data/hup_gap_reason_audit.csv",
        ],
        evidence={"probe_summary": probe_summary, "route_summary": route_summary, "closure_summary": closure_summary},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="coverage_gap_resolution",
        capability_status=(
            "action_queue_closed_by_terminal_closure_facts"
            if int(stats["queue_rows"]) == 0 and int(stats["unresolved_open_gap_rows"]) == 0
            else "action_queue_not_drained"
        ),
        maturity_level=3 if int(stats["queue_rows"]) == 0 and int(stats["unresolved_open_gap_rows"]) == 0 else 2,
        evidence_count=int(stats["terminal_closure_rows"]) if int(stats["queue_rows"]) == 0 else int(stats["queue_rows"]),
        blocker_count=int(stats["queue_rows"]),
        candidate_count=int(stats["candidate_urls"]),
        automation_status="bounded_action_batches_and_packets",
        route_hop_policy="candidate and route lanes must be closed or superseded before no-roster closure",
        parser_policy="parser changes must write candidate outputs back through acceptance/reviewer ledgers",
        identity_policy=common_identity,
        freshness_policy="gap status expires when source hash, route candidate, or denominator row changes",
        recommended_next_action=(
            "submit closure-backed school readiness dossier through GBrain HTTP MCP for explicit verification"
            if int(stats["queue_rows"]) == 0 and int(stats["unresolved_open_gap_rows"]) == 0
            else "drain or explicitly close the Hopkins coverage action queue before GBrain school verification"
        ),
        target_artifacts=[
            "artifacts/data/official_program_coverage_action_queue.csv",
            "artifacts/data/official_program_denominator_closure_audit.csv",
            "artifacts/data/official_program_coverage_batches.csv",
            "artifacts/data/official_program_coverage_batch_packets.csv",
        ],
        evidence={"coverage": stats},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="identity_normalization",
        capability_status="documented_nonblocking_stage_conflict",
        maturity_level=3,
        evidence_count=int(training_summary.get("unique_people") or 0),
        blocker_count=0,
        candidate_count=int(training_summary.get("duplicate_observations_collapsed") or 0),
        automation_status="scripted_same-person_collapse_with_conflict_artifact",
        route_hop_policy="not_applicable",
        parser_policy="preserve multiple program memberships separately from person identity",
        identity_policy=common_identity,
        freshness_policy="recompute identity conflicts on every roster refresh before state mutation",
        recommended_next_action="carry Henry Pronovost stage conflict as lifecycle-mutation review evidence, not as a roster-identity blocker",
        target_artifacts=[
            "artifacts/data/hopkins_identity_conflicts.csv",
            "artifacts/data/hopkins_training_people.json",
        ],
        evidence={"training_summary": training_summary},
        generated_at=generated_at,
    ))
    approval_status = school_gbrain_status(gbrain, school_name)
    hopkins_verified = approval_status in {
        "hopkins_school_verified_next_lane_approved",
        "ucsf_school_verified_next_lane_approved",
        "washu_school_verified_next_lane_approved",
        "yale_school_verified_next_lane_approved",
        "vanderbilt_primary_lane_opening_approved_school_not_verified",
    }
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="gbrain_verification",
        capability_status=(
            "hopkins_school_verified_next_lane_approved"
            if hopkins_verified
            else approval_status
        ),
        maturity_level=4 if hopkins_verified else 2,
        evidence_count=len(gbrain.get("attempts", [])),
        blocker_count=0 if hopkins_verified else 1,
        candidate_count=0,
        automation_status="http_mcp_query_and_think_available",
        route_hop_policy="school verification requires route/action gaps closed or explicitly justified",
        parser_policy="school dossier must separate accepted roster truth from candidate person structures",
        identity_policy=common_identity,
        freshness_policy="submit a fresh school readiness dossier after queue state changes",
        recommended_next_action=(
            "move to the next top-50 primary school lane while preserving Hopkins refresh evidence"
            if hopkins_verified
            else "resubmit Hopkins readiness dossier through HTTP MCP after known blockers are closed"
        ),
        target_artifacts=[
            "artifacts/data/gbrain_consultation_ledger.json",
            "artifacts/research/hopkins-expansion-status-2026-06-05.md",
        ],
        evidence={"approval_status": approval_status, "latest_advisory_summary": gbrain.get("latest_advisory_summary", {})},
        generated_at=generated_at,
    ))
    return rows


def build_penn_rows(conn: sqlite3.Connection, generated_at: str, target: dict) -> list[dict[str, str]]:
    school_key = target.get("school_key", "brimr_2024_school_004")
    school_name = target.get("school_name", "UNIV OF PENNSYLVANIA SCH OF MEDICINE")
    sponsoring = "Hospital of the University of Pennsylvania"
    stats = school_program_stats(conn, sponsoring)
    return [
        row(
            school_key=school_key,
            school_name=school_name,
            sponsoring_institution=sponsoring,
            capability_lane="reference_corpus",
            capability_status="calibration_reference_with_known_gap_lanes",
            maturity_level=3,
            evidence_count=int(stats["coverage_rows"]),
            blocker_count=int(stats["queue_rows"]),
            candidate_count=int(stats["candidate_urls"]),
            automation_status="multi_source_scrapers_and_acceptance_ledgers",
            route_hop_policy="use Penn/HUP gap probes and source-candidate search as calibration for other schools",
            parser_policy="accepted rosters come from supported official sections; profile/enrichment claims stay downstream",
            identity_policy="Krishna/Penn State lesson: normalize education/institution labels separately from person identity and preserve explicit reviewer gaps",
            freshness_policy="annual roster refresh before state mutation; source-hash and temporal-contract ledgers govern retention",
            recommended_next_action="keep Penn as quality baseline while Hopkins/UCSF capability manifests mature",
            target_artifacts=[
                "artifacts/data/penn_gme_program_coverage.csv",
                "artifacts/data/hup_gap_reason_audit.csv",
                "artifacts/data/corpus_quality_lane_review.csv",
            ],
            evidence={"coverage": stats},
            generated_at=generated_at,
        )
    ]


def build_ucsf_rows(conn: sqlite3.Connection, generated_at: str, target: dict) -> list[dict[str, str]]:
    school_key = target.get("school_key", "brimr_2024_school_001")
    school_name = target.get("school_name", "UNIV OF CALIFORNIA SAN FRAN SCH OF MED")
    sponsoring = "University of California, San Francisco School of Medicine"
    stats = school_program_stats(conn, sponsoring)
    training_summary = read_json(ARTIFACTS / "ucsf_training_summary.json", {})
    probe_summary = read_json(ARTIFACTS / "ucsf_program_page_probe_summary.json", {})
    route_summary = read_json(ARTIFACTS / "ucsf_roster_route_inspection_summary.json", {})
    parser_summary = read_json(ARTIFACTS / "ucsf_parser_ready_roster_summary.json", {})
    gbrain = read_json(ARTIFACTS / "gbrain_consultation_ledger.json", {})
    source_gaps = read_csv(ARTIFACTS / "ucsf_source_gap_ledger.csv")
    common_identity = (
        "Do not create or merge trainee identities from directory/program pages; create people only from "
        "verified current-resident/current-fellow roster sections with source-scoped evidence."
    )
    denominator_rows = int(training_summary.get("program_denominator_rows") or stats["coverage_rows"])
    roster_observations = int(training_summary.get("roster_observations") or parser_summary.get("people") or 0)
    roster_gap_count = int(stats["unresolved_open_gap_rows"])
    source_rows = int(training_summary.get("sources") or 0)
    rows: list[dict[str, str]] = []
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="target_registry",
        capability_status="materialized_top50_target",
        maturity_level=3,
        evidence_count=1,
        blocker_count=0,
        candidate_count=0,
        automation_status="scripted_from_brimr_workbook",
        route_hop_policy="not_applicable",
        parser_policy="not_applicable",
        identity_policy="canonical BRIMR target remains separate from UCSF GME sponsoring-institution label",
        freshness_policy="refresh when BRIMR target basis changes or user/gbrain changes top-50 definition",
        recommended_next_action="keep UCSF as the rank-1 primary expansion lane until school dossier is verified",
        target_artifacts=["artifacts/data/top50_medical_school_targets.json"],
        evidence={"target_rank": target.get("target_rank"), "target_basis": target.get("target_basis")},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="denominator_discovery",
        capability_status="official_directory_seeded_not_roster_complete",
        maturity_level=3 if denominator_rows else 1,
        evidence_count=denominator_rows,
        blocker_count=0 if denominator_rows else 1,
        candidate_count=int(training_summary.get("departments") or 0),
        automation_status="repeatable_plain_http_official_directory_parser",
        route_hop_policy="UCSF Current Residents & Fellows hub routes to department-scoped Training Programs links",
        parser_policy="dom-collapsible department blocks are denominator seeds only; nested subspecialty expansion remains downstream",
        identity_policy=common_identity,
        freshness_policy="refresh official UCSF current-residents hub and training-programs page before route discovery batches",
        recommended_next_action="probe each official program URL for current resident/fellow roster routes and nested subspecialty links",
        target_artifacts=[
            "artifacts/data/ucsf_training_sources.json",
            "artifacts/data/ucsf_gme_program_universe.json",
            "artifacts/data/ucsf_training_summary.json",
        ],
        evidence={"training_summary": training_summary, "source_gap_rows": len(source_gaps)},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="official_roster_capture",
        capability_status="partial_current_roster_capture_parser_gated" if roster_observations else "not_started_denominator_only",
        maturity_level=3 if roster_observations else 1,
        evidence_count=roster_observations,
        blocker_count=roster_gap_count,
        candidate_count=denominator_rows,
        automation_status="repeatable_parser_ready_roster_fetcher_partial" if roster_observations else "no_current_roster_parser_loaded_for_ucsf_yet",
        route_hop_policy="only accept pages scoped to current named residents or fellows; program overview pages stay context evidence",
        parser_policy="write scoped parsers per UCSF department/site family after route inspection confirms current-trainee sections",
        identity_policy=common_identity,
        freshness_policy="source hashes and route-discovery evidence must be refreshed before any UCSF people are accepted",
        recommended_next_action=(
            "continue parser/route/URL/source-discovery closure for remaining open UCSF denominator rows"
            if roster_observations
            else "run route discovery on the 51 official program URLs and capture parser-ready current roster pages"
        ),
        target_artifacts=[
            "artifacts/data/ucsf_training_people.json",
            "artifacts/data/ucsf_gme_program_coverage.json",
            "artifacts/data/ucsf_source_gap_ledger.csv",
            "artifacts/data/ucsf_parser_ready_rosters.csv",
            "artifacts/data/ucsf_parser_ready_roster_summary.json",
        ],
        evidence={"coverage": stats, "training_summary": training_summary, "parser_summary": parser_summary},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="route_inspection",
        capability_status="candidate_route_inspection_completed_parser_candidates_open"
        if route_summary
        else "program_page_probe_completed_candidate_routes_open",
        maturity_level=4 if route_summary else (3 if int(probe_summary.get("probe_rows") or 0) == denominator_rows else 2),
        evidence_count=int(route_summary.get("rows") or probe_summary.get("probe_rows") or 0),
        blocker_count=int(stats["queue_rows"]),
        candidate_count=int(parser_summary.get("sources") or route_summary.get("parser_review_candidate_rows") or probe_summary.get("candidate_roster_links") or 0),
        automation_status="repeatable_requests_probe_plus_playwright_candidate_route_inspection",
        route_hop_policy="first-hop official program URLs and candidate roster links are classified before parser acceptance or no-roster closure",
        parser_policy="route-inspection parser candidates remain scoped review inputs until current named trainees are extracted into accepted evidence",
        identity_policy=common_identity,
        freshness_policy="rerun probe and route inspection when UCSF denominator URL, source hash, or candidate route evidence changes",
        recommended_next_action="integrate scoped parsers for parser-review candidates, continue second-hop route probes, and repair blocked/error URLs",
        target_artifacts=[
            "artifacts/data/ucsf_program_page_probe.csv",
            "artifacts/data/ucsf_program_page_probe_summary.json",
            "artifacts/data/ucsf_roster_route_inspection.csv",
            "artifacts/data/ucsf_roster_route_inspection_summary.json",
            "artifacts/data/hup_gap_reason_audit.csv",
        ],
        evidence={"probe_summary": probe_summary, "route_summary": route_summary, "parser_summary": parser_summary, "coverage": stats},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="coverage_gap_resolution",
        capability_status="action_queue_open_denominator_seeded",
        maturity_level=2,
        evidence_count=int(stats["queue_rows"]),
        blocker_count=int(stats["queue_rows"]),
        candidate_count=denominator_rows,
        automation_status="warehouse_action_queue_materialized_from_official_denominator",
        route_hop_policy="do not close no-roster rows until first-hop and reasonable second-hop official route discovery are documented",
        parser_policy="candidate roster pages must feed acceptance/reviewer ledgers before coverage can move to covered_current_roster",
        identity_policy=common_identity,
        freshness_policy="gap status expires when the UCSF training-programs page hash or program URL changes",
        recommended_next_action="drain UCSF action queue through route probes, parser additions, or explicit no-public-roster closure facts",
        target_artifacts=[
            "artifacts/data/official_program_coverage_action_queue.csv",
            "artifacts/data/official_program_coverage_assurance_audit.csv",
            "artifacts/data/official_program_coverage_dossiers.csv",
        ],
        evidence={"coverage": stats},
        generated_at=generated_at,
    ))
    ucsf_people = int(training_summary.get("people") or 0)
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="identity_normalization",
        capability_status="source_scoped_identity_normalization_active" if ucsf_people else "gated_no_ucsf_people_loaded",
        maturity_level=3 if ucsf_people else 2,
        evidence_count=ucsf_people,
        blocker_count=0,
        candidate_count=ucsf_people,
        automation_status=(
            "source_scoped_identity_rows_loaded_from_parser_ready_rosters"
            if ucsf_people
            else "identity_gate_present_but_no_ucsf_person_rows"
        ),
        route_hop_policy="not_applicable",
        parser_policy=(
            "identity rows are accepted only from strict current resident/fellow roster parser outputs"
            if ucsf_people
            else "not_applicable_until_current_roster_rows_exist"
        ),
        identity_policy=common_identity,
        freshness_policy="recompute source-scoped identity conflicts on every UCSF roster refresh",
        recommended_next_action=(
            "recompute identity conflicts as UCSF parser coverage expands; do not merge across programs without source-scoped anchors"
            if ucsf_people
            else "keep identity lane closed to denominator-only evidence; open after first accepted UCSF roster observations"
        ),
        target_artifacts=["artifacts/data/ucsf_training_people.json"],
        evidence={"training_summary": training_summary},
        generated_at=generated_at,
    ))
    approval_status = school_gbrain_status(gbrain, school_name)
    ucsf_verified = approval_status in {
        "ucsf_school_verified_next_lane_approved",
        "washu_school_verified_next_lane_approved",
        "yale_school_verified_next_lane_approved",
        "vanderbilt_primary_lane_opening_approved_school_not_verified",
    }
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="gbrain_verification",
        capability_status=(
            "ucsf_school_verified_next_lane_approved"
            if ucsf_verified
            else "not_submitted"
        ),
        maturity_level=4 if ucsf_verified else 1,
        evidence_count=len(gbrain.get("attempts", [])) if ucsf_verified else 0,
        blocker_count=0 if ucsf_verified else 1,
        candidate_count=0,
        automation_status="http_mcp_query_and_think_available",
        route_hop_policy="school verification requires roster-route/action gaps closed or explicitly justified",
        parser_policy="school dossier must separate denominator seeds from accepted roster truth",
        identity_policy=common_identity,
        freshness_policy="submit a fresh UCSF readiness dossier after queue/source hash changes",
        recommended_next_action=(
            "keep UCSF on scheduled refresh and closure revalidation; move to the next top-50 primary school lane"
            if ucsf_verified
            else "do not request UCSF school verification until roster capture or terminal closure evidence exists"
        ),
        target_artifacts=[
            "artifacts/data/school_readiness_dossiers.csv",
            "artifacts/data/ucsf_training_summary.json",
        ],
        evidence={"approval_status": approval_status, "latest_advisory_summary": gbrain.get("latest_advisory_summary", {}) if ucsf_verified else {}},
        generated_at=generated_at,
    ))
    return rows


def build_washu_rows(conn: sqlite3.Connection, generated_at: str, target: dict) -> list[dict[str, str]]:
    school_key = target.get("school_key", "brimr_2024_school_002")
    school_name = target.get("school_name", "WASHINGTON UNIVERSITY SCH OF MEDICINE")
    sponsoring = "WashU/BJH/SLCH/MBMC Graduate Medical Education Consortium"
    stats = school_program_stats(conn, sponsoring)
    training_summary = read_json(ARTIFACTS / "washu_training_summary.json", {})
    acgme_summary = read_json(ARTIFACTS / "washu_acgme_denominator_summary.json", {})
    probe_summary = read_json(ARTIFACTS / "washu_program_page_probe_summary.json", {})
    route_summary = read_json(ARTIFACTS / "washu_roster_route_inspection_summary.json", {})
    broad_route_summary = read_json(ARTIFACTS / "washu_broad_roster_route_inspection_summary.json", {})
    parser_summary = read_json(ARTIFACTS / "washu_parser_ready_roster_summary.json", {})
    acceptance_gate_summary = read_json(ARTIFACTS / "washu_parser_ready_acceptance_gate_summary.json", {})
    approved_manifest_summary = read_json(ARTIFACTS / "washu_approved_parser_ready_gate_manifest_summary.json", {})
    approved_manifest_drift_summary = read_json(ARTIFACTS / "washu_approved_parser_ready_gate_manifest_drift_summary.json", {})
    fellowship_scope_summary = read_json(ARTIFACTS / "washu_fellowship_scope_review_summary.json", {})
    fellowship_parser_summary = read_json(ARTIFACTS / "washu_ophthalmology_fellowship_parser_ready_roster_summary.json", {})
    broad_source_summary = read_json(ARTIFACTS / "washu_source_probe_summary.json", {})
    source_gaps = read_csv(ARTIFACTS / "washu_source_gap_ledger.csv")
    gbrain = read_json(ARTIFACTS / "gbrain_consultation_ledger.json", {})
    common_identity = (
        "Do not create or merge trainee identities from program/contact PDFs or department hubs; create people "
        "only from verified current-resident/current-fellow roster sections with source-scoped evidence."
    )
    denominator_rows = int(training_summary.get("program_denominator_rows") or stats["coverage_rows"])
    seed_denominator_rows = int(training_summary.get("seed_program_denominator_rows_2022") or 0)
    reconciled_denominator_rows = int(training_summary.get("reconciled_program_denominator_rows") or denominator_rows)
    department_hubs = int(training_summary.get("department_hubs") or 0)
    current_acgme_rows = int(acgme_summary.get("current_acgme_ads_washu_rows") or 0)
    current_acgme_matches = int(acgme_summary.get("current_acgme_ads_matches") or 0)
    current_acgme_drift = int(acgme_summary.get("current_acgme_ads_rows_not_in_2022_seed") or 0)
    candidate_repairs = int(acgme_summary.get("seed_code_stale_or_malformed_candidate_repairs") or 0)
    denominator_mutated = acgme_summary.get("denominator_mutation_status") == "reconciled_denominator_materialized_open_rows_only"
    acceptance_gate_rows = int(acceptance_gate_summary.get("rows") or 0)
    acceptance_gate_status = acceptance_gate_summary.get("overall_status") or ""
    accepted_people = int(training_summary.get("people") or 0)
    accepted_fellow_rows = int(training_summary.get("accepted_ophthalmology_fellowship_gate_rows") or 0)
    route_parser_candidates = int(route_summary.get("parser_review_candidate_rows") or 0) + int(
        broad_route_summary.get("parser_review_candidate_rows") or 0
    )
    route_scope_mismatches = int(route_summary.get("scope_mismatch_rows") or 0) + int(
        broad_route_summary.get("scope_mismatch_rows") or 0
    )
    route_rows = int(route_summary.get("rows") or 0) + int(broad_route_summary.get("rows") or 0)
    rows: list[dict[str, str]] = []
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="target_registry",
        capability_status="materialized_top50_target",
        maturity_level=3,
        evidence_count=1,
        blocker_count=0,
        candidate_count=0,
        automation_status="scripted_from_brimr_workbook",
        route_hop_policy="not_applicable",
        parser_policy="not_applicable",
        identity_policy="canonical BRIMR target remains separate from WashU GME consortium label",
        freshness_policy="refresh when BRIMR target basis changes or user/gbrain changes top-50 definition",
        recommended_next_action="continue WashU as the next GBrain-approved primary school lane after UCSF",
        target_artifacts=["artifacts/data/top50_medical_school_targets.json"],
        evidence={"target_rank": target.get("target_rank"), "target_basis": target.get("target_basis")},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="denominator_discovery",
        capability_status=(
            "reconciled_denominator_materialized_with_current_acgme_drift"
            if denominator_mutated
            else "official_pdf_seeded_current_acgme_subset_reconciled_with_drift"
        ),
        maturity_level=3 if denominator_rows else 1,
        evidence_count=reconciled_denominator_rows + current_acgme_rows,
        blocker_count=0 if denominator_mutated else 1 + current_acgme_drift,
        candidate_count=department_hubs + current_acgme_drift,
        automation_status="repeatable_plain_http_pdf_html_parser_plus_acgme_ads_state_search_reconciliation",
        route_hop_policy=(
            "official GME Explore Our Programs hub gives core department entry points; comprehensive contact PDF gives seed "
            "program rows; current ACGME ADS rows are materialized as open denominator rows before route probing"
        ),
        parser_policy="pdftotext fixed-column parser captures program/type/length/ACGME evidence; ADS state-search parser reconciles current ACGME codes and ADS-only rows; neither creates people",
        identity_policy=common_identity,
        freshness_policy="refresh ADS search plus WashU official sources before school verification; candidate code repairs need current WashU confirmation before overwriting raw seed evidence",
        recommended_next_action=(
            "carry reconciled denominator evidence into the school-level GBrain readiness packet; preserve 2022 seed caveats and current ADS drift notes"
            if denominator_mutated and stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0 and accepted_people
            else
            "begin WashU official route probing against the reconciled denominator; keep candidate code repairs and 86 non-ACGME/missing-ID rows explicit in the dossier"
            if denominator_mutated
            else "resolve stale/malformed 2022 ACGME codes, add/triage current ADS-only WashU rows, and find current WashU evidence for non-ACGME/missing-ID rows"
        ),
        target_artifacts=[
            "artifacts/data/washu_training_sources.json",
            "artifacts/data/washu_gme_department_hubs.json",
            "artifacts/data/washu_gme_program_universe_seed_2022.json",
            "artifacts/data/washu_gme_program_universe_reconciled.json",
            "artifacts/data/washu_gme_program_universe.json",
            "artifacts/data/washu_acgme_current_programs.json",
            "artifacts/data/washu_acgme_denominator_reconciliation.json",
            "artifacts/data/washu_current_denominator_search.csv",
            "artifacts/data/washu_acgme_denominator_summary.json",
            "artifacts/data/washu_training_summary.json",
        ],
        evidence={
            "training_summary": training_summary,
            "acgme_summary": acgme_summary,
            "source_gap_rows": len(source_gaps),
            "seed_denominator_rows": seed_denominator_rows,
            "reconciled_denominator_rows": reconciled_denominator_rows,
            "current_acgme_matches": current_acgme_matches,
            "candidate_seed_code_repairs": candidate_repairs,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="official_roster_capture",
        capability_status=(
            "accepted_exact_gbrain_approved_current_roster_people"
            if accepted_people and stats["unresolved_open_gap_rows"] == 0 and stats["queue_rows"] == 0
            else "parser_ready_acceptance_gate_evidence_ready_gbrain_nonapproved"
            if acceptance_gate_status == "evidence_ready_blocked_pending_gbrain_incremental_acceptance_policy"
            else "parser_ready_acceptance_gate_ready_for_incremental_person_acceptance"
            if acceptance_gate_status == "ready_for_incremental_person_acceptance"
            else "parser_ready_acceptance_gate_blocked_evidence_gap"
            if acceptance_gate_status == "blocked_evidence_gap"
            else
            "parser_ready_roster_artifact_materialized_no_people_loaded"
            if int(parser_summary.get("people") or 0)
            else "parser_review_candidates_identified_no_people_loaded"
            if route_parser_candidates
            else "not_started_denominator_only"
        ),
        maturity_level=3 if accepted_people or int(parser_summary.get("people") or 0) else 2 if route_parser_candidates else 1,
        evidence_count=int(accepted_people or acceptance_gate_rows or parser_summary.get("people") or route_parser_candidates or 0),
        blocker_count=(
            0
            if accepted_people and stats["unresolved_open_gap_rows"] == 0 and stats["queue_rows"] == 0
            else 1
            if acceptance_gate_status == "evidence_ready_blocked_pending_gbrain_incremental_acceptance_policy"
            else int(stats["unresolved_open_gap_rows"] or stats["queue_rows"])
        ),
        candidate_count=denominator_rows,
        automation_status=(
            "accepted_people_loaded_from_exact_gbrain_approved_resident_and_fellowship_gates"
            if accepted_people
            else "acceptance_gate_materialized_evidence_ready_but_gbrain_nonapproved"
            if acceptance_gate_status == "evidence_ready_blocked_pending_gbrain_incremental_acceptance_policy"
            else "acceptance_gate_materialized_ready_to_load_exact_rows"
            if acceptance_gate_status == "ready_for_incremental_person_acceptance"
            else "acceptance_gate_materialized_with_evidence_gaps"
            if acceptance_gate_status == "blocked_evidence_gap"
            else
            "non_mutating_parser_ready_roster_fetcher_materialized_but_no_washu_people_loaded"
            if parser_summary
            else "route_inspection_identified_scoped_parser_review_candidates_but_no_washu_people_loaded"
            if route_summary
            else "no_current_roster_parser_loaded_for_washu_yet"
        ),
        route_hop_policy="only accept pages scoped to current named residents or fellows; program overview pages stay context evidence",
        parser_policy="write scoped parsers after official department/program route inspection confirms current-trainee sections",
        identity_policy=common_identity,
        freshness_policy="source hashes and route-discovery evidence must be refreshed before WashU people are accepted",
        recommended_next_action=(
            "submit school-level readiness dossier; accepted people are exact gate rows only and school verification remains separate"
            if accepted_people and stats["unresolved_open_gap_rows"] == 0 and stats["queue_rows"] == 0
            else "do not load WashU parser-ready people; GBrain explicitly did not approve incremental acceptance until a standing policy or approval_effect exists"
            if acceptance_gate_status == "evidence_ready_blocked_pending_gbrain_incremental_acceptance_policy"
            else "load exact acceptance-gate rows only, keep generic Resident stage caveat, and keep remaining WashU denominator rows open"
            if acceptance_gate_status == "ready_for_incremental_person_acceptance"
            else "fix WashU acceptance-gate evidence gaps before any GBrain acceptance resubmission"
            if acceptance_gate_status == "blocked_evidence_gap"
            else
            "review parser-ready WashU observations for acceptance; do not load people until acceptance/reviewer gate promotes target-scoped current roster evidence"
            if int(parser_summary.get("people") or 0)
            else "build scoped WashU parsers only for route-inspection candidates with current target-program named-trainee structure"
            if route_parser_candidates
            else "probe official department hubs and reconciled program rows for current resident/fellow roster routes"
            if denominator_mutated
            else "finish current denominator mutation before broad route probing"
        ),
        target_artifacts=[
            "artifacts/data/washu_training_people.json",
            "artifacts/data/washu_gme_program_coverage.json",
            "artifacts/data/washu_source_gap_ledger.csv",
            "artifacts/data/washu_roster_route_inspection.csv",
            "artifacts/data/washu_roster_route_inspection_summary.json",
            "artifacts/data/washu_broad_roster_route_inspection.csv",
            "artifacts/data/washu_broad_roster_route_inspection_summary.json",
            "artifacts/data/washu_parser_ready_rosters.csv",
            "artifacts/data/washu_parser_ready_roster_summary.json",
            "artifacts/data/washu_parser_ready_acceptance_gate.csv",
            "artifacts/data/washu_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_drift_summary.json",
            "artifacts/data/washu_live_gate_drift_analysis.csv",
            "artifacts/data/washu_ophthalmology_fellowship_parser_ready_rosters.csv",
            "artifacts/data/washu_ophthalmology_fellowship_parser_ready_roster_summary.json",
            "artifacts/data/washu_fellowship_scope_review.csv",
            "artifacts/data/washu_fellowship_scope_review_summary.json",
            "artifacts/data/washu_school_verification_reconciliation.csv",
            "artifacts/data/washu_school_verification_reconciliation_summary.json",
        ],
        evidence={
            "coverage": stats,
            "training_summary": training_summary,
            "route_summary": route_summary,
            "broad_route_summary": broad_route_summary,
            "parser_summary": parser_summary,
            "acceptance_gate_summary": acceptance_gate_summary,
            "approved_manifest_summary": approved_manifest_summary,
            "approved_manifest_drift_summary": approved_manifest_drift_summary,
            "fellowship_parser_summary": fellowship_parser_summary,
            "fellowship_scope_summary": fellowship_scope_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="route_inspection",
        capability_status=(
            "candidate_routes_and_broad_routes_inspected_parser_candidates_and_scope_mismatches_recorded"
            if route_summary and broad_route_summary
            else
            "candidate_routes_inspected_parser_candidates_and_scope_mismatches_recorded"
            if route_summary
            else "program_page_probe_completed_candidate_routes_open"
            if probe_summary
            else "not_started_department_hubs_seeded"
        ),
        maturity_level=3 if probe_summary or route_summary else 1,
        evidence_count=int(route_rows or probe_summary.get("probe_rows") or department_hubs),
        blocker_count=int(stats["unresolved_open_gap_rows"]),
        candidate_count=int(probe_summary.get("source_candidate_rows") or department_hubs),
        automation_status=(
            "repeatable_playwright_inspection_over_washu_roster_link_and_broad_source_candidates"
            if route_summary and broad_route_summary
            else
            "repeatable_playwright_inspection_over_washu_roster_link_candidates"
            if route_summary
            else "repeatable_requests_probe_over_reconciled_denominator_and_department_hubs"
            if probe_summary
            else "department_hub_candidates_materialized_no_route_probe_yet"
        ),
        route_hop_policy="first hop from official GME department hubs, second hop to department education/residency/fellowship pages, then roster candidates",
        parser_policy="route candidates remain review inputs until current named trainees are extracted into accepted evidence",
        identity_policy=common_identity,
        freshness_policy="rerun route inspection when WashU Explore Our Programs hash or department links change",
        recommended_next_action=(
            "carry route-inspection and scope-mismatch evidence into the school-level GBrain readiness packet; rerun only when source hashes or denominator rows change"
            if stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0 and accepted_people
            else
            "convert current target-program parser candidates, including broad-source Ophthalmology, into scoped non-mutating roster extracts; keep related/faculty-only pages out of person truth"
            if route_summary and broad_route_summary
            else
            "convert current target-program parser candidates into scoped non-mutating roster extracts; keep related-scope mismatches out of person truth"
            if route_summary
            else "inspect WashU roster-link candidates, reject related-scope residency/fellowship mismatches, and add scoped parsers only for current named trainee pages"
            if probe_summary
            else "generalize the UCSF/Hopkins route-probe pattern for WashU department hubs"
        ),
        target_artifacts=[
            "artifacts/data/washu_gme_department_hubs.json",
            "artifacts/data/washu_program_page_probe.csv",
            "artifacts/data/washu_program_page_probe_summary.json",
            "artifacts/data/washu_source_candidates.csv",
            "artifacts/data/washu_roster_route_inspection.csv",
            "artifacts/data/washu_roster_route_inspection_summary.json",
            "artifacts/data/washu_broad_roster_route_inspection.csv",
            "artifacts/data/washu_broad_roster_route_inspection_summary.json",
            "artifacts/data/washu_parser_ready_rosters.csv",
            "artifacts/data/washu_parser_ready_roster_summary.json",
            "artifacts/data/washu_parser_ready_acceptance_gate.csv",
            "artifacts/data/washu_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_drift_summary.json",
            "artifacts/data/washu_live_gate_drift_analysis.csv",
            "artifacts/data/washu_source_gap_ledger.csv",
        ],
        evidence={
            "training_summary": training_summary,
            "coverage": stats,
            "probe_summary": probe_summary,
            "route_summary": route_summary,
            "broad_route_summary": broad_route_summary,
            "parser_summary": parser_summary,
            "acceptance_gate_summary": acceptance_gate_summary,
            "approved_manifest_summary": approved_manifest_summary,
            "approved_manifest_drift_summary": approved_manifest_drift_summary,
            "broad_source_summary": broad_source_summary,
            "fellowship_scope_summary": fellowship_scope_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="coverage_gap_resolution",
        capability_status=(
            "all_open_gaps_closed_or_covered_ready_for_school_verification_packet"
            if stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0
            else "broad_source_route_inspection_completed_parser_candidate_and_closures_open"
            if broad_route_summary
            else "broad_source_discovery_materialized_candidates_open"
            if broad_source_summary
            else "action_queue_open_denominator_seeded"
        ),
        maturity_level=3 if stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0 else 2,
        evidence_count=int(stats["coverage_rows"]),
        blocker_count=int(stats["queue_rows"] or stats["unresolved_open_gap_rows"]),
        candidate_count=int(broad_source_summary.get("candidate_urls") or denominator_rows),
        automation_status=(
            "warehouse_action_queue_plus_washu_broad_source_discovery_materialized"
            if broad_source_summary
            else "warehouse_action_queue_materialized_from_official_denominator"
        ),
        route_hop_policy="do not close no-roster rows until first-hop and reasonable second-hop official route discovery are documented",
        parser_policy="candidate roster pages must feed acceptance/reviewer ledgers before coverage can move to covered_current_roster",
        identity_policy=common_identity,
        freshness_policy="gap status expires when the WashU denominator source hash or department URL changes",
        recommended_next_action=(
            "submit the WashU school-level dossier through GBrain with terminal closure evidence and accepted exact person gates"
            if stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0
            else "route the broad-source Ophthalmology current-resident page through scoped parser/reviewer gating; use faculty/leadership and related-scope broad rows as closure evidence without loading people"
            if broad_route_summary
            else
            "inspect the 52 WashU broad-source roster-candidate rows with headed route inspection before parser or no-roster closure"
            if broad_source_summary
            else "drain WashU action queue through route probes, parser additions, or explicit no-public-roster closure facts"
        ),
        target_artifacts=[
            "artifacts/data/official_program_coverage_action_queue.csv",
            "artifacts/data/official_program_coverage_assurance_audit.csv",
            "artifacts/data/official_program_coverage_dossiers.csv",
            "artifacts/data/washu_source_probes.json",
            "artifacts/data/washu_broad_source_candidates.csv",
            "artifacts/data/washu_broad_roster_route_inspection.csv",
            "artifacts/data/washu_broad_roster_route_inspection_summary.json",
            "artifacts/data/washu_source_search_queries.csv",
            "artifacts/data/washu_source_probe_summary.json",
            "artifacts/data/washu_fellowship_scope_review.csv",
            "artifacts/data/washu_fellowship_scope_review_summary.json",
            "artifacts/data/washu_school_verification_reconciliation_summary.json",
        ],
        evidence={
            "coverage": stats,
            "broad_source_summary": broad_source_summary,
            "broad_route_summary": broad_route_summary,
            "fellowship_scope_summary": fellowship_scope_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="identity_normalization",
        capability_status="source_scoped_identity_rows_loaded_from_approved_washu_roster_gates"
        if accepted_people
        else "gated_no_washu_people_loaded",
        maturity_level=3 if accepted_people else 2,
        evidence_count=accepted_people,
        blocker_count=0,
        candidate_count=0,
        automation_status=(
            "source_scoped_identity_rows_loaded_from_accepted_washu_training_people"
            if accepted_people
            else "identity_gate_present_but_no_washu_person_rows"
        ),
        route_hop_policy="not_applicable",
        parser_policy=(
            "identity rows are accepted only from exact GBrain-approved resident and fellowship gate outputs"
            if accepted_people
            else "not_applicable_until_current_roster_rows_exist"
        ),
        identity_policy=common_identity,
        freshness_policy="recompute source-scoped identity conflicts on every WashU roster refresh",
        recommended_next_action=(
            "recompute identity conflicts as WashU parser coverage expands; do not merge across programs without source-scoped anchors"
            if accepted_people
            else "keep identity lane closed to denominator-only evidence; open after first accepted WashU roster observations"
        ),
        target_artifacts=[
            "artifacts/data/washu_training_people.json",
            "artifacts/data/washu_parser_ready_acceptance_gate.csv",
            "artifacts/data/washu_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_drift_summary.json",
        ],
        evidence={
            "training_summary": training_summary,
            "acceptance_gate_summary": acceptance_gate_summary,
            "approved_manifest_summary": approved_manifest_summary,
            "approved_manifest_drift_summary": approved_manifest_drift_summary,
        },
        generated_at=generated_at,
    ))
    approval_status = school_gbrain_status(gbrain, school_name)
    washu_verified = approval_status in {
        "washu_school_verified_next_lane_approved",
        "yale_school_verified_next_lane_approved",
        "vanderbilt_primary_lane_opening_approved_school_not_verified",
    }
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="gbrain_verification",
        capability_status=approval_status
        if washu_verified
        else "school_dossier_ready_to_submit"
        if stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0 and accepted_people
        else "next_lane_approved_school_not_verified"
        if approval_status == "ucsf_school_verified_next_lane_approved"
        else "not_submitted",
        maturity_level=4 if washu_verified else 1,
        evidence_count=len(gbrain.get("attempts", [])) if washu_verified else 1 if approval_status == "ucsf_school_verified_next_lane_approved" else 0,
        blocker_count=0 if washu_verified or (stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0 and accepted_people) else 1,
        candidate_count=0,
        automation_status="http_mcp_query_and_think_available",
        route_hop_policy="school verification requires roster-route/action gaps closed or explicitly justified",
        parser_policy="school dossier must separate denominator seeds from accepted roster truth",
        identity_policy=common_identity,
        freshness_policy="submit a fresh WashU readiness dossier after route probes, roster capture, and queue closure",
        recommended_next_action=(
            "move to the next top-50 primary school lane while preserving WashU refresh and closure-revalidation evidence"
            if washu_verified
            else
            "submit a fresh WashU readiness dossier through HTTP MCP; keep school unverified until GBrain approves this exact school-level effect"
            if stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0 and accepted_people
            else "do not request WashU school verification until denominator freshness and roster-route gaps are resolved"
        ),
        target_artifacts=[
            "artifacts/data/gbrain_consultation_ledger.json",
            "artifacts/data/school_readiness_dossiers.csv",
            "artifacts/data/washu_training_summary.json",
            "artifacts/data/washu_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_drift_summary.json",
            "artifacts/data/washu_fellowship_scope_review_summary.json",
        ],
        evidence={
            "approval_status": approval_status,
            "latest_advisory_summary": gbrain.get("latest_advisory_summary", {}),
            "acceptance_gate_summary": acceptance_gate_summary,
            "approved_manifest_summary": approved_manifest_summary,
            "approved_manifest_drift_summary": approved_manifest_drift_summary,
        },
        generated_at=generated_at,
    ))
    return rows


def build_yale_rows(conn: sqlite3.Connection, generated_at: str, target: dict) -> list[dict[str, str]]:
    school_key = target.get("school_key", "brimr_2024_school_003")
    school_name = target.get("school_name", "YALE UNIVERSITY SCH OF MEDICINE")
    sponsoring = "Yale-New Haven Medical Center"
    stats = school_program_stats(conn, sponsoring)
    training_summary = read_json(ARTIFACTS / "yale_training_summary.json", {})
    probe_summary = read_json(ARTIFACTS / "yale_program_page_probe_summary.json", {})
    route_summary = read_json(ARTIFACTS / "yale_roster_route_inspection_summary.json", {})
    second_hop_candidate_summary = read_json(ARTIFACTS / "yale_second_hop_source_candidate_summary.json", {})
    second_hop_route_summary = read_json(ARTIFACTS / "yale_second_hop_roster_route_inspection_summary.json", {})
    broad_source_summary = read_json(ARTIFACTS / "yale_source_probe_summary.json", {})
    broad_route_summary = read_json(ARTIFACTS / "yale_broad_roster_route_inspection_summary.json", {})
    parser_ready_summary = read_json(ARTIFACTS / "yale_parser_ready_roster_summary.json", {})
    acceptance_gate_summary = read_json(ARTIFACTS / "yale_parser_ready_acceptance_gate_summary.json", {})
    gbrain = read_json(ARTIFACTS / "gbrain_consultation_ledger.json", {})
    yale_lane_approved = any(
        row.get("approval_effect") == "yale_primary_lane_opening_approved_school_not_verified"
        for row in gbrain.get("attempts", [])
    )
    common_identity = (
        "Do not create or merge Yale trainee identities from program-index, department-hub, or program-context pages; "
        "create people only from verified current-resident/current-fellow roster sections with source-scoped evidence."
    )
    denominator_rows = int(training_summary.get("program_denominator_rows") or stats["coverage_rows"])
    probe_rows = int(probe_summary.get("probe_rows") or 0)
    source_candidate_rows = int(probe_summary.get("source_candidate_rows") or 0)
    route_rows = int(route_summary.get("rows") or 0)
    second_hop_candidate_rows = int(second_hop_candidate_summary.get("second_hop_source_candidate_rows") or 0)
    second_hop_route_rows = int(second_hop_route_summary.get("rows") or 0)
    broad_source_probe_rows = int(broad_source_summary.get("source_pages_probed") or 0)
    broad_source_candidate_rows = int(broad_source_summary.get("candidate_urls") or 0)
    broad_source_search_query_rows = int(broad_source_summary.get("search_query_rows") or 0)
    broad_route_rows = int(broad_route_summary.get("rows") or 0)
    parser_review_candidates = int(route_summary.get("parser_review_candidate_rows") or 0) + int(second_hop_route_summary.get("parser_review_candidate_rows") or 0)
    flat_text_parser_candidates = int(route_summary.get("flat_text_parser_candidate_rows") or 0) + int(second_hop_route_summary.get("flat_text_parser_candidate_rows") or 0)
    parser_ready_rows = int(parser_ready_summary.get("parser_ready_rows") or 0)
    acceptance_gate_rows = int(acceptance_gate_summary.get("rows") or 0)
    evidence_ready_rows = int(acceptance_gate_summary.get("evidence_ready_rows") or 0)
    blocked_gate_rows = int(acceptance_gate_summary.get("blocked_rows") or 0)
    yale_person_acceptance_approved = bool(acceptance_gate_summary.get("gbrain_person_acceptance_approval_present"))
    accepted_people = int(training_summary.get("people") or 0)
    accepted_gate_rows = int(training_summary.get("accepted_incremental_gate_rows") or 0)
    coverage_gaps_closed = stats["queue_rows"] == 0 and stats["unresolved_open_gap_rows"] == 0
    route_materialized = probe_rows >= denominator_rows and denominator_rows > 0
    inspection_materialized = (route_rows > 0 or source_candidate_rows == 0) and (
        second_hop_route_rows > 0 or second_hop_candidate_rows == 0
    )
    if accepted_people and accepted_gate_rows and coverage_gaps_closed:
        roster_capability_status = "accepted_incremental_person_subset_with_scoped_exclusions_school_not_verified"
        roster_automation_status = "gbrain_approved_yale_acceptance_loader_and_closure_packet_materialized"
        roster_next_action = "submit Yale school readiness dossier to GBrain; retain excluded parser rows as non-mutating evidence"
    elif accepted_people and accepted_gate_rows:
        roster_capability_status = "accepted_incremental_person_subset_school_not_verified"
        roster_automation_status = "gbrain_approved_yale_acceptance_loader_materialized"
        roster_next_action = "continue Yale denominator and blocked-row gap remediation before school verification"
    elif acceptance_gate_rows and yale_person_acceptance_approved and evidence_ready_rows:
        roster_capability_status = "parser_ready_acceptance_gate_approved_but_no_loader_run"
        roster_automation_status = "parser_ready_acceptance_gate_materialized_with_gbrain_person_approval"
        roster_next_action = "run the Yale accepted-person loader for the exact GBrain-approved gate subset"
    elif acceptance_gate_rows:
        roster_capability_status = "parser_ready_acceptance_gate_partial_evidence_ready_no_people_loaded"
        roster_automation_status = "parser_ready_acceptance_gate_materialized_pending_gbrain_person_approval"
        roster_next_action = "submit exact Yale acceptance-gate subset to GBrain; load only approved evidence-ready rows if approved"
    elif parser_ready_rows:
        roster_capability_status = "parser_ready_review_artifact_materialized_no_people_loaded"
        roster_automation_status = "parser_ready_artifact_no_acceptance_gate"
        roster_next_action = "submit Yale parser-ready artifact for acceptance-gate review; do not ingest people without GBrain approval"
    elif route_materialized and inspection_materialized:
        roster_capability_status = "route_inspected_no_people_loaded"
        roster_automation_status = "no_current_roster_parser_loaded_for_yale_yet"
        roster_next_action = "review Yale route-inspection parser candidates and implement scoped current-roster parsers"
    else:
        roster_capability_status = "not_started_denominator_only"
        roster_automation_status = "no_current_roster_parser_loaded_for_yale_yet"
        roster_next_action = "continue Yale route discovery or document no-public-roster closure facts before any people"
    roster_evidence_count = accepted_people or (evidence_ready_rows if acceptance_gate_rows else parser_ready_rows)
    roster_blocker_count = 0 if coverage_gaps_closed and accepted_people else blocked_gate_rows if acceptance_gate_rows else denominator_rows
    rows: list[dict[str, str]] = []
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="target_registry",
        capability_status="materialized_top50_target",
        maturity_level=3,
        evidence_count=1,
        blocker_count=0,
        candidate_count=0,
        automation_status="scripted_from_brimr_workbook",
        route_hop_policy="not_applicable",
        parser_policy="not_applicable",
        identity_policy="canonical BRIMR target remains separate from Yale-New Haven sponsoring-institution label",
        freshness_policy="refresh when BRIMR target basis changes or user/gbrain changes top-50 definition",
        recommended_next_action="continue Yale as the GBrain-approved next primary school lane after WashU",
        target_artifacts=["artifacts/data/top50_medical_school_targets.json"],
        evidence={"target_rank": target.get("target_rank"), "target_basis": target.get("target_basis")},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="denominator_discovery",
        capability_status="official_yale_program_index_seeded_open_denominator",
        maturity_level=3 if denominator_rows else 1,
        evidence_count=denominator_rows,
        blocker_count=0 if denominator_rows else 1,
        candidate_count=denominator_rows,
        automation_status="repeatable_plain_http_ysm_program_index_parser",
        route_hop_policy="official YSM Residency & Fellowship Programs index seeds Yale program/source rows before route probing",
        parser_policy="program-index rows do not create people; current trainee rows require route-scoped roster parsers",
        identity_policy=common_identity,
        freshness_policy="refresh the YSM program index hash before Yale school verification and on scheduled school refresh",
        recommended_next_action="probe seeded Yale program URLs for public current resident/fellow roster signals",
        target_artifacts=[
            "artifacts/data/yale_training_sources.json",
            "artifacts/data/yale_gme_program_universe.csv",
            "artifacts/data/yale_gme_program_universe.json",
            "artifacts/data/yale_gme_program_universe_source.json",
            "artifacts/data/yale_gme_program_coverage.json",
            "artifacts/data/yale_training_summary.json",
            "artifacts/data/yale_program_page_probe.csv",
            "artifacts/data/yale_program_page_probe_summary.json",
        ],
        evidence={"training_summary": training_summary, "coverage": stats, "probe_summary": probe_summary},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="official_roster_capture",
        capability_status=roster_capability_status,
        maturity_level=3 if parser_ready_rows else (2 if route_materialized and inspection_materialized else 1),
        evidence_count=roster_evidence_count,
        blocker_count=roster_blocker_count,
        candidate_count=parser_ready_rows or (parser_review_candidates + flat_text_parser_candidates),
        automation_status=roster_automation_status,
        route_hop_policy="only accept pages scoped to current named residents or fellows; program overview pages stay context evidence",
        parser_policy="write scoped parsers only after official program route inspection confirms current-trainee sections",
        identity_policy=common_identity,
        freshness_policy="source hashes and route-discovery evidence must be refreshed before Yale people are accepted",
        recommended_next_action=roster_next_action,
        target_artifacts=[
            "artifacts/data/yale_gme_program_coverage.json",
            "artifacts/data/yale_training_summary.json",
            "artifacts/data/yale_roster_route_inspection.csv",
            "artifacts/data/yale_roster_route_inspection_summary.json",
            "artifacts/data/yale_second_hop_roster_route_inspection.csv",
            "artifacts/data/yale_second_hop_roster_route_inspection_summary.json",
            "artifacts/data/yale_source_probes.json",
            "artifacts/data/yale_source_probe_summary.json",
            "artifacts/data/yale_broad_source_candidates.csv",
            "artifacts/data/yale_source_search_queries.csv",
            "artifacts/data/yale_broad_roster_route_inspection.csv",
            "artifacts/data/yale_broad_roster_route_inspection_summary.json",
            "artifacts/data/yale_parser_ready_rosters.csv",
            "artifacts/data/yale_parser_ready_roster_summary.json",
            "artifacts/data/yale_parser_ready_acceptance_gate.csv",
            "artifacts/data/yale_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/yale_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/yale_approved_parser_ready_gate_manifest_summary.json",
            "artifacts/data/yale_gbrain_acceptance_packet_summary.json",
            "artifacts/data/yale_pending_acceptance_packet_summary.json",
            "artifacts/data/yale_exact_candidate_acceptance_packet_summary.json",
            "artifacts/data/yale_remaining_target_source_search.csv",
            "artifacts/data/yale_remaining_target_source_search_summary.json",
            "artifacts/data/yale_remaining_target_acceptance_packet_summary.json",
            "artifacts/data/yale_radiology_fellowship_source_probe.csv",
            "artifacts/data/yale_radiology_fellowship_source_probe_summary.json",
            "artifacts/data/yale_radiology_fellowship_source_search_observations.csv",
            "artifacts/data/yale_radiology_fellowship_acceptance_packet_summary.json",
            "artifacts/data/yale_radiology_fellowship_scope_review.csv",
            "artifacts/data/yale_radiology_fellowship_scope_review_summary.json",
            "artifacts/data/yale_residual_denominator_source_probe.csv",
            "artifacts/data/yale_residual_denominator_source_probe_summary.json",
            "artifacts/data/yale_internal_medicine_acceptance_packet_summary.json",
            "artifacts/data/yale_denominator_mapping_packet.csv",
            "artifacts/data/yale_denominator_mapping_packet_summary.json",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet.csv",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet_summary.json",
            "artifacts/data/yale_candidate_closure_audit.csv",
            "artifacts/data/yale_candidate_closure_summary.json",
            "artifacts/data/yale_action_queue_triage.csv",
            "artifacts/data/yale_action_queue_triage_summary.json",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet.csv",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet_summary.json",
        ],
        evidence={
            "training_summary": training_summary,
            "coverage": stats,
            "route_summary": route_summary,
            "second_hop_route_summary": second_hop_route_summary,
            "broad_source_summary": broad_source_summary,
            "broad_route_summary": broad_route_summary,
            "parser_ready_summary": parser_ready_summary,
            "acceptance_gate_summary": acceptance_gate_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="route_inspection",
        capability_status=(
            "program_page_probe_and_candidate_inspection_materialized"
            if route_materialized and inspection_materialized
            else "not_started_program_index_seeded"
        ),
        maturity_level=3 if route_materialized and inspection_materialized else 1,
        evidence_count=probe_rows + route_rows + second_hop_route_rows + broad_source_probe_rows + broad_source_search_query_rows + broad_route_rows,
        blocker_count=0 if route_materialized and inspection_materialized else denominator_rows,
        candidate_count=source_candidate_rows + second_hop_candidate_rows + broad_source_candidate_rows,
        automation_status=(
            "repeatable_http_probe_plus_headed_candidate_inspection"
            if route_materialized and inspection_materialized
            else "route_probe_not_yet_materialized"
        ),
        route_hop_policy="first hop from official YSM program links, then department education/residency/fellowship pages, then roster candidates",
        parser_policy="route candidates remain review inputs until current named trainees are extracted into accepted evidence",
        identity_policy=common_identity,
        freshness_policy="rerun route inspection when Yale program index hash or program URLs change",
        recommended_next_action=(
            "triage route-inspection statuses into parser-ready sources or explicit no-public-roster closure facts"
            if route_materialized and inspection_materialized
            else "materialize Yale program-page probe and headed route-inspection ledgers"
        ),
        target_artifacts=[
            "artifacts/data/yale_gme_program_universe.csv",
            "artifacts/data/yale_program_page_probe.csv",
            "artifacts/data/yale_source_candidates.csv",
            "artifacts/data/yale_roster_route_inspection.csv",
            "artifacts/data/yale_second_hop_source_candidates.csv",
            "artifacts/data/yale_second_hop_roster_route_inspection.csv",
            "artifacts/data/yale_source_probes.json",
            "artifacts/data/yale_broad_source_candidates.csv",
            "artifacts/data/yale_source_search_queries.csv",
            "artifacts/data/yale_broad_roster_route_inspection.csv",
            "artifacts/data/yale_broad_roster_route_inspection_summary.json",
            "artifacts/data/yale_parser_ready_rosters.csv",
            "artifacts/data/yale_parser_ready_acceptance_gate.csv",
            "artifacts/data/yale_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/yale_action_queue_triage.csv",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet.csv",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet_summary.json",
            "artifacts/data/yale_candidate_closure_audit.csv",
            "artifacts/data/yale_candidate_closure_summary.json",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet.csv",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet_summary.json",
        ],
        evidence={
            "training_summary": training_summary,
            "coverage": stats,
            "probe_summary": probe_summary,
            "route_summary": route_summary,
            "second_hop_candidate_summary": second_hop_candidate_summary,
            "second_hop_route_summary": second_hop_route_summary,
            "broad_source_summary": broad_source_summary,
            "broad_route_summary": broad_route_summary,
            "parser_ready_summary": parser_ready_summary,
            "acceptance_gate_summary": acceptance_gate_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="coverage_gap_resolution",
        capability_status=(
            "terminal_denominator_closure_materialized_school_verification_ready"
            if coverage_gaps_closed
            else "action_queue_open_denominator_seeded"
        ),
        maturity_level=3 if coverage_gaps_closed else 1,
        evidence_count=int(stats["terminal_closure_rows"]) if coverage_gaps_closed else int(stats["queue_rows"]),
        blocker_count=0 if coverage_gaps_closed else int(stats["queue_rows"] or stats["unresolved_open_gap_rows"] or denominator_rows),
        candidate_count=denominator_rows,
        automation_status=(
            "warehouse_action_queue_drained_by_gbrain_approved_non_mutating_closure"
            if coverage_gaps_closed
            else "warehouse_action_queue_materialized_from_yale_denominator"
        ),
        route_hop_policy="do not close no-roster rows until first-hop and reasonable second-hop official route discovery are documented",
        parser_policy="candidate roster pages must feed acceptance/reviewer ledgers before coverage can move to covered_current_roster",
        identity_policy=common_identity,
        freshness_policy="gap status expires when the Yale program-index hash or program URL changes",
        recommended_next_action=(
            "submit Yale readiness dossier to GBrain; keep closure facts on scheduled refresh/revalidation"
            if coverage_gaps_closed
            else "drain Yale action queue through route probes, parser additions, or explicit no-public-roster closure facts"
        ),
        target_artifacts=[
            "artifacts/data/official_program_coverage_action_queue.csv",
            "artifacts/data/official_program_coverage_assurance_audit.csv",
            "artifacts/data/official_program_coverage_dossiers.csv",
            "artifacts/data/yale_gme_program_coverage.json",
            "artifacts/data/yale_program_page_probe.csv",
            "artifacts/data/yale_source_candidates.csv",
            "artifacts/data/yale_roster_route_inspection.csv",
            "artifacts/data/yale_second_hop_source_candidates.csv",
            "artifacts/data/yale_second_hop_roster_route_inspection.csv",
            "artifacts/data/yale_source_probes.json",
            "artifacts/data/yale_source_probe_summary.json",
            "artifacts/data/yale_broad_source_candidates.csv",
            "artifacts/data/yale_source_search_queries.csv",
            "artifacts/data/yale_broad_roster_route_inspection.csv",
            "artifacts/data/yale_broad_roster_route_inspection_summary.json",
            "artifacts/data/yale_parser_ready_rosters.csv",
            "artifacts/data/yale_parser_ready_acceptance_gate.csv",
            "artifacts/data/yale_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/yale_action_queue_triage.csv",
            "artifacts/data/yale_action_queue_triage_summary.json",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet.csv",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet_summary.json",
            "artifacts/data/yale_candidate_closure_audit.csv",
            "artifacts/data/yale_candidate_closure_summary.json",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet.csv",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet_summary.json",
        ],
        evidence={
            "coverage": stats,
            "training_summary": training_summary,
            "probe_summary": probe_summary,
            "route_summary": route_summary,
            "second_hop_candidate_summary": second_hop_candidate_summary,
            "second_hop_route_summary": second_hop_route_summary,
            "broad_source_summary": broad_source_summary,
            "broad_route_summary": broad_route_summary,
            "parser_ready_summary": parser_ready_summary,
            "acceptance_gate_summary": acceptance_gate_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="identity_normalization",
        capability_status=(
            "accepted_subset_identity_scoped_exclusions_retained"
            if accepted_people and coverage_gaps_closed
            else "accepted_subset_identity_scoped_blocked_rows_retained"
            if accepted_people
            else "gated_no_yale_people_loaded"
        ),
        maturity_level=3 if accepted_people and coverage_gaps_closed else 2,
        evidence_count=accepted_people or evidence_ready_rows,
        blocker_count=0 if accepted_people and coverage_gaps_closed else blocked_gate_rows,
        candidate_count=acceptance_gate_rows,
        automation_status=(
            "accepted_subset_with_scoped_exclusions_retained_after_closure"
            if accepted_people and coverage_gaps_closed
            else "accepted_subset_with_blocked_identity_scope_rows_retained"
            if accepted_people
            else "acceptance_gate_blocks_identity_ambiguous_yale_rows"
            if acceptance_gate_rows
            else "identity_gate_present_but_no_yale_person_rows"
        ),
        route_hop_policy="not_applicable",
        parser_policy="Yale parser-ready rows are split into exact evidence-ready rows and blocked scope/identity rows before any person creation",
        identity_policy=common_identity,
        freshness_policy="recompute source-scoped identity conflicts on every Yale roster refresh",
        recommended_next_action=(
            "submit Yale school readiness dossier; keep excluded duplicate/scope rows as retained non-mutating evidence"
            if accepted_people and coverage_gaps_closed
            else "review and remediate blocked duplicate/shared-source Yale rows; do not merge them into accepted people"
            if accepted_people
            else "keep identity lane closed to denominator-only evidence; open after first accepted Yale roster observations"
        ),
        target_artifacts=[
            "artifacts/data/yale_training_summary.json",
            "artifacts/data/yale_parser_ready_acceptance_gate.csv",
            "artifacts/data/yale_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/yale_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/yale_approved_parser_ready_gate_manifest_summary.json",
            "artifacts/data/yale_action_queue_triage.csv",
            "artifacts/data/yale_action_queue_triage_summary.json",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet.csv",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet_summary.json",
            "artifacts/data/yale_candidate_closure_audit.csv",
            "artifacts/data/yale_candidate_closure_summary.json",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet.csv",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet_summary.json",
        ],
        evidence={"training_summary": training_summary, "acceptance_gate_summary": acceptance_gate_summary},
        generated_at=generated_at,
    ))
    yale_approval_status = school_gbrain_status(gbrain, school_name)
    yale_verified = yale_approval_status in {
        "yale_school_verified_next_lane_approved",
        "yale_school_verified_after_cardiac_surgery_delta_approved",
        "vanderbilt_primary_lane_opening_approved_school_not_verified",
    }
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="gbrain_verification",
        capability_status=(
            yale_approval_status
            if yale_verified
            else
            "yale_primary_lane_approved_school_not_verified"
            if yale_lane_approved
            else "not_submitted"
        ),
        maturity_level=4 if yale_verified else 1,
        evidence_count=(
            len(gbrain.get("attempts", []))
            if yale_verified
            else 1
            if yale_lane_approved
            else 0
        ),
        blocker_count=0 if yale_verified else 1,
        candidate_count=0,
        automation_status="http_mcp_query_and_think_available",
        route_hop_policy="school verification requires roster-route/action gaps closed or explicitly justified",
        parser_policy="school dossier must separate denominator rows from accepted people",
        identity_policy=common_identity,
        freshness_policy="submit a fresh Yale readiness dossier after route probes, roster capture, and queue closure",
        recommended_next_action=(
            "move to the next top-50 school lane; keep Yale on scheduled refresh and closure revalidation"
            if yale_verified
            else "do not request Yale school verification until denominator freshness and roster-route gaps are resolved"
        ),
        target_artifacts=[
            "artifacts/data/gbrain_consultation_ledger.json",
            "artifacts/data/school_readiness_dossiers.csv",
            "artifacts/data/yale_training_summary.json",
            "artifacts/data/yale_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/yale_approved_parser_ready_gate_manifest_summary.json",
            "artifacts/data/yale_gbrain_acceptance_packet_summary.json",
            "artifacts/data/yale_pending_acceptance_packet_summary.json",
            "artifacts/data/yale_exact_candidate_acceptance_packet_summary.json",
            "artifacts/data/yale_remaining_target_source_search_summary.json",
            "artifacts/data/yale_remaining_target_acceptance_packet_summary.json",
            "artifacts/data/yale_radiology_fellowship_source_probe_summary.json",
            "artifacts/data/yale_radiology_fellowship_acceptance_packet_summary.json",
            "artifacts/data/yale_radiology_fellowship_scope_review_summary.json",
            "artifacts/data/yale_residual_denominator_source_probe_summary.json",
            "artifacts/data/yale_internal_medicine_acceptance_packet_summary.json",
            "artifacts/data/yale_denominator_mapping_packet_summary.json",
            "artifacts/data/yale_action_queue_triage_summary.json",
            "artifacts/data/yale_denominator_alias_global_health_closure_packet_summary.json",
            "artifacts/data/yale_candidate_closure_summary.json",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet_summary.json",
            "artifacts/research/yale-parser-ready-acceptance-gbrain-packet-2026-06-06.md",
            "artifacts/research/yale-addiction-medicine-acceptance-gbrain-packet-2026-06-06.md",
            "artifacts/research/yale-exact-candidate-acceptance-gbrain-packet-2026-06-06.md",
            "artifacts/research/yale-action-queue-triage-2026-06-06.md",
            "artifacts/research/yale-cardiac-surgery-role-conflict-gbrain-packet-2026-06-06.md",
        ],
        evidence={
            "approval_status": yale_approval_status,
            "latest_advisory_summary": gbrain.get("latest_advisory_summary", {}),
            "acceptance_gate_summary": acceptance_gate_summary,
        },
        generated_at=generated_at,
    ))
    return rows


def build_vanderbilt_rows(conn: sqlite3.Connection, generated_at: str, target: dict) -> list[dict[str, str]]:
    school_key = target.get("school_key", "brimr_2024_school_005")
    school_name = target.get("school_name", "VANDERBILT UNIVERSITY SCH OF MEDICINE")
    sponsoring = "Vanderbilt University Medical Center"
    stats = school_program_stats(conn, sponsoring)
    training_summary = read_json(ARTIFACTS / "vanderbilt_training_summary.json", {})
    probe_summary = read_json(ARTIFACTS / "vanderbilt_program_page_probe_summary.json", {})
    route_summary = read_json(ARTIFACTS / "vanderbilt_roster_route_inspection_summary.json", {})
    second_hop_route_summary = read_json(ARTIFACTS / "vanderbilt_second_hop_roster_route_inspection_summary.json", {})
    route_packet_summary = read_json(ARTIFACTS / "vanderbilt_route_review_packet_summary.json", {})
    parser_extraction_summary = read_json(ARTIFACTS / "vanderbilt_parser_ready_extraction_packet_summary.json", {})
    approved_manifest_summary = read_json(ARTIFACTS / "vanderbilt_approved_parser_ready_manifest_summary.json", {})
    candidate_closure_summary = read_json(ARTIFACTS / "vanderbilt_candidate_closure_summary.json", {})
    scope_mapping_closure_summary = read_json(ARTIFACTS / "vanderbilt_scope_mapping_closure_packet_summary.json", {})
    approved_source_disposition_summary = read_json(ARTIFACTS / "vanderbilt_approved_candidate_source_disposition_summary.json", {})
    parser_manual_repair_summary = read_json(ARTIFACTS / "vanderbilt_parser_manual_repair_summary.json", {})
    parser_repair_acceptance_summary = read_json(ARTIFACTS / "vanderbilt_parser_repair_acceptance_packet_summary.json", {})
    active_source_target_summary = read_json(ARTIFACTS / "vanderbilt_active_source_candidate_targets_summary.json", {})
    active_source_route_summary = read_json(ARTIFACTS / "vanderbilt_active_source_candidate_route_inspection_summary.json", {})
    active_second_hop_summary = read_json(ARTIFACTS / "vanderbilt_active_second_hop_route_inspection_summary.json", {})
    active_source_acceptance_summary = read_json(ARTIFACTS / "vanderbilt_active_source_acceptance_packet_summary.json", {})
    gap_resolution_summary = read_json(ARTIFACTS / "school_gap_resolution_manifest_summary.json", {})
    gap_resolution_batch_summary = read_json(ARTIFACTS / "school_gap_resolution_batch_summary.json", {})
    gap_resolution_batch_packet_summary = read_json(ARTIFACTS / "school_gap_resolution_batch_packet_summary.json", {})
    gbrain = read_json(ARTIFACTS / "gbrain_consultation_ledger.json", {})
    approval_status = school_gbrain_status(gbrain, school_name)
    lane_open = approval_status == "vanderbilt_primary_lane_opening_approved_school_not_verified"
    membership_accepted = (
        training_summary.get("incremental_acceptance_status") == "accepted_exact_gbrain_approved_manifest"
        and training_summary.get("incremental_acceptance_approval_effect")
        == "vanderbilt_exact_parser_ready_membership_acceptance_approved"
    )
    parser_repair_accepted = (
        training_summary.get("parser_repair_incremental_acceptance_approval_effect")
        == "vanderbilt_parser_repair_incremental_membership_acceptance_approved"
        and int(training_summary.get("accepted_vanderbilt_parser_repair_membership_rows") or 0)
        == int(parser_repair_acceptance_summary.get("rows") or 0)
    )
    active_source_accepted = (
        training_summary.get("active_source_incremental_acceptance_approval_effect")
        == "vanderbilt_active_source_neurosurgery_incremental_membership_acceptance_approved"
        and int(training_summary.get("accepted_vanderbilt_active_source_membership_rows") or 0)
        == int(active_source_acceptance_summary.get("rows") or 0)
    )
    scale_gap = training_summary.get("source_scale_gap_status") or ""
    denominator_rows = int(training_summary.get("program_denominator_rows") or stats["coverage_rows"])
    probe_rows = int(probe_summary.get("probe_rows") or 0)
    source_candidate_rows = int(probe_summary.get("source_candidate_rows") or 0)
    candidate_roster_link_rows = int(probe_summary.get("candidate_roster_link_rows") or 0)
    roster_text_signal_rows = int((probe_summary.get("by_probe_status") or {}).get("roster_text_signal_without_link") or 0)
    no_program_url_rows = int((probe_summary.get("by_probe_status") or {}).get("no_program_url") or 0)
    context_only_rows = int((probe_summary.get("by_probe_status") or {}).get("official_program_context_no_roster_signal") or 0)
    common_identity = (
        "Do not create or merge Vanderbilt trainee identities from the GME program index alone; create people only "
        "from verified current-resident/current-fellow roster sections with source-scoped evidence and a GBrain gate."
    )
    rows: list[dict[str, str]] = []
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="target_registry",
        capability_status="materialized_top50_target",
        maturity_level=3,
        evidence_count=1,
        blocker_count=0,
        candidate_count=0,
        automation_status="scripted_from_brimr_workbook",
        route_hop_policy="not_applicable",
        parser_policy="not_applicable",
        identity_policy="canonical BRIMR school target remains separate from VUMC sponsoring-institution identity",
        freshness_policy="refresh when BRIMR target basis changes or user/gbrain changes top-50 definition",
        recommended_next_action="retain Vanderbilt as the rank-5 primary lane after Yale verification",
        target_artifacts=["artifacts/data/top50_medical_school_targets.json"],
        evidence={"target_rank": target.get("target_rank"), "target_basis": target.get("target_basis")},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="denominator_discovery",
        capability_status="repeatable_official_index_with_scale_caveat" if scale_gap else "repeatable_official_index",
        maturity_level=3,
        evidence_count=int(training_summary.get("program_denominator_rows") or stats["coverage_rows"]),
        blocker_count=1 if scale_gap == "index_rows_equal_180_but_welcome_claims_over_180_programs" else 0,
        candidate_count=int(training_summary.get("linked_program_rows") or 0),
        automation_status="scripted_official_vumc_gme_index_parser",
        route_hop_policy="official VUMC GME Training Programs index is the denominator seed; linked and unlinked rows remain explicit",
        parser_policy="denominator rows do not create people; coverage requires accepted current roster observations",
        identity_policy=common_identity,
        freshness_policy="refresh VUMC training-programs page and scale-context pages before route probes or school verification",
        recommended_next_action=(
            "reconcile the official index's 180 parsed rows against VUMC's over-180 scale wording, then probe linked program pages"
            if scale_gap
            else "probe linked Vanderbilt program URLs for current resident/fellow roster routes"
        ),
        target_artifacts=[
            "artifacts/data/vanderbilt_gme_program_universe.csv",
            "artifacts/data/vanderbilt_gme_program_universe.json",
            "artifacts/data/vanderbilt_gme_program_coverage.json",
            "artifacts/data/vanderbilt_training_summary.json",
        ],
        evidence={"coverage": stats, "training_summary": training_summary},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="official_roster_capture",
        capability_status=(
            "exact_memberships_accepted_with_active_source_school_not_verified"
            if active_source_accepted
            else
            "exact_memberships_accepted_with_parser_repair_school_not_verified"
            if parser_repair_accepted
            else
            "exact_memberships_accepted_parser_repair_packet_ready_gbrain_gate_required"
            if parser_repair_acceptance_summary.get("approval_effect_requested") == "vanderbilt_parser_repair_incremental_membership_acceptance_approved"
            else
            "exact_memberships_accepted_source_dispositions_approved_denominator_closure_denied"
            if approved_source_disposition_summary.get("approval_effect") == "vanderbilt_scope_mapping_candidate_source_exclusion_and_mapping_allowed_for_exact_rowset"
            else
            "exact_memberships_accepted_scope_mapping_packet_ready_school_not_verified"
            if membership_accepted and scope_mapping_closure_summary.get("rowset_status") == "complete"
            else
            "exact_memberships_accepted_gap_closure_audit_complete_school_not_verified"
            if membership_accepted and candidate_closure_summary.get("program_representation_status") == "complete"
            else
            "exact_parser_ready_memberships_accepted_school_not_verified"
            if membership_accepted
            else
            "parser_ready_extraction_packets_materialized_no_people_ingested"
            if parser_extraction_summary
            else
            "route_review_packets_materialized_no_people_ingested"
            if route_packet_summary
            else
            "route_candidates_inspected_no_people_ingested"
            if route_summary
            else "route_candidates_discovered_no_people_ingested"
            if source_candidate_rows
            else "not_started_no_people_ingested"
        ),
        maturity_level=4 if route_packet_summary or parser_extraction_summary else (3 if route_summary else (2 if source_candidate_rows else (1 if lane_open else 0))),
        evidence_count=int(
            training_summary.get("accepted_vanderbilt_parser_ready_membership_rows")
            or parser_extraction_summary.get("evidence_ready_candidate_rows")
            or route_packet_summary.get("packet_rows")
            or route_summary.get("rows")
            or source_candidate_rows
        ),
        blocker_count=int(stats["unresolved_open_gap_rows"]),
        candidate_count=int(
            training_summary.get("accepted_vanderbilt_parser_ready_membership_rows")
            or parser_extraction_summary.get("evidence_ready_candidate_rows")
            or route_packet_summary.get("parser_review_candidate_packets")
            or source_candidate_rows
            or training_summary.get("linked_program_rows")
            or 0
        ),
        automation_status=(
            "repeatable_program_page_probe_materialized_no_people_ingested"
            if source_candidate_rows
            else "not_started_for_vanderbilt"
        ),
        route_hop_policy="probe only official VUMC/Vanderbilt-linked program pages; do not infer people from applicant/program context",
        parser_policy=(
            "exact GBrain-approved Vanderbilt membership manifest may create membership-scoped accepted rows; "
            "blocked extraction rows and residual routes remain non-mutating"
            if membership_accepted
            else "build parsers only after route inspection confirms current-trainee sections"
        ),
        identity_policy=common_identity,
        freshness_policy="record page hash/fetch timestamp for each roster candidate before parser acceptance",
        recommended_next_action=(
            "continue Vanderbilt denominator gap resolution; do not request school verification until open route/source/closure gaps are resolved"
            if membership_accepted and candidate_closure_summary.get("program_representation_status") == "complete"
            else "continue Vanderbilt denominator gap resolution; do not request school verification until open route/source/closure gaps are resolved"
            if membership_accepted
            else "publish an exact Vanderbilt parser-ready GBrain packet for evidence-ready rows, while keeping blocked extraction rows out of acceptance"
            if parser_extraction_summary
            else "turn parser-review packets into exact non-mutating parser-ready rowsets, then ask GBrain before any Vanderbilt ingestion"
            if route_packet_summary
            else "materialize parser-ready review packets for target-scope current-trainee candidates; keep people and closures gated"
            if route_summary
            else "run headed route inspection across Vanderbilt roster-link candidates; do not accept people or close gaps yet"
            if source_candidate_rows
            else "run first-hop roster-route inspection across linked Vanderbilt program pages"
        ),
        target_artifacts=[
            "artifacts/data/vanderbilt_training_sources.json",
            "artifacts/data/vanderbilt_gme_program_universe.json",
            "artifacts/data/vanderbilt_program_page_probe.csv",
            "artifacts/data/vanderbilt_program_page_probe_summary.json",
            "artifacts/data/vanderbilt_source_candidates.csv",
            "artifacts/data/vanderbilt_roster_route_inspection.csv",
            "artifacts/data/vanderbilt_roster_route_inspection_summary.json",
            "artifacts/data/vanderbilt_second_hop_source_candidates.csv",
            "artifacts/data/vanderbilt_second_hop_roster_route_inspection.csv",
            "artifacts/data/vanderbilt_second_hop_roster_route_inspection_summary.json",
            "artifacts/data/vanderbilt_route_review_packets.csv",
            "artifacts/data/vanderbilt_route_review_packet_summary.json",
            "artifacts/data/vanderbilt_parser_ready_extraction_packets.csv",
            "artifacts/data/vanderbilt_parser_ready_extraction_candidates.csv",
            "artifacts/data/vanderbilt_parser_ready_extraction_packet_summary.json",
            "artifacts/data/vanderbilt_approved_parser_ready_manifest.csv",
            "artifacts/data/vanderbilt_approved_parser_ready_manifest_summary.json",
            "artifacts/data/vanderbilt_training_people.csv",
            "artifacts/data/vanderbilt_candidate_closure_audit.csv",
            "artifacts/data/vanderbilt_candidate_closure_summary.json",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet.csv",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet_summary.json",
            "artifacts/data/vanderbilt_approved_candidate_source_dispositions.csv",
            "artifacts/data/vanderbilt_approved_candidate_source_disposition_summary.json",
            "artifacts/data/vanderbilt_parser_manual_repair_probe.csv",
            "artifacts/data/vanderbilt_parser_manual_repair_summary.json",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet.csv",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet_summary.json",
            "artifacts/data/vanderbilt_active_source_candidate_targets.csv",
            "artifacts/data/vanderbilt_active_source_candidate_targets_summary.json",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection.csv",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection_summary.json",
            "artifacts/data/vanderbilt_active_second_hop_targets.csv",
            "artifacts/data/vanderbilt_active_second_hop_targets_summary.json",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection.csv",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection_summary.json",
            "artifacts/data/vanderbilt_active_source_acceptance_packet.csv",
            "artifacts/data/vanderbilt_active_source_acceptance_packet_summary.json",
            "artifacts/data/school_gap_resolution_manifest.csv",
            "artifacts/data/school_gap_resolution_manifest_summary.json",
            "artifacts/data/school_gap_resolution_batches.csv",
            "artifacts/data/school_gap_resolution_batch_summary.json",
            "artifacts/data/school_gap_resolution_batch_packets.csv",
            "artifacts/data/school_gap_resolution_batch_packet_summary.json",
        ],
        evidence={
            "training_summary": training_summary,
            "probe_summary": probe_summary,
            "route_summary": route_summary,
            "second_hop_route_summary": second_hop_route_summary,
            "route_packet_summary": route_packet_summary,
            "parser_extraction_summary": parser_extraction_summary,
            "approved_manifest_summary": approved_manifest_summary,
            "candidate_closure_summary": candidate_closure_summary,
            "scope_mapping_closure_summary": scope_mapping_closure_summary,
            "approved_source_disposition_summary": approved_source_disposition_summary,
            "parser_manual_repair_summary": parser_manual_repair_summary,
            "parser_repair_acceptance_summary": parser_repair_acceptance_summary,
            "active_source_target_summary": active_source_target_summary,
            "active_source_route_summary": active_source_route_summary,
            "active_second_hop_summary": active_second_hop_summary,
            "active_source_acceptance_summary": active_source_acceptance_summary,
            "gap_resolution_manifest_summary": gap_resolution_summary,
            "gap_resolution_batch_summary": gap_resolution_batch_summary,
            "gap_resolution_batch_packet_summary": gap_resolution_batch_packet_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="route_inspection",
        capability_status=(
            "active_source_neurosurgery_rows_accepted_residual_routes_open"
            if active_source_accepted
            else
            "parser_repair_rows_accepted_residual_routes_open"
            if parser_repair_accepted
            else
            "parser_repair_acceptance_packet_materialized_gbrain_gate_required"
            if parser_repair_acceptance_summary.get("approval_effect_requested") == "vanderbilt_parser_repair_incremental_membership_acceptance_approved"
            else
            "candidate_source_dispositions_approved_denominator_closure_denied"
            if approved_source_disposition_summary.get("approval_effect") == "vanderbilt_scope_mapping_candidate_source_exclusion_and_mapping_allowed_for_exact_rowset"
            else
            "scope_mapping_closure_packet_materialized_gbrain_gate_required"
            if scope_mapping_closure_summary.get("rowset_status") == "complete"
            else
            "gap_closure_audit_complete_membership_gate_approved_residuals_open"
            if membership_accepted and candidate_closure_summary.get("program_representation_status") == "complete"
            else
            "exact_parser_ready_membership_gate_approved_residual_routes_open"
            if membership_accepted
            else
            "parser_ready_extraction_packets_materialized_gbrain_gate_required"
            if parser_extraction_summary
            else
            "route_review_packets_materialized_parser_candidates_and_residuals_open"
            if route_packet_summary
            else
            "headed_candidate_route_inspection_completed_parser_candidates_open"
            if route_summary
            else "program_page_probe_completed_candidate_routes_open"
            if probe_rows
            else "not_started_route_probe_required"
        ),
        maturity_level=4 if route_summary or route_packet_summary else (3 if probe_rows == denominator_rows and denominator_rows else (2 if probe_rows else (1 if lane_open else 0))),
        evidence_count=int(parser_extraction_summary.get("candidate_rows") or route_packet_summary.get("packet_rows") or route_summary.get("rows") or probe_rows),
        blocker_count=int(stats["unresolved_open_gap_rows"]),
        candidate_count=int(
            route_packet_summary.get("parser_review_candidate_packets")
            or parser_extraction_summary.get("extraction_packet_rows")
            or route_summary.get("parser_review_candidate_rows")
            or source_candidate_rows
            or candidate_roster_link_rows
            or training_summary.get("linked_program_rows")
            or 0
        ),
        automation_status=(
            "repeatable_headed_route_inspection_and_packetization_over_vanderbilt_candidates"
            if route_packet_summary
            else "repeatable_headed_route_inspection_over_vanderbilt_roster_candidates"
            if route_summary
            else "repeatable_requests_probe_over_official_vumc_program_index"
            if probe_rows
            else "pending_probe_script"
        ),
        route_hop_policy="inspect linked program pages and at least one current-roster-labeled hop before parser-ready status",
        parser_policy="person-card/name structures are candidate evidence until scoped to current trainees",
        identity_policy=common_identity,
        freshness_policy="rerun route probes when program-index hash changes",
        recommended_next_action=(
            "use the 23 approved active-source Neurosurgery rows as accepted observations; continue source-candidate probes and broad source discovery for the remaining open denominator gaps"
            if active_source_accepted
            else "use the 19 approved Vanderbilt parser-repair rows as accepted observations; continue source-candidate probes and broad source discovery for the remaining open denominator gaps"
            if parser_repair_accepted
            else "submit the exact 19-row Vanderbilt parser-repair packet to GBrain before any additional membership ingestion"
            if parser_repair_acceptance_summary.get("approval_effect_requested") == "vanderbilt_parser_repair_incremental_membership_acceptance_approved"
            else "use the 45 approved Vanderbilt candidate-source dispositions as negative route/scope evidence; continue parser/manual repair and source discovery because denominator closure was denied"
            if approved_source_disposition_summary.get("approval_effect") == "vanderbilt_scope_mapping_candidate_source_exclusion_and_mapping_allowed_for_exact_rowset"
            else "submit the exact 45-row Vanderbilt scope/mapping packet to GBrain; do not mutate denominator closure unless the exact rowset is approved"
            if scope_mapping_closure_summary.get("rowset_status") == "complete"
            else "use approved membership rows as accepted observations; keep 78 blocked extraction rows and all residual denominator packets open"
            if membership_accepted and candidate_closure_summary.get("program_representation_status") == "complete"
            else "use approved membership rows as accepted observations; keep 78 blocked extraction rows and all residual denominator packets open"
            if membership_accepted
            else "submit exact GBrain packet only for Vanderbilt evidence-ready extraction rows; keep 78 blocked extraction rows and all residual denominator packets open"
            if parser_extraction_summary
            else "build exact parser-ready extraction packets from the 36 parser-review packets; resolve recursive/scope/residual buckets before school verification"
            if route_packet_summary
            else "review parser candidates, scope mismatches, and second-hop residuals; do not accept people or close gaps without a new GBrain packet"
            if route_summary
            else "run headed route inspection over source candidates, then separately resolve 24 unlinked rows, 35 roster-text pages, and 10 context-only pages"
            if probe_rows
            else "create Vanderbilt route-probe artifact before any parser-ready roster packet"
        ),
        target_artifacts=[
            "artifacts/data/vanderbilt_gme_program_universe.json",
            "artifacts/data/vanderbilt_program_page_probe.csv",
            "artifacts/data/vanderbilt_program_page_probe_summary.json",
            "artifacts/data/vanderbilt_source_candidates.csv",
            "artifacts/data/vanderbilt_roster_route_inspection.csv",
            "artifacts/data/vanderbilt_roster_route_inspection_summary.json",
            "artifacts/data/vanderbilt_second_hop_source_candidates.csv",
            "artifacts/data/vanderbilt_second_hop_roster_route_inspection.csv",
            "artifacts/data/vanderbilt_second_hop_roster_route_inspection_summary.json",
            "artifacts/data/vanderbilt_route_review_packets.csv",
            "artifacts/data/vanderbilt_route_review_packet_summary.json",
            "artifacts/data/vanderbilt_parser_ready_extraction_packets.csv",
            "artifacts/data/vanderbilt_parser_ready_extraction_candidates.csv",
            "artifacts/data/vanderbilt_parser_ready_extraction_packet_summary.json",
            "artifacts/data/vanderbilt_approved_parser_ready_manifest.csv",
            "artifacts/data/vanderbilt_approved_parser_ready_manifest_summary.json",
            "artifacts/data/vanderbilt_candidate_closure_audit.csv",
            "artifacts/data/vanderbilt_candidate_closure_summary.json",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet.csv",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet_summary.json",
            "artifacts/data/vanderbilt_approved_candidate_source_dispositions.csv",
            "artifacts/data/vanderbilt_approved_candidate_source_disposition_summary.json",
            "artifacts/data/vanderbilt_parser_manual_repair_probe.csv",
            "artifacts/data/vanderbilt_parser_manual_repair_summary.json",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet.csv",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet_summary.json",
            "artifacts/data/vanderbilt_active_source_candidate_targets.csv",
            "artifacts/data/vanderbilt_active_source_candidate_targets_summary.json",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection.csv",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection_summary.json",
            "artifacts/data/vanderbilt_active_second_hop_targets.csv",
            "artifacts/data/vanderbilt_active_second_hop_targets_summary.json",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection.csv",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection_summary.json",
            "artifacts/data/vanderbilt_active_source_acceptance_packet.csv",
            "artifacts/data/vanderbilt_active_source_acceptance_packet_summary.json",
            "artifacts/data/school_gap_resolution_manifest.csv",
            "artifacts/data/school_gap_resolution_manifest_summary.json",
            "artifacts/data/school_gap_resolution_batches.csv",
            "artifacts/data/school_gap_resolution_batch_summary.json",
            "artifacts/data/school_gap_resolution_batch_packets.csv",
            "artifacts/data/school_gap_resolution_batch_packet_summary.json",
        ],
        evidence={
            "training_summary": training_summary,
            "probe_summary": probe_summary,
            "route_summary": route_summary,
            "second_hop_route_summary": second_hop_route_summary,
            "route_packet_summary": route_packet_summary,
            "parser_extraction_summary": parser_extraction_summary,
            "approved_manifest_summary": approved_manifest_summary,
            "candidate_closure_summary": candidate_closure_summary,
            "scope_mapping_closure_summary": scope_mapping_closure_summary,
            "approved_source_disposition_summary": approved_source_disposition_summary,
            "parser_manual_repair_summary": parser_manual_repair_summary,
            "parser_repair_acceptance_summary": parser_repair_acceptance_summary,
            "active_source_target_summary": active_source_target_summary,
            "active_source_route_summary": active_source_route_summary,
            "active_second_hop_summary": active_second_hop_summary,
            "active_source_acceptance_summary": active_source_acceptance_summary,
            "residual_route_buckets": {
                "no_program_url_rows": no_program_url_rows,
                "roster_text_signal_without_link_rows": roster_text_signal_rows,
                "official_context_only_rows": context_only_rows,
            },
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="coverage_gap_resolution",
        capability_status=(
            "action_queue_open_after_active_source_acceptance"
            if active_source_accepted
            else "action_queue_open_after_parser_repair_acceptance"
            if parser_repair_accepted
            else "action_queue_open_parser_repair_packet_ready_gbrain_gate_required"
            if parser_repair_acceptance_summary.get("approval_effect_requested") == "vanderbilt_parser_repair_incremental_membership_acceptance_approved"
            else "action_queue_open_candidate_source_dispositions_approved_denominator_closure_denied"
            if approved_source_disposition_summary.get("approval_effect") == "vanderbilt_scope_mapping_candidate_source_exclusion_and_mapping_allowed_for_exact_rowset"
            else "action_queue_open_scope_mapping_packet_ready_gbrain_gate_required"
            if scope_mapping_closure_summary.get("rowset_status") == "complete"
            else "action_queue_open_gap_closure_audit_complete"
            if candidate_closure_summary.get("program_representation_status") == "complete"
            else "action_queue_open_incremental_rosters_accepted"
            if membership_accepted
            else "action_queue_open_denominator_only"
        ),
        maturity_level=1 if lane_open else 0,
        evidence_count=int(stats["coverage_rows"]),
        blocker_count=int(stats["unresolved_open_gap_rows"]),
        candidate_count=int(stats["candidate_urls"]),
        automation_status="coverage_queue_materialized_after_warehouse_rebuild",
        route_hop_policy="open denominator rows must become covered rosters, terminal closures, or documented no-public-roster gaps",
        parser_policy="parser outputs must flow through acceptance/reviewer ledgers before person ingestion",
        identity_policy=common_identity,
        freshness_policy="gap status expires when source hash, route candidate, or denominator row changes",
        recommended_next_action=(
            "keep the 146 remaining Vanderbilt denominator gaps open until explicitly covered or closed; next work residual source-candidate probes and broad-source-discovery rows"
            if active_source_accepted
            else "keep the 147 remaining Vanderbilt denominator gaps open until explicitly covered or closed; next work the 82 source-candidate probes and 65 broad-source-discovery rows"
            if parser_repair_accepted
            else "resolve the exact Vanderbilt parser-repair GBrain packet; keep all denominator gaps open until explicitly closed or covered"
            if parser_repair_acceptance_summary.get("approval_effect_requested") == "vanderbilt_parser_repair_incremental_membership_acceptance_approved"
            else "keep all 155 Vanderbilt denominator gaps open; drain parser/manual repair and source-discovery lanes after approved source dispositions"
            if approved_source_disposition_summary.get("approval_effect") == "vanderbilt_scope_mapping_candidate_source_exclusion_and_mapping_allowed_for_exact_rowset"
            else "submit or resolve the exact Vanderbilt scope/mapping closure packet before any denominator status mutation"
            if scope_mapping_closure_summary.get("rowset_status") == "complete"
            else "work Vanderbilt closure-audit buckets; denominator closure and school verification still require later exact GBrain approval"
            if candidate_closure_summary.get("program_representation_status") == "complete"
            else "drain remaining Vanderbilt source/route/closure action queue after exact membership acceptance"
            if membership_accepted
            else "use official-program action queue to batch Vanderbilt route/source probes"
        ),
        target_artifacts=[
            "artifacts/data/official_program_coverage_action_queue.csv",
            "artifacts/data/official_program_coverage_dossiers.csv",
            "artifacts/data/vanderbilt_candidate_closure_audit.csv",
            "artifacts/data/vanderbilt_candidate_closure_summary.json",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet.csv",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet_summary.json",
            "artifacts/data/vanderbilt_approved_candidate_source_dispositions.csv",
            "artifacts/data/vanderbilt_approved_candidate_source_disposition_summary.json",
            "artifacts/data/vanderbilt_parser_manual_repair_probe.csv",
            "artifacts/data/vanderbilt_parser_manual_repair_summary.json",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet.csv",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet_summary.json",
            "artifacts/data/vanderbilt_active_source_candidate_targets.csv",
            "artifacts/data/vanderbilt_active_source_candidate_targets_summary.json",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection.csv",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection_summary.json",
            "artifacts/data/vanderbilt_active_second_hop_targets.csv",
            "artifacts/data/vanderbilt_active_second_hop_targets_summary.json",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection.csv",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection_summary.json",
            "artifacts/data/vanderbilt_active_source_acceptance_packet.csv",
            "artifacts/data/vanderbilt_active_source_acceptance_packet_summary.json",
        ],
        evidence={
            "coverage": stats,
            "candidate_closure_summary": candidate_closure_summary,
            "scope_mapping_closure_summary": scope_mapping_closure_summary,
            "approved_source_disposition_summary": approved_source_disposition_summary,
            "parser_manual_repair_summary": parser_manual_repair_summary,
            "parser_repair_acceptance_summary": parser_repair_acceptance_summary,
            "active_source_target_summary": active_source_target_summary,
            "active_source_route_summary": active_source_route_summary,
            "active_second_hop_summary": active_second_hop_summary,
            "active_source_acceptance_summary": active_source_acceptance_summary,
            "gap_resolution_manifest_summary": gap_resolution_summary,
            "gap_resolution_batch_summary": gap_resolution_batch_summary,
            "gap_resolution_batch_packet_summary": gap_resolution_batch_packet_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="identity_normalization",
        capability_status="membership_scoped_identity_rows_loaded_unique_collapse_blocked" if membership_accepted else "not_started_no_vanderbilt_people",
        maturity_level=3 if membership_accepted else (1 if lane_open else 0),
        evidence_count=int(training_summary.get("accepted_vanderbilt_parser_ready_membership_rows") or 0),
        blocker_count=int(training_summary.get("accepted_vanderbilt_duplicate_scope_counts", {}).get("shared_source_name_across_multiple_denominator_rows", 0)) if isinstance(training_summary.get("accepted_vanderbilt_duplicate_scope_counts"), dict) else 0,
        candidate_count=int(training_summary.get("accepted_vanderbilt_candidate_person_keys") or 0),
        automation_status="membership_scoped_loader_preserves_candidate_person_key" if membership_accepted else "not_applicable_until_roster_capture",
        route_hop_policy="not_applicable",
        parser_policy=(
            "accepted rows are membership observations with candidate_person_key retained for later normalization"
            if membership_accepted
            else "no person rows exist for Vanderbilt in this lane-opening packet"
        ),
        identity_policy=common_identity,
        freshness_policy="identity rules activate after parser-ready roster evidence exists",
        recommended_next_action=(
            "build downstream identity-normalization review for shared-source Vanderbilt rows before any unique-person merge"
            if membership_accepted
            else "preserve denominator/source facts only until current roster evidence is captured"
        ),
        target_artifacts=[
            "artifacts/data/vanderbilt_training_summary.json",
            "artifacts/data/vanderbilt_training_people.csv",
            "artifacts/data/vanderbilt_approved_parser_ready_manifest_summary.json",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet_summary.json",
            "artifacts/data/vanderbilt_active_source_acceptance_packet_summary.json",
        ],
        evidence={
            "training_summary": training_summary,
            "approved_manifest_summary": approved_manifest_summary,
            "parser_repair_acceptance_summary": parser_repair_acceptance_summary,
            "active_source_acceptance_summary": active_source_acceptance_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="gbrain_verification",
        capability_status=(
            "vanderbilt_membership_acceptance_approved_school_not_verified"
            if membership_accepted
            else "vanderbilt_primary_lane_opening_approved_school_not_verified"
            if lane_open
            else "not_submitted"
        ),
        maturity_level=1 if lane_open else 0,
        evidence_count=len(gbrain.get("attempts", [])) if lane_open else 0,
        blocker_count=1,
        candidate_count=0,
        automation_status="http_mcp_query_and_think_available",
        route_hop_policy="school verification requires roster-route/action gaps closed or explicitly justified",
        parser_policy="school dossier must separate denominator rows from accepted people",
        identity_policy=common_identity,
        freshness_policy="submit a fresh Vanderbilt readiness dossier after route probes, roster capture, and queue closure",
        recommended_next_action="do not request Vanderbilt school verification until denominator and roster-route gaps are resolved",
        target_artifacts=[
            "artifacts/data/gbrain_consultation_ledger.json",
            "artifacts/data/vanderbilt_training_summary.json",
        ],
        evidence={"approval_status": approval_status, "latest_advisory_summary": gbrain.get("latest_advisory_summary", {})},
        generated_at=generated_at,
    ))
    return rows


def build_stanford_rows(conn: sqlite3.Connection, generated_at: str, target: dict) -> list[dict[str, str]]:
    school_key = target.get("school_key", "brimr_2024_school_007")
    school_name = target.get("school_name", "STANFORD UNIVERSITY SCH OF MEDICINE")
    sponsoring = "Stanford Health Care / Stanford University Medical Center"
    manifest = read_csv(ARTIFACTS / "top50_next_school_discovery_manifest.csv")
    manifest = [row for row in manifest if row.get("school_name") == school_name]
    probe_summary = read_json(ARTIFACTS / "stanford_program_page_probe_summary.json", {})
    source_candidates = read_csv(ARTIFACTS / "stanford_source_candidates.csv")
    route_summary = read_json(ARTIFACTS / "stanford_roster_route_inspection_summary.json", {})
    parser_summary = read_json(ARTIFACTS / "stanford_parser_ready_packet_summary.json", {})
    parser_disposition_summary = read_json(ARTIFACTS / "stanford_parser_review_disposition_packet_summary.json", {})
    name_quality_summary = read_json(ARTIFACTS / "stanford_name_quality_acceptance_packet_summary.json", {})
    shared_summary = read_json(ARTIFACTS / "stanford_shared_source_crosswalk_packet_summary.json", {})
    shared_residual_summary = read_json(ARTIFACTS / "stanford_shared_source_residual_disposition_packet_summary.json", {})
    unsupported_label_summary = read_json(ARTIFACTS / "stanford_shared_source_unsupported_label_packet_summary.json", {})
    lifecycle_identity_summary = read_json(ARTIFACTS / "stanford_lifecycle_identity_readiness_packet_summary.json", {})
    radonc_summary = read_json(ARTIFACTS / "stanford_radiation_oncology_scope_packet_summary.json", {})
    repair_summary = read_json(ARTIFACTS / "stanford_program_url_repair_probe_summary.json", {})
    browser_repair_summary = read_json(ARTIFACTS / "stanford_stale_url_browser_repair_probe_summary.json", {})
    stale_disposition_summary = read_json(ARTIFACTS / "stanford_stale_url_repair_disposition_packet_summary.json", {})
    stale_route_map_summary = read_json(ARTIFACTS / "stanford_stale_url_route_map_summary.json", {})
    stale_current_roster_acceptance_summary = read_json(ARTIFACTS / "stanford_stale_url_current_roster_acceptance_packet_summary.json", {})
    stale_second_hop_summary = read_json(ARTIFACTS / "stanford_stale_url_second_hop_inspection_summary.json", {})
    stale_second_hop_acceptance_summary = read_json(ARTIFACTS / "stanford_stale_url_second_hop_acceptance_packet_summary.json", {})
    stale_related_scope_summary = read_json(ARTIFACTS / "stanford_stale_url_related_scope_packet_summary.json", {})
    stale_noop_closure_summary = read_json(ARTIFACTS / "stanford_stale_url_noop_closure_packet_summary.json", {})
    pathology_pdf_summary = read_json(ARTIFACTS / "stanford_pathology_pdf_acceptance_packet_summary.json", {})
    neuro_residency_summary = read_json(ARTIFACTS / "stanford_neuro_residency_acceptance_packet_summary.json", {})
    nuclear_medicine_summary = read_json(ARTIFACTS / "stanford_nuclear_medicine_acceptance_packet_summary.json", {})
    nuclear_radiology_fellow_summary = read_json(ARTIFACTS / "stanford_nuclear_radiology_fellow_acceptance_packet_summary.json", {})
    training_summary = read_json(ARTIFACTS / "stanford_training_summary.json", {})
    gap_resolution_summary = read_json(ARTIFACTS / "school_gap_resolution_manifest_summary.json", {})
    gap_resolution_batch_summary = read_json(ARTIFACTS / "school_gap_resolution_batch_summary.json", {})
    gap_resolution_batch_packet_summary = read_json(ARTIFACTS / "school_gap_resolution_batch_packet_summary.json", {})
    gbrain = read_json(ARTIFACTS / "gbrain_consultation_ledger.json", {})
    accepted_programs = set((training_summary.get("program_counts") or {}).keys())
    denominator_programs = {row.get("program_name", "") for row in manifest if row.get("program_name")}
    covered_programs = denominator_programs & accepted_programs
    open_gap_rows = max(0, len(denominator_programs) - len(covered_programs))
    route_blockers = int(route_summary.get("scope_mismatch_rows") or 0) + int(route_summary.get("second_hop_route_candidate_rows") or 0)
    original_parser_blockers = int(parser_summary.get("review_required_candidate_rows") or 0) + int(parser_summary.get("blocked_candidate_rows") or 0)
    parser_blockers = original_parser_blockers
    if parser_disposition_summary:
        parser_blockers = int(parser_disposition_summary.get("proposed_incremental_acceptance_rows") or 0)
    if name_quality_summary.get("packet_status") == "approved_exact_gbrain_acceptance" and name_quality_summary.get("gbrain_approval_verified"):
        parser_blockers = max(0, parser_blockers - int(name_quality_summary.get("rows") or 0))
    shared_exclusions = int(shared_summary.get("excluded_rows") or 0)
    shared_residual_rows = int(shared_residual_summary.get("rows") or 0)
    shared_residual_approved = (
        shared_residual_summary.get("packet_status") == "approved_non_mutating_shared_source_residual_disposition_packet"
        and shared_residual_summary.get("gbrain_approval_verified")
    )
    unsupported_label_rows = int(unsupported_label_summary.get("rows") or 0)
    unsupported_label_approved = (
        unsupported_label_summary.get("packet_status") == "approved_non_mutating_shared_source_unsupported_label_packet"
        and unsupported_label_summary.get("gbrain_approval_verified")
    )
    approved_shared_disposition_rows = (
        (shared_residual_rows if shared_residual_approved else 0)
        + (unsupported_label_rows if unsupported_label_approved else 0)
    )
    shared_pending_exclusions = max(0, shared_exclusions - approved_shared_disposition_rows)
    radonc_exclusions = int(radonc_summary.get("excluded_rows") or 0)
    stale_url_rows = int(repair_summary.get("stale_program_rows") or 0)
    stale_disposition_approved = (
        stale_disposition_summary.get("packet_status") == "approved_non_mutating_disposition"
        and stale_disposition_summary.get("gbrain_approval_verified")
    )
    stale_pending_disposition_rows = 0 if stale_disposition_approved else stale_url_rows
    stale_related_scope_approved = (
        stale_related_scope_summary.get("packet_status") == "approved_non_mutating_related_scope_packet"
        and stale_related_scope_summary.get("gbrain_approval_verified")
    )
    stale_noop_closure_approved = (
        stale_noop_closure_summary.get("packet_status") == "approved_non_mutating_noop_closure_packet"
        and stale_noop_closure_summary.get("gbrain_approval_verified")
    )
    pathology_pdf_approved = (
        pathology_pdf_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and pathology_pdf_summary.get("gbrain_approval_verified")
    )
    neuro_residency_approved = (
        neuro_residency_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and neuro_residency_summary.get("gbrain_approval_verified")
    )
    nuclear_medicine_approved = (
        nuclear_medicine_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and nuclear_medicine_summary.get("gbrain_approval_verified")
    )
    nuclear_radiology_fellow_approved = (
        nuclear_radiology_fellow_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and nuclear_radiology_fellow_summary.get("gbrain_approval_verified")
    )
    lifecycle_identity_approved = (
        lifecycle_identity_summary.get("packet_status") == "approved_non_mutating_lifecycle_identity_readiness_contract"
        and lifecycle_identity_summary.get("gbrain_approval_verified")
    )
    lifecycle_identity_blockers = (
        1
        + (1 if int(lifecycle_identity_summary.get("stanford_lifecycle_contract_coverage_gap_rows") or 0) else 0)
        + (1 if int(lifecycle_identity_summary.get("stanford_lifecycle_institution_mismatch_rows") or 0) else 0)
    )
    lifecycle_identity_repair_required = bool(lifecycle_identity_summary.get("lifecycle_artifact_repair_required"))
    if lifecycle_identity_approved:
        common_identity = (
            "Preserve membership-scoped Stanford person rows until a later identity-resolution lane has source-backed "
            "same-person evidence and explicit GBrain approval. The approved non-mutating lifecycle/identity contract "
            "keeps identity collapse, training-state mutation, and school verification blocked while lifecycle coverage "
            "and institution-scope defects are repaired."
        )
    else:
        common_identity = (
            "Preserve membership-scoped Stanford person rows until a later identity-resolution lane has source-backed "
            "same-person evidence and explicit GBrain approval."
        )
    rows: list[dict[str, str]] = []
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="target_registry",
        capability_status="materialized_top50_target",
        maturity_level=3,
        evidence_count=1,
        blocker_count=0,
        candidate_count=0,
        automation_status="scripted_from_brimr_workbook",
        route_hop_policy="not_applicable",
        parser_policy="not_applicable",
        identity_policy="canonical school target remains separate from Stanford GME sponsoring-institution string",
        freshness_policy="refresh when BRIMR target basis changes or user/GBrain changes top-50 definition",
        recommended_next_action="keep Stanford as the current opened but unverified BRIMR target lane",
        target_artifacts=["artifacts/data/top50_medical_school_targets.json"],
        evidence={"target_rank": target.get("target_rank"), "target_basis": target.get("target_basis")},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="denominator_discovery",
        capability_status="official_gme_index_materialized_open_gaps",
        maturity_level=3,
        evidence_count=len(manifest),
        blocker_count=open_gap_rows,
        candidate_count=len(denominator_programs),
        automation_status="scripted_official_gme_index_parser",
        route_hop_policy="official Stanford GME program index seeds denominator candidates; stale program URLs require separate repair acceptance",
        parser_policy="denominator rows do not create people or closures without later exact packets",
        identity_policy=common_identity,
        freshness_policy="refresh official GME index and source hashes before any school-verification request",
        recommended_next_action=f"close or cover the {open_gap_rows} open denominator program rows before Stanford school verification",
        target_artifacts=[
            "artifacts/data/top50_next_school_discovery_manifest.csv",
            "artifacts/data/stanford_program_page_probe.csv",
            "artifacts/data/stanford_program_url_repair_probe.csv",
            "artifacts/data/stanford_stale_url_browser_repair_probe.csv",
            "artifacts/data/stanford_stale_url_repair_disposition_packet.csv",
            "artifacts/data/stanford_stale_url_route_map.csv",
            "artifacts/data/stanford_stale_url_current_roster_acceptance_packet.csv",
            "artifacts/data/stanford_stale_url_second_hop_inspection.csv",
            "artifacts/data/stanford_stale_url_second_hop_acceptance_packet.csv",
            "artifacts/data/stanford_stale_url_related_scope_packet.csv",
            "artifacts/data/stanford_stale_url_noop_closure_packet.csv",
            "artifacts/data/stanford_pathology_pdf_acceptance_packet.csv",
            "artifacts/data/stanford_neuro_residency_acceptance_packet.csv",
            "artifacts/data/stanford_nuclear_medicine_acceptance_packet.csv",
            "artifacts/data/stanford_nuclear_radiology_fellow_acceptance_packet.csv",
        ],
        evidence={
            "denominator_rows": len(manifest),
            "covered_program_rows": len(covered_programs),
            "open_gap_rows": open_gap_rows,
            "probe_summary": probe_summary,
            "repair_summary": repair_summary,
            "browser_repair_summary": browser_repair_summary,
            "stale_url_repair_disposition_summary": stale_disposition_summary,
            "stale_url_route_map_summary": stale_route_map_summary,
            "stale_url_current_roster_acceptance_summary": stale_current_roster_acceptance_summary,
            "stale_url_second_hop_inspection_summary": stale_second_hop_summary,
            "stale_url_second_hop_acceptance_summary": stale_second_hop_acceptance_summary,
            "stale_url_related_scope_summary": stale_related_scope_summary,
            "stale_url_noop_closure_summary": stale_noop_closure_summary,
            "pathology_pdf_acceptance_summary": pathology_pdf_summary,
            "neuro_residency_acceptance_summary": neuro_residency_summary,
            "nuclear_medicine_acceptance_summary": nuclear_medicine_summary,
            "nuclear_radiology_fellow_acceptance_summary": nuclear_radiology_fellow_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="route_inspection",
        capability_status="headed_route_inspection_done_with_residual_blockers",
        maturity_level=3,
        evidence_count=int(route_summary.get("rows") or 0),
        blocker_count=route_blockers,
        candidate_count=len(source_candidates),
        automation_status="scripted_first_hop_and_headed_second_hop_inspection",
        route_hop_policy="first-hop roster links and headed second-hop routes are discovery evidence only until packetized",
        parser_policy="person structures are parser candidates, not roster truth, until scoped and approved",
        identity_policy=common_identity,
        freshness_policy="rerun route inspection when the denominator manifest, URL repairs, or program pages change",
        recommended_next_action="turn residual route buckets into exact source-repair, exclusion, or parser packets",
        target_artifacts=[
            "artifacts/data/stanford_source_candidates.csv",
            "artifacts/data/stanford_roster_route_inspection.csv",
            "artifacts/data/stanford_roster_route_inspection_summary.json",
        ],
        evidence={"route_summary": route_summary},
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="official_roster_capture",
        capability_status="incremental_exact_gbrain_approved_membership_rows_loaded",
        maturity_level=3,
        evidence_count=int(training_summary.get("accepted_membership_observations") or 0),
        blocker_count=parser_blockers + shared_pending_exclusions + radonc_exclusions,
        candidate_count=int(parser_summary.get("candidate_rows") or 0) + int(shared_summary.get("rows") or 0) + int(radonc_summary.get("rows") or 0),
        automation_status="packetized_parser_and_crosswalk_loaders",
        route_hop_policy="only approved roster/crosswalk/source-repair packets can create membership observations",
        parser_policy="fail-closed rowset hashes gate every accepted Stanford membership subset",
        identity_policy=common_identity,
        freshness_policy="approved manifests are preserved; live-source drift must be reviewed before deletion or state mutation",
        recommended_next_action="keep residual parser/shared/RadOnc exclusions explicit while working denominator gaps",
        target_artifacts=[
            "artifacts/data/stanford_training_people.csv",
            "artifacts/data/stanford_training_summary.json",
            "artifacts/data/stanford_parser_ready_extraction_candidates.csv",
            "artifacts/data/stanford_parser_review_disposition_packet.csv",
            "artifacts/data/stanford_name_quality_acceptance_packet.csv",
            "artifacts/data/stanford_stale_url_current_roster_acceptance_packet.csv",
            "artifacts/data/stanford_stale_url_second_hop_acceptance_packet.csv",
            "artifacts/data/stanford_pathology_pdf_acceptance_packet.csv",
            "artifacts/data/stanford_neuro_residency_acceptance_packet.csv",
            "artifacts/data/stanford_nuclear_medicine_acceptance_packet.csv",
            "artifacts/data/stanford_nuclear_radiology_fellow_acceptance_packet.csv",
            "artifacts/data/stanford_stale_url_related_scope_packet.csv",
            "artifacts/data/stanford_stale_url_noop_closure_packet.csv",
            "artifacts/data/stanford_shared_source_crosswalk_packet.csv",
            "artifacts/data/stanford_shared_source_residual_disposition_packet.csv",
            "artifacts/data/stanford_shared_source_unsupported_label_packet.csv",
            "artifacts/data/stanford_lifecycle_identity_readiness_packet.csv",
            "artifacts/data/stanford_radiation_oncology_scope_packet.csv",
        ],
        evidence={
            "training_summary": training_summary,
            "parser_summary": parser_summary,
            "parser_disposition_summary": parser_disposition_summary,
            "name_quality_acceptance_summary": name_quality_summary,
            "stale_url_current_roster_acceptance_summary": stale_current_roster_acceptance_summary,
            "stale_url_second_hop_acceptance_summary": stale_second_hop_acceptance_summary,
            "pathology_pdf_acceptance_summary": pathology_pdf_summary,
            "neuro_residency_acceptance_summary": neuro_residency_summary,
            "nuclear_medicine_acceptance_summary": nuclear_medicine_summary,
            "nuclear_radiology_fellow_acceptance_summary": nuclear_radiology_fellow_summary,
            "stale_url_related_scope_summary": stale_related_scope_summary,
            "stale_url_noop_closure_summary": stale_noop_closure_summary,
            "shared_summary": shared_summary,
            "shared_source_residual_disposition_summary": shared_residual_summary,
            "shared_source_unsupported_label_disposition_summary": unsupported_label_summary,
            "lifecycle_identity_readiness_summary": lifecycle_identity_summary,
            "shared_pending_exclusion_rows_after_residual_and_unsupported_label_disposition": shared_pending_exclusions,
            "radonc_summary": radonc_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="coverage_gap_resolution",
        capability_status="custom_gap_surface_open_not_denominator_closed",
        maturity_level=2,
        evidence_count=open_gap_rows,
        blocker_count=open_gap_rows,
        candidate_count=stale_pending_disposition_rows + shared_pending_exclusions + parser_blockers,
        automation_status="custom_stanford_gap_packets_partial",
        route_hop_policy=(
            "approved stale URL dispositions are route-mapped; exact second-hop, Pathology PDF, Neurology/Neurosurgery residency, Nuclear Medicine residency, and Nuclear Radiology fellow acceptance are loaded; "
            "related-scope disposition, no-op/crosswalk closure, shared-source residual disposition, and unsupported-label disposition are approved as non-mutating evidence; remaining "
            "custom Stanford gaps require exact packets before closure"
            if stale_related_scope_approved and stale_noop_closure_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved and shared_residual_approved and unsupported_label_approved
            else
            "approved stale URL dispositions are route-mapped; exact second-hop, Pathology PDF, Neurology/Neurosurgery residency, Nuclear Medicine residency, and Nuclear Radiology fellow acceptance are loaded; "
            "related-scope disposition, no-op/crosswalk closure, and shared-source residual disposition are approved as non-mutating evidence; remaining "
            "custom Stanford gaps require exact packets before closure"
            if stale_related_scope_approved and stale_noop_closure_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved and shared_residual_approved
            else
            "approved stale URL dispositions are route-mapped; exact second-hop, Pathology PDF, Neurology/Neurosurgery residency, Nuclear Medicine residency, and Nuclear Radiology fellow acceptance are loaded; "
            "related-scope disposition and no-op/crosswalk closure are approved as non-mutating evidence; remaining "
            "custom Stanford gaps require exact packets before closure"
            if stale_related_scope_approved and stale_noop_closure_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved
            else
            "approved stale URL dispositions are route-mapped; exact second-hop, Pathology PDF, Neurology/Neurosurgery residency, Nuclear Medicine residency, and Nuclear Radiology fellow acceptance are loaded; "
            "related-scope disposition is approved as non-mutating evidence; remaining already-accepted/no-op crosswalk "
            "rows require exact packets before closure"
            if stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved
            else
            "approved stale URL dispositions are route-mapped; exact second-hop, Pathology PDF, Neurology/Neurosurgery residency, and Nuclear Medicine residency acceptance are loaded; "
            "related-scope disposition is approved as non-mutating evidence; remaining already-accepted/no-op crosswalk "
            "rows require exact packets before closure"
            if stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved
            else
            "approved stale URL dispositions are route-mapped; exact second-hop, Pathology PDF, and Neurology/Neurosurgery residency acceptance are loaded; "
            "related-scope disposition is approved as non-mutating evidence; remaining already-accepted/no-op crosswalk "
            "rows require exact packets before closure"
            if stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved
            else
            "approved stale URL dispositions are route-mapped; exact second-hop and Pathology PDF acceptance are loaded; "
            "related-scope disposition is approved as non-mutating evidence; third-hop, no-roster, shared-source, "
            "scope-mismatch, and team-page rows require exact packets before closure"
            if stale_related_scope_approved and pathology_pdf_approved
            else "approved stale URL dispositions are route-mapped; exact second-hop acceptance is loaded; "
            "related-scope disposition is approved as non-mutating evidence; PDF, third-hop, no-roster, "
            "shared-source, scope-mismatch, and team-page rows require exact packets before closure"
            if stale_related_scope_approved
            else "approved stale URL dispositions are route-mapped; exact second-hop acceptance is loaded; related-scope, PDF, third-hop, no-roster, shared-source, scope-mismatch, and team-page rows require exact packets before closure"
        ),
        parser_policy="do not infer current trainees from context/team pages or non-physician training pages",
        identity_policy=common_identity,
        freshness_policy="gap closures expire when official GME index or route evidence changes",
        recommended_next_action=(
            "use the non-mutating school gap-resolution manifest to batch the 129 Stanford denominator gaps; retain approved stale URL, shared-source residual, unsupported-label, and lifecycle/identity evidence before school verification"
            if stale_related_scope_approved and stale_noop_closure_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved and shared_residual_approved and unsupported_label_approved
            else
            "retain approved stale URL and shared-source residual evidence; next drain unsupported labels, source-specific Hand Surgery assignment only if coverage is attempted, and lifecycle/identity readiness before school verification"
            if stale_related_scope_approved and stale_noop_closure_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved and shared_residual_approved
            else
            "move from stale URL second-hop residuals to Hand Surgery assignment, General Surgery team-page exclusion or scope mapping, unsupported labels, and lifecycle/identity readiness before school verification"
            if stale_related_scope_approved and stale_noop_closure_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved
            else
            "packet the remaining stale URL second-hop outputs into already-accepted/no-op crosswalk closure lanes before school verification"
            if stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved
            else
            "packet the remaining stale URL second-hop outputs into already-accepted/no-op crosswalk closure lanes and separately decide the Nuclear Radiology fellow mapping before school verification"
            if stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved
            else
            "packet the remaining stale URL second-hop outputs into already-accepted/no-op crosswalk closure lanes before school verification"
            if stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved
            else
            "packet the remaining stale URL second-hop inspection outputs into third-hop, already-accepted/no-op crosswalk, and no-roster closure lanes before school verification"
            if stale_related_scope_approved and pathology_pdf_approved
            else "packet the remaining stale URL second-hop inspection outputs into PDF parser, third-hop, already-accepted/no-op crosswalk, and no-roster closure lanes before school verification"
            if stale_related_scope_approved
            else "packet the remaining stale URL second-hop inspection outputs into related-scope closure, PDF parser, third-hop, and no-roster closure lanes before school verification"
        ),
        target_artifacts=[
            "artifacts/data/stanford_program_url_repair_probe.csv",
            "artifacts/data/stanford_stale_url_browser_repair_probe.csv",
            "artifacts/data/stanford_stale_url_repair_disposition_packet.csv",
            "artifacts/data/stanford_stale_url_route_map.csv",
            "artifacts/data/stanford_stale_url_current_roster_acceptance_packet.csv",
            "artifacts/data/stanford_stale_url_second_hop_inspection.csv",
            "artifacts/data/stanford_stale_url_second_hop_acceptance_packet.csv",
            "artifacts/data/stanford_pathology_pdf_acceptance_packet.csv",
            "artifacts/data/stanford_neuro_residency_acceptance_packet.csv",
            "artifacts/data/stanford_nuclear_medicine_acceptance_packet.csv",
            "artifacts/data/stanford_nuclear_radiology_fellow_acceptance_packet.csv",
            "artifacts/data/stanford_stale_url_related_scope_packet.csv",
            "artifacts/data/stanford_stale_url_noop_closure_packet.csv",
            "artifacts/data/stanford_name_quality_acceptance_packet.csv",
            "artifacts/data/stanford_shared_source_crosswalk_packet.csv",
            "artifacts/data/stanford_shared_source_residual_disposition_packet.csv",
            "artifacts/data/stanford_shared_source_unsupported_label_packet.csv",
            "artifacts/data/stanford_lifecycle_identity_readiness_packet.csv",
            "artifacts/data/stanford_radiation_oncology_scope_packet.csv",
            "artifacts/data/school_gap_resolution_manifest.csv",
            "artifacts/data/school_gap_resolution_manifest_summary.json",
            "artifacts/data/school_gap_resolution_batches.csv",
            "artifacts/data/school_gap_resolution_batch_summary.json",
            "artifacts/data/school_gap_resolution_batch_packets.csv",
            "artifacts/data/school_gap_resolution_batch_packet_summary.json",
        ],
        evidence={
            "open_gap_rows": open_gap_rows,
            "stale_url_rows": stale_url_rows,
            "stale_url_disposition_approved_rows": int(stale_disposition_summary.get("rows") or 0) if stale_disposition_approved else 0,
            "stale_url_pending_disposition_rows": stale_pending_disposition_rows,
            "stale_url_repair_disposition_summary": stale_disposition_summary,
            "stale_url_route_map_rows": int(stale_route_map_summary.get("rows") or 0),
            "stale_url_route_map_summary": stale_route_map_summary,
            "stale_url_current_roster_acceptance_summary": stale_current_roster_acceptance_summary,
            "stale_url_second_hop_inspection_summary": stale_second_hop_summary,
            "stale_url_second_hop_acceptance_summary": stale_second_hop_acceptance_summary,
            "pathology_pdf_acceptance_summary": pathology_pdf_summary,
            "pathology_pdf_approved_rows": int(pathology_pdf_summary.get("ready_rows") or 0) if pathology_pdf_approved else 0,
            "neuro_residency_acceptance_summary": neuro_residency_summary,
            "neuro_residency_approved_rows": int(neuro_residency_summary.get("rows") or 0) if neuro_residency_approved else 0,
            "nuclear_medicine_acceptance_summary": nuclear_medicine_summary,
            "nuclear_medicine_approved_rows": int(nuclear_medicine_summary.get("rows") or 0) if nuclear_medicine_approved else 0,
            "nuclear_medicine_excluded_related_rows": int(nuclear_medicine_summary.get("excluded_related_rows") or 0),
            "nuclear_radiology_fellow_acceptance_summary": nuclear_radiology_fellow_summary,
            "nuclear_radiology_fellow_approved_rows": int(nuclear_radiology_fellow_summary.get("rows") or 0) if nuclear_radiology_fellow_approved else 0,
            "stale_url_related_scope_summary": stale_related_scope_summary,
            "stale_url_related_scope_approved_rows": int(stale_related_scope_summary.get("rows") or 0) if stale_related_scope_approved else 0,
            "stale_url_noop_closure_summary": stale_noop_closure_summary,
            "stale_url_noop_closure_approved_rows": int(stale_noop_closure_summary.get("rows") or 0) if stale_noop_closure_approved else 0,
            "shared_excluded_rows": shared_exclusions,
            "shared_source_residual_disposition_summary": shared_residual_summary,
            "shared_source_residual_approved_rows": shared_residual_rows if shared_residual_approved else 0,
            "shared_source_unsupported_label_disposition_summary": unsupported_label_summary,
            "shared_source_unsupported_label_approved_rows": unsupported_label_rows if unsupported_label_approved else 0,
            "lifecycle_identity_readiness_summary": lifecycle_identity_summary,
            "shared_pending_exclusion_rows_after_residual_and_unsupported_label_disposition": shared_pending_exclusions,
            "parser_original_review_or_blocked_rows": original_parser_blockers,
            "parser_remaining_acceptance_candidate_rows": parser_blockers,
            "parser_disposition_summary": parser_disposition_summary,
            "name_quality_acceptance_summary": name_quality_summary,
            "radonc_excluded_rows": radonc_exclusions,
            "gap_resolution_manifest_summary": gap_resolution_summary,
            "gap_resolution_batch_summary": gap_resolution_batch_summary,
            "gap_resolution_batch_packet_summary": gap_resolution_batch_packet_summary,
        },
        generated_at=generated_at,
    ))
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="identity_normalization",
        capability_status=(
            "lifecycle_identity_contract_approved_repair_blocked_unique_collapse_blocked"
            if lifecycle_identity_approved
            else "membership_scoped_identity_rows_loaded_unique_collapse_blocked"
        ),
        maturity_level=3,
        evidence_count=int(training_summary.get("accepted_people") or 0),
        blocker_count=lifecycle_identity_blockers if lifecycle_identity_approved else 1,
        candidate_count=int(training_summary.get("accepted_membership_observations") or 0),
        automation_status=(
            "membership_scoped_loader_plus_non_mutating_lifecycle_identity_contract"
            if lifecycle_identity_approved
            else "membership_scoped_loader_preserves_source_row_keys"
        ),
        route_hop_policy="not_applicable",
        parser_policy="accepted rows are membership observations, not a unique-person identity graph",
        identity_policy=common_identity,
        freshness_policy=(
            "repair lifecycle artifact coverage and institution propagation before any Stanford school-verification request"
            if lifecycle_identity_approved
            else "run identity-review packets only after school denominator truth is stable"
        ),
        recommended_next_action=(
            (
                "retain approved repaired lifecycle/identity contract with full Stanford lifecycle coverage; keep unique-person collapse unapproved"
                if not lifecycle_identity_repair_required
                else (
                    "repair lifecycle artifact coverage for "
                    f"{int(lifecycle_identity_summary.get('stanford_lifecycle_contract_coverage_gap_rows') or 0)} missing Stanford rows "
                    "and institution propagation for "
                    f"{int(lifecycle_identity_summary.get('stanford_lifecycle_institution_mismatch_rows') or 0)} rows; keep unique-person collapse unapproved"
                )
            )
            if lifecycle_identity_approved
            else "keep unique-person collapse unapproved until Stanford school verification is much closer"
        ),
        target_artifacts=[
            "artifacts/data/stanford_training_people.csv",
            "artifacts/data/stanford_training_summary.json",
            "artifacts/data/stanford_lifecycle_identity_readiness_packet.csv",
            "artifacts/data/stanford_lifecycle_identity_readiness_packet_summary.json",
        ],
        evidence={"training_summary": training_summary, "lifecycle_identity_readiness_summary": lifecycle_identity_summary},
        generated_at=generated_at,
    ))
    stanford_gbrain_status = school_gbrain_status(gbrain, school_name)
    stanford_school_verified = stanford_gbrain_status == "stanford_school_verified_next_lane_approved"
    rows.append(row(
        school_key=school_key,
        school_name=school_name,
        sponsoring_institution=sponsoring,
        capability_lane="gbrain_verification",
        capability_status=stanford_gbrain_status if stanford_school_verified else "lane_opened_school_not_verified",
        maturity_level=4 if stanford_school_verified else 1,
        evidence_count=len(gbrain.get("attempts", [])),
        blocker_count=0 if stanford_school_verified else 1,
        candidate_count=0,
        automation_status="http_mcp_query_and_think_available",
        route_hop_policy="school verification requires closed/covered denominator and explicit residual blocker accounting",
        parser_policy="accepted person subsets do not imply school verification",
        identity_policy=common_identity,
        freshness_policy=(
            "refresh Stanford readiness and resubmit if source hashes, accepted rowsets, or gap-disposition evidence changes"
            if stanford_school_verified
            else "submit a fresh Stanford readiness dossier only after open gaps are closed or justified"
        ),
        recommended_next_action=(
            "retain Stanford as school-verified under the approved non-mutating honesty-about-gaps boundary; move to the next GBrain-approved school lane"
            if stanford_school_verified
            else "do not request Stanford school verification yet; use this dossier to drive remaining gap packets"
        ),
        target_artifacts=[
            "artifacts/data/gbrain_consultation_ledger.json",
            "artifacts/data/school_readiness_dossiers.csv",
            "artifacts/data/stanford_school_readiness_packet_summary.json",
        ],
        evidence={"approval_status": stanford_gbrain_status, "latest_advisory_summary": gbrain.get("latest_advisory_summary", {})},
        generated_at=generated_at,
    ))
    return rows


def insert_sqlite(rows: list[dict[str, str]]) -> None:
    if not DB.exists():
        return
    conn = sqlite3.connect(DB)
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS school_capability_manifest (
              capability_key TEXT PRIMARY KEY,
              school_key TEXT,
              school_name TEXT NOT NULL,
              sponsoring_institution TEXT NOT NULL,
              capability_lane TEXT NOT NULL,
              capability_status TEXT NOT NULL,
              maturity_level INTEGER NOT NULL DEFAULT 0,
              maturity_level_definition TEXT NOT NULL,
              evidence_count INTEGER NOT NULL DEFAULT 0,
              blocker_count INTEGER NOT NULL DEFAULT 0,
              candidate_count INTEGER NOT NULL DEFAULT 0,
              automation_status TEXT NOT NULL,
              route_hop_policy TEXT NOT NULL,
              parser_policy TEXT NOT NULL,
              identity_policy TEXT NOT NULL,
              freshness_policy TEXT NOT NULL,
              recommended_next_action TEXT NOT NULL,
              target_artifacts_json TEXT NOT NULL,
              evidence_json TEXT NOT NULL,
              generated_at TEXT NOT NULL
            )
            """
        )
        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(school_capability_manifest)")}
        if "maturity_level_definition" not in existing_columns:
            conn.execute(
                "ALTER TABLE school_capability_manifest "
                "ADD COLUMN maturity_level_definition TEXT NOT NULL DEFAULT ''"
            )
        conn.execute("DELETE FROM school_capability_manifest")
        placeholders = ", ".join(":" + field for field in FIELDS)
        conn.executemany(
            f"INSERT INTO school_capability_manifest ({', '.join(FIELDS)}) VALUES ({placeholders})",
            rows,
        )
    conn.close()


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB)
    targets = target_by_name()
    rows: list[dict[str, str]] = []
    rows.extend(build_hopkins_rows(conn, generated_at, targets.get("JOHNS HOPKINS UNIVERSITY SCH OF MEDICINE", {})))
    rows.extend(build_ucsf_rows(conn, generated_at, targets.get("UNIV OF CALIFORNIA SAN FRAN SCH OF MED", {})))
    rows.extend(build_washu_rows(conn, generated_at, targets.get("WASHINGTON UNIVERSITY SCH OF MEDICINE", {})))
    rows.extend(build_yale_rows(conn, generated_at, targets.get("YALE UNIVERSITY SCH OF MEDICINE", {})))
    rows.extend(build_penn_rows(conn, generated_at, targets.get("UNIV OF PENNSYLVANIA SCH OF MEDICINE", {})))
    rows.extend(build_vanderbilt_rows(conn, generated_at, targets.get("VANDERBILT UNIVERSITY SCH OF MEDICINE", {})))
    rows.extend(build_stanford_rows(conn, generated_at, targets.get("STANFORD UNIVERSITY SCH OF MEDICINE", {})))
    conn.close()

    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "generated_at": generated_at,
        "maturity_level_definitions": MATURITY_LEVELS,
        "policy": (
            "Capability manifests are non-mutating school-level operating contracts. "
            "They define source families, parser posture, route-hop policy, identity gates, freshness expectations, "
            "and next actions before a school can be submitted for GBrain verification."
        ),
        "rows": rows,
    }
    JSON_OUT.write_text(dumps(payload) + "\n", encoding="utf-8")
    summary = {
        "generated_at": generated_at,
        "manifest_rows": len(rows),
        "by_school": dict(Counter(row["school_name"] for row in rows)),
        "by_capability_status": dict(Counter(row["capability_status"] for row in rows)),
        "by_capability_lane": dict(Counter(row["capability_lane"] for row in rows)),
        "open_blocker_rows": sum(1 for row in rows if int(row["blocker_count"]) > 0),
        "maturity_level_definitions": MATURITY_LEVELS,
        "policy": payload["policy"],
    }
    SUMMARY_OUT.write_text(dumps(summary) + "\n", encoding="utf-8")
    insert_sqlite(rows)
    print(dumps({"school_capability_manifest": len(rows), "open_blocker_rows": summary["open_blocker_rows"]}))


if __name__ == "__main__":
    main()
