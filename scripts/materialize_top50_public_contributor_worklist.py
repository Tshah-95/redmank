#!/usr/bin/env python3
"""Materialize a public-safe contributor worklist for the top-50 engine."""

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

VERIFICATION_SUMMARY = ARTIFACTS / "top50_public_clone_verification_summary.json"
SNAPSHOT_JSON = ARTIFACTS / "top50_engine_operating_snapshot.json"
BATCH_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_batch_packet_summary.json"
BATCH_CSV = ARTIFACTS / "vanderbilt_candidate_review_batch_packets.csv"
OPERATOR_SUMMARY = ARTIFACTS / "vanderbilt_public_reviewer_operator_packet_summary.json"
OPERATOR_CSV = ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.csv"
DECISION_AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"
PATCH_TEMPLATE_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_template_summary.json"
PATCH_WORKBOOK_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_summary.json"
PATCH_SLICE_INDEX_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index_summary.json"
GAP_SLICE_INDEX_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_slice_index_summary.json"
GAP_REVIEW_TEMPLATE_SUMMARY = ARTIFACTS / "school_gap_resolution_review_template_summary.json"
GAP_REVIEW_TEMPLATE_VALIDATION_SUMMARY = ARTIFACTS / "school_gap_resolution_review_template_validation_summary.json"
GAP_TARGETED_REVIEW_PACKET_SUMMARY = ARTIFACTS / "school_gap_resolution_targeted_review_packet_summary.json"
GAP_TARGETED_REVIEW_PACKET_VALIDATION_SUMMARY = ARTIFACTS / "school_gap_resolution_targeted_review_packet_validation_summary.json"
GAP_PARSER_SCOPE_BRIDGE_SUMMARY = ARTIFACTS / "school_gap_resolution_parser_scope_bridge_summary.json"
GAP_CANDIDATE_OUTPUT_BRIDGE_SUMMARY = ARTIFACTS / "school_gap_resolution_candidate_output_bridge_summary.json"
GAP_REVIEW_QUEUE_BRIDGE_SUMMARY = ARTIFACTS / "school_gap_resolution_review_queue_bridge_summary.json"
EXECUTION_READINESS_BRIDGE_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge_summary.json"
BLANK_EXECUTION_VERIFICATION_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification_summary.json"
SLICE_PRIORITIZATION_SUMMARY = ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan_summary.json"
PRIORITY_INSTRUCTION_SUMMARY = ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet_summary.json"
PATCH_HELPER_FIXTURE_SUMMARY = ARTIFACTS / "vanderbilt_patch_helper_fixture_verification_summary.json"
PRIORITY_HANDOFF_SUMMARY = ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet_summary.json"
PRIORITY_HANDOFF_CSV = ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet.csv"
SYNTHETIC_HANDOFF_DEMO_SUMMARY = ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo_summary.json"
GAP_SUMMARY = ARTIFACTS / "school_gap_resolution_manifest_summary.json"
GAP_CSV = ARTIFACTS / "school_gap_resolution_manifest.csv"

OUT_CSV = ARTIFACTS / "top50_public_contributor_worklist.csv"
OUT_JSON = ARTIFACTS / "top50_public_contributor_worklist.json"
OUT_SUMMARY = ARTIFACTS / "top50_public_contributor_worklist_summary.json"
OUT_MD = RESEARCH / "top50-public-contributor-worklist-2026-06-09.md"

VERIFICATION_ROWSET_SHA256 = "da28ec6ac1e9a4df95c7f60c12fa9e6a8221ea639d50f27f86776ec194b871ba"
SNAPSHOT_ROWSET_SHA256 = "b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48"
BATCH_PACKET_ROWSET_SHA256 = "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f"
OPERATOR_PACKET_ROWSET_SHA256 = "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"
DECISION_AUDIT_ROWSET_SHA256 = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
PATCH_TEMPLATE_ROWSET_SHA256 = "5532d007555997f54d25884baba2f4e594d4ff1fa286301bfa6f87fc64caaa8d"
PATCH_WORKBOOK_ROWSET_SHA256 = "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3"
PATCH_SLICE_INDEX_ROWSET_SHA256 = "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4"
GAP_SLICE_INDEX_ROWSET_SHA256 = "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75"
GAP_REVIEW_TEMPLATE_ROWSET_SHA256 = "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782"
GAP_TARGETED_REVIEW_PACKET_ROWSET_SHA256 = "d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607"
GAP_PARSER_SCOPE_BRIDGE_ROWSET_SHA256 = "942d131072d56524c9e19832c084b9e2520e43e783e3a9c0c6e2ae30c0f06912"
GAP_CANDIDATE_OUTPUT_BRIDGE_ROWSET_SHA256 = "dfb141c1883d85fd6a8c7c0e015b939414788936eb13dbb04eecb9111ff5b843"
GAP_REVIEW_QUEUE_BRIDGE_ROWSET_SHA256 = "46c2b215f28819df10913fa35f7dff6e7f4afc4ec6c3598e7432088c3f34e10d"
EXECUTION_READINESS_BRIDGE_ROWSET_SHA256 = "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa"
BLANK_EXECUTION_VERIFICATION_ROWSET_SHA256 = "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e"
SLICE_PRIORITIZATION_PLAN_ROWSET_SHA256 = "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c"
PRIORITY_INSTRUCTION_PACKET_ROWSET_SHA256 = "dfe6c7081ac7c3c28ac6e8afcb736a2d16bc8a6cbd8cba1cbc38b420064ddd65"
PATCH_HELPER_FIXTURE_ROWSET_SHA256 = "9d87181804d6ade23ea3bd7fd322cdc7fdeab7b3078aade0921c8d2b2cab2825"
PRIORITY_HANDOFF_PACKET_ROWSET_SHA256 = "9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0"
SYNTHETIC_HANDOFF_DEMO_ROWSET_SHA256 = "81da7a86173eef52ee6fbc4afdf98ab3f33555b6d83f6c61be88bad61a211bb4"
GBRAIN_APPROVAL_LINE = "APPROVE top50_public_contributor_worklist_lane_approved"

MUTATION_POLICY = (
    "Non-mutating public contributor worklist for the top-50/Vanderbilt engine. It ranks bounded public-safe "
    "operator actions from committed verification, snapshot, Vanderbilt batch-packet, decision-audit, and gap "
    "manifest artifacts. It does not approve person ingestion, parser output as accepted people, training-state "
    "mutation, denominator closure, school verification, URL rewrite, unsupported-label ingestion, enrichment "
    "acceptance, raw dump publication, or unique-person identity collapse."
)

