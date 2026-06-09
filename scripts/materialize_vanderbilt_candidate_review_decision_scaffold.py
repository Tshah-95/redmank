#!/usr/bin/env python3
"""Materialize non-mutating Vanderbilt candidate review decision scaffolds."""

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

SOURCE_JSON = ARTIFACTS / "vanderbilt_candidate_review_queues.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_queue_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json"
OUT_MD = RESEARCH / "vanderbilt-candidate-review-decision-scaffold-2026-06-09.md"
OUT_DECISIONS_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.csv"
OUT_DECISIONS_JSON = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.json"

SOURCE_ROWSET_SHA256 = "b74b337bfa43406d8a200956d469eb5dc0d41902c197f78af85001f18750b148"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt candidate review decision scaffold. It creates pending reviewer-decision rows and "
    "blank decision templates for hashed candidate fingerprints, linked-scope metadata, and route recourse rows. "
    "It does not approve raw candidate labels, raw person URLs, accepted person rows, person ingestion, training-"
    "state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, "
    "enrichment acceptance, raw dump publication, or unique-person identity collapse."
)

FIELDS = [
    "decision_scaffold_key",
    "source_review_queue_key",
    "review_batch_key",
    "review_queue_lane",
    "decision_status",
    "decision_priority",
    "program_key",
    "program_name",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "content_sha256",
    "visible_text_sha256",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "decision_fingerprint",
    "manual_decision_file",
    "manual_decision_row_key",
    "accepted_person_row",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

DECISION_FIELDS = [
    "manual_decision_row_key",
    "decision_scaffold_key",
    "review_batch_key",
    "review_queue_lane",
    "program_key",
    "program_name",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "decision_fingerprint",
    "reviewer_action",
    "reviewer_note",
    "confirm_decision_fingerprint",
    "confirm_no_person_ingestion",
    "confirm_no_denominator_closure",
    "confirm_no_raw_name_added",
    "confirm_no_url_rewrite",
]

ROWSET_FIELDS = [
    "source_review_queue_key",
    "review_batch_key",
    "review_queue_lane",
    "decision_status",
    "decision_priority",
    "program_key",
    "program_name",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "content_sha256",
    "visible_text_sha256",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "decision_fingerprint",
    "manual_decision_file",
    "manual_decision_row_key",
    "accepted_person_row",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
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


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt candidate review queue summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "review_queue_rows": summary.get("review_queue_rows") == 159,
        "accepted_person_rows_zero": summary.get("accepted_person_rows") == 0,
        "raw_candidate_names_false": summary.get("raw_candidate_names_committed") is False,
        "raw_person_urls_false": summary.get("raw_person_urls_committed") is False,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
        "denominator_closure_false": summary.get("denominator_closure_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected candidate review queue boundary: {checks}")
    return summary


def batch_key(row: dict[str, object]) -> str:
    lane = str(row.get("review_queue_lane") or "")
    program_key = str(row.get("program_key") or "")
    return stable_key("vanderbilt_candidate_review_batch", lane, program_key)


def required_confirmation_fields(lane: str) -> str:
    common = [
        "confirm_decision_fingerprint",
        "confirm_no_person_ingestion",
        "confirm_no_denominator_closure",
        "confirm_no_raw_name_added",
        "confirm_no_url_rewrite",
    ]
    if lane == "candidate_fingerprint_review":
        common.append("confirm_candidate_fingerprint_only")
    elif lane == "linked_scope_metadata_review":
        common.append("confirm_scope_metadata_only")
    else:
        common.append("confirm_recourse_only")
    return "; ".join(common)


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("decision_scaffold_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Candidate Review Decision Scaffold",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Candidate Review Decision Scaffold",
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
        "## Decision Scaffold Rows",
        "",
        "| priority | program | lane | status | manual row |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in rows[:200]:
        lines.append(
            "| {decision_priority} | {program_name} | {review_queue_lane} | {decision_status} | {manual_decision_row_key} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected Vanderbilt candidate review queue JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    decisions: list[dict[str, object]] = []

    for source in source_rows:
        lane = str(source.get("review_queue_lane") or "")
        bkey = batch_key(source)
        decision_fingerprint = sha256_text(
            "|".join(
                [
                    str(source.get("review_queue_key") or ""),
                    str(source.get("candidate_fingerprint_sha256") or ""),
                    str(source.get("content_sha256") or ""),
                    str(source.get("visible_text_sha256") or ""),
                    SOURCE_ROWSET_SHA256,
                ]
            )
        )
        scaffold_key = stable_key("vanderbilt_candidate_review_decision", source.get("review_queue_key"), decision_fingerprint)
        manual_key = stable_key("vanderbilt_candidate_manual_decision", scaffold_key)
        row = {
            "decision_scaffold_key": scaffold_key,
            "source_review_queue_key": source.get("review_queue_key"),
            "review_batch_key": bkey,
            "review_queue_lane": lane,
            "decision_status": "pending_non_mutating_reviewer_decision",
            "decision_priority": source.get("review_priority"),
            "program_key": source.get("program_key"),
            "program_name": source.get("program_name"),
            "candidate_fingerprint_sha256": source.get("candidate_fingerprint_sha256"),
            "candidate_source_kind": source.get("candidate_source_kind"),
            "content_sha256": source.get("content_sha256"),
            "visible_text_sha256": source.get("visible_text_sha256"),
            "allowed_reviewer_actions": source.get("allowed_reviewer_actions"),
            "required_confirmation_fields": required_confirmation_fields(lane),
            "decision_fingerprint": decision_fingerprint,
            "manual_decision_file": str(OUT_DECISIONS_CSV.relative_to(ROOT)),
            "manual_decision_row_key": manual_key,
            "accepted_person_row": "false",
            "person_ingestion_allowed": "false",
            "denominator_closure_allowed": "false",
            "evidence_json": dumps(
                {
                    "source_review_queue_rowset_sha256": SOURCE_ROWSET_SHA256,
                    "source_review_queue_key": source.get("review_queue_key"),
                    "raw_candidate_names_committed": False,
                    "raw_person_urls_committed": False,
                    "manual_decision_required": True,
                }
            ),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
        rows.append(row)
        decisions.append(
            {
                "manual_decision_row_key": manual_key,
                "decision_scaffold_key": scaffold_key,
                "review_batch_key": bkey,
                "review_queue_lane": lane,
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "candidate_fingerprint_sha256": source.get("candidate_fingerprint_sha256"),
                "candidate_source_kind": source.get("candidate_source_kind"),
                "decision_fingerprint": decision_fingerprint,
                "reviewer_action": "",
                "reviewer_note": "",
                "confirm_decision_fingerprint": "",
                "confirm_no_person_ingestion": "",
                "confirm_no_denominator_closure": "",
                "confirm_no_raw_name_added": "",
                "confirm_no_url_rewrite": "",
            }
        )

    rows.sort(key=lambda item: (-int(item["decision_priority"]), str(item["program_name"]), str(item["decision_scaffold_key"])))
    decisions.sort(key=lambda item: (str(item["review_queue_lane"]), str(item["program_name"]), str(item["manual_decision_row_key"])))
    by_lane = Counter(str(row["review_queue_lane"]) for row in rows)
    by_status = Counter(str(row["decision_status"]) for row in rows)
    by_batch = Counter(str(row["review_batch_key"]) for row in rows)
    by_program = Counter(str(row["program_name"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "manual_decisions_csv": str(OUT_DECISIONS_CSV.relative_to(ROOT)),
        "manual_decisions_json": str(OUT_DECISIONS_JSON.relative_to(ROOT)),
        "source_review_queues": str(SOURCE_JSON.relative_to(ROOT)),
        "source_review_queue_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_review_queue_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_review_queue_rows": source_summary.get("review_queue_rows"),
        "decision_scaffold_rows": len(rows),
        "manual_decision_template_rows": len(decisions),
        "review_batch_count": len(by_batch),
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "by_decision_status": dict(sorted(by_status.items())),
        "by_program_decision_rows": dict(sorted(by_program.items())),
        "accepted_person_rows": 0,
        "raw_candidate_names_committed": False,
        "raw_person_urls_committed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "mutation_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows, FIELDS)
    write_json(OUT_JSON, rows)
    write_csv(OUT_DECISIONS_CSV, decisions, DECISION_FIELDS)
    write_json(OUT_DECISIONS_JSON, decisions)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["decision_scaffold_rows", "review_batch_count", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
