#!/usr/bin/env python3
"""Materialize cross-lane assurance for search-backed discovery utilities."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_OUT = ARTIFACTS / "search_utility_assurance.csv"
JSON_OUT = ARTIFACTS / "search_utility_assurance.json"
SUMMARY_OUT = ARTIFACTS / "search_utility_assurance_summary.json"

FIELDS = [
    "utility_key",
    "utility_name",
    "utility_family",
    "claim_surface",
    "query_artifact",
    "observation_artifact",
    "candidate_artifact",
    "query_rows",
    "search_observation_rows",
    "candidate_rows",
    "search_candidate_rows",
    "result_rows",
    "successful_search_rows",
    "non_200_search_rows",
    "error_rows",
    "search_coverage_rate",
    "candidate_yield_per_observation",
    "search_execution_status",
    "by_search_http_status_json",
    "by_search_error_json",
    "recommended_next_action",
    "source_quality_learning",
    "audited_at",
]

UTILITIES = [
    {
        "utility_key": "official_gap_source_search",
        "utility_name": "Official HUP gap-source broad search",
        "utility_family": "official_program_gap_discovery",
        "claim_surface": "Candidate source URLs for official HUP programs missing current-roster capture.",
        "query_artifact": "penn_gme_gap_source_search_queries.csv",
        "observation_artifact": "penn_gme_gap_source_search_observations.csv",
        "candidate_artifact": "penn_gme_gap_source_candidates.csv",
        "search_candidate_filter": lambda row: row.get("source_role") == "search_result",
    },
    {
        "utility_key": "trainee_profile_search",
        "utility_name": "Official trainee profile search",
        "utility_family": "person_profile_discovery",
        "claim_surface": "Candidate official profile/context URLs for trainees missing roster-linked profiles.",
        "query_artifact": "trainee_profile_search_queries.csv",
        "observation_artifact": "trainee_profile_search_observations.csv",
        "candidate_artifact": "trainee_profile_discovery_candidates.csv",
        "search_candidate_filter": lambda row: bool(row.get("query_key")),
    },
    {
        "utility_key": "prior_training_background_search",
        "utility_name": "Prior-training background search",
        "utility_family": "person_background_discovery",
        "claim_surface": "Candidate pages for medical-school and prior-residency background enrichment.",
        "query_artifact": "prior_training_search_queries.csv",
        "observation_artifact": "prior_training_search_observations.csv",
        "candidate_artifact": "prior_training_discovery_candidates.csv",
        "search_candidate_filter": lambda row: bool(row.get("query_key")),
    },
    {
        "utility_key": "attending_historical_link_search",
        "utility_name": "Attending historical-link search",
        "utility_family": "recent_attending_trend_discovery",
        "claim_surface": "Candidate pages bridging current Penn attendings to historical Penn trainee evidence.",
        "query_artifact": "attending_historical_link_search_queries.csv",
        "observation_artifact": "attending_historical_link_search_observations.csv",
        "candidate_artifact": "attending_historical_link_candidates.csv",
        "search_candidate_filter": lambda row: row.get("search_status") == "ok",
    },
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def status_for(query_rows: int, observation_rows: int, successful_rows: int, non_200_rows: int, error_rows: int, result_rows: int) -> str:
    if query_rows == 0:
        return "no_query_manifest"
    if observation_rows == 0:
        return "planned_not_executed"
    if successful_rows and (non_200_rows or error_rows):
        return "executed_partial_with_endpoint_errors"
    if successful_rows:
        return "executed_success_with_results" if result_rows else "executed_success_no_results"
    if non_200_rows or error_rows:
        return "executed_blocked_by_search_endpoint"
    return "executed_no_results"


def recommended_action(status: str) -> str:
    return {
        "no_query_manifest": "create_query_manifest_before_claiming_search_coverage",
        "planned_not_executed": "execute_optional_search_or_swap_to_a_more_reliable_provider_before_treating_absence_as_evidence",
        "executed_partial_with_endpoint_errors": "retain_candidates_but_treat_search_completeness_as_partial_and_retry_or_crosscheck",
        "executed_success_with_results": "probe_candidates_and_route_claims_through_reconciliation_before_acceptance",
        "executed_success_no_results": "record_no_candidate_signal_but_do_not_treat_as_proof_of_absence_without_source_refresh",
        "executed_blocked_by_search_endpoint": "use_backoff_or_alternate_search_provider_and_record_endpoint_limitations",
        "executed_no_results": "monitor_or_crosscheck_with_official_sources_before closing gaps",
    }[status]


def quality_learning(status: str) -> str:
    if status == "planned_not_executed":
        return "A query manifest is planning evidence, not search evidence; public absence remains untested until observations exist."
    if status == "executed_partial_with_endpoint_errors":
        return "Broad search can produce useful candidates while still being incomplete; endpoint errors must travel with the evidence."
    if status == "executed_success_with_results":
        return "Search results are discovery candidates only; source probing and identity/program reconciliation remain the acceptance gate."
    if status == "executed_blocked_by_search_endpoint":
        return "Endpoint behavior is a source-quality fact; blocked search should lower utility confidence rather than imply no public evidence."
    if status == "executed_success_no_results":
        return "No-result search observations are weak absence evidence unless query coverage and source scope are both strong."
    return "This utility needs a stronger execution trail before it can support coverage or enrichment conclusions."


def build_row(spec: dict, audited_at: str) -> dict:
    query_rows = read_csv(ARTIFACTS / spec["query_artifact"])
    observation_rows = read_csv(ARTIFACTS / spec["observation_artifact"])
    candidate_rows = read_csv(ARTIFACTS / spec["candidate_artifact"])
    http_counts = Counter(str(row.get("search_http_status") or "") for row in observation_rows if row.get("search_http_status") not in (None, ""))
    error_counts = Counter(row.get("error") or "" for row in observation_rows if row.get("error"))
    successful_rows = sum(1 for row in observation_rows if as_int(row.get("search_http_status")) == 200 and not row.get("error"))
    non_200_rows = sum(
        1
        for row in observation_rows
        if row.get("search_http_status") not in (None, "")
        and as_int(row.get("search_http_status")) != 200
    )
    error_rows = sum(1 for row in observation_rows if row.get("error"))
    result_rows = sum(as_int(row.get("result_count")) for row in observation_rows)
    search_candidate_rows = sum(1 for row in candidate_rows if spec["search_candidate_filter"](row))
    observation_count = len(observation_rows)
    status = status_for(len(query_rows), observation_count, successful_rows, non_200_rows, error_rows, result_rows)
    row = {
        "utility_key": spec["utility_key"],
        "utility_name": spec["utility_name"],
        "utility_family": spec["utility_family"],
        "claim_surface": spec["claim_surface"],
        "query_artifact": f"artifacts/data/{spec['query_artifact']}",
        "observation_artifact": f"artifacts/data/{spec['observation_artifact']}",
        "candidate_artifact": f"artifacts/data/{spec['candidate_artifact']}",
        "query_rows": len(query_rows),
        "search_observation_rows": observation_count,
        "candidate_rows": len(candidate_rows),
        "search_candidate_rows": search_candidate_rows,
        "result_rows": result_rows,
        "successful_search_rows": successful_rows,
        "non_200_search_rows": non_200_rows,
        "error_rows": error_rows,
        "search_coverage_rate": round(observation_count / len(query_rows), 4) if query_rows else 0.0,
        "candidate_yield_per_observation": round(search_candidate_rows / observation_count, 4) if observation_count else 0.0,
        "search_execution_status": status,
        "by_search_http_status_json": dumps(dict(sorted(http_counts.items()))),
        "by_search_error_json": dumps(dict(sorted(error_counts.items()))),
        "recommended_next_action": recommended_action(status),
        "source_quality_learning": quality_learning(status),
        "audited_at": audited_at,
    }
    return {field: row[field] for field in FIELDS}


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(rows: list[dict]) -> None:
    conn = sqlite3.connect(DB)
    with conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("DELETE FROM search_utility_assurance")
        placeholders = ", ".join(f":{field}" for field in FIELDS)
        fields = ", ".join(FIELDS)
        conn.executemany(f"INSERT OR REPLACE INTO search_utility_assurance ({fields}) VALUES ({placeholders})", rows)
    conn.close()


def write_summary(rows: list[dict], audited_at: str) -> None:
    by_status = Counter(row["search_execution_status"] for row in rows)
    payload = {
        "audited_at": audited_at,
        "utility_rows": len(rows),
        "query_rows": sum(as_int(row["query_rows"]) for row in rows),
        "search_observation_rows": sum(as_int(row["search_observation_rows"]) for row in rows),
        "candidate_rows": sum(as_int(row["candidate_rows"]) for row in rows),
        "search_candidate_rows": sum(as_int(row["search_candidate_rows"]) for row in rows),
        "result_rows": sum(as_int(row["result_rows"]) for row in rows),
        "successful_search_rows": sum(as_int(row["successful_search_rows"]) for row in rows),
        "non_200_search_rows": sum(as_int(row["non_200_search_rows"]) for row in rows),
        "error_rows": sum(as_int(row["error_rows"]) for row in rows),
        "by_search_execution_status": dict(sorted(by_status.items())),
        "policy": "Search utilities are discovery surfaces. Query manifests, observations, result rows, and candidates are audited separately so endpoint failures or skipped runs cannot masquerade as absence of public evidence.",
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
    }
    SUMMARY_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    audited_at = now_utc()
    rows = [build_row(spec, audited_at) for spec in UTILITIES]
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows, audited_at)
    print(dumps({"search_utility_assurance": len(rows), "query_rows": sum(as_int(row["query_rows"]) for row in rows)}))


if __name__ == "__main__":
    main()