PROHIBITED_MUTATIONS = [
    "person_ingestion",
    "parser_output_as_accepted_people",
    "training_state_mutation",
    "denominator_closure",
    "school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "enrichment_acceptance",
    "raw_dump_publication",
    "unique_person_identity_collapse",
]

FIELDS = [
    "work_item_key",
    "execution_order",
    "action_lane",
    "action_status",
    "priority",
    "priority_band",
    "entity_type",
    "entity_key",
    "display_label",
    "impact_count",
    "source_artifact",
    "target_artifact",
    "required_next_evidence",
    "recommended_next_action",
    "verification_command",
    "success_condition",
    "approval_required_for",
    "prohibited_mutations",
    "source_rowset_sha256",
    "target_rowset_sha256",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "execution_order",
    "action_lane",
    "action_status",
    "priority",
    "priority_band",
    "entity_type",
    "entity_key",
    "display_label",
    "impact_count",
    "source_artifact",
    "target_artifact",
    "required_next_evidence",
    "recommended_next_action",
    "verification_command",
    "success_condition",
    "approval_required_for",
    "prohibited_mutations",
    "source_rowset_sha256",
    "target_rowset_sha256",
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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def priority_band(priority: int) -> str:
    if priority >= 900:
        return "critical"
    if priority >= 700:
        return "high"
    if priority >= 400:
        return "medium"
    return "low"


def semicolon(values: list[str]) -> str:
    return "; ".join(values)


def row(
    *,
    execution_order: int,
    action_lane: str,
    action_status: str,
    priority: int,
    entity_type: str,
    entity_key: str,
    display_label: str,
    impact_count: int,
    source_artifact: str,
    target_artifact: str,
    required_next_evidence: str,
    recommended_next_action: str,
    verification_command: str,
    success_condition: str,
    approval_required_for: list[str],
    source_rowset_sha256: str,
    target_rowset_sha256: str,
    evidence: dict[str, object],
    generated_at: str,
) -> dict[str, object]:
    return {
        "work_item_key": stable_key("top50_public_contributor_work_item", action_lane, entity_key, source_rowset_sha256),
        "execution_order": execution_order,
        "action_lane": action_lane,
        "action_status": action_status,
        "priority": priority,
        "priority_band": priority_band(priority),
        "entity_type": entity_type,
        "entity_key": entity_key,
        "display_label": display_label,
        "impact_count": impact_count,
        "source_artifact": source_artifact,
        "target_artifact": target_artifact,
        "required_next_evidence": required_next_evidence,
        "recommended_next_action": recommended_next_action,
        "verification_command": verification_command,
        "success_condition": success_condition,
        "approval_required_for": semicolon(approval_required_for),
        "prohibited_mutations": semicolon(PROHIBITED_MUTATIONS),
        "source_rowset_sha256": source_rowset_sha256,
        "target_rowset_sha256": target_rowset_sha256,
        "evidence_json": dumps(evidence),
        "mutation_policy": MUTATION_POLICY,
        "generated_at": generated_at,
    }


def verify_source_boundary() -> tuple[dict[str, object], ...]:
    verification_summary = read_json(VERIFICATION_SUMMARY)
    snapshot = read_json(SNAPSHOT_JSON)
    batch_summary = read_json(BATCH_SUMMARY)
    operator_summary = read_json(OPERATOR_SUMMARY)
    decision_audit_summary = read_json(DECISION_AUDIT_SUMMARY)
    patch_template_summary = read_json(PATCH_TEMPLATE_SUMMARY)
    patch_workbook_summary = read_json(PATCH_WORKBOOK_SUMMARY)
    patch_slice_index_summary = read_json(PATCH_SLICE_INDEX_SUMMARY)
    gap_slice_index_summary = read_json(GAP_SLICE_INDEX_SUMMARY)
    gap_review_template_summary = read_json(GAP_REVIEW_TEMPLATE_SUMMARY)
    gap_review_template_validation_summary = read_json(GAP_REVIEW_TEMPLATE_VALIDATION_SUMMARY)
    gap_targeted_review_packet_summary = read_json(GAP_TARGETED_REVIEW_PACKET_SUMMARY)
    gap_targeted_review_packet_validation_summary = read_json(GAP_TARGETED_REVIEW_PACKET_VALIDATION_SUMMARY)
    gap_parser_scope_bridge_summary = read_json(GAP_PARSER_SCOPE_BRIDGE_SUMMARY)
    gap_candidate_output_bridge_summary = read_json(GAP_CANDIDATE_OUTPUT_BRIDGE_SUMMARY)
    gap_review_queue_bridge_summary = read_json(GAP_REVIEW_QUEUE_BRIDGE_SUMMARY)
    execution_readiness_bridge_summary = read_json(EXECUTION_READINESS_BRIDGE_SUMMARY)
    blank_execution_verification_summary = read_json(BLANK_EXECUTION_VERIFICATION_SUMMARY)
    slice_prioritization_summary = read_json(SLICE_PRIORITIZATION_SUMMARY)
    priority_instruction_summary = read_json(PRIORITY_INSTRUCTION_SUMMARY)
    patch_helper_fixture_summary = read_json(PATCH_HELPER_FIXTURE_SUMMARY)
    priority_handoff_summary = read_json(PRIORITY_HANDOFF_SUMMARY)
    synthetic_handoff_demo_summary = read_json(SYNTHETIC_HANDOFF_DEMO_SUMMARY)
    gap_summary = read_json(GAP_SUMMARY)
    if not all(
        isinstance(item, dict)
        for item in [
            verification_summary,
            snapshot,
            batch_summary,
            operator_summary,
            decision_audit_summary,
            patch_template_summary,
            patch_workbook_summary,
            patch_slice_index_summary,
            gap_slice_index_summary,
            gap_review_template_summary,
            gap_review_template_validation_summary,
            gap_targeted_review_packet_summary,
            gap_targeted_review_packet_validation_summary,
            gap_parser_scope_bridge_summary,
            gap_candidate_output_bridge_summary,
            gap_review_queue_bridge_summary,
            execution_readiness_bridge_summary,
            blank_execution_verification_summary,
            slice_prioritization_summary,
            priority_instruction_summary,
            patch_helper_fixture_summary,
            priority_handoff_summary,
            synthetic_handoff_demo_summary,
            gap_summary,
        ]
    ):
        raise SystemExit("Expected public contributor worklist source summaries to be JSON objects.")
    checks = {
        "verification_rowset": verification_summary.get("rowset_sha256") == VERIFICATION_ROWSET_SHA256,
        "verification_passed": verification_summary.get("pass_rows") == verification_summary.get("verification_rows")
        and verification_summary.get("fail_rows") == 0,
        "snapshot_rowset": snapshot.get("rowset_sha256") == SNAPSHOT_ROWSET_SHA256,
        "snapshot_non_mutating": snapshot.get("mutation_allowed") is False,
        "batch_rowset": batch_summary.get("rowset_sha256") == BATCH_PACKET_ROWSET_SHA256,
        "batch_rows": batch_summary.get("batch_packet_rows") == 20 and batch_summary.get("decision_row_count") == 159,
        "operator_rowset": operator_summary.get("rowset_sha256") == OPERATOR_PACKET_ROWSET_SHA256,
        "operator_rows": operator_summary.get("operator_packet_rows") == 20
        and operator_summary.get("decision_row_count") == 159
        and operator_summary.get("missing_required_template_column_mentions") == 0,
        "decision_audit_rowset": decision_audit_summary.get("rowset_sha256") == DECISION_AUDIT_ROWSET_SHA256,
        "decision_audit_pending": decision_audit_summary.get("pending_rows") == 159
        and decision_audit_summary.get("invalid_rows") == 0,
        "patch_template_rowset": patch_template_summary.get("rowset_sha256") == PATCH_TEMPLATE_ROWSET_SHA256,
        "patch_template_blank": patch_template_summary.get("template_rows") == 159
        and patch_template_summary.get("blank_action_rows") == 159
        and patch_template_summary.get("valid_non_mutating_rows") == 0
        and patch_template_summary.get("mutation_allowed") is False,
        "patch_workbook_rowset": patch_workbook_summary.get("rowset_sha256") == PATCH_WORKBOOK_ROWSET_SHA256,
        "patch_workbook_blank": patch_workbook_summary.get("workbook_rows") == 159
        and patch_workbook_summary.get("decision_fingerprint_present_rows") == 159
        and patch_workbook_summary.get("blank_action_rows") == 159
        and patch_workbook_summary.get("valid_non_mutating_rows") == 0
        and patch_workbook_summary.get("mutation_allowed") is False,
        "patch_slice_index_rowset": patch_slice_index_summary.get("rowset_sha256") == PATCH_SLICE_INDEX_ROWSET_SHA256,
        "patch_slice_index_rows": patch_slice_index_summary.get("slice_index_rows") == 20
        and patch_slice_index_summary.get("workbook_rows_represented") == 159
        and patch_slice_index_summary.get("slice_outputs_default_tmp_only") is True
        and patch_slice_index_summary.get("mutation_allowed") is False,
        "gap_slice_index_rowset": gap_slice_index_summary.get("rowset_sha256") == GAP_SLICE_INDEX_ROWSET_SHA256,
        "gap_slice_index_rows": gap_slice_index_summary.get("slice_index_rows") == 21
        and gap_slice_index_summary.get("gap_rows_represented") == 113
        and gap_slice_index_summary.get("slice_outputs_default_tmp_only") is True
        and gap_slice_index_summary.get("mutation_allowed") is False,
        "gap_review_template_rowset": gap_review_template_summary.get("rowset_sha256")
        == GAP_REVIEW_TEMPLATE_ROWSET_SHA256,
        "gap_review_template_blank": gap_review_template_summary.get("review_template_rows") == 113
        and gap_review_template_summary.get("batch_rows_represented") == 21
        and gap_review_template_summary.get("blank_action_rows") == 113
        and gap_review_template_summary.get("valid_non_mutating_review_rows") == 0
        and gap_review_template_summary.get("mutation_allowed") is False,
        "gap_review_template_validation": gap_review_template_validation_summary.get("rowset_sha256")
        == GAP_REVIEW_TEMPLATE_ROWSET_SHA256
        and gap_review_template_validation_summary.get("template_rows") == 113
        and gap_review_template_validation_summary.get("pending_rows") == 113
        and gap_review_template_validation_summary.get("valid_non_mutating_rows") == 0
        and gap_review_template_validation_summary.get("invalid_rows") == 0
        and gap_review_template_validation_summary.get("mutation_allowed") is False,
        "gap_targeted_review_packet_rowset": gap_targeted_review_packet_summary.get("rowset_sha256")
        == GAP_TARGETED_REVIEW_PACKET_ROWSET_SHA256,
        "gap_targeted_review_packet_valid": gap_targeted_review_packet_summary.get("review_packet_rows") == 113
        and gap_targeted_review_packet_summary.get("filled_review_rows") == 19
        and gap_targeted_review_packet_summary.get("blank_review_rows") == 94
        and gap_targeted_review_packet_summary.get("mutation_allowed") is False,
        "gap_targeted_review_packet_validation": gap_targeted_review_packet_validation_summary.get("rowset_sha256")
        == GAP_TARGETED_REVIEW_PACKET_ROWSET_SHA256
        and gap_targeted_review_packet_validation_summary.get("template_rows") == 113
        and gap_targeted_review_packet_validation_summary.get("pending_rows") == 94
        and gap_targeted_review_packet_validation_summary.get("valid_non_mutating_rows") == 19
        and gap_targeted_review_packet_validation_summary.get("invalid_rows") == 0
        and gap_targeted_review_packet_validation_summary.get("mutation_allowed") is False,
        "gap_parser_scope_bridge_rowset": gap_parser_scope_bridge_summary.get("rowset_sha256")
        == GAP_PARSER_SCOPE_BRIDGE_ROWSET_SHA256,
        "gap_parser_scope_bridge_coverage": gap_parser_scope_bridge_summary.get("bridge_rows") == 19
        and gap_parser_scope_bridge_summary.get("targeted_review_rows_represented") == 19
        and gap_parser_scope_bridge_summary.get("parser_scope_review_rows_represented") == 20
        and gap_parser_scope_bridge_summary.get("route_packet_rows_represented") == 20
        and gap_parser_scope_bridge_summary.get("decision_packet_rows_represented") == 20
        and gap_parser_scope_bridge_summary.get("mutation_allowed") is False
        and gap_parser_scope_bridge_summary.get("parser_acceptance_allowed") is False
        and gap_parser_scope_bridge_summary.get("person_ingestion_allowed") is False,
        "gap_candidate_output_bridge_rowset": gap_candidate_output_bridge_summary.get("rowset_sha256")
        == GAP_CANDIDATE_OUTPUT_BRIDGE_ROWSET_SHA256,
        "gap_candidate_output_bridge_coverage": gap_candidate_output_bridge_summary.get("bridge_rows") == 19
        and gap_candidate_output_bridge_summary.get("implementation_approval_rows_represented") == 20
        and gap_candidate_output_bridge_summary.get("candidate_output_rows_represented") == 159
        and gap_candidate_output_bridge_summary.get("candidate_fingerprint_rows_represented") == 155
        and gap_candidate_output_bridge_summary.get("mutation_allowed") is False
        and gap_candidate_output_bridge_summary.get("parser_acceptance_allowed") is False
        and gap_candidate_output_bridge_summary.get("person_ingestion_allowed") is False,
        "gap_review_queue_bridge_rowset": gap_review_queue_bridge_summary.get("rowset_sha256")
        == GAP_REVIEW_QUEUE_BRIDGE_ROWSET_SHA256,
        "gap_review_queue_bridge_coverage": gap_review_queue_bridge_summary.get("bridge_rows") == 19
        and gap_review_queue_bridge_summary.get("review_queue_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("decision_scaffold_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("pending_decision_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("valid_non_mutating_decision_rows_represented") == 0
        and gap_review_queue_bridge_summary.get("invalid_decision_rows_represented") == 0
        and gap_review_queue_bridge_summary.get("mutation_allowed") is False
        and gap_review_queue_bridge_summary.get("person_ingestion_allowed") is False,
        "execution_readiness_bridge_rowset": execution_readiness_bridge_summary.get("rowset_sha256")
        == EXECUTION_READINESS_BRIDGE_ROWSET_SHA256,
        "execution_readiness_bridge_coverage": execution_readiness_bridge_summary.get("bridge_rows") == 19
        and execution_readiness_bridge_summary.get("ready_program_rows") == 19
        and execution_readiness_bridge_summary.get("not_ready_program_rows") == 0
        and execution_readiness_bridge_summary.get("slice_index_rows_represented") == 20
        and execution_readiness_bridge_summary.get("workbook_rows_represented") == 159
        and execution_readiness_bridge_summary.get("pending_decision_rows_represented") == 159
        and execution_readiness_bridge_summary.get("review_queue_rows_represented") == 159
        and execution_readiness_bridge_summary.get("valid_non_mutating_decision_rows_represented") == 0
        and execution_readiness_bridge_summary.get("invalid_decision_rows_represented") == 0
        and execution_readiness_bridge_summary.get("slice_output_paths_tmp_only") is True
        and execution_readiness_bridge_summary.get("patch_output_paths_tmp_only") is True
        and execution_readiness_bridge_summary.get("mutation_allowed") is False
        and execution_readiness_bridge_summary.get("person_ingestion_allowed") is False,
        "blank_execution_verification_rowset": blank_execution_verification_summary.get("rowset_sha256")
        == BLANK_EXECUTION_VERIFICATION_ROWSET_SHA256,
        "blank_execution_verification_coverage": blank_execution_verification_summary.get("verification_rows") == 20
        and blank_execution_verification_summary.get("pass_rows") == 20
        and blank_execution_verification_summary.get("fail_rows") == 0
        and blank_execution_verification_summary.get("slice_rows_represented") == 159
        and blank_execution_verification_summary.get("blank_extract_fail_closed_rows") == 20
        and blank_execution_verification_summary.get("allow_empty_patch_rows_represented") == 0
        and blank_execution_verification_summary.get("dry_run_patch_rows_represented") == 0
        and blank_execution_verification_summary.get("dry_run_valid_non_mutating_rows_represented") == 0
        and blank_execution_verification_summary.get("tmp_outputs_removed_rows") == 20
        and blank_execution_verification_summary.get("mutation_allowed") is False
        and blank_execution_verification_summary.get("person_ingestion_allowed") is False
        and blank_execution_verification_summary.get("apply_executed") is False,
        "slice_prioritization_plan_rowset": slice_prioritization_summary.get("rowset_sha256")
        == SLICE_PRIORITIZATION_PLAN_ROWSET_SHA256,
        "slice_prioritization_plan_coverage": slice_prioritization_summary.get("prioritization_rows") == 20
        and slice_prioritization_summary.get("slice_rows_represented") == 159
        and slice_prioritization_summary.get("ready_for_bounded_human_reviewer_input_rows") == 20
        and slice_prioritization_summary.get("blank_execution_pass_rows_represented") == 20
        and slice_prioritization_summary.get("dry_run_patch_rows_represented") == 0
        and slice_prioritization_summary.get("accepted_person_rows") == 0
        and slice_prioritization_summary.get("apply_executed") is False
        and slice_prioritization_summary.get("first_priority_execution_order") == "4"
        and slice_prioritization_summary.get("first_priority_program_name") == "General Surgery"
        and slice_prioritization_summary.get("mutation_allowed") is False
        and slice_prioritization_summary.get("person_ingestion_allowed") is False,
        "priority_instruction_packet_rowset": priority_instruction_summary.get("rowset_sha256")
        == PRIORITY_INSTRUCTION_PACKET_ROWSET_SHA256,
        "priority_instruction_packet_coverage": priority_instruction_summary.get("instruction_rows") == 2
        and priority_instruction_summary.get("priority_rank") == "1"
        and priority_instruction_summary.get("execution_order") == "4"
        and priority_instruction_summary.get("program_name") == "General Surgery"
        and priority_instruction_summary.get("pending_blank_instruction_rows") == 2
        and priority_instruction_summary.get("free_text_note_column_committed") is False
        and priority_instruction_summary.get("raw_candidate_names_committed") is False
        and priority_instruction_summary.get("raw_person_urls_committed") is False
        and priority_instruction_summary.get("accepted_person_rows") == 0
        and priority_instruction_summary.get("apply_executed") is False
        and priority_instruction_summary.get("mutation_allowed") is False
        and priority_instruction_summary.get("person_ingestion_allowed") is False,
        "patch_helper_fixture_rowset": patch_helper_fixture_summary.get("rowset_sha256")
        == PATCH_HELPER_FIXTURE_ROWSET_SHA256,
        "patch_helper_fixture_coverage": patch_helper_fixture_summary.get("fixture_check_rows") == 16
        and patch_helper_fixture_summary.get("pass_rows") == 16
        and patch_helper_fixture_summary.get("fail_rows") == 0
        and patch_helper_fixture_summary.get("synthetic_fixture_only") is True
        and patch_helper_fixture_summary.get("real_vanderbilt_rows_used") == 0
        and patch_helper_fixture_summary.get("accepted_person_rows") == 0
        and patch_helper_fixture_summary.get("apply_executed") is False
        and patch_helper_fixture_summary.get("mutation_allowed") is False
        and patch_helper_fixture_summary.get("person_ingestion_allowed") is False,
        "priority_handoff_packet_rowset": priority_handoff_summary.get("rowset_sha256")
        == PRIORITY_HANDOFF_PACKET_ROWSET_SHA256,
        "priority_handoff_packet_coverage": priority_handoff_summary.get("handoff_rows") == 1
        and priority_handoff_summary.get("priority_rank") == "1"
        and priority_handoff_summary.get("execution_order") == "4"
        and priority_handoff_summary.get("program_name") == "General Surgery"
        and priority_handoff_summary.get("instruction_rows_represented") == 2
        and priority_handoff_summary.get("pending_blank_instruction_rows") == 2
        and priority_handoff_summary.get("fixture_pass_rows") == 16
        and priority_handoff_summary.get("fixture_fail_rows") == 0
        and priority_handoff_summary.get("decision_audit_valid_non_mutating_rows") == 0
        and priority_handoff_summary.get("decision_audit_invalid_rows") == 0
        and priority_handoff_summary.get("apply_command_allowed") is False
        and priority_handoff_summary.get("accepted_person_rows") == 0
        and priority_handoff_summary.get("apply_executed") is False
        and priority_handoff_summary.get("mutation_allowed") is False
        and priority_handoff_summary.get("person_ingestion_allowed") is False,
        "synthetic_handoff_demo_rowset": synthetic_handoff_demo_summary.get("rowset_sha256")
        == SYNTHETIC_HANDOFF_DEMO_ROWSET_SHA256,
        "synthetic_handoff_demo_coverage": synthetic_handoff_demo_summary.get("demo_check_rows") == 5
        and synthetic_handoff_demo_summary.get("pass_rows") == 5
        and synthetic_handoff_demo_summary.get("fail_rows") == 0
        and synthetic_handoff_demo_summary.get("synthetic_fixture_only") is True
        and synthetic_handoff_demo_summary.get("real_vanderbilt_rows_used") == 0
        and synthetic_handoff_demo_summary.get("slice_rows") == 2
        and synthetic_handoff_demo_summary.get("extracted_patch_rows") == 1
        and synthetic_handoff_demo_summary.get("valid_non_mutating_rows") == 1
        and synthetic_handoff_demo_summary.get("dry_run_outputs_written") == 0
        and synthetic_handoff_demo_summary.get("tmp_outputs_removed") is True
        and synthetic_handoff_demo_summary.get("apply_executed") is False
        and synthetic_handoff_demo_summary.get("mutation_allowed") is False
        and synthetic_handoff_demo_summary.get("person_ingestion_allowed") is False,
        "gap_manifest_rows": gap_summary.get("rows") == 113 and gap_summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected public contributor worklist source boundary: " + dumps(checks))
    return (
        verification_summary,
        snapshot,
        batch_summary,
        operator_summary,
        decision_audit_summary,
        patch_template_summary,
        patch_workbook_summary,
        patch_slice_index_summary,
        gap_slice_index_summary,
        gap_review_template_summary,
        gap_review_template_validation_summary,
        gap_targeted_review_packet_summary,
        gap_targeted_review_packet_validation_summary,
        gap_parser_scope_bridge_summary,
        gap_candidate_output_bridge_summary,
        gap_review_queue_bridge_summary,
        execution_readiness_bridge_summary,
        blank_execution_verification_summary,
        slice_prioritization_summary,
        priority_instruction_summary,
        patch_helper_fixture_summary,
        priority_handoff_summary,
        synthetic_handoff_demo_summary,
        gap_summary,
    )


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("work_item_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Top50 Public Contributor Worklist",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Top50 Public Contributor Worklist",
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
        "## Work Items",
        "",
        "| order | lane | status | priority | impact | source | target | next action |",
        "| ---: | --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for item in rows:
        lines.append(
            "| {execution_order} | {action_lane} | {action_status} | {priority} | {impact_count} | {source_artifact} | {target_artifact} | {recommended_next_action} |".format(
                **item
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    (
        verification_summary,
        snapshot,
        batch_summary,
        operator_summary,
        decision_audit_summary,
        patch_template_summary,
        patch_workbook_summary,
        patch_slice_index_summary,
        gap_slice_index_summary,
        gap_review_template_summary,
        gap_review_template_validation_summary,
        gap_targeted_review_packet_summary,
        gap_targeted_review_packet_validation_summary,
        gap_parser_scope_bridge_summary,
        gap_candidate_output_bridge_summary,
        gap_review_queue_bridge_summary,
        execution_readiness_bridge_summary,
        blank_execution_verification_summary,
        slice_prioritization_summary,
        priority_instruction_summary,
        patch_helper_fixture_summary,
        priority_handoff_summary,
        synthetic_handoff_demo_summary,
        gap_summary,
    ) = verify_source_boundary()
    batch_rows = read_csv_rows(BATCH_CSV)
    operator_rows = read_csv_rows(OPERATOR_CSV)
    priority_handoff_rows = read_csv_rows(PRIORITY_HANDOFF_CSV)
    gap_rows = read_csv_rows(GAP_CSV)
    generated_at = datetime.now(timezone.utc).isoformat()
    by_batch_status = Counter(row.get("packet_status", "") for row in batch_rows)
    by_batch_lane = Counter(row.get("review_queue_lane", "") for row in batch_rows)
    by_operator_status = Counter(row.get("operator_packet_status", "") for row in operator_rows)

    rows = [
        row(
            execution_order=1,
            action_lane="verify_public_clone_substrate",
            action_status="ready_and_passing",
            priority=980,
            entity_type="public_clone_verification",
            entity_key="top50_public_clone_verification",
            display_label="Top-50 public clone verification",
            impact_count=int(verification_summary.get("verification_rows", 0)),
            source_artifact="artifacts/data/top50_public_clone_verification_summary.json",
            target_artifact="artifacts/data/top50_public_clone_verification_summary.json",
            required_next_evidence="All public-clone verification rows must pass before reviewer work or source-discovery work starts.",
            recommended_next_action="Run python3 scripts/materialize_top50_public_substrate_check_contract.py after any public top-50/Vanderbilt artifact change.",
            verification_command="python3 scripts/materialize_top50_public_substrate_check_contract.py",
            success_condition="Aggregate public substrate check contract passes all current public clone, worklist, handoff, synthetic dry-run, and gap fail-closed gates.",
            approval_required_for=["none_for_verification_only"],
            source_rowset_sha256=VERIFICATION_ROWSET_SHA256,
            target_rowset_sha256=VERIFICATION_ROWSET_SHA256,
            evidence={
                "verification_rows": verification_summary.get("verification_rows"),
                "pass_rows": verification_summary.get("pass_rows"),
                "fail_rows": verification_summary.get("fail_rows"),
                "gbrain_approval_status": verification_summary.get("gbrain_approval_status"),
            },
            generated_at=generated_at,
        ),
        row(
            execution_order=2,
            action_lane="vanderbilt_bounded_manual_review_packets",
            action_status="ready_for_non_mutating_reviewer_input",
            priority=940,
            entity_type="vanderbilt_public_reviewer_operator_packets",
            entity_key="vanderbilt_public_reviewer_operator_packets",
            display_label="Vanderbilt public reviewer operator packets",
            impact_count=int(batch_summary.get("decision_row_count", 0)),
            source_artifact="artifacts/data/vanderbilt_public_reviewer_operator_packets.csv",
            target_artifact="artifacts/data/vanderbilt_candidate_reviewer_decisions.csv",
            required_next_evidence=(
                "Reviewer decisions must use allowed actions, current decision fingerprints, all lane-specific "
                "confirmation fields, and no-ingestion/no-closure/no-raw-name/no-url-rewrite confirmations."
            ),
            recommended_next_action=(
                "Use artifacts/data/vanderbilt_reviewer_decision_patch_workbook_slice_index.csv to choose one "
                "operator packet, slice it with scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py, fill only "
                "non-mutating decisions, extract strict patch rows with scripts/extract_vanderbilt_reviewer_decision_patch.py, "
                "dry-run scripts/apply_vanderbilt_reviewer_decision_patch.py, then stop. Do not run --apply or commit "
                "filled decisions until a future exact approval packet exists."
            ),
            verification_command=(
                "python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py && "
                "python3 scripts/materialize_vanderbilt_candidate_review_batch_packets.py && "
                "python3 scripts/materialize_vanderbilt_public_reviewer_operator_packets.py && "
                "python3 scripts/materialize_top50_public_clone_verification.py"
            ),
            success_condition="No invalid reviewer decisions; accepted person rows and denominator closure remain 0.",
            approval_required_for=[
                "accepted_person_rows",
                "person_ingestion",
                "denominator_closure",
                "identity_reconciliation",
                "parser_acceptance",
                "scope_closure",
            ],
            source_rowset_sha256=OPERATOR_PACKET_ROWSET_SHA256,
            target_rowset_sha256=DECISION_AUDIT_ROWSET_SHA256,
            evidence={
                "operator_packet_rows": operator_summary.get("operator_packet_rows"),
                "missing_required_template_column_mentions": operator_summary.get(
                    "missing_required_template_column_mentions"
                ),
                "by_operator_packet_status": dict(sorted(by_operator_status.items())),
                "operator_source_batch_packet_rowset_sha256": operator_summary.get("source_batch_packet_rowset_sha256"),
                "batch_packet_rows": batch_summary.get("batch_packet_rows"),
                "batch_packet_rowset_sha256": batch_summary.get("rowset_sha256"),
                "decision_row_count": batch_summary.get("decision_row_count"),
                "pending_decision_rows": batch_summary.get("pending_decision_rows"),
                "invalid_decision_rows": batch_summary.get("invalid_decision_rows"),
                "patch_template_rows": patch_template_summary.get("template_rows"),
                "patch_template_rowset_sha256": patch_template_summary.get("rowset_sha256"),
                "patch_template_intentionally_invalid_until_filled": patch_template_summary.get(
                    "template_intentionally_invalid_until_filled"
                ),
                "patch_workbook_rows": patch_workbook_summary.get("workbook_rows"),
                "patch_workbook_rowset_sha256": patch_workbook_summary.get("rowset_sha256"),
                "patch_workbook_helper_patch_extraction_required": patch_workbook_summary.get(
                    "helper_patch_extraction_required"
                ),
                "patch_slice_index_rows": patch_slice_index_summary.get("slice_index_rows"),
                "patch_slice_index_rowset_sha256": patch_slice_index_summary.get("rowset_sha256"),
                "patch_slice_outputs_default_tmp_only": patch_slice_index_summary.get("slice_outputs_default_tmp_only"),
                "by_packet_status": dict(sorted(by_batch_status.items())),
                "by_review_queue_lane": dict(sorted(by_batch_lane.items())),
            },
            generated_at=generated_at,
        ),
        row(
            execution_order=3,
            action_lane="vanderbilt_active_gap_manifest_triage",
            action_status="ready_for_local_reviewer_handoff_execution",
            priority=760,
            entity_type="vanderbilt_priority_reviewer_handoff_packet",
            entity_key="vanderbilt_priority_reviewer_handoff_packet",
            display_label="Vanderbilt General Surgery priority reviewer handoff packet",
            impact_count=int(priority_handoff_summary.get("instruction_rows_represented", 0)),
            source_artifact="artifacts/data/vanderbilt_priority_reviewer_handoff_packet.csv",
            target_artifact="artifacts/data/vanderbilt_candidate_reviewer_decisions.csv",
            required_next_evidence=(
                "The handoff packet bundles the first General Surgery reviewer slice, the two blank hash-only "
                "instruction rows, the synthetic fixture status, and the slice/extract/dry-run commands under an "
                "explicit no-apply boundary. The synthetic dry-run demo proves the command path composes against "
                "fabricated /tmp rows. Filled real reviewer decisions still require strict extraction and dry-run "
                "verification, and any apply or repo commit of filled decisions needs future exact approval."
            ),
            recommended_next_action=(
                "Use artifacts/data/vanderbilt_priority_reviewer_handoff_packet.csv as the reviewer-facing runbook. "
                "Run its slice command locally, fill only the blank action/confirmation fields in the local workbook, "
                "extract a strict patch, dry-run apply, and do not run --apply until a future exact approval packet exists."
            ),
            verification_command=(
                "python3 scripts/materialize_vanderbilt_patch_helper_fixture_verification.py && "
                "python3 scripts/materialize_vanderbilt_priority_reviewer_instruction_packet.py && "
                "python3 scripts/materialize_vanderbilt_priority_reviewer_handoff_packet.py && "
                "python3 scripts/materialize_vanderbilt_synthetic_handoff_dry_run_demo.py && "
                "python3 scripts/materialize_top50_public_clone_verification.py && "
                "python3 scripts/assert_gap_manifest_fails_closed.py"
            ),
            success_condition="Handoff packet represents two pending blank General Surgery rows, fixture harness passes 16/16 synthetic checks, synthetic end-to-end dry-run passes 5/5 with one valid non-mutating fabricated patch row and zero dry-run outputs written, no raw labels or URLs are committed, accepted_person_rows=0, apply_command_allowed=false, and apply_executed=false.",
            approval_required_for=[
                "filled_reviewer_decision_commit",
                "patch_apply",
                "denominator_closure",
                "vanderbilt_school_verification",
                "person_ingestion",
                "url_rewrite",
                "identity_collapse",
            ],
            source_rowset_sha256=PRIORITY_HANDOFF_PACKET_ROWSET_SHA256,
            target_rowset_sha256=DECISION_AUDIT_ROWSET_SHA256,
            evidence={
                "gap_manifest_rows": gap_summary.get("rows"),
                "gap_manifest_csv_rows": len(gap_rows),
                "mutation_allowed": gap_summary.get("mutation_allowed"),
                "materializer_fail_closed_expected": True,
                "gap_slice_index_rows": gap_slice_index_summary.get("slice_index_rows"),
                "gap_slice_index_rowset_sha256": gap_slice_index_summary.get("rowset_sha256"),
                "gap_slice_outputs_default_tmp_only": gap_slice_index_summary.get("slice_outputs_default_tmp_only"),
                "gap_review_template_rows": gap_review_template_summary.get("review_template_rows"),
                "gap_review_template_rowset_sha256": gap_review_template_summary.get("rowset_sha256"),
                "gap_review_template_pending_rows": gap_review_template_validation_summary.get("pending_rows"),
                "gap_review_template_invalid_rows": gap_review_template_validation_summary.get("invalid_rows"),
                "gap_targeted_review_packet_rows": gap_targeted_review_packet_summary.get("review_packet_rows"),
                "gap_targeted_review_packet_filled_rows": gap_targeted_review_packet_summary.get("filled_review_rows"),
                "gap_targeted_review_packet_pending_rows": gap_targeted_review_packet_validation_summary.get("pending_rows"),
                "gap_targeted_review_packet_invalid_rows": gap_targeted_review_packet_validation_summary.get("invalid_rows"),
                "gap_targeted_review_packet_rowset_sha256": gap_targeted_review_packet_summary.get("rowset_sha256"),
                "gap_parser_scope_bridge_rows": gap_parser_scope_bridge_summary.get("bridge_rows"),
                "gap_parser_scope_bridge_parser_rows": gap_parser_scope_bridge_summary.get(
                    "parser_scope_review_rows_represented"
                ),
                "gap_parser_scope_bridge_route_rows": gap_parser_scope_bridge_summary.get("route_packet_rows_represented"),
                "gap_parser_scope_bridge_decision_rows": gap_parser_scope_bridge_summary.get(
                    "decision_packet_rows_represented"
                ),
                "gap_parser_scope_bridge_rowset_sha256": gap_parser_scope_bridge_summary.get("rowset_sha256"),
                "gap_candidate_output_bridge_rows": gap_candidate_output_bridge_summary.get("bridge_rows"),
                "gap_candidate_output_bridge_implementation_rows": gap_candidate_output_bridge_summary.get(
                    "implementation_approval_rows_represented"
                ),
                "gap_candidate_output_bridge_output_rows": gap_candidate_output_bridge_summary.get(
                    "candidate_output_rows_represented"
                ),
                "gap_candidate_output_bridge_fingerprint_rows": gap_candidate_output_bridge_summary.get(
                    "candidate_fingerprint_rows_represented"
                ),
                "gap_candidate_output_bridge_rowset_sha256": gap_candidate_output_bridge_summary.get("rowset_sha256"),
                "gap_review_queue_bridge_rows": gap_review_queue_bridge_summary.get("bridge_rows"),
                "gap_review_queue_bridge_review_rows": gap_review_queue_bridge_summary.get(
                    "review_queue_rows_represented"
                ),
                "gap_review_queue_bridge_scaffold_rows": gap_review_queue_bridge_summary.get(
                    "decision_scaffold_rows_represented"
                ),
                "gap_review_queue_bridge_pending_rows": gap_review_queue_bridge_summary.get(
                    "pending_decision_rows_represented"
                ),
                "gap_review_queue_bridge_rowset_sha256": gap_review_queue_bridge_summary.get("rowset_sha256"),
                "execution_readiness_bridge_rows": execution_readiness_bridge_summary.get("bridge_rows"),
                "execution_readiness_ready_program_rows": execution_readiness_bridge_summary.get("ready_program_rows"),
                "execution_readiness_slice_index_rows": execution_readiness_bridge_summary.get(
                    "slice_index_rows_represented"
                ),
                "execution_readiness_workbook_rows": execution_readiness_bridge_summary.get("workbook_rows_represented"),
                "execution_readiness_pending_rows": execution_readiness_bridge_summary.get(
                    "pending_decision_rows_represented"
                ),
                "execution_readiness_rowset_sha256": execution_readiness_bridge_summary.get("rowset_sha256"),
                "blank_execution_verification_rows": blank_execution_verification_summary.get("verification_rows"),
                "blank_execution_pass_rows": blank_execution_verification_summary.get("pass_rows"),
                "blank_execution_slice_rows": blank_execution_verification_summary.get("slice_rows_represented"),
                "blank_execution_fail_closed_rows": blank_execution_verification_summary.get(
                    "blank_extract_fail_closed_rows"
                ),
                "blank_execution_dry_run_patch_rows": blank_execution_verification_summary.get(
                    "dry_run_patch_rows_represented"
                ),
                "blank_execution_rowset_sha256": blank_execution_verification_summary.get("rowset_sha256"),
                "slice_prioritization_rows": slice_prioritization_summary.get("prioritization_rows"),
                "slice_prioritization_slice_rows": slice_prioritization_summary.get("slice_rows_represented"),
                "slice_prioritization_first_priority_execution_order": slice_prioritization_summary.get(
                    "first_priority_execution_order"
                ),
                "slice_prioritization_first_priority_program_name": slice_prioritization_summary.get(
                    "first_priority_program_name"
                ),
                "slice_prioritization_first_priority_workbook_row_count": slice_prioritization_summary.get(
                    "first_priority_workbook_row_count"
                ),
                "slice_prioritization_rowset_sha256": slice_prioritization_summary.get("rowset_sha256"),
                "priority_instruction_rows": priority_instruction_summary.get("instruction_rows"),
                "priority_instruction_pending_blank_rows": priority_instruction_summary.get(
                    "pending_blank_instruction_rows"
                ),
                "priority_instruction_program_name": priority_instruction_summary.get("program_name"),
                "priority_instruction_execution_order": priority_instruction_summary.get("execution_order"),
                "priority_instruction_rowset_sha256": priority_instruction_summary.get("rowset_sha256"),
                "patch_helper_fixture_rows": patch_helper_fixture_summary.get("fixture_check_rows"),
                "patch_helper_fixture_pass_rows": patch_helper_fixture_summary.get("pass_rows"),
                "patch_helper_fixture_rowset_sha256": patch_helper_fixture_summary.get("rowset_sha256"),
                "priority_handoff_rows": priority_handoff_summary.get("handoff_rows"),
                "priority_handoff_status": priority_handoff_summary.get("handoff_status"),
                "priority_handoff_instruction_rows": priority_handoff_summary.get("instruction_rows_represented"),
                "priority_handoff_apply_command_allowed": priority_handoff_summary.get("apply_command_allowed"),
                "priority_handoff_rowset_sha256": priority_handoff_summary.get("rowset_sha256"),
                "priority_handoff_csv_rows": len(priority_handoff_rows),
                "synthetic_handoff_demo_rows": synthetic_handoff_demo_summary.get("demo_check_rows"),
                "synthetic_handoff_demo_pass_rows": synthetic_handoff_demo_summary.get("pass_rows"),
                "synthetic_handoff_demo_slice_rows": synthetic_handoff_demo_summary.get("slice_rows"),
                "synthetic_handoff_demo_extracted_patch_rows": synthetic_handoff_demo_summary.get(
                    "extracted_patch_rows"
                ),
                "synthetic_handoff_demo_valid_non_mutating_rows": synthetic_handoff_demo_summary.get(
                    "valid_non_mutating_rows"
                ),
                "synthetic_handoff_demo_tmp_outputs_removed": synthetic_handoff_demo_summary.get("tmp_outputs_removed"),
                "synthetic_handoff_demo_rowset_sha256": synthetic_handoff_demo_summary.get("rowset_sha256"),
            },
            generated_at=generated_at,
        ),
        row(
            execution_order=4,
            action_lane="future_exact_approval_packet_after_valid_decisions",
            action_status="blocked_until_valid_non_mutating_decisions",
            priority=640,
            entity_type="future_gbrain_approval_packet",
            entity_key="vanderbilt_future_exact_acceptance_packet",
            display_label="Future exact Vanderbilt acceptance/closure packet",
            impact_count=int(decision_audit_summary.get("pending_rows", 0)),
            source_artifact="artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json",
            target_artifact="artifacts/data/vanderbilt_candidate_acceptance_or_closure_approval_packet.csv",
            required_next_evidence=(
                "Only build this after reviewer decisions are valid_non_mutating and no invalid rows remain; acceptance "
                "still requires a separate exact GBrain approval boundary."
            ),
            recommended_next_action=(
                "Do not build person-ingestion, denominator-closure, parser-acceptance, scope-closure, or identity-collapse "
                "packets until reviewer decisions are present and the decision audit passes."
            ),
            verification_command="python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py",
            success_condition="valid_non_mutating_rows > 0, invalid_rows = 0, and mutation flags remain false before any approval request.",
            approval_required_for=[
                "person_ingestion",
                "denominator_closure",
                "parser_acceptance",
                "scope_closure",
                "identity_collapse",
            ],
            source_rowset_sha256=DECISION_AUDIT_ROWSET_SHA256,
            target_rowset_sha256="",
            evidence={
                "pending_rows": decision_audit_summary.get("pending_rows"),
                "valid_non_mutating_rows": decision_audit_summary.get("valid_non_mutating_rows"),
                "invalid_rows": decision_audit_summary.get("invalid_rows"),
                "mutation_allowed": decision_audit_summary.get("mutation_allowed"),
            },
            generated_at=generated_at,
        ),
    ]
    rows.sort(key=lambda item: (int(item["execution_order"]), -int(item["priority"]), str(item["action_lane"])))

    by_status = Counter(str(item["action_status"]) for item in rows)
    by_lane = Counter(str(item["action_lane"]) for item in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "worklist_rows": len(rows),
        "total_impact_count": sum(int(item["impact_count"]) for item in rows),
        "critical_rows": sum(1 for item in rows if item["priority_band"] == "critical"),
        "high_rows": sum(1 for item in rows if item["priority_band"] == "high"),
        "medium_rows": sum(1 for item in rows if item["priority_band"] == "medium"),
        "low_rows": sum(1 for item in rows if item["priority_band"] == "low"),
        "by_action_status": dict(sorted(by_status.items())),
        "by_action_lane": dict(sorted(by_lane.items())),
        "source_verification_rowset_sha256": VERIFICATION_ROWSET_SHA256,
        "source_snapshot_rowset_sha256": SNAPSHOT_ROWSET_SHA256,
        "source_vanderbilt_batch_packet_rowset_sha256": BATCH_PACKET_ROWSET_SHA256,
        "source_vanderbilt_operator_packet_rowset_sha256": OPERATOR_PACKET_ROWSET_SHA256,
        "source_vanderbilt_patch_template_rowset_sha256": PATCH_TEMPLATE_ROWSET_SHA256,
        "source_vanderbilt_patch_workbook_rowset_sha256": PATCH_WORKBOOK_ROWSET_SHA256,
        "source_vanderbilt_patch_slice_index_rowset_sha256": PATCH_SLICE_INDEX_ROWSET_SHA256,
        "source_vanderbilt_gap_slice_index_rowset_sha256": GAP_SLICE_INDEX_ROWSET_SHA256,
        "source_vanderbilt_gap_review_template_rowset_sha256": GAP_REVIEW_TEMPLATE_ROWSET_SHA256,
        "source_vanderbilt_gap_targeted_review_packet_rowset_sha256": GAP_TARGETED_REVIEW_PACKET_ROWSET_SHA256,
        "source_vanderbilt_gap_parser_scope_bridge_rowset_sha256": GAP_PARSER_SCOPE_BRIDGE_ROWSET_SHA256,
        "source_vanderbilt_gap_candidate_output_bridge_rowset_sha256": GAP_CANDIDATE_OUTPUT_BRIDGE_ROWSET_SHA256,
        "source_vanderbilt_gap_review_queue_bridge_rowset_sha256": GAP_REVIEW_QUEUE_BRIDGE_ROWSET_SHA256,
        "source_vanderbilt_reviewer_execution_readiness_bridge_rowset_sha256": EXECUTION_READINESS_BRIDGE_ROWSET_SHA256,
        "source_vanderbilt_reviewer_blank_execution_verification_rowset_sha256": BLANK_EXECUTION_VERIFICATION_ROWSET_SHA256,
        "source_vanderbilt_reviewer_slice_prioritization_plan_rowset_sha256": SLICE_PRIORITIZATION_PLAN_ROWSET_SHA256,
        "source_vanderbilt_priority_reviewer_instruction_packet_rowset_sha256": PRIORITY_INSTRUCTION_PACKET_ROWSET_SHA256,
        "source_vanderbilt_patch_helper_fixture_verification_rowset_sha256": PATCH_HELPER_FIXTURE_ROWSET_SHA256,
        "source_vanderbilt_priority_reviewer_handoff_packet_rowset_sha256": PRIORITY_HANDOFF_PACKET_ROWSET_SHA256,
        "source_vanderbilt_synthetic_handoff_dry_run_demo_rowset_sha256": SYNTHETIC_HANDOFF_DEMO_ROWSET_SHA256,
        "gbrain_approval_status": "approved_non_mutating_public_contributor_worklist_lane",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["worklist_rows", "total_impact_count", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
