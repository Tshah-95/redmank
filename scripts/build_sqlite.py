#!/usr/bin/env python3
"""Build the redmank SQLite warehouse from generated flat-file artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "db" / "schema.sql"
ARTIFACTS = ROOT / "artifacts" / "data"
DEFAULT_DB = ARTIFACTS / "redmank.sqlite"
ORG_SEEDS = ROOT / "config" / "organization_seed_aliases.json"
ENRICHMENT_SOURCES = ROOT / "config" / "enrichment_sources.json"
TRAINING_LIFECYCLE_RULES = ROOT / "config" / "training_lifecycle_rules.json"

PERSON_FILES = [
    ARTIFACTS / "penn_training_people_unique.json",
    ARTIFACTS / "penn_affiliated_people.json",
    ARTIFACTS / "penn_gme_gap_roster_people.json",
    ARTIFACTS / "penn_mstp_students.json",
]
SOURCE_FILES = [
    ARTIFACTS / "penn_training_sources.json",
    ARTIFACTS / "penn_affiliated_sources.json",
    ARTIFACTS / "penn_gme_gap_roster_sources.json",
    ARTIFACTS / "penn_source_discovery.json",
]
OPTIONAL_SOURCE_FILES = [
    ARTIFACTS / "penn_affiliated_source_discovery.json",
    ARTIFACTS / "penn_attending_candidate_sources.json",
    ARTIFACTS / "penn_attending_profile_sources.json",
    ARTIFACTS / "penn_attending_profile_claims.json",
    ARTIFACTS / "penn_attending_profile_summary.json",
    ARTIFACTS / "penn_trainee_profile_sources.json",
    ARTIFACTS / "penn_trainee_profile_claims.json",
    ARTIFACTS / "penn_trainee_profile_summary.json",
    ARTIFACTS / "trainee_profile_discovery_sources.json",
    ARTIFACTS / "trainee_profile_discovery_claims.json",
    ARTIFACTS / "trainee_profile_discovery_summary.json",
    ARTIFACTS / "prior_training_discovery_sources.json",
    ARTIFACTS / "prior_training_discovery_claims.json",
    ARTIFACTS / "prior_training_discovery_summary.json",
    ARTIFACTS / "penn_outcome_candidate_sources.json",
    ARTIFACTS / "penn_attending_candidates.json",
    ARTIFACTS / "penn_outcome_candidates.json",
    ARTIFACTS / "penn_gme_program_universe.json",
    ARTIFACTS / "penn_gme_program_universe_source.json",
    ARTIFACTS / "penn_gme_program_coverage.json",
    ARTIFACTS / "penn_gme_gap_source_candidates.json",
    ARTIFACTS / "penn_gme_gap_source_probes.json",
    ARTIFACTS / "research_candidate_claims.json",
    ARTIFACTS / "research_candidate_summary.json",
    ARTIFACTS / "openalex_work_candidate_claims.json",
    ARTIFACTS / "openalex_work_candidate_summary.json",
    ARTIFACTS / "pubmed_article_candidate_claims.json",
    ARTIFACTS / "pubmed_article_candidate_summary.json",
    ARTIFACTS / "manual_source_quality_observations.json",
]

TRAINING_FIELDS = {
    "medical_school": "medical_school",
    "residency_program": "residency_program",
    "undergraduate_school": "undergraduate_school",
    "graduate_school": "graduate_school",
}

LIFECYCLE_RULE_CACHE: list[dict] | None = None


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def norm_space(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).replace("\xa0", " ")).strip()


def normalized_label(text: str | None) -> str:
    text = norm_space(text).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"\b(univ|univ\.|university\.)\b", "university", text)
    text = re.sub(r"\b(hosp|hosp\.)\b", "hospital", text)
    text = re.sub(r"\b(med|med\.)\b", "medical", text)
    text = re.sub(r"\b(sch|sch\.)\b", "school", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\b(the|at|of|and)\b", " ", text)
    return norm_space(text)


def load_lifecycle_rules() -> list[dict]:
    global LIFECYCLE_RULE_CACHE
    if LIFECYCLE_RULE_CACHE is None:
        LIFECYCLE_RULE_CACHE = load_json(TRAINING_LIFECYCLE_RULES)["rules"]
    return LIFECYCLE_RULE_CACHE


def match_lifecycle_rule(program_name: str | None, role: str | None) -> dict | None:
    role = (role or "").lower()
    program_name = norm_space(program_name)
    default_rule = None
    for rule in load_lifecycle_rules():
        if rule.get("role") != role:
            continue
        match_type = rule.get("match_type")
        if match_type == "default":
            default_rule = rule
            continue
        if match_type == "exact" and program_name in set(rule.get("program_names", [])):
            return rule
        if match_type == "regex" and program_name and re.search(rule.get("pattern", ""), program_name, re.I):
            return rule
    return default_rule


def key_for(prefix: str, text: str) -> str:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", normalized_label(text)).strip("-")[:48]
    return f"{prefix}_{slug}_{digest}"


def fingerprint(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        if not path.exists():
            continue
        h.update(path.name.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


class OrganizationResolver:
    def __init__(self, conn: sqlite3.Connection, seed_path: Path) -> None:
        self.conn = conn
        self.alias_to_org: dict[tuple[str, str], int] = {}
        self.load_seeds(seed_path)

    def load_seeds(self, seed_path: Path) -> None:
        payload = load_json(seed_path)
        for org in payload["organizations"]:
            org_id = self.upsert_org(
                canonical_name=org["canonical_name"],
                category=org.get("category", "organization"),
                parent_name=org.get("parent_name", ""),
                resolver_status="seeded_alias",
                confidence=0.98,
                metadata={"seed_version": payload.get("version")},
            )
            aliases = set(org.get("aliases", [])) | {org["canonical_name"]}
            for alias in aliases:
                self.add_alias(org_id, alias, "seed", 0.98)
                self.alias_to_org[(normalized_label(alias), org.get("category", "organization"))] = org_id
            for identifier in org.get("identifiers", []):
                self.conn.execute(
                    """
                    INSERT OR IGNORE INTO organization_identifiers
                    (organization_id, identifier_type, identifier_value, source)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        org_id,
                        identifier["identifier_type"],
                        identifier["identifier_value"],
                        identifier.get("source", "seed"),
                    ),
                )

    def upsert_org(
        self,
        canonical_name: str,
        category: str,
        parent_name: str,
        resolver_status: str,
        confidence: float,
        metadata: dict | None = None,
    ) -> int:
        canonical_name = norm_space(canonical_name)
        org_key = key_for("org", f"{category}:{canonical_name}")
        self.conn.execute(
            """
            INSERT OR IGNORE INTO organizations
            (organization_key, canonical_name, normalized_name, category, parent_name,
             resolver_status, confidence, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                org_key,
                canonical_name,
                normalized_label(canonical_name),
                category,
                norm_space(parent_name),
                resolver_status,
                confidence,
                dumps(metadata or {}),
            ),
        )
        row = self.conn.execute(
            "SELECT organization_id FROM organizations WHERE organization_key = ?",
            (org_key,),
        ).fetchone()
        return int(row["organization_id"])

    def add_alias(self, org_id: int, alias: str, source_context: str, confidence: float) -> None:
        alias = norm_space(alias)
        if not alias:
            return
        self.conn.execute(
            """
            INSERT OR IGNORE INTO organization_aliases
            (organization_id, alias, normalized_alias, source_context, confidence)
            VALUES (?, ?, ?, ?, ?)
            """,
            (org_id, alias, normalized_label(alias), source_context, confidence),
        )

    def resolve(self, raw_value: str, event_type: str) -> tuple[int, str, float]:
        raw_value = norm_space(raw_value)
        normalized = normalized_label(raw_value)
        if not raw_value:
            raise ValueError("cannot resolve empty organization value")
        category = {
            "medical_school": "medical_school",
            "residency_program": "clinical_training_site",
            "undergraduate_school": "undergraduate_institution",
            "graduate_school": "graduate_institution",
        }.get(event_type, "organization")
        if (normalized, category) in self.alias_to_org:
            return self.alias_to_org[(normalized, category)], "seeded_alias", 0.98
        org_id = self.upsert_org(
            canonical_name=raw_value,
            category=category,
            parent_name="",
            resolver_status="cleaned_label",
            confidence=0.55,
            metadata={"needs_review": True},
        )
        self.add_alias(org_id, raw_value, event_type, 0.55)
        self.alias_to_org[(normalized, category)] = org_id
        return org_id, "cleaned_label", 0.55


def init_db(path: Path) -> sqlite3.Connection:
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    return conn


def insert_sources(conn: sqlite3.Connection) -> None:
    for source in load_json(ARTIFACTS / "penn_training_sources.json"):
        source_key = source["source_key"]
        conn.execute(
            """
            INSERT OR REPLACE INTO sources
            (source_key, source_url, source_type, fetched_at, http_status, sha256, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_key,
                source.get("url"),
                "official_roster_or_context",
                source.get("fetched_at"),
                source.get("http_status"),
                source.get("sha256"),
                dumps(source),
            ),
        )
    affiliated_sources = ARTIFACTS / "penn_affiliated_sources.json"
    if affiliated_sources.exists():
        for source in load_json(affiliated_sources):
            conn.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_key, source_url, source_type, fetched_at, http_status, sha256, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source["source_key"],
                    source.get("url"),
                    "official_affiliated_roster",
                    source.get("fetched_at"),
                    source.get("http_status"),
                    source.get("sha256"),
                    dumps(source),
                ),
            )
    gap_roster_sources = ARTIFACTS / "penn_gme_gap_roster_sources.json"
    if gap_roster_sources.exists():
        for source in load_json(gap_roster_sources):
            conn.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_key, source_url, source_type, title, fetched_at, http_status, sha256, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source["source_key"],
                    source.get("url"),
                    "official_gap_roster",
                    source.get("candidate_title"),
                    source.get("fetched_at"),
                    source.get("http_status"),
                    source.get("sha256"),
                    dumps(source),
                ),
            )
    for optional_sources, source_type in [
        (ARTIFACTS / "penn_attending_candidate_sources.json", "official_attending_faculty_candidate"),
        (ARTIFACTS / "penn_attending_profile_sources.json", "official_attending_profile"),
        (ARTIFACTS / "penn_trainee_profile_sources.json", "official_trainee_profile"),
        (ARTIFACTS / "penn_outcome_candidate_sources.json", "official_outcome_context"),
    ]:
        if optional_sources.exists():
            for source in load_json(optional_sources):
                conn.execute(
                    """
                    INSERT OR REPLACE INTO sources
                    (source_key, source_url, source_type, title, fetched_at, http_status, sha256, metadata_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source["source_key"],
                        source.get("url"),
                        source_type,
                        source.get("title"),
                        source.get("fetched_at"),
                        source.get("http_status"),
                        source.get("sha256"),
                        dumps(source),
                    ),
                )
    discovery = load_json(ARTIFACTS / "penn_source_discovery.json")
    for row in discovery["findings"]:
        source_key = f"discovery:{key_for('source', row['url'])}"
        conn.execute(
            """
            INSERT OR REPLACE INTO sources
            (source_key, source_url, source_type, title, classification, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                source_key,
                row.get("url"),
                "source_discovery",
                row.get("title"),
                row.get("classification"),
                dumps(row),
            ),
        )
    affiliated = ARTIFACTS / "penn_affiliated_source_discovery.json"
    if affiliated.exists():
        payload = load_json(affiliated)
        for row in payload["findings"]:
            source_key = f"affiliated_discovery:{key_for('source', row['url'])}"
            conn.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_key, source_url, source_type, title, classification, sha256, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_key,
                    row.get("url"),
                    "penn_affiliated_source_discovery",
                    row.get("title"),
                    row.get("classification"),
                    row.get("sha256"),
                    dumps(row),
                ),
            )
    conn.execute(
        """
        INSERT OR IGNORE INTO sources
        (source_key, source_url, source_type, title, metadata_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "perelman_mstp_student_directory",
            "https://www.med.upenn.edu/mstp/student-directory/",
            "official_public_student_directory",
            "Penn MSTP Student Directory",
            "{}",
        ),
    )


def insert_lifecycle_rules(conn: sqlite3.Connection) -> None:
    for rule in load_lifecycle_rules():
        conn.execute(
            """
            INSERT OR REPLACE INTO program_lifecycle_rules
            (rule_key, role, match_type, pattern, lifecycle_code, lifecycle_family,
             nominal_years, entry_stage, terminal_stage, clock_rollover_month,
             auto_advance, source, confidence, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rule["rule_key"],
                rule["role"],
                rule["match_type"],
                rule.get("pattern"),
                rule["lifecycle_code"],
                rule["lifecycle_family"],
                rule.get("nominal_years"),
                rule.get("entry_stage"),
                rule.get("terminal_stage"),
                int(rule.get("clock_rollover_month") or 7),
                1 if rule.get("auto_advance") else 0,
                rule.get("source"),
                float(rule.get("confidence") or 0.0),
                dumps(rule),
            ),
        )


