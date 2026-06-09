---
type: research-checkpoint
title: Vanderbilt Parser Scope Execution Evidence
created_at: 2026-06-09T04:57:19.763645+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Parser Scope Execution Evidence

## Boundary

Non-mutating Vanderbilt parser/scope execution evidence. This ledger records parser strategy, scope status, route freshness, hashes, and coarse candidate counts for approved next-packet rows. It stores no raw HTML, raw text, raw headings, raw anchor samples, accepted people, parser-accepted person rows, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "by_approved_followup_artifact": {
    "general_surgery_rendered_parser_scope_packet": 1,
    "linked_route_scope_disposition_packet": 3,
    "route_retry_or_source_discovery_recourse_packet": 1,
    "source_specific_parser_build_review_packet": 15
  },
  "by_approved_next_artifact_lane": {
    "general_surgery_rendered_parser_scope_packet": 1,
    "linked_route_scope_disposition_packet": 3,
    "route_retry_or_recourse_packet": 1,
    "source_specific_parser_build_review_packet": 15
  },
  "by_parser_family": {
    "http_error_recourse": 1,
    "vumc_general_surgery_current_residents_rendered_review": 1,
    "vumc_medicine_division_fellows_shared_page": 4,
    "vumc_orthopaedics_current_residents_page": 1,
    "vumc_pediatrics_node_listing_page": 1,
    "vumc_pediatrics_person_listing_page": 11,
    "vumc_pgy_listing_page": 1
  },
  "by_parser_probe_status": {
    "parser_build_review_ready_candidate_entity_counts": 15,
    "recourse_http_route_retry_or_replace_source": 1,
    "rendered_review_ready_current_resident_signal": 1,
    "scope_disposition_ready_current_roster_context": 3
  },
  "by_route_hash_matches_prior_observation": {
    "true": 20
  },
  "csv": "artifacts/data/vanderbilt_parser_scope_execution_evidence.csv",
  "denominator_closure_allowed": false,
  "execution_evidence_rows": 20,
  "generated_at": "2026-06-09T04:57:19.763645+00:00",
  "json": "artifacts/data/vanderbilt_parser_scope_execution_evidence.json",
  "markdown": "artifacts/research/vanderbilt-parser-scope-execution-evidence-2026-06-09.md",
  "mutation_allowed": false,
  "parser_acceptance_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt parser/scope execution evidence. This ledger records parser strategy, scope status, route freshness, hashes, and coarse candidate counts for approved next-packet rows. It stores no raw HTML, raw text, raw headings, raw anchor samples, accepted people, parser-accepted person rows, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "rowset_sha256": "db7e7c7b03c31c20a6b3b9c2a17da2d24cbf0c725f97872452db63a2e5942812",
  "source_approved_next_packet_rowset_sha256": "098c0a813eb577552b46e9454fbf2e9088bcee228d0aa678827439eba082e261",
  "source_approved_next_packet_summary": "artifacts/data/vanderbilt_approved_parser_scope_next_packet_summary.json",
  "source_approved_next_packets": "artifacts/data/vanderbilt_approved_parser_scope_next_packets.json",
  "source_next_packet_rows": 20,
  "total_candidate_entity_count": 348,
  "unique_fetch_urls": 16
}
```

## Evidence Rows

| program | lane | parser family | probe status | candidates | people allowed | fetch url |
| --- | --- | --- | --- | ---: | --- | --- |
| General Surgery | general_surgery_rendered_parser_scope_packet | vumc_general_surgery_current_residents_rendered_review | rendered_review_ready_current_resident_signal | 5 | false | https://www.vumc.org/generalsurgeryresidency/current-residents |
| Advanced Endoscopy | linked_route_scope_disposition_packet | vumc_medicine_division_fellows_shared_page | scope_disposition_ready_current_roster_context | 10 | false | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Advanced Inflammatory Bowel Disease | linked_route_scope_disposition_packet | vumc_medicine_division_fellows_shared_page | scope_disposition_ready_current_roster_context | 10 | false | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Orthopaedic Surgery | linked_route_scope_disposition_packet | vumc_orthopaedics_current_residents_page | scope_disposition_ready_current_roster_context | 16 | false | https://www.vumc.org/ortho/node/193 |
| Orthopaedic Surgery | route_retry_or_recourse_packet | http_error_recourse | recourse_http_route_retry_or_replace_source | 16 | false | https://www.vumc.org/ortho/2022-residency-match |
| Academic General Pediatrics | source_specific_parser_build_review_packet | vumc_pediatrics_node_listing_page | parser_build_review_ready_candidate_entity_counts | 6 | false | https://pediatrics.vumc.org/node/1106 |
| Developmental-Behavioral Pediatrics | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 12 | false | https://pediatrics.vumc.org/person/current-developmental-behavioral-pediatrics-fellows |
| Gastroenterology | source_specific_parser_build_review_packet | vumc_medicine_division_fellows_shared_page | parser_build_review_ready_candidate_entity_counts | 10 | false | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Neonatal-Perinatal Medicine | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 34 | false | https://pediatrics.vumc.org/person/current-neonatal-perinatal-medicine-fellows |
| Pediatric Critical Care | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 26 | false | https://pediatrics.vumc.org/person/current-pediatric-critical-care-fellows |
| Pediatric Emergency Medicine | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 30 | false | https://pediatrics.vumc.org/person/emergency-medicine-fellows |
| Pediatric Endocrinology | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 8 | false | https://pediatrics.vumc.org/person/current-pediatric-endocrinology-fellows |
| Pediatric Gastroenterology | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 17 | false | https://pediatrics.vumc.org/person/current-pediatric-gastroenterology-hepatology-and-nutrition-fellows |
| Pediatric Hospital Medicine | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 12 | false | https://pediatrics.vumc.org/person/current-pediatric-hospital-medicine-fellows |
| Pediatric Infectious Diseases | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 16 | false | https://pediatrics.vumc.org/person/infectious-diseases-fellowship/fellows |
| Pediatric Rheumatology | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 12 | false | https://pediatrics.vumc.org/person/current-rheumatology-fellows |
| Pediatrics | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 69 | false | https://pediatrics.vumc.org/person/pgy-1 |
| Psychiatry | source_specific_parser_build_review_packet | vumc_pgy_listing_page | parser_build_review_ready_candidate_entity_counts | 17 | false | https://www.vumc.org/psychiatry/post-graduate-year-1-pgy1 |
| Rheumatology | source_specific_parser_build_review_packet | vumc_pediatrics_person_listing_page | parser_build_review_ready_candidate_entity_counts | 12 | false | https://pediatrics.vumc.org/person/current-rheumatology-fellows |
| Transplant Hepatology | source_specific_parser_build_review_packet | vumc_medicine_division_fellows_shared_page | parser_build_review_ready_candidate_entity_counts | 10 | false | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
