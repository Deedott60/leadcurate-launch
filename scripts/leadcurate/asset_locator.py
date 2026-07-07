#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Iterable


PARCEL_FIELDS = (
    "parcel_id", "parcel_pid", "parcel", "pin", "pid", "reid", "account_id",
    "apn", "tax_parcel_id", "parcel_number",
)
ADDRESS_FIELDS = (
    "property_address", "property_location", "situs_address", "site_address",
    "address", "location", "full_address",
)
OWNER_FIELDS = ("owner_name", "owner", "taxpayer_name", "customer_name", "name")
MAILING_FIELDS = ("owner_mailing_address", "mailing_address", "mail_address", "owner_address")
VALUE_FIELDS = (
    "property_total_value", "total_value", "market_value", "assessed_value",
    "appraised_value", "taxable_value",
)
LIEN_FIELDS = ("lien_no", "lienno", "lien_id", "case_number", "record_id", "invoice_no", "invoiceno")
DATE_FIELDS = ("invoice_date", "filed_date", "recorded_date", "date", "created_date")


def norm_key(value: object) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def norm_addr(value: object) -> str:
    text = str(value or "").upper()
    text = re.sub(r"\b(STREET|ST)\b", "ST", text)
    text = re.sub(r"\b(AVENUE|AVE)\b", "AVE", text)
    text = re.sub(r"\b(ROAD|RD)\b", "RD", text)
    text = re.sub(r"\b(DRIVE|DR)\b", "DR", text)
    text = re.sub(r"\b(BOULEVARD|BLVD)\b", "BLVD", text)
    return re.sub(r"[^A-Z0-9]", "", text)


def first(row: dict[str, str], names: Iterable[str]) -> str:
    lower = {k.lower(): k for k in row}
    for name in names:
        key = lower.get(name.lower())
        if key and str(row.get(key, "")).strip():
            return str(row.get(key, "")).strip()
    return ""


def owner_name(row: dict[str, str]) -> str:
    direct = first(row, OWNER_FIELDS)
    if direct:
        return direct
    first_name = first(row, ("owner_firstname", "owner_first_name"))
    last_name = first(row, ("owner_lastname", "owner_last_name"))
    return " ".join(part for part in (first_name, last_name) if part).strip()


def number(value: object) -> float:
    text = str(value or "").replace("$", "").replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        return list(csv.DictReader(f))


