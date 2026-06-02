#!/usr/bin/env python3
"""Materialize non-mutating triage lanes for person evidence review packets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "person_evidence_review_triage.csv"
JSON_PATH = ARTIFACTS / "person_evidence_review_triage.json"
SUMMARY_PATH = ARTIFACTS / "person_evidence_review_triage_summary.json"

FIELDS = [
    "triage_key",
    "reviewer_decision_key",
    "packet_key",
    "person_or_name_key",
    "person_key",
    "display_name",
    "role",
    "review_kind",
    "packet_status",
    "triage_lane",
    "triage_priority",
    "decision_difficulty",
    "risk_level",
    "evidence_density_score",
    "review_ready_record_count",
    "evidence_record_count",
    "source_count",
    "claim_type_count",
    "match_feature_count",
    "source_family_summary",
    "top_source_domains",
    "best_decision",
    "likely_next_action",
    "reviewer_prompt",
    "automation_boundary",
    "acceptance_blocker",
    "required_reviewer_action",
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


def domain_for(url: str) -> str:
    if not url:
        return ""
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def source_family(domain: str, url: str) -> str:
    if not domain:
        return "unknown_source"
    if domain.endswith("pubmed.ncbi.nlm.nih.gov") or domain.endswith("ncbi.nlm.nih.gov"):
        return "publication_index"
    if domain.endswith("npiregistry.cms.hhs.gov"):
        return "npi_registry"
    if domain.endswith("orcid.org"):
        return "orcid_registry"
    if domain.endswith("pennmedicine.org") or domain.endswith("upenn.edu") or domain.endswith("penn.edu"):
        return "official_penn_profile_or_roster"
    if "linkedin.com" in domain:
        return "professional_social_profile"
    if "doximity.com" in domain:
        return "clinician_profile_directory"
    if "scholar.google" in domain:
        return "scholarly_profile"
    if "/cv" in url.lower() or "curriculum-vitae" in url.lower():
        return "cv_or_biosketch"
    return "external_web_source"


def parse_queue_evidence(row: dict) -> dict:
    try:
        return json.loads(row.get("evidence_json") or "{}")
    except json.JSONDecodeError:
        return {}


def triage_key(row: dict) -> str:
    return "person_evidence_triage_" + sha256_text(row["reviewer_decision_key"])[:20]


def evidence_density(review_ready_count: int, evidence_count: int, source_count: int, feature_count: int) -> float:
    if evidence_count <= 0:
        return 0.0
    score = review_ready_count * 2.0
    score += min(source_count, 5) * 0.75
    score += min(feature_count, 12) * 0.25
    score /= max(evidence_count, 1)
    return round(score, 3)


def has_any(values: list[str], needles: set[str]) -> bool:
    lowered = {value.lower() for value in values}
    return any(needle in lowered for needle in needles)


def classify_lane(row: dict, families: Counter, claim_types: list[str], features: list[str]) -> str:
    review_kind = row.get("review_kind") or ""
    packet_status = row.get("packet_status") or ""
    best_decision = row.get("best_decision") or ""
    has_publication = families.get("publication_index", 0) > 0 or any("pubmed" in value.lower() for value in claim_types)
    has_npi_or_orcid = families.get("npi_registry", 0) > 0 or families.get("orcid_registry", 0) > 0
    has_official = families.get("official_penn_profile_or_roster", 0) > 0
    has_personal_profile = has_any(features, {"personal_profile_field", "official_trainee_profile"})
    if "attending" in review_kind or "attending" in packet_status:
        return "attending_trend_bridge_review"
    if has_personal_profile and not has_publication:
        return "official_profile_context_display_review"
    if has_publication and has_npi_or_orcid:
        return "publication_with_secondary_identity_anchor_review"
    if has_publication and has_official:
        return "publication_with_official_profile_anchor_review"
    if review_kind == "publication_identity_review" or has_publication:
        return "publication_identity_final_check"
    if has_npi_or_orcid:
        return "secondary_identity_anchor_context_review"
    if best_decision.startswith("review_ready"):
        return "mixed_evidence_identity_review"
    return "general_candidate_review"


def classify_risk(row: dict, families: Counter, claim_types: list[str], features: list[str]) -> str:
    evidence_count = as_int(row.get("evidence_record_count"))
    source_count = sum(families.values())
    has_personal_profile = has_any(features, {"personal_profile_field"})
    has_publication = families.get("publication_index", 0) > 0 or any("pubmed" in value.lower() for value in claim_types)
    has_secondary = families.get("npi_registry", 0) > 0 or families.get("orcid_registry", 0) > 0
    if has_personal_profile:
        return "display_safety_sensitive"
    if has_publication and not has_secondary and source_count <= 1:
        return "identity_collision_high"
    if evidence_count >= 6 or source_count >= 4:
        return "mixed_evidence_review_risk"
    if has_secondary:
        return "identity_anchor_verification_risk"
    return "standard_review_risk"


def classify_difficulty(review_ready_count: int, evidence_count: int, source_count: int, risk: str) -> str:
    if risk in {"display_safety_sensitive", "identity_collision_high"}:
        return "careful_manual_review"
    if review_ready_count <= 2 and evidence_count <= 3 and source_count <= 2:
        return "quick_manual_review"
    if evidence_count <= 6 and source_count <= 3:
        return "moderate_manual_review"
    return "complex_packet_review"


def likely_action(lane: str, risk: str) -> str:
    if lane == "publication_with_secondary_identity_anchor_review":
        return "confirm_author_identity_and_secondary_anchor_then_decide_publication"
    if lane == "publication_with_official_profile_anchor_review":
        return "confirm_profile_context_and_author_identity_then_decide_publication"
    if lane == "publication_identity_final_check":
        return "confirm_non_name_author_anchors_or_request_secondary_identity_anchor"
    if lane == "official_profile_context_display_review":
        return "apply_display_policy_before_accepting_profile_context"
    if lane == "attending_trend_bridge_review":
        return "confirm_historical_training_bridge_before_trend_acceptance"
    if lane == "secondary_identity_anchor_context_review":
        return "confirm_identifier_belongs_to_current_trainee_before_using_as_anchor"
    if risk == "identity_collision_high":
        return "seek_independent_identity_anchor_before_acceptance"
    return "record_accept_reject_or_needs_more_evidence_decision"


def reviewer_prompt(lane: str) -> str:
    return {
        "publication_with_secondary_identity_anchor_review": (
            "Does the publication author, secondary identifier, and current Penn trainee roster row describe the same person?"
        ),
        "publication_with_official_profile_anchor_review": (
            "Does the official Penn profile or roster context independently support the publication author identity?"
        ),
        "publication_identity_final_check": (
            "Are there enough non-name author anchors to accept this publication, or should a secondary anchor be required?"
        ),
        "official_profile_context_display_review": (
            "Which official-profile fields are useful context, and are any personal fields safe for the intended display?"
        ),
        "attending_trend_bridge_review": (
            "Does the source bridge a Penn training role to a recent attending endpoint inside the trend window?"
        ),
        "secondary_identity_anchor_context_review": (
            "Does this NPI/ORCID-style identifier belong to the same current Penn trainee and support later claims?"
        ),
    }.get(lane, "What candidate facts, if any, are acceptable after identity, source-context, anchor, and display review?")


def automation_boundary(lane: str) -> str:
    return (
        "Triage is non-mutating. It may sort packets and recommend reviewer prompts, but accepted facts still require "
        "person_evidence_reviewer_decisions.csv with matching packet_fingerprint and all confirmation fields set."
    )


def read_queue(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM person_evidence_reviewer_decision_queue
            WHERE queue_status = 'ready_for_reviewer_decision'
            ORDER BY review_priority DESC, display_name, packet_key
            """
        )
    ]


