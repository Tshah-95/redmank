#!/usr/bin/env python3
"""Materialize official Penn trainee profile snippets into durable evidence claims."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
INPUT = ARTIFACTS / "penn_training_people_unique.json"
CLAIMS_JSON = ARTIFACTS / "penn_trainee_profile_claims.json"
CLAIMS_CSV = ARTIFACTS / "penn_trainee_profile_claims.csv"
SOURCES_JSON = ARTIFACTS / "penn_trainee_profile_sources.json"
SUMMARY_JSON = ARTIFACTS / "penn_trainee_profile_summary.json"


PROVIDER_STOP_MARKERS = [
    " Insurance accepted ",
    " Locations ",
    " Reviews ",
    " Providers may participate ",
]

LABEL_SPECS = {
    "Medical School": {
        "claim_type": "education_history_candidate",
        "field_key": "medical_school",
        "confidence": 0.82,
        "status": "candidate",
        "display_safety_status": "safe_for_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "structured_profile_field"],
    },
    "Residency Program": {
        "claim_type": "prior_training_history_candidate",
        "field_key": "residency_program",
        "confidence": 0.78,
        "status": "candidate",
        "display_safety_status": "safe_for_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "structured_profile_field"],
    },
    "Residency": {
        "claim_type": "prior_training_history_candidate",
        "field_key": "residency",
        "confidence": 0.76,
        "status": "candidate",
        "display_safety_status": "safe_for_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "structured_profile_field"],
    },
    "Undergraduate": {
        "claim_type": "education_history_candidate",
        "field_key": "undergraduate",
        "confidence": 0.58,
        "status": "candidate",
        "display_safety_status": "safe_for_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "structured_profile_field"],
    },
    "Career Interests": {
        "claim_type": "career_interest_candidate",
        "field_key": "career_interests",
        "confidence": 0.58,
        "status": "candidate",
        "display_safety_status": "safe_for_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "interest_field"],
    },
    "Academic Interests": {
        "claim_type": "research_interest_candidate",
        "field_key": "academic_interests",
        "confidence": 0.62,
        "status": "candidate",
        "display_safety_status": "safe_for_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "interest_field"],
    },
    "Research Interests": {
        "claim_type": "research_interest_candidate",
        "field_key": "research_interests",
        "confidence": 0.66,
        "status": "candidate",
        "display_safety_status": "safe_for_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "research_interest_field"],
    },
    "Clinical Interests": {
        "claim_type": "clinical_interest_candidate",
        "field_key": "clinical_interests",
        "confidence": 0.6,
        "status": "candidate",
        "display_safety_status": "safe_for_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "interest_field"],
    },
    "Hobbies/Interests": {
        "claim_type": "personal_profile_candidate",
        "field_key": "hobbies_interests",
        "confidence": 0.55,
        "status": "candidate",
        "display_safety_status": "personal_context_not_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "personal_profile_field"],
    },
    "Hobbies": {
        "claim_type": "personal_profile_candidate",
        "field_key": "hobbies",
        "confidence": 0.55,
        "status": "candidate",
        "display_safety_status": "personal_context_not_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "personal_profile_field"],
    },
    "Home State": {
        "claim_type": "personal_profile_candidate",
        "field_key": "home_state",
        "confidence": 0.54,
        "status": "candidate",
        "display_safety_status": "personal_context_not_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "personal_background_field"],
    },
    "Hometown": {
        "claim_type": "personal_profile_candidate",
        "field_key": "hometown",
        "confidence": 0.54,
        "status": "candidate",
        "display_safety_status": "personal_context_not_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "personal_background_field"],
    },
    "Kids": {
        "claim_type": "personal_profile_candidate",
        "field_key": "kids",
        "confidence": 0.45,
        "status": "candidate",
        "display_safety_status": "sensitive_personal_context_restricted",
        "features": ["official_trainee_profile", "roster_linked_profile", "sensitive_personal_profile_field"],
    },
    "If I didn't end up going to medical school, I would be": {
        "claim_type": "personal_profile_candidate",
        "field_key": "alternate_career_interest",
        "confidence": 0.5,
        "status": "candidate",
        "display_safety_status": "personal_context_not_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "personal_profile_field"],
    },
    "I am most looking forward to doing this in Philadelphia": {
        "claim_type": "personal_profile_candidate",
        "field_key": "philadelphia_interest",
        "confidence": 0.5,
        "status": "candidate",
        "display_safety_status": "personal_context_not_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "personal_profile_field"],
    },
    "Why Penn?": {
        "claim_type": "personal_profile_candidate",
        "field_key": "why_penn",
        "confidence": 0.52,
        "status": "candidate",
        "display_safety_status": "personal_context_not_default_display",
        "features": ["official_trainee_profile", "roster_linked_profile", "personal_profile_field"],
    },
}

STOP_LABELS = [
    "Email",
    "Program/Specialty",
    "What inspires me about GI",
    "Why I chose Penn",
    "What Drew Me to Penn",
    "Anticipated Additional Training During Fellowship",
]


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).replace("\xa0", " ")).strip()


def normalized_label(text: str | None) -> str:
    text = norm(text).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return norm(text)


def redact_text(text: str) -> str:
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)
    return re.sub(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b", "[REDACTED_PHONE]", text)


def truncate_provider_noise(text: str) -> str:
    padded = f" {text} "
    stops = [padded.find(marker) for marker in PROVIDER_STOP_MARKERS if padded.find(marker) != -1]
    if not stops:
        return text
    return norm(padded[: min(stops)])


def source_key_for(url: str) -> str:
    path = urlparse(url).path.strip("/").replace("/", "_")
    slug = re.sub(r"[^a-zA-Z0-9_]+", "_", path).strip("_").lower()[:72]
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    return f"penn_trainee_profile_{slug}_{digest}"


def claim_key_for(row: dict) -> str:
    basis = "|".join(
        [
            row.get("person_key", ""),
            row.get("claim_type", ""),
            row.get("claim_value", ""),
            row.get("source_key", ""),
        ]
    )
    return "trainee_profile_claim_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def label_lookup() -> dict[str, str]:
    return {normalized_label(label): label for label in [*LABEL_SPECS, *STOP_LABELS]}


def label_regex() -> re.Pattern:
    no_colon_labels = ["Why Penn?"]
    colon_labels = sorted([label for label in [*LABEL_SPECS, *STOP_LABELS] if label not in no_colon_labels], key=len, reverse=True)
    colon = "|".join(re.escape(label) for label in colon_labels)
    no_colon = "|".join(re.escape(label) for label in no_colon_labels)
    return re.compile(rf"(?:(?P<label>{colon})\s*:|(?P<label_no_colon>{no_colon})\s*)", flags=re.I)


def parsed_fields(text: str) -> list[tuple[str, str, str]]:
    lookup = label_lookup()
    pattern = label_regex()
    matches = list(pattern.finditer(text))
    fields: list[tuple[str, str, str]] = []
    for index, match in enumerate(matches):
        raw_label = norm(match.group("label") or match.group("label_no_colon"))
        canonical = lookup.get(normalized_label(raw_label.rstrip("?"))) or lookup.get(normalized_label(raw_label))
        if not canonical:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        value = norm(text[start:end].strip(" :-"))
        if value and canonical in LABEL_SPECS:
            fields.append((canonical, raw_label, value))
    return fields


def preview(text: str, limit: int = 500) -> str:
    text = norm(text)
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def add_claim(claims: list[dict], record: dict, source: dict, claim_type: str, claim_value: str, confidence: float, status: str, match_features: list[str], evidence: dict, reconciliation_notes: str) -> None:
    claim_value = preview(redact_text(claim_value), 700)
    if not claim_value:
        return
    claim = {
        "person_key": record["person_key"],
        "display_name": record.get("name", ""),
        "role": record.get("role", ""),
        "program_context": record.get("program", ""),
        "claim_type": claim_type,
        "claim_value": claim_value,
        "source_key": source["source_key"],
        "source_url": source["url"],
        "source_type": "official_trainee_profile",
        "confidence": confidence,
        "status": status,
        "match_features": match_features,
        "reconciliation_notes": reconciliation_notes,
        "evidence": evidence,
    }
    claim["claim_key"] = claim_key_for(claim)
    claims.append(claim)


def source_record(record: dict, text: str, generated_at: str) -> dict:
    source_url = record.get("profile_url", "")
    return {
        "source_key": source_key_for(source_url),
        "url": source_url,
        "source_type": "official_trainee_profile",
        "title": f"Penn trainee profile: {record.get('name', '')}",
        "fetched_at": generated_at,
        "http_status": int(record.get("profile_fetch_status") or 0) or None,
        "sha256": sha256_text(text),
        "display_name": record.get("name", ""),
        "person_key": record.get("person_key", ""),
        "role": record.get("role", ""),
        "program": record.get("program", ""),
        "roster_source_key": record.get("source_key", ""),
        "roster_source_url": record.get("source_url", ""),
        "profile_fetch_status": record.get("profile_fetch_status", ""),
    }


def materialize() -> tuple[list[dict], list[dict], dict]:
    records = json.loads(INPUT.read_text(encoding="utf-8"))
    generated_at = datetime.now(timezone.utc).isoformat()
    claims: list[dict] = []
    sources_by_url: dict[str, dict] = {}
    profile_records = 0
    parsed_profile_records = 0
    source_fetch_counts = Counter()
    field_counts = Counter()
    skipped = Counter()

    for record in records:
        profile_url = record.get("profile_url") or ""
        raw_text = record.get("profile_text_excerpt") or ""
        if not profile_url:
            continue
        profile_records += 1
        source_fetch_counts[str(record.get("profile_fetch_status") or "")] += 1
        text = truncate_provider_noise(redact_text(norm(raw_text)))
        source = source_record(record, text, generated_at)
        sources_by_url[profile_url] = source
        if not text:
            skipped["missing_profile_text_excerpt"] += 1
            continue
        parsed_profile_records += 1
        profile_evidence = {
            "origin": "official_roster_linked_profile",
            "utility_key": "official_trainee_profile",
            "display_safety_status": "safe_for_default_display",
            "profile_fetch_status": record.get("profile_fetch_status", ""),
            "profile_excerpt_preview": preview(text),
            "roster_source_key": record.get("source_key", ""),
            "roster_source_url": record.get("source_url", ""),
            "profile_text_sha256": sha256_text(text),
        }
        add_claim(
            claims,
            record,
            source,
            "official_profile_url",
            profile_url,
            0.9,
            "accepted",
            ["official_roster_source", "linked_profile_url", "profile_fetch_status_200"],
            profile_evidence,
            "Accepted only as the official profile URL linked from an official trainee roster; profile-derived fields remain candidate evidence.",
        )
        emitted_fields = 0
        for canonical, raw_label, value in parsed_fields(text):
            spec = LABEL_SPECS[canonical]
            field_counts[spec["field_key"]] += 1
            emitted_fields += 1
            raw_profile_value = value
            clean_value = value
            features = list(spec["features"])
            if spec["field_key"] == "medical_school" and record.get("medical_school"):
                clean_value = record["medical_school"]
                features.append("roster_structured_field_crosscheck")
            elif spec["field_key"] in {"residency", "residency_program"} and record.get("residency_program"):
                clean_value = record["residency_program"]
                features.append("roster_structured_field_crosscheck")
            evidence_text = preview(f"{canonical}: {redact_text(clean_value)}")
            evidence = {
                "origin": "official_trainee_profile_field",
                "utility_key": "official_trainee_profile",
                "field_label": canonical,
                "raw_field_label": raw_label,
                "field_key": spec["field_key"],
                "display_safety_status": spec["display_safety_status"],
                "profile_fetch_status": record.get("profile_fetch_status", ""),
                "evidence_text": evidence_text,
                "raw_profile_value": preview(redact_text(raw_profile_value)),
                "profile_excerpt_preview": preview(text),
                "roster_source_key": record.get("source_key", ""),
                "roster_source_url": record.get("source_url", ""),
                "profile_text_sha256": sha256_text(text),
            }
            add_claim(
                claims,
                record,
                source,
                spec["claim_type"],
                f"{canonical}: {clean_value}",
                spec["confidence"],
                spec["status"],
                features,
                evidence,
                "Candidate profile-derived enrichment. Keep separate from accepted roster truth unless independently reconciled.",
            )
        if emitted_fields == 0:
            skipped["no_known_profile_fields"] += 1

    claims = sorted(claims, key=lambda row: (row["person_key"], row["claim_type"], row["claim_value"], row["source_key"]))
    sources = sorted(sources_by_url.values(), key=lambda row: row["source_key"])
    summary = {
        "generated_at": generated_at,
        "input": str(INPUT.relative_to(ROOT)),
        "profiles_with_url": profile_records,
        "profiles_with_text": parsed_profile_records,
        "sources": len(sources),
        "claims": len(claims),
        "people_with_claims": len({row["person_key"] for row in claims}),
        "by_claim_type": dict(Counter(row["claim_type"] for row in claims)),
        "by_status": dict(Counter(row["status"] for row in claims)),
        "by_role": dict(Counter(row["role"] for row in claims)),
        "field_counts": dict(field_counts),
        "profile_fetch_status_counts": dict(source_fetch_counts),
        "skipped": dict(skipped),
        "display_safety_counts": dict(
            Counter((row.get("evidence") or {}).get("display_safety_status", "") for row in claims)
        ),
        "csv": str(CLAIMS_CSV.relative_to(ROOT)),
        "json": str(CLAIMS_JSON.relative_to(ROOT)),
        "sources_json": str(SOURCES_JSON.relative_to(ROOT)),
        "policy": "Profile URL links from official rosters are accepted as profile-location facts. Structured profile fields are candidate enrichment with display-safety metadata and do not mutate accepted roster/background truth.",
    }
    return claims, sources, summary


def write_csv(path: Path, rows: list[dict]) -> None:
    fieldnames = [
        "claim_key",
        "person_key",
        "display_name",
        "role",
        "program_context",
        "claim_type",
        "claim_value",
        "source_key",
        "source_url",
        "source_type",
        "confidence",
        "status",
        "match_features",
        "reconciliation_notes",
        "evidence",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    **{key: row.get(key, "") for key in fieldnames},
                    "match_features": json.dumps(row.get("match_features", []), sort_keys=True),
                    "evidence": json.dumps(row.get("evidence", {}), sort_keys=True),
                }
            )


def main() -> None:
    claims, sources, summary = materialize()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    CLAIMS_JSON.write_text(json.dumps(claims, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SOURCES_JSON.write_text(json.dumps(sources, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(CLAIMS_CSV, claims)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
