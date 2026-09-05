#!/usr/bin/env python3
"""
Louisville KY pre-foreclosure snapshot — v2.
Fixed: date parser handles "YYYY/MM/DD HH:MM:SS+TZ" format.
Sale_Price is empty for ALL active cases, so we score on date proximity instead.
"""
import csv
import json
import re
from datetime import datetime, timezone, date
from pathlib import Path

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
SRC = Path("/opt/leadcurate/raw_imports/jefferson-ky/property-foreclosures.csv")
OUT_DIR = Path(f"/opt/leadcurate/processed/jefferson-ky/{DATE}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LANE = "pre_foreclosure"
COUNTY = "Jefferson"
STATE = "KY"
SOURCE_URL = "https://data.louisvilleky.gov/datasets/louisville-metro-ky-property-foreclosures"
TOP_N = 100
PREVIEW_N = 25


def clean(s):
    return str(s or "").strip()


def parse_date(s):
    s = clean(s)
    if not s:
        return None
    # Strip timezone suffix like "+00", "+0000"
    s = re.sub(r"[+-]\d{2}:?\d{0,2}$", "", s).strip()
    for fmt in (
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d",
        "%Y-%m-%d",
        "%m/%d/%Y",
    ):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


all_rows = []
with open(SRC, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        all_rows.append(row)

print(f"=== Processing {SRC} ===")
print(f"  total source rows: {len(all_rows):,}")

today = date.today()


def build_address(r):
    parts = [
        clean(r.get("House_Nr")),
        clean(r.get("Dir")),
        clean(r.get("Street_Name")),
        clean(r.get("St_Type")),
        clean(r.get("Post_Dir")),
    ]
    return " ".join(p for p in parts if p)


# Filter
filtered = []
for r in all_rows:
    addr = build_address(r)
    sale_date = parse_date(r.get("Sale_Date"))
    action_filed = parse_date(r.get("Action_Filed"))
    if not addr:
        continue
    days_to_sale = (sale_date - today).days if sale_date else None
    days_since_filed = (today - action_filed).days if action_filed else None
    # Filter to records with at least one date and reasonable freshness
    if sale_date is None and action_filed is None:
        continue
    # Discard sales more than 1 year in the past
    if days_to_sale is not None and days_to_sale < -365:
        continue
    # Discard cases filed more than 3 years ago that have no future sale
    if action_filed and days_since_filed and days_since_filed > 1095 and (days_to_sale is None or days_to_sale < 0):
        continue
    r["_property_address"] = addr
    r["_sale_date"] = sale_date.isoformat() if sale_date else ""
    r["_days_to_sale"] = days_to_sale if days_to_sale is not None else 9999
    r["_action_filed"] = action_filed.isoformat() if action_filed else ""
    r["_days_since_filed"] = days_since_filed if days_since_filed is not None else 9999
    filtered.append(r)

print(f"  active/recent rows: {len(filtered):,}")


def score(r):
    """High urgency = score high. Future sale closer = better; recently filed = better."""
    pts = 0.0
    d = r.get("_days_to_sale", 9999)
    if d != 9999:
        if d >= 0:
            pts += max(0, 90 - d)  # within 90 days = full credit
        else:
            pts += max(0, 30 + d)  # recent past auctions decay
    # Action filed recency
    a = r.get("_days_since_filed", 9999)
    if a != 9999:
        if 0 <= a <= 180:
            pts += 30 - (a / 6)  # very fresh filing
        elif 180 < a <= 720:
            pts += max(0, 30 - (a - 180) / 18)
    return round(pts, 2)


for r in filtered:
    r["_score"] = score(r)

filtered.sort(key=lambda r: r["_score"], reverse=True)
top = filtered[:TOP_N]
if not top:
    raise SystemExit("no rows survived filtering")

print(f"  top {len(top)} by score, range: {top[-1]['_score']:.1f}-{top[0]['_score']:.1f}")

snapshot_cols = [
    "rank", "score", "property_address", "zip", "neighborhood",
    "council_district", "land_size_code", "action_filed_date", "sale_date",
    "days_to_sale", "days_since_filed", "case_number", "case_style",
    "purchaser_at_sale", "parcel_id", "lane", "county", "state",
    "source_url", "source_date",
]

snapshot_path = OUT_DIR / f"jefferson-ky-pre-foreclosure-{DATE}.csv"
with open(snapshot_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=snapshot_cols)
    w.writeheader()
    for i, r in enumerate(top, 1):
        w.writerow({
            "rank": i,
            "score": r["_score"],
            "property_address": r["_property_address"],
            "zip": clean(r.get("Zip")),
            "neighborhood": clean(r.get("Neighborhood")),
            "council_district": clean(r.get("CD")),
            "land_size_code": clean(r.get("L_S")),
            "action_filed_date": r["_action_filed"],
            "sale_date": r["_sale_date"],
            "days_to_sale": r["_days_to_sale"] if r["_days_to_sale"] != 9999 else "",
            "days_since_filed": r["_days_since_filed"] if r["_days_since_filed"] != 9999 else "",
            "case_number": clean(r.get("Case_")),
            "case_style": clean(r.get("Case_Style")),
            "purchaser_at_sale": clean(r.get("Purchaser")),
            "parcel_id": clean(r.get("Full_Parcel_ID")),
            "lane": LANE,
            "county": COUNTY,
            "state": STATE,
            "source_url": SOURCE_URL,
            "source_date": DATE,
        })
print(f"  wrote snapshot: {snapshot_path}")

preview_path = OUT_DIR / f"jefferson-ky-pre-foreclosure-{DATE}-preview.csv"
preview_cols = ["rank", "score", "neighborhood", "zip", "council_district",
                "days_to_sale", "days_since_filed", "sale_date", "case_status",
                "lane", "county"]
with open(preview_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=preview_cols)
    w.writeheader()
    for i, r in enumerate(top[:PREVIEW_N], 1):
        d = r.get("_days_to_sale", 9999)
        if d == 9999:
            status = "filed_only"
        elif d > 0:
            status = "upcoming"
        elif d == 0:
            status = "today"
        else:
            status = "recent_past"
        w.writerow({
            "rank": i,
            "score": r["_score"],
            "neighborhood": clean(r.get("Neighborhood")),
            "zip": clean(r.get("Zip")),
            "council_district": clean(r.get("CD")),
            "days_to_sale": d if d != 9999 else "",
            "days_since_filed": r["_days_since_filed"] if r["_days_since_filed"] != 9999 else "",
            "sale_date": r["_sale_date"],
            "case_status": status,
            "lane": LANE,
            "county": COUNTY,
        })
print(f"  wrote preview: {preview_path}")

# Metadata
upcoming = sum(1 for r in top if 0 <= r.get("_days_to_sale", 9999) < 9999)
recent_past = sum(1 for r in top if -365 < r.get("_days_to_sale", 9999) < 0)
filed_only = sum(1 for r in top if r.get("_days_to_sale", 9999) == 9999)
neighborhoods = {}
for r in top:
    n = clean(r.get("Neighborhood")) or "(unknown)"
    neighborhoods[n] = neighborhoods.get(n, 0) + 1

meta = {
    "product_name": "Louisville KY (Jefferson County) Pre-Foreclosure Snapshot",
    "lane": LANE,
    "county": COUNTY,
    "state": STATE,
    "source_url": SOURCE_URL,
    "source_pulled_at": DATE,
    "source_total_rows": len(all_rows),
    "filtered_universe": len(filtered),
    "delivered_rows": len(top),
    "score_range": [round(top[-1]["_score"], 2), round(top[0]["_score"], 2)],
    "upcoming_sale_count": upcoming,
    "recent_past_sale_count": recent_past,
    "filed_only_count": filed_only,
    "top_neighborhoods": dict(sorted(neighborhoods.items(), key=lambda kv: -kv[1])[:10]),
    "compliance_note": "Public-record court filings. Property address + case data only. Buyer responsible for owner contact lookup, skip trace, DNC compliance, and outreach.",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
}
meta_path = OUT_DIR / f"jefferson-ky-pre-foreclosure-{DATE}-meta.json"
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"  wrote metadata: {meta_path}")
print()
print("=== SNAPSHOT SUMMARY ===")
print(json.dumps(meta, indent=2))
