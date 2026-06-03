#!/usr/bin/env python3
"""Materialize source-quality policy recommendations from utility evidence.

The scorecard says how each source utility performed. This ledger makes the
policy consequence explicit: whether a utility can anchor truth, seed review,
drive a collector batch, or only inform source-quality learning.
"""

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

SCORECARD_CSV = ARTIFACTS / "source_utility_scorecard.csv"
SEARCH_ASSURANCE_CSV = ARTIFACTS / "search_utility_assurance.csv"
CSV_OUT = ARTIFACTS / "source_quality_policy_recommendations.csv"
JSON_OUT = ARTIFACTS / "source_quality_policy_recommendations.json"
SUMMARY_OUT = ARTIFACTS / "source_quality_policy_recommendation_summary.json"

csv.field_size_limit(sys.maxsize)

FIELDS = [
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
    "acceptance_posture",
    "collector_posture",
    "reviewer_posture",
    "trend_relevance",
    "evidence_standard",
    "required_next_evidence",
    "recommended_next_action",
    "source_artifacts_json",
    "downstream_tables_json",
    "scorecard_evidence_json",
    "search_assurance_evidence_json",
    "generated_at",
]


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def stable_key(*parts: object) -> str:
    text = "||".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:20]


def existing_rows() -> dict[str, dict]:
    return {row["recommendation_key"]: row for row in read_csv(CSV_OUT) if row.get("recommendation_key")}


def stable_generated_at(existing: dict[str, dict], row: dict, generated_at: str) -> str:
    prior = existing.get(row["recommendation_key"])
    if not prior:
        return generated_at
    comparable = {field: row.get(field, "") for field in FIELDS if field != "generated_at"}
    prior_comparable = {field: prior.get(field, "") for field in FIELDS if field != "generated_at"}
    return prior.get("generated_at") or generated_at if comparable == prior_comparable else generated_at


