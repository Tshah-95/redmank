#!/usr/bin/env python3
"""Materialize the public top-50 roster-engine operating snapshot."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

OUT_JSON = ARTIFACTS / "top50_engine_operating_snapshot.json"
OUT_MD = RESEARCH / "top50-engine-operating-snapshot-2026-06-09.md"

SUMMARY_FILES = {
    "target_registry": ARTIFACTS / "top50_medical_school_targets_summary.json",
    "school_verification_registry": ARTIFACTS / "school_verification_registry_summary.json",
    "school_capability_manifest": ARTIFACTS / "school_capability_manifest_summary.json",
    "school_readiness_dossiers": ARTIFACTS / "school_readiness_dossier_summary.json",
    "school_gap_resolution_manifest": ARTIFACTS / "school_gap_resolution_manifest_summary.json",
    "school_gap_resolution_batches": ARTIFACTS / "school_gap_resolution_batch_summary.json",
    "school_gap_resolution_batch_packets": ARTIFACTS / "school_gap_resolution_batch_packet_summary.json",
    "source_discovery_playbook": ARTIFACTS / "top50_scraper_source_discovery_playbook_summary.json",
    "vanderbilt_targeted_source_discovery": ARTIFACTS / "vanderbilt_targeted_gap_source_discovery_workbench_summary.json",
    "vanderbilt_parser_scope_review": ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet_summary.json",
    "vanderbilt_parser_scope_execution_workbench": ARTIFACTS
    / "vanderbilt_targeted_parser_scope_execution_workbench_summary.json",
    "vanderbilt_targeted_route_observations": ARTIFACTS / "vanderbilt_targeted_route_observation_summary.json",
    "vanderbilt_targeted_route_parser_scope_packet": ARTIFACTS
    / "vanderbilt_targeted_route_parser_scope_packet_summary.json",
    "vanderbilt_route_parser_scope_verification_packet": ARTIFACTS
    / "vanderbilt_route_parser_scope_verification_packet_summary.json",
    "vanderbilt_approved_parser_scope_next_packets": ARTIFACTS
    / "vanderbilt_approved_parser_scope_next_packet_summary.json",
    "vanderbilt_parser_scope_execution_evidence": ARTIFACTS
    / "vanderbilt_parser_scope_execution_evidence_summary.json",
    "vanderbilt_parser_scope_decision_packets": ARTIFACTS
    / "vanderbilt_parser_scope_decision_packet_summary.json",
    "vanderbilt_candidate_only_parser_outputs": ARTIFACTS
    / "vanderbilt_candidate_only_parser_output_summary.json",
    "vanderbilt_candidate_parser_output_verification": ARTIFACTS
    / "vanderbilt_candidate_parser_output_verification_summary.json",
    "vanderbilt_candidate_review_queue_approval_packet": ARTIFACTS
    / "vanderbilt_candidate_review_queue_approval_packet_summary.json",
    "vanderbilt_candidate_review_queues": ARTIFACTS / "vanderbilt_candidate_review_queue_summary.json",
    "vanderbilt_candidate_review_decision_scaffold": ARTIFACTS
    / "vanderbilt_candidate_review_decision_scaffold_summary.json",
    "vanderbilt_candidate_review_scaffold_verification": ARTIFACTS
    / "vanderbilt_candidate_review_scaffold_verification_summary.json",
    "vanderbilt_candidate_reviewer_decision_audit": ARTIFACTS
    / "vanderbilt_candidate_reviewer_decision_audit_summary.json",
    "vanderbilt_candidate_review_batch_packets": ARTIFACTS
    / "vanderbilt_candidate_review_batch_packet_summary.json",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_json(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def summary_ref(name: str, path: Path) -> dict[str, object]:
    summary = read_json(path)
    keys = [
        "rowset_sha256",
        "targets",
        "rows",
        "registry_rows",
        "verified_school_rows",
        "manifest_rows",
        "dossier_rows",
        "open_gap_rows",
        "workbench_rows",
        "review_rows",
        "unique_fetch_urls",
        "observation_rows",
        "unique_observed_urls",
        "packet_rows",
        "verification_rows",
        "next_packet_rows",
        "execution_evidence_rows",
        "decision_rows",
        "parser_output_rows",
        "candidate_fingerprint_rows",
        "review_queue_rows",
        "decision_scaffold_rows",
        "manual_decision_template_rows",
        "audit_rows",
        "batch_packet_rows",
        "pending_rows",
        "valid_non_mutating_rows",
        "invalid_rows",
        "decision_row_count",
        "total_candidate_entity_count",
        "pass_rows",
        "fail_rows",
        "mutation_allowed",
        "gbrain_approval_verified",
        "gbrain_registration_status",
        "gbrain_approval_status",
        "gbrain_strategy_effect",
    ]
    return {
        "name": name,
        "summary_json": rel(path),
        "exists": path.exists(),
        "selected_summary": {key: summary[key] for key in keys if key in summary},
    }


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    summaries = {name: read_json(path) for name, path in SUMMARY_FILES.items()}
    target_summary = summaries["target_registry"]
    verification_summary = summaries["school_verification_registry"]
    gap_summary = summaries["school_gap_resolution_manifest"]
    playbook_summary = summaries["source_discovery_playbook"]
    vanderbilt_parser_summary = summaries["vanderbilt_parser_scope_review"]
    vanderbilt_execution_summary = summaries["vanderbilt_parser_scope_execution_workbench"]
    vanderbilt_route_summary = summaries["vanderbilt_targeted_route_observations"]
    vanderbilt_parser_scope_packet_summary = summaries["vanderbilt_targeted_route_parser_scope_packet"]
    vanderbilt_verification_summary = summaries["vanderbilt_route_parser_scope_verification_packet"]
    vanderbilt_next_packet_summary = summaries["vanderbilt_approved_parser_scope_next_packets"]
    vanderbilt_execution_evidence_summary = summaries["vanderbilt_parser_scope_execution_evidence"]
    vanderbilt_decision_summary = summaries["vanderbilt_parser_scope_decision_packets"]
    vanderbilt_candidate_parser_summary = summaries["vanderbilt_candidate_only_parser_outputs"]
    vanderbilt_candidate_verification_summary = summaries["vanderbilt_candidate_parser_output_verification"]
    vanderbilt_review_queue_approval_summary = summaries["vanderbilt_candidate_review_queue_approval_packet"]
    vanderbilt_review_queue_summary = summaries["vanderbilt_candidate_review_queues"]
    vanderbilt_review_scaffold_summary = summaries["vanderbilt_candidate_review_decision_scaffold"]
    vanderbilt_review_scaffold_verification_summary = summaries["vanderbilt_candidate_review_scaffold_verification"]
    vanderbilt_reviewer_decision_audit_summary = summaries["vanderbilt_candidate_reviewer_decision_audit"]
    vanderbilt_review_batch_packet_summary = summaries["vanderbilt_candidate_review_batch_packets"]
    parser_scope_status = vanderbilt_parser_scope_packet_summary.get("gbrain_approval_status", "")
    if vanderbilt_review_batch_packet_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_for_bounded_vanderbilt_manual_review_packets"
        parser_scope_next_action = (
            "Use the bounded Vanderbilt candidate review batch packets to enter non-mutating reviewer decisions in "
            "artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit and batch "
            "packet materializer. Any accepted person rows, denominator closure, identity reconciliation, parser "
            "acceptance, or scope closure still requires a later exact approval packet."
        )
        parser_scope_source_artifact = vanderbilt_review_batch_packet_summary.get(
            "csv", "artifacts/data/vanderbilt_candidate_review_batch_packets.csv"
        )
        parser_scope_rowset = vanderbilt_review_batch_packet_summary.get("rowset_sha256", "")
    elif vanderbilt_reviewer_decision_audit_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_for_manual_vanderbilt_candidate_review_input"
        parser_scope_next_action = (
            "Enter non-mutating reviewer decisions in the Vanderbilt manual decision template, then re-run the "
            "decision audit. Any accepted person rows, denominator closure, identity reconciliation, parser "
            "acceptance, or scope closure still requires a later exact approval packet."
        )
        parser_scope_source_artifact = vanderbilt_reviewer_decision_audit_summary.get(
            "manual_decisions_csv", "artifacts/data/vanderbilt_candidate_reviewer_decisions.csv"
        )
        parser_scope_rowset = vanderbilt_reviewer_decision_audit_summary.get("rowset_sha256", "")
    elif vanderbilt_review_scaffold_verification_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_non_mutating_manual_review_decisions"
        parser_scope_next_action = (
            "Use the verified Vanderbilt reviewer decision scaffold and blank manual decision template for "
            "non-mutating candidate/scope/recourse review. Any accepted person rows, denominator closure, or "
            "identity reconciliation still requires a later exact approval packet."
        )
        parser_scope_source_artifact = vanderbilt_review_scaffold_summary.get(
            "csv", "artifacts/data/vanderbilt_candidate_review_decision_scaffold.csv"
        )
        parser_scope_rowset = vanderbilt_review_scaffold_summary.get("rowset_sha256", "")
    elif vanderbilt_review_scaffold_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_non_mutating_review_scaffold_verification"
        parser_scope_next_action = (
            "Verify the Vanderbilt candidate review decision scaffold before any manual decisions are entered."
        )
        parser_scope_source_artifact = vanderbilt_review_scaffold_summary.get(
            "csv", "artifacts/data/vanderbilt_candidate_review_decision_scaffold.csv"
        )
        parser_scope_rowset = vanderbilt_review_scaffold_summary.get("rowset_sha256", "")
    elif vanderbilt_review_queue_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_non_mutating_candidate_review_queue_execution"
        parser_scope_next_action = (
            "Execute Vanderbilt candidate fingerprint, linked-scope, and route-recourse review queues. Reviewer "
            "actions must stay non-mutating; any person ingestion, denominator closure, or identity reconciliation "
            "requires a later exact approval packet."
        )
        parser_scope_source_artifact = vanderbilt_review_queue_summary.get(
            "csv", "artifacts/data/vanderbilt_candidate_review_queues.csv"
        )
        parser_scope_rowset = vanderbilt_review_queue_summary.get("rowset_sha256", "")
    elif vanderbilt_review_queue_approval_summary.get("rowset_sha256"):
        parser_scope_lane_status = str(
            vanderbilt_review_queue_approval_summary.get("gbrain_approval_status", "pending_review_queue_approval")
        )
        parser_scope_next_action = (
            "Materialize approved non-mutating review queues from candidate fingerprints, linked-scope metadata, "
            "and route recourse rows. Do not accept people or close denominators."
        )
        parser_scope_source_artifact = vanderbilt_review_queue_approval_summary.get(
            "csv", "artifacts/data/vanderbilt_candidate_review_queue_approval_packet.csv"
        )
        parser_scope_rowset = vanderbilt_review_queue_approval_summary.get("rowset_sha256", "")
    elif vanderbilt_candidate_verification_summary.get("rowset_sha256"):
        parser_scope_lane_status = str(
            vanderbilt_candidate_verification_summary.get("gbrain_registration_status", "pending_candidate_output_verification")
        )
        parser_scope_next_action = (
            "Use the approved candidate-output verification packet to request exact review-queue materialization. "
            "Do not create reviewer queues or accept people before approval."
        )
        parser_scope_source_artifact = vanderbilt_candidate_verification_summary.get(
            "csv", "artifacts/data/vanderbilt_candidate_parser_output_verification.csv"
        )
        parser_scope_rowset = vanderbilt_candidate_verification_summary.get("rowset_sha256", "")
    elif vanderbilt_candidate_parser_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_non_mutating_candidate_parser_output_verification"
        parser_scope_next_action = (
            "Verify the candidate-only Vanderbilt parser outputs, preserve raw-name-free diagnostics, and build the "
            "next exact approval packet before any person ingestion, denominator closure, or accepted roster rows."
        )
        parser_scope_source_artifact = vanderbilt_candidate_parser_summary.get(
            "csv", "artifacts/data/vanderbilt_candidate_only_parser_outputs.csv"
        )
        parser_scope_rowset = vanderbilt_candidate_parser_summary.get("rowset_sha256", "")
    elif vanderbilt_decision_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_exact_parser_implementation_or_scope_acceptance_approval_packet"
        parser_scope_next_action = (
            "Use the parser/scope decision packets to request exact approval for candidate-only parser "
            "implementation, accepted scope dispositions, General Surgery parser-build review, and Orthopaedic "
            "route replacement/recourse. Do not implement parsers or accept people before that exact approval."
        )
        parser_scope_source_artifact = vanderbilt_decision_summary.get(
            "csv", "artifacts/data/vanderbilt_parser_scope_decision_packets.csv"
        )
        parser_scope_rowset = vanderbilt_decision_summary.get("rowset_sha256", "")
    elif vanderbilt_execution_evidence_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_non_mutating_parser_spec_and_scope_decision_packet"
        parser_scope_next_action = (
            "Use the parser/scope execution evidence to materialize parser-family specs, linked-route scope "
            "decisions, General Surgery rendered-review disposition, and Orthopaedic recourse packets. Keep all "
            "candidate entities as counts/hashes until a later exact person-ingestion/denominator approval exists."
        )
        parser_scope_source_artifact = vanderbilt_execution_evidence_summary.get(
            "csv", "artifacts/data/vanderbilt_parser_scope_execution_evidence.csv"
        )
        parser_scope_rowset = vanderbilt_execution_evidence_summary.get("rowset_sha256", "")
    elif vanderbilt_next_packet_summary.get("rowset_sha256"):
        parser_scope_lane_status = "ready_non_mutating_parser_build_scope_and_recourse_execution"
        parser_scope_next_action = (
            "Use the approved next-packet ledger to execute source-specific parser-build review, linked-route "
            "scope disposition, General Surgery rendered review, and route recourse work. Keep all outputs "
            "candidate-only until a later exact person-ingestion/denominator approval exists."
        )
        parser_scope_source_artifact = vanderbilt_next_packet_summary.get(
            "csv", "artifacts/data/vanderbilt_approved_parser_scope_next_packets.csv"
        )
        parser_scope_rowset = vanderbilt_next_packet_summary.get("rowset_sha256", "")
    elif parser_scope_status == "denied_needs_verification_documentation":
        parser_scope_lane_status = "denied_needs_verification_documentation"
        parser_scope_next_action = (
            "Build verification documentation/registration for the exact route parser/scope packet artifact and "
            "rowset, then resubmit the same non-mutating approval boundary. Do not build parser-acceptance "
            "artifacts while denied."
        )
        parser_scope_source_artifact = vanderbilt_parser_scope_packet_summary.get(
            "csv", "artifacts/data/vanderbilt_targeted_route_parser_scope_packet.csv"
        )
        parser_scope_rowset = vanderbilt_parser_scope_packet_summary.get("rowset_sha256", "")
    elif parser_scope_status == "approved_exact_non_mutating_next_artifact_lane":
        parser_scope_lane_status = "approved_non_mutating_next_artifacts_ready"
        parser_scope_next_action = (
            "Materialize the approved non-mutating source-specific parser-build review packets, linked-route "
            "scope-disposition packets, General Surgery rendered-review packet, and route retry/recourse packet. "
            "Do not ingest people, accept parser output as people, rewrite URLs, or close denominators."
        )
        parser_scope_source_artifact = vanderbilt_parser_scope_packet_summary.get(
            "csv", "artifacts/data/vanderbilt_targeted_route_parser_scope_packet.csv"
        )
        parser_scope_rowset = vanderbilt_parser_scope_packet_summary.get("rowset_sha256", "")
    else:
        parser_scope_lane_status = str(parser_scope_status or "pending_exact_gbrain_approval_line")
        parser_scope_next_action = (
            "Submit the exact parser/scope packet to GBrain. If approved, build only the named non-mutating "
            "parser-build, scope-disposition, General Surgery rendered-review, and recourse artifacts. Do not "
            "ingest people, rewrite URLs, or close denominators without a later exact approval."
        )
        parser_scope_source_artifact = vanderbilt_parser_scope_packet_summary.get(
            "csv", "artifacts/data/vanderbilt_targeted_route_parser_scope_packet.csv"
        )
        parser_scope_rowset = vanderbilt_parser_scope_packet_summary.get("rowset_sha256", "")

    next_lanes = [
        {
            "lane": "vanderbilt_targeted_route_parser_scope_gbrain_approval",
            "status": parser_scope_lane_status,
            "source_artifact": parser_scope_source_artifact,
            "rowset_sha256": parser_scope_rowset,
            "recommended_next_action": parser_scope_next_action,
        },
        {
            "lane": "vanderbilt_active_gap_resolution_manifest",
            "status": "active_non_mutating_discovery_queue",
            "source_artifact": gap_summary.get("csv", "artifacts/data/school_gap_resolution_manifest.csv"),
            "rowset_sha256": gap_summary.get("rowset_sha256", ""),
            "recommended_next_action": (
                "Use the Vanderbilt-only active gap manifest to choose bounded source-discovery, route-inspection, "
                "rendered-review, or closure-packet work."
            ),
        },
    ]

    snapshot = {
        "generated_at": generated_at,
        "json": rel(OUT_JSON),
        "markdown": rel(OUT_MD),
        "target_registry": {
            "target_count": target_summary.get("targets", 0),
            "rowset_sha256": target_summary.get("rowset_sha256", ""),
            "basis": target_summary.get("target_basis", ""),
        },
        "school_verification": {
            "verified_school_rows": verification_summary.get("verified_school_rows", 0),
            "registry_rowset_sha256": verification_summary.get("rowset_sha256", ""),
            "source_summary_files": verification_summary.get("source_summary_files", []),
        },
        "active_gap_resolution": {
            "open_gap_rows": gap_summary.get("open_gap_rows", 0),
            "school_priority_order": gap_summary.get("school_priority_order", []),
            "suppressed_verified_school_raw_gap_rows_by_school": gap_summary.get("suppressed_verified_school_raw_gap_rows_by_school", {}),
            "gbrain_strategy_effect": gap_summary.get("gbrain_strategy_effect", ""),
        },
        "source_discovery_playbook": {
            "rows": playbook_summary.get("rows", 0),
            "rowset_sha256": playbook_summary.get("rowset_sha256", ""),
            "vanderbilt_open_gap_rows_represented": playbook_summary.get("vanderbilt_open_gap_rows_represented", 0),
            "gbrain_approval_verified": playbook_summary.get("gbrain_approval_verified", False),
        },
        "next_lanes": next_lanes,
        "vanderbilt_targeted_parser_scope": {
            "review_packet_rows": vanderbilt_parser_summary.get("review_rows", 0),
            "review_packet_rowset_sha256": vanderbilt_parser_summary.get("rowset_sha256", ""),
            "execution_workbench_rows": vanderbilt_execution_summary.get("workbench_rows", 0),
            "execution_workbench_unique_fetch_urls": vanderbilt_execution_summary.get("unique_fetch_urls", 0),
            "execution_workbench_rowset_sha256": vanderbilt_execution_summary.get("rowset_sha256", ""),
            "route_observation_rows": vanderbilt_route_summary.get("observation_rows", 0),
            "route_observation_unique_urls": vanderbilt_route_summary.get("unique_observed_urls", 0),
            "route_observation_rowset_sha256": vanderbilt_route_summary.get("rowset_sha256", ""),
            "route_parser_scope_packet_rows": vanderbilt_parser_scope_packet_summary.get("packet_rows", 0),
            "route_parser_scope_packet_rowset_sha256": vanderbilt_parser_scope_packet_summary.get("rowset_sha256", ""),
            "route_parser_scope_packet_gbrain_status": vanderbilt_parser_scope_packet_summary.get(
                "gbrain_approval_status", ""
            ),
            "route_parser_scope_verification_rows": vanderbilt_verification_summary.get("verification_rows", 0),
            "route_parser_scope_verification_rowset_sha256": vanderbilt_verification_summary.get("rowset_sha256", ""),
            "route_parser_scope_verification_gbrain_status": vanderbilt_verification_summary.get(
                "gbrain_registration_status", ""
            ),
            "approved_next_packet_rows": vanderbilt_next_packet_summary.get("next_packet_rows", 0),
            "approved_next_packet_rowset_sha256": vanderbilt_next_packet_summary.get("rowset_sha256", ""),
            "parser_scope_execution_evidence_rows": vanderbilt_execution_evidence_summary.get(
                "execution_evidence_rows", 0
            ),
            "parser_scope_execution_evidence_total_candidate_count": vanderbilt_execution_evidence_summary.get(
                "total_candidate_entity_count", 0
            ),
            "parser_scope_execution_evidence_rowset_sha256": vanderbilt_execution_evidence_summary.get(
                "rowset_sha256", ""
            ),
            "parser_scope_decision_rows": vanderbilt_decision_summary.get("decision_rows", 0),
            "parser_scope_decision_rowset_sha256": vanderbilt_decision_summary.get("rowset_sha256", ""),
            "candidate_only_parser_output_rows": vanderbilt_candidate_parser_summary.get("parser_output_rows", 0),
            "candidate_only_parser_fingerprint_rows": vanderbilt_candidate_parser_summary.get(
                "candidate_fingerprint_rows", 0
            ),
            "candidate_only_parser_output_rowset_sha256": vanderbilt_candidate_parser_summary.get("rowset_sha256", ""),
            "candidate_parser_output_verification_rows": vanderbilt_candidate_verification_summary.get(
                "verification_rows", 0
            ),
            "candidate_parser_output_verification_pass_rows": vanderbilt_candidate_verification_summary.get(
                "pass_rows", 0
            ),
            "candidate_parser_output_verification_fail_rows": vanderbilt_candidate_verification_summary.get(
                "fail_rows", 0
            ),
            "candidate_parser_output_verification_rowset_sha256": vanderbilt_candidate_verification_summary.get(
                "rowset_sha256", ""
            ),
            "candidate_review_queue_approval_rows": vanderbilt_review_queue_approval_summary.get("approval_rows", 0),
            "candidate_review_queue_approval_status": vanderbilt_review_queue_approval_summary.get(
                "gbrain_approval_status", ""
            ),
            "candidate_review_queue_approval_rowset_sha256": vanderbilt_review_queue_approval_summary.get(
                "rowset_sha256", ""
            ),
            "candidate_review_queue_rows": vanderbilt_review_queue_summary.get("review_queue_rows", 0),
            "candidate_review_queue_rowset_sha256": vanderbilt_review_queue_summary.get("rowset_sha256", ""),
            "candidate_review_decision_scaffold_rows": vanderbilt_review_scaffold_summary.get(
                "decision_scaffold_rows", 0
            ),
            "candidate_review_manual_decision_template_rows": vanderbilt_review_scaffold_summary.get(
                "manual_decision_template_rows", 0
            ),
            "candidate_review_decision_scaffold_rowset_sha256": vanderbilt_review_scaffold_summary.get(
                "rowset_sha256", ""
            ),
            "candidate_review_scaffold_verification_rows": vanderbilt_review_scaffold_verification_summary.get(
                "verification_rows", 0
            ),
            "candidate_review_scaffold_verification_pass_rows": vanderbilt_review_scaffold_verification_summary.get(
                "pass_rows", 0
            ),
            "candidate_review_scaffold_verification_fail_rows": vanderbilt_review_scaffold_verification_summary.get(
                "fail_rows", 0
            ),
            "candidate_review_scaffold_verification_rowset_sha256": vanderbilt_review_scaffold_verification_summary.get(
                "rowset_sha256", ""
            ),
            "candidate_reviewer_decision_audit_rows": vanderbilt_reviewer_decision_audit_summary.get("audit_rows", 0),
            "candidate_reviewer_decision_pending_rows": vanderbilt_reviewer_decision_audit_summary.get(
                "pending_rows", 0
            ),
            "candidate_reviewer_decision_valid_rows": vanderbilt_reviewer_decision_audit_summary.get(
                "valid_non_mutating_rows", 0
            ),
            "candidate_reviewer_decision_invalid_rows": vanderbilt_reviewer_decision_audit_summary.get(
                "invalid_rows", 0
            ),
            "candidate_reviewer_decision_audit_rowset_sha256": vanderbilt_reviewer_decision_audit_summary.get(
                "rowset_sha256", ""
            ),
            "candidate_review_batch_packet_rows": vanderbilt_review_batch_packet_summary.get("batch_packet_rows", 0),
            "candidate_review_batch_packet_decision_rows": vanderbilt_review_batch_packet_summary.get(
                "decision_row_count", 0
            ),
            "candidate_review_batch_packet_pending_rows": vanderbilt_review_batch_packet_summary.get(
                "pending_decision_rows", 0
            ),
            "candidate_review_batch_packet_invalid_rows": vanderbilt_review_batch_packet_summary.get(
                "invalid_decision_rows", 0
            ),
            "candidate_review_batch_packet_rowset_sha256": vanderbilt_review_batch_packet_summary.get(
                "rowset_sha256", ""
            ),
            "candidate_review_batch_packet_gbrain_status": vanderbilt_review_batch_packet_summary.get(
                "gbrain_approval_status", ""
            ),
        },
        "mutation_allowed": False,
        "not_approved": [
            "person_ingestion",
            "training_state_mutation",
            "denominator_closure",
            "school_verification_without_exact_gbrain_packet",
            "url_rewrite",
            "unsupported_label_ingestion",
            "profile_contact_research_fact_acceptance",
            "unique_person_identity_collapse",
        ],
        "public_safety_policy": (
            "This snapshot is an operating index over committed public artifacts. It does not include raw GBrain "
            "HTTP responses, browser dumps, debug databases, or raw BRIMR workbooks."
        ),
        "summary_refs": [summary_ref(name, path) for name, path in SUMMARY_FILES.items()],
    }
    snapshot["rowset_sha256"] = sha256_json(
        {
            "target_registry": snapshot["target_registry"],
            "school_verification": snapshot["school_verification"],
            "active_gap_resolution": snapshot["active_gap_resolution"],
            "source_discovery_playbook": snapshot["source_discovery_playbook"],
            "vanderbilt_targeted_parser_scope": snapshot["vanderbilt_targeted_parser_scope"],
            "next_lanes": snapshot["next_lanes"],
            "mutation_allowed": snapshot["mutation_allowed"],
        }
    )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(snapshot, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Top50 Engine Operating Snapshot",
        "created_at: " + generated_at,
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Top50 Engine Operating Snapshot",
        "",
        "## Boundary",
        "",
        snapshot["public_safety_policy"],
        "",
        "This snapshot is non-mutating and authorizes no person ingestion, training-state mutation, denominator closure, URL rewrite, enrichment acceptance, or identity collapse.",
        "",
        "## Current State",
        "",
        "```json",
        json.dumps(
            {
                "target_registry": snapshot["target_registry"],
                "school_verification": snapshot["school_verification"],
                "active_gap_resolution": snapshot["active_gap_resolution"],
                "source_discovery_playbook": snapshot["source_discovery_playbook"],
                "vanderbilt_targeted_parser_scope": snapshot["vanderbilt_targeted_parser_scope"],
                "rowset_sha256": snapshot["rowset_sha256"],
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Next Lanes",
        "",
        "| lane | status | artifact | rowset | next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for lane in next_lanes:
        lines.append(
            "| {lane} | {status} | {source_artifact} | {rowset_sha256} | {recommended_next_action} |".format(**lane)
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"rowset_sha256": snapshot["rowset_sha256"], "next_lanes": len(next_lanes)}, sort_keys=True))


if __name__ == "__main__":
    main()
