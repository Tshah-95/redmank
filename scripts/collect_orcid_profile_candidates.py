#!/usr/bin/env python3
"""Collect public ORCID profile candidates from high-confidence author evidence."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DEPS_PATH = Path("/tmp/penn_corpus_deps")
if DEPS_PATH.exists():
    import sys

    sys.path.insert(0, str(DEPS_PATH))

try:
    import requests
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing scraper dependency. Install with: "
        "python3 -m pip install --target /tmp/penn_corpus_deps -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "artifacts" / "data" / "redmank.sqlite"
OUT = ROOT / "artifacts" / "data"
CLAIMS_PATH = OUT / "orcid_profile_candidate_claims.json"
SUMMARY_PATH = OUT / "orcid_profile_candidate_summary.json"

PENN_TERMS = (
    "university of pennsylvania",
    "penn medicine",
    "hospital of the university of pennsylvania",
    "children's hospital of philadelphia",
    "childrens hospital of philadelphia",
    "perelman school of medicine",
    "pennsylvania hospital",
    "presbyterian medical center",
    "chop",
)

DEGREE_TOKENS = (
    "MD",
    "DO",
    "DPM",
    "DDS",
    "DMD",
    "PhD",
    "MPH",
    "MBA",
    "MSc",
    "MS",
    "MSEd",
    "MBBS",
    "MBChB",
    "MPhil",
    "PharmD",
)


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def clean_name(name: str | None) -> str:
    name = re.sub(r"\([^)]*\)", " ", name or "")
    name = re.sub(r"\b(" + "|".join(DEGREE_TOKENS) + r")\b", " ", name, flags=re.I)
    name = re.sub(r"[^A-Za-z' -]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def name_parts(name: str | None) -> tuple[str, str]:
    parts = clean_name(name).lower().split()
    if not parts:
        return "", ""
    return parts[0], parts[-1]


def exactish_name_match(candidate: str | None, target: str | None) -> bool:
    candidate_clean = clean_name(candidate).lower()
    target_clean = clean_name(target).lower()
    if candidate_clean and candidate_clean == target_clean:
        return True
    cf, cl = name_parts(candidate)
    tf, tl = name_parts(target)
    return bool(cf and cl and tf and tl and cl == tl and cf[:1] == tf[:1])


def orcid_path(value: str | None) -> str:
    match = re.search(r"(\d{4}-\d{4}-\d{4}-[\dX]{4})", value or "", re.I)
    return match.group(1).upper() if match else ""


def is_penn_name(name: str | None) -> bool:
    normalized = (name or "").lower()
    return any(term in normalized for term in PENN_TERMS) or "upenn" in normalized


def value_of(node) -> str:
    if isinstance(node, dict):
        value = node.get("value")
        return "" if value is None else str(value)
    return "" if node is None else str(node)


def selected_orcid_candidates(conn: sqlite3.Connection, limit: int | None) -> list[dict]:
    sql = """
        SELECT e.person_key, p.display_name, p.role, e.claim_value AS openalex_author_url,
               e.confidence, e.status, e.match_features_json, e.evidence_json
        FROM evidence_claims e
        JOIN people p ON p.person_key = e.person_key
        WHERE e.source_key = 'openalex_author_search'
          AND e.claim_type = 'research_author_candidate'
          AND e.status = 'needs_review'
          AND e.evidence_json LIKE '%orcid.org%'
        ORDER BY e.confidence DESC, p.display_name, e.claim_value
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    candidates = []
    for row in conn.execute(sql):
        item = dict(row)
        item["match_features"] = json.loads(item.get("match_features_json") or "[]")
        item["author_evidence"] = json.loads(item.get("evidence_json") or "{}")
        item["orcid"] = orcid_path(item["author_evidence"].get("orcid", ""))
        if item["orcid"]:
            candidates.append(item)
    return candidates


