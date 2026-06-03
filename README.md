# redmank

`redmank` is a public-source research corpus for understanding medicine training programs, starting with Penn Medicine and the Perelman School of Medicine.

The first case study focuses on Penn Department of Medicine residents and fellows, with a separate partial medical-student source from the public Penn MSTP directory. The project keeps provenance close to each record: source URL, source type, extraction method, role, program, population, training-year label, current-status inference, and quality notes.

## Current Penn Outputs

- `artifacts/data/penn_training_people_unique.json`: deduplicated Department of Medicine resident/fellow corpus.
- `artifacts/data/penn_training_people_unique.csv`: spreadsheet-friendly version of the same corpus.
- `artifacts/data/penn_profile_index.md`: human review index for the resident/fellow corpus.
- `artifacts/data/penn_trainee_profile_claims.json`: roster-linked official trainee profile URL, education, prior-training, interest, and personal-context candidate claims.
- `artifacts/data/penn_trainee_profile_claims.csv`: spreadsheet-friendly profile-claim export.
- `artifacts/data/penn_trainee_profile_sources.json`: official trainee profile source rows with fetch status and content hash.
- `artifacts/data/penn_trainee_profile_summary.json`: profile extraction counts by claim type, role, status, and display-safety class.
- `artifacts/data/penn_training_summary.json`: counts and field coverage for the resident/fellow corpus.
- `artifacts/data/penn_source_discovery.json`: crawler-based review list of candidate Penn Department of Medicine training pages.
- `artifacts/data/penn_mstp_students.json`: separate public MSTP student-directory extract.
- `artifacts/data/penn_med_student_source_audit.csv`: source-access audit for public MSTP, protected MD-student directory, MD Program context, and MD-PhD graduate-directory cross-checks.
- `artifacts/data/penn_med_student_source_audit_summary.json`: student-source access and capture-status counts.
- `artifacts/data/redmank.sqlite`: local generated SQLite warehouse built from the committed artifacts; ignored by Git once generated.
- `artifacts/data/redmank_sqlite_manifest.json`: committed manifest for the local SQLite warehouse hash, size, storage policy, and validation commands.
- SQLite tables `official_program_universe` and `official_program_coverage_audit`: queryable official-program denominator and coverage status.
- `artifacts/data/warehouse_summary.json`: warehouse table counts and resolver status counts.
- `artifacts/data/organization_review_queue.csv`: organization labels that need alias/identifier review.
- `artifacts/data/organization_identifier_candidates.csv`: non-mutating ROR identifier candidates for high-mention cleaned organization labels.
- `artifacts/data/organization_identifier_source_observations.csv`: ROR query/probe observations, including errors and result counts.
- `artifacts/data/organization_identifier_candidate_summary.json`: organization identifier candidate counts by status, category, and identifier type.
- `artifacts/data/program_identifier_candidates.csv`: non-mutating ACGME program-code candidates for official Penn/HUP GME denominator programs.
- `artifacts/data/program_identifier_source_observations.csv`: ACGME public-search query observation with result counts and content hash.
- `artifacts/data/program_identifier_candidate_summary.json`: ACGME identifier candidate counts by status and program type.
- `artifacts/data/program_identifier_reconciliation.csv`: ACGME candidate reconciliation ledger separating accepted identifiers from facility/track/affiliate review states.
- `artifacts/data/official_program_identifiers.csv`: accepted external program identifiers for unambiguous official Penn/HUP program rows.
- `artifacts/data/program_lifecycle_consistency_audit.csv`: accepted-identifier audit for whether current roster coverage and lifecycle rules support program-level state-machine rollups.
- `artifacts/data/program_lifecycle_consistency_summary.json`: lifecycle-consistency counts for accepted program identifiers, including unvalidated, unknown-duration, mixed-missing, and consistent rows.
- `artifacts/data/program_lifecycle_duration_source_observations.csv`: official Penn program-page fetch observations for accepted ACGME-linked programs still blocked by default/unknown lifecycle rules.
- `artifacts/data/program_lifecycle_duration_evidence.csv`: non-mutating duration-evidence reconciliation rows separating reviewer-ready lifecycle candidates from source mismatches, conflicting context, and no-explicit-duration pages.
- `artifacts/data/program_lifecycle_duration_evidence_summary.json`: duration-evidence counts by status, explicit years, source status, and recommended action.
- `artifacts/data/program_lifecycle_duration_reviewer_decision_queue.csv`: reviewer-decision queue for duration evidence, including evidence fingerprints and required confirmation fields.
- `artifacts/data/program_lifecycle_duration_reviewer_decisions.csv`: manual reviewer decision input file for accepting/rejecting lifecycle-duration mappings.
- `artifacts/data/program_lifecycle_duration_reviewer_decision_audit.csv`: audit of manual lifecycle-duration decisions against the current evidence fingerprint and confirmation requirements.
- `artifacts/data/accepted_program_lifecycle_duration_mappings.csv`: accepted public-source-backed duration mappings; still non-mutating for `config/training_lifecycle_rules.json`.
- `artifacts/data/program_lifecycle_duration_reviewer_decision_summary.json`: duration-decision queue, pending, rejected/deferred, and accepted-mapping counts.
- `artifacts/data/person_enrichment_queue.csv`: source-aware recursive enrichment work queue for residents, fellows, and medical students, including state-machine urgency, priority band, query, source targets, acceptance rule, recency policy, provenance policy, and blocking risk.
- `artifacts/data/person_enrichment_queue_summary.json`: queue rollups by role, task type, source family, priority band, and lifecycle policy lane.
- `artifacts/data/person_enrichment_execution_readiness.csv`: per-task execution-readiness ledger mapping queued enrichment work to existing collectors, command hints, network/review/script-extension/parser requirements, and next system action.
- `artifacts/data/person_enrichment_execution_readiness_rollups.csv`: rollups by task type, source family, execution lane, automation status, priority band, and task-type/execution-lane pair.
- `artifacts/data/person_enrichment_execution_readiness_summary.json`: one-glance counts for runnable collector lanes, manual-review burden, script-extension gaps, and new-parser gaps.
- `artifacts/data/penn_affiliated_source_discovery.json`: Penn-wide source discovery for trainee, alumni/outcome, and attending/faculty candidates.
- `artifacts/data/penn_gme_program_universe.json`: official HUP GME program denominator parsed from the public Penn Medicine program list.
- `artifacts/data/penn_gme_program_coverage.csv`: coverage audit mapping official HUP programs to current captured rosters, discovered pages without roster capture, and undiscovered gaps.
- `artifacts/data/official_program_coverage_assurance_audit.csv`: non-mutating assurance tiers for each official HUP coverage claim, separating direct/resolution-backed coverage from alias/count-review and open gaps.
- `artifacts/data/official_program_coverage_assurance_summary.json`: level counts, covered-people counts, and denominator-evidence status rollups for coverage trust.
- `artifacts/data/official_program_coverage_action_queue.csv`: prioritized non-mutating worklist for official HUP programs that are not level-4 denominator truth, with separate lanes for unresolved alias review versus accepted-alias denominator-closure policy.
- `artifacts/data/official_program_coverage_action_queue_summary.json`: action-lane counts and top next actions for parser, alias, count-conflict, and discovery work.
- `artifacts/data/official_program_alias_review_packets.csv`: review packets for alias-related coverage actions, joining official program rows, loaded labels, role/scope signals, and reviewer-ready decisions.
- `artifacts/data/official_program_alias_review_packets_summary.json`: reviewer-ready alias packet counts and top packet recommendations.
- `artifacts/data/official_program_alias_reviewer_decision_queue.csv`: reviewer-decision queue for alias packets, including packet fingerprints and required confirmation fields.
- `artifacts/data/official_program_alias_reviewer_decisions.csv`: manual reviewer decision input file for accepting/rejecting official-program alias mappings.
- `artifacts/data/official_program_alias_reviewer_decision_audit.csv`: audit of manual alias decisions against the current packet fingerprint and confirmation requirements.
- `artifacts/data/accepted_official_program_alias_mappings.csv`: accepted alias mappings from explicit reviewer decisions; currently 14 public-source-backed mappings covering 390 loaded people, still non-mutating for denominator coverage.
- `artifacts/data/official_program_alias_reviewer_decision_summary.json`: alias decision queue, pending, rejected/deferred, and accepted-mapping counts.
- `artifacts/data/penn_gme_gap_source_candidates.csv`: prioritized source queue for official HUP programs without captured current roster people.
- `artifacts/data/penn_gme_gap_source_probes.json`: reachability and page-signal observations for uncovered official HUP program URLs.
- `artifacts/data/penn_gme_gap_source_search_queries.csv`: reproducible search-query manifest for official HUP programs still missing public current-roster coverage.
- `artifacts/data/penn_gme_gap_source_search_observations.csv`: optional live-search execution ledger for official HUP gap-source searches.
- `artifacts/data/hup_gap_reason_audit.csv`: deterministic reason ledger for remaining official HUP coverage gaps.
- `artifacts/data/hup_gap_reason_summary.json`: gap-reason counts and recommended next-action counts.
- `artifacts/data/official_gap_roster_reconciliation.csv`: source-level reconciliation between extracted HUP gap-roster sources, official denominator rows, loaded memberships, and denominator-link status.
- `artifacts/data/official_gap_roster_reconciliation_summary.json`: counts for denominator-linked extracted records versus seed records that still need official-program-key mapping.
- `artifacts/data/official_gap_roster_program_resolution.csv`: non-mutating resolution ledger for seed-extracted gap rosters, mapping likely official program keys with confidence and denominator-mutation gating.
- `artifacts/data/official_gap_roster_program_resolution_summary.json`: counts for reviewer-ready denominator-resolution candidates versus role/scope review rows.
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
- SQLite tables `evidence_reconciliation_decisions` and `person_reconciliation_decisions`: queryable versions of the item-level and person/name-level reconciliation ledgers.
- `artifacts/data/person_evidence_review_packets.csv`: person/name-level evidence packets with top evidence, review kind, accepted-fact state, blocker, and next action.
- `artifacts/data/person_evidence_review_packet_summary.json`: packet counts for review-ready publication, attending-trend, secondary-anchor, and discovery-only work.
- `artifacts/data/person_evidence_reviewer_decision_queue.csv`: fingerprinted reviewer-decision queue for review-ready person evidence packets.
- `artifacts/data/person_evidence_reviewer_decisions.csv`: manual reviewer decision input file for accepting, rejecting, or deferring person evidence packets.
- `artifacts/data/person_evidence_reviewer_decision_audit.csv`: audit of manual person-evidence decisions against current packet fingerprints and confirmation requirements.
- `artifacts/data/person_evidence_review_triage.csv`: non-mutating review workbench for queued person-evidence packets, with triage lane, risk, decision difficulty, evidence density, source-family summary, reviewer prompt, and likely next action.
- `artifacts/data/person_evidence_review_triage_summary.json`: review-lane/risk/difficulty counts plus the top triage rows for prioritizing publication, identifier, official-profile, and trend-bridge review.
- `artifacts/data/person_evidence_review_dossiers.csv`: per-packet reviewer dossiers with current program context, top evidence records, source domains, decision counts, current decision status, manual decision templates, missing-evidence summary, and non-mutating acceptance boundary.
- `artifacts/data/person_evidence_review_dossier_summary.json`: review-route, decision-status, risk, role, missing-evidence, and top-dossier counts for person-by-person evidence reconciliation.
- `artifacts/data/person_evidence_review_batches.csv`: bounded reviewer batches over triage rows, grouped by lane, difficulty, risk, and role so packet decisions can be executed in coherent review sessions.
- `artifacts/data/person_evidence_review_batch_summary.json`: batch counts, top batches, source-family mix, and total packet/review-ready/evidence burden for person-evidence review execution.
- `artifacts/data/person_evidence_review_batch_packets.csv`: packet-level decision-support rows for each person-evidence review batch, joining packet fingerprints, top evidence records, support status, and recommended reviewer actions.
- `artifacts/data/enrichment_acceptance_audit.csv`: non-mutating acceptance assurance ledger for publication, NPI, profile, and trend evidence.
- `artifacts/data/enrichment_acceptance_summary.json`: acceptance-tier counts, including cross-source publication machine-acceptance candidates.
- `artifacts/data/accepted_enrichment_claims.csv`: strict machine-accepted enrichment facts, currently non-roster-mutating publication claims with provenance, acceptance policy, and final display-sanity checks attached.
- `artifacts/data/accepted_enrichment_summary.json`: accepted-enrichment counts by person, role, claim type, and enrichment type.
- `artifacts/data/attending_trend_linkage_events.csv`: event-level assurance audit for whether attending/faculty/outcome evidence can support a Penn-trainee trend link.
- `artifacts/data/attending_trend_linkage_groups.csv`: person/source-group rollup for recent-attending trend linkage candidates.
- `artifacts/data/attending_historical_link_candidates.csv`: seeded/search-discovered source candidates that may bridge current Penn attending endpoints to dated historical trainee records.
- `artifacts/data/attending_historical_link_search_queries.csv`: deterministic web-search query plan for attending trend identity linkage.
- `artifacts/data/attending_historical_link_query_plan_summary.json`: no-network query-plan coverage counts for current attending endpoints and Penn-training-claim groups before search/probe execution.
- `artifacts/data/attending_historical_link_search_observations.csv`: search execution observations for historical-link trend discovery.
- `artifacts/data/attending_biosketch_bridge_candidates.csv`: official Penn Faculty Biosketch training-line bridge candidates for current attendings with Penn-training claims.
- `artifacts/data/attending_biosketch_bridge_summary.json`: status counts for dated recent Penn training bridge candidates, non-Penn context, and research-training context.
- `artifacts/data/attending_trend_reconciliation.csv`: non-mutating trend acceptance ledger combining endpoint, Penn-training, biosketch, and historical-link evidence.
- `artifacts/data/attending_trend_reconciliation_summary.json`: review-ready recent attending trend counts and remaining bridge gaps.
- `artifacts/data/attending_trend_review_claims.csv`: materialized review-ready recent Penn-trained current-attending trend candidates, still not accepted trend facts until reviewer acceptance.
- `artifacts/data/attending_trend_acceptance_audit.csv`: explicit non-mutating acceptance gate for review-ready recent-attending trend candidates, including reviewer-action blockers and accepted-fact counts.
- `artifacts/data/attending_trend_acceptance_summary.json`: accepted-vs-review-ready trend counts by blocker, training type, and training end year.
- `artifacts/data/attending_trend_reviewer_decision_queue.csv`: reviewer-decision queue for review-ready recent-attending trend claims, including claim fingerprints and required confirmation fields.
- `artifacts/data/attending_trend_reviewer_decisions.csv`: manual reviewer decision input file; accepted facts require `accept_trend_fact`, a matching claim fingerprint, and all confirmation fields set.
- `artifacts/data/attending_trend_reviewer_decision_audit.csv`: audit of manual decisions against the current claim fingerprint and acceptance policy.
- `artifacts/data/attending_trend_reviewer_decision_dossiers.csv`: compact reviewer decision dossiers and prefilled manual-decision templates for pending and accepted recent-attending trend claims.
- `artifacts/data/accepted_attending_trend_facts.csv`: accepted recent Penn-trained current-attending trend facts from explicit reviewer decisions with compact provenance pointers.
- `artifacts/data/attending_trend_reviewer_decision_summary.json`: reviewer-decision queue, pending, rejected/deferred, and accepted-fact counts.
- `artifacts/data/attending_trend_review_rollups.csv`: trend-review rollups by corpus, training type, training end year, source scope, and ten-year-window scope.
- `artifacts/data/attending_trend_review_claims_summary.json`: review-ready trend claim, person, end-year, and rollup counts.
- `artifacts/data/attending_trend_discovery_workbench.csv`: group-level trend discovery state combining dossiers, historical-link query coverage, candidate URLs, reviewer queues, and accepted facts.
- `artifacts/data/attending_trend_discovery_workbench_summary.json`: accepted, review-ready, endpoint-search, historical-candidate, and context-only trend work counts.
- `artifacts/data/npi_candidate_claims.csv`: candidate NPPES/NPI identity, taxonomy, and PA practice-location anchors for current residents/fellows.
- `artifacts/data/npi_candidate_summary.json`: NPI query, status, role, and taxonomy counts.
- `artifacts/data/person_enrichment_coverage.csv`: per-person coverage audit across profile, program, training, contact, research, career-event, reconciliation, and state-machine layers.
- `artifacts/data/program_enrichment_coverage.csv`: per-program/role enrichment coverage rollup and next-action summary.
- `artifacts/data/trainee_profile_search_queries.csv`: queue-driven official-profile search manifest for trainees missing roster-linked profile URLs.
- `artifacts/data/trainee_profile_search_observations.csv`: search execution observations for the trainee profile discovery lane.
- `artifacts/data/trainee_profile_discovery_candidates.csv`: discovered profile/context URL candidates with match features and required next evidence.
- `artifacts/data/trainee_profile_discovery_claims.json`: replayable candidate evidence claims emitted by the profile discovery lane.
- `artifacts/data/trainee_profile_discovery_summary.json`: people/query/candidate counts and non-mutating profile-discovery policy.
- `artifacts/data/official_profile_discovery_workbench.csv`: person-level profile-gap workbench that reconciles planned queries, live search observations, direct probes, and candidate URLs into a next action per uncovered trainee.
- `artifacts/data/official_profile_discovery_workbench_summary.json`: profile-discovery counts by role, lane, query status, candidate status, and top review rows.
- `artifacts/data/official_profile_discovery_batches.csv`: bounded execution batches over profile-gap workbench rows, grouped by discovery lane, role, source domain, and query/candidate status so profile searches, retries, direct probes, and candidate reviews can be worked in coherent sessions.
- `artifacts/data/official_profile_discovery_batch_summary.json`: batch counts, workbench/query burden, blocked/unsearched query counts, and top official-profile discovery batches.
- `artifacts/data/official_profile_reobservation_audit.csv`: current-source reobservation audit for review-ready official-profile candidates, including page hash, canonical URL, title, same-name/program context checks, and route-drift status.
- `artifacts/data/official_profile_reobservation_summary.json`: profile reobservation counts by current fetch status, role, and route/context outcome.
- `artifacts/data/official_profile_reviewer_decision_dossiers.csv`: copy-ready reviewer dossiers for official-profile URL candidates, including current decision status, reobservation/route-drift evidence, acceptance boundary, and manual decision templates keyed to the current profile fingerprint.
- `artifacts/data/official_profile_reviewer_decision_dossier_summary.json`: official-profile reviewer dossier counts by decision status, reobservation status, and role.
- `artifacts/data/prior_training_search_queries.csv`: queue-driven search manifest for medical-school and prior-residency background enrichment gaps.
- `artifacts/data/prior_training_search_observations.csv`: search execution observations for prior-training background discovery.
- `artifacts/data/prior_training_discovery_candidates.csv`: candidate pages that may support medical-school or prior-residency background claims.
- `artifacts/data/prior_training_discovery_claims.json`: replayable candidate-only education/prior-training claims emitted by the prior-training discovery lane.
- `artifacts/data/prior_training_discovery_summary.json`: task, person, query, candidate, and source counts for the prior-training discovery lane.
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
- `artifacts/data/training_lifecycle_assurance_rollups.csv`: compact lifecycle/state-machine assurance rollups across corpus, role, category, program, program-role, lifecycle code, and readiness status.
- `artifacts/data/training_lifecycle_assurance_summary.json`: one-glance answer for stale-information policy, expected next-year changes, and review/source-refresh burden.
- `artifacts/data/training_state_transition_plan.csv`: row-level next-refresh transition policy for every current state, separating expected advancement, expected completion, source refresh, manual review, and no-change lanes.
- `artifacts/data/training_state_transition_plan_rollups.csv`: transition-plan rollups by corpus, institution, country, role, category, program, program-role, institution-role, lifecycle code, policy lane, and diff-readiness status.
- `artifacts/data/training_state_transition_plan_summary.json`: one-glance counts for auto-classifiable, fresh-observation-required, source-bound, and review-bound future transitions.
- `artifacts/data/training_temporal_contracts.csv`: explicit per-state stale/transition contract for next runs, including the current temporal state code, allowed automatic diff outcomes, review triggers, and evidence required to retain, advance, or complete the row.
- `artifacts/data/training_temporal_contract_rollups.csv`: temporal-contract rollups by corpus, institution, country, role, category, program, program-role, lifecycle code, temporal state, next-refresh contract, and diff-readiness status.
- `artifacts/data/training_temporal_contract_summary.json`: one-glance stale-policy, guardrail, and next-refresh contract counts.
- `artifacts/data/official_roster_refresh_workbench.csv`: source/program-level refresh contracts for official trainee rosters, derived from temporal contracts and source provenance.
- `artifacts/data/official_roster_refresh_workbench_summary.json`: roster-refresh counts by lane, difficulty, role, source, program, and top source URLs for next collector runs.
- `artifacts/data/official_roster_refresh_batches.csv`: bounded collector/parser/domain execution batches over roster-refresh contracts, preserving source URLs and expected state-machine outcomes before any mutation.
- `artifacts/data/official_roster_refresh_batch_summary.json`: batch counts by collector, lane, status, source-program burden, and top execution packets.
- `artifacts/data/training_state_snapshots/`: durable snapshot CSV/manifest files for longitudinal reruns.
- `artifacts/data/training_state_transition_events.csv`: SQLite-backed transition ledger for the latest materialized snapshot comparison.
- `artifacts/data/training_state_transition_rollups.csv`: transition rollups by corpus, country, institution, role, trainee category, program, program-role, institution-role, and lifecycle code for annual diff views.
- `artifacts/data/training_state_snapshot_summary.json`: snapshot and transition counts for the current materialized state.
- `config/training_lifecycle_rules.json`: local lifecycle codes and nominal-duration rules used to interpret trainee stages over time.
- `artifacts/data/person_contacts.csv`: public person/contact candidates with source, scope, verification status, confidence, and candidate status.
- `artifacts/data/contact_assurance_audit.csv`: non-mutating assurance ledger for public contact candidates, including domain/source checks, display-safety status, freshness policy, and required next verification.
- `artifacts/data/contact_assurance_summary.json`: public-contact assurance counts by status, role, domain, source class, and display policy.
- `artifacts/data/contact_verification_contracts.csv`: per-contact freshness/verification contracts that define stale dates, allowed refresh outcomes, and evidence required before verified use.
- `artifacts/data/contact_reobservation_audit.csv`: current public-source reobservation audit for contact candidates, recording source fetch status, page hash, whether the same value is still present, and match context without accepting the contact.
- `artifacts/data/contact_reobservation_summary.json`: reobservation counts by status, source fetch outcome, domain status, and source URL burden.
- `artifacts/data/official_program_denominator_closure_audit.csv`: accepted-alias denominator-closure audit for official Penn/HUP programs, separating reporting crosswalk closure from roster-truth mutation.
- `artifacts/data/official_program_denominator_closure_summary.json`: denominator-closure counts and policy notes for accepted official-program alias mappings.
- `artifacts/data/contact_verification_reviewer_decision_queue.csv`: reviewer-decision queue for public contact verification, including contact fingerprints and required confirmation fields.
- `artifacts/data/contact_verification_reviewer_decisions.csv`: manual reviewer decision input file for accepting/rejecting verified contact facts.
- `artifacts/data/contact_verification_reviewer_decision_audit.csv`: audit of manual contact decisions against the current contact fingerprint and confirmation requirements.
- `artifacts/data/contact_verification_reviewer_decision_dossiers.csv`: copy-ready contact reviewer dossiers with current decision status, reobservation evidence, acceptance boundary, and manual decision templates keyed to the current contact fingerprint.
- `artifacts/data/contact_verification_batches.csv`: bounded reviewer batches over contact dossiers, grouped by queue status, verification lane, reobservation result, role, domain, and source class while keeping exact contact values in per-contact dossiers.
- `artifacts/data/contact_verification_batch_summary.json`: batch counts, same-value/missing-value reobservation burden, pending decision counts, and top contact verification batches.
- `artifacts/data/accepted_verified_contact_facts.csv`: accepted public-source-backed verified contact facts; currently empty until explicit reviewer acceptance records current official reobservation.
- `artifacts/data/contact_verification_reviewer_decision_summary.json`: contact-decision queue, pending, rejected/deferred, and accepted-contact counts.
- `artifacts/data/contact_verification_reviewer_decision_dossier_summary.json`: contact reviewer dossier counts by current decision status, queue status, verification lane, and reobservation status.
- `artifacts/data/career_events.csv`: current Penn attending and alumni/outcome candidate events.
- `artifacts/data/source_quality_report.json`: machine-readable source utility observations and feature distributions.
- `artifacts/data/source_utility_scorecard.csv`: empirical source-utility scorecard across roster truth, denominator coverage, source discovery, research enrichment, attending trends, contact evidence, normalization, and longitudinal state-machine readiness.
- `artifacts/data/source_utility_scorecard_summary.json`: quality-band and next-action rollup for source utilities.
- `artifacts/data/search_utility_assurance.csv`: cross-lane assurance ledger for search-backed discovery utilities, separating query manifests, search observations, endpoint failures, and candidate yields.
- `artifacts/data/search_utility_assurance_summary.json`: rollup counts for planned, executed, blocked, and candidate-yielding search utilities.
- `artifacts/data/person_enrichment_action_member_execution_queue.csv`: fingerprinted per-member execution-decision queue.
- `artifacts/data/person_enrichment_action_member_execution_decisions.csv`: manual execution-outcome input file for action-batch members.
- `artifacts/data/person_enrichment_action_member_execution_audit.csv`: audit of execution decisions, stale fingerprints, blockers, and downstream routing.
- `artifacts/data/person_enrichment_action_member_execution_dossiers.csv`: compact per-member execution dossiers with command hints, routing checklists, and manual execution templates.
- `artifacts/data/person_enrichment_action_execution_plan.csv`: batch-level execution plan over person-enrichment action members, including pending/blocked/executed counts, command hints, decision templates, output routing, and non-mutating acceptance boundary.
- `artifacts/data/person_enrichment_action_execution_plan_summary.json`: execution-plan rollups by lane, blocker, batch status, and top operator batches.
- `artifacts/data/research_identity_corroboration.csv`: person-level corroboration ledger that joins PubMed/OpenAlex/ORCID research candidates with NPI/profile/contact/training-state anchors, flags conflicts, and assigns non-mutating review routes.
- `artifacts/data/research_identity_corroboration_summary.json`: rollup counts for people with research signal, review-ready research, multi-source evidence, secondary anchors, and top review-priority rows.
- `artifacts/data/research_identity_review_batches.csv`: bounded reviewer sessions over research identity corroboration rows, grouped by status, route, lane, and role with non-mutating acceptance rules.
- `artifacts/data/research_identity_review_batch_members.csv`: per-person batch membership ledger with current corroboration member fingerprints for source-specific research identity decisions.
- `artifacts/data/research_identity_review_batch_summary.json`: batch/member counts, review-lane mix, conflict-member burden, and top executable research identity batches.
- `artifacts/data/research_identity_reviewer_decision_queue.csv`: fingerprinted reviewer-decision queue for research identity batch members, including conflict resolution and confirmation requirements.
- `artifacts/data/research_identity_reviewer_decisions.csv`: manual reviewer decision input file for accepting, rejecting, quarantining, or deferring research identity evidence.
- `artifacts/data/research_identity_reviewer_decision_audit.csv`: audit of research identity reviewer decisions against current member fingerprints and required confirmations.
- `artifacts/data/research_identity_reviewer_decision_dossiers.csv`: compact per-decision dossiers with top claims, source-family counts, identifier summaries, missing evidence, and manual decision templates.
- `artifacts/data/research_identity_review_batch_packets.csv`: batch-level packets over research identity reviewer sessions, rolling pending member decisions, conflicts, top dossiers, source-family counts, and member decision templates into one review surface per batch.
- `artifacts/data/corpus_action_worklist.csv`: ranked non-mutating operator worklist that unifies program gaps, search execution, person evidence review, contact verification, temporal-state refresh, enrichment collectors, and recent-attending trend bridges.
- The worklist consumes `person_evidence_review_batches.csv` when available, with `person_evidence_review_batch_packets.csv` as packet-level evidence support, so person-evidence actions are bounded review sessions; if batches are absent it falls back to `person_evidence_review_triage.csv`, then the raw reviewer queue.
- The worklist consumes `research_identity_review_batches.csv` when available, so research identity corroboration becomes bounded reviewer sessions with member fingerprints; if batches are absent it falls back to grouped corroboration rows.
- The worklist consumes `official_roster_refresh_workbench.csv` when available, so roster refresh work is grouped by public source URL, program, role, and expected transition lane instead of broad role-level tasks.
- The worklist consumes `official_roster_refresh_batches.csv` when available, so roster refresh execution is grouped into bounded collector/parser/domain batches while source/program contracts remain the downstream evidence detail.
- The worklist consumes `person_enrichment_action_execution_plan.csv` when available, so action-member execution is routed through bounded batch plans with member-fingerprint decision templates instead of raw per-member dossier scans.
- `artifacts/data/official_roster_refresh_execution_audit.csv`: post-run collector audit tying refreshed public roster source summaries to the resulting training-state snapshot diff.
- The worklist consumes the refresh execution audit to down-rank ready roster batches that were already refreshed with no state delta, while keeping parser-support blockers visible.
- The worklist consumes `official_profile_discovery_batches.csv` when available, so missing-profile work becomes bounded review/search/probe sessions with person-level workbench rows as evidence detail; if batches are absent it falls back to the workbench.
- `artifacts/data/corpus_action_worklist_summary.json`: one-glance action-surface, priority-band, impact, and top-work-item rollups for the unresolved corpus.
- `artifacts/data/warehouse_reproducibility_audit.csv`: artifact hash, size, and row-count parity audit for the SQLite warehouse and generated flat files.
- `artifacts/data/warehouse_reproducibility_summary.json`: reproducibility rollup, including required missing artifacts, row-count mismatches, and generated SQLite storage policy.
- `artifacts/research/penn-source-quality-learnings-2026-06-02.md`: first source-quality learning report.
- `artifacts/research/training-state-machine-methodology-2026-06-02.md`: lifecycle/state-machine methodology, mutation guardrails, temporal-contract counts, and diff semantics.
- `artifacts/research/`: methodology and tradeoff briefs.

