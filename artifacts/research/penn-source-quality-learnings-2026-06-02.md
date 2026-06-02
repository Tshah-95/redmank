# Penn Source Quality Learnings

Generated: 2026-06-02T15:25:32.370616+00:00

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
| covered_current_roster | 65 |
| discovered_no_current_roster | 12 |
| not_discovered | 14 |

Coverage assurance tiers:

Level-4 supported programs: 49 covering 821 people. Alias/count-review programs: 15. Open denominator gaps: 26.

| assurance_status | count |
| --- | --- |
| alias_method_current_roster_review | 15 |
| direct_normalized_name_current_roster | 30 |
| discovered_source_without_current_roster | 7 |
| exact_resolution_backed_current_roster | 19 |
| exact_resolution_count_conflict_review | 1 |
| not_discovered_by_current_strategy | 14 |
| open_gap_with_alias_review | 5 |

Coverage action queue:

Action rows: 42. Person-impact count: 542.

| action_lane | count |
| --- | --- |
| alias_review | 20 |
| count_conflict_review | 1 |
| parser_or_roster_source_review | 7 |
| source_candidate_probe | 14 |

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

Queue rows: 32. Ready rows: 15. Manual decision rows: 15. Accepted alias mappings: 14. Pending reviewer decisions: 0.

| decision_status | count |
| --- | --- |
| accepted_reviewer_decision | 14 |
| deferred_needs_more_evidence | 1 |
| not_ready_for_reviewer_decision | 17 |

| official_program_name | loaded_program_name | loaded_person_count | reviewer_decision | decision_status | accepted_alias_mapping | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- |
| Internal Medicine - Categorical | Internal Medicine Residency | 173 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Radiology - Diagnostic | Diagnostic Radiology Residency | 54 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Pulmonary Disease and Critical Care Medicine | Pulmonary and Critical Care Fellowship | 34 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Gastroenterology | Gastroenterology and Hepatology Fellowship | 23 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Plastic Surgery - Integrated | Plastic Surgery Residency | 22 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Endocrinology | Endocrinology, Diabetes and Metabolism Fellowship | 21 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Radiology - Interventional, Integrated | Interventional Radiology Integrated Residency | 19 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Internal Medicine - Pediatrics | Penn-CHOP Internal Medicine-Pediatrics Residency | 16 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Infectious Disease | Infectious Diseases Fellowship | 15 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Surgical Pathology (Selective) | Surgical Pathology Fellowship | 6 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Internal Medicine - Dermatology | Combined Internal Medicine-Dermatology Residency | 3 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Gastrointestinal and Hepatic Pathology (Selective) | GI/Hepatic Pathology Fellowship | 2 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Transplant Hepatology | Advanced Gastroenterology and Hepatology Fellowship | 2 | needs_more_evidence | deferred_needs_more_evidence | 0 | collect_additional_program_role_track_or_current_roster_evidence |
| Blood Banking and Transfusion Medicine | Transfusion Medicine/Blood Bank Fellowship | 1 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
| Soft Tissue/Bone (Selective) | Soft Tissue/Bone Pathology Fellowship | 1 | accept_alias_mapping | accepted_reviewer_decision | 1 | materialize_accepted_alias_mapping |
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
| fellowship | Dermatology | Dermatopathology | not_discovered | none |
| fellowship | Dermatology | Micrographic Surgery and Dermatologic Oncology | not_discovered | none |
| residency | Dermatology | Dermatology | discovered_no_current_roster | source_discovery |
| fellowship | Emergency Medicine | Undersea and Hyperbaric Medicine | discovered_no_current_roster | source_discovery |
| residency | Emergency Medicine | Emergency Medicine | discovered_no_current_roster | source_discovery |
| residency | Emergency Medicine | Occupational and Environmental Medicine (Preventative Medicine) | not_discovered | none |
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
| fellowship | Psychiatry | Addiction Psychiatry | not_discovered | none |
| fellowship | Psychiatry | Consultation and Liaison Psychiatry | not_discovered | none |
| fellowship | Psychiatry | Forensic Psychiatry | not_discovered | none |
| fellowship | Psychiatry | Geriatric Psychiatry | not_discovered | none |
| residency | Radiology | Radiology - Interventional, Independent | discovered_no_current_roster | source_discovery |
| fellowship | Surgery | Plastic Surgery | discovered_no_current_roster | source_discovery |

Learning: source discovery is not coverage. An official program-universe table gives the denominator needed for gap accounting, annual recrawls, and institution-level diff views. `covered_current_roster` means we have current people attached; `discovered_no_current_roster` means a program page is known but no current roster people are captured; `not_discovered` names crawl gaps.

## HUP Gap Source Queue

Gap programs probed: 26. Source pages probed: 22. Search query rows: 42. Search observations: 0. Candidate URLs queued: 71.

Search scope: not_discovered. Search enabled: False.

| candidate_status | count |
| --- | --- |
| low_value_candidate | 5 |
| program_context_candidate | 52 |
| roster_source_candidate | 14 |

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
| Radiology - Interventional, Independent | Radiology | roster_source_candidate | 92 | Interventional Radiology Integrated and Independent Residency | https://www3.pennmedicine.org/departments-and-centers/department-of-radiology/education-and-training/residency-programs/irdr-interventional-radiology |
| Plastic Surgery | Surgery | roster_source_candidate | 92 | Plastic Surgery Integrated & Independent Residency - Penn Medicine | https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training/residencies/plastic-surgery |

Learning: coverage gaps need their own crawl state. Official program URLs, discovered context pages, and linked roster-like pages should be queued separately so the next scraper can attack high-priority roster candidates without conflating them with verified person records.

## HUP Gap Roster Extraction

Supported gap roster sources attempted: 36. Sources with records: 31. Person records extracted: 576.

Records by role:

| role | count |
| --- | --- |
| fellow | 82 |
| resident | 494 |

Extraction statuses:

| extraction_status | count |
| --- | --- |
| http_error | 3 |
| no_supported_person_structure | 2 |
| preserved_previous_records_after_refresh_error | 15 |
| records_extracted | 16 |

Denominator-link reconciliation:

Official-linked extracted records: 94. Seed records still missing denominator keys: 482. Loaded memberships from reconciled sources: 551.

| denominator_link_status | count |
| --- | --- |
| official_program_key_no_supported_person_structure | 6 |
| records_extracted_seed_without_denominator_key | 28 |
| records_extracted_with_official_program_key | 3 |
| skipped_already_loaded_official_source | 4 |

Seed roster program-resolution audit:

Resolution rows reviewed: 28. Reviewer-ready exact-resolution records: 418. Review-required records: 64.

| resolution_status | records |
| --- | --- |
| accepted_exact_program_resolution_candidate | 418 |
| review_program_alias_resolution_candidate | 52 |
| source_role_program_type_mismatch_review | 12 |

Learning: queue-driven extraction should stay template-aware. Pages without supported person structure remain source candidates; this avoids converting program context, generic people directories, or ambiguous student-fellow pages into trainee records. Extracted people and denominator coverage closure are separate claims: seed-derived records need an official program key or alias reconciliation before they can close an official HUP program gap.

## Penn-Wide Program Categorization

| program_name | role | count |
| --- | --- | --- |
| Anesthesiology Residency | resident | 97 |
| General Surgery Residency | resident | 75 |
| Diagnostic Radiology Residency | resident | 54 |
| Neurology Residency | resident | 54 |
| Psychiatry Residency | resident | 52 |
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
| clinical_postgraduate | GME_PGY_1 | current | 217 | 0.873 |
| clinical_postgraduate | GME_PGY_2 | current | 218 | 0.893 |
| clinical_postgraduate | GME_PGY_3 | current | 190 | 0.894 |
| clinical_postgraduate | GME_PGY_4 | current | 83 | 0.88 |
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
| expected GME annual advancement around Jul 1 unless program-specific exception | 670 |
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
| US_GME_RESIDENCY_DURATION_UNKNOWN | source_refresh_required | annual_clock | 96 | 0.9 |
| US_GME_RESIDENCY_DURATION_UNKNOWN | source_refresh_required | source_refresh_required | 8 | 0.46 |
| US_MD_PHD_MSTP_VARIABLE | source_refresh_required | source_refresh_required | 225 | 0.762 |

State-machine audit status:

| state_machine_status | count |
| --- | --- |
| annual_clock_active | 659 |
| current_observation | 121 |
| review_required | 23 |
| source_refresh_required | 627 |
| terminal_year_active | 252 |

Clock models:

| clock_model | count |
| --- | --- |
| annual_gme_july | 1019 |
| refresh_from_source | 13 |
| review_required | 23 |
| source_refresh_required | 627 |

Auto-advance candidate rows: 659. Completion candidate rows: 252. Stale/review rows: 23.

Learning: roster strings should become normalized state observations with explicit clocks and program lifecycle semantics. PGY and fellowship-year states can be annual-clock states, but terminal-year, unknown-duration, research, chief, and source-ambiguous states need different refresh/exit behavior. Lifecycle codes are local `redmank` codes until external ACGME/ERAS/NRMP identifiers are source-backed. The audit layer makes that operational: a row is only stale, advanceable, or removable when its lifecycle rule says so.

## Longitudinal Change Readiness

Projected refresh date: 2027-08-15. State rows: 1682. Person rows: 1535. Program rows: 96.

Readiness statuses:

| readiness_status | count |
| --- | --- |
| active_no_change_expected | 13 |
| expected_advancement_window | 659 |
| expected_completion_window | 252 |
| review_required_window | 23 |
| source_refresh_required_window | 627 |
| stale_without_transition_review | 108 |

Missing-on-refresh expectations:

| missing_expectation | count |
| --- | --- |
| absence_requires_source_reconciliation | 758 |
| expected_absence_after_completion | 252 |
| unexpected_absence_review | 672 |

Same-stage-on-refresh expectations:

| same_stage_expectation | count |
| --- | --- |
| same_stage_after_expected_transition_review | 659 |
| same_stage_expected | 13 |
| same_stage_requires_fresh_source | 758 |
| same_terminal_stage_after_completion_review | 252 |

Advancement due rows: 1498. Completion-window rows: 252. Source-refresh-required rows: 627. Human-review rows: 131.

Learning: annual diffs should be state-machine informed before they are person-table mutations. A missing terminal-year fellow after the stale-after date is likely completion; a missing PGY-2 before the expected exit is a review item; an unchanged MSTP PhD-phase student needs a fresh source rather than an inferred clock advancement.

## Transition Plan Ledger

Plan rows: 1682. Rollup rows: 226. Auto-classifiable transition rows: 911. Fresh-observation-required rows: 1669.

Policy lanes:

| policy_lane | count |
| --- | --- |
| carry_forward_no_change | 13 |
| deterministic_expected_advancement | 659 |
| deterministic_expected_completion | 252 |
| manual_review_required | 131 |
| source_refresh_required | 627 |

