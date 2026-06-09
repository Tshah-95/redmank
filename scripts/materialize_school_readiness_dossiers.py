#!/usr/bin/env python3
"""Materialize school-level readiness dossiers for GBrain verification."""

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
CSV_OUT = ARTIFACTS / "school_readiness_dossiers.csv"
JSON_OUT = ARTIFACTS / "school_readiness_dossiers.json"
SUMMARY_OUT = ARTIFACTS / "school_readiness_dossier_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "dossier_key",
    "school_key",
    "school_name",
    "sponsoring_institution",
    "dossier_status",
    "gbrain_approval_status",
    "verification_posture",
    "manifest_rows",
    "open_manifest_blocker_rows",
    "min_maturity_level",
    "coverage_program_rows",
    "covered_program_rows",
    "open_gap_rows",
    "action_queue_rows",
    "reproducibility_status",
    "warehouse_people",
    "warehouse_training_events",
    "required_next_action",
    "included_artifacts_json",
    "blocker_summary_json",
    "evidence_json",
    "generated_at",
]

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


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sqlite_scalar(conn: sqlite3.Connection, query: str, params: tuple = ()) -> int:
    row = conn.execute(query, params).fetchone()
    return int(row[0] or 0) if row else 0


def sqlite_rows(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query, params)]


def is_covered_status(status: str | None) -> bool:
    return bool(status and status.startswith("covered_current_roster"))


def target_lookup() -> dict[str, dict]:
    payload = read_json(ARTIFACTS / "top50_medical_school_targets.json", {"targets": []})
    return {row.get("school_name", ""): row for row in payload.get("targets", [])}


