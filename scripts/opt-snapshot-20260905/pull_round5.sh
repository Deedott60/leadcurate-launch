#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="LeadCurate-1.0"
BASE=/opt/leadcurate/raw_imports

declare -A PULLS=(
  ["mecklenburg-nc/lien-data.csv"]="https://data.charlottenc.gov/api/download/v1/items/107e93008cbc4430ad2a3afafa839a24/csv?layers=0"
  ["mecklenburg-nc/vacant-land.csv"]="https://data.charlottenc.gov/api/download/v1/items/564477f647634c94a6588d1f57597b30/csv?layers=0"
  ["mecklenburg-nc/parcel-lookup.csv"]="https://data.charlottenc.gov/api/download/v1/items/3cf4a8c868f0476f897fed7e1e8e81c2/csv?layers=4"
  ["wake-nc/property.csv"]="https://data.wakegov.com/api/download/v1/items/758c0774a9b84ee4a1a5bb6db4f8d5de/csv?layers=0"
  ["wake-nc/parcels.csv"]="https://data.wakegov.com/api/download/v1/items/f5ed009c66e844ec82f29064edd95017/csv?layers=0"
  ["marion-in/parcels-owner-assessed.csv"]="https://data.indy.gov/api/download/v1/items/0d28e222479743baa97f8f4456da7bb4/csv?layers=10"
  ["marion-in/hhc-parcel-owner.csv"]="https://data.indy.gov/api/download/v1/items/1dbe42c87bf24d5780bee61907bcbfc2/csv?layers=1"
  ["fulton-ga/current-parcels.csv"]="https://gisdata.fultoncountyga.gov/api/download/v1/items/31006e9cb13a493fbb6c99dbbbea2e4a/csv?layers=0"
  ["fulton-ga/tax-parcels-2025.csv"]="https://gisdata.fultoncountyga.gov/api/download/v1/items/ee82525ee33b49778055622c3a3cf534/csv?layers=0"
  ["fulton-ga/parcels.csv"]="https://gisdata.fultoncountyga.gov/api/download/v1/items/774f52f47ad14a8389af0f851499e4d9/csv?layers=0"
)

echo "=== Bulk download high-value CSV datasets ==="
for path in "${!PULLS[@]}"; do
  url="${PULLS[$path]}"
  out="$BASE/$path"
  mkdir -p "$(dirname "$out")"
  echo "--- $path ---"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
  if [ -s "$out" ]; then
    rows=$(wc -l < "$out" 2>/dev/null)
    head=$(head -1 "$out" 2>/dev/null | cut -c1-200)
    echo "  rows: $rows"
    echo "  header: $head"
  fi
done

echo ""
echo "=== Maricopa Residential Master & Secured Master (binary blob) ==="
mkdir -p "$BASE/maricopa-az/$DATE"
for ID_NAME in \
  "936bbba512bf4c368618cc6e79e64668:secured-master" \
  "e22983d41d91490d90965544b718a120:residential-master" \
  "12ce08cf4d264f9d97bb7ef4d6eb9944:commercial-master" \
  "0b5770a1b73f4637b8f92f088465890b:apartment-master" \
  ; do
  ID="${ID_NAME%%:*}"
  NAME="${ID_NAME#*:}"
  echo "--- $NAME ($ID) ---"
  curl -sS -A "$UA" -L -o "$BASE/maricopa-az/$DATE/${NAME}.zip" "https://www.arcgis.com/sharing/rest/content/items/${ID}/data" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
  if [ -s "$BASE/maricopa-az/$DATE/${NAME}.zip" ]; then
    file "$BASE/maricopa-az/$DATE/${NAME}.zip"
    unzip -l "$BASE/maricopa-az/$DATE/${NAME}.zip" 2>&1 | head -15
  fi
done

echo ""
echo "=== Cuyahoga + Louisville DCAT — property/tax/delinquent ==="
for COUNTY in cuyahoga-oh jefferson-ky; do
  echo "--- $COUNTY ---"
  python3 - <<PY
import json, sys
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
                if fmt == 'csv' or url.endswith('.csv'):
                    print('    CSV:', url[:200])
                elif 'xlsx' in fmt or url.endswith('.xlsx'):
                    print('    XLSX:', url[:200])
    print(f'[{hits} relevant datasets]')
except Exception as e:
    print('parse error:', e)
PY
  echo ""
done

echo ""
echo "=== Jefferson AL — inspect now-reachable pages ==="
mkdir -p "$BASE/jefferson-al/$DATE"
for url_name in \
  "https://eringcapture.jccal.org/DelqSearch:delq-search" \
  "https://eringcapture.jccal.org/collection:collection" \
  ; do
  url="${url_name%%:*}"
  name="${url_name##*:}"
  curl -sS -k -A "$UA" -L -o "$BASE/jefferson-al/$DATE/${name}.html" "$url" --max-time 30 -w "$name: HTTP %{http_code} size %{size_download}\n"
done
echo "--- file links in DelqSearch page ---"
grep -oE 'href="[^"]+"' "$BASE/jefferson-al/$DATE/delq-search.html" 2>/dev/null | sort -u | head -30

echo ""
echo "=== Harris HCAD — find correct bulk URL ==="
curl -sS -A "$UA" -L -o "$BASE/harris-tx/$DATE/pdata-index.html" "https://pdata.hcad.org/" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- links on pdata.hcad.org ---"
grep -oiE 'href="[^"]+"' "$BASE/harris-tx/$DATE/pdata-index.html" 2>/dev/null | grep -iE 'zip|csv|txt|data|cama|real' | sort -u | head -30

echo ""
echo "=== TOTAL DATA ON DISK ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
echo "--- GRAND TOTAL ---"
du -sh /opt/leadcurate/raw_imports
