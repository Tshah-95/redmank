#!/usr/bin/env python3
"""Verify the committed public top-50/Vanderbilt operating substrate."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

OUT_CSV = ARTIFACTS / "top50_public_clone_verification.csv"
OUT_JSON = ARTIFACTS / "top50_public_clone_verification.json"
OUT_SUMMARY = ARTIFACTS / "top50_public_clone_verification_summary.json"
OUT_MD = RESEARCH / "top50-public-clone-verification-2026-06-09.md"

EXPECTED_TOP50_TARGET_ROWSET = "fa547bf602d8dc9998189a0fabe2b45a1cba6892239eedf391cdb65c6ef419d8"
EXPECTED_SCHOOL_VERIFICATION_ROWSET = "e99eb07b856f8bdd546d2ac2bb0641c22cd2bedd69e42d8f38f7e5db04823e29"
EXPECTED_TOP50_SNAPSHOT_ROWSET = "b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48"
EXPECTED_VANDERBILT_BATCH_PACKET_ROWSET = "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f"
EXPECTED_VANDERBILT_OPERATOR_PACKET_ROWSET = "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"
EXPECTED_VANDERBILT_DECISION_AUDIT_ROWSET = "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"
EXPECTED_VANDERBILT_SCAFFOLD_ROWSET = "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"
EXPECTED_VANDERBILT_PATCH_TEMPLATE_ROWSET = "5532d007555997f54d25884baba2f4e594d4ff1fa286301bfa6f87fc64caaa8d"
EXPECTED_VANDERBILT_PATCH_WORKBOOK_ROWSET = "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3"
EXPECTED_VANDERBILT_WORKBOOK_SLICE_INDEX_ROWSET = "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4"
EXPECTED_VANDERBILT_EXECUTION_READINESS_BRIDGE_ROWSET = "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa"
EXPECTED_VANDERBILT_BLANK_EXECUTION_VERIFICATION_ROWSET = "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e"
EXPECTED_VANDERBILT_SLICE_PRIORITIZATION_ROWSET = "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c"
EXPECTED_VANDERBILT_PRIORITY_INSTRUCTION_ROWSET = "dfe6c7081ac7c3c28ac6e8afcb736a2d16bc8a6cbd8cba1cbc38b420064ddd65"
EXPECTED_VANDERBILT_PATCH_HELPER_FIXTURE_ROWSET = "9d87181804d6ade23ea3bd7fd322cdc7fdeab7b3078aade0921c8d2b2cab2825"
EXPECTED_VANDERBILT_PRIORITY_HANDOFF_ROWSET = "9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0"
EXPECTED_VANDERBILT_SYNTHETIC_HANDOFF_DRY_RUN_ROWSET = "81da7a86173eef52ee6fbc4afdf98ab3f33555b6d83f6c61be88bad61a211bb4"
EXPECTED_GAP_BATCH_SLICE_INDEX_ROWSET = "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75"
EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET = "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782"
EXPECTED_GAP_TARGETED_REVIEW_PACKET_ROWSET = "d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607"
EXPECTED_GAP_PARSER_SCOPE_BRIDGE_ROWSET = "942d131072d56524c9e19832c084b9e2520e43e783e3a9c0c6e2ae30c0f06912"
EXPECTED_GAP_CANDIDATE_OUTPUT_BRIDGE_ROWSET = "dfb141c1883d85fd6a8c7c0e015b939414788936eb13dbb04eecb9111ff5b843"
EXPECTED_GAP_REVIEW_QUEUE_BRIDGE_ROWSET = "46c2b215f28819df10913fa35f7dff6e7f4afc4ec6c3598e7432088c3f34e10d"
EXPECTED_VANDERBILT_OPEN_GAP_TRIAGE_ROWSET = "b89f2278c96c18c70403099be2b18542bb0f59a4c50a53921f17fe83864b1391"
EXPECTED_VANDERBILT_TRIAGE_CONTRACT_ROWSET = "b8559206ae9341dae7c9136ddb6d83651ff84905feb74ec133992e822534416f"
EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET = "c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b"
EXPECTED_VANDERBILT_SLICE_2_LIVE_FETCH_APPROVAL_ROWSET = "98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d"
EXPECTED_VANDERBILT_SLICE_2_LIVE_ROUTE_OBSERVATION_ROWSET = "c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0"
EXPECTED_VANDERBILT_SLICE_2_ROUTE_PARSER_SCOPE_APPROVAL_ROWSET = "bb0c69694a411c386964d1b7ae523a65a31452e5d62db227d4469044bd109672"
GBRAIN_APPROVAL_LINE = "APPROVE top50_public_clone_verification_lane_approved"

MUTATION_POLICY = (
    "Non-mutating public clone verification for the top-50/Vanderbilt operating substrate. It reads committed "
    "public-safe summaries, packets, README policy, and script guards. It does not fetch web pages, call GBrain, "
    "regenerate scratch-dependent manifests, approve person ingestion, close denominators, verify schools, rewrite "
    "URLs, accept enrichment facts, publish raw dumps, or collapse identities."
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

URL_RE = re.compile(r"https?://", re.I)
PRIVATE_PATH_PATTERNS = [
    "artifacts/data/gbrain_*_http_mcp_response.json",
    "artifacts/data/browser_page_dumps/",
    "artifacts/data/debug_*.sqlite",
    "artifacts/data/raw/",
    ".playwright-mcp/",
    "inbox/",
    "reports/",
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
            "verification_key": stable_key("top50_public_clone_verification", check_name, expected_value, observed_value),
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


def committed_private_path_hits() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    paths = result.stdout.splitlines()
    hits: list[str] = []
    for path in paths:
        if path.startswith("artifacts/data/gbrain_") and path.endswith("_http_mcp_response.json"):
            hits.append(path)
        elif path.startswith("artifacts/data/browser_page_dumps/"):
            hits.append(path)
        elif path.startswith("artifacts/data/debug_") and path.endswith(".sqlite"):
            hits.append(path)
        elif path.startswith("artifacts/data/raw/"):
            hits.append(path)
        elif path.startswith(".playwright-mcp/") or path.startswith("inbox/") or path.startswith("reports/"):
            hits.append(path)
    return sorted(hits)


def batch_packet_leak_hits(paths: list[Path]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            hits.append({"path": str(path.relative_to(ROOT)), "kind": "missing"})
            continue
        text = path.read_text(encoding="utf-8")
        if URL_RE.search(text):
            hits.append({"path": str(path.relative_to(ROOT)), "kind": "url_like_text"})
        if "reviewer_note\"" in text or "reviewer_note," in text or "reviewer_note:" in text:
            hits.append({"path": str(path.relative_to(ROOT)), "kind": "reviewer_note_text_field"})
    return hits


def gitignore_patterns_present() -> dict[str, bool]:
    text = (ROOT / ".gitignore").read_text(encoding="utf-8") if (ROOT / ".gitignore").exists() else ""
    return {pattern: pattern in text for pattern in PRIVATE_PATH_PATTERNS}


def private_marker_hits_in_paths(paths: list[Path]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for path in paths:
        if not path.exists():
            hits.append({"path": str(path.relative_to(ROOT)), "kind": "missing"})
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in PRIVATE_PATH_PATTERNS:
            marker = pattern.rstrip("*")
            if marker and marker in text:
                hits.append({"path": str(path.relative_to(ROOT)), "kind": "private_marker", "marker": pattern})
    return hits


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Top50 Public Clone Verification",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Top50 Public Clone Verification",
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
    checks: list[dict[str, object]] = []

    target_summary = read_json(ARTIFACTS / "top50_medical_school_targets_summary.json")
    school_verification = read_json(ARTIFACTS / "school_verification_registry_summary.json")
    snapshot = read_json(ARTIFACTS / "top50_engine_operating_snapshot.json")
    batch_summary = read_json(ARTIFACTS / "vanderbilt_candidate_review_batch_packet_summary.json")
    batch_csv = read_csv_rows(ARTIFACTS / "vanderbilt_candidate_review_batch_packets.csv")
    batch_json = read_json(ARTIFACTS / "vanderbilt_candidate_review_batch_packets.json")
    operator_summary = read_json(ARTIFACTS / "vanderbilt_public_reviewer_operator_packet_summary.json")
    operator_csv = read_csv_rows(ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.csv")
    operator_json = read_json(ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.json")
    patch_template_summary = read_json(ARTIFACTS / "vanderbilt_reviewer_decision_patch_template_summary.json")
    patch_template_csv = read_csv_rows(ARTIFACTS / "vanderbilt_reviewer_decision_patch_template.csv")
    patch_template_json = read_json(ARTIFACTS / "vanderbilt_reviewer_decision_patch_template.json")
    patch_workbook_summary = read_json(ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_summary.json")
    patch_workbook_csv = read_csv_rows(ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.csv")
    patch_workbook_json = read_json(ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.json")
    slice_index_summary = read_json(ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index_summary.json")
    slice_index_csv = read_csv_rows(ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.csv")
    slice_index_json = read_json(ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.json")
    execution_readiness_summary = read_json(ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge_summary.json")
    execution_readiness_csv = read_csv_rows(ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge.csv")
    execution_readiness_json = read_json(ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge.json")
    blank_execution_summary = read_json(ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification_summary.json")
    blank_execution_csv = read_csv_rows(ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification.csv")
    blank_execution_json = read_json(ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification.json")
    slice_prioritization_summary = read_json(ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan_summary.json")
    slice_prioritization_csv = read_csv_rows(ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan.csv")
    slice_prioritization_json = read_json(ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan.json")
    priority_instruction_summary = read_json(ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet_summary.json")
    priority_instruction_csv = read_csv_rows(ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet.csv")
    priority_instruction_json = read_json(ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet.json")
    patch_fixture_summary = read_json(ARTIFACTS / "vanderbilt_patch_helper_fixture_verification_summary.json")
    patch_fixture_csv = read_csv_rows(ARTIFACTS / "vanderbilt_patch_helper_fixture_verification.csv")
    patch_fixture_json = read_json(ARTIFACTS / "vanderbilt_patch_helper_fixture_verification.json")
    priority_handoff_summary = read_json(ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet_summary.json")
    priority_handoff_csv = read_csv_rows(ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet.csv")
    priority_handoff_json = read_json(ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet.json")
    synthetic_handoff_demo_summary = read_json(ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo_summary.json")
    synthetic_handoff_demo_csv = read_csv_rows(ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo.csv")
    synthetic_handoff_demo_json = read_json(ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo.json")
    audit_summary = read_json(ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json")
    scaffold_summary = read_json(ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json")
    gap_summary = read_json(ARTIFACTS / "school_gap_resolution_manifest_summary.json")
    gap_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_manifest.csv")
    gap_batch_summary = read_json(ARTIFACTS / "school_gap_resolution_batch_summary.json")
    gap_batch_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_batches.csv")
    gap_packet_summary = read_json(ARTIFACTS / "school_gap_resolution_batch_packet_summary.json")
    gap_packet_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_batch_packets.csv")
    gap_slice_summary = read_json(ARTIFACTS / "school_gap_resolution_batch_slice_index_summary.json")
    gap_slice_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_batch_slice_index.csv")
    gap_slice_json = read_json(ARTIFACTS / "school_gap_resolution_batch_slice_index.json")
    gap_review_template_summary = read_json(ARTIFACTS / "school_gap_resolution_review_template_summary.json")
    gap_review_template_validation = read_json(
        ARTIFACTS / "school_gap_resolution_review_template_validation_summary.json"
    )
    gap_review_template_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_review_template.csv")
    gap_review_template_json = read_json(ARTIFACTS / "school_gap_resolution_review_template.json")
    gap_targeted_review_packet_summary = read_json(ARTIFACTS / "school_gap_resolution_targeted_review_packet_summary.json")
    gap_targeted_review_packet_validation = read_json(
        ARTIFACTS / "school_gap_resolution_targeted_review_packet_validation_summary.json"
    )
    gap_targeted_review_packet_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_targeted_review_packet.csv")
    gap_targeted_review_packet_json = read_json(ARTIFACTS / "school_gap_resolution_targeted_review_packet.json")
    gap_parser_scope_bridge_summary = read_json(ARTIFACTS / "school_gap_resolution_parser_scope_bridge_summary.json")
    gap_parser_scope_bridge_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_parser_scope_bridge.csv")
    gap_parser_scope_bridge_json = read_json(ARTIFACTS / "school_gap_resolution_parser_scope_bridge.json")
    gap_candidate_output_bridge_summary = read_json(
        ARTIFACTS / "school_gap_resolution_candidate_output_bridge_summary.json"
    )
    gap_candidate_output_bridge_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_candidate_output_bridge.csv")
    gap_candidate_output_bridge_json = read_json(ARTIFACTS / "school_gap_resolution_candidate_output_bridge.json")
    gap_review_queue_bridge_summary = read_json(ARTIFACTS / "school_gap_resolution_review_queue_bridge_summary.json")
    gap_review_queue_bridge_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_review_queue_bridge.csv")
    gap_review_queue_bridge_json = read_json(ARTIFACTS / "school_gap_resolution_review_queue_bridge.json")
    vanderbilt_open_gap_triage_summary = read_json(
        ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet_summary.json"
    )
    vanderbilt_open_gap_triage_csv = read_csv_rows(ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.csv")
    vanderbilt_open_gap_triage_json = read_json(ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.json")
    vanderbilt_triage_contract_summary = read_json(
        ARTIFACTS / "vanderbilt_triage_slice_definition_contract_summary.json"
    )
    vanderbilt_triage_contract_csv = read_csv_rows(
        ARTIFACTS / "vanderbilt_triage_slice_definition_contract.csv"
    )
    vanderbilt_triage_contract_json = read_json(
        ARTIFACTS / "vanderbilt_triage_slice_definition_contract.json"
    )
    vanderbilt_slice_2_execution_plan_summary = read_json(
        ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet_summary.json"
    )
    vanderbilt_slice_2_execution_plan_csv = read_csv_rows(
        ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet.csv"
    )
    vanderbilt_slice_2_execution_plan_json = read_json(
        ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet.json"
    )
    vanderbilt_slice_2_live_fetch_approval_summary = read_json(
        ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet_summary.json"
    )
    vanderbilt_slice_2_live_fetch_approval_csv = read_csv_rows(
        ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet.csv"
    )
    vanderbilt_slice_2_live_fetch_approval_json = read_json(
        ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet.json"
    )
    vanderbilt_slice_2_live_route_observation_summary = read_json(
        ARTIFACTS / "vanderbilt_slice_2_live_route_observation_summary.json"
    )
    vanderbilt_slice_2_live_route_observation_csv = read_csv_rows(
        ARTIFACTS / "vanderbilt_slice_2_live_route_observations.csv"
    )
    vanderbilt_slice_2_live_route_observation_json = read_json(
        ARTIFACTS / "vanderbilt_slice_2_live_route_observations.json"
    )
    vanderbilt_slice_2_route_parser_scope_approval_summary = read_json(
        ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet_summary.json"
    )
    vanderbilt_slice_2_route_parser_scope_approval_csv = read_csv_rows(
        ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet.csv"
    )
    vanderbilt_slice_2_route_parser_scope_approval_json = read_json(
        ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet.json"
    )
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")
    gap_manifest_script_text = (ROOT / "scripts" / "materialize_school_gap_resolution_manifest.py").read_text(
        encoding="utf-8"
    )
    reviewer_patch_script_text = (ROOT / "scripts" / "apply_vanderbilt_reviewer_decision_patch.py").read_text(
        encoding="utf-8"
    )
    reviewer_patch_extractor_text = (ROOT / "scripts" / "extract_vanderbilt_reviewer_decision_patch.py").read_text(
        encoding="utf-8"
    )
    reviewer_workbook_slicer_text = (
        ROOT / "scripts" / "slice_vanderbilt_reviewer_decision_patch_workbook.py"
    ).read_text(encoding="utf-8")
    reviewer_execution_bridge_text = (
        ROOT / "scripts" / "materialize_vanderbilt_reviewer_execution_readiness_bridge.py"
    ).read_text(encoding="utf-8")
    reviewer_blank_execution_text = (
        ROOT / "scripts" / "materialize_vanderbilt_reviewer_blank_execution_verification.py"
    ).read_text(encoding="utf-8")
    reviewer_slice_prioritization_text = (
        ROOT / "scripts" / "materialize_vanderbilt_reviewer_slice_prioritization_plan.py"
    ).read_text(encoding="utf-8")
    priority_instruction_text = (
        ROOT / "scripts" / "materialize_vanderbilt_priority_reviewer_instruction_packet.py"
    ).read_text(encoding="utf-8")
    patch_fixture_text = (ROOT / "scripts" / "materialize_vanderbilt_patch_helper_fixture_verification.py").read_text(
        encoding="utf-8"
    )
    priority_handoff_text = (
        ROOT / "scripts" / "materialize_vanderbilt_priority_reviewer_handoff_packet.py"
    ).read_text(encoding="utf-8")
    synthetic_handoff_demo_text = (
        ROOT / "scripts" / "materialize_vanderbilt_synthetic_handoff_dry_run_demo.py"
    ).read_text(encoding="utf-8")
    gap_batch_slicer_text = (ROOT / "scripts" / "slice_school_gap_resolution_batch_packets.py").read_text(
        encoding="utf-8"
    )

    if not all(
        isinstance(item, dict)
        for item in [
            target_summary,
            school_verification,
            snapshot,
            batch_summary,
            operator_summary,
            patch_template_summary,
            patch_workbook_summary,
            slice_index_summary,
            execution_readiness_summary,
            blank_execution_summary,
            slice_prioritization_summary,
            priority_instruction_summary,
            patch_fixture_summary,
            priority_handoff_summary,
            synthetic_handoff_demo_summary,
            audit_summary,
            scaffold_summary,
            gap_summary,
            gap_batch_summary,
            gap_packet_summary,
            gap_slice_summary,
            gap_review_template_summary,
            gap_review_template_validation,
            gap_targeted_review_packet_summary,
            gap_targeted_review_packet_validation,
            gap_parser_scope_bridge_summary,
            gap_candidate_output_bridge_summary,
            gap_review_queue_bridge_summary,
            vanderbilt_open_gap_triage_summary,
            vanderbilt_triage_contract_summary,
            vanderbilt_slice_2_execution_plan_summary,
            vanderbilt_slice_2_live_fetch_approval_summary,
            vanderbilt_slice_2_live_route_observation_summary,
            vanderbilt_slice_2_route_parser_scope_approval_summary,
        ]
    ):
        raise SystemExit("Expected public top-50 summary artifacts to be JSON objects.")
    if (
        not isinstance(batch_json, list)
        or not isinstance(operator_json, list)
        or not isinstance(patch_template_json, list)
        or not isinstance(patch_workbook_json, list)
        or not isinstance(slice_index_json, list)
        or not isinstance(execution_readiness_json, list)
        or not isinstance(blank_execution_json, list)
        or not isinstance(slice_prioritization_json, list)
        or not isinstance(priority_instruction_json, list)
        or not isinstance(patch_fixture_json, list)
        or not isinstance(priority_handoff_json, list)
        or not isinstance(synthetic_handoff_demo_json, list)
        or not isinstance(gap_slice_json, list)
        or not isinstance(gap_review_template_json, list)
        or not isinstance(gap_targeted_review_packet_json, list)
        or not isinstance(gap_parser_scope_bridge_json, list)
        or not isinstance(gap_candidate_output_bridge_json, list)
        or not isinstance(gap_review_queue_bridge_json, list)
        or not isinstance(vanderbilt_open_gap_triage_json, list)
        or not isinstance(vanderbilt_triage_contract_json, list)
        or not isinstance(vanderbilt_slice_2_execution_plan_json, list)
        or not isinstance(vanderbilt_slice_2_live_fetch_approval_json, list)
        or not isinstance(vanderbilt_slice_2_live_route_observation_json, list)
        or not isinstance(vanderbilt_slice_2_route_parser_scope_approval_json, list)
    ):
        raise SystemExit("Expected Vanderbilt candidate review batch and operator packet JSON arrays.")

    add_check(
        checks,
        generated_at,
        "top50_target_registry_boundary",
        target_summary.get("targets") == 50 and target_summary.get("rowset_sha256") == EXPECTED_TOP50_TARGET_ROWSET,
        {"targets": 50, "rowset_sha256": EXPECTED_TOP50_TARGET_ROWSET},
        {"targets": target_summary.get("targets"), "rowset_sha256": target_summary.get("rowset_sha256")},
        {"summary": "artifacts/data/top50_medical_school_targets_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "school_verification_registry_boundary",
        school_verification.get("verified_school_rows") == 1
        and school_verification.get("rowset_sha256") == EXPECTED_SCHOOL_VERIFICATION_ROWSET
        and school_verification.get("mutation_allowed") is False,
        {"verified_school_rows": 1, "rowset_sha256": EXPECTED_SCHOOL_VERIFICATION_ROWSET, "mutation_allowed": False},
        {
            "verified_school_rows": school_verification.get("verified_school_rows"),
            "rowset_sha256": school_verification.get("rowset_sha256"),
            "mutation_allowed": school_verification.get("mutation_allowed"),
        },
        {"summary": "artifacts/data/school_verification_registry_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "operating_snapshot_boundary",
        snapshot.get("rowset_sha256") == EXPECTED_TOP50_SNAPSHOT_ROWSET and snapshot.get("mutation_allowed") is False,
        {"rowset_sha256": EXPECTED_TOP50_SNAPSHOT_ROWSET, "mutation_allowed": False},
        {"rowset_sha256": snapshot.get("rowset_sha256"), "mutation_allowed": snapshot.get("mutation_allowed")},
        {"snapshot": "artifacts/data/top50_engine_operating_snapshot.json"},
    )
    next_lanes = snapshot.get("next_lanes") if isinstance(snapshot.get("next_lanes"), list) else []
    vanderbilt_lane = next(
        (
            lane
            for lane in next_lanes
            if isinstance(lane, dict)
            and lane.get("source_artifact") == "artifacts/data/vanderbilt_public_reviewer_operator_packets.csv"
        ),
        {},
    )
    add_check(
        checks,
        generated_at,
        "snapshot_points_to_vanderbilt_operator_packets",
        vanderbilt_lane.get("status") == "ready_for_public_safe_vanderbilt_operator_packets"
        and vanderbilt_lane.get("rowset_sha256") == EXPECTED_VANDERBILT_OPERATOR_PACKET_ROWSET,
        {
            "status": "ready_for_public_safe_vanderbilt_operator_packets",
            "rowset_sha256": EXPECTED_VANDERBILT_OPERATOR_PACKET_ROWSET,
        },
        {"status": vanderbilt_lane.get("status"), "rowset_sha256": vanderbilt_lane.get("rowset_sha256")},
        {"snapshot_lane": vanderbilt_lane},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_batch_packet_boundary",
        batch_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_BATCH_PACKET_ROWSET
        and batch_summary.get("batch_packet_rows") == 20
        and batch_summary.get("decision_row_count") == 159
        and batch_summary.get("pending_decision_rows") == 159
        and batch_summary.get("invalid_decision_rows") == 0
        and batch_summary.get("raw_candidate_names_committed") is False
        and batch_summary.get("raw_person_urls_committed") is False
        and batch_summary.get("mutation_allowed") is False
        and len(batch_csv) == 20
        and len(batch_json) == 20,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_BATCH_PACKET_ROWSET,
            "batch_packet_rows": 20,
            "decision_row_count": 159,
            "pending_decision_rows": 159,
            "invalid_decision_rows": 0,
            "raw_candidate_names_committed": False,
            "raw_person_urls_committed": False,
            "mutation_allowed": False,
            "csv_rows": 20,
            "json_rows": 20,
        },
        {
            "rowset_sha256": batch_summary.get("rowset_sha256"),
            "batch_packet_rows": batch_summary.get("batch_packet_rows"),
            "decision_row_count": batch_summary.get("decision_row_count"),
            "pending_decision_rows": batch_summary.get("pending_decision_rows"),
            "invalid_decision_rows": batch_summary.get("invalid_decision_rows"),
            "raw_candidate_names_committed": batch_summary.get("raw_candidate_names_committed"),
            "raw_person_urls_committed": batch_summary.get("raw_person_urls_committed"),
            "mutation_allowed": batch_summary.get("mutation_allowed"),
            "csv_rows": len(batch_csv),
            "json_rows": len(batch_json),
        },
        {"summary": "artifacts/data/vanderbilt_candidate_review_batch_packet_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_operator_packet_boundary",
        operator_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_OPERATOR_PACKET_ROWSET
        and operator_summary.get("operator_packet_rows") == 20
        and operator_summary.get("decision_row_count") == 159
        and operator_summary.get("pending_decision_rows") == 159
        and operator_summary.get("missing_required_template_column_mentions") == 0
        and operator_summary.get("raw_candidate_names_committed") is False
        and operator_summary.get("raw_person_urls_committed") is False
        and operator_summary.get("mutation_allowed") is False
        and len(operator_csv) == 20
        and len(operator_json) == 20,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_OPERATOR_PACKET_ROWSET,
            "operator_packet_rows": 20,
            "decision_row_count": 159,
            "pending_decision_rows": 159,
            "missing_required_template_column_mentions": 0,
            "raw_candidate_names_committed": False,
            "raw_person_urls_committed": False,
            "mutation_allowed": False,
            "csv_rows": 20,
            "json_rows": 20,
        },
        {
            "rowset_sha256": operator_summary.get("rowset_sha256"),
            "operator_packet_rows": operator_summary.get("operator_packet_rows"),
            "decision_row_count": operator_summary.get("decision_row_count"),
            "pending_decision_rows": operator_summary.get("pending_decision_rows"),
            "missing_required_template_column_mentions": operator_summary.get(
                "missing_required_template_column_mentions"
            ),
            "raw_candidate_names_committed": operator_summary.get("raw_candidate_names_committed"),
            "raw_person_urls_committed": operator_summary.get("raw_person_urls_committed"),
            "mutation_allowed": operator_summary.get("mutation_allowed"),
            "csv_rows": len(operator_csv),
            "json_rows": len(operator_json),
        },
        {"summary": "artifacts/data/vanderbilt_public_reviewer_operator_packet_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_decision_audit_boundary",
        audit_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_DECISION_AUDIT_ROWSET
        and audit_summary.get("audit_rows") == 159
        and audit_summary.get("pending_rows") == 159
        and audit_summary.get("invalid_rows") == 0
        and audit_summary.get("accepted_person_rows") == 0
        and audit_summary.get("mutation_allowed") is False,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_DECISION_AUDIT_ROWSET,
            "audit_rows": 159,
            "pending_rows": 159,
            "invalid_rows": 0,
            "accepted_person_rows": 0,
            "mutation_allowed": False,
        },
        {
            "rowset_sha256": audit_summary.get("rowset_sha256"),
            "audit_rows": audit_summary.get("audit_rows"),
            "pending_rows": audit_summary.get("pending_rows"),
            "invalid_rows": audit_summary.get("invalid_rows"),
            "accepted_person_rows": audit_summary.get("accepted_person_rows"),
            "mutation_allowed": audit_summary.get("mutation_allowed"),
        },
        {"summary": "artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_scaffold_boundary",
        scaffold_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_SCAFFOLD_ROWSET
        and scaffold_summary.get("decision_scaffold_rows") == 159
        and scaffold_summary.get("manual_decision_template_rows") == 159
        and scaffold_summary.get("mutation_allowed") is False,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_SCAFFOLD_ROWSET,
            "decision_scaffold_rows": 159,
            "manual_decision_template_rows": 159,
            "mutation_allowed": False,
        },
        {
            "rowset_sha256": scaffold_summary.get("rowset_sha256"),
            "decision_scaffold_rows": scaffold_summary.get("decision_scaffold_rows"),
            "manual_decision_template_rows": scaffold_summary.get("manual_decision_template_rows"),
            "mutation_allowed": scaffold_summary.get("mutation_allowed"),
        },
        {"summary": "artifacts/data/vanderbilt_candidate_review_decision_scaffold_summary.json"},
    )
    patch_template_blank_confirmation_counts = patch_template_summary.get("blank_confirmation_rows")
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_patch_template_boundary",
        patch_template_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_PATCH_TEMPLATE_ROWSET
        and patch_template_summary.get("template_rows") == 159
        and patch_template_summary.get("blank_action_rows") == 159
        and isinstance(patch_template_blank_confirmation_counts, dict)
        and all(value == 159 for value in patch_template_blank_confirmation_counts.values())
        and patch_template_summary.get("helper_accepts_template_shape") is True
        and patch_template_summary.get("template_intentionally_invalid_until_filled") is True
        and patch_template_summary.get("valid_non_mutating_rows") == 0
        and patch_template_summary.get("reviewer_note_column_committed") is False
        and patch_template_summary.get("raw_candidate_names_committed") is False
        and patch_template_summary.get("raw_person_urls_committed") is False
        and patch_template_summary.get("mutation_allowed") is False
        and len(patch_template_csv) == 159
        and len(patch_template_json) == 159,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_PATCH_TEMPLATE_ROWSET,
            "template_rows": 159,
            "blank_action_rows": 159,
            "blank_confirmation_rows": 159,
            "helper_accepts_template_shape": True,
            "template_intentionally_invalid_until_filled": True,
            "valid_non_mutating_rows": 0,
            "reviewer_note_column_committed": False,
            "raw_candidate_names_committed": False,
            "raw_person_urls_committed": False,
            "mutation_allowed": False,
            "csv_rows": 159,
            "json_rows": 159,
        },
        {
            "rowset_sha256": patch_template_summary.get("rowset_sha256"),
            "template_rows": patch_template_summary.get("template_rows"),
            "blank_action_rows": patch_template_summary.get("blank_action_rows"),
            "blank_confirmation_rows": patch_template_blank_confirmation_counts,
            "helper_accepts_template_shape": patch_template_summary.get("helper_accepts_template_shape"),
            "template_intentionally_invalid_until_filled": patch_template_summary.get(
                "template_intentionally_invalid_until_filled"
            ),
            "valid_non_mutating_rows": patch_template_summary.get("valid_non_mutating_rows"),
            "reviewer_note_column_committed": patch_template_summary.get("reviewer_note_column_committed"),
            "raw_candidate_names_committed": patch_template_summary.get("raw_candidate_names_committed"),
            "raw_person_urls_committed": patch_template_summary.get("raw_person_urls_committed"),
            "mutation_allowed": patch_template_summary.get("mutation_allowed"),
            "csv_rows": len(patch_template_csv),
            "json_rows": len(patch_template_json),
        },
        {"summary": "artifacts/data/vanderbilt_reviewer_decision_patch_template_summary.json"},
    )
    patch_workbook_blank_confirmation_counts = patch_workbook_summary.get("blank_confirmation_rows")
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_patch_workbook_boundary",
        patch_workbook_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_PATCH_WORKBOOK_ROWSET
        and patch_workbook_summary.get("workbook_rows") == 159
        and patch_workbook_summary.get("operator_packet_rows_represented") == 20
        and patch_workbook_summary.get("decision_fingerprint_present_rows") == 159
        and patch_workbook_summary.get("blank_action_rows") == 159
        and isinstance(patch_workbook_blank_confirmation_counts, dict)
        and all(value == 159 for value in patch_workbook_blank_confirmation_counts.values())
        and patch_workbook_summary.get("helper_patch_extraction_required") is True
        and patch_workbook_summary.get("workbook_intentionally_invalid_as_direct_patch") is True
        and patch_workbook_summary.get("valid_non_mutating_rows") == 0
        and patch_workbook_summary.get("reviewer_note_column_committed") is False
        and patch_workbook_summary.get("raw_candidate_names_committed") is False
        and patch_workbook_summary.get("raw_person_urls_committed") is False
        and patch_workbook_summary.get("mutation_allowed") is False
        and len(patch_workbook_csv) == 159
        and len(patch_workbook_json) == 159,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_PATCH_WORKBOOK_ROWSET,
            "workbook_rows": 159,
            "operator_packet_rows_represented": 20,
            "decision_fingerprint_present_rows": 159,
            "blank_action_rows": 159,
            "blank_confirmation_rows": 159,
            "helper_patch_extraction_required": True,
            "workbook_intentionally_invalid_as_direct_patch": True,
            "valid_non_mutating_rows": 0,
            "reviewer_note_column_committed": False,
            "raw_candidate_names_committed": False,
            "raw_person_urls_committed": False,
            "mutation_allowed": False,
            "csv_rows": 159,
            "json_rows": 159,
        },
        {
            "rowset_sha256": patch_workbook_summary.get("rowset_sha256"),
            "workbook_rows": patch_workbook_summary.get("workbook_rows"),
            "operator_packet_rows_represented": patch_workbook_summary.get("operator_packet_rows_represented"),
            "decision_fingerprint_present_rows": patch_workbook_summary.get("decision_fingerprint_present_rows"),
            "blank_action_rows": patch_workbook_summary.get("blank_action_rows"),
            "blank_confirmation_rows": patch_workbook_blank_confirmation_counts,
            "helper_patch_extraction_required": patch_workbook_summary.get("helper_patch_extraction_required"),
            "workbook_intentionally_invalid_as_direct_patch": patch_workbook_summary.get(
                "workbook_intentionally_invalid_as_direct_patch"
            ),
            "valid_non_mutating_rows": patch_workbook_summary.get("valid_non_mutating_rows"),
            "reviewer_note_column_committed": patch_workbook_summary.get("reviewer_note_column_committed"),
            "raw_candidate_names_committed": patch_workbook_summary.get("raw_candidate_names_committed"),
            "raw_person_urls_committed": patch_workbook_summary.get("raw_person_urls_committed"),
            "mutation_allowed": patch_workbook_summary.get("mutation_allowed"),
            "csv_rows": len(patch_workbook_csv),
            "json_rows": len(patch_workbook_json),
        },
        {"summary": "artifacts/data/vanderbilt_reviewer_decision_patch_workbook_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_workbook_slice_index_boundary",
        slice_index_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_WORKBOOK_SLICE_INDEX_ROWSET
        and slice_index_summary.get("slice_index_rows") == 20
        and slice_index_summary.get("workbook_rows_represented") == 159
        and slice_index_summary.get("slice_outputs_default_tmp_only") is True
        and slice_index_summary.get("reviewer_note_column_committed") is False
        and slice_index_summary.get("raw_candidate_names_committed") is False
        and slice_index_summary.get("raw_person_urls_committed") is False
        and slice_index_summary.get("mutation_allowed") is False
        and len(slice_index_csv) == 20
        and len(slice_index_json) == 20,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_WORKBOOK_SLICE_INDEX_ROWSET,
            "slice_index_rows": 20,
            "workbook_rows_represented": 159,
            "slice_outputs_default_tmp_only": True,
            "reviewer_note_column_committed": False,
            "raw_candidate_names_committed": False,
            "raw_person_urls_committed": False,
            "mutation_allowed": False,
            "csv_rows": 20,
            "json_rows": 20,
        },
        {
            "rowset_sha256": slice_index_summary.get("rowset_sha256"),
            "slice_index_rows": slice_index_summary.get("slice_index_rows"),
            "workbook_rows_represented": slice_index_summary.get("workbook_rows_represented"),
            "slice_outputs_default_tmp_only": slice_index_summary.get("slice_outputs_default_tmp_only"),
            "reviewer_note_column_committed": slice_index_summary.get("reviewer_note_column_committed"),
            "raw_candidate_names_committed": slice_index_summary.get("raw_candidate_names_committed"),
            "raw_person_urls_committed": slice_index_summary.get("raw_person_urls_committed"),
            "mutation_allowed": slice_index_summary.get("mutation_allowed"),
            "csv_rows": len(slice_index_csv),
            "json_rows": len(slice_index_json),
        },
        {"summary": "artifacts/data/vanderbilt_reviewer_decision_patch_workbook_slice_index_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_execution_readiness_bridge_boundary",
        execution_readiness_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_EXECUTION_READINESS_BRIDGE_ROWSET
        and execution_readiness_summary.get("bridge_rows") == 19
        and execution_readiness_summary.get("ready_program_rows") == 19
        and execution_readiness_summary.get("not_ready_program_rows") == 0
        and execution_readiness_summary.get("slice_index_rows_represented") == 20
        and execution_readiness_summary.get("workbook_rows_represented") == 159
        and execution_readiness_summary.get("pending_decision_rows_represented") == 159
        and execution_readiness_summary.get("review_queue_rows_represented") == 159
        and execution_readiness_summary.get("valid_non_mutating_decision_rows_represented") == 0
        and execution_readiness_summary.get("invalid_decision_rows_represented") == 0
        and execution_readiness_summary.get("slice_output_paths_tmp_only") is True
        and execution_readiness_summary.get("patch_output_paths_tmp_only") is True
        and execution_readiness_summary.get("extract_commands_present") is True
        and execution_readiness_summary.get("patch_dry_run_commands_present") is True
        and execution_readiness_summary.get("apply_commands_present") is True
        and execution_readiness_summary.get("mutation_allowed") is False
        and execution_readiness_summary.get("person_ingestion_allowed") is False
        and len(execution_readiness_csv) == 19
        and len(execution_readiness_json) == 19,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_EXECUTION_READINESS_BRIDGE_ROWSET,
            "bridge_rows": 19,
            "ready_program_rows": 19,
            "not_ready_program_rows": 0,
            "slice_index_rows_represented": 20,
            "workbook_rows_represented": 159,
            "pending_decision_rows_represented": 159,
            "review_queue_rows_represented": 159,
            "valid_non_mutating_decision_rows_represented": 0,
            "invalid_decision_rows_represented": 0,
            "slice_output_paths_tmp_only": True,
            "patch_output_paths_tmp_only": True,
            "extract_commands_present": True,
            "patch_dry_run_commands_present": True,
            "apply_commands_present": True,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "csv_rows": 19,
            "json_rows": 19,
        },
        {
            "rowset_sha256": execution_readiness_summary.get("rowset_sha256"),
            "bridge_rows": execution_readiness_summary.get("bridge_rows"),
            "ready_program_rows": execution_readiness_summary.get("ready_program_rows"),
            "not_ready_program_rows": execution_readiness_summary.get("not_ready_program_rows"),
            "slice_index_rows_represented": execution_readiness_summary.get("slice_index_rows_represented"),
            "workbook_rows_represented": execution_readiness_summary.get("workbook_rows_represented"),
            "pending_decision_rows_represented": execution_readiness_summary.get(
                "pending_decision_rows_represented"
            ),
            "review_queue_rows_represented": execution_readiness_summary.get("review_queue_rows_represented"),
            "valid_non_mutating_decision_rows_represented": execution_readiness_summary.get(
                "valid_non_mutating_decision_rows_represented"
            ),
            "invalid_decision_rows_represented": execution_readiness_summary.get(
                "invalid_decision_rows_represented"
            ),
            "slice_output_paths_tmp_only": execution_readiness_summary.get("slice_output_paths_tmp_only"),
            "patch_output_paths_tmp_only": execution_readiness_summary.get("patch_output_paths_tmp_only"),
            "extract_commands_present": execution_readiness_summary.get("extract_commands_present"),
            "patch_dry_run_commands_present": execution_readiness_summary.get("patch_dry_run_commands_present"),
            "apply_commands_present": execution_readiness_summary.get("apply_commands_present"),
            "mutation_allowed": execution_readiness_summary.get("mutation_allowed"),
            "person_ingestion_allowed": execution_readiness_summary.get("person_ingestion_allowed"),
            "csv_rows": len(execution_readiness_csv),
            "json_rows": len(execution_readiness_json),
        },
        {"summary": "artifacts/data/vanderbilt_reviewer_execution_readiness_bridge_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_blank_execution_verification_boundary",
        blank_execution_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_BLANK_EXECUTION_VERIFICATION_ROWSET
        and blank_execution_summary.get("verification_rows") == 20
        and blank_execution_summary.get("pass_rows") == 20
        and blank_execution_summary.get("fail_rows") == 0
        and blank_execution_summary.get("slice_rows_represented") == 159
        and blank_execution_summary.get("blank_extract_fail_closed_rows") == 20
        and blank_execution_summary.get("allow_empty_patch_rows_represented") == 0
        and blank_execution_summary.get("dry_run_patch_rows_represented") == 0
        and blank_execution_summary.get("dry_run_valid_non_mutating_rows_represented") == 0
        and blank_execution_summary.get("tmp_outputs_removed_rows") == 20
        and blank_execution_summary.get("mutation_allowed") is False
        and blank_execution_summary.get("person_ingestion_allowed") is False
        and blank_execution_summary.get("apply_executed") is False
        and len(blank_execution_csv) == 20
        and len(blank_execution_json) == 20,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_BLANK_EXECUTION_VERIFICATION_ROWSET,
            "verification_rows": 20,
            "pass_rows": 20,
            "fail_rows": 0,
            "slice_rows_represented": 159,
            "blank_extract_fail_closed_rows": 20,
            "allow_empty_patch_rows_represented": 0,
            "dry_run_patch_rows_represented": 0,
            "dry_run_valid_non_mutating_rows_represented": 0,
            "tmp_outputs_removed_rows": 20,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "apply_executed": False,
            "csv_rows": 20,
            "json_rows": 20,
        },
        {
            "rowset_sha256": blank_execution_summary.get("rowset_sha256"),
            "verification_rows": blank_execution_summary.get("verification_rows"),
            "pass_rows": blank_execution_summary.get("pass_rows"),
            "fail_rows": blank_execution_summary.get("fail_rows"),
            "slice_rows_represented": blank_execution_summary.get("slice_rows_represented"),
            "blank_extract_fail_closed_rows": blank_execution_summary.get("blank_extract_fail_closed_rows"),
            "allow_empty_patch_rows_represented": blank_execution_summary.get(
                "allow_empty_patch_rows_represented"
            ),
            "dry_run_patch_rows_represented": blank_execution_summary.get("dry_run_patch_rows_represented"),
            "dry_run_valid_non_mutating_rows_represented": blank_execution_summary.get(
                "dry_run_valid_non_mutating_rows_represented"
            ),
            "tmp_outputs_removed_rows": blank_execution_summary.get("tmp_outputs_removed_rows"),
            "mutation_allowed": blank_execution_summary.get("mutation_allowed"),
            "person_ingestion_allowed": blank_execution_summary.get("person_ingestion_allowed"),
            "apply_executed": blank_execution_summary.get("apply_executed"),
            "csv_rows": len(blank_execution_csv),
            "json_rows": len(blank_execution_json),
        },
        {"summary": "artifacts/data/vanderbilt_reviewer_blank_execution_verification_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_slice_prioritization_plan_boundary",
        slice_prioritization_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_SLICE_PRIORITIZATION_ROWSET
        and slice_prioritization_summary.get("prioritization_rows") == 20
        and slice_prioritization_summary.get("slice_rows_represented") == 159
        and slice_prioritization_summary.get("ready_for_bounded_human_reviewer_input_rows") == 20
        and slice_prioritization_summary.get("blank_execution_pass_rows_represented") == 20
        and slice_prioritization_summary.get("dry_run_patch_rows_represented") == 0
        and slice_prioritization_summary.get("accepted_person_rows") == 0
        and slice_prioritization_summary.get("apply_executed") is False
        and slice_prioritization_summary.get("mutation_allowed") is False
        and slice_prioritization_summary.get("person_ingestion_allowed") is False
        and slice_prioritization_summary.get("first_priority_execution_order") == "4"
        and slice_prioritization_summary.get("first_priority_program_name") == "General Surgery"
        and slice_prioritization_summary.get("first_priority_workbook_row_count") == 2
        and len(slice_prioritization_csv) == 20
        and len(slice_prioritization_json) == 20,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_SLICE_PRIORITIZATION_ROWSET,
            "prioritization_rows": 20,
            "slice_rows_represented": 159,
            "ready_for_bounded_human_reviewer_input_rows": 20,
            "blank_execution_pass_rows_represented": 20,
            "dry_run_patch_rows_represented": 0,
            "accepted_person_rows": 0,
            "apply_executed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "first_priority_execution_order": "4",
            "first_priority_program_name": "General Surgery",
            "first_priority_workbook_row_count": 2,
            "csv_rows": 20,
            "json_rows": 20,
        },
        {
            "rowset_sha256": slice_prioritization_summary.get("rowset_sha256"),
            "prioritization_rows": slice_prioritization_summary.get("prioritization_rows"),
            "slice_rows_represented": slice_prioritization_summary.get("slice_rows_represented"),
            "ready_for_bounded_human_reviewer_input_rows": slice_prioritization_summary.get(
                "ready_for_bounded_human_reviewer_input_rows"
            ),
            "blank_execution_pass_rows_represented": slice_prioritization_summary.get(
                "blank_execution_pass_rows_represented"
            ),
            "dry_run_patch_rows_represented": slice_prioritization_summary.get("dry_run_patch_rows_represented"),
            "accepted_person_rows": slice_prioritization_summary.get("accepted_person_rows"),
            "apply_executed": slice_prioritization_summary.get("apply_executed"),
            "mutation_allowed": slice_prioritization_summary.get("mutation_allowed"),
            "person_ingestion_allowed": slice_prioritization_summary.get("person_ingestion_allowed"),
            "first_priority_execution_order": slice_prioritization_summary.get("first_priority_execution_order"),
            "first_priority_program_name": slice_prioritization_summary.get("first_priority_program_name"),
            "first_priority_workbook_row_count": slice_prioritization_summary.get(
                "first_priority_workbook_row_count"
            ),
            "csv_rows": len(slice_prioritization_csv),
            "json_rows": len(slice_prioritization_json),
        },
        {"summary": "artifacts/data/vanderbilt_reviewer_slice_prioritization_plan_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_priority_reviewer_instruction_packet_boundary",
        priority_instruction_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_PRIORITY_INSTRUCTION_ROWSET
        and priority_instruction_summary.get("instruction_rows") == 2
        and priority_instruction_summary.get("priority_rank") == "1"
        and priority_instruction_summary.get("execution_order") == "4"
        and priority_instruction_summary.get("program_name") == "General Surgery"
        and priority_instruction_summary.get("pending_blank_instruction_rows") == 2
        and priority_instruction_summary.get("free_text_note_column_committed") is False
        and priority_instruction_summary.get("raw_candidate_names_committed") is False
        and priority_instruction_summary.get("raw_person_urls_committed") is False
        and priority_instruction_summary.get("accepted_person_rows") == 0
        and priority_instruction_summary.get("apply_executed") is False
        and priority_instruction_summary.get("mutation_allowed") is False
        and priority_instruction_summary.get("person_ingestion_allowed") is False
        and len(priority_instruction_csv) == 2
        and len(priority_instruction_json) == 2,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_PRIORITY_INSTRUCTION_ROWSET,
            "instruction_rows": 2,
            "priority_rank": "1",
            "execution_order": "4",
            "program_name": "General Surgery",
            "pending_blank_instruction_rows": 2,
            "free_text_note_column_committed": False,
            "raw_candidate_names_committed": False,
            "raw_person_urls_committed": False,
            "accepted_person_rows": 0,
            "apply_executed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "csv_rows": 2,
            "json_rows": 2,
        },
        {
            "rowset_sha256": priority_instruction_summary.get("rowset_sha256"),
            "instruction_rows": priority_instruction_summary.get("instruction_rows"),
            "priority_rank": priority_instruction_summary.get("priority_rank"),
            "execution_order": priority_instruction_summary.get("execution_order"),
            "program_name": priority_instruction_summary.get("program_name"),
            "pending_blank_instruction_rows": priority_instruction_summary.get("pending_blank_instruction_rows"),
            "free_text_note_column_committed": priority_instruction_summary.get("free_text_note_column_committed"),
            "raw_candidate_names_committed": priority_instruction_summary.get("raw_candidate_names_committed"),
            "raw_person_urls_committed": priority_instruction_summary.get("raw_person_urls_committed"),
            "accepted_person_rows": priority_instruction_summary.get("accepted_person_rows"),
            "apply_executed": priority_instruction_summary.get("apply_executed"),
            "mutation_allowed": priority_instruction_summary.get("mutation_allowed"),
            "person_ingestion_allowed": priority_instruction_summary.get("person_ingestion_allowed"),
            "csv_rows": len(priority_instruction_csv),
            "json_rows": len(priority_instruction_json),
        },
        {"summary": "artifacts/data/vanderbilt_priority_reviewer_instruction_packet_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_patch_helper_fixture_verification_boundary",
        patch_fixture_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_PATCH_HELPER_FIXTURE_ROWSET
        and patch_fixture_summary.get("fixture_check_rows") == 16
        and patch_fixture_summary.get("pass_rows") == 16
        and patch_fixture_summary.get("fail_rows") == 0
        and patch_fixture_summary.get("synthetic_fixture_only") is True
        and patch_fixture_summary.get("real_vanderbilt_rows_used") == 0
        and patch_fixture_summary.get("accepted_person_rows") == 0
        and patch_fixture_summary.get("apply_executed") is False
        and patch_fixture_summary.get("mutation_allowed") is False
        and patch_fixture_summary.get("person_ingestion_allowed") is False
        and len(patch_fixture_csv) == 16
        and len(patch_fixture_json) == 16,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_PATCH_HELPER_FIXTURE_ROWSET,
            "fixture_check_rows": 16,
            "pass_rows": 16,
            "fail_rows": 0,
            "synthetic_fixture_only": True,
            "real_vanderbilt_rows_used": 0,
            "accepted_person_rows": 0,
            "apply_executed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "csv_rows": 16,
            "json_rows": 16,
        },
        {
            "rowset_sha256": patch_fixture_summary.get("rowset_sha256"),
            "fixture_check_rows": patch_fixture_summary.get("fixture_check_rows"),
            "pass_rows": patch_fixture_summary.get("pass_rows"),
            "fail_rows": patch_fixture_summary.get("fail_rows"),
            "synthetic_fixture_only": patch_fixture_summary.get("synthetic_fixture_only"),
            "real_vanderbilt_rows_used": patch_fixture_summary.get("real_vanderbilt_rows_used"),
            "accepted_person_rows": patch_fixture_summary.get("accepted_person_rows"),
            "apply_executed": patch_fixture_summary.get("apply_executed"),
            "mutation_allowed": patch_fixture_summary.get("mutation_allowed"),
            "person_ingestion_allowed": patch_fixture_summary.get("person_ingestion_allowed"),
            "csv_rows": len(patch_fixture_csv),
            "json_rows": len(patch_fixture_json),
        },
        {"summary": "artifacts/data/vanderbilt_patch_helper_fixture_verification_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_priority_reviewer_handoff_packet_boundary",
        priority_handoff_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_PRIORITY_HANDOFF_ROWSET
        and priority_handoff_summary.get("handoff_rows") == 1
        and priority_handoff_summary.get("priority_rank") == "1"
        and priority_handoff_summary.get("execution_order") == "4"
        and priority_handoff_summary.get("program_name") == "General Surgery"
        and priority_handoff_summary.get("instruction_rows_represented") == 2
        and priority_handoff_summary.get("pending_blank_instruction_rows") == 2
        and priority_handoff_summary.get("fixture_check_rows") == 16
        and priority_handoff_summary.get("fixture_pass_rows") == 16
        and priority_handoff_summary.get("fixture_fail_rows") == 0
        and priority_handoff_summary.get("blank_extract_fail_closed_rows") == 20
        and priority_handoff_summary.get("decision_audit_valid_non_mutating_rows") == 0
        and priority_handoff_summary.get("decision_audit_invalid_rows") == 0
        and priority_handoff_summary.get("slice_command_present") is True
        and priority_handoff_summary.get("extract_command_present") is True
        and priority_handoff_summary.get("patch_dry_run_command_present") is True
        and priority_handoff_summary.get("apply_command_allowed") is False
        and priority_handoff_summary.get("accepted_person_rows") == 0
        and priority_handoff_summary.get("apply_executed") is False
        and priority_handoff_summary.get("raw_candidate_names_committed") is False
        and priority_handoff_summary.get("raw_person_urls_committed") is False
        and priority_handoff_summary.get("free_text_note_column_committed") is False
        and priority_handoff_summary.get("mutation_allowed") is False
        and priority_handoff_summary.get("person_ingestion_allowed") is False
        and priority_handoff_summary.get("denominator_closure_allowed") is False
        and priority_handoff_summary.get("source_priority_instruction_rowset_sha256")
        == EXPECTED_VANDERBILT_PRIORITY_INSTRUCTION_ROWSET
        and priority_handoff_summary.get("source_patch_helper_fixture_rowset_sha256")
        == EXPECTED_VANDERBILT_PATCH_HELPER_FIXTURE_ROWSET
        and priority_handoff_summary.get("source_slice_prioritization_rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_PRIORITIZATION_ROWSET
        and priority_handoff_summary.get("source_blank_execution_verification_rowset_sha256")
        == EXPECTED_VANDERBILT_BLANK_EXECUTION_VERIFICATION_ROWSET
        and priority_handoff_summary.get("source_decision_audit_rowset_sha256")
        == EXPECTED_VANDERBILT_DECISION_AUDIT_ROWSET
        and len(priority_handoff_csv) == 1
        and len(priority_handoff_json) == 1,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_PRIORITY_HANDOFF_ROWSET,
            "handoff_rows": 1,
            "priority_rank": "1",
            "execution_order": "4",
            "program_name": "General Surgery",
            "instruction_rows_represented": 2,
            "pending_blank_instruction_rows": 2,
            "fixture_check_rows": 16,
            "fixture_pass_rows": 16,
            "fixture_fail_rows": 0,
            "blank_extract_fail_closed_rows": 20,
            "decision_audit_valid_non_mutating_rows": 0,
            "decision_audit_invalid_rows": 0,
            "commands_present": True,
            "apply_command_allowed": False,
            "accepted_person_rows": 0,
            "apply_executed": False,
            "raw_candidate_names_committed": False,
            "raw_person_urls_committed": False,
            "free_text_note_column_committed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
            "csv_rows": 1,
            "json_rows": 1,
        },
        {
            "rowset_sha256": priority_handoff_summary.get("rowset_sha256"),
            "handoff_rows": priority_handoff_summary.get("handoff_rows"),
            "priority_rank": priority_handoff_summary.get("priority_rank"),
            "execution_order": priority_handoff_summary.get("execution_order"),
            "program_name": priority_handoff_summary.get("program_name"),
            "instruction_rows_represented": priority_handoff_summary.get("instruction_rows_represented"),
            "pending_blank_instruction_rows": priority_handoff_summary.get("pending_blank_instruction_rows"),
            "fixture_check_rows": priority_handoff_summary.get("fixture_check_rows"),
            "fixture_pass_rows": priority_handoff_summary.get("fixture_pass_rows"),
            "fixture_fail_rows": priority_handoff_summary.get("fixture_fail_rows"),
            "blank_extract_fail_closed_rows": priority_handoff_summary.get("blank_extract_fail_closed_rows"),
            "decision_audit_valid_non_mutating_rows": priority_handoff_summary.get(
                "decision_audit_valid_non_mutating_rows"
            ),
            "decision_audit_invalid_rows": priority_handoff_summary.get("decision_audit_invalid_rows"),
            "slice_command_present": priority_handoff_summary.get("slice_command_present"),
            "extract_command_present": priority_handoff_summary.get("extract_command_present"),
            "patch_dry_run_command_present": priority_handoff_summary.get("patch_dry_run_command_present"),
            "apply_command_allowed": priority_handoff_summary.get("apply_command_allowed"),
            "accepted_person_rows": priority_handoff_summary.get("accepted_person_rows"),
            "apply_executed": priority_handoff_summary.get("apply_executed"),
            "raw_candidate_names_committed": priority_handoff_summary.get("raw_candidate_names_committed"),
            "raw_person_urls_committed": priority_handoff_summary.get("raw_person_urls_committed"),
            "free_text_note_column_committed": priority_handoff_summary.get("free_text_note_column_committed"),
            "mutation_allowed": priority_handoff_summary.get("mutation_allowed"),
            "person_ingestion_allowed": priority_handoff_summary.get("person_ingestion_allowed"),
            "denominator_closure_allowed": priority_handoff_summary.get("denominator_closure_allowed"),
            "source_priority_instruction_rowset_sha256": priority_handoff_summary.get(
                "source_priority_instruction_rowset_sha256"
            ),
            "source_patch_helper_fixture_rowset_sha256": priority_handoff_summary.get(
                "source_patch_helper_fixture_rowset_sha256"
            ),
            "source_slice_prioritization_rowset_sha256": priority_handoff_summary.get(
                "source_slice_prioritization_rowset_sha256"
            ),
            "source_blank_execution_verification_rowset_sha256": priority_handoff_summary.get(
                "source_blank_execution_verification_rowset_sha256"
            ),
            "source_decision_audit_rowset_sha256": priority_handoff_summary.get("source_decision_audit_rowset_sha256"),
            "csv_rows": len(priority_handoff_csv),
            "json_rows": len(priority_handoff_json),
        },
        {"summary": "artifacts/data/vanderbilt_priority_reviewer_handoff_packet_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_synthetic_handoff_dry_run_demo_boundary",
        synthetic_handoff_demo_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_SYNTHETIC_HANDOFF_DRY_RUN_ROWSET
        and synthetic_handoff_demo_summary.get("demo_check_rows") == 5
        and synthetic_handoff_demo_summary.get("pass_rows") == 5
        and synthetic_handoff_demo_summary.get("fail_rows") == 0
        and synthetic_handoff_demo_summary.get("synthetic_fixture_only") is True
        and synthetic_handoff_demo_summary.get("real_vanderbilt_rows_used") == 0
        and synthetic_handoff_demo_summary.get("synthetic_input_rows_written") == 6
        and synthetic_handoff_demo_summary.get("slice_rows") == 2
        and synthetic_handoff_demo_summary.get("extracted_patch_rows") == 1
        and synthetic_handoff_demo_summary.get("valid_non_mutating_rows") == 1
        and synthetic_handoff_demo_summary.get("dry_run_patch_rows") == 1
        and synthetic_handoff_demo_summary.get("dry_run_outputs_written") == 0
        and synthetic_handoff_demo_summary.get("tmp_outputs_removed") is True
        and synthetic_handoff_demo_summary.get("accepted_person_rows") == 0
        and synthetic_handoff_demo_summary.get("apply_executed") is False
        and synthetic_handoff_demo_summary.get("mutation_allowed") is False
        and synthetic_handoff_demo_summary.get("person_ingestion_allowed") is False
        and synthetic_handoff_demo_summary.get("denominator_closure_allowed") is False
        and len(synthetic_handoff_demo_csv) == 5
        and len(synthetic_handoff_demo_json) == 5,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_SYNTHETIC_HANDOFF_DRY_RUN_ROWSET,
            "demo_check_rows": 5,
            "pass_rows": 5,
            "fail_rows": 0,
            "synthetic_fixture_only": True,
            "real_vanderbilt_rows_used": 0,
            "synthetic_input_rows_written": 6,
            "slice_rows": 2,
            "extracted_patch_rows": 1,
            "valid_non_mutating_rows": 1,
            "dry_run_patch_rows": 1,
            "dry_run_outputs_written": 0,
            "tmp_outputs_removed": True,
            "accepted_person_rows": 0,
            "apply_executed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
            "csv_rows": 5,
            "json_rows": 5,
        },
        {
            "rowset_sha256": synthetic_handoff_demo_summary.get("rowset_sha256"),
            "demo_check_rows": synthetic_handoff_demo_summary.get("demo_check_rows"),
            "pass_rows": synthetic_handoff_demo_summary.get("pass_rows"),
            "fail_rows": synthetic_handoff_demo_summary.get("fail_rows"),
            "synthetic_fixture_only": synthetic_handoff_demo_summary.get("synthetic_fixture_only"),
            "real_vanderbilt_rows_used": synthetic_handoff_demo_summary.get("real_vanderbilt_rows_used"),
            "synthetic_input_rows_written": synthetic_handoff_demo_summary.get("synthetic_input_rows_written"),
            "slice_rows": synthetic_handoff_demo_summary.get("slice_rows"),
            "extracted_patch_rows": synthetic_handoff_demo_summary.get("extracted_patch_rows"),
            "valid_non_mutating_rows": synthetic_handoff_demo_summary.get("valid_non_mutating_rows"),
            "dry_run_patch_rows": synthetic_handoff_demo_summary.get("dry_run_patch_rows"),
            "dry_run_outputs_written": synthetic_handoff_demo_summary.get("dry_run_outputs_written"),
            "tmp_outputs_removed": synthetic_handoff_demo_summary.get("tmp_outputs_removed"),
            "accepted_person_rows": synthetic_handoff_demo_summary.get("accepted_person_rows"),
            "apply_executed": synthetic_handoff_demo_summary.get("apply_executed"),
            "mutation_allowed": synthetic_handoff_demo_summary.get("mutation_allowed"),
            "person_ingestion_allowed": synthetic_handoff_demo_summary.get("person_ingestion_allowed"),
            "denominator_closure_allowed": synthetic_handoff_demo_summary.get("denominator_closure_allowed"),
            "csv_rows": len(synthetic_handoff_demo_csv),
            "json_rows": len(synthetic_handoff_demo_json),
        },
        {"summary": "artifacts/data/vanderbilt_synthetic_handoff_dry_run_demo_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_manifest_committed_rows",
        gap_summary.get("rows") == 113
        and gap_summary.get("open_gap_rows") == 113
        and gap_summary.get("mutation_allowed") is False
        and len(gap_csv) == 113,
        {"rows": 113, "open_gap_rows": 113, "mutation_allowed": False, "csv_rows": 113},
        {
            "rows": gap_summary.get("rows"),
            "open_gap_rows": gap_summary.get("open_gap_rows"),
            "mutation_allowed": gap_summary.get("mutation_allowed"),
            "csv_rows": len(gap_csv),
        },
        {"summary": "artifacts/data/school_gap_resolution_manifest_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_batch_slice_index_boundary",
        gap_batch_summary.get("rows") == 21
        and gap_batch_summary.get("gap_rows") == 113
        and gap_batch_summary.get("mutation_allowed") is False
        and len(gap_batch_csv) == 21
        and gap_packet_summary.get("rows") == 113
        and gap_packet_summary.get("batch_rows") == 21
        and gap_packet_summary.get("mutation_allowed") is False
        and len(gap_packet_csv) == 113
        and gap_slice_summary.get("rowset_sha256") == EXPECTED_GAP_BATCH_SLICE_INDEX_ROWSET
        and gap_slice_summary.get("slice_index_rows") == 21
        and gap_slice_summary.get("gap_rows_represented") == 113
        and gap_slice_summary.get("slice_outputs_default_tmp_only") is True
        and gap_slice_summary.get("private_artifact_paths_committed") is False
        and gap_slice_summary.get("mutation_allowed") is False
        and len(gap_slice_csv) == 21
        and len(gap_slice_json) == 21,
        {
            "batch_rows": 21,
            "gap_rows": 113,
            "packet_rows": 113,
            "rowset_sha256": EXPECTED_GAP_BATCH_SLICE_INDEX_ROWSET,
            "slice_index_rows": 21,
            "gap_rows_represented": 113,
            "slice_outputs_default_tmp_only": True,
            "private_artifact_paths_committed": False,
            "mutation_allowed": False,
            "csv_rows": 21,
            "json_rows": 21,
        },
        {
            "batch_rows": gap_batch_summary.get("rows"),
            "batch_gap_rows": gap_batch_summary.get("gap_rows"),
            "batch_mutation_allowed": gap_batch_summary.get("mutation_allowed"),
            "batch_csv_rows": len(gap_batch_csv),
            "packet_rows": gap_packet_summary.get("rows"),
            "packet_batch_rows": gap_packet_summary.get("batch_rows"),
            "packet_mutation_allowed": gap_packet_summary.get("mutation_allowed"),
            "packet_csv_rows": len(gap_packet_csv),
            "rowset_sha256": gap_slice_summary.get("rowset_sha256"),
            "slice_index_rows": gap_slice_summary.get("slice_index_rows"),
            "gap_rows_represented": gap_slice_summary.get("gap_rows_represented"),
            "slice_outputs_default_tmp_only": gap_slice_summary.get("slice_outputs_default_tmp_only"),
            "private_artifact_paths_committed": gap_slice_summary.get("private_artifact_paths_committed"),
            "mutation_allowed": gap_slice_summary.get("mutation_allowed"),
            "csv_rows": len(gap_slice_csv),
            "json_rows": len(gap_slice_json),
        },
        {"summary": "artifacts/data/school_gap_resolution_batch_slice_index_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_open_gap_manifest_triage_boundary",
        vanderbilt_open_gap_triage_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_OPEN_GAP_TRIAGE_ROWSET
        and vanderbilt_open_gap_triage_summary.get("triage_rows") == 21
        and vanderbilt_open_gap_triage_summary.get("gap_rows_represented") == 113
        and vanderbilt_open_gap_triage_summary.get("source_slice_index_rowset_sha256")
        == EXPECTED_GAP_BATCH_SLICE_INDEX_ROWSET
        and vanderbilt_open_gap_triage_summary.get("slice_outputs_default_tmp_only") is True
        and vanderbilt_open_gap_triage_summary.get("private_artifact_paths_committed") is False
        and vanderbilt_open_gap_triage_summary.get("raw_dump_publication_allowed") is False
        and vanderbilt_open_gap_triage_summary.get("mutation_allowed") is False
        and vanderbilt_open_gap_triage_summary.get("person_ingestion_allowed") is False
        and vanderbilt_open_gap_triage_summary.get("denominator_closure_allowed") is False
        and vanderbilt_open_gap_triage_summary.get("school_verification_allowed") is False
        and len(vanderbilt_open_gap_triage_csv) == 21
        and len(vanderbilt_open_gap_triage_json) == 21,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_OPEN_GAP_TRIAGE_ROWSET,
            "triage_rows": 21,
            "gap_rows_represented": 113,
            "source_slice_index_rowset_sha256": EXPECTED_GAP_BATCH_SLICE_INDEX_ROWSET,
            "slice_outputs_default_tmp_only": True,
            "private_artifact_paths_committed": False,
            "raw_dump_publication_allowed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
            "school_verification_allowed": False,
            "csv_rows": 21,
            "json_rows": 21,
        },
        {
            "rowset_sha256": vanderbilt_open_gap_triage_summary.get("rowset_sha256"),
            "triage_rows": vanderbilt_open_gap_triage_summary.get("triage_rows"),
            "gap_rows_represented": vanderbilt_open_gap_triage_summary.get("gap_rows_represented"),
            "source_slice_index_rowset_sha256": vanderbilt_open_gap_triage_summary.get(
                "source_slice_index_rowset_sha256"
            ),
            "slice_outputs_default_tmp_only": vanderbilt_open_gap_triage_summary.get(
                "slice_outputs_default_tmp_only"
            ),
            "private_artifact_paths_committed": vanderbilt_open_gap_triage_summary.get(
                "private_artifact_paths_committed"
            ),
            "raw_dump_publication_allowed": vanderbilt_open_gap_triage_summary.get("raw_dump_publication_allowed"),
            "mutation_allowed": vanderbilt_open_gap_triage_summary.get("mutation_allowed"),
            "person_ingestion_allowed": vanderbilt_open_gap_triage_summary.get("person_ingestion_allowed"),
            "denominator_closure_allowed": vanderbilt_open_gap_triage_summary.get(
                "denominator_closure_allowed"
            ),
            "school_verification_allowed": vanderbilt_open_gap_triage_summary.get("school_verification_allowed"),
            "csv_rows": len(vanderbilt_open_gap_triage_csv),
            "json_rows": len(vanderbilt_open_gap_triage_json),
        },
        {"summary": "artifacts/data/vanderbilt_open_gap_manifest_triage_packet_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_triage_slice_definition_contract_boundary",
        vanderbilt_triage_contract_summary.get("rowset_sha256") == EXPECTED_VANDERBILT_TRIAGE_CONTRACT_ROWSET
        and vanderbilt_triage_contract_summary.get("contract_rows") == 4
        and vanderbilt_triage_contract_summary.get("slice_rows_represented") == 21
        and vanderbilt_triage_contract_summary.get("gap_rows_represented") == 113
        and vanderbilt_triage_contract_summary.get("slice_outputs_default_tmp_only") is True
        and vanderbilt_triage_contract_summary.get("private_artifact_paths_committed") is False
        and vanderbilt_triage_contract_summary.get("raw_dump_publication_allowed") is False
        and vanderbilt_triage_contract_summary.get("mutation_allowed") is False
        and vanderbilt_triage_contract_summary.get("person_ingestion_allowed") is False
        and vanderbilt_triage_contract_summary.get("denominator_closure_allowed") is False
        and vanderbilt_triage_contract_summary.get("school_verification_allowed") is False
        and len(vanderbilt_triage_contract_csv) == 4
        and len(vanderbilt_triage_contract_json) == 4,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_TRIAGE_CONTRACT_ROWSET,
            "contract_rows": 4,
            "slice_rows_represented": 21,
            "gap_rows_represented": 113,
            "slice_outputs_default_tmp_only": True,
            "private_artifact_paths_committed": False,
            "raw_dump_publication_allowed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
            "school_verification_allowed": False,
            "csv_rows": 4,
            "json_rows": 4,
        },
        {
            "rowset_sha256": vanderbilt_triage_contract_summary.get("rowset_sha256"),
            "contract_rows": vanderbilt_triage_contract_summary.get("contract_rows"),
            "slice_rows_represented": vanderbilt_triage_contract_summary.get("slice_rows_represented"),
            "gap_rows_represented": vanderbilt_triage_contract_summary.get("gap_rows_represented"),
            "slice_outputs_default_tmp_only": vanderbilt_triage_contract_summary.get(
                "slice_outputs_default_tmp_only"
            ),
            "private_artifact_paths_committed": vanderbilt_triage_contract_summary.get(
                "private_artifact_paths_committed"
            ),
            "raw_dump_publication_allowed": vanderbilt_triage_contract_summary.get("raw_dump_publication_allowed"),
            "mutation_allowed": vanderbilt_triage_contract_summary.get("mutation_allowed"),
            "person_ingestion_allowed": vanderbilt_triage_contract_summary.get("person_ingestion_allowed"),
            "denominator_closure_allowed": vanderbilt_triage_contract_summary.get(
                "denominator_closure_allowed"
            ),
            "school_verification_allowed": vanderbilt_triage_contract_summary.get("school_verification_allowed"),
            "csv_rows": len(vanderbilt_triage_contract_csv),
            "json_rows": len(vanderbilt_triage_contract_json),
        },
        {"summary": "artifacts/data/vanderbilt_triage_slice_definition_contract_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_slice_2_execution_plan_boundary",
        vanderbilt_slice_2_execution_plan_summary.get("rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET
        and vanderbilt_slice_2_execution_plan_summary.get("plan_rows") == 9
        and vanderbilt_slice_2_execution_plan_summary.get("gap_rows_represented") == 9
        and vanderbilt_slice_2_execution_plan_summary.get("triage_order") == 2
        and vanderbilt_slice_2_execution_plan_summary.get("execution_order") == 1
        and vanderbilt_slice_2_execution_plan_summary.get("source_triage_rowset_sha256")
        == EXPECTED_VANDERBILT_OPEN_GAP_TRIAGE_ROWSET
        and vanderbilt_slice_2_execution_plan_summary.get("source_triage_contract_rowset_sha256")
        == EXPECTED_VANDERBILT_TRIAGE_CONTRACT_ROWSET
        and vanderbilt_slice_2_execution_plan_summary.get("web_fetch_allowed") is False
        and vanderbilt_slice_2_execution_plan_summary.get("private_artifact_paths_committed") is False
        and vanderbilt_slice_2_execution_plan_summary.get("raw_dump_publication_allowed") is False
        and vanderbilt_slice_2_execution_plan_summary.get("mutation_allowed") is False
        and vanderbilt_slice_2_execution_plan_summary.get("person_ingestion_allowed") is False
        and vanderbilt_slice_2_execution_plan_summary.get("denominator_closure_allowed") is False
        and vanderbilt_slice_2_execution_plan_summary.get("school_verification_allowed") is False
        and len(vanderbilt_slice_2_execution_plan_csv) == 9
        and len(vanderbilt_slice_2_execution_plan_json) == 9,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET,
            "plan_rows": 9,
            "gap_rows_represented": 9,
            "triage_order": 2,
            "execution_order": 1,
            "source_triage_rowset_sha256": EXPECTED_VANDERBILT_OPEN_GAP_TRIAGE_ROWSET,
            "source_triage_contract_rowset_sha256": EXPECTED_VANDERBILT_TRIAGE_CONTRACT_ROWSET,
            "web_fetch_allowed": False,
            "private_artifact_paths_committed": False,
            "raw_dump_publication_allowed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
            "school_verification_allowed": False,
            "csv_rows": 9,
            "json_rows": 9,
        },
        {
            "rowset_sha256": vanderbilt_slice_2_execution_plan_summary.get("rowset_sha256"),
            "plan_rows": vanderbilt_slice_2_execution_plan_summary.get("plan_rows"),
            "gap_rows_represented": vanderbilt_slice_2_execution_plan_summary.get("gap_rows_represented"),
            "triage_order": vanderbilt_slice_2_execution_plan_summary.get("triage_order"),
            "execution_order": vanderbilt_slice_2_execution_plan_summary.get("execution_order"),
            "source_triage_rowset_sha256": vanderbilt_slice_2_execution_plan_summary.get(
                "source_triage_rowset_sha256"
            ),
            "source_triage_contract_rowset_sha256": vanderbilt_slice_2_execution_plan_summary.get(
                "source_triage_contract_rowset_sha256"
            ),
            "web_fetch_allowed": vanderbilt_slice_2_execution_plan_summary.get("web_fetch_allowed"),
            "private_artifact_paths_committed": vanderbilt_slice_2_execution_plan_summary.get(
                "private_artifact_paths_committed"
            ),
            "raw_dump_publication_allowed": vanderbilt_slice_2_execution_plan_summary.get(
                "raw_dump_publication_allowed"
            ),
            "mutation_allowed": vanderbilt_slice_2_execution_plan_summary.get("mutation_allowed"),
            "person_ingestion_allowed": vanderbilt_slice_2_execution_plan_summary.get("person_ingestion_allowed"),
            "denominator_closure_allowed": vanderbilt_slice_2_execution_plan_summary.get(
                "denominator_closure_allowed"
            ),
            "school_verification_allowed": vanderbilt_slice_2_execution_plan_summary.get(
                "school_verification_allowed"
            ),
            "csv_rows": len(vanderbilt_slice_2_execution_plan_csv),
            "json_rows": len(vanderbilt_slice_2_execution_plan_json),
        },
        {"summary": "artifacts/data/vanderbilt_slice_2_execution_plan_packet_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_slice_2_live_fetch_approval_request_boundary",
        vanderbilt_slice_2_live_fetch_approval_summary.get("rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_LIVE_FETCH_APPROVAL_ROWSET
        and vanderbilt_slice_2_live_fetch_approval_summary.get("approval_request_rows") == 9
        and vanderbilt_slice_2_live_fetch_approval_summary.get("source_plan_rows") == 9
        and vanderbilt_slice_2_live_fetch_approval_summary.get("triage_order") == 2
        and vanderbilt_slice_2_live_fetch_approval_summary.get("execution_order") == 1
        and vanderbilt_slice_2_live_fetch_approval_summary.get("source_execution_plan_rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET
        and vanderbilt_slice_2_live_fetch_approval_summary.get("gbrain_approval_status")
        == "pending_exact_gbrain_approval"
        and vanderbilt_slice_2_live_fetch_approval_summary.get("web_fetch_allowed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("web_fetch_executed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("future_web_fetch_requested") is True
        and vanderbilt_slice_2_live_fetch_approval_summary.get("private_artifact_paths_committed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("raw_dump_publication_allowed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("mutation_allowed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("person_ingestion_allowed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("parser_acceptance_allowed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("denominator_closure_allowed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("school_verification_allowed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("url_rewrite_allowed") is False
        and vanderbilt_slice_2_live_fetch_approval_summary.get("identity_collapse_allowed") is False
        and len(vanderbilt_slice_2_live_fetch_approval_csv) == 9
        and len(vanderbilt_slice_2_live_fetch_approval_json) == 9,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_LIVE_FETCH_APPROVAL_ROWSET,
            "approval_request_rows": 9,
            "source_plan_rows": 9,
            "triage_order": 2,
            "execution_order": 1,
            "source_execution_plan_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET,
            "gbrain_approval_status": "pending_exact_gbrain_approval",
            "web_fetch_allowed": False,
            "web_fetch_executed": False,
            "future_web_fetch_requested": True,
            "private_artifact_paths_committed": False,
            "raw_dump_publication_allowed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "parser_acceptance_allowed": False,
            "denominator_closure_allowed": False,
            "school_verification_allowed": False,
            "url_rewrite_allowed": False,
            "identity_collapse_allowed": False,
            "csv_rows": 9,
            "json_rows": 9,
        },
        {
            "rowset_sha256": vanderbilt_slice_2_live_fetch_approval_summary.get("rowset_sha256"),
            "approval_request_rows": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "approval_request_rows"
            ),
            "source_plan_rows": vanderbilt_slice_2_live_fetch_approval_summary.get("source_plan_rows"),
            "triage_order": vanderbilt_slice_2_live_fetch_approval_summary.get("triage_order"),
            "execution_order": vanderbilt_slice_2_live_fetch_approval_summary.get("execution_order"),
            "source_execution_plan_rowset_sha256": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "source_execution_plan_rowset_sha256"
            ),
            "gbrain_approval_status": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "gbrain_approval_status"
            ),
            "web_fetch_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get("web_fetch_allowed"),
            "web_fetch_executed": vanderbilt_slice_2_live_fetch_approval_summary.get("web_fetch_executed"),
            "future_web_fetch_requested": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "future_web_fetch_requested"
            ),
            "private_artifact_paths_committed": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "private_artifact_paths_committed"
            ),
            "raw_dump_publication_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "raw_dump_publication_allowed"
            ),
            "mutation_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get("mutation_allowed"),
            "person_ingestion_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "person_ingestion_allowed"
            ),
            "parser_acceptance_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "parser_acceptance_allowed"
            ),
            "denominator_closure_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "denominator_closure_allowed"
            ),
            "school_verification_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "school_verification_allowed"
            ),
            "url_rewrite_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get("url_rewrite_allowed"),
            "identity_collapse_allowed": vanderbilt_slice_2_live_fetch_approval_summary.get(
                "identity_collapse_allowed"
            ),
            "csv_rows": len(vanderbilt_slice_2_live_fetch_approval_csv),
            "json_rows": len(vanderbilt_slice_2_live_fetch_approval_json),
        },
        {"summary": "artifacts/data/vanderbilt_slice_2_live_fetch_approval_request_packet_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_slice_2_live_route_observation_boundary",
        vanderbilt_slice_2_live_route_observation_summary.get("rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_LIVE_ROUTE_OBSERVATION_ROWSET
        and vanderbilt_slice_2_live_route_observation_summary.get("observation_rows") == 18
        and vanderbilt_slice_2_live_route_observation_summary.get("request_rows_represented") == 9
        and vanderbilt_slice_2_live_route_observation_summary.get("unique_observed_urls") == 12
        and vanderbilt_slice_2_live_route_observation_summary.get("source_approval_request_rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_LIVE_FETCH_APPROVAL_ROWSET
        and vanderbilt_slice_2_live_route_observation_summary.get("source_execution_plan_rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET
        and vanderbilt_slice_2_live_route_observation_summary.get("gbrain_approval_status")
        == "approved_exact_non_mutating_live_route_observation"
        and vanderbilt_slice_2_live_route_observation_summary.get("web_fetch_executed") is True
        and vanderbilt_slice_2_live_route_observation_summary.get("web_fetch_approved_by_gbrain") is True
        and vanderbilt_slice_2_live_route_observation_summary.get("private_artifact_paths_committed") is False
        and vanderbilt_slice_2_live_route_observation_summary.get("raw_dump_publication_allowed") is False
        and vanderbilt_slice_2_live_route_observation_summary.get("mutation_allowed") is False
        and vanderbilt_slice_2_live_route_observation_summary.get("person_ingestion_allowed") is False
        and vanderbilt_slice_2_live_route_observation_summary.get("parser_acceptance_allowed") is False
        and vanderbilt_slice_2_live_route_observation_summary.get("denominator_closure_allowed") is False
        and vanderbilt_slice_2_live_route_observation_summary.get("school_verification_allowed") is False
        and vanderbilt_slice_2_live_route_observation_summary.get("url_rewrite_allowed") is False
        and vanderbilt_slice_2_live_route_observation_summary.get("identity_collapse_allowed") is False
        and len(vanderbilt_slice_2_live_route_observation_csv) == 18
        and len(vanderbilt_slice_2_live_route_observation_json) == 18,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_LIVE_ROUTE_OBSERVATION_ROWSET,
            "observation_rows": 18,
            "request_rows_represented": 9,
            "unique_observed_urls": 12,
            "source_approval_request_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_LIVE_FETCH_APPROVAL_ROWSET,
            "source_execution_plan_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET,
            "gbrain_approval_status": "approved_exact_non_mutating_live_route_observation",
            "web_fetch_executed": True,
            "web_fetch_approved_by_gbrain": True,
            "private_artifact_paths_committed": False,
            "raw_dump_publication_allowed": False,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "parser_acceptance_allowed": False,
            "denominator_closure_allowed": False,
            "school_verification_allowed": False,
            "url_rewrite_allowed": False,
            "identity_collapse_allowed": False,
            "csv_rows": 18,
            "json_rows": 18,
        },
        {
            "rowset_sha256": vanderbilt_slice_2_live_route_observation_summary.get("rowset_sha256"),
            "observation_rows": vanderbilt_slice_2_live_route_observation_summary.get("observation_rows"),
            "request_rows_represented": vanderbilt_slice_2_live_route_observation_summary.get(
                "request_rows_represented"
            ),
            "unique_observed_urls": vanderbilt_slice_2_live_route_observation_summary.get(
                "unique_observed_urls"
            ),
            "source_approval_request_rowset_sha256": vanderbilt_slice_2_live_route_observation_summary.get(
                "source_approval_request_rowset_sha256"
            ),
            "source_execution_plan_rowset_sha256": vanderbilt_slice_2_live_route_observation_summary.get(
                "source_execution_plan_rowset_sha256"
            ),
            "gbrain_approval_status": vanderbilt_slice_2_live_route_observation_summary.get(
                "gbrain_approval_status"
            ),
            "web_fetch_executed": vanderbilt_slice_2_live_route_observation_summary.get(
                "web_fetch_executed"
            ),
            "web_fetch_approved_by_gbrain": vanderbilt_slice_2_live_route_observation_summary.get(
                "web_fetch_approved_by_gbrain"
            ),
            "private_artifact_paths_committed": vanderbilt_slice_2_live_route_observation_summary.get(
                "private_artifact_paths_committed"
            ),
            "raw_dump_publication_allowed": vanderbilt_slice_2_live_route_observation_summary.get(
                "raw_dump_publication_allowed"
            ),
            "mutation_allowed": vanderbilt_slice_2_live_route_observation_summary.get("mutation_allowed"),
            "person_ingestion_allowed": vanderbilt_slice_2_live_route_observation_summary.get(
                "person_ingestion_allowed"
            ),
            "parser_acceptance_allowed": vanderbilt_slice_2_live_route_observation_summary.get(
                "parser_acceptance_allowed"
            ),
            "denominator_closure_allowed": vanderbilt_slice_2_live_route_observation_summary.get(
                "denominator_closure_allowed"
            ),
            "school_verification_allowed": vanderbilt_slice_2_live_route_observation_summary.get(
                "school_verification_allowed"
            ),
            "url_rewrite_allowed": vanderbilt_slice_2_live_route_observation_summary.get("url_rewrite_allowed"),
            "identity_collapse_allowed": vanderbilt_slice_2_live_route_observation_summary.get(
                "identity_collapse_allowed"
            ),
            "csv_rows": len(vanderbilt_slice_2_live_route_observation_csv),
            "json_rows": len(vanderbilt_slice_2_live_route_observation_json),
        },
        {"summary": "artifacts/data/vanderbilt_slice_2_live_route_observation_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_slice_2_route_parser_scope_approval_request_boundary",
        vanderbilt_slice_2_route_parser_scope_approval_summary.get("rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_ROUTE_PARSER_SCOPE_APPROVAL_ROWSET
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("packet_rows") == 18
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("request_rows_represented") == 9
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("source_route_observation_rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_LIVE_ROUTE_OBSERVATION_ROWSET
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("source_approval_request_rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_LIVE_FETCH_APPROVAL_ROWSET
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("source_execution_plan_rowset_sha256")
        == EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("gbrain_approval_status")
        == "pending_exact_approval_line"
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("web_fetch_allowed") is False
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("mutation_allowed") is False
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("parser_implementation_allowed") is False
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("parser_acceptance_allowed") is False
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("person_ingestion_allowed") is False
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("denominator_closure_allowed") is False
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("school_verification_allowed") is False
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("url_rewrite_allowed") is False
        and vanderbilt_slice_2_route_parser_scope_approval_summary.get("identity_collapse_allowed") is False
        and len(vanderbilt_slice_2_route_parser_scope_approval_csv) == 18
        and len(vanderbilt_slice_2_route_parser_scope_approval_json) == 18,
        {
            "rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_ROUTE_PARSER_SCOPE_APPROVAL_ROWSET,
            "packet_rows": 18,
            "request_rows_represented": 9,
            "source_route_observation_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_LIVE_ROUTE_OBSERVATION_ROWSET,
            "source_approval_request_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_LIVE_FETCH_APPROVAL_ROWSET,
            "source_execution_plan_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET,
            "gbrain_approval_status": "pending_exact_approval_line",
            "web_fetch_allowed": False,
            "mutation_allowed": False,
            "parser_implementation_allowed": False,
            "parser_acceptance_allowed": False,
            "person_ingestion_allowed": False,
            "denominator_closure_allowed": False,
            "school_verification_allowed": False,
            "url_rewrite_allowed": False,
            "identity_collapse_allowed": False,
            "csv_rows": 18,
            "json_rows": 18,
        },
        {
            "rowset_sha256": vanderbilt_slice_2_route_parser_scope_approval_summary.get("rowset_sha256"),
            "packet_rows": vanderbilt_slice_2_route_parser_scope_approval_summary.get("packet_rows"),
            "request_rows_represented": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "request_rows_represented"
            ),
            "source_route_observation_rowset_sha256": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "source_route_observation_rowset_sha256"
            ),
            "source_approval_request_rowset_sha256": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "source_approval_request_rowset_sha256"
            ),
            "source_execution_plan_rowset_sha256": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "source_execution_plan_rowset_sha256"
            ),
            "gbrain_approval_status": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "gbrain_approval_status"
            ),
            "web_fetch_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "web_fetch_allowed"
            ),
            "mutation_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get("mutation_allowed"),
            "parser_implementation_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "parser_implementation_allowed"
            ),
            "parser_acceptance_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "parser_acceptance_allowed"
            ),
            "person_ingestion_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "person_ingestion_allowed"
            ),
            "denominator_closure_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "denominator_closure_allowed"
            ),
            "school_verification_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "school_verification_allowed"
            ),
            "url_rewrite_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "url_rewrite_allowed"
            ),
            "identity_collapse_allowed": vanderbilt_slice_2_route_parser_scope_approval_summary.get(
                "identity_collapse_allowed"
            ),
            "csv_rows": len(vanderbilt_slice_2_route_parser_scope_approval_csv),
            "json_rows": len(vanderbilt_slice_2_route_parser_scope_approval_json),
        },
        {"summary": "artifacts/data/vanderbilt_slice_2_route_parser_scope_approval_packet_summary.json"},
    )
    gap_review_template_blank_counts = gap_review_template_summary.get("blank_review_fields")
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_review_template_boundary",
        gap_review_template_summary.get("rowset_sha256") == EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET
        and gap_review_template_summary.get("review_template_rows") == 113
        and gap_review_template_summary.get("batch_rows_represented") == 21
        and gap_review_template_summary.get("blank_action_rows") == 113
        and isinstance(gap_review_template_blank_counts, dict)
        and all(value == 113 for value in gap_review_template_blank_counts.values())
        and gap_review_template_summary.get("valid_non_mutating_review_rows") == 0
        and gap_review_template_summary.get("private_artifact_paths_committed") is False
        and gap_review_template_summary.get("reviewer_note_column_committed") is False
        and gap_review_template_summary.get("mutation_allowed") is False
        and len(gap_review_template_csv) == 113
        and len(gap_review_template_json) == 113,
        {
            "rowset_sha256": EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET,
            "review_template_rows": 113,
            "batch_rows_represented": 21,
            "blank_action_rows": 113,
            "blank_review_fields": 113,
            "valid_non_mutating_review_rows": 0,
            "private_artifact_paths_committed": False,
            "reviewer_note_column_committed": False,
            "mutation_allowed": False,
            "csv_rows": 113,
            "json_rows": 113,
        },
        {
            "rowset_sha256": gap_review_template_summary.get("rowset_sha256"),
            "review_template_rows": gap_review_template_summary.get("review_template_rows"),
            "batch_rows_represented": gap_review_template_summary.get("batch_rows_represented"),
            "blank_action_rows": gap_review_template_summary.get("blank_action_rows"),
            "blank_review_fields": gap_review_template_blank_counts,
            "valid_non_mutating_review_rows": gap_review_template_summary.get("valid_non_mutating_review_rows"),
            "private_artifact_paths_committed": gap_review_template_summary.get("private_artifact_paths_committed"),
            "reviewer_note_column_committed": gap_review_template_summary.get("reviewer_note_column_committed"),
            "mutation_allowed": gap_review_template_summary.get("mutation_allowed"),
            "csv_rows": len(gap_review_template_csv),
            "json_rows": len(gap_review_template_json),
        },
        {"summary": "artifacts/data/school_gap_resolution_review_template_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_review_template_validation_boundary",
        gap_review_template_validation.get("rowset_sha256") == EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET
        and gap_review_template_validation.get("template_rows") == 113
        and gap_review_template_validation.get("pending_rows") == 113
        and gap_review_template_validation.get("valid_non_mutating_rows") == 0
        and gap_review_template_validation.get("invalid_rows") == 0
        and gap_review_template_validation.get("mutation_allowed") is False,
        {
            "rowset_sha256": EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET,
            "template_rows": 113,
            "pending_rows": 113,
            "valid_non_mutating_rows": 0,
            "invalid_rows": 0,
            "mutation_allowed": False,
        },
        {
            "rowset_sha256": gap_review_template_validation.get("rowset_sha256"),
            "template_rows": gap_review_template_validation.get("template_rows"),
            "pending_rows": gap_review_template_validation.get("pending_rows"),
            "valid_non_mutating_rows": gap_review_template_validation.get("valid_non_mutating_rows"),
            "invalid_rows": gap_review_template_validation.get("invalid_rows"),
            "mutation_allowed": gap_review_template_validation.get("mutation_allowed"),
        },
        {"summary": "artifacts/data/school_gap_resolution_review_template_validation_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_targeted_review_packet_boundary",
        gap_targeted_review_packet_summary.get("rowset_sha256") == EXPECTED_GAP_TARGETED_REVIEW_PACKET_ROWSET
        and gap_targeted_review_packet_summary.get("review_packet_rows") == 113
        and gap_targeted_review_packet_summary.get("filled_review_rows") == 19
        and gap_targeted_review_packet_summary.get("blank_review_rows") == 94
        and gap_targeted_review_packet_summary.get("target_gap_rows") == 19
        and gap_targeted_review_packet_summary.get("source_template_rowset_sha256") == EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET
        and gap_targeted_review_packet_summary.get("mutation_allowed") is False
        and len(gap_targeted_review_packet_csv) == 113
        and len(gap_targeted_review_packet_json) == 113,
        {
            "rowset_sha256": EXPECTED_GAP_TARGETED_REVIEW_PACKET_ROWSET,
            "review_packet_rows": 113,
            "filled_review_rows": 19,
            "blank_review_rows": 94,
            "target_gap_rows": 19,
            "source_template_rowset_sha256": EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET,
            "mutation_allowed": False,
            "csv_rows": 113,
            "json_rows": 113,
        },
        {
            "rowset_sha256": gap_targeted_review_packet_summary.get("rowset_sha256"),
            "review_packet_rows": gap_targeted_review_packet_summary.get("review_packet_rows"),
            "filled_review_rows": gap_targeted_review_packet_summary.get("filled_review_rows"),
            "blank_review_rows": gap_targeted_review_packet_summary.get("blank_review_rows"),
            "target_gap_rows": gap_targeted_review_packet_summary.get("target_gap_rows"),
            "source_template_rowset_sha256": gap_targeted_review_packet_summary.get("source_template_rowset_sha256"),
            "mutation_allowed": gap_targeted_review_packet_summary.get("mutation_allowed"),
            "csv_rows": len(gap_targeted_review_packet_csv),
            "json_rows": len(gap_targeted_review_packet_json),
        },
        {"summary": "artifacts/data/school_gap_resolution_targeted_review_packet_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_targeted_review_packet_validation_boundary",
        gap_targeted_review_packet_validation.get("rowset_sha256") == EXPECTED_GAP_TARGETED_REVIEW_PACKET_ROWSET
        and gap_targeted_review_packet_validation.get("template_rows") == 113
        and gap_targeted_review_packet_validation.get("pending_rows") == 94
        and gap_targeted_review_packet_validation.get("valid_non_mutating_rows") == 19
        and gap_targeted_review_packet_validation.get("invalid_rows") == 0
        and gap_targeted_review_packet_validation.get("mutation_allowed") is False,
        {
            "rowset_sha256": EXPECTED_GAP_TARGETED_REVIEW_PACKET_ROWSET,
            "template_rows": 113,
            "pending_rows": 94,
            "valid_non_mutating_rows": 19,
            "invalid_rows": 0,
            "mutation_allowed": False,
        },
        {
            "rowset_sha256": gap_targeted_review_packet_validation.get("rowset_sha256"),
            "template_rows": gap_targeted_review_packet_validation.get("template_rows"),
            "pending_rows": gap_targeted_review_packet_validation.get("pending_rows"),
            "valid_non_mutating_rows": gap_targeted_review_packet_validation.get("valid_non_mutating_rows"),
            "invalid_rows": gap_targeted_review_packet_validation.get("invalid_rows"),
            "mutation_allowed": gap_targeted_review_packet_validation.get("mutation_allowed"),
        },
        {"summary": "artifacts/data/school_gap_resolution_targeted_review_packet_validation_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_parser_scope_bridge_boundary",
        gap_parser_scope_bridge_summary.get("rowset_sha256") == EXPECTED_GAP_PARSER_SCOPE_BRIDGE_ROWSET
        and gap_parser_scope_bridge_summary.get("bridge_rows") == 19
        and gap_parser_scope_bridge_summary.get("targeted_review_rows_represented") == 19
        and gap_parser_scope_bridge_summary.get("parser_scope_review_rows_represented") == 20
        and gap_parser_scope_bridge_summary.get("route_packet_rows_represented") == 20
        and gap_parser_scope_bridge_summary.get("decision_packet_rows_represented") == 20
        and gap_parser_scope_bridge_summary.get("mutation_allowed") is False
        and gap_parser_scope_bridge_summary.get("parser_acceptance_allowed") is False
        and gap_parser_scope_bridge_summary.get("person_ingestion_allowed") is False
        and len(gap_parser_scope_bridge_csv) == 19
        and len(gap_parser_scope_bridge_json) == 19,
        {
            "rowset_sha256": EXPECTED_GAP_PARSER_SCOPE_BRIDGE_ROWSET,
            "bridge_rows": 19,
            "targeted_review_rows_represented": 19,
            "parser_scope_review_rows_represented": 20,
            "route_packet_rows_represented": 20,
            "decision_packet_rows_represented": 20,
            "mutation_allowed": False,
            "parser_acceptance_allowed": False,
            "person_ingestion_allowed": False,
            "csv_rows": 19,
            "json_rows": 19,
        },
        {
            "rowset_sha256": gap_parser_scope_bridge_summary.get("rowset_sha256"),
            "bridge_rows": gap_parser_scope_bridge_summary.get("bridge_rows"),
            "targeted_review_rows_represented": gap_parser_scope_bridge_summary.get(
                "targeted_review_rows_represented"
            ),
            "parser_scope_review_rows_represented": gap_parser_scope_bridge_summary.get(
                "parser_scope_review_rows_represented"
            ),
            "route_packet_rows_represented": gap_parser_scope_bridge_summary.get("route_packet_rows_represented"),
            "decision_packet_rows_represented": gap_parser_scope_bridge_summary.get(
                "decision_packet_rows_represented"
            ),
            "mutation_allowed": gap_parser_scope_bridge_summary.get("mutation_allowed"),
            "parser_acceptance_allowed": gap_parser_scope_bridge_summary.get("parser_acceptance_allowed"),
            "person_ingestion_allowed": gap_parser_scope_bridge_summary.get("person_ingestion_allowed"),
            "csv_rows": len(gap_parser_scope_bridge_csv),
            "json_rows": len(gap_parser_scope_bridge_json),
        },
        {"summary": "artifacts/data/school_gap_resolution_parser_scope_bridge_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_candidate_output_bridge_boundary",
        gap_candidate_output_bridge_summary.get("rowset_sha256") == EXPECTED_GAP_CANDIDATE_OUTPUT_BRIDGE_ROWSET
        and gap_candidate_output_bridge_summary.get("bridge_rows") == 19
        and gap_candidate_output_bridge_summary.get("implementation_approval_rows_represented") == 20
        and gap_candidate_output_bridge_summary.get("candidate_output_rows_represented") == 159
        and gap_candidate_output_bridge_summary.get("candidate_fingerprint_rows_represented") == 155
        and gap_candidate_output_bridge_summary.get("mutation_allowed") is False
        and gap_candidate_output_bridge_summary.get("parser_acceptance_allowed") is False
        and gap_candidate_output_bridge_summary.get("person_ingestion_allowed") is False
        and len(gap_candidate_output_bridge_csv) == 19
        and len(gap_candidate_output_bridge_json) == 19,
        {
            "rowset_sha256": EXPECTED_GAP_CANDIDATE_OUTPUT_BRIDGE_ROWSET,
            "bridge_rows": 19,
            "implementation_approval_rows_represented": 20,
            "candidate_output_rows_represented": 159,
            "candidate_fingerprint_rows_represented": 155,
            "mutation_allowed": False,
            "parser_acceptance_allowed": False,
            "person_ingestion_allowed": False,
            "csv_rows": 19,
            "json_rows": 19,
        },
        {
            "rowset_sha256": gap_candidate_output_bridge_summary.get("rowset_sha256"),
            "bridge_rows": gap_candidate_output_bridge_summary.get("bridge_rows"),
            "implementation_approval_rows_represented": gap_candidate_output_bridge_summary.get(
                "implementation_approval_rows_represented"
            ),
            "candidate_output_rows_represented": gap_candidate_output_bridge_summary.get(
                "candidate_output_rows_represented"
            ),
            "candidate_fingerprint_rows_represented": gap_candidate_output_bridge_summary.get(
                "candidate_fingerprint_rows_represented"
            ),
            "mutation_allowed": gap_candidate_output_bridge_summary.get("mutation_allowed"),
            "parser_acceptance_allowed": gap_candidate_output_bridge_summary.get("parser_acceptance_allowed"),
            "person_ingestion_allowed": gap_candidate_output_bridge_summary.get("person_ingestion_allowed"),
            "csv_rows": len(gap_candidate_output_bridge_csv),
            "json_rows": len(gap_candidate_output_bridge_json),
        },
        {"summary": "artifacts/data/school_gap_resolution_candidate_output_bridge_summary.json"},
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_review_queue_bridge_boundary",
        gap_review_queue_bridge_summary.get("rowset_sha256") == EXPECTED_GAP_REVIEW_QUEUE_BRIDGE_ROWSET
        and gap_review_queue_bridge_summary.get("bridge_rows") == 19
        and gap_review_queue_bridge_summary.get("candidate_output_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("queue_approval_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("review_queue_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("decision_scaffold_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("manual_decision_audit_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("pending_decision_rows_represented") == 159
        and gap_review_queue_bridge_summary.get("valid_non_mutating_decision_rows_represented") == 0
        and gap_review_queue_bridge_summary.get("invalid_decision_rows_represented") == 0
        and gap_review_queue_bridge_summary.get("mutation_allowed") is False
        and gap_review_queue_bridge_summary.get("person_ingestion_allowed") is False
        and len(gap_review_queue_bridge_csv) == 19
        and len(gap_review_queue_bridge_json) == 19,
        {
            "rowset_sha256": EXPECTED_GAP_REVIEW_QUEUE_BRIDGE_ROWSET,
            "bridge_rows": 19,
            "candidate_output_rows_represented": 159,
            "queue_approval_rows_represented": 159,
            "review_queue_rows_represented": 159,
            "decision_scaffold_rows_represented": 159,
            "manual_decision_audit_rows_represented": 159,
            "pending_decision_rows_represented": 159,
            "valid_non_mutating_decision_rows_represented": 0,
            "invalid_decision_rows_represented": 0,
            "mutation_allowed": False,
            "person_ingestion_allowed": False,
            "csv_rows": 19,
            "json_rows": 19,
        },
        {
            "rowset_sha256": gap_review_queue_bridge_summary.get("rowset_sha256"),
            "bridge_rows": gap_review_queue_bridge_summary.get("bridge_rows"),
            "candidate_output_rows_represented": gap_review_queue_bridge_summary.get(
                "candidate_output_rows_represented"
            ),
            "queue_approval_rows_represented": gap_review_queue_bridge_summary.get(
                "queue_approval_rows_represented"
            ),
            "review_queue_rows_represented": gap_review_queue_bridge_summary.get("review_queue_rows_represented"),
            "decision_scaffold_rows_represented": gap_review_queue_bridge_summary.get(
                "decision_scaffold_rows_represented"
            ),
            "manual_decision_audit_rows_represented": gap_review_queue_bridge_summary.get(
                "manual_decision_audit_rows_represented"
            ),
            "pending_decision_rows_represented": gap_review_queue_bridge_summary.get(
                "pending_decision_rows_represented"
            ),
            "valid_non_mutating_decision_rows_represented": gap_review_queue_bridge_summary.get(
                "valid_non_mutating_decision_rows_represented"
            ),
            "invalid_decision_rows_represented": gap_review_queue_bridge_summary.get(
                "invalid_decision_rows_represented"
            ),
            "mutation_allowed": gap_review_queue_bridge_summary.get("mutation_allowed"),
            "person_ingestion_allowed": gap_review_queue_bridge_summary.get("person_ingestion_allowed"),
            "csv_rows": len(gap_review_queue_bridge_csv),
            "json_rows": len(gap_review_queue_bridge_json),
        },
        {"summary": "artifacts/data/school_gap_resolution_review_queue_bridge_summary.json"},
    )
    leak_hits = batch_packet_leak_hits(
        [
            ARTIFACTS / "vanderbilt_candidate_review_batch_packets.csv",
            ARTIFACTS / "vanderbilt_candidate_review_batch_packets.json",
            ARTIFACTS / "vanderbilt_candidate_review_batch_packet_summary.json",
            RESEARCH / "vanderbilt-candidate-review-batch-packets-2026-06-09.md",
            ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.csv",
            ARTIFACTS / "vanderbilt_public_reviewer_operator_packets.json",
            ARTIFACTS / "vanderbilt_public_reviewer_operator_packet_summary.json",
            RESEARCH / "vanderbilt-public-reviewer-operator-packets-2026-06-09.md",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_template.csv",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_template.json",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_template_summary.json",
            RESEARCH / "vanderbilt-reviewer-decision-patch-template-2026-06-09.md",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.csv",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.json",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_summary.json",
            RESEARCH / "vanderbilt-reviewer-decision-patch-workbook-2026-06-09.md",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.csv",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index.json",
            ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook_slice_index_summary.json",
            RESEARCH / "vanderbilt-reviewer-decision-patch-workbook-slice-index-2026-06-09.md",
            ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge.csv",
            ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge.json",
            ARTIFACTS / "vanderbilt_reviewer_execution_readiness_bridge_summary.json",
            RESEARCH / "vanderbilt-reviewer-execution-readiness-bridge-2026-06-09.md",
            ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification.csv",
            ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification.json",
            ARTIFACTS / "vanderbilt_reviewer_blank_execution_verification_summary.json",
            RESEARCH / "vanderbilt-reviewer-blank-execution-verification-2026-06-09.md",
            ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan.csv",
            ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan.json",
            ARTIFACTS / "vanderbilt_reviewer_slice_prioritization_plan_summary.json",
            RESEARCH / "vanderbilt-reviewer-slice-prioritization-plan-2026-06-09.md",
            ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet.csv",
            ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet.json",
            ARTIFACTS / "vanderbilt_priority_reviewer_instruction_packet_summary.json",
            RESEARCH / "vanderbilt-priority-reviewer-instruction-packet-2026-06-09.md",
            ARTIFACTS / "vanderbilt_patch_helper_fixture_verification.csv",
            ARTIFACTS / "vanderbilt_patch_helper_fixture_verification.json",
            ARTIFACTS / "vanderbilt_patch_helper_fixture_verification_summary.json",
            RESEARCH / "vanderbilt-patch-helper-fixture-verification-2026-06-09.md",
            ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet.csv",
            ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet.json",
            ARTIFACTS / "vanderbilt_priority_reviewer_handoff_packet_summary.json",
            RESEARCH / "vanderbilt-priority-reviewer-handoff-packet-2026-06-09.md",
            ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo.csv",
            ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo.json",
            ARTIFACTS / "vanderbilt_synthetic_handoff_dry_run_demo_summary.json",
            RESEARCH / "vanderbilt-synthetic-handoff-dry-run-demo-2026-06-09.md",
            ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.csv",
            ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.json",
            ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet_summary.json",
            RESEARCH / "vanderbilt-open-gap-manifest-triage-packet-2026-06-09.md",
            ARTIFACTS / "vanderbilt_triage_slice_definition_contract.csv",
            ARTIFACTS / "vanderbilt_triage_slice_definition_contract.json",
            ARTIFACTS / "vanderbilt_triage_slice_definition_contract_summary.json",
            RESEARCH / "vanderbilt-triage-slice-definition-contract-2026-06-09.md",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_review_packet_public_leak_scan",
        not leak_hits,
        [],
        leak_hits,
        {"scanned_outputs": 56, "scan": "url_like_text_or_reviewer_note_text_field"},
    )
    gap_private_hits = private_marker_hits_in_paths(
        [
            ARTIFACTS / "school_gap_resolution_batch_slice_index.csv",
            ARTIFACTS / "school_gap_resolution_batch_slice_index.json",
            ARTIFACTS / "school_gap_resolution_batch_slice_index_summary.json",
            RESEARCH / "school-gap-resolution-batch-slice-index-2026-06-09.md",
            ARTIFACTS / "school_gap_resolution_review_template.csv",
            ARTIFACTS / "school_gap_resolution_review_template.json",
            ARTIFACTS / "school_gap_resolution_review_template_summary.json",
            ARTIFACTS / "school_gap_resolution_review_template_validation_summary.json",
            RESEARCH / "school-gap-resolution-review-template-2026-06-09.md",
            ARTIFACTS / "school_gap_resolution_targeted_review_packet.csv",
            ARTIFACTS / "school_gap_resolution_targeted_review_packet.json",
            ARTIFACTS / "school_gap_resolution_targeted_review_packet_summary.json",
            ARTIFACTS / "school_gap_resolution_targeted_review_packet_validation_summary.json",
            RESEARCH / "school-gap-resolution-targeted-review-packet-2026-06-09.md",
            ARTIFACTS / "school_gap_resolution_parser_scope_bridge.csv",
            ARTIFACTS / "school_gap_resolution_parser_scope_bridge.json",
            ARTIFACTS / "school_gap_resolution_parser_scope_bridge_summary.json",
            RESEARCH / "school-gap-resolution-parser-scope-bridge-2026-06-09.md",
            ARTIFACTS / "school_gap_resolution_candidate_output_bridge.csv",
            ARTIFACTS / "school_gap_resolution_candidate_output_bridge.json",
            ARTIFACTS / "school_gap_resolution_candidate_output_bridge_summary.json",
            RESEARCH / "school-gap-resolution-candidate-output-bridge-2026-06-09.md",
            ARTIFACTS / "school_gap_resolution_review_queue_bridge.csv",
            ARTIFACTS / "school_gap_resolution_review_queue_bridge.json",
            ARTIFACTS / "school_gap_resolution_review_queue_bridge_summary.json",
            RESEARCH / "school-gap-resolution-review-queue-bridge-2026-06-09.md",
            ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.csv",
            ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet.json",
            ARTIFACTS / "vanderbilt_open_gap_manifest_triage_packet_summary.json",
            RESEARCH / "vanderbilt-open-gap-manifest-triage-packet-2026-06-09.md",
            ARTIFACTS / "vanderbilt_triage_slice_definition_contract.csv",
            ARTIFACTS / "vanderbilt_triage_slice_definition_contract.json",
            ARTIFACTS / "vanderbilt_triage_slice_definition_contract_summary.json",
            RESEARCH / "vanderbilt-triage-slice-definition-contract-2026-06-09.md",
            ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet.csv",
            ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet.json",
            ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet_summary.json",
            RESEARCH / "vanderbilt-slice-2-execution-plan-packet-2026-06-09.md",
            ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet.csv",
            ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet.json",
            ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet_summary.json",
            RESEARCH / "vanderbilt-slice-2-live-fetch-approval-request-packet-2026-06-09.md",
            ARTIFACTS / "vanderbilt_slice_2_live_route_observations.csv",
            ARTIFACTS / "vanderbilt_slice_2_live_route_observations.json",
            ARTIFACTS / "vanderbilt_slice_2_live_route_observation_summary.json",
            RESEARCH / "vanderbilt-slice-2-live-route-observations-2026-06-09.md",
            ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet.csv",
            ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet.json",
            ARTIFACTS / "vanderbilt_slice_2_route_parser_scope_approval_packet_summary.json",
            RESEARCH / "vanderbilt-slice-2-route-parser-scope-approval-packet-2026-06-09.md",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_slice_index_private_marker_scan",
        not gap_private_hits,
        [],
        gap_private_hits,
        {"scanned_outputs": 50, "scan": "private_artifact_path_markers"},
    )
    private_hits = committed_private_path_hits()
    add_check(
        checks,
        generated_at,
        "private_artifact_paths_not_committed",
        not private_hits,
        [],
        private_hits,
        {"patterns": PRIVATE_PATH_PATTERNS},
    )
    ignore_presence = gitignore_patterns_present()
    add_check(
        checks,
        generated_at,
        "private_artifact_patterns_ignored",
        all(ignore_presence.values()),
        {pattern: True for pattern in PRIVATE_PATH_PATTERNS},
        ignore_presence,
        {".gitignore": ".gitignore"},
    )
    guard_present = all(
        token in gap_manifest_script_text
        for token in [
            "ALLOW_EMPTY_GAP_MANIFEST",
            "guard_nonempty_manifest",
            "Refusing to write an empty school gap-resolution manifest",
            "vanderbilt_gme_program_coverage.json",
        ]
    )
    add_check(
        checks,
        generated_at,
        "gap_manifest_empty_output_guard_present",
        guard_present and "ALLOW_EMPTY_GAP_MANIFEST=1" in readme_text,
        {"script_guard": True, "readme_override_documented": True},
        {"script_guard": guard_present, "readme_override_documented": "ALLOW_EMPTY_GAP_MANIFEST=1" in readme_text},
        {"script": "scripts/materialize_school_gap_resolution_manifest.py", "readme": "README.md"},
    )
    patch_helper_guard_present = all(
        token in reviewer_patch_script_text
        for token in [
            "--apply",
            "--scaffold",
            "--decisions",
            "valid_non_mutating",
            "audit.audit_decision",
            "person_ingestion_allowed",
            "denominator_closure_allowed",
            "accepted_person_rows",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_patch_helper_guard_present",
        patch_helper_guard_present and "apply_vanderbilt_reviewer_decision_patch.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": patch_helper_guard_present,
            "readme_documented": "apply_vanderbilt_reviewer_decision_patch.py" in readme_text,
        },
        {"script": "scripts/apply_vanderbilt_reviewer_decision_patch.py", "readme": "README.md"},
    )
    patch_extractor_guard_present = all(
        token in reviewer_patch_extractor_text
        for token in [
            "validate_workbook_header",
            "patch_helper.validate_patch_rows",
            "--scaffold",
            "--decisions",
            "No filled workbook rows to extract",
            "reviewer_note",
            "URL_RE",
            "DEFAULT_OUTPUT = Path(\"/tmp/vanderbilt_reviewer_decision_patch_extracted.csv\")",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_patch_extractor_guard_present",
        patch_extractor_guard_present and "extract_vanderbilt_reviewer_decision_patch.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": patch_extractor_guard_present,
            "readme_documented": "extract_vanderbilt_reviewer_decision_patch.py" in readme_text,
        },
        {"script": "scripts/extract_vanderbilt_reviewer_decision_patch.py", "readme": "README.md"},
    )
    slicer_guard_present = all(
        token in reviewer_workbook_slicer_text
        for token in [
            "add_mutually_exclusive_group(required=True)",
            "operator_execution_order",
            "operator_packet_key",
            "/tmp/vanderbilt_reviewer_workbook_order_",
            "extract_command",
            "patch_dry_run_command",
            "URL_RE",
            "reviewer_note",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_workbook_slicer_guard_present",
        slicer_guard_present and "slice_vanderbilt_reviewer_decision_patch_workbook.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": slicer_guard_present,
            "readme_documented": "slice_vanderbilt_reviewer_decision_patch_workbook.py" in readme_text,
        },
        {"script": "scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py", "readme": "README.md"},
    )
    execution_bridge_guard_present = all(
        token in reviewer_execution_bridge_text
        for token in [
            "REVIEW_QUEUE_BRIDGE_ROWSET",
            "SLICE_INDEX_ROWSET",
            "tmp_only",
            "patch_dry_run_commands_present",
            "apply_commands_present",
            "It does not run commands",
            "person_ingestion_allowed",
            "denominator_closure_allowed",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_execution_readiness_bridge_guard_present",
        execution_bridge_guard_present and "materialize_vanderbilt_reviewer_execution_readiness_bridge.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": execution_bridge_guard_present,
            "readme_documented": "materialize_vanderbilt_reviewer_execution_readiness_bridge.py" in readme_text,
        },
        {
            "script": "scripts/materialize_vanderbilt_reviewer_execution_readiness_bridge.py",
            "readme": "README.md",
        },
    )
    blank_execution_guard_present = all(
        token in reviewer_blank_execution_text
        for token in [
            "EXPECTED_BLANK_EXTRACT_MESSAGE",
            "No filled workbook rows to extract",
            "--allow-empty",
            "apply_executed",
            "tmp_outputs_removed",
            "shutil.rmtree",
            "person_ingestion_allowed",
            "denominator_closure_allowed",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_blank_execution_verification_guard_present",
        blank_execution_guard_present and "materialize_vanderbilt_reviewer_blank_execution_verification.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": blank_execution_guard_present,
            "readme_documented": "materialize_vanderbilt_reviewer_blank_execution_verification.py" in readme_text,
        },
        {
            "script": "scripts/materialize_vanderbilt_reviewer_blank_execution_verification.py",
            "readme": "README.md",
        },
    )
    slice_prioritization_guard_present = all(
        token in reviewer_slice_prioritization_text
        for token in [
            "SLICE_INDEX_ROWSET",
            "BLANK_EXECUTION_ROWSET",
            "DECISION_AUDIT_ROWSET",
            "assignment_group",
            "apply_executed",
            "person_ingestion_allowed",
            "denominator_closure_allowed",
            "does not fill",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_reviewer_slice_prioritization_plan_guard_present",
        slice_prioritization_guard_present
        and "materialize_vanderbilt_reviewer_slice_prioritization_plan.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": slice_prioritization_guard_present,
            "readme_documented": "materialize_vanderbilt_reviewer_slice_prioritization_plan.py" in readme_text,
        },
        {
            "script": "scripts/materialize_vanderbilt_reviewer_slice_prioritization_plan.py",
            "readme": "README.md",
        },
    )
    priority_instruction_guard_present = all(
        token in priority_instruction_text
        for token in [
            "PRIORITIZATION_ROWSET",
            "WORKBOOK_ROWSET",
            "DECISION_AUDIT_ROWSET",
            "priority_rank",
            "General Surgery",
            "does not fill reviewer decisions",
            "raw_candidate_names_committed",
            "person_ingestion_allowed",
            "denominator_closure_allowed",
            "apply_executed",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_priority_reviewer_instruction_packet_guard_present",
        priority_instruction_guard_present
        and "materialize_vanderbilt_priority_reviewer_instruction_packet.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": priority_instruction_guard_present,
            "readme_documented": "materialize_vanderbilt_priority_reviewer_instruction_packet.py" in readme_text,
        },
        {
            "script": "scripts/materialize_vanderbilt_priority_reviewer_instruction_packet.py",
            "readme": "README.md",
        },
    )
    patch_fixture_guard_present = all(
        token in patch_fixture_text
        for token in [
            "synthetic_fixture_only",
            "real_vanderbilt_rows_used",
            "validate_patch_rows",
            "extract_patch_rows",
            "validate_workbook_header",
            "apply_executed",
            "person_ingestion_allowed",
            "denominator_closure_allowed",
            "does not read or write real reviewer decisions",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_patch_helper_fixture_verification_guard_present",
        patch_fixture_guard_present and "materialize_vanderbilt_patch_helper_fixture_verification.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": patch_fixture_guard_present,
            "readme_documented": "materialize_vanderbilt_patch_helper_fixture_verification.py" in readme_text,
        },
        {
            "script": "scripts/materialize_vanderbilt_patch_helper_fixture_verification.py",
            "readme": "README.md",
        },
    )
    priority_handoff_guard_present = all(
        token in priority_handoff_text
        for token in [
            "PRIORITY_INSTRUCTION_ROWSET",
            "PATCH_HELPER_FIXTURE_ROWSET",
            "BLANK_EXECUTION_VERIFICATION_ROWSET",
            "DECISION_AUDIT_ROWSET",
            "apply_command_allowed",
            "ready_for_local_reviewer_handoff_execution",
            "does not fill reviewer decisions",
            "raw_candidate_names_committed",
            "person_ingestion_allowed",
            "denominator_closure_allowed",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_priority_reviewer_handoff_packet_guard_present",
        priority_handoff_guard_present
        and "materialize_vanderbilt_priority_reviewer_handoff_packet.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": priority_handoff_guard_present,
            "readme_documented": "materialize_vanderbilt_priority_reviewer_handoff_packet.py" in readme_text,
        },
        {
            "script": "scripts/materialize_vanderbilt_priority_reviewer_handoff_packet.py",
            "readme": "README.md",
        },
    )
    synthetic_handoff_demo_guard_present = all(
        token in synthetic_handoff_demo_text
        for token in [
            "TMP_DIR",
            "synthetic_fixture_only",
            "real_vanderbilt_rows_used",
            "slice_vanderbilt_reviewer_decision_patch_workbook.py",
            "extract_vanderbilt_reviewer_decision_patch.py",
            "apply_vanderbilt_reviewer_decision_patch.py",
            "--scaffold",
            "--decisions",
            "tmp_outputs_removed",
            "does not read or write real Vanderbilt reviewer decisions",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_synthetic_handoff_dry_run_demo_guard_present",
        synthetic_handoff_demo_guard_present
        and "materialize_vanderbilt_synthetic_handoff_dry_run_demo.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": synthetic_handoff_demo_guard_present,
            "readme_documented": "materialize_vanderbilt_synthetic_handoff_dry_run_demo.py" in readme_text,
        },
        {
            "script": "scripts/materialize_vanderbilt_synthetic_handoff_dry_run_demo.py",
            "readme": "README.md",
        },
    )
    gap_slicer_guard_present = all(
        token in gap_batch_slicer_text
        for token in [
            "add_mutually_exclusive_group(required=True)",
            "school_gap_resolution_batch_key",
            "execution_order",
            "/tmp/school_gap_resolution_batch_order_",
            "PRIVATE_PATH_MARKERS",
            "reviewer_note",
            "mutation_allowed",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_batch_slicer_guard_present",
        gap_slicer_guard_present and "slice_school_gap_resolution_batch_packets.py" in readme_text,
        {"script_guard": True, "readme_documented": True},
        {
            "script_guard": gap_slicer_guard_present,
            "readme_documented": "slice_school_gap_resolution_batch_packets.py" in readme_text,
        },
        {"script": "scripts/slice_school_gap_resolution_batch_packets.py", "readme": "README.md"},
    )
    gap_review_template_guard_present = all(
        token in (ROOT / "scripts" / "materialize_school_gap_resolution_review_template.py").read_text(encoding="utf-8")
        for token in [
            "EXPECTED_SLICE_INDEX_ROWSET",
            "ALLOWED_REVIEW_ACTIONS",
            "PRIVATE_PATH_MARKERS",
            "valid_non_mutating_review_rows",
            "person_ingestion_allowed",
            "identity_collapse_allowed",
        ]
    )
    gap_review_template_validator_guard_present = all(
        token in (ROOT / "scripts" / "validate_school_gap_resolution_review_template.py").read_text(encoding="utf-8")
        for token in [
            "ALLOWED_REVIEW_ACTIONS",
            "CONFIRMATION_FIELDS",
            "PRIVATE_PATH_MARKERS",
            "PROHIBITED_TEXT_RE",
            "proposed_output_artifact_must_be_tmp_path",
            "candidate_evidence_only",
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_gap_review_template_guard_present",
        gap_review_template_guard_present
        and gap_review_template_validator_guard_present
        and "materialize_school_gap_resolution_targeted_review_packet.py" in readme_text
        and "materialize_school_gap_resolution_parser_scope_bridge.py" in readme_text
        and "materialize_school_gap_resolution_candidate_output_bridge.py" in readme_text
        and "materialize_school_gap_resolution_review_queue_bridge.py" in readme_text
        and "materialize_school_gap_resolution_review_template.py" in readme_text
        and "validate_school_gap_resolution_review_template.py" in readme_text,
        {
            "materializer_guard": True,
            "validator_guard": True,
            "targeted_packet_readme_documented": True,
            "bridge_readme_documented": True,
            "candidate_output_bridge_readme_documented": True,
            "review_queue_bridge_readme_documented": True,
        },
        {
            "materializer_guard": gap_review_template_guard_present,
            "validator_guard": gap_review_template_validator_guard_present,
            "targeted_packet_readme_documented": "materialize_school_gap_resolution_targeted_review_packet.py"
            in readme_text,
            "bridge_readme_documented": "materialize_school_gap_resolution_parser_scope_bridge.py" in readme_text,
            "candidate_output_bridge_readme_documented": "materialize_school_gap_resolution_candidate_output_bridge.py"
            in readme_text,
            "review_queue_bridge_readme_documented": "materialize_school_gap_resolution_review_queue_bridge.py"
            in readme_text,
            "materializer_readme_documented": "materialize_school_gap_resolution_review_template.py" in readme_text,
            "validator_readme_documented": "validate_school_gap_resolution_review_template.py" in readme_text,
        },
        {
            "materializer": "scripts/materialize_school_gap_resolution_review_template.py",
            "validator": "scripts/validate_school_gap_resolution_review_template.py",
            "readme": "README.md",
        },
    )
    add_check(
        checks,
        generated_at,
        "gbrain_public_clone_verification_lane_approved",
        GBRAIN_APPROVAL_LINE == "APPROVE top50_public_clone_verification_lane_approved",
        "APPROVE top50_public_clone_verification_lane_approved",
        GBRAIN_APPROVAL_LINE,
        {
            "approval_boundary": "pure public-clone verification of committed top50/Vanderbilt safety and reproducibility invariants",
            "prohibited_mutations": [
                "person_ingestion",
                "training_state_mutation",
                "denominator_closure",
                "school_verification",
                "url_rewrite",
                "unsupported_label_ingestion",
                "unique_person_identity_collapse",
            ],
        },
    )

    pass_rows = sum(1 for row in checks if row["check_status"] == "pass")
    fail_rows = len(checks) - pass_rows
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "verification_rows": len(checks),
        "pass_rows": pass_rows,
        "fail_rows": fail_rows,
        "top50_snapshot_rowset_sha256": EXPECTED_TOP50_SNAPSHOT_ROWSET,
        "vanderbilt_batch_packet_rowset_sha256": EXPECTED_VANDERBILT_BATCH_PACKET_ROWSET,
        "vanderbilt_operator_packet_rowset_sha256": EXPECTED_VANDERBILT_OPERATOR_PACKET_ROWSET,
        "vanderbilt_patch_template_rowset_sha256": EXPECTED_VANDERBILT_PATCH_TEMPLATE_ROWSET,
        "vanderbilt_patch_workbook_rowset_sha256": EXPECTED_VANDERBILT_PATCH_WORKBOOK_ROWSET,
        "vanderbilt_workbook_slice_index_rowset_sha256": EXPECTED_VANDERBILT_WORKBOOK_SLICE_INDEX_ROWSET,
        "vanderbilt_reviewer_execution_readiness_bridge_rowset_sha256": EXPECTED_VANDERBILT_EXECUTION_READINESS_BRIDGE_ROWSET,
        "vanderbilt_reviewer_blank_execution_verification_rowset_sha256": EXPECTED_VANDERBILT_BLANK_EXECUTION_VERIFICATION_ROWSET,
        "vanderbilt_reviewer_slice_prioritization_plan_rowset_sha256": EXPECTED_VANDERBILT_SLICE_PRIORITIZATION_ROWSET,
        "vanderbilt_priority_reviewer_instruction_packet_rowset_sha256": EXPECTED_VANDERBILT_PRIORITY_INSTRUCTION_ROWSET,
        "vanderbilt_patch_helper_fixture_verification_rowset_sha256": EXPECTED_VANDERBILT_PATCH_HELPER_FIXTURE_ROWSET,
        "vanderbilt_priority_reviewer_handoff_packet_rowset_sha256": EXPECTED_VANDERBILT_PRIORITY_HANDOFF_ROWSET,
        "vanderbilt_synthetic_handoff_dry_run_demo_rowset_sha256": EXPECTED_VANDERBILT_SYNTHETIC_HANDOFF_DRY_RUN_ROWSET,
        "vanderbilt_gap_batch_slice_index_rowset_sha256": EXPECTED_GAP_BATCH_SLICE_INDEX_ROWSET,
        "vanderbilt_gap_review_template_rowset_sha256": EXPECTED_GAP_REVIEW_TEMPLATE_ROWSET,
        "vanderbilt_gap_targeted_review_packet_rowset_sha256": EXPECTED_GAP_TARGETED_REVIEW_PACKET_ROWSET,
        "vanderbilt_gap_parser_scope_bridge_rowset_sha256": EXPECTED_GAP_PARSER_SCOPE_BRIDGE_ROWSET,
        "vanderbilt_gap_candidate_output_bridge_rowset_sha256": EXPECTED_GAP_CANDIDATE_OUTPUT_BRIDGE_ROWSET,
        "vanderbilt_gap_review_queue_bridge_rowset_sha256": EXPECTED_GAP_REVIEW_QUEUE_BRIDGE_ROWSET,
        "vanderbilt_open_gap_manifest_triage_rowset_sha256": EXPECTED_VANDERBILT_OPEN_GAP_TRIAGE_ROWSET,
        "vanderbilt_triage_slice_definition_contract_rowset_sha256": EXPECTED_VANDERBILT_TRIAGE_CONTRACT_ROWSET,
        "vanderbilt_slice_2_execution_plan_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_EXECUTION_PLAN_ROWSET,
        "vanderbilt_slice_2_live_fetch_approval_request_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_LIVE_FETCH_APPROVAL_ROWSET,
        "vanderbilt_slice_2_live_route_observation_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_LIVE_ROUTE_OBSERVATION_ROWSET,
        "vanderbilt_slice_2_route_parser_scope_approval_request_rowset_sha256": EXPECTED_VANDERBILT_SLICE_2_ROUTE_PARSER_SCOPE_APPROVAL_ROWSET,
        "vanderbilt_gap_manifest_rows": gap_summary.get("rows"),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "raw_gbrain_responses_committed": False,
        "raw_browser_dumps_committed": False,
        "raw_debug_databases_committed": False,
        "gbrain_approval_status": "approved_non_mutating_public_clone_verification_lane",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(checks)

    write_csv(OUT_CSV, checks)
    write_json(OUT_JSON, checks)
    write_json(OUT_SUMMARY, summary)
    write_markdown(checks, summary)
    print(json.dumps({key: summary[key] for key in ["verification_rows", "pass_rows", "fail_rows", "rowset_sha256"]}, sort_keys=True))
    if fail_rows:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
