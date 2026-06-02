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

`scripts/discover_organization_identifier_candidates.py` is the first non-mutating identifier utility. It queries ROR for high-mention unresolved organization labels and writes:

- `organization_identifier_candidates.csv` / `.json`: candidate rows with source query, ROR identifier, candidate name, candidate type/country/links, match status, confidence, reasons, and evidence JSON.
- `organization_identifier_source_observations.csv`: one row per ROR query, including HTTP/query status, result count, source result count, error text, and request URL.
- `organization_identifier_candidate_summary.json`: status/category/type rollups for the pass.

The important distinction is accepted identifier versus identifier candidate. `organization_identifiers` is reserved for accepted IDs. `organization_identifier_candidates` can include exact ROR hits, parent RORs for medical-school labels, review rows, weak search siblings, and low-signal search artifacts. Parent RORs should be interpreted as institutional context, not as proof that the medical-school sub-entity has its own accepted identifier. Relationship/context labels from ROR are stored as evidence, but they are not allowed to turn a different returned organization into a strong identifier match.

## SQLite Model

The warehouse is generated locally at `artifacts/data/redmank.sqlite`. The SQLite file is ignored by Git; committed flat artifacts plus `artifacts/data/redmank_sqlite_manifest.json` preserve the expected hash, size, storage policy, and validation commands for a rebuilt local warehouse. `scripts/rebuild_local_warehouse.py` performs the no-network replay path from committed artifacts.

Core tables:

- `people`: resolved person rows with raw JSON retained.
- `sources`: official roster, context, and discovery source records.
- `programs`: local program entities.
- `official_program_universe`: official external denominator programs, starting with the public HUP GME program list.
- `official_program_coverage_audit`: comparison of official denominator programs to captured current roster memberships and discovered source pages.
- `official_program_source_probes`: reachability, title, content hash, and page-signal observations for official program gap URLs.
- `official_program_source_candidates`: prioritized candidate source URLs for closing uncovered official program rosters.
- `official_program_gap_reason_audit`: deterministic reason ledger for uncovered official programs, separating context-only pages, parser/manual-review candidates, low-content official pages, related loaded-source alias reviews, and broader-discovery gaps.
- `official_program_alias_reconciliation_candidates`: non-mutating candidate ledger for official denominator rows that may correspond to related loaded program labels.
- `program_identifier_source_observations`: ACGME public-search query observations with HTTP status, result count, relevant-result count, and content hash.
- `program_identifier_candidates`: non-mutating ACGME program-code candidates for official denominator rows, classified as strong, ambiguous, review, or no-code-found.
- `program_identifier_reconciliation`: per-candidate decision ledger for accepted, duplicate-facility, affiliate, track, and no-code states.
- `official_program_identifiers`: accepted external program identifiers for unambiguous official program rows.
- `program_lifecycle_consistency_audit`: accepted-identifier audit that checks current roster coverage and lifecycle-rule completeness before program-level state-machine rollups.
- `medical_student_source_audit`: source-access audit for public MSTP, protected MD-student, MD Program context, and MD-PhD graduate-directory cross-check sources.
- `person_program_memberships`: many-to-many membership links.
- `person_training_states`: normalized current stage observations with expected transition and stale-after dates.
- `program_lifecycle_rules`: local lifecycle codes and nominal-duration assumptions used to interpret training states over time.
- `training_state_snapshots`: materialized longitudinal snapshot metadata with row counts, canonical person/program key counts, duplicate-key counts, and corpus fingerprint.
- `training_state_snapshot_rows`: stable row-level state observations loaded from snapshot CSVs. The canonical comparison key is `person_key + program_name`; raw observations remain separate through `state_key`.
- `training_state_transition_events`: expected-vs-review transition ledger between materialized snapshots.
- `training_state_machine_audit`, `person_training_state_machine_audit`, `program_training_state_machine_audit`: queryable state-machine health ledgers for state-, person-, and program-level refresh decisions.
- `training_temporal_contracts`, `training_temporal_contract_rollups`: explicit next-run stale/transition contracts that define allowed automatic diff outcomes, review triggers, and evidence required to retain, advance, or complete training-state observations.
- `training_state_refresh_expectations`, `person_refresh_expectations`, `program_refresh_expectations`, `category_refresh_expectations`: queryable next-refresh expectation ledgers for missing, unchanged, advanced, stale, and review-required outcomes.
- `organizations`: resolved organization entities.
- `organization_aliases`: raw and curated aliases.
- `organization_identifiers`: external IDs.
- `person_training_events`: medical school, residency, undergraduate, graduate-school events.
- `career_events`: candidate current Penn attending and alumni/outcome events used for future trend reconciliation.
- `person_contacts`: public contact candidates with source, scope, verification status, confidence, and candidate status.
- `evidence_claims`: accepted and candidate claims for recursive enrichment.
- `evidence_reconciliation_decisions`: queryable item-level decision ledger for candidate evidence and career events.
- `person_reconciliation_decisions`: queryable person/name-level reconciliation burden and review-readiness rollup.
- `person_evidence_review_packets`: person/name-level packet ledger for review-ready or high-burden evidence reconciliation.
- `enrichment_acceptance_audit`: non-mutating acceptance assurance ledger that separates machine-acceptance candidates, review-ready evidence, secondary-anchor evidence, and low-signal discovery rows.
- `warehouse_reproducibility_audit`: artifact hash, size, Git-storage policy, and row-count parity ledger for proving that key flat files and SQLite tables agree.
- `source_utilities`: source taxonomy, default trust, claim types, limitations, and acceptance rules.
- `source_quality_observations`: empirical notes from enrichment runs.
- `source_utility_scorecard`: empirical utility scorecard tying each claim surface to observed input/output counts, review burden, blocker counts, quality band, and next action.

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
- `hup_gap_reason_audit.csv` / `.json`: deterministic reason ledger for every uncovered official program.
- `hup_gap_reason_summary.json`: counts by gap reason and recommended next action.
- `official_program_alias_reconciliation_candidates.csv` / `.json`: candidate relation rows for official gaps already represented by related loaded source URLs.
- `official_program_alias_reconciliation_summary.json`: counts by relation status and suggested mapping action.

