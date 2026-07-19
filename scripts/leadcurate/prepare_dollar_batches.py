#!/usr/bin/env python3
"""Cut verified full lane files into disjoint 500-record Dollar Leads batches."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator


PROCESSED = Path("/opt/leadcurate/processed")
DEFAULT_ROOT = Path("/opt/leadcurate/dollar_batches")
BATCH_SIZE = 500


def source(market: str, lane_dir: str, filename: str, market_display: str, lane: str, lane_display: str, source_name: str, source_url: str, key_fields: list[str], row_filter: Callable[[dict[str, str]], bool] | None = None) -> dict[str, Any]:
    return locals()


SOURCES = [
    source("dallas-tx", "2026-07-16/tired-landlords", "dallas-tx-tired-landlords-2026-07-16.csv", "Dallas County TX", "tired-landlords", "Long-hold landlords", "Dallas Central Appraisal District 2026 current package", "https://www.dallascad.org/ViewPDFs.aspx?type=3&id=1", ["lc_parcel_id", "ACCOUNT_NUM"]),
    source("dallas-tx", "2026-07-16/out-of-state-owners", "dallas-tx-out-of-state-owners-2026-07-16.csv", "Dallas County TX", "out-of-state-owners", "Out-of-state owners", "Dallas Central Appraisal District 2026 current package", "https://www.dallascad.org/ViewPDFs.aspx?type=3&id=1", ["lc_parcel_id", "ACCOUNT_NUM"]),
    source("dallas-tx", "2026-07-16/verified-vacant-land", "dallas-tx-verified-vacant-land-2026-07-16.csv", "Dallas County TX", "verified-vacant-land", "Vacant land", "Dallas Central Appraisal District 2026 current package", "https://www.dallascad.org/ViewPDFs.aspx?type=3&id=1", ["lc_parcel_id", "ACCOUNT_NUM"]),
    source("wayne-mi", "2026-07-16/tired-landlords", "wayne-mi-tired-landlords-2026-07-16.csv", "Wayne County MI", "tired-landlords", "Long-hold landlords", "Wayne County 2026 assessments plus Detroit current parcel service", "https://www.waynecountymi.gov/Government/Departments/Management-Budget/Assessment-Equalization/Annual-Assessment-Data", ["lc_parcel_id", "parcel_id", "parcel_key"]),
    source("wayne-mi", "2026-07-16/verified-vacant-land", "wayne-mi-verified-vacant-land-2026-07-16.csv", "Wayne County MI", "verified-vacant-land", "Vacant land", "Wayne County 2026 assessments plus Detroit current parcel service", "https://www.waynecountymi.gov/Government/Departments/Management-Budget/Assessment-Equalization/Annual-Assessment-Data", ["lc_parcel_id", "parcel_id", "parcel_key"]),
    source("wayne-mi", "2026-07-16/tax-delinquent", "wayne-mi-tax-delinquent-2026-07-16.csv", "Wayne County MI", "tax-debt", "Live tax-debt owners", "Wayne County Treasurer live parcel lookup", "https://pta.waynecounty.com/", ["parcel_key", "parcel_id"]),
    source("cook-il", "2026-07-16/tired-landlords", "cook-il-tired-landlords-2026-07-16.csv", "Cook County IL", "tired-landlords", "Long-hold landlords", "Cook County Assessor open data", "https://datacatalog.cookcountyil.gov/", ["lc_parcel_id", "parcel_key", "U_PIN"]),
    source("cook-il", "2026-07-16/out-of-state-owners", "cook-il-out-of-state-owners-2026-07-16.csv", "Cook County IL", "out-of-state-owners", "Out-of-state owners", "Cook County Assessor open data", "https://datacatalog.cookcountyil.gov/", ["lc_parcel_id", "parcel_key", "U_PIN"]),
    source("cook-il", "2026-07-16/verified-vacant-land", "cook-il-verified-vacant-land-2026-07-16.csv", "Cook County IL", "verified-vacant-land", "Vacant land", "Cook County Assessor open data", "https://datacatalog.cookcountyil.gov/", ["lc_parcel_id", "parcel_key", "U_PIN"]),
    source("cook-il", "2026-07-16/industrial-multifamily-distress", "cook-il-industrial-multifamily-distress-2026-07-16.csv", "Cook County IL", "multifamily", "Multifamily owners", "Cook County Assessor open data", "https://datacatalog.cookcountyil.gov/", ["lc_parcel_id", "parcel_key", "U_PIN"], lambda row: row.get("lc_property_segment", "").lower() == "multifamily"),
    source("massachusetts-statewide", "2026-07-16/tired-landlords", "massachusetts-statewide-tired-landlords-2026-07-16.csv", "Massachusetts (statewide)", "tired-landlords", "Long-hold landlords", "MassGIS Level 3 standardized parcels", "https://www.mass.gov/info-details/massgis-data-property-tax-parcels", ["lc_parcel_id", "LC_PARCEL_KEY"]),
    source("massachusetts-statewide", "2026-07-16/out-of-state-owners", "massachusetts-statewide-out-of-state-owners-2026-07-16.csv", "Massachusetts (statewide)", "out-of-state-owners", "Out-of-state owners", "MassGIS Level 3 standardized parcels", "https://www.mass.gov/info-details/massgis-data-property-tax-parcels", ["lc_parcel_id", "LC_PARCEL_KEY"]),
    source("massachusetts-statewide", "2026-07-16/verified-vacant-land", "massachusetts-statewide-verified-vacant-land-2026-07-16.csv", "Massachusetts (statewide)", "verified-vacant-land", "Vacant land", "MassGIS Level 3 standardized parcels", "https://www.mass.gov/info-details/massgis-data-property-tax-parcels", ["lc_parcel_id", "LC_PARCEL_KEY"]),
    source("mecklenburg-nc", "{date}", "mecklenburg-nc-verified-vacant-{date}.csv", "Mecklenburg County NC (Charlotte)", "verified-vacant-land", "Vacant land", "Charlotte Vacant Land", "https://data.charlottenc.gov/datasets/charlotte::vacant-land", ["parcel_pid"]),
    source("mecklenburg-nc", "{date}", "mecklenburg-nc-high-value-absentee-{date}.csv", "Mecklenburg County NC (Charlotte)", "high-value-absentee", "High-value absentee owners", "Charlotte Parcel Look Up", "https://data.charlottenc.gov/datasets/charlotte::parcel-look-up", ["parcel_pid"]),
    source("mecklenburg-nc", "{date}", "mecklenburg-nc-enriched-city-liens-{date}.csv", "Mecklenburg County NC (Charlotte)", "city-liens", "City lien properties", "Charlotte FMS Lien Data joined to Parcel Look Up", "https://data.charlottenc.gov/datasets/charlotte::financial-management-system-lien-data", ["parcel_id"]),
    source("shelby-tn", "{date}", "shelby-tn-tax-sale-{date}-enriched.csv", "Shelby County TN (Memphis)", "tax-sale", "Tax-sale properties", "Shelby County Trustee Tax Sale Extract plus Register GIS", "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv", ["parcel_id"]),
    source("fulton-ga", "{date}", "fulton-ga-verified-vacant-{date}.csv", "Fulton County GA (Atlanta)", "verified-vacant-land", "Vacant land", "Fulton County Tax Parcels 2025", "https://gisdata.fultoncountyga.gov/datasets/ee82525ee33b49778055622c3a3cf534", ["parcel_pid"]),
]


def parcel_key(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = "".join(str(row.get(field, "")).upper().split())
        if value:
            return value
    return ""


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def cut_lane(cfg: dict[str, Any], processed_root: Path, output_root: Path, cycle: str, cycle_slug: str, run_date: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    lane_dir = cfg["lane_dir"].format(date=run_date)
    filename = cfg["filename"].format(date=run_date)
    source_path = processed_root / cfg["market"] / lane_dir / filename
    if not source_path.exists():
        raise FileNotFoundError(source_path)
    destination = output_root / cycle_slug / cfg["market"] / cfg["lane"]
    destination.mkdir(parents=True, exist_ok=False)
    seen: set[str] = set()
    buffer: list[dict[str, str]] = []
    batches: list[dict[str, Any]] = []
    eligible = 0
    fields: list[str] = []
    row_filter = cfg.get("row_filter")
    with source_path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        fields = list(reader.fieldnames or [])
        for row in reader:
            if row_filter and not row_filter(row):
                continue
            key = parcel_key(row, cfg["key_fields"])
            if not key:
                raise ValueError(f"blank parcel key in {source_path}")
            if key in seen:
                raise ValueError(f"duplicate parcel key {key} in {source_path}")
            seen.add(key)
            eligible += 1
            buffer.append(row)
            if len(buffer) == BATCH_SIZE:
                batch_no = len(batches) + 1
                path = destination / f"batch-{batch_no:05d}.csv"
                with path.open("w", newline="", encoding="utf-8") as out:
                    writer = csv.DictWriter(out, fieldnames=fields)
                    writer.writeheader()
                    writer.writerows(buffer)
                batches.append({"batch_no": batch_no, "size": BATCH_SIZE, "file": str(path), "sha256": file_sha256(path), "first_parcel_key": parcel_key(buffer[0], cfg["key_fields"]), "last_parcel_key": parcel_key(buffer[-1], cfg["key_fields"])})
                buffer = []
    db_rows = [{
        "market": cfg["market"], "market_display": cfg["market_display"],
        "lane": cfg["lane"], "lane_display": cfg["lane_display"],
        "batch_no": batch["batch_no"], "size": BATCH_SIZE,
        "seats_total": 3, "seats_sold": 0, "cycle": cycle, "status": "live",
    } for batch in batches]
    manifest = {
        "market": cfg["market"], "market_display": cfg["market_display"],
        "lane": cfg["lane"], "lane_display": cfg["lane_display"],
        "source_name": cfg["source_name"], "source_url": cfg["source_url"],
        "source_file": str(source_path), "source_sha256": file_sha256(source_path),
        "pull_cycle": cycle, "eligible_records": eligible,
        "batch_count": len(batches), "batched_records": len(batches) * BATCH_SIZE,
        "remainder_records": len(buffer), "parcel_key_fields": cfg["key_fields"],
        "duplicate_parcel_keys": 0, "batches": batches,
    }
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest, db_rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--cycle", default=datetime.now().strftime("%B %Y"))
    parser.add_argument("--cycle-slug", default=datetime.now().strftime("%Y-%m"))
    parser.add_argument("--processed-root", type=Path, default=PROCESSED)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    cycle_dir = args.output_root / args.cycle_slug
    if cycle_dir.exists():
        raise FileExistsError(f"cycle output already exists: {cycle_dir}")
    manifests: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for cfg in SOURCES:
        manifest, db_rows = cut_lane(cfg, args.processed_root, args.output_root, args.cycle, args.cycle_slug, args.date)
        manifests.append(manifest)
        rows.extend(db_rows)
        print(f"{cfg['market']}/{cfg['lane']}: {manifest['batch_count']} batches ({manifest['eligible_records']} eligible, {manifest['remainder_records']} remainder)")
    summary = {"cycle": args.cycle, "cycle_slug": args.cycle_slug, "batch_size": BATCH_SIZE, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "lane_count": len(manifests), "batch_count": len(rows), "lanes": manifests}
    cycle_dir.mkdir(parents=True, exist_ok=True)
    (cycle_dir / "inventory.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (cycle_dir / "dollar_batches_rows.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(json.dumps({"inventory": str(cycle_dir / 'inventory.json'), "db_rows": str(cycle_dir / 'dollar_batches_rows.json'), "batch_count": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
