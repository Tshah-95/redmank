#!/usr/bin/env python3
"""Audit captured Penn trainee programs against the public HUP GME program list."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
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
HUP_GME_PROGRAMS_URL = (
    "https://www3.pennmedicine.org/for-health-care-professionals/fellowship-and-residency-programs/"
    "hospital-of-the-university-of-pennsylvania/hup-gme/programs"
)

PROGRAM_ALIASES = {
    ("residency", "internal medicine - categorical"): ["Internal Medicine Residency"],
    ("residency", "internal medicine - dermatology"): ["Combined Internal Medicine-Dermatology Residency"],
    ("residency", "internal medicine - pediatrics"): ["Penn-CHOP Internal Medicine-Pediatrics Residency"],
    ("residency", "radiology - diagnostic"): ["Diagnostic Radiology Residency"],
    ("residency", "radiology - interventional integrated"): ["Interventional Radiology Integrated Residency"],
    ("residency", "radiology - interventional independent"): ["Interventional Radiology Independent Residency"],
    ("residency", "plastic surgery - integrated"): ["Plastic Surgery Residency"],
    ("residency", "thoracic surgery - integrated"): ["Cardiothoracic Surgery Residency"],
    ("residency", "vascular surgery integrated"): ["Vascular Surgery Integrated Residency"],
    ("fellowship", "abdominal radiology"): ["Abdominal Imaging Fellowship"],
    ("fellowship", "adult congenital heart disease"): ["Adult Congenital Heart Disease Fellowship"],
    ("fellowship", "advanced heart failure transplant cardiology"): [
        "Advanced Heart Failure Transplant Cardiology Fellowship"
    ],
    ("fellowship", "allergy and immunology"): ["Allergy and Immunology Fellowship"],
    ("fellowship", "cardiovascular disease"): ["Cardiovascular Disease Fellowship"],
    ("fellowship", "clinical cardiac electrophysiology"): ["Clinical Cardiac Electrophysiology Fellowship"],
    ("fellowship", "endocrinology"): ["Endocrinology, Diabetes and Metabolism Fellowship"],
    ("fellowship", "gastroenterology"): ["Gastroenterology and Hepatology Fellowship"],
    ("fellowship", "geriatric medicine"): ["Geriatric Medicine Fellowship"],
    ("fellowship", "hematology and oncology"): ["Hematology/Oncology Fellowship"],
    ("fellowship", "hospice and palliative medicine"): ["Hospice and Palliative Medicine Fellowship"],
    ("fellowship", "infectious disease"): ["Infectious Diseases Fellowship"],
    ("fellowship", "interventional cardiology"): ["Interventional Cardiology Fellowship"],
    ("fellowship", "nephrology"): ["Nephrology Fellowship"],
    ("fellowship", "neuroradiology"): ["Neuroradiology Fellowship"],
    ("fellowship", "nuclear radiology"): ["Nuclear Radiology Fellowship"],
    ("fellowship", "ophthalmology"): ["Ophthalmology Fellowship"],
    ("fellowship", "pulmonary disease and critical care medicine"): ["Pulmonary and Critical Care Fellowship"],
    ("fellowship", "rheumatology"): ["Rheumatology Fellowship"],
    ("fellowship", "thoracic surgery - cardiac track"): ["Thoracic Surgery Fellowship - Cardiac Track"],
    ("fellowship", "trauma and surgical critical care"): ["Trauma and Surgical Critical Care Fellowship"],
    ("fellowship", "vascular surgery"): ["Vascular Surgery Fellowship"],
}


def alias_lookup() -> dict[tuple[str, str], list[str]]:
    lookup = {}
    for (program_type, official_name), aliases in PROGRAM_ALIASES.items():
        lookup[(program_type, normalize_program_name(official_name))] = aliases
    return lookup


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).replace("\xa0", " ")).strip()


def normalize_program_name(value: str) -> str:
    value = norm(value).lower().replace("&", " and ")
    value = value.replace("/", " and ")
    value = re.sub(r"\b(integrated|independent)\(.*?\)", r"\1", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\b(program|residency|fellowship|fellowships|residencies)\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def entry_key(department: str, program_type: str, program_name: str) -> str:
    digest = hashlib.sha1(f"{department}:{program_type}:{program_name}".encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_program_name(program_name)).strip("-")[:48]
    return f"hup_gme_{program_type}_{slug}_{digest}"


def split_cell_programs(cell, program_type: str, department: str) -> list[dict]:
    links = [a for a in cell.select("a") if norm(a.get_text(" "))]
    if links:
        return [
            {
                "entry_key": entry_key(department, program_type, norm(link.get_text(" "))),
                "source_url": HUP_GME_PROGRAMS_URL,
                "program_url": urljoin(HUP_GME_PROGRAMS_URL, link.get("href", "")),
                "sponsoring_institution": "Hospital of the University of Pennsylvania",
                "department": department,
                "program_type": program_type,
                "program_name": norm(link.get_text(" ")),
                "source_type": "official_hup_gme_program_list",
                "confidence": 0.95,
                "evidence": {"origin": "hup_gme_programs_table_link"},
            }
            for link in links
        ]
    text = norm(cell.get_text("\n"))
    records = []
    for raw_line in text.splitlines():
        program_name = norm(raw_line)
        if not program_name:
            continue
        records.append(
            {
                "entry_key": entry_key(department, program_type, program_name),
                "source_url": HUP_GME_PROGRAMS_URL,
                "program_url": "",
                "sponsoring_institution": "Hospital of the University of Pennsylvania",
                "department": department,
                "program_type": program_type,
                "program_name": program_name,
                "source_type": "official_hup_gme_program_list",
                "confidence": 0.85,
                "evidence": {"origin": "hup_gme_programs_table_text"},
            }
        )
    return records


def fetch_official_programs() -> tuple[list[dict], dict]:
    session = requests.Session()
    session.headers["User-Agent"] = "redmank-penn-gme-program-coverage/0.1"
    response = session.get(HUP_GME_PROGRAMS_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table")
    if not table:
        raise SystemExit("Could not find HUP GME program table")
    records = []
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all(["td", "th"])
        if len(cells) < 3:
            continue
        department = norm(cells[0].get_text(" "))
        records.extend(split_cell_programs(cells[1], "residency", department))
        records.extend(split_cell_programs(cells[2], "fellowship", department))
    source = {
        "source_key": "hup_gme_programs",
        "url": HUP_GME_PROGRAMS_URL,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code,
        "effective_url": response.url,
        "sha256": hashlib.sha256(response.text.encode("utf-8")).hexdigest(),
        "source_type": "official_hup_gme_program_list",
    }
    return records, source


def captured_programs(conn: sqlite3.Connection) -> dict[tuple[str, str], dict]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT pr.program_key, pr.program_name, p.role, COUNT(DISTINCT p.person_key) AS people_count
        FROM programs pr
        JOIN person_program_memberships m ON m.program_key = pr.program_key
        JOIN people p ON p.person_key = m.person_key
        WHERE p.role IN ('resident', 'fellow')
        GROUP BY pr.program_key, pr.program_name, p.role
        """
    ).fetchall()
    result = {}
    for row in rows:
        program_type = "residency" if row["role"] == "resident" else "fellowship"
        key = (program_type, normalize_program_name(row["program_name"]))
        current = result.get(key)
        payload = {
            "program_key": row["program_key"],
            "program_name": row["program_name"],
            "people_count": row["people_count"],
        }
        if not current or payload["people_count"] > current["people_count"]:
            result[key] = payload
    return result


