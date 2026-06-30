#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import glob
import json
import os
import re
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Callable

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

RAW_ROOT = Path("/opt/leadcurate/raw_imports")
SNAPSHOT_ROOT = Path("/opt/leadcurate/snapshots")

MARKET_REGISTRY: dict[str, dict[str, Any]] = {
    "wake-nc": {"display": "Wake County NC", "raw_dir": RAW_ROOT / "wake-nc", "raw_pattern": "delinquent*.xlsx", "default_city": "Raleigh", "state": "NC"},
    "cobb-ga": {"display": "Cobb County GA", "raw_dir": RAW_ROOT / "cobb-ga", "raw_pattern": "*.pdf", "default_city": "Marietta", "state": "GA", "snapshot_pattern": "cobb-ga-delinquent-*.csv"},
    "guilford-nc": {"display": "Guilford County NC", "raw_dir": RAW_ROOT / "guilford-nc", "raw_pattern": "tax-delinquent-report.csv", "default_city": "Greensboro", "state": "NC"},
    "marion-in": {"display": "Marion County IN", "raw_dir": RAW_ROOT / "marion-in", "raw_pattern": "parcels-owner-assessed.csv", "default_city": "Indianapolis", "state": "IN", "snapshot_pattern": "marion-in-*.csv"},
    "dekalb-ga": {"display": "DeKalb County GA", "raw_dir": RAW_ROOT / "dekalb-ga", "raw_pattern": "tax-parcels-2025.csv", "default_city": "Decatur", "state": "GA", "snapshot_pattern": "dekalb-ga-*.csv"},
    "forsyth-nc": {"display": "Forsyth County NC", "raw_dir": RAW_ROOT / "forsyth-nc", "raw_pattern": "parcels.csv", "default_city": "Winston-Salem", "state": "NC", "snapshot_pattern": "forsyth-nc-*.csv"},
    "fulton-ga": {"display": "Fulton County GA", "raw_dir": RAW_ROOT / "fulton-ga", "raw_pattern": "tax-parcels-2025.csv", "default_city": "Atlanta", "state": "GA", "snapshot_pattern": "fulton-ga-*.csv"},
    "harris-tx": {"display": "Harris County TX", "raw_dir": RAW_ROOT / "harris-tx", "raw_pattern": "real_acct.txt", "default_city": "Houston", "state": "TX", "snapshot_pattern": "harris-tx-permit-burnout-*.csv"},
    "jefferson-al": {"display": "Jefferson County AL", "raw_dir": RAW_ROOT / "jefferson-al", "raw_pattern": "DelinquentParcelList.xls", "default_city": "Birmingham", "state": "AL", "snapshot_pattern": "jefferson-al-delinquent-*.csv"},
    "mecklenburg-nc": {"display": "Mecklenburg County NC", "raw_dir": RAW_ROOT / "mecklenburg-nc", "raw_pattern": "parcel-lookup.csv", "default_city": "Charlotte", "state": "NC"},
}

ENTITY_WORDS = (" LLC", " INC", " CORP", " LP", " TTC", " FUND", " TRUST", " L P", " L L C", " LLP", " COMPANY", " PROPERTIES", " INVESTMENTS", " HOLDINGS", " PARTNERS", " CHURCH", " CITY OF", " COUNTY")


def clean(value: Any) -> str:
    return str(value or "").strip()


def money(value: Any) -> float:
    text = clean(value).replace("$", "").replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def is_residential_owner(owner: str, allow_entities: bool = False) -> bool:
    if not owner:
        return False
    if allow_entities:
        return True
    upper = f" {owner.upper()} "
    return not any(word in upper for word in ENTITY_WORDS)


