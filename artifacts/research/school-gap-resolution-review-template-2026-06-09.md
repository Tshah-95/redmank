---
type: research-checkpoint
title: School Gap Resolution Review Template
created_at: 2026-06-09T07:27:25.988119+00:00
project: top-50-medical-school-roster-engine
---

# School Gap Resolution Review Template

## Boundary

Non-mutating school gap-resolution review template. It gives public contributors blank fields for source-discovery planning and packet-prep notes over committed Vanderbilt gap packets. It does not fetch pages, accept candidate URLs as official truth, ingest people, close denominators, verify schools, rewrite URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "allowed_review_actions": [
    "candidate_official_source_for_later_probe",
    "source_discovery_query_only",
    "route_inspection_needed",
    "rendered_or_manual_review_needed",
    "scope_disposition_packet_needed",
    "no_public_roster_closure_packet_needed",
    "defer_needs_more_context"
  ],
  "batch_rows_represented": 21,
  "blank_action_rows": 113,
  "blank_review_fields": {
    "confirm_candidate_evidence_only": 113,
    "confirm_no_denominator_closure": 113,
    "confirm_no_identity_collapse": 113,
    "confirm_no_person_ingestion": 113,
    "confirm_no_school_verification": 113,
    "confirm_no_url_rewrite": 113,
    "proposed_candidate_official_url": 113,
    "proposed_evidence_summary": 113,
    "proposed_non_mutating_review_action": 113,
    "proposed_output_artifact": 113,
    "proposed_source_discovery_query": 113
  },
  "by_next_operator_lane": {
    "headed_refetch": 1,
    "linked_route_inspection_after_related_scope_source_discovery": 2,
    "manual_current_scope_review_packet": 7,
    "manual_rendered_review_or_targeted_source_discovery": 19,
    "manual_url_confirmation_after_official_context_resolution": 4,
    "program_page_probe": 9,
    "rendered_parser_manual_repair_after_official_url_probe": 1,
    "rendered_parser_manual_review_after_related_scope_source_discovery": 7,
    "second_hop_route_inspection_after_official_url_probe": 1,
    "shared_source_program_scope_review_packet": 5,
    "target_program_source_discovery_after_exclusion": 16,
    "target_program_source_discovery_after_mixed_negative_evidence": 9,
    "target_program_source_discovery_after_non_current_exclusion": 1,
    "target_program_source_discovery_after_official_url_probe_exclusion": 1,
    "target_program_source_discovery_after_official_url_probe_related_scope": 1,
    "target_program_source_discovery_after_parser_exclusion": 7,
    "targeted_source_discovery_after_parent_url_resolution": 8,
    "targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe": 4,
    "targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery": 2,
    "targeted_source_discovery_or_no_public_roster_closure_packet": 8
  },
  "by_packet_status": {
    "parser_or_manual_review_gap_packet": 23,
    "related_scope_gap_packet": 5,
    "school_gap_resolution_packet": 15,
    "source_discovery_gap_packet": 65,
    "url_repair_gap_packet": 5
  },
  "csv": "artifacts/data/school_gap_resolution_review_template.csv",
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T07:27:25.988119+00:00",
  "identity_collapse_allowed": false,
  "json": "artifacts/data/school_gap_resolution_review_template.json",
  "markdown": "artifacts/research/school-gap-resolution-review-template-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating school gap-resolution review template. It gives public contributors blank fields for source-discovery planning and packet-prep notes over committed Vanderbilt gap packets. It does not fetch pages, accept candidate URLs as official truth, ingest people, close denominators, verify schools, rewrite URLs, accept enrichment facts, or collapse identities.",
  "private_artifact_paths_committed": false,
  "public_urls_may_be_present": true,
  "review_template_rows": 113,
  "reviewer_note_column_committed": false,
  "rowset_sha256": "537cb74b062b074b7b7bdb9a73fd14675c6cefbf5f2f4bbd72c54ffb56da0782",
  "school_verification_allowed": false,
  "source_packet_summary": "artifacts/data/school_gap_resolution_batch_packet_summary.json",
  "source_slice_index_rowset_sha256": "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75",
  "source_slice_index_summary": "artifacts/data/school_gap_resolution_batch_slice_index_summary.json",
  "url_rewrite_allowed": false,
  "valid_non_mutating_review_rows": 0
}
```

## Template Rows

| order | program | lane | status | action |
| ---: | --- | --- | --- | --- |
| 1 | Plastic Surgery-Integrated | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 1 | Adult and Pediatric Craniofacial | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 1 | Hand Surgery (Plastic Surgery) | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 1 | Plastic Surgery | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 1 | Emergency Medical Services | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 1 | Emergency Medicine Simulation | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 1 | Emergency Medicine Ultrasound | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 1 | Genitourinary Reconstruction and Trauma | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 1 | Global Emergency Medicine | target_program_source_discovery_after_mixed_negative_evidence | blank_pending_non_mutating_review_input |  |
| 2 | Orthopaedic Surgery | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Psychiatry | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | General Surgery | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Pediatrics | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Advanced Endoscopy | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Advanced Inflammatory Bowel Disease | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Developmental-Behavioral Pediatrics | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Gastroenterology | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Neonatal-Perinatal Medicine | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Pediatric Critical Care | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Pediatric Emergency Medicine | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Pediatric Endocrinology | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Pediatric Gastroenterology | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Pediatric Hospital Medicine | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Pediatric Infectious Diseases | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Pediatric Rheumatology | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Rheumatology | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 2 | Transplant Hepatology | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 3 | Laboratory Genetics & Genomics | linked_route_inspection_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 3 | Pediatric Pathology | linked_route_inspection_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 4 | Academic General Pediatrics | manual_rendered_review_or_targeted_source_discovery | blank_pending_non_mutating_review_input |  |
| 5 | Addiction Medicine | rendered_parser_manual_review_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 5 | Genitourinary Pathology | rendered_parser_manual_review_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 5 | Renal Pathology | rendered_parser_manual_review_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 5 | Spine and Muscoskeletal Rehab | rendered_parser_manual_review_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 5 | Functional and Stereotactic Neurosurgery | rendered_parser_manual_review_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 5 | Pediatric Neurosurgery | rendered_parser_manual_review_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 5 | Thoracic Surgery | rendered_parser_manual_review_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 6 | Movement Disorders | shared_source_program_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 6 | Neuroimmunology | shared_source_program_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 6 | Neuromuscular Medicine | shared_source_program_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 6 | Complex Benign Gynecology | shared_source_program_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 6 | Maternal-Fetal Medicine | shared_source_program_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 7 | Dialysis | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Facial Plastic & Reconstructive Surgery | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Hand Surgery (Orthopaedic Surgery) | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Head and Neck | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | LGBTQ Health | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Laryngology | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Musculoskeletal Oncology | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Neurotology | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Nutrition and Metabolic Disease | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Orthopaedic Adult Reconstructive Surgery | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Orthopaedic Spine | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Orthopaedic Sports Medicine | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Orthopaedic Trauma | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Pediatric Orthopaedics | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Pediatric Otolaryngology | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 7 | Rhinology | target_program_source_discovery_after_exclusion | blank_pending_non_mutating_review_input |  |
| 8 | Extracorporeal Membrane Oxygenation | targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 8 | Pediatric Surgery | targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery | blank_pending_non_mutating_review_input |  |
| 9 | Diagnostic Radiology | program_page_probe | blank_pending_non_mutating_review_input |  |
| 9 | Interventional Radiology-Integrated | program_page_probe | blank_pending_non_mutating_review_input |  |
| 9 | Nuclear Medicine | program_page_probe | blank_pending_non_mutating_review_input |  |
| 9 | Ophthalmology | program_page_probe | blank_pending_non_mutating_review_input |  |
| 9 | Advanced Gastrointestinal Minimally Invasive Surgery | program_page_probe | blank_pending_non_mutating_review_input |  |
| 9 | Colon and Rectal Surgery | program_page_probe | blank_pending_non_mutating_review_input |  |
| 9 | Geriatric Psychiatry | program_page_probe | blank_pending_non_mutating_review_input |  |
| 9 | Oculofacial Plastic Surgery | program_page_probe | blank_pending_non_mutating_review_input |  |
| 9 | Vanderbilt ASTS Transplant and Hepatobiliary Surgery | program_page_probe | blank_pending_non_mutating_review_input |  |
| 10 | Anesthesiology | target_program_source_discovery_after_parser_exclusion | blank_pending_non_mutating_review_input |  |
| 10 | Internal Medicine – Wilson County | target_program_source_discovery_after_parser_exclusion | blank_pending_non_mutating_review_input |  |
| 10 | Obstetrics and Gynecology | target_program_source_discovery_after_parser_exclusion | blank_pending_non_mutating_review_input |  |
| 10 | Addiction Psychiatry | target_program_source_discovery_after_parser_exclusion | blank_pending_non_mutating_review_input |  |
| 10 | Global Anesthesiology | target_program_source_discovery_after_parser_exclusion | blank_pending_non_mutating_review_input |  |
| 10 | Pediatric Cardiology | target_program_source_discovery_after_parser_exclusion | blank_pending_non_mutating_review_input |  |
| 10 | Pediatric Pulmonology | target_program_source_discovery_after_parser_exclusion | blank_pending_non_mutating_review_input |  |
| 11 | Plastic Surgery | targeted_source_discovery_after_parent_url_resolution | blank_pending_non_mutating_review_input |  |
| 11 | Advanced Adult Cardiovascular Medicine | targeted_source_discovery_after_parent_url_resolution | blank_pending_non_mutating_review_input |  |
| 11 | Advanced Cardiac Imaging in Pediatric Cardiology | targeted_source_discovery_after_parent_url_resolution | blank_pending_non_mutating_review_input |  |
| 11 | Advanced Sports Medicine | targeted_source_discovery_after_parent_url_resolution | blank_pending_non_mutating_review_input |  |
| 11 | Electrophysiology in Pediatric Cardiology | targeted_source_discovery_after_parent_url_resolution | blank_pending_non_mutating_review_input |  |
| 11 | Heart failure and transplant in Pediatric Cardiology | targeted_source_discovery_after_parent_url_resolution | blank_pending_non_mutating_review_input |  |
| 11 | Hematopoietic Stem Cell Transplant | targeted_source_discovery_after_parent_url_resolution | blank_pending_non_mutating_review_input |  |
| 11 | Interventional Cardiology in Pediatric Cardiology | targeted_source_discovery_after_parent_url_resolution | blank_pending_non_mutating_review_input |  |
| 12 | Pediatrics/Medical Genetics and Genomics (Combined) | targeted_source_discovery_or_no_public_roster_closure_packet | blank_pending_non_mutating_review_input |  |
| 12 | Adult Cardiothoracic Anesthesiology | targeted_source_discovery_or_no_public_roster_closure_packet | blank_pending_non_mutating_review_input |  |
| 12 | Cardiothoracic Imaging | targeted_source_discovery_or_no_public_roster_closure_packet | blank_pending_non_mutating_review_input |  |
| 12 | Consultation - Liaison Psychiatry | targeted_source_discovery_or_no_public_roster_closure_packet | blank_pending_non_mutating_review_input |  |
| 12 | Critical Care Medicine | targeted_source_discovery_or_no_public_roster_closure_packet | blank_pending_non_mutating_review_input |  |
| 12 | Neuroanesthesiology | targeted_source_discovery_or_no_public_roster_closure_packet | blank_pending_non_mutating_review_input |  |
| 12 | Pediatric Hematology/Oncology | targeted_source_discovery_or_no_public_roster_closure_packet | blank_pending_non_mutating_review_input |  |
| 12 | Pediatric Radiology | targeted_source_discovery_or_no_public_roster_closure_packet | blank_pending_non_mutating_review_input |  |
| 13 | Autonomic Disorders | headed_refetch | blank_pending_non_mutating_review_input |  |
| 14 | Glaucoma | manual_current_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 14 | Ocular Oncology | manual_current_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 14 | Pediatric Anesthesiology | manual_current_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 14 | Pediatric Ophthalmology | manual_current_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 14 | Perioperative Medicine | manual_current_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 14 | Vascular Surgery | manual_current_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 14 | Vitreoretinal Diseases and Surgery | manual_current_scope_review_packet | blank_pending_non_mutating_review_input |  |
| 15 | Breast and Body Contouring Plastic Surgery | manual_url_confirmation_after_official_context_resolution | blank_pending_non_mutating_review_input |  |
| 15 | Gender Affirming Surgery | manual_url_confirmation_after_official_context_resolution | blank_pending_non_mutating_review_input |  |
| 15 | Interventional Radiology-Independent | manual_url_confirmation_after_official_context_resolution | blank_pending_non_mutating_review_input |  |
| 15 | Pediatric Extracorporeal Membrane Oxygenation | manual_url_confirmation_after_official_context_resolution | blank_pending_non_mutating_review_input |  |
| 16 | Adolescent Medicine | rendered_parser_manual_repair_after_official_url_probe | blank_pending_non_mutating_review_input |  |
| 17 | Acute Care Surgery | second_hop_route_inspection_after_official_url_probe | blank_pending_non_mutating_review_input |  |
| 18 | Clinical Informatics | target_program_source_discovery_after_non_current_exclusion | blank_pending_non_mutating_review_input |  |
| 19 | Urogynecology and Reconstructive Pelvic Surgery (Urology) | target_program_source_discovery_after_official_url_probe_exclusion | blank_pending_non_mutating_review_input |  |
| 20 | Pediatric Sports Medicine | target_program_source_discovery_after_official_url_probe_related_scope | blank_pending_non_mutating_review_input |  |
| 21 | Advanced Laparoscopic and Bariatric Surgery | targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe | blank_pending_non_mutating_review_input |  |
| 21 | Breast Surgical Oncology | targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe | blank_pending_non_mutating_review_input |  |
| 21 | Pediatric Optometry | targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe | blank_pending_non_mutating_review_input |  |
| 21 | Urogynecology and Reconstructive Pelvic Surgery (OBGYN) | targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe | blank_pending_non_mutating_review_input |  |
