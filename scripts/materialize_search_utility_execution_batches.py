#!/usr/bin/env python3
"""Materialize bounded execution batches for search utility assurance rows."""

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
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "search_utility_execution_batches.csv"
JSON_PATH = ARTIFACTS / "search_utility_execution_batches.json"
SUMMARY_PATH = ARTIFACTS / "search_utility_execution_batch_summary.json"

MAX_ITEMS_PER_BATCH = 50

FIELDS = [
    "search_utility_execution_batch_key",
    "execution_order",
    "utility_key",
    "utility_name",
    "utility_family",
    "batch_lane",
    "batch_status",
    "ready_to_execute",
    "query_artifact",
    "observation_artifact",
    "candidate_artifact",
    "query_kind_signature",
    "priority_band_signature",
    "http_status_signature",
    "error_signature",
    "candidate_status_signature",
    "batch_row_count",
    "query_count",
    "observed_query_count",
    "unobserved_query_count",
    "failed_observation_count",
    "candidate_count",
    "search_candidate_count",
    "result_count",
    "person_count",
    "program_count",
    "max_priority",
    "min_priority",
    "action_impact_count",
    "top_entities",
    "top_domains",
    "query_kind_counts_json",
    "http_status_counts_json",
    "error_counts_json",
    "candidate_status_counts_json",
    "recommended_operator_action",
    "execution_instructions",
    "required_next_evidence",
    "target_artifact",
    "sample_queries_json",
    "sample_observations_json",
    "sample_candidates_json",
    "evidence_json",
    "generated_at",
]

csv.field_size_limit(sys.maxsize)

