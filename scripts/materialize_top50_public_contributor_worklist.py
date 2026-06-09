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
GAP_SUMMARY = ARTIFACTS / "school_gap_resolution_manifest_summary.json"
GAP_CSV = ARTIFACTS / "school_gap_resolution_manifest.csv"

OUT_CSV = ARTIFACTS / "top50_public_contributor_worklist.csv"
OUT_JSON = ARTIFACTS / "top50_public_contributor_worklist.json"
OUT_SUMMARY = ARTIFACTS / "top50_public_contributor_worklist_summary.json"
OUT_MD = RESEARCH / "top50-public-contributor-worklist-2026-06-09.md"

VERIFICATION_ROWSET_SHA256 = "cf1f18abd58299260914f93d697c1a5b14b348b31b5c77d985b43547b53ca76f"
SNAPSHOT_ROWSET_SHA256 = "b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48"
BATCH_PACKET_ROWSET_SHA256 = "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f"
OPERATOR_PACKET_ROWSET_SHA256 = "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"
DECISION_AUDIT_ROWSET_SHA256 = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
PATCH_TEMPLATE_ROWSET_SHA256 = "5532d007555997f54d25884baba2f4e594d4ff1fa286301bfa6f87fc64caaa8d"
PATCH_WORKBOOK_ROWSET_SHA256 = "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3"
PATCH_SLICE_INDEX_ROWSET_SHA256 = "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4"
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
        gap_summary,
    ) = verify_source_boundary()
    batch_rows = read_csv_rows(BATCH_CSV)
    operator_rows = read_csv_rows(OPERATOR_CSV)
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
            recommended_next_action="Run python3 scripts/materialize_top50_public_clone_verification.py after any public top-50 artifact change.",
            verification_command="python3 scripts/materialize_top50_public_clone_verification.py",
            success_condition="20 verification rows pass and fail_rows remains 0.",
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
                "dry-run scripts/apply_vanderbilt_reviewer_decision_patch.py, then apply and rerun the decision audit, "
                "batch-packet materializer, operator-packet materializer, workbook materializer, and slice-index materializer."
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
            action_status="ready_for_non_mutating_source_discovery_planning",
            priority=760,
            entity_type="school_gap_resolution_manifest",
            entity_key="vanderbilt_active_gap_manifest",
            display_label="Vanderbilt active 113-gap manifest",
            impact_count=int(gap_summary.get("rows", 0)),
            source_artifact="artifacts/data/school_gap_resolution_manifest.csv",
            target_artifact="artifacts/data/school_gap_resolution_batch_packets.csv",
            required_next_evidence=(
                "Use committed gap rows for bounded planning only; regenerating the manifest requires private core source "
                "inputs or an explicit ALLOW_EMPTY_GAP_MANIFEST=1 test run."
            ),
            recommended_next_action=(
                "Use existing gap-resolution batches/packets for source-discovery planning; do not regenerate the gap "
                "manifest in a public clone unless the core source inputs are present."
            ),
            verification_command=(
                "python3 scripts/materialize_top50_public_clone_verification.py && "
                "python3 scripts/assert_gap_manifest_fails_closed.py"
            ),
            success_condition="Committed gap manifest remains 113 Vanderbilt rows and mutation_allowed=false.",
            approval_required_for=[
                "denominator_closure",
                "vanderbilt_school_verification",
                "person_ingestion",
                "url_rewrite",
                "identity_collapse",
            ],
            source_rowset_sha256="",
            target_rowset_sha256="",
            evidence={
                "gap_manifest_rows": gap_summary.get("rows"),
                "gap_manifest_csv_rows": len(gap_rows),
                "mutation_allowed": gap_summary.get("mutation_allowed"),
                "materializer_fail_closed_expected": True,
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
