#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib import parse, request

RAW_ROOT = Path("/opt/leadcurate/raw_imports/shelby-tn")
PROCESSED_ROOT = Path("/opt/leadcurate/processed/shelby-tn")
REGISTER_BASE = "https://gis.register.shelby.tn.us"
DATA_MIDSOUTH = "https://datamidsouth.opendatasoft.com/api/explore/v2.1/catalog/datasets"

ENTITY_WORDS = (
    " LLC", " INC", " CORP", " LP", " LLP", " CO ", " COMPANY", " PROPERTIES",
    " INVESTMENTS", " HOLDINGS", " PARTNERS", " BANK", " TRUST", " CHURCH",
    " MINISTR", " CITY OF", " COUNTY", " STATE OF", " AUTHORITY", " AGENCY",
    " ASSOCIATION", " HOA", " FOUNDATION", " SCHOOL", " BOARD", " HOSPITAL",
    " UNIVERSITY", " BAPTIST", " METHODIST", " TEMPLE", " REDEVELOPMENT",
)

OUTPUT_FIELDS = [
    "parcel_id",
    "parcel_id_compact",
    "trustee_id",
    "property_address",
    "property_city",
    "property_zip",
    "municipality",
    "map_page",
    "neighborhood",
    "subdivision",
    "sub_lot",
    "lot_dimensions",
    "calculated_sqft",
    "owner_name",
    "owner_name_2",
    "owner_mailing_street",
    "owner_mailing_city",
    "owner_mailing_state",
    "owner_mailing_zip",
    "owner_address_type",
    "owner_country",
    "property_class",
    "property_use",
    "current_land_value",
    "current_building_value",
    "current_total_value",
    "current_assessed_value",
    "current_greenbelt_land_value",
    "current_greenbelt_total_value",
    "current_greenbelt_assessed_value",
    "current_homestead_land_value",
    "current_homestead_building_value",
    "current_partial_value",
    "prior_class",
    "prior_land_value",
    "prior_building_value",
    "prior_total_value",
    "prior_assessed_value",
    "prior_greenbelt_land_value",
    "prior_greenbelt_total_value",
    "prior_greenbelt_assessed_value",
    "prior_homestead_land_value",
    "prior_homestead_building_value",
    "prior_partial_value",
    "acres",
    "year_built",
    "stories",
    "total_rooms",
    "bedrooms",
    "full_baths",
    "half_baths",
    "living_area_sqft",
    "main_ground_floor_area",
    "exterior_wall",
    "basement_type",
    "heat",
    "heat_fuel",
    "heat_system",
    "parking_type",
    "wood_burning_fireplaces_opening",
    "wood_burning_fireplaces_prefab",
    "tax_sale_status",
    "sales_count",
    "latest_sale_date",
    "latest_sale_price",
    "latest_sale_instrument_code",
    "latest_sale_instrument_number",
    "latest_sale_document_url",
    "sales_instrument_codes",
    "sales_history_json",
    "lanes",
    "lane_reasons",
    "register_gis_url",
    "assessor_property_url",
    "county_tax_url",
    "city_tax_url",
    "tax_map_document_url",
    "source_urls",
    "public_record_json",
]


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def compact_parcel(parcel: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", clean(parcel)).upper()


def money(value: Any) -> float:
    text = clean(value).replace("$", "").replace(",", "")
    try:
        return float(text) if text else 0.0
    except ValueError:
        return 0.0


def register_post(endpoint: str, payload: dict[str, Any], timeout: int = 90) -> Any:
    req = request.Request(
        f"{REGISTER_BASE}{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LeadCurate/1.0)",
            "Content-Type": "application/json",
            "Origin": REGISTER_BASE,
            "Referer": f"{REGISTER_BASE}/",
        },
    )
    with request.urlopen(req, timeout=timeout) as res:
        return json.loads(res.read().decode("utf-8", "replace"))


def register_prefix(prefix: str, max_rows: int) -> list[dict[str, Any]]:
    data = register_post("/details", {"searchtype": "parcelID", "parcelid": prefix})
    if isinstance(data, dict) and data.get("error"):
        return []
    if not isinstance(data, list):
        return []
    return data[:max_rows] if max_rows > 0 else data


