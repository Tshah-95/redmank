# Penn Source Quality Learnings

Generated: 2026-06-02T05:38:09.216638+00:00

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
| covered_current_roster | 33 |
| discovered_no_current_roster | 27 |
| not_discovered | 31 |

Sample uncovered or partially covered official programs:

| program_type | department | program_name | coverage_status | match_method |
| --- | --- | --- | --- | --- |
| residency | Anesthesiology | Anesthesiology | discovered_no_current_roster | source_discovery |
| fellowship | Anesthesiology | Adult Cardiothoracic Anesthesiology | discovered_no_current_roster | source_discovery |
| fellowship | Anesthesiology | Critical Care Medicine | discovered_no_current_roster | source_discovery |
| fellowship | Anesthesiology | Pain Medicine | discovered_no_current_roster | source_discovery |
| residency | Dermatology | Dermatology | discovered_no_current_roster | source_discovery |
| fellowship | Dermatology | Dermatopathology | not_discovered | none |
| fellowship | Dermatology | Micrographic Surgery and Dermatologic Oncology | not_discovered | none |
| residency | Emergency Medicine | Emergency Medicine | discovered_no_current_roster | source_discovery |
| residency | Emergency Medicine | Occupational and Environmental Medicine (Preventative Medicine) | not_discovered | none |
| fellowship | Emergency Medicine | Undersea and Hyperbaric Medicine | discovered_no_current_roster | source_discovery |
| residency | Family Medicine | Family Medicine | not_discovered | none |
| fellowship | Family Medicine | Addiction Medicine | discovered_no_current_roster | source_discovery |
| fellowship | Family Medicine | Sports Medicine | not_discovered | none |
| fellowship | Internal Medicine | Sleep Medicine | discovered_no_current_roster | source_discovery |
| fellowship | Internal Medicine | Transplant Hepatology | discovered_no_current_roster | source_discovery |
| residency | Neurological Surgery | Neurological Surgery | not_discovered | none |
| residency | Neurology | Neurology | not_discovered | none |
| fellowship | Neurology | Clinical Neurophysiology | not_discovered | none |
| fellowship | Neurology | Epilepsy | not_discovered | none |
| fellowship | Neurology | Neurocritical Care | not_discovered | none |
| fellowship | Neurology | Neuromuscular Medicine | not_discovered | none |
| fellowship | Neurology | Vascular Neurology | not_discovered | none |
| residency | Obstetrics and Gynecology | Obstetrics and Gynecology | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Complex Family Planning | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Gynecologic Oncology | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Maternal Fetal Medicine | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Reproductive Endocrinology and Infertility | not_discovered | none |
| fellowship | Obstetrics and Gynecology | Urogynecology and Reconstructive Pelvic Surgery | not_discovered | none |
| residency | Oral and Maxillofacial Surgery | Oral and Maxillofacial Surgery | not_discovered | none |
| residency | Oral and Maxillofacial Surgery | Oral Medicine | not_discovered | none |
| residency | Orthopedic Surgery | Orthopedic Surgery | not_discovered | none |
| fellowship | Orthopedic Surgery | Adult Reconstructive Orthopedics | not_discovered | none |
| fellowship | Orthopedic Surgery | Hand Surgery | not_discovered | none |
| residency | Otorhinolaryngology | Otorhinolaryngology | discovered_no_current_roster | source_discovery |
| fellowship | Otorhinolaryngology | Neurotology | not_discovered | none |

Learning: source discovery is not coverage. An official program-universe table gives the denominator needed for gap accounting, annual recrawls, and institution-level diff views. `covered_current_roster` means we have current people attached; `discovered_no_current_roster` means a program page is known but no current roster people are captured; `not_discovered` names crawl gaps.

## HUP Gap Source Queue

Gap programs probed: 58. Source pages probed: 58. Candidate URLs queued: 278.

| candidate_status | count |
| --- | --- |
| low_value_candidate | 22 |
| program_context_candidate | 156 |
| roster_source_candidate | 100 |

Top roster-source candidates:

| program_name | department | candidate_status | priority | candidate_title | candidate_url |
| --- | --- | --- | --- | --- | --- |
| Family Medicine | Family Medicine | roster_source_candidate | 145 | Current Residents | https://www3.pennmedicine.org/departments-and-centers/family-medicine-and-community-health/education-and-training/residency/current-residents |
| Obstetrics and Gynecology | Obstetrics and Gynecology | roster_source_candidate | 145 | Current Residents | https://www3.pennmedicine.org/departments-and-centers/obstetrics-and-gynecology/education-and-training/residency-programs/obgyn-residency-program-hup/current-residents |
| Adult Reconstructive Orthopedics | Orthopedic Surgery | roster_source_candidate | 145 | Current Fellows | https://www3.pennmedicine.org/departments-and-centers/orthopaedic-surgery/education-and-training/fellowships/current-fellows |
| Hand Surgery | Orthopedic Surgery | roster_source_candidate | 145 | Current Fellows | https://www3.pennmedicine.org/departments-and-centers/orthopaedic-surgery/education-and-training/fellowships/current-fellows |
| Neurotology | Otorhinolaryngology | roster_source_candidate | 145 | Current Fellows | https://oto.med.upenn.edu/current-fellows |
| Neurotology | Otorhinolaryngology | roster_source_candidate | 145 | Current Residents | https://oto.med.upenn.edu/current-residents |
| Neurological Surgery | Neurological Surgery | roster_source_candidate | 135 | Residents | https://www3.pennmedicine.org/departments-and-centers/neurosurgery/education-and-training/residency/residents |
| Oral Medicine | Oral and Maxillofacial Surgery | roster_source_candidate | 135 | Current Residents | https://www.dental.upenn.edu/departments/oral-medicine/resident-profiles |
| Orthopedic Surgery | Orthopedic Surgery | roster_source_candidate | 135 | Residents | https://www3.pennmedicine.org/departments-and-centers/orthopaedic-surgery/education-and-training/residency/residents |
| Neurotology | Otorhinolaryngology | roster_source_candidate | 135 | Resident Profiles | https://oto.med.upenn.edu/resident-profiles |
| Otorhinolaryngology | Otorhinolaryngology | roster_source_candidate | 135 | Current Fellows | https://oto.med.upenn.edu/current-fellows |
| Otorhinolaryngology | Otorhinolaryngology | roster_source_candidate | 135 | Current Residents | https://oto.med.upenn.edu/current-residents |
| Podiatric Surgery | Podiatric Surgery | roster_source_candidate | 135 | Residents | https://www3.pennmedicine.org/departments-and-centers/podiatry-and-podiatric-surgery/education-and-training/residency-program/residents |
| Radiation Oncology | Radiation Oncology | roster_source_candidate | 135 | Current Residents | https://www.med.upenn.edu/radiationoncologymedicalresidency/current-residents.html |
| Radiology - Interventional, Independent | Radiology | roster_source_candidate | 135 | Current Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-radiology/education-and-training/residency-programs/current-residents |
| Colon and Rectal Surgery | Surgery | roster_source_candidate | 135 | Meet Our Fellow | https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training/fellowships/colon-and-rectal-surgery-fellowship/fellows |
| Craniofacial Surgery | Surgery | roster_source_candidate | 135 | Meet Our Fellow | https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training/fellowships/craniofacial-surgery-fellowship/fellow |
| Plastic Surgery | Surgery | roster_source_candidate | 135 | Meet Our Residents | https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training/residencies/plastic-surgery/residents |
| Thoracic Surgery - Thoracic Track | Surgery | roster_source_candidate | 135 | Meet Our Fellow | https://www3.pennmedicine.org/departments-and-centers/department-of-surgery/education-and-training/fellowships/thoracic-surgery-fellowship-thoracic-track/fellow |
| Blood Banking and Transfusion Medicine | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Fellows | https://pathology.med.upenn.edu/department/people/fellows |
| Blood Banking and Transfusion Medicine | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Residents | https://pathology.med.upenn.edu/department/people/residents |
| Cytopathology | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Fellows | https://pathology.med.upenn.edu/department/people/fellows |
| Cytopathology | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Residents | https://pathology.med.upenn.edu/department/people/residents |
| Gastrointestinal and Hepatic Pathology (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Fellows | https://pathology.med.upenn.edu/department/people/fellows |
| Gastrointestinal and Hepatic Pathology (Selective) | Pathology and Laboratory Medicine | roster_source_candidate | 130 | Residents | https://pathology.med.upenn.edu/department/people/residents |

Learning: coverage gaps need their own crawl state. Official program URLs, discovered context pages, and linked roster-like pages should be queued separately so the next scraper can attack high-priority roster candidates without conflating them with verified person records.

## Penn-Wide Program Categorization

| program_name | role | count |
| --- | --- | --- |
| General Surgery Residency | resident | 75 |
| Diagnostic Radiology Residency | resident | 54 |
| Plastic Surgery Residency | resident | 22 |
| Urology Residency | resident | 22 |
| Ophthalmology Residency | resident | 20 |
| Interventional Radiology Integrated Residency | resident | 19 |
| Cardiothoracic Surgery Residency | resident | 15 |
| Trauma and Surgical Critical Care Fellowship | fellow | 12 |
| Neuroradiology Fellowship | fellow | 11 |
| Ophthalmology Fellowship | fellow | 10 |
| Abdominal Imaging Fellowship | fellow | 9 |
| Vascular Surgery Integrated Residency | resident | 9 |
| Microvascular Reconstructive Surgery Fellowship | fellow | 5 |
| Thoracic Surgery Fellowship - Cardiac Track | fellow | 4 |
| Vascular Surgery Fellowship | fellow | 4 |
| Advanced Musculoskeletal Fellowship | fellow | 3 |
| Transplant Surgery Fellowship | fellow | 3 |
| Aortic Surgery Fellowship | fellow | 2 |
| Nuclear Radiology Fellowship | fellow | 2 |
| ABR Alternate Pathway to Certification | fellow | 1 |
| Advanced Nuclear Radiology Fellowship | fellow | 1 |
| Cardiothoracic Fellowship | fellow | 1 |
| Cardiothoracic Transplantation Surgery Fellowship | fellow | 1 |
| Oncologic Imaging Fellowship | fellow | 1 |

Generic `Residents`/`Fellows` program labels remaining: 0.

Learning: program names often require URL-plus-section inference. Page titles alone are too weak because official pages can be titled `Residents` or `Fellows`, while one source page can contain multiple program sections.

## Training State Machine

| stage_family | normalized_stage | status | count | avg_confidence |
| --- | --- | --- | --- | --- |
| clinical_postgraduate | GME_CHIEF_RESIDENT | current | 10 | 0.72 |
| clinical_postgraduate | GME_CLINICAL_YEAR_2 | current | 9 | 0.72 |
| clinical_postgraduate | GME_CLINICAL_YEAR_3 | current | 10 | 0.72 |
| clinical_postgraduate | GME_CLINICAL_YEAR_4 | current | 9 | 0.72 |
| clinical_postgraduate | GME_INDEPENDENT_RESIDENT | current | 2 | 0.62 |
| clinical_postgraduate | GME_PGY_1 | current | 124 | 0.884 |
| clinical_postgraduate | GME_PGY_2 | current | 146 | 0.9 |
| clinical_postgraduate | GME_PGY_3 | current | 121 | 0.9 |
| clinical_postgraduate | GME_PGY_4 | current | 31 | 0.9 |
| clinical_postgraduate | GME_PGY_5 | current | 10 | 0.9 |
| clinical_postgraduate | GME_PGY_6 | current | 5 | 0.9 |
| clinical_postgraduate | GME_PRELIMINARY_RESIDENT | current | 13 | 0.66 |
| clinical_postgraduate | GME_RESIDENT_CLASS_YEAR | current | 15 | 0.62 |
| clinical_postgraduate | GME_RESIDENT_YEAR_UNKNOWN | current | 73 | 0.42 |
| clinical_postgraduate_research | GME_RESEARCH_OR_LAB_YEAR | current | 23 | 0.68 |
| fellowship | FELLOWSHIP_CURRENT_YEAR_UNKNOWN | current | 117 | 0.498 |
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
| expected GME annual advancement around Jul 1 unless program-specific exception | 420 |
| expected fellowship annual advancement around Jul 1; terminal year requires program-length context | 168 |
| MSTP PhD phase duration is individualized; refresh from public directory annually | 123 |
| current fellow but year not normalized; refresh on next roster and use program-specific duration if available | 109 |
| current resident but year not visible on source; refresh on next roster | 73 |
| expected annual medical-school class advancement around Aug 1 | 53 |
| clinical-phase student label is ambiguous; refresh on annual directory update rather than auto-advance | 49 |
| expected clinical-year advancement around Jul 1; map to PGY with program review | 28 |
| research/lab resident state is program-specific; refresh from roster rather than auto-advance | 23 |
| intern label maps to PGY1; expected annual advancement around Jul 1 | 17 |
| class-year resident label; derive exact PGY only with program-duration context | 15 |
| preliminary resident label usually maps to a one-year GME state; verify against program context | 13 |
| terminal_or_historical_state; do not auto-advance | 13 |
| chief year is terminal/program-specific; refresh on next academic-year roster | 10 |
| fellowship specialty section lacks year; refresh on next roster and use program-specific duration if available | 8 |
| postdoctoral fellow duration is individualized; refresh annually | 7 |
| independent-resident track is program-specific; refresh annually and map with specialty rules | 2 |

Learning: roster strings should become normalized state observations with explicit clocks. PGY and fellowship-year states can be expected to stale around the next July academic rollover; medical-student MS states use an annual student-directory refresh clock; MSTP PhD, lab, postdoc, chief, and unknown-year states are source-refresh states, not safe auto-advancement states.

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
| pubmed_eutilities | candidate | pubmed_author_query_candidate | 759 | 0.211 |
| pulmonary_critical_care_current_fellows | accepted | medical_school | 34 | 0.868 |
| pulmonary_critical_care_current_fellows | accepted | residency_program | 34 | 0.832 |
| rheumatology_current_fellows | accepted | medical_school | 15 | 0.817 |
| rheumatology_current_fellows | accepted | residency_program | 15 | 0.83 |
| rheumatology_current_fellows | accepted | undergraduate_school | 15 | 0.777 |

## Utility Observations

| utility_key | sample_size | candidate_claims | accepted_claims | rejected_claims | ambiguous_claims | metrics_json |
| --- | --- | --- | --- | --- | --- | --- |
| openalex_author_search | 0 | 0 | 0 | 0 | 0 | {"collector_resume_supported": true, "current_claims": 0, "rate_limit_observed": true} |
| pubmed_eutilities | 759 | 759 | 0 | 0 | 0 | {"claims": 759, "mean_confidence": 0.211} |

## OpenAlex Feature Distribution

| match_features_json | count | avg_confidence |
| --- | --- | --- |

Learning: OpenAlex remains a promising author-disambiguation utility, but the current full-corpus run hit sustained 429 throttling. Record that as source availability/operations evidence, not as rejected person identity evidence.

## PubMed Feature Distribution

| match_features_json | count | avg_confidence |
| --- | --- | --- |
| ["author_query", "high_collision_risk"] | 466 | 0.16 |
| ["author_query", "bounded_result_count"] | 226 | 0.35 |
| ["author_query", "no_results"] | 67 | 0.1 |

Learning: PubMed E-utilities is a strong article database, but author-query search is a weak identity resolver. It should be used after candidate author identity is constrained by OpenAlex/ORCID/profile context, or at article-level with affiliation/coauthor checks.

## Career / Attending Trend Candidates

| event_type | status | count | avg_confidence |
| --- | --- | --- | --- |
| current_penn_attending_candidate | candidate | 49 | 0.55 |
| penn_alumni_outcome_candidate | candidate | 36 | 0.411 |

Learning: current faculty pages and alumni/outcome pages should feed a career-event layer, not the core current-trainee roster. Current Penn attending candidates are useful endpoints for future trend analysis, but they still need reconciliation to prior Penn training records before we claim someone 'ended up at Penn.'

## Public Contact Evidence

| contact_type | contact_scope | verification_status | status | count | avg_confidence |
| --- | --- | --- | --- | --- | --- |
| email | institutional | public_directory_unverified | candidate | 205 | 0.82 |
| email | institutional | public_profile_unverified | candidate | 34 | 0.82 |
| email | institutional | public_roster_unverified | candidate | 53 | 0.82 |

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
