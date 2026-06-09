---
type: research-checkpoint
title: Vanderbilt Generalized Source Discovery Workbench
created_at: 2026-06-09T02:21:26.597659+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Generalized Source Discovery Workbench

## Boundary

Non-mutating Vanderbilt generalized source-discovery workbench. It searches and fetches official-domain candidate source evidence only. It authorizes no person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, profile enrichment, unsupported-label ingestion, research fact acceptance, or identity collapse.

## Summary

```json
{
  "by_candidate_status": {
    "official_candidate_current_roster_signal_needs_parser_review": 19,
    "official_candidate_roster_text_without_supported_people": 4,
    "official_context_no_current_roster_signal": 10,
    "official_context_or_negative_page_no_current_roster": 5
  },
  "by_confidence": {
    "high": 19,
    "low": 15,
    "medium": 4
  },
  "candidate_url_rows": 38,
  "csv": "artifacts/data/vanderbilt_targeted_gap_source_discovery_workbench.csv",
  "generated_at": "2026-06-09T02:21:26.597659+00:00",
  "json": "artifacts/data/vanderbilt_targeted_gap_source_discovery_workbench.json",
  "lanes": [
    "manual_rendered_review_or_targeted_source_discovery"
  ],
  "markdown": "artifacts/research/vanderbilt-targeted-gap-source-discovery-workbench-2026-06-08.md",
  "mutation_allowed": false,
  "observation_csv": "artifacts/data/vanderbilt_targeted_gap_source_discovery_search_observations.csv",
  "observation_rows": 81,
  "playbook_approval_effect": "top50_scraper_source_discovery_playbook_non_mutating_approved",
  "playbook_rowset_sha256": "1b33439d36c878a527294dea38b8662bc69d5634c4427ad21ffa878b3db1e355",
  "policy": "Non-mutating Vanderbilt generalized source-discovery workbench. It searches and fetches official-domain candidate source evidence only. It authorizes no person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, profile enrichment, unsupported-label ingestion, research fact acceptance, or identity collapse.",
  "programs_with_high_confidence_candidate": [
    "Academic General Pediatrics",
    "Advanced Endoscopy",
    "Advanced Inflammatory Bowel Disease",
    "Developmental-Behavioral Pediatrics",
    "Gastroenterology",
    "Neonatal-Perinatal Medicine",
    "Orthopaedic Surgery",
    "Pediatric Critical Care",
    "Pediatric Emergency Medicine",
    "Pediatric Endocrinology",
    "Pediatric Gastroenterology",
    "Pediatric Hospital Medicine",
    "Pediatric Infectious Diseases",
    "Pediatric Rheumatology",
    "Pediatrics",
    "Psychiatry",
    "Rheumatology",
    "Transplant Hepatology"
  ],
  "programs_with_medium_confidence_candidate": [
    "Academic General Pediatrics",
    "General Surgery",
    "Pediatric Gastroenterology"
  ],
  "query_csv": "artifacts/data/vanderbilt_targeted_gap_source_discovery_queries.csv",
  "query_rows": 76,
  "rowset_sha256": "dd72909d1f992209a414ef232d8c4d499de5de2a90cf45f49428153d1ebe1b71",
  "school_name": "VANDERBILT UNIVERSITY SCH OF MEDICINE",
  "target_gap_rows": 19,
  "workbench_rows": 38
}
```

## Candidate Rows

