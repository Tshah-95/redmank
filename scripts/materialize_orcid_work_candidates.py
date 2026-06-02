#!/usr/bin/env python3
"""Materialize DOI/PMID-level ORCID public work candidates."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
PROFILE_CLAIMS = ARTIFACTS / "orcid_profile_candidate_claims.json"
OUT_CLAIMS = ARTIFACTS / "orcid_work_candidate_claims.json"
OUT_SUMMARY = ARTIFACTS / "orcid_work_candidate_summary.json"


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def norm_id(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "").strip()


def doi_url(value: str) -> str:
    cleaned = value.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    return f"https://doi.org/{cleaned}" if cleaned else ""


def stable_ids(work: dict) -> dict[str, list[str]]:
    ids: dict[str, list[str]] = {"doi": [], "pmid": [], "pmc": []}
    for item in work.get("external_ids") or []:
        id_type = (item.get("type") or "").lower()
        value = norm_id(str(item.get("value") or ""))
        if id_type in ids and value and value not in ids[id_type]:
            ids[id_type].append(value)
    return ids


def publication_year(date_value: str | None) -> int | None:
    match = re.match(r"(\d{4})", date_value or "")
    return int(match.group(1)) if match else None


def claim_value(ids: dict[str, list[str]]) -> str:
    if ids["pmid"]:
        return f"pmid:{ids['pmid'][0]}"
    if ids["doi"]:
        return f"doi:{ids['doi'][0].lower()}"
    if ids["pmc"]:
        return f"pmc:{ids['pmc'][0]}"
    return ""


def source_url(ids: dict[str, list[str]], orcid_uri: str) -> str:
    if ids["pmid"]:
        return f"https://pubmed.ncbi.nlm.nih.gov/{ids['pmid'][0]}/"
    if ids["doi"]:
        return doi_url(ids["doi"][0])
    return orcid_uri


def build_claim(profile: dict, work: dict) -> dict | None:
    ids = stable_ids(work)
    value = claim_value(ids)
    if not value:
        return None
    profile_evidence = profile.get("evidence") or {}
    profile_features = set(profile.get("match_features") or [])
    year = publication_year(work.get("publication_date"))
    features = ["orcid_profile_candidate", "orcid_work_public"]
    if ids["doi"]:
        features.append("doi_present")
    if ids["pmid"]:
        features.append("pmid_present")
    if ids["pmc"]:
        features.append("pmc_present")
    if year and year >= 2016:
        features.append("recent_publication")
    if "orcid_name_match" in profile_features:
        features.append("orcid_name_match_from_profile")
    if "orcid_penn_affiliation" in profile_features:
        features.append("orcid_penn_affiliation_from_profile")
    if "orcid_external_ids_present" in profile_features:
        features.append("orcid_external_ids_present_from_profile")

    confidence = min(float(profile.get("confidence") or 0.0), 0.9) * 0.72
    confidence += 0.12 if ids["doi"] else 0.0
    confidence += 0.15 if ids["pmid"] else 0.0
    confidence += 0.04 if year and year >= 2016 else 0.0
    confidence = round(min(confidence, 0.92), 3)
    return {
        "person_key": profile["person_key"],
        "display_name": profile["display_name"],
        "role": profile["role"],
        "claim_type": "orcid_work_candidate",
        "claim_value": value,
        "source_key": "orcid_public_api",
        "source_url": source_url(ids, profile["claim_value"]),
        "source_type": "scholarly_api",
        "confidence": confidence,
        "status": "needs_review" if confidence >= 0.75 else "candidate",
        "match_features": features,
        "reconciliation_notes": (
            "ORCID public work candidate with stable DOI/PMID evidence; accept only after article metadata, "
            "author position, and same-person profile/source context are reconciled."
        ),
        "evidence": {
            "utility_key": "orcid_public_api",
            "collector": "scripts/materialize_orcid_work_candidates.py",
            "orcid_profile_claim_value": profile["claim_value"],
            "orcid": profile_evidence.get("orcid", ""),
            "orcid_record_name": profile_evidence.get("record_name", ""),
            "orcid_profile_status": profile.get("status", ""),
            "orcid_profile_confidence": profile.get("confidence", 0),
            "orcid_profile_features": profile.get("match_features", []),
            "work": {
                "title": work.get("title") or "",
                "journal_title": work.get("journal_title") or "",
                "type": work.get("type") or "",
                "publication_date": work.get("publication_date") or "",
                "publication_year": year or "",
                "source": work.get("source") or "",
                "visibility": work.get("visibility") or "",
                "stable_ids": ids,
                "external_ids": work.get("external_ids") or [],
            },
        },
    }


def insert_claim(conn: sqlite3.Connection, claim: dict) -> None:
    conn.execute(
        """
        INSERT INTO evidence_claims
        (person_key, claim_type, claim_value, source_key, source_url, source_type,
         confidence, status, match_features_json, reconciliation_notes, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            claim["person_key"],
            claim["claim_type"],
            claim["claim_value"],
            claim["source_key"],
            claim["source_url"],
            claim["source_type"],
            claim["confidence"],
            claim["status"],
            dumps(claim["match_features"]),
            claim["reconciliation_notes"],
            dumps(claim["evidence"]),
        ),
    )