def request_json(session: requests.Session, url: str, *, timeout: float, attempts: int, backoff: float) -> dict:
    retryable = {429, 500, 502, 503, 504}
    last = None
    for attempt in range(attempts):
        response = session.get(url, timeout=timeout)
        last = response
        if response.status_code not in retryable:
            response.raise_for_status()
            return response.json()
        if attempt < attempts - 1:
            retry_after = response.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else backoff * (2**attempt))
    assert last is not None
    last.raise_for_status()
    return last.json()


def upsert_source(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO sources
        (source_key, source_url, source_type, title, metadata_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "orcid_public_api",
            "https://pub.orcid.org/v3.0/",
            "scholarly_api",
            "ORCID public API",
            "{}",
        ),
    )


def person_name(record: dict) -> str:
    person = record.get("person") or {}
    name = person.get("name") or {}
    given = value_of(name.get("given-names"))
    family = value_of(name.get("family-name"))
    credit = value_of(name.get("credit-name"))
    return credit or " ".join(part for part in [given, family] if part).strip()


def external_identifiers(record: dict, limit: int) -> list[dict]:
    identifiers = []
    person = record.get("person") or {}
    wrapper = person.get("external-identifiers") or {}
    for item in wrapper.get("external-identifier") or []:
        identifiers.append(
            {
                "type": value_of(item.get("external-id-type")),
                "value": value_of(item.get("external-id-value")),
                "url": value_of(item.get("external-id-url")),
                "relationship": value_of(item.get("external-id-relationship")),
            }
        )
        if len(identifiers) >= limit:
            break
    return identifiers


def keywords(record: dict, limit: int) -> list[str]:
    person = record.get("person") or {}
    wrapper = person.get("keywords") or {}
    values = []
    for item in wrapper.get("keyword") or []:
        text = value_of(item.get("content"))
        if text:
            values.append(text)
        if len(values) >= limit:
            break
    return values


def researcher_urls(record: dict, limit: int) -> list[dict]:
    person = record.get("person") or {}
    wrapper = person.get("researcher-urls") or {}
    urls = []
    for item in wrapper.get("researcher-url") or []:
        urls.append(
            {
                "name": value_of(item.get("url-name")),
                "url": value_of(item.get("url")),
            }
        )
        if len(urls) >= limit:
            break
    return urls


def affiliation_summaries(activities: dict, key: str, limit: int) -> list[dict]:
    wrapper = activities.get(key) or {}
    rows = []
    for group in wrapper.get("affiliation-group") or []:
        for summary_key, summary in group.items():
            if not summary_key.endswith("summary"):
                continue
            org = summary.get("organization") or {}
            disambiguated = org.get("disambiguated-organization") or {}
            rows.append(
                {
                    "department_name": summary.get("department-name") or "",
                    "role_title": summary.get("role-title") or "",
                    "organization_name": org.get("name") or "",
                    "city": ((org.get("address") or {}).get("city") or ""),
                    "region": ((org.get("address") or {}).get("region") or ""),
                    "country": ((org.get("address") or {}).get("country") or ""),
                    "disambiguated_id": disambiguated.get("disambiguated-organization-identifier") or "",
                    "disambiguation_source": disambiguated.get("disambiguation-source") or "",
                    "start_date": date_parts(summary.get("start-date")),
                    "end_date": date_parts(summary.get("end-date")),
                    "source": source_name(summary.get("source") or {}),
                    "visibility": summary.get("visibility") or "",
                }
            )
            if len(rows) >= limit:
                return rows
    return rows


def date_parts(node) -> str:
    if not isinstance(node, dict):
        return ""
    year = value_of(node.get("year"))
    month = value_of(node.get("month"))
    day = value_of(node.get("day"))
    return "-".join(part for part in [year, month, day] if part)


def source_name(source: dict) -> str:
    if not source:
        return ""
    return value_of(source.get("source-name")) or value_of((source.get("source-orcid") or {}).get("path"))


