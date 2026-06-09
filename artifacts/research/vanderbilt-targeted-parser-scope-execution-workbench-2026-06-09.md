---
type: research-checkpoint
title: Vanderbilt Targeted Parser Scope Execution Workbench
created_at: 2026-06-09T04:24:30.829909+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Targeted Parser Scope Execution Workbench

## Boundary

Non-mutating Vanderbilt targeted parser/scope execution workbench. It routes approved review-packet rows to linked-route fetch, rendered review, parser-test design, or scope disposition. It authorizes no person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, profile enrichment, contact acceptance, research fact acceptance, or unique-person identity collapse.

This workbench is an execution queue only. It preserves the approved parser/scope review packet boundary and does not approve parser acceptance, people, denominator closure, URL rewrites, enrichment claims, or identity collapse.

## Summary

```json
{
  "approval_required_for": [
    "parser_acceptance",
    "person_ingestion",
    "denominator_closure",
    "training_state_mutation",
    "school_verification",
    "source_url_rewrite",
    "unsupported_label_ingestion",
    "profile_contact_research_fact_acceptance",
    "identity_collapse"
  ],
  "by_execution_lane": {
    "ambiguous_roster_link_scope_review": 4,
    "linked_roster_route_fetch": 15,
    "rendered_current_residents_review": 1
  },
  "by_execution_status": {
    "fetch_linked_route_before_parser_scope_packet": 15,
    "render_current_residents_route_before_general_surgery_disposition": 1,
    "review_linked_route_scope_before_parser": 4
  },
  "by_fetch_domain": {
    "medicine.vumc.org": 4,
    "pediatrics.vumc.org": 12,
    "www.vumc.org": 4
  },
  "by_recommended_next_packet": {
    "general_surgery_rendered_review_disposition_packet": 1,
    "linked_route_parser_acceptance_or_scope_disposition_packet": 15,
    "linked_route_scope_review_or_recourse_packet": 4
  },
  "csv": "artifacts/data/vanderbilt_targeted_parser_scope_execution_workbench.csv",
  "fetch_urls": [
    "https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows",
    "https://pediatrics.vumc.org/node/1106",
    "https://pediatrics.vumc.org/person/current-developmental-behavioral-pediatrics-fellows",
    "https://pediatrics.vumc.org/person/current-neonatal-perinatal-medicine-fellows",
    "https://pediatrics.vumc.org/person/current-pediatric-critical-care-fellows",
    "https://pediatrics.vumc.org/person/current-pediatric-endocrinology-fellows",
    "https://pediatrics.vumc.org/person/current-pediatric-gastroenterology-hepatology-and-nutrition-fellows",
    "https://pediatrics.vumc.org/person/current-pediatric-hospital-medicine-fellows",
    "https://pediatrics.vumc.org/person/current-rheumatology-fellows",
    "https://pediatrics.vumc.org/person/emergency-medicine-fellows",
    "https://pediatrics.vumc.org/person/infectious-diseases-fellowship/fellows",
    "https://pediatrics.vumc.org/person/pgy-1",
    "https://www.vumc.org/generalsurgeryresidency/current-residents",
    "https://www.vumc.org/ortho/2022-residency-match",
    "https://www.vumc.org/ortho/node/193",
    "https://www.vumc.org/psychiatry/post-graduate-year-1-pgy1"
  ],
  "generated_at": "2026-06-09T04:24:30.829909+00:00",
  "json": "artifacts/data/vanderbilt_targeted_parser_scope_execution_workbench.json",
  "markdown": "artifacts/research/vanderbilt-targeted-parser-scope-execution-workbench-2026-06-09.md",
  "mutation_allowed": false,
  "not_approved": [
    "person_ingestion",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "profile_contact_research_fact_acceptance",
    "unique_person_identity_collapse"
  ],
  "policy": "Non-mutating Vanderbilt targeted parser/scope execution workbench. It routes approved review-packet rows to linked-route fetch, rendered review, parser-test design, or scope disposition. It authorizes no person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, profile enrichment, contact acceptance, research fact acceptance, or unique-person identity collapse.",
  "public_safety_policy": "Commit this deterministic queue and summaries only. Do not commit raw rendered browser dumps, GBrain HTTP responses, debug databases, or private scratch captures.",
  "rowset_sha256": "b9f7addcc552747c3b0d12459d5055efd60a08d610996aeeeff0a8ea095b2f3b",
  "source_gbrain_registration_status": "approved",
  "source_packet_csv": "artifacts/data/vanderbilt_targeted_parser_scope_review_packet.csv",
  "source_packet_json": "artifacts/data/vanderbilt_targeted_parser_scope_review_packet.json",
  "source_packet_rowset_sha256": "dd7ba52cefcec632da434810653bce1b106696ca9a9d94fe3e517f206ae50785",
  "source_packet_summary": "artifacts/data/vanderbilt_targeted_parser_scope_review_packet_summary.json",
  "source_review_rows": 20,
  "source_workbench_rowset_sha256": "dd72909d1f992209a414ef232d8c4d499de5de2a90cf45f49428153d1ebe1b71",
  "unique_fetch_urls": 16,
  "workbench_rows": 20
}
```

## Execution Rows

| priority | program | lane | status | fetch url | next packet |
| ---: | --- | --- | --- | --- | --- |
| 90 | Academic General Pediatrics | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/node/1106 | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Developmental-Behavioral Pediatrics | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/current-developmental-behavioral-pediatrics-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Gastroenterology | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Neonatal-Perinatal Medicine | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/current-neonatal-perinatal-medicine-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Pediatric Critical Care | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/current-pediatric-critical-care-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Pediatric Emergency Medicine | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/emergency-medicine-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Pediatric Endocrinology | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/current-pediatric-endocrinology-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Pediatric Gastroenterology | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/current-pediatric-gastroenterology-hepatology-and-nutrition-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Pediatric Hospital Medicine | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/current-pediatric-hospital-medicine-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Pediatric Infectious Diseases | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/infectious-diseases-fellowship/fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Pediatric Rheumatology | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/current-rheumatology-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Pediatrics | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/pgy-1 | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Psychiatry | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://www.vumc.org/psychiatry/post-graduate-year-1-pgy1 | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Rheumatology | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://pediatrics.vumc.org/person/current-rheumatology-fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 90 | Transplant Hepatology | linked_roster_route_fetch | fetch_linked_route_before_parser_scope_packet | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | linked_route_parser_acceptance_or_scope_disposition_packet |
| 80 | Advanced Endoscopy | ambiguous_roster_link_scope_review | review_linked_route_scope_before_parser | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | linked_route_scope_review_or_recourse_packet |
| 80 | Advanced Inflammatory Bowel Disease | ambiguous_roster_link_scope_review | review_linked_route_scope_before_parser | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | linked_route_scope_review_or_recourse_packet |
| 80 | Orthopaedic Surgery | ambiguous_roster_link_scope_review | review_linked_route_scope_before_parser | https://www.vumc.org/ortho/2022-residency-match | linked_route_scope_review_or_recourse_packet |
| 80 | Orthopaedic Surgery | ambiguous_roster_link_scope_review | review_linked_route_scope_before_parser | https://www.vumc.org/ortho/node/193 | linked_route_scope_review_or_recourse_packet |
| 75 | General Surgery | rendered_current_residents_review | render_current_residents_route_before_general_surgery_disposition | https://www.vumc.org/generalsurgeryresidency/current-residents | general_surgery_rendered_review_disposition_packet |
