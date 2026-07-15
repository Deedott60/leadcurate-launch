#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any

from process_investor_lanes import MARKETS, clean, derive


TODAY = date.today().isoformat()


def blank_metrics() -> dict[str, Any]:
    return {
        "total_parcels": 0, "out_of_state": 0, "vacant": 0,
        "tired_10_plus": 0, "tired_20_plus": 0, "industrial": 0,
        "multifamily": 0, "industrial_multifamily_distress": 0,
        "opportunity_parcels": 0, "values_out_of_state": [],
        "values_vacant": [], "values_tired": [], "values_distressed_asset": [],
    }


def add(metrics: dict[str, Any], d: dict[str, Any]) -> None:
    metrics["total_parcels"] += 1
    value = float(d["lc_total_value"] or 0)
    out_of_state = d["lc_is_out_of_state"] == "yes"
    vacant = d["lc_verified_vacant"] == "yes"
    tenure = d["lc_years_owned"] if isinstance(d["lc_years_owned"], (int, float)) else None
    tired = bool(tenure is not None and tenure >= 10 and d["lc_is_absentee"] == "yes" and d["lc_is_residential"] == "yes" and d["lc_building_value"] > 0)
    distressed_asset = d["lc_property_segment"] in {"industrial", "multifamily"} and (d["lc_is_absentee"] == "yes" or (tenure is not None and tenure >= 10))
    metrics["out_of_state"] += out_of_state
    metrics["vacant"] += vacant
    metrics["tired_10_plus"] += tired
    metrics["tired_20_plus"] += bool(tired and tenure is not None and tenure >= 20)
    metrics["industrial"] += d["lc_property_segment"] == "industrial"
    metrics["multifamily"] += d["lc_property_segment"] == "multifamily"
    metrics["industrial_multifamily_distress"] += distressed_asset
    metrics["opportunity_parcels"] += out_of_state or vacant or tired or distressed_asset
    if value > 0 and out_of_state:
        metrics["values_out_of_state"].append(value)
    if value > 0 and vacant:
        metrics["values_vacant"].append(value)
    if value > 0 and tired:
        metrics["values_tired"].append(value)
    if value > 0 and distressed_asset:
        metrics["values_distressed_asset"].append(value)


def finalize(name: str, level: str, metrics: dict[str, Any]) -> dict[str, Any]:
    total = metrics["total_parcels"]
    per_10k = lambda count: round(count / total * 10_000, 2) if total else 0
    return {
        "rank": 0, "level": level, "location": name, "total_parcels": total,
        "opportunity_parcels": metrics["opportunity_parcels"],
        "opportunity_density_per_10k": per_10k(metrics["opportunity_parcels"]),
        "out_of_state_owners": metrics["out_of_state"],
        "out_of_state_per_10k": per_10k(metrics["out_of_state"]),
        "verified_vacant_candidates": metrics["vacant"],
        "vacant_per_10k": per_10k(metrics["vacant"]),
        "tired_landlords_10_plus": metrics["tired_10_plus"],
        "tired_landlords_20_plus": metrics["tired_20_plus"],
        "tired_per_10k": per_10k(metrics["tired_10_plus"]),
        "industrial_parcels": metrics["industrial"],
        "multifamily_parcels": metrics["multifamily"],
        "industrial_multifamily_distress": metrics["industrial_multifamily_distress"],
        "distressed_asset_per_10k": per_10k(metrics["industrial_multifamily_distress"]),
        "median_value_out_of_state": median(metrics["values_out_of_state"]) if metrics["values_out_of_state"] else None,
        "median_value_vacant": median(metrics["values_vacant"]) if metrics["values_vacant"] else None,
        "median_value_tired": median(metrics["values_tired"]) if metrics["values_tired"] else None,
        "median_value_distressed_asset": median(metrics["values_distressed_asset"]) if metrics["values_distressed_asset"] else None,
    }


def write_triple(rows: list[dict[str, Any]], stem: Path, source: Path) -> dict[str, Any]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    full = stem.with_suffix(".csv")
    preview = stem.parent / f"{stem.name}-preview.csv"
    meta = stem.parent / f"{stem.name}-meta.json"
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    fields = list(rows[0]) if rows else []
    for path, output_rows in ((full, rows), (preview, rows[:25])):
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(output_rows)
    payload = {
        "source_file": str(source), "records": len(rows),
        "preview_records": min(25, len(rows)),
        "sort": "opportunity parcels descending, then opportunity density per 10,000 parcels",
        "top_10": rows[:10],
        "outputs": {"full": str(full), "preview": str(preview), "meta": str(meta)},
        "verification": {"meta_count_matches_file": len(rows) == sum(1 for _ in full.open(encoding="utf-8")) - 1},
    }
    meta.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def build(source: Path, output_dir: Path) -> dict[str, Any]:
    cfg = MARKETS["massachusetts-statewide"]
    counties: dict[str, dict[str, Any]] = defaultdict(blank_metrics)
    cities: dict[str, dict[str, Any]] = defaultdict(blank_metrics)
    seen: set[str] = set()
    source_rows = 0
    with source.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.DictReader(handle):
            source_rows += 1
            d = derive(row, cfg)
            parcel = clean(d["lc_parcel_id"])
            if not parcel or parcel in seen:
                continue
            seen.add(parcel)
            add(counties[clean(d["lc_county"]) or "UNKNOWN"], d)
            add(cities[clean(d["lc_municipality"]) or "UNKNOWN"], d)
    county_rows = [finalize(name, "county", metrics) for name, metrics in counties.items()]
    city_rows = [finalize(name, "municipality", metrics) for name, metrics in cities.items()]
    county_rows.sort(key=lambda r: (r["opportunity_parcels"], r["opportunity_density_per_10k"]), reverse=True)
    city_rows.sort(key=lambda r: (r["opportunity_parcels"], r["opportunity_density_per_10k"]), reverse=True)
    county = write_triple(county_rows, output_dir / f"massachusetts-county-lane-density-{TODAY}", source)
    city = write_triple(city_rows, output_dir / f"massachusetts-city-lane-density-{TODAY}", source)
    payload = {
        "source_rows": source_rows, "unique_parcels": len(seen),
        "duplicate_source_rows": source_rows - len(seen),
        "county_rollup": county, "city_rollup": city,
    }
    (output_dir / f"massachusetts-statewide-rollup-{TODAY}-meta.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build county and city lane-density rankings from the MassGIS statewide parcel pull.")
    parser.add_argument("--source", type=Path, default=MARKETS["massachusetts-statewide"]["source"])
    parser.add_argument("--output-dir", type=Path, default=Path(f"/opt/leadcurate/processed/massachusetts-statewide/{TODAY}/rollup"))
    args = parser.parse_args()
    payload = build(args.source, args.output_dir)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
