#!/usr/bin/env python3
"""Fetch approved public-safe Vanderbilt slice-2 route observations."""

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

SOURCE_CSV = ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet.csv"
SOURCE_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_live_fetch_approval_request_packet_summary.json"

OUT_CSV = ARTIFACTS / "vanderbilt_slice_2_live_route_observations.csv"
OUT_JSON = ARTIFACTS / "vanderbilt_slice_2_live_route_observations.json"
OUT_SUMMARY = ARTIFACTS / "vanderbilt_slice_2_live_route_observation_summary.json"
OUT_MD = RESEARCH / "vanderbilt-slice-2-live-route-observations-2026-06-09.md"

SOURCE_ROWSET_SHA256 = "98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d"
SOURCE_PLAN_ROWSET_SHA256 = "c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b"
GBRAIN_APPROVAL_LINE = (
    "APPROVE vanderbilt_slice_2_live_fetch_approval_request_packet_approved REQUEST_ROWS 9 "
    "SOURCE_PLAN_ROWS 9 SOURCE_ROWSET_SHA256 c759c51d71ba8336798af94d591822a8002d2d5a95827854848c620da58dcc6b "
    "ROWSET_SHA256 98961c203962855aa7ebc7c31c4396b3ad231e166b71cf2a465e4fa474d6bc2d"
)

MUTATION_POLICY = (
    "Approved non-mutating Vanderbilt slice-2 live route-observation ledger. It fetches only bounded public "
    "official denominator and candidate-context route metadata from the nine approved request rows, records final "
    "URLs, hashes, booleans, and coarse signal counts, and stores no raw HTML, raw text, raw headings, raw anchor "
    "samples, raw candidate names, accepted people, training-state mutation, denominator closure, Vanderbilt school "
    "verification, URL rewrite, unsupported-label ingestion, enrichment/profile/contact/research-fact acceptance, "
    "or identity collapse."
)

NOT_APPROVED = [
    "person_ingestion",
    "parser_acceptance",
    "training_state_mutation",
    "denominator_closure",
    "vanderbilt_school_verification",
    "url_rewrite",
    "unsupported_label_ingestion",
    "profile_fact_acceptance",
    "contact_fact_acceptance",
    "research_fact_acceptance",
    "raw_dump_publication",
    "unique_person_identity_collapse",
]

FIELDS = [
    "observation_key",
    "approval_request_key",
    "request_order",
    "source_execution_plan_key",
    "gap_key",
    "program_key",
    "program_name",
    "program_type",
    "plan_lane",
    "route_role",
    "fetch_url",
    "fetch_status",
    "http_status",
    "final_url",
    "fetch_domain",
    "final_domain",
    "same_domain_final_url",
    "content_type",
    "elapsed_ms",
    "content_length",
    "content_sha256",
    "visible_text_length",
    "visible_text_sha256",
    "title_current_signal",
    "heading_current_signal",
    "heading_signal_count",
    "current_term_count",
    "resident_term_count",
    "fellow_term_count",
    "person_anchor_count",
    "roster_anchor_count",
    "candidate_route_signal",
    "recommended_next_packet",
    "web_fetch_approved_by_gbrain",
    "raw_dump_publication_allowed",
    "accepted_person_rows",
    "person_ingestion_allowed",
    "parser_acceptance_allowed",
    "denominator_closure_allowed",
    "school_verification_allowed",
    "url_rewrite_allowed",
    "identity_collapse_allowed",
    "mutation_policy",
    "evidence_json",
    "generated_at",
]

ROWSET_FIELDS = [
    field
    for field in FIELDS
    if field not in {"observation_key", "elapsed_ms", "evidence_json", "mutation_policy", "generated_at"}
]

SESSION_HEADERS = {
    "User-Agent": "redmank-vanderbilt-slice2-route-observation/0.1 (+https://github.com/Tshah-95/redmank)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.5",
}

CURRENT_RE = re.compile(r"\b(current|residents?|fellows?|trainees?|house\s*staff|pgy[-\s]?\d|2025|2026)\b", re.I)
RESIDENT_RE = re.compile(r"\b(residents?|residency|pgy[-\s]?\d)\b", re.I)
FELLOW_RE = re.compile(r"\b(fellows?|fellowship)\b", re.I)
WHITESPACE_RE = re.compile(r"\s+")

