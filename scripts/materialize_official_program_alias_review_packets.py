#!/usr/bin/env python3
"""Materialize review packets for official-program alias action rows."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

OUT_CSV = ARTIFACTS / "official_program_alias_review_packets.csv"
OUT_JSON = ARTIFACTS / "official_program_alias_review_packets.json"
OUT_SUMMARY = ARTIFACTS / "official_program_alias_review_packets_summary.json"

FIELDNAMES = [
    "packet_key",
    "queue_key",
    "official_program_key",
    "official_program_name",
    "official_program_type",
    "official_department",
    "loaded_program_name",
    "loaded_role",
    "loaded_person_count",
    "loaded_source_url",
    "action_lane",
    "blocker_status",
    "alias_decision_status",
    "alias_confidence",
    "reviewer_ready",
    "coverage_mutation_allowed",
    "recommended_next_action",
    "review_question",
    "rationale",
    "evidence_json",
    "audited_at",
]

STOP_TOKENS = {
    "and",
    "current",
    "fellow",
    "fellows",
    "fellowship",
    "integrated",
    "of",
    "program",
    "residency",
    "resident",
    "residents",
    "selective",
    "the",
    "track",
}


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalized(value: str | None) -> str:
    text = (value or "").lower().replace("&", " and ").replace("/", " and ")
    text = text.replace("pediatrics", "pediatric")
    text = text.replace("diseases", "disease")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def tokens(value: str | None) -> set[str]:
    return {token for token in normalized(value).split() if token and token not in STOP_TOKENS}


def expected_loaded_role(program_type: str | None) -> str:
    if program_type == "residency":
        return "resident"
    if program_type == "fellowship":
        return "fellow"
    return ""


def existing_rows() -> dict[str, dict]:
    if not OUT_CSV.exists():
        return {}
    with OUT_CSV.open(newline="", encoding="utf-8") as handle:
        return {row["packet_key"]: row for row in csv.DictReader(handle)}


def stable_audited_at(existing: dict[str, dict], row: dict, timestamp: str) -> str:
    prior = existing.get(row["packet_key"])
    if not prior:
        return timestamp
    for field in FIELDNAMES:
        if field == "audited_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return timestamp
    return prior.get("audited_at") or timestamp


def rows_by_key(conn: sqlite3.Connection, query: str, key: str) -> dict[str, dict]:
    conn.row_factory = sqlite3.Row
    return {row[key]: dict(row) for row in conn.execute(query)}


def grouped_rows(conn: sqlite3.Connection, query: str, key: str) -> dict[str, list[dict]]:
    conn.row_factory = sqlite3.Row
    groups: dict[str, list[dict]] = {}
    for row in conn.execute(query):
        groups.setdefault(row[key], []).append(dict(row))
    return groups


def classify_alias(
    queue: dict,
    coverage: dict,
    alias_rows: list[dict],
    loaded_program_name: str,
    loaded_role: str,
    loaded_person_count: int,
) -> tuple[str, float, int, str, str, str]:
    official_name = queue.get("official_program_name") or ""
    official_type = queue.get("official_program_type") or ""
    official_norm = normalized(official_name)
    loaded_norm = normalized(loaded_program_name)
    official_tokens = tokens(official_name)
    loaded_tokens = tokens(loaded_program_name)
    overlap = len(official_tokens & loaded_tokens)
    role_matches = expected_loaded_role(official_type) == loaded_role if loaded_role else True
    blocker = queue.get("blocker_status") or ""

    if blocker == "exact_resolution_count_conflict":
        return (
            "not_alias_count_conflict_review",
            0.0,
            0,
            "review_count_conflict_before_alias_acceptance",
            "Does the resolved source contain people from a broader fellowship set than the official denominator row?",
            "Count conflict requires source-level review before any alias acceptance.",
        )
    if alias_rows:
        best = max(alias_rows, key=lambda row: float(row.get("relation_confidence") or 0))
        relation_status = best.get("relation_status") or ""
        confidence = float(best.get("relation_confidence") or 0)
        if relation_status == "same_program_alias_candidate":
            return (
                "reviewer_ready_same_program_alias_candidate",
                confidence,
                1,
                "review_and_accept_same_program_alias_if_source_current",
                "Does the loaded label and official denominator row name the same current program?",
                best.get("rationale") or "Existing alias audit marks this as same-program candidate.",
            )
        if relation_status == "section_level_split_candidate":
            return (
                "reviewer_ready_section_split_candidate",
                confidence,
                1,
                "split_loaded_program_by_section_label_then_close_gap",
                "Can the broader loaded source be split by section label into the official program?",
                best.get("rationale") or "Existing alias audit marks this as section-level split candidate.",
            )
        return (
            f"review_required_{relation_status}",
            confidence,
            0,
            best.get("suggested_mapping_action") or "review_existing_alias_candidate",
            "Does the related loaded source truly cover this official denominator row?",
            best.get("rationale") or "Existing alias audit requires review.",
        )

    if not role_matches:
        return (
            "role_mismatch_review",
            0.52,
            0,
            "do_not_accept_alias_without_role_specific_source",
            "Why does the loaded source role not match the official program type?",
            "Loaded role does not match the expected official program role.",
        )
    if "categorical" in official_norm and loaded_norm == "internal medicine residency":
        return (
            "reviewer_ready_broad_residency_alias_candidate",
            0.78,
            1,
            "accept_alias_only_if_loaded_source_excludes_combined_tracks",
            "Does Internal Medicine Residency source represent categorical residents only, or should tracks be split?",
            "Official categorical row maps to a broad Internal Medicine Residency label; likely useful but track boundaries need review.",
        )
    if {"internal", "medicine", "dermatology"}.issubset(official_tokens | loaded_tokens) and "dermatology" in official_norm:
        return (
            "reviewer_ready_combined_track_alias_candidate",
            0.8,
            1,
            "accept_combined_track_alias_if_roster_matches_official_track",
            "Does the loaded combined-track source exactly represent the official combined-track denominator row?",
            "Official and loaded labels describe the same combined track surface.",
        )
    if {"internal", "medicine", "pediatric"}.issubset(official_tokens | loaded_tokens) and "pediatric" in official_norm:
        return (
            "reviewer_ready_combined_track_alias_candidate",
            0.8,
            1,
            "accept_combined_track_alias_if_roster_matches_official_track",
            "Does the loaded combined-track source exactly represent the official combined-track denominator row?",
            "Official and loaded labels describe the same combined track surface.",
        )
    if "integrated" in official_norm and "integrated" in loaded_norm and overlap:
        return (
            "reviewer_ready_track_alias_candidate",
            0.82,
            1,
            "accept_track_alias_if_roster_scope_matches",
            "Does the loaded track source exactly represent the official integrated-track denominator row?",
            "Official and loaded labels share integrated-track wording and role.",
        )
    if overlap >= max(1, min(2, len(official_tokens))):
        return (
            "reviewer_ready_program_alias_candidate",
            0.82,
            1,
            "accept_program_alias_after_source_scope_check",
            "Does the loaded program label cover exactly this official denominator row?",
            "Official and loaded labels share key program tokens and the expected trainee role.",
        )
    return (
        "weak_alias_review",
        0.58,
        0,
        "collect_stronger_alias_or_split_evidence",
        "What source evidence links the loaded label to the official denominator row?",
        "Alias relation has insufficient token or track evidence for reviewer-ready acceptance.",
    )


def loaded_from_membership(conn: sqlite3.Connection, matched_program_key: str | None) -> dict:
    if not matched_program_key:
        return {}
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT pr.program_name AS loaded_program_name,
               p.role AS loaded_role,
               COUNT(DISTINCT p.person_key) AS loaded_person_count,
               s.source_url AS loaded_source_url
        FROM person_program_memberships m
        JOIN programs pr ON pr.program_key = m.program_key
        JOIN people p ON p.person_key = m.person_key
        LEFT JOIN sources s ON s.source_key = m.source_key
        WHERE m.program_key = ?
        GROUP BY pr.program_name, p.role, s.source_url
        ORDER BY COUNT(DISTINCT p.person_key) DESC
        LIMIT 1
        """,
        (matched_program_key,),
    ).fetchone()
    return dict(row) if row else {}


