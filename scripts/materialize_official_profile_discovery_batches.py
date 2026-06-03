#!/usr/bin/env python3
"""Materialize bounded execution batches for official profile discovery workbench rows."""

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

CSV_PATH = ARTIFACTS / "official_profile_discovery_batches.csv"
JSON_PATH = ARTIFACTS / "official_profile_discovery_batches.json"
SUMMARY_PATH = ARTIFACTS / "official_profile_discovery_batch_summary.json"

MAX_WORKBENCH_ROWS_PER_BATCH = 50

FIELDS = [
    "official_profile_discovery_batch_key",
    "execution_order",
    "discovery_lane",
    "role",
    "batch_status",
    "ready_to_execute",
    "source_domain",
    "query_status_signature",
    "candidate_status_signature",
    "workbench_count",
    "person_count",
    "query_count",
    "observed_query_count",
    "unsearched_query_count",
    "blocked_query_count",
    "successful_query_count",
    "direct_probe_count",
    "candidate_count",
    "official_candidate_count",
    "low_signal_candidate_count",
    "max_discovery_priority",
    "min_discovery_priority",
    "top_programs",
    "top_source_domains",
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


def load_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["official_profile_discovery_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["official_profile_discovery_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def batch_key(parts: tuple[object, ...]) -> str:
    return "official_profile_discovery_batch_" + sha256_text(dumps(parts))[:20]


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def source_domain(row: dict) -> str:
    if row.get("best_candidate_domain"):
        return row["best_candidate_domain"]
    domains = split_semicolon(row.get("source_domains"))
    if domains:
        return domains[0]
    return "no_candidate_domain"


def dominant_signature(json_value: str | None, default: str) -> str:
    counts = load_json(json_value, {})
    if not isinstance(counts, dict) or not counts:
        return default
    key, _ = sorted(counts.items(), key=lambda item: (-as_int(item[1]), str(item[0])))[0]
    return str(key)


def batch_status(lane: str) -> str:
    return {
        "review_official_profile_candidate": "profile_candidate_review_ready",
        "planned_search_not_executed": "profile_search_execution_ready",
        "search_endpoint_blocked_retry": "search_endpoint_retry_required",
        "direct_probe_low_signal_review": "direct_probe_review_ready",
        "low_signal_candidate_review": "low_signal_candidate_review_ready",
        "no_candidate_after_search": "discovery_strategy_review_ready",
        "already_has_profile_url_monitor": "profile_url_monitor_ready",
    }.get(lane, "profile_discovery_review_ready")


def recommended_action(lane: str) -> str:
    return {
        "review_official_profile_candidate": "work_profile_candidate_review_batch_and_record_decisions",
        "planned_search_not_executed": "execute_profile_search_or_direct_probe_batch",
        "search_endpoint_blocked_retry": "retry_profile_search_with_reliable_provider_or_direct_probe_batch",
        "direct_probe_low_signal_review": "review_direct_probe_batch_or_expand_slug_patterns",
        "low_signal_candidate_review": "review_low_signal_candidate_batch_or_collect_stronger_source",
        "no_candidate_after_search": "expand_profile_discovery_strategy_or_record_no_public_candidate",
        "already_has_profile_url_monitor": "monitor_existing_profile_url_batch",
    }.get(lane, "review_profile_discovery_batch")


def execution_instructions(lane: str) -> str:
    if lane == "review_official_profile_candidate":
        return "Review same-person identity, official source ownership, route drift, source hash, and current profile context before writing official_profile_reviewer_decisions.csv."
    if lane == "planned_search_not_executed":
        return "Execute the planned query set or deterministic official-domain direct probes, then regenerate profile discovery artifacts and this workbench."
    if lane == "search_endpoint_blocked_retry":
        return "Use a reliable search provider or direct official-domain probe path; blocked DuckDuckGo HTML responses are endpoint evidence, not absence evidence."
    if lane == "direct_probe_low_signal_review":
        return "Inspect low-signal direct slug probes, refine slug patterns, or route confirmed candidates into trainee_profile_discovery_candidates."
    return "Resolve this profile discovery batch without accepting profile facts outside reviewer decision and acceptance ledgers."


def required_next_evidence(rows: list[dict], lane: str) -> str:
    if lane == "review_official_profile_candidate":
        return "Current official profile candidate reobserved with same-person name/program context, non-generic route, source hash, and reviewer decision."
    if lane == "planned_search_not_executed":
        return "Executed query observations or deterministic direct-probe observations for every batch member before treating profile discovery as exhausted."
    if lane == "search_endpoint_blocked_retry":
        return "Fresh successful search observation, alternate provider result, or direct official-domain probe before concluding no profile exists."
    evidence = Counter(row.get("evidence_required") or "" for row in rows)
    return evidence.most_common(1)[0][0] if evidence else "Official profile or roster-linked public source evidence."


def target_artifact(lane: str) -> str:
    if lane == "review_official_profile_candidate":
        return "artifacts/data/official_profile_reviewer_decisions.csv"
    return "artifacts/data/trainee_profile_discovery_candidates.csv"


def compact_domains(rows: list[dict], limit: int = 10) -> str:
    counts: Counter = Counter()
    for row in rows:
        if row.get("best_candidate_domain"):
            counts[row["best_candidate_domain"]] += 1
        for domain in split_semicolon(row.get("source_domains")):
            counts[domain] += 1
    return "; ".join(f"{domain}:{count}" for domain, count in counts.most_common(limit))


def combined_counts(rows: list[dict], field: str) -> dict:
    counts: Counter = Counter()
    for row in rows:
        values = load_json(row.get(field), {})
        if isinstance(values, dict):
            for key, value in values.items():
                counts[str(key)] += as_int(value)
    return dict(sorted(counts.items()))


def top_workbench_rows(rows: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("discovery_priority")), item.get("display_name") or ""))[
        :limit
    ]:
        output.append(
            {
                "profile_workbench_key": row.get("profile_workbench_key"),
                "person_key": row.get("person_key"),
                "display_name": row.get("display_name"),
                "role": row.get("role"),
                "program_name": row.get("program_name"),
                "discovery_priority": as_int(row.get("discovery_priority")),
                "query_count": as_int(row.get("query_count")),
                "unsearched_query_count": as_int(row.get("unsearched_query_count")),
                "blocked_query_count": as_int(row.get("blocked_query_count")),
                "candidate_count": as_int(row.get("candidate_count")),
                "official_candidate_count": as_int(row.get("official_candidate_count")),
                "best_candidate_url": row.get("best_candidate_url") or "",
                "best_candidate_domain": row.get("best_candidate_domain") or "",
            }
        )
    return output


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    workbench_rows = sqlite_rows(
        conn,
        """
        SELECT *
        FROM official_profile_discovery_workbench
        WHERE discovery_lane != 'already_has_profile_url_monitor'
        ORDER BY discovery_priority DESC, display_name, profile_workbench_key
        """,
    )
    grouped: dict[tuple[str, str, str, str, str], list[dict]] = defaultdict(list)
    for row in workbench_rows:
        lane = row.get("discovery_lane") or ""
        grouped[
            (
                lane,
                row.get("role") or "",
                source_domain(row),
                dominant_signature(row.get("query_status_counts_json"), "no_query_status"),
                dominant_signature(row.get("candidate_status_counts_json"), "no_candidate_status"),
            )
        ].append(row)

    output = []
    for (lane, role, domain, query_signature, candidate_signature), rows in grouped.items():
        rows = sorted(rows, key=lambda item: (-as_int(item.get("discovery_priority")), item.get("display_name") or ""))
        for chunk_index, offset in enumerate(range(0, len(rows), MAX_WORKBENCH_ROWS_PER_BATCH), start=1):
            chunk = rows[offset : offset + MAX_WORKBENCH_ROWS_PER_BATCH]
            priorities = [as_int(item.get("discovery_priority")) for item in chunk]
            keys = [item.get("profile_workbench_key") for item in chunk]
            status = batch_status(lane)
            query_counts = combined_counts(chunk, "query_status_counts_json")
            candidate_counts = combined_counts(chunk, "candidate_status_counts_json")
            row = {
                "official_profile_discovery_batch_key": batch_key(
                    (lane, role, domain, query_signature, candidate_signature, chunk_index, keys)
                ),
                "execution_order": 0,
                "discovery_lane": lane,
                "role": role,
                "batch_status": status,
                "ready_to_execute": 1 if status != "empty_batch" else 0,
                "source_domain": domain,
                "query_status_signature": query_signature,
                "candidate_status_signature": candidate_signature,
                "workbench_count": len(chunk),
                "person_count": len({item.get("person_key") for item in chunk if item.get("person_key")}),
                "query_count": sum(as_int(item.get("query_count")) for item in chunk),
                "observed_query_count": sum(as_int(item.get("observed_query_count")) for item in chunk),
                "unsearched_query_count": sum(as_int(item.get("unsearched_query_count")) for item in chunk),
                "blocked_query_count": sum(as_int(item.get("blocked_query_count")) for item in chunk),
                "successful_query_count": sum(as_int(item.get("successful_query_count")) for item in chunk),
                "direct_probe_count": sum(as_int(item.get("direct_probe_count")) for item in chunk),
                "candidate_count": sum(as_int(item.get("candidate_count")) for item in chunk),
                "official_candidate_count": sum(as_int(item.get("official_candidate_count")) for item in chunk),
                "low_signal_candidate_count": sum(as_int(item.get("low_signal_candidate_count")) for item in chunk),
                "max_discovery_priority": max(priorities) if priorities else 0,
                "min_discovery_priority": min(priorities) if priorities else 0,
                "top_programs": "; ".join(
                    program for program, _ in Counter(item.get("program_name") or "" for item in chunk).most_common(10)
                ),
                "top_source_domains": compact_domains(chunk),
                "query_status_counts_json": dumps(query_counts),
                "candidate_status_counts_json": dumps(candidate_counts),
                "recommended_operator_action": recommended_action(lane),
                "execution_instructions": execution_instructions(lane),
                "required_next_evidence": required_next_evidence(chunk, lane),
                "target_artifact": target_artifact(lane),
                "top_workbench_rows_json": dumps(top_workbench_rows(chunk)),
                "evidence_json": dumps(
                    {
                        "profile_workbench_keys": keys,
                        "query_status_counts": query_counts,
                        "candidate_status_counts": candidate_counts,
                        "top_workbench_rows": top_workbench_rows(chunk),
                        "policy": {
                            "non_mutating": True,
                            "accepted_profile_url_requires": [
                                "official_profile_reviewer_decisions.csv row",
                                "matching profile_fingerprint",
                                "source ownership and same-person/current-context confirmations",
                                "official_profile_reviewer_decision_audit acceptance",
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
            item["role"],
            item["source_domain"],
            item["official_profile_discovery_batch_key"],
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
    conn.execute("DELETE FROM official_profile_discovery_batches")
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO official_profile_discovery_batches ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "workbench_count": sum(as_int(row["workbench_count"]) for row in rows),
        "person_count": sum(as_int(row["person_count"]) for row in rows),
        "query_count": sum(as_int(row["query_count"]) for row in rows),
        "unsearched_query_count": sum(as_int(row["unsearched_query_count"]) for row in rows),
        "blocked_query_count": sum(as_int(row["blocked_query_count"]) for row in rows),
        "candidate_count": sum(as_int(row["candidate_count"]) for row in rows),
        "official_candidate_count": sum(as_int(row["official_candidate_count"]) for row in rows),
        "by_discovery_lane": dict(sorted(Counter(row["discovery_lane"] for row in rows).items())),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "discovery_lane": row["discovery_lane"],
                "role": row["role"],
                "batch_status": row["batch_status"],
                "workbench_count": row["workbench_count"],
                "query_count": row["query_count"],
                "unsearched_query_count": row["unsearched_query_count"],
                "blocked_query_count": row["blocked_query_count"],
                "official_candidate_count": row["official_candidate_count"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Discovery batches are non-mutating operator instructions over profile-gap workbench rows. Accepted profile URLs still require explicit reviewer decisions and acceptance audits.",
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
    print(dumps({"official_profile_discovery_batches": len(rows)}))


if __name__ == "__main__":
    main()