Diff readiness:

| diff_readiness_status | count |
| --- | --- |
| diff_expected_change_classifiable | 911 |
| diff_no_change_expected | 13 |
| diff_review_bound | 131 |
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
| penn_trainee_profile_department_people_1652_frederick_allen_3c3ae7acd3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1652_frederick_allen_3c3ae7acd3 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1653_maria_arisi_00d6da9c48 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1653_maria_arisi_00d6da9c48 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1655_miles_black_6a4faf547c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1655_miles_black_6a4faf547c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1658_meaghan_dougher_d08376165f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1658_meaghan_dougher_d08376165f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1661_cooper_schwartz_cd816e8997 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1661_cooper_schwartz_cd816e8997 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1662_anne_wang_e90d7fcc66 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1662_anne_wang_e90d7fcc66 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1722_alessandro_brunetti_6493b01aa4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1722_alessandro_brunetti_6493b01aa4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1723_gregory_chen_3c168e392e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1723_gregory_chen_3c168e392e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1724_wei_du_88b6c2b89a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1724_wei_du_88b6c2b89a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1725_erika_johnson_662c61962d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1725_erika_johnson_662c61962d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1727_olivia_leung_5b2e7fb526 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1727_olivia_leung_5b2e7fb526 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1728_keshia_mora_761634a15d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1728_keshia_mora_761634a15d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1729_fernanda_tirado_28d518c9a6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1729_fernanda_tirado_28d518c9a6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1730_selemon_walle_323c1143da | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1730_selemon_walle_323c1143da | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1814_abiana_adamson_9de22a4bfd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1814_abiana_adamson_9de22a4bfd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1815_daniel_akuma_27db5452be | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1815_daniel_akuma_27db5452be | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1816_lamarque_coke_6ec5452750 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1816_lamarque_coke_6ec5452750 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1817_anna_davidian_f00d5173bc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1817_anna_davidian_f00d5173bc | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1818_niaz_khan_5eef657e1f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1818_niaz_khan_5eef657e1f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1819_matthew_miller_98d65b02c8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1819_matthew_miller_98d65b02c8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1820_natalie_moore_28615feb23 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1820_natalie_moore_28615feb23 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1821_pravin_patel_2e69d8c8e5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1821_pravin_patel_2e69d8c8e5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1822_derek_sung_64d821c1b3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1822_derek_sung_64d821c1b3 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1823_alexandra_tatarian_1fca7bc153 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1823_alexandra_tatarian_1fca7bc153 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1824_natalie_tupper_8123e8584d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1824_natalie_tupper_8123e8584d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1825_nitin_vaswani_4451f5cfa5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1825_nitin_vaswani_4451f5cfa5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1885_fang_bian_11aa1c17be | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1886_xingchen_monica_li_b86cbbd577 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1887_john_sagrati_f1c462ebde | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1888_chenxu_shi_5cc9a9c51e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1889_qing_yu_57eee34a50 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1890_xiao_zhou_e5cbd6da00 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1892_eman_al_haddad_0edbf2bd83 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1892_eman_al_haddad_0edbf2bd83 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1893_yacob_bizuneh_d79f564b9e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1893_yacob_bizuneh_d79f564b9e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1894_yaelin_caba_silverio_1c80cc48b4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1894_yaelin_caba_silverio_1c80cc48b4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1895_chuan_hao_alex_chen_6a897eb032 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1895_chuan_hao_alex_chen_6a897eb032 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1896_charles_danan_3534c2ef1c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1896_charles_danan_3534c2ef1c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1897_jose_manuel_martin_castelli_c5f3e47187 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1897_jose_manuel_martin_castelli_c5f3e47187 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1898_iniobong_ntukidem_bd10e6ac63 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1898_iniobong_ntukidem_bd10e6ac63 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1899_ranjitha_pratap_nair_1651dd2861 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1899_ranjitha_pratap_nair_1651dd2861 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1900_leslie_roman_3a3b673ebd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1900_leslie_roman_3a3b673ebd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1901_henry_sanchez_04458dc4ad | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1901_henry_sanchez_04458dc4ad | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1902_kevin_yang_100a945463 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1902_kevin_yang_100a945463 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_department_people_1903_denise_zieba_78c721d17d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_department_people_1903_denise_zieba_78c721d17d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_0b1e81b69b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_0b1e81b69b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_0cfdd42206 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_0cfdd42206 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_0eeb893129 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_0eeb893129 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_15242a1f32 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_15242a1f32 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_161687bf84 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_161687bf84 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_1cab33bb1d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_1cab33bb1d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_26feaef620 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_26feaef620 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_29488055c4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_29488055c4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_30669b3fbd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_30669b3fbd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_3a4fda0b4f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_3a4fda0b4f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_4763289fb8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_4763289fb8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_5095461fec | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_5095461fec | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_537283aa6c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_537283aa6c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_5d5ada8419 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_5d5ada8419 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_5d81534711 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_5d81534711 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_6c0bbdd54e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_6c0bbdd54e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_77e9ec7e92 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_77e9ec7e92 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_80beecc545 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_80beecc545 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_8945e719d1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_8945e719d1 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_92e4277eac | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_92e4277eac | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_a61f6f7fcb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_a61f6f7fcb | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_b933c18f97 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_b933c18f97 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_bb63c51a68 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_bb63c51a68 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_c40d17d193 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_c40d17d193 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_d5af2ba98e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_d5af2ba98e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_d92045db80 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_d92045db80 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_ec472aa77a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_ec472aa77a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_efce1f302a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_efce1f302a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_f8de7aaf41 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_f8de7aaf41 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_fa699ec55a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_fa699ec55a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_fc4d64bbf5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_anesthesiology_and_critical_care_education_and_t_fc4d64bbf5 | candidate | education_history_candidate | 1 | 0.82 |
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
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_20c3357188 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_20c3357188 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_27cf2930b7 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_27cf2930b7 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_27cf2930b7 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_3ee39a1aa5 | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_departments_and_centers_department_of_medicine_divisions_infectious_dise_3ee39a1aa5 | candidate | education_history_candidate | 3 | 0.66 |
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
| penn_trainee_profile_departments_and_centers_department_of_medicine_education_and_training_in_64293d58d1 | candidate | education_history_candidate | 1 | 0.82 |
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
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_03dcc0ff9a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_03dcc0ff9a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_03dcc0ff9a | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0cc57f516e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0cc57f516e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0cc57f516e | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0e855c6325 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0e855c6325 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0e855c6325 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0e9d7832f5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0e9d7832f5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_0e9d7832f5 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_191f5542e4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_191f5542e4 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_191f5542e4 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_238ec5b5a5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_238ec5b5a5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_238ec5b5a5 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_26fb8d64ac | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_26fb8d64ac | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_26fb8d64ac | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_30fb0d3d54 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_30fb0d3d54 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_30fb0d3d54 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_391fae59d5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_391fae59d5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_391fae59d5 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_4b9a1d2486 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_4b9a1d2486 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_4b9a1d2486 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_55fe506b82 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_55fe506b82 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_55fe506b82 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_60217c6ac6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_60217c6ac6 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_60217c6ac6 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_8a521786b3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_8a521786b3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_8a521786b3 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_8e398d3e1f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_8e398d3e1f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_8e398d3e1f | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_975feba7b3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_975feba7b3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_975feba7b3 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_a628e739b8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_a628e739b8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_a628e739b8 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_ace4e55a8f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_ace4e55a8f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_ace4e55a8f | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_c2488c5524 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_c2488c5524 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_c2488c5524 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_cf0c838f6d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_cf0c838f6d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_cf0c838f6d | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_d1791e9d22 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_d1791e9d22 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_d1791e9d22 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_dc14c223a9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_dc14c223a9 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_dc14c223a9 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e3a5ee4ca1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e3a5ee4ca1 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e3a5ee4ca1 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e6d78fb7bd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e6d78fb7bd | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e6d78fb7bd | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e70d755a45 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e70d755a45 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e70d755a45 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e8bea3a98f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_e8bea3a98f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_ed8ede9205 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_ed8ede9205 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_ed8ede9205 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_f13948d386 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_f13948d386 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_f13948d386 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_feed21a0ea | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_feed21a0ea | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_f_feed21a0ea | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_00a4b11e6a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_00a4b11e6a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_03126ca925 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_03126ca925 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_040439adcb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_040439adcb | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_04c2e0d208 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_04c2e0d208 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_0a3cdee189 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_0a3cdee189 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_0c40367071 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_0c40367071 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_0faf6a5032 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_0faf6a5032 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_118c57f5ea | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_118c57f5ea | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_1a0b2c22b3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_1a0b2c22b3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_20c0edc3ed | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_20c0edc3ed | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_20c5d389a0 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_20c5d389a0 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_21b018f12b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_21b018f12b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_2244f7973f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_2244f7973f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_2c71d97f0a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_2c71d97f0a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_31914f637c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_31914f637c | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4358a2cdeb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4358a2cdeb | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_442144cc83 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_442144cc83 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4475664a06 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4475664a06 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_45c472ff6f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_45c472ff6f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4666228d02 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4666228d02 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4c6c27a281 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4c6c27a281 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4f3f9e2a25 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_4f3f9e2a25 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_50f6fdaddb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_50f6fdaddb | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_5ad9d683c6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_5ad9d683c6 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_5c466ecdc7 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_5c466ecdc7 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_5f227f0886 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_5f227f0886 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_63196a8fd9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_63196a8fd9 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_6893df5dd3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_6893df5dd3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_68d7cd426e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_68d7cd426e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_6a5391f90d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_6a5391f90d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_6d725fad97 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_6d725fad97 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_7359b8fad5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_7359b8fad5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_7460845236 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_7460845236 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_76038f1edd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_76038f1edd | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_76cfef84a6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_76cfef84a6 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_7ca62b1d69 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_7ca62b1d69 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_7ce023b964 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_7ce023b964 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_881d1e1ecf | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_881d1e1ecf | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_898eb4aa24 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_898eb4aa24 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_8b795c2156 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_8b795c2156 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_934d8a64fc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_934d8a64fc | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_996b154b2b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_996b154b2b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_9b948f08bd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_9b948f08bd | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a1c6c4b7f5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a1c6c4b7f5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a46431aa6d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a46431aa6d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a5f69fbcac | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a5f69fbcac | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a67ac5baf1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a67ac5baf1 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a6d81c6a21 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_a6d81c6a21 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_abaefeaeac | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_abaefeaeac | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_ba2d814dcc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_ba2d814dcc | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_bc3ea8cfbe | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_bc3ea8cfbe | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_bd3f7409fa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_bd3f7409fa | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_c04e14959c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_c04e14959c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_c08bd5558e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_c08bd5558e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_c493d8b6db | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_c493d8b6db | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_ca13d78538 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_ca13d78538 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_cdb0b9a9fe | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_cdb0b9a9fe | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_cf51ff97fa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_cf51ff97fa | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_d0fde81e46 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_d0fde81e46 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_d688e80687 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_d688e80687 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_d7cef74ceb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_d7cef74ceb | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_d96e73eec5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_d96e73eec5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_dc72274486 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_dc72274486 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e39182a52e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e39182a52e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e4672df077 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e4672df077 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e688b97c76 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e688b97c76 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e8061037db | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e8061037db | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e94cbf398c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_e94cbf398c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_eeb44d4917 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_eeb44d4917 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_f004fcb068 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_f004fcb068 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_f443f185a5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_f443f185a5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_f6a5d4d76f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_f6a5d4d76f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_ff5f10fbf4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_radiology_education_and_training_r_ff5f10fbf4 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_0a394b178b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_0a394b178b | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_0a394b178b | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_15a99bdc8c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_15a99bdc8c | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_15a99bdc8c | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_193c76eb8c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_193c76eb8c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_193c76eb8c | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_19c97cd7f2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_2808dac58e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_2808dac58e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_2c75ea52b4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_2c75ea52b4 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_2ec9582ced | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_2ec9582ced | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_3697c73fcb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_3697c73fcb | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_3697c73fcb | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_4c0a25917c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_5430a03551 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_5430a03551 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_5430a03551 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_6083df1f77 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_6083df1f77 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_6083df1f77 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_6977c1b40d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_6977c1b40d | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_6977c1b40d | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_6a6822db17 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_6e6a583482 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_912c778c6e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_912c778c6e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_912c778c6e | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_94cd8d1212 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_94cd8d1212 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_94cd8d1212 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_9add2cbda7 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_9add2cbda7 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_9add2cbda7 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_b5a6ea5b31 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_b5a6ea5b31 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_b5a6ea5b31 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_bc521a3618 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c08d8bcf85 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c08d8bcf85 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c08d8bcf85 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c1ced575dd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c40ecf5997 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c40ecf5997 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c40ecf5997 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c6e3dcd561 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c6e3dcd561 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_c6e3dcd561 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_f25e710a7d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_f25e710a7d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_fel_f25e710a7d | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_042c8f55f5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_042c8f55f5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0888ec0e2d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0888ec0e2d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0ae1f37341 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0ae1f37341 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0bf9af5d8f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0bf9af5d8f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0c22fc8a50 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0c22fc8a50 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0cda5df21e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0cda5df21e | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0d58bf3d35 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_0d58bf3d35 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_11af1dd220 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_11af1dd220 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_11bc65f89a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_11bc65f89a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_125492accb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_125492accb | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1278826dd6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1278826dd6 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_12a2703f61 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_12a2703f61 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_14626108e8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_14626108e8 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1906bdad29 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1906bdad29 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1b799119b7 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1b799119b7 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1d2b71afc8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1d2b71afc8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1e833cf86d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_1e833cf86d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_20f19b7393 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_20f19b7393 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_2472ad01aa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_2472ad01aa | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_24d10d4caf | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_24d10d4caf | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_261fea15f7 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_261fea15f7 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_27874844c3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_27874844c3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_2b091fa2e1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_2b091fa2e1 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_2c671e4f25 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_2c671e4f25 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_31f51582a3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_31f51582a3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_32845ee01f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_32845ee01f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_36dde9837f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_36dde9837f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3ae6330583 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3ae6330583 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3b03e8dedc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3b03e8dedc | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3b0474c48b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3b0474c48b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3b637246ed | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3b637246ed | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3c51cfa6c4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3c51cfa6c4 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3cde59d7a1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3cde59d7a1 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3da8976482 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3da8976482 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3dc3f0a5d8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3dc3f0a5d8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3f8a9308fc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_3f8a9308fc | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_44394001fc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_44394001fc | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_46ebd3a749 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_46ebd3a749 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_48bdbe97aa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_48bdbe97aa | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4ac63a3583 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4ac63a3583 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4cc9fa0acf | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4cc9fa0acf | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4cca193f40 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4cca193f40 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4db08e8207 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4db08e8207 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4e9e6c77a5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4e9e6c77a5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4f966fce33 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_4f966fce33 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_530f3192f8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_530f3192f8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_542cd61393 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_542cd61393 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5531640bc1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5531640bc1 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_563c476c7b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_563c476c7b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5779970ada | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5779970ada | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_579db468fc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_579db468fc | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_57a6491834 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_57a6491834 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5a3987d569 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5a3987d569 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5cd3c62d5c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5cd3c62d5c | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5f67989c87 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_5f67989c87 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_6297f105aa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_6297f105aa | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_62d74e08e3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_62d74e08e3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_68fbd3b925 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_68fbd3b925 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_70b9e89c9d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_70b9e89c9d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_72d3dfc369 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_72d3dfc369 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_77d50889da | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_77d50889da | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7ab522b0ba | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7ab522b0ba | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7b896deeb6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7b896deeb6 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7bc2013f57 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7bc2013f57 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7d4306d7db | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7d4306d7db | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7de8528e11 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7de8528e11 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7e93b82241 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_7e93b82241 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_81b0e3b2e3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_81b0e3b2e3 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_82478220cf | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_82478220cf | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8550c24a54 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8550c24a54 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_899849d105 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_899849d105 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8c61fad336 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8c61fad336 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8c9693358f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8c9693358f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8dbd262714 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8dbd262714 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8fc165c956 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_8fc165c956 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_925ed9628c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_925ed9628c | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_93264bddef | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_93264bddef | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_94ce6e3537 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_94ce6e3537 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9507406863 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9507406863 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_96d7cbfc74 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_96d7cbfc74 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_98f48c70dd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_98f48c70dd | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9ae49e7ea4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9ae49e7ea4 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9b46e0b9c8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9b46e0b9c8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9ccf527565 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9ccf527565 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9dd8b21675 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9dd8b21675 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9e402229a1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9e402229a1 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9f9071389b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_9f9071389b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_a0dac9d486 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_a0dac9d486 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_a357471575 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_a357471575 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_a562befa8f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_a562befa8f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_a8f057e867 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_a8f057e867 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ab1dffe249 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ab1dffe249 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ac7c160810 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ac7c160810 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ae169cb046 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ae169cb046 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_af45117bce | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_af45117bce | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_af8292c79a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_af8292c79a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b10ad42063 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b10ad42063 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b1efa87c87 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b1efa87c87 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b1efa87c87 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b2fc8a3837 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b2fc8a3837 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b3410814a4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b3410814a4 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b612e7b7e8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b612e7b7e8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b7ab2aa956 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b7ab2aa956 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b9067e4460 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_b9067e4460 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_bfabd9ea36 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_bfabd9ea36 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_c139487599 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_c139487599 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_c1b2d67c6c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_c1b2d67c6c | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_c73e749c31 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_c73e749c31 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_c857dd3218 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_c857dd3218 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_cd99511885 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_cd99511885 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_cfd7950ef9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_cfd7950ef9 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_d3fcc1f722 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_d3fcc1f722 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_d4e3c67626 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_d4e3c67626 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_db1741bbd1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_db1741bbd1 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_dde8a9b229 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_dde8a9b229 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_df4a2ea9c3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_df4a2ea9c3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_dffddfe113 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_dffddfe113 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e01835b8c8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e01835b8c8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e1def0dbd9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e1def0dbd9 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e56f7a9e05 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e56f7a9e05 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e653b99661 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e653b99661 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e688a0898d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e688a0898d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e6cbcafdaf | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e6cbcafdaf | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e74d11988a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e74d11988a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e88870ab33 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e88870ab33 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e88870ab33 | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e98ae5124b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_e98ae5124b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ec6d80d32e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ec6d80d32e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_edd63b044e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_edd63b044e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ee3261db11 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_ee3261db11 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_f537ac75bb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_f537ac75bb | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_fa16869494 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_fa16869494 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_fa248e9e9e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_fa248e9e9e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_fb6e242a9b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_fb6e242a9b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_fda6ae6a3a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_department_of_surgery_education_and_training_res_fda6ae6a3a | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_01ab0eb8bf | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_01ab0eb8bf | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_04110847ee | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_04110847ee | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_06c921a273 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_06c921a273 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_0c35a36f7d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_0c35a36f7d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_0d69bdd8d4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_0d69bdd8d4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_11ca3d8211 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_11ca3d8211 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_1858b7762a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_1858b7762a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_1f3cbc86b6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_1f3cbc86b6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_2157ff8014 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_2157ff8014 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_27bc8c0b24 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_27bc8c0b24 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_2f40523214 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_2f40523214 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_400f405c69 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_400f405c69 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_504f9957a2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_504f9957a2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_660e9b07e5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_660e9b07e5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_67f3bd387e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_67f3bd387e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_6db8e472d4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_6db8e472d4 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_7e2c32355d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_7e2c32355d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_80b75d922d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_80b75d922d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_861e38edb0 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_861e38edb0 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_8919ce4cb9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_8919ce4cb9 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_89e923cdc5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_a3019c2dac | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_a3019c2dac | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_a9ca70358f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_a9ca70358f | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_c0ab7c680e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_c0ab7c680e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_c1f01e0876 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_c1f01e0876 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_c4e5c66998 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_c4e5c66998 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_c95eae9a95 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_c95eae9a95 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_ca97918778 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_ca97918778 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_cb81f8f0dc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_cb81f8f0dc | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_d2b405bbc9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_d2b405bbc9 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_dd0cca91c7 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_dd0cca91c7 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_e575704232 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_e575704232 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_f7ee28ed8c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_f7ee28ed8c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_fbead92087 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_fbead92087 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_fe37d22999 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_family_medicine_and_community_health_education_a_fe37d22999 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_0254620ede | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_0254620ede | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_0588a28272 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_0588a28272 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_0b35a127a3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_0b35a127a3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_11a9a01c47 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_11a9a01c47 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_12b778005b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_12b778005b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_1b01343327 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_1b01343327 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_200f12fa1b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_200f12fa1b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_3ea061d550 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_3ea061d550 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_46b143a378 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_46b143a378 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_530ca5aa6f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_530ca5aa6f | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_6b58c72430 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_6b58c72430 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_6ba0a277b9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_6ba0a277b9 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_6f22c445bf | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_6f22c445bf | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_7203b03a49 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_7203b03a49 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_7c8c859cab | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_7c8c859cab | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_8306cf8fa2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_8306cf8fa2 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_8bf1370950 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_8bf1370950 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_a712b0725f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_a712b0725f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_aa87500d10 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_aa87500d10 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_aa97a6d347 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_aa97a6d347 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_aaec97355f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_aaec97355f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_ab5248ce3a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_ab5248ce3a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_c277771cb6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_c277771cb6 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_c844af0f82 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_c844af0f82 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_ce722563ac | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_ce722563ac | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_d1fd414a6d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_d1fd414a6d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_ec8acfdd2d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_ec8acfdd2d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_f42698d9d1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_f42698d9d1 | candidate | education_history_candidate | 3 | 0.66 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_f43aeed9ee | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_f43aeed9ee | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_f8e1844e81 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_f8e1844e81 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_f9becaad0c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_f9becaad0c | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_fc94460e62 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_obstetrics_and_gynecology_education_and_training_fc94460e62 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_04128bfa39 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_04128bfa39 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_0758135160 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_0758135160 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_131086b6ec | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_131086b6ec | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_1fa3ae393d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_1fa3ae393d | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_232d15b8d8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_232d15b8d8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_26db75696c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_26db75696c | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_2c32a8bcd2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_2c32a8bcd2 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_31c0fa87bd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_31c0fa87bd | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_3ffd4cd578 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_3ffd4cd578 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_416052f114 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_416052f114 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_5259148807 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_5259148807 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_5eeb097636 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_5eeb097636 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_63f109a4ae | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_63f109a4ae | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_77df1cbaf0 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_77df1cbaf0 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_79cb306b53 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_79cb306b53 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_7d921b9792 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_7d921b9792 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_810a850521 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_810a850521 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_840edfd66b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_840edfd66b | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_842c2713a8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_842c2713a8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_858f78becc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_858f78becc | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_8a3b0b15f1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_8a3b0b15f1 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_8ac557ca7e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_8ac557ca7e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_974fa4b5d5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_974fa4b5d5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_a029ada37e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_a029ada37e | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_a4e5098a18 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_a4e5098a18 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_a5d960434f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_a5d960434f | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_abe563ab6a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_abe563ab6a | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_bbc94e084c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_bbc94e084c | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_c05d2ecc89 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_c05d2ecc89 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_c305ff2edf | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_c305ff2edf | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_c4f3a6c9d5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_c4f3a6c9d5 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_c78a2c25ce | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_c78a2c25ce | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_cf6a34adf8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_cf6a34adf8 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_e8d24a94da | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_e8d24a94da | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_eb2bd437a9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_eb2bd437a9 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_eeaef294e3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_eeaef294e3 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_f2337e3b14 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_f2337e3b14 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_fdc0c966e2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_orthopaedic_surgery_education_and_training_resid_fdc0c966e2 | candidate | education_history_candidate | 2 | 0.7 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_16cb520b33 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_16cb520b33 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_18fd20a0c7 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_18fd20a0c7 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_24edae82db | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_24edae82db | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_3f5fe386ba | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_3f5fe386ba | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_56863072c7 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_56863072c7 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_678329d0bc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_678329d0bc | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_8a1b4b868e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_8a1b4b868e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_9279d79b35 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_9279d79b35 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_968e3236a8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_968e3236a8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_9ef4bc60d2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_9ef4bc60d2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_ae602f1cb1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_ae602f1cb1 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_bf47b914cb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_bf47b914cb | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_e517961f7b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_e517961f7b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_e9938818c8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_e9938818c8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_f13d0732b5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_f13d0732b5 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_f91c5a68b0 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_departments_and_centers_physical_medicine_and_rehabilitation_education_a_f91c5a68b0 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_002697ab52 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_002697ab52 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0404cc8243 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_0404cc8243 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0404cc8243 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_0404cc8243 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_09e2d83d50 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_09e2d83d50 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_09e2d83d50 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_09e2d83d50 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0ae39a239e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_0ae39a239e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0ae39a239e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_0ae39a239e | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0c57f0d3f3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_0c57f0d3f3 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0c57f0d3f3 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_0c57f0d3f3 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0cd155cd43 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_0cd155cd43 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0cd155cd43 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_0d7cdd8958 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_0d7cdd8958 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0d7cdd8958 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_0d7cdd8958 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_0f68a32cda | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_0f68a32cda | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_0f68a32cda | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_0f68a32cda | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_106dbe9da5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_106dbe9da5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_106dbe9da5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_106dbe9da5 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_10b0a357c8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_10b0a357c8 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_10ba27e10d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_10ba27e10d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_10ba27e10d | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_10c0f21c60 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_10c0f21c60 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_10c0f21c60 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_10c0f21c60 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_11f785d482 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_11f785d482 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_11f785d482 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_11f785d482 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_14bc5b4b56 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_14bc5b4b56 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_14bc5b4b56 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_14bc5b4b56 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_14e4f47fc4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_14e4f47fc4 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_14e4f47fc4 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_14e4f47fc4 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_157b4f0867 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_157b4f0867 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_157b4f0867 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_157b4f0867 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_164e1a7f61 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_164e1a7f61 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_164e1a7f61 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_164e1a7f61 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_178d51774e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_178d51774e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_178d51774e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_178d51774e | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_185f14c045 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_185f14c045 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_185f14c045 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_185f14c045 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_1a33db9c2c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_1a33db9c2c | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1a33db9c2c | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_1a33db9c2c | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1a626f5871 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_1a626f5871 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1a626f5871 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_1a626f5871 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1a8e03a25b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_1a8e03a25b | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1a8e03a25b | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_1a8e03a25b | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_1b9f75c888 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_1b9f75c888 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1b9f75c888 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_1b9f75c888 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1c12bcbae6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_1c12bcbae6 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1c12bcbae6 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_1c2d29af22 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_1c2d29af22 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1c2d29af22 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_1c2d29af22 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_1df15457ff | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_1df15457ff | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_1df15457ff | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_1df15457ff | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_1efebd15b9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_1efebd15b9 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_20f106233a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_20f106233a | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_20f106233a | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_20f106233a | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_21888ef7f4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_21888ef7f4 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_21888ef7f4 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_21888ef7f4 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_27288e6969 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_27288e6969 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2738d899cb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_2738d899cb | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_279fbd48c5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_279fbd48c5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_279fbd48c5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_279fbd48c5 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_27b5abf404 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_27b5abf404 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_27b5abf404 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_27b5abf404 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_27fd06b2dc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_27fd06b2dc | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_27fd06b2dc | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_27fd06b2dc | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_29054c7b22 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_29054c7b22 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_29054c7b22 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_29054c7b22 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_291a14d1cd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_291a14d1cd | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_291a14d1cd | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_2a4dcdf4a4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_2a4dcdf4a4 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2a4dcdf4a4 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_2a4dcdf4a4 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2d00ec44cd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_2d00ec44cd | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2d00ec44cd | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_2d00ec44cd | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2d118d89c5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_2d118d89c5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2d118d89c5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_2d118d89c5 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2e1319cee1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_2e1319cee1 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2e1319cee1 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_2e1319cee1 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2e98ceb38c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_2e98ceb38c | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2e98ceb38c | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_2e98ceb38c | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_2fce536f04 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_2fce536f04 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_2fce536f04 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_2fce536f04 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_32efb7b878 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_32efb7b878 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_32efb7b878 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_32efb7b878 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_350cc2874e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_350cc2874e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_350cc2874e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_350cc2874e | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_357978c698 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_357978c698 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_357978c698 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_357978c698 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_36cc84eed8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_36cc84eed8 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_36cc84eed8 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_372503d3c8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_372503d3c8 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_372503d3c8 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_37701c6f58 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_37701c6f58 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_37701c6f58 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_37701c6f58 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_38d0e291ba | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_38d0e291ba | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_38d0e291ba | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_38d0e291ba | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_3af78f1b25 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_3af78f1b25 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_3af78f1b25 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_3af78f1b25 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_3b8c0583af | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_3b8c0583af | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_3b8c0583af | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_3e48f5055e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_3e48f5055e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_3ed6af72fd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_3ed6af72fd | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_3ed6af72fd | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_3ed6af72fd | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_3fbff79ff2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_3fbff79ff2 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_3fbff79ff2 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_3fbff79ff2 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_3fcc11e0ad | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_3fcc11e0ad | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_3fcc11e0ad | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_41d0f55a08 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_41d0f55a08 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_41d0f55a08 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_41d0f55a08 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_425da68f7c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_425da68f7c | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_425da68f7c | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_425da68f7c | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4324952b8b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4324952b8b | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4324952b8b | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4324952b8b | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_43a303096e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_43a303096e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_43a303096e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_43a303096e | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4464b03065 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4464b03065 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4464b03065 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4464b03065 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_44e968bf63 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_44e968bf63 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_44e968bf63 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_44e968bf63 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_458fb7e537 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_458fb7e537 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_458fb7e537 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_458fb7e537 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_45918aee9f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_45918aee9f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_45918aee9f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_45918aee9f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_459390cddd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_459390cddd | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_459390cddd | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_459390cddd | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_45bffa0df4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_45bffa0df4 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_45bffa0df4 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_45bffa0df4 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_466e5f3f4e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_466e5f3f4e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_466e5f3f4e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_466e5f3f4e | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_4676978578 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4676978578 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4676978578 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4676978578 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_46fa9759e5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_46fa9759e5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_46fa9759e5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_46fa9759e5 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4761dcdc46 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4761dcdc46 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4761dcdc46 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4761dcdc46 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_47d2ae39e5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_47d2ae39e5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_47d2ae39e5 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_4a78ea78e8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4a78ea78e8 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4a78ea78e8 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4a78ea78e8 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_4b084b882b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4b084b882b | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4b084b882b | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4b084b882b | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4b17dc753d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4b17dc753d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4b17dc753d | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4b17dc753d | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_4c00aae857 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4c00aae857 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4c00aae857 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4c00aae857 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_4c8d2b289a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4c8d2b289a | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4c8d2b289a | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4c8d2b289a | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_4ce22014ed | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4ce22014ed | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4ce22014ed | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4ce22014ed | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4cea4c2f0b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4cea4c2f0b | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4cea4c2f0b | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4cea4c2f0b | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_4ddf214313 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4ddf214313 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4ddf214313 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4ddf214313 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4e88800759 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4e88800759 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4e88800759 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4e88800759 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4ea2712748 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4ea2712748 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4ea2712748 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_4ea2712748 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_4ef5c224d3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_4ef5c224d3 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_513ef81023 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_513ef81023 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_513ef81023 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_51a31298d2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_51a31298d2 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_51a31298d2 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_51a31298d2 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_529994522f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_529994522f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_529994522f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_529994522f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_53e807972f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_53e807972f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_53e807972f | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_56b40663c8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_56b40663c8 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_56b40663c8 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_56b40663c8 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_57b5d36407 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_57b5d36407 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_57b5d36407 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_585e7a87d6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_585e7a87d6 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_585e7a87d6 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_585e7a87d6 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_5873c95958 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5873c95958 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5873c95958 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_5873c95958 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_591872c11d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_591872c11d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_591872c11d | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_591872c11d | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_5a09b0d1b3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5a09b0d1b3 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5a09b0d1b3 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_5a09b0d1b3 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5a46d7993e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5a46d7993e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5a46d7993e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_5a46d7993e | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5b1f03cd51 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5b1f03cd51 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5c3dbe8481 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5c3dbe8481 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5c3dbe8481 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_5d17717dc1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5d17717dc1 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5d17717dc1 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_5d17717dc1 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5d2ea24b9d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5d2ea24b9d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5d2ea24b9d | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_5d2ea24b9d | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5f025cc516 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5f025cc516 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_5f025cc516 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5f51d1f48e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5f51d1f48e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5f51d1f48e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_5f51d1f48e | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5fc89a7b02 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_5fc89a7b02 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_5fc89a7b02 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6121943138 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6121943138 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6121943138 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6121943138 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_626b6f82bd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_626b6f82bd | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_626b6f82bd | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_626b6f82bd | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6367b02595 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6367b02595 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6367b02595 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6367b02595 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_664592bae6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_664592bae6 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_664592bae6 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_6696faf9a6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6696faf9a6 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6696faf9a6 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6a9ef38f81 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6a9ef38f81 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6a9ef38f81 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6a9ef38f81 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6b1e561949 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6b1e561949 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6b1e561949 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6b1e561949 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_6b39088709 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6b39088709 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6b39088709 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6b39088709 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_6cad5aa952 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6cad5aa952 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6cad5aa952 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6cad5aa952 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6e15121479 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6e15121479 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6e15121479 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6e15121479 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6ee85769e5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6ee85769e5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6ee85769e5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6ee85769e5 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_6f6de09c81 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_6f6de09c81 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_6f6de09c81 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_6f6de09c81 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_700f49ccfe | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_700f49ccfe | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_700f49ccfe | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_700f49ccfe | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_737ba46cfa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_737ba46cfa | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_74a397a3ef | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_74a397a3ef | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_74a397a3ef | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_77fd1758fa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_77fd1758fa | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_77fd1758fa | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_77fd1758fa | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_781b93b400 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_781b93b400 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_781b93b400 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_781b93b400 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_79aeb12b71 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_79aeb12b71 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_79aeb12b71 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_79efe8ed74 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_79efe8ed74 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_79efe8ed74 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_79efe8ed74 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_7c57f5d78b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_7c57f5d78b | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_7c57f5d78b | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_7c57f5d78b | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_7c806a1ba4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_7c806a1ba4 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_7c806a1ba4 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_7d09389730 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_7d09389730 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_7d09389730 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_7d09389730 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8385ccdb99 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_8385ccdb99 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8385ccdb99 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_83cedb86a5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_83cedb86a5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_83cedb86a5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_83cedb86a5 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_84d44966e0 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_84d44966e0 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_84d44966e0 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_84d44966e0 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_863506a1da | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_863506a1da | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_863506a1da | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_863506a1da | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_86c96197e0 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_86c96197e0 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_892a73109d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_892a73109d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_892a73109d | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_892a73109d | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_8932e28953 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_8932e28953 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8932e28953 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_8932e28953 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8a0b1c0a4d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_8a0b1c0a4d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8a0b1c0a4d | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_8a0b1c0a4d | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8b533f5506 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_8b533f5506 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8b533f5506 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_8b533f5506 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_8cac87573a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_8cac87573a | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8cac87573a | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_8cac87573a | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_8daef6479e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_8daef6479e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_8daef6479e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_8daef6479e | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_901c649e7c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_901c649e7c | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_901c649e7c | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_901c649e7c | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_92b1c6b189 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_92b1c6b189 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_92b1c6b189 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_92b1c6b189 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9318736359 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_9318736359 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9318736359 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_9318736359 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_935f7de73e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_935f7de73e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_935f7de73e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_935f7de73e | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_94102ffa3f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_94102ffa3f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_94102ffa3f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_94102ffa3f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_959a12a7e6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_959a12a7e6 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_959a12a7e6 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_959a12a7e6 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9771326b87 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_9771326b87 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9771326b87 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_9771326b87 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_98cce0bbc0 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_98cce0bbc0 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_98cce0bbc0 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_9aa6bdfd43 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_9aa6bdfd43 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9aa6bdfd43 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_9aa6bdfd43 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_9b56dcb3aa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_9b56dcb3aa | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9b56dcb3aa | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_9b56dcb3aa | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9b6588a0f2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_9b6588a0f2 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9b6588a0f2 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_9b6588a0f2 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_9cf02e9988 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_9cf02e9988 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_9cf02e9988 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_9cf02e9988 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a0c6ea5a1c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_a0c6ea5a1c | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a0c6ea5a1c | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_a0c6ea5a1c | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a0e12272da | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_a0e12272da | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a0e12272da | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_a0e12272da | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_a4b22976a5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_a4b22976a5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a4b22976a5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_a4b22976a5 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_a55e33ac3f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_a55e33ac3f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a55e33ac3f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a6372a23cd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_a6372a23cd | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a6372a23cd | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_a6372a23cd | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a90e32b682 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_a90e32b682 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a90e32b682 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_a90e32b682 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a98b395465 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_a98b395465 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_a98b395465 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_ab0556ba98 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ab0556ba98 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ab1f75cc84 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ab1f75cc84 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ab1f75cc84 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_ab1f75cc84 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ac2101b41d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ac2101b41d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ad5c489987 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ad5c489987 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ad5c489987 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_ad5c489987 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_af28e2237f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_af28e2237f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_af28e2237f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_af28e2237f | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_afa423504b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_afa423504b | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_afa423504b | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_afa423504b | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b07454fb34 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b07454fb34 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b07454fb34 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b07454fb34 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b0fe1b9beb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b0fe1b9beb | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b0fe1b9beb | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b0fe1b9beb | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_b129d7e483 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b129d7e483 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b129d7e483 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b129d7e483 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b189dc204b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b189dc204b | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b48b1644be | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b48b1644be | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b48b1644be | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b534e184fb | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b534e184fb | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b534e184fb | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b534e184fb | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b553adaaf1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b553adaaf1 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b553adaaf1 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b553adaaf1 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_b57252c24f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b57252c24f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b57252c24f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b57252c24f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b5dd721d1d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b5dd721d1d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b5dd721d1d | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_b6924288e1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b6924288e1 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b6924288e1 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b6924288e1 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b6bd4a6431 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b6bd4a6431 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b6bd4a6431 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b6bd4a6431 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_b7f61baa04 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b7f61baa04 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b7f61baa04 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b7f61baa04 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b7fe111805 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b7fe111805 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b7fe111805 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b8e1c07198 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b8e1c07198 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b93f66dc76 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_b93f66dc76 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_b93f66dc76 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_b93f66dc76 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_baa058fe2f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_baa058fe2f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_baa058fe2f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_baa058fe2f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_bb509a8e63 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_bb509a8e63 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_bb509a8e63 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_bb509a8e63 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_c058bbe96f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_c058bbe96f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c058bbe96f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_c058bbe96f | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_c1ca5c27b2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_c1ca5c27b2 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c1ca5c27b2 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_c1ca5c27b2 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c484cc8d67 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_c484cc8d67 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c484cc8d67 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_c484cc8d67 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c62087d831 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_c62087d831 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c62087d831 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_c62087d831 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c6cdf7890d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_c6cdf7890d | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c6cdf7890d | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c861cdd087 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_c861cdd087 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c861cdd087 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_c861cdd087 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c8f4696fc3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_c8f4696fc3 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_c8f4696fc3 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_c8f4696fc3 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_cb81367576 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_cb81367576 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_cb81367576 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_cbd8c483de | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_cbd8c483de | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_cbd8c483de | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_cbd8c483de | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_cdb7922c41 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_cdb7922c41 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_cdb7922c41 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_cdb7922c41 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_cf929c95c6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_cf929c95c6 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_cf929c95c6 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_cf929c95c6 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_cfab21eaa7 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_cfab21eaa7 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_cfab21eaa7 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_d1c1a73279 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_d1c1a73279 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d3d8ea375f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_d3d8ea375f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d3d8ea375f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_d3d8ea375f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d6624ad9a3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_d6624ad9a3 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d707e53f81 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_d707e53f81 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d707e53f81 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_d707e53f81 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d78c94c944 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_d78c94c944 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d78c94c944 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_d78c94c944 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d7c9b61008 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_d7c9b61008 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d7c9b61008 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_d7c9b61008 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d89917f99f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_d89917f99f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_d89917f99f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_d89917f99f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_dbcb24773a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_dbcb24773a | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_dbcb24773a | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_dbcb24773a | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_dff8bcb2ef | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_dff8bcb2ef | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_dff8bcb2ef | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_dff8bcb2ef | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e115fef24f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e115fef24f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e115fef24f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_e115fef24f | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e1f13c7677 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e1f13c7677 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e27140c43a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e27140c43a | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e27140c43a | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_e27140c43a | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e2bbdb1f76 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e2bbdb1f76 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e2bbdb1f76 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_e2bbdb1f76 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_e2c5b0de8f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e2c5b0de8f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e2c5b0de8f | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_e2c5b0de8f | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_e5d97fb7a5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e5d97fb7a5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e5d97fb7a5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_e5d97fb7a5 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e6f9d0d23a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e6f9d0d23a | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e6f9d0d23a | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_e76dc03cce | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e76dc03cce | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e76dc03cce | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_e76dc03cce | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e7c2321edc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e7c2321edc | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e7c2321edc | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_e7c2321edc | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e936e762a2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e936e762a2 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e936e762a2 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_e936e762a2 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_e9815bdd27 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_e9815bdd27 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_e9815bdd27 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ec16a86cbc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ec16a86cbc | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ec16a86cbc | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_ec16a86cbc | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_ec37d13d5e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ec37d13d5e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ec37d13d5e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_ec37d13d5e | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_eca2ee5c80 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_eca2ee5c80 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_eca2ee5c80 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_eca2ee5c80 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ecaff44d15 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ecaff44d15 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ecaff44d15 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_ecaff44d15 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ed37899a61 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ed37899a61 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_ed37899a61 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_ed4e1383cd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_ed4e1383cd | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_edd2f9fbc5 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_edd2f9fbc5 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_edd2f9fbc5 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_edd2f9fbc5 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_eeb4095198 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_eeb4095198 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_eeb4095198 | candidate | research_interest_candidate | 1 | 0.5 |
| penn_trainee_profile_mstp_student_directory_f3a91accde | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_f3a91accde | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_f3a91accde | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_f3a91accde | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_f562d0db32 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_f562d0db32 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_f562d0db32 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_f562d0db32 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_f7881fb856 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_f7881fb856 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_f7881fb856 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_f7881fb856 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_f903773e50 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_f903773e50 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_f903773e50 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_f903773e50 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_f93a8b97c4 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_f93a8b97c4 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_f93a8b97c4 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_f93a8b97c4 | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_fab9643dcc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_fab9643dcc | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_fab9643dcc | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_fab9643dcc | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_faea3a0bb0 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_faea3a0bb0 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_faea3a0bb0 | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_faea3a0bb0 | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_fc9ca17c9e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_fc9ca17c9e | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_fc9ca17c9e | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_fc9ca17c9e | candidate | research_interest_candidate | 1 | 0.62 |
| penn_trainee_profile_mstp_student_directory_fda66d04aa | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_fda66d04aa | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_fda66d04aa | candidate | personal_profile_candidate | 1 | 0.55 |
| penn_trainee_profile_mstp_student_directory_fda66d04aa | candidate | research_interest_candidate | 2 | 0.56 |
| penn_trainee_profile_mstp_student_directory_fdaaa631b2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_fdaaa631b2 | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_mstp_student_directory_fe828c060f | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_mstp_student_directory_fe828c060f | candidate | education_history_candidate | 1 | 0.56 |
| penn_trainee_profile_providers_julie_cooper_e600f7441b | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_providers_julie_cooper_e600f7441b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_providers_julie_cooper_e600f7441b | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_providers_profile_lauren_hogshire_a5d9163adc | accepted | official_profile_url | 1 | 0.9 |
| penn_trainee_profile_providers_profile_lauren_hogshire_a5d9163adc | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_providers_profile_lauren_hogshire_a5d9163adc | candidate | prior_training_history_candidate | 1 | 0.78 |
| penn_trainee_profile_residents_2026_alec_gibson_md_phd_4f43cffd55 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_alec_gibson_md_phd_4f43cffd55 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_alex_chen_md_6389465397 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_alex_chen_md_6389465397 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_anthony_j_cordisco_md_ma_f7416fd25d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_anthony_j_cordisco_md_ma_f7416fd25d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_brendan_zotter_md_phd_65fcfdf093 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_brendan_zotter_md_phd_65fcfdf093 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_brendan_zotter_md_phd_copy_7595b4b87b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_brendan_zotter_md_phd_copy_7595b4b87b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_eli_cornblath_md_phd_8979ab0273 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_eli_cornblath_md_phd_8979ab0273 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_jonathan_perkins_md_2f2530d834 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_jonathan_perkins_md_2f2530d834 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_noelle_ohanesian_md_6f08372005 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_noelle_ohanesian_md_6f08372005 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_noor_shaik_md_phd_fd5ffa0d68 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_noor_shaik_md_phd_fd5ffa0d68 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_robert_eisinger_md_phd_b5985cb09d | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_robert_eisinger_md_phd_b5985cb09d | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_sabine_schneider_md_phd_d6b335a370 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_sabine_schneider_md_phd_d6b335a370 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_theandra_madu_md_mph_992129acfe | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_theandra_madu_md_mph_992129acfe | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_vivian_chioma_md_phd_90251c3e6c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_vivian_chioma_md_phd_90251c3e6c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2026_yombe_fonkeu_m_d_m_sc_32384f43e2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2026_yombe_fonkeu_m_d_m_sc_32384f43e2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_aaron_m_williams_md_phd_d6ac6abd5c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_aaron_m_williams_md_phd_d6ac6abd5c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_anne_t_taylor_md_fa1fb3515a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_anne_t_taylor_md_fa1fb3515a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_asma_akbar_ladak_mbbs_mph_07517b3605 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_asma_akbar_ladak_mbbs_mph_07517b3605 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_elsa_salim_karam_md_80ec82f77a | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_elsa_salim_karam_md_80ec82f77a | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_janine_lemos_melo_lobo_jofili_lopes_md_4b38d5b800 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_janine_lemos_melo_lobo_jofili_lopes_md_4b38d5b800 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_john_t_cook_md_63b5513876 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_john_t_cook_md_63b5513876 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_jonathan_vivian_dickens_md_phd_4ec0506100 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_jonathan_vivian_dickens_md_phd_4ec0506100 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_joseph_r_geraghty_md_phd_43df735368 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_joseph_r_geraghty_md_phd_43df735368 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_naomi_mayman_md_59f9fd9ce8 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_naomi_mayman_md_59f9fd9ce8 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_nicholas_j_fioravante_md_bdf0648b70 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_nicholas_j_fioravante_md_bdf0648b70 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_ozichi_c_osuoha_md_5268f6f6be | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_ozichi_c_osuoha_md_5268f6f6be | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_rebecca_e_row_md_ceb7d282db | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_rebecca_e_row_md_ceb7d282db | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_tanya_f_panwala_md_7f466a4905 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_tanya_f_panwala_md_7f466a4905 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2027_tochi_p_eboh_md_f36308a270 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2027_tochi_p_eboh_md_f36308a270 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_abigail_knowles_md_92fad3c6b2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_abigail_knowles_md_92fad3c6b2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_danya_nees_d_o_c93bc0a262 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_danya_nees_d_o_c93bc0a262 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_emily_marshall_md_be5fd0280b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_emily_marshall_md_be5fd0280b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_esteban_enrique_paredes_stanley_md_e736432193 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_esteban_enrique_paredes_stanley_md_e736432193 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_genna_r_ianni_md_phd_b80c927080 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_genna_r_ianni_md_phd_b80c927080 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_kyle_g_wicker_md_64ae28f89e | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_kyle_g_wicker_md_64ae28f89e | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_lauren_herzog_md_dd0fc29579 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_lauren_herzog_md_dd0fc29579 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_maria_del_mar_melendez_md_faebe84698 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_maria_del_mar_melendez_md_faebe84698 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_maria_m_priyma_crane_md_ms_265f5a7e69 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_maria_m_priyma_crane_md_ms_265f5a7e69 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_matthew_g_boden_md_92edfe89f3 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_matthew_g_boden_md_92edfe89f3 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_maya_ramy_md_mph_ms_e66e4947fc | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_maya_ramy_md_mph_ms_e66e4947fc | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_shriya_suresh_md_504ff35040 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_shriya_suresh_md_504ff35040 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_william_h_roberts_md_bc54c01e78 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_william_h_roberts_md_bc54c01e78 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2028_zoya_gurm_md_3988ad78b2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2028_zoya_gurm_md_3988ad78b2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_adary_zhang_md_056b6c4bf6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_adary_zhang_md_056b6c4bf6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_akshayaa_chittibabu_md_4f572952c9 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_akshayaa_chittibabu_md_4f572952c9 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_alexandria_tartt_md_87215fed24 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_alexandria_tartt_md_87215fed24 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_ashna_aggarwal_md_82f846a4bd | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_ashna_aggarwal_md_82f846a4bd | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_irena_balzekas_md_phd_f91f444cc6 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_irena_balzekas_md_phd_f91f444cc6 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_joanne_crandall_md_14754e82f1 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_joanne_crandall_md_14754e82f1 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_kinnari_karia_md_cdf7b0b748 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_kinnari_karia_md_cdf7b0b748 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_mohammad_zahwi_md_dc1f71027b | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_mohammad_zahwi_md_dc1f71027b | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_samuel_braza_md_bb7aea169c | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_samuel_braza_md_bb7aea169c | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_stephanie_jiang_md_1b069d78c2 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_stephanie_jiang_md_1b069d78c2 | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_sujal_manohar_md_1af41308ff | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_sujal_manohar_md_1af41308ff | candidate | education_history_candidate | 1 | 0.82 |
| penn_trainee_profile_residents_2029_vivian_chen_md_2751056618 | accepted | official_profile_url | 1 | 0.82 |
| penn_trainee_profile_residents_2029_vivian_chen_md_2751056618 | candidate | education_history_candidate | 1 | 0.82 |
| pubmed_eutilities | candidate | pubmed_article_candidate | 1405 | 0.652 |
| pubmed_eutilities | candidate | pubmed_author_query_candidate | 1336 | 0.204 |
| pubmed_eutilities | needs_review | pubmed_article_candidate | 857 | 0.841 |
| pulmonary_critical_care_current_fellows | accepted | medical_school | 34 | 0.868 |
| pulmonary_critical_care_current_fellows | accepted | residency_program | 34 | 0.832 |
| rheumatology_current_fellows | accepted | medical_school | 15 | 0.817 |
| rheumatology_current_fellows | accepted | residency_program | 15 | 0.83 |
| rheumatology_current_fellows | accepted | undergraduate_school | 15 | 0.777 |

