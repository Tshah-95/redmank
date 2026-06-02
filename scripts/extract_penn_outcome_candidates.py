#!/usr/bin/env python3
"""Extract source-level alumni/outcome candidate evidence from discovered Penn pages."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

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


def source_key_for(url: str) -> str:
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    return f"penn_outcome_{digest}"


def should_extract(row: dict) -> bool:
    if row.get("classification") != "alumni_or_outcome_candidate":
        return False
    title_url = f"{row.get('title', '')} {row.get('url', '')}".lower()
    reject_tokens = [
        "current fellows",
        "current residents",
        "leadership",
        "meet our team",
        "faculty",
        "residents |",
        "/residents",
        "/fellows",
    ]
    if any(token in title_url for token in reject_tokens):
        return False
    include_tokens = [
        "alumni",
        "graduate",
        "graduates",
        "career",
        "where are they",
        "outcomes",
        "spotlight",
        "former",
    ]
    return any(token in title_url for token in include_tokens)


def extract_outcome_phrases(text: str) -> list[str]:
    phrases = []
    patterns = [
        r"(?:obtained|accepted|matched|joined|appointed|became|currently (?:serves|works|practices))[^.]{20,220}\.",
        r"(?:alumni|graduates|former residents|former fellows)[^.]{20,260}\.",
        r"(?:career paths?|positions?|fellowship placement|job placement)[^.]{20,260}\.",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.I):
            phrase = redact_text(norm(match.group(0)))
            if phrase and phrase not in phrases:
                phrases.append(phrase)
    return phrases[:12]


def fetch_extract(session: requests.Session, row: dict) -> tuple[dict, list[dict]]:
    url = row["url"]
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    main = soup.select_one("main") or soup.body
    text = redact_text(norm(main.get_text(" "))) if main else ""
    source_key = source_key_for(url)
    source = {
        "source_key": source_key,
        "url": url,
        "title": row.get("title"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code,
        "effective_url": response.url,
        "sha256": hashlib.sha256(response.text.encode("utf-8")).hexdigest(),
        "discovery_classification": row.get("classification"),
    }
    claims = []
    for phrase in extract_outcome_phrases(text):
        claims.append(
            {
                "source_key": source_key,
                "source_url": url,
                "source_type": "official_outcome_context",
                "event_type": "penn_alumni_outcome_candidate",
                "display_name": "",
                "claim_value": phrase,
                "program_context": row.get("title"),
                "confidence": 0.45,
                "status": "candidate",
                "match_features": ["official_penn_page", "outcome_language", "source_level_not_person_resolved"],
                "quality_notes": ["source_level_outcome_phrase_not_person_linked"],
            }
        )
    if not claims:
        claims.append(
            {
                "source_key": source_key,
                "source_url": url,
                "source_type": "official_outcome_context",
                "event_type": "penn_alumni_outcome_candidate",
                "display_name": "",
                "claim_value": text[:700],
                "program_context": row.get("title"),
                "confidence": 0.25,
                "status": "candidate",
                "match_features": ["official_penn_page", "weak_outcome_context", "source_level_not_person_resolved"],
                "quality_notes": ["no_structured_outcome_phrase_found"],
            }
        )
    return source, claims


def write_outputs(sources: list[dict], claims: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "penn_outcome_candidate_sources.json").write_text(
        json.dumps(sources, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT / "penn_outcome_candidates.json").write_text(
        json.dumps(claims, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    fields = sorted({key for row in claims for key in row})
    with (OUT / "penn_outcome_candidates.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(claims)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources_extracted": len(sources),
        "candidate_claims": len(claims),
    }
    (OUT / "penn_outcome_candidates_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    discovery = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    candidates = [row for row in discovery["findings"] if should_extract(row)]
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-outcome-candidate-extractor/0.1"
    sources = []
    claims = []
    for row in candidates:
        source, source_claims = fetch_extract(session, row)
        sources.append(source)
        claims.extend(source_claims)
    write_outputs(sources, claims)
    print(f"sources={len(sources)} claims={len(claims)}")


if __name__ == "__main__":
    main()
