#!/usr/bin/env python3
"""Extract conservative career/training claims from current Penn attending profiles."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

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
ATTENDING_CANDIDATES = OUT / "penn_attending_candidates.json"


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def redact_text(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


def source_key_for(url: str) -> str:
    path = urlparse(url).path.strip("/").replace("/", "_")
    path = re.sub(r"[^a-zA-Z0-9_]+", "_", path).lower()
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"penn_attending_profile_{path[:68]}_{digest}"


def profile_urls(records: list[dict]) -> list[dict]:
    seen = set()
    rows = []
    for row in records:
        url = row.get("profile_url") or ""
        if not url or url in seen:
            continue
        seen.add(url)
        rows.append(row)
    return rows


def useful_profile(response: requests.Response, soup: BeautifulSoup) -> bool:
    title = norm(soup.title.get_text(" ")) if soup.title else ""
    text = norm(soup.get_text(" "))
    if response.status_code != 200:
        return False
    if "404" in title.lower() or "page you are looking for cannot be found" in text[:500].lower():
        return False
    return True


def bio_text(soup: BeautifulSoup) -> str:
    bio = soup.select_one(".bio")
    node = bio or soup.select_one("main") or soup.body
    return redact_text(norm(node.get_text(" "))) if node else ""


def h1_name(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    return norm(h1.get_text(" ")) if h1 else ""


def add_claim(
    claims: list[dict],
    record: dict,
    source: dict,
    claim_type: str,
    claim_value: str,
    evidence_text: str,
    confidence: float,
    features: list[str],
    event_year: int | None = None,
    organization_name: str = "",
    status: str = "candidate",
) -> None:
    claim_value = norm(claim_value)
    evidence_text = norm(evidence_text)
    if not claim_value or not evidence_text:
        return
    if len(evidence_text) < 80:
        return
    claims.append(
        {
            "display_name": record.get("name", ""),
            "event_type": "attending_profile_training_history_candidate",
            "claim_type": claim_type,
            "claim_value": claim_value,
            "organization_name": organization_name,
            "event_year": event_year,
            "department": record.get("department", ""),
            "program_context": record.get("program_context", ""),
            "source_key": source["source_key"],
            "source_url": source["url"],
            "source_type": "official_attending_profile",
            "confidence": confidence,
            "status": status,
            "match_features": features,
            "evidence_text": evidence_text,
        }
    )


def extract_year(text: str) -> int | None:
    matches = [int(value) for value in re.findall(r"\b(19\d{2}|20\d{2})\b", text)]
    return matches[-1] if matches else None


def extract_structured_provider_training(record: dict, source: dict, text: str) -> list[dict]:
    lower = text.lower()
    marker = "my education and training"
    start = lower.find(marker)
    if start == -1:
        return []
    section = text[start + len(marker) :]
    end_positions = [
        position
        for token in [" reviews", " insurance accepted", " locations", " qualifications and experience"]
        for position in [section.lower().find(token)]
        if position != -1
    ]
    if end_positions:
        section = section[: min(end_positions)]
    section = norm(section)
    claims: list[dict] = []
    for label, claim_type in [
        ("Medical School", "education_history_candidate"),
        ("Residency", "prior_training_history_candidate"),
        ("Fellowship", "prior_training_history_candidate"),
    ]:
        field_match = re.search(
            rf"{re.escape(label)}:\s+(.+?)(?=\s+(?:Medical School|Residency|Fellowship):|\s*$)",
            section,
            flags=re.I,
        )
        if not field_match:
            continue
        value = norm(field_match.group(1))
        is_penn = bool(re.search(r"\b(Penn|University of Pennsylvania|HUP|Hospital of the University of Pennsylvania)\b", value, re.I))
        add_claim(
            claims,
            record,
            source,
            "penn_training_history_candidate" if is_penn else claim_type,
            f"{label}: {value}",
            f"My education and training - {label}: {value}",
            0.78 if is_penn else 0.68,
            [
                "official_penn_profile",
                "profile_name_match",
                "structured_provider_training_field",
                "penn_training_language" if is_penn else "training_or_education_language",
            ],
            organization_name="University of Pennsylvania / Penn Medicine" if is_penn else value,
            status="needs_review" if is_penn else "candidate",
        )
    return claims


def extract_claims(record: dict, source: dict, text: str) -> list[dict]:
    structured_claims = extract_structured_provider_training(record, source, text)
    if structured_claims:
        return structured_claims
    if "/providers/" in source.get("effective_url", "") or "/providers/" in source.get("url", ""):
        return []
    claims: list[dict] = []
    protected = text.replace("Dr.", "Dr<dot>").replace("Ms.", "Ms<dot>").replace("Mr.", "Mr<dot>")
    sentences = [
        norm(sentence.replace("Dr<dot>", "Dr.").replace("Ms<dot>", "Ms.").replace("Mr<dot>", "Mr."))
        for sentence in re.split(r"(?<=[.!?])\s+", protected)
        if norm(sentence)
    ]
    for sentence in sentences:
        lower = sentence.lower()
        emitted_training_claim = False
        if any(token in lower for token in ["residency", "fellowship", "graduate medical education", "training at"]):
            if any(token in lower for token in ["hospital of the university of pennsylvania", "hup", "penn"]):
                add_claim(
                    claims,
                    record,
                    source,
                    "penn_training_history_candidate",
                    sentence,
                    sentence,
                    0.72,
                    ["official_penn_profile", "profile_name_match", "penn_training_language"],
                    event_year=extract_year(sentence),
                    organization_name="University of Pennsylvania / Penn Medicine",
                    status="needs_review",
                )
                emitted_training_claim = True
            else:
                add_claim(
                    claims,
                    record,
                    source,
                    "prior_training_history_candidate",
                    sentence,
                    sentence,
                    0.52,
                    ["official_penn_profile", "profile_name_match", "training_language"],
                    event_year=extract_year(sentence),
                    status="candidate",
                )
                emitted_training_claim = True
        if not emitted_training_claim and any(
            token in lower for token in ["medical school", "matriculating at", "graduating from", "graduated from"]
        ):
            add_claim(
                claims,
                record,
                source,
                "education_history_candidate",
                sentence,
                sentence,
                0.5,
                ["official_penn_profile", "profile_name_match", "education_language"],
                event_year=extract_year(sentence),
                status="candidate",
            )
        if "research interest" in lower or "research interests" in lower:
            add_claim(
                claims,
                record,
                source,
                "research_interest_candidate",
                sentence,
                sentence,
                0.55,
                ["official_penn_profile", "profile_name_match", "research_interest_language"],
                status="candidate",
            )
        if any(token in lower for token in ["outside of the hospital", "outside the hospital", "outside of work"]):
            add_claim(
                claims,
                record,
                source,
                "personal_profile_candidate",
                sentence,
                sentence,
                0.45,
                ["official_penn_profile", "profile_name_match", "personal_profile_language"],
                status="candidate",
            )
    return claims


def fetch_profile(session: requests.Session, record: dict) -> tuple[dict, list[dict]]:
    url = record["profile_url"]
    response = session.get(url, timeout=30, allow_redirects=True)
    soup = BeautifulSoup(response.text, "lxml")
    source = {
        "source_key": source_key_for(url),
        "url": url,
        "effective_url": response.url,
        "title": norm(soup.title.get_text(" ")) if soup.title else "",
        "profile_name": h1_name(soup),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code,
        "sha256": hashlib.sha256(response.text.encode("utf-8")).hexdigest(),
        "source_type": "official_attending_profile",
        "usable_profile": useful_profile(response, soup),
    }
    if not source["usable_profile"]:
        source["extraction_status"] = "unusable_profile_or_404"
        return source, []
    text = bio_text(soup)
    source["text_length"] = len(text)
    source["extraction_status"] = "profile_claims_extracted" if text else "no_profile_text"
    return source, extract_claims(record, source, text)


def write_outputs(sources: list[dict], claims: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "penn_attending_profile_sources.json").write_text(
        json.dumps(sources, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (OUT / "penn_attending_profile_claims.json").write_text(
        json.dumps(claims, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    fields = sorted({key for row in claims for key in row})
    with (OUT / "penn_attending_profile_claims.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(claims)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profiles_attempted": len(sources),
        "usable_profiles": sum(1 for row in sources if row.get("usable_profile")),
        "claims": len(claims),
        "by_claim_type": {
            claim_type: sum(1 for row in claims if row.get("claim_type") == claim_type)
            for claim_type in sorted({row.get("claim_type", "") for row in claims})
        },
        "by_status": {
            status: sum(1 for row in claims if row.get("status") == status)
            for status in sorted({row.get("status", "") for row in claims})
        },
        "by_source_status": {
            status: sum(1 for row in sources if row.get("extraction_status") == status)
            for status in sorted({row.get("extraction_status", "") for row in sources})
        },
    }
    (OUT / "penn_attending_profile_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    records = json.loads(ATTENDING_CANDIDATES.read_text(encoding="utf-8"))
    candidates = profile_urls(records)
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-attending-profile-enrichment/0.1"
    sources = []
    claims = []
    for record in candidates:
        source, source_claims = fetch_profile(session, record)
        sources.append(source)
        claims.extend(source_claims)
    write_outputs(sources, claims)
    print(f"profiles={len(sources)} usable={sum(1 for row in sources if row.get('usable_profile'))} claims={len(claims)}")


if __name__ == "__main__":
    main()
