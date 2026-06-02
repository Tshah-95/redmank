#!/usr/bin/env python3
"""Assign assurance tiers to official HUP program coverage claims."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

OUT_CSV = ARTIFACTS / "official_program_coverage_assurance_audit.csv"
OUT_JSON = ARTIFACTS / "official_program_coverage_assurance_audit.json"
OUT_SUMMARY = ARTIFACTS / "official_program_coverage_assurance_summary.json"

FIELDNAMES = [
    "assurance_key",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "coverage_status",
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
    "assurance_status",
    "assurance_level",
    "denominator_evidence_status",
    "coverage_mutation_allowed",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def existing_rows() -> dict[str, dict]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open(newline="", encoding="utf-8") as handle:
        return {row["assurance_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["assurance_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("audited_at") or timestamp


def rows_by_key(conn: sqlite3.Connection, query: str, key: str) -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    return {row[key]: dict(row) for row in conn.execute(query)}


def grouped_rows(conn: sqlite3.Connection, query: str, key: str) -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in conn.execute(query):
        groups[row[key]].append(dict(row))
    return groups


def classify(row: dict, resolution_rows: list[dict], alias_rows: list[dict]) -> tuple[str, int, str, int, str]:
    coverage_status = row.get("coverage_status") or ""
    captured = int(row.get("captured_people_count") or 0)
    match_method = row.get("match_method") or ""
    match_confidence = float(row.get("match_confidence") or 0)
    resolution_records = sum(int(item.get("records_extracted") or 0) for item in resolution_rows if int(item.get("denominator_mutation_allowed") or 0) == 1)
    resolution_review_records = sum(
        int(item.get("records_extracted") or 0) for item in resolution_rows if int(item.get("denominator_mutation_allowed") or 0) == 0
    )
    alias_people = sum(int(item.get("loaded_person_count") or 0) for item in alias_rows)

    if coverage_status == "covered_current_roster":
        if resolution_records and captured and resolution_records > captured:
            return (
                "exact_resolution_count_conflict_review",
                3,
                "exact_program_resolution_has_broader_count_than_coverage",
                0,
                "Review whether the resolved source is broader than the official program before changing denominator counts.",
            )
        if resolution_records and captured and resolution_records == captured:
            return (
                "exact_resolution_backed_current_roster",
                4,
                "exact_program_resolution_supports_current_roster_count",
                0,
                "Retain coverage claim; reviewer can attach exact resolution evidence to denominator record.",
            )
        if match_method == "normalized_name" and match_confidence >= 0.94 and captured > 0:
            return (
                "direct_normalized_name_current_roster",
                4,
                "direct_program_name_match",
                0,
                "Retain coverage claim and refresh from source on the program clock.",
            )
        if match_method == "alias" and captured > 0:
            return (
                "alias_method_current_roster_review",
                3,
                "coverage_from_alias_match",
                0,
                "Retain as useful coverage, but review alias evidence before using as denominator-closed truth.",
            )
        if captured > 0:
            return (
                "covered_current_roster_unclassified_review",
                2,
                "coverage_claim_needs_source_assurance",
                0,
                "Review source and program mapping before using as denominator-closed truth.",
            )
    if resolution_review_records:
        return (
            "open_gap_with_resolution_review",
            1,
            "resolution_candidate_requires_role_or_scope_review",
            0,
            "Resolve role/scope mismatch before accepting coverage or closing the official gap.",
        )
    if alias_people:
        return (
            "open_gap_with_alias_review",
            1,
            "related_loaded_people_but_alias_unaccepted",
            0,
            "Review related loaded program labels before mutating denominator coverage.",
        )
    if coverage_status == "discovered_no_current_roster":
        return (
            "discovered_source_without_current_roster",
            1,
            "program_page_discovered_no_roster_people",
            0,
            "Improve parser or locate a public current roster source.",
        )
    return (
        "not_discovered_by_current_strategy",
        0,
        "no_public_current_roster_source_discovered",
        0,
        "Broaden source discovery with official program URL, department pages, and public search.",
    )


def build_rows(conn: sqlite3.Connection) -> list[dict]:
    timestamp = now_utc()
    existing = existing_rows()
    programs = rows_by_key(
        conn,
        """
        SELECT official_program_key, program_name, program_type, department, program_url
        FROM official_program_universe
        """,
        "official_program_key",
    )
    coverage = rows_by_key(conn, "SELECT * FROM official_program_coverage_audit", "official_program_key")
    resolutions = grouped_rows(
        conn,
        """
        SELECT *
        FROM official_gap_roster_program_resolution
        """,
        "official_program_key",
    )
    aliases = grouped_rows(
        conn,
        """
        SELECT *
        FROM official_program_alias_reconciliation_candidates
        """,
        "official_program_key",
    )

    rows = []
    for official_key, program in sorted(programs.items(), key=lambda item: (item[1]["department"], item[1]["program_type"], item[1]["program_name"])):
        coverage_row = coverage.get(official_key, {})
        resolution_rows = resolutions.get(official_key, [])
        alias_rows = aliases.get(official_key, [])
        status, level, evidence_status, mutation_allowed, action = classify(coverage_row, resolution_rows, alias_rows)
        resolution_record_count = sum(
            int(item.get("records_extracted") or 0) for item in resolution_rows if int(item.get("denominator_mutation_allowed") or 0) == 1
        )
        resolution_review_record_count = sum(
            int(item.get("records_extracted") or 0) for item in resolution_rows if int(item.get("denominator_mutation_allowed") or 0) == 0
        )
        alias_review_person_count = sum(int(item.get("loaded_person_count") or 0) for item in alias_rows)
        evidence = {
            "official_program": program,
            "coverage_row": coverage_row,
            "program_resolution_rows": resolution_rows,
            "alias_review_rows": alias_rows,
            "policy": {
                "coverage_mutation": "This audit does not mutate official_program_coverage_audit; it classifies assurance for downstream review.",
                "level_4": "Direct normalized-name coverage or exact program-resolution coverage.",
                "level_3": "Useful alias-method coverage requiring review before denominator-closed truth.",
                "level_0_or_1": "Open gap or discovered page without accepted current roster evidence.",
            },
        }
        row = {
            "assurance_key": "official_program_coverage_assurance_" + sha256_text(official_key)[:20],
            "official_program_key": official_key,
            "official_program_name": program.get("program_name") or "",
            "official_program_type": program.get("program_type") or "",
            "official_department": program.get("department") or "",
            "coverage_status": coverage_row.get("coverage_status") or "not_in_coverage_audit",
            "captured_people_count": int(coverage_row.get("captured_people_count") or 0),
            "matched_program_key": coverage_row.get("matched_program_key") or "",
            "matched_program_name": coverage_row.get("matched_program_name") or "",
            "match_method": coverage_row.get("match_method") or "",
            "match_confidence": float(coverage_row.get("match_confidence") or 0),
            "resolution_source_count": len(resolution_rows),
            "resolution_record_count": resolution_record_count,
            "resolution_review_record_count": resolution_review_record_count,
            "alias_review_count": len(alias_rows),
            "alias_review_person_count": alias_review_person_count,
            "assurance_status": status,
            "assurance_level": level,
            "denominator_evidence_status": evidence_status,
            "coverage_mutation_allowed": mutation_allowed,
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": "",
        }
        row["audited_at"] = stable_audited_at(existing, row, timestamp)
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_program_coverage_assurance_audit")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    field_sql = ", ".join(FIELDNAMES)
    db_rows = []
    for row in rows:
        db_row = dict(row)
        for nullable in ("matched_program_key",):
            if not db_row.get(nullable):
                db_row[nullable] = None
        db_rows.append(db_row)
    conn.executemany(
        f"INSERT INTO official_program_coverage_assurance_audit ({field_sql}) VALUES ({placeholders})",
        db_rows,
    )


def write_summary(rows: list[dict]) -> None:
    by_status = Counter(row["assurance_status"] for row in rows)
    by_level = Counter(str(row["assurance_level"]) for row in rows)
    by_evidence_status = Counter(row["denominator_evidence_status"] for row in rows)
    payload = {
        "assurance_rows": len(rows),
        "covered_program_rows": sum(1 for row in rows if row["coverage_status"] == "covered_current_roster"),
        "covered_people_count": sum(row["captured_people_count"] for row in rows if row["coverage_status"] == "covered_current_roster"),
        "level_4_program_rows": sum(1 for row in rows if row["assurance_level"] == 4),
        "level_4_people_count": sum(row["captured_people_count"] for row in rows if row["assurance_level"] == 4),
        "alias_review_program_rows": sum(1 for row in rows if row["assurance_status"] == "alias_method_current_roster_review"),
        "alias_review_people_count": sum(
            row["captured_people_count"] for row in rows if row["assurance_status"] == "alias_method_current_roster_review"
        ),
        "open_gap_rows": sum(1 for row in rows if row["coverage_status"] != "covered_current_roster"),
        "open_gap_with_review_evidence_rows": sum(
            1
            for row in rows
            if row["coverage_status"] != "covered_current_roster"
            and row["assurance_status"] in {"open_gap_with_alias_review", "open_gap_with_resolution_review"}
        ),
        "records_supported_by_exact_resolution": sum(row["resolution_record_count"] for row in rows),
        "records_remaining_resolution_review": sum(row["resolution_review_record_count"] for row in rows),
        "by_assurance_status": dict(sorted(by_status.items())),
        "by_assurance_level": dict(sorted(by_level.items())),
        "by_denominator_evidence_status": dict(sorted(by_evidence_status.items())),
        "mutation_policy": "non_mutating_assurance_audit; coverage_mutation_allowed is reserved for future explicit reviewer acceptance",
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    OUT_SUMMARY.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    conn = sqlite3.connect(DB)
    with conn:
        rows = build_rows(conn)
        write_csv(OUT_CSV, rows)
        OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
        write_db(conn, rows)
    conn.close()
    print(dumps({"official_program_coverage_assurance_audit": len(rows)}))


if __name__ == "__main__":
    main()