## Source Utility Scorecard

Scorecard rows: 23.

| utility_label | claim_surface | input_records | output_records | score | quality_band | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- |
| Official roster current-membership extraction | current trainee identity, role, program, stage, and source-backed background | 82 | 1610 | 92.0 | high_utility | keep_as_truth_anchor_and_refresh_on_program_clock |
| Official HUP program denominator coverage | institution program universe, coverage gaps, and denominator drift | 91 | 65 | 86.0 | high_utility | resolve_gap_reason_and_alias_candidates_before_count_mutation |
| ACGME public program identifier candidates | program accreditation code, specialty, sponsoring program name, city, and accreditation-row context | 91 | 113 | 82.0 | strong_with_known_limits | use_accepted_program_identifiers_and_review_remaining_acgme_ambiguities |
| Penn medical-student public-source audit | public MSTP directory, protected MD directory, MD program context, and MD-PhD graduate-directory cross-checks | 16 | 16 | 78.0 | strong_with_known_limits | monitor_protected_md_directory_and_use_grad_directories_only_for_mstp_crosscheck |
| Official gap roster queue extraction | named resident/fellow extraction from prioritized uncovered-program pages | 36 | 576 | 76.0 | strong_with_known_limits | review_denominator_resolution_candidates_then_rerun_coverage |
| Penn-wide source discovery crawler | candidate roster, program context, alumni/outcome, and attending/faculty sources | 878 | 395 | 58.0 | useful_candidate_layer | treat_as_queue_then_probe_and_parse_only_source_backed_rosters |
| PubMed author-query discovery | name-bounded publication discovery seeds | 1336 | 1336 | 39.0 | discovery_or_review_only | use_only_to_seed_article_level_reconciliation |
| PubMed article-level reconciliation | PMID-level publication candidates with author, affiliation, topic, and recency anchors | 2262 | 2262 | 69.0 | useful_candidate_layer | prioritize_review_ready_packets_then_collect_secondary_identity_anchors |
| Enrichment acceptance assurance ledger | non-mutating acceptance tiers for publications, NPI anchors, and profile/trend evidence | 7265 | 7265 | 77.0 | strong_with_known_limits | promote_cross_source_publication_candidates_after_final_duplicate_author_position_check |
| Warehouse reproducibility provenance audit | artifact existence, row-count parity, content hashes, and repository-size pressure | 81 | 81 | 88.0 | high_utility | retain_sqlite_as_generated_untracked_artifact_and_refresh_manifest |
| OpenAlex author search | author-disambiguation, works, affiliations, ORCID, and citation features | 0 | 0 | 24.0 | blocked_or_low_current_utility | run_as_resumable_optional_lane_with_rate_limit_backoff |
| Official Penn trainee profile claims | roster-linked profile URLs, education, prior training, research/career interests, and personal-context snippets | 914 | 3416 | 81.0 | strong_with_known_limits | run_official_trainee_profile_discovery_then_reconcile_candidates |
| Prior training background discovery | medical-school and prior-residency background candidates for trainee enrichment gaps | 269 | 538 | 58.0 | useful_candidate_layer | run_prior_training_background_discovery_then_reconcile_candidates |
| Official Penn attending/profile claims | current attending endpoints, structured education/training, research interests, and personal profile snippets | 20 | 20 | 73.0 | strong_with_known_limits | seek_historical_identity_bridge_before_accepting_trend_links |
| Attending historical-link discovery | source candidates that may bridge current Penn attending endpoints to historical trainee records | 15 | 5 | 47.0 | discovery_or_review_only | run_polite_broad_search_and_prioritize_dated_historical_roster_or_cv_hits |
| Official Penn faculty biosketch training bridges | dated post-graduate training lines from official Penn Faculty Biosketch pages | 4 | 10 | 79.0 | strong_with_known_limits | review_dated_biosketch_bridges_before_accepting_recent_attending_trends |
| Attending trend reconciliation ledger | non-mutating policy ledger for current-attending endpoint, Penn-training, biosketch, and historical-link evidence | 70 | 70 | 82.0 | strong_with_known_limits | expand_attending_profile_and_historical_bridge_discovery_for_more_trend_facts |
| NPPES NPI Registry candidates | candidate NPI, taxonomy, and PA practice-location anchors for current resident/fellow identity review | 1257 | 1073 | 62.0 | useful_candidate_layer | use_npi_candidates_as_secondary_identity_anchors_only |
| Public contact candidate extraction | public email/contact channels with scope and verification status | 313 | 313 | 69.0 | useful_candidate_layer | verify_current_source_before_display_or_outreach_and_review_domain_anomalies |
| Organization normalization resolver | medical school, residency, undergraduate, graduate, institution, and program labels | 834 | 854 | 74.0 | strong_with_known_limits | append_alias_and_identifier_candidates_with_source_backed_evidence |
| Training state machine and longitudinal readiness | normalized stages, lifecycle rules, stale-after semantics, and annual diff expectations | 1682 | 1682 | 84.0 | strong_with_known_limits | use_state_machine_expectations_before_mutating_next_year_roster_diffs |
| Recursive enrichment work queue | person-level next-source tasks with state-machine urgency and evidence gates | 1535 | 6346 | 81.0 | strong_with_known_limits | run_high_priority_queue_tasks_and_feed_results_back_through_acceptance_ledgers |
| Enrichment execution readiness | mapping from queued enrichment tasks to collectors, commands, parser gaps, and review requirements | 6346 | 6346 | 78.0 | strong_with_known_limits | execute_queue_driven_research_profile_prior_training_and_roster_lanes_then_reconcile |

