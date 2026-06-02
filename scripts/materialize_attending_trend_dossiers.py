#!/usr/bin/env python3
"""Materialize group-level recent-attending trend dossiers."""

from __future__ import annotations

import argparse
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

CSV_PATH = ARTIFACTS / "attending_trend_dossiers.csv"
JSON_PATH = ARTIFACTS / "attending_trend_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "attending_trend_dossier_summary.json"

FIELDNAMES = [
    "trend_dossier_key",
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "trend_status",
    "trend_assurance_level",
    "ten_year_trend_window",
    "has_current_attending_endpoint",
    "has_penn_training_claim",
    "has_recent_dated_biosketch_bridge",
    "has_historical_link_candidate",
    "has_current_trainee_name_match",
    "bridge_candidate_count",
    "recent_bridge_candidate_count",
    "non_penn_training_context_count",
    "review_claim_count",
    "reviewer_queue_count",
    "accepted_trend_fact_count",
    "dossier_status",
    "display_safety_status",
    "best_training_type",
    "best_training_line",
    "best_training_start_year",
    "best_training_end_year",
    "best_source_url",
    "accepted_fact_keys",
    "bridge_candidate_keys",
    "reviewer_decision_keys",
    "missing_evidence_summary",
    "required_next_evidence",
    "recommended_next_action",
    "top_source_urls",
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
    return int(value)


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in value.split(";") if part.strip()]


def compact_join(values: list[str], limit: int = 12) -> str:
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    if len(seen) <= limit:
        return "; ".join(seen)
    return "; ".join(seen[:limit]) + f"; +{len(seen) - limit} more"


def grouped(conn: sqlite3.Connection, query: str, key: str = "trend_key") -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    output: dict[str, list[dict]] = defaultdict(list)
    for row in conn.execute(query):
        item = dict(row)
        output[item.get(key) or ""].append(item)
    return output


