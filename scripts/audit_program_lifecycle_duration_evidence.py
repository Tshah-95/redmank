#!/usr/bin/env python3
"""Collect official-page duration evidence for lifecycle-rule review.

This audit is intentionally non-mutating. It targets accepted ACGME-linked
program rows whose current roster states still use default/unknown lifecycle
rules, then captures explicit duration language from the official program page
when Penn publishes it.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

OBSERVATION_CSV = ARTIFACTS / "program_lifecycle_duration_source_observations.csv"
EVIDENCE_CSV = ARTIFACTS / "program_lifecycle_duration_evidence.csv"
EVIDENCE_JSON = ARTIFACTS / "program_lifecycle_duration_evidence.json"
SUMMARY_JSON = ARTIFACTS / "program_lifecycle_duration_evidence_summary.json"

USER_AGENT = "Mozilla/5.0 redmank-public-source-research/1.0"
TIMEOUT_SECONDS = 20

csv.field_size_limit(sys.maxsize)

NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
}

DURATION_PATTERN = re.compile(
    r"""
    (?P<phrase>
      (?:
        (?P<word>one|two|three|four|five|six|seven)
        |
        (?P<num>[1-7])
      )
      \s*(?:-| )
      year
      (?:
        \s+
        (?:
          ACGME[- ]accredited\s+
          |
          accredited\s+
          |
          clinical\s+
          |
          training\s+
        ){0,3}
        (?:
          fellowship
          |
          residency
          |
          program
          |
          clinical\s+training\s+program
          |
          training
        )
      )?
    )
    |
    (?P<duration_clause>
      duration\s+of\s+the\s+
      (?:
        fellowship
        |
        residency
        |
        program
      )
      \s+is\s+
      (?:
        (?P<duration_word>one|two|three|four|five|six|seven)
        |
        (?P<duration_num>[1-7])
      )
      \s+year
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

NEGATIVE_CONTEXT = re.compile(
    r"\b(prior|before|prerequisite|background|completed at least|minimum|applications?|timeline|match)\b",
    re.IGNORECASE,
)
POSITIVE_CONTEXT = re.compile(
    r"\b(duration|fellowship|residency|program|training|ACGME|clinical training)\b",
    re.IGNORECASE,
)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def key_for(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48]
    return f"{prefix}_{slug}_{digest}" if slug else f"{prefix}_{digest}"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def norm_space(value: str | None) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def norm_tokens(value: str | None) -> set[str]:
    text = norm_space(value).lower()
    text = text.replace("orthopaedic", "orthopedic")
    text = text.replace("maternal-fetal", "maternal fetal")
    text = text.replace("pathology-anatomic", "pathology anatomic")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\b(fellowship|residency|program|acgme|accredited|multidisciplinary|obgyn)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return {token for token in text.split() if len(token) > 2}


def load_json(value: str | None):
    if not value:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def official_program_url(row: dict) -> str:
    evidence = load_json(row.get("evidence_json")) or {}
    reconciliation = ((evidence.get("identifier") or {}).get("reconciliation_evidence")) or {}
    candidate = reconciliation.get("candidate_evidence") or {}
    return norm_space(candidate.get("official_program_url") or "")


def html_title_and_text(markup: str) -> tuple[str, str]:
    title_match = re.search(r"<title[^>]*>(.*?)</title>", markup, flags=re.IGNORECASE | re.DOTALL)
    title = html.unescape(norm_space(re.sub(r"<[^>]+>", " ", title_match.group(1)))) if title_match else ""
    cleaned = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", markup, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<!--.*?-->", " ", cleaned, flags=re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return title, html.unescape(norm_space(cleaned))


def read_targets(conn: sqlite3.Connection, all_accepted: bool) -> list[dict]:
    conn.row_factory = sqlite3.Row
    where = ""
    if not all_accepted:
        where = "WHERE a.lifecycle_status = 'accepted_identifier_with_default_or_unknown_lifecycle'"
    rows = []
    for row in conn.execute(
        f"""
        SELECT
          a.audit_key,
          a.official_program_key,
          a.matched_program_key,
          a.identifier_key,
          a.official_program_type,
          a.official_program_name,
          a.matched_program_name,
          a.identifier_value,
          a.source_program_specialty,
          a.lifecycle_status,
          a.evidence_json,
          i.source_url AS identifier_source_url
        FROM program_lifecycle_consistency_audit a
        LEFT JOIN official_program_identifiers i
          ON i.identifier_key = a.identifier_key
        {where}
        ORDER BY a.official_program_type, a.official_program_name
        """
    ):
        item = dict(row)
        item["official_program_url"] = official_program_url(item)
        rows.append(item)
    return rows


def fetch_page(url: str) -> dict:
    if not url:
        return {
            "source_status": "missing_official_program_url",
            "effective_url": "",
            "http_status": None,
            "page_title": "",
            "text": "",
            "error_text": "Accepted identifier evidence did not include an official program URL.",
        }
    try:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            body = response.read()
            html = body.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
            effective_url = response.geturl()
            http_status = response.status
        title, text = html_title_and_text(html)
        status = "ok" if 200 <= http_status < 300 else "http_error"
        return {
            "source_status": status,
            "effective_url": effective_url,
            "http_status": http_status,
            "page_title": title,
            "text": text,
            "error_text": "" if status == "ok" else f"HTTP {http_status}",
        }
    except HTTPError as exc:
        html = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        title, text = html_title_and_text(html)
        return {
            "source_status": "http_error",
            "effective_url": exc.geturl() or "",
            "http_status": exc.code,
            "page_title": title,
            "text": text,
            "error_text": f"HTTPError: {exc}",
        }
    except (URLError, TimeoutError, OSError) as exc:
        return {
            "source_status": "fetch_error",
            "effective_url": "",
            "http_status": None,
            "page_title": "",
            "text": "",
            "error_text": f"{type(exc).__name__}: {exc}",
        }


def duration_years(match: re.Match) -> int | None:
    for group in ["num", "duration_num"]:
        value = match.groupdict().get(group)
        if value:
            return int(value)
    for group in ["word", "duration_word"]:
        value = (match.groupdict().get(group) or "").lower()
        if value:
            return NUMBER_WORDS.get(value)
    return None


def duration_phrase(match: re.Match) -> str:
    return norm_space(match.groupdict().get("duration_clause") or match.groupdict().get("phrase") or match.group(0))


def find_duration_mentions(text: str) -> list[dict]:
    mentions = []
    for match in DURATION_PATTERN.finditer(text):
        years = duration_years(match)
        if not years:
            continue
        start, end = match.span()
        context = norm_space(text[max(0, start - 220) : min(len(text), end + 260)])
        phrase = duration_phrase(match)
        positive = bool(POSITIVE_CONTEXT.search(context))
        negative = bool(NEGATIVE_CONTEXT.search(context)) and "duration of the" not in phrase.lower()
        mentions.append(
            {
                "years": years,
                "phrase": phrase,
                "context": context,
                "positive_context": positive,
                "negative_context": negative,
            }
        )
    return mentions


def page_matches_program(row: dict, page_title: str, text: str) -> tuple[bool, list[str]]:
    haystack = f"{page_title} {text[:3000]}"
    haystack_tokens = norm_tokens(haystack)
    title_tokens = norm_tokens(page_title)
    official_tokens = norm_tokens(row.get("official_program_name"))
    specialty_tokens = norm_tokens(row.get("source_program_specialty"))
    reasons = []
    official_overlap = len(official_tokens & haystack_tokens) / max(1, len(official_tokens))
    specialty_overlap = len(specialty_tokens & haystack_tokens) / max(1, len(specialty_tokens))
    title_official_overlap = len(official_tokens & title_tokens) / max(1, len(official_tokens))
    title_specialty_overlap = len(specialty_tokens & title_tokens) / max(1, len(specialty_tokens))
    title_names_training_page = bool(re.search(r"\b(fellowship|residency|program)\b", page_title, re.IGNORECASE))
    if title_names_training_page and max(title_official_overlap, title_specialty_overlap) < 0.5:
        reasons.append("page_title_names_different_training_program")
        if official_overlap >= 0.55:
            reasons.append("official_program_name_only_supported_outside_title")
        if specialty_overlap >= 0.55:
            reasons.append("acgme_specialty_only_supported_outside_title")
        return False, reasons
    if official_overlap >= 0.55:
        reasons.append("official_program_name_supported_by_page_text")
    if specialty_overlap >= 0.55:
        reasons.append("acgme_specialty_supported_by_page_text")
    if "penn" in haystack.lower() or "university of pennsylvania" in haystack.lower():
        reasons.append("penn_context_present")
    return bool((official_overlap >= 0.55 or specialty_overlap >= 0.55) and reasons), reasons


def classify_duration(row: dict, observation: dict, mentions: list[dict]) -> tuple[str, str, float, list[str], dict | None]:
    if observation["source_status"] in {"missing_official_program_url", "fetch_error", "http_error"}:
        return (
            "duration_source_unavailable",
            "find_current_official_program_page_before_lifecycle_rule_review",
            0.1,
            [observation["source_status"]],
            None,
        )
    page_match, page_reasons = page_matches_program(row, observation.get("page_title") or "", observation.get("text") or "")
    usable_mentions = [item for item in mentions if item["positive_context"] and not item["negative_context"]]
    years = sorted({item["years"] for item in usable_mentions})
    reasons = list(page_reasons)
    if not page_match:
        reasons.append("official_page_program_context_not_confirmed")
    if not usable_mentions:
        return (
            "no_explicit_duration_evidence_found",
            "keep_default_lifecycle_rule_until_explicit_duration_source_is_found",
            0.28 if page_match else 0.18,
            reasons or ["no_supported_duration_phrase"],
            None,
        )
    best = usable_mentions[0]
    if len(years) > 1:
        reasons.extend(["multiple_duration_values_found", "manual_duration_review_required"])
        return (
            "conflicting_duration_evidence_review",
            "review_context_before_proposing_lifecycle_rule_change",
            0.46 if page_match else 0.32,
            reasons,
            best,
        )
    if not page_match:
        reasons.append("duration_phrase_on_unconfirmed_program_page")
        return (
            "duration_source_program_mismatch_review",
            "verify_official_page_scope_before_lifecycle_rule_change",
            0.42,
            reasons,
            best,
        )
    reasons.extend(["single_explicit_duration_value", "official_page_context_confirmed"])
    return (
        "reviewer_ready_duration_lifecycle_candidate",
        "review_duration_evidence_then_add_specific_lifecycle_rule_if_program_scope_matches",
        0.78,
        reasons,
        best,
    )


def observation_row(row: dict, page: dict, mentions: list[dict], observed_at: str) -> dict:
    years = sorted({item["years"] for item in mentions})
    source_url = row.get("official_program_url") or ""
    basis = f"{row['audit_key']}:{source_url}:{page.get('http_status')}:{sha256_text(page.get('text') or '')[:16]}"
    return {
        "observation_key": key_for("program_lifecycle_duration_observation", basis),
        "audit_key": row["audit_key"],
        "official_program_key": row["official_program_key"],
        "official_program_name": row["official_program_name"],
        "identifier_value": row.get("identifier_value") or "",
        "source_program_specialty": row.get("source_program_specialty") or "",
        "source_url": source_url,
        "effective_url": page.get("effective_url") or "",
        "http_status": page.get("http_status"),
        "page_title": page.get("page_title") or "",
        "page_text_sha256": sha256_text(page.get("text") or "") if page.get("text") else "",
        "text_length": len(page.get("text") or ""),
        "duration_phrase_count": len(mentions),
        "explicit_duration_years_json": dumps(years),
        "source_status": page["source_status"],
        "error_text": page.get("error_text") or "",
        "evidence_json": dumps({"duration_mentions": mentions, "identifier_source_url": row.get("identifier_source_url") or ""}),
        "observed_at": observed_at,
    }


def evidence_row(row: dict, observation: dict, page: dict, mentions: list[dict], observed_at: str) -> dict:
    status, action, confidence, reasons, best = classify_duration(row, page, mentions)
    duration_year = best["years"] if best else None
    phrase = best["phrase"] if best else ""
    context = best["context"] if best else ""
    basis = f"{row['audit_key']}:{observation['observation_key']}:{status}:{duration_year or ''}"
    return {
        "duration_evidence_key": key_for("program_lifecycle_duration_evidence", basis),
        "observation_key": observation["observation_key"],
        "audit_key": row["audit_key"],
        "official_program_key": row["official_program_key"],
        "matched_program_key": row.get("matched_program_key") or "",
        "identifier_key": row.get("identifier_key") or "",
        "official_program_type": row["official_program_type"],
        "official_program_name": row["official_program_name"],
        "matched_program_name": row.get("matched_program_name") or "",
        "identifier_value": row.get("identifier_value") or "",
        "source_program_specialty": row.get("source_program_specialty") or "",
        "lifecycle_status": row["lifecycle_status"],
        "source_url": observation["source_url"],
        "http_status": observation.get("http_status"),
        "page_title": observation.get("page_title") or "",
        "explicit_duration_years": duration_year,
        "duration_phrase": phrase,
        "duration_context": context,
        "duration_evidence_status": status,
        "recommended_action": action,
        "confidence": confidence,
        "match_reasons_json": dumps(reasons),
        "evidence_json": dumps(
            {
                "all_duration_mentions": mentions,
                "source_observation": {
                    "source_status": observation["source_status"],
                    "effective_url": observation["effective_url"],
                    "page_text_sha256": observation["page_text_sha256"],
                    "duration_phrase_count": observation["duration_phrase_count"],
                },
                "identifier_source_url": row.get("identifier_source_url") or "",
                "policy": "Duration evidence is a review candidate only; lifecycle rules and person states are not mutated by this audit.",
            }
        ),
        "observed_at": observed_at,
    }


def collect(rows: list[dict], observed_at: str, sleep: float) -> tuple[list[dict], list[dict]]:
    observations = []
    evidence = []
    import time

    for idx, row in enumerate(rows):
        page = fetch_page(row.get("official_program_url") or "")
        mentions = find_duration_mentions(page.get("text") or "")
        obs = observation_row(row, page, mentions, observed_at)
        observations.append(obs)
        evidence.append(evidence_row(row, obs, page, mentions, observed_at))
        if sleep and idx < len(rows) - 1:
            time.sleep(sleep)
    return observations, evidence


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, observations: list[dict], evidence: list[dict]) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM program_lifecycle_duration_evidence")
    conn.execute("DELETE FROM program_lifecycle_duration_source_observations")
    conn.executemany(
        """
        INSERT INTO program_lifecycle_duration_source_observations
        (observation_key, audit_key, official_program_key, official_program_name,
         identifier_value, source_program_specialty, source_url, effective_url,
         http_status, page_title, page_text_sha256, text_length, duration_phrase_count,
         explicit_duration_years_json, source_status, error_text, evidence_json, observed_at)
        VALUES
        (:observation_key, :audit_key, :official_program_key, :official_program_name,
         :identifier_value, :source_program_specialty, :source_url, :effective_url,
         :http_status, :page_title, :page_text_sha256, :text_length, :duration_phrase_count,
         :explicit_duration_years_json, :source_status, :error_text, :evidence_json, :observed_at)
        """,
        observations,
    )
    prepared = []
    for row in evidence:
        db_row = dict(row)
        for nullable in ["matched_program_key", "identifier_key", "explicit_duration_years", "http_status"]:
            if db_row.get(nullable) == "":
                db_row[nullable] = None
        prepared.append(db_row)
    conn.executemany(
        """
        INSERT INTO program_lifecycle_duration_evidence
        (duration_evidence_key, observation_key, audit_key, official_program_key,
         matched_program_key, identifier_key, official_program_type, official_program_name,
         matched_program_name, identifier_value, source_program_specialty, lifecycle_status,
         source_url, http_status, page_title, explicit_duration_years, duration_phrase,
         duration_context, duration_evidence_status, recommended_action, confidence,
         match_reasons_json, evidence_json, observed_at)
        VALUES
        (:duration_evidence_key, :observation_key, :audit_key, :official_program_key,
         :matched_program_key, :identifier_key, :official_program_type, :official_program_name,
         :matched_program_name, :identifier_value, :source_program_specialty, :lifecycle_status,
         :source_url, :http_status, :page_title, :explicit_duration_years, :duration_phrase,
         :duration_context, :duration_evidence_status, :recommended_action, :confidence,
         :match_reasons_json, :evidence_json, :observed_at)
        """,
        prepared,
    )
    conn.commit()


