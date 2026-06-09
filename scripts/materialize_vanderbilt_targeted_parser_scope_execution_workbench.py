#!/usr/bin/env python3
"""Materialize a non-mutating Vanderbilt targeted parser/scope execution workbench."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SOURCE_CSV = ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet.csv"
SOURCE_JSON = ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_targeted_parser_scope_execution_workbench.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_targeted_parser_scope_execution_workbench.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_targeted_parser_scope_execution_workbench_summary.json"
OUT_MD = RESEARCH / "vanderbilt-targeted-parser-scope-execution-workbench-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "dd7ba52cefcec632da434810653bce1b106696ca9a9d94fe3e517f206ae50785"
SOURCE_WORKBENCH_ROWSET_SHA256 = "dd72909d1f992209a414ef232d8c4d499de5de2a90cf45f49428153d1ebe1b71"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt targeted parser/scope execution workbench. It routes approved review-packet rows "
    "to linked-route fetch, rendered review, parser-test design, or scope disposition. It authorizes no person "
    "ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, "
    "unsupported-label ingestion, profile enrichment, contact acceptance, research fact acceptance, or "
    "unique-person identity collapse."
)

NOT_APPROVED = [
    "person_ingestion",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "profile_contact_research_fact_acceptance",
    "unique_person_identity_collapse",
]

APPROVAL_REQUIRED_FOR = [
    "parser_acceptance",
    "person_ingestion",
    "denominator_closure",
    "training_state_mutation",
    "school_verification",
    "source_url_rewrite",
    "unsupported_label_ingestion",
    "profile_contact_research_fact_acceptance",
    "identity_collapse",
]

FIELDS = [
    "execution_key",
    "source_review_packet_key",
    "gap_key",
    "program_key",
    "program_name",
    "candidate_confidence",
    "source_review_lane",
    "execution_lane",
    "execution_status",
    "workbench_priority",
    "fetch_url",
    "fetch_url_source",
    "source_page_url",
    "candidate_url",
    "fetch_domain",
    "same_domain_fetch",
    "rendered_review_required",
    "parser_test_required",
    "scope_disposition_required",
    "parser_acceptance_packet_required",
    "route_scope_check",
    "parser_probe_requirements",
    "acceptance_boundary",
    "recommended_next_packet",
    "mutation_policy",
    "evidence_json",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_review_packet_key",
    "gap_key",
    "program_key",
    "program_name",
    "candidate_confidence",
    "source_review_lane",
    "execution_lane",
    "execution_status",
    "workbench_priority",
    "fetch_url",
    "fetch_url_source",
    "source_page_url",
    "same_domain_fetch",
    "rendered_review_required",
    "parser_test_required",
    "scope_disposition_required",
    "parser_acceptance_packet_required",
    "route_scope_check",
    "recommended_next_packet",
]

csv.field_size_limit(sys.maxsize)


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt targeted parser/scope review summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "review_rows": summary.get("review_rows") == 20,
        "source_workbench_rowset_sha256": summary.get("source_workbench_rowset_sha256") == SOURCE_WORKBENCH_ROWSET_SHA256,
        "gbrain_registration_status": summary.get("gbrain_registration_status") == "approved",
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected Vanderbilt parser/scope source boundary: {checks}")
    return summary


def domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def as_bool(value: bool) -> str:
    return "true" if value else "false"


def route(row: dict[str, object]) -> dict[str, object]:
    source_lane = str(row.get("parser_review_lane") or "")
    source_page_url = str(row.get("effective_url") or row.get("candidate_url") or "")
    top_roster_link_url = str(row.get("top_roster_link_url") or "")
    fetch_url = top_roster_link_url or source_page_url

    if source_lane == "follow_same_program_roster_link_before_parser":
        return {
            "execution_lane": "linked_roster_route_fetch",
            "execution_status": "fetch_linked_route_before_parser_scope_packet",
            "workbench_priority": 90,
            "fetch_url": fetch_url,
            "fetch_url_source": "top_roster_link_url" if top_roster_link_url else "effective_url",
            "rendered_review_required": False,
            "parser_test_required": True,
            "scope_disposition_required": True,
            "parser_acceptance_packet_required": True,
            "route_scope_check": "same_program_current_roster_link_scope_and_person_extractability_required",
            "parser_probe_requirements": (
                "Fetch linked official route, record status/title/final URL/content hash, confirm current trainee "
                "scope, capture exact selectors or text patterns, and emit parser acceptance or disposition packet."
            ),
            "recommended_next_packet": "linked_route_parser_acceptance_or_scope_disposition_packet",
        }
    if source_lane == "scope_ambiguous_roster_link_review":
        return {
            "execution_lane": "ambiguous_roster_link_scope_review",
            "execution_status": "review_linked_route_scope_before_parser",
            "workbench_priority": 80,
            "fetch_url": fetch_url,
            "fetch_url_source": "top_roster_link_url" if top_roster_link_url else "effective_url",
            "rendered_review_required": True,
            "parser_test_required": False,
            "scope_disposition_required": True,
            "parser_acceptance_packet_required": False,
            "route_scope_check": "program_scope_mismatch_or_shared_roster_risk_must_be_resolved",
            "parser_probe_requirements": (
                "Fetch/render linked official route and decide whether it is same-program current roster evidence, "
                "shared-scope context, or negative/source-discovery recourse."
            ),
            "recommended_next_packet": "linked_route_scope_review_or_recourse_packet",
        }
    if source_lane == "rendered_current_residents_scope_review":
        return {
            "execution_lane": "rendered_current_residents_review",
            "execution_status": "render_current_residents_route_before_general_surgery_disposition",
            "workbench_priority": 75,
            "fetch_url": source_page_url,
            "fetch_url_source": "effective_url",
            "rendered_review_required": True,
            "parser_test_required": False,
            "scope_disposition_required": True,
            "parser_acceptance_packet_required": False,
            "route_scope_check": "general_surgery_current_residents_people_signal_or_closure_recourse_required",
            "parser_probe_requirements": (
                "Render official current-residents route, inspect DOM/text after JavaScript, and preserve evidence "
                "for parser acceptance request or medium-evidence recourse."
            ),
            "recommended_next_packet": "general_surgery_rendered_review_disposition_packet",
        }
    return {
        "execution_lane": "unexpected_source_review_lane",
        "execution_status": "manual_boundary_review_required",
        "workbench_priority": 10,
        "fetch_url": fetch_url,
        "fetch_url_source": "top_roster_link_url" if top_roster_link_url else "effective_url",
        "rendered_review_required": True,
        "parser_test_required": False,
        "scope_disposition_required": True,
        "parser_acceptance_packet_required": False,
        "route_scope_check": "source_lane_not_recognized",
        "parser_probe_requirements": "Reconcile source packet lane before any route fetch or parser design.",
        "recommended_next_packet": "manual_boundary_reconciliation_packet",
    }


def materialize_rows(source_rows: list[dict[str, object]], generated_at: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for source in source_rows:
        routed = route(source)
        source_page_url = str(source.get("effective_url") or source.get("candidate_url") or "")
        fetch_url = str(routed["fetch_url"])
        evidence = json.loads(str(source.get("evidence_json") or "{}"))
        rows.append(
            {
                "execution_key": stable_key(
                    "vanderbilt_targeted_parser_scope_execution",
                    source.get("review_packet_key"),
                    routed["execution_lane"],
                    fetch_url,
                ),
                "source_review_packet_key": source.get("review_packet_key"),
                "gap_key": source.get("gap_key"),
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "candidate_confidence": source.get("candidate_confidence"),
                "source_review_lane": source.get("parser_review_lane"),
                "execution_lane": routed["execution_lane"],
                "execution_status": routed["execution_status"],
                "workbench_priority": routed["workbench_priority"],
                "fetch_url": fetch_url,
                "fetch_url_source": routed["fetch_url_source"],
                "source_page_url": source_page_url,
                "candidate_url": source.get("candidate_url"),
                "fetch_domain": domain(fetch_url),
                "same_domain_fetch": as_bool(bool(routed.get("fetch_url")) and domain(fetch_url) == domain(source_page_url)),
                "rendered_review_required": as_bool(bool(routed["rendered_review_required"])),
                "parser_test_required": as_bool(bool(routed["parser_test_required"])),
                "scope_disposition_required": as_bool(bool(routed["scope_disposition_required"])),
                "parser_acceptance_packet_required": as_bool(bool(routed["parser_acceptance_packet_required"])),
                "route_scope_check": routed["route_scope_check"],
                "parser_probe_requirements": routed["parser_probe_requirements"],
                "acceptance_boundary": "Exact GBrain approval required before parser acceptance, person ingestion, denominator closure, or state mutation.",
                "recommended_next_packet": routed["recommended_next_packet"],
                "mutation_policy": MUTATION_POLICY,
                "evidence_json": dumps(
                    {
                        "source_review_packet_key": source.get("review_packet_key"),
                        "source_review_packet_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "source_workbench_rowset_sha256": SOURCE_WORKBENCH_ROWSET_SHA256,
                        "source_candidate_status": source.get("candidate_status"),
                        "source_selection_reason": source.get("source_selection_reason"),
                        "source_parser_readiness_status": source.get("parser_readiness_status"),
                        "source_recommended_next_action": source.get("recommended_next_action"),
                        "candidate_roster_link_count": source.get("candidate_roster_link_count"),
                        "top_roster_link_url": source.get("top_roster_link_url"),
                        "top_roster_link_text": source.get("top_roster_link_text"),
                        "source_evidence": evidence,
                    }
                ),
                "generated_at": generated_at,
            }
        )
    return sorted(rows, key=lambda item: (-int(item["workbench_priority"]), str(item["program_name"]), str(item["fetch_url"])))


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("execution_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Targeted Parser Scope Execution Workbench",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Targeted Parser Scope Execution Workbench",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "This workbench is an execution queue only. It preserves the approved parser/scope review packet boundary and does not approve parser acceptance, people, denominator closure, URL rewrites, enrichment claims, or identity collapse.",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Execution Rows",
        "",
        "| priority | program | lane | status | fetch url | next packet |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {workbench_priority} | {program_name} | {execution_lane} | {execution_status} | {fetch_url} | {recommended_next_packet} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected Vanderbilt targeted parser/scope review packet JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows = materialize_rows(source_rows, generated_at)
    by_lane = Counter(str(row["execution_lane"]) for row in rows)
    by_status = Counter(str(row["execution_status"]) for row in rows)
    by_next_packet = Counter(str(row["recommended_next_packet"]) for row in rows)
    by_fetch_domain = Counter(str(row["fetch_domain"]) for row in rows)
    fetch_urls = sorted({str(row["fetch_url"]) for row in rows if row.get("fetch_url")})

    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_packet_csv": str(SOURCE_CSV.relative_to(ROOT)),
        "source_packet_json": str(SOURCE_JSON.relative_to(ROOT)),
        "source_packet_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_packet_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_workbench_rowset_sha256": SOURCE_WORKBENCH_ROWSET_SHA256,
        "source_review_rows": source_summary.get("review_rows"),
        "source_gbrain_registration_status": source_summary.get("gbrain_registration_status"),
        "workbench_rows": len(rows),
        "unique_fetch_urls": len(fetch_urls),
        "fetch_urls": fetch_urls,
        "by_execution_lane": dict(sorted(by_lane.items())),
        "by_execution_status": dict(sorted(by_status.items())),
        "by_recommended_next_packet": dict(sorted(by_next_packet.items())),
        "by_fetch_domain": dict(sorted(by_fetch_domain.items())),
        "mutation_allowed": False,
        "not_approved": NOT_APPROVED,
        "approval_required_for": APPROVAL_REQUIRED_FOR,
        "policy": MUTATION_POLICY,
        "public_safety_policy": (
            "Commit this deterministic queue and summaries only. Do not commit raw rendered browser dumps, "
            "GBrain HTTP responses, debug databases, or private scratch captures."
        ),
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["workbench_rows", "unique_fetch_urls", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
