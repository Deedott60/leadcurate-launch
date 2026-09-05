#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="LeadCurate-1.0"
BASE=/opt/leadcurate/raw_imports

declare -A PULLS=(
  ["jefferson-ky/property-foreclosures.csv"]="https://data.louisvilleky.gov/api/download/v1/items/62c648120ab44b7794f8b484884efaa9/csv?layers=0"
  ["jefferson-ky/lien-holder-final-orders.csv"]="https://data.louisvilleky.gov/api/download/v1/items/8f25a99a0e2347cc871a203ca325ab5e/csv?layers=0"
  ["jefferson-ky/property-maintenance-violations.csv"]="https://data.louisvilleky.gov/api/download/v1/items/1fd891c3301c4c4581b86c338468fbe4/csv?layers=0"
  ["jefferson-ky/parcels.csv"]="https://data.louisvilleky.gov/api/download/v1/items/47085b87ac754d60942ea324a3b0f54f/csv?layers=1"
  ["cuyahoga-oh/tax-parcels.csv"]="https://data-cuyahoga.opendata.arcgis.com/api/download/v1/items/ffaaa1651d5540419469375d680f3245/csv?layers=0"
  ["cuyahoga-oh/parcel-sales-2021-present.csv"]="https://data-cuyahoga.opendata.arcgis.com/api/download/v1/items/234b606bf7304a9f93bcc9e00afb28fc/csv?layers=0"
)

echo "=== Final-round high-value pulls ==="
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
echo "=== Harris HCAD via correct page ==="
mkdir -p "$BASE/harris-tx/$DATE"
curl -sS -A "$UA" -L -o "$BASE/harris-tx/$DATE/property-downloads.html" "https://hcad.org/pdata/pdata-property-downloads.html" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- zip/data links ---"
grep -oiE 'href="[^"]+\.zip"' "$BASE/harris-tx/$DATE/property-downloads.html" 2>/dev/null | sort -u | head -15

echo ""
echo "=== Probe more ArcGIS hubs ==="
for ENTRY in \
  "shelby-tn:https://data-shelbycountygis.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "erie-ny:https://data-erie.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "allen-in:https://data-aggis.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "allen-in:https://maps-fwallencounty.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "fayette-ky:https://data-lfucg.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "fayette-ky:https://data.lexingtonky.gov/api/feed/dcat-us/1.1.json" \
  "charleston-sc:https://data-charlestoncounty.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "charleston-sc:https://gisdata-charlestoncountysc.hub.arcgis.com/api/feed/dcat-us/1.1.json" \
  "dallas-tx:https://dallascityhall-dallasgis.hub.arcgis.com/api/feed/dcat-us/1.1.json" \
  ; do
  county="${ENTRY%%:*}"
  url="${ENTRY#*:}"
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 10 -L "$url")
  echo "$code  $county  $url"
  if [ "$code" = "200" ]; then
    mkdir -p "$BASE/$county/$DATE"
    curl -sS -A "$UA" --max-time 60 -L -o "$BASE/$county/$DATE/dcat.json" "$url"
  fi
done

echo ""
echo "=== Inspect newly captured DCAT hubs ==="
for COUNTY in shelby-tn erie-ny allen-in fayette-ky charleston-sc dallas-tx; do
  if [ -s "$BASE/$COUNTY/$DATE/dcat.json" ]; then
    echo "--- $COUNTY ---"
    python3 - <<PY
import json
try:
    d = json.load(open(f'/opt/leadcurate/raw_imports/$COUNTY/$DATE/dcat.json'))
    hits=0
    for ds in d.get('dataset', []):
        title = ds.get('title','')
        kw = title.lower()
        if any(k in kw for k in ('parcel','property','tax','owner','delinq','foreclos','vacant','lien','assess')):
            hits += 1
            print('-', title[:70])
            for dist in ds.get('distribution', []):
                fmt = (dist.get('format') or '').lower()
                url = dist.get('downloadURL') or dist.get('accessURL') or ''
                if fmt == 'csv' or url.endswith('.csv'):
                    print('   CSV:', url[:200])
                    break
    print(f'  [{hits} relevant]')
except Exception as e:
    print('  parse error:', e)
PY
  fi
done

echo ""
echo "=== FINAL TOTAL DATA ON DISK ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
echo "--- GRAND TOTAL ---"
du -sh /opt/leadcurate/raw_imports
echo ""
echo "=== CSV ROW COUNTS (real data inventory) ==="
find /opt/leadcurate/raw_imports -name "*.csv" -size +10k 2>/dev/null | while read f; do
  rows=$(wc -l < "$f" 2>/dev/null)
  size=$(du -h "$f" | cut -f1)
  rel=$(echo "$f" | sed 's|/opt/leadcurate/raw_imports/||')
  echo "$rows rows  $size  $rel"
done | sort -rn | head -30