def completedetails(parcel_id: str) -> dict[str, Any] | None:
    data = register_post("/completedetails", {"parcelid": clean(parcel_id)}, timeout=45)
    if isinstance(data, dict) and data.get("content"):
        return data
    return None


def owner_street(c: dict[str, Any]) -> str:
    explicit = clean(" ".join(clean(c.get(k)) for k in ["OADDR1", "OADDR2", "OADDR3"] if clean(c.get(k))))
    if explicit:
        return explicit
    return clean(" ".join(clean(c.get(k)) for k in ["OADRNO", "OADRDIR", "OADRSTR", "OADRSUF", "OADRSUF2", "OUNITDESC", "OUNITNO"] if clean(c.get(k))))


def owner_zip(c: dict[str, Any]) -> str:
    zip1 = clean(c.get("ZIP1"))
    zip2 = clean(c.get("ZIP2"))
    return f"{zip1}-{zip2}" if zip1 and zip2 else zip1


def is_entity(owner: str) -> bool:
    upper = f" {owner.upper()} "
    return any(word in upper for word in ENTITY_WORDS)


def sale_codes(sales: list[dict[str, Any]]) -> list[str]:
    codes = []
    for sale in sales or []:
        code = clean(sale.get("INSTRTYP") or sale.get("INSTR_TYP") or sale.get("INST_TYPE"))
        if code:
            codes.append(code)
    return sorted(set(codes))


def latest_sale(sales: list[dict[str, Any]]) -> dict[str, Any]:
    return (sales or [{}])[0] if sales else {}


def sale_history_json(sales: list[dict[str, Any]]) -> str:
    compact = []
    for sale in sales or []:
        compact.append(
            {
                "date": clean(sale.get("SALEDATE") or sale.get("SALEDT") or sale.get("SALE_DATE")),
                "price": clean(sale.get("PRICE") or sale.get("SALEPRICE") or sale.get("SALE_PRICE")),
                "instrument_number": clean(sale.get("TRANSNO") or sale.get("TRANS_NO") or sale.get("INSTNO")),
                "instrument_code": clean(sale.get("INSTRTYP") or sale.get("INSTR_TYP") or sale.get("INST_TYPE")),
                "url": clean(sale.get("URL") or sale.get("DOCURL") or sale.get("DOC_URL")),
            }
        )
    return json.dumps(compact, separators=(",", ":"))


def city_tax_url(content: dict[str, Any]) -> str:
    muni = clean(content.get("MUNI_JUR")).upper()
    parid = clean(content.get("PARID"))
    if not parid:
        return ""
    if muni == "MEMPHIS":
        return f"https://epayments.memphistn.gov/Property/Detail.aspx?ParcelNo={parid}"
    if muni in {"BARTLETT", "COLLIERVILLE", "GERMANTOWN", "MILLINGTON", "LAKELAND", "ARLINGTON"}:
        return f"https://apps2.shelbycountytrustee.com/Parcel?parcel={parid}"
    return ""


def tax_map_document_url(content: dict[str, Any]) -> str:
    map_page = clean(content.get("MAP_PAGE"))
    if not map_page:
        return ""
    return f"https://documents.shelbycountytn.gov/REGSAppNet/docpop/docpop.aspx?KT825_0_0_0={parse.quote(map_page)}&KT426_0_0_0=2025&clienttype=html&doctypeid=1962"


