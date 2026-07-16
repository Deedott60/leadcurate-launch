#!/usr/bin/env python3
"""Aggregate current unpaid responsible Detroit blight tickets by parcel."""

from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


SOURCE_URL = (
    "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/"
    "blight_tickets/FeatureServer/0"
)
PUBLIC_OWNER = re.compile(
    r"\b(CITY OF|COUNTY OF|STATE OF|UNITED STATES|LAND BANK|SCHOOL|AUTHORITY|DISTRICT|CHURCH|MINISTR(?:Y|IES))\b",
    re.I,
)


def clean(value: object) -> str:
    return str(value or "").strip()


def parcel_key(value: object) -> str:
    return "".join(character for character in clean(value) if character.isdigit())


def number(value: object) -> float:
    try:
        return float(clean(value).replace("$", "").replace(",", ""))
    except ValueError:
        return 0.0


def redact(row: dict[str, object]) -> dict[str, object]:
    result = dict(row)
    for field in result:
        lower = field.lower()
        if any(token in lower for token in ("parcel", "owner", "address", "street", "map_number")):
            result[field] = "REDACTED"
    return result


def aggregate(path: Path) -> tuple[dict[str, dict[str, object]], int]:
    parcels: dict[str, dict[str, object]] = {}
    ticket_rows = 0
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            ticket_rows += 1
            key = parcel_key(row.get("parcel_id"))
            if not key:
                continue
            item = parcels.setdefault(
                key,
                {
                    "ticket_count": 0,
                    "balance_due": 0.0,
                    "judgment_amount": 0.0,
                    "payment_amount": 0.0,
                    "in_collections_count": 0,
                    "first_ticket_date": "",
                    "latest_ticket_date": "",
                    "latest_update_at": "",
                    "ordinances": Counter(),
                    "neighborhood": "",
                },
            )
            item["ticket_count"] = int(item["ticket_count"]) + 1
            item["balance_due"] = float(item["balance_due"]) + number(row.get("amt_balance_due"))
            item["judgment_amount"] = float(item["judgment_amount"]) + number(row.get("amt_judgment"))
            item["payment_amount"] = float(item["payment_amount"]) + number(row.get("amt_payment"))
            item["in_collections_count"] = int(item["in_collections_count"]) + (
                clean(row.get("collection_status")).lower() == "in collections"
            )
            issued = clean(row.get("ticket_issued_date"))[:10]
            updated = clean(row.get("ticket_updated_at"))
            if issued and (not item["first_ticket_date"] or issued < item["first_ticket_date"]):
                item["first_ticket_date"] = issued
            if issued and issued > item["latest_ticket_date"]:
                item["latest_ticket_date"] = issued
            if updated > item["latest_update_at"]:
                item["latest_update_at"] = updated
            ordinance = clean(row.get("ordinance_description")) or clean(row.get("ordinance_law"))
            if ordinance:
                ordinances = item["ordinances"]
                assert isinstance(ordinances, Counter)
                ordinances[ordinance] += 1
            if not item["neighborhood"]:
                item["neighborhood"] = clean(row.get("neighborhood"))
    return parcels, ticket_rows


