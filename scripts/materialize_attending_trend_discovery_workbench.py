#!/usr/bin/env python3
"""Materialize attending trend discovery and review workbench rows."""

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

CSV_PATH = ARTIFACTS / "attending_trend_discovery_workbench.csv"
JSON_PATH = ARTIFACTS / "attending_trend_discovery_workbench.json"
SUMMARY_PATH = ARTIFACTS / "attending_trend_discovery_workbench_summary.json"

DOSSIERS_CSV = ARTIFACTS / "attending_trend_dossiers.csv"
QUERY_CSV = ARTIFACTS / "attending_historical_link_search_queries.csv"
OBSERVATION_CSV = ARTIFACTS / "attending_historical_link_search_observations.csv"
CANDIDATE_CSV = ARTIFACTS / "attending_historical_link_candidates.csv"

csv.field_size_limit(sys.maxsize)

ACTIONABLE_HISTORICAL_STATUSES = {
    "historical_link_source_candidate",
    "historical_roster_or_alumni_candidate",
    "historical_roster_or_alumni_bridge_candidate",
    "historical_training_search_candidate",
    "identity_bridge_candidate",
    "profile_or_cv_candidate",
    "profile_or_cv_bridge_candidate",
}

CURRENT_CONTEXT_STATUSES = {
    "current_profile_context_candidate",
    "current_profile_training_context_candidate",
    "profile_identity_anchor_candidate",
}