def school_stats(conn: sqlite3.Connection, sponsoring_institution: str) -> dict:
    coverage = sqlite_rows(
        conn,
        """
        SELECT a.coverage_status, a.captured_people_count, u.official_program_key
        FROM official_program_coverage_audit a
        JOIN official_program_universe u ON u.official_program_key = a.official_program_key
        WHERE u.sponsoring_institution = ?
        """,
        (sponsoring_institution,),
    )
    queue = sqlite_rows(
        conn,
        """
        SELECT q.action_lane, q.blocker_status
        FROM official_program_coverage_action_queue q
        JOIN official_program_universe u ON u.official_program_key = q.official_program_key
        WHERE u.sponsoring_institution = ?
        """,
        (sponsoring_institution,),
    )
    closures = sqlite_rows(
        conn,
        """
        SELECT c.official_program_key, c.closure_status
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
    unresolved_open_gaps = sum(
        1
        for row in coverage
        if not is_covered_status(row.get("coverage_status"))
        and row.get("official_program_key") not in terminal_closure_keys
    )
    return {
        "coverage_program_rows": len(coverage),
        "covered_program_rows": sum(1 for row in coverage if is_covered_status(row.get("coverage_status"))),
        "raw_not_covered_program_rows": sum(1 for row in coverage if not is_covered_status(row.get("coverage_status"))),
        "open_gap_rows": unresolved_open_gaps,
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
        "coverage_status": dict(Counter(row.get("coverage_status") for row in coverage)),
        "action_queue_rows": len(queue),
        "queue_lanes": dict(Counter(row.get("action_lane") for row in queue)),
        "queue_blockers": dict(Counter(row.get("blocker_status") for row in queue)),
    }


def gbrain_verifies_school(gbrain_status: str, gbrain: dict, school_name: str) -> bool:
    """Return whether the ledger preserves a school-level GBrain verification."""
    if gbrain_status == "hopkins_school_verified_next_lane_approved" and "HOPKINS" in school_name:
        return True
    if gbrain_status == "ucsf_school_verified_next_lane_approved" and (
        "HOPKINS" in school_name or "CALIFORNIA SAN FRAN" in school_name
    ):
        return True
    if gbrain_status == "washu_school_verified_next_lane_approved" and (
        "HOPKINS" in school_name or "CALIFORNIA SAN FRAN" in school_name or "WASHINGTON UNIVERSITY" in school_name
    ):
        return True
    if gbrain_status in {
        "yale_school_verified_next_lane_approved",
        "yale_school_verified_after_cardiac_surgery_delta_approved",
    } and (
        "HOPKINS" in school_name
        or "CALIFORNIA SAN FRAN" in school_name
        or "WASHINGTON UNIVERSITY" in school_name
        or "YALE" in school_name
    ):
        return True
    if gbrain_status == "vanderbilt_primary_lane_opening_approved_school_not_verified" and (
        "HOPKINS" in school_name
        or "CALIFORNIA SAN FRAN" in school_name
        or "WASHINGTON UNIVERSITY" in school_name
    ):
        return True
    if gbrain_status == "stanford_school_verified_next_lane_approved" and (
        "HOPKINS" in school_name
        or "CALIFORNIA SAN FRAN" in school_name
        or "WASHINGTON UNIVERSITY" in school_name
        or "YALE" in school_name
        or "STANFORD" in school_name
    ):
        return True

    advisory = gbrain.get("latest_advisory_summary") or {}
    approved_scope = " ".join(
        str(advisory.get(field) or "")
        for field in ("approved_scope", "current_next_school_strategy", "latest_execution_order")
    ).lower()
    if "hopkins, ucsf, and washu school-level readiness" in approved_scope:
        return "HOPKINS" in school_name or "CALIFORNIA SAN FRAN" in school_name or "WASHINGTON UNIVERSITY" in school_name
    return False


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


def build_dossier(
    *,
    conn: sqlite3.Connection,
    school_key: str,
    school_name: str,
    sponsoring_institution: str,
    generated_at: str,
    gbrain_status: str,
    gbrain: dict,
    manifest_rows: list[dict[str, str]],
    reproducibility: dict,
) -> dict[str, str]:
    stats = school_stats(conn, sponsoring_institution)
    school_manifest = [row for row in manifest_rows if row["school_name"] == school_name]
    open_manifest_blockers = sum(
        1
        for row in school_manifest
        if row.get("capability_lane") != "gbrain_verification"
        and int(row.get("blocker_count") or 0) > 0
    )
    min_maturity = min((int(row.get("maturity_level") or 0) for row in school_manifest), default=0)
    repro_ok = (
        int(reproducibility.get("required_missing_artifacts") or 0) == 0
        and int(reproducibility.get("row_count_mismatch_rows") or 0) == 0
    )
    if gbrain_status == "conditional_strategy_approval_hopkins_not_verified" and stats["open_gap_rows"] > 0:
        dossier_status = "not_ready_for_gbrain_school_verification"
        verification_posture = "strategy_approved_school_not_verified"
        next_action = "Resolve or explicitly close open coverage and manifest blockers, then resubmit the school dossier through GBrain HTTP MCP."
    elif (
        gbrain_verifies_school(gbrain_status, gbrain, school_name)
    ):
        dossier_status = "gbrain_verified_next_lane_approved"
        verification_posture = "school_verified_by_gbrain"
        next_action = (
            "Move to the next top-50 primary school lane; keep verified schools on scheduled refresh, "
            "closure revalidation, and explicit gap worklists."
        )
    elif stats["open_gap_rows"] == 0 and stats["action_queue_rows"] == 0 and open_manifest_blockers == 0 and repro_ok:
        dossier_status = "ready_for_gbrain_school_verification"
        verification_posture = "ready_to_submit"
        next_action = "Submit dossier through GBrain HTTP MCP for school-level approval."
    else:
        dossier_status = "reference_or_incomplete_dossier"
        verification_posture = "not_submitted"
        next_action = "Complete capability manifest lanes and explicit gap classification before requesting approval."
    if school_name.startswith("UNIV OF PENNSYLVANIA"):
        dossier_status = "reference_corpus_not_current_school_verification_request"
        verification_posture = "reference_only"
        next_action = "Use Penn as calibration evidence; generate a separate Penn readiness dossier only when asking GBrain to verify Penn."
    if "VANDERBILT" in school_name and gbrain_status == "vanderbilt_primary_lane_opening_approved_school_not_verified":
        vanderbilt_probe = read_json(ARTIFACTS / "vanderbilt_program_page_probe_summary.json", {})
        vanderbilt_route = read_json(ARTIFACTS / "vanderbilt_roster_route_inspection_summary.json", {})
        vanderbilt_route_packets = read_json(ARTIFACTS / "vanderbilt_route_review_packet_summary.json", {})
        vanderbilt_parser_extraction = read_json(ARTIFACTS / "vanderbilt_parser_ready_extraction_packet_summary.json", {})
        vanderbilt_training = read_json(ARTIFACTS / "vanderbilt_training_summary.json", {})
        vanderbilt_candidate_closure = read_json(ARTIFACTS / "vanderbilt_candidate_closure_summary.json", {})
        vanderbilt_scope_packet = read_json(ARTIFACTS / "vanderbilt_scope_mapping_closure_packet_summary.json", {})
        vanderbilt_source_dispositions = read_json(ARTIFACTS / "vanderbilt_approved_candidate_source_disposition_summary.json", {})
        vanderbilt_parser_repair_packet = read_json(ARTIFACTS / "vanderbilt_parser_repair_acceptance_packet_summary.json", {})
        vanderbilt_active_source_packet = read_json(ARTIFACTS / "vanderbilt_active_source_acceptance_packet_summary.json", {})
        vanderbilt_active_route_packet = read_json(ARTIFACTS / "vanderbilt_active_source_route_inspection_packet_summary.json", {})
        vanderbilt_parser_manual_35_packet = read_json(ARTIFACTS / "vanderbilt_parser_manual_review_35_packet_summary.json", {})
        vanderbilt_probe_rows = int(vanderbilt_probe.get("probe_rows") or 0)
        vanderbilt_source_candidates = int(vanderbilt_probe.get("source_candidate_rows") or 0)
        vanderbilt_repair_approved_loaded = (
            vanderbilt_training.get("parser_repair_incremental_acceptance_approval_effect")
            == "vanderbilt_parser_repair_incremental_membership_acceptance_approved"
            and int(vanderbilt_training.get("accepted_vanderbilt_parser_repair_membership_rows") or 0)
            == int(vanderbilt_parser_repair_packet.get("rows") or 0)
        )
        vanderbilt_active_source_approved_loaded = (
            vanderbilt_training.get("active_source_incremental_acceptance_approval_effect")
            == "vanderbilt_active_source_neurosurgery_incremental_membership_acceptance_approved"
            and int(vanderbilt_training.get("accepted_vanderbilt_active_source_membership_rows") or 0)
            == int(vanderbilt_active_source_packet.get("rows") or 0)
        )
        dossier_status = "lane_opened_denominator_discovery_incomplete"
        verification_posture = "lane_opened_school_not_verified"
        if vanderbilt_repair_approved_loaded:
            split = (
                f"{int(vanderbilt_training.get('accepted_vanderbilt_base_parser_ready_membership_rows') or 0)} base parser-ready, "
                f"{int(vanderbilt_training.get('accepted_vanderbilt_parser_repair_membership_rows') or 0)} parser-repair"
            )
            if vanderbilt_active_source_approved_loaded:
                split += (
                    f", and {int(vanderbilt_training.get('accepted_vanderbilt_active_source_membership_rows') or 0)} "
                    "active-source Neurosurgery rows"
                )
            next_action = (
                f"Vanderbilt has {int(vanderbilt_training.get('accepted_vanderbilt_parser_ready_membership_rows') or 0)} "
                f"exact GBrain-approved membership observations loaded ({split}). "
                + (
                    f"A {int(vanderbilt_active_route_packet.get('rows') or 0)}-row active-source route-inspection packet is "
                    "GBrain-approved as non-mutating evidence, so those rows are now split into related-scope, exclusion, "
                    "negative-route, second-hop-chain, and third-hop recourse lanes. "
                    if vanderbilt_active_route_packet.get("gbrain_approval_verified")
                    else ""
                )
                + (
                    f"A {int(vanderbilt_parser_manual_35_packet.get('rows') or 0)}-row parser/manual review packet is "
                    "GBrain-approved as non-mutating classification evidence, with zero evidence-ready person rows and "
                    "recourse split into shared/program-scope, manual current-scope, no-current-roster, faculty/leadership, "
                    "and non-current lanes. "
                    if vanderbilt_parser_manual_35_packet.get("gbrain_approval_verified")
                    else ""
                )
                + f"{stats['open_gap_rows']} denominator gaps remain open; drain source-candidate probes and broad source discovery before any "
                "denominator closure, identity collapse, or Vanderbilt school-verification request."
            )
        elif vanderbilt_parser_repair_packet.get("approval_effect_requested") == "vanderbilt_parser_repair_incremental_membership_acceptance_approved":
            next_action = (
                f"Vanderbilt has a {int(vanderbilt_parser_repair_packet.get('rows') or 0)}-row parser-repair acceptance packet "
                f"with rowset hash {vanderbilt_parser_repair_packet.get('rowset_sha256')}. Submit or resolve the exact GBrain decision before "
                "any additional membership ingestion; denominator closure, identity collapse, and school verification remain blocked."
            )
        elif vanderbilt_source_dispositions.get("approval_effect") == "vanderbilt_scope_mapping_candidate_source_exclusion_and_mapping_allowed_for_exact_rowset":
            next_action = (
                f"Vanderbilt has {int(vanderbilt_source_dispositions.get('rows') or 0)} GBrain-approved candidate-source dispositions "
                "with denominator closure explicitly denied. Keep all affected denominator gaps open; next drain parser/manual repair rows, "
                "then official URL/source-discovery and route-probe rows before any Vanderbilt school-verification request."
            )
        elif vanderbilt_scope_packet.get("rowset_status") == "complete":
            next_action = (
                f"Vanderbilt has a {int(vanderbilt_scope_packet.get('rows') or 0)}-row non-mutating scope/mapping closure packet "
                f"with rowset hash {vanderbilt_scope_packet.get('rowset_sha256')}. Submit or resolve the exact GBrain decision before any "
                "denominator closure mutation; if denied or partial, keep the affected Vanderbilt gaps open and continue parser/source work."
            )
        elif vanderbilt_candidate_closure.get("program_representation_status") == "complete":
            next_action = (
                f"Vanderbilt has {int(vanderbilt_training.get('accepted_vanderbilt_parser_ready_membership_rows') or 0)} "
                f"exact GBrain-approved membership observations loaded and {int(vanderbilt_candidate_closure.get('programs_represented') or 0)} "
                "remaining gaps classified in a non-mutating closure audit. Work the classified parser repair, official URL, route-probe, "
                "secondary-source, and manual-scope lanes; do not close denominator rows or request school verification without a later exact GBrain approval."
            )
        elif vanderbilt_training.get("incremental_acceptance_status") == "accepted_exact_gbrain_approved_manifest":
            next_action = (
                f"Vanderbilt has {int(vanderbilt_training.get('accepted_vanderbilt_parser_ready_membership_rows') or 0)} "
                "exact GBrain-approved membership observations loaded, but school verification remains blocked. Drain or explicitly close "
                "the remaining denominator/source/route action queue; preserve shared-source identity ambiguity before any unique-person merge."
            )
        elif vanderbilt_parser_extraction:
            next_action = (
                f"Prepare a GBrain packet for exactly {int(vanderbilt_parser_extraction.get('evidence_ready_candidate_rows') or 0)} "
                "Vanderbilt evidence-ready extraction rows; exclude blocked extraction rows, residual route packets, denominator closures, "
                "and school verification until separately approved."
            )
        elif vanderbilt_route_packets:
            next_action = (
                f"Build exact non-mutating parser-ready extraction packets from {int(vanderbilt_route_packets.get('parser_review_candidate_packets') or 0)} "
                "Vanderbilt parser-review packets; resolve recursive route, scope-mismatch, and residual denominator packets before any people, "
                "denominator closures, or school verification."
            )
        elif vanderbilt_route:
            next_action = (
                "Review Vanderbilt route-inspection parser candidates, scope mismatches, and residual route buckets; submit no "
                "people, denominator closures, or school verification until an exact GBrain packet authorizes the specific mutation."
            )
        elif vanderbilt_probe_rows:
            next_action = (
                f"Run headed Vanderbilt route inspection over {vanderbilt_source_candidates} source-candidate rows, then resolve "
                "unlinked program URLs, roster-text pages, and context-only pages before any person acceptance, closure, or school verification."
            )
        else:
            next_action = (
                "Use official VUMC denominator rows to drive roster-route probes; submit no people and no school "
                "verification until gaps are either covered or explicitly closed."
            )

    included_artifacts = [
        "artifacts/data/school_capability_manifest.csv",
        "artifacts/data/gbrain_consultation_ledger.json",
        "artifacts/data/warehouse_reproducibility_summary.json",
        "artifacts/data/official_program_coverage_action_queue.csv",
        "artifacts/data/official_program_coverage_dossiers.csv",
    ]
    if "HOPKINS" in school_name:
        included_artifacts.extend([
            "artifacts/data/hopkins_training_summary.json",
            "artifacts/data/hopkins_training_people.json",
            "artifacts/data/hopkins_candidate_closure_summary.json",
            "artifacts/data/hopkins_candidate_closure_audit.csv",
            "artifacts/data/hopkins_roster_route_inspection.csv",
            "artifacts/research/hopkins-expansion-status-2026-06-05.md",
            "artifacts/research/hopkins-remaining-queue-closure-criteria-2026-06-05.md",
        ])
    if "CALIFORNIA SAN FRAN" in school_name:
        included_artifacts.extend([
            "artifacts/data/ucsf_training_summary.json",
            "artifacts/data/ucsf_training_sources.json",
            "artifacts/data/ucsf_gme_program_universe.json",
            "artifacts/data/ucsf_gme_program_coverage.json",
            "artifacts/data/ucsf_source_gap_ledger.csv",
            "artifacts/data/ucsf_program_page_probe.csv",
            "artifacts/data/ucsf_program_page_probe_summary.json",
            "artifacts/data/ucsf_roster_route_inspection.csv",
            "artifacts/data/ucsf_roster_route_inspection_summary.json",
            "artifacts/data/ucsf_parser_ready_rosters.csv",
            "artifacts/data/ucsf_parser_ready_roster_summary.json",
            "artifacts/data/ucsf_candidate_closure_summary.json",
            "artifacts/data/ucsf_candidate_closure_audit.csv",
        ])
    if "WASHINGTON UNIVERSITY" in school_name:
        included_artifacts.extend([
            "artifacts/data/washu_training_summary.json",
            "artifacts/data/washu_training_sources.json",
            "artifacts/data/washu_gme_department_hubs.json",
            "artifacts/data/washu_gme_program_universe_seed_2022.json",
            "artifacts/data/washu_gme_program_universe_reconciled.json",
            "artifacts/data/washu_gme_program_universe.json",
            "artifacts/data/washu_gme_program_coverage.json",
            "artifacts/data/washu_source_gap_ledger.csv",
            "artifacts/data/washu_program_page_probe.csv",
            "artifacts/data/washu_program_page_probe_summary.json",
            "artifacts/data/washu_source_candidates.csv",
            "artifacts/data/washu_source_probes.json",
            "artifacts/data/washu_source_probe_summary.json",
            "artifacts/data/washu_broad_source_candidates.csv",
            "artifacts/data/washu_broad_source_candidates.json",
            "artifacts/data/washu_source_search_queries.csv",
            "artifacts/data/washu_source_search_observations.csv",
            "artifacts/data/washu_roster_route_inspection.csv",
            "artifacts/data/washu_roster_route_inspection_summary.json",
            "artifacts/data/washu_broad_roster_route_inspection.csv",
            "artifacts/data/washu_broad_roster_route_inspection_summary.json",
            "artifacts/data/washu_parser_ready_rosters.csv",
            "artifacts/data/washu_parser_ready_roster_summary.json",
            "artifacts/data/washu_parser_ready_acceptance_gate.csv",
            "artifacts/data/washu_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/washu_approved_parser_ready_gate_manifest.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_summary.json",
            "artifacts/data/washu_approved_parser_ready_gate_manifest_drift_summary.json",
            "artifacts/data/washu_live_gate_drift_analysis.csv",
            "artifacts/data/washu_live_gate_drift_analysis.json",
            "artifacts/data/washu_ophthalmology_fellowship_parser_ready_rosters.csv",
            "artifacts/data/washu_ophthalmology_fellowship_parser_ready_roster_summary.json",
            "artifacts/data/washu_fellowship_scope_review.csv",
            "artifacts/data/washu_fellowship_scope_review_summary.json",
            "artifacts/data/washu_school_verification_reconciliation.csv",
            "artifacts/data/washu_school_verification_reconciliation_summary.json",
            "artifacts/data/washu_acgme_current_programs.csv",
            "artifacts/data/washu_acgme_denominator_reconciliation.csv",
            "artifacts/data/washu_current_denominator_search.csv",
            "artifacts/data/washu_acgme_denominator_summary.json",
        ])
    if "YALE" in school_name:
        included_artifacts.extend([
            "artifacts/data/yale_training_summary.json",
            "artifacts/data/yale_training_sources.json",
            "artifacts/data/yale_gme_program_universe.csv",
            "artifacts/data/yale_gme_program_universe.json",
            "artifacts/data/yale_gme_program_universe_source.json",
            "artifacts/data/yale_gme_program_coverage.json",
            "artifacts/data/yale_program_page_probe.csv",
            "artifacts/data/yale_program_page_probe_summary.json",
            "artifacts/data/yale_source_candidates.csv",
            "artifacts/data/yale_roster_route_inspection.csv",
            "artifacts/data/yale_roster_route_inspection_summary.json",
            "artifacts/data/yale_second_hop_source_candidates.csv",
            "artifacts/data/yale_second_hop_source_candidate_summary.json",
            "artifacts/data/yale_second_hop_roster_route_inspection.csv",
            "artifacts/data/yale_second_hop_roster_route_inspection_summary.json",
            "artifacts/data/yale_parser_ready_rosters.csv",
            "artifacts/data/yale_parser_ready_rosters.json",
            "artifacts/data/yale_parser_ready_roster_summary.json",
            "artifacts/data/yale_parser_ready_acceptance_gate.csv",
            "artifacts/data/yale_parser_ready_acceptance_gate.json",
            "artifacts/data/yale_parser_ready_acceptance_gate_summary.json",
            "artifacts/data/yale_approved_parser_ready_gate_manifest.csv",
            "artifacts/data/yale_approved_parser_ready_gate_manifest.json",
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
            "artifacts/data/yale_action_queue_triage.json",
            "artifacts/data/yale_action_queue_triage_summary.json",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet.csv",
            "artifacts/data/yale_cardiac_surgery_role_conflict_packet_summary.json",
            "artifacts/research/yale-parser-ready-acceptance-gbrain-packet-2026-06-06.md",
            "artifacts/research/yale-addiction-medicine-acceptance-gbrain-packet-2026-06-06.md",
            "artifacts/research/yale-exact-candidate-acceptance-gbrain-packet-2026-06-06.md",
            "artifacts/research/yale-action-queue-triage-2026-06-06.md",
            "artifacts/research/yale-cardiac-surgery-role-conflict-gbrain-packet-2026-06-06.md",
        ])
    if "VANDERBILT" in school_name:
        included_artifacts.extend([
            "artifacts/data/school_gap_resolution_manifest.csv",
            "artifacts/data/school_gap_resolution_manifest.json",
            "artifacts/data/school_gap_resolution_manifest_summary.json",
            "artifacts/data/school_gap_resolution_batches.csv",
            "artifacts/data/school_gap_resolution_batches.json",
            "artifacts/data/school_gap_resolution_batch_summary.json",
            "artifacts/data/school_gap_resolution_batch_packets.csv",
            "artifacts/data/school_gap_resolution_batch_packets.json",
            "artifacts/data/school_gap_resolution_batch_packet_summary.json",
            "artifacts/data/vanderbilt_training_summary.json",
            "artifacts/data/vanderbilt_training_sources.json",
            "artifacts/data/vanderbilt_gme_program_universe.csv",
            "artifacts/data/vanderbilt_gme_program_universe.json",
            "artifacts/data/vanderbilt_gme_program_universe_source.json",
            "artifacts/data/vanderbilt_gme_program_coverage.json",
            "artifacts/data/vanderbilt_program_page_probe.csv",
            "artifacts/data/vanderbilt_program_page_probe_summary.json",
            "artifacts/data/vanderbilt_source_candidates.csv",
            "artifacts/data/vanderbilt_source_candidates.json",
            "artifacts/data/vanderbilt_roster_route_inspection.csv",
            "artifacts/data/vanderbilt_roster_route_inspection.json",
            "artifacts/data/vanderbilt_roster_route_inspection_summary.json",
            "artifacts/data/vanderbilt_second_hop_source_candidates.csv",
            "artifacts/data/vanderbilt_second_hop_source_candidates.json",
            "artifacts/data/vanderbilt_second_hop_roster_route_inspection.csv",
            "artifacts/data/vanderbilt_second_hop_roster_route_inspection.json",
            "artifacts/data/vanderbilt_second_hop_roster_route_inspection_summary.json",
            "artifacts/data/vanderbilt_route_review_packets.csv",
            "artifacts/data/vanderbilt_route_review_packets.json",
            "artifacts/data/vanderbilt_route_review_packet_summary.json",
            "artifacts/data/vanderbilt_parser_ready_extraction_packets.csv",
            "artifacts/data/vanderbilt_parser_ready_extraction_packets.json",
            "artifacts/data/vanderbilt_parser_ready_extraction_candidates.csv",
            "artifacts/data/vanderbilt_parser_ready_extraction_candidates.json",
            "artifacts/data/vanderbilt_parser_ready_extraction_packet_summary.json",
            "artifacts/data/vanderbilt_candidate_closure_audit.csv",
            "artifacts/data/vanderbilt_candidate_closure_audit.json",
            "artifacts/data/vanderbilt_candidate_closure_summary.json",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet.csv",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet.json",
            "artifacts/data/vanderbilt_scope_mapping_closure_packet_summary.json",
            "artifacts/data/vanderbilt_approved_candidate_source_dispositions.csv",
            "artifacts/data/vanderbilt_approved_candidate_source_dispositions.json",
            "artifacts/data/vanderbilt_approved_candidate_source_disposition_summary.json",
            "artifacts/data/vanderbilt_parser_manual_repair_probe.csv",
            "artifacts/data/vanderbilt_parser_manual_repair_probe.json",
            "artifacts/data/vanderbilt_parser_manual_repair_candidates.csv",
            "artifacts/data/vanderbilt_parser_manual_repair_candidates.json",
            "artifacts/data/vanderbilt_parser_manual_repair_summary.json",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet.csv",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet.json",
            "artifacts/data/vanderbilt_parser_repair_acceptance_packet_summary.json",
            "artifacts/data/vanderbilt_parser_manual_review_35_packet.csv",
            "artifacts/data/vanderbilt_parser_manual_review_35_packet.json",
            "artifacts/data/vanderbilt_parser_manual_review_35_packet_summary.json",
            "artifacts/data/gbrain_vanderbilt_parser_manual_review_35_http_mcp_response.json",
            "artifacts/research/vanderbilt-parser-manual-review-35-gbrain-packet-2026-06-07.md",
            "artifacts/research/vanderbilt-parser-manual-review-35-approval-capsule-2026-06-07.md",
            "artifacts/data/vanderbilt_active_source_candidate_targets.csv",
            "artifacts/data/vanderbilt_active_source_candidate_targets.json",
            "artifacts/data/vanderbilt_active_source_candidate_targets_summary.json",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection.csv",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection.json",
            "artifacts/data/vanderbilt_active_source_candidate_route_inspection_summary.json",
            "artifacts/data/vanderbilt_active_second_hop_targets.csv",
            "artifacts/data/vanderbilt_active_second_hop_targets.json",
            "artifacts/data/vanderbilt_active_second_hop_targets_summary.json",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection.csv",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection.json",
            "artifacts/data/vanderbilt_active_second_hop_route_inspection_summary.json",
            "artifacts/data/vanderbilt_active_source_acceptance_packet.csv",
            "artifacts/data/vanderbilt_active_source_acceptance_packet.json",
            "artifacts/data/vanderbilt_active_source_acceptance_packet_summary.json",
            "artifacts/data/vanderbilt_active_source_route_inspection_packet.csv",
            "artifacts/data/vanderbilt_active_source_route_inspection_packet.json",
            "artifacts/data/vanderbilt_active_source_route_inspection_packet_summary.json",
            "artifacts/data/gbrain_vanderbilt_active_source_route_inspection_76_http_mcp_response.json",
            "artifacts/research/vanderbilt-active-source-route-inspection-gbrain-packet-2026-06-07.md",
            "artifacts/research/vanderbilt-active-source-route-inspection-approval-capsule-2026-06-07.md",
            "artifacts/data/vanderbilt_residual_drain_log.csv",
            "artifacts/data/vanderbilt_residual_drain_log.json",
            "artifacts/data/vanderbilt_residual_drain_log_summary.json",
            "artifacts/data/vanderbilt_gbrain_acceptance_packet_summary.json",
            "artifacts/data/vanderbilt_approved_parser_ready_manifest.csv",
            "artifacts/data/vanderbilt_approved_parser_ready_manifest.json",
            "artifacts/data/vanderbilt_approved_parser_ready_manifest_summary.json",
            "artifacts/data/vanderbilt_training_people.csv",
            "artifacts/data/vanderbilt_training_people.json",
            "artifacts/research/vanderbilt-parser-ready-acceptance-gbrain-packet-2026-06-06.md",
            "artifacts/research/vanderbilt-scope-mapping-closure-gbrain-packet-2026-06-06.md",
            "artifacts/research/vanderbilt-parser-repair-acceptance-gbrain-packet-2026-06-06.md",
            "artifacts/research/vanderbilt-active-source-acceptance-gbrain-packet-2026-06-06.md",
        ])
    evidence = {
        "school_stats": stats,
        "manifest_lanes": [row["capability_lane"] for row in school_manifest],
        "gap_resolution_manifest_summary": read_json(ARTIFACTS / "school_gap_resolution_manifest_summary.json", {}),
        "gap_resolution_batch_summary": read_json(ARTIFACTS / "school_gap_resolution_batch_summary.json", {}),
        "gap_resolution_batch_packet_summary": read_json(ARTIFACTS / "school_gap_resolution_batch_packet_summary.json", {}),
        "reproducibility": {
            "artifact_rows": reproducibility.get("artifact_rows"),
            "required_missing_artifacts": reproducibility.get("required_missing_artifacts"),
            "row_count_mismatch_rows": reproducibility.get("row_count_mismatch_rows"),
            "by_row_count_status": reproducibility.get("by_row_count_status"),
        },
    }
    return {
        "dossier_key": "school_readiness_dossier_" + sha_key(f"{school_key}|{sponsoring_institution}"),
        "school_key": school_key,
        "school_name": school_name,
        "sponsoring_institution": sponsoring_institution,
        "dossier_status": dossier_status,
        "gbrain_approval_status": gbrain_status,
        "verification_posture": verification_posture,
        "manifest_rows": str(len(school_manifest)),
        "open_manifest_blocker_rows": str(open_manifest_blockers),
        "min_maturity_level": str(min_maturity),
        "coverage_program_rows": str(stats["coverage_program_rows"]),
        "covered_program_rows": str(stats["covered_program_rows"]),
        "open_gap_rows": str(stats["open_gap_rows"]),
        "action_queue_rows": str(stats["action_queue_rows"]),
        "reproducibility_status": "ok" if repro_ok else "failed",
        "warehouse_people": str(sqlite_scalar(conn, "SELECT COUNT(*) FROM people")),
        "warehouse_training_events": str(sqlite_scalar(conn, "SELECT COUNT(*) FROM person_training_events")),
        "required_next_action": next_action,
        "included_artifacts_json": dumps(included_artifacts),
        "blocker_summary_json": dumps({
            "manifest_open_blockers": open_manifest_blockers,
            "coverage_open_gaps": stats["open_gap_rows"],
            "action_queue_rows": stats["action_queue_rows"],
            "queue_lanes": stats["queue_lanes"],
            "queue_blockers": stats["queue_blockers"],
        }),
        "evidence_json": dumps(evidence),
        "generated_at": generated_at,
    }


def build_stanford_dossier(
    *,
    conn: sqlite3.Connection,
    school_key: str,
    school_name: str,
    generated_at: str,
    gbrain: dict,
    manifest_rows: list[dict[str, str]],
    reproducibility: dict,
) -> dict[str, str]:
    sponsoring_institution = "Stanford Health Care / Stanford University Medical Center"
    school_manifest = [row for row in manifest_rows if row["school_name"] == school_name]
    open_manifest_blockers = sum(
        1
        for row in school_manifest
        if row.get("capability_lane") != "gbrain_verification"
        and int(row.get("blocker_count") or 0) > 0
    )
    min_maturity = min((int(row.get("maturity_level") or 0) for row in school_manifest), default=0)
    repro_ok = (
        int(reproducibility.get("required_missing_artifacts") or 0) == 0
        and int(reproducibility.get("row_count_mismatch_rows") or 0) == 0
    )

    denominator_rows = read_csv(ARTIFACTS / "top50_next_school_discovery_manifest.csv")
    denominator_rows = [row for row in denominator_rows if row.get("school_name") == school_name]
    denominator_programs = {row.get("program_name", "") for row in denominator_rows if row.get("program_name")}
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
    general_surgery_residency_summary = read_json(ARTIFACTS / "stanford_general_surgery_residency_parser_packet_summary.json", {})
    family_sports_medicine_summary = read_json(ARTIFACTS / "stanford_family_sports_medicine_acceptance_packet_summary.json", {})
    allergy_immunology_summary = read_json(ARTIFACTS / "stanford_allergy_immunology_acceptance_packet_summary.json", {})
    hand_surgery_summary = read_json(ARTIFACTS / "stanford_hand_surgery_acceptance_packet_summary.json", {})
    nuclear_medicine_summary = read_json(ARTIFACTS / "stanford_nuclear_medicine_acceptance_packet_summary.json", {})
    nuclear_radiology_fellow_summary = read_json(ARTIFACTS / "stanford_nuclear_radiology_fellow_acceptance_packet_summary.json", {})
    training_summary = read_json(ARTIFACTS / "stanford_training_summary.json", {})
    gap_drain_summary = read_json(ARTIFACTS / "stanford_gap_drain_queue_summary.json", {})
    active_gap_acceptance_summary = read_json(
        ARTIFACTS / "stanford_active_gap_current_roster_repair_acceptance_packet_summary.json", {}
    )
    active_gap_disposition_summary = read_json(
        ARTIFACTS / "stanford_active_gap_current_roster_repair_disposition_packet_summary.json", {}
    )

    accepted_programs = set((training_summary.get("program_counts") or {}).keys())
    covered_programs = denominator_programs & accepted_programs
    coverage_program_rows = len(denominator_programs)
    covered_program_rows = len(covered_programs)
    raw_open_gap_rows = max(0, coverage_program_rows - covered_program_rows)
    active_gap_drain_rows = int(gap_drain_summary.get("active_batch_rows") or 0)
    gap_drain_queue_complete = (
        int(gap_drain_summary.get("rows") or 0) == 70
        and active_gap_drain_rows == 0
        and int(gap_drain_summary.get("queued_rows") or 0) == 0
    )
    active_gap_acceptance_approved = (
        active_gap_acceptance_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and active_gap_acceptance_summary.get("gbrain_approval_verified") is True
        and int(active_gap_acceptance_summary.get("rows") or 0) == 80
    )
    active_gap_disposition_approved = (
        active_gap_disposition_summary.get("packet_status")
        == "approved_non_mutating_active_gap_current_roster_repair_disposition_packet"
        and active_gap_disposition_summary.get("gbrain_approval_verified") is True
        and int(active_gap_disposition_summary.get("rows") or 0) == 9
    )
    next_lane_effects = {row.get("approval_effect", "") for row in gbrain.get("attempts", [])}
    stanford_readiness_next_lane_recommended = (
        "stanford_school_readiness_packet_next_lane_required_non_mutating" in next_lane_effects
    )
    stanford_ready_for_gbrain = (
        repro_ok
        and gap_drain_queue_complete
        and active_gap_acceptance_approved
        and active_gap_disposition_approved
        and stanford_readiness_next_lane_recommended
        and int(training_summary.get("accepted_people") or 0) >= 1088
    )
    stanford_school_verified = "stanford_school_verified_next_lane_approved" in next_lane_effects
    open_gap_rows = 0 if stanford_ready_for_gbrain else raw_open_gap_rows
    open_manifest_blockers = 0 if stanford_ready_for_gbrain else open_manifest_blockers
    original_parser_review_blocked_rows = int(parser_summary.get("review_required_candidate_rows") or 0) + int(parser_summary.get("blocked_candidate_rows") or 0)
    parser_review_blocked_rows = original_parser_review_blocked_rows
    if parser_disposition_summary:
        parser_review_blocked_rows = int(parser_disposition_summary.get("proposed_incremental_acceptance_rows") or 0)
    if name_quality_summary.get("packet_status") == "approved_exact_gbrain_acceptance" and name_quality_summary.get("gbrain_approval_verified"):
        parser_review_blocked_rows = max(0, parser_review_blocked_rows - int(name_quality_summary.get("rows") or 0))
    shared_excluded_rows = int(shared_summary.get("excluded_rows") or 0)
    radonc_excluded_rows = int(radonc_summary.get("excluded_rows") or 0)
    route_blocker_rows = int(route_summary.get("scope_mismatch_rows") or 0) + int(route_summary.get("second_hop_route_candidate_rows") or 0)
    stale_url_rows = int(repair_summary.get("stale_program_rows") or 0)
    stale_disposition_approved = (
        stale_disposition_summary.get("packet_status") == "approved_non_mutating_disposition"
        and stale_disposition_summary.get("gbrain_approval_verified")
    )
    stale_pending_disposition_rows = 0 if stale_disposition_approved else stale_url_rows
    stale_current_roster_acceptance_approved = (
        stale_current_roster_acceptance_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and stale_current_roster_acceptance_summary.get("gbrain_approval_verified")
    )
    stale_route_person_acceptance_candidate_rows = int(stale_route_map_summary.get("parser_ready_or_current_roster_lane_rows") or 0)
    stale_route_person_acceptance_pending_rows = 0 if stale_current_roster_acceptance_approved else stale_route_person_acceptance_candidate_rows
    stale_second_hop_acceptance_approved = (
        stale_second_hop_acceptance_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and stale_second_hop_acceptance_summary.get("gbrain_approval_verified")
    )
    stale_second_hop_acceptance_candidate_rows = int(stale_second_hop_acceptance_summary.get("rows") or 0)
    stale_second_hop_acceptance_pending_rows = 0 if stale_second_hop_acceptance_approved else stale_second_hop_acceptance_candidate_rows
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
    general_surgery_residency_approved = (
        general_surgery_residency_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and general_surgery_residency_summary.get("gbrain_approval_verified")
    )
    family_sports_medicine_approved = (
        family_sports_medicine_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and family_sports_medicine_summary.get("gbrain_approval_verified")
    )
    allergy_immunology_approved = (
        allergy_immunology_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and allergy_immunology_summary.get("gbrain_approval_verified")
    )
    hand_surgery_approved = (
        hand_surgery_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and hand_surgery_summary.get("gbrain_approval_verified")
    )
    nuclear_medicine_approved = (
        nuclear_medicine_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and nuclear_medicine_summary.get("gbrain_approval_verified")
    )
    nuclear_radiology_fellow_approved = (
        nuclear_radiology_fellow_summary.get("packet_status") == "approved_exact_gbrain_acceptance"
        and nuclear_radiology_fellow_summary.get("gbrain_approval_verified")
    )
    shared_residual_approved = (
        shared_residual_summary.get("packet_status") == "approved_non_mutating_shared_source_residual_disposition_packet"
        and shared_residual_summary.get("gbrain_approval_verified")
    )
    unsupported_label_approved = (
        unsupported_label_summary.get("packet_status") == "approved_non_mutating_shared_source_unsupported_label_packet"
        and unsupported_label_summary.get("gbrain_approval_verified")
    )
    lifecycle_identity_approved = (
        lifecycle_identity_summary.get("packet_status") == "approved_non_mutating_lifecycle_identity_readiness_contract"
        and lifecycle_identity_summary.get("gbrain_approval_verified")
    )
    blocker_counts = shared_summary.get("blocker_counts") or {}
    unsupported_label_rows = int(blocker_counts.get("source_section_label_not_in_stanford_program_set") or 0)
    raw_no_roster_context_closure_rows = int(stale_route_map_summary.get("no_roster_or_context_closure_lane_rows") or 0)
    pending_no_roster_context_closure_rows = 0 if nuclear_medicine_approved else raw_no_roster_context_closure_rows

    included_artifacts = [
        "artifacts/data/top50_next_school_discovery_manifest.csv",
        "artifacts/data/stanford_program_page_probe.csv",
        "artifacts/data/stanford_program_page_probe_summary.json",
        "artifacts/data/stanford_source_candidates.csv",
        "artifacts/data/stanford_roster_route_inspection.csv",
        "artifacts/data/stanford_roster_route_inspection_summary.json",
        "artifacts/data/stanford_program_url_repair_probe.csv",
        "artifacts/data/stanford_program_url_repair_probe_summary.json",
        "artifacts/data/stanford_stale_url_browser_repair_probe.csv",
        "artifacts/data/stanford_stale_url_browser_repair_probe_summary.json",
        "artifacts/data/stanford_stale_url_repair_disposition_packet.csv",
        "artifacts/data/stanford_stale_url_repair_disposition_packet_summary.json",
        "artifacts/data/stanford_stale_url_route_map.csv",
        "artifacts/data/stanford_stale_url_route_map_summary.json",
        "artifacts/data/stanford_stale_url_current_roster_acceptance_packet.csv",
        "artifacts/data/stanford_stale_url_current_roster_acceptance_packet_summary.json",
        "artifacts/data/stanford_stale_url_second_hop_inspection.csv",
        "artifacts/data/stanford_stale_url_second_hop_inspection_summary.json",
        "artifacts/data/stanford_stale_url_second_hop_acceptance_packet.csv",
        "artifacts/data/stanford_stale_url_second_hop_acceptance_packet_summary.json",
        "artifacts/data/stanford_stale_url_related_scope_packet.csv",
        "artifacts/data/stanford_stale_url_related_scope_packet_summary.json",
        "artifacts/data/stanford_stale_url_noop_closure_packet.csv",
        "artifacts/data/stanford_stale_url_noop_closure_packet_summary.json",
        "artifacts/data/stanford_pathology_pdf_acceptance_packet.csv",
        "artifacts/data/stanford_pathology_pdf_acceptance_packet_summary.json",
        "artifacts/data/stanford_neuro_residency_acceptance_packet.csv",
        "artifacts/data/stanford_neuro_residency_acceptance_packet_summary.json",
        "artifacts/data/stanford_general_surgery_residency_parser_packet.csv",
        "artifacts/data/stanford_general_surgery_residency_parser_packet_summary.json",
        "artifacts/data/stanford_family_sports_medicine_acceptance_packet.csv",
        "artifacts/data/stanford_family_sports_medicine_acceptance_packet_summary.json",
        "artifacts/data/stanford_allergy_immunology_acceptance_packet.csv",
        "artifacts/data/stanford_allergy_immunology_acceptance_packet_summary.json",
        "artifacts/research/stanford-allergy-immunology-approval-capsule-2026-06-07.md",
        "artifacts/data/stanford_hand_surgery_acceptance_packet.csv",
        "artifacts/data/stanford_hand_surgery_acceptance_packet_summary.json",
        "artifacts/research/stanford-hand-surgery-approval-capsule-2026-06-07.md",
        "artifacts/data/stanford_nuclear_medicine_acceptance_packet.csv",
        "artifacts/data/stanford_nuclear_medicine_acceptance_packet_summary.json",
        "artifacts/data/stanford_nuclear_radiology_fellow_acceptance_packet.csv",
        "artifacts/data/stanford_nuclear_radiology_fellow_acceptance_packet_summary.json",
        "artifacts/data/stanford_parser_ready_extraction_candidates.csv",
        "artifacts/data/stanford_parser_ready_packet_summary.json",
        "artifacts/data/stanford_parser_review_disposition_packet.csv",
        "artifacts/data/stanford_parser_review_disposition_packet_summary.json",
        "artifacts/data/stanford_name_quality_acceptance_packet.csv",
        "artifacts/data/stanford_name_quality_acceptance_packet_summary.json",
        "artifacts/data/stanford_shared_source_crosswalk_packet.csv",
        "artifacts/data/stanford_shared_source_crosswalk_packet_summary.json",
        "artifacts/data/stanford_shared_source_residual_disposition_packet.csv",
        "artifacts/data/stanford_shared_source_residual_disposition_packet_summary.json",
        "artifacts/data/stanford_shared_source_unsupported_label_packet.csv",
        "artifacts/data/stanford_shared_source_unsupported_label_packet_summary.json",
        "artifacts/data/stanford_lifecycle_identity_readiness_packet.csv",
        "artifacts/data/stanford_lifecycle_identity_readiness_packet_summary.json",
        "artifacts/data/stanford_radiation_oncology_scope_packet.csv",
        "artifacts/data/stanford_radiation_oncology_scope_packet_summary.json",
        "artifacts/data/stanford_training_people.csv",
        "artifacts/data/stanford_training_summary.json",
        "artifacts/data/stanford_gap_drain_queue.csv",
        "artifacts/data/stanford_gap_drain_queue_summary.json",
        "artifacts/data/stanford_active_gap_current_roster_repair_acceptance_packet.csv",
        "artifacts/data/stanford_active_gap_current_roster_repair_acceptance_packet_summary.json",
        "artifacts/data/stanford_active_gap_current_roster_repair_disposition_packet.csv",
        "artifacts/data/stanford_active_gap_current_roster_repair_disposition_packet_summary.json",
        "artifacts/data/gbrain_next_lane_after_stanford_active_gap_drain_complete_http_mcp_response.json",
        "artifacts/data/school_gap_resolution_manifest.csv",
        "artifacts/data/school_gap_resolution_manifest.json",
        "artifacts/data/school_gap_resolution_manifest_summary.json",
        "artifacts/data/school_gap_resolution_batches.csv",
        "artifacts/data/school_gap_resolution_batches.json",
        "artifacts/data/school_gap_resolution_batch_summary.json",
        "artifacts/data/school_gap_resolution_batch_packets.csv",
        "artifacts/data/school_gap_resolution_batch_packets.json",
        "artifacts/data/school_gap_resolution_batch_packet_summary.json",
        "artifacts/data/school_capability_manifest.csv",
        "artifacts/data/gbrain_consultation_ledger.json",
        "artifacts/data/warehouse_reproducibility_summary.json",
    ]
    blocker_summary = {
        "open_denominator_gap_rows": open_gap_rows,
        "raw_denominator_gap_rows_before_approved_gap_drain": raw_open_gap_rows,
        "gap_drain_queue_rows": int(gap_drain_summary.get("rows") or 0),
        "gap_drain_active_batch_rows": active_gap_drain_rows,
        "gap_drain_queue_complete": gap_drain_queue_complete,
        "active_gap_pediatrics_acceptance_rows": int(active_gap_acceptance_summary.get("rows") or 0),
        "active_gap_pediatrics_acceptance_approved": active_gap_acceptance_approved,
        "active_gap_current_roster_disposition_rows": int(active_gap_disposition_summary.get("rows") or 0),
        "active_gap_current_roster_disposition_approved": active_gap_disposition_approved,
        "stanford_readiness_next_lane_recommended_by_gbrain": stanford_readiness_next_lane_recommended,
        "school_verification": (
            "verified_by_gbrain"
            if stanford_school_verified
            else "ready_not_submitted"
            if stanford_ready_for_gbrain
            else "not_submitted_not_ready"
        ),
        "denominator_closure": "not_approved",
        "identity_collapse": "not_approved",
        "stale_url_rows": stale_url_rows,
        "stale_url_browser_repaired_candidate_urls": int(browser_repair_summary.get("unique_repaired_candidate_urls") or 0),
        "stale_url_disposition_rows": int(stale_disposition_summary.get("rows") or 0),
        "stale_url_disposition_status": stale_disposition_summary.get("packet_status", ""),
        "stale_url_disposition_effect": stale_disposition_summary.get("gbrain_decision_effect", ""),
        "stale_url_pending_disposition_rows": stale_pending_disposition_rows,
        "stale_url_route_map_rows": int(stale_route_map_summary.get("rows") or 0),
        "stale_url_route_map_hash": stale_route_map_summary.get("rowset_hash", ""),
        "stale_url_route_person_acceptance_candidate_rows": stale_route_person_acceptance_candidate_rows,
        "stale_url_route_person_acceptance_pending_rows": stale_route_person_acceptance_pending_rows,
        "stale_url_current_roster_acceptance_rows": int(stale_current_roster_acceptance_summary.get("rows") or 0),
        "stale_url_current_roster_acceptance_status": stale_current_roster_acceptance_summary.get("packet_status", ""),
        "stale_url_current_roster_acceptance_effect": stale_current_roster_acceptance_summary.get("gbrain_decision_effect", ""),
        "stale_url_current_roster_acceptance_hash": stale_current_roster_acceptance_summary.get("ready_rowset_sha256", ""),
        "stale_url_route_second_hop_rows": int(stale_route_map_summary.get("second_hop_lane_rows") or 0),
        "stale_url_second_hop_inspection_rows": int(stale_second_hop_summary.get("rows") or 0),
        "stale_url_second_hop_inspection_hash": stale_second_hop_summary.get("rowset_hash", ""),
        "stale_url_second_hop_inspection_effect": stale_second_hop_summary.get("lane_effect", ""),
        "stale_url_second_hop_packet_lanes": stale_second_hop_summary.get("by_second_hop_packet_lane", {}),
        "stale_url_second_hop_acceptance_rows": stale_second_hop_acceptance_candidate_rows,
        "stale_url_second_hop_acceptance_status": stale_second_hop_acceptance_summary.get("packet_status", ""),
        "stale_url_second_hop_acceptance_effect": stale_second_hop_acceptance_summary.get("gbrain_decision_effect", ""),
        "stale_url_second_hop_acceptance_hash": stale_second_hop_acceptance_summary.get("ready_rowset_sha256", ""),
        "stale_url_second_hop_acceptance_pending_rows": stale_second_hop_acceptance_pending_rows,
        "stale_url_related_scope_rows": int(stale_related_scope_summary.get("rows") or 0),
        "stale_url_related_scope_status": stale_related_scope_summary.get("packet_status", ""),
        "stale_url_related_scope_effect": stale_related_scope_summary.get("gbrain_decision_effect", ""),
        "stale_url_related_scope_hash": stale_related_scope_summary.get("rowset_sha256", ""),
        "stale_url_related_scope_approved": stale_related_scope_approved,
        "stale_url_noop_closure_rows": int(stale_noop_closure_summary.get("rows") or 0),
        "stale_url_noop_closure_status": stale_noop_closure_summary.get("packet_status", ""),
        "stale_url_noop_closure_effect": stale_noop_closure_summary.get("gbrain_decision_effect", ""),
        "stale_url_noop_closure_hash": stale_noop_closure_summary.get("rowset_sha256", ""),
        "stale_url_noop_closure_approved": stale_noop_closure_approved,
        "pathology_pdf_acceptance_rows": int(pathology_pdf_summary.get("ready_rows") or 0),
        "pathology_pdf_acceptance_status": pathology_pdf_summary.get("packet_status", ""),
        "pathology_pdf_acceptance_effect": pathology_pdf_summary.get("gbrain_decision_effect", ""),
        "pathology_pdf_acceptance_hash": pathology_pdf_summary.get("ready_rowset_sha256", ""),
        "pathology_pdf_acceptance_approved": pathology_pdf_approved,
        "neuro_residency_acceptance_rows": int(neuro_residency_summary.get("rows") or 0),
        "neuro_residency_acceptance_status": neuro_residency_summary.get("packet_status", ""),
        "neuro_residency_acceptance_effect": neuro_residency_summary.get("gbrain_decision_effect", ""),
        "neuro_residency_acceptance_hash": neuro_residency_summary.get("ready_rowset_sha256", ""),
        "neuro_residency_acceptance_approved": neuro_residency_approved,
        "general_surgery_residency_acceptance_rows": int(general_surgery_residency_summary.get("evidence_ready_current_rows") or 0),
        "general_surgery_residency_acceptance_status": general_surgery_residency_summary.get("packet_status", ""),
        "general_surgery_residency_acceptance_effect": general_surgery_residency_summary.get("gbrain_decision_effect", ""),
        "general_surgery_residency_acceptance_hash": general_surgery_residency_summary.get("ready_rowset_sha256", ""),
        "general_surgery_residency_acceptance_approved": general_surgery_residency_approved,
        "general_surgery_residency_review_or_excluded_rows": int(general_surgery_residency_summary.get("excluded_or_review_rows") or 0),
        "family_sports_medicine_acceptance_rows": int(family_sports_medicine_summary.get("evidence_ready_current_rows") or 0),
        "family_sports_medicine_acceptance_status": family_sports_medicine_summary.get("packet_status", ""),
        "family_sports_medicine_acceptance_effect": family_sports_medicine_summary.get("gbrain_decision_effect", ""),
        "family_sports_medicine_acceptance_hash": family_sports_medicine_summary.get("ready_rowset_sha256", ""),
        "family_sports_medicine_acceptance_approved": family_sports_medicine_approved,
        "allergy_immunology_acceptance_rows": int(allergy_immunology_summary.get("evidence_ready_current_rows") or 0),
        "allergy_immunology_acceptance_status": allergy_immunology_summary.get("packet_status", ""),
        "allergy_immunology_acceptance_effect": allergy_immunology_summary.get("gbrain_decision_effect", ""),
        "allergy_immunology_acceptance_hash": allergy_immunology_summary.get("ready_rowset_sha256", ""),
        "allergy_immunology_acceptance_approved": allergy_immunology_approved,
        "hand_surgery_acceptance_rows": int(hand_surgery_summary.get("evidence_ready_current_rows") or 0),
        "hand_surgery_acceptance_status": hand_surgery_summary.get("packet_status", ""),
        "hand_surgery_acceptance_effect": hand_surgery_summary.get("approval_effect", ""),
        "hand_surgery_acceptance_hash": hand_surgery_summary.get("ready_rowset_sha256", ""),
        "hand_surgery_acceptance_approved": hand_surgery_approved,
        "nuclear_medicine_acceptance_rows": int(nuclear_medicine_summary.get("rows") or 0),
        "nuclear_medicine_acceptance_status": nuclear_medicine_summary.get("packet_status", ""),
        "nuclear_medicine_acceptance_effect": nuclear_medicine_summary.get("gbrain_decision_effect", ""),
        "nuclear_medicine_acceptance_hash": nuclear_medicine_summary.get("ready_rowset_sha256", ""),
        "nuclear_medicine_acceptance_approved": nuclear_medicine_approved,
        "nuclear_medicine_excluded_related_rows": int(nuclear_medicine_summary.get("excluded_related_rows") or 0),
        "nuclear_radiology_fellow_acceptance_rows": int(nuclear_radiology_fellow_summary.get("rows") or 0),
        "nuclear_radiology_fellow_acceptance_status": nuclear_radiology_fellow_summary.get("packet_status", ""),
        "nuclear_radiology_fellow_acceptance_effect": nuclear_radiology_fellow_summary.get("gbrain_decision_effect", ""),
        "nuclear_radiology_fellow_acceptance_hash": nuclear_radiology_fellow_summary.get("ready_rowset_sha256", ""),
        "nuclear_radiology_fellow_acceptance_approved": nuclear_radiology_fellow_approved,
        "stale_url_route_no_roster_context_closure_rows": raw_no_roster_context_closure_rows,
        "stale_url_route_no_roster_context_closure_pending_rows": pending_no_roster_context_closure_rows,
        "route_blocker_rows": route_blocker_rows,
        "parser_original_review_or_blocked_rows": original_parser_review_blocked_rows,
        "parser_remaining_acceptance_candidate_rows": parser_review_blocked_rows,
        "parser_disposition_rows": int(parser_disposition_summary.get("rows") or 0),
        "parser_disposition_status": parser_disposition_summary.get("packet_status", ""),
        "parser_disposition_denial_effect": parser_disposition_summary.get("gbrain_decision_effect", ""),
        "name_quality_acceptance_rows": int(name_quality_summary.get("rows") or 0),
        "name_quality_acceptance_status": name_quality_summary.get("packet_status", ""),
        "name_quality_acceptance_effect": name_quality_summary.get("gbrain_decision_effect", ""),
        "parser_disposition_excluded_rows": int(parser_disposition_summary.get("excluded_rows") or 0),
        "parser_disposition_already_accepted_rows": int(parser_disposition_summary.get("already_accepted_by_prior_packet_rows") or 0),
        "shared_source_excluded_rows": shared_excluded_rows,
        "shared_source_residual_disposition_rows": int(shared_residual_summary.get("rows") or 0),
        "shared_source_residual_disposition_status": shared_residual_summary.get("packet_status", ""),
        "shared_source_residual_disposition_effect": shared_residual_summary.get("gbrain_decision_effect", ""),
        "shared_source_residual_disposition_hash": shared_residual_summary.get("rowset_sha256", ""),
        "shared_source_residual_disposition_approved": shared_residual_approved,
        "shared_source_residual_pending_disposition_rows": 0 if shared_residual_approved else int(shared_residual_summary.get("rows") or 0),
        "shared_source_residual_hand_surgery_rows": int((shared_residual_summary.get("by_requested_disposition") or {}).get("retain_hand_surgery_assignment_blocker") or 0),
        "shared_source_residual_hand_surgery_pending_assignment_rows": 0 if hand_surgery_approved else int((shared_residual_summary.get("by_requested_disposition") or {}).get("retain_hand_surgery_assignment_blocker") or 0),
        "shared_source_residual_general_surgery_team_page_rows": int((shared_residual_summary.get("by_requested_disposition") or {}).get("exclude_general_surgery_team_page_from_trainee_roster_truth") or 0),
        "shared_source_unsupported_label_disposition_rows": int(unsupported_label_summary.get("rows") or 0),
        "shared_source_unsupported_label_disposition_status": unsupported_label_summary.get("packet_status", ""),
        "shared_source_unsupported_label_disposition_effect": unsupported_label_summary.get("gbrain_decision_effect", ""),
        "shared_source_unsupported_label_disposition_hash": unsupported_label_summary.get("rowset_sha256", ""),
        "shared_source_unsupported_label_disposition_approved": unsupported_label_approved,
        "shared_source_unsupported_label_pending_rows": 0 if unsupported_label_approved else unsupported_label_rows,
        "lifecycle_identity_contract_rows": int(lifecycle_identity_summary.get("rows") or 0),
        "lifecycle_identity_contract_status": lifecycle_identity_summary.get("packet_status", ""),
        "lifecycle_identity_contract_effect": lifecycle_identity_summary.get("gbrain_decision_effect", ""),
        "lifecycle_identity_contract_hash": lifecycle_identity_summary.get("rowset_sha256", ""),
        "lifecycle_identity_contract_approved": lifecycle_identity_approved,
        "lifecycle_identity_readiness_contract_complete": bool(lifecycle_identity_summary.get("readiness_contract_complete")),
        "lifecycle_identity_repair_required": bool(lifecycle_identity_summary.get("lifecycle_artifact_repair_required")),
        "stanford_lifecycle_contract_coverage_gap_rows": int(lifecycle_identity_summary.get("stanford_lifecycle_contract_coverage_gap_rows") or 0),
        "stanford_lifecycle_institution_mismatch_rows": int(lifecycle_identity_summary.get("stanford_lifecycle_institution_mismatch_rows") or 0),
        "stanford_temporal_contract_rows": int(lifecycle_identity_summary.get("stanford_temporal_contract_rows") or 0),
        "radiation_oncology_excluded_rows": radonc_excluded_rows,
        "hand_surgery_assignment_rows": int(blocker_counts.get("source_lists_hand_fellows_without_orthopedic_vs_plastic_program_section") or 0),
        "hand_surgery_assignment_pending_rows": 0 if hand_surgery_approved else int(blocker_counts.get("source_lists_hand_fellows_without_orthopedic_vs_plastic_program_section") or 0),
        "general_surgery_team_page_rows": int(blocker_counts.get("source_page_is_mixed_program_leadership_admin_faculty_and_partial_chief_resident_context") or 0),
        "unsupported_section_label_rows": unsupported_label_rows,
        "not_approved": [
            item for item in training_summary.get("not_approved", [])
            if not (stale_noop_closure_approved and item == "stale_url_second_hop_noop_closure_rows_outside_exact_33_pathology_pdf_neuro_residency_nuclear_medicine_and_nuclear_radiology_fellow_packets")
        ],
    }
    evidence = {
        "denominator_summary": {
            "program_rows": coverage_program_rows,
            "manifest_rows": len(denominator_rows),
            "covered_program_rows": covered_program_rows,
            "open_gap_rows": open_gap_rows,
        },
        "training_summary": training_summary,
        "gap_drain_summary": gap_drain_summary,
        "active_gap_acceptance_summary": active_gap_acceptance_summary,
        "active_gap_disposition_summary": active_gap_disposition_summary,
        "probe_summary": probe_summary,
        "route_summary": route_summary,
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
        "general_surgery_residency_acceptance_summary": general_surgery_residency_summary,
        "family_sports_medicine_acceptance_summary": family_sports_medicine_summary,
        "allergy_immunology_acceptance_summary": allergy_immunology_summary,
        "hand_surgery_acceptance_summary": hand_surgery_summary,
        "nuclear_medicine_acceptance_summary": nuclear_medicine_summary,
        "nuclear_radiology_fellow_acceptance_summary": nuclear_radiology_fellow_summary,
        "parser_summary": parser_summary,
        "parser_disposition_summary": parser_disposition_summary,
        "name_quality_acceptance_summary": name_quality_summary,
        "shared_summary": shared_summary,
        "shared_source_residual_disposition_summary": shared_residual_summary,
        "shared_source_unsupported_label_disposition_summary": unsupported_label_summary,
        "lifecycle_identity_readiness_summary": lifecycle_identity_summary,
        "radiation_oncology_summary": radonc_summary,
        "repair_summary": repair_summary,
        "source_candidate_rows": len(source_candidates),
        "manifest_lanes": [row["capability_lane"] for row in school_manifest],
        "gbrain_lane_effect": "stanford_next_lane_school_readiness_dossier_non_mutating",
        "gap_resolution_manifest_summary": read_json(ARTIFACTS / "school_gap_resolution_manifest_summary.json", {}),
        "gap_resolution_batch_summary": read_json(ARTIFACTS / "school_gap_resolution_batch_summary.json", {}),
        "gap_resolution_batch_packet_summary": read_json(ARTIFACTS / "school_gap_resolution_batch_packet_summary.json", {}),
        "reproducibility": {
            "artifact_rows": reproducibility.get("artifact_rows"),
            "required_missing_artifacts": reproducibility.get("required_missing_artifacts"),
            "row_count_mismatch_rows": reproducibility.get("row_count_mismatch_rows"),
            "by_row_count_status": reproducibility.get("by_row_count_status"),
        },
    }
    parser_phrase = (
        "the remaining parser-review acceptance candidates, "
        if parser_review_blocked_rows
        else ""
    )
    unsupported_label_phrase = (
        "retain approved unsupported-label disposition evidence, "
        if unsupported_label_approved
        else "unsupported labels, "
    )
    lifecycle_repair_required = bool(lifecycle_identity_summary.get("lifecycle_artifact_repair_required"))
    lifecycle_identity_phrase = (
        "retain approved repaired lifecycle/identity contract with full Stanford lifecycle coverage and 0 institution mismatches; keep review-bound lifecycle rows non-mutating before school verification"
        if lifecycle_identity_approved and not lifecycle_repair_required
        else (
            "retain approved lifecycle/identity contract while repairing "
            f"{int(lifecycle_identity_summary.get('stanford_lifecycle_contract_coverage_gap_rows') or 0)} missing Stanford lifecycle rows "
            f"and {int(lifecycle_identity_summary.get('stanford_lifecycle_institution_mismatch_rows') or 0)} institution-scope labels before school verification"
            if lifecycle_identity_approved
            else "lifecycle/identity readiness"
        )
    )
    family_sports_phrase = (
        "retain approved Family Sports Medicine current-fellow exact packet, "
        if family_sports_medicine_approved
        else "Family Sports Medicine current-fellow source packet approval, "
    )
    allergy_immunology_phrase = (
        "retain approved Allergy/Immunology current-fellow exact packet, "
        if allergy_immunology_approved
        else "Allergy/Immunology current-fellow source packet approval, "
    )
    hand_surgery_phrase = (
        "retain approved Hand Surgery current-fellow assignment packet, "
        if hand_surgery_approved
        else "Hand Surgery assignment, "
    )
    if stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved and general_surgery_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved and stale_noop_closure_approved:
        second_hop_residual_phrase = (
            "stale URL second-hop residuals "
            "(exact acceptance, related-scope disposition, no-op/crosswalk closure, Pathology PDF acceptance, "
            "Neurology/Neurosurgery residency acceptance, General Surgery residency acceptance, Nuclear Medicine "
            "residency acceptance, and Nuclear Radiology fellow acceptance are approved)"
        )
    elif stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved and general_surgery_residency_approved and nuclear_medicine_approved and nuclear_radiology_fellow_approved:
        second_hop_residual_phrase = (
            "remaining stale URL second-hop outputs "
            "(already-accepted/no-op crosswalk closure lanes; exact acceptance, related-scope disposition, "
            "Pathology PDF acceptance, Neurology/Neurosurgery residency acceptance, General Surgery residency "
            "acceptance, Nuclear Medicine residency acceptance, and Nuclear Radiology fellow acceptance are approved)"
        )
    elif stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved and nuclear_medicine_approved:
        second_hop_residual_phrase = (
            "remaining stale URL second-hop outputs "
            "(already-accepted/no-op crosswalk closure lanes; exact acceptance, related-scope disposition, "
            "Pathology PDF acceptance, Neurology/Neurosurgery residency acceptance, and Nuclear Medicine residency "
            "acceptance are approved)"
        )
    elif stale_related_scope_approved and pathology_pdf_approved and neuro_residency_approved:
        second_hop_residual_phrase = (
            "remaining stale URL second-hop outputs "
            "(already-accepted/no-op crosswalk closure lanes; exact acceptance, related-scope disposition, "
            "Pathology PDF acceptance, and Neurology/Neurosurgery residency acceptance are approved)"
        )
    elif stale_related_scope_approved and pathology_pdf_approved:
        second_hop_residual_phrase = (
            "remaining stale URL second-hop outputs "
            "(third-hop, already-accepted/no-op crosswalk, and no-roster closure lanes; exact acceptance, "
            "related-scope disposition, and Pathology PDF acceptance are approved)"
        )
    elif stale_related_scope_approved:
        second_hop_residual_phrase = (
            "remaining stale URL second-hop outputs "
            "(PDF parser, third-hop, already-accepted/no-op crosswalk, and no-roster closure lanes; "
            "exact acceptance and related-scope disposition are approved)"
        )
    else:
        second_hop_residual_phrase = (
            "remaining stale URL second-hop outputs "
            "(related-scope closure, PDF parser, third-hop, and no-roster closure lanes; exact acceptance is approved and loaded)"
        )
    next_action = (
        "Stanford is school-verified by GBrain under the non-mutating honesty-about-gaps boundary. Continue to "
        "preserve caveats that the 8 non-Pediatrics active-gap repair rows are dispositions only, not people or "
        "closures, and that school verification does not approve URL rewrites, unsupported-label ingestion, "
        "research/profile/contact facts, identity collapse, or global top-50 readiness."
        if stanford_school_verified
        else "Submit the non-mutating Stanford school-level readiness dossier through GBrain HTTP MCP. Do not mark "
        "Stanford school-verified unless GBrain explicitly approves that school-level effect; preserve caveats that "
        "the 8 non-Pediatrics active-gap repair rows are dispositions only, not people or closures, and that school "
        "verification does not approve URL rewrites, unsupported-label ingestion, research/profile/contact facts, or "
        "identity collapse."
        if stanford_ready_for_gbrain
        else (
            f"Do not request Stanford school verification yet. Drain or explicitly justify {open_gap_rows} denominator gaps "
            f"through the non-mutating school gap-resolution manifest, exact packets, or approved disposition recourse: "
            f"{'retain approved evidence for ' if stale_noop_closure_approved else 'drain '}{second_hop_residual_phrase}, "
            f"{'' if nuclear_radiology_fellow_approved else 'the Nuclear Radiology fellow denominator-mapping residual, '}"
            f"{'retain approved shared-source residual disposition evidence, ' if shared_residual_approved else 'General Surgery team-page exclusion or scope mapping, '}"
            f"{family_sports_phrase}"
            f"{allergy_immunology_phrase}"
            f"{hand_surgery_phrase}"
            f"{unsupported_label_phrase}"
            f"{parser_phrase}and {lifecycle_identity_phrase}."
        )
    )
    stanford_people = sqlite_scalar(
        conn,
        "SELECT COUNT(*) FROM people WHERE institution = ?",
        ("Stanford University School of Medicine",),
    )
    stanford_training_states = sqlite_scalar(
        conn,
        "SELECT COUNT(*) FROM person_training_states WHERE source_key LIKE 'stanford%'",
    )
    return {
        "dossier_key": "school_readiness_dossier_" + sha_key(f"{school_key}|{sponsoring_institution}"),
        "school_key": school_key,
        "school_name": school_name,
        "sponsoring_institution": sponsoring_institution,
        "dossier_status": (
            "gbrain_verified_next_lane_approved"
            if stanford_school_verified
            else "ready_for_gbrain_school_verification"
            if stanford_ready_for_gbrain
            else "lane_opened_denominator_discovery_incomplete"
        ),
        "gbrain_approval_status": (
            "stanford_school_verified_next_lane_approved" if stanford_school_verified else "stanford_school_not_submitted"
        ),
        "verification_posture": (
            "school_verified_by_gbrain"
            if stanford_school_verified
            else "ready_for_gbrain_school_verification_not_verified"
            if stanford_ready_for_gbrain
            else "lane_opened_school_not_verified"
        ),
        "manifest_rows": str(len(school_manifest)),
        "open_manifest_blocker_rows": str(open_manifest_blockers),
        "min_maturity_level": str(min_maturity),
        "coverage_program_rows": str(coverage_program_rows),
        "covered_program_rows": str(covered_program_rows),
        "open_gap_rows": str(open_gap_rows),
        "action_queue_rows": str(open_gap_rows),
        "reproducibility_status": "ok" if repro_ok else "failed",
        "warehouse_people": str(stanford_people),
        "warehouse_training_events": str(stanford_training_states),
        "required_next_action": next_action,
        "included_artifacts_json": dumps(included_artifacts),
        "blocker_summary_json": dumps(blocker_summary),
        "evidence_json": dumps(evidence),
        "generated_at": generated_at,
    }


def ensure_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS school_readiness_dossiers (
          dossier_key TEXT PRIMARY KEY,
          school_key TEXT,
          school_name TEXT NOT NULL,
          sponsoring_institution TEXT NOT NULL,
          dossier_status TEXT NOT NULL,
          gbrain_approval_status TEXT NOT NULL,
          verification_posture TEXT NOT NULL,
          manifest_rows INTEGER NOT NULL DEFAULT 0,
          open_manifest_blocker_rows INTEGER NOT NULL DEFAULT 0,
          min_maturity_level INTEGER NOT NULL DEFAULT 0,
          coverage_program_rows INTEGER NOT NULL DEFAULT 0,
          covered_program_rows INTEGER NOT NULL DEFAULT 0,
          open_gap_rows INTEGER NOT NULL DEFAULT 0,
          action_queue_rows INTEGER NOT NULL DEFAULT 0,
          reproducibility_status TEXT NOT NULL,
          warehouse_people INTEGER NOT NULL DEFAULT 0,
          warehouse_training_events INTEGER NOT NULL DEFAULT 0,
          required_next_action TEXT NOT NULL,
          included_artifacts_json TEXT NOT NULL,
          blocker_summary_json TEXT NOT NULL,
          evidence_json TEXT NOT NULL,
          generated_at TEXT NOT NULL
        )
        """
    )


