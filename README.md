# redmank

`redmank` is a public-source research corpus for understanding medicine training programs, starting with Penn Medicine and the Perelman School of Medicine.

The first case study focuses on Penn Department of Medicine residents and fellows, with a separate partial medical-student source from the public Penn MSTP directory. The project keeps provenance close to each record: source URL, source type, extraction method, role, program, population, training-year label, current-status inference, and quality notes.

## Current Penn Outputs

- `artifacts/data/penn_training_people_unique.json`: deduplicated Department of Medicine resident/fellow corpus.
- `artifacts/data/penn_training_people_unique.csv`: spreadsheet-friendly version of the same corpus.
- `artifacts/data/penn_profile_index.md`: human review index for the resident/fellow corpus.
- `artifacts/data/penn_training_summary.json`: counts and field coverage for the resident/fellow corpus.
- `artifacts/data/penn_source_discovery.json`: crawler-based review list of candidate Penn Department of Medicine training pages.
- `artifacts/data/penn_mstp_students.json`: separate public MSTP student-directory extract.
- `artifacts/data/redmank.sqlite`: SQLite warehouse built from the generated artifacts.
- SQLite tables `official_program_universe` and `official_program_coverage_audit`: queryable official-program denominator and coverage status.
- `artifacts/data/warehouse_summary.json`: warehouse table counts and resolver status counts.
- `artifacts/data/organization_review_queue.csv`: organization labels that need alias/identifier review.
- `artifacts/data/person_enrichment_queue.csv`: per-person recursive enrichment tasks.
- `artifacts/data/penn_affiliated_source_discovery.json`: Penn-wide source discovery for trainee, alumni/outcome, and attending/faculty candidates.
- `artifacts/data/penn_gme_program_universe.json`: official HUP GME program denominator parsed from the public Penn Medicine program list.
- `artifacts/data/penn_gme_program_coverage.csv`: coverage audit mapping official HUP programs to current captured rosters, discovered pages without roster capture, and undiscovered gaps.
- `artifacts/data/penn_gme_gap_source_candidates.csv`: prioritized source queue for official HUP programs without captured current roster people.
- `artifacts/data/penn_gme_gap_source_probes.json`: reachability and page-signal observations for uncovered official HUP program URLs.
- `artifacts/data/hup_gap_reason_audit.csv`: deterministic reason ledger for remaining official HUP coverage gaps.
- `artifacts/data/hup_gap_reason_summary.json`: gap-reason counts and recommended next-action counts.
- `artifacts/data/official_program_alias_reconciliation_candidates.csv`: non-mutating candidate ledger for official denominator rows that may map to related loaded program labels.
- `artifacts/data/official_program_alias_reconciliation_summary.json`: alias/denominator reconciliation candidate counts.
- `artifacts/data/penn_gme_gap_roster_people.json`: conservative queue-driven roster extract from supported HUP gap pages.
- `artifacts/data/penn_gme_gap_roster_sources.json`: source provenance and extraction status for queue-driven HUP gap roster pages.
- `artifacts/data/penn_attending_candidates.json`: conservative current Penn attending/faculty candidate layer for future career-trend reconciliation.
- `artifacts/data/penn_attending_profile_claims.json`: official Penn profile-derived attending education/training/research/personal-profile candidate claims.
- `artifacts/data/penn_outcome_candidates.json`: source-level alumni/outcome context claims.
- `artifacts/data/evidence_claims.csv`: accepted and candidate evidence claims.
- `artifacts/data/evidence_reconciliation_queue.csv`: ranked review queue for candidate evidence and career-event reconciliation.
- `artifacts/data/evidence_reconciliation_decisions.csv`: deterministic decision ledger for queued evidence, separating review-ready, discovery-only, secondary-anchor-needed, and attending-trend candidates.
- `artifacts/data/person_reconciliation_decisions.csv`: person/name-level reconciliation decision rollup.
- `artifacts/data/attending_trend_linkage_events.csv`: event-level assurance audit for whether attending/faculty/outcome evidence can support a Penn-trainee trend link.
- `artifacts/data/attending_trend_linkage_groups.csv`: person/source-group rollup for recent-attending trend linkage candidates.
- `artifacts/data/attending_historical_link_candidates.csv`: seeded/search-discovered source candidates that may bridge current Penn attending endpoints to dated historical trainee records.
- `artifacts/data/attending_historical_link_search_queries.csv`: deterministic web-search query plan for attending trend identity linkage.
- `artifacts/data/person_enrichment_coverage.csv`: per-person coverage audit across profile, program, training, contact, research, career-event, reconciliation, and state-machine layers.
- `artifacts/data/program_enrichment_coverage.csv`: per-program/role enrichment coverage rollup and next-action summary.
- `artifacts/data/research_candidate_claims.json`: durable replay artifact for candidate-only scholarly enrichment claims.
- `artifacts/data/pubmed_article_candidate_claims.json`: article-level PubMed candidates with author, affiliation, topic, and recency features.
- `artifacts/data/training_states_current.csv`: normalized person/program training state observations with transition and staleness dates.
- `artifacts/data/training_state_machine_audit.csv`: per-state lifecycle/staleness audit classifying annual-clock, terminal-year, source-refresh, and review-required rows.
- `artifacts/data/person_training_state_machine_audit.csv`: per-person rollup of state-machine health and next action.
- `artifacts/data/program_training_state_machine_audit.csv`: per-program/role rollup for annual refresh and national-scale diff views.
- `artifacts/data/training_state_refresh_expectations.csv`: projected next-refresh expectations for whether each state should advance, complete, refresh from source, or require review.
- `artifacts/data/person_refresh_expectations.csv`: per-person longitudinal readiness rollup for future diff/reconciliation runs.
- `artifacts/data/program_refresh_expectations.csv`: per-program/role longitudinal readiness rollup.
- `artifacts/data/category_refresh_expectations.csv`: resident/fellow/student category rollup for institution-level monitoring.
- `artifacts/data/training_state_snapshots/`: durable snapshot CSV/manifest files for longitudinal reruns.
- `artifacts/data/training_state_transition_events.csv`: SQLite-backed transition ledger for the latest materialized snapshot comparison.
- `artifacts/data/training_state_snapshot_summary.json`: snapshot and transition counts for the current materialized state.
- `config/training_lifecycle_rules.json`: local lifecycle codes and nominal-duration rules used to interpret trainee stages over time.
- `artifacts/data/person_contacts.csv`: public person/contact candidates with source, scope, verification status, confidence, and candidate status.
- `artifacts/data/career_events.csv`: current Penn attending and alumni/outcome candidate events.
- `artifacts/data/source_quality_report.json`: machine-readable source utility observations and feature distributions.
- `artifacts/research/penn-source-quality-learnings-2026-06-02.md`: first source-quality learning report.
- `artifacts/research/`: methodology and tradeoff briefs.

