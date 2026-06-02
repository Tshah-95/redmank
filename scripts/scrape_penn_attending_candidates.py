#!/usr/bin/env python3
"""Scrape conservative current Penn attending/faculty candidate pages."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse

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


OUT = Path("artifacts/data")
DISCOVERY = OUT / "penn_affiliated_source_discovery.json"


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def redact_text(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


def absolute(base: str, maybe_url: str | None) -> str:
    return urljoin(base, maybe_url) if maybe_url else ""


def safe_profile_url(base: str, maybe_url: str | None) -> str:
    if not maybe_url or maybe_url.lower().startswith("mailto:"):
        return ""
    return absolute(base, maybe_url)


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
        "source_type": "official_attending_faculty_candidate",
        "verification_status": "public_profile_unverified",
        "confidence": 0.82 if email.endswith((".edu", ".org")) else 0.62,
        "status": "candidate",
        "match_features": ["public_official_profile", "mailto_link"],
    }


def source_key_for(url: str) -> str:
    path = urlparse(url).path.strip("/").replace("/", "_")
    path = re.sub(r"[^a-zA-Z0-9_]+", "_", path).lower()
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"penn_attending_{path[:70]}_{digest}"


def should_scrape_source(row: dict) -> bool:
    if row.get("classification") != "attending_faculty_candidate":
        return False
    if int(row.get("bio_count") or 0) <= 0:
        return False
    title_url = f"{row.get('title', '')} {row.get('url', '')}".lower()
    reject_tokens = [
        "advanced practice",
        "administrative staff",
        "staff",
        "nurse anesthetists",
        "crna",
        "clerkship",
        "sub-internship",
        "/fellows",
        "/fellow",
        "current fellows",
        "meet our fellow",
        "applying for residency",
    ]
    if any(token in title_url for token in reject_tokens):
        return False
    include_tokens = [
        "/faculty",
        "faculty",
        "leadership",
        "faculty and administration",
        "meet the faculty",
    ]
    return any(token in title_url for token in include_tokens)


def infer_department(title: str, url: str) -> str:
    path = urlparse(url).path
    for marker, department in [
        ("department-of-surgery", "Department of Surgery"),
        ("department-of-radiology", "Department of Radiology"),
        ("department-of-medicine", "Department of Medicine"),
        ("anesthesiology-and-critical-care", "Department of Anesthesiology and Critical Care"),
        ("emergency-medicine", "Emergency Medicine"),
        ("ophthalmology", "Ophthalmology"),
    ]:
        if marker in path:
            return department
    return title.split("- Penn Medicine")[0].strip()


def parse_info_sets(bio, source_url: str) -> tuple[dict, list[dict]]:
    fields = {}
    contacts = []
    for span in bio.select(".bio__info-set"):
        key_node = span.select_one(".bio__info-key")
        if not key_node:
            continue
        key = norm(key_node.get_text()).rstrip(":").lower().replace(" ", "_").replace("/", "_")
        if key == "email":
            for link in span.select('a[href^="mailto:"]'):
                email = email_from_href(link.get("href"))
                if email:
                    contacts.append(contact_from_email(email, norm(link.get_text(" ")) or "Email", source_url))
            continue
        key_node.extract()
        value = redact_text(norm(span.get_text(" ")))
        if value:
            fields[key] = value
    return fields, contacts


def parse_source(session: requests.Session, source: dict) -> tuple[list[dict], dict]:
    url = source["url"]
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    title = source.get("title") or (norm(soup.title.get_text(" ")) if soup.title else "")
    source_key = source_key_for(url)
    meta = {
        "source_key": source_key,
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code,
        "effective_url": response.url,
        "sha256": hashlib.sha256(response.text.encode("utf-8")).hexdigest(),
        "discovery_classification": source.get("classification"),
    }
    rows = []
    for bio in soup.select(".bio-list .bio"):
        name_node = bio.select_one(".bio__name")
        if not name_node:
            continue
        image = bio.select_one("img")
        profile = bio.select_one("a[href]")
        fields, contacts = parse_info_sets(bio, url)
        role_title = fields.get("title") or fields.get("position") or ""
        record = {
            "source_key": source_key,
            "source_url": url,
            "source_type": "official_attending_faculty_candidate",
            "institution": "University of Pennsylvania / Penn Medicine",
            "department": infer_department(title, url),
            "program_context": title,
            "event_type": "current_penn_attending_candidate",
            "role": "attending",
            "current_status": "current",
            "name": norm(name_node.get_text(" ")),
            "role_title": role_title,
            "profile_url": safe_profile_url(url, profile.get("href") if profile else ""),
            "headshot_url": absolute(url, image.get("src") if image else ""),
            "headshot_alt": norm(image.get("alt") if image else ""),
            "extraction_method": "penn_attending_bio_component",
            "quality_tier": "candidate",
            "quality_notes": ["current_faculty_candidate_not_linked_to_prior_training"],
        }
        if contacts:
            record["contacts"] = contacts
            record["quality_notes"].append("public_contact_candidates_extracted")
        record.update(fields)
        rows.append(record)
    return rows, meta


def write_outputs(records: list[dict], sources: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "penn_attending_candidates.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT / "penn_attending_candidate_sources.json").write_text(
        json.dumps(sources, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    fields = sorted({key for row in records for key in row})
    with (OUT / "penn_attending_candidates.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources_scraped": len(sources),
        "candidate_records": len(records),
        "by_department": {
            department: sum(1 for row in records if row.get("department") == department)
            for department in sorted({row.get("department", "") for row in records})
        },
    }
    (OUT / "penn_attending_candidates_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    candidates = [row for row in discovery["findings"] if should_scrape_source(row)]
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-attending-candidate-scraper/0.1"
    records = []
    sources = []
    for candidate in candidates:
        rows, meta = parse_source(session, candidate)
        records.extend(rows)
        sources.append(meta)
    write_outputs(records, sources)
    print(f"sources={len(sources)} records={len(records)}")


if __name__ == "__main__":
    main()
