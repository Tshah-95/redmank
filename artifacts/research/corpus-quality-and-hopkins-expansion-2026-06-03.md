# Corpus Quality Review and Johns Hopkins Expansion Brief

Generated: 2026-06-03

## Current Corpus Quality Review

The first corpus-wide quality review pass now covers every resolved person in the existing Penn corpus.

- People reviewed: 1,535
- Quality lanes per person: 8
- Total review rows: 12,280
- Strong verified rows: 3,543
- Usable with review gaps: 736
- Review-ready rows: 3,017
- Insufficient or candidate-only rows: 1,904
- Blocked/conflicted rows: 3,080
- Rows with any explicit gap: 5,255
- Reviewer-gated auto-normalization suggestions: 10

The lane set is intentionally person-centered:

- `roster_identity`: official current-roster anchor.
- `training_temporal_state`: lifecycle/staleness contract for annual advancement, completion, or retention.
- `official_profile`: accepted profile URL or profile-discovery burden.
- `organization_normalization`: low-confidence education/training labels and trusted-alias suggestions.
- `person_enrichment`: accepted/candidate profile, NPI, publication, career, and secondary evidence.
- `identity_reconciliation`: person-level evidence packet state and blockers.
- `research_identity`: publication/ORCID/OpenAlex/PubMed identity posture.
- `contact_verification`: public contact evidence and freshness contracts.

This is the right shape for the larger autonomous system because it turns "profile quality" into a stable per-person surface. The same lanes can run after each new institution scrape and after every nightly/weekly/monthly maintenance pass.

## Krishna Patel Lesson

Krishna Patel's profile shows the distinction between strong roster identity and weaker enrichment/normalization layers:

- Strong: current Penn Internal Medicine PGY-2 roster identity, official profile URL, and temporal contract.
- Review-bound: NPI/research identity, because common-name collisions need more non-name anchors before acceptance.
- Gap: public contact evidence is absent.
- Normalization issue: `Pern State College of Medicine` now appears as a reviewer-gated organization normalization suggestion to `Penn State College of Medicine`.

The ergonomic lesson is that identity verification needs multiple, visible lanes rather than one overall confidence score. A user should be able to see: "we know this is the right Penn trainee," "we have a profile," "this education label is probably typo-normalizable," and "external identifiers still need review." Those are different risks and should not collapse into one green/red badge.

## Normalization Guardrails Added

The organization review now suggests corrections only from low-confidence labels toward trusted seeded aliases. The first fuzzy pass caught the Penn State typo, but it was too symmetric and could point a good label back toward a typo. The corrected posture is:

- Source strings remain preserved.
- Fuzzy suggestions are non-mutating.
- Suggestions target trusted seeded aliases only.
- Common abbreviations are expanded during comparison, including `SOM`, `RWJ`, and `Mt`.
- Degree suffix collisions are suppressed, so `University of X` is not "fixed" to `University of X, BS`.
- Directional-name collisions are suppressed, so similar real institutions such as Northeastern/Northwestern are not treated as typo fixes.

## Expansion Candidate: Johns Hopkins

Johns Hopkins is a good next institution because it has:

- A central official GME program entry point: `https://www.hopkinsmedicine.org/som/gme/programs`
- Official residency and fellowship finders:
  - `https://www.hopkinsmedicine.org/residencies`
  - `https://www.hopkinsmedicine.org/fellowships/`
- A public ACGME-sponsored program contact/list PDF that can seed denominator rows and program identifiers.
- Several high-yield current roster pages with structured trainee facts:
  - Osler Internal Medicine housestaff: `https://www.hopkinsmedicine.org/medicine/education/osler-medical-residency/housestaff`
  - General Surgery residents: `https://www.hopkinsmedicine.org/surgery/education/residency/general-surgery/meet-our-residents`
  - Neurosurgery residents: `https://www.hopkinsmedicine.org/neurology_neurosurgery/education/neurosurgery_residency/residents.html`
  - Infectious Diseases fellows: `https://www.hopkinsmedicine.org/infectious-diseases/education/fellowships/acgme-adult-infectious-diseases-fellowship/fellows`
  - Neurology residency: `https://www.hopkinsmedicine.org/neurology-neurosurgery/education/neurology-residency`

Recommended first scrape order:

1. Build the Johns Hopkins denominator from GME program finder pages plus the ACGME-sponsored program list.
2. Capture Osler Internal Medicine first, because it is a large, well-structured residency roster with PGY groupings and rich profile text.
3. Capture General Surgery and Neurosurgery next, because they expose PGY groupings, education fields, images, and research interests in page text.
4. Capture one fellowship lane, starting with Infectious Diseases, to validate fellow-specific parser behavior before broad fellowship expansion.
5. Run the same corpus quality lane review immediately after ingestion and compare Penn-vs-Hopkins lane distributions.

## Scraper/Engine Methodology

The repeatable engine should separate four layers:

1. Source observation: fetch URL, status, canonical URL, title, content hash, page text hash, robots/rate policy, parser support, and route-drift signals.
2. Parser output: raw public rows exactly as seen on the page, including section labels, image alt text, profile links, and field labels.
3. Normalization candidates: person keys, program keys, stage labels, organization aliases, profile URLs, and enrichment claims.
4. Acceptance/review: only accepted roster identity and accepted reviewer-gated facts mutate the high-confidence corpus.

Cadence:

- Nightly: reobserve known roster/profile/contact URLs, detect route drift, refresh source hashes, and enqueue parser failures.
- Weekly: execute high-yield enrichment and profile-discovery batches, then run corpus quality lane review.
- Monthly: rebuild denominator/program coverage for each institution, update source-quality scorecards, and search for new source families.

The scraper skill should document common recourse patterns:

- Static HTML roster pages with headings/cards/lists.
- Pages where PGY/class year is in section headers.
- Pages where education is in prose rather than labeled fields.
- Profile pages linked from roster cards.
- Accordion pages, pagination, lazy "see more" sections, and JS-rendered program finders.
- PDF or downloadable program lists used as denominator evidence.
- Route drift where old URLs redirect to department landing pages.
- Parser loss versus true trainee departure: preserve prior rows on transport or parser failure, then let temporal contracts decide stale/change posture.

## Next System Step

The next build unit should make Johns Hopkins look like Penn from the system's perspective:

- institution denominator artifacts
- source discovery/probe artifacts
- roster parser artifacts
- person/program/training-state normalization
- source-quality scorecard rows
- corpus quality lane review comparison

Only then should the third institution be added. The repeatability measure is whether the second institution needs fewer bespoke review fixes than Penn, and whether the third needs fewer than Hopkins.
