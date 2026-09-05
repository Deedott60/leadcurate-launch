#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import html
import json
import re
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib import error, parse, request


RAW_ROOT = Path("/opt/leadcurate/raw_imports")
SEARCH_URL = "https://assessment.cot.tn.gov/TPAD/Search/GetSearchResults"
DETAIL_URL = "https://assessment.cot.tn.gov/TPAD/Parcel/Details"
SOURCE_URL = "https://assessment.cot.tn.gov/TPAD"

MARKETS = {
    "bradley-tn": {"jur": "006", "county": "Bradley"},
    "marion-tn": {"jur": "058", "county": "Marion"},
}

PROPERTY_TYPES = {
    "10": "Farm",
    "11": "Agricultural",
    "12": "Forest",
    "13": "Open Space",
}

OUTPUT_FIELDS = [
    "parcel_id",
    "parcel_key",
    "owner_name",
    "mailing_street",
    "mail_city",
    "mail_state",
    "mail_zip",
    "property_address",
    "class",
    "property_type",
    "land_market_value",
    "improvement_value",
    "total_market_appraisal",
    "assessment",
    "deed_acres",
    "calculated_acres",
    "number_of_buildings",
    "utilities_water_sewer",
    "utilities_electricity",
    "sale_date",
    "sale_vacant_improved",
    "gis_map",
    "source_url",
]


def clean(value: object) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return " ".join(text.split()).strip()


def money(text: str) -> str:
    match = re.search(r"\$[\d,]+(?:\.\d+)?", text or "")
    return match.group(0).replace("$", "").replace(",", "") if match else ""


def post_search(jur: str, property_type: str) -> list[dict[str, Any]]:
    payload = parse.urlencode(
        {"Jur": jur, "PropertyType": property_type, "SortBy": "Owner Name"}
    ).encode()
    req = request.Request(
        SEARCH_URL,
        data=payload,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LeadCurate/1.0)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": SOURCE_URL,
        },
    )
    with request.urlopen(req, timeout=60) as res:
        data = json.load(res)
    if isinstance(data, list):
        return data
    return data.get("value") or []


def detail_html(row: dict[str, Any], attempts: int = 4) -> str:
    params = {
        "parcelId": row["parcelId"],
        "jur": row["jur"],
        "parcelKey": row["parcelKey"],
        "searchParameters": "{}",
    }
    req = request.Request(
        DETAIL_URL + "?" + parse.urlencode(params),
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LeadCurate/1.0)",
            "Referer": SOURCE_URL,
        },
    )
    for attempt in range(attempts):
        try:
            with request.urlopen(req, timeout=60) as res:
                return res.read().decode("utf-8", "ignore")
        except error.HTTPError as exc:
            if exc.code != 403 or attempt == attempts - 1:
                raise
            time.sleep(2 * (attempt + 1))
        except TimeoutError:
            if attempt == attempts - 1:
                raise
            time.sleep(2 * (attempt + 1))
    return ""


def card_body(page: str, title: str) -> str:
    pattern = (
        r'<div[^>]*class="card-header"[^>]*>\s*'
        + re.escape(title)
        + r"\s*</div>\s*<div[^>]*class=\"card-body\"[^>]*>(.*?)</div>\s*</div>"
    )
    match = re.search(pattern, page, re.I | re.S)
    return match.group(1) if match else ""


def label_value(page: str, label: str) -> str:
    match = re.search(r"<strong[^>]*>\s*" + re.escape(label) + r"\s*:?\s*</strong>", page, re.I)
    if not match:
        return ""
    window = page[match.end() : match.end() + 300]
    end = re.search(r"</(?:p|div|span)>", window, re.I)
    return clean(window[: end.start()] if end else window)


def value_after_label(page: str, label: str) -> str:
    match = re.search(r"<strong[^>]*>\s*" + re.escape(label) + r"\s*:?\s*</strong>", page, re.I)
    if not match:
        return ""
    return money(page[match.end() : match.end() + 300])


def owner_and_mailing(page: str) -> tuple[str, str, str, str, str]:
    match = re.search(r"January 1 Owner\s*</strong>\s*</div>(.*?)(?:Property Location|Value Information)", page, re.I | re.S)
    body = match.group(1) if match else card_body(page, "Property Owner and Mailing Address")
    lines = [clean(part) for part in re.findall(r"<div[^>]*>(.*?)</div>", body, re.I | re.S)]
    lines = [line for line in lines if line and line.lower() != "january 1 owner"]
    owner = lines[0] if lines else ""
    street = lines[1] if len(lines) > 1 else ""
    city_state_zip = lines[-1] if len(lines) > 2 else ""
    match = re.match(r"(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)$", city_state_zip)
    if match:
        return owner, street, match.group(1), match.group(2), match.group(3)
    return owner, street, "", "", ""


