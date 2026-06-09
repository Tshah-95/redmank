---
type: research-checkpoint
title: Vanderbilt Targeted Route Parser Scope Packet
created_at: 2026-06-09T04:51:06.681667+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Targeted Route Parser Scope Packet

## Boundary

Non-mutating Vanderbilt route parser/scope approval-request packet. It asks whether route observations may advance into exact parser-build review, linked-scope disposition, or recourse handling. It authorizes no parser acceptance unless the exact approval line is returned, and it never authorizes person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, profile/contact/research-fact acceptance, or unique-person identity collapse.

## Required Approval Line

`APPROVE vanderbilt_targeted_route_observation_parser_scope_packet_approved PACKET_ROWS 20 PARSER_BUILD_REVIEW_ROWS 15 SCOPE_DISPOSITION_ROWS 3 GENERAL_SURGERY_ROWS 1 RECOURSE_ROWS 1 ROWSET_SHA256 9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3`

If GBrain does not return that exact line, this packet remains a non-mutating request artifact only.

GBrain approval status: `approved_exact_non_mutating_next_artifact_lane`.

## Summary

```json
{
  "by_approval_request_lane": {
    "exact_parser_build_review": 15,
    "linked_route_scope_disposition_review": 3,
    "rendered_general_surgery_parser_scope_review": 1,
    "route_recourse_review": 1
  },
  "by_packet_status": {
    "general_surgery_parser_scope_candidate_needs_exact_gbrain_approval": 1,
    "parser_build_candidate_needs_exact_gbrain_approval": 15,
    "recourse_row_not_parser_eligible": 1,
    "scope_disposition_candidate_needs_exact_gbrain_approval": 3
  },
  "csv": "artifacts/data/vanderbilt_targeted_route_parser_scope_packet.csv",
  "gbrain_approval_effect": "vanderbilt_targeted_route_observation_parser_scope_packet_approved",
  "gbrain_approval_status": "approved_exact_non_mutating_next_artifact_lane",
  "gbrain_denial_effect": "vanderbilt_targeted_route_observation_parser_scope_packet_denied",
  "gbrain_denial_line": "",
  "gbrain_denial_recourse": "",
  "generated_at": "2026-06-09T04:51:06.681667+00:00",
  "json": "artifacts/data/vanderbilt_targeted_route_parser_scope_packet.json",
  "markdown": "artifacts/research/vanderbilt-targeted-route-parser-scope-packet-2026-06-09.md",
  "mutation_allowed": false,
  "not_approved": [
    "parser_acceptance_without_exact_gbrain_line",
    "person_ingestion",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "profile_contact_research_fact_acceptance",
    "unique_person_identity_collapse"
  ],
  "packet_rows": 20,
  "policy": "Non-mutating Vanderbilt route parser/scope approval-request packet. It asks whether route observations may advance into exact parser-build review, linked-scope disposition, or recourse handling. It authorizes no parser acceptance unless the exact approval line is returned, and it never authorizes person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, profile/contact/research-fact acceptance, or unique-person identity collapse.",
  "required_approval_line": "APPROVE vanderbilt_targeted_route_observation_parser_scope_packet_approved PACKET_ROWS 20 PARSER_BUILD_REVIEW_ROWS 15 SCOPE_DISPOSITION_ROWS 3 GENERAL_SURGERY_ROWS 1 RECOURSE_ROWS 1 ROWSET_SHA256 9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3",
  "rowset_sha256": "9037a83b5ca96458e9a88f99dec1a13ee46e3ba8a4426bc5fd7a8c13e62e4fc3",
  "source_observation_rows": 20,
  "source_route_observation_rowset_sha256": "f547a298bf0efdaba630aa9d184ecd85979d0356039bbbd92d3c2fd026745258",
  "source_route_observation_summary": "artifacts/data/vanderbilt_targeted_route_observation_summary.json",
  "source_route_observations": "artifacts/data/vanderbilt_targeted_route_observations.json"
}
```

## Packet Rows

| program | lane | status | http | signal | fetch url |
| --- | --- | --- | ---: | --- | --- |
| Academic General Pediatrics | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/node/1106 |
| Developmental-Behavioral Pediatrics | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/current-developmental-behavioral-pediatrics-fellows |
| Gastroenterology | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Neonatal-Perinatal Medicine | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/current-neonatal-perinatal-medicine-fellows |
| Pediatric Critical Care | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/current-pediatric-critical-care-fellows |
| Pediatric Emergency Medicine | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/emergency-medicine-fellows |
| Pediatric Endocrinology | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/current-pediatric-endocrinology-fellows |
| Pediatric Gastroenterology | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/current-pediatric-gastroenterology-hepatology-and-nutrition-fellows |
| Pediatric Hospital Medicine | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/current-pediatric-hospital-medicine-fellows |
| Pediatric Infectious Diseases | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/infectious-diseases-fellowship/fellows |
| Pediatric Rheumatology | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/current-rheumatology-fellows |
| Pediatrics | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/pgy-1 |
| Psychiatry | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://www.vumc.org/psychiatry/post-graduate-year-1-pgy1 |
| Rheumatology | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://pediatrics.vumc.org/person/current-rheumatology-fellows |
| Transplant Hepatology | exact_parser_build_review | parser_build_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Advanced Endoscopy | linked_route_scope_disposition_review | scope_disposition_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Advanced Inflammatory Bowel Disease | linked_route_scope_disposition_review | scope_disposition_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Orthopaedic Surgery | linked_route_scope_disposition_review | scope_disposition_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://www.vumc.org/ortho/node/193 |
| General Surgery | rendered_general_surgery_parser_scope_review | general_surgery_parser_scope_candidate_needs_exact_gbrain_approval | 200 | official_route_current_roster_signal_needs_parser_scope_packet | https://www.vumc.org/generalsurgeryresidency/current-residents |
| Orthopaedic Surgery | route_recourse_review | recourse_row_not_parser_eligible | 404 | http_error_needs_retry_or_recourse | https://www.vumc.org/ortho/2022-residency-match |