def build_rows(queue: list[dict], generated_at: str) -> list[dict]:
    rows = []
    for row in queue:
        urls = split_semicolon(row.get("top_source_urls"))
        if row.get("best_source_url") and row["best_source_url"] not in urls:
            urls.insert(0, row["best_source_url"])
        domains = [domain_for(url) for url in urls]
        domain_values = [domain for domain in domains if domain]
        families = Counter(source_family(domain, url) for domain, url in zip(domains, urls))
        claim_types = split_semicolon(row.get("top_claim_types"))
        features = split_semicolon(row.get("top_match_features"))
        review_ready_count = as_int(row.get("review_ready_record_count"))
        evidence_count = as_int(row.get("evidence_record_count"))
        source_count = len(set(domain_values))
        feature_count = len(features)
        density = evidence_density(review_ready_count, evidence_count, source_count, feature_count)
        lane = classify_lane(row, families, claim_types, features)
        risk = classify_risk(row, families, claim_types, features)
        difficulty = classify_difficulty(review_ready_count, evidence_count, source_count, risk)
        priority = as_int(row.get("review_priority"))
        priority += min(review_ready_count, 5) * 3
        priority += min(source_count, 4) * 2
        if lane in {"publication_with_secondary_identity_anchor_review", "publication_with_official_profile_anchor_review"}:
            priority += 12
        if risk in {"identity_collision_high", "display_safety_sensitive"}:
            priority += 4
        source_family_summary = "; ".join(f"{family}:{count}" for family, count in sorted(families.items()))
        queue_evidence = parse_queue_evidence(row)
        evidence = {
            "source": "person_evidence_reviewer_decision_queue",
            "queue_evidence": queue_evidence,
            "triage_inputs": {
                "source_domains": domain_values,
                "source_family_counts": dict(sorted(families.items())),
                "claim_types": claim_types,
                "match_features": features,
                "evidence_density_score": density,
            },
            "policy": {
                "non_mutating": True,
                "acceptance_gate": "person_evidence_reviewer_decisions.csv plus matching packet fingerprint and confirmations",
            },
        }
        triage = {
            "triage_key": triage_key(row),
            "reviewer_decision_key": row["reviewer_decision_key"],
            "packet_key": row["packet_key"],
            "person_or_name_key": row["person_or_name_key"],
            "person_key": row.get("person_key") or "",
            "display_name": row["display_name"],
            "role": row.get("role") or "",
            "review_kind": row["review_kind"],
            "packet_status": row["packet_status"],
            "triage_lane": lane,
            "triage_priority": priority,
            "decision_difficulty": difficulty,
            "risk_level": risk,
            "evidence_density_score": density,
            "review_ready_record_count": review_ready_count,
            "evidence_record_count": evidence_count,
            "source_count": source_count,
            "claim_type_count": len(claim_types),
            "match_feature_count": feature_count,
            "source_family_summary": source_family_summary,
            "top_source_domains": "; ".join(domain_values[:8]),
            "best_decision": row.get("best_decision") or "",
            "likely_next_action": likely_action(lane, risk),
            "reviewer_prompt": reviewer_prompt(lane),
            "automation_boundary": automation_boundary(lane),
            "acceptance_blocker": row.get("acceptance_blocker") or "",
            "required_reviewer_action": row.get("required_reviewer_action") or "",
            "packet_fingerprint": row["packet_fingerprint"],
            "evidence_json": dumps(evidence),
            "generated_at": generated_at,
        }
        rows.append({field: triage[field] for field in FIELDS})
    return sorted(rows, key=lambda item: (-as_int(item["triage_priority"]), item["display_name"], item["packet_key"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_evidence_review_triage")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO person_evidence_review_triage ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_lane = Counter(row["triage_lane"] for row in rows)
    by_risk = Counter(row["risk_level"] for row in rows)
    by_difficulty = Counter(row["decision_difficulty"] for row in rows)
    by_role_lane = Counter(f"{row['role']}:{row['triage_lane']}" for row in rows)
    top_rows = [
        {
            "display_name": row["display_name"],
            "role": row["role"],
            "triage_lane": row["triage_lane"],
            "triage_priority": row["triage_priority"],
            "risk_level": row["risk_level"],
            "decision_difficulty": row["decision_difficulty"],
            "review_ready_record_count": row["review_ready_record_count"],
            "evidence_record_count": row["evidence_record_count"],
            "top_source_domains": row["top_source_domains"],
            "likely_next_action": row["likely_next_action"],
        }
        for row in rows[:25]
    ]
    payload = {
        "generated_at": generated_at,
        "triage_rows": len(rows),
        "person_count": len({row["person_or_name_key"] for row in rows}),
        "by_triage_lane": dict(sorted(by_lane.items())),
        "by_risk_level": dict(sorted(by_risk.items())),
        "by_decision_difficulty": dict(sorted(by_difficulty.items())),
        "by_role_and_triage_lane": dict(sorted(by_role_lane.items())),
        "top_triage_rows": top_rows,
        "policy": (
            "This artifact is non-mutating decision support. It ranks and classifies person-evidence review packets, "
            "but accepted enrichment/trend/contact facts still require the explicit reviewer-decision gate."
        ),
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
    queue = read_queue(conn)
    rows = build_rows(queue, generated_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"triage_rows": len(rows), "generated_at": generated_at}))


if __name__ == "__main__":
    main()
