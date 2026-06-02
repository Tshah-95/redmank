#!/usr/bin/env python3
"""Materialize review-ready recent attending trend claims and rollups."""

from __future__ import annotations

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

CLAIMS_CSV = ARTIFACTS / "attending_trend_review_claims.csv"
CLAIMS_JSON = ARTIFACTS / "attending_trend_review_claims.json"
ROLLUPS_CSV = ARTIFACTS / "attending_trend_review_rollups.csv"
ROLLUPS_JSON = ARTIFACTS / "attending_trend_review_rollups.json"
SUMMARY_JSON = ARTIFACTS / "attending_trend_review_claims_summary.json"

REVIEW_READY_STATUS = "review_ready_official_biosketch_bridge"
BRIDGE_STATUS = "dated_recent_official_biosketch_training_bridge_candidate"
TREND_CLAIM_TYPE = "recent_penn_trained_current_attending_candidate"
SOURCE_KEY = "official_penn_faculty_biosketch"
ACCEPTANCE_POLICY = (
    "Materialize only current Penn attending groups with a dated recent official Penn Faculty "
    "Biosketch residency/fellowship/internship bridge. A separate provider-page Penn-training "
    "claim is useful corroboration but is not required when the official biosketch itself "
    "supplies the dated Penn training line. Keep as review-ready until an explicit reviewer "
    "acceptance decision is recorded."
)
DISPLAY_SAFETY_STATUS = "review_ready_not_accepted_trend_fact"
REQUIRED_REVIEWER_ACTION = (
    "Confirm same-person identity, current Penn endpoint, training line, program type, and dates "
    "before promoting to an accepted trend fact."
)

CLAIM_FIELDS = [
    "trend_claim_key",
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "trend_claim_type",
    "trend_status",
    "trend_assurance_level",
    "ten_year_trend_window",
    "training_type",
    "training_line",
    "training_organization",
    "training_start_year",
    "training_end_year",
    "source_key",
    "source_url",
    "source_scope",
    "bridge_candidate_key",
    "has_current_attending_endpoint",
    "has_penn_training_claim",
    "has_recent_dated_biosketch_bridge",
    "acceptance_policy",
    "display_safety_status",
    "required_reviewer_action",
    "evidence_json",
    "materialized_at",
]

ROLLUP_FIELDS = [
    "trend_rollup_key",
    "rollup_scope",
    "rollup_value",
    "training_type",
    "training_end_year",
    "ten_year_trend_window",
    "source_scope",
    "claim_count",
    "person_count",
    "evidence_json",
    "materialized_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def as_int(value) -> int:
    if value in {None, ""}:
        return 0
    return int(float(value))


def load_existing(path: Path, key_field: str) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row[key_field]: row for row in csv.DictReader(handle)}


def stable_time(existing: dict[str, dict], key_field: str, fields: list[str], row: dict, timestamp: str) -> str:
    prior = existing.get(row[key_field])
    if not prior:
        return timestamp
    for field in fields:
        if field == "materialized_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("materialized_at") or timestamp


def sqlite_rows(conn: sqlite3.Connection, query: str, params: tuple = ()) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query, params)]


def bridge_candidates(conn: sqlite3.Connection) -> dict[str, dict]:
    return {
        row["candidate_key"]: row
        for row in sqlite_rows(
            conn,
            """
            SELECT *
            FROM attending_biosketch_bridge_candidates
            WHERE bridge_status = ?
            """,
            (BRIDGE_STATUS,),
        )
    }


def choose_bridge(trend: dict, bridges: dict[str, dict]) -> dict:
    keys = [key.strip() for key in (trend.get("bridge_candidate_keys") or "").split(";") if key.strip()]
    candidates = [bridges[key] for key in keys if key in bridges]
    if not candidates:
        return {}
    return sorted(
        candidates,
        key=lambda row: (
            row.get("source_url") != trend.get("best_source_url"),
            row.get("training_line") != trend.get("best_training_line"),
            -as_int(row.get("end_year")),
            row.get("candidate_key") or "",
        ),
    )[0]


