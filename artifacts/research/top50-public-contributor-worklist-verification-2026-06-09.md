---
type: research-checkpoint
title: Top50 Public Contributor Worklist Verification
created_at: 2026-06-09T07:53:40.316769+00:00
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
  "generated_at": "2026-06-09T07:53:40.316769+00:00",
  "json": "artifacts/data/top50_public_contributor_worklist_verification.json",
  "markdown": "artifacts/research/top50-public-contributor-worklist-verification-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 12,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating verification for the public top-50 contributor worklist. It checks committed worklist rowsets, commands, source artifacts, prohibition gates, and public-safety leakage. It does not execute contributor work, ingest people, mutate training states, close denominators, verify schools, rewrite URLs, accept profile/contact/research facts, publish raw dumps, or collapse identities.",
  "rowset_sha256": "b604a1e2df4bef6058742edf826445e4b6a8b00948893ffd66b637f6d4f4680f",
  "school_verification_allowed": false,
  "source_worklist_rowset_sha256": "6cb94e73553eba3879c904983ba53e9ae666284a41e90009f13fe2c5e9814f15",
  "source_worklist_summary": "artifacts/data/top50_public_contributor_worklist_summary.json",
  "verification_rows": 12
}
```

## Checks

| check | status | observed |
| --- | --- | --- |
| worklist_summary_boundary | pass | `{"mutation_allowed":false,"rowset_sha256":"6cb94e73553eba3879c904983ba53e9ae666284a41e90009f13fe2c5e9814f15","total_impact_count":460,"worklist_rows":4}` |
| worklist_csv_json_counts_match | pass | `{"csv_rows":4,"json_rows":4,"summary_rows":4}` |
| worklist_lane_order | pass | `["verify_public_clone_substrate","vanderbilt_bounded_manual_review_packets","vanderbilt_active_gap_manifest_triage","future_exact_approval_packet_after_valid_decisions"]` |
| worklist_status_distribution | pass | `{"blocked_until_valid_non_mutating_decisions":1,"ready_and_passing":1,"ready_for_non_mutating_parser_scope_bridge":1,"ready_for_non_mutating_reviewer_input":1}` |
| worklist_artifact_paths_resolve | pass | `{"sources":{"artifacts/data/school_gap_resolution_batch_packets.csv":true,"artifacts/data/top50_public_clone_verification_summary.json":true,"artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json":true,"artifacts/data/vanderbilt_public_reviewer_operator_packets.csv":true},"targets":{"artifacts/data/school_gap_resolution_parser_scope_bridge.csv":"exists","artifacts/data/top50_public_clone_verification_summary.json":"exists","artifacts/data/vanderbilt_candidate_acceptance_or_closure_approval_packet.csv":"future_allowed","artifacts/data/vanderbilt_candidate_reviewer_decisions.csv":"exists"}}` |
| worklist_verification_commands_allowed | pass | `["python3 scripts/materialize_school_gap_resolution_review_template.py && python3 scripts/materialize_school_gap_resolution_targeted_review_packet.py && python3 scripts/materialize_school_gap_resolution_parser_scope_bridge.py && python3 scripts/validate_school_gap_resolution_review_template.py --input artifacts/data/school_gap_resolution_targeted_review_packet.csv --summary artifacts/data/school_gap_resolution_targeted_review_packet_validation_summary.json && python3 scripts/validate_school_gap_resolution_review_template.py && python3 scripts/materialize_top50_public_clone_verification.py && python3 scripts/assert_gap_manifest_fails_closed.py","python3 scripts/materialize_top50_public_clone_verification.py","python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py","python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py && python3 scripts/materialize_vanderbilt_candidate_review_batch_packets.py && python3 scripts/materialize_vanderbilt_public_reviewer_operator_packets.py && python3 scripts/materialize_top50_public_clone_verification.py"]` |
| worklist_prohibition_gates_present | pass | `{}` |
| worklist_approval_gates_present | pass | `{"future_exact_approval_packet_after_valid_decisions":"person_ingestion; denominator_closure; parser_acceptance; scope_closure; identity_collapse","vanderbilt_active_gap_manifest_triage":"denominator_closure; vanderbilt_school_verification; person_ingestion; url_rewrite; identity_collapse","vanderbilt_bounded_manual_review_packets":"accepted_person_rows; person_ingestion; denominator_closure; identity_reconciliation; parser_acceptance; scope_closure"}` |
| worklist_source_rowsets_match | pass | `{"future_exact_approval_packet_after_valid_decisions":"e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de","vanderbilt_active_gap_manifest_triage":"d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607","vanderbilt_bounded_manual_review_packets":"6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173","verify_public_clone_substrate":"2956b5dd01cd3ad97c398fc04ec8ac6f16e530b91a45d186be8f1f096c0727de"}` |
| worklist_target_rowsets_match | pass | `{"future_exact_approval_packet_after_valid_decisions":"","vanderbilt_active_gap_manifest_triage":"942d131072d56524c9e19832c084b9e2520e43e783e3a9c0c6e2ae30c0f06912","vanderbilt_bounded_manual_review_packets":"e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de","verify_public_clone_substrate":"2956b5dd01cd3ad97c398fc04ec8ac6f16e530b91a45d186be8f1f096c0727de"}` |
| worklist_public_leak_scan | pass | `[]` |
| gbrain_worklist_verification_lane_approved | pass | `"APPROVE top50_public_contributor_worklist_verification_lane_approved"` |
