# Penn Source Quality Learnings

Generated: 2026-06-02T12:35:16.336045+00:00

## What This Pass Did

This pass widened Penn source discovery beyond Department of Medicine, then ran candidate-only scholarly enrichment across the current resident/fellow corpus. No scholarly claims were accepted automatically.

## Penn-Wide Source Discovery

| classification | count |
| --- | --- |
| trainee_roster_candidate | 395 |
| program_context | 276 |
| alumni_or_outcome_candidate | 173 |
| attending_faculty_candidate | 34 |

Interpretation: `trainee_roster_candidate` is a review queue, not a canonical roster count. Program-context pages can mention residents/fellows without listing people, and some faculty pages share the same bio components as trainee pages.

## Official HUP GME Program Universe

Official denominator source: https://www3.pennmedicine.org/for-health-care-professionals/fellowship-and-residency-programs/hospital-of-the-university-of-pennsylvania/hup-gme/programs

Official HUP programs parsed: 91.

| coverage_status | count |
| --- | --- |
| covered_current_roster | 64 |
| discovered_no_current_roster | 12 |
| not_discovered | 15 |

Coverage assurance tiers:

Level-4 supported programs: 48 covering 769 people. Alias/count-review programs: 15. Open denominator gaps: 27.

| assurance_status | count |
| --- | --- |
| alias_method_current_roster_review | 15 |
| direct_normalized_name_current_roster | 29 |
| discovered_source_without_current_roster | 7 |
| exact_resolution_backed_current_roster | 19 |
| exact_resolution_count_conflict_review | 1 |
| not_discovered_by_current_strategy | 15 |
| open_gap_with_alias_review | 5 |

Coverage action queue:

Action rows: 43. Person-impact count: 542.

| action_lane | count |
| --- | --- |
| alias_review | 20 |
| count_conflict_review | 1 |
| parser_or_roster_source_review | 7 |
| source_candidate_probe | 15 |

Top coverage actions:

| official_program_name | official_program_type | action_lane | priority | person_impact_count | recommended_next_action |
| --- | --- | --- | --- | --- | --- |
| Internal Medicine - Categorical | residency | alias_review | 1093 | 173 | accept_or_split_alias_mapping |
| Soft Tissue/Bone (Selective) | fellowship | alias_review | 1009 | 69 | resolve_related_loaded_program_before_gap_closure |
| Adult Reconstructive Orthopedics | fellowship | count_conflict_review | 1003 | 3 | review_count_conflict_before_denominator_mutation |
| Radiology - Diagnostic | residency | alias_review | 974 | 54 | accept_or_split_alias_mapping |
| Radiology - Interventional, Independent | residency | alias_review | 971 | 19 | resolve_related_loaded_program_before_gap_closure |
| Dermatology | residency | alias_review | 963 | 3 | resolve_related_loaded_program_before_gap_closure |
| Plastic Surgery | fellowship | alias_review | 962 | 22 | resolve_related_loaded_program_before_gap_closure |
| Internal Medicine - Pediatrics | residency | alias_review | 945 | 25 | accept_or_split_alias_mapping |
| Plastic Surgery - Integrated | residency | alias_review | 942 | 22 | accept_or_split_alias_mapping |
| Radiology - Interventional, Integrated | residency | alias_review | 939 | 19 | accept_or_split_alias_mapping |
| Thoracic Surgery - Integrated | residency | alias_review | 935 | 15 | accept_or_split_alias_mapping |
| Pulmonary Disease and Critical Care Medicine | fellowship | alias_review | 934 | 34 | accept_or_split_alias_mapping |
| Transplant Hepatology | fellowship | alias_review | 926 | 2 | resolve_related_loaded_program_before_gap_closure |
| Internal Medicine - Dermatology | residency | alias_review | 925 | 5 | accept_or_split_alias_mapping |
| Gastroenterology | fellowship | alias_review | 923 | 23 | accept_or_split_alias_mapping |

Alias review packets:

Alias packet rows: 32. Reviewer-ready rows: 15. Reviewer-ready person count: 392.

| alias_decision_status | count |
| --- | --- |
| not_alias_count_conflict_review | 1 |
| review_required_combined_track_not_categorical_coverage | 1 |
| review_required_official_type_or_track_mismatch_review | 1 |
| review_required_role_mismatch_related_source | 1 |
| review_required_track_split_unresolved_review | 1 |
| review_required_weak_related_source_review | 10 |
| reviewer_ready_broad_residency_alias_candidate | 1 |
| reviewer_ready_combined_track_alias_candidate | 2 |
| reviewer_ready_program_alias_candidate | 9 |
| reviewer_ready_same_program_alias_candidate | 1 |
| reviewer_ready_section_split_candidate | 1 |
| reviewer_ready_track_alias_candidate | 1 |
| weak_alias_review | 2 |

Top alias packets:

| official_program_name | loaded_program_name | loaded_person_count | alias_decision_status | reviewer_ready | recommended_next_action |
| --- | --- | --- | --- | --- | --- |
| Internal Medicine - Categorical | Internal Medicine Residency | 173 | reviewer_ready_broad_residency_alias_candidate | 1 | accept_alias_only_if_loaded_source_excludes_combined_tracks |
| Radiology - Diagnostic | Diagnostic Radiology Residency | 54 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Pulmonary Disease and Critical Care Medicine | Pulmonary and Critical Care Fellowship | 34 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Gastroenterology | Gastroenterology and Hepatology Fellowship | 23 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Plastic Surgery - Integrated | Plastic Surgery Residency | 22 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Endocrinology | Endocrinology, Diabetes and Metabolism Fellowship | 21 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Radiology - Interventional, Integrated | Interventional Radiology Integrated Residency | 19 | reviewer_ready_track_alias_candidate | 1 | accept_track_alias_if_roster_scope_matches |
| Internal Medicine - Pediatrics | Penn-CHOP Internal Medicine-Pediatrics Residency | 16 | reviewer_ready_combined_track_alias_candidate | 1 | accept_combined_track_alias_if_roster_matches_official_track |
| Infectious Disease | Infectious Diseases Fellowship | 15 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Surgical Pathology (Selective) | Surgical Pathology Fellowship | 6 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Internal Medicine - Dermatology | Combined Internal Medicine-Dermatology Residency | 3 | reviewer_ready_combined_track_alias_candidate | 1 | accept_combined_track_alias_if_roster_matches_official_track |
| Transplant Hepatology | Advanced Gastroenterology and Hepatology Fellowship | 2 | reviewer_ready_section_split_candidate | 1 | split_loaded_program_by_section_label_then_close_gap |
| Gastrointestinal and Hepatic Pathology (Selective) | GI/Hepatic Pathology Fellowship | 2 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Blood Banking and Transfusion Medicine | Transfusion Medicine/Blood Bank Fellowship | 1 | reviewer_ready_program_alias_candidate | 1 | accept_program_alias_after_source_scope_check |
| Soft Tissue/Bone (Selective) | Soft Tissue/Bone Pathology Fellowship | 1 | reviewer_ready_same_program_alias_candidate | 1 | review_and_accept_same_program_alias_if_source_current |

Alias reviewer decisions:

Queue rows: 32. Ready rows: 15. Manual decision rows: 0. Accepted alias mappings: 0. Pending reviewer decisions: 15.

| decision_status | count |
| --- | --- |
| not_ready_for_reviewer_decision | 17 |
| pending_reviewer_decision | 15 |

| official_program_name | loaded_program_name | loaded_person_count | reviewer_decision | decision_status | accepted_alias_mapping | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- |
| Internal Medicine - Categorical | Internal Medicine Residency | 173 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Radiology - Diagnostic | Diagnostic Radiology Residency | 54 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Pulmonary Disease and Critical Care Medicine | Pulmonary and Critical Care Fellowship | 34 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Gastroenterology | Gastroenterology and Hepatology Fellowship | 23 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Plastic Surgery - Integrated | Plastic Surgery Residency | 22 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Endocrinology | Endocrinology, Diabetes and Metabolism Fellowship | 21 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Radiology - Interventional, Integrated | Interventional Radiology Integrated Residency | 19 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Internal Medicine - Pediatrics | Penn-CHOP Internal Medicine-Pediatrics Residency | 16 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Infectious Disease | Infectious Diseases Fellowship | 15 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Surgical Pathology (Selective) | Surgical Pathology Fellowship | 6 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Internal Medicine - Dermatology | Combined Internal Medicine-Dermatology Residency | 3 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Gastrointestinal and Hepatic Pathology (Selective) | GI/Hepatic Pathology Fellowship | 2 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Transplant Hepatology | Advanced Gastroenterology and Hepatology Fellowship | 2 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Blood Banking and Transfusion Medicine | Transfusion Medicine/Blood Bank Fellowship | 1 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Soft Tissue/Bone (Selective) | Soft Tissue/Bone Pathology Fellowship | 1 | pending | pending_reviewer_decision | 0 | record_accept_reject_or_needs_more_evidence_decision |
| Soft Tissue/Bone (Selective) | Pathology - Anatomic and Clinical Residency | 44 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Plastic Surgery | Plastic Surgery Residency | 22 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Radiology - Interventional, Independent | Interventional Radiology Integrated Residency | 19 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Thoracic Surgery - Integrated | Cardiothoracic Surgery Residency | 15 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Abdominal Radiology | Abdominal Imaging Fellowship | 9 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Soft Tissue/Bone (Selective) | Surgical Pathology Fellowship | 6 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Soft Tissue/Bone (Selective) | Hematopathology Fellowship | 4 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Adult Reconstructive Orthopedics | Adult Reconstructive Orthopedics Fellowship | 3 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Dermatology | Combined Internal Medicine-Dermatology Residency | 3 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |
| Soft Tissue/Bone (Selective) | Molecular Genetic Pathology Fellowship | 2 | pending | not_ready_for_reviewer_decision | 0 | collect_stronger_alias_or_scope_evidence |

Sample uncovered or partially covered official programs:

| program_type | department | program_name | coverage_status | match_method |
| --- | --- | --- | --- | --- |
| fellowship | Anesthesiology | Adult Cardiothoracic Anesthesiology | discovered_no_current_roster | source_discovery |
| fellowship | Anesthesiology | Critical Care Medicine | discovered_no_current_roster | source_discovery |
| fellowship | Anesthesiology | Pain Medicine | discovered_no_current_roster | source_discovery |
| residency | Dermatology | Dermatology | discovered_no_current_roster | source_discovery |
| fellowship | Dermatology | Dermatopathology | not_discovered | none |
| fellowship | Dermatology | Micrographic Surgery and Dermatologic Oncology | not_discovered | none |
| residency | Emergency Medicine | Emergency Medicine | discovered_no_current_roster | source_discovery |
| residency | Emergency Medicine | Occupational and Environmental Medicine (Preventative Medicine) | not_discovered | none |
| fellowship | Emergency Medicine | Undersea and Hyperbaric Medicine | discovered_no_current_roster | source_discovery |
| fellowship | Family Medicine | Addiction Medicine | discovered_no_current_roster | source_discovery |
| fellowship | Internal Medicine | Transplant Hepatology | discovered_no_current_roster | source_discovery |
| fellowship | Neurology | Clinical Neurophysiology | not_discovered | none |
| fellowship | Neurology | Epilepsy | not_discovered | none |
| fellowship | Neurology | Neurocritical Care | not_discovered | none |
| fellowship | Neurology | Neuromuscular Medicine | not_discovered | none |
| fellowship | Neurology | Vascular Neurology | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Complex Family Planning | not_discovered | none |
| residency | Oral and Maxillofacial Surgery | Oral and Maxillofacial Surgery | not_discovered | none |
| fellowship | Pathology and Laboratory Medicine | Soft Tissue/Bone (Selective) | discovered_no_current_roster | source_discovery |
| fellowship | Physical Medicine and Rehabilitation | Brain Injury Medicine | discovered_no_current_roster | source_discovery |
| residency | Psychiatry | Psychiatry | not_discovered | none |
| fellowship | Psychiatry | Addiction Psychiatry | not_discovered | none |
| fellowship | Psychiatry | Consultation and Liaison Psychiatry | not_discovered | none |
| fellowship | Psychiatry | Forensic Psychiatry | not_discovered | none |
| fellowship | Psychiatry | Geriatric Psychiatry | not_discovered | none |
| residency | Radiology | Radiology - Interventional, Independent | discovered_no_current_roster | source_discovery |
| fellowship | Surgery | Plastic Surgery | discovered_no_current_roster | source_discovery |

Learning: source discovery is not coverage. An official program-universe table gives the denominator needed for gap accounting, annual recrawls, and institution-level diff views. `covered_current_roster` means we have current people attached; `discovered_no_current_roster` means a program page is known but no current roster people are captured; `not_discovered` names crawl gaps.

## HUP Gap Source Queue

Gap programs probed: 27. Source pages probed: 23. Candidate URLs queued: 72.

| candidate_status | count |
| --- | --- |
| low_value_candidate | 5 |
| program_context_candidate | 55 |
| roster_source_candidate | 12 |

Top roster-source candidates:

| program_name | department | candidate_status | priority | candidate_title | candidate_url |
| --- | --- | --- | --- | --- | --- |
| Radiology - Interventional, Independent | Radiology | roster_source_candidate | 135 | Current Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-radiology/education-and-training/residency-programs/current-residents |
| Plastic Surgery | Surgery | roster_source_candidate | 135 | Meet Our Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training/residencies/plastic-surgery/residents |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Fellows | https://pathology.med.upenn.edu/department/people/fellows |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Residents | https://pathology.med.upenn.edu/department/people/residents |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 125 | Fellows | https://pathology.med.upenn.edu/education/fellowships/fellows |
| Radiology - Interventional, Independent | Radiology | roster_source_candidate | 125 | Meet our Integrated IR residents | https://www3.pennmedicine.org/departments-and-centers/department-of-radiology/education-and-training/residency-programs/current-residents/ir-integrated-residents |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 120 | Student Fellows | https://pathology.med.upenn.edu/department/people/students-fellows |
| Dermatology | Dermatology | roster_source_candidate | 115 | Penn Medicine Dermatology site | https://dermatology.upenn.edu/residents/combined-medicine-and-dermatology-track |
| Dermatology | Dermatology | roster_source_candidate | 115 | Chief Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/leadership/chief-residents |
| Dermatology | Dermatology | roster_source_candidate | 115 | Medicine-Dermatology Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/combined-internal-medicine-dermatology-program/medicine-dermatology-residents |
| Transplant Hepatology | Internal Medicine | roster_source_candidate | 115 | Advanced Gastroenterology and Hepatology Fellows | https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/gastroenterology/education-and-training/fellowship-programs/advanced-gastroenterology-fellows |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 115 | Current | https://pathology.med.upenn.edu/education/residency/residents/current |

