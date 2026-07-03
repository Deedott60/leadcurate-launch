#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
from datetime import date
from pathlib import Path
from typing import Any
from urllib import request

RAW_ROOT = Path("/opt/leadcurate/raw_imports")
PACKAGE_ROOT = Path("/opt/leadcurate/ground_floor")
SB_URL = os.environ.get("SUPABASE_URL", "https://jdmlsraqioigbukspduo.supabase.co")
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
SB_KEY = SERVICE_ROLE_KEY or os.environ.get("SUPABASE_PUBLISHABLE_KEY") or "sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4"
N8N_API_KEY = os.environ.get("N8N_API_KEY")

SEED_INVESTMENTS = [
    {
        "location": "Durham County, NC",
        "state": "NC",
        "county": "Durham",
        "company": "AbbVie",
        "dollar_amount": 1_400_000_000,
        "dollar_amount_text": "$1.4B",
        "job_count": 734,
        "announcement_date": "2026-04-22",
        "project_stage": "announced",
        "source_url": "https://news.abbvie.com/2026-04-22-AbbVie-Selects-North-Carolina-for-New-1-4-Billion-Manufacturing-Campus",
        "second_source_url": "https://governor.nc.gov/news/press-releases/2026/04/22/governor-stein-announces-abbvie-build-new-14-billion-manufacturing-campus-durham",
        "confidence_level": "high",
        "notes": "Verified from AbbVie release and NC Governor release.",
    },
    {
        "location": "Cherokee County, SC",
        "state": "SC",
        "county": "Cherokee",
        "company": "USA Rare Earth",
        "dollar_amount": 1_200_000_000,
        "dollar_amount_text": "$1.2B",
        "job_count": 490,
        "announcement_date": "2026-06-02",
        "project_stage": "announced",
        "source_url": "https://governor.sc.gov/news/2026-06/usa-rare-earth-inc-selects-cherokee-county-first-south-carolina-operation",
        "second_source_url": "https://scdailygazette.com/2026/06/02/rare-earth-magnet-maker-pledges-1-2b-investment-in-cherokee-county/",
        "confidence_level": "high",
        "notes": "Verified from SC Governor release and SC Daily Gazette.",
    },
    {
        "location": "Guilford County, NC",
        "state": "NC",
        "county": "Guilford",
        "company": "JetZero",
        "dollar_amount": 4_700_000_000,
        "dollar_amount_text": "$4.7B",
        "job_count": 14500,
        "announcement_date": "2026-06-15",
        "project_stage": "groundbreaking",
        "source_url": "https://www.jetzero.aero/jetzero-breaks-ground-on-greensboro-factory",
        "second_source_url": "https://governor.nc.gov/news/press-releases/2025/06/12/governor-stein-announces-jetzero-selects-north-carolina-4-billion-airplane-manufacturing-hub",
        "confidence_level": "high",
        "notes": "Groundbreaking verified from JetZero release; original NC project announcement verifies Guilford County/jobs.",
    },
]

MARKET_TO_INVESTMENT = {
    "guilford-nc": "JetZero",
    "durham-nc": "AbbVie",
    "cherokee-sc": "USA Rare Earth",
}


def postgrest(method: str, table: str, payload: Any, query: str = "") -> tuple[int, str]:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    req = request.Request(f"{SB_URL}/rest/v1/{table}{query}", data=data, headers=headers, method=method)
    with request.urlopen(req, timeout=30) as res:
        return res.status, res.read().decode()


def rpc(name: str, payload: dict[str, Any]) -> tuple[int, str]:
    data = json.dumps(payload).encode()
    headers = {
        "apikey": SB_KEY,
        "Authorization": f"Bearer {SB_KEY}",
        "Content-Type": "application/json",
    }
    req = request.Request(f"{SB_URL}/rest/v1/rpc/{name}", data=data, headers=headers, method="POST")
    with request.urlopen(req, timeout=30) as res:
        return res.status, res.read().decode()


def seed() -> dict[str, Any]:
    if not SERVICE_ROLE_KEY and N8N_API_KEY:
        status, body = rpc("upsert_ground_floor_investments", {"auth_token": N8N_API_KEY, "rows": SEED_INVESTMENTS})
        return {"ok": status in (200, 201), "status": status, "rpc": json.loads(body or "{}")}
    status, body = postgrest("POST", "ground_floor_investments", SEED_INVESTMENTS, "?on_conflict=location,company,announcement_date,source_url")
    return {"ok": status in (200, 201), "status": status, "rows": json.loads(body or "[]")}


def latest_property_file(market: str) -> Path:
    root = RAW_ROOT / market
    if not root.exists():
        raise FileNotFoundError(f"No raw_imports directory for {market}")
    preferred = ["county-parcels.csv", "historical-parcels-2025.csv", "parcel-lookup.csv", "parcels.csv", "property.csv"]
    for pattern in preferred:
        candidates = sorted(root.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            return candidates[0]
    candidates = sorted(root.rglob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"No CSV property file found for {market}")
    return candidates[0]


def summarize_csv(path: Path, sample_size: int = 25) -> dict[str, Any]:
    count = 0
    sample: list[dict[str, str]] = []
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        headers = reader.fieldnames or []
        for row in reader:
            count += 1
            if len(sample) < sample_size:
                sample.append({k: row.get(k, "") for k in headers[:30]})
    return {"path": str(path), "record_count": count, "headers": headers[:80], "sample": sample}


def investment_for_market(market: str) -> dict[str, Any]:
    company = MARKET_TO_INVESTMENT.get(market)
    for item in SEED_INVESTMENTS:
        if item["company"] == company:
            return item
    raise KeyError(f"No investment seed mapped for {market}")


def package_county(market: str) -> dict[str, Any]:
    investment = investment_for_market(market)
    property_file = latest_property_file(market)
    package = {
        "market_slug": market,
        "county": investment["county"],
        "state": investment["state"],
        "investment_snapshot": investment,
        "property_snapshot": summarize_csv(property_file),
        "source_files": [str(property_file)],
        "status": "ready_for_claude_review",
    }
    out_dir = PACKAGE_ROOT / market / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ground-floor-package.json"
    out_path.write_text(json.dumps(package, indent=2), encoding="utf-8")
    package["package_path"] = str(out_path)
    try:
        if not SERVICE_ROLE_KEY and N8N_API_KEY:
            status, body = rpc("insert_ground_floor_county_package", {"auth_token": N8N_API_KEY, "package": package})
        else:
            status, body = postgrest("POST", "ground_floor_county_packages", [package])
        package["supabase_status"] = status
        package["supabase_rows"] = json.loads(body or "[]")
    except Exception as exc:
        package["supabase_error"] = str(exc)
    return {"ok": True, "package": package}


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual Ground Floor investment + parcel package builder.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("seed-investments")
    pkg = sub.add_parser("package-county")
    pkg.add_argument("--market", required=True)
    args = parser.parse_args()
    if args.command == "seed-investments":
        print(json.dumps(seed(), indent=2))
        return 0
    if args.command == "package-county":
        print(json.dumps(package_county(args.market), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
