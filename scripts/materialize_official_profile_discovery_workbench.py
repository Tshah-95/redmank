#!/usr/bin/env python3
"""Materialize person-level workbench rows for official trainee profile discovery."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "official_profile_discovery_workbench.csv"
JSON_PATH = ARTIFACTS / "official_profile_discovery_workbench.json"
SUMMARY_PATH = ARTIFACTS / "official_profile_discovery_workbench_summary.json"

FIELDS = [
    "profile_workbench_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "task_key",
    "current_profile_url",
    "profile_gap_status",
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
    "discovery_lane",
    "discovery_priority",
    "evidence_required",
    "recommended_next_action",
    "source_domains",
    "query_status_counts_json",
    "candidate_status_counts_json",
    "sample_queries_json",
    "candidate_evidence_json",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key_for(person_key: str, task_key: str) -> str:
    return "official_profile_workbench_" + sha256_text(dumps([person_key, task_key]))[:20]


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def load_tasks(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT q.*, p.profile_url AS current_profile_url
            FROM person_enrichment_work_queue q
            LEFT JOIN people p ON p.person_key = q.person_key
            WHERE q.task_type = 'official_profile_search'
            ORDER BY q.role, q.display_name, q.program_name, q.task_key
            """
        )
    ]


def load_queries(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT q.*, o.searched_at, o.search_http_status, o.result_count, o.error
            FROM trainee_profile_search_queries q
            LEFT JOIN trainee_profile_search_observations o ON o.query_key = q.query_key
            ORDER BY q.person_key, q.priority DESC, q.query_kind, q.query_key
            """
        )
    ]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row.get("task_key") or ""].append(row)
    return grouped


def load_candidates(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM trainee_profile_discovery_candidates
            ORDER BY person_key, priority DESC, confidence DESC, candidate_status, result_rank
            """
        )
    ]
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row.get("task_key") or ""].append(row)
    return grouped


def query_status(row: dict) -> str:
    if not row.get("searched_at"):
        return "planned_not_executed"
    status = as_int(row.get("search_http_status"))
    if status == 200 and as_int(row.get("result_count")) > 0:
        return "executed_success_with_results"
    if status == 200:
        return "executed_success_no_results"
    if status:
        return "executed_blocked_by_search_endpoint"
    return "executed_unknown_status"


def best_candidate(candidates: list[dict]) -> dict:
    if not candidates:
        return {}
    return sorted(
        candidates,
        key=lambda item: (
            item.get("candidate_status") != "official_profile_candidate",
            -as_float(item.get("confidence")),
            -as_int(item.get("priority")),
            as_int(item.get("result_rank")),
            item.get("candidate_url") or "",
        ),
    )[0]


def discovery_lane(task: dict, queries: list[dict], candidates: list[dict], official_count: int, blocked_count: int) -> str:
    if task.get("current_profile_url"):
        return "already_has_profile_url_monitor"
    if official_count:
        return "review_official_profile_candidate"
    if any((candidate.get("query_kind") or "").startswith("direct_") for candidate in candidates):
        return "direct_probe_low_signal_review"
    if blocked_count and blocked_count >= max(1, len(queries) - blocked_count):
        return "search_endpoint_blocked_retry"
    if queries and all(query_status(query) == "planned_not_executed" for query in queries):
        return "planned_search_not_executed"
    if candidates:
        return "low_signal_candidate_review"
    return "no_candidate_after_search"


def recommended_action(lane: str) -> str:
    return {
        "already_has_profile_url_monitor": "retain_existing_profile_url_and_monitor_future_refresh",
        "review_official_profile_candidate": "review_candidate_for_same_person_official_profile_acceptance",
        "direct_probe_low_signal_review": "review_direct_probe_results_or_expand_slug_patterns",
        "search_endpoint_blocked_retry": "retry_profile_search_with_reliable_search_provider_or_direct_probe",
        "planned_search_not_executed": "execute_profile_search_or_direct_roster_sibling_probe",
        "low_signal_candidate_review": "review_low_signal_profile_candidates_or_collect_stronger_official_source",
        "no_candidate_after_search": "expand_profile_discovery_strategy_or_mark_no_public_profile_candidate",
    }.get(lane, "review_profile_discovery_status")


