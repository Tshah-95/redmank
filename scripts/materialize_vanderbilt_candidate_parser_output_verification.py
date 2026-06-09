#!/usr/bin/env python3
"""Verify Vanderbilt candidate-only parser outputs without accepting people."""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SOURCE_CSV = ARTIFACTS / "vanderbilt_candidate_only_parser_outputs.csv"
SOURCE_JSON = ARTIFACTS / "vanderbilt_candidate_only_parser_outputs.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_candidate_only_parser_output_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_candidate_parser_output_verification.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_candidate_parser_output_verification.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_parser_output_verification_summary.json"
OUT_MD = RESEARCH / "vanderbilt-candidate-parser-output-verification-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba"
APPROVAL_EFFECT = "vanderbilt_candidate_parser_output_verification_registered"
DENIAL_EFFECT = "vanderbilt_candidate_parser_output_verification_denied"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt candidate parser output verification. It validates raw-name-free candidate fingerprints, "
    "scope metadata, recourse rows, source rowset boundaries, and acceptance prohibitions. It does not approve "
    "person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt "
    "school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, "
    "or unique-person identity collapse."
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

RAW_NAMEISH_RE = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")
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
            "verification_key": stable_key("vanderbilt_candidate_parser_output_verification", check_name, expected_value, observed_value),
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


