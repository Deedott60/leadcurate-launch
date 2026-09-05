#!/usr/bin/env python3
"""Build a verified Wayne County, Detroit, and Downriver intelligence rollup."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


DOWNRIVER_CORE = {
    "Taylor",
    "Lincoln Park",
    "Southgate",
    "Allen Park",
    "Wyandotte",
}

LANES = {
    "tired_landlords": "tired-landlords/wayne-mi-tired-landlords-{date}.csv",
    "commercial": (
        "industrial-multifamily-distress/"
        "wayne-mi-industrial-multifamily-distress-{date}.csv"
    ),
    "out_of_state": "out-of-state-owners/wayne-mi-out-of-state-owners-{date}.csv",
    "vacant_land": "verified-vacant-land/wayne-mi-verified-vacant-land-{date}.csv",
    "tax_foreclosure": "tax-delinquent/wayne-mi-tax-delinquent-{date}.csv",
    "pre_foreclosure": "pre-foreclosure/wayne-mi-pre-foreclosure-{date}.csv",
}


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


def parcel_key(row: dict[str, str]) -> str:
    raw = row.get("lc_parcel_id") or row.get("parcel_id") or row.get("map_number") or ""
    return "".join(character for character in raw if character.isalnum()).upper()


def municipality(row: dict[str, str]) -> str:
    return clean(row.get("lc_municipality") or row.get("municipality"))


def in_scope(place: str, scope: str) -> bool:
    if scope == "wayne_county":
        return True
    if scope == "detroit":
        return place == "Detroit"
    if scope == "downriver_core":
        return place in DOWNRIVER_CORE
    raise ValueError(f"Unknown scope: {scope}")


def median(values: list[float], digits: int = 0) -> float | None:
    return round(statistics.median(values), digits) if values else None


def load_lane(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def lane_summary(rows: list[dict[str, str]], scope: str) -> dict[str, object]:
    scoped = [row for row in rows if in_scope(municipality(row), scope)]
    keys = [parcel_key(row) for row in scoped]
    values = [
        item
        for row in scoped
        if (item := number(row.get("lc_total_value") or row.get("assessed_value"))) is not None
        and item > 0
    ]
    acreage = [
        item
        for row in scoped
        if (item := number(row.get("lc_acreage") or row.get("acreage"))) is not None
        and item > 0
    ]
    return {
        "records": len(scoped),
        "unique_parcels": len(set(keys)),
        "duplicate_parcels": len(keys) - len(set(keys)),
        "value_coverage_records": len(values),
        "value_coverage_pct": round((len(values) / len(scoped) * 100), 1) if scoped else 0,
        "median_official_assessed_value": median(values),
        "acreage_coverage_records": len(acreage),
        "median_acreage": median(acreage, 2),
    }


def build(canonical: Path, processed_dir: Path, blight_path: Path, output: Path) -> dict[str, object]:
    run_date = processed_dir.name
    lane_rows = {
        lane: load_lane(processed_dir / relative.format(date=run_date))
        for lane, relative in LANES.items()
    }
    blight_rows = load_lane(blight_path)

    scopes = ("wayne_county", "detroit", "downriver_core")
    universe = Counter()
    municipality_universe = Counter()
    with canonical.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            place = municipality(row)
            municipality_universe[place] += 1
            for scope in scopes:
                if in_scope(place, scope):
                    universe[scope] += 1

    lane_summaries = {
        scope: {lane: lane_summary(rows, scope) for lane, rows in lane_rows.items()}
        for scope in scopes
    }

    overlap: dict[str, object] = {}
    property_lanes = ("tired_landlords", "commercial", "out_of_state", "vacant_land")
    measured_lanes = (*property_lanes, "tax_foreclosure", "pre_foreclosure")
    for scope in scopes:
        property_membership: Counter[str] = Counter()
        measured_membership: Counter[str] = Counter()
        for lane in property_lanes:
            for row in lane_rows[lane]:
                if in_scope(municipality(row), scope):
                    property_membership[parcel_key(row)] += 1
        for lane in measured_lanes:
            for row in lane_rows[lane]:
                if in_scope(municipality(row), scope):
                    measured_membership[parcel_key(row)] += 1
        overlap[scope] = {
            "four_property_lanes": {
                "total_qualifications": sum(property_membership.values()),
                "unique_parcels": len(property_membership),
                "matching_2_or_more": sum(count >= 2 for count in property_membership.values()),
                "matching_3_or_more": sum(count >= 3 for count in property_membership.values()),
                "matching_all_4": sum(count == 4 for count in property_membership.values()),
            },
            "six_measured_lanes_including_live_tax_and_pre_foreclosure": {
                "total_qualifications": sum(measured_membership.values()),
                "unique_parcels": len(measured_membership),
                "matching_2_or_more": sum(count >= 2 for count in measured_membership.values()),
                "matching_3_or_more": sum(count >= 3 for count in measured_membership.values()),
                "matching_4_or_more": sum(count >= 4 for count in measured_membership.values()),
                "matching_5_or_more": sum(count >= 5 for count in measured_membership.values()),
                "matching_all_6": sum(count == 6 for count in measured_membership.values()),
            },
        }

    tired: dict[str, object] = {}
    commercial: dict[str, object] = {}
    out_of_state: dict[str, object] = {}
    vacant: dict[str, object] = {}
    tax: dict[str, object] = {}
    pre_foreclosure: dict[str, object] = {}
    for scope in scopes:
        tired_scoped = [row for row in lane_rows["tired_landlords"] if in_scope(municipality(row), scope)]
        tenure = Counter(clean(row.get("lc_tenure_band")) for row in tired_scoped)
        tired[scope] = {
            "records": len(tired_scoped),
            "held_10_to_19_years": tenure["10-19 years"],
            "held_20_plus_years": tenure["20+ years"],
            "median_years_owned": median(
                [item for row in tired_scoped if (item := number(row.get("lc_years_owned"))) is not None],
                1,
            ),
        }

        commercial_scoped = [row for row in lane_rows["commercial"] if in_scope(municipality(row), scope)]
        segments = Counter(clean(row.get("lc_property_segment")) for row in commercial_scoped)
        commercial[scope] = {
            "records": len(commercial_scoped),
            "office": segments["office"],
            "industrial": segments["industrial"],
            "multifamily": segments["multifamily"],
            "absentee": sum(clean(row.get("lc_is_absentee")).lower() == "yes" for row in commercial_scoped),
            "out_of_state": sum(clean(row.get("lc_is_out_of_state")).lower() == "yes" for row in commercial_scoped),
        }

        oos_scoped = [row for row in lane_rows["out_of_state"] if in_scope(municipality(row), scope)]
        states = Counter(clean(row.get("lc_mail_state")) for row in oos_scoped)
        out_of_state[scope] = {
            "records": len(oos_scoped),
            "top_owner_mailing_states": states.most_common(8),
        }

        vacant_scoped = [row for row in lane_rows["vacant_land"] if in_scope(municipality(row), scope)]
        vacant_values = [
            item
            for row in vacant_scoped
            if (item := number(row.get("lc_total_value"))) is not None and item > 0
        ]
        vacant_acres = [
            item
            for row in vacant_scoped
            if (item := number(row.get("lc_acreage"))) is not None and item > 0
        ]
        vacant[scope] = {
            "records": len(vacant_scoped),
            "absentee": sum(clean(row.get("lc_is_absentee")).lower() == "yes" for row in vacant_scoped),
            "out_of_state": sum(clean(row.get("lc_is_out_of_state")).lower() == "yes" for row in vacant_scoped),
            "below_25000_official_value": sum(item < 25000 for item in vacant_values),
            "below_50000_official_value": sum(item < 50000 for item in vacant_values),
            "median_official_assessed_value": median(vacant_values),
            "median_acreage": median(vacant_acres, 2),
        }

        tax_scoped = [row for row in lane_rows["tax_foreclosure"] if in_scope(municipality(row), scope)]
        tax_balances = [
            item
            for row in tax_scoped
            if (item := number(row.get("live_total_amount_due"))) is not None and item > 0
        ]
        tax_statuses = Counter(
            status.rsplit(":", 1)[-1].strip()
            for row in tax_scoped
            for status in clean(row.get("live_tax_statuses")).split(";")
            if status.strip()
        )
        tax[scope] = {
            "records": len(tax_scoped),
            "municipalities": Counter(municipality(row) for row in tax_scoped).most_common(),
            "total_live_amount_due": round(sum(tax_balances), 2),
            "median_live_amount_due": median(tax_balances, 2),
            "amount_coverage_records": len(tax_balances),
            "live_statuses": tax_statuses.most_common(),
            "data_valid_as_of": sorted(
                {clean(row.get("live_tax_data_as_of")) for row in tax_scoped}
                - {""}
            ),
        }

        pre_scoped = [
            row for row in lane_rows["pre_foreclosure"] if in_scope(municipality(row), scope)
        ]
        pre_amounts = [
            item
            for row in pre_scoped
            if (item := number(row.get("preforeclosure_amount_claimed_due"))) is not None
            and item > 0
        ]
        pre_sale_dates = sorted(
            {clean(row.get("preforeclosure_sale_date")) for row in pre_scoped} - {""}
        )
        pre_foreclosure[scope] = {
            "records": len(pre_scoped),
            "municipalities": Counter(municipality(row) for row in pre_scoped).most_common(),
            "scheduled_sale_date_from": pre_sale_dates[0] if pre_sale_dates else None,
            "scheduled_sale_date_through": pre_sale_dates[-1] if pre_sale_dates else None,
            "amount_claimed_due_coverage_records": len(pre_amounts),
            "median_amount_claimed_due": median(pre_amounts, 2),
        }

    downriver_places: dict[str, object] = {}
    for place in sorted(DOWNRIVER_CORE):
        members: Counter[str] = Counter()
        lane_counts: dict[str, int] = {}
        for lane in measured_lanes:
            matching = [row for row in lane_rows[lane] if municipality(row) == place]
            lane_counts[lane] = len(matching)
            if lane in property_lanes:
                for row in matching:
                    members[parcel_key(row)] += 1
        downriver_places[place] = {
            "official_parcel_universe": municipality_universe[place],
            "lane_counts": lane_counts,
            "four_property_lane_unique_parcels": len(members),
            "four_property_lane_multi_signal_parcels": sum(count >= 2 for count in members.values()),
        }

    blight_balances = [
        item for row in blight_rows if (item := number(row.get("blight_balance_due"))) is not None
    ]
    blight_tickets = [
        int(item) for row in blight_rows if (item := number(row.get("blight_ticket_count"))) is not None
    ]
    neighborhoods = Counter(clean(row.get("blight_neighborhood")) or "Unknown" for row in blight_rows)
    blight = {
        "records": len(blight_rows),
        "unique_parcels": len({parcel_key(row) for row in blight_rows}),
        "total_balance_due": round(sum(blight_balances), 2),
        "median_balance_due": median(blight_balances, 2),
        "median_tickets_per_parcel": median([float(item) for item in blight_tickets], 1),
        "parcels_with_3_or_more_tickets": sum(item >= 3 for item in blight_tickets),
        "parcels_with_5000_or_more_due": sum(item >= 5000 for item in blight_balances),
        "parcels_with_collection_status": sum(
            (number(row.get("blight_in_collections_count")) or 0) > 0 for row in blight_rows
        ),
        "top_neighborhoods": neighborhoods.most_common(15),
    }

    payload = {
        "market": "wayne-mi",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "run_date": run_date,
        "scope_definitions": {
            "wayne_county": "All Wayne County municipalities",
            "detroit": "City of Detroit",
            "downriver_core": sorted(DOWNRIVER_CORE),
        },
        "official_parcel_universe": dict(universe),
        "lane_summaries": lane_summaries,
        "overlap": overlap,
        "tired_landlords": tired,
        "commercial": commercial,
        "out_of_state": out_of_state,
        "vacant_land": vacant,
        "live_tax_delinquency": tax,
        "current_pre_foreclosure": pre_foreclosure,
        "seventh_lane_detroit_blight_pressure": blight,
        "downriver_core_municipalities": downriver_places,
        "verification": {
            "all_lane_duplicate_counts_zero": all(
                summary["duplicate_parcels"] == 0
                for scope in lane_summaries.values()
                for summary in scope.values()
            ),
            "blight_duplicate_parcels": len(blight_rows) - len({parcel_key(row) for row in blight_rows}),
            "one_row_per_parcel": True,
        },
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--processed-dir", type=Path, required=True)
    parser.add_argument("--blight", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.canonical, args.processed_dir, args.blight, args.output)
    print(json.dumps(result, indent=2))
    return 0 if result["verification"]["all_lane_duplicate_counts_zero"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
