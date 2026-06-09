#!/usr/bin/env python3
"""Materialize approved Vanderbilt candidate-only parser diagnostics."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from materialize_vanderbilt_parser_scope_execution_evidence import fetch


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SOURCE_JSON = ARTIFACTS / "vanderbilt_parser_scope_implementation_approval_packet.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_parser_scope_implementation_approval_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_candidate_only_parser_outputs.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_candidate_only_parser_outputs.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_candidate_only_parser_output_summary.json"
OUT_MD = RESEARCH / "vanderbilt-candidate-only-parser-outputs-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "0ce935b64a7eb2153b4fb4b5a8cca47034bab839aa932c8951c29d3bda363b40"
APPROVAL_LINE = (
    "APPROVE vanderbilt_parser_scope_candidate_only_implementation_approved APPROVAL_ROWS 20 "
    "PARSER_IMPLEMENTATION_ROWS 15 SCOPE_ACCEPTANCE_ROWS 3 GENERAL_SURGERY_ROWS 1 RECOURSE_ROWS 1 "
    "ROWSET_SHA256 0ce935b64a7eb2153b4fb4b5a8cca47034bab839aa932c8951c29d3bda363b40"
)

MUTATION_POLICY = (
    "Approved Vanderbilt candidate-only parser diagnostics. This artifact may contain candidate fingerprints, "
    "counts, href hashes, route hashes, scope metadata, and recourse rows only. It contains no raw candidate names, "
    "raw person URLs, accepted person rows, person ingestion, training-state mutation, denominator closure, "
    "Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump "
    "publication, or unique-person identity collapse."
)

FIELDS = [
    "parser_output_key",
    "source_approval_packet_key",
    "program_key",
    "program_name",
    "fetch_url",
    "output_kind",
    "parser_family",
    "parser_status",
    "candidate_index",
    "candidate_fingerprint_sha256",
    "candidate_label_sha256",
    "candidate_label_token_count",
    "candidate_label_char_count",
    "candidate_source_kind",
    "candidate_href_sha256",
    "candidate_href_domain",
    "candidate_href_path_bucket",
    "content_sha256",
    "visible_text_sha256",
    "scope_metadata_status",
    "recourse_status",
    "accepted_person_row",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_approval_packet_key",
    "program_key",
    "program_name",
    "fetch_url",
    "output_kind",
    "parser_family",
    "parser_status",
    "candidate_index",
    "candidate_fingerprint_sha256",
    "candidate_label_sha256",
    "candidate_label_token_count",
    "candidate_label_char_count",
    "candidate_source_kind",
    "candidate_href_sha256",
    "candidate_href_domain",
    "candidate_href_path_bucket",
    "content_sha256",
    "visible_text_sha256",
    "scope_metadata_status",
    "recourse_status",
    "accepted_person_row",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
]

NAMEISH_RE = re.compile(r"\b[A-Z][A-Za-z'.-]+(?:\s+[A-Z][A-Za-z'.-]+){1,3}\b")
TRIM_RE = re.compile(r"\s+")

STOP_LABELS = {
    "Vanderbilt University",
    "Medical Center",
    "Popular Links",
    "Patient Care",
    "Referring Providers",
    "Employee Resources",
    "Price Transparency",
    "Give Now",
}

csv.field_size_limit(sys.maxsize)


def clean_label(value: str) -> str:
    return TRIM_RE.sub(" ", value or "").strip(" \t\r\n|-:,;")


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


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt implementation approval packet summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "approval_rows": summary.get("approval_rows") == 20,
        "approval_status": summary.get("gbrain_approval_status")
        == "approved_exact_candidate_only_implementation_scope_recourse",
        "approval_line": summary.get("required_approval_line") == APPROVAL_LINE,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
        "person_ingestion_false": summary.get("person_ingestion_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected implementation approval boundary: {checks}")
    return summary


def href_path_bucket(url: str) -> str:
    path = urlparse(url).path.lower()
    if "/person/" in path:
        return "person_path"
    if "/people/" in path:
        return "people_path"
    if "/faculty/" in path:
        return "faculty_path"
    if "current" in path or "pgy" in path:
        return "current_or_pgy_path"
    return "other_path"


def parser_family(row: dict[str, object]) -> str:
    evidence = json.loads(str(row.get("evidence_json") or "{}"))
    return str(evidence.get("parser_spec_family") or row.get("approval_request_lane") or "")


def is_candidate_label(label: str) -> bool:
    cleaned = clean_label(label)
    if not cleaned or cleaned in STOP_LABELS:
        return False
    if len(cleaned) < 5 or len(cleaned) > 90:
        return False
    if not NAMEISH_RE.search(cleaned):
        return False
    lowered = cleaned.lower()
    blocked = ["current fellows", "current residents", "vanderbilt", "division directory", "fellowship alumni"]
    return not any(token in lowered for token in blocked)


def extract_candidates(fetch_result: dict[str, object]) -> list[dict[str, str]]:
    candidates: dict[str, dict[str, str]] = {}
    for anchor in fetch_result.get("anchors", []) or []:
        label = clean_label(str(anchor.get("text") or ""))
        href = str(anchor.get("href") or "")
        if "/person/" not in urlparse(href).path.lower() or not is_candidate_label(label):
            continue
        key = sha256_text("anchor|" + label.lower() + "|" + href)
        candidates[key] = {"label": label, "href": href, "source_kind": "profile_anchor"}

    for heading in fetch_result.get("headings", []) or []:
        label = clean_label(str(heading))
        if not is_candidate_label(label):
            continue
        key = sha256_text("heading|" + label.lower())
        candidates.setdefault(key, {"label": label, "href": "", "source_kind": "heading_signal"})

    return sorted(candidates.values(), key=lambda item: (item["source_kind"], sha256_text(item["label"].lower() + item["href"])))


def base_row(source: dict[str, object], fetch_result: dict[str, object], generated_at: str) -> dict[str, object]:
    return {
        "source_approval_packet_key": source.get("approval_packet_key"),
        "program_key": source.get("program_key"),
        "program_name": source.get("program_name"),
        "fetch_url": source.get("fetch_url"),
        "parser_family": parser_family(source),
        "content_sha256": fetch_result.get("content_sha256", ""),
        "visible_text_sha256": fetch_result.get("visible_text_sha256", ""),
        "accepted_person_row": "false",
        "person_ingestion_allowed": "false",
        "denominator_closure_allowed": "false",
        "mutation_policy": MUTATION_POLICY,
        "generated_at": generated_at,
    }


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("parser_output_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Candidate Only Parser Outputs",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Candidate Only Parser Outputs",
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
        "## Output Rows",
        "",
        "| program | kind | parser status | candidate index | source kind | accepted person |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows[:200]:
        lines.append(
            "| {program_name} | {output_kind} | {parser_status} | {candidate_index} | {candidate_source_kind} | {accepted_person_row} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected Vanderbilt implementation approval packet JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    fetch_cache: dict[str, dict[str, object]] = {}
    rows: list[dict[str, object]] = []
    for url in sorted({str(row.get("fetch_url") or "") for row in source_rows if row.get("fetch_url")}):
        fetch_cache[url] = fetch(url)

    for source in source_rows:
        request_lane = str(source.get("approval_request_lane") or "")
        url = str(source.get("fetch_url") or "")
        fetch_result = fetch_cache.get(url, {"fetch_status": "not_fetched"})
        common = base_row(source, fetch_result, generated_at)
        if request_lane in {
            "candidate_only_parser_implementation_review",
            "general_surgery_candidate_only_parser_review",
        }:
            candidates = extract_candidates(fetch_result)
            if not candidates:
                output = {
                    **common,
                    "parser_output_key": stable_key("vanderbilt_candidate_only_parser_output", source.get("approval_packet_key"), "no_candidates"),
                    "output_kind": "candidate_parser_diagnostic",
                    "parser_status": "candidate_only_parser_ran_no_candidate_fingerprints",
                    "candidate_index": 0,
                    "candidate_fingerprint_sha256": "",
                    "candidate_label_sha256": "",
                    "candidate_label_token_count": 0,
                    "candidate_label_char_count": 0,
                    "candidate_source_kind": "none",
                    "candidate_href_sha256": "",
                    "candidate_href_domain": "",
                    "candidate_href_path_bucket": "",
                    "scope_metadata_status": "",
                    "recourse_status": "",
                    "evidence_json": dumps(
                        {
                            "source_approval_rowset_sha256": SOURCE_ROWSET_SHA256,
                            "fetch_status": fetch_result.get("fetch_status"),
                            "http_status": fetch_result.get("http_status"),
                        }
                    ),
                }
                rows.append(output)
                continue
            for index, candidate in enumerate(candidates, start=1):
                label = candidate["label"]
                href = candidate["href"]
                label_sha = sha256_text(label.lower())
                href_sha = sha256_text(href) if href else ""
                output = {
                    **common,
                    "parser_output_key": stable_key(
                        "vanderbilt_candidate_only_parser_output",
                        source.get("approval_packet_key"),
                        index,
                        label_sha,
                        href_sha,
                    ),
                    "output_kind": "candidate_fingerprint",
                    "parser_status": "candidate_only_parser_emitted_fingerprint",
                    "candidate_index": index,
                    "candidate_fingerprint_sha256": sha256_text(str(source.get("program_key")) + "|" + str(source.get("fetch_url")) + "|" + label.lower()),
                    "candidate_label_sha256": label_sha,
                    "candidate_label_token_count": len(label.split()),
                    "candidate_label_char_count": len(label),
                    "candidate_source_kind": candidate["source_kind"],
                    "candidate_href_sha256": href_sha,
                    "candidate_href_domain": urlparse(href).netloc.lower() if href else "",
                    "candidate_href_path_bucket": href_path_bucket(href) if href else "",
                    "scope_metadata_status": "",
                    "recourse_status": "",
                    "evidence_json": dumps(
                        {
                            "source_approval_rowset_sha256": SOURCE_ROWSET_SHA256,
                            "fetch_status": fetch_result.get("fetch_status"),
                            "http_status": fetch_result.get("http_status"),
                            "raw_candidate_label_committed": False,
                            "raw_candidate_href_committed": False,
                        }
                    ),
                }
                rows.append(output)
        elif request_lane == "linked_route_scope_disposition_acceptance":
            output = {
                **common,
                "parser_output_key": stable_key("vanderbilt_candidate_only_parser_output", source.get("approval_packet_key"), "scope"),
                "output_kind": "scope_metadata",
                "parser_status": "scope_metadata_recorded_no_parser_output",
                "candidate_index": 0,
                "candidate_fingerprint_sha256": "",
                "candidate_label_sha256": "",
                "candidate_label_token_count": 0,
                "candidate_label_char_count": 0,
                "candidate_source_kind": "none",
                "candidate_href_sha256": "",
                "candidate_href_domain": "",
                "candidate_href_path_bucket": "",
                "scope_metadata_status": "accepted_non_mutating_scope_routing_metadata",
                "recourse_status": "",
                "evidence_json": dumps(
                    {
                        "source_approval_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "approval_scope_requested": source.get("approval_scope_requested"),
                        "raw_names_committed": False,
                    }
                ),
            }
            rows.append(output)
        else:
            output = {
                **common,
                "parser_output_key": stable_key("vanderbilt_candidate_only_parser_output", source.get("approval_packet_key"), "recourse"),
                "output_kind": "route_recourse",
                "parser_status": "recourse_recorded_no_parser_output",
                "candidate_index": 0,
                "candidate_fingerprint_sha256": "",
                "candidate_label_sha256": "",
                "candidate_label_token_count": 0,
                "candidate_label_char_count": 0,
                "candidate_source_kind": "none",
                "candidate_href_sha256": "",
                "candidate_href_domain": "",
                "candidate_href_path_bucket": "",
                "scope_metadata_status": "",
                "recourse_status": "orthopaedic_route_recourse_or_replacement_queue_recorded",
                "evidence_json": dumps(
                    {
                        "source_approval_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "fetch_status": fetch_result.get("fetch_status"),
                        "http_status": fetch_result.get("http_status"),
                        "raw_names_committed": False,
                    }
                ),
            }
            rows.append(output)

    rows.sort(key=lambda item: (str(item["program_name"]), str(item["output_kind"]), int(item["candidate_index"] or 0)))
    by_kind = Counter(str(row["output_kind"]) for row in rows)
    by_status = Counter(str(row["parser_status"]) for row in rows)
    by_program = Counter(str(row["program_name"]) for row in rows)
    by_source_kind = Counter(str(row["candidate_source_kind"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_implementation_approval_packet": str(SOURCE_JSON.relative_to(ROOT)),
        "source_implementation_approval_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_implementation_approval_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_approval_rows": source_summary.get("approval_rows"),
        "parser_output_rows": len(rows),
        "candidate_fingerprint_rows": by_kind.get("candidate_fingerprint", 0),
        "unique_fetch_urls": len(fetch_cache),
        "by_output_kind": dict(sorted(by_kind.items())),
        "by_parser_status": dict(sorted(by_status.items())),
        "by_candidate_source_kind": dict(sorted(by_source_kind.items())),
        "by_program_output_rows": dict(sorted(by_program.items())),
        "mutation_allowed": False,
        "accepted_person_rows": 0,
        "raw_candidate_names_committed": False,
        "raw_candidate_hrefs_committed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["parser_output_rows", "candidate_fingerprint_rows", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
