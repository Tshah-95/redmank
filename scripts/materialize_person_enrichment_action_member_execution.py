#!/usr/bin/env python3
"""Materialize execution tracking for person enrichment action batch members."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

QUEUE_CSV = ARTIFACTS / "person_enrichment_action_member_execution_queue.csv"
QUEUE_JSON = ARTIFACTS / "person_enrichment_action_member_execution_queue.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "person_enrichment_action_member_execution_decisions.csv"
AUDIT_CSV = ARTIFACTS / "person_enrichment_action_member_execution_audit.csv"
AUDIT_JSON = ARTIFACTS / "person_enrichment_action_member_execution_audit.json"
SUMMARY_JSON = ARTIFACTS / "person_enrichment_action_member_execution_summary.json"

ALLOWED_EXECUTION_DECISIONS = [
    "executed_outputs_routed",
    "executed_no_public_output",
    "blocked_source_unavailable",
    "blocked_rate_limited",
    "failed_retry_needed",
    "skipped_superseded",
    "needs_manual_review",
]

QUEUE_FIELDS = [
    "execution_decision_key",
    "action_batch_member_key",
    "action_batch_key",
    "action_packet_key",
    "person_key",
    "display_name",
    "role",
    "programs",
    "primary_action_lane",
    "packet_status",
    "batch_status",
    "priority_band",
    "execution_order",
    "member_order",
    "packet_priority",
    "ready_to_execute",
    "queue_status",
    "member_fingerprint",
    "allowed_execution_decisions",
    "recommended_execution_action",
    "required_output_routing",
    "expected_downstream_artifacts_json",
    "command_hints_json",
    "top_source_urls",
    "evidence_json",
    "generated_at",
]

MANUAL_FIELDS = [
    "execution_decision_key",
    "action_batch_member_key",
    "action_packet_key",
    "member_fingerprint",
    "execution_decision",
    "executor_name",
    "executed_at",
    "command_run",
    "output_artifacts_json",
    "output_record_count",
    "routed_to_downstream_ledgers",
    "downstream_ledger_notes",
    "decision_notes",
]

AUDIT_FIELDS = [
    "execution_decision_key",
    "action_batch_member_key",
    "action_batch_key",
    "action_packet_key",
    "person_key",
    "display_name",
    "role",
    "programs",
    "primary_action_lane",
    "packet_status",
    "batch_status",
    "priority_band",
    "execution_order",
    "member_order",
    "packet_priority",
    "ready_to_execute",
    "queue_status",
    "execution_decision",
    "execution_status",
    "execution_blocker",
    "member_fingerprint",
    "decision_member_fingerprint",
    "executor_name",
    "executed_at",
    "command_run",
    "output_artifacts_json",
    "output_record_count",
    "routed_to_downstream_ledgers",
    "downstream_ledger_notes",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]

csv.field_size_limit(sys.maxsize)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def existing_by_key(path: Path, key: str) -> dict[str, dict]:
    return {row[key]: row for row in read_csv(path) if row.get(key)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["execution_decision_key"])
    if not prior:
        return timestamp
    for field in QUEUE_FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def execution_decision_key(member: dict) -> str:
    return "person_enrichment_action_member_execution_" + sha256_text(
        dumps([member.get("action_batch_member_key") or "", member.get("action_packet_key") or ""])
    )[:20]


def member_fingerprint(member: dict) -> str:
    stable = {
        key: member.get(key) or ""
        for key in [
            "action_batch_member_key",
            "action_batch_key",
            "action_packet_key",
            "person_key",
            "display_name",
            "role",
            "programs",
            "primary_action_lane",
            "packet_status",
            "batch_status",
            "priority_band",
            "ready_to_execute",
            "blocked_reason",
            "packet_priority",
            "recommended_next_action",
            "required_next_evidence",
            "primary_blocker",
            "command_hints_json",
            "downstream_artifacts_json",
        ]
    }
    return sha256_text(dumps(stable))


def queue_status(member: dict) -> str:
    if not as_int(member.get("ready_to_execute")):
        if member.get("primary_action_lane") == "profile_search_retry":
            return "blocked_retry_or_replace_search_endpoint"
        return "blocked_upstream_not_ready"
    lane = member.get("primary_action_lane") or ""
    if lane in {"person_evidence_review", "official_profile_review"}:
        return "ready_for_manual_review_execution_decision"
    if lane in {"official_profile_discovery", "enrichment_collector_execution"}:
        return "ready_for_collector_execution_decision"
    return "ready_for_execution_decision"


def recommended_execution_action(member: dict) -> str:
    lane = member.get("primary_action_lane") or ""
    if not as_int(member.get("ready_to_execute")):
        return "resolve_blocker_before_execution"
    if lane == "person_evidence_review":
        return "review_packet_and_record_source_specific_reviewer_decision"
    if lane == "official_profile_review":
        return "review_profile_candidate_and_record_profile_reviewer_decision"
    if lane == "official_profile_discovery":
        return "run_profile_discovery_then_rebuild_profile_workbench_and_reviewer_queue"
    if lane == "enrichment_collector_execution":
        return "run_collector_then_route_outputs_to_evidence_contact_or_profile_ledgers"
    if lane == "profile_search_retry":
        return "retry_or_replace_search_endpoint_then_rebuild_profile_discovery"
    return "execute_member_then_route_outputs_to_source_specific_ledgers"


def required_output_routing(member: dict) -> str:
    lane = member.get("primary_action_lane") or ""
    if lane == "person_evidence_review":
        return "Record decisions in person_evidence_reviewer_decisions.csv or the relevant accepted/rejected evidence ledger."
    if lane == "official_profile_review":
        return "Record decisions in official_profile_reviewer_decisions.csv before accepted profile facts materialize."
    if lane == "official_profile_discovery":
        return "Write discovered candidates to trainee_profile_discovery_* and official_profile_discovery_workbench artifacts."
    if lane == "enrichment_collector_execution":
        return "Write outputs to source-specific claim/contact/search artifacts, then rebuild reconciliation and acceptance audits."
    return "Route outputs to the downstream artifacts named by this member; never accept facts directly from execution notes."


def compact_member(member: dict) -> dict:
    return {
        key: member.get(key, "")
        for key in [
            "action_batch_member_key",
            "action_batch_key",
            "action_packet_key",
            "person_key",
            "display_name",
            "role",
            "programs",
            "primary_action_lane",
            "packet_status",
            "batch_status",
            "priority_band",
            "ready_to_execute",
            "blocked_reason",
            "recommended_next_action",
            "required_next_evidence",
            "primary_blocker",
            "downstream_artifacts_json",
        ]
    }


def build_queue(members: list[dict], generated_at: str) -> list[dict]:
    existing = existing_by_key(QUEUE_CSV, "execution_decision_key")
    rows = []
    for member in members:
        fingerprint = member_fingerprint(member)
        row = {
            "execution_decision_key": execution_decision_key(member),
            "action_batch_member_key": member.get("action_batch_member_key") or "",
            "action_batch_key": member.get("action_batch_key") or "",
            "action_packet_key": member.get("action_packet_key") or "",
            "person_key": member.get("person_key") or "",
            "display_name": member.get("display_name") or "",
            "role": member.get("role") or "",
            "programs": member.get("programs") or "",
            "primary_action_lane": member.get("primary_action_lane") or "",
            "packet_status": member.get("packet_status") or "",
            "batch_status": member.get("batch_status") or "",
            "priority_band": member.get("priority_band") or "",
            "execution_order": as_int(member.get("execution_order")),
            "member_order": as_int(member.get("member_order")),
            "packet_priority": as_int(member.get("packet_priority")),
            "ready_to_execute": as_int(member.get("ready_to_execute")),
            "queue_status": queue_status(member),
            "member_fingerprint": fingerprint,
            "allowed_execution_decisions": "; ".join(ALLOWED_EXECUTION_DECISIONS),
            "recommended_execution_action": recommended_execution_action(member),
            "required_output_routing": required_output_routing(member),
            "expected_downstream_artifacts_json": member.get("downstream_artifacts_json") or "[]",
            "command_hints_json": member.get("command_hints_json") or "[]",
            "top_source_urls": member.get("top_source_urls") or "",
            "evidence_json": dumps(
                {
                    "member": compact_member(member),
                    "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
                    "policy": {
                        "non_mutating": True,
                        "execution_tracking": "Execution outcomes record operator work only. Factual enrichment must be routed through source-specific ledgers and acceptance gates.",
                        "stale_guard": "Manual decisions must carry the current member_fingerprint.",
                    },
                }
            ),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        rows.append({field: row[field] for field in QUEUE_FIELDS})
    return rows


def ensure_manual_decisions_file() -> None:
    if MANUAL_DECISIONS_CSV.exists():
        return
    write_csv(MANUAL_DECISIONS_CSV, [], MANUAL_FIELDS)


def manual_decisions_by_key() -> dict[str, dict]:
    ensure_manual_decisions_file()
    return {row["execution_decision_key"]: row for row in read_csv(MANUAL_DECISIONS_CSV) if row.get("execution_decision_key")}


def audit_status(queue_row: dict, decision: dict | None) -> tuple[str, str, str]:
    if not as_int(queue_row.get("ready_to_execute")):
        return ("blocked_upstream_not_ready", "batch_member_not_ready_to_execute", "resolve_batch_or_packet_blocker")
    if not decision:
        return ("pending_execution_decision", "manual_execution_decision_missing", queue_row["recommended_execution_action"])
    execution_decision = decision.get("execution_decision") or ""
    if execution_decision not in ALLOWED_EXECUTION_DECISIONS:
        return ("invalid_execution_decision", "execution_decision_not_allowed", "correct_manual_execution_decision")
    if decision.get("member_fingerprint") != queue_row.get("member_fingerprint"):
        return ("stale_execution_decision", "manual_decision_member_fingerprint_mismatch", "re_execute_or_update_decision_against_current_member")
    if execution_decision == "executed_outputs_routed":
        if not as_int(decision.get("routed_to_downstream_ledgers")):
            return ("invalid_execution_routing", "executed_output_not_routed_to_downstream_ledgers", "route_outputs_to_source_specific_ledgers")
        return ("executed_outputs_routed", "none", "rebuild_reconciliation_and_acceptance_audits")
    if execution_decision == "executed_no_public_output":
        return ("executed_no_public_output", "none", "record_no_output_and_reprioritize_if_needed")
    if execution_decision == "skipped_superseded":
        return ("skipped_superseded", "none", "confirm_newer_packet_or_source_artifact_covers_member")
    if execution_decision == "needs_manual_review":
        return ("needs_manual_review", "manual_review_required_after_execution", "route_to_reviewer_queue_or_record_specific_blocker")
    return (execution_decision, execution_decision, "retry_or_replace_source_endpoint_then_rebuild")


def compact_decision(decision: dict | None) -> dict:
    if not decision:
        return {}
    return {
        key: decision.get(key, "")
        for key in [
            "execution_decision_key",
            "action_batch_member_key",
            "action_packet_key",
            "execution_decision",
            "executor_name",
            "executed_at",
            "output_record_count",
            "routed_to_downstream_ledgers",
        ]
    }


def build_audit(queue: list[dict], audited_at: str) -> list[dict]:
    decisions = manual_decisions_by_key()
    rows = []
    for item in queue:
        decision = decisions.get(item["execution_decision_key"])
        status, blocker, next_action = audit_status(item, decision)
        execution_decision = (decision or {}).get("execution_decision") or "pending"
        row = {
            "execution_decision_key": item["execution_decision_key"],
            "action_batch_member_key": item["action_batch_member_key"],
            "action_batch_key": item["action_batch_key"],
            "action_packet_key": item["action_packet_key"],
            "person_key": item["person_key"],
            "display_name": item["display_name"],
            "role": item["role"],
            "programs": item["programs"],
            "primary_action_lane": item["primary_action_lane"],
            "packet_status": item["packet_status"],
            "batch_status": item["batch_status"],
            "priority_band": item["priority_band"],
            "execution_order": item["execution_order"],
            "member_order": item["member_order"],
            "packet_priority": item["packet_priority"],
            "ready_to_execute": item["ready_to_execute"],
            "queue_status": item["queue_status"],
            "execution_decision": execution_decision,
            "execution_status": status,
            "execution_blocker": blocker,
            "member_fingerprint": item["member_fingerprint"],
            "decision_member_fingerprint": (decision or {}).get("member_fingerprint", ""),
            "executor_name": (decision or {}).get("executor_name", ""),
            "executed_at": (decision or {}).get("executed_at", ""),
            "command_run": (decision or {}).get("command_run", ""),
            "output_artifacts_json": (decision or {}).get("output_artifacts_json", "[]") or "[]",
            "output_record_count": as_int((decision or {}).get("output_record_count")),
            "routed_to_downstream_ledgers": as_int((decision or {}).get("routed_to_downstream_ledgers")),
            "downstream_ledger_notes": (decision or {}).get("downstream_ledger_notes", ""),
            "recommended_next_action": next_action,
            "evidence_json": dumps(
                {
                    "queue_row": {
                        "action_batch_member_key": item["action_batch_member_key"],
                        "queue_status": item["queue_status"],
                        "recommended_execution_action": item["recommended_execution_action"],
                        "required_output_routing": item["required_output_routing"],
                        "expected_downstream_artifacts_json": item["expected_downstream_artifacts_json"],
                    },
                    "manual_decision": compact_decision(decision),
                    "decision_policy": {
                        "allowed_execution_decisions": ALLOWED_EXECUTION_DECISIONS,
                        "executed_outputs_routed_requires": [
                            "member_fingerprint matches current queue row",
                            "routed_to_downstream_ledgers=1",
                            "outputs are recorded in source-specific ledgers before acceptance",
                        ],
                    },
                }
            ),
            "audited_at": audited_at,
        }
        rows.append({field: row[field] for field in AUDIT_FIELDS})
    return rows


def write_db(conn: sqlite3.Connection, table: str, rows: list[dict], fields: list[str]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    field_sql = ", ".join(fields)
    placeholders = ", ".join(f":{field}" for field in fields)
    conn.executemany(f"INSERT OR REPLACE INTO {table} ({field_sql}) VALUES ({placeholders})", rows)


def replay_manual_decisions(conn: sqlite3.Connection) -> None:
    ensure_manual_decisions_file()
    write_db(conn, "person_enrichment_action_member_execution_decisions", read_csv(MANUAL_DECISIONS_CSV), MANUAL_FIELDS)


def summary_payload(queue: list[dict], audit: list[dict], generated_at: str) -> dict:
    by_queue = Counter(row["queue_status"] for row in queue)
    by_status = Counter(row["execution_status"] for row in audit)
    by_lane = Counter(row["primary_action_lane"] for row in queue)
    by_decision = Counter(row["execution_decision"] for row in audit)
    return {
        "generated_at": generated_at,
        "queue_rows": len(queue),
        "audit_rows": len(audit),
        "manual_decision_rows": len(read_csv(MANUAL_DECISIONS_CSV)),
        "ready_queue_rows": sum(as_int(row["ready_to_execute"]) for row in queue),
        "blocked_queue_rows": sum(1 for row in queue if not as_int(row["ready_to_execute"])),
        "pending_execution_decision_rows": by_status.get("pending_execution_decision", 0),
        "executed_outputs_routed_rows": by_status.get("executed_outputs_routed", 0),
        "invalid_or_stale_decision_rows": sum(
            by_status.get(status, 0)
            for status in ["invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"]
        ),
        "by_queue_status": dict(sorted(by_queue.items())),
        "by_execution_status": dict(sorted(by_status.items())),
        "by_execution_decision": dict(sorted(by_decision.items())),
        "by_primary_action_lane": dict(sorted(by_lane.items())),
        "queue_csv": str(QUEUE_CSV.relative_to(ROOT)),
        "queue_json": str(QUEUE_JSON.relative_to(ROOT)),
        "manual_decision_csv": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
        "audit_csv": str(AUDIT_CSV.relative_to(ROOT)),
        "audit_json": str(AUDIT_JSON.relative_to(ROOT)),
        "policy": "Execution ledgers are non-mutating. They record whether batch members were worked and whether outputs were routed to source-specific ledgers; no person fact is accepted from execution notes alone.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    members = sqlite_rows(
        conn,
        """
        SELECT *
        FROM person_enrichment_action_batch_members
        ORDER BY execution_order, member_order, action_batch_member_key
        """,
    )
    queue = build_queue(members, generated_at)
    audit = build_audit(queue, generated_at)

    write_csv(QUEUE_CSV, queue, QUEUE_FIELDS)
    write_json(QUEUE_JSON, queue)
    write_csv(AUDIT_CSV, audit, AUDIT_FIELDS)
    write_json(AUDIT_JSON, audit)
    with conn:
        replay_manual_decisions(conn)
        write_db(conn, "person_enrichment_action_member_execution_queue", queue, QUEUE_FIELDS)
        write_db(conn, "person_enrichment_action_member_execution_audit", audit, AUDIT_FIELDS)
    conn.close()

    summary = summary_payload(queue, audit, generated_at)
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
