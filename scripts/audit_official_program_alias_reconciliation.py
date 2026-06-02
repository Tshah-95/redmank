#!/usr/bin/env python3
"""Audit official-program gap cases that may be covered by related loaded program labels."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

STOP_TOKENS = {
    "and",
    "of",
    "the",
    "program",
    "residency",
    "fellowship",
    "fellowships",
    "residencies",
    "selective",
    "track",
    "current",
    "fellows",
    "residents",
}


def norm_space(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def normalized(value: str | None) -> str:
    value = norm_space(value).lower().replace("&", " and ").replace("/", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return norm_space(value)


def tokens(value: str | None) -> set[str]:
    return {token for token in normalized(value).split() if token and token not in STOP_TOKENS}


def canonical_url(url: str | None) -> str:
    if not url:
        return ""
    clean, _fragment = urldefrag(url)
    return clean.rstrip("/")


def key_for(*parts: str) -> str:
    basis = "|".join(parts)
    return "program_alias_reconciliation_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def existing_audit_rows() -> dict[str, dict]:
    path = ARTIFACTS / "official_program_alias_reconciliation_candidates.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        return {row["reconciliation_key"]: row for row in csv.DictReader(f)}


def stable_audited_at(existing: dict[str, dict], row: dict, new_value: str) -> str:
    prior = existing.get(row["reconciliation_key"])
    if not prior:
        return new_value
    stable_fields = [
        "official_program_key",
        "official_program_type",
        "official_program_name",
        "loaded_program_name",
        "loaded_role",
        "loaded_source_url",
        "loaded_person_count",
        "loaded_training_labels",
        "relation_status",
        "suggested_mapping_action",
        "relation_confidence",
        "coverage_mutation_allowed",
        "rationale",
        "evidence_json",
    ]
    for field in stable_fields:
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return new_value
    return prior.get("audited_at") or new_value


def gap_rows(conn: sqlite3.Connection) -> list[dict]:
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT
              g.official_program_key,
              g.department,
              g.program_type,
              g.program_name,
              g.coverage_status,
              g.top_candidate_url,
              g.top_candidate_title,
              g.evidence_json
            FROM official_program_gap_reason_audit g
            WHERE g.gap_reason_status = 'source_already_loaded_related_program_review'
            ORDER BY g.program_type, g.program_name
            """
        )
    ]


