#!/usr/bin/env python3
"""Probe official HUP GME coverage gaps for likely roster source URLs."""

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
from urllib.parse import quote_plus, unquote, urldefrag, urljoin, urlparse

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

from scrape_penn_gme_gap_rosters import (
    extract_accordion_headers,
    extract_bio_cards,
    extract_heading_name_lists,
    extract_neurology_archive_cards,
    extract_obgyn_current_fellows,
    extract_pathology_current_residents,
    extract_pathology_people_accordion,
    extract_profiles,
)


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"
DDG_HTML = "https://html.duckduckgo.com/html/"

SEARCH_QUERY_CSV = ARTIFACTS / "penn_gme_gap_source_search_queries.csv"
SEARCH_OBSERVATION_CSV = ARTIFACTS / "penn_gme_gap_source_search_observations.csv"

ROSTER_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"\bcurrent\s+(residents?|fellows?|trainees?)\b",
        r"\bcurrent\s+house\s+staff\b",
        r"\bour\s+(residents?|fellows?|trainees?)\b",
        r"\bmeet\s+(our\s+)?(residents?|fellows?|trainees?)\b",
        r"\bresident\s+(roster|profiles?|directory)\b",
        r"\bfellow\s+(roster|profiles?|directory)\b",
        r"\btrainee\s+(roster|profiles?|directory)\b",
        r"/(current-)?(residents?|fellows?|resident-profiles)(/|\.html|$)",
        r"\b(residents?|fellows?)\b$",
    ]
]
CONTEXT_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"\bhow to apply\b",
        r"\bapplication\b",
        r"\bcurriculum\b",
        r"\bprogram overview\b",
        r"\bdidactics\b",
        r"\bpeople\b",
    ]
]
EXCLUDE_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"\bapply\b",
        r"\beras\b",
        r"\bsalary\b",
        r"\bbenefits\b",
        r"\bpolic(y|ies)\b",
        r"\balumni\b",
        r"\bgraduates?\b",
        r"\bcontact\b",
        r"\bnews\b",
        r"\bevents?\b",
        r"\bpublications?\b",
    ]
]
STRONG_ROSTER_CUE_PATTERNS = [
    re.compile(pattern, re.I)
    for pattern in [
        r"\bcurrent\s+(residents?|fellows?|trainees?)\b",
        r"\bour\s+(residents?|fellows?|trainees?)\b",
        r"\bmeet\s+(our\s+)?(residents?|fellows?|trainees?)\b",
        r"\b(resident|fellow|trainee)\s+(roster|profiles?|directory)\b",
        r"/(current-)?(residents?|fellows?|resident-profiles)(/|\.html|$)",
    ]
]


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).replace("\xa0", " ")).strip()


def key_for(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48]
    return f"{prefix}_{slug}_{digest}"


def query_key_for(row: sqlite3.Row, query_kind: str, query: str) -> str:
    return key_for("program_source_query", f"{row['official_program_key']}:{query_kind}:{query}")


def observation_key_for(query_key: str) -> str:
    return key_for("program_source_search_observation", query_key)


def canonical_url(url: str) -> str:
    if not url:
        return ""
    clean, _fragment = urldefrag(url)
    return clean.rstrip("/")


def normalize_search_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//duckduckgo.com/l/?"):
        parsed = urlparse("https:" + url)
        params = {}
        for item in parsed.query.split("&"):
            if "=" in item:
                key, value = item.split("=", 1)
                params[key] = value
        if params.get("uddg"):
            return unquote(params["uddg"])
    return url


