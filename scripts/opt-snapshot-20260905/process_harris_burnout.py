#!/usr/bin/env python3
"""Harris TX — Permit Burnout Lane.

Distress signals:
  * Active/open permits (status != 'C' closed)
  * High-distress permit descriptions (FIRELOSS, DEMOLITION, REPAIR, DAMAGE)
  * Absentee owner (mailing state != TX or mailing city != site city)
  * Entity-owned (LLC/INC/TRUST/REIT/etc.)
  * Older property (yr_impr <= 1980)

Output:
  * harris-tx-permit-burnout-2026-06-21.csv          (top 1500 distressed)
  * harris-tx-permit-burnout-2026-06-21-preview.csv  (top 25 redacted)
  * meta.json
"""
import csv
import json
import re
import sys

csv.field_size_limit(sys.maxsize)
from collections import defaultdict
from datetime import date
from pathlib import Path

RAW_DIR = Path("/opt/leadcurate/raw_imports/harris-tx/2026-06-20")
OUT_DIR = Path("/opt/leadcurate/snapshots/harris-tx") / date.today().isoformat()
OUT_DIR.mkdir(parents=True, exist_ok=True)

ENTITY_PATTERNS = re.compile(
    r"\b(LLC|L\.L\.C\.|INC|INCORPORATED|CORP|CORPORATION|CO|COMPANY|LP|LTD|TRUST|TRUSTEE|"
    r"REIT|HOLDINGS?|PARTNERS?|GROUP|ASSOC|ASSN|FOUNDATION|FUND|CHURCH|CITY|COUNTY|STATE|"
    r"HOA|HOMEOWNERS?|REALTY|PROPERTIES|INVESTMENTS?|RENTALS?|MGT|MGMT|MANAGEMENT|"
    r"VENTURE|EQUITY|CAPITAL|GROUP|SFR|REI|HOMES?)\b",
    re.IGNORECASE,
)
DISTRESS_KEYWORDS = re.compile(
    r"\b(FIRELOSS|FIRE LOSS|FIRE.DAMAGE|DEMO|DEMOLITION|REPAIR|DAMAGE|UNSAFE|"
    r"CONDEMNED|CONDEMN|FORECLOSURE|VIOLATION|VACANT|STORM|WIND|FLOOD|HAIL|"
    r"ABATEMENT|EMERGENCY|HAZARDOUS|RESCIND|STOP WORK|STOP_WORK|NON.COMPLIANT|"
    r"DEFECT)\b",
    re.IGNORECASE,
)
RESIDENTIAL_CLASSES = {
    # Harris state_class — residential SFR-ish
    "A1", "A2", "B1", "B2", "B3", "B4", "X1",
}


def s(v):
    return (v or "").strip()


def fnum(v):
    try:
        return float(s(v).replace(",", "") or 0)
    except (ValueError, TypeError):
        return 0.0


def fint(v):
    try:
        return int(float(s(v).replace(",", "") or 0))
    except (ValueError, TypeError):
        return 0


# ============================================
# Pass 1: collect distressed permits keyed by acct
# ============================================
print("[1/4] Scanning permits.txt for distress signals…", file=sys.stderr)
permit_signals = defaultdict(lambda: {"count": 0, "kinds": set(), "latest_year": 0, "latest_dscr": ""})
with open(RAW_DIR / "permits.txt", newline="", encoding="latin-1") as fp:
    reader = csv.DictReader(fp, delimiter="\t")
    for i, row in enumerate(reader):
        if i and i % 200_000 == 0:
            print(f"      …{i:,} permits scanned, {len(permit_signals):,} accts with distress", file=sys.stderr)
        acct = s(row.get("acct"))
        if not acct:
            continue
        status = s(row.get("status")).upper()
        dscr = s(row.get("dscr"))
        ptype = s(row.get("permit_tp_descr"))
        yr = fint(row.get("yr"))
        # Only "open" / "active" / non-closed permits
        is_open = status not in ("C", "F", "VOID", "VO", "X")
        is_distress = bool(DISTRESS_KEYWORDS.search(dscr) or DISTRESS_KEYWORDS.search(ptype))
        if not (is_open or is_distress):
            continue
        rec = permit_signals[acct]
        rec["count"] += 1
        if is_distress:
            kind = (DISTRESS_KEYWORDS.search(dscr) or DISTRESS_KEYWORDS.search(ptype)).group(0).upper()
            rec["kinds"].add(kind)
        if yr > rec["latest_year"]:
            rec["latest_year"] = yr
            rec["latest_dscr"] = dscr[:80]

