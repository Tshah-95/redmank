#!/usr/bin/env python3
"""Audit Vanderbilt candidate reviewer decisions without mutating roster state."""

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

SCAFFOLD_JSON = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold.json"
SCAFFOLD_SUMMARY = ARTIFACTS / "vanderbilt_candidate_review_decision_scaffold_summary.json"
DECISIONS_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.csv"
DECISIONS_JSON = ARTIFACTS / "vanderbilt_candidate_reviewer_decisions.json"

OUT_CSV = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_reviewer_decision_audit_summary.json"
OUT_MD = RESEARCH / "vanderbilt-candidate-reviewer-decision-audit-2026-06-09.md"

SCAFFOLD_ROWSET_SHA256 = "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt candidate reviewer decision audit. It checks manual reviewer decisions against the "
    "verified scaffold, confirmation fields, allowed action lists, and acceptance prohibitions. It does not approve "
    "person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt "
    "school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or "
    "unique-person identity collapse."
)

FIELDS = [
    "audit_key",
    "manual_decision_row_key",
    "decision_scaffold_key",
    "review_batch_key",
    "review_queue_lane",
    "program_key",
    "program_name",
    "audit_status",
    "decision_state",
    "reviewer_action",
    "allowed_action_match",
    "decision_fingerprint_match",
    "required_confirmations_present",
    "accepted_person_row",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "audit_blocker",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "manual_decision_row_key",
    "decision_scaffold_key",
    "review_batch_key",
    "review_queue_lane",
    "program_key",
    "program_name",
    "audit_status",
    "decision_state",
    "reviewer_action",
    "allowed_action_match",
    "decision_fingerprint_match",
    "required_confirmations_present",
    "accepted_person_row",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "audit_blocker",
]

NAME_LIKE_RE = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")
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


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SCAFFOLD_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt candidate review decision scaffold summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SCAFFOLD_ROWSET_SHA256,
        "decision_scaffold_rows": summary.get("decision_scaffold_rows") == 159,
        "manual_decision_template_rows": summary.get("manual_decision_template_rows") == 159,
        "accepted_person_rows_zero": summary.get("accepted_person_rows") == 0,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
        "denominator_closure_false": summary.get("denominator_closure_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected reviewer decision scaffold boundary: {checks}")
    return summary


def allowed_actions(scaffold_row: dict[str, object]) -> set[str]:
    return {item.strip() for item in str(scaffold_row.get("allowed_reviewer_actions") or "").split(";") if item.strip()}


def required_confirmation_fields(scaffold_row: dict[str, object]) -> list[str]:
    return [
        item.strip()
        for item in str(scaffold_row.get("required_confirmation_fields") or "").split(";")
        if item.strip()
    ]


def confirmation_keys(decision_row: dict[str, str]) -> list[str]:
    return [key for key in decision_row if key.startswith("confirm_")]