UTILITIES = [
    {
        "utility_key": "official_gap_source_search",
        "utility_name": "Official HUP gap-source broad search",
        "utility_family": "official_program_gap_discovery",
        "query_artifact": "penn_gme_gap_source_search_queries.csv",
        "observation_artifact": "penn_gme_gap_source_search_observations.csv",
        "candidate_artifact": "penn_gme_gap_source_candidates.csv",
        "search_candidate_filter": lambda row: row.get("source_role") == "search_result",
    },
    {
        "utility_key": "trainee_profile_search",
        "utility_name": "Official trainee profile search",
        "utility_family": "person_profile_discovery",
        "query_artifact": "trainee_profile_search_queries.csv",
        "observation_artifact": "trainee_profile_search_observations.csv",
        "candidate_artifact": "trainee_profile_discovery_candidates.csv",
        "search_candidate_filter": lambda row: bool(row.get("query_key")),
    },
    {
        "utility_key": "prior_training_background_search",
        "utility_name": "Prior-training background search",
        "utility_family": "person_background_discovery",
        "query_artifact": "prior_training_search_queries.csv",
        "observation_artifact": "prior_training_search_observations.csv",
        "candidate_artifact": "prior_training_discovery_candidates.csv",
        "search_candidate_filter": lambda row: bool(row.get("query_key")),
    },
    {
        "utility_key": "attending_historical_link_search",
        "utility_name": "Attending historical-link search",
        "utility_family": "recent_attending_trend_discovery",
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


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["search_utility_execution_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["search_utility_execution_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def batch_key(parts: tuple[object, ...]) -> str:
    return "search_utility_execution_batch_" + sha256_text(dumps(parts))[:20]


def query_key(row: dict) -> str:
    return row.get("query_key") or ""


def entity_key(row: dict) -> str:
    return (
        row.get("person_key")
        or row.get("official_program_key")
        or row.get("event_group_key")
        or row.get("normalized_name")
        or row.get("display_name")
        or row.get("program_name")
        or ""
    )


def entity_label(row: dict) -> str:
    return row.get("display_name") or row.get("program_name") or row.get("normalized_name") or entity_key(row)


def priority(row: dict) -> int:
    value = as_int(row.get("priority"))
    if value:
        return value
    return 80


def priority_band(row: dict) -> str:
    if row.get("priority_band"):
        return row["priority_band"]
    value = priority(row)
    if value >= 100:
        return "critical"
    if value >= 80:
        return "high"
    if value >= 40:
        return "medium"
    return "low"


def row_domain(row: dict) -> str:
    domain = row.get("result_domain") or row.get("candidate_domain")
    if domain:
        return domain
    url = row.get("candidate_url") or row.get("result_url") or ""
    parsed = urlparse(url)
    return parsed.netloc.lower()


def batch_status(lane: str) -> str:
    return {
        "query_execution": "search_query_execution_ready",
        "endpoint_retry": "search_endpoint_retry_ready",
        "candidate_probe": "search_candidate_probe_ready",
    }[lane]


def recommended_action(lane: str) -> str:
    return {
        "query_execution": "execute_search_query_batch_or_replace_with_reliable_provider",
        "endpoint_retry": "retry_failed_search_observation_batch_with_backoff_or_alternate_provider",
        "candidate_probe": "probe_search_candidate_batch_and_route_claims_through_reconciliation",
    }[lane]


def execution_instructions(lane: str) -> str:
    if lane == "query_execution":
        return "Run the unobserved query set with a reliable provider, persist observation rows, and do not treat unrun queries as absence evidence."
    if lane == "endpoint_retry":
        return "Retry failed or non-200 search observations with backoff or an alternate provider; preserve endpoint failures as source-quality evidence."
    return "Probe candidate URLs, capture source hashes/snippets, and route any claims through source-specific reviewer or acceptance ledgers before accepting facts."


def required_next_evidence(lane: str) -> str:
    if lane == "query_execution":
        return "Search observation row for every batch query, including HTTP status, result count, provider, and error text when blocked."
    if lane == "endpoint_retry":
        return "Fresh successful observation, alternate-provider observation, or documented endpoint limitation for each failed query."
    return "Candidate URL probe with source status, content hash, relevant snippet, identity/program anchors, and reconciliation decision target."


def target_artifact(spec: dict, lane: str) -> str:
    if lane in {"query_execution", "endpoint_retry"}:
        return f"artifacts/data/{spec['observation_artifact']}"
    return f"artifacts/data/{spec['candidate_artifact']}"


def sample_queries(rows: list[dict], limit: int = 10) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-priority(item), entity_label(item), query_key(item)))[:limit]:
        output.append(
            {
                "query_key": query_key(row),
                "entity_key": entity_key(row),
                "display_label": entity_label(row),
                "query_kind": row.get("query_kind") or "",
                "query": row.get("query") or "",
                "query_url": row.get("query_url") or "",
                "priority": priority(row),
            }
        )
    return output


def sample_observations(rows: list[dict], limit: int = 10) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-priority(item), entity_label(item), query_key(item)))[:limit]:
        output.append(
            {
                "query_key": query_key(row),
                "entity_key": entity_key(row),
                "display_label": entity_label(row),
                "query_kind": row.get("query_kind") or "",
                "search_http_status": row.get("search_http_status") or "",
                "result_count": as_int(row.get("result_count")),
                "error": row.get("error") or "",
                "searched_at": row.get("searched_at") or "",
                "priority": priority(row),
            }
        )
    return output


def sample_candidates(rows: list[dict], limit: int = 10) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-priority(item), entity_label(item), query_key(item)))[:limit]:
        output.append(
            {
                "candidate_key": row.get("candidate_key") or "",
                "query_key": query_key(row),
                "entity_key": entity_key(row),
                "display_label": entity_label(row),
                "query_kind": row.get("query_kind") or "",
                "candidate_status": row.get("candidate_status") or row.get("search_status") or "",
                "candidate_url": row.get("candidate_url") or row.get("result_url") or "",
                "result_domain": row_domain(row),
                "priority": priority(row),
            }
        )
    return output


