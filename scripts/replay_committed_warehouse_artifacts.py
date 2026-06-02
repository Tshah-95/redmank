#!/usr/bin/env python3
"""Replay committed flat artifacts into the generated SQLite warehouse.

This is the no-network companion to build_sqlite.py. The base builder creates
core people/source/program tables from committed JSON artifacts. This replay
step restores derived audit and reconciliation ledgers that are also committed
as table-shaped CSV/JSON artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"


CSV_TABLES = [
    ("penn_med_student_source_audit.csv", "medical_student_source_audit"),
    ("organization_identifier_candidates.csv", "organization_identifier_candidates"),
    ("npi_candidate_claims.csv", "npi_candidate_claims"),
    ("npi_source_observations.csv", "npi_source_observations"),
    ("attending_biosketch_bridge_candidates.csv", "attending_biosketch_bridge_candidates"),
    ("attending_trend_reconciliation.csv", "attending_trend_reconciliation"),
    ("program_identifier_source_observations.csv", "program_identifier_source_observations"),
    ("program_identifier_candidates.csv", "program_identifier_candidates"),
    ("program_identifier_reconciliation.csv", "program_identifier_reconciliation"),
    ("official_program_identifiers.csv", "official_program_identifiers"),
    ("program_lifecycle_consistency_audit.csv", "program_lifecycle_consistency_audit"),
    ("hup_gap_reason_audit.csv", "official_program_gap_reason_audit"),
    ("official_gap_roster_reconciliation.csv", "official_gap_roster_reconciliation"),
    ("official_gap_roster_program_resolution.csv", "official_gap_roster_program_resolution"),
    ("official_program_coverage_assurance_audit.csv", "official_program_coverage_assurance_audit"),
    ("official_program_coverage_action_queue.csv", "official_program_coverage_action_queue"),
    ("official_program_alias_review_packets.csv", "official_program_alias_review_packets"),
    ("official_program_alias_reviewer_decisions.csv", "official_program_alias_reviewer_decisions"),
    ("official_program_alias_reviewer_decision_queue.csv", "official_program_alias_reviewer_decision_queue"),
    ("official_program_alias_reviewer_decision_audit.csv", "official_program_alias_reviewer_decision_audit"),
    ("accepted_official_program_alias_mappings.csv", "accepted_official_program_alias_mappings"),
    ("official_program_alias_reconciliation_candidates.csv", "official_program_alias_reconciliation_candidates"),
    ("training_state_machine_audit.csv", "training_state_machine_audit"),
    ("person_training_state_machine_audit.csv", "person_training_state_machine_audit"),
    ("program_training_state_machine_audit.csv", "program_training_state_machine_audit"),
    ("training_state_refresh_expectations.csv", "training_state_refresh_expectations"),
    ("person_refresh_expectations.csv", "person_refresh_expectations"),
    ("program_refresh_expectations.csv", "program_refresh_expectations"),
    ("category_refresh_expectations.csv", "category_refresh_expectations"),
    ("training_lifecycle_assurance_rollups.csv", "training_lifecycle_assurance_rollups"),
    ("training_state_transition_plan.csv", "training_state_transition_plan"),
    ("training_state_transition_plan_rollups.csv", "training_state_transition_plan_rollups"),
    ("training_state_transition_events.csv", "training_state_transition_events"),
    ("training_state_transition_rollups.csv", "training_state_transition_rollups"),
    ("source_utility_scorecard.csv", "source_utility_scorecard"),
    ("warehouse_reproducibility_audit.csv", "warehouse_reproducibility_audit"),
    ("accepted_enrichment_claims.csv", "accepted_enrichment_claims"),
    ("contact_assurance_audit.csv", "contact_assurance_audit"),
    ("attending_trend_review_claims.csv", "attending_trend_review_claims"),
    ("attending_trend_acceptance_audit.csv", "attending_trend_acceptance_audit"),
    ("attending_trend_reviewer_decisions.csv", "attending_trend_reviewer_decisions"),
    ("attending_trend_reviewer_decision_queue.csv", "attending_trend_reviewer_decision_queue"),
    ("attending_trend_reviewer_decision_audit.csv", "attending_trend_reviewer_decision_audit"),
    ("accepted_attending_trend_facts.csv", "accepted_attending_trend_facts"),
    ("attending_trend_review_rollups.csv", "attending_trend_review_rollups"),
]

JSON_TABLES = [
    ("penn_gme_gap_source_probes.json", "official_program_source_probes"),
]


def table_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict], delete_first: bool = True) -> int:
    if delete_first:
        conn.execute(f"DELETE FROM {table}")
    if not rows:
        return 0
    columns = table_columns(conn, table)
    row_columns = [column for column in rows[0].keys() if column in columns]
    if not row_columns:
        raise ValueError(f"{table} has no replayable columns")
    unknown = sorted(set(rows[0].keys()) - set(columns))
    auto_columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})") if row[5]}
    required_missing = [
        column
        for column in columns
        if column not in row_columns
        and column not in auto_columns
    ]
    if unknown:
        raise ValueError(f"{table} artifact has columns not in table: {unknown}")
    if required_missing:
        raise ValueError(f"{table} artifact is missing table columns: {required_missing}")
    placeholders = ", ".join(f":{column}" for column in row_columns)
    column_sql = ", ".join(row_columns)
    prepared_rows = [{column: row.get(column, "") for column in row_columns} for row in rows]
    if table == "contact_assurance_audit":
        for row in prepared_rows:
            if not row.get("person_key"):
                row["person_key"] = None
    conn.executemany(f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})", prepared_rows)
    return len(rows)


def replay_training_state_snapshots(conn: sqlite3.Connection) -> dict[str, int]:
    snapshot_dir = ARTIFACTS / "training_state_snapshots"
    manifests = sorted(snapshot_dir.glob("*.json"))
    conn.execute("DELETE FROM training_state_transition_rollups")
    conn.execute("DELETE FROM training_state_transition_events")
    conn.execute("DELETE FROM training_state_snapshot_rows")
    conn.execute("DELETE FROM training_state_snapshots")
    snapshot_count = 0
    snapshot_row_count = 0
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        conn.execute(
            """
            INSERT INTO training_state_snapshots
            (snapshot_id, created_at, as_of_date, source_export_path, corpus_fingerprint,
             row_count, canonical_key_count, duplicate_canonical_key_count, notes)
            VALUES
            (:snapshot_id, :created_at, :as_of_date, :source_export_path, :corpus_fingerprint,
             :row_count, :canonical_key_count, :duplicate_canonical_key_count, :notes)
            """,
            manifest,
        )
        rows = read_csv_rows(ROOT / manifest["snapshot_csv"])
        for row in rows:
            row["snapshot_id"] = manifest["snapshot_id"]
            row.pop("state_id", None)
        snapshot_row_count += insert_rows(conn, "training_state_snapshot_rows", rows, delete_first=False)
        snapshot_count += 1
    return {
        "training_state_snapshots": snapshot_count,
        "training_state_snapshot_rows": snapshot_row_count,
    }


def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json_rows(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError(f"{path} is not a JSON array")
    return rows


def replay(conn: sqlite3.Connection) -> dict[str, int]:
    counts = {}
    counts.update(replay_training_state_snapshots(conn))
    for filename, table in CSV_TABLES:
        counts[table] = insert_rows(conn, table, read_csv_rows(ARTIFACTS / filename))
    for filename, table in JSON_TABLES:
        counts[table] = insert_rows(conn, table, read_json_rows(ARTIFACTS / filename))
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    with conn:
        counts = replay(conn)
    conn.close()
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
