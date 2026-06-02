#!/usr/bin/env python3
"""Audit public-source availability for Penn medical-student rosters."""

from __future__ import annotations

import argparse
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
from urllib.parse import urljoin


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

CSV_PATH = ARTIFACTS / "penn_med_student_source_audit.csv"
JSON_PATH = ARTIFACTS / "penn_med_student_source_audit.json"
SUMMARY_PATH = ARTIFACTS / "penn_med_student_source_audit_summary.json"

MSTP_DIRECTORY_URL = "https://www.med.upenn.edu/mstp/student-directory/"
MSTP_INDEX_URL = "https://www.med.upenn.edu/mstp/student-directories.html"
PSOM_DIRECTORY_URL = "https://www.med.upenn.edu/psom/directory.html"
MD_PROGRAM_URL = "https://my.med.upenn.edu/student/"
PROTECTED_MD_DIRECTORY_URL = "https://www.med.upenn.edu/apps/my/sms/studentdir/"

FIELDNAMES = [
    "audit_key",
    "source_url",
    "source_title",
    "source_scope",
    "access_status",
    "capture_status",
    "source_role",
    "observed_http_status",
    "effective_url",
    "public_person_count_observed",
    "loaded_person_count",
    "md_phd_signal_count",
    "current_student_signal_count",
    "directory_signal_count",
    "recommended_next_action",
    "confidence",
    "evidence_json",
    "audited_at",
]


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def audit_key(url: str, source_scope: str) -> str:
    digest = hashlib.sha1(f"{source_scope}:{url}".encode("utf-8")).hexdigest()[:16]
    return f"penn_med_student_source_{digest}"


def fetch(session: requests.Session, url: str) -> dict:
    try:
        response = session.get(url, timeout=30)
        text = response.text if "text/html" in response.headers.get("content-type", "") else ""
        soup = BeautifulSoup(text, "lxml") if text else BeautifulSoup("", "lxml")
        return {
            "url": url,
            "status": response.status_code,
            "effective_url": response.url,
            "content_type": response.headers.get("content-type", ""),
            "text": text,
            "soup": soup,
            "title": norm(soup.title.get_text(" ")) if soup.title else "",
            "error": "",
        }
    except requests.RequestException as exc:
        return {
            "url": url,
            "status": 0,
            "effective_url": "",
            "content_type": "",
            "text": "",
            "soup": BeautifulSoup("", "lxml"),
            "title": "",
            "error": f"{type(exc).__name__}: {str(exc)[:240]}",
        }


def loaded_mstp_count(conn: sqlite3.Connection) -> int:
    try:
        return int(
            conn.execute(
                """
                SELECT COUNT(DISTINCT p.person_key)
                FROM people p
                JOIN person_program_memberships m ON m.person_key = p.person_key
                WHERE p.role = 'medical_student'
                  AND m.source_key = 'perelman_mstp_student_directory'
                """
            ).fetchone()[0]
            or 0
        )
    except sqlite3.Error:
        return 0


def page_text(payload: dict) -> str:
    return norm(payload["soup"].get_text(" "))


def count_profile_cards(payload: dict) -> int:
    soup = payload["soup"]
    selectors = [
        "li.profile-card",
        ".profile-card",
        "article.profile",
        ".student-card",
    ]
    return max((len(soup.select(selector)) for selector in selectors), default=0)


def count_student_headings(payload: dict) -> int:
    soup = payload["soup"]
    names = []
    for heading in soup.find_all(["h2", "h3"]):
        text = norm(heading.get_text(" "))
        if re.fullmatch(r"[A-Z][A-Za-z' .-]+(?:\([^)]+\))?", text) and len(text.split()) >= 2:
            names.append(text)
    return len(set(names))


def signal_count(text: str, patterns: list[str]) -> int:
    lower = text.lower()
    return sum(lower.count(pattern.lower()) for pattern in patterns)


