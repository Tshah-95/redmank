#!/usr/bin/env python3
"""Collect source-backed ACGME program identifier candidates for Penn GME rows.

The ACGME public program search is treated as an identifier source, not a
roster source. Rows here can corroborate program identity and lifecycle
assumptions, but they do not mutate trainee membership.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from html.parser import HTMLParser
from http.cookiejar import CookieJar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "data"
DB = ARTIFACTS / "redmank.sqlite"
SCHEMA = ROOT / "db" / "schema.sql"

ACGME_SEARCH_URL = "https://apps.acgme.org/ads/Public/Programs/Search"
USER_AGENT = "Mozilla/5.0 redmank-public-source-research/1.0"

CSV_PATH = ARTIFACTS / "program_identifier_candidates.csv"
JSON_PATH = ARTIFACTS / "program_identifier_candidates.json"
OBSERVATION_PATH = ARTIFACTS / "program_identifier_source_observations.csv"
SUMMARY_PATH = ARTIFACTS / "program_identifier_candidate_summary.json"

BASE_RESIDENCY_SPECIALTIES = {
    "anesthesiology",
    "dermatology",
    "emergency medicine",
    "family medicine",
    "internal medicine",
    "internal medicine pediatrics",
    "medical genetics and genomics",
    "neurological surgery",
    "neurology",
    "obstetrics and gynecology",
    "occupational and environmental medicine",
    "ophthalmology",
    "orthopedic surgery",
    "otolaryngology head and neck surgery",
    "pathology anatomic and clinical",
    "physical medicine and rehabilitation",
    "plastic surgery integrated",
    "psychiatry",
    "radiation oncology",
    "radiology diagnostic",
    "surgery",
    "thoracic surgery integrated",
    "urology",
    "vascular surgery integrated",
    "interventional radiology integrated",
    "interventional radiology independent",
}

SPECIALTY_ALIASES = {
    "abdominal radiology": {"abdominal radiology", "abdominal imaging"},
    "adult reconstructive orthopedics": {"adult reconstructive orthopaedics"},
    "addiction medicine": {"addiction medicine multidisciplinary"},
    "endocrinology": {"endocrinology diabetes and metabolism"},
    "hematology and oncology": {"hematology and medical oncology"},
    "maternal fetal medicine": {"maternal fetal medicine"},
    "orthopedic surgery": {"orthopaedic surgery"},
    "otorhinolaryngology": {"otolaryngology head and neck surgery"},
    "pathology anatomic and clinical": {"pathology anatomic and clinical"},
    "radiology diagnostic": {"radiology diagnostic"},
    "radiology interventional independent": {"interventional radiology independent"},
    "radiology interventional integrated": {"interventional radiology integrated"},
    "general surgery": {"surgery"},
    "trauma and surgical critical care": {"surgical critical care"},
    "plastic surgery": {"plastic surgery", "plastic surgery integrated"},
    "vascular surgery integrated": {"vascular surgery integrated"},
    "thoracic surgery integrated": {"thoracic surgery integrated"},
    "thoracic surgery cardiac track": {"thoracic surgery independent"},
    "thoracic surgery thoracic track": {"thoracic surgery independent"},
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def dumps(value) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def key_for(prefix: str, value: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:48]
    return f"{prefix}_{slug}_{digest}" if slug else f"{prefix}_{digest}"


def norm_space(value: str | None) -> str:
    return " ".join((value or "").replace("\xa0", " ").split())


def norm_name(value: str | None) -> str:
    text = norm_space(value).lower()
    text = text.replace("&", " and ")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = text.replace("orthopaedic", "orthopedic")
    text = text.replace("diagnostic radiology", "radiology diagnostic")
    text = text.replace("radiology - diagnostic", "radiology diagnostic")
    text = text.replace("radiology - interventional", "radiology interventional")
    text = text.replace("maternal-fetal", "maternal fetal")
    text = text.replace("pathology-anatomic", "pathology anatomic")
    text = text.replace("otolaryngology - head and neck surgery", "otolaryngology head and neck surgery")
    text = re.sub(r"\b(fellowship|residency|program|hup|categorical)\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return norm_space(text)


def role_for_acgme_specialty(specialty: str) -> str:
    normalized = norm_name(specialty)
    return "resident" if normalized in BASE_RESIDENCY_SPECIALTIES else "fellow"


def is_penn_affiliated_acgme_row(program_name: str) -> bool:
    name = program_name.lower()
    if "penn state" in name or "penn highlands" in name:
        return False
    return any(
        marker in name
        for marker in [
            "university of pennsylvania",
            "pennsylvania hospital of the university of pennsylvania",
            "presbyterian medical center of the university of pennsylvania",
            "children's hospital of philadelphia",
        ]
    )


def institution_reasons(program_name: str) -> tuple[float, list[str]]:
    name = program_name.lower()
    reasons = []
    if "penn state" in name or "penn highlands" in name:
        return 0.0, ["excluded_non_penn_state_or_penn_highlands"]
    if "university of pennsylvania health system program" in name:
        reasons.append("acgme_name_matches_university_of_pennsylvania_health_system")
        return 0.32, reasons
    if "university of pennsylvania/" in name or "health system/children's hospital of philadelphia" in name:
        reasons.append("acgme_name_matches_penn_chop_joint_program")
        return 0.28, reasons
    if "pennsylvania hospital of the university of pennsylvania" in name:
        reasons.append("acgme_name_matches_pennsylvania_hospital_uphs")
        return 0.24, reasons
    if "presbyterian medical center of the university of pennsylvania" in name:
        reasons.append("acgme_name_matches_presbyterian_uphs")
        return 0.24, reasons
    if "children's hospital of philadelphia" in name:
        reasons.append("acgme_name_matches_chop_affiliate_context")
        return 0.12, reasons
    if "university of pennsylvania" in name:
        reasons.append("acgme_name_mentions_university_of_pennsylvania")
        return 0.22, reasons
    return 0.0, reasons


def specialty_score(official_name: str, acgme_specialty: str) -> tuple[float, list[str]]:
    official = norm_name(official_name)
    source = norm_name(acgme_specialty)
    aliases = SPECIALTY_ALIASES.get(official, set())
    if official == source:
        return 0.42, ["exact_specialty_name_match"]
    if source in aliases:
        return 0.40, ["specialty_alias_match"]
    official_tokens = set(official.split())
    source_tokens = set(source.split())
    containment_ratio = min(len(official_tokens), len(source_tokens)) / max(1, max(len(official_tokens), len(source_tokens)))
    token_containment = official_tokens.issubset(source_tokens) or source_tokens.issubset(official_tokens)
    if token_containment and containment_ratio >= 0.6:
        return 0.31, ["specialty_substring_match"]
    ratio = SequenceMatcher(None, official, source).ratio()
    overlap = len(official_tokens & source_tokens) / max(1, len(official_tokens | source_tokens))
    if ratio >= 0.82 and overlap >= 0.67:
        return 0.28, ["high_specialty_name_similarity"]
    if overlap >= 0.67:
        return 0.22, ["specialty_token_overlap"]
    return 0.0, []


def classify_candidate(score: float, close_competitor_count: int, reasons: list[str]) -> str:
    if score >= 0.78 and close_competitor_count <= 1 and (
        "exact_specialty_name_match" in reasons or "specialty_alias_match" in reasons
    ):
        return "strong_acgme_identifier_candidate"
    if score >= 0.74 and close_competitor_count > 1:
        return "ambiguous_acgme_identifier_candidate"
    if score >= 0.64:
        return "review_acgme_identifier_candidate"
    return "weak_acgme_identifier_candidate"


class SearchPageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.inputs: list[dict] = []
        self.options: list[dict] = []
        self._select: str | None = None
        self._option: dict | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag == "input":
            self.inputs.append(attrs)
        elif tag == "select":
            self._select = attrs.get("name") or attrs.get("id")
        elif tag == "option" and self._select:
            self._option = {"select": self._select, "value": attrs.get("value", ""), "text": ""}
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._option is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "option" and self._option is not None:
            self._option["text"] = norm_space(" ".join(self._text))
            self.options.append(self._option)
            self._option = None
            self._text = []
        elif tag == "select":
            self._select = None


class ProgramRowsParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[dict] = []
        self._row: dict | None = None
        self._tds: list[str] = []
        self._hrefs: list[str] = []
        self._in_td = False
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag == "tr" and "listview-row" in attrs.get("class", ""):
            self._row = {"data_item_key": attrs.get("data-item-key", ""), "status_matches": attrs.get("data-status-matches", "")}
            self._tds = []
            self._hrefs = []
        elif tag == "td" and self._row is not None:
            self._in_td = True
            self._text = []
        elif tag == "a" and self._row is not None and attrs.get("href"):
            self._hrefs.append(attrs["href"])

    def handle_data(self, data: str) -> None:
        if self._in_td:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "td" and self._in_td:
            self._tds.append(norm_space(" ".join(self._text)))
            self._in_td = False
        elif tag == "tr" and self._row is not None:
            if len(self._tds) >= 5:
                self._row.update(
                    {
                        "status_cell": self._tds[0],
                        "acgme_code": self._tds[1],
                        "specialty": self._tds[2],
                        "program_name": self._tds[3],
                        "city": self._tds[4],
                        "detail_url": "https://apps.acgme.org" + self._hrefs[0] if self._hrefs else "",
                    }
                )
                self.rows.append(self._row)
            self._row = None


@dataclass
class FetchResult:
    body: str
    http_status: int
    fetched_at: str


def fetch_acgme_pennsylvania_rows() -> tuple[list[dict], dict]:
    cookie_jar = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    get_request = Request(ACGME_SEARCH_URL, headers={"User-Agent": USER_AGENT})
    fetched_at = now_utc()
    with opener.open(get_request, timeout=45) as response:
        search_body = response.read().decode("utf-8", "replace")
        http_status = response.status
    parser = SearchPageParser()
    parser.feed(search_body)
    tokens = [row.get("value") for row in parser.inputs if row.get("name") == "__RequestVerificationToken"]
    if not tokens:
        raise RuntimeError("ACGME search page did not expose an anti-forgery token")
    state_ids = {row["text"]: row["value"] for row in parser.options if row.get("select") == "stateId"}
    pa_state_id = state_ids.get("Pennsylvania")
    if not pa_state_id:
        raise RuntimeError("ACGME search page did not expose Pennsylvania state filter")

    params = {
        "__RequestVerificationToken": tokens[0],
        "accreditationTypeId": "2",
        "specialtyId": "",
        "specialtyCategoryTypeId": "",
        "stateId": pa_state_id,
        "city": "",
        "numCode": "",
        "ShowProgramsList": "True",
        "CaptureProgramId": "",
        "g-recaptcha-response": "",
    }
    post_request = Request(
        ACGME_SEARCH_URL,
        data=urlencode(params).encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": ACGME_SEARCH_URL,
        },
        method="POST",
    )
    with opener.open(post_request, timeout=60) as response:
        body = response.read().decode("utf-8", "replace")
        status = response.status
    row_parser = ProgramRowsParser()
    row_parser.feed(body)
    observation = {
        "observation_key": key_for("acgme_observation", f"pennsylvania:{fetched_at}"),
        "identifier_source": "acgme_public_program_search",
        "query_scope": "state:pennsylvania",
        "query_url": ACGME_SEARCH_URL,
        "query_params_json": dumps({k: v for k, v in params.items() if k != "__RequestVerificationToken"}),
        "http_status": status or http_status,
        "result_count": len(row_parser.rows),
        "relevant_result_count": sum(1 for row in row_parser.rows if is_penn_affiliated_acgme_row(row["program_name"])),
        "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "fetched_at": fetched_at,
        "source_status": "ok" if row_parser.rows else "no_rows",
        "error_text": "",
    }
    return row_parser.rows, observation


def read_official_programs(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    return [
        dict(row)
        for row in conn.execute(
            """
            SELECT official_program_key, department, program_type, program_name, program_url
            FROM official_program_universe
            ORDER BY program_type, program_name
            """
        )
    ]


def score_source_row(official: dict, source: dict) -> tuple[float, list[str]]:
    reasons: list[str] = []
    specialty_component, specialty_reasons = specialty_score(official["program_name"], source["specialty"])
    if not specialty_reasons:
        return 0.0, []
    reasons.extend(specialty_reasons)
    institution_component, institution_reason_list = institution_reasons(source["program_name"])
    reasons.extend(institution_reason_list)
    inferred_role = role_for_acgme_specialty(source["specialty"])
    expected_role = "resident" if official["program_type"] == "residency" else "fellow"
    if inferred_role == expected_role:
        role_component = 0.08
        reasons.append("program_type_matches_acgme_specialty_family")
    else:
        role_component = 0.0
        reasons.append("program_type_mismatch_acgme_specialty_family")
    city_component = 0.09 if norm_name(source["city"]) == "philadelphia" else 0.03
    if city_component == 0.09:
        reasons.append("acgme_city_philadelphia")
    elif source["city"]:
        reasons.append("acgme_city_non_philadelphia")
    score = min(0.99, specialty_component + institution_component + role_component + city_component)
    if inferred_role != expected_role:
        score = min(score, 0.54)
    return round(score, 3), reasons


def candidate_rows(officials: list[dict], source_rows: list[dict], observed_at: str) -> list[dict]:
    penn_rows = [row for row in source_rows if is_penn_affiliated_acgme_row(row["program_name"])]
    rows: list[dict] = []
    for official in officials:
        scored = []
        for source in penn_rows:
            confidence, reasons = score_source_row(official, source)
            if confidence >= 0.64:
                scored.append((confidence, reasons, source))
        scored.sort(key=lambda item: (-item[0], item[2]["acgme_code"]))
        if not scored:
            rows.append(
                {
                    "candidate_key": key_for("program_identifier_candidate", f"{official['official_program_key']}:acgme:none"),
                    "official_program_key": official["official_program_key"],
                    "official_program_type": official["program_type"],
                    "official_program_name": official["program_name"],
                    "official_department": official.get("department") or "",
                    "identifier_type": "acgme_program_code",
                    "identifier_value": "",
                    "identifier_source": "acgme_public_program_search",
                    "source_program_specialty": "",
                    "source_program_name": "",
                    "source_city": "",
                    "source_state": "Pennsylvania",
                    "source_status_json": "",
                    "source_url": "",
                    "candidate_status": "no_acgme_identifier_found",
                    "confidence": 0.0,
                    "match_reasons_json": "[]",
                    "evidence_json": dumps(
                        {
                            "reason": "No Pennsylvania ACGME row crossed the conservative Penn affiliation and specialty threshold.",
                            "official_program_url": official.get("program_url") or "",
                        }
                    ),
                    "observed_at": observed_at,
                }
            )
            continue
        top_score = scored[0][0]
        close_count = sum(1 for confidence, _, _ in scored if top_score - confidence <= 0.06)
        for confidence, reasons, source in scored[:4]:
            if top_score - confidence > 0.12 and confidence < 0.7:
                continue
            status = classify_candidate(confidence, close_count, reasons)
            rows.append(
                {
                    "candidate_key": key_for(
                        "program_identifier_candidate",
                        f"{official['official_program_key']}:acgme:{source['acgme_code']}",
                    ),
                    "official_program_key": official["official_program_key"],
                    "official_program_type": official["program_type"],
                    "official_program_name": official["program_name"],
                    "official_department": official.get("department") or "",
                    "identifier_type": "acgme_program_code",
                    "identifier_value": source["acgme_code"],
                    "identifier_source": "acgme_public_program_search",
                    "source_program_specialty": source["specialty"],
                    "source_program_name": source["program_name"],
                    "source_city": source["city"],
                    "source_state": "Pennsylvania",
                    "source_status_json": source.get("status_matches") or "",
                    "source_url": source["detail_url"],
                    "candidate_status": status,
                    "confidence": confidence,
                    "match_reasons_json": dumps(reasons),
                    "evidence_json": dumps(
                        {
                            "official_program_url": official.get("program_url") or "",
                            "acgme_status_cell": source.get("status_cell") or "",
                            "acgme_data_item_key": source.get("data_item_key") or "",
                            "candidate_is_non_mutating": True,
                        }
                    ),
                    "observed_at": observed_at,
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_db(conn: sqlite3.Connection, rows: list[dict], observation: dict) -> None:
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute("DELETE FROM program_identifier_candidates")
    conn.execute("DELETE FROM program_identifier_source_observations")
    conn.execute(
        """
        INSERT INTO program_identifier_source_observations
        (observation_key, identifier_source, query_scope, query_url, query_params_json,
         http_status, result_count, relevant_result_count, content_sha256, fetched_at,
         source_status, error_text)
        VALUES
        (:observation_key, :identifier_source, :query_scope, :query_url, :query_params_json,
         :http_status, :result_count, :relevant_result_count, :content_sha256, :fetched_at,
         :source_status, :error_text)
        """,
        observation,
    )
    conn.executemany(
        """
        INSERT INTO program_identifier_candidates
        (candidate_key, official_program_key, official_program_type, official_program_name,
         official_department, identifier_type, identifier_value, identifier_source,
         source_program_specialty, source_program_name, source_city, source_state,
         source_status_json, source_url, candidate_status, confidence, match_reasons_json,
         evidence_json, observed_at)
        VALUES
        (:candidate_key, :official_program_key, :official_program_type, :official_program_name,
         :official_department, :identifier_type, :identifier_value, :identifier_source,
         :source_program_specialty, :source_program_name, :source_city, :source_state,
         :source_status_json, :source_url, :candidate_status, :confidence, :match_reasons_json,
         :evidence_json, :observed_at)
        """,
        rows,
    )
    conn.commit()


def write_summary(rows: list[dict], observation: dict) -> dict:
    by_status = Counter(row["candidate_status"] for row in rows)
    by_type = Counter(row["official_program_type"] for row in rows)
    with_identifier = sum(1 for row in rows if row["identifier_value"])
    summary = {
        "audited_at": now_utc(),
        "source": "ACGME public program search",
        "source_url": ACGME_SEARCH_URL,
        "observation": observation,
        "candidate_rows": len(rows),
        "official_program_rows": len({row["official_program_key"] for row in rows}),
        "rows_with_identifier": with_identifier,
        "by_candidate_status": dict(sorted(by_status.items())),
        "by_official_program_type": dict(sorted(by_type.items())),
        "strong_or_review_identifier_rows": sum(
            count
            for status, count in by_status.items()
            if status in {"strong_acgme_identifier_candidate", "review_acgme_identifier_candidate"}
        ),
        "csv": "artifacts/data/program_identifier_candidates.csv",
        "json": "artifacts/data/program_identifier_candidates.json",
        "observation_csv": "artifacts/data/program_identifier_source_observations.csv",
        "acceptance_rule": "Use ACGME code as a program identifier candidate only; do not mutate trainee roster truth or lifecycle rules without review when local tracks, duplicate sites, or non-ACGME programs are possible.",
    }
    SUMMARY_PATH.write_text(dumps(summary) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=str(DB))
    parser.add_argument("--offline-source-json", help="Use a saved ACGME row JSON file instead of fetching live data.")
    args = parser.parse_args()

    if args.offline_source_json:
        payload = json.loads(Path(args.offline_source_json).read_text(encoding="utf-8"))
        source_rows = payload["rows"]
        observation = payload["observation"]
    else:
        source_rows, observation = fetch_acgme_pennsylvania_rows()

    observed_at = observation["fetched_at"]
    conn = sqlite3.connect(args.db)
    officials = read_official_programs(conn)
    rows = candidate_rows(officials, source_rows, observed_at)
    write_db(conn, rows, observation)
    conn.close()

    write_csv(CSV_PATH, rows)
    JSON_PATH.write_text(dumps(rows) + "\n", encoding="utf-8")
    write_csv(OBSERVATION_PATH, [observation])
    summary = write_summary(rows, observation)
    print(dumps({"candidate_rows": len(rows), "by_candidate_status": summary["by_candidate_status"]}))


if __name__ == "__main__":
    main()