Learning: coverage gaps need their own crawl state. Official program URLs, discovered context pages, and linked roster-like pages should be queued separately so the next scraper can attack high-priority roster candidates without conflating them with verified person records.

## HUP Gap Roster Extraction

Supported gap roster sources attempted: 32. Sources with records: 27. Person records extracted: 524.

Records by role:

| role | count |
| --- | --- |
| fellow | 82 |
| resident | 442 |

Extraction statuses:

| extraction_status | count |
| --- | --- |
| no_supported_person_structure | 5 |
| records_extracted | 27 |

Denominator-link reconciliation:

Official-linked extracted records: 94. Seed records still missing denominator keys: 430. Loaded memberships from reconciled sources: 499.

| denominator_link_status | count |
| --- | --- |
| official_program_key_no_supported_person_structure | 6 |
| records_extracted_seed_without_denominator_key | 24 |
| records_extracted_with_official_program_key | 3 |
| skipped_already_loaded_official_source | 4 |

Seed roster program-resolution audit:

Resolution rows reviewed: 24. Reviewer-ready exact-resolution records: 418. Review-required records: 12.

| resolution_status | records |
| --- | --- |
| accepted_exact_program_resolution_candidate | 418 |
| source_role_program_type_mismatch_review | 12 |

Learning: queue-driven extraction should stay template-aware. Pages without supported person structure remain source candidates; this avoids converting program context, generic people directories, or ambiguous student-fellow pages into trainee records. Extracted people and denominator coverage closure are separate claims: seed-derived records need an official program key or alias reconciliation before they can close an official HUP program gap.

## Penn-Wide Program Categorization

| program_name | role | count |
| --- | --- | --- |
| Anesthesiology Residency | resident | 97 |
| General Surgery Residency | resident | 75 |
| Diagnostic Radiology Residency | resident | 54 |
| Neurology Residency | resident | 54 |
| Pathology - Anatomic and Clinical Residency | resident | 44 |
| Orthopedic Surgery Residency | resident | 40 |
| Family Medicine Residency | resident | 35 |
| Obstetrics and Gynecology Residency | resident | 32 |
| Otorhinolaryngology Residency | resident | 31 |
| Physical Medicine and Rehabilitation Residency | resident | 22 |
| Plastic Surgery Residency | resident | 22 |
| Urology Residency | resident | 22 |
| Neurological Surgery Residency | resident | 21 |
| Ophthalmology Residency | resident | 20 |
| Interventional Radiology Integrated Residency | resident | 19 |
| Radiation Oncology Residency | resident | 17 |
| Podiatric Surgery Residency | resident | 16 |
| Cardiothoracic Surgery Residency | resident | 15 |
| Trauma and Surgical Critical Care Fellowship | fellow | 12 |
| Neuroradiology Fellowship | fellow | 11 |
| Ophthalmology Fellowship | fellow | 10 |
| Abdominal Imaging Fellowship | fellow | 9 |
| Vascular Surgery Integrated Residency | resident | 9 |
| Maternal Fetal Medicine Fellowship | fellow | 8 |
| Oral Medicine Residency | resident | 8 |
| Sleep Medicine Fellowship | fellow | 7 |
| Gynecologic Oncology Fellowship | fellow | 6 |
| Reproductive Endocrinology and Infertility Fellowship | fellow | 6 |
| Surgical Pathology Fellowship | fellow | 6 |
| Microvascular Reconstructive Surgery Fellowship | fellow | 5 |
| CHOP Otolaryngology Fellowship | fellow | 4 |
| Hematopathology Fellowship | fellow | 4 |
| Thoracic Surgery Fellowship - Cardiac Track | fellow | 4 |
| Urogynecology and Reconstructive Pelvic Surgery Fellowship | fellow | 4 |
| Vascular Surgery Fellowship | fellow | 4 |
| Adult Reconstructive Orthopedics Fellowship | fellow | 3 |
| Advanced Musculoskeletal Fellowship | fellow | 3 |
| Transplant Surgery Fellowship | fellow | 3 |
| Aortic Surgery Fellowship | fellow | 2 |
| Clinical Chemistry Fellowship | fellow | 2 |

Generic `Residents`/`Fellows` program labels remaining: 0.

Learning: program names often require URL-plus-section inference. Page titles alone are too weak because official pages can be titled `Residents` or `Fellows`, while one source page can contain multiple program sections.

## Penn Medical Student Public-Source Audit

Student-source audit rows: 16. Public MSTP loaded people: 225. Protected MD-directory rows: 1. Graduate cross-check rows: 9.

Capture statuses:

| capture_status | count |
| --- | --- |
| accepted_public_mstp_roster | 1 |
| points_to_medical_student_directory_without_public_records | 1 |
| protected_no_public_roster_records | 1 |
| public_md_phd_crosscheck_candidate | 9 |
| public_md_program_context_no_student_roster | 1 |
| student_directory_index_with_protected_md_notice | 1 |
| unreachable_review | 2 |

Audited student source surfaces:

| source_scope | access_status | capture_status | public_person_count_observed | loaded_person_count | source_url |
| --- | --- | --- | --- | --- | --- |
| student_directory_index | public | student_directory_index_with_protected_md_notice | 0 | 0 | https://www.med.upenn.edu/mstp/student-directories.html |
| md_phd_public_directory | public | accepted_public_mstp_roster | 225 | 225 | https://www.med.upenn.edu/mstp/student-directory/ |
| psom_directory_context | public | points_to_medical_student_directory_without_public_records | 0 | 0 | https://www.med.upenn.edu/psom/directory.html |
| md_program_context | public | public_md_program_context_no_student_roster | 0 | 0 | https://my.med.upenn.edu/student/ |
| md_student_directory | pennkey_protected | protected_no_public_roster_records | 0 | 0 | https://www.med.upenn.edu/apps/my/sms/studentdir/ |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 1 | 0 | https://www.sas.upenn.edu/anthropology/graduate/md/phd-program |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 0 | 0 | https://www.med.upenn.edu/bmbgrad/students_current.html |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 393 | 0 | https://www.med.upenn.edu/camb/current-students/#group=students&program=0&degree=0&year=0&advisor=0 |
| graduate_directory_md_phd_filter | fetch_error_or_unreachable | unreachable_review | 0 | 0 | https://www.med.upenn.edu/ggeb/current-students/#group=students&program=0&degree=0&year=0&advisor=0 |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 65 | 0 | https://www.med.upenn.edu/gcb/student-directory/#group=students&degree=0&year=0&advisor=0 |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 101 | 0 | https://www.med.upenn.edu/immun/current-students/#group=students&degree=0&year=0&advisor=0 |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 145 | 0 | https://www.med.upenn.edu/ngg/current-students/#group=students&degree=0&year=0&advisor=0 |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 68 | 0 | https://www.med.upenn.edu/pgg/current-students/#group=students&degree=0&year=0&advisor=0 |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 1 | 0 | https://be.seas.upenn.edu/doctoral/our-students/student-directory/ |
| graduate_directory_md_phd_filter | public | public_md_phd_crosscheck_candidate | 0 | 0 | https://hcmg.wharton.upenn.edu/programs/phd/students/ |
| graduate_directory_md_phd_filter | fetch_error_or_unreachable | unreachable_review | 0 | 0 | https://hss.sas.upenn.edu/people/graduate-students |

Learning: the public medical-student universe is not the same as the full medical-student universe. The official MSTP directory is a public current MD-PhD roster and remains accepted as a partial student truth anchor. The official MD student directory is PennKey protected, so it should be recorded as unavailable to public scraping and monitored for access changes. Graduate-program student directories can cross-check or enrich MD-PhD students, but they overlap MSTP and broader PhD populations and should not mutate the MD-student denominator.

## Training State Machine

| stage_family | normalized_stage | status | count | avg_confidence |
| --- | --- | --- | --- | --- |
| clinical_postgraduate | GME_CHIEF_RESIDENT | current | 16 | 0.72 |
| clinical_postgraduate | GME_CLINICAL_ANESTHESIA_YEAR_1 | current | 26 | 0.74 |
| clinical_postgraduate | GME_CLINICAL_ANESTHESIA_YEAR_2 | current | 26 | 0.74 |
| clinical_postgraduate | GME_CLINICAL_ANESTHESIA_YEAR_3 | current | 23 | 0.74 |
| clinical_postgraduate | GME_CLINICAL_YEAR_2 | current | 9 | 0.72 |
| clinical_postgraduate | GME_CLINICAL_YEAR_3 | current | 10 | 0.72 |
| clinical_postgraduate | GME_CLINICAL_YEAR_4 | current | 9 | 0.72 |
| clinical_postgraduate | GME_INDEPENDENT_RESIDENT | current | 2 | 0.62 |
| clinical_postgraduate | GME_PGY_1 | current | 205 | 0.872 |
| clinical_postgraduate | GME_PGY_2 | current | 204 | 0.893 |
| clinical_postgraduate | GME_PGY_3 | current | 176 | 0.894 |
| clinical_postgraduate | GME_PGY_4 | current | 71 | 0.877 |
| clinical_postgraduate | GME_PGY_5 | current | 25 | 0.85 |
| clinical_postgraduate | GME_PGY_6 | current | 8 | 0.9 |
| clinical_postgraduate | GME_PGY_7 | current | 3 | 0.9 |
| clinical_postgraduate | GME_PRELIMINARY_RESIDENT | current | 13 | 0.66 |
| clinical_postgraduate | GME_RESIDENT_CLASS_YEAR | current | 73 | 0.62 |
| clinical_postgraduate | GME_RESIDENT_YEAR_UNKNOWN | current | 94 | 0.429 |
| clinical_postgraduate_research | GME_RESEARCH_OR_LAB_YEAR | current | 25 | 0.68 |
| fellowship | FELLOWSHIP_CURRENT_YEAR_UNKNOWN | current | 185 | 0.5 |
| fellowship | FELLOWSHIP_YEAR_1 | current | 72 | 0.82 |
| fellowship | FELLOWSHIP_YEAR_2 | current | 63 | 0.82 |
| fellowship | FELLOWSHIP_YEAR_3 | current | 40 | 0.82 |
| fellowship | FELLOWSHIP_YEAR_4 | current | 7 | 0.82 |
| medical_school | MEDICAL_SCHOOL_MS1 | current | 22 | 0.85 |
| medical_school | MEDICAL_SCHOOL_MS2 | current | 31 | 0.85 |
| medical_school | MEDICAL_SCHOOL_MS3_OR_MS4 | current | 49 | 0.62 |
| post_training_or_alumni | COMPLETED_OR_FORMER | former | 13 | 0.75 |
| research_phase | MSTP_PHD_PHASE | current | 123 | 0.78 |
| research_phase | POSTDOCTORAL_RESEARCH_FELLOW | current | 7 | 0.7 |

Transition rules observed:

| transition_rule | count |
| --- | --- |
| expected GME annual advancement around Jul 1 unless program-specific exception | 618 |
| expected fellowship annual advancement around Jul 1; terminal year requires program-length context | 182 |
| current fellow but year not normalized; refresh on next roster and use program-specific duration if available | 141 |
| MSTP PhD phase duration is individualized; refresh from public directory annually | 123 |
| expected anesthesia clinical-year advancement around Jul 1; map to PGY with program review | 75 |
| class-year resident label; derive exact PGY only with program-duration context | 73 |
| current resident but year not visible on source; refresh on next roster | 73 |
| expected annual medical-school class advancement around Aug 1 | 53 |
| clinical-phase student label is ambiguous; refresh on annual directory update rather than auto-advance | 49 |
| ordinal resident-year label maps to PGY with program review | 38 |
| current fellow section label lacks year; refresh on next roster and use program-specific duration if available | 36 |
| intern label maps to PGY1; expected annual advancement around Jul 1 | 36 |
| expected clinical-year advancement around Jul 1; map to PGY with program review | 28 |
| research/lab resident state is program-specific; refresh from roster rather than auto-advance | 25 |
| current resident but exact year not visible on source; refresh on next roster | 21 |
| chief year is terminal/program-specific; refresh on next academic-year roster | 16 |
| preliminary resident label usually maps to a one-year GME state; verify against program context | 13 |
| terminal_or_historical_state; do not auto-advance | 13 |
| fellowship specialty section lacks year; refresh on next roster and use program-specific duration if available | 8 |
| postdoctoral fellow duration is individualized; refresh annually | 7 |
| independent-resident track is program-specific; refresh annually and map with specialty rules | 2 |

Lifecycle semantics observed:

| lifecycle_code | expected_transition_type | refresh_policy | count | avg_confidence |
| --- | --- | --- | --- | --- |
| None | source_refresh_required | refresh_from_source | 13 | 0.75 |
| US_GME_ANESTHESIA_CA_PHASE_3Y | expected_annual_advancement | annual_clock | 52 | 0.74 |
| US_GME_ANESTHESIA_CA_PHASE_3Y | expected_completion | annual_clock | 23 | 0.74 |
| US_GME_FELLOWSHIP_1Y | source_refresh_required | source_refresh_required | 91 | 0.509 |
| US_GME_FELLOWSHIP_1Y | stage_outside_nominal_duration_review | review_required | 1 | 0.82 |
| US_GME_FELLOWSHIP_2Y | expected_annual_advancement | annual_clock | 28 | 0.82 |
| US_GME_FELLOWSHIP_2Y | expected_completion | annual_clock | 26 | 0.82 |
| US_GME_FELLOWSHIP_2Y | source_refresh_required | source_refresh_required | 27 | 0.567 |
| US_GME_FELLOWSHIP_2Y | stage_outside_nominal_duration_review | review_required | 5 | 0.852 |
| US_GME_FELLOWSHIP_3Y | expected_annual_advancement | annual_clock | 72 | 0.82 |
| US_GME_FELLOWSHIP_3Y | expected_completion | annual_clock | 35 | 0.82 |
| US_GME_FELLOWSHIP_3Y | source_refresh_required | source_refresh_required | 10 | 0.52 |
| US_GME_FELLOWSHIP_3Y | stage_outside_nominal_duration_review | review_required | 7 | 0.82 |
| US_GME_FELLOWSHIP_DURATION_UNKNOWN | source_refresh_required | annual_clock | 12 | 0.833 |
| US_GME_FELLOWSHIP_DURATION_UNKNOWN | source_refresh_required | source_refresh_required | 64 | 0.478 |
| US_GME_PRELIMINARY_1Y | expected_completion | annual_clock | 13 | 0.66 |
| US_GME_RESIDENCY_3Y | expected_annual_advancement | annual_clock | 234 | 0.9 |
| US_GME_RESIDENCY_3Y | expected_completion | annual_clock | 107 | 0.9 |
| US_GME_RESIDENCY_3Y | stage_outside_nominal_duration_review | review_required | 10 | 0.9 |
| US_GME_RESIDENCY_4Y | expected_annual_advancement | annual_clock | 107 | 0.879 |
| US_GME_RESIDENCY_4Y | expected_completion | annual_clock | 23 | 0.9 |
| US_GME_RESIDENCY_4Y | source_refresh_required | source_refresh_required | 7 | 0.72 |
| US_GME_RESIDENCY_5Y | expected_annual_advancement | annual_clock | 123 | 0.801 |
| US_GME_RESIDENCY_5Y | expected_completion | annual_clock | 17 | 0.826 |
| US_GME_RESIDENCY_5Y | source_refresh_required | source_refresh_required | 169 | 0.556 |
| US_GME_RESIDENCY_6Y | expected_annual_advancement | annual_clock | 25 | 0.881 |
| US_GME_RESIDENCY_6Y | expected_completion | annual_clock | 5 | 0.9 |
| US_GME_RESIDENCY_6Y | source_refresh_required | source_refresh_required | 26 | 0.485 |
| US_GME_RESIDENCY_7Y | expected_annual_advancement | annual_clock | 18 | 0.9 |
| US_GME_RESIDENCY_7Y | expected_completion | annual_clock | 3 | 0.9 |
| US_GME_RESIDENCY_DURATION_UNKNOWN | source_refresh_required | annual_clock | 44 | 0.9 |
| US_GME_RESIDENCY_DURATION_UNKNOWN | source_refresh_required | source_refresh_required | 8 | 0.46 |
| US_MD_PHD_MSTP_VARIABLE | source_refresh_required | source_refresh_required | 225 | 0.762 |

State-machine audit status:

| state_machine_status | count |
| --- | --- |
| annual_clock_active | 659 |
| current_observation | 69 |
| review_required | 23 |
| source_refresh_required | 627 |
| terminal_year_active | 252 |

Clock models:

| clock_model | count |
| --- | --- |
| annual_gme_july | 967 |
| refresh_from_source | 13 |
| review_required | 23 |
| source_refresh_required | 627 |

Auto-advance candidate rows: 659. Completion candidate rows: 252. Stale/review rows: 23.

Learning: roster strings should become normalized state observations with explicit clocks and program lifecycle semantics. PGY and fellowship-year states can be annual-clock states, but terminal-year, unknown-duration, research, chief, and source-ambiguous states need different refresh/exit behavior. Lifecycle codes are local `redmank` codes until external ACGME/ERAS/NRMP identifiers are source-backed. The audit layer makes that operational: a row is only stale, advanceable, or removable when its lifecycle rule says so.

## Longitudinal Change Readiness

Projected refresh date: 2027-08-15. State rows: 1630. Person rows: 1483. Program rows: 95.

Readiness statuses:

| readiness_status | count |
| --- | --- |
| active_no_change_expected | 13 |
| expected_advancement_window | 659 |
| expected_completion_window | 252 |
| review_required_window | 23 |
| source_refresh_required_window | 627 |
| stale_without_transition_review | 56 |

Missing-on-refresh expectations:

| missing_expectation | count |
| --- | --- |
| absence_requires_source_reconciliation | 706 |
| expected_absence_after_completion | 252 |
| unexpected_absence_review | 672 |

Same-stage-on-refresh expectations:

| same_stage_expectation | count |
| --- | --- |
| same_stage_after_expected_transition_review | 659 |
| same_stage_expected | 13 |
| same_stage_requires_fresh_source | 706 |
| same_terminal_stage_after_completion_review | 252 |

Advancement due rows: 1446. Completion-window rows: 252. Source-refresh-required rows: 627. Human-review rows: 79.

Learning: annual diffs should be state-machine informed before they are person-table mutations. A missing terminal-year fellow after the stale-after date is likely completion; a missing PGY-2 before the expected exit is a review item; an unchanged MSTP PhD-phase student needs a fresh source rather than an inferred clock advancement.

## Transition Plan Ledger

Plan rows: 1630. Rollup rows: 224. Auto-classifiable transition rows: 911. Fresh-observation-required rows: 1617.

Policy lanes:

| policy_lane | count |
| --- | --- |
| carry_forward_no_change | 13 |
| deterministic_expected_advancement | 659 |
| deterministic_expected_completion | 252 |
| manual_review_required | 79 |
| source_refresh_required | 627 |

Diff readiness:

| diff_readiness_status | count |
| --- | --- |
| diff_expected_change_classifiable | 911 |
| diff_no_change_expected | 13 |
| diff_review_bound | 79 |
| diff_source_refresh_bound | 627 |

Corpus action: review_lifecycle_or_source_before_mutation. Policy: This ledger is non-mutating. Expected transitions are classifiable only with fresh source evidence or explicit terminal absence after stale-after; review/source-bound states are not carried forward silently.

Learning: the transition plan is the executable state-machine contract for future refreshes. It keeps expected advancement/completion, source-bound retention, and manual-review lanes separate, so a next-year run can produce individual, program, institution, category, and country diff views without silently carrying stale trainee states forward.

## Evidence Counts

