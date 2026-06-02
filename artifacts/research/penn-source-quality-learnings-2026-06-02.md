# Penn Source Quality Learnings

Generated: 2026-06-02T06:53:06.654660+00:00

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
| covered_current_roster | 59 |
| discovered_no_current_roster | 12 |
| not_discovered | 20 |

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
| fellowship | Obstetrics and Gynecology | Gynecologic Oncology | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Maternal Fetal Medicine | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Reproductive Endocrinology and Infertility | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Urogynecology and Reconstructive Pelvic Surgery | not_discovered | none |
| residency | Oral and Maxillofacial Surgery | Oral and Maxillofacial Surgery | not_discovered | none |
| residency | Oral and Maxillofacial Surgery | Oral Medicine | not_discovered | none |
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

Gap programs probed: 32. Source pages probed: 28. Candidate URLs queued: 82.

| candidate_status | count |
| --- | --- |
| low_value_candidate | 5 |
| program_context_candidate | 53 |
| roster_source_candidate | 24 |

Top roster-source candidates:

| program_name | department | candidate_status | priority | candidate_title | candidate_url |
| --- | --- | --- | --- | --- | --- |
| Radiology - Interventional, Independent | Radiology | roster_source_candidate | 135 | Current Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-radiology/education-and-training/residency-programs/current-residents |
| Plastic Surgery | Surgery | roster_source_candidate | 135 | Meet Our Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training/residencies/plastic-surgery/residents |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Fellows | https://pathology.med.upenn.edu/department/people/fellows |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Residents | https://pathology.med.upenn.edu/department/people/residents |
| Neurology | Neurology | roster_source_candidate | 125 | Class of 2026 | https://neuroresidency.uphs.upenn.edu/residents/2026 |
| Neurology | Neurology | roster_source_candidate | 125 | Class of 2027 | https://neuroresidency.uphs.upenn.edu/residents/2027 |
| Neurology | Neurology | roster_source_candidate | 125 | Class of 2028 | https://neuroresidency.uphs.upenn.edu/residents/2028 |
| Neurology | Neurology | roster_source_candidate | 125 | Class of 2029 | https://neuroresidency.uphs.upenn.edu/residents/2029 |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 125 | Fellows | https://pathology.med.upenn.edu/education/fellowships/fellows |
| Radiology - Interventional, Independent | Radiology | roster_source_candidate | 125 | Meet our Integrated IR residents | https://www3.pennmedicine.org/departments-and-centers/department-of-radiology/education-and-training/residency-programs/current-residents/ir-integrated-residents |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 120 | Student Fellows | https://pathology.med.upenn.edu/department/people/students-fellows |
| Dermatology | Dermatology | roster_source_candidate | 115 | Penn Medicine Dermatology site | https://dermatology.upenn.edu/residents/combined-medicine-and-dermatology-track |
| Dermatology | Dermatology | roster_source_candidate | 115 | Chief Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/leadership/chief-residents |
| Dermatology | Dermatology | roster_source_candidate | 115 | Medicine-Dermatology Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/combined-internal-medicine-dermatology-program/medicine-dermatology-residents |
| Transplant Hepatology | Internal Medicine | roster_source_candidate | 115 | Advanced Gastroenterology and Hepatology Fellows | https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/gastroenterology/education-and-training/fellowship-programs/advanced-gastroenterology-fellows |
| Soft Tissue/Bone (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 115 | Current | https://pathology.med.upenn.edu/education/residency/residents/current |
| Neurocritical Care | Neurology | roster_source_candidate | 90 | Neurocritical Care \| Penn Neurology Fellowship Programs | https://neurofellowships.uphs.upenn.edu/p/neurocritical-care_17.html |
| Neurology | Neurology | roster_source_candidate | 90 | Penn Neurology Residency Program | https://neuroresidency.uphs.upenn.edu/ |
| Gynecologic Oncology | Obstetrics and Gynecology | roster_source_candidate | 90 | Gynecologic Oncology - Penn Medicine | https://www3.pennmedicine.org/departments-and-centers/obstetrics-and-gynecology/education-and-training/fellowship-programs/gynecologic-oncology |
| Maternal Fetal Medicine | Obstetrics and Gynecology | roster_source_candidate | 90 | Maternal Fetal Medicine - Penn Medicine | https://www3.pennmedicine.org/departments-and-centers/obstetrics-and-gynecology/education-and-training/fellowship-programs/maternal-fetal-medicine |
| Reproductive Endocrinology and Infertility | Obstetrics and Gynecology | roster_source_candidate | 90 | Reproductive Endocrinology - Penn Medicine | https://www3.pennmedicine.org/departments-and-centers/obstetrics-and-gynecology/education-and-training/fellowship-programs/reproductive-endocrinology |
| Urogynecology and Reconstructive Pelvic Surgery | Obstetrics and Gynecology | roster_source_candidate | 90 | Urogynecology - Penn Medicine | https://www3.pennmedicine.org/departments-and-centers/obstetrics-and-gynecology/education-and-training/fellowship-programs/urogynecology |
| Radiology - Interventional, Independent | Radiology | roster_source_candidate | 80 | Interventional Radiology Integrated and Independent Residency | https://www3.pennmedicine.org/departments-and-centers/department-of-radiology/education-and-training/residency-programs/irdr-interventional-radiology |
| Plastic Surgery | Surgery | roster_source_candidate | 80 | Plastic Surgery Integrated & Independent Residency - Penn Medicine | https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training/residencies/plastic-surgery |

Learning: coverage gaps need their own crawl state. Official program URLs, discovered context pages, and linked roster-like pages should be queued separately so the next scraper can attack high-priority roster candidates without conflating them with verified person records.

## HUP Gap Roster Extraction

Supported gap roster sources attempted: 26. Sources with records: 22. Person records extracted: 492.

Records by role:

| role | count |
| --- | --- |
| fellow | 58 |
| resident | 434 |

Extraction statuses:

| extraction_status | count |
| --- | --- |
| no_supported_person_structure | 4 |
| records_extracted | 22 |

Learning: queue-driven extraction should stay template-aware. Pages without supported person structure remain source candidates; this avoids converting program context, generic people directories, or ambiguous student-fellow pages into trainee records.

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
| Sleep Medicine Fellowship | fellow | 7 |
| Surgical Pathology Fellowship | fellow | 6 |
| Microvascular Reconstructive Surgery Fellowship | fellow | 5 |
| CHOP Otolaryngology Fellowship | fellow | 4 |
| Hematopathology Fellowship | fellow | 4 |
| Thoracic Surgery Fellowship - Cardiac Track | fellow | 4 |
| Vascular Surgery Fellowship | fellow | 4 |
| Adult Reconstructive Orthopedics Fellowship | fellow | 3 |
| Advanced Musculoskeletal Fellowship | fellow | 3 |
| Transplant Surgery Fellowship | fellow | 3 |
| Aortic Surgery Fellowship | fellow | 2 |
| Clinical Chemistry Fellowship | fellow | 2 |
| Clinical Microbiology Fellowship | fellow | 2 |
| Cytopathology Fellowship | fellow | 2 |
| Foot and Ankle Fellowship | fellow | 2 |
| GI/Hepatic Pathology Fellowship | fellow | 2 |
| Hand Surgery Fellowship | fellow | 2 |

Generic `Residents`/`Fellows` program labels remaining: 0.

Learning: program names often require URL-plus-section inference. Page titles alone are too weak because official pages can be titled `Residents` or `Fellows`, while one source page can contain multiple program sections.

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
| clinical_postgraduate | GME_RESIDENT_YEAR_UNKNOWN | current | 86 | 0.426 |
| clinical_postgraduate_research | GME_RESEARCH_OR_LAB_YEAR | current | 25 | 0.68 |
| fellowship | FELLOWSHIP_CURRENT_YEAR_UNKNOWN | current | 175 | 0.499 |
| fellowship | FELLOWSHIP_YEAR_1 | current | 66 | 0.82 |
| fellowship | FELLOWSHIP_YEAR_2 | current | 59 | 0.82 |
| fellowship | FELLOWSHIP_YEAR_3 | current | 36 | 0.82 |
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
| expected fellowship annual advancement around Jul 1; terminal year requires program-length context | 168 |
| current fellow but year not normalized; refresh on next roster and use program-specific duration if available | 131 |
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
| chief year is terminal/program-specific; refresh on next academic-year roster | 16 |
| current resident but exact year not visible on source; refresh on next roster | 13 |
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
| US_GME_FELLOWSHIP_2Y | expected_annual_advancement | annual_clock | 26 | 0.82 |
| US_GME_FELLOWSHIP_2Y | expected_completion | annual_clock | 24 | 0.82 |
| US_GME_FELLOWSHIP_2Y | source_refresh_required | source_refresh_required | 27 | 0.567 |
| US_GME_FELLOWSHIP_2Y | stage_outside_nominal_duration_review | review_required | 3 | 0.873 |
| US_GME_FELLOWSHIP_3Y | expected_annual_advancement | annual_clock | 72 | 0.82 |
| US_GME_FELLOWSHIP_3Y | expected_completion | annual_clock | 35 | 0.82 |
| US_GME_FELLOWSHIP_3Y | source_refresh_required | source_refresh_required | 10 | 0.52 |
| US_GME_FELLOWSHIP_3Y | stage_outside_nominal_duration_review | review_required | 7 | 0.82 |
| US_GME_FELLOWSHIP_DURATION_UNKNOWN | source_refresh_required | annual_clock | 4 | 0.86 |
| US_GME_FELLOWSHIP_DURATION_UNKNOWN | source_refresh_required | source_refresh_required | 54 | 0.471 |
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
| US_MD_PHD_MSTP_VARIABLE | source_refresh_required | source_refresh_required | 225 | 0.762 |

State-machine audit status:

| state_machine_status | count |
| --- | --- |
| annual_clock_active | 657 |
| current_observation | 61 |
| review_required | 21 |
| source_refresh_required | 609 |
| terminal_year_active | 250 |

Clock models:

| clock_model | count |
| --- | --- |
| annual_gme_july | 955 |
| refresh_from_source | 13 |
| review_required | 21 |
| source_refresh_required | 609 |

Auto-advance candidate rows: 657. Completion candidate rows: 250. Stale/review rows: 21.

Learning: roster strings should become normalized state observations with explicit clocks and program lifecycle semantics. PGY and fellowship-year states can be annual-clock states, but terminal-year, unknown-duration, research, chief, and source-ambiguous states need different refresh/exit behavior. Lifecycle codes are local `redmank` codes until external ACGME/ERAS/NRMP identifiers are source-backed. The audit layer makes that operational: a row is only stale, advanceable, or removable when its lifecycle rule says so.

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
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_2c6709998d | accepted | graduate_school | 6 | 0.817 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_2c6709998d | accepted | medical_school | 32 | 0.912 |
| penn_gme_gap_departments_and_centers_obstetrics_and_gynecology_education_and_traini_2c6709998d | accepted | undergraduate_school | 29 | 0.929 |
| penn_gme_gap_departments_and_centers_orthopaedic_surgery_education_and_training_res_bc144f028b | accepted | medical_school | 40 | 0.89 |
| penn_gme_gap_departments_and_centers_orthopaedic_surgery_education_and_training_res_bc144f028b | accepted | undergraduate_school | 40 | 0.845 |
| penn_gme_gap_departments_and_centers_physical_medicine_and_rehabilitation_education_7d5742c85a | accepted | medical_school | 22 | 0.841 |
| penn_gme_gap_departments_and_centers_podiatry_and_podiatric_surgery_education_and_t_ebe320ba1d | accepted | graduate_school | 2 | 0.75 |
| penn_gme_gap_departments_and_centers_podiatry_and_podiatric_surgery_education_and_t_ebe320ba1d | accepted | medical_school | 16 | 0.887 |
| penn_gme_gap_departments_and_centers_podiatry_and_podiatric_surgery_education_and_t_ebe320ba1d | accepted | undergraduate_school | 16 | 0.825 |
| penn_gme_gap_education_residency_residents_current_5a6a4942f1 | accepted | medical_school | 38 | 0.876 |
| penn_gme_gap_residents_2026_a44d511002 | accepted | medical_school | 14 | 0.936 |
| penn_gme_gap_residents_2027_15a734ed51 | accepted | medical_school | 14 | 0.821 |
| penn_gme_gap_residents_2028_420d5a86f8 | accepted | medical_school | 14 | 0.879 |
| penn_gme_gap_residents_2029_3396e9a918 | accepted | medical_school | 12 | 0.917 |
| pubmed_eutilities | candidate | pubmed_article_candidate | 1008 | 0.652 |
| pubmed_eutilities | candidate | pubmed_author_query_candidate | 1103 | 0.205 |
| pubmed_eutilities | needs_review | pubmed_article_candidate | 850 | 0.841 |
| pulmonary_critical_care_current_fellows | accepted | medical_school | 34 | 0.868 |
| pulmonary_critical_care_current_fellows | accepted | residency_program | 34 | 0.832 |
| rheumatology_current_fellows | accepted | medical_school | 15 | 0.817 |
| rheumatology_current_fellows | accepted | residency_program | 15 | 0.83 |
| rheumatology_current_fellows | accepted | undergraduate_school | 15 | 0.777 |

## Evidence Reconciliation Queue

| record_type | status | claim_type | count | avg_priority | avg_confidence |
| --- | --- | --- | --- | --- | --- |
| career_event | needs_review | penn_training_history_candidate | 5 | 118.0 | 0.756 |
| evidence_claim | needs_review | pubmed_article_candidate | 850 | 106.3 | 0.841 |
| evidence_claim | candidate | pubmed_article_candidate | 1008 | 51.9 | 0.652 |
| career_event | candidate | education_history_candidate | 6 | 47.3 | 0.62 |
| career_event | candidate | prior_training_history_candidate | 6 | 43.7 | 0.573 |
| career_event | candidate | research_interest_candidate | 1 | 40.0 | 0.55 |
| career_event | candidate | personal_profile_candidate | 2 | 39.0 | 0.45 |
| career_event | candidate | current_penn_attending_candidate | 49 | 35.0 | 0.55 |
| career_event | candidate | penn_alumni_outcome_candidate | 36 | 23.6 | 0.411 |
| evidence_claim | candidate | pubmed_author_query_candidate | 1103 | 13.7 | 0.205 |

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

## Enrichment Coverage Audit

People audited: 1451. Program/role groups audited: 90. Average coverage score: 59.17.

Coverage bands:

| coverage_band | count |
| --- | --- |
| broad_enrichment_surface | 95 |
| moderate_enrichment_surface | 1155 |
| thin_enrichment_surface | 201 |

Recommended next actions:

| recommended_next_action | count |
| --- | --- |
| collect_article_level_research_candidates | 255 |
| monitor_refresh_and_diff | 205 |
| official_profile_search | 484 |
| organization_alias_review | 386 |
| public_contact_search | 33 |
| reconcile_high_priority_evidence | 49 |
| review_training_state_machine | 20 |
| source_medical_school_background | 15 |
| source_residency_background | 4 |

Lowest-scoring program/role surfaces:

| program_name | role | person_count | avg_coverage_score | profile_coverage_rate | medical_school_coverage_rate | article_candidate_coverage_rate | top_recommended_next_action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Breast Pathology Fellowship | fellow | 1 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Clinical Chemistry Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Clinical Microbiology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Cytopathology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| GI/Hepatic Pathology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Hematopathology Fellowship | fellow | 4 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Molecular Genetic Pathology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Neuropathology Fellowship | fellow | 2 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Soft Tissue/Bone Pathology Fellowship | fellow | 1 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Surgical Pathology Fellowship | fellow | 6 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Transfusion Medicine/Blood Bank Fellowship | fellow | 1 | 20.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Adult Reconstructive Orthopedics Fellowship | fellow | 3 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| CHOP Otolaryngology Fellowship | fellow | 4 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Facial Plastic and Reconstructive Surgery Fellowship | fellow | 1 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Foot and Ankle Fellowship | fellow | 2 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Head and Neck Surgical Oncology, Microvascular Reconstruction, and Robotic Surgery Fellowship | fellow | 2 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Neurotology Fellowship | fellow | 1 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Rhinology and Skull Base Surgery Fellowship | fellow | 2 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Shoulder and Elbow Fellowship | fellow | 1 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Sleep Medicine and Surgery Fellowship | fellow | 2 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Spine Fellowship | fellow | 1 | 25.0 | 0.0 | 0.0 | 0.0 | official_profile_search |
| Otorhinolaryngology Residency | resident | 31 | 25.65 | 0.0 | 0.0 | 0.065 | official_profile_search |
| Sleep Medicine Fellowship | fellow | 7 | 26.43 | 0.0 | 0.0 | 0.143 | official_profile_search |
| Radiation Oncology Residency | resident | 17 | 27.35 | 0.0 | 0.0 | 0.235 | official_profile_search |
| ABR Alternate Pathway to Certification | fellow | 1 | 30.0 | 0.0 | 0.0 | 0.0 | official_profile_search |

Learning: coverage needs to be audited separately from evidence acceptance. This pass shows where the recursive loop should work next: official profile search, organization alias review, article-level research collection, and high-priority reconciliation.

## Utility Observations

| utility_key | sample_size | candidate_claims | accepted_claims | rejected_claims | ambiguous_claims | metrics_json |
| --- | --- | --- | --- | --- | --- | --- |
| openalex_author_search | 0 | 0 | 0 | 0 | 0 | {"collector_resume_supported": true, "current_claims": 0, "rate_limit_observed": true} |
| pubmed_article_reconciliation | 297 | 1008 | 0 | 0 | 850 | {"artifact": "pubmed_article_candidate_claims.json", "claims": 1858, "mean_confidence": 0.7386, "orphan_claims_skipped": 0, "orphan_people_skipped": 0, "raw_claims": 1858, "summary": {"article_claims": 1858, "by_feature": {"article_author_name_match": 1858, "bounded_author_query": 1858, "penn_affiliation": 11, "prior_training_or_education_affiliation": 843, "program_topic_match": 215, "recent_publication": 1647}, "by_status": {"candidate": 1008, "needs_review": 850}, "generated_at": "2026-06-02T06:14:49.049485+00:00", "include_high_collision": false, "max_author_count": 20, "query_claims_considered": 305, "unique_pmids_fetched": 1879}} |
| pubmed_eutilities | 1103 | 2111 | 0 | 0 | 850 | {"claims": 2961, "mean_confidence": 0.5398, "orphan_claims_skipped": 8, "orphan_people_skipped": 8, "raw_claims": 2969} |

## OpenAlex Feature Distribution

| match_features_json | count | avg_confidence |
| --- | --- | --- |

Learning: OpenAlex remains a promising author-disambiguation utility, but the current full-corpus run hit sustained 429 throttling. Record that as source availability/operations evidence, not as rejected person identity evidence.

## PubMed Feature Distribution

| match_features_json | count | avg_confidence |
| --- | --- | --- |
| ["author_query", "high_collision_risk"] | 669 | 0.159 |
| ["author_query", "bounded_result_count"] | 305 | 0.35 |
| ["author_query", "no_results"] | 129 | 0.1 |

Learning: PubMed E-utilities is a strong article database, but author-query search is a weak identity resolver. It should be used after candidate author identity is constrained by OpenAlex/ORCID/profile context, or at article-level with affiliation/coauthor checks.

## PubMed Article-Level Reconciliation

Bounded query claims considered: 305. Unique PMIDs fetched: 1879. Article candidates: 1858.

Article candidate statuses:

| status | count |
| --- | --- |
| candidate | 1008 |
| needs_review | 850 |

Article candidate feature distribution:

| match_features_json | count | avg_confidence |
| --- | --- | --- |
| ["article_author_name_match", "bounded_author_query", "recent_publication"] | 719 | 0.65 |
| ["article_author_name_match", "bounded_author_query", "prior_training_or_education_affiliation", "recent_publication"] | 706 | 0.83 |
| ["article_author_name_match", "bounded_author_query"] | 187 | 0.62 |
| ["article_author_name_match", "bounded_author_query", "prior_training_or_education_affiliation", "program_topic_match", "recent_publication"] | 111 | 0.91 |
| ["article_author_name_match", "bounded_author_query", "program_topic_match", "recent_publication"] | 100 | 0.73 |
| ["article_author_name_match", "bounded_author_query", "prior_training_or_education_affiliation"] | 21 | 0.8 |
| ["article_author_name_match", "bounded_author_query", "penn_affiliation", "recent_publication"] | 6 | 0.87 |
| ["article_author_name_match", "bounded_author_query", "penn_affiliation", "prior_training_or_education_affiliation", "recent_publication"] | 4 | 0.95 |
| ["article_author_name_match", "bounded_author_query", "program_topic_match"] | 2 | 0.7 |
| ["article_author_name_match", "bounded_author_query", "prior_training_or_education_affiliation", "program_topic_match"] | 1 | 0.88 |
| ["article_author_name_match", "bounded_author_query", "penn_affiliation", "program_topic_match", "recent_publication"] | 1 | 0.95 |

Learning: article-level PubMed XML is materially better than author-query counts because it exposes the target author, affiliation strings, publication year, journal/title, and topic hints. It is still candidate evidence: many records have one strong non-name anchor, but acceptance should require at least two independent anchors or a human review step.

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

Learning: public contact channels belong in a separate evidence table because a person can have multiple public contacts from sources with different assurance levels. Raw HTML remains redacted; only structured, source-linked public contact candidates are stored.

## Reconciliation Rule Update

For the next pass, accept research enrichment only when at least two non-name anchors agree. Examples: official profile link plus ORCID; OpenAlex Penn affiliation plus specialty-topic match; PubMed affiliation plus coauthor cluster; NPI specialty/location plus official profile.

## Source References

- OpenAlex institutions documentation notes that all OpenAlex institutions have ROR IDs and that parsing author affiliations is nontrivial: https://docs.openalex.org/api-entities/institutions
- NCBI E-utilities are the public API for Entrez databases including PubMed: https://www.ncbi.nlm.nih.gov/home/develop/api/
- ORCID supports organization identifiers including ROR for affiliations: https://info.orcid.org/documentation/integration-guide/working-with-organization-identifiers/
- NPPES provides an official public read API for NPI Registry data: https://npiregistry.cms.hhs.gov/api-page
- ClinicalTrials.gov provides an official API and OpenAPI specification: https://clinicaltrials.gov/data-about-studies/learn-about-api
- WDOMS is a searchable directory of undergraduate medical education programs; listing confirms existence but not accreditation or endorsement unless stated: https://wfme.org/world-directory/
