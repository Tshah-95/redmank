---
type: research-checkpoint
title: School Gap Resolution Candidate Output Bridge
created_at: 2026-06-09T08:11:00.598589+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# School Gap Resolution Candidate Output Bridge

## Boundary

Non-mutating bridge from Vanderbilt parser/scope bridge rows to approved candidate-only parser diagnostics. It records implementation approval coverage, candidate fingerprint counts, scope metadata, recourse rows, and verification status only. It does not accept parser outputs as people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, publish raw names, or collapse identities.

## Summary

```json
{
  "bridge_rows": 19,
  "by_candidate_output_coverage_status": {
    "covered_by_verified_candidate_only_outputs": 16,
    "covered_by_verified_scope_metadata": 3
  },
  "by_candidate_output_status": {
    "candidate_fingerprints_verified": 16,
    "scope_metadata_verified": 3
  },
  "by_next_required_approval": {
    "exact_candidate_review_queue_or_acceptance_packet_required": 16,
    "exact_scope_disposition_acceptance_or_parser_build_approval_required": 3
  },
  "candidate_fingerprint_rows_represented": 155,
  "candidate_output_rows_represented": 159,
  "csv": "artifacts/data/school_gap_resolution_candidate_output_bridge.csv",
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T08:11:00.598589+00:00",
  "identity_collapse_allowed": false,
  "implementation_approval_rows_represented": 20,
  "json": "artifacts/data/school_gap_resolution_candidate_output_bridge.json",
  "markdown": "artifacts/research/school-gap-resolution-candidate-output-bridge-2026-06-09.md",
  "mutation_allowed": false,
  "parser_acceptance_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating bridge from Vanderbilt parser/scope bridge rows to approved candidate-only parser diagnostics. It records implementation approval coverage, candidate fingerprint counts, scope metadata, recourse rows, and verification status only. It does not accept parser outputs as people, ingest people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, publish raw names, or collapse identities.",
  "route_recourse_rows_represented": 1,
  "rowset_sha256": "dfb141c1883d85fd6a8c7c0e015b939414788936eb13dbb04eecb9111ff5b843",
  "school_verification_allowed": false,
  "scope_metadata_rows_represented": 3,
  "source_candidate_output_rowset_sha256": "2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba",
  "source_candidate_output_verification_rowset_sha256": "918556f5b5a33b5d8e7181ed6654a9b7773b8c8a24f09f9a23b06c7157d39fe2",
  "source_implementation_approval_rowset_sha256": "0ce935b64a7eb2153b4fb4b5a8cca47034bab839aa932c8951c29d3bda363b40",
  "source_parser_scope_bridge_rowset_sha256": "942d131072d56524c9e19832c084b9e2520e43e783e3a9c0c6e2ae30c0f06912",
  "url_rewrite_allowed": false
}
```

## Bridge Rows

| program | output status | candidates | scope | recourse | next approval |
| --- | --- | ---: | ---: | ---: | --- |
| Academic General Pediatrics | candidate_fingerprints_verified | 4 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Advanced Endoscopy | scope_metadata_verified | 0 | 1 | 0 | exact_scope_disposition_acceptance_or_parser_build_approval_required |
| Advanced Inflammatory Bowel Disease | scope_metadata_verified | 0 | 1 | 0 | exact_scope_disposition_acceptance_or_parser_build_approval_required |
| Developmental-Behavioral Pediatrics | candidate_fingerprints_verified | 4 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Gastroenterology | candidate_fingerprints_verified | 10 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| General Surgery | candidate_fingerprints_verified | 2 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Neonatal-Perinatal Medicine | candidate_fingerprints_verified | 19 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Orthopaedic Surgery | scope_metadata_verified | 0 | 1 | 1 | exact_scope_disposition_acceptance_or_parser_build_approval_required |
| Pediatric Critical Care | candidate_fingerprints_verified | 17 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Pediatric Emergency Medicine | candidate_fingerprints_verified | 17 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Pediatric Endocrinology | candidate_fingerprints_verified | 3 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Pediatric Gastroenterology | candidate_fingerprints_verified | 12 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Pediatric Hospital Medicine | candidate_fingerprints_verified | 4 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Pediatric Infectious Diseases | candidate_fingerprints_verified | 10 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Pediatric Rheumatology | candidate_fingerprints_verified | 4 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Pediatrics | candidate_fingerprints_verified | 26 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Psychiatry | candidate_fingerprints_verified | 9 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Rheumatology | candidate_fingerprints_verified | 4 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
| Transplant Hepatology | candidate_fingerprints_verified | 10 | 0 | 0 | exact_candidate_review_queue_or_acceptance_packet_required |
