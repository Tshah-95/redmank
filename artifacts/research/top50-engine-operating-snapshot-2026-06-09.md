---
type: research-checkpoint
title: Top50 Engine Operating Snapshot
created_at: 2026-06-09T04:53:20.678859+00:00
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
  "rowset_sha256": "392460e6ceca1d02aac6ad04dbbeffb1ff833e631938fe06f488300ddfea3199",
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
  },
  "vanderbilt_targeted_parser_scope": {
    "approved_next_packet_rows": 20,
    "approved_next_packet_rowset_sha256": "098c0a813eb577552b46e9454fbf2e9088bcee228d0aa678827439eba082e261",
    "execution_workbench_rows": 20,
    "execution_workbench_rowset_sha256": "b9f7addcc552747c3b0d12459d5055efd60a08d610996aeeeff0a8ea095b2f3b",
    "execution_workbench_unique_fetch_urls": 16,
    "review_packet_rows": 20,
    "review_packet_rowset_sha256": "dd7ba52cefcec632da434810653bce1b106696ca9a9d94fe3e517f206ae50785",
    "route_observation_rows": 20,
    "route_observation_rowset_sha256": "f547a298bf0efdaba630aa9d184ecd85979d0356039bbbd92d3c2fd026745258",
    "route_observation_unique_urls": 16,
    "route_parser_scope_packet_gbrain_status": "approved_exact_non_mutating_next_artifact_lane",
    "route_parser_scope_packet_rows": 20,
    "route_parser_scope_packet_rowset_sha256": "9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3",
    "route_parser_scope_verification_gbrain_status": "approved_exact_verification_registration",
    "route_parser_scope_verification_rows": 7,
    "route_parser_scope_verification_rowset_sha256": "fb95acaa555f304beb7875fc13209dc1dd4beec8118cc324c87d09c48baca7f5"
  }
}
```

## Next Lanes

| lane | status | artifact | rowset | next action |
| --- | --- | --- | --- | --- |
| vanderbilt_targeted_route_parser_scope_gbrain_approval | ready_non_mutating_parser_build_scope_and_recourse_execution | artifacts/data/vanderbilt_approved_parser_scope_next_packets.csv | 098c0a813eb577552b46e9454fbf2e9088bcee228d0aa678827439eba082e261 | Use the approved next-packet ledger to execute source-specific parser-build review, linked-route scope disposition, General Surgery rendered review, and route recourse work. Keep all outputs candidate-only until a later exact person-ingestion/denominator approval exists. |
| vanderbilt_active_gap_resolution_manifest | active_non_mutating_discovery_queue | artifacts/data/school_gap_resolution_manifest.csv |  | Use the Vanderbilt-only active gap manifest to choose bounded source-discovery, route-inspection, rendered-review, or closure-packet work. |
