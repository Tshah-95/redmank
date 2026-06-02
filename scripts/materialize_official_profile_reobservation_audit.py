#!/usr/bin/env python3
"""Fetch current official profile candidates and audit whether identity context persists."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "official_profile_reobservation_audit.csv"
JSON_PATH = ARTIFACTS / "official_profile_reobservation_audit.json"
SUMMARY_PATH = ARTIFACTS / "official_profile_reobservation_summary.json"

USER_AGENT = "PennTrainingCorpus/0.1 (+public academic roster research; contact: local research agent)"
TIMEOUT_SECONDS = 30
OFFICIAL_DOMAINS = {"www3.pennmedicine.org", "www.pennmedicine.org", "www.med.upenn.edu", "med.upenn.edu"}
ROLE_TERMS = {"fellow", "fellowship", "resident", "residency", "training", "education"}
DEGREE_AND_SUFFIX_TOKENS = {
    "md",
    "do",
    "mbbs",
    "phd",
    "mph",
    "ms",
    "msc",
    "msce",
    "mhs",
    "mba",
    "dr",
    "jr",
    "sr",
}
PROGRAM_STOPWORDS = {
    "and",
    "of",
    "the",
    "in",
    "program",
    "fellowship",
    "residency",
    "resident",
    "residents",
    "fellows",
    "training",
    "education",
}

FIELDNAMES = [
    "profile_reobservation_key",
    "profile_workbench_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "candidate_url",
    "candidate_domain",
    "fetch_status",
    "http_status",
    "source_hash",
    "title",
    "canonical_url",
    "name_present",
    "program_context_present",
    "role_or_training_context_present",
    "official_domain_confirmed",
    "profile_path_confirmed",
    "reobservation_status",
    "evidence_strength",
    "match_context",
    "reobserved_at",
    "evidence_json",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def normalized_tokens(value: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", (value or "").lower())
    return [token for token in tokens if token not in DEGREE_AND_SUFFIX_TOKENS]


def core_name_tokens(display_name: str) -> list[str]:
    return [token for token in normalized_tokens(display_name) if len(token) > 1]


def program_tokens(program_name: str) -> list[str]:
    return [
        token
        for token in normalized_tokens(program_name)
        if token not in PROGRAM_STOPWORDS and len(token) > 2
    ]


def html_title(text: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", text or "", flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return " ".join(html.unescape(match.group(1)).split())[:300]


def canonical_url(text: str) -> str:
    match = re.search(
        r'<link[^>]+rel=["\\\']canonical["\\\'][^>]+href=["\\\']([^"\\\']+)["\\\']',
        text or "",
        flags=re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r'<link[^>]+href=["\\\']([^"\\\']+)["\\\'][^>]+rel=["\\\']canonical["\\\']',
            text or "",
            flags=re.IGNORECASE,
        )
    return html.unescape(match.group(1)).strip()[:500] if match else ""


def fetch_url(url: str) -> dict:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            content = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
        return {
            "fetch_status": "fetched",
            "http_status": response.status,
            "content": content,
            "text": content.decode(charset, errors="replace"),
            "source_hash": sha256_bytes(content),
            "error": "",
        }
    except HTTPError as exc:
        content = exc.read()
        return {
            "fetch_status": "http_error",
            "http_status": exc.code,
            "content": content,
            "text": content.decode("utf-8", errors="replace"),
            "source_hash": sha256_bytes(content) if content else "",
            "error": str(exc),
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "fetch_status": "fetch_error",
            "http_status": "",
            "content": b"",
            "text": "",
            "source_hash": "",
            "error": str(exc),
        }


def read_queue(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM official_profile_reviewer_decision_queue
            ORDER BY role, program_name, display_name, profile_workbench_key
            """
        )
    ]


def match_context(source_text: str, tokens: list[str], window: int = 120) -> str:
    text = html.unescape(source_text or "")
    lower = text.lower()
    indices = [lower.find(token) for token in tokens if token and lower.find(token) >= 0]
    if not indices:
        return ""
    index = min(indices)
    start = max(0, index - window)
    end = min(len(text), index + window)
    snippet = " ".join(text[start:end].split())
    return snippet[:500]


