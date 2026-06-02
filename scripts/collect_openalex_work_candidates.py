#!/usr/bin/env python3
"""Collect OpenAlex work-level candidates from high-confidence author candidates."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

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
CLAIMS_PATH = OUT / "openalex_work_candidate_claims.json"
SUMMARY_PATH = OUT / "openalex_work_candidate_summary.json"

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


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def openalex_author_id(value: str) -> str:
    match = re.search(r"(A\d+)", value or "")
    return match.group(1) if match else ""


def institution_name(institution: dict) -> str:
    return str(institution.get("display_name") or "").strip()


def is_penn_name(name: str) -> bool:
    normalized = name.lower()
    return any(term in normalized for term in PENN_TERMS) or "upenn" in normalized


def request_with_retry(
    session: requests.Session,
    url: str,
    *,
    timeout: float,
    attempts: int,
    backoff: float,
) -> requests.Response:
    retryable_statuses = {429, 500, 502, 503, 504}
    for attempt in range(attempts):
        response = session.get(url, timeout=timeout)
        if response.status_code not in retryable_statuses:
            return response
        if attempt < attempts - 1:
            retry_after = response.headers.get("Retry-After")
            if retry_after and retry_after.isdigit():
                time.sleep(float(retry_after))
            else:
                time.sleep(backoff * (2**attempt))
    return response


def upsert_source(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO sources
        (source_key, source_url, source_type, title, metadata_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "openalex_work_search",
            "https://api.openalex.org/works",
            "scholarly_api",
            "OpenAlex work search",
            "{}",
        ),
    )


def selected_author_candidates(conn: sqlite3.Connection, limit: int | None) -> list[dict]:
    sql = """
        SELECT e.person_key, p.display_name, p.role, e.claim_value, e.source_url,
               e.confidence, e.status, e.match_features_json, e.evidence_json
        FROM evidence_claims e
        JOIN people p ON p.person_key = e.person_key
        WHERE e.source_key = 'openalex_author_search'
          AND e.claim_type = 'research_author_candidate'
          AND e.status = 'needs_review'
        ORDER BY e.confidence DESC, p.display_name, e.claim_value
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = []
    for row in conn.execute(sql):
        item = dict(row)
        item["author_id"] = openalex_author_id(item["claim_value"])
        item["match_features"] = json.loads(item.get("match_features_json") or "[]")
        item["author_evidence"] = json.loads(item.get("evidence_json") or "{}")
        if item["author_id"]:
            rows.append(item)
    return rows


def target_authorship(work: dict, author_id: str) -> dict:
    for index, authorship in enumerate(work.get("authorships") or [], start=1):
        author = authorship.get("author") or {}
        if openalex_author_id(author.get("id", "")) == author_id:
            return {"position_index": index, **authorship}
    return {}


def work_institutions(authorship: dict) -> list[str]:
    names = []
    seen = set()
    for institution in authorship.get("institutions") or []:
        name = institution_name(institution)
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    for raw in authorship.get("raw_affiliation_strings") or []:
        raw_name = str(raw).strip()
        if raw_name and raw_name not in seen:
            seen.add(raw_name)
            names.append(raw_name)
    return names


def host_venue(work: dict) -> dict:
    primary = work.get("primary_location") or {}
    source = primary.get("source") or {}
    return {
        "display_name": source.get("display_name") or "",
        "issn_l": source.get("issn_l") or "",
        "type": source.get("type") or "",
    }


