#!/usr/bin/env python3
"""
Enrich Mecklenburg city-lien records by cross-referencing the 632k parcel-lookup file.
Adds: property total value, year built, mailing address, mailing state, absentee flag,
property use, building value, land value.
"""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

csv.field_size_limit(2**31 - 1)
RAW = Path("/opt/leadcurate/raw_imports/mecklenburg-nc")
OUT_DIR = Path(f"/opt/leadcurate/processed/mecklenburg-nc/{datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
OUT_DIR.mkdir(parents=True, exist_ok=True)
DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---- Address normalization ----
SUFFIX_MAP = {
    "STREET": "ST", "AVENUE": "AV", "AVE": "AV", "DRIVE": "DR", "ROAD": "RD",
    "BOULEVARD": "BV", "BLVD": "BV", "LANE": "LN", "COURT": "CT", "CIRCLE": "CR",
    "PLACE": "PL", "PARKWAY": "PY", "PKWY": "PY", "TERRACE": "TR",
    "HIGHWAY": "HW", "HWY": "HW", "TRAIL": "TL", "SQUARE": "SQ",
}
DIR_MAP = {"NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W"}


def normalize_addr(s):
    s = (s or "").upper().strip()
    s = re.sub(r"[.,#]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    parts = s.split()
    norm = []
    for p in parts:
        norm.append(DIR_MAP.get(p, SUFFIX_MAP.get(p, p)))
    return " ".join(norm)


def addr_key(s):
    """Best-effort match key: house# + first 2 street words normalized."""
    n = normalize_addr(s)
    if not n:
        return None
    parts = n.split()
    if not parts or not parts[0][0].isdigit():
        return n[:30]  # streets w/o numbers (e.g., "BLUESTEM LN")
    house = parts[0]
    street = " ".join(parts[1:4])  # first ~3 tokens of street name
    return f"{house}|{street}"


# ---- Build parcel index ----
print("Building parcel index from parcel-lookup.csv ...")
parcel_idx = {}
with open(RAW / "parcel-lookup.csv", newline="", encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    n = 0
    for row in r:
        n += 1
        loc = row.get("Location", "").strip()
        if not loc:
            continue
        k = addr_key(loc)
        if not k:
            continue
        if k not in parcel_idx:  # keep first match
            parcel_idx[k] = {
                "total_value": row.get("Total_Value", ""),
                "land_value": row.get("Land_Value", ""),
                "building_value": row.get("Building_Value", ""),
                "year_built": row.get("Year_Built", ""),
                "heated_sqft": row.get("Heated_Sqft", ""),
                "property_use": row.get("Property_Use", ""),
                "mailing_address": row.get("Mailing_Address", ""),
                "mail_city": row.get("City", ""),
                "mail_state": row.get("State", ""),
                "mail_zip": row.get("Zip_Code", ""),
                "parcel_id": row.get("PID", ""),
                "owner_first": row.get("Owner_FirstName", ""),
                "owner_last": row.get("Owner_LastName", ""),
                "property_url": row.get("Property_URL", ""),
            }
        if n % 100000 == 0:
            print(f"  scanned {n:,} parcels, index size {len(parcel_idx):,}")
print(f"  total parcels scanned: {n:,}    index entries: {len(parcel_idx):,}")


def money(s):
    s = str(s or "").replace("$", "").replace(",", "").strip()
    if not s or s.lower() in ("null", "none", "nan"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


# ---- Walk lien file, enrich, score ----
print("\nEnriching lien-data.csv ...")
enriched = []
unmatched = 0
with open(RAW / "lien-data.csv", newline="", encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    for row in r:
        status = (row.get("Lien_Status") or "").upper().strip()
        if "PAID" in status:
            continue
        prop_addr = (row.get("Property_Address") or "").strip()
        owner = (row.get("Customer_Name") or "").strip()
        if not prop_addr or not owner:
            continue
        k = addr_key(prop_addr)
        match = parcel_idx.get(k) if k else None
        if not match:
            unmatched += 1
            continue
        tv = money(match["total_value"])
        mail_state = (match["mail_state"] or "").upper().strip()
        is_oos = bool(mail_state and mail_state != "NC")
        is_diff_city = (match["mail_city"] or "").upper().strip() not in ("CHARLOTTE", "MATTHEWS", "HUNTERSVILLE", "MINT HILL", "PINEVILLE", "DAVIDSON", "CORNELIUS")
        try:
            yb = int(match["year_built"]) if match["year_built"] else 0
        except ValueError:
            yb = 0
        try:
            inv = datetime.strptime(row.get("Invoice_Date", ""), "%m-%d-%Y").date()
        except ValueError:
            inv = None
        # Score: filed status + property value + absentee + age
        pts = 0
        if "FILED" in status:
            pts += 60
        elif "OPEN" in status:
            pts += 50
        else:
            pts += 30
        pts += min(40, tv / 10000.0)  # $400k = 40 pts
        if is_oos:
            pts += 25
        if 1900 < yb < 1990:
            pts += 10
        enriched.append({
            "owner_name": owner,
            "property_address": prop_addr,
            "lien_no": row.get("LienNo", "").strip(),
            "lien_status": status,
            "invoice_no": row.get("InvoiceNo", "").strip(),
            "invoice_date": inv.isoformat() if inv else "",
            "property_total_value": tv,
            "property_land_value": money(match["land_value"]),
            "property_building_value": money(match["building_value"]),
            "year_built": yb if yb else "",
            "heated_sqft": match["heated_sqft"],
            "property_use": match["property_use"],
            "owner_mailing_address": match["mailing_address"],
            "owner_mail_city": match["mail_city"],
            "owner_mail_state": mail_state,
            "owner_mail_zip": match["mail_zip"],
            "is_out_of_state": "yes" if is_oos else "no",
            "parcel_id": match["parcel_id"],
            "parcel_record_url": match["property_url"],
            "_score": round(pts, 2),
        })

print(f"  enriched: {len(enriched):,}    unmatched: {unmatched:,}")

# Sort and take top 100
enriched.sort(key=lambda r: r["_score"], reverse=True)
top = enriched[:100]
print(f"  top 100 score range: {top[-1]['_score']} - {top[0]['_score']}")

# Write enriched CSV
cols = [
    "rank", "score", "owner_name", "property_address",
    "lien_status", "invoice_date", "lien_no",
    "property_total_value", "property_building_value", "property_land_value",
    "year_built", "heated_sqft", "property_use",
    "owner_mailing_address", "owner_mail_city", "owner_mail_state",
    "owner_mail_zip", "is_out_of_state",
    "parcel_id", "parcel_record_url",
    "lane", "county", "state",
]
csv_path = OUT_DIR / f"mecklenburg-nc-enriched-city-liens-{DATE}.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for i, r in enumerate(top, 1):
        w.writerow({
            "rank": i, "score": r["_score"], **{k: r.get(k, "") for k in cols if k not in ("rank", "score", "lane", "county", "state")},
            "lane": "city_lien_active_enriched", "county": "Mecklenburg", "state": "NC",
        })
print(f"  wrote: {csv_path}")

# Stats
oos_count = sum(1 for r in top if r["is_out_of_state"] == "yes")
total_value_sum = sum(r["property_total_value"] for r in top)
print(f"  out-of-state in top 100: {oos_count}")
print(f"  aggregate property value: ${total_value_sum:,.0f}")

meta = {
    "product_name": "Charlotte NC Enriched Open City Liens",
    "lane": "city_lien_active_enriched",
    "county": "Mecklenburg", "state": "NC",
    "source_lien_url": "https://data.charlottenc.gov/datasets/financial-management-system-lien-data",
    "source_parcel_url": "https://data.charlottenc.gov/datasets/parcel-look-up",
    "source_pulled_at": DATE,
    "source_total_rows": 24417,
    "enriched_universe": len(enriched),
    "delivered_rows": len(top),
    "out_of_state_in_top": oos_count,
    "aggregate_property_value": round(total_value_sum, 2),
    "score_range": [top[-1]["_score"], top[0]["_score"]],
    "enrichment_method": "address-key match between Property_Address (lien) and Location (parcel)",
    "compliance_note": "Property-record data only. Buyer responsible for skip trace, DNC, TCPA, outreach.",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
}
(OUT_DIR / f"mecklenburg-nc-enriched-city-liens-{DATE}-meta.json").write_text(json.dumps(meta, indent=2))
print(f"\n=== ENRICHED METADATA ===")
print(json.dumps(meta, indent=2))
