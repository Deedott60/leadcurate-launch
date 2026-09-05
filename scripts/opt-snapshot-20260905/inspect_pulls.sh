#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
cd /opt/leadcurate/raw_imports

echo "=== Guilford ArcGIS catalog — tax-delinquent datasets ==="
python3 - <<'PY'
import json, os
date = os.popen("date -u +%Y-%m-%d").read().strip()
with open(f"guilford-nc/{date}/dcat.json") as f:
    d = json.load(f)
hits = 0
for ds in d.get("dataset", []):
    title = ds.get("title", "")
    if any(k in title.lower() for k in ("delinq", "tax", "parcel", "property")):
        hits += 1
        print("-", title)
        for dist in ds.get("distribution", []):
            fmt = dist.get("format") or dist.get("mediaType") or "?"
            url = dist.get("downloadURL") or dist.get("accessURL") or "?"
            print("   ", fmt, url)
print(f"\n[{hits} matching datasets]")
PY

echo ""
echo "=== Mecklenburg — find data links on page ==="
grep -oE 'href="[^"]+"' "mecklenburg-nc/${DATE}/page.html" | grep -iE 'pdf|csv|xlsx|delinq|list|search' | sort -u | head -20

echo ""
echo "=== Mecklenburg — page text (first 1500 chars) ==="
python3 -c "
import re
with open('mecklenburg-nc/${DATE}/page.html') as f: html = f.read()
txt = re.sub(r'<script.*?</script>', ' ', html, flags=re.S)
txt = re.sub(r'<style.*?</style>', ' ', txt, flags=re.S)
txt = re.sub(r'<[^>]+>', ' ', txt)
txt = re.sub(r'\s+', ' ', txt).strip()
print(txt[:1500])
"

echo ""
echo "=== Forsyth NC — links on advertisement page ==="
grep -oE 'href="[^"]+"' "forsyth-nc/${DATE}/advertisement.html" | grep -iE 'pdf|csv|xlsx|delinq|lien|advert|tax' | sort -u | head -20

echo ""
echo "=== Cobb GA — links on delinquent taxes page ==="
grep -oE 'href="[^"]+"' "cobb-ga/${DATE}/page.html" | grep -iE 'pdf|csv|xlsx|delinq|list|sale|tax' | sort -u | head -20

echo ""
echo "=== DeKalb GA — links on tax sale listing ==="
grep -oE 'href="[^"]+"' "dekalb-ga/${DATE}/page.html" | grep -iE 'pdf|csv|xlsx|delinq|list|sale|tax' | sort -u | head -20

echo ""
echo "=== Sizes of raw data on disk ==="
du -sh /opt/leadcurate/raw_imports/*/${DATE} 2>/dev/null | sort -h
