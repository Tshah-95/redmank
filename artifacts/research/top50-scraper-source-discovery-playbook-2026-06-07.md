---
type: research-checkpoint
title: Top50 Scraper Source-Discovery Playbook
created_at: 2026-06-08T02:42:14.639810+00:00
project: top-50-medical-school-roster-engine
---

# Top50 Scraper Source-Discovery Playbook

## Boundary

Non-mutating scraper/source-discovery playbook. It authorizes only source discovery, route probing, classification, and packet preparation. It does not authorize person ingestion, training-state mutation, denominator closure, school verification, URL rewrite, unsupported-label ingestion, profile/contact/research-fact acceptance, or unique-person identity collapse.

## Summary

```json
{
  "by_operator_stage": {
    "active_batch8_source_discovery": 1,
    "active_source_route_inspection": 1,
    "closure_or_discovery": 4,
    "headed_refetch": 1,
    "manual_or_school_specific_lane": 3,
    "manual_rendered_review_or_discovery": 1,
    "manual_scope_review": 1,
    "manual_url_confirmation": 1,
    "official_url_program_page_probe": 1,
    "official_url_route_inspection": 1,
    "program_page_probe": 8,
    "related_scope_rendered_parser_review": 1,
    "related_scope_source_discovery": 1,
    "rendered_parser_review": 3,
    "route_inspection": 9,
    "second_hop_route_inspection": 2,
    "shared_source_crosswalk": 2,
    "source_discovery": 1,
    "source_discovery_route_inspection": 1,
    "targeted_source_discovery": 5
  },
  "by_row_type": {
    "observed_school_pattern": 22,
    "operator_contract": 6,
    "vanderbilt_next_queue": 20
  },
  "by_school": {
    "ALL_TOP50_SCHOOLS": 6,
    "Hopkins": 2,
    "Stanford": 5,
    "UCSF": 2,
    "VANDERBILT UNIVERSITY SCH OF MEDICINE": 20,
    "Vanderbilt": 8,
    "WashU": 2,
    "Yale": 3
  },
  "csv": "artifacts/data/top50_scraper_source_discovery_playbook.csv",
  "gbrain_approval_verified": true,
  "gbrain_decision_effect": "top50_scraper_source_discovery_playbook_non_mutating_approved",
  "gbrain_decision_summary": "## Answer\n\nThe requested non-mutating top-50 scraper/source-discovery playbook packet located at `reports/top50-scraper-source-discovery-playbook-2026-06-07` is approved. The playbook explicitly defines its boundary as authorizing only source discovery, route probing, classification, and packet preparation, while strictly prohibiting person ingestion, training-state mutation, denominator closure, school verification, URL rewrites, unsupported-label ingestion, profile/contact/research-fact acceptance, or unique-person identity collapse [reports/top50-scraper-source-discovery-playbook-2026-06-07].\n\nAPPROVE top50_scraper_source_discovery_playbook_non_mutating_approved ROW_COUNT 48 ROWSET_SHA256 1b33439d36c878a527294dea38b8662bc69d5634c4427ad21ffa878b3db1e355 VANDERBILT_OPEN_GAPS_REPRESENTED 113",
  "gbrain_response_json": "artifacts/data/gbrain_think_top50_scraper_source_discovery_playbook_v6_http_mcp_response.json",
  "gbrain_strategy_answer_excerpt": "### Answer\nBased on the current state of the top-50 medical school roster engine and the user mandate to build an \"exhaustive, autonomous system\" [reports/top-50-medical-roster-engine-gbrain-decision-request-2026-06-05], the Tejas-aligned next operating strategy is to **pivot to Stanford for immediate verification, followed by a discovery improvement pass, before returning to drain Vanderbilt.**\n\n**Rationale:**\n1.  **Immediate Win (Stanford):** Stanford is currently in a high-readiness state with 1,088 accepted membership observations and is actively requesting `stanford_school_verified_next_lane_approved` [reports/stanford-school-readiness-gbrain-packet-2026-06-07]. Completing this transition increases the count of GBrain-verified schools from 5 to 6.\n2.  **Systemic Bottleneck (Vanderbilt):** Vanderbilt remains `school_not_verified` with 121 open denominator gaps [Prompt]. The breakdown of these gaps reveals a heavy reliance on manual and targeted discovery lanes (e.g., `manual_rendered_review_or_targeted_source_discovery` (23), `target_program_source_discovery_after_exclusion` (20), and `program_page_probe` (9)) [Prompt]. This fragmentation suggests that continuing to \"drain\" via",
  "gbrain_strategy_effect": "strategy_advisory_stanford_then_discovery_improvement_then_vanderbilt_no_new_mutation_approval",
  "generated_at": "2026-06-08T02:42:14.639810+00:00",
  "json": "artifacts/data/top50_scraper_source_discovery_playbook.json",
  "markdown": "artifacts/research/top50-scraper-source-discovery-playbook-2026-06-07.md",
  "mutation_allowed": false,
  "policy": "Non-mutating scraper/source-discovery playbook. It authorizes only source discovery, route probing, classification, and packet preparation. It does not authorize person ingestion, training-state mutation, denominator closure, school verification, URL rewrite, unsupported-label ingestion, profile/contact/research-fact acceptance, or unique-person identity collapse.",
  "prior_gbrain_decision_summary": "",
  "rows": 48,
  "rowset_sha256": "1b33439d36c878a527294dea38b8662bc69d5634c4427ad21ffa878b3db1e355",
  "vanderbilt_open_gap_rows_represented": 113,
  "vanderbilt_queue_rows": 20
}
```