def claim_key_for(trend: dict, bridge: dict) -> str:
    basis = "|".join(
        [
            trend.get("trend_key") or "",
            bridge.get("candidate_key") or "",
            trend.get("display_name") or "",
            str(trend.get("best_training_end_year") or ""),
        ]
    )
    return f"attending_trend_review_{sha256_text(basis)[:20]}"


def materialize_claims(conn: sqlite3.Connection) -> list[dict]:
    existing = load_existing(CLAIMS_CSV, "trend_claim_key")
    timestamp = now_utc()
    bridges = bridge_candidates(conn)
    trends = sqlite_rows(
        conn,
        """
        SELECT *
        FROM attending_trend_reconciliation
        WHERE trend_status = ?
          AND ten_year_trend_window = 'yes'
          AND has_current_attending_endpoint = 1
          AND has_recent_dated_biosketch_bridge = 1
        ORDER BY best_training_end_year DESC, display_name
        """,
        (REVIEW_READY_STATUS,),
    )
    claims = []
    for trend in trends:
        bridge = choose_bridge(trend, bridges)
        evidence = {
            "attending_trend_reconciliation": trend,
            "selected_biosketch_bridge_candidate": bridge,
            "policy": {
                "acceptance_policy": ACCEPTANCE_POLICY,
                "display_safety_status": DISPLAY_SAFETY_STATUS,
                "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
            },
        }
        row = {
            "trend_claim_key": claim_key_for(trend, bridge),
            "trend_key": trend["trend_key"],
            "event_group_key": trend["event_group_key"],
            "display_name": trend["display_name"],
            "normalized_name": trend["normalized_name"],
            "trend_claim_type": TREND_CLAIM_TYPE,
            "trend_status": trend["trend_status"],
            "trend_assurance_level": as_int(trend["trend_assurance_level"]),
            "ten_year_trend_window": trend["ten_year_trend_window"],
            "training_type": bridge.get("training_type") or trend.get("best_training_type") or "",
            "training_line": bridge.get("training_line") or trend.get("best_training_line") or "",
            "training_organization": bridge.get("organization_name") or "",
            "training_start_year": as_int(bridge.get("start_year") or trend.get("best_training_start_year")),
            "training_end_year": as_int(bridge.get("end_year") or trend.get("best_training_end_year")),
            "source_key": SOURCE_KEY,
            "source_url": bridge.get("source_url") or trend.get("best_source_url") or "",
            "source_scope": bridge.get("source_scope") or SOURCE_KEY,
            "bridge_candidate_key": bridge.get("candidate_key") or "",
            "has_current_attending_endpoint": as_int(trend["has_current_attending_endpoint"]),
            "has_penn_training_claim": as_int(trend["has_penn_training_claim"]),
            "has_recent_dated_biosketch_bridge": as_int(trend["has_recent_dated_biosketch_bridge"]),
            "acceptance_policy": ACCEPTANCE_POLICY,
            "display_safety_status": DISPLAY_SAFETY_STATUS,
            "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
            "evidence_json": dumps(evidence),
            "materialized_at": "",
        }
        row["materialized_at"] = stable_time(existing, "trend_claim_key", CLAIM_FIELDS, row, timestamp)
        claims.append(row)
    return claims


def rollup_key(parts: tuple) -> str:
    return f"attending_trend_rollup_{sha256_text(dumps(parts))[:20]}"


