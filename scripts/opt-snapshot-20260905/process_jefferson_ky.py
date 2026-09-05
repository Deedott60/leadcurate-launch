#!/usr/bin/env python3
"""
LeadCurate — Louisville KY (Jefferson County) Property Foreclosures Discovery Snapshot.
Premium pre-foreclosure lane: active court cases with Action_Filed, Sale_Date, Sale_Price.
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
SRC = Path(f"/opt/leadcurate/raw_imports/jefferson-ky/property-foreclosures.csv")
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
    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s.split(".")[0], fmt).date()
        except ValueError:
            continue
    return None


def money(s):
    if s is None:
        return 0.0
    s = clean(s).replace("$", "").replace(",", "")
    if s == "" or s.lower() in ("null", "none", "nan"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def redact_name(name):
    if not name:
        return "[REDACTED]"
    parts = name.strip().split()
    return " ".join(p[0] + "*" * max(2, len(p) - 1) if len(p) > 1 else p for p in parts)


all_rows = []
with open(SRC, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        all_rows.append(row)

print(f"=== Processing {SRC} ===")
print(f"  total source rows: {len(all_rows):,}")

today = datetime.now(timezone.utc).date()

# Build property address from components
def build_address(r):
    parts = [
        clean(r.get("House_Nr")),
        clean(r.get("Dir")),
        clean(r.get("Street_Name")),
        clean(r.get("St_Type")),
        clean(r.get("Post_Dir")),
    ]
    return " ".join(p for p in parts if p)


# Filter and score
filtered = []
for r in all_rows:
    addr = build_address(r)
    sale_date = parse_date(r.get("Sale_Date"))
    action_filed = parse_date(r.get("Action_Filed"))
    sale_price = money(r.get("Sale_Price"))
    if not addr:
        continue
    # Keep records where sale date is in future (upcoming) OR within last 90 days (recent)
    if sale_date:
        days_to_sale = (sale_date - today).days
        if days_to_sale < -90:
            # too old to be useful as pre-foreclosure
            continue
        r["_days_to_sale"] = days_to_sale
    else:
        r["_days_to_sale"] = 999
    r["_property_address"] = addr
    r["_sale_price"] = sale_price
    filtered.append(r)

print(f"  active/recent pre-foreclosure rows: {len(filtered):,}")


def score(r):
    """Higher score = higher urgency (closer sale date) + meaningful price."""
    days = r.get("_days_to_sale", 999)
    price = r.get("_sale_price", 0)
    # Urgency: closer = higher score
    if days >= 0:
        urgency_pts = max(0, 60 - days)  # within 60 days = full score
    else:
        urgency_pts = max(0, 40 + days)  # recent past sales fall off
    # Price component
    price_pts = min(40, price / 5000.0)  # $200k = 40 pts
    return round(urgency_pts + price_pts, 2)


for r in filtered:
    r["_score"] = score(r)

filtered.sort(key=lambda r: r["_score"], reverse=True)
top = filtered[:TOP_N]

print(f"  top {min(TOP_N, len(top))} by score, range: {top[-1]['_score']:.1f}-{top[0]['_score']:.1f}")

snapshot_cols = [
    "rank", "score", "property_address", "zip", "neighborhood", "land_size_code",
    "council_district", "census_tract", "case_number", "case_style",
    "action_filed_date", "sale_date", "days_to_sale", "sale_price", "purchaser",
    "parcel_id", "lane", "county", "state", "source_url", "source_date",
]

def to_out_row(rank, r):
    return {
        "rank": rank,
        "score": r["_score"],
        "property_address": r["_property_address"],
        "zip": clean(r.get("Zip")),
        "neighborhood": clean(r.get("Neighborhood")),
        "land_size_code": clean(r.get("L_S")),
        "council_district": clean(r.get("CD")),
        "census_tract": clean(r.get("Census_Tract")),
        "case_number": clean(r.get("Case_")),
        "case_style": clean(r.get("Case_Style")),
        "action_filed_date": clean(r.get("Action_Filed")),
        "sale_date": clean(r.get("Sale_Date")),
        "days_to_sale": r.get("_days_to_sale"),
        "sale_price": clean(r.get("Sale_Price")),
        "purchaser": clean(r.get("Purchaser")),
        "parcel_id": clean(r.get("Full_Parcel_ID")),
        "lane": LANE,
        "county": COUNTY,
        "state": STATE,
        "source_url": SOURCE_URL,
        "source_date": DATE,
    }


snapshot_path = OUT_DIR / f"jefferson-ky-pre-foreclosure-{DATE}.csv"
with open(snapshot_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=snapshot_cols)
    w.writeheader()
    for i, r in enumerate(top, 1):
        w.writerow(to_out_row(i, r))
print(f"  wrote snapshot: {snapshot_path}")

# Preview (case style + property already public records — keep visible)
preview_path = OUT_DIR / f"jefferson-ky-pre-foreclosure-{DATE}-preview.csv"
preview_cols = [
    "rank", "score", "neighborhood", "zip", "council_district",
    "days_to_sale", "sale_price", "case_status", "lane", "county",
]
with open(preview_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=preview_cols)
    w.writeheader()
    for i, r in enumerate(top[:PREVIEW_N], 1):
        days = r.get("_days_to_sale", 999)
        status = "upcoming" if days >= 0 else "recent"
        w.writerow({
            "rank": i,
            "score": r["_score"],
            "neighborhood": clean(r.get("Neighborhood")),
            "zip": clean(r.get("Zip")),
            "council_district": clean(r.get("CD")),
            "days_to_sale": days,
            "sale_price": clean(r.get("Sale_Price")),
            "case_status": status,
            "lane": LANE,
            "county": COUNTY,
        })
print(f"  wrote preview: {preview_path}")

# Metadata
upcoming = sum(1 for r in top if r.get("_days_to_sale", 999) >= 0)
recent = sum(1 for r in top if -90 <= r.get("_days_to_sale", 999) < 0)
total_sale = sum(r.get("_sale_price", 0) for r in top)

meta = {
    "product_name": "Louisville KY (Jefferson County) Pre-Foreclosure Snapshot",
    "lane": LANE,
    "county": COUNTY,
    "state": STATE,
    "source_url": SOURCE_URL,
    "source_pulled_at": DATE,
    "source_total_rows": len(all_rows),
    "active_universe": len(filtered),
    "delivered_rows": len(top),
    "score_range": [round(top[-1]["_score"], 2), round(top[0]["_score"], 2)],
    "upcoming_sale_count": upcoming,
    "recent_sale_count": recent,
    "total_sale_aggregate": round(total_sale, 2),
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
