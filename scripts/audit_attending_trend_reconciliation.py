#!/usr/bin/env python3
"""Reconcile current-attending trend groups against bridge evidence."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

GROUPS_CSV = ARTIFACTS / "attending_trend_linkage_groups.csv"
BIOSKETCH_CSV = ARTIFACTS / "attending_biosketch_bridge_candidates.csv"
HISTORICAL_CSV = ARTIFACTS / "attending_historical_link_candidates.csv"
OUT_CSV = ARTIFACTS / "attending_trend_reconciliation.csv"
OUT_JSON = ARTIFACTS / "attending_trend_reconciliation.json"
SUMMARY_JSON = ARTIFACTS / "attending_trend_reconciliation_summary.json"

FIELDNAMES = [
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "trend_status",
    "trend_assurance_level",
    "ten_year_trend_window",
    "has_current_attending_endpoint",
    "has_penn_training_claim",
    "has_recent_dated_biosketch_bridge",
    "has_historical_link_candidate",
    "has_current_trainee_name_match",
    "bridge_candidate_keys",
    "historical_candidate_keys",
    "best_training_type",
    "best_training_line",
    "best_training_start_year",
    "best_training_end_year",
    "best_source_url",
    "required_next_evidence",
    "evidence_json",
    "audited_at",
]

ACTIONABLE_HISTORICAL_STATUSES = {
    "historical_link_source_candidate",
    "historical_roster_or_alumni_candidate",
    "historical_roster_or_alumni_bridge_candidate",
    "historical_training_search_candidate",
    "identity_bridge_candidate",
    "profile_or_cv_candidate",
    "profile_or_cv_bridge_candidate",
}


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def as_int(value: str | int | None) -> int:
    if value in {None, ""}:
        return 0
    return int(float(value))


def as_float(value: str | float | None) -> float:
    if value in {None, ""}:
        return 0.0
    return float(value)


def trend_key_for(event_group_key: str) -> str:
    digest = hashlib.sha1(event_group_key.encode("utf-8")).hexdigest()[:16]
    return f"attending_trend_{digest}"


def group_rows(rows: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row.get(key) or ""].append(row)
    return grouped


def best_biosketch_bridge(rows: list[dict]) -> dict:
    if not rows:
        return {}
    return sorted(
        rows,
        key=lambda row: (
            row.get("bridge_status") != "dated_recent_official_biosketch_training_bridge_candidate",
            -as_int(row.get("bridge_assurance_level")),
            -as_float(row.get("confidence")),
            -(as_int(row.get("end_year")) or 0),
            row.get("source_url") or "",
        ),
    )[0]


def trend_window(group: dict, bridge_rows: list[dict], historical_rows: list[dict]) -> str:
    if any(row.get("ten_year_trend_window") == "yes" for row in bridge_rows):
        return "yes"
    if any(row.get("ten_year_trend_window") == "no" for row in bridge_rows):
        return "no"
    group_windows = {item.strip() for item in (group.get("ten_year_windows") or "").split(";") if item.strip()}
    if "yes" in group_windows:
        return "yes"
    if "no" in group_windows and "unknown" not in group_windows:
        return "no"
    if any(row.get("candidate_status") in ACTIONABLE_HISTORICAL_STATUSES for row in historical_rows):
        return "unknown"
    return "unknown"


def classify(group: dict, bridge_rows: list[dict], historical_rows: list[dict]) -> tuple[str, int, str]:
    has_endpoint = as_int(group.get("has_current_attending_endpoint"))
    has_training = as_int(group.get("has_penn_training_claim"))
    has_name_match = as_int(group.get("has_current_trainee_name_match"))
    has_recent_bridge = any(
        row.get("bridge_status") == "dated_recent_official_biosketch_training_bridge_candidate"
        and row.get("ten_year_trend_window") == "yes"
        and row.get("training_type") in {"fellowship", "residency", "internship"}
        for row in bridge_rows
    )
    has_dated_bridge = any(
        row.get("bridge_status")
        in {
            "dated_recent_official_biosketch_training_bridge_candidate",
            "dated_official_biosketch_training_bridge_candidate",
        }
        for row in bridge_rows
    )
    has_actionable_historical = any(
        row.get("candidate_status") in ACTIONABLE_HISTORICAL_STATUSES for row in historical_rows
    )

    if has_endpoint and has_training and has_recent_bridge:
        return (
            "review_ready_official_biosketch_bridge",
            4,
            "Review official biosketch training line against the current attending endpoint; after reviewer acceptance, it can support a recent Penn-trained current-attending trend record.",
        )
    if has_endpoint and has_training and has_dated_bridge:
        return (
            "dated_biosketch_bridge_outside_or_unknown_window",
            3,
            "Review dated official biosketch line; it supplies identity/training context but does not yet prove a recent ten-year trend row.",
        )
    if has_endpoint and has_training and has_actionable_historical:
        return (
            "historical_link_candidate_review",
            3,
            "Review historical-link candidate for explicit same-person, Penn-training, program, and date anchors.",
        )
    if has_name_match:
        return (
            "current_trainee_name_match_review",
            2,
            "Name match alone is not enough; require profile, dated training, or independent identity anchors.",
        )
    if has_endpoint and has_training:
        return (
            "profile_claim_still_needs_dated_bridge",
            2,
            "Current Penn endpoint and Penn-training profile claim exist, but a dated bridge source is still missing.",
        )
    if has_endpoint:
        return (
            "current_endpoint_needs_training_claim",
            1,
            "Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence.",
        )
    return (
        "context_only_not_trend_ready",
        0,
        "This group lacks the endpoint and bridge evidence required for attending trend analysis.",
    )


def reconciliation_rows(
    groups: list[dict],
    biosketch_by_group: dict[str, list[dict]],
    historical_by_group: dict[str, list[dict]],
) -> list[dict]:
    audited_at = datetime.now(timezone.utc).isoformat()
    output = []
    for group in groups:
        key = group.get("event_group_key") or ""
        bridge_rows = biosketch_by_group.get(key, [])
        historical_rows = historical_by_group.get(key, [])
        best_bridge = best_biosketch_bridge(bridge_rows)
        status, assurance, required = classify(group, bridge_rows, historical_rows)
        recent_bridge = int(status == "review_ready_official_biosketch_bridge")
        actionable_historical = [
            row
            for row in historical_rows
            if row.get("candidate_status") in ACTIONABLE_HISTORICAL_STATUSES
        ]
        evidence = {
            "linkage_group": group,
            "biosketch_bridge_candidates": bridge_rows,
            "historical_link_candidates": historical_rows,
            "classification_inputs": {
                "actionable_historical_statuses": sorted(ACTIONABLE_HISTORICAL_STATUSES),
                "recent_bridge_candidate_count": sum(
                    1
                    for row in bridge_rows
                    if row.get("bridge_status") == "dated_recent_official_biosketch_training_bridge_candidate"
                ),
                "actionable_historical_candidate_count": len(actionable_historical),
            },
        }
        output.append(
            {
                "trend_key": trend_key_for(key),
                "event_group_key": key,
                "display_name": group.get("display_name") or "",
                "normalized_name": group.get("normalized_name") or "",
                "trend_status": status,
                "trend_assurance_level": assurance,
                "ten_year_trend_window": trend_window(group, bridge_rows, historical_rows),
                "has_current_attending_endpoint": as_int(group.get("has_current_attending_endpoint")),
                "has_penn_training_claim": as_int(group.get("has_penn_training_claim")),
                "has_recent_dated_biosketch_bridge": recent_bridge,
                "has_historical_link_candidate": int(bool(actionable_historical)),
                "has_current_trainee_name_match": as_int(group.get("has_current_trainee_name_match")),
                "bridge_candidate_keys": "; ".join(row.get("candidate_key") or "" for row in bridge_rows if row.get("candidate_key")),
                "historical_candidate_keys": "; ".join(
                    row.get("candidate_key") or "" for row in actionable_historical if row.get("candidate_key")
                ),
                "best_training_type": best_bridge.get("training_type") or "",
                "best_training_line": best_bridge.get("training_line") or "",
                "best_training_start_year": best_bridge.get("start_year") or "",
                "best_training_end_year": best_bridge.get("end_year") or "",
                "best_source_url": best_bridge.get("source_url") or "",
                "required_next_evidence": required,
                "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
                "audited_at": audited_at,
            }
        )
    return sorted(
        output,
        key=lambda row: (
            -as_int(row["trend_assurance_level"]),
            row["trend_status"],
            row["display_name"],
        ),
    )


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM attending_trend_reconciliation")
    for row in rows:
        conn.execute(
            """
            INSERT INTO attending_trend_reconciliation
            (trend_key, event_group_key, display_name, normalized_name, trend_status,
             trend_assurance_level, ten_year_trend_window, has_current_attending_endpoint,
             has_penn_training_claim, has_recent_dated_biosketch_bridge,
             has_historical_link_candidate, has_current_trainee_name_match,
             bridge_candidate_keys, historical_candidate_keys, best_training_type,
             best_training_line, best_training_start_year, best_training_end_year,
             best_source_url, required_next_evidence, evidence_json, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(row[field] for field in FIELDNAMES),
        )


