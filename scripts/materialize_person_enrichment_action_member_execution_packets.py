#!/usr/bin/env python3
"""Materialize batch/status packets over person enrichment action execution dossiers."""

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

CSV_PATH = ARTIFACTS / "person_enrichment_action_member_execution_packets.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_action_member_execution_packets.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_action_member_execution_packet_summary.json"
MANUAL_DECISIONS_CSV = ARTIFACTS / "person_enrichment_action_member_execution_decisions.csv"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "execution_packet_key",
    "action_batch_key",
    "primary_action_lane",
    "execution_status",
    "queue_status",
    "batch_status",
    "priority_band",
    "role",
    "ready_to_execute",
    "execution_order",
    "member_count",
    "pending_member_count",
    "blocked_member_count",
    "invalid_or_stale_member_count",
    "ready_member_count",
    "high_risk_member_count",
    "manual_review_member_count",
    "collector_execution_member_count",
    "max_packet_priority",
    "min_packet_priority",
    "total_task_count",
    "total_review_packet_count",
    "total_profile_workbench_count",
    "total_contact_contract_count",
    "total_evidence_record_count",
    "total_source_count",
    "top_member_names",
    "top_programs",
    "top_source_urls",
    "required_output_routing",
    "recommended_operator_action",
    "blocker_status",
    "packet_priority",
    "target_artifact",
    "acceptance_boundary",
    "allowed_execution_decisions",
    "manual_execution_templates_json",
    "command_hints_json",
    "output_routing_checklist_json",
    "expected_downstream_artifacts_json",
    "top_dossiers_json",
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


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {
        row["execution_packet_key"]: row
        for row in read_csv(CSV_PATH)
        if row.get("execution_packet_key")
    }


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["execution_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def packet_key(action_batch_key: str, lane: str, status: str) -> str:
    return "person_enrichment_action_member_execution_packet_" + sha256_text(
        "|".join([action_batch_key, lane, status])
    )[:20]


def split_values(value: str | None, separator: str = ";") -> list[str]:
    output = []
    for item in (value or "").split(separator):
        item = item.strip()
        if item and item not in output:
            output.append(item)
    return output


def append_unique(output: list, value) -> None:
    if value in (None, "", [], {}):
        return
    if value not in output:
        output.append(value)


def merge_json_lists(rows: list[dict], field: str, limit: int = 25) -> list:
    merged = []
    for row in rows:
        value = parse_json(row.get(field), [])
        if not isinstance(value, list):
            continue
        for item in value:
            append_unique(merged, item)
            if len(merged) >= limit:
                return merged
    return merged


def expected_artifacts(rows: list[dict]) -> list[str]:
    artifacts = []
    for row in rows:
        for artifact in parse_json(row.get("expected_downstream_artifacts_json"), []):
            if isinstance(artifact, str):
                append_unique(artifacts, artifact)
        summary = parse_json(row.get("downstream_artifact_summary_json"), {})
        if isinstance(summary, dict):
            for artifact in summary.get("artifacts", []):
                if isinstance(artifact, str):
                    append_unique(artifacts, artifact)
    return artifacts


def top_semicolon_values(rows: list[dict], field: str, limit: int = 20) -> str:
    values = []
    for row in rows:
        for item in split_values(row.get(field)):
            append_unique(values, item)
            if len(values) >= limit:
                return "; ".join(values)
    return "; ".join(values)


def top_urls(rows: list[dict], limit: int = 20) -> str:
    values = []
    for row in rows:
        for item in split_values(row.get("top_source_urls")):
            append_unique(values, item)
            if len(values) >= limit:
                return "; ".join(values)
    return "; ".join(values)


def target_artifact(lane: str, status: str) -> str:
    if status == "blocked_upstream_not_ready" and lane == "profile_search_retry":
        return "artifacts/data/trainee_profile_search_observations.csv"
    return "artifacts/data/person_enrichment_action_member_execution_decisions.csv"


def recommended_operator_action(lane: str, status: str) -> str:
    if status == "pending_execution_decision":
        return {
            "person_evidence_review": "record_person_evidence_review_execution_decisions_with_current_fingerprints",
            "official_profile_review": "record_official_profile_review_execution_decisions_with_current_fingerprints",
            "official_profile_discovery": "run_profile_discovery_then_record_member_execution_decisions",
            "enrichment_collector_execution": "run_collector_tasks_then_record_member_execution_decisions",
        }.get(lane, "record_member_execution_decisions_with_current_fingerprints")
    if status == "blocked_upstream_not_ready":
        return "resolve_upstream_search_or_batch_blocker_before_member_execution"
    if status in {"invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"}:
        return "repair_member_execution_decisions_with_current_fingerprints_and_routing"
    if status == "needs_manual_review":
        return "route_execution_outputs_to_source_specific_reviewer_queue"
    return "monitor_routed_member_execution_outputs"


def blocker_status(status_counts: Counter, sample: dict) -> str:
    invalid = sum(
        status_counts.get(status, 0)
        for status in ["invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"]
    )
    if invalid:
        return "invalid_or_stale_member_execution_decisions"
    if status_counts.get("blocked_upstream_not_ready"):
        return sample.get("execution_blocker") or "blocked_upstream_not_ready"
    if status_counts.get("pending_execution_decision"):
        return "manual_execution_decision_missing"
    return "no_execution_blocker"


def packet_priority(max_priority: int, status_counts: Counter) -> int:
    priority = 760 + min(max_priority, 400)
    if status_counts.get("pending_execution_decision"):
        priority += 90
    if status_counts.get("blocked_upstream_not_ready") and not status_counts.get("pending_execution_decision"):
        priority -= 120
    if any(status_counts.get(status, 0) for status in ["invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"]):
        priority += 160
    return priority


def top_dossiers(rows: list[dict], limit: int = 25) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("packet_priority")), as_int(item.get("member_order")), item.get("display_name") or ""))[:limit]:
        output.append(
            {
                "dossier_key": row.get("dossier_key"),
                "execution_decision_key": row.get("execution_decision_key"),
                "action_batch_member_key": row.get("action_batch_member_key"),
                "action_packet_key": row.get("action_packet_key"),
                "person_key": row.get("person_key"),
                "display_name": row.get("display_name"),
                "role": row.get("role"),
                "programs": row.get("programs"),
                "packet_priority": as_int(row.get("packet_priority")),
                "decision_complexity": row.get("decision_complexity"),
                "dossier_status": row.get("dossier_status"),
                "execution_risk_level": row.get("execution_risk_level"),
                "execution_blocker": row.get("execution_blocker"),
                "member_fingerprint": row.get("member_fingerprint"),
                "recommended_operator_action": row.get("recommended_operator_action"),
            }
        )
    return output