FIELDS = [
    "trend_workbench_key",
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "trend_status",
    "dossier_status",
    "ten_year_trend_window",
    "has_current_attending_endpoint",
    "has_penn_training_claim",
    "has_recent_dated_biosketch_bridge",
    "has_historical_link_candidate",
    "accepted_trend_fact_count",
    "review_claim_count",
    "reviewer_queue_count",
    "historical_query_count",
    "historical_search_observation_count",
    "historical_blocked_search_count",
    "historical_candidate_count",
    "actionable_historical_candidate_count",
    "current_profile_context_candidate_count",
    "best_candidate_status",
    "best_candidate_url",
    "best_candidate_domain",
    "best_candidate_title",
    "best_candidate_confidence",
    "best_candidate_priority",
    "discovery_lane",
    "discovery_priority",
    "evidence_required",
    "recommended_next_action",
    "source_urls",
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


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["trend_workbench_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["trend_workbench_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def key_for(trend_key: str, event_group_key: str) -> str:
    return "attending_trend_workbench_" + sha256_text(dumps([trend_key, event_group_key]))[:20]


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


def group_by(rows: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key) or ""].append(row)
    return grouped


def best_candidate(candidates: list[dict]) -> dict:
    if not candidates:
        return {}
    return sorted(
        candidates,
        key=lambda row: (
            row.get("candidate_status") not in ACTIONABLE_HISTORICAL_STATUSES,
            row.get("candidate_status") not in CURRENT_CONTEXT_STATUSES,
            -as_float(row.get("confidence")),
            -as_int(row.get("priority")),
            row.get("result_url") or "",
        ),
    )[0]


def discovery_lane(dossier: dict, queries: list[dict], observations: list[dict], candidates: list[dict]) -> str:
    if as_int(dossier.get("accepted_trend_fact_count")):
        return "accepted_trend_fact_monitor"
    if as_int(dossier.get("review_claim_count")):
        return "reviewer_decision_pending"
    if any(candidate.get("candidate_status") in ACTIONABLE_HISTORICAL_STATUSES for candidate in candidates):
        return "historical_link_candidate_review"
    if dossier.get("trend_status") == "profile_claim_still_needs_dated_bridge":
        return "profile_claim_needs_dated_bridge_search"
    if dossier.get("trend_status") == "current_endpoint_needs_training_claim":
        if not queries:
            return "current_endpoint_query_plan_missing"
        if observations and all(query_status(row) == "executed_blocked_by_search_endpoint" for row in observations):
            return "historical_search_endpoint_blocked_retry"
        if candidates:
            return "current_endpoint_context_candidate_review"
        return "current_endpoint_training_bridge_search"
    if dossier.get("trend_status") == "historical_link_candidate_review":
        return "historical_link_candidate_review"
    return "context_only_monitor"


def evidence_required(lane: str) -> str:
    if lane == "accepted_trend_fact_monitor":
        return "Retain accepted trend fact provenance and monitor future current-endpoint/training-source refreshes."
    if lane == "reviewer_decision_pending":
        return "Explicit reviewer decision confirming same-person identity, current Penn endpoint, training line, program type, and dates."
    if lane == "historical_link_candidate_review":
        return "Review candidate page for same-person identity, Penn training organization/program, dated training line, and current endpoint consistency."
    if lane == "profile_claim_needs_dated_bridge_search":
        return "Dated historical roster, alumni, CV, official biosketch, or independent profile bridge for the current attending with Penn training claim."
    if lane == "historical_search_endpoint_blocked_retry":
        return "Successful search observation or deterministic official-profile/faculty-biosketch probe before concluding no bridge exists."
    if lane == "current_endpoint_query_plan_missing":
        return "Historical-link query manifest covering current endpoint, Penn training terms, official profile, CV, alumni, and roster surfaces."
    if lane == "current_endpoint_training_bridge_search":
        return "Official profile, faculty biosketch, CV, historical roster, or alumni page with dated Penn residency/fellowship/internship evidence."
    if lane == "current_endpoint_context_candidate_review":
        return "Review context candidates, then collect dated Penn-training evidence before trend acceptance."
    return "Do not use as a trend fact until current endpoint and dated Penn-training bridge evidence exist."


def recommended_action(lane: str) -> str:
    return {
        "accepted_trend_fact_monitor": "retain_accepted_trend_fact_and_monitor_future_refresh",
        "reviewer_decision_pending": "record_attending_trend_reviewer_decision",
        "historical_link_candidate_review": "review_historical_link_for_same_person_program_and_dates",
        "profile_claim_needs_dated_bridge_search": "search_historical_roster_alumni_cv_or_biosketch_bridge",
        "historical_search_endpoint_blocked_retry": "retry_attending_historical_link_search_or_direct_official_biosketch_probe",
        "current_endpoint_query_plan_missing": "materialize_attending_historical_link_query_plan_for_endpoint",
        "current_endpoint_training_bridge_search": "collect_dated_training_claim_from_official_biosketch_cv_or_historical_roster",
        "current_endpoint_context_candidate_review": "review_context_candidates_then_collect_dated_training_bridge",
        "context_only_monitor": "retain_as_context_until_current_endpoint_or_training_bridge_appears",
    }.get(lane, "review_attending_trend_discovery_state")


def lane_priority(lane: str, dossier: dict, candidates: list[dict]) -> int:
    base = {
        "reviewer_decision_pending": 930,
        "historical_link_candidate_review": 850,
        "profile_claim_needs_dated_bridge_search": 800,
        "historical_search_endpoint_blocked_retry": 760,
        "current_endpoint_query_plan_missing": 740,
        "current_endpoint_training_bridge_search": 720,
        "current_endpoint_context_candidate_review": 700,
        "accepted_trend_fact_monitor": 260,
        "context_only_monitor": 220,
    }.get(lane, 300)
    if dossier.get("ten_year_trend_window") == "yes":
        base += 60
    if as_int(dossier.get("has_current_attending_endpoint")):
        base += 30
    if as_int(dossier.get("has_penn_training_claim")):
        base += 35
    if candidates:
        base += min(max(as_int(candidate.get("priority")) for candidate in candidates) // 4, 40)
    return base


def build_rows(generated_at: str) -> list[dict]:
    existing = read_existing()
    dossiers = read_csv(DOSSIERS_CSV)
    queries_by_group = group_by(read_csv(QUERY_CSV), "event_group_key")
    observations_by_group = group_by(read_csv(OBSERVATION_CSV), "event_group_key")
    candidates_by_group = group_by(read_csv(CANDIDATE_CSV), "event_group_key")
    rows = []
    for dossier in dossiers:
        event_group_key = dossier.get("event_group_key") or ""
        trend_key = dossier.get("trend_key") or ""
        queries = queries_by_group.get(event_group_key, [])
        observations = observations_by_group.get(event_group_key, [])
        candidates = candidates_by_group.get(event_group_key, [])
        query_counts = Counter(query_status(row) for row in observations)
        if queries and not observations:
            query_counts["planned_not_executed"] = len(queries)
        candidate_counts = Counter(candidate.get("candidate_status") or "" for candidate in candidates)
        actionable_count = sum(1 for candidate in candidates if candidate.get("candidate_status") in ACTIONABLE_HISTORICAL_STATUSES)
        context_count = sum(1 for candidate in candidates if candidate.get("candidate_status") in CURRENT_CONTEXT_STATUSES)
        best = best_candidate(candidates)
        lane = discovery_lane(dossier, queries, observations, candidates)
        source_urls = []
        if dossier.get("top_source_urls"):
            source_urls.extend(part.strip() for part in dossier["top_source_urls"].split(";") if part.strip())
        source_urls.extend(candidate.get("result_url") or "" for candidate in candidates if candidate.get("result_url"))
        source_urls = sorted({url for url in source_urls if url})
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
            for query in (observations or queries)[:8]
        ]
        candidate_evidence = [
            {
                "candidate_key": candidate.get("candidate_key"),
                "candidate_status": candidate.get("candidate_status"),
                "confidence": candidate.get("confidence"),
                "priority": candidate.get("priority"),
                "result_url": candidate.get("result_url"),
                "result_domain": candidate.get("result_domain"),
                "result_title": candidate.get("result_title"),
                "classification_reasons": candidate.get("classification_reasons"),
                "required_next_evidence": candidate.get("required_next_evidence"),
            }
            for candidate in sorted(candidates, key=lambda item: -as_int(item.get("priority")))[:10]
        ]
        evidence = {
            "dossier": dossier,
            "policy": {
                "non_mutating": True,
                "current_endpoint_alone_is_not_trend_fact": True,
                "accepted_trend_fact_requires_reviewer_decision": True,
            },
        }
        row = {
            "trend_workbench_key": key_for(trend_key, event_group_key),
            "trend_key": trend_key,
            "event_group_key": event_group_key,
            "display_name": dossier.get("display_name") or "",
            "normalized_name": dossier.get("normalized_name") or "",
            "trend_status": dossier.get("trend_status") or "",
            "dossier_status": dossier.get("dossier_status") or "",
            "ten_year_trend_window": dossier.get("ten_year_trend_window") or "unknown",
            "has_current_attending_endpoint": as_int(dossier.get("has_current_attending_endpoint")),
            "has_penn_training_claim": as_int(dossier.get("has_penn_training_claim")),
            "has_recent_dated_biosketch_bridge": as_int(dossier.get("has_recent_dated_biosketch_bridge")),
            "has_historical_link_candidate": as_int(dossier.get("has_historical_link_candidate")),
            "accepted_trend_fact_count": as_int(dossier.get("accepted_trend_fact_count")),
            "review_claim_count": as_int(dossier.get("review_claim_count")),
            "reviewer_queue_count": as_int(dossier.get("reviewer_queue_count")),
            "historical_query_count": len(queries),
            "historical_search_observation_count": len(observations),
            "historical_blocked_search_count": query_counts.get("executed_blocked_by_search_endpoint", 0),
            "historical_candidate_count": len(candidates),
            "actionable_historical_candidate_count": actionable_count,
            "current_profile_context_candidate_count": context_count,
            "best_candidate_status": best.get("candidate_status") or "",
            "best_candidate_url": best.get("result_url") or "",
            "best_candidate_domain": best.get("result_domain") or "",
            "best_candidate_title": best.get("result_title") or "",
            "best_candidate_confidence": as_float(best.get("confidence")),
            "best_candidate_priority": as_int(best.get("priority")),
            "discovery_lane": lane,
            "discovery_priority": lane_priority(lane, dossier, candidates),
            "evidence_required": evidence_required(lane),
            "recommended_next_action": recommended_action(lane),
            "source_urls": "; ".join(source_urls[:15]),
            "query_status_counts_json": dumps(dict(sorted(query_counts.items()))),
            "candidate_status_counts_json": dumps(dict(sorted(candidate_counts.items()))),
            "sample_queries_json": dumps(sample_queries),
            "candidate_evidence_json": dumps(candidate_evidence),
            "evidence_json": dumps(evidence),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        rows.append(row)
    return sorted(rows, key=lambda item: (-as_int(item["discovery_priority"]), item["display_name"], item["trend_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM attending_trend_discovery_workbench")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO attending_trend_discovery_workbench ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_lane = Counter(row["discovery_lane"] for row in rows)
    by_status = Counter(row["trend_status"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "workbench_rows": len(rows),
        "accepted_trend_fact_rows": sum(as_int(row["accepted_trend_fact_count"]) for row in rows),
        "review_claim_rows": sum(as_int(row["review_claim_count"]) for row in rows),
        "current_endpoint_rows": sum(as_int(row["has_current_attending_endpoint"]) for row in rows),
        "penn_training_claim_rows": sum(as_int(row["has_penn_training_claim"]) for row in rows),
        "historical_query_count": sum(as_int(row["historical_query_count"]) for row in rows),
        "historical_search_observation_count": sum(as_int(row["historical_search_observation_count"]) for row in rows),
        "historical_blocked_search_count": sum(as_int(row["historical_blocked_search_count"]) for row in rows),
        "historical_candidate_count": sum(as_int(row["historical_candidate_count"]) for row in rows),
        "actionable_historical_candidate_count": sum(as_int(row["actionable_historical_candidate_count"]) for row in rows),
        "by_discovery_lane": dict(sorted(by_lane.items())),
        "by_trend_status": dict(sorted(by_status.items())),
        "top_workbench_rows": [
            {
                "display_name": row["display_name"],
                "trend_status": row["trend_status"],
                "discovery_lane": row["discovery_lane"],
                "discovery_priority": row["discovery_priority"],
                "historical_query_count": row["historical_query_count"],
                "historical_candidate_count": row["historical_candidate_count"],
                "best_candidate_url": row["best_candidate_url"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:20]
        ],
        "policy": (
            "This artifact is non-mutating. It converts attending-trend dossiers, historical-link search "
            "coverage, candidate evidence, reviewer queues, and accepted facts into one action state per group."
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
    rows = build_rows(generated_at)
    conn = sqlite3.connect(args.db)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"attending_trend_discovery_workbench": len(rows)}))


if __name__ == "__main__":
    main()
