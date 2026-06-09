---
type: research-checkpoint
title: Vanderbilt Candidate Review Decision Scaffold
created_at: 2026-06-09T05:29:58.024935+00:00
project: top-50-medical-school-roster-engine
school: Vanderbilt University School of Medicine
---

# Vanderbilt Candidate Review Decision Scaffold

## Boundary

Non-mutating Vanderbilt candidate review decision scaffold. It creates pending reviewer-decision rows and blank decision templates for hashed candidate fingerprints, linked-scope metadata, and route recourse rows. It does not approve raw candidate labels, raw person URLs, accepted person rows, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.

## Summary

```json
{
  "accepted_person_rows": 0,
  "by_decision_status": {
    "pending_non_mutating_reviewer_decision": 159
  },
  "by_program_decision_rows": {
    "Academic General Pediatrics": 4,
    "Advanced Endoscopy": 1,
    "Advanced Inflammatory Bowel Disease": 1,
    "Developmental-Behavioral Pediatrics": 4,
    "Gastroenterology": 10,
    "General Surgery": 2,
    "Neonatal-Perinatal Medicine": 19,
    "Orthopaedic Surgery": 2,
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
  "by_review_queue_lane": {
    "candidate_fingerprint_review": 155,
    "linked_scope_metadata_review": 3,
    "route_recourse_review": 1
  },
  "csv": "artifacts/data/vanderbilt_candidate_review_decision_scaffold.csv",
  "decision_scaffold_rows": 159,
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T05:29:58.024935+00:00",
  "json": "artifacts/data/vanderbilt_candidate_review_decision_scaffold.json",
  "manual_decision_template_rows": 159,
  "manual_decisions_csv": "artifacts/data/vanderbilt_candidate_reviewer_decisions.csv",
  "manual_decisions_json": "artifacts/data/vanderbilt_candidate_reviewer_decisions.json",
  "markdown": "artifacts/research/vanderbilt-candidate-review-decision-scaffold-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt candidate review decision scaffold. It creates pending reviewer-decision rows and blank decision templates for hashed candidate fingerprints, linked-scope metadata, and route recourse rows. It does not approve raw candidate labels, raw person URLs, accepted person rows, person ingestion, training-state mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, enrichment acceptance, raw dump publication, or unique-person identity collapse.",
  "raw_candidate_names_committed": false,
  "raw_person_urls_committed": false,
  "review_batch_count": 20,
  "rowset_sha256": "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938",
  "source_review_queue_rows": 159,
  "source_review_queue_rowset_sha256": "b74b337bfa43406d8a200956d469eb5dc0d41902c197f78af85001f18750b148",
  "source_review_queue_summary": "artifacts/data/vanderbilt_candidate_review_queue_summary.json",
  "source_review_queues": "artifacts/data/vanderbilt_candidate_review_queues.json"
}
```

## Decision Scaffold Rows

