#!/usr/bin/env python3
"""Materialize bounded reviewer batches for person evidence triage rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "person_evidence_review_batches.csv"
JSON_PATH = ARTIFACTS / "person_evidence_review_batches.json"
SUMMARY_PATH = ARTIFACTS / "person_evidence_review_batch_summary.json"

MAX_PACKETS_PER_BATCH = 35

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "review_batch_key",
    "execution_order",
    "triage_lane",
    "decision_difficulty",
    "risk_level",
    "role",
    "batch_status",
    "ready_to_review",
    "packet_count",
    "person_count",
    "review_ready_record_count",
    "evidence_record_count",
    "source_count",
    "claim_type_count",
    "max_triage_priority",
    "min_triage_priority",
    "avg_evidence_density_score",
    "source_family_counts_json",
    "top_source_domains",
    "top_best_decisions_json",
    "allowed_decisions",
    "reviewer_prompt",
    "review_instructions",
    "acceptance_rule",
    "target_decision_artifact",
    "top_packets_json",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def split_semicolon(value: str | None) -> list[str]:
    if not value:
        return []
    return [part.strip() for part in str(value).split(";") if part.strip()]


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["review_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["review_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def batch_key(parts: tuple[object, ...]) -> str:
    return "person_evidence_review_batch_" + sha256_text(dumps(parts))[:20]


def load_triage(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT t.*, q.allowed_decisions
            FROM person_evidence_review_triage t
            LEFT JOIN person_evidence_reviewer_decision_queue q
              ON q.reviewer_decision_key = t.reviewer_decision_key
            ORDER BY t.triage_priority DESC, t.display_name, t.packet_key
            """
        )
    ]


def source_family_counts(rows: list[dict]) -> Counter:
    counts: Counter = Counter()
    for row in rows:
        for part in split_semicolon(row.get("source_family_summary")):
            if ":" not in part:
                continue
            family, count = part.rsplit(":", 1)
            counts[family] += as_int(count)
    return counts


def compact_domains(rows: list[dict], limit: int = 12) -> str:
    counts: Counter = Counter()
    for row in rows:
        for domain in split_semicolon(row.get("top_source_domains")):
            counts[domain] += 1
    values = [f"{domain}:{count}" for domain, count in counts.most_common(limit)]
    return "; ".join(values)


def review_instructions(lane: str, risk: str, difficulty: str) -> str:
    if lane == "publication_with_secondary_identity_anchor_review":
        return "Review author identity, secondary identifier ownership, author position/topic fit, and same-person roster/profile anchors before accepting publication enrichment."
    if lane == "publication_identity_final_check":
        return "Check publication candidates for non-name anchors; accept only when identity is strong or mark needs_more_evidence for secondary anchors."
    if lane == "publication_with_official_profile_anchor_review":
        return "Use the official Penn profile or roster context as an identity anchor, then decide whether publication enrichment is acceptable."
    if lane == "official_profile_context_display_review":
        return "Apply display-safety policy to official-profile context; avoid accepting sensitive personal context as identity or quality evidence."
    if lane == "secondary_identity_anchor_context_review":
        return "Confirm NPI/ORCID-style identifier ownership before using it as a secondary anchor for later claims."
    if "attending" in lane:
        return "Confirm historical training bridge and current endpoint before accepting any attending trend fact."
    if risk == "identity_collision_high":
        return "Seek independent non-name anchors before accepting; similar-name collisions are plausible."
    return f"Review {difficulty} packets and record accept, reject, or needs_more_evidence decisions with matching packet fingerprints."


def batch_status(rows: list[dict]) -> str:
    if not rows:
        return "empty_batch"
    if any(not row.get("reviewer_decision_key") for row in rows):
        return "blocked_missing_reviewer_decision_key"
    if any(not row.get("packet_fingerprint") for row in rows):
        return "blocked_missing_packet_fingerprint"
    return "ready_for_reviewer_decision_batch"


def top_packets(rows: list[dict], limit: int = 12) -> list[dict]:
    packets = []
    for row in sorted(rows, key=lambda item: (-as_int(item.get("triage_priority")), item.get("display_name") or ""))[
        :limit
    ]:
        packets.append(
            {
                "triage_key": row.get("triage_key"),
                "reviewer_decision_key": row.get("reviewer_decision_key"),
                "packet_key": row.get("packet_key"),
                "display_name": row.get("display_name"),
                "role": row.get("role"),
                "triage_priority": as_int(row.get("triage_priority")),
                "review_ready_record_count": as_int(row.get("review_ready_record_count")),
                "best_decision": row.get("best_decision"),
                "top_source_domains": row.get("top_source_domains"),
                "packet_fingerprint": row.get("packet_fingerprint"),
            }
        )
    return packets


