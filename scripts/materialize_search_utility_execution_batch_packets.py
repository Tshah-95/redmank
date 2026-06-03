#!/usr/bin/env python3
"""Materialize per-query/candidate packet support for search utility execution batches."""

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

CSV_PATH = ARTIFACTS / "search_utility_execution_batch_packets.csv"
JSON_PATH = ARTIFACTS / "search_utility_execution_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "search_utility_execution_batch_packet_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "search_utility_execution_batch_packet_key",
    "search_utility_execution_batch_key",
    "execution_order",
    "batch_packet_order",
    "utility_key",
    "utility_name",
    "utility_family",
    "batch_lane",
    "batch_status",
    "packet_status",
    "support_status",
    "work_item_type",
    "query_artifact",
    "observation_artifact",
    "candidate_artifact",
    "query_key",
    "candidate_key",
    "entity_key",
    "display_label",
    "person_key",
    "official_program_key",
    "event_group_key",
    "normalized_name",
    "role",
    "program_name",
    "query_kind",
    "query",
    "query_url",
    "priority",
    "priority_band",
    "search_http_status",
    "result_count",
    "error",
    "searched_at",
    "candidate_status",
    "candidate_url",
    "candidate_title",
    "candidate_domain",
    "candidate_rank",
    "candidate_confidence",
    "probe_http_status",
    "probe_content_type",
    "probe_text_length",
    "probe_sha256",
    "probe_error",
    "probed_at",
    "target_artifact",
    "required_next_evidence",
    "recommended_operator_action",
    "recommended_packet_action",
    "source_row_json",
    "batch_evidence_json",
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


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {
        row["search_utility_execution_batch_packet_key"]: row
        for row in read_csv(CSV_PATH)
        if row.get("search_utility_execution_batch_packet_key")
    }


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["search_utility_execution_batch_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def packet_key(batch_key: str, work_item_type: str, source_key: str) -> str:
    return "search_utility_execution_batch_packet_" + sha256_text(
        f"{batch_key}|{work_item_type}|{source_key}"
    )[:20]


def query_key(row: dict) -> str:
    return row.get("query_key") or ""


def candidate_key(row: dict) -> str:
    return row.get("candidate_key") or ""


def priority(row: dict) -> int:
    value = as_int(row.get("priority"))
    return value or 80


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


def display_label(row: dict) -> str:
    return row.get("display_name") or row.get("program_name") or row.get("normalized_name") or entity_key(row)


def packet_status(lane: str) -> str:
    return {
        "query_execution": "search_query_packet_ready",
        "endpoint_retry": "search_endpoint_retry_packet_ready",
        "candidate_probe": "search_candidate_probe_packet_ready",
    }.get(lane, "search_execution_packet_ready")


def support_status(lane: str, row: dict) -> str:
    if lane == "query_execution":
        return "needs_search_observation"
    if lane == "endpoint_retry":
        if row.get("error"):
            return "needs_retry_after_endpoint_error"
        return "needs_retry_after_non_200_status"
    if lane == "candidate_probe":
        if row.get("probe_http_status") and as_int(row.get("probe_http_status")) != 200:
            return "needs_candidate_source_reprobe_or_access_review"
        return "needs_candidate_source_reconciliation"
    return "needs_search_utility_review"


def work_item_type(lane: str) -> str:
    return {
        "query_execution": "search_query",
        "endpoint_retry": "search_observation_retry",
        "candidate_probe": "search_candidate_probe",
    }.get(lane, "search_utility_packet")


def recommended_packet_action(lane: str) -> str:
    return {
        "query_execution": "execute_query_and_record_search_observation",
        "endpoint_retry": "retry_or_replace_search_endpoint_and_preserve_failure_evidence",
        "candidate_probe": "probe_candidate_url_and_route_claims_through_reconciliation",
    }.get(lane, "review_search_utility_packet")


def compact_batch_evidence(batch: dict) -> dict:
    return {
        "search_utility_execution_batch_key": batch.get("search_utility_execution_batch_key") or "",
        "utility_key": batch.get("utility_key") or "",
        "utility_family": batch.get("utility_family") or "",
        "batch_lane": batch.get("batch_lane") or "",
        "query_artifact": batch.get("query_artifact") or "",
        "observation_artifact": batch.get("observation_artifact") or "",
        "candidate_artifact": batch.get("candidate_artifact") or "",
        "query_count": as_int(batch.get("query_count")),
        "unobserved_query_count": as_int(batch.get("unobserved_query_count")),
        "failed_observation_count": as_int(batch.get("failed_observation_count")),
        "candidate_count": as_int(batch.get("candidate_count")),
        "action_impact_count": as_int(batch.get("action_impact_count")),
        "query_kind_signature": batch.get("query_kind_signature") or "",
        "http_status_signature": batch.get("http_status_signature") or "",
        "candidate_status_signature": batch.get("candidate_status_signature") or "",
        "target_artifact": batch.get("target_artifact") or "",
    }


def source_key_for_lane(lane: str, row: dict) -> str:
    if lane == "candidate_probe":
        return candidate_key(row) or query_key(row) or entity_key(row)
    return query_key(row) or candidate_key(row) or entity_key(row)


def load_rows_by_artifact() -> dict[str, list[dict]]:
    artifacts = {
        row.get("query_artifact")
        for row in read_csv(ARTIFACTS / "search_utility_execution_batches.csv")
    } | {
        row.get("observation_artifact")
        for row in read_csv(ARTIFACTS / "search_utility_execution_batches.csv")
    } | {
        row.get("candidate_artifact")
        for row in read_csv(ARTIFACTS / "search_utility_execution_batches.csv")
    }
    return {
        artifact: read_csv(ROOT / artifact)
        for artifact in sorted(artifact for artifact in artifacts if artifact)
    }


def build_indexes(rows_by_artifact: dict[str, list[dict]]) -> tuple[dict[str, dict[str, dict]], dict[str, dict[str, dict]]]:
    by_query: dict[str, dict[str, dict]] = {}
    by_candidate: dict[str, dict[str, dict]] = {}
    for artifact, rows in rows_by_artifact.items():
        by_query[artifact] = {query_key(row): row for row in rows if query_key(row)}
        by_candidate[artifact] = {candidate_key(row): row for row in rows if candidate_key(row)}
    return by_query, by_candidate


def packet_source_rows(batch: dict, by_query: dict[str, dict[str, dict]], by_candidate: dict[str, dict[str, dict]]) -> list[dict]:
    lane = batch.get("batch_lane") or ""
    evidence = parse_json(batch.get("evidence_json"), {})
    if lane == "candidate_probe":
        candidate_artifact = batch.get("candidate_artifact") or ""
        candidates = by_candidate.get(candidate_artifact, {})
        return [candidates[key] for key in evidence.get("candidate_keys", []) if key in candidates]
    artifact = batch.get("observation_artifact") if lane == "endpoint_retry" else batch.get("query_artifact")
    rows_by_query = by_query.get(artifact or "", {})
    return [rows_by_query[key] for key in evidence.get("query_keys", []) if key in rows_by_query]


def build_packet(batch: dict, row: dict, packet_order: int, generated_at: str, existing: dict[str, dict]) -> dict:
    lane = batch.get("batch_lane") or ""
    source_key = source_key_for_lane(lane, row)
    out = {
        "search_utility_execution_batch_packet_key": packet_key(
            batch["search_utility_execution_batch_key"],
            work_item_type(lane),
            source_key,
        ),
        "search_utility_execution_batch_key": batch["search_utility_execution_batch_key"],
        "execution_order": batch.get("execution_order") or 0,
        "batch_packet_order": packet_order,
        "utility_key": batch.get("utility_key") or "",
        "utility_name": batch.get("utility_name") or "",
        "utility_family": batch.get("utility_family") or "",
        "batch_lane": lane,
        "batch_status": batch.get("batch_status") or "",
        "packet_status": packet_status(lane),
        "support_status": support_status(lane, row),
        "work_item_type": work_item_type(lane),
        "query_artifact": batch.get("query_artifact") or "",
        "observation_artifact": batch.get("observation_artifact") or "",
        "candidate_artifact": batch.get("candidate_artifact") or "",
        "query_key": query_key(row),
        "candidate_key": candidate_key(row),
        "entity_key": entity_key(row),
        "display_label": display_label(row),
        "person_key": row.get("person_key") or "",
        "official_program_key": row.get("official_program_key") or "",
        "event_group_key": row.get("event_group_key") or "",
        "normalized_name": row.get("normalized_name") or "",
        "role": row.get("role") or "",
        "program_name": row.get("program_name") or "",
        "query_kind": row.get("query_kind") or "",
        "query": row.get("query") or "",
        "query_url": row.get("query_url") or "",
        "priority": priority(row),
        "priority_band": priority_band(row),
        "search_http_status": row.get("search_http_status") or row.get("http_status") or "",
        "result_count": as_int(row.get("result_count")),
        "error": row.get("error") or "",
        "searched_at": row.get("searched_at") or "",
        "candidate_status": row.get("candidate_status") or row.get("search_status") or "",
        "candidate_url": row.get("candidate_url") or row.get("result_url") or "",
        "candidate_title": row.get("candidate_title") or row.get("result_title") or "",
        "candidate_domain": row_domain(row),
        "candidate_rank": row.get("result_rank") or "",
        "candidate_confidence": row.get("confidence") or "",
        "probe_http_status": row.get("probe_http_status") or row.get("http_status") or "",
        "probe_content_type": row.get("probe_content_type") or row.get("content_type") or "",
        "probe_text_length": as_int(row.get("probe_text_length") or row.get("text_length")),
        "probe_sha256": row.get("probe_sha256") or row.get("sha256") or "",
        "probe_error": row.get("probe_error") or "",
        "probed_at": row.get("probed_at") or "",
        "target_artifact": batch.get("target_artifact") or "",
        "required_next_evidence": row.get("required_next_evidence") or batch.get("required_next_evidence") or "",
        "recommended_operator_action": batch.get("recommended_operator_action") or "",
        "recommended_packet_action": recommended_packet_action(lane),
        "source_row_json": dumps(row),
        "batch_evidence_json": dumps(compact_batch_evidence(batch)),
        "evidence_json": dumps(
            {
                "policy": "Search execution packets are non-mutating work units. Search observations and candidate probes must route through source-specific reviewer or acceptance ledgers before any fact is accepted.",
                "utility_key": batch.get("utility_key") or "",
                "utility_family": batch.get("utility_family") or "",
                "batch_lane": lane,
                "work_item_type": work_item_type(lane),
                "query_key": query_key(row),
                "candidate_key": candidate_key(row),
                "entity_key": entity_key(row),
                "candidate_url": row.get("candidate_url") or row.get("result_url") or "",
                "support_status": support_status(lane, row),
            }
        ),
        "generated_at": generated_at,
    }
    out["generated_at"] = stable_generated_at(existing, out, generated_at)
    return {field: out[field] for field in FIELDS}


def build_rows(generated_at: str) -> list[dict]:
    existing = read_existing()
    rows_by_artifact = load_rows_by_artifact()
    by_query, by_candidate = build_indexes(rows_by_artifact)
    output = []
    for batch in read_csv(ARTIFACTS / "search_utility_execution_batches.csv"):
        source_rows = sorted(
            packet_source_rows(batch, by_query, by_candidate),
            key=lambda item: (-priority(item), display_label(item), query_key(item), candidate_key(item)),
        )
        for index, source_row in enumerate(source_rows, start=1):
            output.append(build_packet(batch, source_row, index, generated_at, existing))
    output.sort(
        key=lambda item: (
            as_int(item["execution_order"]),
            as_int(item["batch_packet_order"]),
            item["search_utility_execution_batch_packet_key"],
        )
    )
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DROP TABLE IF EXISTS search_utility_execution_batch_packets")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO search_utility_execution_batch_packets ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "batch_count": len({row["search_utility_execution_batch_key"] for row in rows}),
        "query_packet_count": sum(1 for row in rows if row["work_item_type"] == "search_query"),
        "endpoint_retry_packet_count": sum(1 for row in rows if row["work_item_type"] == "search_observation_retry"),
        "candidate_probe_packet_count": sum(1 for row in rows if row["work_item_type"] == "search_candidate_probe"),
        "by_utility_family": dict(sorted(Counter(row["utility_family"] for row in rows).items())),
        "by_batch_lane": dict(sorted(Counter(row["batch_lane"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_work_item_type": dict(sorted(Counter(row["work_item_type"] for row in rows).items())),
        "top_packets": [
            {
                "execution_order": row["execution_order"],
                "batch_packet_order": row["batch_packet_order"],
                "utility_family": row["utility_family"],
                "batch_lane": row["batch_lane"],
                "work_item_type": row["work_item_type"],
                "display_label": row["display_label"],
                "query_kind": row["query_kind"],
                "support_status": row["support_status"],
                "candidate_url": row["candidate_url"],
            }
            for row in rows[:25]
        ],
        "policy": "Search utility execution batch packets make every hidden query, retry, and candidate-probe unit addressable without accepting search output as fact.",
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
    print(dumps({"search_utility_execution_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