This is deliberately separate from person scraping. A source crawler can find a program page without finding a usable roster, and a roster scraper can capture people without proving the full official denominator. Keeping both layers lets future runs show changes at several levels:

- person: new, missing, renamed, duplicated, advanced, regressed, stale, or reconciled.
- program: roster count changed, roster unavailable, official program added/removed, or program alias changed.
- institution/category: coverage changed across HUP, Penn Medicine, GME specialty family, residency, fellowship, or student populations.

The gap-source queue is also deliberately separate from person evidence. It lets the next scraper prioritize likely roster URLs, such as `current-residents`, `current-fellows`, `resident-profiles`, and `meet-our-fellow` pages, while keeping program overview pages and unreachable URLs out of the core person corpus until they yield named public trainees.

`scripts/scrape_penn_gme_gap_rosters.py` consumes only high-priority roster-source candidates and writes a separate `penn_gme_gap_roster_people.json` layer. It currently supports explicit page structures only: Penn Medicine bio cards, PSOM profile blocks, Penn Psychiatry resident profile cards, WordPress/Elementor heading-plus-name lists, and Dental accordion headers. Unsupported pages remain queued rather than becoming weak person claims.

The gap-roster scraper is refresh-conservative. If a later run has a transport-level fetch error for a URL that previously yielded public roster rows, the scraper preserves those prior rows and marks the source as `preserved_previous_records_after_refresh_error`. That prevents a temporary source outage from masquerading as 100 departed residents. The preserved rows are still subject to the training state machine: time can make them stale, but deletion or advancement requires the future evidence/review rules described below.

The source probe treats body-text mentions like “fellows rotate” as weak roster language unless the title or URL has a stronger current-roster cue such as `current fellows`, `current residents`, `meet our fellows`, `resident profiles`, or a roster/directory path. This prevents a program overview or faculty page from being mislabeled as a parser gap when no named current trainees are public on the page.

