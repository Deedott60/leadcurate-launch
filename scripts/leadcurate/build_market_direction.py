#!/usr/bin/env python3
"""Build reproducible market-direction cuts from shipped LeadCurate lane files."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path


LANES = (
    "tired-landlords",
    "out-of-state-owners",
    "industrial-multifamily-distress",
    "verified-vacant-land",
)

LANE_BITS = {lane: 1 << index for index, lane in enumerate(LANES)}


def clean(value: str) -> str:
    return (value or "").strip()


def number(value: str) -> float | None:
    text = clean(value).replace("$", "").replace(",", "")
    if not text:
        return None
    try:
        parsed = float(text)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def first(row: list[str], indexes: dict[str, int], names: tuple[str, ...]) -> str:
    for name in names:
        index = indexes.get(name)
        if index is not None and index < len(row):
            value = clean(row[index])
            if value:
                return value
    return ""


def delivery_file(root: Path, market: str, run_date: str, lane: str) -> Path:
    path = root / market / run_date / lane / f"{market}-{lane}-{run_date}.csv"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def load_market(root: Path, market: str, run_date: str) -> dict[str, dict[str, object]]:
    properties: dict[str, dict[str, object]] = {}
    for lane in LANES:
        path = delivery_file(root, market, run_date, lane)
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            indexes = {name: index for index, name in enumerate(header)}
            for row in reader:
                parcel_id = first(row, indexes, ("lc_parcel_id", "LC_PARCEL_KEY", "parcel_key"))
                if not parcel_id:
                    continue
                item = properties.setdefault(
                    parcel_id,
                    {
                        "lanes": 0,
                        "municipality": "",
                        "zip": "",
                        "county": "",
                        "value": None,
                    },
                )
                item["lanes"] = int(item["lanes"]) | LANE_BITS[lane]
                if not item["municipality"]:
                    item["municipality"] = first(
                        row,
                        indexes,
                        ("lc_municipality", "U_COOK_MUNICIPALITY_NAME", "ADDR_PROP_ADDRESS_CITY_NAME", "CITY"),
                    )
                if not item["zip"]:
                    item["zip"] = first(
                        row,
                        indexes,
                        ("PROPERTY_ZIPCODE", "ZIP", "U_ZIP_CODE", "ADDR_PROP_ADDRESS_ZIPCODE_1"),
                    )[:5]
                if not item["county"]:
                    item["county"] = first(row, indexes, ("lc_county", "COUNTY"))
                if item["value"] is None:
                    item["value"] = number(first(row, indexes, ("lc_total_value", "TOT_VAL", "TOTAL_VAL", "VAL_CERTIFIED_TOT")))
    return properties


def summarize_group(properties: dict[str, dict[str, object]], field: str, minimum: int) -> list[dict[str, object]]:
    groups: dict[str, dict[str, object]] = defaultdict(
        lambda: {"qualifying": 0, "multi_signal": 0, "three_signal": 0, "values": []}
    )
    for item in properties.values():
        label = clean(str(item[field])).upper()
        if not label or label in {"0", "00000", "NONE", "UNKNOWN", "UNINCORPORATED"}:
            continue
        entry = groups[label]
        entry["qualifying"] = int(entry["qualifying"]) + 1
        signal_count = int(item["lanes"]).bit_count()
        if signal_count >= 2:
            entry["multi_signal"] = int(entry["multi_signal"]) + 1
        if signal_count >= 3:
            entry["three_signal"] = int(entry["three_signal"]) + 1
        if item["value"] is not None:
            values = entry["values"]
            assert isinstance(values, list)
            values.append(float(item["value"]))

    result: list[dict[str, object]] = []
    for label, entry in groups.items():
        qualifying = int(entry["qualifying"])
        if qualifying < minimum:
            continue
        values = entry.pop("values")
        assert isinstance(values, list)
        result.append(
            {
                "label": label,
                **entry,
                "multi_signal_share": round(100 * int(entry["multi_signal"]) / qualifying, 1),
                "value_coverage": round(100 * len(values) / qualifying, 1),
                "median_official_value": round(statistics.median(values)) if values else None,
            }
        )
    return sorted(result, key=lambda item: (int(item["multi_signal"]), int(item["qualifying"])), reverse=True)


def summarize_market(properties: dict[str, dict[str, object]]) -> dict[str, object]:
    overlaps = {"two_or_more": 0, "three_or_more": 0}
    for item in properties.values():
        count = int(item["lanes"]).bit_count()
        overlaps["two_or_more"] += count >= 2
        overlaps["three_or_more"] += count >= 3
    return {
        "unique_qualifying_properties": len(properties),
        "overlaps": overlaps,
        "top_zips": summarize_group(properties, "zip", 100),
        "top_municipalities": summarize_group(properties, "municipality", 500),
        "top_counties": summarize_group(properties, "county", 1000),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/opt/leadcurate/processed"))
    parser.add_argument("--date", required=True)
    parser.add_argument("--markets", nargs="+", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = {"run_date": args.date, "markets": {}}
    for market in args.markets:
        report["markets"][market] = summarize_market(load_market(args.root, market, args.date))

    body = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body + "\n", encoding="utf-8")
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
