#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
BASE=/opt/leadcurate/raw_imports

echo "=== SHELBY TN tax-sale-extract.csv ==="
ls -lh $BASE/shelby-tn/$DATE/tax-sale-extract.csv
wc -l $BASE/shelby-tn/$DATE/tax-sale-extract.csv
echo "header:"
head -1 $BASE/shelby-tn/$DATE/tax-sale-extract.csv
echo "first 5 data rows:"
head -6 $BASE/shelby-tn/$DATE/tax-sale-extract.csv | tail -5

echo ""
echo "=== Tax Sale code breakdown ==="
awk -F, 'NR>1 {print $5}' $BASE/shelby-tn/$DATE/tax-sale-extract.csv | sort | uniq -c | sort -rn | head -20

echo ""
echo "=== JEFFERSON KY foreclosures raw header + 3 sample rows ==="
head -1 $BASE/jefferson-ky/property-foreclosures.csv
echo "--- samples ---"
sed -n '2,5p' $BASE/jefferson-ky/property-foreclosures.csv

echo ""
echo "=== Sale_Date and Sale_Price empty check ==="
awk -F, 'NR>1 {
  if ($15 == "" || $15 == " ") sd_empty++; else sd_ok++;
  if ($16 == "" || $16 == " " || $16 == "0") sp_empty++; else sp_ok++;
}
END {
  print "Sale_Date empty:", sd_empty, "ok:", sd_ok
  print "Sale_Price empty/zero:", sp_empty, "ok:", sp_ok
}' $BASE/jefferson-ky/property-foreclosures.csv

echo ""
echo "=== Sample Action_Filed dates (column 12) ==="
awk -F, 'NR>1 && NR<=10 {print "Action_Filed:", $12, "| Sale_Date:", $15, "| Sale_Price:", $16}' $BASE/jefferson-ky/property-foreclosures.csv