`scripts/audit_hup_gap_reasons.py` reads the official denominator, coverage audit, source probes, source candidates, and already-loaded source URLs. Its job is not to scrape new people. It classifies why each official uncovered program remains uncovered:

- `source_already_loaded_related_program_review`: the likely source URL is already represented by accepted people under a related program label, so the denominator/alias map needs review.
- `roster_source_candidate_needs_parser_or_manual_review`: a roster-like candidate URL exists but has not yielded accepted people for the official program.
- `official_page_empty_or_low_content`: the public official URL is reachable but effectively empty or too thin to support extraction.
- `public_program_context_no_current_roster`: public pages describe the program but do not expose current trainee roster structure.
- `candidate_sources_low_signal` or `not_discovered_by_current_strategy`: discovery needs to broaden before scraping should create person records.

This is the reconciliation layer between source discovery and roster extraction. It prevents the corpus from interpreting all remaining official gaps as equal and gives future agents a specific next action for each program.

`scripts/audit_official_program_alias_reconciliation.py` is a narrower non-mutating follow-up for `source_already_loaded_related_program_review` gaps. It compares the official denominator row to the loaded program label, role, source URL, and section/training-year labels. It can identify likely same-program aliases, section-level split candidates, track/type mismatches, combined-track-not-categorical cases, and weak related-source cases. None of these rows mutate official coverage by themselves; they make the mapping decision auditable before a later alias-map or program-splitting pass changes counts.

## Medical Student Source Coverage

The current public medical-student layer is intentionally partial. `scripts/scrape_penn_mstp_students.py` loads the official public MSTP student directory as current MD-PhD student evidence. `scripts/audit_penn_med_student_sources.py` separately audits whether broader Penn medical-student sources are public.

The audit probes official PSOM/MSTP pages and writes:

- `penn_med_student_source_audit.csv` / `.json`: source-level rows with URL, access status, capture status, public person-like count, loaded count, MD-PhD/directory signals, confidence, and evidence JSON.
- `penn_med_student_source_audit_summary.json`: rollups by access status, capture status, source scope, and recommended next action.
- SQLite table `medical_student_source_audit`: queryable version of the same source-access ledger.

The accepted finding is conservative: the public MSTP directory is a partial current-student truth anchor; the official MD-student directory is PennKey protected and should not be scraped; public graduate-program directories can cross-check or enrich MD-PhD students but should not expand the MD-student denominator because they overlap MSTP and broader PhD populations. This keeps “we do not have all MD students” as an evidence-backed source-access state rather than an accidental omission.

### External Program Identifiers

`scripts/discover_acgme_program_identifier_candidates.py` queries the public ACGME program search once for Pennsylvania and reconciles the returned code/specialty/name/city rows against the official Penn/HUP GME denominator. It stores the ACGME page response as a source observation with a content hash, then writes candidate rows rather than mutating program records.

`scripts/audit_program_identifier_reconciliation.py` is the acceptance gate. It writes `official_program_identifiers` only when a program has a single strong top ACGME candidate with no close competing Penn/UPHS facility, affiliate, or track sibling. Duplicate identifiers across multiple official program rows are demoted back to review, because they usually signal track or denominator ambiguity.

`scripts/audit_program_lifecycle_consistency.py` is the next gate. It does not infer duration from ACGME alone. Instead, it checks whether each accepted identifier also has current roster coverage and complete local training-state lifecycle mapping. Rows with no current roster validation, default/unknown duration rules, mixed uncoded state rows, or multiple lifecycle codes stay in review before any program-level annual roll-forward or diff mutation.

The current pass produces strong candidates when the ACGME specialty, Penn/UPHS naming, city, and inferred residency/fellowship family agree. It keeps duplicate UPHS facilities, combined programs, CHOP-affiliate rows, and broad specialty families in ambiguous or review states. Non-ACGME, selective, dental, and locally named programs can legitimately be `no_acgme_identifier_found`.

