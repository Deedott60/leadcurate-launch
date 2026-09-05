#!/usr/bin/env python3
"""
Memphis (Shelby County) tax-sale snapshot.
Source has parcel + address + sale code + GIS lookup URL — no owner names.
Position as entry-tier product. Buyer uses GIS URL for owner lookup.
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
SRC = Path(f"/opt/leadcurate/raw_imports/shelby-tn/{DATE}/tax-sale-extract.csv")
OUT_DIR = Path(f"/opt/leadcurate/processed/shelby-tn/{DATE}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LANE = "tax_sale_upcoming"
COUNTY = "Shelby"
STATE = "TN"
SOURCE_URL = "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv"
TOP_N = 200
PREVIEW_N = 25

def clean(s):
    return " ".join(str(s or "").split())

all_rows = []
with open(SRC, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        all_rows.append(row)

print(f"=== Processing {SRC} ===")
print(f"  total source rows: {len(all_rows):,}")

# Tax sale codes — TS2302 is more recent than TS2301 in this batch
sale_codes = {}
for r in all_rows:
    c = clean(r.get("Tax Sale"))
    sale_codes[c] = sale_codes.get(c, 0) + 1
print(f"  tax sale codes: {sale_codes}")

# Build property address from street number + street name
filtered = []
for r in all_rows:
    parcel = clean(r.get("ParcelID"))
    alt = clean(r.get("Alt_Parcel"))
    street_no = clean(r.get("Street Number"))
    street = clean(r.get("Street Name"))
    sale = clean(r.get("Tax Sale"))
    gis_url = clean(r.get("Register GIS"))
    if not parcel or not street:
        continue
    if street_no == "0":
        street_no = ""
    full_addr = f"{street_no} {street}".strip()
    r["_parcel"] = parcel
    r["_alt_parcel"] = alt
    r["_address"] = full_addr
    r["_sale_code"] = sale
    r["_gis_url"] = gis_url
    filtered.append(r)

print(f"  filtered (valid parcel + street): {len(filtered):,}")

# Score: prioritize most recent tax sale code, then properties with address numbers (not vacant land lots)
def score(r):
    pts = 0
    # Most recent code = highest priority
    sale = r["_sale_code"]
    if sale == "TS2302":
        pts += 60
    elif sale == "TS2301":
        pts += 40
    else:
        pts += 20
    # Has a street number (built parcel) = more sellable
    if r["_address"].split()[0].isdigit() and r["_address"].split()[0] != "0":
        pts += 30
    # Lookup URL present
    if r["_gis_url"].startswith("http"):
        pts += 10
    return pts

for r in filtered:
    r["_score"] = score(r)

filtered.sort(key=lambda r: (-r["_score"], r["_parcel"]))
top = filtered[:TOP_N]

print(f"  top {len(top)} by score, range: {top[-1]['_score']}-{top[0]['_score']}")

snapshot_cols = [
    "rank", "score", "property_address", "parcel_id", "alt_parcel_id",
    "tax_sale_code", "gis_lookup_url", "lane", "county", "state",
    "source_url", "source_date",
]

snapshot_path = OUT_DIR / f"shelby-tn-tax-sale-{DATE}.csv"
with open(snapshot_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=snapshot_cols)
    w.writeheader()
    for i, r in enumerate(top, 1):
        w.writerow({
            "rank": i,
            "score": r["_score"],
            "property_address": r["_address"],
            "parcel_id": r["_parcel"],
            "alt_parcel_id": r["_alt_parcel"],
            "tax_sale_code": r["_sale_code"],
            "gis_lookup_url": r["_gis_url"],
            "lane": LANE,
            "county": COUNTY,
            "state": STATE,
            "source_url": SOURCE_URL,
            "source_date": DATE,
        })
print(f"  wrote snapshot: {snapshot_path}")

preview_path = OUT_DIR / f"shelby-tn-tax-sale-{DATE}-preview.csv"
preview_cols = ["rank", "score", "property_address_partial", "tax_sale_code", "lane", "county"]
with open(preview_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=preview_cols)
    w.writeheader()
    for i, r in enumerate(top[:PREVIEW_N], 1):
        # Partial-mask address for preview
        addr = r["_address"]
        masked = addr
        parts = addr.split()
        if len(parts) >= 2 and parts[0].isdigit():
            masked = parts[0][0] + "***" + " " + " ".join(parts[1:])
        w.writerow({
            "rank": i,
            "score": r["_score"],
            "property_address_partial": masked,
            "tax_sale_code": r["_sale_code"],
            "lane": LANE,
            "county": COUNTY,
        })
print(f"  wrote preview: {preview_path}")

meta = {
    "product_name": "Memphis (Shelby County) Tax Sale Snapshot",
    "lane": LANE,
    "county": COUNTY,
    "state": STATE,
    "source_url": SOURCE_URL,
    "source_pulled_at": DATE,
    "source_total_rows": len(all_rows),
    "filtered_universe": len(filtered),
    "delivered_rows": len(top),
    "tax_sale_breakdown": sale_codes,
    "score_range": [top[-1]["_score"], top[0]["_score"]],
    "data_includes": ["parcel_id", "alt_parcel_id", "property_address", "tax_sale_code", "gis_lookup_url"],
    "data_excludes": ["owner_name", "owner_mailing", "delinquent_amount", "skip_trace_phone", "DNC_status"],
    "pricing_tier_suggested": "$39-59 entry — buyer uses gis_lookup_url for owner enrichment",
    "compliance_note": "Public-record Trustee data. Property + parcel only. Owner contact, skip trace, and DNC compliance are buyer responsibility.",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
}
meta_path = OUT_DIR / f"shelby-tn-tax-sale-{DATE}-meta.json"
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"  wrote metadata: {meta_path}")
print()
print("=== SNAPSHOT SUMMARY ===")
print(json.dumps(meta, indent=2))
