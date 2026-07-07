#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


RAW_ROOT = Path("/opt/leadcurate/raw_imports")
PROCESSED_ROOT = Path("/opt/leadcurate/processed")
TODAY = date.today().isoformat()

EXCLUDE_OWNER = re.compile(
    r"ASSOCIATION|HOMEOWNER|HOA\b|CITY OF|COUNTY|STATE OF|TOWN OF|CHURCH|"
    r"DEPARTMENT|AUTHORITY|DISTRICT|UNITED STATES|NCDOT|GDOT|DUKE ENERGY|"
    r"RAILROAD|RAILWAY|SCHOOL|UNIVERSITY|BOARD OF EDUCATION",
    re.I,
)

MARKETS: dict[str, dict[str, Any]] = {
    "mecklenburg-nc": {
        "display": "Mecklenburg County NC",
        "source": RAW_ROOT / "mecklenburg-nc" / "vacant-land.csv",
        "output_date": "2026-07-07",
        "state": "NC",
        "county": "Mecklenburg",
        "fields": {
            "vacant": ["vacantorimproved"],
            "vacant_values": {"VAC"},
            "land": ["landvalue"],
            "building": ["netbldgvalue"],
            "total": ["totalvalue"],
            "year": ["yearbuilt"],
            "heated": ["heatedarea"],
            "owner": ["ownerfirstname", "ownerlastname"],
            "acreage": ["totalac"],
            "parcel": ["pid"],
            "address": ["FULL_ADDRESS"],
            "city": ["municipality"],
            "mail_city": ["city"],
            "mail_state": ["state"],
            "mail_zip": ["zipcode"],
            "land_use": ["landusecode", "descpropertyuse"],
        },
        "join_fields": {"owner"},
    },
    "wake-nc": {
        "display": "Wake County NC",
        "source": RAW_ROOT / "wake-nc" / "parcels.csv",
        "state": "NC",
        "county": "Wake",
        "fields": {
            "vacant": ["LAND_CLASS", "LAND_CLASS_DECODE"],
            "vacant_values": {"VAC", "VACANT"},
            "land": ["LAND_VAL"],
            "building": ["BLDG_VAL"],
            "total": ["TOTAL_VALUE_ASSD"],
            "year": ["YEAR_BUILT"],
            "heated": ["HEATEDAREA"],
            "owner": ["OWNER"],
            "acreage": ["DEED_ACRES", "CALC_AREA"],
            "parcel": ["REID", "PIN_NUM"],
            "address": ["SITE_ADDRESS"],
            "city": ["CITY_DECODE", "CITY"],
            "mail_city": ["ADDR2"],
            "mail_state": ["ADDR2"],
            "mail_zip": ["ADDR2"],
            "land_use": ["LAND_CLASS_DECODE", "PROPDESC"],
        },
        "join_fields": {"address"},
    },
    "guilford-nc": {
        "display": "Guilford County NC",
        "source": RAW_ROOT / "guilford-nc" / "2026-06-19" / "county-parcels.csv",
        "state": "NC",
        "county": "Guilford",
        "fields": {
            "vacant": ["LAND_CLASS"],
            "vacant_values": {"VACANT"},
            "land": ["TOTAL_LAND_VALUE_ASSESSED"],
            "building": ["TOTAL_BLDG_VALUE_ASSESSED", "TOTAL_OBLDG_VALUE"],
            "total": ["TOTAL_PROP_VALUE"],
            "year": ["YEAR_BUILT"],
            "heated": ["MAIN_BLDG_HEATED_AREA", "HEATED_AREA"],
            "owner": ["PROPERTY_OWNER", "PROP_OWNER1_FULLNAME"],
            "acreage": ["DEEDED_ACRES", "TOTAL_ACRES", "ACREAGE"],
            "parcel": ["PARCEL_NO", "REID", "PIN"],
            "address": ["LOCATION_ADDR"],
            "city": ["PHYADDR_CITY", "CITY"],
            "mail_city": ["OWNER_MAIL_CITY"],
            "mail_state": ["OWNER_MAIL_STATE"],
            "mail_zip": ["OWNER_MAIL_ZIP"],
            "land_use": ["LAND_CLASS", "PROPERTY_DESCR"],
        },
    },
    "fulton-ga": {
        "display": "Fulton County GA",
        "source": RAW_ROOT / "fulton-ga" / "tax-parcels-2025.csv",
        "state": "GA",
        "county": "Fulton",
        "fields": {
            "vacant": ["CLASSDSCRP", "CVTTXDSCRP", "PRPRTYDSCRP"],
            "vacant_values": set(),
            "land": ["LNDVALUE", "LANDAPPR"],
            "building": ["IMPR_APPR"],
            "total": ["TOT_APPR", "CNTASSDVAL", "PRVASSDVAL"],
            "year": [],
            "heated": ["LIVUNITS"],
            "owner": ["OWNERNME1"],
            "acreage": [],
            "parcel": ["PARCELID", "LOWPARCELID"],
            "address": ["SITEADDRESS"],
            "city": ["SITECITY"],
            "mail_city": ["PSTLCITY", "PSTLADDRESS2"],
            "mail_state": ["PSTLSTATE", "PSTLADDRESS2"],
            "mail_zip": ["PSTLZIP5", "PSTLADDRESS2"],
            "land_use": ["CLASSDSCRP", "CVTTXDSCRP"],
        },
        "acreage_from_shape_area": "SHAPEAREA",
    },
    "marion-in": {
        "display": "Marion County IN",
        "source": RAW_ROOT / "marion-in" / "parcels-owner-assessed.csv",
        "state": "IN",
        "county": "Marion",
        "fields": {
            "vacant": ["STATUS", "PROPERTY_SUB_CLASS_DESCRIPTION"],
            "vacant_values": {"VACANT"},
            "land": ["ASSESSORYEAR_LANDTOTAL"],
            "building": ["ASSESSORYEAR_IMPTOTAL"],
            "total": ["ASSESSORYEAR_TOTALAV"],
            "year": [],
            "heated": [],
            "owner": ["FULLOWNERNAME"],
            "acreage": ["ACREAGE"],
            "parcel": ["STATEPARCELNUMBER", "PARCEL_TAG", "CAMAPARCELID"],
            "address": ["STNUMBER", "PRE_DIR", "FULL_STNAME"],
            "city": ["CITY"],
            "mail_city": ["OWNERCITY"],
            "mail_state": ["OWNERSTATE"],
            "mail_zip": ["OWNERZIP"],
            "land_use": ["PROPERTY_SUB_CLASS_DESCRIPTION", "PROPERTY_CLASS"],
        },
        "acreage_from_squarefeet": "ESTSQFT",
    },
}


