#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import html
import re
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib import parse, request

RAW_ROOT = Path("/opt/leadcurate/raw_imports")
SOURCE = RAW_ROOT / "jefferson-ky" / "property-maintenance-violations.csv"
PVA_SEARCH = "https://jeffersonpva.ky.gov/property-search/property-listings/"

OUTPUT_FIELDS = [
    "owner_name",
    "parcel_id",
    "address",
    "Property ZIP",
    "value",
    "total_owed",
    "Violation Status",
    "Occupancy Status",
    "Violation Date",
    "Case ID",
    "source_url",
]


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def strip_tags(text: str) -> str:
    return clean(html.unescape(re.sub(r"<[^>]+>", " ", text)))


def parse_details(page: str) -> dict[str, str]:
    result: dict[str, str] = {}
    title = re.search(r"<h1[^>]*>(.*?)</h1>", page, flags=re.I | re.S)
    if title:
        result["address"] = strip_tags(title.group(1))
    for label, value in re.findall(r"<dt[^>]*>(.*?)</dt>\s*<dd[^>]*class=\"result\"[^>]*>(.*?)</dd>", page, flags=re.I | re.S):
        result[strip_tags(label).lower()] = strip_tags(value)
    return result


def fetch_pva(parcel_id: str, timeout: int = 30) -> dict[str, str]:
    params = parse.urlencode({"psfldParcelId": parcel_id, "searchType": "ParcelSearch"})
    req = request.Request(
        f"{PVA_SEARCH}?{params}",
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; LeadCurate/1.0)",
            "Referer": "https://jeffersonpva.ky.gov/property-search/",
        },
    )
    with request.urlopen(req, timeout=timeout) as res:
        page = res.read().decode("utf-8", "replace")
    return parse_details(page)


def latest_input() -> Path:
    if SOURCE.exists():
        return SOURCE
    candidates = sorted((RAW_ROOT / "jefferson-ky").glob("*/property-maintenance-violations.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    raise FileNotFoundError("property-maintenance-violations.csv not found")


def enrich(limit: int, sleep_seconds: float) -> dict[str, Any]:
    src = latest_input()
    rows = list(csv.DictReader(src.open(newline="", encoding="utf-8-sig", errors="replace")))
    out_rows: list[dict[str, str]] = []
    cache: dict[str, dict[str, str]] = {}
    for raw in rows:
        if len(out_rows) >= limit:
            break
        parcel = clean(raw.get("PARCEL_ID"))
        if not parcel:
            continue
        if parcel not in cache:
            try:
                cache[parcel] = fetch_pva(parcel)
            except Exception as exc:
                cache[parcel] = {"error": str(exc)}
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
        details = cache[parcel]
        owner = clean(details.get("owner"))
        value = clean(details.get("assessed value"))
        address = clean(details.get("address") or raw.get("FullAddress") or raw.get("PartialAddress"))
        if not owner or not value:
            continue
        out_rows.append(
            {
                "owner_name": owner,
                "parcel_id": parcel,
                "address": address,
                "Property ZIP": clean(raw.get("FullAddress")).rsplit(" ", 1)[-1].split("-")[0] if clean(raw.get("FullAddress")) else "",
                "value": value,
                "total_owed": clean(raw.get("CitationAmount")),
                "Violation Status": clean(raw.get("G6A_G6_STATUS")),
                "Occupancy Status": clean(raw.get("OccupancyStatus")),
                "Violation Date": clean(raw.get("G6A_G6_STATUS_DD")),
                "Case ID": clean(raw.get("B1_ALT_ID")),
                "source_url": "https://jeffersonpva.ky.gov/property-search/",
            }
        )
    out_dir = RAW_ROOT / "jefferson-ky" / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "property-maintenance-violations-enriched.csv"
    with out_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)
    return {"ok": True, "source": str(src), "rows_read": len(rows), "unique_pva_lookups": len(cache), "rows": len(out_rows), "csv": str(out_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=250)
    parser.add_argument("--sleep", type=float, default=0.15)
    args = parser.parse_args()
    import json

    print(json.dumps(enrich(args.limit, args.sleep), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
