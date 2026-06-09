---
type: research-checkpoint
title: Vanderbilt Candidate Only Parser Outputs
created_at: 2026-06-09T05:09:16.700734+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Candidate Only Parser Outputs

## Boundary

Approved Vanderbilt candidate-only parser diagnostics. This artifact may contain candidate fingerprints, counts, href hashes, route hashes, scope metadata, and recourse rows only. It contains no raw candidate names, raw person URLs, accepted person rows, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_candidate_source_kind": {
    "heading_signal": 131,
    "none": 4,
    "profile_anchor": 98
  },
  "by_output_kind": {
    "candidate_fingerprint": 229,
    "route_recourse": 1,
    "scope_metadata": 3
  },
  "by_parser_status": {
    "candidate_only_parser_emitted_fingerprint": 229,
    "recourse_recorded_no_parser_output": 1,
    "scope_metadata_recorded_no_parser_output": 3
  },
  "by_program_output_rows": {
    "Academic General Pediatrics": 4,
    "Advanced Endoscopy": 1,
    "Advanced Inflammatory Bowel Disease": 1,
    "Developmental-Behavioral Pediatrics": 6,
    "Gastroenterology": 10,
    "General Surgery": 2,
    "Neonatal-Perinatal Medicine": 32,
    "Orthopaedic Surgery": 2,
    "Pediatric Critical Care": 28,
    "Pediatric Emergency Medicine": 28,
    "Pediatric Endocrinology": 3,
    "Pediatric Gastroenterology": 18,
    "Pediatric Hospital Medicine": 6,
    "Pediatric Infectious Diseases": 14,
    "Pediatric Rheumatology": 6,
    "Pediatrics": 47,
    "Psychiatry": 9,
    "Rheumatology": 6,
    "Transplant Hepatology": 10
  },
  "candidate_fingerprint_rows": 229,
  "csv": "artifacts/data/vanderbilt_candidate_only_parser_outputs.csv",
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T05:09:16.700734+00:00",
  "json": "artifacts/data/vanderbilt_candidate_only_parser_outputs.json",
  "markdown": "artifacts/research/vanderbilt-candidate-only-parser-outputs-2026-06-09.md",
  "mutation_allowed": false,
  "parser_output_rows": 233,
  "person_ingestion_allowed": false,
  "policy": "Approved Vanderbilt candidate-only parser diagnostics. This artifact may contain candidate fingerprints, counts, href hashes, route hashes, scope metadata, and recourse rows only. It contains no raw candidate names, raw person URLs, accepted person rows, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "raw_candidate_hrefs_committed": false,
  "raw_candidate_names_committed": false,
  "rowset_sha256": "312918a4b812f82bbf858a0b5c50d5d04394fa8be634a1a0cc9a7ad6aaa2f034",
  "source_approval_rows": 20,
  "source_implementation_approval_packet": "artifacts/data/vanderbilt_parser_scope_implementation_approval_packet.json",
  "source_implementation_approval_rowset_sha256": "0ce935b64a7eb2153b4fb4b5a8cca47034bab839aa932c8951c29d3bda363b40",
  "source_implementation_approval_summary": "artifacts/data/vanderbilt_parser_scope_implementation_approval_packet_summary.json",
  "unique_fetch_urls": 16
}
```

## Output Rows

| program | kind | parser status | candidate index | source kind | accepted person |
| --- | --- | --- | ---: | --- | --- |
| Academic General Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Academic General Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Academic General Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Academic General Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | profile_anchor | false |
| Advanced Endoscopy | scope_metadata | scope_metadata_recorded_no_parser_output | 0 | none | false |
| Advanced Inflammatory Bowel Disease | scope_metadata | scope_metadata_recorded_no_parser_output | 0 | none | false |
| Developmental-Behavioral Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Developmental-Behavioral Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Developmental-Behavioral Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Developmental-Behavioral Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | profile_anchor | false |
| Developmental-Behavioral Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | profile_anchor | false |
| Developmental-Behavioral Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | profile_anchor | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 7 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 8 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 9 | heading_signal | false |
| Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 10 | heading_signal | false |
| General Surgery | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| General Surgery | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 7 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 8 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 9 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 10 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 11 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 12 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 13 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 14 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 15 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 16 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 17 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 18 | heading_signal | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 19 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 20 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 21 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 22 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 23 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 24 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 25 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 26 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 27 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 28 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 29 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 30 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 31 | profile_anchor | false |
| Neonatal-Perinatal Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 32 | profile_anchor | false |
| Orthopaedic Surgery | route_recourse | recourse_recorded_no_parser_output | 0 | none | false |
| Orthopaedic Surgery | scope_metadata | scope_metadata_recorded_no_parser_output | 0 | none | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 7 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 8 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 9 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 10 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 11 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 12 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 13 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 14 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 15 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 16 | heading_signal | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 17 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 18 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 19 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 20 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 21 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 22 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 23 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 24 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 25 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 26 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 27 | profile_anchor | false |
| Pediatric Critical Care | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 28 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 7 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 8 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 9 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 10 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 11 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 12 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 13 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 14 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 15 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 16 | heading_signal | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 17 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 18 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 19 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 20 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 21 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 22 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 23 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 24 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 25 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 26 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 27 | profile_anchor | false |
| Pediatric Emergency Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 28 | profile_anchor | false |
| Pediatric Endocrinology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Pediatric Endocrinology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Pediatric Endocrinology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | profile_anchor | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 7 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 8 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 9 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 10 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 11 | heading_signal | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 12 | profile_anchor | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 13 | profile_anchor | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 14 | profile_anchor | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 15 | profile_anchor | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 16 | profile_anchor | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 17 | profile_anchor | false |
| Pediatric Gastroenterology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 18 | profile_anchor | false |
| Pediatric Hospital Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Pediatric Hospital Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Pediatric Hospital Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Pediatric Hospital Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | profile_anchor | false |
| Pediatric Hospital Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | profile_anchor | false |
| Pediatric Hospital Medicine | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | profile_anchor | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 7 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 8 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 9 | heading_signal | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 10 | profile_anchor | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 11 | profile_anchor | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 12 | profile_anchor | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 13 | profile_anchor | false |
| Pediatric Infectious Diseases | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 14 | profile_anchor | false |
| Pediatric Rheumatology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Pediatric Rheumatology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Pediatric Rheumatology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Pediatric Rheumatology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | profile_anchor | false |
| Pediatric Rheumatology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | profile_anchor | false |
| Pediatric Rheumatology | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 1 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 2 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 3 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 4 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 5 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 6 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 7 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 8 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 9 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 10 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 11 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 12 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 13 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 14 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 15 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 16 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 17 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 18 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 19 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 20 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 21 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 22 | heading_signal | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 23 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 24 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 25 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 26 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 27 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 28 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 29 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 30 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 31 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 32 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 33 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 34 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 35 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 36 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 37 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 38 | profile_anchor | false |
| Pediatrics | candidate_fingerprint | candidate_only_parser_emitted_fingerprint | 39 | profile_anchor | false |