ACGME identifiers are useful for accreditation and lifecycle grounding, but they are not roster truth. Accepted identifiers can support program normalization; ambiguous/review/no-code rows remain evidence for source-quality and coverage work. They should be attached to canonical program/track records only after review confirms the local Penn program row maps to that ACGME row and not to a facility-specific sibling, combined track, or non-ACGME training offering.

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

`scripts/audit_reconciliation_decisions.py` turns that queue into a deterministic decision ledger:

- `evidence_reconciliation_decisions.csv`: one row per queued evidence item with decision, rationale, required next evidence, non-name anchor count, current-person name matches, and ten-year attending-trend window status.
- `person_reconciliation_decisions.csv`: person/name-level rollup of reconciliation burden and review-ready records.
- `evidence_reconciliation_decision_summary.json`: decision counts by record type, claim type, decision class, and ten-year trend window.

The ledger is deliberately not an acceptance mutator. `review_ready_high_anchor` and `review_ready_training_topic_anchor` mean a human or later verifier has enough non-name evidence to review efficiently; they do not change `evidence_claims.status`. PubMed author-query rows remain `discovery_only`. Current-attending and Penn-training-history profile claims are separated from accepted trend-line facts until a historical trainee identity or independent public anchor links them.

`scripts/audit_person_evidence_review_packets.py` rolls item-level decisions into packet rows:

- `person_evidence_review_packets.csv`: one row per person/name with packet status, review kind, top evidence URLs, claim types, match features, acceptance blocker, and recommended next action.
- `person_evidence_review_packets.json`: same rows with top evidence records in structured JSON.
- `person_evidence_review_packet_summary.json`: counts by packet status, review kind, and next action.

Packets are also non-mutating. They are the workbench between candidate evidence and accepted enrichment: a review-ready publication packet still needs author identity confirmation; an attending-trend packet still needs a historical roster, alumni page, CV, or independent profile bridge.

`scripts/audit_enrichment_acceptance.py` is the stricter acceptance-assurance gate after reconciliation decisions. It still does not mutate roster truth or flip `evidence_claims.status`. Its strictest publication tier, `machine_acceptance_candidate_cross_source`, requires a PubMed article candidate with `review_ready_high_anchor`, confidence at least 0.95, at least four non-name anchors, and an NPI secondary identity anchor for the same person. Other rows remain review-ready, secondary-anchor-needed, partial, endpoint-only, or low-signal with explicit blockers and next actions.

`scripts/audit_enrichment_coverage.py` turns the current evidence layers into person- and program-level coverage rows:

- `person_enrichment_coverage.csv`: one row per person with profile/headshot coverage, contact count, official training-event counts, seeded-vs-cleaned organization status, PubMed author/article candidate counts, career-event candidates, reconciliation queue burden, state-machine status, coverage score, and recommended next action.
- `program_enrichment_coverage.csv`: one row per program/role with profile/contact/background/research coverage rates, unresolved organization-review burden, reconciliation burden, and top next action.
- `enrichment_coverage_summary.json`: role, coverage-band, next-action, and overall coverage-rate counts.

The coverage score is not a truth score. A candidate PubMed article can improve coverage because there is something to reconcile, but it does not become accepted publication enrichment until a separate evidence-reconciliation pass proves identity anchors. The recommended action column is the recursive loop controller: search official profiles, resolve organization aliases, collect article-level research candidates, reconcile high-priority evidence, or monitor for the next refresh/diff.

`scripts/discover_trainee_official_profiles.py` is the profile-search collector for people without roster-linked profile URLs. It reads `official_profile_search` rows from `person_enrichment_work_queue`, emits a reproducible query manifest, and can optionally execute polite DuckDuckGo HTML searches and page probes. The committed baseline uses `--skip-search`, so it records 1,668 planned official-profile queries for 556 uncovered people without making rebuilds depend on a live search endpoint. When run with search enabled, it writes:

- `trainee_profile_search_queries.csv`: person/program/query manifest.
- `trainee_profile_search_observations.csv`: search HTTP status, result count, and error evidence.
- `trainee_profile_discovery_candidates.csv`: URL candidates with official-domain/profile-path/name/program features.
- `trainee_profile_discovery_claims.json`: candidate `official_profile_url_candidate` evidence for the reconciliation queue.

