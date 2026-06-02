#!/usr/bin/env python3
"""Render source-quality learnings from the warehouse."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
REPORTS = ROOT / "artifacts" / "research"
DB = ARTIFACTS / "redmank.sqlite"


def rows(conn: sqlite3.Connection, query: str):
    conn.row_factory = sqlite3.Row
    return [dict(row) for row in conn.execute(query)]


def md_table(items: list[dict], columns: list[str]) -> list[str]:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for item in items:
        lines.append("| " + " | ".join(str(item.get(col, "")).replace("|", "\\|") for col in columns) + " |")
    return lines


def main() -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    source_counts = rows(
        conn,
        """
        SELECT source_type, classification, COUNT(*) AS count
        FROM sources
        GROUP BY source_type, classification
        ORDER BY source_type, classification
        """,
    )
    evidence_counts = rows(
        conn,
        """
        SELECT source_key, status, claim_type, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        GROUP BY source_key, status, claim_type
        ORDER BY source_key, status, claim_type
        """,
    )
    utility_observations = rows(
        conn,
        """
        SELECT utility_key, sample_size, candidate_claims, accepted_claims,
               rejected_claims, ambiguous_claims, metrics_json
        FROM source_quality_observations
        ORDER BY utility_key
        """,
    )
    openalex_features = rows(
        conn,
        """
        SELECT match_features_json, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_key = 'openalex_author_search'
        GROUP BY match_features_json
        ORDER BY count DESC
        LIMIT 20
        """,
    )
    pubmed_features = rows(
        conn,
        """
        SELECT match_features_json, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM evidence_claims
        WHERE source_key = 'pubmed_eutilities'
        GROUP BY match_features_json
        ORDER BY count DESC
        """,
    )
    broad_discovery = rows(
        conn,
        """
        SELECT classification, COUNT(*) AS count
        FROM sources
        WHERE source_type = 'penn_affiliated_source_discovery'
        GROUP BY classification
        ORDER BY count DESC
        """,
    )
    career_events = rows(
        conn,
        """
        SELECT event_type, status, COUNT(*) AS count,
               ROUND(AVG(confidence), 3) AS avg_confidence
        FROM career_events
        GROUP BY event_type, status
        ORDER BY event_type, status
        """,
    )
    broad_program_counts = rows(
        conn,
        """
        SELECT pr.program_name, p.role, COUNT(*) AS count
        FROM person_program_memberships m
        JOIN programs pr ON pr.program_key = m.program_key
        JOIN people p ON p.person_key = m.person_key
        WHERE m.population = 'penn_affiliated_current_trainees'
        GROUP BY pr.program_name, p.role
        ORDER BY count DESC, pr.program_name, p.role
        LIMIT 40
        """,
    )
    generic_program_labels = rows(
        conn,
        """
        SELECT pr.program_name, COUNT(*) AS count
        FROM person_program_memberships m
        JOIN programs pr ON pr.program_key = m.program_key
        WHERE pr.program_name IN ('Residents', 'Fellows')
        GROUP BY pr.program_name
        ORDER BY pr.program_name
        """,
    )
    contact_counts = rows(
        conn,
        """
        SELECT contact_type, contact_scope, verification_status, status,
               COUNT(*) AS count, ROUND(AVG(confidence), 3) AS avg_confidence
        FROM person_contacts
        GROUP BY contact_type, contact_scope, verification_status, status
        ORDER BY contact_type, contact_scope, verification_status, status
        """,
    )
    conn.close()

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_counts": source_counts,
        "evidence_counts": evidence_counts,
        "utility_observations": utility_observations,
        "openalex_feature_distribution": openalex_features,
        "pubmed_feature_distribution": pubmed_features,
        "penn_affiliated_discovery": broad_discovery,
        "career_event_counts": career_events,
        "broad_program_counts": broad_program_counts,
        "generic_program_labels": generic_program_labels,
        "contact_counts": contact_counts,
    }
    if openalex_features:
        openalex_learning = "Learning: OpenAlex is useful for generating review candidates when name, Penn affiliation, prior institution, and ORCID features cluster. It is not safe as a direct profile mutator because author disambiguation and stale affiliations remain real risks."
    else:
        openalex_learning = "Learning: OpenAlex remains a promising author-disambiguation utility, but the current full-corpus run hit sustained 429 throttling. Record that as source availability/operations evidence, not as rejected person identity evidence."
    (ARTIFACTS / "source_quality_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Penn Source Quality Learnings",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## What This Pass Did",
        "",
        "This pass widened Penn source discovery beyond Department of Medicine, then ran candidate-only scholarly enrichment across the current resident/fellow corpus. No scholarly claims were accepted automatically.",
        "",
        "## Penn-Wide Source Discovery",
        "",
        *md_table(broad_discovery, ["classification", "count"]),
        "",
        "Interpretation: `trainee_roster_candidate` is a review queue, not a canonical roster count. Program-context pages can mention residents/fellows without listing people, and some faculty pages share the same bio components as trainee pages.",
        "",
        "## Penn-Wide Program Categorization",
        "",
        *md_table(broad_program_counts, ["program_name", "role", "count"]),
        "",
        f"Generic `Residents`/`Fellows` program labels remaining: {sum(row['count'] for row in generic_program_labels)}.",
        "",
        "Learning: program names often require URL-plus-section inference. Page titles alone are too weak because official pages can be titled `Residents` or `Fellows`, while one source page can contain multiple program sections.",
        "",
        "## Evidence Counts",
        "",
        *md_table(evidence_counts, ["source_key", "status", "claim_type", "count", "avg_confidence"]),
        "",
        "## Utility Observations",
        "",
        *md_table(utility_observations, ["utility_key", "sample_size", "candidate_claims", "accepted_claims", "rejected_claims", "ambiguous_claims", "metrics_json"]),
        "",
        "## OpenAlex Feature Distribution",
        "",
        *md_table(openalex_features, ["match_features_json", "count", "avg_confidence"]),
        "",
        openalex_learning,
        "",
        "## PubMed Feature Distribution",
        "",
        *md_table(pubmed_features, ["match_features_json", "count", "avg_confidence"]),
        "",
        "Learning: PubMed E-utilities is a strong article database, but author-query search is a weak identity resolver. It should be used after candidate author identity is constrained by OpenAlex/ORCID/profile context, or at article-level with affiliation/coauthor checks.",
        "",
        "## Career / Attending Trend Candidates",
        "",
        *md_table(career_events, ["event_type", "status", "count", "avg_confidence"]),
        "",
        "Learning: current faculty pages and alumni/outcome pages should feed a career-event layer, not the core current-trainee roster. Current Penn attending candidates are useful endpoints for future trend analysis, but they still need reconciliation to prior Penn training records before we claim someone 'ended up at Penn.'",
        "",
        "## Public Contact Evidence",
        "",
        *md_table(contact_counts, ["contact_type", "contact_scope", "verification_status", "status", "count", "avg_confidence"]),
        "",
        "Learning: public contact channels belong in a separate evidence table because a person can have multiple public contacts from sources with different assurance levels. Raw HTML remains redacted; only structured, source-linked public contact candidates are stored.",
        "",
        "## Reconciliation Rule Update",
        "",
        "For the next pass, accept research enrichment only when at least two non-name anchors agree. Examples: official profile link plus ORCID; OpenAlex Penn affiliation plus specialty-topic match; PubMed affiliation plus coauthor cluster; NPI specialty/location plus official profile.",
        "",
        "## Source References",
        "",
        "- OpenAlex institutions documentation notes that all OpenAlex institutions have ROR IDs and that parsing author affiliations is nontrivial: https://docs.openalex.org/api-entities/institutions",
        "- NCBI E-utilities are the public API for Entrez databases including PubMed: https://www.ncbi.nlm.nih.gov/home/develop/api/",
        "- ORCID supports organization identifiers including ROR for affiliations: https://info.orcid.org/documentation/integration-guide/working-with-organization-identifiers/",
        "- NPPES provides an official public read API for NPI Registry data: https://npiregistry.cms.hhs.gov/api-page",
        "- ClinicalTrials.gov provides an official API and OpenAPI specification: https://clinicaltrials.gov/data-about-studies/learn-about-api",
        "- WDOMS is a searchable directory of undergraduate medical education programs; listing confirms existence but not accreditation or endorsement unless stated: https://wfme.org/world-directory/",
    ]
    (REPORTS / "penn-source-quality-learnings-2026-06-02.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    print("wrote source quality report")


if __name__ == "__main__":
    main()
