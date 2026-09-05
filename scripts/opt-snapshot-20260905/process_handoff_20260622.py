#!/usr/bin/env python3
"""Generate LeadCurate snapshots for 2026-06-22 handoff counties.

Outputs normalized CSV + redacted preview + meta.json under /opt/leadcurate/snapshots.
No phone/email/DNC fields are produced; these are address/property-only lists.
"""
import csv, json, math, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import requests

DATE = "2026-06-22"
SNAPROOT = Path("/opt/leadcurate/snapshots")
RAWROOT = Path("/opt/leadcurate/raw_imports")
TOP_N = 5000
PREVIEW_N = 25
COMPLIANCE = "Property/address data only. No phone/email/DNC fields. Buyer responsible for skip trace, DNC/TCPA compliance, and outreach."


def clean(v):
    return str(v or "").strip()


def money(v):
    s = clean(v).replace("$", "").replace(",", "")
    if not s or s.lower() in {"null", "none", "nan"}:
        return 0.0
    try:
        return float(s)
    except Exception:
        return 0.0


def redact_name(name):
    name = clean(name)
    if not name:
        return "[REDACTED]"
    out=[]
    for p in name.split():
        out.append(p if len(p)<=1 else p[0] + "*"*min(8, max(2, len(p)-1)))
    return " ".join(out)


def state_from_citystzip(s):
    s = clean(s).upper()
    m = re.search(r"\b([A-Z]{2})\s+\d{5}(?:-\d{4})?\b", s)
    return m.group(1) if m else ""


def write_snapshot(market, product_name, rows, source_url, lane, county, state):
    outdir = SNAPROOT / market / DATE
    outdir.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    rows.sort(key=lambda r: money(r.get("score")), reverse=True)
    rows = rows[:TOP_N]
    full_path = outdir / f"{market}-{lane}-{DATE}.csv"
    preview_path = outdir / f"{market}-{lane}-{DATE}-preview.csv"
    meta_path = outdir / "meta.json"
    cols = [
        "rank","score","owner_name","mail_address","mail_city","mail_state","mail_zip",
        "situs_address","situs_city","situs_state","situs_zip","parcel_id","market_value",
        "land_value","building_value","year_built","acreage","distress_signal","score_reason",
        "lane","county","state","source_url","source_date","compliance_note"
    ]
    with full_path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for i,r in enumerate(rows,1):
            o={c: clean(r.get(c)) for c in cols}; o["rank"]=i; o["source_url"]=source_url; o["source_date"]=DATE; o["lane"]=lane; o["county"]=county; o["state"]=state; o["compliance_note"]=COMPLIANCE
            w.writerow(o)
    pcols = ["rank","score","owner_name_redacted","mail_city","mail_state","situs_city","situs_state","parcel_id","market_value","distress_signal","score_reason","lane","county"]
    with preview_path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=pcols); w.writeheader()
        for i,r in enumerate(rows[:PREVIEW_N],1):
            w.writerow({
                "rank": i,
                "score": clean(r.get("score")),
                "owner_name_redacted": redact_name(r.get("owner_name")),
                "mail_city": clean(r.get("mail_city")),
                "mail_state": clean(r.get("mail_state")),
                "situs_city": clean(r.get("situs_city")),
                "situs_state": clean(r.get("situs_state")),
                "parcel_id": clean(r.get("parcel_id")),
                "market_value": clean(r.get("market_value")),
                "distress_signal": clean(r.get("distress_signal")),
                "score_reason": clean(r.get("score_reason")),
                "lane": lane,
                "county": county,
            })
    states={}
    for r in rows:
        s=clean(r.get("mail_state")).upper() or "UNKNOWN"
        states[s]=states.get(s,0)+1
    meta={
        "product_name": product_name,
        "market": market,
        "lane": lane,
        "county": county,
        "state": state,
        "source_url": source_url,
        "source_date": DATE,
        "delivered_rows": len(rows),
        "preview_rows": min(PREVIEW_N, len(rows)),
        "score_range": [money(rows[-1].get("score")) if rows else 0, money(rows[0].get("score")) if rows else 0],
        "owner_mail_state_breakdown": dict(sorted(states.items(), key=lambda kv:-kv[1])[:25]),
        "compliance_note": COMPLIANCE,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "files": {"snapshot_csv": str(full_path), "preview_csv": str(preview_path)},
    }
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(json.dumps(meta, indent=2))
    return meta


