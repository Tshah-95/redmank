---
type: research-checkpoint
title: Vanderbilt Targeted Parser Scope Review Packet
created_at: 2026-06-09T02:50:42.489373+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Targeted Parser Scope Review Packet

## Boundary

Non-mutating Vanderbilt targeted parser/scope review packet. It queues official candidate pages for parser design, rendered review, link-follow review, or scope disposition. It authorizes no person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, profile enrichment, contact acceptance, research fact acceptance, or unique-person identity collapse.

## Registration Status

GBrain evidence registration status: `approved`.

If `pending_exact_gbrain_registration`, this packet is a draft source-review scaffold only. It must not be used for parser acceptance, person ingestion, denominator closure, or URL rewrites until the exact approval line is supplied and the packet is regenerated.

## Summary

```json
{
  "by_parser_readiness_status": {
    "linked_roster_candidate_needs_fetch_and_scope_review": 15,
    "linked_roster_candidate_scope_ambiguous": 4,
    "medium_signal_rendered_or_js_parser_review_required": 1
  },
  "by_parser_review_lane": {
    "follow_same_program_roster_link_before_parser": 15,
    "rendered_current_residents_scope_review": 1,
    "scope_ambiguous_roster_link_review": 4
  },
  "by_source_selection_reason": {
    "general_surgery_medium_current_residents_review_row": 1,
    "high_confidence_current_roster_signal": 19
  },
  "csv": "artifacts/data/vanderbilt_targeted_parser_scope_review_packet.csv",
  "gbrain_approval_effect": "vanderbilt_targeted_gap_source_discovery_evidence_registration_approved",
  "gbrain_registration_status": "approved",
  "generated_at": "2026-06-09T02:50:42.489373+00:00",
  "json": "artifacts/data/vanderbilt_targeted_parser_scope_review_packet.json",
  "markdown": "artifacts/research/vanderbilt-targeted-parser-scope-review-packet-2026-06-09.md",
  "mutation_allowed": false,
  "policy": "Non-mutating Vanderbilt targeted parser/scope review packet. It queues official candidate pages for parser design, rendered review, link-follow review, or scope disposition. It authorizes no person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, profile enrichment, contact acceptance, research fact acceptance, or unique-person identity collapse.",
  "review_rows": 20,
  "rowset_sha256": "dd7ba52cefcec632da434810653bce1b106696ca9a9d94fe3e517f206ae50785",
  "source_target_gap_rows": 19,
  "source_workbench": "artifacts/data/vanderbilt_targeted_gap_source_discovery_workbench.json",
  "source_workbench_rows": 38,
  "source_workbench_rowset_sha256": "dd72909d1f992209a414ef232d8c4d499de5de2a90cf45f49428153d1ebe1b71"
}
```

## Review Rows

| priority | program | confidence | lane | people | url | next action |
| ---: | --- | --- | --- | ---: | --- | --- |
| 10 | General Surgery | medium | rendered_current_residents_scope_review | 0 | https://www.vumc.org/generalsurgeryresidency/current-residents | Run rendered/headed review of the official current-residents route before parser acceptance or closure. |
| 8 | Academic General Pediatrics | high | follow_same_program_roster_link_before_parser | 1 | https://pediatrics.vumc.org/general-pediatrics-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Developmental-Behavioral Pediatrics | high | follow_same_program_roster_link_before_parser | 2 | https://pediatrics.vumc.org/developmental-behavioral-pediatrics-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Gastroenterology | high | follow_same_program_roster_link_before_parser | 3 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/gastroenterology-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Neonatal-Perinatal Medicine | high | follow_same_program_roster_link_before_parser | 1 | https://pediatrics.vumc.org/neonatal-perinatal-medicine-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Pediatric Critical Care | high | follow_same_program_roster_link_before_parser | 2 | https://pediatrics.vumc.org/critical-care-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Pediatric Emergency Medicine | high | follow_same_program_roster_link_before_parser | 6 | https://pediatrics.vumc.org/emergency-medicine-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Pediatric Endocrinology | high | follow_same_program_roster_link_before_parser | 1 | https://pediatrics.vumc.org/endocrinology-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Pediatric Gastroenterology | high | follow_same_program_roster_link_before_parser | 4 | https://pediatrics.vumc.org/gastroenterology-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Pediatric Hospital Medicine | high | follow_same_program_roster_link_before_parser | 1 | https://pediatrics.vumc.org/hospital-medicine-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Pediatric Infectious Diseases | high | follow_same_program_roster_link_before_parser | 2 | https://pediatrics.vumc.org/infectious-diseases-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Pediatric Rheumatology | high | follow_same_program_roster_link_before_parser | 2 | https://pediatrics.vumc.org/rheumatology-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Pediatrics | high | follow_same_program_roster_link_before_parser | 2 | https://pediatrics.vumc.org/residency | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Psychiatry | high | follow_same_program_roster_link_before_parser | 9 | https://www.vumc.org/psychiatry/vanderbilt-psychiatry-residency-program | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Rheumatology | high | follow_same_program_roster_link_before_parser | 2 | https://pediatrics.vumc.org/rheumatology-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 8 | Transplant Hepatology | high | follow_same_program_roster_link_before_parser | 12 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/transplant-hepatology-fellowship | Fetch and inspect the same-program roster link, then prepare exact parser acceptance or disposition. |
| 7 | Advanced Endoscopy | high | scope_ambiguous_roster_link_review | 2 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/advanced-endoscopy-fellowship | Review roster-link scope before treating this page as a parser source. |
| 7 | Advanced Inflammatory Bowel Disease | high | scope_ambiguous_roster_link_review | 1 | https://medicine.vumc.org/divisions/gastroenterology-hepatology-nutrition/education/advanced-ibd-fellowship | Review roster-link scope before treating this page as a parser source. |
| 7 | Orthopaedic Surgery | high | scope_ambiguous_roster_link_review | 24 | https://www.vumc.org/ortho/node/193 | Review roster-link scope before treating this page as a parser source. |
| 7 | Orthopaedic Surgery | high | scope_ambiguous_roster_link_review | 2 | https://www.vumc.org/ortho/residency-program | Review roster-link scope before treating this page as a parser source. |
