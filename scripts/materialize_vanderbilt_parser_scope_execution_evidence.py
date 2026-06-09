#!/usr/bin/env python3
"""Materialize non-mutating Vanderbilt parser/scope execution evidence."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
RESEARCH = ROOT / "artifacts" / "research"

SOURCE_JSON = ARTIFACTS / "vanderbilt_approved_parser_scope_next_packets.json"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_approved_parser_scope_next_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_parser_scope_execution_evidence.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_parser_scope_execution_evidence.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_parser_scope_execution_evidence_summary.json"
OUT_MD = RESEARCH / "vanderbilt-parser-scope-execution-evidence-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "098c0a813eb577552b46e9454fbf2e9088bcee228d0aa678827439eba082e261"

MUTATION_POLICY = (
    "Non-mutating Vanderbilt parser/scope execution evidence. This ledger records parser strategy, scope status, "
    "route freshness, hashes, and coarse candidate counts for approved next-packet rows. It stores no raw HTML, "
    "raw text, raw headings, raw anchor samples, accepted people, parser-accepted person rows, training-state "
    "mutation, denominator closure, Vanderbilt school verification, URL rewrite, unsupported-label ingestion, "
    "enrichment acceptance, raw dump publication, or unique-person identity collapse."
)

FIELDS = [
    "execution_evidence_key",
    "source_next_packet_key",
    "program_key",
    "program_name",
    "approved_next_artifact_lane",
    "fetch_url",
    "fetch_status",
    "http_status",
    "final_url",
    "content_sha256",
    "visible_text_sha256",
    "route_hash_matches_prior_observation",
    "parser_family",
    "parser_probe_status",
    "candidate_entity_count",
    "candidate_group_count",
    "person_anchor_count",
    "profile_like_anchor_count",
    "current_signal_count",
    "resident_signal_count",
    "fellow_signal_count",
    "pgy_signal_count",
    "scope_disposition_status",
    "recourse_status",
    "approved_followup_artifact",
    "parser_acceptance_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "required_next_action",
    "evidence_json",
    "mutation_policy",
    "generated_at",
]

ROWSET_FIELDS = [
    "source_next_packet_key",
    "program_key",
    "program_name",
    "approved_next_artifact_lane",
    "fetch_url",
    "fetch_status",
    "http_status",
    "final_url",
    "content_sha256",
    "visible_text_sha256",
    "route_hash_matches_prior_observation",
    "parser_family",
    "parser_probe_status",
    "candidate_entity_count",
    "candidate_group_count",
    "person_anchor_count",
    "profile_like_anchor_count",
    "current_signal_count",
    "resident_signal_count",
    "fellow_signal_count",
    "pgy_signal_count",
    "scope_disposition_status",
    "recourse_status",
    "approved_followup_artifact",
    "parser_acceptance_allowed",
    "person_ingestion_allowed",
    "denominator_closure_allowed",
    "required_next_action",
]

HEADERS = {
    "User-Agent": "redmank-vanderbilt-parser-scope-evidence/0.1 (+https://github.com/Tshah-95/redmank)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.5",
}

CURRENT_RE = re.compile(r"\b(current|residents?|fellows?|trainees?|house\s*staff|pgy[-\s]?\d)\b", re.I)
RESIDENT_RE = re.compile(r"\b(residents?|residency)\b", re.I)
FELLOW_RE = re.compile(r"\b(fellows?|fellowship)\b", re.I)
PGY_RE = re.compile(r"\bpgy[-\s]?\d\b", re.I)
NAMEISH_RE = re.compile(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b")
WHITESPACE_RE = re.compile(r"\s+")

csv.field_size_limit(sys.maxsize)


class EvidenceHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.text_parts: list[str] = []
        self.anchor_parts: list[dict[str, str]] = []
        self.heading_texts: list[str] = []
        self.class_counts: Counter[str] = Counter()
        self._tag_stack: list[str] = []
        self._active_anchor: dict[str, str] | None = None
        self._active_heading: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._tag_stack.append(tag)
        attr_map = {name.lower(): value or "" for name, value in attrs}
        for class_name in attr_map.get("class", "").split():
            self.class_counts[class_name.lower()] += 1
        if tag == "a" and attr_map.get("href"):
            self._active_anchor = {"text": "", "href": urljoin(self.base_url, attr_map["href"])}
            self.anchor_parts.append(self._active_anchor)
        if tag in {"h1", "h2", "h3", "h4"}:
            self._active_heading = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a":
            self._active_anchor = None
        if tag in {"h1", "h2", "h3", "h4"} and self._active_heading is not None:
            text = clean_text(" ".join(self._active_heading))
            if text:
                self.heading_texts.append(text)
            self._active_heading = None
        for index in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[index] == tag:
                del self._tag_stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if any(tag in {"script", "style", "noscript", "svg"} for tag in self._tag_stack):
            return
        text = clean_text(data)
        if not text:
            return
        self.text_parts.append(text)
        if self._active_anchor is not None:
            self._active_anchor["text"] = clean_text(self._active_anchor["text"] + " " + text)
        if self._active_heading is not None:
            self._active_heading.append(text)

    @property
    def visible_text(self) -> str:
        return clean_text(" ".join(self.text_parts))


def clean_text(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value or "").strip()


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt approved parser/scope next-packet summary JSON object.")
    checks = {
        "rowset_sha256": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "next_packet_rows": summary.get("next_packet_rows") == 20,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
    }
    if not all(checks.values()):
        raise SystemExit(f"Unexpected approved next-packet boundary: {checks}")
    return summary


def decode_content(content: bytes, content_type: str) -> str:
    encoding = "utf-8"
    if "charset=" in content_type.lower():
        encoding = content_type.lower().split("charset=", 1)[1].split(";", 1)[0].strip() or "utf-8"
    return content.decode(encoding, errors="replace")


def fetch(url: str) -> dict[str, object]:
    started = time.monotonic()
    try:
        request = Request(url, headers=HEADERS)
        with urlopen(request, timeout=30) as response:
            content = response.read()
            final_url = response.geturl()
            http_status = response.status
            content_type = response.headers.get("content-type", "")
    except HTTPError as exc:
        content = exc.read()
        final_url = exc.geturl()
        http_status = exc.code
        content_type = exc.headers.get("content-type", "")
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "fetch_status": "fetch_error",
            "fetch_error": type(exc).__name__ + ": " + str(exc)[:220],
            "http_status": "",
            "final_url": "",
            "content_sha256": "",
            "visible_text_sha256": "",
            "text": "",
            "anchors": [],
            "headings": [],
            "class_counts": {},
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }

    parser = EvidenceHTMLParser(final_url)
    parser.feed(decode_content(content, content_type))
    return {
        "fetch_status": "fetched",
        "fetch_error": "",
        "http_status": http_status,
        "final_url": final_url,
        "content_sha256": sha256_bytes(content),
        "visible_text_sha256": sha256_text(parser.visible_text),
        "text": parser.visible_text,
        "anchors": parser.anchor_parts,
        "headings": parser.heading_texts,
        "class_counts": dict(parser.class_counts),
        "elapsed_ms": int((time.monotonic() - started) * 1000),
    }


def parser_family(url: str, lane: str, http_status: object) -> str:
    parsed = urlparse(url)
    path = parsed.path.lower()
    host = parsed.netloc.lower()
    if str(http_status) == "404":
        return "http_error_recourse"
    if lane == "general_surgery_rendered_parser_scope_packet":
        return "vumc_general_surgery_current_residents_rendered_review"
    if "medicine.vumc.org" in host and "gastroenterology" in path:
        return "vumc_medicine_division_fellows_shared_page"
    if "pediatrics.vumc.org" in host and "/person/" in path:
        return "vumc_pediatrics_person_listing_page"
    if "pediatrics.vumc.org" in host:
        return "vumc_pediatrics_node_listing_page"
    if "psychiatry" in path or "pgy" in path:
        return "vumc_pgy_listing_page"
    if "ortho" in path:
        return "vumc_orthopaedics_current_residents_page"
    return "official_route_manual_parser_review"


def candidate_counts(fetch_result: dict[str, object]) -> dict[str, int]:
    text = str(fetch_result.get("text") or "")
    anchors = list(fetch_result.get("anchors") or [])
    headings = list(fetch_result.get("headings") or [])
    person_anchors = [anchor for anchor in anchors if "/person/" in str(anchor.get("href", ""))]
    profile_like = [
        anchor
        for anchor in anchors
        if any(token in str(anchor.get("href", "")).lower() for token in ["/person/", "/people/", "/faculty/"])
    ]
    heading_nameish = [heading for heading in headings if NAMEISH_RE.search(str(heading))]
    return {
        "person_anchor_count": len(person_anchors),
        "profile_like_anchor_count": len(profile_like),
        "candidate_entity_count": max(len(person_anchors), len(heading_nameish)),
        "candidate_group_count": len([heading for heading in headings if CURRENT_RE.search(str(heading))]),
        "current_signal_count": len(CURRENT_RE.findall(text)),
        "resident_signal_count": len(RESIDENT_RE.findall(text)),
        "fellow_signal_count": len(FELLOW_RE.findall(text)),
        "pgy_signal_count": len(PGY_RE.findall(text)),
    }


def classify_probe(source: dict[str, object], fetch_result: dict[str, object], counts: dict[str, int]) -> tuple[str, str, str, str]:
    lane = str(source.get("approved_next_artifact_lane") or "")
    http_status = str(fetch_result.get("http_status") or source.get("http_status") or "")
    if lane == "route_retry_or_recourse_packet":
        return (
            "recourse_http_route_retry_or_replace_source",
            "http_error_recourse_needed" if http_status == "404" else "recourse_route_reobserved_needs_disposition",
            "route_retry_or_source_discovery_recourse_packet",
            "Record retry/final route evidence and seek a stronger official current roster source before parser acceptance.",
        )
    if lane == "linked_route_scope_disposition_packet":
        if counts["current_signal_count"] and (counts["person_anchor_count"] or counts["fellow_signal_count"] or counts["resident_signal_count"]):
            status = "scope_disposition_ready_current_roster_context"
        else:
            status = "scope_disposition_needs_manual_context_review"
        return (
            status,
            "not_recourse",
            "linked_route_scope_disposition_packet",
            "Decide same-program, shared-source, or context-only scope using counts and hashes; do not rewrite URLs or close denominators.",
        )
    if lane == "general_surgery_rendered_parser_scope_packet":
        status = "rendered_review_ready_current_resident_signal" if counts["resident_signal_count"] else "rendered_review_needs_manual_recourse"
        return (
            status,
            "not_recourse",
            "general_surgery_rendered_parser_scope_packet",
            "Build rendered parser/scope evidence for General Surgery current-residents route without accepting people.",
        )
    if counts["candidate_entity_count"] or counts["person_anchor_count"]:
        status = "parser_build_review_ready_candidate_entity_counts"
    elif counts["current_signal_count"]:
        status = "parser_build_review_ready_current_text_without_entity_count"
    else:
        status = "parser_build_review_needs_manual_recourse"
    return (
        status,
        "not_recourse",
        "source_specific_parser_build_review_packet",
        "Build source-specific parser tests and candidate-only extraction count evidence; do not publish raw names or ingest people.",
    )


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("execution_evidence_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Parser Scope Execution Evidence",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Parser Scope Execution Evidence",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Evidence Rows",
        "",
        "| program | lane | parser family | probe status | candidates | people allowed | fetch url |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {program_name} | {approved_next_artifact_lane} | {parser_family} | {parser_probe_status} | {candidate_entity_count} | {person_ingestion_allowed} | {fetch_url} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_json(SOURCE_JSON)
    if not isinstance(source_rows, list):
        raise SystemExit("Expected approved parser/scope next-packet JSON array.")

    generated_at = datetime.now(timezone.utc).isoformat()
    fetch_cache: dict[str, dict[str, object]] = {}
    rows: list[dict[str, object]] = []
    for url in sorted({str(row.get("fetch_url") or "") for row in source_rows if row.get("fetch_url")}):
        fetch_cache[url] = fetch(url)

    for source in source_rows:
        url = str(source.get("fetch_url") or "")
        fetch_result = fetch_cache.get(url, {"fetch_status": "not_fetched"})
        counts = candidate_counts(fetch_result)
        lane = str(source.get("approved_next_artifact_lane") or "")
        family = parser_family(url, lane, fetch_result.get("http_status") or source.get("http_status"))
        probe_status, recourse_status, followup, next_action = classify_probe(source, fetch_result, counts)
        prior_hash = str(source.get("content_sha256") or "")
        current_hash = str(fetch_result.get("content_sha256") or "")
        hash_matches = "true" if prior_hash and current_hash and prior_hash == current_hash else "false"
        rows.append(
            {
                "execution_evidence_key": stable_key("vanderbilt_parser_scope_execution_evidence", source.get("next_packet_key"), current_hash),
                "source_next_packet_key": source.get("next_packet_key"),
                "program_key": source.get("program_key"),
                "program_name": source.get("program_name"),
                "approved_next_artifact_lane": lane,
                "fetch_url": url,
                "fetch_status": fetch_result.get("fetch_status", ""),
                "http_status": fetch_result.get("http_status", ""),
                "final_url": fetch_result.get("final_url", ""),
                "content_sha256": current_hash,
                "visible_text_sha256": fetch_result.get("visible_text_sha256", ""),
                "route_hash_matches_prior_observation": hash_matches,
                "parser_family": family,
                "parser_probe_status": probe_status,
                "candidate_entity_count": counts["candidate_entity_count"],
                "candidate_group_count": counts["candidate_group_count"],
                "person_anchor_count": counts["person_anchor_count"],
                "profile_like_anchor_count": counts["profile_like_anchor_count"],
                "current_signal_count": counts["current_signal_count"],
                "resident_signal_count": counts["resident_signal_count"],
                "fellow_signal_count": counts["fellow_signal_count"],
                "pgy_signal_count": counts["pgy_signal_count"],
                "scope_disposition_status": probe_status if "scope" in lane else "",
                "recourse_status": recourse_status,
                "approved_followup_artifact": followup,
                "parser_acceptance_allowed": "false",
                "person_ingestion_allowed": "false",
                "denominator_closure_allowed": "false",
                "required_next_action": next_action,
                "evidence_json": dumps(
                    {
                        "source_next_packet_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "source_next_packet_key": source.get("next_packet_key"),
                        "prior_route_observation_content_sha256": prior_hash,
                        "route_hash_matches_prior_observation": hash_matches,
                        "class_name_counts_top": dict(Counter(fetch_result.get("class_counts", {})).most_common(8)),
                        "fetch_error": fetch_result.get("fetch_error", ""),
                    }
                ),
                "mutation_policy": MUTATION_POLICY,
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (str(item["approved_next_artifact_lane"]), str(item["program_name"]), str(item["fetch_url"])))
    by_lane = Counter(str(row["approved_next_artifact_lane"]) for row in rows)
    by_family = Counter(str(row["parser_family"]) for row in rows)
    by_probe_status = Counter(str(row["parser_probe_status"]) for row in rows)
    by_hash_match = Counter(str(row["route_hash_matches_prior_observation"]) for row in rows)
    by_followup = Counter(str(row["approved_followup_artifact"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_approved_next_packets": str(SOURCE_JSON.relative_to(ROOT)),
        "source_approved_next_packet_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_approved_next_packet_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_next_packet_rows": source_summary.get("next_packet_rows"),
        "execution_evidence_rows": len(rows),
        "unique_fetch_urls": len(fetch_cache),
        "total_candidate_entity_count": sum(int(row["candidate_entity_count"]) for row in rows),
        "by_approved_next_artifact_lane": dict(sorted(by_lane.items())),
        "by_parser_family": dict(sorted(by_family.items())),
        "by_parser_probe_status": dict(sorted(by_probe_status.items())),
        "by_route_hash_matches_prior_observation": dict(sorted(by_hash_match.items())),
        "by_approved_followup_artifact": dict(sorted(by_followup.items())),
        "mutation_allowed": False,
        "parser_acceptance_allowed": False,
        "person_ingestion_allowed": False,
        "denominator_closure_allowed": False,
        "policy": MUTATION_POLICY,
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(json.dumps({k: summary[k] for k in ["execution_evidence_rows", "unique_fetch_urls", "rowset_sha256"]}, sort_keys=True))


if __name__ == "__main__":
    main()
