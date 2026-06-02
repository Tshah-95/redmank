#!/usr/bin/env python3
"""Classify remaining official HUP GME coverage gaps by evidence-backed reason."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urldefrag


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"


def norm_space(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip()


def canonical_url(url: str | None) -> str:
    if not url:
        return ""
    clean, _fragment = urldefrag(url)
    return clean.rstrip("/")


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def existing_audit_rows() -> dict[str, dict]:
    path = ARTIFACTS / "hup_gap_reason_audit.csv"
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as f:
        return {row["official_program_key"]: row for row in csv.DictReader(f)}


def stable_audited_at(existing: dict[str, dict], row: dict, new_value: str) -> str:
    prior = existing.get(row["official_program_key"])
    if not prior:
        return new_value
    stable_fields = [
        "coverage_status",
        "gap_reason_status",
        "recommended_next_action",
        "reason_confidence",
        "candidate_count",
        "roster_candidate_count",
        "context_candidate_count",
        "low_value_candidate_count",
        "probed_url_count",
        "reachable_probe_count",
        "low_content_probe_count",
        "max_roster_term_count",
        "max_context_term_count",
        "related_loaded_source_count",
        "related_loaded_person_count",
        "top_candidate_url",
        "top_candidate_title",
        "top_candidate_status",
        "top_candidate_priority",
        "top_candidate_confidence",
        "evidence_json",
    ]
    for field in stable_fields:
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return new_value
    return prior.get("audited_at") or new_value


def uncovered_program_rows(conn: sqlite3.Connection) -> list[dict]:
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT
              u.official_program_key,
              u.department,
              u.program_type,
              u.program_name,
              u.program_url,
              a.coverage_status,
              a.discovery_classification,
              a.discovery_title,
              a.discovery_url,
              a.notes
            FROM official_program_universe u
            JOIN official_program_coverage_audit a
              ON a.official_program_key = u.official_program_key
            WHERE a.coverage_status != 'covered_current_roster'
            ORDER BY a.coverage_status, u.department, u.program_type, u.program_name
            """
        )
    ]