def read_reconciliation(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM attending_trend_reconciliation
            ORDER BY trend_assurance_level DESC, display_name, trend_key
            """
        )
    ]


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["trend_dossier_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["trend_dossier_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def classify(row: dict, review_claims: list[dict], queue_rows: list[dict], facts: list[dict]) -> tuple[str, str, str]:
    if facts:
        return (
            "accepted_recent_attending_trend_fact",
            "accepted_trend_fact_public_source_backed",
            "retain_accepted_trend_fact_and_monitor_future_refresh",
        )
    if review_claims:
        return (
            "review_ready_recent_attending_trend",
            "review_ready_not_accepted_trend_fact",
            "record_explicit_reviewer_acceptance_or_rejection",
        )
    status = row.get("trend_status") or ""
    if status == "current_endpoint_needs_training_claim":
        return (
            "current_endpoint_missing_training_evidence",
            "endpoint_only_not_trend_ready",
            "collect_dated_penn_training_or_historical_roster_bridge",
        )
    if status == "historical_link_candidate_review":
        return (
            "historical_link_candidate_needs_review",
            "historical_candidate_not_accepted_trend_fact",
            "review_historical_link_candidate_for_identity_training_and_dates",
        )
    if status == "context_only_not_trend_ready":
        return (
            "context_only_not_trend_ready",
            "context_only_not_default_trend_display",
            "deprioritize_until_current_endpoint_or_training_bridge_appears",
        )
    return (
        "trend_group_review_required",
        "review_required_not_accepted_trend_fact",
        "review_trend_reconciliation_inputs",
    )


def missing_summary(row: dict, review_claims: list[dict], facts: list[dict]) -> str:
    missing = []
    if not as_int(row.get("has_current_attending_endpoint")):
        missing.append("current_penn_attending_endpoint")
    if not as_int(row.get("has_penn_training_claim")) and not as_int(row.get("has_recent_dated_biosketch_bridge")):
        missing.append("dated_penn_training_claim")
    if as_int(row.get("has_current_attending_endpoint")) and not review_claims and not facts:
        missing.append("review_ready_bridge_or_training_claim")
    if review_claims and not facts:
        missing.append("explicit_reviewer_acceptance")
    if row.get("ten_year_trend_window") == "unknown":
        missing.append("training_date_window")
    return compact_join(missing)


def materialize(conn: sqlite3.Connection) -> list[dict]:
    existing = read_existing()
    timestamp = now_utc()
    reconciliation_rows = read_reconciliation(conn)
    bridges = grouped(
        conn,
        """
        SELECT *
        FROM attending_biosketch_bridge_candidates
        ORDER BY event_group_key, bridge_assurance_level DESC, end_year DESC
        """,
        key="event_group_key",
    )
    review_claims = grouped(
        conn,
        """
        SELECT *
        FROM attending_trend_review_claims
        ORDER BY trend_key, training_end_year DESC, trend_claim_key
        """,
    )
    acceptances = grouped(
        conn,
        """
        SELECT *
        FROM attending_trend_acceptance_audit
        ORDER BY trend_key, accepted_trend_fact DESC, training_end_year DESC
        """,
    )
    queue = grouped(
        conn,
        """
        SELECT *
        FROM attending_trend_reviewer_decision_queue
        ORDER BY trend_key, queue_status, reviewer_decision_key
        """,
    )
    facts = grouped(
        conn,
        """
        SELECT *
        FROM accepted_attending_trend_facts
        ORDER BY trend_key, training_end_year DESC, trend_fact_key
        """,
    )

    rows = []
    for recon in reconciliation_rows:
        trend_key = recon["trend_key"]
        event_group_key = recon["event_group_key"]
        bridge_rows = bridges.get(event_group_key, [])
        claim_rows = review_claims.get(trend_key, [])
        queue_rows = queue.get(trend_key, [])
        fact_rows = facts.get(trend_key, [])
        acceptance_rows = acceptances.get(trend_key, [])
        dossier_status, display_status, next_action = classify(recon, claim_rows, queue_rows, fact_rows)
        recent_bridges = [
            row for row in bridge_rows if row.get("bridge_status") == "dated_recent_official_biosketch_training_bridge_candidate"
        ]
        non_penn_context = [row for row in bridge_rows if row.get("bridge_status") == "non_penn_training_context"]
        source_urls = []
        source_urls.extend(split_semicolon(recon.get("best_source_url")))
        for row in bridge_rows[:6]:
            source_urls.extend(split_semicolon(row.get("source_url")))
        for row in claim_rows:
            source_urls.extend(split_semicolon(row.get("source_url")))
        for row in fact_rows:
            source_urls.extend(split_semicolon(row.get("source_url")))
        evidence = {
            "reconciliation": recon,
            "biosketch_bridge_candidates": bridge_rows,
            "review_claims": claim_rows,
            "acceptance_audit": acceptance_rows,
            "reviewer_queue": queue_rows,
            "accepted_facts": fact_rows,
            "policy": {
                "non_mutating": True,
                "accepted_trend_fact_requires_explicit_reviewer_decision": True,
                "current_endpoint_without_training_claim_is_not_trend_ready": True,
            },
        }
        row = {
            "trend_dossier_key": "attending_trend_dossier_" + sha256_text(trend_key)[:20],
            "trend_key": trend_key,
            "event_group_key": event_group_key,
            "display_name": recon["display_name"],
            "normalized_name": recon["normalized_name"],
            "trend_status": recon["trend_status"],
            "trend_assurance_level": as_int(recon.get("trend_assurance_level")),
            "ten_year_trend_window": recon.get("ten_year_trend_window") or "",
            "has_current_attending_endpoint": as_int(recon.get("has_current_attending_endpoint")),
            "has_penn_training_claim": as_int(recon.get("has_penn_training_claim")),
            "has_recent_dated_biosketch_bridge": as_int(recon.get("has_recent_dated_biosketch_bridge")),
            "has_historical_link_candidate": as_int(recon.get("has_historical_link_candidate")),
            "has_current_trainee_name_match": as_int(recon.get("has_current_trainee_name_match")),
            "bridge_candidate_count": len(bridge_rows),
            "recent_bridge_candidate_count": len(recent_bridges),
            "non_penn_training_context_count": len(non_penn_context),
            "review_claim_count": len(claim_rows),
            "reviewer_queue_count": len(queue_rows),
            "accepted_trend_fact_count": len(fact_rows),
            "dossier_status": dossier_status,
            "display_safety_status": display_status,
            "best_training_type": recon.get("best_training_type") or "",
            "best_training_line": recon.get("best_training_line") or "",
            "best_training_start_year": recon.get("best_training_start_year") or "",
            "best_training_end_year": recon.get("best_training_end_year") or "",
            "best_source_url": recon.get("best_source_url") or "",
            "accepted_fact_keys": compact_join([row.get("trend_fact_key") or "" for row in fact_rows]),
            "bridge_candidate_keys": compact_join(
                split_semicolon(recon.get("bridge_candidate_keys"))
                + [row.get("candidate_key") or "" for row in bridge_rows]
            ),
            "reviewer_decision_keys": compact_join([row.get("reviewer_decision_key") or "" for row in queue_rows]),
            "missing_evidence_summary": missing_summary(recon, claim_rows, fact_rows),
            "required_next_evidence": recon.get("required_next_evidence") or "",
            "recommended_next_action": next_action,
            "top_source_urls": compact_join(source_urls, limit=8),
            "evidence_json": dumps(evidence),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, timestamp)
        rows.append({field: row[field] for field in FIELDNAMES})
    return rows


def write_csv(rows: list[dict]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict]) -> None:
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM attending_trend_dossiers")
    if not rows:
        return
    fields = ", ".join(FIELDNAMES)
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    conn.executemany(
        f"INSERT OR REPLACE INTO attending_trend_dossiers ({fields}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict]) -> None:
    payload = {
        "dossier_rows": len(rows),
        "event_group_count": len({row["event_group_key"] for row in rows}),
        "accepted_trend_fact_groups": sum(1 for row in rows if int(row["accepted_trend_fact_count"]) > 0),
        "review_ready_groups": sum(1 for row in rows if row["dossier_status"] == "review_ready_recent_attending_trend"),
        "current_endpoint_missing_training_groups": sum(
            1 for row in rows if row["dossier_status"] == "current_endpoint_missing_training_evidence"
        ),
        "context_only_groups": sum(1 for row in rows if row["dossier_status"] == "context_only_not_trend_ready"),
        "ten_year_yes_groups": sum(1 for row in rows if row["ten_year_trend_window"] == "yes"),
        "by_dossier_status": dict(sorted(Counter(row["dossier_status"] for row in rows).items())),
        "by_display_safety_status": dict(sorted(Counter(row["display_safety_status"] for row in rows).items())),
        "by_trend_status": dict(sorted(Counter(row["trend_status"] for row in rows).items())),
        "by_ten_year_trend_window": dict(sorted(Counter(row["ten_year_trend_window"] for row in rows).items())),
        "policy": (
            "Attending trend dossiers are non-mutating group summaries. They separate current endpoint evidence, "
            "Penn training evidence, dated biosketch bridges, review claims, reviewer queues, and accepted trend facts."
        ),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    with conn:
        rows = materialize(conn)
        write_csv(rows)
        write_json(rows)
        write_db(conn, rows)
        write_summary(rows)
    conn.close()
    print(dumps({"attending_trend_dossiers": len(rows)}))


if __name__ == "__main__":
    main()
