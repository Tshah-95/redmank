---
type: research-checkpoint
title: Vanderbilt Reviewer Decision Patch Workbook Slice Index
created_at: 2026-06-09T07:04:03.560983+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Reviewer Decision Patch Workbook Slice Index

## Boundary

Non-mutating Vanderbilt reviewer workbook slice index. It lists one bounded slice command per public reviewer operator packet and writes slices to /tmp by default. It does not fill reviewer decisions, include reviewer notes, publish raw candidate names or URLs, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "by_review_queue_lane": {
    "candidate_fingerprint_review": 16,
    "linked_scope_metadata_review": 3,
    "route_recourse_review": 1
  },
  "csv": "artifacts/data/vanderbilt_reviewer_decision_patch_workbook_slice_index.csv",
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T07:04:03.560983+00:00",
  "json": "artifacts/data/vanderbilt_reviewer_decision_patch_workbook_slice_index.json",
  "markdown": "artifacts/research/vanderbilt-reviewer-decision-patch-workbook-slice-index-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt reviewer workbook slice index. It lists one bounded slice command per public reviewer operator packet and writes slices to /tmp by default. It does not fill reviewer decisions, include reviewer notes, publish raw candidate names or URLs, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, or collapse identities.",
  "raw_candidate_names_committed": false,
  "raw_person_urls_committed": false,
  "reviewer_note_column_committed": false,
  "rowset_sha256": "d16ccc0adbb0be4a5fd5b59bdcf82ecb976e1d032baa1d3c9d92bf861c4179c4",
  "school_verification_allowed": false,
  "slice_index_rows": 20,
  "slice_outputs_default_tmp_only": true,
  "source_operator_packet_rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
  "source_operator_packet_summary": "artifacts/data/vanderbilt_public_reviewer_operator_packet_summary.json",
  "source_workbook_rowset_sha256": "18619a07cc9bf02fba3cf898dc3d21252b25f9c4a8adfb0d88d126a506bed3c3",
  "source_workbook_summary": "artifacts/data/vanderbilt_reviewer_decision_patch_workbook_summary.json",
  "workbook_rows_represented": 159
}
```

## Slices

| order | program | lane | rows | slice command |
| ---: | --- | --- | ---: | --- |
| 1 | Academic General Pediatrics | candidate_fingerprint_review | 4 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 1 --output /tmp/vanderbilt_reviewer_workbook_order_1.csv` |
| 2 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | 4 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 2 --output /tmp/vanderbilt_reviewer_workbook_order_2.csv` |
| 3 | Gastroenterology | candidate_fingerprint_review | 10 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 3 --output /tmp/vanderbilt_reviewer_workbook_order_3.csv` |
| 4 | General Surgery | candidate_fingerprint_review | 2 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 4 --output /tmp/vanderbilt_reviewer_workbook_order_4.csv` |
| 5 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | 19 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 5 --output /tmp/vanderbilt_reviewer_workbook_order_5.csv` |
| 6 | Pediatric Critical Care | candidate_fingerprint_review | 17 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 6 --output /tmp/vanderbilt_reviewer_workbook_order_6.csv` |
| 7 | Pediatric Emergency Medicine | candidate_fingerprint_review | 17 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 7 --output /tmp/vanderbilt_reviewer_workbook_order_7.csv` |
| 8 | Pediatric Endocrinology | candidate_fingerprint_review | 3 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 8 --output /tmp/vanderbilt_reviewer_workbook_order_8.csv` |
| 9 | Pediatric Gastroenterology | candidate_fingerprint_review | 12 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 9 --output /tmp/vanderbilt_reviewer_workbook_order_9.csv` |
| 10 | Pediatric Hospital Medicine | candidate_fingerprint_review | 4 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 10 --output /tmp/vanderbilt_reviewer_workbook_order_10.csv` |
| 11 | Pediatric Infectious Diseases | candidate_fingerprint_review | 10 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 11 --output /tmp/vanderbilt_reviewer_workbook_order_11.csv` |
| 12 | Pediatric Rheumatology | candidate_fingerprint_review | 4 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 12 --output /tmp/vanderbilt_reviewer_workbook_order_12.csv` |
| 13 | Pediatrics | candidate_fingerprint_review | 26 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 13 --output /tmp/vanderbilt_reviewer_workbook_order_13.csv` |
| 14 | Psychiatry | candidate_fingerprint_review | 9 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 14 --output /tmp/vanderbilt_reviewer_workbook_order_14.csv` |
| 15 | Rheumatology | candidate_fingerprint_review | 4 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 15 --output /tmp/vanderbilt_reviewer_workbook_order_15.csv` |
| 16 | Transplant Hepatology | candidate_fingerprint_review | 10 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 16 --output /tmp/vanderbilt_reviewer_workbook_order_16.csv` |
| 17 | Advanced Endoscopy | linked_scope_metadata_review | 1 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 17 --output /tmp/vanderbilt_reviewer_workbook_order_17.csv` |
| 18 | Advanced Inflammatory Bowel Disease | linked_scope_metadata_review | 1 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 18 --output /tmp/vanderbilt_reviewer_workbook_order_18.csv` |
| 19 | Orthopaedic Surgery | linked_scope_metadata_review | 1 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 19 --output /tmp/vanderbilt_reviewer_workbook_order_19.csv` |
| 20 | Orthopaedic Surgery | route_recourse_review | 1 | `python3 scripts/slice_vanderbilt_reviewer_decision_patch_workbook.py --execution-order 20 --output /tmp/vanderbilt_reviewer_workbook_order_20.csv` |
