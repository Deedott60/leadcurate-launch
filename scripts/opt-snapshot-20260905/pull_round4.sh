#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="LeadCurate-1.0"
BASE=/opt/leadcurate/raw_imports

echo "=== Harris TX HCAD Real_acct_owner.zip ==="
mkdir -p "$BASE/harris-tx/$DATE"
curl -sS -A "$UA" -L -o "$BASE/harris-tx/$DATE/real-acct-owner.zip" "https://pdata.hcad.org/data/cama/2026/Real_acct_owner.zip" --max-time 600 -w "HTTP %{http_code} size %{size_download} bytes time %{time_total}s\n"
ls -lh "$BASE/harris-tx/$DATE/real-acct-owner.zip" 2>/dev/null
if [ -s "$BASE/harris-tx/$DATE/real-acct-owner.zip" ]; then
  echo "--- Harris zip contents ---"
  unzip -l "$BASE/harris-tx/$DATE/real-acct-owner.zip" 2>&1 | head -25
fi

echo ""
echo "=== Re-fetch Fulton DCAT (last attempt timed out) ==="
curl -sS -A "$UA" -L -o "$BASE/fulton-ga/$DATE/dcat.json" "https://gisdata.fultoncountyga.gov/api/feed/dcat-us/1.1.json" --max-time 180 -w "HTTP %{http_code} size %{size_download}\n"

echo ""
for COUNTY in mecklenburg-nc wake-nc marion-in fulton-ga; do
  echo "=== $COUNTY DCAT — property/tax/delinquent datasets ==="
  python3 - <<PY
import json
try:
    d = json.load(open(f'/opt/leadcurate/raw_imports/$COUNTY/$DATE/dcat.json'))
    hits = 0
    for ds in d.get('dataset', []):
        title = ds.get('title','')
        kw = title.lower()
        if any(k in kw for k in ('parcel','property','tax','assess','owner','delinq','foreclos','vacant','lien')):
            hits += 1
            print('-', title[:80])
            for dist in ds.get('distribution', []):
                fmt = (dist.get('format') or '').lower()
                url = dist.get('downloadURL') or dist.get('accessURL') or ''
                if fmt == 'csv' or url.endswith('.csv') or 'csv' in url:
                    print('    CSV:', url[:200])
                elif fmt == 'xlsx' or url.endswith('.xlsx'):
                    print('    XLSX:', url[:200])
    print(f'[{hits} relevant datasets]')
except Exception as e:
    print('parse error:', e)
PY
  echo ""
done

echo "=== Maricopa Secured Master + Residential Master CSV download attempts ==="
mkdir -p "$BASE/maricopa-az/$DATE/secured" "$BASE/maricopa-az/$DATE/residential"
for ID in 936bbba512bf4c368618cc6e79e64668 e22983d41d91490d90965544b718a120; do
  echo "--- item $ID ---"
  meta=$(curl -sS -A "$UA" --max-time 15 "https://www.arcgis.com/sharing/rest/content/items/${ID}/data?f=json" 2>/dev/null)
  echo "$meta" | head -c 800
  echo ""
done

echo ""
echo "=== Jefferson AL — try with -k (insecure SSL) ==="
mkdir -p "$BASE/jefferson-al/$DATE"
for url in \
  "https://eringcapture.jccal.org/DelqSearch" \
  "https://eringcapture.jccal.org/collection" \
  "https://www.jccal.org/Default.asp?ID=2628" \
  "https://www.jccal.org/Sites/Jefferson_County/Documents/Tax%20Collector/2024%20Birmingham%20Delinquent%20Parcels.xlsx" \
  ; do
  code=$(curl -sS -k -o /dev/null -w "%{http_code}" -A "$UA" --max-time 20 -L "$url")
  echo "$code  $url"
done

echo ""
echo "=== ArcGIS hub probes for more counties ==="
for ENTRY in \
  "harris-tx:https://geo-harriscountygis.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "dallas-tx:https://gis.dallascityhall.com/opendata/api/feed/dcat-us/1.1.json" \
  "dallas-tx:https://gis-dallasgis.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "shelby-tn:https://data.shelbycountytn.gov/api/feed/dcat-us/1.1.json" \
  "cuyahoga-oh:https://data.cuyahogacounty.us/api/feed/dcat-us/1.1.json" \
  "cuyahoga-oh:https://data-cuyahoga.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "allen-in:https://data-acgis.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "jefferson-ky:https://data.louisvilleky.gov/api/feed/dcat-us/1.1.json" \
  ; do
  county="${ENTRY%%:*}"
  url="${ENTRY#*:}"
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 12 -L "$url")
  echo "$code  $county  $url"
  if [ "$code" = "200" ]; then
    mkdir -p "$BASE/$county/$DATE"
    curl -sS -A "$UA" --max-time 60 -L -o "$BASE/$county/$DATE/dcat.json" "$url"
  fi
done

echo ""
echo "=== TOTAL DATA ON DISK ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
echo ""
echo "=== GRAND TOTAL ==="
du -sh /opt/leadcurate/raw_imports
