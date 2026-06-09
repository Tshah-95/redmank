#!/usr/bin/env python3
"""Materialize public-safe Vanderbilt reviewer operator packets."""

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

BATCH_CSV = ARTIFACTS / "vanderbilt_candidate_review_batch_packets.csv"
BATCH_JSON = ARTIFACTS / "vanderbilt_candidate_review_batch_packets.json"
BATCH_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_batch_packet_summary.json"
DECISIONS_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.csv"
AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"
SCAFFOLD_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_public_reviewer_operator_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-public-reviewer-operator-packets-2026-06-09.md"

BATCH_PACKET_ROWSET_SHA256 = "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f"
DECISION_AUDIT_ROWSET_SHA256 = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
SCAFFOLD_ROWSET_SHA256 = "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"
SOURCE_GBRAIN_APPROVAL_LINE = "APPROVE vanderbilt_candidate_review_packet_materialization_non_mutating_approved"

MUTATION_POLICY = (
    "Public-safe Vanderbilt reviewer operator packets. They are a non-mutating runbook layer over the approved "
    "Vanderbilt candidate review batch packets and the hardened blank manual decision template. They do not fill "
    "reviewer decisions, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite "
    "URLs, publish raw candidate labels or raw person URLs, accept enrichment facts, or collapse identities."
)

PROHIBITED_MUTATIONS = [
    "fill_reviewer_decisions_without_operator_action",
    "accept_person",
    "ingest_person",
    "close_denominator",
    "verify_vanderbilt_school",
    "rewrite_url",
    "publish_raw_candidate_label",
    "publish_raw_person_url",
    "accept_enrichment",
    "collapse_identity",
]

FIELDS = [
    "operator_packet_key",
    "source_batch_packet_key",
    "execution_order",
    "review_queue_lane",
    "program_key",
    "program_name",
    "operator_packet_status",
    "decision_row_count",
    "pending_decision_rows",
    "valid_non_mutating_decision_rows",
    "invalid_decision_rows",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "manual_decision_file",
    "manual_decision_row_keys_json",
    "template_columns_present_json",
    "missing_template_columns_json",
    "operator_steps_json",
    "verification_command",
    "approval_required_for",
    "prohibited_mutations",
    "source_batch_packet_rowset_sha256",
    "source_decision_audit_rowset_sha256",
    "source_scaffold_rowset_sha256",
    "source_gbrain_approval_line",
    "new_gbrain_approval_status",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_batch_packet_key",
    "execution_order",
    "review_queue_lane",
    "program_key",
    "program_name",
    "operator_packet_status",
    "decision_row_count",
    "pending_decision_rows",
    "valid_non_mutating_decision_rows",
    "invalid_decision_rows",
    "allowed_reviewer_actions",
    "required_confirmation_fields",
    "manual_decision_file",
    "manual_decision_row_keys_json",
    "template_columns_present_json",
    "missing_template_columns_json",
    "operator_steps_json",
    "verification_command",
    "approval_required_for",
    "prohibited_mutations",
    "source_batch_packet_rowset_sha256",
    "source_decision_audit_rowset_sha256",
    "source_scaffold_rowset_sha256",
    "source_gbrain_approval_line",
    "new_gbrain_approval_status",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "raw_candidate_names_committed",
    "raw_person_urls_committed",
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


def split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split(";") if part.strip()]


