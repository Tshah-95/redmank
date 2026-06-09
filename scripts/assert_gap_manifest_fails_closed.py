#!/usr/bin/env python3
"""Assert the school gap manifest fails closed in an incomplete public checkout."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATHS = [
    ROOT / "artifacts" / "data" / "school_gap_resolution_manifest.csv",
    ROOT / "artifacts" / "data" / "school_gap_resolution_manifest.json",
    ROOT / "artifacts" / "data" / "school_gap_resolution_manifest_summary.json",
]
EXPECTED_MESSAGE = "Refusing to write an empty school gap-resolution manifest from an incomplete checkout"


def read_bytes(path: Path) -> bytes:
    return path.read_bytes() if path.exists() else b""


def main() -> None:
    before = {path: read_bytes(path) for path in MANIFEST_PATHS}
    result = subprocess.run(
        ["python3", "scripts/materialize_school_gap_resolution_manifest.py"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    after = {path: read_bytes(path) for path in MANIFEST_PATHS}
    changed = [str(path.relative_to(ROOT)) for path in MANIFEST_PATHS if before[path] != after[path]]
    if changed:
        for path, content in before.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
    if result.returncode == 0:
        raise SystemExit("Expected gap manifest materializer to fail closed, but it exited 0.")
    if EXPECTED_MESSAGE not in result.stdout:
        raise SystemExit("Expected fail-closed message was not present in materializer output.")
    if changed:
        raise SystemExit("Gap manifest materializer changed files before refusing: " + ", ".join(changed))
    print("gap_manifest_fail_closed_assertion_passed")


if __name__ == "__main__":
    main()
