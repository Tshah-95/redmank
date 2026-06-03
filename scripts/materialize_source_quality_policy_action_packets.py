#!/usr/bin/env python3
"""Materialize action packets for source-quality policy recommendations."""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

RECOMMENDATION_CSV = ARTIFACTS / "source_quality_policy_recommendations.csv"
CSV_OUT = ARTIFACTS / "source_quality_policy_action_packets.csv"
JSON_OUT = ARTIFACTS / "source_quality_policy_action_packets.json"
SUMMARY_OUT = ARTIFACTS / "source_quality_policy_action_packet_summary.json"

FIELDS = [
    "source_quality_policy_packet_key",
    "packet_order",
    "recommendation_key",
    "source_row_type",
    "utility_key",
    "utility_label",
    "source_family",
    "claim_surface",
    "score",
    "quality_band",
    "policy_lane",
    "policy_status",
    "action_priority",
    "action_readiness",
    "packet_status",
    "support_status",
    "trend_relevance",
    "acceptance_posture",
    "collector_posture",
    "reviewer_posture",
    "evidence_standard",
    "required_next_evidence",
    "recommended_next_action",
    "source_artifacts_json",
    "downstream_tables_json",
    "scorecard_evidence_json",
    "search_assurance_evidence_json",
    "acceptance_boundary_json",
    "evidence_json",
    "generated_at",
]

csv.field_size_limit(sys.maxsize)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def stable_key(*parts: object) -> str:
    text = "||".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_existing() -> dict[str, dict]:
    return {row["source_quality_policy_packet_key"]: row for row in read_csv(CSV_OUT)}


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["source_quality_policy_packet_key"])
    if not prior:
        return generated_at
    comparable = {field: row.get(field, "") for field in FIELDS if field != "generated_at"}
    prior_comparable = {field: prior.get(field, "") for field in FIELDS if field != "generated_at"}
    return prior.get("generated_at") or generated_at if comparable == prior_comparable else generated_at


def packet_status(row: dict) -> str:
    if row.get("trend_relevance") == "directly_relevant_to_recent_attending_trend_path":
        return "recent_attending_trend_policy_packet"
    lane = row.get("policy_lane") or "source_quality_policy"
    return f"{lane}_packet"


def support_status(row: dict) -> str:
    readiness = row.get("action_readiness") or ""
    if readiness == "blocked_or_low_signal_until_next_evidence":
        return "blocked_or_low_signal_policy_support"
    if readiness == "review_ready_or_review_bound":
        return "review_ready_policy_support"
    if readiness in {"collector_or_probe_ready", "search_execution_needed", "candidate_probe_ready"}:
        return "collector_or_probe_policy_support"
    if readiness == "retry_or_provider_swap_needed":
        return "retry_or_provider_swap_policy_support"
    return "monitor_or_refresh_policy_support"


def acceptance_boundary(row: dict) -> dict:
    return {
        "non_mutating": True,
        "packet_role": "source-quality policy action envelope",
        "does_not_accept_facts": True,
        "fact_promotion_requires": [
            "source-specific evidence ledger",
            "current source observation or packet fingerprint",
            "source-specific reviewer decision or accepted-fact ledger",
        ],
        "trend_path_boundary": (
            "Recent-attending trend relevance means this source utility can prioritize trend discovery or review; "
            "it does not itself establish a Penn training-history bridge or current attending endpoint fact."
        ),
    }


