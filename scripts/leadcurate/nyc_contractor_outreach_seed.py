#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path


SOURCE_URL = "https://data.cityofnewyork.us/resource/9hiw-49pz.json"
SAMPLE_URL = "https://leadcurate.com/sample-deliveries/nyc-code-violations-2026-07-06/"
TRADE_RE = re.compile(
    r"GENERAL CONTRACTOR|FIRE SUPPRESSION|OIL BURNER|MASTER PLUMBER|RIGGER|WELDER|ELEVATOR|SPECIAL INSPECTION|CONCRETE",
    re.I,
)


def trade_for(license_type: str) -> str:
    if re.search(r"OIL BURNER|MASTER PLUMBER|BOILER", license_type, re.I):
        return "boiler/mechanical"
    if re.search(r"RIGGER|WELDER|CONCRETE", license_type, re.I):
        return "facade/masonry"
    return "restoration/general"


def fetch(limit: int) -> list[dict[str, str]]:
    query = urllib.parse.urlencode({"$limit": limit, "license_status": "ACTIVE"})
    req = urllib.request.Request(f"{SOURCE_URL}?{query}", headers={"Accept": "application/json", "User-Agent": "LeadCurate manual outreach queue/1.0"})
    with urllib.request.urlopen(req, timeout=60) as res:
        return json.loads(res.read().decode("utf-8"))


def normalize(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, str]] = []
    for row in rows:
        license_type = (row.get("license_type") or "").strip()
        email = (row.get("business_email") or "").strip().lower()
        if not email or not TRADE_RE.search(license_type):
            continue
        key = (email, "nyc_code_violations")
        if key in seen:
            continue
        seen.add(key)
        contact = " ".join(part for part in [(row.get("first_name") or "").strip(), (row.get("last_name") or "").strip()] if part)
        firm = (row.get("business_name") or contact or "").strip()
        out.append({
            "source": "nyc_dob_active_licenses",
            "lane": "nyc_code_violations",
            "firm_name": firm,
            "contact_name": contact,
            "email": email,
            "phone": (row.get("business_phone_number") or "").strip(),
            "license_type": license_type,
            "license_number": (row.get("license_number") or "").strip(),
            "business_city": (row.get("license_business_city") or "").strip(),
            "business_state": (row.get("business_state") or "").strip(),
            "business_zip": (row.get("business_zip_code") or "").strip(),
            "trade": trade_for(license_type),
            "territory": "NYC",
            "sample_url": SAMPLE_URL,
            "status": "queued",
        })
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual seed file for NYC contractor outreach queue.")
    parser.add_argument("--limit", type=int, default=50000)
    parser.add_argument("--out", default="/opt/leadcurate/processed/nyc/2026-07-07/nyc-contractor-outreach-queue-seed.csv")
    args = parser.parse_args()

    rows = normalize(fetch(args.limit))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "source", "lane", "firm_name", "contact_name", "email", "phone", "license_type",
        "license_number", "business_city", "business_state", "business_zip", "trade",
        "territory", "sample_url", "status",
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"source_url": SOURCE_URL, "queued_candidates": len(rows), "output": str(out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
