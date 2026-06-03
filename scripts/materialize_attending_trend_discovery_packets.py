#!/usr/bin/env python3
"""Materialize per-group packets for attending trend discovery work."""

from __future__ import annotations

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

CSV_OUT = ARTIFACTS / "attending_trend_discovery_packets.csv"
JSON_OUT = ARTIFACTS / "attending_trend_discovery_packets.json"
SUMMARY_OUT = ARTIFACTS / "attending_trend_discovery_packet_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
    "trend_discovery_packet_key",
    "attending_trend_discovery_batch_key",
    "batch_execution_order",
    "trend_workbench_key",
    "trend_key",
    "event_group_key",
    "display_name",
    "normalized_name",
    "discovery_lane",
    "trend_status",
    "dossier_status",
    "ten_year_trend_window",
    "packet_status",
    "packet_priority",
    "has_current_attending_endpoint",
    "has_penn_training_claim",
    "has_recent_dated_biosketch_bridge",
    "has_historical_link_candidate",
    "accepted_trend_fact_count",
    "review_claim_count",
    "reviewer_queue_count",
    "historical_query_count",
    "historical_search_observation_count",
    "historical_blocked_search_count",
    "historical_candidate_count",
    "actionable_historical_candidate_count",
    "current_profile_context_candidate_count",
    "best_candidate_status",
    "best_candidate_url",
    "best_candidate_domain",
    "best_candidate_title",
    "best_candidate_confidence",
    "best_candidate_priority",
    "required_next_evidence",
    "recommended_operator_action",
    "target_artifact",
    "acceptance_boundary",
    "source_urls",
    "reviewer_decision_keys",
    "claim_fingerprints",
    "query_bundle_json",
    "candidate_review_json",
    "reviewer_dossiers_json",
    "manual_action_template_json",
    "evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def parse_json(value: str | None, fallback):
    if not value:
        return fallback
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return fallback


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def existing_rows() -> dict[str, dict]:
    return {
        row["trend_discovery_packet_key"]: row
        for row in read_csv(CSV_OUT)
        if row.get("trend_discovery_packet_key")
    }


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["trend_discovery_packet_key"])
    if not prior:
        return generated_at
    for field in FIELDS:
        if field == "generated_at":
            continue
        if str(prior.get(field, "")) != str(row.get(field, "")):
            return generated_at
    return prior.get("generated_at") or generated_at


def packet_key(workbench_key: str) -> str:
    return "attending_trend_discovery_packet_" + sha256_text(workbench_key)[:20]


def packet_status(lane: str) -> str:
    return {
        "accepted_trend_fact_monitor": "accepted_trend_fact_monitor",
        "reviewer_decision_pending": "ready_for_trend_reviewer_decision",
        "historical_link_candidate_review": "ready_for_historical_candidate_review",
        "profile_claim_needs_dated_bridge_search": "ready_for_dated_bridge_search",
        "historical_search_endpoint_blocked_retry": "retry_search_endpoint_before_absence_inference",
        "current_endpoint_query_plan_missing": "missing_query_plan",
        "current_endpoint_training_bridge_search": "ready_for_training_bridge_search",
        "current_endpoint_context_candidate_review": "ready_for_context_candidate_review",
        "context_only_monitor": "context_only_monitor",
    }.get(lane, "trend_discovery_review_ready")


def target_artifact(lane: str) -> str:
    if lane == "reviewer_decision_pending":
        return "artifacts/data/attending_trend_reviewer_decisions.csv"
    if lane in {
        "historical_link_candidate_review",
        "current_endpoint_training_bridge_search",
        "profile_claim_needs_dated_bridge_search",
        "current_endpoint_context_candidate_review",
    }:
        return "artifacts/data/attending_historical_link_candidates.csv"
    if lane in {"historical_search_endpoint_blocked_retry", "current_endpoint_query_plan_missing"}:
        return "artifacts/data/attending_historical_link_search_observations.csv"
    return "artifacts/data/attending_trend_discovery_workbench.csv"


