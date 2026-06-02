#!/usr/bin/env python3
"""Materialize strict machine-accepted enrichment claims without mutating roster truth."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "accepted_enrichment_claims.csv"
JSON_PATH = ARTIFACTS / "accepted_enrichment_claims.json"
SUMMARY_PATH = ARTIFACTS / "accepted_enrichment_summary.json"

ACCEPTANCE_STATUS = "machine_acceptance_candidate_cross_source"
ACCEPTANCE_POLICY = (
    "A PubMed article candidate is materialized only when the acceptance audit marks it as "
    "machine_acceptance_candidate_cross_source: review-ready high anchor, confidence >= 0.95, "
    "at least four non-name anchors, and an NPI secondary identity anchor for the same person_key."
)
DISPLAY_SAFETY_STATUS = "accepted_for_enrichment_not_roster_truth"
REQUIRED_FINAL_CHECK = "final_duplicate_author_position_and_same_name_sanity_check"

FIELDNAMES = [
    "accepted_enrichment_key",
    "acceptance_key",
    "person_key",
    "display_name",
    "role",
    "enrichment_type",
    "claim_type",
    "claim_value",
    "source_key",
    "source_url",
    "acceptance_status",
    "assurance_level",
    "confidence",
    "non_name_anchor_count",
    "corroborating_source_count",
    "corroborating_sources_json",
    "anchor_features_json",
    "acceptance_policy",
    "display_safety_status",
    "required_final_check",
    "evidence_json",
    "accepted_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["accepted_enrichment_key"]: row for row in csv.DictReader(handle)}


def stable_accepted_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["accepted_enrichment_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "accepted_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("accepted_at") or timestamp


def enrichment_type_for(claim_type: str) -> str:
    if claim_type.startswith("pubmed_"):
        return "publication"
    if "npi" in claim_type:
        return "identity_anchor"
    if "training" in claim_type or "education" in claim_type:
        return "training_or_education"
    if "contact" in claim_type:
        return "contact"
    return "profile_or_context"


def read_acceptance_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return list(
        conn.execute(
            """
            SELECT acceptance_key, person_key, display_name, role, claim_type,
                   accepted_claim_value, source_key, source_url, acceptance_status,
                   assurance_level, confidence, non_name_anchor_count,
                   corroborating_source_count, corroborating_sources_json,
                   anchor_features_json, evidence_json
            FROM enrichment_acceptance_audit
            WHERE acceptance_status = ?
            ORDER BY display_name, claim_type, accepted_claim_value, acceptance_key
            """,
            (ACCEPTANCE_STATUS,),
        )
    )


def materialize_rows(conn: sqlite3.Connection) -> list[dict]:
    existing = load_existing()
    timestamp = now_utc()
    rows = []
    for source in read_acceptance_rows(conn):
        claim_value = source["accepted_claim_value"] or ""
        key_basis = "|".join([source["acceptance_key"], source["person_key"] or "", source["claim_type"], claim_value])
        row = {
            "accepted_enrichment_key": f"accepted_enrichment_{sha256_text(key_basis)[:20]}",
            "acceptance_key": source["acceptance_key"],
            "person_key": source["person_key"] or "",
            "display_name": source["display_name"],
            "role": source["role"] or "",
            "enrichment_type": enrichment_type_for(source["claim_type"]),
            "claim_type": source["claim_type"],
            "claim_value": claim_value,
            "source_key": source["source_key"] or "",
            "source_url": source["source_url"] or "",
            "acceptance_status": source["acceptance_status"],
            "assurance_level": int(source["assurance_level"] or 0),
            "confidence": float(source["confidence"] or 0.0),
            "non_name_anchor_count": int(source["non_name_anchor_count"] or 0),
            "corroborating_source_count": int(source["corroborating_source_count"] or 0),
            "corroborating_sources_json": source["corroborating_sources_json"] or "[]",
            "anchor_features_json": source["anchor_features_json"] or "[]",
            "acceptance_policy": ACCEPTANCE_POLICY,
            "display_safety_status": DISPLAY_SAFETY_STATUS,
            "required_final_check": REQUIRED_FINAL_CHECK,
            "evidence_json": source["evidence_json"] or "{}",
            "accepted_at": "",
        }
        row["accepted_at"] = stable_accepted_at(existing, row, timestamp)
        rows.append(row)
    return rows


def write_csv(rows: list[dict]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict]) -> None:
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_summary(rows: list[dict]) -> None:
    by_type = Counter(row["enrichment_type"] for row in rows)
    by_claim_type = Counter(row["claim_type"] for row in rows)
    by_role = Counter(row["role"] for row in rows)
    by_person = Counter(row["person_key"] for row in rows)
    payload = {
        "accepted_enrichment_rows": len(rows),
        "accepted_people": len(by_person),
        "acceptance_status": ACCEPTANCE_STATUS,
        "acceptance_policy": ACCEPTANCE_POLICY,
        "display_safety_status": DISPLAY_SAFETY_STATUS,
        "required_final_check": REQUIRED_FINAL_CHECK,
        "by_enrichment_type": dict(sorted(by_type.items())),
        "by_claim_type": dict(sorted(by_claim_type.items())),
        "by_role": dict(sorted(by_role.items())),
        "by_person_key": dict(sorted(by_person.items())),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM accepted_enrichment_claims")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    fields = ", ".join(FIELDNAMES)
    conn.executemany(
        f"INSERT INTO accepted_enrichment_claims ({fields}) VALUES ({placeholders})",
        rows,
    )


def main() -> None:
    conn = sqlite3.connect(DB)
    with conn:
        rows = materialize_rows(conn)
        write_csv(rows)
        write_json(rows)
        write_summary(rows)
        write_db(conn, rows)
    conn.close()
    print(dumps({"accepted_enrichment_claims": len(rows), "accepted_people": len({row["person_key"] for row in rows})}))


if __name__ == "__main__":
    main()
