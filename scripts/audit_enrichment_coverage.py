#!/usr/bin/env python3
"""Audit enrichment/provenance coverage for current Penn-affiliated people."""

from __future__ import annotations

import csv
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
STATE_AUDIT = ARTIFACTS / "person_training_state_machine_audit.csv"


def rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def read_state_audit() -> dict[str, dict]:
    if not STATE_AUDIT.exists():
        return {}
    with STATE_AUDIT.open(newline="", encoding="utf-8") as f:
        return {row["person_key"]: row for row in csv.DictReader(f)}


def list_join(values: set[str] | list[str]) -> str:
    return "; ".join(sorted(value for value in values if value))


def load_people(conn: sqlite3.Connection) -> list[dict]:
    return rows(
        conn,
        """
        SELECT person_key, display_name, role, current_status, institution,
               profile_url, headshot_url, quality_tier
        FROM people
        ORDER BY role, display_name
        """,
    )


def program_map(conn: sqlite3.Connection) -> dict[str, set[str]]:
    out: dict[str, set[str]] = defaultdict(set)
    for row in rows(
        conn,
        """
        SELECT m.person_key, pr.program_name
        FROM person_program_memberships m
        JOIN programs pr ON pr.program_key = m.program_key
        """,
    ):
        out[row["person_key"]].add(row["program_name"])
    return out


def training_map(conn: sqlite3.Connection) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"events": Counter(), "resolver": Counter(), "values": defaultdict(set)})
    for row in rows(
        conn,
        """
        SELECT e.person_key, e.event_type, e.raw_value, e.resolver_status
        FROM person_training_events e
        """,
    ):
        target = out[row["person_key"]]
        target["events"][row["event_type"]] += 1
        target["resolver"][row["resolver_status"]] += 1
        target["values"][row["event_type"]].add(row["raw_value"])
    return out


def contact_map(conn: sqlite3.Connection) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"count": 0, "types": Counter(), "statuses": Counter()})
    for row in rows(
        conn,
        """
        SELECT person_key, contact_type, verification_status, status
        FROM person_contacts
        WHERE person_key IS NOT NULL
        """,
    ):
        target = out[row["person_key"]]
        target["count"] += 1
        target["types"][row["contact_type"]] += 1
        target["statuses"][row["status"]] += 1
        target["statuses"][row["verification_status"]] += 1
    return out


def evidence_map(conn: sqlite3.Connection) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"claims": Counter(), "statuses": Counter(), "features": Counter()})
    for row in rows(
        conn,
        """
        SELECT person_key, claim_type, status, match_features_json
        FROM evidence_claims
        WHERE person_key IS NOT NULL
        """,
    ):
        target = out[row["person_key"]]
        target["claims"][row["claim_type"]] += 1
        target["statuses"][f"{row['claim_type']}:{row['status']}"] += 1
        try:
            features = json.loads(row["match_features_json"] or "[]")
        except json.JSONDecodeError:
            features = []
        for feature in features:
            target["features"][feature] += 1
    return out


def career_map(conn: sqlite3.Connection) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"events": Counter(), "statuses": Counter()})
    for row in rows(
        conn,
        """
        SELECT person_key, event_type, status
        FROM career_events
        WHERE person_key IS NOT NULL
        """,
    ):
        target = out[row["person_key"]]
        target["events"][row["event_type"]] += 1
        target["statuses"][f"{row['event_type']}:{row['status']}"] += 1
    return out


def npi_map(conn: sqlite3.Connection) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"count": 0, "statuses": Counter(), "taxonomies": Counter()})
    for row in rows(
        conn,
        """
        SELECT person_key, candidate_status, primary_taxonomy
        FROM npi_candidate_claims
        """,
    ):
        target = out[row["person_key"]]
        target["count"] += 1
        target["statuses"][row["candidate_status"]] += 1
        target["taxonomies"][row["primary_taxonomy"] or "none"] += 1
    return out


def queue_map(conn: sqlite3.Connection) -> dict[str, dict]:
    out: dict[str, dict] = defaultdict(lambda: {"count": 0, "max_priority": 0, "types": Counter()})
    for row in rows(
        conn,
        """
        SELECT person_key, record_type, claim_type, status, priority
        FROM v_evidence_reconciliation_queue
        WHERE person_key IS NOT NULL
        """,
    ):
        target = out[row["person_key"]]
        target["count"] += 1
        target["max_priority"] = max(target["max_priority"], int(row["priority"] or 0))
        target["types"][f"{row['record_type']}:{row['claim_type']}:{row['status']}"] += 1
    return out


def count_int(mapping: dict, key: str) -> int:
    value = mapping.get(key, 0)
    return int(value or 0)


