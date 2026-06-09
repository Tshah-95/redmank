---
type: research-checkpoint
title: Vanderbilt Candidate Parser Output Verification
created_at: 2026-06-09T05:20:26.208987+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Candidate Parser Output Verification

## Boundary

Non-mutating Vanderbilt candidate parser output verification. It validates raw-name-free candidate fingerprints, scope metadata, recourse rows, source rowset boundaries, and acceptance prohibitions. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_candidate_source_kind": {
    "heading_signal": 57,
    "profile_anchor": 98
  },
  "by_check_status": {
    "pass": 9
  },
  "by_program_candidate_fingerprints": {
    "Academic General Pediatrics": 4,
    "Developmental-Behavioral Pediatrics": 4,
    "Gastroenterology": 10,
    "General Surgery": 2,
    "Neonatal-Perinatal Medicine": 19,
    "Pediatric Critical Care": 17,
    "Pediatric Emergency Medicine": 17,
    "Pediatric Endocrinology": 3,
    "Pediatric Gastroenterology": 12,
    "Pediatric Hospital Medicine": 4,
    "Pediatric Infectious Diseases": 10,
    "Pediatric Rheumatology": 4,
    "Pediatrics": 26,
    "Psychiatry": 9,
    "Rheumatology": 4,
    "Transplant Hepatology": 10
  },
  "candidate_fingerprint_rows": 155,
  "csv": "artifacts/data/vanderbilt_candidate_parser_output_verification.csv",
  "denominator_closure_allowed": false,
  "duplicate_fingerprint_groups": 0,
  "fail_rows": 0,
  "gbrain_approval_effect": "vanderbilt_candidate_parser_output_verification_registered",
  "gbrain_denial_effect": "vanderbilt_candidate_parser_output_verification_denied",
  "gbrain_denial_line": "",
  "gbrain_denial_recourse": "",
  "gbrain_registration_status": "approved_exact_candidate_output_verification",
  "generated_at": "2026-06-09T05:20:26.208987+00:00",
  "json": "artifacts/data/vanderbilt_candidate_parser_output_verification.json",
  "markdown": "artifacts/research/vanderbilt-candidate-parser-output-verification-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 9,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt candidate parser output verification. It validates raw-name-free candidate fingerprints, scope metadata, recourse rows, source rowset boundaries, and acceptance prohibitions. It does not approve person ingestion, parser output as accepted people, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "raw_leak_hit_rows": 0,
  "required_approval_line": "APPROVE vanderbilt_candidate_parser_output_verification_registered VERIFICATION_ROWS 9 PASS_ROWS 9 FAIL_ROWS 0 CANDIDATE_FINGERPRINT_ROWS 155 SOURCE_ROWSET_SHA256 2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba ROWSET_SHA256 918556f5b5a33b5d8e7181ed6654a9b7773b8c8a24f09f9a23b06c7157d39fe2",
  "route_recourse_rows": 1,
  "rowset_sha256": "918556f5b5a33b5d8e7181ed6654a9b7773b8c8a24f09f9a23b06c7157d39fe2",
  "scope_metadata_rows": 3,
  "source_candidate_parser_output_rowset_sha256": "2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba",
  "source_candidate_parser_output_summary": "artifacts/data/vanderbilt_candidate_only_parser_output_summary.json",
  "source_candidate_parser_outputs": "artifacts/data/vanderbilt_candidate_only_parser_outputs.json",
  "verification_rows": 9
}
```

## Required Approval Line

`APPROVE vanderbilt_candidate_parser_output_verification_registered VERIFICATION_ROWS 9 PASS_ROWS 9 FAIL_ROWS 0 CANDIDATE_FINGERPRINT_ROWS 155 SOURCE_ROWSET_SHA256 2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba ROWSET_SHA256 918556f5b5a33b5d8e7181ed6654a9b7773b8c8a24f09f9a23b06c7157d39fe2`

GBrain registration status: `approved_exact_candidate_output_verification`.

## Checks

| check | status | observed |
| --- | --- | --- |
| acceptance_flags_all_false | pass | [] |
| csv_json_summary_row_counts_match | pass | {"csv_rows":159,"json_rows":159,"summary_rows":159} |
| duplicate_candidate_fingerprints_absent | pass | [] |
| fingerprint_hash_fields_present | pass | [] |
| output_kind_counts_match | pass | {"candidate_fingerprint":155,"route_recourse":1,"scope_metadata":3} |
| profile_anchor_paths_are_person_path | pass | [] |
| raw_name_and_url_fields_absent | pass | [] |
| scope_and_recourse_rows_have_no_candidate_fingerprints | pass | {"scope_or_recourse_fingerprints":0} |
| source_rowset_boundary_matches | pass | "2740184f00379fd6b1885632ac13faec45ff96bfbf0a70130aa712e5966612ba" |
