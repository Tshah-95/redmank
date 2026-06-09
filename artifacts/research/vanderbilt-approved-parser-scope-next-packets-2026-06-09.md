---
type: research-checkpoint
title: Vanderbilt Approved Parser Scope Next Packets
created_at: 2026-06-09T04:52:32.693253+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Approved Parser Scope Next Packets

## Boundary

Approved non-mutating Vanderbilt parser/scope next-packet lane. The exact GBrain approval allows only source-specific parser-build review packets, linked-route scope-disposition packets, a General Surgery rendered-review packet, and route retry/recourse handling. It does not approve parser output as people, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "by_approved_next_artifact_lane": {
    "general_surgery_rendered_parser_scope_packet": 1,
    "linked_route_scope_disposition_packet": 3,
    "route_retry_or_recourse_packet": 1,
    "source_specific_parser_build_review_packet": 15
  },
  "by_next_packet_status": {
    "approved_non_mutating_general_surgery_rendered_review_packet_ready": 1,
    "approved_non_mutating_parser_build_review_packet_ready": 15,
    "approved_non_mutating_route_recourse_packet_ready": 1,
    "approved_non_mutating_scope_disposition_packet_ready": 3
  },
  "csv": "artifacts/data/vanderbilt_approved_parser_scope_next_packets.csv",
  "gbrain_approval_line": "APPROVE vanderbilt_targeted_route_observation_parser_scope_packet_approved PACKET_ROWS 20 PARSER_BUILD_REVIEW_ROWS 15 SCOPE_DISPOSITION_ROWS 3 GENERAL_SURGERY_ROWS 1 RECOURSE_ROWS 1 ROWSET_SHA256 9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3",
  "generated_at": "2026-06-09T04:52:32.693253+00:00",
  "json": "artifacts/data/vanderbilt_approved_parser_scope_next_packets.json",
  "markdown": "artifacts/research/vanderbilt-approved-parser-scope-next-packets-2026-06-09.md",
  "mutation_allowed": false,
  "next_packet_rows": 20,
  "policy": "Approved non-mutating Vanderbilt parser/scope next-packet lane. The exact GBrain approval allows only source-specific parser-build review packets, linked-route scope-disposition packets, a General Surgery rendered-review packet, and route retry/recourse handling. It does not approve parser output as people, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "rowset_sha256": "098c0a813eb577552b46e9454fbf2e9088bcee228d0aa678827439eba082e261",
  "source_parser_scope_packet": "artifacts/data/vanderbilt_targeted_route_parser_scope_packet.json",
  "source_parser_scope_packet_rows": 20,
  "source_parser_scope_packet_rowset_sha256": "9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3",
  "source_parser_scope_packet_summary": "artifacts/data/vanderbilt_targeted_route_parser_scope_packet_summary.json"
}
```

## Next Packet Rows

| program | approved lane | status | fetch url | required action |
| --- | --- | --- | --- | --- |
| General Surgery | general_surgery_rendered_parser_scope_packet | approved_non_mutating_general_surgery_rendered_review_packet_ready | https://www.vumc.org/generalsurgeryresidency/current-residents | Run rendered/DOM review for General Surgery current-residents evidence before parser-build or recourse. |
| Advanced Endoscopy | linked_route_scope_disposition_packet | approved_non_mutating_scope_disposition_packet_ready | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | Classify shared or ambiguous linked-route evidence as same-program parser candidate, context, or recourse. |
| Advanced Inflammatory Bowel Disease | linked_route_scope_disposition_packet | approved_non_mutating_scope_disposition_packet_ready | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | Classify shared or ambiguous linked-route evidence as same-program parser candidate, context, or recourse. |
| Orthopaedic Surgery | linked_route_scope_disposition_packet | approved_non_mutating_scope_disposition_packet_ready | https://www.vumc.org/ortho/node/193 | Classify shared or ambiguous linked-route evidence as same-program parser candidate, context, or recourse. |
| Orthopaedic Surgery | route_retry_or_recourse_packet | approved_non_mutating_route_recourse_packet_ready | https://www.vumc.org/ortho/2022-residency-match | Retry or replace the failed official route and carry recourse evidence without parser acceptance. |
| Academic General Pediatrics | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/node/1106 | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Developmental-Behavioral Pediatrics | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/current-developmental-behavioral-pediatrics-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Gastroenterology | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Neonatal-Perinatal Medicine | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/current-neonatal-perinatal-medicine-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Pediatric Critical Care | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/current-pediatric-critical-care-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Pediatric Emergency Medicine | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/emergency-medicine-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Pediatric Endocrinology | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/current-pediatric-endocrinology-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Pediatric Gastroenterology | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/current-pediatric-gastroenterology-hepatology-and-nutrition-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Pediatric Hospital Medicine | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/current-pediatric-hospital-medicine-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Pediatric Infectious Diseases | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/infectious-diseases-fellowship/fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Pediatric Rheumatology | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/current-rheumatology-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Pediatrics | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/pgy-1 | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Psychiatry | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://www.vumc.org/psychiatry/post-graduate-year-1-pgy1 | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Rheumatology | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://pediatrics.vumc.org/person/current-rheumatology-fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
| Transplant Hepatology | source_specific_parser_build_review_packet | approved_non_mutating_parser_build_review_packet_ready | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | Build source-specific parser tests and candidate-only extraction evidence; do not accept extracted people. |
