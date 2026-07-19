#!/usr/bin/env python3
"""Build current Chicago-subset Cook County permit and code-event lanes."""
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import parse, request


DOMAIN = "data.cityofchicago.org"
PERMIT_ID = "ydr8-5enu"
CODE_ID = "22u3-xenr"
SOURCES = {
    "active-permits": f"https://{DOMAIN}/d/{PERMIT_ID}",
    "code-violations": f"https://{DOMAIN}/d/{CODE_ID}",
    "blight-pressure": f"https://{DOMAIN}/d/{CODE_ID}",
}
SUFFIXES = {"STREET": "ST", "ROAD": "RD", "AVENUE": "AVE", "DRIVE": "DR", "LANE": "LN", "COURT": "CT", "PLACE": "PL", "BOULEVARD": "BLVD", "PARKWAY": "PKWY", "TERRACE": "TER"}
BLIGHT_PATTERN = re.compile(r"BLIGHT|VACAN|ABANDON|DANGEROUS|DEMOL|BOARD|UNSAFE|STRUCTUR|OPEN AND UNGUARDED|FIRE DAMAGE", re.IGNORECASE)


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def normalized_address(value: Any) -> str:
    words = re.sub(r"[^A-Z0-9 ]", " ", clean(value).upper()).split()
    return " ".join(SUFFIXES.get(word, word) for word in words)


def is_blight_event(event: dict[str, Any]) -> bool:
    text = " ".join(clean(event.get(field)) for field in (
        "violation_description", "violation_inspector_comments", "inspection_status"
    ))
    return bool(BLIGHT_PATTERN.search(text))


