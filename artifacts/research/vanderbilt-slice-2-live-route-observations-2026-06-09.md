---
type: research-checkpoint
title: Vanderbilt Slice 2 Live Route Observations
created_at: 2026-06-09T11:27:16.915210+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Slice 2 Live Route Observations

## Boundary

Approved non-mutating Vanderbilt slice-2 live route-observation ledger. It fetches only bounded public official denominator and candidate-context route metadata from the nine approved request rows, records final URLs, hashes, booleans, and coarse signal counts, and stores no raw HTML, raw text, raw headings, raw anchor samples, raw candidate names, accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment/profile/contact/research-fact acceptance, or identity collapse.

GBrain approval line used: `APPROVE vanderbilt_slice_2_live_fetch_approval_request_packet_approved REQUEST_ROWS 9 SOURCE_PLAN_ROWS 9 SOURCE_ROWSET_SHA256 c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b ROWSET_SHA256 98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d`

These observations are public-safe route metadata only. They do not accept parsers, people, denominators, state changes, URL rewrites, enrichment claims, or identity collapse.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_candidate_route_signal": {
    "official_route_current_roster_signal_needs_parser_scope_packet": 18
  },
  "by_fetch_status": {
    "fetched": 18
  },
  "by_final_or_fetch_domain": {
    "emergencymedicine.vumc.org": 8,
    "www.vumc.org": 10
  },
  "by_route_role": {
    "candidate_context": 9,
    "denominator": 9
  },
  "csv": "artifacts/data/vanderbilt_slice_2_live_route_observations.csv",
  "denominator_closure_allowed": false,
  "gbrain_approval_line": "APPROVE vanderbilt_slice_2_live_fetch_approval_request_packet_approved REQUEST_ROWS 9 SOURCE_PLAN_ROWS 9 SOURCE_ROWSET_SHA256 c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b ROWSET_SHA256 98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d",
  "gbrain_approval_status": "approved_exact_non_mutating_live_route_observation",
  "generated_at": "2026-06-09T11:27:16.915210+00:00",
  "identity_collapse_allowed": false,
  "json": "artifacts/data/vanderbilt_slice_2_live_route_observations.json",
  "markdown": "artifacts/research/vanderbilt-slice-2-live-route-observations-2026-06-09.md",
  "mutation_allowed": false,
  "not_approved": [
    "person_ingestion",
    "parser_acceptance",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "profile_fact_acceptance",
    "contact_fact_acceptance",
    "research_fact_acceptance",
    "raw_dump_publication",
    "unique_person_identity_collapse"
  ],
  "observation_rows": 18,
  "parser_acceptance_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Approved non-mutating Vanderbilt slice-2 live route-observation ledger. It fetches only bounded public official denominator and candidate-context route metadata from the nine approved request rows, records final URLs, hashes, booleans, and coarse signal counts, and stores no raw HTML, raw text, raw headings, raw anchor samples, raw candidate names, accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment/profile/contact/research-fact acceptance, or identity collapse.",
  "private_artifact_paths_committed": false,
  "public_safety_policy": "This ledger stores fetch metadata, hashes, booleans, and coarse link/signal counts only. Do not commit raw HTML/text/browser dumps, raw candidate names, or accepted person records from this observation lane.",
  "raw_dump_publication_allowed": false,
  "request_rows_represented": 9,
  "rowset_sha256": "c606878519468dacb24ba3579ddb382f3d234abea8048db4d57f5ede6a06bbf0",
  "school_verification_allowed": false,
  "source_approval_request_packet": "artifacts/data/vanderbilt_slice_2_live_fetch_approval_request_packet.csv",
  "source_approval_request_rows": 9,
  "source_approval_request_rowset_sha256": "98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d",
  "source_approval_request_summary": "artifacts/data/vanderbilt_slice_2_live_fetch_approval_request_packet_summary.json",
  "source_execution_plan_rowset_sha256": "c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b",
  "unique_observed_urls": 12,
  "url_rewrite_allowed": false,
  "web_fetch_approved_by_gbrain": true,
  "web_fetch_executed": true
}
```

## Observation Rows

| request | role | program | status | signal | http | final domain | current | resident | fellow | person links |
| ---: | --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| 1 | candidate_context | Plastic Surgery-Integrated | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 21 | 11 | 13 | 53 |
| 1 | denominator | Plastic Surgery-Integrated | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 22 | 21 | 12 | 17 |
| 2 | candidate_context | Adult and Pediatric Craniofacial | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 21 | 11 | 13 | 53 |
| 2 | denominator | Adult and Pediatric Craniofacial | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 46 | 10 | 41 | 50 |
| 3 | candidate_context | Hand Surgery (Plastic Surgery) | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 9 | 6 | 10 | 26 |
| 3 | denominator | Hand Surgery (Plastic Surgery) | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 10 | 10 | 13 | 16 |
| 4 | candidate_context | Plastic Surgery | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 21 | 11 | 13 | 53 |
| 4 | denominator | Plastic Surgery | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 10 | 10 | 13 | 16 |
| 5 | candidate_context | Emergency Medical Services | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | emergencymedicine.vumc.org | 65 | 33 | 58 | 0 |
| 5 | denominator | Emergency Medical Services | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | emergencymedicine.vumc.org | 7 | 4 | 2 | 0 |
| 6 | candidate_context | Emergency Medicine Simulation | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | emergencymedicine.vumc.org | 65 | 33 | 58 | 0 |
| 6 | denominator | Emergency Medicine Simulation | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | emergencymedicine.vumc.org | 7 | 4 | 2 | 0 |
| 7 | candidate_context | Emergency Medicine Ultrasound | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | emergencymedicine.vumc.org | 65 | 33 | 58 | 0 |
| 7 | denominator | Emergency Medicine Ultrasound | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | emergencymedicine.vumc.org | 7 | 4 | 2 | 0 |
| 8 | candidate_context | Genitourinary Reconstruction and Trauma | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 13 | 14 | 40 | 47 |
| 8 | denominator | Genitourinary Reconstruction and Trauma | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 5 | 5 | 19 | 5 |
| 9 | candidate_context | Global Emergency Medicine | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | emergencymedicine.vumc.org | 65 | 33 | 58 | 0 |
| 9 | denominator | Global Emergency Medicine | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | emergencymedicine.vumc.org | 7 | 4 | 2 | 0 |