def build_claim(author: dict, work: dict, as_of_year: int) -> dict:
    authorship = target_authorship(work, author["author_id"])
    institutions = work_institutions(authorship)
    features = [
        "openalex_author_candidate_needs_review",
        "author_id_match",
    ]
    if "name_match" in author["match_features"]:
        features.append("name_match_from_author_candidate")
    if "orcid_present" in author["match_features"]:
        features.append("orcid_present_from_author_candidate")
    if "penn_affiliation" in author["match_features"]:
        features.append("penn_affiliation_from_author_candidate")
    if any(is_penn_name(name) for name in institutions):
        features.append("work_penn_affiliation")
    publication_year = int(work.get("publication_year") or 0)
    if publication_year and publication_year >= as_of_year - 10:
        features.append("ten_year_publication_window")
    if work.get("doi"):
        features.append("doi_present")
    if work.get("ids", {}).get("pmid"):
        features.append("pmid_present")
    if authorship.get("author_position"):
        features.append(f"author_position_{authorship['author_position']}")

    confidence = min(float(author["confidence"] or 0.0), 0.9) * 0.72
    confidence += 0.1 if "work_penn_affiliation" in features else 0
    confidence += 0.06 if "doi_present" in features else 0
    confidence += 0.05 if "pmid_present" in features else 0
    confidence += 0.05 if "ten_year_publication_window" in features else 0
    confidence = round(min(confidence, 0.92), 3)

    return {
        "person_key": author["person_key"],
        "display_name": author["display_name"],
        "role": author["role"],
        "claim_type": "openalex_work_candidate",
        "claim_value": work.get("id") or "",
        "source_key": "openalex_work_search",
        "source_url": work.get("id") or "",
        "source_type": "scholarly_api",
        "confidence": confidence,
        "status": "needs_review" if confidence >= 0.75 else "candidate",
        "match_features": features,
        "reconciliation_notes": (
            "OpenAlex work candidate derived from a high-confidence author candidate; "
            "accept only after same-person author-position/affiliation/profile review."
        ),
        "evidence": {
            "utility_key": "openalex_work_search",
            "collector": "scripts/collect_openalex_work_candidates.py",
            "author_candidate": {
                "openalex_author_id": author["author_id"],
                "claim_value": author["claim_value"],
                "confidence": author["confidence"],
                "match_features": author["match_features"],
                "orcid": author["author_evidence"].get("orcid", ""),
                "affiliations": author["author_evidence"].get("affiliations", []),
                "source_url": author.get("source_url") or "",
            },
            "work": {
                "openalex_id": work.get("id") or "",
                "doi": work.get("doi") or "",
                "pmid": (work.get("ids") or {}).get("pmid") or "",
                "title": work.get("title") or "",
                "publication_year": publication_year or "",
                "publication_date": work.get("publication_date") or "",
                "type": work.get("type") or "",
                "cited_by_count": work.get("cited_by_count") or 0,
                "host_venue": host_venue(work),
                "authorship": {
                    "author_position": authorship.get("author_position") or "",
                    "position_index": authorship.get("position_index") or "",
                    "institutions": institutions,
                    "raw_affiliation_strings": authorship.get("raw_affiliation_strings") or [],
                },
            },
        },
    }


def collect_works(
    session: requests.Session,
    author: dict,
    *,
    per_author: int,
    timeout: float,
    attempts: int,
    backoff: float,
    mailto: str,
    as_of_year: int,
) -> list[dict]:
    mailto_param = f"&mailto={quote(mailto)}" if mailto else ""
    url = (
        "https://api.openalex.org/works"
        f"?filter=author.id:{quote(author['author_id'])}"
        f"&sort=publication_date:desc&per-page={int(per_author)}"
        f"{mailto_param}"
    )
    response = request_with_retry(session, url, timeout=timeout, attempts=attempts, backoff=backoff)
    response.raise_for_status()
    claims = []
    for work in response.json().get("results", []):
        claim = build_claim(author, work, as_of_year)
        claim["evidence"]["query_url"] = url
        claims.append(claim)
    return claims


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