def recommended_action(lane: str) -> str:
    return {
        "accepted_trend_fact_monitor": "monitor_accepted_trend_fact_provenance",
        "reviewer_decision_pending": "record_attending_trend_reviewer_decision_with_current_claim_fingerprint",
        "historical_link_candidate_review": "review_historical_link_candidate_for_same_person_training_and_dates",
        "profile_claim_needs_dated_bridge_search": "search_for_dated_historical_roster_alumni_cv_or_biosketch_bridge",
        "historical_search_endpoint_blocked_retry": "retry_search_or_use_deterministic_official_domain_probe",
        "current_endpoint_query_plan_missing": "materialize_missing_attending_historical_link_queries",
        "current_endpoint_training_bridge_search": "collect_dated_training_bridge_for_current_endpoint",
        "current_endpoint_context_candidate_review": "review_context_candidate_then_collect_dated_bridge",
        "context_only_monitor": "keep_out_of_trend_counts_until_endpoint_and_training_bridge_exist",
    }.get(lane, "review_attending_trend_discovery_packet")


def acceptance_boundary() -> str:
    return (
        "Trend discovery packets are non-mutating. Current endpoint, search hit, profile context, or "
        "candidate page evidence does not become an accepted recent-attending trend fact until an explicit "
        "attending_trend_reviewer_decisions.csv row matches the current claim_fingerprint and confirms "
        "same-person identity, current Penn endpoint, Penn training line, and date window."
    )


def batch_membership(rows: list[dict]) -> dict[str, dict]:
    output = {}
    for batch in rows:
        evidence = parse_json(batch.get("evidence_json"), {})
        keys = evidence.get("trend_workbench_keys") if isinstance(evidence, dict) else []
        if not isinstance(keys, list):
            keys = []
        top_rows = {
            item.get("trend_workbench_key"): item
            for item in parse_json(batch.get("top_workbench_rows_json"), [])
            if isinstance(item, dict) and item.get("trend_workbench_key")
        }
        for key in keys:
            output[str(key)] = {
                "attending_trend_discovery_batch_key": batch.get("attending_trend_discovery_batch_key") or "",
                "batch_execution_order": as_int(batch.get("execution_order")),
                "batch_status": batch.get("batch_status") or "",
                "batch_recommended_operator_action": batch.get("recommended_operator_action") or "",
                "batch_required_next_evidence": batch.get("required_next_evidence") or "",
                "batch_top_row": top_rows.get(str(key), {}),
            }
    return output


def compact_queries(queries: list[dict], observations: list[dict]) -> dict:
    source = observations or queries
    status_counts = Counter()
    for row in observations:
        if not row.get("searched_at"):
            status = "planned_not_executed"
        elif as_int(row.get("search_http_status")) == 200 and as_int(row.get("result_count")) > 0:
            status = "executed_success_with_results"
        elif as_int(row.get("search_http_status")) == 200:
            status = "executed_success_no_results"
        elif row.get("search_http_status"):
            status = "executed_blocked_by_search_endpoint"
        else:
            status = "executed_unknown_status"
        status_counts[status] += 1
    if queries and not observations:
        status_counts["planned_not_executed"] = len(queries)
    return {
        "query_count": len(queries),
        "observation_count": len(observations),
        "status_counts": dict(sorted(status_counts.items())),
        "query_kind_counts": dict(sorted(Counter(row.get("query_kind") or "" for row in queries).items())),
        "sample_queries": [
            {
                "query_key": row.get("query_key"),
                "query_kind": row.get("query_kind"),
                "query": row.get("query"),
                "query_url": row.get("query_url"),
                "search_status": row.get("search_status"),
                "search_http_status": row.get("search_http_status"),
                "result_url": row.get("result_url"),
                "result_domain": row.get("result_domain"),
                "result_title": row.get("result_title"),
            }
            for row in source[:12]
        ],
    }


def compact_candidates(candidates: list[dict]) -> list[dict]:
    output = []
    for candidate in sorted(candidates, key=lambda item: (-as_int(item.get("priority")), item.get("result_url") or "")):
        output.append(
            {
                "candidate_key": candidate.get("candidate_key"),
                "candidate_status": candidate.get("candidate_status"),
                "confidence": as_float(candidate.get("confidence")),
                "priority": as_int(candidate.get("priority")),
                "result_url": candidate.get("result_url"),
                "result_domain": candidate.get("result_domain"),
                "result_title": candidate.get("result_title") or candidate.get("probe_title"),
                "search_status": candidate.get("search_status"),
                "search_http_status": candidate.get("search_http_status"),
                "probe_http_status": candidate.get("probe_http_status"),
                "page_term_hits": candidate.get("page_term_hits"),
                "classification_reasons": candidate.get("classification_reasons"),
                "required_next_evidence": candidate.get("required_next_evidence"),
            }
        )
    return output