def work_summaries(activities: dict, limit: int) -> list[dict]:
    wrapper = activities.get("works") or {}
    rows = []
    for group in wrapper.get("group") or []:
        external_ids = []
        ids_wrapper = group.get("external-ids") or {}
        for external_id in ids_wrapper.get("external-id") or []:
            external_ids.append(
                {
                    "type": value_of(external_id.get("external-id-type")),
                    "value": value_of(external_id.get("external-id-value")),
                    "relationship": value_of(external_id.get("external-id-relationship")),
                }
            )
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        first = summaries[0]
        title = first.get("title") or {}
        rows.append(
            {
                "title": value_of((title.get("title") or {})),
                "journal_title": value_of(first.get("journal-title")),
                "type": first.get("type") or "",
                "publication_date": date_parts(first.get("publication-date")),
                "external_ids": external_ids[:5],
                "source": source_name(first.get("source") or {}),
                "visibility": first.get("visibility") or "",
            }
        )
        if len(rows) >= limit:
            break
    return rows


def all_affiliation_names(affiliations: dict[str, list[dict]]) -> list[str]:
    names = []
    for rows in affiliations.values():
        for row in rows:
            name = row.get("organization_name") or ""
            if name:
                names.append(name)
    return names


def build_claim(candidate: dict, record: dict, activities: dict, *, limits: dict[str, int]) -> dict:
    orcid_uri = f"https://orcid.org/{candidate['orcid']}"
    record_name = person_name(record)
    affiliations = {
        "employments": affiliation_summaries(activities, "employments", limits["affiliations"]),
        "educations": affiliation_summaries(activities, "educations", limits["affiliations"]),
        "qualifications": affiliation_summaries(activities, "qualifications", limits["affiliations"]),
        "memberships": affiliation_summaries(activities, "memberships", limits["affiliations"]),
        "invited_positions": affiliation_summaries(activities, "invited-positions", limits["affiliations"]),
        "distinctions": affiliation_summaries(activities, "distinctions", limits["affiliations"]),
    }
    works = work_summaries(activities, limits["works"])
    ext_ids = external_identifiers(record, limits["external_ids"])
    profile_keywords = keywords(record, limits["keywords"])
    urls = researcher_urls(record, limits["urls"])

    features = [
        "orcid_from_openalex_author_candidate",
        "openalex_author_candidate_needs_review",
        "orcid_record_public",
    ]
    if exactish_name_match(record_name, candidate["display_name"]):
        features.append("orcid_name_match")
    if any(is_penn_name(name) for name in all_affiliation_names(affiliations)):
        features.append("orcid_penn_affiliation")
    if ext_ids:
        features.append("orcid_external_ids_present")
    if works:
        features.append("orcid_works_present")
    if profile_keywords:
        features.append("orcid_keywords_present")
    if urls:
        features.append("orcid_researcher_urls_present")

    confidence = 0.52
    confidence += 0.16 if "orcid_name_match" in features else 0
    confidence += 0.12 if "orcid_penn_affiliation" in features else 0
    confidence += 0.08 if "orcid_external_ids_present" in features else 0
    confidence += 0.08 if "orcid_works_present" in features else 0
    confidence += 0.06 if "penn_affiliation" in candidate["match_features"] else 0
    confidence = round(min(confidence, 0.94), 3)

    return {
        "person_key": candidate["person_key"],
        "display_name": candidate["display_name"],
        "role": candidate["role"],
        "claim_type": "orcid_profile_candidate",
        "claim_value": orcid_uri,
        "source_key": "orcid_public_api",
        "source_url": f"https://pub.orcid.org/v3.0/{candidate['orcid']}/record",
        "source_type": "scholarly_api",
        "confidence": confidence,
        "status": "needs_review" if confidence >= 0.75 else "candidate",
        "match_features": features,
        "reconciliation_notes": (
            "ORCID profile candidate derived from a high-confidence OpenAlex author candidate; "
            "accept only when ORCID is independently linked or multiple public non-name anchors agree."
        ),
        "evidence": {
            "utility_key": "orcid_public_api",
            "collector": "scripts/collect_orcid_profile_candidates.py",
            "orcid": candidate["orcid"],
            "orcid_uri": orcid_uri,
            "record_last_modified": value_of((record.get("history") or {}).get("last-modified-date")),
            "activities_last_modified": value_of(activities.get("last-modified-date")),
            "record_name": record_name,
            "openalex_author_candidate": {
                "claim_value": candidate["openalex_author_url"],
                "confidence": candidate["confidence"],
                "match_features": candidate["match_features"],
                "affiliations": candidate["author_evidence"].get("affiliations", []),
                "works_count": candidate["author_evidence"].get("works_count", ""),
                "cited_by_count": candidate["author_evidence"].get("cited_by_count", ""),
            },
            "profile": {
                "keywords": profile_keywords,
                "external_identifiers": ext_ids,
                "researcher_urls": urls,
                "affiliations": affiliations,
                "works": works,
                "public_counts": {
                    "external_identifiers": len(ext_ids),
                    "keywords": len(profile_keywords),
                    "researcher_urls": len(urls),
                    "works_sampled": len(works),
                    **{key: len(value) for key, value in affiliations.items()},
                },
            },
        },
    }


