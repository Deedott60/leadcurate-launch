#!/usr/bin/env python3
"""Independently verify a prospect evaluation batch before human review."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from build_prospect_evaluation_batch import (
    DESHAWN_MASSACHUSETTS_800,
    MASSACHUSETTS_PARCEL_URL,
    MINIMUM_VALUE,
    NON_ACQUISITION_OWNER,
    NON_ACQUISITION_USE,
    clean,
    number,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def event_keys(path: Path) -> set[str]:
    return {
        clean(row.get("lc_parcel_id") or row.get("LC_PARCEL_KEY")).upper()
        for row in read_csv(path)
        if clean(row.get("lc_parcel_id") or row.get("LC_PARCEL_KEY"))
    }


def verify(args: argparse.Namespace) -> dict[str, object]:
    master_path = args.package_dir / f"{args.batch_id}.csv"
    meta_path = args.package_dir / f"{args.batch_id}-meta.json"
    master = read_csv(master_path)
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    failures: list[str] = []

    keys = [clean(row.get("parcel_id")).upper() for row in master]
    if len(master) != args.expected_records:
        failures.append(f"master has {len(master)} rows; expected {args.expected_records}")
    if len(set(keys)) != len(keys):
        failures.append("master contains duplicate parcel IDs")

    required = (
        "owner_name", "property_address", "mailing_address", "mailing_city",
        "mailing_state", "mailing_zip", "parcel_id", "land_value",
        "building_value", "total_value", "acreage", "years_owned", "USE_CODE",
        "USE_DESC", "LS_DATE", "LS_PRICE", "official_parcel_source_url",
    )
    missing_by_field = {
        field: sum(not clean(row.get(field)) for row in master)
        for field in required
    }
    required_missing = {field: count for field, count in missing_by_field.items() if count}
    if required_missing:
        failures.append(f"required public-record coverage gaps: {required_missing}")

    stale = sum(int(number(row.get("FY"))) < args.min_fiscal_year for row in master)
    if stale:
        failures.append(f"{stale} rows have stale or missing fiscal years")
    wrong_source = sum(clean(row.get("official_parcel_source_url")) != MASSACHUSETTS_PARCEL_URL for row in master)
    if wrong_source:
        failures.append(f"{wrong_source} rows have a missing or wrong official parcel URL")
    banned = sum(bool(NON_ACQUISITION_USE.search(clean(row.get("USE_DESC")))) for row in master)
    if banned:
        failures.append(f"{banned} rows contain excluded non-acquisition use descriptions")
    banned_owners = sum(bool(NON_ACQUISITION_OWNER.search(clean(row.get("owner_name")))) for row in master)
    if banned_owners:
        failures.append(f"{banned_owners} rows contain excluded institutional or utility owners")

    phone_email_columns = [
        field for field in (master[0].keys() if master else [])
        if "phone" in field.lower() or "email" in field.lower()
    ]
    if phone_email_columns:
        failures.append(f"unexpected phone/email columns: {phone_email_columns}")

    category_results: dict[str, object] = {}
    category_master_counts = Counter(clean(row.get("primary_category_key")) for row in master)
    category_union: set[str] = set()
    pre_keys = event_keys(args.pre_foreclosure)
    tax_keys = event_keys(args.tax_title)
    current_events = {"pre-foreclosure": pre_keys, "tax-title": tax_keys}

    for category, expected in DESHAWN_MASSACHUSETTS_800.items():
        path = args.package_dir / "qa" / "massachusetts-statewide" / category / f"{category}.csv"
        rows = read_csv(path)
        lane_keys = [clean(row.get("parcel_id")).upper() for row in rows]
        lane_failures: list[str] = []
        if len(rows) != expected:
            lane_failures.append(f"has {len(rows)} rows; expected {expected}")
        if category_master_counts[category] != expected:
            lane_failures.append(f"master count is {category_master_counts[category]}; expected {expected}")
        if len(set(lane_keys)) != len(lane_keys):
            lane_failures.append("contains duplicate parcel IDs")
        if any(clean(row.get("primary_category_key")) != category for row in rows):
            lane_failures.append("contains a wrong primary category")
        if any(number(row.get("total_value")) < MINIMUM_VALUE[category] for row in rows):
            lane_failures.append("contains a row below the lane minimum official value")
        if category in current_events:
            mismatches = sum(key not in current_events[category] for key in lane_keys)
            if mismatches:
                lane_failures.append(f"contains {mismatches} rows absent from the current court extract")
        if category in {"multifamily", "office", "industrial"}:
            if any(clean(row.get("property_segment")) != category for row in rows):
                lane_failures.append("contains a row with the wrong official property segment")
            if any(number(row.get("building_value")) < 50_000 for row in rows):
                lane_failures.append("contains a row below the commercial improvement-value floor")
        if category == "verified-vacant-land":
            if any(clean(row.get("is_verified_vacant_land")) != "yes" for row in rows):
                lane_failures.append("contains a row that did not pass the vacant-land rule")
        if category == "tired-landlords":
            if any(number(row.get("years_owned")) < 10 or clean(row.get("is_absentee_owner")) != "yes" for row in rows):
                lane_failures.append("contains a row without both tenure and absentee evidence")
        if category == "out-of-state-owners":
            if any(clean(row.get("mailing_state")).upper() == "MA" or clean(row.get("is_out_of_state_owner")) != "yes" for row in rows):
                lane_failures.append("contains a row without out-of-state mailing evidence")
        if lane_failures:
            failures.extend(f"{category}: {item}" for item in lane_failures)
        category_union.update(lane_keys)
        category_results[category] = {
            "records": len(rows),
            "unique_parcels": len(set(lane_keys)),
            "failures": lane_failures,
            "sha256": sha256(path),
        }

    if category_union != set(keys):
        failures.append("category parcel union does not exactly match the master parcel set")
    if meta.get("records") != len(master) or meta.get("unique_parcels") != len(set(keys)):
        failures.append("metadata record counts do not match the master")
    if meta.get("selection_profile") != DESHAWN_MASSACHUSETTS_800:
        failures.append("metadata quota profile does not match the locked 800-record profile")
    if meta.get("full_csv_sha256") != sha256(master_path):
        failures.append("metadata SHA256 does not match the master CSV")
    if meta.get("phone_numbers_included") is not False or meta.get("email_addresses_included") is not False:
        failures.append("metadata does not explicitly mark phone and email as unavailable")

    payload: dict[str, object] = {
        "ok": not failures,
        "status": "verified" if not failures else "failed",
        "batch_id": args.batch_id,
        "records": len(master),
        "unique_parcels": len(set(keys)),
        "duplicate_parcels": len(keys) - len(set(keys)),
        "missing_required_fields": required_missing,
        "stale_or_missing_fiscal_year_records": stale,
        "excluded_use_records": banned,
        "excluded_owner_records": banned_owners,
        "phone_or_email_columns": phone_email_columns,
        "current_event_source_counts": {
            "pre_foreclosure_exact_parcels": len(pre_keys),
            "tax_title_exact_parcels": len(tax_keys),
        },
        "category_results": category_results,
        "master_sha256": sha256(master_path),
        "failures": failures,
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-dir", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--pre-foreclosure", type=Path, required=True)
    parser.add_argument("--tax-title", type=Path, required=True)
    parser.add_argument("--expected-records", type=int, default=800)
    parser.add_argument("--min-fiscal-year", type=int, default=2025)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = verify(args)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
