#!/usr/bin/env python3
"""Pull current official City of Detroit parcel and blight datasets.

Manual-invoke only. ArcGIS queries are paginated at the service's advertised
record limit and each output receives file-matched source metadata.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


ROOT = "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services"
DATASETS: dict[str, dict[str, str]] = {
    "parcels": {
        "layer": f"{ROOT}/parcel_file_current/FeatureServer/0",
        "where": "1=1",
        "fields": "*",
        "file": "detroit-current-parcels.csv",
    },
    "assessment": {
        "layer": f"{ROOT}/tentative_assessment_roll_2026/FeatureServer/0",
        "where": "1=1",
        "fields": "*",
        "file": "detroit-2026-tentative-assessment.csv",
    },
    "blight": {
        "layer": f"{ROOT}/blight_tickets/FeatureServer/0",
        "where": "amt_balance_due > 0 AND disposition LIKE 'Responsible%' AND parcel_id IS NOT NULL",
        "fields": (
            "OBJECTID,ticket_id,ticket_number,address,ordinance_law,ordinance_description,"
            "disposition,ticket_issued_date,judgment_date,ticket_updated_at,amt_judgment,"
            "amt_payment,amt_balance_due,payment_status,collection_status,property_owner_name,"
            "property_owner_address,property_owner_city,property_owner_state,property_owner_zip_code,"
            "neighborhood,council_district,zip_code,parcel_id"
        ),
        "file": "detroit-current-unpaid-responsible-blight.csv",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def request_json(session: requests.Session, method: str, url: str, **kwargs: Any) -> dict[str, Any]:
    last: Exception | None = None
    for attempt in range(6):
        try:
            response = session.request(method, url, timeout=120, **kwargs)
            response.raise_for_status()
            payload = response.json()
            if payload.get("error"):
                raise RuntimeError(json.dumps(payload["error"]))
            return payload
        except (requests.RequestException, ValueError, RuntimeError) as exc:
            last = exc
            time.sleep(min(30, 2 ** attempt))
    raise RuntimeError(f"ArcGIS request failed after retries: {last}")


def epoch_iso(value: object) -> str | None:
    try:
        return datetime.fromtimestamp(float(value) / 1000, tz=timezone.utc).isoformat()
    except (TypeError, ValueError, OSError):
        return None


def pull(name: str, output_dir: Path) -> dict[str, object]:
    spec = DATASETS[name]
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / spec["file"]
    session = requests.Session()
    session.headers.update({"User-Agent": "LeadCurate official-source pull/1.0"})
    layer = request_json(session, "GET", spec["layer"], params={"f": "json"})
    object_id = layer.get("objectIdField") or layer.get("objectIdFieldName")
    if not object_id:
        object_id = next(
            field["name"] for field in layer["fields"] if field["type"] == "esriFieldTypeOID"
        )
    max_records = int(layer.get("maxRecordCount") or 1000)
    requested = [item.strip() for item in spec["fields"].split(",")]
    fields = [field["name"] for field in layer["fields"]] if requested == ["*"] else requested
    date_fields = {
        field["name"] for field in layer["fields"] if field["type"] == "esriFieldTypeDate"
    }
    count_payload = request_json(
        session,
        "POST",
        f"{spec['layer']}/query",
        data={"where": spec["where"], "returnCountOnly": "true", "f": "json"},
    )
    expected = int(count_payload["count"])
    rows = 0
    seen_ids: set[str] = set()
    offset = 0
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        while offset < expected:
            payload = request_json(
                session,
                "POST",
                f"{spec['layer']}/query",
                data={
                    "where": spec["where"],
                    "outFields": ",".join(fields),
                    "returnGeometry": "false",
                    "orderByFields": f"{object_id} ASC",
                    "resultOffset": offset,
                    "resultRecordCount": max_records,
                    "f": "json",
                },
            )
            features = payload.get("features", [])
            if not features:
                break
            for feature in features:
                row = feature["attributes"]
                oid = str(row.get(object_id) or "")
                if oid in seen_ids:
                    continue
                seen_ids.add(oid)
                for field in date_fields & row.keys():
                    if row[field] is not None:
                        row[field] = epoch_iso(row[field])
                writer.writerow(row)
                rows += 1
            offset += len(features)
    metadata = {
        "dataset": name,
        "source_url": spec["layer"],
        "source_where": spec["where"],
        "source_description": layer.get("description"),
        "source_last_edit_at": epoch_iso((layer.get("editingInfo") or {}).get("lastEditDate")),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "expected_records": expected,
        "records": rows,
        "unique_object_ids": len(seen_ids),
        "duplicate_object_ids": rows - len(seen_ids),
        "field_count": len(fields),
        "file": str(output),
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "verification": {
            "count_matches_source": rows == expected,
            "zero_duplicate_object_ids": rows == len(seen_ids),
        },
    }
    output.with_name(output.stem + "-meta.json").write_text(
        json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["all", *DATASETS], default="all")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    names = list(DATASETS) if args.dataset == "all" else [args.dataset]
    results = [pull(name, args.output_dir) for name in names]
    print(json.dumps(results, indent=2))
    return 0 if all(item["verification"]["count_matches_source"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
