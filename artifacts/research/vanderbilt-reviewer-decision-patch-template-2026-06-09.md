---
type: research-checkpoint
title: Vanderbilt Reviewer Decision Patch Template
created_at: 2026-06-09T06:45:12.574679+00:00
project: top-50-medical-school-roster-engine
---

# Vanderbilt Reviewer Decision Patch Template

## Boundary

Non-mutating Vanderbilt reviewer decision patch template. It materializes only helper-compatible blank patch rows keyed by manual_decision_row_key. It does not fill reviewer decisions, include reviewer notes, publish raw candidate names or URLs, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, or collapse identities.

## Summary

```json
{
  "blank_action_rows": 159,
  "blank_confirmation_rows": {
    "confirm_candidate_fingerprint_only": 159,
    "confirm_decision_fingerprint": 159,
    "confirm_no_denominator_closure": 159,
    "confirm_no_person_ingestion": 159,
    "confirm_no_raw_name_added": 159,
    "confirm_no_url_rewrite": 159,
    "confirm_recourse_only": 159,
    "confirm_scope_metadata_only": 159
  },
  "by_source_review_queue_lane": {
    "candidate_fingerprint_review": 155,
    "linked_scope_metadata_review": 3,
    "route_recourse_review": 1
  },
  "csv": "artifacts/data/vanderbilt_reviewer_decision_patch_template.csv",
  "denominator_closure_allowed": false,
  "generated_at": "2026-06-09T06:45:12.574679+00:00",
  "helper_accepts_template_shape": true,
  "helper_patch_fields": [
    "manual_decision_row_key",
    "reviewer_action",
    "confirm_decision_fingerprint",
    "confirm_no_person_ingestion",
    "confirm_no_denominator_closure",
    "confirm_no_raw_name_added",
    "confirm_no_url_rewrite",
    "confirm_candidate_fingerprint_only",
    "confirm_scope_metadata_only",
    "confirm_recourse_only"
  ],
  "json": "artifacts/data/vanderbilt_reviewer_decision_patch_template.json",
  "markdown": "artifacts/research/vanderbilt-reviewer-decision-patch-template-2026-06-09.md",
  "mutation_allowed": false,
  "person_ingestion_allowed": false,
  "policy": "Non-mutating Vanderbilt reviewer decision patch template. It materializes only helper-compatible blank patch rows keyed by manual_decision_row_key. It does not fill reviewer decisions, include reviewer notes, publish raw candidate names or URLs, approve people, ingest people, close denominators, verify Vanderbilt as a school, rewrite URLs, accept enrichment facts, or collapse identities.",
  "raw_candidate_names_committed": false,
  "raw_person_urls_committed": false,
  "reviewer_note_column_committed": false,
  "rowset_sha256": "5532d007555997f54d25884baba2f4e594d4ff1fa286301bfa6f87fc64caaa8d",
  "school_verification_allowed": false,
  "source_operator_packet_rowset_sha256": "6d61db6d2fa9a43034c35b401f2cc2d1b8a7b96b6a606368b825aa9822c2c173",
  "source_operator_packet_summary": "artifacts/data/vanderbilt_public_reviewer_operator_packet_summary.json",
  "source_scaffold_rowset_sha256": "29f91bd14647f1d9ee3eaa82dda6326e2b2d78f30c10041f31ac781f05353938",
  "source_scaffold_summary": "artifacts/data/vanderbilt_candidate_review_decision_scaffold_summary.json",
  "template_intentionally_invalid_until_filled": true,
  "template_rows": 159,
  "valid_non_mutating_rows": 0
}
```

## Template Rows

