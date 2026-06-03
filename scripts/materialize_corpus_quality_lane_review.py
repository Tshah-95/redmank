#!/usr/bin/env python3
"""Materialize corpus-wide person quality lanes and normalization review hints."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

CSV_OUT = ARTIFACTS / "corpus_quality_lane_review.csv"
JSON_OUT = ARTIFACTS / "corpus_quality_lane_review.json"
SUMMARY_OUT = ARTIFACTS / "corpus_quality_lane_review_summary.json"

FIELDS = [
    "quality_review_key",
    "person_key",
    "display_name",
    "role",
    "lane",
    "lane_status",
    "quality_band",
    "confidence_score",
    "accepted_fact_count",
    "candidate_count",
    "review_ready_count",
    "blocker_count",
    "gap_count",
    "best_source_url",
    "recommended_next_action",
    "auto_fixable",
    "proposed_fix_json",
    "evidence_json",
    "generated_at",
]

csv.field_size_limit(sys.maxsize)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def stable_key(*parts: object) -> str:
    return hashlib.sha256(dumps(parts).encode("utf-8")).hexdigest()[:20]


def read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def as_int(value) -> int:
    if value in (None, ""):
        return 0
    return int(float(value))


def as_float(value) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def parse_json(value: str | None, default):
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def norm_label(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", str(value).lower().replace("&", " and ")).strip()
    value = re.sub(r"\bsom\b", "school of medicine", value)
    value = re.sub(r"\brwj\b", "robert wood johnson", value)
    value = re.sub(r"\bmt\b", "mount", value)
    value = re.sub(r"[^a-z0-9 ]+", " ", value)
    value = re.sub(r"\b(the|at|of|and)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


DEGREE_TOKENS = {"ba", "bs", "bsc", "ma", "ms", "msc", "mph", "mhs", "md", "phd", "do", "dpm", "mba"}
DIRECTIONAL_TOKENS = {
    "north",
    "northern",
    "northeastern",
    "northwestern",
    "south",
    "southern",
    "southeastern",
    "southwestern",
    "east",
    "eastern",
    "west",
    "western",
}


def tokens(value: str | None) -> set[str]:
    return set(norm_label(value).split())


def ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, norm_label(left), norm_label(right)).ratio()


def indexed(rows: list[dict], key: str) -> dict[str, dict]:
    return {row.get(key) or "": row for row in rows if row.get(key)}


def grouped(rows: list[dict], key: str) -> dict[str, list[dict]]:
    output: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        output[row.get(key) or ""].append(row)
    return output


def quality_band(score: float, blocker_count: int, gap_count: int) -> str:
    if blocker_count:
        return "blocked_or_conflicted"
    if score >= 0.9 and gap_count == 0:
        return "strong_verified"
    if score >= 0.75:
        return "usable_with_review_gaps"
    if score >= 0.5:
        return "review_ready"
    return "insufficient_or_candidate_only"


def row(
    *,
    person: dict,
    lane: str,
    lane_status: str,
    score: float,
    accepted: int = 0,
    candidate: int = 0,
    review_ready: int = 0,
    blockers: int = 0,
    gaps: int = 0,
    best_source_url: str = "",
    recommended_next_action: str,
    auto_fixable: int = 0,
    proposed_fix=None,
    evidence=None,
    generated_at: str,
) -> dict:
    payload = {
        "quality_review_key": "quality_lane_" + stable_key(person.get("person_key"), lane),
        "person_key": person.get("person_key") or "",
        "display_name": person.get("display_name") or "",
        "role": person.get("role") or "",
        "lane": lane,
        "lane_status": lane_status,
        "quality_band": quality_band(score, blockers, gaps),
        "confidence_score": round(score, 3),
        "accepted_fact_count": accepted,
        "candidate_count": candidate,
        "review_ready_count": review_ready,
        "blocker_count": blockers,
        "gap_count": gaps,
        "best_source_url": best_source_url,
        "recommended_next_action": recommended_next_action,
        "auto_fixable": auto_fixable,
        "proposed_fix_json": dumps(proposed_fix or []),
        "evidence_json": dumps(evidence or {}),
        "generated_at": generated_at,
    }
    return {field: payload[field] for field in FIELDS}


def source_profile_lane(person: dict, profile_packets_by_person: dict[str, list[dict]], generated_at: str) -> dict:
    packets = profile_packets_by_person.get(person["person_key"], [])
    profile_url = person.get("profile_url") or ""
    if profile_url:
        return row(
            person=person,
            lane="official_profile",
            lane_status="accepted_profile_url",
            score=0.9,
            accepted=1,
            best_source_url=profile_url,
            recommended_next_action="reobserve_profile_url_on_refresh_clock",
            evidence={"profile_url": profile_url, "profile_discovery_packets": len(packets)},
            generated_at=generated_at,
        )
    if packets:
        best = sorted(packets, key=lambda item: -as_int(item.get("best_candidate_http_status") == "200"))[0]
        return row(
            person=person,
            lane="official_profile",
            lane_status=best.get("packet_status") or "profile_candidate_review_ready",
            score=0.62,
            candidate=len(packets),
            review_ready=sum(1 for item in packets if "ready" in (item.get("support_status") or "")),
            gaps=1,
            best_source_url=best.get("best_candidate_url") or "",
            recommended_next_action="review_or_probe_official_profile_candidate",
            evidence={"profile_gap_status": best.get("profile_gap_status"), "packets": len(packets)},
            generated_at=generated_at,
        )
    return row(
        person=person,
        lane="official_profile",
        lane_status="missing_profile_signal",
        score=0.35,
        gaps=1,
        recommended_next_action="run_official_profile_discovery_or_accept_absence_context",
        evidence={"profile_url": "", "profile_discovery_packets": 0},
        generated_at=generated_at,
    )


def has_directional_collision(left: str, right: str) -> bool:
    left_tokens = tokens(left)
    right_tokens = tokens(right)
    changed_tokens = (left_tokens ^ right_tokens) - {"university", "college", "school", "medicine", "medical"}
    return bool(changed_tokens & DIRECTIONAL_TOKENS)


def has_degree_suffix_collision(left: str, right: str) -> bool:
    changed_tokens = tokens(left) ^ tokens(right)
    return bool(changed_tokens & DEGREE_TOKENS)


def best_org_suggestion(value: str, category: str, category_labels: dict[str, list[str]]) -> dict | None:
    normalized = norm_label(value)
    if not normalized:
        return None
    best_label = ""
    best_ratio = 0.0
    for label in category_labels.get(category, []):
        if norm_label(label) == normalized:
            continue
        if has_degree_suffix_collision(value, label):
            continue
        if has_directional_collision(value, label):
            continue
        score = ratio(value, label)
        if score > best_ratio:
            best_ratio = score
            best_label = label
    if best_ratio >= 0.93:
        return {"suggested_canonical_name": best_label, "similarity": round(best_ratio, 3)}
    return None


def build_org_label_index(events: list[dict], review_queue: list[dict]) -> dict[str, list[str]]:
    labels: dict[str, set[str]] = defaultdict(set)
    for event in events:
        if event.get("resolver_status") not in {"seeded_alias", "accepted_identifier"}:
            continue
        category = event.get("category") or ""
        name = event.get("canonical_name") or event.get("raw_value") or ""
        if name:
            labels[category].add(name)
    for item in review_queue:
        if item.get("resolver_status") not in {"seeded_alias", "accepted_identifier"}:
            continue
        event_type = item.get("event_type") or ""
        category = {
            "medical_school": "medical_school",
            "residency_program": "clinical_training_site",
            "undergraduate_school": "undergraduate_institution",
            "graduate_school": "graduate_school",
        }.get(event_type, event_type)
        name = item.get("canonical_name") or item.get("raw_value") or ""
        if name:
            labels[category].add(name)
    return {category: sorted(values) for category, values in labels.items()}


def organization_lane(person: dict, events: list[dict], category_labels: dict[str, list[str]], generated_at: str) -> dict:
    suggestions = []
    low_confidence = []
    for event in events:
        if event.get("resolver_status") in {"seeded_alias", "accepted_identifier"}:
            continue
        confidence = as_float(event.get("confidence"))
        if confidence < 0.75:
            low_confidence.append(event)
        suggestion = best_org_suggestion(event.get("canonical_name") or event.get("raw_value") or "", event.get("category") or "", category_labels)
        if suggestion:
            suggestions.append(
                {
                    "event_type": event.get("event_type"),
                    "raw_value": event.get("raw_value"),
                    "current_canonical_name": event.get("canonical_name"),
                    **suggestion,
                }
            )
    if suggestions:
        return row(
            person=person,
            lane="organization_normalization",
            lane_status="auto_suggested_alias_review",
            score=0.58,
            candidate=len(events),
            review_ready=len(suggestions),
            blockers=0,
            gaps=len(suggestions),
            recommended_next_action="review_and_accept_or_reject_suggested_organization_aliases",
            auto_fixable=1,
            proposed_fix=suggestions,
            evidence={"event_count": len(events), "low_confidence_events": len(low_confidence)},
            generated_at=generated_at,
        )
    if low_confidence:
        return row(
            person=person,
            lane="organization_normalization",
            lane_status="cleaned_label_review_recommended",
            score=0.68,
            candidate=len(events),
            gaps=len(low_confidence),
            recommended_next_action="review_low_confidence_organization_labels_or_seed_aliases",
            evidence={"event_count": len(events), "low_confidence_events": len(low_confidence)},
            generated_at=generated_at,
        )
    return row(
        person=person,
        lane="organization_normalization",
        lane_status="no_obvious_normalization_gap",
        score=0.9 if events else 0.55,
        accepted=sum(1 for item in events if item.get("resolver_status") == "seeded_alias"),
        candidate=sum(1 for item in events if item.get("resolver_status") != "seeded_alias"),
        recommended_next_action="monitor_new_training_background_labels",
        evidence={"event_count": len(events), "resolver_status_counts": dict(Counter(item.get("resolver_status") or "" for item in events))},
        generated_at=generated_at,
    )


def build_rows() -> list[dict]:
    generated_at = now_utc()
    people = read_csv(ARTIFACTS / "people_resolved.csv")
    training_states_by_person = grouped(read_csv(ARTIFACTS / "training_states_current.csv"), "person_key")
    stage_by_person = indexed(read_csv(ARTIFACTS / "person_training_stage_state.csv"), "person_key")
    events_by_person = grouped(read_csv(ARTIFACTS / "training_events_resolved.csv"), "person_key")
    evidence_by_person = grouped(read_csv(ARTIFACTS / "evidence_claims.csv"), "person_key")
    dossiers = indexed(read_csv(ARTIFACTS / "person_enrichment_dossiers.csv"), "person_key")
    review_packets = indexed(read_csv(ARTIFACTS / "person_evidence_review_packets.csv"), "person_key")
    research = indexed(read_csv(ARTIFACTS / "research_identity_corroboration.csv"), "person_key")
    contacts_by_person = grouped(read_csv(ARTIFACTS / "contact_verification_contracts.csv"), "person_key")
    profile_packets_by_person = grouped(read_csv(ARTIFACTS / "official_profile_discovery_batch_packets.csv"), "person_key")
    category_labels = build_org_label_index(
        read_csv(ARTIFACTS / "training_events_resolved.csv"),
        read_csv(ARTIFACTS / "organization_review_queue.csv"),
    )

    output = []
    for person in people:
        person_key = person["person_key"]
        states = training_states_by_person.get(person_key, [])
        stage = stage_by_person.get(person_key, {})
        evidence = evidence_by_person.get(person_key, [])
        dossier = dossiers.get(person_key, {})
        packet = review_packets.get(person_key, {})
        research_row = research.get(person_key, {})
        contact_rows = contacts_by_person.get(person_key, [])

        output.append(
            row(
                person=person,
                lane="roster_identity",
                lane_status="current_roster_identity" if person.get("current_status") == "current" and states else "identity_gap",
                score=0.94 if person.get("current_status") == "current" and states else 0.45,
                accepted=1 if person.get("current_status") == "current" else 0,
                gaps=0 if states else 1,
                best_source_url=(evidence[0].get("source_url") if evidence else person.get("profile_url") or ""),
                recommended_next_action="retain_roster_identity_and_refresh_source" if states else "find_current_roster_or_profile_identity_anchor",
                evidence={"quality_tier": person.get("quality_tier"), "training_state_rows": len(states)},
                generated_at=generated_at,
            )
        )
        output.append(
            row(
                person=person,
                lane="training_temporal_state",
                lane_status=stage.get("stage_state_status") or "missing_training_temporal_contract",
                score=as_float(stage.get("confidence")) if stage else 0.3,
                accepted=len(states),
                gaps=0 if stage else 1,
                best_source_url=(evidence[0].get("source_url") if evidence else ""),
                recommended_next_action=(
                    "refresh_source_and_apply_temporal_contract"
                    if stage
                    else "create_training_temporal_contract_from_current_state"
                ),
                evidence={
                    "programs": [item.get("program_name") for item in states],
                    "expected_next_stage": stage.get("expected_next_stage"),
                    "stale_after_date": stage.get("stale_after_date"),
                    "policy_lane": stage.get("policy_lane"),
                },
                generated_at=generated_at,
            )
        )
        output.append(source_profile_lane(person, profile_packets_by_person, generated_at))
        output.append(organization_lane(person, events_by_person.get(person_key, []), category_labels, generated_at))
        output.append(
            row(
                person=person,
                lane="person_enrichment",
                lane_status=dossier.get("dossier_status") or "missing_enrichment_dossier",
                score=min((as_int(dossier.get("coverage_score")) or 0) / 100.0, 1.0) if dossier else 0.25,
                accepted=as_int(dossier.get("accepted_enrichment_count")),
                candidate=as_int(dossier.get("candidate_evidence_count")),
                review_ready=as_int(dossier.get("review_ready_evidence_count")),
                blockers=1 if dossier.get("acceptance_blocker") else 0,
                gaps=len([item for item in (dossier.get("missing_surface_summary") or "").split(";") if item.strip()]),
                best_source_url=(dossier.get("top_source_urls") or "").split("; ")[0] if dossier else "",
                recommended_next_action=dossier.get("recommended_next_action") or "materialize_person_enrichment_dossier",
                evidence={"coverage_band": dossier.get("coverage_band"), "acceptance_blocker": dossier.get("acceptance_blocker")},
                generated_at=generated_at,
            )
        )
        output.append(
            row(
                person=person,
                lane="identity_reconciliation",
                lane_status=packet.get("packet_status") or "no_review_packet",
                score=0.72 if packet else 0.45,
                candidate=as_int(packet.get("evidence_record_count")),
                review_ready=as_int(packet.get("review_ready_record_count")),
                blockers=1 if packet.get("acceptance_blocker") else 0,
                best_source_url=packet.get("best_source_url") or "",
                recommended_next_action=packet.get("recommended_next_action") or "collect_identity_or_enrichment_evidence",
                evidence={
                    "review_kind": packet.get("review_kind"),
                    "best_decision": packet.get("best_decision"),
                    "top_claim_types": packet.get("top_claim_types"),
                },
                generated_at=generated_at,
            )
        )
        output.append(
            row(
                person=person,
                lane="research_identity",
                lane_status=research_row.get("research_identity_status") or "no_research_signal",
                score=as_float(research_row.get("best_confidence")) if research_row else 0.4,
                accepted=as_int(research_row.get("accepted_research_count")),
                candidate=as_int(research_row.get("research_candidate_count")),
                review_ready=as_int(research_row.get("research_review_ready_count")),
                blockers=1 if research_row.get("research_identity_status") in {"conflict_review_required"} else 0,
                gaps=1 if research_row.get("recommended_review_route") in {"collect_secondary_identity_anchors_before_review"} else 0,
                best_source_url="",
                recommended_next_action=research_row.get("recommended_review_route") or "monitor_research_sources",
                evidence={
                    "top_claim_types": research_row.get("top_claim_types"),
                    "required_next_evidence": research_row.get("required_next_evidence"),
                    "non_name_anchor_count": research_row.get("non_name_anchor_count"),
                },
                generated_at=generated_at,
            )
        )
        output.append(
            row(
                person=person,
                lane="contact_verification",
                lane_status="contact_contracts_present" if contact_rows else "no_contact_evidence",
                score=0.65 if contact_rows else 0.4,
                candidate=len(contact_rows),
                gaps=0 if contact_rows else 1,
                best_source_url=contact_rows[0].get("source_url") if contact_rows else "",
                recommended_next_action="verify_public_contact_contracts" if contact_rows else "collect_only_public_role-appropriate_contact_sources",
                evidence={"contact_contract_count": len(contact_rows), "contact_types": dict(Counter(item.get("contact_type") for item in contact_rows))},
                generated_at=generated_at,
            )
        )

    output.sort(key=lambda item: (item["person_key"], item["lane"]))
    return output


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_sqlite(rows: list[dict]) -> None:
    conn = sqlite3.connect(DB)
    with conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute("DELETE FROM corpus_quality_lane_review")
        fields = ", ".join(FIELDS)
        placeholders = ", ".join(f":{field}" for field in FIELDS)
        conn.executemany(
            f"INSERT OR REPLACE INTO corpus_quality_lane_review ({fields}) VALUES ({placeholders})",
            rows,
        )
    conn.close()


def write_summary(rows: list[dict]) -> None:
    people = {row["person_key"] for row in rows}
    by_lane_status = Counter(f"{row['lane']}:{row['lane_status']}" for row in rows)
    payload = {
        "generated_at": max((row["generated_at"] for row in rows), default=now_utc()),
        "csv": str(CSV_OUT.relative_to(ROOT)),
        "json": str(JSON_OUT.relative_to(ROOT)),
        "review_rows": len(rows),
        "person_count": len(people),
        "lane_count": len({row["lane"] for row in rows}),
        "auto_fixable_rows": sum(as_int(row["auto_fixable"]) for row in rows),
        "blocker_rows": sum(1 for row in rows if as_int(row["blocker_count"])),
        "gap_rows": sum(1 for row in rows if as_int(row["gap_count"])),
        "by_lane": dict(sorted(Counter(row["lane"] for row in rows).items())),
        "by_quality_band": dict(sorted(Counter(row["quality_band"] for row in rows).items())),
        "by_lane_status": dict(sorted(by_lane_status.items())),
        "top_auto_fixable": [
            {
                "display_name": row["display_name"],
                "role": row["role"],
                "lane": row["lane"],
                "lane_status": row["lane_status"],
                "proposed_fix": parse_json(row["proposed_fix_json"], []),
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows
            if as_int(row["auto_fixable"])
        ][:50],
        "top_blockers": [
            {
                "display_name": row["display_name"],
                "role": row["role"],
                "lane": row["lane"],
                "lane_status": row["lane_status"],
                "recommended_next_action": row["recommended_next_action"],
            }
            for row in rows
            if as_int(row["blocker_count"])
        ][:50],
        "policy": (
            "Corpus quality lane review is non-mutating. Auto-fixable rows are suggested reviewer-gated "
            "normalizations, not applied truth changes."
        ),
    }
    SUMMARY_OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    rows = build_rows()
    write_csv(CSV_OUT, rows)
    JSON_OUT.write_text(json.dumps(rows, indent=2, ensure_ascii=True, sort_keys=True) + "\n", encoding="utf-8")
    write_sqlite(rows)
    write_summary(rows)
    print(dumps({"corpus_quality_lane_review": len(rows), "people": len({row["person_key"] for row in rows})}))


if __name__ == "__main__":
    main()
