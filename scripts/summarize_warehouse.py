#!/usr/bin/env python3
"""Write warehouse summary counts for the current SQLite database."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    tables = [
        "people",
        "sources",
        "source_utilities",
        "program_lifecycle_rules",
        "programs",
        "organizations",
        "organization_aliases",
        "organization_identifiers",
        "person_training_events",
        "person_training_states",
        "career_events",
        "person_contacts",
        "evidence_claims",
        "source_quality_observations",
        "official_program_universe",
        "official_program_coverage_audit",
        "official_program_source_probes",
        "official_program_source_candidates",
    ]
    counts = {table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] for table in tables}
    resolver_counts = {
        row["resolver_status"]: row["count"]
        for row in conn.execute(
            "SELECT resolver_status, COUNT(*) AS count FROM person_training_events GROUP BY resolver_status"
        )
    }
    evidence_status_counts = {
        row["status"]: row["count"]
        for row in conn.execute("SELECT status, COUNT(*) AS count FROM evidence_claims GROUP BY status")
    }
    evidence_source_counts = {
        row["source_key"]: row["count"]
        for row in conn.execute("SELECT source_key, COUNT(*) AS count FROM evidence_claims GROUP BY source_key")
    }
    role_counts = {
        row["role"]: row["count"]
        for row in conn.execute("SELECT role, COUNT(*) AS count FROM people GROUP BY role")
    }
    generic_program_label_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM person_program_memberships m
        JOIN programs p ON p.program_key = m.program_key
        WHERE p.program_name IN ('Residents', 'Fellows')
        """
    ).fetchone()[0]
    training_state_family_counts = {
        row["stage_family"]: row["count"]
        for row in conn.execute("SELECT stage_family, COUNT(*) AS count FROM person_training_states GROUP BY stage_family")
    }
    normalized_stage_counts = {
        row["normalized_stage"]: row["count"]
        for row in conn.execute(
            "SELECT normalized_stage, COUNT(*) AS count FROM person_training_states GROUP BY normalized_stage"
        )
    }
    lifecycle_code_counts = {
        row["lifecycle_code"] or "none": row["count"]
        for row in conn.execute(
            "SELECT lifecycle_code, COUNT(*) AS count FROM person_training_states GROUP BY lifecycle_code"
        )
    }
    expected_transition_type_counts = {
        row["expected_transition_type"] or "none": row["count"]
        for row in conn.execute(
            """
            SELECT expected_transition_type, COUNT(*) AS count
            FROM person_training_states
            GROUP BY expected_transition_type
            """
        )
    }
    stale_by_next_august_count = conn.execute(
        """
        SELECT COUNT(*)
        FROM person_training_states
        WHERE stale_after_date IS NOT NULL
          AND stale_after_date <= date('now', '+14 months')
        """
    ).fetchone()[0]
    career_event_counts = {
        row["event_type"]: row["count"]
        for row in conn.execute("SELECT event_type, COUNT(*) AS count FROM career_events GROUP BY event_type")
    }
    evidence_reconciliation_queue_counts = {
        f"{row['record_type']}:{row['status']}": row["count"]
        for row in conn.execute(
            """
            SELECT record_type, status, COUNT(*) AS count
            FROM v_evidence_reconciliation_queue
            GROUP BY record_type, status
            """
        )
    }
    evidence_reconciliation_top_claim_counts = {
        row["claim_type"]: row["count"]
        for row in conn.execute(
            """
            SELECT claim_type, COUNT(*) AS count
            FROM v_evidence_reconciliation_queue
            GROUP BY claim_type
            ORDER BY count DESC
            LIMIT 20
            """
        )
    }
    contact_counts = {
        row["contact_type"]: row["count"]
        for row in conn.execute("SELECT contact_type, COUNT(*) AS count FROM person_contacts GROUP BY contact_type")
    }
    official_program_coverage_counts = {
        row["coverage_status"]: row["count"]
        for row in conn.execute(
            "SELECT coverage_status, COUNT(*) AS count FROM official_program_coverage_audit GROUP BY coverage_status"
        )
    }
    official_program_source_candidate_counts = {
        row["candidate_status"]: row["count"]
        for row in conn.execute(
            """
            SELECT candidate_status, COUNT(*) AS count
            FROM official_program_source_candidates
            GROUP BY candidate_status
            """
        )
    }
    category_counts = {
        row["category"]: row["count"]
        for row in conn.execute("SELECT category, COUNT(*) AS count FROM organizations GROUP BY category")
    }
    conn.close()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": str(DB.relative_to(ROOT)),
        "counts": counts,
        "resolver_counts": resolver_counts,
        "role_counts": role_counts,
        "generic_program_label_count": generic_program_label_count,
        "training_state_family_counts": training_state_family_counts,
        "normalized_stage_counts": normalized_stage_counts,
        "lifecycle_code_counts": lifecycle_code_counts,
        "expected_transition_type_counts": expected_transition_type_counts,
        "stale_by_next_august_count": stale_by_next_august_count,
        "evidence_status_counts": evidence_status_counts,
        "evidence_source_counts": evidence_source_counts,
        "career_event_counts": career_event_counts,
        "evidence_reconciliation_queue_counts": evidence_reconciliation_queue_counts,
        "evidence_reconciliation_top_claim_counts": evidence_reconciliation_top_claim_counts,
        "contact_counts": contact_counts,
        "official_program_coverage_counts": official_program_coverage_counts,
        "official_program_source_candidate_counts": official_program_source_candidate_counts,
        "organization_category_counts": category_counts,
    }
    (ARTIFACTS / "warehouse_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
