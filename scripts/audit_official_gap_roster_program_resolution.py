#!/usr/bin/env python3
"""Resolve seed-extracted gap roster sources against the official HUP program denominator.

This is intentionally non-mutating. It produces a reviewable ledger of which
seed roster extracts can safely be attached to an official denominator row and
which are still too broad or weak for coverage closure.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

OUT_CSV = ARTIFACTS / "official_gap_roster_program_resolution.csv"
OUT_JSON = ARTIFACTS / "official_gap_roster_program_resolution.json"
OUT_SUMMARY = ARTIFACTS / "official_gap_roster_program_resolution_summary.json"

FIELDNAMES = [
    "resolution_key",
    "reconciliation_key",
    "source_key",
    "source_url",
    "source_program_name",
    "source_department",
    "inferred_source_role",
    "records_extracted",
    "loaded_person_count",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "resolution_status",
    "resolution_confidence",
    "denominator_mutation_allowed",
    "recommended_next_action",
    "match_features_json",
    "evidence_json",
    "audited_at",
]

STOP_TOKENS = {
    "a",
    "and",
    "at",
    "current",
    "education",
    "fellow",
    "fellows",
    "fellowship",
    "fellowships",
    "hup",
    "of",
    "our",
    "program",
    "programs",
    "resident",
    "residency",
    "residents",
    "the",
    "training",
}


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_url(value: str | None) -> str:
    return (value or "").strip().rstrip("/")


def normalize_text(value: str | None) -> str:
    text = (value or "").lower()
    text = text.replace("&", " and ")
    text = text.replace("orthopaedic", "orthopedic")
    text = text.replace("ob/gyn", "obstetrics and gynecology")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def tokens(value: str | None) -> set[str]:
    return {token for token in normalize_text(value).split() if token and token not in STOP_TOKENS}


def url_tokens(value: str | None) -> set[str]:
    parsed = urlparse(normalize_url(value))
    return tokens(parsed.netloc + " " + parsed.path.replace("/", " "))


def jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    return len(left & right) / len(left | right)


def infer_source_role(row: dict) -> str:
    text = normalize_text(
        " ".join(
            [
                row.get("source_url") or "",
                row.get("source_program_name") or "",
                row.get("source_department") or "",
            ]
        )
    )
    if re.search(r"\bfellow(ship|ships|s)?\b", text):
        return "fellowship"
    if re.search(r"\bresident(s|cy)?\b", text):
        return "residency"
    return ""


def existing_rows() -> dict[str, dict]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open(newline="", encoding="utf-8") as handle:
        return {row["resolution_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["resolution_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("audited_at") or timestamp


def load_official_programs(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT official_program_key, program_name, program_type, department, program_url
            FROM official_program_universe
            """
        )
    ]


