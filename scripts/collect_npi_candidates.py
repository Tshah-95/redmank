#!/usr/bin/env python3
"""Collect candidate NPI registry matches for Penn physician trainees."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode


DEPS_PATH = Path(os.environ.get("PENN_CORPUS_DEPS", "/tmp/penn_corpus_deps"))
if DEPS_PATH.exists():
    sys.path.insert(0, str(DEPS_PATH))

try:
    import requests
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing scraper dependency. Install with: "
        "python3 -m pip install --target /tmp/penn_corpus_deps -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

API_BASE = "https://npiregistry.cms.hhs.gov/api/"
CSV_PATH = ARTIFACTS / "npi_candidate_claims.csv"
JSON_PATH = ARTIFACTS / "npi_candidate_claims.json"
OBSERVATION_CSV = ARTIFACTS / "npi_source_observations.csv"
SUMMARY_PATH = ARTIFACTS / "npi_candidate_summary.json"

FIELDS = [
    "candidate_key",
    "person_key",
    "display_name",
    "normalized_name",
    "role",
    "program_names",
    "npi",
    "provider_name",
    "provider_credential",
    "enumeration_type",
    "primary_taxonomy",
    "taxonomy_descriptions",
    "practice_city",
    "practice_state",
    "practice_postal_code",
    "result_rank",
    "total_results",
    "candidate_status",
    "confidence",
    "source_url",
    "match_features_json",
    "evidence_json",
    "queried_at",
]

OBS_FIELDS = [
    "query_key",
    "person_key",
    "display_name",
    "first_name",
    "last_name",
    "state_filter",
    "request_url",
    "queried_at",
    "http_status",
    "total_results",
    "candidate_rows",
    "error",
    "sha256",
]

NAME_PARTICLES = {"de", "del", "der", "di", "la", "le", "van", "von"}


def norm_space(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def normalized_name(value: str | None) -> str:
    value = norm_space(value).lower()
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(
        r"\b(md|m\.d\.|do|d\.o\.|phd|ph\.d\.|mbe|msce|mse?d|msc|mph|mba|ms|m\.s\.|ma|m\.a\.|facp)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return norm_space(value)


def name_parts(display_name: str) -> tuple[str, str]:
    clean = normalized_name(display_name)
    tokens = [token for token in clean.split() if token]
    if len(tokens) < 2:
        return "", ""
    first = tokens[0]
    last_tokens = [tokens[-1]]
    if len(tokens) >= 3 and tokens[-2] in NAME_PARTICLES:
        last_tokens.insert(0, tokens[-2])
    return first, " ".join(last_tokens)


def key_for(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:16]}"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def rows(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query, params)]


def target_people(conn: sqlite3.Connection, include_medical_students: bool) -> list[dict]:
    roles = ("'resident','fellow','medical_student'" if include_medical_students else "'resident','fellow'")
    return rows(
        conn,
        f"""
        SELECT p.person_key, p.display_name, p.role, p.current_status,
               GROUP_CONCAT(DISTINCT pr.program_name) AS program_names
        FROM people p
        LEFT JOIN person_program_memberships m ON m.person_key = p.person_key
        LEFT JOIN programs pr ON pr.program_key = m.program_key
        WHERE p.role IN ({roles})
        GROUP BY p.person_key, p.display_name, p.role, p.current_status
        ORDER BY p.role, p.display_name
        """,
    )


def request_url(first: str, last: str, state: str, limit: int) -> str:
    params = {
        "version": "2.1",
        "enumeration_type": "NPI-1",
        "first_name": first,
        "last_name": last,
        "limit": str(limit),
    }
    if state:
        params["state"] = state
    return f"{API_BASE}?{urlencode(params)}"


def fetch(session: requests.Session, url: str) -> tuple[int, dict, str]:
    try:
        response = session.get(url, timeout=30)
        if response.status_code != 200:
            return response.status_code, {}, response.text[:500]
        return response.status_code, response.json(), ""
    except (requests.RequestException, json.JSONDecodeError) as exc:
        return 0, {}, f"{type(exc).__name__}: {str(exc)[:240]}"


def provider_name(result: dict) -> str:
    basic = result.get("basic") or {}
    parts = [
        basic.get("first_name"),
        basic.get("middle_name"),
        basic.get("last_name"),
        basic.get("credential"),
    ]
    return norm_space(" ".join(part for part in parts if part))


def primary_taxonomy(result: dict) -> dict:
    taxonomies = result.get("taxonomies") or []
    for taxonomy in taxonomies:
        if taxonomy.get("primary"):
            return taxonomy
    return taxonomies[0] if taxonomies else {}


def taxonomy_descriptions(result: dict) -> list[str]:
    descriptions = []
    for taxonomy in result.get("taxonomies") or []:
        description = norm_space(taxonomy.get("desc"))
        if description and description not in descriptions:
            descriptions.append(description)
    return descriptions


def practice_address(result: dict) -> dict:
    addresses = result.get("addresses") or []
    for address in addresses:
        if (address.get("address_purpose") or "").upper() == "LOCATION":
            return address
    return addresses[0] if addresses else {}


def program_topic_tokens(program_names: str | None) -> set[str]:
    text = normalized_name(program_names)
    tokens = set()
    for token in text.split():
        if len(token) >= 5 and token not in {"fellow", "fellowship", "residency", "resident", "program"}:
            tokens.add(token)
    return tokens


def candidate_features(person: dict, result: dict, state_filter: str) -> tuple[list[str], float, str]:
    basic = result.get("basic") or {}
    first, last = name_parts(person["display_name"])
    result_first = normalized_name(basic.get("first_name")).split()
    result_last = normalized_name(basic.get("last_name"))
    features = []
    score = 0.25
    if result_first and first == result_first[0] and last == result_last:
        features.append("exact_first_last_name")
        score += 0.24
    elif last == result_last:
        features.append("last_name_match_only")
        score += 0.08
    middle = normalized_name(basic.get("middle_name")).split()
    person_tokens = normalized_name(person["display_name"]).split()
    if middle and len(person_tokens) > 2 and middle[0][0] == person_tokens[1][0]:
        features.append("middle_initial_match")
        score += 0.06
    credentials = normalized_name(basic.get("credential"))
    if any(token in credentials.split() for token in ["md", "do"]):
        features.append("physician_credential")
        score += 0.08
    address = practice_address(result)
    if state_filter and (address.get("state") or "").upper() == state_filter.upper():
        features.append("state_location_match")
        score += 0.1
    if normalized_name(address.get("city")) == "philadelphia":
        features.append("philadelphia_location")
        score += 0.06
    descriptions = " ".join(taxonomy_descriptions(result)).lower()
    if "student in an organized health care education/training program" in descriptions:
        features.append("student_or_training_taxonomy")
        score += 0.08
    elif any(token in descriptions for token in ["internal medicine", "pediatrics", "surgery", "radiology", "pathology", "anesthesiology", "psychiatry", "obstetrics", "gynecology"]):
        features.append("physician_specialty_taxonomy")
        score += 0.06
    program_tokens = program_topic_tokens(person.get("program_names"))
    if program_tokens and any(token in descriptions for token in sorted(program_tokens)):
        features.append("program_taxonomy_topic_match")
        score += 0.06
    if "exact_first_last_name" in features and "state_location_match" in features and (
        "physician_specialty_taxonomy" in features or "student_or_training_taxonomy" in features
    ):
        status = "needs_review"
    elif "exact_first_last_name" in features:
        status = "candidate"
    else:
        status = "low_signal_npi_candidate"
    return features, min(score, 0.95), status


def collect(args: argparse.Namespace) -> tuple[list[dict], list[dict]]:
    conn = sqlite3.connect(args.db)
    people = target_people(conn, args.include_medical_students)
    conn.close()
    if args.limit:
        people = people[: args.limit]

    session = requests.Session()
    session.headers["User-Agent"] = "redmank-npi-candidate-collector/0.1"
    candidates = []
    observations = []
    for person in people:
        first, last = name_parts(person["display_name"])
        if not first or not last:
            continue
        url = request_url(first, last, args.state, args.per_query_limit)
        queried_at = datetime.now(timezone.utc).isoformat()
        status, payload, error = fetch(session, url)
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True) if payload else error
        results = payload.get("results") or []
        total_results = int(payload.get("result_count") or len(results) or 0)
        observation = {
            "query_key": key_for("npi_query", f"{person['person_key']}:{url}"),
            "person_key": person["person_key"],
            "display_name": person["display_name"],
            "first_name": first,
            "last_name": last,
            "state_filter": args.state,
            "request_url": url,
            "queried_at": queried_at,
            "http_status": status,
            "total_results": total_results,
            "candidate_rows": 0,
            "error": error,
            "sha256": sha256_text(raw) if raw else "",
        }
        for index, result in enumerate(results, start=1):
            features, confidence, candidate_status = candidate_features(person, result, args.state)
            address = practice_address(result)
            primary = primary_taxonomy(result)
            taxonomies = taxonomy_descriptions(result)
            npi = str(result.get("number") or "")
            if not npi:
                continue
            row = {
                "candidate_key": key_for("npi_candidate", f"{person['person_key']}:{npi}"),
                "person_key": person["person_key"],
                "display_name": person["display_name"],
                "normalized_name": normalized_name(person["display_name"]),
                "role": person.get("role") or "",
                "program_names": person.get("program_names") or "",
                "npi": npi,
                "provider_name": provider_name(result),
                "provider_credential": norm_space((result.get("basic") or {}).get("credential")),
                "enumeration_type": result.get("enumeration_type") or "",
                "primary_taxonomy": norm_space(primary.get("desc")),
                "taxonomy_descriptions": "; ".join(taxonomies),
                "practice_city": norm_space(address.get("city")),
                "practice_state": norm_space(address.get("state")),
                "practice_postal_code": norm_space(address.get("postal_code")),
                "result_rank": index,
                "total_results": total_results,
                "candidate_status": candidate_status,
                "confidence": round(confidence, 3),
                "source_url": f"https://npiregistry.cms.hhs.gov/provider-view/{npi}",
                "match_features_json": dumps(features),
                "evidence_json": dumps(
                    {
                        "nppes_api_url": url,
                        "basic": result.get("basic") or {},
                        "taxonomies": result.get("taxonomies") or [],
                        "practice_address": address,
                    }
                ),
                "queried_at": queried_at,
            }
            candidates.append(row)
            observation["candidate_rows"] += 1
        observations.append(observation)
        if args.sleep:
            time.sleep(args.sleep)
    return candidates, observations


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(conn: sqlite3.Connection, candidates: list[dict], observations: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM npi_candidate_claims")
    conn.execute("DELETE FROM npi_source_observations")
    for row in observations:
        conn.execute(
            """
            INSERT INTO npi_source_observations
            (query_key, person_key, display_name, first_name, last_name, state_filter,
             request_url, queried_at, http_status, total_results, candidate_rows,
             error, sha256)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row[field] for field in OBS_FIELDS),
        )
    for row in candidates:
        conn.execute(
            """
            INSERT INTO npi_candidate_claims
            (candidate_key, person_key, display_name, normalized_name, role, program_names,
             npi, provider_name, provider_credential, enumeration_type, primary_taxonomy,
             taxonomy_descriptions, practice_city, practice_state, practice_postal_code,
             result_rank, total_results, candidate_status, confidence, source_url,
             match_features_json, evidence_json, queried_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row[field] for field in FIELDS),
        )


def write_summary(candidates: list[dict], observations: list[dict], args: argparse.Namespace) -> None:
    summary = {
        "generated_at": max((row["queried_at"] for row in observations), default=datetime.now(timezone.utc).isoformat()),
        "utility_key": "nppes_npi_registry",
        "api_base": API_BASE,
        "api_version": "2.1",
        "state_filter": args.state,
        "target_queries": len(observations),
        "candidate_rows": len(candidates),
        "queries_with_candidates": sum(1 for row in observations if int(row["candidate_rows"]) > 0),
        "queries_with_no_results": sum(1 for row in observations if int(row["total_results"]) == 0),
        "queries_with_error": sum(1 for row in observations if row["error"]),
        "by_candidate_status": dict(sorted(Counter(row["candidate_status"] for row in candidates).items())),
        "by_role": dict(sorted(Counter(row["role"] for row in candidates).items())),
        "by_primary_taxonomy": dict(
            sorted(Counter(row["primary_taxonomy"] or "none" for row in candidates).items(), key=lambda item: (-item[1], item[0]))[:30]
        ),
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
        "observation_csv": str(OBSERVATION_CSV.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--state", default="PA")
    parser.add_argument("--per-query-limit", type=int, default=10)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep", type=float, default=0.03)
    parser.add_argument("--include-medical-students", action="store_true")
    args = parser.parse_args()

    candidates, observations = collect(args)
    candidates = sorted(
        candidates,
        key=lambda row: (
            row["person_key"],
            -float(row["confidence"]),
            int(row["result_rank"]),
            row["npi"],
        ),
    )
    write_csv(CSV_PATH, candidates, FIELDS)
    write_csv(OBSERVATION_CSV, observations, OBS_FIELDS)
    JSON_PATH.write_text(json.dumps(candidates, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    conn = sqlite3.connect(args.db)
    with conn:
        write_sqlite(conn, candidates, observations)
    conn.close()
    write_summary(candidates, observations, args)


if __name__ == "__main__":
    main()