def approval_line(summary: dict[str, object]) -> str:
    return (
        "APPROVE "
        + APPROVAL_EFFECT
        + " VERIFICATION_ROWS "
        + str(summary["verification_rows"])
        + " PASS_ROWS "
        + str(summary["pass_rows"])
        + " FAIL_ROWS "
        + str(summary["fail_rows"])
        + " CANDIDATE_FINGERPRINT_ROWS "
        + str(summary["candidate_fingerprint_rows"])
        + " SOURCE_ROWSET_SHA256 "
        + str(summary["source_candidate_parser_output_rowset_sha256"])
        + " ROWSET_SHA256 "
        + str(summary["rowset_sha256"])
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def verify_source_boundary() -> tuple[dict[str, object], list[dict[str, object]], list[dict[str, str]]]:
    summary = read_json(SOURCE_SUMMARY)
    json_rows = read_json(SOURCE_JSON)
    csv_rows = read_csv_rows(SOURCE_CSV)
    if not isinstance(summary, dict) or not isinstance(json_rows, list):
        raise SystemExit("Expected Vanderbilt candidate-only parser output summary and JSON rows.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "parser_output_rows": summary.get("parser_output_rows") == 159,
        "candidate_fingerprint_rows": summary.get("candidate_fingerprint_rows") == 155,
        "accepted_person_rows_zero": summary.get("accepted_person_rows") == 0,
        "raw_candidate_names_false": summary.get("raw_candidate_names_committed") is False,
        "raw_candidate_hrefs_false": summary.get("raw_candidate_hrefs_committed") is False,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
        "denominator_closure_false": summary.get("denominator_closure_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected candidate parser output boundary: {checks}")
    return summary, json_rows, csv_rows


def raw_leak_hits(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    allowed_fields = {
        "program_name",
        "fetch_url",
        "mutation_policy",
        "candidate_href_domain",
        "candidate_href_path_bucket",
        "candidate_source_kind",
        "output_kind",
        "parser_status",
        "scope_metadata_status",
        "recourse_status",
    }
    hits: list[dict[str, str]] = []
    for row in rows:
        for field, value in row.items():
            if field in allowed_fields or not value:
                continue
            if RAW_NAMEISH_RE.search(value) or URL_RE.search(value):
                hits.append(
                    {
                        "program_name": row.get("program_name", ""),
                        "field": field,
                        "value_hash": sha256_text(value),
                    }
                )
    return hits


def duplicate_fingerprint_groups(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_fingerprint: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        fingerprint = row.get("candidate_fingerprint_sha256", "")
        if fingerprint:
            by_fingerprint[fingerprint].append(row)
    duplicates = []
    for fingerprint, group in by_fingerprint.items():
        if len(group) > 1:
            duplicates.append(
                {
                    "candidate_fingerprint_sha256": fingerprint,
                    "count": len(group),
                    "programs": sorted({item.get("program_name", "") for item in group}),
                }
            )
    return sorted(duplicates, key=lambda item: (-int(item["count"]), str(item["candidate_fingerprint_sha256"])))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-line", default="", help="Exact GBrain approval line, if returned.")
    parser.add_argument("--denial-line", default="", help="Exact GBrain denial line, if returned.")
    parser.add_argument("--denial-recourse", default="", help="Concise recourse extracted from GBrain denial.")
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    summary, json_rows, csv_rows = verify_source_boundary()
    fingerprint_rows = [row for row in csv_rows if row.get("output_kind") == "candidate_fingerprint"]
    scope_rows = [row for row in csv_rows if row.get("output_kind") == "scope_metadata"]
    recourse_rows = [row for row in csv_rows if row.get("output_kind") == "route_recourse"]
    raw_hits = raw_leak_hits(csv_rows)
    duplicates = duplicate_fingerprint_groups(csv_rows)
    by_program = Counter(row.get("program_name", "") for row in fingerprint_rows)
    by_source_kind = Counter(row.get("candidate_source_kind", "") for row in fingerprint_rows)
    bad_acceptance_rows = [
        row.get("parser_output_key", "")
        for row in csv_rows
        if row.get("accepted_person_row") != "false"
        or row.get("person_ingestion_allowed") != "false"
        or row.get("denominator_closure_allowed") != "false"
    ]
    missing_hash_rows = [
        row.get("parser_output_key", "")
        for row in fingerprint_rows
        if not row.get("candidate_fingerprint_sha256")
        or not row.get("candidate_label_sha256")
        or row.get("candidate_label_char_count") in {"", "0"}
    ]
    suspicious_path_rows = [
        row.get("parser_output_key", "")
        for row in fingerprint_rows
        if row.get("candidate_source_kind") == "profile_anchor" and row.get("candidate_href_path_bucket") != "person_path"
    ]

    checks: list[dict[str, object]] = []
    add_check(
        checks,
        generated_at,
        "source_rowset_boundary_matches",
        summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        SOURCE_ROWSET_SHA256,
        summary.get("rowset_sha256"),
        {"source_summary": str(SOURCE_SUMMARY.relative_to(ROOT))},
    )
    add_check(
        checks,
        generated_at,
        "csv_json_summary_row_counts_match",
        len(csv_rows) == len(json_rows) == summary.get("parser_output_rows") == 159,
        {"csv_rows": 159, "json_rows": 159, "summary_rows": 159},
        {"csv_rows": len(csv_rows), "json_rows": len(json_rows), "summary_rows": summary.get("parser_output_rows")},
        {"source_csv": str(SOURCE_CSV.relative_to(ROOT)), "source_json": str(SOURCE_JSON.relative_to(ROOT))},
    )
    add_check(
        checks,
        generated_at,
        "output_kind_counts_match",
        len(fingerprint_rows) == 155 and len(scope_rows) == 3 and len(recourse_rows) == 1,
        {"candidate_fingerprint": 155, "scope_metadata": 3, "route_recourse": 1},
        {"candidate_fingerprint": len(fingerprint_rows), "scope_metadata": len(scope_rows), "route_recourse": len(recourse_rows)},
        {"by_output_kind": summary.get("by_output_kind", {})},
    )
    add_check(
        checks,
        generated_at,
        "raw_name_and_url_fields_absent",
        not raw_hits,
        [],
        raw_hits[:20],
        {"scan": "RAW_NAMEISH_RE and URL_RE across non-allowed CSV fields; values reported by hash only"},
    )
    add_check(
        checks,
        generated_at,
        "acceptance_flags_all_false",
        not bad_acceptance_rows,
        [],
        bad_acceptance_rows[:20],
        {"fields": ["accepted_person_row", "person_ingestion_allowed", "denominator_closure_allowed"]},
    )
    add_check(
        checks,
        generated_at,
        "fingerprint_hash_fields_present",
        not missing_hash_rows,
        [],
        missing_hash_rows[:20],
        {"fingerprint_rows": len(fingerprint_rows)},
    )
    add_check(
        checks,
        generated_at,
        "profile_anchor_paths_are_person_path",
        not suspicious_path_rows,
        [],
        suspicious_path_rows[:20],
        {"profile_anchor_rows": by_source_kind.get("profile_anchor", 0)},
    )
    add_check(
        checks,
        generated_at,
        "duplicate_candidate_fingerprints_absent",
        not duplicates,
        [],
        duplicates[:20],
        {"fingerprint_rows": len(fingerprint_rows)},
    )
    add_check(
        checks,
        generated_at,
        "scope_and_recourse_rows_have_no_candidate_fingerprints",
        all(not row.get("candidate_fingerprint_sha256") for row in scope_rows + recourse_rows),
        {"scope_or_recourse_fingerprints": 0},
        {"scope_or_recourse_fingerprints": sum(1 for row in scope_rows + recourse_rows if row.get("candidate_fingerprint_sha256"))},
        {"scope_rows": len(scope_rows), "recourse_rows": len(recourse_rows)},
    )

    checks.sort(key=lambda item: str(item["check_name"]))
    by_check_status = Counter(str(row["check_status"]) for row in checks)
    verification_summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_candidate_parser_outputs": str(SOURCE_JSON.relative_to(ROOT)),
        "source_candidate_parser_output_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_candidate_parser_output_rowset_sha256": SOURCE_ROWSET_SHA256,
        "verification_rows": len(checks),
        "pass_rows": by_check_status.get("pass", 0),
        "fail_rows": by_check_status.get("fail", 0),
        "by_check_status": dict(sorted(by_check_status.items())),
        "candidate_fingerprint_rows": len(fingerprint_rows),
        "scope_metadata_rows": len(scope_rows),
        "route_recourse_rows": len(recourse_rows),
        "raw_leak_hit_rows": len(raw_hits),
        "duplicate_fingerprint_groups": len(duplicates),
        "by_candidate_source_kind": dict(sorted(by_source_kind.items())),
        "by_program_candidate_fingerprints": dict(sorted(by_program.items())),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "accepted_person_rows": 0,
        "gbrain_registration_status": "pending_exact_approval_line",
        "gbrain_approval_effect": APPROVAL_EFFECT,
        "gbrain_denial_effect": DENIAL_EFFECT,
        "gbrain_denial_line": "",
        "gbrain_denial_recourse": "",
        "policy": MUTATION_POLICY,
    }
    verification_summary["rowset_sha256"] = rowset_sha256(checks)
    verification_summary["required_approval_line"] = approval_line(verification_summary)
    if args.approval_line == verification_summary["required_approval_line"]:
        verification_summary["gbrain_registration_status"] = "approved_exact_candidate_output_verification"
    elif DENIAL_EFFECT in args.denial_line:
        verification_summary["gbrain_registration_status"] = "denied"
        verification_summary["gbrain_denial_line"] = args.denial_line
        verification_summary["gbrain_denial_recourse"] = args.denial_recourse or "Resolve the GBrain blocker and resubmit this exact verification boundary."

    write_csv(OUT_CSV, checks)
    write_json(OUT_JSON, checks)
    write_json(OUT_SUMMARY, verification_summary)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Candidate Parser Output Verification",
        "created_at: " + generated_at,
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Candidate Parser Output Verification",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(verification_summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Required Approval Line",
        "",
        "`" + str(verification_summary["required_approval_line"]) + "`",
        "",
        "GBrain registration status: `" + str(verification_summary["gbrain_registration_status"]) + "`.",
        "",
        "## Checks",
        "",
        "| check | status | observed |",
        "| --- | --- | --- |",
    ]
    for row in checks:
        lines.append("| {check_name} | {check_status} | {observed_value} |".format(**row))
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: verification_summary[k] for k in ["verification_rows", "pass_rows", "fail_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
