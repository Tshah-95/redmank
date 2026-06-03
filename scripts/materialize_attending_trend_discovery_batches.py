#!/usr/bin/env python3
"""Materialize bounded operator batches for attending trend discovery rows."""

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

CSV_PATH = ARTIFACTS / "attending_trend_discovery_batches.csv"
JSON_PATH = ARTIFACTS / "attending_trend_discovery_batches.json"
SUMMARY_PATH = ARTIFACTS / "attending_trend_discovery_batch_summary.json"

MAX_WORKBENCH_ROWS_PER_BATCH = 25

FIELDS = [
    "attending_trend_discovery_batch_key",
    "execution_order",
    "discovery_lane",
    "trend_status",
    "ten_year_trend_window",
    "batch_status",
    "ready_to_execute",
    "candidate_status_signature",
    "workbench_count",
    "person_count",
    "current_endpoint_count",
    "penn_training_claim_count",
    "recent_dated_bridge_count",
    "accepted_trend_fact_count",
    "review_claim_count",
    "reviewer_queue_count",
    "historical_query_count",
    "historical_search_observation_count",
    "historical_blocked_search_count",
    "historical_candidate_count",
    "actionable_historical_candidate_count",
    "current_profile_context_candidate_count",
    "max_discovery_priority",
    "min_discovery_priority",
    "top_display_names",
    "top_candidate_domains",
    "query_status_counts_json",
    "candidate_status_counts_json",
    "recommended_operator_action",
    "execution_instructions",
    "required_next_evidence",
    "target_artifact",
    "top_workbench_rows_json",
    "evidence_json",
    "generated_at",
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


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def load_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["attending_trend_discovery_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["attending_trend_discovery_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def batch_key(parts: tuple[object, ...]) -> str:
    return "attending_trend_discovery_batch_" + sha256_text(dumps(parts))[:20]


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def dominant_signature(json_value: str | None, default: str) -> str:
    counts = load_json(json_value, {})
    if not isinstance(counts, dict) or not counts:
        return default
    key, _ = sorted(counts.items(), key=lambda item: (-as_int(item[1]), str(item[0])))[0]
    return str(key)


def combined_counts(rows: list[dict], field: str) -> dict:
    counts: Counter = Counter()
    for row in rows:
        values = load_json(row.get(field), {})
        if isinstance(values, dict):
            for key, value in values.items():
                counts[str(key)] += as_int(value)
    return dict(sorted(counts.items()))


def batch_status(lane: str) -> str:
    return {
        "accepted_trend_fact_monitor": "accepted_trend_monitor_ready",
        "reviewer_decision_pending": "trend_reviewer_decision_ready",
        "historical_link_candidate_review": "historical_link_review_ready",
        "profile_claim_needs_dated_bridge_search": "dated_bridge_search_ready",
        "historical_search_endpoint_blocked_retry": "historical_search_retry_required",
        "current_endpoint_query_plan_missing": "query_plan_materialization_required",
        "current_endpoint_training_bridge_search": "training_bridge_search_ready",
        "current_endpoint_context_candidate_review": "context_candidate_review_ready",
        "context_only_monitor": "context_monitor_ready",
    }.get(lane, "attending_trend_discovery_ready")


def recommended_action(lane: str) -> str:
    return {
        "accepted_trend_fact_monitor": "monitor_accepted_trend_fact_batch",
        "reviewer_decision_pending": "record_attending_trend_reviewer_decision_batch",
        "historical_link_candidate_review": "review_historical_link_candidate_batch",
        "profile_claim_needs_dated_bridge_search": "run_dated_bridge_search_batch",
        "historical_search_endpoint_blocked_retry": "retry_historical_link_search_or_direct_probe_batch",
        "current_endpoint_query_plan_missing": "materialize_missing_historical_link_query_plan_batch",
        "current_endpoint_training_bridge_search": "collect_dated_training_bridge_batch",
        "current_endpoint_context_candidate_review": "review_context_candidates_then_collect_bridge_batch",
        "context_only_monitor": "monitor_context_only_attending_groups",
    }.get(lane, "review_attending_trend_discovery_batch")


def execution_instructions(lane: str) -> str:
    if lane == "reviewer_decision_pending":
        return "Record reviewer decisions only after confirming same-person identity, current Penn endpoint, Penn training line, program type, and dates against the current claim fingerprint."
    if lane == "historical_link_candidate_review":
        return "Review candidate pages for same-person identity, dated Penn residency/fellowship/internship evidence, and consistency with the current attending endpoint."
    if lane == "current_endpoint_training_bridge_search":
        return "Search official biosketch, CV, alumni, and historical roster sources for dated Penn training evidence; endpoint-only evidence is not a trend fact."
    if lane == "historical_search_endpoint_blocked_retry":
        return "Retry with a reliable search provider or deterministic official-domain probe path; blocked endpoint behavior is source-quality evidence, not absence evidence."
    if lane == "accepted_trend_fact_monitor":
        return "Retain accepted trend facts and monitor future endpoint or source-refresh drift without reaccepting facts."
    if lane == "context_only_monitor":
        return "Keep context-only rows out of trend counts until a current endpoint and dated Penn-training bridge are found."
    return "Work the batch through discovery, reviewer, and accepted-fact ledgers without mutating trainee roster truth."


def required_next_evidence(rows: list[dict], lane: str) -> str:
    evidence = Counter(row.get("evidence_required") or "" for row in rows)
    if evidence:
        return evidence.most_common(1)[0][0]
    if lane == "current_endpoint_training_bridge_search":
        return "Dated Penn residency, fellowship, internship, or alumni bridge evidence tied to the current attending endpoint."
    return "Current endpoint plus dated Penn-training bridge evidence before trend acceptance."


def target_artifact(lane: str) -> str:
    if lane == "reviewer_decision_pending":
        return "artifacts/data/attending_trend_reviewer_decisions.csv"
    if lane in {
        "historical_link_candidate_review",
        "current_endpoint_training_bridge_search",
        "profile_claim_needs_dated_bridge_search",
        "current_endpoint_context_candidate_review",
    }:
        return "artifacts/data/attending_historical_link_candidates.csv"
    if lane in {"historical_search_endpoint_blocked_retry", "current_endpoint_query_plan_missing"}:
        return "artifacts/data/attending_historical_link_search_observations.csv"
    return "artifacts/data/attending_trend_discovery_workbench.csv"


def compact_candidate_domains(rows: list[dict], limit: int = 10) -> str:
    counts = Counter(row.get("best_candidate_domain") or "" for row in rows if row.get("best_candidate_domain"))
    return "; ".join(f"{domain}:{count}" for domain, count in counts.most_common(limit))


def top_workbench_rows(rows: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("discovery_priority")), item.get("display_name") or ""))[
        :limit
    ]:
        output.append(
            {
                "trend_workbench_key": row.get("trend_workbench_key"),
                "trend_key": row.get("trend_key"),
                "event_group_key": row.get("event_group_key"),
                "display_name": row.get("display_name"),
                "trend_status": row.get("trend_status"),
                "ten_year_trend_window": row.get("ten_year_trend_window"),
                "discovery_priority": as_int(row.get("discovery_priority")),
                "historical_query_count": as_int(row.get("historical_query_count")),
                "historical_candidate_count": as_int(row.get("historical_candidate_count")),
                "best_candidate_status": row.get("best_candidate_status") or "",
                "best_candidate_url": row.get("best_candidate_url") or "",
                "best_candidate_confidence": as_float(row.get("best_candidate_confidence")),
            }
        )
    return output


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    workbench_rows = sqlite_rows(
        conn,
        """
        SELECT *
        FROM attending_trend_discovery_workbench
        ORDER BY discovery_priority DESC, display_name, trend_workbench_key
        """,
    )
    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in workbench_rows:
        grouped[
            (
                row.get("discovery_lane") or "",
                row.get("trend_status") or "",
                row.get("ten_year_trend_window") or "unknown",
                dominant_signature(row.get("candidate_status_counts_json"), "no_candidate_status"),
            )
        ].append(row)

    output = []
    for (lane, trend_status, window, candidate_signature), rows in grouped.items():
        rows = sorted(rows, key=lambda item: (-as_int(item.get("discovery_priority")), item.get("display_name") or ""))
        for chunk_index, offset in enumerate(range(0, len(rows), MAX_WORKBENCH_ROWS_PER_BATCH), start=1):
            chunk = rows[offset : offset + MAX_WORKBENCH_ROWS_PER_BATCH]
            priorities = [as_int(item.get("discovery_priority")) for item in chunk]
            keys = [item.get("trend_workbench_key") for item in chunk]
            query_counts = combined_counts(chunk, "query_status_counts_json")
            candidate_counts = combined_counts(chunk, "candidate_status_counts_json")
            status = batch_status(lane)
            row = {
                "attending_trend_discovery_batch_key": batch_key(
                    (lane, trend_status, window, candidate_signature, chunk_index, keys)
                ),
                "execution_order": 0,
                "discovery_lane": lane,
                "trend_status": trend_status,
                "ten_year_trend_window": window,
                "batch_status": status,
                "ready_to_execute": 1,
                "candidate_status_signature": candidate_signature,
                "workbench_count": len(chunk),
                "person_count": len({item.get("trend_key") or item.get("display_name") for item in chunk}),
                "current_endpoint_count": sum(as_int(item.get("has_current_attending_endpoint")) for item in chunk),
                "penn_training_claim_count": sum(as_int(item.get("has_penn_training_claim")) for item in chunk),
                "recent_dated_bridge_count": sum(as_int(item.get("has_recent_dated_biosketch_bridge")) for item in chunk),
                "accepted_trend_fact_count": sum(as_int(item.get("accepted_trend_fact_count")) for item in chunk),
                "review_claim_count": sum(as_int(item.get("review_claim_count")) for item in chunk),
                "reviewer_queue_count": sum(as_int(item.get("reviewer_queue_count")) for item in chunk),
                "historical_query_count": sum(as_int(item.get("historical_query_count")) for item in chunk),
                "historical_search_observation_count": sum(
                    as_int(item.get("historical_search_observation_count")) for item in chunk
                ),
                "historical_blocked_search_count": sum(
                    as_int(item.get("historical_blocked_search_count")) for item in chunk
                ),
                "historical_candidate_count": sum(as_int(item.get("historical_candidate_count")) for item in chunk),
                "actionable_historical_candidate_count": sum(
                    as_int(item.get("actionable_historical_candidate_count")) for item in chunk
                ),
                "current_profile_context_candidate_count": sum(
                    as_int(item.get("current_profile_context_candidate_count")) for item in chunk
                ),
                "max_discovery_priority": max(priorities) if priorities else 0,
                "min_discovery_priority": min(priorities) if priorities else 0,
                "top_display_names": "; ".join(item.get("display_name") or "" for item in chunk[:12]),
                "top_candidate_domains": compact_candidate_domains(chunk),
                "query_status_counts_json": dumps(query_counts),
                "candidate_status_counts_json": dumps(candidate_counts),
                "recommended_operator_action": recommended_action(lane),
                "execution_instructions": execution_instructions(lane),
                "required_next_evidence": required_next_evidence(chunk, lane),
                "target_artifact": target_artifact(lane),
                "top_workbench_rows_json": dumps(top_workbench_rows(chunk)),
                "evidence_json": dumps(
                    {
                        "trend_workbench_keys": keys,
                        "query_status_counts": query_counts,
                        "candidate_status_counts": candidate_counts,
                        "top_workbench_rows": top_workbench_rows(chunk),
                        "policy": {
                            "non_mutating": True,
                            "endpoint_only_rows_do_not_count_as_trend_facts": True,
                            "accepted_trend_fact_requires": [
                                "attending_trend_reviewer_decisions.csv row",
                                "matching claim_fingerprint",
                                "same-person current Penn endpoint confirmation",
                                "dated Penn training bridge confirmation",
                                "attending_trend_acceptance_audit acceptance",
                            ],
                        },
                    }
                ),
                "generated_at": generated_at,
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            output.append({field: row[field] for field in FIELDS})

    output.sort(
        key=lambda item: (
            -as_int(item["max_discovery_priority"]),
            item["discovery_lane"],
            item["trend_status"],
            item["attending_trend_discovery_batch_key"],
        )
    )
    for index, row in enumerate(output, start=1):
        row["execution_order"] = index
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM attending_trend_discovery_batches")
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO attending_trend_discovery_batches ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "workbench_count": sum(as_int(row["workbench_count"]) for row in rows),
        "person_count": sum(as_int(row["person_count"]) for row in rows),
        "current_endpoint_count": sum(as_int(row["current_endpoint_count"]) for row in rows),
        "penn_training_claim_count": sum(as_int(row["penn_training_claim_count"]) for row in rows),
        "review_claim_count": sum(as_int(row["review_claim_count"]) for row in rows),
        "accepted_trend_fact_count": sum(as_int(row["accepted_trend_fact_count"]) for row in rows),
        "historical_query_count": sum(as_int(row["historical_query_count"]) for row in rows),
        "historical_candidate_count": sum(as_int(row["historical_candidate_count"]) for row in rows),
        "actionable_historical_candidate_count": sum(
            as_int(row["actionable_historical_candidate_count"]) for row in rows
        ),
        "by_discovery_lane": dict(sorted(Counter(row["discovery_lane"] for row in rows).items())),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_ten_year_trend_window": dict(sorted(Counter(row["ten_year_trend_window"] for row in rows).items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "discovery_lane": row["discovery_lane"],
                "trend_status": row["trend_status"],
                "ten_year_trend_window": row["ten_year_trend_window"],
                "batch_status": row["batch_status"],
                "workbench_count": row["workbench_count"],
                "historical_query_count": row["historical_query_count"],
                "historical_candidate_count": row["historical_candidate_count"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Trend discovery batches are non-mutating operator sessions. Accepted recent-attending trend facts still require explicit reviewer decisions and acceptance audit pass.",
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
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"attending_trend_discovery_batches": len(rows)}))


if __name__ == "__main__":
    main()
