#!/usr/bin/env python3
"""Build the freshest Wayne MI parcel universe with a Detroit breakout.

Outer Wayne municipalities use the county's 2026 post-Board-of-Review roll.
Detroit rows are replaced by the city's daily current parcel service and are
enriched with the city's separate 2026 tentative assessment fields.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path


EXTRA_FIELDS = [
    "property_class_description",
    "use_code_description",
    "sale_date",
    "sale_price",
    "year_built",
    "building_style",
    "num_buildings",
    "total_floor_area",
    "total_square_footage",
    "tax_status_description",
    "estimated_true_cash_value",
    "source_component",
    "source_last_edit_at",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def key(value: object) -> str:
    return "".join(character for character in clean(value) if character.isdigit())


def number(value: object) -> float:
    try:
        return float(clean(value).replace(",", ""))
    except ValueError:
        return 0.0


def display_number(value: float) -> int | float:
    return int(value) if value.is_integer() else value


def load_tentative(path: Path) -> dict[str, dict[str, str]]:
    fields = (
        "amt_land_value",
        "amt_estimated_true_cash_value",
        "amt_assessed_value_tentative",
        "amt_taxable_value_tentative",
    )
    result: dict[str, dict[str, str]] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            parcel = key(row.get("parcel_id"))
            if parcel:
                result[parcel] = {field: clean(row.get(field)) for field in fields}
    return result


def detroit_row(row: dict[str, str], tentative: dict[str, dict[str, str]]) -> dict[str, object]:
    parcel = key(row.get("parcel_id"))
    assessment = tentative.get(parcel, {})
    assessed = number(row.get("amt_assessed_value"))
    description = clean(row.get("property_class_description"))
    improved = clean(row.get("is_improved")) not in {"", "0", "False", "false"}
    tentative_land = number(assessment.get("amt_land_value"))
    if "VACANT" in description.upper() or not improved:
        land_assessment = assessed
        building_assessment = 0.0
    else:
        land_assessment = min(assessed, tentative_land) if tentative_land > 0 else 0.0
        building_assessment = max(0.0, assessed - land_assessment)
    owner_1 = clean(row.get("taxpayer_1"))
    owner_2 = clean(row.get("taxpayer_2"))
    return {
        "parcel_id": clean(row.get("parcel_id")),
        "gov_unit": "01",
        "tax_unit": "01",
        "record_status": "A",
        "owner_name": " ".join(value for value in (owner_1, owner_2) if value),
        "owner_name_1": owner_1,
        "owner_name_2": owner_2,
        "property_street": clean(row.get("address")),
        "property_city": "Detroit",
        "property_state": "MI",
        "property_zip": clean(row.get("zip_code")),
        "owner_care_of": "",
        "owner_street": clean(row.get("taxpayer_address")),
        "owner_city": clean(row.get("taxpayer_city")),
        "owner_state": clean(row.get("taxpayer_state")),
        "owner_zip": clean(row.get("taxpayer_zip_code")),
        "owner_country": "",
        "current_taxable_status": clean(row.get("tax_status")),
        "property_class": clean(row.get("property_class")),
        "class_number": "",
        "use_code": clean(row.get("use_code")),
        "pre_pct": clean(row.get("pct_pre_claimed")),
        "assessed_value": display_number(assessed),
        "capped_value": "",
        "taxable_value": clean(row.get("amt_taxable_value")),
        "previous_assessed_value": clean(row.get("amt_assessed_value_previous")),
        "land_assessment": display_number(land_assessment),
        "building_assessment": display_number(building_assessment),
        "latest_transfer_pct": "",
        "latest_transfer_date": clean(row.get("sale_date"))[:10],
        "land_value": clean(assessment.get("amt_land_value")),
        "acreage": clean(row.get("total_acreage")),
        "frontage": clean(row.get("frontage")),
        "average_depth": clean(row.get("depth")),
        "map_number": clean(row.get("landmap")),
        "municipality": "Detroit",
        "property_class_description": description,
        "use_code_description": clean(row.get("use_code_description")),
        "sale_date": clean(row.get("sale_date"))[:10],
        "sale_price": clean(row.get("amt_sale_price")),
        "year_built": clean(row.get("year_built")),
        "building_style": clean(row.get("building_style")),
        "num_buildings": clean(row.get("num_buildings")),
        "total_floor_area": clean(row.get("total_floor_area")),
        "total_square_footage": clean(row.get("total_square_footage")),
        "tax_status_description": clean(row.get("tax_status_description")),
        "estimated_true_cash_value": clean(assessment.get("amt_estimated_true_cash_value")),
        "source_component": "detroit_current_parcels",
        "source_last_edit_at": "2026-07-15T20:35:17.567Z",
    }


def build(outer: Path, detroit: Path, tentative_path: Path, output: Path) -> dict[str, object]:
    tentative = load_tentative(tentative_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    outer_rows = 0
    detroit_rows = 0
    duplicate_rows = 0
    with outer.open(newline="", encoding="utf-8-sig") as outer_handle:
        reader = csv.DictReader(outer_handle)
        fields = [*reader.fieldnames, *[field for field in EXTRA_FIELDS if field not in reader.fieldnames]]
        with output.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for row in reader:
                if clean(row.get("municipality")) == "Detroit":
                    continue
                parcel = key(row.get("parcel_id"))
                if not parcel or parcel in seen:
                    duplicate_rows += bool(parcel)
                    continue
                seen.add(parcel)
                row["source_component"] = "wayne_2026_post_board_of_review"
                row["source_last_edit_at"] = "2026-06-04"
                writer.writerow(row)
                outer_rows += 1
            with detroit.open(newline="", encoding="utf-8-sig") as detroit_handle:
                for source_row in csv.DictReader(detroit_handle):
                    row = detroit_row(source_row, tentative)
                    parcel = key(row["parcel_id"])
                    if not parcel or parcel in seen:
                        duplicate_rows += bool(parcel)
                        continue
                    seen.add(parcel)
                    writer.writerow(row)
                    detroit_rows += 1
    metadata = {
        "market": "wayne-mi",
        "canonical": str(output),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_components": {
            "outer_wayne": str(outer),
            "detroit_current_parcels": str(detroit),
            "detroit_2026_tentative_assessment": str(tentative_path),
        },
        "outer_wayne_records": outer_rows,
        "detroit_records": detroit_rows,
        "detroit_tentative_records_loaded": len(tentative),
        "records": outer_rows + detroit_rows,
        "unique_parcels": len(seen),
        "duplicate_parcels_removed": duplicate_rows,
        "field_count": len(fields),
        "verification": {
            "one_row_per_parcel": outer_rows + detroit_rows == len(seen),
            "detroit_replaced_not_stacked": detroit_rows > 0 and outer_rows > 0,
        },
    }
    output.with_name(output.stem + "-meta.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wayne-canonical", type=Path, required=True)
    parser.add_argument("--detroit-current", type=Path, required=True)
    parser.add_argument("--detroit-assessment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.wayne_canonical, args.detroit_current, args.detroit_assessment, args.output)
    print(json.dumps(result, indent=2))
    return 0 if result["verification"]["one_row_per_parcel"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
