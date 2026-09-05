#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="Mozilla/5.0"
BASE=/opt/leadcurate/raw_imports

echo "=== Re-download Shelby TN tax sale extract ==="
mkdir -p "$BASE/shelby-tn/$DATE"
curl -sS -A "$UA" -L -o "$BASE/shelby-tn/$DATE/tax-sale-extract.csv" "https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv" --max-time 120 -w "HTTP %{http_code} size %{size_download} bytes\n"
ls -lh "$BASE/shelby-tn/$DATE/tax-sale-extract.csv"
echo "rows:"
wc -l "$BASE/shelby-tn/$DATE/tax-sale-extract.csv"
echo "header:"
head -1 "$BASE/shelby-tn/$DATE/tax-sale-extract.csv"
echo "first 5 data rows:"
sed -n '2,6p' "$BASE/shelby-tn/$DATE/tax-sale-extract.csv"
echo "tax sale code breakdown:"
awk -F, 'NR>1 {gsub(/^ +| +$/,"",$5); print $5}' "$BASE/shelby-tn/$DATE/tax-sale-extract.csv" | sort | uniq -c | sort -rn | head
