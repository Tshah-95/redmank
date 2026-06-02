#!/usr/bin/env python3
"""Rebuild the local SQLite warehouse from committed artifacts only."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


PIPELINE = [
    ["python3", "scripts/materialize_trainee_profile_claims.py"],
    ["python3", "scripts/build_sqlite.py"],
    ["python3", "scripts/materialize_orcid_work_candidates.py", "--replace-claim-type"],
    ["python3", "scripts/audit_penn_gme_program_coverage.py", "--from-warehouse"],
    ["python3", "scripts/replay_committed_warehouse_artifacts.py"],
    ["python3", "scripts/materialize_program_lifecycle_duration_reviewer_decisions.py"],
    ["python3", "scripts/audit_hup_gap_reasons.py"],
    ["python3", "scripts/audit_reconciliation_decisions.py", "--as-of-year", "2026"],
    ["python3", "scripts/audit_person_evidence_review_packets.py"],
    ["python3", "scripts/audit_enrichment_acceptance.py"],
    ["python3", "scripts/materialize_accepted_enrichment.py"],
    ["python3", "scripts/audit_contact_assurance.py"],
    ["python3", "scripts/materialize_contact_verification_contracts.py", "--as-of-date", "2026-06-02"],
    ["python3", "scripts/materialize_contact_verification_reviewer_decisions.py"],
    ["python3", "scripts/materialize_attending_trend_review_claims.py"],
    ["python3", "scripts/audit_attending_trend_acceptance.py"],
    ["python3", "scripts/materialize_attending_trend_reviewer_decisions.py"],
    ["python3", "scripts/audit_attending_trend_acceptance.py"],
    ["python3", "scripts/materialize_attending_trend_reviewer_decisions.py"],
    ["python3", "scripts/materialize_attending_trend_dossiers.py"],
    ["python3", "scripts/materialize_attending_trend_discovery_workbench.py"],
    ["python3", "scripts/audit_person_evidence_review_packets.py"],
    ["python3", "scripts/materialize_person_evidence_reviewer_decisions.py"],
    ["python3", "scripts/materialize_person_evidence_review_triage.py"],
    ["python3", "scripts/materialize_person_evidence_review_batches.py"],
    ["python3", "scripts/materialize_person_evidence_review_batch_packets.py"],
    ["python3", "scripts/export_warehouse_views.py"],
    ["python3", "scripts/audit_training_state_machine.py", "--as-of-date", "2026-06-02"],
    ["python3", "scripts/audit_longitudinal_change_readiness.py", "--refresh-date", "2027-08-15"],
    ["python3", "scripts/materialize_training_lifecycle_assurance.py"],
    ["python3", "scripts/materialize_training_state_transition_plan.py"],
    ["python3", "scripts/materialize_training_temporal_contracts.py"],
    ["python3", "scripts/materialize_person_training_stage_state.py"],
    ["python3", "scripts/materialize_official_roster_refresh_workbench.py"],
    ["python3", "scripts/materialize_official_roster_refresh_batches.py"],
    ["python3", "scripts/materialize_person_enrichment_dossiers.py"],
    ["python3", "scripts/materialize_training_state_snapshot.py", "--compare-date", "2026-06-02"],
    ["python3", "scripts/diff_training_states.py", "--new", "artifacts/data/training_states_current.csv", "--compare-date", "2026-06-02"],
    ["python3", "scripts/audit_enrichment_coverage.py"],
    ["python3", "scripts/generate_enrichment_queue.py"],
    ["python3", "scripts/materialize_person_enrichment_execution_readiness.py"],
    ["python3", "scripts/materialize_person_enrichment_execution_batches.py"],
    ["python3", "scripts/materialize_official_profile_discovery_workbench.py"],
    ["python3", "scripts/materialize_official_profile_reviewer_decisions.py"],
    ["python3", "scripts/materialize_person_enrichment_action_packets.py"],
    ["python3", "scripts/materialize_person_enrichment_action_batches.py"],
    ["python3", "scripts/materialize_person_enrichment_action_batch_members.py"],
    ["python3", "scripts/materialize_evidence_temporal_contracts.py"],
    ["python3", "scripts/audit_official_gap_roster_reconciliation.py"],
    ["python3", "scripts/audit_official_gap_roster_program_resolution.py"],
    ["python3", "scripts/audit_official_program_coverage_assurance.py"],
    ["python3", "scripts/materialize_official_program_coverage_action_queue.py"],
    ["python3", "scripts/materialize_official_program_alias_review_packets.py"],
    ["python3", "scripts/materialize_official_program_alias_reviewer_decisions.py"],
    ["python3", "scripts/materialize_official_program_coverage_dossiers.py"],
    ["python3", "scripts/export_warehouse_views.py"],
    ["python3", "scripts/audit_warehouse_reproducibility.py"],
    ["python3", "scripts/audit_source_utility_scorecard.py"],
    ["python3", "scripts/materialize_search_utility_assurance.py"],
    ["python3", "scripts/materialize_corpus_action_worklist.py"],
    ["python3", "scripts/materialize_official_roster_refresh_execution_audit.py"],
    ["python3", "scripts/report_source_quality.py"],
    ["python3", "scripts/audit_warehouse_reproducibility.py"],
    ["python3", "scripts/summarize_warehouse.py"],
]


def run(command: list[str], dry_run: bool) -> None:
    print(" ".join(command), flush=True)
    if dry_run:
        return
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for command in PIPELINE:
        run(command, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