def reviewer_dossier_payload(dossiers: list[dict]) -> list[dict]:
    output = []
    for dossier in dossiers:
        output.append(
            {
                "dossier_key": dossier.get("dossier_key"),
                "reviewer_decision_key": dossier.get("reviewer_decision_key"),
                "trend_claim_key": dossier.get("trend_claim_key"),
                "trend_acceptance_key": dossier.get("trend_acceptance_key"),
                "decision_status": dossier.get("decision_status"),
                "decision_blocker": dossier.get("decision_blocker"),
                "claim_fingerprint": dossier.get("claim_fingerprint"),
                "training_type": dossier.get("training_type"),
                "training_line": dossier.get("training_line"),
                "training_start_year": dossier.get("training_start_year"),
                "training_end_year": dossier.get("training_end_year"),
                "source_url": dossier.get("source_url"),
                "manual_decision_template": parse_json(dossier.get("manual_decision_template_json"), {}),
                "acceptance_boundary": dossier.get("acceptance_boundary"),
            }
        )
    return output


def manual_template(row: dict, dossiers: list[dict], candidates: list[dict], membership: dict) -> dict:
    lane = row.get("discovery_lane") or ""
    if lane == "reviewer_decision_pending" and dossiers:
        templates = [
            parse_json(dossier.get("manual_decision_template_json"), {})
            for dossier in dossiers
            if dossier.get("manual_decision_template_json")
        ]
        return {
            "packet_action": "record_attending_trend_reviewer_decision",
            "target_artifact": "artifacts/data/attending_trend_reviewer_decisions.csv",
            "decision_templates": templates,
        }
    if lane in {"historical_link_candidate_review", "current_endpoint_context_candidate_review"}:
        return {
            "packet_action": "review_historical_link_candidates",
            "target_artifact": "artifacts/data/attending_historical_link_candidates.csv",
            "event_group_key": row.get("event_group_key"),
            "candidate_reviews": [
                {
                    "candidate_key": candidate.get("candidate_key"),
                    "candidate_status": candidate.get("candidate_status"),
                    "result_url": candidate.get("result_url"),
                    "same_person_identity_confirmed": 0,
                    "current_endpoint_consistent": 0,
                    "penn_training_line_confirmed": 0,
                    "date_window_confirmed": 0,
                    "reviewer_notes": "",
                }
                for candidate in candidates[:10]
            ],
        }
    if "bridge_search" in lane or lane == "profile_claim_needs_dated_bridge_search":
        return {
            "packet_action": "collect_dated_training_bridge",
            "target_artifact": "artifacts/data/attending_historical_link_candidates.csv",
            "event_group_key": row.get("event_group_key"),
            "display_name": row.get("display_name"),
            "needed_evidence": row.get("evidence_required"),
            "suggested_batch_key": membership.get("attending_trend_discovery_batch_key", ""),
            "new_candidate_url": "",
            "candidate_source_type": "",
            "same_person_identity_anchor": "",
            "penn_training_line": "",
            "training_start_year": "",
            "training_end_year": "",
            "reviewer_notes": "",
        }
    return {
        "packet_action": "monitor_or_retain_context",
        "target_artifact": target_artifact(lane),
        "event_group_key": row.get("event_group_key"),
        "display_name": row.get("display_name"),
        "reviewer_notes": "",
    }


