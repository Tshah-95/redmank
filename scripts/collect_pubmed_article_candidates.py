#!/usr/bin/env python3
"""Fetch article-level PubMed candidates for bounded author-query hits."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
import xml.etree.ElementTree as ET
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
ARTIFACTS = ROOT / "artifacts" / "data"
QUERY_CLAIMS = ARTIFACTS / "research_candidate_claims.json"
OUT_CLAIMS = ARTIFACTS / "pubmed_article_candidate_claims.json"
OUT_SUMMARY = ARTIFACTS / "pubmed_article_candidate_summary.json"

COMMON_TOPIC_WORDS = {
    "and",
    "critical",
    "current",
    "department",
    "disease",
    "fellowship",
    "health",
    "integrated",
    "internal",
    "medicine",
    "program",
    "residency",
    "resident",
    "surgery",
    "training",
}


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def clean_name(name: str) -> str:
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(
        r"\b(MD|DO|DPM|DDS|DMD|PhD|MPH|MBA|MSc|MS|MSEd|MBBS|MBChB|MPhil|PharmD)\b",
        " ",
        name,
        flags=re.I,
    )
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


def norm_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalized_label(text: str | None) -> str:
    text = norm_text(text).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return norm_text(text)


def person_context(conn: sqlite3.Connection) -> dict[str, dict]:
    rows = conn.execute("SELECT person_key, display_name, role, raw_json FROM people").fetchall()
    context = {}
    for row in rows:
        raw = json.loads(row["raw_json"])
        programs = raw.get("program_memberships") or [raw.get("program", "")]
        org_values = [
            raw.get("medical_school", ""),
            raw.get("residency_program", ""),
            raw.get("undergraduate_school", ""),
            raw.get("graduate_school", ""),
        ]
        context[row["person_key"]] = {
            "display_name": row["display_name"],
            "role": row["role"],
            "program": programs[0] if programs else "",
            "org_values": [value for value in org_values if value],
        }
    return context


def topic_terms(context: dict) -> list[str]:
    program = normalized_label(context.get("program", ""))
    terms = []
    for token in program.split():
        if len(token) >= 6 and token not in COMMON_TOPIC_WORDS:
            terms.append(token)
    return sorted(set(terms))


def prior_org_anchor(affiliations: list[str], context: dict) -> str | None:
    affiliation_text = normalized_label(" ".join(affiliations))
    for raw_value in context.get("org_values", []):
        value = normalized_label(raw_value)
        if len(value) >= 10 and value in affiliation_text:
            return raw_value
        tokens = [token for token in value.split() if len(token) >= 5]
        if len(tokens) >= 2 and sum(1 for token in tokens if token in affiliation_text) >= 2:
            return raw_value
    return None


def penn_affiliation(affiliations: list[str]) -> bool:
    text = normalized_label(" ".join(affiliations))
    return any(
        phrase in text
        for phrase in [
            "university pennsylvania",
            "penn medicine",
            "hospital university pennsylvania",
            "perelman school medicine",
            "childrens hospital philadelphia",
            "chop",
        ]
    )


def request_with_retry(session: requests.Session, url: str, attempts: int = 5) -> requests.Response:
    retryable_statuses = {429, 500, 502, 503, 504}
    for attempt in range(attempts):
        response = session.get(url, timeout=30)
        if response.status_code not in retryable_statuses:
            return response
        if attempt < attempts - 1:
            time.sleep(1.0 + attempt)
    return response


def load_query_claims(max_author_count: int, include_high_collision: bool) -> list[dict]:
    rows = json.loads(QUERY_CLAIMS.read_text(encoding="utf-8"))
    selected = []
    for row in rows:
        if row.get("source_key") != "pubmed_eutilities":
            continue
        evidence = row.get("evidence", {})
        count = int(evidence.get("count") or 0)
        pmids = [str(pmid) for pmid in evidence.get("pmids", []) if str(pmid).strip()]
        if not pmids or count == 0:
            continue
        if count <= max_author_count or include_high_collision:
            selected.append(row)
    return selected


def fetch_articles(session: requests.Session, pmids: list[str]) -> dict[str, ET.Element]:
    if not pmids:
        return {}
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&retmode=xml&id={quote(','.join(pmids))}"
    )
    response = request_with_retry(session, url)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    articles = {}
    for article in root.findall(".//PubmedArticle"):
        pmid = norm_text(article.findtext(".//MedlineCitation/PMID"))
        if pmid:
            articles[pmid] = article
    return articles


def article_year(article: ET.Element) -> int | None:
    for path in [
        ".//Article/Journal/JournalIssue/PubDate/Year",
        ".//Article/ArticleDate/Year",
        ".//MedlineCitation/DateCompleted/Year",
    ]:
        value = norm_text(article.findtext(path))
        if value.isdigit():
            return int(value)
    return None


def article_authors(article: ET.Element) -> list[dict]:
    authors = []
    for author in article.findall(".//Article/AuthorList/Author"):
        last = norm_text(author.findtext("LastName"))
        fore = norm_text(author.findtext("ForeName"))
        initials = norm_text(author.findtext("Initials"))
        collective = norm_text(author.findtext("CollectiveName"))
        name = norm_text(f"{fore} {last}") if last else collective
        affiliations = [norm_text(node.text) for node in author.findall(".//AffiliationInfo/Affiliation") if norm_text(node.text)]
        authors.append(
            {
                "name": name,
                "last_name": last,
                "fore_name": fore,
                "initials": initials,
                "affiliations": affiliations,
            }
        )
    return authors


def article_text(article: ET.Element) -> str:
    parts = [
        norm_text(article.findtext(".//Article/ArticleTitle")),
        norm_text(article.findtext(".//Article/Journal/Title")),
    ]
    parts.extend(norm_text(node.text) for node in article.findall(".//MeshHeading/DescriptorName") if norm_text(node.text))
    return normalized_label(" ".join(parts))


def article_claim(person: dict, article: ET.Element, query_claim: dict) -> dict | None:
    pmid = norm_text(article.findtext(".//MedlineCitation/PMID"))
    title = norm_text(article.findtext(".//Article/ArticleTitle"))
    journal = norm_text(article.findtext(".//Article/Journal/Title"))
    year = article_year(article)
    authors = article_authors(article)
    matched_authors = [author for author in authors if exactish_name_match(author["name"], person["display_name"])]
    if not matched_authors:
        return None
    matched_affiliations = []
    for author in matched_authors:
        matched_affiliations.extend(author["affiliations"])
    all_affiliations = [aff for author in authors for aff in author["affiliations"]]
    features = ["article_author_name_match"]
    if int((query_claim.get("evidence") or {}).get("count") or 0) <= 20:
        features.append("bounded_author_query")
    if penn_affiliation(matched_affiliations or all_affiliations):
        features.append("penn_affiliation")
    prior_anchor = prior_org_anchor(matched_affiliations or all_affiliations, person)
    if prior_anchor:
        features.append("prior_training_or_education_affiliation")
    terms = topic_terms(person)
    text = article_text(article)
    specialty_terms = [term for term in terms if term in text]
    if specialty_terms:
        features.append("program_topic_match")
    if year and year >= 2016:
        features.append("recent_publication")

    confidence = 0.25
    confidence += 0.25 if "article_author_name_match" in features else 0
    confidence += 0.12 if "bounded_author_query" in features else 0
    confidence += 0.22 if "penn_affiliation" in features else 0
    confidence += 0.18 if "prior_training_or_education_affiliation" in features else 0
    confidence += 0.08 if "program_topic_match" in features else 0
    confidence += 0.03 if "recent_publication" in features else 0
    confidence = min(round(confidence, 3), 0.95)
    status = "needs_review" if confidence >= 0.75 else "candidate"
    return {
        "person_key": query_claim["person_key"],
        "display_name": person["display_name"],
        "role": person["role"],
        "claim_type": "pubmed_article_candidate",
        "claim_value": pmid,
        "source_key": "pubmed_eutilities",
        "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "source_type": "scholarly_api",
        "confidence": confidence,
        "status": status,
        "match_features": features,
        "reconciliation_notes": "Article-level PubMed candidate; accept only after identity review confirms non-name anchors.",
        "evidence": {
            "utility_key": "pubmed_eutilities",
            "pmid": pmid,
            "title": title,
            "journal": journal,
            "publication_year": year,
            "matched_authors": matched_authors,
            "matched_affiliations": matched_affiliations,
            "prior_anchor": prior_anchor,
            "program_topic_terms": specialty_terms,
            "query_claim_value": query_claim.get("claim_value"),
            "query_features": query_claim.get("match_features", []),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-author-count", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.34)
    parser.add_argument("--limit-people", type=int)
    parser.add_argument("--include-high-collision", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    people = person_context(conn)
    conn.close()

    query_claims = load_query_claims(args.max_author_count, args.include_high_collision)
    if args.limit_people:
        seen = set()
        limited = []
        for claim in query_claims:
            if claim["person_key"] not in seen:
                seen.add(claim["person_key"])
            if len(seen) <= args.limit_people:
                limited.append(claim)
        query_claims = limited

    pmids = sorted({pmid for claim in query_claims for pmid in claim.get("evidence", {}).get("pmids", [])})
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-pubmed-article-reconciliation/0.1 (candidate evidence only)"
    articles = {}
    for start in range(0, len(pmids), args.batch_size):
        batch = pmids[start : start + args.batch_size]
        articles.update(fetch_articles(session, batch))
        print(f"fetched_pmids={min(start + len(batch), len(pmids))}/{len(pmids)}", flush=True)
        time.sleep(args.sleep)

    claims = []
    for query_claim in query_claims:
        person = people.get(query_claim["person_key"])
        if not person:
            continue
        for pmid in query_claim.get("evidence", {}).get("pmids", []):
            article = articles.get(str(pmid))
            if article is None:
                continue
            claim = article_claim(person, article, query_claim)
            if claim:
                claims.append(claim)

    claims.sort(key=lambda row: (row["display_name"], row["claim_value"]))
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "query_claims_considered": len(query_claims),
        "unique_pmids_fetched": len(pmids),
        "article_claims": len(claims),
        "max_author_count": args.max_author_count,
        "include_high_collision": args.include_high_collision,
        "by_status": {},
        "by_feature": {},
    }
    for claim in claims:
        summary["by_status"][claim["status"]] = summary["by_status"].get(claim["status"], 0) + 1
        for feature in claim["match_features"]:
            summary["by_feature"][feature] = summary["by_feature"].get(feature, 0) + 1

    OUT_CLAIMS.write_text(json.dumps(claims, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    OUT_SUMMARY.write_text(dumps(summary) + "\n", encoding="utf-8")
    print(dumps(summary))


if __name__ == "__main__":
    main()
