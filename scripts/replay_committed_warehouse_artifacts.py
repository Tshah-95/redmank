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
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"

csv.field_size_limit(sys.maxsize)


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
    ("program_lifecycle_duration_source_observations.csv", "program_lifecycle_duration_source_observations"),
    ("program_lifecycle_duration_evidence.csv", "program_lifecycle_duration_evidence"),
    ("program_lifecycle_duration_reviewer_decisions.csv", "program_lifecycle_duration_reviewer_decisions"),
    ("program_lifecycle_duration_reviewer_decision_queue.csv", "program_lifecycle_duration_reviewer_decision_queue"),
    ("program_lifecycle_duration_reviewer_decision_audit.csv", "program_lifecycle_duration_reviewer_decision_audit"),
    ("accepted_program_lifecycle_duration_mappings.csv", "accepted_program_lifecycle_duration_mappings"),
    ("hup_gap_reason_audit.csv", "official_program_gap_reason_audit"),
    ("official_gap_roster_reconciliation.csv", "official_gap_roster_reconciliation"),
    ("official_gap_roster_program_resolution.csv", "official_gap_roster_program_resolution"),
    ("penn_gme_gap_source_search_queries.csv", "official_program_source_search_queries"),
    ("penn_gme_gap_source_search_observations.csv", "official_program_source_search_observations"),
    ("official_program_coverage_assurance_audit.csv", "official_program_coverage_assurance_audit"),
    ("official_program_coverage_action_queue.csv", "official_program_coverage_action_queue"),
    ("official_program_coverage_dossiers.csv", "official_program_coverage_dossiers"),
    ("official_program_alias_review_packets.csv", "official_program_alias_review_packets"),
    ("official_program_alias_reviewer_decisions.csv", "official_program_alias_reviewer_decisions"),
    ("official_program_alias_reviewer_decision_queue.csv", "official_program_alias_reviewer_decision_queue"),
    ("official_program_alias_reviewer_decision_audit.csv", "official_program_alias_reviewer_decision_audit"),
    ("accepted_official_program_alias_mappings.csv", "accepted_official_program_alias_mappings"),
    ("official_program_denominator_closure_audit.csv", "official_program_denominator_closure_audit"),
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
    ("training_temporal_contracts.csv", "training_temporal_contracts"),
    ("training_temporal_contract_rollups.csv", "training_temporal_contract_rollups"),
    ("person_training_stage_state.csv", "person_training_stage_state"),
    ("training_stage_state_rollups.csv", "training_stage_state_rollups"),
    ("official_roster_refresh_workbench.csv", "official_roster_refresh_workbench"),
    ("official_roster_refresh_batches.csv", "official_roster_refresh_batches"),
    ("official_roster_refresh_execution_audit.csv", "official_roster_refresh_execution_audit"),
    ("trainee_profile_search_queries.csv", "trainee_profile_search_queries"),
    ("trainee_profile_search_observations.csv", "trainee_profile_search_observations"),
    ("trainee_profile_discovery_candidates.csv", "trainee_profile_discovery_candidates"),
    ("official_profile_discovery_workbench.csv", "official_profile_discovery_workbench"),
    ("official_profile_reobservation_audit.csv", "official_profile_reobservation_audit"),
    ("official_profile_reviewer_decisions.csv", "official_profile_reviewer_decisions"),
    ("official_profile_reviewer_decision_queue.csv", "official_profile_reviewer_decision_queue"),
    ("official_profile_reviewer_decision_audit.csv", "official_profile_reviewer_decision_audit"),
    ("accepted_official_profile_url_facts.csv", "accepted_official_profile_url_facts"),
    ("evidence_temporal_contracts.csv", "evidence_temporal_contracts"),
    ("evidence_temporal_contract_rollups.csv", "evidence_temporal_contract_rollups"),
    ("prior_training_search_queries.csv", "prior_training_search_queries"),
    ("prior_training_search_observations.csv", "prior_training_search_observations"),
    ("prior_training_discovery_candidates.csv", "prior_training_discovery_candidates"),
    ("training_state_transition_events.csv", "training_state_transition_events"),
    ("training_state_transition_rollups.csv", "training_state_transition_rollups"),
    ("person_enrichment_coverage.csv", "person_enrichment_coverage"),
    ("program_enrichment_coverage.csv", "program_enrichment_coverage"),
    ("person_enrichment_queue.csv", "person_enrichment_work_queue"),
    ("person_enrichment_execution_readiness.csv", "person_enrichment_execution_readiness"),
    ("person_enrichment_execution_readiness_rollups.csv", "person_enrichment_execution_readiness_rollups"),
    ("person_enrichment_execution_batches.csv", "person_enrichment_execution_batches"),
    ("person_enrichment_dossiers.csv", "person_enrichment_dossiers"),
    ("person_enrichment_action_packets.csv", "person_enrichment_action_packets"),
    ("person_enrichment_action_batches.csv", "person_enrichment_action_batches"),
    ("person_enrichment_action_batch_members.csv", "person_enrichment_action_batch_members"),
    ("person_enrichment_action_member_execution_decisions.csv", "person_enrichment_action_member_execution_decisions"),
    ("person_enrichment_action_member_execution_queue.csv", "person_enrichment_action_member_execution_queue"),
    ("person_enrichment_action_member_execution_audit.csv", "person_enrichment_action_member_execution_audit"),
    ("person_evidence_reviewer_decisions.csv", "person_evidence_reviewer_decisions"),
    ("person_evidence_reviewer_decision_queue.csv", "person_evidence_reviewer_decision_queue"),
    ("person_evidence_reviewer_decision_audit.csv", "person_evidence_reviewer_decision_audit"),
    ("person_evidence_review_triage.csv", "person_evidence_review_triage"),
    ("person_evidence_review_batches.csv", "person_evidence_review_batches"),
    ("person_evidence_review_batch_packets.csv", "person_evidence_review_batch_packets"),
    ("source_utility_scorecard.csv", "source_utility_scorecard"),
    ("search_utility_assurance.csv", "search_utility_assurance"),
    ("corpus_action_worklist.csv", "corpus_action_worklist"),
    ("warehouse_reproducibility_audit.csv", "warehouse_reproducibility_audit"),
    ("accepted_enrichment_claims.csv", "accepted_enrichment_claims"),
    ("contact_assurance_audit.csv", "contact_assurance_audit"),
    ("contact_verification_contracts.csv", "contact_verification_contracts"),
    ("contact_reobservation_audit.csv", "contact_reobservation_audit"),
    ("contact_verification_reviewer_decisions.csv", "contact_verification_reviewer_decisions"),
    ("contact_verification_reviewer_decision_queue.csv", "contact_verification_reviewer_decision_queue"),
    ("contact_verification_reviewer_decision_audit.csv", "contact_verification_reviewer_decision_audit"),
    ("accepted_verified_contact_facts.csv", "accepted_verified_contact_facts"),
    ("attending_trend_review_claims.csv", "attending_trend_review_claims"),
    ("attending_trend_acceptance_audit.csv", "attending_trend_acceptance_audit"),
    ("attending_trend_reviewer_decisions.csv", "attending_trend_reviewer_decisions"),
    ("attending_trend_reviewer_decision_queue.csv", "attending_trend_reviewer_decision_queue"),
    ("attending_trend_reviewer_decision_audit.csv", "attending_trend_reviewer_decision_audit"),
    ("accepted_attending_trend_facts.csv", "accepted_attending_trend_facts"),
    ("attending_trend_dossiers.csv", "attending_trend_dossiers"),
    ("attending_trend_review_rollups.csv", "attending_trend_review_rollups"),
    ("attending_historical_link_search_queries.csv", "attending_historical_link_search_queries"),
    ("attending_historical_link_search_observations.csv", "attending_historical_link_search_observations"),
    ("attending_historical_link_candidates.csv", "attending_historical_link_candidates"),
    ("attending_trend_discovery_workbench.csv", "attending_trend_discovery_workbench"),
]

