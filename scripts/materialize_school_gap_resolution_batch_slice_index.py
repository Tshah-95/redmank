#!/usr/bin/env python3
"""Materialize a public-safe slice index for school gap-resolution batches."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

BATCH_CSV = ARTIFACTS / "school_gap_resolution_batches.csv"
BATCH_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_summary.json"
PACKET_CSV = ARTIFACTS / "school_gap_resolution_batch_packets.csv"
PACKET_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_packet_summary.json"
MANIFEST_SUMMARY = ARTIFACTS / "school_gap_resolution_manifest_summary.json"

OUT_CSV = ARTIFACTS / "school_gap_resolution_batch_slice_index.csv"
OUT_JSON = ARTIFACTS / "school_gap_resolution_batch_slice_index.json"
OUT_SUMMARY = ARTIFACTS / "school_gap_resolution_batch_slice_index_summary.json"
OUT_MD = RESEARCH / "school-gap-resolution-batch-slice-index-2026-06-09.md"

EXPECTED_BATCH_ROWS = 21
EXPECTED_GAP_ROWS = 113

MUTATION_POLICY = (
    "Non-mutating school gap-resolution batch slice index. It lists one bounded /tmp slice command per committed "
    "Vanderbilt gap-resolution batch. It may reference public official-source URLs already committed in gap packets, "
    "but it does not fetch web pages, fill reviewer decisions, approve people, ingest people, close denominators, "
    "verify schools, rewrite URLs, accept enrichment facts, or collapse identities."
)

FIELDS = [
    "slice_index_key",
    "execution_order",
    "school_gap_resolution_batch_key",
    "school_name",
    "sponsoring_institution",
    "next_operator_lane",
    "resolution_category",
    "batch_status",
    "gap_count",
    "program_count",
    "slice_output_path",
    "slice_command",
    "verification_command",
    "target_artifact",
    "required_next_evidence",
    "approval_required_for",
    "prohibited_mutations",
    "source_batch_rows",
    "source_packet_rows",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "private_artifact_paths_committed",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "execution_order",
    "school_gap_resolution_batch_key",
    "school_name",
    "sponsoring_institution",
    "next_operator_lane",
    "resolution_category",
    "batch_status",
    "gap_count",
    "program_count",
    "slice_output_path",
    "slice_command",
    "verification_command",
    "target_artifact",
    "required_next_evidence",
    "approval_required_for",
    "prohibited_mutations",
    "source_batch_rows",
    "source_packet_rows",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "private_artifact_paths_committed",
]

PROHIBITED_MUTATIONS = [
    "person_ingestion",
    "parser_output_as_accepted_people",
    "training_state_mutation",
    "denominator_closure",
    "school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "enrichment_acceptance",
    "raw_dump_publication",
    "unique_person_identity_collapse",
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


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("slice_index_key", "")))
    ]
    return sha256_text(dumps(material))


def private_marker_hits(rows: list[dict[str, object]]) -> list[str]:
    text = dumps(rows)
    return [marker for marker in PRIVATE_PATH_MARKERS if marker in text]


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: School Gap Resolution Batch Slice Index",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "---",
        "",
        "# School Gap Resolution Batch Slice Index",
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
        "## Slices",
        "",
        "| order | lane | category | gaps | slice command |",
        "| ---: | --- | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            "| {execution_order} | {next_operator_lane} | {resolution_category} | {gap_count} | `{slice_command}` |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    batch_summary = read_json(BATCH_SUMMARY)
    packet_summary = read_json(PACKET_SUMMARY)
    manifest_summary = read_json(MANIFEST_SUMMARY)
    if not all(isinstance(item, dict) for item in [batch_summary, packet_summary, manifest_summary]):
        raise SystemExit("Expected gap manifest, batch, and packet summary JSON objects.")
    source_checks = {
        "manifest_rows": manifest_summary.get("rows") == EXPECTED_GAP_ROWS,
        "manifest_mutation_false": manifest_summary.get("mutation_allowed") is False,
        "batch_rows": batch_summary.get("rows") == EXPECTED_BATCH_ROWS,
        "batch_gap_rows": batch_summary.get("gap_rows") == EXPECTED_GAP_ROWS,
        "batch_mutation_false": batch_summary.get("mutation_allowed") is False,
        "packet_rows": packet_summary.get("rows") == EXPECTED_GAP_ROWS,
        "packet_batch_rows": packet_summary.get("batch_rows") == EXPECTED_BATCH_ROWS,
        "packet_mutation_false": packet_summary.get("mutation_allowed") is False,
    }
    if not all(source_checks.values()):
        raise SystemExit("Unexpected school gap slice-index source boundary: " + dumps(source_checks))

    packet_rows = read_csv_rows(PACKET_CSV)
    packets_by_batch: dict[str, list[dict[str, str]]] = {}
    for packet in packet_rows:
        packets_by_batch.setdefault(packet.get("school_gap_resolution_batch_key", ""), []).append(packet)

    generated_at = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, object]] = []
    by_lane: Counter[str] = Counter()
    for batch in sorted(read_csv_rows(BATCH_CSV), key=lambda row: int(row.get("execution_order", 0))):
        execution_order = int(batch.get("execution_order", 0))
        batch_key = batch.get("school_gap_resolution_batch_key", "")
        packet_count = len(packets_by_batch.get(batch_key, []))
        slice_output = f"/tmp/school_gap_resolution_batch_order_{execution_order}.csv"
        slice_command = (
            "python3 scripts/slice_school_gap_resolution_batch_packets.py "
            f"--execution-order {execution_order} --output {slice_output}"
        )
        by_lane[batch.get("next_operator_lane", "")] += 1
        rows.append(
            {
                "slice_index_key": stable_key("school_gap_resolution_batch_slice_index", batch_key, EXPECTED_GAP_ROWS),
                "execution_order": execution_order,
                "school_gap_resolution_batch_key": batch_key,
                "school_name": batch.get("school_name", ""),
                "sponsoring_institution": batch.get("sponsoring_institution", ""),
                "next_operator_lane": batch.get("next_operator_lane", ""),
                "resolution_category": batch.get("resolution_category", ""),
                "batch_status": batch.get("batch_status", ""),
                "gap_count": int(batch.get("gap_count", "0") or "0"),
                "program_count": int(batch.get("program_count", "0") or "0"),
                "slice_output_path": slice_output,
                "slice_command": slice_command,
                "verification_command": (
                    "python3 scripts/materialize_school_gap_resolution_batches.py && "
                    "python3 scripts/materialize_school_gap_resolution_batch_packets.py && "
                    "python3 scripts/materialize_school_gap_resolution_batch_slice_index.py"
                ),
                "target_artifact": batch.get("target_artifact", ""),
                "required_next_evidence": batch.get("required_next_evidence", ""),
                "approval_required_for": (
                    "person_ingestion; denominator_closure; school_verification; parser_acceptance; "
                    "scope_closure; url_rewrite; identity_collapse"
                ),
                "prohibited_mutations": "; ".join(PROHIBITED_MUTATIONS),
                "source_batch_rows": EXPECTED_BATCH_ROWS,
                "source_packet_rows": EXPECTED_GAP_ROWS,
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "private_artifact_paths_committed": "false",
                "evidence_json": dumps(
                    {
                        "packet_rows_in_slice": packet_count,
                        "slice_output_policy": "tmp_only_default",
                        "public_urls_may_be_present_in_packet_slice": True,
                        "private_artifact_paths_committed": False,
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    hits = private_marker_hits(rows)
    if hits:
        raise SystemExit("Slice index rows contain private artifact path markers: " + ", ".join(hits))
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_manifest_summary": str(MANIFEST_SUMMARY.relative_to(ROOT)),
        "source_batch_summary": str(BATCH_SUMMARY.relative_to(ROOT)),
        "source_packet_summary": str(PACKET_SUMMARY.relative_to(ROOT)),
        "slice_index_rows": len(rows),
        "gap_rows_represented": sum(int(row["gap_count"]) for row in rows),
        "by_next_operator_lane": dict(sorted(by_lane.items())),
        "slice_outputs_default_tmp_only": True,
        "public_urls_may_be_present_in_packet_slices": True,
        "private_artifact_paths_committed": False,
        "reviewer_note_column_committed": False,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)
    if len(rows) != EXPECTED_BATCH_ROWS or summary["gap_rows_represented"] != EXPECTED_GAP_ROWS:
        raise SystemExit("School gap-resolution slice index failed completeness checks.")

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({key: summary[key] for key in ["slice_index_rows", "gap_rows_represented", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
