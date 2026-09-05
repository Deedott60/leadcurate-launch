#!/usr/bin/env python3
"""
LeadCurate — Guilford NC Discovery Snapshot generator.
Filters Guilford County tax delinquent records to absentee owners,
scores by amount owed, exports a sellable snapshot.
"""
import csv
import json
import os
from datetime import datetime, timezone
from pathlib import Path

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
SRC = Path(f"/opt/leadcurate/raw_imports/guilford-nc/{DATE}/tax-delinquent-report.csv")
OUT_DIR = Path(f"/opt/leadcurate/processed/guilford-nc/{DATE}")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LANE = "tax_delinquent_absentee"
COUNTY = "Guilford"
STATE = "NC"
SOURCE_URL = "https://open-data-hub-guilfordgis.hub.arcgis.com/datasets/cd3e1ae082b0406aa12ca6bbfbe1b741_0"
TOP_N = 100
PREVIEW_N = 25


def money(s):
    """Parse a money-ish field into a float, returns 0.0 on failure."""
    if s is None:
        return 0.0
    s = str(s).strip().replace("$", "").replace(",", "")
    if s == "" or s.lower() in ("null", "none", "nan"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def clean(s):
    return str(s or "").strip()


def redact_name(name):
    """Turn 'JANE SMITH' -> 'J*** S****' for preview."""
    if not name:
        return "[REDACTED]"
    parts = name.strip().split()
    out = []
    for p in parts:
        if len(p) <= 1:
            out.append(p)
        else:
            out.append(p[0] + "*" * max(2, len(p) - 1))
    return " ".join(out)


print(f"=== Processing {SRC} ===")
print(f"  output dir: {OUT_DIR}")

all_rows = []
with open(SRC, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        all_rows.append(row)

print(f"  total source rows: {len(all_rows):,}")

# Filter: absentee owner = mailing state is not NC, OR mailing state is empty
# Also filter to records with a real delinquent amount and not internal placeholders
filtered = []
for r in all_rows:
    mail_state = clean(r.get("MAIL_STATE", "")).upper()
    owner = clean(r.get("OWNER_NAME", ""))
    total_due = money(r.get("TOTAL_DUE_AMOUNT", "0"))
    assess = money(r.get("PROP_ASSESS_VALUE", "0"))
    if not owner or owner.lower() in ("null", "none"):
        continue
    if total_due <= 0:
        continue
    # Absentee: mailing state is set AND != NC
    if mail_state and mail_state != "NC":
        r["_absentee"] = True
        r["_absentee_reason"] = f"out_of_state:{mail_state}"
        filtered.append(r)

print(f"  absentee + delinquent rows: {len(filtered):,}")

# Score: weighted blend of amount owed + property value + tax year age.
# Higher score = more motivated, more equity, longer outstanding.
def score(r):
    due = money(r.get("TOTAL_DUE_AMOUNT", "0"))
    assess = money(r.get("PROP_ASSESS_VALUE", "0"))
    try:
        year = int(clean(r.get("TAX_YEAR", "0")) or 0)
    except ValueError:
        year = 0
    # Age component: older tax year = more years delinquent
    age = max(0, 2026 - year) if year > 1990 else 0
    # Normalize each piece roughly to 0-100
    due_pts = min(100, due / 100.0)  # $10,000 due = 100 pts
    val_pts = min(50, assess / 10000.0)  # $500k = 50 pts
    age_pts = min(30, age * 10)  # 3 years = 30 pts
    return due_pts + val_pts + age_pts


for r in filtered:
    r["_score"] = round(score(r), 2)

filtered.sort(key=lambda r: r["_score"], reverse=True)
top = filtered[:TOP_N]

print(f"  top {TOP_N} by score, range: {top[-1]['_score']:.1f}-{top[0]['_score']:.1f}")

# Build the full snapshot CSV
snapshot_cols = [
    "rank",
    "score",
    "owner_name",
    "in_care_of",
    "mail_address_1",
    "mail_address_2",
    "mail_city",
    "mail_state",
    "mail_zip",
    "parcel_number",
    "tax_year",
    "property_assessed_value",
    "bill_amount",
    "interest_due",
    "total_due",
    "bill_due_date",
    "legal_description",
    "absentee_signal",
    "lane",
    "county",
    "state",
    "source_url",
    "source_date",
]

def to_out_row(rank, r):
    return {
        "rank": rank,
        "score": r["_score"],
        "owner_name": clean(r.get("OWNER_NAME")),
        "in_care_of": clean(r.get("IN_CARE_OF")),
        "mail_address_1": clean(r.get("MAIL_ADDR1")),
        "mail_address_2": clean(r.get("MAIL_ADDR2")) or clean(r.get("MAIL_ADDR3")),
        "mail_city": clean(r.get("MAIL_CITY")),
        "mail_state": clean(r.get("MAIL_STATE")).upper(),
        "mail_zip": clean(r.get("MAIL_ZIP")),
        "parcel_number": clean(r.get("PARCEL_NUM")),
        "tax_year": clean(r.get("TAX_YEAR")),
        "property_assessed_value": clean(r.get("PROP_ASSESS_VALUE")),
        "bill_amount": clean(r.get("BILL_AMOUNT")),
        "interest_due": clean(r.get("INTEREST_DUE")),
        "total_due": clean(r.get("TOTAL_DUE_AMOUNT")),
        "bill_due_date": clean(r.get("BILL_DUE_DATE")),
        "legal_description": clean(r.get("LEGAL_DESCRIPTION"))[:200],
        "absentee_signal": r.get("_absentee_reason", ""),
        "lane": LANE,
        "county": COUNTY,
        "state": STATE,
        "source_url": SOURCE_URL,
        "source_date": DATE,
    }

snapshot_path = OUT_DIR / f"guilford-nc-absentee-tax-delinquent-{DATE}.csv"
with open(snapshot_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=snapshot_cols)
    w.writeheader()
    for i, r in enumerate(top, 1):
        w.writerow(to_out_row(i, r))
print(f"  wrote snapshot: {snapshot_path}")

# Build preview (first 25, names redacted for sales)
preview_path = OUT_DIR / f"guilford-nc-absentee-tax-delinquent-{DATE}-preview.csv"
preview_cols = [
    "rank",
    "score",
    "owner_name_redacted",
    "mail_city",
    "mail_state",
    "tax_year",
    "property_assessed_value",
    "total_due",
    "absentee_signal",
    "lane",
    "county",
]
with open(preview_path, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=preview_cols)
    w.writeheader()
    for i, r in enumerate(top[:PREVIEW_N], 1):
        w.writerow({
            "rank": i,
            "score": r["_score"],
            "owner_name_redacted": redact_name(clean(r.get("OWNER_NAME"))),
            "mail_city": clean(r.get("MAIL_CITY")),
            "mail_state": clean(r.get("MAIL_STATE")).upper(),
            "tax_year": clean(r.get("TAX_YEAR")),
            "property_assessed_value": clean(r.get("PROP_ASSESS_VALUE")),
            "total_due": clean(r.get("TOTAL_DUE_AMOUNT")),
            "absentee_signal": r.get("_absentee_reason", ""),
            "lane": LANE,
            "county": COUNTY,
        })
print(f"  wrote preview: {preview_path}")

# Metadata
total_due_top = sum(money(r.get("TOTAL_DUE_AMOUNT")) for r in top)
states = {}
for r in top:
    s = clean(r.get("MAIL_STATE")).upper()
    states[s] = states.get(s, 0) + 1

meta = {
    "product_name": "Guilford NC Absentee + Tax Delinquent Snapshot",
    "lane": LANE,
    "county": COUNTY,
    "state": STATE,
    "source_url": SOURCE_URL,
    "source_pulled_at": DATE,
    "source_total_rows": len(all_rows),
    "absentee_delinquent_universe": len(filtered),
    "delivered_rows": len(top),
    "score_range": [round(top[-1]["_score"], 2), round(top[0]["_score"], 2)],
    "total_due_aggregate": round(total_due_top, 2),
    "owner_mail_state_breakdown": dict(sorted(states.items(), key=lambda kv: -kv[1])),
    "compliance_note": "Property data only. Buyer responsible for skip trace, DNC compliance, TCPA, and outreach. DNC-aware fields not included in this tier.",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
}
meta_path = OUT_DIR / f"guilford-nc-absentee-tax-delinquent-{DATE}-meta.json"
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, indent=2)
print(f"  wrote metadata: {meta_path}")

print()
print("=== SNAPSHOT SUMMARY ===")
print(json.dumps(meta, indent=2))