def discovery_index(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT source_url, title, classification, source_type
            FROM sources
            WHERE source_type IN ('source_discovery', 'penn_affiliated_source_discovery')
            """
        )
    ]


def source_discovery_hit(entry: dict, discoveries: list[dict]) -> dict | None:
    program_url = entry.get("program_url") or ""
    program_norm = normalize_program_name(entry["program_name"])
    for row in discoveries:
        url = row.get("source_url") or ""
        title = row.get("title") or ""
        if program_url and url.rstrip("/") == program_url.rstrip("/"):
            return row
        if program_norm and program_norm in normalize_program_name(f"{title} {url}"):
            return row
    return None


def audit_coverage(records: list[dict]) -> tuple[list[dict], dict]:
    conn = sqlite3.connect(DB)
    captured = captured_programs(conn)
    discoveries = discovery_index(conn)
    aliases_by_key = alias_lookup()
    audit_rows = []
    for record in records:
        aliases = aliases_by_key.get((record["program_type"], normalize_program_name(record["program_name"])), [])
        match = None
        match_method = ""
        for candidate in [record["program_name"], *aliases]:
            match = captured.get((record["program_type"], normalize_program_name(candidate)))
            if match:
                match_method = "alias" if candidate != record["program_name"] else "normalized_name"
                break
        discovery = source_discovery_hit(record, discoveries)
        if match:
            coverage_status = "covered_current_roster"
            confidence = 0.95 if match_method == "normalized_name" else 0.88
        elif discovery:
            coverage_status = "discovered_no_current_roster"
            confidence = 0.55
        else:
            coverage_status = "not_discovered"
            confidence = 0.2
        audit_rows.append(
            {
                **record,
                "coverage_status": coverage_status,
                "matched_program_key": match["program_key"] if match else "",
                "matched_program_name": match["program_name"] if match else "",
                "captured_people_count": match["people_count"] if match else 0,
                "match_method": match_method or ("source_discovery" if discovery else "none"),
                "match_confidence": confidence,
                "discovery_title": discovery.get("title", "") if discovery else "",
                "discovery_url": discovery.get("source_url", "") if discovery else "",
                "discovery_classification": discovery.get("classification", "") if discovery else "",
                "notes": "Official HUP GME program with current roster capture."
                if match
                else "Official HUP GME program discovered as a page but no current roster people captured."
                if discovery
                else "Official HUP GME program not yet discovered/captured by current Penn source strategy.",
            }
        )
    conn.close()
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_url": HUP_GME_PROGRAMS_URL,
        "programs": len(records),
        "by_program_type": {},
        "by_coverage_status": {},
    }
    for row in audit_rows:
        summary["by_program_type"][row["program_type"]] = summary["by_program_type"].get(row["program_type"], 0) + 1
        summary["by_coverage_status"][row["coverage_status"]] = (
            summary["by_coverage_status"].get(row["coverage_status"], 0) + 1
        )
    return audit_rows, summary


def write_outputs(records: list[dict], source: dict, audit_rows: list[dict], summary: dict) -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "penn_gme_program_universe.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "penn_gme_program_universe_source.json").write_text(
        json.dumps(source, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    fields = [
        "entry_key",
        "sponsoring_institution",
        "department",
        "program_type",
        "program_name",
        "program_url",
        "coverage_status",
        "matched_program_name",
        "captured_people_count",
        "match_method",
        "match_confidence",
        "discovery_classification",
        "discovery_title",
        "discovery_url",
        "notes",
    ]
    with (ARTIFACTS / "penn_gme_program_coverage.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in fields} for row in audit_rows])
    (ARTIFACTS / "penn_gme_program_coverage.json").write_text(
        json.dumps(audit_rows, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "penn_gme_program_coverage_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_sqlite(records: list[dict], source: dict, audit_rows: list[dict]) -> None:
    if not DB.exists():
        return
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            """
            INSERT OR REPLACE INTO sources
            (source_key, source_url, source_type, title, fetched_at, http_status, sha256, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source["source_key"],
                source["url"],
                source["source_type"],
                "HUP GME Programs",
                source.get("fetched_at"),
                source.get("http_status"),
                source.get("sha256"),
                json.dumps(source, ensure_ascii=False, sort_keys=True),
            ),
        )
        conn.execute("DELETE FROM official_program_universe WHERE source_key = ?", (source["source_key"],))
        for record in records:
            conn.execute(
                """
                INSERT INTO official_program_universe
                (official_program_key, source_key, source_url, sponsoring_institution, department,
                 program_type, program_name, program_url, source_type, confidence, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record["entry_key"],
                    source["source_key"],
                    record["source_url"],
                    record["sponsoring_institution"],
                    record["department"],
                    record["program_type"],
                    record["program_name"],
                    record.get("program_url"),
                    record.get("source_type"),
                    record.get("confidence", 0.0),
                    json.dumps(record.get("evidence", {}), ensure_ascii=False, sort_keys=True),
                ),
            )
        audited_at = datetime.now(timezone.utc).isoformat()
        for row in audit_rows:
            conn.execute(
                """
                INSERT OR REPLACE INTO official_program_coverage_audit
                (official_program_key, coverage_status, matched_program_key, matched_program_name,
                 captured_people_count, match_method, match_confidence, discovery_classification,
                 discovery_title, discovery_url, notes, audited_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["entry_key"],
                    row["coverage_status"],
                    row.get("matched_program_key") or None,
                    row.get("matched_program_name"),
                    int(row.get("captured_people_count") or 0),
                    row.get("match_method"),
                    float(row.get("match_confidence") or 0.0),
                    row.get("discovery_classification"),
                    row.get("discovery_title"),
                    row.get("discovery_url"),
                    row.get("notes"),
                    audited_at,
                ),
            )
    conn.close()


def main() -> None:
    records, source = fetch_official_programs()
    audit_rows, summary = audit_coverage(records)
    write_outputs(records, source, audit_rows, summary)
    write_sqlite(records, source, audit_rows)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