## Operator Contracts

| stage | automation | target artifact | next action |
| --- | --- | --- | --- |
| closure_or_discovery | packet_required_no_automatic_closure | artifacts/data/<school>_closure_packet.csv | Prepare no-public-roster closure packet only after exhausting official-domain discovery evidence. |
| program_page_probe | scriptable_static_http_first_headed_browser_on_fetch_or_js_failure | artifacts/data/<school>_program_page_probe.csv | Probe official URL, extract roster links, and classify into exact parser candidate, route inspection, source discovery, or closure packet. |
| rendered_parser_review | scriptable_with_strict_false_positive_filters | artifacts/data/<school>_rendered_parser_review_packet.csv | Build exact acceptance packets only for target-scope current trainee rows and ask GBrain for rowset approval. |
| route_inspection | scriptable_static_http_plus_headed_browser_for_js_or_access_failures | artifacts/data/<school>_roster_route_inspection.csv | Inspect candidate page and second-hop links before any acceptance or terminal closure. |
| shared_source_crosswalk | semi_scriptable_requires_packet_boundary | artifacts/data/<school>_shared_source_crosswalk_packet.csv | Build crosswalk/disposition packet before loading rows from shared pages. |
| targeted_source_discovery | scriptable_search_and_fetch_with_official_domain_filter | artifacts/data/<school>_source_discovery_workbench.csv | Generate query variants, fetch official-domain results, and route evidence to parser review, route inspection, or no-public-roster closure packet. |

## Vanderbilt Next Queue

