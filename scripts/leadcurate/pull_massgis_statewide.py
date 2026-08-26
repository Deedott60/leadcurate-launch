#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


TODAY = date.today().isoformat()
PARCEL_URL = "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Property_Tax_Parcels/FeatureServer/0"
MUNICIPAL_URL = "https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Municipalities/FeatureServer/1"
DEFAULT_OUTPUT = Path(f"/opt/leadcurate/raw_imports/massachusetts-statewide/{TODAY}/massgis-parcels-canonical.csv")


def request_json(url: str, params: dict[str, Any], attempts: int = 5) -> dict[str, Any]:
    error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(f"{url}?{urlencode(params)}", headers={"User-Agent": "LeadCurate/1.0"})
            with urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if "error" in payload:
                raise RuntimeError(str(payload["error"]))
            return payload
        except Exception as exc:
            error = exc
            time.sleep(2 ** attempt)
    raise RuntimeError(f"MassGIS request failed after {attempts} attempts: {error}")


def municipality_map() -> dict[int, dict[str, Any]]:
    payload = request_json(
        MUNICIPAL_URL + "/query",
        {"where": "1=1", "outFields": "TOWN,TOWN_ID,COUNTY,FIPS_STCO,POP2020", "returnGeometry": "false", "f": "json"},
    )
    return {int(f["attributes"]["TOWN_ID"]): f["attributes"] for f in payload["features"]}


def fetch_page(start_id: int, batch_size: int, out_fields: str) -> list[dict[str, Any]]:
    payload = request_json(
        PARCEL_URL + "/query",
        {
            "where": f"OBJECTID >= {start_id} AND OBJECTID < {start_id + batch_size}",
            "outFields": out_fields,
            "returnGeometry": "false",
            "orderByFields": "OBJECTID",
            "resultRecordCount": batch_size,
            "f": "json",
        },
    )
    return [feature["attributes"] for feature in payload.get("features", [])]


def pull(output: Path, workers: int, batch_size: int) -> dict[str, Any]:
    output.parent.mkdir(parents=True, exist_ok=True)
    municipalities = municipality_map()
    if len(municipalities) != 351:
        raise RuntimeError(f"Expected 351 Massachusetts municipalities, received {len(municipalities)}")
    layer = request_json(PARCEL_URL, {"f": "json"})
    retrieved_at_utc = datetime.now(timezone.utc).isoformat()
    edit_epoch_ms = layer.get("editingInfo", {}).get("dataLastEditDate")
    data_last_edited_utc = (
        datetime.fromtimestamp(float(edit_epoch_ms) / 1000, timezone.utc).isoformat()
        if edit_epoch_ms
        else None
    )
    source_fields = [field["name"] for field in layer["fields"]]
    out_fields = ",".join(source_fields)
    sqlite_path = output.with_suffix(".sqlite")
    for stale in (sqlite_path, Path(str(sqlite_path) + "-wal"), Path(str(sqlite_path) + "-shm")):
        if stale.exists():
            stale.unlink()
    conn = sqlite3.connect(sqlite_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    columns = ["LC_PARCEL_KEY", "COUNTY", "COUNTY_FIPS", "TOWN_POP2020"] + source_fields
    definitions = ",".join(f'"{column}" TEXT' for column in columns)
    conn.execute(f'CREATE TABLE parcels ({definitions}, PRIMARY KEY ("LC_PARCEL_KEY"))')
    placeholders = ",".join("?" for _ in columns)
    insert = f"INSERT OR REPLACE INTO parcels VALUES ({placeholders})"

    count_payload = request_json(
        PARCEL_URL + "/query",
        {"where": "1=1", "returnCountOnly": "true", "f": "json"},
    )
    source_count = int(count_payload["count"])
    oid_payload = request_json(
        PARCEL_URL + "/query",
        {
            "where": "1=1",
            "outStatistics": json.dumps([
                {"statisticType": "min", "onStatisticField": "OBJECTID", "outStatisticFieldName": "min_oid"},
                {"statisticType": "max", "onStatisticField": "OBJECTID", "outStatisticFieldName": "max_oid"},
            ]),
            "returnGeometry": "false",
            "f": "json",
        },
    )
    oid_stats = oid_payload["features"][0]["attributes"]
    min_oid = int(oid_stats["min_oid"])
    max_oid = int(oid_stats["max_oid"])
    starts = list(range(min_oid, max_oid + 1, batch_size))

    fetched_rows = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        start_iter = iter(starts)
        pending = {pool.submit(fetch_page, start, batch_size, out_fields) for start in starts[: workers * 2]}
        for _ in range(min(workers * 2, len(starts))):
            next(start_iter)
        index = 0
        while pending:
            completed, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                rows = future.result()
                batch = []
                for row in rows:
                    town_id = int(row.get("TOWN_ID"))
                    muni = municipalities[town_id]
                    prop_id = str(row.get("PROP_ID") or "").strip()
                    loc_id = str(row.get("LOC_ID") or "").strip()
                    object_id = str(row.get("OBJECTID") or "").strip()
                    parcel_key = f"{town_id}|{prop_id or loc_id or object_id}"
                    prefix = [parcel_key, muni["COUNTY"], muni["FIPS_STCO"], muni["POP2020"]]
                    batch.append(tuple(prefix + [row.get(field) for field in source_fields]))
                conn.executemany(insert, batch)
                fetched_rows += len(batch)
                index += 1
                try:
                    start = next(start_iter)
                except StopIteration:
                    pass
                else:
                    pending.add(pool.submit(fetch_page, start, batch_size, out_fields))
                if index % 50 == 0:
                    conn.commit()
                    print(json.dumps({"pages_complete": index, "pages_total": len(starts), "rows_fetched": fetched_rows}), flush=True)
    conn.commit()

    unique_rows = int(conn.execute("SELECT COUNT(*) FROM parcels").fetchone()[0])
    fiscal_years = {
        str(year or "missing"): int(count)
        for year, count in conn.execute(
            "SELECT COALESCE(NULLIF(TRIM(FY), ''), 'missing'), COUNT(*) "
            "FROM parcels GROUP BY COALESCE(NULLIF(TRIM(FY), ''), 'missing') ORDER BY 1"
        )
    }
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in conn.execute("SELECT * FROM parcels ORDER BY TOWN_ID, LC_PARCEL_KEY"):
            writer.writerow(["" if value is None else value for value in row])
    conn.close()
    payload = {
        "ok": unique_rows > 0 and unique_rows <= fetched_rows,
        "source_url": PARCEL_URL,
        "source_data_last_edited_utc": data_last_edited_utc,
        "retrieved_at_utc": retrieved_at_utc,
        "source_status": "Current live MassGIS service; municipal assessor fiscal years vary and must be checked separately.",
        "municipality_source_url": MUNICIPAL_URL,
        "municipalities": len(municipalities),
        "source_reported_rows": source_count,
        "rows_fetched": fetched_rows,
        "unique_parcels": unique_rows,
        "duplicate_rows_removed": fetched_rows - unique_rows,
        "field_count": len(columns),
        "municipal_fiscal_years": fiscal_years,
        "output_csv": str(output),
    }
    output.with_suffix(".meta.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Pull the official MassGIS statewide assessor parcel layer without geometry.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=2000)
    args = parser.parse_args()
    payload = pull(args.output, args.workers, args.batch_size)
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
