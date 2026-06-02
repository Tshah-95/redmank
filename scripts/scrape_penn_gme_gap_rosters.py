#!/usr/bin/env python3
"""Scrape conservative trainee rosters from the official HUP gap source queue."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
from collections import Counter, defaultdict
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


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"

DEGREE_PATTERN = re.compile(
    r"\b(M\.?D\.?|D\.?O\.?|D\.?D\.?S\.?|D\.?P\.?M\.?|BDS|MBBS|MBBCh|PhD|Ph\.D\.?|MPH|MPP|MS|M\.S\.?|MBA|MHA|MEHP)\b",
    re.I,
)
NAME_LINE_PATTERN = re.compile(
    r"^[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.\-]+(?:\s+[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.\-]+){1,5}(?:,\s*| )(?:M\.?D\.?|D\.?O\.?|D\.?D\.?S\.?|D\.?P\.?M\.?|BDS|MBBS|MBBCh)\b",
    re.I,
)
STOP_HEADING_RE = re.compile(
    r"\b(alumni|graduates?|congratulations|faculty|apply|application|overview|curriculum|benefits|salary|contact)\b",
    re.I,
)

PROGRAM_ALIASES = {
    "Adult Reconstruction": "Adult Reconstructive Orthopedics Fellowship",
    "Hand Surgery": "Hand Surgery Fellowship",
    "Orthoplastics & Limb Salvage": "Orthoplastics and Limb Salvage Fellowship",
    "Shoulder & Elbow": "Shoulder and Elbow Fellowship",
    "Spine (non-ACGME)": "Spine Fellowship",
    "Sports Medicine": "Sports Medicine Fellowship",
    "Foot & Ankle (non-ACGME)": "Foot and Ankle Fellowship",
    "Head And Neck Surgical Oncology, Microvascular Reconstruction, & Robotic Surgery Fellows": "Head and Neck Surgical Oncology, Microvascular Reconstruction, and Robotic Surgery Fellowship",
    "Rhinology & Skull Base Surgery Fellows": "Rhinology and Skull Base Surgery Fellowship",
    "Sleep Medicine and Surgery Fellows": "Sleep Medicine and Surgery Fellowship",
    "Neurotology Fellow": "Neurotology Fellowship",
    "Facial Plastic and Reconstructive Surgery Fellow": "Facial Plastic and Reconstructive Surgery Fellowship",
    "Children’s Hospital Of Philadelphia Otolaryngology Fellows": "CHOP Otolaryngology Fellowship",
    "Children's Hospital Of Philadelphia Otolaryngology Fellows": "CHOP Otolaryngology Fellowship",
}


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).replace("\xa0", " ")).strip()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def source_key_for(url: str) -> str:
    path = urlparse(url).path.strip("/").replace("/", "_")
    path = re.sub(r"[^a-zA-Z0-9_]+", "_", path).lower()
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"penn_gme_gap_{path[:70]}_{digest}"


def absolute(base: str, maybe_url: str | None) -> str:
    if not maybe_url:
        return ""
    return urljoin(base, maybe_url)


def redact_text(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


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
        "source_type": "official_gap_roster",
        "verification_status": "public_roster_unverified",
        "confidence": 0.82 if email.endswith((".edu", ".org")) else 0.62,
        "status": "candidate",
        "match_features": ["public_official_roster", "mailto_link"],
    }


def normalize_program(program_name: str, program_type: str) -> str:
    program_name = norm(program_name)
    if not program_name:
        return ""
    if program_name in PROGRAM_ALIASES:
        return PROGRAM_ALIASES[program_name]
    if program_type == "residency" and "residency" not in program_name.lower():
        return f"{program_name} Residency"
    if program_type == "fellowship" and "fellowship" not in program_name.lower():
        return f"{program_name} Fellowship"
    return program_name


def program_for_candidate(candidate: dict, source_url: str, label: str = "") -> str:
    path = urlparse(source_url).path.lower()
    label = norm(label)
    if "oto.med.upenn.edu/current-residents" in source_url or "oto.med.upenn.edu/resident-profiles" in source_url:
        return "Otorhinolaryngology Residency"
    if "oto.med.upenn.edu/current-fellows" in source_url and label in PROGRAM_ALIASES:
        return PROGRAM_ALIASES[label]
    if "orthopaedic-surgery/education-and-training/fellowships/current-fellows" in path and label in PROGRAM_ALIASES:
        return PROGRAM_ALIASES[label]
    return normalize_program(candidate["program_name"], candidate["program_type"])


def clean_name(value: str) -> str:
    value = norm(value)
    value = re.sub(r"\([^)]*\)", "", value)
    value = re.sub(r"\bView Full Profile\b", "", value, flags=re.I)
    value = re.sub(r"\bChief Resident\b|\bChief Education Officer\b|\bAcademic Chief Resident\b", "", value, flags=re.I)
    value = re.sub(r"\b([A-Z])\s+([a-z]{2,})\b", r"\1\2", value)
    value = re.sub(r"\b([A-Z][a-z]{1,5})\s+([a-z]{1,4})(?=,)", r"\1\2", value)
    value = re.sub(r"\s+([,.;])", r"\1", value)
    value = re.sub(r"\bM\.D\s+\.", "M.D.", value)
    value = re.sub(r"\s+", " ", value).strip(" ,")
    parts = value.split()
    joined = []
    index = 0
    while index < len(parts):
        if (
            index + 1 < len(parts)
            and re.fullmatch(r"[A-Z][a-z]{1,5}", parts[index])
            and re.fullmatch(r"[a-z]{1,4}", parts[index + 1])
        ):
            joined.append(parts[index] + parts[index + 1])
            index += 2
            continue
        joined.append(parts[index])
        index += 1
    value = " ".join(joined)
    return value


def looks_like_person_name(value: str) -> bool:
    value = clean_name(value)
    if not value or value.upper() == "TBD" or STOP_HEADING_RE.search(value):
        return False
    return bool(NAME_LINE_PATTERN.search(value) or (DEGREE_PATTERN.search(value) and len(value.split()) <= 8))


def looks_like_structured_roster_name(value: str) -> bool:
    value = clean_name(value)
    if not value or value.upper() == "TBD" or STOP_HEADING_RE.search(value):
        return False
    if looks_like_person_name(value):
        return True
    return bool(re.fullmatch(r"[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.\-]+(?:\s+[A-Z][A-Za-zÀ-ÖØ-öø-ÿ'’.\-]+){1,4}", value))


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


def infer_role(program_type: str, label: str, url: str) -> str:
    haystack = f"{program_type} {label} {url}".lower()
    if "fellow" in haystack:
        return "fellow"
    if "resident" in haystack or "pgy" in haystack:
        return "resident"
    return "resident" if program_type == "residency" else "fellow"


def record_for(
    candidate: dict,
    source_key: str,
    source_url: str,
    name: str,
    program: str,
    role: str,
    training_label: str,
    extraction_method: str,
    fields: dict | None = None,
    contacts: list[dict] | None = None,
    profile_url: str = "",
    headshot_url: str = "",
) -> dict:
    quality_notes = [
        "official_hup_gap_queue_source",
        "queue_driven_roster_scrape_needs_review",
        f"source_priority_{candidate.get('priority')}",
    ]
    if contacts:
        quality_notes.append("public_contact_candidates_extracted")
    record = {
        "source_key": source_key,
        "source_url": source_url,
        "source_type": "official_gap_roster",
        "institution": "University of Pennsylvania / Penn Medicine",
        "unit": candidate.get("department") or "Penn Medicine",
        "program": program,
        "program_memberships": [program],
        "population": "penn_affiliated_current_trainees",
        "role": role,
        "training_year_label": training_label,
        "current_status": "current",
        "name": clean_name(name),
        "profile_url": profile_url,
        "headshot_url": headshot_url,
        "headshot_alt": "",
        "extraction_method": extraction_method,
        "quality_tier": "medium",
        "quality_notes": quality_notes,
        "official_program_key": candidate.get("official_program_key"),
        "coverage_gap_program_name": candidate.get("program_name"),
        "coverage_gap_status": candidate.get("coverage_status"),
    }
    if contacts:
        record["contacts"] = contacts
    if fields:
        record.update(fields)
    return record


def class_or_pgy_label(text: str) -> str:
    text = norm(text)
    if re.fullmatch(r"PGY\s*\d+", text, flags=re.I):
        return text.upper().replace(" ", "")
    if re.fullmatch(r"Class of \d{4}", text, flags=re.I):
        return text
    if "chief resident" in text.lower():
        return "Chief Resident"
    return text


def extract_bio_cards(soup: BeautifulSoup, candidate: dict, source_key: str, source_url: str) -> list[dict]:
    title = norm(soup.title.get_text(" ")) if soup.title else candidate.get("candidate_title", "")
    rows = []
    for group in soup.select(".bio-list"):
        heading = group.find(["h1", "h2", "h3"], recursive=False)
        label = norm(heading.get_text(" ")) if heading else ""
        if not label:
            previous = group.find_previous(["h1", "h2", "h3"])
            label = norm(previous.get_text(" ")) if previous else candidate.get("candidate_title", "")
        if STOP_HEADING_RE.search(label):
            continue
        program = program_for_candidate(candidate, source_url, label)
        role = infer_role(candidate["program_type"], label or title, source_url)
        for bio in group.select(".bio"):
            name_node = bio.select_one(".bio__name")
            if not name_node:
                continue
            name = norm(name_node.get_text(" "))
            if not looks_like_structured_roster_name(name):
                continue
            image = bio.select_one("img")
            profile = bio.select_one("a[href]")
            fields, contacts = parse_info_sets(bio, source_url)
            rows.append(
                record_for(
                    candidate,
                    source_key,
                    source_url,
                    name,
                    program,
                    role,
                    class_or_pgy_label(label),
                    "gap_queue_bio_component",
                    fields=fields,
                    contacts=contacts,
                    profile_url=absolute(source_url, profile.get("href") if profile else ""),
                    headshot_url=absolute(source_url, image.get("src") if image else ""),
                )
            )
    return rows


def extract_profiles(soup: BeautifulSoup, candidate: dict, source_key: str, source_url: str) -> list[dict]:
    rows = []
    for profile in soup.select(".profile"):
        name_node = profile.select_one(".name, h2, h3, h4")
        if not name_node:
            continue
        name = norm(name_node.get_text(" "))
        if not looks_like_person_name(name):
            continue
        label = ""
        previous = profile.find_previous(["h2", "h3"])
        if previous and previous is not name_node:
            previous_text = norm(previous.get_text(" "))
            if re.search(r"\b(Class of \d{4}|PGY\s*\d+)\b", previous_text, re.I):
                label = previous_text
        rows.append(
            record_for(
                candidate,
                source_key,
                source_url,
                name,
                program_for_candidate(candidate, source_url, label),
                infer_role(candidate["program_type"], label, source_url),
                class_or_pgy_label(label or candidate.get("candidate_title", "")),
                "gap_queue_profile_component",
                fields={"bio_text": redact_text(norm(profile.get_text(" ")))},
            )
        )
    return rows


def extract_accordion_headers(soup: BeautifulSoup, candidate: dict, source_key: str, source_url: str) -> list[dict]:
    rows = []
    for heading in soup.select(".accordion-header"):
        name = norm(heading.get_text(" "))
        if not looks_like_person_name(name):
            continue
        text = ""
        panel = heading.find_next()
        if panel:
            text = redact_text(norm(panel.get_text(" ")))
        label = ""
        phase_match = re.search(r"\bPGY-?\s*(\d+)\b", text, re.I)
        if phase_match:
            label = f"PGY {phase_match.group(1)}"
        rows.append(
            record_for(
                candidate,
                source_key,
                source_url,
                name,
                program_for_candidate(candidate, source_url, label),
                infer_role(candidate["program_type"], label, source_url),
                class_or_pgy_label(label or candidate.get("candidate_title", "")),
                "gap_queue_accordion_header",
                fields={"bio_text": text},
            )
        )
    return rows


def iter_heading_sections(soup: BeautifulSoup):
    main = soup.find("main") or soup.body
    if not main:
        return
    current_label = ""
    for node in main.find_all(["h2", "h3", "p"], recursive=True):
        text = norm(node.get_text(" "))
        if not text:
            continue
        if node.name in {"h2", "h3"}:
            current_label = text
            continue
        yield current_label, text


def extract_heading_name_lists(soup: BeautifulSoup, candidate: dict, source_key: str, source_url: str) -> list[dict]:
    rows = []
    for label, text in iter_heading_sections(soup) or []:
        if not label or STOP_HEADING_RE.search(label):
            continue
        if not looks_like_person_name(text):
            continue
        if "View Full Profile" in text:
            continue
        program_label = PROGRAM_ALIASES.get(label) or program_for_candidate(candidate, source_url, label)
        rows.append(
            record_for(
                candidate,
                source_key,
                source_url,
                text,
                program_label,
                infer_role(candidate["program_type"], label, source_url),
                class_or_pgy_label(label),
                "gap_queue_heading_name_list",
            )
        )
    return rows


def existing_roster_urls(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0].rstrip("/")
        for row in conn.execute(
            """
            SELECT DISTINCT source_url
            FROM sources
            WHERE source_type IN ('official_roster_or_context', 'official_affiliated_roster')
            """
        )
        if row[0]
    }


def queue_candidates(conn: sqlite3.Connection, limit: int | None) -> list[dict]:
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT *
        FROM official_program_source_candidates
        WHERE candidate_status = 'roster_source_candidate'
          AND priority >= 115
        ORDER BY priority DESC, confidence DESC, department, program_name, candidate_url
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = [dict(row) for row in conn.execute(sql)]
    by_url = defaultdict(list)
    for row in rows:
        by_url[row["candidate_url"].rstrip("/")].append(row)
    selected = []
    for url, candidates in by_url.items():
        def url_fit(row: dict) -> int:
            haystack = f"{url} {row.get('candidate_title', '')}".lower()
            score = 0
            if any(token in haystack for token in ["current-residents", "/residents", "resident-profiles"]):
                score += 30 if row.get("program_type") == "residency" else -30
            if any(token in haystack for token in ["current-fellows", "/fellows", "/fellow"]):
                score += 30 if row.get("program_type") == "fellowship" else -30
            if "student-fellows" in haystack:
                score -= 80
            return score

        candidates.sort(
            key=lambda row: (
                -url_fit(row),
                -int(row.get("priority") or 0),
                row.get("program_name", ""),
            )
        )
        selected.append(candidates[0])
    selected.sort(key=lambda row: (-int(row.get("priority") or 0), row.get("department", ""), row.get("program_name", "")))
    return selected


def parse_candidate(session: requests.Session, candidate: dict) -> tuple[list[dict], dict]:
    url = candidate["candidate_url"].rstrip("/")
    response = session.get(url, timeout=30)
    fetched_at = datetime.now(timezone.utc).isoformat()
    meta = {
        "source_key": source_key_for(url),
        "url": url,
        "fetched_at": fetched_at,
        "http_status": response.status_code,
        "effective_url": response.url,
        "sha256": hashlib.sha256(response.content).hexdigest(),
        "source_type": "official_gap_roster",
        "candidate_key": candidate.get("candidate_key"),
        "official_program_key": candidate.get("official_program_key"),
        "candidate_priority": candidate.get("priority"),
        "candidate_confidence": candidate.get("confidence"),
        "candidate_title": candidate.get("candidate_title"),
        "program_name": candidate.get("program_name"),
        "department": candidate.get("department"),
        "extraction_status": "fetched",
        "records_extracted": 0,
        "extractors_used": [],
    }
    if response.status_code >= 400:
        meta["extraction_status"] = "http_error"
        return [], meta
    soup = BeautifulSoup(response.text, "lxml")
    rows_by_extractor = [
        ("bio_component", extract_bio_cards(soup, candidate, meta["source_key"], url)),
        ("profile_component", extract_profiles(soup, candidate, meta["source_key"], url)),
        ("accordion_header", extract_accordion_headers(soup, candidate, meta["source_key"], url)),
        ("heading_name_list", extract_heading_name_lists(soup, candidate, meta["source_key"], url)),
    ]
    records = []
    seen = set()
    for extractor, rows in rows_by_extractor:
        if rows:
            meta["extractors_used"].append(extractor)
        for row in rows:
            dedupe_key = (row["name"].lower(), row["program"].lower(), row["training_year_label"].lower())
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            records.append(row)
    meta["records_extracted"] = len(records)
    meta["extraction_status"] = "records_extracted" if records else "no_supported_person_structure"
    return records, meta


def write_outputs(records: list[dict], sources: list[dict], skipped: list[dict]) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "penn_gme_gap_roster_people.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "penn_gme_gap_roster_sources.json").write_text(
        json.dumps(sources, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    fields = sorted({key for row in records for key in row})
    with (ARTIFACTS / "penn_gme_gap_roster_people.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sources_attempted": len(sources),
        "sources_with_records": sum(1 for source in sources if source.get("records_extracted", 0)),
        "skipped_already_captured_sources": len(skipped),
        "person_records": len(records),
        "unique_names": len({row["name"].lower() for row in records}),
        "by_role": dict(sorted(Counter(row.get("role", "") for row in records).items())),
        "by_program": dict(sorted(Counter(row.get("program", "") for row in records).items())),
        "by_extraction_status": dict(sorted(Counter(row.get("extraction_status", "") for row in sources).items())),
        "skipped_sources": skipped,
    }
    (ARTIFACTS / "penn_gme_gap_roster_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    conn = sqlite3.connect(DB)
    captured_urls = existing_roster_urls(conn)
    candidates = queue_candidates(conn, limit=None)
    conn.close()
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-gme-gap-roster-scraper/0.1"
    records = []
    sources = []
    skipped = []
    for candidate in candidates:
        url = candidate["candidate_url"].rstrip("/")
        if "students-fellows" in url:
            skipped.append(
                {
                    "candidate_url": url,
                    "candidate_title": candidate.get("candidate_title"),
                    "program_name": candidate.get("program_name"),
                    "reason": "student_fellows_directory_not_gme_roster",
                }
            )
            continue
        if url in captured_urls:
            skipped.append(
                {
                    "candidate_url": url,
                    "candidate_title": candidate.get("candidate_title"),
                    "program_name": candidate.get("program_name"),
                    "reason": "already_loaded_as_official_roster_source",
                }
            )
            continue
        rows, meta = parse_candidate(session, candidate)
        records.extend(rows)
        sources.append(meta)
    write_outputs(records, sources, skipped)
    print(
        json.dumps(
            {
                "sources_attempted": len(sources),
                "sources_with_records": sum(1 for source in sources if source.get("records_extracted", 0)),
                "records": len(records),
                "skipped": len(skipped),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
