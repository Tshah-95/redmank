# Redmank Penn Medicine Trainee Corpus Methodology

Date: 2026-06-01

## Scope

This brief documents the first `redmank` case study: a public-source Penn trainee corpus centered on Penn Department of Medicine residents and fellows, plus a separately labeled partial medical-student source from Penn MSTP. The user goal is maximum public-source enrichment with explicit methodology, quality scoring, and tradeoffs.

## Key Findings

1. The current resident/fellow corpus has 528 person rows and 453 deduplicated people in `artifacts/data/penn_training_people_unique.json`, generated from 28 official roster/context sources recorded in `artifacts/data/penn_training_sources.json`.
2. Deduplicated status counts are 220 current fellows, 13 former fellows, 219 current residents, and 1 chief resident in `artifacts/data/penn_training_summary.json`.
3. The second-pass source-discovery crawler reviewed 650 Penn Department of Medicine pages and produced 394 findings: 24 roster candidates, 67 non-bio roster candidates, 11 review candidates, and 292 context pages in `artifacts/data/penn_source_discovery.json`.
4. The discovery pass found two cardiology trainee sources missing from the first curated pass: Penn's Cardio-Oncology Fellowship page and Advanced Noninvasive Cardiac Imaging page. Those are now included in `scripts/scrape_penn_training.py`.
5. No public all-Perelman-MD-student roster was found. A public Penn MSTP student directory does exist and is now kept as a separate partial student dataset with 225 records in `artifacts/data/penn_mstp_students.json`.
6. The best person-level roster authority is the official Penn roster page itself. Enrichment sources like PubMed, OpenAlex, ORCID, NIH RePORTER, ClinicalTrials.gov, NPPES, and society abstracts are useful but should not overwrite roster truth without identity-resolution evidence.

## Current Corpus

### Resident and Fellow Sources

The main scraper uses official Penn Medicine and CHOP pages:

| Source class | Examples | Quality |
|---|---|---|
| Official Penn `bio-list` rosters | Cardiovascular Disease current fellows, hematology/oncology fellows, infectious diseases fellows, pulmonary/critical care fellows, categorical residents | High for name, program, year/group label, medical school/residency fields when present |
| Official Penn fellowship pages with mixed bio components | Adult congenital cardiology, advanced heart failure, electrophysiology, interventional cardiology, cardio-oncology, advanced imaging, geriatrics | High after group-label filtering removes leadership/faculty sections |
| Official prose rosters | Hospice and palliative medicine fellows, Penn-CHOP med-peds residents | Medium because fields are parsed from prose rather than uniform components |
| Official context-only pages | Cardiology alumni, IM FAQ, program landing pages in source discovery | Context only; useful for methodology and program attributes, not person extraction |
| Public source discovery results | `artifacts/data/penn_source_discovery.json` | Review queue for coverage, not canonical roster data |

Representative official roster sources include Penn's Cardiovascular Disease current fellows page, Penn's categorical residents page, Penn's primary care residents page, Penn's hematology/oncology fellows page, and Penn's Department of Medicine education/training pages:

- https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/cardiovascular-disease-fellowship/current-fellows
- https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/categorical/categorical-residents
- https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/primary-care-program/primary-care-residents
- https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/hematology-and-oncology/education-and-training/hematology-oncology-fellowship/fellows
- https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training

### Counts

From `artifacts/data/penn_training_summary.json`:

| Metric | Count |
|---|---:|
| Person rows | 528 |
| Deduplicated people | 453 |
| Context rows | 2 |
| Current fellows | 220 |
| Former fellows | 13 |
| Current residents | 219 |
| Chief residents | 1 |
| Records with medical school | 515 |
| Records with residency program | 233 |
| Records with profile URL | 230 |