| row | manual_decision_row_key | reviewer_action |
| ---: | --- | --- |
| 1 | vanderbilt_candidate_manual_decision_4064b8c50348aa1e8f9a |  |
| 2 | vanderbilt_candidate_manual_decision_64720c5a5f44fe7cc522 |  |
| 3 | vanderbilt_candidate_manual_decision_bdc4f62970c7eb142413 |  |
| 4 | vanderbilt_candidate_manual_decision_cd36852868ed255dffa3 |  |
| 5 | vanderbilt_candidate_manual_decision_2241afa21e19e80a60b3 |  |
| 6 | vanderbilt_candidate_manual_decision_5bc100b3c28e5ca6a39f |  |
| 7 | vanderbilt_candidate_manual_decision_9e40693f7538a38d1491 |  |
| 8 | vanderbilt_candidate_manual_decision_f71f5ec5c86da430c633 |  |
| 9 | vanderbilt_candidate_manual_decision_143d950856b53ff8e77e |  |
| 10 | vanderbilt_candidate_manual_decision_1f940c7a900537b18dd3 |  |
| 11 | vanderbilt_candidate_manual_decision_56820b78dd600cb14786 |  |
| 12 | vanderbilt_candidate_manual_decision_786e533f5a1129b2e8db |  |
| 13 | vanderbilt_candidate_manual_decision_99a49324e6ddb002948d |  |
| 14 | vanderbilt_candidate_manual_decision_c10790d7c74912ac55fe |  |
| 15 | vanderbilt_candidate_manual_decision_cd1f8f0e8ebee89eb5a9 |  |
| 16 | vanderbilt_candidate_manual_decision_dea0ea21f10ff6a40dfc |  |
| 17 | vanderbilt_candidate_manual_decision_f9824841462cee1cfe36 |  |
| 18 | vanderbilt_candidate_manual_decision_ff3981f51e60b20073e5 |  |
| 19 | vanderbilt_candidate_manual_decision_0588b8016515e8e9d817 |  |
| 20 | vanderbilt_candidate_manual_decision_076850032ce8a6bdf46b |  |
| 21 | vanderbilt_candidate_manual_decision_0de73cce2256fecf6d9a |  |
| 22 | vanderbilt_candidate_manual_decision_11e956e154816cefa013 |  |
| 23 | vanderbilt_candidate_manual_decision_31a80bed45e2f2532b5f |  |
| 24 | vanderbilt_candidate_manual_decision_7cb8f6347db55fcef3cc |  |
| 25 | vanderbilt_candidate_manual_decision_7d4e81cf8a6b61092509 |  |
| 26 | vanderbilt_candidate_manual_decision_8933824f55b87200aa94 |  |
| 27 | vanderbilt_candidate_manual_decision_8d9f0f540559de0b1993 |  |
| 28 | vanderbilt_candidate_manual_decision_8deb608791eaa8a54fc2 |  |
| 29 | vanderbilt_candidate_manual_decision_9929f8231caf5291b189 |  |
| 30 | vanderbilt_candidate_manual_decision_a3b22e9cf9c2060e6ac0 |  |
| 31 | vanderbilt_candidate_manual_decision_a72b614cf1c2f3ef7440 |  |
| 32 | vanderbilt_candidate_manual_decision_b794902e2d3e6d7fef6f |  |
| 33 | vanderbilt_candidate_manual_decision_bb848b009ce6e7087c9d |  |
| 34 | vanderbilt_candidate_manual_decision_c559e9b2e38014268c75 |  |
| 35 | vanderbilt_candidate_manual_decision_c8d1412b9a31fcc1f723 |  |
| 36 | vanderbilt_candidate_manual_decision_f0ad43b977a28be192d2 |  |
| 37 | vanderbilt_candidate_manual_decision_f9963a5ae4a8c10e3688 |  |
| 38 | vanderbilt_candidate_manual_decision_044a9c6190f11cf535f6 |  |
| 39 | vanderbilt_candidate_manual_decision_08e9e929c74db144c690 |  |
| 40 | vanderbilt_candidate_manual_decision_1c991b84f6ae229235f0 |  |
| 41 | vanderbilt_candidate_manual_decision_34c539b1aaffb69b2c2a |  |
| 42 | vanderbilt_candidate_manual_decision_44ecd5a4b6246f90b452 |  |
| 43 | vanderbilt_candidate_manual_decision_59c9fbb941f29fa9c472 |  |
| 44 | vanderbilt_candidate_manual_decision_77dc4a401a6a35299c2a |  |
| 45 | vanderbilt_candidate_manual_decision_873049e5ccde8d2d45fc |  |
| 46 | vanderbilt_candidate_manual_decision_88589a5725325a6ccd3d |  |
| 47 | vanderbilt_candidate_manual_decision_9c1f1f14e033a95b31ee |  |
| 48 | vanderbilt_candidate_manual_decision_a104e19512e559febb1c |  |
| 49 | vanderbilt_candidate_manual_decision_a3f1951532d6ea26081c |  |
| 50 | vanderbilt_candidate_manual_decision_a8bf0204327b953973cd |  |
| 51 | vanderbilt_candidate_manual_decision_b7f945c7c6b2c778e335 |  |
| 52 | vanderbilt_candidate_manual_decision_e892bee2d863be259d18 |  |
| 53 | vanderbilt_candidate_manual_decision_f1beee533c80c2a950ed |  |
| 54 | vanderbilt_candidate_manual_decision_f412e1e197a3844a8dd6 |  |
| 55 | vanderbilt_candidate_manual_decision_117552caf1886eb5b00a |  |
| 56 | vanderbilt_candidate_manual_decision_13a2138a24bf41bbbff5 |  |
| 57 | vanderbilt_candidate_manual_decision_15558823f0cfbc4a4018 |  |
| 58 | vanderbilt_candidate_manual_decision_2983a5c364311fad6ad9 |  |
| 59 | vanderbilt_candidate_manual_decision_67578fb2b6925ca788a0 |  |
| 60 | vanderbilt_candidate_manual_decision_6ee31495fbfd6c3ee378 |  |
| 61 | vanderbilt_candidate_manual_decision_8bedb8b701c282edb7bd |  |
| 62 | vanderbilt_candidate_manual_decision_95ab198df60f2ae05921 |  |
| 63 | vanderbilt_candidate_manual_decision_9f402606bd088c1f40b2 |  |
| 64 | vanderbilt_candidate_manual_decision_9ff2d13d2e9f9637292a |  |
| 65 | vanderbilt_candidate_manual_decision_b7eaf35d13b1d4150058 |  |
| 66 | vanderbilt_candidate_manual_decision_c26608a5b7629c8ddf3a |  |
| 67 | vanderbilt_candidate_manual_decision_c3ec56fc866e3017ab56 |  |
| 68 | vanderbilt_candidate_manual_decision_ceab5ba77e0cbc674f4f |  |
| 69 | vanderbilt_candidate_manual_decision_d072283948efbbc9296a |  |
| 70 | vanderbilt_candidate_manual_decision_f046f91f7abc807134a3 |  |
| 71 | vanderbilt_candidate_manual_decision_f5a28461c9d159168959 |  |
| 72 | vanderbilt_candidate_manual_decision_05a4e3d6215ba89b32bc |  |
| 73 | vanderbilt_candidate_manual_decision_209a2e643d6ccdef0e2f |  |
| 74 | vanderbilt_candidate_manual_decision_4aac191f55711ebab45a |  |
| 75 | vanderbilt_candidate_manual_decision_1c27c6d48941791b15b3 |  |
| 76 | vanderbilt_candidate_manual_decision_49df105b86c4bc9a926d |  |
| 77 | vanderbilt_candidate_manual_decision_6378fa11f6c5686ce2fa |  |
| 78 | vanderbilt_candidate_manual_decision_6806d2dd4434d72d6daa |  |
| 79 | vanderbilt_candidate_manual_decision_748532dd8ea61cb32e7f |  |
| 80 | vanderbilt_candidate_manual_decision_85243c734e0434885fb7 |  |
| 81 | vanderbilt_candidate_manual_decision_85a9e57f12a519a0239a |  |
| 82 | vanderbilt_candidate_manual_decision_912234a0e5968f89adf8 |  |
| 83 | vanderbilt_candidate_manual_decision_ab3fcad794ce1cc6b287 |  |
| 84 | vanderbilt_candidate_manual_decision_c4d6717a7684805b7b98 |  |
| 85 | vanderbilt_candidate_manual_decision_c57b0dc2a64af51d17e4 |  |
| 86 | vanderbilt_candidate_manual_decision_cef4ed69bca1364e1246 |  |
| 87 | vanderbilt_candidate_manual_decision_1a2b03b02e6eefd08289 |  |
| 88 | vanderbilt_candidate_manual_decision_1cea0ee5677b7572bf2a |  |
| 89 | vanderbilt_candidate_manual_decision_4a67985ea9291ac901b4 |  |
| 90 | vanderbilt_candidate_manual_decision_a490fc9883a26deb2bfd |  |
| 91 | vanderbilt_candidate_manual_decision_1513604bafe574333957 |  |
| 92 | vanderbilt_candidate_manual_decision_607dfa03362f41e0c7e9 |  |
| 93 | vanderbilt_candidate_manual_decision_761009de715b9716e9e8 |  |
| 94 | vanderbilt_candidate_manual_decision_85c00159cd7307b27ebe |  |
| 95 | vanderbilt_candidate_manual_decision_afd6a61487c1526efc54 |  |
| 96 | vanderbilt_candidate_manual_decision_c680d6ac9f9e7c226843 |  |
| 97 | vanderbilt_candidate_manual_decision_c93657ec34a17dc68ad5 |  |
| 98 | vanderbilt_candidate_manual_decision_d01ddd8ec876abf1ac27 |  |
| 99 | vanderbilt_candidate_manual_decision_de86f4059f334b73fb09 |  |
| 100 | vanderbilt_candidate_manual_decision_f41dacaaab5500a892ee |  |
| 101 | vanderbilt_candidate_manual_decision_1077cbf238fc18784aa3 |  |
| 102 | vanderbilt_candidate_manual_decision_4988013c59c100445e1f |  |
| 103 | vanderbilt_candidate_manual_decision_644e74affc7ac5181ad1 |  |
| 104 | vanderbilt_candidate_manual_decision_da695063db2848598172 |  |
| 105 | vanderbilt_candidate_manual_decision_2bd835d04703caeb21da |  |
| 106 | vanderbilt_candidate_manual_decision_4951e15682e2090061ae |  |
| 107 | vanderbilt_candidate_manual_decision_6b67e4cd2c5f4c81dd9d |  |
| 108 | vanderbilt_candidate_manual_decision_db30ba83e8c0cfccec71 |  |
| 109 | vanderbilt_candidate_manual_decision_1074d7c46baa176a3cc1 |  |
| 110 | vanderbilt_candidate_manual_decision_23eb4f2e7398d00b74fa |  |
| 111 | vanderbilt_candidate_manual_decision_2e8fd4470fe9f0426d29 |  |
| 112 | vanderbilt_candidate_manual_decision_33ca2f64724befb47647 |  |
| 113 | vanderbilt_candidate_manual_decision_4bd3ab3e567e186344c3 |  |
| 114 | vanderbilt_candidate_manual_decision_4beed575b79cab19cc19 |  |
| 115 | vanderbilt_candidate_manual_decision_54b04e0e3a60a114bf7d |  |
| 116 | vanderbilt_candidate_manual_decision_62ca061845b586055fe2 |  |
| 117 | vanderbilt_candidate_manual_decision_6a1b681d7a868202e26b |  |
| 118 | vanderbilt_candidate_manual_decision_c49eeb9774a46d0d479c |  |
| 119 | vanderbilt_candidate_manual_decision_6f12df3d4fb193d7332d |  |
| 120 | vanderbilt_candidate_manual_decision_df3d7a97dd81a5e1a202 |  |
| 121 | vanderbilt_candidate_manual_decision_0a607f356578addb84a1 |  |
| 122 | vanderbilt_candidate_manual_decision_17a077d5387b6610b166 |  |
| 123 | vanderbilt_candidate_manual_decision_1d1ff4bee76841c437ba |  |
| 124 | vanderbilt_candidate_manual_decision_280c907c8d3b406a02a5 |  |
| 125 | vanderbilt_candidate_manual_decision_41bc7335a0d7d9288088 |  |
| 126 | vanderbilt_candidate_manual_decision_5870b8f62e2dd0f58379 |  |
| 127 | vanderbilt_candidate_manual_decision_59abfd699aec2ce81de2 |  |
| 128 | vanderbilt_candidate_manual_decision_5ad0992a650b2a678c33 |  |
| 129 | vanderbilt_candidate_manual_decision_61682d72040b2bd2a5e1 |  |
| 130 | vanderbilt_candidate_manual_decision_65de70b1ebdd0e355704 |  |
| 131 | vanderbilt_candidate_manual_decision_77e8eeaec474cef7bf25 |  |
| 132 | vanderbilt_candidate_manual_decision_824218168269dd97455b |  |
| 133 | vanderbilt_candidate_manual_decision_8877dc5d08299c228cf4 |  |
| 134 | vanderbilt_candidate_manual_decision_90fe7a19afe4f98352d0 |  |
| 135 | vanderbilt_candidate_manual_decision_9ad94f8e7719327a00f8 |  |
| 136 | vanderbilt_candidate_manual_decision_9c75d066432ec3c31467 |  |
| 137 | vanderbilt_candidate_manual_decision_b7d4c257c751ab6b1201 |  |
| 138 | vanderbilt_candidate_manual_decision_ba815b5776970eede34c |  |
| 139 | vanderbilt_candidate_manual_decision_bfbc6dacf37c548e5fef |  |
| 140 | vanderbilt_candidate_manual_decision_c5d68c671b21c80f7a9f |  |
| 141 | vanderbilt_candidate_manual_decision_cacf52af403e5450323f |  |
| 142 | vanderbilt_candidate_manual_decision_d853f57e0ffefc1f901c |  |
| 143 | vanderbilt_candidate_manual_decision_da19bdede0cc39409205 |  |
| 144 | vanderbilt_candidate_manual_decision_f0ed676b5e542593e43c |  |
| 145 | vanderbilt_candidate_manual_decision_f35eea5674758fdedbd4 |  |
| 146 | vanderbilt_candidate_manual_decision_fa3ee36ba0a2fdd7bc8e |  |
| 147 | vanderbilt_candidate_manual_decision_00305373b0fe1e44a129 |  |
| 148 | vanderbilt_candidate_manual_decision_2778e62fdb93042245cb |  |
| 149 | vanderbilt_candidate_manual_decision_30c3989728a3ef1e161f |  |
| 150 | vanderbilt_candidate_manual_decision_41a237be99fc306cbc45 |  |
| 151 | vanderbilt_candidate_manual_decision_6c95b5bba7b241656a5c |  |
| 152 | vanderbilt_candidate_manual_decision_722dc48a646d5231f0ae |  |
| 153 | vanderbilt_candidate_manual_decision_afdf97b988297afbab6f |  |
| 154 | vanderbilt_candidate_manual_decision_b0710ce12e8dbc33bdf7 |  |
| 155 | vanderbilt_candidate_manual_decision_d5171386cd9a56a20015 |  |
| 156 | vanderbilt_candidate_manual_decision_34f010a0ce64ef87824d |  |
| 157 | vanderbilt_candidate_manual_decision_b53a5a74cba16b597dcf |  |
| 158 | vanderbilt_candidate_manual_decision_916caca41e4ec0677543 |  |
| 159 | vanderbilt_candidate_manual_decision_954c8daf198b49d30d57 |  |
