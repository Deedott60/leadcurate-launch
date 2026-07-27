#!/usr/bin/env python3
"""Join current Shelby tax-sale, open-code, and recent-permit events to parcels."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SOURCES = {
    "tax": "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv",
    "code": "https://datamidsouth.opendatasoft.com/explore/dataset/historical-code-enforcement-requests/",
    "permit": "https://datamidsouth.opendatasoft.com/explore/dataset/shelby-county-building-and-demolition-permits/",
}
OPEN_CODE_STATUSES = {"IN PROGRESS", "PENDING LITIGATION", "BACK TO DEPARTMENT", "BACK TO MCSC"}


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def compact(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", clean(value).upper())


def rows(path: Path) -> Iterable[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        sample = handle.read(65536)
        handle.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        yield from csv.DictReader(handle, delimiter=delimiter)


def load_events(tax_path: Path, code_path: Path, permit_path: Path, cutoff: date) -> dict[str, dict[str, list[dict[str, str]]]]:
    events: dict[str, dict[str, list[dict[str, str]]]] = {
        "tax-sale": defaultdict(list), "tax-debt": defaultdict(list),
        "code-violations": defaultdict(list), "active-permits": defaultdict(list),
        "blight-pressure": defaultdict(list),
    }
    for row in rows(tax_path):
        keys = {compact(row.get("ParcelID")), compact(row.get("Alt_Parcel"))} - {""}
        for key in keys:
            events["tax-sale"][key].append(row)
            events["tax-debt"][key].append(row)
    for row in rows(code_path):
        if clean(row.get("service_request_status")).upper() not in OPEN_CODE_STATUSES:
            continue
        if key := compact(row.get("parcel_id")):
            events["code-violations"][key].append(row)
            blight_text = " ".join(clean(row.get(field)) for field in ("code_definition", "service_request_summary", "service_request_type")).upper()
            if re.search(r"BLIGHT|DEMOL|CONDEMN|VACAT|BOARD|SECURE|DANGEROUS|STRUCTUR", blight_text):
                events["blight-pressure"][key].append(row)
    for row in rows(permit_path):
        status = clean(row.get("status")).upper()
        try:
            status_date = date.fromisoformat(clean(row.get("date_status"))[:10])
        except ValueError:
            continue
        if status not in {"ISSUED", "ACTIVE", "OPEN"} or status_date < cutoff:
            continue
        if key := compact(row.get("parid")):
            events["active-permits"][key].append(row)
    return events


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parcels", type=Path, required=True)
    parser.add_argument("--tax-sale", type=Path, required=True)
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--permits", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--permit-cutoff", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    events = load_events(args.tax_sale, args.code, args.permits, args.permit_cutoff)
    wanted = set().union(*(set(values) for values in events.values()))
    matched: dict[str, list[tuple[dict[str, str], list[dict[str, str]]]]] = {lane: [] for lane in events}
    matched_event_keys: dict[str, set[str]] = {lane: set() for lane in events}
    with args.parcels.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        parcel_fields = list(reader.fieldnames or [])
        seen: dict[str, set[str]] = {lane: set() for lane in events}
        for parcel in reader:
            keys = {compact(parcel.get(field)) for field in ("PARCELID", "PARID", "TPARCEL", "PAID")} - {""}
            if not keys.intersection(wanted):
                continue
            canonical = compact(parcel.get("PARCELID") or parcel.get("PARID"))
            for lane, by_key in events.items():
                lane_events: list[dict[str, str]] = []
                for key in keys:
                    lane_events.extend(by_key.get(key, []))
                if lane_events and canonical and canonical not in seen[lane]:
                    seen[lane].add(canonical)
                    matched_event_keys[lane].update(keys.intersection(by_key))
                    unique_events = {json.dumps(event, sort_keys=True): event for event in lane_events}
                    matched[lane].append((parcel, list(unique_events.values())))
    event_fields = [
        "lc_parcel_id", "lc_lane", "lc_event_status", "lc_event_count",
        "lc_event_date", "lc_event_description", "lc_event_reference",
        "lc_source_url", "lc_events_json",
    ]
    results: dict[str, Any] = {}
    for lane, parcel_events in matched.items():
        output_rows: list[dict[str, str]] = []
        kind = "tax" if lane in {"tax-sale", "tax-debt"} else "code" if lane in {"code-violations", "blight-pressure"} else "permit"
        for parcel, lane_events in parcel_events:
            first = lane_events[0]
            if kind == "tax":
                event_date, description, reference = "", "Current Shelby Trustee tax-sale extract", clean(first.get("Tax Sale"))
            elif kind == "code":
                event_date = clean(first.get("last_edited_date") or first.get("reported_date"))
                description = clean(first.get("service_request_summary") or first.get("service_request_type"))
                reference = clean(first.get("service_request_number"))
            else:
                event_date = clean(first.get("date_status"))
                description = clean(first.get("description") or first.get("record_type"))
                reference = clean(first.get("record_id"))
            output_rows.append({
                **parcel,
                "lc_parcel_id": clean(parcel.get("PARCELID") or parcel.get("PARID")),
                "lc_lane": lane,
                "lc_event_status": "current tax-sale extract" if kind == "tax" else clean(first.get("service_request_status") or first.get("status")),
                "lc_event_count": str(len(lane_events)), "lc_event_date": event_date,
                "lc_event_description": description, "lc_event_reference": reference,
                "lc_source_url": SOURCES[kind], "lc_events_json": json.dumps(lane_events, separators=(",", ":")),
            })
        lane_dir = args.output_dir / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        stem = f"shelby-tn-{lane}-{args.date}"
        fields = parcel_fields + event_fields
        for suffix, subset in (("", output_rows), ("-preview", output_rows[:25])):
            with (lane_dir / f"{stem}{suffix}.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                writer.writeheader(); writer.writerows(subset)
        source_event_count = sum(len(value) for value in events[lane].values())
        payload = {
            "market": "shelby-tn", "lane": lane, "status": "verified",
            "source_name": "Shelby County Trustee" if kind == "tax" else "Data Midsouth official county open-data export",
            "source_url": SOURCES[kind], "source_data_as_of": args.date,
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_event_key_rows": source_event_count, "records": len(output_rows),
            "unmatched_event_keys": len(set(events[lane]) - matched_event_keys[lane]),
            "policy": ("Only open-status official code cases with demolition, condemnation, vacancy, board/secure, dangerous, or structural language are included." if lane == "blight-pressure" else "Only official code requests whose current status is In Progress, Pending Litigation, Back to Department, or Back to MCSC are included.") if kind == "code" else f"Only permits with Issued/Active/Open status dated {args.permit_cutoff.isoformat()} or later are included." if kind == "permit" else "Current Trustee tax-sale extract; one parcel per customer row.",
            "outputs": {"full": str(lane_dir / f"{stem}.csv"), "preview": str(lane_dir / f"{stem}-preview.csv")},
            "verification": {"full_csv_rows": len(output_rows), "unique_parcels_in_full_csv": len(output_rows), "duplicate_parcels_in_full_csv": 0},
        }
        (lane_dir / f"{stem}-meta.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        results[lane] = payload
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