def verify_source_boundary() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    batch_summary = read_json(BATCH_SUMMARY)
    audit_summary = read_json(AUDIT_SUMMARY)
    scaffold_summary = read_json(SCAFFOLD_SUMMARY)
    if not all(isinstance(summary, dict) for summary in [batch_summary, audit_summary, scaffold_summary]):
        raise SystemExit("Expected Vanderbilt batch, audit, and scaffold summary JSON objects.")
    checks = {
        "batch_rowset": batch_summary.get("rowset_sha256") == BATCH_PACKET_ROWSET_SHA256,
        "batch_rows": batch_summary.get("batch_packet_rows") == 20,
        "batch_pending": batch_summary.get("pending_decision_rows") == 159,
        "batch_invalid_zero": batch_summary.get("invalid_decision_rows") == 0,
        "batch_mutation_false": batch_summary.get("mutation_allowed") is False,
        "audit_rowset": audit_summary.get("rowset_sha256") == DECISION_AUDIT_ROWSET_SHA256,
        "audit_pending": audit_summary.get("pending_rows") == 159,
        "audit_invalid_zero": audit_summary.get("invalid_rows") == 0,
        "scaffold_rowset": scaffold_summary.get("rowset_sha256") == SCAFFOLD_ROWSET_SHA256,
        "scaffold_rows": scaffold_summary.get("decision_scaffold_rows") == 159,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected Vanderbilt public reviewer operator source boundary: {checks}")
    return batch_summary, audit_summary, scaffold_summary


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("operator_packet_key", "")))
    ]
    return sha256_text(dumps(material))


def operator_status(row: dict[str, str], missing_columns: list[str]) -> str:
    if missing_columns:
        return "blocked_missing_required_template_columns"
    if int(row.get("invalid_decision_rows", 0)):
        return "blocked_invalid_manual_decisions"
    if int(row.get("pending_decision_rows", 0)):
        return "ready_for_blank_template_manual_review"
    return "ready_for_later_exact_acceptance_or_closure_packet"