Learning: a source utility should be judged by the claim surface it supports, not by whether it exists. Official rosters are current-membership truth anchors; PubMed author-query rows are discovery only; PubMed article rows become review-ready only with non-name anchors; current attending profiles are endpoint and training-history candidates until a historical identity bridge exists; and broad search/crawler outputs should feed probe and parser queues before becoming person evidence.

## Search Utility Assurance

Utility rows: 4. Query rows: 2440. Search observations: 66. Search candidates: 7. Non-200 search rows: 62.

| utility_name | query_rows | search_observation_rows | search_candidate_rows | result_rows | search_execution_status | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- |
| Official HUP gap-source broad search | 42 | 0 | 0 | 0 | planned_not_executed | execute_optional_search_or_swap_to_a_more_reliable_provider_before_treating_absence_as_evidence |
| Official trainee profile search | 1824 | 30 | 0 | 0 | executed_partial_with_endpoint_errors | retain_candidates_but_treat_search_completeness_as_partial_and_retry_or_crosscheck |
| Prior-training background search | 538 | 0 | 0 | 0 | planned_not_executed | execute_optional_search_or_swap_to_a_more_reliable_provider_before_treating_absence_as_evidence |
| Attending historical-link search | 36 | 36 | 7 | 8 | executed_partial_with_endpoint_errors | retain_candidates_but_treat_search_completeness_as_partial_and_retry_or_crosscheck |