def evidence_required(lane: str) -> str:
    if lane == "review_official_profile_candidate":
        return "Official-domain profile candidate with same-person name, program/department or roster-linked context, URL, content hash, and reviewer/profile acceptance gate."
    if lane == "already_has_profile_url_monitor":
        return "Existing profile URL remains provenance context; refresh only if source hash or displayed role changes."
    if lane == "search_endpoint_blocked_retry":
        return "Fresh successful search observation or deterministic official-domain direct probe before concluding no public profile exists."
    return "Official Penn/Penn Medicine/CHOP profile or roster-linked profile evidence; search hits remain candidate-only until source ownership and identity anchors are confirmed."


def build_rows(tasks: list[dict], queries_by_task: dict[str, list[dict]], candidates_by_task: dict[str, list[dict]], generated_at: str) -> list[dict]:
    rows = []
    for task in tasks:
        task_key = task.get("task_key") or ""
        queries = queries_by_task.get(task_key, [])
        candidates = candidates_by_task.get(task_key, [])
        query_counts = Counter(query_status(query) for query in queries)
        candidate_counts = Counter(candidate.get("candidate_status") or "" for candidate in candidates)
        official_count = candidate_counts.get("official_profile_candidate", 0)
        low_signal_count = candidate_counts.get("low_signal_search_result", 0)
        blocked_count = query_counts.get("executed_blocked_by_search_endpoint", 0)
        successful_count = query_counts.get("executed_success_with_results", 0) + query_counts.get(
            "executed_success_no_results", 0
        )
        direct_probe_count = sum(1 for query in queries if (query.get("query_kind") or "").startswith("direct_"))
        best = best_candidate(candidates)
        lane = discovery_lane(task, queries, candidates, official_count, blocked_count)
        priority = as_int(task.get("priority")) * 10
        if lane == "review_official_profile_candidate":
            priority += 120
        elif lane == "search_endpoint_blocked_retry":
            priority += 70
        elif lane == "planned_search_not_executed":
            priority += 55
        elif lane == "low_signal_candidate_review":
            priority += 35
        elif lane == "already_has_profile_url_monitor":
            priority -= 150
        domains = sorted({candidate.get("result_domain") or "" for candidate in candidates if candidate.get("result_domain")})
        sample_queries = [
            {
                "query_key": query.get("query_key"),
                "query_kind": query.get("query_kind"),
                "query": query.get("query"),
                "query_status": query_status(query),
                "search_http_status": query.get("search_http_status"),
                "result_count": query.get("result_count"),
                "error": query.get("error"),
            }
            for query in queries[:6]
        ]
        candidate_evidence = [
            {
                "candidate_key": candidate.get("candidate_key"),
                "candidate_status": candidate.get("candidate_status"),
                "confidence": candidate.get("confidence"),
                "candidate_title": candidate.get("candidate_title"),
                "candidate_url": candidate.get("candidate_url"),
                "result_domain": candidate.get("result_domain"),
                "http_status": candidate.get("http_status"),
                "match_features_json": candidate.get("match_features_json"),
                "required_next_evidence": candidate.get("required_next_evidence"),
            }
            for candidate in candidates[:8]
        ]
        evidence = {
            "task": {
                "task_key": task_key,
                "person_key": task.get("person_key"),
                "display_name": task.get("display_name"),
                "role": task.get("role"),
                "program_name": task.get("program_name"),
                "priority_band": task.get("priority_band"),
            },
            "policy": {
                "non_mutating": True,
                "profile_candidate_acceptance": "Profile candidates do not mutate people.profile_url without official-source ownership and same-person/current-context review.",
            },
        }
        rows.append(
            {
                "profile_workbench_key": key_for(task.get("person_key") or "", task_key),
                "person_key": task.get("person_key") or "",
                "display_name": task.get("display_name") or "",
                "role": task.get("role") or "",
                "program_name": task.get("program_name") or "",
                "task_key": task_key,
                "current_profile_url": task.get("current_profile_url") or "",
                "profile_gap_status": "has_profile_url" if task.get("current_profile_url") else "missing_profile_url",
                "query_count": len(queries),
                "observed_query_count": len(queries) - query_counts.get("planned_not_executed", 0),
                "unsearched_query_count": query_counts.get("planned_not_executed", 0),
                "blocked_query_count": blocked_count,
                "successful_query_count": successful_count,
                "direct_probe_count": direct_probe_count,
                "candidate_count": len(candidates),
                "official_candidate_count": official_count,
                "low_signal_candidate_count": low_signal_count,
                "best_candidate_status": best.get("candidate_status") or "",
                "best_candidate_url": best.get("candidate_url") or "",
                "best_candidate_title": best.get("candidate_title") or "",
                "best_candidate_domain": best.get("result_domain") or "",
                "best_candidate_confidence": as_float(best.get("confidence")),
                "best_candidate_http_status": as_int(best.get("http_status")),
                "best_candidate_features": best.get("match_features_json") or "",
                "discovery_lane": lane,
                "discovery_priority": priority,
                "evidence_required": evidence_required(lane),
                "recommended_next_action": recommended_action(lane),
                "source_domains": "; ".join(domains),
                "query_status_counts_json": dumps(dict(sorted(query_counts.items()))),
                "candidate_status_counts_json": dumps(dict(sorted(candidate_counts.items()))),
                "sample_queries_json": dumps(sample_queries),
                "candidate_evidence_json": dumps(candidate_evidence),
                "evidence_json": dumps(evidence),
                "generated_at": generated_at,
            }
        )
    return sorted(rows, key=lambda item: (-as_int(item["discovery_priority"]), item["display_name"], item["task_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_profile_discovery_workbench")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO official_profile_discovery_workbench ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_lane = Counter(row["discovery_lane"] for row in rows)
    by_role_lane = Counter(f"{row['role']}:{row['discovery_lane']}" for row in rows)
    payload = {
        "generated_at": generated_at,
        "workbench_rows": len(rows),
        "person_count": len({row["person_key"] for row in rows}),
        "program_count": len({row["program_name"] for row in rows}),
        "query_count": sum(as_int(row["query_count"]) for row in rows),
        "observed_query_count": sum(as_int(row["observed_query_count"]) for row in rows),
        "unsearched_query_count": sum(as_int(row["unsearched_query_count"]) for row in rows),
        "blocked_query_count": sum(as_int(row["blocked_query_count"]) for row in rows),
        "candidate_count": sum(as_int(row["candidate_count"]) for row in rows),
        "official_candidate_count": sum(as_int(row["official_candidate_count"]) for row in rows),
        "by_discovery_lane": dict(sorted(by_lane.items())),
        "by_role_and_discovery_lane": dict(sorted(by_role_lane.items())),
        "top_profile_workbench_rows": [
            {
                "display_name": row["display_name"],
                "role": row["role"],
                "program_name": row["program_name"],
                "discovery_lane": row["discovery_lane"],
                "discovery_priority": row["discovery_priority"],
                "query_count": row["query_count"],
                "candidate_count": row["candidate_count"],
                "official_candidate_count": row["official_candidate_count"],
                "best_candidate_url": row["best_candidate_url"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:25]
        ],
        "policy": (
            "This artifact is non-mutating. It turns official-profile enrichment gaps into person-level discovery "
            "work, preserving query, search observation, direct-probe, and candidate provenance before any profile URL is accepted."
        ),
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
    rows = build_rows(load_tasks(conn), load_queries(conn), load_candidates(conn), generated_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"profile_workbench_rows": len(rows), "query_count": sum(as_int(row["query_count"]) for row in rows)}))


if __name__ == "__main__":
    main()
