---
type: research-checkpoint
title: Vanderbilt Slice 2 Route Parser Scope Approval Packet
created_at: 2026-06-09T11:27:20.039477+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Slice 2 Route Parser Scope Approval Packet

## Boundary

Non-mutating Vanderbilt slice-2 route parser/scope approval-request packet. It classifies the 18 approved live route observations into target-route parser-build review, related-scope/context disposition, broader official-context recourse, or denominator-redirect recourse lanes. It requests exact future approval only; it does not allow web fetching, parser implementation, parser acceptance, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment/profile/contact/research-fact acceptance, raw dump publication, or identity collapse.

## Required Approval Line

`APPROVE vanderbilt_slice_2_route_parser_scope_approval_packet_approved PACKET_ROWS 18 TARGET_ROUTE_REVIEW_ROWS 5 RELATED_SCOPE_ROWS 5 BROADER_CONTEXT_RECOURSE_ROWS 4 DENOMINATOR_REDIRECT_RECOURSE_ROWS 4 SOURCE_ROWSET_SHA256 c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0 ROWSET_SHA256 bb0c69694a411c386964d1b7ae523a65a31452e5d62db227d4469044bd109672`

If GBrain does not return that exact line, this packet remains a non-mutating request artifact only.

GBrain approval status: `pending_exact_approval_line`.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_approval_request_lane": {
    "broader_context_recourse_review": 4,
    "denominator_redirect_recourse_review": 4,
    "related_scope_context_disposition_review": 5,
    "target_route_parser_build_review": 5
  },
  "by_packet_status": {
    "broader_context_recourse_candidate_needs_exact_gbrain_approval": 4,
    "redirect_recourse_candidate_needs_exact_gbrain_approval": 4,
    "related_scope_context_needs_exact_gbrain_approval": 5,
    "target_route_parser_scope_candidate_needs_exact_gbrain_approval": 5
  },
  "by_route_role": {
    "candidate_context": 9,
    "denominator": 9
  },
  "csv": "artifacts/data/vanderbilt_slice_2_route_parser_scope_approval_packet.csv",
  "denominator_closure_allowed": false,
  "gbrain_approval_effect": "vanderbilt_slice_2_route_parser_scope_approval_packet_approved",
  "gbrain_approval_status": "pending_exact_approval_line",
  "gbrain_denial_effect": "vanderbilt_slice_2_route_parser_scope_approval_packet_denied",
  "gbrain_denial_line": "",
  "gbrain_denial_recourse": "",
  "generated_at": "2026-06-09T11:27:20.039477+00:00",
  "identity_collapse_allowed": false,
  "json": "artifacts/data/vanderbilt_slice_2_route_parser_scope_approval_packet.json",
  "markdown": "artifacts/research/vanderbilt-slice-2-route-parser-scope-approval-packet-2026-06-09.md",
  "mutation_allowed": false,
  "not_approved": [
    "live_web_fetch",
    "parser_implementation",
    "parser_acceptance",
    "person_ingestion",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "enrichment_acceptance",
    "profile_fact_acceptance",
    "contact_fact_acceptance",
    "research_fact_acceptance",
    "raw_dump_publication",
    "unique_person_identity_collapse"
  ],
  "packet_rows": 18,
  "parser_acceptance_allowed": false,
  "parser_implementation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt slice-2 route parser/scope approval-request packet. It classifies the 18 approved live route observations into target-route parser-build review, related-scope/context disposition, broader official-context recourse, or denominator-redirect recourse lanes. It requests exact future approval only; it does not allow web fetching, parser implementation, parser acceptance, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment/profile/contact/research-fact acceptance, raw dump publication, or identity collapse.",
  "raw_dump_publication_allowed": false,
  "request_rows_represented": 9,
  "required_approval_line": "APPROVE vanderbilt_slice_2_route_parser_scope_approval_packet_approved PACKET_ROWS 18 TARGET_ROUTE_REVIEW_ROWS 5 RELATED_SCOPE_ROWS 5 BROADER_CONTEXT_RECOURSE_ROWS 4 DENOMINATOR_REDIRECT_RECOURSE_ROWS 4 SOURCE_ROWSET_SHA256 c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0 ROWSET_SHA256 bb0c69694a411c386964d1b7ae523a65a31452e5d62db227d4469044bd109672",
  "rowset_sha256": "bb0c69694a411c386964d1b7ae523a65a31452e5d62db227d4469044bd109672",
  "school_verification_allowed": false,
  "source_approval_request_rowset_sha256": "98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d",
  "source_execution_plan_rowset_sha256": "c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b",
  "source_observation_rows": 18,
  "source_route_observation_rowset_sha256": "c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0",
  "source_route_observation_summary": "artifacts/data/vanderbilt_slice_2_live_route_observation_summary.json",
  "source_route_observations": "artifacts/data/vanderbilt_slice_2_live_route_observations.csv",
  "url_rewrite_allowed": false,
  "web_fetch_allowed": false
}
```

## Packet Rows

| request | role | program | request lane | status | next artifact if approved |
| ---: | --- | --- | --- | --- | --- |
| 1 | candidate_context | Plastic Surgery-Integrated | related_scope_context_disposition_review | related_scope_context_needs_exact_gbrain_approval | vanderbilt_slice_2_related_scope_disposition_packet |
| 1 | denominator | Plastic Surgery-Integrated | target_route_parser_build_review | target_route_parser_scope_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_target_route_parser_build_review_packet |
| 2 | candidate_context | Adult and Pediatric Craniofacial | related_scope_context_disposition_review | related_scope_context_needs_exact_gbrain_approval | vanderbilt_slice_2_related_scope_disposition_packet |
| 2 | denominator | Adult and Pediatric Craniofacial | target_route_parser_build_review | target_route_parser_scope_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_target_route_parser_build_review_packet |
| 3 | candidate_context | Hand Surgery (Plastic Surgery) | related_scope_context_disposition_review | related_scope_context_needs_exact_gbrain_approval | vanderbilt_slice_2_related_scope_disposition_packet |
| 3 | denominator | Hand Surgery (Plastic Surgery) | target_route_parser_build_review | target_route_parser_scope_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_target_route_parser_build_review_packet |
| 4 | candidate_context | Plastic Surgery | related_scope_context_disposition_review | related_scope_context_needs_exact_gbrain_approval | vanderbilt_slice_2_related_scope_disposition_packet |
| 4 | denominator | Plastic Surgery | target_route_parser_build_review | target_route_parser_scope_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_target_route_parser_build_review_packet |
| 5 | candidate_context | Emergency Medical Services | broader_context_recourse_review | broader_context_recourse_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_broader_context_recourse_packet |
| 5 | denominator | Emergency Medical Services | denominator_redirect_recourse_review | redirect_recourse_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_denominator_redirect_recourse_packet |
| 6 | candidate_context | Emergency Medicine Simulation | broader_context_recourse_review | broader_context_recourse_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_broader_context_recourse_packet |
| 6 | denominator | Emergency Medicine Simulation | denominator_redirect_recourse_review | redirect_recourse_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_denominator_redirect_recourse_packet |
| 7 | candidate_context | Emergency Medicine Ultrasound | broader_context_recourse_review | broader_context_recourse_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_broader_context_recourse_packet |
| 7 | denominator | Emergency Medicine Ultrasound | denominator_redirect_recourse_review | redirect_recourse_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_denominator_redirect_recourse_packet |
| 8 | candidate_context | Genitourinary Reconstruction and Trauma | related_scope_context_disposition_review | related_scope_context_needs_exact_gbrain_approval | vanderbilt_slice_2_related_scope_disposition_packet |
| 8 | denominator | Genitourinary Reconstruction and Trauma | target_route_parser_build_review | target_route_parser_scope_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_target_route_parser_build_review_packet |
| 9 | candidate_context | Global Emergency Medicine | broader_context_recourse_review | broader_context_recourse_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_broader_context_recourse_packet |
| 9 | denominator | Global Emergency Medicine | denominator_redirect_recourse_review | redirect_recourse_candidate_needs_exact_gbrain_approval | vanderbilt_slice_2_denominator_redirect_recourse_packet |
