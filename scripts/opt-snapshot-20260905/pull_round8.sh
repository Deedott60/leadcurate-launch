#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
BASE=/opt/leadcurate/raw_imports

echo "=== DeKalb GA — ArcGIS Hub DCAT ==="
mkdir -p "$BASE/dekalb-ga/$DATE"
for url in \
  "https://dcgis-dekalbgis.hub.arcgis.com/api/feed/dcat-us/1.1.json" \
  "https://dekalbinsights-dekalbgis.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  ; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 12 -L "$url")
  echo "$code  $url"
  if [ "$code" = "200" ]; then
    name=$(echo "$url" | sed 's|https://||;s|/.*||')
    curl -sS -A "$UA" -L -o "$BASE/dekalb-ga/$DATE/dcat-${name}.json" "$url" --max-time 60
  fi
done

echo ""
echo "=== Forsyth NC — MapForsyth Hub DCAT ==="
mkdir -p "$BASE/forsyth-nc/$DATE"
for url in \
  "https://www.mapforsyth.org/api/feed/dcat-us/1.1.json" \
  "https://mapforsyth.org/api/feed/dcat-us/1.1.json" \
  "https://gis-forsyth.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  ; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 12 -L "$url")
  echo "$code  $url"
  if [ "$code" = "200" ]; then
    name=$(echo "$url" | sed 's|https://||;s|/.*||')
    curl -sS -A "$UA" -L -o "$BASE/forsyth-nc/$DATE/dcat-${name}.json" "$url" --max-time 60
  fi
done

echo ""
echo "=== Erie NY (Buffalo) — try GIS / RP DCAT and direct ==="
mkdir -p "$BASE/erie-ny/$DATE"
for url in \
  "https://data-erieny.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "https://gis-erieny.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "https://eriegis.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "https://gis-buffalonygov.opendata.arcgis.com/api/feed/dcat-us/1.1.json" \
  "https://data.buffalony.gov/api/feed/dcat-us/1.1.json" \
  ; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 10 -L "$url")
  echo "$code  $url"
  if [ "$code" = "200" ]; then
    name=$(echo "$url" | sed 's|https://||;s|/.*||')
    curl -sS -A "$UA" -L -o "$BASE/erie-ny/$DATE/dcat-${name}.json" "$url" --max-time 60
  fi
done
echo "--- Erie auction-foreclosure-information page ---"
curl -sS -A "$UA" -L -o "$BASE/erie-ny/$DATE/auction-foreclosure.html" "https://www3.erie.gov/ecrpts/auction-foreclosure-information" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
grep -oiE 'href="[^"]+"' "$BASE/erie-ny/$DATE/auction-foreclosure.html" 2>/dev/null | grep -iE 'pdf|csv|xls|zip|delinq|sale|list|auction|foreclos' | sort -u | head -20

echo ""
echo "=== Allen IN — direct delinquent property page ==="
mkdir -p "$BASE/allen-in/$DATE"
curl -sS -A "$UA" -L -o "$BASE/allen-in/$DATE/delinquent-page.html" "https://www.allencounty.in.gov/824/Delinquent-Property-List" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- file links on Allen IN delinquent page ---"
grep -oiE 'href="[^"]+"' "$BASE/allen-in/$DATE/delinquent-page.html" 2>/dev/null | grep -iE 'pdf|csv|xls|zip|delinq|list|tax' | sort -u | head -20

echo ""
echo "=== Charleston SC — current year tax sale PDF probes ==="
mkdir -p "$BASE/charleston-sc/$DATE"
for path in \
  "files/2026-RP-Tax-Sale-Listing.pdf" \
  "files/2025-RP-Tax-Sale-Listing.pdf" \
  "files/2024-RP-Tax-Sale-Listing.pdf" \
  "files/2023-RP-Tax-Sale-Listing.pdf" \
  "files/MH-Tax-Sale-Listing.pdf" \
  "files/RP-Tax-Sale-Listing.pdf" \
  ; do
  url="https://www.charlestoncounty.org/departments/delinquent-tax/${path}"
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 12 -L "$url")
  echo "$code  $url"
  if [ "$code" = "200" ]; then
    fname=$(basename "$path")
    curl -sS -A "$UA" -L -o "$BASE/charleston-sc/$DATE/$fname" "$url" --max-time 90
    ls -lh "$BASE/charleston-sc/$DATE/$fname"
  fi
done

echo ""
echo "=== Greenville SC — tax sale info ==="
mkdir -p "$BASE/greenville-sc/$DATE"
for url in \
  "https://www.greenvillecounty.org/TaxCollector/pdf/taxsaleinfo.pdf" \
  "https://www.greenvillecounty.org/appsAS400/taxsale/" \
  "https://www.greenvillecounty.org/TaxCollector/" \
  ; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 12 -L "$url")
  echo "$code  $url"
