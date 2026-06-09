---
type: research-checkpoint
title: Top50 Public Contributor Worklist
created_at: 2026-06-09T06:45:28.552032+00:00
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
  "generated_at": "2026-06-09T06:45:28.552032+00:00",
  "high_rows": 1,
  "json": "artifacts/data/top50_public_contributor_worklist.json",
  "low_rows": 0,
  "markdown": "artifacts/research/top50-public-contributor-worklist-2026-06-09.md",
  "medium_rows": 1,
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating public contributor worklist for the top-50/Vanderbilt engine. It ranks bounded public-safe operator actions from committed verification, snapshot, Vanderbilt batch-packet, decision-audit, and gap manifest artifacts. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "rowset_sha256": "f05605e694a6777c7e6b5f3809412ecee2846bbdd30b316d3b9bdaa2d1d0b319",
  "school_verification_allowed": false,
  "source_snapshot_rowset_sha256": "b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48",
  "source_vanderbilt_batch_packet_rowset_sha256": "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f",
  "source_vanderbilt_operator_packet_rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
  "source_vanderbilt_patch_template_rowset_sha256": "5532d007555997f54d25884baba2f4e594d4ff1fa286301bfa6f87fc64caaa8d",
  "source_verification_rowset_sha256": "3005db62be8f9b3adcb1d5b17399c495fdbdad9099269097f7b5367ba9a9a80d",
  "total_impact_count": 447,
  "worklist_rows": 4
}
```

## Work Items

| order | lane | status | priority | impact | source | target | next action |
| ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | verify_public_clone_substrate | ready_and_passing | 980 | 16 | artifacts/data/top50_public_clone_verification_summary.json | artifacts/data/top50_public_clone_verification_summary.json | Run python3 scripts/materialize_top50_public_clone_verification.py after any public top-50 artifact change. |
| 2 | vanderbilt_bounded_manual_review_packets | ready_for_non_mutating_reviewer_input | 940 | 159 | artifacts/data/vanderbilt_public_reviewer_operator_packets.csv | artifacts/data/vanderbilt_candidate_reviewer_decisions.csv | Work one public-safe operator packet at a time, copy relevant rows from artifacts/data/vanderbilt_reviewer_decision_patch_template.csv, fill only non-mutating decisions, dry-run scripts/apply_vanderbilt_reviewer_decision_patch.py, then apply and rerun the decision audit, batch-packet materializer, and operator-packet materializer. |
| 3 | vanderbilt_active_gap_manifest_triage | ready_for_non_mutating_source_discovery_planning | 760 | 113 | artifacts/data/school_gap_resolution_manifest.csv | artifacts/data/school_gap_resolution_batch_packets.csv | Use existing gap-resolution batches/packets for source-discovery planning; do not regenerate the gap manifest in a public clone unless the core source inputs are present. |
| 4 | future_exact_approval_packet_after_valid_decisions | blocked_until_valid_non_mutating_decisions | 640 | 159 | artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json | artifacts/data/vanderbilt_candidate_acceptance_or_closure_approval_packet.csv | Do not build person-ingestion, denominator-closure, parser-acceptance, scope-closure, or identity-collapse packets until reviewer decisions are present and the decision audit passes. |
