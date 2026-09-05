#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import zipfile
from datetime import date
from pathlib import Path

RAW_ROOT = Path("/opt/leadcurate/raw_imports")


def clean(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def residential_rows(zip_path: Path, limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path) as zf, zf.open("Data/Residential_Master.txt") as handle:
        for raw in handle:
            parts = raw.decode("utf-8", errors="replace").rstrip("\r\n").split("|")
            if len(parts) < 39:
                continue
            parcel = clean(parts[0])
            owner = clean(parts[24])
            mailing = clean(parts[25])
            city = clean(parts[27])
            state = clean(parts[28])
            zip_code = clean(parts[29])
            situs = " ".join(clean(parts[i]) for i in [31, 32, 33, 34, 35, 36] if clean(parts[i]))
            value = clean(parts[19] or parts[18] or "0")
            if not parcel or not owner or not situs:
                continue
            rows.append({
                "parcel_id": parcel,
                "owner_name": owner,
                "address": situs,
                "city": clean(parts[37]) or city or "Phoenix",
                "Property ZIP": clean(parts[38]) or zip_code,
                "Mailing Street": mailing,
                "Mailing City": city,
                "Mailing State": state,
                "Mailing ZIP": zip_code,
                "value": value,
                "Building Value": value,
                "Land Value": "0",
                "source_url": str(zip_path),
            })
            if len(rows) >= limit:
                break
    return rows


def secured_rows(zip_path: Path, limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if not name.startswith("Data/Secured_Master"):
                continue
            with zf.open(name) as handle:
                for raw in handle:
                    parts = raw.decode("utf-8", errors="replace").rstrip("\r\n").split("|")
                    if len(parts) < 20:
                        continue
                    parcel = clean(parts[0])
                    owner = clean(parts[1])
                    mail = clean(parts[2])
                    city = clean(parts[4])
                    state = clean(parts[5])
                    zip_code = clean(parts[6])
                    prop_type = clean(parts[12])
                    value = clean(parts[16] or parts[15] or "0")
                    if not parcel or not owner or not mail:
                        continue
                    rows.append({
                        "parcel_id": parcel,
                        "owner_name": owner,
                        "address": mail,
                        "city": city or "Phoenix",
                        "Property ZIP": zip_code,
                        "Mailing Street": mail,
                        "Mailing City": city,
                        "Mailing State": state,
                        "Mailing ZIP": zip_code,
                        "value": value,
                        "Building Value": clean(parts[15]),
                        "Land Value": clean(parts[14]),
                        "property_type": prop_type,
                        "source_url": str(zip_path),
                    })
                    if len(rows) >= limit:
                        return rows
    return rows


def extract(raw_dir: Path, output_dir: Path, limit: int) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    residential = residential_rows(raw_dir / "residential-master.zip", limit)
    secured = secured_rows(raw_dir / "secured-master.zip", limit)
    rows = residential + secured
    out = output_dir / "parcels-extracted.csv"
    fields = ["parcel_id", "owner_name", "address", "city", "Property ZIP", "Mailing Street", "Mailing City", "Mailing State", "Mailing ZIP", "value", "Building Value", "Land Value", "property_type", "source_url"]
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return {"ok": True, "raw_dir": str(raw_dir), "residential_rows": len(residential), "secured_rows": len(secured), "rows": len(rows), "csv": str(out)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default=str(RAW_ROOT / "maricopa-az" / "2026-06-18"))
    parser.add_argument("--output-dir", default=str(RAW_ROOT / "maricopa-az" / date.today().isoformat()))
    parser.add_argument("--limit", type=int, default=10000)
    args = parser.parse_args()
    print(json.dumps(extract(Path(args.raw_dir), Path(args.output_dir), args.limit), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