def process(canonical: Path, blight: Path, output_dir: Path, preview_count: int) -> dict[str, object]:
    aggregated, ticket_rows = aggregate(blight)
    lane = "blight-pressure"
    lane_dir = output_dir / lane
    lane_dir.mkdir(parents=True, exist_ok=True)
    run_date = output_dir.name
    stem = f"detroit-mi-{lane}-{run_date}"
    full = lane_dir / f"{stem}.csv"
    preview = lane_dir / f"{stem}-preview.csv"
    meta = lane_dir / f"{stem}-meta.json"
    records = 0
    public_owner_rows = 0
    balances: list[float] = []
    ticket_counts: list[int] = []
    collections = 0
    matched_keys: set[str] = set()
    matched_source_keys: set[str] = set()
    preview_rows: list[dict[str, object]] = []
    neighborhoods: Counter[str] = Counter()
    with canonical.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        extra = [
            "lc_lane", "blight_ticket_count", "blight_balance_due", "blight_judgment_amount",
            "blight_payment_amount", "blight_in_collections_count", "blight_first_ticket_date",
            "blight_latest_ticket_date", "blight_latest_update_at", "blight_top_violations",
            "blight_neighborhood",
        ]
        fields = [*reader.fieldnames, *extra]
        with full.open("w", newline="", encoding="utf-8") as target:
            writer = csv.DictWriter(target, fieldnames=fields)
            writer.writeheader()
            for row in reader:
                if clean(row.get("municipality")) != "Detroit":
                    continue
                key = parcel_key(row.get("parcel_id"))
                item = aggregated.get(key)
                if not item:
                    continue
                matched_source_keys.add(key)
                owner = clean(row.get("owner_name"))
                if PUBLIC_OWNER.search(owner):
                    public_owner_rows += 1
                    continue
                violations = item["ordinances"]
                assert isinstance(violations, Counter)
                row.update(
                    {
                        "lc_lane": lane,
                        "blight_ticket_count": item["ticket_count"],
                        "blight_balance_due": round(float(item["balance_due"]), 2),
                        "blight_judgment_amount": round(float(item["judgment_amount"]), 2),
                        "blight_payment_amount": round(float(item["payment_amount"]), 2),
                        "blight_in_collections_count": item["in_collections_count"],
                        "blight_first_ticket_date": item["first_ticket_date"],
                        "blight_latest_ticket_date": item["latest_ticket_date"],
                        "blight_latest_update_at": item["latest_update_at"],
                        "blight_top_violations": "; ".join(
                            f"{label} ({count})" for label, count in violations.most_common(3)
                        ),
                        "blight_neighborhood": item["neighborhood"],
                    }
                )
                writer.writerow(row)
                records += 1
                matched_keys.add(key)
                balances.append(float(item["balance_due"]))
                ticket_counts.append(int(item["ticket_count"]))
                collections += int(item["in_collections_count"]) > 0
                neighborhoods[clean(item["neighborhood"]) or "Unknown"] += 1
                if len(preview_rows) < preview_count:
                    preview_rows.append(redact(row))
    with preview.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(preview_rows)
    payload = {
        "market": "detroit-mi",
        "lane": lane,
        "status": "verified",
        "source_url": SOURCE_URL,
        "source_file": str(blight),
        "source_last_edit_at": "2026-07-16T19:05:50.222Z",
        "source_status": "Daily City of Detroit blight-ticket data filtered to responsible dispositions with a positive balance due and a parcel ID",
        "source_where": "amt_balance_due > 0 AND disposition LIKE 'Responsible%' AND parcel_id IS NOT NULL",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "source_ticket_rows": ticket_rows,
        "source_unique_parcels": len(aggregated),
        "records": records,
        "public_owner_parcels_excluded": public_owner_rows,
        "unmatched_source_parcels": len(set(aggregated) - matched_source_keys),
        "total_balance_due": round(sum(balances), 2),
        "median_balance_due": round(statistics.median(balances), 2) if balances else None,
        "median_ticket_count": round(statistics.median(ticket_counts), 1) if ticket_counts else None,
        "parcels_with_collection_status": collections,
        "top_neighborhoods": neighborhoods.most_common(15),
        "outputs": {"full": str(full), "preview": str(preview), "meta": str(meta)},
        "verification": {
            "full_csv_rows": records,
            "unique_parcels_in_full_csv": len(matched_keys),
            "duplicate_parcels_in_full_csv": records - len(matched_keys),
            "positive_balances_only": bool(balances) and min(balances) > 0,
        },
    }
    meta.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--blight", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--preview", type=int, default=25)
    args = parser.parse_args()
    result = process(args.canonical, args.blight, args.output_dir, args.preview)
    print(json.dumps(result, indent=2))
    return 0 if result["verification"]["duplicate_parcels_in_full_csv"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
