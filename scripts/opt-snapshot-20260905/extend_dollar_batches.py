#!/usr/bin/env python3
"""Extend the existing 2026-07 Dollar Leads cycle with lanes cut from
already-verified processed files. Merges into the existing inventory.json
rather than overwriting, and never touches existing lane directories
(mkdir exist_ok=False guards every lane)."""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

PROCESSED = Path("/opt/leadcurate/processed")
ROOT = Path("/opt/leadcurate/dollar_batches")
CYCLE = "July 2026"
CYCLE_SLUG = "2026-07"

csv.field_size_limit(2**31 - 1)


def seg_filter(value):
    return lambda row: row.get("lc_property_segment", "").strip().lower() == value


NEW_SOURCES = [
    # market, lane_dir, filename, market_display, lane, lane_display, source_name, source_url, key_fields, row_filter, batch_size
    ("dallas-tx", "2026-07-16/industrial-multifamily-distress", "dallas-tx-industrial-multifamily-distress-2026-07-16.csv", "Dallas County TX", "office", "Office property owners", "Dallas Central Appraisal District 2026 current package", "https://www.dallascad.org/ViewPDFs.aspx?type=3&id=1", ["lc_parcel_id", "ACCOUNT_NUM"], seg_filter("office"), 500),
    ("dallas-tx", "2026-07-16/industrial-multifamily-distress", "dallas-tx-industrial-multifamily-distress-2026-07-16.csv", "Dallas County TX", "industrial", "Industrial property owners", "Dallas Central Appraisal District 2026 current package", "https://www.dallascad.org/ViewPDFs.aspx?type=3&id=1", ["lc_parcel_id", "ACCOUNT_NUM"], seg_filter("industrial"), 500),
    ("dallas-tx", "2026-07-16/industrial-multifamily-distress", "dallas-tx-industrial-multifamily-distress-2026-07-16.csv", "Dallas County TX", "multifamily", "Multifamily owners", "Dallas Central Appraisal District 2026 current package", "https://www.dallascad.org/ViewPDFs.aspx?type=3&id=1", ["lc_parcel_id", "ACCOUNT_NUM"], seg_filter("multifamily"), 500),
    ("massachusetts-statewide", "2026-07-16/industrial-multifamily-distress", "massachusetts-statewide-industrial-multifamily-distress-2026-07-16.csv", "Massachusetts (statewide)", "office", "Office property owners", "MassGIS Level 3 standardized parcels", "https://www.mass.gov/info-details/massgis-data-property-tax-parcels", ["lc_parcel_id", "LC_PARCEL_KEY"], seg_filter("office"), 500),
    ("massachusetts-statewide", "2026-07-16/industrial-multifamily-distress", "massachusetts-statewide-industrial-multifamily-distress-2026-07-16.csv", "Massachusetts (statewide)", "industrial", "Industrial property owners", "MassGIS Level 3 standardized parcels", "https://www.mass.gov/info-details/massgis-data-property-tax-parcels", ["lc_parcel_id", "LC_PARCEL_KEY"], seg_filter("industrial"), 500),
    ("massachusetts-statewide", "2026-07-16/industrial-multifamily-distress", "massachusetts-statewide-industrial-multifamily-distress-2026-07-16.csv", "Massachusetts (statewide)", "multifamily", "Multifamily owners", "MassGIS Level 3 standardized parcels", "https://www.mass.gov/info-details/massgis-data-property-tax-parcels", ["lc_parcel_id", "LC_PARCEL_KEY"], seg_filter("multifamily"), 500),
    ("cook-il", "2026-07-16/industrial-multifamily-distress", "cook-il-industrial-multifamily-distress-2026-07-16.csv", "Cook County IL", "office", "Office property owners", "Cook County Assessor open data", "https://datacatalog.cookcountyil.gov/", ["lc_parcel_id", "parcel_key", "U_PIN"], seg_filter("office"), 500),
    ("cook-il", "2026-07-16/industrial-multifamily-distress", "cook-il-industrial-multifamily-distress-2026-07-16.csv", "Cook County IL", "industrial", "Industrial property owners", "Cook County Assessor open data", "https://datacatalog.cookcountyil.gov/", ["lc_parcel_id", "parcel_key", "U_PIN"], seg_filter("industrial"), 500),
    ("wayne-mi", "2026-07-16/out-of-state-owners", "wayne-mi-out-of-state-owners-2026-07-16.csv", "Wayne County MI", "out-of-state-owners", "Out-of-state owners", "Wayne County 2026 assessments plus Detroit current parcel service", "https://www.waynecountymi.gov/Government/Departments/Management-Budget/Assessment-Equalization/Annual-Assessment-Data", ["lc_parcel_id", "parcel_id", "parcel_key"], None, 500),
    ("wayne-mi", "2026-07-16/industrial-multifamily-distress", "wayne-mi-industrial-multifamily-distress-2026-07-16.csv", "Wayne County MI", "income-property", "Office / industrial / multifamily owners", "Wayne County 2026 assessments plus Detroit current parcel service", "https://www.waynecountymi.gov/Government/Departments/Management-Budget/Assessment-Equalization/Annual-Assessment-Data", ["lc_parcel_id", "parcel_id", "parcel_key"], None, 500),
    ("wayne-mi", "2026-07-16/blight-pressure", "detroit-mi-blight-pressure-2026-07-16.csv", "Wayne County MI", "blight-pressure", "Blight-pressure properties (Detroit)", "Detroit open data blight tickets matched to current parcels", "https://data.detroitmi.gov/", ["lc_parcel_id", "parcel_id", "parcel_key"], None, 500),
    ("mecklenburg-nc", "2026-07-19", "mecklenburg-nc-enriched-city-liens-2026-07-19.csv", "Mecklenburg County NC (Charlotte)", "city-liens", "City lien properties", "Charlotte FMS Lien Data joined to Parcel Look Up", "https://data.charlottenc.gov/datasets/charlotte::financial-management-system-lien-data", ["parcel_id", "parcel_pid"], None, 100),
]


