---
type: research-checkpoint
title: Vanderbilt Route Parser Scope Verification Packet
created_at: 2026-06-09T04:47:56.563247+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Route Parser Scope Verification Packet

## Boundary

Non-mutating verification documentation for the Vanderbilt route parser/scope packet. It registers checks, counts, rowsets, and public-safety evidence for a previously denied approval request. It does not approve parser acceptance, parser-build execution, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Required Approval Line

`APPROVE vanderbilt_targeted_route_parser_scope_verification_registration_approved VERIFICATION_ROWS 7 PASS_ROWS 7 TARGET_PACKET_ROWS 20 TARGET_ROWSET_SHA256 9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3 ROWSET_SHA256 fb95acaa555f304beb7875fc13209dc1dd4beec8118cc324c87d09c48baca7f5`

This registration only verifies the parser/scope packet artifact and rowset. It does not approve parser-build execution or any person/denominator mutation.

GBrain registration status: `approved_exact_verification_registration`.

## Summary

```json
{
  "by_check_status": {
    "pass": 7
  },
  "csv": "artifacts/data/vanderbilt_route_parser_scope_verification_packet.csv",
  "gbrain_approval_effect": "vanderbilt_targeted_route_parser_scope_verification_registration_approved",
  "gbrain_denial_effect": "vanderbilt_targeted_route_parser_scope_verification_registration_denied",
  "gbrain_denial_line": "",
  "gbrain_denial_recourse": "",
  "gbrain_registration_status": "approved_exact_verification_registration",
  "generated_at": "2026-06-09T04:47:56.563247+00:00",
  "json": "artifacts/data/vanderbilt_route_parser_scope_verification_packet.json",
  "markdown": "artifacts/research/vanderbilt-route-parser-scope-verification-packet-2026-06-09.md",
  "mutation_allowed": false,
  "policy": "Non-mutating verification documentation for the Vanderbilt route parser/scope packet. It registers checks, counts, rowsets, and public-safety evidence for a previously denied approval request. It does not approve parser acceptance, parser-build execution, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "required_approval_line": "APPROVE vanderbilt_targeted_route_parser_scope_verification_registration_approved VERIFICATION_ROWS 7 PASS_ROWS 7 TARGET_PACKET_ROWS 20 TARGET_ROWSET_SHA256 9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3 ROWSET_SHA256 fb95acaa555f304beb7875fc13209dc1dd4beec8118cc324c87d09c48baca7f5",
  "rowset_sha256": "fb95acaa555f304beb7875fc13209dc1dd4beec8118cc324c87d09c48baca7f5",
  "source_route_observation_rowset_sha256": "f547a298bf0efdaba630aa9d184ecd85979d0356039bbbd92d3c2fd026745258",
  "target_packet_csv": "artifacts/data/vanderbilt_targeted_route_parser_scope_packet.csv",
  "target_packet_json": "artifacts/data/vanderbilt_targeted_route_parser_scope_packet.json",
  "target_packet_markdown": "artifacts/research/vanderbilt-targeted-route-parser-scope-packet-2026-06-09.md",
  "target_packet_rows": 20,
  "target_packet_rowset_sha256": "9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3",
  "target_packet_summary": "artifacts/data/vanderbilt_targeted_route_parser_scope_packet_summary.json",
  "verification_rows": 7
}
```

## Checks

| check | status | observed |
| --- | --- | --- |
| gbrain_denial_recourse_recorded | pass | "denied_needs_verification_documentation" |
| mutation_boundary_preserved | pass | {"source_mutation_allowed":false,"target_mutation_allowed":false} |
| public_safety_no_raw_signal_names_in_route_signal_json | pass | [] |
| route_signal_counts_match | pass | {"http_error_needs_retry_or_recourse":1,"official_route_current_roster_signal_needs_parser_scope_packet":19} |
| source_route_observation_rowset_matches_summary | pass | {"source_summary_rowset":"f547a298bf0efdaba630aa9d184ecd85979d0356039bbbd92d3c2fd026745258","target_summary_source_rowset":"f547a298bf0efdaba630aa9d184ecd85979d0356039bbbd92d3c2fd026745258"} |
| target_packet_rows_and_lanes_match | pass | {"by_lane":{"exact_parser_build_review":15,"linked_route_scope_disposition_review":3,"rendered_general_surgery_parser_scope_review":1,"route_recourse_review":1},"packet_rows":20} |
| target_packet_rowset_matches_summary | pass | "9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3" |
