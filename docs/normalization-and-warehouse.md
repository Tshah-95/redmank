# Normalization and Warehouse

`redmank` keeps source strings and resolved entities separate. The source string is what Penn published. The resolved entity is our best current interpretation.

## Organization Normalization

The resolver uses four layers:

1. Preserve `raw_value` exactly as extracted.
2. Create a mechanical `normalized_label` for matching.
3. Resolve through seeded aliases in `config/organization_seed_aliases.json`.
4. Create reviewable `cleaned_label` organizations when no seeded alias exists.

The important detail is context. The same text can mean different things depending on the field:

- `University of Pennsylvania` as `medical_school` can mean Perelman.
- `University of Pennsylvania` as `residency_program` can mean Hospital of the University of Pennsylvania.
- `University of Pennsylvania` as `undergraduate_school` should stay the university.

So aliases are applied by organization category, not globally.

## Identifiers

The schema supports external identifiers without requiring every row to have one immediately:

- `ror` or `parent_ror` for universities, health systems, and research institutions.
- `openalex` for publication-affiliation reconciliation.
- `ipeds_unitid` for US higher-ed campuses.
- `wdoms` for international medical schools.
- `lcme` or `coca` status/source URLs for US MD/DO schools.
- `acgme`, `eras`, and `nrmp` for programs or match tracks, not medical schools.

Identifier attachment should be conservative. Name-only automatic matches should become candidates unless another anchor agrees, such as city/state, parent institution, official profile, program, or source URL.

## SQLite Model

The warehouse is generated at `artifacts/data/redmank.sqlite`.

Core tables:

- `people`: resolved person rows with raw JSON retained.
- `sources`: official roster, context, and discovery source records.
- `programs`: local program entities.
- `official_program_universe`: official external denominator programs, starting with the public HUP GME program list.
- `official_program_coverage_audit`: comparison of official denominator programs to captured current roster memberships and discovered source pages.
- `official_program_source_probes`: reachability, title, content hash, and page-signal observations for official program gap URLs.
- `official_program_source_candidates`: prioritized candidate source URLs for closing uncovered official program rosters.
- `person_program_memberships`: many-to-many membership links.
- `person_training_states`: normalized current stage observations with expected transition and stale-after dates.
- `program_lifecycle_rules`: local lifecycle codes and nominal-duration assumptions used to interpret training states over time.
- `organizations`: resolved organization entities.
- `organization_aliases`: raw and curated aliases.
- `organization_identifiers`: external IDs.
- `person_training_events`: medical school, residency, undergraduate, graduate-school events.
- `career_events`: candidate current Penn attending and alumni/outcome events used for future trend reconciliation.
- `person_contacts`: public contact candidates with source, scope, verification status, confidence, and candidate status.
- `evidence_claims`: accepted and candidate claims for recursive enrichment.
- `source_utilities`: source taxonomy, default trust, claim types, limitations, and acceptance rules.
- `source_quality_observations`: empirical notes from enrichment runs.

Useful views:

- `v_person_training`: joined person-training-organization view.
- `v_current_training_states`: normalized state-machine view for annual refresh/diff work.
- `v_official_program_coverage_gaps`: official programs without captured current roster people.
- `v_official_program_source_queue`: prioritized candidate roster/context pages for uncovered official programs.
- `v_organization_review_queue`: organization aliases that need review.
- `v_recent_attending_trend_candidates`: career-event candidates for current Penn attending and alumni/outcome trend work.
- `v_evidence_reconciliation_queue`: ranked candidate evidence and career-event review queue.
- `v_public_person_contacts`: public structured contact candidates joined to reconciled people when possible.

## Program Universe Coverage

The state machine needs a denominator. For HUP, `scripts/audit_penn_gme_program_coverage.py` parses the official public Penn Medicine HUP GME program list and compares each official residency/fellowship program to the current SQLite warehouse.

It emits:

