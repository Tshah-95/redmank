#!/usr/bin/env python3
"""Collect public scholarly enrichment candidates for Penn resident/fellow people."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
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


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def clean_name(name: str) -> str:
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"\b(MD|DO|PhD|MPH|MBA|MSc|MS|MSEd|MBBS|MBChB|MPhil|PharmD)\b", " ", name, flags=re.I)
    name = re.sub(r"[^A-Za-z' -]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def name_parts(name: str) -> tuple[str, str, str]:
    clean = clean_name(name)
    parts = clean.split()
    if not parts:
        return "", "", ""
    first = parts[0]
    last = parts[-1]
    initials = "".join(part[0] for part in parts[:-1] if part)
    return first, last, initials


def exactish_name_match(candidate: str, target: str) -> bool:
    c = clean_name(candidate).lower()
    t = clean_name(target).lower()
    if c == t:
        return True
    cf, cl, ci = name_parts(candidate)
    tf, tl, ti = name_parts(target)
    return bool(cl and tl and cl.lower() == tl.lower() and cf[:1].lower() == tf[:1].lower() and ci[:1].lower() == ti[:1].lower())


def people(conn: sqlite3.Connection, limit: int | None, skip_existing_source: str | None = None) -> list[sqlite3.Row]:
    sql = """
        SELECT person_key, display_name, role, raw_json
        FROM people
        WHERE role IN ('resident', 'fellow')
    """
    params: list[str] = []
    if skip_existing_source:
        sql += """
          AND NOT EXISTS (
            SELECT 1
            FROM evidence_claims e
            WHERE e.person_key = people.person_key
              AND e.source_key = ?
              AND e.status != 'rejected'
          )
        """
        params.append(skip_existing_source)
    sql += """
        ORDER BY role, display_name
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    return conn.execute(sql, params).fetchall()


def profile_context(raw: dict) -> dict:
    return {
        "program": (raw.get("program_memberships") or [raw.get("program", "")])[0],
        "medical_school": raw.get("medical_school", ""),
        "residency_program": raw.get("residency_program", ""),
        "profile_url": raw.get("profile_url", ""),
    }