As of the latest local generation, the warehouse has 1,483 people: 873 residents, 385 fellows, and 225 public MSTP student-directory records. It also has 1,775 accepted roster/training event rows, 1,111 PubMed author-query research candidates, 313 public contact candidates, and 105 career/outcome candidate events. The Department of Medicine subset remains the highest-confidence starting corpus; the broader Penn-affiliated and HUP gap-queue scrapes add conservative non-Medicine resident/fellow rosters from official Penn pages and mark them for review.

The official HUP GME coverage audit currently parses 91 public HUP programs: 64 have captured current roster people, 12 are discovered as program/source pages without current roster capture, and 15 are not yet discovered by the current Penn-wide crawl.

The HUP gap-source probe currently inspects the 27 official programs without captured roster people and queues 72 candidate URLs, including 15 roster-source candidates, for the next scraper pass. The queue-driven HUP gap roster scraper currently retains 524 conservative person records from 27 official public sources with extracted records.

## Reproduce

Install dependencies:

```bash
python3 -m pip install --target /tmp/penn_corpus_deps -r requirements.txt
```

Run the resident/fellow corpus:

```bash
python3 scripts/scrape_penn_training.py
```

Run Penn Department of Medicine source discovery:

```bash
python3 scripts/discover_penn_training_sources.py
```

Run the separate public MSTP student extract:

```bash
python3 scripts/scrape_penn_mstp_students.py
```

Build the SQLite warehouse and review queues:

```bash
python3 scripts/build_sqlite.py
python3 scripts/generate_enrichment_queue.py
```

Run Penn-wide source discovery and first-pass research candidate collection:

```bash
python3 scripts/discover_penn_affiliated_sources.py
python3 scripts/scrape_penn_affiliated_rosters.py
python3 scripts/scrape_penn_attending_candidates.py
python3 scripts/enrich_penn_attending_profiles.py
python3 scripts/extract_penn_outcome_candidates.py
python3 scripts/build_sqlite.py
python3 scripts/audit_penn_gme_program_coverage.py
python3 scripts/probe_penn_gme_gap_sources.py
python3 scripts/scrape_penn_gme_gap_rosters.py
python3 scripts/build_sqlite.py
python3 scripts/audit_penn_gme_program_coverage.py
python3 scripts/probe_penn_gme_gap_sources.py
python3 scripts/scrape_penn_gme_gap_rosters.py
python3 scripts/build_sqlite.py
python3 scripts/audit_penn_gme_program_coverage.py
python3 scripts/audit_hup_gap_reasons.py
python3 scripts/audit_official_program_alias_reconciliation.py
python3 scripts/generate_enrichment_queue.py
python3 scripts/collect_research_candidates.py --only pubmed --skip-existing-source pubmed_eutilities --sleep 0.34
python3 scripts/collect_pubmed_article_candidates.py --sleep 0.34 --batch-size 100
python3 scripts/build_sqlite.py
python3 scripts/export_warehouse_views.py
python3 scripts/materialize_training_state_snapshot.py --compare-date 2026-06-02
python3 scripts/audit_training_state_machine.py
python3 scripts/audit_longitudinal_change_readiness.py --refresh-date 2027-08-15
python3 scripts/audit_enrichment_coverage.py
python3 scripts/audit_reconciliation_decisions.py --as-of-year 2026
python3 scripts/audit_attending_trend_linkage.py --as-of-year 2026
python3 scripts/discover_attending_historical_links.py --max-groups 4 --probe-pages --skip-search --sleep 0.1
python3 scripts/report_source_quality.py
python3 scripts/summarize_warehouse.py
```

