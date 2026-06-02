#!/usr/bin/env python3
"""Rebuild the local SQLite warehouse from committed artifacts only."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


PIPELINE = [
    ["python3", "scripts/build_sqlite.py"],
    ["python3", "scripts/replay_committed_warehouse_artifacts.py"],
    ["python3", "scripts/audit_reconciliation_decisions.py", "--as-of-year", "2026"],
    ["python3", "scripts/audit_person_evidence_review_packets.py"],
    ["python3", "scripts/audit_enrichment_acceptance.py"],
    ["python3", "scripts/audit_warehouse_reproducibility.py"],
    ["python3", "scripts/audit_source_utility_scorecard.py"],
    ["python3", "scripts/report_source_quality.py"],
    ["python3", "scripts/audit_warehouse_reproducibility.py"],
    ["python3", "scripts/summarize_warehouse.py"],
]


def run(command: list[str], dry_run: bool) -> None:
    print(" ".join(command), flush=True)
    if dry_run:
        return
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    for command in PIPELINE:
        run(command, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
