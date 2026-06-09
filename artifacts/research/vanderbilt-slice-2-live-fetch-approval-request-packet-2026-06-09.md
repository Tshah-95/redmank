---
type: research-checkpoint
title: Vanderbilt Slice 2 Live Fetch Approval Request Packet
created_at: 2026-06-09T10:31:37.761420+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Slice 2 Live Fetch Approval Request Packet

## Boundary

Non-mutating Vanderbilt slice-2 live-fetch approval request. It asks whether a later bounded route-probing run may fetch current public official pages for the nine committed slice-2 execution-plan rows. This packet does not fetch web pages, run probes, store raw dumps, fill reviewer decisions, apply patches, approve parser output, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept unsupported labels, accept enrichment/profile/contact/research facts, or collapse identities.

## Exact Approval Line

`APPROVE vanderbilt_slice_2_live_fetch_approval_request_packet_approved REQUEST_ROWS 9 SOURCE_PLAN_ROWS 9 SOURCE_ROWSET_SHA256 c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b ROWSET_SHA256 98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d`

## Summary

```json
{
  "accepted_person_rows": 0,
  "approval_request_rows": 9,
  "approval_required_for": [
    "live_web_fetch_or_probe",
    "route_observation_commit",
    "parser_acceptance",
    "person_ingestion",
    "denominator_closure",
    "vanderbilt_school_verification",
    "source_url_rewrite",
    "scope_closure",
    "identity_collapse"
  ],
  "artifact_label": "vanderbilt-slice2-live-fetch-approval-request-packet",
  "by_candidate_context_status": {
    "manual_scope_review": 5,
    "secondary_source_search_needed": 4
  },
  "by_plan_lane": {
    "broader_official_search_plan": 4,
    "related_scope_exclusion_then_target_program_source_discovery": 5
  },
  "csv": "artifacts/data/vanderbilt_slice_2_live_fetch_approval_request_packet.csv",
  "denominator_closure_allowed": false,
  "execution_order": 1,
  "future_web_fetch_requested": true,
  "gbrain_advisory_effect": "gbrain_selected_vanderbilt_slice_2_live_fetch_approval_request_packet_option_a",
  "gbrain_approval_status": "pending_exact_gbrain_approval",
  "gbrain_denial_line": "DENY vanderbilt_slice_2_live_fetch_approval_request_packet_denied",
  "gbrain_exact_approval_line": "APPROVE vanderbilt_slice_2_live_fetch_approval_request_packet_approved REQUEST_ROWS 9 SOURCE_PLAN_ROWS 9 SOURCE_ROWSET_SHA256 c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b ROWSET_SHA256 98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d",
  "generated_at": "2026-06-09T10:31:37.761420+00:00",
  "identity_collapse_allowed": false,
  "json": "artifacts/data/vanderbilt_slice_2_live_fetch_approval_request_packet.json",
  "markdown": "artifacts/research/vanderbilt-slice-2-live-fetch-approval-request-packet-2026-06-09.md",
  "mutation_allowed": false,
  "parser_acceptance_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt slice-2 live-fetch approval request. It asks whether a later bounded route-probing run may fetch current public official pages for the nine committed slice-2 execution-plan rows. This packet does not fetch web pages, run probes, store raw dumps, fill reviewer decisions, apply patches, approve parser output, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept unsupported labels, accept enrichment/profile/contact/research facts, or collapse identities.",
  "private_artifact_paths_committed": false,
  "prohibited_mutations": [
    "person_ingestion",
    "parser_output_as_accepted_people",
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
  "raw_dump_publication_allowed": false,
  "rowset_sha256": "98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d",
  "school_verification_allowed": false,
  "source_execution_plan_rowset_sha256": "c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b",
  "source_plan_rows": 9,
  "triage_order": 2,
  "url_rewrite_allowed": false,
  "web_fetch_allowed": false,
  "web_fetch_executed": false
}
```

## Request Rows

| order | program | lane | request status | future fetch requested | fetched now |
| ---: | --- | --- | --- | --- | --- |
| 1 | Plastic Surgery-Integrated | related_scope_exclusion_then_target_program_source_discovery | pending_exact_gbrain_approval | true | false |
| 2 | Adult and Pediatric Craniofacial | related_scope_exclusion_then_target_program_source_discovery | pending_exact_gbrain_approval | true | false |
| 3 | Hand Surgery (Plastic Surgery) | related_scope_exclusion_then_target_program_source_discovery | pending_exact_gbrain_approval | true | false |
| 4 | Plastic Surgery | related_scope_exclusion_then_target_program_source_discovery | pending_exact_gbrain_approval | true | false |
| 5 | Emergency Medical Services | broader_official_search_plan | pending_exact_gbrain_approval | true | false |
| 6 | Emergency Medicine Simulation | broader_official_search_plan | pending_exact_gbrain_approval | true | false |
| 7 | Emergency Medicine Ultrasound | broader_official_search_plan | pending_exact_gbrain_approval | true | false |
| 8 | Genitourinary Reconstruction and Trauma | related_scope_exclusion_then_target_program_source_discovery | pending_exact_gbrain_approval | true | false |
| 9 | Global Emergency Medicine | broader_official_search_plan | pending_exact_gbrain_approval | true | false |
