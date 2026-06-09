---
type: research-checkpoint
title: Vanderbilt Patch Helper Fixture Verification
created_at: 2026-06-09T09:21:21.211100+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Patch Helper Fixture Verification

## Boundary

Synthetic-only Vanderbilt patch-helper fixture verification. It imports helper functions and exercises fabricated keys, fingerprints, workbook rows, patch rows, and confirmation fields in memory. It writes only verification artifacts and does not read or write real reviewer decisions, extract real filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "apply_executed": false,
  "csv": "artifacts/data/vanderbilt_patch_helper_fixture_verification.csv",
  "denominator_closure_allowed": false,
  "fail_rows": 0,
  "fixture_check_rows": 16,
  "gbrain_approval_line": "APPROVE vanderbilt_patch_helper_fixture_verification_non_mutating_increment",
  "gbrain_approval_status": "approved_non_mutating_vanderbilt_patch_helper_fixture_verification_increment",
  "generated_at": "2026-06-09T09:21:21.211100+00:00",
  "json": "artifacts/data/vanderbilt_patch_helper_fixture_verification.json",
  "markdown": "artifacts/research/vanderbilt-patch-helper-fixture-verification-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 16,
  "person_ingestion_allowed": false,
  "policy": "Synthetic-only Vanderbilt patch-helper fixture verification. It imports helper functions and exercises fabricated keys, fingerprints, workbook rows, patch rows, and confirmation fields in memory. It writes only verification artifacts and does not read or write real reviewer decisions, extract real filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.",
  "real_vanderbilt_rows_used": 0,
  "rowset_sha256": "9d87181804d6ade23ea3bd7fd322cdc7fdeab7b3078aade0921c8d2b2cab2825",
  "school_verification_allowed": false,
  "synthetic_fixture_only": true
}
```

## Checks

| order | surface | check | status | observed |
| ---: | --- | --- | --- | --- |
| 1 | patch_header | valid header accepted | pass | success |
| 2 | patch_header | missing patch column rejected | pass | Patch is missing required columns: confirm_recourse_only |
| 3 | patch_header | extra patch column rejected | pass | Patch contains unsupported columns: unsupported_fixture_column |
| 4 | patch_rows | valid non-mutating synthetic patch accepted | pass | success |
| 5 | patch_rows | unsupported action rejected | pass | Patch row is not a valid non-mutating decision for fixture_manual_decision_row_alpha: reviewer_action_not_allowed |
| 6 | patch_rows | stale fingerprint rejected | pass | Patch row is not a valid non-mutating decision for fixture_manual_decision_row_alpha: decision_fingerprint_confirmation_missing_or_mismatched |
| 7 | patch_rows | irrelevant lane confirmation rejected | pass | Patch sets confirmation fields outside this row's lane for fixture_manual_decision_row_alpha: confirm_scope_metadata_only |
| 8 | patch_rows | duplicate patch key rejected | pass | Patch contains duplicate manual_decision_row_key: fixture_manual_decision_row_alpha |
| 9 | workbook_header | valid workbook header accepted | pass | success |
| 10 | workbook_header | extra workbook column rejected | pass | Workbook contains unsupported columns: unsupported_fixture_column |
| 11 | workbook_context | blank synthetic workbook row accepted | pass | success |
| 12 | workbook_context | partial blank action rejected | pass | Workbook row has confirmations without reviewer_action: fixture_manual_decision_row_alpha |
| 13 | workbook_context | stale workbook fingerprint rejected | pass | Workbook decision_fingerprint is stale for: fixture_manual_decision_row_alpha |
| 14 | patch_extraction | blank workbook extracts zero filled patch rows | pass | extracted_rows=0 |
| 15 | patch_extraction | filled synthetic workbook extracts valid patch row | pass | success; extracted_rows=1 |
| 16 | patch_extraction | include_blank preserves blank patch shape | pass | extracted_rows=1 |
