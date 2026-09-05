#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="Mozilla/5.0 LeadCurate"
BASE=/opt/leadcurate/raw_imports

echo "=== Sample of the Guilford Discovery Snapshot ==="
head -8 /opt/leadcurate/processed/guilford-nc/$DATE/guilford-nc-absentee-tax-delinquent-${DATE}.csv | column -t -s, 2>/dev/null | cut -c1-200
echo ""
echo "=== Preview file sample (sales-ready) ==="
head -10 /opt/leadcurate/processed/guilford-nc/$DATE/guilford-nc-absentee-tax-delinquent-${DATE}-preview.csv

echo ""
echo "=== Shelby Trustee — re-probe sub-pages with correct quoting ==="
mkdir -p "$BASE/shelby-tn/$DATE"
for slug in \
  "161:Properties-Available-for-Sale" \
  "191:Tax-Sale-Schedule" \
  "103:Tax-Look-Up" \
  "94:Taxes" \
  "173:Delinquent-Taxes" \
  ; do
  num="${slug%%:*}"
  rest="${slug#*:}"
  url="https://www.shelbycountytrustee.com/${num}/${rest}"
  out="$BASE/shelby-tn/$DATE/${num}-$(echo $rest | tr / _ | tr -d ' ').html"
  curl -sS -A "$UA" -L -o "$out" "$url" --max-time 30 -w "$num: HTTP %{http_code} size %{size_download}\n"
done

echo ""
echo "--- file links across all Shelby Trustee pages ---"
for f in "$BASE/shelby-tn/$DATE"/*.html; do
  echo "## $(basename $f) ##"
  grep -oiE 'href="[^"]+"' "$f" 2>/dev/null | grep -iE 'pdf|csv|xls|zip|delinq|sale|list|zeus|sri|auction' | sort -u | head -15
done

echo ""
echo "--- Shelby County (not trustee) Chancery Court tax sale info ---"
curl -sS -A "$UA" -L -o "$BASE/shelby-tn/$DATE/chancery.html" "https://www.shelbycountytn.gov/330/Tax-Sale-Information" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
grep -oiE 'href="[^"]+"' "$BASE/shelby-tn/$DATE/chancery.html" 2>/dev/null | grep -iE 'pdf|csv|xls|zip|delinq|sale|list|zeus|sri|auction|registration' | sort -u | head -20

echo ""
echo "--- Shelby Assessor data ---"
for url in \
  "https://www.assessormelvinburgess.com/" \
  "https://www.assessormelvinburgess.com/property-search" \
  "https://www.assessormelvinburgess.com/data" \
  "https://gis.shelbycountytn.gov/" \
  "https://www.shelbycountytn.gov/2155/Assessor" \
  ; do
  code=$(curl -sS -A "$UA" -o /dev/null -w "%{http_code}" --max-time 12 -L "$url")
  echo "$code  $url"
done