def build_rows() -> list[dict]:
    existing = read_existing()
    generated_at = now_utc()
    rows = []
    recommendations = sorted(
        read_csv(RECOMMENDATION_CSV),
        key=lambda row: (-as_int(row.get("action_priority")), row.get("policy_lane") or "", row.get("utility_label") or ""),
    )
    for index, item in enumerate(recommendations, start=1):
        boundary = acceptance_boundary(item)
        source_artifacts = parse_json(item.get("source_artifacts_json"), [])
        downstream_tables = parse_json(item.get("downstream_tables_json"), [])
        scorecard_evidence = parse_json(item.get("scorecard_evidence_json"), {})
        search_evidence = parse_json(item.get("search_assurance_evidence_json"), {})
        packet_key = "source_quality_policy_packet_" + stable_key(item.get("recommendation_key"))
        row = {
            "source_quality_policy_packet_key": packet_key,
            "packet_order": index,
            "recommendation_key": item.get("recommendation_key") or "",
            "source_row_type": item.get("source_row_type") or "",
            "utility_key": item.get("utility_key") or "",
            "utility_label": item.get("utility_label") or "",
            "source_family": item.get("source_family") or "",
            "claim_surface": item.get("claim_surface") or "",
            "score": as_float(item.get("score")),
            "quality_band": item.get("quality_band") or "",
            "policy_lane": item.get("policy_lane") or "",
            "policy_status": item.get("policy_status") or "",
            "action_priority": as_int(item.get("action_priority")),
            "action_readiness": item.get("action_readiness") or "",
            "packet_status": packet_status(item),
            "support_status": support_status(item),
            "trend_relevance": item.get("trend_relevance") or "",
            "acceptance_posture": item.get("acceptance_posture") or "",
            "collector_posture": item.get("collector_posture") or "",
            "reviewer_posture": item.get("reviewer_posture") or "",
            "evidence_standard": item.get("evidence_standard") or "",
            "required_next_evidence": item.get("required_next_evidence") or "",
            "recommended_next_action": item.get("recommended_next_action") or "",
            "source_artifacts_json": dumps(source_artifacts),
            "downstream_tables_json": dumps(downstream_tables),
            "scorecard_evidence_json": dumps(scorecard_evidence),
            "search_assurance_evidence_json": dumps(search_evidence),
            "acceptance_boundary_json": dumps(boundary),
            "evidence_json": dumps(
                {
                    "source_quality_policy_packet_key": packet_key,
                    "recommendation_key": item.get("recommendation_key"),
                    "utility_key": item.get("utility_key"),
                    "policy_lane": item.get("policy_lane"),
                    "action_readiness": item.get("action_readiness"),
                    "trend_relevance": item.get("trend_relevance"),
                    "source_artifacts": source_artifacts,
                    "downstream_tables": downstream_tables,
                    "acceptance_boundary": boundary,
                }
            ),
            "generated_at": generated_at,
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        rows.append({field: row[field] for field in FIELDS})
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(rows: list[dict]) -> None:
    conn = sqlite3.connect(DB)
    with conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("DELETE FROM source_quality_policy_action_packets")
        placeholders = ", ".join(f":{field}" for field in FIELDS)
        fields = ", ".join(FIELDS)
        conn.executemany(
            f"INSERT OR REPLACE INTO source_quality_policy_action_packets ({fields}) VALUES ({placeholders})",
            rows,
        )
    conn.close()


def write_summary(rows: list[dict]) -> None:
    payload = {
        "generated_at": max((row["generated_at"] for row in rows), default=now_utc()),
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "packet_rows": len(rows),
        "distinct_recommendations": len({row["recommendation_key"] for row in rows}),
        "recent_attending_trend_packet_rows": sum(
            1 for row in rows if row["trend_relevance"] == "directly_relevant_to_recent_attending_trend_path"
        ),
        "by_policy_lane": dict(sorted(Counter(row["policy_lane"] for row in rows).items())),
        "by_action_readiness": dict(sorted(Counter(row["action_readiness"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_support_status": dict(sorted(Counter(row["support_status"] for row in rows).items())),
        "by_trend_relevance": dict(sorted(Counter(row["trend_relevance"] for row in rows).items())),
        "top_packets": [
            {
                "packet_order": row["packet_order"],
                "utility_label": row["utility_label"],
                "policy_lane": row["policy_lane"],
                "action_readiness": row["action_readiness"],
                "support_status": row["support_status"],
                "trend_relevance": row["trend_relevance"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:25]
        ],
        "policy": (
            "Source-quality policy action packets are non-mutating envelopes around source-quality "
            "recommendations. They prioritize collectors, reviewers, and recent-attending trend work; "
            "fact acceptance still requires source-specific evidence and acceptance ledgers."
        ),
    }
    SUMMARY_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows)
    print(dumps({"source_quality_policy_action_packets": len(rows)}))


if __name__ == "__main__":
    main()
