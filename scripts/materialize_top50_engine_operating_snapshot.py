#!/usr/bin/env python3
"""Materialize the public top-50 roster-engine operating snapshot."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

OUT_JSON = ARTIFACTS / "top50_engine_operating_snapshot.json"
OUT_MD = RESEARCH / "top50-engine-operating-snapshot-2026-06-09.md"

SUMMARY_FILES = {
    "target_registry": ARTIFACTS / "top50_medical_school_targets_summary.json",
    "school_verification_registry": ARTIFACTS / "school_verification_registry_summary.json",
    "school_capability_manifest": ARTIFACTS / "school_capability_manifest_summary.json",
    "school_readiness_dossiers": ARTIFACTS / "school_readiness_dossier_summary.json",
    "school_gap_resolution_manifest": ARTIFACTS / "school_gap_resolution_manifest_summary.json",
    "school_gap_resolution_batches": ARTIFACTS / "school_gap_resolution_batch_summary.json",
    "school_gap_resolution_batch_packets": ARTIFACTS / "school_gap_resolution_batch_packet_summary.json",
    "source_discovery_playbook": ARTIFACTS / "top50_scraper_source_discovery_playbook_summary.json",
    "vanderbilt_targeted_source_discovery": ARTIFACTS / "vanderbilt_targeted_gap_source_discovery_workbench_summary.json",
    "vanderbilt_parser_scope_review": ARTIFACTS / "vanderbilt_targeted_parser_scope_review_packet_summary.json",
    "vanderbilt_parser_scope_execution_workbench": ARTIFACTS
    / "vanderbilt_targeted_parser_scope_execution_workbench_summary.json",
}


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256_json(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def summary_ref(name: str, path: Path) -> dict[str, object]:
    summary = read_json(path)
    keys = [
        "rowset_sha256",
        "targets",
        "rows",
        "registry_rows",
        "verified_school_rows",
        "manifest_rows",
        "dossier_rows",
        "open_gap_rows",
        "workbench_rows",
        "review_rows",
        "unique_fetch_urls",
        "mutation_allowed",
        "gbrain_approval_verified",
        "gbrain_registration_status",
        "gbrain_strategy_effect",
    ]
    return {
        "name": name,
        "summary_json": rel(path),
        "exists": path.exists(),
        "selected_summary": {key: summary[key] for key in keys if key in summary},
    }


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    summaries = {name: read_json(path) for name, path in SUMMARY_FILES.items()}
    target_summary = summaries["target_registry"]
    verification_summary = summaries["school_verification_registry"]
    gap_summary = summaries["school_gap_resolution_manifest"]
    playbook_summary = summaries["source_discovery_playbook"]
    vanderbilt_parser_summary = summaries["vanderbilt_parser_scope_review"]
    vanderbilt_execution_summary = summaries["vanderbilt_parser_scope_execution_workbench"]

    next_lanes = [
        {
            "lane": "vanderbilt_targeted_parser_scope_execution_workbench",
            "status": "ready_non_mutating_route_fetch_and_rendered_review",
            "source_artifact": vanderbilt_execution_summary.get(
                "csv", "artifacts/data/vanderbilt_targeted_parser_scope_execution_workbench.csv"
            ),
            "rowset_sha256": vanderbilt_execution_summary.get("rowset_sha256", ""),
            "recommended_next_action": (
                "Fetch/render the queued official routes, preserve route observations, and emit exact parser "
                "acceptance, scope-disposition, or recourse packets. Do not ingest people or close denominators "
                "without exact GBrain approval."
            ),
        },
        {
            "lane": "vanderbilt_active_gap_resolution_manifest",
            "status": "active_non_mutating_discovery_queue",
            "source_artifact": gap_summary.get("csv", "artifacts/data/school_gap_resolution_manifest.csv"),
            "rowset_sha256": gap_summary.get("rowset_sha256", ""),
            "recommended_next_action": (
                "Use the Vanderbilt-only active gap manifest to choose bounded source-discovery, route-inspection, "
                "rendered-review, or closure-packet work."
            ),
        },
    ]

    snapshot = {
        "generated_at": generated_at,
        "json": rel(OUT_JSON),
        "markdown": rel(OUT_MD),
        "target_registry": {
            "target_count": target_summary.get("targets", 0),
            "rowset_sha256": target_summary.get("rowset_sha256", ""),
            "basis": target_summary.get("target_basis", ""),
        },
        "school_verification": {
            "verified_school_rows": verification_summary.get("verified_school_rows", 0),
            "registry_rowset_sha256": verification_summary.get("rowset_sha256", ""),
            "source_summary_files": verification_summary.get("source_summary_files", []),
        },
        "active_gap_resolution": {
            "open_gap_rows": gap_summary.get("open_gap_rows", 0),
            "school_priority_order": gap_summary.get("school_priority_order", []),
            "suppressed_verified_school_raw_gap_rows_by_school": gap_summary.get("suppressed_verified_school_raw_gap_rows_by_school", {}),
            "gbrain_strategy_effect": gap_summary.get("gbrain_strategy_effect", ""),
        },
        "source_discovery_playbook": {
            "rows": playbook_summary.get("rows", 0),
            "rowset_sha256": playbook_summary.get("rowset_sha256", ""),
            "vanderbilt_open_gap_rows_represented": playbook_summary.get("vanderbilt_open_gap_rows_represented", 0),
            "gbrain_approval_verified": playbook_summary.get("gbrain_approval_verified", False),
        },
        "next_lanes": next_lanes,
        "vanderbilt_targeted_parser_scope": {
            "review_packet_rows": vanderbilt_parser_summary.get("review_rows", 0),
            "review_packet_rowset_sha256": vanderbilt_parser_summary.get("rowset_sha256", ""),
            "execution_workbench_rows": vanderbilt_execution_summary.get("workbench_rows", 0),
            "execution_workbench_unique_fetch_urls": vanderbilt_execution_summary.get("unique_fetch_urls", 0),
            "execution_workbench_rowset_sha256": vanderbilt_execution_summary.get("rowset_sha256", ""),
        },
        "mutation_allowed": False,
        "not_approved": [
            "person_ingestion",
            "training_state_mutation",
            "denominator_closure",
            "school_verification_without_exact_gbrain_packet",
            "url_rewrite",
            "unsupported_label_ingestion",
            "profile_contact_research_fact_acceptance",
            "unique_person_identity_collapse",
        ],
        "public_safety_policy": (
            "This snapshot is an operating index over committed public artifacts. It does not include raw GBrain "
            "HTTP responses, browser dumps, debug databases, or raw BRIMR workbooks."
        ),
        "summary_refs": [summary_ref(name, path) for name, path in SUMMARY_FILES.items()],
    }
    snapshot["rowset_sha256"] = sha256_json(
        {
            "target_registry": snapshot["target_registry"],
            "school_verification": snapshot["school_verification"],
            "active_gap_resolution": snapshot["active_gap_resolution"],
            "source_discovery_playbook": snapshot["source_discovery_playbook"],
            "vanderbilt_targeted_parser_scope": snapshot["vanderbilt_targeted_parser_scope"],
            "next_lanes": snapshot["next_lanes"],
            "mutation_allowed": snapshot["mutation_allowed"],
        }
    )

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(snapshot, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Top50 Engine Operating Snapshot",
        "created_at: " + generated_at,
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# Top50 Engine Operating Snapshot",
        "",
        "## Boundary",
        "",
        snapshot["public_safety_policy"],
        "",
        "This snapshot is non-mutating and authorizes no person ingestion, training-state mutation, denominator closure, URL rewrite, enrichment acceptance, or identity collapse.",
        "",
        "## Current State",
        "",
        "```json",
        json.dumps(
            {
                "target_registry": snapshot["target_registry"],
                "school_verification": snapshot["school_verification"],
                "active_gap_resolution": snapshot["active_gap_resolution"],
                "source_discovery_playbook": snapshot["source_discovery_playbook"],
                "vanderbilt_targeted_parser_scope": snapshot["vanderbilt_targeted_parser_scope"],
                "rowset_sha256": snapshot["rowset_sha256"],
            },
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        ),
        "```",
        "",
        "## Next Lanes",
        "",
        "| lane | status | artifact | rowset | next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for lane in next_lanes:
        lines.append(
            "| {lane} | {status} | {source_artifact} | {rowset_sha256} | {recommended_next_action} |".format(**lane)
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"rowset_sha256": snapshot["rowset_sha256"], "next_lanes": len(next_lanes)}, sort_keys=True))


if __name__ == "__main__":
    main()