Profile discovery does not mutate roster truth. Search hits are useful identity and enrichment candidates, but they need official ownership, same-person identity, and current trainee/program context before becoming accepted profile enrichment.

## Attending Trend Evidence

Current Penn attending/faculty pages and official Penn provider/profile pages are loaded as career-event evidence, not as trainee roster truth. `scripts/enrich_penn_attending_profiles.py` follows profile URLs from current attending candidates and extracts only conservative official-profile claims:

- structured provider-page Medical School, Residency, and Fellowship fields.
- department biography sentences with explicit Penn/HUP training language.
- research-interest and personal-profile sentences when the profile page publishes them directly.

Penn training-history claims from current attending profiles are `needs_review`, not accepted. They are useful for the ten-year trend line only after reconciliation links the current attending identity to a prior Penn trainee record or another independent public anchor.

`scripts/audit_attending_trend_linkage.py` turns those career events into an explicit trend-link assurance ledger:

- `attending_trend_linkage_events.csv`: every career event with normalized event-group key, ten-year-window flag, linkage status, assurance level, current-trainee name-match count, reconciliation-decision context, and required next evidence.
- `attending_trend_linkage_groups.csv`: one row per attending/source group, showing whether the group has a current Penn attending endpoint, Penn-training profile claim, current-trainee name match, event years, source URLs, and best linkage status.
- `attending_trend_linkage_summary.json`: machine-readable counts by event type, linkage status, ten-year window, and assurance level.

The assurance ledger is deliberately not an accepted trend table. A current Penn attending endpoint plus a same-name Penn-training profile claim is still only a candidate until a dated historical roster, alumni page, CV, or independent profile links that attending identity to a Penn trainee record. This prevents the trend layer from turning current faculty pages into alumni-flow evidence without a real identity bridge.

`scripts/discover_attending_historical_links.py` is the next recursive loop for those assurance gaps. It reads the trend-linkage groups, seeds already-known official Penn/provider URLs, optionally runs polite broad web search queries, probes candidate pages, and writes:

- `attending_historical_link_candidates.csv`: source candidates with query/source provenance, probe status, content hash, term-hit labels, candidate status, confidence, priority, and required next evidence.
- `attending_historical_link_search_queries.csv`: deterministic query plan for historical roster, alumni, profile, CV, and Penn-training searches.
- `attending_historical_link_search_observations.csv`: search-endpoint observations, including rate-limit or non-200 behavior.
- `attending_historical_link_discovery_summary.json`: counts by candidate status, query kind, result domain, searched group, and seeded/search rows.

The seeded mode is intentionally reproducible and uses only already-known official source URLs. Broad search is useful, but it is a source utility with availability constraints; non-200, throttled, or empty search responses are recorded as source-quality evidence rather than silently treated as no historical evidence.

Historical-link candidates are also classified by source surface. Current Penn provider or faculty pages can remain useful profile/training context, but they are not accepted as historical trainee bridges unless a dated roster, alumni page, CV, or independent profile source supplies same-person Penn-training evidence.

`scripts/audit_attending_biosketch_bridges.py` adds a narrower official-profile bridge utility. It uses the Penn Faculty Biosketch index for current-attending groups that already have Penn-training claims, fetches matched official biosketches, and extracts dated post-graduate training lines. Recent dated Penn residency/fellowship lines become `dated_recent_official_biosketch_training_bridge_candidate`; non-Penn lines stay background; Penn postdoctoral research lines are retained as research-training context rather than GME trainee-flow evidence.

This bridge audit is still non-mutating. A faculty biosketch is much stronger than a search result because it is official, dated, and profile-attached, but it is still not the same source class as a historical roster or alumni record. The trend layer should treat it as review-ready bridge evidence until the reconciliation policy explicitly accepts official biosketch training lines as sufficient for a given trend analysis.

