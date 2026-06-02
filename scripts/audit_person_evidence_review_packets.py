#!/usr/bin/env python3
"""Build person/name-level review packets from evidence reconciliation decisions."""

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


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"
DECISIONS_CSV = ARTIFACTS / "evidence_reconciliation_decisions.csv"
TREND_RECONCILIATION_CSV = ARTIFACTS / "attending_trend_reconciliation.csv"
PACKETS_CSV = ARTIFACTS / "person_evidence_review_packets.csv"

REVIEW_READY_DECISIONS = {
    "review_ready_high_anchor",
    "review_ready_training_topic_anchor",
    "attending_training_claim_review_ready",
    "attending_training_claim_linkable_name_match",
    "trend_review_ready_official_biosketch_bridge",
}
SECONDARY_ANCHOR_DECISIONS = {
    "needs_secondary_identity_anchor",
    "attending_training_claim_needs_identity_link",
    "trend_profile_claim_still_needs_dated_bridge",
}
ATTENDING_DECISIONS = {
    "attending_training_claim_review_ready",
    "attending_training_claim_linkable_name_match",
    "attending_training_claim_needs_identity_link",
    "current_attending_endpoint_candidate",
    "outcome_context_only",
    "profile_context_candidate",
    "trend_review_ready_official_biosketch_bridge",
    "trend_profile_claim_still_needs_dated_bridge",
    "trend_current_endpoint_needs_training_claim",
    "trend_context_only_not_ready",
}
PUBLICATION_DECISIONS = {
    "review_ready_high_anchor",
    "review_ready_training_topic_anchor",
    "needs_secondary_identity_anchor",
    "candidate_with_partial_anchor",
    "low_signal_candidate",
    "discovery_only",
}


