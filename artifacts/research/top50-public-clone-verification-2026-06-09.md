---
type: research-checkpoint
title: Top50 Public Clone Verification
created_at: 2026-06-09T06:29:54.283919+00:00
project: top-50-medical-school-roster-engine
---

# Top50 Public Clone Verification

## Boundary

Non-mutating public clone verification for the top-50/Vanderbilt operating substrate. It reads committed public-safe summaries, packets, README policy, and script guards. It does not fetch web pages, call GBrain, regenerate scratch-dependent manifests, approve person ingestion, close denominators, verify schools, rewrite URLs, accept enrichment facts, publish raw dumps, or collapse identities.

## Summary

```json
{
  "csv": "artifacts/data/top50_public_clone_verification.csv",
  "denominator_closure_allowed": false,
  "fail_rows": 0,
  "gbrain_approval_line": "APPROVE top50_public_clone_verification_lane_approved",
  "gbrain_approval_status": "approved_non_mutating_public_clone_verification_lane",
  "generated_at": "2026-06-09T06:29:54.283919+00:00",
  "json": "artifacts/data/top50_public_clone_verification.json",
  "markdown": "artifacts/research/top50-public-clone-verification-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 14,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating public clone verification for the top-50/Vanderbilt operating substrate. It reads committed public-safe summaries, packets, README policy, and script guards. It does not fetch web pages, call GBrain, regenerate scratch-dependent manifests, approve person ingestion, close denominators, verify schools, rewrite URLs, accept enrichment facts, publish raw dumps, or collapse identities.",
  "raw_browser_dumps_committed": false,
  "raw_debug_databases_committed": false,
  "raw_gbrain_responses_committed": false,
  "rowset_sha256": "1056abc4a0d52b01aea33e74c312c0d143881b126bdfe2edbc49357845d8a7bd",
  "top50_snapshot_rowset_sha256": "b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48",
  "vanderbilt_batch_packet_rowset_sha256": "26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f",
  "vanderbilt_gap_manifest_rows": 113,
  "vanderbilt_operator_packet_rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
  "verification_rows": 14
}
```

## Checks

| check | status | observed |
| --- | --- | --- |
| top50_target_registry_boundary | pass | `{"rowset_sha256":"fa547bf602d8dc9998189a0fabe2b45a1cba6892239eedf391cdb65c6ef419d8","targets":50}` |
| school_verification_registry_boundary | pass | `{"mutation_allowed":false,"rowset_sha256":"e99eb07b856f8bdd546d2ac2bb0641c22cd2bedd69e42d8f38f7e5db04823e29","verified_school_rows":1}` |
| operating_snapshot_boundary | pass | `{"mutation_allowed":false,"rowset_sha256":"b8933a5875eb28cdf61430110ddd9a70a41b2d4525198e38e17ff3924236fd48"}` |
| snapshot_points_to_vanderbilt_operator_packets | pass | `{"rowset_sha256":"6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173","status":"ready_for_public_safe_vanderbilt_operator_packets"}` |
| vanderbilt_batch_packet_boundary | pass | `{"batch_packet_rows":20,"csv_rows":20,"decision_row_count":159,"invalid_decision_rows":0,"json_rows":20,"mutation_allowed":false,"pending_decision_rows":159,"raw_candidate_names_committed":false,"raw_person_urls_committed":false,"rowset_sha256":"26b30bda381e9bc86c8d8448c0dcdb2a00466fcaf7f1d8b6d438331e702c3a0f"}` |
| vanderbilt_operator_packet_boundary | pass | `{"csv_rows":20,"decision_row_count":159,"json_rows":20,"missing_required_template_column_mentions":0,"mutation_allowed":false,"operator_packet_rows":20,"pending_decision_rows":159,"raw_candidate_names_committed":false,"raw_person_urls_committed":false,"rowset_sha256":"6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173"}` |
| vanderbilt_decision_audit_boundary | pass | `{"accepted_person_rows":0,"audit_rows":159,"invalid_rows":0,"mutation_allowed":false,"pending_rows":159,"rowset_sha256":"e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"}` |
| vanderbilt_scaffold_boundary | pass | `{"decision_scaffold_rows":159,"manual_decision_template_rows":159,"mutation_allowed":false,"rowset_sha256":"29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"}` |
| vanderbilt_gap_manifest_committed_rows | pass | `{"csv_rows":113,"mutation_allowed":false,"open_gap_rows":113,"rows":113}` |
| vanderbilt_review_packet_public_leak_scan | pass | `[]` |
| private_artifact_paths_not_committed | pass | `[]` |
| private_artifact_patterns_ignored | pass | `{".playwright-mcp/":true,"artifacts/data/browser_page_dumps/":true,"artifacts/data/debug_*.sqlite":true,"artifacts/data/gbrain_*_http_mcp_response.json":true,"artifacts/data/raw/":true,"inbox/":true,"reports/":true}` |
| gap_manifest_empty_output_guard_present | pass | `{"readme_override_documented":true,"script_guard":true}` |
| gbrain_public_clone_verification_lane_approved | pass | `"APPROVE top50_public_clone_verification_lane_approved"` |
