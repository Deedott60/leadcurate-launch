#!/bin/bash
DATE=$(date -u +%Y-%m-%d)
ENTITY='LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|BANK|CITY|COUNTY|DEPT|AUTHORITY|DISTRICT|FUND|SCHOOL|CHURCH|ASSOC|UNIV|COLLEGE'

# ─── FULTON GA ─────────────────────────────────────────────────
echo "--- Fulton GA ---"
python3 - <<'PYEOF'
import csv, json, re
from pathlib import Path
from datetime import date
import glob, sys

ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|BANK|CITY|COUNTY|DEPT|AUTHORITY|FUND|CHURCH|ASSOC)\b', re.I)
raw = sorted(glob.glob('/opt/leadcurate/raw_imports/fulton-ga/*/*.csv'))
if not raw: print("Fulton: no CSV"); sys.exit()
f = raw[-1]
out = Path(f'/opt/leadcurate/snapshots/fulton-ga/{date.today().isoformat()}')
out.mkdir(parents=True, exist_ok=True)
rows = []
with open(f, newline='', encoding='utf-8-sig') as fp:
    for r in csv.DictReader(fp):
        owner = r.get('Owner','')
        if not owner: continue
        is_e = bool(ENTITY.search(owner))
        addr = r.get('Address','')
        parcel = r.get('ParcelID','')
        val = r.get('TotAppr','0') or '0'
        try: val_n = float(str(val).replace(',',''))
        except: val_n = 0
        rows.append({
            'parcel_id': parcel,
            'owner_name': owner,
            'owner_type': 'entity' if is_e else 'individual',
            'site_addr': addr,
            'total_appraisal': val_n,
            'land_assess': r.get('LandAssess',''),
            'impr_assess': r.get('ImprAssess',''),
            'tax_dist': r.get('TaxDist',''),
            'score': 65 + (8 if is_e else 0) + (10 if val_n > 100000 else 0)
        })
rows.sort(key=lambda x: x['score'], reverse=True)
p = out / f'fulton-ga-parcels-{date.today().isoformat()}.csv'
with open(p,'w',newline='',encoding='utf-8') as fp:
    w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows[:5000])
(out/'meta.json').write_text(json.dumps({'market':'Fulton County GA (Atlanta)','lane':'Parcel Owner','total_rows':len(rows),'top_5000':True,'processed':date.today().isoformat()}))
print(f'Fulton GA: {len(rows):,} total rows, top 5000 saved')
PYEOF

# ─── DEKALB GA ─────────────────────────────────────────────────
echo "--- DeKalb GA ---"
python3 - <<'PYEOF'
import csv, json, re
from pathlib import Path
from datetime import date
import glob, sys

ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|BANK|CITY|COUNTY|DEPT|AUTHORITY|FUND|CHURCH|ASSOC)\b', re.I)
raw = sorted(glob.glob('/opt/leadcurate/raw_imports/dekalb-ga/*/*.csv'))
if not raw: print("DeKalb: no CSV"); sys.exit()
f = raw[-1]

# Check full headers
with open(f, newline='', encoding='utf-8-sig') as fp:
    reader = csv.DictReader(fp)
    headers = reader.fieldnames or []
    # Find owner col
    owner_col = next((h for h in headers if 'OWN' in h.upper() or 'NAME' in h.upper()), None)
    addr_col = next((h for h in headers if 'ADDR' in h.upper() or 'STREET' in h.upper() or 'SITE' in h.upper()), None)
    val_col = next((h for h in headers if 'APPR' in h.upper() or 'VALUE' in h.upper() or 'ASSESS' in h.upper()), None)

print(f"DeKalb cols: owner={owner_col} addr={addr_col} val={val_col}")

out = Path(f'/opt/leadcurate/snapshots/dekalb-ga/{date.today().isoformat()}')
out.mkdir(parents=True, exist_ok=True)

# Need second pass for owner col — DeKalb may have owner in a later column
with open(f, newline='', encoding='utf-8-sig') as fp:
    sample = list(csv.DictReader(fp))[:5]

print("DeKalb sample keys:", list(sample[0].keys())[:30] if sample else 'empty')