def upsert_api_sources(conn: sqlite3.Connection) -> None:
    rows = [
        (
            "openalex_author_search",
            "https://api.openalex.org/authors",
            "scholarly_api",
            "OpenAlex author search",
        ),
        (
            "pubmed_eutilities",
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
            "scholarly_api",
            "NCBI PubMed E-utilities",
        ),
    ]
    for row in rows:
        conn.execute(
            """
            INSERT OR REPLACE INTO sources
            (source_key, source_url, source_type, title, metadata_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (*row, "{}"),
        )


def openalex_candidates(session: requests.Session, person: sqlite3.Row) -> list[dict]:
    url = f"https://api.openalex.org/authors?search={quote(clean_name(person['display_name']))}&per-page=5"
    response = request_with_retry(session, url)
    response.raise_for_status()
    payload = response.json()
    candidates = []
    raw = json.loads(person["raw_json"])
    context = profile_context(raw)
    for result in payload.get("results", []):
        affiliations = []
        for affiliation in result.get("affiliations", [])[:8]:
            institution = affiliation.get("institution") or {}
            if institution.get("display_name"):
                affiliations.append(institution["display_name"])
        affiliation_text = " ".join(affiliations).lower()
        features = []
        if exactish_name_match(result.get("display_name", ""), person["display_name"]):
            features.append("name_match")
        if "penn" in affiliation_text or "university of Pennsylvania".lower() in affiliation_text:
            features.append("penn_affiliation")
        for field in ["medical_school", "residency_program"]:
            value = (context.get(field) or "").lower()
            if value and value in affiliation_text:
                features.append(f"{field}_affiliation")
        if result.get("orcid"):
            features.append("orcid_present")
        confidence = 0.15
        confidence += 0.25 if "name_match" in features else 0
        confidence += 0.25 if "penn_affiliation" in features else 0
        confidence += 0.15 if any(feature.endswith("_affiliation") for feature in features) else 0
        confidence += 0.1 if "orcid_present" in features else 0
        candidates.append(
            {
                "claim_type": "research_author_candidate",
                "claim_value": result.get("id", ""),
                "source_key": "openalex_author_search",
                "source_url": result.get("id", url),
                "source_type": "scholarly_api",
                "confidence": min(confidence, 0.95),
                "status": "candidate" if confidence < 0.85 else "needs_review",
                "match_features": features,
                "reconciliation_notes": "OpenAlex author candidate; do not accept without two identity anchors beyond name.",
                "evidence": {
                    "utility_key": "openalex_author_search",
                    "display_name": result.get("display_name"),
                    "orcid": result.get("orcid"),
                    "works_count": result.get("works_count"),
                    "cited_by_count": result.get("cited_by_count"),
                    "affiliations": affiliations,
                    "query_url": url,
                },
            }
        )
    return candidates


def pubmed_candidate(session: requests.Session, person: sqlite3.Row) -> dict:
    first, last, initials = name_parts(person["display_name"])
    author = f"{last} {initials}" if last and initials else clean_name(person["display_name"])
    term = f"{author}[Author]"
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&retmode=json&retmax=10&term={quote(term)}"
    )
    response = request_with_retry(session, url)
    response.raise_for_status()
    payload = response.json().get("esearchresult", {})
    count = int(payload.get("count", 0))
    features = ["author_query"]
    if count == 0:
        features.append("no_results")
    elif count <= 20:
        features.append("bounded_result_count")
    else:
        features.append("high_collision_risk")
    confidence = 0.2 if count else 0.1
    if count and count <= 20:
        confidence = 0.35
    if count > 50:
        confidence = 0.15
    return {
        "claim_type": "pubmed_author_query_candidate",
        "claim_value": f"{term} count={count}",
        "source_key": "pubmed_eutilities",
        "source_url": url,
        "source_type": "scholarly_api",
        "confidence": confidence,
        "status": "candidate",
        "match_features": features,
        "reconciliation_notes": "PubMed author query is a discovery signal only; article-level affiliation/coauthor review is required.",
        "evidence": {
            "utility_key": "pubmed_eutilities",
            "author_query": term,
            "count": count,
            "pmids": payload.get("idlist", []),
        },
    }


def request_with_retry(session: requests.Session, url: str, attempts: int = 5) -> requests.Response:
    retryable_statuses = {429, 500, 502, 503, 504}
    for attempt in range(attempts):
        response = session.get(url, timeout=20)
        if response.status_code not in retryable_statuses:
            return response
        if attempt < attempts - 1:
            time.sleep(1.0 + attempt)
    return response


def insert_claim(conn: sqlite3.Connection, person_key: str, claim: dict) -> None:
    conn.execute(
        """
        INSERT INTO evidence_claims
        (person_key, claim_type, claim_value, source_key, source_url, source_type,
         confidence, status, match_features_json, reconciliation_notes, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            person_key,
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


def record_quality(conn: sqlite3.Connection, utility_key: str, claims: list[dict], sample_size: int) -> None:
    if sample_size == 0 and not claims:
        return
    conn.execute(
        """
        INSERT INTO source_quality_observations
        (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
         rejected_claims, ambiguous_claims, notes, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            utility_key,
            datetime.now(timezone.utc).isoformat(),
            sample_size,
            sum(1 for claim in claims if claim["status"] == "candidate"),
            sum(1 for claim in claims if claim["status"] == "accepted"),
            sum(1 for claim in claims if claim["status"] == "rejected"),
            sum(1 for claim in claims if claim["status"] == "needs_review"),
            "Automated first-pass candidate generation; no claims accepted automatically.",
            dumps(
                {
                    "mean_confidence": round(
                        sum(claim["confidence"] for claim in claims) / len(claims), 4
                    )
                    if claims
                    else 0,
                    "claims": len(claims),
                }
            ),
        ),
    )


def current_research_claims(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT e.person_key, p.display_name, p.role, e.claim_type, e.claim_value,
               e.source_key, e.source_url, e.source_type, e.confidence, e.status,
               e.match_features_json, e.reconciliation_notes, e.evidence_json
        FROM evidence_claims e
        JOIN people p ON p.person_key = e.person_key
        WHERE e.source_key IN ('openalex_author_search', 'pubmed_eutilities')
        ORDER BY e.source_key, p.display_name, e.claim_type, e.claim_value
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--sleep", type=float, default=0.34)
    parser.add_argument("--only", choices=["all", "openalex", "pubmed"], default="all")
    parser.add_argument("--replace-source", action="append", default=[])
    parser.add_argument(
        "--skip-existing-source",
        choices=["openalex_author_search", "pubmed_eutilities"],
        default=None,
        help="Skip people with at least one non-rejected claim from this source.",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-research-enrichment/0.1 (candidate evidence only)"
    selected = people(conn, args.limit, args.skip_existing_source)
    all_claims: list[dict] = []
    with conn:
        upsert_api_sources(conn)
        for source_key in args.replace_source:
            conn.execute("DELETE FROM evidence_claims WHERE source_key = ?", (source_key,))
            conn.execute("DELETE FROM source_quality_observations WHERE utility_key = ?", (source_key,))
        for index, person in enumerate(selected, start=1):
            person_claims = []
            if args.only in {"all", "openalex"}:
                try:
                    person_claims.extend(openalex_candidates(session, person))
                except Exception as exc:  # noqa: BLE001
                    person_claims.append(
                        {
                            "claim_type": "research_author_candidate_error",
                            "claim_value": f"OpenAlex error: {type(exc).__name__}",
                            "source_key": "openalex_author_search",
                            "source_url": "https://api.openalex.org/authors",
                            "source_type": "scholarly_api",
                            "confidence": 0.0,
                            "status": "rejected",
                            "match_features": ["collector_error"],
                            "reconciliation_notes": str(exc)[:500],
                            "evidence": {"utility_key": "openalex_author_search"},
                        }
                    )
                time.sleep(args.sleep)
            if args.only in {"all", "pubmed"}:
                try:
                    person_claims.append(pubmed_candidate(session, person))
                except Exception as exc:  # noqa: BLE001
                    person_claims.append(
                        {
                            "claim_type": "pubmed_author_query_candidate_error",
                            "claim_value": f"PubMed error: {type(exc).__name__}",
                            "source_key": "pubmed_eutilities",
                            "source_url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
                            "source_type": "scholarly_api",
                            "confidence": 0.0,
                            "status": "rejected",
                            "match_features": ["collector_error"],
                            "reconciliation_notes": str(exc)[:500],
                            "evidence": {"utility_key": "pubmed_eutilities"},
                        }
                    )
            for claim in person_claims:
                insert_claim(conn, person["person_key"], claim)
                all_claims.append(
                    {
                        "person_key": person["person_key"],
                        "display_name": person["display_name"],
                        "role": person["role"],
                        **claim,
                    }
                )
            if index % 50 == 0:
                print(f"processed={index} claims={len(all_claims)}", flush=True)
            time.sleep(args.sleep)
        if args.only in {"all", "openalex"}:
            record_quality(
                conn,
                "openalex_author_search",
                [claim for claim in all_claims if claim["source_key"] == "openalex_author_search"],
                len(selected),
            )
        if args.only in {"all", "pubmed"}:
            record_quality(
                conn,
                "pubmed_eutilities",
                [claim for claim in all_claims if claim["source_key"] == "pubmed_eutilities"],
                len(selected),
            )
    current_counts = {
        row["source_key"]: row["count"]
        for row in conn.execute(
            """
            SELECT source_key, COUNT(*) AS count
            FROM evidence_claims
            WHERE source_key IN ('openalex_author_search', 'pubmed_eutilities')
            GROUP BY source_key
            """
        )
    }
    current_status_counts = {
        f"{row['source_key']}:{row['status']}": row["count"]
        for row in conn.execute(
            """
            SELECT source_key, status, COUNT(*) AS count
            FROM evidence_claims
            WHERE source_key IN ('openalex_author_search', 'pubmed_eutilities')
            GROUP BY source_key, status
            """
        )
    }
    durable_claims = current_research_claims(conn)
    conn.close()
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "people_processed": len(selected),
        "claims_generated": len(all_claims),
        "by_source": {
            source: sum(1 for claim in all_claims if claim["source_key"] == source)
            for source in sorted({claim["source_key"] for claim in all_claims})
        },
        "current_database_by_source": current_counts,
        "current_database_by_source_status": current_status_counts,
    }
    (OUT / "research_candidate_claims.json").write_text(
        json.dumps(durable_claims, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (OUT / "research_candidate_summary.json").write_text(dumps(summary) + "\n", encoding="utf-8")
    print(dumps(summary))


if __name__ == "__main__":
    main()
