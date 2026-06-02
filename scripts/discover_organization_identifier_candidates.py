#!/usr/bin/env python3
"""Discover source-backed external identifier candidates for organizations."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"
CSV_PATH = ARTIFACTS / "organization_identifier_candidates.csv"
JSON_PATH = ARTIFACTS / "organization_identifier_candidates.json"
SUMMARY_PATH = ARTIFACTS / "organization_identifier_candidate_summary.json"
ROR_API = "https://api.ror.org/organizations"

FIELDNAMES = [
    "candidate_key",
    "organization_key",
    "canonical_name",
    "category",
    "mention_count",
    "source_name",
    "query",
    "identifier_type",
    "identifier_value",
    "candidate_name",
    "candidate_types",
    "candidate_country",
    "candidate_links",
    "match_status",
    "confidence",
    "match_reasons",
    "evidence_json",
    "audited_at",
]

STOPWORDS = {
    "at",
    "and",
    "of",
    "the",
    "for",
    "in",
    "a",
    "an",
}

GENERIC_ORG_TOKENS = {
    "center",
    "centre",
    "clinic",
    "college",
    "health",
    "healthcare",
    "hospital",
    "institute",
    "medical",
    "medicine",
    "press",
    "school",
    "system",
    "university",
}


def norm_space(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def normalized_label(value: str | None) -> str:
    value = norm_space(value).lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return norm_space(value)


def tokens(value: str | None) -> set[str]:
    return {token for token in normalized_label(value).split() if token and token not in STOPWORDS}


def identity_tokens(value: str | None) -> set[str]:
    return {token for token in tokens(value) if token not in GENERIC_ORG_TOKENS}


def display_name(item: dict) -> str:
    for name in item.get("names") or []:
        if "ror_display" in name.get("types", []):
            return name.get("value", "")
    for name in item.get("names") or []:
        if "label" in name.get("types", []):
            return name.get("value", "")
    return (item.get("names") or [{}])[0].get("value", "")


def candidate_name_aliases(item: dict) -> list[str]:
    aliases = []
    for name in item.get("names") or []:
        value = norm_space(name.get("value"))
        if value and value not in aliases:
            aliases.append(value)
    return aliases


def candidate_context_aliases(item: dict) -> list[str]:
    aliases = []
    for relation in item.get("relationships") or []:
        value = norm_space(relation.get("label"))
        if value and value not in aliases:
            aliases.append(value)
    return aliases


def candidate_aliases(item: dict) -> list[str]:
    aliases = candidate_name_aliases(item)
    for value in candidate_context_aliases(item):
        if value not in aliases:
            aliases.append(value)
    return aliases


def candidate_country(item: dict) -> str:
    locations = item.get("locations") or []
    if not locations:
        return ""
    details = locations[0].get("geonames_details") or {}
    return norm_space(details.get("country_name") or details.get("country_code"))


def candidate_links(item: dict) -> str:
    return "; ".join(
        link.get("value", "")
        for link in item.get("links") or []
        if link.get("value")
    )


def exact_or_alias_match(query: str, aliases: list[str]) -> bool:
    query_norm = normalized_label(query)
    return any(normalized_label(alias) == query_norm for alias in aliases)


def parent_like_match(query: str, candidate: str) -> bool:
    query_norm = normalized_label(query)
    candidate_norm = normalized_label(candidate)
    if not candidate_norm:
        return False
    if candidate_norm in query_norm:
        return True
    return False


def name_score(query: str, item: dict) -> tuple[float, list[str], str]:
    aliases = candidate_name_aliases(item) or [display_name(item)]
    context_aliases = candidate_context_aliases(item)
    best_alias = max(aliases or [display_name(item)], key=lambda alias: SequenceMatcher(None, normalized_label(query), normalized_label(alias)).ratio())
    best_ratio = SequenceMatcher(None, normalized_label(query), normalized_label(best_alias)).ratio()
    query_tokens = tokens(query)
    alias_tokens = tokens(best_alias)
    query_identity_tokens = identity_tokens(query)
    alias_identity_tokens = identity_tokens(best_alias)
    overlap = len(query_tokens & alias_tokens)
    query_coverage = overlap / max(len(query_tokens), 1)
    candidate_coverage = overlap / max(len(alias_tokens), 1)
    jaccard = overlap / max(len(query_tokens | alias_tokens), 1)
    identity_overlap = len(query_identity_tokens & alias_identity_tokens)
    identity_jaccard = identity_overlap / max(len(query_identity_tokens | alias_identity_tokens), 1)
    score = max(best_ratio, jaccard, min(query_coverage, candidate_coverage))
    reasons = [
        f"best_alias={best_alias}",
        f"name_ratio={best_ratio:.3f}",
        f"query_token_coverage={query_coverage:.3f}",
        f"candidate_token_coverage={candidate_coverage:.3f}",
        f"token_jaccard={jaccard:.3f}",
        f"identity_token_overlap={identity_overlap}",
        f"identity_token_jaccard={identity_jaccard:.3f}",
    ]
    if exact_or_alias_match(query, aliases):
        score = max(score, 0.98)
        reasons.append("exact_alias_match")
    elif parent_like_match(query, display_name(item)):
        score = max(score, 0.72)
        reasons.append("parent_or_short_label_match")
    else:
        best_context = ""
        if context_aliases:
            best_context = max(
                context_aliases,
                key=lambda alias: SequenceMatcher(None, normalized_label(query), normalized_label(alias)).ratio(),
            )
        if best_context:
            context_ratio = SequenceMatcher(None, normalized_label(query), normalized_label(best_context)).ratio()
            context_tokens = tokens(best_context)
            context_overlap = len(query_tokens & context_tokens)
            context_jaccard = context_overlap / max(len(query_tokens | context_tokens), 1)
            reasons.append(f"best_context_alias={best_context}")
            reasons.append(f"context_name_ratio={context_ratio:.3f}")
            reasons.append(f"context_token_jaccard={context_jaccard:.3f}")
            if context_ratio >= 0.9 or context_jaccard >= 0.75:
                score = max(score, 0.74)
                reasons.append("relationship_context_match_not_identifier_match")
    return round(score, 3), reasons, best_alias


def expected_identifier_type(category: str, query: str, item: dict, score: float) -> tuple[str, str]:
    candidate = display_name(item)
    candidate_low = normalized_label(candidate)
    query_low = normalized_label(query)
    medical_school_like = category == "medical_school"
    school_terms = {"school", "college", "medicine", "medical"}
    if medical_school_like and not any(term in candidate_low.split() for term in school_terms):
        if parent_like_match(query, candidate):
            return "parent_ror", "candidate_names_parent_institution_not_school"
        return "ror", "candidate_name_not_school_specific_review"
    if medical_school_like and score < 0.9 and any(term in query_low.split() for term in school_terms):
        return "ror", "medical_school_candidate_needs_name_review"
    return "ror", "candidate_label_matches_requested_surface"


def classify_match(category: str, query: str, item: dict, score: float, identifier_type: str, reason: str) -> tuple[str, float, list[str]]:
    reasons = [reason]
    candidate_types = set(item.get("types") or [])
    exact_name = exact_or_alias_match(query, candidate_name_aliases(item))
    query_tokens = tokens(query)
    candidate_tokens = tokens(display_name(item))
    query_identity_tokens = identity_tokens(query)
    candidate_identity_tokens = identity_tokens(display_name(item))
    overlap = len(query_tokens & candidate_tokens)
    jaccard = overlap / max(len(query_tokens | candidate_tokens), 1)
    query_coverage = overlap / max(len(query_tokens), 1)
    candidate_coverage = overlap / max(len(candidate_tokens), 1)
    identity_overlap = len(query_identity_tokens & candidate_identity_tokens)
    identity_query_coverage = identity_overlap / max(len(query_identity_tokens), 1)
    identity_candidate_coverage = identity_overlap / max(len(candidate_identity_tokens), 1)
    identity_jaccard = identity_overlap / max(len(query_identity_tokens | candidate_identity_tokens), 1)
    if "education" in candidate_types:
        reasons.append("ror_type_education")
    if "healthcare" in candidate_types:
        reasons.append("ror_type_healthcare")
    if candidate_country(item) == "United States":
        reasons.append("country_us")
    if identifier_type == "parent_ror":
        if not parent_like_match(query, display_name(item)):
            confidence = min(score, 0.62)
            reasons.append("parent_candidate_without_display_name_containment")
            return "weak_identifier_candidate", round(confidence, 3), reasons
        confidence = min(max(score, 0.68), 0.86)
        return "parent_identifier_candidate", round(confidence, 3), reasons
    if exact_name:
        return "strong_identifier_candidate", round(min(max(score, 0.96), 0.98), 3), reasons
    if score >= 0.93 and jaccard >= 0.72 and query_coverage >= 0.8 and candidate_coverage >= 0.72:
        return "strong_identifier_candidate", round(min(score, 0.96), 3), reasons
    has_identity_anchor = bool(
        identity_overlap
        and (
            identity_jaccard >= 0.5
            or (identity_query_coverage >= 0.8 and identity_candidate_coverage >= 0.6)
        )
    )
    if len(query_identity_tokens) <= 1 and identity_candidate_coverage < 0.9:
        has_identity_anchor = False
    if score >= 0.82 and has_identity_anchor and (jaccard >= 0.45 or min(query_coverage, candidate_coverage) >= 0.65):
        return "review_identifier_candidate", round(min(score, 0.88), 3), reasons
    if score >= 0.65 and identity_overlap and (jaccard >= 0.25 or min(query_coverage, candidate_coverage) >= 0.4):
        return "weak_identifier_candidate", round(min(score, 0.7), 3), reasons
    return "low_signal_identifier_candidate", round(min(score, 0.55), 3), reasons


def candidate_key(org_key: str, identifier_type: str, identifier_value: str) -> str:
    digest = hashlib.sha1(f"{org_key}:{identifier_type}:{identifier_value}".encode("utf-8")).hexdigest()[:16]
    return f"org_identifier_candidate_{digest}"


def existing_rows() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return {row["candidate_key"]: row for row in csv.DictReader(f)}


def stable_audited_at(existing: dict[str, dict], row: dict, new_value: str) -> str:
    prior = existing.get(row["candidate_key"])
    if not prior:
        return new_value
    stable_fields = [field for field in FIELDNAMES if field != "audited_at"]
    for field in stable_fields:
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return new_value
    return prior.get("audited_at") or new_value


def load_organizations(conn: sqlite3.Connection, limit: int, min_mentions: int, categories: set[str]) -> list[dict]:
    placeholders = ",".join("?" for _ in categories)
    params: list = list(categories) + [min_mentions, limit]
    return [
        dict(row)
        for row in conn.execute(
            f"""
            SELECT o.organization_key, o.canonical_name, o.category, o.resolver_status,
                   COUNT(e.person_key) AS mention_count
            FROM organizations o
            LEFT JOIN person_training_events e ON e.organization_id = o.organization_id
            WHERE o.category IN ({placeholders})
              AND o.resolver_status = 'cleaned_label'
            GROUP BY o.organization_key, o.canonical_name, o.category, o.resolver_status
            HAVING mention_count >= ?
            ORDER BY mention_count DESC, o.category, o.canonical_name
            LIMIT ?
            """,
            params,
        )
    ]


def fetch_ror(query: str, rows: int) -> dict:
    url = ROR_API + "?" + urllib.parse.urlencode({"query": query, "page": 1})
    request = urllib.request.Request(url, headers={"User-Agent": "redmank-organization-identifier-discovery/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    payload["request_url"] = url
    payload["items"] = (payload.get("items") or [])[:rows]
    return payload


def row_from_candidate(org: dict, item: dict, query: str, source_payload: dict) -> dict:
    score, name_reasons, best_alias = name_score(query, item)
    identifier_type, identifier_reason = expected_identifier_type(org["category"], query, item, score)
    status, confidence, status_reasons = classify_match(org["category"], query, item, score, identifier_type, identifier_reason)
    evidence = {
        "ror_request_url": source_payload.get("request_url"),
        "ror_number_of_results": source_payload.get("number_of_results"),
        "ror_time_taken": source_payload.get("time_taken"),
        "candidate_aliases": candidate_aliases(item)[:20],
        "candidate_relationships": item.get("relationships") or [],
        "candidate_external_ids": item.get("external_ids") or [],
        "best_alias": best_alias,
        "source_payload_version": "ror_api_v2",
    }
    row = {
        "candidate_key": candidate_key(org["organization_key"], identifier_type, item["id"]),
        "organization_key": org["organization_key"],
        "canonical_name": org["canonical_name"],
        "category": org["category"],
        "mention_count": int(org["mention_count"] or 0),
        "source_name": "ROR",
        "query": query,
        "identifier_type": identifier_type,
        "identifier_value": item["id"],
        "candidate_name": display_name(item),
        "candidate_types": "; ".join(item.get("types") or []),
        "candidate_country": candidate_country(item),
        "candidate_links": candidate_links(item),
        "match_status": status,
        "confidence": confidence,
        "match_reasons": "; ".join(name_reasons + status_reasons),
        "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
        "audited_at": "",
    }
    return row


def discover(conn: sqlite3.Connection, args: argparse.Namespace) -> tuple[list[dict], list[dict]]:
    categories = set(args.categories.split(","))
    orgs = load_organizations(conn, args.limit, args.min_mentions, categories)
    rows: dict[str, dict] = {}
    observations = []
    for org in orgs:
        query = org["canonical_name"]
        observed_at = datetime.now(timezone.utc).isoformat()
        try:
            payload = fetch_ror(query, args.candidates_per_org)
            observations.append(
                {
                    "organization_key": org["organization_key"],
                    "canonical_name": org["canonical_name"],
                    "category": org["category"],
                    "query": query,
                    "source_name": "ROR",
                    "status": "ok",
                    "observed_at": observed_at,
                    "result_count": len(payload.get("items") or []),
                    "source_number_of_results": payload.get("number_of_results", 0),
                    "error": "",
                    "request_url": payload.get("request_url", ""),
                }
            )
            for item in payload.get("items") or []:
                row = row_from_candidate(org, item, query, payload)
                current = rows.get(row["candidate_key"])
                if not current or float(row["confidence"]) > float(current["confidence"]):
                    rows[row["candidate_key"]] = row
        except Exception as exc:  # urllib can raise several concrete HTTP/socket exceptions.
            observations.append(
                {
                    "organization_key": org["organization_key"],
                    "canonical_name": org["canonical_name"],
                    "category": org["category"],
                    "query": query,
                    "source_name": "ROR",
                    "status": "error",
                    "observed_at": observed_at,
                    "result_count": 0,
                    "source_number_of_results": 0,
                    "error": f"{type(exc).__name__}: {str(exc)[:240]}",
                    "request_url": ROR_API + "?" + urllib.parse.urlencode({"query": query, "page": 1}),
                }
            )
        time.sleep(args.sleep)
    existing = existing_rows()
    audited_at = datetime.now(timezone.utc).isoformat()
    output = sorted(
        rows.values(),
        key=lambda row: (
            -int(row["mention_count"]),
            row["canonical_name"],
            -float(row["confidence"]),
            row["identifier_value"],
        ),
    )
    for row in output:
        row["audited_at"] = stable_audited_at(existing, row, audited_at)
    return output, observations


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM organization_identifier_candidates")
    for row in rows:
        conn.execute(
            """
            INSERT INTO organization_identifier_candidates
            (candidate_key, organization_key, canonical_name, category, mention_count,
             source_name, query, identifier_type, identifier_value, candidate_name,
             candidate_types, candidate_country, candidate_links, match_status,
             confidence, match_reasons, evidence_json, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row[field] for field in FIELDNAMES),
        )


