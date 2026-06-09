---
type: research-checkpoint
title: Top50 Engine Operating Snapshot
created_at: 2026-06-09T05:10:04.120236+00:00
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
  "rowset_sha256": "d4c5ca61d015919e8fae37d899ff5ccb648ae9a64418d2c58f35c0732ce35701",
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
    "candidate_only_parser_fingerprint_rows": 229,
    "candidate_only_parser_output_rows": 233,
    "candidate_only_parser_output_rowset_sha256": "312918a4b812f82bbf858a0b5c50d5d04394fa8be634a1a0cc9a7ad6aaa2f034",
    "execution_workbench_rows": 20,
    "execution_workbench_rowset_sha256": "b9f7addcc552747c3b0d12459d5055efd60a08d610996aeeeff0a8ea095b2f3b",
    "execution_workbench_unique_fetch_urls": 16,
    "parser_scope_decision_rows": 20,
    "parser_scope_decision_rowset_sha256": "aa94351eae7a7309d2b760a891f69538d8a8998058fc1ceb24af3d2b918644b8",
    "parser_scope_execution_evidence_rows": 20,
    "parser_scope_execution_evidence_rowset_sha256": "db7e7c7b03c31c20a6b3b9c2a17da2d24cbf0c725f97872452db63a2e5942812",
    "parser_scope_execution_evidence_total_candidate_count": 348,
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
| vanderbilt_targeted_route_parser_scope_gbrain_approval | ready_non_mutating_candidate_parser_output_verification | artifacts/data/vanderbilt_candidate_only_parser_outputs.csv | 312918a4b812f82bbf858a0b5c50d5d04394fa8be634a1a0cc9a7ad6aaa2f034 | Verify the candidate-only Vanderbilt parser outputs, preserve raw-name-free diagnostics, and build the next exact approval packet before any person ingestion, denominator closure, or accepted roster rows. |
| vanderbilt_active_gap_resolution_manifest | active_non_mutating_discovery_queue | artifacts/data/school_gap_resolution_manifest.csv |  | Use the Vanderbilt-only active gap manifest to choose bounded source-discovery, route-inspection, rendered-review, or closure-packet work. |
