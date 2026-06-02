#!/usr/bin/env python3
"""Probe official HUP GME coverage gaps for likely roster source URLs."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

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
SCHEMA = ROOT / "db" / "schema.sql"

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


def canonical_url(url: str) -> str:
    if not url:
        return ""
    clean, _fragment = urldefrag(url)
    return clean.rstrip("/")


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


def make_candidate(row: sqlite3.Row, source_role: str, url: str, page: dict, label: str = "") -> dict:
    title = label or page.get("title", "")
    status, confidence, reasons = classify_candidate(title, url, source_role)
    strong_roster_cues = pattern_hits(f"{title} {url}", STRONG_ROSTER_CUE_PATTERNS)
    if page.get("roster_term_count", 0) and strong_roster_cues:
        confidence = min(round(confidence + 0.1, 3), 0.95)
        reasons = sorted(set(reasons + ["page_roster_terms"]))
        if status != "low_value_candidate":
            status = "roster_source_candidate"
    elif page.get("roster_term_count", 0):
        reasons = sorted(set(reasons + ["weak_body_roster_language"]))
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
        "confidence": confidence,
        "priority": priority(status, confidence, row["coverage_status"], source_role),
        "reasons": reasons,
        "error": page.get("error", ""),
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


def probe() -> tuple[list[dict], list[dict], dict]:
    conn = sqlite3.connect(DB)
    rows = gap_rows(conn)
    conn.close()
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-gme-gap-source-probe/0.1"
    candidates = []
    probes = []
    fetched: dict[str, dict] = {}
    for row in rows:
        for source_role, url in source_urls_for_gap(row):
            if url not in fetched:
                fetched[url] = fetch_page(session, url)
            page = fetched[url]
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
                    "sha256": page.get("sha256", ""),
                    "fetched_at": page.get("fetched_at", ""),
                    "error": page.get("error", ""),
                }
            )
            candidates.append(make_candidate(row, source_role, page.get("url") or url, page))
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
        "candidate_urls": len(candidates),
        "by_candidate_status": dict(Counter(row["candidate_status"] for row in candidates)),
        "by_coverage_status": dict(Counter(row["coverage_status"] for row in candidates)),
        "top_roster_candidates": [
            {
                "program_name": row["program_name"],
                "department": row["department"],
                "candidate_url": row["candidate_url"],
                "candidate_title": row["candidate_title"],
                "priority": row["priority"],
                "confidence": row["confidence"],
            }
            for row in candidates
            if row["candidate_status"] == "roster_source_candidate"
        ][:25],
    }
    return candidates, probes, summary


def write_outputs(candidates: list[dict], probes: list[dict], summary: dict) -> None:
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
        "reasons",
        "error",
    ]
    with (ARTIFACTS / "penn_gme_gap_source_candidates.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in candidates:
            out = {field: row.get(field, "") for field in fields}
            out["reasons"] = ";".join(row.get("reasons", []))
            writer.writerow(out)


def write_sqlite(candidates: list[dict], probes: list[dict]) -> None:
    if not DB.exists():
        return
    conn = sqlite3.connect(DB)
    with conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("DELETE FROM official_program_source_candidates")
        conn.execute("DELETE FROM official_program_source_probes")
        for row in probes:
            conn.execute(
                """
                INSERT INTO official_program_source_probes
                (official_program_key, program_name, coverage_status, source_role,
                 requested_url, effective_url, http_status, title, content_type,
                 text_length, roster_term_count, context_term_count, sha256,
                 fetched_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                 roster_term_count, context_term_count, reasons_json, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    dumps(row.get("reasons", [])),
                    dumps(row),
                ),
            )
    conn.close()


def main() -> None:
    candidates, probes, summary = probe()
    write_outputs(candidates, probes, summary)
    write_sqlite(candidates, probes)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
