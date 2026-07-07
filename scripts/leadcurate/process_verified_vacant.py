#!/usr/bin/env python3
"""Mecklenburg verified-vacant land — STRICT empty-land proof.

A parcel only qualifies if EVERY vacancy signal agrees:
  - county flag vacantorimproved == 'VAC'
  - no building value (netbldgvalue 0/empty)
  - total value == land value (nothing but dirt is assessed)
  - no year built, no heated area
  - owner is not an HOA / municipality / utility (not sellable leads)
  - parcel is at least 0.1 acre (no slivers/easements)
Score: land value + acreage + absentee bonus.
"""
import csv
import json
import os
import re

SRC = "/opt/leadcurate/raw_imports/mecklenburg-nc/vacant-land.csv"
OUT_DIR = "/opt/leadcurate/processed/mecklenburg-nc/2026-07-07"
DATE = "2026-07-07"

EXCLUDE_OWNER = re.compile(
    r"ASSOCIATION|HOMEOWNER|HOA\b|CITY OF|COUNTY|STATE OF|TOWN OF|CHURCH|"
    r"DEPARTMENT|AUTHORITY|DISTRICT|UNITED STATES|NCDOT|DUKE ENERGY|RAILROAD|RAILWAY",
    re.I,
)

def fnum(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0

def main():
    rows = []
    total = 0
    with open(SRC, newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            total += 1
            if (r.get("vacantorimproved") or "").strip().upper() != "VAC":
                continue
            land = fnum(r.get("landvalue"))
            totv = fnum(r.get("totalvalue"))
            bldg = fnum(r.get("netbldgvalue"))
            if bldg > 0 or land <= 0 or totv <= 0:
                continue
            if abs(totv - land) > 1:  # anything above land value implies improvements
                continue
            if (r.get("yearbuilt") or "").strip() or fnum(r.get("heatedarea")) > 0:
                continue
            ac = fnum(r.get("totalac"))
            if ac < 0.1:
                continue
            owner = " ".join(x for x in [
                (r.get("ownerfirstname") or "").strip(),
                (r.get("ownerlastname") or "").strip()] if x).strip()
            if not owner or EXCLUDE_OWNER.search(owner):
                continue
            addr = " ".join(x for x in [
                (r.get("houseno") or "").strip(), (r.get("stdir") or "").strip(),
                (r.get("stname") or "").strip(), (r.get("sttype") or "").strip()] if x).strip()
            mail_city = (r.get("city") or "").strip()
            mail_state = (r.get("state") or "").strip()
            absentee = "yes" if mail_state.upper() != "NC" or (
                mail_city.upper() not in ("CHARLOTTE", "") and mail_state.upper() == "NC" and
                mail_city.upper() != (r.get("municipality") or "").strip().upper()) else "no"
            score = land / 1000 + ac * 40 + (150 if mail_state.upper() != "NC" else 0)
            rows.append({
                "owner_name": owner, "property_address": addr or "(unaddressed parcel)",
                "municipality": (r.get("municipality") or "").strip(),
                "mail_city": mail_city, "mail_state": mail_state,
                "total_acreage": ac, "land_value": land, "total_value": totv,
                "is_absentee_owner": absentee,
                "county_vacant_flag": "VAC", "building_value": 0,
                "year_built": "", "heated_sqft": 0,
                "land_use_code": (r.get("landusecode") or "").strip(),
                "parcel_pid": (r.get("pid") or "").strip(),
                "score": round(score, 1),
            })

    rows.sort(key=lambda r: r["score"], reverse=True)
    top = rows[:250]
    os.makedirs(OUT_DIR, exist_ok=True)
    cols = ["rank", "score", "owner_name", "property_address", "municipality",
            "mail_city", "mail_state", "total_acreage", "land_value", "total_value",
            "is_absentee_owner", "county_vacant_flag", "building_value", "year_built",
            "heated_sqft", "land_use_code", "parcel_pid", "lane", "county", "state"]
    full = f"{OUT_DIR}/mecklenburg-nc-verified-vacant-{DATE}.csv"
    prev = f"{OUT_DIR}/mecklenburg-nc-verified-vacant-{DATE}-preview.csv"
    meta = f"{OUT_DIR}/mecklenburg-nc-verified-vacant-{DATE}-meta.json"
    with open(full, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols)
        for i, r in enumerate(top, 1):
            w.writerow([i, r["score"], r["owner_name"], r["property_address"], r["municipality"],
                        r["mail_city"], r["mail_state"], r["total_acreage"], r["land_value"],
                        r["total_value"], r["is_absentee_owner"], "VAC", 0, "", 0,
                        r["land_use_code"], r["parcel_pid"], "verified_vacant_land", "Mecklenburg", "NC"])
    with open(prev, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(cols)
        for i, r in enumerate(top[:25], 1):
            parts = r["owner_name"].split()
            red = " ".join(p[0] + "*" * max(len(p) - 1, 2) for p in parts)
            w.writerow([i, r["score"], red, r["property_address"], r["municipality"],
                        "", r["mail_state"], r["total_acreage"], r["land_value"],
                        r["total_value"], r["is_absentee_owner"], "VAC", 0, "", 0,
                        r["land_use_code"], "REDACTED", "verified_vacant_land", "Mecklenburg", "NC"])
    absentee_n = sum(1 for r in rows if r["is_absentee_owner"] == "yes")
    oos_n = sum(1 for r in rows if r["mail_state"].upper() not in ("NC", ""))
    with open(meta, "w", encoding="utf-8") as f:
        json.dump({
            "lane": "verified_vacant_land", "processed_date": DATE,
            "source": "Mecklenburg County parcel file (vacant-land extract)",
            "total_source_rows": total, "verified_vacant": len(rows),
            "absentee": absentee_n, "out_of_state": oos_n,
            "exported": len(top),
            "verification_criteria": [
                "county flag vacantorimproved=VAC", "building value = 0",
                "total value == land value", "no year built / heated area",
                "owner not HOA/municipal/utility/rail", ">= 0.1 acre"],
        }, f, indent=2)
    print(json.dumps({"source_rows": total, "verified_vacant": len(rows),
                      "absentee": absentee_n, "out_of_state": oos_n,
                      "top5": [(r["owner_name"][:30], r["total_acreage"], r["land_value"],
                                r["mail_state"]) for r in top[:5]]}, indent=2))

if __name__ == "__main__":
    main()
