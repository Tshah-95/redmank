#!/usr/bin/env python3
"""Materialize bounded batches for official program coverage action rows."""

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

CSV_PATH = ARTIFACTS / "official_program_coverage_batches.csv"
JSON_PATH = ARTIFACTS / "official_program_coverage_batches.json"
SUMMARY_PATH = ARTIFACTS / "official_program_coverage_batch_summary.json"

MAX_QUEUE_ROWS_PER_BATCH = 25

FIELDS = [
    "official_program_coverage_batch_key",
    "execution_order",
    "action_lane",
    "blocker_status",
    "official_program_type",
    "assurance_level_signature",
    "batch_status",
    "ready_to_review",
    "queue_count",
    "program_count",
    "person_impact_count",
    "candidate_source_count",
    "action_impact_count",
    "max_priority",
    "min_priority",
    "assurance_level_counts_json",
    "coverage_status_counts_json",
    "assurance_status_counts_json",
    "department_counts_json",
    "top_programs",
    "top_candidate_urls",
    "recommended_operator_action",
    "review_instructions",
    "required_next_evidence",
    "target_artifact",
    "top_queue_rows_json",
    "top_dossiers_json",
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


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["official_program_coverage_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["official_program_coverage_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def batch_key(parts: tuple[object, ...]) -> str:
    return "official_program_coverage_batch_" + sha256_text(dumps(parts))[:20]


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def batch_status(action_lane: str) -> str:
    return {
        "count_conflict_review": "count_conflict_review_ready",
        "alias_review": "alias_scope_review_ready",
        "accepted_alias_open_gap_policy": "accepted_alias_gap_policy_review_ready",
        "accepted_alias_denominator_policy": "accepted_alias_denominator_policy_review_ready",
        "accepted_alias_denominator_closed_monitor": "accepted_alias_monitor_ready",
        "parser_or_roster_source_review": "parser_or_context_review_ready",
        "source_candidate_probe": "candidate_source_probe_ready",
        "official_page_manual_review": "official_page_review_ready",
        "broad_source_discovery": "source_discovery_ready",
    }.get(action_lane, "coverage_action_review_ready")


def recommended_action(action_lane: str) -> str:
    return {
        "count_conflict_review": "review_count_conflict_batch_before_denominator_mutation",
        "alias_review": "review_alias_scope_batch_and_record_decisions",
        "accepted_alias_open_gap_policy": "review_accepted_alias_gap_policy_batch",
        "accepted_alias_denominator_policy": "review_accepted_alias_denominator_policy_batch",
        "accepted_alias_denominator_closed_monitor": "monitor_accepted_alias_denominator_closure_batch",
        "parser_or_roster_source_review": "review_candidate_sources_for_parser_or_context_only_batch",
        "source_candidate_probe": "probe_candidate_sources_and_classify_roster_support_batch",
        "official_page_manual_review": "review_official_pages_for_linked_current_roster_batch",
        "broad_source_discovery": "run_broad_official_source_discovery_batch",
    }.get(action_lane, "review_official_program_coverage_batch")


def review_instructions(action_lane: str) -> str:
    if action_lane == "count_conflict_review":
        return "Compare accepted membership count with the resolved official source before any denominator coverage mutation."
    if action_lane == "alias_review":
        return "Confirm same official program scope, role, track, and current-roster denominator before accepting or splitting an alias."
    if action_lane.startswith("accepted_alias"):
        return "Review accepted alias evidence against denominator-closure policy; monitor-only rows do not reopen unless source scope changes."
    if action_lane == "parser_or_roster_source_review":
        return "Inspect candidate pages and decide whether parser support can extract current people or the page is context-only."
    if action_lane == "source_candidate_probe":
        return "Probe candidate URLs and retain only current roster pages with supported person structure."
    return "Resolve public-source coverage evidence without mutating program denominator truth outside accepted alias/source ledgers."


def required_next_evidence(rows: list[dict]) -> str:
    questions = Counter(row.get("review_question") or "" for row in rows)
    if questions:
        return questions.most_common(1)[0][0]
    return "Official program URL, current roster source, parser output, or explicit denominator reviewer decision."


def target_artifact(action_lane: str) -> str:
    if action_lane == "alias_review":
        return "artifacts/data/official_program_alias_reviewer_decisions.csv"
    if action_lane.startswith("accepted_alias"):
        return "artifacts/data/official_program_denominator_closure_audit.csv"
    if action_lane in {"parser_or_roster_source_review", "source_candidate_probe"}:
        return "artifacts/data/penn_gme_gap_source_candidates.csv"
    return "artifacts/data/official_program_coverage_assurance_audit.csv"


def compact_candidate_urls(rows: list[dict], limit: int = 10) -> str:
    counts = Counter(row.get("candidate_url") or "" for row in rows if row.get("candidate_url"))
    return "; ".join(url for url, _ in counts.most_common(limit))


def top_queue_rows(rows: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("priority")), item.get("official_program_name") or ""))[
        :limit
    ]:
        output.append(
            {
                "queue_key": row.get("queue_key"),
                "official_program_key": row.get("official_program_key"),
                "official_program_name": row.get("official_program_name"),
                "official_program_type": row.get("official_program_type"),
                "official_department": row.get("official_department"),
                "priority": as_int(row.get("priority")),
                "person_impact_count": as_int(row.get("person_impact_count")),
                "candidate_source_count": as_int(row.get("candidate_source_count")),
                "coverage_status": row.get("coverage_status"),
                "assurance_status": row.get("assurance_status"),
                "assurance_level": as_int(row.get("assurance_level")),
                "candidate_url": row.get("candidate_url") or "",
            }
        )
    return output


