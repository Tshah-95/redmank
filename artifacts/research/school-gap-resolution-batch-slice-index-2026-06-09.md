---
type: research-checkpoint
title: School Gap Resolution Batch Slice Index
created_at: 2026-06-09T07:14:00.900260+00:00
project: top-50-medical-school-roster-engine
---

# School Gap Resolution Batch Slice Index

## Boundary

Non-mutating school gap-resolution batch slice index. It lists one bounded /tmp slice command per committed Vanderbilt gap-resolution batch. It may reference public official-source URLs already committed in gap packets, but it does not fetch web pages, fill reviewer decisions, approve people, ingest people, close denominators, verify schools, rewrite URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "by_next_operator_lane": {
    "headed_refetch": 1,
    "linked_route_inspection_after_related_scope_source_discovery": 1,
    "manual_current_scope_review_packet": 1,
    "manual_rendered_review_or_targeted_source_discovery": 2,
    "manual_url_confirmation_after_official_context_resolution": 1,
    "program_page_probe": 1,
    "rendered_parser_manual_repair_after_official_url_probe": 1,
    "rendered_parser_manual_review_after_related_scope_source_discovery": 1,
    "second_hop_route_inspection_after_official_url_probe": 1,
    "shared_source_program_scope_review_packet": 1,
    "target_program_source_discovery_after_exclusion": 1,
    "target_program_source_discovery_after_mixed_negative_evidence": 1,
    "target_program_source_discovery_after_non_current_exclusion": 1,
    "target_program_source_discovery_after_official_url_probe_exclusion": 1,
    "target_program_source_discovery_after_official_url_probe_related_scope": 1,
    "target_program_source_discovery_after_parser_exclusion": 1,
    "targeted_source_discovery_after_parent_url_resolution": 1,
    "targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe": 1,
    "targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery": 1,
    "targeted_source_discovery_or_no_public_roster_closure_packet": 1
  },
  "csv": "artifacts/data/school_gap_resolution_batch_slice_index.csv",
  "denominator_closure_allowed": false,
  "gap_rows_represented": 113,
  "generated_at": "2026-06-09T07:14:00.900260+00:00",
  "identity_collapse_allowed": false,
  "json": "artifacts/data/school_gap_resolution_batch_slice_index.json",
  "markdown": "artifacts/research/school-gap-resolution-batch-slice-index-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating school gap-resolution batch slice index. It lists one bounded /tmp slice command per committed Vanderbilt gap-resolution batch. It may reference public official-source URLs already committed in gap packets, but it does not fetch web pages, fill reviewer decisions, approve people, ingest people, close denominators, verify schools, rewrite URLs, accept enrichment facts, or collapse identities.",
  "private_artifact_paths_committed": false,
  "public_urls_may_be_present_in_packet_slices": true,
  "reviewer_note_column_committed": false,
  "rowset_sha256": "2442accacb8ff67df1d2df3915c737af70e0186f11b9750c0d52c6b819c2cb75",
  "school_verification_allowed": false,
  "slice_index_rows": 21,
  "slice_outputs_default_tmp_only": true,
  "source_batch_summary": "artifacts/data/school_gap_resolution_batch_summary.json",
  "source_manifest_summary": "artifacts/data/school_gap_resolution_manifest_summary.json",
  "source_packet_summary": "artifacts/data/school_gap_resolution_batch_packet_summary.json",
  "url_rewrite_allowed": false
}
```

## Slices

| order | lane | category | gaps | slice command |
| ---: | --- | --- | ---: | --- |
| 1 | target_program_source_discovery_after_mixed_negative_evidence | mixed_negative_route_evidence_recorded_source_discovery_needed | 9 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 1 --output /tmp/school_gap_resolution_batch_order_1.csv` |
| 2 | manual_rendered_review_or_targeted_source_discovery | negative_route_evidence_recorded_manual_or_source_discovery_needed | 18 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 2 --output /tmp/school_gap_resolution_batch_order_2.csv` |
| 3 | linked_route_inspection_after_related_scope_source_discovery | open_gap_linked_route_inspection_after_related_scope_source_discovery | 2 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 3 --output /tmp/school_gap_resolution_batch_order_3.csv` |
| 4 | manual_rendered_review_or_targeted_source_discovery | open_gap_manual_rendered_review_or_targeted_source_discovery_needed | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 4 --output /tmp/school_gap_resolution_batch_order_4.csv` |
| 5 | rendered_parser_manual_review_after_related_scope_source_discovery | open_gap_rendered_parser_review_after_related_scope_source_discovery | 7 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 5 --output /tmp/school_gap_resolution_batch_order_5.csv` |
| 6 | shared_source_program_scope_review_packet | shared_or_related_program_scope_review_needed | 5 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 6 --output /tmp/school_gap_resolution_batch_order_6.csv` |
| 7 | target_program_source_discovery_after_exclusion | faculty_leadership_exclusion_recorded_source_discovery_needed | 16 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 7 --output /tmp/school_gap_resolution_batch_order_7.csv` |
| 8 | targeted_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery | open_gap_source_discovery_or_no_public_roster_closure_after_related_scope_source_discovery | 2 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 8 --output /tmp/school_gap_resolution_batch_order_8.csv` |
| 9 | program_page_probe | first_hop_program_probe_needed | 9 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 9 --output /tmp/school_gap_resolution_batch_order_9.csv` |
| 10 | target_program_source_discovery_after_parser_exclusion | faculty_leadership_parser_exclusion_recorded_source_discovery_needed | 7 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 10 --output /tmp/school_gap_resolution_batch_order_10.csv` |
| 11 | targeted_source_discovery_after_parent_url_resolution | official_parent_url_resolution_recorded_source_discovery_needed | 8 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 11 --output /tmp/school_gap_resolution_batch_order_11.csv` |
| 12 | targeted_source_discovery_or_no_public_roster_closure_packet | no_current_roster_probe_recorded_source_discovery_or_closure_needed | 8 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 12 --output /tmp/school_gap_resolution_batch_order_12.csv` |
| 13 | headed_refetch | retry_or_refetch_needed | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 13 --output /tmp/school_gap_resolution_batch_order_13.csv` |
| 14 | manual_current_scope_review_packet | manual_current_scope_review_needed_after_parser_probe | 7 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 14 --output /tmp/school_gap_resolution_batch_order_14.csv` |
| 15 | manual_url_confirmation_after_official_context_resolution | official_context_url_resolution_recorded_manual_confirmation_needed | 4 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 15 --output /tmp/school_gap_resolution_batch_order_15.csv` |
| 16 | rendered_parser_manual_repair_after_official_url_probe | official_url_probe_rendered_parser_manual_needed | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 16 --output /tmp/school_gap_resolution_batch_order_16.csv` |
| 17 | second_hop_route_inspection_after_official_url_probe | official_url_probe_route_second_hop_inspection_needed | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 17 --output /tmp/school_gap_resolution_batch_order_17.csv` |
| 18 | target_program_source_discovery_after_non_current_exclusion | non_current_parser_exclusion_recorded_source_discovery_needed | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 18 --output /tmp/school_gap_resolution_batch_order_18.csv` |
| 19 | target_program_source_discovery_after_official_url_probe_exclusion | official_url_probe_route_faculty_leadership_recorded_source_discovery_needed | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 19 --output /tmp/school_gap_resolution_batch_order_19.csv` |
| 20 | target_program_source_discovery_after_official_url_probe_related_scope | official_url_probe_route_related_scope_recorded_source_discovery_needed | 1 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 20 --output /tmp/school_gap_resolution_batch_order_20.csv` |
| 21 | targeted_source_discovery_or_no_public_roster_closure_after_official_url_probe | official_url_probe_no_roster_signal_source_discovery_or_closure_needed | 4 | `python3 scripts/slice_school_gap_resolution_batch_packets.py --execution-order 21 --output /tmp/school_gap_resolution_batch_order_21.csv` |
