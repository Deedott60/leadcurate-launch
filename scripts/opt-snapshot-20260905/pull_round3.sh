#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="LeadCurate-1.0"
BASE=/opt/leadcurate/raw_imports

mkdir -p "$BASE/maricopa-az/$DATE/datasets"

echo "=== Probe each Maricopa ArcGIS dataset to find names ==="
MARICOPA_IDS=(
  06135128284149c4bf872d03aa1901f1
  0b5770a1b73f4637b8f92f088465890b
  0e40c41c13eb4ae7ae2811daa6ec42fd
  12ce08cf4d264f9d97bb7ef4d6eb9944
  41748ea2b5284e69b379455974b44428
  604707186f8b4100b6d0a09d0679eec2
  936bbba512bf4c368618cc6e79e64668
  a56a15b7563b4757962588b23358bca1
  b879b43734be496eb7d98ac93c2f222c
  c3f08de3057b4ebda9165fb3e6cc274b
  c937f17330f64e64abd41976fc8bb17f
  dbf139379db946e1b10a2f15672c142d
  e22983d41d91490d90965544b718a120
  efa5c41c405e432e9162459ad2589d16
  f3484c72a938497286adc4e5de7e9963
  fd86f94d3e934b97985547cf234ba36e
)
for id in "${MARICOPA_IDS[@]}"; do
  meta=$(curl -sS -A "$UA" --max-time 10 "https://www.arcgis.com/sharing/rest/content/items/${id}?f=json" 2>/dev/null)
  title=$(echo "$meta" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('title','?'),'|', d.get('type','?'),'|',d.get('numViews','?'),'views')" 2>/dev/null)
  echo "$id  $title"
done

echo ""
echo "=== Maricopa DCAT catalog (master list with download URLs) ==="
curl -sS -A "$UA" --max-time 30 -L -o "$BASE/maricopa-az/$DATE/dcat.json" "https://data-maricopa.opendata.arcgis.com/api/feed/dcat-us/1.1.json" -w "HTTP %{http_code} size %{size_download}\n"
python3 - <<'PY'
import json, os
date=os.popen('date -u +%Y-%m-%d').read().strip()
try:
    d=json.load(open(f'/opt/leadcurate/raw_imports/maricopa-az/{date}/dcat.json'))
    hits=0
    for ds in d.get('dataset', []):
        title = ds.get('title','')
        kw = title.lower()
        if any(k in kw for k in ('parcel','property','tax','assess','owner','delinq')):
            hits+=1
            print('-',title)
            for dist in ds.get('distribution', []):
                fmt = dist.get('format') or '?'
                url = dist.get('downloadURL') or dist.get('accessURL') or '?'
                if 'csv' in str(fmt).lower() or 'csv' in str(url).lower():
                    print('    CSV:',url)
    print(f'\n[{hits} relevant datasets]')
except Exception as e:
    print('parse error:', e)
PY

echo ""
echo "=== Hunt for ArcGIS open data hubs on more counties ==="
for ENTRY in \
  "mecklenburg-nc:https://data.charlottenc.gov/api/feed/dcat-us/1.1.json" \
  "mecklenburg-nc:https://data.mecklenburgcountync.gov/api/feed/dcat-us/1.1.json" \
  "wake-nc:https://data.wake.gov/api/feed/dcat-us/1.1.json" \
  "wake-nc:https://data.wakegov.com/api/feed/dcat-us/1.1.json" \
  "cuyahoga-oh:https://data.cuyahogacounty.gov/api/feed/dcat-us/1.1.json" \
  "marion-in:https://data.indy.gov/api/feed/dcat-us/1.1.json" \
  "fulton-ga:https://gisdata.fultoncountyga.gov/api/feed/dcat-us/1.1.json" \
  ; do
  county="${ENTRY%%:*}"
  url="${ENTRY#*:}"
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 15 -L "$url")
  echo "$code  $county  $url"
  if [ "$code" = "200" ]; then
    mkdir -p "$BASE/$county/$DATE"
    curl -sS -A "$UA" --max-time 30 -L -o "$BASE/$county/$DATE/dcat.json" "$url"
    echo "  saved to $BASE/$county/$DATE/dcat.json"
  fi
done

echo ""
echo "=== Jefferson AL — multiple URL probes ==="
mkdir -p "$BASE/jefferson-al/$DATE"
for url in \
  "https://www.jccal.org/Default.asp?ID=368" \
  "https://www.jccal.org/Default.asp?ID=2310" \
  "https://eringcapture.jccal.org/DelqSearch" \
  "https://eringcapture.jccal.org/collection" \
  ; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 15 -L "$url")
  echo "$code  $url"
done

echo ""
echo "=== Harris TX HCAD bulk data — try multiple paths ==="
mkdir -p "$BASE/harris-tx/$DATE"
for url in \
  "https://download.hcad.org/data/CAMA/Real_acct_owner.zip" \
  "https://pdata.hcad.org/data/cama/2026/Real_acct_owner.zip" \
  "https://pdata.hcad.org/" \
  "https://hcad.org/hcad-resources/hcad-public-data" \
  ; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 30 -L "$url")
  echo "$code  $url"
done

echo ""
echo "=== TOTAL DATA ON DISK ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
