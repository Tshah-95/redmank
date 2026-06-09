#!/usr/bin/env python3
"""Materialize a no-fetch approval request for Vanderbilt slice-2 live route probing."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SOURCE_CSV = ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet.csv"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_execution_plan_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet_summary.json"
OUT_MD = RESEARCH / "vanderbilt-slice-2-live-fetch-approval-request-packet-2026-06-09.md"

GBRAIN_ARTIFACT_LABEL = "vanderbilt-slice2-live-fetch-approval-request-packet"
GBRAIN_ADVISORY_EFFECT = "gbrain_selected_vanderbilt_slice_2_live_fetch_approval_request_packet_option_a"
EXPECTED_SOURCE_ROWSET = "c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b"
EXPECTED_SOURCE_ROWS = 9

MUTATION_POLICY = (
    "Non-mutating Vanderbilt slice-2 live-fetch approval request. It asks whether a later bounded route-probing "
    "run may fetch current public official pages for the nine committed slice-2 execution-plan rows. This packet "
    "does not fetch web pages, run probes, store raw dumps, fill reviewer decisions, apply patches, approve parser "
    "output, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept unsupported "
    "labels, accept enrichment/profile/contact/research facts, or collapse identities."
)

PROHIBITED_MUTATIONS = [
    "person_ingestion",
    "parser_output_as_accepted_people",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "enrichment_acceptance",
    "profile_fact_acceptance",
    "contact_fact_acceptance",
    "research_fact_acceptance",
    "raw_dump_publication",
    "unique_person_identity_collapse",
]

APPROVAL_REQUIRED_FOR = [
    "live_web_fetch_or_probe",
    "route_observation_commit",
    "parser_acceptance",
    "person_ingestion",
    "denominator_closure",
    "vanderbilt_school_verification",
    "source_url_rewrite",
    "scope_closure",
    "identity_collapse",
]

FIELDS = [
    "approval_request_key",
    "request_order",
    "gbrain_artifact_label",
    "approval_request_status",
    "source_execution_plan_key",
    "source_plan_order",
    "triage_order",
    "execution_order",
    "school_gap_resolution_batch_key",
    "gap_key",
    "program_key",
    "program_name",
    "program_type",
    "plan_lane",
    "candidate_context_status",
    "denominator_domain",
    "candidate_context_domain",
    "denominator_url",
    "candidate_context_url",
    "source_discovery_query",
    "proposed_future_probe_scope",
    "permitted_if_exactly_approved",
    "future_probe_output_artifact",
    "future_probe_verification_command",
    "required_next_evidence_after_probe",
    "web_fetch_executed",
    "web_fetch_allowed_under_this_packet",
    "future_web_fetch_requested",
    "raw_dump_publication_allowed",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "parser_acceptance_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "approval_required_for",
    "prohibited_mutations",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"approval_request_key", "evidence_json", "mutation_policy", "generated_at"}
]

PRIVATE_PATH_MARKERS = [
    "artifacts/data/gbrain_",
    "artifacts/data/browser_page_dumps/",
    "artifacts/data/debug_",
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


def semicolon(values: list[str]) -> str:
    return "; ".join(values)


def domain(url: str) -> str:
    return urlparse(url or "").netloc.lower()


def int_value(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("approval_request_key", "")))
    ]
    return sha256_text(dumps(material))


def safe_program_slug(program_name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in program_name.lower()).strip("_")[:64]


def verify_source_boundary() -> tuple[dict[str, object], list[dict[str, str]]]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt slice-2 execution-plan summary to be a JSON object.")
    checks = {
        "source_rowset": summary.get("rowset_sha256") == EXPECTED_SOURCE_ROWSET,
        "source_rows": summary.get("plan_rows") == EXPECTED_SOURCE_ROWS,
        "triage_order": summary.get("triage_order") == 2,
        "execution_order": summary.get("execution_order") == 1,
        "web_fetch_allowed": summary.get("web_fetch_allowed") is False,
        "mutation_allowed": summary.get("mutation_allowed") is False,
        "person_ingestion_allowed": summary.get("person_ingestion_allowed") is False,
        "denominator_closure_allowed": summary.get("denominator_closure_allowed") is False,
        "school_verification_allowed": summary.get("school_verification_allowed") is False,
    }
    rows = read_csv_rows(SOURCE_CSV)
    if len(rows) != EXPECTED_SOURCE_ROWS:
        checks["csv_rows"] = False
    if not all(checks.values()):
        raise SystemExit("Unexpected Vanderbilt slice-2 live-fetch approval source boundary: " + dumps(checks))
    return summary, rows


def proposed_probe_scope(row: dict[str, str]) -> str:
    if row.get("plan_lane") == "related_scope_exclusion_then_target_program_source_discovery":
        return (
            "Fetch only current public official target-program pages or official search-result candidate routes; "
            "record route status, final URL, page hash, title/heading roster signals, and coarse roster-presence "
            "booleans. Treat committed context URL as exclusion/context evidence, not person truth."
        )
    return (
        "Fetch only current public official pages reachable from the denominator/context anchors or official search "
        "queries; record route status, final URL, page hash, title/heading roster signals, and coarse roster-presence "
        "booleans."
    )


def future_output_path(row: dict[str, str]) -> str:
    slug = safe_program_slug(row.get("program_name", "program"))
    return f"/tmp/vanderbilt_slice_2_live_probe_{slug}_observations.csv"


def build_rows(generated_at: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    source_summary, source_rows = verify_source_boundary()
    rows: list[dict[str, object]] = []
    for row in sorted(source_rows, key=lambda item: int_value(item.get("plan_order"))):
        rows.append(
            {
                "approval_request_key": stable_key(
                    "vanderbilt_slice_2_live_fetch_approval_request",
                    row.get("execution_plan_key"),
                    EXPECTED_SOURCE_ROWSET,
                    GBRAIN_ADVISORY_EFFECT,
                ),
                "request_order": int_value(row.get("plan_order")),
                "gbrain_artifact_label": GBRAIN_ARTIFACT_LABEL,
                "approval_request_status": "pending_exact_gbrain_approval",
                "source_execution_plan_key": row.get("execution_plan_key", ""),
                "source_plan_order": int_value(row.get("plan_order")),
                "triage_order": int_value(row.get("triage_order")),
                "execution_order": int_value(row.get("execution_order")),
                "school_gap_resolution_batch_key": row.get("school_gap_resolution_batch_key", ""),
                "gap_key": row.get("gap_key", ""),
                "program_key": row.get("program_key", ""),
                "program_name": row.get("program_name", ""),
                "program_type": row.get("program_type", ""),
                "plan_lane": row.get("plan_lane", ""),
                "candidate_context_status": row.get("candidate_context_status", ""),
                "denominator_domain": domain(row.get("denominator_url", "")),
                "candidate_context_domain": domain(row.get("candidate_context_url", "")),
                "denominator_url": row.get("denominator_url", ""),
                "candidate_context_url": row.get("candidate_context_url", ""),
                "source_discovery_query": row.get("source_discovery_query", ""),
                "proposed_future_probe_scope": proposed_probe_scope(row),
                "permitted_if_exactly_approved": (
                    "future_route_probe_metadata_hashes_only_no_raw_dumps_no_person_acceptance_no_closure"
                ),
                "future_probe_output_artifact": future_output_path(row),
                "future_probe_verification_command": (
                    "python3 scripts/materialize_vanderbilt_slice_2_live_fetch_approval_request_packet.py"
                ),
                "required_next_evidence_after_probe": (
                    "A separate non-mutating route-observation packet with fetch status, final URL, content hash, "
                    "title/heading roster signals, no raw HTML, no raw candidate names, and no accepted people."
                ),
                "web_fetch_executed": "false",
                "web_fetch_allowed_under_this_packet": "false",
                "future_web_fetch_requested": "true",
                "raw_dump_publication_allowed": "false",
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "parser_acceptance_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "approval_required_for": semicolon(APPROVAL_REQUIRED_FOR),
                "prohibited_mutations": semicolon(PROHIBITED_MUTATIONS),
                "evidence_json": dumps(
                    {
                        "gbrain_advisory_effect": GBRAIN_ADVISORY_EFFECT,
                        "source_execution_plan_rowset_sha256": EXPECTED_SOURCE_ROWSET,
                        "source_execution_plan_key": row.get("execution_plan_key"),
                        "source_execution_plan_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
                        "source_web_fetch_allowed": source_summary.get("web_fetch_allowed"),
                        "approval_request_only": True,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )
    return rows, source_summary


def private_marker_hits(rows: list[dict[str, object]]) -> list[str]:
    text = dumps(rows)
    return [marker for marker in PRIVATE_PATH_MARKERS if marker in text]


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Slice 2 Live Fetch Approval Request Packet",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Vanderbilt Slice 2 Live Fetch Approval Request Packet",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Exact Approval Line",
        "",
        "`" + str(summary["gbrain_exact_approval_line"]) + "`",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Request Rows",
        "",
        "| order | program | lane | request status | future fetch requested | fetched now |",
        "| ---: | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {request_order} | {program_name} | {plan_lane} | {approval_request_status} | {future_web_fetch_requested} | {web_fetch_executed} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows, source_summary = build_rows(generated_at)
    hits = private_marker_hits(rows)
    if hits:
        raise SystemExit(
            "Vanderbilt slice-2 live-fetch approval request contains private artifact markers: " + ", ".join(hits)
        )
    by_lane = Counter(str(row["plan_lane"]) for row in rows)
    by_context = Counter(str(row["candidate_context_status"]) for row in rows)
    rowset = rowset_sha256(rows)
    exact_approval_line = (
        "APPROVE vanderbilt_slice_2_live_fetch_approval_request_packet_approved "
        f"REQUEST_ROWS {len(rows)} SOURCE_PLAN_ROWS {source_summary.get('plan_rows')} "
        f"SOURCE_ROWSET_SHA256 {EXPECTED_SOURCE_ROWSET} ROWSET_SHA256 {rowset}"
    )
    summary = {
        "generated_at": generated_at,
        "artifact_label": GBRAIN_ARTIFACT_LABEL,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "approval_request_rows": len(rows),
        "source_plan_rows": source_summary.get("plan_rows"),
        "triage_order": source_summary.get("triage_order"),
        "execution_order": source_summary.get("execution_order"),
        "by_plan_lane": dict(sorted(by_lane.items())),
        "by_candidate_context_status": dict(sorted(by_context.items())),
        "source_execution_plan_rowset_sha256": EXPECTED_SOURCE_ROWSET,
        "gbrain_advisory_effect": GBRAIN_ADVISORY_EFFECT,
        "gbrain_approval_status": "pending_exact_gbrain_approval",
        "gbrain_exact_approval_line": exact_approval_line,
        "gbrain_denial_line": "DENY vanderbilt_slice_2_live_fetch_approval_request_packet_denied",
        "web_fetch_allowed": False,
        "web_fetch_executed": False,
        "future_web_fetch_requested": True,
        "raw_dump_publication_allowed": False,
        "private_artifact_paths_committed": False,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "parser_acceptance_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "accepted_person_rows": 0,
        "approval_required_for": APPROVAL_REQUIRED_FOR,
        "prohibited_mutations": PROHIBITED_MUTATIONS,
        "policy": MUTATION_POLICY,
        "rowset_sha256": rowset,
    }
    if len(rows) != EXPECTED_SOURCE_ROWS:
        raise SystemExit("Vanderbilt slice-2 live-fetch approval request failed row count checks.")

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(
        json.dumps(
            {
                "approval_request_rows": summary["approval_request_rows"],
                "rowset_sha256": summary["rowset_sha256"],
                "gbrain_approval_status": summary["gbrain_approval_status"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