def first_sale(page: str) -> tuple[str, str]:
    start = re.search(r"Sale Information", page, re.I)
    end = re.search(r"Land Information", page, re.I)
    page = page[start.start() : end.start()] if start and end and start.start() < end.start() else page
    match = re.search(
        r"<tbody>\s*<tr>\s*<td[^>]*>(.*?)</td>.*?<td[^>]*>.*?</td>.*?<td[^>]*>.*?</td>.*?"
        r"<td[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>",
        page,
        re.I | re.S,
    )
    if not match:
        return "", ""
    return clean(match.group(1)), clean(match.group(2))


def parse_detail(row: dict[str, Any], page: str) -> dict[str, str]:
    owner, street, mail_city, mail_state, mail_zip = owner_and_mailing(page)
    sale_date, sale_vacant = first_sale(page)
    land = value_after_label(page, "Land Market Value")
    improvement = value_after_label(page, "Improvement Value")
    total = value_after_label(page, "Total Market Appraisal")
    assessment = value_after_label(page, "Assessment")
    return {
        "parcel_id": clean(row.get("parcelId")),
        "parcel_key": clean(row.get("parcelKey")),
        "owner_name": owner or clean(row.get("owner")),
        "mailing_street": street,
        "mail_city": mail_city,
        "mail_state": mail_state,
        "mail_zip": mail_zip,
        "property_address": label_value(page, "Address") or clean(row.get("propertyAddress")),
        "class": label_value(page, "Class") or clean(row.get("class")),
        "property_type": clean(row.get("propertyType")),
        "land_market_value": land,
        "improvement_value": improvement,
        "total_market_appraisal": total,
        "assessment": assessment,
        "deed_acres": label_value(page, "Deed Acres"),
        "calculated_acres": label_value(page, "Calculated Acres"),
        "number_of_buildings": label_value(page, "Number of buildings"),
        "utilities_water_sewer": label_value(page, "Utilities - Water/Sewer"),
        "utilities_electricity": label_value(page, "Utilities - Electricity"),
        "sale_date": sale_date or clean(row.get("dateOfSaleShort")),
        "sale_vacant_improved": sale_vacant,
        "gis_map": clean(row.get("gisMap")),
        "source_url": SOURCE_URL,
    }


def fetch_detail(search_row: dict[str, Any], sleep_seconds: float) -> dict[str, str]:
    page = detail_html(search_row)
    if sleep_seconds:
        time.sleep(sleep_seconds)
    return parse_detail(search_row, page)


def pull(market: str, limit: int | None, sleep_seconds: float, workers: int) -> dict[str, Any]:
    cfg = MARKETS[market]
    out_dir = RAW_ROOT / market / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates: list[dict[str, Any]] = []
    searched: dict[str, int] = {}
    seen: set[str] = set()
    for property_type in PROPERTY_TYPES:
        search_rows = post_search(cfg["jur"], property_type)
        searched[property_type] = len(search_rows)
        for search_row in search_rows:
            key = clean(search_row.get("parcelKey"))
            if not key or key in seen:
                continue
            seen.add(key)
            candidates.append(search_row)
            if limit and len(candidates) >= limit:
                break
        if limit and len(candidates) >= limit:
            break
    rows: list[dict[str, str]] = []
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = [pool.submit(fetch_detail, row, sleep_seconds) for row in candidates]
        for future in as_completed(futures):
            try:
                rows.append(future.result())
            except Exception as exc:
                rows.append({
                    "parcel_id": "",
                    "parcel_key": "",
                    "owner_name": "",
                    "mailing_street": "",
                    "mail_city": "",
                    "mail_state": "",
                    "mail_zip": "",
                    "property_address": "",
                    "class": "",
                    "property_type": "",
                    "land_market_value": "",
                    "improvement_value": "",
                    "total_market_appraisal": "",
                    "assessment": "",
                    "deed_acres": "",
                    "calculated_acres": "",
                    "number_of_buildings": "",
                    "utilities_water_sewer": "",
                    "utilities_electricity": "",
                    "sale_date": "",
                    "sale_vacant_improved": "",
                    "gis_map": "",
                    "source_url": f"ERROR: {type(exc).__name__}: {exc}",
                })
    out_path = out_dir / "tpad-land.csv"
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    error_rows = sum(1 for row in rows if row["source_url"].startswith("ERROR:"))
    return {
        "ok": True,
        "market": market,
        "county": cfg["county"],
        "jur": cfg["jur"],
        "source_url": SOURCE_URL,
        "property_types": PROPERTY_TYPES,
        "searched_rows": searched,
        "candidate_rows": len(candidates),
        "written_rows": len(rows),
        "error_rows": error_rows,
        "csv": str(out_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual TPAD land parcel pull for TN comparison counties.")
    parser.add_argument("--market", required=True, choices=sorted(MARKETS))
    parser.add_argument("--limit", type=int, default=0, help="Optional row cap for testing.")
    parser.add_argument("--sleep", type=float, default=0.1)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    print(json.dumps(pull(args.market, args.limit or None, args.sleep, args.workers), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

