#!/usr/bin/env python3
"""Materialize a non-mutating Vanderbilt targeted parser/scope review packet."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

WORKBENCH_JSON = ARTIFACTS / "vanderbilt_targeted_gap_source_discovery_workbench.json"
SUMMARY_JSON = ARTIFACTS / "vanderbilt_targeted_gap_source_discovery_workbench_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-targeted-parser-scope-review-packet-2026-06-09.md"

WORKBENCH_ROWSET_SHA256 = "dd72909d1f992209a414ef232d8c4d499de5de2a90cf45f49428153d1ebe1b71"
APPROVAL_EFFECT = "vanderbilt_targeted_gap_source_discovery_evidence_registration_approved"
APPROVAL_LINE = (
    "APPROVE vanderbilt_targeted_gap_source_discovery_evidence_registration_approved "
    "WORKBENCH_ROWS 38 HIGH_SIGNAL_ROWS 19 TARGET_GAPS 19 ROWSET_SHA256 "
    "dd72909d1f992209a414ef232d8c4d499de5de2a90cf45f49428153d1ebe1b71"
)

MUTATION_POLICY = (
    "Non-mutating Vanderbilt targeted parser/scope review packet. It queues official candidate pages for "
    "parser design, rendered review, link-follow review, or scope disposition. It authorizes no person "
    "ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, "
    "unsupported-label ingestion, profile enrichment, contact acceptance, research fact acceptance, or "
    "unique-person identity collapse."
)

FIELDS = [
    "review_packet_key",
    "gap_key",
    "program_key",
    "program_name",
    "candidate_url",
    "effective_url",
    "candidate_status",
    "candidate_confidence",
    "source_selection_reason",
    "roster_signal_count",
    "person_signal_count",
    "current_card_count",
    "candidate_roster_link_count",
    "top_roster_link_url",
    "top_roster_link_text",
    "parser_review_lane",
    "review_priority",
    "parser_readiness_status",
    "recommended_next_action",
    "gbrain_registration_status",
    "mutation_policy",
    "evidence_json",
    "generated_at",
]

ROWSET_FIELDS = [
    "gap_key",
    "program_key",
    "program_name",
    "effective_url",
    "candidate_status",
    "candidate_confidence",
    "source_selection_reason",
    "top_roster_link_url",
    "parser_review_lane",
    "review_priority",
    "parser_readiness_status",
    "recommended_next_action",
    "gbrain_registration_status",
]

STOP_TOKENS = {
    "and",
    "the",
    "of",
    "in",
    "medicine",
    "surgery",
    "fellowship",
    "residency",
    "program",
    "vanderbilt",
    "pediatric",
    "adult",
    "health",
    "general",
}

csv.field_size_limit(sys.maxsize)


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def program_tokens(program_name: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", program_name.lower())
        if len(token) > 2 and token not in STOP_TOKENS
    }


def approval_status(approval_line: str) -> str:
    return "approved" if APPROVAL_LINE in approval_line else "pending_exact_gbrain_registration"


def verify_workbench_boundary() -> dict[str, object]:
    summary = read_json(SUMMARY_JSON)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt targeted source-discovery summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == WORKBENCH_ROWSET_SHA256,
        "workbench_rows": summary.get("workbench_rows") == 38,
        "target_gap_rows": summary.get("target_gap_rows") == 19,
        "high_confidence_rows": summary.get("by_confidence", {}).get("high") == 19,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected targeted workbench boundary: {checks}")
    return summary


def select_review_rows(workbench: list[dict[str, object]]) -> list[tuple[dict[str, object], str]]:
    selected: list[tuple[dict[str, object], str]] = []
    for row in workbench:
        if row.get("candidate_confidence") == "high":
            selected.append((row, "high_confidence_current_roster_signal"))

    general_surgery = [
        row
        for row in workbench
        if row.get("program_name") == "General Surgery"
        and row.get("candidate_confidence") == "medium"
        and "current-residents" in str(row.get("effective_url") or row.get("candidate_url") or "")
    ]
    if len(general_surgery) != 1:
        raise SystemExit("Expected exactly one General Surgery current-residents medium-evidence row.")
    selected.append((general_surgery[0], "general_surgery_medium_current_residents_review_row"))
    return selected


def classify(row: dict[str, object], selection_reason: str) -> tuple[str, int, str, str]:
    effective_url = str(row.get("effective_url") or "")
    candidate_status = str(row.get("candidate_status") or "")
    link_url = str(row.get("top_roster_link_url") or "")
    link_text = str(row.get("top_roster_link_text") or "")
    person_count = int(row.get("person_signal_count") or 0)
    card_count = int(row.get("current_card_count") or 0)
    link_count = int(row.get("candidate_roster_link_count") or 0)
    tokens = program_tokens(str(row.get("program_name") or ""))
    link_blob = f"{link_text} {link_url}".lower()
    link_token_hits = sum(1 for token in tokens if token in link_blob)
    current_blob = f"{effective_url} {row.get('title') or ''}".lower()

    if selection_reason.startswith("general_surgery"):
        return (
            "rendered_current_residents_scope_review",
            10,
            "medium_signal_rendered_or_js_parser_review_required",
            "Run rendered/headed review of the official current-residents route before parser acceptance or closure.",
        )
    if "current-fellow" in current_blob or "current_fellow" in current_blob or "/person/" in effective_url:
        return (
            "direct_current_fellows_page_parser_candidate",
            9,
            "parser_candidate_needs_exact_person_extraction_review",
            "Build exact parser tests and source-scope review before any person ingestion.",
        )
    if link_count and link_token_hits:
        return (
            "follow_same_program_roster_link_before_parser",
            8,
            "linked_roster_candidate_needs_fetch_and_scope_review",
            "Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition.",
        )
    if link_count:
        return (
            "scope_ambiguous_roster_link_review",
            7,
            "linked_roster_candidate_scope_ambiguous",
            "Review roster-link scope before treating this page as a parser source.",
        )
    if "current_roster_signal" in candidate_status and person_count:
        return (
            "official_page_parser_candidate",
            6,
            "parser_candidate_needs_exact_person_extraction_review",
            "Build source-specific parser tests and scope checks before any person ingestion.",
        )
    if card_count and person_count:
        return (
            "rendered_section_parser_review",
            5,
            "section_parser_candidate_scope_ambiguous",
            "Use rendered/headed review to decide whether current trainee sections are extractable or only context.",
        )
    return (
        "low_volume_program_page_scope_review",
        4,
        "weak_parser_candidate_needs_more_evidence",
        "Retain as source-discovery evidence and seek stronger official roster support before closure.",
    )


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("review_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Targeted Parser Scope Review Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Targeted Parser Scope Review Packet",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Registration Status",
        "",
        "GBrain evidence registration status: `" + str(summary["gbrain_registration_status"]) + "`.",
        "",
        "If `pending_exact_gbrain_registration`, this packet is a draft source-review scaffold only. It must not be used for parser acceptance, person ingestion, denominator closure, or URL rewrites until the exact approval line is supplied and the packet is regenerated.",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Review Rows",
        "",
        "| priority | program | confidence | lane | people | url | next action |",
        "| ---: | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in sorted(rows, key=lambda item: (-int(item["review_priority"]), str(item["program_name"]), str(item["effective_url"]))):
        lines.append(
            "| {review_priority} | {program_name} | {candidate_confidence} | {parser_review_lane} | {person_signal_count} | {effective_url} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--approval-line",
        default="",
        help="Exact GBrain approval line. Omit to emit a pending-registration draft packet.",
    )
    args = parser.parse_args()

    source_summary = verify_workbench_boundary()
    workbench = read_json(WORKBENCH_JSON)
    if not isinstance(workbench, list):
        raise SystemExit("Expected Vanderbilt targeted source-discovery workbench JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    registration_status = approval_status(args.approval_line)
    selected = select_review_rows(workbench)
    rows: list[dict[str, object]] = []

    for row, selection_reason in selected:
        lane, priority, readiness, next_action = classify(row, selection_reason)
        evidence = json.loads(str(row.get("evidence_json") or "{}"))
        rows.append(
            {
                "review_packet_key": stable_key("vanderbilt_targeted_parser_scope_review", row.get("workbench_key"), lane, selection_reason),
                "gap_key": row.get("gap_key"),
                "program_key": row.get("program_key"),
                "program_name": row.get("program_name"),
                "candidate_url": row.get("candidate_url"),
                "effective_url": row.get("effective_url"),
                "candidate_status": row.get("candidate_status"),
                "candidate_confidence": row.get("candidate_confidence"),
                "source_selection_reason": selection_reason,
                "roster_signal_count": row.get("roster_signal_count"),
                "person_signal_count": row.get("person_signal_count"),
                "current_card_count": row.get("current_card_count"),
                "candidate_roster_link_count": row.get("candidate_roster_link_count"),
                "top_roster_link_url": row.get("top_roster_link_url"),
                "top_roster_link_text": row.get("top_roster_link_text"),
                "parser_review_lane": lane,
                "review_priority": priority,
                "parser_readiness_status": readiness,
                "recommended_next_action": next_action,
                "gbrain_registration_status": registration_status,
                "mutation_policy": MUTATION_POLICY,
                "evidence_json": dumps(
                    {
                        "source_workbench_key": row.get("workbench_key"),
                        "source_workbench_rowset_sha256": WORKBENCH_ROWSET_SHA256,
                        "source_selection_reason": selection_reason,
                        "program_tokens": sorted(program_tokens(str(row.get("program_name") or ""))),
                        "roster_links": evidence.get("roster_links", []),
                        "current_card_sample": evidence.get("current_card_sample", []),
                        "text_excerpt": row.get("text_excerpt"),
                    }
                ),
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (-int(item["review_priority"]), str(item["program_name"]), str(item["effective_url"])))
    by_lane = Counter(str(row["parser_review_lane"]) for row in rows)
    by_readiness = Counter(str(row["parser_readiness_status"]) for row in rows)
    by_selection = Counter(str(row["source_selection_reason"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_workbench": str(WORKBENCH_JSON.relative_to(ROOT)),
        "source_workbench_rowset_sha256": WORKBENCH_ROWSET_SHA256,
        "source_workbench_rows": source_summary.get("workbench_rows"),
        "source_target_gap_rows": source_summary.get("target_gap_rows"),
        "gbrain_approval_effect": APPROVAL_EFFECT if registration_status == "approved" else "",
        "gbrain_registration_status": registration_status,
        "mutation_allowed": False,
        "policy": MUTATION_POLICY,
        "review_rows": len(rows),
        "by_source_selection_reason": dict(sorted(by_selection.items())),
        "by_parser_review_lane": dict(sorted(by_lane.items())),
        "by_parser_readiness_status": dict(sorted(by_readiness.items())),
        "rowset_sha256": rowset_sha256(rows),
    }
    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["review_rows", "gbrain_registration_status", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
