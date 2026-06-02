#!/usr/bin/env python3
"""Materialize execution readiness for the recursive enrichment queue."""

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

CSV_PATH = ARTIFACTS / "person_enrichment_execution_readiness.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_execution_readiness.json"
ROLLUP_CSV_PATH = ARTIFACTS / "person_enrichment_execution_readiness_rollups.csv"
ROLLUP_JSON_PATH = ARTIFACTS / "person_enrichment_execution_readiness_rollups.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_execution_readiness_summary.json"

READINESS_FIELDS = [
    "readiness_key",
    "task_key",
    "person_key",
    "display_name",
    "role",
    "program_name",
    "task_type",
    "source_family",
    "priority",
    "priority_band",
    "execution_lane",
    "automation_status",
    "existing_collector",
    "command_hint",
    "input_artifacts_json",
    "output_artifacts_json",
    "requires_network",
    "requires_manual_review",
    "requires_script_extension",
    "requires_new_parser",
    "batch_key",
    "batch_rank",
    "readiness_reason",
    "next_system_action",
    "evidence_json",
    "generated_at",
]

ROLLUP_FIELDS = [
    "rollup_key",
    "rollup_scope",
    "rollup_value",
    "task_type",
    "source_family",
    "priority_band",
    "execution_lane",
    "automation_status",
    "task_count",
    "person_count",
    "critical_task_count",
    "network_required_count",
    "manual_review_required_count",
    "script_extension_required_count",
    "new_parser_required_count",
    "top_command_hint",
    "next_system_action",
    "evidence_json",
    "generated_at",
]