| source_key | status | claim_type | count | avg_confidence |
| --- | --- | --- | --- | --- |
| allergy_immunology_current_fellows | accepted | medical_school | 4 | 0.8 |
| allergy_immunology_current_fellows | accepted | residency_program | 4 | 0.75 |
| cardiology_adult_congenital_current_fellows | accepted | medical_school | 2 | 0.85 |
| cardiology_adult_congenital_current_fellows | accepted | residency_program | 2 | 0.75 |
| cardiology_advanced_heart_failure_current_fellows | accepted | medical_school | 2 | 0.85 |
| cardiology_advanced_heart_failure_current_fellows | accepted | residency_program | 2 | 0.75 |
| cardiology_advanced_imaging_current_fellows | accepted | medical_school | 2 | 0.75 |
| cardiology_advanced_imaging_current_fellows | accepted | residency_program | 2 | 0.75 |
| cardiology_cardio_oncology_current_fellows | accepted | medical_school | 2 | 0.75 |
| cardiology_cardio_oncology_current_fellows | accepted | residency_program | 2 | 0.85 |
| cardiology_current_fellows | accepted | medical_school | 33 | 0.871 |
| cardiology_current_fellows | accepted | residency_program | 33 | 0.877 |
| cardiology_electrophysiology_current_fellows | accepted | medical_school | 12 | 0.833 |
| cardiology_electrophysiology_current_fellows | accepted | residency_program | 12 | 0.883 |
| cardiology_interventional_current_fellows | accepted | medical_school | 4 | 0.8 |
| cardiology_interventional_current_fellows | accepted | residency_program | 4 | 0.8 |
| endocrinology_current_fellows | accepted | medical_school | 21 | 0.817 |
| endocrinology_current_fellows | accepted | residency_program | 21 | 0.826 |
| gastroenterology_advanced_current_fellows | accepted | medical_school | 2 | 0.75 |
| gastroenterology_advanced_current_fellows | accepted | residency_program | 2 | 0.95 |
| gastroenterology_advanced_current_fellows | accepted | undergraduate_school | 1 | 0.75 |
| gastroenterology_current_fellows | accepted | medical_school | 23 | 0.828 |
| gastroenterology_current_fellows | accepted | residency_program | 23 | 0.889 |
| gastroenterology_current_fellows | accepted | undergraduate_school | 8 | 0.75 |
| geriatrics_current_fellows | accepted | medical_school | 3 | 0.883 |
| geriatrics_current_fellows | accepted | residency_program | 3 | 0.75 |
| hematology_oncology_current_fellows | accepted | medical_school | 32 | 0.831 |
| hematology_oncology_current_fellows | accepted | residency_program | 32 | 0.881 |
| infectious_diseases_current_fellows | accepted | graduate_school | 5 | 0.75 |
| infectious_diseases_current_fellows | accepted | medical_school | 15 | 0.843 |
| infectious_diseases_current_fellows | accepted | residency_program | 15 | 0.857 |
| infectious_diseases_current_fellows | accepted | undergraduate_school | 14 | 0.779 |
| internal_medicine_categorical | accepted | graduate_school | 1 | 0.75 |
| internal_medicine_categorical | accepted | medical_school | 169 | 0.865 |
| internal_medicine_global_health_equities | accepted | medical_school | 8 | 0.8 |
| internal_medicine_healthcare_quality | accepted | medical_school | 3 | 0.817 |
| internal_medicine_med_derm | accepted | medical_school | 3 | 0.883 |
| internal_medicine_med_peds | accepted | medical_school | 16 | 0.813 |
| internal_medicine_physician_scientist | accepted | medical_school | 3 | 0.883 |
| internal_medicine_primary_care | accepted | medical_school | 8 | 0.875 |
| nephrology_current_fellows | accepted | medical_school | 22 | 0.768 |
| nephrology_current_fellows | accepted | residency_program | 22 | 0.777 |
| palliative_current_fellows | accepted | medical_school | 5 | 0.75 |
| palliative_current_fellows | accepted | residency_program | 5 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_radiology_education_and_training_282737f299 | accepted | medical_school | 19 | 0.908 |
| penn_affiliated_departments_and_centers_department_of_radiology_education_and_training_282737f299 | accepted | undergraduate_school | 19 | 0.929 |
| penn_affiliated_departments_and_centers_department_of_radiology_education_and_training_2ebc99cda7 | accepted | graduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_radiology_education_and_training_2ebc99cda7 | accepted | medical_school | 54 | 0.857 |
| penn_affiliated_departments_and_centers_department_of_radiology_education_and_training_2ebc99cda7 | accepted | undergraduate_school | 47 | 0.844 |
| penn_affiliated_departments_and_centers_department_of_radiology_education_and_training_4250553081 | accepted | medical_school | 28 | 0.836 |
| penn_affiliated_departments_and_centers_department_of_radiology_education_and_training_4250553081 | accepted | residency_program | 27 | 0.802 |
| penn_affiliated_departments_and_centers_department_of_radiology_education_and_training_4250553081 | accepted | undergraduate_school | 20 | 0.84 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_059f3f8bc0 | accepted | medical_school | 1 | 0.95 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_059f3f8bc0 | accepted | undergraduate_school | 1 | 0.95 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_4ccb7e8d57 | accepted | graduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_4ccb7e8d57 | accepted | medical_school | 4 | 0.85 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_4ccb7e8d57 | accepted | residency_program | 4 | 0.8 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_4ccb7e8d57 | accepted | undergraduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_acebe4929a | accepted | graduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_acebe4929a | accepted | medical_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_e9538572e0 | accepted | graduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_e9538572e0 | accepted | medical_school | 3 | 0.883 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_e9538572e0 | accepted | residency_program | 3 | 0.817 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_e9538572e0 | accepted | undergraduate_school | 2 | 0.95 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_f1043500c4 | accepted | medical_school | 2 | 0.85 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_f1043500c4 | accepted | residency_program | 2 | 0.95 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_f1043500c4 | accepted | undergraduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_fb4824f4f4 | accepted | graduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_fb4824f4f4 | accepted | medical_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_fb4824f4f4 | accepted | undergraduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_ff73f3288d | accepted | medical_school | 4 | 0.85 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_ff73f3288d | accepted | residency_program | 4 | 0.8 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_f_ff73f3288d | accepted | undergraduate_school | 4 | 0.85 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_8726482f2e | accepted | medical_school | 9 | 0.906 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_8726482f2e | accepted | undergraduate_school | 8 | 0.825 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b1bc5a1dae | accepted | graduate_school | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b1bc5a1dae | accepted | medical_school | 22 | 0.877 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b1bc5a1dae | accepted | residency_program | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b1bc5a1dae | accepted | undergraduate_school | 21 | 0.845 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b688511031 | accepted | graduate_school | 6 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b688511031 | accepted | medical_school | 69 | 0.889 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b688511031 | accepted | residency_program | 1 | 0.75 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b688511031 | accepted | undergraduate_school | 61 | 0.842 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b953e0b386 | accepted | medical_school | 22 | 0.905 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_b953e0b386 | accepted | undergraduate_school | 21 | 0.817 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_f767efabe7 | accepted | medical_school | 15 | 0.857 |
| penn_affiliated_departments_and_centers_department_of_surgery_education_and_training_r_f767efabe7 | accepted | undergraduate_school | 14 | 0.836 |
| penn_affiliated_departments_and_centers_ophthalmology_education_and_training_current_r_eec75b1532 | accepted | medical_school | 20 | 0.9 |
| penn_affiliated_departments_and_centers_ophthalmology_education_and_training_current_r_eec75b1532 | accepted | residency_program | 10 | 0.77 |
| penn_gme_gap_departments_and_centers_anesthesiology_and_critical_care_education_and_4122b4df93 | accepted | medical_school | 97 | 0.892 |
| penn_gme_gap_departments_and_centers_department_of_surgery_education_and_training_f_3d64800a80 | accepted | medical_school | 1 | 0.75 |
| penn_gme_gap_departments_and_centers_department_of_surgery_education_and_training_f_3d64800a80 | accepted | residency_program | 1 | 0.75 |
| penn_gme_gap_departments_and_centers_department_of_surgery_education_and_training_f_4a5e8aaebf | accepted | graduate_school | 1 | 0.95 |
| penn_gme_gap_departments_and_centers_department_of_surgery_education_and_training_f_4a5e8aaebf | accepted | medical_school | 1 | 0.95 |
| penn_gme_gap_departments_and_centers_department_of_surgery_education_and_training_f_4a5e8aaebf | accepted | residency_program | 1 | 0.75 |
| penn_gme_gap_departments_and_centers_department_of_surgery_education_and_training_f_4a5e8aaebf | accepted | undergraduate_school | 1 | 0.95 |
| penn_gme_gap_departments_and_centers_family_medicine_and_community_health_education_3e2990eebf | accepted | medical_school | 34 | 0.897 |
| penn_gme_gap_departments_and_centers_neurosurgery_education_and_training_residency__aa4b8422b4 | accepted | medical_school | 21 | 0.94 |
| penn_gme_gap_departments_and_centers_neurosurgery_education_and_training_residency__aa4b8422b4 | accepted | undergraduate_school | 21 | 0.912 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_291e92d34d | accepted | residency_program | 4 | 0.85 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_2c6709998d | accepted | graduate_school | 6 | 0.817 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_2c6709998d | accepted | medical_school | 32 | 0.912 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_2c6709998d | accepted | undergraduate_school | 29 | 0.929 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_9f2f64f93c | accepted | medical_school | 6 | 0.883 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_9f2f64f93c | accepted | residency_program | 6 | 0.85 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_9f2f64f93c | accepted | undergraduate_school | 6 | 0.917 |
| penn_gme_gap_departments_and_centers_orthopaedic_surgery_education_and_training_res_bc144f028b | accepted | medical_school | 40 | 0.895 |
| penn_gme_gap_departments_and_centers_orthopaedic_surgery_education_and_training_res_bc144f028b | accepted | undergraduate_school | 40 | 0.845 |
| penn_gme_gap_departments_and_centers_physical_medicine_and_rehabilitation_education_7d5742c85a | accepted | medical_school | 22 | 0.841 |
| penn_gme_gap_departments_and_centers_podiatry_and_podiatric_surgery_education_and_t_ebe320ba1d | accepted | graduate_school | 2 | 0.75 |
| penn_gme_gap_departments_and_centers_podiatry_and_podiatric_surgery_education_and_t_ebe320ba1d | accepted | medical_school | 16 | 0.887 |
| penn_gme_gap_departments_and_centers_podiatry_and_podiatric_surgery_education_and_t_ebe320ba1d | accepted | undergraduate_school | 16 | 0.825 |
| penn_gme_gap_education_residency_residents_current_5a6a4942f1 | accepted | medical_school | 38 | 0.876 |
| penn_gme_gap_residents_2026_a44d511002 | accepted | medical_school | 14 | 0.921 |
| penn_gme_gap_residents_2027_15a734ed51 | accepted | medical_school | 14 | 0.821 |
| penn_gme_gap_residents_2028_420d5a86f8 | accepted | medical_school | 14 | 0.879 |
| penn_gme_gap_residents_2029_3396e9a918 | accepted | medical_school | 12 | 0.917 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_191c59e052 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_191c59e052 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_191c59e052 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_3792f37aea | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_3792f37aea | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_3792f37aea | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_ef527b2c83 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_ef527b2c83 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_division_of_end_ef527b2c83 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_060eb08ed7 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_060eb08ed7 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_060eb08ed7 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_060eb08ed7 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_125aaa0f5a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_125aaa0f5a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_125aaa0f5a | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_125aaa0f5a | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_1bbe3bb1a8 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_1bbe3bb1a8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_1bbe3bb1a8 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_1bbe3bb1a8 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_2298ff7dda | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_2298ff7dda | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_2298ff7dda | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_2298ff7dda | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_2c3c369a36 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_2c3c369a36 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_2c3c369a36 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_2c3c369a36 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_44f5dce947 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_44f5dce947 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_44f5dce947 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_44f5dce947 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_4e4b7c5c93 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_4e4b7c5c93 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_4e4b7c5c93 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_4e4b7c5c93 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_50b42bd55d | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_50b42bd55d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_50b42bd55d | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_50b42bd55d | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_803a4d5a9c | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_803a4d5a9c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_803a4d5a9c | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_803a4d5a9c | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_83dbdccf06 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_83dbdccf06 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_83dbdccf06 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_83dbdccf06 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_871646d4c0 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_871646d4c0 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_871646d4c0 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_871646d4c0 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_8cf5000b22 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_8cf5000b22 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_8cf5000b22 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_8cf5000b22 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9429badf64 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9429badf64 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9429badf64 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9429badf64 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9b39acfac4 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9b39acfac4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9b39acfac4 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9b39acfac4 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9be76bb000 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9be76bb000 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9be76bb000 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_9be76bb000 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_a17fa21e4e | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_a17fa21e4e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_a17fa21e4e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_a17fa21e4e | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_bc2b8bf764 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_bc2b8bf764 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_bc2b8bf764 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_bc2b8bf764 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_bff9ffffda | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_bff9ffffda | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_bff9ffffda | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_bff9ffffda | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_c36f9c5f94 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_c36f9c5f94 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_c36f9c5f94 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_c36f9c5f94 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_d00081d1ad | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_d00081d1ad | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_d00081d1ad | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_d00081d1ad | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_dbafc41e90 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_dbafc41e90 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_dbafc41e90 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_dbafc41e90 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_e5cda5f9aa | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_e5cda5f9aa | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_e5cda5f9aa | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_e5cda5f9aa | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_e8eaf8363f | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_e8eaf8363f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_e8eaf8363f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_e8eaf8363f | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_fc12bf2f87 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_fc12bf2f87 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_fc12bf2f87 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_gastroenterolog_fc12bf2f87 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_041aa6235a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_041aa6235a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_041aa6235a | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_20c3357188 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_20c3357188 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_20c3357188 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_27cf2930b7 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_27cf2930b7 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_27cf2930b7 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_3ee39a1aa5 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_3ee39a1aa5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_3ee39a1aa5 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_55d5a5dd99 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_55d5a5dd99 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_55d5a5dd99 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_73dd8e4bb6 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_73dd8e4bb6 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_73dd8e4bb6 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_7613d674be | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_7613d674be | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_7613d674be | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_f6d477a9c1 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_f6d477a9c1 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_f6d477a9c1 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_0440faa844 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_0440faa844 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_0440faa844 | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_0440faa844 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_0440faa844 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_30afaa188a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_30afaa188a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_30afaa188a | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_30afaa188a | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_30afaa188a | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_390c9ee06a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_390c9ee06a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_390c9ee06a | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_390c9ee06a | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_390c9ee06a | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_5758c6b85f | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_5758c6b85f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_5758c6b85f | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_5758c6b85f | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_5758c6b85f | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_6a21790ce0 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_6a21790ce0 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_6a21790ce0 | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_6a21790ce0 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_6a21790ce0 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_7819699494 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_7819699494 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_7819699494 | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_7819699494 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_be68f5062f | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_be68f5062f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_be68f5062f | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_be68f5062f | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_be68f5062f | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_d71d1686ba | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_d71d1686ba | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_d71d1686ba | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_d71d1686ba | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_d71d1686ba | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eb6b55c5cf | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eb6b55c5cf | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eb6b55c5cf | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eb6b55c5cf | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eb6b55c5cf | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_ee44d9f889 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_ee44d9f889 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_ee44d9f889 | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_ee44d9f889 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_ee44d9f889 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eeac438f2f | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eeac438f2f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eeac438f2f | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eeac438f2f | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_eeac438f2f | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_f90a7cb3c5 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_f90a7cb3c5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_f90a7cb3c5 | candidate | personal_profile_candidate | 3 | 0.537 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_f90a7cb3c5 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_renal_electroly_f90a7cb3c5 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_091cfa42b9 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_091cfa42b9 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_091cfa42b9 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_091cfa42b9 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_091cfa42b9 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_2e9c843bbe | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_2e9c843bbe | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_2e9c843bbe | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_2e9c843bbe | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_2e9c843bbe | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_335bf2eb6a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_335bf2eb6a | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_335bf2eb6a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_335bf2eb6a | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_335bf2eb6a | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_3c11a9702b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_3c11a9702b | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_3c11a9702b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_3c11a9702b | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_3c11a9702b | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_6216e9d3f5 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_6216e9d3f5 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_6216e9d3f5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_6216e9d3f5 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_6216e9d3f5 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_62b307a818 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_62b307a818 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_62b307a818 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_62b307a818 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_62b307a818 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_721ea1c1de | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_721ea1c1de | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_721ea1c1de | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_721ea1c1de | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_721ea1c1de | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_75c8f02e62 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_75c8f02e62 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_75c8f02e62 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_75c8f02e62 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_75c8f02e62 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_8d1df66760 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_8d1df66760 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_8d1df66760 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_8d1df66760 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_8d1df66760 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_9bebf84bca | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_9bebf84bca | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_9bebf84bca | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_9bebf84bca | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_9bebf84bca | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_a7bb372cb3 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_a7bb372cb3 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_a7bb372cb3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_a7bb372cb3 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_a7bb372cb3 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_be845708f4 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_be845708f4 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_be845708f4 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_be845708f4 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_be845708f4 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d033e7cf8b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d033e7cf8b | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d033e7cf8b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d033e7cf8b | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d033e7cf8b | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d4af4119f9 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d4af4119f9 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d4af4119f9 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d4af4119f9 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d4af4119f9 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d5f7a1cac7 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d5f7a1cac7 | candidate | career_interest_candidate | 1 | 0.58 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d5f7a1cac7 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d5f7a1cac7 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_rheumatology_ed_d5f7a1cac7 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_004f4c3fd6 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_004f4c3fd6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_004f4c3fd6 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_01cd640b53 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_01cd640b53 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_01cd640b53 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_0280f19f1f | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_0280f19f1f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_0280f19f1f | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_028e771d67 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_028e771d67 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_028e771d67 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_086bf29cdd | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_086bf29cdd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_086bf29cdd | candidate | personal_profile_candidate | 4 | 0.51 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_091c15d808 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_091c15d808 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_091c15d808 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_094193d4ab | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_094193d4ab | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_094193d4ab | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_103d7a2572 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_103d7a2572 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_11a14b9485 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_11a14b9485 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_11a14b9485 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_192321016a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_192321016a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_192321016a | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_1a8158f916 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_1a8158f916 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_1a8158f916 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_1bd462a05a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_22bf12dfe6 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_22bf12dfe6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_22bf12dfe6 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_241a11b319 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_241a11b319 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_241a11b319 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_24731acf6c | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_24731acf6c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_24731acf6c | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2a7dfec8b0 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2a7dfec8b0 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2a7dfec8b0 | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2b66c5b5df | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2b66c5b5df | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2b66c5b5df | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2b884aee25 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2b884aee25 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_2b884aee25 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_30440d7b05 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_30440d7b05 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_30440d7b05 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_353dda4605 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_353dda4605 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_353dda4605 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_355a6e27f5 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_355a6e27f5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_355a6e27f5 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_36844d43c9 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_36844d43c9 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_36844d43c9 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3823d28ab0 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3823d28ab0 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3823d28ab0 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3886bf5ed3 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3886bf5ed3 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3886bf5ed3 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3a4eea84ac | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3a4eea84ac | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3a4eea84ac | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3b9dc751d6 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3b9dc751d6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3b9dc751d6 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3de6b243d8 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3de6b243d8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3de6b243d8 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3f32922931 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3f32922931 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_3f32922931 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4296b41350 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4296b41350 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4296b41350 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_44f2c262b0 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_44f2c262b0 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_44f2c262b0 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_45dcd2e15d | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_45dcd2e15d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_45dcd2e15d | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_46093b1b6e | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_46093b1b6e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_46093b1b6e | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_480922e673 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_480922e673 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_480922e673 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4a2a06bab5 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4a2a06bab5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4a2a06bab5 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4a847833de | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4a847833de | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4a847833de | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4c490308fc | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4c490308fc | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4c490308fc | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4e4a2690e5 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4e4a2690e5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4e4a2690e5 | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4f181bc5b2 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4f181bc5b2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4f181bc5b2 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4fc2a9e37a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4fc2a9e37a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_4fc2a9e37a | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5237506604 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5237506604 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5237506604 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5388d538fd | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5388d538fd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5388d538fd | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_553049e327 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_553049e327 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_553049e327 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_55a9bf057b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_55a9bf057b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_55a9bf057b | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_55fe9421ed | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_55fe9421ed | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_55fe9421ed | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_573610d6f2 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_573610d6f2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_573610d6f2 | candidate | personal_profile_candidate | 1 | 0.54 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_598ee2f141 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_598ee2f141 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_598ee2f141 | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_59d7b0533a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_59d7b0533a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_59d7b0533a | candidate | personal_profile_candidate | 4 | 0.51 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5ab5dc6f21 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5ab5dc6f21 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5ab5dc6f21 | candidate | personal_profile_candidate | 2 | 0.545 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5bf5b7530b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5bf5b7530b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5bf5b7530b | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5d957ce8ec | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5d957ce8ec | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5d957ce8ec | candidate | personal_profile_candidate | 4 | 0.51 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5fb3b45912 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5fb3b45912 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_5fb3b45912 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_60bddd9b01 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_60bddd9b01 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_60bddd9b01 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_64293d58d1 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_64293d58d1 | candidate | education_history_candidate | 2 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_64293d58d1 | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6978445826 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6978445826 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6978445826 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6d18786df9 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6d18786df9 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6d18786df9 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6ea4cf856b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6ea4cf856b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6ea4cf856b | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6eaf839bf8 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6eaf839bf8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_6eaf839bf8 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_705e97190a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_705e97190a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_705e97190a | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_72b0400a0b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_72b0400a0b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_72b0400a0b | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_73486ea3b6 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_73486ea3b6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_73486ea3b6 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_73731ec9b6 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_73731ec9b6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_73731ec9b6 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_747a88c358 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_747a88c358 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_747a88c358 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_74907a4385 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_74907a4385 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_74907a4385 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_75acf9a071 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_75acf9a071 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_75acf9a071 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7762435884 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7762435884 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7762435884 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_792113b57d | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_792113b57d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_792113b57d | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7966f043a3 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7966f043a3 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7966f043a3 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7995d0e511 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7995d0e511 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7995d0e511 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7d3ada37f4 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7d3ada37f4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_7d3ada37f4 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_87a6712b15 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_87a6712b15 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_87a6712b15 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_8983150632 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_8983150632 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_8e658d8689 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_8e658d8689 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_8e658d8689 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9456f7f3b8 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9456f7f3b8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9456f7f3b8 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9475e014b4 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9475e014b4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9475e014b4 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_96c62ee6df | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_96c62ee6df | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_96c62ee6df | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9906493216 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9906493216 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9906493216 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9a77587716 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9a77587716 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9a77587716 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9bdb5c7919 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9bdb5c7919 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9bdb5c7919 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9cb80119bd | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9cb80119bd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9cb80119bd | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9dd55559dd | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9dd55559dd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9dd55559dd | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9f0201968c | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9f0201968c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9f0201968c | candidate | personal_profile_candidate | 4 | 0.51 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9f525c067f | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9f525c067f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_9f525c067f | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a04dc7a02b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a04dc7a02b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a04dc7a02b | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a34a17fb3a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a34a17fb3a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a34a17fb3a | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a5767b3ccf | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a5767b3ccf | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a5767b3ccf | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8549d2f44 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8549d2f44 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8549d2f44 | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8ce21730b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8ce21730b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8ce21730b | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8d4116167 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8d4116167 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a8d4116167 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a977d7fe82 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a977d7fe82 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_a977d7fe82 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_aaa63d021b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_aaa63d021b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_aaa63d021b | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_abc969c2c4 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_abc969c2c4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_abc969c2c4 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_aceffc32c2 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_aceffc32c2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_aceffc32c2 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b0a7871c73 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b0a7871c73 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b0a7871c73 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b12a3a88a0 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b12a3a88a0 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b12a3a88a0 | candidate | personal_profile_candidate | 4 | 0.51 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b27c295a0f | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b27c295a0f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b27c295a0f | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b3eb0f4c3d | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b3eb0f4c3d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b3eb0f4c3d | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b511fc6140 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b511fc6140 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b511fc6140 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b8208063fd | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b8208063fd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b8208063fd | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b8a0d66b74 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b8a0d66b74 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_b8a0d66b74 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ba01c78d55 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ba01c78d55 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ba01c78d55 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_bbf59c4ca7 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_bbf59c4ca7 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_bbf59c4ca7 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_bd7863964a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_bd7863964a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_bd7863964a | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c2b02d7d2c | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c2b02d7d2c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c2b02d7d2c | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c316cf7b6c | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c316cf7b6c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c316cf7b6c | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c39e074bba | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c39e074bba | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c39e074bba | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c488959209 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c488959209 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_c488959209 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ccaccd9794 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ccaccd9794 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ccaccd9794 | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cce450752d | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cce450752d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cce450752d | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cde1d6cc11 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cde1d6cc11 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cde1d6cc11 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cdf03e85da | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cdf03e85da | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_cdf03e85da | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d08bab62b9 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d08bab62b9 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d08bab62b9 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d2d3e17f33 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d2d3e17f33 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d2d3e17f33 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d55d39d2cb | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d55d39d2cb | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d55d39d2cb | candidate | personal_profile_candidate | 3 | 0.53 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d58409de17 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d58409de17 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d58409de17 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d68720e2ba | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d68720e2ba | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d68720e2ba | candidate | personal_profile_candidate | 1 | 0.54 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d6a5808099 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d6a5808099 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_d6a5808099 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_dc41f03984 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_dc41f03984 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_dc41f03984 | candidate | personal_profile_candidate | 5 | 0.508 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_dcfc878f6c | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_dcfc878f6c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_dcfc878f6c | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e6896c0547 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e6896c0547 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e6896c0547 | candidate | personal_profile_candidate | 4 | 0.497 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e838979a0a | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e838979a0a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e838979a0a | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e8e6d40118 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e8e6d40118 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e8e6d40118 | candidate | personal_profile_candidate | 4 | 0.51 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e949b09e3c | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e949b09e3c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e949b09e3c | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e985d17b5e | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e985d17b5e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_e985d17b5e | candidate | personal_profile_candidate | 4 | 0.51 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_eb6b2277d9 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_eb6b2277d9 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_eb6b2277d9 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ec4f444a39 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ec4f444a39 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_ec4f444a39 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f199d0f682 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f199d0f682 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f199d0f682 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f623f1f05c | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f623f1f05c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f623f1f05c | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f7cc016585 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f7cc016585 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_f7cc016585 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_fc55861c79 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_fc55861c79 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_fc55861c79 | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_fe6d2202be | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_fe6d2202be | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_fe6d2202be | candidate | personal_profile_candidate | 4 | 0.522 |
| penn_trainee_profile_providers_julie_cooper_e600f7441b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_providers_profile_lauren_hogshire_a5d9163adc | accepted | official_profile_url | 1 | 0.9 |
| pubmed_eutilities | candidate | pubmed_article_candidate | 1405 | 0.652 |
| pubmed_eutilities | candidate | pubmed_author_query_candidate | 1336 | 0.204 |
| pubmed_eutilities | needs_review | pubmed_article_candidate | 857 | 0.841 |
| pulmonary_critical_care_current_fellows | accepted | medical_school | 34 | 0.868 |
| pulmonary_critical_care_current_fellows | accepted | residency_program | 34 | 0.832 |
| rheumatology_current_fellows | accepted | medical_school | 15 | 0.817 |
| rheumatology_current_fellows | accepted | residency_program | 15 | 0.83 |
| rheumatology_current_fellows | accepted | undergraduate_school | 15 | 0.777 |