done
curl -sS -A "$UA" -L -o "$BASE/greenville-sc/$DATE/tax-sale-info.pdf" "https://www.greenvillecounty.org/TaxCollector/pdf/taxsaleinfo.pdf" --max-time 60 -w "main pdf HTTP %{http_code} size %{size_download}\n"
curl -sS -A "$UA" -L -o "$BASE/greenville-sc/$DATE/tax-sale-app.html" "https://www.greenvillecounty.org/appsAS400/taxsale/" --max-time 30 -w "html HTTP %{http_code} size %{size_download}\n"
echo "--- links on tax sale app ---"
grep -oiE 'href="[^"]+"' "$BASE/greenville-sc/$DATE/tax-sale-app.html" 2>/dev/null | sort -u | head -20

echo ""
echo "=== Jefferson AL — 2024 and 2023 delinquent parcels pages ==="
mkdir -p "$BASE/jefferson-al/$DATE"
curl -sS -A "$UA" -L -o "$BASE/jefferson-al/$DATE/page-2024-id2663.html" "https://www.jccal.org/Default.asp?ID=2663" --max-time 30 -w "2024 HTTP %{http_code} size %{size_download}\n"
curl -sS -A "$UA" -L -o "$BASE/jefferson-al/$DATE/page-2023-id2520.html" "https://www.jccal.org/Default.asp?ID=2520" --max-time 30 -w "2023 HTTP %{http_code} size %{size_download}\n"
echo "--- excel/data links across both pages ---"
grep -oiE 'href="[^"]+"' "$BASE/jefferson-al/$DATE/page-2024-id2663.html" "$BASE/jefferson-al/$DATE/page-2023-id2520.html" 2>/dev/null | grep -iE '\.xls|\.xlsx|\.csv|\.pdf|excel|download|delinq' | sort -u | head -30

echo ""
echo "=== Cobb GA — recent monthly delinquent PDFs (revize CDN) ==="
mkdir -p "$BASE/cobb-ga/$DATE"
# These monthly PDFs follow this URL pattern. Try recent months.
for dt in "07.06.2025" "06.01.2025" "05.01.2025" "04.01.2025" "03.01.2025" "02.01.2025" "01.01.2025" "12.01.2024" "11.01.2024" "10.01.2024" "09.01.2024" "08.01.2024" "07.01.2024"; do
  url="https://cms9files.revize.com/cobbcounty/Property/Delinquent/Cobb%20County%20Tax%20Commissioner%20Delinquent%20Tax%20List%20${dt}.pdf"
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 10 -L "$url")
  echo "$code  $dt"
  if [ "$code" = "200" ]; then
    curl -sS -A "$UA" -L -o "$BASE/cobb-ga/$DATE/delinquent-${dt}.pdf" "$url" --max-time 90
    ls -lh "$BASE/cobb-ga/$DATE/delinquent-${dt}.pdf"
    break
  fi
done

echo ""
echo "=== Harris TX HCAD — grab the PDATA codebook to learn zip filenames ==="
mkdir -p "$BASE/harris-tx/$DATE"
curl -sS -A "$UA" -L -o "$BASE/harris-tx/$DATE/pdataCodebook.pdf" "https://hcad.org/assets/uploads/pdf/pdataCodebook.pdf" --max-time 60 -w "HTTP %{http_code} size %{size_download}\n"
ls -lh "$BASE/harris-tx/$DATE/pdataCodebook.pdf" 2>/dev/null
echo "--- try common HCAD zip URL patterns ---"
for ZIP in Real_acct_owner Real_building_land Real_jur_exempt Real_lease Real_neighborhood_code Real_acct_history Real_pp_files Real_subdivision; do
  url="http://pdata.hcad.org/data/cama/2026/${ZIP}.zip"
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 10 -L "$url")
  echo "$code  $url"
done
for ZIP in Real_acct_owner Real_building_land Real_acct_history; do
  for YR in 2025 2024; do
    url="http://pdata.hcad.org/data/cama/${YR}/${ZIP}.zip"
    code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 8 -L "$url")
    echo "$code  $url"
  done
done

echo ""
echo "=== Dallas DCAD — maps.dcad.org GIS data products ==="
mkdir -p "$BASE/dallas-tx/$DATE"
for url in \
  "https://maps.dcad.org/prd/dpm/help.htm" \
  "https://www.dallascad.org/openrecords.aspx" \
  "https://www.dallascad.org/DataProducts.aspx" \
  "https://www.dallascad.org/GIS.aspx" \
  ; do
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 12 -L "$url")
  echo "$code  $url"
done
curl -sS -A "$UA" -L -o "$BASE/dallas-tx/$DATE/dpm-help.htm" "https://maps.dcad.org/prd/dpm/help.htm" --max-time 30
echo "--- links on dpm help ---"
grep -oiE 'href="[^"]+"' "$BASE/dallas-tx/$DATE/dpm-help.htm" 2>/dev/null | grep -iE 'csv|zip|xls|data|download' | sort -u | head -10

echo ""
echo "=== TOTAL DATA ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
du -sh /opt/leadcurate/raw_imports
