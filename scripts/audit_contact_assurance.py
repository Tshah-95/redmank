#!/usr/bin/env python3
"""Classify public contact candidates into non-mutating assurance tiers."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "contact_assurance_audit.csv"
JSON_PATH = ARTIFACTS / "contact_assurance_audit.json"
SUMMARY_PATH = ARTIFACTS / "contact_assurance_summary.json"

FIELDNAMES = [
    "contact_assurance_key",
    "contact_key",
    "contact_id",
    "person_key",
    "display_name",
    "role",
    "subject_type",
    "contact_type",
    "contact_value",
    "contact_domain",
    "contact_label",
    "contact_scope",
    "source_key",
    "source_url",
    "source_type",
    "source_assurance_class",
    "verification_status",
    "prior_status",
    "assurance_status",
    "assurance_level",
    "confidence",
    "display_safety_status",
    "freshness_policy",
    "required_next_check",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]

INSTITUTIONAL_DOMAINS = {
    "pennmedicine.upenn.edu",
    "upenn.edu",
    "wharton.upenn.edu",
}

OFFICIAL_SOURCE_TYPES = {
    "official_public_student_directory",
    "official_roster",
    "official_gap_roster",
    "official_attending_faculty_candidate",
}


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


def contact_domain(contact_type: str, contact_value: str) -> str:
    if contact_type != "email" or "@" not in contact_value:
        return ""
    return contact_value.rsplit("@", 1)[1].lower()


def valid_email(value: str) -> bool:
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value or ""))


def source_assurance_class(source_type: str, source_url: str) -> str:
    if source_type in {"official_roster", "official_gap_roster"}:
        return "official_current_or_gap_roster_contact"
    if source_type == "official_public_student_directory":
        return "official_public_student_directory_contact"
    if source_type == "official_attending_faculty_candidate":
        return "official_profile_contact_candidate"
    if source_url:
        return "public_source_contact_candidate"
    return "source_missing_contact_candidate"


def classify(row: dict) -> tuple[str, int, str, str, str, str]:
    contact_type = row["contact_type"]
    value = row["contact_value"]
    domain = row["contact_domain"]
    source_type = row.get("source_type") or ""
    verification_status = row.get("verification_status") or ""
    confidence = float(row.get("confidence") or 0.0)
    has_source = bool(row.get("source_url"))
    institutional_domain = domain in INSTITUTIONAL_DOMAINS
    official_source = source_type in OFFICIAL_SOURCE_TYPES

    if contact_type == "email" and not valid_email(value):
        return (
            "invalid_contact_value_review",
            0,
            "do_not_display_until_format_verified",
            "do_not_carry_forward_without_fresh_valid_contact_source",
            "verify_email_format_and_source_markup",
            "review_or_remove_invalid_contact_candidate",
        )
    if contact_type == "email" and domain and not institutional_domain:
        return (
            "domain_review_required",
            1 if has_source else 0,
            "do_not_display_until_domain_verified",
            "do_not_carry_forward_without_domain_and_source_refresh",
            "verify_institutional_domain_or_source_typo",
            "review_domain_before_contact_use",
        )
    if verification_status.endswith("_unverified") and official_source and institutional_domain and confidence >= 0.8:
        return (
            "official_public_unverified_contact",
            2,
            "public_contact_candidate_not_verified",
            "source_refresh_required_before_operational_use",
            "confirm_contact_on_current_official_source_or_directory",
            "verify_current_source_before_display_or_outreach",
        )
    if official_source and institutional_domain:
        return (
            "official_public_low_confidence_contact",
            1,
            "public_contact_candidate_low_confidence",
            "source_refresh_required_before_operational_use",
            "confirm_contact_value_and_person_identity",
            "review_contact_context_before_use",
        )
    if institutional_domain and has_source:
        return (
            "public_institutional_contact_candidate",
            1,
            "public_contact_candidate_not_verified",
            "source_refresh_required_before_operational_use",
            "confirm_contact_on_current_public_source",
            "verify_current_source_before_display_or_outreach",
        )
    return (
        "low_signal_contact_candidate",
        0,
        "do_not_display_until_verified",
        "do_not_carry_forward_without_fresh_source",
        "collect_current_public_source_and_identity_context",
        "deprioritize_until_stronger_contact_source_appears",
    )


def read_contacts(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    rows = []
    for row in conn.execute(
        """
        SELECT c.contact_id, c.contact_key, c.person_key,
               COALESCE(p.display_name, c.display_name) AS display_name,
               COALESCE(p.role, c.subject_type) AS role,
               c.subject_type, c.contact_type, c.contact_value, c.contact_label,
               c.contact_scope, c.source_key, c.source_url, c.source_type,
               c.verification_status, c.confidence, c.status AS prior_status,
               c.match_features_json, c.evidence_json
        FROM person_contacts c
        LEFT JOIN people p ON p.person_key = c.person_key
        ORDER BY c.contact_id
        """
    ):
        item = dict(row)
        item["contact_domain"] = contact_domain(item["contact_type"], item["contact_value"])
        rows.append(item)
    return rows


def load_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["contact_assurance_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["contact_assurance_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("audited_at") or timestamp


def materialize_rows(conn: sqlite3.Connection) -> list[dict]:
    existing = load_existing()
    timestamp = now_utc()
    output = []
    for source in read_contacts(conn):
        assurance_status, assurance_level, display_safety, freshness_policy, required_check, action = classify(source)
        source_class = source_assurance_class(source.get("source_type") or "", source.get("source_url") or "")
        key = f"contact_assurance_{sha256_text(source['contact_key'])[:20]}"
        evidence = {
            "match_features": parse_json(source.get("match_features_json"), []),
            "source_contact_evidence": parse_json(source.get("evidence_json"), {}),
            "institutional_domain": source["contact_domain"] in INSTITUTIONAL_DOMAINS,
            "official_source_type": (source.get("source_type") or "") in OFFICIAL_SOURCE_TYPES,
            "policy": {
                "acceptance_rule": (
                    "Public contacts remain non-mutating candidates until the current official source or "
                    "directory reconfirms the contact value, domain, person identity, and intended contact scope."
                )
            },
        }
        row = {
            "contact_assurance_key": key,
            "contact_key": source["contact_key"],
            "contact_id": source["contact_id"],
            "person_key": source.get("person_key") or "",
            "display_name": source["display_name"],
            "role": source.get("role") or "",
            "subject_type": source.get("subject_type") or "",
            "contact_type": source["contact_type"],
            "contact_value": source["contact_value"],
            "contact_domain": source["contact_domain"],
            "contact_label": source.get("contact_label") or "",
            "contact_scope": source.get("contact_scope") or "",
            "source_key": source.get("source_key") or "",
            "source_url": source.get("source_url") or "",
            "source_type": source.get("source_type") or "",
            "source_assurance_class": source_class,
            "verification_status": source.get("verification_status") or "",
            "prior_status": source.get("prior_status") or "",
            "assurance_status": assurance_status,
            "assurance_level": assurance_level,
            "confidence": float(source.get("confidence") or 0.0),
            "display_safety_status": display_safety,
            "freshness_policy": freshness_policy,
            "required_next_check": required_check,
            "recommended_next_action": action,
            "evidence_json": dumps(evidence),
            "audited_at": "",
        }
        row["audited_at"] = stable_audited_at(existing, row, timestamp)
        output.append({field: row[field] for field in FIELDNAMES})
    return output


def write_csv(rows: list[dict]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict]) -> None:
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM contact_assurance_audit")
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
        f"INSERT OR REPLACE INTO contact_assurance_audit ({fields}) VALUES ({placeholders})",
        db_rows,
    )


def write_summary(rows: list[dict]) -> None:
    by_status = Counter(row["assurance_status"] for row in rows)
    by_role = Counter(row["role"] for row in rows)
    by_source_class = Counter(row["source_assurance_class"] for row in rows)
    by_display_safety = Counter(row["display_safety_status"] for row in rows)
    by_domain = Counter(row["contact_domain"] or "none" for row in rows)
    review_rows = [
        row
        for row in rows
        if row["assurance_status"] in {"domain_review_required", "invalid_contact_value_review"}
    ]
    payload = {
        "contact_assurance_rows": len(rows),
        "contact_people": len({row["person_key"] for row in rows if row["person_key"]}),
        "contact_type_counts": dict(sorted(Counter(row["contact_type"] for row in rows).items())),
        "by_assurance_status": dict(sorted(by_status.items())),
        "by_role": dict(sorted(by_role.items())),
        "by_source_assurance_class": dict(sorted(by_source_class.items())),
        "by_display_safety_status": dict(sorted(by_display_safety.items())),
        "by_contact_domain": dict(sorted(by_domain.items())),
        "review_required_rows": len(review_rows),
        "verified_contact_fact_rows": 0,
        "acceptance_policy": (
            "No public contact candidate is treated as a verified contact fact until a current official source "
            "or directory reconfirms contact value, domain, person identity, and intended scope."
        ),
        "display_policy": "display_as_public_candidate_only_until_verified",
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
    print(dumps({"contact_assurance_rows": len(rows), "review_required_rows": sum(1 for row in rows if row["assurance_level"] == 1 and row["assurance_status"] == "domain_review_required")}))


if __name__ == "__main__":
    main()
