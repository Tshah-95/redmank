# Penn Source Quality Learnings

Generated: 2026-06-02T03:43:11.997564+00:00

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
| openalex_author_search | candidate | research_author_candidate | 1085 | 0.427 |
| openalex_author_search | needs_review | research_author_candidate | 116 | 0.9 |
| palliative_current_fellows | accepted | medical_school | 5 | 0.75 |
| palliative_current_fellows | accepted | residency_program | 5 | 0.75 |
| pubmed_eutilities | candidate | pubmed_author_query_candidate | 453 | 0.208 |
| pulmonary_critical_care_current_fellows | accepted | medical_school | 34 | 0.868 |
| pulmonary_critical_care_current_fellows | accepted | residency_program | 34 | 0.832 |
| rheumatology_current_fellows | accepted | medical_school | 15 | 0.817 |
| rheumatology_current_fellows | accepted | residency_program | 15 | 0.83 |
| rheumatology_current_fellows | accepted | undergraduate_school | 15 | 0.777 |

## Utility Observations

| utility_key | sample_size | candidate_claims | accepted_claims | rejected_claims | ambiguous_claims | metrics_json |
| --- | --- | --- | --- | --- | --- | --- |
| openalex_author_search | 453 | 1085 | 0 | 0 | 116 | {"claims": 1201, "mean_confidence": 0.4723} |
| pubmed_eutilities | 453 | 453 | 0 | 0 | 0 | {"claims": 453, "mean_confidence": 0.2084} |

## OpenAlex Feature Distribution

| match_features_json | count | avg_confidence |
| --- | --- | --- |
| ["name_match"] | 386 | 0.4 |
| ["name_match", "orcid_present"] | 206 | 0.5 |
| ["orcid_present"] | 172 | 0.25 |
| [] | 118 | 0.15 |
| ["name_match", "penn_affiliation"] | 94 | 0.8 |
| ["name_match", "penn_affiliation", "orcid_present"] | 83 | 0.9 |
| ["name_match", "penn_affiliation", "residency_program_affiliation", "orcid_present"] | 18 | 0.9 |
| ["name_match", "penn_affiliation", "residency_program_affiliation"] | 16 | 0.8 |
| ["name_match", "residency_program_affiliation"] | 15 | 0.55 |
| ["penn_affiliation", "orcid_present"] | 14 | 0.65 |
| ["name_match", "medical_school_affiliation"] | 12 | 0.55 |
| ["name_match", "penn_affiliation", "medical_school_affiliation", "orcid_present"] | 11 | 0.9 |
| ["name_match", "medical_school_affiliation", "orcid_present"] | 11 | 0.65 |
| ["name_match", "penn_affiliation", "medical_school_affiliation"] | 9 | 0.8 |
| ["penn_affiliation"] | 7 | 0.55 |
| ["name_match", "residency_program_affiliation", "orcid_present"] | 7 | 0.65 |
| ["name_match", "medical_school_affiliation", "residency_program_affiliation"] | 7 | 0.55 |
| ["name_match", "medical_school_affiliation", "residency_program_affiliation", "orcid_present"] | 6 | 0.65 |
| ["name_match", "penn_affiliation", "medical_school_affiliation", "residency_program_affiliation", "orcid_present"] | 4 | 0.9 |
| ["residency_program_affiliation", "orcid_present"] | 1 | 0.4 |

Learning: OpenAlex is useful for generating review candidates when name, Penn affiliation, prior institution, and ORCID features cluster. It is not safe as a direct profile mutator because author disambiguation and stale affiliations remain real risks.

## PubMed Feature Distribution

| match_features_json | count | avg_confidence |
| --- | --- | --- |
| ["author_query", "high_collision_risk"] | 280 | 0.158 |
| ["author_query", "bounded_result_count"] | 131 | 0.35 |
| ["author_query", "no_results"] | 42 | 0.1 |

Learning: PubMed E-utilities is a strong article database, but author-query search is a weak identity resolver. It should be used after candidate author identity is constrained by OpenAlex/ORCID/profile context, or at article-level with affiliation/coauthor checks.

## Reconciliation Rule Update

For the next pass, accept research enrichment only when at least two non-name anchors agree. Examples: official profile link plus ORCID; OpenAlex Penn affiliation plus specialty-topic match; PubMed affiliation plus coauthor cluster; NPI specialty/location plus official profile.

## Source References

- OpenAlex institutions documentation notes that all OpenAlex institutions have ROR IDs and that parsing author affiliations is nontrivial: https://docs.openalex.org/api-entities/institutions
- NCBI E-utilities are the public API for Entrez databases including PubMed: https://www.ncbi.nlm.nih.gov/home/develop/api/
- ORCID supports organization identifiers including ROR for affiliations: https://info.orcid.org/documentation/integration-guide/working-with-organization-identifiers/
- NPPES provides an official public read API for NPI Registry data: https://npiregistry.cms.hhs.gov/api-page
- ClinicalTrials.gov provides an official API and OpenAPI specification: https://clinicaltrials.gov/data-about-studies/learn-about-api
- WDOMS is a searchable directory of undergraduate medical education programs; listing confirms existence but not accreditation or endorsement unless stated: https://wfme.org/world-directory/
