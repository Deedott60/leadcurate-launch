#!/usr/bin/env python3
"""
Mecklenburg NC (Charlotte) — multi-category Discovery Snapshot showcase.
Produces 3 distinct lanes from one county:
  1) Open City Liens         (24k source -> 100 ranked)
  2) Vacant Land Specialty   (23k source -> 100 ranked)
  3) High-Value Absentee     (632k source -> 100 ranked)
"""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
RAW = Path("/opt/leadcurate/raw_imports/mecklenburg-nc")
OUT = Path(f"/opt/leadcurate/processed/mecklenburg-nc/{DATE}")
OUT.mkdir(parents=True, exist_ok=True)

COUNTY, STATE = "Mecklenburg", "NC"
TOP = 100

# Allow large fields (parcel-lookup has long Legal_Description strings)
csv.field_size_limit(2**31 - 1)


def clean(s):
    return " ".join(str(s or "").split())


def money(s):
    s = clean(s).replace("$", "").replace(",", "")
    if not s or s.lower() in ("null", "none", "nan"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def redact(name):
    if not name:
        return "[REDACTED]"
    parts = name.split()
    return " ".join(p[0] + "*" * max(2, len(p) - 1) if len(p) > 1 else p for p in parts)


def write_artifacts(slug, lane, source_url, rows, full_cols, preview_cols, preview_map, extras_meta):
    csv_path = OUT / f"{slug}-{DATE}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=full_cols)
        w.writeheader()
        for i, r in enumerate(rows, 1):
            w.writerow({k: r.get(k, "") for k in full_cols})
    preview_path = OUT / f"{slug}-{DATE}-preview.csv"
    with open(preview_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=preview_cols)
        w.writeheader()
        for i, r in enumerate(rows[:25], 1):
            w.writerow(preview_map(i, r))
    meta = {
        "product_name": extras_meta["product_name"],
        "lane": lane,
        "county": COUNTY,
        "state": STATE,
        "source_url": source_url,
        "source_pulled_at": DATE,
        "delivered_rows": len(rows),
        "compliance_note": (
            "Property-record data only. Buyer is responsible for owner contact lookup, "
            "skip trace, DNC compliance, TCPA, and outreach decisions."
        ),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        **{k: v for k, v in extras_meta.items() if k != "product_name"},
    }
    meta_path = OUT / f"{slug}-{DATE}-meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  -> {csv_path.name}  ({len(rows)} rows)")
    return csv_path, preview_path, meta_path, meta


