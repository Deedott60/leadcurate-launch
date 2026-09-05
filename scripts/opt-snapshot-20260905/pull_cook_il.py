#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import sqlite3
import time
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Iterable


TODAY = date.today().isoformat()
SOCRATA = "https://datacatalog.cookcountyil.gov/resource"
RAW_ROOT = Path("/opt/leadcurate/raw_imports/cook-il")

DATASETS = {
    "universe": {
        "id": "pabr-t5kh",
        "prefix": "U_",
        "key": "pin",
        "order": "pin",
        "description": "Assessor - Parcel Universe (Current Year Only)",
    },
    "addresses": {
        "id": "3723-97qp",
        "prefix": "ADDR_",
        "key": "pin",
        "where": "year=2026",
        "order": "pin",
        "description": "Assessor - Parcel Addresses",
    },
    "values": {
        "id": "uzyt-m557",
        "prefix": "VAL_",
        "key": "pin",
        "where": "year=2026",
        "order": "pin",
        "description": "Assessor - Assessed Values",
    },
    "improvements": {
        "id": "x54s-btds",
        "prefix": "IMPR_",
        "key": "pin",
        "where": "year=2026",
        "order": "pin, card",
        "description": "Assessor - Single and Multi-Family Improvement Characteristics",
        "grouped": True,
    },
    "sales": {
        "id": "wvhk-k5uv",
        "prefix": "SALE_",
        "key": "pin",
        "order": "pin, sale_date DESC",
        "description": "Assessor - Parcel Sales (latest row retained per parcel)",
        "first_only": True,
    },
    "commercial": {
        "id": "csik-bsws",
        "prefix": "COMM_",
        "key": "keypin",
        "where": "year=2025",
        "order": "keypin",
        "description": "Assessor - Commercial Valuation Data (latest available year)",
        "first_only": True,
    },
    "parcel_area": {
        "id": "77tz-riq7",
        "prefix": "GEO_",
        "key": "pin10",
        "select": "pin10, area(the_geom) as parcel_area_sq_meters",
        "order": "pin10",
        "description": "Cook County GIS Parcel 2021 geometry area",
        "pin10": True,
    },
}


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def normalize_pin(value: object, length: int = 14) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits.zfill(length) if digits else ""


def source_url(spec: dict[str, object]) -> str:
    params = {"$limit": "5000000"}
    for key in ("where", "order", "select"):
        if spec.get(key):
            params["$" + key] = str(spec[key])
    return f"{SOCRATA}/{spec['id']}.csv?{urllib.parse.urlencode(params)}"


def download(name: str, spec: dict[str, object], output: Path, force: bool) -> dict[str, object]:
    if output.exists() and output.stat().st_size > 100 and not force:
        return {"path": str(output), "bytes": output.stat().st_size, "reused": True, "url": source_url(spec)}
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_suffix(output.suffix + ".part")
    url = source_url(spec)
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "LeadCurate/1.0 data fulfillment"})
            with urllib.request.urlopen(request, timeout=600) as response, gzip.open(temp, "wb", compresslevel=5) as target:
                shutil.copyfileobj(response, target, length=1024 * 1024)
            temp.replace(output)
            return {"path": str(output), "bytes": output.stat().st_size, "reused": False, "url": url}
        except Exception as exc:  # network retries are intentional here
            last_error = exc
            temp.unlink(missing_ok=True)
            if attempt < 3:
                time.sleep(attempt * 5)
    raise RuntimeError(f"Failed to download {name}: {last_error}")


def open_rows(path: Path) -> tuple[list[str], Iterable[dict[str, str]]]:
    handle = gzip.open(path, "rt", newline="", encoding="utf-8-sig", errors="replace")
    reader = csv.DictReader(handle)
    return reader.fieldnames or [], reader


def add_columns(db: sqlite3.Connection, columns: list[str]) -> None:
    existing = {row[1] for row in db.execute("PRAGMA table_info(parcels)")}
    for column in columns:
        if column not in existing:
            db.execute(f"ALTER TABLE parcels ADD COLUMN {q(column)} TEXT")
            existing.add(column)