- `penn_gme_program_universe.json`: official program records with department, program type, program URL, source URL, content hash, and confidence.
- `penn_gme_program_coverage.csv` / `.json`: official programs annotated as `covered_current_roster`, `discovered_no_current_roster`, or `not_discovered`.
- `penn_gme_program_coverage_summary.json`: denominator counts by program type and coverage status.
- `penn_gme_gap_source_candidates.csv` / `.json`: prioritized next-source queue for programs without captured roster people.
- `penn_gme_gap_source_probes.json`: page-level probe evidence, including reachability, title, content hash, roster/context term counts, and errors.

This is deliberately separate from person scraping. A source crawler can find a program page without finding a usable roster, and a roster scraper can capture people without proving the full official denominator. Keeping both layers lets future runs show changes at several levels:

- person: new, missing, renamed, duplicated, advanced, regressed, stale, or reconciled.
- program: roster count changed, roster unavailable, official program added/removed, or program alias changed.
- institution/category: coverage changed across HUP, Penn Medicine, GME specialty family, residency, fellowship, or student populations.

The gap-source queue is also deliberately separate from person evidence. It lets the next scraper prioritize likely roster URLs, such as `current-residents`, `current-fellows`, `resident-profiles`, and `meet-our-fellow` pages, while keeping program overview pages and unreachable URLs out of the core person corpus until they yield named public trainees.

`scripts/scrape_penn_gme_gap_rosters.py` consumes only high-priority roster-source candidates and writes a separate `penn_gme_gap_roster_people.json` layer. It currently supports explicit page structures only: Penn Medicine bio cards, PSOM profile blocks, WordPress/Elementor heading-plus-name lists, and Dental accordion headers. Unsupported pages remain queued rather than becoming weak person claims.

## Recursive Enrichment Loop

`scripts/generate_enrichment_queue.py` creates `artifacts/data/person_enrichment_queue.csv`.

The intended loop:

1. Run a batch of high-priority enrichment tasks.
2. Store findings as `evidence_claims`, not direct profile mutations.
3. Accept only claims with sufficient identity anchors.
4. Add successful organization aliases/identifiers to the seed map.
5. Rebuild SQLite and regenerate queues.
6. Repeat until the remaining queue is mostly low-confidence or low-value.

This lets the method improve without quietly poisoning the corpus.

`v_evidence_reconciliation_queue` is the review workbench. It combines candidate/needs-review scholarly claims and career-event claims into one ranked surface with a review action. Priority is based on status, source/claim type, confidence, and non-name anchors such as Penn affiliation, prior education/training affiliation, specialty-topic match, ORCID presence, structured provider training fields, and Penn-training language. Low-value discovery signals remain visible but are ranked below article/profile evidence.

## Attending Trend Evidence

Current Penn attending/faculty pages and official Penn provider/profile pages are loaded as career-event evidence, not as trainee roster truth. `scripts/enrich_penn_attending_profiles.py` follows profile URLs from current attending candidates and extracts only conservative official-profile claims:

- structured provider-page Medical School, Residency, and Fellowship fields.
- department biography sentences with explicit Penn/HUP training language.
- research-interest and personal-profile sentences when the profile page publishes them directly.

Penn training-history claims from current attending profiles are `needs_review`, not accepted. They are useful for the ten-year trend line only after reconciliation links the current attending identity to a prior Penn trainee record or another independent public anchor.

## First Research Utility Learnings

The first expanded resident/fellow research pass processed 759 Penn-affiliated resident/fellow people from official Penn roster sources.

- PubMed E-utilities generated 759 author-query candidates with zero rejected API errors after retry cleanup. It is useful for discovery, but author-query counts alone are weak evidence because common names collide heavily.
- PubMed article-level reconciliation now fetches PubMed XML for bounded author-query candidates and stores per-article candidates with target-author, affiliation, topic, and recency features. This is stronger than count evidence but still not accepted automatically.
- OpenAlex author search is implemented, retryable, and resumable, but the latest full-corpus run hit sustained 429 throttling. The current warehouse records this as a source-quality observation rather than as rejected person evidence.
- No research claims were accepted automatically.

The current acceptance rule is deliberately strict: accept research enrichment only when at least two non-name anchors agree, such as official profile link plus ORCID, OpenAlex Penn affiliation plus specialty-topic match, PubMed affiliation plus coauthor cluster, or NPI specialty/location plus official profile.

## Public Contact Evidence

The current warehouse stores 292 public email candidates:

