#!/usr/bin/env python3
"""Scrape first-pass Penn cardiology fellowship and IM residency rosters."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import date, datetime, timezone
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


OUT = Path("artifacts/data")
RAW = OUT / "raw"
TODAY = date.today().isoformat()
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "PennTrainingCorpus/0.1 (+public academic roster research; contact: local research agent)"
    }
)


SOURCES = {
    "cardiology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/cardiovascular-disease-fellowship/current-fellows",
        "program": "Cardiovascular Disease Fellowship",
        "unit": "Division of Cardiovascular Medicine",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "cardiology_alumni": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/cardiovascular-disease-fellowship/alumni",
        "program": "Cardiovascular Disease Fellowship",
        "unit": "Division of Cardiovascular Medicine",
        "population": "alumni",
        "role": "alumni",
        "parser": "alumni_note",
    },
    "cardiology_adult_congenital_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/adult-congenital-heart-disease-fellowship",
        "program": "Adult Congenital Heart Disease Fellowship",
        "unit": "Division of Cardiovascular Medicine",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "cardiology_advanced_heart_failure_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/advanced-heart-failure-transplant-cardiology-fellowship",
        "program": "Advanced Heart Failure Transplant Cardiology Fellowship",
        "unit": "Division of Cardiovascular Medicine",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "cardiology_electrophysiology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/electrophysiology-fellowship",
        "program": "Clinical Cardiac Electrophysiology Fellowship",
        "unit": "Division of Cardiovascular Medicine",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "cardiology_interventional_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/interventional-fellowship",
        "program": "Interventional Cardiology Fellowship",
        "unit": "Division of Cardiovascular Medicine",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "cardiology_cardio_oncology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/cardio-oncology-fellowship-program",
        "program": "Cardio-Oncology Fellowship",
        "unit": "Division of Cardiovascular Medicine",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "cardiology_advanced_imaging_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/advanced-imaging-cardiology-fellowship",
        "program": "Advanced Noninvasive Cardiac Imaging Fellowship",
        "unit": "Division of Cardiovascular Medicine",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "endocrinology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-endocrinology-diabetes-and-metabolism/education-and-training/endcrinology-fellowship-programs/fellows",
        "program": "Endocrinology, Diabetes and Metabolism Fellowship",
        "unit": "Division of Endocrinology, Diabetes and Metabolism",
        "population": "current_fellows_and_recent_graduates",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "gastroenterology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/gastroenterology/education-and-training/fellowship-programs/gastroenterology-and-hepatology-fellow-profiles",
        "program": "Gastroenterology and Hepatology Fellowship",
        "unit": "Division of Gastroenterology",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "gastroenterology_advanced_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/gastroenterology/education-and-training/fellowship-programs/advanced-gastroenterology-fellows",
        "program": "Advanced Gastroenterology and Hepatology Fellowship",
        "unit": "Division of Gastroenterology",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "geriatrics_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/geriatrics/education-and-training/fellowship-program/our-fellows",
        "program": "Geriatric Medicine Fellowship",
        "unit": "Division of Geriatrics",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "hematology_oncology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/hematology-and-oncology/education-and-training/hematology-oncology-fellowship/fellows",
        "program": "Hematology/Oncology Fellowship",
        "unit": "Division of Hematology and Oncology",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "infectious_diseases_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/infectious-diseases/education-and-training/fellowship-program/current-fellows",
        "program": "Infectious Diseases Fellowship",
        "unit": "Division of Infectious Diseases",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "pulmonary_critical_care_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/pulmonology-allergy-and-critical-care/education-and-training/fellowship-offerings/fellows",
        "program": "Pulmonary and Critical Care Fellowship",
        "unit": "Division of Pulmonary, Allergy and Critical Care",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "allergy_immunology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/pulmonology-allergy-and-critical-care/allergy-and-immunology/allergy-immunology-fellowship/fellows",
        "program": "Allergy and Immunology Fellowship",
        "unit": "Division of Pulmonary, Allergy and Critical Care",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "nephrology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/renal-electrolyte-and-hypertension-division/education-and-training/fellowship-programs/nephrology-fellows",
        "program": "Nephrology Fellowship",
        "unit": "Division of Renal Electrolyte and Hypertension",
        "population": "current_fellows_and_research_trainees",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "rheumatology_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/rheumatology/education-and-training/fellowship-programs/current-fellows",
        "program": "Rheumatology Fellowship",
        "unit": "Division of Rheumatology",
        "population": "current_fellows_and_postdocs",
        "role": "fellow",
        "parser": "penn_bio",
    },
    "palliative_current_fellows": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/program-in-palliative-care/education-and-training/fellowship-program-in-hospice-and-palliative-medicine/current-fellows",
        "program": "Hospice and Palliative Medicine Fellowship",
        "unit": "Program in Palliative Care",
        "population": "current_fellows",
        "role": "fellow",
        "parser": "palliative_prose",
    },
    "internal_medicine_categorical": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/categorical/categorical-residents",
        "program": "Internal Medicine Residency",
        "unit": "Department of Medicine",
        "population": "categorical_residents",
        "role": "resident",
        "parser": "penn_bio",
    },
    "internal_medicine_physician_scientist": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/physician-scientist-pathway/physician-scientist-residents",
        "program": "Internal Medicine Physician-Scientist Pathway",
        "unit": "Department of Medicine",
        "population": "physician_scientist_pathway_residents",
        "role": "resident",
        "parser": "penn_bio",
    },
    "internal_medicine_primary_care": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/primary-care-program/primary-care-residents",
        "program": "Internal Medicine Primary Care Residency",
        "unit": "Department of Medicine",
        "population": "primary_care_residents",
        "role": "resident",
        "parser": "penn_bio",
    },
    "internal_medicine_med_derm": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/combined-internal-medicine-dermatology-program/medicine-dermatology-residents",
        "program": "Combined Internal Medicine-Dermatology Residency",
        "unit": "Department of Medicine",
        "population": "medicine_dermatology_residents",
        "role": "resident",
        "parser": "penn_bio",
    },
    "internal_medicine_medical_education": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/medical-education/medical-education-residents",
        "program": "Internal Medicine Residency - Medical Education Leadership Track",
        "unit": "Department of Medicine",
        "population": "medical_education_track_residents",
        "role": "resident",
        "parser": "penn_bio",
    },
    "internal_medicine_healthcare_quality": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/healthcare-quality-in-leadership/healthcare-leadership-in-quality-residents",
        "program": "Internal Medicine Residency - Healthcare Leadership in Quality Track",
        "unit": "Department of Medicine",
        "population": "healthcare_leadership_quality_track_residents",
        "role": "resident",
        "parser": "penn_bio",
    },
    "internal_medicine_global_health_equities": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/global-health/global-health-equities-residents",
        "program": "Internal Medicine Residency - Global Health Equities Track",
        "unit": "Department of Medicine",
        "population": "global_health_equities_track_residents",
        "role": "resident",
        "parser": "penn_bio",
    },
    "internal_medicine_med_peds": {
        "url": "https://www.chop.edu/med-peds-residency/current-residents",
        "program": "Penn-CHOP Internal Medicine-Pediatrics Residency",
        "unit": "Department of Medicine / CHOP",
        "population": "medicine_pediatrics_residents",
        "role": "resident",
        "parser": "chop_med_peds",
    },
    "internal_medicine_faq": {
        "url": "https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/application-information/faqs",
        "program": "Internal Medicine Residency",
        "unit": "Department of Medicine",
        "population": "program_metadata",
        "role": "metadata",
        "parser": "faq_note",
    },
}


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def fetch(key: str, url: str) -> tuple[str, dict]:
    response = SESSION.get(url, timeout=30)
    meta = {
        "source_key": key,
        "url": url,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "http_status": response.status_code,
        "effective_url": response.url,
    }
    response.raise_for_status()
    body = response.text
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    meta["sha256"] = digest
    (RAW / f"{key}.html").write_text(redact_html(body), encoding="utf-8")
    return body, meta


def redact_html(html: str) -> str:
    html = re.sub(
        r'(configureCloudV2Endpoint\(\s*"[^"]+"\s*,\s*")[^"]+(")',
        r"\1[REDACTED_COVEO_API_KEY]\2",
        html,
    )
    html = re.sub(r"mailto:[^\"' <>\n]+", "mailto:[REDACTED_EMAIL]", html)
    return redact_text(html)


def redact_text(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


def absolute(base: str, maybe_url: str | None) -> str:
    if not maybe_url:
        return ""
    return urljoin(base, maybe_url)


def parse_info_sets(bio) -> dict:
    fields = {}
    for span in bio.select(".bio__info-set"):
        key_node = span.select_one(".bio__info-key")
        if not key_node:
            continue
        key = norm(key_node.get_text()).rstrip(":").lower().replace(" ", "_")
        if key == "email":
            continue
        key_node.extract()
        value = norm(span.get_text())
        if value:
            fields[key] = value
    return fields


def parse_penn_bio_page(source_key: str, html: str, source: dict) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for group in soup.select(".bio-list"):
        heading = group.find(["h1", "h2"], recursive=False)
        label = norm(heading.get_text()) if heading else ""
        if not label:
            section = group.find_parent("section", class_="tabs__content")
            mobile_heading = section.select_one(".tabs__toggle--mobile") if section else None
            if not mobile_heading:
                mobile_heading = group.find_previous(["h1", "h2"])
            label = norm(mobile_heading.get_text()) if mobile_heading else ""
        if should_skip_group(label):
            continue
        for bio in group.select(".bio"):
            name_node = bio.select_one(".bio__name")
            if not name_node:
                continue
            profile = bio.select_one('a[href*="residents/"], a[href*="fellows/"]')
            image = bio.select_one("img")
            fields = parse_info_sets(bio)
            record = {
                "source_key": source_key,
                "source_url": source["url"],
                "source_type": "official_roster",
                "institution": "University of Pennsylvania / Penn Medicine",
                "unit": source["unit"],
                "program": source["program"],
                "population": source["population"],
                "role": source["role"],
                "training_year_label": label,
                "current_status": infer_current_status(label),
                "name": norm(name_node.get_text()),
                "profile_url": absolute(source["url"], profile.get("href") if profile else ""),
                "headshot_url": absolute(source["url"], image.get("src") if image else ""),
                "headshot_alt": norm(image.get("alt") if image else ""),
                "extraction_method": "penn_medicine_bio_component",
                "quality_tier": "high" if fields else "medium",
                "quality_notes": [],
            }
            record.update(fields)
            expected = ["medical_school"]
            if source_key == "cardiology_current_fellows":
                expected.append("residency_program")
            missing = [field for field in expected if not record.get(field)]
            if missing:
                record["quality_notes"].append(f"missing_expected_fields:{','.join(missing)}")
            if not record["profile_url"]:
                record["quality_notes"].append("no_individual_profile_link_on_roster")
            rows.append(record)
    return rows


def should_skip_group(label: str) -> bool:
    normalized = label.lower()
    skip_tokens = [
        "program director",
        "program directors",
        "associate program director",
        "faculty and staff",
        "leadership",
        "instructor",
    ]
    return any(token in normalized for token in skip_tokens)


def infer_current_status(label: str) -> str:
    normalized = label.lower()
    if any(token in normalized for token in ["past", "previous", "alumni", "recent graduate", "graduates"]):
        return "former"
    if "chief resident" in normalized:
        return "chief"
    return "current"


def infer_med_school_from_bio(text: str) -> tuple[str, str]:
    patterns = [
        r"(?:attended|went to|comes to us from|come to us from) ([^.]+?(?:School of Medicine|College of Medicine|Medical School|Medicine|University|College))",
        r"At ([^.]+?(?:School of Medicine|College of Medicine|Medical School|Medicine)),",
        r"from ([^.]+?(?:School of Medicine|College of Medicine|Medical School|Medicine)),",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return norm(match.group(1)), "regex_inferred_from_bio"
    return "", ""


def parse_chop_med_peds(source_key: str, html: str, source: dict) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    content = soup.select_one("chop-styled-text") or soup.select_one(".block-node\\:page\\:body")
    rows = []
    current_year = ""
    if not content:
        return rows
    for node in content.find_all(["h2", "p"]):
        if node.name == "h2":
            current_year = norm(node.get_text())
            continue
        strong = node.find("strong")
        if not strong:
            continue
        raw_name = norm(strong.get_text())
        if not raw_name:
            continue
        bio_text = norm(node.get_text(" "))
        bio_text = norm(bio_text.removeprefix(raw_name))
        pronouns = ""
        pronoun_match = re.search(r"\(([^)]*/[^)]*)\)", raw_name)
        if pronoun_match:
            pronouns = pronoun_match.group(1)
        med_school, method = infer_med_school_from_bio(bio_text)
        image = node.find_previous("img")
        rows.append(
            {
                "source_key": source_key,
                "source_url": source["url"],
                "source_type": "official_roster",
                "institution": "University of Pennsylvania / CHOP",
                "unit": source["unit"],
                "program": source["program"],
                "population": source["population"],
                "role": source["role"],
                "training_year_label": current_year,
                "current_status": infer_current_status(current_year),
                "name": re.sub(r"\s*\([^)]*/[^)]*\)", "", raw_name).strip(),
                "pronouns": pronouns,
                "bio_text": bio_text,
                "medical_school": med_school,
                "medical_school_extraction_method": method,
                "profile_url": "",
                "headshot_url": absolute(source["url"], image.get("src") if image else ""),
                "headshot_alt": norm(image.get("alt") if image else ""),
                "extraction_method": "chop_prose_profile_page",
                "quality_tier": "medium",
                "quality_notes": ["prose_not_fielded_roster"],
            }
        )
    return rows


def parse_palliative_prose(source_key: str, html: str, source: dict) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main") or soup.body
    rows = []
    current_year = ""
    if not main:
        return rows
    for node in main.find_all(["h2", "p"]):
        if node.name == "h2":
            current_year = norm(node.get_text())
            continue
        name_holder = node.find("strong") or node.find("a", href=True)
        if not name_holder or should_skip_group(current_year):
            continue
        image = name_holder.find("img") or node.find("img")
        raw_name = norm(name_holder.get_text(" "))
        if not raw_name:
            continue
        profile_url = absolute(source["url"], name_holder.get("href")) if name_holder.name == "a" else ""
        text = norm(node.get_text("\n"))
        medical_school = ""
        residency = ""
        med_match = re.search(r"Medical School:\s*([^\n]+)", text)
        res_match = re.search(r"Residency:\s*([^\n]+)", text)
        if med_match:
            medical_school = norm(med_match.group(1))
        if res_match:
            residency = norm(res_match.group(1))
        rows.append(
            {
                "source_key": source_key,
                "source_url": source["url"],
                "source_type": "official_roster",
                "institution": "University of Pennsylvania / Penn Medicine",
                "unit": source["unit"],
                "program": source["program"],
                "population": source["population"],
                "role": source["role"],
                "training_year_label": current_year,
                "current_status": infer_current_status(current_year),
                "name": raw_name,
                "profile_url": profile_url,
                "headshot_url": absolute(source["url"], image.get("src") if image else ""),
                "headshot_alt": norm(image.get("alt") if image else ""),
                "medical_school": medical_school,
                "residency_program": residency,
                "extraction_method": "palliative_care_prose",
                "quality_tier": "medium",
                "quality_notes": ["prose_not_fielded_roster"],
            }
        )
    return rows


def parse_note_page(source_key: str, html: str, source: dict) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    main = soup.select_one("main") or soup.body
    text = redact_text(norm(main.get_text(" "))) if main else ""
    return [
        {
            "source_key": source_key,
            "source_url": source["url"],
            "source_type": "official_context_page",
            "institution": "University of Pennsylvania / Penn Medicine",
            "unit": source["unit"],
            "program": source["program"],
            "population": source["population"],
            "role": source["role"],
            "page_text_excerpt": text[:1200],
            "extraction_method": source["parser"],
            "quality_tier": "context_only",
            "quality_notes": ["no_person_level_roster_extracted"],
        }
    ]


def fetch_profile_excerpt(url: str) -> dict:
    if not url:
        return {}
    try:
        response = SESSION.get(url, timeout=30)
    except requests.RequestException as exc:
        return {"profile_fetch_status": f"error:{type(exc).__name__}"}
    if response.status_code != 200:
        return {"profile_fetch_status": str(response.status_code)}
    soup = BeautifulSoup(response.text, "lxml")
    main = soup.select_one("main") or soup.body
    if not main:
        return {"profile_fetch_status": "200_no_main"}
    text = redact_text(norm(main.get_text(" ")))
    return {
        "profile_fetch_status": "200",
        "profile_text_excerpt": text[:1500],
    }


def write_outputs(records: list[dict], source_meta: list[dict]) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "penn_training_people.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    unique_records = unique_people(records)
    (OUT / "penn_training_people_unique.json").write_text(
        json.dumps(unique_records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (OUT / "penn_training_sources.json").write_text(
        json.dumps(source_meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    fields = sorted({key for row in records for key in row.keys()})
    with (OUT / "penn_training_people.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in records:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, list) else value for key, value in row.items()})
    unique_fields = sorted({key for row in unique_records for key in row.keys()})
    with (OUT / "penn_training_people_unique.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=unique_fields)
        writer.writeheader()
        for row in unique_records:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value for key, value in row.items()})
    (OUT / "penn_profile_index.md").write_text(render_profile_index(unique_records), encoding="utf-8")


def md_cell(value) -> str:
    if isinstance(value, list):
        value = ", ".join(value)
    value = norm(str(value or ""))
    return value.replace("|", "\\|")


def quality_label(row: dict) -> str:
    notes = row.get("quality_notes") or []
    if row.get("quality_tier") == "high" and not notes:
        return "high"
    if row.get("quality_tier") == "context_only":
        return "context"
    return f"{row.get('quality_tier', 'unknown')} ({'; '.join(notes)})" if notes else row.get("quality_tier", "unknown")


def render_profile_index(unique_records: list[dict]) -> str:
    lines = [
        "# Penn Training Profile Index",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "This is a review index for the first Penn case study. The canonical machine-readable outputs are `penn_training_people.json` and `penn_training_people_unique.json`.",
        "",
        "| Name | Role | Programs / memberships | Year labels seen | Medical school | Residency program | Profile | Quality |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in sorted(unique_records, key=lambda r: (", ".join(r.get("program_memberships", [])), r.get("training_year_label", ""), r.get("name", ""))):
        profile = f"[profile]({row['profile_url']})" if row.get("profile_url") else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    md_cell(row.get("name")),
                    md_cell(row.get("role")),
                    md_cell(row.get("program_memberships")),
                    md_cell(row.get("training_year_labels_seen")),
                    md_cell(row.get("medical_school")),
                    md_cell(row.get("residency_program")),
                    profile,
                    md_cell(quality_label(row)),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


MANUAL_ALIASES = {
    "annie albright": "anne albright",
    "emma greenstreet akman": "emma akman greenstreet",
}


def canonical_person_key(row: dict) -> str:
    name = row.get("name", "").lower()
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"\b(md|do|phd|mph|mba|msc|ms|mphil|mbe|mts|mbchb|mbss|meng|dphil)\b", " ", name)
    name = re.sub(r"[^a-z ]+", " ", name)
    name = norm(name)
    name = MANUAL_ALIASES.get(name, name)
    return name


def unique_people(records: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in records:
        if not row.get("name"):
            continue
        grouped.setdefault(canonical_person_key(row), []).append(row)
    unique = []
    for key, rows in sorted(grouped.items()):
        best = max(rows, key=lambda r: sum(1 for _, value in r.items() if value not in ("", [], None)))
        merged = dict(best)
        merged["person_key"] = key
        merged["source_memberships"] = sorted({r["source_key"] for r in rows})
        merged["program_memberships"] = sorted({r["program"] for r in rows})
        merged["population_memberships"] = sorted({r["population"] for r in rows})
        merged["training_year_labels_seen"] = sorted({r.get("training_year_label", "") for r in rows if r.get("training_year_label")})
        merged["duplicate_roster_rows"] = len(rows)
        names_seen = sorted({r["name"] for r in rows})
        if len(names_seen) > 1:
            merged["name_variants_seen"] = names_seen
            merged.setdefault("quality_notes", []).append("merged_name_variants")
        unique.append(merged)
    return unique


def summarize(records: list[dict]) -> dict:
    people = [row for row in records if row.get("name")]
    unique = unique_people(records)
    by_source = {}
    for row in records:
        by_source.setdefault(row["source_key"], 0)
        if row.get("name"):
            by_source[row["source_key"]] += 1
    profile_links = sum(1 for row in people if row.get("profile_url"))
    med_school = sum(1 for row in people if row.get("medical_school"))
    residency = sum(1 for row in people if row.get("residency_program"))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "person_records": len(people),
        "unique_person_records": len(unique),
        "context_records": len(records) - len(people),
        "by_source": by_source,
        "by_role_status_unique": {
            f"{role}:{status}": count
            for (role, status), count in sorted(
                Counter((row.get("role"), row.get("current_status")) for row in unique).items()
            )
        },
        "fields_present": {
            "medical_school": med_school,
            "residency_program": residency,
            "profile_url": profile_links,
        },
    }


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    all_records = []
    source_meta = []
    for key, source in SOURCES.items():
        html, meta = fetch(key, source["url"])
        source_meta.append(meta)
        if source["parser"] == "penn_bio":
            records = parse_penn_bio_page(key, html, source)
        elif source["parser"] == "chop_med_peds":
            records = parse_chop_med_peds(key, html, source)
        elif source["parser"] == "palliative_prose":
            records = parse_palliative_prose(key, html, source)
        else:
            records = parse_note_page(key, html, source)
        all_records.extend(records)

    for row in all_records:
        if row.get("profile_url"):
            row.update(fetch_profile_excerpt(row["profile_url"]))
            if row.get("profile_fetch_status") != "200":
                row.setdefault("quality_notes", []).append(f"profile_fetch:{row.get('profile_fetch_status')}")

    write_outputs(all_records, source_meta)
    (OUT / "penn_training_summary.json").write_text(
        json.dumps(summarize(all_records), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