def is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def same_pennish_domain(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(
        host == domain or host.endswith("." + domain)
        for domain in [
            "pennmedicine.org",
            "upenn.edu",
            "uphs.upenn.edu",
            "dental.upenn.edu",
        ]
    )


def pattern_hits(text: str, patterns: list[re.Pattern]) -> list[str]:
    return [pattern.pattern for pattern in patterns if pattern.search(text)]


def classify_candidate(label: str, url: str, source_role: str) -> tuple[str, float, list[str]]:
    haystack = f"{label} {url}"
    roster_hits = pattern_hits(haystack, ROSTER_PATTERNS)
    context_hits = pattern_hits(haystack, CONTEXT_PATTERNS)
    exclude_hits = pattern_hits(haystack, EXCLUDE_PATTERNS)
    reasons = []
    confidence = 0.2
    status = "program_context_candidate"
    if source_role == "official_program_url":
        confidence += 0.15
        reasons.append("official_program_url")
    if source_role == "known_discovery_url":
        confidence += 0.1
        reasons.append("known_discovery_url")
    if source_role == "linked_candidate":
        confidence += 0.05
        reasons.append("linked_from_gap_page")
    if roster_hits:
        confidence += min(0.5, 0.2 + 0.1 * len(roster_hits))
        status = "roster_source_candidate"
        reasons.append("roster_language")
    if context_hits:
        confidence += 0.05
        reasons.append("program_context_language")
    if exclude_hits and not roster_hits:
        confidence -= 0.15
        reasons.append("non_roster_language")
    if not same_pennish_domain(url):
        confidence -= 0.2
        reasons.append("external_domain")
    confidence = max(0.05, min(round(confidence, 3), 0.95))
    if confidence < 0.3:
        status = "low_value_candidate"
    return status, confidence, reasons


def gap_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        """
        SELECT
          u.official_program_key,
          u.sponsoring_institution,
          u.department,
          u.program_type,
          u.program_name,
          u.program_url,
          a.coverage_status,
          a.discovery_url
        FROM official_program_universe u
        JOIN official_program_coverage_audit a
          ON a.official_program_key = u.official_program_key
        WHERE a.coverage_status != 'covered_current_roster'
        ORDER BY a.coverage_status, u.department, u.program_type, u.program_name
        """
    ).fetchall()


def search_query_specs(rows: list[sqlite3.Row], generated_at: str, max_queries_per_program: int | None) -> list[dict]:
    specs = []
    for row in rows:
        base = [
            (
                "official_program_current_roster_search",
                f'site:pennmedicine.org "{row["program_name"]}" "current" "{row["program_type"]}"',
            ),
            (
                "upenn_current_roster_search",
                f'site:upenn.edu "{row["program_name"]}" "current" "{row["program_type"]}" "Penn"',
            ),
            (
                "department_current_roster_search",
                f'"Penn" "{row["department"]}" "{row["program_name"]}" "current" "fellows" "residents"',
            ),
        ]
        seen = set()
        emitted = 0
        for index, (query_kind, query) in enumerate(base):
            query = norm(query)
            if not query or query in seen:
                continue
            seen.add(query)
            specs.append(
                {
                    "query_key": query_key_for(row, query_kind, query),
                    "official_program_key": row["official_program_key"],
                    "department": row["department"],
                    "program_type": row["program_type"],
                    "program_name": row["program_name"],
                    "coverage_status": row["coverage_status"],
                    "query_kind": query_kind,
                    "query": query,
                    "query_url": f"{DDG_HTML}?q={quote_plus(query)}",
                    "priority": 100 - index * 10 + (15 if row["coverage_status"] == "not_discovered" else 0),
                    "generated_at": generated_at,
                }
            )
            emitted += 1
            if max_queries_per_program and emitted >= max_queries_per_program:
                break
    return specs


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def search_rows_for_scope(rows: list[sqlite3.Row], search_scope: str) -> list[sqlite3.Row]:
    if search_scope == "all_gaps":
        return rows
    if search_scope == "not_discovered":
        return [row for row in rows if row["coverage_status"] == "not_discovered"]
    if search_scope == "discovered_no_current_roster":
        return [row for row in rows if row["coverage_status"] == "discovered_no_current_roster"]
    raise ValueError(f"unknown search scope: {search_scope}")


