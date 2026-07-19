#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import request

PROCESSED_ROOT = Path("/opt/leadcurate/processed/shelby-tn")
REGISTER_BASE = "https://gis.register.shelby.tn.us"
TRUSTEE_BASE = "https://apps2.shelbycountytrustee.com/Parcel?parcel="

OUTPUT_FIELDS = [
    "rank",
    "score",
    "property_address",
    "parcel_id",
    "alt_parcel_id",
    "tax_sale_code",
    "owner_name",
    "owner_name_2",
    "owner_mailing_street",
    "owner_mailing_city",
    "owner_mailing_state",
    "owner_mailing_zip",
    "property_class",
    "property_use",
    "current_land_value",
    "current_building_value",
    "current_total_value",
    "current_assessed_value",
    "acres",
    "trustee_id",
    "tax_sale_status",
    "delinquent_balance",
    "sale_auction_status",
    "gis_lookup_url",
    "register_gis_source_url",
    "trustee_lookup_url",
    "tax_sale_extract_source_url",
    "source_date",
    "enrichment_status",
    "enrichment_notes",
]


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def money_text(value: Any) -> str:
    return clean(value)


def latest_snapshot() -> Path:
    candidates = sorted(PROCESSED_ROOT.glob("*/shelby-tn-tax-sale-*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    candidates = [p for p in candidates if "preview" not in p.name and "enriched" not in p.name]
    if not candidates:
        raise FileNotFoundError("No Shelby processed tax-sale snapshot found")
    return candidates[0]


def output_dir_for(path: Path) -> Path:
    return path.parent


def register_post(endpoint: str, payload: dict[str, Any], timeout: int = 30) -> Any:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        f"{REGISTER_BASE}{endpoint}",
        data=body,
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


def normalize_parcel(parcel_id: str) -> str:
    return clean(parcel_id)


def fetch_register_details(parcel_id: str) -> dict[str, Any]:
    parcel = normalize_parcel(parcel_id)
    data = register_post("/completedetails", {"parcelid": parcel})
    if isinstance(data, dict) and data.get("content"):
        return data
    search = register_post("/details", {"searchtype": "parcelID", "parcelid": parcel})
    if isinstance(search, list) and search:
        parid = clean(search[0].get("PARID") or search[0].get("parcelid") or search[0].get("PARCELID"))
        if parid:
            data = register_post("/completedetails", {"parcelid": parid})
            if isinstance(data, dict) and data.get("content"):
                return data
    return {"error": True}


def owner_street(content: dict[str, Any]) -> str:
    explicit = clean(" ".join(clean(content.get(k)) for k in ["OADDR1", "OADDR2", "OADDR3"] if clean(content.get(k))))
    if explicit:
        return explicit
    parts = [
        content.get("OADRNO"),
        content.get("OADRDIR"),
        content.get("OADRSTR"),
        content.get("OADRSUF"),
        content.get("OADRSUF2"),
        content.get("OUNITDESC"),
        content.get("OUNITNO"),
    ]
    return clean(" ".join(clean(p) for p in parts if clean(p)))


def owner_zip(content: dict[str, Any]) -> str:
    zip1 = clean(content.get("ZIP1"))
    zip2 = clean(content.get("ZIP2"))
    return f"{zip1}-{zip2}" if zip1 and zip2 else zip1


def enrich_row(row: dict[str, str]) -> dict[str, str]:
    notes: list[str] = []
    details = fetch_register_details(row["parcel_id"])
    content = details.get("content") if isinstance(details, dict) else None
    if not content:
        out = {field: "" for field in OUTPUT_FIELDS}
        out.update({k: row.get(k, "") for k in row})
        out["tax_sale_extract_source_url"] = row.get("source_url", "")
        out["register_gis_source_url"] = REGISTER_BASE
        out["trustee_lookup_url"] = ""
        out["enrichment_status"] = "register_gis_not_found"
        out["enrichment_notes"] = "Register GIS did not return parcel details for this parcel_id."
        return out

    trustee_id = clean(content.get("TRUSTEE_ID"))
    if trustee_id:
        notes.append("Trustee parcel id found, but tax balance automation is blocked by the Trustee site's legacy TLS handshake on the VPS.")
    notes.append("Owner/value/class/use fields came from Shelby Register GIS /completedetails.")
    notes.append("Contact phone/email and skip trace data are not public-record fields in this source.")

    out = {
        "rank": row.get("rank", ""),
        "score": row.get("score", ""),
        "property_address": clean(content.get("PROPERTY_LOCATION")) or row.get("property_address", ""),
        "parcel_id": row.get("parcel_id", ""),
        "alt_parcel_id": row.get("alt_parcel_id", ""),
        "tax_sale_code": row.get("tax_sale_code", ""),
        "owner_name": clean(content.get("OWN1")),
        "owner_name_2": clean(content.get("OWN2")),
        "owner_mailing_street": owner_street(content),
        "owner_mailing_city": clean(content.get("OCITYNAME")),
        "owner_mailing_state": clean(content.get("OSTATECODE")),
        "owner_mailing_zip": owner_zip(content),
        "property_class": clean(content.get("CURR_CLASS")),
        "property_use": clean(content.get("LAND_USE")),
        "current_land_value": money_text(content.get("CURR_LAND")),
        "current_building_value": money_text(content.get("CURR_BLDG")),
        "current_total_value": money_text(content.get("CURR_TOTAL")),
        "current_assessed_value": money_text(content.get("CURR_ASSESS")),
        "acres": clean(content.get("ACRES")),
        "trustee_id": trustee_id,
        "tax_sale_status": clean(content.get("ECODE")),
        "delinquent_balance": "",
        "sale_auction_status": "",
        "gis_lookup_url": row.get("gis_lookup_url", ""),
        "register_gis_source_url": f"{REGISTER_BASE}/?parcelid={row.get('parcel_id', '')}",
        "trustee_lookup_url": f"{TRUSTEE_BASE}{trustee_id}" if trustee_id else "",
        "tax_sale_extract_source_url": row.get("source_url", ""),
        "source_date": row.get("source_date", ""),
        "enrichment_status": "verified_register_gis",
        "enrichment_notes": " ".join(notes),
    }
    return out


def compact_before_after(before: dict[str, str], after: dict[str, str]) -> dict[str, Any]:
    return {
        "before": {
            "parcel_id": before.get("parcel_id", ""),
            "property_address": before.get("property_address", ""),
            "tax_sale_code": before.get("tax_sale_code", ""),
            "owner_name": before.get("owner_name", ""),
            "owner_mailing_street": before.get("owner_mailing_street", ""),
            "current_total_value": before.get("current_total_value", ""),
        },
        "after": {
            "parcel_id": after.get("parcel_id", ""),
            "property_address": after.get("property_address", ""),
            "tax_sale_code": after.get("tax_sale_code", ""),
            "owner_name": after.get("owner_name", ""),
            "owner_mailing_street": after.get("owner_mailing_street", ""),
            "owner_mailing_city": after.get("owner_mailing_city", ""),
            "owner_mailing_state": after.get("owner_mailing_state", ""),
            "owner_mailing_zip": after.get("owner_mailing_zip", ""),
            "property_class": after.get("property_class", ""),
            "property_use": after.get("property_use", ""),
            "current_total_value": after.get("current_total_value", ""),
            "current_assessed_value": after.get("current_assessed_value", ""),
            "tax_sale_status": after.get("tax_sale_status", ""),
        },
    }


def enrich(input_path: Path, limit: int, sleep_seconds: float, workers: int = 1) -> dict[str, Any]:
    with input_path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        rows = list(csv.DictReader(handle))
    selected = rows[:limit] if limit > 0 else rows
    enriched: list[dict[str, str]] = []
    before_after: list[dict[str, Any]] = []
    def run(row: dict[str, str]) -> dict[str, str]:
        out = enrich_row(row)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
        return out

    if workers > 1:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = executor.map(run, selected)
            paired = zip(selected, results)
            for row, out in paired:
                enriched.append(out)
                if len(before_after) < 10:
                    before_after.append(compact_before_after(row, out))
    else:
        for row in selected:
            out = run(row)
            enriched.append(out)
            if len(before_after) < 10:
                before_after.append(compact_before_after(row, out))

    out_dir = output_dir_for(input_path)
    date_part = out_dir.name
    out_path = out_dir / f"shelby-tn-tax-sale-{date_part}-enriched.csv"
    meta_path = out_dir / f"shelby-tn-tax-sale-{date_part}-enriched-meta.json"
    before_after_path = out_dir / f"shelby-tn-tax-sale-{date_part}-before-after.json"
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(enriched)

    owner_count = sum(1 for row in enriched if clean(row.get("owner_name")))
    mailing_count = sum(1 for row in enriched if clean(row.get("owner_mailing_street")))
    value_count = sum(1 for row in enriched if clean(row.get("current_total_value")))
    meta = {
        "status": "partial" if owner_count < len(enriched) else "verified",
        "input_file": str(input_path),
        "output_file": str(out_path),
        "rows_attempted": len(selected),
        "rows_enriched_owner": owner_count,
        "rows_enriched_mailing": mailing_count,
        "rows_enriched_value": value_count,
        "sources_checked": {
            "tax_sale_extract": "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv",
            "register_gis_page": "https://gis.register.shelby.tn.us/",
            "register_gis_details_endpoint": "https://gis.register.shelby.tn.us/completedetails",
            "register_gis_search_endpoint": "https://gis.register.shelby.tn.us/details",
            "assessor_property_search": "https://assessormelvinburgess.com/propertySearch",
            "trustee_tax_lookup": "https://www.shelbycountytrustee.com/103/Tax-Look-Up",
            "trustee_parcel_endpoint": "https://apps2.shelbycountytrustee.com/Parcel?parcel=<trustee_id>",
            "memphis_311_parcel_layer": "https://311.memphistn.gov/server/rest/services/311/ParcelCentroids/MapServer/1",
        },
        "field_provenance": {
            "tax_sale_extract": ["parcel_id", "alt_parcel_id", "property_address", "tax_sale_code", "gis_lookup_url", "source_date"],
            "register_gis_completedetails": [
                "owner_name",
                "owner_name_2",
                "owner_mailing_street",
                "owner_mailing_city",
                "owner_mailing_state",
                "owner_mailing_zip",
                "property_class",
                "property_use",
                "current_land_value",
                "current_building_value",
                "current_total_value",
                "current_assessed_value",
                "acres",
                "trustee_id",
                "tax_sale_status",
            ],
            "unavailable_without_other_source": ["contact_phone", "contact_email", "skip_trace_phone", "DNC_status"],
            "not_automated_from_vps": ["delinquent_balance", "sale_auction_status"],
        },
        "limitations": [
            "Shelby Assessor propertySearch returned HTTP 403 from the VPS during direct automation checks.",
            "Trustee parcel endpoint failed TLS handshake from the VPS with OpenSSL unsafe legacy renegotiation disabled, so tax balance is not populated by this script.",
            "Memphis 311 parcel ArcGIS layer is queryable but only exposes parcel geometry/basic parcel fields, not owner/value/mailing details.",
        ],
        "customer_explanation": "Shelby publishes the current tax-sale property list, but the extract does not include owner/contact data. LeadCurate identifies properties in the tax-sale cycle first, then enriches ownership and mailing details through parcel/GIS/assessor lookups where public records expose them.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    before_after_path.write_text(json.dumps(before_after, indent=2), encoding="utf-8")
    return {**meta, "meta_file": str(meta_path), "before_after_file": str(before_after_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--sleep", type=float, default=0.1)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    input_path = args.input or latest_snapshot()
    if args.workers < 1 or args.workers > 32:
        parser.error("--workers must be between 1 and 32")
    result = enrich(input_path, args.limit, args.sleep, args.workers)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