def manual_templates(rows: list[dict], limit: int = 25) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("packet_priority")), as_int(item.get("member_order")), item.get("display_name") or ""))[:limit]:
        template = parse_json(row.get("manual_execution_template_json"), {})
        if isinstance(template, dict):
            template["display_name"] = row.get("display_name") or ""
            template["primary_action_lane"] = row.get("primary_action_lane") or ""
            template["execution_status"] = row.get("execution_status") or ""
            output.append(template)
    return output


def build_rows(dossiers: list[dict], generated_at: str) -> list[dict]:
    existing = read_existing()
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in dossiers:
        status = row.get("execution_status") or ""
        if status in {"executed_outputs_routed", "executed_no_public_output", "skipped_superseded"}:
            continue
        key = (row.get("action_batch_key") or "", row.get("primary_action_lane") or "", status)
        grouped[key].append(row)

    output = []
    for (batch_key, lane, status), group in grouped.items():
        group.sort(key=lambda item: (-as_int(item.get("packet_priority")), as_int(item.get("member_order")), item.get("display_name") or ""))
        sample = group[0]
        status_counts = Counter(row.get("execution_status") or "" for row in group)
        queue_counts = Counter(row.get("queue_status") or "" for row in group)
        dossier_counts = Counter(row.get("dossier_status") or "" for row in group)
        risk_counts = Counter(row.get("execution_risk_level") or "" for row in group)
        max_priority = max(as_int(row.get("packet_priority")) for row in group)
        min_priority = min(as_int(row.get("packet_priority")) for row in group)
        invalid = sum(
            status_counts.get(item, 0)
            for item in ["invalid_execution_decision", "stale_execution_decision", "invalid_execution_routing"]
        )
        row = {
            "execution_packet_key": packet_key(batch_key, lane, status),
            "action_batch_key": batch_key,
            "primary_action_lane": lane,
            "execution_status": status,
            "queue_status": sample.get("queue_status") or "",
            "batch_status": sample.get("batch_status") or "",
            "priority_band": sample.get("priority_band") or "",
            "role": sample.get("role") or "",
            "ready_to_execute": 1 if all(as_int(item.get("ready_to_execute")) for item in group) else 0,
            "execution_order": as_int(sample.get("execution_order")),
            "member_count": len(group),
            "pending_member_count": status_counts.get("pending_execution_decision", 0),
            "blocked_member_count": sum(count for item, count in status_counts.items() if item.startswith("blocked_")),
            "invalid_or_stale_member_count": invalid,
            "ready_member_count": sum(as_int(item.get("ready_to_execute")) for item in group),
            "high_risk_member_count": risk_counts.get("high", 0),
            "manual_review_member_count": sum(
                count
                for item, count in dossier_counts.items()
                if item in {"pending_manual_review_execution", "pending_manual_review_after_execution"}
            ),
            "collector_execution_member_count": dossier_counts.get("pending_collector_execution", 0),
            "max_packet_priority": max_priority,
            "min_packet_priority": min_priority,
            "total_task_count": sum(as_int(item.get("task_count")) for item in group),
            "total_review_packet_count": sum(as_int(item.get("review_packet_count")) for item in group),
            "total_profile_workbench_count": sum(as_int(item.get("profile_workbench_count")) for item in group),
            "total_contact_contract_count": sum(as_int(item.get("contact_contract_count")) for item in group),
            "total_evidence_record_count": sum(as_int(item.get("evidence_record_count")) for item in group),
            "total_source_count": sum(as_int(item.get("source_count")) for item in group),
            "top_member_names": "; ".join(
                list(dict.fromkeys(item.get("display_name") or "" for item in group if item.get("display_name")))[:25]
            ),
            "top_programs": top_semicolon_values(group, "programs"),
            "top_source_urls": top_urls(group),
            "required_output_routing": sample.get("required_output_routing") or "",
            "recommended_operator_action": recommended_operator_action(lane, status),
            "blocker_status": blocker_status(status_counts, sample),
            "packet_priority": packet_priority(max_priority, status_counts),
            "target_artifact": target_artifact(lane, status),
            "acceptance_boundary": (
                "Execution packets are non-mutating. They group current-fingerprint execution dossiers; "
                "facts only materialize after outputs are routed to source-specific ledgers and pass reviewer "
                "or acceptance audits."
            ),
            "allowed_execution_decisions": sample.get("allowed_execution_decisions") or "",
            "manual_execution_templates_json": dumps(manual_templates(group)),
            "command_hints_json": dumps(merge_json_lists(group, "command_hints_json")),
            "output_routing_checklist_json": dumps(merge_json_lists(group, "output_routing_checklist_json")),
            "expected_downstream_artifacts_json": dumps(expected_artifacts(group)),
            "top_dossiers_json": dumps(top_dossiers(group)),
            "evidence_json": dumps(
                {
                    "action_batch_key": batch_key,
                    "primary_action_lane": lane,
                    "execution_status": status,
                    "queue_status_counts": dict(sorted(queue_counts.items())),
                    "dossier_status_counts": dict(sorted(dossier_counts.items())),
                    "execution_risk_counts": dict(sorted(risk_counts.items())),
                    "manual_decision_file": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
                    "member_count": len(group),
                    "member_fingerprint_policy": "manual execution decisions must copy the current member_fingerprint from each dossier template",
                    "downstream_artifacts": expected_artifacts(group),
                }
            ),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        output.append({field: row[field] for field in FIELDS})
    return sorted(output, key=lambda item: (-as_int(item["packet_priority"]), as_int(item["execution_order"]), item["execution_packet_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_enrichment_action_member_execution_packets")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO person_enrichment_action_member_execution_packets ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def summary_payload(rows: list[dict], generated_at: str) -> dict:
    by_lane = Counter(row["primary_action_lane"] for row in rows)
    by_status = Counter(row["execution_status"] for row in rows)
    by_blocker = Counter(row["blocker_status"] for row in rows)
    return {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "member_count": sum(as_int(row["member_count"]) for row in rows),
        "pending_member_count": sum(as_int(row["pending_member_count"]) for row in rows),
        "blocked_member_count": sum(as_int(row["blocked_member_count"]) for row in rows),
        "invalid_or_stale_member_count": sum(as_int(row["invalid_or_stale_member_count"]) for row in rows),
        "ready_member_count": sum(as_int(row["ready_member_count"]) for row in rows),
        "manual_review_member_count": sum(as_int(row["manual_review_member_count"]) for row in rows),
        "collector_execution_member_count": sum(as_int(row["collector_execution_member_count"]) for row in rows),
        "by_primary_action_lane": dict(sorted(by_lane.items())),
        "by_execution_status": dict(sorted(by_status.items())),
        "by_blocker_status": dict(sorted(by_blocker.items())),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "manual_decision_csv": str(MANUAL_DECISIONS_CSV.relative_to(ROOT)),
        "policy": "Execution packets are non-mutating groupings over current-fingerprint execution dossiers; downstream reviewer/acceptance ledgers remain the fact gate.",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    dossiers = read_csv(ARTIFACTS / "person_enrichment_action_member_execution_dossiers.csv")
    rows = build_rows(dossiers, generated_at)
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
