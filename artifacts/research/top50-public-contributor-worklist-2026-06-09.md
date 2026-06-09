---
type: research-checkpoint
title: Top50 Public Contributor Worklist
created_at: 2026-06-09T11:27:20.190881+00:00
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
    "vanderbilt_open_gap_manifest_triage_packet": 1,
    "vanderbilt_slice_2_approved_parser_scope_next_packets": 1,
    "vanderbilt_slice_2_execution_plan_packet": 1,
    "vanderbilt_slice_2_followup_packet_set": 1,
    "vanderbilt_slice_2_live_fetch_approval_request_packet": 1,
    "vanderbilt_slice_2_live_route_observation_packet": 1,
    "vanderbilt_slice_2_route_parser_scope_approval_packet": 1,
    "verify_public_clone_substrate": 1
  },
  "by_action_status": {
    "approved_and_route_observations_materialized": 1,
    "approved_next_packet_ledger_materialized": 1,
    "blocked_until_valid_non_mutating_decisions": 1,
    "followup_packet_set_materialized": 1,
    "parser_scope_approval_request_materialized": 1,
    "ready_and_passing": 1,
    "ready_for_exact_followup_packet_approval_request": 1,
    "ready_for_local_reviewer_handoff_execution": 1,
    "ready_for_no_fetch_execution_planning": 1,
    "ready_for_non_mutating_gap_slice_execution": 1,
    "ready_for_non_mutating_reviewer_input": 1
  },
  "critical_rows": 2,
  "csv": "artifacts/data/top50_public_contributor_worklist.csv",
  "denominator_closure_allowed": false,
  "gbrain_approval_line": "APPROVE top50_public_contributor_worklist_lane_approved",
  "gbrain_approval_status": "approved_non_mutating_public_contributor_worklist_lane",
  "generated_at": "2026-06-09T11:27:20.190881+00:00",
  "high_rows": 8,
  "json": "artifacts/data/top50_public_contributor_worklist.json",
  "low_rows": 0,
  "markdown": "artifacts/research/top50-public-contributor-worklist-2026-06-09.md",
  "medium_rows": 1,
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating public contributor worklist for the top-50/Vanderbilt engine. It ranks bounded public-safe operator actions from committed verification, snapshot, Vanderbilt batch-packet, decision-audit, and gap manifest artifacts. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "rowset_sha256": "76b85a5939c2899334fe6372b895dbf1198b208a88dcedf33027064d8fb52d31",
  "school_verification_allowed": false,
  "source_snapshot_rowset_sha256": "b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48",
  "source_vanderbilt_batch_packet_rowset_sha256": "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f",
  "source_vanderbilt_gap_candidate_output_bridge_rowset_sha256": "dfb141c1883d85fd6a8c7c0e015b939414788936eb13dbb04eecb9111ff5b843",
  "source_vanderbilt_gap_parser_scope_bridge_rowset_sha256": "942d131072d56524c9e19832c084b9e2520e43e783e3a9c0c6e2ae30c0f06912",
  "source_vanderbilt_gap_review_queue_bridge_rowset_sha256": "46c2b215f28819df10913fa35f7dff6e7f4afc4ec6c3598e7432088c3f34e10d",
  "source_vanderbilt_gap_review_template_rowset_sha256": "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782",
  "source_vanderbilt_gap_slice_index_rowset_sha256": "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75",
  "source_vanderbilt_gap_targeted_review_packet_rowset_sha256": "d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607",
  "source_vanderbilt_open_gap_manifest_triage_packet_rowset_sha256": "b89f2278c96c18c70403099be2b18542bb0f59a4c50a53921f17fe83864b1391",
  "source_vanderbilt_operator_packet_rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
  "source_vanderbilt_patch_helper_fixture_verification_rowset_sha256": "9d87181804d6ade23ea3bd7fd322cdc7fdeab7b3078aade0921c8d2b2cab2825",
  "source_vanderbilt_patch_slice_index_rowset_sha256": "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4",
  "source_vanderbilt_patch_template_rowset_sha256": "5532d007555997f54d25884baba2f4e594d4ff1fa286301bfa6f87fc64caaa8d",
  "source_vanderbilt_patch_workbook_rowset_sha256": "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3",
  "source_vanderbilt_priority_reviewer_handoff_packet_rowset_sha256": "9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0",
  "source_vanderbilt_priority_reviewer_instruction_packet_rowset_sha256": "dfe6c7081ac7c3c28ac6e8afcb736a2d16bc8a6cbd8cba1cbc38b420064ddd65",
  "source_vanderbilt_reviewer_blank_execution_verification_rowset_sha256": "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e",
  "source_vanderbilt_reviewer_execution_readiness_bridge_rowset_sha256": "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa",
  "source_vanderbilt_reviewer_slice_prioritization_plan_rowset_sha256": "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c",
  "source_vanderbilt_slice_2_execution_plan_rowset_sha256": "c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b",
  "source_vanderbilt_slice_2_live_fetch_approval_request_rowset_sha256": "98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d",
  "source_vanderbilt_slice_2_live_route_observation_rowset_sha256": "c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0",
  "source_vanderbilt_slice_2_route_parser_scope_approval_rowset_sha256": "bb0c69694a411c386964d1b7ae523a65a31452e5d62db227d4469044bd109672",
  "source_vanderbilt_synthetic_handoff_dry_run_demo_rowset_sha256": "81da7a86173eef52ee6fbc4afdf98ab3f33555b6d83f6c61be88bad61a211bb4",
  "source_vanderbilt_triage_slice_definition_contract_rowset_sha256": "b8559206ae9341dae7c9136ddb6d83651ff84905feb74ec133992e822534416f",
  "source_verification_rowset_sha256": "a93dbbaef2ae1ad30906102091611e0b6f6912ef79674815debbb1e4461a2f0f",
  "total_impact_count": 576,
  "worklist_rows": 11
}
```

## Work Items

| order | lane | status | priority | impact | source | target | next action |
| ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | verify_public_clone_substrate | ready_and_passing | 980 | 53 | artifacts/data/top50_public_clone_verification_summary.json | artifacts/data/top50_public_clone_verification_summary.json | Run python3 scripts/materialize_top50_public_substrate_check_contract.py after any public top-50/Vanderbilt artifact change. |
| 2 | vanderbilt_bounded_manual_review_packets | ready_for_non_mutating_reviewer_input | 940 | 159 | artifacts/data/vanderbilt_public_reviewer_operator_packets.csv | artifacts/data/vanderbilt_candidate_reviewer_decisions.csv | Use artifacts/data/vanderbilt_reviewer_decision_patch_workbook_slice_index.csv to choose one operator packet, slice it with scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py, fill only non-mutating decisions, extract strict patch rows with scripts/extract_vanderbilt_reviewer_decision_patch.py, dry-run scripts/apply_vanderbilt_reviewer_decision_patch.py, then stop. Do not run --apply or commit filled decisions until a future exact approval packet exists. |
| 3 | vanderbilt_active_gap_manifest_triage | ready_for_local_reviewer_handoff_execution | 760 | 2 | artifacts/data/vanderbilt_priority_reviewer_handoff_packet.csv | artifacts/data/vanderbilt_candidate_reviewer_decisions.csv | Use artifacts/data/vanderbilt_priority_reviewer_handoff_packet.csv as the reviewer-facing runbook. Run its slice command locally, fill only the blank action/confirmation fields in the local workbook, extract a strict patch, dry-run apply, and do not run --apply until a future exact approval packet exists. |
| 4 | vanderbilt_open_gap_manifest_triage_packet | ready_for_non_mutating_gap_slice_execution | 880 | 113 | artifacts/data/vanderbilt_open_gap_manifest_triage_packet_summary.json | artifacts/data/vanderbilt_open_gap_manifest_triage_packet_summary.json | Use artifacts/data/vanderbilt_open_gap_manifest_triage_packet.csv to pick the next Vanderbilt open-gap slice beyond the General Surgery reviewer handoff; run only its /tmp slice command, then prepare non-mutating source-discovery or review evidence for a future exact packet. |
| 5 | vanderbilt_slice_2_execution_plan_packet | ready_for_no_fetch_execution_planning | 860 | 9 | artifacts/data/vanderbilt_slice_2_execution_plan_packet_summary.json | artifacts/data/vanderbilt_slice_2_execution_plan_packet_summary.json | Use artifacts/data/vanderbilt_slice_2_execution_plan_packet.csv to review the 9 execution-order-1 Vanderbilt gaps and decide the next exact non-mutating source-discovery packet; do not fetch web pages under this packet. |
| 6 | vanderbilt_slice_2_live_fetch_approval_request_packet | approved_and_route_observations_materialized | 850 | 9 | artifacts/data/vanderbilt_slice_2_execution_plan_packet_summary.json | artifacts/data/vanderbilt_slice_2_live_fetch_approval_request_packet_summary.json | Submit artifacts/data/vanderbilt_slice_2_live_fetch_approval_request_packet_summary.json for exact GBrain approval. If approved, the next implementation must fetch only bounded public route metadata and hashes, then commit a separate non-mutating route-observation packet. |
| 7 | vanderbilt_slice_2_live_route_observation_packet | parser_scope_approval_request_materialized | 845 | 18 | artifacts/data/vanderbilt_slice_2_live_route_observation_summary.json | artifacts/data/vanderbilt_slice_2_route_parser_scope_approval_packet_summary.json | Build a non-mutating Vanderbilt slice-2 route parser/scope approval-request packet from artifacts/data/vanderbilt_slice_2_live_route_observations.csv; do not parse or accept people. |
| 8 | vanderbilt_slice_2_route_parser_scope_approval_packet | approved_next_packet_ledger_materialized | 842 | 18 | artifacts/data/vanderbilt_slice_2_route_parser_scope_approval_packet_summary.json | artifacts/data/vanderbilt_slice_2_approved_parser_scope_next_packet_summary.json | Keep artifacts/data/vanderbilt_slice_2_approved_parser_scope_next_packet_summary.json as the approved lane boundary for the next bounded parser/scope follow-up packets. |
| 9 | vanderbilt_slice_2_approved_parser_scope_next_packets | followup_packet_set_materialized | 838 | 18 | artifacts/data/vanderbilt_slice_2_approved_parser_scope_next_packet_summary.json | artifacts/data/vanderbilt_slice_2_followup_packet_set_summary.json | Use artifacts/data/vanderbilt_slice_2_followup_packet_set_summary.json as the combined packet-set boundary for the next exact approval request; do not fetch, execute parsers, or accept people. |
| 10 | vanderbilt_slice_2_followup_packet_set | ready_for_exact_followup_packet_approval_request | 834 | 18 | artifacts/data/vanderbilt_slice_2_followup_packet_set_summary.json | artifacts/data/vanderbilt_slice_2_followup_packet_set_summary.json | Build an exact non-mutating approval-request packet from artifacts/data/vanderbilt_slice_2_followup_packet_set.csv before any parser execution, source fetching, scope acceptance, route replacement, person ingestion, or denominator closure. |
| 11 | future_exact_approval_packet_after_valid_decisions | blocked_until_valid_non_mutating_decisions | 640 | 159 | artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json | artifacts/data/vanderbilt_candidate_acceptance_or_closure_approval_packet.csv | Do not build person-ingestion, denominator-closure, parser-acceptance, scope-closure, or identity-collapse packets until reviewer decisions are present and the decision audit passes. |