OpenAlex author search is implemented as a candidate utility, but the latest full-corpus run hit sustained OpenAlex 429 throttling. Keep it as a resumable/polite enrichment lane rather than a default blocking rebuild step:

```bash
python3 scripts/collect_research_candidates.py --only openalex --skip-existing-source openalex_author_search --sleep 0.5
```

Broad web search for attending historical-link discovery is also optional. The default reproducible pass can use seeded official Penn/provider URLs with `--skip-search`; remove that flag only for a polite, rate-limit-aware discovery run.

Validate scripts:

```bash
python3 -m py_compile scripts/*.py
```

Compare two annual state exports:

```bash
python3 scripts/diff_training_states.py \
  --old path/to/previous/training_states_current.csv \
  --new artifacts/data/training_states_current.csv
```

The diff writes both person-level changes and `artifacts/data/training_state_diff_rollups.csv`, grouped by program, role, lifecycle code, and change type.

Materialize a durable state snapshot:

```bash
python3 scripts/materialize_training_state_snapshot.py --compare-date 2026-06-02
```

The materializer writes `artifacts/data/training_state_snapshots/<snapshot_id>.csv` plus a JSON manifest, reloads every committed snapshot into SQLite, and writes transition events for the current snapshot against the previous one when present. The first snapshot is a baseline where all canonical person/program rows are `added`; later snapshots classify expected advancement, expected completion disappearance, unchanged states, stale removals, regressions, and review-required stage changes.

Audit the current state-machine readiness:

```bash
python3 scripts/audit_training_state_machine.py --as-of-date 2026-06-02
```

The audit writes state-, person-, and program-level CSVs plus `artifacts/data/training_state_machine_summary.json`. It distinguishes annual-clock rows that can advance after their expected date from source-refresh rows that should never be guessed forward, such as MSTP PhD phase, unknown fellow year, research/lab year, and other individualized states.

Project expected refresh behavior:

```bash
python3 scripts/audit_longitudinal_change_readiness.py --refresh-date 2027-08-15
```

The readiness audit writes state-, person-, program-, and category-level CSVs plus `artifacts/data/longitudinal_change_readiness_summary.json`. It describes how the next refresh should interpret missing, unchanged, or advanced rows before mutating the person table: expected completion, expected advancement, source-refresh-required, human-review-required, or no-change-expected.

## Data Policy

This project uses public web sources only. It does not bypass login walls, private directories, robots exclusions, or application-only systems. Public institutional contact channels may be stored only as structured contact candidates with source URL, scope, verification status, confidence, and candidate status; raw HTML remains redacted and ignored by Git. Records should retain source URLs and quality notes so downstream users can distinguish official roster facts from inferred categorization and enrichment candidates.

## Method

The initial methodology is conservative:

- Prefer official program roster pages over search snippets or secondary profiles.
- Store source metadata, including HTTP status and content hash. Redacted raw snapshots can be regenerated locally but are ignored by Git.
- Deduplicate by normalized person name with manual aliases only when the same public corpus shows the variant.
- Keep track and fellowship memberships as multi-valued fields instead of forcing one person into one category.
- Infer broad Penn program names from page URL plus section heading when official roster page titles are generic, because pages like Radiology fellows contain multiple programs on one source page.
- Normalize training labels into state observations with transition rules and stale-after dates so future runs can distinguish expected annual advancement from surprising changes.
- Attach conservative lifecycle semantics to state observations so PGY/fellowship-year labels can be interpreted as annual advancement, terminal completion, unknown-duration refresh, or review-required states.
- Project state observations into refresh expectations so future annual runs can produce person-, program-, and category-level diffs with expected-vs-surprising change semantics.
- Classify official denominator gaps by evidence-backed reason before treating them as missing people: context-only public page, parser/manual-review candidate, low-content official page, related-program alias review, or broader-discovery-needed.
- Keep official-program alias/denominator reconciliation as a candidate ledger until the relation is strong enough to mutate coverage or split a loaded broad program into a narrower official program.
- Separate resident/fellow rosters, context-only program pages, alumni/former pages, and partial student directories.
- Store public contact channels as provenance-backed contact evidence, not as unqualified person identity fields.
- Treat publication, grant, trial, NPI, and social-web enrichment as separate evidence layers requiring identity-resolution confidence, not as roster truth.
- Rank candidate enrichment in an evidence reconciliation queue before accepting profile, publication, or attending-trend claims.
- Keep current-attending endpoints separate from accepted trend-line links until a historical roster, alumni page, CV, or independent profile connects the attending identity to a dated Penn trainee record.
- Resolve school/hospital/program labels into organization rows with raw values, aliases, identifiers, and review status instead of overwriting source strings.
- Keep scholarly API results as candidate evidence until reconciliation supplies enough non-name anchors.

See the latest research brief in `artifacts/research/` for source coverage, quality grades, and recommended enrichment tiers.