def current_work_claims(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT e.person_key, p.display_name, p.role, e.claim_type, e.claim_value,
               e.source_key, e.source_url, e.source_type, e.confidence, e.status,
               e.match_features_json, e.reconciliation_notes, e.evidence_json
        FROM evidence_claims e
        JOIN people p ON p.person_key = e.person_key
        WHERE e.source_key = 'openalex_work_search'
          AND e.claim_type IN ('openalex_work_candidate', 'openalex_work_candidate_error')
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


def record_quality(conn: sqlite3.Connection, claims: list[dict], author_count: int, generated_at: str) -> None:
    conn.execute(
        """
        INSERT INTO source_quality_observations
        (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
         rejected_claims, ambiguous_claims, notes, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "openalex_work_search",
            generated_at,
            author_count,
            sum(1 for claim in claims if claim["status"] == "candidate"),
            sum(1 for claim in claims if claim["status"] == "accepted"),
            sum(1 for claim in claims if claim["status"] == "rejected"),
            sum(1 for claim in claims if claim["status"] == "needs_review"),
            "OpenAlex work candidates derived from high-confidence OpenAlex author candidates; no claims accepted automatically.",
            dumps(
                {
                    "claims": len(claims),
                    "mean_confidence": round(
                        sum(float(claim["confidence"]) for claim in claims) / len(claims), 4
                    )
                    if claims
                    else 0,
                    "people_with_claims": len({claim["person_key"] for claim in claims}),
                }
            ),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--per-author", type=int, default=5)
    parser.add_argument("--sleep", type=float, default=0.1)
    parser.add_argument("--request-timeout", type=float, default=8.0)
    parser.add_argument("--request-attempts", type=int, default=4)
    parser.add_argument("--retry-backoff", type=float, default=8.0)
    parser.add_argument("--progress-every", type=int, default=10)
    parser.add_argument("--replace-source", action="store_true")
    parser.add_argument("--as-of-year", type=int, default=datetime.now(timezone.utc).year)
    parser.add_argument("--mailto", default="", help="Optional email for OpenAlex polite-pool requests.")
    parser.add_argument(
        "--max-errors",
        type=int,
        default=5,
        help="Abort after this many collector errors to avoid durable all-error artifacts.",
    )
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    authors = selected_author_candidates(conn, args.limit)
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-openalex-work-enrichment/0.1 (candidate evidence only)"

    generated_claims: list[dict] = []
    error_count = 0
    with conn:
        upsert_source(conn)
        if args.replace_source:
            conn.execute("DELETE FROM evidence_claims WHERE source_key = 'openalex_work_search'")
            conn.execute("DELETE FROM source_quality_observations WHERE utility_key = 'openalex_work_search'")
        for index, author in enumerate(authors, start=1):
            try:
                claims = collect_works(
                    session,
                    author,
                    per_author=args.per_author,
                    timeout=args.request_timeout,
                    attempts=args.request_attempts,
                    backoff=args.retry_backoff,
                    mailto=args.mailto,
                    as_of_year=args.as_of_year,
                )
            except Exception as exc:  # noqa: BLE001
                error_count += 1
                if error_count > args.max_errors:
                    raise SystemExit(
                        f"aborting after {error_count} OpenAlex work collector errors; "
                        "rerun later or increase --max-errors"
                    ) from exc
                claims = [
                    {
                        "person_key": author["person_key"],
                        "display_name": author["display_name"],
                        "role": author["role"],
                        "claim_type": "openalex_work_candidate_error",
                        "claim_value": f"OpenAlex works error: {type(exc).__name__}",
                        "source_key": "openalex_work_search",
                        "source_url": "https://api.openalex.org/works",
                        "source_type": "scholarly_api",
                        "confidence": 0.0,
                        "status": "rejected",
                        "match_features": ["collector_error"],
                        "reconciliation_notes": str(exc)[:500],
                        "evidence": {
                            "utility_key": "openalex_work_search",
                            "collector": "scripts/collect_openalex_work_candidates.py",
                            "openalex_author_id": author["author_id"],
                        },
                    }
                ]
            for claim in claims:
                insert_claim(conn, claim)
                generated_claims.append(claim)
            if args.progress_every and index % args.progress_every == 0:
                print(f"processed_authors={index} claims={len(generated_claims)}", flush=True)
            time.sleep(args.sleep)
        record_quality(conn, generated_claims, len(authors), generated_at)

    durable_claims = current_work_claims(conn)
    conn.close()
    by_status = Counter(claim["status"] for claim in durable_claims)
    by_role = Counter(claim["role"] for claim in durable_claims)
    by_feature = Counter(feature for claim in durable_claims for feature in claim["match_features"])
    summary = {
        "generated_at": generated_at,
        "source_key": "openalex_work_search",
        "authors_considered": len(authors),
        "claims_generated": len(generated_claims),
        "durable_claim_rows": len(durable_claims),
        "people_with_durable_claims": len({claim["person_key"] for claim in durable_claims}),
        "by_status": dict(sorted(by_status.items())),
        "by_role": dict(sorted(by_role.items())),
        "top_match_features": dict(by_feature.most_common(20)),
        "per_author": args.per_author,
        "as_of_year": args.as_of_year,
        "policy": "Work-level evidence remains candidate/needs-review evidence; it can corroborate research enrichment but does not by itself accept identity or publication authorship.",
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
