#!/usr/bin/env python3
"""Materialize person-level enrichment dossiers with provenance and safety status."""

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

CSV_PATH = ARTIFACTS / "person_enrichment_dossiers.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_dossier_summary.json"

FIELDNAMES = [
    "dossier_key",
    "person_key",
    "display_name",
    "role",
    "current_status",
    "institution",
    "profile_url",
    "headshot_url",
    "program_count",
    "programs",
    "current_training_states",
    "lifecycle_codes",
    "temporal_policy_lanes",
    "coverage_score",
    "coverage_band",
    "accepted_enrichment_count",
    "accepted_publication_count",
    "accepted_enrichment_json",
    "candidate_evidence_count",
    "review_ready_evidence_count",
    "publication_candidate_count",
    "npi_candidate_count",
    "profile_background_candidate_count",
    "contact_contract_count",
    "verified_contact_fact_count",
    "contact_operational_use_statuses",
    "contacts_json",
    "review_packet_count",
    "max_review_priority",
    "best_packet_status",
    "best_review_kind",
    "best_review_action",
    "acceptance_blocker",
    "top_source_urls",
    "missing_surface_summary",
    "dossier_status",
    "display_safety_status",
    "recommended_next_action",
    "evidence_json",
    "generated_at",
]

REVIEW_READY_DECISIONS = {
    "review_ready_high_anchor",
    "review_ready_profile_background_field",
    "review_ready_training_topic_anchor",
    "attending_training_claim_review_ready",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["dossier_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["dossier_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def fetch_people(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT p.person_key, p.display_name, p.role, p.current_status, p.institution,
                   p.profile_url, p.headshot_url,
                   COALESCE(c.program_count, 0) AS program_count,
                   COALESCE(c.programs, '') AS programs,
                   COALESCE(c.coverage_score, 0) AS coverage_score,
                   COALESCE(c.coverage_band, 'unknown_coverage') AS coverage_band,
                   COALESCE(c.recommended_next_action, '') AS coverage_next_action
            FROM people p
            LEFT JOIN person_enrichment_coverage c ON c.person_key = p.person_key
            ORDER BY p.role, p.display_name, p.person_key
            """
        )
    ]


def grouped(conn: sqlite3.Connection, query: str, key: str = "person_key") -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    groups: dict[str, list[dict]] = defaultdict(list)
    for row in conn.execute(query):
        item = dict(row)
        groups[item.get(key) or ""].append(item)
    return groups


def contact_values(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        result.append(
            {
                "contact_type": row.get("contact_type") or "",
                "value": row.get("normalized_contact_value") or "",
                "domain_status": row.get("domain_status") or "",
                "verification_lane": row.get("verification_lane") or "",
                "operational_use_status": row.get("operational_use_status") or "",
                "stale_after_date": row.get("stale_after_date") or "",
                "source_url": row.get("source_url") or "",
            }
        )
    return result


def accepted_values(rows: list[dict]) -> list[dict]:
    return [
        {
            "enrichment_type": row.get("enrichment_type") or "",
            "claim_type": row.get("claim_type") or "",
            "claim_value": row.get("claim_value") or "",
            "source_url": row.get("source_url") or "",
            "assurance_level": int(row.get("assurance_level") or 0),
            "confidence": float(row.get("confidence") or 0.0),
            "display_safety_status": row.get("display_safety_status") or "",
        }
        for row in rows
    ]


def top_review_packet(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return sorted(rows, key=lambda row: int(row.get("review_priority") or 0), reverse=True)[0]


def dossier_status(
    accepted_count: int,
    review_ready_count: int,
    candidate_count: int,
    contact_count: int,
    coverage_band: str,
) -> tuple[str, str]:
    if accepted_count and review_ready_count:
        return "accepted_enrichment_with_review_queue", "accepted_facts_plus_review_candidates"
    if accepted_count:
        return "accepted_enrichment_present", "accepted_enrichment_not_roster_truth"
    if review_ready_count:
        return "review_ready_evidence_present", "review_ready_not_accepted_enrichment_fact"
    if candidate_count or contact_count:
        return "candidate_evidence_present", "candidate_only_not_accepted"
    if coverage_band == "thin_enrichment_surface":
        return "thin_profile_needs_collection", "no_enrichment_default_display"
    return "baseline_roster_only", "roster_identity_only"


def materialize(conn: sqlite3.Connection) -> list[dict]:
    existing = read_existing()
    timestamp = now_utc()
    people = fetch_people(conn)
    training = grouped(
        conn,
        """
        SELECT s.person_key, p.program_name, s.normalized_stage, s.lifecycle_code,
               s.trainee_category, s.expected_next_stage, s.expected_next_date,
               s.stale_after_date, s.confidence
        FROM person_training_states s
        LEFT JOIN programs p ON p.program_key = s.program_key
        ORDER BY s.person_key, p.program_name, s.normalized_stage
        """,
    )
    temporal = grouped(
        conn,
        """
        SELECT person_key, program_name, policy_lane, next_refresh_contract,
               temporal_validity_status, stale_after_date, expected_next_stage,
               expected_next_date, confidence
        FROM training_temporal_contracts
        ORDER BY person_key, program_name, policy_lane
        """,
    )
    accepted = grouped(
        conn,
        """
        SELECT *
        FROM accepted_enrichment_claims
        ORDER BY person_key, enrichment_type, confidence DESC
        """,
    )
    decisions = grouped(
        conn,
        """
        SELECT *
        FROM evidence_reconciliation_decisions
        WHERE person_key IS NOT NULL AND person_key != ''
        ORDER BY person_key, priority DESC, confidence DESC
        """,
    )
    packets = grouped(
        conn,
        """
        SELECT *
        FROM person_evidence_review_packets
        WHERE person_key IS NOT NULL AND person_key != ''
        ORDER BY person_key, review_priority DESC
        """,
    )
    contacts = grouped(
        conn,
        """
        SELECT *
        FROM contact_verification_contracts
        WHERE person_key IS NOT NULL AND person_key != ''
        ORDER BY person_key, contact_type, normalized_contact_value
        """,
    )
    accepted_contacts = grouped(
        conn,
        """
        SELECT *
        FROM accepted_verified_contact_facts
        WHERE person_key IS NOT NULL AND person_key != ''
        ORDER BY person_key, contact_type, normalized_contact_value
        """,
    )

    rows = []
    for person in people:
        person_key = person["person_key"]
        accepted_rows = accepted.get(person_key, [])
        decision_rows = decisions.get(person_key, [])
        packet_rows = packets.get(person_key, [])
        contact_rows = contacts.get(person_key, [])
        accepted_contact_rows = accepted_contacts.get(person_key, [])
        training_rows = training.get(person_key, [])
        temporal_rows = temporal.get(person_key, [])

        decision_counts = Counter(row.get("decision") or "" for row in decision_rows)
        review_ready_count = sum(decision_counts.get(decision, 0) for decision in REVIEW_READY_DECISIONS)
        candidate_count = sum(
            1
            for row in decision_rows
            if row.get("decision") not in REVIEW_READY_DECISIONS
            and row.get("decision") not in {"discovery_only", "low_signal_candidate", "npi_low_signal_candidate"}
        )
        publication_candidates = sum(
            1
            for row in decision_rows
            if (row.get("claim_type") or "") in {"pubmed_article_candidate", "pubmed_author_query_candidate"}
        )
        npi_candidates = sum(1 for row in decision_rows if (row.get("claim_type") or "") == "npi_candidate")
        profile_background = sum(
            1
            for row in decision_rows
            if (row.get("claim_type") or "")
            in {"education_history_candidate", "prior_training_history_candidate", "research_interest_candidate", "personal_profile_candidate"}
        )
        accepted_publications = sum(1 for row in accepted_rows if (row.get("enrichment_type") or "") == "publication")
        verified_contacts = len(accepted_contact_rows)
        best_packet = top_review_packet(packet_rows)
        source_urls = []
        for row in decision_rows[:8]:
            source_urls.extend(split_semicolon(row.get("source_url")))
        for row in packet_rows[:3]:
            source_urls.extend(split_semicolon(row.get("top_source_urls")))
        for row in accepted_rows:
            source_urls.extend(split_semicolon(row.get("source_url")))
        for row in accepted_contact_rows:
            source_urls.extend(split_semicolon(row.get("reobserved_source_url") or row.get("source_url")))
        missing = []
        if not person.get("profile_url"):
            missing.append("official_profile_url")
        if not accepted_rows:
            missing.append("accepted_enrichment")
        if review_ready_count:
            missing.append("review_decision")
        if contact_rows and not verified_contacts:
            missing.append("verified_contact")
        if not contact_rows:
            missing.append("contact_evidence")

        status, display_status = dossier_status(
            len(accepted_rows),
            review_ready_count,
            candidate_count,
            len(contact_rows),
            person.get("coverage_band") or "",
        )
        next_action = (
            best_packet.get("recommended_next_action")
            or person.get("coverage_next_action")
            or "monitor_refresh_and_diff"
        )
        training_labels = [
            " | ".join(
                part
                for part in [
                    row.get("program_name") or "",
                    row.get("normalized_stage") or "",
                    row.get("trainee_category") or "",
                    row.get("expected_next_stage") or "",
                ]
                if part
            )
            for row in training_rows
        ]
        evidence = {
            "training_states": training_rows[:20],
            "temporal_contracts": temporal_rows[:20],
            "decision_counts": dict(sorted(decision_counts.items())),
            "top_review_packet": best_packet,
            "contacts": contact_values(contact_rows),
            "accepted_verified_contacts": accepted_contact_rows,
            "accepted_enrichment": accepted_values(accepted_rows),
            "policy": {
                "non_mutating": True,
                "candidate_fields_are_not_accepted_facts": True,
                "contacts_require_verification_contract": True,
                "verified_contact_facts_require_reviewer_acceptance": True,
            },
        }
        row = {
            "dossier_key": "person_dossier_" + sha256_text(person_key)[:20],
            "person_key": person_key,
            "display_name": person["display_name"],
            "role": person.get("role") or "",
            "current_status": person.get("current_status") or "",
            "institution": person.get("institution") or "",
            "profile_url": person.get("profile_url") or "",
            "headshot_url": person.get("headshot_url") or "",
            "program_count": int(person.get("program_count") or 0),
            "programs": person.get("programs") or "",
            "current_training_states": compact_join(training_labels),
            "lifecycle_codes": compact_join([row.get("lifecycle_code") or "" for row in training_rows]),
            "temporal_policy_lanes": compact_join([row.get("policy_lane") or "" for row in temporal_rows]),
            "coverage_score": int(person.get("coverage_score") or 0),
            "coverage_band": person.get("coverage_band") or "",
            "accepted_enrichment_count": len(accepted_rows),
            "accepted_publication_count": accepted_publications,
            "accepted_enrichment_json": dumps(accepted_values(accepted_rows)),
            "candidate_evidence_count": candidate_count,
            "review_ready_evidence_count": review_ready_count,
            "publication_candidate_count": publication_candidates,
            "npi_candidate_count": npi_candidates,
            "profile_background_candidate_count": profile_background,
            "contact_contract_count": len(contact_rows),
            "verified_contact_fact_count": verified_contacts,
            "contact_operational_use_statuses": compact_join(
                [row.get("operational_use_status") or "" for row in contact_rows]
            ),
            "contacts_json": dumps(contact_values(contact_rows)),
            "review_packet_count": len(packet_rows),
            "max_review_priority": int(best_packet.get("review_priority") or 0),
            "best_packet_status": best_packet.get("packet_status") or "",
            "best_review_kind": best_packet.get("review_kind") or "",
            "best_review_action": best_packet.get("recommended_next_action") or "",
            "acceptance_blocker": best_packet.get("acceptance_blocker") or "",
            "top_source_urls": compact_join(source_urls, limit=8),
            "missing_surface_summary": compact_join(missing, limit=8),
            "dossier_status": status,
            "display_safety_status": display_status,
            "recommended_next_action": next_action,
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
    conn.execute("DELETE FROM person_enrichment_dossiers")
    if not rows:
        return
    fields = ", ".join(FIELDNAMES)
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    conn.executemany(
        f"INSERT OR REPLACE INTO person_enrichment_dossiers ({fields}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict]) -> None:
    payload = {
        "dossier_rows": len(rows),
        "person_count": len({row["person_key"] for row in rows}),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "by_dossier_status": dict(sorted(Counter(row["dossier_status"] for row in rows).items())),
        "by_display_safety_status": dict(sorted(Counter(row["display_safety_status"] for row in rows).items())),
        "by_coverage_band": dict(sorted(Counter(row["coverage_band"] for row in rows).items())),
        "accepted_enrichment_people": sum(1 for row in rows if int(row["accepted_enrichment_count"]) > 0),
        "review_ready_people": sum(1 for row in rows if int(row["review_ready_evidence_count"]) > 0),
        "contact_contract_people": sum(1 for row in rows if int(row["contact_contract_count"]) > 0),
        "verified_contact_people": sum(1 for row in rows if int(row["verified_contact_fact_count"]) > 0),
        "thin_profile_people": sum(1 for row in rows if row["dossier_status"] == "thin_profile_needs_collection"),
        "policy": (
            "Dossiers are non-mutating person summaries. Accepted facts, candidate evidence, review-ready evidence, "
            "contact contracts, and missing surfaces are separated so downstream display or scoring can choose its "
            "assurance threshold explicitly."
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
    print(dumps({"person_enrichment_dossiers": len(rows)}))


if __name__ == "__main__":
    main()
