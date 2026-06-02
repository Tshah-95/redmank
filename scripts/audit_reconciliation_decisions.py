#!/usr/bin/env python3
"""Create deterministic decision records for candidate evidence reconciliation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

REVIEW_READY_PUBMED_FEATURES = {
    "penn_affiliation",
    "prior_training_or_education_affiliation",
    "program_topic_match",
    "orcid_present",
}
NPI_REVIEW_FEATURES = {
    "state_location_match",
    "philadelphia_location",
    "physician_specialty_taxonomy",
    "student_or_training_taxonomy",
    "program_taxonomy_topic_match",
}
PROFILE_REVIEW_FEATURES = {
    "official_trainee_profile",
    "official_student_directory",
    "roster_linked_profile",
    "directory_linked_profile_anchor",
    "official_domain",
    "profile_path",
    "structured_profile_field",
    "roster_structured_field_crosscheck",
    "research_training_field",
}
NON_NAME_FEATURES = (
    REVIEW_READY_PUBMED_FEATURES
    | NPI_REVIEW_FEATURES
    | PROFILE_REVIEW_FEATURES
    | {"recent_publication", "bounded_author_query"}
)


def norm_space(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def normalized_person_name(value: str | None) -> str:
    value = norm_space(value).lower()
    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(
        r"\b(md|m\.d\.|do|d\.o\.|phd|ph\.d\.|mbe|msce|mse?d|mph|mba|ms|m\.s\.|ma|m\.a\.)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return norm_space(value)


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def key_for(prefix: str, *parts: object) -> str:
    basis = "|".join(str(part or "") for part in parts)
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def person_name_index(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = defaultdict(list)
    for row in rows(
        conn,
        """
        SELECT person_key, display_name, role, current_status
        FROM people
        """,
    ):
        index[normalized_person_name(row["display_name"])].append(row)
    return index


def load_queue(conn: sqlite3.Connection) -> list[dict]:
    return rows(
        conn,
        """
        SELECT record_type, record_id, person_key, display_name, role, claim_type,
               claim_value, event_type, organization_name, event_year, source_key,
               source_url, source_type, status, confidence, priority,
               match_features_json, reconciliation_notes, review_action
        FROM v_evidence_reconciliation_queue
        ORDER BY priority DESC, confidence DESC, display_name, record_type, record_id
        """,
    )


def pubmed_decision(row: dict, features: set[str]) -> tuple[str, str, str]:
    confidence = float(row.get("confidence") or 0)
    if row["claim_type"] == "pubmed_author_query_candidate":
        return (
            "discovery_only",
            "Do not accept author-query counts as identity evidence.",
            "Fetch article-level candidates, then require affiliation/coauthor/profile anchors.",
        )
    strong_review = bool(features & {"penn_affiliation", "orcid_present"}) and bool(
        features & {"prior_training_or_education_affiliation", "program_topic_match"}
    )
    topic_training_review = "prior_training_or_education_affiliation" in features and "program_topic_match" in features
    if row["status"] == "needs_review" and confidence >= 0.9 and strong_review:
        return (
            "review_ready_high_anchor",
            "Article has name match plus Penn/ORCID-style anchor and another non-name identity anchor.",
            "Manual reviewer may accept publication enrichment after checking author position, affiliation text, and profile/source context.",
        )
    if row["status"] == "needs_review" and confidence >= 0.85 and topic_training_review:
        return (
            "review_ready_training_topic_anchor",
            "Article has name match plus prior training/education affiliation and program-topic anchors.",
            "Manual reviewer should check whether the topic and affiliation refer to the trainee rather than a same-name author.",
        )
    if row["status"] == "needs_review" and confidence >= 0.8 and "prior_training_or_education_affiliation" in features:
        return (
            "needs_secondary_identity_anchor",
            "Article has a prior-training anchor but lacks Penn/ORCID/topic corroboration.",
            "Seek ORCID, institutional profile, coauthor cluster, or Penn/current-program affiliation before accepting.",
        )
    if row["status"] == "candidate" and features & REVIEW_READY_PUBMED_FEATURES:
        return (
            "candidate_with_partial_anchor",
            "Candidate has at least one non-name anchor but did not reach needs-review confidence.",
            "Keep as candidate and enrich with profile/ORCID/coauthor evidence.",
        )
    return (
        "low_signal_candidate",
        "Candidate lacks enough non-name identity evidence for review-ready treatment.",
        "Use only as discovery input unless a stronger source creates a second anchor.",
    )


def career_decision(row: dict, features: set[str], match_count: int, as_of_year: int) -> tuple[str, str, str, str]:
    event_year = row.get("event_year")
    within_window = "unknown"
    if event_year not in {None, ""}:
        within_window = "yes" if int(event_year) >= as_of_year - 10 else "no"
    if row["event_type"] == "attending_profile_training_history_candidate" and row["claim_type"] == "penn_training_history_candidate":
        if match_count:
            return (
                "attending_training_claim_linkable_name_match",
                within_window,
                "Official Penn profile contains Penn-training language and name matches a known trainee row.",
                "Review matched trainee identity, training dates, and program before linking attending trend event.",
            )
        if "structured_provider_training_field" in features:
            return (
                "attending_training_claim_review_ready",
                within_window,
                "Official Penn provider profile has structured Penn training field, but no known trainee identity link yet.",
                "Search historical roster/alumni pages or independent profile to link this attending to a trainee record.",
            )
        return (
            "attending_training_claim_needs_identity_link",
            within_window,
            "Official Penn page has Penn training language, but identity-to-trainee link is not established.",
            "Find historical Penn roster, alumni page, CV, or independent profile before using for trend lines.",
        )
    if row["event_type"] == "current_penn_attending_candidate":
        return (
            "current_attending_endpoint_candidate",
            within_window,
            "Current Penn attending/faculty endpoint candidate.",
            "Use as endpoint only after finding training-history or employment-start evidence.",
        )
    if row["event_type"] == "penn_alumni_outcome_candidate":
        return (
            "outcome_context_only",
            within_window,
            "Alumni/outcome source context is not linked to a resolved person yet.",
            "Resolve named person and source date before using in trend lines.",
        )
    return (
        "profile_context_candidate",
        within_window,
        "Official profile context candidate.",
        "Keep as context until identity, date, and claim type are independently reconciled.",
    )


def npi_decision(row: dict, features: set[str]) -> tuple[str, str, str]:
    confidence = float(row.get("confidence") or 0)
    has_exact_name = "exact_first_last_name" in features
    has_location = bool(features & {"state_location_match", "philadelphia_location"})
    has_taxonomy = bool(
        features
        & {
            "physician_specialty_taxonomy",
            "student_or_training_taxonomy",
            "program_taxonomy_topic_match",
        }
    )
    if row["status"] == "needs_review" and confidence >= 0.65 and has_exact_name and has_location and has_taxonomy:
        return (
            "npi_secondary_identity_anchor_review",
            "NPPES candidate has exact name plus location and taxonomy anchors.",
            "Use only as a secondary identity anchor; accept person enrichment only when official profile, roster, publication, or another independent source also agrees.",
        )
    if row["status"] in {"needs_review", "candidate"} and has_exact_name and (has_location or has_taxonomy):
        return (
            "npi_candidate_with_partial_anchor",
            "NPPES candidate has exact name plus one non-name anchor, but not enough corroboration for review-ready identity support.",
            "Seek official profile, publication affiliation, or stronger location/taxonomy corroboration before using.",
        )
    return (
        "npi_low_signal_candidate",
        "NPPES candidate lacks enough non-name identity support or is likely name-collision noise.",
        "Do not use without stronger independent anchors.",
    )


def profile_decision(row: dict, features: set[str]) -> tuple[str, str, str]:
    claim_type = row.get("claim_type") or ""
    confidence = float(row.get("confidence") or 0)
    if claim_type == "official_profile_url_candidate":
        if {"official_domain", "name_present", "profile_path"} <= features and confidence >= 0.7:
            return (
                "profile_context_candidate",
                "Discovered profile URL has official ownership, name match, and profile-path evidence, but is not roster-linked.",
                "Confirm same-person identity and current trainee/program context before accepting the URL as profile enrichment.",
            )
        return (
            "profile_context_candidate",
            "Discovered profile URL or context hit is useful only as candidate identity evidence.",
            "Seek official roster linkage, explicit current trainee role, or reviewer acceptance before promoting profile enrichment.",
        )
    if claim_type in {"education_history_candidate", "prior_training_history_candidate"}:
        if "roster_structured_field_crosscheck" in features and confidence >= 0.75:
            return (
                "review_ready_profile_background_field",
                "Official roster-linked profile field is backed by a structured roster/profile value.",
                "Reviewer may promote background enrichment after checking the source URL, field label, and duplicate-person context.",
            )
        return (
            "profile_background_candidate",
            "Official roster-linked profile contains education or prior-training background, but it remains candidate enrichment.",
            "Corroborate with another profile/CV/roster field or explicit reviewer acceptance before treating as accepted background.",
        )
    if claim_type in {"research_interest_candidate", "career_interest_candidate"}:
        return (
            "profile_interest_context_candidate",
            "Official profile exposes research or career interest context.",
            "Use as enrichment context only; do not treat as publication, outcome, or program-quality evidence without downstream support.",
        )
    if claim_type == "personal_profile_candidate":
        return (
            "profile_personal_context_display_review",
            "Official profile exposes personal context that may be useful for qualitative enrichment but has display-safety concerns.",
            "Apply display policy before use and avoid treating personal context as identity, quality, or outreach evidence.",
        )
    return (
        "profile_context_candidate",
        "Official profile candidate evidence is useful context but not acceptance-ready.",
        "Keep in reconciliation queue until a source-specific acceptance rule applies.",
    )


def make_decisions(conn: sqlite3.Connection, as_of_year: int) -> list[dict]:
    names = person_name_index(conn)
    decisions = []
    for row in load_queue(conn):
        features = set(parse_json(row.get("match_features_json"), []))
        name_matches = names.get(normalized_person_name(row.get("display_name")), [])
        if row["record_type"] == "evidence_claim":
            if row.get("source_type") in {"official_trainee_profile", "prior_training_background_discovery"}:
                decision, rationale, required = profile_decision(row, features)
            else:
                decision, rationale, required = pubmed_decision(row, features)
            trend_window = ""
        elif row["record_type"] == "npi_candidate":
            decision, rationale, required = npi_decision(row, features)
            trend_window = ""
        else:
            decision, trend_window, rationale, required = career_decision(row, features, len(name_matches), as_of_year)
        non_name_anchor_count = len(features & NON_NAME_FEATURES)
        decisions.append(
            {
                "record_type": row["record_type"],
                "record_id": row["record_id"],
                "person_key": row.get("person_key") or "",
                "display_name": row.get("display_name") or "",
                "role": row.get("role") or "",
                "claim_type": row.get("claim_type") or "",
                "event_type": row.get("event_type") or "",
                "status": row.get("status") or "",
                "confidence": row.get("confidence") or 0,
                "priority": row.get("priority") or 0,
                "decision": decision,
                "decision_rationale": rationale,
                "required_next_evidence": required,
                "non_name_anchor_count": non_name_anchor_count,
                "matched_current_person_count": len(name_matches),
                "matched_current_person_keys": "; ".join(match["person_key"] for match in name_matches[:5]),
                "ten_year_trend_window": trend_window,
                "source_key": row.get("source_key") or "",
                "source_url": row.get("source_url") or "",
                "match_features": "; ".join(sorted(features)),
            }
        )
    return decisions


def person_rollups(decisions: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in decisions:
        key = (row.get("person_key") or normalized_person_name(row.get("display_name")), row.get("display_name") or "")
        grouped[key].append(row)
    output = []
    for (person_key, display_name), items in grouped.items():
        decisions_count = Counter(row["decision"] for row in items)
        max_priority = max(int(row["priority"] or 0) for row in items)
        output.append(
            {
                "person_or_name_key": person_key,
                "display_name": display_name,
                "record_count": len(items),
                "max_priority": max_priority,
                "review_ready_records": sum(
                    count
                    for decision, count in decisions_count.items()
                    if decision.startswith("review_ready")
                    or decision.startswith("attending_training_claim_review_ready")
                    or decision == "npi_secondary_identity_anchor_review"
                ),
                "decision_counts_json": json.dumps(dict(sorted(decisions_count.items())), sort_keys=True),
                "top_decision": decisions_count.most_common(1)[0][0],
            }
        )
    return sorted(output, key=lambda row: (-row["max_priority"], row["display_name"]))


def write_csv(path: Path, output_rows: list[dict]) -> None:
    if not output_rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)


def write_sqlite(conn: sqlite3.Connection, decisions: list[dict], people: list[dict], decided_at: str) -> None:
    existing_decisions = {}
    existing_rollups = {}
    table_names = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    if "evidence_reconciliation_decisions" in table_names:
        existing_decisions = {
            row["decision_key"]: dict(row)
            for row in conn.execute(
                """
                SELECT decision_key, evidence_json, decided_at
                FROM evidence_reconciliation_decisions
                """
            )
        }
    if "person_reconciliation_decisions" in table_names:
        existing_rollups = {
            row["rollup_key"]: dict(row)
            for row in conn.execute(
                """
                SELECT rollup_key, record_count, max_priority, review_ready_records,
                       top_decision, decision_counts_json, decided_at
                FROM person_reconciliation_decisions
                """
            )
        }
    conn.execute("DROP TABLE IF EXISTS evidence_reconciliation_decisions")
    conn.execute("DROP TABLE IF EXISTS person_reconciliation_decisions")
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    decision_rows = []
    for row in decisions:
        db_row = dict(row)
        db_row["decision_key"] = key_for("evidence_decision", row["record_type"], row["record_id"])
        db_row["person_key"] = row.get("person_key") or None
        db_row["confidence"] = float(row.get("confidence") or 0)
        db_row["priority"] = int(float(row.get("priority") or 0))
        db_row["non_name_anchor_count"] = int(float(row.get("non_name_anchor_count") or 0))
        db_row["matched_current_person_count"] = int(float(row.get("matched_current_person_count") or 0))
        db_row["evidence_json"] = json.dumps(row, sort_keys=True)
        prior = existing_decisions.get(db_row["decision_key"])
        if prior and prior.get("evidence_json") == db_row["evidence_json"]:
            db_row["decided_at"] = prior.get("decided_at") or decided_at
        else:
            db_row["decided_at"] = decided_at
        decision_rows.append(db_row)
    conn.executemany(
        """
        INSERT INTO evidence_reconciliation_decisions
        (decision_key, record_type, record_id, person_key, display_name, role,
         claim_type, event_type, status, confidence, priority, decision,
         decision_rationale, required_next_evidence, non_name_anchor_count,
         matched_current_person_count, matched_current_person_keys,
         ten_year_trend_window, source_key, source_url, match_features,
         evidence_json, decided_at)
        VALUES
        (:decision_key, :record_type, :record_id, :person_key, :display_name, :role,
         :claim_type, :event_type, :status, :confidence, :priority, :decision,
         :decision_rationale, :required_next_evidence, :non_name_anchor_count,
         :matched_current_person_count, :matched_current_person_keys,
         :ten_year_trend_window, :source_key, :source_url, :match_features,
         :evidence_json, :decided_at)
        """,
        decision_rows,
    )
    rollup_rows = []
    known_person_keys = {decision.get("person_key") for decision in decisions if decision.get("person_key")}
    for row in people:
        db_row = dict(row)
        db_row["rollup_key"] = key_for("person_reconciliation", row["person_or_name_key"], row["display_name"])
        db_row["person_key"] = (
            row["person_or_name_key"]
            if row["person_or_name_key"] and row["person_or_name_key"] in known_person_keys
            else None
        )
        db_row["record_count"] = int(float(row.get("record_count") or 0))
        db_row["max_priority"] = int(float(row.get("max_priority") or 0))
        db_row["review_ready_records"] = int(float(row.get("review_ready_records") or 0))
        prior = existing_rollups.get(db_row["rollup_key"])
        if prior and all(
            str(prior.get(field, "")) == str(db_row.get(field, ""))
            for field in ["record_count", "max_priority", "review_ready_records", "top_decision", "decision_counts_json"]
        ):
            db_row["decided_at"] = prior.get("decided_at") or decided_at
        else:
            db_row["decided_at"] = decided_at
        rollup_rows.append(db_row)
    conn.executemany(
        """
        INSERT INTO person_reconciliation_decisions
        (rollup_key, person_or_name_key, person_key, display_name, record_count,
         max_priority, review_ready_records, top_decision, decision_counts_json,
         decided_at)
        VALUES
        (:rollup_key, :person_or_name_key, :person_key, :display_name, :record_count,
         :max_priority, :review_ready_records, :top_decision, :decision_counts_json,
         :decided_at)
        """,
        rollup_rows,
    )


def write_outputs(conn: sqlite3.Connection, decisions: list[dict], people: list[dict], as_of_year: int) -> None:
    decided_at = now_utc()
    summary = {
        "as_of_year": as_of_year,
        "decision_rows": len(decisions),
        "person_or_name_rows": len(people),
        "sqlite_tables": ["evidence_reconciliation_decisions", "person_reconciliation_decisions"],
        "decided_at": decided_at,
        "by_decision": dict(sorted(Counter(row["decision"] for row in decisions).items())),
        "by_record_type": dict(sorted(Counter(row["record_type"] for row in decisions).items())),
        "by_claim_type": dict(sorted(Counter(row["claim_type"] for row in decisions).items())),
        "by_ten_year_trend_window": dict(
            sorted(Counter(row["ten_year_trend_window"] for row in decisions if row["ten_year_trend_window"]).items())
        ),
        "review_ready_rows": sum(
            1
            for row in decisions
            if row["decision"].startswith("review_ready")
            or row["decision"].startswith("attending_training_claim_review_ready")
            or row["decision"] == "npi_secondary_identity_anchor_review"
        ),
        "decision_csv": "artifacts/data/evidence_reconciliation_decisions.csv",
        "person_rollup_csv": "artifacts/data/person_reconciliation_decisions.csv",
    }
    summary_path = ARTIFACTS / "evidence_reconciliation_decision_summary.json"
    if summary_path.exists():
        prior_summary = parse_json(summary_path.read_text(encoding="utf-8"), {})
        comparable_prior = dict(prior_summary)
        comparable_current = dict(summary)
        comparable_prior.pop("decided_at", None)
        comparable_current.pop("decided_at", None)
        if comparable_prior == comparable_current:
            summary["decided_at"] = prior_summary.get("decided_at") or decided_at
    write_sqlite(conn, decisions, people, decided_at)
    write_csv(ARTIFACTS / "evidence_reconciliation_decisions.csv", decisions)
    write_csv(ARTIFACTS / "person_reconciliation_decisions.csv", people)
    summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB)
    parser.add_argument("--as-of-year", type=int, default=date.today().year)
    args = parser.parse_args()
    conn = sqlite3.connect(args.db)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    decisions = make_decisions(conn, args.as_of_year)
    people = person_rollups(decisions)
    write_outputs(conn, decisions, people, args.as_of_year)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
