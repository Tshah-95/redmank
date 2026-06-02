#!/usr/bin/env python3
"""Persist current training-state exports as durable snapshots and transition rows."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
CURRENT_EXPORT = ARTIFACTS / "training_states_current.csv"
SNAPSHOT_DIR = ARTIFACTS / "training_state_snapshots"

SNAPSHOT_FIELDS = [
    "state_key",
    "canonical_person_program_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "observed_at",
    "as_of_date",
    "raw_stage_label",
    "normalized_stage",
    "stage_family",
    "stage_index",
    "stage_rank",
    "trainee_category",
    "lifecycle_rule_key",
    "lifecycle_code",
    "lifecycle_stage",
    "academic_year",
    "estimated_start_date",
    "estimated_end_date",
    "expected_next_stage",
    "expected_next_date",
    "expected_exit_date",
    "expected_transition_type",
    "stale_after_date",
    "refresh_policy",
    "transition_rule",
    "status",
    "confidence",
    "source_key",
    "state_fingerprint",
]

STAGE_FAMILY_PRIORITY = {
    "clinical_postgraduate": 90,
    "fellowship": 80,
    "medical_school": 70,
    "research_phase": 60,
    "clinical_postgraduate_research": 55,
    "post_training_or_alumni": 20,
    "unknown": 0,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def as_int(value: str | None) -> int | None:
    if value in {None, ""}:
        return None
    return int(value)


def as_float(value: str | None) -> float:
    if value in {None, ""}:
        return 0.0
    return float(value)


def canonical_key(row: dict) -> str:
    return f"{row.get('person_key') or ''}::{row.get('program_name') or ''}"


def state_fingerprint(row: dict) -> str:
    payload = {
        key: row.get(key) or ""
        for key in [
            "person_key",
            "program_name",
            "role",
            "raw_stage_label",
            "normalized_stage",
            "stage_family",
            "stage_index",
            "lifecycle_code",
            "expected_next_stage",
            "expected_next_date",
            "expected_exit_date",
            "expected_transition_type",
            "stale_after_date",
            "source_key",
        ]
    }
    return sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))


def deterministic_state_key(row: dict) -> str:
    if row.get("state_key"):
        return row["state_key"]
    basis = "|".join(
        [
            row.get("person_key") or "",
            row.get("program_name") or "",
            row.get("source_key") or "",
            row.get("raw_stage_label") or "",
            row.get("normalized_stage") or "",
        ]
    )
    return f"snapshot_state_{sha256_bytes(basis.encode('utf-8'))[:16]}"


def canonical_rank(row: dict) -> tuple[int, int, float, str]:
    return (
        int(as_int(row.get("stage_index")) is not None),
        as_float(row.get("confidence")),
        STAGE_FAMILY_PRIORITY.get(row.get("stage_family") or "", 0),
        as_int(row.get("stage_rank")) or 999,
        row.get("observed_at") or "",
    )


def canonical_rows(rows: list[dict]) -> tuple[dict[str, dict], int]:
    chosen: dict[str, dict] = {}
    duplicate_count = 0
    for row in rows:
        key = row["canonical_person_program_key"]
        if key in chosen:
            duplicate_count += 1
            if canonical_rank(row) <= canonical_rank(chosen[key]):
                continue
        chosen[key] = row
    return chosen, duplicate_count


def read_export(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        raw_rows = list(csv.DictReader(f))
    rows = []
    for row in raw_rows:
        row = {key: row.get(key, "") for key in row}
        row["state_key"] = deterministic_state_key(row)
        row["canonical_person_program_key"] = canonical_key(row)
        row["state_fingerprint"] = state_fingerprint(row)
        rows.append(row)
    return rows


def snapshot_id_for(rows: list[dict], csv_hash: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    as_of_dates = sorted({row.get("as_of_date") or "" for row in rows if row.get("as_of_date")})
    as_of = as_of_dates[-1] if as_of_dates else date.today().isoformat()
    return f"training_states_{as_of}_{csv_hash[:12]}"


def write_snapshot_files(snapshot_id: str, rows: list[dict], csv_hash: str, source_path: Path, notes: str) -> dict:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = SNAPSHOT_DIR / f"{snapshot_id}.csv"
    manifest_path = SNAPSHOT_DIR / f"{snapshot_id}.json"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(rows[0].keys()) if rows else SNAPSHOT_FIELDS
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    canonical, duplicate_count = canonical_rows(rows)
    as_of_dates = sorted({row.get("as_of_date") or "" for row in rows if row.get("as_of_date")})
    existing_manifest = {}
    if manifest_path.exists():
        try:
            existing_manifest = read_manifest(manifest_path)
        except json.JSONDecodeError:
            existing_manifest = {}
    created_at = datetime.now(timezone.utc).isoformat()
    if (
        existing_manifest.get("snapshot_id") == snapshot_id
        and existing_manifest.get("corpus_fingerprint") == csv_hash
        and existing_manifest.get("created_at")
    ):
        created_at = existing_manifest["created_at"]
    manifest = {
        "snapshot_id": snapshot_id,
        "created_at": created_at,
        "as_of_date": as_of_dates[-1] if as_of_dates else date.today().isoformat(),
        "source_export_path": str(source_path.relative_to(ROOT)),
        "snapshot_csv": str(csv_path.relative_to(ROOT)),
        "corpus_fingerprint": csv_hash,
        "row_count": len(rows),
        "canonical_key_count": len(canonical),
        "duplicate_canonical_key_count": duplicate_count,
        "notes": notes,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def read_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def insert_snapshot(conn: sqlite3.Connection, manifest: dict, rows: list[dict]) -> None:
    conn.execute(
        """
        INSERT OR REPLACE INTO training_state_snapshots
        (snapshot_id, created_at, as_of_date, source_export_path, corpus_fingerprint,
         row_count, canonical_key_count, duplicate_canonical_key_count, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            manifest["snapshot_id"],
            manifest["created_at"],
            manifest["as_of_date"],
            manifest["source_export_path"],
            manifest["corpus_fingerprint"],
            manifest["row_count"],
            manifest["canonical_key_count"],
            manifest["duplicate_canonical_key_count"],
            manifest.get("notes", ""),
        ),
    )
    for row in rows:
        conn.execute(
            """
            INSERT OR REPLACE INTO training_state_snapshot_rows
            (snapshot_id, state_key, canonical_person_program_key, person_key,
             display_name, role, program_name, observed_at, as_of_date, raw_stage_label,
             normalized_stage, stage_family, stage_index, stage_rank, trainee_category,
             lifecycle_rule_key, lifecycle_code, lifecycle_stage, academic_year,
             estimated_start_date, estimated_end_date, expected_next_stage,
             expected_next_date, expected_exit_date, expected_transition_type,
             stale_after_date, refresh_policy, transition_rule, status, confidence,
             source_key, state_fingerprint)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                manifest["snapshot_id"],
                row["state_key"],
                row["canonical_person_program_key"],
                row.get("person_key"),
                row.get("display_name"),
                row.get("role"),
                row.get("program_name"),
                row.get("observed_at"),
                row.get("as_of_date"),
                row.get("raw_stage_label"),
                row.get("normalized_stage"),
                row.get("stage_family"),
                as_int(row.get("stage_index")),
                as_int(row.get("stage_rank")),
                row.get("trainee_category"),
                row.get("lifecycle_rule_key"),
                row.get("lifecycle_code"),
                row.get("lifecycle_stage"),
                row.get("academic_year"),
                row.get("estimated_start_date"),
                row.get("estimated_end_date"),
                row.get("expected_next_stage"),
                row.get("expected_next_date"),
                row.get("expected_exit_date"),
                row.get("expected_transition_type"),
                row.get("stale_after_date"),
                row.get("refresh_policy"),
                row.get("transition_rule"),
                row.get("status"),
                as_float(row.get("confidence")),
                row.get("source_key"),
                row["state_fingerprint"],
            ),
        )


def classify_transition(old: dict | None, new: dict | None, compare_date: date) -> dict:
    if old and not new:
        stale_after = parse_date(old.get("stale_after_date"))
        is_stale = bool(stale_after and stale_after <= compare_date)
        is_completion = old.get("expected_transition_type") == "expected_completion"
        if is_stale and is_completion:
            return {
                "change_type": "removed_expected_completion",
                "transition_assurance": "expected",
                "expected_by_state_machine": 1,
                "review_action": "mark_completion_or_alumni_candidate",
                "notes": "Terminal state disappeared after stale-after date.",
            }
        if is_stale:
            return {
                "change_type": "removed_after_stale_review",
                "transition_assurance": "review",
                "expected_by_state_machine": 0,
                "review_action": "refresh_source_before_departure_mutation",
                "notes": "State disappeared after stale-after date but did not have a deterministic completion rule.",
            }
        return {
            "change_type": "removed_unexpected",
            "transition_assurance": "review",
            "expected_by_state_machine": 0,
            "review_action": "review_scraper_source_identity_or_early_departure",
            "notes": "State disappeared before stale-after date.",
        }
    if new and not old:
        return {
            "change_type": "added",
            "transition_assurance": "new_observation",
            "expected_by_state_machine": 0,
            "review_action": "accept_as_new_public_observation",
            "notes": "New person/program state observation.",
        }
    assert old and new
    if old.get("state_fingerprint") == new.get("state_fingerprint"):
        return {
            "change_type": "unchanged",
            "transition_assurance": "same_state",
            "expected_by_state_machine": 1,
            "review_action": "retain",
            "notes": "Same state fingerprint.",
        }
    if old.get("normalized_stage") == new.get("normalized_stage"):
        expected_next_date = parse_date(old.get("expected_next_date"))
        if expected_next_date and expected_next_date <= compare_date:
            return {
                "change_type": "same_stage_after_expected_transition_review",
                "transition_assurance": "review",
                "expected_by_state_machine": 0,
                "review_action": "require_fresh_source_or_lifecycle_rule_review",
                "notes": "Stage stayed the same after the prior expected transition date.",
            }
        return {
            "change_type": "same_stage_updated_evidence",
            "transition_assurance": "same_stage",
            "expected_by_state_machine": 1,
            "review_action": "retain_with_new_evidence",
            "notes": "Same normalized stage with changed evidence fields.",
        }
    if old.get("expected_next_stage") and old.get("expected_next_stage") == new.get("normalized_stage"):
        return {
            "change_type": "advanced_expected",
            "transition_assurance": "expected",
            "expected_by_state_machine": 1,
            "review_action": "accept_expected_stage_advancement_if_freshly_observed",
            "notes": "New normalized stage matches prior expected_next_stage.",
        }
    old_rank = as_int(old.get("stage_rank")) or 999
    new_rank = as_int(new.get("stage_rank")) or 999
    if new_rank < old_rank:
        return {
            "change_type": "stage_regressed_review",
            "transition_assurance": "review",
            "expected_by_state_machine": 0,
            "review_action": "review_duplicate_identity_or_stage_parser",
            "notes": "New stage rank is earlier than prior stage rank.",
        }
    return {
        "change_type": "stage_changed_review",
        "transition_assurance": "review",
        "expected_by_state_machine": 0,
        "review_action": "review_lifecycle_rule_source_label_or_identity",
        "notes": "Stage changed outside the prior expected transition.",
    }


def write_transition_events(
    conn: sqlite3.Connection,
    old_snapshot_id: str | None,
    new_snapshot_id: str,
    old_rows: list[dict],
    new_rows: list[dict],
    compare_date: date,
) -> list[dict]:
    old_canonical, _ = canonical_rows(old_rows)
    new_canonical, _ = canonical_rows(new_rows)
    events = []
    for key in sorted(set(old_canonical) | set(new_canonical)):
        old = old_canonical.get(key)
        new = new_canonical.get(key)
        source = new or old or {}
        event = {
            "old_snapshot_id": old_snapshot_id,
            "new_snapshot_id": new_snapshot_id,
            "canonical_person_program_key": key,
            "person_key": source.get("person_key"),
            "display_name": source.get("display_name"),
            "program_name": source.get("program_name"),
            "role": source.get("role"),
            "old_state_key": (old or {}).get("state_key"),
            "new_state_key": (new or {}).get("state_key"),
            "old_stage": (old or {}).get("normalized_stage"),
            "new_stage": (new or {}).get("normalized_stage"),
            "old_expected_next_stage": (old or {}).get("expected_next_stage"),
            "old_expected_next_date": (old or {}).get("expected_next_date"),
            "old_expected_exit_date": (old or {}).get("expected_exit_date"),
            "old_expected_transition_type": (old or {}).get("expected_transition_type"),
            "old_stale_after_date": (old or {}).get("stale_after_date"),
            **classify_transition(old, new, compare_date),
        }
        event["evidence_json"] = json.dumps(
            {
                "old_lifecycle_code": (old or {}).get("lifecycle_code"),
                "new_lifecycle_code": (new or {}).get("lifecycle_code"),
                "old_state_fingerprint": (old or {}).get("state_fingerprint"),
                "new_state_fingerprint": (new or {}).get("state_fingerprint"),
                "compare_date": compare_date.isoformat(),
            },
            sort_keys=True,
        )
        events.append(event)
        conn.execute(
            """
            INSERT OR REPLACE INTO training_state_transition_events
            (old_snapshot_id, new_snapshot_id, canonical_person_program_key,
             person_key, display_name, program_name, role, old_state_key, new_state_key,
             change_type, transition_assurance, expected_by_state_machine,
             old_stage, new_stage, old_expected_next_stage, old_expected_next_date,
             old_expected_exit_date, old_expected_transition_type, old_stale_after_date,
             review_action, notes, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["old_snapshot_id"],
                event["new_snapshot_id"],
                event["canonical_person_program_key"],
                event["person_key"],
                event["display_name"],
                event["program_name"],
                event["role"],
                event["old_state_key"],
                event["new_state_key"],
                event["change_type"],
                event["transition_assurance"],
                event["expected_by_state_machine"],
                event["old_stage"],
                event["new_stage"],
                event["old_expected_next_stage"],
                event["old_expected_next_date"],
                event["old_expected_exit_date"],
                event["old_expected_transition_type"],
                event["old_stale_after_date"],
                event["review_action"],
                event["notes"],
                event["evidence_json"],
            ),
        )
    return events