def load_seed_rows(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM official_gap_roster_reconciliation
            WHERE denominator_link_status = 'records_extracted_seed_without_denominator_key'
              AND records_extracted > 0
            ORDER BY records_extracted DESC, source_program_name, source_url
            """
        )
    ]


def score_candidate(source: dict, program: dict, inferred_role: str) -> tuple[float, list[str]]:
    source_name = normalize_text(source.get("source_program_name"))
    program_name = normalize_text(program.get("program_name"))
    source_department = normalize_text(source.get("source_department"))
    official_department = normalize_text(program.get("department"))
    source_name_tokens = tokens(source_name)
    program_name_tokens = tokens(program_name)
    source_url_tokens = url_tokens(source.get("source_url"))
    program_url_tokens = url_tokens(program.get("program_url"))

    score = 0.0
    features: list[str] = []

    if source_name and source_name == program_name:
        score += 0.62
        features.append("exact_normalized_program_name")
    elif source_name and program_name and (source_name in program_name or program_name in source_name):
        score += 0.46
        features.append("contained_normalized_program_name")
    else:
        overlap = jaccard(source_name_tokens, program_name_tokens)
        if overlap:
            score += min(0.35, 0.42 * overlap)
            features.append(f"name_token_overlap_{overlap:.2f}")

    if source_department and official_department and source_department == official_department:
        score += 0.16
        features.append("exact_department_match")
    elif source_department and official_department and (
        source_department in official_department or official_department in source_department
    ):
        score += 0.1
        features.append("contained_department_match")

    if inferred_role and inferred_role == program.get("program_type"):
        score += 0.12
        features.append("source_role_matches_program_type")
    elif inferred_role:
        score -= 0.18
        features.append("source_role_program_type_mismatch")

    source_url = normalize_url(source.get("source_url"))
    program_url = normalize_url(program.get("program_url"))
    if source_url and program_url and (source_url.startswith(program_url) or program_url.startswith(source_url)):
        score += 0.08
        features.append("program_url_path_prefix_match")

    path_overlap = jaccard(source_url_tokens, program_url_tokens)
    if path_overlap >= 0.35:
        score += 0.03
        features.append(f"url_token_overlap_{path_overlap:.2f}")

    return max(0.0, min(score, 0.99)), features


def classify(source: dict, program: dict | None, confidence: float, features: list[str], same_dept_type_count: int) -> tuple[str, int, str]:
    if not program or confidence < 0.48:
        return (
            "no_official_denominator_candidate",
            0,
            "Keep as extracted trainee evidence, but do not attach denominator coverage until a source-backed official program key is found.",
        )

    source_name = normalize_text(source.get("source_program_name"))
    source_department = normalize_text(source.get("source_department"))
    generic_department_source = bool(source_name and source_department and source_name == source_department)
    exact_name = "exact_normalized_program_name" in features
    role_match = "source_role_matches_program_type" in features
    role_mismatch = "source_role_program_type_mismatch" in features
    department_match = "exact_department_match" in features or "contained_department_match" in features
    url_match = "program_url_path_prefix_match" in features

    if role_mismatch:
        return (
            "source_role_program_type_mismatch_review",
            0,
            "Do not attach coverage until the source role is reconciled against the official program type.",
        )
    if generic_department_source and not exact_name and same_dept_type_count > 1:
        return (
            "source_scope_too_broad_review",
            0,
            "Review broad department roster manually; it may cover several official programs or tracks.",
        )
    if exact_name and role_match and department_match and confidence >= 0.86:
        return (
            "accepted_exact_program_resolution_candidate",
            1,
            "Attach this extracted source to the official program key after reviewer confirms the roster is current.",
        )
    if exact_name and role_match and (department_match or url_match) and confidence >= 0.82:
        return (
            "accepted_url_and_name_resolution_candidate",
            1,
            "Attach this source to the official program key after reviewer confirms the roster page is current.",
        )
    if confidence >= 0.72:
        return (
            "review_program_alias_resolution_candidate",
            0,
            "Review program alias or track naming before denominator coverage mutation.",
        )
    if confidence >= 0.55:
        return (
            "weak_program_resolution_review",
            0,
            "Use as a review hint only; collect stronger program identity evidence before coverage mutation.",
        )
    return (
        "no_official_denominator_candidate",
        0,
        "Keep as extracted trainee evidence, but do not attach denominator coverage until a source-backed official program key is found.",
    )


def build_rows(conn: sqlite3.Connection) -> list[dict]:
    existing = existing_rows()
    timestamp = now_utc()
    programs = load_official_programs(conn)
    seed_rows = load_seed_rows(conn)
    same_dept_type_counts = Counter(
        (normalize_text(program.get("department")), program.get("program_type") or "")
        for program in programs
    )

    rows = []
    for source in seed_rows:
        inferred_role = infer_source_role(source)
        scored = []
        for program in programs:
            confidence, features = score_candidate(source, program, inferred_role)
            scored.append((confidence, features, program))
        scored.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        best_confidence, best_features, best_program = scored[0] if scored else (0.0, [], None)
        if best_confidence < 0.48:
            best_program = None
            best_features = []
            best_confidence = 0.0

        same_dept_type_count = 0
        if best_program:
            same_dept_type_count = same_dept_type_counts[
                (normalize_text(best_program.get("department")), best_program.get("program_type") or "")
            ]
        status, mutation_allowed, action = classify(
            source,
            best_program,
            best_confidence,
            best_features,
            same_dept_type_count,
        )
        resolution_key = "official_gap_roster_program_resolution_" + sha256_text(
            source["reconciliation_key"] + "|" + ((best_program or {}).get("official_program_key") or "")
        )[:20]
        evidence = {
            "source_reconciliation_row": source,
            "top_candidate": best_program or {},
            "top_candidate_count_for_department_type": same_dept_type_count,
            "top_three_candidates": [
                {
                    "official_program_key": program.get("official_program_key"),
                    "program_name": program.get("program_name"),
                    "program_type": program.get("program_type"),
                    "department": program.get("department"),
                    "confidence": round(confidence, 4),
                    "features": features,
                }
                for confidence, features, program in scored[:3]
            ],
        }
        row = {
            "resolution_key": resolution_key,
            "reconciliation_key": source["reconciliation_key"],
            "source_key": source.get("source_key") or "",
            "source_url": source.get("source_url") or "",
            "source_program_name": source.get("source_program_name") or "",
            "source_department": source.get("source_department") or "",
            "inferred_source_role": inferred_role,
            "records_extracted": int(source.get("records_extracted") or 0),
            "loaded_person_count": int(source.get("loaded_person_count") or 0),
            "official_program_key": (best_program or {}).get("official_program_key") or "",
            "official_program_name": (best_program or {}).get("program_name") or "",
            "official_program_type": (best_program or {}).get("program_type") or "",
            "official_department": (best_program or {}).get("department") or "",
            "resolution_status": status,
            "resolution_confidence": round(best_confidence, 4),
            "denominator_mutation_allowed": mutation_allowed,
            "recommended_next_action": action,
            "match_features_json": dumps(best_features),
            "evidence_json": dumps(evidence),
            "audited_at": "",
        }
        row["audited_at"] = stable_audited_at(existing, row, timestamp)
        rows.append(row)

    return sorted(
        rows,
        key=lambda row: (
            row["denominator_mutation_allowed"] == 0,
            -row["records_extracted"],
            row["resolution_status"],
            row["source_program_name"],
        ),
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_gap_roster_program_resolution")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    field_sql = ", ".join(FIELDNAMES)
    db_rows = []
    for row in rows:
        db_row = dict(row)
        if not db_row.get("official_program_key"):
            db_row["official_program_key"] = None
        db_rows.append(db_row)
    conn.executemany(
        f"INSERT INTO official_gap_roster_program_resolution ({field_sql}) VALUES ({placeholders})",
        db_rows,
    )


def write_summary(rows: list[dict]) -> None:
    by_status = Counter(row["resolution_status"] for row in rows)
    by_role = Counter(row["inferred_source_role"] or "unknown" for row in rows)
    mutation_allowed_records = sum(
        row["records_extracted"] for row in rows if int(row["denominator_mutation_allowed"]) == 1
    )
    review_records = sum(row["records_extracted"] for row in rows if int(row["denominator_mutation_allowed"]) == 0)
    payload = {
        "resolution_rows": len(rows),
        "source_records_reviewed": sum(row["records_extracted"] for row in rows),
        "loaded_people_reviewed": sum(row["loaded_person_count"] for row in rows),
        "denominator_mutation_allowed_rows": sum(1 for row in rows if int(row["denominator_mutation_allowed"]) == 1),
        "denominator_mutation_allowed_records": mutation_allowed_records,
        "review_required_rows": sum(1 for row in rows if int(row["denominator_mutation_allowed"]) == 0),
        "review_required_records": review_records,
        "by_resolution_status": dict(sorted(by_status.items())),
        "records_by_resolution_status": dict(
            sorted(
                {
                    status: sum(row["records_extracted"] for row in rows if row["resolution_status"] == status)
                    for status in by_status
                }.items()
            )
        ),
        "by_inferred_source_role": dict(sorted(by_role.items())),
        "mutation_policy": "non_mutating_audit; denominator_mutation_allowed marks reviewer-ready candidates but this script does not close coverage gaps",
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    OUT_SUMMARY.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    conn = sqlite3.connect(DB)
    with conn:
        rows = build_rows(conn)
        write_csv(OUT_CSV, rows)
        OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
        write_db(conn, rows)
    conn.close()
    print(dumps({"official_gap_roster_program_resolution": len(rows)}))


if __name__ == "__main__":
    main()
