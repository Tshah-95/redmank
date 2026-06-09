---
type: research-checkpoint
title: Vanderbilt Parser Scope Decision Packets
created_at: 2026-06-09T04:59:54.749106+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Parser Scope Decision Packets

## Boundary

Non-mutating Vanderbilt parser-family spec and scope/recourse decision packet. It turns approved execution evidence into parser-family specifications, scope dispositions, General Surgery rendered-review disposition, and route recourse decisions. It does not approve parser implementation as accepted people, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "by_decision_lane": {
    "general_surgery_rendered_decision": 1,
    "linked_route_scope_decision": 3,
    "parser_family_spec": 15,
    "route_recourse_decision": 1
  },
  "by_decision_status": {
    "candidate_only_parser_spec_ready_for_exact_implementation_approval": 15,
    "http_error_recourse_ready": 1,
    "rendered_current_residents_parser_scope_ready": 1,
    "same_program_scope_disposition_ready": 1,
    "shared_source_scope_disposition_ready": 2
  },
  "by_next_required_approval": {
    "exact_general_surgery_parser_build_or_candidate_extraction_approval_required": 1,
    "exact_parser_implementation_or_candidate_extraction_approval_required": 15,
    "exact_route_replacement_or_unresolved_gap_closure_approval_required": 1,
    "exact_scope_disposition_acceptance_or_parser_build_approval_required": 3
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
  "csv": "artifacts/data/vanderbilt_parser_scope_decision_packets.csv",
  "decision_rows": 20,
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T04:59:54.749106+00:00",
  "json": "artifacts/data/vanderbilt_parser_scope_decision_packets.json",
  "markdown": "artifacts/research/vanderbilt-parser-scope-decision-packets-2026-06-09.md",
  "mutation_allowed": false,
  "parser_acceptance_allowed": false,
  "parser_implementation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt parser-family spec and scope/recourse decision packet. It turns approved execution evidence into parser-family specifications, scope dispositions, General Surgery rendered-review disposition, and route recourse decisions. It does not approve parser implementation as accepted people, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "rowset_sha256": "aa94351eae7a7309d2b760a891f69538d8a8998058fc1ceb24af3d2b918644b8",
  "source_execution_evidence": "artifacts/data/vanderbilt_parser_scope_execution_evidence.json",
  "source_execution_evidence_rows": 20,
  "source_execution_evidence_rowset_sha256": "db7e7c7b03c31c20a6b3b9c2a17da2d24cbf0c725f97872452db63a2e5942812",
  "source_execution_evidence_summary": "artifacts/data/vanderbilt_parser_scope_execution_evidence_summary.json"
}
```

## Decision Rows

| program | lane | status | parser family | scope decision | next approval |
| --- | --- | --- | --- | --- | --- |
| General Surgery | general_surgery_rendered_decision | rendered_current_residents_parser_scope_ready | vumc_general_surgery_current_residents_rendered_review | general_surgery_current_residents_route_has_current_resident_signal | exact_general_surgery_parser_build_or_candidate_extraction_approval_required |
| Advanced Endoscopy | linked_route_scope_decision | shared_source_scope_disposition_ready | vumc_medicine_division_fellows_shared_page | shared_gastroenterology_fellows_route_requires_subscope_before_parser_build | exact_scope_disposition_acceptance_or_parser_build_approval_required |
| Advanced Inflammatory Bowel Disease | linked_route_scope_decision | shared_source_scope_disposition_ready | vumc_medicine_division_fellows_shared_page | shared_gastroenterology_fellows_route_requires_subscope_before_parser_build | exact_scope_disposition_acceptance_or_parser_build_approval_required |
| Orthopaedic Surgery | linked_route_scope_decision | same_program_scope_disposition_ready | vumc_orthopaedics_current_residents_page | same_program_current_residents_route_candidate_for_parser_build_review | exact_scope_disposition_acceptance_or_parser_build_approval_required |
| Academic General Pediatrics | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_node_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Developmental-Behavioral Pediatrics | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Gastroenterology | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_medicine_division_fellows_shared_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Neonatal-Perinatal Medicine | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Pediatric Critical Care | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Pediatric Emergency Medicine | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Pediatric Endocrinology | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Pediatric Gastroenterology | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Pediatric Hospital Medicine | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Pediatric Infectious Diseases | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Pediatric Rheumatology | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Pediatrics | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Psychiatry | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pgy_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Rheumatology | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_pediatrics_person_listing_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Transplant Hepatology | parser_family_spec | candidate_only_parser_spec_ready_for_exact_implementation_approval | vumc_medicine_division_fellows_shared_page | same_program_current_roster_signal_for_parser_spec | exact_parser_implementation_or_candidate_extraction_approval_required |
| Orthopaedic Surgery | route_recourse_decision | http_error_recourse_ready | http_error_recourse | not_parser_scope_candidate | exact_route_replacement_or_unresolved_gap_closure_approval_required |