def scorecard_policy(row: dict) -> dict[str, str | int]:
    quality = row.get("quality_band") or ""
    action = row.get("recommended_next_action") or ""
    family = row.get("source_family") or ""
    claim_surface = (row.get("claim_surface") or "").lower()
    needs_review = as_int(row.get("needs_review_records"))
    review_ready = as_int(row.get("review_ready_records"))
    discovery = as_int(row.get("discovery_only_records"))
    blocked = as_int(row.get("blocked_records"))
    low_signal = as_int(row.get("low_signal_records"))
    coverage_gap = as_int(row.get("coverage_gap_records"))
    candidate = as_int(row.get("candidate_records"))

    if quality == "high_utility":
        lane = "truth_anchor_governance"
        status = "usable_with_refresh_or_denominator_guardrails"
        acceptance = "can_anchor_truth_only_on_claim_surfaces_explicitly_marked_accepted"
        collector = "keep_on_refresh_clock"
        reviewer = "review_denominator_alias_or_drift_exceptions"
        evidence = "fresh official source observation plus source-specific lifecycle, denominator, or transition audit."
        priority = 460 + min(coverage_gap + blocked + needs_review, 300)
    elif quality == "strong_with_known_limits":
        lane = "strong_candidate_governance"
        status = "useful_but_requires_surface_specific_acceptance_gate"
        acceptance = "review_or_accept_only_through_source_specific_reviewer_and_acceptance_ledgers"
        collector = "run targeted refresh or discovery where gaps are enumerated"
        reviewer = "prioritize review-ready rows and display-safety constraints"
        evidence = "same-person/source-scope evidence, current source reobservation, and matching reviewer or acceptance fingerprint."
        priority = 620 + min(review_ready + needs_review + blocked, 300)
    elif quality == "useful_candidate_layer":
        lane = "candidate_reconciliation_policy"
        status = "candidate_evidence_requires_non_name_anchor_or_reviewer_decision"
        acceptance = "do_not_mutate_person_truth_without_independent_anchor"
        collector = "route exact identifiers or high-yield candidates to corroborating collectors"
        reviewer = "review only bounded packets with current fingerprints"
        evidence = "independent non-name anchor, exact identifier bridge, or reviewer decision tied to current packet evidence."
        priority = 700 + min(needs_review + candidate + review_ready, 300)
    elif quality == "discovery_or_review_only":
        lane = "discovery_execution_policy"
        status = "discovery_signal_not_acceptance_evidence"
        acceptance = "never_accept_directly_from_discovery_result"
        collector = "execute_or_probe_candidates_before_reconciliation"
        reviewer = "review only after candidate page/source content is probed"
        evidence = "query or candidate provenance, fetch observation, content hash, and source-specific reconciliation row."
        priority = 680 + min(discovery + low_signal + blocked + candidate, 300)
    else:
        lane = "source_quality_review"
        status = "policy_requires_manual_interpretation"
        acceptance = "hold_acceptance_until_policy_lane_is_classified"
        collector = "inspect source utility evidence before execution"
        reviewer = "review source utility limitations before fact review"
        evidence = "source utility scorecard evidence and explicit downstream acceptance boundary."
        priority = 520 + min(needs_review + candidate + blocked, 300)

    if "attending" in claim_surface or "attending" in action or "attending" in family:
        trend = "directly_relevant_to_recent_attending_trend_path"
        priority += 80
    elif "profile" in claim_surface or "training" in claim_surface or "education" in claim_surface:
        trend = "indirect_trend_or_background_context"
        priority += 20
    else:
        trend = "not_primary_trend_surface"

    if blocked or low_signal:
        readiness = "blocked_or_low_signal_until_next_evidence"
    elif review_ready or needs_review:
        readiness = "review_ready_or_review_bound"
    elif discovery or candidate:
        readiness = "collector_or_probe_ready"
    else:
        readiness = "monitor_or_refresh_ready"

    required_next = {
        "truth_anchor_governance": "Refresh official source or resolve denominator/lifecycle exceptions before mutating downstream truth.",
        "strong_candidate_governance": "Record source-specific reviewer or acceptance-ledger evidence before promoting candidate facts.",
        "candidate_reconciliation_policy": "Collect independent identity/context anchors or reviewer decisions before acceptance.",
        "discovery_execution_policy": "Execute/probe discovery candidates and route fetched evidence through reconciliation ledgers.",
        "source_quality_review": "Classify the source utility policy before using it in acceptance or display logic.",
    }[lane]

    return {
        "policy_lane": lane,
        "policy_status": status,
        "action_priority": min(priority, 1100),
        "action_readiness": readiness,
        "acceptance_posture": acceptance,
        "collector_posture": collector,
        "reviewer_posture": reviewer,
        "trend_relevance": trend,
        "evidence_standard": evidence,
        "required_next_evidence": required_next,
    }


def search_policy(row: dict) -> dict[str, str | int]:
    status = row.get("search_execution_status") or ""
    query_rows = as_int(row.get("query_rows"))
    unexecuted = max(query_rows - as_int(row.get("search_observation_rows")), 0)
    non_200 = as_int(row.get("non_200_search_rows"))
    candidates = as_int(row.get("search_candidate_rows"))
    utility_family = row.get("utility_family") or ""

    if status in {"planned_not_executed", "no_query_manifest"}:
        lane = "search_observation_required"
        policy_status = "query_plan_is_not_absence_evidence"
        readiness = "search_execution_needed"
        priority = 760 + min(unexecuted or query_rows, 260)
        evidence = "completed search observations, provider/status metadata, and query manifest provenance."
    elif status in {"executed_blocked_by_search_endpoint", "executed_partial_with_endpoint_errors"}:
        lane = "search_endpoint_reliability_policy"
        policy_status = "endpoint_errors_limit_source_quality_confidence"
        readiness = "retry_or_provider_swap_needed"
        priority = 740 + min(non_200 + unexecuted, 260)
        evidence = "retry observations or alternate-provider observations preserving HTTP status/error provenance."
    elif candidates:
        lane = "search_candidate_probe_policy"
        policy_status = "candidates_require_fetch_probe_before_reconciliation"
        readiness = "candidate_probe_ready"
        priority = 660 + min(candidates, 260)
        evidence = "candidate page fetch status, content hash, source title, and source-specific match context."
    else:
        lane = "search_absence_weak_signal_policy"
        policy_status = "no_result_search_is_weak_absence_evidence"
        readiness = "monitor_or_crosscheck_ready"
        priority = 420 + min(query_rows, 160)
        evidence = "query coverage, source-scope review, and refreshed official/candidate source checks."

    trend = (
        "directly_relevant_to_recent_attending_trend_path"
        if "attending" in utility_family or "attending" in (row.get("utility_key") or "")
        else "not_primary_trend_surface"
    )

    return {
        "policy_lane": lane,
        "policy_status": policy_status,
        "action_priority": min(priority, 1050),
        "action_readiness": readiness,
        "acceptance_posture": "search_results_are_discovery_only_and_never_direct_acceptance_evidence",
        "collector_posture": "execute_search_retry_or_probe_candidates_with_provider_status_and_content_hashes",
        "reviewer_posture": "review_only_after_candidate_source_content_is_observed",
        "trend_relevance": trend,
        "evidence_standard": evidence,
        "required_next_evidence": "Search utility claims need observed queries or probed candidate sources before supporting coverage, enrichment, or trend conclusions.",
    }