def source_membership_index(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    by_url: dict[str, list[dict]] = defaultdict(list)
    for row in conn.execute(
        """
        SELECT
          s.source_url,
          pr.program_name,
          p.role,
          m.training_year_label,
          COUNT(DISTINCT p.person_key) AS person_count,
          GROUP_CONCAT(DISTINCT p.person_key) AS person_keys,
          GROUP_CONCAT(DISTINCT p.display_name) AS people
        FROM person_program_memberships m
        JOIN sources s ON s.source_key = m.source_key
        JOIN programs pr ON pr.program_key = m.program_key
        JOIN people p ON p.person_key = m.person_key
        WHERE s.source_url IS NOT NULL AND s.source_url != ''
        GROUP BY s.source_url, pr.program_name, p.role, m.training_year_label
        """
    ):
        by_url[canonical_url(row["source_url"])].append(dict(row))
    return by_url


def expected_role(program_type: str) -> str:
    if program_type == "residency":
        return "resident"
    if program_type == "fellowship":
        return "fellow"
    return ""


def relation_for(
    official: dict,
    loaded_program_name: str,
    loaded_role: str,
    labels: list[str],
    loaded_person_count: int,
) -> tuple[str, str, float, int, str]:
    official_name = official["program_name"]
    official_type = official["program_type"]
    official_tokens = tokens(official_name)
    loaded_tokens = tokens(loaded_program_name)
    label_tokens = tokens(" ".join(labels))
    title_tokens = tokens(official.get("top_candidate_title") or "")
    overlap = len(official_tokens & (loaded_tokens | label_tokens | title_tokens))
    expected = expected_role(official_type)
    role_matches = bool(expected and loaded_role == expected)
    official_norm = normalized(official_name)
    loaded_norm = normalized(loaded_program_name)
    labels_norm = normalized(" ".join(labels))
    title_norm = normalized(official.get("top_candidate_title") or "")

    if {"soft", "tissue", "bone"}.issubset(official_tokens) and {"soft", "tissue", "bone"}.issubset(loaded_tokens) and role_matches:
        return (
            "same_program_alias_candidate",
            "candidate_accept_alias_after_manual_source_check",
            0.9,
            0,
            "Official selective label and loaded fellowship label name the same Soft Tissue/Bone pathology program.",
        )
    if "transplant hepatology" in official_norm and role_matches and "transplant hepatology" in labels_norm:
        return (
            "section_level_split_candidate",
            "split_loaded_program_by_section_label",
            0.84,
            0,
            "Loaded broader advanced gastroenterology source has an explicit Advanced Transplant Hepatology Fellow section.",
        )
    if "plastic surgery" in official_norm and not role_matches:
        return (
            "official_type_or_track_mismatch_review",
            "review_official_program_type_against_integrated_independent_residency_source",
            0.72,
            0,
            "Official row is fellowship-typed, but the related loaded source is Plastic Surgery Integrated/Independent Residency residents.",
        )
    if "radiology interventional independent" in official_norm and "integrated" in loaded_norm:
        return (
            "track_split_unresolved_review",
            "find_or_confirm_independent_ir_current_roster_before_aliasing",
            0.7,
            0,
            "Official row is Interventional Radiology Independent, while loaded people are labeled Integrated IR residents.",
        )
    if "dermatology" in official_norm and "internal medicine dermatology" in loaded_norm:
        return (
            "combined_track_not_categorical_coverage",
            "do_not_mark_categorical_dermatology_covered_without_dermatology_roster",
            0.74,
            0,
            "Loaded source covers the combined Internal Medicine-Dermatology track, not necessarily categorical Dermatology residency.",
        )
    if role_matches and overlap >= max(1, min(2, len(official_tokens))):
        return (
            "probable_program_alias_candidate",
            "review_and_optionally_add_program_alias",
            0.68,
            0,
            "Official and loaded labels share role and key program tokens but need manual confirmation before coverage mutation.",
        )
    if not role_matches:
        return (
            "role_mismatch_related_source",
            "do_not_alias_without_track_specific_source",
            0.52,
            0,
            "Related source has accepted people, but their role does not match the official program type.",
        )
    return (
        "weak_related_source_review",
        "keep_gap_open_and_collect_stronger_evidence",
        0.45 if loaded_person_count else 0.3,
        0,
        "Related source has accepted people but does not provide enough label overlap for an alias decision.",
    )


def grouped_memberships(rows: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row.get("program_name") or "", row.get("role") or "")
        bucket = grouped.setdefault(
            key,
            {
                "program_name": key[0],
                "role": key[1],
                "labels": set(),
                "person_count": 0,
                "person_keys": set(),
                "people": set(),
            },
        )
        if norm_space(row.get("training_year_label")):
            bucket["labels"].add(norm_space(row.get("training_year_label")))
        for person_key in (row.get("person_keys") or "").split(","):
            if norm_space(person_key):
                bucket["person_keys"].add(norm_space(person_key))
        for person in (row.get("people") or "").split(","):
            if norm_space(person):
                bucket["people"].add(norm_space(person))
    return [
        {
            "program_name": item["program_name"],
            "role": item["role"],
            "labels": sorted(item["labels"]),
            "person_count": len(item["person_keys"]) or item["person_count"],
            "people": sorted(item["people"]),
        }
        for item in grouped.values()
    ]


def audit_rows(conn: sqlite3.Connection) -> list[dict]:
    existing = existing_audit_rows()
    by_url = source_membership_index(conn)
    audited_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for official in gap_rows(conn):
        evidence = json.loads(official.get("evidence_json") or "{}")
        related_sources = evidence.get("related_loaded_sources") or []
        for related in related_sources:
            source_url = related.get("candidate_url") or ""
            memberships = grouped_memberships(by_url.get(canonical_url(source_url), []))
            if not memberships:
                memberships = [
                    {
                        "program_name": program,
                        "role": ";".join(related.get("roles") or []),
                        "labels": [],
                        "person_count": related.get("person_count", 0),
                        "people": [],
                    }
                    for program in related.get("programs") or [""]
                ]
            for membership in memberships:
                relation_status, action, confidence, mutation_allowed, rationale = relation_for(
                    official,
                    membership["program_name"],
                    membership["role"],
                    membership["labels"],
                    int(membership["person_count"] or 0),
                )
                audit_row = {
                        "reconciliation_key": key_for(
                            official["official_program_key"],
                            source_url,
                            membership["program_name"],
                            membership["role"],
                        ),
                        "official_program_key": official["official_program_key"],
                        "official_department": official.get("department") or "",
                        "official_program_type": official["program_type"],
                        "official_program_name": official["program_name"],
                        "loaded_program_name": membership["program_name"],
                        "loaded_role": membership["role"],
                        "loaded_source_url": source_url,
                        "loaded_person_count": int(membership["person_count"] or 0),
                        "loaded_training_labels": "; ".join(membership["labels"]),
                        "relation_status": relation_status,
                        "suggested_mapping_action": action,
                        "relation_confidence": confidence,
                        "coverage_mutation_allowed": mutation_allowed,
                        "rationale": rationale,
                        "evidence_json": dumps(
                            {
                                "official": {
                                    "program_name": official["program_name"],
                                    "program_type": official["program_type"],
                                    "top_candidate_title": official.get("top_candidate_title"),
                                    "top_candidate_url": official.get("top_candidate_url"),
                                },
                                "related_source": related,
                                "loaded_membership": membership,
                                "token_overlap": sorted(tokens(official["program_name"]) & tokens(membership["program_name"])),
                            }
                        ),
                        "audited_at": audited_at,
                    }
                audit_row["audited_at"] = stable_audited_at(existing, audit_row, audited_at)
                rows.append(audit_row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_program_alias_reconciliation_candidates")
    for row in rows:
        conn.execute(
            """
            INSERT INTO official_program_alias_reconciliation_candidates
            (reconciliation_key, official_program_key, official_department,
             official_program_type, official_program_name, loaded_program_name,
             loaded_role, loaded_source_url, loaded_person_count, loaded_training_labels,
             relation_status, suggested_mapping_action, relation_confidence,
             coverage_mutation_allowed, rationale, evidence_json, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["reconciliation_key"],
                row["official_program_key"],
                row["official_department"],
                row["official_program_type"],
                row["official_program_name"],
                row["loaded_program_name"],
                row["loaded_role"],
                row["loaded_source_url"],
                row["loaded_person_count"],
                row["loaded_training_labels"],
                row["relation_status"],
                row["suggested_mapping_action"],
                row["relation_confidence"],
                row["coverage_mutation_allowed"],
                row["rationale"],
                row["evidence_json"],
                row["audited_at"],
            ),
        )


def summary_payload(rows: list[dict]) -> dict:
    return {
        "generated_at": max((row["audited_at"] for row in rows), default=datetime.now(timezone.utc).isoformat()),
        "candidate_rows": len(rows),
        "official_program_rows": len({row["official_program_key"] for row in rows}),
        "by_relation_status": dict(sorted(Counter(row["relation_status"] for row in rows).items())),
        "by_suggested_mapping_action": dict(sorted(Counter(row["suggested_mapping_action"] for row in rows).items())),
        "coverage_mutation_allowed_rows": sum(int(row["coverage_mutation_allowed"]) for row in rows),
        "csv": "artifacts/data/official_program_alias_reconciliation_candidates.csv",
        "json": "artifacts/data/official_program_alias_reconciliation_candidates.json",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = audit_rows(conn)
    summary = summary_payload(rows)
    with conn:
        write_sqlite(conn, rows)
    conn.close()

    write_csv(ARTIFACTS / "official_program_alias_reconciliation_candidates.csv", rows)
    (ARTIFACTS / "official_program_alias_reconciliation_candidates.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "official_program_alias_reconciliation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
