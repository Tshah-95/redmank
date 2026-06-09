#!/usr/bin/env python3
"""Bridge candidate-output coverage to Vanderbilt review queues and decisions."""

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

CANDIDATE_OUTPUT_BRIDGE_CSV = ARTIFACTS / "school_gap_resolution_candidate_output_bridge.csv"
CANDIDATE_OUTPUT_BRIDGE_SUMMARY = ARTIFACTS / "school_gap_resolution_candidate_output_bridge_summary.json"
QUEUE_APPROVAL_CSV = ARTIFACTS / "vanderbilt_candidate_review_queue_approval_packet.csv"
QUEUE_APPROVAL_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_queue_approval_packet_summary.json"
REVIEW_QUEUE_CSV = ARTIFACTS / "vanderbilt_candidate_review_queues.csv"
REVIEW_QUEUE_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_queue_summary.json"
DECISION_SCAFFOLD_CSV = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.csv"
DECISION_SCAFFOLD_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json"
SCAFFOLD_VERIFICATION_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_scaffold_verification_summary.json"
DECISION_AUDIT_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit.csv"
DECISION_AUDIT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"

OUT_CSV = ARTIFACTS / "school_gap_resolution_review_queue_bridge.csv"
OUT_JSON = ARTIFACTS / "school_gap_resolution_review_queue_bridge.json"
OUT_SUMMARY = ARTIFACTS / "school_gap_resolution_review_queue_bridge_summary.json"
OUT_MD = RESEARCH / "school-gap-resolution-review-queue-bridge-2026-06-09.md"

CANDIDATE_OUTPUT_BRIDGE_ROWSET = "dfb141c1883d85fd6a8c7c0e015b939414788936eb13dbb04eecb9111ff5b843"
QUEUE_APPROVAL_ROWSET = "a62defd685b64560a138cfaeb82956254f49341ce982bb549fe1846b25dd5bd5"
REVIEW_QUEUE_ROWSET = "b74b337bfa43406d8a200956d469eb5dc0d41902c197f78af85001f18750b148"
DECISION_SCAFFOLD_ROWSET = "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"
SCAFFOLD_VERIFICATION_ROWSET = "24e03f71174cd456b4783457113d64d4b15185721fc86092ca2a5f47e7eb4260"
DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"

MUTATION_POLICY = (
    "Non-mutating bridge from Vanderbilt candidate-output coverage to review queues, decision scaffolds, and pending "
    "manual-decision audit rows. It records reviewer-decision readiness only. It does not fill reviewer decisions, "
    "accept people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, "
    "or collapse identities."
)

FIELDS = [
    "review_queue_bridge_key",
    "gap_key",
    "program_key",
    "program_name",
    "candidate_output_status",
    "candidate_output_rows",
    "queue_approval_rows",
    "review_queue_rows",
    "decision_scaffold_rows",
    "manual_decision_audit_rows",
    "pending_decision_rows",
    "valid_non_mutating_decision_rows",
    "invalid_decision_rows",
    "review_queue_bridge_status",
    "review_queue_coverage_status",
    "next_required_approval",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]
ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"review_queue_bridge_key", "evidence_json", "mutation_policy", "generated_at"}
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


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("review_queue_bridge_key", "")))
    ]
    return sha256_text(dumps(material))


