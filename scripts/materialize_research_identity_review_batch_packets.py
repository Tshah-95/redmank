#!/usr/bin/env python3
"""Materialize batch-level packets for research identity review sessions."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "research_identity_review_batch_packets.csv"
JSON_PATH = ARTIFACTS / "research_identity_review_batch_packets.json"
SUMMARY_PATH = ARTIFACTS / "research_identity_review_batch_packet_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "batch_packet_key",
    "review_batch_key",
    "execution_order",
    "review_lane",
    "research_identity_status",
    "role",
    "batch_status",
    "packet_status",
    "ready_to_review",
    "person_count",
    "pending_decision_count",
    "stale_decision_count",
    "accepted_review_count",
    "conflict_member_count",
    "research_candidate_count",
    "review_ready_record_count",
    "scholarly_source_count",
    "non_name_anchor_count",
    "secondary_anchor_count",
    "conflict_count",
    "max_review_priority",
    "min_review_priority",
    "top_source_keys",
    "top_claim_types",
    "source_family_counts_json",
    "identifier_summary_json",
    "decision_status_counts_json",
    "dossier_status_counts_json",
    "top_member_dossiers_json",
    "member_decision_index_json",
    "reviewer_prompt",
    "review_instructions",
    "acceptance_rule",
    "target_decision_artifact",
    "recommended_reviewer_action",
    "support_status",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def load_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["batch_packet_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["batch_packet_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def batch_packet_key(batch: dict) -> str:
    return "research_identity_review_batch_packet_" + sha256_text(batch["review_batch_key"])[:20]


def compact_member(row: dict) -> dict:
    return {
        "dossier_key": row.get("dossier_key") or "",
        "reviewer_decision_key": row.get("reviewer_decision_key") or "",
        "review_batch_member_key": row.get("review_batch_member_key") or "",
        "display_name": row.get("display_name") or "",
        "role": row.get("role") or "",
        "programs": row.get("programs") or "",
        "decision_status": row.get("decision_status") or "",
        "dossier_status": row.get("dossier_status") or "",
        "identity_risk_level": row.get("identity_risk_level") or "",
        "decision_complexity": row.get("decision_complexity") or "",
        "review_priority": as_int(row.get("review_priority")),
        "research_review_ready_count": as_int(row.get("research_review_ready_count")),
        "conflicting_identifier_count": as_int(row.get("conflicting_identifier_count")),
        "best_confidence": round(as_float(row.get("best_confidence")), 3),
        "missing_evidence_summary": row.get("missing_evidence_summary") or "",
        "recommended_reviewer_action": row.get("recommended_reviewer_action") or "",
        "member_fingerprint": row.get("member_fingerprint") or "",
    }


def decision_index(row: dict) -> dict:
    template = load_json(row.get("manual_decision_template_json"), {})
    return {
        "reviewer_decision_key": row.get("reviewer_decision_key") or "",
        "review_batch_member_key": row.get("review_batch_member_key") or "",
        "display_name": row.get("display_name") or "",
        "member_fingerprint": row.get("member_fingerprint") or "",
        "manual_decision_template": template,
    }


def merge_counter(rows: list[dict], json_field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        payload = load_json(row.get(json_field), {})
        if not isinstance(payload, dict):
            continue
        for key, value in payload.items():
            counter[str(key)] += as_int(value)
    return dict(sorted(counter.items()))


def packet_status(batch: dict, dossier_rows: list[dict]) -> str:
    if not dossier_rows:
        return "blocked_missing_reviewer_decision_dossiers"
    pending = [row for row in dossier_rows if row.get("decision_status") == "pending_reviewer_decision"]
    stale = [row for row in dossier_rows if row.get("decision_status") == "stale_decision_evidence_mismatch"]
    if stale:
        return "stale_member_decision_recheck_required"
    if pending and batch.get("review_lane") == "conflict_reconciliation":
        return "ready_for_conflict_packet_review"
    if pending:
        return "ready_for_research_identity_packet_review"
    return "accepted_or_closed_packet_monitor"


def recommended_action(status: str, batch: dict) -> str:
    if status == "blocked_missing_reviewer_decision_dossiers":
        return "materialize_research_identity_reviewer_decision_dossiers_before_batch_review"
    if status == "stale_member_decision_recheck_required":
        return "re_review_stale_member_decisions_before_batch_completion"
    if batch.get("review_lane") == "conflict_reconciliation":
        return "resolve_conflicting_identifiers_or_quarantine_members_before_acceptance"
    if batch.get("review_lane") == "secondary_anchor_collection":
        return "collect_secondary_identity_anchors_or_record_needs_more_evidence"
    if batch.get("review_lane") == "research_relevance_decision":
        return "record_research_relevance_decisions_for_each_member"
    return "record_research_identity_reviewer_decisions_for_packet_members"


def support_status(status: str) -> str:
    if status.startswith("blocked"):
        return "blocked"
    if status.startswith("stale"):
        return "needs_recheck"
    if status.startswith("accepted"):
        return "monitor"
    return "ready"


def load_batches(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM research_identity_review_batches
        ORDER BY execution_order, review_batch_key
        """,
    )


