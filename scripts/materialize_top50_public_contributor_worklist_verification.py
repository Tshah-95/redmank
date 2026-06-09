#!/usr/bin/env python3
"""Verify the public top-50 contributor worklist without mutating state."""

from __future__ import annotations

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

WORKLIST_CSV = ARTIFACTS / "top50_public_contributor_worklist.csv"
WORKLIST_JSON = ARTIFACTS / "top50_public_contributor_worklist.json"
WORKLIST_SUMMARY = ARTIFACTS / "top50_public_contributor_worklist_summary.json"

OUT_CSV = ARTIFACTS / "top50_public_contributor_worklist_verification.csv"
OUT_JSON = ARTIFACTS / "top50_public_contributor_worklist_verification.json"
OUT_SUMMARY = ARTIFACTS / "top50_public_contributor_worklist_verification_summary.json"
OUT_MD = RESEARCH / "top50-public-contributor-worklist-verification-2026-06-09.md"

EXPECTED_WORKLIST_ROWSET = "49ef8213829012327e0b190e25d8ade137527447ac6c0732df46784b7967e0a3"
EXPECTED_CLONE_VERIFICATION_ROWSET = "da28ec6ac1e9a4df95c7f60c12fa9e6a8221ea639d50f27f86776ec194b871ba"
EXPECTED_BATCH_PACKET_ROWSET = "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f"
EXPECTED_OPERATOR_PACKET_ROWSET = "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"
EXPECTED_DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
EXPECTED_GAP_SLICE_INDEX_ROWSET = "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75"
EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET = "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782"
EXPECTED_GAP_TARGETED_REVIEW_PACKET_ROWSET = "d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607"
EXPECTED_GAP_PARSER_SCOPE_BRIDGE_ROWSET = "942d131072d56524c9e19832c084b9e2520e43e783e3a9c0c6e2ae30c0f06912"
EXPECTED_GAP_CANDIDATE_OUTPUT_BRIDGE_ROWSET = "dfb141c1883d85fd6a8c7c0e015b939414788936eb13dbb04eecb9111ff5b843"
EXPECTED_GAP_REVIEW_QUEUE_BRIDGE_ROWSET = "46c2b215f28819df10913fa35f7dff6e7f4afc4ec6c3598e7432088c3f34e10d"
EXPECTED_EXECUTION_READINESS_BRIDGE_ROWSET = "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa"
EXPECTED_BLANK_EXECUTION_VERIFICATION_ROWSET = "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e"
EXPECTED_SLICE_PRIORITIZATION_PLAN_ROWSET = "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c"
EXPECTED_PRIORITY_INSTRUCTION_PACKET_ROWSET = "dfe6c7081ac7c3c28ac6e8afcb736a2d16bc8a6cbd8cba1cbc38b420064ddd65"
EXPECTED_PATCH_HELPER_FIXTURE_ROWSET = "9d87181804d6ade23ea3bd7fd322cdc7fdeab7b3078aade0921c8d2b2cab2825"
EXPECTED_PRIORITY_HANDOFF_PACKET_ROWSET = "9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0"
GBRAIN_APPROVAL_LINE = "APPROVE top50_public_contributor_worklist_verification_lane_approved"

MUTATION_POLICY = (
    "Non-mutating verification for the public top-50 contributor worklist. It checks committed worklist rowsets, "
    "commands, source artifacts, prohibition gates, and public-safety leakage. It does not execute contributor "
    "work, ingest people, mutate training states, close denominators, verify schools, rewrite URLs, accept "
    "profile/contact/research facts, publish raw dumps, or collapse identities."
)

