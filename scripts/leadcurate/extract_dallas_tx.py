#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
import zipfile
from pathlib import Path
from typing import Iterable


DEFAULT_ARCHIVE = Path(
    "/opt/leadcurate/raw_imports/dallas-tx/2026-07-16/DCAD2026_CURRENT.ZIP"
)
DEFAULT_OUTPUT = Path(
    "/opt/leadcurate/raw_imports/dallas-tx/2026-07-16/dallas-parcels-canonical.csv"
)


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def clean(value: object) -> str:
    return str(value or "").strip()


def load_zip_csv(
    conn: sqlite3.Connection,
    archive: zipfile.ZipFile,
    member: str,
    table: str,
    columns: list[str] | None = None,
    primary_key: str | None = None,
    where_divisions: set[str] | None = None,
    optional_columns: set[str] | None = None,
) -> tuple[list[str], int]:
    with archive.open(member) as raw:
        text = (line.decode("latin1", "replace") for line in raw)
        reader = csv.DictReader(text)
        source_columns = [clean(c) for c in (reader.fieldnames or [])]
        selected = columns or source_columns
        optional_columns = optional_columns or set()
        missing = [c for c in selected if c not in source_columns and c not in optional_columns]
        if missing:
            raise ValueError(f"{member} is missing expected columns: {missing}")
        defs = [f"{q(c)} TEXT" for c in selected]
        if primary_key:
            defs.append(f"PRIMARY KEY ({q(primary_key)})")
        conn.execute(f"DROP TABLE IF EXISTS {q(table)}")
        conn.execute(f"CREATE TABLE {q(table)} ({', '.join(defs)})")
        placeholders = ",".join("?" for _ in selected)
        verb = "INSERT OR REPLACE" if primary_key else "INSERT"
        insert = f"{verb} INTO {q(table)} VALUES ({placeholders})"
        batch: list[tuple[str, ...]] = []
        count = 0
        for row in reader:
            if where_divisions and clean(row.get("DIVISION_CD")) not in where_divisions:
                continue
            batch.append(tuple(clean(row.get(c)) for c in selected))
            if len(batch) >= 10_000:
                conn.executemany(insert, batch)
                count += len(batch)
                batch.clear()
        if batch:
            conn.executemany(insert, batch)
            count += len(batch)
        conn.commit()
    return selected, count


def make_aggregate(
    conn: sqlite3.Connection,
    raw_table: str,
    output_table: str,
    expressions: Iterable[str],
) -> None:
    conn.execute(f"DROP TABLE IF EXISTS {q(output_table)}")
    conn.execute(
        f"CREATE TABLE {q(output_table)} AS "
        f"SELECT ACCOUNT_NUM, {', '.join(expressions)} "
        f"FROM {q(raw_table)} GROUP BY ACCOUNT_NUM"
    )
    conn.execute(
        f"CREATE UNIQUE INDEX {q('idx_' + output_table + '_account')} "
        f"ON {q(output_table)} (ACCOUNT_NUM)"
    )
    conn.execute(f"DROP TABLE {q(raw_table)}")
    conn.commit()


