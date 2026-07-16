#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import Any


TODAY = date.today().isoformat()
RAW_ROOT = Path("/opt/leadcurate/raw_imports")
PROCESSED_ROOT = Path("/opt/leadcurate/processed")

LANES = (
    "pre-foreclosure",
    "tax-delinquent",
    "tired-landlords",
    "industrial-multifamily-distress",
    "out-of-state-owners",
    "verified-vacant-land",
)

MARKETS: dict[str, dict[str, Any]] = {
    "dallas-tx": {
        "display": "Dallas County TX",
        "state": "TX",
        "source_pattern": "dallas-tx/*/dallas-parcels-canonical.csv",
        "source_url": "https://www.dallascad.org/ViewPDFs.aspx?id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CDATA+PRODUCTS%5CDCAD2026_CURRENT.ZIP&type=3",
        "source_data_as_of": "2026-07-14",
        "fields": {
            "parcel": ["ACCOUNT_NUM"],
            "owner": ["OWNER_NAME1"],
            "mail_street": ["OWNER_ADDRESS_LINE1", "OWNER_ADDRESS_LINE2", "OWNER_ADDRESS_LINE3", "OWNER_ADDRESS_LINE4"],
            "mail_compare_street": ["OWNER_ADDRESS_LINE3", "OWNER_ADDRESS_LINE4"],
            "mail_city": ["OWNER_CITY"],
            "mail_state": ["OWNER_STATE"],
            "mail_zip": ["OWNER_ZIPCODE"],
            "property_street": ["STREET_NUM", "STREET_HALF_NUM", "FULL_STREET_NAME", "UNIT_ID"],
            "property_city": ["PROPERTY_CITY"],
            "property_zip": ["PROPERTY_ZIPCODE"],
            "sale_date": ["DEED_TXFR_DATE"],
            "land_value": ["LAND_VAL"],
            "building_value": ["IMPR_VAL"],
            "other_value": [],
            "total_value": ["TOT_VAL"],
            "acreage": ["LAND_ACRES_CALC"],
            "acreage_units": [],
            "use_code": ["SPTD_CODE", "LAND_SPTD_CODES"],
            "use_desc": ["LAND_SPTD_DESCS", "P_BUS_TYP_CD", "BLDG_CLASS_CD"],
            "division": ["DIVISION_CD"],
            "year_built": ["RES_MIN_YEAR_BUILT", "COM_MIN_YEAR_BUILT"],
            "living_area": ["RES_TOTAL_LIVING_SF", "COM_GROSS_BLDG_AREA"],
            "units": ["RES_NUM_UNITS", "COM_NUM_UNITS"],
            "homestead": ["HOMESTEAD_ACTIVE"],
            "county": ["COUNTY_JURIS_DESC"],
            "municipality": ["PROPERTY_CITY"],
            "tax_delinquent": [],
            "pre_foreclosure": [],
        },
        "multifamily_prefixes": ("B1",),
        "industrial_prefixes": ("F2",),
        "residential_prefixes": ("A", "B", "C"),
        "unsupported": {
            "tax-delinquent": "DCAD appraisal data exposes taxable and assessed values, but not unpaid tax balances or delinquency status.",
            "pre-foreclosure": "DCAD appraisal data does not expose foreclosure notices or court docket filings.",
        },
    },
    "massachusetts-statewide": {
        "display": "Massachusetts Statewide",
        "state": "MA",
        "source": RAW_ROOT / "massachusetts-statewide" / TODAY / "massgis-parcels-canonical.csv",
        "source_url": "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Property_Tax_Parcels/FeatureServer/0",
        "fields": {
            "parcel": ["LC_PARCEL_KEY"],
            "owner": ["OWNER1"],
            "mail_street": ["OWN_ADDR"],
            "mail_compare_street": ["OWN_ADDR"],
            "mail_city": ["OWN_CITY"],
            "mail_state": ["OWN_STATE"],
            "mail_zip": ["OWN_ZIP"],
            "property_street": ["SITE_ADDR"],
            "property_city": ["CITY"],
            "property_zip": ["ZIP"],
            "sale_date": ["LS_DATE"],
            "land_value": ["LAND_VAL"],
            "building_value": ["BLDG_VAL"],
            "other_value": ["OTHER_VAL"],
            "total_value": ["TOTAL_VAL"],
            "acreage": ["LOT_SIZE"],
            "acreage_units": ["LOT_UNITS"],
            "use_code": ["USE_CODE"],
            "use_desc": [],
            "division": [],
            "year_built": ["YEAR_BUILT"],
            "living_area": ["BLD_AREA", "RES_AREA"],
            "units": ["UNITS"],
            "homestead": [],
            "county": ["COUNTY"],
            "municipality": ["CITY"],
            "tax_delinquent": [],
            "pre_foreclosure": [],
        },
        "vacant_codes": {"130", "131", "132", "390", "391", "392", "440", "441", "442"},
        "multifamily_prefixes": ("11", "12"),
        "industrial_prefixes": ("4",),
        "residential_prefixes": ("1",),
        "homestead_available": False,
        "unsupported": {
            "tax-delinquent": "The MassGIS statewide assessor layer does not expose municipal tax-title balances or delinquency status; that lane must be sourced after the rollup selects a county.",
            "pre-foreclosure": "Massachusetts foreclosure and Land Court records are not included in the statewide MassGIS assessor layer; that lane must be sourced after the rollup selects a county.",
        },
    },
    "cook-il": {
        "display": "Cook County IL",
        "state": "IL",
        "source": RAW_ROOT / "cook-il" / TODAY / "cook-parcels-canonical.csv",
        "source_url": "https://datacatalog.cookcountyil.gov/resource/pabr-t5kh.csv",
        "fields": {
            "parcel": ["parcel_key"],
            "owner": ["ADDR_OWNER_ADDRESS_NAME", "ADDR_MAIL_ADDRESS_NAME"],
            "mail_street": ["ADDR_OWNER_ADDRESS_FULL", "ADDR_MAIL_ADDRESS_FULL"],
            "mail_compare_street": ["ADDR_OWNER_ADDRESS_FULL", "ADDR_MAIL_ADDRESS_FULL"],
            "mail_city": ["ADDR_OWNER_ADDRESS_CITY_NAME", "ADDR_MAIL_ADDRESS_CITY_NAME"],
            "mail_state": ["ADDR_OWNER_ADDRESS_STATE", "ADDR_MAIL_ADDRESS_STATE"],
            "mail_zip": ["ADDR_OWNER_ADDRESS_ZIPCODE_1", "ADDR_MAIL_ADDRESS_ZIPCODE_1"],
            "property_street": ["ADDR_PROP_ADDRESS_FULL"],
            "property_city": ["ADDR_PROP_ADDRESS_CITY_NAME", "U_COOK_MUNICIPALITY_NAME"],
            "property_zip": ["ADDR_PROP_ADDRESS_ZIPCODE_1", "U_ZIP_CODE"],
            "sale_date": ["SALE_SALE_DATE"],
            "land_value": ["VAL_BOARD_LAND", "VAL_CERTIFIED_LAND", "VAL_MAILED_LAND"],
            "building_value": ["VAL_BOARD_BLDG", "VAL_CERTIFIED_BLDG", "VAL_MAILED_BLDG"],
            "other_value": [],
            "total_value": ["VAL_BOARD_TOT", "VAL_CERTIFIED_TOT", "VAL_MAILED_TOT"],
            "acreage": ["GEO_PARCEL_AREA_SQ_METERS"],
            "acreage_units": [],
            "use_code": ["U_CLASS", "VAL_CLASS"],
            "use_desc": ["IMPR_CHAR_USE", "COMM_PROPERTY_TYPE_USE", "COMM_PROPERTY_NAME_DESCRIPTION"],
            "division": [],
            "year_built": ["IMPR_LC_EARLIEST_YEAR_BUILT", "COMM_YEARBUILT"],
            "living_area": ["IMPR_LC_TOTAL_BUILDING_SQFT", "COMM_GROSS_BUILDING_AREA", "COMM_BLDGSF"],
            "units": ["IMPR_LC_TOTAL_APARTMENTS", "COMM_TOT_UNITS"],
            "homestead": [],
            "county": [],
            "municipality": ["U_COOK_MUNICIPALITY_NAME", "ADDR_PROP_ADDRESS_CITY_NAME"],
            "tax_delinquent": [],
            "pre_foreclosure": [],
        },
        "acreage_divisor": 4046.8564224,
        "vacant_codes": {"100"},
        "multifamily_codes": {"211", "212"},
        "multifamily_prefixes": ("3",),
        "industrial_codes": {"550", "580", "581", "583", "587", "589", "593"},
        "industrial_prefixes": ("6",),
        "residential_prefixes": ("2", "3"),
        "homestead_available": False,
        "mail_street_first_available": True,
        "mail_compare_street_first_available": True,
        "unsupported": {
            "tax-delinquent": "Cook County's public Annual Tax Sale catalog dataset is inactive and contains only a stale 2016 list; the current Treasurer list is not available as unrestricted reusable open data.",
            "pre-foreclosure": "Cook County's public Recorder foreclosure dataset ends in March 2015 and is not current enough for a customer delivery.",
        },
    },
}

