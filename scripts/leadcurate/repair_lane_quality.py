#!/usr/bin/env python3
"""Repair an existing lane file or batch directory through deterministic QA rules."""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sqlite3
import tempfile
import zlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from lane_quality import INSTITUTIONAL_OWNER, canonical_address_key, is_po_box


OWNER_FIELDS = ("lc_owner_name", "owner_name", "OWNER1", "Owner_LastName", "COMM_OWNER")
PROP_FIELDS = (
    "lc_property_address", "property_address", "SITE_ADDR",
    "ADDR_PROP_ADDRESS_FULL", "Property_Address", "property_street",
)
MAIL_FIELDS = (
    "lc_mailing_address", "mailing_address", "Mailing_Address",
    "ADDR_MAIL_ADDRESS_FULL", "OWN_ADDR", "owner_street",
)
PARCEL_FIELDS = (
    "lc_parcel_id", "parcel_id", "parcel_pid", "parcel_key",
    "Tax_ID", "PID", "U_PIN",
)
VALUE_FIELDS = (
    "lc_total_value", "total_value", "Total_Value", "assessed_value",
    "VAL_MAILED_TOT", "TOTAL_VAL", "lc_land_value", "land_value", "Land_Value",
)


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def first_value(row: dict[str, str], names: tuple[str, ...]) -> str:
    return next((clean(row.get(name)) for name in names if clean(row.get(name))), "")


def to_float(value: str) -> float:
    try:
        return float("".join(char for char in value if char in "0123456789.-") or 0)
    except ValueError:
        return 0.0


def input_files(source: Path) -> list[Path]:
    if source.is_file():
        return [source]
    files = sorted(source.glob("batch-*.csv")) + sorted(source.glob("batch-*.csv.gz"))
    if not files:
        files = [
            path for path in sorted(source.glob("*.csv*"))
            if "preview" not in path.name and "meta" not in path.name
        ]
    return files


def open_csv(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", newline="", encoding="utf-8-sig", errors="replace")
    return path.open("r", newline="", encoding="utf-8-sig", errors="replace")


def rows_from(files: Iterable[Path]):
    for path in files:
        with open_csv(path) as handle:
            yield from csv.DictReader(handle)


def header_from(path: Path) -> list[str]:
    with open_csv(path) as handle:
        return list(csv.DictReader(handle).fieldnames or [])


def percentile_95(connection: sqlite3.Connection) -> float | None:
    count = connection.execute("SELECT count(*) FROM eligible WHERE value > 0").fetchone()[0]
    if not count:
        return None
    offset = max(0, int((count - 1) * 0.95))
    return connection.execute(
        "SELECT value FROM eligible WHERE value > 0 ORDER BY value LIMIT 1 OFFSET ?",
        (offset,),
    ).fetchone()[0]


def repair(args: argparse.Namespace) -> dict[str, Any]:
    files = input_files(args.source)
    if not files:
        raise ValueError(f"no lane CSV files found under {args.source}")
    fields = header_from(files[0])
    if not fields:
        raise ValueError(f"missing CSV header in {files[0]}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    counters = {
        "input_rows": 0,
        "duplicate_parcels_removed": 0,
        "missing_core_removed": 0,
        "owner_occupied_or_unprovable_removed": 0,
        "institutional_removed": 0,
        "top_value_removed": 0,
    }

    with tempfile.TemporaryDirectory(prefix="leadcurate-lane-repair-") as temp_dir:
        database = Path(temp_dir) / "rows.sqlite3"
        connection = sqlite3.connect(database)
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute(
            "CREATE TABLE eligible (parcel_key TEXT PRIMARY KEY, value REAL NOT NULL, payload BLOB NOT NULL)"
        )

        for row in rows_from(files):
            counters["input_rows"] += 1
            parcel = first_value(row, PARCEL_FIELDS).upper()
            owner = first_value(row, OWNER_FIELDS)
            property_address = first_value(row, PROP_FIELDS)
            mailing_address = first_value(row, MAIL_FIELDS)
            if not parcel or not owner or not property_address:
                counters["missing_core_removed"] += 1
                continue

            if args.require_absentee:
                property_key = canonical_address_key(property_address)
                mailing_key = canonical_address_key(mailing_address)
                proven_absentee = is_po_box(mailing_address) or bool(
                    property_key and mailing_key and property_key != mailing_key
                )
                if not proven_absentee:
                    counters["owner_occupied_or_unprovable_removed"] += 1
                    continue

            if args.exclude_institutional and INSTITUTIONAL_OWNER.search(owner):
                counters["institutional_removed"] += 1
                continue

            value = to_float(first_value(row, VALUE_FIELDS))
            try:
                connection.execute(
                    "INSERT INTO eligible(parcel_key, value, payload) VALUES (?, ?, ?)",
                    (
                        parcel,
                        value,
                        sqlite3.Binary(zlib.compress(
                            json.dumps(row, separators=(",", ":")).encode("utf-8"),
                            level=1,
                        )),
                    ),
                )
            except sqlite3.IntegrityError:
                counters["duplicate_parcels_removed"] += 1
            if counters["input_rows"] % 10000 == 0:
                connection.commit()
        connection.commit()

        cutoff = None
        if args.trim_top_percent:
            cutoff = percentile_95(connection)
            if cutoff is not None:
                counters["top_value_removed"] = connection.execute(
                    "SELECT count(*) FROM eligible WHERE value > ?",
                    (cutoff,),
                ).fetchone()[0]

        where = "WHERE value <= ?" if cutoff is not None else ""
        params = (cutoff,) if cutoff is not None else ()
        order = (
            "ORDER BY CASE WHEN value > 0 THEN 0 ELSE 1 END, value, parcel_key"
            if args.sort_wholesale
            else "ORDER BY rowid"
        )
        query = f"SELECT payload FROM eligible {where} {order}"
        output_rows = 0
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for (payload,) in connection.execute(query, params):
                writer.writerow(json.loads(zlib.decompress(payload)))
                output_rows += 1
        connection.close()

    report = {
        "market": args.market,
        "lane": args.lane,
        "source": str(args.source),
        "output": str(args.output),
        "output_rows": output_rows,
        "require_absentee": args.require_absentee,
        "exclude_institutional": args.exclude_institutional,
        "trim_top_percent": args.trim_top_percent,
        "sort_wholesale": args.sort_wholesale,
        "value_95th_percentile": cutoff,
        "counters": counters,
        "repaired_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True)
    parser.add_argument("--lane", required=True)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--require-absentee", action="store_true")
    parser.add_argument("--exclude-institutional", action="store_true")
    parser.add_argument("--trim-top-percent", type=float, choices=(5.0,))
    parser.add_argument("--sort-wholesale", action="store_true")
    args = parser.parse_args()
    repair(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
