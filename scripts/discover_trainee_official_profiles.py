#!/usr/bin/env python3
"""Discover official profile candidates for trainees missing profile URLs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, unquote, urlparse


DEPS_PATH = Path(os.environ.get("PENN_CORPUS_DEPS", "/tmp/penn_corpus_deps"))
if DEPS_PATH.exists():
    sys.path.insert(0, str(DEPS_PATH))

try:
    import requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing scraper dependency. Install with: "
        "python3 -m pip install --target /tmp/penn_corpus_deps -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
DDG_HTML = "https://html.duckduckgo.com/html/"

QUERY_CSV = ARTIFACTS / "trainee_profile_search_queries.csv"
OBSERVATION_CSV = ARTIFACTS / "trainee_profile_search_observations.csv"
CANDIDATE_CSV = ARTIFACTS / "trainee_profile_discovery_candidates.csv"
CLAIMS_JSON = ARTIFACTS / "trainee_profile_discovery_claims.json"
SOURCES_JSON = ARTIFACTS / "trainee_profile_discovery_sources.json"
SUMMARY_JSON = ARTIFACTS / "trainee_profile_discovery_summary.json"

OFFICIAL_DOMAINS = {
    "www3.pennmedicine.org",
    "pennmedicine.org",
    "www.med.upenn.edu",
    "med.upenn.edu",
    "pathology.med.upenn.edu",
    "www.chop.edu",
    "chop.edu",
}
OFFICIAL_DOMAIN_SUFFIXES = (".pennmedicine.org", ".med.upenn.edu", ".chop.edu")
PROFILE_PATH_RE = re.compile(
    r"/providers/profile/|/faculty/index\.php|/department/people/|/(people|profile|profiles)(/|$)",
    re.I,
)
ROLE_TERMS = ["resident", "residency", "fellow", "fellowship", "trainee", "education", "training"]
PENN_TERMS = ["penn", "penn medicine", "university of pennsylvania", "perelman", "hup", "chop"]


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).replace("\xa0", " ")).strip()


def redact(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


def clean_name(name: str) -> str:
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(
        r"\b(MD|M\.D\.|DO|D\.O\.|DPM|DDS|DMD|PhD|Ph\.D\.|MPH|MBA|MSc|MS|MSEd|MBBS|MBChB|MPhil|PharmD)\b",
        " ",
        name,
        flags=re.I,
    )
    name = re.sub(r"[^A-Za-z' -]+", " ", name)
    return norm(name)


def normalized_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean_name(name).lower()).strip()


def slug(value: str, max_len: int = 72) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:max_len] or "row"


def sha(value: str, length: int = 16) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]


def key_for(prefix: str, *parts: object) -> str:
    basis = "|".join(str(part or "") for part in parts)
    return f"{prefix}_{slug(basis, 48)}_{sha(basis, 16)}"


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def normalize_ddg_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//duckduckgo.com/l/?"):
        parsed = urlparse("https:" + url)
        params = dict(item.split("=", 1) for item in parsed.query.split("&") if "=" in item)
        if "uddg" in params:
            return unquote(params["uddg"])
    return url


def official_domain(domain: str) -> bool:
    domain = (domain or "").lower()
    return domain in OFFICIAL_DOMAINS or any(domain.endswith(suffix) for suffix in OFFICIAL_DOMAIN_SUFFIXES)


def name_present(display_name: str, text: str) -> bool:
    target = normalized_name(display_name)
    haystack = normalized_name(text)
    tokens = [token for token in target.split() if len(token) > 1]
    return bool(tokens) and all(token in haystack for token in tokens)


def program_terms(program_name: str) -> list[str]:
    terms = []
    for token in re.split(r"[^A-Za-z0-9]+", program_name.lower()):
        if len(token) >= 5 and token not in {"fellowship", "residency", "program", "medicine"}:
            terms.append(token)
    return terms[:6]


def load_people(conn: sqlite3.Connection, limit: int | None) -> list[dict]:
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT p.person_key, p.display_name, p.role, p.raw_json,
               q.task_key, q.priority, q.priority_band, q.query,
               q.blocking_risk, q.recency_policy, q.provenance_policy,
               q.acceptance_rule
        FROM people p
        JOIN person_enrichment_work_queue q ON q.person_key = p.person_key
        WHERE q.task_type = 'official_profile_search'
        ORDER BY CAST(q.priority AS INTEGER) DESC, p.role, p.display_name
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    return [dict(row) for row in conn.execute(sql)]


def query_specs(person: dict, max_queries: int | None = None) -> list[dict]:
    display = person["display_name"]
    plain = clean_name(display)
    raw = json.loads(person.get("raw_json") or "{}")
    programs = raw.get("program_memberships") or [raw.get("program") or ""]
    program = next((item for item in programs if item), "")
    base_queries = [
        person.get("query") or "",
        f'site:www3.pennmedicine.org "{plain}" profile',
        f'site:med.upenn.edu "{plain}"',
        f'site:pathology.med.upenn.edu "{plain}"',
        f'site:chop.edu "{plain}" {person.get("role") or ""}',
        f'"{plain}" "Penn Medicine" "{program}"',
    ]
    seen = set()
    output = []
    for index, query in enumerate(base_queries):
        query = norm(query)
        if not query or query in seen:
            continue
        seen.add(query)
        query_kind = "queue_query" if index == 0 and person.get("query") else "official_profile_search"
        output.append(
            {
                "query_key": key_for("trainee_profile_query", person["person_key"], query),
                "person_key": person["person_key"],
                "display_name": display,
                "role": person.get("role") or "",
                "program_name": program,
                "task_key": person.get("task_key") or "",
                "query_kind": query_kind,
                "query": query,
                "query_url": f"{DDG_HTML}?q={quote_plus(query)}",
                "priority": person.get("priority") or "",
                "priority_band": person.get("priority_band") or "",
            }
        )
        if max_queries and len(output) >= max_queries:
            break
    return output


def ddg_results(
    session: requests.Session,
    spec: dict,
    max_results: int,
    search_timeout: float,
) -> tuple[list[dict], dict]:
    searched_at = datetime.now(timezone.utc).isoformat()
    response = session.get(DDG_HTML, params={"q": spec["query"]}, timeout=search_timeout)
    soup = BeautifulSoup(response.text, "lxml")
    observation = {
        **spec,
        "searched_at": searched_at,
        "search_http_status": response.status_code,
        "result_count": 0,
        "error": "" if response.status_code == 200 else "search_endpoint_non_200",
    }
    if response.status_code != 200:
        return [], observation
    rows = []
    for rank, result in enumerate(soup.select(".result")[:max_results], start=1):
        link = result.select_one(".result__a")
        if not link:
            continue
        url = normalize_ddg_url(link.get("href", ""))
        if not url:
            continue
        snippet_node = result.select_one(".result__snippet")
        rows.append(
            {
                **spec,
                "result_rank": rank,
                "result_url": url,
                "result_domain": urlparse(url).netloc.lower(),
                "result_title": redact(norm(link.get_text(" "))),
                "result_snippet": redact(norm(snippet_node.get_text(" ") if snippet_node else "")),
                "search_status": "ok",
                "searched_at": searched_at,
                "search_http_status": response.status_code,
            }
        )
    observation["result_count"] = len(rows)
    return rows, observation


def probe_page(session: requests.Session, result: dict) -> dict:
    fetched_at = datetime.now(timezone.utc).isoformat()
    probe = {
        "probe_http_status": "",
        "probe_content_type": "",
        "probe_title": "",
        "probe_text_length": 0,
        "probe_sha256": "",
        "probe_error": "",
        "probed_at": fetched_at,
        "page_term_hits": "",
        "page_name_present": 0,
    }
    parsed = urlparse(result["result_url"])
    if parsed.scheme not in {"http", "https"}:
        probe["probe_error"] = "non_http_url"
        return probe
    try:
        response = session.get(result["result_url"], timeout=20, allow_redirects=True)
        probe["probe_http_status"] = response.status_code
        probe["probe_content_type"] = response.headers.get("content-type", "")
        probe["probe_sha256"] = hashlib.sha256(response.content).hexdigest()
        if "text/html" not in probe["probe_content_type"]:
            return probe
        soup = BeautifulSoup(response.text, "lxml")
        title = redact(norm(soup.title.get_text(" ") if soup.title else ""))
        text = redact(norm(soup.get_text(" ")))
        probe["probe_title"] = title
        probe["probe_text_length"] = len(text)
        probe["page_name_present"] = int(name_present(result["display_name"], f"{title} {text[:6000]}"))
        hits = []
        low = f"{title} {text[:6000]}".lower()
        if any(term in low for term in ROLE_TERMS):
            hits.append("role_or_training_term")
        if any(term in low for term in PENN_TERMS):
            hits.append("penn_or_chop_term")
        for term in program_terms(result.get("program_name") or ""):
            if term in low:
                hits.append("program_term")
                break
        probe["page_term_hits"] = "; ".join(sorted(set(hits)))
    except requests.RequestException as exc:
        probe["probe_error"] = f"{type(exc).__name__}: {str(exc)[:220]}"
    return probe


def classify_candidate(row: dict) -> tuple[str, float, list[str], str]:
    url = row.get("result_url") or ""
    domain = row.get("result_domain") or urlparse(url).netloc.lower()
    haystack = " ".join(
        [
            row.get("result_title", ""),
            row.get("result_snippet", ""),
            row.get("probe_title", ""),
            row.get("page_term_hits", ""),
            url,
        ]
    )
    features = []
    if name_present(row.get("display_name") or "", haystack) or int(row.get("page_name_present") or 0):
        features.append("name_present")
    if official_domain(domain):
        features.append("official_domain")
    if domain.endswith("pennmedicine.org") or domain.endswith("med.upenn.edu"):
        features.append("penn_domain")
    if domain.endswith("chop.edu"):
        features.append("chop_domain")
    if PROFILE_PATH_RE.search(url):
        features.append("profile_path")
    if "role_or_training_term" in (row.get("page_term_hits") or "") or any(term in haystack.lower() for term in ROLE_TERMS):
        features.append("role_or_training_term")
    if "program_term" in (row.get("page_term_hits") or ""):
        features.append("program_term")
    if row.get("probe_http_status") == 200:
        features.append("probe_http_200")
    if row.get("probe_sha256"):
        features.append("content_hash_recorded")

    score = 0.12
    score += 0.22 if "name_present" in features else 0
    score += 0.22 if "official_domain" in features else 0
    score += 0.16 if "profile_path" in features else 0
    score += 0.08 if "role_or_training_term" in features else 0
    score += 0.08 if "program_term" in features else 0
    score += 0.05 if "probe_http_200" in features else 0
    if row.get("result_rank") and int(row["result_rank"]) <= 2:
        score += 0.03

    if {"official_domain", "name_present", "profile_path"} <= set(features):
        status = "official_profile_candidate"
    elif "official_domain" in features and "name_present" in features:
        status = "official_profile_context_candidate"
    elif "official_domain" in features:
        status = "official_context_candidate"
        score = min(score, 0.55)
    elif "name_present" in features and any(term in haystack.lower() for term in PENN_TERMS):
        status = "external_profile_context_candidate"
        score = min(score, 0.48)
    else:
        status = "low_signal_search_result"
        score = min(score, 0.3)

    required = "Review candidate for same-person identity, official ownership, and current trainee/program anchor before accepting profile enrichment."
    if status == "official_profile_candidate":
        required = "Confirm same-person identity and official source ownership; do not use as current roster truth unless linked from a current roster or profile states current trainee role."
    if status == "low_signal_search_result":
        required = "Keep as discovery context only unless another source supplies official profile or identity anchors."
    return status, round(min(score, 0.92), 3), sorted(set(features)), required


def candidate_to_claim(row: dict) -> dict:
    status = "needs_review" if row["candidate_status"] in {"official_profile_candidate", "official_profile_context_candidate"} else "candidate"
    source_key = row["source_key"]
    return {
        "claim_key": key_for("trainee_profile_discovery_claim", row["person_key"], row["candidate_url"]),
        "person_key": row["person_key"],
        "display_name": row["display_name"],
        "role": row["role"],
        "program_context": row["program_name"],
        "claim_type": "official_profile_url_candidate",
        "claim_value": row["candidate_url"],
        "source_key": source_key,
        "source_url": row["candidate_url"],
        "source_type": "official_trainee_profile",
        "confidence": row["confidence"],
        "status": status,
        "match_features": json.loads(row["match_features_json"]),
        "reconciliation_notes": row["required_next_evidence"],
        "evidence": {
            "origin": "official_profile_search_discovery",
            "candidate_status": row["candidate_status"],
            "candidate_key": row["candidate_key"],
            "query_key": row["query_key"],
            "query": row["query"],
            "result_rank": row["result_rank"],
            "result_title": row["candidate_title"],
            "result_snippet": row["result_snippet"],
            "probe_http_status": row["http_status"],
            "probe_sha256": row["sha256"],
            "page_term_hits": row["page_term_hits"],
            "display_safety_status": "safe_for_default_display",
            "utility_key": "official_trainee_profile_discovery",
        },
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--max-people", type=int)
    parser.add_argument("--max-queries-per-person", type=int, default=3)
    parser.add_argument("--max-results", type=int, default=4)
    parser.add_argument("--search-timeout", type=float, default=8.0)
    parser.add_argument("--probe-pages", action="store_true")
    parser.add_argument("--skip-search", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(args.db)
    people = load_people(conn, args.max_people)
    conn.close()
    queries = [query for person in people for query in query_specs(person, args.max_queries_per_person)]

    session = requests.Session()
    session.headers["User-Agent"] = "redmank-trainee-official-profile-discovery/0.1"
    observations = []
    candidates_by_key = {}
    for spec in [] if args.skip_search else queries:
        try:
            results, observation = ddg_results(session, spec, args.max_results, args.search_timeout)
        except requests.RequestException as exc:
            results = []
            observation = {
                **spec,
                "searched_at": datetime.now(timezone.utc).isoformat(),
                "search_http_status": 0,
                "result_count": 0,
                "error": f"{type(exc).__name__}: {str(exc)[:220]}",
            }
        observations.append(observation)
        for result in results:
            if args.probe_pages:
                result.update(probe_page(session, result))
                time.sleep(args.sleep)
            else:
                result.update(
                    {
                        "probe_http_status": "",
                        "probe_content_type": "",
                        "probe_title": "",
                        "probe_text_length": 0,
                        "probe_sha256": "",
                        "probe_error": "",
                        "probed_at": "",
                        "page_term_hits": "",
                        "page_name_present": 0,
                    }
                )
            status, confidence, features, required = classify_candidate(result)
            candidate_url = result["result_url"]
            candidate = {
                "candidate_key": key_for("trainee_profile_candidate", result["person_key"], candidate_url),
                "person_key": result["person_key"],
                "display_name": result["display_name"],
                "role": result["role"],
                "program_name": result.get("program_name") or "",
                "task_key": result.get("task_key") or "",
                "query_key": result["query_key"],
                "query_kind": result["query_kind"],
                "query": result["query"],
                "candidate_status": status,
                "priority": int(round(confidence * 100)) + (10 if status == "official_profile_candidate" else 0),
                "confidence": confidence,
                "candidate_title": result["result_title"] or result.get("probe_title") or "",
                "candidate_url": candidate_url,
                "result_rank": result["result_rank"],
                "result_domain": result["result_domain"],
                "result_snippet": result["result_snippet"],
                "http_status": result.get("probe_http_status") or "",
                "content_type": result.get("probe_content_type") or "",
                "text_length": result.get("probe_text_length") or 0,
                "sha256": result.get("probe_sha256") or "",
                "probed_at": result.get("probed_at") or "",
                "page_term_hits": result.get("page_term_hits") or "",
                "match_features_json": dumps(features),
                "required_next_evidence": required,
                "source_key": key_for("trainee_profile_discovery", candidate_url),
                "evidence_json": dumps(result),
                "discovered_at": generated_at,
            }
            current = candidates_by_key.get(candidate["candidate_key"])
            if not current or int(candidate["priority"]) > int(current["priority"]):
                candidates_by_key[candidate["candidate_key"]] = candidate
        time.sleep(args.sleep)

    candidates = sorted(
        candidates_by_key.values(),
        key=lambda row: (-int(row["priority"]), row["display_name"], int(row["result_rank"] or 999)),
    )
    claims = [candidate_to_claim(row) for row in candidates if row["candidate_status"] != "low_signal_search_result"]
    sources = [
        {
            "source_key": row["source_key"],
            "url": row["candidate_url"],
            "source_type": "official_trainee_profile",
            "title": row["candidate_title"],
            "fetched_at": row["probed_at"] or row["discovered_at"],
            "http_status": row["http_status"],
            "sha256": row["sha256"],
            "person_key": row["person_key"],
            "display_name": row["display_name"],
            "role": row["role"],
            "program": row["program_name"],
            "candidate_status": row["candidate_status"],
            "confidence": row["confidence"],
        }
        for row in candidates
        if row["candidate_status"] in {"official_profile_candidate", "official_profile_context_candidate"}
    ]
    summary = {
        "generated_at": generated_at,
        "people_considered": len(people),
        "query_rows": len(queries),
        "search_skipped": args.skip_search,
        "search_observations": len(observations),
        "candidate_rows": len(candidates),
        "claim_rows": len(claims),
        "source_rows": len(sources),
        "by_candidate_status": dict(sorted(Counter(row["candidate_status"] for row in candidates).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in candidates).items())),
        "by_result_domain": dict(sorted(Counter(row["result_domain"] for row in candidates).most_common(25))),
        "by_search_http_status": dict(sorted(Counter(str(row.get("search_http_status", "")) for row in observations).items())),
        "by_search_error": dict(sorted(Counter(row.get("error", "") for row in observations if row.get("error")).items())),
        "official_profile_candidate_people": len(
            {row["person_key"] for row in candidates if row["candidate_status"] == "official_profile_candidate"}
        ),
        "official_or_context_candidate_people": len(
            {
                row["person_key"]
                for row in candidates
                if row["candidate_status"] in {"official_profile_candidate", "official_profile_context_candidate"}
            }
        ),
        "csv": str(CANDIDATE_CSV.relative_to(ROOT)),
        "claims_json": str(CLAIMS_JSON.relative_to(ROOT)),
        "sources_json": str(SOURCES_JSON.relative_to(ROOT)),
        "policy": "Discovered profile URLs are candidate evidence only. They do not mutate people.profile_url unless an official roster-linked profile or reviewer-accepted evidence later confirms same-person/current-trainee context.",
    }

    query_fields = [
        "query_key",
        "person_key",
        "display_name",
        "role",
        "program_name",
        "task_key",
        "query_kind",
        "query",
        "query_url",
        "priority",
        "priority_band",
    ]
    observation_fields = query_fields + ["searched_at", "search_http_status", "result_count", "error"]
    candidate_fields = [
        "candidate_key",
        "person_key",
        "display_name",
        "role",
        "program_name",
        "task_key",
        "query_key",
        "query_kind",
        "query",
        "candidate_status",
        "priority",
        "confidence",
        "candidate_title",
        "candidate_url",
        "result_rank",
        "result_domain",
        "result_snippet",
        "http_status",
        "content_type",
        "text_length",
        "sha256",
        "probed_at",
        "page_term_hits",
        "match_features_json",
        "required_next_evidence",
        "source_key",
        "evidence_json",
        "discovered_at",
    ]
    write_csv(QUERY_CSV, queries, query_fields)
    write_csv(OBSERVATION_CSV, observations, observation_fields)
    write_csv(CANDIDATE_CSV, candidates, candidate_fields)
    CLAIMS_JSON.write_text(json.dumps(claims, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    SOURCES_JSON.write_text(json.dumps(sources, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
