#!/usr/bin/env python3
"""Materialize all-program Penn GME coverage dossiers."""

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

CSV_PATH = ARTIFACTS / "official_program_coverage_dossiers.csv"
JSON_PATH = ARTIFACTS / "official_program_coverage_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "official_program_coverage_dossier_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDNAMES = [
    "dossier_key",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "official_program_url",
    "coverage_status",
    "assurance_status",
    "assurance_level",
    "denominator_status",
    "display_safety_status",
    "coverage_mutation_allowed",
    "captured_people_count",
    "matched_program_key",
    "matched_program_name",
    "match_method",
    "match_confidence",
    "resolution_source_count",
    "resolution_record_count",
    "resolution_review_record_count",
    "alias_review_count",
    "alias_review_person_count",
    "accepted_alias_mapping_count",
    "accepted_alias_people_count",
    "candidate_source_count",
    "roster_candidate_count",
    "context_candidate_count",
    "action_queue_count",
    "top_action_lane",
    "top_blocker_status",
    "top_priority",
    "top_candidate_url",
    "top_candidate_title",
    "missing_evidence_summary",
    "required_next_evidence",
    "recommended_next_action",
    "source_candidate_keys",
    "alias_reconciliation_keys",
    "accepted_alias_keys",
    "action_queue_keys",
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
    return int(value)


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def compact_join(values: list[str], limit: int = 12) -> str:
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= limit:
        return "; ".join(seen)
    return "; ".join(seen[:limit]) + f"; +{len(seen) - limit} more"


def grouped(conn: sqlite3.Connection, query: str, key: str = "official_program_key") -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    output: dict[str, list[dict]] = defaultdict(list)
    for row in conn.execute(query):
        item = dict(row)
        output[item.get(key) or ""].append(item)
    return output


def keyed(conn: sqlite3.Connection, query: str, key: str = "official_program_key") -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    return {row[key]: dict(row) for row in conn.execute(query)}


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["dossier_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["dossier_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def classify(
    assurance: dict,
    candidates: list[dict],
    alias_rows: list[dict],
    accepted_aliases: list[dict],
    action_rows: list[dict],
) -> tuple[str, str, str, str, str]:
    assurance_level = as_int(assurance.get("assurance_level"))
    assurance_status = assurance.get("assurance_status") or ""
    coverage_status = assurance.get("coverage_status") or ""
    mutation_allowed = as_int(assurance.get("coverage_mutation_allowed"))

    if assurance_level >= 4:
        return (
            "denominator_closed_current_roster_evidence",
            "denominator_closed_public_source_backed",
            "",
            "none",
            "retain_closed_denominator_and_refresh_on_program_clock",
        )
    if accepted_aliases and coverage_status == "covered_current_roster":
        return (
            "accepted_alias_denominator_bridge",
            "accepted_alias_public_source_backed",
            "",
            "none",
            "promote_or_crosswalk_accepted_alias_mapping_into_denominator_closure_policy",
        )
    if assurance_level == 3:
        if assurance_status == "exact_resolution_count_conflict_review":
            return (
                "count_conflict_review_required",
                "review_ready_not_denominator_closed",
                "count_conflict_resolution",
                "accepted_count_scope_or_exact_source_scope",
                "review_count_conflict_before_denominator_mutation",
            )
        return (
            "alias_or_scope_review_required",
            "review_ready_not_denominator_closed",
            "explicit_alias_scope_acceptance",
            "official_program_identity_current_roster_and_role_scope_confirmation",
            "accept_or_split_alias_mapping",
        )
    if alias_rows:
        return (
            "open_gap_with_related_loaded_people",
            "related_loaded_people_not_denominator_closed",
            "alias_or_track_scope_decision",
            "official_program_identity_current_roster_and_role_scope_confirmation",
            "resolve_related_loaded_program_before_gap_closure",
        )
    if candidates:
        return (
            "open_gap_with_candidate_sources",
            "candidate_source_not_denominator_closed",
            "current_roster_person_extraction",
            "supported_current_roster_parser_or_context_only_source_decision",
            "probe_candidate_sources_and_extract_supported_rosters",
        )
    if action_rows:
        top_action = sorted(action_rows, key=lambda row: as_int(row.get("priority")), reverse=True)[0]
        return (
            "open_gap_action_required",
            "open_gap_not_denominator_closed",
            top_action.get("blocker_status") or "source_discovery",
            top_action.get("review_question") or "public current roster evidence",
            top_action.get("recommended_next_action") or "run_broad_official_source_discovery",
        )
    if mutation_allowed:
        return (
            "mutation_allowed_review_state",
            "review_ready_not_denominator_closed",
            "",
            "none",
            assurance.get("recommended_next_action") or "review_denominator_evidence",
        )
    return (
        "no_current_public_roster_discovered",
        "no_default_denominator_display",
        "public_current_roster_source",
        "official_program_url_department_training_page_or_web_search_hit",
        "run_broad_official_source_discovery",
    )


def materialize(conn: sqlite3.Connection) -> list[dict]:
    existing = read_existing()
    timestamp = now_utc()
    programs = keyed(
        conn,
        """
        SELECT official_program_key, program_name, program_type, department, program_url, source_url
        FROM official_program_universe
        ORDER BY department, program_type, program_name
        """,
    )
    assurance_by_program = keyed(conn, "SELECT * FROM official_program_coverage_assurance_audit")
    coverage_by_program = keyed(conn, "SELECT * FROM official_program_coverage_audit")
    candidates_by_program = grouped(
        conn,
        """
        SELECT *
        FROM official_program_source_candidates
        ORDER BY official_program_key, priority DESC, confidence DESC, candidate_url
        """,
    )
    alias_by_program = grouped(
        conn,
        """
        SELECT *
        FROM official_program_alias_reconciliation_candidates
        ORDER BY official_program_key, relation_confidence DESC, loaded_person_count DESC
        """,
    )
    accepted_aliases_by_program = grouped(
        conn,
        """
        SELECT *
        FROM accepted_official_program_alias_mappings
        ORDER BY official_program_key, loaded_person_count DESC, accepted_alias_key
        """,
    )
    action_by_program = grouped(
        conn,
        """
        SELECT *
        FROM official_program_coverage_action_queue
        ORDER BY official_program_key, priority DESC, queue_key
        """,
    )
    gap_by_program = keyed(conn, "SELECT * FROM official_program_gap_reason_audit")
    resolutions_by_program = grouped(
        conn,
        """
        SELECT *
        FROM official_gap_roster_program_resolution
        ORDER BY official_program_key, resolution_confidence DESC, records_extracted DESC
        """,
    )

    rows = []
    for official_key, program in programs.items():
        assurance = assurance_by_program.get(official_key, {})
        coverage = coverage_by_program.get(official_key, {})
        candidates = candidates_by_program.get(official_key, [])
        alias_rows = alias_by_program.get(official_key, [])
        accepted_aliases = accepted_aliases_by_program.get(official_key, [])
        action_rows = action_by_program.get(official_key, [])
        gap = gap_by_program.get(official_key, {})
        resolution_rows = resolutions_by_program.get(official_key, [])

        status, display_status, missing, required_next, recommended_next = classify(
            assurance, candidates, alias_rows, accepted_aliases, action_rows
        )
        top_action = sorted(action_rows, key=lambda row: as_int(row.get("priority")), reverse=True)[0] if action_rows else {}
        top_candidate = candidates[0] if candidates else {}
        roster_candidate_count = sum(1 for row in candidates if row.get("candidate_status") == "roster_source_candidate")
        context_candidate_count = sum(1 for row in candidates if row.get("candidate_status") == "program_context_candidate")
        source_candidate_keys = [row.get("candidate_key") or "" for row in candidates]
        alias_keys = [row.get("reconciliation_key") or "" for row in alias_rows]
        accepted_alias_keys = [row.get("accepted_alias_key") or "" for row in accepted_aliases]
        action_keys = [row.get("queue_key") or "" for row in action_rows]

        evidence = {
            "official_program": program,
            "coverage_audit": coverage,
            "coverage_assurance": assurance,
            "gap_reason": gap,
            "source_candidates": candidates,
            "alias_reconciliation_candidates": alias_rows,
            "accepted_alias_mappings": accepted_aliases,
            "action_queue_rows": action_rows,
            "program_resolution_rows": resolution_rows,
            "policy": {
                "dossier": "Non-mutating official-program denominator summary for coverage review and future diffing.",
                "level_4": "Denominator closed by direct current roster or exact resolved roster evidence.",
                "accepted_alias_bridge": "Reviewer-accepted alias is visible, but downstream denominator closure still depends on explicit policy.",
                "review_ready": "Useful evidence exists but denominator coverage is not closed until reviewer or source scope confirms it.",
                "open_gap": "No supported public current roster source has been accepted for this official program.",
            },
        }
        row = {
            "dossier_key": "official_program_coverage_dossier_" + sha256_text(official_key)[:20],
            "official_program_key": official_key,
            "official_program_name": program.get("program_name") or assurance.get("official_program_name") or "",
            "official_program_type": program.get("program_type") or assurance.get("official_program_type") or "",
            "official_department": program.get("department") or assurance.get("official_department") or "",
            "official_program_url": program.get("program_url") or "",
            "coverage_status": assurance.get("coverage_status") or coverage.get("coverage_status") or "not_in_coverage_audit",
            "assurance_status": assurance.get("assurance_status") or "not_in_coverage_assurance",
            "assurance_level": as_int(assurance.get("assurance_level")),
            "denominator_status": status,
            "display_safety_status": display_status,
            "coverage_mutation_allowed": as_int(assurance.get("coverage_mutation_allowed")),
            "captured_people_count": as_int(assurance.get("captured_people_count") or coverage.get("captured_people_count")),
            "matched_program_key": assurance.get("matched_program_key") or coverage.get("matched_program_key") or "",
            "matched_program_name": assurance.get("matched_program_name") or coverage.get("matched_program_name") or "",
            "match_method": assurance.get("match_method") or coverage.get("match_method") or "",
            "match_confidence": as_float(assurance.get("match_confidence") or coverage.get("match_confidence")),
            "resolution_source_count": as_int(assurance.get("resolution_source_count")),
            "resolution_record_count": as_int(assurance.get("resolution_record_count")),
            "resolution_review_record_count": as_int(assurance.get("resolution_review_record_count")),
            "alias_review_count": as_int(assurance.get("alias_review_count")),
            "alias_review_person_count": as_int(assurance.get("alias_review_person_count")),
            "accepted_alias_mapping_count": len(accepted_aliases),
            "accepted_alias_people_count": sum(as_int(row.get("loaded_person_count")) for row in accepted_aliases),
            "candidate_source_count": len(candidates),
            "roster_candidate_count": roster_candidate_count,
            "context_candidate_count": context_candidate_count,
            "action_queue_count": len(action_rows),
            "top_action_lane": top_action.get("action_lane") or "",
            "top_blocker_status": top_action.get("blocker_status") or "",
            "top_priority": as_int(top_action.get("priority")),
            "top_candidate_url": top_candidate.get("candidate_url") or gap.get("top_candidate_url") or top_action.get("candidate_url") or "",
            "top_candidate_title": top_candidate.get("candidate_title") or gap.get("top_candidate_title") or "",
            "missing_evidence_summary": missing,
            "required_next_evidence": required_next,
            "recommended_next_action": recommended_next,
            "source_candidate_keys": compact_join(source_candidate_keys),
            "alias_reconciliation_keys": compact_join(alias_keys),
            "accepted_alias_keys": compact_join(accepted_alias_keys),
            "action_queue_keys": compact_join(action_keys),
            "evidence_json": dumps(evidence),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, timestamp)
        rows.append(row)

    return sorted(rows, key=lambda row: (row["official_department"], row["official_program_type"], row["official_program_name"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_program_coverage_dossiers")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    field_sql = ", ".join(FIELDNAMES)
    conn.executemany(
        f"INSERT INTO official_program_coverage_dossiers ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict]) -> None:
    by_status = Counter(row["denominator_status"] for row in rows)
    by_display = Counter(row["display_safety_status"] for row in rows)
    by_level = Counter(str(row["assurance_level"]) for row in rows)
    by_type = Counter(row["official_program_type"] for row in rows)
    by_department = Counter(row["official_department"] for row in rows)
    closed_rows = [
        row
        for row in rows
        if row["denominator_status"]
        in {
            "denominator_closed_current_roster_evidence",
            "accepted_alias_denominator_bridge",
        }
    ]
    review_rows = [
        row
        for row in rows
        if row["display_safety_status"]
        in {
            "review_ready_not_denominator_closed",
            "related_loaded_people_not_denominator_closed",
            "candidate_source_not_denominator_closed",
        }
    ]
    open_gap_rows = [
        row
        for row in rows
        if row["denominator_status"].startswith("open_gap")
        or row["denominator_status"] == "no_current_public_roster_discovered"
    ]
    no_default_display_rows = [row for row in rows if row["display_safety_status"] == "no_default_denominator_display"]
    payload = {
        "dossier_rows": len(rows),
        "official_program_count": len({row["official_program_key"] for row in rows}),
        "denominator_closed_or_accepted_alias_rows": len(closed_rows),
        "review_or_candidate_rows": len(review_rows),
        "open_gap_rows": len(open_gap_rows),
        "open_gap_no_default_display_rows": len(no_default_display_rows),
        "level_4_rows": sum(1 for row in rows if row["assurance_level"] >= 4),
        "accepted_alias_bridge_rows": sum(1 for row in rows if row["denominator_status"] == "accepted_alias_denominator_bridge"),
        "total_captured_people_count": sum(row["captured_people_count"] for row in rows),
        "total_alias_review_person_count": sum(row["alias_review_person_count"] for row in rows),
        "total_accepted_alias_people_count": sum(row["accepted_alias_people_count"] for row in rows),
        "by_denominator_status": dict(sorted(by_status.items())),
        "by_display_safety_status": dict(sorted(by_display.items())),
        "by_assurance_level": dict(sorted(by_level.items())),
        "by_program_type": dict(sorted(by_type.items())),
        "by_department": dict(sorted(by_department.items())),
        "top_open_or_review_programs": [
            {
                "official_program_name": row["official_program_name"],
                "official_program_type": row["official_program_type"],
                "official_department": row["official_department"],
                "denominator_status": row["denominator_status"],
                "assurance_level": row["assurance_level"],
                "captured_people_count": row["captured_people_count"],
                "alias_review_person_count": row["alias_review_person_count"],
                "accepted_alias_people_count": row["accepted_alias_people_count"],
                "top_priority": row["top_priority"],
                "recommended_next_action": row["recommended_next_action"],
                "top_candidate_url": row["top_candidate_url"],
            }
            for row in sorted(
                [row for row in rows if row["denominator_status"] != "denominator_closed_current_roster_evidence"],
                key=lambda row: (
                    -row["top_priority"],
                    -row["alias_review_person_count"],
                    -row["captured_people_count"],
                    row["official_department"],
                    row["official_program_name"],
                ),
            )[:20]
        ],
        "policy": "Coverage dossiers are non-mutating official-program denominator summaries. They make closed evidence, accepted aliases, review-ready aliases, candidate sources, and open gaps comparable before any coverage truth changes.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    with conn:
        rows = materialize(conn)
        write_csv(CSV_PATH, rows)
        JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
        write_db(conn, rows)
    conn.close()
    print(dumps({"official_program_coverage_dossiers": len(rows)}))


if __name__ == "__main__":
    main()