| program | status | confidence | roster | people | url | next action |
| --- | --- | --- | ---: | ---: | --- | --- |
| Academic General Pediatrics | official_candidate_current_roster_signal_needs_parser_review | high | 4 | 1 | https://pediatrics.vumc.org/general-pediatrics-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Academic General Pediatrics | official_candidate_roster_text_without_supported_people | medium | 2 | 0 | https://pediatrics.vumc.org/node/1106 | Run rendered/headed review or continue targeted source discovery before closure. |
| Advanced Endoscopy | official_candidate_current_roster_signal_needs_parser_review | high | 2 | 2 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/advanced-endoscopy-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Advanced Endoscopy | official_context_or_negative_page_no_current_roster | low | 0 | 7 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | Retain as negative/context evidence; continue discovery or prepare closure packet only with broader evidence. |
| Advanced Inflammatory Bowel Disease | official_candidate_current_roster_signal_needs_parser_review | high | 1 | 1 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/advanced-ibd-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Advanced Inflammatory Bowel Disease | official_context_or_negative_page_no_current_roster | low | 0 | 7 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | Retain as negative/context evidence; continue discovery or prepare closure packet only with broader evidence. |
| Developmental-Behavioral Pediatrics | official_candidate_current_roster_signal_needs_parser_review | high | 2 | 2 | https://pediatrics.vumc.org/developmental-behavioral-pediatrics-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Developmental-Behavioral Pediatrics | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/house-staff | Retain as context evidence and continue targeted source discovery. |
| Gastroenterology | official_candidate_current_roster_signal_needs_parser_review | high | 3 | 3 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/gastroenterology-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Gastroenterology | official_context_or_negative_page_no_current_roster | low | 0 | 7 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | Retain as negative/context evidence; continue discovery or prepare closure packet only with broader evidence. |
| General Surgery | official_candidate_roster_text_without_supported_people | medium | 4 | 0 | https://www.vumc.org/generalsurgeryresidency/ | Run rendered/headed review or continue targeted source discovery before closure. |
| General Surgery | official_candidate_roster_text_without_supported_people | medium | 6 | 0 | https://www.vumc.org/generalsurgeryresidency/current-residents | Run rendered/headed review or continue targeted source discovery before closure. |
| Neonatal-Perinatal Medicine | official_candidate_current_roster_signal_needs_parser_review | high | 3 | 1 | https://pediatrics.vumc.org/neonatal-perinatal-medicine-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Neonatal-Perinatal Medicine | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/tools-instructions-resources | Retain as context evidence and continue targeted source discovery. |
| Orthopaedic Surgery | official_candidate_current_roster_signal_needs_parser_review | high | 8 | 24 | https://www.vumc.org/ortho/node/193 | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Orthopaedic Surgery | official_candidate_current_roster_signal_needs_parser_review | high | 7 | 2 | https://www.vumc.org/ortho/residency-program | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatric Critical Care | official_candidate_current_roster_signal_needs_parser_review | high | 2 | 2 | https://pediatrics.vumc.org/critical-care-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatric Critical Care | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/house-staff | Retain as context evidence and continue targeted source discovery. |
| Pediatric Emergency Medicine | official_candidate_current_roster_signal_needs_parser_review | high | 3 | 6 | https://pediatrics.vumc.org/emergency-medicine-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatric Emergency Medicine | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/house-staff | Retain as context evidence and continue targeted source discovery. |
| Pediatric Endocrinology | official_candidate_current_roster_signal_needs_parser_review | high | 3 | 1 | https://pediatrics.vumc.org/endocrinology-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatric Endocrinology | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/house-staff | Retain as context evidence and continue targeted source discovery. |
| Pediatric Gastroenterology | official_candidate_current_roster_signal_needs_parser_review | high | 6 | 4 | https://pediatrics.vumc.org/gastroenterology-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatric Gastroenterology | official_candidate_roster_text_without_supported_people | medium | 1 | 0 | https://www.vumc.org/gme/ | Run rendered/headed review or continue targeted source discovery before closure. |
| Pediatric Hospital Medicine | official_candidate_current_roster_signal_needs_parser_review | high | 4 | 1 | https://pediatrics.vumc.org/hospital-medicine-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatric Hospital Medicine | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/house-staff | Retain as context evidence and continue targeted source discovery. |
| Pediatric Infectious Diseases | official_candidate_current_roster_signal_needs_parser_review | high | 4 | 2 | https://pediatrics.vumc.org/infectious-diseases-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatric Infectious Diseases | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/house-staff | Retain as context evidence and continue targeted source discovery. |
| Pediatric Rheumatology | official_candidate_current_roster_signal_needs_parser_review | high | 6 | 2 | https://pediatrics.vumc.org/rheumatology-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatric Rheumatology | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/house-staff | Retain as context evidence and continue targeted source discovery. |
| Pediatrics | official_candidate_current_roster_signal_needs_parser_review | high | 7 | 2 | https://pediatrics.vumc.org/residency | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Pediatrics | official_context_or_negative_page_no_current_roster | low | 0 | 44 | https://medicine.vumc.org/education/medicine-pediatrics-residency-program/med-peds-residents-directory | Retain as negative/context evidence; continue discovery or prepare closure packet only with broader evidence. |
| Psychiatry | official_candidate_current_roster_signal_needs_parser_review | high | 2 | 9 | https://www.vumc.org/psychiatry/vanderbilt-psychiatry-residency-program | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Psychiatry | official_context_no_current_roster_signal | low | 0 | 0 | https://www.vumc.org/psychiatry/sites/default/files/people/2024-2025%20Resident%20composite.pdf | Retain as context evidence and continue targeted source discovery. |
| Rheumatology | official_candidate_current_roster_signal_needs_parser_review | high | 6 | 2 | https://pediatrics.vumc.org/rheumatology-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Rheumatology | official_context_no_current_roster_signal | low | 0 | 1 | https://www.vumc.org/gme/house-staff | Retain as context evidence and continue targeted source discovery. |
| Transplant Hepatology | official_candidate_current_roster_signal_needs_parser_review | high | 2 | 12 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/transplant-hepatology-fellowship | Build exact parser/review packet for target-scope validation before any person ingestion. |
| Transplant Hepatology | official_context_or_negative_page_no_current_roster | low | 0 | 7 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/fellows | Retain as negative/context evidence; continue discovery or prepare closure packet only with broader evidence. |