STATE_ALIASES = {
    "TEXAS": "TX", "MASSACHUSETTS": "MA", "ILLINOIS": "IL", "NEW YORK": "NY",
    "CALIFORNIA": "CA", "FLORIDA": "FL", "GEORGIA": "GA", "TENNESSEE": "TN",
    "NORTH CAROLINA": "NC", "SOUTH CAROLINA": "SC", "OKLAHOMA": "OK",
    "LOUISIANA": "LA", "ARKANSAS": "AR", "NEW MEXICO": "NM", "ARIZONA": "AZ",
    "COLORADO": "CO", "MISSOURI": "MO", "VIRGINIA": "VA", "WASHINGTON": "WA",
}

PUBLIC_OWNER = re.compile(
    r"\b(CITY|COUNTY|STATE OF|UNITED STATES|U\s*S\s*A\b|U\s*S\s+ARMY|ISD\b|DISD\b|"
    r"SCHOOL|AUTHORITY|DISTRICT|UTILITY|CHURCH|METHODIST|BAPTIST|MINISTR(?:Y|IES)|"
    r"TEMPLE|MOSQUE|ISLAMIC ASSOCIATION|HOMEOWNER|ASSOCIATION|ASSN\b|HOA\b|"
    r"RAILROAD|RAILWAY|RAPID TRANSIT)\b",
    re.I,
)


