#!/usr/bin/env python3
"""Materialize approved non-mutating Vanderbilt candidate review queues."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SOURCE_JSON = ARTIFACTS / "vanderbilt_candidate_review_queue_approval_packet.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_queue_approval_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_candidate_review_queues.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_candidate_review_queues.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_queue_summary.json"
OUT_MD = RESEARCH / "vanderbilt-candidate-review-queues-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "a62defd685b64560a138cfaeb82956254f49341ce982bb549fe1846b25dd5bd5"
APPROVAL_LINE = (
    "APPROVE vanderbilt_candidate_review_queue_materialization_approved APPROVAL_ROWS 159 "
    "CANDIDATE_QUEUE_ROWS 155 SCOPE_QUEUE_ROWS 3 RECOURSE_QUEUE_ROWS 1 "
    "SOURCE_ROWSET_SHA256 2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba "
    "VERIFICATION_ROWSET_SHA256 918556f5b5a33b5d8e7181ed6654a9b7773b8c8a24f09f9a23b06c7157d39fe2 "
    "ROWSET_SHA256 a62defd685b64560a138cfaeb82956254f49341ce982bb549fe1846b25dd5bd5"
)

MUTATION_POLICY = (
    "Approved non-mutating Vanderbilt candidate review queues. Queue rows contain candidate/program/source hashes, "
    "source kind, route hashes, scope status, and recourse status only. They contain no raw candidate labels, raw "
    "person URLs, accepted person rows, person ingestion, training-state mutation, denominator closure, Vanderbilt "
    "school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or "
    "unique-person identity collapse."
)

FIELDS = [
    "review_queue_key",
    "source_approval_packet_key",
    "review_queue_lane",
    "queue_status",
    "review_priority",
    "program_key",
    "program_name",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "content_sha256",
    "visible_text_sha256",
    "review_prompt",
    "allowed_reviewer_actions",
    "prohibited_reviewer_actions",
    "accepted_person_row",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_approval_packet_key",
    "review_queue_lane",
    "queue_status",
    "review_priority",
    "program_key",
    "program_name",
    "candidate_fingerprint_sha256",
    "candidate_source_kind",
    "content_sha256",
    "visible_text_sha256",
    "review_prompt",
    "allowed_reviewer_actions",
    "prohibited_reviewer_actions",
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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt candidate review queue approval summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "approval_rows": summary.get("approval_rows") == 159,
        "approval_status": summary.get("gbrain_approval_status")
        == "approved_exact_non_mutating_review_queue_materialization",
        "queue_allowed": summary.get("queue_materialization_allowed") is True,
        "approval_line": summary.get("required_approval_line") == APPROVAL_LINE,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected review queue approval boundary: {checks}")
    return summary


def classify(row: dict[str, object]) -> tuple[str, str, int, str, str]:
    lane = str(row.get("approval_request_lane") or "")
    if lane == "candidate_fingerprint_review_queue":
        return (
            "candidate_fingerprint_review",
            "ready_for_human_candidate_identity_review_no_ingestion",
            90,
            "Review hashed candidate fingerprint context against official source evidence; request exact person-ingestion approval separately if warranted.",
            "mark_for_later_exact_person_review; mark_duplicate_hash_for_reconciliation; reject_candidate_hash_as_parser_noise",
        )
    if lane == "linked_scope_metadata_review_queue":
        return (
            "linked_scope_metadata_review",
            "ready_for_scope_routing_review_no_url_rewrite",
            70,
            "Review linked-route scope metadata for same-program/shared-source routing without URL rewrite or denominator closure.",
            "mark_same_program_scope_candidate; mark_shared_source_context; mark_scope_recourse_needed",
        )
    return (
        "route_recourse_review",
        "ready_for_route_replacement_review_no_closure",
        60,
        "Review Orthopaedic route recourse and find/verify replacement official source without closing the gap.",
        "mark_retry_needed; mark_replacement_source_candidate; mark_unresolved_without_closure",
    )


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("review_queue_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Candidate Review Queues",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Candidate Review Queues",
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
        "## Queue Rows",
        "",
        "| priority | program | lane | status | accepted person |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for row in rows[:200]:
        lines.append(
            "| {review_priority} | {program_name} | {review_queue_lane} | {queue_status} | {accepted_person_row} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected Vanderbilt candidate review queue approval JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in source_rows:
        lane, status, priority, prompt, allowed_actions = classify(source)
        rows.append(
            {
                "review_queue_key": stable_key("vanderbilt_candidate_review_queue", source.get("approval_packet_key"), lane),
                "source_approval_packet_key": source.get("approval_packet_key"),
                "review_queue_lane": lane,
                "queue_status": status,
                "review_priority": priority,
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "candidate_fingerprint_sha256": source.get("candidate_fingerprint_sha256"),
                "candidate_source_kind": source.get("candidate_source_kind"),
                "content_sha256": source.get("content_sha256"),
                "visible_text_sha256": source.get("visible_text_sha256"),
                "review_prompt": prompt,
                "allowed_reviewer_actions": allowed_actions,
                "prohibited_reviewer_actions": (
                    "accept_person; ingest_person; close_denominator; rewrite_url; accept_enrichment; publish_raw_name; "
                    "publish_raw_person_url; collapse_identity"
                ),
                "accepted_person_row": "false",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "evidence_json": dumps(
                    {
                        "source_review_queue_approval_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "source_approval_packet_key": source.get("approval_packet_key"),
                        "next_artifact_if_approved": source.get("next_artifact_if_approved"),
                        "raw_candidate_labels_committed": False,
                        "raw_person_urls_committed": False,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (-int(item["review_priority"]), str(item["program_name"]), str(item["review_queue_key"])))
    by_lane = Counter(str(row["review_queue_lane"]) for row in rows)
    by_status = Counter(str(row["queue_status"]) for row in rows)
    by_program = Counter(str(row["program_name"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_review_queue_approval_packet": str(SOURCE_JSON.relative_to(ROOT)),
        "source_review_queue_approval_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_review_queue_approval_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_approval_rows": source_summary.get("approval_rows"),
        "review_queue_rows": len(rows),
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "by_queue_status": dict(sorted(by_status.items())),
        "by_program_queue_rows": dict(sorted(by_program.items())),
        "mutation_allowed": False,
        "accepted_person_rows": 0,
        "raw_candidate_names_committed": False,
        "raw_person_urls_committed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["review_queue_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