JSON_TABLES = [
    ("penn_gme_gap_source_probes.json", "official_program_source_probes"),
]

NULLABLE_REPLAY_COLUMNS = {
    "contact_assurance_audit": {"person_key"},
    "program_lifecycle_consistency_audit": {"matched_program_key", "identifier_key"},
}


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
    prepared_rows = []
    for row in rows:
        prepared = {}
        for column in row_columns:
            value = row.get(column, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, sort_keys=True)
            if column in NULLABLE_REPLAY_COLUMNS.get(table, set()) and value == "":
                value = None
            prepared[column] = value
        prepared_rows.append(prepared)
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


def replay_official_program_source_candidates(conn: sqlite3.Connection) -> int:
    rows = read_json_rows(ARTIFACTS / "penn_gme_gap_source_candidates.json")
    conn.execute("DELETE FROM official_program_source_candidates")
    for row in rows:
        conn.execute(
            """
            INSERT OR REPLACE INTO official_program_source_candidates
            (candidate_key, official_program_key, department, program_type,
             program_name, coverage_status, source_role, candidate_status,
             priority, confidence, candidate_title, candidate_url, http_status,
             roster_term_count, context_term_count, supported_person_structure_count,
             supported_person_structure_types, reasons_json, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["candidate_key"],
                row["official_program_key"],
                row.get("department"),
                row.get("program_type"),
                row.get("program_name"),
                row.get("coverage_status"),
                row.get("source_role"),
                row.get("candidate_status"),
                int(row.get("priority") or 0),
                float(row.get("confidence") or 0.0),
                row.get("candidate_title"),
                row.get("candidate_url"),
                row.get("http_status") if row.get("http_status") != "" else None,
                int(row.get("roster_term_count") or 0),
                int(row.get("context_term_count") or 0),
                int(row.get("supported_person_structure_count") or 0),
                json.dumps(row.get("supported_person_structure_types", []), ensure_ascii=False, sort_keys=True),
                json.dumps(row.get("reasons", []), ensure_ascii=False, sort_keys=True),
                json.dumps(row, ensure_ascii=False, sort_keys=True),
            ),
        )
    return len(rows)


def replay(conn: sqlite3.Connection) -> dict[str, int]:
    counts = {}
    counts.update(replay_training_state_snapshots(conn))
    for filename, table in CSV_TABLES:
        counts[table] = insert_rows(conn, table, read_csv_rows(ARTIFACTS / filename))
    counts["official_program_source_candidates"] = replay_official_program_source_candidates(conn)
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
