#!/usr/bin/env python3
"""Materialize per-action packets for official program coverage batches."""

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

CSV_PATH = ARTIFACTS / "official_program_coverage_batch_packets.csv"
JSON_PATH = ARTIFACTS / "official_program_coverage_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "official_program_coverage_batch_packet_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "coverage_batch_packet_key",
    "official_program_coverage_batch_key",
    "execution_order",
    "batch_packet_order",
    "queue_key",
    "dossier_key",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "action_lane",
    "blocker_status",
    "batch_status",
    "packet_status",
    "support_status",
    "priority",
    "person_impact_count",
    "candidate_source_count",
    "assurance_level",
    "coverage_status",
    "assurance_status",
    "denominator_status",
    "display_safety_status",
    "coverage_mutation_allowed",
    "captured_people_count",
    "candidate_url",
    "official_program_url",
    "top_candidate_url",
    "top_candidate_title",
    "alias_review_count",
    "accepted_alias_mapping_count",
    "accepted_alias_people_count",
    "dossier_candidate_source_count",
    "target_artifact",
    "required_next_evidence",
    "recommended_next_action",
    "recommended_packet_action",
    "review_question",
    "review_instructions",
    "queue_row_json",
    "dossier_json",
    "acceptance_boundary",
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


def load_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {row["coverage_batch_packet_key"]: row for row in read_csv(CSV_PATH) if row.get("coverage_batch_packet_key")}


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["coverage_batch_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def packet_key(batch_key: str, queue_key: str) -> str:
    return "official_program_coverage_batch_packet_" + sha256_text(f"{batch_key}|{queue_key}")[:20]


def packet_status(row: dict) -> str:
    lane = row.get("action_lane") or ""
    blocker = row.get("blocker_status") or ""
    if lane == "accepted_alias_denominator_closed_monitor":
        return "accepted_alias_denominator_monitor_packet"
    if lane == "alias_review":
        return "ready_for_alias_scope_review_packet"
    if lane == "accepted_alias_open_gap_policy":
        return "ready_for_accepted_alias_gap_policy_packet"
    if lane == "count_conflict_review":
        return "ready_for_count_conflict_review_packet"
    if lane == "parser_or_roster_source_review":
        return "ready_for_parser_or_context_review_packet"
    if lane == "source_candidate_probe":
        return "ready_for_candidate_source_probe_packet"
    if blocker:
        return "ready_for_official_program_coverage_review_packet"
    return "official_program_coverage_packet_ready"


def support_status(status: str) -> str:
    if "monitor" in status:
        return "monitor"
    return "ready"


def recommended_packet_action(queue: dict, dossier: dict, status: str) -> str:
    if status == "accepted_alias_denominator_monitor_packet":
        return "monitor_accepted_alias_denominator_closure_without_mutation"
    return (
        queue.get("recommended_next_action")
        or dossier.get("recommended_next_action")
        or "review_official_program_coverage_packet"
    )


def compact_queue_row(row: dict) -> dict:
    return {
        "queue_key": row.get("queue_key"),
        "official_program_key": row.get("official_program_key"),
        "official_program_name": row.get("official_program_name"),
        "official_program_type": row.get("official_program_type"),
        "official_department": row.get("official_department"),
        "assurance_status": row.get("assurance_status"),
        "assurance_level": as_int(row.get("assurance_level")),
        "coverage_status": row.get("coverage_status"),
        "action_lane": row.get("action_lane"),
        "priority": as_int(row.get("priority")),
        "person_impact_count": as_int(row.get("person_impact_count")),
        "candidate_source_count": as_int(row.get("candidate_source_count")),
        "candidate_url": row.get("candidate_url") or "",
        "official_program_url": row.get("official_program_url") or "",
        "blocker_status": row.get("blocker_status"),
        "recommended_next_action": row.get("recommended_next_action"),
        "review_question": row.get("review_question"),
    }


def compact_dossier(row: dict) -> dict:
    if not row:
        return {}
    return {
        "dossier_key": row.get("dossier_key"),
        "official_program_key": row.get("official_program_key"),
        "official_program_name": row.get("official_program_name"),
        "denominator_status": row.get("denominator_status"),
        "display_safety_status": row.get("display_safety_status"),
        "coverage_mutation_allowed": as_int(row.get("coverage_mutation_allowed")),
        "captured_people_count": as_int(row.get("captured_people_count")),
        "alias_review_count": as_int(row.get("alias_review_count")),
        "accepted_alias_mapping_count": as_int(row.get("accepted_alias_mapping_count")),
        "accepted_alias_people_count": as_int(row.get("accepted_alias_people_count")),
        "candidate_source_count": as_int(row.get("candidate_source_count")),
        "top_candidate_url": row.get("top_candidate_url") or "",
        "top_candidate_title": row.get("top_candidate_title") or "",
        "missing_evidence_summary": row.get("missing_evidence_summary") or "",
        "recommended_next_action": row.get("recommended_next_action") or "",
    }


def load_batches(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM official_program_coverage_batches
        ORDER BY execution_order, official_program_coverage_batch_key
        """,
    )


def load_queue(conn: sqlite3.Connection) -> dict[str, dict]:
    return {row["queue_key"]: row for row in sqlite_rows(conn, "SELECT * FROM official_program_coverage_action_queue")}


def load_dossiers(conn: sqlite3.Connection) -> dict[str, dict]:
    return {
        row["official_program_key"]: row
        for row in sqlite_rows(conn, "SELECT * FROM official_program_coverage_dossiers")
        if row.get("official_program_key")
    }


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    queue_by_key = load_queue(conn)
    dossiers_by_program = load_dossiers(conn)
    rows = []

    for batch in load_batches(conn):
        evidence = load_json(batch.get("evidence_json"), {})
        queue_keys = evidence.get("queue_keys") if isinstance(evidence, dict) else []
        if not isinstance(queue_keys, list):
            queue_keys = []
        for index, queue_key in enumerate(queue_keys, start=1):
            queue = queue_by_key.get(str(queue_key), {})
            if not queue:
                continue
            dossier = dossiers_by_program.get(queue.get("official_program_key") or "", {})
            status = packet_status(queue)
            row = {
                "coverage_batch_packet_key": packet_key(batch["official_program_coverage_batch_key"], str(queue_key)),
                "official_program_coverage_batch_key": batch["official_program_coverage_batch_key"],
                "execution_order": as_int(batch.get("execution_order")),
                "batch_packet_order": index,
                "queue_key": str(queue_key),
                "dossier_key": dossier.get("dossier_key") or "",
                "official_program_key": queue.get("official_program_key") or "",
                "official_program_name": queue.get("official_program_name") or "",
                "official_program_type": queue.get("official_program_type") or "",
                "official_department": queue.get("official_department") or "",
                "action_lane": queue.get("action_lane") or batch.get("action_lane") or "",
                "blocker_status": queue.get("blocker_status") or batch.get("blocker_status") or "",
                "batch_status": batch.get("batch_status") or "",
                "packet_status": status,
                "support_status": support_status(status),
                "priority": as_int(queue.get("priority")),
                "person_impact_count": as_int(queue.get("person_impact_count")),
                "candidate_source_count": as_int(queue.get("candidate_source_count")),
                "assurance_level": as_int(queue.get("assurance_level")),
                "coverage_status": queue.get("coverage_status") or "",
                "assurance_status": queue.get("assurance_status") or "",
                "denominator_status": dossier.get("denominator_status") or "",
                "display_safety_status": dossier.get("display_safety_status") or "",
                "coverage_mutation_allowed": as_int(dossier.get("coverage_mutation_allowed")),
                "captured_people_count": as_int(dossier.get("captured_people_count")),
                "candidate_url": queue.get("candidate_url") or "",
                "official_program_url": queue.get("official_program_url") or dossier.get("official_program_url") or "",
                "top_candidate_url": dossier.get("top_candidate_url") or "",
                "top_candidate_title": dossier.get("top_candidate_title") or "",
                "alias_review_count": as_int(dossier.get("alias_review_count")),
                "accepted_alias_mapping_count": as_int(dossier.get("accepted_alias_mapping_count")),
                "accepted_alias_people_count": as_int(dossier.get("accepted_alias_people_count")),
                "dossier_candidate_source_count": as_int(dossier.get("candidate_source_count")),
                "target_artifact": batch.get("target_artifact") or "artifacts/data/official_program_coverage_assurance_audit.csv",
                "required_next_evidence": dossier.get("required_next_evidence")
                or queue.get("review_question")
                or batch.get("required_next_evidence")
                or "",
                "recommended_next_action": queue.get("recommended_next_action") or "",
                "recommended_packet_action": recommended_packet_action(queue, dossier, status),
                "review_question": queue.get("review_question") or "",
                "review_instructions": batch.get("review_instructions") or "",
                "queue_row_json": dumps(compact_queue_row(queue)),
                "dossier_json": dumps(compact_dossier(dossier)),
                "acceptance_boundary": (
                    "Official program coverage packets are non-mutating. Denominator coverage changes require "
                    "source-backed roster extraction, accepted alias mapping, or explicit denominator closure "
                    "evidence routed through the official program assurance ledgers."
                ),
                "evidence_json": dumps(
                    {
                        "derived_from": [
                            "official_program_coverage_batches",
                            "official_program_coverage_action_queue",
                            "official_program_coverage_dossiers",
                        ],
                        "official_program_coverage_batch_key": batch.get("official_program_coverage_batch_key"),
                        "queue_key": str(queue_key),
                        "dossier_key": dossier.get("dossier_key") or "",
                        "policy": {
                            "non_mutating": True,
                            "coverage_truth_requires_source_or_reviewer_gate": True,
                            "accepted_alias_monitor_rows_do_not_mutate_roster_truth": True,
                        },
                    }
                ),
                "generated_at": "",
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            rows.append({field: row[field] for field in FIELDS})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_program_coverage_batch_packets")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO official_program_coverage_batch_packets ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "packet_rows": len(rows),
        "batch_count": len({row["official_program_coverage_batch_key"] for row in rows}),
        "queue_count": len({row["queue_key"] for row in rows}),
        "program_count": len({row["official_program_key"] for row in rows if row["official_program_key"]}),
        "person_impact_count": sum(as_int(row["person_impact_count"]) for row in rows),
        "candidate_source_count": sum(as_int(row["candidate_source_count"]) for row in rows),
        "dossier_packet_rows": sum(1 for row in rows if row["dossier_key"]),
        "accepted_alias_monitor_packet_rows": sum(1 for row in rows if row["support_status"] == "monitor"),
        "by_action_lane": dict(sorted(Counter(row["action_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_blocker_status": dict(sorted(Counter(row["blocker_status"] for row in rows).items())),
        "top_packets": [
            {
                "execution_order": row["execution_order"],
                "official_program_name": row["official_program_name"],
                "official_program_type": row["official_program_type"],
                "action_lane": row["action_lane"],
                "packet_status": row["packet_status"],
                "support_status": row["support_status"],
                "person_impact_count": row["person_impact_count"],
                "candidate_source_count": row["candidate_source_count"],
                "recommended_packet_action": row["recommended_packet_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Official program coverage batch packets are non-mutating support rows over denominator coverage actions; accepted coverage still requires source-backed extraction, accepted alias mapping, or explicit denominator closure evidence.",
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
    print(dumps({"official_program_coverage_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