# ---------------- LANE 1: OPEN CITY LIENS ----------------
print("=== Lane 1: Open City Liens ===")
lien_src = RAW / "lien-data.csv"
all_liens = []
with open(lien_src, newline="", encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    for row in r:
        status = clean(row.get("Lien_Status", "")).upper()
        if "PAID" in status:
            continue
        owner = clean(row.get("Customer_Name", ""))
        addr = clean(row.get("Property_Address", ""))
        if not owner or not addr:
            continue
        try:
            inv = datetime.strptime(clean(row.get("Invoice_Date", "")), "%m-%d-%Y").date()
        except ValueError:
            inv = None
        all_liens.append({
            "lien_no": clean(row.get("LienNo")),
            "lien_status": status,
            "owner_name": owner,
            "property_address": addr,
            "invoice_no": clean(row.get("InvoiceNo")),
            "invoice_date": inv.isoformat() if inv else "",
            "_inv": inv,
        })

print(f"  open-lien candidates: {len(all_liens):,}")
status_counts = {}
for r in all_liens:
    status_counts[r["lien_status"]] = status_counts.get(r["lien_status"], 0) + 1

# Score: prefer newer invoices, status weighting
STATUS_WEIGHT = {
    "LF - LIEN FILED": 100,
    "LU - LIEN UPDATED": 80,
    "LO - LIEN OPEN": 90,
    "LP - LIEN PAID": 0,
}
today = datetime.now(timezone.utc).date()
for r in all_liens:
    base = STATUS_WEIGHT.get(r["lien_status"], 50)
    age = (today - r["_inv"]).days if r["_inv"] else 9999
    fresh = max(0, 60 - max(0, age) / 30)  # ~5pt/mo decay
    r["_score"] = round(base + fresh, 2)

all_liens.sort(key=lambda r: r["_score"], reverse=True)
top_liens = all_liens[:TOP]

write_artifacts(
    slug="mecklenburg-nc-open-city-liens",
    lane="city_lien_active",
    source_url="https://data.charlottenc.gov/datasets/financial-management-system-lien-data",
    rows=[{
        "rank": i,
        "score": r["_score"],
        "owner_name": r["owner_name"],
        "property_address": r["property_address"],
        "lien_no": r["lien_no"],
        "lien_status": r["lien_status"],
        "invoice_no": r["invoice_no"],
        "invoice_date": r["invoice_date"],
        "lane": "city_lien_active",
        "county": COUNTY,
        "state": STATE,
    } for i, r in enumerate(top_liens, 1)],
    full_cols=["rank", "score", "owner_name", "property_address", "lien_no",
               "lien_status", "invoice_no", "invoice_date", "lane", "county", "state"],
    preview_cols=["rank", "score", "owner_name_redacted", "property_address_partial",
                  "lien_status", "invoice_date", "lane", "county"],
    preview_map=lambda i, r: {
        "rank": i,
        "score": r["score"],
        "owner_name_redacted": redact(r["owner_name"]),
        "property_address_partial": r["property_address"].split()[0][0] + "*** "
                                    + " ".join(r["property_address"].split()[1:]) if r["property_address"].split() else "[REDACTED]",
        "lien_status": r["lien_status"],
        "invoice_date": r["invoice_date"],
        "lane": "city_lien_active",
        "county": COUNTY,
    },
    extras_meta={
        "product_name": "Charlotte Open City Liens Snapshot",
        "source_total_rows": len(all_liens) + status_counts.get("LP - LIEN PAID", 0),
        "open_lien_universe": len(all_liens),
        "lien_status_breakdown": dict(sorted(status_counts.items(), key=lambda kv: -kv[1])),
        "score_range": [round(top_liens[-1]["_score"], 2), round(top_liens[0]["_score"], 2)],
    },
)

# ---------------- LANE 2: VACANT LAND SPECIALTY ----------------
print()
print("=== Lane 2: Vacant Land Specialty ===")
vac_src = RAW / "vacant-land.csv"
all_vacant = []
with open(vac_src, newline="", encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    for row in r:
        ac = money(row.get("totalac", 0))
        last = clean(row.get("ownerlastname", ""))
        first = clean(row.get("ownerfirstname", ""))
        mail_city = clean(row.get("city", "")).upper()
        mail_state = clean(row.get("state", "")).upper()
        total_val = money(row.get("totalvalue", 0))
        land_val = money(row.get("landvalue", 0))
        if ac < 0.10:
            continue  # tiny remnant lots
        if not last and not first:
            continue
        owner = f"{first} {last}".strip()
        # Absentee bonus
        is_absentee = mail_state and mail_state != "NC"
        # build property addr
        addr_parts = [
            clean(row.get("houseno")),
            clean(row.get("stdir")),
            clean(row.get("stname")),
            clean(row.get("sttype")),
        ]
        prop_addr = " ".join(p for p in addr_parts if p)
        all_vacant.append({
            "_score": 0,
            "owner_name": owner,
            "property_address": prop_addr,
            "municipality": clean(row.get("municipality")),
            "mail_city": mail_city,
            "mail_state": mail_state,
            "total_acreage": ac,
            "land_value": land_val,
            "total_value": total_val,
            "parcel_pid": clean(row.get("pid")),
            "is_absentee": is_absentee,
        })

print(f"  vacant-land candidates: {len(all_vacant):,}")

# Score: bigger acreage + higher value + absentee bonus
for r in all_vacant:
    pts = min(40, r["total_acreage"] * 8) + min(40, r["land_value"] / 5000)
    if r["is_absentee"]:
        pts += 20
    r["_score"] = round(pts, 2)

all_vacant.sort(key=lambda r: r["_score"], reverse=True)
top_vacant = all_vacant[:TOP]

write_artifacts(
    slug="mecklenburg-nc-vacant-land-specialty",
    lane="vacant_land",
    source_url="https://data.charlottenc.gov/datasets/vacant-land",
    rows=[{
        "rank": i,
        "score": r["_score"],
        "owner_name": r["owner_name"],
        "property_address": r["property_address"],
        "municipality": r["municipality"],
        "mail_city": r["mail_city"],
        "mail_state": r["mail_state"],
        "total_acreage": round(r["total_acreage"], 4),
        "land_value": round(r["land_value"], 2),
        "total_value": round(r["total_value"], 2),
        "is_absentee_owner": "yes" if r["is_absentee"] else "no",
        "parcel_pid": r["parcel_pid"],
        "lane": "vacant_land",
        "county": COUNTY,
        "state": STATE,
    } for i, r in enumerate(top_vacant, 1)],
    full_cols=["rank", "score", "owner_name", "property_address", "municipality",
               "mail_city", "mail_state", "total_acreage", "land_value", "total_value",
               "is_absentee_owner", "parcel_pid", "lane", "county", "state"],
    preview_cols=["rank", "score", "owner_name_redacted", "municipality", "mail_state",
                  "total_acreage", "land_value", "is_absentee_owner", "lane", "county"],
    preview_map=lambda i, r: {
        "rank": i,
        "score": r["score"],
        "owner_name_redacted": redact(r["owner_name"]),
        "municipality": r["municipality"],
        "mail_state": r["mail_state"],
        "total_acreage": round(r["total_acreage"], 3),
        "land_value": round(r["land_value"], 2),
        "is_absentee_owner": r["is_absentee_owner"],
        "lane": "vacant_land",
        "county": COUNTY,
    },
    extras_meta={
        "product_name": "Charlotte Vacant Land Specialty Snapshot",
        "source_total_rows": 23204,
        "filtered_universe": len(all_vacant),
        "absentee_in_top": sum(1 for r in top_vacant if r["is_absentee"]),
        "score_range": [round(top_vacant[-1]["_score"], 2), round(top_vacant[0]["_score"], 2)],
    },
)

# ---------------- LANE 3: HIGH-VALUE ABSENTEE (streaming the 632k parcel file) ----------------
print()
print("=== Lane 3: High-Value Absentee (streamed) ===")
parc_src = RAW / "parcel-lookup.csv"
total_rows = 0
candidates = []
THRESH = 200000  # property total_value > $200k
with open(parc_src, newline="", encoding="utf-8-sig") as f:
    r = csv.DictReader(f)
    for row in r:
        total_rows += 1
        prop_use = clean(row.get("Property_Use", "")).lower()
        # residential signal
        if "single" not in prop_use and "townhouse" not in prop_use and "condo" not in prop_use:
            continue
        total_val = money(row.get("Total_Value", 0))
        if total_val < THRESH:
            continue
        owner_first = clean(row.get("Owner_FirstName", ""))
        owner_last = clean(row.get("Owner_LastName", ""))
        owner = f"{owner_first} {owner_last}".strip()
        if not owner:
            continue
        mail_addr = clean(row.get("Mailing_Address", "")).upper()
        mail_city = clean(row.get("City", "")).upper()
        mail_state = clean(row.get("State", "")).upper()
        prop_location = clean(row.get("Location", "")).upper()
        # Absentee = mailing address NOT in NC OR not in same city as property
        if not mail_state:
            continue
        is_oos = mail_state != "NC"
        is_diff_city = mail_city and "CHARLOTTE" not in mail_city and "CHARLOTTE" in prop_location
        if not (is_oos or is_diff_city):
            continue
        bldg_val = money(row.get("Building_Value", 0))
        land_val = money(row.get("Land_Value", 0))
        year_built = clean(row.get("Year_Built", ""))
        try:
            yb = int(year_built) if year_built else 0
        except ValueError:
            yb = 0
        sqft = money(row.get("Heated_Sqft", 0))
        candidates.append({
            "owner_name": owner,
            "mailing_address": clean(row.get("Mailing_Address")),
            "mail_city": mail_city,
            "mail_state": mail_state,
            "mail_zip": clean(row.get("Zip_Code")),
            "property_location": clean(row.get("Location")),
            "property_use": clean(row.get("Property_Use")),
            "year_built": yb,
            "heated_sqft": int(sqft) if sqft else 0,
            "land_value": land_val,
            "building_value": bldg_val,
            "total_value": total_val,
            "parcel_pid": clean(row.get("PID")),
            "is_out_of_state": is_oos,
            "property_url": clean(row.get("Property_URL")),
        })

print(f"  scanned {total_rows:,} rows  -> {len(candidates):,} absentee high-value candidates")

# Score: value + out-of-state bonus + older home bonus (motivated rehab candidates)
for r in candidates:
    pts = min(60, r["total_value"] / 10000)
    if r["is_out_of_state"]:
        pts += 25
    if 1900 < r["year_built"] < 1990:
        pts += 15
    r["_score"] = round(pts, 2)

candidates.sort(key=lambda r: r["_score"], reverse=True)
top_abs = candidates[:TOP]

write_artifacts(
    slug="mecklenburg-nc-high-value-absentee",
    lane="absentee_high_value",
    source_url="https://data.charlottenc.gov/datasets/parcel-look-up",
    rows=[{
        "rank": i,
        "score": r["_score"],
        "owner_name": r["owner_name"],
        "mailing_address": r["mailing_address"],
        "mail_city": r["mail_city"],
        "mail_state": r["mail_state"],
        "mail_zip": r["mail_zip"],
        "property_location": r["property_location"],
        "property_use": r["property_use"],
        "year_built": r["year_built"] or "",
        "heated_sqft": r["heated_sqft"] or "",
        "land_value": r["land_value"],
        "building_value": r["building_value"],
        "total_value": r["total_value"],
        "is_out_of_state": "yes" if r["is_out_of_state"] else "no",
        "parcel_pid": r["parcel_pid"],
        "parcel_record_url": r["property_url"],
        "lane": "absentee_high_value",
        "county": COUNTY,
        "state": STATE,
    } for i, r in enumerate(top_abs, 1)],
    full_cols=["rank", "score", "owner_name", "mailing_address", "mail_city",
               "mail_state", "mail_zip", "property_location", "property_use",
               "year_built", "heated_sqft", "land_value", "building_value",
               "total_value", "is_out_of_state", "parcel_pid", "parcel_record_url",
               "lane", "county", "state"],
    preview_cols=["rank", "score", "owner_name_redacted", "mail_city", "mail_state",
                  "property_use", "year_built", "total_value", "is_out_of_state",
                  "lane", "county"],
    preview_map=lambda i, r: {
        "rank": i,
        "score": r["score"],
        "owner_name_redacted": redact(r["owner_name"]),
        "mail_city": r["mail_city"],
        "mail_state": r["mail_state"],
        "property_use": r["property_use"],
        "year_built": r["year_built"] or "",
        "total_value": r["total_value"],
        "is_out_of_state": "yes" if r["is_out_of_state"] else "no",
        "lane": "absentee_high_value",
        "county": COUNTY,
    },
    extras_meta={
        "product_name": "Charlotte High-Value Absentee Snapshot",
        "source_total_rows": total_rows,
        "filtered_universe": len(candidates),
        "out_of_state_in_top": sum(1 for r in top_abs if r["is_out_of_state"]),
        "score_range": [round(top_abs[-1]["_score"], 2), round(top_abs[0]["_score"], 2)],
    },
)

print()
print("=== DONE ===")
for p in sorted(OUT.iterdir()):
    print(" ", p.stat().st_size, p.name)
