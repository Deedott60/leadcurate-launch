#!/usr/bin/env python3
"""Pull the authoritative Fulton and Shelby catalog/event source files.

The two markets were previously represented by one lane each.  This pull is
deliberately bulk and restart-safe: ArcGIS object ids are fetched first, rows
are downloaded in stable chunks, and the final CSV is atomically promoted only
after its row/parcel uniqueness gates pass.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import ssl
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib import parse, request


RAW_ROOT = Path("/opt/leadcurate/raw_imports")
TODAY = date.today().isoformat()

FULTON_PARCELS = "https://services1.arcgis.com/AQDHTHDrZzfsFsB5/arcgis/rest/services/Tax_Parcels_2025/FeatureServer/0"
SHELBY_PARCELS = "https://scgis.shelbycountytn.gov/serverhigh/rest/services/Parcel/CERTParcel/MapServer/0"
SHELBY_TAX_SALE = "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv"
SHELBY_DATASETS = {
    "shelby-code-enforcement.csv": "historical-code-enforcement-requests",
    "shelby-building-demolition-permits.csv": "shelby-county-building-and-demolition-permits",
    "shelby-property-transactions.csv": "shelby-county-register-of-deeds-property-transactions",
}
FULTON_TAX_SALE_PDF = "https://fultoncountyga.gov/-/media/Departments/Sheriff/Tax-Sales/2026/Sheriffs-August-4-2026-Levy-Sale-List--1st-Posting.pdf"

SSL_CONTEXT = ssl.create_default_context()
if hasattr(ssl, "OP_LEGACY_SERVER_CONNECT"):
    SSL_CONTEXT.options |= ssl.OP_LEGACY_SERVER_CONNECT


def get_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    encoded = parse.urlencode(params).encode("utf-8")
    req = request.Request(
        url,
        data=encoded,
        method="POST",
        headers={
            "User-Agent": "LeadCurate/1.0 public-record pull",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    with request.urlopen(req, timeout=120, context=SSL_CONTEXT) as response:
        payload = json.load(response)
    if payload.get("error"):
        raise RuntimeError(f"ArcGIS error from {url}: {payload['error']}")
    return payload


def download(url: str, destination: Path) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, pending_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    pending = Path(pending_name)
    try:
        req = request.Request(url, headers={"User-Agent": "LeadCurate/1.0 public-record pull"})
        with request.urlopen(req, timeout=300, context=SSL_CONTEXT) as response, pending.open("wb") as handle:
            while chunk := response.read(1024 * 1024):
                handle.write(chunk)
        if pending.stat().st_size == 0:
            raise RuntimeError(f"empty download from {url}")
        pending.replace(destination)
    finally:
        pending.unlink(missing_ok=True)
    return {"url": url, "file": str(destination), "bytes": destination.stat().st_size}


def arcgis_csv(layer: str, destination: Path, key_field: str, chunk_size: int = 1000) -> dict[str, Any]:
    ids_payload = get_json(f"{layer}/query", {"where": "1=1", "returnIdsOnly": "true", "f": "json"})
    object_field = ids_payload.get("objectIdFieldName") or "OBJECTID"
    object_ids = sorted({int(value) for value in ids_payload.get("objectIds") or []})
    if not object_ids:
        raise RuntimeError(f"no object ids returned by {layer}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, pending_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    os.close(fd)
    pending = Path(pending_name)
    fieldnames: list[str] | None = None
    writer: csv.DictWriter | None = None
    seen: set[str] = set()
    returned_object_ids: set[int] = set()
    rows = 0
    try:
        with pending.open("w", newline="", encoding="utf-8") as handle:
            for start in range(0, len(object_ids), chunk_size):
                chunk = object_ids[start : start + chunk_size]
                payload = get_json(
                    f"{layer}/query",
                    {
                        "objectIds": ",".join(map(str, chunk)),
                        "outFields": "*",
                        "returnGeometry": "false",
                        "orderByFields": f"{object_field} ASC",
                        "f": "json",
                    },
                )
                features = payload.get("features") or []
                if fieldnames is None:
                    fieldnames = [field["name"] for field in payload.get("fields") or []]
                    if not fieldnames and features:
                        fieldnames = list(features[0].get("attributes") or {})
                    if not fieldnames or key_field not in fieldnames:
                        raise RuntimeError(f"{key_field} missing from {layer}")
                    writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
                    writer.writeheader()
                for feature in features:
                    row = feature.get("attributes") or {}
                    if row.get(object_field) is not None:
                        returned_object_ids.add(int(row[object_field]))
                    key = " ".join(str(row.get(key_field) or "").upper().split())
                    if not key or key in seen:
                        continue
                    seen.add(key)
                    writer.writerow(row)
                    rows += 1
        if returned_object_ids != set(object_ids):
            missing = len(set(object_ids) - returned_object_ids)
            raise RuntimeError(f"{layer}: {missing} object ids were not returned")
        pending.replace(destination)
    finally:
        pending.unlink(missing_ok=True)
    return {
        "url": layer,
        "file": str(destination),
        "object_id_field": object_field,
        "source_object_ids": len(object_ids),
        "returned_object_ids": len(returned_object_ids),
        "rows": rows,
        "duplicate_or_blank_keys_removed": len(object_ids) - rows,
        "unique_keys": len(seen),
        "key_field": key_field,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=TODAY)
    parser.add_argument("--market", action="append", choices=("fulton", "shelby"))
    args = parser.parse_args()
    fulton = RAW_ROOT / "fulton-ga" / args.date
    shelby = RAW_ROOT / "shelby-tn" / args.date
    markets = set(args.market or ("fulton", "shelby"))
    results: dict[str, Any] = {"generated_at_utc": datetime.now(timezone.utc).isoformat()}
    if "fulton" in markets:
        results["fulton_parcels"] = arcgis_csv(FULTON_PARCELS, fulton / "fulton-county-tax-parcels-2025.csv", "ParcelID")
        results["fulton_tax_sale"] = download(FULTON_TAX_SALE_PDF, fulton / "fulton-sheriff-2026-08-04-levy-sale.pdf")
    if "shelby" in markets:
        results["shelby_parcels"] = arcgis_csv(SHELBY_PARCELS, shelby / "shelby-county-parcels-current.csv", "PARCELID")
        results["shelby_tax_sale"] = download(SHELBY_TAX_SALE, shelby / "tax-sale-extract.csv")
        results["shelby_events"] = {}
        for filename, dataset in SHELBY_DATASETS.items():
            url = f"https://datamidsouth.opendatasoft.com/api/explore/v2.1/catalog/datasets/{dataset}/exports/csv"
            results["shelby_events"][dataset] = download(url, shelby / filename)
    for directory in (fulton, shelby):
        (directory / "priority-catalog-pull-meta.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