def write_outputs(observations: list[dict], evidence: list[dict], observed_at: str, all_accepted: bool) -> dict:
    write_csv(OBSERVATION_CSV, observations)
    write_csv(EVIDENCE_CSV, evidence)
    EVIDENCE_JSON.write_text(dumps(evidence) + "\n", encoding="utf-8")
    status_counts = Counter(row["duration_evidence_status"] for row in evidence)
    action_counts = Counter(row["recommended_action"] for row in evidence)
    source_counts = Counter(row["source_status"] for row in observations)
    duration_counts = Counter(str(row["explicit_duration_years"] or "none") for row in evidence)
    summary = {
        "observed_at": observed_at,
        "target_scope": "all_accepted_program_identifiers" if all_accepted else "accepted_identifier_with_default_or_unknown_lifecycle",
        "target_rows": len(evidence),
        "observation_rows": len(observations),
        "reviewer_ready_duration_candidates": status_counts.get("reviewer_ready_duration_lifecycle_candidate", 0),
        "source_unavailable_rows": status_counts.get("duration_source_unavailable", 0),
        "source_mismatch_review_rows": status_counts.get("duration_source_program_mismatch_review", 0),
        "conflicting_duration_review_rows": status_counts.get("conflicting_duration_evidence_review", 0),
        "no_explicit_duration_rows": status_counts.get("no_explicit_duration_evidence_found", 0),
        "by_duration_evidence_status": dict(sorted(status_counts.items())),
        "by_recommended_action": dict(sorted(action_counts.items())),
        "by_source_status": dict(sorted(source_counts.items())),
        "by_explicit_duration_years": dict(sorted(duration_counts.items())),
        "observation_csv": "artifacts/data/program_lifecycle_duration_source_observations.csv",
        "evidence_csv": "artifacts/data/program_lifecycle_duration_evidence.csv",
        "evidence_json": "artifacts/data/program_lifecycle_duration_evidence.json",
        "policy": "Non-mutating evidence audit. Explicit duration rows are reviewer-ready lifecycle-rule candidates, not accepted lifecycle changes.",
    }
    SUMMARY_JSON.write_text(dumps(summary) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB))
    parser.add_argument("--all-accepted", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.05)
    args = parser.parse_args()

    observed_at = now_utc()
    conn = sqlite3.connect(args.db)
    targets = read_targets(conn, args.all_accepted)
    observations, evidence = collect(targets, observed_at, args.sleep)
    write_db(conn, observations, evidence)
    conn.close()
    print(dumps(write_outputs(observations, evidence, observed_at, args.all_accepted)))


if __name__ == "__main__":
    main()