def classify(content: dict[str, Any], sales: list[dict[str, Any]], overlays: dict[str, set[str]]) -> tuple[list[str], list[str]]:
    lanes: set[str] = set()
    reasons: list[str] = []
    parcel_key = compact_parcel(content.get("PARID"))
    owner = clean(content.get("OWN1"))
    owner_state = clean(content.get("OSTATECODE")).upper()
    owner_zip_code = owner_zip(content)[:5]
    prop_zip = clean(content.get("ZIP1"))[:5]
    prop_class = clean(content.get("CURR_CLASS")).upper()
    land_use = clean(content.get("LAND_USE")).upper()
    total_value = money(content.get("CURR_TOTAL"))
    codes = set(sale_codes(sales))

    if "tax_sale" in overlays and parcel_key in overlays["tax_sale"]:
        lanes.add("tax-delinquent")
        reasons.append("parcel appears in Shelby Trustee tax-sale extract")
    if "code_violations" in overlays and parcel_key in overlays["code_violations"]:
        lanes.add("code-violations")
        reasons.append("parcel appears in Data Midsouth historical code-enforcement requests")
    if "active_permits" in overlays and parcel_key in overlays["active_permits"]:
        lanes.add("active-permits")
        reasons.append("parcel appears in Data Midsouth Shelby building/demo permits")
    if clean(content.get("ECODE")).upper().find("TAX SALE") >= 0:
        lanes.add("tax-delinquent")
        reasons.append("Register GIS ECODE contains TAX SALE")
    if owner_state and owner_state != "TN":
        lanes.add("absentee")
        reasons.append("owner mailing state is outside Tennessee")
    elif owner_zip_code and prop_zip and owner_zip_code != prop_zip:
        lanes.add("absentee")
        reasons.append("owner mailing ZIP differs from property ZIP")
    if is_entity(owner):
        lanes.add("entity-owned")
        reasons.append("owner name matches entity/institution pattern")
    elif prop_class == "RESIDENTIAL":
        lanes.add("individual-homeowner")
        reasons.append("residential class and owner name does not match entity pattern")
    if "VACANT" in land_use:
        lanes.add("vacant-land")
        reasons.append("land-use text contains VACANT")
    if total_value >= 150000:
        lanes.add("high-equity")
        reasons.append("current total assessed/appraisal value is at or above $150k; debt/free-clear still needs mortgage/deed review")
    if codes.intersection({"PC", "DN"}) or re.search(r"\b(ESTATE|HEIRS?)\b", owner.upper()):
        lanes.add("probate")
        reasons.append("Register sales/owner signal suggests probate/death/estate")
    if codes.intersection({"FJ", "L"}):
        lanes.add("liens")
        reasons.append("Register sales instrument code suggests judgment/taxpayer letter lien signal")
    if codes.intersection({"CH", "D", "TD"}):
        lanes.add("pre-foreclosure")
        reasons.append("Register sales instrument code suggests court/trustee/decree signal; needs quality review")
    return sorted(lanes), reasons


def fetch_dataset(dataset: str, id_field: str, limit: int) -> set[str]:
    rows: set[str] = set()
    offset = 0
    page_size = min(limit, 100) if limit > 0 else 100
    while True:
        if limit > 0 and len(rows) >= limit:
            break
        params = {"limit": page_size, "offset": offset}
        url = f"{DATA_MIDSOUTH}/{dataset}/records?{parse.urlencode(params)}"
        data = json.load(request.urlopen(url, timeout=45))
        results = data.get("results") or []
        if not results:
            break
        for row in results:
            key = compact_parcel(row.get(id_field))
            if key:
                rows.add(key)
        offset += len(results)
        if len(results) < page_size:
            break
    return rows