csv.field_size_limit(sys.maxsize)


class RouteHTMLParser(HTMLParser):
    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title_parts: list[str] = []
        self.heading_parts: list[tuple[str, list[str]]] = []
        self.anchor_parts: list[dict[str, str]] = []
        self.text_parts: list[str] = []
        self._tag_stack: list[str] = []
        self._active_anchor: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        self._tag_stack.append(tag)
        attr_map = {name.lower(): value or "" for name, value in attrs}
        if tag == "a" and attr_map.get("href"):
            self._active_anchor = {"text": "", "href": urljoin(self.base_url, attr_map["href"])}
            self.anchor_parts.append(self._active_anchor)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a":
            self._active_anchor = None
        for index in range(len(self._tag_stack) - 1, -1, -1):
            if self._tag_stack[index] == tag:
                del self._tag_stack[index:]
                break

    def handle_data(self, data: str) -> None:
        if any(tag in {"script", "style", "noscript", "svg"} for tag in self._tag_stack):
            return
        text = WHITESPACE_RE.sub(" ", data).strip()
        if not text:
            return
        self.text_parts.append(text)
        if "title" in self._tag_stack:
            self.title_parts.append(text)
        heading_tags = [tag for tag in self._tag_stack if tag in {"h1", "h2", "h3"}]
        if heading_tags:
            if not self.heading_parts or self.heading_parts[-1][0] != heading_tags[-1]:
                self.heading_parts.append((heading_tags[-1], []))
            self.heading_parts[-1][1].append(text)
        if self._active_anchor is not None:
            self._active_anchor["text"] = (self._active_anchor["text"] + " " + text).strip()

    @property
    def visible_text(self) -> str:
        return WHITESPACE_RE.sub(" ", " ".join(self.text_parts)).strip()

    @property
    def title(self) -> str:
        return WHITESPACE_RE.sub(" ", " ".join(self.title_parts)).strip()

    @property
    def headings(self) -> list[str]:
        return [WHITESPACE_RE.sub(" ", " ".join(parts)).strip() for _, parts in self.heading_parts if parts]

    @property
    def anchors(self) -> list[dict[str, str]]:
        return [{"text": anchor["text"], "href": anchor["href"]} for anchor in self.anchor_parts]


def dumps(value: object) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()


def stable_key(prefix: str, *parts: object) -> str:
    return prefix + "_" + sha256_text("|".join(str(part or "") for part in parts))[:20]


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FIELDS} for row in rows)


def domain(url: str) -> str:
    return urlparse(url or "").netloc.lower()


def int_value(value: object) -> int:
    try:
        return int(str(value or "0"))
    except ValueError:
        return 0


def verify_source_boundary() -> dict[str, object]:
    summary = read_json(SOURCE_SUMMARY)
    if not isinstance(summary, dict):
        raise SystemExit("Expected Vanderbilt slice-2 live-fetch approval request summary JSON object.")
    checks = {
        "source_rowset": summary.get("rowset_sha256") == SOURCE_ROWSET_SHA256,
        "source_plan_rowset": summary.get("source_execution_plan_rowset_sha256") == SOURCE_PLAN_ROWSET_SHA256,
        "approval_request_rows": summary.get("approval_request_rows") == 9,
        "source_plan_rows": summary.get("source_plan_rows") == 9,
        "web_fetch_allowed_false": summary.get("web_fetch_allowed") is False,
        "web_fetch_executed_false": summary.get("web_fetch_executed") is False,
        "future_web_fetch_requested_true": summary.get("future_web_fetch_requested") is True,
        "mutation_allowed_false": summary.get("mutation_allowed") is False,
        "person_ingestion_allowed_false": summary.get("person_ingestion_allowed") is False,
        "denominator_closure_allowed_false": summary.get("denominator_closure_allowed") is False,
        "school_verification_allowed_false": summary.get("school_verification_allowed") is False,
        "exact_approval_line_matches": summary.get("gbrain_exact_approval_line") == GBRAIN_APPROVAL_LINE,
    }
    if not all(checks.values()):
        raise SystemExit("Unexpected Vanderbilt slice-2 route observation source boundary: " + dumps(checks))
    return summary