def insert_source_utilities(conn: sqlite3.Connection) -> None:
    payload = load_json(ENRICHMENT_SOURCES)
    for utility in payload["utilities"]:
        conn.execute(
            """
            INSERT OR REPLACE INTO source_utilities
            (utility_key, display_name, source_family, default_tier, default_status,
             default_confidence, claim_types_json, strengths_json, limitations_json,
             acceptance_rule, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utility["utility_key"],
                utility["display_name"],
                utility["source_family"],
                utility["default_tier"],
                utility["default_status"],
                utility["default_confidence"],
                dumps(utility["claim_types"]),
                dumps(utility["strengths"]),
                dumps(utility["limitations"]),
                utility["acceptance_rule"],
                dumps({"seed_version": payload.get("version")}),
            ),
        )


def upsert_scholarly_sources(conn: sqlite3.Connection) -> None:
    for source_key, source_url, title in [
        ("openalex_author_search", "https://api.openalex.org/authors", "OpenAlex author search"),
        ("openalex_work_search", "https://api.openalex.org/works", "OpenAlex work search"),
        ("pubmed_eutilities", "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/", "NCBI PubMed E-utilities"),
    ]:
        conn.execute(
            """
            INSERT OR REPLACE INTO sources
            (source_key, source_url, source_type, title, metadata_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (source_key, source_url, "scholarly_api", title, "{}"),
        )


def insert_manual_source_quality_observations(conn: sqlite3.Connection) -> None:
    path = ARTIFACTS / "manual_source_quality_observations.json"
    if not path.exists():
        return
    for row in load_json(path):
        conn.execute(
            """
            INSERT INTO source_quality_observations
            (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
             rejected_claims, ambiguous_claims, notes, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["utility_key"],
                row.get("observed_at") or datetime.now(timezone.utc).isoformat(),
                int(row.get("sample_size", 0)),
                int(row.get("candidate_claims", 0)),
                int(row.get("accepted_claims", 0)),
                int(row.get("rejected_claims", 0)),
                int(row.get("ambiguous_claims", 0)),
                row.get("notes", ""),
                dumps(row.get("metrics", {})),
            ),
        )


def insert_research_candidate_claims(conn: sqlite3.Connection) -> None:
    claim_paths = [
        ARTIFACTS / "research_candidate_claims.json",
        ARTIFACTS / "openalex_work_candidate_claims.json",
        ARTIFACTS / "pubmed_article_candidate_claims.json",
    ]
    paths = [path for path in claim_paths if path.exists()]
    if not paths:
        return
    raw_claims = []
    for path in paths:
        raw_claims.extend(load_json(path))
    if not raw_claims:
        return
    existing_people = {row[0] for row in conn.execute("SELECT person_key FROM people")}
    orphan_claims = [row for row in raw_claims if row.get("person_key") not in existing_people]
    claims = [row for row in raw_claims if row.get("person_key") in existing_people]
    if not claims:
        return
    upsert_scholarly_sources(conn)
    for row in claims:
        conn.execute(
            """
            INSERT INTO evidence_claims
            (person_key, claim_type, claim_value, source_key, source_url, source_type,
             confidence, status, match_features_json, reconciliation_notes, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["person_key"],
                row["claim_type"],
                row["claim_value"],
                row["source_key"],
                row["source_url"],
                row["source_type"],
                row["confidence"],
                row["status"],
                dumps(row.get("match_features", [])),
                row.get("reconciliation_notes", ""),
                dumps(row.get("evidence", {})),
            ),
        )
    summaries = {
        "research_candidate_claims.json": load_json(ARTIFACTS / "research_candidate_summary.json")
        if (ARTIFACTS / "research_candidate_summary.json").exists()
        else {},
        "openalex_work_candidate_claims.json": load_json(ARTIFACTS / "openalex_work_candidate_summary.json")
        if (ARTIFACTS / "openalex_work_candidate_summary.json").exists()
        else {},
        "pubmed_article_candidate_claims.json": load_json(ARTIFACTS / "pubmed_article_candidate_summary.json")
        if (ARTIFACTS / "pubmed_article_candidate_summary.json").exists()
        else {},
    }
    artifact_observed_at = sorted(
        summary["generated_at"] for summary in summaries.values() if summary.get("generated_at")
    )
    generated_at = artifact_observed_at[-1] if artifact_observed_at else datetime.now(timezone.utc).isoformat()
    orphan_claims_by_source = Counter(row.get("source_key", "") for row in orphan_claims)
    orphan_people_by_source: dict[str, set[str]] = defaultdict(set)
    for row in orphan_claims:
        orphan_people_by_source[row.get("source_key", "")].add(row.get("person_key", ""))
    for source_key in sorted({row["source_key"] for row in claims}):
        source_claims = [row for row in claims if row["source_key"] == source_key]
        source_people = len({row["person_key"] for row in source_claims})
        conn.execute(
            """
            INSERT INTO source_quality_observations
            (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
             rejected_claims, ambiguous_claims, notes, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_key,
                generated_at,
                source_people,
                sum(1 for row in source_claims if row["status"] == "candidate"),
                sum(1 for row in source_claims if row["status"] == "accepted"),
                sum(1 for row in source_claims if row["status"] == "rejected"),
                sum(1 for row in source_claims if row["status"] == "needs_review"),
                "Replayed durable research evidence artifacts; no claims accepted automatically.",
                dumps(
                    {
                        "claims": len(source_claims),
                        "raw_claims": len([row for row in raw_claims if row.get("source_key") == source_key]),
                        "orphan_claims_skipped": orphan_claims_by_source.get(source_key, 0),
                        "orphan_people_skipped": len(orphan_people_by_source.get(source_key, set())),
                        "mean_confidence": round(
                            sum(float(row["confidence"]) for row in source_claims) / len(source_claims), 4
                        )
                        if source_claims
                        else 0,
                    }
                ),
            ),
        )
    for path in paths:
        summary = summaries.get(path.name, {})
        raw_path_claims = load_json(path)
        path_claims = [row for row in raw_path_claims if row.get("person_key") in existing_people]
        if not raw_path_claims:
            continue
        if path.name != "pubmed_article_candidate_claims.json":
            continue
        utility_key = "pubmed_article_reconciliation"
        conn.execute(
            """
            INSERT INTO source_quality_observations
            (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
             rejected_claims, ambiguous_claims, notes, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                utility_key,
                summary.get("generated_at") or generated_at,
                len({row["person_key"] for row in path_claims}),
                sum(1 for row in path_claims if row["status"] == "candidate"),
                sum(1 for row in path_claims if row["status"] == "accepted"),
                sum(1 for row in path_claims if row["status"] == "rejected"),
                sum(1 for row in path_claims if row["status"] == "needs_review"),
                "Replayed durable research evidence artifact; candidate and needs-review claims are not accepted automatically.",
                dumps(
                    {
                        "claims": len(path_claims),
                        "raw_claims": len(raw_path_claims),
                        "orphan_claims_skipped": len(raw_path_claims) - len(path_claims),
                        "orphan_people_skipped": len(
                            {
                                row.get("person_key", "")
                                for row in raw_path_claims
                                if row.get("person_key") not in existing_people
                            }
                        ),
                        "mean_confidence": round(
                            sum(float(row["confidence"]) for row in path_claims) / len(path_claims), 4
                        )
                        if path_claims
                        else 0,
                        "artifact": path.name,
                        "summary": summary,
                    }
                ),
            ),
        )


def insert_trainee_profile_claims(conn: sqlite3.Connection) -> None:
    claims_path = ARTIFACTS / "penn_trainee_profile_claims.json"
    sources_path = ARTIFACTS / "penn_trainee_profile_sources.json"
    summary_path = ARTIFACTS / "penn_trainee_profile_summary.json"
    if not claims_path.exists():
        return
    if sources_path.exists():
        for source in load_json(sources_path):
            conn.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_key, source_url, source_type, title, fetched_at, http_status, sha256, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source["source_key"],
                    source.get("url"),
                    "official_trainee_profile",
                    source.get("title"),
                    source.get("fetched_at"),
                    source.get("http_status"),
                    source.get("sha256"),
                    dumps(source),
                ),
            )
    raw_claims = load_json(claims_path)
    if not raw_claims:
        return
    existing_people = {row[0] for row in conn.execute("SELECT person_key FROM people")}
    claims = [row for row in raw_claims if row.get("person_key") in existing_people]
    orphan_claims = [row for row in raw_claims if row.get("person_key") not in existing_people]
    if not claims:
        return
    for row in claims:
        conn.execute(
            """
            INSERT INTO evidence_claims
            (person_key, claim_type, claim_value, source_key, source_url, source_type,
             confidence, status, match_features_json, reconciliation_notes, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["person_key"],
                row["claim_type"],
                row["claim_value"],
                row["source_key"],
                row["source_url"],
                row["source_type"],
                row["confidence"],
                row["status"],
                dumps(row.get("match_features", [])),
                row.get("reconciliation_notes", ""),
                dumps(row.get("evidence", {})),
            ),
        )
    summary = load_json(summary_path) if summary_path.exists() else {}
    generated_at = summary.get("generated_at") or datetime.now(timezone.utc).isoformat()
    display_safety = Counter((row.get("evidence") or {}).get("display_safety_status", "") for row in claims)
    conn.execute(
        """
        INSERT INTO source_quality_observations
        (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
         rejected_claims, ambiguous_claims, notes, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "official_trainee_profile",
            generated_at,
            len({row["person_key"] for row in claims}),
            sum(1 for row in claims if row["status"] == "candidate"),
            sum(1 for row in claims if row["status"] == "accepted"),
            sum(1 for row in claims if row["status"] == "rejected"),
            sum(1 for row in claims if row["status"] == "needs_review"),
            "Replayed roster-linked official trainee profile claims; profile URL facts are accepted, profile-derived fields remain candidate enrichment with display-safety metadata.",
            dumps(
                {
                    "claims": len(claims),
                    "raw_claims": len(raw_claims),
                    "orphan_claims_skipped": len(orphan_claims),
                    "people_with_claims": len({row["person_key"] for row in claims}),
                    "source_rows": len({row["source_key"] for row in claims}),
                    "by_claim_type": dict(Counter(row["claim_type"] for row in claims)),
                    "by_status": dict(Counter(row["status"] for row in claims)),
                    "display_safety_counts": dict(display_safety),
                    "summary": summary,
                }
            ),
        ),
    )