print(f"      done: {len(permit_signals):,} accts have open or distressed permits.", file=sys.stderr)


# ============================================
# Pass 2: collect primary owner per acct
# ============================================
print("[2/4] Scanning owners.txt for primary owner…", file=sys.stderr)
primary_owner = {}
with open(RAW_DIR / "owners.txt", newline="", encoding="latin-1") as fp:
    reader = csv.DictReader(fp, delimiter="\t")
    for row in reader:
        acct = s(row.get("acct"))
        ln = s(row.get("ln_num"))
        if not acct or acct in primary_owner:
            continue
        if ln in ("", "1"):
            primary_owner[acct] = s(row.get("name"))
print(f"      done: {len(primary_owner):,} primary owners indexed.", file=sys.stderr)


# ============================================
# Pass 3: scan real_acct, score, write top distressed
# ============================================
print("[3/4] Scoring real_acct.txt against distress signals…", file=sys.stderr)
rows_out = []
candidates = 0
with open(RAW_DIR / "real_acct.txt", newline="", encoding="latin-1") as fp:
    reader = csv.DictReader(fp, delimiter="\t")
    for i, row in enumerate(reader):
        if i and i % 200_000 == 0:
            print(f"      …{i:,} accts scanned, {len(rows_out):,} kept", file=sys.stderr)
        acct = s(row.get("acct"))
        if not acct:
            continue
        signal = permit_signals.get(acct)
        if not signal:
            continue
        candidates += 1
        # Only residential
        state_class = s(row.get("state_class"))
        if state_class[:2] not in RESIDENTIAL_CLASSES and not state_class.startswith("A"):
            continue
        owner = primary_owner.get(acct) or s(row.get("mailto"))
        if not owner:
            continue

        site_addr = " ".join(filter(None, [
            s(row.get("str_num")), s(row.get("str_pfx")), s(row.get("str")),
            s(row.get("str_sfx")), s(row.get("str_sfx_dir")),
        ])).strip()
        if not site_addr:
            site_addr = s(row.get("site_addr_1"))
        site_addr = re.sub(r"\s+", " ", site_addr)
        site_unit = s(row.get("str_unit"))

        site_city = s(row.get("site_addr_2")) or "HOUSTON"
        site_zip = s(row.get("site_addr_3"))

        mail_state = s(row.get("mail_state"))
        mail_city = s(row.get("mail_city"))
        is_absentee = (mail_state and mail_state.upper() != "TX") or (
            mail_city and site_city and mail_city.upper() != site_city.upper()
        )
        is_entity = bool(ENTITY_PATTERNS.search(owner))

        mkt_val = fnum(row.get("tot_mkt_val"))
        land_val = fnum(row.get("land_val"))
        bld_val = fnum(row.get("bld_val"))
        yr_impr = fint(row.get("yr_impr"))

        # Skip vacant land and ultra-low value
        if bld_val == 0 or mkt_val < 25_000:
            continue
        if mkt_val > 2_000_000:  # skip mansions (not core investor target)
            continue

        # Scoring
        score = 0
        kinds = signal["kinds"]
        score += 35 if kinds else 0
        score += min(25, signal["count"] * 5)
        score += 15 if is_absentee else 0
        score += 10 if is_entity else 0
        if yr_impr and yr_impr <= 1970:
            score += 15
        elif yr_impr and yr_impr <= 1990:
            score += 8
        # Value-equity proxy
        if 50_000 <= mkt_val <= 250_000:
            score += 10

        rows_out.append({
            "parcel_id": acct,
            "owner_name": owner,
            "owner_type": "entity" if is_entity else "individual",
            "absentee": "Y" if is_absentee else "N",
            "site_addr": site_addr,
            "site_unit": site_unit,
            "site_city": site_city or "HOUSTON",
            "site_zip": site_zip,
            "mail_city": mail_city,
            "mail_state": mail_state,
            "mail_zip": s(row.get("mail_zip")),
            "yr_built": yr_impr,
            "bld_sqft": fint(row.get("bld_ar")),
            "land_sqft": fint(row.get("land_ar")),
            "mkt_val": int(mkt_val),
            "land_val": int(land_val),
            "bld_val": int(bld_val),
            "permit_count": signal["count"],
            "distress_kinds": ", ".join(sorted(kinds)),
            "latest_permit_yr": signal["latest_year"],
            "latest_permit_dscr": signal["latest_dscr"],
            "score": score,
        })