def build_rows(conn: sqlite3.Connection) -> list[dict]:
    timestamp = now_utc()
    existing = existing_rows()
    coverage = rows_by_key(conn, "SELECT * FROM official_program_coverage_audit", "official_program_key")
    alias_by_program = grouped_rows(conn, "SELECT * FROM official_program_alias_reconciliation_candidates", "official_program_key")
    queue_rows = [
        dict(row)
        for row in conn.execute(
            """
            SELECT *
            FROM official_program_coverage_action_queue
            WHERE action_lane IN (
                'alias_review',
                'accepted_alias_denominator_policy',
                'accepted_alias_open_gap_policy',
                'count_conflict_review'
            )
            ORDER BY priority DESC
            """
        )
    ]

    rows = []
    for queue in queue_rows:
        official_key = queue["official_program_key"]
        coverage_row = coverage.get(official_key, {})
        alias_rows = alias_by_program.get(official_key, [])
        packet_inputs: list[tuple[dict, list[dict]]] = []
        if alias_rows:
            for alias_row in alias_rows:
                packet_inputs.append(
                    (
                        {
                            "loaded_program_name": alias_row.get("loaded_program_name") or "",
                            "loaded_role": alias_row.get("loaded_role") or "",
                            "loaded_person_count": int(alias_row.get("loaded_person_count") or 0),
                            "loaded_source_url": alias_row.get("loaded_source_url") or "",
                            "alias_reconciliation_key": alias_row.get("reconciliation_key") or "",
                        },
                        [alias_row],
                    )
                )
        else:
            loaded = {}
            if coverage_row.get("matched_program_key"):
                loaded = loaded_from_membership(conn, coverage_row.get("matched_program_key"))
            packet_inputs.append(
                (
                    {
                        "loaded_program_name": loaded.get("loaded_program_name") or coverage_row.get("matched_program_name") or "",
                        "loaded_role": loaded.get("loaded_role") or "",
                        "loaded_person_count": int(loaded.get("loaded_person_count") or coverage_row.get("captured_people_count") or 0),
                        "loaded_source_url": loaded.get("loaded_source_url") or queue.get("candidate_url") or coverage_row.get("discovery_url") or "",
                        "alias_reconciliation_key": "",
                    },
                    [],
                )
            )

        for loaded, packet_alias_rows in packet_inputs:
            loaded_program_name = loaded.get("loaded_program_name") or ""
            loaded_role = loaded.get("loaded_role") or ""
            loaded_person_count = int(loaded.get("loaded_person_count") or 0)
            loaded_source_url = loaded.get("loaded_source_url") or ""
            status, confidence, reviewer_ready, action, question, rationale = classify_alias(
                queue,
                coverage_row,
                packet_alias_rows,
                loaded_program_name,
                loaded_role,
                loaded_person_count,
            )
            evidence = {
                "coverage_action_queue": queue,
                "coverage_row": coverage_row,
                "loaded_membership_summary": loaded,
                "existing_alias_candidates": packet_alias_rows,
                "token_features": {
                    "official_tokens": sorted(tokens(queue.get("official_program_name"))),
                    "loaded_tokens": sorted(tokens(loaded_program_name)),
                    "token_overlap": sorted(tokens(queue.get("official_program_name")) & tokens(loaded_program_name)),
                    "expected_loaded_role": expected_loaded_role(queue.get("official_program_type")),
                },
                "policy": {
                    "mutation": "This packet is non-mutating; reviewer_ready means ready for explicit acceptance/rejection, not automatic coverage mutation.",
                },
            }
            packet_identity_lane = (
                "alias_review"
                if queue.get("action_lane", "").startswith("accepted_alias_")
                else queue.get("action_lane", "")
            )
            packet_identity_queue_key = (
                "official_program_coverage_action_"
                + sha256_text(queue["official_program_key"] + "|" + packet_identity_lane)[:20]
            )
            packet_identity_key = (
                packet_identity_queue_key
                + "|"
                + loaded_program_name
                + "|"
                + loaded_role
                + "|"
                + loaded.get("alias_reconciliation_key", "")
            )
            packet_key = "official_program_alias_review_packet_" + sha256_text(packet_identity_key)[:20]
            row = {
                "packet_key": packet_key,
                "queue_key": queue["queue_key"],
                "official_program_key": official_key,
                "official_program_name": queue.get("official_program_name") or "",
                "official_program_type": queue.get("official_program_type") or "",
                "official_department": queue.get("official_department") or "",
                "loaded_program_name": loaded_program_name,
                "loaded_role": loaded_role,
                "loaded_person_count": loaded_person_count,
                "loaded_source_url": loaded_source_url,
                "action_lane": queue.get("action_lane") or "",
                "blocker_status": queue.get("blocker_status") or "",
                "alias_decision_status": status,
                "alias_confidence": confidence,
                "reviewer_ready": reviewer_ready,
                "coverage_mutation_allowed": 0,
                "recommended_next_action": action,
                "review_question": question,
                "rationale": rationale,
                "evidence_json": dumps(evidence),
                "audited_at": "",
            }
            row["audited_at"] = stable_audited_at(existing, row, timestamp)
            rows.append(row)

    return sorted(rows, key=lambda row: (-row["reviewer_ready"], -row["loaded_person_count"], row["official_department"], row["official_program_name"]))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_program_alias_review_packets")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    field_sql = ", ".join(FIELDNAMES)
    conn.executemany(f"INSERT INTO official_program_alias_review_packets ({field_sql}) VALUES ({placeholders})", rows)


