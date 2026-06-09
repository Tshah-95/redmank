---
type: research-checkpoint
title: Top50 Public Substrate Check Contract
created_at: 2026-06-09T10:09:08.161055+00:00
project: top-50-medical-school-roster-engine
---

# Top50 Public Substrate Check Contract

## Boundary

Aggregate non-mutating public substrate check contract for the top-50/Vanderbilt lane. It runs the committed synthetic handoff dry-run, priority handoff, open-gap triage, public clone verification, contributor worklist, worklist verification, and gap-manifest fail-closed checks, then records their rowsets and pass counts. It does not fill reviewer decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "apply_executed": false,
  "contract_check_rows": 9,
  "csv": "artifacts/data/top50_public_substrate_check_contract.csv",
  "decision_audit_invalid_rows": 0,
  "decision_audit_pending_rows": 159,
  "decision_audit_valid_non_mutating_rows": 0,
  "denominator_closure_allowed": false,
  "fail_rows": 0,
  "gbrain_approval_line": "APPROVE top50_public_substrate_check_contract_non_mutating_increment",
  "gbrain_approval_status": "approved_non_mutating_top50_public_substrate_check_contract_increment",
  "generated_at": "2026-06-09T10:09:08.161055+00:00",
  "json": "artifacts/data/top50_public_substrate_check_contract.json",
  "markdown": "artifacts/research/top50-public-substrate-check-contract-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 9,
  "person_ingestion_allowed": false,
  "policy": "Aggregate non-mutating public substrate check contract for the top-50/Vanderbilt lane. It runs the committed synthetic handoff dry-run, priority handoff, open-gap triage, public clone verification, contributor worklist, worklist verification, and gap-manifest fail-closed checks, then records their rowsets and pass counts. It does not fill reviewer decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.",
  "rowset_sha256": "ab69ee5d4e5d57a3f8583b8cfecda9ee31b61fefcbbf743ef5c9e26cc03c97ce",
  "school_verification_allowed": false,
  "source_clone_verification_rowset_sha256": "3769d2294e7d3682257fd4df8f4484aea699bb757ef4ba510c1262d1039cbeaa",
  "source_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_open_gap_triage_rowset_sha256": "b89f2278c96c18c70403099be2b18542bb0f59a4c50a53921f17fe83864b1391",
  "source_priority_handoff_rowset_sha256": "9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0",
  "source_synthetic_handoff_rowset_sha256": "81da7a86173eef52ee6fbc4afdf98ab3f33555b6d83f6c61be88bad61a211bb4",
  "source_triage_contract_rowset_sha256": "b8559206ae9341dae7c9136ddb6d83651ff84905feb74ec133992e822534416f",
  "source_worklist_rowset_sha256": "2908c35a7730cb55bd2305943a305a97995d483c8b26ca8c68b39e4bab3b14ea",
  "source_worklist_verification_rowset_sha256": "606e729b15ae4de6db830326b8e5a885a15b1dc0f3f018df7ebf2d0a8f99f59d"
}
```

## Checks

| order | check | status | command |
| ---: | --- | --- | --- |
| 1 | synthetic_handoff_dry_run_demo | pass | `python3 scripts/materialize_vanderbilt_synthetic_handoff_dry_run_demo.py` |
| 2 | priority_reviewer_handoff_packet | pass | `python3 scripts/materialize_vanderbilt_priority_reviewer_handoff_packet.py` |
| 3 | open_gap_manifest_triage_packet | pass | `python3 scripts/materialize_vanderbilt_open_gap_manifest_triage_packet.py` |
| 4 | triage_slice_definition_contract | pass | `python3 scripts/materialize_vanderbilt_open_gap_manifest_triage_packet.py` |
| 5 | public_clone_verification | pass | `python3 scripts/materialize_top50_public_clone_verification.py` |
| 6 | public_contributor_worklist | pass | `python3 scripts/materialize_top50_public_contributor_worklist.py` |
| 7 | public_contributor_worklist_verification | pass | `python3 scripts/materialize_top50_public_contributor_worklist_verification.py` |
| 8 | decision_audit_pending_boundary | pass | `python3 scripts/materialize_vanderbilt_candidate_reviewer_decision_audit.py` |
| 9 | gap_manifest_fail_closed_assertion | pass | `python3 scripts/assert_gap_manifest_fails_closed.py` |
