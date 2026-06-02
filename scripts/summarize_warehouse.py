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
        "programs",
        "organizations",
        "organization_aliases",
        "organization_identifiers",
        "person_training_events",
        "career_events",
        "person_contacts",
        "evidence_claims",
        "source_quality_observations",
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
    career_event_counts = {
        row["event_type"]: row["count"]
        for row in conn.execute("SELECT event_type, COUNT(*) AS count FROM career_events GROUP BY event_type")
    }
    contact_counts = {
        row["contact_type"]: row["count"]
        for row in conn.execute("SELECT contact_type, COUNT(*) AS count FROM person_contacts GROUP BY contact_type")
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
        "evidence_status_counts": evidence_status_counts,
        "evidence_source_counts": evidence_source_counts,
        "career_event_counts": career_event_counts,
        "contact_counts": contact_counts,
        "organization_category_counts": category_counts,
    }
    (ARTIFACTS / "warehouse_summary.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload["counts"], sort_keys=True))


if __name__ == "__main__":
    main()
