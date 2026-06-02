#!/usr/bin/env python3
"""Scrape conservative Penn-wide resident/fellow roster candidates discovered outside Medicine."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter
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
PROGRAM_SLUG_OVERRIDES = {
    "aortic-surgery-fellowship": "Aortic Surgery Fellowship",
    "cardiothoracic-residency": "Cardiothoracic Surgery Residency",
    "cardiothoracic-transplantation-surgery-fellowship": "Cardiothoracic Transplantation Surgery Fellowship",
    "general-surgery-residency": "General Surgery Residency",
    "microvascular-reconstructive-surgery-fellowship": "Microvascular Reconstructive Surgery Fellowship",
    "plastic-surgery": "Plastic Surgery Residency",
    "thoracic-surgery-fellowship-cardiac-track": "Thoracic Surgery Fellowship - Cardiac Track",
    "transplant-fellowship": "Transplant Surgery Fellowship",
    "trauma-and-surgical-critical-care-fellowship": "Trauma and Surgical Critical Care Fellowship",
    "urology-residency": "Urology Residency",
    "vascular-surgery-fellowship": "Vascular Surgery Fellowship",
    "vascular-surgery-integrated-residency": "Vascular Surgery Integrated Residency",
}


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def redact_text(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


def absolute(base: str, maybe_url: str | None) -> str:
    if not maybe_url:
        return ""
    return urljoin(base, maybe_url)


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
        "source_type": "official_roster",
        "verification_status": "public_roster_unverified",
        "confidence": 0.82 if email.endswith((".edu", ".org")) else 0.62,
        "status": "candidate",
        "match_features": ["public_official_roster", "mailto_link"],
    }


def source_key_for(url: str) -> str:
    path = urlparse(url).path.strip("/").replace("/", "_")
    path = re.sub(r"[^a-zA-Z0-9_]+", "_", path).lower()
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"penn_affiliated_{path[:70]}_{digest}"


def should_scrape_source(row: dict) -> bool:
    if row.get("classification") != "trainee_roster_candidate":
        return False
    if int(row.get("bio_count") or 0) <= 0:
        return False
    title_url = f"{row.get('title', '')} {row.get('url', '')}".lower()
    if "/department-of-medicine/" in title_url:
        return False
    reject_tokens = [
        "/faculty",
        "faculty -",
        "meet our faculty",
        "leadership",
        "how to apply",
        "application",
        "welcome message",
        "advanced practice",
        "nurse anesthetists",
        "administrative staff",
    ]
    if any(token in title_url for token in reject_tokens):
        return False
    include_tokens = [
        "current residents",
        "current residents and fellows",
        "meet our residents",
        "meet our fellows",
        "current fellows",
        "/residents",
        "/fellows",
        "diagnostic-radiology-residents",
        "ir-integrated-residents",
    ]
    return any(token in title_url for token in include_tokens)


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


def infer_role(title: str, url: str) -> str:
    haystack = f"{title} {url}".lower()
    if "resident" in haystack:
        return "resident"
    if "fellow" in haystack:
        return "fellow"
    return "trainee"


def infer_role_for_group(title: str, url: str, label: str) -> str:
    label_lower = label.lower()
    if "fellow" in label_lower:
        return "fellow"
    if any(token in label_lower for token in ["resident", "pgy", "intern", "cy", "lab resident"]):
        return "resident"
    return infer_role(title, url)


def title_from_slug(slug: str) -> str:
    if slug in PROGRAM_SLUG_OVERRIDES:
        return PROGRAM_SLUG_OVERRIDES[slug]
    words = []
    for index, part in enumerate(slug.split("-")):
        if index > 0 and part in {"and", "of", "to"}:
            words.append(part)
        else:
            words.append(part.title())
    return " ".join(part for part in words if part)


def ensure_suffix(value: str, suffix: str) -> str:
    if suffix.lower() in value.lower():
        return value
    return f"{value} {suffix}"


def program_from_path(url: str, label: str) -> str:
    path = urlparse(url).path.strip("/")
    parts = path.split("/")
    if "department-of-radiology" in path:
        if path.endswith("diagnostic-radiology-residents"):
            return "Diagnostic Radiology Residency"
        if path.endswith("ir-integrated-residents"):
            return "Interventional Radiology Integrated Residency"
        if path.endswith("fellowships/meet-our-fellows") and label:
            return ensure_suffix(label, "Fellowship")
    if "ophthalmology" in path and "current-residents-and-fellows" in path:
        return "Ophthalmology Fellowship" if "fellow" in label.lower() else "Ophthalmology Residency"
    if "department-of-surgery" in path:
        for marker, suffix in [("residencies", "Residency"), ("fellowships", "Fellowship")]:
            if marker not in parts:
                continue
            marker_index = parts.index(marker)
            if len(parts) <= marker_index + 1:
                continue
            program = title_from_slug(parts[marker_index + 1])
            return ensure_suffix(program, suffix)
    return ""


def infer_program(title: str, url: str, label: str = "") -> str:
    path_program = program_from_path(url, label)
    if path_program:
        return path_program
    title = re.sub(r"\s*[-|]\s*Penn Medicine.*$", "", title).strip()
    title = re.sub(r"^Meet Our\s+", "", title, flags=re.I)
    title = title.replace("Current Residents & Fellows", "Ophthalmology Residency and Fellowship")
    if title:
        return title
    path = urlparse(url).path.strip("/").split("/")
    return " ".join(part.replace("-", " ").title() for part in path[-3:])


def infer_status(label: str) -> str:
    lower = label.lower()
    if any(token in lower for token in ["alumni", "former", "graduate"]):
        return "former"
    return "current"


def parse_source(session: requests.Session, source: dict) -> tuple[list[dict], dict]:
    url = source["url"]
    response = session.get(url, timeout=30)
    meta = {
        "source_key": source_key_for(url),
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code,
        "effective_url": response.url,
        "sha256": hashlib.sha256(response.text.encode("utf-8")).hexdigest(),
        "discovery_classification": source.get("classification"),
    }
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    title = source.get("title") or (norm(soup.title.get_text(" ")) if soup.title else "")
    rows = []
    for group in soup.select(".bio-list"):
        heading = group.find(["h1", "h2"], recursive=False)
        label = norm(heading.get_text(" ")) if heading else ""
        if not label:
            label_node = group.find_previous(["h1", "h2"])
            label = norm(label_node.get_text(" ")) if label_node else ""
        program = infer_program(title, url, label)
        role = infer_role_for_group(title, url, label)
        for bio in group.select(".bio"):
            name_node = bio.select_one(".bio__name")
            if not name_node:
                continue
            image = bio.select_one("img")
            profile = bio.select_one("a[href]")
            fields, contacts = parse_info_sets(bio, url)
            record = {
                "source_key": meta["source_key"],
                "source_url": url,
                "source_type": "official_roster",
                "institution": "University of Pennsylvania / Penn Medicine",
                "unit": "Penn Medicine",
                "program": program,
                "population": "penn_affiliated_current_trainees",
                "role": role,
                "training_year_label": label,
                "current_status": infer_status(label),
                "name": norm(name_node.get_text(" ")),
                "profile_url": absolute(url, profile.get("href") if profile else ""),
                "headshot_url": absolute(url, image.get("src") if image else ""),
                "headshot_alt": norm(image.get("alt") if image else ""),
                "extraction_method": "penn_affiliated_bio_component",
                "quality_tier": "medium",
                "quality_notes": ["broad_affiliated_scrape_needs_review"],
            }
            if contacts:
                record["contacts"] = contacts
                record["quality_notes"].append("public_contact_candidates_extracted")
            record.update(fields)
            rows.append(record)
    return rows, meta


def write_outputs(records: list[dict], source_meta: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "penn_affiliated_people.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT / "penn_affiliated_sources.json").write_text(
        json.dumps(source_meta, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    fields = sorted({key for row in records for key in row})
    with (OUT / "penn_affiliated_people.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources_scraped": len(source_meta),
        "person_records": len(records),
        "by_role": dict(sorted(Counter(row.get("role", "") for row in records).items())),
        "by_program": dict(sorted(Counter(row.get("program", "") for row in records).items())),
        "generic_program_label_count": sum(1 for row in records if row.get("program") in {"Residents", "Fellows"}),
        "by_source": {
            meta["source_key"]: sum(1 for row in records if row["source_key"] == meta["source_key"])
            for meta in source_meta
        },
    }
    (OUT / "penn_affiliated_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    candidates = [row for row in discovery["findings"] if should_scrape_source(row)]
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-affiliated-roster-scraper/0.1"
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