def clean(value: object) -> str:
    return str(value or "").strip()


def money(value: object) -> float:
    text = clean(value).replace("$", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def first(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def join_fields(row: dict[str, str], fields: list[str]) -> str:
    return " ".join(clean(row.get(field)) for field in fields if clean(row.get(field)))


def parse_city_state_zip(value: str) -> tuple[str, str, str]:
    text = clean(value)
    zip_match = re.search(r"\b(\d{5}(?:-\d{4})?)\b", text)
    state_match = re.search(r"\b([A-Z]{2})\b", text)
    zip_code = zip_match.group(1) if zip_match else ""
    state = state_match.group(1) if state_match else ""
    city = text
    if state_match:
        city = text[: state_match.start()].strip().rstrip(",")
    return city, state, zip_code


def field_value(row: dict[str, str], cfg: dict[str, Any], key: str) -> str:
    fields = cfg["fields"][key]
    if key in cfg.get("join_fields", set()) and len(fields) > 1:
        return join_fields(row, fields)
    return first(row, fields)


def vacant_signal(row: dict[str, str], cfg: dict[str, Any]) -> tuple[bool, str]:
    values = [clean(row.get(field)) for field in cfg["fields"]["vacant"] if clean(row.get(field))]
    text = " ".join(values).upper()
    allowed = {v.upper() for v in cfg["fields"].get("vacant_values", set())}
    if allowed and any(value.upper() in allowed or value.upper().find("VACANT") >= 0 for value in values):
        return True, text
    if "VACANT" in text or re.search(r"\bVAC\b", text):
        return True, text
    if not allowed:
        return True, "NO_IMPROVEMENT_VALUE_PROFILE"
    return False, text


def acreage(row: dict[str, str], cfg: dict[str, Any]) -> float:
    value = money(field_value(row, cfg, "acreage"))
    if value:
        return value
    area_field = cfg.get("acreage_from_shape_area")
    if area_field:
        square_feet = money(row.get(area_field))
        if square_feet:
            return square_feet / 43560
    sqft_field = cfg.get("acreage_from_squarefeet")
    if sqft_field:
        square_feet = money(row.get(sqft_field))
        if square_feet:
            return square_feet / 43560
    return 0.0


def mailing_parts(row: dict[str, str], cfg: dict[str, Any]) -> tuple[str, str, str]:
    city = field_value(row, cfg, "mail_city")
    state = field_value(row, cfg, "mail_state")
    zip_code = field_value(row, cfg, "mail_zip")
    if (not state or len(state.strip()) != 2 or not zip_code or not re.search(r"\d{5}", zip_code)) and city:
        parse_source = " ".join(dict.fromkeys([city, state, zip_code]))
        parsed_city, parsed_state, parsed_zip = parse_city_state_zip(parse_source)
        city = parsed_city or city
        if not state or len(state.strip()) != 2:
            state = parsed_state
        if not zip_code or not re.search(r"\d{5}", zip_code):
            zip_code = parsed_zip
    return city, state, zip_code


def qualifies(row: dict[str, str], cfg: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    vacant_ok, vacant_text = vacant_signal(row, cfg)
    land = money(field_value(row, cfg, "land"))
    building = money(field_value(row, cfg, "building"))
    total = money(field_value(row, cfg, "total"))
    year_built = field_value(row, cfg, "year")
    heated = money(field_value(row, cfg, "heated"))
    ac = acreage(row, cfg)
    owner = field_value(row, cfg, "owner")
    failures = []
    if not vacant_ok:
        failures.append("vacant signal missing")
    if building > 0:
        failures.append("building value present")
    if land <= 0 or total <= 0 or abs(total - land) > max(1.0, total * 0.01):
        failures.append("total value not equal to land value")
    if clean(year_built) or heated > 0:
        failures.append("year built or heated area present")
    if not owner or EXCLUDE_OWNER.search(owner):
        failures.append("excluded owner")
    if ac < 0.1:
        failures.append("acreage under 0.1")
    city, mail_state, mail_zip = mailing_parts(row, cfg)
    return not failures, {
        "failures": failures,
        "owner_name": owner,
        "property_address": field_value(row, cfg, "address") or "(unaddressed parcel)",
        "municipality": field_value(row, cfg, "city"),
        "mail_city": city,
        "mail_state": mail_state,
        "mail_zip": mail_zip,
        "total_acreage": round(ac, 4),
        "land_value": round(land, 2),
        "total_value": round(total, 2),
        "building_value": round(building, 2),
        "year_built": clean(year_built),
        "heated_sqft": round(heated, 2),
        "land_use_code": field_value(row, cfg, "land_use"),
        "vacant_signal": vacant_text,
        "parcel_pid": field_value(row, cfg, "parcel"),
    }


def redact_name(value: str) -> str:
    return " ".join(part[:1] + "*" * max(len(part) - 1, 2) for part in value.split())


def write_outputs(market: str, rows: list[dict[str, Any]], total: int, cfg: dict[str, Any], output_dir: Path, top_n: int) -> dict[str, Any]:
    rows.sort(key=lambda r: (r["score"], r["land_value"], r["total_acreage"]), reverse=True)
    top = rows[:top_n]
    output_dir.mkdir(parents=True, exist_ok=True)
    out_date = cfg.get("output_date", TODAY)
    stem = f"{market}-verified-vacant-{out_date}"
    full = output_dir / f"{stem}.csv"
    preview = output_dir / f"{stem}-preview.csv"
    meta = output_dir / f"{stem}-meta.json"
    cols = [
        "rank", "score", "owner_name", "property_address", "municipality", "mail_city",
        "mail_state", "mail_zip", "total_acreage", "land_value", "total_value",
        "is_absentee_owner", "vacant_signal", "building_value", "year_built",
        "heated_sqft", "land_use_code", "parcel_pid", "lane", "county", "state",
    ]
    with full.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        for idx, row in enumerate(top, 1):
            writer.writerow([idx] + [row.get(c, "") for c in cols[1:]])
    with preview.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(cols)
        for idx, row in enumerate(top[:25], 1):
            out = dict(row)
            out["owner_name"] = redact_name(clean(out["owner_name"]))
            out["mail_city"] = ""
            out["mail_zip"] = ""
            out["parcel_pid"] = "REDACTED"
            writer.writerow([idx] + [out.get(c, "") for c in cols[1:]])
    absentee = sum(1 for row in rows if row["is_absentee_owner"] == "yes")
    oos = sum(1 for row in rows if clean(row["mail_state"]).upper() not in ("", cfg["state"]))
    payload = {
        "lane": "verified_vacant_land",
        "market": market,
        "processed_date": out_date,
        "source": str(cfg["source"]),
        "total_source_rows": total,
        "verified_vacant": len(rows),
        "absentee": absentee,
        "out_of_state": oos,
        "exported": len(top),
        "outputs": {"full": str(full), "preview": str(preview), "meta": str(meta)},
        "verification_criteria": [
            "county vacant/land signal mapped per market",
            "building value = 0",
            "total value equals land value",
            "no year built / heated area",
            "owner not HOA/municipal/utility/rail/public institutional",
            "parcel acreage >= 0.1",
        ],
    }
    meta.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def process_market(market: str, source: Path | None, output_dir: Path | None, top_n: int) -> dict[str, Any]:
    cfg = MARKETS[market]
    source_path = source or cfg["source"]
    out_dir = output_dir or PROCESSED_ROOT / market / cfg.get("output_date", TODAY)
    rows = []
    total = 0
    with source_path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for raw in csv.DictReader(f):
            total += 1
            ok, row = qualifies(raw, cfg)
            if not ok:
                continue
            row["is_absentee_owner"] = "yes" if clean(row["mail_state"]).upper() not in ("", cfg["state"]) else "no"
            row["score"] = round(row["land_value"] / 1000 + row["total_acreage"] * 40 + (150 if row["is_absentee_owner"] == "yes" else 0), 1)
            row["lane"] = "verified_vacant_land"
            row["county"] = cfg["county"]
            row["state"] = cfg["state"]
            rows.append(row)
    return write_outputs(market, rows, total, cfg, out_dir, top_n)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verified vacant land processor with per-county column maps.")
    parser.add_argument("--market", choices=sorted(MARKETS), default="mecklenburg-nc")
    parser.add_argument("--source")
    parser.add_argument("--output-dir")
    parser.add_argument("--top", type=int, default=250)
    args = parser.parse_args()
    payload = process_market(
        args.market,
        Path(args.source) if args.source else None,
        Path(args.output_dir) if args.output_dir else None,
        args.top,
    )
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
