#!/usr/bin/env python3
"""Materialize bounded reviewer batches for lifecycle-duration evidence."""

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

CSV_PATH = ARTIFACTS / "program_lifecycle_duration_review_batches.csv"
JSON_PATH = ARTIFACTS / "program_lifecycle_duration_review_batches.json"
SUMMARY_PATH = ARTIFACTS / "program_lifecycle_duration_review_batch_summary.json"

MAX_ROWS_PER_BATCH = 25

FIELDS = [
    "duration_review_batch_key",
    "execution_order",
    "batch_status",
    "ready_to_execute",
    "queue_status",
    "decision_status_signature",
    "decision_blocker_signature",
    "official_program_type",
    "duration_evidence_status",
    "recommended_next_action",
    "review_row_count",
    "program_count",
    "source_count",
    "ready_queue_count",
    "context_review_count",
    "not_ready_count",
    "pending_decision_count",
    "explicit_duration_years_signature",
    "max_duration_confidence",
    "min_duration_confidence",
    "top_programs",
    "top_sources",
    "queue_status_counts_json",
    "decision_status_counts_json",
    "duration_evidence_status_counts_json",
    "explicit_duration_year_counts_json",
    "recommended_operator_action",
    "execution_instructions",
    "required_next_evidence",
    "target_artifact",
    "top_review_rows_json",
    "manual_decision_templates_json",
    "evidence_json",
    "generated_at",
]

csv.field_size_limit(sys.maxsize)


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


def read_existing() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row["duration_review_batch_key"]: row for row in csv.DictReader(handle)}


def stable_generated_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["duration_review_batch_key"])
    if not prior:
        return timestamp
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("generated_at") or timestamp


def sqlite_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def batch_key(parts: tuple[object, ...]) -> str:
    return "program_lifecycle_duration_review_batch_" + sha256_text(dumps(parts))[:20]


def batch_status(queue_status: str) -> str:
    if queue_status == "ready_for_reviewer_decision":
        return "duration_manual_decision_ready"
    if queue_status == "context_review_required_before_decision":
        return "duration_context_review_ready"
    if queue_status == "not_ready_for_reviewer_decision":
        return "duration_evidence_collection_required"
    return "duration_review_repair_required"


def recommended_operator_action(queue_status: str) -> str:
    if queue_status == "ready_for_reviewer_decision":
        return "record_lifecycle_duration_reviewer_decisions_for_batch"
    if queue_status == "context_review_required_before_decision":
        return "resolve_duration_context_or_page_scope_for_batch"
    if queue_status == "not_ready_for_reviewer_decision":
        return "collect_stronger_official_duration_evidence_for_batch"
    return "repair_lifecycle_duration_review_batch"


def execution_instructions(queue_status: str) -> str:
    if queue_status == "ready_for_reviewer_decision":
        return (
            "Review each current fingerprint and record accept, reject, or needs-more-evidence decisions "
            "in the manual lifecycle-duration decision file."
        )
    if queue_status == "context_review_required_before_decision":
        return (
            "Inspect page scope and duration context before any accept decision is allowed; collect stronger "
            "official duration evidence if the current page is ambiguous."
        )
    if queue_status == "not_ready_for_reviewer_decision":
        return "Find explicit official duration evidence or retain the default/unknown lifecycle rule until one exists."
    return "Repair stale or invalid lifecycle-duration decision state before routing reviewer decisions."


def required_next_evidence(queue_status: str) -> str:
    if queue_status == "ready_for_reviewer_decision":
        return "Manual decision with matching evidence fingerprint and all required confirmation fields."
    if queue_status == "context_review_required_before_decision":
        return "Reviewer-resolved page scope/duration context or stronger official duration source evidence."
    if queue_status == "not_ready_for_reviewer_decision":
        return "Explicit public official duration source evidence for the matched program lifecycle."
    return "Current lifecycle-duration queue row and repaired decision audit evidence."


def target_artifact(queue_status: str) -> str:
    if queue_status == "ready_for_reviewer_decision":
        return "artifacts/data/program_lifecycle_duration_reviewer_decisions.csv"
    return "artifacts/data/program_lifecycle_duration_evidence.csv"


def read_unresolved_rows(conn: sqlite3.Connection) -> list[dict]:
    return sqlite_rows(
        conn,
        """
        SELECT
          q.*,
          a.decision_status,
          a.decision_blocker,
          a.reviewer_decision,
          a.recommended_next_action AS audit_recommended_next_action
        FROM program_lifecycle_duration_reviewer_decision_queue q
        JOIN program_lifecycle_duration_reviewer_decision_audit a
          ON a.reviewer_decision_key = q.reviewer_decision_key
        WHERE a.decision_status NOT IN ('accepted_reviewer_decision', 'rejected_by_reviewer')
        ORDER BY
          CASE q.queue_status
            WHEN 'ready_for_reviewer_decision' THEN 0
            WHEN 'context_review_required_before_decision' THEN 1
            WHEN 'not_ready_for_reviewer_decision' THEN 2
            ELSE 3
          END,
          q.official_program_type,
          q.duration_evidence_status,
          q.official_program_name,
          q.reviewer_decision_key
        """,
    )