def build_rows() -> list[dict]:
    existing = existing_rows()
    generated_at = now_utc()
    workbench_rows = read_csv(ARTIFACTS / "attending_trend_discovery_workbench.csv")
    memberships = batch_membership(read_csv(ARTIFACTS / "attending_trend_discovery_batches.csv"))
    queries_by_group: dict[str, list[dict]] = defaultdict(list)
    observations_by_group: dict[str, list[dict]] = defaultdict(list)
    candidates_by_group: dict[str, list[dict]] = defaultdict(list)
    dossiers_by_trend: dict[str, list[dict]] = defaultdict(list)

    for row in read_csv(ARTIFACTS / "attending_historical_link_search_queries.csv"):
        queries_by_group[row.get("event_group_key") or ""].append(row)
    for row in read_csv(ARTIFACTS / "attending_historical_link_search_observations.csv"):
        observations_by_group[row.get("event_group_key") or ""].append(row)
    for row in read_csv(ARTIFACTS / "attending_historical_link_candidates.csv"):
        candidates_by_group[row.get("event_group_key") or ""].append(row)
    for row in read_csv(ARTIFACTS / "attending_trend_reviewer_decision_dossiers.csv"):
        dossiers_by_trend[row.get("trend_key") or ""].append(row)

    rows = []
    for workbench in workbench_rows:
        workbench_key = workbench.get("trend_workbench_key") or ""
        group_key = workbench.get("event_group_key") or ""
        trend_key = workbench.get("trend_key") or ""
        membership = memberships.get(workbench_key, {})
        queries = queries_by_group.get(group_key, [])
        observations = observations_by_group.get(group_key, [])
        candidates = compact_candidates(candidates_by_group.get(group_key, []))
        dossiers = dossiers_by_trend.get(trend_key, [])
        lane = workbench.get("discovery_lane") or ""
        reviewer_payload = reviewer_dossier_payload(dossiers)
        row = {
            "trend_discovery_packet_key": packet_key(workbench_key),
            "attending_trend_discovery_batch_key": membership.get("attending_trend_discovery_batch_key", ""),
            "batch_execution_order": as_int(membership.get("batch_execution_order")),
            "trend_workbench_key": workbench_key,
            "trend_key": trend_key,
            "event_group_key": group_key,
            "display_name": workbench.get("display_name") or "",
            "normalized_name": workbench.get("normalized_name") or "",
            "discovery_lane": lane,
            "trend_status": workbench.get("trend_status") or "",
            "dossier_status": workbench.get("dossier_status") or "",
            "ten_year_trend_window": workbench.get("ten_year_trend_window") or "unknown",
            "packet_status": packet_status(lane),
            "packet_priority": as_int(workbench.get("discovery_priority")),
            "has_current_attending_endpoint": as_int(workbench.get("has_current_attending_endpoint")),
            "has_penn_training_claim": as_int(workbench.get("has_penn_training_claim")),
            "has_recent_dated_biosketch_bridge": as_int(workbench.get("has_recent_dated_biosketch_bridge")),
            "has_historical_link_candidate": as_int(workbench.get("has_historical_link_candidate")),
            "accepted_trend_fact_count": as_int(workbench.get("accepted_trend_fact_count")),
            "review_claim_count": as_int(workbench.get("review_claim_count")),
            "reviewer_queue_count": as_int(workbench.get("reviewer_queue_count")),
            "historical_query_count": as_int(workbench.get("historical_query_count")),
            "historical_search_observation_count": as_int(workbench.get("historical_search_observation_count")),
            "historical_blocked_search_count": as_int(workbench.get("historical_blocked_search_count")),
            "historical_candidate_count": as_int(workbench.get("historical_candidate_count")),
            "actionable_historical_candidate_count": as_int(workbench.get("actionable_historical_candidate_count")),
            "current_profile_context_candidate_count": as_int(workbench.get("current_profile_context_candidate_count")),
            "best_candidate_status": workbench.get("best_candidate_status") or "",
            "best_candidate_url": workbench.get("best_candidate_url") or "",
            "best_candidate_domain": workbench.get("best_candidate_domain") or "",
            "best_candidate_title": workbench.get("best_candidate_title") or "",
            "best_candidate_confidence": as_float(workbench.get("best_candidate_confidence")),
            "best_candidate_priority": as_int(workbench.get("best_candidate_priority")),
            "required_next_evidence": workbench.get("evidence_required") or membership.get("batch_required_next_evidence", ""),
            "recommended_operator_action": recommended_action(lane),
            "target_artifact": target_artifact(lane),
            "acceptance_boundary": acceptance_boundary(),
            "source_urls": workbench.get("source_urls") or "",
            "reviewer_decision_keys": "; ".join(
                dossier.get("reviewer_decision_key") or "" for dossier in dossiers if dossier.get("reviewer_decision_key")
            ),
            "claim_fingerprints": "; ".join(
                dossier.get("claim_fingerprint") or "" for dossier in dossiers if dossier.get("claim_fingerprint")
            ),
            "query_bundle_json": dumps(compact_queries(queries, observations)),
            "candidate_review_json": dumps(candidates),
            "reviewer_dossiers_json": dumps(reviewer_payload),
            "manual_action_template_json": dumps(manual_template(workbench, dossiers, candidates, membership)),
            "evidence_json": dumps(
                {
                    "workbench_row": workbench,
                    "batch_membership": membership,
                    "policy": {
                        "non_mutating": True,
                        "endpoint_only_rows_do_not_count_as_trend_facts": True,
                        "search_candidates_are_discovery_only": True,
                        "accepted_trend_fact_requires_explicit_reviewer_decision": True,
                    },
                }
            ),
            "generated_at": "",
        }
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
        rows.append({field: row[field] for field in FIELDS})

    rows.sort(
        key=lambda item: (
            -as_int(item["packet_priority"]),
            as_int(item["batch_execution_order"]),
            item["display_name"],
            item["trend_discovery_packet_key"],
        )
    )
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
        conn.execute("DELETE FROM attending_trend_discovery_packets")
        if rows:
            fields = ", ".join(FIELDS)
            placeholders = ", ".join(f":{field}" for field in FIELDS)
            conn.executemany(
                f"INSERT OR REPLACE INTO attending_trend_discovery_packets ({fields}) VALUES ({placeholders})",
                rows,
            )
    conn.close()


