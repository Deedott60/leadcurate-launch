#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
WAKE_DATE=$(date -u +%m%d%Y)
UA="LeadCurate-1.0"
BASE=/opt/leadcurate/raw_imports

# Ensure all per-county date folders exist
for c in tarrant-tx harris-tx maricopa-az jefferson-al wake-nc marion-in cuyahoga-oh allen-in fayette-ky jefferson-ky erie-ny; do
  mkdir -p "$BASE/$c/$DATE"
done

echo "=== Tarrant TX weekly tax roll zip (retry) ==="
curl -sS -A "$UA" -L -o "$BASE/tarrant-tx/$DATE/tax-roll.zip" "https://www.tarrantcountytx.gov/content/dam/main/tax/tax-rolls/2026/TaxRoll20260612.zip" --max-time 600 -w "HTTP %{http_code} size %{size_download} bytes time %{time_total}s\n"
ls -lh "$BASE/tarrant-tx/$DATE/tax-roll.zip" 2>/dev/null
if [ -s "$BASE/tarrant-tx/$DATE/tax-roll.zip" ]; then
  echo "--- Tarrant zip contents ---"
  unzip -l "$BASE/tarrant-tx/$DATE/tax-roll.zip" 2>&1 | head -20
fi

echo ""
echo "=== Wake NC delinquent file — try today's date ${WAKE_DATE} ==="
# Try yesterday and today since cadence is daily
for d in $(date -u +%m%d%Y) $(date -u -d 'yesterday' +%m%d%Y 2>/dev/null) $(date -u -d '2 days ago' +%m%d%Y 2>/dev/null) $(date -u -d '3 days ago' +%m%d%Y 2>/dev/null); do
  for fmt in xlsx zip; do
    url="https://services.wake.gov/collection_extracts/Real_Estate_Delq853_${d}.${fmt}"
    code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" -L --max-time 15 "$url" 2>&1)
    echo "$code  $url"
    if [ "$code" = "200" ]; then
      curl -sS -A "$UA" -L -o "$BASE/wake-nc/$DATE/delinquent.${fmt}" "$url" --max-time 180 -w "downloaded %{size_download} bytes\n"
      ls -lh "$BASE/wake-nc/$DATE/delinquent.${fmt}"
      break 2
    fi
  done
done

echo ""
echo "=== Wake NC full tax bill file probe ==="
for d in $(date -u +%m%d%Y) $(date -u -d 'yesterday' +%m%d%Y); do
  url="https://services.wake.gov/collection_extracts/Real_Estate_Full853_${d}.zip"
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" -L --max-time 15 "$url")
  echo "$code  $url"
  if [ "$code" = "200" ]; then
    curl -sS -A "$UA" -L -o "$BASE/wake-nc/$DATE/full-bill.zip" "$url" --max-time 300 -w "downloaded %{size_download} bytes\n"
    break
  fi
done

echo ""
echo "=== Maricopa AZ data sales page ==="
curl -sS -A "$UA" -k -L -o "$BASE/maricopa-az/$DATE/page.html" "https://www.mcassessor.maricopa.gov/page/data_sales/" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- file links on page ---"
grep -oE 'href="[^"]+"' "$BASE/maricopa-az/$DATE/page.html" 2>/dev/null | grep -iE 'csv|txt|zip|xlsx|xls|download|data' | sort -u | head -25

echo ""
echo "=== Charlotte Mecklenburg open data — search delinquent ==="
mkdir -p "$BASE/mecklenburg-nc/$DATE"
curl -sS -A "$UA" --max-time 30 "https://data.charlottenc.gov/api/catalog/v1?q=delinquent&limit=20" -o "$BASE/mecklenburg-nc/$DATE/catalog-search.json" -w "HTTP %{http_code} size %{size_download}\n"
python3 -c "
import json
d = json.load(open('$BASE/mecklenburg-nc/$DATE/catalog-search.json'))
print('total results:', d.get('resultSetSize', '?'))
for r in d.get('results', [])[:15]:
    res = r.get('resource', {})
    print(' -', res.get('name', '?'), '::', res.get('id', '?'))
" 2>&1 | head -20

echo ""
echo "=== Charlotte Mecklenburg open data — search property tax ==="
curl -sS -A "$UA" --max-time 30 "https://data.charlottenc.gov/api/catalog/v1?q=property+tax&limit=20" -o "$BASE/mecklenburg-nc/$DATE/catalog-property-tax.json" -w "HTTP %{http_code} size %{size_download}\n"
python3 -c "
import json
d = json.load(open('$BASE/mecklenburg-nc/$DATE/catalog-property-tax.json'))
print('total results:', d.get('resultSetSize', '?'))
for r in d.get('results', [])[:15]:
    res = r.get('resource', {})
    print(' -', res.get('name', '?'), '::', res.get('id', '?'))
" 2>&1 | head -20

echo ""
echo "=== Jefferson AL — try main delinquent page ==="
curl -sS -A "$UA" -L -o "$BASE/jefferson-al/$DATE/landing.html" "https://www.jccal.org/Default.asp?ID=2310" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
grep -oE 'href="[^"]+"' "$BASE/jefferson-al/$DATE/landing.html" 2>/dev/null | grep -iE 'delinq|tax|excel|xls|csv|pdf' | sort -u | head -20

echo ""
echo "=== TOTAL DATA ON DISK ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
