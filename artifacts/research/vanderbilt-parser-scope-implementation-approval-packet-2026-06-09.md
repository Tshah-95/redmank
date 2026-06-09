---
type: research-checkpoint
title: Vanderbilt Parser Scope Implementation Approval Packet
created_at: 2026-06-09T05:06:36.430434+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Parser Scope Implementation Approval Packet

## Boundary

Non-mutating Vanderbilt parser/scope implementation approval request. It asks whether candidate-only parser implementation, scope-disposition recording, General Surgery parser-build review, and Orthopaedic route recourse work may proceed from the verified decision rowset. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Required Approval Line

`APPROVE vanderbilt_parser_scope_candidate_only_implementation_approved APPROVAL_ROWS 20 PARSER_IMPLEMENTATION_ROWS 15 SCOPE_ACCEPTANCE_ROWS 3 GENERAL_SURGERY_ROWS 1 RECOURSE_ROWS 1 ROWSET_SHA256 0ce935b64a7eb2153b4fb4b5a8cca47034bab839aa932c8951c29d3bda363b40`

GBrain approval status: `approved_exact_candidate_only_implementation_scope_recourse`.

## Summary

```json
{
  "approval_rows": 20,
  "by_approval_request_lane": {
    "candidate_only_parser_implementation_review": 15,
    "general_surgery_candidate_only_parser_review": 1,
    "linked_route_scope_disposition_acceptance": 3,
    "orthopaedic_route_recourse_or_replacement_review": 1
  },
  "by_next_artifact_if_approved": {
    "accepted_linked_route_scope_disposition_metadata": 3,
    "candidate_only_vanderbilt_parser_implementation_and_review_outputs": 15,
    "general_surgery_candidate_only_parser_review_outputs": 1,
    "orthopaedic_route_recourse_or_replacement_packet": 1
  },
  "csv": "artifacts/data/vanderbilt_parser_scope_implementation_approval_packet.csv",
  "denominator_closure_allowed": false,
  "gbrain_approval_effect": "vanderbilt_parser_scope_candidate_only_implementation_approved",
  "gbrain_approval_status": "approved_exact_candidate_only_implementation_scope_recourse",
  "gbrain_denial_effect": "vanderbilt_parser_scope_candidate_only_implementation_denied",
  "gbrain_denial_line": "",
  "gbrain_denial_recourse": "",
  "generated_at": "2026-06-09T05:06:36.430434+00:00",
  "json": "artifacts/data/vanderbilt_parser_scope_implementation_approval_packet.json",
  "markdown": "artifacts/research/vanderbilt-parser-scope-implementation-approval-packet-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt parser/scope implementation approval request. It asks whether candidate-only parser implementation, scope-disposition recording, General Surgery parser-build review, and Orthopaedic route recourse work may proceed from the verified decision rowset. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "required_approval_line": "APPROVE vanderbilt_parser_scope_candidate_only_implementation_approved APPROVAL_ROWS 20 PARSER_IMPLEMENTATION_ROWS 15 SCOPE_ACCEPTANCE_ROWS 3 GENERAL_SURGERY_ROWS 1 RECOURSE_ROWS 1 ROWSET_SHA256 0ce935b64a7eb2153b4fb4b5a8cca47034bab839aa932c8951c29d3bda363b40",
  "rowset_sha256": "0ce935b64a7eb2153b4fb4b5a8cca47034bab839aa932c8951c29d3bda363b40",
  "source_decision_packet_rowset_sha256": "aa94351eae7a7309d2b760a891f69538d8a8998058fc1ceb24af3d2b918644b8",
  "source_decision_packet_summary": "artifacts/data/vanderbilt_parser_scope_decision_packet_summary.json",
  "source_decision_packets": "artifacts/data/vanderbilt_parser_scope_decision_packets.json",
  "source_decision_rows": 20,
  "url_rewrite_allowed": false
}
```

## Approval Rows

| program | request lane | if approved | output boundary |
| --- | --- | --- | --- |
| Academic General Pediatrics | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Developmental-Behavioral Pediatrics | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Gastroenterology | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Neonatal-Perinatal Medicine | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Pediatric Critical Care | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Pediatric Emergency Medicine | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Pediatric Endocrinology | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Pediatric Gastroenterology | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Pediatric Hospital Medicine | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Pediatric Infectious Diseases | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Pediatric Rheumatology | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Pediatrics | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Psychiatry | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Rheumatology | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| Transplant Hepatology | candidate_only_parser_implementation_review | candidate_only_parser_code_and_tests | No raw names in committed artifacts; no accepted person rows; candidate fingerprints/counts and parser diagnostics only. |
| General Surgery | general_surgery_candidate_only_parser_review | general_surgery_candidate_only_parser_review | No accepted General Surgery people; rendered parser evidence must remain counts/hashes/diagnostics. |
| Advanced Endoscopy | linked_route_scope_disposition_acceptance | scope_metadata_and_parser_queue_routing | No URL rewrite, denominator closure, or person ingestion; scope decisions only route future parser/source-discovery work. |
| Advanced Inflammatory Bowel Disease | linked_route_scope_disposition_acceptance | scope_metadata_and_parser_queue_routing | No URL rewrite, denominator closure, or person ingestion; scope decisions only route future parser/source-discovery work. |
| Orthopaedic Surgery | linked_route_scope_disposition_acceptance | scope_metadata_and_parser_queue_routing | No URL rewrite, denominator closure, or person ingestion; scope decisions only route future parser/source-discovery work. |
| Orthopaedic Surgery | orthopaedic_route_recourse_or_replacement_review | route_recourse_probe_and_replacement_queue | No unresolved-gap closure or URL rewrite; recourse outputs must remain source-discovery evidence. |