def write_summary(rows: list[dict]) -> None:
    generated_at = max((row["generated_at"] for row in rows), default=now_utc())
    payload = {
        "generated_at": generated_at,
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "packet_rows": len(rows),
        "person_count": len({row["trend_key"] for row in rows}),
        "batch_count": len({row["attending_trend_discovery_batch_key"] for row in rows if row["attending_trend_discovery_batch_key"]}),
        "reviewer_decision_packet_rows": sum(1 for row in rows if row["packet_status"] == "ready_for_trend_reviewer_decision"),
        "historical_candidate_packet_rows": sum(
            1 for row in rows if row["packet_status"] == "ready_for_historical_candidate_review"
        ),
        "training_bridge_search_packet_rows": sum(
            1 for row in rows if row["packet_status"] == "ready_for_training_bridge_search"
        ),
        "accepted_monitor_packet_rows": sum(1 for row in rows if row["packet_status"] == "accepted_trend_fact_monitor"),
        "context_monitor_packet_rows": sum(1 for row in rows if row["packet_status"] == "context_only_monitor"),
        "historical_query_count": sum(as_int(row["historical_query_count"]) for row in rows),
        "historical_candidate_count": sum(as_int(row["historical_candidate_count"]) for row in rows),
        "actionable_historical_candidate_count": sum(as_int(row["actionable_historical_candidate_count"]) for row in rows),
        "by_discovery_lane": dict(sorted(Counter(row["discovery_lane"] for row in rows).items())),
        "by_packet_status": dict(sorted(Counter(row["packet_status"] for row in rows).items())),
        "by_ten_year_trend_window": dict(sorted(Counter(row["ten_year_trend_window"] for row in rows).items())),
        "top_packets": [
            {
                "display_name": row["display_name"],
                "discovery_lane": row["discovery_lane"],
                "packet_status": row["packet_status"],
                "packet_priority": row["packet_priority"],
                "ten_year_trend_window": row["ten_year_trend_window"],
                "historical_candidate_count": row["historical_candidate_count"],
                "target_artifact": row["target_artifact"],
                "recommended_operator_action": row["recommended_operator_action"],
            }
            for row in rows[:25]
        ],
        "policy": "Attending trend discovery packets are non-mutating per-group work surfaces. They expose reviewer, search, and candidate evidence; accepted trend facts still require reviewer decision and acceptance audit ledgers.",
    }
    SUMMARY_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows)
    print(dumps({"attending_trend_discovery_packets": len(rows)}))


if __name__ == "__main__":
    main()
