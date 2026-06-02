#!/usr/bin/env python3
"""Materialize no-network historical-link query plans for attending trend gaps."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

GROUPS_CSV = ARTIFACTS / "attending_trend_linkage_groups.csv"
QUERY_CSV = ARTIFACTS / "attending_historical_link_search_queries.csv"
SUMMARY_JSON = ARTIFACTS / "attending_historical_link_query_plan_summary.json"
DDG_HTML = "https://html.duckduckgo.com/html/"

FIELDS = [
    "query_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "query_kind",
    "query",
    "query_url",
]

csv.field_size_limit(sys.maxsize)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def normalized_name(value: str) -> str:
    value = norm(value).lower()
    value = re.sub(
        r"\b(md|m\.d\.|do|d\.o\.|phd|ph\.d\.|mbe|msce|mse?d|msc|m\.sc\.|mph|mba|ms|m\.s\.|ma|m\.a\.|facp|faahpm)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return norm(value)


def slug_key(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:72]
    return f"{prefix}_{slug}_{digest}"


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def has_flag(row: dict, key: str) -> bool:
    return str(row.get(key) or "0") == "1"


def selected_groups(groups: list[dict], include_endpoint_only: bool) -> list[dict]:
    selected = []
    for row in groups:
        if has_flag(row, "has_penn_training_claim"):
            selected.append(row)
        elif include_endpoint_only and has_flag(row, "has_current_attending_endpoint"):
            selected.append(row)
    return sorted(
        selected,
        key=lambda row: (
            -int(row.get("has_penn_training_claim") or 0),
            -int(row.get("has_current_attending_endpoint") or 0),
            -int(row.get("best_trend_link_assurance_level") or 0),
            row.get("display_name") or "",
        ),
    )


def query_specs(row: dict) -> list[dict]:
    display_name = row["display_name"]
    plain = row.get("normalized_name") or normalized_name(display_name)
    query_templates = [
        ("historical_penn_training", f'"{plain}" "University of Pennsylvania" fellowship'),
        ("historical_penn_training", f'"{plain}" "Penn" fellowship'),
        ("historical_penn_training", f'"{plain}" "University of Pennsylvania" residency'),
        ("historical_penn_training", f'"{plain}" "Hospital of the University of Pennsylvania"'),
        ("official_penn_profile", f'site:pennmedicine.org "{plain}"'),
        ("historical_penn_training", f'"{display_name}" "University of Pennsylvania" fellowship'),
        ("historical_penn_training", f'"{display_name}" "Penn" fellowship'),
        ("historical_penn_training", f'"{display_name}" "Penn Medicine" residency fellowship'),
        ("historical_penn_training", f'"{display_name}" "Hospital of the University of Pennsylvania"'),
        ("historical_roster_or_alumni", f'"{display_name}" Penn alumni fellow resident'),
        ("historical_roster_or_alumni", f'"{display_name}" Penn "class of" resident fellow'),
        ("official_penn_profile", f'site:pennmedicine.org "{display_name}"'),
        ("upenn_profile_or_cv", f'site:upenn.edu "{display_name}" fellowship OR residency'),
        ("upenn_profile_or_cv", f'site:med.upenn.edu "{display_name}" CV OR "curriculum vitae"'),
    ]
    seen = set()
    rows = []
    for query_kind, query in query_templates:
        if query in seen:
            continue
        seen.add(query)
        rows.append(
            {
                "query_key": slug_key("attending_history_query", f"{row['event_group_key']}:{query_kind}:{query}"),
                "event_group_key": row["event_group_key"],
                "display_name": display_name,
                "normalized_name": plain,
                "query_kind": query_kind,
                "query": query,
                "query_url": f"{DDG_HTML}?q={quote_plus(query)}",
            }
        )
    return rows


def merge_queries(existing_rows: list[dict], planned_rows: list[dict]) -> tuple[list[dict], int, int]:
    merged: dict[str, dict] = {}
    for row in existing_rows:
        if not row.get("query_key"):
            continue
        merged[row["query_key"]] = {field: row.get(field, "") for field in FIELDS}
    existing_count = len(merged)
    for row in planned_rows:
        merged[row["query_key"]] = row
    return sorted(merged.values(), key=lambda row: (row["event_group_key"], row["query_kind"], row["query"])), existing_count, len(merged) - existing_count


def write_db(rows: list[dict]) -> None:
    with sqlite3.connect(DB) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("DELETE FROM attending_historical_link_search_queries")
        conn.executemany(
            """
            INSERT INTO attending_historical_link_search_queries
            (query_key, event_group_key, display_name, normalized_name, query_kind, query, query_url)
            VALUES
            (:query_key, :event_group_key, :display_name, :normalized_name, :query_kind, :query, :query_url)
            """,
            rows,
        )
        conn.commit()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-endpoint-only", action="store_true", help="Only plan groups with explicit Penn-training claims.")
    args = parser.parse_args()

    generated_at = now_utc()
    groups = read_csv(GROUPS_CSV)
    targets = selected_groups(groups, include_endpoint_only=not args.no_endpoint_only)
    planned_rows = [query for group in targets for query in query_specs(group)]
    existing_rows = read_csv(QUERY_CSV)
    merged_rows, existing_count, added_count = merge_queries(existing_rows, planned_rows)

    write_csv(QUERY_CSV, merged_rows)
    write_db(merged_rows)

    target_group_keys = {row["event_group_key"] for row in targets}
    existing_group_keys = {row.get("event_group_key") for row in existing_rows if row.get("event_group_key")}
    summary = {
        "generated_at": generated_at,
        "policy": "No-network query planning only. Query rows are search/probe work instructions and do not imply a historical training bridge exists.",
        "group_rows_available": len(groups),
        "target_group_rows": len(targets),
        "target_endpoint_only_groups": sum(
            1 for row in targets if has_flag(row, "has_current_attending_endpoint") and not has_flag(row, "has_penn_training_claim")
        ),
        "target_penn_training_claim_groups": sum(1 for row in targets if has_flag(row, "has_penn_training_claim")),
        "existing_query_rows": existing_count,
        "planned_query_rows": len(planned_rows),
        "added_query_rows": added_count,
        "merged_query_rows": len(merged_rows),
        "newly_planned_group_rows": len(target_group_keys - existing_group_keys),
        "by_query_kind": dict(sorted(Counter(row["query_kind"] for row in merged_rows).items())),
        "csv": "artifacts/data/attending_historical_link_search_queries.csv",
    }
    SUMMARY_JSON.write_text(dumps(summary) + "\n", encoding="utf-8")
    print(dumps(summary))


if __name__ == "__main__":
    main()