def read_grouped(conn: sqlite3.Connection, table: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in conn.execute(f"SELECT * FROM {table}"):
        grouped[row["official_program_key"]].append(dict(row))
    return grouped


def source_usage_by_url(conn: sqlite3.Connection) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for row in conn.execute(
        """
        SELECT
          s.source_url,
          COUNT(DISTINCT m.person_key) AS membership_people,
          COUNT(DISTINCT e.person_key) AS evidence_people,
          GROUP_CONCAT(DISTINCT p.program_name) AS programs,
          GROUP_CONCAT(DISTINCT pe.role) AS roles
        FROM sources s
        LEFT JOIN person_program_memberships m ON m.source_key = s.source_key
        LEFT JOIN programs p ON p.program_key = m.program_key
        LEFT JOIN people pe ON pe.person_key = m.person_key
        LEFT JOIN evidence_claims e ON e.source_key = s.source_key AND e.status = 'accepted'
        WHERE s.source_url IS NOT NULL AND s.source_url != ''
        GROUP BY s.source_url
        """
    ):
        key = canonical_url(row["source_url"])
        if not key:
            continue
        current = result.setdefault(
            key,
            {
                "source_urls": set(),
                "membership_people": 0,
                "evidence_people": 0,
                "programs": set(),
                "roles": set(),
            },
        )
        current["source_urls"].add(row["source_url"])
        current["membership_people"] += int(row["membership_people"] or 0)
        current["evidence_people"] += int(row["evidence_people"] or 0)
        for program in (row["programs"] or "").split(","):
            if norm_space(program):
                current["programs"].add(norm_space(program))
        for role in (row["roles"] or "").split(","):
            if norm_space(role):
                current["roles"].add(norm_space(role))
    return result


def top_candidate(candidates: list[dict]) -> dict:
    if not candidates:
        return {}
    status_priority = {
        "roster_source_candidate": 3,
        "program_context_candidate": 2,
        "low_value_candidate": 1,
        "unreachable_or_error": 0,
    }
    role_priority = {
        "official_program_url": 3,
        "known_discovery_url": 2,
        "linked_candidate": 1,
    }
    return max(
        candidates,
        key=lambda row: (
            (100 if row.get("candidate_status") == "roster_source_candidate" else 0)
            + (10 * role_priority.get(row.get("source_role") or "", 0))
            + status_priority.get(row.get("candidate_status") or "", 0),
            int(row.get("priority") or 0),
            float(row.get("confidence") or 0.0),
            int(row.get("roster_term_count") or 0),
        ),
    )


def related_loaded_sources(candidates: list[dict], usage_by_url: dict[str, dict]) -> list[dict]:
    hits = []
    for candidate in candidates:
        usage = usage_by_url.get(canonical_url(candidate.get("candidate_url")))
        if not usage:
            continue
        person_count = max(int(usage["membership_people"]), int(usage["evidence_people"]))
        if person_count <= 0:
            continue
        hits.append(
            {
                "candidate_url": candidate.get("candidate_url"),
                "candidate_status": candidate.get("candidate_status"),
                "person_count": person_count,
                "programs": sorted(usage["programs"]),
                "roles": sorted(usage["roles"]),
            }
        )
    return hits


def classify_gap(row: dict, candidates: list[dict], probes: list[dict], related_hits: list[dict]) -> tuple[str, str, float, str]:
    roster_count = sum(1 for item in candidates if item.get("candidate_status") == "roster_source_candidate")
    context_count = sum(1 for item in candidates if item.get("candidate_status") == "program_context_candidate")
    low_value_count = sum(1 for item in candidates if item.get("candidate_status") == "low_value_candidate")
    reachable_probe_count = sum(1 for item in probes if int(item.get("http_status") or 0) and int(item.get("http_status") or 0) < 400)
    low_content_count = sum(
        1
        for item in probes
        if int(item.get("http_status") or 0) == 200 and int(item.get("text_length") or 0) < 200
    )
    max_roster_terms = max([int(item.get("roster_term_count") or 0) for item in probes + candidates] or [0])
    max_context_terms = max([int(item.get("context_term_count") or 0) for item in probes + candidates] or [0])

    if related_hits:
        return (
            "source_already_loaded_related_program_review",
            "review_program_alias_or_official_denominator_mapping",
            0.86,
            "A candidate roster/source URL is already represented by accepted people under a related program label.",
        )
    if low_content_count and low_content_count >= reachable_probe_count and reachable_probe_count:
        return (
            "official_page_empty_or_low_content",
            "find_alternate_public_source_or_record_no_public_roster",
            0.78,
            "The reachable official/probed page has too little text to support a current roster extraction.",
        )
    if roster_count:
        return (
            "roster_source_candidate_needs_parser_or_manual_review",
            "inspect_candidate_roster_page_and_add_supported_parser",
            0.72 if max_roster_terms else 0.66,
            "A candidate URL has roster-like language but no accepted current roster people for this official program.",
        )
    if reachable_probe_count and (context_count or max_context_terms):
        return (
            "public_program_context_no_current_roster",
            "record_context_source_and_monitor_for_roster_or_alumni_link",
            0.7,
            "Public Penn pages describe the program but current trainee roster structure is not visible in probe evidence.",
        )
    if candidates:
        return (
            "candidate_sources_low_signal",
            "broaden_source_discovery_queries_before_scraping_people",
            0.56 if low_value_count else 0.5,
            "Candidate URLs exist but are low-signal for current public trainee rosters.",
        )
    if row.get("coverage_status") == "not_discovered":
        return (
            "not_discovered_by_current_strategy",
            "broaden_official_site_search_and_external_profile_discovery",
            0.48,
            "No usable Penn source candidate has been discovered for this official denominator program.",
        )
    return (
        "unclassified_gap_review",
        "manual_gap_review",
        0.35,
        "Existing audit evidence does not support a more specific deterministic gap reason.",
    )


def audit_rows(conn: sqlite3.Connection) -> list[dict]:
    existing = existing_audit_rows()
    candidates_by_program = read_grouped(conn, "official_program_source_candidates")
    probes_by_program = read_grouped(conn, "official_program_source_probes")
    usage_by_url = source_usage_by_url(conn)
    audited_at = datetime.now(timezone.utc).isoformat()
    rows = []
    for row in uncovered_program_rows(conn):
        candidates = candidates_by_program.get(row["official_program_key"], [])
        probes = probes_by_program.get(row["official_program_key"], [])
        related_hits = related_loaded_sources(candidates, usage_by_url)
        top = top_candidate(candidates)
        status, action, confidence, rationale = classify_gap(row, candidates, probes, related_hits)
        roster_count = sum(1 for item in candidates if item.get("candidate_status") == "roster_source_candidate")
        context_count = sum(1 for item in candidates if item.get("candidate_status") == "program_context_candidate")
        low_value_count = sum(1 for item in candidates if item.get("candidate_status") == "low_value_candidate")
        reachable_probe_count = sum(
            1 for item in probes if int(item.get("http_status") or 0) and int(item.get("http_status") or 0) < 400
        )
        low_content_probe_count = sum(
            1
            for item in probes
            if int(item.get("http_status") or 0) == 200 and int(item.get("text_length") or 0) < 200
        )
        related_person_count = sum(int(item["person_count"]) for item in related_hits)
        evidence = {
            "classification_rationale": rationale,
            "coverage_discovery_classification": row.get("discovery_classification") or "",
            "coverage_discovery_url": row.get("discovery_url") or "",
            "related_loaded_sources": related_hits,
            "top_candidate": top,
            "probe_urls": [
                {
                    "requested_url": probe.get("requested_url"),
                    "http_status": probe.get("http_status"),
                    "title": probe.get("title"),
                    "text_length": probe.get("text_length"),
                    "roster_term_count": probe.get("roster_term_count"),
                    "context_term_count": probe.get("context_term_count"),
                }
                for probe in probes
            ],
        }
        audit_row = {
                "official_program_key": row["official_program_key"],
                "department": row.get("department") or "",
                "program_type": row["program_type"],
                "program_name": row["program_name"],
                "coverage_status": row["coverage_status"],
                "gap_reason_status": status,
                "recommended_next_action": action,
                "reason_confidence": confidence,
                "candidate_count": len(candidates),
                "roster_candidate_count": roster_count,
                "context_candidate_count": context_count,
                "low_value_candidate_count": low_value_count,
                "probed_url_count": len(probes),
                "reachable_probe_count": reachable_probe_count,
                "low_content_probe_count": low_content_probe_count,
                "max_roster_term_count": max(
                    [int(item.get("roster_term_count") or 0) for item in probes + candidates] or [0]
                ),
                "max_context_term_count": max(
                    [int(item.get("context_term_count") or 0) for item in probes + candidates] or [0]
                ),
                "related_loaded_source_count": len(related_hits),
                "related_loaded_person_count": related_person_count,
                "top_candidate_url": top.get("candidate_url", ""),
                "top_candidate_title": top.get("candidate_title", ""),
                "top_candidate_status": top.get("candidate_status", ""),
                "top_candidate_priority": top.get("priority", ""),
                "top_candidate_confidence": top.get("confidence", ""),
                "evidence_json": dumps(evidence),
                "audited_at": audited_at,
            }
        audit_row["audited_at"] = stable_audited_at(existing, audit_row, audited_at)
        rows.append(audit_row)
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM official_program_gap_reason_audit")
    for row in rows:
        conn.execute(
            """
            INSERT INTO official_program_gap_reason_audit
            (official_program_key, department, program_type, program_name, coverage_status,
             gap_reason_status, recommended_next_action, reason_confidence,
             candidate_count, roster_candidate_count, context_candidate_count,
             low_value_candidate_count, probed_url_count, reachable_probe_count,
             low_content_probe_count, max_roster_term_count, max_context_term_count,
             related_loaded_source_count, related_loaded_person_count,
             top_candidate_url, top_candidate_title, top_candidate_status,
             top_candidate_priority, top_candidate_confidence, evidence_json, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["official_program_key"],
                row["department"],
                row["program_type"],
                row["program_name"],
                row["coverage_status"],
                row["gap_reason_status"],
                row["recommended_next_action"],
                row["reason_confidence"],
                row["candidate_count"],
                row["roster_candidate_count"],
                row["context_candidate_count"],
                row["low_value_candidate_count"],
                row["probed_url_count"],
                row["reachable_probe_count"],
                row["low_content_probe_count"],
                row["max_roster_term_count"],
                row["max_context_term_count"],
                row["related_loaded_source_count"],
                row["related_loaded_person_count"],
                row["top_candidate_url"],
                row["top_candidate_title"],
                row["top_candidate_status"],
                row["top_candidate_priority"],
                row["top_candidate_confidence"],
                row["evidence_json"],
                row["audited_at"],
            ),
        )


def summary_payload(rows: list[dict]) -> dict:
    by_status = Counter(row["gap_reason_status"] for row in rows)
    by_action = Counter(row["recommended_next_action"] for row in rows)
    by_coverage = Counter(row["coverage_status"] for row in rows)
    by_program_type_status = Counter(f"{row['program_type']}:{row['gap_reason_status']}" for row in rows)
    return {
        "generated_at": max((row["audited_at"] for row in rows), default=datetime.now(timezone.utc).isoformat()),
        "gap_rows": len(rows),
        "by_gap_reason_status": dict(sorted(by_status.items())),
        "by_recommended_next_action": dict(sorted(by_action.items())),
        "by_coverage_status": dict(sorted(by_coverage.items())),
        "by_program_type_and_reason": dict(sorted(by_program_type_status.items())),
        "roster_candidate_gap_rows": sum(1 for row in rows if row["roster_candidate_count"]),
        "related_loaded_source_gap_rows": sum(1 for row in rows if row["related_loaded_source_count"]),
        "low_content_gap_rows": sum(1 for row in rows if row["low_content_probe_count"]),
        "csv": "artifacts/data/hup_gap_reason_audit.csv",
        "json": "artifacts/data/hup_gap_reason_audit.json",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    rows = audit_rows(conn)
    summary = summary_payload(rows)
    with conn:
        write_sqlite(conn, rows)
    conn.close()

    write_csv(ARTIFACTS / "hup_gap_reason_audit.csv", rows)
    (ARTIFACTS / "hup_gap_reason_audit.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ARTIFACTS / "hup_gap_reason_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