def source_artifacts_for_scorecard(row: dict) -> list[str]:
    artifacts = ["artifacts/data/source_utility_scorecard.csv"]
    evidence = parse_json(row.get("evidence_json"), {})
    for key in ("csv", "accepted_mappings_csv", "accepted_facts_csv", "queue_csv", "audit_csv", "candidate_csv"):
        value = evidence.get(key)
        if isinstance(value, str) and value.startswith("artifacts/"):
            artifacts.append(value)
    for nested_key in ("summary", "discovery_summary", "coverage_action_queue_summary", "official_profile_reviewer_decision_summary"):
        nested = evidence.get(nested_key)
        if isinstance(nested, dict):
            for key in ("csv", "claims_json", "queue_csv", "audit_csv"):
                value = nested.get(key)
                if isinstance(value, str) and value.startswith("artifacts/"):
                    artifacts.append(value)
    return sorted(set(artifacts))


def build_scorecard_rows(search_by_key: dict[str, dict]) -> list[dict]:
    rows = []
    for item in read_csv(SCORECARD_CSV):
        policy = scorecard_policy(item)
        utility_key = item.get("utility_key") or item.get("scorecard_key") or ""
        search = search_by_key.get(utility_key, {})
        source_artifacts = source_artifacts_for_scorecard(item)
        if search:
            source_artifacts.extend(
                artifact
                for artifact in [
                    search.get("query_artifact"),
                    search.get("observation_artifact"),
                    search.get("candidate_artifact"),
                ]
                if artifact
            )
        downstream = [
            "source_utility_scorecard",
            "source_quality_policy_recommendations",
            "corpus_action_worklist",
        ]
        if item.get("source_family") == "scholarly_api":
            downstream.extend(["evidence_claims", "research_identity_corroboration", "enrichment_acceptance_audit"])
        if "attending" in (policy["trend_relevance"] or ""):
            downstream.extend(["attending_trend_reconciliation", "attending_trend_reviewer_decision_queue"])
        row = {
            "recommendation_key": "source_quality_policy_" + stable_key("scorecard", item.get("scorecard_key"), utility_key),
            "source_row_type": "source_utility_scorecard",
            "utility_key": utility_key,
            "utility_label": item.get("utility_label") or "",
            "source_family": item.get("source_family") or "",
            "claim_surface": item.get("claim_surface") or "",
            "score": round(as_float(item.get("score")), 3),
            "quality_band": item.get("quality_band") or "",
            "recommended_next_action": item.get("recommended_next_action") or "",
            "source_artifacts_json": dumps(sorted(set(source_artifacts))),
            "downstream_tables_json": dumps(sorted(set(downstream))),
            "scorecard_evidence_json": item.get("evidence_json") or "{}",
            "search_assurance_evidence_json": dumps(search) if search else "{}",
            "generated_at": "",
            **policy,
        }
        rows.append({field: row[field] for field in FIELDS})
    return rows


