---
type: research-checkpoint
title: Vanderbilt Open Gap Manifest Triage Packet
created_at: 2026-06-09T11:00:38.823773+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Open Gap Manifest Triage Packet

## Boundary

Non-mutating Vanderbilt open-gap manifest triage packet. It ranks the committed 21 Vanderbilt gap-resolution batch slices covering 113 open gaps and records slice-definition boundaries for contributor execution. It does not fetch web pages, fill reviewer decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw dumps, or collapse identities.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_triage_family": {
    "official_url_confirmation": 1,
    "route_parser_or_rendered_review": 3,
    "scope_or_shared_source_review": 2,
    "source_discovery_or_program_probe": 15
  },
  "critical_rows": 3,
  "csv": "artifacts/data/vanderbilt_open_gap_manifest_triage_packet.csv",
  "denominator_closure_allowed": false,
  "gap_rows_by_triage_family": {
    "official_url_confirmation": 4,
    "route_parser_or_rendered_review": 3,
    "scope_or_shared_source_review": 12,
    "source_discovery_or_program_probe": 94
  },
  "gap_rows_represented": 113,
  "gbrain_advisory_effect": "gbrain_selected_vanderbilt_open_gap_manifest_triage_packet_option_b",
  "generated_at": "2026-06-09T11:00:38.823773+00:00",
  "high_rows": 5,
  "identity_collapse_allowed": false,
  "json": "artifacts/data/vanderbilt_open_gap_manifest_triage_packet.json",
  "low_rows": 13,
  "markdown": "artifacts/research/vanderbilt-open-gap-manifest-triage-packet-2026-06-09.md",
  "medium_rows": 0,
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt open-gap manifest triage packet. It ranks the committed 21 Vanderbilt gap-resolution batch slices covering 113 open gaps and records slice-definition boundaries for contributor execution. It does not fetch web pages, fill reviewer decisions, apply patches, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, publish raw dumps, or collapse identities.",
  "private_artifact_paths_committed": false,
  "raw_dump_publication_allowed": false,
  "rowset_sha256": "b89f2278c96c18c70403099be2b18542bb0f59a4c50a53921f17fe83864b1391",
  "school_verification_allowed": false,
  "slice_definition_contract_summary": "artifacts/data/vanderbilt_triage_slice_definition_contract_summary.json",
  "slice_outputs_default_tmp_only": true,
  "source_batch_summary": "artifacts/data/school_gap_resolution_batch_summary.json",
  "source_manifest_summary": "artifacts/data/school_gap_resolution_manifest_summary.json",
  "source_packet_summary": "artifacts/data/school_gap_resolution_batch_packet_summary.json",
  "source_slice_index_rowset_sha256": "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75",
  "source_slice_summary": "artifacts/data/school_gap_resolution_batch_slice_index_summary.json",
  "triage_rows": 21,
  "url_rewrite_allowed": false
}
```

## Triage Slices

| triage | source order | family | lane | gaps | command |
| ---: | ---: | --- | --- | ---: | --- |
| 1 | 2 | source_discovery_or_program_probe | manual_rendered_review_or_targeted_source_discovery | 18 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 2 --output /tmp/school_gap_resolution_batch_order_2.csv` |
| 2 | 1 | source_discovery_or_program_probe | target_program_source_discovery_after_mixed_negative_evidence | 9 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 1 --output /tmp/school_gap_resolution_batch_order_1.csv` |
| 3 | 3 | source_discovery_or_program_probe | linked_route_inspection_after_related_scope_source_discovery | 2 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 3 --output /tmp/school_gap_resolution_batch_order_3.csv` |
| 4 | 5 | source_discovery_or_program_probe | rendered_parser_manual_review_after_related_scope_source_discovery | 7 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 5 --output /tmp/school_gap_resolution_batch_order_5.csv` |
| 5 | 7 | source_discovery_or_program_probe | target_program_source_discovery_after_exclusion | 16 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 7 --output /tmp/school_gap_resolution_batch_order_7.csv` |
| 6 | 4 | source_discovery_or_program_probe | manual_rendered_review_or_targeted_source_discovery | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 4 --output /tmp/school_gap_resolution_batch_order_4.csv` |
| 7 | 8 | source_discovery_or_program_probe | targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery | 2 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 8 --output /tmp/school_gap_resolution_batch_order_8.csv` |
| 8 | 6 | scope_or_shared_source_review | shared_source_program_scope_review_packet | 5 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 6 --output /tmp/school_gap_resolution_batch_order_6.csv` |
| 9 | 9 | source_discovery_or_program_probe | program_page_probe | 9 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 9 --output /tmp/school_gap_resolution_batch_order_9.csv` |
| 10 | 11 | source_discovery_or_program_probe | targeted_source_discovery_after_parent_url_resolution | 8 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 11 --output /tmp/school_gap_resolution_batch_order_11.csv` |
| 11 | 12 | source_discovery_or_program_probe | targeted_source_discovery_or_no_public_roster_closure_packet | 8 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 12 --output /tmp/school_gap_resolution_batch_order_12.csv` |
| 12 | 10 | source_discovery_or_program_probe | target_program_source_discovery_after_parser_exclusion | 7 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 10 --output /tmp/school_gap_resolution_batch_order_10.csv` |
| 13 | 19 | source_discovery_or_program_probe | target_program_source_discovery_after_official_url_probe_exclusion | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 19 --output /tmp/school_gap_resolution_batch_order_19.csv` |
| 14 | 20 | source_discovery_or_program_probe | target_program_source_discovery_after_official_url_probe_related_scope | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 20 --output /tmp/school_gap_resolution_batch_order_20.csv` |
| 15 | 17 | route_parser_or_rendered_review | second_hop_route_inspection_after_official_url_probe | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 17 --output /tmp/school_gap_resolution_batch_order_17.csv` |
| 16 | 18 | source_discovery_or_program_probe | target_program_source_discovery_after_non_current_exclusion | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 18 --output /tmp/school_gap_resolution_batch_order_18.csv` |
| 17 | 21 | source_discovery_or_program_probe | targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe | 4 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 21 --output /tmp/school_gap_resolution_batch_order_21.csv` |
| 18 | 13 | route_parser_or_rendered_review | headed_refetch | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 13 --output /tmp/school_gap_resolution_batch_order_13.csv` |
| 19 | 16 | route_parser_or_rendered_review | rendered_parser_manual_repair_after_official_url_probe | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 16 --output /tmp/school_gap_resolution_batch_order_16.csv` |
| 20 | 14 | scope_or_shared_source_review | manual_current_scope_review_packet | 7 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 14 --output /tmp/school_gap_resolution_batch_order_14.csv` |
| 21 | 15 | official_url_confirmation | manual_url_confirmation_after_official_context_resolution | 4 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 15 --output /tmp/school_gap_resolution_batch_order_15.csv` |