| lane | stage | gaps | target artifact | next action |
| --- | --- | ---: | --- | --- |
| manual_rendered_review_or_targeted_source_discovery | manual_rendered_review_or_discovery | 19 | artifacts/data/school_gap_resolution_batch_packets.csv#manual_rendered_review_or_targeted_source_discovery | run rendered review first where source is official; otherwise route to source discovery |
| target_program_source_discovery_after_exclusion | targeted_source_discovery | 16 | artifacts/data/vanderbilt_generalized_source_discovery_workbench.csv | run generalized official-domain targeted source discovery with query/observation ledger |
| program_page_probe | program_page_probe | 9 | artifacts/data/vanderbilt_program_page_probe.csv | run generalized program-page probe and classify roster links before manual review |
| target_program_source_discovery_after_mixed_negative_evidence | targeted_source_discovery | 9 | artifacts/data/vanderbilt_generalized_source_discovery_workbench.csv | run generalized official-domain targeted source discovery with query/observation ledger |
| targeted_source_discovery_or_no_public_roster_closure_packet | closure_or_discovery | 8 | artifacts/data/vanderbilt_no_public_roster_or_source_discovery_packet.csv | continue discovery until closure packet evidence is strong enough for GBrain review |
| targeted_source_discovery_after_parent_url_resolution | targeted_source_discovery | 8 | artifacts/data/vanderbilt_generalized_source_discovery_workbench.csv | run generalized official-domain targeted source discovery with query/observation ledger |
| manual_current_scope_review_packet | manual_scope_review | 7 | artifacts/data/school_gap_resolution_batch_packets.csv#manual_current_scope_review_packet | build non-mutating manual scope-review packet with explicit target/related/shared decision |
| rendered_parser_manual_review_after_related_scope_source_discovery | rendered_parser_review | 7 | artifacts/data/vanderbilt_related_scope_rendered_parser_review_packet.csv | run strict rendered parser review and build exact acceptance packet only for target-scope rows |
| target_program_source_discovery_after_parser_exclusion | targeted_source_discovery | 7 | artifacts/data/vanderbilt_generalized_source_discovery_workbench.csv | run generalized official-domain targeted source discovery with query/observation ledger |
| shared_source_program_scope_review_packet | shared_source_crosswalk | 5 | artifacts/data/vanderbilt_shared_source_crosswalk_packet.csv | build shared-source crosswalk/disposition packet before accepting people |
| targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe | closure_or_discovery | 4 | artifacts/data/vanderbilt_no_public_roster_or_source_discovery_packet.csv | continue discovery until closure packet evidence is strong enough for GBrain review |
| manual_url_confirmation_after_official_context_resolution | manual_url_confirmation | 4 | artifacts/data/school_gap_resolution_batch_packets.csv#manual_url_confirmation_after_official_context_resolution | build non-mutating packet or school-specific probe according to manifest lane |
| targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery | closure_or_discovery | 2 | artifacts/data/vanderbilt_no_public_roster_or_source_discovery_packet.csv | continue discovery until closure packet evidence is strong enough for GBrain review |
| linked_route_inspection_after_related_scope_source_discovery | route_inspection | 2 | artifacts/data/vanderbilt_generalized_route_inspection.csv | run headed/static route inspection and split into parser, shared-source, related-scope, or repair packet |
| headed_refetch | headed_refetch | 1 | artifacts/data/school_gap_resolution_batch_packets.csv#headed_refetch | build non-mutating packet or school-specific probe according to manifest lane |
| target_program_source_discovery_after_non_current_exclusion | manual_or_school_specific_lane | 1 | artifacts/data/school_gap_resolution_batch_packets.csv#target_program_source_discovery_after_non_current_exclusion | build non-mutating packet or school-specific probe according to manifest lane |
| target_program_source_discovery_after_official_url_probe_exclusion | manual_or_school_specific_lane | 1 | artifacts/data/school_gap_resolution_batch_packets.csv#target_program_source_discovery_after_official_url_probe_exclusion | build non-mutating packet or school-specific probe according to manifest lane |
| target_program_source_discovery_after_official_url_probe_related_scope | manual_or_school_specific_lane | 1 | artifacts/data/school_gap_resolution_batch_packets.csv#target_program_source_discovery_after_official_url_probe_related_scope | build non-mutating packet or school-specific probe according to manifest lane |
| rendered_parser_manual_repair_after_official_url_probe | rendered_parser_review | 1 | artifacts/data/vanderbilt_related_scope_rendered_parser_review_packet.csv | run strict rendered parser review and build exact acceptance packet only for target-scope rows |
| second_hop_route_inspection_after_official_url_probe | route_inspection | 1 | artifacts/data/vanderbilt_generalized_route_inspection.csv | run headed/static route inspection and split into parser, shared-source, related-scope, or repair packet |