def build_rows(triage_rows: list[dict], generated_at: str) -> list[dict]:
    existing = read_existing()
    grouped: dict[tuple[str, str, str, str], list[dict]] = defaultdict(list)
    for row in triage_rows:
        grouped[
            (
                row.get("triage_lane") or "",
                row.get("decision_difficulty") or "",
                row.get("risk_level") or "",
                row.get("role") or "",
            )
        ].append(row)

    output = []
    for (lane, difficulty, risk, role), rows in grouped.items():
        sorted_rows = sorted(rows, key=lambda item: (-as_int(item.get("triage_priority")), item.get("display_name") or ""))
        for chunk_index, offset in enumerate(range(0, len(sorted_rows), MAX_PACKETS_PER_BATCH), start=1):
            chunk = sorted_rows[offset : offset + MAX_PACKETS_PER_BATCH]
            priorities = [as_int(row.get("triage_priority")) for row in chunk]
            density_values = [as_float(row.get("evidence_density_score")) for row in chunk]
            status = batch_status(chunk)
            family_counts = source_family_counts(chunk)
            best_decisions = Counter(row.get("best_decision") or "" for row in chunk)
            allowed_decisions = Counter(row.get("allowed_decisions") or "" for row in chunk)
            prompts = Counter(row.get("reviewer_prompt") or "" for row in chunk)
            packet_keys = [row.get("packet_key") for row in chunk]
            row = {
                "review_batch_key": batch_key((lane, difficulty, risk, role, chunk_index, packet_keys)),
                "execution_order": 0,
                "triage_lane": lane,
                "decision_difficulty": difficulty,
                "risk_level": risk,
                "role": role,
                "batch_status": status,
                "ready_to_review": 1 if status == "ready_for_reviewer_decision_batch" else 0,
                "packet_count": len(chunk),
                "person_count": len({item.get("person_or_name_key") or item.get("person_key") for item in chunk}),
                "review_ready_record_count": sum(as_int(item.get("review_ready_record_count")) for item in chunk),
                "evidence_record_count": sum(as_int(item.get("evidence_record_count")) for item in chunk),
                "source_count": sum(as_int(item.get("source_count")) for item in chunk),
                "claim_type_count": sum(as_int(item.get("claim_type_count")) for item in chunk),
                "max_triage_priority": max(priorities) if priorities else 0,
                "min_triage_priority": min(priorities) if priorities else 0,
                "avg_evidence_density_score": round(sum(density_values) / max(len(density_values), 1), 3),
                "source_family_counts_json": dumps(dict(sorted(family_counts.items()))),
                "top_source_domains": compact_domains(chunk),
                "top_best_decisions_json": dumps(dict(best_decisions.most_common(12))),
                "allowed_decisions": allowed_decisions.most_common(1)[0][0] if allowed_decisions else "",
                "reviewer_prompt": prompts.most_common(1)[0][0] if prompts else "",
                "review_instructions": review_instructions(lane, risk, difficulty),
                "acceptance_rule": (
                    "Batch rows are non-mutating. A fact is accepted only after a reviewer decision with the "
                    "current packet_fingerprint and required identity/source/non-name-anchor/display confirmations."
                ),
                "target_decision_artifact": "artifacts/data/person_evidence_reviewer_decisions.csv",
                "top_packets_json": dumps(top_packets(chunk)),
                "evidence_json": dumps(
                    {
                        "derived_from": "person_evidence_review_triage",
                        "packet_keys": packet_keys,
                        "policy": {
                            "non_mutating": True,
                            "accepted_facts_flow_through": [
                                "person_evidence_reviewer_decisions",
                                "person_evidence_reviewer_decision_audit",
                                "enrichment_acceptance_audit",
                                "accepted_enrichment_claims",
                            ],
                        },
                    }
                ),
                "generated_at": "",
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            output.append(row)

    output.sort(
        key=lambda item: (
            -as_int(item["ready_to_review"]),
            -as_int(item["max_triage_priority"]),
            -as_int(item["review_ready_record_count"]),
            item["triage_lane"],
            item["role"],
            item["review_batch_key"],
        )
    )
    for index, row in enumerate(output, start=1):
        row["execution_order"] = index
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_evidence_review_batches")
    if not rows:
        return
    field_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(f"INSERT OR REPLACE INTO person_evidence_review_batches ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict], generated_at: str) -> None:
    by_lane = Counter(row["triage_lane"] for row in rows)
    by_status = Counter(row["batch_status"] for row in rows)
    by_risk = Counter(row["risk_level"] for row in rows)
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "ready_batch_rows": sum(as_int(row["ready_to_review"]) for row in rows),
        "packet_count": sum(as_int(row["packet_count"]) for row in rows),
        "person_count_policy": "Summed batch person counts are not deduplicated across lanes.",
        "review_ready_record_count": sum(as_int(row["review_ready_record_count"]) for row in rows),
        "evidence_record_count": sum(as_int(row["evidence_record_count"]) for row in rows),
        "by_triage_lane": dict(sorted(by_lane.items())),
        "by_batch_status": dict(sorted(by_status.items())),
        "by_risk_level": dict(sorted(by_risk.items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "triage_lane": row["triage_lane"],
                "decision_difficulty": row["decision_difficulty"],
                "risk_level": row["risk_level"],
                "role": row["role"],
                "packet_count": row["packet_count"],
                "review_ready_record_count": row["review_ready_record_count"],
                "max_triage_priority": row["max_triage_priority"],
                "review_instructions": row["review_instructions"],
            }
            for row in rows[:25]
        ],
        "policy": "This artifact batches person evidence review work only; it does not accept enrichment, contact, trend, or roster facts.",
        "csv": str(CSV_PATH.relative_to(ROOT)),
        "json": str(JSON_PATH.relative_to(ROOT)),
    }
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    generated_at = now_utc()
    conn = sqlite3.connect(args.db)
    rows = build_rows(load_triage(conn), generated_at)
    with conn:
        write_db(conn, rows)
    conn.close()
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_summary(rows, generated_at)
    print(dumps({"person_evidence_review_batches": len(rows), "packet_count": sum(as_int(row["packet_count"]) for row in rows)}))


if __name__ == "__main__":
    main()