def arcgis_features(url, where, out_fields="*", order_by=None, limit=TOP_N, page_size=1000):
    got=0; offset=0
    sess=requests.Session()
    while got < limit:
        n=min(page_size, limit-got)
        params={"f":"json","where":where,"outFields":out_fields,"returnGeometry":"false","resultOffset":offset,"resultRecordCount":n}
        if order_by:
            params["orderByFields"] = order_by
        for attempt in range(4):
            r=sess.get(url.rstrip('/') + '/query', params=params, timeout=90)
            if r.status_code == 200:
                try:
                    data=r.json(); break
                except Exception:
                    pass
            if attempt == 3:
                raise RuntimeError(f"ArcGIS query failed {r.status_code}: {r.text[:500]}")
            time.sleep(2*(attempt+1))
        feats=data.get("features", [])
        if not feats:
            break
        for f in feats:
            yield f.get("attributes", {})
            got += 1
            if got >= limit:
                break
        if len(feats) < n or not data.get("exceededTransferLimit", True):
            break
        offset += len(feats)


def process_guilford():
    src = RAWROOT / "guilford-nc" / DATE / "tax-delinquent-report.csv"
    rows=[]; total=0
    with src.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            total += 1
            owner=clean(r.get("OWNER_NAME")); due=money(r.get("TOTAL_DUE_AMOUNT")); val=money(r.get("PROP_ASSESS_VALUE"))
            if not owner or due <= 0: continue
            mail_state=clean(r.get("MAIL_STATE")).upper()
            absentee = mail_state and mail_state != "NC"
            score = min(100, due/100) + min(50, val/10000) + (25 if absentee else 0)
            rows.append({
                "score": round(score,2), "owner_name": owner, "mail_address": " ".join(filter(None,[clean(r.get('MAIL_ADDR1')), clean(r.get('MAIL_ADDR2')), clean(r.get('MAIL_ADDR3'))])),
                "mail_city": clean(r.get("MAIL_CITY")), "mail_state": mail_state, "mail_zip": clean(r.get("MAIL_ZIP")),
                "parcel_id": clean(r.get("PARCEL_NUM")), "market_value": val, "distress_signal": f"tax delinquent ${due:,.0f}",
                "score_reason": f"unpaid tax balance + assessed value" + (" + absentee owner" if absentee else ""),
            })
    meta=write_snapshot("guilford-nc", "Guilford NC Tax Delinquent Snapshot", rows, "https://open-data-hub-guilfordgis.hub.arcgis.com/api/download/v1/items/cd3e1ae082b0406aa12ca6bbfbe1b741/csv?layers=0", "tax-delinquent", "Guilford", "NC")
    meta["source_total_rows"] = total
    (SNAPROOT/"guilford-nc"/DATE/"meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def latest_raw_file(market, filename):
    preferred = RAWROOT / market / DATE / filename
    if preferred.exists():
        return preferred
    candidates = sorted((RAWROOT / market).glob(f"*/{filename}"), reverse=True)
    if not candidates:
        raise FileNotFoundError(preferred)
    return candidates[0]


def process_forsyth():
    src = latest_raw_file("forsyth-nc", "parcels.csv")
    rows=[]; total=0
    with src.open(newline="", encoding="utf-8-sig", errors="replace") as f:
        for r in csv.DictReader(f):
            total += 1
            owner=" ".join(filter(None,[clean(r.get("CURRENTOWNERNAME1")), clean(r.get("CURRENTOWNERNAME2"))]))
            if not owner: continue
            val=money(r.get("TOTALVALUE")); built=clean(r.get("RESCOMYRBLT")); mail_state=state_from_citystzip(r.get("CURRENTOWNERCITYSTZIP"))
            absentee = mail_state and mail_state != "NC"
            age_pts=0
            try:
                age_pts=min(35, max(0, 2026-int(built))/2) if built else 0
            except Exception: pass
            score=min(80,val/10000)+age_pts+(25 if absentee else 0)
            cityst=clean(r.get("CURRENTOWNERCITYSTZIP"))
            rows.append({
                "score": round(score,2), "owner_name": owner, "mail_address": clean(r.get("CURRENTOWNERADDRESS")), "mail_city": cityst,
                "mail_state": mail_state, "situs_address": clean(r.get("PROPERTYADDRESS")), "situs_state":"NC", "parcel_id": clean(r.get("PIN")) or clean(r.get("TAXPIN")),
                "market_value": val, "year_built": built, "acreage": clean(r.get("ACREAGE")), "distress_signal": "absentee/aged/value signal" if absentee or age_pts else "value-ranked parcel owner",
                "score_reason": "assessed value + owner mailing state + building age",
            })
    meta=write_snapshot("forsyth-nc", "Forsyth NC Parcel Owner Snapshot", rows, "https://www.mapforsyth.org/api/download/v1/items/fd915221da64453aad7989b05f06707e/csv?layers=0", "parcel-owner-ranked", "Forsyth", "NC")
    meta["source_total_rows"] = total
    (SNAPROOT/"forsyth-nc"/DATE/"meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def process_dekalb():
    url="https://dcgis.dekalbcountyga.gov/mapping/rest/services/TaxParcels/MapServer/0"
    rows=[]
    where="OWNERNME1 IS NOT NULL AND PSTLSTATE IS NOT NULL AND PSTLSTATE <> 'GA'"
    for r in arcgis_features(url, where=where, order_by="TOTAPR1 DESC", limit=TOP_N, page_size=2000):
        val=money(r.get("TOTAPR1")) or money(r.get("CNTASSDVAL"))
        owner=" ".join(filter(None,[clean(r.get("OWNERNME1")), clean(r.get("OWNERNME2"))]))
        if not owner: continue
        rows.append({
            "score": round(min(100,val/10000)+25,2), "owner_name": owner, "mail_address": clean(r.get("PSTLADDRESS")), "mail_city": clean(r.get("PSTLCITY")), "mail_state": clean(r.get("PSTLSTATE")).upper(), "mail_zip": clean(r.get("PSTLZIP5")),
            "situs_address": clean(r.get("SITEADDRESS")), "situs_city": clean(r.get("CITY")), "situs_state":"GA", "situs_zip": clean(r.get("ZIP")), "parcel_id": clean(r.get("PARCELID")),
            "market_value": val, "acreage": clean(r.get("ACREAGE")), "distress_signal":"out-of-state absentee owner", "score_reason":"top appraised value among out-of-state owners",
        })
    write_snapshot("dekalb-ga", "DeKalb GA Absentee Parcel Owner Snapshot", rows, url, "absentee-parcel-owner-ranked", "DeKalb", "GA")


def process_marion():
    url="https://gis.indy.gov/server/rest/services/MapIndy/MapIndyProperty/MapServer/10"
    rows=[]
    where="FULLOWNERNAME IS NOT NULL AND OWNERSTATE IS NOT NULL AND OWNERSTATE <> 'IN'"
    for r in arcgis_features(url, where=where, out_fields="*", order_by="ASSESSORYEAR_TOTALAV DESC", limit=TOP_N, page_size=1000):
        val=money(r.get("ASSESSORYEAR_TOTALAV")); owner=clean(r.get("FULLOWNERNAME"))
        if not owner: continue
        situs=" ".join(filter(None,[clean(r.get("STNUMBER")), clean(r.get("PRE_DIR")), clean(r.get("STREET_NAME")), clean(r.get("SUFFIX")), clean(r.get("SUF_DIR"))])) or clean(r.get("FULL_STNAME"))
        rows.append({
            "score": round(min(100,val/10000)+25,2), "owner_name": owner, "mail_address": clean(r.get("OWNERADDRESS")), "mail_city": clean(r.get("OWNERCITY")), "mail_state": clean(r.get("OWNERSTATE")).upper(), "mail_zip": clean(r.get("OWNERZIP")),
            "situs_address": situs, "situs_city": clean(r.get("CITY")), "situs_state":"IN", "situs_zip": clean(r.get("ZIPCODE")), "parcel_id": clean(r.get("PARCEL_TAG")) or clean(r.get("STATEPARCELNUMBER")),
            "market_value": val, "acreage": clean(r.get("ACREAGE")), "distress_signal":"out-of-state absentee owner", "score_reason":"top assessed value among out-of-state owners", "lane":"absentee-parcel-owner-ranked",
        })
    write_snapshot("marion-in", "Marion IN Absentee Parcel Owner Snapshot", rows, url, "absentee-parcel-owner-ranked", "Marion", "IN")


if __name__ == "__main__":
    process_guilford()
    process_forsyth()
    process_dekalb()
    process_marion()