def search_results(
    session: requests.Session,
    spec: dict,
    max_results: int,
    search_timeout: float,
) -> tuple[list[dict], dict]:
    searched_at = datetime.now(timezone.utc).isoformat()
    try:
        response = session.get(DDG_HTML, params={"q": spec["query"]}, timeout=search_timeout)
    except requests.RequestException as exc:
        return [], {
            "observation_key": observation_key_for(spec["query_key"]),
            **spec,
            "searched_at": searched_at,
            "search_http_status": 0,
            "result_count": 0,
            "error": f"{type(exc).__name__}: {str(exc)[:300]}",
        }
    soup = BeautifulSoup(response.text, "lxml")
    observation = {
        "observation_key": observation_key_for(spec["query_key"]),
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
        url = canonical_url(normalize_search_url(link.get("href", "")))
        if not url or not is_http_url(url):
            continue
        snippet = result.select_one(".result__snippet")
        rows.append(
            {
                **spec,
                "result_rank": rank,
                "result_url": url,
                "result_domain": urlparse(url).netloc.lower(),
                "result_title": norm(link.get_text(" ")),
                "result_snippet": norm(snippet.get_text(" ") if snippet else ""),
                "searched_at": searched_at,
                "search_http_status": response.status_code,
            }
        )
    observation["result_count"] = len(rows)
    return rows, observation


def fetch_page(session: requests.Session, url: str) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    try:
        response = session.get(url, timeout=25)
        body = response.text if "text/html" in response.headers.get("content-type", "") else ""
        soup = BeautifulSoup(body, "lxml") if body else BeautifulSoup("", "lxml")
        title = norm(soup.title.get_text(" ")) if soup.title else ""
        text = norm(soup.get_text(" "))
        return {
            "url": response.url,
            "requested_url": url,
            "fetched_at": started,
            "http_status": response.status_code,
            "content_type": response.headers.get("content-type", ""),
            "sha256": hashlib.sha256(response.content).hexdigest(),
            "title": title,
            "text_length": len(text),
            "roster_term_count": sum(1 for pattern in ROSTER_PATTERNS if pattern.search(text)),
            "context_term_count": sum(1 for pattern in CONTEXT_PATTERNS if pattern.search(text)),
            "soup": soup,
        }
    except requests.RequestException as exc:
        return {
            "url": url,
            "requested_url": url,
            "fetched_at": started,
            "http_status": 0,
            "content_type": "",
            "sha256": "",
            "title": "",
            "text_length": 0,
            "roster_term_count": 0,
            "context_term_count": 0,
            "error": f"{type(exc).__name__}: {str(exc)[:300]}",
            "soup": BeautifulSoup("", "lxml"),
        }


def source_urls_for_gap(row: sqlite3.Row) -> list[tuple[str, str]]:
    urls = []
    if row["program_url"]:
        urls.append(("official_program_url", row["program_url"]))
    if row["discovery_url"] and row["discovery_url"] != row["program_url"]:
        urls.append(("known_discovery_url", row["discovery_url"]))
    seen = set()
    deduped = []
    for source_role, url in urls:
        clean = canonical_url(url)
        if clean and clean not in seen and is_http_url(clean):
            seen.add(clean)
            deduped.append((source_role, clean))
    return deduped


def link_candidates(soup: BeautifulSoup, base_url: str) -> list[tuple[str, str]]:
    candidates = []
    seen = set()
    for link in soup.select("a[href]"):
        label = norm(link.get_text(" "))
        href = canonical_url(urljoin(base_url, link.get("href", "")))
        if not href or href in seen or not is_http_url(href) or not same_pennish_domain(href):
            continue
        haystack = f"{label} {href}"
        if pattern_hits(haystack, ROSTER_PATTERNS + CONTEXT_PATTERNS):
            seen.add(href)
            candidates.append((label, href))
    return candidates[:25]


def parser_supported_structure(
    row: sqlite3.Row,
    soup: BeautifulSoup,
    url: str,
    allow_heading_name_list: bool,
) -> tuple[int, list[str]]:
    if not soup:
        return 0, []
    candidate = {
        "candidate_key": "",
        "official_program_key": row["official_program_key"],
        "priority": 0,
        "confidence": 0.0,
        "candidate_title": "",
        "candidate_url": url,
        "department": row["department"],
        "program_name": row["program_name"],
        "program_type": row["program_type"],
        "coverage_status": row["coverage_status"],
    }
    extractors = [
        ("bio_component", extract_bio_cards),
        ("profile_component", extract_profiles),
        ("accordion_header", extract_accordion_headers),
        ("neurology_archive_card", extract_neurology_archive_cards),
        ("pathology_current_resident_accordion", extract_pathology_current_residents),
        ("pathology_people_accordion", extract_pathology_people_accordion),
        ("obgyn_current_fellows", extract_obgyn_current_fellows),
    ]
    if allow_heading_name_list:
        extractors.append(("heading_name_list", extract_heading_name_lists))
    count = 0
    names = []
    for name, extractor in extractors:
        rows = extractor(soup, candidate, "probe_supported_structure", url)
        if rows:
            names.append(name)
            count += len(rows)
    return count, names


def make_candidate(
    row: sqlite3.Row,
    source_role: str,
    url: str,
    page: dict,
    label: str = "",
    supported_structure_count: int = 0,
    supported_structure_types: list[str] | None = None,
) -> dict:
    title = label or page.get("title", "")
    status, confidence, reasons = classify_candidate(title, url, source_role)
    strong_roster_cues = pattern_hits(f"{title} {url}", STRONG_ROSTER_CUE_PATTERNS)
    supported_structure_types = supported_structure_types or []
    if page.get("roster_term_count", 0) and strong_roster_cues:
        confidence = min(round(confidence + 0.1, 3), 0.95)
        reasons = sorted(set(reasons + ["page_roster_terms"]))
        if status != "low_value_candidate":
            status = "roster_source_candidate"
    elif page.get("roster_term_count", 0):
        reasons = sorted(set(reasons + ["weak_body_roster_language"]))
    if supported_structure_count:
        confidence = min(round(confidence + 0.22, 3), 0.95)
        reasons = sorted(set(reasons + ["supported_person_structure"]))
        if status != "unreachable_or_error":
            status = "roster_source_candidate"
    if page.get("http_status") and int(page["http_status"]) >= 400:
        confidence = min(confidence, 0.2)
        status = "unreachable_or_error"
        reasons = sorted(set(reasons + ["http_error"]))
    if page.get("error"):
        confidence = min(confidence, 0.15)
        status = "unreachable_or_error"
        reasons = sorted(set(reasons + ["request_error"]))
    candidate_key = key_for("program_source_candidate", f"{row['official_program_key']}:{url}:{source_role}")
    return {
        "candidate_key": candidate_key,
        "official_program_key": row["official_program_key"],
        "sponsoring_institution": row["sponsoring_institution"],
        "department": row["department"],
        "program_type": row["program_type"],
        "program_name": row["program_name"],
        "coverage_status": row["coverage_status"],
        "source_role": source_role,
        "candidate_status": status,
        "candidate_url": url,
        "candidate_title": title,
        "http_status": page.get("http_status", 0),
        "content_type": page.get("content_type", ""),
        "fetched_at": page.get("fetched_at", ""),
        "sha256": page.get("sha256", ""),
        "text_length": page.get("text_length", 0),
        "roster_term_count": page.get("roster_term_count", 0),
        "context_term_count": page.get("context_term_count", 0),
        "supported_person_structure_count": supported_structure_count,
        "supported_person_structure_types": supported_structure_types,
        "confidence": confidence,
        "priority": priority(status, confidence, row["coverage_status"], source_role),
        "reasons": reasons,
        "error": page.get("error", ""),
    }


def make_search_candidate(row: dict) -> dict:
    page = {
        "url": row["result_url"],
        "title": row.get("result_title", ""),
        "http_status": row.get("search_http_status", ""),
        "content_type": "",
        "text_length": 0,
        "roster_term_count": 0,
        "context_term_count": 0,
    }
    official_row = {
        "official_program_key": row["official_program_key"],
        "sponsoring_institution": "Hospital of the University of Pennsylvania",
        "department": row["department"],
        "program_type": row["program_type"],
        "program_name": row["program_name"],
        "coverage_status": row["coverage_status"],
    }
    status, confidence, reasons = classify_candidate(
        f"{row.get('result_title', '')} {row.get('result_snippet', '')}",
        row["result_url"],
        "search_result",
    )
    if same_pennish_domain(row["result_url"]):
        confidence = min(round(confidence + 0.08, 3), 0.95)
        reasons = sorted(set(reasons + ["pennish_search_result_domain"]))
    if row.get("result_rank") and int(row["result_rank"]) <= 2:
        confidence = min(round(confidence + 0.03, 3), 0.95)
        reasons = sorted(set(reasons + ["top_search_result"]))
    if status == "low_value_candidate" and same_pennish_domain(row["result_url"]):
        status = "program_context_candidate"
    candidate_key = key_for(
        "program_source_candidate",
        f"{row['official_program_key']}:{row['result_url']}:search_result:{row['query_key']}",
    )
    return {
        "candidate_key": candidate_key,
        "official_program_key": official_row["official_program_key"],
        "sponsoring_institution": official_row["sponsoring_institution"],
        "department": official_row["department"],
        "program_type": official_row["program_type"],
        "program_name": official_row["program_name"],
        "coverage_status": official_row["coverage_status"],
        "source_role": "search_result",
        "candidate_status": status,
        "candidate_url": row["result_url"],
        "candidate_title": row.get("result_title", ""),
        "http_status": page["http_status"],
        "content_type": "",
        "fetched_at": row.get("searched_at", ""),
        "sha256": "",
        "text_length": 0,
        "roster_term_count": 0,
        "context_term_count": 0,
        "supported_person_structure_count": 0,
        "supported_person_structure_types": [],
        "confidence": confidence,
        "priority": priority(status, confidence, row["coverage_status"], "linked_candidate"),
        "reasons": sorted(set(reasons + ["gap_search_result", f"query_kind:{row['query_kind']}"])),
        "error": "",
        "query_key": row["query_key"],
        "query": row["query"],
        "result_rank": row["result_rank"],
        "result_snippet": row.get("result_snippet", ""),
    }


def priority(status: str, confidence: float, coverage_status: str, source_role: str) -> int:
    score = int(round(confidence * 100))
    if status == "roster_source_candidate":
        score += 40
    if source_role == "linked_candidate" and status == "roster_source_candidate":
        score += 20
    if coverage_status == "not_discovered":
        score += 10
    if source_role == "official_program_url":
        score += 5
    if source_role == "official_program_url" and status == "roster_source_candidate":
        score -= 10
    if status == "unreachable_or_error":
        score -= 50
    return max(0, min(score, 175))


def probe(args: argparse.Namespace) -> tuple[list[dict], list[dict], list[dict], list[dict], dict]:
    conn = sqlite3.connect(DB)
    rows = gap_rows(conn)
    conn.close()
    generated_at = datetime.now(timezone.utc).isoformat()
    search_specs = search_query_specs(
        search_rows_for_scope(rows, args.search_scope),
        generated_at,
        args.max_search_queries_per_program,
    )
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-gme-gap-source-probe/0.1"
    candidates = []
    probes = []
    search_observations = []
    fetched: dict[str, dict] = {}
    for row in rows:
        for source_role, url in source_urls_for_gap(row):
            if url not in fetched:
                fetched[url] = fetch_page(session, url)
            page = fetched[url]
            strong_roster_cues = bool(pattern_hits(f"{page.get('title', '')} {page.get('url') or url}", STRONG_ROSTER_CUE_PATTERNS))
            allow_heading_name_list = strong_roster_cues or int(page.get("roster_term_count") or 0) >= 2
            supported_count, supported_types = parser_supported_structure(
                row,
                page["soup"],
                page.get("url") or url,
                allow_heading_name_list=allow_heading_name_list,
            )
            probes.append(
                {
                    "official_program_key": row["official_program_key"],
                    "program_name": row["program_name"],
                    "coverage_status": row["coverage_status"],
                    "source_role": source_role,
                    "requested_url": url,
                    "effective_url": page.get("url", url),
                    "http_status": page.get("http_status", 0),
                    "title": page.get("title", ""),
                    "content_type": page.get("content_type", ""),
                    "text_length": page.get("text_length", 0),
                    "roster_term_count": page.get("roster_term_count", 0),
                    "context_term_count": page.get("context_term_count", 0),
                    "supported_person_structure_count": supported_count,
                    "supported_person_structure_types": supported_types,
                    "heading_name_list_support_allowed": int(allow_heading_name_list),
                    "sha256": page.get("sha256", ""),
                    "fetched_at": page.get("fetched_at", ""),
                    "error": page.get("error", ""),
                }
            )
            candidates.append(
                make_candidate(
                    row,
                    source_role,
                    page.get("url") or url,
                    page,
                    supported_structure_count=supported_count,
                    supported_structure_types=supported_types,
                )
            )
            for label, href in link_candidates(page["soup"], page.get("url") or url):
                link_page = {
                    "url": href,
                    "requested_url": href,
                    "fetched_at": page.get("fetched_at", ""),
                    "http_status": "",
                    "content_type": "",
                    "sha256": "",
                    "title": label,
                    "text_length": 0,
                    "roster_term_count": 0,
                    "context_term_count": 0,
                }
                candidates.append(make_candidate(row, "linked_candidate", href, link_page, label=label))
    if args.search:
        search_candidate_rows = []
        for spec in search_specs:
            results, observation = search_results(session, spec, args.max_search_results, args.search_timeout)
            search_observations.append(observation)
            for result in results:
                candidate = make_search_candidate(result)
                candidates.append(candidate)
                search_candidate_rows.append(candidate)
            if args.sleep:
                time.sleep(args.sleep)
    else:
        search_observations = []
    unique_candidates = {}
    for candidate in candidates:
        current = unique_candidates.get(candidate["candidate_key"])
        if not current or candidate["priority"] > current["priority"]:
            unique_candidates[candidate["candidate_key"]] = candidate
    candidates = sorted(
        unique_candidates.values(),
        key=lambda item: (-int(item["priority"]), item["department"], item["program_name"], item["candidate_url"]),
    )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gap_programs": len(rows),
        "source_pages_probed": len(fetched),
        "search_scope": args.search_scope,
        "search_enabled": bool(args.search),
        "search_query_rows": len(search_specs),
        "search_observation_rows": len(search_observations),
        "candidate_urls": len(candidates),
        "by_candidate_status": dict(Counter(row["candidate_status"] for row in candidates)),
        "by_coverage_status": dict(Counter(row["coverage_status"] for row in candidates)),
        "by_source_role": dict(Counter(row["source_role"] for row in candidates)),
        "by_search_error": dict(Counter(row.get("error", "") for row in search_observations if row.get("error"))),
        "by_search_http_status": dict(Counter(str(row.get("search_http_status", "")) for row in search_observations)),
        "top_roster_candidates": [
            {
                "program_name": row["program_name"],
                "department": row["department"],
                "candidate_url": row["candidate_url"],
                "candidate_title": row["candidate_title"],
                "priority": row["priority"],
                "confidence": row["confidence"],
                "supported_person_structure_count": row["supported_person_structure_count"],
                "supported_person_structure_types": row["supported_person_structure_types"],
            }
            for row in candidates
            if row["candidate_status"] == "roster_source_candidate"
        ][:25],
    }
    return candidates, probes, search_specs, search_observations, summary


