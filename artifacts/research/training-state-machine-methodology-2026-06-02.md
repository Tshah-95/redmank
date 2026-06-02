# Training State Machine Methodology

Generated from the 2026-06-02 Penn-affiliated trainee warehouse refresh.

## Current Answer

Training rows are stored as time-aware state observations, not as flat permanent facts. The warehouse currently has 1,682 `person_training_states` rows across 1,535 people and 95 programs. Each state preserves the raw public-source label, then attaches a normalized stage, lifecycle code, expected next date, expected exit date, stale-after date, refresh policy, transition rule, and confidence.

The state machine is deliberately non-mutating. Time can make a row stale, but time alone does not rewrite a person's record. A future refresh must supply fresh public evidence, an expected terminal absence, an alumni/completion endpoint, or a reviewer decision before accepted person/program truth changes.

## Temporal Contracts

`training_temporal_contracts` is the row-level contract ledger for future reruns. It currently contains:

- 659 rows in `ANNUAL_CLOCK_EXPECTED_ADVANCEMENT`.
- 252 rows in `TERMINAL_STAGE_EXPECTED_COMPLETION`.
- 627 rows in `VARIABLE_DURATION_SOURCE_REFRESH`.
- 131 rows in `AMBIGUOUS_OR_OUT_OF_RULE_REVIEW`.
- 13 rows in `CURRENT_OBSERVATION`.

The projected next refresh date is 2027-08-15. By then, 1,669 rows require fresh observation or review before retention, advancement, or completion is accepted. That is intentional: the system can say a row is stale without pretending it is false.

## Diff Semantics

Durable snapshots live in `artifacts/data/training_state_snapshots/` and load into `training_state_snapshot_rows`. Snapshot comparisons materialize into `training_state_transition_events` and rollups by person, program, institution, role, category, lifecycle code, and temporal-policy lane.

The latest same-day corpus revision compares `training_states_2026-06-02_ed87f34b0e2f` against `training_states_2026-06-02_dffa6e406d83`:

- 1,610 canonical person/program keys.
- 1,558 unchanged keys.
- 52 added resident keys.
- 72 duplicate raw observations collapsed into canonical person/program comparisons.

Same-day corpus revisions, same-corpus reruns, cross-date refreshes, and annual refresh windows are labeled separately so data churn is not mistaken for annual training progression.

## Mutation Guardrails

Expected advancement is only a candidate if the later public source observes the expected next stage for the same person/program. Expected completion can be classified only when the person is absent after the stale-after window or when a public alumni/completion endpoint supports the transition.

The current corpus guardrail is `review_bound` because some rows have unknown fellow years, variable-duration phases, lab/research labels, chief-year ambiguity, or lifecycle labels outside local rules. Those rows stay in `source_refresh_required` or `manual_review_required` lanes rather than being advanced automatically.

## What This Enables

The same structure supports individual, program, institution, category, and national-level flow views:

- individual: "Where did this person move, and was it expected?"
- program: "Which roster changes are expected advancement, expected completion, additions, or surprises?"
- institution: "Which Penn programs are stale, source-bound, or review-bound?"
- category: "How do residents, fellows, and medical students differ in refresh reliability?"
- national: "Once other institutions are loaded, compare lifecycle-normalized flows without relying on local source labels."

The practical rule is: raw public facts remain provenance-preserved; normalized lifecycle state drives stale/diff/review behavior; accepted person truth changes only after a contract-supported fresh observation, expected terminal absence, or reviewer decision.
