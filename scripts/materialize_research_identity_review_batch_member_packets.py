#!/usr/bin/env python3
"""Materialize per-member packets for research identity review batches."""

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

CSV_PATH = ARTIFACTS / "research_identity_review_batch_member_packets.csv"
JSON_PATH = ARTIFACTS / "research_identity_review_batch_member_packets.json"
SUMMARY_PATH = ARTIFACTS / "research_identity_review_batch_member_packet_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "member_packet_key",
    "batch_packet_key",
    "review_batch_key",
    "review_batch_member_key",
    "reviewer_decision_key",
    "dossier_key",
    "corroboration_key",
    "execution_order",
    "member_order",
    "person_key",
    "display_name",
    "role",
    "programs",
    "current_training_states",
    "review_lane",
    "research_identity_status",
    "recommended_review_route",
    "batch_status",
    "member_fingerprint",
    "decision_status",
    "queue_status",
    "dossier_status",
    "packet_status",
    "support_status",
    "decision_complexity",
    "identity_risk_level",
    "review_priority",
    "research_candidate_count",
    "research_review_ready_count",
    "accepted_research_count",
    "scholarly_source_count",
    "non_name_anchor_count",
    "secondary_anchor_count",
    "persistent_identifier_count",
    "publication_identifier_count",
    "conflicting_identifier_count",
    "best_confidence",
    "top_source_keys",
    "top_claim_types",
    "source_family_counts_json",
    "identifier_summary_json",
    "required_confirmation_fields",
    "allowed_decisions",
    "manual_decision_template_json",
    "top_claims_json",
    "missing_evidence_summary",
    "required_next_evidence",
    "recommended_reviewer_action",
    "target_decision_artifact",
    "acceptance_boundary",
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


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {row["member_packet_key"]: row for row in read_csv(CSV_PATH) if row.get("member_packet_key")}


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["member_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def member_packet_key(member_key: str) -> str:
    return "research_identity_review_batch_member_packet_" + sha256_text(member_key)[:20]


def fallback_batch_packet_key(batch_key: str) -> str:
    return "research_identity_review_batch_packet_" + sha256_text(batch_key)[:20]


def packet_status(member: dict, dossier: dict) -> str:
    if not dossier:
        return "blocked_missing_reviewer_decision_dossier"
    if dossier.get("decision_status") == "stale_decision_evidence_mismatch":
        return "stale_member_decision_recheck_required"
    if dossier.get("decision_status") == "pending_reviewer_decision":
        if as_int(member.get("conflicting_identifier_count")) > 0:
            return "ready_for_conflict_member_review"
        if member.get("recommended_review_route") == "collect_secondary_identity_anchor":
            return "ready_for_secondary_anchor_collection_decision"
        return "ready_for_research_identity_member_review"
    return "accepted_or_closed_member_monitor"


def support_status(status: str) -> str:
    if status.startswith("blocked"):
        return "blocked"
    if status.startswith("stale"):
        return "needs_recheck"
    if status.startswith("accepted"):
        return "monitor"
    return "ready"


def recommended_action(member: dict, dossier: dict, status: str) -> str:
    if status == "blocked_missing_reviewer_decision_dossier":
        return "materialize_research_identity_reviewer_decision_dossiers_before_member_review"
    if status == "stale_member_decision_recheck_required":
        return "re_review_member_decision_against_current_fingerprint"
    if dossier.get("recommended_reviewer_action"):
        return dossier["recommended_reviewer_action"]
    if as_int(member.get("conflicting_identifier_count")) > 0:
        return "resolve_or_quarantine_conflicting_research_identifiers"
    if member.get("recommended_review_route") == "collect_secondary_identity_anchor":
        return "collect_secondary_identity_anchor_or_record_needs_more_evidence"
    return "record_research_identity_reviewer_decision_with_current_member_fingerprint"


def load_batches(conn: sqlite3.Connection) -> dict[str, dict]:
    return {row["review_batch_key"]: row for row in sqlite_rows(conn, "SELECT * FROM research_identity_review_batches")}


def load_batch_packets(conn: sqlite3.Connection) -> dict[str, dict]:
    return {row["review_batch_key"]: row for row in sqlite_rows(conn, "SELECT * FROM research_identity_review_batch_packets")}


def load_members(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM research_identity_review_batch_members
        ORDER BY execution_order, member_order, review_batch_member_key
        """,
    )


def load_dossiers(conn: sqlite3.Connection) -> dict[str, dict]:
    return {
        row["review_batch_member_key"]: row
        for row in sqlite_rows(conn, "SELECT * FROM research_identity_reviewer_decision_dossiers")
    }


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    batches_by_key = load_batches(conn)
    batch_packets_by_key = load_batch_packets(conn)
    dossiers_by_member = load_dossiers(conn)
    rows = []

    for member in load_members(conn):
        batch = batches_by_key.get(member["review_batch_key"], {})
        batch_packet = batch_packets_by_key.get(member["review_batch_key"], {})
        dossier = dossiers_by_member.get(member["review_batch_member_key"], {})
        status = packet_status(member, dossier)
        target_artifact = batch.get("target_decision_artifact") or "artifacts/data/research_identity_reviewer_decisions.csv"
        row = {
            "member_packet_key": member_packet_key(member["review_batch_member_key"]),
            "batch_packet_key": batch_packet.get("batch_packet_key")
            or fallback_batch_packet_key(member["review_batch_key"]),
            "review_batch_key": member["review_batch_key"],
            "review_batch_member_key": member["review_batch_member_key"],
            "reviewer_decision_key": dossier.get("reviewer_decision_key") or "",
            "dossier_key": dossier.get("dossier_key") or "",
            "corroboration_key": member.get("corroboration_key") or "",
            "execution_order": as_int(member.get("execution_order")),
            "member_order": as_int(member.get("member_order")),
            "person_key": member.get("person_key") or "",
            "display_name": member.get("display_name") or "",
            "role": member.get("role") or "",
            "programs": member.get("programs") or "",
            "current_training_states": member.get("current_training_states") or "",
            "review_lane": batch.get("review_lane") or "",
            "research_identity_status": member.get("research_identity_status") or "",
            "recommended_review_route": member.get("recommended_review_route") or "",
            "batch_status": batch.get("batch_status") or "",
            "member_fingerprint": member.get("member_fingerprint") or dossier.get("member_fingerprint") or "",
            "decision_status": dossier.get("decision_status") or "missing_reviewer_decision_dossier",
            "queue_status": dossier.get("queue_status") or "",
            "dossier_status": dossier.get("dossier_status") or "",
            "packet_status": status,
            "support_status": support_status(status),
            "decision_complexity": dossier.get("decision_complexity") or "",
            "identity_risk_level": dossier.get("identity_risk_level") or "",
            "review_priority": as_int(member.get("review_priority")),
            "research_candidate_count": as_int(member.get("research_candidate_count")),
            "research_review_ready_count": as_int(member.get("research_review_ready_count")),
            "accepted_research_count": as_int(member.get("accepted_research_count")),
            "scholarly_source_count": as_int(member.get("scholarly_source_count")),
            "non_name_anchor_count": as_int(member.get("non_name_anchor_count")),
            "secondary_anchor_count": as_int(member.get("secondary_anchor_count")),
            "persistent_identifier_count": as_int(member.get("persistent_identifier_count")),
            "publication_identifier_count": as_int(member.get("publication_identifier_count")),
            "conflicting_identifier_count": as_int(member.get("conflicting_identifier_count")),
            "best_confidence": round(as_float(member.get("best_confidence")), 3),
            "top_source_keys": member.get("top_source_keys") or "",
            "top_claim_types": member.get("top_claim_types") or "",
            "source_family_counts_json": dossier.get("source_family_counts_json") or "{}",
            "identifier_summary_json": dossier.get("identifier_summary_json") or "{}",
            "required_confirmation_fields": dossier.get("required_confirmation_fields") or "",
            "allowed_decisions": dossier.get("allowed_decisions") or "",
            "manual_decision_template_json": dossier.get("manual_decision_template_json") or "{}",
            "top_claims_json": dossier.get("top_claims_json") or "[]",
            "missing_evidence_summary": dossier.get("missing_evidence_summary") or "",
            "required_next_evidence": member.get("required_next_evidence") or "",
            "recommended_reviewer_action": recommended_action(member, dossier, status),
            "target_decision_artifact": target_artifact,
            "acceptance_boundary": member.get("acceptance_boundary")
            or batch.get("acceptance_rule")
            or "Research identity member packets are non-mutating reviewer aids; accepted facts require explicit decisions and downstream source-specific acceptance ledgers.",
            "evidence_json": dumps(
                {
                    "derived_from": [
                        "research_identity_review_batches",
                        "research_identity_review_batch_packets",
                        "research_identity_review_batch_members",
                        "research_identity_reviewer_decision_dossiers",
                    ],
                    "review_batch_key": member.get("review_batch_key"),
                    "review_batch_member_key": member.get("review_batch_member_key"),
                    "reviewer_decision_key": dossier.get("reviewer_decision_key") or "",
                    "dossier_key": dossier.get("dossier_key") or "",
                    "policy": {
                        "non_mutating": True,
                        "accepted_review_requires_current_member_fingerprint": True,
                        "accepted_person_facts_require_downstream_source_specific_ledgers": True,
                    },
                }
            ),
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
    conn.execute("DELETE FROM research_identity_review_batch_member_packets")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO research_identity_review_batch_member_packets ({field_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "member_packet_rows": len(rows),
        "batch_count": len({row["review_batch_key"] for row in rows}),
        "person_count": len({row["person_key"] for row in rows if row["person_key"]}),
        "review_ready_record_count": sum(as_int(row["research_review_ready_count"]) for row in rows),
        "research_candidate_count": sum(as_int(row["research_candidate_count"]) for row in rows),
        "conflict_member_count": sum(1 for row in rows if as_int(row["conflicting_identifier_count"]) > 0),
        "reviewer_dossier_member_rows": sum(1 for row in rows if row["dossier_key"]),
        "manual_decision_template_rows": sum(1 for row in rows if load_json(row["manual_decision_template_json"], {})),
        "by_review_lane": dict(sorted(Counter(row["review_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_decision_status": dict(sorted(Counter(row["decision_status"] for row in rows).items())),
        "top_member_packets": [
            {
                "execution_order": row["execution_order"],
                "member_order": row["member_order"],
                "display_name": row["display_name"],
                "role": row["role"],
                "review_lane": row["review_lane"],
                "packet_status": row["packet_status"],
                "support_status": row["support_status"],
                "research_review_ready_count": row["research_review_ready_count"],
                "conflicting_identifier_count": row["conflicting_identifier_count"],
                "recommended_reviewer_action": row["recommended_reviewer_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Research identity member packets are non-mutating reviewer aids over current batch-member fingerprints; accepted person facts still require explicit decisions and downstream source-specific acceptance ledgers.",
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
    print(dumps({"research_identity_review_batch_member_packets": len(rows)}))


if __name__ == "__main__":
    main()