def load_dossiers(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    rows = sqlite_rows(
        conn,
        """
        SELECT *
        FROM research_identity_reviewer_decision_dossiers
        ORDER BY review_batch_key,
                 conflicting_identifier_count DESC,
                 review_priority DESC,
                 research_review_ready_count DESC,
                 display_name
        """,
    )
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["review_batch_key"], []).append(row)
    return grouped


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    rows = []
    dossiers_by_batch = load_dossiers(conn)
    for batch in load_batches(conn):
        dossier_rows = dossiers_by_batch.get(batch["review_batch_key"], [])
        decision_counts = Counter(row.get("decision_status") or "" for row in dossier_rows)
        dossier_counts = Counter(row.get("dossier_status") or "" for row in dossier_rows)
        conflict_members = [row for row in dossier_rows if as_int(row.get("conflicting_identifier_count")) > 0]
        status = packet_status(batch, dossier_rows)
        top_members = [compact_member(row) for row in dossier_rows[:12]]
        member_index = [decision_index(row) for row in dossier_rows]
        evidence = {
            "research_identity_review_batch": {
                key: batch.get(key)
                for key in [
                    "review_batch_key",
                    "execution_order",
                    "research_identity_status",
                    "recommended_review_route",
                    "review_lane",
                    "role",
                    "batch_status",
                    "person_count",
                    "review_ready_record_count",
                    "conflict_count",
                    "target_decision_artifact",
                ]
            },
            "decision_status_counts": dict(sorted(decision_counts.items())),
            "dossier_status_counts": dict(sorted(dossier_counts.items())),
            "top_member_dossiers": top_members,
            "policy": {
                "non_mutating": True,
                "packet_accepts_no_person_facts": True,
                "accepted_review_requires_member_decisions_with_current_fingerprints": True,
                "accepted_person_facts_require_downstream_source_specific_ledgers": True,
            },
        }
        row = {
            "batch_packet_key": batch_packet_key(batch),
            "review_batch_key": batch["review_batch_key"],
            "execution_order": as_int(batch.get("execution_order")),
            "review_lane": batch.get("review_lane") or "",
            "research_identity_status": batch.get("research_identity_status") or "",
            "role": batch.get("role") or "",
            "batch_status": batch.get("batch_status") or "",
            "packet_status": status,
            "ready_to_review": as_int(batch.get("ready_to_review")),
            "person_count": as_int(batch.get("person_count")),
            "pending_decision_count": decision_counts.get("pending_reviewer_decision", 0),
            "stale_decision_count": decision_counts.get("stale_decision_evidence_mismatch", 0),
            "accepted_review_count": decision_counts.get("accepted_research_identity_review_decision", 0),
            "conflict_member_count": len(conflict_members),
            "research_candidate_count": as_int(batch.get("research_candidate_count")),
            "review_ready_record_count": as_int(batch.get("review_ready_record_count")),
            "scholarly_source_count": as_int(batch.get("scholarly_source_count")),
            "non_name_anchor_count": as_int(batch.get("non_name_anchor_count")),
            "secondary_anchor_count": as_int(batch.get("secondary_anchor_count")),
            "conflict_count": as_int(batch.get("conflict_count")),
            "max_review_priority": as_int(batch.get("max_review_priority")),
            "min_review_priority": as_int(batch.get("min_review_priority")),
            "top_source_keys": batch.get("top_source_keys") or "",
            "top_claim_types": batch.get("top_claim_types") or "",
            "source_family_counts_json": dumps(merge_counter(dossier_rows, "source_family_counts_json")),
            "identifier_summary_json": dumps(merge_counter(dossier_rows, "identifier_summary_json")),
            "decision_status_counts_json": dumps(dict(sorted(decision_counts.items()))),
            "dossier_status_counts_json": dumps(dict(sorted(dossier_counts.items()))),
            "top_member_dossiers_json": dumps(top_members),
            "member_decision_index_json": dumps(member_index),
            "reviewer_prompt": batch.get("reviewer_prompt") or "",
            "review_instructions": batch.get("review_instructions") or "",
            "acceptance_rule": batch.get("acceptance_rule") or "",
            "target_decision_artifact": batch.get("target_decision_artifact") or "artifacts/data/research_identity_reviewer_decisions.csv",
            "recommended_reviewer_action": recommended_action(status, batch),
            "support_status": support_status(status),
            "evidence_json": dumps(evidence),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        rows.append({field: row[field] for field in FIELDS})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM research_identity_review_batch_packets")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO research_identity_review_batch_packets ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_packet_rows": len(rows),
        "batch_count": len({row["review_batch_key"] for row in rows}),
        "person_count": sum(as_int(row["person_count"]) for row in rows),
        "pending_decision_count": sum(as_int(row["pending_decision_count"]) for row in rows),
        "conflict_packet_rows": sum(1 for row in rows if as_int(row["conflict_member_count"]) > 0),
        "conflict_member_count": sum(as_int(row["conflict_member_count"]) for row in rows),
        "review_ready_record_count": sum(as_int(row["review_ready_record_count"]) for row in rows),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_review_lane": dict(sorted(Counter(row["review_lane"] for row in rows).items())),
        "top_batch_packets": [
            {
                "execution_order": row["execution_order"],
                "review_lane": row["review_lane"],
                "role": row["role"],
                "person_count": row["person_count"],
                "pending_decision_count": row["pending_decision_count"],
                "conflict_member_count": row["conflict_member_count"],
                "packet_status": row["packet_status"],
                "recommended_reviewer_action": row["recommended_reviewer_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Research identity batch packets are non-mutating reviewer aids over batches and per-member dossiers; accepted person facts still require explicit member decisions and downstream source-specific acceptance ledgers.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = build_rows(conn, generated_at)
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"research_identity_review_batch_packets": len(rows)}))


if __name__ == "__main__":
    main()
