#!/usr/bin/env python3
"""Materialize the next-action queue for non-level-4 official coverage rows."""

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

OUT_CSV = ARTIFACTS / "official_program_coverage_action_queue.csv"
OUT_JSON = ARTIFACTS / "official_program_coverage_action_queue.json"
OUT_SUMMARY = ARTIFACTS / "official_program_coverage_action_queue_summary.json"

FIELDNAMES = [
    "queue_key",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "assurance_status",
    "assurance_level",
    "coverage_status",
    "action_lane",
    "priority",
    "person_impact_count",
    "candidate_source_count",
    "candidate_url",
    "official_program_url",
    "blocker_status",
    "recommended_next_action",
    "review_question",
    "evidence_json",
    "audited_at",
]

csv.field_size_limit(sys.maxsize)


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def existing_rows() -> dict[str, dict]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open(newline="", encoding="utf-8") as handle:
        return {row["queue_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["queue_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("audited_at") or timestamp


def rows_by_key(conn: sqlite3.Connection, query: str, key: str) -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    return {row[key]: dict(row) for row in conn.execute(query)}


def grouped_rows(conn: sqlite3.Connection, query: str, key: str) -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    groups: dict[str, list[dict]] = {}
    for row in conn.execute(query):
        groups.setdefault(row[key], []).append(dict(row))
    return groups


def classify_action(
    row: dict,
    candidate_rows: list[dict],
    gap_reason: dict | None,
    accepted_alias_rows: list[dict],
    closure_rows: list[dict],
) -> tuple[str, str, str, str]:
    assurance_status = row.get("assurance_status") or ""
    coverage_status = row.get("coverage_status") or ""
    if any(closure.get("closure_status") == "denominator_closed_by_accepted_alias_crosswalk" for closure in closure_rows):
        return (
            "accepted_alias_denominator_closed_monitor",
            "accepted_alias_denominator_closed",
            "Retain accepted alias denominator closure and reopen only when source scope, official denominator, or roster evidence changes.",
            "retain_accepted_alias_denominator_closure_and_monitor_future_refresh",
        )
    if accepted_alias_rows and coverage_status == "covered_current_roster":
        return (
            "accepted_alias_denominator_policy",
            "accepted_alias_mapping_not_yet_denominator_closed",
            "Decide whether the accepted official-to-loaded program alias can be promoted into denominator-closed coverage or must remain a non-mutating bridge.",
            "promote_or_crosswalk_accepted_alias_mapping_into_denominator_closure_policy",
        )
    if accepted_alias_rows:
        return (
            "accepted_alias_open_gap_policy",
            "accepted_alias_bridge_exists_but_official_gap_remains_open",
            "Review the accepted alias bridge against the official denominator row and decide whether this closes the gap, needs a section split, or should remain non-mutating evidence.",
            "review_accepted_alias_bridge_before_denominator_closure",
        )
    if assurance_status == "exact_resolution_count_conflict_review":
        return (
            "count_conflict_review",
            "exact_resolution_count_conflict",
            "Compare accepted membership count against the extracted resolved source and decide whether the source is broader, stale, or the accepted count is incomplete.",
            "review_count_conflict_before_denominator_mutation",
        )
    if assurance_status == "alias_method_current_roster_review":
        return (
            "alias_review",
            "covered_by_alias_without_explicit_acceptance",
            "Confirm the matched loaded program is the same official denominator program or split it into narrower official program rows.",
            "accept_or_split_alias_mapping",
        )
    if assurance_status == "open_gap_with_alias_review":
        return (
            "alias_review",
            "open_gap_with_related_loaded_people",
            "Review related loaded people and decide whether this is a true alias, a track split, a role mismatch, or a false relation.",
            "resolve_related_loaded_program_before_gap_closure",
        )
    if coverage_status == "discovered_no_current_roster":
        if candidate_rows:
            return (
                "parser_or_roster_source_review",
                "candidate_source_without_people",
                "Open the candidate URL and determine whether a parser can extract current people or whether the page is context-only.",
                "improve_parser_or_mark_context_only",
            )
        return (
            "official_page_manual_review",
            "official_page_discovered_no_candidate_roster",
            "Review the official program page and department training pages for linked current roster pages.",
            "find_linked_current_roster_or_confirm_no_public_roster",
        )
    if candidate_rows:
        return (
            "source_candidate_probe",
            "not_covered_but_candidate_sources_exist",
            "Probe queued candidate URLs and keep only current roster pages with supported person structure.",
            "probe_candidate_sources_and_extract_supported_rosters",
        )
    if gap_reason and gap_reason.get("top_candidate_url"):
        return (
            "source_candidate_probe",
            "gap_reason_has_candidate_url",
            "Probe the gap-reason candidate URL and classify it as roster, context, alumni, or unsupported.",
            "probe_gap_reason_candidate_url",
        )
    return (
        "broad_source_discovery",
        "no_candidate_source",
        "Search official program URL, department education pages, and public web for a current roster source.",
        "run_broad_official_source_discovery",
    )


def priority_for(row: dict, action_lane: str, person_impact: int, candidate_count: int) -> int:
    base_by_lane = {
        "count_conflict_review": 1000,
        "alias_review": 900,
        "accepted_alias_denominator_policy": 860,
        "accepted_alias_open_gap_policy": 840,
        "accepted_alias_denominator_closed_monitor": 260,
        "parser_or_roster_source_review": 760,
        "source_candidate_probe": 700,
        "official_page_manual_review": 620,
        "broad_source_discovery": 520,
    }
    base = base_by_lane.get(action_lane, 400)
    program_weight = 20 if row.get("official_program_type") == "residency" else 0
    discovery_weight = 15 if row.get("coverage_status") == "not_discovered" else 0
    return base + min(person_impact, 250) + min(candidate_count * 8, 40) + program_weight + discovery_weight


def build_rows(conn: sqlite3.Connection, use_closure: bool = True) -> list[dict]:
    timestamp = now_utc()
    existing = existing_rows()
    programs = rows_by_key(
        conn,
        """
        SELECT official_program_key, program_name, program_type, department, program_url
        FROM official_program_universe
        """,
        "official_program_key",
    )
    assurance_rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM official_program_coverage_assurance_audit
            WHERE assurance_level < 4
            """
        )
    ]
    candidates_by_program = grouped_rows(
        conn,
        """
        SELECT *
        FROM official_program_source_candidates
        ORDER BY priority DESC, confidence DESC, candidate_url
        """,
        "official_program_key",
    )
    gap_reasons = rows_by_key(conn, "SELECT * FROM official_program_gap_reason_audit", "official_program_key")
    aliases_by_program = grouped_rows(conn, "SELECT * FROM official_program_alias_reconciliation_candidates", "official_program_key")
    accepted_aliases_by_program = grouped_rows(
        conn,
        """
        SELECT *
        FROM accepted_official_program_alias_mappings
        ORDER BY official_program_key, loaded_person_count DESC, accepted_alias_key
        """,
        "official_program_key",
    )
    closure_by_program = (
        grouped_rows(
            conn,
            """
            SELECT *
            FROM official_program_denominator_closure_audit
            ORDER BY denominator_closure_allowed DESC, loaded_person_count DESC, closure_key
            """,
            "official_program_key",
        )
        if use_closure
        else {}
    )
    resolutions_by_program = grouped_rows(conn, "SELECT * FROM official_gap_roster_program_resolution", "official_program_key")

    rows = []
    for assurance in assurance_rows:
        official_key = assurance["official_program_key"]
        program = programs.get(official_key, {})
        candidates = candidates_by_program.get(official_key, [])
        gap_reason = gap_reasons.get(official_key, {})
        aliases = aliases_by_program.get(official_key, [])
        accepted_aliases = accepted_aliases_by_program.get(official_key, [])
        closure_rows = closure_by_program.get(official_key, [])
        resolutions = resolutions_by_program.get(official_key, [])
        action_lane, blocker, review_question, action = classify_action(
            assurance, candidates, gap_reason, accepted_aliases, closure_rows
        )
        person_impact = max(
            int(assurance.get("captured_people_count") or 0),
            int(assurance.get("alias_review_person_count") or 0),
            int(assurance.get("resolution_review_record_count") or 0),
            sum(int(row.get("loaded_person_count") or 0) for row in accepted_aliases),
        )
        priority = priority_for(assurance, action_lane, person_impact, len(candidates))
        candidate_url = ""
        if candidates:
            candidate_url = candidates[0].get("candidate_url") or ""
        elif gap_reason:
            candidate_url = gap_reason.get("top_candidate_url") or ""
        evidence = {
            "official_program": program,
            "coverage_assurance": assurance,
            "gap_reason": gap_reason or {},
            "source_candidates": candidates,
            "alias_review_rows": aliases,
            "accepted_alias_mappings": accepted_aliases,
            "denominator_closure_rows": closure_rows,
            "program_resolution_rows": resolutions,
        }
        row = {
            "queue_key": "official_program_coverage_action_" + sha256_text(official_key + "|" + action_lane)[:20],
            "official_program_key": official_key,
            "official_program_name": assurance.get("official_program_name") or program.get("program_name") or "",
            "official_program_type": assurance.get("official_program_type") or program.get("program_type") or "",
            "official_department": assurance.get("official_department") or program.get("department") or "",
            "assurance_status": assurance.get("assurance_status") or "",
            "assurance_level": int(assurance.get("assurance_level") or 0),
            "coverage_status": assurance.get("coverage_status") or "",
            "action_lane": action_lane,
            "priority": priority,
            "person_impact_count": person_impact,
            "candidate_source_count": len(candidates),
            "candidate_url": candidate_url,
            "official_program_url": program.get("program_url") or "",
            "blocker_status": blocker,
            "recommended_next_action": action,
            "review_question": review_question,
            "evidence_json": dumps(evidence),
            "audited_at": "",
        }
        row["audited_at"] = stable_audited_at(existing, row, timestamp)
        rows.append(row)

    return sorted(
        rows,
        key=lambda row: (-row["priority"], -row["person_impact_count"], row["official_department"], row["official_program_name"]),
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    field_sql = ", ".join(FIELDNAMES)
    updates = ", ".join(
        f"{field}=excluded.{field}"
        for field in FIELDNAMES
        if field != "queue_key"
    )
    conn.executemany(
        f"""
        INSERT INTO official_program_coverage_action_queue ({field_sql})
        VALUES ({placeholders})
        ON CONFLICT(queue_key) DO UPDATE SET {updates}
        """,
        rows,
    )
    active_keys = {row["queue_key"] for row in rows}
    stale_keys = [
        row[0]
        for row in conn.execute("SELECT queue_key FROM official_program_coverage_action_queue")
        if row[0] not in active_keys
    ]
    for key in stale_keys:
        conn.execute("DELETE FROM official_program_coverage_action_queue WHERE queue_key = ?", (key,))


def write_summary(rows: list[dict]) -> None:
    by_lane = Counter(row["action_lane"] for row in rows)
    by_blocker = Counter(row["blocker_status"] for row in rows)
    by_level = Counter(str(row["assurance_level"]) for row in rows)
    by_type = Counter(row["official_program_type"] for row in rows)
    payload = {
        "queue_rows": len(rows),
        "total_person_impact_count": sum(row["person_impact_count"] for row in rows),
        "highest_priority": max((row["priority"] for row in rows), default=0),
        "by_action_lane": dict(sorted(by_lane.items())),
        "by_blocker_status": dict(sorted(by_blocker.items())),
        "by_assurance_level": dict(sorted(by_level.items())),
        "by_program_type": dict(sorted(by_type.items())),
        "top_actions": [
            {
                "official_program_name": row["official_program_name"],
                "official_program_type": row["official_program_type"],
                "official_department": row["official_department"],
                "action_lane": row["action_lane"],
                "priority": row["priority"],
                "person_impact_count": row["person_impact_count"],
                "recommended_next_action": row["recommended_next_action"],
                "candidate_url": row["candidate_url"],
            }
            for row in rows[:15]
        ],
        "mutation_policy": "non_mutating_action_queue; actions require source-backed parser output or explicit reviewer acceptance before coverage truth changes",
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    OUT_SUMMARY.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ignore-closure",
        action="store_true",
        help="Build the preliminary alias-review queue before accepted-alias closure is applied.",
    )
    args = parser.parse_args()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    with conn:
        rows = build_rows(conn, use_closure=not args.ignore_closure)
        write_csv(OUT_CSV, rows)
        OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
        write_db(conn, rows)
    conn.close()
    print(dumps({"official_program_coverage_action_queue": len(rows)}))


if __name__ == "__main__":
    main()