def insert_sqlite(rows: list[dict[str, str]]) -> None:
    if not DB.exists():
        return
    conn = sqlite3.connect(DB)
    with conn:
        ensure_table(conn)
        conn.execute("DELETE FROM school_readiness_dossiers")
        placeholders = ", ".join(":" + field for field in FIELDS)
        conn.executemany(
            f"INSERT INTO school_readiness_dossiers ({', '.join(FIELDS)}) VALUES ({placeholders})",
            rows,
        )
    conn.close()


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB)
    targets = target_lookup()
    gbrain = read_json(ARTIFACTS / "gbrain_consultation_ledger.json", {})
    reproducibility = read_json(ARTIFACTS / "warehouse_reproducibility_summary.json", {})
    manifest_rows = read_csv(ARTIFACTS / "school_capability_manifest.csv")
    hopkins_name = targets.get("JOHNS HOPKINS UNIVERSITY SCH OF MEDICINE", {}).get("school_name", "JOHNS HOPKINS UNIVERSITY SCH OF MEDICINE")
    ucsf_name = targets.get("UNIV OF CALIFORNIA SAN FRAN SCH OF MED", {}).get("school_name", "UNIV OF CALIFORNIA SAN FRAN SCH OF MED")
    washu_name = targets.get("WASHINGTON UNIVERSITY SCH OF MEDICINE", {}).get("school_name", "WASHINGTON UNIVERSITY SCH OF MEDICINE")
    yale_name = targets.get("YALE UNIVERSITY SCH OF MEDICINE", {}).get("school_name", "YALE UNIVERSITY SCH OF MEDICINE")
    penn_name = targets.get("UNIV OF PENNSYLVANIA SCH OF MEDICINE", {}).get("school_name", "UNIV OF PENNSYLVANIA SCH OF MEDICINE")
    vanderbilt_name = targets.get("VANDERBILT UNIVERSITY SCH OF MEDICINE", {}).get("school_name", "VANDERBILT UNIVERSITY SCH OF MEDICINE")
    stanford_name = targets.get("STANFORD UNIVERSITY SCH OF MEDICINE", {}).get("school_name", "STANFORD UNIVERSITY SCH OF MEDICINE")
    rows = [
        build_dossier(
            conn=conn,
            school_key=targets.get("JOHNS HOPKINS UNIVERSITY SCH OF MEDICINE", {}).get("school_key", "brimr_2024_school_006"),
            school_name=hopkins_name,
            sponsoring_institution="Johns Hopkins University School of Medicine",
            generated_at=generated_at,
            gbrain_status=school_gbrain_status(gbrain, hopkins_name),
            gbrain=gbrain,
            manifest_rows=manifest_rows,
            reproducibility=reproducibility,
        ),
        build_dossier(
            conn=conn,
            school_key=targets.get("UNIV OF CALIFORNIA SAN FRAN SCH OF MED", {}).get("school_key", "brimr_2024_school_001"),
            school_name=ucsf_name,
            sponsoring_institution="University of California, San Francisco School of Medicine",
            generated_at=generated_at,
            gbrain_status=school_gbrain_status(gbrain, ucsf_name),
            gbrain=gbrain,
            manifest_rows=manifest_rows,
            reproducibility=reproducibility,
        ),
        build_dossier(
            conn=conn,
            school_key=targets.get("WASHINGTON UNIVERSITY SCH OF MEDICINE", {}).get("school_key", "brimr_2024_school_002"),
            school_name=washu_name,
            sponsoring_institution="WashU/BJH/SLCH/MBMC Graduate Medical Education Consortium",
            generated_at=generated_at,
            gbrain_status=school_gbrain_status(gbrain, washu_name),
            gbrain=gbrain,
            manifest_rows=manifest_rows,
            reproducibility=reproducibility,
        ),
        build_dossier(
            conn=conn,
            school_key=targets.get("YALE UNIVERSITY SCH OF MEDICINE", {}).get("school_key", "brimr_2024_school_003"),
            school_name=yale_name,
            sponsoring_institution="Yale-New Haven Medical Center",
            generated_at=generated_at,
            gbrain_status=school_gbrain_status(gbrain, yale_name),
            gbrain=gbrain,
            manifest_rows=manifest_rows,
            reproducibility=reproducibility,
        ),
        build_dossier(
            conn=conn,
            school_key=targets.get("UNIV OF PENNSYLVANIA SCH OF MEDICINE", {}).get("school_key", "brimr_2024_school_004"),
            school_name=penn_name,
            sponsoring_institution="Hospital of the University of Pennsylvania",
            generated_at=generated_at,
            gbrain_status=school_gbrain_status(gbrain, penn_name),
            gbrain=gbrain,
            manifest_rows=manifest_rows,
            reproducibility=reproducibility,
        ),
        build_dossier(
            conn=conn,
            school_key=targets.get("VANDERBILT UNIVERSITY SCH OF MEDICINE", {}).get("school_key", "brimr_2024_school_005"),
            school_name=vanderbilt_name,
            sponsoring_institution="Vanderbilt University Medical Center",
            generated_at=generated_at,
            gbrain_status=school_gbrain_status(gbrain, vanderbilt_name),
            gbrain=gbrain,
            manifest_rows=manifest_rows,
            reproducibility=reproducibility,
        ),
        build_stanford_dossier(
            conn=conn,
            school_key=targets.get("STANFORD UNIVERSITY SCH OF MEDICINE", {}).get("school_key", "brimr_2024_school_007"),
            school_name=stanford_name,
            generated_at=generated_at,
            gbrain=gbrain,
            manifest_rows=manifest_rows,
            reproducibility=reproducibility,
        ),
    ]
    conn.close()

    with CSV_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "generated_at": generated_at,
        "policy": (
            "Readiness dossiers are non-mutating verification packets. They wrap capability manifest state, "
            "official program coverage, action blockers, GBrain approval posture, and reproducibility evidence "
            "before a school can be submitted or marked verified."
        ),
        "rows": rows,
    }
    JSON_OUT.write_text(dumps(payload) + "\n", encoding="utf-8")
    summary = {
        "generated_at": generated_at,
        "dossier_rows": len(rows),
        "by_dossier_status": dict(Counter(row["dossier_status"] for row in rows)),
        "by_verification_posture": dict(Counter(row["verification_posture"] for row in rows)),
        "open_gap_rows": sum(int(row["open_gap_rows"]) for row in rows),
        "action_queue_rows": sum(int(row["action_queue_rows"]) for row in rows),
        "policy": payload["policy"],
    }
    SUMMARY_OUT.write_text(dumps(summary) + "\n", encoding="utf-8")
    insert_sqlite(rows)
    print(dumps({"school_readiness_dossiers": len(rows), "by_dossier_status": summary["by_dossier_status"]}))


if __name__ == "__main__":
    main()
