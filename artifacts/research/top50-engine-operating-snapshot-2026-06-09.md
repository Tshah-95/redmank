---
type: research-checkpoint
title: Top50 Engine Operating Snapshot
created_at: 2026-06-09T06:36:39.328748+00:00
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
  "rowset_sha256": "b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48",
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
    "candidate_only_parser_fingerprint_rows": 155,
    "candidate_only_parser_output_rows": 159,
    "candidate_only_parser_output_rowset_sha256": "2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba",
    "candidate_parser_output_verification_fail_rows": 0,
    "candidate_parser_output_verification_pass_rows": 9,
    "candidate_parser_output_verification_rows": 9,
    "candidate_parser_output_verification_rowset_sha256": "918556f5b5a33b5d8e7181ed6654a9b7773b8c8a24f09f9a23b06c7157d39fe2",
    "candidate_review_batch_packet_decision_rows": 159,
    "candidate_review_batch_packet_gbrain_status": "approved_non_mutating_batch_packet_materialization",
    "candidate_review_batch_packet_invalid_rows": 0,
    "candidate_review_batch_packet_pending_rows": 159,
    "candidate_review_batch_packet_rows": 20,
    "candidate_review_batch_packet_rowset_sha256": "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f",
    "candidate_review_decision_scaffold_rows": 159,
    "candidate_review_decision_scaffold_rowset_sha256": "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938",
    "candidate_review_manual_decision_template_rows": 159,
    "candidate_review_queue_approval_rows": 159,
    "candidate_review_queue_approval_rowset_sha256": "a62defd685b64560a138cfaeb82956254f49341ce982bb549fe1846b25dd5bd5",
    "candidate_review_queue_approval_status": "approved_exact_non_mutating_review_queue_materialization",
    "candidate_review_queue_rows": 159,
    "candidate_review_queue_rowset_sha256": "b74b337bfa43406d8a200956d469eb5dc0d41902c197f78af85001f18750b148",
    "candidate_review_scaffold_verification_fail_rows": 0,
    "candidate_review_scaffold_verification_pass_rows": 7,
    "candidate_review_scaffold_verification_rows": 7,
    "candidate_review_scaffold_verification_rowset_sha256": "24e03f71174cd456b4783457113d64d4b15185721fc86092ca2a5f47e7eb4260",
    "candidate_reviewer_decision_audit_rows": 159,
    "candidate_reviewer_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
    "candidate_reviewer_decision_invalid_rows": 0,
    "candidate_reviewer_decision_pending_rows": 159,
    "candidate_reviewer_decision_valid_rows": 0,
    "execution_workbench_rows": 20,
    "execution_workbench_rowset_sha256": "b9f7addcc552747c3b0d12459d5055efd60a08d610996aeeeff0a8ea095b2f3b",
    "execution_workbench_unique_fetch_urls": 16,
    "parser_scope_decision_rows": 20,
    "parser_scope_decision_rowset_sha256": "aa94351eae7a7309d2b760a891f69538d8a8998058fc1ceb24af3d2b918644b8",
    "parser_scope_execution_evidence_rows": 20,
    "parser_scope_execution_evidence_rowset_sha256": "db7e7c7b03c31c20a6b3b9c2a17da2d24cbf0c725f97872452db63a2e5942812",
    "parser_scope_execution_evidence_total_candidate_count": 348,
    "public_reviewer_operator_missing_required_template_column_mentions": 0,
    "public_reviewer_operator_packet_rows": 20,
    "public_reviewer_operator_packet_rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
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
| vanderbilt_targeted_route_parser_scope_gbrain_approval | ready_for_public_safe_vanderbilt_operator_packets | artifacts/data/vanderbilt_public_reviewer_operator_packets.csv | 6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173 | Use the public-safe Vanderbilt reviewer operator packets to enter non-mutating reviewer decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit, batch packet materializer, and operator-packet materializer. Any accepted person rows, denominator closure, identity reconciliation, parser acceptance, or scope closure still requires a later exact approval packet. |
| vanderbilt_active_gap_resolution_manifest | active_non_mutating_discovery_queue | artifacts/data/school_gap_resolution_manifest.csv |  | Use the Vanderbilt-only active gap manifest to choose bounded source-discovery, route-inspection, rendered-review, or closure-packet work. |
