#!/usr/bin/env python3
"""Generate a source-aware recursive enrichment work queue.

The queue is intentionally non-mutating. It describes what to collect next, why
that source is useful, and the evidence gate required before a later acceptance
or reconciliation script may treat the finding as a fact.
"""

from __future__ import annotations

import csv
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_PATH = ARTIFACTS / "person_enrichment_queue.csv"
JSON_PATH = ARTIFACTS / "person_enrichment_queue.json"
SUMMARY_PATH = ARTIFACTS / "person_enrichment_queue_summary.json"

FIELDNAMES = [
    "task_key",
    "person_key",
    "display_name",
    "role",
    "current_status",
    "program_name",
    "trainee_category",
    "coverage_score",
    "coverage_band",
    "recommended_next_action",
    "state_machine_status",
    "policy_lane",
    "diff_readiness_status",
    "stale_by_refresh",
    "fresh_observation_required",
    "task_type",
    "source_family",
    "source_strategy",
    "priority",
    "priority_band",
    "query",
    "source_targets_json",
    "expected_claim_types_json",
    "evidence_requirement",
    "acceptance_rule",
    "recency_policy",
    "provenance_policy",
    "blocking_risk",
    "operator_action",
    "evidence_json",
    "generated_at",
]

SOURCE_TARGETS = {
    "official_profile": [
        "Penn Medicine profile",
        "Perelman School of Medicine profile",
        "CHOP profile when the program is pediatric/child-health affiliated",
        "official program roster outbound links",
    ],
    "official_roster": [
        "Penn Medicine/HUP current roster page",
        "Perelman department trainee page",
        "CHOP current roster page when relevant",
        "program page with explicit current-trainee year labels",
    ],
    "research_identity": [
        "PubMed author/article search",
        "ORCID public record",
        "OpenAlex author/work search",
        "Google Scholar only as discovery, never as sole acceptance evidence",
    ],
    "research": [
        "PubMed author/article search",
        "ORCID public record",
        "OpenAlex author/work search",
        "Google Scholar only as discovery, never as sole acceptance evidence",
    ],
    "prior_training": [
        "official prior institution profile",
        "residency/fellowship alumni roster",
        "departmental bio/CV page",
        "conference or society bio with education/training fields",
    ],
    "organization_identifier": [
        "ROR organization search",
        "official institution website",
        "AAMC/ERAS/ACGME identifiers only when program-level source-backed",
    ],
    "normalization": [
        "ROR organization search",
        "official institution website",
        "AAMC/ERAS/ACGME identifiers only when program-level source-backed",
    ],
    "contact": [
        "official Penn profile contact section",
        "department directory",
        "NPPES only for public physician/practice contact evidence",
    ],
    "review": [
        "existing reconciliation queue",
        "person evidence review packet",
        "accepted/rejected decision ledgers",
    ],
    "review_queue": [
        "existing reconciliation queue",
        "person evidence review packet",
        "accepted/rejected decision ledgers",
    ],
}

