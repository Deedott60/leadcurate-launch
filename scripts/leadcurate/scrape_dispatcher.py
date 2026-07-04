#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib import request

RAW_ROOT = Path("/opt/leadcurate/raw_imports")
SCRIPT_ROOT = Path("/opt/leadcurate")
SCRIPT_DIR = Path("/opt/leadcurate/scripts")

SOURCES = {
    ("wake-nc", "tax-delinquent"): {"url": "https://services.wake.gov/realestate/", "scraper": "tax-delinquent/wake-nc.py", "pattern": "delinquent*.xlsx"},
    ("mecklenburg-nc", "tax-delinquent"): {"url": "https://data.charlottenc.gov/", "scraper": "tax-delinquent/mecklenburg-nc.py", "pattern": "parcel-lookup.csv"},
    ("mecklenburg-nc", "probate"): {"url": "https://meckrod.manatron.com/", "scraper": "probate/mecklenburg-nc.py", "pattern": "mecklenburg-probate.csv"},
    ("harris-tx", "tax-delinquent"): {"url": "https://pdata.hcad.org/", "scraper": "tax-delinquent/harris-tx.py", "pattern": "real_acct.txt"},
    ("harris-tx", "active-permits"): {"url": "https://pdata.hcad.org/", "scraper": "active-permits/harris-tx.py", "pattern": "permits.txt"},
    ("cobb-ga", "tax-delinquent"): {"url": "https://www.cobbtax.org/", "scraper": "tax-delinquent/cobb-ga.py", "pattern": "*.pdf"},
    ("fulton-ga", "tax-delinquent"): {"url": "https://data.fultoncountyga.gov/", "scraper": "tax-delinquent/fulton-ga.py", "pattern": "tax-parcels-2025.csv"},
    ("jefferson-ky", "code-violations"): {"url": "https://jeffersonpva.ky.gov/property-search/", "cmd": ["enrich_jefferson_ky_code_violations.py", "--limit", "1000"], "pattern": "property-maintenance-violations-enriched.csv"},
    ("duval-fl", "individual-homeowner"): {"url": "https://maps.clayutility.org/server/rest/services/ParcelsHybridv2_LGIM/MapServer/14", "cmd": ["arcgis_property_pull.py", "--market", "duval-fl", "--limit", "8000"], "pattern": "parcels.csv"},
    ("davidson-tn", "individual-homeowner"): {"url": "https://datanashvillegov-nashville.hub.arcgis.com/datasets/fa26cd9326c446179be059e00449cb1f_0/about", "cmd": ["arcgis_property_pull.py", "--market", "davidson-tn", "--limit", "8000"], "pattern": "parcels.csv"},
    ("york-sc", "individual-homeowner"): {"url": "https://www.yorkcountysc.gov/239/GIS-Data-Download", "cmd": ["arcgis_property_pull.py", "--market", "york-sc", "--limit", "8000"], "pattern": "parcels.csv"},
    ("cabarrus-nc", "individual-homeowner"): {"url": "https://gis-cabarrus.opendata.arcgis.com/", "cmd": ["arcgis_property_pull.py", "--market", "cabarrus-nc", "--limit", "8000"], "pattern": "parcels.csv"},
    ("lancaster-sc", "individual-homeowner"): {"url": "https://lancaster-launch-lancogis.hub.arcgis.com/pages/2f49a6ade70a4197bcdaeb3202cedbf7", "cmd": ["arcgis_property_pull.py", "--market", "lancaster-sc", "--limit", "8000"], "pattern": "parcels.csv"},
    ("gaston-nc", "individual-homeowner"): {"url": "https://gis.gastoncountync.gov/publicgis/rest/services/PublicGIS/Parcels/MapServer/layers", "cmd": ["arcgis_property_pull.py", "--market", "gaston-nc", "--limit", "8000"], "pattern": "parcels.csv"},
    ("tarrant-tx", "tax-delinquent"): {"url": "local raw_imports tax-roll.zip", "cmd": ["extract_tarrant_tx.py", "--limit", "10000"], "pattern": "tax-roll-extracted.csv"},
    ("maricopa-az", "individual-homeowner"): {"url": "local raw_imports Maricopa master ZIPs", "cmd": ["extract_maricopa_az.py", "--limit", "10000"], "pattern": "parcels-extracted.csv"},
    ("maricopa-az", "high-equity"): {"url": "local raw_imports Maricopa master ZIPs", "cmd": ["extract_maricopa_az.py", "--limit", "10000"], "pattern": "parcels-extracted.csv"},
}