def insert_trainee_profile_discovery_claims(conn: sqlite3.Connection) -> None:
    claims_path = ARTIFACTS / "trainee_profile_discovery_claims.json"
    sources_path = ARTIFACTS / "trainee_profile_discovery_sources.json"
    summary_path = ARTIFACTS / "trainee_profile_discovery_summary.json"
    if not claims_path.exists():
        return
    if sources_path.exists():
        for source in load_json(sources_path):
            conn.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_key, source_url, source_type, title, fetched_at, http_status, sha256, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source["source_key"],
                    source.get("url"),
                    "official_trainee_profile",
                    source.get("title"),
                    source.get("fetched_at"),
                    source.get("http_status") or None,
                    source.get("sha256"),
                    dumps(source),
                ),
            )
    raw_claims = load_json(claims_path)
    if not raw_claims:
        return
    existing_people = {row[0] for row in conn.execute("SELECT person_key FROM people")}
    claims = [row for row in raw_claims if row.get("person_key") in existing_people]
    orphan_claims = [row for row in raw_claims if row.get("person_key") not in existing_people]
    if not claims:
        return
    for row in claims:
        conn.execute(
            """
            INSERT INTO evidence_claims
            (person_key, claim_type, claim_value, source_key, source_url, source_type,
             confidence, status, match_features_json, reconciliation_notes, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["person_key"],
                row["claim_type"],
                row["claim_value"],
                row["source_key"],
                row["source_url"],
                row["source_type"],
                row["confidence"],
                row["status"],
                dumps(row.get("match_features", [])),
                row.get("reconciliation_notes", ""),
                dumps(row.get("evidence", {})),
            ),
        )
    summary = load_json(summary_path) if summary_path.exists() else {}
    generated_at = summary.get("generated_at") or datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO source_quality_observations
        (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
         rejected_claims, ambiguous_claims, notes, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "official_trainee_profile_discovery",
            generated_at,
            len({row["person_key"] for row in claims}),
            sum(1 for row in claims if row["status"] == "candidate"),
            sum(1 for row in claims if row["status"] == "accepted"),
            sum(1 for row in claims if row["status"] == "rejected"),
            sum(1 for row in claims if row["status"] == "needs_review"),
            "Replayed discovered official trainee profile candidates; no discovered URL mutates roster truth without official roster linkage or review.",
            dumps(
                {
                    "claims": len(claims),
                    "raw_claims": len(raw_claims),
                    "orphan_claims_skipped": len(orphan_claims),
                    "people_with_claims": len({row["person_key"] for row in claims}),
                    "source_rows": len({row["source_key"] for row in claims}),
                    "by_claim_type": dict(Counter(row["claim_type"] for row in claims)),
                    "by_status": dict(Counter(row["status"] for row in claims)),
                    "summary": summary,
                }
            ),
        ),
    )


def insert_prior_training_discovery_claims(conn: sqlite3.Connection) -> None:
    claims_path = ARTIFACTS / "prior_training_discovery_claims.json"
    sources_path = ARTIFACTS / "prior_training_discovery_sources.json"
    summary_path = ARTIFACTS / "prior_training_discovery_summary.json"
    if not claims_path.exists():
        return
    if sources_path.exists():
        for source in load_json(sources_path):
            conn.execute(
                """
                INSERT OR REPLACE INTO sources
                (source_key, source_url, source_type, title, fetched_at, http_status, sha256, metadata_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source["source_key"],
                    source.get("url"),
                    "prior_training_background_discovery",
                    source.get("title"),
                    source.get("fetched_at"),
                    source.get("http_status") or None,
                    source.get("sha256"),
                    dumps(source),
                ),
            )
    raw_claims = load_json(claims_path)
    if not raw_claims:
        return
    existing_people = {row[0] for row in conn.execute("SELECT person_key FROM people")}
    claims = [row for row in raw_claims if row.get("person_key") in existing_people]
    orphan_claims = [row for row in raw_claims if row.get("person_key") not in existing_people]
    if not claims:
        return
    for row in claims:
        conn.execute(
            """
            INSERT INTO evidence_claims
            (person_key, claim_type, claim_value, source_key, source_url, source_type,
             confidence, status, match_features_json, reconciliation_notes, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["person_key"],
                row["claim_type"],
                row["claim_value"],
                row["source_key"],
                row["source_url"],
                row["source_type"],
                row["confidence"],
                row["status"],
                dumps(row.get("match_features", [])),
                row.get("reconciliation_notes", ""),
                dumps(row.get("evidence", {})),
            ),
        )
    summary = load_json(summary_path) if summary_path.exists() else {}
    generated_at = summary.get("generated_at") or datetime.now(timezone.utc).isoformat()
    conn.execute(
        """
        INSERT INTO source_quality_observations
        (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
         rejected_claims, ambiguous_claims, notes, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "prior_training_background_discovery",
            generated_at,
            len({row["person_key"] for row in claims}),
            sum(1 for row in claims if row["status"] == "candidate"),
            sum(1 for row in claims if row["status"] == "accepted"),
            sum(1 for row in claims if row["status"] == "rejected"),
            sum(1 for row in claims if row["status"] == "needs_review"),
            "Replayed discovered medical-school/prior-GME background candidates; no background field is accepted without source-text review.",
            dumps(
                {
                    "claims": len(claims),
                    "raw_claims": len(raw_claims),
                    "orphan_claims_skipped": len(orphan_claims),
                    "people_with_claims": len({row["person_key"] for row in claims}),
                    "source_rows": len({row["source_key"] for row in claims}),
                    "by_claim_type": dict(Counter(row["claim_type"] for row in claims)),
                    "by_status": dict(Counter(row["status"] for row in claims)),
                    "summary": summary,
                }
            ),
        ),
    )