def extract(archive_path: Path, output_path: Path, sqlite_path: Path) -> dict[str, object]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()
    conn = sqlite3.connect(sqlite_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA temp_store=FILE")
    source_counts: dict[str, int] = {}

    with zipfile.ZipFile(archive_path) as archive:
        value_columns, source_counts["ACCOUNT_APPRL_YEAR.CSV"] = load_zip_csv(
            conn,
            archive,
            "ACCOUNT_APPRL_YEAR.CSV",
            "account_value",
            primary_key="ACCOUNT_NUM",
            where_divisions={"RES", "COM"},
        )
        info_columns, source_counts["ACCOUNT_INFO.CSV"] = load_zip_csv(
            conn,
            archive,
            "ACCOUNT_INFO.CSV",
            "account_info",
            primary_key="ACCOUNT_NUM",
            where_divisions={"RES", "COM"},
        )
        conn.execute("CREATE INDEX idx_info_account ON account_info (ACCOUNT_NUM)")
        conn.commit()

        land_cols = [
            "ACCOUNT_NUM", "SPTD_CD", "SPTD_DESC", "ZONING", "AREA_SIZE",
            "AREA_UOM_DESC", "PRICING_METH_DESC", "COST_PER_UOM",
            "MARKET_ADJ_PCT", "VAL_AMT", "AG_USE_IND", "ACCT_AG_VAL_AMT",
        ]
        _, source_counts["LAND.CSV"] = load_zip_csv(
            conn, archive, "LAND.CSV", "land_raw", columns=land_cols
        )
        make_aggregate(
            conn,
            "land_raw",
            "land_agg",
            [
                "GROUP_CONCAT(DISTINCT SPTD_CD) AS LAND_SPTD_CODES",
                "GROUP_CONCAT(DISTINCT SPTD_DESC) AS LAND_SPTD_DESCS",
                "GROUP_CONCAT(DISTINCT ZONING) AS LAND_ZONING",
                "GROUP_CONCAT(DISTINCT AREA_UOM_DESC) AS LAND_AREA_UNITS",
                "GROUP_CONCAT(DISTINCT PRICING_METH_DESC) AS LAND_PRICING_METHODS",
                "SUM(CASE WHEN UPPER(AREA_UOM_DESC) LIKE '%ACRE%' THEN CAST(AREA_SIZE AS REAL) ELSE CAST(AREA_SIZE AS REAL) / 43560.0 END) AS LAND_ACRES_CALC",
                "SUM(CAST(VAL_AMT AS REAL)) AS LAND_SECTION_VALUE_SUM",
                "MAX(CAST(COST_PER_UOM AS REAL)) AS LAND_MAX_COST_PER_UOM",
                "MAX(CAST(MARKET_ADJ_PCT AS REAL)) AS LAND_MAX_MARKET_ADJ_PCT",
                "MAX(CASE WHEN UPPER(AG_USE_IND) = 'Y' THEN 1 ELSE 0 END) AS LAND_AG_USE_IND",
                "SUM(CAST(ACCT_AG_VAL_AMT AS REAL)) AS LAND_AG_VALUE_SUM",
            ],
        )

        res_cols = [
            "ACCOUNT_NUM", "BLDG_CLASS_DESC", "YR_BUILT", "EFF_YR_BUILT",
            "CDU_RATING_DESC", "TOT_MAIN_SF", "TOT_LIVING_AREA_SF",
            "NUM_STORIES_DESC", "CONSTR_FRAM_TYP_DESC", "FOUNDATION_TYP_DESC",
            "HEATING_TYP_DESC", "AC_TYP_DESC", "EXT_WALL_DESC", "ROOF_TYP_DESC",
            "ROOF_MAT_DESC", "NUM_FIREPLACES", "NUM_KITCHENS", "NUM_FULL_BATHS",
            "NUM_HALF_BATHS", "NUM_BEDROOMS", "POOL_IND", "DEPRECIATION_PCT",
            "NUM_UNITS",
        ]
        _, source_counts["RES_DETAIL.CSV"] = load_zip_csv(
            conn, archive, "RES_DETAIL.CSV", "res_raw", columns=res_cols
        )
        make_aggregate(
            conn,
            "res_raw",
            "res_agg",
            [
                "GROUP_CONCAT(DISTINCT BLDG_CLASS_DESC) AS RES_BLDG_CLASSES",
                "MIN(NULLIF(CAST(YR_BUILT AS INTEGER), 0)) AS RES_MIN_YEAR_BUILT",
                "MAX(CAST(EFF_YR_BUILT AS INTEGER)) AS RES_MAX_EFFECTIVE_YEAR",
                "GROUP_CONCAT(DISTINCT CDU_RATING_DESC) AS RES_CONDITION_RATINGS",
                "SUM(CAST(TOT_MAIN_SF AS REAL)) AS RES_TOTAL_MAIN_SF",
                "SUM(CAST(TOT_LIVING_AREA_SF AS REAL)) AS RES_TOTAL_LIVING_SF",
                "GROUP_CONCAT(DISTINCT NUM_STORIES_DESC) AS RES_STORIES",
                "GROUP_CONCAT(DISTINCT CONSTR_FRAM_TYP_DESC) AS RES_CONSTRUCTION",
                "GROUP_CONCAT(DISTINCT FOUNDATION_TYP_DESC) AS RES_FOUNDATION",
                "GROUP_CONCAT(DISTINCT HEATING_TYP_DESC) AS RES_HEATING",
                "GROUP_CONCAT(DISTINCT AC_TYP_DESC) AS RES_AC",
                "GROUP_CONCAT(DISTINCT EXT_WALL_DESC) AS RES_EXT_WALL",
                "GROUP_CONCAT(DISTINCT ROOF_TYP_DESC) AS RES_ROOF_TYPE",
                "GROUP_CONCAT(DISTINCT ROOF_MAT_DESC) AS RES_ROOF_MATERIAL",
                "SUM(CAST(NUM_FIREPLACES AS INTEGER)) AS RES_FIREPLACES",
                "SUM(CAST(NUM_KITCHENS AS INTEGER)) AS RES_KITCHENS",
                "SUM(CAST(NUM_FULL_BATHS AS INTEGER)) AS RES_FULL_BATHS",
                "SUM(CAST(NUM_HALF_BATHS AS INTEGER)) AS RES_HALF_BATHS",
                "SUM(CAST(NUM_BEDROOMS AS INTEGER)) AS RES_BEDROOMS",
                "MAX(CASE WHEN UPPER(POOL_IND) = 'Y' THEN 1 ELSE 0 END) AS RES_POOL_IND",
                "MAX(CAST(DEPRECIATION_PCT AS REAL)) AS RES_MAX_DEPRECIATION_PCT",
                "SUM(CAST(NUM_UNITS AS INTEGER)) AS RES_NUM_UNITS",
            ],
        )

        com_cols = [
            "ACCOUNT_NUM", "BLDG_CLASS_DESC", "YEAR_BUILT", "REMODEL_YR",
            "GROSS_BLDG_AREA", "NUM_STORIES", "CONSTR_TYP_DESC", "NUM_UNITS",
            "NET_LEASE_AREA", "PROPERTY_NAME", "PROPERTY_QUAL_DESC",
            "PROPERTY_COND_DESC", "PHYS_DEPR_PCT", "FUNCT_DEPR_PCT",
            "EXTRNL_DEPR_PCT", "TOT_DEPR_PCT", "APPR_METHOD_DESC",
            "COMPARABILITY_CD", "PCT_COMPLETE",
        ]
        _, source_counts["COM_DETAIL.CSV"] = load_zip_csv(
            conn, archive, "COM_DETAIL.CSV", "com_raw", columns=com_cols
        )
        make_aggregate(
            conn,
            "com_raw",
            "com_agg",
            [
                "GROUP_CONCAT(DISTINCT BLDG_CLASS_DESC) AS COM_BLDG_CLASSES",
                "MIN(NULLIF(CAST(YEAR_BUILT AS INTEGER), 0)) AS COM_MIN_YEAR_BUILT",
                "MAX(CAST(REMODEL_YR AS INTEGER)) AS COM_MAX_REMODEL_YEAR",
                "SUM(CAST(GROSS_BLDG_AREA AS REAL)) AS COM_GROSS_BLDG_AREA",
                "MAX(CAST(NUM_STORIES AS REAL)) AS COM_MAX_STORIES",
                "GROUP_CONCAT(DISTINCT CONSTR_TYP_DESC) AS COM_CONSTRUCTION",
                "SUM(CAST(NUM_UNITS AS INTEGER)) AS COM_NUM_UNITS",
                "SUM(CAST(NET_LEASE_AREA AS REAL)) AS COM_NET_LEASE_AREA",
                "GROUP_CONCAT(DISTINCT PROPERTY_NAME) AS COM_PROPERTY_NAMES",
                "GROUP_CONCAT(DISTINCT PROPERTY_QUAL_DESC) AS COM_QUALITY",
                "GROUP_CONCAT(DISTINCT PROPERTY_COND_DESC) AS COM_CONDITION",
                "MAX(CAST(PHYS_DEPR_PCT AS REAL)) AS COM_PHYS_DEPR_PCT",
                "MAX(CAST(FUNCT_DEPR_PCT AS REAL)) AS COM_FUNCT_DEPR_PCT",
                "MAX(CAST(EXTRNL_DEPR_PCT AS REAL)) AS COM_EXTERNAL_DEPR_PCT",
                "MAX(CAST(TOT_DEPR_PCT AS REAL)) AS COM_TOTAL_DEPR_PCT",
                "GROUP_CONCAT(DISTINCT APPR_METHOD_DESC) AS COM_APPR_METHODS",
                "GROUP_CONCAT(DISTINCT COMPARABILITY_CD) AS COM_COMPARABILITY",
                "MIN(CAST(PCT_COMPLETE AS REAL)) AS COM_MIN_PCT_COMPLETE",
            ],
        )

        multi_cols = ["ACCOUNT_NUM", "OWNER_NAME", "OWNERSHIP_PCT"]
        _, source_counts["MULTI_OWNER.CSV"] = load_zip_csv(
            conn, archive, "MULTI_OWNER.CSV", "multi_raw", columns=multi_cols
        )
        make_aggregate(
            conn,
            "multi_raw",
            "multi_agg",
            [
                "GROUP_CONCAT(DISTINCT OWNER_NAME) AS ADDITIONAL_OWNERS",
                "SUM(CAST(OWNERSHIP_PCT AS REAL)) AS ADDITIONAL_OWNERSHIP_PCT",
            ],
        )

        exempt_cols = [
            "ACCOUNT_NUM", "HOMESTEAD_EFF_DT", "OVER65_DESC", "DISABLED_DESC",
            "TAX_DEFERRED_DESC", "HS_PCT", "CAPPED_HS_AMT", "CIRCUIT_BK_FLG",
        ]
        _, source_counts["APPLIED_STD_EXEMPT.CSV"] = load_zip_csv(
            conn,
            archive,
            "APPLIED_STD_EXEMPT.CSV",
            "std_exempt_raw",
            columns=exempt_cols,
            optional_columns={"CIRCUIT_BK_FLG"},
        )
        make_aggregate(
            conn,
            "std_exempt_raw",
            "std_exempt_agg",
            [
                "MAX(CASE WHEN TRIM(HOMESTEAD_EFF_DT) <> '' OR CAST(HS_PCT AS REAL) > 0 THEN 1 ELSE 0 END) AS HOMESTEAD_ACTIVE",
                "MIN(NULLIF(HOMESTEAD_EFF_DT, '')) AS HOMESTEAD_EFF_DATE",
                "GROUP_CONCAT(DISTINCT NULLIF(OVER65_DESC, '')) AS OVER65_DESCS",
                "GROUP_CONCAT(DISTINCT NULLIF(DISABLED_DESC, '')) AS DISABLED_DESCS",
                "GROUP_CONCAT(DISTINCT NULLIF(TAX_DEFERRED_DESC, '')) AS TAX_DEFERRED_DESCS",
                "MAX(CAST(HS_PCT AS REAL)) AS HOMESTEAD_MAX_PCT",
                "MAX(CAST(CAPPED_HS_AMT AS REAL)) AS HOMESTEAD_CAPPED_VALUE",
                "MAX(CASE WHEN UPPER(CIRCUIT_BK_FLG) = 'Y' THEN 1 ELSE 0 END) AS CIRCUIT_BREAKER_ACTIVE",
            ],
        )

        acct_exempt_cols = ["ACCOUNT_NUM", "EXEMPTION"]
        _, source_counts["ACCT_EXEMPT_VALUE.CSV"] = load_zip_csv(
            conn, archive, "ACCT_EXEMPT_VALUE.CSV", "acct_exempt_raw", columns=acct_exempt_cols
        )
        make_aggregate(
            conn,
            "acct_exempt_raw",
            "acct_exempt_agg",
            ["GROUP_CONCAT(DISTINCT EXEMPTION) AS ACCOUNT_EXEMPTIONS"],
        )

    info_output: list[tuple[str, str]] = []
    used = set(value_columns)
    for column in info_columns:
        if column in {"ACCOUNT_NUM", "APPRAISAL_YR", "DIVISION_CD"}:
            continue
        alias = column if column not in used else f"INFO_{column}"
        info_output.append((column, alias))
        used.add(alias)

    aggregate_tables = ["land_agg", "res_agg", "com_agg", "multi_agg", "std_exempt_agg", "acct_exempt_agg"]
    aggregate_columns: list[tuple[str, str]] = []
    for table in aggregate_tables:
        for row in conn.execute(f"PRAGMA table_info({q(table)})"):
            column = row[1]
            if column != "ACCOUNT_NUM":
                aggregate_columns.append((table, column))

    select_parts = [f"v.{q(c)} AS {q(c)}" for c in value_columns]
    select_parts.extend(f"i.{q(c)} AS {q(alias)}" for c, alias in info_output)
    select_parts.extend(f"{q(t)}.{q(c)} AS {q(c)}" for t, c in aggregate_columns)
    joins = " ".join(
        ["LEFT JOIN account_info i ON i.ACCOUNT_NUM = v.ACCOUNT_NUM"]
        + [f"LEFT JOIN {q(t)} ON {q(t)}.ACCOUNT_NUM = v.ACCOUNT_NUM" for t in aggregate_tables]
    )
    query = f"SELECT {', '.join(select_parts)} FROM account_value v {joins} ORDER BY v.ACCOUNT_NUM"
    output_columns = value_columns + [a for _, a in info_output] + [c for _, c in aggregate_columns]
    row_count = 0
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(output_columns)
        for row in conn.execute(query):
            writer.writerow(["" if value is None else value for value in row])
            row_count += 1

    unique_count = conn.execute("SELECT COUNT(DISTINCT ACCOUNT_NUM) FROM account_value").fetchone()[0]
    conn.close()
    payload = {
        "ok": row_count == unique_count,
        "source_archive": str(archive_path),
        "output_csv": str(output_path),
        "output_rows": row_count,
        "unique_parcels": unique_count,
        "duplicate_parcels": row_count - unique_count,
        "output_columns": len(output_columns),
        "source_rows_loaded": source_counts,
    }
    output_path.with_suffix(".meta.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Dallas DCAD current ZIP into one maximum-field row per real parcel.")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--sqlite", type=Path)
    args = parser.parse_args()
    sqlite_path = args.sqlite or args.output.with_suffix(".sqlite")
    payload = extract(args.archive, args.output, sqlite_path)
    print(json.dumps(payload, indent=2))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
