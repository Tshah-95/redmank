---
type: research-checkpoint
title: Vanderbilt Candidate Review Batch Packets
created_at: 2026-06-09T05:47:38.130871+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Candidate Review Batch Packets

## Boundary

Non-mutating Vanderbilt candidate reviewer batch packets. They group hash-only candidate, linked-scope, and route-recourse decision rows into bounded program/lane review packets with manual decision templates. They do not approve raw candidate labels, raw person URLs, accepted person rows, parser output as accepted people, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "accepted_person_rows": 0,
  "batch_packet_rows": 20,
  "by_packet_status": {
    "ready_for_manual_input": 20
  },
  "by_review_queue_lane": {
    "candidate_fingerprint_review": 16,
    "linked_scope_metadata_review": 3,
    "route_recourse_review": 1
  },
  "csv": "artifacts/data/vanderbilt_candidate_review_batch_packets.csv",
  "decision_row_count": 159,
  "denominator_closure_allowed": false,
  "gbrain_approval_line": "APPROVE vanderbilt_candidate_review_packet_materialization_non_mutating_approved",
  "gbrain_approval_status": "approved_non_mutating_batch_packet_materialization",
  "generated_at": "2026-06-09T05:47:38.130871+00:00",
  "invalid_decision_rows": 0,
  "json": "artifacts/data/vanderbilt_candidate_review_batch_packets.json",
  "manual_decisions_csv": "artifacts/data/vanderbilt_candidate_reviewer_decisions.csv",
  "markdown": "artifacts/research/vanderbilt-candidate-review-batch-packets-2026-06-09.md",
  "mutation_allowed": false,
  "pending_decision_rows": 159,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt candidate reviewer batch packets. They group hash-only candidate, linked-scope, and route-recourse decision rows into bounded program/lane review packets with manual decision templates. They do not approve raw candidate labels, raw person URLs, accepted person rows, parser output as accepted people, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "raw_candidate_names_committed": false,
  "raw_person_urls_committed": false,
  "rowset_sha256": "1f9da0ab244581dbf5782eab572d5045b8a53c8bffc9d4892e077ca1c7b0e30e",
  "source_decision_scaffold": "artifacts/data/vanderbilt_candidate_review_decision_scaffold.json",
  "source_decision_scaffold_rowset_sha256": "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938",
  "source_decision_scaffold_summary": "artifacts/data/vanderbilt_candidate_review_decision_scaffold_summary.json",
  "source_reviewer_decision_audit": "artifacts/data/vanderbilt_candidate_reviewer_decision_audit.json",
  "source_reviewer_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_reviewer_decision_audit_summary": "artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json",
  "valid_non_mutating_decision_rows": 0
}
```

## Batch Packets

| order | program | lane | status | rows | pending | invalid | next action |
| ---: | --- | --- | --- | ---: | ---: | ---: | --- |
| 1 | Academic General Pediatrics | candidate_fingerprint_review | ready_for_manual_input | 4 | 4 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 2 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | ready_for_manual_input | 4 | 4 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 3 | Gastroenterology | candidate_fingerprint_review | ready_for_manual_input | 10 | 10 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 4 | General Surgery | candidate_fingerprint_review | ready_for_manual_input | 2 | 2 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 5 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_manual_input | 19 | 19 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 6 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_manual_input | 17 | 17 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 7 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_manual_input | 17 | 17 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 8 | Pediatric Endocrinology | candidate_fingerprint_review | ready_for_manual_input | 3 | 3 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 9 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_manual_input | 12 | 12 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 10 | Pediatric Hospital Medicine | candidate_fingerprint_review | ready_for_manual_input | 4 | 4 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 11 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_manual_input | 10 | 10 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 12 | Pediatric Rheumatology | candidate_fingerprint_review | ready_for_manual_input | 4 | 4 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 13 | Pediatrics | candidate_fingerprint_review | ready_for_manual_input | 26 | 26 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 14 | Psychiatry | candidate_fingerprint_review | ready_for_manual_input | 9 | 9 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 15 | Rheumatology | candidate_fingerprint_review | ready_for_manual_input | 4 | 4 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 16 | Transplant Hepatology | candidate_fingerprint_review | ready_for_manual_input | 10 | 10 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 17 | Advanced Endoscopy | linked_scope_metadata_review | ready_for_manual_input | 1 | 1 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 18 | Advanced Inflammatory Bowel Disease | linked_scope_metadata_review | ready_for_manual_input | 1 | 1 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 19 | Orthopaedic Surgery | linked_scope_metadata_review | ready_for_manual_input | 1 | 1 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
| 20 | Orthopaedic Surgery | route_recourse_review | ready_for_manual_input | 1 | 1 | 0 | Review this bounded Vanderbilt packet and enter only non-mutating decisions in artifacts/data/vanderbilt_candidate_reviewer_decisions.csv, then rerun the decision audit. |