def top_review_rows(rows: list[dict], limit: int = 12) -> list[dict]:
    output = []
    for row in rows[:limit]:
        output.append(
            {
                "reviewer_decision_key": row.get("reviewer_decision_key"),
                "duration_evidence_key": row.get("duration_evidence_key"),
                "evidence_fingerprint": row.get("evidence_fingerprint"),
                "official_program_name": row.get("official_program_name"),
                "matched_program_name": row.get("matched_program_name"),
                "official_program_type": row.get("official_program_type"),
                "source_url": row.get("source_url"),
                "page_title": row.get("page_title"),
                "explicit_duration_years": row.get("explicit_duration_years"),
                "queue_status": row.get("queue_status"),
                "decision_status": row.get("decision_status"),
                "decision_blocker": row.get("decision_blocker"),
                "review_question": row.get("review_question"),
            }
        )
    return output


def manual_decision_templates(rows: list[dict], limit: int = 12) -> list[dict]:
    templates = []
    for row in rows[:limit]:
        templates.append(
            {
                "reviewer_decision_key": row.get("reviewer_decision_key"),
                "duration_evidence_key": row.get("duration_evidence_key"),
                "evidence_fingerprint": row.get("evidence_fingerprint"),
                "reviewer_decision": "",
                "reviewer_name": "",
                "decided_at": "",
                "official_program_confirmed": "",
                "duration_phrase_confirmed": "",
                "duration_years_confirmed": "",
                "role_family_confirmed": "",
                "lifecycle_scope_confirmed": "",
                "decision_notes": "",
            }
        )
    return templates


def build_rows(conn: sqlite3.Connection, generated_at: str) -> list[dict]:
    existing = read_existing()
    unresolved = read_unresolved_rows(conn)
    grouped: dict[tuple[str, str, str, str, str], list[dict]] = defaultdict(list)
    for row in unresolved:
        key = (
            row.get("queue_status") or "",
            row.get("decision_blocker") or "",
            row.get("official_program_type") or "",
            row.get("duration_evidence_status") or "",
            row.get("audit_recommended_next_action") or row.get("recommended_next_action") or "",
        )
        grouped[key].append(row)

    rows = []
    for (queue_status, decision_blocker, program_type, evidence_status, action), group_rows in grouped.items():
        ordered = sorted(
            group_rows,
            key=lambda item: (
                item.get("official_program_name") or "",
                item.get("matched_program_name") or "",
                item.get("reviewer_decision_key") or "",
            ),
        )
        for chunk_index, offset in enumerate(range(0, len(ordered), MAX_ROWS_PER_BATCH), start=1):
            chunk = ordered[offset : offset + MAX_ROWS_PER_BATCH]
            reviewer_keys = [row.get("reviewer_decision_key") for row in chunk]
            confidences = [as_float(row.get("duration_confidence")) for row in chunk]
            queue_counts = Counter(row.get("queue_status") or "" for row in chunk)
            decision_counts = Counter(row.get("decision_status") or "" for row in chunk)
            evidence_counts = Counter(row.get("duration_evidence_status") or "" for row in chunk)
            year_counts = Counter(str(row.get("explicit_duration_years") or "") for row in chunk)
            sources = Counter(row.get("source_url") or "" for row in chunk if row.get("source_url"))
            status = batch_status(queue_status)
            row = {
                "duration_review_batch_key": batch_key(
                    (queue_status, decision_blocker, program_type, evidence_status, action, chunk_index, reviewer_keys)
                ),
                "execution_order": 0,
                "batch_status": status,
                "ready_to_execute": 1,
                "queue_status": queue_status,
                "decision_status_signature": decision_counts.most_common(1)[0][0] if decision_counts else "",
                "decision_blocker_signature": decision_blocker,
                "official_program_type": program_type,
                "duration_evidence_status": evidence_status,
                "recommended_next_action": action,
                "review_row_count": len(chunk),
                "program_count": len({row.get("official_program_key") for row in chunk if row.get("official_program_key")}),
                "source_count": len(sources),
                "ready_queue_count": queue_counts.get("ready_for_reviewer_decision", 0),
                "context_review_count": queue_counts.get("context_review_required_before_decision", 0),
                "not_ready_count": queue_counts.get("not_ready_for_reviewer_decision", 0),
                "pending_decision_count": decision_counts.get("pending_reviewer_decision", 0),
                "explicit_duration_years_signature": year_counts.most_common(1)[0][0] if year_counts else "",
                "max_duration_confidence": max(confidences) if confidences else 0.0,
                "min_duration_confidence": min(confidences) if confidences else 0.0,
                "top_programs": "; ".join(
                    row.get("official_program_name") or row.get("matched_program_name") or "" for row in chunk[:12]
                ),
                "top_sources": "; ".join(source for source, _ in sources.most_common(8)),
                "queue_status_counts_json": dumps(dict(sorted(queue_counts.items()))),
                "decision_status_counts_json": dumps(dict(sorted(decision_counts.items()))),
                "duration_evidence_status_counts_json": dumps(dict(sorted(evidence_counts.items()))),
                "explicit_duration_year_counts_json": dumps(dict(sorted(year_counts.items()))),
                "recommended_operator_action": recommended_operator_action(queue_status),
                "execution_instructions": execution_instructions(queue_status),
                "required_next_evidence": required_next_evidence(queue_status),
                "target_artifact": target_artifact(queue_status),
                "top_review_rows_json": dumps(top_review_rows(chunk)),
                "manual_decision_templates_json": dumps(manual_decision_templates(chunk)),
                "evidence_json": dumps(
                    {
                        "reviewer_decision_keys": reviewer_keys,
                        "duration_evidence_keys": [row.get("duration_evidence_key") for row in chunk],
                        "queue_status_counts": dict(sorted(queue_counts.items())),
                        "decision_status_counts": dict(sorted(decision_counts.items())),
                        "duration_evidence_status_counts": dict(sorted(evidence_counts.items())),
                        "policy": {
                            "non_mutating": True,
                            "accepted_duration_requires": [
                                "manual reviewer decision",
                                "matching evidence fingerprint",
                                "ready_for_reviewer_decision queue status",
                                "all lifecycle-duration confirmation fields",
                            ],
                            "rule_mutation_requires": [
                                "accepted duration mapping",
                                "later config/training_lifecycle_rules.json change citing the mapping",
                            ],
                        },
                    }
                ),
                "generated_at": generated_at,
            }
            row["generated_at"] = stable_generated_at(existing, row, generated_at)
            rows.append({field: row[field] for field in FIELDS})

    rows.sort(
        key=lambda item: (
            {"duration_manual_decision_ready": 0, "duration_context_review_ready": 1}.get(item["batch_status"], 2),
            -as_int(item["review_row_count"]),
            item["official_program_type"],
            item["duration_evidence_status"],
            item["duration_review_batch_key"],
        )
    )
    for index, row in enumerate(rows, start=1):
        row["execution_order"] = index
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.execute("DROP TABLE IF EXISTS program_lifecycle_duration_review_batch_packets")
    conn.execute("DROP TABLE IF EXISTS program_lifecycle_duration_review_batches")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    if not rows:
        return
    fields_sql = ", ".join(FIELDS)
    placeholders = ", ".join(f":{field}" for field in FIELDS)
    conn.executemany(
        f"INSERT OR REPLACE INTO program_lifecycle_duration_review_batches ({fields_sql}) VALUES ({placeholders})",
        rows,
    )


