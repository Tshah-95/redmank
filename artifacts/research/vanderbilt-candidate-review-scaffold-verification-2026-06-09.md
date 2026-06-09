---
type: research-checkpoint
title: Vanderbilt Candidate Review Scaffold Verification
created_at: 2026-06-09T05:31:05.391559+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Candidate Review Scaffold Verification

## Boundary

Non-mutating Vanderbilt candidate review scaffold verification. It checks pending decision rows, blank manual decision templates, confirmation fields, hash boundaries, and raw-field absence. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_check_status": {
    "pass": 7
  },
  "csv": "artifacts/data/vanderbilt_candidate_review_scaffold_verification.csv",
  "decision_scaffold_rows": 159,
  "denominator_closure_allowed": false,
  "fail_rows": 0,
  "generated_at": "2026-06-09T05:31:05.391559+00:00",
  "json": "artifacts/data/vanderbilt_candidate_review_scaffold_verification.json",
  "manual_decision_template_rows": 159,
  "markdown": "artifacts/research/vanderbilt-candidate-review-scaffold-verification-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 7,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt candidate review scaffold verification. It checks pending decision rows, blank manual decision templates, confirmation fields, hash boundaries, and raw-field absence. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "raw_leak_hit_rows": 0,
  "rowset_sha256": "24e03f71174cd456b4783457113d64d4b15185721fc86092ca2a5f47e7eb4260",
  "source_decision_scaffold": "artifacts/data/vanderbilt_candidate_review_decision_scaffold.json",
  "source_decision_scaffold_rowset_sha256": "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938",
  "source_decision_scaffold_summary": "artifacts/data/vanderbilt_candidate_review_decision_scaffold_summary.json",
  "verification_rows": 7
}
```

## Checks

| check | status | observed |
| --- | --- | --- |
| acceptance_flags_all_false | pass | [] |
| manual_decision_keys_match_scaffold | pass | {"extra_in_decisions":[],"missing_in_decisions":[]} |
| manual_decision_templates_blank | pass | {"nonblank_actions":[],"nonblank_confirmations":[]} |
| raw_name_and_url_fields_absent | pass | [] |
| review_lane_counts_match | pass | {"candidate_fingerprint_review":155,"linked_scope_metadata_review":3,"route_recourse_review":1} |
| scaffold_and_manual_row_counts_match | pass | {"decision_csv":159,"decision_json":159,"scaffold_csv":159,"scaffold_json":159} |
| source_rowset_boundary_matches | pass | "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938" |
