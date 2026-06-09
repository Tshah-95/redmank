#!/usr/bin/env python3
"""Write one bounded school gap-resolution batch packet slice to /tmp by default."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"

DEFAULT_PACKETS = ARTIFACTS / "school_gap_resolution_batch_packets.csv"
PRIVATE_PATH_MARKERS = [
    "artifacts/data/gbrain_",
    "artifacts/data/browser_page_dumps/",
    "artifacts/data/debug_",
    "artifacts/data/raw/",
    ".playwright-mcp/",
    "inbox/",
    "reports/",
]
SANITIZED_FIELDS = ["source_artifacts_json"]


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def resolved(value: str) -> Path:
    return Path(value).expanduser().resolve()


def validate_packet_rows(fields: list[str], rows: list[dict[str, str]]) -> None:
    required = [
        "school_gap_resolution_batch_key",
        "execution_order",
        "gap_key",
        "program_name",
        "next_operator_lane",
        "target_artifact",
        "gbrain_packet_required_for",
    ]
    missing = [field for field in required if field not in fields]
    if missing:
        raise SystemExit("Gap packet CSV is missing required columns: " + ", ".join(missing))
    text = json.dumps(rows, ensure_ascii=True, sort_keys=True)
    if "reviewer_note" in text:
        raise SystemExit("Gap packet rows must not contain reviewer_note text.")


def sanitize_rows(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[str]]:
    sanitized_rows: list[dict[str, str]] = []
    sanitized_fields: set[str] = set()
    for row in rows:
        next_row = dict(row)
        for field in SANITIZED_FIELDS:
            value = next_row.get(field, "")
            if any(marker in value for marker in PRIVATE_PATH_MARKERS):
                next_row[field] = json.dumps(
                    {
                        "sanitized_for_public_slice": True,
                        "reason": "source artifact list contained private or scratch artifact path markers",
                    },
                    ensure_ascii=True,
                    sort_keys=True,
                )
                sanitized_fields.add(field)
        sanitized_rows.append(next_row)
    text = json.dumps(sanitized_rows, ensure_ascii=True, sort_keys=True)
    private_hits = [marker for marker in PRIVATE_PATH_MARKERS if marker in text]
    if private_hits:
        raise SystemExit("Sanitized gap packet rows still contain private artifact path markers: " + ", ".join(private_hits))
    return sanitized_rows, sorted(sanitized_fields)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--execution-order", type=int, help="Gap batch execution_order to slice.")
    selector.add_argument("--batch-key", help="school_gap_resolution_batch_key to slice.")
    parser.add_argument("--packets", default=str(DEFAULT_PACKETS), help="Source school gap-resolution batch packet CSV.")
    parser.add_argument("--output", help="Slice output CSV. Defaults to /tmp/school_gap_resolution_batch_order_<n>.csv.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    packets_path = resolved(args.packets)
    if not packets_path.exists():
        raise SystemExit("Gap packet CSV does not exist: " + str(packets_path))
    fields, rows = read_csv_rows(packets_path)
    validate_packet_rows(fields, rows)

    if args.execution_order is not None:
        selected = [row for row in rows if row.get("execution_order", "") == str(args.execution_order)]
        selector_value = str(args.execution_order)
    else:
        selected = [row for row in rows if row.get("school_gap_resolution_batch_key", "") == args.batch_key]
        selector_value = selected[0].get("execution_order", "unknown") if selected else "unknown"
    if not selected:
        raise SystemExit("No gap packet rows matched the requested batch selector.")

    batch_keys = sorted({row.get("school_gap_resolution_batch_key", "") for row in selected})
    execution_orders = sorted({row.get("execution_order", "") for row in selected}, key=lambda value: int(value))
    if len(batch_keys) != 1 or len(execution_orders) != 1:
        raise SystemExit("Gap packet selector matched more than one batch.")

    output = resolved(args.output) if args.output else Path(f"/tmp/school_gap_resolution_batch_order_{selector_value}.csv")
    sanitized, sanitized_fields = sanitize_rows(selected)
    write_csv(output, fields, sanitized)
    summary = {
        "packets": str(packets_path),
        "output": str(output),
        "school_gap_resolution_batch_key": batch_keys[0],
        "execution_order": execution_orders[0],
        "school_name": selected[0].get("school_name", ""),
        "next_operator_lane": selected[0].get("next_operator_lane", ""),
        "resolution_category": selected[0].get("resolution_category", ""),
        "slice_rows": len(selected),
        "sanitized_fields": sanitized_fields,
        "private_artifact_paths_committed": False,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "recommended_next_actions": sorted({row.get("recommended_packet_action", "") for row in selected if row.get("recommended_packet_action", "")}),
        "verification_command": (
            "python3 scripts/materialize_school_gap_resolution_batches.py && "
            "python3 scripts/materialize_school_gap_resolution_batch_packets.py"
        ),
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