def parcel_key(row, fields):
    for field in fields:
        value = "".join(str(row.get(field, "")).upper().split())
        if value:
            return value
    return ""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cut(market, lane_dir, filename, market_display, lane, lane_display, source_name, source_url, key_fields, row_filter, batch_size):
    source_path = PROCESSED / market / lane_dir / filename
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    destination = ROOT / CYCLE_SLUG / market / lane
    destination.mkdir(parents=True, exist_ok=False)
    seen, buffer, batches = set(), [], []
    eligible = skipped_dupes = 0
    fields = []
    with source_path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        for row in reader:
            if row_filter and not row_filter(row):
                continue
            key = parcel_key(row, key_fields)
            if not key:
                continue
            if key in seen:
                skipped_dupes += 1
                continue
            seen.add(key)
            eligible += 1
            buffer.append(row)
            if len(buffer) == batch_size:
                batch_no = len(batches) + 1
                path = destination / f"batch-{batch_no:05d}.csv"
                with path.open("w", newline="", encoding="utf-8") as out:
                    writer = csv.DictWriter(out, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(buffer)
                batches.append({"batch_no": batch_no, "size": batch_size, "file": str(path), "sha256": sha256(path), "first_parcel_key": parcel_key(buffer[0], key_fields), "last_parcel_key": parcel_key(buffer[-1], key_fields)})
                buffer = []
    db_rows = [{"market": market, "market_display": market_display, "lane": lane, "lane_display": lane_display, "batch_no": b["batch_no"], "size": batch_size, "seats_total": 3, "seats_sold": 0, "cycle": CYCLE, "status": "live"} for b in batches]
    manifest = {"market": market, "market_display": market_display, "lane": lane, "lane_display": lane_display, "source_name": source_name, "source_url": source_url, "source_file": str(source_path), "source_sha256": sha256(source_path), "pull_cycle": CYCLE, "eligible_records": eligible, "batch_count": len(batches), "batched_records": sum(b["size"] for b in batches), "remainder_records": len(buffer), "parcel_key_fields": key_fields, "duplicate_parcel_keys": skipped_dupes, "batches": batches}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest, db_rows


def main():
    cycle_dir = ROOT / CYCLE_SLUG
    inv_path = cycle_dir / "inventory.json"
    inventory = json.loads(inv_path.read_text(encoding="utf-8"))
    existing = {(l["market"], l["lane"]) for l in inventory["lanes"]}
    new_manifests, new_rows = [], []
    for cfg in NEW_SOURCES:
        market, lane = cfg[0], cfg[4]
        if (market, lane) in existing:
            print(f"SKIP existing: {market}/{lane}")
            continue
        manifest, rows = cut(*cfg)
        new_manifests.append(manifest)
        new_rows.extend(rows)
        print(f"{market}/{lane}: {manifest['batch_count']} batches ({manifest['eligible_records']} eligible, {manifest['duplicate_parcel_keys']} dupes skipped, {manifest['remainder_records']} remainder)")
    inventory["lanes"].extend(new_manifests)
    inventory["lane_count"] = len(inventory["lanes"])
    inventory["batch_count"] = inventory.get("batch_count", 0) + len(new_rows)
    inventory["extended_at_utc"] = datetime.now(timezone.utc).isoformat()
    inv_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    (cycle_dir / "dollar_batches_rows_extension_1.json").write_text(json.dumps(new_rows, indent=2), encoding="utf-8")
    print(json.dumps({"new_lanes": len(new_manifests), "new_batches": len(new_rows)}))


if __name__ == "__main__":
    main()
