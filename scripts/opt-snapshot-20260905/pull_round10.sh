#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="Mozilla/5.0 LeadCurate"
BASE=/opt/leadcurate/raw_imports

echo "=== Rename Allen IN Excel to xlsx ==="
mv "$BASE/allen-in/$DATE/2025-delinquent-property.pdf" "$BASE/allen-in/$DATE/2025-delinquent-property.xlsx" 2>/dev/null
ls -lh "$BASE/allen-in/$DATE/"

echo ""
echo "=== Find any DCAT we already have on disk for DeKalb, Forsyth, Erie, Allen, Dallas ==="
find $BASE -name "dcat*.json" -newer $BASE/.touch 2>/dev/null; touch $BASE/.touch
find $BASE -name "dcat*.json" -size +1k | xargs ls -lh 2>/dev/null

echo ""
echo "=== Parse DeKalb GA DCAT (from yesterday's folder if any) ==="
for f in $BASE/dekalb-ga/*/dcat-*.json; do
  [ -s "$f" ] || continue
  echo "--- $f ---"
  python3 - <<PY
import json
try:
    d = json.load(open('$f'))
    rel=[]
    for ds in d.get('dataset', []):
        t = ds.get('title','')
        if any(k in t.lower() for k in ('parcel','property','tax','owner','delinq','foreclos','vacant','lien','assess')):
            csv_url=None
            for dist in ds.get('distribution', []):
                fmt = (dist.get('format') or '').lower()
                url = dist.get('downloadURL') or dist.get('accessURL') or ''
                if fmt=='csv' or url.endswith('.csv'):
                    csv_url=url; break
            rel.append((t[:80], csv_url))
    for t,u in rel[:15]:
        print('  -', t)
        if u: print('     CSV:', u[:200])
    print(f'  total: {len(rel)}')
except Exception as e:
    print('error:', e)
PY
done

echo ""
echo "=== Parse Forsyth NC MapForsyth DCAT ==="
for f in $BASE/forsyth-nc/*/dcat-*.json; do
  [ -s "$f" ] || continue
  echo "--- $f ---"
  python3 - <<PY
import json
try:
    d = json.load(open('$f'))
    rel=[]
    for ds in d.get('dataset', []):
        t = ds.get('title','')
        if any(k in t.lower() for k in ('parcel','property','tax','owner','delinq','foreclos','vacant','lien','assess','land')):
            csv_url=None
            for dist in ds.get('distribution', []):
                fmt = (dist.get('format') or '').lower()
                url = dist.get('downloadURL') or dist.get('accessURL') or ''
                if fmt=='csv' or url.endswith('.csv'):
                    csv_url=url; break
            rel.append((t[:80], csv_url))
    for t,u in rel[:15]:
        print('  -', t)
        if u: print('     CSV:', u[:200])
    print(f'  total: {len(rel)}')
except Exception as e:
    print('error:', e)
PY
done

echo ""
echo "=== Dallas DCAD — try downloading 2025 REAL PROPERTY CERT APPR ROLL via ViewPDFs ==="
mkdir -p "$BASE/dallas-tx/$DATE"
# Their URL format encodes a Windows-style file path. Try direct download with the ViewPDFs.aspx endpoint.
DALLAS_URL="https://www.dallascad.org/ViewPDFs.aspx?type=3&id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CDATA%20PRODUCTS%5C2025_REAL_PROPERTY_CERT_APPR_ROLL.zip"
curl -sS -A "$UA" -L -o "$BASE/dallas-tx/$DATE/2025-real-property-cert-roll.zip" "$DALLAS_URL" --max-time 600 -w "HTTP %{http_code} size %{size_download}\n"
ls -lh "$BASE/dallas-tx/$DATE/2025-real-property-cert-roll.zip" 2>/dev/null
file "$BASE/dallas-tx/$DATE/2025-real-property-cert-roll.zip" 2>/dev/null
if [ -s "$BASE/dallas-tx/$DATE/2025-real-property-cert-roll.zip" ]; then
  unzip -l "$BASE/dallas-tx/$DATE/2025-real-property-cert-roll.zip" 2>&1 | head -20
fi

# Also try the 2025 parcels
PARCELS_URL="https://www.dallascad.org/ViewPDFs.aspx?type=3&id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CGIS%20PRODUCTS%5CPARCEL2025.zip"
curl -sS -A "$UA" -L -o "$BASE/dallas-tx/$DATE/parcel2025.zip" "$PARCELS_URL" --max-time 600 -w "PARCEL2025 HTTP %{http_code} size %{size_download}\n"
ls -lh "$BASE/dallas-tx/$DATE/parcel2025.zip" 2>/dev/null

echo ""
echo "=== Harris HCAD — try via HTTPS + referer + with curl options ==="
mkdir -p "$BASE/harris-tx/$DATE"
# Get cookies from a page first
curl -sS -A "$UA" -c "$BASE/harris-tx/$DATE/cookies.txt" -o /dev/null "https://hcad.org/hcad-online-services/pdata/" --max-time 15
# Then try the zip with referer + cookies
curl -sS -A "$UA" -b "$BASE/harris-tx/$DATE/cookies.txt" -e "https://hcad.org/hcad-online-services/pdata/" -L \
  -o "$BASE/harris-tx/$DATE/Real_acct_owner.zip" \
  "https://pdata.hcad.org/data/cama/2026/Real_acct_owner.zip" --max-time 600 \
  -w "HTTPS+ref HTTP %{http_code} size %{size_download}\n"
ls -lh "$BASE/harris-tx/$DATE/Real_acct_owner.zip" 2>/dev/null
file "$BASE/harris-tx/$DATE/Real_acct_owner.zip" 2>/dev/null
echo "--- if small, dump body ---"
SZ=$(stat -c %s "$BASE/harris-tx/$DATE/Real_acct_owner.zip" 2>/dev/null || echo 0)
if [ "$SZ" -lt 100000 ]; then
  head -c 1500 "$BASE/harris-tx/$DATE/Real_acct_owner.zip"
fi

echo ""
echo "=== TOTAL ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
du -sh /opt/leadcurate/raw_imports
