#!/usr/bin/env python3
"""Generate a per-person enrichment queue from the SQLite warehouse."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"


def quote(value: str) -> str:
    value = (value or "").strip()
    return f'"{value}"' if value else ""


def load_people(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return conn.execute(
        """
        SELECT
          p.person_key,
          p.display_name,
          p.role,
          p.current_status,
          p.profile_url,
          p.raw_json
        FROM people p
        WHERE p.role IN ('resident', 'fellow')
        ORDER BY p.role, p.display_name
        """
    ).fetchall()


def training_map(conn: sqlite3.Connection) -> dict[str, dict[str, list[str]]]:
    out: dict[str, dict[str, list[str]]] = {}
    for row in conn.execute(
        """
        SELECT person_key, event_type, canonical_name
        FROM v_person_training
        WHERE canonical_name IS NOT NULL
        """
    ):
        out.setdefault(row["person_key"], {}).setdefault(row["event_type"], [])
        if row["canonical_name"] not in out[row["person_key"]][row["event_type"]]:
            out[row["person_key"]][row["event_type"]].append(row["canonical_name"])
    return out


def program_map(conn: sqlite3.Connection) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for row in conn.execute(
        """
        SELECT m.person_key, pr.program_name
        FROM person_program_memberships m
        JOIN programs pr ON pr.program_key = m.program_key
        ORDER BY pr.program_name
        """
    ):
        out.setdefault(row["person_key"], [])
        if row["program_name"] not in out[row["person_key"]]:
            out[row["person_key"]].append(row["program_name"])
    return out


def make_queue(conn: sqlite3.Connection) -> list[dict]:
    people = load_people(conn)
    trainings = training_map(conn)
    programs = program_map(conn)
    queue = []
    for person in people:
        raw = json.loads(person["raw_json"])
        name = person["display_name"]
        program = (programs.get(person["person_key"]) or [raw.get("program", "")])[0]
        school = (trainings.get(person["person_key"], {}).get("medical_school") or [""])[0]
        residency = (trainings.get(person["person_key"], {}).get("residency_program") or [""])[0]
        base = {
            "person_key": person["person_key"],
            "name": name,
            "role": person["role"],
            "program": program,
            "medical_school": school,
            "residency_program": residency,
        }
        if not person["profile_url"]:
            queue.append(
                {
                    **base,
                    "task_type": "official_profile_search",
                    "priority": 90,
                    "query": " ".join(
                        token
                        for token in [
                            quote(name),
                            quote("Penn Medicine"),
                            quote(program),
                            "profile",
                        ]
                        if token
                    ),
                    "acceptance_rule": "Accept only if the page is official Penn/Penn Medicine/CHOP or directly linked from an official roster.",
                }
            )
        queue.append(
            {
                **base,
                "task_type": "publication_identity_search",
                "priority": 70 if person["role"] == "fellow" else 55,
                "query": " ".join(
                    token
                    for token in [
                        quote(name),
                        "PubMed OR ORCID OR OpenAlex",
                        quote("University of Pennsylvania"),
                        quote(program),
                    ]
                    if token
                ),
                "acceptance_rule": "Attach publications only with at least two identity anchors beyond name.",
            }
        )
        if residency:
            queue.append(
                {
                    **base,
                    "task_type": "prior_training_profile_search",
                    "priority": 45,
                    "query": " ".join(
                        token
                        for token in [
                            quote(name),
                            quote(residency),
                            "resident OR fellow OR profile",
                        ]
                        if token
                    ),
                    "acceptance_rule": "Treat prior profile pages as enrichment candidates, not current-roster truth.",
                }
            )
    return sorted(queue, key=lambda row: (-row["priority"], row["role"], row["name"], row["task_type"]))


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    queue = make_queue(conn)
    conn.close()
    (ARTIFACTS / "person_enrichment_queue.json").write_text(
        json.dumps(queue, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    with (ARTIFACTS / "person_enrichment_queue.csv").open("w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "person_key",
            "name",
            "role",
            "program",
            "medical_school",
            "residency_program",
            "task_type",
            "priority",
            "query",
            "acceptance_rule",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(queue)
    print(f"wrote {len(queue)} enrichment tasks")


if __name__ == "__main__":
    main()
