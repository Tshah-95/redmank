#!/usr/bin/env python3
"""Write one bounded Vanderbilt reviewer workbook slice to /tmp by default."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import materialize_vanderbilt_reviewer_decision_patch_workbook as workbook_materializer


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"

DEFAULT_WORKBOOK = ARTIFACTS / "vanderbilt_reviewer_decision_patch_workbook.csv"
URL_RE = re.compile(r"https?://", re.I)


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


def validate_workbook(fields: list[str], rows: list[dict[str, str]]) -> None:
    missing = [field for field in workbook_materializer.FIELDS if field not in fields]
    extras = [field for field in fields if field not in set(workbook_materializer.FIELDS)]
    if missing:
        raise SystemExit("Workbook is missing required columns: " + ", ".join(missing))
    if extras:
        raise SystemExit("Workbook contains unsupported columns: " + ", ".join(extras))
    if any("reviewer_note" in field for field in fields):
        raise SystemExit("Workbook must not contain reviewer_note columns.")
    text = json.dumps(rows, ensure_ascii=True, sort_keys=True)
    if "reviewer_note" in text:
        raise SystemExit("Workbook rows must not contain reviewer_note text.")
    if URL_RE.search(text):
        raise SystemExit("Workbook rows contain URL-like text.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selector = parser.add_mutually_exclusive_group(required=True)
    selector.add_argument("--execution-order", type=int, help="Operator packet execution_order to slice.")
    selector.add_argument("--operator-packet-key", help="Operator packet key to slice.")
    parser.add_argument("--workbook", default=str(DEFAULT_WORKBOOK), help="Source Vanderbilt reviewer workbook CSV.")
    parser.add_argument("--output", help="Slice output CSV. Defaults to /tmp/vanderbilt_reviewer_workbook_order_<n>.csv.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook = resolved(args.workbook)
    if not workbook.exists():
        raise SystemExit("Workbook file does not exist: " + str(workbook))
    fields, rows = read_csv_rows(workbook)
    validate_workbook(fields, rows)

    if args.execution_order is not None:
        selected = [row for row in rows if row.get("operator_execution_order", "") == str(args.execution_order)]
        selector_value = str(args.execution_order)
    else:
        selected = [row for row in rows if row.get("operator_packet_key", "") == args.operator_packet_key]
        selector_value = str(selected[0].get("operator_execution_order", "")) if selected else "unknown"
    if not selected:
        raise SystemExit("No workbook rows matched the requested operator packet selector.")

    packet_keys = sorted({row.get("operator_packet_key", "") for row in selected})
    execution_orders = sorted({row.get("operator_execution_order", "") for row in selected}, key=lambda value: int(value))
    if len(packet_keys) != 1 or len(execution_orders) != 1:
        raise SystemExit("Workbook selector matched more than one operator packet.")

    output = resolved(args.output) if args.output else Path(f"/tmp/vanderbilt_reviewer_workbook_order_{selector_value}.csv")
    write_csv(output, workbook_materializer.FIELDS, selected)

    extract_output = Path(f"/tmp/vanderbilt_reviewer_patch_order_{execution_orders[0]}.csv")
    summary = {
        "workbook": str(workbook),
        "output": str(output),
        "operator_packet_key": packet_keys[0],
        "execution_order": execution_orders[0],
        "program_name": selected[0].get("program_name", ""),
        "review_queue_lane": selected[0].get("review_queue_lane", ""),
        "slice_rows": len(selected),
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "raw_candidate_names_committed": False,
        "raw_person_urls_committed": False,
        "extract_command": (
            "python3 scripts/extract_vanderbilt_reviewer_decision_patch.py "
            f"--workbook {output} --output {extract_output}"
        ),
        "patch_dry_run_command": f"python3 scripts/apply_vanderbilt_reviewer_decision_patch.py --patch {extract_output}",
    }
    print(json.dumps(summary, ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    main()
