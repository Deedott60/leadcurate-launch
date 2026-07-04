#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any
from urllib import parse, request

RAW_ROOT = Path("/opt/leadcurate/raw_imports")

SOURCES: dict[str, dict[str, Any]] = {
    "davidson-tn": {
        "url": "https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Parcels_view/FeatureServer/0",
        "source_url": "https://datanashvillegov-nashville.hub.arcgis.com/datasets/fa26cd9326c446179be059e00449cb1f_0/about",
        "state": "TN",
        "city": "Nashville",
        "fields": {
            "parcel_id": "STANPAR",
            "owner_name": "Owner",
            "address": "PropAddr",
            "city": "PropCity",
            "zip": "PropZip",
            "mailing_street": "OwnAddr1",
            "mailing_city": "OwnCity",
            "mailing_state": "OwnState",
            "mailing_zip": "OwnZip",
            "value": "TotlAppr",
            "building_value": "ImprAppr",
            "land_value": "LandAppr",
            "acres": "Acres",
        },
    },
    "york-sc": {
        "url": "https://services1.arcgis.com/2AGLxyiJoNiVHKwq/arcgis/rest/services/Parcels/FeatureServer/0",
        "source_url": "https://www.yorkcountysc.gov/239/GIS-Data-Download",
        "state": "SC",
        "city": "York",
        "fields": {
            "parcel_id": "ParcelID",
            "owner_name": "Owner1",
            "secondary_owner": "Owner2",
            "address": "PropertyAddress",
            "mailing_street": "MailAddr1",
            "mailing_city": "MailCity",
            "mailing_state": "MailState",
            "mailing_zip": "MailZip",
            "value": "AprTotVal",
            "building_value": "AprBldgVal",
            "land_value": "AprLandVal",
            "acres": "deededacres",
        },
    },
    "cabarrus-nc": {
        "url": "https://location.cabarruscounty.us/arcgisservices/rest/services/OpenData/Tax_Parcels/MapServer/1",
        "source_url": "https://gis-cabarrus.opendata.arcgis.com/",
        "state": "NC",
        "city": "Concord",
        "where": "AcctName1 is not null and AcctNumber is not null",
        "fields": {
            "parcel_id": "PIN14",
            "owner_name": "AcctName1",
            "secondary_owner": "AcctName2",
            "address": "MailAddr1",
            "mailing_street": "MailAddr1",
            "mailing_city": "MailCity",
            "mailing_state": "MailState",
            "mailing_zip": "MailZipCode",
            "value": "MarketValue",
            "building_value": "BuildingValue",
            "land_value": "LandValue",
            "acres": "CALCULATED_ACREAGE",
        },
    },
    "lancaster-sc": {
        "url": "https://services3.arcgis.com/rJcpRneDUBgTeCT3/arcgis/rest/services/SDE_County_Parcels_Patriot_View/FeatureServer/0",
        "source_url": "https://lancaster-launch-lancogis.hub.arcgis.com/pages/2f49a6ade70a4197bcdaeb3202cedbf7",
        "state": "SC",
        "city": "Lancaster",
        "where": "Owner1 is not null and ParcelID is not null and TotalValue is not null",
        "fields": {
            "parcel_id": "ParcelID",
            "owner_name": "Owner1",
            "secondary_owner": "Owner2",
            "address_parts": ["StreetNum", "StreetName"],
            "city": "City",
            "zip": "Zip",
            "mailing_street": "BillingAddress",
            "mailing_city": "City",
            "mailing_state": "State",
            "mailing_zip": "Zip",
            "value": "TotalValue",
            "building_value": "TotalBuildingBalue",
            "land_value": "TotalLandValue",
            "acres": "TotalAcres",
        },
    },
    "gaston-nc": {
        "url": "https://gis.gastoncountync.gov/publicgis/rest/services/PublicGIS/Parcels/MapServer/11",
        "source_url": "https://gis.gastoncountync.gov/publicgis/rest/services/PublicGIS/Parcels/MapServer/layers",
        "state": "NC",
        "city": "Gastonia",
        "where": "JAN1_NAME1 is not null and AKPAR is not null",
        "fields": {
            "parcel_id": "AKPAR",
            "owner_name": "JAN1_NAME1",
            "secondary_owner": "JAN1_NAME2",
            "address": "WHOLE_ADDRESS",
            "city": "POSTAL",
            "zip": "ZIP",
            "mailing_street": "CURR_ADDR1",
            "mailing_city": "CURR_CITY",
            "mailing_state": "CURR_STATE",
            "mailing_zip": "CURR_ZIPCODE",
            "value": "FMV_TOTAL",
            "building_value": "FMV_IMPRV",
            "land_value": "FMV_LAND",
            "acres": "CALCAC",
        },
    },
    "duval-fl": {
        "url": "https://maps.clayutility.org/server/rest/services/ParcelsHybridv2_LGIM/MapServer/14",
        "source_url": "https://maps.clayutility.org/server/rest/services/ParcelsHybridv2_LGIM/MapServer/14",
        "state": "FL",
        "city": "Jacksonville",
        "fields": {
            "parcel_id": "RE",
            "owner_name": "LNAME",
            "address_parts": ["LOC_ST_NO", "LOC_ST_DIR", "LOC_ST_NAM", "LOC_ST_TYP", "LOC_ST_UNI"],
            "city": "LOC_CITY",
            "zip": "LOC_ZIP",
            "acres": "ACRES",
        },
    },
}