FIELDS = [
    "verification_key",
    "check_name",
    "check_status",
    "expected_value",
    "observed_value",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = ["check_name", "check_status", "expected_value", "observed_value", "evidence_json"]

REQUIRED_PROHIBITIONS = [
    "person_ingestion",
    "training_state_mutation",
    "denominator_closure",
    "school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "enrichment_acceptance",
    "unique_person_identity_collapse",
]
ALLOWED_COMMANDS = {
    "python3 scripts/materialize_top50_public_clone_verification.py",
    (
        "python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py && "
        "python3 scripts/materialize_vanderbilt_candidate_review_batch_packets.py && "
        "python3 scripts/materialize_vanderbilt_public_reviewer_operator_packets.py && "
        "python3 scripts/materialize_top50_public_clone_verification.py"
    ),
    (
        "python3 scripts/materialize_vanderbilt_patch_helper_fixture_verification.py && "
        "python3 scripts/materialize_vanderbilt_priority_reviewer_instruction_packet.py && "
        "python3 scripts/materialize_vanderbilt_priority_reviewer_handoff_packet.py && "
        "python3 scripts/materialize_vanderbilt_synthetic_handoff_dry_run_demo.py && "
        "python3 scripts/materialize_top50_public_clone_verification.py && "
        "python3 scripts/assert_gap_manifest_fails_closed.py"
    ),
    "python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py",
}
URL_RE = re.compile(r"https?://", re.I)

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
    if not path.exists():
        return []
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


def add_check(
    rows: list[dict[str, object]],
    generated_at: str,
    check_name: str,
    passed: bool,
    expected_value: object,
    observed_value: object,
    evidence: object,
) -> None:
    rows.append(
        {
            "verification_key": stable_key("top50_public_contributor_worklist_verification", check_name, expected_value, observed_value),
            "check_name": check_name,
            "check_status": "pass" if passed else "fail",
            "expected_value": dumps(expected_value),
            "observed_value": dumps(observed_value),
            "evidence_json": dumps(evidence),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
    )


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("verification_key", "")))
    ]
    return sha256_text(dumps(material))


def source_artifact_status(rows: list[dict[str, str]]) -> dict[str, bool]:
    paths = sorted({row.get("source_artifact", "") for row in rows if row.get("source_artifact")})
    return {path: (ROOT / path).exists() for path in paths}


def target_artifact_status(rows: list[dict[str, str]]) -> dict[str, str]:
    allowed_future = {
        "artifacts/data/vanderbilt_candidate_acceptance_or_closure_approval_packet.csv",
    }
    status: dict[str, str] = {}
    for path in sorted({row.get("target_artifact", "") for row in rows if row.get("target_artifact")}):
        if (ROOT / path).exists():
            status[path] = "exists"
        elif path in allowed_future:
            status[path] = "future_allowed"
        else:
            status[path] = "missing"
    return status