def upsert_sql(columns: list[str]) -> str:
    names = ["parcel_key", *columns]
    updates = ", ".join(f"{q(column)}=excluded.{q(column)}" for column in columns)
    return (
        f"INSERT INTO parcels ({', '.join(q(name) for name in names)}) "
        f"VALUES ({', '.join('?' for _ in names)}) "
        f"ON CONFLICT(parcel_key) DO UPDATE SET {updates}"
    )


def grouped_improvements(rows: Iterable[dict[str, str]], fields: list[str], key_field: str) -> Iterable[tuple[str, dict[str, str], int]]:
    current = ""
    group: list[dict[str, str]] = []

    def collapse(items: list[dict[str, str]]) -> dict[str, str]:
        result: dict[str, str] = {}
        for field in fields:
            values: list[str] = []
            for item in items:
                value = str(item.get(field) or "").strip()
                if value and value not in values:
                    values.append(value)
            result[field] = " | ".join(values)
        def numeric(field: str) -> list[float]:
            result: list[float] = []
            for item in items:
                try:
                    result.append(float(str(item.get(field) or 0).replace(",", "")))
                except ValueError:
                    continue
            return result
        bldg = numeric("char_bldg_sf")
        land = numeric("char_land_sf")
        years = numeric("char_yrblt")
        apartments = numeric("char_apts")
        result["lc_card_count"] = str(len(items))
        result["lc_total_building_sqft"] = str(sum(bldg)) if bldg else ""
        result["lc_land_sqft"] = str(max(land)) if land else ""
        result["lc_earliest_year_built"] = str(int(min(years))) if years else ""
        result["lc_total_apartments"] = str(sum(apartments)) if apartments else ""
        return result

    for row in rows:
        key = normalize_pin(row.get(key_field))
        if not key:
            continue
        if current and key != current:
            yield current, collapse(group), len(group)
            group = []
        current = key
        group.append(row)
    if current and group:
        yield current, collapse(group), len(group)


def load_dataset(db: sqlite3.Connection, name: str, spec: dict[str, object], path: Path) -> dict[str, int]:
    fields, rows = open_rows(path)
    prefix = str(spec["prefix"])
    extra_fields = ["lc_card_count", "lc_total_building_sqft", "lc_land_sqft", "lc_earliest_year_built", "lc_total_apartments"] if spec.get("grouped") else []
    output_fields = fields + extra_fields
    columns = [prefix + field.upper() for field in output_fields]
    add_columns(db, columns)
    sql = upsert_sql(columns)
    source_rows = 0
    accepted = 0
    duplicates = 0
    batch: list[tuple[str, ...]] = []

    if spec.get("grouped"):
        iterable = grouped_improvements(rows, fields, str(spec["key"]))
        for key, row, group_count in iterable:
            source_rows += group_count
            duplicates += max(0, group_count - 1)
            batch.append((key, *(str(row.get(field) or "") for field in output_fields)))
            accepted += 1
            if len(batch) >= 5000:
                db.executemany(sql, batch)
                db.commit()
                batch.clear()
    elif spec.get("pin10"):
        db.execute("CREATE TEMP TABLE parcel_areas (pin10 TEXT PRIMARY KEY, area TEXT)")
        area_batch: list[tuple[str, str]] = []
        for row in rows:
            source_rows += 1
            key = normalize_pin(row.get(str(spec["key"])), 10)
            if not key:
                continue
            area_batch.append((key, str(row.get(output_fields[1]) or "")))
            if len(area_batch) >= 10000:
                db.executemany("INSERT OR REPLACE INTO parcel_areas VALUES (?, ?)", area_batch)
                area_batch.clear()
        if area_batch:
            db.executemany("INSERT OR REPLACE INTO parcel_areas VALUES (?, ?)", area_batch)
        db.execute(
            f"UPDATE parcels SET {q(columns[1])}=(SELECT area FROM parcel_areas WHERE pin10={q('U_PIN10')}) "
            f"WHERE {q('U_PIN10')} IN (SELECT pin10 FROM parcel_areas)"
        )
        accepted = db.execute("SELECT changes()").fetchone()[0]
        db.execute("DROP TABLE parcel_areas")
        db.commit()
    else:
        seen = ""
        for row in rows:
            source_rows += 1
            key = normalize_pin(row.get(str(spec["key"])), 14)
            if not key:
                continue
            if key == seen:
                duplicates += 1
                if spec.get("first_only"):
                    continue
            seen = key
            batch.append((key, *(str(row.get(field) or "") for field in output_fields)))
            accepted += 1
            if len(batch) >= 5000:
                db.executemany(sql, batch)
                db.commit()
                batch.clear()
    if batch:
        db.executemany(sql, batch)
    db.commit()
    return {"source_rows": source_rows, "accepted_rows": accepted, "duplicate_rows_collapsed": duplicates, "source_fields": len(fields)}