## Source Utility Scorecard

Scorecard rows: 22.

| utility_label | claim_surface | input_records | output_records | score | quality_band | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- |
| Official roster current-membership extraction | current trainee identity, role, program, stage, and source-backed background | 78 | 1558 | 92.0 | high_utility | keep_as_truth_anchor_and_refresh_on_program_clock |
| Official HUP program denominator coverage | institution program universe, coverage gaps, and denominator drift | 91 | 64 | 86.0 | high_utility | resolve_gap_reason_and_alias_candidates_before_count_mutation |
| ACGME public program identifier candidates | program accreditation code, specialty, sponsoring program name, city, and accreditation-row context | 91 | 113 | 82.0 | strong_with_known_limits | use_accepted_program_identifiers_and_review_remaining_acgme_ambiguities |
| Penn medical-student public-source audit | public MSTP directory, protected MD directory, MD program context, and MD-PhD graduate-directory cross-checks | 16 | 16 | 78.0 | strong_with_known_limits | monitor_protected_md_directory_and_use_grad_directories_only_for_mstp_crosscheck |
| Official gap roster queue extraction | named resident/fellow extraction from prioritized uncovered-program pages | 32 | 524 | 76.0 | strong_with_known_limits | review_denominator_resolution_candidates_then_rerun_coverage |
| Penn-wide source discovery crawler | candidate roster, program context, alumni/outcome, and attending/faculty sources | 878 | 395 | 58.0 | useful_candidate_layer | treat_as_queue_then_probe_and_parse_only_source_backed_rosters |
| PubMed author-query discovery | name-bounded publication discovery seeds | 1336 | 1336 | 39.0 | discovery_or_review_only | use_only_to_seed_article_level_reconciliation |
| PubMed article-level reconciliation | PMID-level publication candidates with author, affiliation, topic, and recency anchors | 2262 | 2262 | 69.0 | useful_candidate_layer | prioritize_review_ready_packets_then_collect_secondary_identity_anchors |
| Enrichment acceptance assurance ledger | non-mutating acceptance tiers for publications, NPI anchors, and profile/trend evidence | 4776 | 4776 | 77.0 | strong_with_known_limits | promote_cross_source_publication_candidates_after_final_duplicate_author_position_check |
| Warehouse reproducibility provenance audit | artifact existence, row-count parity, content hashes, and repository-size pressure | 66 | 66 | 88.0 | high_utility | retain_sqlite_as_generated_untracked_artifact_and_refresh_manifest |
| OpenAlex author search | author-disambiguation, works, affiliations, ORCID, and citation features | 0 | 0 | 24.0 | blocked_or_low_current_utility | run_as_resumable_optional_lane_with_rate_limit_backoff |
| Official Penn trainee profile claims | roster-linked profile URLs, education, prior training, research/career interests, and personal-context snippets | 194 | 1110 | 81.0 | strong_with_known_limits | use_as_profile_enrichment_and_parser_training_set_then_expand_to_uncovered_official_profiles |
| Official Penn attending/profile claims | current attending endpoints, structured education/training, research interests, and personal profile snippets | 20 | 20 | 73.0 | strong_with_known_limits | seek_historical_identity_bridge_before_accepting_trend_links |
| Attending historical-link discovery | source candidates that may bridge current Penn attending endpoints to historical trainee records | 15 | 5 | 47.0 | discovery_or_review_only | run_polite_broad_search_and_prioritize_dated_historical_roster_or_cv_hits |
| Official Penn faculty biosketch training bridges | dated post-graduate training lines from official Penn Faculty Biosketch pages | 4 | 10 | 79.0 | strong_with_known_limits | review_dated_biosketch_bridges_before_accepting_recent_attending_trends |
| Attending trend reconciliation ledger | non-mutating policy ledger for current-attending endpoint, Penn-training, biosketch, and historical-link evidence | 70 | 70 | 82.0 | strong_with_known_limits | review_ready_trend_rows_then_record_explicit_acceptance_decisions |
| NPPES NPI Registry candidates | candidate NPI, taxonomy, and PA practice-location anchors for current resident/fellow identity review | 1257 | 1073 | 62.0 | useful_candidate_layer | use_npi_candidates_as_secondary_identity_anchors_only |
| Public contact candidate extraction | public email/contact channels with scope and verification status | 313 | 313 | 69.0 | useful_candidate_layer | verify_current_source_before_display_or_outreach_and_review_domain_anomalies |
| Organization normalization resolver | medical school, residency, undergraduate, graduate, institution, and program labels | 834 | 854 | 74.0 | strong_with_known_limits | append_alias_and_identifier_candidates_with_source_backed_evidence |
| Training state machine and longitudinal readiness | normalized stages, lifecycle rules, stale-after semantics, and annual diff expectations | 1630 | 1630 | 84.0 | strong_with_known_limits | use_state_machine_expectations_before_mutating_next_year_roster_diffs |
| Recursive enrichment work queue | person-level next-source tasks with state-machine urgency and evidence gates | 1483 | 6068 | 81.0 | strong_with_known_limits | run_high_priority_queue_tasks_and_feed_results_back_through_acceptance_ledgers |
| Enrichment execution readiness | mapping from queued enrichment tasks to collectors, commands, parser gaps, and review requirements | 6068 | 6068 | 78.0 | strong_with_known_limits | execute_queue_driven_research_and_roster_lanes_then_build_missing_profile_and_prior_training_collectors |

Learning: a source utility should be judged by the claim surface it supports, not by whether it exists. Official rosters are current-membership truth anchors; PubMed author-query rows are discovery only; PubMed article rows become review-ready only with non-name anchors; current attending profiles are endpoint and training-history candidates until a historical identity bridge exists; and broad search/crawler outputs should feed probe and parser queues before becoming person evidence.

## Evidence Reconciliation Queue

| record_type | status | claim_type | count | avg_priority | avg_confidence |
| --- | --- | --- | --- | --- | --- |
| career_event | needs_review | penn_training_history_candidate | 5 | 118.0 | 0.756 |
| evidence_claim | needs_review | pubmed_article_candidate | 857 | 106.3 | 0.841 |
| npi_candidate | needs_review | npi_candidate | 801 | 105.5 | 0.736 |
| npi_candidate | candidate | npi_candidate | 146 | 69.2 | 0.602 |
| evidence_claim | candidate | pubmed_article_candidate | 1405 | 51.8 | 0.652 |
| career_event | candidate | education_history_candidate | 6 | 47.3 | 0.62 |
| career_event | candidate | prior_training_history_candidate | 6 | 43.7 | 0.573 |
| career_event | candidate | research_interest_candidate | 1 | 40.0 | 0.55 |
| career_event | candidate | personal_profile_candidate | 2 | 39.0 | 0.45 |
| career_event | candidate | current_penn_attending_candidate | 49 | 35.0 | 0.55 |
| npi_candidate | low_signal_npi_candidate | npi_candidate | 126 | 30.9 | 0.47 |
| career_event | candidate | penn_alumni_outcome_candidate | 36 | 23.6 | 0.411 |
| evidence_claim | candidate | pubmed_author_query_candidate | 1336 | 13.6 | 0.204 |

Top queued records:

| record_type | display_name | role | claim_type | status | confidence | priority | review_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| career_event | Patrick Kevin Gleeson, MD, MSCE | attending_or_outcome_candidate | penn_training_history_candidate | needs_review | 0.78 | 122 | Review official profile training-history claim and reconcile to a Penn trainee identity or independent public anchor. |
| career_event | Priya Patel, MD | attending_or_outcome_candidate | penn_training_history_candidate | needs_review | 0.78 | 122 | Review official profile training-history claim and reconcile to a Penn trainee identity or independent public anchor. |
| career_event | Timothy Buckey, MD, MBE | attending_or_outcome_candidate | penn_training_history_candidate | needs_review | 0.78 | 122 | Review official profile training-history claim and reconcile to a Penn trainee identity or independent public anchor. |
| evidence_claim | Michelle Munyikwa, MD, PhD | fellow | pubmed_article_candidate | needs_review | 0.95 | 121 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Samer Mohandes, MD | fellow | pubmed_article_candidate | needs_review | 0.95 | 121 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Samer Mohandes, MD | fellow | pubmed_article_candidate | needs_review | 0.95 | 121 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Samer Mohandes, MD | fellow | pubmed_article_candidate | needs_review | 0.95 | 121 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Rachel Flaugh, MD* | resident | pubmed_article_candidate | needs_review | 0.95 | 117 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Amber Meservey, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Amber Meservey, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Amber Meservey, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Amber Meservey, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Amir Heravi, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Amir Heravi, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Amir Heravi, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Andrew M. Acker, MD | resident | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Bradley Osemwengie, MD | resident | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Brittany Brookner, MD | resident | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Bruk Mekonen, MD, MS | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Carissa E. Livingston, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Caroline Granruth, MD | resident | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Caroline L. Simon, MD | resident | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | China N. Byrns, MD, PhD, MS | resident | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Christopher M. Anthony, DO | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Dania Salih Bacha, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Dania Salih Bacha, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Dania Salih Bacha, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Dania Salih Bacha, MD | fellow | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Danielle Murashige, MD | resident | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |
| evidence_claim | Elisabeth (Elise) Seyferth, MD | resident | pubmed_article_candidate | needs_review | 0.91 | 114 | Review article author, affiliation, topic, and source profile anchors before accepting publication enrichment. |