def parcel_indexes(rows: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    by_parcel: dict[str, dict[str, str]] = {}
    by_address: dict[str, dict[str, str]] = {}
    for row in rows:
        parcel = norm_key(first(row, PARCEL_FIELDS))
        address = norm_addr(first(row, ADDRESS_FIELDS))
        if parcel and parcel not in by_parcel:
            by_parcel[parcel] = row
        if address and address not in by_address:
            by_address[address] = row
    return by_parcel, by_address


def classify_owner(owner: str) -> str:
    if re.search(r"\b(LLC|INC|CORP|COMPANY|CO\.|TRUST|LP|LLP|HOLDINGS|INVESTMENTS|PROPERTIES)\b", owner, re.I):
        return "entity"
    return "individual" if owner else ""


def score(lien: dict[str, str], parcel: dict[str, str] | None, match_method: str) -> int:
    value = number(first(parcel or {}, VALUE_FIELDS))
    base = 60 if match_method == "parcel" else 45 if match_method == "address" else 20
    value_bonus = min(25, int(value // 100000)) if value else 0
    lien_bonus = 10 if first(lien, LIEN_FIELDS) else 0
    return base + value_bonus + lien_bonus


def redact_name(value: str) -> str:
    return " ".join((part[:1] + "***") if part else "" for part in value.split())


def redact_address(value: str) -> str:
    return re.sub(r"\b\d{1,6}\b", lambda m: m.group(0)[:1] + "***", value, count=1)


def merge_rows(market: str, lien_rows: list[dict[str, str]], parcel_rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], Counter]:
    by_parcel, by_address = parcel_indexes(parcel_rows)
    stats: Counter = Counter()
    merged: list[dict[str, object]] = []

    for lien in lien_rows:
        parcel_key = norm_key(first(lien, PARCEL_FIELDS))
        address_key = norm_addr(first(lien, ADDRESS_FIELDS))
        parcel = by_parcel.get(parcel_key)
        match_method = "parcel" if parcel else ""
        if not parcel and address_key:
            parcel = by_address.get(address_key)
            match_method = "address" if parcel else ""
        stats[match_method or "unmatched"] += 1

        owner = owner_name(lien) or owner_name(parcel or {})
        address = first(lien, ADDRESS_FIELDS) or first(parcel or {}, ADDRESS_FIELDS)
        mailing = first(lien, MAILING_FIELDS) or first(parcel or {}, MAILING_FIELDS)
        parcel_id = first(lien, PARCEL_FIELDS) or first(parcel or {}, PARCEL_FIELDS)
        total_value = first(lien, VALUE_FIELDS) or first(parcel or {}, VALUE_FIELDS)

        merged.append({
            "market": market,
            "rank": 0,
            "score": score(lien, parcel, match_method),
            "match_method": match_method or "unmatched",
            "parcel_id": parcel_id,
            "owner_name": owner,
            "owner_type": classify_owner(owner),
            "property_address": address,
            "owner_mailing_address": mailing,
            "property_total_value": total_value,
            "lien_id": first(lien, LIEN_FIELDS),
            "lien_date": first(lien, DATE_FIELDS),
            "lien_status": first(lien, ("lien_status", "status", "case_status")),
            "source_lane": first(lien, ("lane", "lead_lane", "source_type")) or "asset_locator",
        })

    merged.sort(key=lambda r: (int(r["score"]), r["match_method"] == "parcel"), reverse=True)
    for idx, row in enumerate(merged, 1):
        row["rank"] = idx
    return merged, stats


def write_csv(path: Path, rows: list[dict[str, object]], preview: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "rank", "score", "match_method", "parcel_id", "owner_name", "owner_type",
        "property_address", "owner_mailing_address", "property_total_value",
        "lien_id", "lien_date", "lien_status", "source_lane", "market",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            if preview:
                out["owner_name"] = redact_name(str(out.get("owner_name") or ""))
                out["property_address"] = redact_address(str(out.get("property_address") or ""))
                out["owner_mailing_address"] = ""
                out["parcel_id"] = "REDACTED" if out.get("parcel_id") else ""
            writer.writerow({k: out.get(k, "") for k in fields})


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-reference lien/debt rows with parcel rows for Asset Locator packages.")
    parser.add_argument("--market", required=True)
    parser.add_argument("--lien-csv", required=True)
    parser.add_argument("--parcel-csv", required=True)
    parser.add_argument("--output-dir")
    parser.add_argument("--top", type=int, default=500)
    args = parser.parse_args()

    lien_path = Path(args.lien_csv)
    parcel_path = Path(args.parcel_csv)
    output_dir = Path(args.output_dir) if args.output_dir else lien_path.parent
    run_date = date.today().isoformat()

    lien_rows = read_csv(lien_path)
    parcel_rows = read_csv(parcel_path)
    rows, stats = merge_rows(args.market, lien_rows, parcel_rows)
    rows = rows[: max(1, args.top)]

    stem = f"{args.market}-asset-locator-{run_date}"
    full_path = output_dir / f"{stem}.csv"
    preview_path = output_dir / f"{stem}-preview.csv"
    meta_path = output_dir / f"{stem}-meta.json"

    write_csv(full_path, rows)
    write_csv(preview_path, rows[:25], preview=True)
    meta = {
        "market": args.market,
        "lane": "asset_locator",
        "lien_source_csv": str(lien_path),
        "parcel_source_csv": str(parcel_path),
        "source_lien_rows": len(lien_rows),
        "source_parcel_rows": len(parcel_rows),
        "exported_rows": len(rows),
        "match_counts": dict(stats),
        "outputs": {
            "full": str(full_path),
            "preview": str(preview_path),
            "meta": str(meta_path),
        },
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