def build_batch(spec: dict, lane: str, rows: list[dict], chunk_index: int, generated_at: str, existing: dict[str, dict]) -> dict:
    priorities = [priority(row) for row in rows]
    query_kinds = Counter(row.get("query_kind") or "" for row in rows)
    priority_bands = Counter(priority_band(row) for row in rows)
    http_statuses = Counter(str(row.get("search_http_status") or "") for row in rows if row.get("search_http_status") not in (None, ""))
    errors = Counter(row.get("error") or row.get("probe_error") or "" for row in rows if row.get("error") or row.get("probe_error"))
    candidate_statuses = Counter(row.get("candidate_status") or row.get("search_status") or "" for row in rows if row.get("candidate_status") or row.get("search_status"))
    domains = Counter(row_domain(row) for row in rows if row_domain(row))
    entities = Counter(entity_label(row) for row in rows if entity_label(row))
    entity_keys = {entity_key(row) for row in rows if entity_key(row)}
    person_keys = {row.get("person_key") for row in rows if row.get("person_key")}
    program_keys = {row.get("official_program_key") for row in rows if row.get("official_program_key")}
    query_keys = {query_key(row) for row in rows if query_key(row)}
    failed_count = sum(
        1
        for row in rows
        if (
            row.get("search_http_status") not in (None, "")
            and as_int(row.get("search_http_status")) != 200
        )
        or bool(row.get("error"))
    )
    observed_count = sum(1 for row in rows if row.get("searched_at") or row.get("search_http_status"))
    candidate_count = len(rows) if lane == "candidate_probe" else 0
    search_candidate_count = candidate_count
    action_impact = {
        "query_execution": len(query_keys) or len(rows),
        "endpoint_retry": failed_count or len(rows),
        "candidate_probe": search_candidate_count or len(rows),
    }[lane]
    key_parts = (
        spec["utility_key"],
        lane,
        query_kinds.most_common(1)[0][0] if query_kinds else "",
        priority_bands.most_common(1)[0][0] if priority_bands else "",
        http_statuses.most_common(1)[0][0] if http_statuses else "",
        errors.most_common(1)[0][0] if errors else "",
        candidate_statuses.most_common(1)[0][0] if candidate_statuses else "",
        chunk_index,
        sorted(query_keys)[:MAX_ITEMS_PER_BATCH],
        [row.get("candidate_key") for row in rows if row.get("candidate_key")][:MAX_ITEMS_PER_BATCH],
    )
    row = {
        "search_utility_execution_batch_key": batch_key(key_parts),
        "execution_order": 0,
        "utility_key": spec["utility_key"],
        "utility_name": spec["utility_name"],
        "utility_family": spec["utility_family"],
        "batch_lane": lane,
        "batch_status": batch_status(lane),
        "ready_to_execute": 1,
        "query_artifact": f"artifacts/data/{spec['query_artifact']}",
        "observation_artifact": f"artifacts/data/{spec['observation_artifact']}",
        "candidate_artifact": f"artifacts/data/{spec['candidate_artifact']}",
        "query_kind_signature": query_kinds.most_common(1)[0][0] if query_kinds else "",
        "priority_band_signature": priority_bands.most_common(1)[0][0] if priority_bands else "",
        "http_status_signature": http_statuses.most_common(1)[0][0] if http_statuses else "",
        "error_signature": errors.most_common(1)[0][0] if errors else "",
        "candidate_status_signature": candidate_statuses.most_common(1)[0][0] if candidate_statuses else "",
        "batch_row_count": len(rows),
        "query_count": len(query_keys),
        "observed_query_count": observed_count,
        "unobserved_query_count": len(rows) if lane == "query_execution" else 0,
        "failed_observation_count": failed_count,
        "candidate_count": candidate_count,
        "search_candidate_count": search_candidate_count,
        "result_count": sum(as_int(row.get("result_count")) for row in rows),
        "person_count": len(person_keys) or (len(entity_keys) if spec["utility_family"] in {"person_profile_discovery", "person_background_discovery", "recent_attending_trend_discovery"} else 0),
        "program_count": len(program_keys) or (len(entity_keys) if spec["utility_family"] == "official_program_gap_discovery" else 0),
        "max_priority": max(priorities) if priorities else 0,
        "min_priority": min(priorities) if priorities else 0,
        "action_impact_count": action_impact,
        "top_entities": "; ".join(entity for entity, _ in entities.most_common(12)),
        "top_domains": "; ".join(domain for domain, _ in domains.most_common(12)),
        "query_kind_counts_json": dumps(dict(sorted(query_kinds.items()))),
        "http_status_counts_json": dumps(dict(sorted(http_statuses.items()))),
        "error_counts_json": dumps(dict(sorted(errors.items()))),
        "candidate_status_counts_json": dumps(dict(sorted(candidate_statuses.items()))),
        "recommended_operator_action": recommended_action(lane),
        "execution_instructions": execution_instructions(lane),
        "required_next_evidence": required_next_evidence(lane),
        "target_artifact": target_artifact(spec, lane),
        "sample_queries_json": dumps(sample_queries(rows if lane == "query_execution" else [])),
        "sample_observations_json": dumps(sample_observations(rows if lane == "endpoint_retry" else [])),
        "sample_candidates_json": dumps(sample_candidates(rows if lane == "candidate_probe" else [])),
        "evidence_json": dumps(
            {
                "utility_key": spec["utility_key"],
                "utility_family": spec["utility_family"],
                "batch_lane": lane,
                "query_keys": sorted(query_keys),
                "candidate_keys": [row.get("candidate_key") for row in rows if row.get("candidate_key")],
                "query_kind_counts": dict(sorted(query_kinds.items())),
                "http_status_counts": dict(sorted(http_statuses.items())),
                "error_counts": dict(sorted(errors.items())),
                "candidate_status_counts": dict(sorted(candidate_statuses.items())),
                "policy": "Search utility execution batches are discovery/probe work only; no candidate becomes accepted trainee, program, contact, or trend evidence without source-specific reconciliation.",
            }
        ),
        "generated_at": generated_at,
    }
    row["generated_at"] = stable_generated_at(existing, row, generated_at)
    return {field: row[field] for field in FIELDS}