def insert_claim(conn: sqlite3.Connection, claim: dict) -> None:
    conn.execute(
        """
        INSERT INTO evidence_claims
        (person_key, claim_type, claim_value, source_key, source_url, source_type,
         confidence, status, match_features_json, reconciliation_notes, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim["person_key"],
            claim["claim_type"],
            claim["claim_value"],
            claim["source_key"],
            claim["source_url"],
            claim["source_type"],
            claim["confidence"],
            claim["status"],
            dumps(claim["match_features"]),
            claim["reconciliation_notes"],
            dumps(claim["evidence"]),
        ),
    )


def current_claims(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT e.person_key, p.display_name, p.role, e.claim_type, e.claim_value,
               e.source_key, e.source_url, e.source_type, e.confidence, e.status,
               e.match_features_json, e.reconciliation_notes, e.evidence_json
        FROM evidence_claims e
        JOIN people p ON p.person_key = e.person_key
        WHERE e.source_key = 'orcid_public_api'
          AND e.claim_type IN ('orcid_profile_candidate', 'orcid_profile_candidate_error')
        ORDER BY p.display_name, e.claim_type, e.claim_value
        """
    ).fetchall()
    claims = []
    for row in rows:
        claims.append(
            {
                "person_key": row["person_key"],
                "display_name": row["display_name"],
                "role": row["role"],
                "claim_type": row["claim_type"],
                "claim_value": row["claim_value"],
                "source_key": row["source_key"],
                "source_url": row["source_url"],
                "source_type": row["source_type"],
                "confidence": row["confidence"],
                "status": row["status"],
                "match_features": json.loads(row["match_features_json"] or "[]"),
                "reconciliation_notes": row["reconciliation_notes"],
                "evidence": json.loads(row["evidence_json"] or "{}"),
            }
        )
    return claims