`scripts/audit_attending_trend_reconciliation.py` is the policy ledger above those source utilities. It joins trend-linkage groups, official biosketch bridge candidates, and historical-link candidates into `attending_trend_reconciliation.csv` and SQLite table `attending_trend_reconciliation`. The ledger classifies groups as review-ready official-biosketch bridges, profile claims still needing a dated bridge, endpoints needing Penn-training evidence, or context-only rows.

This table is the right place to build the ten-year recent-attending trend line. It is deliberately still non-mutating: `review_ready_official_biosketch_bridge` means endpoint evidence, Penn-training claim, and dated recent official Penn GME biosketch evidence agree enough for explicit reviewer acceptance. It does not rewrite the current trainee roster or promote profile claims into accepted trend facts by itself.

## Trainee Background Discovery

Official trainee profile and prior-training background discovery are queue-driven lanes, not default rebuild steps. The committed warehouse stores deterministic no-network manifests so a local rebuild can verify the queue without depending on search-engine availability.

`scripts/discover_trainee_official_profiles.py` searches for missing official profile URLs and profile-context pages. It writes query, observation, candidate, source, claim, and summary artifacts. Discovered URLs can support profile, education, prior-training, research-interest, career-interest, and personal-context candidates, but they do not mutate roster truth unless same-person/current-trainee context is confirmed through a current official roster link or reviewer-accepted evidence.

`scripts/discover_prior_training_background.py` covers the narrower background gap for medical-school and prior-residency history. It reads `source_medical_school_background` and `source_residency_background` tasks from `person_enrichment_work_queue`, materializes deterministic search queries, and can optionally run/probe public search results into:

- `prior_training_search_queries.csv`
- `prior_training_search_observations.csv`
- `prior_training_discovery_candidates.csv`
- `prior_training_discovery_claims.json`
- `prior_training_discovery_sources.json`
- `prior_training_discovery_summary.json`

This lane is intentionally candidate-only. Prior education and previous GME facts are high-value enrichment fields, but they are also name-collision and staleness prone because they often come from old biosketches, article affiliations, residency newsletters, alumni pages, or scraped profile mirrors. Reconciliation should accept them only with corroborating same-person anchors such as official trainee profile context, dated institutional profile text, CV/biosketch lines, stable program affiliation, or reviewer acceptance.

The current readiness ledger now treats profile, research, and prior-training discovery as collector-backed queue lanes. That means the next improvement loop is execution and reconciliation quality, not building another parser skeleton: run candidate collection, inspect hit quality by source utility, promote only evidence-backed claims, then rerun the queue to see which tasks remain unresolved.

## First Research Utility Learnings

The first expanded resident/fellow research pass processed 759 Penn-affiliated resident/fellow people from official Penn roster sources.

- PubMed E-utilities generated 759 author-query candidates with zero rejected API errors after retry cleanup. It is useful for discovery, but author-query counts alone are weak evidence because common names collide heavily.
- PubMed article-level reconciliation now fetches PubMed XML for bounded author-query candidates and stores per-article candidates with target-author, affiliation, topic, and recency features. This is stronger than count evidence but still not accepted automatically.
- OpenAlex author search is implemented, retryable, and resumable, but the latest full-corpus run hit sustained 429 throttling. The current warehouse records this as a source-quality observation rather than as rejected person evidence.
- No research claims were accepted automatically.

The current acceptance rule is deliberately strict: accept research enrichment only when at least two non-name anchors agree, such as official profile link plus ORCID, OpenAlex Penn affiliation plus specialty-topic match, PubMed affiliation plus coauthor cluster, or NPI specialty/location plus official profile.

`scripts/collect_npi_candidates.py` implements the NPPES/NPI lane as candidate-only identity enrichment for current residents and fellows. It queries the official NPPES API with exact first/last name and a PA state filter, stores query observations separately from candidate rows, and scores features such as exact name match, PA/Philadelphia practice location, physician or student-training taxonomy, and program-taxonomy topic overlap.

NPI candidates do not mutate roster truth. They are useful secondary identity anchors for profile/publication/trend reconciliation, especially when location and taxonomy agree, but NPPES can be stale, sparse, or name-colliding for residents and fellows. The accepted person/program source remains the official trainee roster.