Learning: query manifests, endpoint observations, and discovered candidates are separate evidence classes. A skipped or blocked search lane cannot be interpreted as evidence that no public page exists; it only tells us which discovery utility still needs execution, retry, or replacement.

## Corpus Action Worklist

Worklist rows: 1279. Summed impact count: 11317. Critical rows: 16. High rows: 766.

| action_surface | action_scope | display_label | role | priority | impact_count | recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- |
| person_enrichment_execution | official_roster:current_roster_state_reconciliation | resident current_roster_state_reconciliation | resident | 1300 | 330 | refresh_roster_and_reconcile_state_machine |
| person_enrichment_execution | official_roster:current_roster_state_reconciliation | resident current_roster_state_reconciliation | resident | 1300 | 286 | refresh_roster_and_reconcile_state_machine |
| person_enrichment_execution | official_roster:current_roster_state_reconciliation | fellow current_roster_state_reconciliation | fellow | 1297 | 247 | refresh_roster_and_reconcile_state_machine |
| person_enrichment_execution | official_roster:current_roster_state_reconciliation | resident current_roster_state_reconciliation | resident | 1286 | 236 | refresh_roster_and_reconcile_state_machine |
| person_enrichment_execution | review_queue:evidence_reconciliation_review | resident evidence_reconciliation_review | resident | 1286 | 236 | review_reconciliation_packet |
| person_enrichment_execution | review_queue:evidence_reconciliation_review | resident evidence_reconciliation_review | resident | 1256 | 206 | review_reconciliation_packet |
| person_enrichment_execution | official_roster:current_roster_state_reconciliation | medical_student current_roster_state_reconciliation | medical_student | 1253 | 203 | refresh_roster_and_reconcile_state_machine |
| person_enrichment_execution | review_queue:evidence_reconciliation_review | resident evidence_reconciliation_review | resident | 1252 | 202 | review_reconciliation_packet |
| person_enrichment_execution | official_profile:official_profile_search | resident official_profile_search | resident | 1120 | 330 | collect_official_profile_evidence |
| person_enrichment_execution | official_profile:official_profile_search | fellow official_profile_search | fellow | 1120 | 257 | collect_official_profile_evidence |
| person_enrichment_execution | review_queue:evidence_reconciliation_review | fellow evidence_reconciliation_review | fellow | 1116 | 110 | review_reconciliation_packet |
| official_program_coverage | alias_review | Internal Medicine - Categorical | residency | 1093 | 173 | accept_or_split_alias_mapping |
| person_enrichment_execution | official_roster:current_roster_state_reconciliation | fellow current_roster_state_reconciliation | fellow | 1088 | 94 | refresh_roster_and_reconcile_state_machine |
| official_program_coverage | alias_review | Soft Tissue/Bone (Selective) | fellowship | 1009 | 69 | resolve_related_loaded_program_before_gap_closure |
| person_enrichment_execution | review_queue:evidence_reconciliation_review | fellow evidence_reconciliation_review | fellow | 1009 | 55 | review_reconciliation_packet |
| official_program_coverage | count_conflict_review | Adult Reconstructive Orthopedics | fellowship | 1003 | 3 | review_count_conflict_before_denominator_mutation |
| person_enrichment_execution | official_roster:current_roster_state_reconciliation | resident current_roster_state_reconciliation | resident | 998 | 49 | refresh_roster_and_reconcile_state_machine |
| person_evidence_review | mixed_identity_anchor_review | Katharine F. Michel, MD | resident | 976 | 10 | record_accept_reject_or_needs_more_evidence_decision |
| official_program_coverage | alias_review | Radiology - Diagnostic | residency | 974 | 54 | accept_or_split_alias_mapping |
| official_program_coverage | alias_review | Radiology - Interventional, Independent | residency | 971 | 19 | resolve_related_loaded_program_before_gap_closure |
| official_program_coverage | alias_review | Dermatology | residency | 963 | 17 | resolve_related_loaded_program_before_gap_closure |
| official_program_coverage | alias_review | Plastic Surgery | fellowship | 962 | 22 | resolve_related_loaded_program_before_gap_closure |
| person_evidence_review | mixed_identity_anchor_review | Pooja Humar, MD | resident | 961 | 7 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | publication_identity_review | Jared Alswang, MD | resident | 954 | 5 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | publication_identity_review | Lee H. Kilmer, MD | fellow | 954 | 5 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | mixed_identity_anchor_review | Amber Meservey, MD | fellow | 951 | 5 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | publication_identity_review | Dania Salih Bacha, MD | fellow | 949 | 4 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | mixed_identity_anchor_review | Matthew J. Rabinowitz, MD | resident | 949 | 4 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | publication_identity_review | Sarah Gorvetzian, MD | fellow | 949 | 4 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | mixed_identity_anchor_review | Krishna Patel MD | resident | 948 | 5 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | mixed_identity_anchor_review | Daniel Kim, MD | resident | 947 | 6 | record_accept_reject_or_needs_more_evidence_decision |
| official_program_coverage | alias_review | Internal Medicine - Pediatrics | residency | 945 | 25 | accept_or_split_alias_mapping |
| person_evidence_review | publication_identity_review | Amir Heravi, MD | fellow | 944 | 3 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | publication_identity_review | Elisabeth (Elise) Seyferth, MD | resident | 944 | 3 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | mixed_identity_anchor_review | Nikita O. Shulzhenko, MD | fellow | 944 | 3 | record_accept_reject_or_needs_more_evidence_decision |
| official_program_coverage | alias_review | Plastic Surgery - Integrated | residency | 942 | 22 | accept_or_split_alias_mapping |
| person_evidence_review | mixed_identity_anchor_review | Christopher M. Anthony, DO | fellow | 941 | 3 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | mixed_identity_anchor_review | Eric Schweppe, MD* | resident | 941 | 3 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | mixed_identity_anchor_review | Jetmir Vojnika, MD | fellow | 941 | 3 | record_accept_reject_or_needs_more_evidence_decision |
| person_evidence_review | mixed_identity_anchor_review | Joseph T. Tarr, MD, PhD | fellow | 941 | 3 | record_accept_reject_or_needs_more_evidence_decision |