def current_claims(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT e.person_key, p.display_name, p.role, e.claim_type, e.claim_value,
               e.source_key, e.source_url, e.source_type, e.confidence, e.status,
               e.match_features_json, e.reconciliation_notes, e.evidence_json
        FROM evidence_claims e
        JOIN people p ON p.person_key = e.person_key
        WHERE e.source_key = 'orcid_public_api'
          AND e.claim_type IN ('orcid_work_candidate', 'orcid_work_candidate_error')
        ORDER BY p.display_name, e.claim_type, e.claim_value
        """
    ).fetchall()
    output = []
    for row in rows:
        output.append(
            {
                "person_key": row["person_key"],
                "display_name": row["display_name"],
                "role": row["role"],
                "claim_type": row["claim_type"],
                "claim_value": row["claim_value"],
                "source_key": row["source_key"],
                "source_url": row["source_url"],
                "source_type": row["source_type"],
                "confidence": row["confidence"],
                "status": row["status"],
                "match_features": json.loads(row["match_features_json"] or "[]"),
                "reconciliation_notes": row["reconciliation_notes"],
                "evidence": json.loads(row["evidence_json"] or "{}"),
            }
        )
    return output


def record_quality(conn: sqlite3.Connection, claims: list[dict], profile_count: int, generated_at: str) -> None:
    conn.execute(
        """
        INSERT INTO source_quality_observations
        (utility_key, observed_at, sample_size, candidate_claims, accepted_claims,
         rejected_claims, ambiguous_claims, notes, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "orcid_work_candidates",
            generated_at,
            profile_count,
            sum(1 for claim in claims if claim["status"] == "candidate"),
            0,
            sum(1 for claim in claims if claim["status"] == "rejected"),
            sum(1 for claim in claims if claim["status"] == "needs_review"),
            "ORCID public work candidates materialized from committed ORCID profile artifacts; no claims accepted automatically.",
            dumps(
                {
                    "claims": len(claims),
                    "people_with_claims": len({claim["person_key"] for claim in claims}),
                    "feature_counts": dict(
                        Counter(feature for claim in claims for feature in claim["match_features"]).most_common(20)
                    ),
                    "mean_confidence": round(sum(float(claim["confidence"]) for claim in claims) / len(claims), 4)
                    if claims
                    else 0,
                }
            ),
        ),
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--replace-claim-type", action="store_true")
    args = parser.parse_args()

    profiles = json.loads(PROFILE_CLAIMS.read_text(encoding="utf-8")) if PROFILE_CLAIMS.exists() else []
    generated_at = datetime.now(timezone.utc).isoformat()
    claims = []
    seen = set()
    for profile in profiles:
        works = ((profile.get("evidence") or {}).get("profile") or {}).get("works") or []
        for work in works:
            claim = build_claim(profile, work)
            if not claim:
                continue
            key = (claim["person_key"], claim["claim_value"])
            if key in seen:
                continue
            seen.add(key)
            claims.append(claim)
    claims.sort(key=lambda row: (row["display_name"], row["claim_value"]))

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    with conn:
        if args.replace_claim_type:
            conn.execute("DELETE FROM evidence_claims WHERE source_key = 'orcid_public_api' AND claim_type = 'orcid_work_candidate'")
            conn.execute("DELETE FROM source_quality_observations WHERE utility_key = 'orcid_work_candidates'")
        for claim in claims:
            insert_claim(conn, claim)
        record_quality(conn, claims, len(profiles), generated_at)
    durable_claims = current_claims(conn)
    conn.close()

    by_status = Counter(claim["status"] for claim in durable_claims)
    by_role = Counter(claim["role"] for claim in durable_claims)
    by_feature = Counter(feature for claim in durable_claims for feature in claim["match_features"])
    summary = {
        "generated_at": generated_at,
        "source_key": "orcid_public_api",
        "utility_key": "orcid_work_candidates",
        "profiles_considered": len(profiles),
        "claims_generated": len(claims),
        "durable_claim_rows": len(durable_claims),
        "people_with_durable_claims": len({claim["person_key"] for claim in durable_claims}),
        "by_status": dict(sorted(by_status.items())),
        "by_role": dict(sorted(by_role.items())),
        "top_match_features": dict(by_feature.most_common(20)),
        "policy": "ORCID work candidates require DOI/PMID/PMC evidence and remain review-only until reconciled with article metadata, author position, and same-person source context.",
        "json": str(OUT_CLAIMS.relative_to(ROOT)),
    }
    OUT_CLAIMS.write_text(
        json.dumps(durable_claims, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    OUT_SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(dumps(summary))


if __name__ == "__main__":
    main()