`scripts/audit_source_utility_scorecard.py` turns those observations into an operational scorecard:

- `source_utility_scorecard.csv` / `.json`: one row per utility surface, including official roster truth, official denominator coverage, ACGME program identifiers, gap-roster extraction, Penn-wide source discovery, PubMed author discovery, PubMed article reconciliation, OpenAlex, attending profiles, faculty-biosketch bridge evidence, historical-link discovery, public contacts, organization normalization, and training state-machine readiness.
- `source_utility_scorecard_summary.json`: counts by quality band, source family, and recommended next action.
- SQLite table `source_utility_scorecard`: queryable version of the same ledger.

The scorecard is not an acceptance mutator. It answers which utility is good for which job. Current observations classify official rosters as high-utility current-membership anchors; official denominator coverage as strong but alias-sensitive; ACGME public search as strong for candidate program codes but not trainee truth; broad source discovery as a queue, not truth; official trainee profile discovery as a resumable query/probe lane; PubMed author-query rows as discovery only; PubMed article candidates as reviewable only after non-name anchors; OpenAlex as blocked in the latest full-corpus pass by rate limiting; attending profiles as endpoint/training-history candidates needing historical identity bridges; and the state machine as the freshness layer that decides when stale, missing, unchanged, or advanced rows are expected.

## Public Contact Evidence

The current warehouse stores 313 public email candidates:

- 205 from the official public Penn MSTP student directory.
- 53 from official Medicine roster pages.
- 21 from official HUP gap roster pages.
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

The state machine is intentionally evidence-preserving. Time can make an observation stale, but time alone should not overwrite the person row. A PGY-2 internal-medicine resident can be projected as an expected PGY-3 candidate after the July rollover only if the same person/program is freshly observed or the later snapshot supplies compatible evidence. If the person disappears after a terminal-year stale date, the transition can be classified as expected completion; if they disappear early, stay in the same stage after the expected transition, regress, or move outside the nominal program duration, the transition ledger marks the row for review.

Durable snapshots live under `artifacts/data/training_state_snapshots/`, and SQLite stores both `training_state_snapshot_rows` and `training_state_transition_events`. That is the longitudinal layer for future national-scale diffs: individual flows, program roster movement, institution-level coverage changes, category rollups, and stale-versus-surprising change classification all derive from the same canonical person/program state keys.

The latest snapshot loop demonstrates the intended behavior: adding the official Penn Psychiatry PGY class pages created a new deterministic snapshot and classified 52 added person/program observations against the previous baseline. The previous baseline remains in `training_state_snapshots/`, so future runs can compare against either the immediate prior snapshot or a chosen historical snapshot without treating a flat file as informal memory.

`scripts/diff_training_states.py` compares exported state snapshots. It collapses multiple raw observations for the same person/program into a canonical comparison key and reports how many duplicate keys were collapsed, so the diff view stays readable while the warehouse still preserves raw state observations. It also writes rollups by program, role, lifecycle code, and change type for program-, category-, and institution-level monitoring.

`scripts/materialize_training_state_snapshot.py` is the durable version of that diff flow. It stores snapshot manifests and CSVs under `artifacts/data/training_state_snapshots/`, reloads them into SQLite, and emits `training_state_transition_events.csv` from the queryable `training_state_transition_events` table. That makes next-year reruns stateful in a verifiable way: the corpus can show what changed at person, program, and category levels without treating last year's flat file as informal memory.

`scripts/audit_training_state_machine.py` audits the current snapshot before a future diff exists. It writes:

- `training_state_machine_audit.csv`: every state observation with a clock model, machine status, days until expected transition, days until stale, and recommended action.
- `person_training_state_machine_audit.csv`: one row per person summarizing the worst current lifecycle/staleness condition and duplicate person/program state keys.
- `program_training_state_machine_audit.csv`: one row per program/role summarizing lifecycle codes, clock models, stale/review counts, and next action.
- `training_state_machine_summary.json`: machine-readable status, role, lifecycle, clock, and action counts.