def parse_mailing_csz(addr2: str) -> tuple[str, str, str]:
    text = clean(addr2)
    if not text:
        return "", "", ""
    zip_match = re.search(r"\b(\d{5}(?:-\d{4})?)\s*$", text)
    zip_code = zip_match.group(1) if zip_match else ""
    rest = text[: zip_match.start()].strip().rstrip(",") if zip_match else text
    state_match = re.search(r"\b([A-Z]{2})\s*$", rest)
    state = state_match.group(1) if state_match else ""
    city = rest[: state_match.start()].strip().rstrip(",") if state_match else rest
    return city.title(), state, zip_code


def motivation(owed: float, years: int) -> str:
    if owed >= 10000 or years >= 3:
        return "HOT"
    if owed >= 3000 or years >= 2:
        return "WARM"
    return "WORKING"


def date_dirs(raw_dir: Path) -> list[Path]:
    dirs = [p for p in raw_dir.iterdir() if p.is_dir()]
    return sorted(dirs, key=lambda p: p.name, reverse=True)


def latest_file(market: str, lane: str) -> Path:
    cfg = MARKET_REGISTRY[market]
    raw_dir = Path(cfg["raw_dir"])
    patterns = [cfg.get("raw_pattern", "*")]
    if lane == "active-permits":
        patterns = ["permits.txt", "real_acct.txt"]
    for dated in date_dirs(raw_dir):
        for pattern in patterns:
            matches = sorted(dated.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            if matches:
                return matches[0]
    for pattern in patterns:
        matches = sorted(raw_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if matches:
            return matches[0]
    raise FileNotFoundError(f"No raw file found for {market}/{lane}")


def latest_snapshot(market: str, pattern: str | None = None) -> Path | None:
    root = SNAPSHOT_ROOT / market
    if not root.exists():
        return None
    patterns = [pattern or "*.csv"]
    candidates: list[Path] = []
    for dated in date_dirs(root):
        for pat in patterns:
            candidates.extend(p for p in dated.glob(pat) if "preview" not in p.name and "tiered" not in p.name)
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0] if candidates else None


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def read_xlsx_rows(path: Path) -> tuple[list[str], list[tuple[Any, ...]]]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = [clean(h) for h in next(rows)]
    return headers, list(rows)


def normalize_record(raw: dict[str, Any], cfg: dict[str, Any], lane_label: str) -> dict[str, Any] | None:
    owner = clean(raw.get("owner") or raw.get("owner_name") or raw.get("Owner Name") or raw.get("OWNER_NAME") or raw.get("OWNERNME1") or raw.get("FULLOWNERNAME") or raw.get("CURRENTOWNERNAME1"))
    if not is_residential_owner(owner):
        return None
    parcel = clean(raw.get("parcel") or raw.get("parcel_id") or raw.get("Parcel REID") or raw.get("PARCEL_NUM") or raw.get("PARCELID") or raw.get("ParcelID") or raw.get("PID") or raw.get("Tax_ID"))
    account = clean(raw.get("account") or raw.get("Account ID") or raw.get("acct") or parcel)
    if not (parcel or account):
        return None
    total_owed = money(raw.get("total_owed") or raw.get("Total Owed") or raw.get("TOTAL_DUE_AMOUNT") or raw.get("delinquent_amount") or raw.get("total_due") or raw.get("BILL_DUE_AMT") or raw.get("score"))
    value = money(raw.get("value") or raw.get("Property Value") or raw.get("PROP_ASSESS_VALUE") or raw.get("TOT_APPR") or raw.get("APPRAISED_VALUE") or raw.get("CAMAPARCELID") or raw.get("mkt_val") or raw.get("Total_Value") or raw.get("TOTALVALUE"))
    if value <= 0 and total_owed <= 0:
        return None
    years = int(money(raw.get("years") or raw.get("Years Behind") or raw.get("tax_years") or 1)) or 1
    prop_zip = clean(raw.get("Property ZIP") or raw.get("SITEZIP") or raw.get("ZIPCODE") or raw.get("site_zip") or raw.get("Zip_Code"))
    mail_zip = clean(raw.get("Mailing ZIP") or raw.get("MAIL_ZIP") or raw.get("PSTLZIP5") or raw.get("OWNERZIP") or raw.get("mail_zip") or raw.get("Zip_Code"))
    absentee = "Yes" if (mail_zip and prop_zip and mail_zip[:5] != prop_zip[:5]) or clean(raw.get("absentee")).upper() in ("Y", "YES", "TRUE") else "No"
    address = clean(raw.get("address") or raw.get("Property Address") or raw.get("SITEADDRESS") or raw.get("site_addr") or raw.get("PROPERTYADDRESS") or raw.get("Location"))
    city = clean(raw.get("city") or raw.get("Property City") or raw.get("SITECITY") or raw.get("site_city") or raw.get("CITY") or cfg.get("default_city"))
    equity = max(0.0, value - total_owed)
    return {
        "Account ID": account,
        "Parcel REID": parcel,
        "Owner Name": owner.title(),
        "Secondary Owner": clean(raw.get("secondary") or raw.get("Secondary Owner") or raw.get("OWNERNME2")),
        "Property Address": address.title(),
        "Property City": city.title(),
        "Property ZIP": prop_zip,
        "Mailing Street": clean(raw.get("Mailing Street") or raw.get("MAIL_ADDR1") or raw.get("PSTLADDRESS") or raw.get("OWNERADDRESS") or raw.get("mail_address_1")).title(),
        "Mailing City": clean(raw.get("Mailing City") or raw.get("MAIL_CITY") or raw.get("PSTLCITY") or raw.get("OWNERCITY") or raw.get("mail_city")).title(),
        "Mailing State": clean(raw.get("Mailing State") or raw.get("MAIL_STATE") or raw.get("PSTLSTATE") or raw.get("OWNERSTATE") or raw.get("mail_state")),
        "Mailing ZIP": mail_zip,
        "Absentee Owner": absentee,
        "Acres": round(money(raw.get("Acres") or raw.get("PROP_SIZE") or raw.get("ACREAGE") or raw.get("Total_Acreage")), 2),
        "Property Value": round(value, 2),
        "Building Value": round(money(raw.get("Building Value") or raw.get("IMPR_APPR") or raw.get("Building_Value") or raw.get("bld_val")), 2),
        "Land Value": round(money(raw.get("Land Value") or raw.get("LNDVALUE") or raw.get("Land_Value") or raw.get("land_val")), 2),
        "Years Behind": years,
        "Total Owed": round(total_owed, 2),
        "Estimated Equity": round(equity, 2),
        "Motivation": motivation(total_owed, years),
        "Lane": lane_label,
    }


def parse_wake_nc(path: Path, cfg: dict[str, Any], lane: str) -> list[dict[str, Any]]:
    headers, rows = read_xlsx_rows(path)
    h = {name: i for i, name in enumerate(headers)}
    parcels: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        td = money(row[h.get("TOTAL_DUE")])
        tv = money(row[h.get("TOTAL_REAL_VALUE")])
        owner = clean(row[h.get("Primary_Owner")])
        if td <= 0 or tv < 10000 or not is_residential_owner(owner):
            continue
        street_name = clean(row[h.get("STREET_NAME")])
        reid = clean(row[h.get("REID")])
        acct = clean(row[h.get("ACCOUNT_NUM")])
        key = (reid, acct)
        tax_year = int(money(row[h.get("TAX_YEAR")]) or 2025)
        if key not in parcels:
            parcels[key] = {"tax_years": set(), "total_owed": 0.0}
        p = parcels[key]
        p.update({
            "parcel": reid,
            "account": acct,
            "owner": owner,
            "secondary": clean(row[h.get("Secondary_Owner")]).title(),
            "address": f"{clean(row[h.get('Street_Number')])} {street_name} {clean(row[h.get('ST_TYPE')])}".strip(),
            "city": clean(row[h.get("CITY")]) or cfg["default_city"],
            "Property ZIP": clean(row[h.get("ZIP_CODE")]).split(".")[0],
            "Acres": money(row[h.get("ACRES")]),
            "value": tv,
            "Building Value": money(row[h.get("Building_value")]),
            "Land Value": money(row[h.get("LAND_VALUE")]),
            "Mailing Street": clean(row[h.get("Mailing_Address1")]),
        })
        c, s, z = parse_mailing_csz(clean(row[h.get("Mailing_Address2")]))
        p["Mailing City"], p["Mailing State"], p["Mailing ZIP"] = c, s, z
        p["tax_years"].add(tax_year)
        p["total_owed"] += td
    out = []
    for p in parcels.values():
        p["years"] = len(p.pop("tax_years"))
        rec = normalize_record(p, cfg, "Tax Delinquent")
        if rec:
            out.append(rec)
    return out


def parse_guilford_nc(path: Path, cfg: dict[str, Any], lane: str) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row in read_csv(path):
        parcel = clean(row.get("PARCEL_NUM"))
        if not parcel:
            continue
        rec = grouped.setdefault(parcel, dict(row, tax_years=set(), total_owed=0.0))
        rec["total_owed"] += money(row.get("TOTAL_DUE_AMOUNT"))
        rec["tax_years"].add(clean(row.get("TAX_YEAR")))
    out = []
    for rec in grouped.values():
        rec["years"] = len(rec.pop("tax_years"))
        normalized = normalize_record(rec, cfg, "Tax Delinquent")
        if normalized:
            out.append(normalized)
    return out


def parse_snapshot(path: Path, cfg: dict[str, Any], lane: str) -> list[dict[str, Any]]:
    label = "Active Permits Distress" if lane == "active-permits" else "Tax Delinquent"
    return [r for r in (normalize_record(row, cfg, label) for row in read_csv(path)) if r]


def parse_generic_csv(path: Path, cfg: dict[str, Any], lane: str) -> list[dict[str, Any]]:
    label = "Probate Premium" if lane == "probate" else "Tax Delinquent"
    return [r for r in (normalize_record(row, cfg, label) for row in read_csv(path)) if r]


PARSERS: dict[str, Callable[[Path, dict[str, Any], str], list[dict[str, Any]]]] = {
    "wake-nc": parse_wake_nc,
    "guilford-nc": parse_guilford_nc,
}


def load_records(market: str, lane: str) -> tuple[Path, list[dict[str, Any]]]:
    cfg = MARKET_REGISTRY[market]
    if market in PARSERS and lane == "tax-delinquent":
        src = latest_file(market, lane)
        return src, PARSERS[market](src, cfg, lane)
    snap = latest_snapshot(market, cfg.get("snapshot_pattern"))
    if snap:
        return snap, parse_snapshot(snap, cfg, lane)
    src = latest_file(market, lane)
    return src, parse_generic_csv(src, cfg, lane)


def add_analytics(records: list[dict[str, Any]], market: str, lane: str, src: Path) -> dict[str, Any]:
    hot = sum(1 for r in records if r["Motivation"] == "HOT")
    warm = sum(1 for r in records if r["Motivation"] == "WARM")
    absentee = sum(1 for r in records if r["Absentee Owner"] == "Yes")
    heirs = sum(1 for r in records if re.search(r"\b(heirs|hrs)\b", r["Owner Name"], re.I))
    owed = [float(r["Total Owed"]) for r in records]
    years = [int(r["Years Behind"]) for r in records]
    return {
        "market_slug": market,
        "market": MARKET_REGISTRY[market]["display"],
        "lane": lane,
        "source_file": str(src),
        "total": len(records),
        "hot": hot,
        "warm": warm,
        "working": len(records) - hot - warm,
        "absentee": absentee,
        "heirs_count": heirs,
        "top_equity": max((float(r["Estimated Equity"]) for r in records), default=0),
        "top_debt": max(owed, default=0),
        "median_debt": sorted(owed)[len(owed) // 2] if owed else 0,
        "median_years": sorted(years)[len(years) // 2] if years else 0,
        "avg_debt": round(sum(owed) / len(owed), 2) if owed else 0,
        "debt_buckets": bucketize(owed, [1000, 3000, 5000, 10000], ["<$1K", "$1K-$3K", "$3K-$5K", "$5K-$10K", "$10K+"]),
        "years_buckets": bucketize(years, [1, 2, 3, 5], ["0-1", "2", "3", "4-5", "6+"]),
    }


def bucketize(values: list[float], thresholds: list[float], labels: list[str]) -> list[dict[str, Any]]:
    buckets = [{"label": label, "value": 0} for label in labels]
    for value in values:
        idx = 0
        while idx < len(thresholds) and value > thresholds[idx]:
            idx += 1
        buckets[idx]["value"] += 1
    return buckets


def write_outputs(records: list[dict[str, Any]], summary: dict[str, Any], output_dir: Path, count: int) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = summary["market_slug"]
    xlsx_path = output_dir / f"{slug}-Curated-Distress-{count}.xlsx"
    json_path = output_dir / f"{slug}-preview.json"
    wb = openpyxl.Workbook()
    cover = wb.active
    cover.title = "Cover"
    cover["A1"] = "LeadCurate"
    cover["A1"].font = Font(size=24, bold=True, color="15803d")
    cover["A3"] = f"Curated Distress List - {summary['market']}"
    cover["A3"].font = Font(size=16, bold=True)
    for i, (key, value) in enumerate([
        ("Market:", summary["market"]),
        ("Lane:", summary["lane"]),
        ("Records:", summary["total"]),
        ("HOT:", summary["hot"]),
        ("WARM:", summary["warm"]),
        ("Absentee owners:", summary["absentee"]),
        ("Top equity:", f"${summary['top_equity']:,.2f}"),
        ("Source:", summary["source_file"]),
    ], 5):
        cover[f"A{i}"] = key
        cover[f"B{i}"] = value
    sheet = wb.create_sheet("Records")
    cols = list(records[0].keys()) if records else []
    sheet.append(cols)
    for rec in records:
        sheet.append([rec.get(c) for c in cols])
    fill = PatternFill("solid", fgColor="15803d")
    font = Font(color="FFFFFF", bold=True)
    for cell in sheet[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = Alignment(horizontal="center")
    for idx, col in enumerate(cols, 1):
        sheet.column_dimensions[get_column_letter(idx)].width = max(12, min(32, len(col) + 2))
    sheet.freeze_panes = "A2"
    wb.save(xlsx_path)
    payload = dict(summary)
    payload["preview"] = [
        {"owner": r["Owner Name"], "address": r["Property Address"], "city": r["Property City"], "owed": r["Total Owed"], "value": r["Property Value"], "equity": r["Estimated Equity"], "years": r["Years Behind"], "motivation": r["Motivation"], "absentee": r["Absentee Owner"]}
        for r in records[:30]
    ]
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"xlsx": str(xlsx_path), "json": str(json_path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True, choices=sorted(MARKET_REGISTRY))
    parser.add_argument("--lane", default="tax-delinquent")
    parser.add_argument("--count", type=int, default=500)
    parser.add_argument("--output-dir", default="/tmp")
    args = parser.parse_args()
    src, records = load_records(args.market, args.lane)
    records.sort(key=lambda r: (-float(r["Total Owed"]), -float(r["Estimated Equity"])))
    top = records[: args.count]
    if not top:
        raise SystemExit(f"No deliverable records built for {args.market}/{args.lane} from {src}")
    summary = add_analytics(top, args.market, args.lane, src)
    outputs = write_outputs(top, summary, Path(args.output_dir), args.count)
    print(json.dumps({"ok": True, **summary, **outputs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
