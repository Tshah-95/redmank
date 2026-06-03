#!/usr/bin/env python3
"""Materialize compact dossiers for person enrichment action member execution."""

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

CSV_PATH = ARTIFACTS / "person_enrichment_action_member_execution_dossiers.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_action_member_execution_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_action_member_execution_dossier_summary.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "person_enrichment_action_member_execution_decisions.csv"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "dossier_key",
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
    "execution_status",
    "execution_decision",
    "execution_blocker",
    "decision_complexity",
    "dossier_status",
    "execution_risk_level",
    "task_count",
    "review_packet_count",
    "profile_workbench_count",
    "contact_contract_count",
    "evidence_record_count",
    "source_count",
    "required_output_routing",
    "expected_downstream_artifacts_json",
    "top_source_urls",
    "allowed_execution_decisions",
    "manual_execution_template_json",
    "command_hints_json",
    "next_action_sequence_json",
    "output_routing_checklist_json",
    "downstream_artifact_summary_json",
    "missing_execution_summary",
    "recommended_operator_action",
    "acceptance_boundary",
    "member_fingerprint",
    "evidence_json",
    "generated_at",
]


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


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["dossier_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["dossier_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def dossier_key(row: dict) -> str:
    return "person_enrichment_action_member_execution_dossier_" + sha256_text(row["execution_decision_key"])[:20]


def load_rows(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT
          a.*,
          q.allowed_execution_decisions,
          q.required_output_routing,
          q.expected_downstream_artifacts_json,
          q.command_hints_json AS queue_command_hints_json,
          q.top_source_urls AS queue_top_source_urls,
          m.task_count,
          m.review_packet_count,
          m.profile_workbench_count,
          m.contact_contract_count,
          m.evidence_record_count,
          m.source_count,
          m.required_next_evidence,
          m.primary_blocker,
          m.command_hints_json AS member_command_hints_json,
          m.next_action_sequence_json,
          m.downstream_artifacts_json AS member_downstream_artifacts_json,
          m.evidence_json AS member_evidence_json
        FROM person_enrichment_action_member_execution_audit a
        JOIN person_enrichment_action_member_execution_queue q
          ON q.execution_decision_key = a.execution_decision_key
        JOIN person_enrichment_action_batch_members m
          ON m.action_batch_member_key = a.action_batch_member_key
        ORDER BY a.execution_order, a.member_order, a.execution_decision_key
        """,
    )


def decision_complexity(row: dict) -> str:
    lane = row.get("primary_action_lane") or ""
    if row.get("execution_status") in {"invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"}:
        return "decision_repair"
    if not as_int(row.get("ready_to_execute")):
        return "blocked_upstream"
    if lane == "person_evidence_review":
        if as_int(row.get("review_packet_count")) > 1 or as_int(row.get("evidence_record_count")) >= 3:
            return "multi_evidence_review"
        return "single_packet_review"
    if lane == "official_profile_review":
        return "official_profile_manual_review"
    if lane == "official_profile_discovery":
        return "profile_discovery_execution"
    if lane == "enrichment_collector_execution":
        if as_int(row.get("task_count")) >= 7:
            return "multi_collector_execution"
        return "collector_execution"
    if lane == "profile_search_retry":
        return "search_endpoint_retry"
    return "operator_execution"


def dossier_status(row: dict) -> str:
    status = row.get("execution_status") or ""
    if status == "pending_execution_decision":
        lane = row.get("primary_action_lane") or ""
        if lane in {"person_evidence_review", "official_profile_review"}:
            return "pending_manual_review_execution"
        if lane in {"official_profile_discovery", "enrichment_collector_execution"}:
            return "pending_collector_execution"
        return "pending_execution_decision"
    if status == "blocked_upstream_not_ready":
        return "blocked_upstream_not_ready"
    if status in {"invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"}:
        return "pending_execution_decision_repair"
    if status == "executed_outputs_routed":
        return "executed_outputs_routed"
    if status == "executed_no_public_output":
        return "executed_no_public_output"
    if status == "skipped_superseded":
        return "skipped_superseded"
    if status == "needs_manual_review":
        return "pending_manual_review_after_execution"
    if status.startswith("blocked_") or status.startswith("failed_"):
        return "blocked_or_failed_execution"
    return status or "unknown_execution_status"


def execution_risk_level(row: dict) -> str:
    status = row.get("execution_status") or ""
    lane = row.get("primary_action_lane") or ""
    if status in {"invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"}:
        return "high"
    if not as_int(row.get("ready_to_execute")):
        return "medium"
    if lane in {"person_evidence_review", "official_profile_review"}:
        return "high"
    if as_int(row.get("source_count")) >= 3 or as_int(row.get("evidence_record_count")) >= 3:
        return "medium"
    return "low"


def missing_execution_summary(row: dict) -> str:
    status = row.get("execution_status") or ""
    if status == "pending_execution_decision":
        return "missing current-fingerprint execution decision and downstream routing evidence"
    if status == "blocked_upstream_not_ready":
        blocker = row.get("primary_blocker") or row.get("execution_blocker") or "upstream blocker"
        return f"blocked before execution: {blocker}"
    if status == "invalid_execution_decision":
        return "manual execution decision is not in the allowed decision set"
    if status == "stale_execution_decision":
        return "manual execution decision fingerprint does not match the current member"
    if status == "invalid_execution_routing":
        return "execution was marked complete without routed downstream ledgers"
    if status == "needs_manual_review":
        return "execution outcome needs a source-specific reviewer decision"
    return "no missing execution evidence"


def recommended_operator_action(row: dict) -> str:
    status = row.get("execution_status") or ""
    if status == "pending_execution_decision":
        return row.get("recommended_next_action") or "execute_or_review_member_and_record_current_fingerprint_decision"
    if status == "blocked_upstream_not_ready":
        return "resolve_upstream_batch_or_packet_blocker_before_execution"
    if status in {"invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"}:
        return row.get("recommended_next_action") or "repair_execution_decision_with_current_member_fingerprint"
    if status == "needs_manual_review":
        return "route_execution_output_to_source_specific_reviewer_queue"
    return row.get("recommended_next_action") or "monitor_execution_outcome"


def output_routing_checklist(row: dict) -> list[str]:
    lane = row.get("primary_action_lane") or ""
    checklist = [
        "copy the current member_fingerprint into the manual execution decision",
        "record the exact command_run or reviewer action",
    ]
    if lane == "person_evidence_review":
        checklist.append("record source-specific person evidence decisions before acceptance")
    elif lane == "official_profile_review":
        checklist.append("record official profile reviewer decisions before profile acceptance")
    elif lane == "official_profile_discovery":
        checklist.append("write profile candidates/workbench rows and rebuild reviewer queues")
    elif lane == "enrichment_collector_execution":
        checklist.append("write collector outputs to source-specific claim/contact/profile artifacts")
    else:
        checklist.append("route outputs to the expected downstream artifacts")
    checklist.append("set routed_to_downstream_ledgers=1 only after downstream artifacts exist")
    return checklist


def downstream_artifact_summary(row: dict) -> dict:
    expected = parse_json(row.get("expected_downstream_artifacts_json"), [])
    member = parse_json(row.get("member_downstream_artifacts_json"), [])
    if not isinstance(expected, list):
        expected = []
    if not isinstance(member, list):
        member = []
    merged = []
    seen = set()
    for item in expected + member:
        if isinstance(item, str) and item and item not in seen:
            merged.append(item)
            seen.add(item)
    return {
        "artifact_count": len(merged),
        "artifacts": merged,
        "has_expected_artifacts": bool(expected),
    }


def manual_execution_template(row: dict) -> dict:
    return {
        "execution_decision_key": row.get("execution_decision_key") or "",
        "action_batch_member_key": row.get("action_batch_member_key") or "",
        "action_packet_key": row.get("action_packet_key") or "",
        "member_fingerprint": row.get("member_fingerprint") or "",
        "execution_decision": "",
        "executor_name": "",
        "executed_at": "",
        "command_run": "",
        "output_artifacts_json": "[]",
        "output_record_count": 0,
        "routed_to_downstream_ledgers": 0,
        "downstream_ledger_notes": "",
        "decision_notes": "",
    }


def build_dossiers(rows: list[dict], generated_at: str) -> list[dict]:
    existing = read_existing()
    output = []
    for row in rows:
        command_hints = parse_json(row.get("queue_command_hints_json") or row.get("member_command_hints_json"), [])
        if not isinstance(command_hints, list):
            command_hints = []
        next_actions = parse_json(row.get("next_action_sequence_json"), [])
        if not isinstance(next_actions, list):
            next_actions = []
        downstream_summary = downstream_artifact_summary(row)
        item = {
            "dossier_key": dossier_key(row),
            "execution_decision_key": row.get("execution_decision_key") or "",
            "action_batch_member_key": row.get("action_batch_member_key") or "",
            "action_batch_key": row.get("action_batch_key") or "",
            "action_packet_key": row.get("action_packet_key") or "",
            "person_key": row.get("person_key") or "",
            "display_name": row.get("display_name") or "",
            "role": row.get("role") or "",
            "programs": row.get("programs") or "",
            "primary_action_lane": row.get("primary_action_lane") or "",
            "packet_status": row.get("packet_status") or "",
            "batch_status": row.get("batch_status") or "",
            "priority_band": row.get("priority_band") or "",
            "execution_order": as_int(row.get("execution_order")),
            "member_order": as_int(row.get("member_order")),
            "packet_priority": as_int(row.get("packet_priority")),
            "ready_to_execute": as_int(row.get("ready_to_execute")),
            "queue_status": row.get("queue_status") or "",
            "execution_status": row.get("execution_status") or "",
            "execution_decision": row.get("execution_decision") or "",
            "execution_blocker": row.get("execution_blocker") or "",
            "decision_complexity": decision_complexity(row),
            "dossier_status": dossier_status(row),
            "execution_risk_level": execution_risk_level(row),
            "task_count": as_int(row.get("task_count")),
            "review_packet_count": as_int(row.get("review_packet_count")),
            "profile_workbench_count": as_int(row.get("profile_workbench_count")),
            "contact_contract_count": as_int(row.get("contact_contract_count")),
            "evidence_record_count": as_int(row.get("evidence_record_count")),
            "source_count": as_int(row.get("source_count")),
            "required_output_routing": row.get("required_output_routing") or "",
            "expected_downstream_artifacts_json": row.get("expected_downstream_artifacts_json") or "[]",
            "top_source_urls": row.get("queue_top_source_urls") or row.get("top_source_urls") or "",
            "allowed_execution_decisions": row.get("allowed_execution_decisions") or "",
            "manual_execution_template_json": dumps(manual_execution_template(row)),
            "command_hints_json": dumps(command_hints),
            "next_action_sequence_json": dumps(next_actions),
            "output_routing_checklist_json": dumps(output_routing_checklist(row)),
            "downstream_artifact_summary_json": dumps(downstream_summary),
            "missing_execution_summary": missing_execution_summary(row),
            "recommended_operator_action": recommended_operator_action(row),
            "acceptance_boundary": "Execution dossiers do not accept person facts. Outputs must be written to source-specific ledgers and pass reviewer or acceptance audits before mutation.",
            "member_fingerprint": row.get("member_fingerprint") or "",
            "evidence_json": dumps(
                {
                    "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
                    "member_evidence": parse_json(row.get("member_evidence_json"), {}),
                    "downstream_artifacts": downstream_summary,
                    "policy": {
                        "non_mutating": True,
                        "fingerprint_required": True,
                        "routing_required_for_executed_outputs": True,
                    },
                }
            ),
            "generated_at": "",
        }
        item["generated_at"] = stable_generated_at(existing, item, generated_at)
        output.append({field: item[field] for field in FIELDS})
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_enrichment_action_member_execution_dossiers")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"""
        INSERT OR REPLACE INTO person_enrichment_action_member_execution_dossiers
        ({field_sql}) VALUES ({placeholders})
        """,
        rows,
    )


def summary_payload(rows: list[dict], generated_at: str) -> dict:
    by_lane = Counter(row["primary_action_lane"] for row in rows)
    by_status = Counter(row["dossier_status"] for row in rows)
    by_complexity = Counter(row["decision_complexity"] for row in rows)
    by_risk = Counter(row["execution_risk_level"] for row in rows)
    pending_rows = [row for row in rows if row["dossier_status"].startswith("pending")]
    return {
        "generated_at": generated_at,
        "dossier_rows": len(rows),
        "ready_dossier_rows": sum(as_int(row["ready_to_execute"]) for row in rows),
        "blocked_dossier_rows": sum(1 for row in rows if not as_int(row["ready_to_execute"])),
        "pending_dossier_rows": len(pending_rows),
        "manual_review_dossier_rows": sum(
            1 for row in rows if row["dossier_status"] in {"pending_manual_review_execution", "pending_manual_review_after_execution"}
        ),
        "collector_execution_dossier_rows": sum(1 for row in rows if row["dossier_status"] == "pending_collector_execution"),
        "decision_repair_dossier_rows": sum(1 for row in rows if row["dossier_status"] == "pending_execution_decision_repair"),
        "by_primary_action_lane": dict(sorted(by_lane.items())),
        "by_dossier_status": dict(sorted(by_status.items())),
        "by_decision_complexity": dict(sorted(by_complexity.items())),
        "by_execution_risk_level": dict(sorted(by_risk.items())),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "manual_decision_csv": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
        "policy": "Execution dossiers are operator templates over the fingerprinted execution ledger. They do not accept facts; they require routed downstream ledgers for factual enrichment.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = build_dossiers(load_rows(conn), generated_at)
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    with conn:
        write_db(conn, rows)
    conn.close()

    summary = summary_payload(rows, generated_at)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
