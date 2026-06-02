#!/usr/bin/env python3
"""Materialize non-mutating verification contracts for public contact candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "contact_verification_contracts.csv"
JSON_PATH = ARTIFACTS / "contact_verification_contracts.json"
SUMMARY_PATH = ARTIFACTS / "contact_verification_contract_summary.json"

FIELDNAMES = [
    "contact_contract_key",
    "contact_assurance_key",
    "contact_key",
    "person_key",
    "display_name",
    "role",
    "contact_type",
    "normalized_contact_value",
    "contact_domain",
    "canonical_contact_domain",
    "domain_status",
    "source_key",
    "source_url",
    "source_type",
    "source_assurance_class",
    "source_observed_at",
    "current_assurance_status",
    "current_display_safety_status",
    "verification_lane",
    "verification_confidence",
    "operational_use_status",
    "stale_after_date",
    "next_refresh_date",
    "if_reobserved_same_value_change_type",
    "if_reobserved_different_value_change_type",
    "if_missing_on_refresh_change_type",
    "evidence_required_to_verify",
    "evidence_required_to_reject",
    "recommended_reverification_query",
    "required_reviewer_action",
    "allowed_auto_outcomes_json",
    "review_trigger_json",
    "evidence_json",
    "generated_at",
]

INSTITUTIONAL_DOMAINS = {
    "pennmedicine.upenn.edu",
    "upenn.edu",
    "wharton.upenn.edu",
}

DOMAIN_CORRECTIONS = {
    "pennmedine.upenn.edu": "pennmedicine.upenn.edu",
}

OFFICIAL_CURRENT_CLASSES = {
    "official_current_or_gap_roster_contact",
    "official_public_student_directory_contact",
    "official_profile_contact_candidate",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_date_prefix(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def normalize_contact(contact_type: str, value: str) -> str:
    if contact_type == "email":
        return (value or "").strip().lower()
    return (value or "").strip()


def source_observed_at(row: dict) -> str:
    return row.get("source_fetched_at") or row.get("audited_at") or ""


def refresh_date(row: dict, as_of: date) -> date:
    observed = parse_date_prefix(source_observed_at(row)) or as_of
    source_class = row.get("source_assurance_class") or ""
    if source_class == "official_profile_contact_candidate":
        return observed + timedelta(days=180)
    if source_class in OFFICIAL_CURRENT_CLASSES:
        return observed + timedelta(days=120)
    return observed + timedelta(days=90)


def domain_status(domain: str) -> tuple[str, str]:
    normalized = (domain or "").lower()
    if normalized in INSTITUTIONAL_DOMAINS:
        return normalized, "institutional_domain"
    if normalized in DOMAIN_CORRECTIONS:
        return DOMAIN_CORRECTIONS[normalized], "likely_domain_typo_review"
    if normalized.endswith(".upenn.edu"):
        return normalized, "upenn_subdomain_review"
    if normalized:
        return normalized, "external_domain_review"
    return "", "missing_domain_review"


def classify_contract(row: dict, as_of: date) -> dict:
    normalized_value = normalize_contact(row["contact_type"], row["contact_value"])
    canonical_domain, domain_state = domain_status(row.get("contact_domain") or "")
    source_class = row.get("source_assurance_class") or ""
    assurance_status = row.get("assurance_status") or ""
    display_status = row.get("display_safety_status") or ""
    current_confidence = float(row.get("confidence") or 0.0)
    stale_date = refresh_date(row, as_of)
    source_is_official = source_class in OFFICIAL_CURRENT_CLASSES
    domain_ok = domain_state == "institutional_domain"

    if not domain_ok:
        lane = "domain_review_before_contact_use"
        operational = "do_not_use_until_domain_reviewed"
        verify_evidence = "Fresh official source must show the same contact value and an institutional domain."
        reject_evidence = "Reject if the domain typo/external domain is not confirmed by an official current source."
        reviewer_action = "Review domain anomaly before display, outreach, or acceptance."
        same = "domain_review_still_required"
        different = "contact_value_or_domain_changed_review"
        missing = "contact_missing_domain_anomaly_review"
        allowed = []
        triggers = ["domain_not_in_institutional_allowlist", "source_refresh_required"]
        confidence = min(current_confidence, 0.35)
    elif source_is_official and assurance_status == "official_public_unverified_contact":
        lane = "fresh_official_reobservation_required"
        operational = "public_candidate_only_not_verified"
        verify_evidence = (
            "A fresh official roster, directory, profile, or mailto source reobserves the same value, "
            "domain, person identity, and intended contact scope."
        )
        reject_evidence = "Reject or mark stale if a fresh official source removes the value or shows a different value."
        reviewer_action = "Reobserve the current official source before promoting this candidate to a verified contact fact."
        same = "verified_same_value_after_fresh_official_reobservation"
        different = "contact_value_changed_review"
        missing = "contact_absent_on_refresh_stale_review"
        allowed = ["verified_same_value_after_fresh_official_reobservation"]
        triggers = ["stale_after_date_reached", "contact_value_changed", "contact_absent_on_refresh"]
        confidence = min(0.74, current_confidence)
    elif source_is_official:
        lane = "official_source_low_confidence_review"
        operational = "public_candidate_low_confidence"
        verify_evidence = "Reviewer confirms same-person identity, official source currency, contact value, and scope."
        reject_evidence = "Reject if context is generic/program contact or not person-specific."
        reviewer_action = "Review contact context before treating as person-level contact evidence."
        same = "same_value_low_confidence_review"
        different = "contact_value_changed_review"
        missing = "contact_absent_on_refresh_stale_review"
        allowed = []
        triggers = ["low_confidence_contact_context", "source_refresh_required"]
        confidence = min(0.5, current_confidence)
    else:
        lane = "public_source_reverification_required"
        operational = "do_not_use_until_official_reobserved"
        verify_evidence = "Current official Penn source must reobserve the same value and person identity."
        reject_evidence = "Reject if no current official source can anchor the value to this person."
        reviewer_action = "Seek an official Penn source or directory before using this contact candidate."
        same = "same_value_public_source_review"
        different = "contact_value_changed_review"
        missing = "contact_absent_on_refresh_stale_review"
        allowed = []
        triggers = ["non_official_contact_source", "source_refresh_required"]
        confidence = min(0.4, current_confidence)

    query_parts = [
        f'"{row["display_name"]}"',
        f'"{normalized_value}"',
        '"Penn Medicine"',
        '"contact"',
    ]
    contract_key = "contact_contract_" + sha256_text(
        dumps(
            {
                "contact_key": row["contact_key"],
                "normalized_contact_value": normalized_value,
                "lane": lane,
            }
        )
    )[:20]
    evidence = {
        "contact_assurance_key": row["contact_assurance_key"],
        "source_observed_at": source_observed_at(row),
        "source_assurance_class": source_class,
        "domain_status": domain_state,
        "canonical_contact_domain": canonical_domain,
        "current_contact_assurance": {
            "assurance_status": assurance_status,
            "display_safety_status": display_status,
            "confidence": current_confidence,
            "verification_status": row.get("verification_status") or "",
        },
        "policy": {
            "non_mutating": True,
            "accepted_contact_fact_requires": verify_evidence,
        },
    }
    return {
        "contact_contract_key": contract_key,
        "contact_assurance_key": row["contact_assurance_key"],
        "contact_key": row["contact_key"],
        "person_key": row.get("person_key") or "",
        "display_name": row["display_name"],
        "role": row.get("role") or "",
        "contact_type": row["contact_type"],
        "normalized_contact_value": normalized_value,
        "contact_domain": row.get("contact_domain") or "",
        "canonical_contact_domain": canonical_domain,
        "domain_status": domain_state,
        "source_key": row.get("source_key") or "",
        "source_url": row.get("source_url") or "",
        "source_type": row.get("source_type") or "",
        "source_assurance_class": source_class,
        "source_observed_at": source_observed_at(row),
        "current_assurance_status": assurance_status,
        "current_display_safety_status": display_status,
        "verification_lane": lane,
        "verification_confidence": round(confidence, 2),
        "operational_use_status": operational,
        "stale_after_date": stale_date.isoformat(),
        "next_refresh_date": stale_date.isoformat(),
        "if_reobserved_same_value_change_type": same,
        "if_reobserved_different_value_change_type": different,
        "if_missing_on_refresh_change_type": missing,
        "evidence_required_to_verify": verify_evidence,
        "evidence_required_to_reject": reject_evidence,
        "recommended_reverification_query": " ".join(query_parts),
        "required_reviewer_action": reviewer_action,
        "allowed_auto_outcomes_json": dumps(allowed),
        "review_trigger_json": dumps(triggers),
        "evidence_json": dumps(evidence),
        "generated_at": "",
    }


def read_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT a.*, s.fetched_at AS source_fetched_at
            FROM contact_assurance_audit a
            LEFT JOIN sources s ON s.source_key = a.source_key
            ORDER BY a.role, a.display_name, a.contact_type, a.contact_value, a.contact_assurance_key
            """
        )
    ]


