#!/usr/bin/env python3
"""Search for historical public identity anchors for attending trend candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus, unquote, urlparse

DEPS_PATH = Path(os.environ.get("PENN_CORPUS_DEPS", "/tmp/penn_corpus_deps"))
if DEPS_PATH.exists():
    sys.path.insert(0, str(DEPS_PATH))

try:
    import requests
    from bs4 import BeautifulSoup
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing scraper dependency. Install with: "
        "python3 -m pip install --target /tmp/penn_corpus_deps -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
GROUPS_CSV = ARTIFACTS / "attending_trend_linkage_groups.csv"
DDG_HTML = "https://html.duckduckgo.com/html/"


HISTORICAL_TERMS = [
    "fellow",
    "fellowship",
    "resident",
    "residency",
    "alumni",
    "graduate",
    "graduates",
    "class of",
    "pgy",
]
PENN_TERMS = [
    "penn",
    "penn medicine",
    "university of pennsylvania",
    "hospital of the university of pennsylvania",
    "hup",
    "perelman",
]
PROFILE_TERMS = ["cv", "curriculum vitae", "profile", "bio", "biography", "qualifications", "education"]
CURRENT_PROFILE_PATH_RE = re.compile(
    r"/providers/profile/|/faculty|/leadership|/departments-and-centers/.+/(faculty|leadership)",
    re.I,
)
HISTORICAL_BRIDGE_RE = re.compile(
    r"\b(alumni|graduates?|former|class of|past fellows?|past residents?|current fellows?|current residents?|"
    r"fellows? and alumni|residents? and alumni|cv|curriculum vitae)\b|"
    r"/(alumni|graduates?|former|current-)?(fellows?|residents?)(/|\.html|$)|\.pdf($|\?)",
    re.I,
)


def norm(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def redact(text: str) -> str:
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[REDACTED_EMAIL]", text)


def normalized_name(value: str) -> str:
    value = norm(value).lower()
    value = re.sub(
        r"\b(md|m\.d\.|do|d\.o\.|phd|ph\.d\.|mbe|msce|mse?d|msc|m\.sc\.|mph|mba|ms|m\.s\.|ma|m\.a\.|facp|faahpm)\b",
        " ",
        value,
    )
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return norm(value)


def slug_key(prefix: str, value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:60]
    return f"{prefix}_{slug}_{digest}"


def load_groups(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def selected_groups(groups: list[dict], include_endpoints: bool, max_groups: int) -> list[dict]:
    selected = []
    for row in groups:
        if row.get("has_penn_training_claim") == "1":
            selected.append(row)
        elif include_endpoints and row.get("has_current_attending_endpoint") == "1":
            selected.append(row)
    selected = sorted(
        selected,
        key=lambda row: (
            -int(row.get("has_penn_training_claim") or 0),
            -int(row.get("best_trend_link_assurance_level") or 0),
            row.get("display_name", ""),
        ),
    )
    return selected[:max_groups]


def query_specs(row: dict) -> list[dict]:
    name = row["display_name"]
    plain = normalized_name(name)
    queries = [
        ("historical_penn_training", f'"{plain}" "University of Pennsylvania" fellowship'),
        ("historical_penn_training", f'"{plain}" "Penn" fellowship'),
        ("official_penn_profile", f'site:pennmedicine.org "{plain}"'),
        ("historical_penn_training", f'"{name}" "University of Pennsylvania" fellowship'),
        ("historical_penn_training", f'"{name}" "Penn" fellowship'),
        ("historical_penn_training", f'"{name}" "Penn Medicine" residency fellowship'),
        ("historical_roster_or_alumni", f'"{name}" Penn alumni fellow resident'),
        ("official_penn_profile", f'site:pennmedicine.org "{name}"'),
        ("upenn_profile_or_cv", f'site:upenn.edu "{name}" fellowship OR residency'),
    ]
    seen = set()
    deduped = []
    for kind, query in queries:
        if query not in seen:
            seen.add(query)
            deduped.append((kind, query))
    return [
        {
            "query_key": slug_key("attending_history_query", f"{row['event_group_key']}:{kind}:{query}"),
            "event_group_key": row["event_group_key"],
            "display_name": name,
            "normalized_name": row.get("normalized_name") or plain,
            "query_kind": kind,
            "query": query,
            "query_url": f"{DDG_HTML}?q={quote_plus(query)}",
        }
        for kind, query in deduped
    ]


def ddg_results(session: requests.Session, spec: dict, max_results: int) -> tuple[list[dict], dict]:
    fetched_at = datetime.now(timezone.utc).isoformat()
    response = session.get(DDG_HTML, params={"q": spec["query"]}, timeout=25)
    soup = BeautifulSoup(response.text, "lxml")
    results = []
    if response.status_code != 200:
        return [], {
            **spec,
            "searched_at": fetched_at,
            "search_http_status": response.status_code,
            "result_count": 0,
            "error": "search_endpoint_non_200",
        }
    for result in soup.select(".result")[:max_results]:
        link = result.select_one(".result__a")
        if not link:
            continue
        url = normalize_ddg_url(link.get("href", ""))
        title = redact(norm(link.get_text(" ")))
        snippet_node = result.select_one(".result__snippet")
        snippet = redact(norm(snippet_node.get_text(" ") if snippet_node else ""))
        if not url:
            continue
        results.append(
            {
                **spec,
                "result_url": url,
                "result_domain": urlparse(url).netloc.lower(),
                "result_title": title,
                "result_snippet": snippet,
                "search_status": "ok",
                "searched_at": fetched_at,
                "search_http_status": response.status_code,
            }
        )
    observation = {
        **spec,
        "searched_at": fetched_at,
        "search_http_status": response.status_code,
        "result_count": len(results),
        "error": "",
    }
    return results, observation


def seeded_group_sources(groups: list[dict]) -> list[dict]:
    rows = []
    for group in groups:
        urls = [url for url in (group.get("source_urls") or "").split("; ") if url]
        for url in urls:
            rows.append(
                {
                    "query_key": slug_key("attending_history_seed", f"{group['event_group_key']}:{url}"),
                    "event_group_key": group["event_group_key"],
                    "display_name": group["display_name"],
                    "normalized_name": group.get("normalized_name") or normalized_name(group["display_name"]),
                    "query_kind": "existing_linkage_source_url",
                    "query": "",
                    "query_url": "",
                    "result_url": url,
                    "result_domain": urlparse(url).netloc.lower(),
                    "result_title": "",
                    "result_snippet": "",
                    "search_status": "seeded_from_attending_trend_linkage_group",
                    "searched_at": "",
                    "search_http_status": "",
                }
            )
    return rows


def normalize_ddg_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("//duckduckgo.com/l/?"):
        parsed = urlparse("https:" + url)
        params = dict(item.split("=", 1) for item in parsed.query.split("&") if "=" in item)
        if "uddg" in params:
            return unquote(params["uddg"])
    return url


def page_probe(session: requests.Session, result: dict) -> dict:
    url = result["result_url"]
    fetched_at = datetime.now(timezone.utc).isoformat()
    probe = {
        "probe_http_status": "",
        "probe_content_type": "",
        "probe_title": "",
        "probe_text_length": 0,
        "probe_sha256": "",
        "probe_error": "",
        "probed_at": fetched_at,
        "page_term_hits": "",
    }
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        probe["probe_error"] = "non_http_url"
        return probe
    try:
        response = session.get(url, timeout=20, allow_redirects=True)
        probe["probe_http_status"] = response.status_code
        probe["probe_content_type"] = response.headers.get("content-type", "")
        probe["probe_sha256"] = hashlib.sha256(response.content).hexdigest()
        if "text/html" not in probe["probe_content_type"]:
            return probe
        soup = BeautifulSoup(response.text, "lxml")
        title = redact(norm(soup.title.get_text(" ") if soup.title else ""))
        text = redact(norm(soup.get_text(" ")))
        probe["probe_title"] = title
        probe["probe_text_length"] = len(text)
        probe["page_term_hits"] = "; ".join(term_hits(f"{title} {text[:5000]}"))
    except requests.RequestException as exc:
        probe["probe_error"] = f"{type(exc).__name__}: {str(exc)[:220]}"
    return probe


def term_hits(text: str) -> list[str]:
    low = text.lower()
    hits = []
    for existing in ["historical_training_term", "penn_term", "profile_term", "recent_or_dated_term"]:
        if existing in low:
            hits.append(existing)
    for label, terms in [
        ("historical_training_term", HISTORICAL_TERMS),
        ("penn_term", PENN_TERMS),
        ("profile_term", PROFILE_TERMS),
    ]:
        if any(term in low for term in terms):
            hits.append(label)
    if re.search(r"\b20(0[0-9]|1[0-9]|2[0-6])\b", low):
        hits.append("recent_or_dated_term")
    return hits


def source_surface(row: dict, haystack: str) -> str:
    url = row.get("result_url", "")
    query_kind = row.get("query_kind", "")
    if query_kind == "existing_linkage_source_url" and CURRENT_PROFILE_PATH_RE.search(url):
        return "current_profile_or_faculty_context"
    if HISTORICAL_BRIDGE_RE.search(f"{url} {haystack}"):
        if re.search(r"\bcv|curriculum vitae\b|\.pdf($|\?)", f"{url} {haystack}", re.I):
            return "profile_or_cv_bridge_candidate"
        return "historical_roster_or_alumni_bridge_candidate"
    if CURRENT_PROFILE_PATH_RE.search(url):
        return "current_profile_or_faculty_context"
    return "general_search_context"


def name_hit(row: dict, haystack: str) -> bool:
    name = normalized_name(row.get("display_name", ""))
    if not name:
        return False
    compact_haystack = normalized_name(haystack)
    tokens = [token for token in name.split() if len(token) > 1]
    return bool(tokens) and all(token in compact_haystack for token in tokens)


def classify_result(row: dict) -> tuple[str, float, list[str], str]:
    haystack = " ".join(
        [
            row.get("result_title", ""),
            row.get("result_snippet", ""),
            row.get("probe_title", ""),
            row.get("page_term_hits", ""),
            row.get("result_url", ""),
        ]
    ).lower()
    hits = term_hits(haystack)
    reasons = list(hits)
    domain = row.get("result_domain", "")
    surface = source_surface(row, haystack)
    if surface:
        reasons.append(surface)
    has_name_hit = name_hit(row, haystack + " " + row.get("result_url", ""))
    if has_name_hit:
        reasons.append("name_present")
    score = 0.1
    status = "low_signal_search_result"
    if has_name_hit:
        score += 0.2
    if "penn_term" in hits:
        score += 0.25
    if "historical_training_term" in hits:
        score += 0.25
    if "recent_or_dated_term" in hits:
        score += 0.15
    if "profile_term" in hits:
        score += 0.1
    if domain.endswith("pennmedicine.org") or domain.endswith("upenn.edu"):
        score += 0.15
        reasons.append("official_or_penn_domain")
    if row.get("query_kind") in {"historical_penn_training", "historical_roster_or_alumni"}:
        score += 0.05
    if surface == "historical_roster_or_alumni_bridge_candidate" and has_name_hit and "penn_term" in hits:
        status = "historical_roster_or_alumni_candidate"
        score += 0.2
    elif surface == "profile_or_cv_bridge_candidate" and has_name_hit and ("penn_term" in hits or "historical_training_term" in hits):
        status = "profile_or_cv_bridge_candidate"
        score += 0.15
    elif surface == "current_profile_or_faculty_context" and "penn_term" in hits:
        if has_name_hit and "historical_training_term" in hits:
            status = "current_profile_training_context_candidate"
            score = min(score, 0.78)
        else:
            status = "current_profile_context_candidate"
            score = min(score, 0.65 if has_name_hit else 0.55)
    elif "penn_term" in hits and "historical_training_term" in hits and has_name_hit:
        status = "historical_training_search_candidate"
    elif "penn_term" in hits and "profile_term" in hits and has_name_hit:
        status = "profile_identity_anchor_candidate"
    elif domain.endswith("pennmedicine.org") or domain.endswith("upenn.edu"):
        status = "penn_context_candidate"
        score = min(score, 0.55 if not has_name_hit else 0.7)
    confidence = round(min(score, 0.95), 3)
    required = "Review page text for explicit same-person, Penn-training, program, and date anchors before accepting trend link."
    if status in {"current_profile_training_context_candidate", "current_profile_context_candidate"}:
        required = "Use as current profile/training context only; still requires dated historical roster, alumni, CV, or independent profile bridge for trend acceptance."
    if status == "low_signal_search_result":
        required = "Keep only as discovery context unless another source supplies Penn-training or identity anchors."
    return status, confidence, sorted(set(reasons)), required


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = fieldnames or (list(rows[0].keys()) if rows else [])
    if not rows:
        if not fieldnames:
            path.write_text("", encoding="utf-8")
            return
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-groups", type=int, default=12)
    parser.add_argument("--max-results", type=int, default=6)
    parser.add_argument("--include-endpoints", action="store_true")
    parser.add_argument("--probe-pages", action="store_true")
    parser.add_argument("--skip-search", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.25)
    args = parser.parse_args()

    session = requests.Session()
    session.headers["User-Agent"] = "redmank-attending-historical-link-discovery/0.1"
    groups = selected_groups(load_groups(GROUPS_CSV), args.include_endpoints, args.max_groups)
    query_rows = [spec for group in groups for spec in query_specs(group)]
    observations = []
    candidates = {}
    seeded_rows = seeded_group_sources(groups)
    for result in seeded_rows:
        if args.probe_pages:
            result.update(page_probe(session, result))
            time.sleep(args.sleep)
        else:
            result.update(
                {
                    "probe_http_status": "",
                    "probe_content_type": "",
                    "probe_title": "",
                    "probe_text_length": 0,
                    "probe_sha256": "",
                    "probe_error": "",
                    "probed_at": "",
                    "page_term_hits": "",
                }
            )
        status, confidence, reasons, required = classify_result(result)
        result.update(
            {
                "candidate_key": slug_key("attending_history_candidate", f"{result['event_group_key']}:{result['result_url']}"),
                "candidate_status": status,
                "confidence": confidence,
                "priority": int(round(confidence * 100))
                + (25 if status in {"historical_roster_or_alumni_candidate", "profile_or_cv_bridge_candidate"} else 0),
                "classification_reasons": "; ".join(reasons + ["seeded_from_existing_linkage_group"]),
                "required_next_evidence": required,
            }
        )
        candidates[result["candidate_key"]] = result
    for spec in [] if args.skip_search else query_rows:
        try:
            results, observation = ddg_results(session, spec, args.max_results)
        except requests.RequestException as exc:
            results = []
            observation = {**spec, "searched_at": datetime.now(timezone.utc).isoformat(), "search_http_status": 0, "result_count": 0, "error": f"{type(exc).__name__}: {str(exc)[:220]}"}
        observations.append(observation)
        for result in results:
            if args.probe_pages:
                result.update(page_probe(session, result))
                time.sleep(args.sleep)
            else:
                result.update(
                    {
                        "probe_http_status": "",
                        "probe_content_type": "",
                        "probe_title": "",
                        "probe_text_length": 0,
                        "probe_sha256": "",
                        "probe_error": "",
                        "probed_at": "",
                        "page_term_hits": "",
                    }
                )
            status, confidence, reasons, required = classify_result(result)
            result.update(
                {
                    "candidate_key": slug_key("attending_history_candidate", f"{result['event_group_key']}:{result['result_url']}"),
                    "candidate_status": status,
                    "confidence": confidence,
                    "priority": int(round(confidence * 100))
                    + (25 if status in {"historical_roster_or_alumni_candidate", "profile_or_cv_bridge_candidate"} else 0),
                    "classification_reasons": "; ".join(reasons),
                    "required_next_evidence": required,
                }
            )
            current = candidates.get(result["candidate_key"])
            if not current or int(result["priority"]) > int(current["priority"]):
                candidates[result["candidate_key"]] = result
        time.sleep(args.sleep)

    candidate_rows = sorted(
        candidates.values(),
        key=lambda row: (-int(row["priority"]), row["display_name"], row["result_domain"], row["result_title"]),
    )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "groups_considered": len(groups),
        "query_rows": len(query_rows),
        "search_observations": len(observations),
        "search_skipped": args.skip_search,
        "seeded_source_rows": len(seeded_rows),
        "candidate_rows": len(candidate_rows),
        "by_candidate_status": dict(sorted(Counter(row["candidate_status"] for row in candidate_rows).items())),
        "by_query_kind": dict(sorted(Counter(row["query_kind"] for row in query_rows).items())),
        "by_search_http_status": dict(sorted(Counter(str(row.get("search_http_status", "")) for row in observations).items())),
        "by_search_error": dict(sorted(Counter(row.get("error", "") for row in observations if row.get("error")).items())),
        "by_result_domain": dict(sorted(Counter(row["result_domain"] for row in candidate_rows).most_common(25))),
        "searched_group_keys": [row["event_group_key"] for row in groups],
        "candidate_csv": "artifacts/data/attending_historical_link_candidates.csv",
        "query_csv": "artifacts/data/attending_historical_link_search_queries.csv",
        "observation_csv": "artifacts/data/attending_historical_link_search_observations.csv",
    }
    observation_fields = list(query_rows[0].keys()) + ["searched_at", "search_http_status", "result_count", "error"]
    write_csv(ARTIFACTS / "attending_historical_link_search_queries.csv", query_rows)
    write_csv(ARTIFACTS / "attending_historical_link_search_observations.csv", observations, observation_fields)
    write_csv(ARTIFACTS / "attending_historical_link_candidates.csv", candidate_rows)
    (ARTIFACTS / "attending_historical_link_discovery_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
