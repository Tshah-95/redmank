#!/usr/bin/env python3
"""Reconcile extracted HUP gap-roster sources back to official program gaps."""

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

SOURCES_JSON = ARTIFACTS / "penn_gme_gap_roster_sources.json"
SUMMARY_JSON = ARTIFACTS / "penn_gme_gap_roster_summary.json"
OUT_CSV = ARTIFACTS / "official_gap_roster_reconciliation.csv"
OUT_JSON = ARTIFACTS / "official_gap_roster_reconciliation.json"
OUT_SUMMARY = ARTIFACTS / "official_gap_roster_reconciliation_summary.json"

FIELDNAMES = [
    "reconciliation_key",
    "source_key",
    "candidate_key",
    "source_url",
    "effective_url",
    "source_program_name",
    "source_department",
    "extraction_status",
    "records_extracted",
    "loaded_membership_count",
    "loaded_person_count",
    "official_program_key",
    "official_program_name",
    "official_coverage_status",
    "gap_reason_status",
    "source_candidate_status",
    "denominator_link_status",
    "denominator_link_confidence",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_url(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def existing_rows() -> dict[str, dict]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open(newline="", encoding="utf-8") as handle:
        return {row["reconciliation_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["reconciliation_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("audited_at") or timestamp


def rows_by_key(conn: sqlite3.Connection, query: str, key_field: str) -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    return {str(row[key_field] or ""): dict(row) for row in conn.execute(query)}


def official_programs(conn: sqlite3.Connection) -> dict[str, dict]:
    return rows_by_key(
        conn,
        """
        SELECT official_program_key, program_name, department, program_type
        FROM official_program_universe
        """,
        "official_program_key",
    )


def coverage_rows(conn: sqlite3.Connection) -> dict[str, dict]:
    return rows_by_key(
        conn,
        """
        SELECT official_program_key, coverage_status, matched_program_name,
               captured_people_count, match_method, match_confidence
        FROM official_program_coverage_audit
        """,
        "official_program_key",
    )


def gap_reason_rows(conn: sqlite3.Connection) -> dict[str, dict]:
    return rows_by_key(
        conn,
        """
        SELECT official_program_key, gap_reason_status, recommended_next_action,
               related_loaded_person_count, top_candidate_url
        FROM official_program_gap_reason_audit
        """,
        "official_program_key",
    )


def source_candidates(conn: sqlite3.Connection) -> tuple[dict[str, dict], dict[str, dict]]:
    conn.row_factory = sqlite3.Row
    by_key = {}
    by_url = {}
    for row in conn.execute("SELECT * FROM official_program_source_candidates"):
        item = dict(row)
        by_key[item["candidate_key"]] = item
        by_url[normalize_url(item.get("candidate_url"))] = item
    return by_key, by_url


def membership_counts(conn: sqlite3.Connection) -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    counts = {}
    for row in conn.execute(
        """
        SELECT source_key,
               COUNT(*) AS loaded_membership_count,
               COUNT(DISTINCT person_key) AS loaded_person_count
        FROM person_program_memberships
        WHERE source_key IS NOT NULL
        GROUP BY source_key
        """
    ):
        counts[row["source_key"]] = dict(row)
    return counts


def classify(source: dict, official_key: str, candidate: dict | None, skipped_reason: str = "") -> tuple[str, float, str]:
    records = int(source.get("records_extracted") or 0)
    extraction_status = source.get("extraction_status") or skipped_reason or ""
    if skipped_reason == "already_loaded_as_official_roster_source":
        return (
            "skipped_already_loaded_official_source",
            0.86,
            "Retain as already-covered source evidence; review alias mapping only if denominator row remains open.",
        )
    if skipped_reason:
        return (
            "skipped_not_current_gme_roster",
            0.7,
            "Do not count skipped source as current GME roster evidence; keep reason for denominator review.",
        )
    if official_key and records > 0:
        return (
            "records_extracted_with_official_program_key",
            0.92,
            "Review extracted source against official denominator row; if program identity matches, update coverage mapping.",
        )
    if official_key:
        return (
            "official_program_key_no_supported_person_structure",
            0.72,
            "Keep official gap open and improve parser or locate alternate public roster source.",
        )
    if candidate and candidate.get("official_program_key") and records > 0:
        return (
            "records_extracted_linked_by_candidate_url",
            0.84,
            "Review URL-linked candidate against extracted records before denominator coverage mutation.",
        )
    if candidate and candidate.get("official_program_key"):
        return (
            "candidate_url_linked_no_supported_person_structure",
            0.66,
            "Keep official gap open; URL has candidate linkage but parser did not extract current people.",
        )
    if records > 0:
        return (
            "records_extracted_seed_without_denominator_key",
            0.58,
            "Review source/program alias and attach an official_program_key before counting denominator coverage.",
        )
    return (
        "seed_without_denominator_key_no_records",
        0.35,
        "Do not use for denominator coverage until an official program key or current roster structure is found.",
    )


def source_row_for_skipped(item: dict) -> dict:
    url = normalize_url(item.get("candidate_url"))
    return {
        "source_key": "",
        "candidate_key": "",
        "url": url,
        "effective_url": url,
        "program_name": item.get("program_name") or "",
        "department": "",
        "extraction_status": item.get("reason") or "skipped",
        "records_extracted": 0,
        "candidate_title": item.get("candidate_title") or "",
        "official_program_key": "",
    }


def reconciliation_rows(conn: sqlite3.Connection) -> list[dict]:
    sources = read_json(SOURCES_JSON, [])
    summary = read_json(SUMMARY_JSON, {})
    skipped_sources = [source_row_for_skipped(item) for item in summary.get("skipped_sources") or []]
    existing = existing_rows()
    timestamp = now_utc()

    programs = official_programs(conn)
    coverage = coverage_rows(conn)
    gap_reasons = gap_reason_rows(conn)
    candidates_by_key, candidates_by_url = source_candidates(conn)
    counts_by_source = membership_counts(conn)

    rows = []
    for source in [*sources, *skipped_sources]:
        source_url = normalize_url(source.get("url") or source.get("candidate_url"))
        candidate = candidates_by_key.get(source.get("candidate_key") or "") or candidates_by_url.get(source_url)
        official_key = source.get("official_program_key") or (candidate or {}).get("official_program_key") or ""
        skipped_reason = source.get("extraction_status") if str(source.get("extraction_status") or "").startswith("already_") else ""
        status, confidence, action = classify(source, official_key, candidate, skipped_reason=skipped_reason)
        program = programs.get(official_key, {})
        coverage_row = coverage.get(official_key, {})
        gap_row = gap_reasons.get(official_key, {})
        source_key = source.get("source_key") or ""
        membership = counts_by_source.get(source_key, {})
        evidence = {
            "gap_roster_source": source,
            "official_program": program,
            "coverage_row": coverage_row,
            "gap_reason_row": gap_row,
            "matched_source_candidate": candidate or {},
        }
        row = {
            "reconciliation_key": f"official_gap_roster_reconciliation_{sha256_text(source_url + '|' + (source.get('candidate_key') or ''))[:20]}",
            "source_key": source_key,
            "candidate_key": source.get("candidate_key") or (candidate or {}).get("candidate_key") or "",
            "source_url": source_url,
            "effective_url": normalize_url(source.get("effective_url")) or source_url,
            "source_program_name": source.get("program_name") or "",
            "source_department": source.get("department") or "",
            "extraction_status": source.get("extraction_status") or "skipped",
            "records_extracted": int(source.get("records_extracted") or 0),
            "loaded_membership_count": int(membership.get("loaded_membership_count") or 0),
            "loaded_person_count": int(membership.get("loaded_person_count") or 0),
            "official_program_key": official_key,
            "official_program_name": program.get("program_name") or "",
            "official_coverage_status": coverage_row.get("coverage_status") or "",
            "gap_reason_status": gap_row.get("gap_reason_status") or "",
            "source_candidate_status": (candidate or {}).get("candidate_status") or "",
            "denominator_link_status": status,
            "denominator_link_confidence": confidence,
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": "",
        }
        row["audited_at"] = stable_audited_at(existing, row, timestamp)
        rows.append(row)
    return sorted(rows, key=lambda row: (-row["records_extracted"], row["denominator_link_status"], row["source_program_name"], row["source_url"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_gap_roster_reconciliation")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    field_sql = ", ".join(FIELDNAMES)
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if not db_row.get("official_program_key"):
            db_row["official_program_key"] = None
        db_rows.append(db_row)
    conn.executemany(f"INSERT INTO official_gap_roster_reconciliation ({field_sql}) VALUES ({placeholders})", db_rows)


def write_summary(rows: list[dict]) -> None:
    by_status = Counter(row["denominator_link_status"] for row in rows)
    by_extraction = Counter(row["extraction_status"] for row in rows)
    linked_records = sum(
        row["records_extracted"]
        for row in rows
        if row["denominator_link_status"] in {
            "records_extracted_with_official_program_key",
            "records_extracted_linked_by_candidate_url",
        }
    )
    seed_unmapped_records = sum(
        row["records_extracted"]
        for row in rows
        if row["denominator_link_status"] == "records_extracted_seed_without_denominator_key"
    )
    payload = {
        "reconciliation_rows": len(rows),
        "sources_with_records": sum(1 for row in rows if row["records_extracted"] > 0),
        "records_extracted": sum(row["records_extracted"] for row in rows),
        "loaded_membership_count": sum(row["loaded_membership_count"] for row in rows),
        "loaded_person_count": sum(row["loaded_person_count"] for row in rows),
        "official_linked_records_extracted": linked_records,
        "seed_without_denominator_key_records": seed_unmapped_records,
        "by_denominator_link_status": dict(sorted(by_status.items())),
        "by_extraction_status": dict(sorted(by_extraction.items())),
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    OUT_SUMMARY.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    conn = sqlite3.connect(DB)
    with conn:
        rows = reconciliation_rows(conn)
        write_csv(OUT_CSV, rows)
        OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
        write_db(conn, rows)
    conn.close()
    print(dumps({"official_gap_roster_reconciliation": len(rows)}))


if __name__ == "__main__":
    main()
