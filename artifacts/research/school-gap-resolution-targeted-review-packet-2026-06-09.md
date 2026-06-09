---
type: research-checkpoint
title: School Gap Resolution Targeted Review Packet
created_at: 2026-06-09T07:40:20.307140+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# School Gap Resolution Targeted Review Packet

## Boundary

Non-mutating targeted Vanderbilt gap review packet. It copies the committed blank review template, fills only candidate-evidence planning fields for the 19 targeted workbench gaps, and keeps candidate URLs as later-review evidence. It does not fetch pages, accept people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "blank_review_rows": 94,
  "by_action": {
    "rendered_or_manual_review_needed": 1,
    "route_inspection_needed": 18
  },
  "by_candidate_status": {
    "official_candidate_current_roster_signal_needs_parser_review": 18,
    "official_candidate_roster_text_without_supported_people": 1
  },
  "by_confidence": {
    "high": 18,
    "medium": 1
  },
  "candidate_evidence_only": true,
  "csv": "artifacts/data/school_gap_resolution_targeted_review_packet.csv",
  "denominator_closure_allowed": false,
  "filled_review_rows": 19,
  "generated_at": "2026-06-09T07:40:20.307140+00:00",
  "identity_collapse_allowed": false,
  "json": "artifacts/data/school_gap_resolution_targeted_review_packet.json",
  "markdown": "artifacts/research/school-gap-resolution-targeted-review-packet-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating targeted Vanderbilt gap review packet. It copies the committed blank review template, fills only candidate-evidence planning fields for the 19 targeted workbench gaps, and keeps candidate URLs as later-review evidence. It does not fetch pages, accept people, close denominators, verify Vanderbilt, rewrite URLs, accept enrichment facts, or collapse identities.",
  "review_packet_rows": 113,
  "rowset_sha256": "d2e85a18ae738930a5371e48e30615663e14fbcd8d7199f2bdbe059b38728607",
  "school_verification_allowed": false,
  "source_template_rowset_sha256": "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782",
  "source_workbench_rowset_sha256": "dd72909d1f992209a414ef232d8c4d499de5de2a90cf45f49428153d1ebe1b71",
  "target_gap_rows": 19,
  "url_rewrite_allowed": false,
  "validation_command": "python3 scripts/validate_school_gap_resolution_review_template.py --input artifacts/data/school_gap_resolution_targeted_review_packet.csv --summary artifacts/data/school_gap_resolution_targeted_review_packet_validation_summary.json"
}
```

## Filled Rows

| program | action | confidence | candidate |
| --- | --- | --- | --- |
| Orthopaedic Surgery | route_inspection_needed | high | https://www.vumc.org/ortho/node/193 |
| Psychiatry | route_inspection_needed | high | https://www.vumc.org/psychiatry/vanderbilt-psychiatry-residency-program |
| General Surgery | rendered_or_manual_review_needed | medium | https://www.vumc.org/generalsurgeryresidency/current-residents |
| Pediatrics | route_inspection_needed | high | https://pediatrics.vumc.org/residency |
| Advanced Endoscopy | route_inspection_needed | high | https://medicine.vumc.org/advanced-endoscopy-fellowship |
| Advanced Inflammatory Bowel Disease | route_inspection_needed | high | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/advanced-ibd-fellowship |
| Developmental-Behavioral Pediatrics | route_inspection_needed | high | https://pediatrics.vumc.org/developmental-behavioral-pediatrics-fellowship |
| Gastroenterology | route_inspection_needed | high | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/gastroenterology-fellowship |
| Neonatal-Perinatal Medicine | route_inspection_needed | high | https://pediatrics.vumc.org/neonatal-perinatal-medicine-fellowship |
| Pediatric Critical Care | route_inspection_needed | high | https://pediatrics.vumc.org/critical-care-fellowship |
| Pediatric Emergency Medicine | route_inspection_needed | high | https://pediatrics.vumc.org/emergency-medicine-fellowship |
| Pediatric Endocrinology | route_inspection_needed | high | https://pediatrics.vumc.org/endocrinology-fellowship |
| Pediatric Gastroenterology | route_inspection_needed | high | https://pediatrics.vumc.org/gastroenterology-fellowship |
| Pediatric Hospital Medicine | route_inspection_needed | high | https://pediatrics.vumc.org/hospital-medicine-fellowship |
| Pediatric Infectious Diseases | route_inspection_needed | high | https://pediatrics.vumc.org/infectious-diseases-fellowship |
| Pediatric Rheumatology | route_inspection_needed | high | https://pediatrics.vumc.org/rheumatology-fellowship |
| Rheumatology | route_inspection_needed | high | https://pediatrics.vumc.org/rheumatology-fellowship |
| Transplant Hepatology | route_inspection_needed | high | https://medicine.vumc.org/transplant-hepatology-fellowship |
| Academic General Pediatrics | route_inspection_needed | high | https://pediatrics.vumc.org/general-pediatrics-fellowship |