- 205 from the official public Penn MSTP student directory.
- 53 from official Medicine roster pages.
- 34 from current Penn attending/faculty candidate pages.

These are not flattened into `people`. They live in `person_contacts` because contact channels can be multiple, stale, source-specific, or attached to a named candidate who has not yet been reconciled into the core identity table. Raw HTML snapshots remain redacted; only structured public contact candidates are committed.

## Program Categorization

Broad Penn roster pages cannot always use the page title as the program name. Some official pages are titled only `Residents` or `Fellows`, and some pages, especially Radiology, contain several fellowship sections on one source page. The broad Penn scraper therefore infers program labels from the URL path plus section heading. This removed generic `Residents`/`Fellows` program labels from the warehouse and corrected Ophthalmology fellows that share a `Current Residents & Fellows` page with residents.

## Training State Machine

Training labels are stored as state observations, not just strings. `person_training_states` keeps the raw source label plus a normalized stage, family, index, academic year, lifecycle rule/code, expected next stage/date, expected exit date, stale-after date, refresh policy, transition rule, confidence, and evidence JSON.

`observed_at` is source-derived when the source has a fetch timestamp, with a deterministic as-of-date fallback. That keeps rebuilds from creating fake state changes just because SQLite was regenerated later.

Program lifecycle assumptions live in `config/training_lifecycle_rules.json`, not in source records. A lifecycle rule can say that a current PGY-2 observation is `year_2_of_3`, `year_2_of_5`, or `year_2_duration_unknown` depending on the program. This is intentionally an interpretation layer: source rows still preserve exactly what Penn published, while lifecycle codes make time-based comparison possible.

The current lifecycle code namespace is local to `redmank`, for example `US_GME_RESIDENCY_3Y`, `US_GME_FELLOWSHIP_1Y`, and `US_MD_PHD_MSTP_VARIABLE`. External identifiers such as ACGME, ERAS, or NRMP belong on program/track records only after source-backed verification; they should not be guessed from program names.

The current rules are intentionally conservative:

- PGY, CY, intern, and fellowship-year labels use a GME annual-clock assumption around July 1, then lifecycle rules determine whether the state is annual advancement, terminal completion, outside nominal duration, or unknown-duration refresh.
- MS1/MS2/MS3-4 labels use a medical-student annual-refresh clock around August 1.
- MSTP PhD phase, lab/research residents, postdoc fellows, chief residents, and unknown-year fellows/residents are not auto-advanced. They become stale on a refresh schedule and require a new public source observation.

This creates the future diff surface: when the corpus is rerun, we can compare person/program/institution/category state observations, identify expected transitions, flag surprising disappearances or regressions, and separate obvious stale data from genuinely changed records.

`scripts/diff_training_states.py` compares exported state snapshots. It collapses multiple raw observations for the same person/program into a canonical comparison key and reports how many duplicate keys were collapsed, so the diff view stays readable while the warehouse still preserves raw state observations. It also writes rollups by program, role, lifecycle code, and change type for program-, category-, and institution-level monitoring.

The intended freshness semantics are:

- Expected advancement: PGY/CY/fellowship-year and MS-year labels can advance on their academic clocks if the same person/program remains observed.
- Expected completion: terminal-year observations can disappear after their stale-after date without being treated as a scraper miss.
- Source refresh required: PhD phase, lab/research residents, postdoc fellows, chief residents, unknown-year fellows/residents, and public contact channels become stale unless a fresh public source repeats or updates them.
- Surprising change: disappearance before an expected end date, program-family change, regression in normalized stage, or conflicting concurrent stage labels should become review items, not automatic mutations.
- Denominator change: official program-universe additions/removals should be separated from person-level roster movement so an annual diff can tell the difference between “program disappeared from Penn’s public list” and “our scraper missed the page.”

## Next Programs

After Penn, good next targets are:

- Johns Hopkins: strong peer benchmark with rich cardiology/internal medicine context.
- UCSF: different web stack and strong research-profile enrichment surface.
- Mass General Brigham / Harvard programs: intentionally hard normalization case because school, hospital, health-system, and program identity diverge.

Those three will stress the resolver better than adding three Penn-like sites.