TASK_EXECUTION = {
    "current_roster_state_reconciliation": {
        "execution_lane": "collector_with_reconciliation_required",
        "automation_status": "collector_available_partial_source_coverage",
        "existing_collector": "scripts/scrape_penn_training.py; scripts/discover_penn_affiliated_sources.py; scripts/scrape_penn_affiliated_rosters.py",
        "command_hint": "python3 scripts/scrape_penn_training.py && python3 scripts/discover_penn_affiliated_sources.py && python3 scripts/scrape_penn_affiliated_rosters.py",
        "input_artifacts": [
            "artifacts/data/penn_training_sources.json",
            "artifacts/data/penn_affiliated_source_discovery.json",
        ],
        "output_artifacts": [
            "artifacts/data/penn_training_people.json",
            "artifacts/data/penn_affiliated_people.json",
            "artifacts/data/training_states_current.csv",
        ],
        "requires_network": 1,
        "requires_manual_review": 0,
        "requires_script_extension": 0,
        "requires_new_parser": 0,
        "readiness_reason": "Roster collectors exist, but broad Penn coverage is source/parser-dependent and still must be reconciled through the state-machine transition plan.",
        "next_system_action": "run_or_extend_official_roster_collectors_then_reconcile_state_machine",
    },
    "evidence_reconciliation_review": {
        "execution_lane": "reviewer_decision_required",
        "automation_status": "manual_decision_ready",
        "existing_collector": "scripts/audit_person_evidence_review_packets.py; scripts/audit_enrichment_acceptance.py",
        "command_hint": "review artifacts/data/person_evidence_review_packets.csv and record decisions in evidence_reconciliation_decisions.csv policy lanes",
        "input_artifacts": [
            "artifacts/data/person_evidence_review_packets.csv",
            "artifacts/data/enrichment_acceptance_audit.csv",
        ],
        "output_artifacts": [
            "artifacts/data/evidence_reconciliation_decisions.csv",
            "artifacts/data/accepted_enrichment_claims.csv",
        ],
        "requires_network": 0,
        "requires_manual_review": 1,
        "requires_script_extension": 0,
        "requires_new_parser": 0,
        "readiness_reason": "Candidate evidence is already packetized; acceptance requires explicit review/assurance rather than another search.",
        "next_system_action": "review_high_priority_evidence_packets_and_record_accept_or_reject_decisions",
    },
    "official_profile_search": {
        "execution_lane": "new_or_extended_collector_required",
        "automation_status": "trainee_profile_collector_missing",
        "existing_collector": "scripts/enrich_penn_attending_profiles.py (attending-oriented only)",
        "command_hint": "extend profile discovery/collection to trainee profiles using official roster profile links and Penn/CHOP profile search targets",
        "input_artifacts": [
            "artifacts/data/person_enrichment_queue.csv",
            "artifacts/data/penn_profile_index.md",
        ],
        "output_artifacts": [
            "artifacts/data/trainee_profile_claims.csv",
            "artifacts/data/person_contacts.csv",
            "artifacts/data/evidence_claims.csv",
        ],
        "requires_network": 1,
        "requires_manual_review": 0,
        "requires_script_extension": 1,
        "requires_new_parser": 1,
        "readiness_reason": "Profile search is high-value for identity/background/contact enrichment, but the current profile collector is aimed at attendings, not trainees.",
        "next_system_action": "build_official_trainee_profile_discovery_and_parser",
    },
    "organization_alias_review": {
        "execution_lane": "collector_then_manual_normalization",
        "automation_status": "collector_available_review_required",
        "existing_collector": "scripts/discover_organization_identifier_candidates.py",
        "command_hint": "python3 scripts/discover_organization_identifier_candidates.py --limit 200 --min-mentions 2 --candidates-per-org 3 --sleep 0.05",
        "input_artifacts": [
            "artifacts/data/organization_review_queue.csv",
            "artifacts/data/organization_identifier_candidates.csv",
        ],
        "output_artifacts": [
            "artifacts/data/organization_identifier_candidates.csv",
            "artifacts/data/organization_identifier_source_observations.csv",
        ],
        "requires_network": 1,
        "requires_manual_review": 1,
        "requires_script_extension": 0,
        "requires_new_parser": 0,
        "readiness_reason": "ROR candidate collection exists, but alias collapse still needs review to avoid merging schools, hospitals, programs, and campuses incorrectly.",
        "next_system_action": "run_identifier_candidate_collection_then_review_alias_collapses",
    },
    "research_identity_search": {
        "execution_lane": "collector_available_with_role_gap",
        "automation_status": "collector_available_partial_role_coverage",
        "existing_collector": "scripts/collect_research_candidates.py",
        "command_hint": "python3 scripts/collect_research_candidates.py --skip-existing-source pubmed_eutilities --sleep 0.34",
        "input_artifacts": [
            "artifacts/data/person_enrichment_queue.csv",
            "artifacts/data/research_candidate_claims.json",
        ],
        "output_artifacts": [
            "artifacts/data/research_candidate_claims.json",
            "artifacts/data/research_candidate_summary.json",
            "artifacts/data/evidence_claims.csv",
        ],
        "requires_network": 1,
        "requires_manual_review": 1,
        "requires_script_extension": 1,
        "requires_new_parser": 0,
        "readiness_reason": "PubMed/OpenAlex collection exists for residents/fellows; queue-driven execution and medical-student coverage still need script extension.",
        "next_system_action": "extend_research_collector_to_queue_and_medical_students_then_run_candidate_collection",
    },
    "source_medical_school_background": {
        "execution_lane": "source_search_then_review",
        "automation_status": "general_search_required_no_dedicated_collector",
        "existing_collector": "none",
        "command_hint": "build prior-training profile/CV collector from official profile, alumni roster, and conference-bio candidates",
        "input_artifacts": [
            "artifacts/data/person_enrichment_queue.csv",
            "artifacts/data/person_enrichment_coverage.csv",
        ],
        "output_artifacts": [
            "artifacts/data/evidence_claims.csv",
            "artifacts/data/person_training_events.csv",
        ],
        "requires_network": 1,
        "requires_manual_review": 1,
        "requires_script_extension": 1,
        "requires_new_parser": 1,
        "readiness_reason": "Medical-school background is missing for a small but important tail; current extraction depends on roster/profile fields and lacks a broad prior-training collector.",
        "next_system_action": "build_prior_training_source_collector_and_review_candidate_background_claims",
    },
    "source_residency_background": {
        "execution_lane": "source_search_then_review",
        "automation_status": "general_search_required_no_dedicated_collector",
        "existing_collector": "none",
        "command_hint": "build prior-GME profile/CV collector from official profile, alumni roster, and conference-bio candidates",
        "input_artifacts": [
            "artifacts/data/person_enrichment_queue.csv",
            "artifacts/data/person_enrichment_coverage.csv",
        ],
        "output_artifacts": [
            "artifacts/data/evidence_claims.csv",
            "artifacts/data/person_training_events.csv",
        ],
        "requires_network": 1,
        "requires_manual_review": 1,
        "requires_script_extension": 1,
        "requires_new_parser": 1,
        "readiness_reason": "Fellow prior-residency background is source-backed for many people, but the remaining gap has no dedicated public prior-GME collector.",
        "next_system_action": "build_prior_gme_source_collector_and_review_candidate_background_claims",
    },
    "public_contact_verification": {
        "execution_lane": "dependent_on_roster_or_profile_refresh",
        "automation_status": "collector_available_only_when_source_exposes_contact",
        "existing_collector": "scripts/scrape_penn_training.py; scripts/scrape_penn_affiliated_rosters.py; future trainee profile collector",
        "command_hint": "refresh official roster/profile sources and run scripts/audit_contact_assurance.py",
        "input_artifacts": [
            "artifacts/data/person_contacts.csv",
            "artifacts/data/contact_assurance_audit.csv",
        ],
        "output_artifacts": [
            "artifacts/data/person_contacts.csv",
            "artifacts/data/contact_assurance_audit.csv",
        ],
        "requires_network": 1,
        "requires_manual_review": 1,
        "requires_script_extension": 0,
        "requires_new_parser": 0,
        "readiness_reason": "Contact evidence can be harvested from official rosters/profiles when displayed, but contact values are stale-prone and require assurance before display/use.",
        "next_system_action": "refresh_public_contact_sources_and_reaudit_display_safety",
    },
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def key_for(prefix: str, parts: list[str]) -> str:
    return f"{prefix}_{sha256_text(dumps(parts))[:20]}"


def read_queue(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT task_key, person_key, display_name, role, program_name,
                   task_type, source_family, priority, priority_band,
                   policy_lane, diff_readiness_status, stale_by_refresh,
                   fresh_observation_required, evidence_json
            FROM person_enrichment_work_queue
            ORDER BY priority DESC, role, display_name, task_type
            """
        )
    ]


def existing_rows(path: Path, key_field: str) -> dict[str, dict]:
    if not path.exists():
        return {}
    with path.open(newline="", encoding="utf-8") as handle:
        return {row[key_field]: row for row in csv.DictReader(handle) if row.get(key_field)}


def stable_generated_at(existing: dict[str, dict], key_field: str, row: dict, new_value: str, fields: list[str]) -> str:
    prior = existing.get(row[key_field])
    if not prior:
        return new_value
    for field in fields:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return new_value
    return prior.get("generated_at") or new_value


def batch_key_for(row: dict, config: dict) -> str:
    return key_for(
        "enrichment_batch",
        [
            row.get("task_type") or "",
            row.get("source_family") or "",
            config["execution_lane"],
            config["automation_status"],
            row.get("priority_band") or "",
        ],
    )


def readiness_rows(queue: list[dict]) -> list[dict]:
    ranks: Counter[str] = Counter()
    rows = []
    for task in queue:
        config = TASK_EXECUTION[task["task_type"]]
        batch_key = batch_key_for(task, config)
        ranks[batch_key] += 1
        requires_manual_review = int(config["requires_manual_review"])
        if task["task_type"] == "current_roster_state_reconciliation" and task.get("policy_lane") == "manual_review_required":
            requires_manual_review = 1
        requires_script_extension = int(config["requires_script_extension"])
        if task["task_type"] == "research_identity_search" and task.get("role") != "medical_student":
            requires_script_extension = 0
        evidence = {
            "queue_task": {
                "task_key": task["task_key"],
                "policy_lane": task.get("policy_lane") or "",
                "diff_readiness_status": task.get("diff_readiness_status") or "",
                "stale_by_refresh": int(task.get("stale_by_refresh") or 0),
                "fresh_observation_required": int(task.get("fresh_observation_required") or 0),
                "queue_evidence": json.loads(task.get("evidence_json") or "{}"),
            },
            "execution_config": {
                key: config[key]
                for key in [
                    "execution_lane",
                    "automation_status",
                    "existing_collector",
                    "requires_network",
                    "requires_manual_review",
                    "requires_script_extension",
                    "requires_new_parser",
                ]
            },
        }
        rows.append(
            {
                "readiness_key": key_for("person_enrichment_readiness", [task["task_key"]]),
                "task_key": task["task_key"],
                "person_key": task["person_key"],
                "display_name": task["display_name"],
                "role": task.get("role") or "",
                "program_name": task.get("program_name") or "",
                "task_type": task["task_type"],
                "source_family": task["source_family"],
                "priority": int(task.get("priority") or 0),
                "priority_band": task.get("priority_band") or "",
                "execution_lane": config["execution_lane"],
                "automation_status": config["automation_status"],
                "existing_collector": config["existing_collector"],
                "command_hint": config["command_hint"],
                "input_artifacts_json": dumps(config["input_artifacts"]),
                "output_artifacts_json": dumps(config["output_artifacts"]),
                "requires_network": int(config["requires_network"]),
                "requires_manual_review": requires_manual_review,
                "requires_script_extension": requires_script_extension,
                "requires_new_parser": int(config["requires_new_parser"]),
                "batch_key": batch_key,
                "batch_rank": ranks[batch_key],
                "readiness_reason": config["readiness_reason"],
                "next_system_action": config["next_system_action"],
                "evidence_json": dumps(evidence),
                "generated_at": "",
            }
        )
    return rows


def rollup_rows(rows: list[dict]) -> list[dict]:
    scopes: list[tuple[str, str, list[str]]] = [
        ("task_type", "", ["task_type"]),
        ("source_family", "", ["source_family"]),
        ("execution_lane", "", ["execution_lane"]),
        ("automation_status", "", ["automation_status"]),
        ("priority_band", "", ["priority_band"]),
        ("task_type_execution_lane", "", ["task_type", "execution_lane"]),
    ]
    grouped: dict[tuple[str, str, tuple[str, ...]], list[dict]] = defaultdict(list)
    for row in rows:
        for scope, _, fields in scopes:
            values = tuple(row[field] for field in fields)
            grouped[(scope, " / ".join(values), values)].append(row)
    output = []
    for (scope, value, values), grouped_rows in grouped.items():
        commands = Counter(row["command_hint"] for row in grouped_rows)
        actions = Counter(row["next_system_action"] for row in grouped_rows)
        first = grouped_rows[0]
        output.append(
            {
                "rollup_key": key_for("enrichment_readiness_rollup", [scope, value]),
                "rollup_scope": scope,
                "rollup_value": value,
                "task_type": first["task_type"] if "task_type" in scope else "",
                "source_family": first["source_family"] if scope == "source_family" else "",
                "priority_band": first["priority_band"] if scope == "priority_band" else "",
                "execution_lane": first["execution_lane"] if "execution_lane" in scope else "",
                "automation_status": first["automation_status"] if scope == "automation_status" else "",
                "task_count": len(grouped_rows),
                "person_count": len({row["person_key"] for row in grouped_rows}),
                "critical_task_count": sum(1 for row in grouped_rows if row["priority_band"] == "critical"),
                "network_required_count": sum(int(row["requires_network"]) for row in grouped_rows),
                "manual_review_required_count": sum(int(row["requires_manual_review"]) for row in grouped_rows),
                "script_extension_required_count": sum(int(row["requires_script_extension"]) for row in grouped_rows),
                "new_parser_required_count": sum(int(row["requires_new_parser"]) for row in grouped_rows),
                "top_command_hint": commands.most_common(1)[0][0],
                "next_system_action": actions.most_common(1)[0][0],
                "evidence_json": dumps(
                    {
                        "by_priority_band": dict(Counter(row["priority_band"] for row in grouped_rows)),
                        "by_task_type": dict(Counter(row["task_type"] for row in grouped_rows)),
                        "by_execution_lane": dict(Counter(row["execution_lane"] for row in grouped_rows)),
                        "by_automation_status": dict(Counter(row["automation_status"] for row in grouped_rows)),
                    }
                ),
                "generated_at": "",
            }
        )
    return sorted(output, key=lambda row: (row["rollup_scope"], -int(row["task_count"]), row["rollup_value"]))


def apply_stable_timestamps(rows: list[dict], rollups: list[dict]) -> None:
    generated_at = now_utc()
    existing_readiness = existing_rows(CSV_PATH, "readiness_key")
    existing_rollups = existing_rows(ROLLUP_CSV_PATH, "rollup_key")
    for row in rows:
        row["generated_at"] = stable_generated_at(
            existing_readiness,
            "readiness_key",
            row,
            generated_at,
            READINESS_FIELDS,
        )
    for row in rollups:
        row["generated_at"] = stable_generated_at(
            existing_rollups,
            "rollup_key",
            row,
            generated_at,
            ROLLUP_FIELDS,
        )


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db_table(conn: sqlite3.Connection, table: str, rows: list[dict], fields: list[str]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(f"DELETE FROM {table}")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in fields)
    column_sql = ", ".join(fields)
    conn.executemany(
        f"INSERT INTO {table} ({column_sql}) VALUES ({placeholders})",
        [{field: row.get(field, "") for field in fields} for row in rows],
    )


def summary(rows: list[dict], rollups: list[dict]) -> dict:
    return {
        "readiness_rows": len(rows),
        "rollup_rows": len(rollups),
        "person_count": len({row["person_key"] for row in rows}),
        "by_execution_lane": dict(sorted(Counter(row["execution_lane"] for row in rows).items())),
        "by_automation_status": dict(sorted(Counter(row["automation_status"] for row in rows).items())),
        "by_task_type": dict(sorted(Counter(row["task_type"] for row in rows).items())),
        "by_priority_band": dict(sorted(Counter(row["priority_band"] for row in rows).items())),
        "network_required_tasks": sum(int(row["requires_network"]) for row in rows),
        "manual_review_required_tasks": sum(int(row["requires_manual_review"]) for row in rows),
        "script_extension_required_tasks": sum(int(row["requires_script_extension"]) for row in rows),
        "new_parser_required_tasks": sum(int(row["requires_new_parser"]) for row in rows),
        "top_next_system_actions": dict(Counter(row["next_system_action"] for row in rows).most_common(10)),
        "readiness_csv": str(CSV_PATH.relative_to(ROOT)),
        "readiness_json": str(JSON_PATH.relative_to(ROOT)),
        "rollup_csv": str(ROLLUP_CSV_PATH.relative_to(ROOT)),
        "rollup_json": str(ROLLUP_JSON_PATH.relative_to(ROOT)),
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    with conn:
        queue = read_queue(conn)
        rows = readiness_rows(queue)
        rollups = rollup_rows(rows)
        apply_stable_timestamps(rows, rollups)
        write_db_table(conn, "person_enrichment_execution_readiness", rows, READINESS_FIELDS)
        write_db_table(conn, "person_enrichment_execution_readiness_rollups", rollups, ROLLUP_FIELDS)
    conn.close()

    write_csv(CSV_PATH, rows, READINESS_FIELDS)
    write_csv(ROLLUP_CSV_PATH, rollups, ROLLUP_FIELDS)
    JSON_PATH.write_text(json.dumps(rows, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    ROLLUP_JSON_PATH.write_text(json.dumps(rollups, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    payload = summary(rows, rollups)
    SUMMARY_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