Learning: unresolved evidence should be ranked as operator work, not inferred away. Program gaps, search execution, person evidence packets, contact verification, temporal-state refreshes, enrichment collectors, and attending-trend bridges all have different acceptance gates, so the worklist keeps their required next evidence explicit.

## Evidence Reconciliation Queue

| record_type | status | claim_type | count | avg_priority | avg_confidence |
| --- | --- | --- | --- | --- | --- |
| career_event | needs_review | penn_training_history_candidate | 5 | 118.0 | 0.756 |
| evidence_claim | needs_review | pubmed_article_candidate | 857 | 106.3 | 0.841 |
| npi_candidate | needs_review | npi_candidate | 801 | 105.5 | 0.736 |
| evidence_claim | candidate | prior_training_history_candidate | 108 | 70.0 | 0.78 |
| npi_candidate | candidate | npi_candidate | 146 | 69.2 | 0.602 |
| evidence_claim | candidate | education_history_candidate | 1248 | 66.1 | 0.709 |
| evidence_claim | candidate | pubmed_article_candidate | 1405 | 51.8 | 0.652 |
| career_event | candidate | education_history_candidate | 6 | 47.3 | 0.62 |
| evidence_claim | candidate | research_interest_candidate | 335 | 45.6 | 0.571 |
| evidence_claim | candidate | career_interest_candidate | 15 | 45.0 | 0.58 |
| career_event | candidate | prior_training_history_candidate | 6 | 43.7 | 0.573 |
| career_event | candidate | research_interest_candidate | 1 | 40.0 | 0.55 |
| career_event | candidate | personal_profile_candidate | 2 | 39.0 | 0.45 |
| career_event | candidate | current_penn_attending_candidate | 49 | 35.0 | 0.55 |
| npi_candidate | low_signal_npi_candidate | npi_candidate | 126 | 30.9 | 0.47 |
| evidence_claim | candidate | personal_profile_candidate | 783 | 30.0 | 0.529 |
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

