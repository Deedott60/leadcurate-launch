#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


def clean(value: object) -> str:
    return str(value or "").strip()


def number(value: object) -> int | float:
    text = clean(value).replace("$", "").replace(",", "")
    if not text:
        return 0
    try:
        parsed = float(text)
    except ValueError:
        return 0
    return int(parsed) if parsed.is_integer() else parsed


def money(value: object) -> str:
    return f"${int(round(float(number(value)))):,}"


def redact_address(value: str) -> str:
    parts = value.split()
    if parts and parts[0].isdigit():
        parts[0] = "###"
    return " ".join(parts)


def choose_csv(meta: dict[str, Any], mode: str) -> Path:
    outputs = meta.get("outputs") or {}
    key = "preview" if mode == "sample" else "full"
    path = outputs.get(key) or outputs.get("full")
    if not path:
        raise SystemExit(f"meta.outputs.{key} or meta.outputs.full is required")
    return Path(path)


def sample_rows(path: Path, limit: int, redact: bool) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        for row in csv.DictReader(handle):
            address = clean(row.get("property_address") or row.get("address"))
            rows.append(
                {
                    "owner": clean(row.get("owner_name") or row.get("owner")),
                    "address": redact_address(address) if redact else address,
                    "land_value": number(row.get("land_value")),
                    "value": number(row.get("total_value") or row.get("value")),
                    "acreage": number(row.get("total_acreage") or row.get("acreage")),
                    "years": clean(row.get("years_owned") or row.get("years")),
                    "is_absentee_owner": clean(row.get("is_absentee_owner")),
                    "lane": clean(row.get("lane")),
                    "status": clean(row.get("status")),
                    "vacant_signal": clean(row.get("vacant_signal")),
                }
            )
            if len(rows) >= limit:
                break
    return rows


def default_audit_url(meta: dict[str, Any]) -> str:
    market = clean(meta.get("market"))
    processed = clean(meta.get("processed_date"))
    if market == "hamilton-tn" and processed == "2026-07-08":
        return "https://leadcurate.com/sample-deliveries/chattanooga-verified-vacant-2026-07-08/"
    return ""


def payload(meta: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    mode = args.mode
    csv_path = Path(args.csv) if args.csv else choose_csv(meta, mode)
    sample = sample_rows(csv_path, args.sample_limit, mode == "sample")
    market = args.market or clean(meta.get("market"))
    lane = args.lane or clean(meta.get("lane"))
    total = number(meta.get("verified_vacant") or meta.get("exported") or meta.get("total_records") or meta.get("total_source_rows"))
    absentee = number(meta.get("absentee"))
    result: dict[str, Any] = {
        "mode": mode,
        "to": args.to,
        "name": args.name,
        "market": args.display_market or market,
        "lane": lane,
        "total": total,
        "absentee": absentee,
        "median_land_value": number(meta.get("median_land_value")),
        "sample": sample,
        "numbers": [
            ["Total records", f"{int(total):,}"],
            ["Absentee owners", f"{int(absentee):,}"],
            ["Median land value", money(meta.get("median_land_value"))],
            ["Median acreage", clean(meta.get("median_acreage"))],
        ],
        "hero_cards": [
            ["Records", f"{int(total):,}"],
            ["Absentee", f"{int(absentee):,}"],
            ["Median land", money(meta.get("median_land_value"))],
        ],
        "source_meta": str(args.meta),
        "source_csv": str(csv_path),
    }
    if meta.get("avg_years_owned") not in ("", None):
        result["numbers"].append(["Average years owned", clean(meta.get("avg_years_owned"))])
    audit_url = args.audit_url if args.audit_url is not None else default_audit_url(meta)
    if audit_url:
        result["audit_url"] = audit_url
    if args.list_url:
        result["list_url"] = args.list_url
    if args.filename:
        result["filename"] = args.filename
    if args.summary:
        result["summary"] = args.summary
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a send-delivery JSON payload from a LeadCurate meta.json file.")
    parser.add_argument("--meta", required=True, type=Path)
    parser.add_argument("--mode", choices=["sample", "delivery"], default="sample")
    parser.add_argument("--to", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--market")
    parser.add_argument("--display-market")
    parser.add_argument("--lane")
    parser.add_argument("--csv")
    parser.add_argument("--sample-limit", type=int, default=5)
    parser.add_argument("--audit-url", default=None)
    parser.add_argument("--list-url")
    parser.add_argument("--filename")
    parser.add_argument("--summary")
    args = parser.parse_args()
    meta = json.loads(args.meta.read_text(encoding="utf-8"))
    print(json.dumps(payload(meta, args), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
