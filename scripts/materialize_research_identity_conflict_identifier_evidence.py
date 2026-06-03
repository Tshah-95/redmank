#!/usr/bin/env python3
"""Explode research identity conflict packets into per-identifier evidence rows."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_OUT = ARTIFACTS / "research_identity_conflict_identifier_evidence.csv"
JSON_OUT = ARTIFACTS / "research_identity_conflict_identifier_evidence.json"
SUMMARY_OUT = ARTIFACTS / "research_identity_conflict_identifier_evidence_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "conflict_identifier_key",
    "conflict_packet_key",
    "reviewer_decision_key",
    "review_batch_key",
    "person_key",
    "display_name",
    "role",
    "programs",
    "conflict_resolution_lane",
    "packet_status",
    "identifier_key",
    "identifier_type",
    "identifier_value",
    "identifier_rank",
    "packet_identifier_count",
    "support_claim_count",
    "needs_review_claim_count",
    "candidate_claim_count",
    "max_confidence",
    "source_family_count",
    "source_domain_count",
    "supporting_pmid_count",
    "supporting_doi_count",
    "identifier_review_posture",
    "recommended_identifier_action",
    "required_next_evidence",
    "source_families_json",
    "source_domains_json",
    "match_features_json",
    "supporting_pmids",
    "supporting_dois",
    "supporting_claims_json",
    "competing_identifier_context_json",
    "acceptance_boundary",
    "member_fingerprint",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def existing_rows() -> dict[str, dict]:
    return {
        row["conflict_identifier_key"]: row
        for row in read_csv(CSV_OUT)
        if row.get("conflict_identifier_key")
    }


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["conflict_identifier_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def conflict_identifier_key(packet_key: str, identifier_key: str) -> str:
    return "research_identity_conflict_identifier_" + sha256_text(f"{packet_key}|{identifier_key}")[:20]


def identifier_review_posture(identifier: dict, rank: int, packet_identifier_count: int) -> str:
    if identifier.get("identifier_type") == "missing_secondary_anchor":
        return "missing_secondary_anchor_evidence"
    max_confidence = as_float(identifier.get("max_confidence"))
    support_count = as_int(identifier.get("support_claim_count"))
    needs_review = as_int(identifier.get("needs_review_claim_count"))
    if packet_identifier_count <= 1:
        return "single_identifier_context_check"
    if rank == 1 and max_confidence >= 0.85 and support_count >= 1 and needs_review >= 1:
        return "leading_identifier_candidate_needs_collision_review"
    if max_confidence >= 0.85 and support_count >= 1:
        return "high_confidence_competing_identifier"
    if support_count > 0:
        return "low_or_partial_support_competing_identifier"
    return "identifier_without_claim_support"


def recommended_identifier_action(posture: str, identifier_type: str) -> str:
    if posture == "missing_secondary_anchor_evidence":
        return "collect_secondary_identity_anchor_before_research_identity_acceptance"
    if posture == "leading_identifier_candidate_needs_collision_review":
        return f"review_and_choose_or_quarantine_leading_{identifier_type}_identifier"
    if posture == "high_confidence_competing_identifier":
        return f"compare_{identifier_type}_source_context_against_leading_identifier"
    if posture == "low_or_partial_support_competing_identifier":
        return f"collect_or_reject_additional_{identifier_type}_support"
    if posture == "identifier_without_claim_support":
        return f"quarantine_or_remove_unsupported_{identifier_type}_identifier"
    return f"confirm_single_{identifier_type}_identifier_context"


def required_next_evidence(packet: dict, identifier: dict, posture: str) -> str:
    identifier_type = identifier.get("identifier_type") or "identifier"
    if posture == "missing_secondary_anchor_evidence":
        return packet.get("required_next_evidence") or "Collect an independent ORCID, NPI, official profile, or equivalent non-name identity anchor."
    if posture == "leading_identifier_candidate_needs_collision_review":
        return (
            f"Confirm this {identifier_type} against official profile, publication author position, and non-name anchors; "
            "quarantine competing identifiers before accepting research identity."
        )
    if posture == "high_confidence_competing_identifier":
        return (
            f"Compare this high-confidence {identifier_type} with the leading identifier using source URLs, PMIDs/DOIs, "
            "ORCID/OpenAlex works, and trainee program context."
        )
    if posture == "low_or_partial_support_competing_identifier":
        return f"Collect stronger public evidence for this {identifier_type} or reject it as insufficiently anchored."
    if posture == "identifier_without_claim_support":
        return f"No supporting claims are present for this {identifier_type}; quarantine unless a reviewer adds source evidence."
    return packet.get("required_next_evidence") or "Confirm identifier context before acceptance."


def context_payload(packet: dict, identifiers: list[dict]) -> dict:
    return {
        "packet_identifier_count": len(identifiers),
        "identifier_type_counts": dict(sorted(Counter(item.get("identifier_type") or "" for item in identifiers).items())),
        "risk_flags": parse_json(packet.get("risk_flags_json"), []),
        "support_summary": parse_json(packet.get("support_summary_json"), {}),
    }


def build_rows() -> list[dict]:
    generated_at = now_utc()
    existing = existing_rows()
    rows = []
    for packet in read_csv(ARTIFACTS / "research_identity_conflict_resolution_packets.csv"):
        identifiers = parse_json(packet.get("competing_identifiers_json"), [])
        if not isinstance(identifiers, list):
            continue
        identifiers = [
            item
            for item in identifiers
            if isinstance(item, dict) and item.get("identifier_key")
        ]
        if not identifiers:
            identifiers = [
                {
                    "identifier_key": f"missing_secondary_anchor:{packet.get('person_key') or packet.get('conflict_packet_key')}",
                    "identifier_type": "missing_secondary_anchor",
                    "identifier_value": "",
                    "support_claim_count": 0,
                    "needs_review_claim_count": 0,
                    "candidate_claim_count": 0,
                    "max_confidence": 0.0,
                    "source_families": {},
                    "source_domains": {},
                    "match_features": {},
                    "supporting_pmids": [],
                    "supporting_dois": [],
                    "supporting_claims": [],
                }
            ]
        identifiers.sort(
            key=lambda item: (
                -as_float(item.get("max_confidence")),
                -as_int(item.get("support_claim_count")),
                item.get("identifier_type") or "",
                item.get("identifier_key") or "",
            )
        )
        context = context_payload(packet, identifiers)
        for index, identifier in enumerate(identifiers, start=1):
            source_families = identifier.get("source_families") if isinstance(identifier.get("source_families"), dict) else {}
            source_domains = identifier.get("source_domains") if isinstance(identifier.get("source_domains"), dict) else {}
            match_features = identifier.get("match_features") if isinstance(identifier.get("match_features"), dict) else {}
            supporting_pmids = identifier.get("supporting_pmids") if isinstance(identifier.get("supporting_pmids"), list) else []
            supporting_dois = identifier.get("supporting_dois") if isinstance(identifier.get("supporting_dois"), list) else []
            supporting_claims = identifier.get("supporting_claims") if isinstance(identifier.get("supporting_claims"), list) else []
            posture = identifier_review_posture(identifier, index, len(identifiers))
            row = {
                "conflict_identifier_key": conflict_identifier_key(packet["conflict_packet_key"], identifier["identifier_key"]),
                "conflict_packet_key": packet.get("conflict_packet_key") or "",
                "reviewer_decision_key": packet.get("reviewer_decision_key") or "",
                "review_batch_key": packet.get("review_batch_key") or "",
                "person_key": packet.get("person_key") or "",
                "display_name": packet.get("display_name") or "",
                "role": packet.get("role") or "",
                "programs": packet.get("programs") or "",
                "conflict_resolution_lane": packet.get("conflict_resolution_lane") or "",
                "packet_status": packet.get("packet_status") or "",
                "identifier_key": identifier.get("identifier_key") or "",
                "identifier_type": identifier.get("identifier_type") or "",
                "identifier_value": identifier.get("identifier_value") or "",
                "identifier_rank": index,
                "packet_identifier_count": len(identifiers),
                "support_claim_count": as_int(identifier.get("support_claim_count")),
                "needs_review_claim_count": as_int(identifier.get("needs_review_claim_count")),
                "candidate_claim_count": as_int(identifier.get("candidate_claim_count")),
                "max_confidence": round(as_float(identifier.get("max_confidence")), 3),
                "source_family_count": len(source_families),
                "source_domain_count": len(source_domains),
                "supporting_pmid_count": len(supporting_pmids),
                "supporting_doi_count": len(supporting_dois),
                "identifier_review_posture": posture,
                "recommended_identifier_action": recommended_identifier_action(posture, identifier.get("identifier_type") or "identifier"),
                "required_next_evidence": required_next_evidence(packet, identifier, posture),
                "source_families_json": dumps(source_families),
                "source_domains_json": dumps(source_domains),
                "match_features_json": dumps(match_features),
                "supporting_pmids": "; ".join(str(item) for item in supporting_pmids),
                "supporting_dois": "; ".join(str(item) for item in supporting_dois),
                "supporting_claims_json": dumps(supporting_claims[:12]),
                "competing_identifier_context_json": dumps(context),
                "acceptance_boundary": packet.get("acceptance_boundary") or "",
                "member_fingerprint": packet.get("member_fingerprint") or "",
                "evidence_json": dumps(
                    {
                        "derived_from": "research_identity_conflict_resolution_packets",
                        "conflict_packet_key": packet.get("conflict_packet_key"),
                        "identifier_key": identifier.get("identifier_key"),
                        "reviewer_decision_key": packet.get("reviewer_decision_key"),
                        "policy": {
                            "non_mutating": True,
                            "identifier_row_is_not_acceptance": True,
                            "accepted_review_requires_matching_member_fingerprint": True,
                        },
                    }
                ),
                "generated_at": "",
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            rows.append({field: row[field] for field in FIELDS})
    rows.sort(
        key=lambda item: (
            item["display_name"],
            as_int(item["identifier_rank"]),
            item["identifier_key"],
        )
    )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(rows: list[dict]) -> None:
    conn = sqlite3.connect(DB)
    with conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("DELETE FROM research_identity_conflict_identifier_evidence")
        if rows:
            fields = ", ".join(FIELDS)
            placeholders = ", ".join(f":{field}" for field in FIELDS)
            conn.executemany(
                f"INSERT OR REPLACE INTO research_identity_conflict_identifier_evidence ({fields}) VALUES ({placeholders})",
                rows,
            )
    conn.close()


def write_summary(rows: list[dict]) -> None:
    payload = {
        "generated_at": max((row["generated_at"] for row in rows), default=now_utc()),
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "identifier_rows": len(rows),
        "conflict_packet_count": len({row["conflict_packet_key"] for row in rows}),
        "person_count": len({row["person_key"] for row in rows}),
        "leading_identifier_rows": sum(1 for row in rows if as_int(row["identifier_rank"]) == 1),
        "high_confidence_identifier_rows": sum(1 for row in rows if as_float(row["max_confidence"]) >= 0.85),
        "publication_supported_identifier_rows": sum(1 for row in rows if as_int(row["supporting_pmid_count"]) + as_int(row["supporting_doi_count"]) > 0),
        "by_identifier_type": dict(sorted(Counter(row["identifier_type"] for row in rows).items())),
        "by_identifier_review_posture": dict(sorted(Counter(row["identifier_review_posture"] for row in rows).items())),
        "by_conflict_resolution_lane": dict(sorted(Counter(row["conflict_resolution_lane"] for row in rows).items())),
        "top_identifier_rows": [
            {
                "display_name": row["display_name"],
                "identifier_type": row["identifier_type"],
                "identifier_value": row["identifier_value"],
                "identifier_rank": row["identifier_rank"],
                "support_claim_count": row["support_claim_count"],
                "max_confidence": row["max_confidence"],
                "identifier_review_posture": row["identifier_review_posture"],
                "recommended_identifier_action": row["recommended_identifier_action"],
            }
            for row in sorted(
                rows,
                key=lambda item: (
                    -as_float(item["max_confidence"]),
                    -as_int(item["support_claim_count"]),
                    item["display_name"],
                    as_int(item["identifier_rank"]),
                ),
            )[:25]
        ],
        "policy": "Conflict identifier evidence rows are non-mutating exploded support records. They help reviewers compare competing ORCID/OpenAlex/NPI identifiers, but only current-fingerprint reviewer decisions can accept or quarantine research identity.",
    }
    SUMMARY_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows)
    print(dumps({"research_identity_conflict_identifier_evidence": len(rows)}))


if __name__ == "__main__":
    main()