As of the latest local generation, the warehouse has 1,535 people: 925 residents, 385 fellows, and 225 public MSTP student-directory records. It also has 1,775 accepted roster/training event rows, 1,111 PubMed author-query research candidates, 3,416 official trainee profile claims, 313 public contact candidates, and 105 career/outcome candidate events. The Department of Medicine subset remains the highest-confidence starting corpus; the broader Penn-affiliated and HUP gap-queue scrapes add conservative non-Medicine resident/fellow rosters from official Penn pages and mark them for review.

The official HUP GME coverage audit currently parses 91 public HUP programs: 65 have captured current roster people, 12 are discovered as program/source pages without current roster capture, and 14 are not yet discovered by the current Penn-wide crawl.

The HUP gap-source probe currently queues 72 candidate URLs, including 15 roster-source candidates, for the next scraper pass. The recomputed official gap-reason ledger has 26 official programs without captured roster people. The queue-driven HUP gap roster scraper currently retains 576 conservative person records from 31 official public sources with extracted records, including 52 Psychiatry residents from the official Penn Psychiatry PGY class pages. If a later refresh hits a transport-level error or the reachable page loses parser-supported roster structure for a previously successful public roster URL, the scraper preserves the prior successful rows and records the refresh problem in source provenance; staleness and mutation decisions remain in the training state machine.

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
python3 scripts/audit_penn_med_student_sources.py
python3 scripts/generate_enrichment_queue.py
python3 scripts/materialize_person_enrichment_execution_readiness.py
python3 scripts/discover_organization_identifier_candidates.py --limit 80 --min-mentions 4 --candidates-per-org 3 --sleep 0.05
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
python3 scripts/audit_official_gap_roster_reconciliation.py
python3 scripts/audit_official_gap_roster_program_resolution.py
python3 scripts/audit_official_program_coverage_assurance.py
python3 scripts/materialize_official_program_coverage_action_queue.py --ignore-closure
python3 scripts/materialize_official_program_alias_review_packets.py
python3 scripts/materialize_official_program_alias_reviewer_decisions.py
python3 scripts/materialize_official_program_denominator_closure_audit.py
python3 scripts/materialize_official_program_coverage_action_queue.py
python3 scripts/audit_official_program_alias_reconciliation.py
python3 scripts/generate_enrichment_queue.py
python3 scripts/materialize_person_enrichment_execution_readiness.py
python3 scripts/collect_research_candidates.py --from-queue --roles resident,fellow,medical_student --only pubmed --skip-existing-source pubmed_eutilities --sleep 0.34
python3 scripts/collect_research_candidates.py --from-queue --roles resident,fellow,medical_student --only openalex --skip-existing-source pubmed_eutilities --sleep 0.05 --request-timeout 5 --request-attempts 2 --progress-every 25
python3 scripts/collect_pubmed_article_candidates.py --sleep 0.34 --batch-size 100
python3 scripts/materialize_trainee_profile_claims.py
python3 scripts/build_sqlite.py
python3 scripts/audit_hup_gap_reasons.py
python3 scripts/audit_official_program_alias_reconciliation.py
python3 scripts/audit_penn_med_student_sources.py
python3 scripts/discover_organization_identifier_candidates.py --limit 80 --min-mentions 4 --candidates-per-org 3 --sleep 0.05
python3 scripts/discover_acgme_program_identifier_candidates.py
python3 scripts/audit_program_identifier_reconciliation.py
python3 scripts/audit_program_lifecycle_consistency.py
python3 scripts/audit_program_lifecycle_duration_evidence.py
python3 scripts/materialize_program_lifecycle_duration_reviewer_decisions.py
python3 scripts/export_warehouse_views.py
python3 scripts/materialize_training_state_snapshot.py --compare-date 2026-06-02
python3 scripts/audit_training_state_machine.py
python3 scripts/audit_longitudinal_change_readiness.py --refresh-date 2027-08-15
python3 scripts/materialize_training_lifecycle_assurance.py
python3 scripts/materialize_training_state_transition_plan.py
python3 scripts/materialize_official_roster_refresh_batches.py
python3 scripts/audit_enrichment_coverage.py
python3 scripts/generate_enrichment_queue.py
python3 scripts/materialize_person_enrichment_execution_readiness.py
python3 scripts/collect_npi_candidates.py --sleep 0.03
python3 scripts/audit_reconciliation_decisions.py --as-of-year 2026
python3 scripts/audit_attending_trend_linkage.py --as-of-year 2026
python3 scripts/audit_attending_biosketch_bridges.py --as-of-year 2026
python3 scripts/materialize_attending_historical_link_query_plan.py
python3 scripts/discover_attending_historical_links.py --max-groups 4 --max-results 4 --probe-pages --sleep 0.2
python3 scripts/audit_attending_trend_reconciliation.py --as-of-year 2026
python3 scripts/audit_person_evidence_review_packets.py
python3 scripts/materialize_person_evidence_reviewer_decisions.py
python3 scripts/materialize_person_evidence_review_triage.py
python3 scripts/materialize_person_evidence_review_dossiers.py
python3 scripts/materialize_person_evidence_review_batches.py
python3 scripts/materialize_person_enrichment_action_packets.py
python3 scripts/materialize_person_enrichment_action_batches.py
python3 scripts/materialize_person_enrichment_action_batch_members.py
python3 scripts/materialize_person_enrichment_action_member_execution.py
python3 scripts/materialize_person_enrichment_action_member_execution_dossiers.py
python3 scripts/materialize_person_enrichment_action_execution_plan.py
python3 scripts/materialize_research_identity_corroboration.py
python3 scripts/materialize_research_identity_review_batches.py
python3 scripts/materialize_research_identity_reviewer_decisions.py
python3 scripts/materialize_research_identity_reviewer_decision_dossiers.py
python3 scripts/materialize_research_identity_review_batch_packets.py
python3 scripts/audit_enrichment_acceptance.py
python3 scripts/materialize_accepted_enrichment.py
python3 scripts/audit_contact_assurance.py
python3 scripts/materialize_contact_verification_contracts.py --as-of-date 2026-06-02
python3 scripts/materialize_contact_verification_reviewer_decisions.py
python3 scripts/materialize_contact_verification_reviewer_decision_dossiers.py
python3 scripts/materialize_contact_verification_batches.py
python3 scripts/materialize_attending_trend_review_claims.py
python3 scripts/audit_attending_trend_acceptance.py
python3 scripts/materialize_attending_trend_reviewer_decisions.py
python3 scripts/materialize_attending_trend_reviewer_decision_dossiers.py
python3 scripts/materialize_attending_trend_discovery_workbench.py
python3 scripts/audit_warehouse_reproducibility.py
python3 scripts/audit_source_utility_scorecard.py
python3 scripts/materialize_search_utility_assurance.py
python3 scripts/materialize_official_profile_discovery_workbench.py
python3 scripts/materialize_official_profile_discovery_batches.py
python3 scripts/materialize_official_profile_reobservation_audit.py
python3 scripts/materialize_official_profile_reviewer_decision_dossiers.py
python3 scripts/materialize_official_roster_refresh_batches.py
python3 scripts/materialize_corpus_action_worklist.py
python3 scripts/report_source_quality.py
python3 scripts/summarize_warehouse.py
```

`artifacts/data/redmank.sqlite` is a generated local warehouse, not a committed data blob. Rebuild it from committed artifacts with `python3 scripts/rebuild_local_warehouse.py`, then compare the resulting hash/storage metadata in `artifacts/data/redmank_sqlite_manifest.json`. The replay step intentionally avoids network collection; it recomputes official HUP denominator coverage from the committed official-program universe and current warehouse rows, then recomputes gap reasons so newly loaded rosters cannot remain stale gaps. Use the longer collection pipeline above when refreshing source data from the public web.

OpenAlex author search is implemented as a candidate utility. The latest queue-driven pass processed the 199 research-queued residents/fellows without non-rejected PubMed evidence and produced 549 OpenAlex author candidates, including 51 `needs_review` rows. Keep it as a resumable/polite enrichment lane rather than a default blocking rebuild step; OpenAlex rows are author-disambiguation candidates, not accepted research facts.

```bash
python3 scripts/collect_research_candidates.py --from-queue --roles resident,fellow,medical_student --only openalex --skip-existing-source pubmed_eutilities --sleep 0.05 --request-timeout 5 --request-attempts 2 --progress-every 25
```

Broad web search for attending historical-link discovery is optional and rate-limit sensitive. The latest pass attempted polite DuckDuckGo HTML queries for the four Penn-training-claim groups and recorded non-200 search responses as source-quality evidence; add `--skip-search` when you only want the seeded official Penn/provider baseline.

Official HUP gap-source search expansion is also optional. The default gap probe records search queries for not-discovered programs without calling a live search endpoint. Run an explicit search pass when broadening the official program universe:

```bash
python3 scripts/probe_penn_gme_gap_sources.py --search --search-scope not_discovered --max-search-queries-per-program 3 --max-search-results 4 --search-timeout 8 --sleep 0.2
```

Official trainee profile discovery is also queue-driven and rate-limit sensitive. The committed artifact is a no-network manifest for all uncovered profile-search rows; run the collector separately when refreshing candidate URLs:

```bash
python3 scripts/discover_trainee_official_profiles.py --resume-existing --max-search-queries 30 --max-queries-per-person 3 --max-results 3 --search-timeout 8 --probe-pages --sleep 0.1
```

Use `--resume-existing` with `--max-search-queries` for bounded live passes; this preserves the full planned query manifest while adding observations only for unsearched queries. Discovered URLs are candidate evidence only; they do not mutate `people.profile_url` unless a current roster link or reviewer-accepted evidence confirms same-person/current-trainee context.

After any profile-discovery pass, run `python3 scripts/materialize_official_profile_discovery_workbench.py` and `python3 scripts/materialize_official_profile_discovery_batches.py` to convert raw query/candidate evidence into person-level workbench rows and bounded execution batches. The workbench distinguishes planned-but-unexecuted searches, blocked search endpoints, low-signal direct probes, and official-profile candidates ready for same-person review; the batches keep those lanes executable without losing person-level provenance.

The same collector also supports a bounded direct Penn Medicine provider-profile slug probe. Use it as an optional fallback when broad search is throttled, not as a default corpus-wide step. Direct URL guesses remain low-signal unless the page fetches with HTTP 200 evidence:

```bash
python3 scripts/discover_trainee_official_profiles.py --skip-search --resume-existing --direct-provider-slug-probes --max-provider-slugs-per-person 1 --max-direct-probes 25 --probe-timeout 3 --sleep 0.05 --direct-progress-every 1
```

Prior-training background discovery uses the same queue-driven pattern for medical-school and residency-background gaps. The committed artifact is a no-network manifest; run the collector separately when refreshing public search candidates:

```bash
python3 scripts/discover_prior_training_background.py --max-queries-per-task 2 --max-results 4 --search-timeout 8 --sleep 0.2
```

Add `--probe-pages` when you want page hashes, HTTP status, titles, and term hits. Medical-school and prior-residency discoveries are candidate evidence only because name collisions and stale biosketches are common; accepted education/prior-training facts require corroborating same-person context or reviewer acceptance.

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

If `--old` is omitted, the script reads `artifacts/data/training_state_snapshot_summary.json` and compares against the recorded `previous_snapshot_id`.

The diff writes both person-level changes and `artifacts/data/training_state_diff_rollups.csv`, grouped by program, role, lifecycle code, temporal policy lane, and change type. By default it also reads `artifacts/data/training_temporal_contracts.csv`, so each row carries the contract key, policy lane, next-refresh contract, evidence requirement, review triggers, and expected-vs-review assurance used to classify the transition. The durable snapshot materializer also writes `artifacts/data/training_state_transition_rollups.csv`, which preserves transition views across corpus, country, institution, trainee category, role, program, program-role, institution-role, and lifecycle-code scopes. Snapshot transition events and rollups include `snapshot_comparison_kind`, snapshot as-of dates, and `days_between_snapshots` so same-day corpus revisions are not confused with annual advancement/completion flows.

`scripts/materialize_official_roster_refresh_batches.py` turns the source/program refresh contracts into execution packets by collector script, parser support, source domain, and bounded source-program count. These batches are operational only: they tell the next collector run what to refresh and why, while actual person/program state changes still require rebuilt source observations plus the snapshot/transition/reviewer gates.

Materialize a durable state snapshot:

```bash
python3 scripts/materialize_training_state_snapshot.py --compare-date 2026-06-02
```

The materializer writes `artifacts/data/training_state_snapshots/<snapshot_id>.csv` plus a JSON manifest, reloads every committed snapshot into SQLite, and writes transition events for the current snapshot against the previous one when present. The first snapshot is a baseline where all canonical person/program rows are `added`; later snapshots classify expected advancement, expected completion disappearance, unchanged states, stale removals, regressions, and review-required stage changes. When temporal contracts are materialized, transition events embed the matching contract policy in `evidence_json` and use that policy for expected-vs-review classification. Same-date snapshots are labeled `same_day_corpus_revision`, same-fingerprint reruns are labeled `same_corpus_rerun`, and snapshots roughly one academic year apart are labeled `annual_refresh_window`.

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

Materialize lifecycle assurance rollups:

```bash
python3 scripts/materialize_training_lifecycle_assurance.py
```

The assurance materializer writes `artifacts/data/training_lifecycle_assurance_rollups.csv` plus `artifacts/data/training_lifecycle_assurance_summary.json` and reloads the rollups into SQLite. It summarizes whether each corpus/program/category slice is deterministic-clock-supported, source-refresh-bound, or review-bound, and states the stale-information policy to use before next-year mutations.

Materialize explicit temporal contracts:

```bash
python3 scripts/materialize_training_temporal_contracts.py
```

The temporal-contract materializer writes row-level and rollup artifacts that make the future state machine queryable without reading several ledgers at once. Each row says what stage is currently valid, when it becomes stale, what evidence is needed to retain/advance/complete it, which diff outcomes are auto-classifiable, and which observations must enter review.

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
- Summarize state-machine assurance into corpus-, program-, category-, and lifecycle-code rollups so future reruns can show flow/change views without treating stale public roster facts as current truth.
- Preserve prior successful public roster rows when a later refresh has a transport-level fetch error or loses parser-supported roster structure, and let state-machine stale/review policy decide whether the observation can be retained, advanced, completed, or routed to review.
- Classify official denominator gaps by evidence-backed reason before treating them as missing people: context-only public page, parser/manual-review candidate, low-content official page, related-program alias review, or broader-discovery-needed.
- Resolve seed-extracted gap rosters against the official denominator with a separate program-resolution ledger; exact name/type/department candidates may become reviewer-ready, while role mismatches and broad department pages remain non-mutating review evidence.
- Assign assurance tiers to official coverage claims so denominator reports distinguish direct normalized-name support, exact program-resolution support, alias-method coverage requiring review, count conflicts, and open gaps.
- Materialize a prioritized action queue for non-level-4 official programs so the next loop can choose between parser work, source discovery, alias review, and count-conflict review from a stable evidence-backed list.
- Materialize alias review packets for alias-related coverage actions so broad labels, combined tracks, section splits, weak related sources, and count conflicts can be reviewed with consistent evidence before any denominator mutation.
- Separate accepted official-program alias bridges from unresolved alias review in the action queue; accepted bridges remain non-mutating until an explicit denominator-closure policy promotes or crosswalks them.
- Keep official-program alias/denominator reconciliation as a candidate ledger until the relation is strong enough to mutate coverage or split a loaded broad program into a narrower official program.
- Separate resident/fellow rosters, context-only program pages, alumni/former pages, and partial student directories.
- Treat the official MD-student directory as unavailable to public scraping when PennKey protection is observed; keep public MSTP records as partial student truth and public graduate-program directories as MD-PhD cross-check/enrichment candidates only.
- Store public contact channels as provenance-backed contact evidence, not as unqualified person identity fields.
- Treat public contact channels as display-safe candidates only after source, domain, person identity, and scope verification; domain anomalies remain review-required even when they came from public official pages.
- Treat publication, grant, trial, NPI, and social-web enrichment as separate evidence layers requiring identity-resolution confidence, not as roster truth.
- Rank candidate enrichment in an evidence reconciliation queue before accepting profile, publication, or attending-trend claims.
- Roll item-level evidence decisions into person/name review packets so manual or automated verifiers can see the best evidence, blocker, and next action before accepting enrichment.
- Score source utilities by observed claim surface, output quality, blockers, and next action before widening the corpus.
- Keep current-attending endpoints separate from accepted trend-line links until a historical roster, alumni page, CV, or independent profile connects the attending identity to a dated Penn trainee record.
- Keep review-ready recent-attending trend candidates separate from accepted trend facts until an explicit reviewer acceptance decision confirms identity, current endpoint, training line, program type, and dates.
- Use `attending_trend_reviewer_decision_dossiers.csv` as the compact review surface for pending recent-attending trend decisions; it carries the current claim fingerprint, source URL, bridge candidate key, confirmation checklist, and manual-decision template.
- Convert trend dossiers into `attending_trend_discovery_workbench.csv` so endpoint-only attendings, profile-claim bridge searches, historical-link candidates, pending reviewer decisions, and accepted facts stay in separate action lanes.
- Resolve school/hospital/program labels into organization rows with raw values, aliases, identifiers, and review status instead of overwriting source strings.
- Keep external organization identifiers as candidates until the source result agrees on the actual entity surface. Parent ROR candidates, search siblings, and relationship-only hints are useful evidence, but they should not mutate accepted organization identifiers without a second anchor.
- Keep scholarly API results as candidate evidence until reconciliation supplies enough non-name anchors.

See the latest research brief in `artifacts/research/` for source coverage, quality grades, and recommended enrichment tiers.
