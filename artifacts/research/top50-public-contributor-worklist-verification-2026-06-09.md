---
type: research-checkpoint
title: Top50 Public Contributor Worklist Verification
created_at: 2026-06-09T09:55:07.441383+00:00
project: top-50-medical-school-roster-engine
---

# Top50 Public Contributor Worklist Verification

## Boundary

Non-mutating verification for the public top-50 contributor worklist. It checks committed worklist rowsets, commands, source artifacts, prohibition gates, and public-safety leakage. It does not execute contributor work, ingest people, mutate training states, close denominators, verify schools, rewrite URLs, accept profile/contact/research facts, publish raw dumps, or collapse identities.

## Summary

```json
{
  "csv": "artifacts/data/top50_public_contributor_worklist_verification.csv",
  "denominator_closure_allowed": false,
  "fail_rows": 0,
  "gbrain_approval_line": "APPROVE top50_public_contributor_worklist_verification_lane_approved",
  "gbrain_approval_status": "approved_non_mutating_public_contributor_worklist_verification_lane",
  "generated_at": "2026-06-09T09:55:07.441383+00:00",
  "json": "artifacts/data/top50_public_contributor_worklist_verification.json",
  "markdown": "artifacts/research/top50-public-contributor-worklist-verification-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 12,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating verification for the public top-50 contributor worklist. It checks committed worklist rowsets, commands, source artifacts, prohibition gates, and public-safety leakage. It does not execute contributor work, ingest people, mutate training states, close denominators, verify schools, rewrite URLs, accept profile/contact/research facts, publish raw dumps, or collapse identities.",
  "rowset_sha256": "045d521cc6215a7dad3e73badd04983f32bcdad336e1bf089316bbf0e6a27c75",
  "school_verification_allowed": false,
  "source_worklist_rowset_sha256": "673714f62ed47e6d0826cb12de3542a9d5ff8acae16650ab646ff8c902a873c4",
  "source_worklist_summary": "artifacts/data/top50_public_contributor_worklist_summary.json",
  "verification_rows": 12
}
```

## Checks

| check | status | observed |
| --- | --- | --- |
| worklist_summary_boundary | pass | `{"mutation_allowed":false,"rowset_sha256":"673714f62ed47e6d0826cb12de3542a9d5ff8acae16650ab646ff8c902a873c4","total_impact_count":365,"worklist_rows":4}` |
| worklist_csv_json_counts_match | pass | `{"csv_rows":4,"json_rows":4,"summary_rows":4}` |
| worklist_lane_order | pass | `["verify_public_clone_substrate","vanderbilt_bounded_manual_review_packets","vanderbilt_active_gap_manifest_triage","future_exact_approval_packet_after_valid_decisions"]` |
| worklist_status_distribution | pass | `{"blocked_until_valid_non_mutating_decisions":1,"ready_and_passing":1,"ready_for_local_reviewer_handoff_execution":1,"ready_for_non_mutating_reviewer_input":1}` |
| worklist_artifact_paths_resolve | pass | `{"sources":{"artifacts/data/top50_public_clone_verification_summary.json":true,"artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json":true,"artifacts/data/vanderbilt_priority_reviewer_handoff_packet.csv":true,"artifacts/data/vanderbilt_public_reviewer_operator_packets.csv":true},"targets":{"artifacts/data/top50_public_clone_verification_summary.json":"exists","artifacts/data/vanderbilt_candidate_acceptance_or_closure_approval_packet.csv":"future_allowed","artifacts/data/vanderbilt_candidate_reviewer_decisions.csv":"exists"}}` |
| worklist_verification_commands_allowed | pass | `["python3 scripts/materialize_top50_public_substrate_check_contract.py","python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py","python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py && python3 scripts/materialize_vanderbilt_candidate_review_batch_packets.py && python3 scripts/materialize_vanderbilt_public_reviewer_operator_packets.py && python3 scripts/materialize_top50_public_clone_verification.py","python3 scripts/materialize_vanderbilt_patch_helper_fixture_verification.py && python3 scripts/materialize_vanderbilt_priority_reviewer_instruction_packet.py && python3 scripts/materialize_vanderbilt_priority_reviewer_handoff_packet.py && python3 scripts/materialize_vanderbilt_synthetic_handoff_dry_run_demo.py && python3 scripts/materialize_top50_public_clone_verification.py && python3 scripts/assert_gap_manifest_fails_closed.py"]` |
| worklist_prohibition_gates_present | pass | `{}` |
| worklist_approval_gates_present | pass | `{"future_exact_approval_packet_after_valid_decisions":"person_ingestion; denominator_closure; parser_acceptance; scope_closure; identity_collapse","vanderbilt_active_gap_manifest_triage":"filled_reviewer_decision_commit; patch_apply; denominator_closure; vanderbilt_school_verification; person_ingestion; url_rewrite; identity_collapse","vanderbilt_bounded_manual_review_packets":"accepted_person_rows; person_ingestion; denominator_closure; identity_reconciliation; parser_acceptance; scope_closure"}` |
| worklist_source_rowsets_match | pass | `{"future_exact_approval_packet_after_valid_decisions":"e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de","vanderbilt_active_gap_manifest_triage":"9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0","vanderbilt_bounded_manual_review_packets":"6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173","verify_public_clone_substrate":"da28ec6ac1e9a4df95c7f60c12fa9e6a8221ea639d50f27f86776ec194b871ba"}` |
| worklist_target_rowsets_match | pass | `{"future_exact_approval_packet_after_valid_decisions":"","vanderbilt_active_gap_manifest_triage":"e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de","vanderbilt_bounded_manual_review_packets":"e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de","verify_public_clone_substrate":"da28ec6ac1e9a4df95c7f60c12fa9e6a8221ea639d50f27f86776ec194b871ba"}` |
| worklist_public_leak_scan | pass | `[]` |
| gbrain_worklist_verification_lane_approved | pass | `"APPROVE top50_public_contributor_worklist_verification_lane_approved"` |
