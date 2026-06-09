---
type: research-checkpoint
title: Vanderbilt Reviewer Execution Readiness Bridge
created_at: 2026-06-09T08:38:52.722329+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Reviewer Execution Readiness Bridge

## Boundary

Non-mutating bridge from Vanderbilt pending review queues to bounded reviewer execution commands. It verifies that each review-queue bridge program is represented by /tmp-only slice, extraction, dry-run, and explicit apply commands from the public slice index. It does not run commands, fill reviewer decisions, apply patches, accept people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, publish raw candidate labels or URLs, or collapse identities.

## Summary

```json
{
  "apply_commands_present": true,
  "bridge_rows": 19,
  "csv": "artifacts/data/vanderbilt_reviewer_execution_readiness_bridge.csv",
  "denominator_closure_allowed": false,
  "extract_commands_present": true,
  "generated_at": "2026-06-09T08:38:52.722329+00:00",
  "identity_collapse_allowed": false,
  "invalid_decision_rows_represented": 0,
  "json": "artifacts/data/vanderbilt_reviewer_execution_readiness_bridge.json",
  "markdown": "artifacts/research/vanderbilt-reviewer-execution-readiness-bridge-2026-06-09.md",
  "mutation_allowed": false,
  "not_ready_program_rows": 0,
  "patch_dry_run_commands_present": true,
  "patch_output_paths_tmp_only": true,
  "pending_decision_rows_represented": 159,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating bridge from Vanderbilt pending review queues to bounded reviewer execution commands. It verifies that each review-queue bridge program is represented by /tmp-only slice, extraction, dry-run, and explicit apply commands from the public slice index. It does not run commands, fill reviewer decisions, apply patches, accept people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, publish raw candidate labels or URLs, or collapse identities.",
  "ready_program_rows": 19,
  "review_queue_rows_represented": 159,
  "rowset_sha256": "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa",
  "school_verification_allowed": false,
  "slice_index_rows_represented": 20,
  "slice_output_paths_tmp_only": true,
  "source_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_operator_packet_rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
  "source_review_queue_bridge_rowset_sha256": "46c2b215f28819df10913fa35f7dff6e7f4afc4ec6c3598e7432088c3f34e10d",
  "source_slice_index_rowset_sha256": "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4",
  "source_workbook_rowset_sha256": "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3",
  "url_rewrite_allowed": false,
  "valid_non_mutating_decision_rows_represented": 0,
  "workbook_rows_represented": 159
}
```

## Program Readiness

| program | status | slices | workbook rows | pending decisions | next action |
| --- | --- | ---: | ---: | ---: | --- |
| Academic General Pediatrics | ready_for_bounded_reviewer_slice_execution | 1 | 4 | 4 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Advanced Endoscopy | ready_for_bounded_reviewer_slice_execution | 1 | 1 | 1 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Advanced Inflammatory Bowel Disease | ready_for_bounded_reviewer_slice_execution | 1 | 1 | 1 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Developmental-Behavioral Pediatrics | ready_for_bounded_reviewer_slice_execution | 1 | 4 | 4 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Gastroenterology | ready_for_bounded_reviewer_slice_execution | 1 | 10 | 10 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| General Surgery | ready_for_bounded_reviewer_slice_execution | 1 | 2 | 2 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Neonatal-Perinatal Medicine | ready_for_bounded_reviewer_slice_execution | 1 | 19 | 19 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Orthopaedic Surgery | ready_for_bounded_reviewer_slice_execution | 2 | 2 | 2 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Pediatric Critical Care | ready_for_bounded_reviewer_slice_execution | 1 | 17 | 17 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Pediatric Emergency Medicine | ready_for_bounded_reviewer_slice_execution | 1 | 17 | 17 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Pediatric Endocrinology | ready_for_bounded_reviewer_slice_execution | 1 | 3 | 3 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Pediatric Gastroenterology | ready_for_bounded_reviewer_slice_execution | 1 | 12 | 12 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Pediatric Hospital Medicine | ready_for_bounded_reviewer_slice_execution | 1 | 4 | 4 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Pediatric Infectious Diseases | ready_for_bounded_reviewer_slice_execution | 1 | 10 | 10 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Pediatric Rheumatology | ready_for_bounded_reviewer_slice_execution | 1 | 4 | 4 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Pediatrics | ready_for_bounded_reviewer_slice_execution | 1 | 26 | 26 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Psychiatry | ready_for_bounded_reviewer_slice_execution | 1 | 9 | 9 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Rheumatology | ready_for_bounded_reviewer_slice_execution | 1 | 4 | 4 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
| Transplant Hepatology | ready_for_bounded_reviewer_slice_execution | 1 | 10 | 10 | choose_one_tmp_slice_command_fill_non_mutating_patch_extract_and_dry_run |