Important nuance: Penn's Department of Medicine "About" page describes the department as having "171 residents and 160 subspecialty fellows" and also says it has 12 divisions and extensive UME/GME/CME leadership. That page is useful as an institutional context source, but it is not a clean reconciliation target for this corpus because our person-level scrape includes tracks, combined programs, research trainees/postdocs when exposed on roster pages, advanced/non-ACGME fellowship pages, and current plus recently graduated groups where Penn publishes them. Source: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/about-us

### Medical Students

I did not find a public all-MD-student roster for Perelman. Penn Department of Medicine's medical-student education page describes medical-student education, clerkships, sub-internships, electives, and mentoring, but it is not a person-level student roster:

- https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/student-education

I did find Penn MSTP's public student directory, which exposes names, phase, graduate group, thesis advisor for many students, academic interests, hobbies/interests, student organizations, and some publication links. This is now extracted separately as `artifacts/data/penn_mstp_students.json`, not merged into the resident/fellow corpus because it is an MD-PhD subset rather than all Perelman medical students:

- https://www.med.upenn.edu/mstp/student-directory/

The MSTP extraction intentionally does not harvest email addresses, even though the page contains email links.

## Categorization Model

The current schema treats these as separate concepts:

- `role`: resident, fellow, medical_student, alumni, metadata.
- `current_status`: current, former, chief.
- `program`: named program or fellowship.
- `population`: the source's population label, such as `current_fellows`, `categorical_residents`, `public_mstp_students`.
- `training_year_label`: source-visible grouping such as PGY year, first-year fellows, or second-year fellows.
- `source_memberships` and `program_memberships`: multi-valued fields created during deduplication.
- `quality_tier` and `quality_notes`: extraction confidence and missing-field caveats.

This is better than forcing one trainee into one bucket because Penn publishes overlapping memberships. A resident can appear in categorical plus a track page; a fellow can appear in a current fellows page and an advanced fellowship page; a person can have name variants across pages.

## Confirmation Method

The confirmation pass now has three layers:

1. Curated official source list in `scripts/scrape_penn_training.py`.
2. Broad Penn Department of Medicine crawl in `scripts/discover_penn_training_sources.py`, seeded from Department education/training and divisions pages.
3. Manual review of crawler findings for roster pages missed by the curated list.

The crawler classifies pages into:

- `roster_candidate`: pages with Penn bio components and resident/fellow language.
- `non_bio_roster_candidate`: pages likely relevant but without standard bio components.
- `review`: pages with bio components that may be trainees or may be leadership/faculty.
- `context`: fellowship/residency/student pages useful for program metadata.

Merit: this catches source-list blind spots. The cardiology cardio-oncology and advanced imaging pages are concrete examples.

Tradeoff: broad crawl classifications are intentionally noisy. Faculty pages, leadership pages, student-education pages, and observership team pages can look like rosters. The crawler should create a review queue, not automatically expand canonical people.

## Enrichment Source Stack

### Tier 1: Roster Truth

Use official program pages as the source of truth for current membership, role, program, year label, medical school, residency program, and headshot/profile URL when visible. Do not let secondary sources override current roster membership unless Penn updates or removes a page.

### Tier 2: Official Institutional Profiles

Penn trainee profile pages and official health-system/provider pages can add biography excerpts, clinical/research interests, publications links, and sometimes education/training. These are strong enrichment sources when linked directly from the roster.

### Tier 3: Scholarly Identity

Use these sources to enrich publications, citation signals, grants, and trials:

- PubMed through NCBI E-utilities. NCBI documents E-utilities as the public API to Entrez databases including PubMed and PMC: https://www.ncbi.nlm.nih.gov/home/develop/api/
- OpenAlex for open metadata across works, authors, sources, institutions, and topics: https://developers.openalex.org/api-reference/introduction
- ORCID public API for author identifiers when a public ORCID/publications link is present or a high-confidence match exists: https://info.orcid.org/documentation/integration-and-api-faq/
- NIH RePORTER API for federal grant/project records: https://api.reporter.nih.gov/?urls.primaryName=V2.0
- ClinicalTrials.gov API v2.0 for public trial records and investigator/sponsor context: https://www.nlm.nih.gov/pubs/techbull/ma24/ma24_clinicaltrials_api.html

