#!/usr/bin/env python3
"""Materialize the aggregate public substrate check contract."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

OUT_CSV = ARTIFACTS / "top50_public_substrate_check_contract.csv"
OUT_JSON = ARTIFACTS / "top50_public_substrate_check_contract.json"
OUT_SUMMARY = ARTIFACTS / "top50_public_substrate_check_contract_summary.json"
OUT_MD = RESEARCH / "top50-public-substrate-check-contract-2026-06-09.md"

EXPECTED_SYNTHETIC_HANDOFF_ROWSET = "81da7a86173eef52ee6fbc4afdf98ab3f33555b6d83f6c61be88bad61a211bb4"
EXPECTED_PRIORITY_HANDOFF_ROWSET = "9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0"
EXPECTED_OPEN_GAP_TRIAGE_ROWSET = "b89f2278c96c18c70403099be2b18542bb0f59a4c50a53921f17fe83864b1391"
EXPECTED_TRIAGE_CONTRACT_ROWSET = "b8559206ae9341dae7c9136ddb6d83651ff84905feb74ec133992e822534416f"
EXPECTED_CLONE_VERIFICATION_ROWSET = "3769d2294e7d3682257fd4df8f4484aea699bb757ef4ba510c1262d1039cbeaa"
EXPECTED_WORKLIST_ROWSET = "2908c35a7730cb55bd2305943a305a97995d483c8b26ca8c68b39e4bab3b14ea"
EXPECTED_WORKLIST_VERIFICATION_ROWSET = "606e729b15ae4de6db830326b8e5a885a15b1dc0f3f018df7ebf2d0a8f99f59d"
EXPECTED_DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
GBRAIN_APPROVAL_LINE = "APPROVE top50_public_substrate_check_contract_non_mutating_increment"

MUTATION_POLICY = (
    "Aggregate non-mutating public substrate check contract for the top-50/Vanderbilt lane. It runs the committed "
    "synthetic handoff dry-run, priority handoff, open-gap triage, public clone verification, contributor worklist, "
    "worklist verification, and gap-manifest fail-closed checks, then records their rowsets and pass counts. It does not fill "
    "reviewer decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a "
    "school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities."
)

FIELDS = [
    "contract_check_key",
    "execution_order",
    "check_name",
    "check_status",
    "command",
    "expected_rowset_sha256",
    "observed_rowset_sha256",
    "expected_pass_rows",
    "observed_pass_rows",
    "expected_fail_rows",
    "observed_fail_rows",
    "expected_rows",
    "observed_rows",
    "mutation_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "accepted_person_rows",
    "apply_executed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"contract_check_key", "evidence_json", "mutation_policy", "generated_at"}
]

COMMANDS = [
    (
        "synthetic_handoff_dry_run_demo",
        [sys.executable, "scripts/materialize_vanderbilt_synthetic_handoff_dry_run_demo.py"],
        ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo_summary.json",
        EXPECTED_SYNTHETIC_HANDOFF_ROWSET,
        {"pass_rows": 5, "fail_rows": 0, "demo_check_rows": 5},
    ),
    (
        "priority_reviewer_handoff_packet",
        [sys.executable, "scripts/materialize_vanderbilt_priority_reviewer_handoff_packet.py"],
        ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet_summary.json",
        EXPECTED_PRIORITY_HANDOFF_ROWSET,
        {"handoff_rows": 1, "accepted_person_rows": 0, "apply_executed": False},
    ),
    (
        "open_gap_manifest_triage_packet",
        [sys.executable, "scripts/materialize_vanderbilt_open_gap_manifest_triage_packet.py"],
        ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet_summary.json",
        EXPECTED_OPEN_GAP_TRIAGE_ROWSET,
        {
            "triage_rows": 21,
            "gap_rows_represented": 113,
            "slice_outputs_default_tmp_only": True,
            "accepted_person_rows": 0,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
            "school_verification_allowed": False,
        },
    ),
    (
        "triage_slice_definition_contract",
        [sys.executable, "scripts/materialize_vanderbilt_open_gap_manifest_triage_packet.py"],
        ARTIFACTS / "vanderbilt_triage_slice_definition_contract_summary.json",
        EXPECTED_TRIAGE_CONTRACT_ROWSET,
        {
            "contract_rows": 4,
            "slice_rows_represented": 21,
            "gap_rows_represented": 113,
            "slice_outputs_default_tmp_only": True,
            "accepted_person_rows": 0,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
            "school_verification_allowed": False,
        },
    ),
    (
        "public_clone_verification",
        [sys.executable, "scripts/materialize_top50_public_clone_verification.py"],
        ARTIFACTS / "top50_public_clone_verification_summary.json",
        EXPECTED_CLONE_VERIFICATION_ROWSET,
        {"pass_rows": 47, "fail_rows": 0, "verification_rows": 47},
    ),
    (
        "public_contributor_worklist",
        [sys.executable, "scripts/materialize_top50_public_contributor_worklist.py"],
        ARTIFACTS / "top50_public_contributor_worklist_summary.json",
        EXPECTED_WORKLIST_ROWSET,
        {"worklist_rows": 5, "total_impact_count": 480},
    ),
    (
        "public_contributor_worklist_verification",
        [sys.executable, "scripts/materialize_top50_public_contributor_worklist_verification.py"],
        ARTIFACTS / "top50_public_contributor_worklist_verification_summary.json",
        EXPECTED_WORKLIST_VERIFICATION_ROWSET,
        {"pass_rows": 12, "fail_rows": 0, "verification_rows": 12},
    ),
    (
        "decision_audit_pending_boundary",
        [sys.executable, "scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py"],
        ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json",
        EXPECTED_DECISION_AUDIT_ROWSET,
        {
            "audit_rows": 159,
            "pending_rows": 159,
            "valid_non_mutating_rows": 0,
            "invalid_rows": 0,
            "accepted_person_rows": 0,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
        },
    ),
    (
        "gap_manifest_fail_closed_assertion",
        [sys.executable, "scripts/assert_gap_manifest_fails_closed.py"],
        None,
        "",
        {"stdout": "gap_manifest_fail_closed_assertion_passed"},
    ),
]


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def command_text(command: list[str]) -> str:
    if command and command[0] == sys.executable:
        command = ["python3", *command[1:]]
    return " ".join(command)


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("contract_check_key", "")))
    ]
    return sha256_text(dumps(material))


def summary_value(summary: dict[str, object], keys: tuple[str, ...]) -> int:
    for key in keys:
        value = summary.get(key)
        if isinstance(value, int):
            return value
    return 0


def add_row(
    rows: list[dict[str, object]],
    generated_at: str,
    execution_order: int,
    check_name: str,
    command: list[str],
    expected_rowset: str,
    summary_path: Path | None,
    expectations: dict[str, object],
) -> None:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    stdout = result.stdout.strip()
    stderr = result.stderr.strip()
    summary = read_json(summary_path) if summary_path else {}
    if summary_path and not isinstance(summary, dict):
        summary = {}

    observed_rowset = str(summary.get("rowset_sha256", ""))
    expected_pass = int(expectations.get("pass_rows", 0) or 0)
    observed_pass = summary_value(summary, ("pass_rows",))
    expected_fail = int(expectations.get("fail_rows", 0) or 0)
    observed_fail = summary_value(summary, ("fail_rows",))
    expected_rows = int(
        expectations.get("verification_rows")
        or expectations.get("demo_check_rows")
        or expectations.get("worklist_rows")
        or expectations.get("handoff_rows")
        or 0
    )
    observed_rows = summary_value(summary, ("verification_rows", "demo_check_rows", "worklist_rows", "handoff_rows"))

    expected_pairs = {
        key: value
        for key, value in expectations.items()
        if key not in {"pass_rows", "fail_rows", "verification_rows", "demo_check_rows", "worklist_rows", "handoff_rows", "stdout"}
    }
    observed_pairs = {key: summary.get(key) for key in expected_pairs}
    passed = (
        result.returncode == 0
        and (not expected_rowset or observed_rowset == expected_rowset)
        and all(observed_pairs.get(key) == value for key, value in expected_pairs.items())
        and (not expected_pass or observed_pass == expected_pass)
        and observed_fail == expected_fail
        and (not expected_rows or observed_rows == expected_rows)
        and (not expectations.get("stdout") or stdout == expectations["stdout"])
    )

    rows.append(
        {
            "contract_check_key": stable_key("top50_public_substrate_check_contract", execution_order, check_name),
            "execution_order": execution_order,
            "check_name": check_name,
            "check_status": "pass" if passed else "fail",
            "command": command_text(command),
            "expected_rowset_sha256": expected_rowset,
            "observed_rowset_sha256": observed_rowset,
            "expected_pass_rows": expected_pass,
            "observed_pass_rows": observed_pass,
            "expected_fail_rows": expected_fail,
            "observed_fail_rows": observed_fail,
            "expected_rows": expected_rows,
            "observed_rows": observed_rows,
            "mutation_allowed": "false",
            "person_ingestion_allowed": "false",
            "denominator_closure_allowed": "false",
            "accepted_person_rows": int(summary.get("accepted_person_rows", 0) or 0),
            "apply_executed": "true" if summary.get("apply_executed") is True else "false",
            "evidence_json": dumps(
                {
                    "returncode": result.returncode,
                    "summary": str(summary_path.relative_to(ROOT)) if summary_path else "",
                    "expected_pairs": expected_pairs,
                    "observed_pairs": observed_pairs,
                    "stdout_match": stdout == expectations.get("stdout") if expectations.get("stdout") else True,
                    "stderr_present": bool(stderr),
                }
            ),
            "mutation_policy": MUTATION_POLICY,
            "generated_at": generated_at,
        }
    )


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Top50 Public Substrate Check Contract",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Top50 Public Substrate Check Contract",
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
        "| order | check | status | command |",
        "| ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append("| {execution_order} | {check_name} | {check_status} | `{command}` |".format(**row))
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    for index, (name, command, summary_path, expected_rowset, expectations) in enumerate(COMMANDS, start=1):
        add_row(rows, generated_at, index, name, command, expected_rowset, summary_path, expectations)

    pass_rows = sum(1 for row in rows if row["check_status"] == "pass")
    fail_rows = len(rows) - pass_rows
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "contract_check_rows": len(rows),
        "pass_rows": pass_rows,
        "fail_rows": fail_rows,
        "source_synthetic_handoff_rowset_sha256": EXPECTED_SYNTHETIC_HANDOFF_ROWSET,
        "source_priority_handoff_rowset_sha256": EXPECTED_PRIORITY_HANDOFF_ROWSET,
        "source_open_gap_triage_rowset_sha256": EXPECTED_OPEN_GAP_TRIAGE_ROWSET,
        "source_triage_contract_rowset_sha256": EXPECTED_TRIAGE_CONTRACT_ROWSET,
        "source_clone_verification_rowset_sha256": EXPECTED_CLONE_VERIFICATION_ROWSET,
        "source_worklist_rowset_sha256": EXPECTED_WORKLIST_ROWSET,
        "source_worklist_verification_rowset_sha256": EXPECTED_WORKLIST_VERIFICATION_ROWSET,
        "source_decision_audit_rowset_sha256": EXPECTED_DECISION_AUDIT_ROWSET,
        "decision_audit_pending_rows": 159,
        "decision_audit_valid_non_mutating_rows": 0,
        "decision_audit_invalid_rows": 0,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "accepted_person_rows": 0,
        "apply_executed": False,
        "gbrain_approval_status": "approved_non_mutating_top50_public_substrate_check_contract_increment",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["contract_check_rows", "pass_rows", "fail_rows", "rowset_sha256"]}, sort_keys=True))
    if fail_rows:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