def operator_steps(row: dict[str, str]) -> list[str]:
    return [
        "Open the batch packet row for this program and lane.",
        "Review only the hash-level candidate, scope, or recourse evidence already committed in the packet.",
        "Fill reviewer_action only with one of the allowed actions for that row.",
        "Copy decision_fingerprint into confirm_decision_fingerprint and set every boolean safety confirmation to true.",
        "Set the required lane-specific boolean confirmation to true.",
        "Do not add raw candidate names, raw person URLs, acceptance claims, denominator closure, or URL rewrites.",
        "Run python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py.",
    ]


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Public Reviewer Operator Packets",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Public Reviewer Operator Packets",
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
        "## Operator Packets",
        "",
        "| order | program | lane | status | rows | pending | missing columns |",
        "| ---: | --- | --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {execution_order} | {program_name} | {review_queue_lane} | {operator_packet_status} | {decision_row_count} | {pending_decision_rows} | `{missing_template_columns_json}` |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    batch_summary, audit_summary, scaffold_summary = verify_source_boundary()
    batch_rows = read_csv_rows(BATCH_CSV)
    batch_json = read_json(BATCH_JSON)
    decision_rows = read_csv_rows(DECISIONS_CSV)
    if not isinstance(batch_json, list):
        raise SystemExit("Expected Vanderbilt batch packet JSON array.")
    if len(batch_rows) != len(batch_json) != 20:
        raise SystemExit("Vanderbilt batch packet CSV/JSON row counts do not match 20.")

    decision_columns = set(decision_rows[0]) if decision_rows else set()
    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for source in batch_rows:
        required_fields = split_semicolon(source.get("required_confirmation_fields", ""))
        missing_columns = [field for field in required_fields if field not in decision_columns]
        status = operator_status(source, missing_columns)
        row = {
            "operator_packet_key": stable_key(
                "vanderbilt_public_reviewer_operator_packet",
                source.get("batch_packet_key"),
                BATCH_PACKET_ROWSET_SHA256,
            ),
            "source_batch_packet_key": source.get("batch_packet_key", ""),
            "execution_order": source.get("execution_order", ""),
            "review_queue_lane": source.get("review_queue_lane", ""),
            "program_key": source.get("program_key", ""),
            "program_name": source.get("program_name", ""),
            "operator_packet_status": status,
            "decision_row_count": source.get("decision_row_count", "0"),
            "pending_decision_rows": source.get("pending_decision_rows", "0"),
            "valid_non_mutating_decision_rows": source.get("valid_non_mutating_decision_rows", "0"),
            "invalid_decision_rows": source.get("invalid_decision_rows", "0"),
            "allowed_reviewer_actions": source.get("allowed_reviewer_actions", ""),
            "required_confirmation_fields": source.get("required_confirmation_fields", ""),
            "manual_decision_file": source.get("manual_decision_file", str(DECISIONS_CSV.relative_to(ROOT))),
            "manual_decision_row_keys_json": source.get("manual_decision_row_keys_json", "[]"),
            "template_columns_present_json": dumps({field: field in decision_columns for field in required_fields}),
            "missing_template_columns_json": dumps(missing_columns),
            "operator_steps_json": dumps(operator_steps(source)),
            "verification_command": (
                "python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py && "
                "python3 scripts/materialize_vanderbilt_candidate_review_batch_packets.py && "
                "python3 scripts/materialize_vanderbilt_public_reviewer_operator_packets.py"
            ),
            "approval_required_for": (
                "accepted_person_rows; person_ingestion; denominator_closure; parser_acceptance; "
                "scope_closure; url_rewrite; enrichment_acceptance; identity_collapse"
            ),
            "prohibited_mutations": "; ".join(PROHIBITED_MUTATIONS),
            "source_batch_packet_rowset_sha256": BATCH_PACKET_ROWSET_SHA256,
            "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET_SHA256,
            "source_scaffold_rowset_sha256": SCAFFOLD_ROWSET_SHA256,
            "source_gbrain_approval_line": SOURCE_GBRAIN_APPROVAL_LINE,
            "new_gbrain_approval_status": "no_new_approval_line_claimed_retrieval_consulted_only",
            "accepted_person_rows": 0,
            "person_ingestion_allowed": "false",
            "denominator_closure_allowed": "false",
            "raw_candidate_names_committed": "false",
            "raw_person_urls_committed": "false",
            "evidence_json": dumps(
                {
                    "source_batch_packet_rowset_sha256": BATCH_PACKET_ROWSET_SHA256,
                    "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET_SHA256,
                    "source_scaffold_rowset_sha256": SCAFFOLD_ROWSET_SHA256,
                    "source_batch_rows": batch_summary.get("batch_packet_rows"),
                    "source_audit_rows": audit_summary.get("audit_rows"),
                    "source_scaffold_rows": scaffold_summary.get("decision_scaffold_rows"),
                    "missing_required_template_columns": missing_columns,
                }
            ),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
        rows.append(row)

    by_status = Counter(str(row["operator_packet_status"]) for row in rows)
    by_lane = Counter(str(row["review_queue_lane"]) for row in rows)
    missing_total = sum(len(json.loads(str(row["missing_template_columns_json"]))) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_batch_packets": str(BATCH_CSV.relative_to(ROOT)),
        "source_batch_packet_summary": str(BATCH_SUMMARY.relative_to(ROOT)),
        "source_batch_packet_rowset_sha256": BATCH_PACKET_ROWSET_SHA256,
        "source_decision_audit_summary": str(AUDIT_SUMMARY.relative_to(ROOT)),
        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET_SHA256,
        "source_scaffold_summary": str(SCAFFOLD_SUMMARY.relative_to(ROOT)),
        "source_scaffold_rowset_sha256": SCAFFOLD_ROWSET_SHA256,
        "manual_decisions_csv": str(DECISIONS_CSV.relative_to(ROOT)),
        "operator_packet_rows": len(rows),
        "decision_row_count": sum(int(row["decision_row_count"]) for row in rows),
        "pending_decision_rows": sum(int(row["pending_decision_rows"]) for row in rows),
        "valid_non_mutating_decision_rows": sum(int(row["valid_non_mutating_decision_rows"]) for row in rows),
        "invalid_decision_rows": sum(int(row["invalid_decision_rows"]) for row in rows),
        "missing_required_template_column_mentions": missing_total,
        "by_operator_packet_status": dict(sorted(by_status.items())),
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "accepted_person_rows": 0,
        "raw_candidate_names_committed": False,
        "raw_person_urls_committed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "mutation_allowed": False,
        "source_gbrain_approval_line": SOURCE_GBRAIN_APPROVAL_LINE,
        "new_gbrain_approval_status": "no_new_approval_line_claimed_retrieval_consulted_only",
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["operator_packet_rows", "missing_required_template_column_mentions", "rowset_sha256"]}, sort_keys=True))
    if missing_total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
