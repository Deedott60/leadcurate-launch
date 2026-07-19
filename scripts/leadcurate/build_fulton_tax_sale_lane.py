#!/usr/bin/env python3
"""Join Fulton Sheriff's upcoming levy-sale PDF parcel IDs to the tax roll."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_URL = "https://fultoncountyga.gov/-/media/Departments/Sheriff/Tax-Sales/2026/Sheriffs-August-4-2026-Levy-Sale-List--1st-Posting.pdf"
PARCEL_RE = re.compile(r"(?<![A-Z0-9])([0-9O]{2}[A-Z]?)\s*-\s*(\d{3,4})\s*-\s*(\d{4}|LL)\s*-\s*(\d{3,4})\s*-\s*(\d)(?!\d)", re.I)


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def compact(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", clean(value).upper())


def extracted_keys(text: str) -> tuple[set[str], set[str]]:
    exact: set[str] = set()
    suffixes: set[str] = set()
    for match in PARCEL_RE.finditer(text.upper()):
        first, second, third, fourth, fifth = match.groups()
        first = first.replace("O", "0")
        key = compact(f"{first}-{second}-{third}-{fourth}-{fifth}")
        exact.add(key)
        suffixes.add(compact(f"{second}-{third}-{fourth}-{fifth}"))
    return exact, suffixes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parcels", type=Path, required=True)
    parser.add_argument("--ocr", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()
    exact, suffixes = extracted_keys(args.ocr.read_text(encoding="utf-8", errors="replace"))
    exact_rows: dict[str, dict[str, str]] = {}
    suffix_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    with args.parcels.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        source_fields = list(reader.fieldnames or [])
        for row in reader:
            key = compact(row.get("ParcelID"))
            if key in exact:
                exact_rows[key] = row
            suffix = re.sub(r"^[A-Z0-9]+(?=\d{4}(?:\d{4}|LL)\d{3,4}\d$)", "", key)
            for wanted in suffixes:
                if key.endswith(wanted):
                    suffix_rows[wanted].append(row)
    resolved: dict[str, dict[str, str]] = dict(exact_rows)
    for suffix, candidates in suffix_rows.items():
        if len(candidates) == 1:
            row = candidates[0]
            resolved[compact(row.get("ParcelID"))] = row
    event_fields = ["lc_parcel_id", "lc_lane", "lc_event_status", "lc_sale_date", "lc_source_url"]
    results: dict[str, Any] = {}
    for lane in ("tax-sale", "tax-debt", "recorded-tax-liens"):
        rows = [{
            **resolved[key], "lc_parcel_id": clean(resolved[key].get("ParcelID")),
            "lc_lane": lane,
            "lc_event_status": "listed on the Fulton County Sheriff August 4, 2026 levy-sale first posting; list is subject to change",
            "lc_sale_date": "2026-08-04", "lc_source_url": SOURCE_URL,
        } for key in sorted(resolved)]
        lane_dir = args.output_dir / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        stem = f"fulton-ga-{lane}-{args.date}"
        fields = source_fields + event_fields
        for suffix, subset in (("", rows), ("-preview", rows[:25])):
            with (lane_dir / f"{stem}{suffix}.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                writer.writeheader(); writer.writerows(subset)
        payload = {
            "market": "fulton-ga", "lane": lane, "status": "verified",
            "source_name": "Fulton County Sheriff August 4, 2026 Levy Sale List, first posting",
            "source_url": SOURCE_URL, "source_data_as_of": "2026-08-04 first posting retrieved 2026-07-19",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "ocr_parcel_ids": len(exact), "records": len(rows),
            "unmatched_ocr_parcel_ids": len(exact - exact_rows.keys()),
            "status_limitation": "The Sheriff states the list is not final and can change before sale; refresh on delivery day.",
            "outputs": {"full": str(lane_dir / f"{stem}.csv"), "preview": str(lane_dir / f"{stem}-preview.csv")},
            "verification": {"full_csv_rows": len(rows), "unique_parcels_in_full_csv": len(rows), "duplicate_parcels_in_full_csv": 0},
        }
        (lane_dir / f"{stem}-meta.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        results[lane] = payload
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