rows = []
if owner_col:
    with open(f, newline='', encoding='utf-8-sig') as fp:
        for r in csv.DictReader(fp):
            owner = r.get(owner_col,'')
            if not owner: continue
            is_e = bool(ENTITY.search(owner))
            rows.append({'parcel_id': r.get('ParcelID',''), 'owner_name': owner,
                'owner_type': 'entity' if is_e else 'individual',
                'site_addr': r.get(addr_col,'') if addr_col else '',
                'score': 60 + (8 if is_e else 0)})
    rows.sort(key=lambda x: x['score'], reverse=True)
    p = out / f'dekalb-ga-parcels-{date.today().isoformat()}.csv'
    with open(p,'w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows[:5000])
    (out/'meta.json').write_text(json.dumps({'market':'DeKalb County GA (Atlanta East)','lane':'Parcel Owner','total_rows':len(rows),'processed':date.today().isoformat()}))
    print(f'DeKalb GA: {len(rows):,} rows')
else:
    print("DeKalb: no owner column found in headers")
PYEOF

# ─── MARION IN (Indianapolis) ──────────────────────────────────
echo "--- Marion IN ---"
python3 - <<'PYEOF'
import csv, json, re
from pathlib import Path
from datetime import date
import glob, sys

ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|BANK|CITY|COUNTY|DEPT|AUTHORITY|FUND|CHURCH|ASSOC)\b', re.I)
raw = sorted(glob.glob('/opt/leadcurate/raw_imports/marion-in/*/*.csv'))
if not raw: print("Marion: no CSV"); sys.exit()
f = raw[-1]

with open(f, newline='', encoding='utf-8-sig') as fp:
    reader = csv.DictReader(fp)
    headers = reader.fieldnames or []
    owner_col = next((h for h in headers if 'OWN' in h.upper() or 'TAXPAYER' in h.upper()), None)
    addr_col = next((h for h in headers if 'STNAME' in h.upper() or 'STREET' in h.upper() or 'STNUMBER' in h.upper()), 'FULL_STNAME')

print(f"Marion cols: owner={owner_col} addr={addr_col}")
print("Marion sample headers:", headers[:25])

out = Path(f'/opt/leadcurate/snapshots/marion-in/{date.today().isoformat()}')
out.mkdir(parents=True, exist_ok=True)

rows = []
if owner_col:
    with open(f, newline='', encoding='utf-8-sig') as fp:
        for r in csv.DictReader(fp):
            owner = r.get(owner_col,'')
            if not owner: continue
            is_e = bool(ENTITY.search(owner))
            stn = r.get('STNUMBER','')
            st = r.get('FULL_STNAME','') or r.get('STREET_NAME','')
            city = r.get('CITY','INDIANAPOLIS')
            zip_ = r.get('ZIPCODE','')
            rows.append({'parcel_id': r.get('PARCEL_TAG','') or r.get('PARCEL_I',''),
                'owner_name': owner, 'owner_type': 'entity' if is_e else 'individual',
                'site_addr': f"{stn} {st}".strip(), 'city': city, 'zip': zip_,
                'score': 60 + (8 if is_e else 0)})
    rows.sort(key=lambda x: x['score'], reverse=True)
    p = out / f'marion-in-parcels-{date.today().isoformat()}.csv'
    with open(p,'w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows[:5000])
    (out/'meta.json').write_text(json.dumps({'market':'Marion County IN (Indianapolis)','lane':'Parcel Owner','total_rows':len(rows),'processed':date.today().isoformat()}))
    print(f'Marion IN: {len(rows):,} rows')
else:
    # Try reading a few rows to find owner
    with open(f, newline='', encoding='utf-8-sig') as fp:
        for row in list(csv.DictReader(fp))[:3]:
            print("Marion sample:", dict(list(row.items())[:15]))
            break
    print("Marion IN: owner column not found by heuristic")
PYEOF

# ─── FORSYTH NC (re-pull from ArcGIS) ─────────────────────────
echo "--- Forsyth NC re-pull ---"
DATE_NOW=$(date -u +%Y-%m-%d)
mkdir -p /opt/leadcurate/raw_imports/forsyth-nc/$DATE_NOW
URL="https://www.mapforsyth.org/api/download/v1/items/fd915221da64453aad7989b05f06707e/csv?layers=0"
curl -sS -L -A "LeadCurate-1.0" -o /opt/leadcurate/raw_imports/forsyth-nc/$DATE_NOW/parcels.csv "$URL" -w "Forsyth NC: HTTP %{http_code} size %{size_download}\n" --max-time 120
head -1 /opt/leadcurate/raw_imports/forsyth-nc/$DATE_NOW/parcels.csv | cut -c1-200

echo ""
echo "=== FINAL SNAPSHOT INVENTORY ==="
for d in /opt/leadcurate/snapshots/*/; do
  market=$(basename $d)
  latest=$(ls -td $d*/ 2>/dev/null | head -1)
  if [ -n "$latest" ]; then
    meta="$latest/meta.json"
    rows=$(python3 -c "import json; d=json.load(open('$meta')); print(d.get('total_rows',d.get('top_5000','?')))" 2>/dev/null || echo '?')
    echo "  ✅ $market: $rows rows"
  fi
done
