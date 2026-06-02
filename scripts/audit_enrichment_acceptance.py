#!/usr/bin/env python3
"""Classify candidate enrichment evidence into non-mutating acceptance assurance tiers."""

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

DECISIONS_CSV = ARTIFACTS / "evidence_reconciliation_decisions.csv"
ACCEPTANCE_CSV = ARTIFACTS / "enrichment_acceptance_audit.csv"
ACCEPTANCE_JSON = ARTIFACTS / "enrichment_acceptance_audit.json"
SUMMARY_JSON = ARTIFACTS / "enrichment_acceptance_summary.json"

FIELDNAMES = [
    "acceptance_key",
    "record_type",
    "record_id",
    "person_key",
    "display_name",
    "role",
    "claim_type",
    "accepted_claim_type",
    "accepted_claim_value",
    "source_key",
    "source_url",
    "prior_decision",
    "acceptance_status",
    "assurance_level",
    "confidence",
    "non_name_anchor_count",
    "corroborating_source_count",
    "corroborating_sources_json",
    "anchor_features_json",
    "acceptance_blocker",
    "recommended_next_action",
    "evidence_json",
    "audited_at",
]

MACHINE_ACCEPTANCE_PUBMED_DECISIONS = {"review_ready_high_anchor"}
REVIEW_READY_PUBMED_DECISIONS = {"review_ready_high_anchor", "review_ready_training_topic_anchor"}
SECONDARY_DECISIONS = {
    "needs_secondary_identity_anchor",
    "npi_candidate_with_partial_anchor",
    "orcid_profile_with_partial_anchor",
    "attending_training_claim_needs_identity_link",
}
LOW_SIGNAL_DECISIONS = {"low_signal_candidate", "npi_low_signal_candidate", "orcid_low_signal_candidate", "discovery_only"}
PROFILE_CONTEXT_DECISIONS = {
    "profile_background_candidate",
    "profile_interest_context_candidate",
    "profile_personal_context_display_review",
    "profile_context_candidate",
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def existing_rows() -> dict[str, dict]:
    if not ACCEPTANCE_CSV.exists():
        return {}
    with ACCEPTANCE_CSV.open(newline="", encoding="utf-8") as handle:
        return {row["acceptance_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, new_value: str) -> str:
    prior = existing.get(row["acceptance_key"])
    if not prior:
        return new_value
    for field in FIELDNAMES:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return new_value
    return prior.get("audited_at") or new_value


def acceptance_key(row: dict) -> str:
    basis = f"{row.get('record_type')}|{row.get('record_id')}|{row.get('decision')}"
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]
    return f"enrichment_acceptance_{digest}"


def rows_by_id(conn: sqlite3.Connection, query: str) -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    return {str(row[0]): dict(row) for row in conn.execute(query)}


def load_context(conn: sqlite3.Connection) -> dict:
    return {
        "evidence_claims": rows_by_id(
            conn,
            """
            SELECT evidence_id, claim_value, evidence_json, match_features_json, reconciliation_notes
            FROM evidence_claims
            """,
        ),
        "career_events": rows_by_id(
            conn,
            """
            SELECT career_event_id, role_title, organization_name, department, program_context,
                   event_year, evidence_json, match_features_json
            FROM career_events
            """,
        ),
        "npi_candidates": {
            row["candidate_key"]: dict(row)
            for row in conn.execute(
                """
                SELECT candidate_key, person_key, npi, provider_name, provider_credential,
                       primary_taxonomy, taxonomy_descriptions, practice_city, practice_state,
                       candidate_status, confidence, source_url, match_features_json, evidence_json
                FROM npi_candidate_claims
                """
            )
        },
    }


def npi_decisions_by_person(decisions: list[dict], context: dict) -> dict[str, list[dict]]:
    output: dict[str, list[dict]] = defaultdict(list)
    npi_candidates = context["npi_candidates"]
    for row in decisions:
        if row.get("record_type") != "npi_candidate":
            continue
        if row.get("decision") != "npi_secondary_identity_anchor_review":
            continue
        person_key = row.get("person_key") or ""
        candidate = npi_candidates.get(row.get("record_id") or "", {})
        output[person_key].append(
            {
                "record_type": "npi_candidate",
                "record_id": row.get("record_id") or "",
                "decision": row.get("decision") or "",
                "npi": candidate.get("npi") or "",
                "provider_name": candidate.get("provider_name") or "",
                "primary_taxonomy": candidate.get("primary_taxonomy") or "",
                "practice_city": candidate.get("practice_city") or "",
                "practice_state": candidate.get("practice_state") or "",
                "confidence": row.get("confidence") or candidate.get("confidence") or "",
                "source_url": row.get("source_url") or candidate.get("source_url") or "",
                "match_features": row.get("match_features") or "",
            }
        )
    return output


def claim_context(row: dict, context: dict) -> tuple[str, dict]:
    record_type = row.get("record_type")
    record_id = row.get("record_id") or ""
    if record_type == "evidence_claim":
        claim = context["evidence_claims"].get(record_id, {})
        return claim.get("claim_value") or "", claim
    if record_type == "career_event":
        event = context["career_events"].get(record_id, {})
        parts = [
            event.get("role_title") or row.get("claim_type") or "",
            event.get("organization_name") or "",
            str(event.get("event_year") or "").strip(),
        ]
        return " | ".join(part for part in parts if part), event
    if record_type == "npi_candidate":
        npi = context["npi_candidates"].get(record_id, {})
        parts = [
            npi.get("npi") or "",
            npi.get("provider_name") or "",
            npi.get("primary_taxonomy") or "",
            ", ".join(part for part in [npi.get("practice_city") or "", npi.get("practice_state") or ""] if part),
        ]
        return " | ".join(part for part in parts if part), npi
    return "", {}


def structured_context(record: dict) -> dict:
    output = dict(record)
    for key in ["evidence_json", "match_features_json"]:
        if key in output:
            output[key] = parse_json(output.get(key), output.get(key))
    return output


def classify(row: dict, corroborating_sources: list[dict]) -> tuple[str, int, str, str]:
    decision = row.get("decision") or ""
    record_type = row.get("record_type") or ""
    claim_type = row.get("claim_type") or ""
    confidence = float(row.get("confidence") or 0.0)
    non_name_anchors = int(float(row.get("non_name_anchor_count") or 0))
    has_npi_anchor = bool(corroborating_sources)

    if (
        record_type == "evidence_claim"
        and claim_type == "pubmed_article_candidate"
        and decision in MACHINE_ACCEPTANCE_PUBMED_DECISIONS
        and confidence >= 0.95
        and non_name_anchors >= 4
        and has_npi_anchor
    ):
        return (
            "machine_acceptance_candidate_cross_source",
            4,
            "No blocker for non-mutating accepted-publication candidate status; final author-position/same-name sanity check remains recommended before display.",
            "promote_to_accepted_enrichment_after_final_duplicate_author_position_check",
        )
    if record_type == "evidence_claim" and claim_type == "pubmed_article_candidate" and decision in REVIEW_READY_PUBMED_DECISIONS:
        return (
            "review_ready_publication_identity",
            3,
            "Publication has strong non-name anchors but lacks the full cross-source acceptance bundle.",
            "review_article_author_affiliation_topic_and_secondary_identity_anchors",
        )
    if record_type == "npi_candidate" and decision == "npi_secondary_identity_anchor_review":
        return (
            "secondary_identity_anchor_available",
            2,
            "NPI is useful corroborating evidence but not accepted roster or publication truth by itself.",
            "use_as_secondary_identity_anchor_with_profile_publication_or_roster_context",
        )
    if record_type == "evidence_claim" and claim_type == "orcid_profile_candidate" and decision == "orcid_secondary_identity_anchor_review":
        return (
            "secondary_identity_anchor_available",
            2,
            "ORCID is useful corroborating evidence but not accepted roster or publication truth by itself.",
            "use_as_secondary_identity_anchor_with_profile_publication_or_roster_context",
        )
    if decision == "attending_training_claim_review_ready":
        return (
            "review_ready_attending_training_claim",
            3,
            "Official profile training claim needs a historical trainee bridge before trend acceptance.",
            "seek_historical_roster_cv_or_biosketch_bridge_before_accepting_trend",
        )
    if decision == "review_ready_profile_background_field":
        return (
            "review_ready_profile_background",
            2,
            "Official trainee profile background field is roster-linked but still requires reviewer acceptance before becoming an accepted enrichment fact.",
            "review_profile_background_field_before_acceptance",
        )
    if decision in PROFILE_CONTEXT_DECISIONS:
        return (
            "profile_context_candidate",
            1,
            "Official trainee profile evidence is useful context but is not accepted roster, research, contact, or trend truth.",
            "retain_profile_context_with_display_policy",
        )
    if decision.startswith("current_attending_endpoint"):
        return (
            "attending_endpoint_only",
            1,
            "Current Penn attending endpoint does not prove prior Penn trainee status.",
            "find_training_history_or_start_date_evidence_before_trend_use",
        )
    if decision in SECONDARY_DECISIONS:
        return (
            "needs_secondary_identity_anchor",
            2,
            "Evidence has partial anchors but needs another independent source before acceptance.",
            "collect_profile_identifier_coauthor_or_historical_bridge_evidence",
        )
    if decision in LOW_SIGNAL_DECISIONS:
        return (
            "low_signal_or_discovery_only",
            0,
            "Evidence is discovery-only or too weak for identity acceptance.",
            "deprioritize_until_stronger_independent_source_appears",
        )
    if decision == "candidate_with_partial_anchor" or decision == "npi_candidate_with_partial_anchor":
        return (
            "partial_anchor_candidate",
            1,
            "Evidence has at least one non-name anchor but does not meet review-ready policy.",
            "collect_additional_identity_anchors",
        )
    return (
        "context_or_review_queue_only",
        1,
        "Evidence remains useful queue context but is not acceptance-ready.",
        "retain_in_reconciliation_queue",
    )


def audit_rows(conn: sqlite3.Connection, decisions: list[dict], audited_at: str) -> list[dict]:
    context = load_context(conn)
    npi_by_person = npi_decisions_by_person(decisions, context)
    rows = []
    for row in decisions:
        claim_value, raw_context = claim_context(row, context)
        corroborating_sources = []
        if row.get("record_type") == "evidence_claim" and row.get("claim_type") == "pubmed_article_candidate":
            corroborating_sources = npi_by_person.get(row.get("person_key") or "", [])
        status, assurance, blocker, action = classify(row, corroborating_sources)
        features = [feature.strip() for feature in (row.get("match_features") or "").split(";") if feature.strip()]
        evidence = {
            "decision_row": row,
            "source_record": structured_context(raw_context),
            "corroborating_sources": corroborating_sources,
            "policy": {
                "machine_acceptance_candidate_cross_source": (
                    "PubMed article candidate requires review_ready_high_anchor, confidence >= 0.95, "
                    "at least four non-name anchors, and an NPI secondary identity anchor for the same person_key."
                )
            },
        }
        rows.append(
            {
                "acceptance_key": acceptance_key(row),
                "record_type": row.get("record_type") or "",
                "record_id": row.get("record_id") or "",
                "person_key": row.get("person_key") or "",
                "display_name": row.get("display_name") or "",
                "role": row.get("role") or "",
                "claim_type": row.get("claim_type") or "",
                "accepted_claim_type": row.get("claim_type") or "",
                "accepted_claim_value": claim_value,
                "source_key": row.get("source_key") or "",
                "source_url": row.get("source_url") or "",
                "prior_decision": row.get("decision") or "",
                "acceptance_status": status,
                "assurance_level": assurance,
                "confidence": float(row.get("confidence") or 0.0),
                "non_name_anchor_count": int(float(row.get("non_name_anchor_count") or 0)),
                "corroborating_source_count": len(corroborating_sources),
                "corroborating_sources_json": dumps(corroborating_sources),
                "anchor_features_json": dumps(features),
                "acceptance_blocker": blocker,
                "recommended_next_action": action,
                "evidence_json": dumps(evidence),
                "audited_at": audited_at,
            }
        )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DROP TABLE IF EXISTS enrichment_acceptance_audit")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM enrichment_acceptance_audit")
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if not db_row.get("person_key"):
            db_row["person_key"] = None
        db_rows.append(db_row)
    conn.executemany(
        """
        INSERT INTO enrichment_acceptance_audit
        (acceptance_key, record_type, record_id, person_key, display_name, role,
         claim_type, accepted_claim_type, accepted_claim_value, source_key, source_url,
         prior_decision, acceptance_status, assurance_level, confidence,
         non_name_anchor_count, corroborating_source_count, corroborating_sources_json,
         anchor_features_json, acceptance_blocker, recommended_next_action,
         evidence_json, audited_at)
        VALUES
        (:acceptance_key, :record_type, :record_id, :person_key, :display_name, :role,
         :claim_type, :accepted_claim_type, :accepted_claim_value, :source_key, :source_url,
         :prior_decision, :acceptance_status, :assurance_level, :confidence,
         :non_name_anchor_count, :corroborating_source_count, :corroborating_sources_json,
         :anchor_features_json, :acceptance_blocker, :recommended_next_action,
         :evidence_json, :audited_at)
        """,
        db_rows,
    )


def write_outputs(rows: list[dict], audited_at: str) -> dict:
    existing = existing_rows()
    for row in rows:
        row["audited_at"] = stable_audited_at(existing, row, audited_at)
    write_csv(ACCEPTANCE_CSV, rows)
    ACCEPTANCE_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    by_status = Counter(row["acceptance_status"] for row in rows)
    by_action = Counter(row["recommended_next_action"] for row in rows)
    by_claim_type = Counter(row["claim_type"] for row in rows)
    by_assurance = Counter(str(row["assurance_level"]) for row in rows)
    machine_rows = [
        row for row in rows if row["acceptance_status"] == "machine_acceptance_candidate_cross_source"
    ]
    summary = {
        "audited_at": max((row["audited_at"] for row in rows), default=audited_at),
        "acceptance_rows": len(rows),
        "person_rows": len({row["person_key"] or row["display_name"] for row in rows}),
        "machine_acceptance_candidate_rows": len(machine_rows),
        "machine_acceptance_candidate_people": len({row["person_key"] for row in machine_rows if row["person_key"]}),
        "review_ready_publication_rows": by_status.get("review_ready_publication_identity", 0),
        "secondary_identity_anchor_rows": by_status.get("secondary_identity_anchor_available", 0),
        "by_acceptance_status": dict(sorted(by_status.items())),
        "by_recommended_action": dict(sorted(by_action.items())),
        "by_claim_type": dict(sorted(by_claim_type.items())),
        "by_assurance_level": dict(sorted(by_assurance.items())),
        "csv": "artifacts/data/enrichment_acceptance_audit.csv",
        "json": "artifacts/data/enrichment_acceptance_audit.json",
        "acceptance_rule": (
            "Do not mutate roster truth. A PubMed article becomes a machine-acceptance candidate only with "
            "review_ready_high_anchor, confidence >= 0.95, at least four non-name anchors, and an NPI secondary "
            "identity anchor for the same person."
        ),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--decisions", type=Path, default=DECISIONS_CSV)
    args = parser.parse_args()
    decisions = read_csv(args.decisions)
    audited_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = audit_rows(conn, decisions, audited_at)
    summary = write_outputs(rows, audited_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    print(dumps(summary))


if __name__ == "__main__":
    main()
