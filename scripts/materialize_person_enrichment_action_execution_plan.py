#!/usr/bin/env python3
"""Materialize batch-level execution plans for person enrichment action work."""

from __future__ import annotations

import argparse
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

CSV_PATH = ARTIFACTS / "person_enrichment_action_execution_plan.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_action_execution_plan.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_action_execution_plan_summary.json"

DECISIONS_CSV = ARTIFACTS / "person_enrichment_action_member_execution_decisions.csv"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "execution_plan_key",
    "action_batch_key",
    "primary_action_lane",
    "role",
    "priority_band",
    "batch_status",
    "ready_to_execute",
    "execution_order",
    "packet_count",
    "person_count",
    "pending_member_count",
    "blocked_member_count",
    "executed_member_count",
    "invalid_or_stale_member_count",
    "max_packet_priority",
    "total_review_packet_count",
    "total_evidence_record_count",
    "total_profile_workbench_count",
    "top_programs",
    "top_member_names",
    "first_command_hint",
    "command_hints_json",
    "expected_downstream_artifacts_json",
    "required_output_routing",
    "decision_template_json",
    "recommended_operator_action",
    "blocker_status",
    "acceptance_boundary",
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
        return {row["execution_plan_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["execution_plan_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def plan_key(action_batch_key: str) -> str:
    return "person_enrichment_action_execution_plan_" + sha256_text(action_batch_key)[:20]


def first_command_hint(command_hints_json: str) -> str:
    hints = parse_json(command_hints_json, [])
    if isinstance(hints, list) and hints:
        return str(hints[0])
    return ""


def expected_artifacts(batch: dict, members: list[dict]) -> str:
    artifacts = parse_json(batch.get("downstream_artifacts_json"), [])
    if not isinstance(artifacts, list):
        artifacts = []
    for member in members:
        for artifact in parse_json(member.get("output_artifacts_json"), []):
            if artifact and artifact not in artifacts:
                artifacts.append(artifact)
    return dumps(artifacts)


def routing_for_lane(lane: str) -> str:
    if lane == "person_evidence_review":
        return "Record reviewer decisions in person_evidence_reviewer_decisions.csv; accepted facts flow through enrichment/trend acceptance ledgers."
    if lane == "official_profile_review":
        return "Record profile decisions in official_profile_reviewer_decisions.csv before any profile URL fact is accepted."
    if lane == "official_profile_discovery":
        return "Run profile discovery and route outputs through trainee_profile_discovery_* plus official_profile_discovery_workbench."
    if lane == "enrichment_collector_execution":
        return "Route collector outputs to source-specific claim/contact/search artifacts, then rebuild reconciliation and acceptance ledgers."
    if lane == "profile_search_retry":
        return "Replace or retry the search endpoint before rerunning official profile discovery."
    return "Route outputs through named downstream ledgers before any accepted fact is materialized."


def recommended_action(batch: dict, pending: int, blocked: int, invalid: int) -> str:
    lane = batch.get("primary_action_lane") or ""
    if invalid:
        return "fix_invalid_or_stale_member_execution_decisions_before_new_execution"
    if blocked and not pending:
        return "resolve_batch_blocker_before_execution"
    if lane == "person_evidence_review":
        return "work_person_evidence_review_batch_and_record_member_execution_decisions"
    if lane == "official_profile_review":
        return "work_official_profile_review_batch_and_record_member_execution_decisions"
    if lane == "official_profile_discovery":
        return "run_official_profile_discovery_for_batch_then_route_outputs"
    if lane == "enrichment_collector_execution":
        return "run_collector_batch_then_route_outputs"
    if lane == "profile_search_retry":
        return "retry_or_replace_profile_search_endpoint"
    return "execute_ready_batch_and_record_member_decisions"


def blocker_status(batch: dict, pending: int, blocked: int, invalid: int) -> str:
    if invalid:
        return "invalid_or_stale_member_execution_decisions"
    if blocked and not as_int(batch.get("ready_to_execute")):
        return batch.get("blocked_reason") or "batch_blocked_upstream"
    if pending:
        return "manual_execution_decision_missing"
    return "no_execution_blocker"


def top_member_names(members: list[dict], limit: int = 12) -> str:
    names = []
    for row in sorted(members, key=lambda item: (-as_int(item.get("packet_priority")), as_int(item.get("member_order")))):
        name = row.get("display_name") or ""
        if name and name not in names:
            names.append(name)
        if len(names) >= limit:
            break
    return "; ".join(names)


def decision_template(members: list[dict], limit: int = 10) -> list[dict]:
    template = []
    pending = [row for row in members if row.get("execution_status") == "pending_execution_decision"]
    pending.sort(key=lambda item: (-as_int(item.get("packet_priority")), as_int(item.get("member_order"))))
    for row in pending[:limit]:
        template.append(
            {
                "execution_decision_key": row.get("execution_decision_key"),
                "action_batch_member_key": row.get("action_batch_member_key"),
                "action_packet_key": row.get("action_packet_key"),
                "member_fingerprint": row.get("member_fingerprint"),
                "display_name": row.get("display_name"),
                "recommended_execution_action": row.get("recommended_next_action"),
                "allowed_execution_decisions": [
                    "executed_outputs_routed",
                    "executed_no_public_output",
                    "blocked_source_unavailable",
                    "blocked_rate_limited",
                    "failed_retry_needed",
                    "skipped_superseded",
                    "needs_manual_review",
                ],
            }
        )
    return template


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    batches = sqlite_rows(conn, "SELECT * FROM person_enrichment_action_batches ORDER BY execution_order, action_batch_key")
    members_by_batch: dict[str, list[dict]] = defaultdict(list)
    for row in sqlite_rows(conn, "SELECT * FROM person_enrichment_action_member_execution_audit"):
        members_by_batch[row["action_batch_key"]].append(row)

    rows = []
    for batch in batches:
        members = members_by_batch.get(batch["action_batch_key"], [])
        status_counts = Counter(member.get("execution_status") or "" for member in members)
        pending = status_counts.get("pending_execution_decision", 0)
        blocked = sum(1 for member in members if str(member.get("execution_status", "")).startswith("blocked_"))
        executed = status_counts.get("executed_outputs_routed", 0) + status_counts.get("executed_no_public_output", 0)
        invalid = sum(
            status_counts.get(status, 0)
            for status in ["invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"]
        )
        template = decision_template(members)
        action = recommended_action(batch, pending, blocked, invalid)
        blocker = blocker_status(batch, pending, blocked, invalid)
        evidence = {
            "action_batch": {
                key: batch.get(key)
                for key in [
                    "action_batch_key",
                    "primary_action_lane",
                    "packet_status",
                    "priority_band",
                    "batch_status",
                    "ready_to_execute",
                    "packet_count",
                    "person_count",
                    "max_priority",
                ]
            },
            "member_execution_status_counts": dict(sorted(status_counts.items())),
            "decision_template_sample": template,
            "manual_decision_file": str(DECISIONS_CSV.relative_to(ROOT)),
            "policy": {
                "non_mutating": True,
                "member_decisions_require_current_fingerprint": True,
                "execution_notes_do_not_accept_facts": True,
            },
        }
        row = {
            "execution_plan_key": plan_key(batch["action_batch_key"]),
            "action_batch_key": batch["action_batch_key"],
            "primary_action_lane": batch.get("primary_action_lane") or "",
            "role": batch.get("role") or "",
            "priority_band": batch.get("priority_band") or "",
            "batch_status": batch.get("batch_status") or "",
            "ready_to_execute": as_int(batch.get("ready_to_execute")),
            "execution_order": as_int(batch.get("execution_order")),
            "packet_count": as_int(batch.get("packet_count")),
            "person_count": as_int(batch.get("person_count")),
            "pending_member_count": pending,
            "blocked_member_count": blocked,
            "executed_member_count": executed,
            "invalid_or_stale_member_count": invalid,
            "max_packet_priority": as_int(batch.get("max_priority")),
            "total_review_packet_count": as_int(batch.get("total_review_packet_count")),
            "total_evidence_record_count": as_int(batch.get("total_evidence_record_count")),
            "total_profile_workbench_count": as_int(batch.get("total_profile_workbench_count")),
            "top_programs": batch.get("top_programs") or "",
            "top_member_names": top_member_names(members),
            "first_command_hint": first_command_hint(batch.get("command_hints_json") or "[]"),
            "command_hints_json": batch.get("command_hints_json") or "[]",
            "expected_downstream_artifacts_json": expected_artifacts(batch, members),
            "required_output_routing": routing_for_lane(batch.get("primary_action_lane") or ""),
            "decision_template_json": dumps(template),
            "recommended_operator_action": action,
            "blocker_status": blocker,
            "acceptance_boundary": (
                "Execution plans are non-mutating. Member execution decisions only record work performed; factual "
                "changes require source-specific artifacts plus reviewer/acceptance ledgers."
            ),
            "evidence_json": dumps(evidence),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        rows.append({field: row[field] for field in FIELDS})
    return sorted(rows, key=lambda item: (-as_int(item["max_packet_priority"]), as_int(item["execution_order"]), item["action_batch_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_enrichment_action_execution_plan")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO person_enrichment_action_execution_plan ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_lane = Counter(row["primary_action_lane"] for row in rows)
    by_blocker = Counter(row["blocker_status"] for row in rows)
    by_status = Counter(row["batch_status"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "execution_plan_rows": len(rows),
        "ready_plan_rows": sum(as_int(row["ready_to_execute"]) for row in rows),
        "pending_member_count": sum(as_int(row["pending_member_count"]) for row in rows),
        "blocked_member_count": sum(as_int(row["blocked_member_count"]) for row in rows),
        "executed_member_count": sum(as_int(row["executed_member_count"]) for row in rows),
        "invalid_or_stale_member_count": sum(as_int(row["invalid_or_stale_member_count"]) for row in rows),
        "by_primary_action_lane": dict(sorted(by_lane.items())),
        "by_blocker_status": dict(sorted(by_blocker.items())),
        "by_batch_status": dict(sorted(by_status.items())),
        "top_execution_plans": [
            {
                "execution_order": row["execution_order"],
                "primary_action_lane": row["primary_action_lane"],
                "role": row["role"],
                "priority_band": row["priority_band"],
                "batch_status": row["batch_status"],
                "packet_count": row["packet_count"],
                "pending_member_count": row["pending_member_count"],
                "max_packet_priority": row["max_packet_priority"],
                "recommended_operator_action": row["recommended_operator_action"],
                "first_command_hint": row["first_command_hint"],
            }
            for row in rows[:20]
        ],
        "policy": "Execution plans are non-mutating batch-level operator instructions over member execution fingerprints.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = build_rows(conn, generated_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"person_enrichment_action_execution_plan": len(rows), "generated_at": generated_at}))


if __name__ == "__main__":
    main()
