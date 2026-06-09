#!/usr/bin/env python3
"""Materialize bounded Vanderbilt candidate reviewer batch packets."""

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

SCAFFOLD_JSON = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.json"
SCAFFOLD_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json"
DECISIONS_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.csv"
AUDIT_JSON = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit.json"
AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_candidate_review_batch_packets.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_candidate_review_batch_packets.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_batch_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-candidate-review-batch-packets-2026-06-09.md"

SCAFFOLD_ROWSET_SHA256 = "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"
AUDIT_ROWSET_SHA256 = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
GBRAIN_APPROVAL_LINE = "APPROVE vanderbilt_candidate_review_packet_materialization_non_mutating_approved"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt candidate reviewer batch packets. They group hash-only candidate, linked-scope, "
    "and route-recourse decision rows into bounded program/lane review packets with manual decision templates. "
    "They do not approve raw candidate labels, raw person URLs, accepted person rows, parser output as accepted "
    "people, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL "
    "rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity "
    "collapse."
)

PROHIBITED_MUTATIONS = [
    "accept_person",
    "ingest_person",
    "close_denominator",
    "collapse_identity",
    "accept_parser_output_as_people",
    "rewrite_url",
    "accept_enrichment",
    "publish_raw_name",
    "publish_raw_person_url",
    "verify_vanderbilt_school",
]

