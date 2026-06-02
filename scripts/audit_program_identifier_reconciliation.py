#!/usr/bin/env python3
"""Reconcile external program identifier candidates into accepted/review states."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

RECONCILIATION_CSV = ARTIFACTS / "program_identifier_reconciliation.csv"
RECONCILIATION_JSON = ARTIFACTS / "program_identifier_reconciliation.json"
IDENTIFIERS_CSV = ARTIFACTS / "official_program_identifiers.csv"
SUMMARY_JSON = ARTIFACTS / "program_identifier_reconciliation_summary.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def key_for(prefix: str, value: str) -> str:
    import hashlib
    import re

    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48]
    return f"{prefix}_{slug}_{digest}" if slug else f"{prefix}_{digest}"


def read_candidates(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    grouped: dict[str, list[dict]] = {}
    for row in conn.execute(
        """
        SELECT candidate_key, official_program_key, official_program_type, official_program_name,
               official_department, identifier_type, identifier_value, identifier_source,
               source_program_specialty, source_program_name, source_city, source_state,
               source_status_json, source_url, candidate_status, confidence,
               match_reasons_json, evidence_json, observed_at
        FROM program_identifier_candidates
        ORDER BY official_program_name, confidence DESC, identifier_value
        """
    ):
        grouped.setdefault(row["official_program_key"], []).append(dict(row))
    return grouped


def load_json(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def decision_for(row: dict, rank: int, group: list[dict]) -> tuple[str, str, float, str]:
    top_confidence = max(float(item["confidence"] or 0) for item in group)
    close_count = sum(1 for item in group if top_confidence - float(item["confidence"] or 0) <= 0.08)
    strong_rows = [item for item in group if item["candidate_status"] == "strong_acgme_identifier_candidate"]
    status = row["candidate_status"]
    confidence = float(row["confidence"] or 0)

    if status == "no_acgme_identifier_found":
        return (
            "no_external_identifier_supported",
            "record_no_acgme_code_and_keep_program_as_local_or_non_acgme_until_better_source",
            0.0,
            "No ACGME row crossed the conservative source-backed threshold for this official program.",
        )

    if (
        status == "strong_acgme_identifier_candidate"
        and rank == 1
        and len(strong_rows) == 1
        and close_count == 1
        and row.get("identifier_value")
    ):
        return (
            "accepted_official_program_identifier",
            "attach_identifier_to_official_program_record",
            confidence,
            "Single strong ACGME candidate with no close competing Penn/UPHS facility or track sibling.",
        )

    if status == "strong_acgme_identifier_candidate" and row.get("identifier_value"):
        return (
            "manual_review_required_competing_strong_identifier",
            "review_facility_track_or_affiliate_context_before_accepting_identifier",
            min(confidence, 0.72),
            "Strong ACGME signal exists, but the official program has multiple strong or close identifier candidates.",
        )

    if status == "ambiguous_acgme_identifier_candidate":
        return (
            "manual_review_required_ambiguous_identifier",
            "review_duplicate_facility_or_track_specific_acgme_rows",
            min(confidence, 0.68),
            "ACGME candidate is ambiguous because duplicate facility, track, or broad specialty rows compete.",
        )

    if status == "review_acgme_identifier_candidate":
        return (
            "review_affiliate_or_specialty_alias_identifier",
            "review_affiliate_specialty_alias_or_chop_context_before_accepting",
            min(confidence, 0.62),
            "Candidate has useful ACGME evidence but needs source review before accepted identifier use.",
        )

    return (
        "do_not_accept_weak_identifier_candidate",
        "ignore_until_stronger_program_identifier_source_appears",
        min(confidence, 0.3),
        "Candidate does not have enough program, institution, or specialty support for identifier use.",
    )


def reconcile(grouped: dict[str, list[dict]], reconciled_at: str) -> tuple[list[dict], list[dict]]:
    decisions: list[dict] = []
    accepted_by_decision_key: dict[str, dict] = {}
    for official_program_key, group in grouped.items():
        ordered = sorted(group, key=lambda item: (-float(item["confidence"] or 0), item["identifier_value"] or ""))
        top_confidence = max(float(item["confidence"] or 0) for item in ordered)
        close_count = sum(1 for item in ordered if top_confidence - float(item["confidence"] or 0) <= 0.08)
        for rank, row in enumerate(ordered, start=1):
            status, action, reconciliation_confidence, rationale = decision_for(row, rank, ordered)
            evidence = {
                "candidate_evidence": load_json(row.get("evidence_json")),
                "match_reasons": load_json(row.get("match_reasons_json")),
                "candidate_count_for_program": len(ordered),
                "close_candidate_count": close_count,
                "top_confidence": top_confidence,
                "observed_at": row.get("observed_at"),
            }
            decision = {
                "reconciliation_key": key_for("program_identifier_reconciliation", row["candidate_key"]),
                "candidate_key": row["candidate_key"],
                "official_program_key": official_program_key,
                "official_program_type": row["official_program_type"],
                "official_program_name": row["official_program_name"],
                "identifier_type": row["identifier_type"],
                "identifier_value": row.get("identifier_value") or "",
                "identifier_source": row["identifier_source"],
                "source_program_specialty": row.get("source_program_specialty") or "",
                "source_program_name": row.get("source_program_name") or "",
                "source_city": row.get("source_city") or "",
                "candidate_status": row["candidate_status"],
                "reconciliation_status": status,
                "recommended_action": action,
                "reconciliation_confidence": round(reconciliation_confidence, 3),
                "rank_in_official_program": rank,
                "candidate_count_for_program": len(ordered),
                "close_candidate_count": close_count,
                "rationale": rationale,
                "evidence_json": dumps(evidence),
                "reconciled_at": reconciled_at,
            }
            decisions.append(decision)
            if status == "accepted_official_program_identifier":
                accepted_by_decision_key[decision["reconciliation_key"]] = {
                    "identifier_key": key_for(
                        "official_program_identifier",
                        f"{official_program_key}:{row['identifier_type']}:{row['identifier_value']}",
                    ),
                    "official_program_key": official_program_key,
                    "identifier_type": row["identifier_type"],
                    "identifier_value": row["identifier_value"],
                    "identifier_source": row["identifier_source"],
                    "source_url": row.get("source_url") or "",
                    "acceptance_status": "accepted",
                    "confidence": round(reconciliation_confidence, 3),
                    "accepted_from_candidate_key": row["candidate_key"],
                    "accepted_at": reconciled_at,
                    "evidence_json": dumps(
                        {
                            "reconciliation_status": status,
                            "rationale": rationale,
                            "source_program_specialty": row.get("source_program_specialty") or "",
                            "source_program_name": row.get("source_program_name") or "",
                            "source_city": row.get("source_city") or "",
                            "candidate_evidence": load_json(row.get("evidence_json")),
                        }
                    ),
                }
    accepted_value_counts = Counter(
        (row["identifier_type"], row["identifier_value"]) for row in accepted_by_decision_key.values()
    )
    for decision in decisions:
        value_key = (decision["identifier_type"], decision["identifier_value"])
        if (
            decision["reconciliation_status"] == "accepted_official_program_identifier"
            and accepted_value_counts[value_key] > 1
        ):
            decision["reconciliation_status"] = "manual_review_required_duplicate_identifier_across_programs"
            decision["recommended_action"] = "review_track_mapping_before_reusing_identifier_across_official_programs"
            decision["reconciliation_confidence"] = min(float(decision["reconciliation_confidence"]), 0.7)
            decision["rationale"] = (
                "The same ACGME identifier is the top candidate for multiple official Penn program rows; "
                "treat as track or denominator ambiguity until an explicit mapping source is reviewed."
            )
            evidence = load_json(decision["evidence_json"]) or {}
            evidence["duplicate_identifier_value_across_official_programs"] = True
            evidence["duplicate_identifier_count"] = accepted_value_counts[value_key]
            decision["evidence_json"] = dumps(evidence)
            accepted_by_decision_key.pop(decision["reconciliation_key"], None)
    return decisions, list(accepted_by_decision_key.values())


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, decisions: list[dict], accepted: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_program_identifiers")
    conn.execute("DELETE FROM program_identifier_reconciliation")
    conn.executemany(
        """
        INSERT INTO program_identifier_reconciliation
        (reconciliation_key, candidate_key, official_program_key, official_program_type,
         official_program_name, identifier_type, identifier_value, identifier_source,
         source_program_specialty, source_program_name, source_city, candidate_status,
         reconciliation_status, recommended_action, reconciliation_confidence,
         rank_in_official_program, candidate_count_for_program, close_candidate_count,
         rationale, evidence_json, reconciled_at)
        VALUES
        (:reconciliation_key, :candidate_key, :official_program_key, :official_program_type,
         :official_program_name, :identifier_type, :identifier_value, :identifier_source,
         :source_program_specialty, :source_program_name, :source_city, :candidate_status,
         :reconciliation_status, :recommended_action, :reconciliation_confidence,
         :rank_in_official_program, :candidate_count_for_program, :close_candidate_count,
         :rationale, :evidence_json, :reconciled_at)
        """,
        decisions,
    )
    conn.executemany(
        """
        INSERT INTO official_program_identifiers
        (identifier_key, official_program_key, identifier_type, identifier_value,
         identifier_source, source_url, acceptance_status, confidence,
         accepted_from_candidate_key, accepted_at, evidence_json)
        VALUES
        (:identifier_key, :official_program_key, :identifier_type, :identifier_value,
         :identifier_source, :source_url, :acceptance_status, :confidence,
         :accepted_from_candidate_key, :accepted_at, :evidence_json)
        """,
        accepted,
    )
    conn.commit()


def write_outputs(decisions: list[dict], accepted: list[dict], reconciled_at: str) -> dict:
    write_csv(RECONCILIATION_CSV, decisions)
    RECONCILIATION_JSON.write_text(dumps(decisions) + "\n", encoding="utf-8")
    write_csv(IDENTIFIERS_CSV, accepted)
    by_status = Counter(row["reconciliation_status"] for row in decisions)
    by_action = Counter(row["recommended_action"] for row in decisions)
    summary = {
        "reconciled_at": reconciled_at,
        "candidate_rows": len(decisions),
        "official_program_rows": len({row["official_program_key"] for row in decisions}),
        "accepted_identifier_rows": len(accepted),
        "accepted_official_program_rows": len({row["official_program_key"] for row in accepted}),
        "by_reconciliation_status": dict(sorted(by_status.items())),
        "by_recommended_action": dict(sorted(by_action.items())),
        "acceptance_rule": "Accept only a single strong top ACGME candidate with no close competing Penn/UPHS facility, affiliate, or track sibling.",
        "reconciliation_csv": "artifacts/data/program_identifier_reconciliation.csv",
        "reconciliation_json": "artifacts/data/program_identifier_reconciliation.json",
        "accepted_identifier_csv": "artifacts/data/official_program_identifiers.csv",
    }
    SUMMARY_JSON.write_text(dumps(summary) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB))
    args = parser.parse_args()
    reconciled_at = now_utc()
    conn = sqlite3.connect(args.db)
    decisions, accepted = reconcile(read_candidates(conn), reconciled_at)
    write_db(conn, decisions, accepted)
    conn.close()
    summary = write_outputs(decisions, accepted, reconciled_at)
    print(dumps(summary))


if __name__ == "__main__":
    main()