def write_summary(rows: list[dict], as_of_year: int) -> None:
    summary = {
        "generated_at": max((row["audited_at"] for row in rows), default=datetime.now(timezone.utc).isoformat()),
        "as_of_year": as_of_year,
        "trend_rows": len(rows),
        "by_trend_status": dict(sorted(Counter(row["trend_status"] for row in rows).items())),
        "by_assurance_level": dict(sorted(Counter(str(row["trend_assurance_level"]) for row in rows).items())),
        "by_ten_year_trend_window": dict(sorted(Counter(row["ten_year_trend_window"] for row in rows).items())),
        "review_ready_recent_bridge_rows": sum(
            1 for row in rows if row["trend_status"] == "review_ready_official_biosketch_bridge"
        ),
        "groups_with_current_endpoint": sum(as_int(row["has_current_attending_endpoint"]) for row in rows),
        "groups_with_penn_training_claim": sum(as_int(row["has_penn_training_claim"]) for row in rows),
        "groups_with_recent_dated_biosketch_bridge": sum(
            as_int(row["has_recent_dated_biosketch_bridge"]) for row in rows
        ),
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--groups-csv", type=Path, default=GROUPS_CSV)
    parser.add_argument("--biosketch-csv", type=Path, default=BIOSKETCH_CSV)
    parser.add_argument("--historical-csv", type=Path, default=HISTORICAL_CSV)
    parser.add_argument("--as-of-year", type=int, default=2026)
    args = parser.parse_args()

    groups = read_csv(args.groups_csv)
    biosketch_by_group = group_rows(read_csv(args.biosketch_csv), "event_group_key")
    historical_by_group = group_rows(read_csv(args.historical_csv), "event_group_key")
    rows = reconciliation_rows(groups, biosketch_by_group, historical_by_group)

    conn = sqlite3.connect(args.db)
    with conn:
        write_sqlite(conn, rows)
    conn.close()

    write_csv(OUT_CSV, rows)
    OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, args.as_of_year)


if __name__ == "__main__":
    main()