SB_URL = os.environ.get("SUPABASE_URL", "https://jdmlsraqioigbukspduo.supabase.co")
SB_KEY = os.environ.get("SUPABASE_PUBLISHABLE_KEY", "sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4")


def post_activity(event_type: str, title: str, body: str = "") -> None:
    payload = json.dumps({"event_type": event_type, "source": "scrape-dispatcher", "title": title, "body": body, "target": "derrick"}).encode()
    req = request.Request(
        f"{SB_URL}/rest/v1/activity_feed",
        data=payload,
        headers={"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Content-Type": "application/json", "Prefer": "return=minimal"},
        method="POST",
    )
    try:
        request.urlopen(req, timeout=15).read()
    except Exception as exc:
        print(f"activity_feed warning: {exc}", file=sys.stderr)


def latest_existing(market: str, pattern: str) -> Path | None:
    root = RAW_ROOT / market
    if not root.exists():
        return None
    candidates = []
    for dated in sorted([p for p in root.iterdir() if p.is_dir()], key=lambda p: p.name, reverse=True):
        candidates.extend(dated.glob(pattern))
        if candidates:
            break
    candidates.extend(root.glob(pattern))
    candidates = [p for p in candidates if p.is_file()]
    return sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)[0] if candidates else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True)
    parser.add_argument("--lane", required=True)
    args = parser.parse_args()
    key = (args.market, args.lane)
    source = SOURCES.get(key)
    if not source:
        message = f"Source URL needed for {args.market}/{args.lane}. Add to registry first."
        post_activity("scrape:blocker", f"Scrape source needed: {args.market}/{args.lane}", message)
        print(message, file=sys.stderr)
        return 1

    existing = latest_existing(args.market, source["pattern"])
    if existing:
        print(existing)
        return 0

    out_dir = RAW_ROOT / args.market / date.today().isoformat()
    out_dir.mkdir(parents=True, exist_ok=True)
    post_activity("scrape:started", f"Scrape started: {args.market}/{args.lane}", source["url"])
    if source.get("cmd"):
        cmd = [sys.executable, str(SCRIPT_DIR / source["cmd"][0]), *source["cmd"][1:]]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        if proc.returncode != 0:
            body = (proc.stdout + "\n" + proc.stderr).strip()[-1500:]
            post_activity("scrape:failed", f"Scrape failed: {args.market}/{args.lane}", body)
            print(body, file=sys.stderr)
            return proc.returncode
        produced = latest_existing(args.market, source["pattern"]) or out_dir
        post_activity("scrape:done", f"Scrape done: {args.market}/{args.lane}", str(produced))
        print(produced)
        return 0

    scraper = SCRIPT_ROOT / "scrapers" / source["scraper"]
    if not scraper.exists():
        message = f"Scraper missing: {scraper}"
        post_activity("scrape:failed", f"Scrape failed: {args.market}/{args.lane}", message)
        print(message, file=sys.stderr)
        return 1

    proc = subprocess.run([sys.executable, str(scraper), "--output-dir", str(out_dir)], text=True, capture_output=True)
    if proc.returncode != 0:
        body = (proc.stdout + "\n" + proc.stderr).strip()[-1500:]
        post_activity("scrape:failed", f"Scrape failed: {args.market}/{args.lane}", body)
        print(body, file=sys.stderr)
        return proc.returncode
    produced = latest_existing(args.market, source["pattern"]) or out_dir
    post_activity("scrape:done", f"Scrape done: {args.market}/{args.lane}", str(produced))
    print(produced)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
