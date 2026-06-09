---
type: research-checkpoint
title: Vanderbilt Priority Reviewer Handoff Packet
created_at: 2026-06-09T09:55:07.141213+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Priority Reviewer Handoff Packet

## Boundary

Non-mutating Vanderbilt priority reviewer handoff packet. It bundles the General Surgery priority_rank=1 instruction packet, synthetic patch-helper fixture status, slice command, extract command, dry-run command, and explicit no-apply boundary for local reviewer execution. It does not fill reviewer decisions, extract filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, publish raw candidate labels or person URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "apply_command_allowed": false,
  "apply_executed": false,
  "blank_execution_pass_rows": 20,
  "blank_extract_fail_closed_rows": 20,
  "candidate_source_kind_counts": {
    "heading_signal": 1,
    "profile_anchor": 1
  },
  "csv": "artifacts/data/vanderbilt_priority_reviewer_handoff_packet.csv",
  "decision_audit_invalid_rows": 0,
  "decision_audit_pending_rows": 159,
  "decision_audit_valid_non_mutating_rows": 0,
  "denominator_closure_allowed": false,
  "execution_order": "4",
  "extract_command_present": true,
  "fixture_check_rows": 16,
  "fixture_fail_rows": 0,
  "fixture_pass_rows": 16,
  "free_text_note_column_committed": false,
  "gbrain_approval_line": "APPROVE vanderbilt_priority_reviewer_handoff_packet_non_mutating_increment",
  "gbrain_approval_status": "approved_non_mutating_vanderbilt_priority_reviewer_handoff_packet_increment",
  "generated_at": "2026-06-09T09:55:07.141213+00:00",
  "handoff_rows": 1,
  "handoff_status": "ready_for_local_reviewer_handoff_execution",
  "instruction_rows_represented": 2,
  "json": "artifacts/data/vanderbilt_priority_reviewer_handoff_packet.json",
  "markdown": "artifacts/research/vanderbilt-priority-reviewer-handoff-packet-2026-06-09.md",
  "mutation_allowed": false,
  "parser_acceptance_allowed": false,
  "patch_dry_run_command_present": true,
  "pending_blank_instruction_rows": 2,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt priority reviewer handoff packet. It bundles the General Surgery priority_rank=1 instruction packet, synthetic patch-helper fixture status, slice command, extract command, dry-run command, and explicit no-apply boundary for local reviewer execution. It does not fill reviewer decisions, extract filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, publish raw candidate labels or person URLs, accept enrichment facts, or collapse identities.",
  "priority_rank": "1",
  "program_name": "General Surgery",
  "raw_candidate_names_committed": false,
  "raw_person_urls_committed": false,
  "review_queue_lane": "candidate_fingerprint_review",
  "rowset_sha256": "9ec4ad8a9117ff2b48e6e67b1044b0d59e2d1fe367f381bb4ac3c8b7fc39b8b0",
  "school_verification_allowed": false,
  "slice_command_present": true,
  "source_blank_execution_verification_rowset_sha256": "8214eb3162fd6c56206c6c937b78fcd0ee485e5cdb6ca681737f8a64a378f02e",
  "source_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_patch_helper_fixture_rowset_sha256": "9d87181804d6ade23ea3bd7fd322cdc7fdeab7b3078aade0921c8d2b2cab2825",
  "source_priority_instruction_rowset_sha256": "dfe6c7081ac7c3c28ac6e8afcb736a2d16bc8a6cbd8cba1cbc38b420064ddd65",
  "source_slice_prioritization_rowset_sha256": "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c"
}
```

## Handoff Rows

| priority | execution | program | status | instruction rows | fixture | apply allowed |
| ---: | ---: | --- | --- | ---: | --- | --- |
| 1 | 4 | General Surgery | ready_for_local_reviewer_handoff_execution | 2 | 16/16 pass | false |

## Commands

| command | value |
| --- | --- |
| slice | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 4 --output /tmp/vanderbilt_reviewer_workbook_order_4.csv` |
| extract | `python3 scripts/extract_vanderbilt_reviewer_decision_patch.py --workbook /tmp/vanderbilt_reviewer_workbook_order_4.csv --output /tmp/vanderbilt_reviewer_patch_order_4.csv` |
| dry run | `python3 scripts/apply_vanderbilt_reviewer_decision_patch.py --patch /tmp/vanderbilt_reviewer_patch_order_4.csv` |