def top_dossiers(dossiers: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in dossiers[:limit]:
        output.append(
            {
                "dossier_key": row.get("dossier_key"),
                "official_program_key": row.get("official_program_key"),
                "official_program_name": row.get("official_program_name"),
                "denominator_status": row.get("denominator_status"),
                "display_safety_status": row.get("display_safety_status"),
                "top_priority": as_int(row.get("top_priority")),
                "top_action_lane": row.get("top_action_lane"),
                "recommended_next_action": row.get("recommended_next_action"),
            }
        )
    return output


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    queue_rows = sqlite_rows(
        conn,
        """
        SELECT *
        FROM official_program_coverage_action_queue
        ORDER BY priority DESC, person_impact_count DESC, official_department, official_program_name, queue_key
        """,
    )
    dossiers_by_program: dict[str, dict] = {
        row["official_program_key"]: row
        for row in sqlite_rows(
            conn,
            """
            SELECT *
            FROM official_program_coverage_dossiers
            ORDER BY top_priority DESC, official_program_name, dossier_key
            """,
        )
    }

    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in queue_rows:
        grouped[
            (
                row.get("action_lane") or "",
                row.get("blocker_status") or "",
                row.get("official_program_type") or "",
                str(as_int(row.get("assurance_level"))),
            )
        ].append(row)

    output = []
    for (lane, blocker, program_type, level_signature), rows in grouped.items():
        rows = sorted(rows, key=lambda item: (-as_int(item.get("priority")), item.get("official_program_name") or ""))
        for chunk_index, offset in enumerate(range(0, len(rows), MAX_QUEUE_ROWS_PER_BATCH), start=1):
            chunk = rows[offset : offset + MAX_QUEUE_ROWS_PER_BATCH]
            keys = [item.get("queue_key") for item in chunk]
            priorities = [as_int(item.get("priority")) for item in chunk]
            status = batch_status(lane)
            assurance_levels = Counter(str(as_int(item.get("assurance_level"))) for item in chunk)
            coverage_statuses = Counter(item.get("coverage_status") or "" for item in chunk)
            assurance_statuses = Counter(item.get("assurance_status") or "" for item in chunk)
            departments = Counter(item.get("official_department") or "" for item in chunk)
            dossier_rows = [
                dossiers_by_program[item.get("official_program_key") or ""]
                for item in chunk
                if item.get("official_program_key") in dossiers_by_program
            ]
            row = {
                "official_program_coverage_batch_key": batch_key(
                    (lane, blocker, program_type, level_signature, chunk_index, keys)
                ),
                "execution_order": 0,
                "action_lane": lane,
                "blocker_status": blocker,
                "official_program_type": program_type,
                "assurance_level_signature": level_signature,
                "batch_status": status,
                "ready_to_review": 1,
                "queue_count": len(chunk),
                "program_count": len({item.get("official_program_key") or item.get("official_program_name") for item in chunk}),
                "person_impact_count": sum(as_int(item.get("person_impact_count")) for item in chunk),
                "candidate_source_count": sum(as_int(item.get("candidate_source_count")) for item in chunk),
                "action_impact_count": sum(
                    max(
                        as_int(item.get("person_impact_count")),
                        as_int(item.get("candidate_source_count")),
                        1,
                    )
                    for item in chunk
                ),
                "max_priority": max(priorities) if priorities else 0,
                "min_priority": min(priorities) if priorities else 0,
                "assurance_level_counts_json": dumps(dict(sorted(assurance_levels.items()))),
                "coverage_status_counts_json": dumps(dict(sorted(coverage_statuses.items()))),
                "assurance_status_counts_json": dumps(dict(sorted(assurance_statuses.items()))),
                "department_counts_json": dumps(dict(sorted(departments.items()))),
                "top_programs": "; ".join(item.get("official_program_name") or "" for item in chunk[:12]),
                "top_candidate_urls": compact_candidate_urls(chunk),
                "recommended_operator_action": recommended_action(lane),
                "review_instructions": review_instructions(lane),
                "required_next_evidence": required_next_evidence(chunk),
                "target_artifact": target_artifact(lane),
                "top_queue_rows_json": dumps(top_queue_rows(chunk)),
                "top_dossiers_json": dumps(top_dossiers(dossier_rows)),
                "evidence_json": dumps(
                    {
                        "queue_keys": keys,
                        "assurance_level_counts": dict(sorted(assurance_levels.items())),
                        "coverage_status_counts": dict(sorted(coverage_statuses.items())),
                        "assurance_status_counts": dict(sorted(assurance_statuses.items())),
                        "department_counts": dict(sorted(departments.items())),
                        "top_queue_rows": top_queue_rows(chunk),
                        "top_dossiers": top_dossiers(dossier_rows),
                        "policy": {
                            "non_mutating": True,
                            "coverage_truth_requires": [
                                "current public roster extraction, accepted alias mapping, or explicit denominator closure evidence",
                                "source-backed person structure or reviewer-confirmed alias/scope decision",
                                "downstream rebuild through official_program_coverage_assurance_audit",
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
            -as_int(item["max_priority"]),
            item["action_lane"],
            item["official_program_type"],
            item["official_program_coverage_batch_key"],
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
    conn.execute("DROP TABLE IF EXISTS official_program_coverage_batches")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO official_program_coverage_batches ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "queue_count": sum(as_int(row["queue_count"]) for row in rows),
        "program_count": sum(as_int(row["program_count"]) for row in rows),
        "person_impact_count": sum(as_int(row["person_impact_count"]) for row in rows),
        "candidate_source_count": sum(as_int(row["candidate_source_count"]) for row in rows),
        "action_impact_count": sum(as_int(row["action_impact_count"]) for row in rows),
        "by_action_lane": dict(sorted(Counter(row["action_lane"] for row in rows).items())),
        "by_blocker_status": dict(sorted(Counter(row["blocker_status"] for row in rows).items())),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_program_type": dict(sorted(Counter(row["official_program_type"] for row in rows).items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "action_lane": row["action_lane"],
                "blocker_status": row["blocker_status"],
                "official_program_type": row["official_program_type"],
                "batch_status": row["batch_status"],
                "queue_count": row["queue_count"],
                "person_impact_count": row["person_impact_count"],
                "candidate_source_count": row["candidate_source_count"],
                "action_impact_count": row["action_impact_count"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Official program coverage batches are non-mutating operator sessions over denominator coverage gaps; coverage truth changes still require source-backed extraction, accepted alias mapping, or explicit denominator closure evidence.",
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
    print(dumps({"official_program_coverage_batches": len(rows)}))


if __name__ == "__main__":
    main()