Decision rows: 7265. Review-ready rows: 1716. Person/name rollups: 1504.

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
| profile_background_candidate | 561 |
| profile_context_candidate | 15 |
| profile_interest_context_candidate | 350 |
| profile_personal_context_display_review | 783 |
| review_ready_high_anchor | 5 |
| review_ready_profile_background_field | 795 |
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

## Person Evidence Reviewer Decisions

Queue rows: 686. Audit rows: 686. Pending reviewer decisions: 686. Accepted candidate facts: 0.

Decision statuses:

| decision_status | count |
| --- | --- |
| pending_reviewer_decision | 686 |

Review kinds:

| review_kind | count |
| --- | --- |
| mixed_identity_anchor_review | 663 |
| publication_identity_review | 23 |

Top packet-level reviewer rows:

| display_name | role | packet_status | review_kind | decision_status | review_priority | best_decision | best_source_url |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Amir Heravi, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/33509400/ |
| Brittany Brookner, MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/38509339/ |
| Bruk Mekonen, MD, MS | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/40336497/ |
| Dania Salih Bacha, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/33954783/ |
| Elisabeth (Elise) Seyferth, MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/39658750/ |
| Fatimah Alkhunaizi, MD, MS | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/38584015/ |
| Ian McCurry, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/34927154/ |
| Ianto Xi, MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/38521564/ |
| Jared Alswang, MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/37619942/ |
| Javier Eli Sierra-Pagan MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/37036809/ |
| Joav Birjiniuk, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/28608325/ |
| Katie Lattanzio, MD | resident | review_ready_mixed_packet | mixed_identity_anchor_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/37453876/ |
| Lee H. Kilmer, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/38016264/ |
| M Elle Saine, MD | fellow | review_ready_mixed_packet | mixed_identity_anchor_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/41643739/ |
| Margaret Kruithoff, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/40553957/ |
| Marine-Ayan Ibrahim Aibo, MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/40782885/ |
| Matthew J. Rabinowitz, MD | resident | review_ready_mixed_packet | mixed_identity_anchor_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/36017622/ |
| Michael J. Morano, MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/37274012/ |
| Moses Flash, MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/36496090/ |
| Nikita O. Shulzhenko, MD | fellow | review_ready_mixed_packet | mixed_identity_anchor_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/31689721/ |
| Rochelle Prokupets, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/41117724/ |
| Rohan Savoor, MD | resident | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/36526074/ |
| S. Muhammad Mustafa Zaidi, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/41758093/ |
| Sahityasri Thapi, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/40306969/ |
| Sarah Gorvetzian, MD | fellow | review_ready_publication_packet | publication_identity_review | pending_reviewer_decision | 129 | review_ready_training_topic_anchor | https://pubmed.ncbi.nlm.nih.gov/37383249/ |