print(f"      done: {candidates:,} candidates with permit signal, {len(rows_out):,} qualified residentials.", file=sys.stderr)


# ============================================
# Pass 4: rank and write
# ============================================
print("[4/4] Ranking, writing CSV + preview…", file=sys.stderr)
rows_out.sort(key=lambda r: r["score"], reverse=True)
TOP = 1500
top_rows = rows_out[:TOP]

csv_path = OUT_DIR / f"harris-tx-permit-burnout-{date.today().isoformat()}.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as fp:
    writer = csv.DictWriter(fp, fieldnames=list(top_rows[0].keys()))
    writer.writeheader()
    writer.writerows(top_rows)

# Redacted preview (top 25, owner_name + addresses scrubbed except first letter + ***)
def redact_name(n):
    parts = n.split()
    return " ".join((p[0] + "***") if len(p) > 1 else p for p in parts)

def redact_addr(a):
    return re.sub(r"\b\d+\b", "###", a, count=1)

preview_path = OUT_DIR / f"harris-tx-permit-burnout-{date.today().isoformat()}-preview.csv"
with open(preview_path, "w", newline="", encoding="utf-8") as fp:
    writer = csv.DictWriter(fp, fieldnames=list(top_rows[0].keys()))
    writer.writeheader()
    for r in top_rows[:25]:
        rr = dict(r)
        rr["owner_name"] = redact_name(rr["owner_name"])
        rr["site_addr"] = redact_addr(rr["site_addr"])
        rr["mail_zip"] = (rr["mail_zip"][:3] + "**") if rr["mail_zip"] else ""
        writer.writerow(rr)

# Stats for meta.json
abs_count = sum(1 for r in top_rows if r["absentee"] == "Y")
ent_count = sum(1 for r in top_rows if r["owner_type"] == "entity")
fire_count = sum(1 for r in top_rows if "FIRELOSS" in r["distress_kinds"] or "FIRE" in r["distress_kinds"])
demo_count = sum(1 for r in top_rows if "DEMO" in r["distress_kinds"] or "DEMOLITION" in r["distress_kinds"])
repair_count = sum(1 for r in top_rows if "REPAIR" in r["distress_kinds"] or "DAMAGE" in r["distress_kinds"])

meta = {
    "market": "Harris County, TX (Houston metro)",
    "lane": "Permit Burnout",
    "pulled": "2026-06-20",
    "processed": date.today().isoformat(),
    "source": "HCAD bulk download (real_acct + owners + permits)",
    "universe_size": 1623292,
    "candidates_with_permits": candidates,
    "qualified_residential": len(rows_out),
    "delivered_top_n": len(top_rows),
    "absentee_count": abs_count,
    "entity_count": ent_count,
    "fire_loss_count": fire_count,
    "demolition_count": demo_count,
    "repair_damage_count": repair_count,
    "avg_market_value": int(sum(r["mkt_val"] for r in top_rows) / len(top_rows)),
    "min_score": top_rows[-1]["score"],
    "max_score": top_rows[0]["score"],
}
(OUT_DIR / "meta.json").write_text(json.dumps(meta, indent=2))

print(f"\n=== DONE ===", file=sys.stderr)
print(f"  CSV:     {csv_path}", file=sys.stderr)
print(f"  Preview: {preview_path}", file=sys.stderr)
print(f"  Meta:    {OUT_DIR / 'meta.json'}", file=sys.stderr)
print(json.dumps(meta, indent=2))
