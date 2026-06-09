---
type: research-checkpoint
title: Vanderbilt Candidate Review Queues
created_at: 2026-06-09T05:26:28.566876+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Candidate Review Queues

## Boundary

Approved non-mutating Vanderbilt candidate review queues. Queue rows contain candidate/program/source hashes, source kind, route hashes, scope status, and recourse status only. They contain no raw candidate labels, raw person URLs, accepted person rows, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_program_queue_rows": {
    "Academic General Pediatrics": 4,
    "Advanced Endoscopy": 1,
    "Advanced Inflammatory Bowel Disease": 1,
    "Developmental-Behavioral Pediatrics": 4,
    "Gastroenterology": 10,
    "General Surgery": 2,
    "Neonatal-Perinatal Medicine": 19,
    "Orthopaedic Surgery": 2,
    "Pediatric Critical Care": 17,
    "Pediatric Emergency Medicine": 17,
    "Pediatric Endocrinology": 3,
    "Pediatric Gastroenterology": 12,
    "Pediatric Hospital Medicine": 4,
    "Pediatric Infectious Diseases": 10,
    "Pediatric Rheumatology": 4,
    "Pediatrics": 26,
    "Psychiatry": 9,
    "Rheumatology": 4,
    "Transplant Hepatology": 10
  },
  "by_queue_status": {
    "ready_for_human_candidate_identity_review_no_ingestion": 155,
    "ready_for_route_replacement_review_no_closure": 1,
    "ready_for_scope_routing_review_no_url_rewrite": 3
  },
  "by_review_queue_lane": {
    "candidate_fingerprint_review": 155,
    "linked_scope_metadata_review": 3,
    "route_recourse_review": 1
  },
  "csv": "artifacts/data/vanderbilt_candidate_review_queues.csv",
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T05:26:28.566876+00:00",
  "json": "artifacts/data/vanderbilt_candidate_review_queues.json",
  "markdown": "artifacts/research/vanderbilt-candidate-review-queues-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Approved non-mutating Vanderbilt candidate review queues. Queue rows contain candidate/program/source hashes, source kind, route hashes, scope status, and recourse status only. They contain no raw candidate labels, raw person URLs, accepted person rows, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "raw_candidate_names_committed": false,
  "raw_person_urls_committed": false,
  "review_queue_rows": 159,
  "rowset_sha256": "b74b337bfa43406d8a200956d469eb5dc0d41902c197f78af85001f18750b148",
  "source_approval_rows": 159,
  "source_review_queue_approval_packet": "artifacts/data/vanderbilt_candidate_review_queue_approval_packet.json",
  "source_review_queue_approval_rowset_sha256": "a62defd685b64560a138cfaeb82956254f49341ce982bb549fe1846b25dd5bd5",
  "source_review_queue_approval_summary": "artifacts/data/vanderbilt_candidate_review_queue_approval_packet_summary.json"
}
```

## Queue Rows

| priority | program | lane | status | accepted person |
| ---: | --- | --- | --- | --- |
| 90 | Academic General Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Academic General Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Academic General Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Academic General Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | General Surgery | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | General Surgery | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Endocrinology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Endocrinology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Endocrinology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Hospital Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Hospital Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Hospital Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Hospital Medicine | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Rheumatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Rheumatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Rheumatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatric Rheumatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Pediatrics | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Psychiatry | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Rheumatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Rheumatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Rheumatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Rheumatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 90 | Transplant Hepatology | candidate_fingerprint_review | ready_for_human_candidate_identity_review_no_ingestion | false |
| 70 | Advanced Endoscopy | linked_scope_metadata_review | ready_for_scope_routing_review_no_url_rewrite | false |
| 70 | Advanced Inflammatory Bowel Disease | linked_scope_metadata_review | ready_for_scope_routing_review_no_url_rewrite | false |
| 70 | Orthopaedic Surgery | linked_scope_metadata_review | ready_for_scope_routing_review_no_url_rewrite | false |
| 60 | Orthopaedic Surgery | route_recourse_review | ready_for_route_replacement_review_no_closure | false |
