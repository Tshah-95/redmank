#!/usr/bin/env python3
"""Materialize person-level recursive enrichment action packets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "person_enrichment_action_packets.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_action_packets.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_action_packet_summary.json"

FIELDS = [
    "action_packet_key",
    "person_key",
    "display_name",
    "role",
    "current_status",
    "programs",
    "coverage_score",
    "coverage_band",
    "dossier_status",
    "display_safety_status",
    "task_count",
    "critical_task_count",
    "high_task_count",
    "network_task_count",
    "manual_review_task_count",
    "collector_ready_task_count",
    "profile_workbench_count",
    "profile_candidate_count",
    "official_profile_candidate_count",
    "unsearched_profile_query_count",
    "blocked_profile_query_count",
    "contact_contract_count",
    "unverified_contact_count",
    "domain_review_contact_count",
    "review_packet_count",
    "review_ready_packet_count",
    "evidence_record_count",
    "source_count",
    "accepted_enrichment_count",
    "candidate_evidence_count",
    "review_ready_evidence_count",
    "publication_candidate_count",
    "npi_candidate_count",
    "primary_action_lane",
    "packet_status",
    "priority",
    "priority_band",
    "primary_blocker",
    "recommended_next_action",
    "required_next_evidence",
    "top_task_types_json",
    "top_source_families_json",
    "execution_lane_counts_json",
    "automation_status_counts_json",
    "profile_discovery_lanes_json",
    "contact_verification_lanes_json",
    "review_triage_lanes_json",
    "command_hints_json",
    "next_action_sequence_json",
    "top_source_urls",
    "downstream_artifacts_json",
    "evidence_json",
    "generated_at",
]

csv.field_size_limit(sys.maxsize)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key_for(prefix: str, parts: list[object]) -> str:
    return f"{prefix}_{sha256_text(dumps(parts))[:20]}"


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def compact_counter(counter: Counter, limit: int = 12) -> dict:
    return {key: value for key, value in counter.most_common(limit) if key}


def compact_values(values: list[str], limit: int = 12) -> list[str]:
    seen = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
    return seen[:limit]


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["action_packet_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["action_packet_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def group_by_person(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        person_key = row.get("person_key") or ""
        if person_key:
            grouped[person_key].append(row)
    return grouped


def readiness_rows(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    return group_by_person(
        sqlite_rows(
            conn,
            """
            SELECT r.*,
                   q.evidence_requirement,
                   q.operator_action,
                   q.blocking_risk,
                   q.query,
                   q.source_targets_json,
                   q.expected_claim_types_json
            FROM person_enrichment_execution_readiness r
            JOIN person_enrichment_work_queue q ON q.task_key = r.task_key
            """,
        )
    )


def profile_rows(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    return group_by_person(sqlite_rows(conn, "SELECT * FROM official_profile_discovery_workbench"))


def contact_rows(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    return group_by_person(sqlite_rows(conn, "SELECT * FROM contact_verification_contracts"))


def review_rows(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    return group_by_person(sqlite_rows(conn, "SELECT * FROM person_evidence_review_batch_packets"))


def priority_band(priority: int) -> str:
    if priority >= 1000:
        return "critical"
    if priority >= 700:
        return "high"
    if priority >= 350:
        return "medium"
    return "low"


def command_hints(rows: list[dict]) -> list[str]:
    return compact_values([row.get("command_hint") or "" for row in rows if row.get("command_hint")])


def source_urls(dossier: dict, profiles: list[dict], contacts: list[dict], reviews: list[dict]) -> str:
    urls: list[str] = []
    urls.extend(split_semicolon(dossier.get("top_source_urls")))
    for row in profiles:
        urls.extend(split_semicolon(row.get("best_candidate_url")))
    for row in contacts:
        urls.extend(split_semicolon(row.get("source_url")))
    for row in reviews:
        urls.extend(split_semicolon(row.get("top_source_urls")))
    return "; ".join(compact_values(urls, limit=18))


def action_sequence(
    dossier: dict,
    readiness: list[dict],
    profiles: list[dict],
    contacts: list[dict],
    reviews: list[dict],
) -> list[dict]:
    actions = []
    if reviews:
        actions.append(
            {
                "lane": "person_evidence_review",
                "action": "review_packet_and_record_decision",
                "count": len(reviews),
                "artifact": "artifacts/data/person_evidence_review_batch_packets.csv",
            }
        )
    official_profile_candidates = sum(as_int(row.get("official_candidate_count")) for row in profiles)
    if official_profile_candidates:
        actions.append(
            {
                "lane": "official_profile_review",
                "action": "review_profile_candidate_and_record_decision",
                "count": official_profile_candidates,
                "artifact": "artifacts/data/official_profile_reviewer_decision_queue.csv",
            }
        )
    unsearched_profile_queries = sum(as_int(row.get("unsearched_query_count")) for row in profiles)
    if unsearched_profile_queries:
        actions.append(
            {
                "lane": "official_profile_discovery",
                "action": "execute_profile_search_or_direct_probe_queries",
                "count": unsearched_profile_queries,
                "artifact": "artifacts/data/official_profile_discovery_workbench.csv",
            }
        )
    if contacts:
        actions.append(
            {
                "lane": "contact_verification",
                "action": "reobserve_public_contact_or_record_reviewer_decision",
                "count": len(contacts),
                "artifact": "artifacts/data/contact_verification_reviewer_decision_queue.csv",
            }
        )
    if readiness:
        actions.append(
            {
                "lane": "enrichment_execution",
                "action": "run_queue_task_collectors_then_rebuild_acceptance_ledgers",
                "count": len(readiness),
                "artifact": "artifacts/data/person_enrichment_execution_readiness.csv",
            }
        )
    if not actions:
        actions.append(
            {
                "lane": "monitor_or_refresh",
                "action": dossier.get("recommended_next_action") or "monitor_refresh_and_diff",
                "count": 1,
                "artifact": "artifacts/data/person_enrichment_dossiers.csv",
            }
        )
    return actions


def choose_lane(
    readiness: list[dict],
    profiles: list[dict],
    contacts: list[dict],
    reviews: list[dict],
) -> tuple[str, str, str, str]:
    official_profile_candidates = sum(as_int(row.get("official_candidate_count")) for row in profiles)
    unsearched_profile_queries = sum(as_int(row.get("unsearched_query_count")) for row in profiles)
    blocked_profile_queries = sum(as_int(row.get("blocked_query_count")) for row in profiles)
    domain_review_contacts = sum(1 for row in contacts if row.get("domain_status") == "likely_domain_typo_review")
    collector_ready = sum(
        1
        for row in readiness
        if row.get("automation_status", "").startswith("collector_available")
        or row.get("automation_status") == "manual_review_packet_available"
    )
    manual_review = sum(as_int(row.get("requires_manual_review")) for row in readiness)
    if reviews:
        return (
            "person_evidence_review",
            "review_packet_ready",
            "none",
            "review evidence packets and record matching-fingerprint reviewer decisions",
        )
    if official_profile_candidates:
        return (
            "official_profile_review",
            "official_profile_candidate_ready",
            "profile_url_not_accepted_until_reviewer_decision",
            "review official profile candidate and record decision",
        )
    if domain_review_contacts:
        return (
            "contact_domain_review",
            "contact_domain_review_required",
            "contact_domain_needs_review",
            "review contact domain before contact verification",
        )
    if blocked_profile_queries:
        return (
            "profile_search_retry",
            "search_endpoint_retry_required",
            "profile_search_endpoint_blocked",
            "retry or replace blocked profile search query",
        )
    if unsearched_profile_queries:
        return (
            "official_profile_discovery",
            "profile_search_ready",
            "profile_search_not_executed",
            "execute profile discovery queries",
        )
    if collector_ready:
        return (
            "enrichment_collector_execution",
            "collector_execution_ready",
            "none",
            "run queued collector and feed output through review ledgers",
        )
    if contacts:
        return (
            "contact_verification",
            "contact_reobservation_ready",
            "contact_unverified",
            "reobserve contact on official source or record reviewer verification",
        )
    if manual_review:
        return (
            "manual_review",
            "manual_review_ready",
            "review_required",
            "record manual review decision",
        )
    return ("monitor_or_refresh", "monitoring_packet", "none", "monitor next refresh and diff")


def build_packet(
    dossier: dict,
    readiness: list[dict],
    profiles: list[dict],
    contacts: list[dict],
    reviews: list[dict],
    generated_at: str,
) -> dict:
    lane, status, blocker, action = choose_lane(readiness, profiles, contacts, reviews)
    task_priorities = [as_int(row.get("priority")) for row in readiness]
    profile_priorities = [as_int(row.get("discovery_priority")) for row in profiles]
    review_priorities = [as_int(row.get("triage_priority")) for row in reviews]
    contact_priorities = [650 for _ in contacts]
    priorities = task_priorities + profile_priorities + review_priorities + contact_priorities + [
        as_int(dossier.get("max_review_priority")),
        as_int(dossier.get("coverage_score")),
    ]
    priority = max(priorities) if priorities else 0
    sequence = action_sequence(dossier, readiness, profiles, contacts, reviews)
    required_next_evidence = []
    required_next_evidence.extend(row.get("evidence_requirement") or "" for row in readiness)
    required_next_evidence.extend(row.get("evidence_required") or "" for row in profiles)
    required_next_evidence.extend(row.get("evidence_required_to_verify") or "" for row in contacts)
    required_next_evidence.extend(row.get("required_reviewer_action") or "" for row in reviews)
    downstream_artifacts = [
        "artifacts/data/person_enrichment_dossiers.csv",
        "artifacts/data/person_enrichment_execution_readiness.csv",
        "artifacts/data/official_profile_discovery_workbench.csv",
        "artifacts/data/contact_verification_contracts.csv",
        "artifacts/data/person_evidence_review_batch_packets.csv",
        "artifacts/data/person_enrichment_action_packets.csv",
    ]
    evidence = {
        "policy": {
            "packet": "Non-mutating person-level work packet for recursive enrichment.",
            "acceptance": "Actions must feed source-specific reviewer, contact, profile, evidence, or temporal ledgers before person truth changes.",
            "privacy": "Public contact candidates remain candidate-only unless verified by contact assurance contracts or reviewer decisions.",
        },
        "dossier": {
            key: dossier.get(key, "")
            for key in [
                "dossier_key",
                "person_key",
                "display_name",
                "coverage_score",
                "coverage_band",
                "dossier_status",
                "display_safety_status",
                "recommended_next_action",
                "missing_surface_summary",
            ]
        },
        "action_sequence": sequence,
        "top_readiness_tasks": [
            {
                "task_key": row.get("task_key") or "",
                "task_type": row.get("task_type") or "",
                "source_family": row.get("source_family") or "",
                "priority": as_int(row.get("priority")),
                "command_hint": row.get("command_hint") or "",
            }
            for row in sorted(readiness, key=lambda item: -as_int(item.get("priority")))[:8]
        ],
        "top_profile_candidates": [
            {
                "profile_workbench_key": row.get("profile_workbench_key") or "",
                "best_candidate_status": row.get("best_candidate_status") or "",
                "best_candidate_url": row.get("best_candidate_url") or "",
                "discovery_lane": row.get("discovery_lane") or "",
                "discovery_priority": as_int(row.get("discovery_priority")),
            }
            for row in sorted(profiles, key=lambda item: -as_int(item.get("discovery_priority")))[:5]
        ],
        "top_review_packets": [
            {
                "batch_packet_key": row.get("batch_packet_key") or "",
                "reviewer_decision_key": row.get("reviewer_decision_key") or "",
                "triage_lane": row.get("triage_lane") or "",
                "triage_priority": as_int(row.get("triage_priority")),
                "packet_fingerprint": row.get("packet_fingerprint") or "",
            }
            for row in sorted(reviews, key=lambda item: -as_int(item.get("triage_priority")))[:8]
        ],
    }
    return {
        "action_packet_key": key_for("person_enrichment_action_packet", [dossier["person_key"]]),
        "person_key": dossier["person_key"],
        "display_name": dossier.get("display_name") or "",
        "role": dossier.get("role") or "",
        "current_status": dossier.get("current_status") or "",
        "programs": dossier.get("programs") or "",
        "coverage_score": as_int(dossier.get("coverage_score")),
        "coverage_band": dossier.get("coverage_band") or "",
        "dossier_status": dossier.get("dossier_status") or "",
        "display_safety_status": dossier.get("display_safety_status") or "",
        "task_count": len(readiness),
        "critical_task_count": sum(1 for row in readiness if row.get("priority_band") == "critical"),
        "high_task_count": sum(1 for row in readiness if row.get("priority_band") == "high"),
        "network_task_count": sum(as_int(row.get("requires_network")) for row in readiness),
        "manual_review_task_count": sum(as_int(row.get("requires_manual_review")) for row in readiness),
        "collector_ready_task_count": sum(
            1
            for row in readiness
            if row.get("automation_status", "").startswith("collector_available")
            or row.get("automation_status") == "manual_review_packet_available"
        ),
        "profile_workbench_count": len(profiles),
        "profile_candidate_count": sum(as_int(row.get("candidate_count")) for row in profiles),
        "official_profile_candidate_count": sum(as_int(row.get("official_candidate_count")) for row in profiles),
        "unsearched_profile_query_count": sum(as_int(row.get("unsearched_query_count")) for row in profiles),
        "blocked_profile_query_count": sum(as_int(row.get("blocked_query_count")) for row in profiles),
        "contact_contract_count": len(contacts),
        "unverified_contact_count": sum(1 for row in contacts if row.get("operational_use_status") != "verified_current_contact"),
        "domain_review_contact_count": sum(1 for row in contacts if row.get("domain_status") == "likely_domain_typo_review"),
        "review_packet_count": len(reviews),
        "review_ready_packet_count": sum(1 for row in reviews if row.get("support_status") == "ready_for_packet_review"),
        "evidence_record_count": sum(as_int(row.get("evidence_record_count")) for row in reviews),
        "source_count": sum(as_int(row.get("source_count")) for row in reviews),
        "accepted_enrichment_count": as_int(dossier.get("accepted_enrichment_count")),
        "candidate_evidence_count": as_int(dossier.get("candidate_evidence_count")),
        "review_ready_evidence_count": as_int(dossier.get("review_ready_evidence_count")),
        "publication_candidate_count": as_int(dossier.get("publication_candidate_count")),
        "npi_candidate_count": as_int(dossier.get("npi_candidate_count")),
        "primary_action_lane": lane,
        "packet_status": status,
        "priority": priority,
        "priority_band": priority_band(priority),
        "primary_blocker": blocker,
        "recommended_next_action": action,
        "required_next_evidence": "; ".join(compact_values([value for value in required_next_evidence if value], 8)),
        "top_task_types_json": dumps(compact_counter(Counter(row.get("task_type") or "" for row in readiness))),
        "top_source_families_json": dumps(compact_counter(Counter(row.get("source_family") or "" for row in readiness))),
        "execution_lane_counts_json": dumps(compact_counter(Counter(row.get("execution_lane") or "" for row in readiness))),
        "automation_status_counts_json": dumps(compact_counter(Counter(row.get("automation_status") or "" for row in readiness))),
        "profile_discovery_lanes_json": dumps(compact_counter(Counter(row.get("discovery_lane") or "" for row in profiles))),
        "contact_verification_lanes_json": dumps(compact_counter(Counter(row.get("verification_lane") or "" for row in contacts))),
        "review_triage_lanes_json": dumps(compact_counter(Counter(row.get("triage_lane") or "" for row in reviews))),
        "command_hints_json": dumps(command_hints(readiness)),
        "next_action_sequence_json": dumps(sequence),
        "top_source_urls": source_urls(dossier, profiles, contacts, reviews),
        "downstream_artifacts_json": dumps(downstream_artifacts),
        "evidence_json": dumps(evidence),
        "generated_at": generated_at,
    }


def materialize(conn: sqlite3.Connection) -> list[dict]:
    existing = read_existing()
    timestamp = now_utc()
    dossiers = sqlite_rows(conn, "SELECT * FROM person_enrichment_dossiers ORDER BY display_name")
    readiness_by_person = readiness_rows(conn)
    profiles_by_person = profile_rows(conn)
    contacts_by_person = contact_rows(conn)
    reviews_by_person = review_rows(conn)
    rows = []
    for dossier in dossiers:
        person_key = dossier.get("person_key") or ""
        if not person_key:
            continue
        row = build_packet(
            dossier,
            readiness_by_person.get(person_key, []),
            profiles_by_person.get(person_key, []),
            contacts_by_person.get(person_key, []),
            reviews_by_person.get(person_key, []),
            timestamp,
        )
        row["generated_at"] = stable_generated_at(existing, row, timestamp)
        rows.append(row)
    return sorted(rows, key=lambda row: (-row["priority"], row["display_name"], row["person_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_enrichment_action_packets")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    fields = ", ".join(FIELDS)
    conn.executemany(f"INSERT INTO person_enrichment_action_packets ({fields}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict]) -> None:
    payload = {
        "action_packet_rows": len(rows),
        "person_count": len({row["person_key"] for row in rows}),
        "critical_packet_rows": sum(1 for row in rows if row["priority_band"] == "critical"),
        "high_packet_rows": sum(1 for row in rows if row["priority_band"] == "high"),
        "review_packet_ready_rows": sum(1 for row in rows if row["packet_status"] == "review_packet_ready"),
        "collector_execution_ready_rows": sum(1 for row in rows if row["packet_status"] == "collector_execution_ready"),
        "profile_search_ready_rows": sum(1 for row in rows if row["packet_status"] == "profile_search_ready"),
        "contact_reobservation_ready_rows": sum(1 for row in rows if row["packet_status"] == "contact_reobservation_ready"),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_primary_action_lane": dict(sorted(Counter(row["primary_action_lane"] for row in rows).items())),
        "by_priority_band": dict(sorted(Counter(row["priority_band"] for row in rows).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "top_packets": [
            {
                "person_key": row["person_key"],
                "display_name": row["display_name"],
                "role": row["role"],
                "priority": row["priority"],
                "priority_band": row["priority_band"],
                "packet_status": row["packet_status"],
                "primary_action_lane": row["primary_action_lane"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:20]
        ],
        "policy": "Action packets are non-mutating. They assemble per-person next actions from dossiers, execution readiness, profile discovery, contact contracts, and evidence review packets.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    with conn:
        rows = materialize(conn)
        write_db(conn, rows)
        write_csv(CSV_PATH, rows)
        JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
    conn.close()
    print(dumps({"person_enrichment_action_packets": len(rows)}))


if __name__ == "__main__":
    main()
