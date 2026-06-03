#!/usr/bin/env python3
"""Materialize bounded reviewer batches for research identity corroboration rows."""

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

BATCH_CSV_PATH = ARTIFACTS / "research_identity_review_batches.csv"
BATCH_JSON_PATH = ARTIFACTS / "research_identity_review_batches.json"
MEMBER_CSV_PATH = ARTIFACTS / "research_identity_review_batch_members.csv"
MEMBER_JSON_PATH = ARTIFACTS / "research_identity_review_batch_members.json"
SUMMARY_PATH = ARTIFACTS / "research_identity_review_batch_summary.json"

MAX_MEMBERS_PER_BATCH = 40

csv.field_size_limit(sys.maxsize)

BATCH_FIELDS = [
    "review_batch_key",
    "execution_order",
    "research_identity_status",
    "recommended_review_route",
    "review_lane",
    "role",
    "batch_number",
    "batch_status",
    "ready_to_review",
    "person_count",
    "research_candidate_count",
    "review_ready_record_count",
    "scholarly_source_count",
    "non_name_anchor_count",
    "secondary_anchor_count",
    "conflict_count",
    "max_review_priority",
    "min_review_priority",
    "top_source_keys",
    "top_claim_types",
    "reviewer_prompt",
    "review_instructions",
    "acceptance_rule",
    "target_decision_artifact",
    "top_people_json",
    "evidence_json",
    "generated_at",
]

MEMBER_FIELDS = [
    "review_batch_member_key",
    "review_batch_key",
    "corroboration_key",
    "execution_order",
    "member_order",
    "member_fingerprint",
    "person_key",
    "display_name",
    "role",
    "programs",
    "current_training_states",
    "research_identity_status",
    "recommended_review_route",
    "review_priority",
    "scholarly_source_count",
    "research_candidate_count",
    "research_review_ready_count",
    "accepted_research_count",
    "pubmed_article_candidate_count",
    "pubmed_review_ready_count",
    "openalex_author_candidate_count",
    "openalex_review_ready_count",
    "orcid_profile_candidate_count",
    "orcid_work_candidate_count",
    "orcid_pubmed_article_candidate_count",
    "npi_candidate_count",
    "profile_candidate_count",
    "contact_candidate_count",
    "non_name_anchor_count",
    "persistent_identifier_count",
    "publication_identifier_count",
    "conflicting_identifier_count",
    "best_confidence",
    "top_source_keys",
    "top_claim_types",
    "required_next_evidence",
    "recommended_reviewer_action",
    "acceptance_boundary",
    "evidence_json",
    "generated_at",
]