FIELDS = [
    "batch_packet_key",
    "review_batch_key",
    "execution_order",
    "review_queue_lane",
    "program_key",
    "program_name",
    "packet_status",
    "decision_row_count",
    "pending_decision_rows",
    "valid_non_mutating_decision_rows",
    "invalid_decision_rows",
    "candidate_fingerprint_review_rows",
    "linked_scope_metadata_review_rows",
    "route_recourse_review_rows",
    "source_kind_counts_json",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "manual_decision_file",
    "manual_decision_row_keys_json",
    "decision_fingerprints_json",
    "candidate_fingerprint_hashes_json",
    "content_hashes_json",
    "visible_text_hashes_json",
    "manual_decision_templates_json",
    "recommended_next_action",
    "approval_required_for",
    "prohibited_mutations",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
    "gbrain_approval_status",
    "gbrain_approval_line",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "review_batch_key",
    "execution_order",
    "review_queue_lane",
    "program_key",
    "program_name",
    "packet_status",
    "decision_row_count",
    "pending_decision_rows",
    "valid_non_mutating_decision_rows",
    "invalid_decision_rows",
    "candidate_fingerprint_review_rows",
    "linked_scope_metadata_review_rows",
    "route_recourse_review_rows",
    "source_kind_counts_json",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "manual_decision_file",
    "manual_decision_row_keys_json",
    "decision_fingerprints_json",
    "candidate_fingerprint_hashes_json",
    "content_hashes_json",
    "visible_text_hashes_json",
    "manual_decision_templates_json",
    "recommended_next_action",
    "approval_required_for",
    "prohibited_mutations",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
    "gbrain_approval_status",
    "gbrain_approval_line",
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


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def verify_source_boundary() -> tuple[dict[str, object], dict[str, object]]:
    scaffold_summary = read_json(SCAFFOLD_SUMMARY)
    audit_summary = read_json(AUDIT_SUMMARY)
    if not isinstance(scaffold_summary, dict) or not isinstance(audit_summary, dict):
        raise SystemExit("Expected Vanderbilt scaffold and reviewer decision audit summary JSON objects.")
    checks = {
        "scaffold_rowset_sha256": scaffold_summary.get("rowset_sha256") == SCAFFOLD_ROWSET_SHA256,
        "scaffold_rows": scaffold_summary.get("decision_scaffold_rows") == 159,
        "manual_template_rows": scaffold_summary.get("manual_decision_template_rows") == 159,
        "audit_rowset_sha256": audit_summary.get("rowset_sha256") == AUDIT_ROWSET_SHA256,
        "audit_rows": audit_summary.get("audit_rows") == 159,
        "accepted_person_rows_zero": audit_summary.get("accepted_person_rows") == 0,
        "person_ingestion_false": audit_summary.get("person_ingestion_allowed") is False,
        "denominator_closure_false": audit_summary.get("denominator_closure_allowed") is False,
        "mutation_allowed_false": audit_summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected Vanderbilt candidate review batch packet boundary: {checks}")
    return scaffold_summary, audit_summary


def unique_sorted(values: list[str]) -> list[str]:
    return sorted({value for value in values if value})


def split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def packet_status(counter: Counter[str]) -> str:
    invalid = counter.get("invalid", 0)
    pending = counter.get("pending", 0)
    valid = counter.get("valid_non_mutating", 0)
    if invalid:
        return "blocked_invalid_manual_decisions"
    if pending and valid:
        return "manual_review_in_progress"
    if pending:
        return "ready_for_manual_input"
    if valid:
        return "ready_for_exact_acceptance_or_closure_approval_packet"
    return "blocked_no_decision_rows"


def recommended_next_action(status: str) -> str:
    if status == "ready_for_manual_input":
        return (
            "Review this bounded Vanderbilt packet and enter only non-mutating decisions in "
            "artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit."
        )
    if status == "manual_review_in_progress":
        return "Finish remaining pending decisions, then rerun the decision audit before any approval request."
    if status == "blocked_invalid_manual_decisions":
        return "Fix invalid manual decisions and rerun the decision audit before building any approval packet."
    if status == "ready_for_exact_acceptance_or_closure_approval_packet":
        return (
            "Build a later exact approval packet from valid non-mutating reviewer decisions before accepting people, "
            "closing denominators, accepting parser output, or changing scope."
        )
    return "Regenerate the Vanderbilt decision scaffold and decision audit before review."


def manual_template(decision_row: dict[str, str], scaffold_row: dict[str, object]) -> dict[str, object]:
    template = {
        "manual_decision_row_key": decision_row.get("manual_decision_row_key", ""),
        "decision_scaffold_key": decision_row.get("decision_scaffold_key", ""),
        "decision_fingerprint": decision_row.get("decision_fingerprint", ""),
        "reviewer_action": decision_row.get("reviewer_action", ""),
        "reviewer_note_hash": sha256_text(decision_row.get("reviewer_note", "")) if decision_row.get("reviewer_note") else "",
        "allowed_reviewer_actions": split_semicolon(str(scaffold_row.get("allowed_reviewer_actions") or "")),
        "required_confirmation_fields": split_semicolon(str(scaffold_row.get("required_confirmation_fields") or "")),
    }
    for key, value in decision_row.items():
        if key.startswith("confirm_"):
            template[key] = value
    return template


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("batch_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Candidate Review Batch Packets",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Candidate Review Batch Packets",
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
        "## Batch Packets",
        "",
        "| order | program | lane | status | rows | pending | invalid | next action |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {execution_order} | {program_name} | {review_queue_lane} | {packet_status} | {decision_row_count} | {pending_decision_rows} | {invalid_decision_rows} | {recommended_next_action} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    scaffold_summary, audit_summary = verify_source_boundary()
    scaffold_rows = read_json(SCAFFOLD_JSON)
    audit_rows = read_json(AUDIT_JSON)
    decision_rows = read_csv_rows(DECISIONS_CSV)
    if not isinstance(scaffold_rows, list) or not isinstance(audit_rows, list):
        raise SystemExit("Expected Vanderbilt scaffold and audit JSON arrays.")

    scaffold_by_manual_key = {str(row.get("manual_decision_row_key")): row for row in scaffold_rows}
    audit_by_manual_key = {str(row.get("manual_decision_row_key")): row for row in audit_rows}
    decisions_by_manual_key = {row.get("manual_decision_row_key", ""): row for row in decision_rows}
    expected_keys = set(scaffold_by_manual_key)
    if expected_keys != set(audit_by_manual_key) or expected_keys != set(decisions_by_manual_key):
        raise SystemExit("Vanderbilt batch packet source key sets do not match scaffold/audit/manual decisions.")

    generated_at = datetime.now(timezone.utc).isoformat()
    by_batch: dict[str, list[dict[str, object]]] = defaultdict(list)
    for scaffold_row in scaffold_rows:
        by_batch[str(scaffold_row.get("review_batch_key"))].append(scaffold_row)

    rows: list[dict[str, object]] = []
    for order, (batch_key, batch_rows) in enumerate(
        sorted(
            by_batch.items(),
            key=lambda item: (
                str(item[1][0].get("review_queue_lane") or ""),
                str(item[1][0].get("program_name") or ""),
                str(item[0]),
            ),
        ),
        start=1,
    ):
        audit_counter = Counter(
            str(audit_by_manual_key[str(row.get("manual_decision_row_key"))].get("audit_status") or "")
            for row in batch_rows
        )
        lane_counter = Counter(str(row.get("review_queue_lane") or "") for row in batch_rows)
        source_kind_counter = Counter(str(row.get("candidate_source_kind") or "") for row in batch_rows)
        status = packet_status(audit_counter)
        manual_keys = [str(row.get("manual_decision_row_key") or "") for row in batch_rows]
        decision_rows_for_batch = [decisions_by_manual_key[key] for key in manual_keys]
        templates = [manual_template(decisions_by_manual_key[key], scaffold_by_manual_key[key]) for key in manual_keys]
        first = batch_rows[0]
        row = {
            "batch_packet_key": stable_key("vanderbilt_candidate_review_batch_packet", batch_key, AUDIT_ROWSET_SHA256),
            "review_batch_key": batch_key,
            "execution_order": order,
            "review_queue_lane": first.get("review_queue_lane", ""),
            "program_key": first.get("program_key", ""),
            "program_name": first.get("program_name", ""),
            "packet_status": status,
            "decision_row_count": len(batch_rows),
            "pending_decision_rows": audit_counter.get("pending", 0),
            "valid_non_mutating_decision_rows": audit_counter.get("valid_non_mutating", 0),
            "invalid_decision_rows": audit_counter.get("invalid", 0),
            "candidate_fingerprint_review_rows": lane_counter.get("candidate_fingerprint_review", 0),
            "linked_scope_metadata_review_rows": lane_counter.get("linked_scope_metadata_review", 0),
            "route_recourse_review_rows": lane_counter.get("route_recourse_review", 0),
            "source_kind_counts_json": dumps(dict(sorted(source_kind_counter.items()))),
            "allowed_reviewer_actions": "; ".join(
                unique_sorted([action for row_item in batch_rows for action in split_semicolon(str(row_item.get("allowed_reviewer_actions") or ""))])
            ),
            "required_confirmation_fields": "; ".join(
                unique_sorted(
                    [
                        field
                        for row_item in batch_rows
                        for field in split_semicolon(str(row_item.get("required_confirmation_fields") or ""))
                    ]
                )
            ),
            "manual_decision_file": "artifacts/data/vanderbilt_candidate_reviewer_decisions.csv",
            "manual_decision_row_keys_json": dumps(manual_keys),
            "decision_fingerprints_json": dumps([row.get("decision_fingerprint", "") for row in batch_rows]),
            "candidate_fingerprint_hashes_json": dumps(
                unique_sorted([str(row.get("candidate_fingerprint_sha256") or "") for row in batch_rows])
            ),
            "content_hashes_json": dumps(unique_sorted([str(row.get("content_sha256") or "") for row in batch_rows])),
            "visible_text_hashes_json": dumps(
                unique_sorted([str(row.get("visible_text_sha256") or "") for row in batch_rows])
            ),
            "manual_decision_templates_json": dumps(templates),
            "recommended_next_action": recommended_next_action(status),
            "approval_required_for": "; ".join(
                [
                    "accepted_person_rows",
                    "person_ingestion",
                    "denominator_closure",
                    "identity_reconciliation",
                    "parser_acceptance",
                    "scope_closure",
                    "url_rewrite",
                    "enrichment_acceptance",
                ]
            ),
            "prohibited_mutations": "; ".join(PROHIBITED_MUTATIONS),
            "accepted_person_rows": 0,
            "person_ingestion_allowed": "false",
            "denominator_closure_allowed": "false",
            "raw_candidate_names_committed": "false",
            "raw_person_urls_committed": "false",
            "gbrain_approval_status": "approved_non_mutating_batch_packet_materialization",
            "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
            "evidence_json": dumps(
                {
                    "source_decision_scaffold_rowset_sha256": SCAFFOLD_ROWSET_SHA256,
                    "source_reviewer_decision_audit_rowset_sha256": AUDIT_ROWSET_SHA256,
                    "source_decision_scaffold_rows": scaffold_summary.get("decision_scaffold_rows"),
                    "source_audit_rows": audit_summary.get("audit_rows"),
                    "manual_decision_rows": len(decision_rows_for_batch),
                    "raw_candidate_names_committed": False,
                    "raw_person_urls_committed": False,
                }
            ),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
        rows.append(row)

    by_status = Counter(str(row["packet_status"]) for row in rows)
    by_lane = Counter(str(row["review_queue_lane"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_decision_scaffold": str(SCAFFOLD_JSON.relative_to(ROOT)),
        "source_decision_scaffold_summary": str(SCAFFOLD_SUMMARY.relative_to(ROOT)),
        "source_decision_scaffold_rowset_sha256": SCAFFOLD_ROWSET_SHA256,
        "source_reviewer_decision_audit": str(AUDIT_JSON.relative_to(ROOT)),
        "source_reviewer_decision_audit_summary": str(AUDIT_SUMMARY.relative_to(ROOT)),
        "source_reviewer_decision_audit_rowset_sha256": AUDIT_ROWSET_SHA256,
        "manual_decisions_csv": str(DECISIONS_CSV.relative_to(ROOT)),
        "batch_packet_rows": len(rows),
        "decision_row_count": sum(int(row["decision_row_count"]) for row in rows),
        "pending_decision_rows": sum(int(row["pending_decision_rows"]) for row in rows),
        "valid_non_mutating_decision_rows": sum(int(row["valid_non_mutating_decision_rows"]) for row in rows),
        "invalid_decision_rows": sum(int(row["invalid_decision_rows"]) for row in rows),
        "by_packet_status": dict(sorted(by_status.items())),
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "accepted_person_rows": 0,
        "raw_candidate_names_committed": False,
        "raw_person_urls_committed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "mutation_allowed": False,
        "gbrain_approval_status": "approved_non_mutating_batch_packet_materialization",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(
        json.dumps(
            {key: summary[key] for key in ["batch_packet_rows", "decision_row_count", "pending_decision_rows", "rowset_sha256"]},
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
