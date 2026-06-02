#!/usr/bin/env python3
"""Fetch current public contact source pages and audit whether values persist."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "contact_reobservation_audit.csv"
JSON_PATH = ARTIFACTS / "contact_reobservation_audit.json"
SUMMARY_PATH = ARTIFACTS / "contact_reobservation_summary.json"

USER_AGENT = "PennTrainingCorpus/0.1 (+public academic roster research; contact: local research agent)"
TIMEOUT_SECONDS = 30

FIELDNAMES = [
    "contact_reobservation_key",
    "contact_contract_key",
    "contact_assurance_key",
    "contact_key",
    "person_key",
    "display_name",
    "role",
    "contact_type",
    "normalized_contact_value",
    "contact_domain",
    "canonical_contact_domain",
    "domain_status",
    "source_url",
    "fetch_status",
    "http_status",
    "source_hash",
    "reobserved_same_value",
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


def read_contracts(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM contact_verification_contracts
            ORDER BY source_url, display_name, normalized_contact_value, contact_contract_key
            """
        )
    ]


def fetch_sources(urls: list[str]) -> dict[str, dict]:
    fetched = {}
    for url in urls:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                content = response.read()
                charset = response.headers.get_content_charset() or "utf-8"
            fetched[url] = {
                "fetch_status": "fetched",
                "http_status": response.status,
                "content": content,
                "text": content.decode(charset, errors="replace"),
                "source_hash": sha256_bytes(content),
                "error": "",
            }
        except HTTPError as exc:
            content = exc.read()
            fetched[url] = {
                "fetch_status": "http_error",
                "http_status": exc.code,
                "content": content,
                "text": content.decode("utf-8", errors="replace"),
                "source_hash": sha256_bytes(content) if content else "",
                "error": str(exc),
            }
        except (URLError, TimeoutError, OSError) as exc:
            fetched[url] = {
                "fetch_status": "fetch_error",
                "http_status": "",
                "content": b"",
                "text": "",
                "source_hash": "",
                "error": str(exc),
            }
    return fetched


def match_context(source_text: str, needle: str, window: int = 80) -> str:
    haystack = html.unescape(source_text or "")
    lower = haystack.lower()
    target = (needle or "").lower()
    index = lower.find(target)
    if index < 0:
        return ""
    start = max(0, index - window)
    end = min(len(haystack), index + len(needle) + window)
    snippet = " ".join(haystack[start:end].split())
    return snippet[:400]


def classify(row: dict, fetch: dict, reobserved_at: str) -> dict:
    normalized_value = row.get("normalized_contact_value") or ""
    status = fetch["fetch_status"]
    http_status = fetch.get("http_status") or ""
    source_text = html.unescape(fetch.get("text") or "")
    source_lower = source_text.lower()
    value_lower = normalized_value.lower()
    page_ok = status == "fetched" and int(http_status or 0) == 200
    same_value = bool(page_ok and value_lower and value_lower in source_lower)

    if not page_ok:
        reobservation_status = "source_fetch_failed_or_non_200"
        evidence_strength = 0
    elif same_value and row.get("domain_status") == "institutional_domain":
        reobservation_status = "fresh_official_same_value_reobserved"
        evidence_strength = 3
    elif same_value:
        reobservation_status = "same_value_reobserved_domain_review_required"
        evidence_strength = 2
    else:
        reobservation_status = "fresh_official_value_absent"
        evidence_strength = 1

    parsed = urlparse(row.get("source_url") or "")
    evidence = {
        "source_fetch": {
            "source_url": row.get("source_url") or "",
            "source_domain": parsed.netloc,
            "fetch_status": status,
            "http_status": http_status,
            "source_hash": fetch.get("source_hash") or "",
            "error": fetch.get("error") or "",
            "reobserved_at": reobserved_at,
        },
        "contact_check": {
            "normalized_contact_value": normalized_value,
            "same_value_present_in_current_source": same_value,
            "domain_status": row.get("domain_status") or "",
            "canonical_contact_domain": row.get("canonical_contact_domain") or "",
        },
        "policy": {
            "non_mutating": True,
            "reviewer_decision_still_required": True,
            "accepted_contact_fact_requires": [
                "same-person identity confirmation",
                "current official source confirmation",
                "same value confirmation",
                "institutional domain confirmation",
                "person-specific scope confirmation",
            ],
        },
    }
    key_basis = {
        "contact_contract_key": row["contact_contract_key"],
        "source_hash": fetch.get("source_hash") or "",
        "same_value": same_value,
        "reobservation_status": reobservation_status,
    }
    output = {
        "contact_reobservation_key": "contact_reobservation_" + sha256_text(dumps(key_basis))[:20],
        "contact_contract_key": row["contact_contract_key"],
        "contact_assurance_key": row.get("contact_assurance_key") or "",
        "contact_key": row.get("contact_key") or "",
        "person_key": row.get("person_key") or "",
        "display_name": row.get("display_name") or "",
        "role": row.get("role") or "",
        "contact_type": row.get("contact_type") or "",
        "normalized_contact_value": normalized_value,
        "contact_domain": row.get("contact_domain") or "",
        "canonical_contact_domain": row.get("canonical_contact_domain") or "",
        "domain_status": row.get("domain_status") or "",
        "source_url": row.get("source_url") or "",
        "fetch_status": status,
        "http_status": http_status,
        "source_hash": fetch.get("source_hash") or "",
        "reobserved_same_value": 1 if same_value else 0,
        "reobservation_status": reobservation_status,
        "evidence_strength": evidence_strength,
        "match_context": match_context(source_text, normalized_value),
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
    conn.execute("DELETE FROM contact_reobservation_audit")
    if not rows:
        return
    fields = ", ".join(FIELDNAMES)
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if not db_row.get("person_key"):
            db_row["person_key"] = None
        if db_row.get("http_status") == "":
            db_row["http_status"] = None
        db_rows.append(db_row)
    conn.executemany(
        f"INSERT OR REPLACE INTO contact_reobservation_audit ({fields}) VALUES ({placeholders})",
        db_rows,
    )


def write_summary(rows: list[dict], source_count: int, generated_at: str) -> None:
    from collections import Counter

    by_status = Counter(row["reobservation_status"] for row in rows)
    by_fetch = Counter(row["fetch_status"] for row in rows)
    by_domain = Counter(row["domain_status"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "reobservation_rows": len(rows),
        "unique_source_url_count": source_count,
        "fresh_same_value_rows": by_status.get("fresh_official_same_value_reobserved", 0),
        "same_value_domain_review_rows": by_status.get("same_value_reobserved_domain_review_required", 0),
        "value_absent_rows": by_status.get("fresh_official_value_absent", 0),
        "source_fetch_problem_rows": by_status.get("source_fetch_failed_or_non_200", 0),
        "by_reobservation_status": dict(sorted(by_status.items())),
        "by_fetch_status": dict(sorted(by_fetch.items())),
        "by_domain_status": dict(sorted(by_domain.items())),
        "policy": (
            "Contact reobservation is non-mutating. It records whether the current public source still contains "
            "the same contact value; verified contact facts still require explicit reviewer acceptance."
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
    contracts = read_contracts(conn)
    urls = sorted({row["source_url"] for row in contracts if row.get("source_url")})
    fetched = fetch_sources(urls)
    rows = [classify(row, fetched[row["source_url"]], generated_at) for row in contracts if row.get("source_url")]
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(rows)
    write_json(rows)
    write_summary(rows, len(urls), generated_at)
    print(dumps({"contact_reobservation_rows": len(rows), "unique_source_url_count": len(urls)}))


if __name__ == "__main__":
    main()
