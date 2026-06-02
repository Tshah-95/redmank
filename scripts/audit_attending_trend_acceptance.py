#!/usr/bin/env python3
"""Audit review-ready attending trend candidates against explicit acceptance gates."""

from __future__ import annotations

import argparse
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

CSV_PATH = ARTIFACTS / "attending_trend_acceptance_audit.csv"
JSON_PATH = ARTIFACTS / "attending_trend_acceptance_audit.json"
SUMMARY_PATH = ARTIFACTS / "attending_trend_acceptance_summary.json"

REVIEW_READY_DISPLAY_STATUS = "review_ready_not_accepted_trend_fact"
ACCEPTED_DISPLAY_STATUS = "accepted_trend_fact_public_source_backed"
ACCEPTANCE_STATUS_REVIEW = "review_ready_requires_explicit_reviewer_acceptance"
ACCEPTANCE_STATUS_ACCEPTED = "accepted_after_explicit_reviewer_decision"
ACCEPTANCE_BLOCKER = "explicit_reviewer_acceptance_missing"
REQUIRED_REVIEWER_ACTION = (
    "Confirm same-person identity, current Penn endpoint, training line, program type, and dates "
    "before promoting to an accepted trend fact."
)

FIELDNAMES = [
    "trend_acceptance_key",
    "trend_claim_key",
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "trend_claim_type",
    "acceptance_status",
    "accepted_trend_fact",
    "acceptance_level",
    "ten_year_trend_window",
    "training_type",
    "training_line",
    "training_organization",
    "training_start_year",
    "training_end_year",
    "source_key",
    "source_url",
    "source_scope",
    "bridge_candidate_key",
    "identity_check_status",
    "endpoint_check_status",
    "training_line_check_status",
    "date_window_check_status",
    "acceptance_blocker",
    "display_safety_status",
    "required_reviewer_action",
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


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def load_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["trend_acceptance_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["trend_acceptance_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("audited_at") or timestamp


def read_review_claims(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM attending_trend_review_claims
            ORDER BY training_end_year DESC, display_name, trend_claim_key
            """
        )
    ]


def read_accepted_facts(conn: sqlite3.Connection) -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    facts = {}
    for row in conn.execute(
        """
        SELECT *
        FROM accepted_attending_trend_facts
        ORDER BY accepted_at DESC, trend_fact_key
        """
    ):
        fact = dict(row)
        facts[fact["trend_acceptance_key"]] = fact
    return facts


def compact_accepted_fact(fact: dict | None) -> dict:
    if not fact:
        return {}
    return {
        "trend_fact_key": fact.get("trend_fact_key", ""),
        "reviewer_decision_key": fact.get("reviewer_decision_key", ""),
        "trend_acceptance_key": fact.get("trend_acceptance_key", ""),
        "trend_claim_key": fact.get("trend_claim_key", ""),
        "trend_key": fact.get("trend_key", ""),
        "display_name": fact.get("display_name", ""),
        "trend_fact_type": fact.get("trend_fact_type", ""),
        "training_type": fact.get("training_type", ""),
        "training_line": fact.get("training_line", ""),
        "training_organization": fact.get("training_organization", ""),
        "training_start_year": fact.get("training_start_year", ""),
        "training_end_year": fact.get("training_end_year", ""),
        "ten_year_trend_window": fact.get("ten_year_trend_window", ""),
        "source_key": fact.get("source_key", ""),
        "source_url": fact.get("source_url", ""),
        "source_scope": fact.get("source_scope", ""),
        "bridge_candidate_key": fact.get("bridge_candidate_key", ""),
        "claim_fingerprint": fact.get("claim_fingerprint", ""),
        "accepted_by": fact.get("accepted_by", ""),
        "accepted_at": fact.get("accepted_at", ""),
        "display_safety_status": fact.get("display_safety_status", ""),
    }


def check_status(value: bool, ready_status: str = "evidence_present_reviewer_confirmation_required") -> str:
    return ready_status if value else "missing_required_evidence"


def classify(row: dict) -> dict:
    endpoint_ok = bool(int(row.get("has_current_attending_endpoint") or 0))
    bridge_ok = bool(int(row.get("has_recent_dated_biosketch_bridge") or 0))
    training_claim_ok = bool(int(row.get("has_penn_training_claim") or 0)) or bridge_ok
    date_window_ok = row.get("ten_year_trend_window") == "yes" and bool(row.get("training_end_year"))

    if endpoint_ok and training_claim_ok and bridge_ok and date_window_ok:
        return {
            "acceptance_status": ACCEPTANCE_STATUS_REVIEW,
            "accepted_trend_fact": 0,
            "acceptance_level": 4,
            "identity_check_status": "same_person_identity_evidence_present_reviewer_confirmation_required",
            "endpoint_check_status": "current_penn_endpoint_present_reviewer_confirmation_required",
            "training_line_check_status": "dated_penn_training_line_present_reviewer_confirmation_required",
            "date_window_check_status": "recent_ten_year_window_present_reviewer_confirmation_required",
            "acceptance_blocker": ACCEPTANCE_BLOCKER,
            "display_safety_status": REVIEW_READY_DISPLAY_STATUS,
            "recommended_next_action": "record_explicit_reviewer_acceptance_or_rejection",
        }

    blockers = []
    if not endpoint_ok:
        blockers.append("current_penn_endpoint_missing")
    if not training_claim_ok:
        blockers.append("penn_training_evidence_missing")
    if not bridge_ok:
        blockers.append("recent_dated_biosketch_bridge_missing")
    if not date_window_ok:
        blockers.append("ten_year_window_or_training_date_missing")
    return {
        "acceptance_status": "not_acceptance_ready_missing_required_evidence",
        "accepted_trend_fact": 0,
        "acceptance_level": 1,
        "identity_check_status": check_status(training_claim_ok and bridge_ok),
        "endpoint_check_status": check_status(endpoint_ok, "current_penn_endpoint_present_reviewer_confirmation_required"),
        "training_line_check_status": check_status(bridge_ok, "dated_penn_training_line_present_reviewer_confirmation_required"),
        "date_window_check_status": check_status(date_window_ok, "recent_ten_year_window_present_reviewer_confirmation_required"),
        "acceptance_blocker": "; ".join(blockers) or "missing_required_evidence",
        "display_safety_status": "do_not_display_as_trend_fact",
        "recommended_next_action": "collect_required_endpoint_training_or_date_evidence",
    }


def materialize_rows(conn: sqlite3.Connection) -> list[dict]:
    existing = load_existing()
    accepted_facts = read_accepted_facts(conn)
    timestamp = now_utc()
    rows = []
    for claim in read_review_claims(conn):
        classification = classify(claim)
        key_basis = "|".join([claim["trend_claim_key"], claim["trend_key"], claim["event_group_key"]])
        trend_acceptance_key = f"attending_trend_acceptance_{sha256_text(key_basis)[:20]}"
        accepted_fact = accepted_facts.get(trend_acceptance_key)
        if accepted_fact:
            classification = {
                "acceptance_status": ACCEPTANCE_STATUS_ACCEPTED,
                "accepted_trend_fact": 1,
                "acceptance_level": 5,
                "identity_check_status": "same_person_identity_confirmed_by_reviewer_decision",
                "endpoint_check_status": "current_penn_endpoint_confirmed_by_reviewer_decision",
                "training_line_check_status": "dated_penn_training_line_confirmed_by_reviewer_decision",
                "date_window_check_status": "recent_ten_year_window_confirmed_by_reviewer_decision",
                "acceptance_blocker": "none",
                "display_safety_status": ACCEPTED_DISPLAY_STATUS,
                "recommended_next_action": "retain_accepted_trend_fact_and_monitor_future_refresh",
            }
        evidence = {
            "review_claim": claim,
            "parsed_review_claim_evidence": parse_json(claim.get("evidence_json"), {}),
            "accepted_fact": compact_accepted_fact(accepted_fact),
            "acceptance_policy": {
                "accepted_trend_fact_requires": [
                    "same-person identity confirmed",
                    "current Penn attending endpoint confirmed",
                    "dated Penn residency/fellowship/internship training line confirmed",
                    "training end year inside the configured ten-year trend window",
                    "explicit reviewer acceptance decision recorded",
                ],
                "current_materializer_policy": (
                    "Review-ready rows are not promoted to accepted trend facts without an explicit reviewer decision; "
                    "when an accepted fact already exists, this audit reflects the accepted state."
                ),
            },
            "decision_options": [
                "accept_trend_fact",
                "reject_identity_mismatch",
                "reject_not_current_penn_endpoint",
                "reject_training_line_or_date",
                "needs_more_evidence",
            ],
        }
        row = {
            "trend_acceptance_key": trend_acceptance_key,
            "trend_claim_key": claim["trend_claim_key"],
            "trend_key": claim["trend_key"],
            "event_group_key": claim["event_group_key"],
            "display_name": claim["display_name"],
            "normalized_name": claim["normalized_name"],
            "trend_claim_type": claim["trend_claim_type"],
            "acceptance_status": classification["acceptance_status"],
            "accepted_trend_fact": classification["accepted_trend_fact"],
            "acceptance_level": classification["acceptance_level"],
            "ten_year_trend_window": claim["ten_year_trend_window"],
            "training_type": claim.get("training_type") or "",
            "training_line": claim.get("training_line") or "",
            "training_organization": claim.get("training_organization") or "",
            "training_start_year": claim.get("training_start_year") or "",
            "training_end_year": claim.get("training_end_year") or "",
            "source_key": claim.get("source_key") or "",
            "source_url": claim.get("source_url") or "",
            "source_scope": claim.get("source_scope") or "",
            "bridge_candidate_key": claim.get("bridge_candidate_key") or "",
            "identity_check_status": classification["identity_check_status"],
            "endpoint_check_status": classification["endpoint_check_status"],
            "training_line_check_status": classification["training_line_check_status"],
            "date_window_check_status": classification["date_window_check_status"],
            "acceptance_blocker": classification["acceptance_blocker"],
            "display_safety_status": classification["display_safety_status"],
            "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
            "recommended_next_action": classification["recommended_next_action"],
            "evidence_json": dumps(evidence),
            "audited_at": "",
        }
        row["audited_at"] = stable_audited_at(existing, row, timestamp)
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
    conn.execute("DELETE FROM attending_trend_acceptance_audit")
    if not rows:
        return
    fields = ", ".join(FIELDNAMES)
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    conn.executemany(
        f"INSERT OR REPLACE INTO attending_trend_acceptance_audit ({fields}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict]) -> None:
    by_status = Counter(row["acceptance_status"] for row in rows)
    by_blocker = Counter(row["acceptance_blocker"] for row in rows)
    by_display = Counter(row["display_safety_status"] for row in rows)
    by_action = Counter(row["recommended_next_action"] for row in rows)
    by_end_year = Counter(str(row["training_end_year"]) for row in rows if row["training_end_year"])
    by_training_type = Counter(row["training_type"] for row in rows if row["training_type"])
    accepted_rows = sum(int(row["accepted_trend_fact"] or 0) for row in rows)
    payload = {
        "trend_acceptance_rows": len(rows),
        "accepted_trend_fact_rows": accepted_rows,
        "review_ready_requires_reviewer_acceptance_rows": by_status.get(ACCEPTANCE_STATUS_REVIEW, 0),
        "acceptance_policy": (
            "No recent-attending trend candidate is accepted as a trend fact until explicit reviewer acceptance "
            "confirms same-person identity, current Penn endpoint, training line, program type, and dates."
        ),
        "by_acceptance_status": dict(sorted(by_status.items())),
        "by_acceptance_blocker": dict(sorted(by_blocker.items())),
        "by_display_safety_status": dict(sorted(by_display.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "by_training_end_year": dict(sorted(by_end_year.items())),
        "by_training_type": dict(sorted(by_training_type.items())),
        "display_safety_status": (
            ACCEPTED_DISPLAY_STATUS if accepted_rows == len(rows) and rows else REVIEW_READY_DISPLAY_STATUS if rows else ""
        ),
        "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
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
        rows = materialize_rows(conn)
        write_csv(rows)
        write_json(rows)
        write_db(conn, rows)
        write_summary(rows)
    conn.close()
    print(dumps({"trend_acceptance_rows": len(rows), "accepted_trend_fact_rows": sum(int(row["accepted_trend_fact"]) for row in rows)}))


if __name__ == "__main__":
    main()