def write_summary(rows: list[dict], generated_at: str) -> None:
    payload = {
        "generated_at": generated_at,
        "batch_rows": len(rows),
        "review_row_count": sum(as_int(row["review_row_count"]) for row in rows),
        "program_count": sum(as_int(row["program_count"]) for row in rows),
        "ready_queue_count": sum(as_int(row["ready_queue_count"]) for row in rows),
        "context_review_count": sum(as_int(row["context_review_count"]) for row in rows),
        "not_ready_count": sum(as_int(row["not_ready_count"]) for row in rows),
        "pending_decision_count": sum(as_int(row["pending_decision_count"]) for row in rows),
        "by_batch_status": dict(sorted(Counter(row["batch_status"] for row in rows).items())),
        "by_queue_status": dict(sorted(Counter(row["queue_status"] for row in rows).items())),
        "by_official_program_type": dict(sorted(Counter(row["official_program_type"] for row in rows).items())),
        "by_duration_evidence_status": dict(sorted(Counter(row["duration_evidence_status"] for row in rows).items())),
        "top_batches": [
            {
                "execution_order": row["execution_order"],
                "batch_status": row["batch_status"],
                "queue_status": row["queue_status"],
                "official_program_type": row["official_program_type"],
                "duration_evidence_status": row["duration_evidence_status"],
                "review_row_count": row["review_row_count"],
                "top_programs": row["top_programs"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": (
            "Lifecycle-duration review batches are non-mutating operator sessions. Accepted duration mappings "
            "still require explicit reviewer decisions, current evidence fingerprints, and later lifecycle-rule "
            "config changes before state-machine behavior changes."
        ),
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
    rows = build_rows(conn, generated_at)
    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    with conn:
        write_db(conn, rows)
    conn.close()
    write_summary(rows, generated_at)
    print(dumps({"program_lifecycle_duration_review_batches": len(rows)}))


if __name__ == "__main__":
    main()