def write_outputs(
    candidates: list[dict],
    probes: list[dict],
    search_specs: list[dict],
    search_observations: list[dict],
    summary: dict,
) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "penn_gme_gap_source_candidates.json").write_text(
        json.dumps(candidates, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "penn_gme_gap_source_probes.json").write_text(
        json.dumps(probes, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "penn_gme_gap_source_probe_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_csv(
        SEARCH_QUERY_CSV,
        search_specs,
        [
            "query_key",
            "official_program_key",
            "department",
            "program_type",
            "program_name",
            "coverage_status",
            "query_kind",
            "query",
            "query_url",
            "priority",
            "generated_at",
        ],
    )
    write_csv(
        SEARCH_OBSERVATION_CSV,
        search_observations,
        [
            "observation_key",
            "query_key",
            "official_program_key",
            "department",
            "program_type",
            "program_name",
            "coverage_status",
            "query_kind",
            "query",
            "searched_at",
            "search_http_status",
            "result_count",
            "error",
        ],
    )
    fields = [
        "candidate_key",
        "official_program_key",
        "department",
        "program_type",
        "program_name",
        "coverage_status",
        "source_role",
        "candidate_status",
        "priority",
        "confidence",
        "candidate_title",
        "candidate_url",
        "http_status",
        "roster_term_count",
        "context_term_count",
        "supported_person_structure_count",
        "supported_person_structure_types",
        "reasons",
        "error",
    ]
    with (ARTIFACTS / "penn_gme_gap_source_candidates.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in candidates:
            out = {field: row.get(field, "") for field in fields}
            out["reasons"] = ";".join(row.get("reasons", []))
            out["supported_person_structure_types"] = ";".join(row.get("supported_person_structure_types", []))
            writer.writerow(out)


def ensure_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def ensure_sqlite_columns(conn: sqlite3.Connection) -> None:
    ensure_column(conn, "official_program_source_probes", "supported_person_structure_count", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "official_program_source_probes", "supported_person_structure_types", "TEXT")
    ensure_column(conn, "official_program_source_probes", "heading_name_list_support_allowed", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "official_program_source_candidates", "supported_person_structure_count", "INTEGER NOT NULL DEFAULT 0")
    ensure_column(conn, "official_program_source_candidates", "supported_person_structure_types", "TEXT")


def write_sqlite(
    candidates: list[dict],
    probes: list[dict],
    search_specs: list[dict],
    search_observations: list[dict],
) -> None:
    if not DB.exists():
        return
    conn = sqlite3.connect(DB)
    with conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        ensure_sqlite_columns(conn)
        conn.execute("DELETE FROM official_program_source_candidates")
        conn.execute("DELETE FROM official_program_source_probes")
        conn.execute("DELETE FROM official_program_source_search_queries")
        conn.execute("DELETE FROM official_program_source_search_observations")
        for row in search_specs:
            conn.execute(
                """
                INSERT OR REPLACE INTO official_program_source_search_queries
                (query_key, official_program_key, department, program_type, program_name,
                 coverage_status, query_kind, query, query_url, priority, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["query_key"],
                    row["official_program_key"],
                    row.get("department"),
                    row.get("program_type"),
                    row.get("program_name"),
                    row.get("coverage_status"),
                    row["query_kind"],
                    row["query"],
                    row["query_url"],
                    int(row.get("priority") or 0),
                    row["generated_at"],
                ),
            )
        for row in search_observations:
            conn.execute(
                """
                INSERT OR REPLACE INTO official_program_source_search_observations
                (observation_key, query_key, official_program_key, department, program_type,
                 program_name, coverage_status, query_kind, query, searched_at,
                 search_http_status, result_count, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["observation_key"],
                    row["query_key"],
                    row["official_program_key"],
                    row.get("department"),
                    row.get("program_type"),
                    row.get("program_name"),
                    row.get("coverage_status"),
                    row["query_kind"],
                    row["query"],
                    row["searched_at"],
                    row.get("search_http_status"),
                    int(row.get("result_count") or 0),
                    row.get("error", ""),
                ),
            )
        for row in probes:
            conn.execute(
                """
                INSERT INTO official_program_source_probes
                (official_program_key, program_name, coverage_status, source_role,
                 requested_url, effective_url, http_status, title, content_type,
                 text_length, roster_term_count, context_term_count,
                 supported_person_structure_count, supported_person_structure_types,
                 heading_name_list_support_allowed, sha256, fetched_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["official_program_key"],
                    row["program_name"],
                    row["coverage_status"],
                    row["source_role"],
                    row["requested_url"],
                    row["effective_url"],
                    row["http_status"],
                    row["title"],
                    row["content_type"],
                    row["text_length"],
                    row["roster_term_count"],
                    row["context_term_count"],
                    row.get("supported_person_structure_count", 0),
                    dumps(row.get("supported_person_structure_types", [])),
                    row.get("heading_name_list_support_allowed", 0),
                    row["sha256"],
                    row["fetched_at"],
                    row["error"],
                ),
            )
        for row in candidates:
            conn.execute(
                """
                INSERT OR REPLACE INTO official_program_source_candidates
                (candidate_key, official_program_key, department, program_type,
                 program_name, coverage_status, source_role, candidate_status,
                 priority, confidence, candidate_title, candidate_url, http_status,
                 roster_term_count, context_term_count, supported_person_structure_count,
                 supported_person_structure_types, reasons_json, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["candidate_key"],
                    row["official_program_key"],
                    row["department"],
                    row["program_type"],
                    row["program_name"],
                    row["coverage_status"],
                    row["source_role"],
                    row["candidate_status"],
                    row["priority"],
                    row["confidence"],
                    row["candidate_title"],
                    row["candidate_url"],
                    row["http_status"] if row["http_status"] != "" else None,
                    row["roster_term_count"],
                    row["context_term_count"],
                    row.get("supported_person_structure_count", 0),
                    dumps(row.get("supported_person_structure_types", [])),
                    dumps(row.get("reasons", [])),
                    dumps(row),
                ),
            )
    conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", action="store_true", help="Execute opt-in DuckDuckGo HTML searches for gap programs.")
    parser.add_argument(
        "--search-scope",
        choices=["not_discovered", "discovered_no_current_roster", "all_gaps"],
        default="not_discovered",
    )
    parser.add_argument("--max-search-queries-per-program", type=int, default=3)
    parser.add_argument("--max-search-results", type=int, default=4)
    parser.add_argument("--search-timeout", type=float, default=8.0)
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()
    candidates, probes, search_specs, search_observations, summary = probe(args)
    write_outputs(candidates, probes, search_specs, search_observations, summary)
    write_sqlite(candidates, probes, search_specs, search_observations)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