def row(
    payload: dict,
    source_scope: str,
    access_status: str,
    capture_status: str,
    source_role: str,
    recommended_next_action: str,
    confidence: float,
    loaded_count: int = 0,
    public_count: int | None = None,
    evidence_extra: dict | None = None,
) -> dict:
    text = page_text(payload)
    if public_count is None:
        public_count = max(count_profile_cards(payload), count_student_headings(payload))
    evidence = {
        "content_type": payload["content_type"],
        "sha256": sha256_text(payload["text"]) if payload["text"] else "",
        "error": payload["error"],
        "text_length": len(text),
        "profile_card_count": count_profile_cards(payload),
        "student_heading_count": count_student_headings(payload),
    }
    evidence.update(evidence_extra or {})
    return {
        "audit_key": audit_key(payload["url"], source_scope),
        "source_url": payload["url"],
        "source_title": payload["title"],
        "source_scope": source_scope,
        "access_status": access_status,
        "capture_status": capture_status,
        "source_role": source_role,
        "observed_http_status": payload["status"],
        "effective_url": payload["effective_url"],
        "public_person_count_observed": int(public_count or 0),
        "loaded_person_count": int(loaded_count or 0),
        "md_phd_signal_count": signal_count(text, ["MD/PhD", "MD-PhD", "MD PhD"]),
        "current_student_signal_count": signal_count(text, ["current students", "student directory", "students by year"]),
        "directory_signal_count": signal_count(text, ["directory", "directories", "studentdir"]),
        "recommended_next_action": recommended_next_action,
        "confidence": round(confidence, 3),
        "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
        "audited_at": "",
    }


def discover_directory_links(index_payload: dict) -> list[dict]:
    soup = index_payload["soup"]
    links = []
    for anchor in soup.select("a[href]"):
        text = norm(anchor.get_text(" "))
        href = urljoin(index_payload["url"], anchor["href"])
        if not text:
            continue
        text_low = text.lower()
        href_low = href.lower()
        if any(
            token in " ".join([text_low, href_low])
            for token in [
                "student-directory",
                "students_current",
                "current-students",
                "studentdir",
                "anthropology",
                "bioengineering",
                "biochemistry",
                "biostatistics",
                "cell and molecular biology",
                "genomics",
                "immunology",
                "neuroscience",
                "pharmacology",
                "hcmg",
                "health care management",
                "hss",
                "history and sociology",
            ]
        ):
            links.append({"label": text, "url": href})
    deduped = []
    seen = set()
    for link in links:
        if link["url"] in seen:
            continue
        seen.add(link["url"])
        deduped.append(link)
    return deduped


def classify_link(label: str, url: str) -> tuple[str, str]:
    label_low = label.lower()
    url_low = url.lower()
    if "apps/my/sms/studentdir" in url_low:
        return "md_student_directory", "protected_md_student_directory"
    if "mstp/student-directory" in url_low:
        return "md_phd_public_directory", "accepted_public_mstp_roster"
    graduate_labels = [
        "anthropology",
        "bioengineering",
        "biochemistry",
        "biostatistics",
        "cell and molecular biology",
        "genomics",
        "health care management",
        "history and sociology",
        "immunology",
        "neuroscience",
        "pharmacology",
    ]
    if (
        "student" in label_low
        or "current-students" in url_low
        or "students_current" in url_low
        or any(item in label_low for item in graduate_labels)
    ):
        return "graduate_directory_md_phd_filter", "public_md_phd_crosscheck_candidate"
    return "directory_context", "public_directory_context"


def protected_access(payload: dict) -> bool:
    effective = payload["effective_url"].lower()
    text = page_text(payload).lower()
    return "/apps/my/" in effective or "_preserve" in effective or "refresh automatically" in text


def canonical_url(url: str) -> str:
    return url.replace("http://www.med.upenn.edu/", "https://www.med.upenn.edu/")