def program_key(program_name: str, role: str | None) -> str:
    return key_for("program", f"{role or ''}:{program_name}")


def insert_program(conn: sqlite3.Connection, row: dict, program_name: str) -> str:
    key = program_key(program_name, row.get("role"))
    conn.execute(
        """
        INSERT OR IGNORE INTO programs
        (program_key, program_name, role, unit, institution, normalized_name)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            program_name,
            row.get("role"),
            row.get("unit"),
            row.get("institution"),
            normalized_label(program_name),
        ),
    )
    return key


def insert_person(conn: sqlite3.Connection, row: dict) -> None:
    person_key = row.get("person_key") or key_for("person", row["name"])
    conn.execute(
        """
        INSERT OR REPLACE INTO people
        (person_key, display_name, role, current_status, institution, profile_url,
         headshot_url, quality_tier, quality_notes_json, source_json, raw_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            person_key,
            row["name"],
            row.get("role"),
            row.get("current_status"),
            row.get("institution"),
            row.get("profile_url") or row.get("profile_anchor_url"),
            row.get("headshot_url"),
            row.get("quality_tier"),
            dumps(row.get("quality_notes", [])),
            dumps(
                {
                    "source_key": row.get("source_key"),
                    "source_url": row.get("source_url"),
                    "source_memberships": row.get("source_memberships", []),
                }
            ),
            dumps(row),
        ),
    )


