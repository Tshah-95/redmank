#!/usr/bin/env python3
"""Build the redmank SQLite warehouse from generated flat-file artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "db" / "schema.sql"
ARTIFACTS = ROOT / "artifacts" / "data"
DEFAULT_DB = ARTIFACTS / "redmank.sqlite"
ORG_SEEDS = ROOT / "config" / "organization_seed_aliases.json"
ENRICHMENT_SOURCES = ROOT / "config" / "enrichment_sources.json"

PERSON_FILES = [
    ARTIFACTS / "penn_training_people_unique.json",
    ARTIFACTS / "penn_affiliated_people.json",
    ARTIFACTS / "penn_mstp_students.json",
]
SOURCE_FILES = [
    ARTIFACTS / "penn_training_sources.json",
    ARTIFACTS / "penn_affiliated_sources.json",
    ARTIFACTS / "penn_source_discovery.json",
]
OPTIONAL_SOURCE_FILES = [
    ARTIFACTS / "penn_affiliated_source_discovery.json",
    ARTIFACTS / "penn_attending_candidate_sources.json",
    ARTIFACTS / "penn_outcome_candidate_sources.json",
    ARTIFACTS / "penn_attending_candidates.json",
    ARTIFACTS / "penn_outcome_candidates.json",
    ARTIFACTS / "penn_gme_program_universe.json",
    ARTIFACTS / "penn_gme_program_universe_source.json",
    ARTIFACTS / "penn_gme_program_coverage.json",
    ARTIFACTS / "research_candidate_claims.json",
    ARTIFACTS / "research_candidate_summary.json",
    ARTIFACTS / "manual_source_quality_observations.json",
]

TRAINING_FIELDS = {
    "medical_school": "medical_school",
    "residency_program": "residency_program",
    "undergraduate_school": "undergraduate_school",
    "graduate_school": "graduate_school",
}


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
    for optional_sources, source_type in [
        (ARTIFACTS / "penn_attending_candidate_sources.json", "official_attending_faculty_candidate"),
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
    path = ARTIFACTS / "research_candidate_claims.json"
    if not path.exists():
        return
    claims = load_json(path)
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
    generated_at = datetime.now(timezone.utc).isoformat()
    summary_path = ARTIFACTS / "research_candidate_summary.json"
    summary = load_json(summary_path) if summary_path.exists() else {}
    people_processed = int(summary.get("people_processed", 0))
    for source_key in sorted({row["source_key"] for row in claims}):
        source_claims = [row for row in claims if row["source_key"] == source_key]
        conn.execute(
            """
            INSERT INTO source_quality_observations
            (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
             rejected_claims, ambiguous_claims, notes, metrics_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_key,
                summary.get("generated_at") or generated_at,
                people_processed or len({row["person_key"] for row in source_claims}),
                sum(1 for row in source_claims if row["status"] == "candidate"),
                sum(1 for row in source_claims if row["status"] == "accepted"),
                sum(1 for row in source_claims if row["status"] == "rejected"),
                sum(1 for row in source_claims if row["status"] == "needs_review"),
                "Replayed durable research-candidate artifact; no claims accepted automatically.",
                dumps(
                    {
                        "claims": len(source_claims),
                        "mean_confidence": round(
                            sum(float(row["confidence"]) for row in source_claims) / len(source_claims), 4
                        )
                        if source_claims
                        else 0,
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
    academic_year_value: str | None = None,
    estimated_start_date: date | None = None,
    estimated_end_date: date | None = None,
    expected_next_stage: str | None = None,
    expected_next_date: date | None = None,
    stale_after_date: date | None = None,
) -> dict:
    return {
        "raw_stage_label": raw_label,
        "normalized_stage": normalized_stage,
        "stage_family": stage_family,
        "stage_index": stage_index,
        "stage_rank": stage_rank,
        "trainee_category": trainee_category,
        "academic_year": academic_year_value,
        "estimated_start_date": estimated_start_date.isoformat() if estimated_start_date else None,
        "estimated_end_date": estimated_end_date.isoformat() if estimated_end_date else None,
        "expected_next_stage": expected_next_stage,
        "expected_next_date": expected_next_date.isoformat() if expected_next_date else None,
        "stale_after_date": stale_after_date.isoformat() if stale_after_date else None,
        "transition_rule": transition_rule,
        "status": status,
        "confidence": confidence,
    }


def infer_training_state(row: dict, raw_label: str, as_of: date) -> dict:
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
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
            expected_next_stage=f"GME_CLINICAL_YEAR_{index + 1}",
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
            academic_year_value=ay,
            estimated_start_date=start,
            estimated_end_date=end,
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
        for label in labels:
            state = infer_training_state(row, label, as_of)
            state_key = key_for("state", f"{person_key}:{program_id or ''}:{source_key}:{label}:{state['normalized_stage']}")
            conn.execute(
                """
                INSERT OR IGNORE INTO person_training_states
                (state_key, person_key, program_key, source_key, observed_at, as_of_date,
                 raw_stage_label, normalized_stage, stage_family, stage_index, stage_rank,
                 trainee_category, academic_year, estimated_start_date, estimated_end_date,
                 expected_next_stage, expected_next_date, stale_after_date, transition_rule,
                 status, confidence, evidence_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    state["academic_year"],
                    state["estimated_start_date"],
                    state["estimated_end_date"],
                    state["expected_next_stage"],
                    state["expected_next_date"],
                    state["stale_after_date"],
                    state["transition_rule"],
                    state["status"],
                    state["confidence"],
                    dumps(
                        {
                            "origin": "source_training_label",
                            "source_url": row.get("source_url") or row.get("profile_anchor_url"),
                            "program": program_name,
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
    for row in load_json(coverage_path):
        conn.execute(
            """
            INSERT OR REPLACE INTO official_program_coverage_audit
            (official_program_key, coverage_status, matched_program_key, matched_program_name,
             captured_people_count, match_method, match_confidence, discovery_classification,
             discovery_title, discovery_url, notes, audited_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["entry_key"],
                row["coverage_status"],
                row.get("matched_program_key") or None,
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
        "programs",
        "organizations",
        "organization_aliases",
        "organization_identifiers",
        "person_training_events",
        "person_training_states",
        "career_events",
        "person_contacts",
        "evidence_claims",
        "source_quality_observations",
        "official_program_universe",
        "official_program_coverage_audit",
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
                fingerprint(PERSON_FILES + SOURCE_FILES + OPTIONAL_SOURCE_FILES + [ORG_SEEDS, ENRICHMENT_SOURCES, SCHEMA]),
                "Penn first-pass warehouse build",
            ),
        )
        insert_sources(conn)
        insert_source_utilities(conn)
        insert_manual_source_quality_observations(conn)
        resolver = OrganizationResolver(conn, ORG_SEEDS)
        load_people(conn, resolver)
        insert_research_candidate_claims(conn)
        insert_official_program_coverage(conn)
        export_review_queue(conn)
        write_summary(conn, db_path)
    conn.close()
    print(f"wrote {db_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