def audit_decision(scaffold_row: dict[str, object], decision_row: dict[str, str], generated_at: str) -> dict[str, object]:
    action = str(decision_row.get("reviewer_action") or "").strip()
    note = str(decision_row.get("reviewer_note") or "").strip()
    allowed = allowed_actions(scaffold_row)
    required_confirmations = required_confirmation_fields(scaffold_row)
    missing_confirmation_fields = [key for key in required_confirmations if key not in decision_row]
    fingerprint_match = decision_row.get("confirm_decision_fingerprint") == scaffold_row.get("decision_fingerprint")
    confirmations = required_confirmations or confirmation_keys(decision_row)
    boolean_confirmations = [key for key in confirmations if key != "confirm_decision_fingerprint"]
    confirmations_present = all(str(decision_row.get(key) or "").lower() == "true" for key in boolean_confirmations)
    raw_note_hit = bool(NAME_LIKE_RE.search(note) or URL_RE.search(note))

    if not action and not note and not any(decision_row.get(key) for key in confirmations):
        state = "pending_blank_decision"
        status = "pending"
        blocker = ""
        allowed_match = ""
        fingerprint_value = ""
        confirmations_value = ""
    elif action not in allowed:
        state = "invalid_manual_decision"
        status = "invalid"
        blocker = "reviewer_action_not_allowed"
        allowed_match = "false"
        fingerprint_value = "true" if fingerprint_match else "false"
        confirmations_value = "true" if confirmations_present else "false"
    elif not fingerprint_match:
        state = "invalid_manual_decision"
        status = "invalid"
        blocker = "decision_fingerprint_confirmation_missing_or_mismatched"
        allowed_match = "true"
        fingerprint_value = "false"
        confirmations_value = "true" if confirmations_present else "false"
    elif missing_confirmation_fields:
        state = "invalid_manual_decision"
        status = "invalid"
        blocker = "required_confirmation_fields_absent_from_manual_template"
        allowed_match = "true"
        fingerprint_value = "true"
        confirmations_value = "false"
    elif not confirmations_present:
        state = "invalid_manual_decision"
        status = "invalid"
        blocker = "required_confirmation_fields_missing"
        allowed_match = "true"
        fingerprint_value = "true"
        confirmations_value = "false"
    elif raw_note_hit:
        state = "invalid_manual_decision"
        status = "invalid"
        blocker = "reviewer_note_contains_raw_name_or_url_like_text"
        allowed_match = "true"
        fingerprint_value = "true"
        confirmations_value = "true"
    else:
        state = "valid_non_mutating_manual_decision"
        status = "valid_non_mutating"
        blocker = ""
        allowed_match = "true"
        fingerprint_value = "true"
        confirmations_value = "true"

    return {
        "audit_key": stable_key("vanderbilt_candidate_reviewer_decision_audit", decision_row.get("manual_decision_row_key"), state, blocker),
        "manual_decision_row_key": decision_row.get("manual_decision_row_key"),
        "decision_scaffold_key": scaffold_row.get("decision_scaffold_key"),
        "review_batch_key": scaffold_row.get("review_batch_key"),
        "review_queue_lane": scaffold_row.get("review_queue_lane"),
        "program_key": scaffold_row.get("program_key"),
        "program_name": scaffold_row.get("program_name"),
        "audit_status": status,
        "decision_state": state,
        "reviewer_action": action,
        "allowed_action_match": allowed_match,
        "decision_fingerprint_match": fingerprint_value,
        "required_confirmations_present": confirmations_value,
        "accepted_person_row": "false",
        "person_ingestion_allowed": "false",
        "denominator_closure_allowed": "false",
        "audit_blocker": blocker,
        "evidence_json": dumps(
            {
                "source_scaffold_rowset_sha256": SCAFFOLD_ROWSET_SHA256,
                "allowed_actions": sorted(allowed),
                "required_confirmation_fields": required_confirmations,
                "missing_confirmation_fields": missing_confirmation_fields,
                "note_hash": sha256_text(note) if note else "",
                "raw_note_hit": raw_note_hit,
            }
        ),
        "mutation_policy": MUTATION_POLICY,
        "generated_at": generated_at,
    }


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("audit_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Candidate Reviewer Decision Audit",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Candidate Reviewer Decision Audit",
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
        "## Audit Rows",
        "",
        "| program | lane | status | state | blocker |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows[:200]:
        lines.append(
            "| {program_name} | {review_queue_lane} | {audit_status} | {decision_state} | {audit_blocker} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    scaffold_rows_raw = read_json(SCAFFOLD_JSON)
    decisions_json = read_json(DECISIONS_JSON)
    decision_rows = read_csv_rows(DECISIONS_CSV)
    if not isinstance(scaffold_rows_raw, list) or not isinstance(decisions_json, list):
        raise SystemExit("Expected scaffold and decision JSON arrays.")
    scaffold_by_manual_key = {str(row.get("manual_decision_row_key")): row for row in scaffold_rows_raw}
    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []

    for decision_row in decision_rows:
        manual_key = decision_row.get("manual_decision_row_key", "")
        scaffold_row = scaffold_by_manual_key.get(manual_key)
        if not scaffold_row:
            rows.append(
                {
                    "audit_key": stable_key("vanderbilt_candidate_reviewer_decision_audit", manual_key, "missing_scaffold"),
                    "manual_decision_row_key": manual_key,
                    "decision_scaffold_key": decision_row.get("decision_scaffold_key"),
                    "review_batch_key": decision_row.get("review_batch_key"),
                    "review_queue_lane": decision_row.get("review_queue_lane"),
                    "program_key": decision_row.get("program_key"),
                    "program_name": decision_row.get("program_name"),
                    "audit_status": "invalid",
                    "decision_state": "invalid_manual_decision",
                    "reviewer_action": decision_row.get("reviewer_action", ""),
                    "allowed_action_match": "false",
                    "decision_fingerprint_match": "false",
                    "required_confirmations_present": "false",
                    "accepted_person_row": "false",
                    "person_ingestion_allowed": "false",
                    "denominator_closure_allowed": "false",
                    "audit_blocker": "manual_decision_row_missing_scaffold",
                    "evidence_json": dumps({"source_scaffold_rowset_sha256": SCAFFOLD_ROWSET_SHA256}),
                    "mutation_policy": MUTATION_POLICY,
                    "generated_at": generated_at,
                }
            )
            continue
        rows.append(audit_decision(scaffold_row, decision_row, generated_at))

    rows.sort(key=lambda item: (str(item["audit_status"]), str(item["program_name"]), str(item["manual_decision_row_key"])))
    by_status = Counter(str(row["audit_status"]) for row in rows)
    by_state = Counter(str(row["decision_state"]) for row in rows)
    by_lane = Counter(str(row["review_queue_lane"]) for row in rows)
    by_blocker = Counter(str(row["audit_blocker"]) for row in rows if row.get("audit_blocker"))
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_decision_scaffold": str(SCAFFOLD_JSON.relative_to(ROOT)),
        "source_decision_scaffold_summary": str(SCAFFOLD_SUMMARY.relative_to(ROOT)),
        "source_decision_scaffold_rowset_sha256": SCAFFOLD_ROWSET_SHA256,
        "manual_decisions_csv": str(DECISIONS_CSV.relative_to(ROOT)),
        "manual_decisions_json": str(DECISIONS_JSON.relative_to(ROOT)),
        "source_decision_scaffold_rows": source_summary.get("decision_scaffold_rows"),
        "manual_decision_rows": len(decision_rows),
        "audit_rows": len(rows),
        "pending_rows": by_status.get("pending", 0),
        "valid_non_mutating_rows": by_status.get("valid_non_mutating", 0),
        "invalid_rows": by_status.get("invalid", 0),
        "by_audit_status": dict(sorted(by_status.items())),
        "by_decision_state": dict(sorted(by_state.items())),
        "by_review_queue_lane": dict(sorted(by_lane.items())),
        "by_audit_blocker": dict(sorted(by_blocker.items())),
        "accepted_person_rows": 0,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "mutation_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["audit_rows", "pending_rows", "invalid_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