def existing_rows() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["contact_contract_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["contact_contract_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def materialize(conn: sqlite3.Connection, as_of: date) -> list[dict]:
    existing = existing_rows()
    timestamp = now_utc()
    rows = []
    for source in read_rows(conn):
        row = classify_contract(source, as_of)
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
    conn.execute("DELETE FROM contact_verification_contracts")
    if not rows:
        return
    fields = ", ".join(FIELDNAMES)
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if not db_row.get("person_key"):
            db_row["person_key"] = None
        db_rows.append(db_row)
    conn.executemany(
        f"INSERT OR REPLACE INTO contact_verification_contracts ({fields}) VALUES ({placeholders})",
        db_rows,
    )


def write_summary(rows: list[dict], as_of: date) -> None:
    by_lane = Counter(row["verification_lane"] for row in rows)
    by_domain = Counter(row["domain_status"] for row in rows)
    by_operational = Counter(row["operational_use_status"] for row in rows)
    by_role = Counter(row["role"] for row in rows)
    stale_by_refresh = sum(1 for row in rows if row["stale_after_date"] <= as_of.isoformat())
    payload = {
        "contract_rows": len(rows),
        "person_count": len({row["person_key"] for row in rows if row["person_key"]}),
        "contact_type_counts": dict(sorted(Counter(row["contact_type"] for row in rows).items())),
        "by_verification_lane": dict(sorted(by_lane.items())),
        "by_domain_status": dict(sorted(by_domain.items())),
        "by_operational_use_status": dict(sorted(by_operational.items())),
        "by_role": dict(sorted(by_role.items())),
        "verified_contact_fact_rows": 0,
        "fresh_official_reobservation_required_rows": by_lane.get("fresh_official_reobservation_required", 0),
        "domain_review_required_rows": sum(count for lane, count in by_lane.items() if "domain_review" in lane),
        "stale_by_as_of_date_rows": stale_by_refresh,
        "as_of_date": as_of.isoformat(),
        "policy": (
            "Contact contracts are non-mutating. They define how future fresh source observations, absences, "
            "domain anomalies, and changed values should be classified before a contact candidate can become "
            "a verified contact fact."
        ),
        "acceptance_rule": (
            "A contact becomes verified only after a fresh official source reobserves the same value, domain, "
            "person identity, and intended contact scope, or after an explicit reviewer decision records that evidence."
        ),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--as-of-date", default=date.today().isoformat())
    args = parser.parse_args()

    as_of = date.fromisoformat(args.as_of_date)
    conn = sqlite3.connect(args.db)
    with conn:
        rows = materialize(conn, as_of)
        write_csv(rows)
        write_json(rows)
        write_db(conn, rows)
        write_summary(rows, as_of)
    conn.close()
    print(dumps({"contact_verification_contract_rows": len(rows)}))


if __name__ == "__main__":
    main()
