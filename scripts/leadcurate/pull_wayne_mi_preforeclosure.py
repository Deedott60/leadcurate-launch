#!/usr/bin/env python3
"""Pull current Wayne County mortgage-foreclosure notices and match parcels.

Wayne County's Sheriff directs the public to Detroit Legal News for the weekly
sale notices. This manual tool queries future sale dates, downloads every notice
detail, and matches the published address to the newest Wayne parcel universe.
Expired sale dates are never emitted as current pre-foreclosure leads.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import html
import json
import re
import time
from datetime import date, datetime, time as clock_time, timedelta, timezone
from pathlib import Path
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

import requests


BASE_URL = "https://www.legalnews.com"
SEARCH_URL = f"{BASE_URL}/Home/PublicNotices"
SHERIFF_URL = "https://www.sheriffconnect.com/court-services/"
DETROIT_PARCEL_QUERY = (
    "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/"
    "parcel_file_current/FeatureServer/0/query"
)
DETAIL_PATTERN = re.compile(
    r'href="(?P<href>/Home/PublicNoticesDetails/(?P<id>\d+))"[^>]*>(?P<title>.*?)</a>',
    re.I | re.S,
)
SPACE = re.compile(r"\s+")
ADDRESS_ALIASES = {
    "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W",
    "STREET": "ST", "AVENUE": "AVE", "ROAD": "RD", "BOULEVARD": "BLVD",
    "DRIVE": "DR", "LANE": "LN", "COURT": "CT", "PARKWAY": "PKWY",
    "HIGHWAY": "HWY", "PLACE": "PL", "TERRACE": "TER", "CIRCLE": "CIR",
    "SAINT": "ST", "SECOND": "2ND",
}
STREET_SUFFIXES = {"ST", "AVE", "RD", "BLVD", "DR", "LN", "CT", "PKWY", "HWY", "PL", "TER", "CIR"}


def clean(value: object) -> str:
    return SPACE.sub(" ", str(value or "")).strip()


def html_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?</\1>", " ", value)
    return clean(html.unescape(re.sub(r"<[^>]+>", " ", value)))


def normalize_address(value: object) -> str:
    text = re.sub(r"#\s*", " UNIT ", clean(value).upper())
    tokens = re.findall(r"[A-Z0-9]+", text)
    normalized = [ADDRESS_ALIASES.get(token, token) for token in tokens if token not in {"MICHIGAN", "MI"}]
    if normalized and normalized[-1] in STREET_SUFFIXES:
        normalized.pop()
    return "".join(normalized)


def normalize_base_address(value: object) -> str:
    text = re.sub(r"^(\d+)\s*-\s*\d+", r"\1", clean(value))
    text = re.sub(r"(?:#|\bUNIT\b|\bAPT\b|\bAPARTMENT\b|\bSUITE\b).*$", "", text, flags=re.I)
    return normalize_address(text)


def normalize_city(value: object) -> str:
    text = re.sub(r"\(.*?\)", "", clean(value).upper())
    tokens = [token for token in re.findall(r"[A-Z0-9]+", text) if token not in {"CITY", "TWP", "TOWNSHIP"}]
    return "".join(tokens)


def normalize_name(value: object) -> str:
    ignored = {"A", "AN", "THE", "HUSBAND", "WIFE", "MAN", "WOMAN", "MARRIED", "SINGLE"}
    tokens = [token for token in re.findall(r"[A-Z0-9]+", clean(value).upper()) if token not in ignored]
    return "".join(sorted(tokens))


def parcel_key(value: object) -> str:
    return "".join(character for character in clean(value).upper() if character.isalnum())


def published_parcel_key(value: object) -> str:
    raw = clean(value)
    key = parcel_key(raw)
    return key[2:] if raw.startswith("82-") and key.startswith("82") else key


def house_number(value: object) -> str:
    match = re.match(r"\s*(\d+)", clean(value))
    return match.group(1) if match else ""


def parse_mdy(value: str) -> date | None:
    for fmt in ("%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(clean(value), fmt).date()
        except ValueError:
            continue
    return None


def result_address(title: str) -> tuple[str, str]:
    parts = [clean(part) for part in html_text(title).split(",") if clean(part)]
    if len(parts) < 2:
        return (parts[0] if parts else "", "")
    return ", ".join(parts[:-1]), parts[-1]


def search_payload(as_of: date, through: date) -> dict[str, str]:
    return {
        "action": "search", "search": "", "foreclosures": "true",
        "foreclosurePrevention": "false", "probates": "false",
        "vehicleAbandonment": "false", "other": "false",
        "drpproximity": "county", "drpcounty": "Wayne", "city": "", "zip": "",
        "first_date_published": "", "first_date_published_thru": "",
        "last_date_published": "", "last_date_published_thru": "",
        "published_sale_date": as_of.strftime("%m/%d/%Y"),
        "published_sale_date_thru": through.strftime("%m/%d/%Y"),
        "nameOfNotice": "", "addressOfNotice": "", "attorney": "",
        "fileNumber": "", "internalId": "", "advancedSearchResults": "1",
        "proximity": "county", "county": "Wayne",
    }


def fetch_notice_index(
    session: requests.Session, as_of: date, through: date, timeout: float
) -> list[dict[str, str]]:
    session.get(SEARCH_URL, timeout=timeout).raise_for_status()
    response = session.post(
        SEARCH_URL, data=search_payload(as_of, through), timeout=timeout
    )
    response.raise_for_status()
    notices: dict[str, dict[str, str]] = {}
    page = 1
    while True:
        if page > 1:
            response = session.get(f"{SEARCH_URL}?page={page}", timeout=timeout)
            response.raise_for_status()
        page_ids: list[str] = []
        new_ids = 0
        for match in DETAIL_PATTERN.finditer(response.text):
            notice_id = match.group("id")
            page_ids.append(notice_id)
            street, city = result_address(match.group("title"))
            if notice_id not in notices:
                new_ids += 1
                notices[notice_id] = {
                    "notice_id": notice_id,
                    "result_title": html_text(match.group("title")),
                    "published_address": street,
                    "published_city": city,
                    "detail_url": urljoin(BASE_URL, match.group("href")),
                }
        if not page_ids or new_ids == 0:
            break
        next_page = f"/Home/PublicNotices?page={page + 1}"
        if next_page not in response.text:
            break
        page += 1
        if page > 200:
            raise RuntimeError("Legal-notice pagination exceeded 200 pages")
    return list(notices.values())


def field(text: str, label: str, next_label: str) -> str:
    match = re.search(rf"{re.escape(label)}\s*(.*?)\s*{re.escape(next_label)}", text, re.I)
    return clean(match.group(1)) if match else ""


def notice_parcel_ids(text: str) -> list[str]:
    patterns = (
        r"\bPermanent\s+Property\s+No\.?\s*[:#]?\s*([0-9A-Z][0-9A-Z.\-]{6,30})",
        r"\bParcel\s+ID\s+No\.?\s*[:#]?\s*([0-9A-Z][0-9A-Z.\-]{6,30})",
        r"\bParcel\s*(?:No\.?|Number|ID)(?![A-Za-z])\s*[:#]?\s*([0-9A-Z][0-9A-Z.\-]{6,30})",
        r"\bTax\s+(?:Parcel|Property)\s*(?:No\.?|Number|ID)(?![A-Za-z])\s*[:#]?\s*([0-9A-Z][0-9A-Z.\-]{6,30})",
        r"\bTax\s+ID\s*(?:No\.?|Number)?\s*[:#]?\s*([0-9][0-9.\- ]{6,30}[0-9])",
        r"\bTax\s+Parcel\s*[:#]?\s*([0-9][0-9.\- ]{6,30}[0-9])",
        r"\bTax\s+Identification\s*(?:No\.?|Number|ID)?\s*[:#]?\s*([0-9][0-9.\- ]{6,30}[0-9])",
        r"\bSidwell\s+No\.?\s*[:#]?\s*([0-9A-Z][0-9A-Z.\-]{6,30})",
    )
    result: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.I):
            value = clean(match.group(1)).rstrip(". ,;")
            if value and published_parcel_key(value) not in {
                published_parcel_key(item) for item in result
            }:
                result.append(value)
    ward_item = re.search(r"\bWard\s+(\d{1,2})\s*,?\s*Item\s+(\d{4,8})", text, re.I)
    if ward_item:
        value = f"{int(ward_item.group(1)):02d}{int(ward_item.group(2)):06d}"
        if published_parcel_key(value) not in {published_parcel_key(item) for item in result}:
            result.append(value)
    return result


def notice_parcel_id(text: str) -> str:
    values = notice_parcel_ids(text)
    return values[0] if values else ""


def parse_detail(notice: dict[str, str], body: str) -> dict[str, object]:
    text = html_text(body)
    notice_start = text.find("View Notice Clip Foreclosures")
    if notice_start >= 0:
        text = text[notice_start:]
    notice_end = text.find("Full Description")
    if notice_end >= 0:
        text = text[:notice_end]
    first_published = field(text, "First Published:", "Last Published:")
    last_published = field(text, "Last Published:", "Published Sale Date:")
    sale_match = re.search(
        r"Published Sale Date:\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})", text, re.I
    )
    sale_label = clean(sale_match.group(1)) if sale_match else ""
    name_match = re.search(r"\bName:\s*(.*?)\s+(?:NOTICE|Notice)", text)
    amount_patterns = (
        r"Amount claimed to be due[^$]*\$([\d,]+(?:\.\d{2})?)",
        r"amount due[^$]{0,120}\$([\d,]+(?:\.\d{2})?)",
        r"(?:sum|balance)[^$]{0,180}\(\$([\d,]+(?:\.\d{2})?)\)",
    )
    amount = ""
    for pattern in amount_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            amount = match.group(1).replace(",", "")
            break
    mortgage_match = re.search(
        r"(?:Date of mortgage:|mortgage[^.]{0,180}?dated)\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        text,
        re.I,
    )
    file_match = re.search(
        r"\b(?:C&M\s+File|File\s*(?:No\.?|Number)?|Case\s*(?:No\.?|Number)?)"
        r"\s*[:#]?\s*([A-Z0-9-]{5,})",
        text,
        re.I,
    )
    published_parcels = notice_parcel_ids(text)
    published_parcel = published_parcels[0] if published_parcels else ""
    result = dict(notice)
    result.update(
        {
            "notice_type": "mortgage_foreclosure_sale",
            "first_published": first_published,
            "last_published": last_published,
            "published_sale_date": sale_label,
            "published_sale_date_iso": (
                parse_mdy(sale_label).isoformat() if parse_mdy(sale_label) else ""
            ),
            "published_name": clean(name_match.group(1)) if name_match else "",
            "published_parcel_id": published_parcel,
            "published_parcel_ids": "; ".join(published_parcels),
            "published_parcel_key": published_parcel_key(published_parcel),
            "amount_claimed_due": amount,
            "mortgage_date": clean(mortgage_match.group(1)) if mortgage_match else "",
            "file_number": clean(file_match.group(1)) if file_match else "",
            "notice_text": text,
        }
    )
    return result


def fetch_notices(
    as_of: date, through: date, delay: float, timeout: float
) -> list[dict[str, object]]:
    session = requests.Session()
    session.headers["User-Agent"] = "LeadCurate/1.0 public-record verification"
    index = fetch_notice_index(session, as_of, through, timeout)
    result: list[dict[str, object]] = []
    for item in index:
        response = session.get(str(item["detail_url"]), timeout=timeout)
        response.raise_for_status()
        parsed = parse_detail(item, response.text)
        sale_date = parse_mdy(str(parsed["published_sale_date_iso"]))
        if sale_date and as_of <= sale_date <= through:
            result.append(parsed)
        time.sleep(delay)
    return result


def detroit_legal_parcel_keys(notice: dict[str, object], timeout: float) -> list[str]:
    if normalize_city(notice.get("published_city")) != "DETROIT":
        return []
    text = clean(notice.get("notice_text")).upper()
    if "PARCEL 1" not in text or "PARCEL 2" not in text:
        return []
    lots = set(re.findall(r"\bLOT\s+(\d+)\b", text))
    subdivision = re.search(r"\bLOT\s+\d+\s*,\s*([A-Z0-9 &'\-]+?)\s+SUBDIVISION\b", text)
    if not lots or not subdivision:
        return []
    terms = [token for token in re.findall(r"[A-Z0-9]+", subdivision.group(1)) if len(token) >= 3]
    if not terms:
        return []
    where = " AND ".join(f"UPPER(legal_description) LIKE '%{term}%'" for term in terms)
    response = requests.post(
        DETROIT_PARCEL_QUERY,
        data={
            "f": "json", "where": where,
            "outFields": "parcel_id,legal_description", "returnGeometry": "false",
            "resultRecordCount": "200",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    result: list[str] = []
    for feature in response.json().get("features", []):
        attributes = feature.get("attributes") or {}
        legal = clean(attributes.get("legal_description")).upper()
        if any(re.search(rf"\b{re.escape(lot)}\b", legal) for lot in lots):
            key = parcel_key(attributes.get("parcel_id"))
            if key:
                result.append(key)
    return sorted(set(result))


def redact(row: dict[str, object]) -> dict[str, object]:
    result = dict(row)
    for key in result:
        if any(
            token in key.lower()
            for token in (
                "owner", "address", "parcel", "street", "zip", "map_number",
                "published_name", "notice_text", "notice_url",
            )
        ):
            result[key] = "REDACTED"
    return result


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build(
    canonical: Path,
    output_dir: Path,
    as_of: date,
    sale_date_from: date,
    through: date,
    delay: float,
    timeout: float,
    preview_count: int,
    notices_file: Path | None,
) -> dict[str, object]:
    if notices_file:
        with notices_file.open(newline="", encoding="utf-8-sig") as handle:
            notices = list(csv.DictReader(handle))
        for notice in notices:
            published_parcels = notice_parcel_ids(clean(notice.get("notice_text")))
            published_parcel = published_parcels[0] if published_parcels else ""
            notice["published_parcel_id"] = published_parcel
            notice["published_parcel_ids"] = "; ".join(published_parcels)
            notice["published_parcel_key"] = published_parcel_key(published_parcel)
        notices = [
            notice
            for notice in notices
            if (
                (sale_date := parse_mdy(clean(notice.get("published_sale_date_iso"))))
                and sale_date_from <= sale_date <= through
            )
        ]
    else:
        notices = fetch_notices(sale_date_from, through, delay, timeout)
    for notice in notices:
        explicit_ids = [value for value in clean(notice.get("published_parcel_ids")).split("; ") if value]
        keys = [published_parcel_key(value) for value in explicit_ids]
        if not keys:
            keys.extend(detroit_legal_parcel_keys(notice, timeout))
        notice["published_parcel_keys"] = sorted({key for key in keys if key})
    direct_keys: set[str] = set()
    exact_notice_keys: dict[tuple[str, str], list[str]] = {}
    base_notice_keys: dict[tuple[str, str], list[str]] = {}
    county_exact_notice_keys: dict[str, list[str]] = {}
    county_base_notice_keys: dict[str, list[str]] = {}
    house_notice_keys: dict[tuple[str, str], list[str]] = {}
    owner_notice_keys: dict[str, list[str]] = {}
    for notice in notices:
        direct_keys.update(str(key) for key in notice["published_parcel_keys"])
        exact_key = (
            normalize_address(notice["published_address"]),
            normalize_city(notice["published_city"]),
        )
        base_key = (
            normalize_base_address(notice["published_address"]),
            normalize_city(notice["published_city"]),
        )
        if all(exact_key):
            exact_notice_keys.setdefault(exact_key, []).append(str(notice["notice_id"]))
        if all(base_key):
            base_notice_keys.setdefault(base_key, []).append(str(notice["notice_id"]))
        if exact_key[0]:
            county_exact_notice_keys.setdefault(exact_key[0], []).append(str(notice["notice_id"]))
        if base_key[0]:
            county_base_notice_keys.setdefault(base_key[0], []).append(str(notice["notice_id"]))
        house_key = (house_number(notice["published_address"]), normalize_city(notice["published_city"]))
        if all(house_key):
            house_notice_keys.setdefault(house_key, []).append(str(notice["notice_id"]))
        owner_key = normalize_name(notice.get("published_name"))
        if owner_key:
            owner_notice_keys.setdefault(owner_key, []).append(str(notice["notice_id"]))

    direct_rows: dict[str, dict[str, str]] = {}
    exact_candidates: dict[str, dict[str, dict[str, str]]] = {}
    base_candidates: dict[str, dict[str, dict[str, str]]] = {}
    county_exact_candidates: dict[str, dict[str, dict[str, str]]] = {}
    county_base_candidates: dict[str, dict[str, dict[str, str]]] = {}
    house_candidates: dict[str, dict[str, dict[str, str]]] = {}
    owner_candidates: dict[str, dict[str, dict[str, str]]] = {}
    with canonical.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        canonical_fields = reader.fieldnames or []
        for row in reader:
            parcel = parcel_key(row.get("parcel_id"))
            if not parcel:
                continue
            if parcel in direct_keys:
                direct_rows[parcel] = row
            for notice_id in owner_notice_keys.get(normalize_name(row.get("owner_name")), []):
                owner_candidates.setdefault(notice_id, {})[parcel] = row
            cities = {
                normalize_city(row.get("municipality")),
                normalize_city(row.get("property_city")),
            } - {""}
            normalized_street = normalize_address(row.get("property_street"))
            normalized_base = normalize_base_address(row.get("property_street"))
            for notice_id in county_exact_notice_keys.get(normalized_street, []):
                county_exact_candidates.setdefault(notice_id, {})[parcel] = row
            for notice_id in county_base_notice_keys.get(normalized_base, []):
                county_base_candidates.setdefault(notice_id, {})[parcel] = row
            for city in cities:
                exact_key = (normalized_street, city)
                base_key = (normalized_base, city)
                house_key = (house_number(row.get("property_street")), city)
                for notice_id in exact_notice_keys.get(exact_key, []):
                    exact_candidates.setdefault(notice_id, {})[parcel] = row
                for notice_id in base_notice_keys.get(base_key, []):
                    base_candidates.setdefault(notice_id, {})[parcel] = row
                for notice_id in house_notice_keys.get(house_key, []):
                    house_candidates.setdefault(notice_id, {})[parcel] = row

    notices_by_parcel: dict[str, list[dict[str, object]]] = {}
    matched_notices: set[str] = set()
    parcel_rows: dict[str, dict[str, str]] = {}
    for notice in notices:
        notice_id = str(notice["notice_id"])
        resolved_rows = [
            direct_rows[str(key)]
            for key in notice["published_parcel_keys"]
            if str(key) in direct_rows
        ]
        match_method = "published_parcel_or_legal_key" if resolved_rows else ""
        row = None
        if not resolved_rows and len(exact_candidates.get(notice_id, {})) == 1:
            row = next(iter(exact_candidates[notice_id].values()))
            match_method = "exact_address_and_city"
        if not resolved_rows and row is None and len(base_candidates.get(notice_id, {})) == 1:
            row = next(iter(base_candidates[notice_id].values()))
            match_method = "normalized_address_and_city"
        if not resolved_rows and row is None and len(county_exact_candidates.get(notice_id, {})) == 1:
            row = next(iter(county_exact_candidates[notice_id].values()))
            match_method = "unique_exact_address_countywide"
        if not resolved_rows and row is None and len(county_base_candidates.get(notice_id, {})) == 1:
            row = next(iter(county_base_candidates[notice_id].values()))
            match_method = "unique_normalized_address_countywide"
        if not resolved_rows and row is None and len(owner_candidates.get(notice_id, {})) == 1:
            row = next(iter(owner_candidates[notice_id].values()))
            match_method = "unique_current_owner_name"
        if not resolved_rows and row is None and house_candidates.get(notice_id):
            target = normalize_base_address(notice["published_address"])
            scored = sorted(
                [
                    [
                        difflib.SequenceMatcher(
                            None, target, normalize_base_address(candidate.get("property_street"))
                        ).ratio(),
                        candidate,
                    ]
                    for candidate in house_candidates[notice_id].values()
                ],
                key=lambda item: item[0],
            )
            best_score, best_row = scored[-1]
            second_score = scored[-2][0] if len(scored) > 1 else 0.0
            if best_score >= 0.84 and best_score - second_score >= 0.05:
                row = best_row
                match_method = "unique_fuzzy_address_with_house_number_and_city"
        if row is not None:
            resolved_rows = [row]
        if not resolved_rows:
            continue
        notice["match_method"] = match_method
        for resolved in resolved_rows:
            parcel = parcel_key(resolved.get("parcel_id"))
            parcel_rows[parcel] = resolved
            notices_by_parcel.setdefault(parcel, []).append(notice)
        matched_notices.add(notice_id)

    matched_rows: dict[str, dict[str, object]] = {}
    for parcel, events in notices_by_parcel.items():
        events.sort(key=lambda item: str(item.get("published_sale_date_iso")))
        first = events[0]
        out: dict[str, object] = dict(parcel_rows[parcel])
        out.update({
                "lc_lane": "pre-foreclosure",
                "preforeclosure_status": "scheduled_sale_notice_current_as_of_pull",
                "preforeclosure_notice_count": len(events),
                "preforeclosure_notice_ids": "; ".join(str(item["notice_id"]) for item in events),
                "preforeclosure_match_methods": "; ".join(
                    sorted({str(item.get("match_method") or "") for item in events})
                ),
                "preforeclosure_first_published": first["first_published"],
                "preforeclosure_last_published": first["last_published"],
                "preforeclosure_sale_date": first["published_sale_date_iso"],
                "preforeclosure_published_name": first["published_name"],
                "preforeclosure_amount_claimed_due": first["amount_claimed_due"],
                "preforeclosure_mortgage_date": first["mortgage_date"],
                "preforeclosure_file_number": first["file_number"],
                "preforeclosure_notice_url": first["detail_url"],
                "preforeclosure_notice_text": first["notice_text"],
        })
        matched_rows[parcel] = out

    lane_dir = output_dir / "pre-foreclosure"
    lane_dir.mkdir(parents=True, exist_ok=True)
    stem = f"wayne-mi-pre-foreclosure-{output_dir.name}"
    full = lane_dir / f"{stem}.csv"
    preview = lane_dir / f"{stem}-preview.csv"
    unmatched = lane_dir / f"{stem}-unmatched-notices.csv"
    meta = lane_dir / f"{stem}-meta.json"
    raw = lane_dir / f"{stem}-source-notices.csv"
    event_fields = [
        "lc_lane", "preforeclosure_status", "preforeclosure_notice_count",
        "preforeclosure_notice_ids", "preforeclosure_match_methods", "preforeclosure_first_published",
        "preforeclosure_last_published", "preforeclosure_sale_date",
        "preforeclosure_published_name", "preforeclosure_amount_claimed_due",
        "preforeclosure_mortgage_date", "preforeclosure_file_number",
        "preforeclosure_notice_url", "preforeclosure_notice_text",
    ]
    fields = [*canonical_fields, *event_fields]
    rows = list(matched_rows.values())
    write_csv(full, rows, fields)
    write_csv(preview, [redact(row) for row in rows[:preview_count]], fields)
    source_fields = list(notices[0]) if notices else ["notice_id"]
    write_csv(raw, notices, source_fields)
    unmatched_rows = [row for row in notices if str(row["notice_id"]) not in matched_notices]
    match_methods: dict[str, int] = {}
    for notice in notices:
        method = str(notice.get("match_method") or "unmatched")
        match_methods[method] = match_methods.get(method, 0) + 1
    write_csv(unmatched, unmatched_rows, source_fields)
    payload = {
        "market": "wayne-mi",
        "lane": "pre-foreclosure",
        "status": "verified" if not unmatched_rows else "partial_address_match",
        "source_url": SEARCH_URL,
        "source_page": SHERIFF_URL,
        "source_status": "Sheriff-directed weekly statutory mortgage-sale notices",
        "source_data_as_of": as_of.isoformat(),
        "source_sale_date_window": {
            "from": sale_date_from.isoformat(),
            "through": through.isoformat(),
        },
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "current_status_limitation": (
            "A published future sale notice is a current pre-foreclosure event, but a sale can be "
            "postponed, canceled, cured, or affected by bankruptcy. Refresh on delivery day."
        ),
        "canonical_source": str(canonical),
        "source_notices": len(notices),
        "matched_notices": len(matched_notices),
        "unmatched_notices": len(unmatched_rows),
        "notice_match_methods": dict(sorted(match_methods.items())),
        "published_or_legal_keys_not_in_current_roll": sorted(direct_keys - set(direct_rows)),
        "records": len(rows),
        "outputs": {
            "full": str(full), "preview": str(preview), "meta": str(meta),
            "source_notices": str(raw), "unmatched_notices": str(unmatched),
        },
        "verification": {
            "full_csv_rows": len(rows),
            "unique_parcels_in_full_csv": len(matched_rows),
            "duplicate_parcels_in_full_csv": len(rows) - len(matched_rows),
            "all_notices_address_matched": not unmatched_rows,
            "no_expired_sale_dates_in_full_csv": all(
                str(row["preforeclosure_sale_date"]) >= sale_date_from.isoformat()
                for row in rows
            ),
        },
    }
    meta.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    local_now = datetime.now(ZoneInfo("America/Detroit"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--as-of", type=date.fromisoformat, default=local_now.date())
    parser.add_argument("--sale-date-from", type=date.fromisoformat)
    parser.add_argument("--through", type=date.fromisoformat)
    parser.add_argument("--lookahead-days", type=int, default=365)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--preview", type=int, default=25)
    parser.add_argument("--notices-file", type=Path)
    args = parser.parse_args()
    sale_date_from = args.sale_date_from or args.as_of
    if (
        args.sale_date_from is None
        and args.as_of == local_now.date()
        and local_now.time() >= clock_time(11, 0)
    ):
        sale_date_from += timedelta(days=1)
    through = args.through or sale_date_from + timedelta(days=args.lookahead_days)
    if sale_date_from < args.as_of:
        parser.error("--sale-date-from cannot be earlier than --as-of")
    result = build(
        args.canonical, args.output_dir, args.as_of, sale_date_from, through,
        args.delay, args.timeout, args.preview, args.notices_file,
    )
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
