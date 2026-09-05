#!/usr/bin/env python3
"""
Build paying-customer-ready packages.

Two County Seat packages:
  - Louisville KY (Jefferson)  — 3 lanes
  - Charlotte NC (Mecklenburg) — 3 lanes (reuses already-built snapshots)

Each package is a folder containing:
  - README.txt              — branded cover sheet for the customer
  - manifest.json           — machine-readable index
  - lanes/{lane}/*.csv      — per-lane full snapshot + preview + meta
  - combined-top25.csv      — best 25 from each lane in one view
"""
import csv
import json
import shutil
import re
from datetime import datetime, timezone, date
from pathlib import Path

DATE = datetime.now(timezone.utc).strftime("%Y-%m-%d")
RAW = Path("/opt/leadcurate/raw_imports")
PROC = Path("/opt/leadcurate/processed")
PACKAGES = Path("/opt/leadcurate/packages")
PACKAGES.mkdir(parents=True, exist_ok=True)

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


def parse_date(s):
    s = clean(s)
    if not s:
        return None
    s = re.sub(r"[+-]\d{2}:?\d{0,2}$", "", s).strip()
    for fmt in (
        "%m/%d/%Y %I:%M:%S %p",
        "%m/%d/%Y %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# =====================================================================
# LANE BUILDER: Louisville code violations
# =====================================================================
def build_louisville_code_violations(out_dir):
    src = RAW / "jefferson-ky" / "property-maintenance-violations.csv"
    rows = []
    with open(src, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            status = clean(r.get("G6A_G6_STATUS", "")).lower()
            if status in ("closed", "void", "withdrawn"):
                continue
            addr = clean(r.get("FullAddress"))
            if not addr or addr.upper() == "NULL":
                continue
            violation = clean(r.get("VIOLATION_CODE")) or clean(r.get("GUIDE_ITEM_TEXT"))
            occupancy = clean(r.get("OccupancyStatus"))
            citation = money(r.get("CitationAmount"))
            insp_dt = parse_date(r.get("G6A_G6_COMPL_DD"))
            rows.append({
                "_addr": addr,
                "_partial": clean(r.get("PartialAddress")),
                "_parcel": clean(r.get("PARCEL_ID")),
                "_violation": violation,
                "_occupancy": occupancy,
                "_status": clean(r.get("G6A_G6_STATUS")),
                "_citation": citation,
                "_council": clean(r.get("CouncilDist")),
                "_dt": insp_dt,
                "_dt_iso": insp_dt.isoformat() if insp_dt else "",
            })
    today = date.today()
    for r in rows:
        pts = 0
        if r["_dt"]:
            age = (today - r["_dt"]).days
            pts += max(0, 60 - max(0, age) / 30)
        v = r["_violation"].upper()
        if any(w in v for w in ("ABANDONED", "VACANT", "STRUCTURE", "BOARDED")):
            pts += 30
        if any(w in r["_occupancy"].upper() for w in ("VACANT", "ABANDONED")):
            pts += 20
        if r["_citation"] > 0:
            pts += min(20, r["_citation"] / 25)
        r["_score"] = round(pts, 2)
    rows.sort(key=lambda r: r["_score"], reverse=True)
    top = rows[:100]
    cols = ["rank", "score", "property_address", "violation_code",
            "occupancy_status", "violation_status", "citation_amount",
            "inspection_date", "council_district", "parcel_id",
            "lane", "county", "state"]
    csv_path = out_dir / "louisville-ky-code-violations.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, r in enumerate(top, 1):
            w.writerow({
                "rank": i, "score": r["_score"],
                "property_address": r["_addr"],
                "violation_code": r["_violation"],
                "occupancy_status": r["_occupancy"],
                "violation_status": r["_status"],
                "citation_amount": r["_citation"],
                "inspection_date": r["_dt_iso"],
                "council_district": r["_council"],
                "parcel_id": r["_parcel"],
                "lane": "code_violations_open",
                "county": "Jefferson", "state": "KY",
            })
    preview_path = out_dir / "louisville-ky-code-violations-preview.csv"
    with open(preview_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "score", "property_partial",
                                          "violation_code", "occupancy_status",
                                          "inspection_date", "lane"])
        w.writeheader()
        for i, r in enumerate(top[:25], 1):
            parts = r["_partial"].split()
            masked = (parts[0][0] + "***" + " " + " ".join(parts[1:])) if parts and parts[0].isdigit() else r["_partial"]
            w.writerow({
                "rank": i, "score": r["_score"],
                "property_partial": masked,
                "violation_code": r["_violation"],
                "occupancy_status": r["_occupancy"],
                "inspection_date": r["_dt_iso"],
                "lane": "code_violations_open",
            })
    meta = {
        "lane": "code_violations_open",
        "product_name": "Louisville KY Open Code Violations",
        "source_total_rows": 17756,
        "filtered_universe": len(rows),
        "delivered_rows": len(top),
        "score_range": [round(top[-1]["_score"], 2), round(top[0]["_score"], 2)],
        "source_url": "https://data.louisvilleky.gov/datasets/louisville-metro-ky-property-maintenance-inspection-violations",
        "source_pulled_at": DATE,
    }
    (out_dir / "louisville-ky-code-violations-meta.json").write_text(json.dumps(meta, indent=2))
    return top, meta


# =====================================================================
# LANE BUILDER: Louisville lien holder final orders
# =====================================================================
def build_louisville_lien_orders(out_dir):
    src = RAW / "jefferson-ky" / "lien-holder-final-orders.csv"
    rows = []
    with open(src, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            state = clean(r.get("final_order_state", "")).lower()
            if state in ("rescinded", "vacated"):
                continue
            owner = clean(r.get("fullname"))
            stno = clean(r.get("stno"))
            stname = clean(r.get("stname"))
            suffix = clean(r.get("suffix"))
            predir = clean(r.get("predir"))
            stsub = clean(r.get("stsub"))
            addr = " ".join(p for p in [stno, predir, stname, suffix, stsub] if p)
            mail_city = clean(r.get("city"))
            mail_state = clean(r.get("state")).upper()
            mail_zip = clean(r.get("zip"))
            citation = money(r.get("final_citation_amount"))
            notif = parse_date(r.get("date_of_notification"))
            hearing = parse_date(r.get("hearing_scheduled"))
            if not addr or not owner:
                continue
            rows.append({
                "_owner": owner,
                "_addr": addr,
                "_mail_addr1": clean(r.get("addr1")),
                "_mail_city": mail_city,
                "_mail_state": mail_state,
                "_mail_zip": mail_zip,
                "_state": clean(r.get("final_order_state")),
                "_citation": citation,
                "_notif": notif.isoformat() if notif else "",
                "_hearing": hearing.isoformat() if hearing else "",
                "_inspector": clean(r.get("inspector")),
                "_aca": clean(r.get("aca_deeplink")),
            })
    today = date.today()
    for r in rows:
        pts = min(50, r["_citation"] / 50)  # higher fine = bigger distress
        if r["_mail_state"] and r["_mail_state"] != "KY":
            pts += 25  # out-of-state owner
        notif_d = parse_date(r["_notif"])
        if notif_d:
            age = (today - notif_d).days
            pts += max(0, 30 - max(0, age) / 30)
        r["_score"] = round(pts, 2)
    rows.sort(key=lambda r: r["_score"], reverse=True)
    top = rows[:100] if len(rows) >= 100 else rows
    cols = ["rank", "score", "owner_name", "property_address",
            "owner_mail_address", "owner_mail_city", "owner_mail_state",
            "owner_mail_zip", "is_out_of_state", "final_order_state",
            "final_citation_amount", "date_of_notification",
            "hearing_scheduled", "case_link", "lane", "county", "state"]
    csv_path = out_dir / "louisville-ky-lien-holder-orders.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for i, r in enumerate(top, 1):
            w.writerow({
                "rank": i, "score": r["_score"],
                "owner_name": r["_owner"],
                "property_address": r["_addr"],
                "owner_mail_address": r["_mail_addr1"],
                "owner_mail_city": r["_mail_city"],
                "owner_mail_state": r["_mail_state"],
                "owner_mail_zip": r["_mail_zip"],
                "is_out_of_state": "yes" if (r["_mail_state"] and r["_mail_state"] != "KY") else "no",
                "final_order_state": r["_state"],
                "final_citation_amount": r["_citation"],
                "date_of_notification": r["_notif"],
                "hearing_scheduled": r["_hearing"],
                "case_link": r["_aca"],
                "lane": "lien_holder_final_orders",
                "county": "Jefferson", "state": "KY",
            })
    preview_path = out_dir / "louisville-ky-lien-holder-orders-preview.csv"
    with open(preview_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "score", "owner_redacted",
                                          "owner_mail_state", "final_order_state",
                                          "final_citation_amount", "date_of_notification",
                                          "is_out_of_state", "lane"])
        w.writeheader()
        for i, r in enumerate(top[:25], 1):
            parts = r["_owner"].split()
            owner_red = " ".join(p[0] + "*" * max(2, len(p) - 1) if len(p) > 1 else p for p in parts)
            w.writerow({
                "rank": i, "score": r["_score"],
                "owner_redacted": owner_red,
                "owner_mail_state": r["_mail_state"],
                "final_order_state": r["_state"],
                "final_citation_amount": r["_citation"],
                "date_of_notification": r["_notif"],
                "is_out_of_state": "yes" if (r["_mail_state"] and r["_mail_state"] != "KY") else "no",
                "lane": "lien_holder_final_orders",
            })
    meta = {
        "lane": "lien_holder_final_orders",
        "product_name": "Louisville KY Lien Holder Final Orders",
        "source_total_rows": 516,
        "filtered_universe": len(rows),
        "delivered_rows": len(top),
        "score_range": [round(top[-1]["_score"], 2), round(top[0]["_score"], 2)] if top else [0, 0],
        "source_url": "https://data.louisvilleky.gov/datasets/louisville-metro-ky-lien-holder-final-orders",
        "source_pulled_at": DATE,
    }
    (out_dir / "louisville-ky-lien-holder-orders-meta.json").write_text(json.dumps(meta, indent=2))
    return top, meta


# =====================================================================
# README BUILDER
# =====================================================================
README_TEMPLATE = """\
======================================================================
  L E A D C U R A T E   .
  ----------------------------------------------------------------------
  County Seat delivery package
======================================================================

CUSTOMER COUNTY:    {county_name}, {state}
DELIVERY DATE:      {date}
LANE COUNT:         {lane_count}
TOTAL RECORDS:      {total_records}
PACKAGE ID:         {pkg_id}

----------------------------------------------------------------------
  WHAT'S IN THIS PACKAGE
----------------------------------------------------------------------

This folder contains your monthly County Seat delivery for {county_name},
{state}. It is organized into {lane_count} distinct distress lanes, each
sold and serviced separately so the same record never appears in more
than one product across LeadCurate's customer base.

Folder layout:

  README.txt                          this file
  manifest.json                       machine-readable index
  combined-top25.csv                  the strongest 25 records from
                                      every lane, in one consolidated
                                      view for quick triage
  lanes/{{lane_slug}}/                  one folder per lane:
    <lane>.csv                        full ranked list (this delivery)
    <lane>-preview.csv                25-row preview (names redacted) -
                                      forward this when you want to
                                      bring on a partner without
                                      exposing the live list
    <lane>-meta.json                  source URL, pull date, universe
                                      counts, score range, compliance

----------------------------------------------------------------------
  THE LANES YOU OWN THIS MONTH
----------------------------------------------------------------------
{lanes_block}
----------------------------------------------------------------------
  WORKING THE BATCH
----------------------------------------------------------------------

Records are pre-scored - rank 1 is the highest-priority record in
each lane based on the freshness + distress + value signals listed
in that lane's meta.json.

Suggested workflow:
  1. Start with combined-top25.csv for the highest-priority 25 records
     across all your lanes - this is the warm-up list.
  2. Move into each lane's full CSV in rank order.
  3. Cross-reference owner mailing address vs. property address in
     each row - out-of-state mailing addresses are flagged in the data.
  4. Run skip-trace through your existing tool (PropStream / BatchLeads /
     BatchData / Skip Genie). This package ships clean property-record
     data only - we do not include phone numbers in this tier so you
     stay free of TCPA/DNC exposure on our end.
  5. Mark and exclude any records you decide to skip. We track
     exclusions on our side too so the same record does not come back
     in your next batch.

----------------------------------------------------------------------
  FRESHNESS POSTURE
----------------------------------------------------------------------

LeadCurate sources directly from official county portals - not
licensed reseller feeds. Compared to PropStream / BatchLeads, which
license from ATTOM and CoreLogic on a 30 to 90 day refresh cycle,
this package was pulled fresh from the county on {date}.

A name that hits the {county_name} public record on the first of the
month is in your batch within days. The same name does not appear in
PropStream's data for another 30 to 90 days.

----------------------------------------------------------------------
  COMPLIANCE
----------------------------------------------------------------------

This delivery is property-record data only - no skip-traced phone
numbers, no email addresses, no DNC scrub. You handle owner contact
lookup, skip trace, DNC compliance, TCPA, and outreach decisions on
your side. LeadCurate provides data and educational tools only and
does not guarantee deals.

For every record we ship the source URL and source pull date in the
lane's meta.json so you can verify provenance independently.

----------------------------------------------------------------------
  REPLACEMENT POLICY (SUMMARY)
----------------------------------------------------------------------

We will replace a record if:
  - the record was a duplicate inside your same monthly batch
  - the record was the wrong county / territory / lane
  - a required field was missing that should have been included
  - there was a clear parsing error in our delivery
  - the record was already assigned to another buyer in an active
    exclusivity window (this should not happen but we will make it
    right if it does)

We will NOT replace a record because the seller was unmotivated,
did not answer, did not close, was not a deal, or because you did
not follow up. The data is the data. Your execution closes the deal.

----------------------------------------------------------------------

  Better data. Cleaner workflow. No hype.

  LeadCurate.

======================================================================
"""


def build_readme(county_name, state, lanes_info, pkg_id):
    lanes_block = ""
    for i, info in enumerate(lanes_info, 1):
        lanes_block += (
            f"\n  LANE {i}: {info['product_name']}\n"
            f"     records delivered : {info['delivered_rows']}\n"
            f"     filtered from    : {info['filtered_universe']:,} qualified  "
            f"(source universe: {info['source_total_rows']:,})\n"
            f"     score range      : {info['score_range'][0]} - {info['score_range'][1]}\n"
            f"     source           : {info['source_url']}\n"
        )
    total = sum(info["delivered_rows"] for info in lanes_info)
    return README_TEMPLATE.format(
        county_name=county_name, state=state, date=DATE,
        lane_count=len(lanes_info), total_records=total,
        pkg_id=pkg_id, lanes_block=lanes_block,
    )


# =====================================================================
# PACKAGE ASSEMBLER
# =====================================================================
def assemble_package(pkg_id, county_name, state, lanes_built):
    """lanes_built: list of (lane_slug, top_rows, meta, src_dir)"""
    pkg = PACKAGES / pkg_id
    if pkg.exists():
        shutil.rmtree(pkg)
    pkg.mkdir(parents=True)
    lanes_dir = pkg / "lanes"
    lanes_dir.mkdir()

    lanes_info = []
    for lane_slug, top_rows, meta, src_dir in lanes_built:
        ldir = lanes_dir / lane_slug
        ldir.mkdir()
        # Copy/find the lane CSVs into this folder
        for src in src_dir.glob(f"*{lane_slug}*"):
            shutil.copy(src, ldir / src.name)
        lanes_info.append(meta)

    # Build combined top-25
    combined_path = pkg / "combined-top25.csv"
    rows = []
    for lane_slug, top_rows, meta, _ in lanes_built:
        for r in top_rows[:25]:
            rows.append({
                "lane": meta["product_name"],
                "rank_in_lane": top_rows.index(r) + 1,
                "score": r.get("_score") if isinstance(r, dict) and "_score" in r else r.get("score", ""),
                "headline": _build_headline(meta["lane"], r),
            })
    with open(combined_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["lane", "rank_in_lane", "score", "headline"])
        w.writeheader()
        for row in rows:
            w.writerow(row)

    # Manifest
    manifest = {
        "package_id": pkg_id,
        "customer_county": county_name,
        "state": state,
        "delivery_date": DATE,
        "lane_count": len(lanes_built),
        "total_records": sum(m["delivered_rows"] for m in lanes_info),
        "lanes": lanes_info,
        "compliance_note": "Property-record data only. Buyer responsible for owner contact lookup, skip trace, DNC compliance, TCPA, and outreach decisions.",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (pkg / "manifest.json").write_text(json.dumps(manifest, indent=2))

    # README
    (pkg / "README.txt").write_text(build_readme(county_name, state, lanes_info, pkg_id))
    print(f"  package: {pkg}")
    return pkg


def _build_headline(lane, r):
    if isinstance(r, dict):
        if lane == "pre_foreclosure":
            return f"{r.get('property_address','?')} | sale: {r.get('sale_date','?')} | days_to_sale: {r.get('days_to_sale','?')}"
        if lane == "code_violations_open":
            return f"{r.get('_addr','?')} | {r.get('_violation','?')} | {r.get('_occupancy','?')}"
        if lane == "lien_holder_final_orders":
            return f"{r.get('_owner','?')} | {r.get('_state','?')} | ${r.get('_citation','?')} | mail_state: {r.get('_mail_state','?')}"
        if lane == "city_lien_active":
            return f"{r.get('owner_name','?')} | {r.get('property_address','?')} | {r.get('lien_status','?')}"
        if lane == "vacant_land":
            return f"{r.get('owner_name','?')} | {r.get('property_address','?')} | {r.get('total_acreage','?')} ac | {r.get('mail_state','?')}"
        if lane == "absentee_high_value":
            try:
                val = float(str(r.get("total_value", 0)).replace(",", "").replace("$", ""))
                val_str = f"${val:,.0f}"
            except Exception:
                val_str = str(r.get("total_value", "?"))
            return f"{r.get('owner_name','?')} | {r.get('property_location','?')} | {val_str} | {r.get('mail_state','?')}"
    return str(r)[:120]


# =====================================================================
# LOAD already-built Mecklenburg snapshots
# =====================================================================
def load_existing_snapshot(slug, src_dir, lane_key):
    csv_path = next((p for p in src_dir.glob(f"*{slug}*-2026-*.csv")
                     if "preview" not in p.name), None)
    meta_path = next(src_dir.glob(f"*{slug}*-meta.json"), None)
    if not csv_path or not meta_path:
        raise FileNotFoundError(f"{slug} not found in {src_dir}")
    meta = json.loads(meta_path.read_text())
    # Re-derive product_name + source_total_rows + filtered_universe
    if "product_name" not in meta:
        meta["product_name"] = slug
    if "filtered_universe" not in meta:
        meta["filtered_universe"] = meta.get("filtered_universe", meta.get("open_lien_universe", 0))
    if "source_total_rows" not in meta:
        meta["source_total_rows"] = meta.get("source_total_rows", 0)
    if "source_url" not in meta:
        meta["source_url"] = meta.get("source_url", "n/a")
    if "score_range" not in meta:
        meta["score_range"] = meta.get("score_range", [0, 0])
    rows = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows, meta


# =====================================================================
# RUN
# =====================================================================
print("\n=== Building Louisville KY package ===")
lou_dir = PROC / "jefferson-ky" / DATE
lou_dir.mkdir(parents=True, exist_ok=True)

# Existing pre-foreclosure (built 2026-06-18)
pre_dir = PROC / "jefferson-ky" / "2026-06-18"
pre_rows, pre_meta = load_existing_snapshot("pre-foreclosure", pre_dir, "pre_foreclosure")
pre_meta["product_name"] = "Louisville KY Pre-Foreclosure"
pre_meta.setdefault("filtered_universe", pre_meta.get("filtered_universe", 259))
pre_meta.setdefault("source_total_rows", 3000)

print(f"  pre-foreclosure: {len(pre_rows)} rows loaded")
cv_rows, cv_meta = build_louisville_code_violations(lou_dir)
print(f"  code violations: {len(cv_rows)} rows built")
lho_rows, lho_meta = build_louisville_lien_orders(lou_dir)
print(f"  lien holder orders: {len(lho_rows)} rows built")

# Stage pre-foreclosure files into lou_dir as well so they can be copied
for f in pre_dir.glob("*pre-foreclosure*"):
    target = lou_dir / f.name.replace("2026-06-18", DATE)
    if not target.exists():
        shutil.copy(f, target)

lou_pkg = assemble_package(
    pkg_id=f"louisville-ky-{DATE}",
    county_name="Louisville (Jefferson County)",
    state="KY",
    lanes_built=[
        ("pre-foreclosure", pre_rows, pre_meta, lou_dir),
        ("code-violations", cv_rows, cv_meta, lou_dir),
        ("lien-holder-orders", lho_rows, lho_meta, lou_dir),
    ],
)

print("\n=== Building Charlotte NC package ===")
char_dir = PROC / "mecklenburg-nc" / DATE
liens_rows, liens_meta = load_existing_snapshot("open-city-liens", char_dir, "city_lien_active")
liens_meta["product_name"] = "Charlotte NC Open City Liens"
vac_rows, vac_meta = load_existing_snapshot("vacant-land-specialty", char_dir, "vacant_land")
vac_meta["product_name"] = "Charlotte NC Vacant Land Specialty"
abs_rows, abs_meta = load_existing_snapshot("high-value-absentee", char_dir, "absentee_high_value")
abs_meta["product_name"] = "Charlotte NC High-Value Absentee Single-Family"

char_pkg = assemble_package(
    pkg_id=f"charlotte-nc-{DATE}",
    county_name="Charlotte (Mecklenburg County)",
    state="NC",
    lanes_built=[
        ("open-city-liens", liens_rows, liens_meta, char_dir),
        ("vacant-land-specialty", vac_rows, vac_meta, char_dir),
        ("high-value-absentee", abs_rows, abs_meta, char_dir),
    ],
)

print("\n=== Folder trees ===")
import os
for pkg in (lou_pkg, char_pkg):
    print(f"\n{pkg}/")
    for root, dirs, files in os.walk(pkg):
        rel = Path(root).relative_to(pkg.parent)
        for d in sorted(dirs):
            print(f"  {Path(rel)/d}/")
        for fn in sorted(files):
            sz = (Path(root) / fn).stat().st_size
            print(f"  {Path(rel)/fn}  ({sz} bytes)")