def verify_boundaries() -> None:
    candidate_bridge = read_json(CANDIDATE_OUTPUT_BRIDGE_SUMMARY)
    queue_approval = read_json(QUEUE_APPROVAL_SUMMARY)
    review_queue = read_json(REVIEW_QUEUE_SUMMARY)
    scaffold = read_json(DECISION_SCAFFOLD_SUMMARY)
    scaffold_verification = read_json(SCAFFOLD_VERIFICATION_SUMMARY)
    audit = read_json(DECISION_AUDIT_SUMMARY)
    if not all(
        isinstance(item, dict)
        for item in [candidate_bridge, queue_approval, review_queue, scaffold, scaffold_verification, audit]
    ):
        raise SystemExit("Expected review-queue bridge source summaries to be JSON objects.")
    checks = {
        "candidate_bridge": candidate_bridge.get("rowset_sha256") == CANDIDATE_OUTPUT_BRIDGE_ROWSET
        and candidate_bridge.get("bridge_rows") == 19
        and candidate_bridge.get("candidate_output_rows_represented") == 159
        and candidate_bridge.get("mutation_allowed") is False
        and candidate_bridge.get("person_ingestion_allowed") is False,
        "queue_approval": queue_approval.get("rowset_sha256") == QUEUE_APPROVAL_ROWSET
        and queue_approval.get("approval_rows") == 159
        and queue_approval.get("gbrain_approval_status") == "approved_exact_non_mutating_review_queue_materialization"
        and queue_approval.get("person_ingestion_allowed") is False,
        "review_queue": review_queue.get("rowset_sha256") == REVIEW_QUEUE_ROWSET
        and review_queue.get("review_queue_rows") == 159
        and review_queue.get("accepted_person_rows") == 0
        and review_queue.get("person_ingestion_allowed") is False,
        "decision_scaffold": scaffold.get("rowset_sha256") == DECISION_SCAFFOLD_ROWSET
        and scaffold.get("decision_scaffold_rows") == 159
        and scaffold.get("manual_decision_template_rows") == 159
        and scaffold.get("accepted_person_rows") == 0
        and scaffold.get("person_ingestion_allowed") is False,
        "scaffold_verification": scaffold_verification.get("rowset_sha256") == SCAFFOLD_VERIFICATION_ROWSET
        and scaffold_verification.get("verification_rows") == 7
        and scaffold_verification.get("pass_rows") == 7
        and scaffold_verification.get("fail_rows") == 0,
        "decision_audit": audit.get("rowset_sha256") == DECISION_AUDIT_ROWSET
        and audit.get("audit_rows") == 159
        and audit.get("pending_rows") == 159
        and audit.get("valid_non_mutating_rows") == 0
        and audit.get("invalid_rows") == 0
        and audit.get("accepted_person_rows") == 0,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected review-queue bridge source boundary: " + dumps(checks))


def index_by_program(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    by_program: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_program[row.get("program_key", "")].append(row)
    return dict(by_program)


def status_for(counts: dict[str, int]) -> tuple[str, str, str]:
    if counts["queue_approval"] == 0:
        return "missing_review_queue_approval", "not_ready_for_review_queue", "exact_review_queue_materialization_approval_required"
    if counts["review_queue"] == 0:
        return "queue_approved_not_materialized", "review_queue_materialization_missing", "materialize_review_queue_rows"
    if counts["scaffold"] == 0:
        return "queue_materialized_no_decision_scaffold", "decision_scaffold_missing", "materialize_decision_scaffold"
    if counts["audit"] == 0:
        return "decision_scaffold_not_audited", "manual_decision_audit_missing", "run_reviewer_decision_audit"
    return (
        "pending_reviewer_decisions_ready",
        "covered_by_review_queue_scaffold_and_pending_audit",
        "exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required",
    )


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    lines = [
        "---",
        "type: research-checkpoint",
        "title: School Gap Resolution Review Queue Bridge",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# School Gap Resolution Review Queue Bridge",
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
        "## Bridge Rows",
        "",
        "| program | bridge status | queue | scaffold | pending | next approval |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {program_name} | {review_queue_bridge_status} | {review_queue_rows} | {decision_scaffold_rows} | {pending_decision_rows} | {next_required_approval} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    verify_boundaries()
    candidate_bridge_rows = read_csv_rows(CANDIDATE_OUTPUT_BRIDGE_CSV)
    queue_approval_by_program = index_by_program(read_csv_rows(QUEUE_APPROVAL_CSV))
    review_queue_by_program = index_by_program(read_csv_rows(REVIEW_QUEUE_CSV))
    scaffold_by_program = index_by_program(read_csv_rows(DECISION_SCAFFOLD_CSV))
    audit_by_program = index_by_program(read_csv_rows(DECISION_AUDIT_CSV))
    if len(candidate_bridge_rows) != 19:
        raise SystemExit("Expected exactly 19 candidate-output bridge rows.")

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for bridge in sorted(candidate_bridge_rows, key=lambda item: (item.get("program_name", ""), item.get("gap_key", ""))):
        program_key = bridge.get("program_key", "")
        queue_approval_rows = queue_approval_by_program.get(program_key, [])
        review_queue_rows = review_queue_by_program.get(program_key, [])
        scaffold_rows = scaffold_by_program.get(program_key, [])
        audit_rows = audit_by_program.get(program_key, [])
        pending_rows = [row for row in audit_rows if row.get("audit_status") == "pending"]
        valid_rows = [row for row in audit_rows if row.get("audit_status") == "valid_non_mutating"]
        invalid_rows = [row for row in audit_rows if row.get("audit_status") == "invalid"]
        counts = {
            "queue_approval": len(queue_approval_rows),
            "review_queue": len(review_queue_rows),
            "scaffold": len(scaffold_rows),
            "audit": len(audit_rows),
        }
        status, coverage, next_approval = status_for(counts)
        lanes = sorted({row.get("review_queue_lane", "") for row in review_queue_rows if row.get("review_queue_lane")})
        rows.append(
            {
                "review_queue_bridge_key": stable_key(
                    "school_gap_resolution_review_queue_bridge",
                    bridge.get("candidate_output_bridge_key", ""),
                    program_key,
                ),
                "gap_key": bridge.get("gap_key", ""),
                "program_key": program_key,
                "program_name": bridge.get("program_name", ""),
                "candidate_output_status": bridge.get("candidate_output_status", ""),
                "candidate_output_rows": bridge.get("candidate_output_rows", "0"),
                "queue_approval_rows": len(queue_approval_rows),
                "review_queue_rows": len(review_queue_rows),
                "decision_scaffold_rows": len(scaffold_rows),
                "manual_decision_audit_rows": len(audit_rows),
                "pending_decision_rows": len(pending_rows),
                "valid_non_mutating_decision_rows": len(valid_rows),
                "invalid_decision_rows": len(invalid_rows),
                "review_queue_bridge_status": status,
                "review_queue_coverage_status": coverage,
                "next_required_approval": next_approval,
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "evidence_json": dumps(
                    {
                        "source_candidate_output_bridge_rowset_sha256": CANDIDATE_OUTPUT_BRIDGE_ROWSET,
                        "source_queue_approval_rowset_sha256": QUEUE_APPROVAL_ROWSET,
                        "source_review_queue_rowset_sha256": REVIEW_QUEUE_ROWSET,
                        "source_decision_scaffold_rowset_sha256": DECISION_SCAFFOLD_ROWSET,
                        "source_scaffold_verification_rowset_sha256": SCAFFOLD_VERIFICATION_ROWSET,
                        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
                        "review_queue_lanes": lanes,
                        "queue_approval_keys": [row.get("approval_packet_key", "") for row in queue_approval_rows],
                        "review_queue_keys": [row.get("review_queue_key", "") for row in review_queue_rows],
                        "decision_scaffold_keys": [row.get("decision_scaffold_key", "") for row in scaffold_rows],
                        "candidate_evidence_only": True,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    by_status = Counter(str(row["review_queue_bridge_status"]) for row in rows)
    by_coverage = Counter(str(row["review_queue_coverage_status"]) for row in rows)
    by_next = Counter(str(row["next_required_approval"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_candidate_output_bridge_rowset_sha256": CANDIDATE_OUTPUT_BRIDGE_ROWSET,
        "source_queue_approval_rowset_sha256": QUEUE_APPROVAL_ROWSET,
        "source_review_queue_rowset_sha256": REVIEW_QUEUE_ROWSET,
        "source_decision_scaffold_rowset_sha256": DECISION_SCAFFOLD_ROWSET,
        "source_scaffold_verification_rowset_sha256": SCAFFOLD_VERIFICATION_ROWSET,
        "source_decision_audit_rowset_sha256": DECISION_AUDIT_ROWSET,
        "bridge_rows": len(rows),
        "candidate_output_rows_represented": sum(int(row["candidate_output_rows"]) for row in rows),
        "queue_approval_rows_represented": sum(int(row["queue_approval_rows"]) for row in rows),
        "review_queue_rows_represented": sum(int(row["review_queue_rows"]) for row in rows),
        "decision_scaffold_rows_represented": sum(int(row["decision_scaffold_rows"]) for row in rows),
        "manual_decision_audit_rows_represented": sum(int(row["manual_decision_audit_rows"]) for row in rows),
        "pending_decision_rows_represented": sum(int(row["pending_decision_rows"]) for row in rows),
        "valid_non_mutating_decision_rows_represented": sum(int(row["valid_non_mutating_decision_rows"]) for row in rows),
        "invalid_decision_rows_represented": sum(int(row["invalid_decision_rows"]) for row in rows),
        "by_review_queue_bridge_status": dict(sorted(by_status.items())),
        "by_review_queue_coverage_status": dict(sorted(by_coverage.items())),
        "by_next_required_approval": dict(sorted(by_next.items())),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    if (
        summary["bridge_rows"] != 19
        or summary["candidate_output_rows_represented"] != 159
        or summary["queue_approval_rows_represented"] != 159
        or summary["review_queue_rows_represented"] != 159
        or summary["decision_scaffold_rows_represented"] != 159
        or summary["manual_decision_audit_rows_represented"] != 159
        or summary["pending_decision_rows_represented"] != 159
        or summary["valid_non_mutating_decision_rows_represented"] != 0
        or summary["invalid_decision_rows_represented"] != 0
    ):
        raise SystemExit("Review-queue bridge failed coverage checks: " + dumps(summary))

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["bridge_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
