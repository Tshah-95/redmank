#!/usr/bin/env python3
"""Discover Penn Department of Medicine public trainee-roster candidates."""

from __future__ import annotations

import csv
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


SEEDS = [
    "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training",
    "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions",
]
ALLOWED_PREFIX = "/departments-and-centers/department-of-medicine"
OUT = Path("artifacts/data")


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def redact_text(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


def classify_candidate(url: str, title: str, headings: list[str], bio_count: int, text: str) -> str:
    haystack = " ".join([url, title, *headings, text[:1500]]).lower()
    if bio_count and any(token in haystack for token in ["current fellow", "fellows", "current resident", "residents"]):
        if any(token in haystack for token in ["program director", "faculty and staff"]) and not any(
            token in haystack for token in ["current fellow", "current resident", "first year", "pgy"]
        ):
            return "review"
        return "roster_candidate"
    if any(token in haystack for token in ["current fellows", "current residents", "student directory"]):
        return "non_bio_roster_candidate"
    if any(token in haystack for token in ["fellowship", "residency", "medical student"]):
        return "context"
    return "ignore"


def main() -> None:
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-source-discovery/0.1"
    queue = deque(SEEDS)
    seen = set()
    findings = []
    max_pages = int(os.environ.get("REDMANK_MAX_DISCOVERY_PAGES", "650"))

    while queue and len(seen) < max_pages:
        url = urldefrag(queue.popleft())[0]
        if url in seen:
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
        bio_count = len(soup.select(".bio-list .bio"))
        text = redact_text(norm(soup.get_text(" ")))
        classification = classify_candidate(url, title, headings, bio_count, text)
        if classification != "ignore":
            findings.append(
                {
                    "url": url,
                    "title": title,
                    "classification": classification,
                    "bio_count": bio_count,
                    "headings": headings[:12],
                }
            )

        for anchor in soup.select("a[href]"):
            href = urldefrag(urljoin(url, anchor["href"]))[0]
            parsed = urlparse(href)
            if parsed.netloc != "www3.pennmedicine.org":
                continue
            if not parsed.path.startswith(ALLOWED_PREFIX):
                continue
            if not any(token in parsed.path for token in ["education", "training", "fellow", "resident", "division"]):
                continue
            if href not in seen:
                queue.append(href)

    OUT.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pages_seen": len(seen),
        "findings": findings,
    }
    (OUT / "penn_source_discovery.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with (OUT / "penn_source_discovery.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["classification", "bio_count", "title", "url", "headings"])
        writer.writeheader()
        for row in findings:
            writer.writerow({**row, "headings": " | ".join(row["headings"])})
    print(f"seen={len(seen)} findings={len(findings)}")


if __name__ == "__main__":
    main()
