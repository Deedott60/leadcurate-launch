#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="Mozilla/5.0 LeadCurate"
BASE=/opt/leadcurate/raw_imports

echo "=== Fayette KY (Lexington) — pull all 4 property datasets ==="
mkdir -p "$BASE/fayette-ky/$DATE"
declare -A FAYETTE=(
  ["pdr-property.csv"]="https://data.lexingtonky.gov/api/download/v1/items/320fc4939dc74ea293c639f5c4a6beca/csv?layers=0"
  ["parcel.csv"]="https://data.lexingtonky.gov/api/download/v1/items/e4a525d8772741468205e82fc173db22/csv?layers=0"
  ["vacant-land-2010.csv"]="https://data.lexingtonky.gov/api/download/v1/items/ec2e091883834259b99b26b2c1b191be/csv?layers=0"
  ["national-register-property.csv"]="https://data.lexingtonky.gov/api/download/v1/items/8ad0ec81df2c451c897c44a4623967af/csv?layers=0"
)
for path in "${!FAYETTE[@]}"; do
  url="${FAYETTE[$path]}"
  out="$BASE/fayette-ky/$DATE/$path"
  echo "--- $path ---"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 300 -w "HTTP %{http_code} size %{size_download}\n"
  if [ -s "$out" ]; then
    head -c 200 "$out" | grep -q '^{.*Pending' && echo "  (async pending - will retry)" || echo "  rows: $(wc -l < "$out")"
  fi
done

echo ""
echo "=== Forsyth NC Bank Foreclosures dataset ==="
# First, parse DCAT to find the dataset ID
python3 - <<'PY'
import json
try:
    d = json.load(open('/opt/leadcurate/raw_imports/forsyth-nc/2026-06-18/dcat-www.mapforsyth.org.json'))
    for ds in d.get('dataset', []):
        t = ds.get('title', '')
        if 'foreclos' in t.lower() or 'bank' in t.lower():
            print(f'Found: {t}')
            for dist in ds.get('distribution', []):
                fmt = (dist.get('format') or '').lower()
                url = dist.get('downloadURL') or dist.get('accessURL') or ''
                if fmt == 'csv' or url.endswith('.csv'):
                    print(f'  CSV: {url}')
except Exception as e:
    print('error:', e)
PY

# Pull Forsyth Bank Foreclosures and Tax Parcel Viewer additional datasets
mkdir -p "$BASE/forsyth-nc/$DATE"
declare -A FORSYTH=(
  ["bank-foreclosures.csv"]="https://www.mapforsyth.org/api/download/v1/items/d6e7c54bf17a4a59a2b85ddae6df9a37/csv?layers=0"
)
for path in "${!FORSYTH[@]}"; do
  url="${FORSYTH[$path]}"
  out="$BASE/forsyth-nc/$DATE/$path"
  echo "--- $path ---"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 300 -w "HTTP %{http_code} size %{size_download}\n"
done

echo ""
echo "=== NYC additional property datasets ==="
# NYC Open Data has many more datasets — pull a few high-value ones
mkdir -p "$BASE/nyc/$DATE"
# PLUTO (Primary Land Use Tax Lot Output) — every parcel in NYC
declare -A NYC=(
  ["hpd-tax-delinquency.csv"]="https://data.cityofnewyork.us/api/views/8usp-z89r/rows.csv?accessType=DOWNLOAD"
  ["hpd-mortgage.csv"]="https://data.cityofnewyork.us/api/views/td66-tdm6/rows.csv?accessType=DOWNLOAD"
  ["dob-violations.csv"]="https://data.cityofnewyork.us/api/views/3h2n-5cm9/rows.csv?accessType=DOWNLOAD"
)
for path in "${!NYC[@]}"; do
  url="${NYC[$path]}"
  out="$BASE/nyc/$DATE/$path"
  echo "--- $path ---"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
  [ -s "$out" ] && echo "  rows: $(wc -l < "$out")"
done

echo ""
echo "=== Guilford NC — pull additional datasets (Parcels full, Tax Data) ==="
mkdir -p "$BASE/guilford-nc/$DATE"
declare -A GUILFORD=(
  ["county-parcels.csv"]="https://open-data-hub-guilfordgis.hub.arcgis.com/api/download/v1/items/d7775eadfb094a7689eb4b8581109e4e/csv?layers=0"
  ["historical-parcels-2025.csv"]="https://open-data-hub-guilfordgis.hub.arcgis.com/api/download/v1/items/e83bae3d263046b2b83dcaa076df6cf6/csv?layers=30"
)
for path in "${!GUILFORD[@]}"; do
  url="${GUILFORD[$path]}"
  out="$BASE/guilford-nc/$DATE/$path"
  echo "--- $path ---"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
  [ -s "$out" ] && echo "  rows: $(wc -l < "$out" 2>/dev/null || echo 0)"
done

echo ""
echo "=== Charlotte Open Data — additional property/tax datasets ==="
mkdir -p "$BASE/mecklenburg-nc/$DATE"
declare -A CHARLOTTE=(
  ["parcels-full.csv"]="https://data.charlottenc.gov/api/download/v1/items/859c7065d49749ab894e119aac72ab87/csv?layers=3"
  ["historic-district-parcels.csv"]="https://data.charlottenc.gov/api/download/v1/items/3149b2c2874e4d38ac1c46dac46fc834/csv?layers=0"
)
for path in "${!CHARLOTTE[@]}"; do
  url="${CHARLOTTE[$path]}"
  out="$BASE/mecklenburg-nc/$DATE/$path"
  echo "--- $path ---"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
done

echo ""
echo "=== Marion IN (Indianapolis) — additional tax sale + delinquent datasets ==="
mkdir -p "$BASE/marion-in/$DATE"
declare -A MARION=(
  ["parcels-base.csv"]="https://data.indy.gov/api/download/v1/items/458cf4b7d44543d2a3bee3bd92914af9/csv?layers=15"
  ["tif-districts.csv"]="https://data.indy.gov/api/download/v1/items/8c4eacdbe35248cc892649e1d01ad501/csv?layers=15"
)
for path in "${!MARION[@]}"; do
  url="${MARION[$path]}"
  out="$BASE/marion-in/$DATE/$path"
  echo "--- $path ---"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
done

echo ""
echo "=== Fulton GA — pull additional tax parcel years for trending ==="
mkdir -p "$BASE/fulton-ga/$DATE"
declare -A FULTON=(
  ["tax-parcels-2024.csv"]="https://gisdata.fultoncountyga.gov/api/download/v1/items/0486089398034e48a53c3e8512123167/csv?layers=0"
  ["tax-parcels-2023.csv"]="https://gisdata.fultoncountyga.gov/api/download/v1/items/f355d80f6d9e4888928e68ddf67140ae/csv?layers=0"
)
for path in "${!FULTON[@]}"; do
  url="${FULTON[$path]}"
  out="$BASE/fulton-ga/$DATE/$path"
  echo "--- $path ---"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
done

echo ""
echo "=== FINAL DISK USAGE ==="
du -sh /opt/leadcurate/raw_imports
echo ""
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h | tail -20
