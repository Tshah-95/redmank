#!/usr/bin/env python3
"""Materialize public school-level GBrain verification posture."""

from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"

OUT_CSV = ARTIFACTS / "school_verification_registry.csv"
OUT_JSON = ARTIFACTS / "school_verification_registry.json"
OUT_SUMMARY = ARTIFACTS / "school_verification_registry_summary.json"

FIELDS = [
    "registry_key",
    "school_name",
    "verification_status",
    "gbrain_decision_effect",
    "packet_status",
    "membership_observation_count",
    "open_gap_rows",
    "gap_drain_queue_rows",
    "gap_drain_active_batch_rows",
    "rowset_sha256",
    "required_approval_line",
    "source_summary_json",
    "source_markdown",
    "mutation_allowed",
    "not_approved_json",
    "recommended_next_action",
    "generated_at",
]

ROWSET_FIELDS = [
    "school_name",
    "verification_status",
    "gbrain_decision_effect",
    "packet_status",
    "membership_observation_count",
    "open_gap_rows",
    "gap_drain_queue_rows",
    "gap_drain_active_batch_rows",
    "rowset_sha256",
    "source_summary_json",
    "mutation_allowed",
]

SCHOOL_READINESS_SUMMARY_FILES = [
    ARTIFACTS / "stanford_school_readiness_packet_summary.json",
]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def int_value(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("registry_key", "")))
    ]
    return sha256_text(dumps(material))


def readiness_row(summary_path: Path, generated_at: str) -> dict[str, object] | None:
    summary = read_json(summary_path)
    if not isinstance(summary, dict) or not summary:
        return None

    school_name = str(summary.get("school_name") or "")
    if not school_name:
        return None
    approved = bool(summary.get("gbrain_approval_verified")) and bool(summary.get("gbrain_decision_effect"))
    packet_status = str(summary.get("packet_status") or "")
    source_markdown = str(summary.get("markdown") or "")
    not_approved = summary.get("not_approved") if isinstance(summary.get("not_approved"), list) else []

    return {
        "registry_key": stable_key("school_verification_registry", school_name, summary.get("rowset_sha256")),
        "school_name": school_name,
        "verification_status": "school_verified_by_gbrain" if approved else "not_school_verified",
        "gbrain_decision_effect": summary.get("gbrain_decision_effect", ""),
        "packet_status": packet_status,
        "membership_observation_count": summary.get("accepted_stanford_membership_observations", ""),
        "open_gap_rows": summary.get("open_gap_rows", 0),
        "gap_drain_queue_rows": summary.get("gap_drain_queue_rows", ""),
        "gap_drain_active_batch_rows": summary.get("gap_drain_active_batch_rows", ""),
        "rowset_sha256": summary.get("rowset_sha256", ""),
        "required_approval_line": summary.get("required_approval_line", ""),
        "source_summary_json": rel(summary_path),
        "source_markdown": source_markdown,
        "mutation_allowed": "false",
        "not_approved_json": dumps(not_approved),
        "recommended_next_action": (
            "Treat this as school-level verified under the packet boundary; do not infer person ingestion, "
            "denominator closure, URL rewrite, enrichment acceptance, or identity collapse."
            if approved
            else "Prepare exact GBrain school-readiness packet before marking the school verified."
        ),
        "generated_at": generated_at,
    }


def main() -> None:
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = [
        row
        for row in (readiness_row(path, generated_at) for path in SCHOOL_READINESS_SUMMARY_FILES)
        if row is not None
    ]
    rows.sort(key=lambda row: str(row["school_name"]))

    by_status = Counter(str(row["verification_status"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": rel(OUT_CSV),
        "json": rel(OUT_JSON),
        "registry_rows": len(rows),
        "verified_school_rows": int(by_status.get("school_verified_by_gbrain", 0)),
        "by_verification_status": dict(sorted(by_status.items())),
        "mutation_allowed": False,
        "policy": (
            "Public school verification registry. It records GBrain school-level verification decisions and "
            "their exact packet boundaries. It does not publish raw GBrain responses and does not authorize "
            "person ingestion, training-state mutation, denominator closure, URL rewrites, enrichment facts, "
            "or identity collapse."
        ),
        "rowset_sha256": rowset_sha256(rows),
        "source_summary_files": [rel(path) for path in SCHOOL_READINESS_SUMMARY_FILES if path.exists()],
    }

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    print(json.dumps({"registry_rows": len(rows), "rowset_sha256": summary["rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
