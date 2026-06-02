#!/usr/bin/env python3
"""Export stable CSV views from the SQLite warehouse."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"


EXPORTS = {
    "people_resolved.csv": """
        SELECT person_key, display_name, role, current_status, institution,
               profile_url, headshot_url, quality_tier
        FROM people
        ORDER BY role, display_name
    """,
    "training_events_resolved.csv": """
        SELECT person_key, display_name, role, event_type, raw_value,
               canonical_name, category, resolver_status, confidence
        FROM v_person_training
        ORDER BY role, display_name, event_type
    """,
    "organizations_resolved.csv": """
        SELECT organization_key, canonical_name, normalized_name, category,
               parent_name, resolver_status, confidence
        FROM organizations
        ORDER BY category, canonical_name
    """,
    "evidence_claims.csv": """
        SELECT e.evidence_id, e.person_key, p.display_name, e.claim_type,
               e.claim_value, e.source_key, e.source_url, e.source_type,
               e.confidence, e.status, e.match_features_json, e.reconciliation_notes
        FROM evidence_claims e
        LEFT JOIN people p ON p.person_key = e.person_key
        ORDER BY e.status, e.source_key, p.display_name, e.claim_type
    """,
    "source_quality_observations.csv": """
        SELECT utility_key, observed_at, sample_size, candidate_claims,
               accepted_claims, rejected_claims, ambiguous_claims, notes, metrics_json
        FROM source_quality_observations
        ORDER BY observed_at, utility_key
    """,
}


def write_csv(conn: sqlite3.Connection, name: str, query: str) -> int:
    rows = conn.execute(query).fetchall()
    path = ARTIFACTS / name
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([description[0] for description in conn.execute(query).description])
        for row in rows:
            writer.writerow(row)
    return len(rows)


def main() -> None:
    conn = sqlite3.connect(DB)
    counts = {name: write_csv(conn, name, query) for name, query in EXPORTS.items()}
    conn.close()
    (ARTIFACTS / "warehouse_exports_summary.json").write_text(
        json.dumps(counts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(counts, sort_keys=True))


if __name__ == "__main__":
    main()
