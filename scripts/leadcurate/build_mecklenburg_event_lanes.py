#!/usr/bin/env python3
"""Build current Mecklenburg code and blight lanes from official ArcGIS cases."""
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


CODE_URL = "https://gis.charlottenc.gov/arcgis/rest/services/HNS/CodeEnforcementCasesAll/MapServer/0"
DEMO_URL = "https://gis.charlottenc.gov/arcgis/rest/services/HNS/CodeEnforcementOrderstoDemolish/MapServer/0"
BLIGHT_PATTERN = re.compile(r"BLIGHT|VACAN|ABANDON|DANGEROUS|DEMOL|BOARD|UNSAFE|STRUCTUR|FIRE DAMAGE", re.I)


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def key(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", clean(value).upper())


def post_json(url: str, values: dict[str, Any]) -> dict[str, Any]:
    body = parse.urlencode(values).encode()
    req = request.Request(url, data=body, headers={"User-Agent": "LeadCurate/1.0 official-source pull"})
    with request.urlopen(req, timeout=180) as response:
        payload = json.load(response)
    if "error" in payload:
        raise RuntimeError(payload["error"])
    return payload


def fetch(url: str, where: str) -> list[dict[str, Any]]:
    query = f"{url}/query"
    ids = post_json(query, {"where": where, "returnIdsOnly": "true", "f": "json"}).get("objectIds", [])
    rows: list[dict[str, Any]] = []
    for offset in range(0, len(ids), 1000):
        payload = post_json(query, {
            "objectIds": ",".join(map(str, ids[offset:offset + 1000])),
            "outFields": "*", "returnGeometry": "false", "f": "json",
        })
        rows.extend(feature["attributes"] for feature in payload.get("features", []))
    if len(rows) != len(ids):
        raise RuntimeError(f"{url}: returned {len(rows)} rows for {len(ids)} object IDs")
    return rows


def event_date(value: Any) -> str:
    try:
        return datetime.fromtimestamp(int(value) / 1000, timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return clean(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parcels", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    cases = fetch(CODE_URL, "CaseStatus IN ('Open','New')")
    demolitions = fetch(DEMO_URL, "1=1")
    args.raw_dir.mkdir(parents=True, exist_ok=True)
    (args.raw_dir / "charlotte-open-new-code-cases.json").write_text(json.dumps(cases), encoding="utf-8")
    (args.raw_dir / "charlotte-demolition-orders.json").write_text(json.dumps(demolitions), encoding="utf-8")

    lane_events: dict[str, dict[str, list[dict[str, Any]]]] = {
        "code-violations": defaultdict(list), "blight-pressure": defaultdict(list)
    }
    for event in cases:
        parcel = key(event.get("ParcelId"))
        if not parcel:
            continue
        lane_events["code-violations"][parcel].append(event)
        text = " ".join(clean(event.get(field)) for field in ("CaseType", "DetailedDescription", "Conclusion"))
        if BLIGHT_PATTERN.search(text):
            lane_events["blight-pressure"][parcel].append(event)
    for event in demolitions:
        if parcel := key(event.get("ParcelId")):
            lane_events["blight-pressure"][parcel].append({**event, "lc_demolition_order": True})

    wanted = set(lane_events["code-violations"]) | set(lane_events["blight-pressure"])
    parcels: dict[str, dict[str, str]] = {}
    with args.parcels.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        parcel_fields = list(reader.fieldnames or [])
        for row in reader:
            keys = {key(row.get(field)) for field in ("PID", "Common_PID", "Tax_ID")} - {""}
            for parcel_key in keys & wanted:
                parcels.setdefault(parcel_key, row)

    event_fields = [
        "lc_parcel_id", "lc_lane", "lc_event_status", "lc_event_count", "lc_event_date",
        "lc_event_description", "lc_event_reference", "lc_source_url", "lc_events_json",
    ]
    results: dict[str, Any] = {}
    for lane, by_parcel in lane_events.items():
        output_rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for event_key, events in by_parcel.items():
            parcel = parcels.get(event_key)
            canonical = key((parcel or {}).get("PID") or (parcel or {}).get("Common_PID"))
            if not parcel or not canonical or canonical in seen:
                continue
            seen.add(canonical)
            first = events[0]
            output_rows.append({
                **parcel, "lc_parcel_id": canonical, "lc_lane": lane,
                "lc_event_status": clean(first.get("CaseStatus")), "lc_event_count": str(len(events)),
                "lc_event_date": event_date(first.get("DateCreated")),
                "lc_event_description": clean(first.get("DetailedDescription") or first.get("CaseType")),
                "lc_event_reference": clean(first.get("CaseNumber")),
                "lc_source_url": DEMO_URL if first.get("lc_demolition_order") else CODE_URL,
                "lc_events_json": json.dumps(events, separators=(",", ":")),
            })
        lane_dir = args.output_dir / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        stem = f"mecklenburg-nc-{lane}-{args.date}"
        fields = parcel_fields + event_fields
        for suffix, subset in (("", output_rows), ("-preview", output_rows[:25])):
            with (lane_dir / f"{stem}{suffix}.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
                writer.writeheader(); writer.writerows(subset)
        payload = {
            "market": "mecklenburg-nc", "lane": lane, "status": "verified",
            "source_name": "Charlotte Code Enforcement Cases All" + (" plus Orders to Demolish" if lane == "blight-pressure" else ""),
            "source_url": CODE_URL, "secondary_source_url": DEMO_URL if lane == "blight-pressure" else None,
            "source_data_as_of": args.date, "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_events": sum(len(events) for events in by_parcel.values()), "records": len(output_rows),
            "policy": "Only current Open or New cases." if lane == "code-violations" else "Current Open/New cases with explicit blight evidence, plus official demolition orders.",
            "verification": {"full_csv_rows": len(output_rows), "unique_parcels_in_full_csv": len(output_rows), "duplicate_parcels_in_full_csv": 0},
            "outputs": {"full": str(lane_dir / f"{stem}.csv"), "preview": str(lane_dir / f"{stem}-preview.csv")},
        }
        (lane_dir / f"{stem}-meta.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        results[lane] = payload
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
