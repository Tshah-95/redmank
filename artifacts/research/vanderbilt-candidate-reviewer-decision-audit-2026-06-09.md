---
type: research-checkpoint
title: Vanderbilt Candidate Reviewer Decision Audit
created_at: 2026-06-09T11:13:14.569067+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Candidate Reviewer Decision Audit

## Boundary

Non-mutating Vanderbilt candidate reviewer decision audit. It checks manual reviewer decisions against the verified scaffold, confirmation fields, allowed action lists, and acceptance prohibitions. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "accepted_person_rows": 0,
  "audit_rows": 159,
  "by_audit_blocker": {},
  "by_audit_status": {
    "pending": 159
  },
  "by_decision_state": {
    "pending_blank_decision": 159
  },
  "by_review_queue_lane": {
    "candidate_fingerprint_review": 155,
    "linked_scope_metadata_review": 3,
    "route_recourse_review": 1
  },
  "csv": "artifacts/data/vanderbilt_candidate_reviewer_decision_audit.csv",
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T11:13:14.569067+00:00",
  "invalid_rows": 0,
  "json": "artifacts/data/vanderbilt_candidate_reviewer_decision_audit.json",
  "manual_decision_rows": 159,
  "manual_decisions_csv": "artifacts/data/vanderbilt_candidate_reviewer_decisions.csv",
  "manual_decisions_json": "artifacts/data/vanderbilt_candidate_reviewer_decisions.json",
  "markdown": "artifacts/research/vanderbilt-candidate-reviewer-decision-audit-2026-06-09.md",
  "mutation_allowed": false,
  "pending_rows": 159,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt candidate reviewer decision audit. It checks manual reviewer decisions against the verified scaffold, confirmation fields, allowed action lists, and acceptance prohibitions. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_decision_scaffold": "artifacts/data/vanderbilt_candidate_review_decision_scaffold.json",
  "source_decision_scaffold_rows": 159,
  "source_decision_scaffold_rowset_sha256": "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938",
  "source_decision_scaffold_summary": "artifacts/data/vanderbilt_candidate_review_decision_scaffold_summary.json",
  "valid_non_mutating_rows": 0
}
```

## Audit Rows

| program | lane | status | state | blocker |
| --- | --- | --- | --- | --- |
| Academic General Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Academic General Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Academic General Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Academic General Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Advanced Endoscopy | linked_scope_metadata_review | pending | pending_blank_decision |  |
| Advanced Inflammatory Bowel Disease | linked_scope_metadata_review | pending | pending_blank_decision |  |
| Developmental-Behavioral Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Developmental-Behavioral Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Developmental-Behavioral Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Developmental-Behavioral Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| General Surgery | candidate_fingerprint_review | pending | pending_blank_decision |  |
| General Surgery | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Orthopaedic Surgery | linked_scope_metadata_review | pending | pending_blank_decision |  |
| Orthopaedic Surgery | route_recourse_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Critical Care | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Emergency Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Endocrinology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Endocrinology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Endocrinology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Gastroenterology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Hospital Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Hospital Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Hospital Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Hospital Medicine | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Infectious Diseases | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Rheumatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Rheumatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Rheumatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatric Rheumatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Pediatrics | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Psychiatry | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Rheumatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Rheumatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Rheumatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Rheumatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
| Transplant Hepatology | candidate_fingerprint_review | pending | pending_blank_decision |  |