def load_all_snapshots(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    snapshots = {}
    conn.execute("DELETE FROM training_state_transition_events")
    conn.execute("DELETE FROM training_state_snapshot_rows")
    conn.execute("DELETE FROM training_state_snapshots")
    for manifest_path in sorted(SNAPSHOT_DIR.glob("*.json")):
        manifest = read_manifest(manifest_path)
        csv_path = ROOT / manifest["snapshot_csv"]
        rows = read_export(csv_path)
        insert_snapshot(conn, manifest, rows)
        snapshots[manifest["snapshot_id"]] = rows
    return snapshots


def write_events_csv(events: list[dict]) -> None:
    path = ARTIFACTS / "training_state_transition_events.csv"
    if not events:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        fieldnames = [key for key in events[0].keys() if key != "evidence_json"] + ["evidence_json"]
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(events)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--current-export", type=Path, default=CURRENT_EXPORT)
    parser.add_argument("--snapshot-id")
    parser.add_argument("--previous-snapshot-id")
    parser.add_argument("--compare-date", default=date.today().isoformat())
    parser.add_argument("--notes", default="Current training-state export materialized for longitudinal diffing")
    args = parser.parse_args()

    source_bytes = args.current_export.read_bytes()
    csv_hash = sha256_bytes(source_bytes)
    current_rows = read_export(args.current_export)
    snapshot_id = snapshot_id_for(current_rows, csv_hash, args.snapshot_id)
    manifest = write_snapshot_files(snapshot_id, current_rows, csv_hash, args.current_export, args.notes)

    conn = sqlite3.connect(args.db)
    with conn:
        snapshots = load_all_snapshots(conn)
        snapshot_ids = sorted(snapshots)
        previous_snapshot_id = args.previous_snapshot_id
        if previous_snapshot_id is None:
            candidates = [item for item in snapshot_ids if item != snapshot_id]
            previous_snapshot_id = candidates[-1] if candidates else None
        old_rows = snapshots.get(previous_snapshot_id, []) if previous_snapshot_id else []
        events = write_transition_events(
            conn,
            previous_snapshot_id,
            snapshot_id,
            old_rows,
            snapshots[snapshot_id],
            date.fromisoformat(args.compare_date),
        )
    conn.close()

    write_events_csv(events)
    change_counts = Counter(event["change_type"] for event in events)
    summary = {
        "snapshot_id": snapshot_id,
        "previous_snapshot_id": previous_snapshot_id,
        "snapshot_manifest": str((SNAPSHOT_DIR / f"{snapshot_id}.json").relative_to(ROOT)),
        "snapshot_csv": manifest["snapshot_csv"],
        "row_count": manifest["row_count"],
        "canonical_key_count": manifest["canonical_key_count"],
        "duplicate_canonical_key_count": manifest["duplicate_canonical_key_count"],
        "transition_event_rows": len(events),
        "transition_events_csv": "artifacts/data/training_state_transition_events.csv",
        "by_change_type": dict(sorted(change_counts.items())),
        "compare_date": args.compare_date,
    }
    (ARTIFACTS / "training_state_snapshot_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