def fetch(url: str) -> dict[str, object]:
    started = time.monotonic()
    try:
        request = Request(url, headers=SESSION_HEADERS)
        with urlopen(request, timeout=30) as response:
            content = response.read()
            final_url = response.geturl()
            status_code = response.status
            content_type = response.headers.get("content-type", "")
        elapsed_ms = int((time.monotonic() - started) * 1000)
    except HTTPError as exc:
        content = exc.read()
        final_url = exc.geturl()
        status_code = exc.code
        content_type = exc.headers.get("content-type", "")
        elapsed_ms = int((time.monotonic() - started) * 1000)
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "fetch_status": "fetch_error",
            "http_status": "",
            "final_url": "",
            "content_type": "",
            "elapsed_ms": int((time.monotonic() - started) * 1000),
            "content_length": 0,
            "content_sha256": "",
            "visible_text_length": 0,
            "visible_text_sha256": "",
            "title_current_signal": "false",
            "heading_current_signal": "false",
            "heading_signal_count": 0,
            "current_term_count": 0,
            "resident_term_count": 0,
            "fellow_term_count": 0,
            "person_anchor_count": 0,
            "roster_anchor_count": 0,
            "candidate_route_signal": "fetch_error_needs_retry_or_manual_review",
            "fetch_error": type(exc).__name__ + ": " + str(exc)[:220],
        }

    encoding = "utf-8"
    if "charset=" in content_type.lower():
        encoding = content_type.lower().split("charset=", 1)[1].split(";", 1)[0].strip() or "utf-8"
    html = content.decode(encoding, errors="replace")
    parser = RouteHTMLParser(final_url)
    parser.feed(html)
    text = parser.visible_text
    headings = parser.headings
    heading_signal_count = sum(1 for heading in headings if CURRENT_RE.search(heading))
    title_current_signal = bool(CURRENT_RE.search(parser.title))
    heading_current_signal = bool(heading_signal_count)
    anchors = parser.anchors
    person_anchor_count = sum(1 for anchor in anchors if "/person/" in anchor["href"])
    roster_anchor_count = sum(1 for anchor in anchors if CURRENT_RE.search(anchor["text"] + " " + anchor["href"]))
    current_term_count = len(CURRENT_RE.findall(text))
    resident_term_count = len(RESIDENT_RE.findall(text))
    fellow_term_count = len(FELLOW_RE.findall(text))

    if int(status_code) >= 400:
        route_signal = "http_error_needs_retry_or_recourse"
    elif heading_signal_count or person_anchor_count >= 3 or (current_term_count and (resident_term_count or fellow_term_count)):
        route_signal = "official_route_current_roster_signal_needs_parser_scope_packet"
    elif current_term_count or roster_anchor_count:
        route_signal = "official_route_context_signal_needs_scope_review"
    else:
        route_signal = "official_route_without_current_roster_signal_needs_recourse_review"

    return {
        "fetch_status": "fetched",
        "http_status": status_code,
        "final_url": final_url,
        "content_type": content_type[:140],
        "elapsed_ms": elapsed_ms,
        "content_length": len(content),
        "content_sha256": sha256_bytes(content),
        "visible_text_length": len(text),
        "visible_text_sha256": sha256_text(text),
        "title_current_signal": "true" if title_current_signal else "false",
        "heading_current_signal": "true" if heading_current_signal else "false",
        "heading_signal_count": heading_signal_count,
        "current_term_count": current_term_count,
        "resident_term_count": resident_term_count,
        "fellow_term_count": fellow_term_count,
        "person_anchor_count": person_anchor_count,
        "roster_anchor_count": roster_anchor_count,
        "candidate_route_signal": route_signal,
        "fetch_error": "",
    }


