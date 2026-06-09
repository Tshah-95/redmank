---
type: research-checkpoint
title: Vanderbilt Synthetic Handoff Dry Run Demo
created_at: 2026-06-09T11:13:10.720725+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Synthetic Handoff Dry Run Demo

## Boundary

Synthetic-only Vanderbilt handoff dry-run demonstration. It writes fabricated scaffold, decision, and workbook rows under /tmp, runs the public slice, extract, and dry-run patch helper commands against those fabricated inputs, then removes the temporary tree. It does not read or write real Vanderbilt reviewer decisions, fill real decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "apply_executed": false,
  "csv": "artifacts/data/vanderbilt_synthetic_handoff_dry_run_demo.csv",
  "demo_check_rows": 5,
  "denominator_closure_allowed": false,
  "dry_run_outputs_written": 0,
  "dry_run_patch_rows": 1,
  "extracted_patch_rows": 1,
  "fail_rows": 0,
  "gbrain_approval_line": "APPROVE vanderbilt_synthetic_handoff_dry_run_demo_non_mutating_increment",
  "gbrain_approval_status": "approved_non_mutating_vanderbilt_synthetic_handoff_dry_run_demo_increment",
  "generated_at": "2026-06-09T11:13:10.720725+00:00",
  "json": "artifacts/data/vanderbilt_synthetic_handoff_dry_run_demo.json",
  "markdown": "artifacts/research/vanderbilt-synthetic-handoff-dry-run-demo-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 5,
  "person_ingestion_allowed": false,
  "policy": "Synthetic-only Vanderbilt handoff dry-run demonstration. It writes fabricated scaffold, decision, and workbook rows under /tmp, runs the public slice, extract, and dry-run patch helper commands against those fabricated inputs, then removes the temporary tree. It does not read or write real Vanderbilt reviewer decisions, fill real decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.",
  "real_vanderbilt_rows_used": 0,
  "rowset_sha256": "81da7a86173eef52ee6fbc4afdf98ab3f33555b6d83f6c61be88bad61a211bb4",
  "school_verification_allowed": false,
  "slice_rows": 2,
  "synthetic_fixture_only": true,
  "synthetic_input_rows_written": 6,
  "tmp_dir": "/tmp/redmank_vanderbilt_synthetic_handoff_dry_run_demo",
  "tmp_outputs_removed": true,
  "valid_non_mutating_rows": 1
}
```

## Checks

| order | surface | check | status | observed |
| ---: | --- | --- | --- | --- |
| 1 | synthetic_inputs | fabricated tmp inputs written | pass | scaffold_rows=2; decision_rows=2; workbook_rows=2 |
| 2 | slice_command | synthetic handoff slice command writes two rows | pass | exit=0; slice_rows=2; stderr= |
| 3 | extract_command | synthetic extract command emits one filled patch row | pass | exit=0; extracted_patch_rows=1; stderr= |
| 4 | dry_run_command | synthetic dry-run validates patch without writing outputs | pass | exit=0; patch_rows=1; valid_non_mutating_rows=1; outputs_absent=True; stderr= |
| 5 | cleanup | synthetic tmp tree removed | pass | tmp_outputs_removed=true |
