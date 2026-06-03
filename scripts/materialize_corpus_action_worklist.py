#!/usr/bin/env python3
"""Materialize a ranked cross-corpus action worklist.

The source-specific ledgers are intentionally conservative. This script does
not accept facts or mutate roster truth; it merges unresolved source, review,
state-machine, and enrichment surfaces into one operator queue so the next run
can attack the highest-value evidence gaps first.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_OUT = ARTIFACTS / "corpus_action_worklist.csv"
JSON_OUT = ARTIFACTS / "corpus_action_worklist.json"
SUMMARY_OUT = ARTIFACTS / "corpus_action_worklist_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "work_item_key",
    "action_surface",
    "action_scope",
    "entity_type",
    "entity_key",
    "display_label",
    "role",
    "program_name",
    "priority",
    "priority_band",
    "impact_count",
    "readiness_status",
    "blocker_status",
    "required_next_evidence",
    "recommended_next_action",
    "source_artifact",
    "target_artifact",
    "downstream_tables_json",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_key(*parts: object) -> str:
    text = "||".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def priority_band(priority: int) -> str:
    if priority >= 1000:
        return "critical"
    if priority >= 700:
        return "high"
    if priority >= 300:
        return "medium"
    return "low"


def row(
    *,
    action_surface: str,
    action_scope: str,
    entity_type: str,
    entity_key: str,
    display_label: str,
    role: str = "",
    program_name: str = "",
    priority: int,
    impact_count: int,
    readiness_status: str,
    blocker_status: str,
    required_next_evidence: str,
    recommended_next_action: str,
    source_artifact: str,
    target_artifact: str,
    downstream_tables: list[str],
    evidence: dict,
    generated_at: str,
) -> dict:
    return {
        "work_item_key": "corpus_action_" + stable_key(action_surface, action_scope, entity_key, recommended_next_action),
        "action_surface": action_surface,
        "action_scope": action_scope,
        "entity_type": entity_type,
        "entity_key": entity_key,
        "display_label": display_label,
        "role": role,
        "program_name": program_name,
        "priority": priority,
        "priority_band": priority_band(priority),
        "impact_count": impact_count,
        "readiness_status": readiness_status,
        "blocker_status": blocker_status,
        "required_next_evidence": required_next_evidence,
        "recommended_next_action": recommended_next_action,
        "source_artifact": source_artifact,
        "target_artifact": target_artifact,
        "downstream_tables_json": dumps(downstream_tables),
        "evidence_json": dumps(evidence),
        "generated_at": generated_at,
    }


def official_program_actions(generated_at: str) -> list[dict]:
    rows = []
    batch_path = ARTIFACTS / "official_program_coverage_batches.csv"
    if batch_path.exists():
        source = "artifacts/data/official_program_coverage_batches.csv"
        for item in read_csv(batch_path):
            priority = as_int(item.get("max_priority")) + min(as_int(item.get("queue_count")) * 2, 40)
            rows.append(
                row(
                    action_surface="official_program_coverage",
                    action_scope=f"{item.get('action_lane') or ''}:{item.get('batch_status') or ''}",
                    entity_type="official_program_coverage_batch",
                    entity_key=item.get("official_program_coverage_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("official_program_type"),
                            item.get("action_lane"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("official_program_type") or "",
                    program_name="",
                    priority=priority,
                    impact_count=max(
                        as_int(item.get("action_impact_count")),
                        1,
                    ),
                    readiness_status=item.get("batch_status") or "",
                    blocker_status=item.get("blocker_status") or "",
                    required_next_evidence=item.get("required_next_evidence") or "",
                    recommended_next_action=item.get("recommended_operator_action") or "",
                    source_artifact=source,
                    target_artifact=item.get("target_artifact") or "artifacts/data/official_program_coverage_assurance_audit.csv",
                    downstream_tables=[
                        "official_program_coverage_batches",
                        "official_program_coverage_action_queue",
                        "official_program_coverage_dossiers",
                        "official_program_coverage_assurance_audit",
                        "official_program_alias_review_packets",
                        "official_program_alias_reviewer_decision_queue",
                        "official_program_denominator_closure_audit",
                        "person_program_memberships",
                        "person_training_states",
                    ],
                    evidence={
                        "official_program_coverage_batch_key": item.get("official_program_coverage_batch_key"),
                        "execution_order": item.get("execution_order"),
                        "action_lane": item.get("action_lane"),
                        "blocker_status": item.get("blocker_status"),
                        "official_program_type": item.get("official_program_type"),
                        "assurance_level_signature": item.get("assurance_level_signature"),
                        "queue_count": item.get("queue_count"),
                        "program_count": item.get("program_count"),
                        "person_impact_count": item.get("person_impact_count"),
                        "candidate_source_count": item.get("candidate_source_count"),
                        "action_impact_count": item.get("action_impact_count"),
                        "assurance_level_counts": parse_json(item.get("assurance_level_counts_json"), {}),
                        "coverage_status_counts": parse_json(item.get("coverage_status_counts_json"), {}),
                        "assurance_status_counts": parse_json(item.get("assurance_status_counts_json"), {}),
                        "department_counts": parse_json(item.get("department_counts_json"), {}),
                        "top_queue_rows": parse_json(item.get("top_queue_rows_json"), []),
                        "top_dossiers": parse_json(item.get("top_dossiers_json"), []),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    source = "artifacts/data/official_program_coverage_action_queue.csv"
    for item in read_csv(ARTIFACTS / "official_program_coverage_action_queue.csv"):
        priority = as_int(item.get("priority"))
        rows.append(
            row(
                action_surface="official_program_coverage",
                action_scope=item.get("action_lane") or "coverage_action",
                entity_type="official_program",
                entity_key=item.get("official_program_key") or item.get("official_program_name") or "",
                display_label=item.get("official_program_name") or "",
                role=item.get("official_program_type") or "",
                program_name=item.get("official_program_name") or "",
                priority=priority,
                impact_count=max(as_int(item.get("person_impact_count")), as_int(item.get("candidate_source_count")), 1),
                readiness_status=item.get("coverage_status") or "",
                blocker_status=item.get("blocker_status") or item.get("assurance_status") or "",
                required_next_evidence=item.get("review_question") or "Resolve official denominator coverage before closing this program gap.",
                recommended_next_action=item.get("recommended_next_action") or "",
                source_artifact=source,
                target_artifact="artifacts/data/official_program_coverage_assurance_audit.csv",
                downstream_tables=[
                    "official_program_coverage_assurance_audit",
                    "official_program_alias_review_packets",
                    "official_program_alias_reviewer_decision_queue",
                    "person_program_memberships",
                    "person_training_states",
                ],
                evidence={
                    "assurance_status": item.get("assurance_status"),
                    "assurance_level": item.get("assurance_level"),
                    "candidate_url": item.get("candidate_url"),
                    "official_program_url": item.get("official_program_url"),
                    "candidate_source_count": item.get("candidate_source_count"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def person_evidence_actions(generated_at: str) -> list[dict]:
    rows = []
    batch_path = ARTIFACTS / "person_evidence_review_batches.csv"
    if batch_path.exists():
        dossier_path = ARTIFACTS / "person_evidence_review_dossiers.csv"
        source = "artifacts/data/person_evidence_review_batches.csv"
        batch_key_by_decision: dict[str, str] = {}
        batch_packets_by_batch: dict[str, list[dict]] = defaultdict(list)
        batch_packet_path = ARTIFACTS / "person_evidence_review_batch_packets.csv"
        if batch_packet_path.exists():
            for batch_packet in read_csv(batch_packet_path):
                batch_key = batch_packet.get("review_batch_key") or ""
                if batch_key:
                    batch_packets_by_batch[batch_key].append(batch_packet)
                decision_key = batch_packet.get("reviewer_decision_key") or ""
                if decision_key:
                    batch_key_by_decision[decision_key] = batch_packet.get("review_batch_key") or ""
        dossiers_by_batch: dict[str, list[dict]] = defaultdict(list)
        if dossier_path.exists():
            for dossier in read_csv(dossier_path):
                batch_key = batch_key_by_decision.get(dossier.get("reviewer_decision_key") or "")
                if batch_key:
                    dossiers_by_batch[batch_key].append(dossier)
        for item in read_csv(batch_path):
            dossier_rows = dossiers_by_batch.get(item.get("review_batch_key") or "", [])
            batch_packet_rows = batch_packets_by_batch.get(item.get("review_batch_key") or "", [])
            priority = 880 + as_int(item.get("max_triage_priority")) + min(as_int(item.get("packet_count")) * 2, 70)
            rows.append(
                row(
                    action_surface="person_evidence_review",
                    action_scope=item.get("triage_lane") or "person_evidence_review_batch",
                    entity_type="person_evidence_review_batch",
                    entity_key=item.get("review_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("triage_lane"),
                            item.get("role"),
                            item.get("decision_difficulty"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("role") or "",
                    program_name="",
                    priority=priority,
                    impact_count=max(as_int(item.get("review_ready_record_count")), as_int(item.get("packet_count")), 1),
                    readiness_status=item.get("decision_difficulty") or item.get("batch_status") or "",
                    blocker_status=item.get("risk_level") or "",
                    required_next_evidence=item.get("reviewer_prompt") or item.get("review_instructions") or "",
                    recommended_next_action="review_batch_and_record_packet_decisions",
                    source_artifact=source,
                    target_artifact=item.get("target_decision_artifact") or "artifacts/data/person_evidence_reviewer_decisions.csv",
                    downstream_tables=[
                        "person_evidence_review_batches",
                        "person_evidence_review_batch_packets",
                        "person_evidence_review_dossiers",
                        "person_evidence_review_triage",
                        "person_evidence_reviewer_decision_queue",
                        "person_evidence_reviewer_decision_audit",
                        "enrichment_acceptance_audit",
                        "accepted_enrichment_claims",
                    ],
                    evidence={
                        "review_batch_key": item.get("review_batch_key"),
                        "packet_count": item.get("packet_count"),
                        "review_ready_record_count": item.get("review_ready_record_count"),
                        "evidence_record_count": item.get("evidence_record_count"),
                        "source_family_counts_json": item.get("source_family_counts_json"),
                        "top_source_domains": item.get("top_source_domains"),
                        "top_best_decisions_json": item.get("top_best_decisions_json"),
                        "acceptance_rule": item.get("acceptance_rule"),
                        "batch_packet_support_rows": len(batch_packet_rows),
                        "ready_batch_packet_support_rows": sum(
                            1
                            for packet in batch_packet_rows
                            if packet.get("support_status") == "ready_for_packet_review"
                        ),
                        "blocked_batch_packet_support_rows": sum(
                            1
                            for packet in batch_packet_rows
                            if packet.get("support_status") != "ready_for_packet_review"
                        ),
                        "top_batch_packet_reviewer_actions": dict(
                            Counter(
                                packet.get("recommended_reviewer_action") or ""
                                for packet in batch_packet_rows
                            ).most_common(8)
                        ),
                        "top_batch_packet_names": [
                            packet.get("display_name") or ""
                            for packet in sorted(
                                batch_packet_rows,
                                key=lambda packet: (
                                    -as_int(packet.get("triage_priority")),
                                    as_int(packet.get("batch_packet_order")),
                                ),
                            )[:8]
                        ],
                        "reviewer_decision_dossier_rows": len(dossier_rows),
                        "pending_reviewer_decision_dossier_rows": sum(
                            1 for dossier in dossier_rows if dossier.get("decision_status") == "pending_reviewer_decision"
                        ),
                        "top_dossier_review_routes": dict(
                            Counter(dossier.get("review_route") or "" for dossier in dossier_rows).most_common(8)
                        ),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    triage_path = ARTIFACTS / "person_evidence_review_triage.csv"
    if triage_path.exists():
        source = "artifacts/data/person_evidence_review_triage.csv"
        for item in read_csv(triage_path):
            impact = max(as_int(item.get("review_ready_record_count")), 1)
            priority = 840 + as_int(item.get("triage_priority")) + min(impact * 4, 60)
            rows.append(
                row(
                    action_surface="person_evidence_review",
                    action_scope=item.get("triage_lane") or item.get("review_kind") or "person_evidence_review",
                    entity_type="person_or_name",
                    entity_key=item.get("person_or_name_key") or item.get("person_key") or "",
                    display_label=item.get("display_name") or "",
                    role=item.get("role") or "",
                    program_name="",
                    priority=priority,
                    impact_count=impact,
                    readiness_status=item.get("decision_difficulty") or item.get("packet_status") or "",
                    blocker_status=item.get("risk_level") or item.get("acceptance_blocker") or "",
                    required_next_evidence=item.get("reviewer_prompt") or item.get("required_reviewer_action") or "",
                    recommended_next_action=item.get("likely_next_action") or "record_accept_reject_or_needs_more_evidence_decision",
                    source_artifact=source,
                    target_artifact="artifacts/data/person_evidence_reviewer_decisions.csv",
                    downstream_tables=[
                        "person_evidence_review_triage",
                        "person_evidence_reviewer_decision_queue",
                        "person_evidence_reviewer_decision_audit",
                        "accepted_enrichment_claims",
                        "evidence_claims",
                    ],
                    evidence={
                        "packet_key": item.get("packet_key"),
                        "reviewer_decision_key": item.get("reviewer_decision_key"),
                        "packet_fingerprint": item.get("packet_fingerprint"),
                        "review_kind": item.get("review_kind"),
                        "packet_status": item.get("packet_status"),
                        "best_decision": item.get("best_decision"),
                        "top_source_domains": item.get("top_source_domains"),
                        "source_family_summary": item.get("source_family_summary"),
                        "evidence_density_score": item.get("evidence_density_score"),
                        "automation_boundary": item.get("automation_boundary"),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    source = "artifacts/data/person_evidence_reviewer_decision_queue.csv"
    for item in read_csv(ARTIFACTS / "person_evidence_reviewer_decision_queue.csv"):
        priority = 800 + as_int(item.get("review_priority")) + min(as_int(item.get("review_ready_record_count")) * 5, 50)
        rows.append(
            row(
                action_surface="person_evidence_review",
                action_scope=item.get("review_kind") or "person_evidence_review",
                entity_type="person_or_name",
                entity_key=item.get("person_or_name_key") or item.get("person_key") or "",
                display_label=item.get("display_name") or "",
                role=item.get("role") or "",
                program_name="",
                priority=priority,
                impact_count=max(as_int(item.get("review_ready_record_count")), 1),
                readiness_status=item.get("packet_status") or "",
                blocker_status=item.get("acceptance_blocker") or "pending_reviewer_decision",
                required_next_evidence=item.get("required_reviewer_action") or "",
                recommended_next_action="record_accept_reject_or_needs_more_evidence_decision",
                source_artifact=source,
                target_artifact="artifacts/data/person_evidence_reviewer_decisions.csv",
                downstream_tables=[
                    "person_evidence_reviewer_decision_queue",
                    "person_evidence_reviewer_decision_audit",
                    "accepted_enrichment_claims",
                    "evidence_claims",
                ],
                evidence={
                    "packet_key": item.get("packet_key"),
                    "packet_fingerprint": item.get("packet_fingerprint"),
                    "best_decision": item.get("best_decision"),
                    "best_source_url": item.get("best_source_url"),
                    "top_claim_types": item.get("top_claim_types"),
                    "top_match_features": item.get("top_match_features"),
                    "display_safety_status": item.get("display_safety_status"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def contact_actions(generated_at: str) -> list[dict]:
    rows = []
    batch_path = ARTIFACTS / "contact_verification_batches.csv"
    if batch_path.exists():
        source = "artifacts/data/contact_verification_batches.csv"
        for item in read_csv(batch_path):
            status = item.get("batch_status") or item.get("queue_status") or ""
            if status == "blocked_before_contact_review":
                base_priority = 720
            elif status == "same_value_contact_review_ready":
                base_priority = 350
            elif status == "missing_value_contact_review_ready":
                base_priority = 330
            else:
                base_priority = 320
            rows.append(
                row(
                    action_surface="contact_verification",
                    action_scope=f"{item.get('verification_lane') or ''}:{status}",
                    entity_type="contact_verification_batch",
                    entity_key=item.get("contact_verification_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("role"),
                            item.get("canonical_contact_domain"),
                            item.get("reobservation_status"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("role") or "",
                    program_name="",
                    priority=base_priority + min(as_int(item.get("contact_count")) * 2, 80),
                    impact_count=max(as_int(item.get("contact_count")), as_int(item.get("person_count")), 1),
                    readiness_status=status,
                    blocker_status=item.get("reobservation_status") or item.get("queue_status") or "",
                    required_next_evidence=item.get("acceptance_boundary") or item.get("review_instructions") or "",
                    recommended_next_action=item.get("recommended_operator_action") or "",
                    source_artifact=source,
                    target_artifact=item.get("target_artifact") or "artifacts/data/contact_verification_reviewer_decisions.csv",
                    downstream_tables=[
                        "contact_verification_batches",
                        "contact_verification_reviewer_decision_dossiers",
                        "contact_verification_reviewer_decision_queue",
                        "contact_verification_reviewer_decision_audit",
                        "accepted_verified_contact_facts",
                        "contact_verification_contracts",
                        "contact_reobservation_audit",
                        "contact_assurance_audit",
                        "person_contacts",
                    ],
                    evidence={
                        "contact_verification_batch_key": item.get("contact_verification_batch_key"),
                        "execution_order": item.get("execution_order"),
                        "queue_status": item.get("queue_status"),
                        "verification_lane": item.get("verification_lane"),
                        "reobservation_status": item.get("reobservation_status"),
                        "canonical_contact_domain": item.get("canonical_contact_domain"),
                        "source_assurance_class": item.get("source_assurance_class"),
                        "contact_count": item.get("contact_count"),
                        "person_count": item.get("person_count"),
                        "same_value_reobserved_count": item.get("same_value_reobserved_count"),
                        "value_absent_count": item.get("value_absent_count"),
                        "pending_decision_count": item.get("pending_decision_count"),
                        "not_ready_count": item.get("not_ready_count"),
                        "domain_review_count": item.get("domain_review_count"),
                        "contact_type_counts": parse_json(item.get("contact_type_counts_json"), {}),
                        "source_key_counts": parse_json(item.get("source_key_counts_json"), {}),
                        "domain_status_counts": parse_json(item.get("domain_status_counts_json"), {}),
                        "top_display_names": item.get("top_display_names"),
                        "top_dossiers": parse_json(item.get("top_dossiers_json"), []),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    dossier_path = ARTIFACTS / "contact_verification_reviewer_decision_dossiers.csv"
    decision_queue_path = ARTIFACTS / "contact_verification_reviewer_decision_queue.csv"
    contract_path = ARTIFACTS / "contact_verification_contracts.csv"
    source_path = (
        dossier_path
        if dossier_path.exists()
        else decision_queue_path
        if decision_queue_path.exists()
        else contract_path
        if contract_path.exists()
        else ARTIFACTS / "contact_assurance_audit.csv"
    )
    source = str(source_path.relative_to(ROOT))
    for item in read_csv(source_path):
        status = item.get("queue_status") or item.get("verification_lane") or item.get("assurance_status") or ""
        queue_evidence = parse_json(item.get("evidence_json"), {})
        reobservation = queue_evidence.get("current_source_reobservation") or {}
        if status == "ready_for_reviewer_verification":
            base_priority = 330
        elif status == "fresh_official_reobservation_required":
            base_priority = 290
        elif status == "official_public_unverified_contact":
            base_priority = 290
        else:
            base_priority = 720
        rows.append(
            row(
                action_surface="contact_verification",
                action_scope=status,
                entity_type="person_contact",
                entity_key=item.get("reviewer_decision_key") or item.get("contact_contract_key") or item.get("contact_assurance_key") or item.get("contact_key") or "",
                display_label=item.get("display_name") or "",
                role=item.get("role") or "",
                program_name="",
                priority=base_priority + as_int(item.get("assurance_level")) * 10,
                impact_count=1,
                readiness_status=item.get("operational_use_status") or item.get("display_safety_status") or "",
                blocker_status=item.get("decision_blocker")
                or item.get("queue_status")
                or item.get("required_reviewer_action")
                or item.get("required_next_check")
                or "",
                required_next_evidence=item.get("evidence_required_to_verify")
                or item.get("acceptance_boundary")
                or "Verify current official source, person identity, contact domain, and intended contact scope before treating as a verified contact fact.",
                recommended_next_action=item.get("recommended_next_action") or item.get("required_reviewer_action") or "",
                source_artifact=source,
                target_artifact=(
                    "artifacts/data/contact_verification_reviewer_decisions.csv"
                    if source_path in {decision_queue_path, dossier_path}
                    else "artifacts/data/contact_verification_contracts.csv"
                ),
                downstream_tables=[
                    "contact_verification_reviewer_decision_queue",
                    "contact_verification_reviewer_decision_audit",
                    "contact_verification_reviewer_decision_dossiers",
                    "accepted_verified_contact_facts",
                    "contact_verification_contracts",
                    "contact_assurance_audit",
                    "person_contacts",
                ],
                evidence={
                    "reviewer_decision_key": item.get("reviewer_decision_key"),
                    "contact_fingerprint": item.get("contact_fingerprint"),
                    "contact_type": item.get("contact_type"),
                    "contact_domain": item.get("contact_domain"),
                    "domain_status": item.get("domain_status"),
                    "source_url": item.get("source_url"),
                    "source_assurance_class": item.get("source_assurance_class"),
                    "verification_status": item.get("verification_status") or item.get("current_assurance_status"),
                    "display_safety_status": item.get("current_display_safety_status") or item.get("display_safety_status"),
                    "stale_after_date": item.get("stale_after_date"),
                    "if_reobserved_same_value_change_type": item.get("if_reobserved_same_value_change_type"),
                    "if_missing_on_refresh_change_type": item.get("if_missing_on_refresh_change_type"),
                    "review_question": item.get("review_question"),
                    "decision_status": item.get("decision_status"),
                    "decision_blocker": item.get("decision_blocker"),
                    "manual_decision_template_json": item.get("manual_decision_template_json"),
                    "reobservation_status": reobservation.get("reobservation_status"),
                    "reobserved_same_value": reobservation.get("reobserved_same_value"),
                    "reobserved_at": item.get("reobserved_at") or reobservation.get("reobserved_at"),
                    "reobservation_evidence_strength": item.get("reobservation_evidence_strength")
                    or reobservation.get("evidence_strength"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def search_utility_actions(generated_at: str) -> list[dict]:
    rows = []
    batch_path = ARTIFACTS / "search_utility_execution_batches.csv"
    if batch_path.exists():
        source = "artifacts/data/search_utility_execution_batches.csv"
        for item in read_csv(batch_path):
            lane = item.get("batch_lane") or ""
            priority = {
                "query_execution": 760,
                "endpoint_retry": 740,
                "candidate_probe": 620,
            }.get(lane, 360) + min(as_int(item.get("action_impact_count")), 220)
            rows.append(
                row(
                    action_surface="search_utility_assurance",
                    action_scope=f"{item.get('utility_family') or ''}:{item.get('batch_lane') or ''}",
                    entity_type="search_utility_execution_batch",
                    entity_key=item.get("search_utility_execution_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("utility_name"),
                            item.get("batch_lane"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role="",
                    program_name="",
                    priority=priority,
                    impact_count=max(as_int(item.get("action_impact_count")), 1),
                    readiness_status=item.get("batch_status") or "",
                    blocker_status=item.get("error_signature") or item.get("http_status_signature") or item.get("candidate_status_signature") or "",
                    required_next_evidence=item.get("required_next_evidence") or "",
                    recommended_next_action=item.get("recommended_operator_action") or "",
                    source_artifact=source,
                    target_artifact=item.get("target_artifact") or "",
                    downstream_tables=[
                        "search_utility_execution_batches",
                        "search_utility_assurance",
                        "official_program_source_search_observations",
                        "official_program_source_candidates",
                        "trainee_profile_discovery_candidates",
                        "prior_training_discovery_candidates",
                        "attending_historical_link_candidates",
                    ],
                    evidence={
                        "search_utility_execution_batch_key": item.get("search_utility_execution_batch_key"),
                        "execution_order": item.get("execution_order"),
                        "utility_key": item.get("utility_key"),
                        "utility_family": item.get("utility_family"),
                        "batch_lane": item.get("batch_lane"),
                        "query_artifact": item.get("query_artifact"),
                        "observation_artifact": item.get("observation_artifact"),
                        "candidate_artifact": item.get("candidate_artifact"),
                        "query_count": item.get("query_count"),
                        "unobserved_query_count": item.get("unobserved_query_count"),
                        "failed_observation_count": item.get("failed_observation_count"),
                        "candidate_count": item.get("candidate_count"),
                        "search_candidate_count": item.get("search_candidate_count"),
                        "action_impact_count": item.get("action_impact_count"),
                        "query_kind_counts": parse_json(item.get("query_kind_counts_json"), {}),
                        "http_status_counts": parse_json(item.get("http_status_counts_json"), {}),
                        "error_counts": parse_json(item.get("error_counts_json"), {}),
                        "candidate_status_counts": parse_json(item.get("candidate_status_counts_json"), {}),
                        "sample_queries": parse_json(item.get("sample_queries_json"), []),
                        "sample_observations": parse_json(item.get("sample_observations_json"), []),
                        "sample_candidates": parse_json(item.get("sample_candidates_json"), []),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    source = "artifacts/data/search_utility_assurance.csv"
    for item in read_csv(ARTIFACTS / "search_utility_assurance.csv"):
        status = item.get("search_execution_status") or ""
        priority = {
            "planned_not_executed": 760,
            "executed_blocked_by_search_endpoint": 740,
            "executed_partial_with_endpoint_errors": 690,
            "executed_success_with_results": 420,
            "executed_success_no_results": 260,
            "executed_no_results": 240,
            "no_query_manifest": 820,
        }.get(status, 300)
        impact = max(as_int(item.get("query_rows")), as_int(item.get("search_candidate_rows")), 1)
        rows.append(
            row(
                action_surface="search_utility_assurance",
                action_scope=item.get("utility_family") or "",
                entity_type="search_utility",
                entity_key=item.get("utility_key") or "",
                display_label=item.get("utility_name") or "",
                role="",
                program_name="",
                priority=priority,
                impact_count=impact,
                readiness_status=status,
                blocker_status=item.get("source_quality_learning") or "",
                required_next_evidence="Execute or retry search observations with a reliable provider before treating candidate absence as public-source absence.",
                recommended_next_action=item.get("recommended_next_action") or "",
                source_artifact=source,
                target_artifact=item.get("candidate_artifact") or "",
                downstream_tables=[
                    "search_utility_assurance",
                    "official_program_source_candidates",
                    "trainee_profile_discovery_candidates",
                    "prior_training_discovery_candidates",
                    "attending_historical_link_candidates",
                ],
                evidence={
                    "query_rows": item.get("query_rows"),
                    "search_observation_rows": item.get("search_observation_rows"),
                    "search_candidate_rows": item.get("search_candidate_rows"),
                    "non_200_search_rows": item.get("non_200_search_rows"),
                    "by_search_http_status_json": item.get("by_search_http_status_json"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def source_quality_policy_actions(generated_at: str) -> list[dict]:
    rows = []
    source = "artifacts/data/source_quality_policy_recommendations.csv"
    for item in read_csv(ARTIFACTS / "source_quality_policy_recommendations.csv"):
        priority = as_int(item.get("action_priority"))
        rows.append(
            row(
                action_surface="source_quality_policy",
                action_scope=f"{item.get('policy_lane') or ''}:{item.get('action_readiness') or ''}",
                entity_type="source_quality_policy_recommendation",
                entity_key=item.get("recommendation_key") or "",
                display_label=" | ".join(
                    part
                    for part in [
                        item.get("utility_label"),
                        item.get("policy_lane"),
                        item.get("quality_band"),
                    ]
                    if part
                ),
                role="",
                program_name="",
                priority=priority,
                impact_count=1,
                readiness_status=item.get("action_readiness") or "",
                blocker_status=item.get("policy_status") or "",
                required_next_evidence=item.get("required_next_evidence") or "",
                recommended_next_action=item.get("recommended_next_action") or "",
                source_artifact=source,
                target_artifact="artifacts/data/source_utility_scorecard.csv",
                downstream_tables=parse_json(item.get("downstream_tables_json"), ["source_quality_policy_recommendations"]),
                evidence={
                    "recommendation_key": item.get("recommendation_key"),
                    "source_row_type": item.get("source_row_type"),
                    "utility_key": item.get("utility_key"),
                    "source_family": item.get("source_family"),
                    "claim_surface": item.get("claim_surface"),
                    "score": item.get("score"),
                    "quality_band": item.get("quality_band"),
                    "policy_lane": item.get("policy_lane"),
                    "policy_status": item.get("policy_status"),
                    "action_readiness": item.get("action_readiness"),
                    "acceptance_posture": item.get("acceptance_posture"),
                    "collector_posture": item.get("collector_posture"),
                    "reviewer_posture": item.get("reviewer_posture"),
                    "trend_relevance": item.get("trend_relevance"),
                    "evidence_standard": item.get("evidence_standard"),
                    "source_artifacts": parse_json(item.get("source_artifacts_json"), []),
                    "search_assurance": parse_json(item.get("search_assurance_evidence_json"), {}),
                },
                generated_at=generated_at,
            )
        )
    return rows


def temporal_contract_actions(generated_at: str) -> list[dict]:
    batch_path = ARTIFACTS / "training_temporal_contract_batches.csv"
    if batch_path.exists():
        rows = []
        source = "artifacts/data/training_temporal_contract_batches.csv"
        for item in read_csv(batch_path):
            lane = item.get("policy_lane") or ""
            priority = (720 if lane == "manual_review_required" else 640) + min(as_int(item.get("contract_count")), 220)
            rows.append(
                row(
                    action_surface="training_temporal_contract",
                    action_scope=f"{lane}:{item.get('batch_status') or ''}",
                    entity_type="training_temporal_contract_batch",
                    entity_key=item.get("temporal_contract_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("program_name"),
                            item.get("role"),
                            item.get("lifecycle_code"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("role") or "",
                    program_name=item.get("program_name") or "",
                    priority=priority,
                    impact_count=max(as_int(item.get("contract_count")), 1),
                    readiness_status=item.get("batch_status") or "",
                    blocker_status=item.get("temporal_state_signature") or item.get("diff_readiness_status_signature") or "",
                    required_next_evidence=item.get("required_next_evidence") or "",
                    recommended_next_action=item.get("recommended_operator_action") or "",
                    source_artifact=source,
                    target_artifact=item.get("target_artifact") or "artifacts/data/training_state_transition_plan.csv",
                    downstream_tables=[
                        "training_temporal_contract_batches",
                        "training_temporal_contracts",
                        "training_temporal_contract_rollups",
                        "training_state_transition_plan",
                        "training_state_transition_events",
                        "person_training_stage_state",
                        "person_training_states",
                        "official_roster_refresh_batches",
                    ],
                    evidence={
                        "temporal_contract_batch_key": item.get("temporal_contract_batch_key"),
                        "execution_order": item.get("execution_order"),
                        "policy_lane": lane,
                        "role": item.get("role"),
                        "trainee_category": item.get("trainee_category"),
                        "program_name": item.get("program_name"),
                        "lifecycle_code": item.get("lifecycle_code"),
                        "next_refresh_contract": item.get("next_refresh_contract"),
                        "contract_count": item.get("contract_count"),
                        "person_count": item.get("person_count"),
                        "stale_by_refresh_count": item.get("stale_by_refresh_count"),
                        "fresh_observation_required_count": item.get("fresh_observation_required_count"),
                        "source_refresh_required_count": item.get("source_refresh_required_count"),
                        "human_review_required_count": item.get("human_review_required_count"),
                        "diff_readiness_counts": parse_json(item.get("diff_readiness_counts_json"), {}),
                        "temporal_state_counts": parse_json(item.get("temporal_state_counts_json"), {}),
                        "stage_code_counts": parse_json(item.get("stage_code_counts_json"), {}),
                        "review_triggers": parse_json(item.get("review_triggers_json"), []),
                        "top_contracts": parse_json(item.get("top_contracts_json"), []),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    grouped: dict[tuple[str, str, str, str, str], dict] = defaultdict(lambda: {"count": 0, "sample": None})
    for item in read_csv(ARTIFACTS / "training_temporal_contracts.csv"):
        lane = item.get("policy_lane") or ""
        if lane not in {"manual_review_required", "source_refresh_required"}:
            continue
        key = (
            lane,
            item.get("role") or "",
            item.get("program_name") or "",
            item.get("lifecycle_code") or "",
            item.get("next_refresh_contract") or "",
        )
        grouped[key]["count"] += 1
        grouped[key]["sample"] = grouped[key]["sample"] or item
    rows = []
    for (lane, role, program_name, lifecycle_code, contract), data in grouped.items():
        sample = data["sample"] or {}
        count = data["count"]
        priority = (680 if lane == "manual_review_required" else 610) + min(count, 300)
        rows.append(
            row(
                action_surface="training_temporal_contract",
                action_scope=lane,
                entity_type="program_role_lifecycle",
                entity_key=stable_key(program_name, role, lifecycle_code, contract),
                display_label=" | ".join(part for part in [program_name, role, lifecycle_code] if part),
                role=role,
                program_name=program_name,
                priority=priority,
                impact_count=count,
                readiness_status=sample.get("diff_readiness_status") or lane,
                blocker_status=sample.get("temporal_validity_status") or "",
                required_next_evidence=sample.get("evidence_required_to_retain") or "",
                recommended_next_action=sample.get("recommended_operator_action") or "",
                source_artifact="artifacts/data/training_temporal_contracts.csv",
                target_artifact="artifacts/data/training_state_transition_plan.csv",
                downstream_tables=[
                    "training_temporal_contracts",
                    "training_state_transition_plan",
                    "training_state_transition_events",
                    "person_training_states",
                ],
                evidence={
                    "lifecycle_code": lifecycle_code,
                    "next_refresh_contract": contract,
                    "sample_person_key": sample.get("person_key"),
                    "sample_display_name": sample.get("display_name"),
                    "sample_current_stage_code": sample.get("current_stage_code"),
                    "stale_after_date": sample.get("stale_after_date"),
                    "projected_refresh_date": sample.get("projected_refresh_date"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def official_roster_refresh_actions(generated_at: str) -> list[dict]:
    rows = []
    source_path = ARTIFACTS / "official_roster_refresh_workbench.csv"
    if not source_path.exists():
        return rows
    source = "artifacts/data/official_roster_refresh_workbench.csv"
    for item in read_csv(source_path):
        priority = 780 + as_int(item.get("refresh_priority")) // 3 + min(as_int(item.get("contract_count")), 80)
        rows.append(
            row(
                action_surface="official_roster_refresh",
                action_scope=item.get("refresh_lane") or "official_roster_refresh",
                entity_type="source_program_role",
                entity_key=item.get("refresh_key") or stable_key(item.get("source_key"), item.get("program_name"), item.get("role")),
                display_label=" | ".join(part for part in [item.get("program_name"), item.get("role")] if part),
                role=item.get("role") or "",
                program_name=item.get("program_name") or "",
                priority=priority,
                impact_count=max(as_int(item.get("contract_count")), 1),
                readiness_status=item.get("refresh_difficulty") or "",
                blocker_status=item.get("parser_status") or item.get("refresh_lane") or "",
                required_next_evidence=item.get("evidence_required") or "",
                recommended_next_action=item.get("recommended_next_action") or "",
                source_artifact=source,
                target_artifact="artifacts/data/training_state_transition_events.csv",
                downstream_tables=[
                    "official_roster_refresh_workbench",
                    "training_temporal_contracts",
                    "training_state_transition_plan",
                    "person_training_states",
                    "sources",
                ],
                evidence={
                    "source_key": item.get("source_key"),
                    "source_url": item.get("source_url"),
                    "http_status": item.get("http_status"),
                    "policy_lane_counts_json": item.get("policy_lane_counts_json"),
                    "diff_readiness_counts_json": item.get("diff_readiness_counts_json"),
                    "expected_change_summary": item.get("expected_change_summary"),
                    "collector_hint": item.get("collector_hint"),
                    "sample_people_json": item.get("sample_people_json"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def roster_execution_audit_by_collector() -> dict[str, dict]:
    rows = {}
    for item in read_csv(ARTIFACTS / "official_roster_refresh_execution_audit.csv"):
        if item.get("audit_scope") == "official_roster_refresh_aggregate":
            continue
        collector = item.get("collector_command") or ""
        if not collector:
            continue
        rows[collector] = item
    return rows


def apply_roster_execution_context(item: dict, priority: int, audit_by_collector: dict[str, dict]) -> tuple[int, str, str, str, dict]:
    """Return execution-aware priority/status/action/evidence for a roster batch."""
    audit = audit_by_collector.get(item.get("collector_hint") or "")
    evidence = {}
    if not audit:
        return priority, item.get("batch_status") or "", item.get("blocked_reason") or item.get("parser_status") or "", item.get("recommended_next_action") or "", evidence
    evidence = {
        "execution_audit_key": audit.get("execution_audit_key"),
        "refreshed_at": audit.get("refreshed_at"),
        "execution_status": audit.get("execution_status"),
        "state_delta_status": audit.get("state_delta_status"),
        "current_snapshot_id": audit.get("current_snapshot_id"),
        "previous_snapshot_id": audit.get("previous_snapshot_id"),
        "snapshot_comparison_kind": audit.get("snapshot_comparison_kind"),
        "unchanged_state_count": audit.get("unchanged_state_count"),
        "added_state_count": audit.get("added_state_count"),
        "removed_state_count": audit.get("removed_state_count"),
        "changed_state_count": audit.get("changed_state_count"),
        "preserved_source_count": audit.get("preserved_source_count"),
        "skipped_source_count": audit.get("skipped_source_count"),
    }
    if item.get("batch_status") == "blocked_needs_parser_support_review":
        return priority, item.get("batch_status") or "", item.get("blocked_reason") or item.get("parser_status") or "", item.get("recommended_next_action") or "", evidence
    if audit.get("state_delta_status") != "fresh_refresh_no_state_delta":
        return priority, item.get("batch_status") or "", item.get("blocked_reason") or item.get("parser_status") or "", item.get("recommended_next_action") or "", evidence
    priority_cap = 720 if as_int(audit.get("preserved_source_count")) else 640
    return (
        min(priority, priority_cap),
        "recently_refreshed_no_state_delta",
        audit.get("execution_status") or "",
        "defer_roster_rerun_until_next_refresh_window_or_source_error_resolution",
        evidence,
    )


def official_roster_refresh_batch_actions(generated_at: str) -> list[dict]:
    rows = []
    source_path = ARTIFACTS / "official_roster_refresh_batches.csv"
    if not source_path.exists():
        return rows
    source = "artifacts/data/official_roster_refresh_batches.csv"
    audit_by_collector = roster_execution_audit_by_collector()
    for item in read_csv(source_path):
        priority = 860 + as_int(item.get("max_refresh_priority")) // 4 + min(as_int(item.get("contract_count")), 100)
        if item.get("batch_status") == "blocked_needs_parser_support_review":
            priority -= 120
        priority, readiness_status, blocker_status, recommended_next_action, execution_evidence = apply_roster_execution_context(item, priority, audit_by_collector)
        rows.append(
            row(
                action_surface="official_roster_refresh_execution",
                action_scope=item.get("batch_lane") or item.get("batch_status") or "official_roster_refresh_batch",
                entity_type="roster_refresh_batch",
                entity_key=item.get("roster_batch_key") or "",
                display_label=" | ".join(
                    part
                    for part in [
                        item.get("collector_hint"),
                        item.get("source_domain"),
                        f"batch {item.get('execution_order')}",
                    ]
                    if part
                ),
                role="",
                program_name="",
                priority=priority,
                impact_count=max(as_int(item.get("contract_count")), as_int(item.get("source_program_count")), 1),
                readiness_status=readiness_status,
                blocker_status=blocker_status,
                required_next_evidence=item.get("evidence_required") or "",
                recommended_next_action=recommended_next_action,
                source_artifact=source,
                target_artifact="artifacts/data/training_state_transition_events.csv",
                downstream_tables=[
                    "official_roster_refresh_batches",
                    "official_roster_refresh_execution_audit",
                    "official_roster_refresh_workbench",
                    "training_temporal_contracts",
                    "training_state_snapshots",
                    "training_state_transition_events",
                    "person_training_states",
                    "sources",
                ],
                evidence={
                    "collector_hint": item.get("collector_hint"),
                    "parser_status": item.get("parser_status"),
                    "source_domain": item.get("source_domain"),
                    "source_count": item.get("source_count"),
                    "source_program_count": item.get("source_program_count"),
                    "contract_count": item.get("contract_count"),
                    "expected_advancement_count": item.get("expected_advancement_count"),
                    "expected_completion_count": item.get("expected_completion_count"),
                    "source_refresh_required_count": item.get("source_refresh_required_count"),
                    "manual_review_required_count": item.get("manual_review_required_count"),
                    "command_hint": item.get("command_hint"),
                    "source_urls_json": item.get("source_urls_json"),
                    "execution_audit": execution_evidence,
                },
                generated_at=generated_at,
            )
        )
    return rows


def official_profile_discovery_actions(generated_at: str) -> list[dict]:
    rows = []
    batch_path = ARTIFACTS / "official_profile_discovery_batches.csv"
    if batch_path.exists():
        batch_packet_path = ARTIFACTS / "official_profile_discovery_batch_packets.csv"
        source = (
            "artifacts/data/official_profile_discovery_batch_packets.csv"
            if batch_packet_path.exists()
            else "artifacts/data/official_profile_discovery_batches.csv"
        )
        packets_by_batch: dict[str, list[dict]] = defaultdict(list)
        if batch_packet_path.exists():
            for packet_row in read_csv(batch_packet_path):
                packets_by_batch[packet_row.get("official_profile_discovery_batch_key") or ""].append(packet_row)
        for item in read_csv(batch_path):
            lane = item.get("discovery_lane") or "official_profile_discovery"
            packet_rows = packets_by_batch.get(item.get("official_profile_discovery_batch_key") or "", [])
            priority = 650 + as_int(item.get("max_discovery_priority")) // 3
            if lane == "review_official_profile_candidate":
                priority += 80
            elif lane == "search_endpoint_blocked_retry":
                priority += 35
            elif lane == "planned_search_not_executed":
                priority += 20
            priority += min(as_int(item.get("workbench_count")) * 2, 80)
            rows.append(
                row(
                    action_surface="official_profile_discovery",
                    action_scope=f"{lane}:{item.get('batch_status') or ''}",
                    entity_type="official_profile_discovery_batch",
                    entity_key=item.get("official_profile_discovery_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            lane,
                            item.get("role"),
                            item.get("source_domain"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("role") or "",
                    program_name="",
                    priority=priority,
                    impact_count=max(as_int(item.get("workbench_count")), as_int(item.get("person_count")), 1),
                    readiness_status=item.get("batch_status") or "",
                    blocker_status=item.get("query_status_signature") or item.get("candidate_status_signature") or "",
                    required_next_evidence=item.get("required_next_evidence") or "",
                    recommended_next_action=item.get("recommended_operator_action") or "",
                    source_artifact=source,
                    target_artifact=item.get("target_artifact") or "artifacts/data/trainee_profile_discovery_candidates.csv",
                    downstream_tables=[
                        "official_profile_discovery_batches",
                        "official_profile_discovery_batch_packets",
                        "official_profile_discovery_workbench",
                        "official_profile_reobservation_audit",
                        "official_profile_reviewer_decision_queue",
                        "official_profile_reviewer_decision_audit",
                        "official_profile_reviewer_decision_dossiers",
                        "trainee_profile_search_queries",
                        "trainee_profile_search_observations",
                        "trainee_profile_discovery_candidates",
                        "evidence_claims",
                    ],
                    evidence={
                        "official_profile_discovery_batch_key": item.get("official_profile_discovery_batch_key"),
                        "execution_order": item.get("execution_order"),
                        "discovery_lane": lane,
                        "batch_status": item.get("batch_status"),
                        "source_domain": item.get("source_domain"),
                        "workbench_count": item.get("workbench_count"),
                        "person_count": item.get("person_count"),
                        "query_count": item.get("query_count"),
                        "observed_query_count": item.get("observed_query_count"),
                        "unsearched_query_count": item.get("unsearched_query_count"),
                        "blocked_query_count": item.get("blocked_query_count"),
                        "candidate_count": item.get("candidate_count"),
                        "official_candidate_count": item.get("official_candidate_count"),
                        "low_signal_candidate_count": item.get("low_signal_candidate_count"),
                        "query_status_counts": parse_json(item.get("query_status_counts_json"), {}),
                        "candidate_status_counts": parse_json(item.get("candidate_status_counts_json"), {}),
                        "profile_discovery_packet_rows": len(packet_rows),
                        "top_packet_support_statuses": dict(
                            Counter(packet.get("support_status") or "" for packet in packet_rows).most_common(8)
                        ),
                        "top_profile_discovery_packets": [
                            {
                                "display_name": packet.get("display_name"),
                                "discovery_lane": packet.get("discovery_lane"),
                                "packet_status": packet.get("packet_status"),
                                "support_status": packet.get("support_status"),
                                "best_candidate_url": packet.get("best_candidate_url"),
                                "reviewer_decision_key": packet.get("reviewer_decision_key"),
                                "recommended_operator_action": packet.get("recommended_operator_action"),
                            }
                            for packet in packet_rows[:10]
                        ],
                        "top_workbench_rows": parse_json(item.get("top_workbench_rows_json"), []),
                        "execution_instructions": item.get("execution_instructions"),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    source_path = ARTIFACTS / "official_profile_discovery_workbench.csv"
    if not source_path.exists():
        return rows
    workbench_source = "artifacts/data/official_profile_discovery_workbench.csv"
    dossier_source = "artifacts/data/official_profile_reviewer_decision_dossiers.csv"
    profile_dossiers_by_workbench = {
        item.get("profile_workbench_key"): item
        for item in read_csv(ARTIFACTS / "official_profile_reviewer_decision_dossiers.csv")
        if item.get("profile_workbench_key")
    }
    profile_audit_by_workbench = {
        item.get("profile_workbench_key"): item
        for item in read_csv(ARTIFACTS / "official_profile_reviewer_decision_audit.csv")
        if item.get("profile_workbench_key")
    }
    profile_reobs_by_workbench = {
        item.get("profile_workbench_key"): item
        for item in read_csv(ARTIFACTS / "official_profile_reobservation_audit.csv")
        if item.get("profile_workbench_key")
    }
    for item in read_csv(source_path):
        dossier = profile_dossiers_by_workbench.get(item.get("profile_workbench_key") or "", {})
        audit = profile_audit_by_workbench.get(item.get("profile_workbench_key") or "", {})
        reobservation = profile_reobs_by_workbench.get(item.get("profile_workbench_key") or "", {})
        source = dossier_source if dossier else workbench_source
        priority = 650 + as_int(item.get("discovery_priority")) // 3
        if item.get("discovery_lane") == "review_official_profile_candidate":
            priority += 80
        elif item.get("discovery_lane") == "search_endpoint_blocked_retry":
            priority += 35
        elif item.get("discovery_lane") == "planned_search_not_executed":
            priority += 20
        rows.append(
            row(
                action_surface="official_profile_discovery",
                action_scope=item.get("discovery_lane") or "official_profile_discovery",
                entity_type="person_profile_gap",
                entity_key=dossier.get("reviewer_decision_key")
                or item.get("profile_workbench_key")
                or stable_key(item.get("person_key"), item.get("task_key")),
                display_label=item.get("display_name") or "",
                role=item.get("role") or "",
                program_name=item.get("program_name") or "",
                priority=priority,
                impact_count=1,
                readiness_status=item.get("profile_gap_status") or "",
                blocker_status=dossier.get("decision_blocker")
                or item.get("best_candidate_status")
                or item.get("discovery_lane")
                or "",
                required_next_evidence=dossier.get("acceptance_boundary") or item.get("evidence_required") or "",
                recommended_next_action=dossier.get("recommended_next_action")
                or audit.get("recommended_next_action")
                or item.get("recommended_next_action")
                or "",
                source_artifact=source,
                target_artifact=(
                    "artifacts/data/official_profile_reviewer_decisions.csv"
                    if dossier
                    else "artifacts/data/trainee_profile_discovery_candidates.csv"
                ),
                downstream_tables=[
                    "official_profile_discovery_workbench",
                    "official_profile_reobservation_audit",
                    "official_profile_reviewer_decision_queue",
                    "official_profile_reviewer_decision_audit",
                    "official_profile_reviewer_decision_dossiers",
                    "trainee_profile_search_queries",
                    "trainee_profile_search_observations",
                    "trainee_profile_discovery_candidates",
                    "evidence_claims",
                ],
                evidence={
                    "person_key": item.get("person_key"),
                    "task_key": item.get("task_key"),
                    "query_count": item.get("query_count"),
                    "observed_query_count": item.get("observed_query_count"),
                    "unsearched_query_count": item.get("unsearched_query_count"),
                    "blocked_query_count": item.get("blocked_query_count"),
                    "official_candidate_count": item.get("official_candidate_count"),
                    "best_candidate_url": item.get("best_candidate_url"),
                    "best_candidate_confidence": item.get("best_candidate_confidence"),
                    "source_domains": item.get("source_domains"),
                    "profile_reobservation_status": reobservation.get("reobservation_status"),
                    "profile_reobserved_at": reobservation.get("reobserved_at"),
                    "profile_reobservation_title": reobservation.get("title"),
                    "profile_reobservation_canonical_url": reobservation.get("canonical_url"),
                    "profile_decision_status": dossier.get("decision_status") or audit.get("decision_status"),
                    "profile_decision_blocker": dossier.get("decision_blocker") or audit.get("decision_blocker"),
                    "profile_fingerprint": dossier.get("profile_fingerprint"),
                    "manual_decision_template_json": dossier.get("manual_decision_template_json"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def lifecycle_duration_review_actions(generated_at: str) -> list[dict]:
    rows = []
    batch_path = ARTIFACTS / "program_lifecycle_duration_review_batches.csv"
    if batch_path.exists():
        source = "artifacts/data/program_lifecycle_duration_review_batches.csv"
        for item in read_csv(batch_path):
            status = item.get("batch_status") or ""
            queue_status = item.get("queue_status") or ""
            if status == "duration_manual_decision_ready":
                priority = 830
            elif status == "duration_context_review_ready":
                priority = 700
            elif status == "duration_evidence_collection_required":
                priority = 445
            else:
                priority = 520
            rows.append(
                row(
                    action_surface="program_lifecycle_duration_review",
                    action_scope=f"{queue_status}:{status}",
                    entity_type="program_lifecycle_duration_review_batch",
                    entity_key=item.get("duration_review_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("official_program_type"),
                            item.get("duration_evidence_status"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("official_program_type") or "",
                    program_name="",
                    priority=priority + min(as_int(item.get("review_row_count")), 25),
                    impact_count=max(as_int(item.get("review_row_count")), 1),
                    readiness_status=status,
                    blocker_status=item.get("decision_blocker_signature")
                    or item.get("decision_status_signature")
                    or item.get("duration_evidence_status")
                    or "",
                    required_next_evidence=item.get("required_next_evidence") or "",
                    recommended_next_action=item.get("recommended_operator_action") or "",
                    source_artifact=source,
                    target_artifact=item.get("target_artifact") or "artifacts/data/program_lifecycle_duration_reviewer_decisions.csv",
                    downstream_tables=[
                        "program_lifecycle_duration_review_batches",
                        "program_lifecycle_duration_reviewer_decision_queue",
                        "program_lifecycle_duration_reviewer_decision_audit",
                        "program_lifecycle_duration_reviewer_decisions",
                        "accepted_program_lifecycle_duration_mappings",
                        "program_lifecycle_rules",
                        "training_temporal_contracts",
                    ],
                    evidence={
                        "duration_review_batch_key": item.get("duration_review_batch_key"),
                        "execution_order": item.get("execution_order"),
                        "batch_status": status,
                        "queue_status": queue_status,
                        "decision_status_signature": item.get("decision_status_signature"),
                        "decision_blocker_signature": item.get("decision_blocker_signature"),
                        "duration_evidence_status": item.get("duration_evidence_status"),
                        "review_row_count": item.get("review_row_count"),
                        "program_count": item.get("program_count"),
                        "ready_queue_count": item.get("ready_queue_count"),
                        "context_review_count": item.get("context_review_count"),
                        "not_ready_count": item.get("not_ready_count"),
                        "pending_decision_count": item.get("pending_decision_count"),
                        "queue_status_counts": parse_json(item.get("queue_status_counts_json"), {}),
                        "decision_status_counts": parse_json(item.get("decision_status_counts_json"), {}),
                        "duration_evidence_status_counts": parse_json(
                            item.get("duration_evidence_status_counts_json"), {}
                        ),
                        "top_review_rows": parse_json(item.get("top_review_rows_json"), []),
                        "manual_decision_templates": parse_json(item.get("manual_decision_templates_json"), []),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    source = "artifacts/data/program_lifecycle_duration_reviewer_decision_queue.csv"
    audit_by_key = {
        item.get("reviewer_decision_key"): item
        for item in read_csv(ARTIFACTS / "program_lifecycle_duration_reviewer_decision_audit.csv")
        if item.get("reviewer_decision_key")
    }
    for item in read_csv(ARTIFACTS / "program_lifecycle_duration_reviewer_decision_queue.csv"):
        audit = audit_by_key.get(item.get("reviewer_decision_key") or "", {})
        decision_status = audit.get("decision_status") or ""
        if decision_status in {"accepted_reviewer_decision", "rejected_by_reviewer"}:
            continue
        status = item.get("queue_status") or ""
        if status == "ready_for_reviewer_decision":
            priority = 815
        elif status == "context_review_required_before_decision":
            priority = 690
        else:
            priority = 430
        rows.append(
            row(
                action_surface="program_lifecycle_duration_review",
                action_scope=status or "duration_review",
                entity_type="official_program",
                entity_key=item.get("official_program_key") or item.get("duration_evidence_key") or "",
                display_label=item.get("official_program_name") or item.get("matched_program_name") or "",
                role=item.get("official_program_type") or "",
                program_name=item.get("matched_program_name") or item.get("official_program_name") or "",
                priority=priority,
                impact_count=1,
                readiness_status=status,
                blocker_status=audit.get("decision_blocker") or decision_status or item.get("duration_evidence_status") or "",
                required_next_evidence=item.get("required_reviewer_action") or "",
                recommended_next_action=(
                    "record_accept_reject_or_needs_more_evidence_decision"
                    if status == "ready_for_reviewer_decision" and not decision_status
                    else audit.get("recommended_next_action")
                    if decision_status
                    else item.get("recommended_next_action") or "collect_stronger_duration_or_scope_evidence"
                ),
                source_artifact=source,
                target_artifact="artifacts/data/program_lifecycle_duration_reviewer_decisions.csv",
                downstream_tables=[
                    "program_lifecycle_duration_reviewer_decision_queue",
                    "program_lifecycle_duration_reviewer_decision_audit",
                    "accepted_program_lifecycle_duration_mappings",
                    "program_lifecycle_rules",
                    "training_temporal_contracts",
                ],
                evidence={
                    "duration_evidence_key": item.get("duration_evidence_key"),
                    "evidence_fingerprint": item.get("evidence_fingerprint"),
                    "source_url": item.get("source_url"),
                    "page_title": item.get("page_title"),
                    "explicit_duration_years": item.get("explicit_duration_years"),
                    "duration_confidence": item.get("duration_confidence"),
                    "review_question": item.get("review_question"),
                    "decision_status": decision_status,
                    "reviewer_decision": audit.get("reviewer_decision") or "",
                    "decision_blocker": audit.get("decision_blocker") or "",
                },
                generated_at=generated_at,
            )
        )
    return rows


def enrichment_queue_actions(generated_at: str) -> list[dict]:
    batch_path = ARTIFACTS / "person_enrichment_execution_batches.csv"
    if batch_path.exists():
        rows = []
        source = "artifacts/data/person_enrichment_execution_batches.csv"
        roster_workbench_exists = (ARTIFACTS / "official_roster_refresh_workbench.csv").exists()
        evidence_triage_exists = (ARTIFACTS / "person_evidence_review_triage.csv").exists()
        profile_workbench_exists = (ARTIFACTS / "official_profile_discovery_workbench.csv").exists()
        for item in read_csv(batch_path):
            task_type = item.get("task_type") or ""
            if roster_workbench_exists and task_type == "current_roster_state_reconciliation":
                continue
            if evidence_triage_exists and task_type == "evidence_reconciliation_review":
                continue
            if profile_workbench_exists and task_type == "official_profile_search":
                continue
            priority = as_int(item.get("max_priority")) * 10 + min(as_int(item.get("person_count")), 250)
            rows.append(
                row(
                    action_surface="person_enrichment_execution",
                    action_scope=f"{item.get('source_family') or ''}:{task_type}:{item.get('batch_status') or ''}",
                    entity_type="person_enrichment_execution_batch",
                    entity_key=item.get("batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("source_family"),
                            task_type,
                            item.get("priority_band"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role="",
                    program_name="",
                    priority=priority,
                    impact_count=max(as_int(item.get("person_count")), as_int(item.get("task_count")), 1),
                    readiness_status=item.get("batch_status") or "",
                    blocker_status=item.get("blocked_reason") or "",
                    required_next_evidence=item.get("evidence_requirement") or "",
                    recommended_next_action=item.get("next_system_action") or "",
                    source_artifact=source,
                    target_artifact="artifacts/data/person_enrichment_execution_readiness.csv",
                    downstream_tables=[
                        "person_enrichment_execution_batches",
                        "person_enrichment_execution_readiness",
                        "person_enrichment_work_queue",
                        "person_enrichment_dossiers",
                        "person_evidence_review_batches",
                        "research_identity_review_batches",
                        "contact_verification_batches",
                        "official_profile_discovery_batches",
                        "official_roster_refresh_batches",
                        "evidence_reconciliation_decisions",
                        "accepted_enrichment_claims",
                    ],
                    evidence={
                        "batch_key": item.get("batch_key"),
                        "execution_order": item.get("execution_order"),
                        "task_type": task_type,
                        "source_family": item.get("source_family"),
                        "priority_band": item.get("priority_band"),
                        "execution_lane": item.get("execution_lane"),
                        "automation_status": item.get("automation_status"),
                        "task_count": item.get("task_count"),
                        "person_count": item.get("person_count"),
                        "role_counts": parse_json(item.get("role_counts_json"), {}),
                        "program_count": item.get("program_count"),
                        "top_programs": item.get("top_programs"),
                        "network_required_count": item.get("network_required_count"),
                        "manual_review_required_count": item.get("manual_review_required_count"),
                        "existing_collector": item.get("existing_collector"),
                        "command_hint": item.get("command_hint"),
                        "input_artifacts": parse_json(item.get("input_artifacts_json"), []),
                        "output_artifacts": parse_json(item.get("output_artifacts_json"), []),
                        "expected_claim_types": parse_json(item.get("expected_claim_types_json"), []),
                        "acceptance_rule": item.get("acceptance_rule"),
                        "recency_policy": item.get("recency_policy"),
                        "provenance_policy": item.get("provenance_policy"),
                        "top_people": parse_json(item.get("top_people_json"), []),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    grouped: dict[tuple[str, str, str, str, str, str], dict] = defaultdict(lambda: {"count": 0, "fresh": 0, "sample": None})
    roster_workbench_exists = (ARTIFACTS / "official_roster_refresh_workbench.csv").exists()
    evidence_triage_exists = (ARTIFACTS / "person_evidence_review_triage.csv").exists()
    profile_workbench_exists = (ARTIFACTS / "official_profile_discovery_workbench.csv").exists()
    for item in read_csv(ARTIFACTS / "person_enrichment_queue.csv"):
        if roster_workbench_exists and item.get("task_type") == "current_roster_state_reconciliation":
            continue
        if evidence_triage_exists and item.get("task_type") == "evidence_reconciliation_review":
            continue
        if profile_workbench_exists and item.get("task_type") == "official_profile_search":
            continue
        key = (
            item.get("task_type") or "",
            item.get("source_family") or "",
            item.get("role") or "",
            item.get("priority_band") or "",
            item.get("recommended_next_action") or "",
            item.get("operator_action") or "",
        )
        grouped[key]["count"] += 1
        grouped[key]["fresh"] += as_int(item.get("fresh_observation_required"))
        grouped[key]["sample"] = grouped[key]["sample"] or item
    rows = []
    for (task_type, source_family, role, band, recommended, operator_action), data in grouped.items():
        sample = data["sample"] or {}
        count = data["count"]
        base = {"critical": 900, "high": 720, "medium": 500, "low": 250}.get(band, 300)
        priority = base + min(count, 250) + min(data["fresh"], 150)
        rows.append(
            row(
                action_surface="person_enrichment_execution",
                action_scope=f"{source_family}:{task_type}",
                entity_type="enrichment_task_group",
                entity_key=stable_key(task_type, source_family, role, band, recommended, operator_action),
                display_label=f"{role or 'all roles'} {task_type}",
                role=role,
                program_name="",
                priority=priority,
                impact_count=count,
                readiness_status=band,
                blocker_status=sample.get("blocking_risk") or "",
                required_next_evidence=sample.get("evidence_requirement") or "",
                recommended_next_action=operator_action or recommended,
                source_artifact="artifacts/data/person_enrichment_queue.csv",
                target_artifact="artifacts/data/person_enrichment_execution_readiness.csv",
                downstream_tables=[
                    "person_enrichment_work_queue",
                    "person_enrichment_execution_readiness",
                    "evidence_claims",
                    "evidence_reconciliation_decisions",
                ],
                evidence={
                    "task_type": task_type,
                    "source_family": source_family,
                    "priority_band": band,
                    "fresh_observation_required_count": data["fresh"],
                    "sample_person_key": sample.get("person_key"),
                    "sample_display_name": sample.get("display_name"),
                    "sample_query": sample.get("query"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def attending_trend_actions(generated_at: str) -> list[dict]:
    rows = []
    source = "artifacts/data/attending_trend_reconciliation.csv"
    for item in read_csv(ARTIFACTS / "attending_trend_reconciliation.csv"):
        status = item.get("trend_status") or ""
        if status == "review_ready_official_biosketch_bridge":
            priority = 860
        elif status == "historical_link_candidate_review":
            priority = 760
        elif status == "current_endpoint_needs_training_claim":
            priority = 620
        else:
            priority = 320
        rows.append(
            row(
                action_surface="recent_attending_trend",
                action_scope=status,
                entity_type="attending_event_group",
                entity_key=item.get("event_group_key") or item.get("trend_key") or "",
                display_label=item.get("display_name") or "",
                role="current_penn_attending_candidate",
                program_name="",
                priority=priority,
                impact_count=1,
                readiness_status=item.get("ten_year_trend_window") or "unknown",
                blocker_status=status,
                required_next_evidence=item.get("required_next_evidence") or "",
                recommended_next_action={
                    "review_ready_official_biosketch_bridge": "record_attending_trend_reviewer_decision",
                    "historical_link_candidate_review": "review_historical_link_for_same_person_program_and_dates",
                    "current_endpoint_needs_training_claim": "collect_dated_training_claim_from_official_biosketch_cv_or_historical_roster",
                }.get(status, "retain_as_context_until_stronger_training_bridge_appears"),
                source_artifact=source,
                target_artifact="artifacts/data/attending_trend_review_claims.csv",
                downstream_tables=[
                    "attending_trend_reconciliation",
                    "attending_trend_review_claims",
                    "attending_trend_reviewer_decision_queue",
                    "accepted_attending_trend_facts",
                ],
                evidence={
                    "trend_key": item.get("trend_key"),
                    "has_current_attending_endpoint": item.get("has_current_attending_endpoint"),
                    "has_penn_training_claim": item.get("has_penn_training_claim"),
                    "has_recent_dated_biosketch_bridge": item.get("has_recent_dated_biosketch_bridge"),
                    "best_training_type": item.get("best_training_type"),
                    "best_training_end_year": item.get("best_training_end_year"),
                    "best_source_url": item.get("best_source_url"),
                },
                generated_at=generated_at,
            )
        )
    return rows


def attending_trend_discovery_actions(generated_at: str) -> list[dict]:
    rows = []
    batch_path = ARTIFACTS / "attending_trend_discovery_batches.csv"
    if batch_path.exists():
        packet_path = ARTIFACTS / "attending_trend_discovery_packets.csv"
        source = (
            "artifacts/data/attending_trend_discovery_packets.csv"
            if packet_path.exists()
            else "artifacts/data/attending_trend_discovery_batches.csv"
        )
        packets_by_batch: dict[str, list[dict]] = defaultdict(list)
        if packet_path.exists():
            for packet_row in read_csv(packet_path):
                packets_by_batch[packet_row.get("attending_trend_discovery_batch_key") or ""].append(packet_row)
        for item in read_csv(batch_path):
            packet_rows = packets_by_batch.get(item.get("attending_trend_discovery_batch_key") or "", [])
            priority = as_int(item.get("max_discovery_priority"))
            status = item.get("batch_status") or item.get("discovery_lane") or "attending_trend_discovery"
            rows.append(
                row(
                    action_surface="recent_attending_trend_discovery",
                    action_scope=f"{item.get('discovery_lane') or ''}:{status}",
                    entity_type="attending_trend_discovery_batch",
                    entity_key=item.get("attending_trend_discovery_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("discovery_lane"),
                            item.get("ten_year_trend_window"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role="current_penn_attending_candidate" if as_int(item.get("current_endpoint_count")) else "",
                    program_name="",
                    priority=priority + min(as_int(item.get("workbench_count")) * 2, 40),
                    impact_count=max(as_int(item.get("workbench_count")), as_int(item.get("person_count")), 1),
                    readiness_status=item.get("ten_year_trend_window") or "unknown",
                    blocker_status=status,
                    required_next_evidence=item.get("required_next_evidence") or "",
                    recommended_next_action=item.get("recommended_operator_action") or "",
                    source_artifact=source,
                    target_artifact=item.get("target_artifact") or "artifacts/data/attending_historical_link_candidates.csv",
                    downstream_tables=[
                        "attending_trend_discovery_batches",
                        "attending_trend_discovery_packets",
                        "attending_trend_discovery_workbench",
                        "attending_trend_dossiers",
                        "attending_trend_reviewer_decision_dossiers",
                        "attending_historical_link_search_queries",
                        "attending_historical_link_search_observations",
                        "attending_historical_link_candidates",
                        "attending_trend_reviewer_decision_queue",
                        "accepted_attending_trend_facts",
                    ],
                    evidence={
                        "attending_trend_discovery_batch_key": item.get("attending_trend_discovery_batch_key"),
                        "execution_order": item.get("execution_order"),
                        "discovery_lane": item.get("discovery_lane"),
                        "trend_status": item.get("trend_status"),
                        "ten_year_trend_window": item.get("ten_year_trend_window"),
                        "batch_status": item.get("batch_status"),
                        "workbench_count": item.get("workbench_count"),
                        "current_endpoint_count": item.get("current_endpoint_count"),
                        "penn_training_claim_count": item.get("penn_training_claim_count"),
                        "review_claim_count": item.get("review_claim_count"),
                        "accepted_trend_fact_count": item.get("accepted_trend_fact_count"),
                        "historical_query_count": item.get("historical_query_count"),
                        "historical_candidate_count": item.get("historical_candidate_count"),
                        "trend_discovery_packet_rows": len(packet_rows),
                        "top_trend_discovery_packets": [
                            {
                                "display_name": packet_row.get("display_name"),
                                "packet_status": packet_row.get("packet_status"),
                                "packet_priority": packet_row.get("packet_priority"),
                                "target_artifact": packet_row.get("target_artifact"),
                                "recommended_operator_action": packet_row.get("recommended_operator_action"),
                            }
                            for packet_row in packet_rows[:10]
                        ],
                        "query_status_counts": parse_json(item.get("query_status_counts_json"), {}),
                        "candidate_status_counts": parse_json(item.get("candidate_status_counts_json"), {}),
                        "top_workbench_rows": parse_json(item.get("top_workbench_rows_json"), []),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    source_path = ARTIFACTS / "attending_trend_discovery_workbench.csv"
    if not source_path.exists():
        return rows
    discovery_source = "artifacts/data/attending_trend_discovery_workbench.csv"
    dossier_source = "artifacts/data/attending_trend_reviewer_decision_dossiers.csv"
    dossier_path = ARTIFACTS / "attending_trend_reviewer_decision_dossiers.csv"
    dossiers_by_trend: dict[str, list[dict]] = defaultdict(list)
    if dossier_path.exists():
        for dossier_row in read_csv(dossier_path):
            dossiers_by_trend[dossier_row.get("trend_key") or ""].append(dossier_row)
    for item in read_csv(source_path):
        priority = as_int(item.get("discovery_priority"))
        dossier_rows = dossiers_by_trend.get(item.get("trend_key") or "", [])
        pending_dossier_rows = [
            dossier_row for dossier_row in dossier_rows if dossier_row.get("decision_status") == "pending_reviewer_decision"
        ]
        action_source = dossier_source if dossier_rows else discovery_source
        target_artifact = (
            "artifacts/data/attending_trend_reviewer_decisions.csv"
            if dossier_rows
            else "artifacts/data/attending_historical_link_candidates.csv"
        )
        rows.append(
            row(
                action_surface="recent_attending_trend_discovery",
                action_scope=item.get("discovery_lane") or "attending_trend_discovery",
                entity_type="attending_event_group",
                entity_key=item.get("trend_workbench_key") or item.get("event_group_key") or item.get("trend_key") or "",
                display_label=item.get("display_name") or "",
                role="current_penn_attending_candidate" if as_int(item.get("has_current_attending_endpoint")) else "",
                program_name="",
                priority=priority,
                impact_count=1,
                readiness_status=item.get("ten_year_trend_window") or "unknown",
                blocker_status=item.get("discovery_lane") or item.get("trend_status") or "",
                required_next_evidence=item.get("evidence_required") or "",
                recommended_next_action=item.get("recommended_next_action") or "",
                source_artifact=action_source,
                target_artifact=target_artifact,
                downstream_tables=[
                    "attending_trend_discovery_workbench",
                    "attending_trend_dossiers",
                    "attending_trend_reviewer_decision_dossiers",
                    "attending_historical_link_search_queries",
                    "attending_historical_link_search_observations",
                    "attending_historical_link_candidates",
                    "attending_trend_reviewer_decision_queue",
                    "accepted_attending_trend_facts",
                ],
                evidence={
                    "trend_key": item.get("trend_key"),
                    "event_group_key": item.get("event_group_key"),
                    "trend_status": item.get("trend_status"),
                    "dossier_status": item.get("dossier_status"),
                    "has_current_attending_endpoint": item.get("has_current_attending_endpoint"),
                    "has_penn_training_claim": item.get("has_penn_training_claim"),
                    "accepted_trend_fact_count": item.get("accepted_trend_fact_count"),
                    "review_claim_count": item.get("review_claim_count"),
                    "historical_query_count": item.get("historical_query_count"),
                    "historical_candidate_count": item.get("historical_candidate_count"),
                    "best_candidate_status": item.get("best_candidate_status"),
                    "best_candidate_url": item.get("best_candidate_url"),
                    "reviewer_decision_key": (dossier_rows[0].get("reviewer_decision_key") if dossier_rows else ""),
                    "reviewer_decision_status": (dossier_rows[0].get("decision_status") if dossier_rows else ""),
                    "pending_reviewer_decision_count": len(pending_dossier_rows),
                },
                generated_at=generated_at,
            )
        )
    return rows


def research_identity_corroboration_actions(generated_at: str) -> list[dict]:
    batch_path = ARTIFACTS / "research_identity_review_batches.csv"
    if batch_path.exists():
        packet_path = ARTIFACTS / "research_identity_review_batch_packets.csv"
        dossier_path = ARTIFACTS / "research_identity_reviewer_decision_dossiers.csv"
        conflict_packet_path = ARTIFACTS / "research_identity_conflict_resolution_packets.csv"
        conflict_identifier_path = ARTIFACTS / "research_identity_conflict_identifier_evidence.csv"
        source = (
            "artifacts/data/research_identity_review_batch_packets.csv"
            if packet_path.exists()
            else "artifacts/data/research_identity_reviewer_decision_dossiers.csv"
            if dossier_path.exists()
            else "artifacts/data/research_identity_review_batches.csv"
        )
        packets_by_batch: dict[str, dict] = {}
        if packet_path.exists():
            for packet_row in read_csv(packet_path):
                packets_by_batch[packet_row.get("review_batch_key") or ""] = packet_row
        audit_by_batch: dict[str, list[dict]] = defaultdict(list)
        audit_path = ARTIFACTS / "research_identity_reviewer_decision_audit.csv"
        if audit_path.exists():
            for audit_row in read_csv(audit_path):
                audit_by_batch[audit_row.get("review_batch_key") or ""].append(audit_row)
        dossiers_by_batch: dict[str, list[dict]] = defaultdict(list)
        if dossier_path.exists():
            for dossier_row in read_csv(dossier_path):
                dossiers_by_batch[dossier_row.get("review_batch_key") or ""].append(dossier_row)
        conflict_packets_by_batch: dict[str, list[dict]] = defaultdict(list)
        if conflict_packet_path.exists():
            for conflict_packet in read_csv(conflict_packet_path):
                conflict_packets_by_batch[conflict_packet.get("review_batch_key") or ""].append(conflict_packet)
        conflict_identifiers_by_batch: dict[str, list[dict]] = defaultdict(list)
        if conflict_identifier_path.exists():
            for identifier_row in read_csv(conflict_identifier_path):
                conflict_identifiers_by_batch[identifier_row.get("review_batch_key") or ""].append(identifier_row)
        rows = []
        priority_by_lane = {
            "conflict_reconciliation": 980,
            "multi_source_identity_review": 930,
            "secondary_anchor_review": 875,
            "single_source_publication_review": 825,
            "secondary_anchor_collection": 635,
            "research_relevance_decision": 470,
        }
        for item in read_csv(batch_path):
            lane = item.get("review_lane") or "research_identity_review_batch"
            packet = packets_by_batch.get(item.get("review_batch_key") or "", {})
            audit_rows = audit_by_batch.get(item.get("review_batch_key") or "", [])
            dossier_rows = dossiers_by_batch.get(item.get("review_batch_key") or "", [])
            conflict_packet_rows = conflict_packets_by_batch.get(item.get("review_batch_key") or "", [])
            conflict_identifier_rows = conflict_identifiers_by_batch.get(item.get("review_batch_key") or "", [])
            pending_audit_rows = [
                audit_row
                for audit_row in audit_rows
                if audit_row.get("decision_status") in {"pending_reviewer_decision", "stale_decision_evidence_mismatch"}
            ]
            pending_dossier_rows = [
                dossier_row for dossier_row in dossier_rows if str(dossier_row.get("dossier_status") or "").startswith("pending")
            ]
            impact = max(len(pending_audit_rows), 1) if audit_rows else max(as_int(item.get("person_count")), 1)
            priority = (
                priority_by_lane.get(lane, 640)
                + min(as_int(item.get("max_review_priority")), 120)
                + min(as_int(item.get("review_ready_record_count")), 140)
            )
            if as_int(item.get("conflict_count")) > 0:
                priority += 100
            if audit_rows and not pending_audit_rows:
                priority -= 250
            rows.append(
                row(
                    action_surface="research_identity_corroboration",
                    action_scope=f"{item.get('research_identity_status') or ''}:{lane}",
                    entity_type="research_identity_review_batch",
                    entity_key=item.get("review_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("role") or "all roles",
                            lane,
                            item.get("research_identity_status"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("role") or "",
                    program_name="",
                    priority=priority,
                    impact_count=impact,
                    readiness_status=(
                        "pending_research_identity_reviewer_decisions"
                        if pending_audit_rows
                        else packet.get("packet_status")
                        if packet
                        else item.get("batch_status") or item.get("research_identity_status") or ""
                    ),
                    blocker_status=(
                        "conflict_blocks_acceptance"
                        if as_int(item.get("conflict_count")) > 0
                        else item.get("recommended_review_route") or ""
                    ),
                    required_next_evidence=item.get("reviewer_prompt") or item.get("review_instructions") or "",
                    recommended_next_action="record_research_identity_reviewer_decisions_with_current_member_fingerprints",
                    source_artifact=(
                        "artifacts/data/research_identity_conflict_resolution_packets.csv"
                        if conflict_packet_rows
                        else source
                    ),
                    target_artifact=item.get("target_decision_artifact")
                    or "artifacts/data/research_identity_reviewer_decisions.csv",
                    downstream_tables=[
                        "research_identity_review_batches",
                        "research_identity_review_batch_members",
                        "research_identity_review_batch_packets",
                        "research_identity_conflict_resolution_packets",
                        "research_identity_conflict_identifier_evidence",
                        "research_identity_reviewer_decision_queue",
                        "research_identity_reviewer_decisions",
                        "research_identity_reviewer_decision_audit",
                        "research_identity_reviewer_decision_dossiers",
                        "research_identity_corroboration",
                        "evidence_reconciliation_decisions",
                        "person_evidence_reviewer_decisions",
                        "enrichment_acceptance_audit",
                        "accepted_enrichment_claims",
                        "evidence_temporal_contracts",
                    ],
                    evidence={
                        "review_batch_key": item.get("review_batch_key"),
                        "review_lane": lane,
                        "research_identity_status": item.get("research_identity_status"),
                        "recommended_review_route": item.get("recommended_review_route"),
                        "person_count": item.get("person_count"),
                        "research_candidate_count": item.get("research_candidate_count"),
                        "review_ready_record_count": item.get("review_ready_record_count"),
                        "scholarly_source_count": item.get("scholarly_source_count"),
                        "secondary_anchor_count": item.get("secondary_anchor_count"),
                        "conflict_count": item.get("conflict_count"),
                        "reviewer_decision_audit_rows": len(audit_rows),
                        "pending_reviewer_decision_rows": len(pending_audit_rows),
                        "reviewer_decision_dossier_rows": len(dossier_rows),
                        "pending_reviewer_decision_dossier_rows": len(pending_dossier_rows),
                        "conflict_resolution_packet_rows": len(conflict_packet_rows),
                        "conflict_identifier_evidence_rows": len(conflict_identifier_rows),
                        "top_conflict_identifier_postures": dict(
                            Counter(
                                identifier_row.get("identifier_review_posture") or ""
                                for identifier_row in conflict_identifier_rows
                            ).most_common(8)
                        ),
                        "top_conflict_resolution_packets": [
                            {
                                "display_name": packet_row.get("display_name"),
                                "conflict_resolution_lane": packet_row.get("conflict_resolution_lane"),
                                "competing_identifier_count": packet_row.get("competing_identifier_count"),
                                "publication_support_count": packet_row.get("publication_support_count"),
                                "recommended_reviewer_action": packet_row.get("recommended_reviewer_action"),
                            }
                            for packet_row in conflict_packet_rows[:10]
                        ],
                        "batch_packet_key": packet.get("batch_packet_key") or "",
                        "batch_packet_status": packet.get("packet_status") or "",
                        "batch_packet_support_status": packet.get("support_status") or "",
                        "top_dossier_statuses": dict(
                            Counter(dossier_row.get("dossier_status") or "" for dossier_row in dossier_rows).most_common(8)
                        ),
                        "top_source_keys": item.get("top_source_keys"),
                        "top_claim_types": item.get("top_claim_types"),
                        "top_people_json": item.get("top_people_json"),
                        "acceptance_rule": item.get("acceptance_rule"),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    source_path = ARTIFACTS / "research_identity_corroboration.csv"
    if not source_path.exists():
        return []
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for item in read_csv(source_path):
        status = item.get("research_identity_status") or ""
        route = item.get("recommended_review_route") or ""
        if status == "no_public_research_identity_signal":
            continue
        grouped[(status, route, item.get("role") or "")].append(item)

    priority_by_status = {
        "conflict_review_required": 970,
        "strong_multi_source_research_identity_review": 940,
        "multi_source_candidate_review": 880,
        "research_plus_secondary_identity_anchor_review": 865,
        "single_source_research_review_ready": 805,
        "research_candidate_only": 610,
        "secondary_anchor_without_research_signal": 420,
    }
    rows = []
    for (status, route, role), group in grouped.items():
        max_priority = max(as_int(item.get("review_priority")) for item in group)
        review_ready = sum(as_int(item.get("research_review_ready_count")) for item in group)
        multi_source = sum(1 for item in group if as_int(item.get("scholarly_source_count")) >= 2)
        priority = priority_by_status.get(status, 500) + min(max_priority, 100) + min(review_ready, 150)
        if status == "research_candidate_only":
            priority += min(len(group), 120)
        sample = sorted(
            group,
            key=lambda item: (
                -as_int(item.get("review_priority")),
                -as_int(item.get("research_review_ready_count")),
                item.get("display_name") or "",
            ),
        )[0]
        rows.append(
            row(
                action_surface="research_identity_corroboration",
                action_scope=f"{status}:{route}",
                entity_type="person_research_identity_group",
                entity_key=stable_key(status, route, role),
                display_label=" | ".join(part for part in [role or "all roles", status, route] if part),
                role=role,
                program_name="",
                priority=priority,
                impact_count=len(group),
                readiness_status=status,
                blocker_status="conflict_blocks_acceptance" if status == "conflict_review_required" else route,
                required_next_evidence=sample.get("required_next_evidence") or "",
                recommended_next_action=route,
                source_artifact="artifacts/data/research_identity_corroboration.csv",
                target_artifact="artifacts/data/person_evidence_reviewer_decisions.csv",
                downstream_tables=[
                    "research_identity_corroboration",
                    "person_evidence_review_triage",
                    "person_evidence_reviewer_decision_audit",
                    "enrichment_acceptance_audit",
                    "accepted_enrichment_claims",
                    "evidence_temporal_contracts",
                ],
                evidence={
                    "research_identity_status": status,
                    "recommended_review_route": route,
                    "person_count": len(group),
                    "review_ready_record_count": review_ready,
                    "multi_source_people": multi_source,
                    "top_people": [
                        {
                            "person_key": item.get("person_key"),
                            "display_name": item.get("display_name"),
                            "review_priority": item.get("review_priority"),
                            "scholarly_source_count": item.get("scholarly_source_count"),
                            "research_review_ready_count": item.get("research_review_ready_count"),
                            "non_name_anchor_count": item.get("non_name_anchor_count"),
                            "top_claim_types": item.get("top_claim_types"),
                        }
                        for item in sorted(
                            group,
                            key=lambda item: (
                                -as_int(item.get("review_priority")),
                                -as_int(item.get("research_review_ready_count")),
                                item.get("display_name") or "",
                            ),
                        )[:10]
                    ],
                },
                generated_at=generated_at,
            )
        )
    return rows


def action_member_execution_actions(generated_at: str) -> list[dict]:
    packet_path = ARTIFACTS / "person_enrichment_action_member_execution_packets.csv"
    if packet_path.exists():
        rows = []
        for item in read_csv(packet_path):
            top_dossiers = parse_json(item.get("top_dossiers_json"), [])
            command_hints = parse_json(item.get("command_hints_json"), [])
            templates = parse_json(item.get("manual_execution_templates_json"), [])
            rows.append(
                row(
                    action_surface="person_action_member_execution",
                    action_scope=f"{item.get('primary_action_lane') or ''}:{item.get('execution_status') or ''}",
                    entity_type="person_enrichment_action_member_execution_packet",
                    entity_key=item.get("execution_packet_key") or item.get("action_batch_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("primary_action_lane"),
                            item.get("execution_status"),
                            item.get("priority_band"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("role") or "",
                    program_name="",
                    priority=as_int(item.get("packet_priority")),
                    impact_count=max(as_int(item.get("member_count")), 1),
                    readiness_status=item.get("queue_status") or item.get("batch_status") or "",
                    blocker_status=item.get("blocker_status") or "",
                    required_next_evidence=item.get("required_output_routing") or "",
                    recommended_next_action=item.get("recommended_operator_action")
                    or "record_member_execution_decisions_with_current_fingerprints",
                    source_artifact="artifacts/data/person_enrichment_action_member_execution_packets.csv",
                    target_artifact=item.get("target_artifact")
                    or "artifacts/data/person_enrichment_action_member_execution_decisions.csv",
                    downstream_tables=[
                        "person_enrichment_action_member_execution_packets",
                        "person_enrichment_action_member_execution_dossiers",
                        "person_enrichment_action_execution_plan",
                        "person_enrichment_action_batches",
                        "person_enrichment_action_batch_members",
                        "person_enrichment_action_member_execution_queue",
                        "person_enrichment_action_member_execution_decisions",
                        "person_enrichment_action_member_execution_audit",
                        "person_evidence_reviewer_decision_audit",
                        "official_profile_reviewer_decision_audit",
                        "evidence_reconciliation_decisions",
                        "accepted_enrichment_claims",
                    ],
                    evidence={
                        "execution_packet_key": item.get("execution_packet_key"),
                        "action_batch_key": item.get("action_batch_key"),
                        "primary_action_lane": item.get("primary_action_lane"),
                        "execution_status": item.get("execution_status"),
                        "queue_status": item.get("queue_status"),
                        "member_count": item.get("member_count"),
                        "pending_member_count": item.get("pending_member_count"),
                        "blocked_member_count": item.get("blocked_member_count"),
                        "invalid_or_stale_member_count": item.get("invalid_or_stale_member_count"),
                        "manual_execution_template_count": len(templates) if isinstance(templates, list) else 0,
                        "command_hint_count": len(command_hints) if isinstance(command_hints, list) else 0,
                        "top_dossier_count": len(top_dossiers) if isinstance(top_dossiers, list) else 0,
                        "top_dossiers": top_dossiers[:10] if isinstance(top_dossiers, list) else [],
                        "expected_downstream_artifacts": parse_json(item.get("expected_downstream_artifacts_json"), []),
                        "acceptance_boundary": item.get("acceptance_boundary"),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    plan_path = ARTIFACTS / "person_enrichment_action_execution_plan.csv"
    if plan_path.exists():
        rows = []
        for item in read_csv(plan_path):
            pending = as_int(item.get("pending_member_count"))
            blocked = as_int(item.get("blocked_member_count"))
            invalid = as_int(item.get("invalid_or_stale_member_count"))
            max_priority = as_int(item.get("max_packet_priority"))
            priority = 760 + min(max_priority, 400)
            if pending:
                priority += 90
            if blocked and not pending:
                priority -= 120
            if invalid:
                priority += 160
            command_hints = parse_json(item.get("command_hints_json"), [])
            decision_templates = parse_json(item.get("decision_template_json"), [])
            rows.append(
                row(
                    action_surface="person_action_member_execution",
                    action_scope=f"{item.get('primary_action_lane') or ''}:{item.get('batch_status') or ''}",
                    entity_type="person_enrichment_action_batch",
                    entity_key=item.get("action_batch_key") or item.get("execution_plan_key") or "",
                    display_label=" | ".join(
                        part
                        for part in [
                            item.get("primary_action_lane"),
                            item.get("batch_status"),
                            item.get("priority_band"),
                            f"batch {item.get('execution_order')}",
                        ]
                        if part
                    ),
                    role=item.get("role") or "",
                    program_name="",
                    priority=priority,
                    impact_count=max(pending + blocked + invalid, as_int(item.get("person_count")), 1),
                    readiness_status=item.get("batch_status") or "",
                    blocker_status=item.get("blocker_status") or "",
                    required_next_evidence=item.get("required_output_routing") or "",
                    recommended_next_action=item.get("recommended_operator_action")
                    or "execute_batch_and_record_member_decisions",
                    source_artifact="artifacts/data/person_enrichment_action_execution_plan.csv",
                    target_artifact="artifacts/data/person_enrichment_action_member_execution_decisions.csv",
                    downstream_tables=[
                        "person_enrichment_action_execution_plan",
                        "person_enrichment_action_batches",
                        "person_enrichment_action_batch_members",
                        "person_enrichment_action_member_execution_queue",
                        "person_enrichment_action_member_execution_decisions",
                        "person_enrichment_action_member_execution_audit",
                        "person_enrichment_action_member_execution_dossiers",
                        "person_evidence_reviewer_decision_audit",
                        "official_profile_reviewer_decision_audit",
                        "evidence_reconciliation_decisions",
                        "accepted_enrichment_claims",
                    ],
                    evidence={
                        "execution_plan_key": item.get("execution_plan_key"),
                        "action_batch_key": item.get("action_batch_key"),
                        "primary_action_lane": item.get("primary_action_lane"),
                        "batch_status": item.get("batch_status"),
                        "ready_to_execute": item.get("ready_to_execute"),
                        "person_count": item.get("person_count"),
                        "packet_count": item.get("packet_count"),
                        "pending_member_count": item.get("pending_member_count"),
                        "blocked_member_count": item.get("blocked_member_count"),
                        "invalid_or_stale_member_count": item.get("invalid_or_stale_member_count"),
                        "top_member_names": item.get("top_member_names"),
                        "first_command_hint": item.get("first_command_hint"),
                        "command_hint_count": len(command_hints) if isinstance(command_hints, list) else 0,
                        "decision_template_count": len(decision_templates) if isinstance(decision_templates, list) else 0,
                        "expected_downstream_artifacts": parse_json(item.get("expected_downstream_artifacts_json"), []),
                        "acceptance_boundary": item.get("acceptance_boundary"),
                    },
                    generated_at=generated_at,
                )
            )
        return rows

    audit_path = ARTIFACTS / "person_enrichment_action_member_execution_audit.csv"
    if not audit_path.exists():
        return []
    dossier_path = ARTIFACTS / "person_enrichment_action_member_execution_dossiers.csv"
    source = (
        "artifacts/data/person_enrichment_action_member_execution_dossiers.csv"
        if dossier_path.exists()
        else "artifacts/data/person_enrichment_action_member_execution_audit.csv"
    )
    dossiers_by_group: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    if dossier_path.exists():
        for dossier_row in read_csv(dossier_path):
            key = (
                dossier_row.get("action_batch_key") or "",
                dossier_row.get("primary_action_lane") or "",
                dossier_row.get("execution_status") or "",
            )
            dossiers_by_group[key].append(dossier_row)
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for item in read_csv(audit_path):
        status = item.get("execution_status") or ""
        if status in {"executed_outputs_routed", "executed_no_public_output", "skipped_superseded"}:
            continue
        key = (item.get("action_batch_key") or "", item.get("primary_action_lane") or "", status)
        grouped[key].append(item)

    rows = []
    for (batch_key, lane, status), group in grouped.items():
        dossier_rows = dossiers_by_group.get((batch_key, lane, status), [])
        max_priority = max(as_int(item.get("packet_priority")) for item in group)
        priority = 760 + min(max_priority, 400)
        if status == "pending_execution_decision":
            priority += 90
        if status == "blocked_upstream_not_ready":
            priority -= 120
        if status in {"invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"}:
            priority += 160
        sample = group[0]
        rows.append(
            row(
                action_surface="person_action_member_execution",
                action_scope=f"{lane}:{status}",
                entity_type="person_enrichment_action_batch",
                entity_key=batch_key,
                display_label=" | ".join(
                    part
                    for part in [
                        lane,
                        status,
                        sample.get("priority_band"),
                        f"batch {sample.get('execution_order')}",
                    ]
                    if part
                ),
                role=sample.get("role") or "",
                program_name="",
                priority=priority,
                impact_count=len(group),
                readiness_status=sample.get("queue_status") or "",
                blocker_status=status,
                required_next_evidence="A matching member_fingerprint execution decision plus routed downstream source-specific artifacts when outputs are produced.",
                recommended_next_action=sample.get("recommended_next_action") or "record_execution_decision_with_matching_member_fingerprint",
                source_artifact=source,
                target_artifact="artifacts/data/person_enrichment_action_member_execution_decisions.csv",
                downstream_tables=[
                    "person_enrichment_action_member_execution_decisions",
                    "person_enrichment_action_member_execution_audit",
                    "person_enrichment_action_member_execution_dossiers",
                    "person_evidence_reviewer_decision_audit",
                    "official_profile_reviewer_decision_audit",
                    "evidence_reconciliation_decisions",
                    "accepted_enrichment_claims",
                ],
                evidence={
                    "action_batch_key": batch_key,
                    "primary_action_lane": lane,
                    "execution_status": status,
                    "member_count": len(group),
                    "execution_dossier_rows": len(dossier_rows),
                    "top_dossier_statuses": dict(
                        Counter(dossier_row.get("dossier_status") or "" for dossier_row in dossier_rows).most_common(8)
                    ),
                    "top_members": [
                        {
                            "action_batch_member_key": item.get("action_batch_member_key"),
                            "display_name": item.get("display_name"),
                            "packet_status": item.get("packet_status"),
                            "packet_priority": item.get("packet_priority"),
                            "execution_blocker": item.get("execution_blocker"),
                        }
                        for item in group[:10]
                    ],
                },
                generated_at=generated_at,
            )
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(rows: list[dict]) -> None:
    conn = sqlite3.connect(DB)
    with conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("DELETE FROM corpus_action_worklist")
        placeholders = ", ".join(f":{field}" for field in FIELDS)
        fields = ", ".join(FIELDS)
        conn.executemany(f"INSERT OR REPLACE INTO corpus_action_worklist ({fields}) VALUES ({placeholders})", rows)
    conn.close()


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_surface = Counter(row["action_surface"] for row in rows)
    by_band = Counter(row["priority_band"] for row in rows)
    by_scope = Counter(f"{row['action_surface']}:{row['action_scope']}" for row in rows)
    top = rows[:25]
    summary = {
        "generated_at": generated_at,
        "worklist_rows": len(rows),
        "total_impact_count": sum(as_int(row["impact_count"]) for row in rows),
        "impact_count_policy": "Summed action-item impact, not deduplicated unique people; the same person or program can correctly appear in multiple evidence, review, contact, state, or source-refresh surfaces.",
        "critical_rows": by_band.get("critical", 0),
        "high_rows": by_band.get("high", 0),
        "by_action_surface": dict(sorted(by_surface.items())),
        "by_priority_band": dict(sorted(by_band.items())),
        "top_action_scope_counts": dict(by_scope.most_common(25)),
        "top_work_items": [
            {
                "action_surface": row["action_surface"],
                "action_scope": row["action_scope"],
                "display_label": row["display_label"],
                "role": row["role"],
                "program_name": row["program_name"],
                "priority": row["priority"],
                "impact_count": row["impact_count"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in top
        ],
        "csv": "artifacts/data/corpus_action_worklist.csv",
        "json": "artifacts/data/corpus_action_worklist.json",
        "policy": "This worklist is non-mutating. It ranks unresolved evidence, coverage, state-machine, search, contact, and trend surfaces so operators can collect or review the next evidence without silently accepting facts.",
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    generated_at = now_utc()
    rows = []
    rows.extend(official_program_actions(generated_at))
    rows.extend(person_evidence_actions(generated_at))
    rows.extend(contact_actions(generated_at))
    rows.extend(search_utility_actions(generated_at))
    rows.extend(source_quality_policy_actions(generated_at))
    rows.extend(temporal_contract_actions(generated_at))
    roster_batch_rows = official_roster_refresh_batch_actions(generated_at)
    rows.extend(roster_batch_rows if roster_batch_rows else official_roster_refresh_actions(generated_at))
    rows.extend(official_profile_discovery_actions(generated_at))
    rows.extend(lifecycle_duration_review_actions(generated_at))
    rows.extend(enrichment_queue_actions(generated_at))
    rows.extend(action_member_execution_actions(generated_at))
    rows.extend(research_identity_corroboration_actions(generated_at))
    attending_discovery_rows = attending_trend_discovery_actions(generated_at)
    rows.extend(attending_discovery_rows if attending_discovery_rows else attending_trend_actions(generated_at))
    rows.sort(key=lambda item: (-as_int(item["priority"]), -as_int(item["impact_count"]), item["action_surface"], item["display_label"]))
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows, generated_at)
    print(json.dumps({"corpus_action_worklist": len(rows), "total_impact_count": sum(as_int(row["impact_count"]) for row in rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
