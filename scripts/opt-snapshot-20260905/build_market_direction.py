#!/usr/bin/env python3
"""Build reproducible market-direction cuts from shipped LeadCurate lane files."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
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


def truthy(value: str) -> bool:
    return clean(value).lower() in {"1", "true", "t", "yes", "y"}


def tenure_band(years: float | None) -> str:
    if years is None:
        return "unavailable"
    if years < 10:
        return "under-10"
    if years < 20:
        return "10-19"
    if years < 30:
        return "20-29"
    return "30-plus"


def value_band(value: float | None) -> str:
    if value is None:
        return "unavailable"
    if value < 100_000:
        return "under-100k"
    if value < 250_000:
        return "100k-249k"
    if value < 500_000:
        return "250k-499k"
    if value < 1_000_000:
        return "500k-999k"
    return "1m-plus"


def acreage_band(acres: float | None) -> str:
    if acres is None:
        return "unavailable"
    if acres < 0.25:
        return "under-0.25"
    if acres < 1:
        return "0.25-0.99"
    if acres < 5:
        return "1-4.99"
    return "5-plus"


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


def new_lane_stats() -> dict[str, object]:
    return {
        "records": 0,
        "tenure_bins": Counter(),
        "tenure_values": [],
        "value_bins": Counter(),
        "values": [],
        "acreage_bins": Counter(),
        "acreage_values": [],
        "absentee": 0,
        "out_of_state": 0,
        "segments": Counter(),
        "owner_mail_states": Counter(),
    }


def load_market(
    root: Path, market: str, run_date: str
) -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    properties: dict[str, dict[str, object]] = {}
    lane_stats = {lane: new_lane_stats() for lane in LANES}
    for lane in LANES:
        path = delivery_file(root, market, run_date, lane)
        stats = lane_stats[lane]
        with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
            reader = csv.reader(handle)
            header = next(reader)
            indexes = {name: index for index, name in enumerate(header)}
            for row in reader:
                parcel_id = first(row, indexes, ("lc_parcel_id", "LC_PARCEL_KEY", "parcel_key"))
                if not parcel_id:
                    continue
                stats["records"] = int(stats["records"]) + 1
                years = number(first(row, indexes, ("lc_years_owned",)))
                value = number(first(row, indexes, ("lc_total_value", "TOT_VAL", "TOTAL_VAL", "VAL_CERTIFIED_TOT")))
                acreage = number(first(row, indexes, ("lc_acreage", "LAND_ACRES_CALC", "LOT_SIZE")))
                tenure_bins = stats["tenure_bins"]
                value_bins = stats["value_bins"]
                acreage_bins = stats["acreage_bins"]
                assert isinstance(tenure_bins, Counter)
                assert isinstance(value_bins, Counter)
                assert isinstance(acreage_bins, Counter)
                tenure_bins[tenure_band(years)] += 1
                value_bins[value_band(value)] += 1
                acreage_bins[acreage_band(acreage)] += 1
                if years is not None:
                    tenure_values = stats["tenure_values"]
                    assert isinstance(tenure_values, list)
                    tenure_values.append(years)
                if value is not None:
                    values = stats["values"]
                    assert isinstance(values, list)
                    values.append(value)
                if acreage is not None:
                    acreage_values = stats["acreage_values"]
                    assert isinstance(acreage_values, list)
                    acreage_values.append(acreage)
                stats["absentee"] = int(stats["absentee"]) + truthy(first(row, indexes, ("lc_is_absentee",)))
                stats["out_of_state"] = int(stats["out_of_state"]) + truthy(first(row, indexes, ("lc_is_out_of_state",)))
                segment = first(row, indexes, ("lc_property_segment",)).lower()
                if segment:
                    segments = stats["segments"]
                    assert isinstance(segments, Counter)
                    segments[segment] += 1
                mail_state = first(row, indexes, ("lc_mail_state",)).upper()
                if mail_state:
                    owner_mail_states = stats["owner_mail_states"]
                    assert isinstance(owner_mail_states, Counter)
                    owner_mail_states[mail_state] += 1
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
                    item["value"] = value
    return properties, lane_stats


def ranked(counter: Counter[str], limit: int | None = None) -> list[dict[str, object]]:
    rows = [{"label": label, "count": count} for label, count in counter.most_common(limit)]
    return rows


def finalize_lane_stats(stats: dict[str, object]) -> dict[str, object]:
    records = int(stats["records"])
    tenure_values = stats["tenure_values"]
    values = stats["values"]
    acreage_values = stats["acreage_values"]
    assert isinstance(tenure_values, list)
    assert isinstance(values, list)
    assert isinstance(acreage_values, list)
    return {
        "records": records,
        "absentee": int(stats["absentee"]),
        "out_of_state": int(stats["out_of_state"]),
        "tenure": {
            "coverage_pct": round(100 * len(tenure_values) / records, 1) if records else 0,
            "median_years": round(statistics.median(tenure_values), 1) if tenure_values else None,
            "bands": dict(stats["tenure_bins"]),
        },
        "official_value": {
            "coverage_pct": round(100 * len(values) / records, 1) if records else 0,
            "median": round(statistics.median(values)) if values else None,
            "bands": dict(stats["value_bins"]),
        },
        "acreage": {
            "coverage_pct": round(100 * len(acreage_values) / records, 1) if records else 0,
            "median": round(statistics.median(acreage_values), 2) if acreage_values else None,
            "bands": dict(stats["acreage_bins"]),
        },
        "property_segments": ranked(stats["segments"]),
        "top_owner_mail_states": ranked(stats["owner_mail_states"], 10),
    }


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


def summarize_market(
    properties: dict[str, dict[str, object]], lane_stats: dict[str, dict[str, object]]
) -> dict[str, object]:
    overlaps = {
        "exactly_two": 0,
        "exactly_three": 0,
        "all_four": 0,
        "two_or_more": 0,
        "three_or_more": 0,
        "pairs": Counter(),
    }
    for item in properties.values():
        count = int(item["lanes"]).bit_count()
        overlaps["exactly_two"] = int(overlaps["exactly_two"]) + (count == 2)
        overlaps["exactly_three"] = int(overlaps["exactly_three"]) + (count == 3)
        overlaps["all_four"] = int(overlaps["all_four"]) + (count == 4)
        overlaps["two_or_more"] += count >= 2
        overlaps["three_or_more"] += count >= 3
        pairs = overlaps["pairs"]
        assert isinstance(pairs, Counter)
        for index, left in enumerate(LANES):
            for right in LANES[index + 1 :]:
                if int(item["lanes"]) & LANE_BITS[left] and int(item["lanes"]) & LANE_BITS[right]:
                    pairs[f"{left}+{right}"] += 1
    pair_counts = overlaps.pop("pairs")
    assert isinstance(pair_counts, Counter)
    overlaps["pairs"] = dict(pair_counts)
    return {
        "unique_qualifying_properties": len(properties),
        "overlaps": overlaps,
        "lanes": {lane: finalize_lane_stats(stats) for lane, stats in lane_stats.items()},
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
        properties, lane_stats = load_market(args.root, market, args.date)
        report["markets"][market] = summarize_market(properties, lane_stats)

    body = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(body + "\n", encoding="utf-8")
    print(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