def route_rows(source_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for source in source_rows:
        for route_role, url_field in [
            ("denominator", "denominator_url"),
            ("candidate_context", "candidate_context_url"),
        ]:
            fetch_url = source.get(url_field, "")
            if not fetch_url:
                continue
            route = dict(source)
            route["route_role"] = route_role
            route["fetch_url"] = fetch_url
            rows.append(route)
    return rows


def recommended_next_packet(route_role: str, candidate_route_signal: str) -> str:
    if candidate_route_signal == "official_route_current_roster_signal_needs_parser_scope_packet":
        return "slice_2_route_parser_scope_approval_request_packet"
    if candidate_route_signal in {"http_error_needs_retry_or_recourse", "fetch_error_needs_retry_or_manual_review"}:
        return "slice_2_route_retry_or_recourse_packet"
    if route_role == "candidate_context":
        return "slice_2_related_scope_or_context_disposition_packet"
    return "slice_2_official_route_source_discovery_recourse_packet"


def rowset_sha256(rows: list[dict[str, object]]) -> str:
    material = [
        {field: row.get(field, "") for field in ROWSET_FIELDS}
        for row in sorted(rows, key=lambda item: str(item.get("observation_key", "")))
    ]
    return sha256_text(dumps(material))


def write_markdown(rows: list[dict[str, object]], summary: dict[str, object]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        "type: research-checkpoint",
        "title: Vanderbilt Slice 2 Live Route Observations",
        "created_at: " + str(summary["generated_at"]),
        "project: top-50-medical-school-roster-engine",
        "school: Vanderbilt University School of Medicine",
        "---",
        "",
        "# Vanderbilt Slice 2 Live Route Observations",
        "",
        "## Boundary",
        "",
        MUTATION_POLICY,
        "",
        "GBrain approval line used: `" + GBRAIN_APPROVAL_LINE + "`",
        "",
        "These observations are public-safe route metadata only. They do not accept parsers, people, denominators, state changes, URL rewrites, enrichment claims, or identity collapse.",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, ensure_ascii=True, indent=2, sort_keys=True),
        "```",
        "",
        "## Observation Rows",
        "",
        "| request | role | program | status | signal | http | final domain | current | resident | fellow | person links |",
        "| ---: | --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {request_order} | {route_role} | {program_name} | {fetch_status} | {candidate_route_signal} | {http_status} | {final_domain} | {current_term_count} | {resident_term_count} | {fellow_term_count} | {person_anchor_count} |".format(
                **row
            )
        )
    lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    source_summary = verify_source_boundary()
    source_rows = read_csv_rows(SOURCE_CSV)
    if len(source_rows) != 9:
        raise SystemExit("Expected 9 Vanderbilt slice-2 live-fetch approval request rows.")

    generated_at = datetime.now(timezone.utc).isoformat()
    source_route_rows = route_rows(source_rows)
    observations_by_url: dict[str, dict[str, object]] = {}
    for url in sorted({row["fetch_url"] for row in source_route_rows if row.get("fetch_url")}):
        observations_by_url[url] = fetch(url)

    rows: list[dict[str, object]] = []
    for source in source_route_rows:
        fetch_url = source["fetch_url"]
        observation = observations_by_url.get(fetch_url, {})
        final_url = str(observation.get("final_url") or "")
        route_signal = str(observation.get("candidate_route_signal") or "not_fetched")
        rows.append(
            {
                "observation_key": stable_key(
                    "vanderbilt_slice_2_live_route_observation",
                    source.get("approval_request_key"),
                    source.get("route_role"),
                    fetch_url,
                    final_url,
                ),
                "approval_request_key": source.get("approval_request_key", ""),
                "request_order": int_value(source.get("request_order")),
                "source_execution_plan_key": source.get("source_execution_plan_key", ""),
                "gap_key": source.get("gap_key", ""),
                "program_key": source.get("program_key", ""),
                "program_name": source.get("program_name", ""),
                "program_type": source.get("program_type", ""),
                "plan_lane": source.get("plan_lane", ""),
                "route_role": source.get("route_role", ""),
                "fetch_url": fetch_url,
                "fetch_status": observation.get("fetch_status", "not_fetched"),
                "http_status": observation.get("http_status", ""),
                "final_url": final_url,
                "fetch_domain": domain(fetch_url),
                "final_domain": domain(final_url),
                "same_domain_final_url": "true" if final_url and domain(fetch_url) == domain(final_url) else "false",
                "content_type": observation.get("content_type", ""),
                "elapsed_ms": observation.get("elapsed_ms", ""),
                "content_length": observation.get("content_length", 0),
                "content_sha256": observation.get("content_sha256", ""),
                "visible_text_length": observation.get("visible_text_length", 0),
                "visible_text_sha256": observation.get("visible_text_sha256", ""),
                "title_current_signal": observation.get("title_current_signal", "false"),
                "heading_current_signal": observation.get("heading_current_signal", "false"),
                "heading_signal_count": observation.get("heading_signal_count", 0),
                "current_term_count": observation.get("current_term_count", 0),
                "resident_term_count": observation.get("resident_term_count", 0),
                "fellow_term_count": observation.get("fellow_term_count", 0),
                "person_anchor_count": observation.get("person_anchor_count", 0),
                "roster_anchor_count": observation.get("roster_anchor_count", 0),
                "candidate_route_signal": route_signal,
                "recommended_next_packet": recommended_next_packet(str(source.get("route_role", "")), route_signal),
                "web_fetch_approved_by_gbrain": "true",
                "raw_dump_publication_allowed": "false",
                "accepted_person_rows": 0,
                "person_ingestion_allowed": "false",
                "parser_acceptance_allowed": "false",
                "denominator_closure_allowed": "false",
                "school_verification_allowed": "false",
                "url_rewrite_allowed": "false",
                "identity_collapse_allowed": "false",
                "mutation_policy": MUTATION_POLICY,
                "evidence_json": dumps(
                    {
                        "source_approval_request_rowset_sha256": SOURCE_ROWSET_SHA256,
                        "source_execution_plan_rowset_sha256": SOURCE_PLAN_ROWSET_SHA256,
                        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
                        "source_approval_request_status": source.get("approval_request_status"),
                        "route_role": source.get("route_role"),
                        "fetch_error": observation.get("fetch_error", ""),
                    }
                ),
                "generated_at": generated_at,
            }
        )

    rows.sort(key=lambda item: (int(item["request_order"]), str(item["route_role"]), str(item["fetch_url"])))
    by_fetch_status = Counter(str(row["fetch_status"]) for row in rows)
    by_signal = Counter(str(row["candidate_route_signal"]) for row in rows)
    by_role = Counter(str(row["route_role"]) for row in rows)
    by_domain = Counter(str(row["final_domain"] or row["fetch_domain"]) for row in rows)
    summary = {
        "generated_at": generated_at,
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "json": str(OUT_JSON.relative_to(ROOT)),
        "markdown": str(OUT_MD.relative_to(ROOT)),
        "source_approval_request_packet": str(SOURCE_CSV.relative_to(ROOT)),
        "source_approval_request_summary": str(SOURCE_SUMMARY.relative_to(ROOT)),
        "source_approval_request_rowset_sha256": SOURCE_ROWSET_SHA256,
        "source_execution_plan_rowset_sha256": SOURCE_PLAN_ROWSET_SHA256,
        "source_approval_request_rows": source_summary.get("approval_request_rows"),
        "observation_rows": len(rows),
        "request_rows_represented": len({str(row["approval_request_key"]) for row in rows}),
        "unique_observed_urls": len(observations_by_url),
        "by_route_role": dict(sorted(by_role.items())),
        "by_fetch_status": dict(sorted(by_fetch_status.items())),
        "by_candidate_route_signal": dict(sorted(by_signal.items())),
        "by_final_or_fetch_domain": dict(sorted(by_domain.items())),
        "gbrain_approval_status": "approved_exact_non_mutating_live_route_observation",
        "gbrain_approval_line": GBRAIN_APPROVAL_LINE,
        "web_fetch_executed": True,
        "web_fetch_approved_by_gbrain": True,
        "private_artifact_paths_committed": False,
        "raw_dump_publication_allowed": False,
        "mutation_allowed": False,
        "person_ingestion_allowed": False,
        "parser_acceptance_allowed": False,
        "denominator_closure_allowed": False,
        "school_verification_allowed": False,
        "url_rewrite_allowed": False,
        "identity_collapse_allowed": False,
        "accepted_person_rows": 0,
        "not_approved": NOT_APPROVED,
        "policy": MUTATION_POLICY,
        "public_safety_policy": (
            "This ledger stores fetch metadata, hashes, booleans, and coarse link/signal counts only. Do not commit "
            "raw HTML/text/browser dumps, raw candidate names, or accepted person records from this observation lane."
        ),
    }
    summary["rowset_sha256"] = rowset_sha256(rows)

    write_csv(OUT_CSV, rows)
    write_json(OUT_JSON, rows)
    write_json(OUT_SUMMARY, summary)
    write_markdown(rows, summary)
    print(
        json.dumps(
            {
                "observation_rows": summary["observation_rows"],
                "unique_observed_urls": summary["unique_observed_urls"],
                "rowset_sha256": summary["rowset_sha256"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
