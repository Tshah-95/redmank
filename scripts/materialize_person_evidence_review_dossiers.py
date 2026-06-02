#!/usr/bin/env python3
"""Materialize per-packet dossiers for person evidence review."""

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
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "person_evidence_review_dossiers.csv"
JSON_PATH = ARTIFACTS / "person_evidence_review_dossiers.json"
SUMMARY_PATH = ARTIFACTS / "person_evidence_review_dossier_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "dossier_key",
    "reviewer_decision_key",
    "triage_key",
    "packet_key",
    "person_or_name_key",
    "person_key",
    "display_name",
    "role",
    "current_programs",
    "review_kind",
    "packet_status",
    "triage_lane",
    "triage_priority",
    "decision_difficulty",
    "risk_level",
    "review_route",
    "review_packet_summary",
    "review_ready_record_count",
    "evidence_record_count",
    "publication_candidate_count",
    "npi_candidate_count",
    "orcid_candidate_count",
    "official_profile_candidate_count",
    "attending_candidate_count",
    "source_count",
    "top_source_domains",
    "top_source_urls",
    "top_claim_types",
    "top_match_features",
    "decision_counts_json",
    "top_evidence_records_json",
    "missing_evidence_summary",
    "recommended_reviewer_action",
    "acceptance_boundary",
    "packet_fingerprint",
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


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    seen: set[str] = set()
    values: list[str] = []
    for raw in str(value).split(";"):
        item = raw.strip()
        if item and item not in seen:
            values.append(item)
            seen.add(item)
    return values


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def domain_for(url: str | None) -> str:
    if not url:
        return ""
    host = urlparse(url).netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def source_family_for(url: str | None, claim_type: str | None) -> str:
    domain = domain_for(url)
    claim = (claim_type or "").lower()
    if "pubmed" in domain or "pubmed" in claim:
        return "pubmed_publication"
    if "doi.org" in domain or "orcid_work" in claim:
        return "doi_or_orcid_work"
    if "orcid.org" in domain or "orcid" in claim:
        return "orcid_identity"
    if "npiregistry.cms.hhs.gov" in domain or "npi" in claim:
        return "npi_identity"
    if "pennmedicine.org" in domain or "upenn.edu" in domain or "penn.edu" in domain:
        return "official_penn_context"
    if "openalex.org" in domain or "research_author" in claim:
        return "openalex_author_context"
    return "other_public_source"


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["dossier_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["dossier_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def sqlite_rows(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query, params)]


def current_programs_by_person(conn: sqlite3.Connection) -> dict[str, str]:
    rows = sqlite_rows(
        conn,
        """
        SELECT m.person_key,
               p.program_name,
               m.training_year_label
        FROM person_program_memberships m
        JOIN programs p ON p.program_key = m.program_key
        ORDER BY m.person_key, p.program_name, m.training_year_label
        """,
    )
    values: dict[str, list[str]] = {}
    for row in rows:
        label = row["program_name"]
        if row.get("training_year_label"):
            label = f"{label} ({row['training_year_label']})"
        values.setdefault(row["person_key"], [])
        if label not in values[row["person_key"]]:
            values[row["person_key"]].append(label)
    return {key: "; ".join(items[:6]) for key, items in values.items()}


