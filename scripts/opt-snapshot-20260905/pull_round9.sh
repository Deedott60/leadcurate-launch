#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="Mozilla/5.0 LeadCurate"
BASE=/opt/leadcurate/raw_imports

echo "=== Harris TX HCAD — bulk zip downloads ==="
mkdir -p "$BASE/harris-tx/$DATE"
for ZIP in Real_acct_owner Real_acct_history Real_building_land Real_jur_exempt Real_pp_files Real_subdivision Real_neighborhood_code; do
  echo "-- $ZIP --"
  curl -sS -A "$UA" -L -o "$BASE/harris-tx/$DATE/${ZIP}.zip" "http://pdata.hcad.org/data/cama/2026/${ZIP}.zip" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
  ls -lh "$BASE/harris-tx/$DATE/${ZIP}.zip" 2>/dev/null
done

echo ""
echo "=== Allen IN — 2025 Delinquent Property document ==="
mkdir -p "$BASE/allen-in/$DATE"
curl -sS -A "$UA" -L -o "$BASE/allen-in/$DATE/2025-delinquent-property.pdf" "https://www.allencounty.in.gov/DocumentCenter/View/11377/2025-Delinquent-Property" --max-time 120 -w "HTTP %{http_code} size %{size_download}\n"
ls -lh "$BASE/allen-in/$DATE/2025-delinquent-property.pdf" 2>/dev/null
file "$BASE/allen-in/$DATE/2025-delinquent-property.pdf" 2>/dev/null

echo ""
echo "=== Erie NY — filed list of delinquent taxes + petition + redemption stmts ==="
mkdir -p "$BASE/erie-ny/$DATE"
for path in \
  "2026-05/filed-list-of-delinquent-taxes-9691950.1.pdf" \
  "2026-05/filed-petition-notice.pdf" \
  "2026-03/in-rem-173-tax-lien-foreclosure-information-and-frequently-asked-questions-updated-as-of-2-24-2026.PDF" \
  "2026-05/homeowner-warning-notice-pursuant-to-rptl-1144.pdf" \
  "2026-05/in-rem-174-frequently-asked-questions.pdf" \
  "2026-01/filed-judgment-of-foreclosure-and-sale.pdf" \
  "2026-01/filed-third-collective-stmt-of-redemptions.pdf" \
  "2025-12/first-collective-statement.pdf" \
  "2025-12/second-collective-statement.pdf" \
  "2025-09/petition-and-notice-of-in-rem-foreclosure-as-filed-with-the-erie-county-clerk-on-september-9-2025.pdf" \
  ; do
  url="https://www3.erie.gov/ecrpts/sites/www3.erie.gov.ecrpts/files/${path}"
  fname=$(basename "$path")
  curl -sS -A "$UA" -L -o "$BASE/erie-ny/$DATE/${fname}" "$url" --max-time 120 -w "$fname: HTTP %{http_code} size %{size_download}\n"