def export_csv(db: sqlite3.Connection, output: Path) -> tuple[int, int]:
    fields = [row[1] for row in db.execute("PRAGMA table_info(parcels)")]
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(fields)
        for row in db.execute("SELECT * FROM parcels ORDER BY parcel_key"):
            writer.writerow(row)
            count += 1
    return count, len(fields)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull and join maximum-field Cook County official parcel datasets.")
    parser.add_argument("--date", default=TODAY)
    parser.add_argument("--force-download", action="store_true")
    args = parser.parse_args()

    raw_dir = RAW_ROOT / args.date
    raw_dir.mkdir(parents=True, exist_ok=True)
    downloads: dict[str, dict[str, object]] = {}
    for name, spec in DATASETS.items():
        downloads[name] = download(name, spec, raw_dir / f"{name}.csv.gz", args.force_download)

    sqlite_path = raw_dir / "cook-parcels-canonical.sqlite"
    sqlite_path.unlink(missing_ok=True)
    for suffix in ("-wal", "-shm"):
        Path(str(sqlite_path) + suffix).unlink(missing_ok=True)
    db = sqlite3.connect(sqlite_path)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA temp_store=FILE")
    db.execute("CREATE TABLE parcels (parcel_key TEXT PRIMARY KEY)")

    loads: dict[str, dict[str, int]] = {}
    for name in ("universe", "addresses", "values", "improvements", "sales", "commercial"):
        loads[name] = load_dataset(db, name, DATASETS[name], Path(downloads[name]["path"]))
        if name == "universe":
            db.execute(f"CREATE INDEX idx_parcels_pin10 ON parcels ({q('U_PIN10')})")
            db.commit()
    orphan_enrichment_rows = int(db.execute("SELECT COUNT(*) FROM parcels WHERE U_PIN IS NULL").fetchone()[0])
    db.execute("DELETE FROM parcels WHERE U_PIN IS NULL")
    db.commit()
    loads["parcel_area"] = load_dataset(db, "parcel_area", DATASETS["parcel_area"], Path(downloads["parcel_area"]["path"]))

    canonical = raw_dir / "cook-parcels-canonical.csv"
    rows, fields = export_csv(db, canonical)
    duplicate_parcels = db.execute("SELECT COUNT(*) - COUNT(DISTINCT parcel_key) FROM parcels").fetchone()[0]
    db.close()
    meta = {
        "market": "cook-il",
        "run_date": args.date,
        "canonical_file": str(canonical),
        "sqlite_file": str(sqlite_path),
        "unique_parcels": rows,
        "duplicate_parcels": duplicate_parcels,
        "field_count": fields,
        "enrichment_only_pins_removed": orphan_enrichment_rows,
        "downloads": downloads,
        "loads": loads,
        "notes": [
            "One output row per 14-digit Cook County PIN.",
            "Current 2026 owner/address and assessed-value datasets were used; assessed values are not market values.",
            "Latest available 2025 commercial valuation fields were joined where a key PIN matched.",
            "Latest recorded sale row was retained per PIN; all raw sale rows remain in the compressed source snapshot.",
            "Parcel acreage is calculated from the official 2021 GIS parcel geometry and may be unavailable for parcels created after that geometry vintage.",
        ],
    }
    meta_path = canonical.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return 0 if rows and duplicate_parcels == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