def write_summary(rows: list[dict]) -> None:
    by_status = Counter(row["alias_decision_status"] for row in rows)
    by_action = Counter(row["recommended_next_action"] for row in rows)
    by_blocker = Counter(row["blocker_status"] for row in rows)
    payload = {
        "packet_rows": len(rows),
        "reviewer_ready_rows": sum(int(row["reviewer_ready"]) for row in rows),
        "reviewer_ready_person_count": sum(row["loaded_person_count"] for row in rows if int(row["reviewer_ready"]) == 1),
        "coverage_mutation_allowed_rows": sum(int(row["coverage_mutation_allowed"]) for row in rows),
        "total_loaded_person_count": sum(row["loaded_person_count"] for row in rows),
        "by_alias_decision_status": dict(sorted(by_status.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "by_blocker_status": dict(sorted(by_blocker.items())),
        "top_packets": [
            {
                "official_program_name": row["official_program_name"],
                "loaded_program_name": row["loaded_program_name"],
                "loaded_person_count": row["loaded_person_count"],
                "alias_decision_status": row["alias_decision_status"],
                "reviewer_ready": row["reviewer_ready"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:15]
        ],
        "mutation_policy": "non_mutating_alias_review_packets; explicit reviewer acceptance is required before denominator coverage mutation",
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "generated_at": now_utc(),
    }
    OUT_SUMMARY.write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    with conn:
        rows = build_rows(conn)
        write_csv(OUT_CSV, rows)
        OUT_JSON.write_text(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
        write_summary(rows)
        write_db(conn, rows)
    conn.close()
    print(dumps({"official_program_alias_review_packets": len(rows)}))


if __name__ == "__main__":
    main()