def fetch(dataset: str, where: str, select: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    offset = 0
    while True:
        query = parse.urlencode({"$select": select, "$where": where, "$limit": 50000, "$offset": offset})
        req = request.Request(f"https://{DOMAIN}/resource/{dataset}.json?{query}", headers={"User-Agent": "LeadCurate/1.0 public-record pull"})
        with request.urlopen(req, timeout=180) as response:
            page = json.load(response)
        result.extend(page)
        if len(page) < 50000:
            return result
        offset += len(page)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--permit-cutoff", required=True)
    args = parser.parse_args()
    permits = fetch(PERMIT_ID, f"permit_status='ACTIVE' AND issue_date >= '{args.permit_cutoff}T00:00:00.000'", "id,permit_,permit_status,permit_milestone,permit_type,issue_date,street_number,street_direction,street_name,work_type,work_description,reported_cost,pin_list")
    violations = fetch(CODE_ID, "violation_status='OPEN'", "id,violation_last_modified_date,violation_date,violation_code,violation_status,violation_status_date,violation_description,violation_inspector_comments,inspection_number,inspection_status,address,street_number,street_direction,street_name,street_type")
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    (args.raw_dir / "chicago-active-building-permits.json").write_text(json.dumps(permits), encoding="utf-8")
    (args.raw_dir / "chicago-open-building-code-violations.json").write_text(json.dumps(violations), encoding="utf-8")
    permits_by_pin: dict[str, list[dict[str, Any]]] = defaultdict(list)
    permits_by_address: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in permits:
        for pin in re.findall(r"\d{10}", clean(event.get("pin_list"))):
            permits_by_pin[pin].append(event)
        address = normalized_address(" ".join(clean(event.get(field)) for field in ("street_number", "street_direction", "street_name")))
        if address:
            permits_by_address[address].append(event)
    violations_by_address: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in violations:
        if address := normalized_address(event.get("address")):
            violations_by_address[address].append(event)
    wanted_pins = set(permits_by_pin)
    wanted_addresses = set(permits_by_address) | set(violations_by_address)
    parcels_by_pin: dict[str, list[dict[str, str]]] = defaultdict(list)
    parcels_by_address: dict[str, list[dict[str, str]]] = defaultdict(list)
    with args.canonical.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        source_fields = list(reader.fieldnames or [])
        for parcel in reader:
            pin10 = clean(parcel.get("U_PIN10"))
            if pin10 in wanted_pins and len(parcels_by_pin[pin10]) < 2:
                parcels_by_pin[pin10].append(parcel)
            if clean(parcel.get("ADDR_PROP_ADDRESS_CITY_NAME")).upper() == "CHICAGO":
                address = normalized_address(parcel.get("ADDR_PROP_ADDRESS_FULL"))
                if address in wanted_addresses and len(parcels_by_address[address]) < 2:
                    parcels_by_address[address].append(parcel)
    matched_maps: dict[str, dict[str, tuple[dict[str, str], list[dict[str, Any]], str]]] = {
        "active-permits": {}, "code-violations": {}, "blight-pressure": {}
    }
    for pin10, events in permits_by_pin.items():
        candidates = parcels_by_pin.get(pin10, [])
        if len(candidates) == 1:
            parcel = candidates[0]
            key = clean(parcel.get("U_PIN"))
            matched_maps["active-permits"][key] = (parcel, list(events), "unique_official_pin10")
    for address, events in permits_by_address.items():
        candidates = parcels_by_address.get(address, [])
        if len(candidates) == 1:
            parcel = candidates[0]
            key = clean(parcel.get("U_PIN"))
            if key in matched_maps["active-permits"]:
                matched_maps["active-permits"][key][1].extend(events)
            else:
                matched_maps["active-permits"][key] = (parcel, list(events), "unique_exact_normalized_address")
    for address, events in violations_by_address.items():
        candidates = parcels_by_address.get(address, [])
        if len(candidates) == 1:
            parcel = candidates[0]
            key = clean(parcel.get("U_PIN"))
            matched_maps["code-violations"][key] = (parcel, list(events), "unique_exact_normalized_address")
            blight_events = [event for event in events if is_blight_event(event)]
            if blight_events:
                matched_maps["blight-pressure"][key] = (parcel, blight_events, "unique_exact_normalized_address")
    matched = {lane: list(values.values()) for lane, values in matched_maps.items()}
    event_fields = ["lc_parcel_id", "lc_lane", "lc_event_status", "lc_event_count", "lc_event_date", "lc_event_description", "lc_event_reference", "lc_match_method", "lc_source_url", "lc_events_json"]
    results: dict[str, Any] = {}
    for lane, records in matched.items():
        output_rows = []
        for parcel, events, method in records:
            first = events[0]
            permit = lane == "active-permits"
            output_rows.append({
                **parcel, "lc_parcel_id": clean(parcel.get("U_PIN")), "lc_lane": lane,
                "lc_event_status": clean(first.get("permit_status") if permit else first.get("violation_status")),
                "lc_event_count": str(len(events)), "lc_event_date": clean(first.get("issue_date") if permit else first.get("violation_date")),
                "lc_event_description": clean(first.get("work_description") if permit else first.get("violation_description")),
                "lc_event_reference": clean(first.get("permit_") if permit else first.get("id")),
                "lc_match_method": method, "lc_source_url": SOURCES[lane],
                "lc_events_json": json.dumps(events, separators=(",", ":")),
            })
        lane_dir = args.output_dir / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        stem = f"cook-il-{lane}-{args.date}"
        fields = source_fields + event_fields
        for suffix, subset in (("", output_rows), ("-preview", output_rows[:25])):
            with (lane_dir / f"{stem}{suffix}.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                writer.writeheader(); writer.writerows(subset)
        payload = {
            "market": "cook-il", "geographic_coverage": "City of Chicago parcels within Cook County", "lane": lane, "status": "verified",
            "source_name": "City of Chicago Building Permits" if lane == "active-permits" else "City of Chicago Building Violations",
            "source_url": SOURCES[lane], "source_data_as_of": args.date, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_events": len(permits) if lane == "active-permits" else sum(1 for event in violations if lane == "code-violations" or is_blight_event(event)),
            "records": len(output_rows),
            "policy": (
                f"Permit status ACTIVE with issue date {args.permit_cutoff} or later."
                if lane == "active-permits" else
                "Only OPEN violations with vacancy, abandonment, dangerous-building, demolition, boarding, unsafe-structure, or fire-damage evidence."
                if lane == "blight-pressure" else
                "Only violations whose current official status is OPEN."
            ),
            "outputs": {"full": str(lane_dir / f"{stem}.csv"), "preview": str(lane_dir / f"{stem}-preview.csv")},
            "verification": {"full_csv_rows": len(output_rows), "unique_parcels_in_full_csv": len(output_rows), "duplicate_parcels_in_full_csv": 0},
        }
        (lane_dir / f"{stem}-meta.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        results[lane] = payload
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