def coverage_score(person: dict, programs: set[str], training: dict, contacts: dict, evidence: dict, state: dict, npi: dict) -> int:
    score = 0
    role = person.get("role") or ""
    training_events = training.get("events", Counter())
    resolver = training.get("resolver", Counter())
    claims = evidence.get("claims", Counter())
    statuses = evidence.get("statuses", Counter())
    if programs:
        score += 10
    if state:
        score += 10
    if person.get("profile_url"):
        score += 10
    if person.get("headshot_url"):
        score += 5
    if role in {"resident", "fellow"}:
        if training_events.get("medical_school"):
            score += 15
        if role == "fellow" and training_events.get("residency_program"):
            score += 12
        if role == "resident" and training_events.get("undergraduate_school"):
            score += 5
        if training_events.get("graduate_school"):
            score += 3
    elif role == "medical_student":
        if state:
            score += 15
        if person.get("profile_url"):
            score += 5
    if contacts.get("count"):
        score += 8
    if statuses.get("pubmed_article_candidate:needs_review") or statuses.get("pubmed_article_candidate:candidate"):
        score += 15
    elif claims.get("pubmed_author_query_candidate"):
        score += 5
    if npi.get("statuses", Counter()).get("needs_review"):
        score += 4
    elif npi.get("count"):
        score += 2
    if resolver and not resolver.get("cleaned_label"):
        score += 7
    elif resolver.get("cleaned_label"):
        score += 2
    return min(score, 100)


def quality_band(score: int) -> str:
    if score >= 75:
        return "broad_enrichment_surface"
    if score >= 50:
        return "moderate_enrichment_surface"
    return "thin_enrichment_surface"


def next_action(person: dict, programs: set[str], training: dict, contacts: dict, evidence: dict, career: dict, queue: dict, state: dict) -> str:
    role = person.get("role") or ""
    training_events = training.get("events", Counter())
    resolver = training.get("resolver", Counter())
    statuses = evidence.get("statuses", Counter())
    state_status = state.get("worst_state_machine_status", "")
    if not programs:
        return "repair_program_membership"
    if state_status in {"stale_now", "ready_for_expected_advancement", "review_required"}:
        return "review_training_state_machine"
    if not person.get("profile_url"):
        return "official_profile_search"
    if role in {"resident", "fellow"} and not training_events.get("medical_school"):
        return "source_medical_school_background"
    if role == "fellow" and not training_events.get("residency_program"):
        return "source_residency_background"
    if resolver.get("cleaned_label"):
        return "organization_alias_review"
    if queue.get("max_priority", 0) >= 90:
        return "reconcile_high_priority_evidence"
    if statuses.get("pubmed_article_candidate:needs_review"):
        return "reconcile_pubmed_article_candidates"
    if role in {"resident", "fellow"} and not statuses.get("pubmed_article_candidate:candidate"):
        return "collect_article_level_research_candidates"
    if career.get("statuses", Counter()).get("attending_profile_training_history_candidate:needs_review"):
        return "reconcile_attending_training_history"
    if not contacts.get("count"):
        return "public_contact_search"
    return "monitor_refresh_and_diff"


def person_rows(conn: sqlite3.Connection) -> list[dict]:
    people = load_people(conn)
    programs = program_map(conn)
    trainings = training_map(conn)
    contacts = contact_map(conn)
    evidences = evidence_map(conn)
    careers = career_map(conn)
    npis = npi_map(conn)
    queues = queue_map(conn)
    states = read_state_audit()
    out = []
    for person in people:
        person_key = person["person_key"]
        person_programs = programs.get(person_key, set())
        training = trainings.get(person_key, {})
        contact = contacts.get(person_key, {})
        evidence = evidences.get(person_key, {})
        career = careers.get(person_key, {})
        npi = npis.get(person_key, {})
        queue = queues.get(person_key, {})
        state = states.get(person_key, {})
        training_events = training.get("events", Counter())
        resolver = training.get("resolver", Counter())
        claim_statuses = evidence.get("statuses", Counter())
        npi_statuses = npi.get("statuses", Counter())
        score = coverage_score(person, person_programs, training, contact, evidence, state, npi)
        out.append(
            {
                "person_key": person_key,
                "display_name": person["display_name"],
                "role": person.get("role") or "",
                "current_status": person.get("current_status") or "",
                "program_count": len(person_programs),
                "programs": list_join(person_programs),
                "has_profile_url": int(bool(person.get("profile_url"))),
                "has_headshot_url": int(bool(person.get("headshot_url"))),
                "contact_count": contact.get("count", 0),
                "medical_school_count": count_int(training_events, "medical_school"),
                "residency_program_count": count_int(training_events, "residency_program"),
                "undergraduate_school_count": count_int(training_events, "undergraduate_school"),
                "graduate_school_count": count_int(training_events, "graduate_school"),
                "seeded_training_org_count": count_int(resolver, "seeded_alias"),
                "cleaned_training_org_count": count_int(resolver, "cleaned_label"),
                "pubmed_author_query_count": count_int(claim_statuses, "pubmed_author_query_candidate:candidate"),
                "pubmed_article_candidate_count": count_int(claim_statuses, "pubmed_article_candidate:candidate"),
                "pubmed_article_needs_review_count": count_int(claim_statuses, "pubmed_article_candidate:needs_review"),
                "career_event_candidate_count": sum(career.get("events", Counter()).values()),
                "npi_candidate_count": npi.get("count", 0),
                "npi_needs_review_count": count_int(npi_statuses, "needs_review"),
                "npi_candidate_status_count": count_int(npi_statuses, "candidate"),
                "npi_low_signal_count": count_int(npi_statuses, "low_signal_npi_candidate"),
                "reconciliation_queue_count": queue.get("count", 0),
                "max_reconciliation_priority": queue.get("max_priority", 0),
                "worst_state_machine_status": state.get("worst_state_machine_status", ""),
                "coverage_score": score,
                "coverage_band": quality_band(score),
                "recommended_next_action": next_action(person, person_programs, training, contact, evidence, career, queue, state),
            }
        )
    return sorted(out, key=lambda row: (row["coverage_score"], row["role"], row["display_name"]))