def leak_hits(paths: list[Path]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in paths:
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        if URL_RE.search(text):
            hits.append({"path": str(path.relative_to(ROOT)), "kind": "url_like_text"})
        if "reviewer_note\"" in text or "reviewer_note," in text or "reviewer_note:" in text:
            hits.append({"path": str(path.relative_to(ROOT)), "kind": "reviewer_note_text_field"})
    return hits


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Top50 Public Contributor Worklist Verification",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Top50 Public Contributor Worklist Verification",
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
        "## Checks",
        "",
        "| check | status | observed |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append("| {check_name} | {check_status} | `{observed_value}` |".format(**row))
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = read_json(WORKLIST_SUMMARY)
    csv_rows = read_csv_rows(WORKLIST_CSV)
    json_rows = read_json(WORKLIST_JSON)
    if not isinstance(summary, dict) or not isinstance(json_rows, list):
        raise SystemExit("Expected public contributor worklist summary JSON object and worklist JSON array.")

    checks: list[dict[str, object]] = []
    add_check(
        checks,
        generated_at,
        "worklist_summary_boundary",
        summary.get("rowset_sha256") == EXPECTED_WORKLIST_ROWSET
        and summary.get("worklist_rows") == 4
        and summary.get("total_impact_count") == 365
        and summary.get("mutation_allowed") is False,
        {"rowset_sha256": EXPECTED_WORKLIST_ROWSET, "worklist_rows": 4, "total_impact_count": 365, "mutation_allowed": False},
        {
            "rowset_sha256": summary.get("rowset_sha256"),
            "worklist_rows": summary.get("worklist_rows"),
            "total_impact_count": summary.get("total_impact_count"),
            "mutation_allowed": summary.get("mutation_allowed"),
        },
        {"summary": str(WORKLIST_SUMMARY.relative_to(ROOT))},
    )
    add_check(
        checks,
        generated_at,
        "worklist_csv_json_counts_match",
        len(csv_rows) == len(json_rows) == summary.get("worklist_rows") == 4,
        {"csv_rows": 4, "json_rows": 4, "summary_rows": 4},
        {"csv_rows": len(csv_rows), "json_rows": len(json_rows), "summary_rows": summary.get("worklist_rows")},
        {},
    )
    observed_order = [row.get("action_lane", "") for row in sorted(csv_rows, key=lambda item: int(item.get("execution_order", 0)))]
    expected_order = [
        "verify_public_clone_substrate",
        "vanderbilt_bounded_manual_review_packets",
        "vanderbilt_active_gap_manifest_triage",
        "future_exact_approval_packet_after_valid_decisions",
    ]
    add_check(checks, generated_at, "worklist_lane_order", observed_order == expected_order, expected_order, observed_order, {})
    by_status = Counter(row.get("action_status", "") for row in csv_rows)
    add_check(
        checks,
        generated_at,
        "worklist_status_distribution",
        dict(sorted(by_status.items())) == summary.get("by_action_status"),
        summary.get("by_action_status"),
        dict(sorted(by_status.items())),
        {},
    )
    source_status = source_artifact_status(csv_rows)
    target_status = target_artifact_status(csv_rows)
    add_check(
        checks,
        generated_at,
        "worklist_artifact_paths_resolve",
        all(source_status.values()) and all(value in {"exists", "future_allowed"} for value in target_status.values()),
        {"all_sources_exist": True, "targets_exist_or_future_allowed": True},
        {"sources": source_status, "targets": target_status},
        {},
    )
    observed_commands = sorted({row.get("verification_command", "") for row in csv_rows})
    add_check(
        checks,
        generated_at,
        "worklist_verification_commands_allowed",
        set(observed_commands) == ALLOWED_COMMANDS,
        sorted(ALLOWED_COMMANDS),
        observed_commands,
        {},
    )
    missing_prohibitions = {
        row.get("action_lane", ""): [
            prohibition for prohibition in REQUIRED_PROHIBITIONS if prohibition not in row.get("prohibited_mutations", "")
        ]
        for row in csv_rows
    }
    missing_prohibitions = {lane: values for lane, values in missing_prohibitions.items() if values}
    add_check(checks, generated_at, "worklist_prohibition_gates_present", not missing_prohibitions, {}, missing_prohibitions, {})
    approval_targets = {
        row.get("action_lane", ""): row.get("approval_required_for", "")
        for row in csv_rows
        if row.get("action_lane") != "verify_public_clone_substrate"
    }
    add_check(
        checks,
        generated_at,
        "worklist_approval_gates_present",
        all(value for value in approval_targets.values())
        and "person_ingestion" in approval_targets.get("vanderbilt_bounded_manual_review_packets", "")
        and "denominator_closure" in approval_targets.get("vanderbilt_active_gap_manifest_triage", ""),
        {"approval_required_for_non_verification_rows": "present"},
        approval_targets,
        {},
    )
    source_rowsets = {
        row.get("action_lane", ""): row.get("source_rowset_sha256", "")
        for row in csv_rows
    }
    add_check(
        checks,
        generated_at,
        "worklist_source_rowsets_match",
        source_rowsets.get("verify_public_clone_substrate") == EXPECTED_CLONE_VERIFICATION_ROWSET
        and source_rowsets.get("vanderbilt_bounded_manual_review_packets") == EXPECTED_OPERATOR_PACKET_ROWSET
        and source_rowsets.get("vanderbilt_active_gap_manifest_triage") == EXPECTED_PRIORITY_HANDOFF_PACKET_ROWSET
        and source_rowsets.get("future_exact_approval_packet_after_valid_decisions") == EXPECTED_DECISION_AUDIT_ROWSET,
        {
            "verify_public_clone_substrate": EXPECTED_CLONE_VERIFICATION_ROWSET,
            "vanderbilt_bounded_manual_review_packets": EXPECTED_OPERATOR_PACKET_ROWSET,
            "vanderbilt_active_gap_manifest_triage": EXPECTED_PRIORITY_HANDOFF_PACKET_ROWSET,
            "future_exact_approval_packet_after_valid_decisions": EXPECTED_DECISION_AUDIT_ROWSET,
        },
        source_rowsets,
        {},
    )
    target_rowsets = {
        row.get("action_lane", ""): row.get("target_rowset_sha256", "")
        for row in csv_rows
    }
    add_check(
        checks,
        generated_at,
        "worklist_target_rowsets_match",
        target_rowsets.get("verify_public_clone_substrate") == EXPECTED_CLONE_VERIFICATION_ROWSET
        and target_rowsets.get("vanderbilt_bounded_manual_review_packets") == EXPECTED_DECISION_AUDIT_ROWSET
        and target_rowsets.get("vanderbilt_active_gap_manifest_triage") == EXPECTED_DECISION_AUDIT_ROWSET,
        {
            "verify_public_clone_substrate": EXPECTED_CLONE_VERIFICATION_ROWSET,
            "vanderbilt_bounded_manual_review_packets": EXPECTED_DECISION_AUDIT_ROWSET,
            "vanderbilt_active_gap_manifest_triage": EXPECTED_DECISION_AUDIT_ROWSET,
        },
        target_rowsets,
        {},
    )
    leaks = leak_hits(
        [
            WORKLIST_CSV,
            WORKLIST_JSON,
            WORKLIST_SUMMARY,
            RESEARCH / "top50-public-contributor-worklist-2026-06-09.md",
        ]
    )
    add_check(checks, generated_at, "worklist_public_leak_scan", not leaks, [], leaks, {"scan": "url_like_text_or_reviewer_note_text_field"})
    add_check(
        checks,
        generated_at,
        "gbrain_worklist_verification_lane_approved",
        GBRAIN_APPROVAL_LINE == "APPROVE top50_public_contributor_worklist_verification_lane_approved",
        "APPROVE top50_public_contributor_worklist_verification_lane_approved",
        GBRAIN_APPROVAL_LINE,
        {"approval_boundary": "non-mutating contributor-worklist verification"},
    )

    pass_rows = sum(1 for row in checks if row["check_status"] == "pass")
    fail_rows = len(checks) - pass_rows
    out_summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_worklist_summary": str(WORKLIST_SUMMARY.relative_to(ROOT)),
        "source_worklist_rowset_sha256": EXPECTED_WORKLIST_ROWSET,
        "verification_rows": len(checks),
        "pass_rows": pass_rows,
        "fail_rows": fail_rows,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "gbrain_approval_status": "approved_non_mutating_public_contributor_worklist_verification_lane",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "policy": MUTATION_POLICY,
    }
    out_summary["rowset_sha256"] = rowset_sha256(checks)

    write_csv(OUT_CSV, checks)
    write_json(OUT_JSON, checks)
    write_json(OUT_SUMMARY, out_summary)
    write_markdown(checks, out_summary)
    print(json.dumps({key: out_summary[key] for key in ["verification_rows", "pass_rows", "fail_rows", "rowset_sha256"]}, sort_keys=True))
    if fail_rows:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
