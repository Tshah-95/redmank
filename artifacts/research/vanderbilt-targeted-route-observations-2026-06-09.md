---
type: research-checkpoint
title: Vanderbilt Targeted Route Observations
created_at: 2026-06-09T04:29:32.373163+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Targeted Route Observations

## Boundary

Non-mutating Vanderbilt targeted route observation ledger. It records fetch status, final URL, hashes, title/heading booleans, and coarse current-roster route signals for official public pages. It stores no raw browser dump, raw HTML dump, raw text dump, raw headings, raw anchor samples, accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, or identity collapse.

These observations are public-safe route evidence only. They do not accept parsers, people, denominators, state changes, URL rewrites, enrichment claims, or identity collapse.

## Summary

```json
{
  "by_candidate_route_signal": {
    "http_error_needs_retry_or_recourse": 1,
    "official_route_current_roster_signal_needs_parser_scope_packet": 19
  },
  "by_fetch_status": {
    "fetched": 20
  },
  "by_final_or_fetch_domain": {
    "medicine.vumc.org": 4,
    "pediatrics.vumc.org": 12,
    "www.vumc.org": 4
  },
  "csv": "artifacts/data/vanderbilt_targeted_route_observations.csv",
  "generated_at": "2026-06-09T04:29:32.373163+00:00",
  "json": "artifacts/data/vanderbilt_targeted_route_observations.json",
  "markdown": "artifacts/research/vanderbilt-targeted-route-observations-2026-06-09.md",
  "mutation_allowed": false,
  "not_approved": [
    "person_ingestion",
    "parser_acceptance",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "profile_contact_research_fact_acceptance",
    "unique_person_identity_collapse"
  ],
  "observation_rows": 20,
  "policy": "Non-mutating Vanderbilt targeted route observation ledger. It records fetch status, final URL, hashes, title/heading booleans, and coarse current-roster route signals for official public pages. It stores no raw browser dump, raw HTML dump, raw text dump, raw headings, raw anchor samples, accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, or identity collapse.",
  "public_safety_policy": "This ledger stores fetch metadata, hashes, title/heading booleans, and coarse link/signal counts only. Do not commit raw HTML/text/browser dumps or accepted person records from this observation lane.",
  "rowset_sha256": "f547a298bf0efdaba630aa9d184ecd85979d0356039bbbd92d3c2fd026745258",
  "source_execution_rows": 20,
  "source_execution_workbench": "artifacts/data/vanderbilt_targeted_parser_scope_execution_workbench.json",
  "source_execution_workbench_rowset_sha256": "b9f7addcc552747c3b0d12459d5055efd60a08d610996aeeeff0a8ea095b2f3b",
  "source_execution_workbench_summary": "artifacts/data/vanderbilt_targeted_parser_scope_execution_workbench_summary.json",
  "source_unique_fetch_urls": 16,
  "unique_observed_urls": 16
}
```

## Observation Rows

| program | status | signal | http | final domain | current | resident | fellow | person links | fetch url |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | --- |
| Orthopaedic Surgery | fetched | http_error_needs_retry_or_recourse | 404 | www.vumc.org | 2 | 9 | 2 | 16 | https://www.vumc.org/ortho/2022-residency-match |
| Academic General Pediatrics | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 10 | 0 | 7 | 6 | https://pediatrics.vumc.org/node/1106 |
| Advanced Endoscopy | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | medicine.vumc.org | 26 | 6 | 24 | 0 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Advanced Inflammatory Bowel Disease | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | medicine.vumc.org | 26 | 6 | 24 | 0 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| Developmental-Behavioral Pediatrics | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 8 | 2 | 8 | 12 | https://pediatrics.vumc.org/person/current-developmental-behavioral-pediatrics-fellows |
| Gastroenterology | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | medicine.vumc.org | 26 | 6 | 24 | 0 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
| General Surgery | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 21 | 21 | 4 | 4 | https://www.vumc.org/generalsurgeryresidency/current-residents |
| Neonatal-Perinatal Medicine | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 25 | 13 | 23 | 34 | https://pediatrics.vumc.org/person/current-neonatal-perinatal-medicine-fellows |
| Orthopaedic Surgery | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 15 | 20 | 2 | 16 | https://www.vumc.org/ortho/node/193 |
| Pediatric Critical Care | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 23 | 12 | 24 | 26 | https://pediatrics.vumc.org/person/current-pediatric-critical-care-fellows |
| Pediatric Emergency Medicine | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 22 | 12 | 22 | 30 | https://pediatrics.vumc.org/person/emergency-medicine-fellows |
| Pediatric Endocrinology | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 7 | 0 | 7 | 8 | https://pediatrics.vumc.org/person/current-pediatric-endocrinology-fellows |
| Pediatric Gastroenterology | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 17 | 7 | 16 | 17 | https://pediatrics.vumc.org/person/current-pediatric-gastroenterology-hepatology-and-nutrition-fellows |
| Pediatric Hospital Medicine | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 8 | 2 | 8 | 12 | https://pediatrics.vumc.org/person/current-pediatric-hospital-medicine-fellows |
| Pediatric Infectious Diseases | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 17 | 5 | 14 | 16 | https://pediatrics.vumc.org/person/infectious-diseases-fellowship/fellows |
| Pediatric Rheumatology | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 8 | 2 | 8 | 12 | https://pediatrics.vumc.org/person/current-rheumatology-fellows |
| Pediatrics | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 9 | 11 | 0 | 69 | https://pediatrics.vumc.org/person/pgy-1 |
| Psychiatry | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | www.vumc.org | 26 | 26 | 2 | 17 | https://www.vumc.org/psychiatry/post-graduate-year-1-pgy1 |
| Rheumatology | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | pediatrics.vumc.org | 8 | 2 | 8 | 12 | https://pediatrics.vumc.org/person/current-rheumatology-fellows |
| Transplant Hepatology | fetched | official_route_current_roster_signal_needs_parser_scope_packet | 200 | medicine.vumc.org | 26 | 6 | 24 | 0 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows |
