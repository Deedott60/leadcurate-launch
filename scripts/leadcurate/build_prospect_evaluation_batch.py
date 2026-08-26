#!/usr/bin/env python3
"""Cut a verified prospect evaluation batch from a gated territory package.

The script never invents contact data or event evidence. It keeps the complete
public-record row, applies a prospect-specific lane quota, removes obvious
non-acquisition noise, and emits the exact files used for human review and QA.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any


MASSACHUSETTS_PARCEL_URL = (
    "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/"
    "Massachusetts_Property_Tax_Parcels/FeatureServer/0"
)

CATEGORY_LABELS = {
    "pre-foreclosure": "Current pre-foreclosure filing signal",
    "tax-title": "Current Land Court tax-title filing",
    "multifamily": "Multifamily ownership opportunity",
    "office": "Office ownership opportunity",
    "industrial": "Industrial ownership opportunity",
    "verified-vacant-land": "Verified vacant land",
    "tired-landlords": "Long-hold absentee owner",
    "out-of-state-owners": "Out-of-state owner",
}

DESHAWN_MASSACHUSETTS_800 = {
    "pre-foreclosure": 200,
    "tax-title": 4,
    "multifamily": 150,
    "office": 50,
    "industrial": 75,
    "verified-vacant-land": 120,
    "tired-landlords": 101,
    "out-of-state-owners": 100,
}

MINIMUM_VALUE = {
    "pre-foreclosure": 1,
    "tax-title": 1,
    "multifamily": 100_000,
    "office": 100_000,
    "industrial": 100_000,
    "verified-vacant-land": 10_000,
    "tired-landlords": 75_000,
    "out-of-state-owners": 75_000,
}

PREFERRED_VALUE_CEILING = {
    "pre-foreclosure": 5_000_000,
    "tax-title": 5_000_000,
    "multifamily": 5_000_000,
    "office": 10_000_000,
    "industrial": 15_000_000,
    "verified-vacant-land": 1_000_000,
    "tired-landlords": 2_500_000,
    "out-of-state-owners": 2_500_000,
}

# Official use descriptions that may be technically classified as land or a
# commercial class but are poor acquisition targets for this evaluation cut.
NON_ACQUISITION_USE = re.compile(
    r"(?:RIGHT[ -]?OF[ -]?WAY|UTILITY|ELECTRIC(?:AL)? TRANSMISSION|"
    r"GAS TRANSMISSION|CEMET|CONSERVATION|UNDEVELOPABLE|WETLAND|MARSH|"
    r"WATER SUPPLY|RAILROAD|PUBLIC OPEN SPACE|MUNICIPAL PARK|TOWN OWNED)",
    re.IGNORECASE,
)

REQUIRED_FIELDS = (
    "owner_name",
    "property_address",
    "parcel_id",
    "mailing_address",
    "mailing_city",
    "mailing_state",
    "mailing_zip",
)


def clean(value: Any) -> str:
    return str(value or "").strip()


def number(value: Any) -> float:
    try:
        return float(re.sub(r"[^0-9.\-]", "", clean(value)) or 0)
    except ValueError:
        return 0.0


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def is_eligible(row: dict[str, str], category: str, min_fiscal_year: int) -> tuple[bool, str]:
    if any(not clean(row.get(field)) for field in REQUIRED_FIELDS):
        return False, "missing_required_public_record_field"
    if int(number(row.get("FY"))) < min_fiscal_year:
        return False, "stale_or_missing_fiscal_year"
    if clean(row.get("primary_category_key")) != category:
        return False, "wrong_primary_category"

    use_desc = clean(row.get("USE_DESC"))
    if NON_ACQUISITION_USE.search(use_desc):
        return False, "non_acquisition_use"

    total_value = number(row.get("total_value"))
    if total_value < MINIMUM_VALUE[category]:
        return False, "below_minimum_official_value"

    if category in {"multifamily", "office", "industrial"}:
        if number(row.get("building_value")) < 50_000:
            return False, "insufficient_improvement_value"
    if category == "verified-vacant-land" and number(row.get("acreage")) < 0.1:
        return False, "insufficient_acreage"
    if category in {"pre-foreclosure", "tax-title"}:
        if not clean(row.get("case_number")) or not clean(row.get("filed_date")):
            return False, "missing_current_court_evidence"
    if category == "tired-landlords":
        if number(row.get("years_owned")) < 10 or clean(row.get("is_absentee_owner")) != "yes":
            return False, "missing_tenure_or_absentee_evidence"
    if category == "out-of-state-owners":
        if clean(row.get("mailing_state")).upper() == "MA" or clean(row.get("is_out_of_state_owner")) != "yes":
            return False, "missing_out_of_state_evidence"
    return True, ""


def completeness_score(row: dict[str, str]) -> int:
    useful = (
        "land_value", "building_value", "total_value", "acreage", "years_owned",
        "LS_DATE", "LS_PRICE", "USE_CODE", "USE_DESC", "YEAR_BUILT", "BLD_AREA",
        "UNITS", "ZONING", "LS_BOOK", "LS_PAGE",
    )
    return sum(bool(clean(row.get(field))) for field in useful)


def selection_key(row: dict[str, str], category: str) -> tuple[Any, ...]:
    total_value = number(row.get("total_value"))
    preferred = total_value <= PREFERRED_VALUE_CEILING[category]
    overlaps = int(number(row.get("verified_category_count")))
    score = int(number(row.get("acquisition_priority_score")))
    tenure = number(row.get("years_owned"))
    # Stable parcel tie-breaker keeps repeat runs byte-for-byte reproducible.
    parcel_hash = hashlib.sha1(clean(row.get("parcel_id")).upper().encode("utf-8")).hexdigest()
    return (preferred, overlaps, score, completeness_score(row), tenure, -total_value, parcel_hash)


def lane_note(category: str) -> str:
    if category == "pre-foreclosure":
        return "Exact parcel match to a current Massachusetts Land Court Servicemembers filing; not a foreclosure judgment."
    if category == "tax-title":
        return "Exact parcel match to the current Massachusetts Land Court tax-title report."
    if category in {"multifamily", "office", "industrial"}:
        return "Official property class plus absentee ownership or at least 10 years of ownership; not a claimed distress event."
    if category == "verified-vacant-land":
        return "Current official vacant-use and no-improvement checks passed; obvious undevelopable and utility uses removed from this cut."
    if category == "tired-landlords":
        return "Residential improvement, absentee mailing signal, and at least 10 years of recorded ownership."
    return "Official owner mailing state is outside Massachusetts."


def clean_customer_property_zip(row: dict[str, Any]) -> None:
    zip_code = clean(row.get("property_zip"))
    if zip_code in {"0", "00000"}:
        row["property_zip"] = ""
        row["property_address"] = re.sub(r"\s+00000$", "", clean(row.get("property_address")))
        unavailable = [
            item.strip() for item in clean(row.get("information_not_available")).split(";")
            if item.strip()
        ]
        if "Property ZIP" not in unavailable:
            unavailable.append("Property ZIP")
        row["information_not_available"] = "; ".join(unavailable)


def build(args: argparse.Namespace) -> dict[str, Any]:
    source_fields, source_rows = read_csv(args.master)
    source_meta = json.loads(args.source_meta.read_text(encoding="utf-8"))
    quotas = dict(DESHAWN_MASSACHUSETTS_800)
    if args.limit != sum(quotas.values()):
        raise ValueError(f"DeShawn profile is locked at {sum(quotas.values())} records")

    rejected = Counter()
    eligible_by_category: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        category = clean(row.get("primary_category_key"))
        if category not in quotas:
            rejected["unknown_category"] += 1
            continue
        eligible, reason = is_eligible(row, category, args.min_fiscal_year)
        if not eligible:
            rejected[reason] += 1
            continue
        eligible_by_category[category].append(row)

    selected: list[dict[str, Any]] = []
    category_counts: dict[str, int] = {}
    for category, quota in quotas.items():
        candidates = sorted(
            eligible_by_category[category],
            key=lambda row: selection_key(row, category),
            reverse=True,
        )
        if len(candidates) < quota:
            raise ValueError(f"{category} has {len(candidates)} eligible records; {quota} required")
        lane_rows = candidates[:quota]
        category_counts[category] = len(lane_rows)
        for lane_rank, source_row in enumerate(lane_rows, 1):
            row: dict[str, Any] = dict(source_row)
            clean_customer_property_zip(row)
            row["evaluation_batch_id"] = args.batch_id
            row["evaluation_lane_rank"] = lane_rank
            row["official_parcel_source_url"] = MASSACHUSETTS_PARCEL_URL
            row["public_record_scope"] = (
                "Public assessor and court data; no phone number, email address, or skip-trace contact data"
            )
            row["category_evidence_note"] = lane_note(category)
            selected.append(row)

    category_order = {category: index for index, category in enumerate(quotas)}
    selected.sort(key=lambda row: (
        category_order[clean(row.get("primary_category_key"))],
        int(number(row.get("evaluation_lane_rank"))),
    ))

    parcel_keys = [clean(row.get("parcel_id")).upper() for row in selected]
    if len(selected) != args.limit or len(set(parcel_keys)) != args.limit:
        raise ValueError("evaluation batch is not exactly one row per parcel")

    added_fields = [
        "evaluation_batch_id", "evaluation_lane_rank", "official_parcel_source_url",
        "public_record_scope", "category_evidence_note",
    ]
    output_fields = list(source_fields)
    insert_at = output_fields.index("source_name") if "source_name" in output_fields else len(output_fields)
    for field in reversed(added_fields):
        output_fields.insert(insert_at, field)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    master_path = args.output_dir / f"{args.batch_id}.csv"
    preview_path = args.output_dir / f"{args.batch_id}-review-preview.csv"
    write_csv(master_path, output_fields, selected)
    write_csv(preview_path, output_fields, selected[:25])

    category_outputs: dict[str, dict[str, Any]] = {}
    for category in quotas:
        lane_rows = [row for row in selected if clean(row.get("primary_category_key")) == category]
        lane_path = args.output_dir / "qa" / "massachusetts-statewide" / category / f"{category}.csv"
        write_csv(lane_path, output_fields, lane_rows)
        values = [number(row.get("total_value")) for row in lane_rows if number(row.get("total_value")) > 0]
        category_outputs[category] = {
            "label": CATEGORY_LABELS[category],
            "records": len(lane_rows),
            "eligible_after_quality_filters": len(eligible_by_category[category]),
            "median_official_value": median(values) if values else None,
            "path": str(lane_path),
            "sha256": file_sha256(lane_path),
            "definition": lane_note(category),
        }

    coverage_fields = (
        "owner_name", "property_address", "mailing_address", "mailing_city",
        "mailing_state", "mailing_zip", "parcel_id", "land_value",
        "building_value", "total_value", "acreage", "years_owned", "USE_CODE",
        "USE_DESC", "LS_DATE", "LS_PRICE", "YEAR_BUILT", "BLD_AREA", "UNITS",
    )
    coverage = {
        field: sum(bool(clean(row.get(field))) for row in selected)
        for field in coverage_fields
    }
    counties = Counter(clean(row.get("county")) or "Unknown" for row in selected)
    municipalities = Counter(clean(row.get("municipality")) or "Unknown" for row in selected)
    fiscal_years = Counter(clean(row.get("FY")) or "missing" for row in selected)
    values = [number(row.get("total_value")) for row in selected if number(row.get("total_value")) > 0]

    metadata: dict[str, Any] = {
        "ok": True,
        "status": "held for Derrick and Claude review; not sent to customer",
        "batch_id": args.batch_id,
        "prospect": "DeShawn Bunch",
        "market": "Massachusetts statewide",
        "purpose": "Private free evaluation batch",
        "records": len(selected),
        "unique_parcels": len(set(parcel_keys)),
        "duplicate_parcels": len(parcel_keys) - len(set(parcel_keys)),
        "fields": len(output_fields),
        "phone_numbers_included": False,
        "email_addresses_included": False,
        "skip_tracing_included": False,
        "contact_data_note": "Official Massachusetts parcel and court sources do not publish phone numbers or email addresses in these bulk files.",
        "selection_profile": quotas,
        "category_outputs": category_outputs,
        "field_coverage_records": coverage,
        "selected_fiscal_years": dict(sorted(fiscal_years.items())),
        "median_official_value": median(values) if values else None,
        "top_counties": counties.most_common(14),
        "top_municipalities": municipalities.most_common(25),
        "source": source_meta.get("source", {}),
        "source_package_sha256": file_sha256(args.master),
        "selection_filters": {
            "complete_owner_property_parcel_and_mailing_fields": True,
            "minimum_fiscal_year": args.min_fiscal_year,
            "obvious_non_acquisition_use_descriptions_removed": True,
            "commercial_minimum_total_value": 100_000,
            "commercial_minimum_building_value": 50_000,
            "vacant_land_minimum_value": 10_000,
            "vacant_land_minimum_acreage": 0.1,
        },
        "rejected_from_15000_source_package": dict(rejected),
        "outputs": {
            "full_csv": str(master_path),
            "review_preview_csv": str(preview_path),
        },
        "full_csv_sha256": file_sha256(master_path),
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    meta_path = args.output_dir / f"{args.batch_id}-meta.json"
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    readme_lines = [
        "LEADCURATE MASSACHUSETTS PRIVATE EVALUATION BATCH",
        "",
        f"Batch: {args.batch_id}",
        f"Properties: {len(selected):,} unique parcels",
        f"Fields retained: {len(output_fields)} public-record and LeadCurate review fields",
        f"Parcel service last edited: {metadata['source'].get('parcel_data_last_edited_utc', 'See metadata')}",
        "Status: Held for Derrick and Claude review. Not sent to DeShawn.",
        "",
        "CONTACT INFORMATION",
        "The files include official owner names and owner mailing addresses where published.",
        "They do not include phone numbers or email addresses because those fields are not in the official bulk sources.",
        "No skip tracing was performed and no missing contact field was guessed.",
        "",
        "EVALUATION MIX",
    ]
    for category, count in quotas.items():
        readme_lines.append(f"{CATEGORY_LABELS[category]}: {count:,}")
    readme_lines.extend([
        "",
        "WHAT EACH ROW CAN CONTAIN",
        "Owner name, property address, owner mailing address, parcel ID, municipality, county, official property use, land value, building value, total assessed value, acreage, last sale date and price, ownership years, fiscal year, zoning, building facts, source URLs, and court filing details where a current event match exists.",
        "",
        "IMPORTANT CATEGORY DEFINITIONS",
        "Pre-foreclosure means an exact parcel match to a current Land Court Servicemembers filing. It is not a foreclosure judgment.",
        "Tax title means an exact parcel match to the current Land Court tax-title report.",
        "Commercial and multifamily rows are official property classes with absentee ownership or at least 10 years of ownership. They are not labeled as verified distress events.",
        "Vacant land passed the current parcel and no-improvement checks. Obvious utility, right-of-way, conservation, wetland, cemetery, and undevelopable descriptions were removed from this evaluation cut.",
        "Tired landlords have an absentee mailing signal, a residential improvement, and at least 10 years of recorded ownership.",
        "Out-of-state owners have an official owner mailing state outside Massachusetts.",
        "",
        "USE AND RELEASE",
        "This is a private evaluation batch. Do not send it until Derrick approves the exact file after Claude review.",
        "The full 15,000-parcel territory package is separate and is not part of this free release.",
    ])
    readme_path = args.output_dir / "README.txt"
    readme_path.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")
    metadata["outputs"]["metadata"] = str(meta_path)
    metadata["outputs"]["readme"] = str(readme_path)
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True)
    parser.add_argument("--source-meta", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--batch-id", default="deshawn-massachusetts-evaluation-800-2026-08-26")
    parser.add_argument("--limit", type=int, default=800)
    parser.add_argument("--min-fiscal-year", type=int, default=2025)
    args = parser.parse_args()
    payload = build(args)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
