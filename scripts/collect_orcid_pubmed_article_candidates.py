#!/usr/bin/env python3
"""Resolve ORCID DOI/PMID work candidates into PubMed article evidence."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import time
import xml.etree.ElementTree as ET
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
ARTIFACTS = ROOT / "artifacts" / "data"
ORCID_WORK_CLAIMS = ARTIFACTS / "orcid_work_candidate_claims.json"
OUT_CLAIMS = ARTIFACTS / "orcid_pubmed_article_candidate_claims.json"
OUT_SUMMARY = ARTIFACTS / "orcid_pubmed_article_candidate_summary.json"

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


def norm_space(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def normalized_label(text: str | None) -> str:
    text = norm_space(text).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return norm_space(text)


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
    parts = clean_name(name).split()
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


def normalize_doi(value: str | None) -> str:
    value = norm_space(value).lower()
    value = value.removeprefix("https://doi.org/").removeprefix("http://doi.org/").removeprefix("doi:")
    return value.strip()


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
            retry_after = response.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else 1.0 + attempt)
    return response


def source_ids(claim: dict) -> tuple[list[str], list[str]]:
    work = ((claim.get("evidence") or {}).get("work") or {})
    stable_ids = work.get("stable_ids") or {}
    pmids = [str(value).strip() for value in stable_ids.get("pmid", []) if str(value).strip()]
    dois = [normalize_doi(value) for value in stable_ids.get("doi", []) if normalize_doi(value)]
    if claim.get("claim_value", "").startswith("pmid:"):
        pmids.insert(0, claim["claim_value"].split(":", 1)[1])
    if claim.get("claim_value", "").startswith("doi:"):
        dois.insert(0, normalize_doi(claim["claim_value"].split(":", 1)[1]))
    return sorted(set(pmids)), sorted(set(dois))


def resolve_doi_to_pmids(session: requests.Session, doi: str) -> list[str]:
    if not doi:
        return []
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        f"?db=pubmed&retmode=json&retmax=5&term={quote(doi + '[AID]')}"
    )
    response = request_with_retry(session, url)
    response.raise_for_status()
    payload = response.json()
    return [str(value) for value in ((payload.get("esearchresult") or {}).get("idlist") or []) if str(value).strip()]


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
        pmid = norm_space(article.findtext(".//MedlineCitation/PMID"))
        if pmid:
            articles[pmid] = article
    return articles


def article_year(article: ET.Element) -> int | None:
    for path in [
        ".//Article/Journal/JournalIssue/PubDate/Year",
        ".//Article/ArticleDate/Year",
        ".//MedlineCitation/DateCompleted/Year",
    ]:
        value = norm_space(article.findtext(path))
        if value.isdigit():
            return int(value)
    return None


def article_dois(article: ET.Element) -> list[str]:
    dois = []
    for node in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        if (node.attrib.get("IdType") or "").lower() == "doi":
            doi = normalize_doi(node.text)
            if doi and doi not in dois:
                dois.append(doi)
    return dois


def article_authors(article: ET.Element) -> list[dict]:
    authors = []
    raw_authors = article.findall(".//Article/AuthorList/Author")
    for index, author in enumerate(raw_authors, start=1):
        last = norm_space(author.findtext("LastName"))
        fore = norm_space(author.findtext("ForeName"))
        initials = norm_space(author.findtext("Initials"))
        collective = norm_space(author.findtext("CollectiveName"))
        name = norm_space(f"{fore} {last}") if last else collective
        affiliations = [norm_space(node.text) for node in author.findall(".//AffiliationInfo/Affiliation") if norm_space(node.text)]
        if index == 1:
            position = "first"
        elif index == len(raw_authors):
            position = "last"
        else:
            position = "middle"
        authors.append(
            {
                "name": name,
                "last_name": last,
                "fore_name": fore,
                "initials": initials,
                "affiliations": affiliations,
                "position_index": index,
                "author_position": position,
            }
        )
    return authors


def article_text(article: ET.Element) -> str:
    parts = [
        norm_space(article.findtext(".//Article/ArticleTitle")),
        norm_space(article.findtext(".//Article/Journal/Title")),
    ]
    parts.extend(norm_space(node.text) for node in article.findall(".//MeshHeading/DescriptorName") if norm_space(node.text))
    return normalized_label(" ".join(parts))


def article_claim(person: dict, article: ET.Element, seed_claim: dict, seed_pmids: list[str], seed_dois: list[str]) -> dict | None:
    pmid = norm_space(article.findtext(".//MedlineCitation/PMID"))
    title = norm_space(article.findtext(".//Article/ArticleTitle"))
    journal = norm_space(article.findtext(".//Article/Journal/Title"))
    year = article_year(article)
    article_doi_values = article_dois(article)
    authors = article_authors(article)
    matched_authors = [author for author in authors if exactish_name_match(author["name"], person["display_name"])]
    if not matched_authors:
        return None

    matched_author = matched_authors[0]
    matched_affiliations = [aff for author in matched_authors for aff in author["affiliations"]]
    all_affiliations = [aff for author in authors for aff in author["affiliations"]]
    features = [
        "orcid_seeded_work",
        "pmid_present",
        "article_author_name_match",
        "author_position_known",
        f"author_position_{matched_author['author_position']}",
    ]
    seed_features = set(seed_claim.get("match_features") or [])
    if pmid in seed_pmids:
        features.append("pmid_from_orcid_work")
    if set(article_doi_values) & set(seed_dois):
        features.append("doi_consistent_with_orcid")
    if "orcid_name_match_from_profile" in seed_features:
        features.append("orcid_profile_name_match")
    if "orcid_external_ids_present_from_profile" in seed_features:
        features.append("orcid_profile_secondary_anchor")
    if "orcid_penn_affiliation_from_profile" in seed_features:
        features.append("orcid_profile_penn_affiliation")
    if penn_affiliation(matched_affiliations or all_affiliations):
        features.append("penn_affiliation")
    prior_anchor = prior_org_anchor(matched_affiliations or all_affiliations, person)
    if prior_anchor:
        features.append("prior_training_or_education_affiliation")
    terms = topic_terms(person)
    specialty_terms = [term for term in terms if term in article_text(article)]
    if specialty_terms:
        features.append("program_topic_match")
    if year and year >= 2016:
        features.append("recent_publication")

    confidence = 0.32
    confidence += 0.22 if "article_author_name_match" in features else 0
    confidence += 0.15 if "orcid_seeded_work" in features else 0
    confidence += 0.08 if "doi_consistent_with_orcid" in features else 0
    confidence += 0.08 if "orcid_profile_secondary_anchor" in features else 0
    confidence += 0.12 if "penn_affiliation" in features else 0
    confidence += 0.12 if "prior_training_or_education_affiliation" in features else 0
    confidence += 0.06 if "program_topic_match" in features else 0
    confidence += 0.03 if "recent_publication" in features else 0
    confidence = min(round(confidence, 3), 0.96)
    status = "needs_review" if confidence >= 0.75 else "candidate"

    return {
        "person_key": seed_claim["person_key"],
        "display_name": person["display_name"],
        "role": person["role"],
        "claim_type": "orcid_pubmed_article_candidate",
        "claim_value": pmid,
        "source_key": "pubmed_eutilities",
        "source_url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "source_type": "scholarly_api",
        "confidence": confidence,
        "status": status,
        "match_features": features,
        "reconciliation_notes": (
            "PubMed article resolved from ORCID public work DOI/PMID; accept only after reviewer "
            "confirms same-person ORCID linkage, article author position, and profile/source context."
        ),
        "evidence": {
            "utility_key": "orcid_pubmed_article_reconciliation",
            "collector": "scripts/collect_orcid_pubmed_article_candidates.py",
            "pmid": pmid,
            "title": title,
            "journal": journal,
            "publication_year": year,
            "article_dois": article_doi_values,
            "matched_authors": matched_authors,
            "matched_affiliations": matched_affiliations,
            "prior_anchor": prior_anchor,
            "program_topic_terms": specialty_terms,
            "orcid_work_claim": {
                "claim_value": seed_claim.get("claim_value"),
                "confidence": seed_claim.get("confidence"),
                "status": seed_claim.get("status"),
                "match_features": seed_claim.get("match_features", []),
                "source_url": seed_claim.get("source_url"),
                "orcid_profile_claim_value": (seed_claim.get("evidence") or {}).get("orcid_profile_claim_value"),
                "orcid": (seed_claim.get("evidence") or {}).get("orcid", ""),
                "work": (seed_claim.get("evidence") or {}).get("work", {}),
            },
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.34)
    parser.add_argument("--limit-people", type=int)
    parser.add_argument("--skip-doi-resolution", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    people = person_context(conn)
    conn.close()

    seed_claims = json.loads(ORCID_WORK_CLAIMS.read_text(encoding="utf-8")) if ORCID_WORK_CLAIMS.exists() else []
    seed_claims = [claim for claim in seed_claims if claim.get("person_key") in people]
    if args.limit_people:
        seen = set()
        limited = []
        for claim in seed_claims:
            seen.add(claim["person_key"])
            if len(seen) <= args.limit_people:
                limited.append(claim)
        seed_claims = limited

    session = requests.Session()
    session.headers["User-Agent"] = "redmank-orcid-pubmed-reconciliation/0.1 (candidate evidence only)"

    pmids_by_seed: dict[int, list[str]] = {}
    dois_by_seed: dict[int, list[str]] = {}
    doi_resolution: dict[str, list[str]] = {}
    for index, claim in enumerate(seed_claims):
        pmids, dois = source_ids(claim)
        pmids_by_seed[index] = list(pmids)
        dois_by_seed[index] = list(dois)
        if not args.skip_doi_resolution:
            for doi in dois:
                if doi not in doi_resolution:
                    doi_resolution[doi] = resolve_doi_to_pmids(session, doi)
                    time.sleep(args.sleep)
                for resolved in doi_resolution[doi]:
                    if resolved not in pmids_by_seed[index]:
                        pmids_by_seed[index].append(resolved)

    unique_pmids = sorted({pmid for values in pmids_by_seed.values() for pmid in values if pmid})
    articles = {}
    for start in range(0, len(unique_pmids), args.batch_size):
        batch = unique_pmids[start : start + args.batch_size]
        articles.update(fetch_articles(session, batch))
        print(f"fetched_pmids={min(start + len(batch), len(unique_pmids))}/{len(unique_pmids)}", flush=True)
        time.sleep(args.sleep)

    claims = []
    seen = set()
    skipped_missing_article = 0
    skipped_no_author_match = 0
    for index, seed_claim in enumerate(seed_claims):
        person = people.get(seed_claim["person_key"])
        if not person:
            continue
        for pmid in pmids_by_seed[index]:
            article = articles.get(str(pmid))
            if article is None:
                skipped_missing_article += 1
                continue
            claim = article_claim(person, article, seed_claim, pmids_by_seed[index], dois_by_seed[index])
            if not claim:
                skipped_no_author_match += 1
                continue
            key = (claim["person_key"], claim["claim_value"])
            if key in seen:
                continue
            seen.add(key)
            claims.append(claim)

    claims.sort(key=lambda row: (row["display_name"], row["claim_value"]))
    by_status = Counter(claim["status"] for claim in claims)
    by_feature = Counter(feature for claim in claims for feature in claim["match_features"])
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_key": "pubmed_eutilities",
        "utility_key": "orcid_pubmed_article_reconciliation",
        "orcid_work_claims_considered": len(seed_claims),
        "orcid_people_considered": len({claim["person_key"] for claim in seed_claims}),
        "seed_pmids": sum(1 for values in pmids_by_seed.values() if values),
        "unique_pmids_fetched": len(unique_pmids),
        "doi_values_considered": len({doi for values in dois_by_seed.values() for doi in values}),
        "doi_values_resolved_to_pmids": sum(1 for values in doi_resolution.values() if values),
        "article_claims": len(claims),
        "people_with_article_claims": len({claim["person_key"] for claim in claims}),
        "skipped_missing_article": skipped_missing_article,
        "skipped_no_author_name_match": skipped_no_author_match,
        "by_status": dict(sorted(by_status.items())),
        "top_match_features": dict(by_feature.most_common(25)),
        "policy": "ORCID-seeded PubMed article candidates are review-only publication evidence; they are not accepted person truth without independent identity/context review.",
    }
    OUT_CLAIMS.write_text(json.dumps(claims, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    OUT_SUMMARY.write_text(dumps(summary) + "\n", encoding="utf-8")
    print(dumps(summary))


if __name__ == "__main__":
    main()
