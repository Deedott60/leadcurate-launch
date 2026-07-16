#!/usr/bin/env python3
"""Parse Wayne County MI's official 2026 BS&A assessment package.

The source uses the BS&A "ASCII for General Use" fixed-width layout. This
script streams the ZIP into SQLite, joins VALUES.TXT to NAMES.TXT by parcel,
and exports one active assessment row per parcel.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


LAYOUT_URL = (
    "https://www.bsasoftware.com/Portals/0/Support/Legacy%20Application/"
    "Assessing-Equalization/exp_gen.pdf"
)

GOV_UNIT_NAMES = {
    "01": "Detroit",
    "30": "Allen Park",
    "31": "Belleville",
    "32": "Dearborn",
    "33": "Dearborn Heights",
    "34": "Ecorse",
    "35": "Garden City",
    "36": "Gibraltar",
    "37": "Grosse Pointe",
    "38": "Grosse Pointe Farms",
    "39": "Grosse Pointe Park",
    "40": "Grosse Pointe Woods",
    "41": "Hamtramck",
    "42": "Harper Woods",
    "43": "Highland Park",
    "44": "Inkster",
    "45": "Lincoln Park",
    "46": "Livonia",
    "47": "Melvindale",
    "48": "Northville",
    "49": "Plymouth",
    "50": "River Rouge",
    "51": "Riverview",
    "52": "Rockwood",
    "53": "Southgate",
    "54": "Trenton",
    "55": "Wayne",
    "56": "Westland",
    "57": "Wyandotte",
    "58": "Flat Rock",
    "59": "Woodhaven",
    "60": "Taylor",
    "70": "Brownstown Township",
    "71": "Canton Township",
    "73": "Grosse Ile Township",
    "74": "Grosse Pointe Shores",
    "75": "Huron Township",
    "77": "Northville Township",
    "78": "Plymouth Township",
    "79": "Redford Township",
    "80": "Romulus",
    "81": "Sumpter Township",
    "83": "Van Buren Township",
}

REAL_PROPERTY_CLASSES = (
    "101", "102", "110",
    "201", "202", "203", "207", "210",
    "301", "302", "303", "307", "310",
    "401", "402", "403", "407", "410",
)


def text(line: str, start: int, size: int) -> str:
    return line[start - 1 : start - 1 + size].strip()


def integer(line: str, start: int, size: int) -> int | None:
    value = text(line, start, size).replace(",", "")
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def decimal(line: str, start: int, size: int) -> float | None:
    value = text(line, start, size).replace(",", "")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def compact_address(*parts: str) -> str:
    return " ".join(part.strip() for part in parts if part and part.strip())


def parse_names(line: str) -> tuple[object, ...]:
    return (
        text(line, 1, 25),
        compact_address(text(line, 26, 35), text(line, 61, 35)),
        text(line, 26, 35),
        text(line, 61, 35),
        text(line, 138, 34),
        text(line, 172, 25),
        text(line, 197, 2),
        text(line, 199, 10),
        text(line, 209, 35),
        text(line, 244, 35),
        text(line, 279, 25),
        text(line, 304, 2),
        text(line, 306, 10),
        text(line, 503, 35),
        text(line, 882, 1),
        text(line, 883, 5),
        text(line, 888, 5),
    )


def parse_values(line: str) -> tuple[object, ...]:
    return (
        text(line, 1, 25),
        text(line, 26, 5),
        text(line, 31, 5),
        text(line, 36, 1),
        text(line, 37, 20),
        text(line, 100, 5),
        text(line, 105, 2),
        text(line, 129, 5),
        decimal(line, 134, 8),
        integer(line, 391, 10),
        integer(line, 401, 10),
        integer(line, 411, 10),
        integer(line, 919, 10),
        integer(line, 982, 10),
        integer(line, 992, 10),
        decimal(line, 1162, 8),
        text(line, 1170, 8),
        integer(line, 1372, 10),
        decimal(line, 1382, 10),
        decimal(line, 1392, 8),
        decimal(line, 1400, 8),
        text(line, 1408, 25),
    )


def setup(db: sqlite3.Connection) -> None:
    db.executescript(
        """
        pragma journal_mode = wal;
        pragma synchronous = off;
        pragma temp_store = memory;
        create table names (
          parcel_id text primary key,
          owner_name text, owner_name_1 text, owner_name_2 text,
          property_street text, property_city text, property_state text, property_zip text,
          owner_care_of text, owner_street text, owner_city text, owner_state text,
          owner_zip text, owner_country text, name_status text,
          name_gov_unit text, name_tax_unit text
        ) without rowid;
        create table values_roll (
          parcel_id text primary key,
          gov_unit text, tax_unit text, record_status text, current_taxable_status text,
          property_class text, class_number text, use_code text, pre_pct real,
          assessed_value integer, capped_value integer, taxable_value integer,
          previous_assessed_value integer, land_assessment integer, building_assessment integer,
          latest_transfer_pct real, latest_transfer_date text, land_value integer,
          acreage real, frontage real, average_depth real, map_number text
        ) without rowid;
        """
    )


def load_zip(source: Path, db: sqlite3.Connection, batch_size: int) -> dict[str, object]:
    counts: dict[str, object] = {}
    with zipfile.ZipFile(source) as archive:
        names_sql = "insert or replace into names values (" + ",".join("?" * 17) + ")"
        values_sql = "insert or replace into values_roll values (" + ",".join("?" * 22) + ")"
        for member, parser, sql in (
            ("NAMES.TXT", parse_names, names_sql),
            ("VALUES.TXT", parse_values, values_sql),
        ):
            rows = 0
            malformed = 0
            batch: list[tuple[object, ...]] = []
            with archive.open(member) as raw:
                raw.readline()
                for raw_line in raw:
                    line = raw_line.decode("latin-1").rstrip("\r\n")
                    expected = 892 if member == "NAMES.TXT" else 2003
                    if len(line) < expected:
                        malformed += 1
                        continue
                    parsed = parser(line)
                    if not parsed[0]:
                        malformed += 1
                        continue
                    batch.append(parsed)
                    rows += 1
                    if len(batch) >= batch_size:
                        db.executemany(sql, batch)
                        db.commit()
                        batch.clear()
                if batch:
                    db.executemany(sql, batch)
                    db.commit()
            counts[member] = {"rows_read": rows, "malformed_rows": malformed}
    return counts


def export(db: sqlite3.Connection, output: Path) -> dict[str, object]:
    output.parent.mkdir(parents=True, exist_ok=True)
    query = """
      select
        v.parcel_id, v.gov_unit, v.tax_unit, v.record_status,
        n.owner_name, n.owner_name_1, n.owner_name_2,
        n.property_street, n.property_city, n.property_state, n.property_zip,
        n.owner_care_of, n.owner_street, n.owner_city, n.owner_state, n.owner_zip,
        n.owner_country, v.current_taxable_status, v.property_class, v.class_number,
        v.use_code, v.pre_pct, v.assessed_value, v.capped_value, v.taxable_value,
        v.previous_assessed_value, v.land_assessment, v.building_assessment,
        v.latest_transfer_pct, v.latest_transfer_date, v.land_value, v.acreage,
        v.frontage, v.average_depth, v.map_number
      from values_roll v
      join names n using (parcel_id)
      where v.record_status = 'A'
        and v.property_class in ({real_classes})
      order by v.parcel_id
    """.format(real_classes=",".join(f"'{value}'" for value in REAL_PROPERTY_CLASSES))
    cursor = db.execute(query)
    headers = [item[0] for item in cursor.description]
    headers.append("municipality")
    rows = 0
    seen: set[str] = set()
    cities: Counter[str] = Counter()
    classes: Counter[str] = Counter()
    gov_units: Counter[str] = Counter()
    cities_by_gov_unit: dict[str, Counter[str]] = defaultdict(Counter)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for row in cursor:
            writer.writerow((*row, GOV_UNIT_NAMES.get(str(row[1] or "").strip(), "Unknown")))
            rows += 1
            seen.add(row[0])
            gov_units[str(row[1] or "").strip()] += 1
            cities[str(row[8] or "").strip().upper()] += 1
            cities_by_gov_unit[str(row[1] or "").strip()][str(row[8] or "").strip().upper()] += 1
            classes[str(row[18] or "").strip()] += 1
    return {
        "rows": rows,
        "unique_parcels": len(seen),
        "duplicate_parcels": rows - len(seen),
        "field_count": len(headers),
        "top_property_cities": cities.most_common(50),
        "property_classes": classes.most_common(),
        "government_units": gov_units.most_common(),
        "top_property_cities_by_government_unit": {
            unit: counts.most_common(8) for unit, counts in sorted(cities_by_gov_unit.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--batch-size", type=int, default=20_000)
    parser.add_argument("--reuse-database", action="store_true")
    args = parser.parse_args()
    database = args.database or args.output.with_suffix(".sqlite")
    reuse = args.reuse_database and database.exists()
    if database.exists() and not reuse:
        database.unlink()
    with sqlite3.connect(database) as db:
        if reuse:
            loads = {"status": "reused_existing_database", "database": str(database)}
        else:
            setup(db)
            loads = load_zip(args.source, db, args.batch_size)
        result = export(db, args.output)
    metadata = {
        "market": "wayne-mi",
        "source_file": str(args.source),
        "source_data_as_of": "2026-06-04",
        "source_status": "2026 post-March-Board-of-Review annual assessment package",
        "source_layout": LAYOUT_URL,
        "included_real_property_classes": REAL_PROPERTY_CLASSES,
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "loads": loads,
        "canonical": str(args.output),
        "verification": result,
    }
    meta_path = args.output.with_name(args.output.stem + "-meta.json")
    meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))
    return 0 if result["duplicate_parcels"] == 0 and result["rows"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
