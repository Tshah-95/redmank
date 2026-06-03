#!/usr/bin/env python3
"""Materialize conflict-resolution packets for research identity review."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_OUT = ARTIFACTS / "research_identity_conflict_resolution_packets.csv"
JSON_OUT = ARTIFACTS / "research_identity_conflict_resolution_packets.json"
SUMMARY_OUT = ARTIFACTS / "research_identity_conflict_resolution_packet_summary.json"

csv.field_size_limit(sys.maxsize)

ORCID_RE = re.compile(r"\b\d{4}-\d{4}-\d{4}-[\dX]{4}\b", re.I)
OPENALEX_AUTHOR_RE = re.compile(r"openalex\.org/(A\d+)", re.I)
PMID_RE = re.compile(r"(?:pmid:|pubmed\.ncbi\.nlm\.nih\.gov/)?(\d{6,9})", re.I)

FIELDS = [
    "conflict_packet_key",
    "reviewer_decision_key",
    "review_batch_member_key",
    "review_batch_key",
    "corroboration_key",
    "person_key",
    "display_name",
    "role",
    "programs",
    "current_training_states",
    "queue_status",
    "decision_status",
    "review_priority",
    "identity_risk_level",
    "conflicting_identifier_count",
    "competing_identifier_count",
    "high_confidence_identifier_count",
    "publication_support_count",
    "secondary_anchor_count",
    "conflict_resolution_lane",
    "packet_status",
    "required_next_evidence",
    "recommended_reviewer_action",
    "acceptance_boundary",
    "member_fingerprint",
    "competing_identifiers_json",
    "support_summary_json",
    "risk_flags_json",
    "manual_decision_template_json",
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


def domain_for(url: str | None) -> str:
    if not url:
        return ""
    host = urlparse(url).netloc.lower()
    return host[4:] if host.startswith("www.") else host


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def existing_rows() -> dict[str, dict]:
    return {row["conflict_packet_key"]: row for row in read_csv(CSV_OUT) if row.get("conflict_packet_key")}


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["conflict_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def identifier_values(claim: dict) -> list[dict]:
    claim_type = (claim.get("claim_type") or "").lower()
    claim_value = str(claim.get("claim_value") or "")
    source_url = str(claim.get("source_url") or "")
    text = " ".join([claim_value, source_url])
    values: list[dict] = []

    for match in ORCID_RE.findall(text):
        values.append({"identifier_type": "orcid", "identifier_value": match.upper()})
    for match in OPENALEX_AUTHOR_RE.findall(text):
        values.append({"identifier_type": "openalex_author", "identifier_value": match.upper()})
    if "npi" in claim_type and claim_value:
        values.append({"identifier_type": "npi", "identifier_value": claim_value})
    if "doi:" in claim_value.lower():
        values.append({"identifier_type": "doi", "identifier_value": claim_value.lower().replace("doi:", "", 1)})
    elif "doi.org/" in source_url.lower():
        values.append({"identifier_type": "doi", "identifier_value": source_url.split("doi.org/", 1)[-1].lower()})
    if "article_candidate" in claim_type or "pubmed" in source_url.lower() or claim_value.lower().startswith("pmid:"):
        match = PMID_RE.search(text)
        if match:
            values.append({"identifier_type": "pmid", "identifier_value": match.group(1)})
    output = []
    seen = set()
    for item in values:
        key = (item["identifier_type"], item["identifier_value"])
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def identity_identifier_key(item: dict) -> str:
    return f"{item['identifier_type']}:{item['identifier_value']}"


def claim_support_record(claim: dict) -> dict:
    return {
        "claim_type": claim.get("claim_type") or "",
        "claim_value": claim.get("claim_value") or "",
        "status": claim.get("status") or "",
        "confidence": as_float(claim.get("confidence")),
        "source_identifier": claim.get("source_identifier") or "",
        "source_family": claim.get("source_family") or "",
        "source_domain": claim.get("source_domain") or domain_for(claim.get("source_url")),
        "source_url": claim.get("source_url") or "",
        "match_features": claim.get("match_features") or [],
    }


def dedupe_claims(claims: list[dict]) -> list[dict]:
    output = []
    seen = set()
    for claim in claims:
        if not isinstance(claim, dict):
            continue
        key = (
            claim.get("claim_type") or "",
            claim.get("claim_value") or "",
            claim.get("source_identifier") or "",
            claim.get("source_url") or "",
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(claim)
    return output


def packet_key(dossier: dict) -> str:
    return "research_identity_conflict_resolution_packet_" + sha256_text(dossier["reviewer_decision_key"])[:20]


def build_identifier_groups(claims: list[dict]) -> tuple[list[dict], dict]:
    grouped: dict[str, dict] = {}
    publication_identifiers: set[str] = set()
    secondary_anchor_identifiers: set[str] = set()

    for claim in claims:
        identifiers = identifier_values(claim)
        support = claim_support_record(claim)
        claim_publications = [
            identity_identifier_key(item)
            for item in identifiers
            if item["identifier_type"] in {"pmid", "doi"}
        ]
        for pub in claim_publications:
            publication_identifiers.add(pub)

        for item in identifiers:
            key = identity_identifier_key(item)
            if item["identifier_type"] in {"npi", "orcid"}:
                secondary_anchor_identifiers.add(key)
            if item["identifier_type"] not in {"orcid", "openalex_author", "npi"}:
                continue
            group = grouped.setdefault(
                key,
                {
                    "identifier_type": item["identifier_type"],
                    "identifier_value": item["identifier_value"],
                    "support_claim_count": 0,
                    "needs_review_claim_count": 0,
                    "candidate_claim_count": 0,
                    "max_confidence": 0.0,
                    "source_families": Counter(),
                    "source_domains": Counter(),
                    "match_features": Counter(),
                    "supporting_pmids": set(),
                    "supporting_dois": set(),
                    "supporting_claims": [],
                },
            )
            group["support_claim_count"] += 1
            status = support["status"]
            if status == "needs_review":
                group["needs_review_claim_count"] += 1
            if status == "candidate":
                group["candidate_claim_count"] += 1
            group["max_confidence"] = max(group["max_confidence"], support["confidence"])
            if support["source_family"]:
                group["source_families"][support["source_family"]] += 1
            if support["source_domain"]:
                group["source_domains"][support["source_domain"]] += 1
            for feature in support["match_features"]:
                group["match_features"][feature] += 1
            for pub_key in claim_publications:
                if pub_key.startswith("pmid:"):
                    group["supporting_pmids"].add(pub_key.split(":", 1)[1])
                if pub_key.startswith("doi:"):
                    group["supporting_dois"].add(pub_key.split(":", 1)[1])
            group["supporting_claims"].append(support)

    rows = []
    for key, group in grouped.items():
        rows.append(
            {
                "identifier_key": key,
                "identifier_type": group["identifier_type"],
                "identifier_value": group["identifier_value"],
                "support_claim_count": group["support_claim_count"],
                "needs_review_claim_count": group["needs_review_claim_count"],
                "candidate_claim_count": group["candidate_claim_count"],
                "max_confidence": round(group["max_confidence"], 3),
                "source_families": dict(sorted(group["source_families"].items())),
                "source_domains": dict(group["source_domains"].most_common(8)),
                "match_features": dict(group["match_features"].most_common(12)),
                "supporting_pmids": sorted(group["supporting_pmids"])[:12],
                "supporting_dois": sorted(group["supporting_dois"])[:12],
                "supporting_claims": sorted(
                    group["supporting_claims"],
                    key=lambda item: (-as_float(item.get("confidence")), item.get("claim_type") or ""),
                )[:8],
            }
        )
    rows.sort(key=lambda item: (-as_float(item["max_confidence"]), -as_int(item["support_claim_count"]), item["identifier_key"]))
    summary = {
        "identity_identifier_count": len(rows),
        "publication_identifier_count": len(publication_identifiers),
        "secondary_anchor_identifier_count": len(secondary_anchor_identifiers),
        "identifier_type_counts": dict(sorted(Counter(row["identifier_type"] for row in rows).items())),
    }
    return rows, summary


def risk_flags(identifier_groups: list[dict], support_summary: dict, dossier: dict) -> list[str]:
    flags = []
    type_counts = Counter(row["identifier_type"] for row in identifier_groups)
    if type_counts.get("orcid", 0) > 1:
        flags.append("multiple_orcid_identifiers")
    if type_counts.get("openalex_author", 0) > 1:
        flags.append("multiple_openalex_author_identifiers")
    if type_counts.get("npi", 0) > 1:
        flags.append("multiple_npi_identifiers")
    if as_int(dossier.get("conflicting_identifier_count")) > 0:
        flags.append("corroboration_flagged_identifier_conflict")
    if not any(row["identifier_type"] in {"orcid", "npi"} for row in identifier_groups):
        flags.append("missing_secondary_identity_identifier")
    if as_int(support_summary.get("publication_identifier_count")) == 0:
        flags.append("missing_publication_identifier_support")
    if as_int(dossier.get("non_name_anchor_count")) == 0:
        flags.append("name_only_or_no_non_name_anchor")
    return flags


def resolution_lane(identifier_groups: list[dict], flags: list[str]) -> str:
    if "multiple_orcid_identifiers" in flags:
        return "orcid_collision_review"
    if "multiple_openalex_author_identifiers" in flags:
        return "openalex_author_collision_review"
    if "multiple_npi_identifiers" in flags:
        return "secondary_anchor_collision_review"
    if "missing_secondary_identity_identifier" in flags:
        return "collect_secondary_anchor_before_research_acceptance"
    if "missing_publication_identifier_support" in flags:
        return "collect_publication_identifier_support"
    if len(identifier_groups) > 1:
        return "mixed_identifier_consistency_review"
    return "single_identifier_conflict_context_review"


def required_evidence(lane: str) -> str:
    return {
        "orcid_collision_review": "Resolve which ORCID, if any, belongs to the trainee using official profile, ORCID works, PMID/DOI author position, and institutional anchors.",
        "openalex_author_collision_review": "Resolve which OpenAlex author, if any, is same-person; quarantine extra author IDs before accepting research identity.",
        "secondary_anchor_collision_review": "Resolve competing NPI/secondary anchors before using them to support research identity.",
        "collect_secondary_anchor_before_research_acceptance": "Collect an independent ORCID, NPI, official profile, or equivalent non-name identity anchor.",
        "collect_publication_identifier_support": "Collect PMID/DOI author-position evidence before accepting a publication or author identity.",
        "mixed_identifier_consistency_review": "Confirm that identity identifiers, publication identifiers, and institutional anchors all describe the same person.",
        "single_identifier_conflict_context_review": "Confirm source context and explicitly resolve the conflict flag before acceptance.",
    }[lane]


def recommended_action(lane: str) -> str:
    return {
        "orcid_collision_review": "choose_or_quarantine_conflicting_orcid_before_research_identity_acceptance",
        "openalex_author_collision_review": "choose_or_quarantine_conflicting_openalex_author_before_acceptance",
        "secondary_anchor_collision_review": "resolve_secondary_anchor_collision_before_using_anchor",
        "collect_secondary_anchor_before_research_acceptance": "collect_secondary_identity_anchor_or_reject_insufficient_anchors",
        "collect_publication_identifier_support": "collect_pmid_or_doi_author_position_support",
        "mixed_identifier_consistency_review": "confirm_identifier_consistency_or_reject_collision",
        "single_identifier_conflict_context_review": "record_explicit_conflict_resolution_with_current_fingerprint",
    }[lane]


def packet_status(dossier: dict) -> str:
    if dossier.get("decision_status") != "pending_reviewer_decision":
        return "decision_already_recorded_or_stale"
    if as_int(dossier.get("conflicting_identifier_count")) > 0:
        return "ready_for_identifier_conflict_review"
    return "not_conflict_packet"


def build_rows() -> list[dict]:
    existing = existing_rows()
    generated_at = now_utc()
    rows = []
    for dossier in read_csv(ARTIFACTS / "research_identity_reviewer_decision_dossiers.csv"):
        if as_int(dossier.get("conflicting_identifier_count")) <= 0:
            continue
        claims = parse_json(dossier.get("top_claims_json"), [])
        if not isinstance(claims, list):
            claims = []
        claims = dedupe_claims(claims)
        identifiers, support_summary = build_identifier_groups(claims)
        flags = risk_flags(identifiers, support_summary, dossier)
        lane = resolution_lane(identifiers, flags)
        template = parse_json(dossier.get("manual_decision_template_json"), {})
        row = {
            "conflict_packet_key": packet_key(dossier),
            "reviewer_decision_key": dossier.get("reviewer_decision_key") or "",
            "review_batch_member_key": dossier.get("review_batch_member_key") or "",
            "review_batch_key": dossier.get("review_batch_key") or "",
            "corroboration_key": dossier.get("corroboration_key") or "",
            "person_key": dossier.get("person_key") or "",
            "display_name": dossier.get("display_name") or "",
            "role": dossier.get("role") or "",
            "programs": dossier.get("programs") or "",
            "current_training_states": dossier.get("current_training_states") or "",
            "queue_status": dossier.get("queue_status") or "",
            "decision_status": dossier.get("decision_status") or "",
            "review_priority": as_int(dossier.get("review_priority")),
            "identity_risk_level": dossier.get("identity_risk_level") or "",
            "conflicting_identifier_count": as_int(dossier.get("conflicting_identifier_count")),
            "competing_identifier_count": len(identifiers),
            "high_confidence_identifier_count": sum(1 for item in identifiers if as_float(item.get("max_confidence")) >= 0.85),
            "publication_support_count": as_int(support_summary.get("publication_identifier_count")),
            "secondary_anchor_count": as_int(dossier.get("secondary_anchor_count")),
            "conflict_resolution_lane": lane,
            "packet_status": packet_status(dossier),
            "required_next_evidence": required_evidence(lane),
            "recommended_reviewer_action": recommended_action(lane),
            "acceptance_boundary": dossier.get("acceptance_boundary") or "",
            "member_fingerprint": dossier.get("member_fingerprint") or "",
            "competing_identifiers_json": dumps(identifiers),
            "support_summary_json": dumps(support_summary),
            "risk_flags_json": dumps(flags),
            "manual_decision_template_json": dumps(template),
            "evidence_json": dumps(
                {
                    "derived_from": "research_identity_reviewer_decision_dossiers",
                    "dossier_key": dossier.get("dossier_key"),
                    "reviewer_decision_key": dossier.get("reviewer_decision_key"),
                    "top_claim_count": len(claims),
                    "policy": {
                        "non_mutating": True,
                        "conflict_packet_is_not_acceptance": True,
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
            -as_int(item["review_priority"]),
            -as_int(item["competing_identifier_count"]),
            item["conflict_resolution_lane"],
            item["display_name"],
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
        conn.execute("DELETE FROM research_identity_conflict_resolution_packets")
        if rows:
            fields = ", ".join(FIELDS)
            placeholders = ", ".join(f":{field}" for field in FIELDS)
            conn.executemany(
                f"INSERT OR REPLACE INTO research_identity_conflict_resolution_packets ({fields}) VALUES ({placeholders})",
                rows,
            )
    conn.close()


def write_summary(rows: list[dict]) -> None:
    generated_at = max((row["generated_at"] for row in rows), default=now_utc())
    payload = {
        "generated_at": generated_at,
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "packet_rows": len(rows),
        "person_count": len({row["person_key"] for row in rows}),
        "ready_packet_rows": sum(1 for row in rows if row["packet_status"] == "ready_for_identifier_conflict_review"),
        "competing_identifier_count": sum(as_int(row["competing_identifier_count"]) for row in rows),
        "publication_support_count": sum(as_int(row["publication_support_count"]) for row in rows),
        "by_conflict_resolution_lane": dict(sorted(Counter(row["conflict_resolution_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "top_packets": [
            {
                "display_name": row["display_name"],
                "role": row["role"],
                "conflict_resolution_lane": row["conflict_resolution_lane"],
                "competing_identifier_count": row["competing_identifier_count"],
                "publication_support_count": row["publication_support_count"],
                "recommended_reviewer_action": row["recommended_reviewer_action"],
            }
            for row in rows[:20]
        ],
        "policy": "Research identity conflict-resolution packets are non-mutating. They expose competing identifiers and support evidence; reviewer decisions still require current member fingerprints and downstream acceptance ledgers.",
    }
    SUMMARY_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows)
    print(dumps({"research_identity_conflict_resolution_packets": len(rows)}))


if __name__ == "__main__":
    main()
