# UPenn Cardiology + Internal Medicine Roster Case Study

Date: 2026-06-01

## Scope

This first pass builds a public, source-backed seed corpus for:

- University of Pennsylvania / Penn Medicine Cardiovascular Disease Fellowship current fellows.
- Penn cardiology fellowship alumni availability from official Penn sources.
- Current Penn Internal Medicine-associated residents across the official Penn Medicine and CHOP roster pages that are publicly available.

The durable outputs are:

- `artifacts/data/penn_training_people.json` - all extracted roster rows, including duplicate track appearances.
- `artifacts/data/penn_training_people_unique.json` - deduplicated person view using normalized names plus a small alias map.
- `artifacts/data/penn_training_people.csv` and `artifacts/data/penn_training_people_unique.csv` - spreadsheet-ready versions.
- `artifacts/data/penn_profile_index.md` - human-readable per-person review table with quality notes.
- `artifacts/data/raw/*.html` - raw source snapshots fetched by the scraper.
- `scripts/scrape_penn_training.py` - repeatable scraper.

## Sources Used

Official Penn Medicine / CHOP sources:

- Penn Cardiovascular Disease Fellowship current fellows: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/cardiovascular-disease-fellowship/current-fellows
- Penn Cardiovascular Disease Fellowship alumni page: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/cardiovascular-disease-fellowship/alumni
- Penn Cardiovascular Disease Fellowship landing page: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/divisions/division-of-cardiovascular-medicine/education-and-training/fellowship-programs/cardiovascular-disease-fellowship
- Penn Internal Medicine categorical residents: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/categorical/categorical-residents
- Penn Internal Medicine primary care residents: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/primary-care-program/primary-care-residents
- Penn Medicine-Dermatology residents: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/combined-internal-medicine-dermatology-program/medicine-dermatology-residents
- Penn Internal Medicine Global Health Equities residents: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/global-health/global-health-equities-residents
- Penn-CHOP Internal Medicine-Pediatrics current residents: https://www.chop.edu/med-peds-residency/current-residents
- Penn Internal Medicine FAQ, used for program position categories: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/application-information/faqs

## What We Got

The scraper extracted 279 roster rows and 2 context rows. After deduping residents who appear on both a main roster and a track page, this becomes 252 unique people:

| Population | Roster rows | Notes |
|---|---:|---|
| Cardiology current fellows | 33 | 12 first-year, 10 second-year, 10 third-year, 1 fourth-year. |
| Cardiology alumni | 0 person rows | Official alumni page is aggregate-only. It gives example career destinations/roles, not names. |
| IM categorical page | 173 | The page appears to function as the broad HUP IM resident roster, not just a narrow categorical-only list. |
| IM primary care page | 21 | Mostly duplicates people already on the categorical page, but useful as a track membership source. |
| IM medicine-dermatology page | 5 | Mostly duplicates people already on the categorical page, but useful as a combined-program source. |
| IM Global Health Equities page | 22 | Track roster; includes duplicates from categorical and med-peds. |
| Penn-CHOP med-peds page | 25 | 24 PGY1-PGY4 residents plus 1 chief resident. |

Unique people after dedupe:

- 33 current cardiology fellows.
- 219 Internal Medicine-associated people including the med-peds chief resident.
- 218 Internal Medicine-associated current residents if the med-peds chief is excluded.

Field coverage across the 252 unique people:

| Field | Coverage | Consistency |
|---|---:|---|
| Name | 252/252 | Complete from all roster pages. |
| Headshot URL | 252/252 | Complete from all roster pages. |
| Medical school | 241/252 | Strong on Penn Medicine structured pages; weaker on CHOP med-peds prose. |
| Cardiology prior residency program | 33/33 fellows | Complete for current fellows. |
| Individual Penn profile URL | 124/252 | Present for many Penn Medicine residents; absent for cardiology fellows and CHOP med-peds. |
| Individual profile text excerpt | 124/124 linked profiles | Successful fetch for all linked profiles. |

## Source Quality

High quality:

- Penn Medicine `bio-list` pages are structured enough for reliable extraction of name, training year, medical school, headshot, and sometimes profile URL.
- Penn cardiology current fellows are particularly clean for the key cardiology-fellowship fields: year, medical school, and residency program.
- Linked Penn IM profile pages add extra profile text for many residents, including fields such as home state and interests when the profile exists.

Medium quality:

- CHOP med-peds is a prose page. It is good for names, class year, pronouns, headshots, and biographies, but medical school is not consistently represented as a field. The scraper only infers medical school when the bio language is clear.
- Track pages create duplicate people. This is useful because the duplicates become membership signals, but the raw row count should not be interpreted as unique people.

Low / missing:

- Penn’s official cardiology alumni page does not expose person-level former fellow names. It only describes broad alumni outcomes and example roles. A reliable former-fellow corpus will need another source class: archived current-fellow pages, graduation announcements, faculty bios that mention Penn cardiology fellowship training, PubMed/OpenAlex affiliation histories, LinkedIn/manual web search, or direct program-provided lists.
- Penn’s Physician-Scientist Pathway page did not expose a current resident roster in the same way the other pages did. The broad categorical roster likely contains physician-scientist residents, but the pathway membership is not recoverable from the current public page alone.

## Notable Profile Example

Krishna Ravindra appears on the Penn IM broad/categorical roster as:

- Name: Krishna Ravindra MD
- Training year: PGY 3
- Medical school: Virginia Commonwealth University
- Public profile URL: https://www3.pennmedicine.org/departments-and-centers/department-of-medicine/education-and-training/internal-medicine-residency/our-program/categorical/categorical-residents/pgy-3/ravindra-kirshna
- Profile excerpt includes home state, hobbies, and Philadelphia-interest fields.

The official profile URL uses `ravindra-kirshna`, which appears misspelled but returns HTTP 200 and is therefore preserved as the canonical public URL.

## Methodology Notes

The first version intentionally separates:

- `source rows`: every roster appearance, including duplicate track memberships.
- `unique people`: deduped person view with `source_memberships`, `program_memberships`, and `training_year_labels_seen`.

This is the right shape for fellowship-comparison work because track membership is a meaningful signal and should not be lost during dedupe.

The quality model in this pass is simple:

- `high`: structured Penn Medicine component with expected fields.
- `medium`: prose extraction or missing expected fields.
- `context_only`: official page used for program context, but no person-level roster.

The next methodological layer should enrich each person against canonical sources in this order:

1. Official program profile page and source roster.
2. Institution faculty/provider page, if the person has one.
3. PubMed/OpenAlex/ORCID for publication graph and topical research signal.
4. NIH RePORTER, clinicaltrials.gov, and society abstracts where relevant.
5. General web search only after canonical sources are exhausted, with provenance labels.

## Caveats

- This is a public web snapshot fetched on 2026-06-01. Roster pages can change without notice.
- The Penn IM categorical page count is larger than a narrow categorical class count, so treat it as the broad official Penn IM roster unless the program gives a more specific export.
- Person dedupe uses normalized names plus a small alias map. It correctly merges observed variants such as Anne/Annie Albright and Emma Akman Greenstreet/Emma Greenstreet Akman, but future schools will need stronger identity resolution.