def chunked(rows: list[dict]) -> list[list[dict]]:
    return [rows[index : index + MAX_ITEMS_PER_BATCH] for index in range(0, len(rows), MAX_ITEMS_PER_BATCH)]


def build_rows(generated_at: str) -> list[dict]:
    existing = read_existing()
    output = []
    for spec in UTILITIES:
        queries = read_csv(ARTIFACTS / spec["query_artifact"])
        observations = read_csv(ARTIFACTS / spec["observation_artifact"])
        candidates = [row for row in read_csv(ARTIFACTS / spec["candidate_artifact"]) if spec["search_candidate_filter"](row)]
        observed_query_keys = {query_key(row) for row in observations if query_key(row)}
        unobserved_queries = [row for row in queries if query_key(row) not in observed_query_keys]
        failed_observations = [
            row
            for row in observations
            if (
                row.get("search_http_status") not in (None, "")
                and as_int(row.get("search_http_status")) != 200
            )
            or bool(row.get("error"))
        ]
        grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
        for row in unobserved_queries:
            grouped[("query_execution", row.get("query_kind") or "", priority_band(row), "")].append(row)
        for row in failed_observations:
            grouped[("endpoint_retry", row.get("query_kind") or "", str(row.get("search_http_status") or ""), row.get("error") or "")].append(row)
        for row in candidates:
            grouped[("candidate_probe", row.get("query_kind") or "", row.get("candidate_status") or row.get("search_status") or "", row_domain(row))].append(row)

        chunk_index = 0
        for key, rows in sorted(grouped.items()):
            lane = key[0]
            ordered = sorted(rows, key=lambda item: (-priority(item), entity_label(item), query_key(item), item.get("candidate_key") or ""))
            for chunk in chunked(ordered):
                chunk_index += 1
                output.append(build_batch(spec, lane, chunk, chunk_index, generated_at, existing))

    output.sort(
        key=lambda item: (
            -as_int(item["max_priority"]),
            item["utility_family"],
            item["batch_lane"],
            item["query_kind_signature"],
            item["search_utility_execution_batch_key"],
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
    conn.execute("DROP TABLE IF EXISTS search_utility_execution_batches")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO search_utility_execution_batches ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "query_count": sum(as_int(row["query_count"]) for row in rows),
        "unobserved_query_count": sum(as_int(row["unobserved_query_count"]) for row in rows),
        "failed_observation_count": sum(as_int(row["failed_observation_count"]) for row in rows),
        "candidate_count": sum(as_int(row["candidate_count"]) for row in rows),
        "search_candidate_count": sum(as_int(row["search_candidate_count"]) for row in rows),
        "action_impact_count": sum(as_int(row["action_impact_count"]) for row in rows),
        "by_utility_family": dict(sorted(Counter(row["utility_family"] for row in rows).items())),
        "by_batch_lane": dict(sorted(Counter(row["batch_lane"] for row in rows).items())),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "utility_family": row["utility_family"],
                "batch_lane": row["batch_lane"],
                "batch_status": row["batch_status"],
                "batch_row_count": row["batch_row_count"],
                "action_impact_count": row["action_impact_count"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Search utility execution batches make unobserved queries, endpoint retries, and candidate probes executable without turning search results into accepted evidence.",
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
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    conn = sqlite3.connect(args.db)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"search_utility_execution_batches": len(rows)}))


if __name__ == "__main__":
    main()
