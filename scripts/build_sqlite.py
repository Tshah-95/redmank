#!/usr/bin/env python3
"""Build the redmank SQLite warehouse from generated flat-file artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
from datetime import datetime, timezone
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


def load_people(conn: sqlite3.Connection, resolver: OrganizationResolver) -> None:
    people = []
    for path in PERSON_FILES:
        people.extend(load_json(path))
    for row in people:
        insert_person(conn, row)
        insert_contacts(conn, row)
        insert_memberships(conn, row)
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
        "career_events",
        "person_contacts",
        "evidence_claims",
        "source_quality_observations",
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
        export_review_queue(conn)
        write_summary(conn, db_path)
    conn.close()
    print(f"wrote {db_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
