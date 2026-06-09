---
type: research-checkpoint
title: Vanderbilt Public Reviewer Operator Packets
created_at: 2026-06-09T06:29:54.221079+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Public Reviewer Operator Packets

## Boundary

Public-safe Vanderbilt reviewer operator packets. They are a non-mutating runbook layer over the approved Vanderbilt candidate review batch packets and the hardened blank manual decision template. They do not fill reviewer decisions, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, publish raw candidate labels or raw person URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_operator_packet_status": {
    "ready_for_blank_template_manual_review": 20
  },
  "by_review_queue_lane": {
    "candidate_fingerprint_review": 16,
    "linked_scope_metadata_review": 3,
    "route_recourse_review": 1
  },
  "csv": "artifacts/data/vanderbilt_public_reviewer_operator_packets.csv",
  "decision_row_count": 159,
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T06:29:54.221079+00:00",
  "invalid_decision_rows": 0,
  "json": "artifacts/data/vanderbilt_public_reviewer_operator_packets.json",
  "manual_decisions_csv": "artifacts/data/vanderbilt_candidate_reviewer_decisions.csv",
  "markdown": "artifacts/research/vanderbilt-public-reviewer-operator-packets-2026-06-09.md",
  "missing_required_template_column_mentions": 0,
  "mutation_allowed": false,
  "new_gbrain_approval_status": "no_new_approval_line_claimed_retrieval_consulted_only",
  "operator_packet_rows": 20,
  "pending_decision_rows": 159,
  "person_ingestion_allowed": false,
  "policy": "Public-safe Vanderbilt reviewer operator packets. They are a non-mutating runbook layer over the approved Vanderbilt candidate review batch packets and the hardened blank manual decision template. They do not fill reviewer decisions, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, publish raw candidate labels or raw person URLs, accept enrichment facts, or collapse identities.",
  "raw_candidate_names_committed": false,
  "raw_person_urls_committed": false,
  "rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
  "source_batch_packet_rowset_sha256": "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f",
  "source_batch_packet_summary": "artifacts/data/vanderbilt_candidate_review_batch_packet_summary.json",
  "source_batch_packets": "artifacts/data/vanderbilt_candidate_review_batch_packets.csv",
  "source_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_decision_audit_summary": "artifacts/data/vanderbilt_candidate_reviewer_decision_audit_summary.json",
  "source_gbrain_approval_line": "APPROVE vanderbilt_candidate_review_packet_materialization_non_mutating_approved",
  "source_scaffold_rowset_sha256": "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938",
  "source_scaffold_summary": "artifacts/data/vanderbilt_candidate_review_decision_scaffold_summary.json",
  "valid_non_mutating_decision_rows": 0
}
```

## Operator Packets

| order | program | lane | status | rows | pending | missing columns |
| ---: | --- | --- | --- | ---: | ---: | --- |
| 1 | Academic General Pediatrics | candidate_fingerprint_review | ready_for_blank_template_manual_review | 4 | 4 | `[]` |
| 2 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | ready_for_blank_template_manual_review | 4 | 4 | `[]` |
| 3 | Gastroenterology | candidate_fingerprint_review | ready_for_blank_template_manual_review | 10 | 10 | `[]` |
| 4 | General Surgery | candidate_fingerprint_review | ready_for_blank_template_manual_review | 2 | 2 | `[]` |
| 5 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_blank_template_manual_review | 19 | 19 | `[]` |
| 6 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_blank_template_manual_review | 17 | 17 | `[]` |
| 7 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_blank_template_manual_review | 17 | 17 | `[]` |
| 8 | Pediatric Endocrinology | candidate_fingerprint_review | ready_for_blank_template_manual_review | 3 | 3 | `[]` |
| 9 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_blank_template_manual_review | 12 | 12 | `[]` |
| 10 | Pediatric Hospital Medicine | candidate_fingerprint_review | ready_for_blank_template_manual_review | 4 | 4 | `[]` |
| 11 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_blank_template_manual_review | 10 | 10 | `[]` |
| 12 | Pediatric Rheumatology | candidate_fingerprint_review | ready_for_blank_template_manual_review | 4 | 4 | `[]` |
| 13 | Pediatrics | candidate_fingerprint_review | ready_for_blank_template_manual_review | 26 | 26 | `[]` |
| 14 | Psychiatry | candidate_fingerprint_review | ready_for_blank_template_manual_review | 9 | 9 | `[]` |
| 15 | Rheumatology | candidate_fingerprint_review | ready_for_blank_template_manual_review | 4 | 4 | `[]` |
| 16 | Transplant Hepatology | candidate_fingerprint_review | ready_for_blank_template_manual_review | 10 | 10 | `[]` |
| 17 | Advanced Endoscopy | linked_scope_metadata_review | ready_for_blank_template_manual_review | 1 | 1 | `[]` |
| 18 | Advanced Inflammatory Bowel Disease | linked_scope_metadata_review | ready_for_blank_template_manual_review | 1 | 1 | `[]` |
| 19 | Orthopaedic Surgery | linked_scope_metadata_review | ready_for_blank_template_manual_review | 1 | 1 | `[]` |
| 20 | Orthopaedic Surgery | route_recourse_review | ready_for_blank_template_manual_review | 1 | 1 | `[]` |
