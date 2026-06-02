# redmank

`redmank` is a public-source research corpus for understanding medicine training programs, starting with Penn Medicine and the Perelman School of Medicine.

The first case study focuses on Penn Department of Medicine residents and fellows, with a separate partial medical-student source from the public Penn MSTP directory. The project keeps provenance close to each record: source URL, source type, extraction method, role, program, population, training-year label, current-status inference, and quality notes.

## Current Penn Outputs

- `artifacts/data/penn_training_people_unique.json`: deduplicated Department of Medicine resident/fellow corpus.
- `artifacts/data/penn_training_people_unique.csv`: spreadsheet-friendly version of the same corpus.
- `artifacts/data/penn_profile_index.md`: human review index for the resident/fellow corpus.
- `artifacts/data/penn_training_summary.json`: counts and field coverage for the resident/fellow corpus.
- `artifacts/data/penn_source_discovery.json`: crawler-based review list of candidate Penn Department of Medicine training pages.
- `artifacts/data/penn_mstp_students.json`: separate public MSTP student-directory extract.
- `artifacts/data/redmank.sqlite`: SQLite warehouse built from the generated artifacts.
- `artifacts/data/warehouse_summary.json`: warehouse table counts and resolver status counts.
- `artifacts/data/organization_review_queue.csv`: organization labels that need alias/identifier review.
- `artifacts/data/person_enrichment_queue.csv`: per-person recursive enrichment tasks.
- `artifacts/data/penn_affiliated_source_discovery.json`: Penn-wide source discovery for trainee, alumni/outcome, and attending/faculty candidates.
- `artifacts/data/evidence_claims.csv`: accepted and candidate evidence claims.
- `artifacts/data/source_quality_report.json`: machine-readable source utility observations and feature distributions.
- `artifacts/research/penn-source-quality-learnings-2026-06-02.md`: first source-quality learning report.
- `artifacts/research/`: methodology and tradeoff briefs.

As of the latest local generation, the Department of Medicine corpus has 453 unique resident/fellow profiles: 220 current fellows, 219 current residents, 1 chief resident, and 13 former fellows exposed on current fellowship pages. The separate MSTP student subset has 225 public student-directory records and is intentionally not treated as an all-medical-student roster.

## Reproduce

Install dependencies:

```bash
python3 -m pip install --target /tmp/penn_corpus_deps -r requirements.txt
```

Run the resident/fellow corpus:

```bash
python3 scripts/scrape_penn_training.py
```

Run Penn Department of Medicine source discovery:

```bash
python3 scripts/discover_penn_training_sources.py
```

Run the separate public MSTP student extract:

```bash
python3 scripts/scrape_penn_mstp_students.py
```

Build the SQLite warehouse and review queues:

```bash
python3 scripts/build_sqlite.py
python3 scripts/generate_enrichment_queue.py
```

Run Penn-wide source discovery and first-pass research candidate collection:

```bash
python3 scripts/discover_penn_affiliated_sources.py
python3 scripts/collect_research_candidates.py
python3 scripts/export_warehouse_views.py
python3 scripts/report_source_quality.py
python3 scripts/summarize_warehouse.py
```

Validate scripts:

```bash
python3 -m py_compile scripts/*.py
```

## Data Policy

This project uses public web sources only. It does not bypass login walls, private directories, robots exclusions, or application-only systems. Public student-directory email links are intentionally not extracted. Records should retain source URLs and quality notes so downstream users can distinguish official roster facts from inferred categorization and enrichment candidates.

## Method

The initial methodology is conservative:

- Prefer official program roster pages over search snippets or secondary profiles.
- Store source metadata, including HTTP status and content hash. Redacted raw snapshots can be regenerated locally but are ignored by Git.
- Deduplicate by normalized person name with manual aliases only when the same public corpus shows the variant.
- Keep track and fellowship memberships as multi-valued fields instead of forcing one person into one category.
- Separate resident/fellow rosters, context-only program pages, alumni/former pages, and partial student directories.
- Treat publication, grant, trial, NPI, and social-web enrichment as separate evidence layers requiring identity-resolution confidence, not as roster truth.
- Resolve school/hospital/program labels into organization rows with raw values, aliases, identifiers, and review status instead of overwriting source strings.
- Keep scholarly API results as candidate evidence until reconciliation supplies enough non-name anchors.

See the latest research brief in `artifacts/research/` for source coverage, quality grades, and recommended enrichment tiers.
