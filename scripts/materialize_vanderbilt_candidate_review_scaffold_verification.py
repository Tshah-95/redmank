#!/usr/bin/env python3
"""Verify Vanderbilt candidate review decision scaffold safety."""

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

SOURCE_CSV = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.csv"
SOURCE_JSON = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json"
DECISIONS_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.csv"
DECISIONS_JSON = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.json"

OUT_CSV = ARTIFACTS / "vanderbilt_candidate_review_scaffold_verification.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_candidate_review_scaffold_verification.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_scaffold_verification_summary.json"
OUT_MD = RESEARCH / "vanderbilt-candidate-review-scaffold-verification-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt candidate review scaffold verification. It checks pending decision rows, blank manual "
    "decision templates, confirmation fields, hash boundaries, and raw-field absence. It does not approve person "
    "ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school "
    "verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-"
    "person identity collapse."
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

NAMEISH_RE = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")
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
            "verification_key": stable_key("vanderbilt_candidate_review_scaffold_verification", check_name, expected_value, observed_value),
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


def raw_leak_hits(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    allowed = {
        "program_name",
        "mutation_policy",
        "review_prompt",
        "allowed_reviewer_actions",
        "prohibited_reviewer_actions",
        "required_confirmation_fields",
        "manual_decision_file",
        "review_queue_lane",
        "queue_status",
        "decision_status",
        "candidate_source_kind",
    }
    hits: list[dict[str, str]] = []
    for row in rows:
        for field, value in row.items():
            if field in allowed or not value:
                continue
            if NAMEISH_RE.search(value) or URL_RE.search(value):
                hits.append({"field": field, "program_name": row.get("program_name", ""), "value_hash": sha256_text(value)})
    return hits


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    summary = read_json(SOURCE_SUMMARY)
    scaffold_json = read_json(SOURCE_JSON)
    decisions_json = read_json(DECISIONS_JSON)
    scaffold_rows = read_csv_rows(SOURCE_CSV)
    decision_rows = read_csv_rows(DECISIONS_CSV)
    if not isinstance(summary, dict) or not isinstance(scaffold_json, list) or not isinstance(decisions_json, list):
        raise SystemExit("Expected scaffold summary and JSON arrays.")

    raw_hits = raw_leak_hits(scaffold_rows)
    decision_nonblank_actions = [row["manual_decision_row_key"] for row in decision_rows if row.get("reviewer_action")]
    decision_nonblank_confirmations = [
        row["manual_decision_row_key"]
        for row in decision_rows
        if any(value for key, value in row.items() if key.startswith("confirm_"))
    ]
    decision_key_set = {row["manual_decision_row_key"] for row in decision_rows}
    scaffold_decision_key_set = {row["manual_decision_row_key"] for row in scaffold_rows}
    bad_flags = [
        row["decision_scaffold_key"]
        for row in scaffold_rows
        if row.get("accepted_person_row") != "false"
        or row.get("person_ingestion_allowed") != "false"
        or row.get("denominator_closure_allowed") != "false"
    ]
    by_lane = Counter(row.get("review_queue_lane", "") for row in scaffold_rows)

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
        "scaffold_and_manual_row_counts_match",
        len(scaffold_rows) == len(scaffold_json) == len(decision_rows) == len(decisions_json) == 159,
        {"scaffold_csv": 159, "scaffold_json": 159, "decision_csv": 159, "decision_json": 159},
        {
            "scaffold_csv": len(scaffold_rows),
            "scaffold_json": len(scaffold_json),
            "decision_csv": len(decision_rows),
            "decision_json": len(decisions_json),
        },
        {},
    )
    add_check(
        checks,
        generated_at,
        "review_lane_counts_match",
        by_lane == Counter({"candidate_fingerprint_review": 155, "linked_scope_metadata_review": 3, "route_recourse_review": 1}),
        {"candidate_fingerprint_review": 155, "linked_scope_metadata_review": 3, "route_recourse_review": 1},
        dict(sorted(by_lane.items())),
        {},
    )
    add_check(
        checks,
        generated_at,
        "manual_decision_templates_blank",
        not decision_nonblank_actions and not decision_nonblank_confirmations,
        {"reviewer_action": "", "confirmations": ""},
        {"nonblank_actions": decision_nonblank_actions[:20], "nonblank_confirmations": decision_nonblank_confirmations[:20]},
        {"manual_decisions_csv": str(DECISIONS_CSV.relative_to(ROOT))},
    )
    add_check(
        checks,
        generated_at,
        "manual_decision_keys_match_scaffold",
        decision_key_set == scaffold_decision_key_set,
        {"manual_decision_keys_equal": True},
        {
            "missing_in_decisions": sorted(scaffold_decision_key_set - decision_key_set)[:20],
            "extra_in_decisions": sorted(decision_key_set - scaffold_decision_key_set)[:20],
        },
        {},
    )
    add_check(
        checks,
        generated_at,
        "acceptance_flags_all_false",
        not bad_flags,
        [],
        bad_flags[:20],
        {"fields": ["accepted_person_row", "person_ingestion_allowed", "denominator_closure_allowed"]},
    )
    add_check(
        checks,
        generated_at,
        "raw_name_and_url_fields_absent",
        not raw_hits,
        [],
        raw_hits[:20],
        {"scan": "NAMEISH_RE and URL_RE over non-allowed scaffold fields; values reported by hash only"},
    )

    checks.sort(key=lambda item: str(item["check_name"]))
    by_status = Counter(str(row["check_status"]) for row in checks)
    verification_summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_decision_scaffold": str(SOURCE_JSON.relative_to(ROOT)),
        "source_decision_scaffold_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_decision_scaffold_rowset_sha256": SOURCE_ROWSET_SHA256,
        "verification_rows": len(checks),
        "pass_rows": by_status.get("pass", 0),
        "fail_rows": by_status.get("fail", 0),
        "by_check_status": dict(sorted(by_status.items())),
        "decision_scaffold_rows": len(scaffold_rows),
        "manual_decision_template_rows": len(decision_rows),
        "raw_leak_hit_rows": len(raw_hits),
        "accepted_person_rows": 0,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "policy": MUTATION_POLICY,
    }
    verification_summary["rowset_sha256"] = rowset_sha256(checks)

    write_csv(OUT_CSV, checks)
    write_json(OUT_JSON, checks)
    write_json(OUT_SUMMARY, verification_summary)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Candidate Review Scaffold Verification",
        "created_at: " + generated_at,
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Candidate Review Scaffold Verification",
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
