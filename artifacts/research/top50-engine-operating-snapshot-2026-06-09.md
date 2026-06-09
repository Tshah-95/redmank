---
type: research-checkpoint
title: Top50 Engine Operating Snapshot
created_at: 2026-06-09T04:15:43.808892+00:00
project: top-50-medical-school-roster-engine
---

# Top50 Engine Operating Snapshot

## Boundary

This snapshot is an operating index over committed public artifacts. It does not include raw GBrain HTTP responses, browser dumps, debug databases, or raw BRIMR workbooks.

This snapshot is non-mutating and authorizes no person ingestion, training-state mutation, denominator closure, URL rewrite, enrichment acceptance, or identity collapse.

## Current State

```json
{
  "active_gap_resolution": {
    "gbrain_strategy_effect": "top50_gap_resolution_manifest_strategy_non_mutating_stanford_first_vanderbilt_second",
    "open_gap_rows": 113,
    "school_priority_order": [
      "STANFORD UNIVERSITY SCH OF MEDICINE",
      "VANDERBILT UNIVERSITY SCH OF MEDICINE"
    ],
    "suppressed_verified_school_raw_gap_rows_by_school": {
      "STANFORD UNIVERSITY SCH OF MEDICINE": 69
    }
  },
  "rowset_sha256": "8cb6f5ca85f84ead769e5e4d72e8bcbaa4ebe0e9b1479009b7004828c2afabcf",
  "school_verification": {
    "registry_rowset_sha256": "e99eb07b856f8bdd546d2ac2bb0641c22cd2bedd69e42d8f38f7e5db04823e29",
    "source_summary_files": [
      "artifacts/data/stanford_school_readiness_packet_summary.json"
    ],
    "verified_school_rows": 1
  },
  "source_discovery_playbook": {
    "gbrain_approval_verified": true,
    "rows": 48,
    "rowset_sha256": "1b33439d36c878a527294dea38b8662bc69d5634c4427ad21ffa878b3db1e355",
    "vanderbilt_open_gap_rows_represented": 113
  },
  "target_registry": {
    "basis": "BRIMR 2024 NIH funding - Schools of Medicine",
    "rowset_sha256": "fa547bf602d8dc9998189a0fabe2b45a1cba6892239eedf391cdb65c6ef419d8",
    "target_count": 50
  }
}
```

## Next Lanes

| lane | status | artifact | rowset | next action |
| --- | --- | --- | --- | --- |
| vanderbilt_targeted_parser_scope_review | ready_non_mutating_parser_scope_execution | artifacts/data/vanderbilt_targeted_parser_scope_review_packet.csv | dd7ba52cefcec632da434810653bce1b106696ca9a9d94fe3e517f206ae50785 | Run parser/scope review rows into exact parser acceptance, rendered review, or source-discovery recourse packets. Do not ingest people or close denominators without exact GBrain approval. |
| vanderbilt_active_gap_resolution_manifest | active_non_mutating_discovery_queue | artifacts/data/school_gap_resolution_manifest.csv |  | Use the Vanderbilt-only active gap manifest to choose bounded source-discovery, route-inspection, rendered-review, or closure-packet work. |
