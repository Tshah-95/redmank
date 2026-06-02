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
    contract_path = ARTIFACTS / "contact_verification_contracts.csv"
    source_path = contract_path if contract_path.exists() else ARTIFACTS / "contact_assurance_audit.csv"
    source = str(source_path.relative_to(ROOT))
    for item in read_csv(source_path):
        status = item.get("verification_lane") or item.get("assurance_status") or ""
        if status == "fresh_official_reobservation_required":
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
                entity_key=item.get("contact_contract_key") or item.get("contact_assurance_key") or item.get("contact_key") or "",
                display_label=item.get("display_name") or "",
                role=item.get("role") or "",
                program_name="",
                priority=base_priority + as_int(item.get("assurance_level")) * 10,
                impact_count=1,
                readiness_status=item.get("operational_use_status") or item.get("display_safety_status") or "",
                blocker_status=item.get("required_reviewer_action") or item.get("required_next_check") or "",
                required_next_evidence=item.get("evidence_required_to_verify") or "Verify current official source, person identity, contact domain, and intended contact scope before treating as a verified contact fact.",
                recommended_next_action=item.get("required_reviewer_action") or item.get("recommended_next_action") or "",
                source_artifact=source,
                target_artifact="artifacts/data/contact_verification_contracts.csv",
                downstream_tables=["contact_verification_contracts", "contact_assurance_audit", "person_contacts"],
                evidence={
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
                },
                generated_at=generated_at,
            )
        )
    return rows


def search_utility_actions(generated_at: str) -> list[dict]:
    rows = []
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


def temporal_contract_actions(generated_at: str) -> list[dict]:
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


def lifecycle_duration_review_actions(generated_at: str) -> list[dict]:
    rows = []
    source = "artifacts/data/program_lifecycle_duration_reviewer_decision_queue.csv"
    for item in read_csv(ARTIFACTS / "program_lifecycle_duration_reviewer_decision_queue.csv"):
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
                blocker_status=item.get("duration_evidence_status") or "",
                required_next_evidence=item.get("required_reviewer_action") or "",
                recommended_next_action=(
                    "record_accept_reject_or_needs_more_evidence_decision"
                    if status == "ready_for_reviewer_decision"
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
                },
                generated_at=generated_at,
            )
        )
    return rows


def enrichment_queue_actions(generated_at: str) -> list[dict]:
    grouped: dict[tuple[str, str, str, str, str, str], dict] = defaultdict(lambda: {"count": 0, "fresh": 0, "sample": None})
    for item in read_csv(ARTIFACTS / "person_enrichment_queue.csv"):
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
    rows.extend(temporal_contract_actions(generated_at))
    rows.extend(lifecycle_duration_review_actions(generated_at))
    rows.extend(enrichment_queue_actions(generated_at))
    rows.extend(attending_trend_actions(generated_at))
    rows.sort(key=lambda item: (-as_int(item["priority"]), -as_int(item["impact_count"]), item["action_surface"], item["display_label"]))
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows, generated_at)
    print(json.dumps({"corpus_action_worklist": len(rows), "total_impact_count": sum(as_int(row["impact_count"]) for row in rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