def build_rows(conn: sqlite3.Connection, session: requests.Session) -> list[dict]:
    loaded_count = loaded_mstp_count(conn)
    rows = []
    index_payload = fetch(session, MSTP_INDEX_URL)
    links = discover_directory_links(index_payload)
    rows.append(
        row(
            index_payload,
            "student_directory_index",
            "public",
            "student_directory_index_with_protected_md_notice",
            "source_index",
            "use_index_to_monitor_whether_md_student_directory_becomes_public",
            0.9,
            public_count=0,
            evidence_extra={
                "directory_links": links,
                "protected_md_directory_notice": "Pennkey protected" in page_text(index_payload),
            },
        )
    )

    mstp_payload = fetch(session, MSTP_DIRECTORY_URL)
    rows.append(
        row(
            mstp_payload,
            "md_phd_public_directory",
            "public",
            "accepted_public_mstp_roster",
            "current_md_phd_students",
            "retain_as_partial_medical_student_truth_anchor_and_refresh_annually",
            0.92,
            loaded_count=loaded_count,
            public_count=count_profile_cards(mstp_payload),
        )
    )

    psom_payload = fetch(session, PSOM_DIRECTORY_URL)
    rows.append(
        row(
            psom_payload,
            "psom_directory_context",
            "public",
            "points_to_medical_student_directory_without_public_records",
            "directory_context",
            "probe_medical_student_directory_but_do_not_scrape_pennkey_content",
            0.86,
            public_count=0,
            evidence_extra={
                "medical_student_directory_link_seen": "Medical Student Directory" in page_text(psom_payload),
            },
        )
    )

    md_program_payload = fetch(session, MD_PROGRAM_URL)
    rows.append(
        row(
            md_program_payload,
            "md_program_context",
            "public",
            "public_md_program_context_no_student_roster",
            "md_program_context",
            "record_context_and_do_not_infer_student_people",
            0.76,
            public_count=0,
        )
    )

    protected_payload = fetch(session, PROTECTED_MD_DIRECTORY_URL)
    rows.append(
        row(
            protected_payload,
            "md_student_directory",
            "pennkey_protected" if protected_access(protected_payload) else "review_access_status",
            "protected_no_public_roster_records" if protected_access(protected_payload) else "review_required",
            "current_md_students",
            "record_as_not_public_and_monitor_index_for_access_change",
            0.92 if protected_access(protected_payload) else 0.5,
            public_count=0,
            evidence_extra={"protected_redirect_detected": protected_access(protected_payload)},
        )
    )

    for link in links:
        if canonical_url(link["url"]) in {
            canonical_url(MSTP_DIRECTORY_URL),
            canonical_url(MSTP_INDEX_URL),
            canonical_url(PSOM_DIRECTORY_URL),
            canonical_url(MD_PROGRAM_URL),
            canonical_url(PROTECTED_MD_DIRECTORY_URL),
        }:
            continue
        scope, status = classify_link(link["label"], link["url"])
        if scope not in {"graduate_directory_md_phd_filter", "md_student_directory"}:
            continue
        payload = fetch(session, link["url"])
        if scope == "md_student_directory":
            access = "pennkey_protected" if protected_access(payload) else "review_access_status"
            capture = "protected_no_public_roster_records" if protected_access(payload) else "review_required"
            action = "record_as_not_public_and_monitor_index_for_access_change"
            confidence = 0.9 if protected_access(payload) else 0.5
            public_count = 0
        else:
            access = "public" if payload["status"] == 200 else "fetch_error_or_unreachable"
            capture = status if payload["status"] == 200 else "unreachable_review"
            action = "use_only_for_mstp_crosscheck_or_background_enrichment_not_md_denominator"
            confidence = 0.66 if payload["status"] == 200 else 0.3
            public_count = max(count_profile_cards(payload), count_student_headings(payload))
        rows.append(
            row(
                payload,
                scope,
                access,
                capture,
                "md_phd_or_graduate_students",
                action,
                confidence,
                public_count=public_count,
                evidence_extra={"index_link_label": link["label"], "index_url": MSTP_INDEX_URL},
            )
        )

    audited_at = datetime.now(timezone.utc).isoformat()
    for item in rows:
        item["audited_at"] = audited_at
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM medical_student_source_audit")
    for item in rows:
        conn.execute(
            """
            INSERT INTO medical_student_source_audit
            (audit_key, source_url, source_title, source_scope, access_status,
             capture_status, source_role, observed_http_status, effective_url,
             public_person_count_observed, loaded_person_count, md_phd_signal_count,
             current_student_signal_count, directory_signal_count, recommended_next_action,
             confidence, evidence_json, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(item[field] for field in FIELDNAMES),
        )


def write_outputs(conn: sqlite3.Connection, rows: list[dict]) -> None:
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with conn:
        write_sqlite(conn, rows)
    summary = {
        "generated_at": max((row["audited_at"] for row in rows), default=datetime.now(timezone.utc).isoformat()),
        "audit_rows": len(rows),
        "by_access_status": dict(sorted(Counter(row["access_status"] for row in rows).items())),
        "by_capture_status": dict(sorted(Counter(row["capture_status"] for row in rows).items())),
        "by_source_scope": dict(sorted(Counter(row["source_scope"] for row in rows).items())),
        "by_recommended_next_action": dict(sorted(Counter(row["recommended_next_action"] for row in rows).items())),
        "public_mstp_loaded_people": sum(
            row["loaded_person_count"] for row in rows if row["capture_status"] == "accepted_public_mstp_roster"
        ),
        "public_mstp_observed_people": sum(
            row["public_person_count_observed"] for row in rows if row["capture_status"] == "accepted_public_mstp_roster"
        ),
        "protected_md_directory_rows": sum(
            1 for row in rows if row["capture_status"] == "protected_no_public_roster_records"
        ),
        "graduate_crosscheck_rows": sum(
            1 for row in rows if row["capture_status"] == "public_md_phd_crosscheck_candidate"
        ),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-med-student-source-audit/0.1"
    conn = sqlite3.connect(args.db)
    rows = build_rows(conn, session)
    write_outputs(conn, rows)
    conn.close()


if __name__ == "__main__":
    main()
