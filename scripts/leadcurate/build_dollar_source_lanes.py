#!/usr/bin/env python3
"""Build uncapped Dollar Leads lanes from current county source files.

This script intentionally handles the three launch markets whose older outputs
were capped samples. It emits a paid full CSV, a redacted preview, and metadata
for each lane. Every output is one row per parcel.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from process_verified_vacant import MARKETS, process_market


RAW_ROOT = Path("/opt/leadcurate/raw_imports")
PROCESSED_ROOT = Path("/opt/leadcurate/processed")
TODAY = date.today().isoformat()
MECK_VACANT_URL = "https://data.charlottenc.gov/api/download/v1/items/564477f647634c94a6588d1f57597b30/csv?layers=0"
MECK_PARCEL_URL = "https://data.charlottenc.gov/api/download/v1/items/3cf4a8c868f0476f897fed7e1e8e81c2/csv?layers=4"
MECK_LIEN_URL = "https://data.charlottenc.gov/api/download/v1/items/107e93008cbc4430ad2a3afafa839a24/csv?layers=0"
SHELBY_URL = "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv"
FULTON_URL = "https://gisdata.fultoncountyga.gov/api/download/v1/items/ee82525ee33b49778055622c3a3cf534/csv?layers=0"

csv.field_size_limit(2**31 - 1)


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def money(value: Any) -> float:
    try:
        return float(clean(value).replace("$", "").replace(",", ""))
    except ValueError:
        return 0.0


def redact(value: str) -> str:
    return " ".join((part[:1] + "*" * max(2, len(part) - 1)) for part in clean(value).split())


def write_triple(
    market: str,
    slug: str,
    lane: str,
    rows: list[dict[str, Any]],
    output_date: str,
    source_name: str,
    source_url: str,
    source_file: Path,
    source_rows: int,
    parcel_field: str,
    extra_meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out_dir = PROCESSED_ROOT / market / output_date
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{market}-{slug}-{output_date}"
    full_path = out_dir / f"{stem}.csv"
    preview_path = out_dir / f"{stem}-preview.csv"
    meta_path = out_dir / f"{stem}-meta.json"
    fields = list(rows[0]) if rows else [parcel_field]
    with full_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    with preview_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows[:25]:
            out = dict(row)
            for key in fields:
                lowered = key.lower()
                if "owner" in lowered and "state" not in lowered and "type" not in lowered:
                    out[key] = redact(clean(out.get(key))) if clean(out.get(key)) else ""
                if key == parcel_field or "parcel" in lowered or lowered in {"pid", "pin"}:
                    out[key] = "REDACTED"
                if "mailing_address" in lowered or "owner_mailing_street" in lowered:
                    out[key] = "REDACTED"
            writer.writerow(out)
    keys = [clean(row.get(parcel_field)) for row in rows]
    if not keys or any(not key for key in keys) or len(keys) != len(set(keys)):
        raise ValueError(f"{market}/{lane} failed parcel-key uniqueness gate")
    meta = {
        "market": market,
        "lane": lane,
        "processed_date": output_date,
        "source_name": source_name,
        "source_url": source_url,
        "source_file": str(source_file),
        "source_data_status": "current official public source retrieved for this cycle",
        "retrieved_at": output_date,
        "source_total_rows": source_rows,
        "record_count": len(rows),
        "parcel_key_field": parcel_field,
        "duplicate_parcel_keys": 0,
        "outputs": {"full": str(full_path), "preview": str(preview_path), "meta": str(meta_path)},
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        **(extra_meta or {}),
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def build_meck_absentee(source: Path, output_date: str) -> dict[str, Any]:
    rows_by_parcel: dict[str, dict[str, Any]] = {}
    total = 0
    with source.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for raw in csv.DictReader(handle):
            total += 1
            use = clean(raw.get("Property_Use")).lower()
            if not any(token in use for token in ("single", "townhouse", "condo")):
                continue
            value = money(raw.get("Total_Value"))
            if value < 200000:
                continue
            parcel = clean(raw.get("PID"))
            owner = clean(f"{clean(raw.get('Owner_FirstName'))} {clean(raw.get('Owner_LastName'))}")
            state = clean(raw.get("State")).upper()
            mail_city = clean(raw.get("City")).upper()
            location = clean(raw.get("Location"))
            if not parcel or not owner or not state:
                continue
            out_of_state = state != "NC"
            different_city = bool(mail_city and "CHARLOTTE" not in mail_city and "CHARLOTTE" in location.upper())
            if not (out_of_state or different_city):
                continue
            year_text = clean(raw.get("Year_Built"))
            year = int(year_text) if year_text.isdigit() else 0
            score = min(60, value / 10000) + (25 if out_of_state else 0) + (15 if 1900 < year < 1990 else 0)
            row = {
                "rank": 0,
                "score": round(score, 2),
                "owner_name": owner,
                "mailing_address": clean(raw.get("Mailing_Address")),
                "mail_city": mail_city,
                "mail_state": state,
                "mail_zip": clean(raw.get("Zip_Code")),
                "property_address": location,
                "property_use": clean(raw.get("Property_Use")),
                "year_built": year or "",
                "heated_sqft": money(raw.get("Heated_Sqft")) or "",
                "land_value": money(raw.get("Land_Value")),
                "building_value": money(raw.get("Building_Value")),
                "total_value": value,
                "parcel_pid": parcel,
                "is_out_of_state": "yes" if out_of_state else "no",
                "property_url": clean(raw.get("Property_URL")),
                "lane": "absentee_high_value",
                "county": "Mecklenburg",
                "state": "NC",
            }
            previous = rows_by_parcel.get(parcel)
            if previous is None or row["score"] > previous["score"]:
                rows_by_parcel[parcel] = row
    rows = sorted(rows_by_parcel.values(), key=lambda row: (row["score"], row["total_value"], row["parcel_pid"]), reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return write_triple(
        "mecklenburg-nc", "high-value-absentee", "absentee_high_value", rows, output_date,
        "Charlotte Parcel Look Up", MECK_PARCEL_URL, source, total, "parcel_pid",
        {"minimum_total_value": 200000, "filtered_universe": len(rows)},
    )


SUFFIX = {"STREET": "ST", "AVENUE": "AV", "AVE": "AV", "DRIVE": "DR", "ROAD": "RD", "BOULEVARD": "BV", "BLVD": "BV", "LANE": "LN", "COURT": "CT", "CIRCLE": "CR", "PLACE": "PL", "PARKWAY": "PY", "PKWY": "PY", "TERRACE": "TR"}
DIR = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}


def address_key(value: str) -> str:
    text = re.sub(r"[.,#]", " ", clean(value).upper())
    parts = [DIR.get(part, SUFFIX.get(part, part)) for part in text.split()]
    return f"{parts[0]}|{' '.join(parts[1:4])}" if parts else ""


def build_meck_liens(lien_source: Path, parcel_source: Path, output_date: str) -> dict[str, Any]:
    parcels: dict[str, dict[str, str]] = {}
    with parcel_source.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.DictReader(handle):
            key = address_key(clean(row.get("Location")))
            if key and key not in parcels:
                parcels[key] = row
    grouped: dict[str, dict[str, Any]] = {}
    total = 0
    open_rows = 0
    unmatched = 0
    with lien_source.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for lien in csv.DictReader(handle):
            total += 1
            status = clean(lien.get("Lien_Status")).upper()
            if "PAID" in status:
                continue
            open_rows += 1
            parcel = parcels.get(address_key(clean(lien.get("Property_Address"))))
            if not parcel:
                unmatched += 1
                continue
            pid = clean(parcel.get("PID"))
            if not pid:
                unmatched += 1
                continue
            item = grouped.setdefault(pid, {"parcel": parcel, "liens": []})
            item["liens"].append(lien)
    rows: list[dict[str, Any]] = []
    for pid, item in grouped.items():
        parcel = item["parcel"]
        liens = item["liens"]
        statuses = sorted({clean(lien.get("Lien_Status")).upper() for lien in liens if clean(lien.get("Lien_Status"))})
        invoice_dates = [clean(lien.get("Invoice_Date")) for lien in liens if clean(lien.get("Invoice_Date"))]
        total_value = money(parcel.get("Total_Value"))
        mail_state = clean(parcel.get("State")).upper()
        score = 50 + min(40, total_value / 10000) + (25 if mail_state and mail_state != "NC" else 0) + min(20, len(liens) * 2)
        rows.append({
            "rank": 0, "score": round(score, 2), "owner_name": clean(lien_owner(liens, parcel)),
            "property_address": clean(parcel.get("Location")) or clean(liens[0].get("Property_Address")),
            "parcel_id": pid, "lien_count": len(liens),
            "lien_numbers": "; ".join(sorted({clean(x.get("LienNo")) for x in liens if clean(x.get("LienNo"))})),
            "lien_statuses": "; ".join(statuses), "latest_invoice_date": max(invoice_dates, default=""),
            "property_total_value": total_value, "property_land_value": money(parcel.get("Land_Value")),
            "property_building_value": money(parcel.get("Building_Value")), "year_built": clean(parcel.get("Year_Built")),
            "heated_sqft": clean(parcel.get("Heated_Sqft")), "property_use": clean(parcel.get("Property_Use")),
            "owner_mailing_address": clean(parcel.get("Mailing_Address")), "owner_mail_city": clean(parcel.get("City")),
            "owner_mail_state": mail_state, "owner_mail_zip": clean(parcel.get("Zip_Code")),
            "is_out_of_state": "yes" if mail_state and mail_state != "NC" else "no",
            "parcel_record_url": clean(parcel.get("Property_URL")), "lane": "city_lien_active_enriched",
            "county": "Mecklenburg", "state": "NC",
        })
    rows.sort(key=lambda row: (row["score"], row["lien_count"], row["property_total_value"], row["parcel_id"]), reverse=True)
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return write_triple(
        "mecklenburg-nc", "enriched-city-liens", "city_lien_active_enriched", rows, output_date,
        "Charlotte Financial Management System Lien Data joined to Parcel Look Up",
        MECK_LIEN_URL, lien_source, total, "parcel_id",
        {"parcel_source_url": MECK_PARCEL_URL, "parcel_source_file": str(parcel_source), "open_source_rows": open_rows, "unmatched_open_rows": unmatched, "enriched_universe": len(rows)},
    )


def lien_owner(liens: Iterable[dict[str, str]], parcel: dict[str, str]) -> str:
    first = next(iter(liens), {})
    return clean(first.get("Customer_Name")) or clean(f"{parcel.get('Owner_FirstName', '')} {parcel.get('Owner_LastName', '')}")


def build_shelby(source: Path, output_date: str) -> dict[str, Any]:
    rows_by_parcel: dict[str, dict[str, Any]] = {}
    codes: Counter[str] = Counter()
    total = 0
    with source.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for raw in csv.DictReader(handle):
            total += 1
            parcel = clean(raw.get("ParcelID"))
            street = clean(raw.get("Street Name"))
            if not parcel or not street:
                continue
            code = clean(raw.get("Tax Sale"))
            codes[code] += 1
            number = clean(raw.get("Street Number"))
            address = f"{'' if number == '0' else number} {street}".strip()
            score = (60 if code == "TS2302" else 40 if code == "TS2301" else 20) + (30 if number not in {"", "0"} else 0) + (10 if clean(raw.get("Register GIS")).startswith("http") else 0)
            row = {
                "rank": 0, "score": score, "property_address": address, "parcel_id": parcel,
                "alt_parcel_id": clean(raw.get("Alt_Parcel")), "tax_sale_code": code,
                "gis_lookup_url": clean(raw.get("Register GIS")), "lane": "tax_sale_upcoming",
                "county": "Shelby", "state": "TN", "source_url": SHELBY_URL, "source_date": output_date,
            }
            previous = rows_by_parcel.get(parcel)
            if previous is None or score > previous["score"]:
                rows_by_parcel[parcel] = row
    rows = sorted(rows_by_parcel.values(), key=lambda row: (-row["score"], row["parcel_id"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return write_triple(
        "shelby-tn", "tax-sale", "tax_sale_upcoming", rows, output_date,
        "Shelby County Trustee Tax Sale Extract", SHELBY_URL, source, total, "parcel_id",
        {"filtered_universe": len(rows), "tax_sale_breakdown": dict(codes)},
    )


def build_vacant(market: str, source: Path, output_date: str, source_url: str, source_name: str) -> dict[str, Any]:
    cfg = MARKETS[market]
    cfg["output_date"] = output_date
    cfg["source_url"] = source_url
    payload = process_market(market, source, PROCESSED_ROOT / market / output_date, 10**9)
    meta_path = Path(payload["outputs"]["meta"])
    payload.update({
        "source_name": source_name, "source_url": source_url,
        "source_data_status": "current official public source retrieved for this cycle",
        "retrieved_at": output_date, "record_count": payload["exported"],
        "parcel_key_field": "parcel_pid", "duplicate_parcel_keys": 0,
    })
    meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=TODAY)
    parser.add_argument("--raw-root", type=Path, default=RAW_ROOT)
    args = parser.parse_args()
    d = args.date
    results = [
        build_vacant("mecklenburg-nc", args.raw_root / "mecklenburg-nc" / d / "vacant-land.csv", d, MECK_VACANT_URL, "Charlotte Vacant Land"),
        build_meck_absentee(args.raw_root / "mecklenburg-nc" / d / "parcel-lookup.csv", d),
        build_meck_liens(args.raw_root / "mecklenburg-nc" / d / "lien-data.csv", args.raw_root / "mecklenburg-nc" / d / "parcel-lookup.csv", d),
        build_shelby(args.raw_root / "shelby-tn" / d / "tax-sale-extract.csv", d),
        build_vacant("fulton-ga", args.raw_root / "fulton-ga" / d / "tax-parcels-2025.csv", d, FULTON_URL, "Fulton County Tax Parcels 2025"),
    ]
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
