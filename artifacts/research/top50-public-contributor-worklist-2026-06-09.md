---
type: research-checkpoint
title: Top50 Public Contributor Worklist
created_at: 2026-06-09T09:00:54.757803+00:00
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
    "ready_for_prioritized_reviewer_slice_input": 1
  },
  "critical_rows": 2,
  "csv": "artifacts/data/top50_public_contributor_worklist.csv",
  "denominator_closure_allowed": false,
  "gbrain_approval_line": "APPROVE top50_public_contributor_worklist_lane_approved",
  "gbrain_approval_status": "approved_non_mutating_public_contributor_worklist_lane",
  "generated_at": "2026-06-09T09:00:54.757803+00:00",
  "high_rows": 1,
  "json": "artifacts/data/top50_public_contributor_worklist.json",
  "low_rows": 0,
  "markdown": "artifacts/research/top50-public-contributor-worklist-2026-06-09.md",
  "medium_rows": 1,
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating public contributor worklist for the top-50/Vanderbilt engine. It ranks bounded public-safe operator actions from committed verification, snapshot, Vanderbilt batch-packet, decision-audit, and gap manifest artifacts. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "rowset_sha256": "468f756cc2edf11529384607190f5559c16663976ded77b0a6a2889da9e287ae",
  "school_verification_allowed": false,
  "source_snapshot_rowset_sha256": "b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48",
  "source_vanderbilt_batch_packet_rowset_sha256": "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f",
  "source_vanderbilt_gap_candidate_output_bridge_rowset_sha256": "dfb141c1883d85fd6a8c7c0e015b939414788936eb13dbb04eecb9111ff5b843",
  "source_vanderbilt_gap_parser_scope_bridge_rowset_sha256": "942d131072d56524c9e19832c084b9e2520e43e783e3a9c0c6e2ae30c0f06912",
  "source_vanderbilt_gap_review_queue_bridge_rowset_sha256": "46c2b215f28819df10913fa35f7dff6e7f4afc4ec6c3598e7432088c3f34e10d",
  "source_vanderbilt_gap_review_template_rowset_sha256": "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782",
  "source_vanderbilt_gap_slice_index_rowset_sha256": "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75",
  "source_vanderbilt_gap_targeted_review_packet_rowset_sha256": "d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607",
  "source_vanderbilt_operator_packet_rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
  "source_vanderbilt_patch_slice_index_rowset_sha256": "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4",
  "source_vanderbilt_patch_template_rowset_sha256": "5532d007555997f54d25884baba2f4e594d4ff1fa286301bfa6f87fc64caaa8d",
  "source_vanderbilt_patch_workbook_rowset_sha256": "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3",
  "source_vanderbilt_reviewer_blank_execution_verification_rowset_sha256": "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e",
  "source_vanderbilt_reviewer_execution_readiness_bridge_rowset_sha256": "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa",
  "source_vanderbilt_reviewer_slice_prioritization_plan_rowset_sha256": "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c",
  "source_verification_rowset_sha256": "84ae362168b6aaf892152ee5fefc1fd38dc60c7fb26a1b029518c2ae52efde26",
  "total_impact_count": 514,
  "worklist_rows": 4
}
```

## Work Items

| order | lane | status | priority | impact | source | target | next action |
| ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | verify_public_clone_substrate | ready_and_passing | 980 | 37 | artifacts/data/top50_public_clone_verification_summary.json | artifacts/data/top50_public_clone_verification_summary.json | Run python3 scripts/materialize_top50_public_clone_verification.py after any public top-50 artifact change. |
| 2 | vanderbilt_bounded_manual_review_packets | ready_for_non_mutating_reviewer_input | 940 | 159 | artifacts/data/vanderbilt_public_reviewer_operator_packets.csv | artifacts/data/vanderbilt_candidate_reviewer_decisions.csv | Use artifacts/data/vanderbilt_reviewer_decision_patch_workbook_slice_index.csv to choose one operator packet, slice it with scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py, fill only non-mutating decisions, extract strict patch rows with scripts/extract_vanderbilt_reviewer_decision_patch.py, dry-run scripts/apply_vanderbilt_reviewer_decision_patch.py, then apply and rerun the decision audit, batch-packet materializer, operator-packet materializer, workbook materializer, and slice-index materializer. |
| 3 | vanderbilt_active_gap_manifest_triage | ready_for_prioritized_reviewer_slice_input | 760 | 159 | artifacts/data/vanderbilt_reviewer_blank_execution_verification.csv | artifacts/data/vanderbilt_reviewer_slice_prioritization_plan.csv | Use artifacts/data/vanderbilt_reviewer_slice_prioritization_plan.csv and start with priority_rank=1. Slice execution_order=4 to /tmp, fill only allowed non-mutating reviewer decisions, extract a strict patch, dry-run apply, and do not run --apply until that slice is reviewed. |
| 4 | future_exact_approval_packet_after_valid_decisions | blocked_until_valid_non_mutating_decisions | 640 | 159 | artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json | artifacts/data/vanderbilt_candidate_acceptance_or_closure_approval_packet.csv | Do not build person-ingestion, denominator-closure, parser-acceptance, scope-closure, or identity-collapse packets until reviewer decisions are present and the decision audit passes. |
