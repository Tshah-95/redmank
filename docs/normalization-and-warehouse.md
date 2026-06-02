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
- `person_program_memberships`: many-to-many membership links.
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
- `v_organization_review_queue`: organization aliases that need review.
- `v_recent_attending_trend_candidates`: career-event candidates for current Penn attending and alumni/outcome trend work.
- `v_public_person_contacts`: public structured contact candidates joined to reconciled people when possible.

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

## First Research Utility Learnings

The first expanded resident/fellow research pass processed 759 Penn-affiliated resident/fellow people from official Penn roster sources.

- PubMed E-utilities generated 759 author-query candidates with zero rejected API errors after retry cleanup. It is useful for discovery, but author-query counts alone are weak evidence because common names collide heavily.
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

## Next Programs

After Penn, good next targets are:

- Johns Hopkins: strong peer benchmark with rich cardiology/internal medicine context.
- UCSF: different web stack and strong research-profile enrichment surface.
- Mass General Brigham / Harvard programs: intentionally hard normalization case because school, hospital, health-system, and program identity diverge.

Those three will stress the resolver better than adding three Penn-like sites.
