#!/usr/bin/env python3
"""Extract official Penn faculty-biosketch bridge candidates for attending trends."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
import warnings
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin


DEPS_PATH = Path(os.environ.get("PENN_CORPUS_DEPS", "/tmp/penn_corpus_deps"))
if DEPS_PATH.exists():
    sys.path.insert(0, str(DEPS_PATH))

try:
    import requests
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing scraper dependency. Install with: "
        "python3 -m pip install --target /tmp/penn_corpus_deps -r requirements.txt"
    ) from exc

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"
GROUPS_CSV = ARTIFACTS / "attending_trend_linkage_groups.csv"

CSV_PATH = ARTIFACTS / "attending_biosketch_bridge_candidates.csv"
JSON_PATH = ARTIFACTS / "attending_biosketch_bridge_candidates.json"
OBSERVATION_CSV = ARTIFACTS / "attending_biosketch_source_observations.csv"
SUMMARY_PATH = ARTIFACTS / "attending_biosketch_bridge_summary.json"

DEFAULT_INDEX_URLS = [
    "https://www.med.upenn.edu/apps/faculty/index.php/g353",
]

PENN_TERMS = [
    "University of Pennsylvania",
    "Hospital of the University of Pennsylvania",
    "Perelman School of Medicine",
    "Pennsylvania Hospital",
    "Penn Medicine",
    "CHOP",
    "Children's Hospital of Philadelphia",
    "Children’s Hospital of Philadelphia",
]

TRAINING_TERMS = [
    "Fellow",
    "Fellowship",
    "Resident",
    "Residency",
    "Intern",
    "Internship",
    "Post-doctoral Fellow",
    "Postdoctoral Fellow",
]

FIELDNAMES = [
    "candidate_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "source_url",
    "source_title",
    "source_scope",
    "bridge_status",
    "bridge_assurance_level",
    "training_line",
    "training_type",
    "organization_name",
    "start_year",
    "end_year",
    "ten_year_trend_window",
    "confidence",
    "required_next_evidence",
    "evidence_json",
    "audited_at",
]


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def clean_name(name: str) -> str:
    value = re.sub(r"\b(MD|MSEd|MSCE|MBE|PhD|DO|MBA|MPH|MSc|MA|MS|MHS)\b\.?", "", name, flags=re.I)
    value = re.sub(r"[^A-Za-z0-9]+", " ", value).strip().lower()
    return norm(value)


def name_tokens(name: str) -> list[str]:
    return clean_name(name).split()


def compatible_name(left: str, right: str) -> bool:
    left_clean = clean_name(left)
    right_clean = clean_name(right)
    if not left_clean or not right_clean:
        return False
    if left_clean == right_clean:
        return True
    left_tokens = left_clean.split()
    right_tokens = right_clean.split()
    return len(left_tokens) >= 2 and len(right_tokens) >= 2 and left_tokens[0] == right_tokens[0] and left_tokens[-1] == right_tokens[-1]


def detail_links_for_target(target_key: str, links: dict[str, list[dict]]) -> list[dict]:
    matches = []
    for link_key, values in links.items():
        if compatible_name(target_key, link_key):
            for value in values:
                match_type = "exact_clean_name" if clean_name(target_key) == clean_name(link_key) else "first_last_name"
                matches.append({**value, "faculty_name_match_type": match_type, "faculty_index_clean_name": link_key})
    return matches


def slug_key(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def fetch(session: requests.Session, url: str) -> dict:
    observed_at = datetime.now(timezone.utc).isoformat()
    try:
        response = session.get(url, timeout=30)
        html = response.text if "text/html" in response.headers.get("content-type", "") else ""
        soup = BeautifulSoup(html, "lxml") if html else BeautifulSoup("", "lxml")
        return {
            "url": url,
            "observed_at": observed_at,
            "status": response.status_code,
            "effective_url": response.url,
            "content_type": response.headers.get("content-type", ""),
            "html": html,
            "soup": soup,
            "title": norm(soup.title.get_text(" ")) if soup.title else "",
            "error": "",
        }
    except requests.RequestException as exc:
        return {
            "url": url,
            "observed_at": observed_at,
            "status": 0,
            "effective_url": "",
            "content_type": "",
            "html": "",
            "soup": BeautifulSoup("", "lxml"),
            "title": "",
            "error": f"{type(exc).__name__}: {str(exc)[:240]}",
        }


def read_target_groups(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    targets = []
    for row in rows:
        if row.get("has_current_attending_endpoint") != "1":
            continue
        if row.get("has_penn_training_claim") != "1" and "penn_training" not in row.get("best_linkage_status", ""):
            continue
        targets.append(row)
    return sorted(
        targets,
        key=lambda row: (-int(row.get("best_trend_link_assurance_level") or 0), row.get("display_name") or ""),
    )


def faculty_links(index_payloads: list[dict]) -> tuple[dict[str, list[dict]], list[dict]]:
    links: dict[str, list[dict]] = {}
    observations = []
    for payload in index_payloads:
        observations.append(
            {
                "source_url": payload["url"],
                "source_scope": "faculty_index",
                "observed_at": payload["observed_at"],
                "http_status": payload["status"],
                "effective_url": payload["effective_url"],
                "title": payload["title"],
                "content_type": payload["content_type"],
                "candidate_link_count": 0,
                "error": payload["error"],
                "sha256": sha256_text(payload["html"]) if payload["html"] else "",
            }
        )
        if payload["status"] != 200:
            continue
        count = 0
        for anchor in payload["soup"].select("a[href]"):
            label = norm(anchor.get_text(" "))
            href = anchor.get("href") or ""
            if not label or "/apps/faculty/index.php/" not in urljoin(payload["url"], href):
                continue
            full_url = urljoin(payload["url"], href)
            key = clean_name(label)
            if not key:
                continue
            links.setdefault(key, []).append({"label": label, "url": full_url, "index_url": payload["url"]})
            count += 1
        observations[-1]["candidate_link_count"] = count
    return links, observations


def text_lines(payload: dict) -> list[str]:
    return [norm(line) for line in payload["soup"].get_text("\n").splitlines() if norm(line)]


def postgrad_training_lines(lines: list[str]) -> list[str]:
    try:
        start = lines.index("Post-Graduate Training") + 1
    except ValueError:
        return []
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index] in {"Certifications", "Permanent link", "Selected Publications"}:
            end = index
            break
    raw = lines[start:end]
    output = []
    current = ""
    for line in raw:
        if not line:
            continue
        if line.startswith(",") or re.fullmatch(r"\d{4}(?:-\d{4})?\.?", line):
            current = norm(f"{current} {line}")
            continue
        if current:
            output.append(clean_training_line(current))
        current = line
    if current:
        output.append(clean_training_line(current))
    return [line for line in output if any(term.lower() in line.lower() for term in TRAINING_TERMS)]


def clean_training_line(line: str) -> str:
    line = re.sub(r"\s+,", ",", norm(line))
    line = re.sub(r"\s+\.", ".", line)
    return line.strip(" .") + "."


def training_type(line: str) -> str:
    lower = line.lower()
    if "post-doctoral" in lower or "postdoctoral" in lower:
        return "postdoctoral"
    if "fellow" in lower:
        return "fellowship"
    if "residen" in lower:
        return "residency"
    if "intern" in lower:
        return "internship"
    return "training"


def penn_organization(line: str) -> str:
    for term in PENN_TERMS:
        if term.lower() in line.lower():
            return term
    return ""


def year_range(line: str) -> tuple[int | None, int | None]:
    ranges = re.findall(r"\b(19\d{2}|20\d{2})\s*[-–]\s*(19\d{2}|20\d{2})\b", line)
    if ranges:
        start, end = ranges[-1]
        return int(start), int(end)
    years = [int(year) for year in re.findall(r"\b(19\d{2}|20\d{2})\b", line)]
    if years:
        return min(years), max(years)
    return None, None


def ten_year_window(end_year: int | None, as_of_year: int) -> str:
    if end_year is None:
        return "unknown"
    return "yes" if end_year >= as_of_year - 10 else "no"


def classify_bridge(line: str, as_of_year: int) -> tuple[str, int, float, str]:
    org = penn_organization(line)
    start_year, end_year = year_range(line)
    if org and training_type(line) == "postdoctoral":
        return (
            "official_biosketch_research_training_context",
            2,
            0.72,
            "Use as research-training context only; do not count as GME trainee-to-attending trend bridge.",
        )
    if org and end_year and ten_year_window(end_year, as_of_year) == "yes":
        return (
            "dated_recent_official_biosketch_training_bridge_candidate",
            3,
            0.9,
            "Review official biosketch line against current endpoint before accepting trend link.",
        )
    if org and end_year:
        return (
            "dated_official_biosketch_training_bridge_candidate",
            3,
            0.88,
            "Review official biosketch line; dated Penn training is outside the ten-year trend window.",
        )
    if org:
        return (
            "undated_official_biosketch_training_context",
            2,
            0.72,
            "Find date range before using for trend timing.",
        )
    return (
        "non_penn_training_context",
        1,
        0.5,
        "Use as background only unless another source links Penn training.",
    )


def build_candidates(
    session: requests.Session,
    targets: list[dict],
    links: dict[str, list[dict]],
    as_of_year: int,
) -> tuple[list[dict], list[dict]]:
    candidates = []
    observations = []
    seen_urls = set()
    for target in targets:
        target_key = clean_name(target.get("display_name") or target.get("event_group_key") or "")
        detail_links = detail_links_for_target(target_key, links)
        for detail in detail_links:
            if detail["url"] in seen_urls:
                continue
            seen_urls.add(detail["url"])
            payload = fetch(session, detail["url"])
            lines = text_lines(payload)
            training_lines = postgrad_training_lines(lines)
            observations.append(
                {
                    "source_url": payload["url"],
                    "source_scope": "faculty_biosketch",
                    "observed_at": payload["observed_at"],
                    "http_status": payload["status"],
                    "effective_url": payload["effective_url"],
                    "title": payload["title"],
                    "content_type": payload["content_type"],
                    "candidate_link_count": "",
                    "error": payload["error"],
                    "sha256": sha256_text(payload["html"]) if payload["html"] else "",
                    "matched_event_group_key": target.get("event_group_key") or "",
                    "matched_display_name": target.get("display_name") or "",
                    "training_line_count": len(training_lines),
                }
            )
            for line in training_lines:
                status, assurance, confidence, required = classify_bridge(line, as_of_year)
                start_year, end_year = year_range(line)
                org = penn_organization(line)
                evidence = {
                    "faculty_index_url": detail["index_url"],
                    "faculty_index_label": detail["label"],
                    "faculty_name_match_type": detail.get("faculty_name_match_type", ""),
                    "faculty_index_clean_name": detail.get("faculty_index_clean_name", ""),
                    "source_sha256": observations[-1]["sha256"],
                    "source_last_updated": next((item for item in lines if item.lower().startswith("last updated:")), ""),
                    "target_best_linkage_status": target.get("best_linkage_status") or "",
                    "target_required_next_evidence": target.get("best_required_next_evidence") or "",
                }
                candidates.append(
                    {
                        "candidate_key": slug_key(
                            "attending_biosketch_bridge",
                            f"{target.get('event_group_key')}:{payload['url']}:{line}",
                        ),
                        "event_group_key": target.get("event_group_key") or "",
                        "display_name": target.get("display_name") or detail["label"],
                        "normalized_name": target.get("normalized_name") or target_key,
                        "source_url": payload["url"],
                        "source_title": payload["title"],
                        "source_scope": "official_penn_faculty_biosketch",
                        "bridge_status": status,
                        "bridge_assurance_level": assurance,
                        "training_line": line,
                        "training_type": training_type(line),
                        "organization_name": org,
                        "start_year": start_year or "",
                        "end_year": end_year or "",
                        "ten_year_trend_window": ten_year_window(end_year, as_of_year),
                        "confidence": confidence,
                        "required_next_evidence": required,
                        "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
                        "audited_at": "",
                    }
                )
    return candidates, observations


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM attending_biosketch_bridge_candidates")
    for row in rows:
        conn.execute(
            """
            INSERT INTO attending_biosketch_bridge_candidates
            (candidate_key, event_group_key, display_name, normalized_name,
             source_url, source_title, source_scope, bridge_status,
             bridge_assurance_level, training_line, training_type, organization_name,
             start_year, end_year, ten_year_trend_window, confidence,
             required_next_evidence, evidence_json, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row[field] for field in FIELDNAMES),
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--groups-csv", type=Path, default=GROUPS_CSV)
    parser.add_argument("--index-url", action="append", dest="index_urls")
    parser.add_argument("--as-of-year", type=int, default=2026)
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = "redmank-attending-biosketch-bridge-audit/0.1"
    targets = read_target_groups(args.groups_csv)
    index_urls = args.index_urls or DEFAULT_INDEX_URLS
    index_payloads = [fetch(session, url) for url in index_urls]
    links, observations = faculty_links(index_payloads)
    candidates, detail_observations = build_candidates(session, targets, links, args.as_of_year)
    observations.extend(detail_observations)
    audited_at = datetime.now(timezone.utc).isoformat()
    for row in candidates:
        row["audited_at"] = audited_at

    candidates = sorted(
        candidates,
        key=lambda row: (
            row["event_group_key"],
            -int(row["bridge_assurance_level"]),
            row["source_url"],
            row["training_line"],
        ),
    )
    write_csv(CSV_PATH, candidates, FIELDNAMES)
    JSON_PATH.write_text(json.dumps(candidates, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    observation_fields = [
        "source_url",
        "source_scope",
        "observed_at",
        "http_status",
        "effective_url",
        "title",
        "content_type",
        "candidate_link_count",
        "error",
        "sha256",
        "matched_event_group_key",
        "matched_display_name",
        "training_line_count",
    ]
    for observation in observations:
        for field in observation_fields:
            observation.setdefault(field, "")
    write_csv(OBSERVATION_CSV, observations, observation_fields)

    conn = sqlite3.connect(args.db)
    with conn:
        write_sqlite(conn, candidates)
    conn.close()

    summary = {
        "generated_at": audited_at,
        "as_of_year": args.as_of_year,
        "target_groups": len(targets),
        "index_urls": index_urls,
        "source_observation_rows": len(observations),
        "candidate_rows": len(candidates),
        "groups_with_candidates": len({row["event_group_key"] for row in candidates}),
        "groups_with_recent_dated_bridge_candidates": len(
            {
                row["event_group_key"]
                for row in candidates
                if row["bridge_status"] == "dated_recent_official_biosketch_training_bridge_candidate"
            }
        ),
        "by_bridge_status": dict(sorted(Counter(row["bridge_status"] for row in candidates).items())),
        "by_ten_year_trend_window": dict(sorted(Counter(row["ten_year_trend_window"] for row in candidates).items())),
        "by_training_type": dict(sorted(Counter(row["training_type"] for row in candidates).items())),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "observation_csv": str(OBSERVATION_CSV.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
