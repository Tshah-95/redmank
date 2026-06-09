---
type: research-checkpoint
title: Top50 Public Clone Verification
created_at: 2026-06-09T05:57:32.218247+00:00
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
  "generated_at": "2026-06-09T05:57:32.218247+00:00",
  "json": "artifacts/data/top50_public_clone_verification.json",
  "markdown": "artifacts/research/top50-public-clone-verification-2026-06-09.md",
  "mutation_allowed": false,
  "pass_rows": 13,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating public clone verification for the top-50/Vanderbilt operating substrate. It reads committed public-safe summaries, packets, README policy, and script guards. It does not fetch web pages, call GBrain, regenerate scratch-dependent manifests, approve person ingestion, close denominators, verify schools, rewrite URLs, accept enrichment facts, publish raw dumps, or collapse identities.",
  "raw_browser_dumps_committed": false,
  "raw_debug_databases_committed": false,
  "raw_gbrain_responses_committed": false,
  "rowset_sha256": "0347fde0a9594cd476c49938e55bc710d46104f325f061221c324902f95cc490",
  "top50_snapshot_rowset_sha256": "2743bdc6aa80c59dbcfa2f4dceb4a84668cbaff298a4d79756f79a6bad222588",
  "vanderbilt_batch_packet_rowset_sha256": "1f9da0ab244581dbf5782eab572d5045b8a53c8bffc9d4892e077ca1c7b0e30e",
  "vanderbilt_gap_manifest_rows": 113,
  "verification_rows": 13
}
```

## Checks

| check | status | observed |
| --- | --- | --- |
| top50_target_registry_boundary | pass | `{"rowset_sha256":"fa547bf602d8dc9998189a0fabe2b45a1cba6892239eedf391cdb65c6ef419d8","targets":50}` |
| school_verification_registry_boundary | pass | `{"mutation_allowed":false,"rowset_sha256":"e99eb07b856f8bdd546d2ac2bb0641c22cd2bedd69e42d8f38f7e5db04823e29","verified_school_rows":1}` |
| operating_snapshot_boundary | pass | `{"mutation_allowed":false,"rowset_sha256":"2743bdc6aa80c59dbcfa2f4dceb4a84668cbaff298a4d79756f79a6bad222588"}` |
| snapshot_points_to_vanderbilt_batch_packets | pass | `{"rowset_sha256":"1f9da0ab244581dbf5782eab572d5045b8a53c8bffc9d4892e077ca1c7b0e30e","status":"ready_for_bounded_vanderbilt_manual_review_packets"}` |
| vanderbilt_batch_packet_boundary | pass | `{"batch_packet_rows":20,"csv_rows":20,"decision_row_count":159,"invalid_decision_rows":0,"json_rows":20,"mutation_allowed":false,"pending_decision_rows":159,"raw_candidate_names_committed":false,"raw_person_urls_committed":false,"rowset_sha256":"1f9da0ab244581dbf5782eab572d5045b8a53c8bffc9d4892e077ca1c7b0e30e"}` |
| vanderbilt_decision_audit_boundary | pass | `{"accepted_person_rows":0,"audit_rows":159,"invalid_rows":0,"mutation_allowed":false,"pending_rows":159,"rowset_sha256":"e75fc27de3e1374e1e945efe207adbfb4cc04c4c7bc969afe4eaa3d0eb8e93de"}` |
| vanderbilt_scaffold_boundary | pass | `{"decision_scaffold_rows":159,"manual_decision_template_rows":159,"mutation_allowed":false,"rowset_sha256":"29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938"}` |
| vanderbilt_gap_manifest_committed_rows | pass | `{"csv_rows":113,"mutation_allowed":false,"open_gap_rows":113,"rows":113}` |
| vanderbilt_batch_packet_public_leak_scan | pass | `[]` |
| private_artifact_paths_not_committed | pass | `[]` |
| private_artifact_patterns_ignored | pass | `{".playwright-mcp/":true,"artifacts/data/browser_page_dumps/":true,"artifacts/data/debug_*.sqlite":true,"artifacts/data/gbrain_*_http_mcp_response.json":true,"artifacts/data/raw/":true,"inbox/":true,"reports/":true}` |
| gap_manifest_empty_output_guard_present | pass | `{"readme_override_documented":true,"script_guard":true}` |
| gbrain_public_clone_verification_lane_approved | pass | `"APPROVE top50_public_clone_verification_lane_approved"` |