def listish(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [norm_space(v) for v in value if norm_space(v)]
    return [norm_space(value)]


def normalize_contact_type(value: str | None) -> str:
    normalized = normalized_label(value)
    if normalized in {"email", "e mail", "mail"}:
        return "email"
    if normalized in {"phone", "telephone", "tel"}:
        return "phone"
    return normalized.replace(" ", "_") or "unknown"


def normalize_contact_value(contact_type: str, value: str | None) -> str:
    value = norm_space(value)
    if contact_type == "email":
        return value.lower()
    if contact_type == "phone":
        return re.sub(r"\s+", " ", value)
    return value


def insert_contacts(
    conn: sqlite3.Connection,
    row: dict,
    person_key: str | None = None,
    subject_type: str = "person",
    allow_unmatched_person: bool = False,
) -> None:
    if person_key is None and not allow_unmatched_person:
        person_key = row.get("person_key") or key_for("person", row["name"])
    display_name = norm_space(row.get("name") or row.get("display_name"))
    contacts = row.get("contacts") or []
    if not isinstance(contacts, list):
        return
    for contact in contacts:
        if not isinstance(contact, dict):
            continue
        contact_type = normalize_contact_type(contact.get("contact_type") or contact.get("type"))
        contact_value = normalize_contact_value(contact_type, contact.get("value") or contact.get("contact_value"))
        if not contact_value:
            continue
        source_key = contact.get("source_key") or row.get("source_key")
        source_url = contact.get("source_url") or row.get("profile_url") or row.get("source_url")
        contact_key = key_for(
            "contact",
            f"{person_key or ''}:{display_name}:{subject_type}:{source_key}:{contact_type}:{contact_value}",
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO person_contacts
            (contact_key, person_key, display_name, subject_type,
             contact_type, contact_value, contact_label, contact_scope,
             source_key, source_url, source_type, verification_status, confidence,
             status, match_features_json, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                contact_key,
                person_key,
                display_name,
                subject_type,
                contact_type,
                contact_value,
                norm_space(contact.get("contact_label") or contact.get("label")),
                contact.get("contact_scope") or "institutional",
                source_key,
                source_url,
                contact.get("source_type") or row.get("source_type"),
                contact.get("verification_status") or "public_unverified",
                float(contact.get("confidence", 0.5)),
                contact.get("status") or "candidate",
                dumps(contact.get("match_features", [])),
                dumps(
                    {
                        "origin": "person_contact",
                        "source_record": {
                            "source_key": row.get("source_key"),
                            "source_url": row.get("source_url"),
                            "profile_url": row.get("profile_url") or row.get("profile_anchor_url"),
                        },
                        "contact": contact,
                    }
                ),
            ),
        )


def insert_memberships(conn: sqlite3.Connection, row: dict) -> None:
    person_key = row.get("person_key") or key_for("person", row["name"])
    programs = listish(row.get("program_memberships")) or listish(row.get("program"))
    sources = listish(row.get("source_memberships")) or listish(row.get("source_key"))
    populations = listish(row.get("population_memberships")) or listish(row.get("population"))
    year_labels = listish(row.get("training_year_labels_seen")) or listish(row.get("training_year_label"))
    for program_name in programs:
        pkey = insert_program(conn, row, program_name)
        conn.execute(
            """
            INSERT OR IGNORE INTO person_program_memberships
            (person_key, program_key, source_key, population, training_year_label, current_status, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_key,
                pkey,
                sources[0] if sources else row.get("source_key"),
                ", ".join(populations),
                ", ".join(year_labels),
                row.get("current_status"),
                row.get("role"),
            ),
        )


def academic_year(as_of: date, rollover_month: int) -> tuple[str, date, date]:
    start_year = as_of.year if as_of.month >= rollover_month else as_of.year - 1
    start = date(start_year, rollover_month, 1)
    end = date(start_year + 1, rollover_month, 1) - timedelta(days=1)
    return f"{start_year}-{start_year + 1}", start, end


def next_date_for(as_of: date, rollover_month: int) -> date:
    start_year = as_of.year if as_of.month < rollover_month else as_of.year + 1
    return date(start_year, rollover_month, 1)


def academic_exit_date(start: date, stage_index: int | None, nominal_years: int | None, rollover_month: int) -> date | None:
    if not start or not stage_index or not nominal_years or stage_index <= 0:
        return None
    remaining_years_including_current = nominal_years - stage_index + 1
    if remaining_years_including_current < 1:
        return None
    return date(start.year + remaining_years_including_current, rollover_month, 1) - timedelta(days=1)


def lifecycle_transition(
    lifecycle: dict | None,
    stage_family: str,
    stage_index: int | None,
    default_next_stage: str | None,
    estimated_start_date: date | None,
    default_policy: str,
) -> dict:
    if not lifecycle:
        return {
            "lifecycle_rule_key": None,
            "lifecycle_code": None,
            "lifecycle_stage": None,
            "expected_next_stage": default_next_stage,
            "expected_exit_date": None,
            "expected_transition_type": default_policy,
            "refresh_policy": "refresh_from_source",
        }
    nominal_years = lifecycle.get("nominal_years")
    rollover_month = int(lifecycle.get("clock_rollover_month") or 7)
    expected_exit = academic_exit_date(estimated_start_date, stage_index, nominal_years, rollover_month)
    lifecycle_stage = None
    expected_next = default_next_stage
    transition_type = default_policy
    refresh_policy = "annual_clock" if lifecycle.get("auto_advance") else "source_refresh_required"
    if stage_index and nominal_years:
        if stage_index < nominal_years:
            lifecycle_stage = f"year_{stage_index}_of_{nominal_years}"
            transition_type = "expected_annual_advancement"
        elif stage_index == nominal_years:
            lifecycle_stage = f"terminal_year_{stage_index}_of_{nominal_years}"
            expected_next = lifecycle.get("terminal_stage") or "TRAINING_COMPLETION_OR_ALUMNI"
            transition_type = "expected_completion"
        else:
            lifecycle_stage = f"year_{stage_index}_beyond_nominal_{nominal_years}"
            expected_next = None
            transition_type = "stage_outside_nominal_duration_review"
            refresh_policy = "review_required"
    elif stage_family in {"clinical_postgraduate_research", "research_phase"}:
        lifecycle_stage = "variable_duration_research_phase"
        expected_next = None
        transition_type = "source_refresh_required"
        refresh_policy = "source_refresh_required"
    elif stage_index:
        lifecycle_stage = f"year_{stage_index}_duration_unknown"
    else:
        refresh_policy = "source_refresh_required"
    return {
        "lifecycle_rule_key": lifecycle.get("rule_key"),
        "lifecycle_code": lifecycle.get("lifecycle_code"),
        "lifecycle_stage": lifecycle_stage,
        "expected_next_stage": expected_next,
        "expected_exit_date": expected_exit.isoformat() if expected_exit else None,
        "expected_transition_type": transition_type,
        "refresh_policy": refresh_policy,
    }


def stage_result(
    raw_label: str,
    normalized_stage: str,
    stage_family: str,
    stage_index: int | None,
    stage_rank: int | None,
    trainee_category: str,
    transition_rule: str,
    confidence: float,
    status: str = "current",
    lifecycle: dict | None = None,
    academic_year_value: str | None = None,
    estimated_start_date: date | None = None,
    estimated_end_date: date | None = None,
    expected_next_stage: str | None = None,
    expected_next_date: date | None = None,
    stale_after_date: date | None = None,
    expected_transition_type: str = "source_refresh_required",
    refresh_policy: str = "refresh_from_source",
) -> dict:
    lifecycle_fields = lifecycle_transition(
        lifecycle,
        stage_family,
        stage_index,
        expected_next_stage,
        estimated_start_date,
        expected_transition_type,
    )
    if refresh_policy != "refresh_from_source":
        lifecycle_fields["refresh_policy"] = refresh_policy
    return {
        "raw_stage_label": raw_label,
        "normalized_stage": normalized_stage,
        "stage_family": stage_family,
        "stage_index": stage_index,
        "stage_rank": stage_rank,
        "trainee_category": trainee_category,
        "lifecycle_rule_key": lifecycle_fields["lifecycle_rule_key"],
        "lifecycle_code": lifecycle_fields["lifecycle_code"],
        "lifecycle_stage": lifecycle_fields["lifecycle_stage"],
        "academic_year": academic_year_value,
        "estimated_start_date": estimated_start_date.isoformat() if estimated_start_date else None,
        "estimated_end_date": estimated_end_date.isoformat() if estimated_end_date else None,
        "expected_next_stage": lifecycle_fields["expected_next_stage"],
        "expected_next_date": expected_next_date.isoformat() if expected_next_date else None,
        "expected_exit_date": lifecycle_fields["expected_exit_date"],
        "expected_transition_type": lifecycle_fields["expected_transition_type"],
        "stale_after_date": stale_after_date.isoformat() if stale_after_date else None,
        "refresh_policy": lifecycle_fields["refresh_policy"],
        "transition_rule": transition_rule,
        "status": status,
        "confidence": confidence,
    }


def infer_training_state(row: dict, raw_label: str, as_of: date, lifecycle: dict | None = None) -> dict:
    label = norm_space(raw_label)
    lower = label.lower()
    role = (row.get("role") or "").lower()
    current_status = (row.get("current_status") or "").lower()
    if current_status in {"former", "alumni"} or any(token in lower for token in ["recent graduate", "alumni", "former"]):
        return stage_result(
            label,
            "COMPLETED_OR_FORMER",
            "post_training_or_alumni",
            None,
            900,
            role or "trainee",
            "terminal_or_historical_state; do not auto-advance",
            0.75,
            status="former",
        )
    if role == "medical_student":
        phase = norm_space(row.get("phase") or label)
        phase_lower = phase.lower()
        ay, start, end = academic_year(as_of, 8)
        stale_after = end + timedelta(days=45)
        if phase_lower == "ms1":
            return stage_result(
                phase,
                "MEDICAL_SCHOOL_MS1",
                "medical_school",
                1,
                101,
                "medical_student",
                "expected annual medical-school class advancement around Aug 1",
                0.85,
                lifecycle=lifecycle,
                academic_year_value=ay,
                estimated_start_date=start,
                estimated_end_date=end,
                expected_next_stage="MEDICAL_SCHOOL_MS2",
                expected_next_date=next_date_for(as_of, 8),
                stale_after_date=stale_after,
            )
        if phase_lower == "ms2":
            return stage_result(
                phase,
                "MEDICAL_SCHOOL_MS2",
                "medical_school",
                2,
                102,
                "medical_student",
                "expected annual medical-school class advancement around Aug 1",
                0.85,
                lifecycle=lifecycle,
                academic_year_value=ay,
                estimated_start_date=start,
                estimated_end_date=end,
                expected_next_stage="MEDICAL_SCHOOL_CLINICAL_PHASE",
                expected_next_date=next_date_for(as_of, 8),
                stale_after_date=stale_after,
            )
        if phase_lower in {"ms3/4", "ms3", "ms4"}:
            return stage_result(
                phase,
                "MEDICAL_SCHOOL_MS3_OR_MS4",
                "medical_school",
                3,
                103,
                "medical_student",
                "clinical-phase student label is ambiguous; refresh on annual directory update rather than auto-advance",
                0.62,
                lifecycle=lifecycle,
                academic_year_value=ay,
                estimated_start_date=start,
                estimated_end_date=end,
                expected_next_stage="MEDICAL_SCHOOL_CLINICAL_OR_GRADUATING_PHASE",
                expected_next_date=next_date_for(as_of, 8),
                stale_after_date=stale_after,
            )
        if "phd" in phase_lower:
            return stage_result(
                phase,
                "MSTP_PHD_PHASE",
                "research_phase",
                None,
                150,
                "medical_student",
                "MSTP PhD phase duration is individualized; refresh from public directory annually",
                0.78,
                lifecycle=lifecycle,
                stale_after_date=as_of + timedelta(days=395),
            )
        return stage_result(
            phase or label,
            "MEDICAL_SCHOOL_PHASE_UNKNOWN",
            "medical_school",
            None,
            199,
            "medical_student",
            "unknown student phase; refresh from source",
            0.35,
            lifecycle=lifecycle,
            stale_after_date=as_of + timedelta(days=395),
        )
    pgy_match = re.search(r"\b(?:pgy|post graduate year)\s*[- ]?(\d+)\b", lower)
    if pgy_match:
        index = int(pgy_match.group(1))
        ay, start, end = academic_year(as_of, 7)
        next_stage = f"GME_PGY_{index + 1}" if index < 9 else None
        return stage_result(
            label,
            f"GME_PGY_{index}",
            "clinical_postgraduate",
            index,
            200 + index,
            role or "resident",
            "expected GME annual advancement around Jul 1 unless program-specific exception",
            0.9,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_stage=next_stage,
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    cy_match = re.search(r"\bcy\s*[- ]?(\d+)\b", lower)
    if cy_match:
        index = int(cy_match.group(1))
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            f"GME_CLINICAL_YEAR_{index}",
            "clinical_postgraduate",
            index,
            220 + index,
            role or "resident",
            "expected clinical-year advancement around Jul 1; map to PGY with program review",
            0.72,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_stage=f"GME_CLINICAL_YEAR_{index + 1}",
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    ca_match = re.search(r"\bca\s*[- ]?(\d+)\b", lower)
    if ca_match:
        index = int(ca_match.group(1))
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            f"GME_CLINICAL_ANESTHESIA_YEAR_{index}",
            "clinical_postgraduate",
            index,
            230 + index,
            role or "resident",
            "expected anesthesia clinical-year advancement around Jul 1; map to PGY with program review",
            0.74,
            lifecycle={
                **(lifecycle or {}),
                "rule_key": "anesthesia_ca_phase_3y",
                "lifecycle_code": "US_GME_ANESTHESIA_CA_PHASE_3Y",
                "nominal_years": 3,
                "clock_rollover_month": 7,
                "auto_advance": True,
                "terminal_stage": "GME_RESIDENCY_COMPLETION",
            },
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_stage=f"GME_CLINICAL_ANESTHESIA_YEAR_{index + 1}",
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    if "intern" in lower:
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            "GME_PGY_1",
            "clinical_postgraduate",
            1,
            201,
            "resident",
            "intern label maps to PGY1; expected annual advancement around Jul 1",
            0.78,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_stage="GME_PGY_2",
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    if role == "resident" and re.search(r"class of \d{4}", lower):
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            "GME_RESIDENT_CLASS_YEAR",
            "clinical_postgraduate",
            None,
            260,
            "resident",
            "class-year resident label; derive exact PGY only with program-duration context",
            0.62,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    resident_ordinal_match = re.search(r"\b(first|1st|second|2nd|third|3rd|fourth|4th|fifth|5th)\s+year\s+residents?\b", lower)
    if role == "resident" and resident_ordinal_match:
        index = {
            "first": 1,
            "1st": 1,
            "second": 2,
            "2nd": 2,
            "third": 3,
            "3rd": 3,
            "fourth": 4,
            "4th": 4,
            "fifth": 5,
            "5th": 5,
        }[resident_ordinal_match.group(1)]
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            f"GME_PGY_{index}",
            "clinical_postgraduate",
            index,
            200 + index,
            "resident",
            "ordinal resident-year label maps to PGY with program review",
            0.72,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_stage=f"GME_PGY_{index + 1}",
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    if role == "resident" and "preliminary" in lower:
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            "GME_PRELIMINARY_RESIDENT",
            "clinical_postgraduate",
            1,
            265,
            "resident",
            "preliminary resident label usually maps to a one-year GME state; verify against program context",
            0.66,
            lifecycle={"rule_key": "preliminary_one_year", "lifecycle_code": "US_GME_PRELIMINARY_1Y", "nominal_years": 1, "clock_rollover_month": 7, "auto_advance": True, "terminal_stage": "TRANSITION_OUT_OR_PROGRAM_SPECIFIC_NEXT_STATE"},
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_stage="TRANSITION_OUT_OR_PROGRAM_SPECIFIC_NEXT_STATE",
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    if role == "resident" and "independent" in lower:
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            "GME_INDEPENDENT_RESIDENT",
            "clinical_postgraduate",
            None,
            270,
            "resident",
            "independent-resident track is program-specific; refresh annually and map with specialty rules",
            0.62,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    if "lab resident" in lower or "research resident" in lower:
        return stage_result(
            label,
            "GME_RESEARCH_OR_LAB_YEAR",
            "clinical_postgraduate_research",
            None,
            280,
            "resident",
            "research/lab resident state is program-specific; refresh from roster rather than auto-advance",
            0.68,
            lifecycle=lifecycle,
            stale_after_date=as_of + timedelta(days=395),
        )
    if "chief" in lower and "resident" in lower:
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            "GME_CHIEF_RESIDENT",
            "clinical_postgraduate",
            None,
            290,
            "resident",
            "chief year is terminal/program-specific; refresh on next academic-year roster",
            0.72,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            stale_after_date=end + timedelta(days=45),
        )
    fellow_year_match = re.search(r"\b(?:first|1st|second|2nd|third|3rd|fourth|4th)\b", lower)
    if role == "fellow" and fellow_year_match:
        token = fellow_year_match.group(0)
        index = {
            "first": 1,
            "1st": 1,
            "second": 2,
            "2nd": 2,
            "third": 3,
            "3rd": 3,
            "fourth": 4,
            "4th": 4,
        }[token]
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            f"FELLOWSHIP_YEAR_{index}",
            "fellowship",
            index,
            300 + index,
            "fellow",
            "expected fellowship annual advancement around Jul 1; terminal year requires program-length context",
            0.82,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_stage=f"FELLOWSHIP_YEAR_{index + 1}",
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    if role == "fellow":
        if any(
            token in lower
            for token in [
                "advanced musculoskeletal",
                "nuclear radiology",
                "abr alternate pathway",
                "oncologic imaging",
            ]
        ):
            ay, start, end = academic_year(as_of, 7)
            return stage_result(
                label,
                "FELLOWSHIP_CURRENT_YEAR_UNKNOWN",
                "fellowship",
                None,
                399,
                "fellow",
                "fellowship specialty section lacks year; refresh on next roster and use program-specific duration if available",
                0.58,
                lifecycle=lifecycle,
                academic_year_value=ay,
                estimated_start_date=start,
                estimated_end_date=end,
                expected_next_date=next_date_for(as_of, 7),
                stale_after_date=end + timedelta(days=45),
            )
        if any(token in lower for token in ["post-doc", "postdoc", "nrsa"]):
            return stage_result(
                label,
                "POSTDOCTORAL_RESEARCH_FELLOW",
                "research_phase",
                None,
                380,
                "fellow",
                "postdoctoral fellow duration is individualized; refresh annually",
                0.7,
                lifecycle=lifecycle,
                stale_after_date=as_of + timedelta(days=395),
            )
        if "fellow" in lower or "fellowship" in lower or not lower:
            ay, start, end = academic_year(as_of, 7)
            return stage_result(
                label,
                "FELLOWSHIP_CURRENT_YEAR_UNKNOWN",
                "fellowship",
                None,
                399,
                "fellow",
                "current fellow but year not normalized; refresh on next roster and use program-specific duration if available",
                0.52 if lower else 0.42,
                lifecycle=lifecycle,
                academic_year_value=ay,
                estimated_start_date=start,
                estimated_end_date=end,
                expected_next_date=next_date_for(as_of, 7),
                stale_after_date=end + timedelta(days=45),
            )
    if role == "resident" and not lower:
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            "GME_RESIDENT_YEAR_UNKNOWN",
            "clinical_postgraduate",
            None,
            299,
            "resident",
            "current resident but year not visible on source; refresh on next roster",
            0.42,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    if role == "resident" and lower in {"current residents", "residents"}:
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            "GME_RESIDENT_YEAR_UNKNOWN",
            "clinical_postgraduate",
            None,
            299,
            "resident",
            "current resident but exact year not visible on source; refresh on next roster",
            0.46,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    if role == "fellow":
        ay, start, end = academic_year(as_of, 7)
        return stage_result(
            label,
            "FELLOWSHIP_CURRENT_YEAR_UNKNOWN",
            "fellowship",
            None,
            399,
            "fellow",
            "current fellow section label lacks year; refresh on next roster and use program-specific duration if available",
            0.5,
            lifecycle=lifecycle,
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_date=next_date_for(as_of, 7),
            stale_after_date=end + timedelta(days=45),
        )
    return stage_result(
        label,
        "TRAINING_STAGE_UNMAPPED",
        "unknown",
        None,
        999,
        role or "trainee",
        "unmapped source label; review rule table before auto-advancing",
        0.25,
        lifecycle=lifecycle,
        stale_after_date=as_of + timedelta(days=395),
    )


def observed_at_for_source(conn: sqlite3.Connection, source_key: str | None, as_of: date) -> str:
    if source_key:
        row = conn.execute("SELECT fetched_at FROM sources WHERE source_key = ?", (source_key,)).fetchone()
        if row and row["fetched_at"]:
            return row["fetched_at"]
    return f"{as_of.isoformat()}T00:00:00+00:00"


def insert_training_states(conn: sqlite3.Connection, row: dict) -> None:
    person_key = row.get("person_key") or key_for("person", row["name"])
    programs = listish(row.get("program_memberships")) or listish(row.get("program"))
    if not programs:
        programs = [""]
    source_key = row.get("source_key") or (listish(row.get("source_memberships")) or [""])[0]
    labels = listish(row.get("training_year_labels_seen")) or listish(row.get("training_year_label"))
    if not labels and row.get("role") == "medical_student":
        labels = listish(row.get("phase"))
    if not labels:
        labels = [""]
    as_of = date.today()
    observed_at = observed_at_for_source(conn, source_key, as_of)
    for program_name in programs:
        program_id = program_key(program_name, row.get("role")) if program_name else None
        lifecycle = match_lifecycle_rule(program_name, row.get("role"))
        for label in labels:
            state = infer_training_state(row, label, as_of, lifecycle)
            state_key = key_for("state", f"{person_key}:{program_id or ''}:{source_key}:{label}:{state['normalized_stage']}")
            conn.execute(
                """
                INSERT OR IGNORE INTO person_training_states
                (state_key, person_key, program_key, source_key, observed_at, as_of_date,
                 raw_stage_label, normalized_stage, stage_family, stage_index, stage_rank,
                 trainee_category, lifecycle_rule_key, lifecycle_code, lifecycle_stage,
                 academic_year, estimated_start_date, estimated_end_date,
                 expected_next_stage, expected_next_date, expected_exit_date,
                 expected_transition_type, stale_after_date, refresh_policy, transition_rule,
                 status, confidence, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state_key,
                    person_key,
                    program_id,
                    source_key or None,
                    observed_at,
                    as_of.isoformat(),
                    state["raw_stage_label"],
                    state["normalized_stage"],
                    state["stage_family"],
                    state["stage_index"],
                    state["stage_rank"],
                    state["trainee_category"],
                    state["lifecycle_rule_key"],
                    state["lifecycle_code"],
                    state["lifecycle_stage"],
                    state["academic_year"],
                    state["estimated_start_date"],
                    state["estimated_end_date"],
                    state["expected_next_stage"],
                    state["expected_next_date"],
                    state["expected_exit_date"],
                    state["expected_transition_type"],
                    state["stale_after_date"],
                    state["refresh_policy"],
                    state["transition_rule"],
                    state["status"],
                    state["confidence"],
                    dumps(
                        {
                            "origin": "source_training_label",
                            "source_url": row.get("source_url") or row.get("profile_anchor_url"),
                            "program": program_name,
                            "lifecycle_rule_key": state["lifecycle_rule_key"],
                            "raw_row_role": row.get("role"),
                            "raw_current_status": row.get("current_status"),
                        }
                    ),
                ),
            )


def insert_training_events(conn: sqlite3.Connection, resolver: OrganizationResolver, row: dict) -> None:
    person_key = row.get("person_key") or key_for("person", row["name"])
    for field, event_type in TRAINING_FIELDS.items():
        raw_value = norm_space(row.get(field))
        if not raw_value:
            continue
        org_id, status, confidence = resolver.resolve(raw_value, event_type)
        conn.execute(
            """
            INSERT INTO person_training_events
            (person_key, event_type, raw_value, organization_id, source_key,
             resolver_status, confidence, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_key,
                event_type,
                raw_value,
                org_id,
                row.get("source_key"),
                status,
                confidence,
                dumps({"field": field, "source_url": row.get("source_url")}),
            ),
        )
        conn.execute(
            """
            INSERT INTO evidence_claims
            (person_key, claim_type, claim_value, source_key, source_url, source_type,
             confidence, status, match_features_json, reconciliation_notes, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                person_key,
                event_type,
                raw_value,
                row.get("source_key"),
                row.get("source_url"),
                row.get("source_type"),
                0.95 if status == "seeded_alias" else 0.75,
                "accepted",
                dumps(
                    [
                        "official_roster_source",
                        "direct_structured_field",
                        "person_program_context",
                        status,
                    ]
                ),
                "Accepted as roster-published training field; organization canonicalization remains separately reviewable when resolver_status is cleaned_label.",
                dumps(
                    {
                        "origin": "roster_field",
                        "resolver_status": status,
                        "utility_key": "official_roster",
                    }
                ),
            ),
        )


def person_key_by_normalized_name(conn: sqlite3.Connection) -> dict[str, str]:
    mapping = {}
    for row in conn.execute("SELECT person_key, display_name FROM people"):
        mapping[normalized_label(row["display_name"])] = row["person_key"]
    return mapping


def insert_career_events(conn: sqlite3.Connection) -> None:
    existing_people = person_key_by_normalized_name(conn)
    attending_path = ARTIFACTS / "penn_attending_candidates.json"
    if attending_path.exists():
        for row in load_json(attending_path):
            normalized_name = normalized_label(row.get("name"))
            person_key = existing_people.get(normalized_name)
            conn.execute(
                """
                INSERT INTO career_events
                (person_key, display_name, event_type, role_title, organization_name,
                 department, program_context, event_year, source_key, source_url,
                 confidence, status, match_features_json, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    person_key,
                    row.get("name", ""),
                    "current_penn_attending_candidate",
                    row.get("role_title") or row.get("title") or "",
                    "University of Pennsylvania / Penn Medicine",
                    row.get("department"),
                    row.get("program_context"),
                    None,
                    row.get("source_key"),
                    row.get("source_url"),
                    0.7 if person_key else 0.55,
                    "needs_review" if person_key else "candidate",
                    dumps(
                        [
                            "official_penn_faculty_page",
                            "exact_current_person_name_match" if person_key else "not_linked_to_existing_person",
                        ]
                    ),
                    dumps(row),
                ),
            )
            insert_contacts(
                conn,
                row,
                person_key=person_key,
                subject_type="current_penn_attending_candidate",
                allow_unmatched_person=True,
            )
    outcome_path = ARTIFACTS / "penn_outcome_candidates.json"
    if outcome_path.exists():
        for row in load_json(outcome_path):
            conn.execute(
                """
                INSERT INTO career_events
                (person_key, display_name, event_type, role_title, organization_name,
                 department, program_context, event_year, source_key, source_url,
                 confidence, status, match_features_json, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    None,
                    row.get("display_name") or "",
                    "penn_alumni_outcome_candidate",
                    "",
                    "",
                    "",
                    row.get("program_context"),
                    None,
                    row.get("source_key"),
                    row.get("source_url"),
                    row.get("confidence", 0.25),
                    row.get("status", "candidate"),
                    dumps(row.get("match_features", [])),
                    dumps(row),
                ),
            )
    profile_claims_path = ARTIFACTS / "penn_attending_profile_claims.json"
    if profile_claims_path.exists():
        for row in load_json(profile_claims_path):
            normalized_name = normalized_label(row.get("display_name"))
            person_key = existing_people.get(normalized_name)
            conn.execute(
                """
                INSERT INTO career_events
                (person_key, display_name, event_type, role_title, organization_name,
                 department, program_context, event_year, source_key, source_url,
                 confidence, status, match_features_json, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    person_key,
                    row.get("display_name") or "",
                    row.get("event_type") or "attending_profile_training_history_candidate",
                    row.get("claim_type") or "",
                    row.get("organization_name") or "",
                    row.get("department") or "",
                    row.get("program_context") or "",
                    row.get("event_year"),
                    row.get("source_key"),
                    row.get("source_url"),
                    row.get("confidence", 0.45),
                    row.get("status", "candidate"),
                    dumps(row.get("match_features", [])),
                    dumps(row),
                ),
            )


def insert_official_program_coverage(conn: sqlite3.Connection) -> None:
    universe_path = ARTIFACTS / "penn_gme_program_universe.json"
    source_path = ARTIFACTS / "penn_gme_program_universe_source.json"
    coverage_path = ARTIFACTS / "penn_gme_program_coverage.json"
    if not (universe_path.exists() and source_path.exists() and coverage_path.exists()):
        return
    source = load_json(source_path)
    conn.execute(
        """
        INSERT OR REPLACE INTO sources
        (source_key, source_url, source_type, title, fetched_at, http_status, sha256, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source["source_key"],
            source["url"],
            source["source_type"],
            "HUP GME Programs",
            source.get("fetched_at"),
            source.get("http_status"),
            source.get("sha256"),
            dumps(source),
        ),
    )
    for record in load_json(universe_path):
        conn.execute(
            """
            INSERT OR REPLACE INTO official_program_universe
            (official_program_key, source_key, source_url, sponsoring_institution, department,
             program_type, program_name, program_url, source_type, confidence, evidence_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["entry_key"],
                source["source_key"],
                record["source_url"],
                record["sponsoring_institution"],
                record["department"],
                record["program_type"],
                record["program_name"],
                record.get("program_url"),
                record.get("source_type"),
                record.get("confidence", 0.0),
                dumps(record.get("evidence", {})),
            ),
        )
    audited_at = datetime.now(timezone.utc).isoformat()
    official_program_keys = {row[0] for row in conn.execute("SELECT official_program_key FROM official_program_universe")}
    local_program_keys = {row[0] for row in conn.execute("SELECT program_key FROM programs")}
    for row in load_json(coverage_path):
        official_program_key = row["entry_key"]
        if official_program_key not in official_program_keys:
            continue
        matched_program_key = row.get("matched_program_key") or None
        if matched_program_key and matched_program_key not in local_program_keys:
            matched_program_key = None
        conn.execute(
            """
            INSERT OR REPLACE INTO official_program_coverage_audit
            (official_program_key, coverage_status, matched_program_key, matched_program_name,
             captured_people_count, match_method, match_confidence, discovery_classification,
             discovery_title, discovery_url, notes, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                official_program_key,
                row["coverage_status"],
                matched_program_key,
                row.get("matched_program_name"),
                int(row.get("captured_people_count") or 0),
                row.get("match_method"),
                float(row.get("match_confidence") or 0.0),
                row.get("discovery_classification"),
                row.get("discovery_title"),
                row.get("discovery_url"),
                row.get("notes"),
                audited_at,
            ),
        )


def insert_official_program_gap_source_candidates(conn: sqlite3.Connection) -> None:
    probes_path = ARTIFACTS / "penn_gme_gap_source_probes.json"
    candidates_path = ARTIFACTS / "penn_gme_gap_source_candidates.json"
    if probes_path.exists():
        for row in load_json(probes_path):
            conn.execute(
                """
                INSERT INTO official_program_source_probes
                (official_program_key, program_name, coverage_status, source_role,
                 requested_url, effective_url, http_status, title, content_type,
                 text_length, roster_term_count, context_term_count,
                 supported_person_structure_count, supported_person_structure_types,
                 heading_name_list_support_allowed, sha256, fetched_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["official_program_key"],
                    row.get("program_name"),
                    row.get("coverage_status"),
                    row.get("source_role"),
                    row.get("requested_url"),
                    row.get("effective_url"),
                    row.get("http_status") or None,
                    row.get("title"),
                    row.get("content_type"),
                    int(row.get("text_length") or 0),
                    int(row.get("roster_term_count") or 0),
                    int(row.get("context_term_count") or 0),
                    int(row.get("supported_person_structure_count") or 0),
                    dumps(row.get("supported_person_structure_types", [])),
                    int(row.get("heading_name_list_support_allowed") or 0),
                    row.get("sha256"),
                    row.get("fetched_at"),
                    row.get("error"),
                ),
            )
    if candidates_path.exists():
        for row in load_json(candidates_path):
            conn.execute(
                """
                INSERT OR REPLACE INTO official_program_source_candidates
                (candidate_key, official_program_key, department, program_type,
                 program_name, coverage_status, source_role, candidate_status,
                 priority, confidence, candidate_title, candidate_url, http_status,
                 roster_term_count, context_term_count, supported_person_structure_count,
                 supported_person_structure_types, reasons_json, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["candidate_key"],
                    row["official_program_key"],
                    row.get("department"),
                    row.get("program_type"),
                    row.get("program_name"),
                    row.get("coverage_status"),
                    row.get("source_role"),
                    row.get("candidate_status"),
                    int(row.get("priority") or 0),
                    float(row.get("confidence") or 0.0),
                    row.get("candidate_title"),
                    row.get("candidate_url"),
                    row.get("http_status") if row.get("http_status") != "" else None,
                    int(row.get("roster_term_count") or 0),
                    int(row.get("context_term_count") or 0),
                    int(row.get("supported_person_structure_count") or 0),
                    dumps(row.get("supported_person_structure_types", [])),
                    dumps(row.get("reasons", [])),
                    dumps(row),
                ),
            )


def load_people(conn: sqlite3.Connection, resolver: OrganizationResolver) -> None:
    people = []
    for path in PERSON_FILES:
        people.extend(load_json(path))
    for row in people:
        insert_person(conn, row)
        insert_contacts(conn, row)
        insert_memberships(conn, row)
        insert_training_states(conn, row)
        insert_training_events(conn, resolver, row)
    insert_career_events(conn)


def export_review_queue(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT * FROM v_organization_review_queue").fetchall()
    with (ARTIFACTS / "organization_review_queue.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["raw_value", "event_type", "mention_count", "resolver_status", "canonical_name"],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows([dict(row) for row in rows])


def write_summary(conn: sqlite3.Connection, db_path: Path) -> None:
    counts = {}
    for table in [
        "people",
        "sources",
        "source_utilities",
        "program_lifecycle_rules",
        "programs",
        "organizations",
        "organization_aliases",
        "organization_identifiers",
        "organization_identifier_candidates",
        "medical_student_source_audit",
        "person_training_events",
        "person_training_states",
        "person_evidence_review_packets",
        "person_evidence_reviewer_decisions",
        "person_evidence_reviewer_decision_queue",
        "person_evidence_reviewer_decision_audit",
        "training_state_snapshots",
        "training_state_snapshot_rows",
        "training_state_transition_events",
        "training_state_transition_rollups",
        "person_enrichment_coverage",
        "program_enrichment_coverage",
        "person_enrichment_work_queue",
        "person_enrichment_execution_readiness",
        "person_enrichment_execution_readiness_rollups",
        "training_state_machine_audit",
        "person_training_state_machine_audit",
        "program_training_state_machine_audit",
        "training_state_refresh_expectations",
        "person_refresh_expectations",
        "program_refresh_expectations",
        "category_refresh_expectations",
        "training_temporal_contracts",
        "training_temporal_contract_rollups",
        "trainee_profile_search_queries",
        "trainee_profile_search_observations",
        "trainee_profile_discovery_candidates",
        "prior_training_search_queries",
        "prior_training_search_observations",
        "prior_training_discovery_candidates",
        "career_events",
        "attending_biosketch_bridge_candidates",
        "attending_trend_reconciliation",
        "attending_trend_review_claims",
        "attending_trend_acceptance_audit",
        "attending_trend_reviewer_decisions",
        "attending_trend_reviewer_decision_queue",
        "attending_trend_reviewer_decision_audit",
        "accepted_attending_trend_facts",
        "attending_trend_review_rollups",
        "npi_candidate_claims",
        "npi_source_observations",
        "person_contacts",
        "contact_assurance_audit",
        "evidence_claims",
        "evidence_reconciliation_decisions",
        "person_reconciliation_decisions",
        "enrichment_acceptance_audit",
        "accepted_enrichment_claims",
        "warehouse_reproducibility_audit",
        "source_quality_observations",
        "source_utility_scorecard",
        "search_utility_assurance",
        "corpus_action_worklist",
        "official_program_universe",
        "official_program_coverage_audit",
        "official_program_source_probes",
        "official_program_source_search_queries",
        "official_program_source_search_observations",
        "official_program_source_candidates",
        "official_program_gap_reason_audit",
        "official_gap_roster_reconciliation",
        "official_gap_roster_program_resolution",
        "official_program_coverage_assurance_audit",
        "official_program_coverage_action_queue",
        "official_program_alias_review_packets",
        "official_program_alias_reviewer_decisions",
        "official_program_alias_reviewer_decision_queue",
        "official_program_alias_reviewer_decision_audit",
        "accepted_official_program_alias_mappings",
        "official_program_alias_reconciliation_candidates",
        "program_identifier_source_observations",
        "program_identifier_candidates",
        "program_identifier_reconciliation",
        "official_program_identifiers",
        "program_lifecycle_consistency_audit",
    ]:
        counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    resolver_counts = {
        row["resolver_status"]: row["count"]
        for row in conn.execute(
            "SELECT resolver_status, COUNT(*) AS count FROM person_training_events GROUP BY resolver_status"
        )
    }
    category_counts = {
        row["category"]: row["count"]
        for row in conn.execute("SELECT category, COUNT(*) AS count FROM organizations GROUP BY category")
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "database_path": str(db_path.relative_to(ROOT)),
        "counts": counts,
        "resolver_counts": resolver_counts,
        "organization_category_counts": category_counts,
    }
    (ARTIFACTS / "warehouse_summary.json").write_text(
        dumps(payload) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    db_path = DEFAULT_DB
    conn = init_db(db_path)
    with conn:
        conn.execute(
            "INSERT INTO load_runs (loaded_at, input_fingerprint, notes) VALUES (?, ?, ?)",
            (
                datetime.now(timezone.utc).isoformat(),
                fingerprint(
                    PERSON_FILES
                    + SOURCE_FILES
                    + OPTIONAL_SOURCE_FILES
                    + [ORG_SEEDS, ENRICHMENT_SOURCES, TRAINING_LIFECYCLE_RULES, SCHEMA]
                ),
                "Penn first-pass warehouse build",
            ),
        )
        insert_sources(conn)
        insert_source_utilities(conn)
        insert_lifecycle_rules(conn)
        insert_manual_source_quality_observations(conn)
        resolver = OrganizationResolver(conn, ORG_SEEDS)
        load_people(conn, resolver)
        insert_trainee_profile_claims(conn)
        insert_trainee_profile_discovery_claims(conn)
        insert_prior_training_discovery_claims(conn)
        insert_research_candidate_claims(conn)
        insert_official_program_coverage(conn)
        insert_official_program_gap_source_candidates(conn)
        export_review_queue(conn)
        write_summary(conn, db_path)
    conn.close()
    print(f"wrote {db_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