def load_review_rows(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT q.*,
               t.triage_key,
               t.triage_lane,
               t.triage_priority,
               t.decision_difficulty,
               t.risk_level,
               t.likely_next_action,
               t.reviewer_prompt,
               p.publication_candidate_count,
               p.attending_candidate_count,
               p.current_attending_endpoint_count,
               p.evidence_json AS packet_evidence_json
        FROM person_evidence_reviewer_decision_queue q
        JOIN person_evidence_review_packets p
          ON p.packet_key = q.packet_key
        LEFT JOIN person_evidence_review_triage t
          ON t.reviewer_decision_key = q.reviewer_decision_key
        WHERE q.queue_status = 'ready_for_reviewer_decision'
        ORDER BY q.review_priority DESC, q.display_name, q.packet_key
        """,
    )


def dossier_key(row: dict) -> str:
    return "person_evidence_review_dossier_" + sha256_text(row["reviewer_decision_key"])[:20]


def clean_top_record(record: dict) -> dict:
    return {
        "record_type": record.get("record_type") or "",
        "record_id": record.get("record_id") or "",
        "claim_type": record.get("claim_type") or "",
        "decision": record.get("decision") or "",
        "confidence": as_float(record.get("confidence")),
        "priority": as_int(record.get("priority")),
        "source_family": source_family_for(record.get("source_url"), record.get("claim_type")),
        "source_domain": domain_for(record.get("source_url")),
        "source_url": record.get("source_url") or "",
        "match_features": record.get("match_features") or "",
        "required_next_evidence": record.get("required_next_evidence") or "",
    }


def review_route(row: dict, records: list[dict]) -> str:
    lane = row.get("triage_lane") or ""
    decisions = Counter(record.get("decision") or "" for record in records)
    families = Counter(record.get("source_family") or "" for record in records)
    if "attending" in lane:
        return "trend_bridge_manual_review"
    if decisions.get("review_ready_orcid_seeded_article") and (
        families.get("npi_identity") or families.get("orcid_identity") or families.get("doi_or_orcid_work")
    ):
        return "orcid_pubmed_publication_review"
    if families.get("npi_identity") and row.get("review_kind") == "mixed_identity_anchor_review":
        return "secondary_identity_anchor_then_publication_review"
    if families.get("official_penn_context"):
        return "official_profile_or_roster_anchor_review"
    if as_int(row.get("publication_candidate_count")):
        return "publication_identity_review"
    return "general_evidence_review"


def missing_evidence(row: dict, records: list[dict]) -> str:
    families = Counter(record.get("source_family") or "" for record in records)
    blockers: list[str] = []
    if as_int(row.get("publication_candidate_count")) and not (
        families.get("npi_identity") or families.get("orcid_identity") or families.get("official_penn_context")
    ):
        blockers.append("secondary_identity_or_official_profile_anchor")
    if any(record.get("decision") == "orcid_work_publication_review" for record in records):
        blockers.append("article_metadata_author_position_reconciliation")
    if "attending" in (row.get("review_kind") or ""):
        blockers.append("dated_historical_training_bridge")
    if row.get("risk_level") in {"display_safety_sensitive", "identity_collision_high"}:
        blockers.append(row["risk_level"])
    return "; ".join(blockers) if blockers else "reviewer_confirmation_required"


def packet_summary(row: dict, records: list[dict]) -> str:
    decisions = Counter(record.get("decision") or "unknown_decision" for record in records)
    families = Counter(record.get("source_family") or "unknown_source" for record in records)
    decision_text = ", ".join(f"{key}:{value}" for key, value in decisions.most_common(4))
    family_text = ", ".join(f"{key}:{value}" for key, value in families.most_common(4))
    return f"{as_int(row.get('review_ready_record_count'))} review-ready of {as_int(row.get('evidence_record_count'))} evidence rows; decisions [{decision_text}]; sources [{family_text}]"


def recommended_action(row: dict, route: str, missing: str) -> str:
    if route == "orcid_pubmed_publication_review":
        return "confirm_orcid_pubmed_author_identity_then_record_publication_decision"
    if route == "secondary_identity_anchor_then_publication_review":
        return "confirm_secondary_identity_anchor_before_accepting_publication_or_profile_claims"
    if route == "official_profile_or_roster_anchor_review":
        return "confirm_official_profile_or_roster_context_before_accepting_candidate_claims"
    if route == "trend_bridge_manual_review":
        return "confirm_recent_penn_training_bridge_before_accepting_attending_trend_fact"
    if "secondary_identity_or_official_profile_anchor" in missing:
        return "collect_or_confirm_independent_identity_anchor_before_acceptance"
    return row.get("likely_next_action") or "record_accept_reject_or_needs_more_evidence_decision"


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    programs = current_programs_by_person(conn)
    rows = []
    for row in load_review_rows(conn):
        packet_evidence = parse_json(row.get("packet_evidence_json"), {})
        top_records = [clean_top_record(record) for record in packet_evidence.get("top_records", [])]
        top_records = sorted(top_records, key=lambda item: (-item["priority"], -item["confidence"], item["source_url"]))[:12]
        decisions = Counter(record["decision"] or "unknown_decision" for record in top_records)
        claim_types = Counter(record["claim_type"] or "unknown_claim_type" for record in top_records)
        families = Counter(record["source_family"] or "unknown_source" for record in top_records)
        urls = []
        for value in split_semicolon(row.get("top_source_urls")):
            urls.append(value)
        if row.get("best_source_url"):
            urls.insert(0, row["best_source_url"])
        for record in top_records:
            if record["source_url"]:
                urls.append(record["source_url"])
        deduped_urls = []
        for url in urls:
            if url and url not in deduped_urls:
                deduped_urls.append(url)
        domains = []
        for url in deduped_urls:
            domain = domain_for(url)
            if domain and domain not in domains:
                domains.append(domain)
        route = review_route(row, top_records)
        missing = missing_evidence(row, top_records)
        evidence = {
            "person_evidence_reviewer_decision_queue": {
                key: row.get(key)
                for key in [
                    "reviewer_decision_key",
                    "packet_key",
                    "person_or_name_key",
                    "person_key",
                    "display_name",
                    "role",
                    "packet_status",
                    "review_kind",
                    "packet_fingerprint",
                ]
            },
            "triage": {
                "triage_key": row.get("triage_key") or "",
                "triage_lane": row.get("triage_lane") or "",
                "triage_priority": as_int(row.get("triage_priority")),
                "decision_difficulty": row.get("decision_difficulty") or "",
                "risk_level": row.get("risk_level") or "",
            },
            "top_evidence_records": top_records,
            "source_family_counts": dict(sorted(families.items())),
            "decision_counts": dict(sorted(decisions.items())),
            "claim_type_counts": dict(sorted(claim_types.items())),
            "policy": {
                "non_mutating": True,
                "accepted_fact_gate": (
                    "person_evidence_reviewer_decisions.csv with matching packet_fingerprint and all "
                    "identity/source/non-name-anchor/display confirmations"
                ),
            },
        }
        dossier = {
            "dossier_key": dossier_key(row),
            "reviewer_decision_key": row["reviewer_decision_key"],
            "triage_key": row.get("triage_key") or "",
            "packet_key": row["packet_key"],
            "person_or_name_key": row["person_or_name_key"],
            "person_key": row.get("person_key") or "",
            "display_name": row["display_name"],
            "role": row.get("role") or "",
            "current_programs": programs.get(row.get("person_key") or "", ""),
            "review_kind": row["review_kind"],
            "packet_status": row["packet_status"],
            "triage_lane": row.get("triage_lane") or "",
            "triage_priority": as_int(row.get("triage_priority")),
            "decision_difficulty": row.get("decision_difficulty") or "",
            "risk_level": row.get("risk_level") or "",
            "review_route": route,
            "review_packet_summary": packet_summary(row, top_records),
            "review_ready_record_count": as_int(row.get("review_ready_record_count")),
            "evidence_record_count": as_int(row.get("evidence_record_count")),
            "publication_candidate_count": as_int(row.get("publication_candidate_count")),
            "npi_candidate_count": sum(1 for record in top_records if record["source_family"] == "npi_identity"),
            "orcid_candidate_count": sum(
                1 for record in top_records if record["source_family"] in {"orcid_identity", "doi_or_orcid_work"}
            ),
            "official_profile_candidate_count": sum(
                1 for record in top_records if record["source_family"] == "official_penn_context"
            ),
            "attending_candidate_count": as_int(row.get("attending_candidate_count"))
            + as_int(row.get("current_attending_endpoint_count")),
            "source_count": len(domains),
            "top_source_domains": "; ".join(domains[:10]),
            "top_source_urls": "; ".join(deduped_urls[:12]),
            "top_claim_types": "; ".join(key for key, _ in claim_types.most_common(10)),
            "top_match_features": row.get("top_match_features") or "",
            "decision_counts_json": dumps(dict(sorted(decisions.items()))),
            "top_evidence_records_json": dumps(top_records),
            "missing_evidence_summary": missing,
            "recommended_reviewer_action": recommended_action(row, route, missing),
            "acceptance_boundary": (
                "Dossier is review support only; no enrichment, trend, contact, or roster fact is accepted without "
                "the explicit reviewer-decision and downstream acceptance ledgers."
            ),
            "packet_fingerprint": row["packet_fingerprint"],
            "evidence_json": dumps(evidence),
            "generated_at": "",
        }
        dossier["generated_at"] = stable_generated_at(existing, dossier, generated_at)
        rows.append({field: dossier[field] for field in FIELDS})
    return sorted(rows, key=lambda item: (-as_int(item["triage_priority"]), item["display_name"], item["packet_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_evidence_review_dossiers")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO person_evidence_review_dossiers ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_route = Counter(row["review_route"] for row in rows)
    by_risk = Counter(row["risk_level"] for row in rows)
    by_role = Counter(row["role"] or "unknown_role" for row in rows)
    by_missing = Counter(row["missing_evidence_summary"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "dossier_rows": len(rows),
        "person_count": len({row["person_or_name_key"] for row in rows}),
        "review_ready_record_count": sum(as_int(row["review_ready_record_count"]) for row in rows),
        "evidence_record_count": sum(as_int(row["evidence_record_count"]) for row in rows),
        "publication_candidate_count": sum(as_int(row["publication_candidate_count"]) for row in rows),
        "by_review_route": dict(sorted(by_route.items())),
        "by_risk_level": dict(sorted(by_risk.items())),
        "by_role": dict(sorted(by_role.items())),
        "top_missing_evidence": dict(by_missing.most_common(12)),
        "top_dossiers": [
            {
                "display_name": row["display_name"],
                "role": row["role"],
                "current_programs": row["current_programs"],
                "review_route": row["review_route"],
                "risk_level": row["risk_level"],
                "triage_priority": row["triage_priority"],
                "review_ready_record_count": row["review_ready_record_count"],
                "evidence_record_count": row["evidence_record_count"],
                "recommended_reviewer_action": row["recommended_reviewer_action"],
                "top_source_domains": row["top_source_domains"],
            }
            for row in rows[:25]
        ],
        "policy": "Dossiers are non-mutating review support. Accepted facts still require explicit reviewer decisions and downstream acceptance ledgers.",
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
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"person_evidence_review_dossiers": len(rows), "generated_at": generated_at}))


if __name__ == "__main__":
    main()
