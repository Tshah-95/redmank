#!/usr/bin/env python3
"""Materialize an audit ledger for executed official roster refresh collectors."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "official_roster_refresh_execution_audit.csv"
JSON_PATH = ARTIFACTS / "official_roster_refresh_execution_audit.json"
SUMMARY_PATH = ARTIFACTS / "official_roster_refresh_execution_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "execution_audit_key",
    "audit_scope",
    "collector_command",
    "source_family",
    "refreshed_at",
    "source_count",
    "sources_attempted",
    "sources_with_records",
    "records_observed",
    "unique_records_observed",
    "preserved_source_count",
    "skipped_source_count",
    "current_snapshot_id",
    "previous_snapshot_id",
    "snapshot_comparison_kind",
    "canonical_state_count",
    "unchanged_state_count",
    "added_state_count",
    "removed_state_count",
    "changed_state_count",
    "execution_status",
    "state_delta_status",
    "evidence_json",
    "acceptance_rule",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_json(path: str) -> dict:
    return json.loads((ARTIFACTS / path).read_text(encoding="utf-8"))


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def execution_key(*parts: object) -> str:
    return "official_roster_refresh_execution_" + sha256_text(dumps(parts))[:20]


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["execution_audit_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["execution_audit_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def snapshot_context() -> dict:
    snapshot = read_json("training_state_snapshot_summary.json")
    diff = read_json("training_state_diff_summary.json")
    change_counts = diff.get("by_change_type") or snapshot.get("by_change_type") or {}
    added = as_int(change_counts.get("added"))
    removed = sum(
        as_int(count)
        for change_type, count in change_counts.items()
        if str(change_type).startswith("removed")
    )
    unchanged = as_int(change_counts.get("unchanged"))
    changed = max(sum(as_int(count) for count in change_counts.values()) - unchanged - added - removed, 0)
    return {
        "current_snapshot_id": snapshot.get("snapshot_id") or "",
        "previous_snapshot_id": snapshot.get("previous_snapshot_id") or "",
        "snapshot_comparison_kind": snapshot.get("snapshot_comparison_kind") or "",
        "canonical_state_count": as_int(snapshot.get("canonical_key_count") or diff.get("new_canonical_keys")),
        "unchanged_state_count": unchanged,
        "added_state_count": added,
        "removed_state_count": removed,
        "changed_state_count": changed,
        "change_counts": change_counts,
    }


def state_delta_status(context: dict) -> str:
    if (
        as_int(context["added_state_count"]) == 0
        and as_int(context["removed_state_count"]) == 0
        and as_int(context["changed_state_count"]) == 0
        and as_int(context["unchanged_state_count"]) > 0
    ):
        return "fresh_refresh_no_state_delta"
    return "fresh_refresh_with_state_delta"


def row_from_summary(
    *,
    audit_scope: str,
    collector_command: str,
    source_family: str,
    refreshed_at: str,
    source_count: int,
    sources_attempted: int,
    sources_with_records: int,
    records_observed: int,
    unique_records_observed: int,
    preserved_source_count: int,
    skipped_source_count: int,
    evidence: dict,
    context: dict,
    generated_at: str,
    existing: dict[str, dict],
) -> dict:
    execution_status = "refresh_executed"
    if preserved_source_count:
        execution_status = "refresh_executed_with_preserved_prior_rows"
    if skipped_source_count and records_observed == 0:
        execution_status = "refresh_executed_no_records"
    row = {
        "execution_audit_key": execution_key(audit_scope, collector_command, refreshed_at, records_observed, context["current_snapshot_id"]),
        "audit_scope": audit_scope,
        "collector_command": collector_command,
        "source_family": source_family,
        "refreshed_at": refreshed_at,
        "source_count": source_count,
        "sources_attempted": sources_attempted,
        "sources_with_records": sources_with_records,
        "records_observed": records_observed,
        "unique_records_observed": unique_records_observed,
        "preserved_source_count": preserved_source_count,
        "skipped_source_count": skipped_source_count,
        "current_snapshot_id": context["current_snapshot_id"],
        "previous_snapshot_id": context["previous_snapshot_id"],
        "snapshot_comparison_kind": context["snapshot_comparison_kind"],
        "canonical_state_count": context["canonical_state_count"],
        "unchanged_state_count": context["unchanged_state_count"],
        "added_state_count": context["added_state_count"],
        "removed_state_count": context["removed_state_count"],
        "changed_state_count": context["changed_state_count"],
        "execution_status": execution_status,
        "state_delta_status": state_delta_status(context),
        "evidence_json": dumps(evidence),
        "acceptance_rule": (
            "Collector execution is public-source observation only. Roster truth changes require the rebuilt "
            "training-state snapshot diff, temporal contracts, and reviewer/expected-transition gates."
        ),
        "generated_at": "",
    }
    row["generated_at"] = stable_generated_at(existing, row, generated_at)
    return row


def build_rows(generated_at: str) -> list[dict]:
    existing = read_existing()
    context = snapshot_context()
    training = read_json("penn_training_summary.json")
    mstp = read_json("penn_mstp_students_summary.json")
    gap = read_json("penn_gme_gap_roster_summary.json")

    rows = [
        row_from_summary(
            audit_scope="main_penn_training_rosters",
            collector_command="python3 scripts/scrape_penn_training.py",
            source_family="official_penn_training_rosters",
            refreshed_at=training.get("generated_at") or "",
            source_count=len(training.get("by_source") or {}),
            sources_attempted=len(training.get("by_source") or {}),
            sources_with_records=sum(1 for count in (training.get("by_source") or {}).values() if as_int(count) > 0),
            records_observed=as_int(training.get("person_records")),
            unique_records_observed=as_int(training.get("unique_person_records")),
            preserved_source_count=as_int(training.get("preserved_source_count")),
            skipped_source_count=0,
            evidence={
                "summary_artifact": "artifacts/data/penn_training_summary.json",
                "source_refresh_status": training.get("source_refresh_status"),
                "by_role_status_unique": training.get("by_role_status_unique"),
                "fields_present": training.get("fields_present"),
            },
            context=context,
            generated_at=generated_at,
            existing=existing,
        ),
        row_from_summary(
            audit_scope="penn_mstp_student_directory",
            collector_command="python3 scripts/scrape_penn_mstp_students.py",
            source_family="official_penn_mstp_student_directory",
            refreshed_at=mstp.get("generated_at") or "",
            source_count=1,
            sources_attempted=1,
            sources_with_records=1 if as_int(mstp.get("student_records")) else 0,
            records_observed=as_int(mstp.get("student_records")),
            unique_records_observed=as_int(mstp.get("student_records")),
            preserved_source_count=0,
            skipped_source_count=0,
            evidence={
                "summary_artifact": "artifacts/data/penn_mstp_students_summary.json",
                "source": mstp.get("source"),
                "fields_present": mstp.get("fields_present"),
            },
            context=context,
            generated_at=generated_at,
            existing=existing,
        ),
        row_from_summary(
            audit_scope="official_hup_gap_roster_sources",
            collector_command="python3 scripts/scrape_penn_gme_gap_rosters.py",
            source_family="official_hup_gap_roster_queue",
            refreshed_at=gap.get("generated_at") or "",
            source_count=as_int(gap.get("sources_attempted")),
            sources_attempted=as_int(gap.get("sources_attempted")),
            sources_with_records=as_int(gap.get("sources_with_records")),
            records_observed=as_int(gap.get("person_records")),
            unique_records_observed=as_int(gap.get("unique_names")),
            preserved_source_count=0,
            skipped_source_count=as_int(gap.get("skipped_already_captured_sources")),
            evidence={
                "summary_artifact": "artifacts/data/penn_gme_gap_roster_summary.json",
                "by_extraction_status": gap.get("by_extraction_status"),
                "by_role": gap.get("by_role"),
                "skipped_sources": gap.get("skipped_sources"),
            },
            context=context,
            generated_at=generated_at,
            existing=existing,
        ),
    ]

    aggregate = row_from_summary(
        audit_scope="official_roster_refresh_aggregate",
        collector_command="multiple_collectors",
        source_family="official_roster_refresh_execution",
        refreshed_at=max(row["refreshed_at"] for row in rows if row["refreshed_at"]),
        source_count=sum(as_int(row["source_count"]) for row in rows),
        sources_attempted=sum(as_int(row["sources_attempted"]) for row in rows),
        sources_with_records=sum(as_int(row["sources_with_records"]) for row in rows),
        records_observed=sum(as_int(row["records_observed"]) for row in rows),
        unique_records_observed=sum(as_int(row["unique_records_observed"]) for row in rows),
        preserved_source_count=sum(as_int(row["preserved_source_count"]) for row in rows),
        skipped_source_count=sum(as_int(row["skipped_source_count"]) for row in rows),
        evidence={
            "collector_audit_keys": [row["execution_audit_key"] for row in rows],
            "snapshot_change_counts": context["change_counts"],
            "policy": "Aggregate counts are summed collector outputs, not deduplicated unique people across source families.",
        },
        context=context,
        generated_at=generated_at,
        existing=existing,
    )
    return rows + [aggregate]


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(rows: list[dict]) -> None:
    conn = sqlite3.connect(DB)
    with conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("DELETE FROM official_roster_refresh_execution_audit")
        placeholders = ", ".join(f":{field}" for field in FIELDS)
        fields = ", ".join(FIELDS)
        conn.executemany(
            f"INSERT OR REPLACE INTO official_roster_refresh_execution_audit ({fields}) VALUES ({placeholders})",
            rows,
        )
    conn.close()


def write_summary(rows: list[dict], generated_at: str) -> None:
    aggregate = next(row for row in rows if row["audit_scope"] == "official_roster_refresh_aggregate")
    summary = {
        "generated_at": generated_at,
        "audit_rows": len(rows),
        "collector_rows": len(rows) - 1,
        "aggregate_records_observed": as_int(aggregate["records_observed"]),
        "aggregate_sources_attempted": as_int(aggregate["sources_attempted"]),
        "aggregate_sources_with_records": as_int(aggregate["sources_with_records"]),
        "aggregate_preserved_source_count": as_int(aggregate["preserved_source_count"]),
        "aggregate_skipped_source_count": as_int(aggregate["skipped_source_count"]),
        "current_snapshot_id": aggregate["current_snapshot_id"],
        "previous_snapshot_id": aggregate["previous_snapshot_id"],
        "snapshot_comparison_kind": aggregate["snapshot_comparison_kind"],
        "canonical_state_count": as_int(aggregate["canonical_state_count"]),
        "unchanged_state_count": as_int(aggregate["unchanged_state_count"]),
        "added_state_count": as_int(aggregate["added_state_count"]),
        "removed_state_count": as_int(aggregate["removed_state_count"]),
        "changed_state_count": as_int(aggregate["changed_state_count"]),
        "state_delta_status": aggregate["state_delta_status"],
        "by_collector": {
            row["collector_command"]: {
                "records_observed": as_int(row["records_observed"]),
                "sources_attempted": as_int(row["sources_attempted"]),
                "sources_with_records": as_int(row["sources_with_records"]),
                "execution_status": row["execution_status"],
            }
            for row in rows
            if row["audit_scope"] != "official_roster_refresh_aggregate"
        },
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "policy": "This ledger records collector execution and state-diff outcome; it does not mutate roster truth.",
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    generated_at = now_utc()
    rows = build_rows(generated_at)
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_db(rows)
    write_summary(rows, generated_at)
    print(dumps({"official_roster_refresh_execution_audit": len(rows), "state_delta_status": rows[-1]["state_delta_status"]}))


if __name__ == "__main__":
    main()