done
ls -lh "$BASE/erie-ny/$DATE"/*.pdf "$BASE/erie-ny/$DATE"/*.PDF 2>/dev/null

echo ""
echo "=== DeKalb GA — parse DCAT for property/tax datasets ==="
mkdir -p "$BASE/dekalb-ga/$DATE"
python3 - <<'PY'
import json, os
date = os.popen('date -u +%Y-%m-%d').read().strip()
import glob
for path in glob.glob(f'/opt/leadcurate/raw_imports/dekalb-ga/{date}/dcat-*.json'):
    print(f'\n=== {path} ===')
    try:
        d = json.load(open(path))
        hits = 0
        for ds in d.get('dataset', []):
            t = ds.get('title','')
            if any(k in t.lower() for k in ('parcel','property','tax','owner','delinq','foreclos','vacant','lien','assess','land')):
                hits += 1
                print('-', t[:70])
                for dist in ds.get('distribution', []):
                    fmt = (dist.get('format') or '').lower()
                    url = dist.get('downloadURL') or dist.get('accessURL') or ''
                    if fmt == 'csv' or url.endswith('.csv'):
                        print('   CSV:', url[:200])
                        break
        print(f'  [{hits} relevant]')
    except Exception as e:
        print('error:', e)
PY

echo ""
echo "=== Forsyth NC — parse MapForsyth DCAT ==="
mkdir -p "$BASE/forsyth-nc/$DATE"
python3 - <<'PY'
import json, os, glob
date = os.popen('date -u +%Y-%m-%d').read().strip()
for path in glob.glob(f'/opt/leadcurate/raw_imports/forsyth-nc/{date}/dcat-*.json'):
    print(f'\n=== {path} ===')
    try:
        d = json.load(open(path))
        hits = 0
        for ds in d.get('dataset', []):
            t = ds.get('title','')
            if any(k in t.lower() for k in ('parcel','property','tax','owner','delinq','foreclos','vacant','lien','assess','land')):
                hits += 1
                print('-', t[:70])
                for dist in ds.get('distribution', []):
                    fmt = (dist.get('format') or '').lower()
                    url = dist.get('downloadURL') or dist.get('accessURL') or ''
                    if fmt == 'csv' or url.endswith('.csv'):
                        print('   CSV:', url[:200])
                        break
        print(f'  [{hits} relevant]')
    except Exception as e:
        print('error:', e)
PY

echo ""
echo "=== Dallas DCAD — drill into DataProducts and GISDataProducts ==="
mkdir -p "$BASE/dallas-tx/$DATE"
curl -sS -A "$UA" -L -o "$BASE/dallas-tx/$DATE/data-products.html" "https://www.dallascad.org/DataProducts.aspx" --max-time 30 -w "DataProducts HTTP %{http_code} size %{size_download}\n"
curl -sS -A "$UA" -L -o "$BASE/dallas-tx/$DATE/gis-data-products.html" "https://www.dallascad.org/GISDataProducts.aspx" --max-time 30 -w "GISDataProducts HTTP %{http_code} size %{size_download}\n"
echo "--- file/zip links on DataProducts ---"
grep -oiE 'href="[^"]+"' "$BASE/dallas-tx/$DATE/data-products.html" 2>/dev/null | grep -iE 'zip|csv|xls|pdf|data|download' | sort -u | head -20
echo "--- file/zip links on GISDataProducts ---"
grep -oiE 'href="[^"]+"' "$BASE/dallas-tx/$DATE/gis-data-products.html" 2>/dev/null | grep -iE 'zip|csv|xls|pdf|data|download' | sort -u | head -20

echo ""
echo "=== Cobb GA — find current delinquent PDF via revize ==="
# Use direct page search since URL pattern changed
curl -sS -A "$UA" -L -o "$BASE/cobb-ga/$DATE/page-fresh.html" "https://www.cobbtax.gov/property/delinquent_taxes/index.php" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- ALL PDF links ---"
grep -oiE 'href="[^"]+\.pdf"' "$BASE/cobb-ga/$DATE/page-fresh.html" 2>/dev/null | sort -u | head -10
grep -oiE 'href="[^"]+"' "$BASE/cobb-ga/$DATE/page-fresh.html" 2>/dev/null | grep -iE 'revize|delinq' | sort -u | head -10

echo ""
echo "=== Jefferson AL — try with pg parameter for 2024 ==="
curl -sS -A "$UA" -L -o "$BASE/jefferson-al/$DATE/2024-parcels.html" "https://www.jccal.org/Default.asp?ID=2663&pg=2024+tax+delinquent+parcels+for+the+Birmingham+District" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- excel links on 2024 page ---"
grep -oiE 'href="[^"]+"' "$BASE/jefferson-al/$DATE/2024-parcels.html" 2>/dev/null | grep -iE '\.xls|\.xlsx|excel|delinq|parcel|tax' | sort -u | head -20

echo ""
echo "=== TOTAL ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
du -sh /opt/leadcurate/raw_imports