`scripts/audit_longitudinal_change_readiness.py` projects the same current-state observations into next-refresh semantics. For a target refresh date, it writes:

- `training_state_refresh_expectations.csv`: every state observation with expected behavior if the next run finds the person missing, unchanged, or advanced.
- `person_refresh_expectations.csv`: per-person rollup of expected advancement, completion, source-refresh, and human-review windows.
- `program_refresh_expectations.csv`: per-program/role rollup, including the current official HUP coverage status when available.
- `category_refresh_expectations.csv`: trainee-category rollup for resident/fellow/student monitoring.
- `longitudinal_change_readiness_summary.json`: machine-readable readiness counts and artifact paths.

The audit categories are intentionally operational:

- `annual_clock_active`: PGY/CY/fellowship-year rows with a future expected next date.
- `terminal_year_active`: final-year rows that can disappear after stale-after as expected completion.
- `source_refresh_required`: rows whose next state is not safely inferable, such as MSTP PhD phase, unknown fellow year, research/lab year, chief year, or source-ambiguous current resident/fellow labels.
- `review_required`: rows outside nominal lifecycle assumptions, such as PGY4 in a three-year residency rule.
- `ready_for_expected_advancement`: annual-clock rows past expected next date but not yet stale.
- `stale_now`: rows past stale-after date.

That gives yearly runs a stable decision surface. A PGY-2 row in a three-year residency can become an expected advancement candidate around July 1; a second-year fellow in a two-year fellowship can become a terminal completion candidate; an MSTP PhD-phase row remains refresh-required because the individualized duration is not inferable from the label. The stale bit is therefore derived from the state machine, not from how old a CSV file feels.

`scripts/materialize_training_temporal_contracts.py` turns that decision surface into an explicit contract ledger:

- `training_temporal_contracts.csv`: one row per current state observation with a canonical person/program key, current temporal state code, temporal validity status, next-refresh contract, allowed automatic diff outcomes, review triggers, stale policy, and evidence required to retain, advance, or complete the row.
- `training_temporal_contract_rollups.csv`: rollups by corpus, institution, country, role, trainee category, program, program-role, institution-role, lifecycle code, current temporal state, next-refresh contract, and diff-readiness status.
- `training_temporal_contract_summary.json`: machine-readable counts for guardrail status, next-refresh contract type, stale-by-refresh burden, source-refresh burden, and review-bound burden.

This is the answer to the “when is it stale?” problem. A row can be stale without being false, and an expected transition can be known without being accepted. The contract says which future evidence permits a mutation and which future evidence must be routed to review. That lets later refreshes produce diff views at individual, program, institution, category, and eventually national scopes without losing the provenance of the original observation.

The intended freshness semantics are:

- Expected advancement: PGY/CY/fellowship-year and MS-year labels can advance on their academic clocks if the same person/program remains observed.
- Expected completion: terminal-year observations can disappear after their stale-after date without being treated as a scraper miss.
- Source refresh required: PhD phase, lab/research residents, postdoc fellows, chief residents, unknown-year fellows/residents, and public contact channels become stale unless a fresh public source repeats or updates them.
- Surprising change: disappearance before an expected end date, program-family change, regression in normalized stage, or conflicting concurrent stage labels should become review items, not automatic mutations.
- Denominator change: official program-universe additions/removals should be separated from person-level roster movement so an annual diff can tell the difference between “program disappeared from Penn’s public list” and “our scraper missed the page.”

The readiness layer is the bridge between current-state audit and future two-snapshot diffs. It makes the next run pre-explainable: a missing terminal-year fellow can be classified as expected completion, an unchanged PGY row after July can require a fresh-source check, and a source-dependent MSTP or research state can be retained only when the public source repeats it.

## Next Programs

After Penn, good next targets are:

- Johns Hopkins: strong peer benchmark with rich cardiology/internal medicine context.
- UCSF: different web stack and strong research-profile enrichment surface.
- Mass General Brigham / Harvard programs: intentionally hard normalization case because school, hospital, health-system, and program identity diverge.

Those three will stress the resolver better than adding three Penn-like sites.