METRIC_FIELDS = [
    "scholarly_source_count",
    "research_candidate_count",
    "research_review_ready_count",
    "accepted_research_count",
    "pubmed_article_candidate_count",
    "pubmed_review_ready_count",
    "openalex_author_candidate_count",
    "openalex_review_ready_count",
    "orcid_profile_candidate_count",
    "orcid_work_candidate_count",
    "orcid_pubmed_article_candidate_count",
    "npi_candidate_count",
    "profile_candidate_count",
    "contact_candidate_count",
    "non_name_anchor_count",
    "persistent_identifier_count",
    "publication_identifier_count",
    "conflicting_identifier_count",
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
    return [part.strip() for part in str(value).split(";") if part.strip()]


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def read_existing(path: Path, key_field: str) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row[key_field]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], key_field: str, fields: list[str], row: dict, timestamp: str) -> str:
    prior = existing.get(row[key_field])
    if not prior:
        return timestamp
    for field in fields:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def load_corroboration(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT *
        FROM research_identity_corroboration
        WHERE research_identity_status <> 'no_public_research_identity_signal'
        ORDER BY review_priority DESC, display_name, person_key
        """,
    )


def review_lane(row: dict) -> str:
    status = row.get("research_identity_status") or ""
    route = row.get("recommended_review_route") or ""
    if "conflict" in status or "conflict" in route:
        return "conflict_reconciliation"
    if status in {"strong_multi_source_research_identity_review", "multi_source_candidate_review"}:
        return "multi_source_identity_review"
    if "cross_source" in route:
        return "multi_source_identity_review"
    if status == "single_source_research_review_ready":
        return "single_source_publication_review"
    if status in {"research_candidate_only", "research_identity_candidate_only"}:
        return "secondary_anchor_collection"
    if status == "secondary_anchor_without_research_signal":
        return "research_relevance_decision"
    if "secondary" in route:
        return "secondary_anchor_review"
    return route or "research_identity_review"


def batch_status(rows: list[dict], lane: str) -> str:
    if not rows:
        return "empty_batch"
    if lane == "conflict_reconciliation":
        return "ready_for_conflict_reconciliation"
    if lane == "secondary_anchor_collection":
        return "ready_for_secondary_anchor_collection"
    if lane == "research_relevance_decision":
        return "ready_for_research_relevance_decision"
    if any(as_int(row.get("research_review_ready_count")) > 0 for row in rows):
        return "ready_for_research_identity_review"
    if any(as_int(row.get("scholarly_source_count")) >= 2 for row in rows):
        return "ready_for_multi_source_identity_review"
    return "ready_for_evidence_collection"


def recommended_reviewer_action(row: dict, lane: str) -> str:
    if lane == "conflict_reconciliation":
        return "resolve_identifier_conflicts_before_acceptance"
    if lane == "multi_source_identity_review":
        return "confirm_same_person_across_scholarly_sources_and_secondary_anchors"
    if lane == "secondary_anchor_review":
        return "confirm_secondary_identifier_or_official_profile_before_acceptance"
    if lane == "single_source_publication_review":
        return "add_non_name_anchor_or_mark_needs_more_evidence"
    if lane == "secondary_anchor_collection":
        return "collect_orcid_openalex_pubmed_profile_or_training_anchor"
    if lane == "research_relevance_decision":
        return "decide_whether_research_search_is_relevant_before_collection"
    return row.get("recommended_review_route") or "review_research_identity_evidence"


def reviewer_prompt(lane: str) -> str:
    if lane == "conflict_reconciliation":
        return "Resolve conflicting identifiers before any acceptance; require an official profile or independent non-name anchors."
    if lane == "multi_source_identity_review":
        return "Review multi-source scholarly identity agreement and record source-specific decisions only after confirming same-person anchors."
    if lane == "secondary_anchor_review":
        return "Use NPI, ORCID, official profile, contact, or training-state anchors to decide whether scholarly identity evidence is review-ready."
    if lane == "single_source_publication_review":
        return "Review single-source publication evidence; accept only with a matching non-name anchor or mark needs_more_evidence."
    if lane == "secondary_anchor_collection":
        return "Collect a second non-name identity anchor before reviewer acceptance."
    if lane == "research_relevance_decision":
        return "Decide whether a research identity search is relevant for this trainee before collecting more evidence."
    return "Review research identity corroboration and route decisions through the source-specific ledgers."


def review_instructions(lane: str) -> str:
    if lane == "conflict_reconciliation":
        return "Compare ORCID, PMID/DOI, OpenAlex, NPI/profile/contact, and training-state anchors; reject or quarantine ambiguous identifiers before accepting any person fact."
    if lane == "multi_source_identity_review":
        return "Confirm that scholarly sources point to the same person, that at least one non-name anchor supports the match, and that the current member_fingerprint matches the reviewed evidence."
    if lane == "secondary_anchor_review":
        return "Verify ownership of the secondary anchor, then decide whether it is strong enough to support research identity acceptance."
    if lane == "single_source_publication_review":
        return "Check publication identifiers, topic/program fit, author context, and Penn or prior-training anchors; otherwise request more evidence."
    if lane == "secondary_anchor_collection":
        return "Search for ORCID/OpenAlex/PubMed detail, official profiles, NPI/profile links, or prior-training anchors before any acceptance decision."
    if lane == "research_relevance_decision":
        return "Use role, program, training state, and available public signals to decide whether a research identity search should be executed."
    return "Review the corroboration evidence and record a source-specific decision with the current member_fingerprint."


def acceptance_rule() -> str:
    return (
        "Batches are non-mutating. Accept facts only through source-specific reviewer or acceptance ledgers "
        "after matching the current member_fingerprint and corroboration evidence."
    )


def compact_counter(values: list[str], limit: int = 12) -> str:
    counts: Counter = Counter()
    for value in values:
        for part in split_semicolon(value):
            counts[part] += 1
    return "; ".join(f"{value}:{count}" for value, count in counts.most_common(limit))


def secondary_anchor_count(row: dict) -> int:
    return (
        as_int(row.get("npi_candidate_count"))
        + as_int(row.get("profile_candidate_count"))
        + as_int(row.get("contact_candidate_count"))
        + as_int(row.get("persistent_identifier_count"))
    )


def member_fingerprint(row: dict) -> str:
    payload = {
        "corroboration_key": row.get("corroboration_key"),
        "person_key": row.get("person_key"),
        "research_identity_status": row.get("research_identity_status"),
        "recommended_review_route": row.get("recommended_review_route"),
        "review_priority": as_int(row.get("review_priority")),
        "metrics": {field: as_int(row.get(field)) for field in METRIC_FIELDS},
        "best_confidence": round(as_float(row.get("best_confidence")), 4),
        "top_source_keys": row.get("top_source_keys") or "",
        "top_claim_types": row.get("top_claim_types") or "",
        "required_next_evidence": row.get("required_next_evidence") or "",
        "acceptance_boundary": row.get("acceptance_boundary") or "",
        "evidence_json": row.get("evidence_json") or "",
    }
    return "research_identity_member_" + sha256_text(dumps(payload))[:24]


def review_batch_key(status: str, route: str, lane: str, role: str, batch_number: int, members: list[dict]) -> str:
    keys = [row.get("corroboration_key") for row in members]
    return "research_identity_review_batch_" + sha256_text(dumps([status, route, lane, role, batch_number, keys]))[:20]


def review_batch_member_key(batch_key: str, corroboration_key: str) -> str:
    return "research_identity_review_batch_member_" + sha256_text(f"{batch_key}:{corroboration_key}")[:20]


def top_people(rows: list[dict], limit: int = 12) -> list[dict]:
    people = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("review_priority")), item.get("display_name") or ""))[:limit]:
        people.append(
            {
                "corroboration_identifier": row.get("corroboration_key"),
                "person_identifier": row.get("person_key"),
                "display_name": row.get("display_name"),
                "role": row.get("role"),
                "research_identity_status": row.get("research_identity_status"),
                "review_priority": as_int(row.get("review_priority")),
                "research_candidate_count": as_int(row.get("research_candidate_count")),
                "review_ready_record_count": as_int(row.get("research_review_ready_count")),
                "non_name_anchor_count": as_int(row.get("non_name_anchor_count")),
                "conflicting_identifier_count": as_int(row.get("conflicting_identifier_count")),
            }
        )
    return people


def member_evidence(row: dict, lane: str, fingerprint: str) -> str:
    original_evidence = parse_json(row.get("evidence_json"), {})
    evidence = {
        "derived_from": "research_identity_corroboration",
        "corroboration_identifier": row.get("corroboration_key"),
        "person_identifier": row.get("person_key"),
        "member_fingerprint": fingerprint,
        "review_lane": lane,
        "policy": {
            "non_mutating": True,
            "corroboration_is_not_acceptance": True,
            "accepted_facts_flow_through": [
                "evidence_reconciliation_decisions",
                "person_evidence_reviewer_decisions",
                "enrichment_acceptance_audit",
                "accepted_enrichment_claims",
            ],
        },
        "corroboration_evidence": original_evidence,
    }
    return dumps(evidence)


def build_rows(corroboration_rows: list[dict], generated_at: str) -> tuple[list[dict], list[dict]]:
    existing_batches = read_existing(BATCH_CSV_PATH, "review_batch_key")
    existing_members = read_existing(MEMBER_CSV_PATH, "review_batch_member_key")
    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in corroboration_rows:
        lane = review_lane(row)
        grouped[
            (
                row.get("research_identity_status") or "",
                row.get("recommended_review_route") or "",
                lane,
                row.get("role") or "",
            )
        ].append(row)

    batch_rows: list[dict] = []
    member_rows: list[dict] = []
    for (status, route, lane, role), rows in grouped.items():
        sorted_rows = sorted(rows, key=lambda item: (-as_int(item.get("review_priority")), item.get("display_name") or ""))
        for batch_number, offset in enumerate(range(0, len(sorted_rows), MAX_MEMBERS_PER_BATCH), start=1):
            chunk = sorted_rows[offset : offset + MAX_MEMBERS_PER_BATCH]
            priorities = [as_int(row.get("review_priority")) for row in chunk]
            batch_key = review_batch_key(status, route, lane, role, batch_number, chunk)
            status_for_batch = batch_status(chunk, lane)
            secondary_count = sum(secondary_anchor_count(row) for row in chunk)
            conflict_count = sum(as_int(row.get("conflicting_identifier_count")) for row in chunk)
            batch_row = {
                "review_batch_key": batch_key,
                "execution_order": 0,
                "research_identity_status": status,
                "recommended_review_route": route,
                "review_lane": lane,
                "role": role,
                "batch_number": batch_number,
                "batch_status": status_for_batch,
                "ready_to_review": 1 if status_for_batch != "empty_batch" else 0,
                "person_count": len({row.get("person_key") for row in chunk}),
                "research_candidate_count": sum(as_int(row.get("research_candidate_count")) for row in chunk),
                "review_ready_record_count": sum(as_int(row.get("research_review_ready_count")) for row in chunk),
                "scholarly_source_count": sum(as_int(row.get("scholarly_source_count")) for row in chunk),
                "non_name_anchor_count": sum(as_int(row.get("non_name_anchor_count")) for row in chunk),
                "secondary_anchor_count": secondary_count,
                "conflict_count": conflict_count,
                "max_review_priority": max(priorities) if priorities else 0,
                "min_review_priority": min(priorities) if priorities else 0,
                "top_source_keys": compact_counter([row.get("top_source_keys") or "" for row in chunk]),
                "top_claim_types": compact_counter([row.get("top_claim_types") or "" for row in chunk]),
                "reviewer_prompt": reviewer_prompt(lane),
                "review_instructions": review_instructions(lane),
                "acceptance_rule": acceptance_rule(),
                "target_decision_artifact": "artifacts/data/evidence_reconciliation_decisions.csv",
                "top_people_json": dumps(top_people(chunk)),
                "evidence_json": dumps(
                    {
                        "derived_from": "research_identity_corroboration",
                        "corroboration_identifiers": [row.get("corroboration_key") for row in chunk],
                        "person_identifiers": [row.get("person_key") for row in chunk],
                        "source_identifiers": compact_counter([row.get("top_source_keys") or "" for row in chunk]),
                        "review_lane": lane,
                        "policy": {
                            "non_mutating": True,
                            "member_fingerprint_required": True,
                            "accepted_facts_flow_through": [
                                "evidence_reconciliation_decisions",
                                "person_evidence_reviewer_decisions",
                                "enrichment_acceptance_audit",
                                "accepted_enrichment_claims",
                            ],
                        },
                    }
                ),
                "generated_at": "",
            }
            batch_row["generated_at"] = stable_generated_at(
                existing_batches, "review_batch_key", BATCH_FIELDS, batch_row, generated_at
            )
            batch_rows.append(batch_row)

            for member_order, source_row in enumerate(chunk, start=1):
                fingerprint = member_fingerprint(source_row)
                member_row = {
                    "review_batch_member_key": review_batch_member_key(batch_key, source_row.get("corroboration_key") or ""),
                    "review_batch_key": batch_key,
                    "corroboration_key": source_row.get("corroboration_key") or "",
                    "execution_order": 0,
                    "member_order": member_order,
                    "member_fingerprint": fingerprint,
                    "person_key": source_row.get("person_key") or "",
                    "display_name": source_row.get("display_name") or "",
                    "role": source_row.get("role") or "",
                    "programs": source_row.get("programs") or "",
                    "current_training_states": source_row.get("current_training_states") or "",
                    "research_identity_status": source_row.get("research_identity_status") or "",
                    "recommended_review_route": source_row.get("recommended_review_route") or "",
                    "review_priority": as_int(source_row.get("review_priority")),
                    "best_confidence": round(as_float(source_row.get("best_confidence")), 3),
                    "top_source_keys": source_row.get("top_source_keys") or "",
                    "top_claim_types": source_row.get("top_claim_types") or "",
                    "required_next_evidence": source_row.get("required_next_evidence") or "",
                    "recommended_reviewer_action": recommended_reviewer_action(source_row, lane),
                    "acceptance_boundary": source_row.get("acceptance_boundary") or acceptance_rule(),
                    "evidence_json": member_evidence(source_row, lane, fingerprint),
                    "generated_at": "",
                    **{field: as_int(source_row.get(field)) for field in METRIC_FIELDS},
                }
                member_row["generated_at"] = stable_generated_at(
                    existing_members,
                    "review_batch_member_key",
                    MEMBER_FIELDS,
                    member_row,
                    generated_at,
                )
                member_rows.append(member_row)

    batch_rows.sort(
        key=lambda item: (
            -as_int(item["ready_to_review"]),
            -as_int(item["max_review_priority"]),
            -as_int(item["review_ready_record_count"]),
            item["review_lane"],
            item["role"],
            item["review_batch_key"],
        )
    )
    order_by_key = {}
    for index, row in enumerate(batch_rows, start=1):
        row["execution_order"] = index
        order_by_key[row["review_batch_key"]] = index

    member_rows.sort(
        key=lambda item: (
            order_by_key.get(item["review_batch_key"], 0),
            as_int(item["member_order"]),
            item["display_name"],
            item["person_key"],
        )
    )
    for row in member_rows:
        row["execution_order"] = order_by_key.get(row["review_batch_key"], 0)

    return batch_rows, member_rows


def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, batch_rows: list[dict], member_rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM research_identity_review_batch_members")
    conn.execute("DELETE FROM research_identity_review_batches")
    if batch_rows:
        batch_fields = ", ".join(BATCH_FIELDS)
        batch_placeholders = ", ".join(f":{field}" for field in BATCH_FIELDS)
        conn.executemany(
            f"INSERT OR REPLACE INTO research_identity_review_batches ({batch_fields}) VALUES ({batch_placeholders})",
            batch_rows,
        )
    if member_rows:
        member_fields = ", ".join(MEMBER_FIELDS)
        member_placeholders = ", ".join(f":{field}" for field in MEMBER_FIELDS)
        conn.executemany(
            f"INSERT OR REPLACE INTO research_identity_review_batch_members ({member_fields}) VALUES ({member_placeholders})",
            member_rows,
        )


def write_summary(batch_rows: list[dict], member_rows: list[dict], generated_at: str) -> None:
    by_status = Counter(row["research_identity_status"] for row in batch_rows)
    by_lane = Counter(row["review_lane"] for row in batch_rows)
    by_batch_status = Counter(row["batch_status"] for row in batch_rows)
    member_status = Counter(row["research_identity_status"] for row in member_rows)
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(batch_rows),
        "member_rows": len(member_rows),
        "ready_batch_rows": sum(as_int(row["ready_to_review"]) for row in batch_rows),
        "person_count_policy": "Summed batch person counts are not deduplicated across lanes.",
        "review_ready_record_count": sum(as_int(row["review_ready_record_count"]) for row in batch_rows),
        "research_candidate_count": sum(as_int(row["research_candidate_count"]) for row in batch_rows),
        "conflict_member_rows": sum(1 for row in member_rows if as_int(row["conflicting_identifier_count"]) > 0),
        "candidate_only_member_rows": sum(
            1 for row in member_rows if row["research_identity_status"] == "research_identity_candidate_only"
        ),
        "by_research_identity_status": dict(sorted(by_status.items())),
        "by_member_research_identity_status": dict(sorted(member_status.items())),
        "by_review_lane": dict(sorted(by_lane.items())),
        "by_batch_status": dict(sorted(by_batch_status.items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "review_batch_key": row["review_batch_key"],
                "research_identity_status": row["research_identity_status"],
                "review_lane": row["review_lane"],
                "role": row["role"],
                "person_count": row["person_count"],
                "research_candidate_count": row["research_candidate_count"],
                "review_ready_record_count": row["review_ready_record_count"],
                "conflict_count": row["conflict_count"],
                "max_review_priority": row["max_review_priority"],
                "target_decision_artifact": row["target_decision_artifact"],
            }
            for row in batch_rows[:25]
        ],
        "policy": "Research identity batches prioritize and fingerprint review sessions only; they do not accept person, publication, contact, or trend facts.",
        "csv": str(BATCH_CSV_PATH.relative_to(ROOT)),
        "json": str(BATCH_JSON_PATH.relative_to(ROOT)),
        "member_csv": str(MEMBER_CSV_PATH.relative_to(ROOT)),
        "member_json": str(MEMBER_JSON_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    batch_rows, member_rows = build_rows(load_corroboration(conn), generated_at)
    with conn:
        write_db(conn, batch_rows, member_rows)
    conn.close()

    write_csv(BATCH_CSV_PATH, BATCH_FIELDS, batch_rows)
    write_csv(MEMBER_CSV_PATH, MEMBER_FIELDS, member_rows)
    BATCH_JSON_PATH.write_text(json.dumps(batch_rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    MEMBER_JSON_PATH.write_text(
        json.dumps(member_rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_summary(batch_rows, member_rows, generated_at)
    print(dumps({"research_identity_review_batches": len(batch_rows), "members": len(member_rows)}))


if __name__ == "__main__":
    main()
