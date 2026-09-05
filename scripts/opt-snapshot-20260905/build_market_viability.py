#!/usr/bin/env python3
"""Measure whether a candidate market has an active, established housing base.

This manual tool uses parcel-level government records. It does not claim buyer
demand or appreciation. It measures recent recorded transfers, improved
residential depth, homestead/PRE coverage, and official assessed values so a
low-cost lead market is not recommended only because it has distressed land.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path


def clean(value: object) -> str:
    return str(value or "").strip()


def number(value: object) -> float | None:
    raw = clean(value).replace("$", "").replace(",", "")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def parcel_key(value: object) -> str:
    return "".join(character for character in clean(value).upper() if character.isalnum())


def parse_date(value: object) -> date | None:
    raw = clean(value)
    if len(raw) >= 10 and raw[4:5] == "-" and raw[7:8] == "-":
        raw = raw[:10]
    for fmt in ("%Y-%m-%d", "%m%d%Y", "%Y%m%d", "%m/%d/%Y", "%m-%d-%Y"):
        try:
            parsed = datetime.strptime(raw, fmt).date()
            return parsed if parsed <= date.today() else None
        except ValueError:
            continue
    return None


def latest_date(row: dict[str, str], fields: list[str]) -> date | None:
    dates = [parsed for field in fields if (parsed := parse_date(row.get(field)))]
    return max(dates) if dates else None


def median(values: list[float]) -> float | None:
    return round(statistics.median(values), 2) if values else None


def summarize(
    source: Path,
    places: list[str],
    parcel_field: str,
    municipality_field: str,
    class_field: str,
    residential_improved_codes: set[str],
    value_field: str,
    homestead_field: str,
    transfer_date_fields: list[str],
    recent_since: date,
    thresholds: dict[str, float],
) -> dict[str, object]:
    place_set = set(places)
    buckets: dict[str, dict[str, object]] = {
        place: {
            "official_parcels": 0,
            "residential_improved_parcels": 0,
            "homestead_proxy_parcels": 0,
            "recent_transfers_all_property": 0,
            "recent_transfers_residential_improved": 0,
            "official_values": [],
            "residential_official_values": [],
        }
        for place in places
    }
    seen: set[str] = set()
    duplicates = 0
    source_rows = 0
    with source.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            source_rows += 1
            place = clean(row.get(municipality_field))
            if place not in place_set:
                continue
            key = parcel_key(row.get(parcel_field))
            if not key:
                continue
            scoped_key = f"{place}|{key}"
            if scoped_key in seen:
                duplicates += 1
                continue
            seen.add(scoped_key)
            bucket = buckets[place]
            bucket["official_parcels"] = int(bucket["official_parcels"]) + 1
            assessed = number(row.get(value_field))
            if assessed is not None and assessed > 0:
                values = bucket["official_values"]
                assert isinstance(values, list)
                values.append(assessed)
            residential = clean(row.get(class_field)) in residential_improved_codes
            if residential:
                bucket["residential_improved_parcels"] = (
                    int(bucket["residential_improved_parcels"]) + 1
                )
                if (number(row.get(homestead_field)) or 0) > 0:
                    bucket["homestead_proxy_parcels"] = (
                        int(bucket["homestead_proxy_parcels"]) + 1
                    )
                if assessed is not None and assessed > 0:
                    values = bucket["residential_official_values"]
                    assert isinstance(values, list)
                    values.append(assessed)
            transfer = latest_date(row, transfer_date_fields)
            if transfer and transfer >= recent_since:
                bucket["recent_transfers_all_property"] = (
                    int(bucket["recent_transfers_all_property"]) + 1
                )
                if residential:
                    bucket["recent_transfers_residential_improved"] = (
                        int(bucket["recent_transfers_residential_improved"]) + 1
                    )

    rows: list[dict[str, object]] = []
    combined_residential_values: list[float] = []
    for place in places:
        bucket = buckets[place]
        residential = int(bucket["residential_improved_parcels"])
        homestead = int(bucket["homestead_proxy_parcels"])
        recent_residential = int(bucket["recent_transfers_residential_improved"])
        values = bucket.pop("official_values")
        residential_values = bucket.pop("residential_official_values")
        assert isinstance(values, list)
        assert isinstance(residential_values, list)
        combined_residential_values.extend(residential_values)
        owner_proxy_pct = round(homestead / residential * 100, 1) if residential else 0.0
        transfers_per_1000 = round(recent_residential / residential * 1000, 1) if residential else 0.0
        passes = (
            residential >= thresholds["min_residential_improved"]
            and recent_residential >= thresholds["min_recent_residential_transfers"]
            and owner_proxy_pct >= thresholds["min_homestead_proxy_pct"]
            and (median(residential_values) or 0) >= thresholds["min_median_assessed_value"]
        )
        rows.append(
            {
                "municipality": place,
                **bucket,
                "homestead_proxy_pct_of_residential": owner_proxy_pct,
                "recent_residential_transfers_per_1000": transfers_per_1000,
                "median_official_assessed_value": median(values),
                "median_residential_official_assessed_value": median(residential_values),
                "viability_screen": "passes" if passes else "review",
            }
        )

    combined_counts = Counter()
    for row in rows:
        for key in (
            "official_parcels",
            "residential_improved_parcels",
            "homestead_proxy_parcels",
            "recent_transfers_all_property",
            "recent_transfers_residential_improved",
        ):
            combined_counts[key] += int(row[key])
    residential = combined_counts["residential_improved_parcels"]
    homestead = combined_counts["homestead_proxy_parcels"]
    recent_residential = combined_counts["recent_transfers_residential_improved"]
    combined = {
        "municipalities": places,
        **dict(combined_counts),
        "homestead_proxy_pct_of_residential": round(homestead / residential * 100, 1)
        if residential
        else 0.0,
        "recent_residential_transfers_per_1000": round(recent_residential / residential * 1000, 1)
        if residential
        else 0.0,
        "median_residential_official_assessed_value": median(combined_residential_values),
        "all_municipalities_pass_screen": all(row["viability_screen"] == "passes" for row in rows),
    }
    return {
        "source_file": str(source),
        "source_rows": source_rows,
        "recent_since": recent_since.isoformat(),
        "screen_definition": {
            **thresholds,
            "meaning": (
                "A pass confirms an established improved-residential base, recent official transfer "
                "activity, a substantial homestead/PRE proxy, and a nonzero official value base. "
                "It is not a forecast of buyer demand, resale price, or appreciation."
            ),
        },
        "municipalities": rows,
        "combined": combined,
        "verification": {
            "duplicate_scoped_parcels_removed": duplicates,
            "unique_scoped_parcels": len(seen),
            "requested_municipalities_found": sorted(
                row["municipality"] for row in rows if row["official_parcels"]
            ),
        },
    }


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--places", nargs="+", required=True)
    parser.add_argument("--parcel-field", default="parcel_id")
    parser.add_argument("--municipality-field", default="municipality")
    parser.add_argument("--class-field", default="property_class")
    parser.add_argument("--value-field", default="assessed_value")
    parser.add_argument("--homestead-field", default="pre_pct")
    parser.add_argument("--transfer-date-fields", default="sale_date,latest_transfer_date")
    parser.add_argument("--residential-improved-codes", default="401,403,407,410")
    parser.add_argument("--recent-since", type=date.fromisoformat, required=True)
    parser.add_argument("--min-residential-improved", type=float, default=5_000)
    parser.add_argument("--min-recent-residential-transfers", type=float, default=100)
    parser.add_argument("--min-homestead-proxy-pct", type=float, default=50)
    parser.add_argument("--min-median-assessed-value", type=float, default=10_000)
    args = parser.parse_args()
    result = summarize(
        source=args.source,
        places=args.places,
        parcel_field=args.parcel_field,
        municipality_field=args.municipality_field,
        class_field=args.class_field,
        residential_improved_codes={
            item.strip() for item in args.residential_improved_codes.split(",") if item.strip()
        },
        value_field=args.value_field,
        homestead_field=args.homestead_field,
        transfer_date_fields=[
            item.strip() for item in args.transfer_date_fields.split(",") if item.strip()
        ],
        recent_since=args.recent_since,
        thresholds={
            "min_residential_improved": args.min_residential_improved,
            "min_recent_residential_transfers": args.min_recent_residential_transfers,
            "min_homestead_proxy_pct": args.min_homestead_proxy_pct,
            "min_median_assessed_value": args.min_median_assessed_value,
        },
    )
    result["built_at"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    write_csv(args.output.with_suffix(".csv"), result["municipalities"])
    print(json.dumps(result, indent=2))
    return 0 if result["combined"]["all_municipalities_pass_screen"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