def build_search_only_rows(scorecard_utility_keys: set[str]) -> list[dict]:
    rows = []
    for item in read_csv(SEARCH_ASSURANCE_CSV):
        utility_key = item.get("utility_key") or ""
        if utility_key in scorecard_utility_keys:
            continue
        policy = search_policy(item)
        downstream = [
            "search_utility_assurance",
            "search_utility_execution_batches",
            "source_quality_policy_recommendations",
            "corpus_action_worklist",
        ]
        if policy["trend_relevance"] == "directly_relevant_to_recent_attending_trend_path":
            downstream.extend(["attending_historical_link_candidates", "attending_trend_discovery_workbench"])
        row = {
            "recommendation_key": "source_quality_policy_" + stable_key("search", utility_key),
            "source_row_type": "search_utility_assurance",
            "utility_key": utility_key,
            "utility_label": item.get("utility_name") or "",
            "source_family": item.get("utility_family") or "",
            "claim_surface": item.get("claim_surface") or "",
            "score": 0.0,
            "quality_band": "search_quality_observation",
            "recommended_next_action": item.get("recommended_next_action") or "",
            "source_artifacts_json": dumps(
                [
                    artifact
                    for artifact in [
                        "artifacts/data/search_utility_assurance.csv",
                        item.get("query_artifact") or "",
                        item.get("observation_artifact") or "",
                        item.get("candidate_artifact") or "",
                    ]
                    if artifact
                ]
            ),
            "downstream_tables_json": dumps(sorted(set(downstream))),
            "scorecard_evidence_json": "{}",
            "search_assurance_evidence_json": dumps(item),
            "generated_at": "",
            **policy,
        }
        rows.append({field: row[field] for field in FIELDS})
    return rows


def build_rows() -> list[dict]:
    search_rows = read_csv(SEARCH_ASSURANCE_CSV)
    search_by_key = {row.get("utility_key") or "": row for row in search_rows}
    scorecard_rows = read_csv(SCORECARD_CSV)
    scorecard_utility_keys = {row.get("utility_key") or "" for row in scorecard_rows}
    rows = build_scorecard_rows(search_by_key) + build_search_only_rows(scorecard_utility_keys)
    rows.sort(key=lambda row: (-as_int(row["action_priority"]), row["policy_lane"], row["utility_label"]))
    existing = existing_rows()
    generated_at = now_utc()
    for row in rows:
        row["generated_at"] = stable_generated_at(existing, row, generated_at)
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
        conn.execute("DELETE FROM source_quality_policy_recommendations")
        placeholders = ", ".join(f":{field}" for field in FIELDS)
        fields = ", ".join(FIELDS)
        conn.executemany(
            f"INSERT OR REPLACE INTO source_quality_policy_recommendations ({fields}) VALUES ({placeholders})",
            rows,
        )
    conn.close()


def write_summary(rows: list[dict]) -> None:
    payload = {
        "generated_at": max((row["generated_at"] for row in rows), default=now_utc()),
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "recommendation_rows": len(rows),
        "by_source_row_type": dict(sorted(Counter(row["source_row_type"] for row in rows).items())),
        "by_quality_band": dict(sorted(Counter(row["quality_band"] for row in rows).items())),
        "by_policy_lane": dict(sorted(Counter(row["policy_lane"] for row in rows).items())),
        "by_action_readiness": dict(sorted(Counter(row["action_readiness"] for row in rows).items())),
        "by_trend_relevance": dict(sorted(Counter(row["trend_relevance"] for row in rows).items())),
        "top_policy_rows": [
            {
                "utility_label": row["utility_label"],
                "policy_lane": row["policy_lane"],
                "action_priority": row["action_priority"],
                "action_readiness": row["action_readiness"],
                "trend_relevance": row["trend_relevance"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows[:15]
        ],
        "policy": (
            "Source-quality policy recommendations are non-mutating. They translate observed utility "
            "performance into acceptance, collector, reviewer, and trend-readiness posture; factual "
            "promotion still requires source-specific evidence and reviewer/acceptance ledgers."
        ),
    }
    SUMMARY_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows)
    print(dumps({"source_quality_policy_recommendations": len(rows)}))


if __name__ == "__main__":
    main()