Learning: candidate evidence needs a ranked reconciliation surface. The queue separates review-ready items, such as article-level PubMed candidates with non-name anchors and official attending profile Penn-training claims, from low-value discovery signals like name-only PubMed query counts.

## Reconciliation Decision Ledger

Decision rows: 4776. Review-ready rows: 921. Person/name rollups: 1488.

Decision counts:

| decision | count |
| --- | --- |
| attending_training_claim_needs_identity_link | 2 |
| attending_training_claim_review_ready | 3 |
| candidate_with_partial_anchor | 121 |
| current_attending_endpoint_candidate | 49 |
| discovery_only | 1336 |
| low_signal_candidate | 1297 |
| needs_secondary_identity_anchor | 727 |
| npi_candidate_with_partial_anchor | 138 |
| npi_low_signal_candidate | 134 |
| npi_secondary_identity_anchor_review | 801 |
| outcome_context_only | 36 |
| profile_context_candidate | 15 |
| review_ready_high_anchor | 5 |
| review_ready_training_topic_anchor | 112 |

Ten-year attending trend window:

| ten_year_trend_window | count |
| --- | --- |
| no | 3 |
| unknown | 100 |
| yes | 2 |

Top review-ready decisions:

| record_type | display_name | role | claim_type | decision | confidence | priority | ten_year_trend_window | source_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| career_event | Patrick Kevin Gleeson, MD, MSCE | attending_or_outcome_candidate | penn_training_history_candidate | attending_training_claim_review_ready | 0.78 | 122 | unknown | https://www3.pennmedicine.org/providers/profile/patrick-gleeson |
| career_event | Priya Patel, MD | attending_or_outcome_candidate | penn_training_history_candidate | attending_training_claim_review_ready | 0.78 | 122 | unknown | https://www3.pennmedicine.org/providers/profile/priya-patel |
| career_event | Timothy Buckey, MD, MBE | attending_or_outcome_candidate | penn_training_history_candidate | attending_training_claim_review_ready | 0.78 | 122 | unknown | https://www3.pennmedicine.org/providers/profile/timothy-buckey |
| evidence_claim | Michelle Munyikwa, MD, PhD | fellow | pubmed_article_candidate | review_ready_high_anchor | 0.95 | 121 |  | https://pubmed.ncbi.nlm.nih.gov/33406326/ |
| evidence_claim | Samer Mohandes, MD | fellow | pubmed_article_candidate | review_ready_high_anchor | 0.95 | 121 |  | https://pubmed.ncbi.nlm.nih.gov/40796935/ |
| evidence_claim | Samer Mohandes, MD | fellow | pubmed_article_candidate | review_ready_high_anchor | 0.95 | 121 |  | https://pubmed.ncbi.nlm.nih.gov/41986737/ |
| evidence_claim | Samer Mohandes, MD | fellow | pubmed_article_candidate | review_ready_high_anchor | 0.95 | 121 |  | https://pubmed.ncbi.nlm.nih.gov/42056516/ |
| evidence_claim | Rachel Flaugh, MD* | resident | pubmed_article_candidate | review_ready_high_anchor | 0.95 | 117 |  | https://pubmed.ncbi.nlm.nih.gov/38299252/ |
| evidence_claim | Amber Meservey, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/31828514/ |
| evidence_claim | Amber Meservey, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/40145043/ |
| evidence_claim | Amber Meservey, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/40404217/ |
| evidence_claim | Amber Meservey, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/41290323/ |
| evidence_claim | Amir Heravi, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/33509400/ |
| evidence_claim | Amir Heravi, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/35675673/ |
| evidence_claim | Amir Heravi, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/36978803/ |
| evidence_claim | Andrew M. Acker, MD | resident | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/37808021/ |
| evidence_claim | Bradley Osemwengie, MD | resident | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/29929716/ |
| evidence_claim | Brittany Brookner, MD | resident | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/38509339/ |
| evidence_claim | Bruk Mekonen, MD, MS | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/40336497/ |
| evidence_claim | Carissa E. Livingston, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/36877449/ |
| evidence_claim | Caroline Granruth, MD | resident | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/36890044/ |
| evidence_claim | Caroline L. Simon, MD | resident | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/36516943/ |
| evidence_claim | China N. Byrns, MD, PhD, MS | resident | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/34115987/ |
| evidence_claim | Christopher M. Anthony, DO | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/34865104/ |
| evidence_claim | Dania Salih Bacha, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/33954783/ |
| evidence_claim | Dania Salih Bacha, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/34687206/ |
| evidence_claim | Dania Salih Bacha, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/38468148/ |
| evidence_claim | Dania Salih Bacha, MD | fellow | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/42162870/ |
| evidence_claim | Danielle Murashige, MD | resident | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/39960981/ |
| evidence_claim | Elisabeth (Elise) Seyferth, MD | resident | pubmed_article_candidate | review_ready_training_topic_anchor | 0.91 | 114 |  | https://pubmed.ncbi.nlm.nih.gov/39658750/ |

Learning: reconciliation should be an explicit decision ledger, not a side effect of queue priority. Review-ready means enough anchors exist for efficient review; accepted truth still requires a manual or stronger automated identity verifier.

## Attending Trend Linkage Assurance

Career-event rows audited: 105. Person/source groups: 70. Groups with current attending endpoints: 49. Groups with Penn-training profile claims: 4. Groups with current trainee name matches: 0.

Linkage statuses:

| linkage_status | count |
| --- | --- |
| current_attending_endpoint_unlinked | 45 |
| current_attending_with_penn_training_claim_unlinked | 4 |
| outcome_context_only_no_person | 36 |
| profile_context_non_penn_training | 15 |
| profile_penn_training_claim_needs_historical_roster | 5 |

Assurance levels:

| assurance_level | count |
| --- | --- |
| 0 | 36 |
| 1 | 60 |
| 2 | 9 |

Top linkage groups:

| display_name | event_count | best_linkage_status | best_trend_link_assurance_level | has_current_attending_endpoint | has_penn_training_claim | has_current_trainee_name_match | event_years |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Emily Gordon, MD, MSEd | 6 | profile_penn_training_claim_needs_historical_roster | 2 | 1 | 1 | 0 | 2002; 2006; 2012 |
| Patrick Kevin Gleeson, MD, MSCE | 3 | profile_penn_training_claim_needs_historical_roster | 2 | 1 | 1 | 0 |  |
| Priya Patel, MD | 2 | profile_penn_training_claim_needs_historical_roster | 2 | 1 | 1 | 0 |  |
| Timothy Buckey, MD, MBE | 3 | profile_penn_training_claim_needs_historical_roster | 2 | 1 | 1 | 0 |  |
| Alana Sagin, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Alison Wakoff Loren, MD, MSCE | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Anar A. Dossumbekova, MD, PhD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Andrea J. Apter, MD, MA, MSc | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Ann Soliman, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Barbara A. Carr | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Bridget Durkin, MD, MBE | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Christine Ciunci, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Christopher A. D'Avella, MD | 2 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Daniel J. Landsburg, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| David M. Mintzer, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Denis Hadjiliadis, MD, PhD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Douglas Eric Guggenheim, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Edward A. Stadtmauer, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Emily Chan, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |
| Erin O. Aakhus, MD | 1 | current_attending_endpoint_unlinked | 1 | 1 | 0 | 0 |  |

Learning: current Penn attending pages are endpoint evidence, not trend-line facts. The current corpus has endpoint-plus-Penn-training groups but no linked historical trainee identity yet, so recent-attending trend claims should remain candidates until a historical roster, alumni page, CV, or independent profile supplies the missing dated Penn trainee link.

## Attending Historical Link Discovery

Groups considered: 4. Seeded source rows: 8. Search observations: 36. Search skipped: False. Candidate rows: 15.

Candidate statuses:

| candidate_status | count |
| --- | --- |
| current_profile_context_candidate | 2 |
| current_profile_training_context_candidate | 3 |
| historical_roster_or_alumni_candidate | 1 |
| historical_training_search_candidate | 4 |
| low_signal_search_result | 1 |
| penn_context_candidate | 3 |
| profile_identity_anchor_candidate | 1 |

Top historical-link candidates:

| display_name | query_kind | candidate_status | confidence | priority | result_domain | probe_title | required_next_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Emily Gordon, MD, MSEd | historical_penn_training | historical_roster_or_alumni_candidate | 0.95 | 120 | www.linkedin.com |  | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |
| Emily Gordon, MD, MSEd | historical_penn_training | historical_training_search_candidate | 0.95 | 95 | www.doximity.com | Dr. Emily Gordon, MD – Philadelphia, PA \| Anesthesiology | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |
| Emily Gordon, MD, MSEd | historical_penn_training | historical_training_search_candidate | 0.95 | 95 | www.pennmedicine.org | Provider Profile \| Penn Medicine | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |
| Emily Gordon, MD, MSEd | historical_penn_training | historical_training_search_candidate | 0.95 | 95 | www.researchgate.net | ResearchGate - Temporarily Unavailable | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |
| Emily Gordon, MD, MSEd | historical_penn_training | historical_training_search_candidate | 0.95 | 95 | www3.pennmedicine.org | Anesthesiologists - Penn Medicine | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |
| Emily Gordon, MD, MSEd | existing_linkage_source_url | current_profile_training_context_candidate | 0.78 | 78 | www3.pennmedicine.org | Emily Gordon - Penn Medicine | Use as current profile/training context only; still requires dated historical roster, alumni, CV, or independent profile bridge for trend acceptance. |
| Priya Patel, MD | existing_linkage_source_url | current_profile_training_context_candidate | 0.78 | 78 | www3.pennmedicine.org | Provider Profile \| Penn Medicine | Use as current profile/training context only; still requires dated historical roster, alumni, CV, or independent profile bridge for trend acceptance. |
| Timothy Buckey, MD, MBE | existing_linkage_source_url | current_profile_training_context_candidate | 0.78 | 78 | www3.pennmedicine.org | Provider Profile \| Penn Medicine | Use as current profile/training context only; still requires dated historical roster, alumni, CV, or independent profile bridge for trend acceptance. |
| Emily Gordon, MD, MSEd | historical_penn_training | profile_identity_anchor_candidate | 0.7 | 70 | www.linkedin.com |  | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |
| Emily Gordon, MD, MSEd | historical_penn_training | low_signal_search_result | 0.6 | 60 | www.mapquest.com |  | Keep only as discovery context unless another source supplies Penn-training or identity anchors. |
| Emily Gordon, MD, MSEd | existing_linkage_source_url | current_profile_context_candidate | 0.55 | 55 | www3.pennmedicine.org | Department of Anesthesiology Education Leadership Team | Use as current profile/training context only; still requires dated historical roster, alumni, CV, or independent profile bridge for trend acceptance. |
| Patrick Kevin Gleeson, MD, MSCE | existing_linkage_source_url | penn_context_candidate | 0.55 | 55 | www3.pennmedicine.org | Section of Allergy and Immunology Faculty | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |
| Patrick Kevin Gleeson, MD, MSCE | existing_linkage_source_url | current_profile_context_candidate | 0.55 | 55 | www3.pennmedicine.org | Provider Profile \| Penn Medicine | Use as current profile/training context only; still requires dated historical roster, alumni, CV, or independent profile bridge for trend acceptance. |
| Priya Patel, MD | existing_linkage_source_url | penn_context_candidate | 0.55 | 55 | www3.pennmedicine.org | Section of Allergy and Immunology Faculty | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |
| Timothy Buckey, MD, MBE | existing_linkage_source_url | penn_context_candidate | 0.55 | 55 | www3.pennmedicine.org | Section of Allergy and Immunology Faculty | Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link. |

Learning: seeded official Penn/provider URLs give a deterministic baseline for trend-link discovery, while broad web search is an optional, rate-limited enrichment utility. Even strong official profile candidates remain review candidates until the page text supplies explicit same-person, Penn-training, program, and date anchors.

## Official Faculty Biosketch Bridge Audit

Target Penn-training current-attending groups: 4. Source observations: 4. Candidate rows: 10. Groups with recent dated bridge candidates: 3.

Bridge statuses:

| bridge_status | count |
| --- | --- |
| dated_recent_official_biosketch_training_bridge_candidate | 3 |
| non_penn_training_context | 6 |
| official_biosketch_research_training_context | 1 |

Top biosketch bridge candidates:

| display_name | bridge_status | training_type | start_year | end_year | ten_year_trend_window | training_line | source_url |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Patrick Kevin Gleeson, MD, MSCE | dated_recent_official_biosketch_training_bridge_candidate | fellowship | 2018 | 2020 | yes | Fellowship, Allergy and Immunology, Hospital of the University of Pennsylvania, Chief Fellow 2019, 2018-2020. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8940694 |
| Patrick Kevin Gleeson, MD, MSCE | official_biosketch_research_training_context | postdoctoral | 2020 | 2022 | yes | Post-doctoral Fellow, University of Pennsylvania, 2020-2022. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8940694 |
| Patrick Kevin Gleeson, MD, MSCE | non_penn_training_context | residency | 2015 | 2018 | yes | Categorical Internal Medicine Residency, Temple University Hospital, 2015-2018. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8940694 |
| Priya Patel, MD | dated_recent_official_biosketch_training_bridge_candidate | fellowship | 2017 | 2019 | yes | Fellow, Allergy & Immunology, Hospital of the University of Pennsylvania, Philadelphia, PA, 2017-2019. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p9009993 |
| Priya Patel, MD | non_penn_training_context | residency | 2016 | 2017 | yes | Chief Resident, Internal Medicine, VA NJ Health Care System, East Orange Campus, Rutgers New Jersey Medical School, 2016-2017. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p9009993 |
| Priya Patel, MD | non_penn_training_context | residency | 2015 | 2016 | yes | Chief Resident, Pediatric and Internal Medicine, Rutgers New Jersey Medical School, Newark, NJ, 2015-2016. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p9009993 |
| Priya Patel, MD | non_penn_training_context | internship | 2012 | 2013 | no | Intern, Pediatrics and Internal Medicine, UMDNJ New Jersey Medical School, Newark, NJ, 2012-2013. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p9009993 |
| Priya Patel, MD | non_penn_training_context | residency | 2013 | 2016 | yes | Resident, Pediatrics and Internal Medicine, Rutgers (former UMDNJ) New Jersey Medical School, Newark, NJ, 2013-2016. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p9009993 |
| Timothy Buckey, MD, MBE | dated_recent_official_biosketch_training_bridge_candidate | fellowship | 2022 | 2024 | yes | Fellowship, Allergy and Immunology, Perelman School of Medicine, University of Pennsylvania, The Children’s Hospital of Philadelphia, 2022-2024. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8497949 |
| Timothy Buckey, MD, MBE | non_penn_training_context | residency | 2019 | 2022 | yes | Residency, Internal Medicine, Katz School of Medicine, Temple University Hospital, Philadelphia, PA, 2019-2022. | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8497949 |