Learning: packet-level reviewer decisions are now a first-class ledger. The system can separate candidate evidence that is merely review-ready from evidence that a reviewer explicitly accepted, rejected, or deferred against a stable packet fingerprint.

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

Pre-review acceptance rows: 3. Pre-review accepted facts: 3. Reviewer-accepted trend facts: 3. Pending reviewer decisions: 0.

| display_name | training_end_year | acceptance_status | accepted_trend_fact | acceptance_blocker | recommended_next_action |
| --- | --- | --- | --- | --- | --- |
| Timothy Buckey, MD, MBE | 2024 | accepted_after_explicit_reviewer_decision | 1 | none | retain_accepted_trend_fact_and_monitor_future_refresh |
| Patrick Kevin Gleeson, MD, MSCE | 2020 | accepted_after_explicit_reviewer_decision | 1 | none | retain_accepted_trend_fact_and_monitor_future_refresh |
| Priya Patel, MD | 2019 | accepted_after_explicit_reviewer_decision | 1 | none | retain_accepted_trend_fact_and_monitor_future_refresh |

Reviewer decision queue:

Queue rows: 3. Manual decision rows: 3. Accepted trend facts: 3. Pending reviewer decisions: 0.

| decision_status | count |
| --- | --- |
| accepted_reviewer_decision | 3 |

| display_name | reviewer_decision | decision_status | accepted_trend_fact | decision_blocker | recommended_next_action |
| --- | --- | --- | --- | --- | --- |
| Timothy Buckey, MD, MBE | accept_trend_fact | accepted_reviewer_decision | 1 | none | materialize_accepted_trend_fact |
| Patrick Kevin Gleeson, MD, MSCE | accept_trend_fact | accepted_reviewer_decision | 1 | none | materialize_accepted_trend_fact |
| Priya Patel, MD | accept_trend_fact | accepted_reviewer_decision | 1 | none | materialize_accepted_trend_fact |

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

People audited: 1535. Program/role groups audited: 96. Average coverage score: 60.27.

Coverage bands:

| coverage_band | count |
| --- | --- |
| broad_enrichment_surface | 203 |
| moderate_enrichment_surface | 1097 |
| thin_enrichment_surface | 235 |

Recommended next actions:

| recommended_next_action | count |
| --- | --- |
| collect_article_level_research_candidates | 52 |
| monitor_refresh_and_diff | 203 |
| official_profile_search | 587 |
| organization_alias_review | 383 |
| public_contact_search | 26 |
| reconcile_high_priority_evidence | 243 |
| review_training_state_machine | 22 |
| source_medical_school_background | 15 |
| source_residency_background | 4 |

Lowest-scoring program/role surfaces:

| program_name | role | person_count | avg_coverage_score | profile_coverage_rate | medical_school_coverage_rate | article_candidate_coverage_rate | npi_candidate_coverage_rate | npi_needs_review_coverage_rate | top_recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Clinical Microbiology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| GI/Hepatic Pathology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Soft Tissue/Bone Pathology Fellowship | fellow | 1 | 20.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Psychiatry Residency | resident | 52 | 20.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
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

Learning: coverage needs to be audited separately from evidence acceptance. This pass shows where the recursive loop should work next: official profile search, organization alias review, article-level research collection, and high-priority reconciliation.

## Utility Observations

| utility_key | sample_size | candidate_claims | accepted_claims | rejected_claims | ambiguous_claims | metrics_json |
| --- | --- | --- | --- | --- | --- | --- |
| official_trainee_profile | 927 | 2489 | 927 | 0 | 0 | {"by_claim_type": {"career_interest_candidate": 15, "education_history_candidate": 1248, "official_profile_url": 927, "personal_profile_candidate": 783, "prior_training_history_candidate": 108, "research_interest_candidate": 335}, "by_status": {"accepted": 927, "candidate": 2489}, "claims": 3416, "display_safety_counts": {"personal_context_not_default_display": 749, "safe_for_default_display": 2633, "sensitive_personal_context_restricted": 34}, "orphan_claims_skipped": 0, "people_with_claims": 927, "raw_claims": 3416, "source_rows": 927, "summary": {"by_claim_type": {"career_interest_candidate": 15, "education_history_candidate": 1248, "official_profile_url": 927, "personal_profile_candidate": 783, "prior_training_history_candidate": 108, "research_interest_candidate": 335}, "by_role": {"fellow": 517, "medical_student": 946, "resident": 1953}, "by_status": {"accepted": 927, "candidate": 2489}, "claims": 3416, "csv": "artifacts/data/penn_trainee_profile_claims.csv", "display_safety_counts": {"personal_context_not_default_display": 749, "safe_for_default_display": 2633, "sensitive_personal_context_restricted": 34}, "field_counts": {"academic_interests": 197, "alternate_career_interest": 110, "career_interests": 15, "graduate_group": 220, "graduate_school": 22, "hobbies": 166, "hobbies_interests": 187, "home_state": 35, "hometown": 121, "kids": 34, "medical_school": 689, "philadelphia_interest": 120, "residency_program": 111, "thesis_advisor": 138, "undergraduate": 319, "why_penn": 10}, "generated_at": "2026-06-02T15:25:03.009955+00:00", "inputs": {"artifacts/data/penn_affiliated_people.json": 306, "artifacts/data/penn_gme_gap_roster_people.json": 576, "artifacts/data/penn_mstp_students.json": 225, "artifacts/data/penn_training_people_unique.json": 453}, "json": "artifacts/data/penn_trainee_profile_claims.json", "people_with_claims": 927, "policy": "Profile URL links from official rosters are accepted as profile-location facts. Structured profile fields are candidate enrichment with display-safety metadata and do not mutate accepted roster/background truth.", "profile_fetch_status_counts": {"": 733, "200": 194}, "profiles_with_text": 914, "profiles_with_url": 927, "skipped": {"missing_profile_text_excerpt": 13, "no_known_profile_fields": 14}, "sources": 927, "sources_json": "artifacts/data/penn_trainee_profile_sources.json"}} |
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

Roster-linked trainee profiles with text: 914. Claims extracted: 3416. People with profile claims: 927.

Profile claim counts:

| status | claim_type | count | avg_confidence |
| --- | --- | --- | --- |
| accepted | official_profile_url | 927 | 0.837 |
| candidate | career_interest_candidate | 15 | 0.58 |
| candidate | education_history_candidate | 1248 | 0.709 |
| candidate | personal_profile_candidate | 783 | 0.529 |
| candidate | prior_training_history_candidate | 108 | 0.78 |
| candidate | research_interest_candidate | 335 | 0.571 |

Display-safety policy counts:

| display_safety_status | count |
| --- | --- |
| safe_for_default_display | 2633 |
| personal_context_not_default_display | 749 |
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
