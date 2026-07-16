#!/usr/bin/env python3
import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


MARKETS = ("dallas-tx", "massachusetts-statewide", "cook-il")
PROCESSED_ROOT = Path("/opt/leadcurate/processed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify availability notes and file integrity across investor-lane deliveries.")
    parser.add_argument("--date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    args = parser.parse_args()
    failed = False
    all_unique: set[str] = set()
    total_lane_rows = 0
    results = {}
    for market in MARKETS:
        folder = PROCESSED_ROOT / market / args.date
        market_unique: set[str] = set()
        lane_results = {}
        for meta_path in sorted(folder.rglob("*-meta.json")):
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if (
                meta.get("status") != "verified"
                or "lane" not in meta
                or "records" not in meta
                or not meta.get("outputs", {}).get("full")
            ):
                continue
            full_path = Path(meta["outputs"]["full"])
            seen: set[str] = set()
            availability = Counter()
            row_count = 0
            blank_notes = 0
            false_vacant_notes = 0
            field_count = 0
            with full_path.open(newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                field_count = len(reader.fieldnames or [])
                for row in reader:
                    row_count += 1
                    parcel = row.get("lc_parcel_id", "").strip()
                    seen.add(parcel)
                    market_unique.add(parcel)
                    note = row.get("Information Not Available", "").strip()
                    if not note:
                        blank_notes += 1
                    elif note != "None among the core facts checked":
                        availability.update(note.split("; "))
                    if row.get("lc_verified_vacant") == "yes" and any(
                        label in note for label in ("Year built", "Building area", "Unit count")
                    ):
                        false_vacant_notes += 1
            duplicates = row_count - len(seen - {""})
            availability_matches = dict(availability) == meta.get("information_not_available_counts", {})
            lane_ok = (
                row_count == meta["records"]
                and duplicates == 0
                and blank_notes == 0
                and false_vacant_notes == 0
                and availability_matches
                and field_count == meta["field_count"]
            )
            failed = failed or not lane_ok
            total_lane_rows += row_count
            lane_results[meta["lane"]] = {
                "rows": row_count,
                "fields": field_count,
                "duplicates": duplicates,
                "blank_availability_notes": blank_notes,
                "false_vacant_missing_notes": false_vacant_notes,
                "availability_counts_match_meta": availability_matches,
                "ok": lane_ok,
            }
        results[market] = {
            "unique_properties": len(market_unique),
            "lanes": lane_results,
        }
        all_unique.update(f"{market}:{parcel}" for parcel in market_unique)
    results["totals"] = {
        "lane_rows": total_lane_rows,
        "unique_properties": len(all_unique),
        "ok": not failed,
    }
    print(json.dumps(results, indent=2, sort_keys=True))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
