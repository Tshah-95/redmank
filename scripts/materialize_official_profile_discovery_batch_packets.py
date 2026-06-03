#!/usr/bin/env python3
"""Materialize per-workbench packet support rows for official profile discovery batches."""

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

CSV_PATH = ARTIFACTS / "official_profile_discovery_batch_packets.csv"
JSON_PATH = ARTIFACTS / "official_profile_discovery_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "official_profile_discovery_batch_packet_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "profile_discovery_packet_key",
    "official_profile_discovery_batch_key",
    "execution_order",
    "batch_packet_order",
    "profile_workbench_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "task_key",
    "discovery_lane",
    "batch_status",
    "profile_gap_status",
    "packet_status",
    "support_status",
    "discovery_priority",
    "query_count",
    "observed_query_count",
    "unsearched_query_count",
    "blocked_query_count",
    "successful_query_count",
    "direct_probe_count",
    "candidate_count",
    "official_candidate_count",
    "low_signal_candidate_count",
    "best_candidate_status",
    "best_candidate_url",
    "best_candidate_title",
    "best_candidate_domain",
    "best_candidate_confidence",
    "best_candidate_http_status",
    "best_candidate_features",
    "reviewer_decision_key",
    "reviewer_dossier_key",
    "reviewer_queue_status",
    "reviewer_decision_status",
    "profile_fingerprint",
    "target_artifact",
    "required_next_evidence",
    "recommended_operator_action",
    "manual_decision_template_json",
    "query_status_counts_json",
    "candidate_status_counts_json",
    "sample_queries_json",
    "candidate_evidence_json",
    "reviewer_dossier_json",
    "acceptance_boundary",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {
        row["profile_discovery_packet_key"]: row
        for row in read_csv(CSV_PATH)
        if row.get("profile_discovery_packet_key")
    }


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["profile_discovery_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def packet_key(batch_key: str, workbench_key: str) -> str:
    return "official_profile_discovery_batch_packet_" + sha256_text(f"{batch_key}|{workbench_key}")[:20]


def packet_status(workbench: dict, dossier: dict) -> str:
    lane = workbench.get("discovery_lane") or ""
    if lane == "review_official_profile_candidate":
        if dossier:
            return "ready_for_profile_candidate_reviewer_decision"
        return "missing_profile_reviewer_decision_dossier"
    return {
        "planned_search_not_executed": "ready_for_profile_search_execution",
        "search_endpoint_blocked_retry": "retry_search_endpoint_before_absence_inference",
        "direct_probe_low_signal_review": "ready_for_direct_probe_review",
        "low_signal_candidate_review": "ready_for_low_signal_candidate_review",
        "no_candidate_after_search": "ready_for_discovery_strategy_review",
    }.get(lane, "profile_discovery_packet_ready")


def support_status(workbench: dict, dossier: dict) -> str:
    lane = workbench.get("discovery_lane") or ""
    if lane == "review_official_profile_candidate":
        if not dossier:
            return "blocked_missing_reviewer_dossier"
        if dossier.get("decision_status") == "pending_reviewer_decision":
            return "ready_for_profile_reviewer_decision"
        return dossier.get("decision_status") or "profile_reviewer_decision_status_unknown"
    if lane == "planned_search_not_executed":
        return "ready_for_search_execution"
    if lane == "search_endpoint_blocked_retry":
        return "ready_for_search_retry_or_direct_probe"
    if lane == "direct_probe_low_signal_review":
        return "ready_for_direct_probe_review"
    if lane == "low_signal_candidate_review":
        return "ready_for_low_signal_candidate_review"
    if lane == "no_candidate_after_search":
        return "ready_for_discovery_strategy_review"
    return "ready_for_profile_discovery_review"


def target_artifact(workbench: dict) -> str:
    if workbench.get("discovery_lane") == "review_official_profile_candidate":
        return "artifacts/data/official_profile_reviewer_decisions.csv"
    return "artifacts/data/trainee_profile_discovery_candidates.csv"


def recommended_operator_action(workbench: dict, dossier: dict) -> str:
    lane = workbench.get("discovery_lane") or ""
    if lane == "review_official_profile_candidate":
        return dossier.get("recommended_next_action") or "record_official_profile_reviewer_decision_with_current_fingerprint"
    return workbench.get("recommended_next_action") or "execute_profile_discovery_packet"


def manual_template(dossier: dict) -> dict:
    template = parse_json(dossier.get("manual_decision_template_json"), {})
    return template if isinstance(template, dict) else {}


def reviewer_dossier_payload(dossier: dict) -> dict:
    if not dossier:
        return {}
    return {
        "dossier_key": dossier.get("dossier_key"),
        "reviewer_decision_key": dossier.get("reviewer_decision_key"),
        "candidate_url": dossier.get("candidate_url"),
        "candidate_title": dossier.get("candidate_title"),
        "candidate_domain": dossier.get("candidate_domain"),
        "candidate_confidence": dossier.get("candidate_confidence"),
        "queue_status": dossier.get("queue_status"),
        "decision_status": dossier.get("decision_status"),
        "decision_blocker": dossier.get("decision_blocker"),
        "required_reviewer_action": dossier.get("required_reviewer_action"),
        "display_safety_status": dossier.get("display_safety_status"),
        "profile_fingerprint": dossier.get("profile_fingerprint"),
    }


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    batches = sqlite_rows(conn, "SELECT * FROM official_profile_discovery_batches ORDER BY execution_order")
    workbench_by_key = {
        row["profile_workbench_key"]: row
        for row in sqlite_rows(conn, "SELECT * FROM official_profile_discovery_workbench")
    }
    dossiers_by_workbench = {
        row["profile_workbench_key"]: row
        for row in sqlite_rows(conn, "SELECT * FROM official_profile_reviewer_decision_dossiers")
    }

    rows = []
    for batch in batches:
        evidence = parse_json(batch.get("evidence_json"), {})
        workbench_keys = evidence.get("profile_workbench_keys") if isinstance(evidence, dict) else []
        if not isinstance(workbench_keys, list):
            workbench_keys = []
        for index, workbench_key in enumerate(workbench_keys, start=1):
            workbench = workbench_by_key.get(str(workbench_key), {})
            if not workbench:
                continue
            dossier = dossiers_by_workbench.get(str(workbench_key), {})
            status = packet_status(workbench, dossier)
            support = support_status(workbench, dossier)
            row = {
                "profile_discovery_packet_key": packet_key(
                    batch["official_profile_discovery_batch_key"],
                    str(workbench_key),
                ),
                "official_profile_discovery_batch_key": batch["official_profile_discovery_batch_key"],
                "execution_order": as_int(batch.get("execution_order")),
                "batch_packet_order": index,
                "profile_workbench_key": str(workbench_key),
                "person_key": workbench.get("person_key") or "",
                "display_name": workbench.get("display_name") or "",
                "role": workbench.get("role") or "",
                "program_name": workbench.get("program_name") or "",
                "task_key": workbench.get("task_key") or "",
                "discovery_lane": workbench.get("discovery_lane") or "",
                "batch_status": batch.get("batch_status") or "",
                "profile_gap_status": workbench.get("profile_gap_status") or "",
                "packet_status": status,
                "support_status": support,
                "discovery_priority": as_int(workbench.get("discovery_priority")),
                "query_count": as_int(workbench.get("query_count")),
                "observed_query_count": as_int(workbench.get("observed_query_count")),
                "unsearched_query_count": as_int(workbench.get("unsearched_query_count")),
                "blocked_query_count": as_int(workbench.get("blocked_query_count")),
                "successful_query_count": as_int(workbench.get("successful_query_count")),
                "direct_probe_count": as_int(workbench.get("direct_probe_count")),
                "candidate_count": as_int(workbench.get("candidate_count")),
                "official_candidate_count": as_int(workbench.get("official_candidate_count")),
                "low_signal_candidate_count": as_int(workbench.get("low_signal_candidate_count")),
                "best_candidate_status": workbench.get("best_candidate_status") or "",
                "best_candidate_url": workbench.get("best_candidate_url") or "",
                "best_candidate_title": workbench.get("best_candidate_title") or "",
                "best_candidate_domain": workbench.get("best_candidate_domain") or "",
                "best_candidate_confidence": round(as_float(workbench.get("best_candidate_confidence")), 3),
                "best_candidate_http_status": as_int(workbench.get("best_candidate_http_status")),
                "best_candidate_features": workbench.get("best_candidate_features") or "",
                "reviewer_decision_key": dossier.get("reviewer_decision_key") or "",
                "reviewer_dossier_key": dossier.get("dossier_key") or "",
                "reviewer_queue_status": dossier.get("queue_status") or "",
                "reviewer_decision_status": dossier.get("decision_status") or "",
                "profile_fingerprint": dossier.get("profile_fingerprint") or "",
                "target_artifact": target_artifact(workbench),
                "required_next_evidence": workbench.get("evidence_required") or batch.get("required_next_evidence") or "",
                "recommended_operator_action": recommended_operator_action(workbench, dossier),
                "manual_decision_template_json": dumps(manual_template(dossier)),
                "query_status_counts_json": workbench.get("query_status_counts_json") or "{}",
                "candidate_status_counts_json": workbench.get("candidate_status_counts_json") or "{}",
                "sample_queries_json": workbench.get("sample_queries_json") or "[]",
                "candidate_evidence_json": workbench.get("candidate_evidence_json") or "[]",
                "reviewer_dossier_json": dumps(reviewer_dossier_payload(dossier)),
                "acceptance_boundary": (
                    "Profile discovery batch packets are non-mutating. A candidate URL becomes an accepted official "
                    "profile fact only through official_profile_reviewer_decisions.csv with a matching profile_fingerprint "
                    "and acceptance audit confirmation."
                ),
                "evidence_json": dumps(
                    {
                        "derived_from": [
                            "official_profile_discovery_batches",
                            "official_profile_discovery_workbench",
                            "official_profile_reviewer_decision_dossiers",
                        ],
                        "official_profile_discovery_batch_key": batch.get("official_profile_discovery_batch_key"),
                        "profile_workbench_key": str(workbench_key),
                        "reviewer_decision_key": dossier.get("reviewer_decision_key") or "",
                        "policy": {
                            "non_mutating": True,
                            "search_hits_are_candidate_only": True,
                            "accepted_profile_url_requires_matching_profile_fingerprint": True,
                        },
                    }
                ),
                "generated_at": "",
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            rows.append({field: row[field] for field in FIELDS})
    rows.sort(
        key=lambda item: (
            as_int(item["execution_order"]),
            as_int(item["batch_packet_order"]),
            -as_int(item["discovery_priority"]),
            item["display_name"],
        )
    )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_profile_discovery_batch_packets")
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO official_profile_discovery_batch_packets ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "person_count": len({row["person_key"] for row in rows if row["person_key"]}),
        "query_count": sum(as_int(row["query_count"]) for row in rows),
        "unsearched_query_count": sum(as_int(row["unsearched_query_count"]) for row in rows),
        "blocked_query_count": sum(as_int(row["blocked_query_count"]) for row in rows),
        "candidate_count": sum(as_int(row["candidate_count"]) for row in rows),
        "official_candidate_count": sum(as_int(row["official_candidate_count"]) for row in rows),
        "reviewer_dossier_packet_rows": sum(1 for row in rows if row["reviewer_dossier_key"]),
        "by_discovery_lane": dict(sorted(Counter(row["discovery_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "policy": "Official profile discovery batch packets are non-mutating support rows over profile-gap workbench batches; accepted profile facts require reviewer decisions and acceptance audits.",
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = build_rows(conn, generated_at)
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"official_profile_discovery_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