def classify(row: dict, fetch: dict, reobserved_at: str) -> dict:
    parsed = urlparse(row.get("candidate_url") or "")
    domain = (row.get("candidate_domain") or parsed.netloc or "").lower()
    page_ok = fetch["fetch_status"] == "fetched" and int(fetch.get("http_status") or 0) == 200
    text = html.unescape(fetch.get("text") or "")
    lower = text.lower()
    path = parsed.path.lower()
    title = html_title(text)
    canonical = canonical_url(text)
    name_tokens = core_name_tokens(row.get("display_name") or "")
    program_terms = program_tokens(row.get("program_name") or "")
    name_present = bool(page_ok and name_tokens and all(token in lower for token in name_tokens[:3]))
    program_context_present = bool(page_ok and program_terms and any(token in lower or token in path for token in program_terms))
    role_context_present = bool(page_ok and any(term in lower or term in path for term in ROLE_TERMS))
    official_domain = domain in OFFICIAL_DOMAINS or domain.endswith(".pennmedicine.org") or domain.endswith(".upenn.edu")
    profile_path = any(part in path for part in ("/fellows/", "/residents/", "/faculty/", "/people/"))

    generic_canonical = bool(
        page_ok
        and canonical
        and canonical.rstrip("/") != (row.get("candidate_url") or "").rstrip("/")
        and ("academic-departments" in canonical or "_site_psom" in canonical.lower())
    )

    if not page_ok:
        status = "source_fetch_failed_or_non_200"
        strength = 0
    elif generic_canonical and not name_present:
        status = "fresh_source_resolved_to_generic_academic_departments_page"
        strength = 1
    elif official_domain and name_present and role_context_present and (program_context_present or profile_path):
        status = "fresh_official_profile_context_reobserved"
        strength = 4
    elif official_domain and name_present:
        status = "fresh_official_profile_identity_reobserved_context_review"
        strength = 3
    elif official_domain:
        status = "fresh_official_profile_identity_not_reobserved"
        strength = 1
    else:
        status = "non_official_profile_candidate_review"
        strength = 0

    evidence = {
        "source_fetch": {
            "candidate_url": row.get("candidate_url") or "",
            "candidate_domain": domain,
            "fetch_status": fetch.get("fetch_status") or "",
            "http_status": fetch.get("http_status") or "",
            "source_hash": fetch.get("source_hash") or "",
            "error": fetch.get("error") or "",
            "reobserved_at": reobserved_at,
        },
        "profile_context_check": {
            "display_name": row.get("display_name") or "",
            "name_tokens_checked": name_tokens,
            "program_terms_checked": program_terms,
            "name_present": name_present,
            "program_context_present": program_context_present,
            "role_or_training_context_present": role_context_present,
            "official_domain_confirmed": official_domain,
            "profile_path_confirmed": profile_path,
        },
        "policy": {
            "non_mutating": True,
            "reviewer_decision_still_required": True,
            "accepted_profile_url_fact_requires": [
                "same-person identity confirmation",
                "official source ownership confirmation",
                "profile context confirmation",
                "source hash confirmation",
                "display-safety confirmation",
            ],
        },
    }
    key_basis = {
        "profile_workbench_key": row["profile_workbench_key"],
        "candidate_url": row.get("candidate_url") or "",
        "source_hash": fetch.get("source_hash") or "",
        "reobservation_status": status,
    }
    output = {
        "profile_reobservation_key": "official_profile_reobservation_" + sha256_text(dumps(key_basis))[:20],
        "profile_workbench_key": row["profile_workbench_key"],
        "person_key": row.get("person_key") or "",
        "display_name": row.get("display_name") or "",
        "role": row.get("role") or "",
        "program_name": row.get("program_name") or "",
        "candidate_url": row.get("candidate_url") or "",
        "candidate_domain": domain,
        "fetch_status": fetch.get("fetch_status") or "",
        "http_status": fetch.get("http_status") or "",
        "source_hash": fetch.get("source_hash") or "",
        "title": title,
        "canonical_url": canonical,
        "name_present": 1 if name_present else 0,
        "program_context_present": 1 if program_context_present else 0,
        "role_or_training_context_present": 1 if role_context_present else 0,
        "official_domain_confirmed": 1 if official_domain else 0,
        "profile_path_confirmed": 1 if profile_path else 0,
        "reobservation_status": status,
        "evidence_strength": strength,
        "match_context": match_context(text, name_tokens + program_terms),
        "reobserved_at": reobserved_at,
        "evidence_json": dumps(evidence),
    }
    return {field: output[field] for field in FIELDNAMES}


def write_csv(rows: list[dict]) -> None:
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_json(rows: list[dict]) -> None:
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    columns = {row[1] for row in conn.execute("PRAGMA table_info(official_profile_reobservation_audit)")}
    if "canonical_url" not in columns:
        conn.execute("ALTER TABLE official_profile_reobservation_audit ADD COLUMN canonical_url TEXT")
    conn.execute("DELETE FROM official_profile_reobservation_audit")
    if not rows:
        return
    fields = ", ".join(FIELDNAMES)
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if db_row.get("http_status") == "":
            db_row["http_status"] = None
        db_rows.append(db_row)
    conn.executemany(
        f"INSERT OR REPLACE INTO official_profile_reobservation_audit ({fields}) VALUES ({placeholders})",
        db_rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    from collections import Counter

    by_status = Counter(row["reobservation_status"] for row in rows)
    by_role = Counter(row["role"] for row in rows)
    by_fetch = Counter(row["fetch_status"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "reobservation_rows": len(rows),
        "unique_candidate_url_count": len({row["candidate_url"] for row in rows}),
        "fresh_profile_context_rows": by_status.get("fresh_official_profile_context_reobserved", 0),
        "identity_context_review_rows": by_status.get("fresh_official_profile_identity_reobserved_context_review", 0),
        "identity_not_reobserved_rows": by_status.get("fresh_official_profile_identity_not_reobserved", 0),
        "generic_page_resolution_rows": by_status.get("fresh_source_resolved_to_generic_academic_departments_page", 0),
        "source_fetch_problem_rows": by_status.get("source_fetch_failed_or_non_200", 0),
        "by_reobservation_status": dict(sorted(by_status.items())),
        "by_role": dict(sorted(by_role.items())),
        "by_fetch_status": dict(sorted(by_fetch.items())),
        "policy": (
            "Official profile reobservation is non-mutating. It records current source hash and context checks; "
            "accepted profile URL facts still require explicit reviewer acceptance."
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
    fetched = {row["candidate_url"]: fetch_url(row["candidate_url"]) for row in queue if row.get("candidate_url")}
    rows = [classify(row, fetched[row["candidate_url"]], generated_at) for row in queue if row.get("candidate_url")]
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(rows)
    write_json(rows)
    write_summary(rows, generated_at)
    print(dumps({"official_profile_reobservation_rows": len(rows), "unique_candidate_url_count": len(fetched)}))


if __name__ == "__main__":
    main()
