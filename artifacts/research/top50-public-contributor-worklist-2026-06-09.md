---
type: research-checkpoint
title: Top50 Public Contributor Worklist
created_at: 2026-06-09T06:03:34.365521+00:00
project: top-50-medical-school-roster-engine
---

# Top50 Public Contributor Worklist

## Boundary

Non-mutating public contributor worklist for the top-50/Vanderbilt engine. It ranks bounded public-safe operator actions from committed verification, snapshot, Vanderbilt batch-packet, decision-audit, and gap manifest artifacts. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "by_action_lane": {
    "future_exact_approval_packet_after_valid_decisions": 1,
    "vanderbilt_active_gap_manifest_triage": 1,
    "vanderbilt_bounded_manual_review_packets": 1,
    "verify_public_clone_substrate": 1
  },
  "by_action_status": {
    "blocked_until_valid_non_mutating_decisions": 1,
    "ready_and_passing": 1,
    "ready_for_non_mutating_reviewer_input": 1,
    "ready_for_non_mutating_source_discovery_planning": 1
  },
  "critical_rows": 2,
  "csv": "artifacts/data/top50_public_contributor_worklist.csv",
  "denominator_closure_allowed": false,
  "gbrain_approval_line": "APPROVE top50_public_contributor_worklist_lane_approved",
  "gbrain_approval_status": "approved_non_mutating_public_contributor_worklist_lane",
  "generated_at": "2026-06-09T06:03:34.365521+00:00",
  "high_rows": 1,
  "json": "artifacts/data/top50_public_contributor_worklist.json",
  "low_rows": 0,
  "markdown": "artifacts/research/top50-public-contributor-worklist-2026-06-09.md",
  "medium_rows": 1,
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating public contributor worklist for the top-50/Vanderbilt engine. It ranks bounded public-safe operator actions from committed verification, snapshot, Vanderbilt batch-packet, decision-audit, and gap manifest artifacts. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "rowset_sha256": "3baf8429b506fdca5df2a35e5d9f23c1be976d3fba84c58024b6ac1fa1809f8f",
  "school_verification_allowed": false,
  "source_snapshot_rowset_sha256": "2743bdc6aa80c59dbcfa2f4dceb4a84668cbaff298a4d79756f79a6bad222588",
  "source_vanderbilt_batch_packet_rowset_sha256": "1f9da0ab244581dbf5782eab572d5045b8a53c8bffc9d4892e077ca1c7b0e30e",
  "source_verification_rowset_sha256": "0347fde0a9594cd476c49938e55bc710d46104f325f061221c324902f95cc490",
  "total_impact_count": 444,
  "worklist_rows": 4
}
```

## Work Items

| order | lane | status | priority | impact | source | target | next action |
| ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | verify_public_clone_substrate | ready_and_passing | 980 | 13 | artifacts/data/top50_public_clone_verification_summary.json | artifacts/data/top50_public_clone_verification_summary.json | Run python3 scripts/materialize_top50_public_clone_verification.py after any public top-50 artifact change. |
| 2 | vanderbilt_bounded_manual_review_packets | ready_for_non_mutating_reviewer_input | 940 | 159 | artifacts/data/vanderbilt_candidate_review_batch_packets.csv | artifacts/data/vanderbilt_candidate_reviewer_decisions.csv | Work one bounded packet at a time, enter only non-mutating decisions in the reviewer decision template, then rerun the decision audit and batch-packet materializer. |
| 3 | vanderbilt_active_gap_manifest_triage | ready_for_non_mutating_source_discovery_planning | 760 | 113 | artifacts/data/school_gap_resolution_manifest.csv | artifacts/data/school_gap_resolution_batch_packets.csv | Use existing gap-resolution batches/packets for source-discovery planning; do not regenerate the gap manifest in a public clone unless the core source inputs are present. |
| 4 | future_exact_approval_packet_after_valid_decisions | blocked_until_valid_non_mutating_decisions | 640 | 159 | artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json | artifacts/data/vanderbilt_candidate_acceptance_or_closure_approval_packet.csv | Do not build person-ingestion, denominator-closure, parser-acceptance, scope-closure, or identity-collapse packets until reviewer decisions are present and the decision audit passes. |