def program_rows(persons: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in persons:
        programs = [program for program in row["programs"].split("; ") if program] or ["Unassigned Program"]
        for program in programs:
            grouped[(program, row["role"])].append(row)
    out = []
    for (program, role), rows_for_program in grouped.items():
        total = len(rows_for_program)
        actions = Counter(row["recommended_next_action"] for row in rows_for_program)
        bands = Counter(row["coverage_band"] for row in rows_for_program)
        out.append(
            {
                "program_name": program,
                "role": role,
                "person_count": total,
                "avg_coverage_score": round(sum(int(row["coverage_score"]) for row in rows_for_program) / total, 2),
                "broad_enrichment_surface_count": bands.get("broad_enrichment_surface", 0),
                "moderate_enrichment_surface_count": bands.get("moderate_enrichment_surface", 0),
                "thin_enrichment_surface_count": bands.get("thin_enrichment_surface", 0),
                "profile_coverage_rate": round(sum(row["has_profile_url"] for row in rows_for_program) / total, 3),
                "contact_coverage_rate": round(sum(1 for row in rows_for_program if row["contact_count"]) / total, 3),
                "medical_school_coverage_rate": round(
                    sum(1 for row in rows_for_program if row["medical_school_count"]) / total, 3
                ),
                "residency_coverage_rate": round(
                    sum(1 for row in rows_for_program if row["residency_program_count"]) / total, 3
                ),
                "article_candidate_coverage_rate": round(
                    sum(
                        1
                        for row in rows_for_program
                        if row["pubmed_article_candidate_count"] or row["pubmed_article_needs_review_count"]
                    )
                    / total,
                    3,
                ),
                "npi_candidate_coverage_rate": round(sum(1 for row in rows_for_program if row["npi_candidate_count"]) / total, 3),
                "npi_needs_review_coverage_rate": round(
                    sum(1 for row in rows_for_program if row["npi_needs_review_count"]) / total, 3
                ),
                "cleaned_org_review_count": sum(row["cleaned_training_org_count"] for row in rows_for_program),
                "reconciliation_queue_count": sum(row["reconciliation_queue_count"] for row in rows_for_program),
                "top_recommended_next_action": actions.most_common(1)[0][0],
            }
        )
    return sorted(out, key=lambda row: (row["avg_coverage_score"], row["role"], row["program_name"]))


def write_csv(path: Path, output_rows: list[dict]) -> None:
    if not output_rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(output_rows)


def summary(persons: list[dict], programs: list[dict]) -> dict:
    return {
        "person_rows": len(persons),
        "program_rows": len(programs),
        "by_role": dict(sorted(Counter(row["role"] for row in persons).items())),
        "by_coverage_band": dict(sorted(Counter(row["coverage_band"] for row in persons).items())),
        "by_recommended_next_action": dict(sorted(Counter(row["recommended_next_action"] for row in persons).items())),
        "avg_coverage_score": round(sum(row["coverage_score"] for row in persons) / len(persons), 2) if persons else 0,
        "profile_coverage_rate": round(sum(row["has_profile_url"] for row in persons) / len(persons), 3) if persons else 0,
        "contact_coverage_rate": round(sum(1 for row in persons if row["contact_count"]) / len(persons), 3)
        if persons
        else 0,
        "article_candidate_coverage_rate": round(
            sum(1 for row in persons if row["pubmed_article_candidate_count"] or row["pubmed_article_needs_review_count"])
            / len(persons),
            3,
        )
        if persons
        else 0,
        "npi_candidate_coverage_rate": round(sum(1 for row in persons if row["npi_candidate_count"]) / len(persons), 3)
        if persons
        else 0,
        "npi_needs_review_coverage_rate": round(
            sum(1 for row in persons if row["npi_needs_review_count"]) / len(persons),
            3,
        )
        if persons
        else 0,
        "cleaned_org_review_people": sum(1 for row in persons if row["cleaned_training_org_count"]),
        "people_with_reconciliation_queue": sum(1 for row in persons if row["reconciliation_queue_count"]),
        "person_coverage_csv": "artifacts/data/person_enrichment_coverage.csv",
        "program_coverage_csv": "artifacts/data/program_enrichment_coverage.csv",
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    persons = person_rows(conn)
    conn.close()
    programs = program_rows(persons)
    payload = summary(persons, programs)
    write_csv(ARTIFACTS / "person_enrichment_coverage.csv", persons)
    write_csv(ARTIFACTS / "program_enrichment_coverage.csv", programs)
    (ARTIFACTS / "enrichment_coverage_summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
