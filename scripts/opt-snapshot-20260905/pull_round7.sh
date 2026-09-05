#!/bin/bash
set -u
DATE=$(date -u +%Y-%m-%d)
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE=/opt/leadcurate/raw_imports

# Shelby TN — Memphis. Zeus Auction is run by SRI Inc.
echo "=== Shelby TN — Zeus Auction probes ==="
mkdir -p "$BASE/shelby-tn/$DATE"
for url in \
  "https://www.zeusauction.com/" \
  "https://www.zeusauction.com/api/auctions" \
  "https://www.zeusauction.com/auctions" \
  "https://www.zeusauction.com/sitemap.xml" \
  "https://www.zeusauction.com/robots.txt" \
  "https://www.zeusauction.com/SRI/AuctionList.aspx" \
  "https://www.zeusauction.com/SHELBY" \
  "https://www.zeusauction.com/auctions/?county=Shelby&state=TN" \
  ; do
  code=$(curl -sS -k -A "$UA" -o /dev/null -w "%{http_code}" --max-time 15 -L "$url")
  echo "$code  $url"
done
echo "--- pull main pages ---"
curl -sS -k -A "$UA" -L -o "$BASE/shelby-tn/$DATE/zeus-home.html" "https://www.zeusauction.com/" --max-time 30 -w "home HTTP %{http_code} size %{size_download}\n"
curl -sS -k -A "$UA" -L -o "$BASE/shelby-tn/$DATE/zeus-robots.txt" "https://www.zeusauction.com/robots.txt" --max-time 10 -w "robots HTTP %{http_code}\n"
curl -sS -k -A "$UA" -L -o "$BASE/shelby-tn/$DATE/zeus-sitemap.xml" "https://www.zeusauction.com/sitemap.xml" --max-time 10 -w "sitemap HTTP %{http_code}\n"
echo "--- links on Zeus home ---"
grep -oiE 'href="[^"]+"' "$BASE/shelby-tn/$DATE/zeus-home.html" 2>/dev/null | grep -iE 'auction|shelby|tn|memphis|tax|delinq|sale' | sort -u | head -20
echo "--- robots.txt ---"
cat "$BASE/shelby-tn/$DATE/zeus-robots.txt" 2>/dev/null | head -30

echo ""
echo "=== Shelby County Trustee — direct page probe ==="
curl -sS -k -A "$UA" -L -o "$BASE/shelby-tn/$DATE/trustee-delinquent.html" "https://www.shelbycountytrustee.com/173/Delinquent-Taxes" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- file links on trustee page ---"
grep -oiE 'href="[^"]+"' "$BASE/shelby-tn/$DATE/trustee-delinquent.html" 2>/dev/null | grep -iE 'pdf|xls|csv|delinq|tax|sale|list|zeus' | sort -u | head -20

echo ""
echo "=== Harris TX HCAD — drill into property-downloads.html ==="
curl -sS -A "$UA" -L -o "$BASE/harris-tx/$DATE/property-downloads.html" "http://hcad.org/pdata/pdata-property-downloads.html" --max-time 30 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- all links on that page ---"
grep -oiE 'href="[^"]+"' "$BASE/harris-tx/$DATE/property-downloads.html" 2>/dev/null | sort -u | head -40
echo ""
echo "--- specifically zip downloads ---"
grep -oiE '(http[s]?://[^"<>]+|/[^"<>]+)\.zip' "$BASE/harris-tx/$DATE/property-downloads.html" 2>/dev/null | sort -u

echo ""
echo "=== Jefferson AL — eringcapture with -k and cookies ==="
curl -sS -k -A "$UA" -L -c "$BASE/jefferson-al/$DATE/cookies.txt" \
  -o "$BASE/jefferson-al/$DATE/eringcapture-collection.html" \
  "https://eringcapture.jccal.org/collection" --max-time 60 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- find data links on collection page ---"
grep -oiE 'href="[^"]+"' "$BASE/jefferson-al/$DATE/eringcapture-collection.html" 2>/dev/null | sort -u | head -25
echo ""
curl -sS -k -A "$UA" -L -b "$BASE/jefferson-al/$DATE/cookies.txt" \
  -o "$BASE/jefferson-al/$DATE/eringcapture-delq.html" \
  "https://eringcapture.jccal.org/DelqSearch" --max-time 60 -w "HTTP %{http_code} size %{size_download}\n"
echo "--- find data links on DelqSearch ---"
grep -oiE 'href="[^"]+"' "$BASE/jefferson-al/$DATE/eringcapture-delq.html" 2>/dev/null | sort -u | head -25

echo ""
echo "=== Dallas TX — direct CAD probes ==="
mkdir -p "$BASE/dallas-tx/$DATE"
for url in \
  "https://www.dallascad.org/" \
  "https://www.dallascad.org/SearchOwner.aspx" \
  "https://www.dallascad.org/ResDetail.aspx" \
  "https://www.dallasact.com/act_webdev/dallas/index.jsp" \
  "https://gis.dallascad.org/arcgis/rest/services?f=pjson" \
  ; do
  code=$(curl -sS -A "$UA" -o /dev/null -w "%{http_code}" --max-time 12 -L "$url")
  echo "$code  $url"