def write_outputs(conn: sqlite3.Connection, rows: list[dict], observations: list[dict]) -> None:
    write_csv(CSV_PATH, rows, FIELDNAMES)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    observation_path = ARTIFACTS / "organization_identifier_source_observations.csv"
    observation_fields = [
        "organization_key",
        "canonical_name",
        "category",
        "query",
        "source_name",
        "status",
        "observed_at",
        "result_count",
        "source_number_of_results",
        "error",
        "request_url",
    ]
    write_csv(observation_path, observations, observation_fields)
    with conn:
        write_sqlite(conn, rows)
    summary = {
        "generated_at": max((row["audited_at"] for row in rows), default=datetime.now(timezone.utc).isoformat()),
        "candidate_rows": len(rows),
        "organizations_queried": len(observations),
        "organizations_with_candidates": len({row["organization_key"] for row in rows}),
        "source_observation_rows": len(observations),
        "by_match_status": dict(sorted(Counter(row["match_status"] for row in rows).items())),
        "by_identifier_type": dict(sorted(Counter(row["identifier_type"] for row in rows).items())),
        "by_category": dict(sorted(Counter(row["category"] for row in rows).items())),
        "by_observation_status": dict(sorted(Counter(row["status"] for row in observations).items())),
        "strong_or_parent_candidate_rows": sum(
            1 for row in rows if row["match_status"] in {"strong_identifier_candidate", "parent_identifier_candidate"}
        ),
        "review_candidate_rows": sum(1 for row in rows if row["match_status"] == "review_identifier_candidate"),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "observation_csv": str(observation_path.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--limit", type=int, default=80)
    parser.add_argument("--min-mentions", type=int, default=4)
    parser.add_argument("--candidates-per-org", type=int, default=3)
    parser.add_argument(
        "--categories",
        default="medical_school,undergraduate_institution,clinical_training_site,graduate_institution",
    )
    parser.add_argument("--sleep", type=float, default=0.1)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows, observations = discover(conn, args)
    write_outputs(conn, rows, observations)
    conn.close()


if __name__ == "__main__":
    main()