| priority | program | lane | status | manual row |
| ---: | --- | --- | --- | --- |
| 90 | Academic General Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_bdc4f62970c7eb142413 |
| 90 | Academic General Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_4064b8c50348aa1e8f9a |
| 90 | Academic General Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_cd36852868ed255dffa3 |
| 90 | Academic General Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_64720c5a5f44fe7cc522 |
| 90 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_5bc100b3c28e5ca6a39f |
| 90 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f71f5ec5c86da430c633 |
| 90 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_9e40693f7538a38d1491 |
| 90 | Developmental-Behavioral Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_2241afa21e19e80a60b3 |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_cd1f8f0e8ebee89eb5a9 |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f9824841462cee1cfe36 |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_56820b78dd600cb14786 |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_99a49324e6ddb002948d |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_786e533f5a1129b2e8db |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_143d950856b53ff8e77e |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_ff3981f51e60b20073e5 |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1f940c7a900537b18dd3 |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_dea0ea21f10ff6a40dfc |
| 90 | Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c10790d7c74912ac55fe |
| 90 | General Surgery | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_6f12df3d4fb193d7332d |
| 90 | General Surgery | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_df3d7a97dd81a5e1a202 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_7cb8f6347db55fcef3cc |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_b794902e2d3e6d7fef6f |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_0de73cce2256fecf6d9a |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_8d9f0f540559de0b1993 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_8deb608791eaa8a54fc2 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c559e9b2e38014268c75 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_7d4e81cf8a6b61092509 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_8933824f55b87200aa94 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_31a80bed45e2f2532b5f |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_a72b614cf1c2f3ef7440 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f9963a5ae4a8c10e3688 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_0588b8016515e8e9d817 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c8d1412b9a31fcc1f723 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_9929f8231caf5291b189 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_bb848b009ce6e7087c9d |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_11e956e154816cefa013 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_a3b22e9cf9c2060e6ac0 |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_076850032ce8a6bdf46b |
| 90 | Neonatal-Perinatal Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f0ad43b977a28be192d2 |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_a3f1951532d6ea26081c |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1c991b84f6ae229235f0 |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_e892bee2d863be259d18 |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_b7f945c7c6b2c778e335 |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_08e9e929c74db144c690 |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_34c539b1aaffb69b2c2a |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_a8bf0204327b953973cd |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_044a9c6190f11cf535f6 |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_873049e5ccde8d2d45fc |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_44ecd5a4b6246f90b452 |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_9c1f1f14e033a95b31ee |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_59c9fbb941f29fa9c472 |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_88589a5725325a6ccd3d |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_77dc4a401a6a35299c2a |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f1beee533c80c2a950ed |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_a104e19512e559febb1c |
| 90 | Pediatric Critical Care | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f412e1e197a3844a8dd6 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_6ee31495fbfd6c3ee378 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_b7eaf35d13b1d4150058 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f046f91f7abc807134a3 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_13a2138a24bf41bbbff5 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_2983a5c364311fad6ad9 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_95ab198df60f2ae05921 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_117552caf1886eb5b00a |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_d072283948efbbc9296a |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_8bedb8b701c282edb7bd |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c26608a5b7629c8ddf3a |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c3ec56fc866e3017ab56 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_67578fb2b6925ca788a0 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_15558823f0cfbc4a4018 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_9ff2d13d2e9f9637292a |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f5a28461c9d159168959 |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_ceab5ba77e0cbc674f4f |
| 90 | Pediatric Emergency Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_9f402606bd088c1f40b2 |
| 90 | Pediatric Endocrinology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_05a4e3d6215ba89b32bc |
| 90 | Pediatric Endocrinology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_209a2e643d6ccdef0e2f |
| 90 | Pediatric Endocrinology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_4aac191f55711ebab45a |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_49df105b86c4bc9a926d |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_85a9e57f12a519a0239a |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_6806d2dd4434d72d6daa |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_85243c734e0434885fb7 |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c57b0dc2a64af51d17e4 |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_ab3fcad794ce1cc6b287 |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_6378fa11f6c5686ce2fa |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1c27c6d48941791b15b3 |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_cef4ed69bca1364e1246 |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_912234a0e5968f89adf8 |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c4d6717a7684805b7b98 |
| 90 | Pediatric Gastroenterology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_748532dd8ea61cb32e7f |
| 90 | Pediatric Hospital Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1cea0ee5677b7572bf2a |
| 90 | Pediatric Hospital Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_a490fc9883a26deb2bfd |
| 90 | Pediatric Hospital Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1a2b03b02e6eefd08289 |
| 90 | Pediatric Hospital Medicine | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_4a67985ea9291ac901b4 |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f41dacaaab5500a892ee |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_de86f4059f334b73fb09 |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_afd6a61487c1526efc54 |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_761009de715b9716e9e8 |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_85c00159cd7307b27ebe |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c93657ec34a17dc68ad5 |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_607dfa03362f41e0c7e9 |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_d01ddd8ec876abf1ac27 |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c680d6ac9f9e7c226843 |
| 90 | Pediatric Infectious Diseases | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1513604bafe574333957 |
| 90 | Pediatric Rheumatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1077cbf238fc18784aa3 |
| 90 | Pediatric Rheumatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_644e74affc7ac5181ad1 |
| 90 | Pediatric Rheumatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_da695063db2848598172 |
| 90 | Pediatric Rheumatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_4988013c59c100445e1f |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_65de70b1ebdd0e355704 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f35eea5674758fdedbd4 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_0a607f356578addb84a1 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_cacf52af403e5450323f |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_8877dc5d08299c228cf4 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_59abfd699aec2ce81de2 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_fa3ee36ba0a2fdd7bc8e |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_77e8eeaec474cef7bf25 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_da19bdede0cc39409205 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_5870b8f62e2dd0f58379 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_61682d72040b2bd2a5e1 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_b7d4c257c751ab6b1201 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_90fe7a19afe4f98352d0 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_ba815b5776970eede34c |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_824218168269dd97455b |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1d1ff4bee76841c437ba |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_17a077d5387b6610b166 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_f0ed676b5e542593e43c |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_280c907c8d3b406a02a5 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_9c75d066432ec3c31467 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_d853f57e0ffefc1f901c |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_9ad94f8e7719327a00f8 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c5d68c671b21c80f7a9f |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_bfbc6dacf37c548e5fef |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_41bc7335a0d7d9288088 |
| 90 | Pediatrics | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_5ad0992a650b2a678c33 |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_b0710ce12e8dbc33bdf7 |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_00305373b0fe1e44a129 |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_afdf97b988297afbab6f |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_2778e62fdb93042245cb |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_30c3989728a3ef1e161f |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_722dc48a646d5231f0ae |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_41a237be99fc306cbc45 |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_d5171386cd9a56a20015 |
| 90 | Psychiatry | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_6c95b5bba7b241656a5c |
| 90 | Rheumatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_2bd835d04703caeb21da |
| 90 | Rheumatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_6b67e4cd2c5f4c81dd9d |
| 90 | Rheumatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_db30ba83e8c0cfccec71 |
| 90 | Rheumatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_4951e15682e2090061ae |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_2e8fd4470fe9f0426d29 |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_c49eeb9774a46d0d479c |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_6a1b681d7a868202e26b |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_4bd3ab3e567e186344c3 |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_62ca061845b586055fe2 |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_1074d7c46baa176a3cc1 |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_23eb4f2e7398d00b74fa |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_33ca2f64724befb47647 |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_54b04e0e3a60a114bf7d |
| 90 | Transplant Hepatology | candidate_fingerprint_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_4beed575b79cab19cc19 |
| 70 | Advanced Endoscopy | linked_scope_metadata_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_34f010a0ce64ef87824d |
| 70 | Advanced Inflammatory Bowel Disease | linked_scope_metadata_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_b53a5a74cba16b597dcf |
| 70 | Orthopaedic Surgery | linked_scope_metadata_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_916caca41e4ec0677543 |
| 60 | Orthopaedic Surgery | route_recourse_review | pending_non_mutating_reviewer_decision | vanderbilt_candidate_manual_decision_954c8daf198b49d30d57 |
