#!/usr/bin/env python3
"""Scrape the public Penn MSTP student directory as a separate partial student corpus."""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin

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


SOURCE_URL = "https://www.med.upenn.edu/mstp/student-directory/"
OUT = Path("artifacts/data")
RAW = OUT / "raw"


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def redact_html(html: str) -> str:
    html = re.sub(r"mailto:[^\"' <>\n]+", "mailto:[REDACTED_EMAIL]", html)
    html = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", html)
    return html


def snake(label: str) -> str:
    label = label.lower().replace("&", "and")
    label = re.sub(r"[^a-z0-9]+", "_", label).strip("_")
    if label == "grad_group":
        return "graduate_group"
    return label


def display_name(directory_name: str) -> str:
    if "," not in directory_name:
        return directory_name
    last, first = [part.strip() for part in directory_name.split(",", 1)]
    return norm(f"{first} {last}")


def email_from_href(href: str | None) -> str:
    if not href or not href.lower().startswith("mailto:"):
        return ""
    address = unquote(href.split(":", 1)[1].split("?", 1)[0]).strip()
    if not re.fullmatch(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", address):
        return ""
    return address.lower()


def contact_from_email(email: str, label: str, source_url: str) -> dict:
    return {
        "contact_type": "email",
        "value": email,
        "contact_label": label or "Email",
        "contact_scope": "institutional" if email.endswith((".edu", ".org")) else "public_unknown",
        "source_url": source_url,
        "source_type": "official_public_student_directory",
        "verification_status": "public_directory_unverified",
        "confidence": 0.82 if email.endswith((".edu", ".org")) else 0.62,
        "status": "candidate",
        "match_features": ["public_official_student_directory", "mailto_link"],
    }


def parse_detail_paragraph(paragraph) -> tuple[str, str]:
    title = paragraph.select_one(".profile-card__details-title")
    if not title:
        return "", ""
    label = snake(title.get_text(" "))
    title.extract()
    return label, norm(paragraph.get_text(" "))


def parse_students(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for card in soup.select("li.profile-card"):
        name_node = card.select_one("h2.name")
        if not name_node:
            continue
        directory_name = norm(name_node.get_text(" "))
        image = card.select_one("img")
        publication_link = card.find("a", string=re.compile("Publications", re.I))
        contacts = []
        for link in card.select('a[href^="mailto:"]'):
            email = email_from_href(link.get("href"))
            if email:
                contacts.append(contact_from_email(email, norm(link.get_text(" ")) or "Email", SOURCE_URL))
        row = {
            "source_key": "perelman_mstp_student_directory",
            "source_url": SOURCE_URL,
            "source_type": "official_public_student_directory",
            "institution": "Perelman School of Medicine at the University of Pennsylvania",
            "unit": "Medical Scientist Training Program",
            "program": "Medical Scientist Training Program",
            "population": "public_mstp_students",
            "role": "medical_student",
            "current_status": "current",
            "name": display_name(directory_name),
            "directory_name": directory_name,
            "profile_anchor_url": f"{SOURCE_URL}#{name_node.get('id')}" if name_node.get("id") else SOURCE_URL,
            "headshot_url": urljoin(SOURCE_URL, image.get("src")) if image else "",
            "publications_url": urljoin(SOURCE_URL, publication_link.get("href")) if publication_link else "",
            "extraction_method": "perelman_mstp_profile_card",
            "quality_tier": "medium",
            "quality_notes": [
                "partial_medical_student_population_mstp_only",
                "public_contact_candidates_extracted" if contacts else "no_public_contact_link_seen",
            ],
        }
        if contacts:
            row["contacts"] = contacts
        for paragraph in card.select("p"):
            key, value = parse_detail_paragraph(paragraph)
            if value:
                row[key] = value
        rows.append(row)
    return rows


def write_outputs(records: list[dict], source_meta: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "penn_mstp_students.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fields = sorted({key for row in records for key in row.keys()})
    with (OUT / "penn_mstp_students.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": source_meta,
        "student_records": len(records),
        "fields_present": {
            field: sum(1 for row in records if row.get(field))
            for field in [
                "graduate_group",
                "phase",
                "thesis_advisor",
                "affinity_groups_and_student_orgs",
                "academic_interests",
                "hobbies_and_interests",
                "other",
                "publications_url",
                "contacts",
            ]
        },
    }
    (OUT / "penn_mstp_students_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-mstp-student-directory/0.1"
    response = session.get(SOURCE_URL, timeout=30)
    source_meta = {
        "source_key": "perelman_mstp_student_directory",
        "url": SOURCE_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code,
        "effective_url": response.url,
    }
    response.raise_for_status()
    (RAW / "perelman_mstp_student_directory.html").write_text(redact_html(response.text), encoding="utf-8")
    write_outputs(parse_students(response.text), source_meta)


if __name__ == "__main__":
    main()