def norm_space(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def normalized_person_name(value: str | None) -> str:
    value = norm_space(value).lower()
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(
        r"\b(md|m\.d\.|do|d\.o\.|phd|ph\.d\.|mbe|msce|mse?d|mph|mba|ms|m\.s\.|ma|m\.a\.)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return norm_space(value)


def packet_key_for(person_or_name_key: str, display_name: str) -> str:
    basis = f"{person_or_name_key}|{display_name}"
    return "person_evidence_packet_" + hashlib.sha1(basis.encode("utf-8")).hexdigest()[:16]


def existing_packet_rows() -> dict[str, dict]:
    if not PACKETS_CSV.exists():
        return {}
    with PACKETS_CSV.open(newline="", encoding="utf-8") as f:
        return {row["packet_key"]: row for row in csv.DictReader(f)}


def stable_audited_at(existing: dict[str, dict], row: dict, new_value: str) -> str:
    prior = existing.get(row["packet_key"])
    if not prior:
        return new_value
    stable_fields = [
        "packet_status",
        "review_kind",
        "recommended_next_action",
        "acceptance_blocker",
        "review_priority",
        "review_ready_record_count",
        "secondary_anchor_needed_count",
        "low_signal_record_count",
        "discovery_only_count",
        "publication_candidate_count",
        "attending_candidate_count",
        "current_attending_endpoint_count",
        "evidence_record_count",
        "best_decision",
        "best_source_url",
        "top_source_urls",
        "top_claim_types",
        "top_match_features",
        "evidence_json",
    ]
    for field in stable_fields:
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return new_value
    return prior.get("audited_at") or new_value


def read_decisions(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def trend_decision_for_status(status: str) -> str:
    if status == "review_ready_official_biosketch_bridge":
        return "trend_review_ready_official_biosketch_bridge"
    if status == "profile_claim_still_needs_dated_bridge":
        return "trend_profile_claim_still_needs_dated_bridge"
    if status == "current_endpoint_needs_training_claim":
        return "trend_current_endpoint_needs_training_claim"
    return "trend_context_only_not_ready"


def read_trend_reconciliation(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    decisions = []
    for row in rows:
        decision = trend_decision_for_status(row.get("trend_status") or "")
        assurance = as_int(row.get("trend_assurance_level"))
        priority = 120 + assurance * 20
        decisions.append(
            {
                "record_type": "attending_trend_reconciliation",
                "record_id": row.get("trend_key") or "",
                "person_key": "",
                "display_name": row.get("display_name") or "",
                "role": "attending_or_outcome_candidate",
                "claim_type": "recent_attending_trend_candidate",
                "event_type": "recent_attending_trend_candidate",
                "status": row.get("trend_status") or "",
                "confidence": round(min(0.99, 0.55 + assurance * 0.1), 3),
                "priority": priority,
                "decision": decision,
                "decision_rationale": row.get("trend_status") or "",
                "required_next_evidence": row.get("required_next_evidence") or "",
                "non_name_anchor_count": assurance,
                "matched_current_person_count": row.get("has_current_trainee_name_match") or "0",
                "matched_current_person_keys": "",
                "ten_year_trend_window": row.get("ten_year_trend_window") or "",
                "source_key": "attending_trend_reconciliation",
                "source_url": row.get("best_source_url") or "",
                "match_features": "; ".join(
                    feature
                    for feature, flag in [
                        ("current_attending_endpoint", row.get("has_current_attending_endpoint")),
                        ("penn_training_claim", row.get("has_penn_training_claim")),
                        ("official_biosketch_bridge", row.get("has_recent_dated_biosketch_bridge")),
                        ("historical_link_candidate", row.get("has_historical_link_candidate")),
                    ]
                    if as_int(flag)
                ),
            }
        )
    return decisions


def as_int(value: str | int | None) -> int:
    if value in {None, ""}:
        return 0
    return int(float(value))


def as_float(value: str | float | None) -> float:
    if value in {None, ""}:
        return 0.0
    return float(value)


def group_key(row: dict) -> tuple[str, str]:
    key = row.get("person_key") or normalized_person_name(row.get("display_name"))
    return key, row.get("display_name") or ""


def review_kind(decisions: Counter) -> str:
    has_attending = any(decision in ATTENDING_DECISIONS for decision in decisions)
    has_publication = any(decision in PUBLICATION_DECISIONS for decision in decisions)
    if has_attending and has_publication:
        return "mixed_publication_and_attending_trend"
    if has_attending:
        return "attending_trend_identity_link"
    if has_publication:
        return "publication_identity_review"
    return "general_evidence_review"


def classify_packet(items: list[dict], decisions: Counter) -> tuple[str, str, str, int]:
    review_ready = sum(decisions.get(decision, 0) for decision in REVIEW_READY_DECISIONS)
    secondary = sum(decisions.get(decision, 0) for decision in SECONDARY_ANCHOR_DECISIONS)
    partial = decisions.get("candidate_with_partial_anchor", 0)
    low_signal = decisions.get("low_signal_candidate", 0)
    discovery = decisions.get("discovery_only", 0)
    kind = review_kind(decisions)
    max_priority = max(as_int(row.get("priority")) for row in items)
    if decisions.get("trend_review_ready_official_biosketch_bridge", 0):
        return (
            "review_ready_recent_attending_trend_packet",
            "review_official_biosketch_bridge_for_trend_acceptance",
            "Needs reviewer acceptance before accepted trend-line use; do not mutate current trainee roster.",
            max_priority + 30,
        )
    if review_ready and kind == "attending_trend_identity_link":
        return (
            "review_ready_attending_trend_packet",
            "review_attending_training_claim_and_seek_historical_identity_link",
            "Needs historical roster/alumni/CV/profile bridge before trend-line acceptance.",
            max_priority + 20,
        )
    if review_ready:
        return (
            "review_ready_publication_packet" if kind == "publication_identity_review" else "review_ready_mixed_packet",
            "manual_review_for_candidate_acceptance",
            "Needs reviewer confirmation of author identity, source context, and non-name anchors.",
            max_priority + 15,
        )
    if secondary:
        return (
            "needs_secondary_identity_anchor_packet",
            "seek_profile_or_identifier_or_coauthor_anchor",
            "Has partial non-name evidence but lacks enough corroboration for review-ready acceptance.",
            max_priority + 5,
        )
    if partial:
        return (
            "partial_anchor_candidate_packet",
            "collect_additional_identity_anchors",
            "Has at least one non-name anchor but remains below review-ready confidence.",
            max_priority,
        )
    if low_signal and low_signal >= discovery:
        return (
            "low_signal_candidate_packet",
            "deprioritize_until_stronger_source_appears",
            "Mostly name-only or weak-topic evidence.",
            max_priority,
        )
    return (
        "discovery_only_packet",
        "use_only_as_discovery_seed",
        "Author-query or context evidence is insufficient for identity review.",
        max_priority,
    )


def ordered_items(items: list[dict]) -> list[dict]:
    return sorted(
        items,
        key=lambda row: (
            row.get("decision") not in REVIEW_READY_DECISIONS,
            -as_int(row.get("priority")),
            -as_float(row.get("confidence")),
            row.get("source_url") or "",
        ),
    )


def packet_rows(decisions: list[dict]) -> list[dict]:
    existing = existing_packet_rows()
    audited_at = datetime.now(timezone.utc).isoformat()
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in decisions:
        grouped[group_key(row)].append(row)
    packets = []
    for (person_or_name_key, display_name), items in grouped.items():
        items = ordered_items(items)
        decision_counts = Counter(row["decision"] for row in items)
        status, action, blocker, priority = classify_packet(items, decision_counts)
        kind = review_kind(decision_counts)
        review_ready_count = sum(decision_counts.get(decision, 0) for decision in REVIEW_READY_DECISIONS)
        secondary_count = sum(decision_counts.get(decision, 0) for decision in SECONDARY_ANCHOR_DECISIONS)
        publication_count = sum(1 for row in items if row.get("claim_type") in {"pubmed_article_candidate", "pubmed_author_query_candidate"})
        attending_count = sum(1 for row in items if row.get("record_type") == "career_event")
        endpoint_count = sum(1 for row in items if row.get("decision") == "current_attending_endpoint_candidate")
        top_urls = []
        for row in items:
            url = row.get("source_url") or ""
            if url and url not in top_urls:
                top_urls.append(url)
        claim_types = sorted({row.get("claim_type") or row.get("event_type") or "" for row in items if row.get("claim_type") or row.get("event_type")})
        features = sorted(
            {
                feature.strip()
                for row in items[:10]
                for feature in (row.get("match_features") or "").split(";")
                if feature.strip()
            }
        )
        evidence = {
            "decision_counts": dict(sorted(decision_counts.items())),
            "top_records": [
                {
                    "record_type": row.get("record_type"),
                    "record_id": row.get("record_id"),
                    "decision": row.get("decision"),
                    "claim_type": row.get("claim_type"),
                    "event_type": row.get("event_type"),
                    "confidence": row.get("confidence"),
                    "priority": row.get("priority"),
                    "source_url": row.get("source_url"),
                    "required_next_evidence": row.get("required_next_evidence"),
                    "match_features": row.get("match_features"),
                }
                for row in items[:8]
            ],
        }
        packet = {
            "packet_key": packet_key_for(person_or_name_key, display_name),
            "person_or_name_key": person_or_name_key,
            "person_key": items[0].get("person_key") or "",
            "display_name": display_name,
            "role": items[0].get("role") or "",
            "packet_status": status,
            "review_kind": kind,
            "recommended_next_action": action,
            "acceptance_blocker": blocker,
            "review_priority": priority,
            "review_ready_record_count": review_ready_count,
            "secondary_anchor_needed_count": secondary_count,
            "low_signal_record_count": decision_counts.get("low_signal_candidate", 0),
            "discovery_only_count": decision_counts.get("discovery_only", 0),
            "publication_candidate_count": publication_count,
            "attending_candidate_count": attending_count,
            "current_attending_endpoint_count": endpoint_count,
            "evidence_record_count": len(items),
            "best_decision": items[0].get("decision") or "",
            "best_source_url": items[0].get("source_url") or "",
            "top_source_urls": "; ".join(top_urls[:5]),
            "top_claim_types": "; ".join(claim_types),
            "top_match_features": "; ".join(features[:20]),
            "evidence_json": json.dumps(evidence, ensure_ascii=False, sort_keys=True),
            "audited_at": audited_at,
        }
        packet["audited_at"] = stable_audited_at(existing, packet, audited_at)
        packets.append(packet)
    return sorted(packets, key=lambda row: (-int(row["review_priority"]), row["display_name"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_evidence_review_packets")
    for row in rows:
        conn.execute(
            """
            INSERT INTO person_evidence_review_packets
            (packet_key, person_or_name_key, person_key, display_name, role,
             packet_status, review_kind, recommended_next_action, acceptance_blocker,
             review_priority, review_ready_record_count, secondary_anchor_needed_count,
             low_signal_record_count, discovery_only_count, publication_candidate_count,
             attending_candidate_count, current_attending_endpoint_count,
             evidence_record_count, best_decision, best_source_url, top_source_urls,
             top_claim_types, top_match_features, evidence_json, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["packet_key"],
                row["person_or_name_key"],
                row["person_key"],
                row["display_name"],
                row["role"],
                row["packet_status"],
                row["review_kind"],
                row["recommended_next_action"],
                row["acceptance_blocker"],
                row["review_priority"],
                row["review_ready_record_count"],
                row["secondary_anchor_needed_count"],
                row["low_signal_record_count"],
                row["discovery_only_count"],
                row["publication_candidate_count"],
                row["attending_candidate_count"],
                row["current_attending_endpoint_count"],
                row["evidence_record_count"],
                row["best_decision"],
                row["best_source_url"],
                row["top_source_urls"],
                row["top_claim_types"],
                row["top_match_features"],
                row["evidence_json"],
                row["audited_at"],
            ),
        )


def summary_payload(rows: list[dict]) -> dict:
    return {
        "generated_at": max((row["audited_at"] for row in rows), default=datetime.now(timezone.utc).isoformat()),
        "packet_rows": len(rows),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_review_kind": dict(sorted(Counter(row["review_kind"] for row in rows).items())),
        "by_recommended_next_action": dict(sorted(Counter(row["recommended_next_action"] for row in rows).items())),
        "review_ready_packets": sum(1 for row in rows if row["packet_status"].startswith("review_ready")),
        "needs_secondary_anchor_packets": sum(1 for row in rows if row["packet_status"] == "needs_secondary_identity_anchor_packet"),
        "attending_trend_packets": sum(1 for row in rows if "attending" in row["review_kind"]),
        "publication_review_packets": sum(1 for row in rows if "publication" in row["review_kind"]),
        "csv": "artifacts/data/person_evidence_review_packets.csv",
        "json": "artifacts/data/person_evidence_review_packets.json",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--decisions", type=Path, default=DECISIONS_CSV)
    parser.add_argument("--trend-reconciliation", type=Path, default=TREND_RECONCILIATION_CSV)
    args = parser.parse_args()

    decisions = read_decisions(args.decisions)
    decisions.extend(read_trend_reconciliation(args.trend_reconciliation))
    rows = packet_rows(decisions)
    summary = summary_payload(rows)
    conn = sqlite3.connect(args.db)
    with conn:
        write_sqlite(conn, rows)
    conn.close()

    write_csv(PACKETS_CSV, rows)
    (ARTIFACTS / "person_evidence_review_packets.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "person_evidence_review_packet_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
