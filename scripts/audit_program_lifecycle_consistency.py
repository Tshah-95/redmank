#!/usr/bin/env python3
"""Audit accepted program identifiers against local training-state lifecycle rules."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "program_lifecycle_consistency_audit.csv"
JSON_PATH = ARTIFACTS / "program_lifecycle_consistency_audit.json"
SUMMARY_PATH = ARTIFACTS / "program_lifecycle_consistency_summary.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def key_for(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48]
    return f"{prefix}_{slug}_{digest}" if slug else f"{prefix}_{digest}"


def load_json(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def read_programs(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT
              u.official_program_key,
              u.program_type AS official_program_type,
              u.program_name AS official_program_name,
              a.coverage_status,
              a.matched_program_key,
              a.matched_program_name,
              a.match_method,
              a.match_confidence,
              i.identifier_key,
              i.identifier_type,
              i.identifier_value,
              i.identifier_source,
              i.source_url,
              i.confidence AS identifier_confidence,
              i.accepted_from_candidate_key,
              r.source_program_specialty,
              r.source_program_name,
              r.source_city,
              r.evidence_json AS identifier_reconciliation_evidence_json
            FROM official_program_identifiers i
            JOIN official_program_universe u
              ON u.official_program_key = i.official_program_key
            LEFT JOIN official_program_coverage_audit a
              ON a.official_program_key = u.official_program_key
            LEFT JOIN program_identifier_reconciliation r
              ON r.candidate_key = i.accepted_from_candidate_key
            ORDER BY u.program_type, u.program_name, i.identifier_value
            """
        )
    ]


