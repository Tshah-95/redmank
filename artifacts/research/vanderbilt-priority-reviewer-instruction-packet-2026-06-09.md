---
type: research-checkpoint
title: Vanderbilt Priority Reviewer Instruction Packet
created_at: 2026-06-09T09:10:58.521296+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Priority Reviewer Instruction Packet

## Boundary

Non-mutating Vanderbilt priority reviewer instruction packet. It materializes the priority_rank=1 General Surgery reviewer slice scaffold from public-safe hashes, keys, allowed actions, required confirmations, and helper commands only. It does not fill reviewer decisions, include reviewer notes, publish raw candidate labels or URLs, extract filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "apply_executed": false,
  "by_candidate_source_kind": {
    "heading_signal": 1,
    "profile_anchor": 1
  },
  "csv": "artifacts/data/vanderbilt_priority_reviewer_instruction_packet.csv",
  "denominator_closure_allowed": false,
  "execution_order": "4",
  "free_text_note_column_committed": false,
  "gbrain_approval_line": "APPROVE vanderbilt_priority_1_reviewer_instruction_packet_non_mutating_increment",
  "gbrain_approval_status": "approved_non_mutating_vanderbilt_priority_1_reviewer_instruction_packet_increment",
  "generated_at": "2026-06-09T09:10:58.521296+00:00",
  "instruction_rows": 2,
  "json": "artifacts/data/vanderbilt_priority_reviewer_instruction_packet.json",
  "markdown": "artifacts/research/vanderbilt-priority-reviewer-instruction-packet-2026-06-09.md",
  "mutation_allowed": false,
  "pending_blank_instruction_rows": 2,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt priority reviewer instruction packet. It materializes the priority_rank=1 General Surgery reviewer slice scaffold from public-safe hashes, keys, allowed actions, required confirmations, and helper commands only. It does not fill reviewer decisions, include reviewer notes, publish raw candidate labels or URLs, extract filled patches, run apply, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, or collapse identities.",
  "priority_rank": "1",
  "program_name": "General Surgery",
  "raw_candidate_names_committed": false,
  "raw_person_urls_committed": false,
  "review_queue_lane": "candidate_fingerprint_review",
  "rowset_sha256": "dfe6c7081ac7c3c28ac6e8afcb736a2d16bc8a6cbd8cba1cbc38b420064ddd65",
  "school_verification_allowed": false,
  "source_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_prioritization_rowset_sha256": "eeaf14d0496276eb6603f3434a497eb3640afc7a69802301e1077a7e52c92d7c",
  "source_workbook_rowset_sha256": "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3"
}
```

## Instruction Rows

| order | priority | execution | lane | program | source kind | status |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 4 | candidate_fingerprint_review | General Surgery | profile_anchor | pending_blank_reviewer_instruction |
| 2 | 1 | 4 | candidate_fingerprint_review | General Surgery | heading_signal | pending_blank_reviewer_instruction |