TASK_CONFIG = {
    "current_roster_state_reconciliation": {
        "source_family": "official_roster",
        "source_strategy": "refresh_current_roster_and_compare_expected_stage",
        "expected_claim_types": ["current_program_membership", "training_stage", "current_status"],
        "evidence_requirement": "Fresh official roster observation with same-person, same-program anchors and a current as-of date.",
        "acceptance_rule": "Use only official Penn/Penn Medicine/CHOP or directly linked institutional roster pages; classify changes through the transition plan before mutating state.",
        "recency_policy": "Must be refreshed at or after the projected transition/stale window before retaining, advancing, or removing a state.",
        "provenance_policy": "Store source URL, source_key, observation date, content hash, raw stage label, and parser/reviewer decision.",
        "operator_action": "refresh_roster_and_reconcile_state_machine",
    },
    "official_profile_search": {
        "source_family": "official_profile",
        "source_strategy": "find_or_confirm_official_person_profile",
        "expected_claim_types": ["profile_url", "headshot_url", "department", "bio", "contact"],
        "evidence_requirement": "Official profile or profile linked from an official roster, with name plus program/department or institution anchor.",
        "acceptance_rule": "Accept profile URL only from official Penn/Penn Medicine/CHOP/department domains or a directly linked official roster.",
        "recency_policy": "Profile can enrich identity and background but cannot prove current trainee status unless it states current role or is linked from a current roster.",
        "provenance_policy": "Capture canonical URL, title, source owner, content hash, and which fields were visible.",
        "operator_action": "collect_official_profile_evidence",
    },
    "evidence_reconciliation_review": {
        "source_family": "review_queue",
        "source_strategy": "resolve_high_priority_candidate_evidence",
        "expected_claim_types": ["research", "identity", "training_background", "career_event"],
        "evidence_requirement": "Existing candidate evidence plus enough independent non-name anchors to accept or reject.",
        "acceptance_rule": "Do not accept ambiguous evidence without the explicit assurance gates in the acceptance audit.",
        "recency_policy": "Review packets are current to the latest rebuild; refresh source pages only if source timestamps or hashes changed.",
        "provenance_policy": "Record reviewer decision, packet fingerprint, accepted/rejected status, and blocker rationale.",
        "operator_action": "review_reconciliation_packet",
    },
    "source_medical_school_background": {
        "source_family": "prior_training",
        "source_strategy": "find_public_medical_school_or_degree_background",
        "expected_claim_types": ["medical_school", "degree", "education_background"],
        "evidence_requirement": "Public bio/CV/profile with name and at least one current or prior institution/program anchor.",
        "acceptance_rule": "Treat education background as candidate evidence unless official profile/CV or two independent high-signal sources corroborate.",
        "recency_policy": "Background fields do not expire quickly, but source URL/hash should be retained for future reconciliation.",
        "provenance_policy": "Store exact source URL, source owner, observed field text, and match anchors.",
        "operator_action": "collect_prior_training_background",
    },
    "source_residency_background": {
        "source_family": "prior_training",
        "source_strategy": "find_public_residency_or_prior_gme_background",
        "expected_claim_types": ["residency_program", "prior_gme_program", "education_background"],
        "evidence_requirement": "Public bio/CV/profile or prior program roster with name plus specialty/program/institution anchor.",
        "acceptance_rule": "For fellows, residency background needs source-backed program or institution anchor; do not infer from specialty alone.",
        "recency_policy": "Prior GME history is stable once source-backed, but URLs should be rechecked if used for identity linkage.",
        "provenance_policy": "Store exact source URL, source owner, observed field text, and match anchors.",
        "operator_action": "collect_prior_gme_background",
    },
    "organization_alias_review": {
        "source_family": "normalization",
        "source_strategy": "resolve_training_organization_alias_or_identifier",
        "expected_claim_types": ["organization_alias", "organization_identifier"],
        "evidence_requirement": "Alias mapping or identifier candidate with canonical organization evidence.",
        "acceptance_rule": "Do not collapse organizations unless alias/identifier evidence distinguishes campus, hospital, program, and school variants.",
        "recency_policy": "Organization identifiers are durable; recheck only when source candidate or alias text changes.",
        "provenance_policy": "Record resolver status, candidate identifier URL, match features, and ambiguity reason.",
        "operator_action": "review_organization_alias_candidate",
    },
    "research_identity_search": {
        "source_family": "research",
        "source_strategy": "collect_article_level_research_candidates",
        "expected_claim_types": ["pubmed_article_candidate", "orcid_profile_candidate", "openalex_author_candidate"],
        "evidence_requirement": "Publication/author candidate with at least two non-name anchors; NPI or official profile anchor required for machine acceptance.",
        "acceptance_rule": "Attach publications only through the enrichment acceptance audit; name-only author matches remain discovery-only.",
        "recency_policy": "Search current scholarly indexes each enrichment pass; publication lists can change after the previous run.",
        "provenance_policy": "Capture query, source API/page, author identifiers, PMID/DOI/OpenAlex/ORCID IDs, and match features.",
        "operator_action": "collect_research_identity_candidates",
    },
    "public_contact_verification": {
        "source_family": "contact",
        "source_strategy": "collect_public_contact_candidates",
        "expected_claim_types": ["public_email", "public_phone", "public_profile_contact"],
        "evidence_requirement": "Publicly displayed contact field from an official profile/directory or NPPES public registry candidate.",
        "acceptance_rule": "Keep contacts with verification and display-safety status; do not infer or generate email/phone values.",
        "recency_policy": "Contact fields are stale-prone and require source recheck before display or use.",
        "provenance_policy": "Store contact type, source URL, verification status, display-safety status, observed_at, and source owner.",
        "operator_action": "collect_public_contact_evidence",
    },
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def quote(value: str) -> str:
    value = (value or "").strip()
    return f'"{value}"' if value else ""


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def task_key(person_key: str, task_type: str, program_name: str, source_strategy: str) -> str:
    basis = dumps([person_key, task_type, program_name, source_strategy])
    return f"person_enrichment_task_{sha256_text(basis)[:20]}"


def priority_band(priority: int) -> str:
    if priority >= 95:
        return "critical"
    if priority >= 85:
        return "high"
    if priority >= 70:
        return "medium"
    return "low"


def read_rows(conn: sqlite3.Connection, query: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def coverage_rows(conn: sqlite3.Connection) -> list[dict]:
    return read_rows(
        conn,
        """
        SELECT p.person_key, p.display_name, p.role, p.current_status,
               COALESCE(c.programs, '') AS programs,
               COALESCE(c.program_count, 0) AS program_count,
               COALESCE(c.has_profile_url, CASE WHEN p.profile_url IS NULL OR p.profile_url = '' THEN 0 ELSE 1 END) AS has_profile_url,
               COALESCE(c.has_headshot_url, CASE WHEN p.headshot_url IS NULL OR p.headshot_url = '' THEN 0 ELSE 1 END) AS has_headshot_url,
               COALESCE(c.contact_count, 0) AS contact_count,
               COALESCE(c.medical_school_count, 0) AS medical_school_count,
               COALESCE(c.residency_program_count, 0) AS residency_program_count,
               COALESCE(c.undergraduate_school_count, 0) AS undergraduate_school_count,
               COALESCE(c.graduate_school_count, 0) AS graduate_school_count,
               COALESCE(c.cleaned_training_org_count, 0) AS cleaned_training_org_count,
               COALESCE(c.pubmed_article_candidate_count, 0) AS pubmed_article_candidate_count,
               COALESCE(c.pubmed_article_needs_review_count, 0) AS pubmed_article_needs_review_count,
               COALESCE(c.reconciliation_queue_count, 0) AS reconciliation_queue_count,
               COALESCE(c.max_reconciliation_priority, 0) AS max_reconciliation_priority,
               COALESCE(c.worst_state_machine_status, '') AS worst_state_machine_status,
               COALESCE(c.coverage_score, 0) AS coverage_score,
               COALESCE(c.coverage_band, 'thin_enrichment_surface') AS coverage_band,
               COALESCE(c.recommended_next_action, 'monitor_refresh_and_diff') AS recommended_next_action
        FROM people p
        LEFT JOIN person_enrichment_coverage c ON c.person_key = p.person_key
        WHERE p.role IN ('resident', 'fellow', 'medical_student')
        ORDER BY p.role, p.display_name
        """,
    )


def transition_map(conn: sqlite3.Connection) -> dict[str, dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in read_rows(
        conn,
        """
        SELECT person_key, program_name, trainee_category, policy_lane,
               diff_readiness_status, state_machine_status, stale_by_refresh,
               fresh_observation_required, recommended_operator_action,
               projected_refresh_date, evidence_requirement
        FROM training_state_transition_plan
        """,
    ):
        grouped[row["person_key"]].append(row)

    priority = {
        "manual_review_required": 100,
        "source_refresh_required": 90,
        "deterministic_expected_advancement": 85,
        "deterministic_expected_completion": 82,
        "pending_annual_advancement": 50,
        "pending_terminal_completion": 45,
        "carry_forward_no_change": 20,
    }
    result = {}
    for person_key, rows_for_person in grouped.items():
        chosen = max(rows_for_person, key=lambda row: priority.get(row.get("policy_lane") or "", 0))
        result[person_key] = {
            **chosen,
            "state_count": len(rows_for_person),
            "policy_lane_counts": dict(Counter(row.get("policy_lane") or "" for row in rows_for_person)),
            "diff_readiness_counts": dict(Counter(row.get("diff_readiness_status") or "" for row in rows_for_person)),
        }
    return result


def split_programs(value: str) -> list[str]:
    programs = [part.strip() for part in (value or "").split("; ") if part.strip()]
    return programs or [""]


def query_for(task_type: str, person: dict, transition: dict, program_name: str) -> str:
    name = person["display_name"]
    role = person.get("role") or ""
    if task_type == "current_roster_state_reconciliation":
        return " ".join(
            token
            for token in [
                quote(name),
                quote("Penn Medicine"),
                quote(program_name),
                "current roster trainee PGY fellow resident student",
            ]
            if token
        )
    if task_type == "official_profile_search":
        return " ".join(
            token
            for token in [quote(name), "Penn OR PennMedicine OR Perelman OR CHOP", quote(program_name), "profile bio"]
            if token
        )
    if task_type == "research_identity_search":
        return " ".join(
            token
            for token in [
                quote(name),
                "PubMed OR ORCID OR OpenAlex",
                quote("University of Pennsylvania"),
                quote(program_name),
            ]
            if token
        )
    if task_type == "source_medical_school_background":
        return " ".join(token for token in [quote(name), quote(program_name), "medical school MD education bio CV"] if token)
    if task_type == "source_residency_background":
        return " ".join(token for token in [quote(name), quote(program_name), "residency prior training bio CV"] if token)
    if task_type == "organization_alias_review":
        return " ".join(token for token in [quote(name), "training institution alias ROR", role, quote(program_name)] if token)
    if task_type == "public_contact_verification":
        return " ".join(token for token in [quote(name), quote("Penn Medicine"), quote(program_name), "email phone contact profile"] if token)
    return " ".join(token for token in [quote(name), quote(program_name), "evidence review"] if token)


def add_task(tasks: list[dict], person: dict, transition: dict, task_type: str, base_priority: int, risk: str) -> None:
    config = TASK_CONFIG[task_type]
    program_name = transition.get("program_name") or split_programs(person.get("programs") or "")[0]
    coverage_score = int(person.get("coverage_score") or 0)
    policy_lane = transition.get("policy_lane") or ""
    state_status = transition.get("state_machine_status") or person.get("worst_state_machine_status") or ""
    priority = base_priority
    if task_type == "current_roster_state_reconciliation":
        if policy_lane in {"manual_review_required", "source_refresh_required"}:
            priority += 8
        if policy_lane.startswith("deterministic_expected_"):
            priority += 5
        if int(transition.get("stale_by_refresh") or 0):
            priority += 6
        if int(transition.get("fresh_observation_required") or 0):
            priority += 4
    elif task_type == "evidence_reconciliation_review":
        if int(person.get("max_reconciliation_priority") or 0) >= 95:
            priority += 5
        elif int(person.get("max_reconciliation_priority") or 0) >= 85:
            priority += 2
    elif policy_lane in {"manual_review_required", "source_refresh_required"}:
        priority += 2
    if coverage_score < 35:
        priority += 4
    if person.get("role") == "fellow" and task_type in {"research_identity_search", "source_residency_background"}:
        priority += 3
    priority = min(priority, 100)
    evidence = {
        "coverage": {
            "coverage_score": coverage_score,
            "coverage_band": person.get("coverage_band") or "",
            "recommended_next_action": person.get("recommended_next_action") or "",
            "has_profile_url": int(person.get("has_profile_url") or 0),
            "contact_count": int(person.get("contact_count") or 0),
            "medical_school_count": int(person.get("medical_school_count") or 0),
            "residency_program_count": int(person.get("residency_program_count") or 0),
            "article_candidate_count": int(person.get("pubmed_article_candidate_count") or 0),
            "article_needs_review_count": int(person.get("pubmed_article_needs_review_count") or 0),
            "reconciliation_queue_count": int(person.get("reconciliation_queue_count") or 0),
        },
        "transition": {
            "policy_lane": policy_lane,
            "diff_readiness_status": transition.get("diff_readiness_status") or "",
            "state_machine_status": state_status,
            "projected_refresh_date": transition.get("projected_refresh_date") or "",
            "state_count": transition.get("state_count") or 0,
            "policy_lane_counts": transition.get("policy_lane_counts") or {},
        },
    }
    tasks.append(
        {
            "task_key": task_key(person["person_key"], task_type, program_name, config["source_strategy"]),
            "person_key": person["person_key"],
            "display_name": person["display_name"],
            "role": person.get("role") or "",
            "current_status": person.get("current_status") or "",
            "program_name": program_name,
            "trainee_category": transition.get("trainee_category") or "",
            "coverage_score": coverage_score,
            "coverage_band": person.get("coverage_band") or "",
            "recommended_next_action": person.get("recommended_next_action") or "",
            "state_machine_status": state_status,
            "policy_lane": policy_lane,
            "diff_readiness_status": transition.get("diff_readiness_status") or "",
            "stale_by_refresh": int(transition.get("stale_by_refresh") or 0),
            "fresh_observation_required": int(transition.get("fresh_observation_required") or 0),
            "task_type": task_type,
            "source_family": config["source_family"],
            "source_strategy": config["source_strategy"],
            "priority": priority,
            "priority_band": priority_band(priority),
            "query": query_for(task_type, person, transition, program_name),
            "source_targets_json": dumps(SOURCE_TARGETS[config["source_family"]]),
            "expected_claim_types_json": dumps(config["expected_claim_types"]),
            "evidence_requirement": config["evidence_requirement"],
            "acceptance_rule": config["acceptance_rule"],
            "recency_policy": config["recency_policy"],
            "provenance_policy": config["provenance_policy"],
            "blocking_risk": risk,
            "operator_action": config["operator_action"],
            "evidence_json": dumps(evidence),
            "generated_at": "",
        }
    )


def make_queue(conn: sqlite3.Connection) -> list[dict]:
    people = coverage_rows(conn)
    transitions = transition_map(conn)
    tasks: list[dict] = []
    for person in people:
        transition = transitions.get(person["person_key"], {})
        next_action = person.get("recommended_next_action") or ""
        role = person.get("role") or ""

        if transition.get("policy_lane") in {
            "manual_review_required",
            "source_refresh_required",
            "deterministic_expected_advancement",
            "deterministic_expected_completion",
        }:
            add_task(
                tasks,
                person,
                transition,
                "current_roster_state_reconciliation",
                88,
                "Training state may become stale or misclassified without a fresh current-roster observation.",
            )

        if not int(person.get("has_profile_url") or 0):
            add_task(
                tasks,
                person,
                transition,
                "official_profile_search",
                82 if role == "medical_student" else 86,
                "Profile absence weakens identity, contact, background, and research disambiguation.",
            )

        if int(person.get("max_reconciliation_priority") or 0) >= 85 or next_action == "reconcile_high_priority_evidence":
            add_task(
                tasks,
                person,
                transition,
                "evidence_reconciliation_review",
                90,
                "High-priority candidate evidence is present but not yet accepted or rejected.",
            )

        if role in {"resident", "fellow"} and not int(person.get("medical_school_count") or 0):
            add_task(
                tasks,
                person,
                transition,
                "source_medical_school_background",
                78,
                "Prior education background is missing, limiting identity disambiguation and program-quality analysis.",
            )

        if role == "fellow" and not int(person.get("residency_program_count") or 0):
            add_task(
                tasks,
                person,
                transition,
                "source_residency_background",
                80,
                "Fellowship interpretation is weaker without source-backed prior residency training.",
            )

        if int(person.get("cleaned_training_org_count") or 0):
            add_task(
                tasks,
                person,
                transition,
                "organization_alias_review",
                72,
                "Training organization labels exist but are not fully normalized to durable identifiers.",
            )

        if role in {"resident", "fellow", "medical_student"} and not (
            int(person.get("pubmed_article_candidate_count") or 0)
            or int(person.get("pubmed_article_needs_review_count") or 0)
        ):
            add_task(
                tasks,
                person,
                transition,
                "research_identity_search",
                68 if role == "medical_student" else 72,
                "No article-level research candidate exists; research signal is absent rather than negative.",
            )

        if not int(person.get("contact_count") or 0):
            add_task(
                tasks,
                person,
                transition,
                "public_contact_verification",
                46,
                "No public contact candidate is stored; future display must distinguish absent from unsearched.",
            )

    existing = existing_tasks()
    generated_at = now_utc()
    deduped = {task["task_key"]: task for task in tasks}
    output = sorted(
        deduped.values(),
        key=lambda row: (-int(row["priority"]), row["role"], row["display_name"], row["task_type"]),
    )
    for task in output:
        prior = existing.get(task["task_key"])
        if prior and all(str(prior.get(field, "")) == str(task.get(field, "")) for field in FIELDNAMES if field != "generated_at"):
            task["generated_at"] = prior.get("generated_at") or generated_at
        else:
            task["generated_at"] = generated_at
    return output


def existing_tasks() -> dict[str, dict]:
    if not CSV_PATH.exists():
        return {}
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return {row.get("task_key", ""): row for row in csv.DictReader(handle) if row.get("task_key")}


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db_table(conn: sqlite3.Connection, rows: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM person_enrichment_work_queue")
    if not rows:
        return
    placeholders = ", ".join(f":{field}" for field in FIELDNAMES)
    column_sql = ", ".join(FIELDNAMES)
    conn.executemany(
        f"INSERT INTO person_enrichment_work_queue ({column_sql}) VALUES ({placeholders})",
        [{field: row.get(field, "") for field in FIELDNAMES} for row in rows],
    )


def summary(rows: list[dict]) -> dict:
    return {
        "queue_rows": len(rows),
        "person_count": len({row["person_key"] for row in rows}),
        "by_role": dict(sorted(Counter(row["role"] for row in rows).items())),
        "by_task_type": dict(sorted(Counter(row["task_type"] for row in rows).items())),
        "by_source_family": dict(sorted(Counter(row["source_family"] for row in rows).items())),
        "by_priority_band": dict(sorted(Counter(row["priority_band"] for row in rows).items())),
        "by_policy_lane": dict(sorted(Counter(row["policy_lane"] or "none" for row in rows).items())),
        "fresh_observation_required_tasks": sum(int(row["fresh_observation_required"] or 0) for row in rows),
        "stale_by_refresh_tasks": sum(int(row["stale_by_refresh"] or 0) for row in rows),
        "top_critical_tasks": [
            {
                "display_name": row["display_name"],
                "role": row["role"],
                "program_name": row["program_name"],
                "task_type": row["task_type"],
                "priority": row["priority"],
                "blocking_risk": row["blocking_risk"],
            }
            for row in rows[:10]
        ],
        "queue_csv": "artifacts/data/person_enrichment_queue.csv",
        "queue_json": "artifacts/data/person_enrichment_queue.json",
    }


def main() -> None:
    conn = sqlite3.connect(DB)
    with conn:
        queue = make_queue(conn)
        write_db_table(conn, queue)
    conn.close()
    write_csv(CSV_PATH, queue)
    JSON_PATH.write_text(json.dumps(queue, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary(queue), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary(queue), sort_keys=True))


if __name__ == "__main__":
    main()