Identity-resolution rule: require at least two anchors beyond name for automatic attachment, such as institution, specialty, mentor, ORCID, profile link, training program, coauthor cluster, or publication topic. Common names should stay in "candidate enrichment" until reviewed.

### Tier 4: Licensure and Program Validation

- NPPES/NPI Registry can validate physicians and sometimes add taxonomy/location data, but it is not a training roster and can be stale or misleading for residents/fellows. Official docs: https://npiregistry.cms.hhs.gov/api-page
- ACGME public data can validate accredited programs and sponsoring institutions, but not individual trainee membership. ACGME support describes public advanced search as basic information about accredited programs and sponsoring institutions: https://support.acgmecloud.org/hc/en-us/articles/36070312362391-Advance-Search-Feature
- AMA FREIDA is useful for program-level context and applicant-facing attributes, but it is not a person-level roster source: https://freida.ama-assn.org/

### Tier 5: Web and Social

General web search, conference abstracts, lab pages, specialty society pages, alumni magazines, personal websites, and LinkedIn-like pages can add previous education, research interests, hobbies, awards, and career outcomes. These should be low-confidence by default unless directly linked by an official profile or independently corroborated.

For a public open-source corpus, I would avoid scraping or republishing emails, phone numbers, private social URLs, or content from login/session-gated pages. For personal text such as hobbies/interests, include only if the source is clearly public and profile-like, keep provenance, and consider summarizing rather than expanding beyond what the source owner already published.

## Quality Scoring

Recommended profile score dimensions:

| Dimension | Examples | Scoring idea |
|---|---|---|
| Roster confidence | Official current roster, official profile, context-only page | 0-1 |
| Categorization confidence | Role, program, year, current/former/chief | 0-1 |
| Field completeness | Medical school, residency, profile, headshot, interests | 0-1 |
| Identity enrichment confidence | PubMed/OpenAlex/ORCID/NPI match certainty | 0-1 |
| Recency | Fresh fetch timestamp, current AY label, archived page | 0-1 |
| Provenance quality | Official page, API, secondary web, social | 0-1 |
| Privacy sensitivity | Student personal text, contact info, private pages | penalty |

Suggested quality labels:

- `gold`: official current roster plus linked official profile or direct profile page.
- `silver`: official roster with structured fields but no profile link.
- `bronze`: official prose roster or partial directory with parse caveats.
- `candidate`: crawler/search result awaiting review.
- `context`: program-level page, not person-level evidence.

## Merits and Tradeoffs

### Merits

- Official roster-first method maximizes precision.
- Raw source snapshots and SHA-256 hashes make the corpus auditable.
- Discovery crawler gives a repeatable way to find missed Penn pages.
- Multi-membership deduplication preserves track/fellowship overlap.
- Separate medical-student dataset avoids claiming MSTP equals all medical students.

### Tradeoffs

- Public rosters change without stable versioning; raw snapshots help but do not prove historical completeness.
- Some Penn pages mix trainee, faculty, leadership, and staff bio components; group filtering is necessary and can miss unusual labels.
- Search/crawl recall is bounded by Penn's information architecture and robots/visibility.
- Publication enrichment is identity-resolution heavy; attaching papers by name alone will create false positives.
- Public student directories can contain personal material; publishing that material increases discoverability even when the source is already public.

## Next Methodological Bar

The next high-confidence expansion should add an enrichment pipeline with explicit evidence objects:

- `evidence_id`, `person_key`, `source_url`, `source_api`, `field_claimed`, `value`, `confidence`, `match_features`, `retrieved_at`.
- Candidate enrichment should be separate from accepted enrichment until identity confidence passes threshold.
- Every automatic enrichment should be reproducible from an API query or stored source URL.
- Human review should focus on ambiguous names, personal-profile fields, and any source below official/institutional quality.
