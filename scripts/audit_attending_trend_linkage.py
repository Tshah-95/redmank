#!/usr/bin/env python3
"""Audit whether attending/faculty career events can support Penn trainee trend links."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"


STATUS_PRIORITY = {
    "current_trainee_name_match_review": 100,
    "current_trainee_name_collision_review": 95,
    "profile_penn_training_claim_needs_historical_roster": 85,
    "current_attending_with_penn_training_claim_unlinked": 75,
    "current_attending_endpoint_unlinked": 55,
    "profile_context_non_penn_training": 35,
    "outcome_context_only_no_person": 25,
    "source_context_only_no_person": 10,
}


def norm_space(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalized_person_name(value: str | None) -> str:
    value = norm_space(value).lower()
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(
        r"\b(md|m\.d\.|do|d\.o\.|phd|ph\.d\.|mbe|msce|mse?d|msc|m\.sc\.|mph|mba|ms|m\.s\.|ma|m\.a\.|facp|faahpm)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return norm_space(value)


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def load_people(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = defaultdict(list)
    for row in rows(
        conn,
        """
        SELECT p.person_key, p.display_name, p.role, p.current_status, p.profile_url,
               GROUP_CONCAT(DISTINCT pr.program_name) AS programs,
               GROUP_CONCAT(DISTINCT s.normalized_stage) AS normalized_stages
        FROM people p
        LEFT JOIN person_program_memberships m ON m.person_key = p.person_key
        LEFT JOIN programs pr ON pr.program_key = m.program_key
        LEFT JOIN person_training_states s ON s.person_key = p.person_key
        GROUP BY p.person_key, p.display_name, p.role, p.current_status, p.profile_url
        """,
    ):
        index[normalized_person_name(row["display_name"])].append(row)
    return index


def load_events(conn: sqlite3.Connection) -> list[dict]:
    return rows(
        conn,
        """
        SELECT career_event_id, person_key, display_name, event_type, role_title,
               organization_name, department, program_context, event_year,
               source_key, source_url, confidence, status, match_features_json,
               evidence_json
        FROM career_events
        ORDER BY display_name, event_type, confidence DESC, career_event_id
        """,
    )


def load_decisions() -> dict[int, dict]:
    path = ARTIFACTS / "evidence_reconciliation_decisions.csv"
    if not path.exists():
        return {}
    result = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("record_type") == "career_event" and row.get("record_id"):
                result[int(row["record_id"])] = row
    return result


def ten_year_window(event_year: int | None, as_of_year: int) -> str:
    if not event_year:
        return "unknown"
    return "yes" if event_year >= as_of_year - 10 else "no"


def event_status(event: dict, features: set[str], matches: list[dict], group: list[dict]) -> tuple[str, str, int, str]:
    has_group_penn_training = any(
        item["event_type"] == "attending_profile_training_history_candidate"
        and item["role_title"] == "penn_training_history_candidate"
        for item in group
    )
    if matches:
        if len(matches) > 1:
            return (
                "current_trainee_name_collision_review",
                "Name matches multiple current trainee rows; do not link without disambiguating anchors.",
                1,
                "Find profile URL, training date, program, or independent identity anchor before linking.",
            )
        return (
            "current_trainee_name_match_review",
            "Name matches one current trainee row, but this is not sufficient for an attending trend link.",
            1,
            "Verify whether the attending event and trainee record describe the same person, then reconcile dates and program.",
        )
    if not normalized_person_name(event.get("display_name")):
        if event["event_type"] == "penn_alumni_outcome_candidate":
            return (
                "outcome_context_only_no_person",
                "Outcome/alumni source has no resolved person name in the extracted event.",
                0,
                "Extract named alumni from the source page before identity reconciliation.",
            )
        return (
            "source_context_only_no_person",
            "Career source is useful context but no person identity was extracted.",
            0,
            "Extract named people and dated outcomes from the source page.",
        )
    if event["event_type"] == "attending_profile_training_history_candidate" and event["role_title"] == "penn_training_history_candidate":
        return (
            "profile_penn_training_claim_needs_historical_roster",
            "Official Penn profile contains Penn-training language, but no historical trainee identity is linked.",
            2,
            "Search historical Penn roster/alumni/CV/profile evidence for a dated Penn trainee record.",
        )
    if event["event_type"] == "current_penn_attending_candidate" and has_group_penn_training:
        return (
            "current_attending_with_penn_training_claim_unlinked",
            "Current Penn attending endpoint has a same-name Penn-training profile claim in this event group.",
            2,
            "Link endpoint and training claim to a historical trainee identity before trend analysis.",
        )
    if event["event_type"] == "current_penn_attending_candidate":
        return (
            "current_attending_endpoint_unlinked",
            "Current Penn attending/faculty endpoint candidate lacks linked Penn training-history evidence.",
            1,
            "Find profile, CV, employment-start, or training-history evidence before using as a trend endpoint.",
        )
    if event["event_type"] == "attending_profile_training_history_candidate":
        return (
            "profile_context_non_penn_training",
            "Official profile context is useful enrichment but is not itself a Penn trainee trend link.",
            1,
            "Keep as background unless it supplies a non-name identity anchor for another claim.",
        )
    return (
        "source_context_only_no_person",
        "Career event remains contextual until identity and date are reconciled.",
        0,
        "Resolve identity and event date before trend use.",
    )


def audit_events(events: list[dict], people_index: dict[str, list[dict]], decisions: dict[int, dict], as_of_year: int) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        name_key = normalized_person_name(event.get("display_name"))
        group_key = name_key or f"source:{event.get('source_url') or event['career_event_id']}"
        grouped[group_key].append(event)

    output = []
    for group_key, group in grouped.items():
        for event in group:
            name_key = normalized_person_name(event.get("display_name"))
            matches = people_index.get(name_key, [])
            features = set(parse_json(event.get("match_features_json"), []))
            event_year = event.get("event_year")
            event_year_int = int(event_year) if event_year not in {None, ""} else None
            status, rationale, assurance, required = event_status(event, features, matches, group)
            decision = decisions.get(event["career_event_id"], {})
            output.append(
                {
                    "career_event_id": event["career_event_id"],
                    "event_group_key": group_key,
                    "display_name": event.get("display_name") or "",
                    "normalized_name": name_key,
                    "event_type": event.get("event_type") or "",
                    "claim_type": event.get("role_title") or "",
                    "organization_name": event.get("organization_name") or "",
                    "department": event.get("department") or "",
                    "program_context": event.get("program_context") or "",
                    "event_year": event_year or "",
                    "ten_year_trend_window": ten_year_window(event_year_int, as_of_year),
                    "source_key": event.get("source_key") or "",
                    "source_url": event.get("source_url") or "",
                    "event_status": event.get("status") or "",
                    "event_confidence": event.get("confidence") or 0,
                    "linkage_status": status,
                    "linkage_priority": STATUS_PRIORITY[status],
                    "trend_link_assurance_level": assurance,
                    "linkage_rationale": rationale,
                    "required_next_evidence": required,
                    "reconciliation_decision": decision.get("decision", ""),
                    "reconciliation_required_next_evidence": decision.get("required_next_evidence", ""),
                    "current_trainee_match_count": len(matches),
                    "current_trainee_match_keys": "; ".join(match["person_key"] for match in matches[:5]),
                    "current_trainee_match_roles": "; ".join(sorted({match["role"] for match in matches if match.get("role")})),
                    "current_trainee_match_programs": "; ".join(
                        sorted({match["programs"] for match in matches if match.get("programs")})[:5]
                    ),
                    "match_features": "; ".join(sorted(features)),
                }
            )
    return sorted(output, key=lambda row: (-row["linkage_priority"], row["display_name"], row["career_event_id"]))


def rollup_groups(rows_for_events: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows_for_events:
        grouped[row["event_group_key"]].append(row)
    output = []
    for group_key, group in grouped.items():
        best = max(group, key=lambda row: (row["linkage_priority"], float(row["event_confidence"] or 0)))
        statuses = Counter(row["linkage_status"] for row in group)
        event_types = Counter(row["event_type"] for row in group)
        years = sorted({str(row["event_year"]) for row in group if row.get("event_year")})
        urls = sorted({row["source_url"] for row in group if row.get("source_url")})
        output.append(
            {
                "event_group_key": group_key,
                "display_name": best["display_name"],
                "normalized_name": best["normalized_name"],
                "event_count": len(group),
                "event_types_json": json.dumps(dict(sorted(event_types.items())), sort_keys=True),
                "best_linkage_status": best["linkage_status"],
                "best_trend_link_assurance_level": best["trend_link_assurance_level"],
                "best_required_next_evidence": best["required_next_evidence"],
                "has_current_attending_endpoint": int(any(row["event_type"] == "current_penn_attending_candidate" for row in group)),
                "has_penn_training_claim": int(
                    any(row["claim_type"] == "penn_training_history_candidate" for row in group)
                ),
                "has_current_trainee_name_match": int(any(row["current_trainee_match_count"] for row in group)),
                "current_trainee_match_keys": "; ".join(
                    sorted({key for row in group for key in row["current_trainee_match_keys"].split("; ") if key})
                ),
                "ten_year_windows": "; ".join(sorted({row["ten_year_trend_window"] for row in group if row["ten_year_trend_window"]})),
                "event_years": "; ".join(years),
                "source_urls": "; ".join(urls[:5]),
                "linkage_status_counts_json": json.dumps(dict(sorted(statuses.items())), sort_keys=True),
            }
        )
    return sorted(output, key=lambda row: (-int(row["best_trend_link_assurance_level"]), row["display_name"]))


def write_csv(path: Path, output_rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not output_rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)


def write_outputs(event_rows: list[dict], group_rows: list[dict], as_of_year: int) -> None:
    summary = {
        "as_of_year": as_of_year,
        "event_rows": len(event_rows),
        "event_group_rows": len(group_rows),
        "by_linkage_status": dict(sorted(Counter(row["linkage_status"] for row in event_rows).items())),
        "by_event_type": dict(sorted(Counter(row["event_type"] for row in event_rows).items())),
        "by_ten_year_trend_window": dict(sorted(Counter(row["ten_year_trend_window"] for row in event_rows).items())),
        "by_assurance_level": dict(
            sorted(Counter(str(row["trend_link_assurance_level"]) for row in event_rows).items())
        ),
        "groups_with_current_endpoint": sum(row["has_current_attending_endpoint"] for row in group_rows),
        "groups_with_penn_training_claim": sum(row["has_penn_training_claim"] for row in group_rows),
        "groups_with_current_trainee_name_match": sum(row["has_current_trainee_name_match"] for row in group_rows),
        "linkage_event_csv": "artifacts/data/attending_trend_linkage_events.csv",
        "linkage_group_csv": "artifacts/data/attending_trend_linkage_groups.csv",
    }
    write_csv(ARTIFACTS / "attending_trend_linkage_events.csv", event_rows)
    write_csv(ARTIFACTS / "attending_trend_linkage_groups.csv", group_rows)
    (ARTIFACTS / "attending_trend_linkage_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--as-of-year", type=int, default=date.today().year)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    people = load_people(conn)
    events = load_events(conn)
    conn.close()
    event_rows = audit_events(events, people, load_decisions(), args.as_of_year)
    group_rows = rollup_groups(event_rows)
    write_outputs(event_rows, group_rows, args.as_of_year)


if __name__ == "__main__":
    main()
