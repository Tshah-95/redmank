---
type: research-checkpoint
title: Vanderbilt Reviewer Slice Prioritization Plan
created_at: 2026-06-09T09:00:54.658110+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Reviewer Slice Prioritization Plan

## Boundary

Non-mutating Vanderbilt reviewer slice prioritization plan. It ranks the 20 fail-closed reviewer slices using only public-safe lane, row-count, command-surface, and blank-execution verification metrics. It does not fill reviewer decisions, extract filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "apply_executed": false,
  "blank_execution_pass_rows_represented": 20,
  "by_assignment_band": {
    "first_pass_small_candidate_slice": 7,
    "large_candidate_slice": 4,
    "scope_or_recourse_micro_slice": 4,
    "standard_candidate_slice": 5
  },
  "by_review_queue_lane": {
    "candidate_fingerprint_review": 16,
    "linked_scope_metadata_review": 3,
    "route_recourse_review": 1
  },
  "csv": "artifacts/data/vanderbilt_reviewer_slice_prioritization_plan.csv",
  "denominator_closure_allowed": false,
  "dry_run_patch_rows_represented": 0,
  "first_priority_execution_order": "4",
  "first_priority_program_name": "General Surgery",
  "first_priority_workbook_row_count": 2,
  "gbrain_approval_line": "APPROVE vanderbilt_reviewer_slice_prioritization_plan_non_mutating_increment",
  "gbrain_approval_status": "approved_non_mutating_vanderbilt_reviewer_slice_prioritization_plan_increment",
  "generated_at": "2026-06-09T09:00:54.658110+00:00",
  "json": "artifacts/data/vanderbilt_reviewer_slice_prioritization_plan.json",
  "markdown": "artifacts/research/vanderbilt-reviewer-slice-prioritization-plan-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt reviewer slice prioritization plan. It ranks the 20 fail-closed reviewer slices using only public-safe lane, row-count, command-surface, and blank-execution verification metrics. It does not fill reviewer decisions, extract filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw candidate labels or person URLs, or collapse identities.",
  "prioritization_rows": 20,
  "ready_for_bounded_human_reviewer_input_rows": 20,
  "rowset_sha256": "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c",
  "school_verification_allowed": false,
  "slice_rows_represented": 159,
  "source_blank_execution_rowset_sha256": "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e",
  "source_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_execution_readiness_rowset_sha256": "ac16e7d92c4992c248162c05778abc4739a487aa01ffe8bc6dde21d6b372dafa",
  "source_slice_index_rowset_sha256": "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4"
}
```

## Priority Rows

| rank | order | band | lane | program | rows | status |
| ---: | ---: | --- | --- | --- | ---: | --- |
| 1 | 4 | first_pass_small_candidate_slice | candidate_fingerprint_review | General Surgery | 2 | ready_for_bounded_human_reviewer_input |
| 2 | 8 | first_pass_small_candidate_slice | candidate_fingerprint_review | Pediatric Endocrinology | 3 | ready_for_bounded_human_reviewer_input |
| 3 | 1 | first_pass_small_candidate_slice | candidate_fingerprint_review | Academic General Pediatrics | 4 | ready_for_bounded_human_reviewer_input |
| 4 | 2 | first_pass_small_candidate_slice | candidate_fingerprint_review | Developmental-Behavioral Pediatrics | 4 | ready_for_bounded_human_reviewer_input |
| 5 | 10 | first_pass_small_candidate_slice | candidate_fingerprint_review | Pediatric Hospital Medicine | 4 | ready_for_bounded_human_reviewer_input |
| 6 | 12 | first_pass_small_candidate_slice | candidate_fingerprint_review | Pediatric Rheumatology | 4 | ready_for_bounded_human_reviewer_input |
| 7 | 15 | first_pass_small_candidate_slice | candidate_fingerprint_review | Rheumatology | 4 | ready_for_bounded_human_reviewer_input |
| 8 | 17 | scope_or_recourse_micro_slice | linked_scope_metadata_review | Advanced Endoscopy | 1 | ready_for_bounded_human_reviewer_input |
| 9 | 18 | scope_or_recourse_micro_slice | linked_scope_metadata_review | Advanced Inflammatory Bowel Disease | 1 | ready_for_bounded_human_reviewer_input |
| 10 | 19 | scope_or_recourse_micro_slice | linked_scope_metadata_review | Orthopaedic Surgery | 1 | ready_for_bounded_human_reviewer_input |
| 11 | 20 | scope_or_recourse_micro_slice | route_recourse_review | Orthopaedic Surgery | 1 | ready_for_bounded_human_reviewer_input |
| 12 | 14 | standard_candidate_slice | candidate_fingerprint_review | Psychiatry | 9 | ready_for_bounded_human_reviewer_input |
| 13 | 3 | standard_candidate_slice | candidate_fingerprint_review | Gastroenterology | 10 | ready_for_bounded_human_reviewer_input |
| 14 | 11 | standard_candidate_slice | candidate_fingerprint_review | Pediatric Infectious Diseases | 10 | ready_for_bounded_human_reviewer_input |
| 15 | 16 | standard_candidate_slice | candidate_fingerprint_review | Transplant Hepatology | 10 | ready_for_bounded_human_reviewer_input |
| 16 | 9 | standard_candidate_slice | candidate_fingerprint_review | Pediatric Gastroenterology | 12 | ready_for_bounded_human_reviewer_input |
| 17 | 6 | large_candidate_slice | candidate_fingerprint_review | Pediatric Critical Care | 17 | ready_for_bounded_human_reviewer_input |
| 18 | 7 | large_candidate_slice | candidate_fingerprint_review | Pediatric Emergency Medicine | 17 | ready_for_bounded_human_reviewer_input |
| 19 | 5 | large_candidate_slice | candidate_fingerprint_review | Neonatal-Perinatal Medicine | 19 | ready_for_bounded_human_reviewer_input |
| 20 | 13 | large_candidate_slice | candidate_fingerprint_review | Pediatrics | 26 | ready_for_bounded_human_reviewer_input |