def clean(value: object) -> str:
    return str(value or "").strip()


def first(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def joined(row: dict[str, str], fields: list[str]) -> str:
    return " ".join(clean(row.get(field)) for field in fields if clean(row.get(field)))


def number(value: object) -> float:
    text = clean(value).replace("$", "").replace(",", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def state_code(value: str) -> str:
    upper = clean(value).upper()
    return STATE_ALIASES.get(upper, upper[:2] if len(upper) == 2 else upper)


def parsed_date(value: str) -> date | None:
    text = clean(value)
    if len(text) >= 10 and re.fullmatch(r"\d{4}-\d{2}-\d{2}", text[:10]):
        try:
            parsed = date.fromisoformat(text[:10])
            return parsed if parsed <= date.today() else None
        except ValueError:
            pass
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%Y%m%d", "%m-%d-%Y"):
        try:
            parsed = datetime.strptime(text, fmt).date()
            return parsed if parsed <= date.today() else None
        except ValueError:
            continue
    return None


def years_owned(value: str) -> float | None:
    parsed = parsed_date(value)
    return round((date.today() - parsed).days / 365.25, 1) if parsed else None


def normalized_address(value: str) -> str:
    aliases = {
        "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W",
        "STREET": "ST", "AVENUE": "AVE", "ROAD": "RD", "BOULEVARD": "BLVD",
        "DRIVE": "DR", "LANE": "LN", "COURT": "CT", "PARKWAY": "PKWY",
        "HIGHWAY": "HWY", "PLACE": "PL", "TERRACE": "TER", "CIRCLE": "CIR",
    }
    tokens = re.findall(r"[A-Z0-9]+", clean(value).upper())
    return "".join(aliases.get(token, token) for token in tokens)


def derive(row: dict[str, str], cfg: dict[str, Any]) -> dict[str, Any]:
    f = cfg["fields"]
    owner = first(row, f["owner"])
    mail_street = first(row, f["mail_street"]) if cfg.get("mail_street_first_available") else joined(row, f["mail_street"])
    compare_fields = f.get("mail_compare_street", f["mail_street"])
    mail_compare_street = first(row, compare_fields) if cfg.get("mail_compare_street_first_available") else joined(row, compare_fields)
    mail_city = first(row, f["mail_city"])
    mail_state = state_code(first(row, f["mail_state"]))
    mail_zip = re.sub(r"\D", "", first(row, f["mail_zip"]))[:5]
    prop_street = joined(row, f["property_street"])
    prop_city = first(row, f["property_city"])
    prop_zip = re.sub(r"\D", "", first(row, f["property_zip"]))[:5]
    land = number(first(row, f["land_value"]))
    building = number(first(row, f["building_value"]))
    other = number(first(row, f.get("other_value", [])))
    total = number(first(row, f["total_value"]))
    acres = number(first(row, f["acreage"]))
    acreage_units = first(row, f.get("acreage_units", [])).upper()
    if cfg.get("acreage_divisor") and acres:
        acres /= float(cfg["acreage_divisor"])
    elif acres and ("SQ" in acreage_units or "SQUARE" in acreage_units):
        acres /= 43560.0
    year = number(first(row, f["year_built"]))
    area = number(first(row, f["living_area"]))
    use_code = joined(row, f["use_code"]).upper()
    use_desc = joined(row, f["use_desc"]).upper()
    tenure = years_owned(first(row, f["sale_date"]))
    homestead_value = first(row, f["homestead"])
    homestead = number(homestead_value) > 0
    homestead_known = bool(homestead_value) if not cfg.get("homestead_available", True) else True
    out_of_state = bool(mail_state and mail_state != cfg["state"])
    address_mismatch = bool(
        mail_compare_street
        and prop_street
        and normalized_address(mail_compare_street) != normalized_address(prop_street)
    )
    absentee = out_of_state or address_mismatch or bool(mail_zip and prop_zip and mail_zip != prop_zip)
    code_tokens = {token.strip() for token in re.split(r"[,;\s]+", use_code) if token.strip()}
    multifamily = bool(code_tokens & cfg.get("multifamily_codes", set())) or any(token.startswith(tuple(cfg.get("multifamily_prefixes", ()))) for token in code_tokens) or "MULTIFAMILY" in use_desc or "MULTI-FAMILY" in use_desc or "APARTMENT" in use_desc
    industrial = bool(code_tokens & cfg.get("industrial_codes", set())) or any(token.startswith(tuple(cfg.get("industrial_prefixes", ()))) for token in code_tokens) or "INDUSTRIAL" in use_desc or "MANUFACTUR" in use_desc
    segment = "multifamily" if multifamily else "industrial" if industrial else "other"
    residential = any(token.startswith(tuple(cfg.get("residential_prefixes", ()))) for token in code_tokens)
    vacant_codes = cfg.get("vacant_codes", set())
    vacant_signal = bool(code_tokens & vacant_codes) if vacant_codes else "VACANT" in use_desc
    is_vacant = (
        owner
        and not PUBLIC_OWNER.search(owner)
        and land > 0
        and building <= 0
        and other <= 0
        and total > 0
        and abs(total - land) <= max(1.0, total * 0.01)
        and year <= 0
        and area <= 0
        and acres >= 0.1
        and vacant_signal
    )
    return {
        "lc_parcel_id": first(row, f["parcel"]),
        "lc_owner_name": owner,
        "lc_property_address": " ".join(v for v in (prop_street, prop_city, cfg["state"], prop_zip) if v),
        "lc_mailing_address": " ".join(v for v in (mail_street, mail_city, mail_state, mail_zip) if v),
        "lc_county": first(row, f.get("county", [])),
        "lc_municipality": first(row, f.get("municipality", [])),
        "lc_mail_state": mail_state,
        "lc_is_absentee": "yes" if absentee else "no",
        "lc_is_out_of_state": "yes" if out_of_state else "no",
        "lc_years_owned": "" if tenure is None else tenure,
        "lc_tenure_band": "20+ years" if tenure is not None and tenure >= 20 else "10-19 years" if tenure is not None and tenure >= 10 else "under 10 years" if tenure is not None else "unknown",
        "lc_property_segment": segment,
        "lc_is_residential": "yes" if residential else "no",
        "lc_land_value": land,
        "lc_building_value": building,
        "lc_other_value": other,
        "lc_total_value": total,
        "lc_acreage": round(acres, 4),
        "lc_homestead": "yes" if homestead else "no" if homestead_known else "unknown",
        "lc_verified_vacant": "yes" if is_vacant else "no",
    }


def matches(lane: str, row: dict[str, str], d: dict[str, Any], cfg: dict[str, Any]) -> bool:
    if lane in cfg.get("unsupported", {}):
        return False
    if not d["lc_parcel_id"] or not d["lc_owner_name"] or PUBLIC_OWNER.search(d["lc_owner_name"]):
        return False
    if lane == "out-of-state-owners":
        return d["lc_is_out_of_state"] == "yes"
    if lane == "tired-landlords":
        return (
            isinstance(d["lc_years_owned"], (int, float))
            and d["lc_years_owned"] >= 10
            and d["lc_is_absentee"] == "yes"
            and d["lc_homestead"] != "yes"
            and d["lc_building_value"] > 0
            and (
                first(row, cfg["fields"].get("division", [])).upper() == "RES"
                or d["lc_is_residential"] == "yes"
            )
        )
    if lane == "industrial-multifamily-distress":
        return d["lc_property_segment"] in {"industrial", "multifamily"} and (
            d["lc_is_absentee"] == "yes"
            or (isinstance(d["lc_years_owned"], (int, float)) and d["lc_years_owned"] >= 10)
        )
    if lane == "verified-vacant-land":
        return d["lc_verified_vacant"] == "yes"
    if lane == "tax-delinquent":
        return bool(first(row, cfg["fields"]["tax_delinquent"]))
    if lane == "pre-foreclosure":
        return bool(first(row, cfg["fields"]["pre_foreclosure"]))
    return False


def redact(row: dict[str, Any]) -> dict[str, Any]:
    result = dict(row)
    owner = clean(result.get("lc_owner_name"))
    result["lc_owner_name"] = " ".join(part[:1] + "*" * max(2, len(part) - 1) for part in owner.split())
    result["lc_parcel_id"] = "REDACTED"
    result["lc_mailing_address"] = "REDACTED"
    address = clean(result.get("lc_property_address"))
    result["lc_property_address"] = re.sub(r"^\d+", "###", address)
    for key in list(result):
        upper = key.upper()
        exact_identifiers = {
            "ACCOUNT_NUM", "GIS_PARCEL_ID", "INFO_GIS_PARCEL_ID", "LC_PARCEL_KEY",
            "MAP_PAR_ID", "LOC_ID", "PROP_ID", "PARCEL_KEY", "U_PIN", "U_PIN10",
            "OBJECTID", "GLOBALID", "ROW_ID", "ADDR_ROW_ID", "SALE_ROW_ID",
        }
        sensitive_fragments = (
            "OWNER", "MAIL_ADDRESS", "OWN_ADDR", "OWN_CITY", "OWN_STATE", "OWN_ZIP",
            "PROPERTY_ADDRESS", "PROP_ADDRESS", "SITE_ADDR", "FULL_STREET", "FULL_STR",
            "STREET_NUM", "ADDR_NUM", "UNIT_ID", "LEGAL", "PHONE", "SALE_DOCUMENT",
        )
        coordinate_fields = {"U_LON", "U_LAT", "U_X_3435", "U_Y_3435", "LON", "LAT", "X_3435", "Y_3435"}
        if (
            upper not in {"LC_OWNER_NAME", "LC_PROPERTY_ADDRESS", "LC_MAILING_ADDRESS"}
            and (
                upper in exact_identifiers
                or upper in coordinate_fields
                or any(fragment in upper for fragment in sensitive_fragments)
            )
        ):
            result[key] = "REDACTED"
    return result


def process(market: str, source: Path, output_dir: Path, preview_count: int) -> dict[str, Any]:
    cfg = MARKETS[market]
    output_dir.mkdir(parents=True, exist_ok=True)
    csv.field_size_limit(100_000_000)
    with source.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        source_fields = reader.fieldnames or []
        derived_fields = [
            "lc_parcel_id", "lc_owner_name", "lc_property_address", "lc_mailing_address",
            "lc_county", "lc_municipality", "lc_mail_state", "lc_is_absentee", "lc_is_out_of_state", "lc_years_owned",
            "lc_tenure_band", "lc_property_segment", "lc_is_residential", "lc_land_value",
            "lc_building_value", "lc_other_value", "lc_total_value", "lc_acreage", "lc_homestead",
            "lc_verified_vacant", "lc_lane",
        ]
        fields = source_fields + derived_fields
        handles: dict[str, Any] = {}
        writers: dict[str, csv.DictWriter] = {}
        previews: dict[str, list[dict[str, Any]]] = {lane: [] for lane in LANES}
        stats: dict[str, dict[str, Any]] = {
            lane: {"count": 0, "values": [], "tenures": [], "absentee": 0, "out_of_state": 0, "segments": {"industrial": 0, "multifamily": 0}}
            for lane in LANES
        }
        paths: dict[str, dict[str, str]] = {}
        for lane in LANES:
            lane_dir = output_dir / lane
            lane_dir.mkdir(parents=True, exist_ok=True)
            stem = f"{market}-{lane}-{TODAY}"
            full = lane_dir / f"{stem}.csv"
            preview = lane_dir / f"{stem}-preview.csv"
            meta = lane_dir / f"{stem}-meta.json"
            fh = full.open("w", newline="", encoding="utf-8")
            writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            handles[lane] = fh
            writers[lane] = writer
            paths[lane] = {"full": str(full), "preview": str(preview), "meta": str(meta)}

        seen: set[str] = set()
        source_rows = 0
        duplicate_source_rows = 0
        for row in reader:
            source_rows += 1
            d = derive(row, cfg)
            parcel = clean(d["lc_parcel_id"])
            if not parcel:
                continue
            if parcel in seen:
                duplicate_source_rows += 1
                continue
            seen.add(parcel)
            for lane in LANES:
                if not matches(lane, row, d, cfg):
                    continue
                out = dict(row)
                out.update(d)
                out["lc_lane"] = lane
                writers[lane].writerow(out)
                s = stats[lane]
                s["count"] += 1
                if d["lc_total_value"] > 0:
                    s["values"].append(d["lc_total_value"])
                if isinstance(d["lc_years_owned"], (int, float)):
                    s["tenures"].append(d["lc_years_owned"])
                s["absentee"] += d["lc_is_absentee"] == "yes"
                s["out_of_state"] += d["lc_is_out_of_state"] == "yes"
                if d["lc_property_segment"] in s["segments"]:
                    s["segments"][d["lc_property_segment"]] += 1
                if len(previews[lane]) < preview_count:
                    previews[lane].append(redact(out))

        for fh in handles.values():
            fh.close()

    result: dict[str, Any] = {"market": market, "source_rows": source_rows, "unique_parcels": len(seen), "duplicate_source_rows": duplicate_source_rows, "lanes": {}}
    for lane in LANES:
        s = stats[lane]
        with Path(paths[lane]["preview"]).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(previews[lane])
        full_count = -1
        unique_full: set[str] = set()
        with Path(paths[lane]["full"]).open(newline="", encoding="utf-8") as handle:
            full_count = 0
            for shipped in csv.DictReader(handle):
                full_count += 1
                unique_full.add(clean(shipped.get("lc_parcel_id")))
        unsupported_reason = cfg.get("unsupported", {}).get(lane)
        payload = {
            "market": market,
            "market_display": cfg["display"],
            "lane": lane,
            "status": "unavailable_from_current_source" if unsupported_reason else "verified",
            "source_file": str(source),
            "source_url": cfg["source_url"],
            "source_data_as_of": cfg.get("source_data_as_of"),
            "source_rows": source_rows,
            "unique_source_parcels": len(seen),
            "source_duplicate_rows_removed": duplicate_source_rows,
            "records": s["count"],
            "preview_records": len(previews[lane]),
            "field_count": len(fields),
            "absentee_records": int(s["absentee"]),
            "out_of_state_records": int(s["out_of_state"]),
            "industrial_records": s["segments"]["industrial"],
            "multifamily_records": s["segments"]["multifamily"],
            "median_total_value": median(s["values"]) if s["values"] else None,
            "median_years_owned": median(s["tenures"]) if s["tenures"] else None,
            "unavailable_reason": unsupported_reason,
            "outputs": paths[lane],
            "verification": {
                "full_csv_rows": full_count,
                "unique_parcels_in_full_csv": len(unique_full - {""}),
                "duplicate_parcels_in_full_csv": full_count - len(unique_full - {""}),
                "meta_count_matches_file": full_count == s["count"],
            },
        }
        Path(paths[lane]["meta"]).write_text(json.dumps(payload, indent=2), encoding="utf-8")
        result["lanes"][lane] = payload
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build reusable investor lane cuts from a deduplicated maximum-field parcel CSV.")
    parser.add_argument("--market", required=True, choices=sorted(MARKETS))
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--preview", type=int, default=25)
    args = parser.parse_args()
    cfg = MARKETS[args.market]
    if args.source:
        source = args.source
    elif cfg.get("source_pattern"):
        candidates = sorted(RAW_ROOT.glob(cfg["source_pattern"]), reverse=True)
        if not candidates:
            parser.error(f"No source matched {RAW_ROOT / cfg['source_pattern']}")
        source = candidates[0]
    else:
        source = cfg["source"]
    output = args.output_dir or PROCESSED_ROOT / args.market / TODAY
    result = process(args.market, source, output, args.preview)
    print(json.dumps(result, indent=2))
    failed = any(
        lane["status"] == "verified" and (
            not lane["verification"]["meta_count_matches_file"]
            or lane["verification"]["duplicate_parcels_in_full_csv"] != 0
        )
        for lane in result["lanes"].values()
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
