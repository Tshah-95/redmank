#!/usr/bin/env python3
"""Audit accepted alias mappings for official-program denominator closure."""

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

OUT_CSV = ARTIFACTS / "official_program_denominator_closure_audit.csv"
OUT_JSON = ARTIFACTS / "official_program_denominator_closure_audit.json"
OUT_SUMMARY = ARTIFACTS / "official_program_denominator_closure_summary.json"

FIELDS = [
    "closure_key",
    "official_program_key",
    "accepted_alias_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "loaded_program_name",
    "loaded_role",
    "loaded_person_count",
    "coverage_status",
    "assurance_status",
    "closure_status",
    "closure_confidence",
    "denominator_closure_allowed",
    "roster_truth_mutation_allowed",
    "required_next_evidence",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_existing() -> dict[str, dict]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open(newline="", encoding="utf-8") as handle:
        return {row["closure_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["closure_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("audited_at") or timestamp


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def keyed(rows: list[dict], key: str) -> dict[str, dict]:
    return {row.get(key) or "": row for row in rows}


def classify(alias: dict, assurance: dict) -> tuple[str, float, int, str, str]:
    coverage_status = assurance.get("coverage_status") or ""
    assurance_status = assurance.get("assurance_status") or ""
    loaded_people = int(alias.get("loaded_person_count") or 0)
    if coverage_status == "covered_current_roster" and assurance_status == "alias_method_current_roster_review" and loaded_people > 0:
        return (
            "denominator_closed_by_accepted_alias_crosswalk",
            0.9,
            1,
            (
                "Retain accepted alias provenance, loaded roster count, and source URL. Reopen if the official "
                "denominator row, loaded source scope, or current roster source changes."
            ),
            "retain_accepted_alias_denominator_closure_and_monitor_future_refresh",
        )
    if coverage_status != "covered_current_roster":
        return (
            "accepted_alias_bridge_open_gap_review",
            0.62,
            0,
            "Accepted alias bridge exists, but the current coverage audit still marks the official denominator row as open.",
            "review_accepted_alias_bridge_before_denominator_closure",
        )
    return (
        "accepted_alias_requires_denominator_policy_review",
        0.7,
        0,
        "Accepted alias exists, but assurance status is not eligible for denominator closure without policy review.",
        "review_accepted_alias_denominator_policy",
    )


def build_rows(conn: sqlite3.Connection) -> list[dict]:
    timestamp = now_utc()
    existing = read_existing()
    aliases = sqlite_rows(conn, "SELECT * FROM accepted_official_program_alias_mappings ORDER BY official_program_name")
    assurance = keyed(sqlite_rows(conn, "SELECT * FROM official_program_coverage_assurance_audit"), "official_program_key")
    coverage = keyed(sqlite_rows(conn, "SELECT * FROM official_program_coverage_audit"), "official_program_key")
    programs = keyed(sqlite_rows(conn, "SELECT * FROM official_program_universe"), "official_program_key")
    rows = []
    for alias in aliases:
        official_key = alias.get("official_program_key") or ""
        assurance_row = assurance.get(official_key, {})
        coverage_row = coverage.get(official_key, {})
        program_row = programs.get(official_key, {})
        status, confidence, closure_allowed, required, action = classify(alias, assurance_row)
        evidence = {
            "accepted_alias_mapping": alias,
            "coverage_assurance": assurance_row,
            "coverage_audit": coverage_row,
            "official_program": program_row,
            "closure_policy": {
                "denominator_closure_allowed_means": (
                    "The official denominator row can be reported as covered through the accepted alias crosswalk. "
                    "This does not rewrite person program labels or mutate roster truth."
                ),
                "roster_truth_mutation_allowed": 0,
            },
        }
        row = {
            "closure_key": "official_program_denominator_closure_" + sha256_text(alias["accepted_alias_key"])[:20],
            "official_program_key": official_key,
            "accepted_alias_key": alias["accepted_alias_key"],
            "official_program_name": alias.get("official_program_name") or "",
            "official_program_type": alias.get("official_program_type") or "",
            "official_department": alias.get("official_department") or "",
            "loaded_program_name": alias.get("loaded_program_name") or "",
            "loaded_role": alias.get("loaded_role") or "",
            "loaded_person_count": int(alias.get("loaded_person_count") or 0),
            "coverage_status": assurance_row.get("coverage_status") or "",
            "assurance_status": assurance_row.get("assurance_status") or "",
            "closure_status": status,
            "closure_confidence": confidence,
            "denominator_closure_allowed": closure_allowed,
            "roster_truth_mutation_allowed": 0,
            "required_next_evidence": required,
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": "",
        }
        row["audited_at"] = stable_audited_at(existing, row, timestamp)
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_program_denominator_closure_audit")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT INTO official_program_denominator_closure_audit ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict]) -> None:
    by_status = Counter(row["closure_status"] for row in rows)
    by_type = Counter(row["official_program_type"] for row in rows)
    payload = {
        "closure_rows": len(rows),
        "denominator_closed_rows": sum(int(row["denominator_closure_allowed"]) for row in rows),
        "denominator_closed_people_count": sum(
            row["loaded_person_count"] for row in rows if int(row["denominator_closure_allowed"])
        ),
        "roster_truth_mutation_allowed_rows": sum(int(row["roster_truth_mutation_allowed"]) for row in rows),
        "by_closure_status": dict(sorted(by_status.items())),
        "by_program_type": dict(sorted(by_type.items())),
        "policy": (
            "Accepted alias denominator closure is a reporting/crosswalk layer. It can close official denominator "
            "coverage for source-backed reporting, but it does not rewrite people, program labels, or roster truth."
        ),
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    OUT_SUMMARY.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    with sqlite3.connect(DB) as conn:
        rows = build_rows(conn)
        write_csv(OUT_CSV, rows)
        OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
        write_db(conn, rows)
        conn.commit()
    print(dumps({"official_program_denominator_closure_audit": len(rows)}))


if __name__ == "__main__":
    main()
