#!/usr/bin/env python3
"""Discover Penn-affiliated public pages that may contain trainees, alumni, or attendings."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from collections import deque
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


OUT = Path("artifacts/data")
SEEDS = [
    "https://www3.pennmedicine.org/departments-and-centers",
    "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training",
    "https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training",
    "https://www3.pennmedicine.org/departments-and-centers/department-of-radiology/education-and-training",
    "https://www3.pennmedicine.org/departments-and-centers/emergency-medicine/education-and-training",
    "https://www3.pennmedicine.org/departments-and-centers/anesthesiology-and-critical-care/education-and-training",
    "https://www3.pennmedicine.org/departments-and-centers/ophthalmology/education-and-training",
    "https://www3.pennmedicine.org/departments-and-centers/physical-medicine-and-rehabilitation/education-and-training",
    "https://pathology.med.upenn.edu/education",
]
ALLOWED_HOSTS = {"www3.pennmedicine.org", "pathology.med.upenn.edu"}
ALLOW_PATH_PREFIXES = {
    "www3.pennmedicine.org": ["/departments-and-centers"],
    "pathology.med.upenn.edu": ["/education", "/people"],
}
PATH_TOKENS = [
    "education",
    "training",
    "resident",
    "residen",
    "fellow",
    "faculty",
    "people",
    "team",
    "profile",
    "alumni",
]


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def redact_text(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


def allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.netloc not in ALLOWED_HOSTS:
        return False
    if not any(parsed.path.startswith(prefix) for prefix in ALLOW_PATH_PREFIXES[parsed.netloc]):
        return False
    return any(token in parsed.path.lower() for token in PATH_TOKENS)


def classify(url: str, title: str, headings: list[str], bio_count: int, text: str) -> tuple[str, list[str]]:
    haystack = " ".join([url, title, *headings, text[:2500]]).lower()
    signals = []
    if bio_count:
        signals.append(f"bio_count:{bio_count}")
    for token in [
        "current residents",
        "current fellows",
        "meet our residents",
        "meet our fellows",
        "our current fellows",
        "resident profiles",
        "fellow profiles",
        "alumni",
        "faculty",
        "attending",
        "current faculty",
        "clinical faculty",
        "program director",
    ]:
        if token in haystack:
            signals.append(token)

    trainee_tokens = [
        "current residents",
        "current fellows",
        "meet our residents",
        "meet our fellows",
        "our current fellows",
        "resident profiles",
        "fellow profiles",
    ]
    faculty_tokens = ["faculty", "attending", "clinical faculty", "current faculty"]
    alumni_tokens = ["alumni", "graduates", "former residents", "former fellows"]
    if any(token in haystack for token in trainee_tokens):
        return "trainee_roster_candidate", signals
    if any(token in haystack for token in alumni_tokens):
        return "alumni_or_outcome_candidate", signals
    if bio_count and any(token in haystack for token in faculty_tokens):
        return "attending_faculty_candidate", signals
    if any(token in haystack for token in ["residency", "fellowship", "graduate medical education"]):
        return "program_context", signals
    if bio_count:
        return "bio_review", signals
    return "ignore", signals


def page_digest(html: str) -> str:
    return hashlib.sha256(html.encode("utf-8")).hexdigest()


def main() -> None:
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-affiliated-source-discovery/0.1"
    max_pages = int(os.environ.get("REDMANK_MAX_AFFILIATED_DISCOVERY_PAGES", "900"))
    queue = deque(SEEDS)
    seen: set[str] = set()
    findings = []

    while queue and len(seen) < max_pages:
        url = urldefrag(queue.popleft())[0]
        if url in seen:
            continue
        if not allowed_url(url) and url not in SEEDS:
            continue
        seen.add(url)
        try:
            response = session.get(url, timeout=20)
        except requests.RequestException:
            continue
        if response.status_code != 200 or "text/html" not in response.headers.get("content-type", ""):
            continue
        soup = BeautifulSoup(response.text, "lxml")
        title = redact_text(norm(soup.title.get_text(" "))) if soup.title else ""
        headings = [redact_text(norm(h.get_text(" "))) for h in soup.find_all(["h1", "h2"])[:20]]
        bio_count = len(soup.select(".bio-list .bio, li.profile-card, article.profile, .profile-card"))
        text = redact_text(norm(soup.get_text(" ")))
        classification, signals = classify(url, title, headings, bio_count, text)
        if classification != "ignore":
            findings.append(
                {
                    "url": url,
                    "title": title,
                    "classification": classification,
                    "bio_count": bio_count,
                    "signals": signals,
                    "headings": headings[:12],
                    "sha256": page_digest(response.text),
                }
            )

        for anchor in soup.select("a[href]"):
            href = urldefrag(urljoin(url, anchor["href"]))[0]
            if href not in seen and allowed_url(href):
                queue.append(href)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages_seen": len(seen),
        "seeds": SEEDS,
        "findings": findings,
    }
    (OUT / "penn_affiliated_source_discovery.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with (OUT / "penn_affiliated_source_discovery.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["classification", "bio_count", "title", "url", "signals", "headings", "sha256"],
            lineterminator="\n",
        )
        writer.writeheader()
        for row in findings:
            writer.writerow(
                {
                    **row,
                    "signals": " | ".join(row["signals"]),
                    "headings": " | ".join(row["headings"]),
                }
            )
    print(f"seen={len(seen)} findings={len(findings)}")


if __name__ == "__main__":
    main()