def materialize_rollups(claims: list[dict]) -> list[dict]:
    existing = load_existing(ROLLUPS_CSV, "trend_rollup_key")
    timestamp = now_utc()
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for claim in claims:
        scopes = [
            ("corpus", "recent_penn_trained_current_attending_candidates"),
            ("training_type", claim["training_type"]),
            ("training_end_year", str(claim["training_end_year"])),
            ("training_type_end_year", f"{claim['training_type']}::{claim['training_end_year']}"),
            ("source_scope", claim["source_scope"]),
            ("ten_year_trend_window", claim["ten_year_trend_window"]),
        ]
        for scope, value in scopes:
            if value in {None, ""}:
                continue
            grouped[(scope, value)].append(claim)

    rows = []
    for (scope, value), scope_claims in sorted(grouped.items()):
        training_types = sorted({claim["training_type"] for claim in scope_claims if claim["training_type"]})
        end_years = sorted({as_int(claim["training_end_year"]) for claim in scope_claims if claim["training_end_year"]})
        windows = sorted({claim["ten_year_trend_window"] for claim in scope_claims if claim["ten_year_trend_window"]})
        source_scopes = sorted({claim["source_scope"] for claim in scope_claims if claim["source_scope"]})
        key_parts = (scope, value, tuple(training_types), tuple(end_years), tuple(windows), tuple(source_scopes))
        row = {
            "trend_rollup_key": rollup_key(key_parts),
            "rollup_scope": scope,
            "rollup_value": value,
            "training_type": training_types[0] if len(training_types) == 1 else "",
            "training_end_year": end_years[0] if len(end_years) == 1 else "",
            "ten_year_trend_window": windows[0] if len(windows) == 1 else "",
            "source_scope": source_scopes[0] if len(source_scopes) == 1 else "",
            "claim_count": len(scope_claims),
            "person_count": len({claim["normalized_name"] for claim in scope_claims}),
            "evidence_json": dumps(
                {
                    "trend_claim_keys": [claim["trend_claim_key"] for claim in scope_claims],
                    "display_names": [claim["display_name"] for claim in scope_claims],
                }
            ),
            "materialized_at": "",
        }
        row["materialized_at"] = stable_time(existing, "trend_rollup_key", ROLLUP_FIELDS, row, timestamp)
        rows.append(row)
    return rows


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, table: str, rows: list[dict], fields: list[str]) -> None:
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in fields)
    field_sql = ", ".join(fields)
    conn.executemany(f"INSERT INTO {table} ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(claims: list[dict], rollups: list[dict]) -> None:
    by_training_type = Counter(claim["training_type"] for claim in claims)
    by_end_year = Counter(str(claim["training_end_year"]) for claim in claims)
    by_source_scope = Counter(claim["source_scope"] for claim in claims)
    by_status = Counter(claim["trend_status"] for claim in claims)
    payload = {
        "trend_review_claim_rows": len(claims),
        "trend_review_people": len({claim["normalized_name"] for claim in claims}),
        "trend_review_rollup_rows": len(rollups),
        "trend_claim_type": TREND_CLAIM_TYPE,
        "acceptance_policy": ACCEPTANCE_POLICY,
        "display_safety_status": DISPLAY_SAFETY_STATUS,
        "required_reviewer_action": REQUIRED_REVIEWER_ACTION,
        "by_training_type": dict(sorted(by_training_type.items())),
        "by_training_end_year": dict(sorted(by_end_year.items())),
        "by_source_scope": dict(sorted(by_source_scope.items())),
        "by_trend_status": dict(sorted(by_status.items())),
        "claims_csv": str(CLAIMS_CSV.relative_to(ROOT)),
        "claims_json": str(CLAIMS_JSON.relative_to(ROOT)),
        "rollups_csv": str(ROLLUPS_CSV.relative_to(ROOT)),
        "rollups_json": str(ROLLUPS_JSON.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    conn = sqlite3.connect(DB)
    with conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        claims = materialize_claims(conn)
        rollups = materialize_rollups(claims)
        write_csv(CLAIMS_CSV, claims, CLAIM_FIELDS)
        CLAIMS_JSON.write_text(json.dumps(claims, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        write_csv(ROLLUPS_CSV, rollups, ROLLUP_FIELDS)
        ROLLUPS_JSON.write_text(json.dumps(rollups, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(claims, rollups)
        write_db(conn, "attending_trend_review_claims", claims, CLAIM_FIELDS)
        write_db(conn, "attending_trend_review_rollups", rollups, ROLLUP_FIELDS)
    conn.close()
    print(dumps({"attending_trend_review_claims": len(claims), "attending_trend_review_rollups": len(rollups)}))


if __name__ == "__main__":
    main()
