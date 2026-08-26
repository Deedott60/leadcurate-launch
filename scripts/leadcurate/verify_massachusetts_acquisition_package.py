#!/usr/bin/env python3
"""Independently verify a Massachusetts acquisition package on disk."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from lane_quality import INSTITUTIONAL_OWNER


CATEGORY_RULES: dict[str, Callable[[dict[str, str]], bool]] = {
    "pre-foreclosure": lambda row: bool(row.get("case_number") and row.get("filed_date")),
    "tax-title": lambda row: bool(row.get("case_number") and row.get("filed_date")),
    "multifamily": lambda row: row.get("property_segment") == "multifamily",
    "office": lambda row: row.get("property_segment") == "office",
    "industrial": lambda row: row.get("property_segment") == "industrial",
    "verified-vacant-land": lambda row: row.get("is_verified_vacant_land") == "yes",
    "tired-landlords": lambda row: (
        number(row.get("years_owned")) >= 10
        and row.get("is_absentee_owner") == "yes"
        and number(row.get("building_value")) > 0
    ),
    "out-of-state-owners": lambda row: (
        bool(clean(row.get("mailing_state")))
        and clean(row.get("mailing_state")).upper() != "MA"
        and row.get("is_out_of_state_owner") == "yes"
    ),
}


def clean(value: object) -> str:
    return str(value or "").strip()


def number(value: object) -> float:
    try:
        return float(clean(value).replace(",", "").replace("$", "") or 0)
    except ValueError:
        return 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def event_keys(path: Path) -> set[str]:
    return {
        clean(row.get("lc_parcel_id") or row.get("LC_PARCEL_KEY")).upper()
        for row in read_csv(path)
        if clean(row.get("lc_parcel_id") or row.get("LC_PARCEL_KEY"))
    }


def verify(args: argparse.Namespace) -> dict[str, object]:
    master_path = args.package_dir / f"massachusetts-acquisition-package-{args.source_cycle}.csv"
    meta_path = args.package_dir / f"massachusetts-acquisition-package-{args.source_cycle}-meta.json"
    master = read_csv(master_path)
    master_keys = [clean(row.get("parcel_id")).upper() for row in master]
    failures: list[str] = []
    warnings: list[str] = []

    if len(master) != args.expected_records:
        failures.append(f"master has {len(master)} records; expected {args.expected_records}")
    if len(set(master_keys)) != len(master_keys):
        failures.append("master contains duplicate parcel IDs")
    missing_core = sum(
        not all(clean(row.get(field)) for field in ("owner_name", "property_address", "parcel_id"))
        for row in master
    )
    if missing_core:
        failures.append(f"master contains {missing_core} rows missing a core field")
    institutional = sum(bool(INSTITUTIONAL_OWNER.search(clean(row.get("owner_name")))) for row in master)
    if institutional:
        failures.append(f"master contains {institutional} institutional/public owners")
    stale_fiscal_years = Counter(
        clean(row.get("FY")) or "missing"
        for row in master
        if int(number(row.get("FY"))) < args.min_fiscal_year
    )
    if stale_fiscal_years:
        failures.append(
            f"master contains fiscal years below {args.min_fiscal_year} or missing: "
            f"{dict(stale_fiscal_years)}"
        )

    category_results: dict[str, object] = {}
    category_keys: list[str] = []
    pre_keys = event_keys(args.pre_foreclosure)
    tax_keys = event_keys(args.tax_title)
    expected_event_keys = {"pre-foreclosure": pre_keys, "tax-title": tax_keys}
    for category, rule in CATEGORY_RULES.items():
        path = args.package_dir / "categories" / category / f"{category}.csv"
        rows = read_csv(path)
        keys = [clean(row.get("parcel_id")).upper() for row in rows]
        category_keys.extend(keys)
        invalid = [key for key, row in zip(keys, rows) if not rule(row)]
        wrong_primary = sum(clean(row.get("primary_category_key")) != category for row in rows)
        duplicate_count = len(keys) - len(set(keys))
        event_mismatch = 0
        if category in expected_event_keys:
            event_mismatch = sum(key not in expected_event_keys[category] for key in keys)
        if invalid:
            failures.append(f"{category} has {len(invalid)} records that fail its lane rule")
        if wrong_primary:
            failures.append(f"{category} has {wrong_primary} records with the wrong primary category")
        if duplicate_count:
            failures.append(f"{category} has {duplicate_count} duplicate parcel IDs")
        if event_mismatch:
            failures.append(f"{category} has {event_mismatch} parcels absent from its current court extract")
        category_results[category] = {
            "records": len(rows),
            "unique_parcels": len(set(keys)),
            "rule_failures": len(invalid),
            "event_source_mismatches": event_mismatch,
        }

    if len(category_keys) != len(master):
        failures.append("category row count does not equal the master row count")
    if len(set(category_keys)) != len(category_keys):
        failures.append("a parcel appears in more than one primary category file")
    if set(category_keys) != set(master_keys):
        failures.append("category parcel set does not exactly match the master parcel set")

    overlap_counts = Counter()
    for row in master:
        for category in CATEGORY_RULES:
            if category.replace("-", " ") in clean(row.get("all_verified_categories")).lower():
                overlap_counts[category] += 1
    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    if metadata.get("records") != len(master) or metadata.get("duplicate_parcels") != 0:
        failures.append("package metadata does not match the verified master counts")

    payload: dict[str, object] = {
        "ok": not failures,
        "package_dir": str(args.package_dir),
        "master_records": len(master),
        "master_unique_parcels": len(set(master_keys)),
        "missing_core_records": missing_core,
        "institutional_or_public_owner_records": institutional,
        "stale_or_missing_fiscal_year_records": sum(stale_fiscal_years.values()),
        "category_records_sum": len(category_keys),
        "category_results": category_results,
        "current_event_source_counts": {
            "pre_foreclosure_exact_parcels": len(pre_keys),
            "tax_title_exact_parcels": len(tax_keys),
        },
        "failures": failures,
        "warnings": warnings,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--pre-foreclosure", type=Path, required=True)
    parser.add_argument("--tax-title", type=Path, required=True)
    parser.add_argument("--source-cycle", required=True)
    parser.add_argument("--expected-records", type=int, default=15000)
    parser.add_argument("--min-fiscal-year", type=int, default=2025)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = verify(args)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
