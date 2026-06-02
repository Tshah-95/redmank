#!/usr/bin/env python3
"""Generate and optionally execute prior-training background searches."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, urlparse


DEPS_PATH = Path(os.environ.get("PENN_CORPUS_DEPS", "/tmp/penn_corpus_deps"))
if DEPS_PATH.exists():
    sys.path.insert(0, str(DEPS_PATH))
sys.path.insert(0, str(Path(__file__).resolve().parent))

try:
    import requests
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing scraper dependency. Install with: "
        "python3 -m pip install --target /tmp/penn_corpus_deps -r requirements.txt"
    ) from exc

from discover_trainee_official_profiles import (  # noqa: E402
    DDG_HTML,
    clean_name,
    ddg_results,
    dumps,
    key_for,
    name_present,
    norm,
    official_domain,
    probe_page,
)


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"

QUERY_CSV = ARTIFACTS / "prior_training_search_queries.csv"
OBSERVATION_CSV = ARTIFACTS / "prior_training_search_observations.csv"
CANDIDATE_CSV = ARTIFACTS / "prior_training_discovery_candidates.csv"
CLAIMS_JSON = ARTIFACTS / "prior_training_discovery_claims.json"
SOURCES_JSON = ARTIFACTS / "prior_training_discovery_sources.json"
SUMMARY_JSON = ARTIFACTS / "prior_training_discovery_summary.json"

TASKS = {"source_medical_school_background", "source_residency_background"}
BACKGROUND_TERMS = {
    "source_medical_school_background": [
        "medical school",
        "md",
        "doctor of medicine",
        "education",
        "bio",
        "biography",
        "cv",
    ],
    "source_residency_background": [
        "residency",
        "resident",
        "prior training",
        "education",
        "bio",
        "biography",
        "cv",
    ],
}


def load_tasks(conn: sqlite3.Connection, limit: int | None) -> list[dict]:
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT p.person_key, p.display_name, p.role, p.raw_json,
               q.task_key, q.task_type, q.priority, q.priority_band, q.query,
               q.blocking_risk, q.recency_policy, q.provenance_policy,
               q.acceptance_rule
        FROM people p
        JOIN person_enrichment_work_queue q ON q.person_key = p.person_key
        WHERE q.task_type IN ('source_medical_school_background', 'source_residency_background')
        ORDER BY CAST(q.priority AS INTEGER) DESC, q.task_type, p.role, p.display_name
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    return [dict(row) for row in conn.execute(sql)]


def program_name(task: dict) -> str:
    raw = json.loads(task.get("raw_json") or "{}")
    programs = raw.get("program_memberships") or [raw.get("program") or ""]
    return next((item for item in programs if item), "")


def query_specs(task: dict, max_queries: int | None) -> list[dict]:
    display = task["display_name"]
    plain = clean_name(display)
    program = program_name(task)
    task_type = task["task_type"]
    if task_type == "source_medical_school_background":
        base_queries = [
            task.get("query") or "",
            f'"{plain}" "medical school"',
            f'"{plain}" education bio CV',
            f'"{plain}" "{program}" "medical school"',
        ]
    else:
        base_queries = [
            task.get("query") or "",
            f'"{plain}" residency',
            f'"{plain}" education bio CV',
            f'"{plain}" "{program}" residency',
        ]
    output = []
    seen = set()
    for index, query in enumerate(base_queries):
        query = norm(query)
        if not query or query in seen:
            continue
        seen.add(query)
        output.append(
            {
                "query_key": key_for("prior_training_query", task["task_key"], query),
                "person_key": task["person_key"],
                "display_name": display,
                "role": task.get("role") or "",
                "program_name": program,
                "task_key": task.get("task_key") or "",
                "task_type": task_type,
                "query_kind": "queue_query" if index == 0 and task.get("query") else "prior_training_background_search",
                "query": query,
                "query_url": f"{DDG_HTML}?q={quote_plus(query)}",
                "priority": task.get("priority") or "",
                "priority_band": task.get("priority_band") or "",
            }
        )
        if max_queries and len(output) >= max_queries:
            break
    return output


def background_hits(task_type: str, text: str) -> list[str]:
    low = text.lower()
    hits = []
    if any(term in low for term in BACKGROUND_TERMS[task_type]):
        hits.append("background_term")
    if re.search(r"\b(md|m\.d\.|do|d\.o\.|mbbs|medical school|school of medicine)\b", low):
        hits.append("medical_training_term")
    if re.search(r"\b(residency|resident|internship|preliminary|chief resident)\b", low):
        hits.append("gme_training_term")
    if re.search(r"\b(cv|curriculum vitae|bio|biography|profile)\b", low):
        hits.append("profile_or_cv_term")
    if re.search(r"\b(penn|penn medicine|university of pennsylvania|perelman|chop)\b", low):
        hits.append("penn_or_current_program_context")
    return hits


def classify_candidate(row: dict) -> tuple[str, float, list[str], str]:
    task_type = row["task_type"]
    url = row.get("result_url") or ""
    domain = row.get("result_domain") or urlparse(url).netloc.lower()
    haystack = " ".join(
        [
            row.get("result_title", ""),
            row.get("result_snippet", ""),
            row.get("probe_title", ""),
            row.get("page_term_hits", ""),
            url,
        ]
    )
    features = []
    if name_present(row.get("display_name") or "", haystack) or int(row.get("page_name_present") or 0):
        features.append("name_present")
    if official_domain(domain):
        features.append("official_domain")
    if domain.endswith("pennmedicine.org") or domain.endswith("med.upenn.edu") or domain.endswith("chop.edu"):
        features.append("current_penn_or_chop_domain")
    hits = background_hits(task_type, haystack)
    features.extend(hits)
    if task_type == "source_medical_school_background" and "medical_training_term" in hits:
        features.append("education_background_anchor")
    if task_type == "source_residency_background" and "gme_training_term" in hits:
        features.append("prior_gme_background_anchor")
    if row.get("probe_http_status") == 200:
        features.append("probe_http_200")
    if row.get("probe_sha256"):
        features.append("content_hash_recorded")

    score = 0.1
    score += 0.22 if "name_present" in features else 0
    score += 0.18 if "official_domain" in features else 0
    score += 0.16 if "education_background_anchor" in features or "prior_gme_background_anchor" in features else 0
    score += 0.08 if "profile_or_cv_term" in features else 0
    score += 0.05 if "penn_or_current_program_context" in features else 0
    score += 0.04 if row.get("result_rank") and int(row["result_rank"]) <= 2 else 0

    if "name_present" in features and (
        "education_background_anchor" in features or "prior_gme_background_anchor" in features
    ):
        status = "background_claim_candidate"
    elif "name_present" in features and "profile_or_cv_term" in features:
        status = "profile_background_context_candidate"
        score = min(score, 0.62)
    elif "official_domain" in features:
        status = "official_context_candidate"
        score = min(score, 0.55)
    else:
        status = "low_signal_search_result"
        score = min(score, 0.3)

    if status == "background_claim_candidate":
        required = "Review source text for same-person identity and explicit education/prior-training field before accepting background enrichment."
    elif status == "profile_background_context_candidate":
        required = "Use as context only until explicit education/prior-training text and same-person anchors are confirmed."
    else:
        required = "Keep as discovery context only unless another source supplies explicit background anchors."
    return status, round(min(score, 0.9), 3), sorted(set(features)), required


def candidate_to_claim(row: dict) -> dict:
    claim_type = (
        "education_history_candidate"
        if row["task_type"] == "source_medical_school_background"
        else "prior_training_history_candidate"
    )
    status = "needs_review" if row["candidate_status"] == "background_claim_candidate" else "candidate"
    return {
        "claim_key": key_for("prior_training_discovery_claim", row["person_key"], row["task_type"], row["candidate_url"]),
        "person_key": row["person_key"],
        "display_name": row["display_name"],
        "role": row["role"],
        "program_context": row["program_name"],
        "claim_type": claim_type,
        "claim_value": row["candidate_url"],
        "source_key": row["source_key"],
        "source_url": row["candidate_url"],
        "source_type": "prior_training_background_discovery",
        "confidence": row["confidence"],
        "status": status,
        "match_features": json.loads(row["match_features_json"]),
        "reconciliation_notes": row["required_next_evidence"],
        "evidence": {
            "origin": "prior_training_background_search_discovery",
            "candidate_status": row["candidate_status"],
            "candidate_key": row["candidate_key"],
            "task_type": row["task_type"],
            "query_key": row["query_key"],
            "query": row["query"],
            "result_rank": row["result_rank"],
            "result_title": row["candidate_title"],
            "result_snippet": row["result_snippet"],
            "probe_http_status": row["http_status"],
            "probe_sha256": row["sha256"],
            "page_term_hits": row["page_term_hits"],
            "display_safety_status": "safe_for_default_display",
            "utility_key": "prior_training_background_discovery",
        },
    }


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--max-tasks", type=int)
    parser.add_argument("--max-queries-per-task", type=int, default=2)
    parser.add_argument("--max-results", type=int, default=4)
    parser.add_argument("--search-timeout", type=float, default=8.0)
    parser.add_argument("--probe-pages", action="store_true")
    parser.add_argument("--skip-search", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(args.db)
    tasks = load_tasks(conn, args.max_tasks)
    conn.close()
    queries = [query for task in tasks for query in query_specs(task, args.max_queries_per_task)]

    session = requests.Session()
    session.headers["User-Agent"] = "redmank-prior-training-background-discovery/0.1"
    observations = []
    candidates_by_key = {}
    for spec in [] if args.skip_search else queries:
        try:
            results, observation = ddg_results(session, spec, args.max_results, args.search_timeout)
        except requests.RequestException as exc:
            results = []
            observation = {
                **spec,
                "searched_at": datetime.now(timezone.utc).isoformat(),
                "search_http_status": 0,
                "result_count": 0,
                "error": f"{type(exc).__name__}: {str(exc)[:220]}",
            }
        observations.append(observation)
        for result in results:
            if args.probe_pages:
                result.update(probe_page(session, result))
                time.sleep(args.sleep)
            else:
                result.update(
                    {
                        "probe_http_status": "",
                        "probe_content_type": "",
                        "probe_title": "",
                        "probe_text_length": 0,
                        "probe_sha256": "",
                        "probe_error": "",
                        "probed_at": "",
                        "page_term_hits": "",
                        "page_name_present": 0,
                    }
                )
            status, confidence, features, required = classify_candidate(result)
            candidate_url = result["result_url"]
            candidate = {
                "candidate_key": key_for("prior_training_candidate", result["task_key"], candidate_url),
                "person_key": result["person_key"],
                "display_name": result["display_name"],
                "role": result["role"],
                "program_name": result.get("program_name") or "",
                "task_key": result.get("task_key") or "",
                "task_type": result["task_type"],
                "query_key": result["query_key"],
                "query_kind": result["query_kind"],
                "query": result["query"],
                "candidate_status": status,
                "priority": int(round(confidence * 100)) + (10 if status == "background_claim_candidate" else 0),
                "confidence": confidence,
                "candidate_title": result["result_title"] or result.get("probe_title") or "",
                "candidate_url": candidate_url,
                "result_rank": result["result_rank"],
                "result_domain": result["result_domain"],
                "result_snippet": result["result_snippet"],
                "http_status": result.get("probe_http_status") or "",
                "content_type": result.get("probe_content_type") or "",
                "text_length": result.get("probe_text_length") or 0,
                "sha256": result.get("probe_sha256") or "",
                "probed_at": result.get("probed_at") or "",
                "page_term_hits": result.get("page_term_hits") or "",
                "match_features_json": dumps(features),
                "required_next_evidence": required,
                "source_key": key_for("prior_training_discovery", candidate_url),
                "evidence_json": dumps(result),
                "discovered_at": generated_at,
            }
            current = candidates_by_key.get(candidate["candidate_key"])
            if not current or int(candidate["priority"]) > int(current["priority"]):
                candidates_by_key[candidate["candidate_key"]] = candidate
        time.sleep(args.sleep)

    candidates = sorted(
        candidates_by_key.values(),
        key=lambda row: (-int(row["priority"]), row["display_name"], row["task_type"], int(row["result_rank"] or 999)),
    )
    claims = [candidate_to_claim(row) for row in candidates if row["candidate_status"] != "low_signal_search_result"]
    sources = [
        {
            "source_key": row["source_key"],
            "url": row["candidate_url"],
            "source_type": "prior_training_background_discovery",
            "title": row["candidate_title"],
            "fetched_at": row["probed_at"] or row["discovered_at"],
            "http_status": row["http_status"],
            "sha256": row["sha256"],
            "person_key": row["person_key"],
            "display_name": row["display_name"],
            "role": row["role"],
            "program": row["program_name"],
            "task_type": row["task_type"],
            "candidate_status": row["candidate_status"],
            "confidence": row["confidence"],
        }
        for row in candidates
        if row["candidate_status"] in {"background_claim_candidate", "profile_background_context_candidate"}
    ]
    summary = {
        "generated_at": generated_at,
        "tasks_considered": len(tasks),
        "people_considered": len({row["person_key"] for row in tasks}),
        "query_rows": len(queries),
        "search_skipped": args.skip_search,
        "search_observations": len(observations),
        "candidate_rows": len(candidates),
        "claim_rows": len(claims),
        "source_rows": len(sources),
        "by_task_type": dict(sorted(Counter(row["task_type"] for row in tasks).items())),
        "by_candidate_status": dict(sorted(Counter(row["candidate_status"] for row in candidates).items())),
        "by_result_domain": dict(sorted(Counter(row["result_domain"] for row in candidates).most_common(25))),
        "by_search_http_status": dict(sorted(Counter(str(row.get("search_http_status", "")) for row in observations).items())),
        "by_search_error": dict(sorted(Counter(row.get("error", "") for row in observations if row.get("error")).items())),
        "csv": str(CANDIDATE_CSV.relative_to(ROOT)),
        "claims_json": str(CLAIMS_JSON.relative_to(ROOT)),
        "sources_json": str(SOURCES_JSON.relative_to(ROOT)),
        "policy": "Prior-training background discoveries are candidate evidence only. They do not mutate accepted education or GME background without explicit source-text review and reconciliation.",
    }

    query_fields = [
        "query_key",
        "person_key",
        "display_name",
        "role",
        "program_name",
        "task_key",
        "task_type",
        "query_kind",
        "query",
        "query_url",
        "priority",
        "priority_band",
    ]
    observation_fields = query_fields + ["searched_at", "search_http_status", "result_count", "error"]
    candidate_fields = [
        "candidate_key",
        "person_key",
        "display_name",
        "role",
        "program_name",
        "task_key",
        "task_type",
        "query_key",
        "query_kind",
        "query",
        "candidate_status",
        "priority",
        "confidence",
        "candidate_title",
        "candidate_url",
        "result_rank",
        "result_domain",
        "result_snippet",
        "http_status",
        "content_type",
        "text_length",
        "sha256",
        "probed_at",
        "page_term_hits",
        "match_features_json",
        "required_next_evidence",
        "source_key",
        "evidence_json",
        "discovered_at",
    ]
    write_csv(QUERY_CSV, queries, query_fields)
    write_csv(OBSERVATION_CSV, observations, observation_fields)
    write_csv(CANDIDATE_CSV, candidates, candidate_fields)
    CLAIMS_JSON.write_text(json.dumps(claims, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    SOURCES_JSON.write_text(json.dumps(sources, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
