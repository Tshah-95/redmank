---
type: research-checkpoint
title: School Gap Resolution Review Queue Bridge
created_at: 2026-06-09T08:25:57.081390+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# School Gap Resolution Review Queue Bridge

## Boundary

Non-mutating bridge from Vanderbilt candidate-output coverage to review queues, decision scaffolds, and pending manual-decision audit rows. It records reviewer-decision readiness only. It does not fill reviewer decisions, accept people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "bridge_rows": 19,
  "by_next_required_approval": {
    "exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required": 19
  },
  "by_review_queue_bridge_status": {
    "pending_reviewer_decisions_ready": 19
  },
  "by_review_queue_coverage_status": {
    "covered_by_review_queue_scaffold_and_pending_audit": 19
  },
  "candidate_output_rows_represented": 159,
  "csv": "artifacts/data/school_gap_resolution_review_queue_bridge.csv",
  "decision_scaffold_rows_represented": 159,
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T08:25:57.081390+00:00",
  "identity_collapse_allowed": false,
  "invalid_decision_rows_represented": 0,
  "json": "artifacts/data/school_gap_resolution_review_queue_bridge.json",
  "manual_decision_audit_rows_represented": 159,
  "markdown": "artifacts/research/school-gap-resolution-review-queue-bridge-2026-06-09.md",
  "mutation_allowed": false,
  "pending_decision_rows_represented": 159,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating bridge from Vanderbilt candidate-output coverage to review queues, decision scaffolds, and pending manual-decision audit rows. It records reviewer-decision readiness only. It does not fill reviewer decisions, accept people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, or collapse identities.",
  "queue_approval_rows_represented": 159,
  "review_queue_rows_represented": 159,
  "rowset_sha256": "46c2b215f28819df10913fa35f7dff6e7f4afc4ec6c3598e7432088c3f34e10d",
  "school_verification_allowed": false,
  "source_candidate_output_bridge_rowset_sha256": "dfb141c1883d85fd6a8c7c0e015b939414788936eb13dbb04eecb9111ff5b843",
  "source_decision_audit_rowset_sha256": "e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de",
  "source_decision_scaffold_rowset_sha256": "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938",
  "source_queue_approval_rowset_sha256": "a62defd685b64560a138cfaeb82956254f49341ce982bb549fe1846b25dd5bd5",
  "source_review_queue_rowset_sha256": "b74b337bfa43406d8a200956d469eb5dc0d41902c197f78af85001f18750b148",
  "source_scaffold_verification_rowset_sha256": "24e03f71174cd456b4783457113d64d4b15185721fc86092ca2a5f47e7eb4260",
  "url_rewrite_allowed": false,
  "valid_non_mutating_decision_rows_represented": 0
}
```

## Bridge Rows

| program | bridge status | queue | scaffold | pending | next approval |
| --- | --- | ---: | ---: | ---: | --- |
| Academic General Pediatrics | pending_reviewer_decisions_ready | 4 | 4 | 4 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Advanced Endoscopy | pending_reviewer_decisions_ready | 1 | 1 | 1 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Advanced Inflammatory Bowel Disease | pending_reviewer_decisions_ready | 1 | 1 | 1 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Developmental-Behavioral Pediatrics | pending_reviewer_decisions_ready | 4 | 4 | 4 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Gastroenterology | pending_reviewer_decisions_ready | 10 | 10 | 10 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| General Surgery | pending_reviewer_decisions_ready | 2 | 2 | 2 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Neonatal-Perinatal Medicine | pending_reviewer_decisions_ready | 19 | 19 | 19 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Orthopaedic Surgery | pending_reviewer_decisions_ready | 2 | 2 | 2 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Pediatric Critical Care | pending_reviewer_decisions_ready | 17 | 17 | 17 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Pediatric Emergency Medicine | pending_reviewer_decisions_ready | 17 | 17 | 17 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Pediatric Endocrinology | pending_reviewer_decisions_ready | 3 | 3 | 3 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Pediatric Gastroenterology | pending_reviewer_decisions_ready | 12 | 12 | 12 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Pediatric Hospital Medicine | pending_reviewer_decisions_ready | 4 | 4 | 4 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Pediatric Infectious Diseases | pending_reviewer_decisions_ready | 10 | 10 | 10 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Pediatric Rheumatology | pending_reviewer_decisions_ready | 4 | 4 | 4 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Pediatrics | pending_reviewer_decisions_ready | 26 | 26 | 26 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Psychiatry | pending_reviewer_decisions_ready | 9 | 9 | 9 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Rheumatology | pending_reviewer_decisions_ready | 4 | 4 | 4 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
| Transplant Hepatology | pending_reviewer_decisions_ready | 10 | 10 | 10 | exact_non_mutating_reviewer_decision_patch_or_future_acceptance_packet_required |