def record_quality(conn: sqlite3.Connection, claims: list[dict], selected_count: int, generated_at: str) -> None:
    conn.execute(
        """
        INSERT INTO source_quality_observations
        (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
         rejected_claims, ambiguous_claims, notes, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "orcid_public_api",
            generated_at,
            selected_count,
            sum(1 for claim in claims if claim["status"] == "candidate"),
            sum(1 for claim in claims if claim["status"] == "accepted"),
            sum(1 for claim in claims if claim["status"] == "rejected"),
            sum(1 for claim in claims if claim["status"] == "needs_review"),
            "ORCID profile candidates derived from OpenAlex author candidates; no claims accepted automatically.",
            dumps(
                {
                    "claims": len(claims),
                    "mean_confidence": round(
                        sum(float(claim["confidence"]) for claim in claims) / len(claims), 4
                    )
                    if claims
                    else 0,
                    "people_with_claims": len({claim["person_key"] for claim in claims}),
                    "feature_counts": dict(
                        Counter(feature for claim in claims for feature in claim["match_features"]).most_common(20)
                    ),
                }
            ),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.1)
    parser.add_argument("--request-timeout", type=float, default=10.0)
    parser.add_argument("--request-attempts", type=int, default=3)
    parser.add_argument("--retry-backoff", type=float, default=2.0)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--replace-source", action="store_true")
    parser.add_argument("--max-works", type=int, default=20)
    parser.add_argument("--max-affiliations", type=int, default=10)
    parser.add_argument("--max-external-ids", type=int, default=10)
    parser.add_argument("--max-keywords", type=int, default=10)
    parser.add_argument("--max-urls", type=int, default=10)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    selected = selected_orcid_candidates(conn, args.limit)
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": "redmank-orcid-profile-enrichment/0.1 (candidate evidence only)",
        }
    )
    limits = {
        "works": args.max_works,
        "affiliations": args.max_affiliations,
        "external_ids": args.max_external_ids,
        "keywords": args.max_keywords,
        "urls": args.max_urls,
    }

    generated_claims: list[dict] = []
    with conn:
        upsert_source(conn)
        if args.replace_source:
            conn.execute("DELETE FROM evidence_claims WHERE source_key = 'orcid_public_api'")
            conn.execute("DELETE FROM source_quality_observations WHERE utility_key = 'orcid_public_api'")
        for index, candidate in enumerate(selected, start=1):
            try:
                record = request_json(
                    session,
                    f"https://pub.orcid.org/v3.0/{candidate['orcid']}/record",
                    timeout=args.request_timeout,
                    attempts=args.request_attempts,
                    backoff=args.retry_backoff,
                )
                activities = request_json(
                    session,
                    f"https://pub.orcid.org/v3.0/{candidate['orcid']}/activities",
                    timeout=args.request_timeout,
                    attempts=args.request_attempts,
                    backoff=args.retry_backoff,
                )
                claims = [build_claim(candidate, record, activities, limits=limits)]
            except Exception as exc:  # noqa: BLE001
                claims = [
                    {
                        "person_key": candidate["person_key"],
                        "display_name": candidate["display_name"],
                        "role": candidate["role"],
                        "claim_type": "orcid_profile_candidate_error",
                        "claim_value": f"ORCID error: {type(exc).__name__}",
                        "source_key": "orcid_public_api",
                        "source_url": f"https://pub.orcid.org/v3.0/{candidate['orcid']}/record",
                        "source_type": "scholarly_api",
                        "confidence": 0.0,
                        "status": "rejected",
                        "match_features": ["collector_error"],
                        "reconciliation_notes": str(exc)[:500],
                        "evidence": {
                            "utility_key": "orcid_public_api",
                            "collector": "scripts/collect_orcid_profile_candidates.py",
                            "orcid": candidate["orcid"],
                        },
                    }
                ]
            for claim in claims:
                insert_claim(conn, claim)
                generated_claims.append(claim)
            if args.progress_every and index % args.progress_every == 0:
                print(f"processed_orcids={index} claims={len(generated_claims)}", flush=True)
            time.sleep(args.sleep)
        record_quality(conn, generated_claims, len(selected), generated_at)

    durable_claims = current_claims(conn)
    conn.close()
    by_status = Counter(claim["status"] for claim in durable_claims)
    by_role = Counter(claim["role"] for claim in durable_claims)
    by_feature = Counter(feature for claim in durable_claims for feature in claim["match_features"])
    summary = {
        "generated_at": generated_at,
        "source_key": "orcid_public_api",
        "orcids_considered": len(selected),
        "claims_generated": len(generated_claims),
        "durable_claim_rows": len(durable_claims),
        "people_with_durable_claims": len({claim["person_key"] for claim in durable_claims}),
        "by_status": dict(sorted(by_status.items())),
        "by_role": dict(sorted(by_role.items())),
        "top_match_features": dict(by_feature.most_common(20)),
        "policy": "ORCID profile evidence remains candidate/needs-review evidence unless independently linked or reconciled with multiple public non-name anchors.",
        "json": str(CLAIMS_PATH.relative_to(ROOT)),
    }
    CLAIMS_PATH.write_text(
        json.dumps(durable_claims, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(dumps(summary))


if __name__ == "__main__":
    main()
