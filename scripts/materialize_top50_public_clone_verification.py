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
    audit_summary = read_json(ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json")
    scaffold_summary = read_json(ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json")
    gap_summary = read_json(ARTIFACTS / "school_gap_resolution_manifest_summary.json")
    gap_csv = read_csv_rows(ARTIFACTS / "school_gap_resolution_manifest.csv")
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
            audit_summary,
            scaffold_summary,
            gap_summary,
        ]
    ):
        raise SystemExit("Expected public top-50 summary artifacts to be JSON objects.")
    if (
        not isinstance(batch_json, list)
        or not isinstance(operator_json, list)
        or not isinstance(patch_template_json, list)
        or not isinstance(patch_workbook_json, list)
        or not isinstance(slice_index_json, list)
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
        ]
    )
    add_check(
        checks,
        generated_at,
        "vanderbilt_review_packet_public_leak_scan",
        not leak_hits,
        [],
        leak_hits,
        {"scanned_outputs": 20, "scan": "url_like_text_or_reviewer_note_text_field"},
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