Learning: official Penn Faculty Biosketch pages are a high-quality bridge utility when they provide dated Penn residency/fellowship lines for current faculty. They still remain review candidates rather than accepted trend facts because a profile training line is not the same evidence class as a historical roster or alumni record. Postdoctoral research lines are retained as context, not counted as GME trainee-flow bridges.

## Attending Trend Reconciliation Ledger

Trend groups reconciled: 70. Review-ready recent bridge rows: 3. Groups with current endpoints: 49. Groups with Penn-training claims: 4.

Trend statuses:

| trend_status | count |
| --- | --- |
| context_only_not_trend_ready | 21 |
| current_endpoint_needs_training_claim | 45 |
| historical_link_candidate_review | 1 |
| review_ready_official_biosketch_bridge | 3 |

Top trend reconciliation rows:

| display_name | trend_status | trend_assurance_level | ten_year_trend_window | best_training_type | best_training_end_year | best_source_url | required_next_evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Patrick Kevin Gleeson, MD, MSCE | review_ready_official_biosketch_bridge | 4 | yes | fellowship | 2020 | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8940694 | Review official biosketch training line against the current attending endpoint; after reviewer acceptance, it can support a recent Penn-trained current-attending trend record. |
| Priya Patel, MD | review_ready_official_biosketch_bridge | 4 | yes | fellowship | 2019 | https://www.med.upenn.edu/apps/faculty/index.php/g353/p9009993 | Review official biosketch training line against the current attending endpoint; after reviewer acceptance, it can support a recent Penn-trained current-attending trend record. |
| Timothy Buckey, MD, MBE | review_ready_official_biosketch_bridge | 4 | yes | fellowship | 2024 | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8497949 | Review official biosketch training line against the current attending endpoint; after reviewer acceptance, it can support a recent Penn-trained current-attending trend record. |
| Emily Gordon, MD, MSEd | historical_link_candidate_review | 3 | unknown |  |  |  | Review historical-link candidate for explicit same-person, Penn-training, program, and date anchors. |
| Alana Sagin, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Alison Wakoff Loren, MD, MSCE | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Anar A. Dossumbekova, MD, PhD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Andrea J. Apter, MD, MA, MSc | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Ann Soliman, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Barbara A. Carr | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Bridget Durkin, MD, MBE | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Christine Ciunci, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Christopher A. D'Avella, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Daniel J. Landsburg, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| David M. Mintzer, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Denis Hadjiliadis, MD, PhD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Douglas Eric Guggenheim, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Edward A. Stadtmauer, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Emily Chan, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Erin O. Aakhus, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Geeta Ravi Patel, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Janet Long | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Jesse Kiefer MD MSEd | current_endpoint_needs_training_claim | 1 | yes |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Katherine Courtright, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |
| Kathryn A. McGrath, MD | current_endpoint_needs_training_claim | 1 | unknown |  |  |  | Current Penn attending endpoint exists; seek official profile, CV, or biosketch training evidence. |

Review-ready trend claims:

Materialized review-ready trend claims: 3. People: 3. Rollup rows: 10. Display status: review_ready_not_accepted_trend_fact.

| display_name | trend_claim_type | training_type | training_start_year | training_end_year | source_scope | source_url | display_safety_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Timothy Buckey, MD, MBE | recent_penn_trained_current_attending_candidate | fellowship | 2022 | 2024 | official_penn_faculty_biosketch | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8497949 | review_ready_not_accepted_trend_fact |
| Patrick Kevin Gleeson, MD, MSCE | recent_penn_trained_current_attending_candidate | fellowship | 2018 | 2020 | official_penn_faculty_biosketch | https://www.med.upenn.edu/apps/faculty/index.php/g353/p8940694 | review_ready_not_accepted_trend_fact |
| Priya Patel, MD | recent_penn_trained_current_attending_candidate | fellowship | 2017 | 2019 | official_penn_faculty_biosketch | https://www.med.upenn.edu/apps/faculty/index.php/g353/p9009993 | review_ready_not_accepted_trend_fact |

Trend acceptance audit:

Acceptance rows: 3. Accepted trend facts: 0. Review-ready rows requiring explicit reviewer acceptance: 3.

| display_name | training_end_year | acceptance_status | accepted_trend_fact | acceptance_blocker | recommended_next_action |
| --- | --- | --- | --- | --- | --- |
| Timothy Buckey, MD, MBE | 2024 | review_ready_requires_explicit_reviewer_acceptance | 0 | explicit_reviewer_acceptance_missing | record_explicit_reviewer_acceptance_or_rejection |
| Patrick Kevin Gleeson, MD, MSCE | 2020 | review_ready_requires_explicit_reviewer_acceptance | 0 | explicit_reviewer_acceptance_missing | record_explicit_reviewer_acceptance_or_rejection |
| Priya Patel, MD | 2019 | review_ready_requires_explicit_reviewer_acceptance | 0 | explicit_reviewer_acceptance_missing | record_explicit_reviewer_acceptance_or_rejection |

Reviewer decision queue:

Queue rows: 3. Manual decision rows: 0. Accepted trend facts: 0. Pending reviewer decisions: 3.

| decision_status | count |
| --- | --- |
| pending_reviewer_decision | 3 |

| display_name | reviewer_decision | decision_status | accepted_trend_fact | decision_blocker | recommended_next_action |
| --- | --- | --- | --- | --- | --- |
| Timothy Buckey, MD, MBE | pending | pending_reviewer_decision | 0 | manual_reviewer_decision_missing | record_accept_reject_or_needs_more_evidence_decision |
| Patrick Kevin Gleeson, MD, MSCE | pending | pending_reviewer_decision | 0 | manual_reviewer_decision_missing | record_accept_reject_or_needs_more_evidence_decision |
| Priya Patel, MD | pending | pending_reviewer_decision | 0 | manual_reviewer_decision_missing | record_accept_reject_or_needs_more_evidence_decision |

Trend review rollups:

| rollup_scope | rollup_value | training_type | training_end_year | claim_count | person_count |
| --- | --- | --- | --- | --- | --- |
| corpus | recent_penn_trained_current_attending_candidates | fellowship |  | 3 | 3 |
| source_scope | official_penn_faculty_biosketch | fellowship |  | 3 | 3 |
| ten_year_trend_window | yes | fellowship |  | 3 | 3 |
| training_end_year | 2019 | fellowship | 2019 | 1 | 1 |
| training_end_year | 2020 | fellowship | 2020 | 1 | 1 |
| training_end_year | 2024 | fellowship | 2024 | 1 | 1 |
| training_type | fellowship | fellowship |  | 3 | 3 |
| training_type_end_year | fellowship::2019 | fellowship | 2019 | 1 | 1 |
| training_type_end_year | fellowship::2020 | fellowship | 2020 | 1 | 1 |
| training_type_end_year | fellowship::2024 | fellowship | 2024 | 1 | 1 |

Learning: trend analysis needs its own non-mutating acceptance lane. Endpoint evidence plus a Penn-training profile claim is still not enough. Endpoint plus profile claim plus dated official Penn biosketch GME bridge is review-ready for trend acceptance. Accepted trend facts now require a separate reviewer decision row with a matching claim fingerprint and all confirmation fields set, so stale or partial decisions cannot silently promote changed claims.

## NPPES NPI Registry Candidate Enrichment

NPI queries run: 1257. Candidate rows: 1073. Queries with candidates: 832. Queries with no results: 425. Query errors: 0.

Candidate statuses:

| candidate_status | count |
| --- | --- |
| candidate | 146 |
| low_signal_npi_candidate | 126 |
| needs_review | 801 |

Top NPI primary taxonomies:

| primary_taxonomy | count |
| --- | --- |
| Anesthesiology | 12 |
| Counselor, Mental Health | 9 |
| Counselor, Professional | 4 |
| Dentist | 5 |
| Dentist, General Practice | 6 |
| Dietitian, Registered | 4 |
| Emergency Medicine | 11 |
| Family Medicine | 15 |
| Hospitalist | 7 |
| Internal Medicine | 61 |
| Internal Medicine, Gastroenterology | 5 |
| Internal Medicine, Infectious Disease | 4 |
| Internal Medicine, Nephrology | 7 |
| Nurse Practitioner | 5 |
| Obstetrics & Gynecology | 11 |
| Occupational Therapist | 8 |
| Ophthalmology | 7 |
| Orthopaedic Surgery | 9 |
| Pediatrics | 12 |
| Pharmacist | 11 |

Sample NPI candidates:

| display_name | role | candidate_status | confidence | provider_name | primary_taxonomy | practice_city | practice_state | source_url |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Aardra Rajendran, MD | fellow | needs_review | 0.73 | AARDRA RAJENDRAN | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1750955530 |
| Abigail Black MD | resident | needs_review | 0.73 | ABIGAIL MARIE BLACK MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1487414330 |
| Abigail Taye MD | resident | needs_review | 0.73 | ABIGAIL MESFIN TAYE MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1811784853 |
| Adam Barsouk, MD | resident | needs_review | 0.73 | ADAM BARSOUK MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1689377798 |
| Adam Tuchinsky, DO | fellow | needs_review | 0.77 | ADAM JOSHUA TUCHINSKY DO | Internal Medicine | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1881278729 |
| Ahmed Gawash DO | resident | needs_review | 0.73 | AHMED MOHAMED GAWASH | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1053113985 |
| Akshatha Kiran MD | resident | needs_review | 0.73 | AKSHATHA KIRAN MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1467212431 |
| Akshayaa Chittibabu MD | resident | needs_review | 0.73 | AKSHAYAA KETHINNI CHITTIBABU MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1972305977 |
| Alan Tang, MD, PhD | fellow | needs_review | 0.73 | ALAN TIEN TANG MD PhD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1013536861 |
| Alec Gayner MD | resident | needs_review | 0.73 | ALEC GAYNER | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1184483380 |
| Alexa Larsen, MD, MSc | resident | low_signal_npi_candidate | 0.57 | ALEXANDRA LYNN LARSEN MD, MSc | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1437853173 |
| Alexander Ortiz, MD | fellow | needs_review | 0.73 | ALEXANDER ORTIZ MD | Internal Medicine | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1285196493 |
| Alexandra Leto, MD | fellow | needs_review | 0.67 | ALEXANDRA CAROLINE LETO MD | Internal Medicine | WYNNEWOOD | PA | https://npiregistry.cms.hhs.gov/provider-view/1336723071 |
| Alexandria Nicole Tartt MD | resident | needs_review | 0.73 | ALEXANDRIA TARTT | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1891582441 |
| Alison Leslie MD | resident | needs_review | 0.73 | ALISON LESLIE MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1003676719 |
| Alison Leslie MD | resident | candidate | 0.59 | ALISON FEDORIS LESLIE LCSW | Social Worker, Clinical | PENN VALLEY | PA | https://npiregistry.cms.hhs.gov/provider-view/1568227304 |
| Alison Ranum MD | resident | needs_review | 0.73 | ALISON NICOLE RANUM MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1073200341 |
| Amanda Perez, MD | resident | needs_review | 0.79 | AMANDA ESTRELLITA PEREZ | Internal Medicine | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1770343733 |
| Amanda Perez, MD | resident | candidate | 0.65 | AMANDA LUZ PEREZ | Case Manager/Care Coordinator | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1740838481 |
| Amber Meservey, MD | fellow | needs_review | 0.77 | AMBER JOY MESERVEY MD | Internal Medicine, Pulmonary Disease | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1710448758 |
| Andrea Szabo, MD | resident | needs_review | 0.79 | ANDREA SZABO MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1568112266 |
| Andrea Szabo, MD | resident | low_signal_npi_candidate | 0.55 | ANDREW JOSEPH SZABO D.O. | Surgery | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1023338258 |
| Andrew Jarrah, MD, MBA | fellow | needs_review | 0.73 | ANDREW AMIR JARRAH | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1396205951 |
| Andrew Lin MD | resident | needs_review | 0.73 | ANDREW AUSTIN LIN MD, Ph.D. | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1841092467 |
| Andrew Lin MD | resident | low_signal_npi_candidate | 0.55 | ANDREA LIN MD | Surgery | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1891534566 |
| Andrew Pham, MD | fellow | needs_review | 0.77 | ANDREW TUAN QUOC PHAM | Internal Medicine | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1841878675 |
| Angela Liu, MD | fellow | needs_review | 0.71 | ANGELA JIN LIU MD | Obstetrics & Gynecology | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1700379716 |
| Anitra Persaud, MD | resident | needs_review | 0.73 | ANITRA PERSAUD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1861187866 |
| Anjali Agarwalla, MD | fellow | needs_review | 0.71 | ANJALI AGARWALLA | Internal Medicine | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1558980391 |
| Anjana Murali MD | resident | needs_review | 0.79 | ANJANA MURALI MD | Student in an Organized Health Care Education/Training Program | PHILADELPHIA | PA | https://npiregistry.cms.hhs.gov/provider-view/1508561333 |

Learning: NPPES is an official provider registry and useful as a secondary identity anchor, especially when exact name, PA/Philadelphia location, physician or trainee taxonomy, and program specialty agree. It is not roster truth. Residents and fellows may have missing, stale, student-training, or non-Penn practice data, and name collisions are expected.

## Enrichment Coverage Audit

People audited: 1483. Program/role groups audited: 95. Average coverage score: 61.82.

Coverage bands:

| coverage_band | count |
| --- | --- |
| broad_enrichment_surface | 219 |
| moderate_enrichment_surface | 1081 |
| thin_enrichment_surface | 183 |

Recommended next actions:

| recommended_next_action | count |
| --- | --- |
| collect_article_level_research_candidates | 53 |
| monitor_refresh_and_diff | 203 |
| official_profile_search | 514 |
| organization_alias_review | 387 |
| public_contact_search | 26 |
| reconcile_high_priority_evidence | 259 |
| review_training_state_machine | 22 |
| source_medical_school_background | 15 |
| source_residency_background | 4 |

Lowest-scoring program/role surfaces:

| program_name | role | person_count | avg_coverage_score | profile_coverage_rate | medical_school_coverage_rate | article_candidate_coverage_rate | npi_candidate_coverage_rate | npi_needs_review_coverage_rate | top_recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clinical Microbiology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| GI/Hepatic Pathology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Soft Tissue/Bone Pathology Fellowship | fellow | 1 | 20.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Gynecologic Oncology Fellowship | fellow | 6 | 20.67 | 0.0 | 0.0 | 0.0 | 0.167 | 0.167 | official_profile_search |
| Hematopathology Fellowship | fellow | 4 | 21.0 | 0.0 | 0.0 | 0.0 | 0.25 | 0.25 | official_profile_search |
| Maternal Fetal Medicine Fellowship | fellow | 8 | 21.0 | 0.0 | 0.0 | 0.0 | 0.25 | 0.25 | official_profile_search |
| Surgical Pathology Fellowship | fellow | 6 | 21.67 | 0.0 | 0.0 | 0.0 | 0.5 | 0.333 | official_profile_search |
| Clinical Chemistry Fellowship | fellow | 2 | 22.0 | 0.0 | 0.0 | 0.0 | 0.5 | 0.5 | official_profile_search |
| Cytopathology Fellowship | fellow | 2 | 22.0 | 0.0 | 0.0 | 0.0 | 0.5 | 0.5 | official_profile_search |
| Molecular Genetic Pathology Fellowship | fellow | 2 | 23.0 | 0.0 | 0.0 | 0.0 | 1.0 | 0.5 | official_profile_search |
| Breast Pathology Fellowship | fellow | 1 | 24.0 | 0.0 | 0.0 | 0.0 | 1.0 | 1.0 | official_profile_search |
| Neuropathology Fellowship | fellow | 2 | 24.0 | 0.0 | 0.0 | 0.0 | 1.0 | 1.0 | official_profile_search |
| Transfusion Medicine/Blood Bank Fellowship | fellow | 1 | 24.0 | 0.0 | 0.0 | 0.0 | 1.0 | 1.0 | official_profile_search |
| CHOP Otolaryngology Fellowship | fellow | 4 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Facial Plastic and Reconstructive Surgery Fellowship | fellow | 1 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Foot and Ankle Fellowship | fellow | 2 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Head and Neck Surgical Oncology, Microvascular Reconstruction, and Robotic Surgery Fellowship | fellow | 2 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Neurotology Fellowship | fellow | 1 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Rhinology and Skull Base Surgery Fellowship | fellow | 2 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Shoulder and Elbow Fellowship | fellow | 1 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Sleep Medicine and Surgery Fellowship | fellow | 2 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Spine Fellowship | fellow | 1 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Oral Medicine Residency | resident | 8 | 25.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Otorhinolaryngology Residency | resident | 31 | 26.42 | 0.0 | 0.0 | 0.065 | 0.194 | 0.194 | official_profile_search |
| Adult Reconstructive Orthopedics Fellowship | fellow | 3 | 27.0 | 0.0 | 0.0 | 0.0 | 0.667 | 0.333 | official_profile_search |

Learning: coverage needs to be audited separately from evidence acceptance. This pass shows where the recursive loop should work next: official profile search, organization alias review, article-level research collection, and high-priority reconciliation.

## Utility Observations

| utility_key | sample_size | candidate_claims | accepted_claims | rejected_claims | ambiguous_claims | metrics_json |
| --- | --- | --- | --- | --- | --- | --- |
| official_trainee_profile | 194 | 916 | 194 | 0 | 0 | {"by_claim_type": {"career_interest_candidate": 15, "education_history_candidate": 222, "official_profile_url": 194, "personal_profile_candidate": 606, "prior_training_history_candidate": 62, "research_interest_candidate": 11}, "by_status": {"accepted": 194, "candidate": 916}, "claims": 1110, "display_safety_counts": {"personal_context_not_default_display": 572, "safe_for_default_display": 504, "sensitive_personal_context_restricted": 34}, "orphan_claims_skipped": 0, "people_with_claims": 194, "raw_claims": 1110, "source_rows": 194, "summary": {"by_claim_type": {"career_interest_candidate": 15, "education_history_candidate": 222, "official_profile_url": 194, "personal_profile_candidate": 606, "prior_training_history_candidate": 62, "research_interest_candidate": 11}, "by_role": {"fellow": 334, "resident": 776}, "by_status": {"accepted": 194, "candidate": 916}, "claims": 1110, "csv": "artifacts/data/penn_trainee_profile_claims.csv", "display_safety_counts": {"personal_context_not_default_display": 572, "safe_for_default_display": 504, "sensitive_personal_context_restricted": 34}, "field_counts": {"academic_interests": 11, "alternate_career_interest": 110, "career_interests": 15, "hobbies": 166, "hobbies_interests": 10, "home_state": 35, "hometown": 121, "kids": 34, "medical_school": 191, "philadelphia_interest": 120, "residency_program": 62, "undergraduate": 31, "why_penn": 10}, "generated_at": "2026-06-02T12:34:54.462129+00:00", "input": "artifacts/data/penn_training_people_unique.json", "json": "artifacts/data/penn_trainee_profile_claims.json", "people_with_claims": 194, "policy": "Profile URL links from official rosters are accepted as profile-location facts. Structured profile fields are candidate enrichment with display-safety metadata and do not mutate accepted roster/background truth.", "profile_fetch_status_counts": {"200": 194}, "profiles_with_text": 194, "profiles_with_url": 194, "skipped": {"no_known_profile_fields": 3}, "sources": 194, "sources_json": "artifacts/data/penn_trainee_profile_sources.json"}} |
| openalex_author_search | 0 | 0 | 0 | 0 | 0 | {"collector_resume_supported": true, "current_claims": 0, "rate_limit_observed": true} |
| pubmed_article_reconciliation | 357 | 1405 | 0 | 0 | 857 | {"artifact": "pubmed_article_candidate_claims.json", "claims": 2262, "mean_confidence": 0.7237, "orphan_claims_skipped": 0, "orphan_people_skipped": 0, "raw_claims": 2262, "summary": {"article_claims": 2262, "by_feature": {"article_author_name_match": 2262, "bounded_author_query": 2262, "penn_affiliation": 18, "prior_training_or_education_affiliation": 843, "program_topic_match": 234, "recent_publication": 2020}, "by_status": {"candidate": 1405, "needs_review": 857}, "generated_at": "2026-06-02T12:15:53.752328+00:00", "include_high_collision": false, "max_author_count": 20, "query_claims_considered": 365, "unique_pmids_fetched": 2271}} |
| pubmed_eutilities | 1336 | 2741 | 0 | 0 | 857 | {"claims": 3598, "mean_confidence": 0.5309, "orphan_claims_skipped": 0, "orphan_people_skipped": 0, "raw_claims": 3598} |

## OpenAlex Feature Distribution

| match_features_json | count | avg_confidence |
| --- | --- | --- |

Learning: OpenAlex remains a promising author-disambiguation utility, but the current full-corpus run hit sustained 429 throttling. Record that as source availability/operations evidence, not as rejected person identity evidence.

## PubMed Feature Distribution

| match_features_json | count | avg_confidence |
| --- | --- | --- |
| ["author_query", "high_collision_risk"] | 831 | 0.158 |
| ["author_query", "bounded_result_count"] | 365 | 0.35 |
| ["author_query", "no_results"] | 140 | 0.1 |

Learning: PubMed E-utilities is a strong article database, but author-query search is a weak identity resolver. It should be used after candidate author identity is constrained by OpenAlex/ORCID/profile context, or at article-level with affiliation/coauthor checks.

## PubMed Article-Level Reconciliation

Bounded query claims considered: 365. Unique PMIDs fetched: 2271. Article candidates: 2262.

Article candidate statuses:

| status | count |
| --- | --- |
| candidate | 1405 |
| needs_review | 857 |

Article candidate feature distribution:

| match_features_json | count | avg_confidence |
| --- | --- | --- |
| ["article_author_name_match", "bounded_author_query", "recent_publication"] | 1067 | 0.65 |
| ["article_author_name_match", "bounded_author_query", "prior_training_or_education_affiliation", "recent_publication"] | 706 | 0.83 |
| ["article_author_name_match", "bounded_author_query"] | 217 | 0.62 |
| ["article_author_name_match", "bounded_author_query", "program_topic_match", "recent_publication"] | 118 | 0.73 |
| ["article_author_name_match", "bounded_author_query", "prior_training_or_education_affiliation", "program_topic_match", "recent_publication"] | 111 | 0.91 |
| ["article_author_name_match", "bounded_author_query", "prior_training_or_education_affiliation"] | 21 | 0.8 |
| ["article_author_name_match", "bounded_author_query", "penn_affiliation", "recent_publication"] | 13 | 0.87 |
| ["article_author_name_match", "bounded_author_query", "penn_affiliation", "prior_training_or_education_affiliation", "recent_publication"] | 4 | 0.95 |
| ["article_author_name_match", "bounded_author_query", "program_topic_match"] | 3 | 0.7 |
| ["article_author_name_match", "bounded_author_query", "prior_training_or_education_affiliation", "program_topic_match"] | 1 | 0.88 |
| ["article_author_name_match", "bounded_author_query", "penn_affiliation", "program_topic_match", "recent_publication"] | 1 | 0.95 |

Learning: article-level PubMed XML is materially better than author-query counts because it exposes the target author, affiliation strings, publication year, journal/title, and topic hints. It is still candidate evidence: many records have one strong non-name anchor, but acceptance should require at least two independent anchors or a human review step.

## Official Trainee Profile Enrichment

Roster-linked trainee profiles with text: 194. Claims extracted: 1110. People with profile claims: 194.

Profile claim counts:

| status | claim_type | count | avg_confidence |
| --- | --- | --- | --- |
| accepted | official_profile_url | 194 | 0.9 |
| candidate | career_interest_candidate | 15 | 0.58 |
| candidate | education_history_candidate | 222 | 0.786 |
| candidate | personal_profile_candidate | 606 | 0.522 |
| candidate | prior_training_history_candidate | 62 | 0.78 |
| candidate | research_interest_candidate | 11 | 0.62 |

Display-safety policy counts:

| display_safety_status | count |
| --- | --- |
| personal_context_not_default_display | 572 |
| safe_for_default_display | 504 |
| sensitive_personal_context_restricted | 34 |

Learning: roster-linked official profile pages are strong identity/profile-location anchors and can expose education, residency background, research or career interests, and personal context. The URL fact is accepted when linked from an official roster, but extracted profile fields remain candidate enrichment with display-safety metadata, especially hobbies, home-state, family, and free-text personal snippets.

## Career / Attending Trend Candidates

| event_type | status | count | avg_confidence |
| --- | --- | --- | --- |
| attending_profile_training_history_candidate | candidate | 15 | 0.574 |
| attending_profile_training_history_candidate | needs_review | 5 | 0.756 |
| current_penn_attending_candidate | candidate | 49 | 0.55 |
| penn_alumni_outcome_candidate | candidate | 36 | 0.411 |

Attending profile enrichment:

Profiles attempted: 12. Usable profiles: 10. Claims extracted: 20.

| claim_type | count |
| --- | --- |
| education_history_candidate | 6 |
| penn_training_history_candidate | 5 |
| personal_profile_candidate | 2 |
| prior_training_history_candidate | 6 |
| research_interest_candidate | 1 |

Learning: current faculty pages, provider profiles, and alumni/outcome pages should feed a career-event layer, not the core current-trainee roster. Official profile training-history claims are stronger than source-level outcome prose, but they still remain candidates until reconciled to a prior Penn trainee identity or another independent anchor.

## Public Contact Evidence

| contact_type | contact_scope | verification_status | status | count | avg_confidence |
| --- | --- | --- | --- | --- | --- |
| email | institutional | public_directory_unverified | candidate | 205 | 0.82 |
| email | institutional | public_profile_unverified | candidate | 34 | 0.82 |
| email | institutional | public_roster_unverified | candidate | 74 | 0.82 |

| assurance_status | display_safety_status | required_next_check | count | avg_confidence |
| --- | --- | --- | --- | --- |
| official_public_unverified_contact | public_contact_candidate_not_verified | confirm_contact_on_current_official_source_or_directory | 312 | 0.82 |
| domain_review_required | do_not_display_until_domain_verified | verify_institutional_domain_or_source_typo | 1 | 0.82 |

Learning: public contact channels belong in a separate evidence table because a person can have multiple public contacts from sources with different assurance levels. The assurance layer keeps public contacts as candidates until current-source verification, and it catches domain or format anomalies before display or outreach use.

## Reconciliation Rule Update

For the next pass, accept research enrichment only when at least two non-name anchors agree. Examples: official profile link plus ORCID; OpenAlex Penn affiliation plus specialty-topic match; PubMed affiliation plus coauthor cluster; NPI specialty/location plus official profile.

## Source References

- OpenAlex institutions documentation notes that all OpenAlex institutions have ROR IDs and that parsing author affiliations is nontrivial: https://docs.openalex.org/api-entities/institutions
- NCBI E-utilities are the public API for Entrez databases including PubMed: https://www.ncbi.nlm.nih.gov/home/develop/api/
- ORCID supports organization identifiers including ROR for affiliations: https://info.orcid.org/documentation/integration-guide/working-with-organization-identifiers/
- NPPES provides an official public read API for NPI Registry data: https://npiregistry.cms.hhs.gov/api-page
- ClinicalTrials.gov provides an official API and OpenAPI specification: https://clinicaltrials.gov/data-about-studies/learn-about-api
- WDOMS is a searchable directory of undergraduate medical education programs; listing confirms existence but not accreditation or endorsement unless stated: https://wfme.org/world-directory/