def state_summary(conn: sqlite3.Connection, matched_program_key: str | None) -> dict:
    if not matched_program_key:
        return {
            "state_rows": 0,
            "coded_state_rows": 0,
            "unclassified_state_rows": 0,
            "lifecycle_codes": [],
            "rule_keys": [],
            "stage_families": [],
            "normalized_stages": [],
            "refresh_policies": [],
            "expected_transition_types": [],
        }
    conn.row_factory = sqlite3.Row
    rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT lifecycle_code, lifecycle_rule_key, stage_family, normalized_stage,
                   refresh_policy, expected_transition_type, COUNT(*) AS count
            FROM person_training_states
            WHERE program_key = ?
            GROUP BY lifecycle_code, lifecycle_rule_key, stage_family,
                     normalized_stage, refresh_policy, expected_transition_type
            ORDER BY count DESC, lifecycle_code, lifecycle_rule_key, normalized_stage
            """,
            (matched_program_key,),
        )
    ]
    state_rows = sum(row["count"] for row in rows)
    unclassified_state_rows = sum(row["count"] for row in rows if not row["lifecycle_code"])
    return {
        "state_rows": state_rows,
        "coded_state_rows": state_rows - unclassified_state_rows,
        "unclassified_state_rows": unclassified_state_rows,
        "lifecycle_codes": sorted({row["lifecycle_code"] or "" for row in rows}),
        "rule_keys": sorted({row["lifecycle_rule_key"] or "" for row in rows}),
        "stage_families": sorted({row["stage_family"] or "" for row in rows}),
        "normalized_stages": sorted({row["normalized_stage"] or "" for row in rows}),
        "refresh_policies": sorted({row["refresh_policy"] or "" for row in rows}),
        "expected_transition_types": sorted({row["expected_transition_type"] or "" for row in rows}),
        "state_summary_rows": rows,
    }


def classify(program: dict, summary: dict) -> tuple[str, str, float, str]:
    coverage_status = program.get("coverage_status") or "unknown"
    state_rows = int(summary["state_rows"])
    lifecycle_codes = [code for code in summary["lifecycle_codes"] if code]
    rule_keys = [key for key in summary["rule_keys"] if key]
    unclassified_state_rows = int(summary.get("unclassified_state_rows", 0))

    if coverage_status != "covered_current_roster":
        return (
            "identifier_accepted_no_current_roster_validation",
            "find_or_refresh_current_roster_before_using_lifecycle_for_diff_mutation",
            0.42,
            "Accepted ACGME identifier exists, but there is no captured current roster program row to validate lifecycle states.",
        )
    if state_rows == 0:
        return (
            "identifier_accepted_missing_training_states",
            "inspect_roster_parser_and_state_extraction_for_matched_program",
            0.35,
            "Official program is covered, but no training-state rows are attached to the matched program.",
        )
    if not lifecycle_codes:
        return (
            "lifecycle_rule_missing_for_state_rows",
            "add_or_review_program_lifecycle_rule_before_annual_diff_use",
            0.4,
            "Matched program has state rows, but no lifecycle code was assigned.",
        )
    if unclassified_state_rows:
        return (
            "mixed_missing_lifecycle_rows_review",
            "classify_unmapped_state_rows_before_auto_advancing_program_rollups",
            0.52,
            "Matched program has a lifecycle code for some state rows but also has unclassified rows; annual diff rollups need a complete state map.",
        )
    if len(lifecycle_codes) > 1:
        return (
            "multiple_lifecycle_codes_for_program_review",
            "split_program_tracks_or_review_label_specific_lifecycle_rules",
            0.55,
            "Matched program has multiple lifecycle codes; this may be valid for label-specific phases but needs review before program-level rollups.",
        )
    code = lifecycle_codes[0]
    if "DURATION_UNKNOWN" in code or any(key.startswith("default_") for key in rule_keys):
        return (
            "accepted_identifier_with_default_or_unknown_lifecycle",
            "source_duration_or_specialty_rule_before_auto_advancing_program_rollups",
            0.58,
            "Accepted ACGME identifier anchors the program, but lifecycle duration is still default or unknown.",
        )
    if program["official_program_type"] == "residency" and "RESIDENCY" not in code and "ANESTHESIA_CA_PHASE" not in code:
        return (
            "program_type_lifecycle_family_mismatch_review",
            "review_program_type_role_mapping_before_annual_diff_use",
            0.5,
            "Official residency row is mapped to a non-residency lifecycle family.",
        )
    if program["official_program_type"] == "fellowship" and "FELLOWSHIP" not in code:
        return (
            "program_type_lifecycle_family_mismatch_review",
            "review_program_type_role_mapping_before_annual_diff_use",
            0.5,
            "Official fellowship row is mapped to a non-fellowship lifecycle family.",
        )
    return (
        "accepted_identifier_lifecycle_consistent",
        "use_for_program_level_normalization_and_state_machine_rollups",
        0.84,
        "Accepted ACGME identifier, official coverage mapping, and single non-default lifecycle code agree.",
    )


def audit_rows(conn: sqlite3.Connection, audited_at: str) -> list[dict]:
    rows = []
    for program in read_programs(conn):
        summary = state_summary(conn, program.get("matched_program_key"))
        status, action, confidence, rationale = classify(program, summary)
        lifecycle_codes = [code for code in summary["lifecycle_codes"] if code]
        rule_keys = [key for key in summary["rule_keys"] if key]
        evidence = {
            "coverage": {
                "coverage_status": program.get("coverage_status") or "",
                "matched_program_key": program.get("matched_program_key") or "",
                "matched_program_name": program.get("matched_program_name") or "",
                "match_method": program.get("match_method") or "",
                "match_confidence": program.get("match_confidence") or 0,
            },
            "identifier": {
                "identifier_source": program.get("identifier_source") or "",
                "identifier_confidence": program.get("identifier_confidence") or 0,
                "source_url": program.get("source_url") or "",
                "source_program_name": program.get("source_program_name") or "",
                "source_city": program.get("source_city") or "",
                "reconciliation_evidence": load_json(program.get("identifier_reconciliation_evidence_json")),
            },
            "training_state_summary": summary,
        }
        rows.append(
            {
                "audit_key": key_for("program_lifecycle_consistency", program["identifier_key"]),
                "official_program_key": program["official_program_key"],
                "matched_program_key": program.get("matched_program_key") or "",
                "identifier_key": program["identifier_key"],
                "official_program_type": program["official_program_type"],
                "official_program_name": program["official_program_name"],
                "matched_program_name": program.get("matched_program_name") or "",
                "identifier_type": program["identifier_type"],
                "identifier_value": program["identifier_value"],
                "source_program_specialty": program.get("source_program_specialty") or "",
                "coverage_status": program.get("coverage_status") or "",
                "lifecycle_status": status,
                "recommended_action": action,
                "lifecycle_confidence": confidence,
                "state_row_count": summary["state_rows"],
                "coded_state_row_count": summary["coded_state_rows"],
                "unclassified_state_row_count": summary["unclassified_state_rows"],
                "lifecycle_code_count": len(lifecycle_codes),
                "lifecycle_codes_json": dumps(lifecycle_codes),
                "rule_keys_json": dumps(rule_keys),
                "rationale": rationale,
                "evidence_json": dumps(evidence),
                "audited_at": audited_at,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DROP TABLE IF EXISTS program_lifecycle_consistency_audit")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM program_lifecycle_consistency_audit")
    db_rows = []
    for row in rows:
        db_row = dict(row)
        for nullable_key in ["matched_program_key", "identifier_key"]:
            if not db_row.get(nullable_key):
                db_row[nullable_key] = None
        db_rows.append(db_row)
    conn.executemany(
        """
        INSERT INTO program_lifecycle_consistency_audit
        (audit_key, official_program_key, matched_program_key, identifier_key,
         official_program_type, official_program_name, matched_program_name,
         identifier_type, identifier_value, source_program_specialty, coverage_status,
         lifecycle_status, recommended_action, lifecycle_confidence, state_row_count,
         coded_state_row_count, unclassified_state_row_count, lifecycle_code_count,
         lifecycle_codes_json, rule_keys_json, rationale,
         evidence_json, audited_at)
        VALUES
        (:audit_key, :official_program_key, :matched_program_key, :identifier_key,
         :official_program_type, :official_program_name, :matched_program_name,
         :identifier_type, :identifier_value, :source_program_specialty, :coverage_status,
         :lifecycle_status, :recommended_action, :lifecycle_confidence, :state_row_count,
         :coded_state_row_count, :unclassified_state_row_count, :lifecycle_code_count,
         :lifecycle_codes_json, :rule_keys_json, :rationale,
         :evidence_json, :audited_at)
        """,
        db_rows,
    )
    conn.commit()


def write_outputs(rows: list[dict], audited_at: str) -> dict:
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(dumps(rows) + "\n", encoding="utf-8")
    by_status = Counter(row["lifecycle_status"] for row in rows)
    by_action = Counter(row["recommended_action"] for row in rows)
    by_coverage = Counter(row["coverage_status"] or "unknown" for row in rows)
    summary = {
        "audited_at": audited_at,
        "audit_rows": len(rows),
        "accepted_identifier_rows": len(rows),
        "consistent_lifecycle_rows": by_status.get("accepted_identifier_lifecycle_consistent", 0),
        "review_or_unvalidated_rows": len(rows) - by_status.get("accepted_identifier_lifecycle_consistent", 0),
        "state_rows": sum(int(row["state_row_count"]) for row in rows),
        "coded_state_rows": sum(int(row["coded_state_row_count"]) for row in rows),
        "unclassified_state_rows": sum(int(row["unclassified_state_row_count"]) for row in rows),
        "by_lifecycle_status": dict(sorted(by_status.items())),
        "by_recommended_action": dict(sorted(by_action.items())),
        "by_coverage_status": dict(sorted(by_coverage.items())),
        "csv": "artifacts/data/program_lifecycle_consistency_audit.csv",
        "json": "artifacts/data/program_lifecycle_consistency_audit.json",
        "acceptance_rule": "Use accepted ACGME identifiers for lifecycle rollups only when official coverage mapping and a single non-default lifecycle code agree.",
    }
    SUMMARY_PATH.write_text(dumps(summary) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB))
    args = parser.parse_args()
    audited_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = audit_rows(conn, audited_at)
    write_db(conn, rows)
    conn.close()
    print(dumps(write_outputs(rows, audited_at)))


if __name__ == "__main__":
    main()
