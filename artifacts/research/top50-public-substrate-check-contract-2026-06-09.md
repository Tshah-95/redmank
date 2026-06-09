---
type: research-checkpoint
title: Top50 Public Substrate Check Contract
created_at: 2026-06-09T09:55:07.001514+00:00
project: top-50-medical-school-roster-engine
---

# Top50 Public Substrate Check Contract

## Boundary

Aggregate non-mutating public substrate check contract for the top-50/Vanderbilt lane. It runs the committed synthetic handoff dry-run, priority handoff, public clone verification, contributor worklist, worklist verification, and gap-manifest fail-closed checks, then records their rowsets and pass counts. It does not fill reviewer decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "apply_executed": false,
  "contract_check_rows": 7,
  "csv": "artifacts/data/top50_public_substrate_check_contract.csv",
  "decision_audit_invalid_rows": 0,
  "decision_audit_pending_rows": 159,
  "decision_audit_valid_non_mutating_rows": 0,
  "denominator_closure_allowed": false,
  "fail_rows": 0,
  "gbrain_approval_line": "APPROVE top50_public_substrate_check_contract_non_mutating_increment",
  "gbrain_approval_status": "approved_non_mutating_top50_public_substrate_check_contract_increment",
  "generated_at": "2026-06-09T09:55:07.001514+00:00",
  "json": "artifacts/data/top50_public_substrate_check_contract.json",
  "markdown": "artifacts/research/top50-public-substrate-check-contract-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 7,
  "person_ingestion_allowed": false,
  "policy": "Aggregate non-mutating public substrate check contract for the top-50/Vanderbilt lane. It runs the committed synthetic handoff dry-run, priority handoff, public clone verification, contributor worklist, worklist verification, and gap-manifest fail-closed checks, then records their rowsets and pass counts. It does not fill reviewer decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.",
  "rowset_sha256": "6c2ae0046c5616dfd270cc6855c1758f6c947dcbfcf1984edbcb9c2212aaf8e1",
  "school_verification_allowed": false,
  "source_clone_verification_rowset_sha256": "da28ec6ac1e9a4df95c7f60c12fa9e6a8221ea639d50f27f86776ec194b871ba",
  "source_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_priority_handoff_rowset_sha256": "9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0",
  "source_synthetic_handoff_rowset_sha256": "81da7a86173eef52ee6fbc4afdf98ab3f33555b6d83f6c61be88bad61a211bb4",
  "source_worklist_rowset_sha256": "673714f62ed47e6d0826cb12de3542a9d5ff8acae16650ab646ff8c902a873c4",
  "source_worklist_verification_rowset_sha256": "045d521cc6215a7dad3e73badd04983f32bcdad336e1bf089316bbf0e6a27c75"
}
```

## Checks

| order | check | status | command |
| ---: | --- | --- | --- |
| 1 | synthetic_handoff_dry_run_demo | pass | `python3 scripts/materialize_vanderbilt_synthetic_handoff_dry_run_demo.py` |
| 2 | priority_reviewer_handoff_packet | pass | `python3 scripts/materialize_vanderbilt_priority_reviewer_handoff_packet.py` |
| 3 | public_clone_verification | pass | `python3 scripts/materialize_top50_public_clone_verification.py` |
| 4 | public_contributor_worklist | pass | `python3 scripts/materialize_top50_public_contributor_worklist.py` |
| 5 | public_contributor_worklist_verification | pass | `python3 scripts/materialize_top50_public_contributor_worklist_verification.py` |
| 6 | decision_audit_pending_boundary | pass | `python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py` |
| 7 | gap_manifest_fail_closed_assertion | pass | `python3 scripts/assert_gap_manifest_fails_closed.py` |