done

echo ""
echo "=== Forsyth NC — ncptscloud direct ==="
mkdir -p "$BASE/forsyth-nc/$DATE"
for url in \
  "https://bcpwa.ncptscloud.com/forsythtax/BillDelinquentSearch.aspx" \
  "https://bcpwa.ncptscloud.com/forsythtax/" \
  "https://bcpwa.ncptscloud.com/forsythtax/Report.aspx" \
  ; do
  code=$(curl -sS -A "$UA" -o /dev/null -w "%{http_code}" --max-time 12 -L "$url")
  echo "$code  $url"
done

echo ""
echo "=== ArcGIS hub naming hunt — Shelby/Allen/Erie/Charleston/Greenville/Dallas ==="
HOSTS=(
  "shelby-tn:data-shelbygis.opendata.arcgis.com"
  "shelby-tn:shelbycountygis.hub.arcgis.com"
  "shelby-tn:data.memphistn.gov"
  "shelby-tn:opendata-memphistn.opendata.arcgis.com"
  "allen-in:data-allencountyin.opendata.arcgis.com"
  "allen-in:gis-allencountyin.opendata.arcgis.com"
  "allen-in:fortwaynegis.opendata.arcgis.com"
  "erie-ny:data-erieny.opendata.arcgis.com"
  "erie-ny:buffalogis.opendata.arcgis.com"
  "erie-ny:gis-erieny.opendata.arcgis.com"
  "charleston-sc:gis-charlestoncountysc.opendata.arcgis.com"
  "charleston-sc:charleston-county-sc.opendata.arcgis.com"
  "charleston-sc:data-charlestoncountygis.opendata.arcgis.com"
  "greenville-sc:gis-gcgis.opendata.arcgis.com"
  "greenville-sc:data-greenvillesc.opendata.arcgis.com"
  "greenville-sc:gcgis.opendata.arcgis.com"
  "dallas-tx:data-dallasgis.opendata.arcgis.com"
  "dallas-tx:data.dallascityhall.com"
  "dallas-tx:gis-dallascountytx.opendata.arcgis.com"
  "cobb-ga:data-cobbcountyga.opendata.arcgis.com"
  "cobb-ga:gis-cobbcountyga.opendata.arcgis.com"
  "cobb-ga:cobbcountyga.opendata.arcgis.com"
  "dekalb-ga:data-dekalbcounty.opendata.arcgis.com"
  "dekalb-ga:dekalbgis.opendata.arcgis.com"
)
for H in "${HOSTS[@]}"; do
  county="${H%%:*}"
  host="${H#*:}"
  url="https://${host}/api/feed/dcat-us/1.1.json"
  code=$(curl -sS -o /dev/null -w "%{http_code}" -A "$UA" --max-time 8 -L "$url")
  if [ "$code" = "200" ]; then
    mkdir -p "$BASE/$county/$DATE"
    out="$BASE/$county/$DATE/dcat-${host//./_}.json"
    curl -sS -A "$UA" --max-time 30 -L -o "$out" "$url"
    sz=$(du -h "$out" | cut -f1)
    echo "200  $county  $host  -> $sz"
  else
    echo "$code  $county  $host"
  fi
done

echo ""
echo "=== Inspect any new DCAT files ==="
for COUNTY in shelby-tn allen-in erie-ny charleston-sc greenville-sc dallas-tx cobb-ga dekalb-ga; do
  for f in "$BASE/$COUNTY/$DATE"/dcat-*.json; do
    [ -f "$f" ] || continue
    echo "--- $f ---"
    python3 - <<PY
import json
try:
    d = json.load(open('$f'))
    rel=[]
    for ds in d.get('dataset', []):
        title = ds.get('title','')
        kw = title.lower()
        if any(k in kw for k in ('parcel','property','tax','owner','delinq','foreclos','vacant','lien','assess','land')):
            csv_url = None
            for dist in ds.get('distribution', []):
                fmt = (dist.get('format') or '').lower()
                url = dist.get('downloadURL') or dist.get('accessURL') or ''
                if fmt == 'csv' or url.endswith('.csv'):
                    csv_url = url
                    break
            rel.append((title[:70], csv_url))
    for t,u in rel[:10]:
        print('  -', t, '\n    CSV:', (u or '(no CSV)')[:200])
    print(f'  total relevant: {len(rel)}')
except Exception as e:
    print(' parse error:', e)
PY
  done
done

echo ""
echo "=== FINAL TOTAL ==="
du -sh /opt/leadcurate/raw_imports/*/$DATE 2>/dev/null | sort -h
du -sh /opt/leadcurate/raw_imports