OUTPUT_FIELDS = [
    "parcel_id",
    "owner_name",
    "secondary_owner",
    "address",
    "city",
    "Property ZIP",
    "Mailing Street",
    "Mailing City",
    "Mailing State",
    "Mailing ZIP",
    "value",
    "Building Value",
    "Land Value",
    "Acres",
    "source_url",
]


def clean(value: Any) -> str:
    text = str(value or "").strip()
    if text.endswith(".0"):
        text = text[:-2]
    return " ".join(text.split())


def layer_meta(url: str) -> dict[str, Any]:
    req = request.Request(
        url + "?" + parse.urlencode({"f": "json"}),
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LeadCurate/1.0)",
            "Referer": "https://leadcurate.com/",
        },
    )
    with request.urlopen(req, timeout=30) as res:
        return json.load(res)


def query_page(url: str, offset: int, count: int, order_field: str, out_fields: str, where: str = "1=1") -> list[dict[str, Any]]:
    params = {
        "f": "json",
        "where": where,
        "outFields": out_fields,
        "returnGeometry": "false",
        "resultOffset": offset,
        "resultRecordCount": count,
        "orderByFields": order_field,
    }
    req = request.Request(
        url + "/query?" + parse.urlencode(params),
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LeadCurate/1.0)",
            "Referer": "https://leadcurate.com/",
        },
    )
    with request.urlopen(req, timeout=60) as res:
        data = json.load(res)
    if data.get("error"):
        raise RuntimeError(data["error"])
    return [f["attributes"] for f in data.get("features", [])]


def field_value(row: dict[str, Any], name: str | None) -> str:
    return clean(row.get(name)) if name else ""


def normalize(market: str, row: dict[str, Any]) -> dict[str, str]:
    cfg = SOURCES[market]
    fields = cfg.get("fields") or {}
    if not fields:
        fields = auto_fields(row)
    address = field_value(row, fields.get("address"))
    if not address and fields.get("address_parts"):
        address = " ".join(field_value(row, part) for part in fields["address_parts"] if field_value(row, part))
    return {
        "parcel_id": field_value(row, fields.get("parcel_id")),
        "owner_name": field_value(row, fields.get("owner_name")),
        "secondary_owner": field_value(row, fields.get("secondary_owner")),
        "address": address,
        "city": field_value(row, fields.get("city")) or cfg["city"],
        "Property ZIP": field_value(row, fields.get("zip")),
        "Mailing Street": field_value(row, fields.get("mailing_street")),
        "Mailing City": field_value(row, fields.get("mailing_city")),
        "Mailing State": field_value(row, fields.get("mailing_state")),
        "Mailing ZIP": field_value(row, fields.get("mailing_zip")),
        "value": field_value(row, fields.get("value")),
        "Building Value": field_value(row, fields.get("building_value")),
        "Land Value": field_value(row, fields.get("land_value")),
        "Acres": field_value(row, fields.get("acres")),
        "source_url": cfg["source_url"],
    }


def auto_fields(row: dict[str, Any]) -> dict[str, str]:
    keys = {k.lower(): k for k in row}
    def pick(*names: str) -> str:
        for name in names:
            if name.lower() in keys:
                return keys[name.lower()]
        for key_lower, original in keys.items():
            if any(name.lower() in key_lower for name in names):
                return original
        return ""
    return {
        "parcel_id": pick("parcel", "pin", "pid", "taxid", "account"),
        "owner_name": pick("owner", "ownname", "name1"),
        "secondary_owner": pick("owner2", "name2"),
        "address": pick("siteaddress", "propaddr", "propertyaddress", "location"),
        "city": pick("sitecity", "propcity", "city"),
        "zip": pick("sitezip", "propzip", "zip"),
        "mailing_street": pick("mailaddr", "mailing", "ownaddr"),
        "mailing_city": pick("mailcity", "owncity"),
        "mailing_state": pick("mailstate", "ownstate"),
        "mailing_zip": pick("mailzip", "ownzip"),
        "value": pick("totalvalue", "totlappr", "marketvalue", "assessed", "value"),
        "building_value": pick("building", "impr", "bldg"),
        "land_value": pick("land"),
        "acres": pick("acres", "acreage"),
    }


def pull(market: str, limit: int) -> dict[str, Any]:
    cfg = SOURCES[market]
    meta = layer_meta(cfg["url"])
    fields = [f["name"] for f in meta.get("fields", []) if f.get("type") != "esriFieldTypeGeometry"]
    oid = next((f["name"] for f in meta.get("fields", []) if f.get("type") == "esriFieldTypeOID"), fields[0])
    page_size = min(int(meta.get("maxRecordCount") or 1000), 2000)
    rows: list[dict[str, str]] = []
    offset = 0
    while len(rows) < limit:
        page = query_page(cfg["url"], offset, min(page_size, limit - len(rows)), oid, ",".join(fields), cfg.get("where", "1=1"))
        if not page:
            break
        for raw in page:
            rec = normalize(market, raw)
            if rec["parcel_id"] and rec["owner_name"] and rec["address"]:
                rows.append(rec)
        offset += page_size
    out_dir = RAW_ROOT / market / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "parcels.csv"
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return {"ok": True, "market": market, "source": cfg["url"], "rows": len(rows), "csv": str(out_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, choices=sorted(SOURCES))
    parser.add_argument("--limit", type=int, default=5000)
    args = parser.parse_args()
    print(json.dumps(pull(args.market, args.limit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
