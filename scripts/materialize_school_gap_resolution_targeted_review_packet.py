#!/usr/bin/env python3
"""Materialize a non-mutating targeted Vanderbilt gap review packet."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

TEMPLATE_CSV = ARTIFACTS / "school_gap_resolution_review_template.csv"
TEMPLATE_SUMMARY = ARTIFACTS / "school_gap_resolution_review_template_summary.json"
WORKBENCH_CSV = ARTIFACTS / "vanderbilt_targeted_gap_source_discovery_workbench.csv"
WORKBENCH_SUMMARY = ARTIFACTS / "vanderbilt_targeted_gap_source_discovery_workbench_summary.json"

OUT_CSV = ARTIFACTS / "school_gap_resolution_targeted_review_packet.csv"
OUT_JSON = ARTIFACTS / "school_gap_resolution_targeted_review_packet.json"
OUT_SUMMARY = ARTIFACTS / "school_gap_resolution_targeted_review_packet_summary.json"
OUT_MD = RESEARCH / "school-gap-resolution-targeted-review-packet-2026-06-09.md"

EXPECTED_TEMPLATE_ROWSET = "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782"
EXPECTED_WORKBENCH_ROWSET = "dd72909d1f992209a414ef232d8c4d499de5de2a90cf45f49428153d1ebe1b71"
EXPECTED_TEMPLATE_ROWS = 113
EXPECTED_TARGET_GAPS = 19
EXPECTED_WORKBENCH_ROWS = 38

MUTATION_POLICY = (
    "Non-mutating targeted Vanderbilt gap review packet. It copies the committed blank review template, fills only "
    "candidate-evidence planning fields for the 19 targeted workbench gaps, and keeps candidate URLs as later-review "
    "evidence. It does not fetch pages, accept people, close denominators, verify Vanderbilt, rewrite URLs, accept "
    "enrichment facts, or collapse identities."
)

HIGH_STATUS = "official_candidate_current_roster_signal_needs_parser_review"
MEDIUM_STATUS = "official_candidate_roster_text_without_supported_people"
STATUS_RANK = {
    HIGH_STATUS: 0,
    MEDIUM_STATUS: 1,
    "official_context_no_current_roster_signal": 2,
    "official_context_or_negative_page_no_current_roster": 3,
}
CONFIRMATION_FIELDS = [
    "confirm_no_person_ingestion",
    "confirm_no_denominator_closure",
    "confirm_no_school_verification",
    "confirm_no_url_rewrite",
    "confirm_no_identity_collapse",
    "confirm_candidate_evidence_only",
]

csv.field_size_limit(sys.maxsize)


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rowset_sha256(rows: list[dict[str, str]], fields: list[str]) -> str:
    excluded = {"review_template_key", "evidence_json", "mutation_policy", "generated_at"}
    material = [
        {field: row.get(field, "") for field in fields if field not in excluded}
        for row in sorted(rows, key=lambda item: str(item.get("review_template_key", "")))
    ]
    return sha256_text(dumps(material))


def workbench_choice_key(row: dict[str, str]) -> tuple[int, int, int, str]:
    roster_count = int(row.get("roster_signal_count") or 0)
    person_count = int(row.get("person_signal_count") or 0)
    return (
        STATUS_RANK.get(row.get("candidate_status", ""), 9),
        -roster_count,
        -person_count,
        row.get("candidate_url", ""),
    )


def action_for(row: dict[str, str]) -> str:
    if row.get("candidate_status") == HIGH_STATUS:
        return "route_inspection_needed"
    if row.get("candidate_status") == MEDIUM_STATUS:
        return "rendered_or_manual_review_needed"
    return "source_discovery_query_only"


def summary_for(row: dict[str, str]) -> str:
    status = row.get("candidate_status", "")
    confidence = row.get("candidate_confidence", "")
    roster_count = row.get("roster_signal_count", "0")
    person_count = row.get("person_signal_count", "0")
    if status == HIGH_STATUS:
        return (
            "Official-domain candidate with current-roster signals; "
            f"confidence={confidence}; roster_signals={roster_count}; person_signals={person_count}; "
            "candidate evidence only."
        )
    if status == MEDIUM_STATUS:
        return (
            "Official-domain candidate with roster text but unsupported people in static text; "
            f"confidence={confidence}; roster_signals={roster_count}; candidate evidence only."
        )
    return "Official-domain context candidate; continue source planning with candidate evidence only."


def output_artifact_for(row: dict[str, str]) -> str:
    program = row.get("program_name", "program").lower()
    safe = "".join(ch if ch.isalnum() else "_" for ch in program).strip("_")
    return f"/tmp/vanderbilt_gap_review_{safe[:64]}.csv"


def write_markdown(rows: list[dict[str, str]], summary: dict[str, object]) -> None:
    lines = [
        "---",
        "type: research-checkpoint",
        "title: School Gap Resolution Targeted Review Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# School Gap Resolution Targeted Review Packet",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Filled Rows",
        "",
        "| program | action | confidence | candidate |",
        "| --- | --- | --- | --- |",
    ]
    for row in rows:
        if not row.get("proposed_non_mutating_review_action"):
            continue
        evidence = json.loads(row.get("evidence_json") or "{}")
        lines.append(
            "| {program_name} | {action} | {confidence} | {url} |".format(
                program_name=row.get("program_name", ""),
                action=row.get("proposed_non_mutating_review_action", ""),
                confidence=evidence.get("candidate_confidence", ""),
                url=row.get("proposed_candidate_official_url", ""),
            )
        )
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    template_summary = read_json(TEMPLATE_SUMMARY)
    workbench_summary = read_json(WORKBENCH_SUMMARY)
    if not isinstance(template_summary, dict) or not isinstance(workbench_summary, dict):
        raise SystemExit("Expected template and targeted workbench summaries to be JSON objects.")
    source_checks = {
        "template_rowset": template_summary.get("rowset_sha256") == EXPECTED_TEMPLATE_ROWSET,
        "template_rows": template_summary.get("review_template_rows") == EXPECTED_TEMPLATE_ROWS,
        "template_mutation_false": template_summary.get("mutation_allowed") is False,
        "workbench_rowset": workbench_summary.get("rowset_sha256") == EXPECTED_WORKBENCH_ROWSET,
        "workbench_rows": workbench_summary.get("workbench_rows") == EXPECTED_WORKBENCH_ROWS,
        "workbench_target_gaps": workbench_summary.get("target_gap_rows") == EXPECTED_TARGET_GAPS,
        "workbench_mutation_false": workbench_summary.get("mutation_allowed") is False,
    }
    if not all(source_checks.values()):
        raise SystemExit("Unexpected targeted review packet source boundary: " + dumps(source_checks))

    fields, template_rows = read_csv_rows(TEMPLATE_CSV)
    _, workbench_rows = read_csv_rows(WORKBENCH_CSV)
    by_gap: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in workbench_rows:
        by_gap[row.get("gap_key", "")].append(row)
    selected = {gap: sorted(rows, key=workbench_choice_key)[0] for gap, rows in by_gap.items() if gap}
    if len(template_rows) != EXPECTED_TEMPLATE_ROWS or len(selected) != EXPECTED_TARGET_GAPS:
        raise SystemExit("Unexpected template row or selected targeted gap count.")

    generated_at = datetime.now(timezone.utc).isoformat()
    output_rows: list[dict[str, str]] = []
    by_action: Counter[str] = Counter()
    by_candidate_status: Counter[str] = Counter()
    by_confidence: Counter[str] = Counter()
    missing_template_gaps = sorted(set(selected) - {row.get("gap_key", "") for row in template_rows})
    if missing_template_gaps:
        raise SystemExit("Targeted workbench gaps missing from template: " + ", ".join(missing_template_gaps))

    for template_row in template_rows:
        row = dict(template_row)
        row["generated_at"] = generated_at
        candidate = selected.get(row.get("gap_key", ""))
        if candidate:
            action = action_for(candidate)
            row["proposed_non_mutating_review_action"] = action
            row["proposed_source_discovery_query"] = (
                "Review official Vanderbilt candidate source for "
                + candidate.get("program_name", "")
                + " current roster scope."
            )
            row["proposed_candidate_official_url"] = candidate.get("candidate_url", "")
            row["proposed_evidence_summary"] = summary_for(candidate)
            row["proposed_output_artifact"] = output_artifact_for(candidate)
            for field in CONFIRMATION_FIELDS:
                row[field] = "true"
            row["template_row_status"] = "targeted_candidate_evidence_ready_for_non_mutating_review"
            row["evidence_json"] = dumps(
                {
                    "source_workbench_key": candidate.get("workbench_key", ""),
                    "source_workbench_rowset_sha256": EXPECTED_WORKBENCH_ROWSET,
                    "candidate_status": candidate.get("candidate_status", ""),
                    "candidate_confidence": candidate.get("candidate_confidence", ""),
                    "candidate_url": candidate.get("candidate_url", ""),
                    "effective_url": candidate.get("effective_url", ""),
                    "http_status": candidate.get("http_status", ""),
                    "fetch_status": candidate.get("fetch_status", ""),
                    "content_sha256": candidate.get("content_sha256", ""),
                    "roster_signal_count": candidate.get("roster_signal_count", ""),
                    "person_signal_count": candidate.get("person_signal_count", ""),
                    "candidate_evidence_only": True,
                }
            )
            by_action[action] += 1
            by_candidate_status[candidate.get("candidate_status", "")] += 1
            by_confidence[candidate.get("candidate_confidence", "")] += 1
        output_rows.append(row)

    rowset = rowset_sha256(output_rows, fields)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_template_rowset_sha256": EXPECTED_TEMPLATE_ROWSET,
        "source_workbench_rowset_sha256": EXPECTED_WORKBENCH_ROWSET,
        "review_packet_rows": len(output_rows),
        "filled_review_rows": sum(1 for row in output_rows if row.get("proposed_non_mutating_review_action")),
        "blank_review_rows": sum(1 for row in output_rows if not row.get("proposed_non_mutating_review_action")),
        "target_gap_rows": len(selected),
        "by_action": dict(sorted(by_action.items())),
        "by_candidate_status": dict(sorted(by_candidate_status.items())),
        "by_confidence": dict(sorted(by_confidence.items())),
        "validation_command": (
            "python3 scripts/validate_school_gap_resolution_review_template.py "
            "--input artifacts/data/school_gap_resolution_targeted_review_packet.csv "
            "--summary artifacts/data/school_gap_resolution_targeted_review_packet_validation_summary.json"
        ),
        "rowset_sha256": rowset,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "candidate_evidence_only": True,
        "policy": MUTATION_POLICY,
    }
    if summary["filled_review_rows"] != EXPECTED_TARGET_GAPS or summary["review_packet_rows"] != EXPECTED_TEMPLATE_ROWS:
        raise SystemExit("Targeted review packet failed row count checks.")

    write_csv(OUT_CSV, fields, output_rows)
    write_json(OUT_JSON, output_rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(output_rows, summary)
    print(json.dumps({key: summary[key] for key in ["review_packet_rows", "filled_review_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