def tax_sale_keys() -> set[str]:
    candidates = sorted(RAW_ROOT.glob("*/tax-sale-extract.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        return set()
    keys = set()
    with candidates[0].open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.DictReader(handle):
            for field in ("ParcelID", "Alt_Parcel"):
                key = compact_parcel(row.get(field))
                if key:
                    keys.add(key)
    return keys


def normalize(content: dict[str, Any], sales: list[dict[str, Any]], overlays: dict[str, set[str]]) -> dict[str, str]:
    lanes, reasons = classify(content, sales, overlays)
    parid = clean(content.get("PARID"))
    trustee_id = clean(content.get("TRUSTEE_ID"))
    sale = latest_sale(sales)
    source_urls = [
        f"{REGISTER_BASE}/?parcelid={parid}",
        "https://datamidsouth.org/explore/dataset/historical-code-enforcement-requests/",
        "https://datamidsouth.org/explore/dataset/shelby-county-building-and-demolition-permits/",
        "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv",
    ]
    return {
        "parcel_id": parid,
        "parcel_id_compact": compact_parcel(parid),
        "trustee_id": trustee_id,
        "property_address": clean(content.get("PROPERTY_LOCATION")),
        "property_city": clean(content.get("MUNI_JUR")),
        "property_zip": clean(content.get("ZIP1")),
        "municipality": clean(content.get("MUNI_JUR")),
        "map_page": clean(content.get("MAP_PAGE")),
        "neighborhood": clean(content.get("NEIGHBORHOOD")),
        "subdivision": clean(content.get("SUBDIV")),
        "sub_lot": clean(content.get("SUBLOT")),
        "lot_dimensions": clean(content.get("LOTDIM")),
        "calculated_sqft": clean(content.get("CALC_SQFT")),
        "owner_name": clean(content.get("OWN1")),
        "owner_name_2": clean(content.get("OWN2")),
        "owner_mailing_street": owner_street(content),
        "owner_mailing_city": clean(content.get("OCITYNAME")),
        "owner_mailing_state": clean(content.get("OSTATECODE")),
        "owner_mailing_zip": owner_zip(content),
        "owner_address_type": clean(content.get("OADDRTYPE")),
        "owner_country": clean(content.get("OCOUNTRY")),
        "property_class": clean(content.get("CURR_CLASS")),
        "property_use": clean(content.get("LAND_USE")),
        "current_land_value": clean(content.get("CURR_LAND")),
        "current_building_value": clean(content.get("CURR_BLDG")),
        "current_total_value": clean(content.get("CURR_TOTAL")),
        "current_assessed_value": clean(content.get("CURR_ASSESS")),
        "current_greenbelt_land_value": clean(content.get("CURR_GBLAND")),
        "current_greenbelt_total_value": clean(content.get("CURR_GBTOT")),
        "current_greenbelt_assessed_value": clean(content.get("CURR_GBASSESS")),
        "current_homestead_land_value": clean(content.get("CURR_HMLAND")),
        "current_homestead_building_value": clean(content.get("CURR_HMBLDG")),
        "current_partial_value": clean(content.get("CURRVAL_PARTIAL")),
        "prior_class": clean(content.get("PRIOR_CLASS")),
        "prior_land_value": clean(content.get("PRIOR_LAND")),
        "prior_building_value": clean(content.get("PRIOR_BLDG")),
        "prior_total_value": clean(content.get("PRIOR_TOTAL")),
        "prior_assessed_value": clean(content.get("PRIOR_ASSESS")),
        "prior_greenbelt_land_value": clean(content.get("PRIOR_GBLAND")),
        "prior_greenbelt_total_value": clean(content.get("PRIOR_TOTGRBAPR")),
        "prior_greenbelt_assessed_value": clean(content.get("PRIOR_GRBASSESS")),
        "prior_homestead_land_value": clean(content.get("PRIOR_HMLAND")),
        "prior_homestead_building_value": clean(content.get("PRIOR_HMBLDG")),
        "prior_partial_value": clean(content.get("PRIORVAL_PARTIAL")),
        "acres": clean(content.get("ACRES")),
        "year_built": clean(content.get("YRBLT")),
        "stories": clean(content.get("STORIES")),
        "total_rooms": clean(content.get("RMTOT")),
        "bedrooms": clean(content.get("RMBED")),
        "full_baths": clean(content.get("FIXBATH")),
        "half_baths": clean(content.get("FIXHALF")),
        "living_area_sqft": clean(content.get("SFLA")),
        "main_ground_floor_area": clean(content.get("MGFA")),
        "exterior_wall": clean(content.get("EXTWALL_WD")),
        "basement_type": clean(content.get("BASEMENT_TYPE")),
        "heat": clean(content.get("HEAT_WORD")),
        "heat_fuel": clean(content.get("FUEL_WORD")),
        "heat_system": clean(content.get("HEATSYS_WORD")),
        "parking_type": clean(content.get("PARK_TYPE")),
        "wood_burning_fireplaces_opening": clean(content.get("WBFP_O")),
        "wood_burning_fireplaces_prefab": clean(content.get("WBFP_PF")),
        "tax_sale_status": clean(content.get("ECODE")),
        "sales_count": str(len(sales or [])),
        "latest_sale_date": clean(sale.get("SALEDATE") or sale.get("SALEDT") or sale.get("SALE_DATE")),
        "latest_sale_price": clean(sale.get("PRICE") or sale.get("SALEPRICE") or sale.get("SALE_PRICE")),
        "latest_sale_instrument_code": clean(sale.get("INSTRTYP") or sale.get("INSTR_TYP") or sale.get("INST_TYPE")),
        "latest_sale_instrument_number": clean(sale.get("TRANSNO") or sale.get("TRANS_NO") or sale.get("INSTNO")),
        "latest_sale_document_url": clean(sale.get("URL") or sale.get("DOCURL") or sale.get("DOC_URL")),
        "sales_instrument_codes": ",".join(sale_codes(sales)),
        "sales_history_json": sale_history_json(sales),
        "lanes": ",".join(lanes),
        "lane_reasons": " | ".join(reasons),
        "register_gis_url": f"{REGISTER_BASE}/?parcelid={parid}",
        "assessor_property_url": f"https://www.assessormelvinburgess.com/propertyDetails?IR=true&parcelid={parid}",
        "county_tax_url": f"https://apps2.shelbycountytrustee.com/Parcel?parcel={trustee_id or parid}",
        "city_tax_url": city_tax_url(content),
        "tax_map_document_url": tax_map_document_url(content),
        "source_urls": " | ".join(source_urls),
        "public_record_json": json.dumps({"content": content, "sales": sales or []}, separators=(",", ":"), default=str),
    }


def build(prefixes: list[str], max_prefix_rows: int, max_details: int, overlay_limit: int, sleep_seconds: float) -> dict[str, Any]:
    overlays = {
        "tax_sale": tax_sale_keys(),
        "code_violations": fetch_dataset("historical-code-enforcement-requests", "parcel_id", overlay_limit),
        "active_permits": fetch_dataset("shelby-county-building-and-demolition-permits", "parid", overlay_limit),
    }
    seen: set[str] = set()
    rows: list[dict[str, str]] = []
    prefix_counts: dict[str, int] = {}
    for prefix in prefixes:
        hits = register_prefix(prefix, max_prefix_rows)
        prefix_counts[prefix] = len(hits)
        for hit in hits:
            parcel = clean(hit.get("PARID") or hit.get("parcelid") or hit.get("PARCELID"))
            key = compact_parcel(parcel)
            if not parcel or key in seen:
                continue
            seen.add(key)
            details = completedetails(parcel)
            if not details or not details.get("content"):
                continue
            rows.append(normalize(details["content"], details.get("sales") or [], overlays))
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
            if max_details > 0 and len(rows) >= max_details:
                break
        if max_details > 0 and len(rows) >= max_details:
            break

    out_dir = PROCESSED_ROOT / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_csv = out_dir / f"shelby-tn-universal-key-sample-{date.today().isoformat()}.csv"
    out_meta = out_dir / f"shelby-tn-universal-key-sample-{date.today().isoformat()}-meta.json"
    with out_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    lane_counts: dict[str, int] = defaultdict(int)
    for row in rows:
        for lane in row["lanes"].split(","):
            if lane:
                lane_counts[lane] += 1
    meta = {
        "status": "verified_sample",
        "universal_key": "Register GIS PARID / normalized parcel_id; Trustee ID is available per parcel when Register exposes it.",
        "prefixes": prefixes,
        "prefix_counts": prefix_counts,
        "rows_written": len(rows),
        "lane_counts": dict(sorted(lane_counts.items())),
        "overlay_counts": {k: len(v) for k, v in overlays.items()},
        "source_strategy": {
            "base_owner_value_mailing": "https://gis.register.shelby.tn.us/details + /completedetails",
            "tax_sale": "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv plus Register GIS ECODE",
            "code_violations": "Data Midsouth historical-code-enforcement-requests API joined by parcel_id",
            "active_permits": "Data Midsouth shelby-county-building-and-demolition-permits API joined by parid",
            "probate_liens_preforeclosure": "Register sales instrument codes PC/DN/FJ/L/CH/D/TD are useful signals; court/notice sources still need separate quality gate.",
            "not_public_here": "skip-trace phones/emails and DNC status",
        },
        "output_csv": str(out_csv),
    }
    out_meta.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return {**meta, "meta_file": str(out_meta)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prefix", action="append", default=[])
    parser.add_argument("--max-prefix-rows", type=int, default=200)
    parser.add_argument("--max-details", type=int, default=50)
    parser.add_argument("--overlay-limit", type=int, default=1000)
    parser.add_argument("--sleep", type=float, default=0.05)
    args = parser.parse_args()
    prefixes = args.prefix or ["001"]
    print(json.dumps(build(prefixes, args.max_prefix_rows, args.max_details, args.overlay_limit, args.sleep), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
