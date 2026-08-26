#!/usr/bin/env python3
"""Build a ranked, deduplicated Massachusetts acquisition package.

The builder streams the current MassGIS statewide parcel file, joins only
verified Land Court event matches, assigns every selected parcel to one
primary category, and preserves all other qualifying category flags.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import heapq
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any

from lane_quality import INSTITUTIONAL_OWNER, validate_role_mapping
from process_investor_lanes import ENTITY_OWNER, MARKETS, clean, derive, matches


STANDARD_DELIVERY_FIELDS = (
    "owner_name",
    "property_address",
    "property_city",
    "property_zip",
    "mailing_address",
    "mailing_city",
    "mailing_state",
    "mailing_zip",
    "parcel_id",
    "property_type",
    "land_value",
    "building_value",
    "total_value",
    "acreage",
    "years_owned",
    "category",
    "county",
    "source_name",
    "source_cycle",
)

CATEGORY_ORDER = (
    "pre-foreclosure",
    "tax-title",
    "multifamily",
    "office",
    "industrial",
    "verified-vacant-land",
    "tired-landlords",
    "out-of-state-owners",
)

# Reserve scarce or explicitly requested segments before broad ownership lanes.
# The master stays deduplicated, while all overlaps remain visible in
# all_verified_categories.
SELECTION_ORDER = (
    "pre-foreclosure",
    "tax-title",
    "out-of-state-owners",
    "verified-vacant-land",
    "multifamily",
    "office",
    "industrial",
    "tired-landlords",
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

DEFAULT_QUOTAS = {
    "pre-foreclosure": 1000,
    "tax-title": 200,
    "multifamily": 4500,
    "office": 1000,
    "industrial": 1500,
    "verified-vacant-land": 4000,
    "tired-landlords": 2200,
    "out-of-state-owners": 1200,
}

SOURCE_URL = (
    "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/"
    "Massachusetts_Property_Tax_Parcels/FeatureServer/0"
)
REPORT_URL = "https://www.mass.gov/lists/land-court-masscourts-reports"
PROBATE_URL = (
    "https://www.mass.gov/info-details/probate-and-family-court-access-to-"
    "public-court-records-frequently-asked-questions"
)


def number(value: Any) -> float:
    try:
        return float(re.sub(r"[^0-9.\-]", "", str(value or "")) or 0)
    except ValueError:
        return 0.0


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_events(path: Path, lane: str) -> dict[str, dict[str, str]]:
    if not path.exists():
        return {}
    events: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.DictReader(handle):
            parcel = clean(row.get("lc_parcel_id") or row.get("LC_PARCEL_KEY")).upper()
            if not parcel:
                continue
            events[parcel] = {
                "event_lane": lane,
                "event_status": clean(row.get("lc_event_status")),
                "case_number": clean(row.get("lc_case_number")),
                "filed_date": clean(row.get("lc_filed_date")),
                "plaintiff": clean(row.get("lc_plaintiff")),
                "defendant": clean(row.get("lc_defendant")),
                "event_source_url": clean(row.get("lc_source_url")),
            }
    return events


def category_flags(
    source: dict[str, str],
    derived: dict[str, Any],
    pre: dict[str, dict[str, str]],
    tax: dict[str, dict[str, str]],
    cfg: dict[str, Any],
) -> list[str]:
    parcel = clean(derived["lc_parcel_id"]).upper()
    flags: list[str] = []
    if parcel in pre:
        flags.append("pre-foreclosure")
    if parcel in tax:
        flags.append("tax-title")
    segment = derived["lc_property_segment"]
    ownership_pressure = (
        derived["lc_is_absentee"] == "yes"
        or isinstance(derived["lc_years_owned"], (int, float))
        and derived["lc_years_owned"] >= 10
    )
    if (
        segment in {"multifamily", "office", "industrial"}
        and ownership_pressure
        and derived["lc_verified_vacant"] != "yes"
    ):
        flags.append(segment)
    if derived["lc_verified_vacant"] == "yes":
        flags.append("verified-vacant-land")
    if matches("tired-landlords", source, derived, cfg):
        flags.append("tired-landlords")
    if matches("out-of-state-owners", source, derived, cfg):
        flags.append("out-of-state-owners")
    return flags


def priority_score(derived: dict[str, Any], flags: list[str]) -> tuple[int, list[str]]:
    score = 0
    reasons: list[str] = []
    weights = {
        "pre-foreclosure": 100,
        "tax-title": 110,
        "multifamily": 32,
        "office": 28,
        "industrial": 28,
        "verified-vacant-land": 35,
        "tired-landlords": 25,
        "out-of-state-owners": 20,
    }
    for flag in flags:
        score += weights[flag]
        reasons.append(CATEGORY_LABELS[flag])
    tenure = derived["lc_years_owned"]
    if isinstance(tenure, (int, float)) and tenure >= 20:
        score += 18
        reasons.append("20+ years owned")
    elif isinstance(tenure, (int, float)) and tenure >= 10:
        score += 10
        reasons.append("10 to 19 years owned")
    if derived["lc_is_absentee"] == "yes":
        score += 10
    if derived["lc_is_out_of_state"] == "yes":
        score += 8
    if len(flags) > 1:
        score += min(30, (len(flags) - 1) * 10)
        reasons.append(f"{len(flags)} verified categories")
    if derived["lc_total_value"] > 0:
        score += 4
    if derived["lc_mailing_address"]:
        score += 3
    if derived["lc_property_segment"] == "multifamily":
        score += 4
    return score, reasons


def candidate_row(
    source: dict[str, str],
    derived: dict[str, Any],
    flags: list[str],
    score: int,
    reasons: list[str],
    pre: dict[str, dict[str, str]],
    tax: dict[str, dict[str, str]],
    source_cycle: str,
    source_data_date: str,
) -> dict[str, Any]:
    parcel = clean(derived["lc_parcel_id"]).upper()
    event = pre.get(parcel) or tax.get(parcel) or {}
    segment = clean(derived["lc_property_segment"])
    use_code = clean(source.get("USE_CODE"))
    row: dict[str, Any] = {
        "owner_name": derived["lc_owner_name"],
        "property_address": derived["lc_property_address"],
        "property_city": clean(source.get("CITY")),
        "property_zip": clean(source.get("ZIP")),
        "mailing_address": derived["lc_mailing_address"],
        "mailing_city": clean(source.get("OWN_CITY")),
        "mailing_state": clean(source.get("OWN_STATE")),
        "mailing_zip": clean(source.get("OWN_ZIP")),
        "parcel_id": derived["lc_parcel_id"],
        "property_type": " / ".join(part for part in (segment, use_code) if part),
        "land_value": derived["lc_land_value"],
        "building_value": derived["lc_building_value"],
        "total_value": derived["lc_total_value"],
        "acreage": derived["lc_acreage"],
        "years_owned": derived["lc_years_owned"],
        "category": "",
        "county": derived["lc_county"],
        "source_name": "MassGIS property-tax parcels" + (" plus Massachusetts Land Court" if event else ""),
        "source_cycle": source_cycle,
        "acquisition_priority_score": score,
        "priority_tier": "A" if score >= 90 else "B" if score >= 60 else "C",
        "priority_reasons": "; ".join(dict.fromkeys(reasons)),
        "verified_category_count": len(flags),
        "all_verified_categories": "; ".join(CATEGORY_LABELS[flag] for flag in flags),
        "is_absentee_owner": derived["lc_is_absentee"],
        "is_out_of_state_owner": derived["lc_is_out_of_state"],
        "is_verified_vacant_land": derived["lc_verified_vacant"],
        "municipality": derived["lc_municipality"],
        "property_segment": segment,
        "source_data_date": source_data_date,
        "event_status": event.get("event_status", ""),
        "case_number": event.get("case_number", ""),
        "filed_date": event.get("filed_date", ""),
        "plaintiff": event.get("plaintiff", ""),
        "defendant": event.get("defendant", ""),
        "event_source_url": event.get("event_source_url", ""),
        "information_not_available": derived["Information Not Available"],
    }
    for key, value in source.items():
        if key not in row:
            row[key] = value
    return row


def push_candidate(heap: list[tuple[Any, ...]], limit: int, candidate: dict[str, Any]) -> None:
    parcel = clean(candidate["parcel_id"]).upper()
    score = int(candidate["acquisition_priority_score"])
    stable = int(hashlib.sha1(parcel.encode("utf-8")).hexdigest()[:12], 16)
    item = (score, stable, parcel, candidate)
    if len(heap) < limit:
        heapq.heappush(heap, item)
    elif item[:3] > heap[0][:3]:
        heapq.heapreplace(heap, item)


def ranked_candidates(heap: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    return [item[3] for item in sorted(heap, key=lambda item: item[:3], reverse=True)]


def output_sort(row: dict[str, Any]) -> tuple[Any, ...]:
    tier = {"A": 0, "B": 1, "C": 2}.get(clean(row.get("priority_tier")), 3)
    value = number(row.get("total_value"))
    return (tier, value <= 0, value, -int(number(row.get("acquisition_priority_score"))), clean(row.get("parcel_id")))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def count_csv(path: Path) -> int:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def ranking_rows(rows: list[dict[str, Any]], field: str, level: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[clean(row.get(field)) or "Unknown"].append(row)
    output: list[dict[str, Any]] = []
    for location, items in grouped.items():
        scores = [int(number(row.get("acquisition_priority_score"))) for row in items]
        values = [number(row.get("total_value")) for row in items if number(row.get("total_value")) > 0]
        categories = Counter(clean(row.get("category")) for row in items)
        output.append({
            "rank": 0,
            "level": level,
            "location": location,
            "selected_properties": len(items),
            "priority_a": sum(clean(row.get("priority_tier")) == "A" for row in items),
            "median_priority_score": median(scores) if scores else None,
            "median_official_value": median(values) if values else None,
            "pre_foreclosure": categories[CATEGORY_LABELS["pre-foreclosure"]],
            "tax_title": categories[CATEGORY_LABELS["tax-title"]],
            "multifamily": categories[CATEGORY_LABELS["multifamily"]],
            "office": categories[CATEGORY_LABELS["office"]],
            "industrial": categories[CATEGORY_LABELS["industrial"]],
            "verified_vacant_land": categories[CATEGORY_LABELS["verified-vacant-land"]],
            "tired_landlords": categories[CATEGORY_LABELS["tired-landlords"]],
            "out_of_state_owners": categories[CATEGORY_LABELS["out-of-state-owners"]],
        })
    output.sort(key=lambda row: (row["priority_a"], row["selected_properties"], row["median_priority_score"]), reverse=True)
    for index, row in enumerate(output, 1):
        row["rank"] = index
    return output


def write_package_readme(output_dir: Path, payload: dict[str, Any]) -> Path:
    categories = payload["category_outputs"]
    fiscal_years = ", ".join(
        f"FY {year}: {count:,}" for year, count in payload["selected_fiscal_years"].items()
    )
    lines = [
        "LEADCURATE MASSACHUSETTS ACQUISITION PACKAGE",
        "",
        f"Properties: {payload['records']:,} unique parcels",
        f"Fields: {payload['delivery_field_count']} columns",
        f"Parcel source retrieved: {payload['source']['parcel_retrieved_on']}",
        f"Parcel service last edited: {payload['source']['parcel_data_last_edited_utc']}",
        f"Included assessor fiscal years: {fiscal_years}",
        "Skip tracing: not included",
        "",
        "PRIMARY CATEGORY FILES",
    ]
    for category in CATEGORY_ORDER:
        lines.append(f"{CATEGORY_LABELS[category]}: {categories[category]['records']:,}")
    lines.extend([
        "",
        "WHAT THE FILES CONTAIN",
        "Owner name, property address, owner mailing address where public, parcel ID, official use code, land, building and total assessed values where public, acreage, last sale date and price where public, years owned, fiscal year, county, municipality, targeting score, targeting reasons, and current court case details where matched.",
        "",
        "HOW TO READ THE CATEGORIES",
        "Pre-foreclosure records are exact parcel matches to current Massachusetts Land Court Servicemembers filings. They are filing signals, not foreclosure judgments.",
        "Tax-title records are exact parcel matches to the current Massachusetts Land Court tax-lien report. The small count is the verified current match count, not an estimate of statewide tax delinquency.",
        "Office, industrial and multifamily records use the official property class plus absentee ownership or at least 10 years of ownership. They are ownership-pressure targets, not claims of a recorded foreclosure, tax debt or violation.",
        "Verified vacant land requires a nonpublic owner, an official Massachusetts vacant-use code, at least 0.1 acre, no building value, no other improvement value, total value matching land value, no year built and no building area.",
        "Tired landlords have at least 10 years of ownership, an absentee mailing signal, a residential use and building value above zero.",
        "Out-of-state owners have a public owner mailing state outside Massachusetts.",
        "A property appears once in the master and once in its primary category file. Other verified overlaps remain in all_verified_categories.",
        "",
        "RANKINGS AND LIMITATIONS",
        "The county and municipality ranking files are computed from the same 15,000 properties that ship.",
        "Probate is not included because Massachusetts provides public case search but no verified statewide bulk probate filing report. No owner-name keyword proxy was used.",
        "The priority score ranks verified public-record facts for outreach order. It does not prove seller motivation or willingness to sell.",
    ])
    path = output_dir / "README.txt"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def build(args: argparse.Namespace) -> dict[str, Any]:
    cfg = MARKETS["massachusetts-statewide"]
    pre = load_events(args.pre_foreclosure, "pre-foreclosure")
    tax = load_events(args.tax_title, "tax-title")
    heaps: dict[str, list[tuple[Any, ...]]] = {category: [] for category in CATEGORY_ORDER}
    eligible = Counter()
    skipped = Counter()
    source_rows = 0
    source_fields: list[str] = []
    with args.canonical.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        source_fields = list(reader.fieldnames or [])
        validate_role_mapping(source_fields, cfg["fields"], ("parcel", "owner", "property_street"))
        for source in reader:
            source_rows += 1
            fiscal_year = int(number(source.get("FY")))
            if fiscal_year < args.min_fiscal_year:
                skipped[f"fiscal_year_before_{args.min_fiscal_year}_or_missing"] += 1
                continue
            derived = derive(source, cfg)
            parcel = clean(derived["lc_parcel_id"])
            owner = clean(derived["lc_owner_name"])
            prop = clean(derived["lc_property_address"])
            if not parcel or not owner or not prop:
                skipped["missing_core_field"] += 1
                continue
            if INSTITUTIONAL_OWNER.search(owner):
                skipped["institutional_owner"] += 1
                continue
            flags = category_flags(source, derived, pre, tax, cfg)
            if not flags:
                continue
            score, reasons = priority_score(derived, flags)
            candidate = candidate_row(
                source, derived, flags, score, reasons, pre, tax,
                args.source_cycle, args.source_data_date,
            )
            for category in flags:
                eligible[category] += 1
                keep = min(args.limit + 5000, DEFAULT_QUOTAS[category] + 5000)
                push_candidate(heaps[category], keep, candidate)

    selected: list[dict[str, Any]] = []
    selected_keys: set[str] = set()
    selected_by_category = Counter()
    for category in SELECTION_ORDER:
        for candidate in ranked_candidates(heaps[category]):
            if len(selected) >= args.limit or selected_by_category[category] >= DEFAULT_QUOTAS[category]:
                break
            parcel = clean(candidate["parcel_id"]).upper()
            if parcel in selected_keys:
                continue
            row = dict(candidate)
            row["category"] = CATEGORY_LABELS[category]
            row["primary_category_key"] = category
            selected.append(row)
            selected_keys.add(parcel)
            selected_by_category[category] += 1

    if len(selected) < args.limit:
        fallback: list[dict[str, Any]] = []
        seen_fallback: set[str] = set()
        for category in CATEGORY_ORDER:
            for candidate in ranked_candidates(heaps[category]):
                parcel = clean(candidate["parcel_id"]).upper()
                if parcel in selected_keys or parcel in seen_fallback:
                    continue
                seen_fallback.add(parcel)
                fallback.append(candidate)
        fallback.sort(key=lambda row: (int(row["acquisition_priority_score"]), clean(row["parcel_id"])), reverse=True)
        for candidate in fallback:
            if len(selected) >= args.limit:
                break
            flags = clean(candidate["all_verified_categories"])
            first_label = next((CATEGORY_LABELS[c] for c in CATEGORY_ORDER if CATEGORY_LABELS[c] in flags), "Additional verified opportunity")
            row = dict(candidate)
            row["category"] = first_label
            row["primary_category_key"] = next((c for c in CATEGORY_ORDER if CATEGORY_LABELS[c] == first_label), "additional")
            selected.append(row)
            selected_keys.add(clean(row["parcel_id"]).upper())
            selected_by_category[row["primary_category_key"]] += 1

    selected.sort(key=output_sort)
    extra_fields = [
        "acquisition_priority_score", "priority_tier", "priority_reasons",
        "verified_category_count", "all_verified_categories", "primary_category_key",
        "is_absentee_owner", "is_out_of_state_owner", "is_verified_vacant_land",
        "municipality", "property_segment", "source_data_date", "event_status",
        "case_number", "filed_date", "plaintiff", "defendant", "event_source_url",
        "information_not_available",
    ]
    fields = list(STANDARD_DELIVERY_FIELDS) + extra_fields
    fields.extend(field for field in source_fields if field not in fields)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"massachusetts-acquisition-package-{args.source_cycle}"
    master = args.output_dir / f"{stem}.csv"
    preview = args.output_dir / f"{stem}-preview.csv"
    write_csv(master, fields, selected)
    write_csv(preview, fields, selected[:50])

    category_outputs: dict[str, dict[str, Any]] = {}
    for category in CATEGORY_ORDER:
        rows = [row for row in selected if row.get("primary_category_key") == category]
        path = args.output_dir / "categories" / category / f"{category}.csv"
        write_csv(path, fields, rows)
        category_outputs[category] = {
            "records": len(rows),
            "eligible_before_quota": eligible[category],
            "path": str(path),
            "sha256": file_sha256(path),
        }

    county_rows = ranking_rows(selected, "county", "county")
    municipality_rows = ranking_rows(selected, "municipality", "municipality")
    ranking_fields = list(county_rows[0]) if county_rows else []
    county_path = args.output_dir / "massachusetts-county-ranking.csv"
    municipality_path = args.output_dir / "massachusetts-municipality-ranking.csv"
    write_csv(county_path, ranking_fields, county_rows)
    write_csv(municipality_path, ranking_fields, municipality_rows)

    status_rows = [
        {"category": CATEGORY_LABELS[c], "status": "included", "records": selected_by_category[c], "source": REPORT_URL if c in {"pre-foreclosure", "tax-title"} else SOURCE_URL, "note": ""}
        for c in CATEGORY_ORDER
    ]
    status_rows.append({
        "category": "Probate and estate filings",
        "status": "unavailable for bulk delivery",
        "records": 0,
        "source": PROBATE_URL,
        "note": "Massachusetts provides public case search by name, case number, or case type, but no verified statewide bulk probate filing report. No owner-name keyword proxy was used.",
    })
    status_path = args.output_dir / "category-status.csv"
    write_csv(status_path, ["category", "status", "records", "source", "note"], status_rows)

    core_complete = sum(
        bool(clean(row.get("owner_name")) and clean(row.get("property_address")) and clean(row.get("parcel_id")))
        for row in selected
    )
    duplicate_count = len(selected) - len({clean(row.get("parcel_id")).upper() for row in selected})
    field_coverage = {
        field: sum(bool(clean(row.get(field))) for row in selected)
        for field in (
            "owner_name", "property_address", "mailing_address", "mailing_city",
            "mailing_state", "mailing_zip", "parcel_id", "land_value",
            "building_value", "total_value", "acreage", "years_owned",
            "LS_DATE", "LS_PRICE", "USE_CODE", "YEAR_BUILT",
        )
    }
    selected_fiscal_years = Counter(clean(row.get("FY")) or "missing" for row in selected)
    payload = {
        "ok": len(selected) == args.limit and duplicate_count == 0 and core_complete == len(selected),
        "market": "Massachusetts statewide",
        "package_purpose": "Free initial acquisition package for DeShawn Bunch",
        "source": {
            "parcel_url": SOURCE_URL,
            "parcel_data_last_edited_utc": args.source_data_date,
            "parcel_retrieved_on": args.source_cycle,
            "land_court_reports_url": REPORT_URL,
            "land_court_reports_retrieved_on": args.source_cycle,
            "canonical_file": str(args.canonical),
            "source_rows_streamed": source_rows,
        },
        "records": len(selected),
        "unique_parcels": len(selected_keys),
        "duplicate_parcels": duplicate_count,
        "core_field_complete_records": core_complete,
        "delivery_field_count": len(fields),
        "field_coverage_records": field_coverage,
        "selected_fiscal_years": dict(sorted(selected_fiscal_years.items())),
        "freshness_policy": f"Only MassGIS parcels with municipal fiscal year {args.min_fiscal_year} or newer were eligible.",
        "skip_tracing": "not included",
        "selection_method": "Verified category evidence, ownership tenure and location, category overlap, and public-record completeness. Score is a targeting priority, not proof of seller intent.",
        "category_outputs": category_outputs,
        "category_status_file": str(status_path),
        "probate_status": status_rows[-1],
        "skipped": dict(skipped),
        "outputs": {
            "master": str(master),
            "preview": str(preview),
            "county_ranking": str(county_path),
            "municipality_ranking": str(municipality_path),
        },
        "top_counties": county_rows[:10],
        "top_municipalities": municipality_rows[:15],
        "verification": {
            "master_rows": count_csv(master),
            "master_sha256": file_sha256(master),
            "preview_rows": count_csv(preview),
            "category_rows_sum_to_master": sum(item["records"] for item in category_outputs.values()) == len(selected),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    readme = write_package_readme(args.output_dir, payload)
    payload["outputs"]["readme"] = str(readme)
    meta = args.output_dir / f"{stem}-meta.json"
    meta.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a fresh Massachusetts acquisition package.")
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--pre-foreclosure", type=Path, required=True)
    parser.add_argument("--tax-title", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-cycle", required=True)
    parser.add_argument("--source-data-date", required=True)
    parser.add_argument("--limit", type=int, default=15000)
    parser.add_argument("--min-fiscal-year", type=int, default=2025)
    args = parser.parse_args()
    if args.limit < 1 or args.limit > 50000:
        parser.error("--limit must be between 1 and 50000")
    payload = build(args)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
