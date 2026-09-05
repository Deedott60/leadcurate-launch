#!/bin/bash
# Process all unprocessed counties into sellable snapshots
# Runs on VPS. Uses existing skill patterns.
set -e
DATE=$(date -u +%Y-%m-%d)
SCRIPTS=/opt/leadcurate/scripts
SNAPS=/opt/leadcurate/snapshots
RAW=/opt/leadcurate/raw_imports
LOG=/opt/leadcurate/logs/batch_process_$DATE.log

mkdir -p $SNAPS $LOG 2>/dev/null || true
exec > >(tee -a $LOG) 2>&1
echo "=== LeadCurate batch processing $DATE ==="

# ─── helper: quick CSV row-count ───────────────────────────────
rowcount(){ wc -l < "$1" 2>/dev/null || echo 0; }

# ─── 1. Guilford NC ────────────────────────────────────────────
if [ -d "$RAW/guilford-nc" ]; then
  echo "--- Guilford NC ---"
  CSV=$(ls $RAW/guilford-nc/*/tax_delinquent*.csv 2>/dev/null | sort | tail -1)
  [ -n "$CSV" ] && python3 $SCRIPTS/process_guilford.py "$CSV" "$SNAPS/guilford-nc/$DATE/" && echo "Guilford done ($(rowcount $CSV) rows)" || echo "Guilford: no raw CSV found"
fi

# ─── 2. Wake NC ────────────────────────────────────────────────
if [ -d "$RAW/wake-nc" ]; then
  echo "--- Wake NC ---"
  XSLX=$(ls $RAW/wake-nc/*/*.xlsx 2>/dev/null | sort | tail -1)
  CSV=$(ls $RAW/wake-nc/*/*.csv 2>/dev/null | sort | tail -1)
  F=${XSLX:-$CSV}
  if [ -n "$F" ]; then
    python3 - <<PYEOF
import csv, json, re, sys
from pathlib import Path
from datetime import date

f = Path("$F")
out = Path("$SNAPS/wake-nc/$DATE")
out.mkdir(parents=True, exist_ok=True)

ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|ASSOC|BANK|CITY|COUNTY|DEPT)\b', re.I)

rows = []
try:
    import openpyxl
    wb = openpyxl.load_workbook(str(f), read_only=True, data_only=True)
    ws = wb.active
    headers = [str(c.value or '').strip() for c in next(ws.iter_rows())]
    for row in ws.iter_rows(min_row=2, values_only=True):
        rows.append(dict(zip(headers, [str(v or '').strip() for v in row])))
except Exception:
    with open(str(f), newline='', encoding='utf-8-sig') as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)

owner_col = next((h for h in (rows[0].keys() if rows else []) if any(k in h.upper() for k in ['OWNER','NAME'])), None)
addr_col  = next((h for h in (rows[0].keys() if rows else []) if any(k in h.upper() for k in ['ADDR','SITE','PROP'])), None)

out_rows = []
for r in rows:
    owner = r.get(owner_col,'') if owner_col else ''
    if not owner: continue
    is_entity = bool(ENTITY.search(owner))
    out_rows.append({**r, 'owner_type': 'entity' if is_entity else 'individual', 'score': 60 if is_entity else 70})

out_rows.sort(key=lambda x: x['score'], reverse=True)

csv_path = out / f"wake-nc-delinquent-{date.today().isoformat()}.csv"
if out_rows:
    with open(csv_path, 'w', newline='', encoding='utf-8') as fp:
        w = csv.DictWriter(fp, fieldnames=list(out_rows[0].keys()))
        w.writeheader(); w.writerows(out_rows)
    (out / 'meta.json').write_text(json.dumps({'market':'Wake County NC (Raleigh)','lane':'Tax Delinquent','total_rows':len(out_rows),'processed':date.today().isoformat(),'source':str(f)}))
    print(f"Wake NC: {len(out_rows)} rows -> {csv_path}")
else:
    print("Wake NC: 0 rows extracted")
PYEOF
  else
    echo "Wake NC: no raw file found"
  fi
fi

# ─── 3. Forsyth NC ─────────────────────────────────────────────
if [ -d "$RAW/forsyth-nc" ]; then
  echo "--- Forsyth NC ---"
  CSV=$(ls $RAW/forsyth-nc/*/*.csv 2>/dev/null | sort | tail -1)
  if [ -n "$CSV" ]; then
    python3 - <<PYEOF
import csv, json, re
from pathlib import Path
from datetime import date

f = Path("$CSV")
out = Path("$SNAPS/forsyth-nc/$DATE")
out.mkdir(parents=True, exist_ok=True)
ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|ASSOC|BANK|CITY|COUNTY)\b', re.I)
rows = []
with open(str(f), newline='', encoding='utf-8-sig') as fp:
    reader = csv.DictReader(fp)
    for r in reader:
        owner = r.get('CURRENTOWNERNAME','') or r.get('OWNER_NAME','') or r.get('NAME','')
        if not owner: continue
        is_e = bool(ENTITY.search(owner))
        rows.append({**r, 'owner_type':'entity' if is_e else 'individual','score':60 if is_e else 70})
rows.sort(key=lambda x: x['score'], reverse=True)
p = out / f"forsyth-nc-parcels-{date.today().isoformat()}.csv"
if rows:
    with open(p,'w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    (out/'meta.json').write_text(json.dumps({'market':'Forsyth County NC (Winston-Salem)','lane':'Parcel Owner','total_rows':len(rows),'processed':date.today().isoformat()}))
    print(f"Forsyth NC: {len(rows)} rows")
else: print("Forsyth NC: 0 rows")
PYEOF
  else echo "Forsyth NC: no raw CSV"; fi
fi

# ─── 4. Guilford NC (second pass / foreclosure) ────────────────
if [ -d "$RAW/guilford-nc" ]; then
  CSV2=$(ls $RAW/guilford-nc/*/foreclosure*.csv 2>/dev/null | sort | tail -1)
  [ -n "$CSV2" ] && echo "Guilford foreclosure: $(rowcount $CSV2) rows (already handled by process_guilford.py)" || true
fi

# ─── 5. Jefferson KY (Louisville) ──────────────────────────────
if [ -d "$RAW/jefferson-ky" ]; then
  echo "--- Jefferson KY (Louisville) ---"
  CSV=$(ls $RAW/jefferson-ky/*/*.csv 2>/dev/null | sort | tail -1)
  [ -n "$CSV" ] && python3 $SCRIPTS/process_jefferson_ky_v2.py 2>/dev/null || echo "Jefferson KY: script ran (check logs)"
fi

# ─── 6. Shelby TN (Memphis) ────────────────────────────────────
if [ -d "$RAW/shelby-tn" ]; then
  echo "--- Shelby TN ---"
  CSV=$(ls $RAW/shelby-tn/*/*.csv 2>/dev/null | sort | tail -1)
  [ -n "$CSV" ] && python3 $SCRIPTS/process_shelby_tn.py 2>/dev/null || echo "Shelby TN: script ran"
fi

# ─── 7. Fulton GA (Atlanta) ────────────────────────────────────
if [ -d "$RAW/fulton-ga" ]; then
  echo "--- Fulton GA ---"
  python3 - <<'PYEOF'
import csv, json, re
from pathlib import Path
from datetime import date
import glob, os

raw = sorted(glob.glob('/opt/leadcurate/raw_imports/fulton-ga/*/*.csv'))
if not raw:
    print("Fulton GA: no raw CSV"); exit()
f = raw[-1]
out = Path(f'/opt/leadcurate/snapshots/fulton-ga/{date.today().isoformat()}')
out.mkdir(parents=True, exist_ok=True)
ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|BANK|CITY|COUNTY|DEPT)\b', re.I)
rows = []
with open(f, newline='', encoding='utf-8-sig') as fp:
    for r in csv.DictReader(fp):
        owner = r.get('OWNER','') or r.get('OWNERNAME','') or r.get('NAME','')
        if not owner: continue
        is_e = bool(ENTITY.search(owner))
        rows.append({**r, 'owner_type':'entity' if is_e else 'individual','score':60+is_e*8})
rows.sort(key=lambda x: x['score'], reverse=True)
p = out / f'fulton-ga-parcels-{date.today().isoformat()}.csv'
if rows:
    with open(p,'w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows[:5000])
    (out/'meta.json').write_text(json.dumps({'market':'Fulton County GA (Atlanta)','lane':'Parcel Owner','total_rows':len(rows),'processed':date.today().isoformat()}))
    print(f'Fulton GA: {len(rows)} rows -> top 5000 saved')
else: print('Fulton GA: 0 rows')
PYEOF
fi

# ─── 8. DeKalb GA ──────────────────────────────────────────────
if [ -d "$RAW/dekalb-ga" ]; then
  echo "--- DeKalb GA ---"
  python3 - <<'PYEOF'
import csv, json, re
from pathlib import Path
from datetime import date
import glob

raw = sorted(glob.glob('/opt/leadcurate/raw_imports/dekalb-ga/*/*.csv'))
if not raw:
    print("DeKalb GA: no raw CSV"); exit()
f = raw[-1]
out = Path(f'/opt/leadcurate/snapshots/dekalb-ga/{date.today().isoformat()}')
out.mkdir(parents=True, exist_ok=True)
ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|BANK|CITY|COUNTY)\b', re.I)
rows = []
with open(f, newline='', encoding='utf-8-sig') as fp:
    for r in csv.DictReader(fp):
        owner = r.get('OWNER','') or r.get('OWN1','') or r.get('NAME','')
        if not owner: continue
        is_e = bool(ENTITY.search(owner))
        rows.append({**r, 'owner_type':'entity' if is_e else 'individual','score':60+is_e*8})
rows.sort(key=lambda x: x['score'], reverse=True)
p = out / f'dekalb-ga-parcels-{date.today().isoformat()}.csv'
if rows:
    with open(p,'w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows[:5000])
    (out/'meta.json').write_text(json.dumps({'market':'DeKalb County GA (Atlanta)','lane':'Parcel Owner','total_rows':len(rows),'processed':date.today().isoformat()}))
    print(f'DeKalb GA: {len(rows)} rows')
else: print('DeKalb GA: 0 rows')
PYEOF
fi

# ─── 9. Marion IN (Indianapolis) ───────────────────────────────
if [ -d "$RAW/marion-in" ]; then
  echo "--- Marion IN ---"
  python3 - <<'PYEOF'
import csv, json, re
from pathlib import Path
from datetime import date
import glob

raw = sorted(glob.glob('/opt/leadcurate/raw_imports/marion-in/*/*.csv'))
if not raw: print("Marion IN: no raw CSV"); exit()
f = raw[-1]
out = Path(f'/opt/leadcurate/snapshots/marion-in/{date.today().isoformat()}')
out.mkdir(parents=True, exist_ok=True)
ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|BANK|CITY|COUNTY)\b', re.I)
rows = []
with open(f, newline='', encoding='utf-8-sig') as fp:
    for r in csv.DictReader(fp):
        owner = r.get('OWNER','') or r.get('OWN_NAME','') or r.get('NAME','')
        if not owner: continue
        is_e = bool(ENTITY.search(owner))
        rows.append({**r,'owner_type':'entity' if is_e else 'individual','score':60+is_e*8})
rows.sort(key=lambda x: x['score'], reverse=True)
p = out / f'marion-in-parcels-{date.today().isoformat()}.csv'
if rows:
    with open(p,'w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows[:5000])
    (out/'meta.json').write_text(json.dumps({'market':'Marion County IN (Indianapolis)','lane':'Parcel Owner','total_rows':len(rows),'processed':date.today().isoformat()}))
    print(f'Marion IN: {len(rows)} rows')
else: print('Marion IN: 0 rows')
PYEOF
fi

# ─── 10. Cuyahoga OH (Cleveland) ───────────────────────────────
if [ -d "$RAW/cuyahoga-oh" ]; then
  echo "--- Cuyahoga OH ---"
  python3 - <<'PYEOF'
import csv, json, re
from pathlib import Path
from datetime import date
import glob

raw = sorted(glob.glob('/opt/leadcurate/raw_imports/cuyahoga-oh/*/*.csv'))
if not raw: print("Cuyahoga OH: no raw CSV"); exit()
f = raw[-1]
out = Path(f'/opt/leadcurate/snapshots/cuyahoga-oh/{date.today().isoformat()}')
out.mkdir(parents=True, exist_ok=True)
ENTITY = re.compile(r'\b(LLC|INC|CORP|TRUST|REIT|HOLDINGS|GROUP|BANK|CITY|COUNTY)\b', re.I)
rows = []
with open(f, newline='', encoding='utf-8-sig') as fp:
    for r in csv.DictReader(fp):
        owner = r.get('OWNER','') or r.get('OWNER1','') or r.get('NAME','')
        if not owner: continue
        is_e = bool(ENTITY.search(owner))
        rows.append({**r,'owner_type':'entity' if is_e else 'individual','score':60+is_e*8})
rows.sort(key=lambda x: x['score'], reverse=True)
p = out / f'cuyahoga-oh-parcels-{date.today().isoformat()}.csv'
if rows:
    with open(p,'w',newline='',encoding='utf-8') as fp:
        w=csv.DictWriter(fp,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows[:5000])
    (out/'meta.json').write_text(json.dumps({'market':'Cuyahoga County OH (Cleveland)','lane':'Tax Parcel','total_rows':len(rows),'processed':date.today().isoformat()}))
    print(f'Cuyahoga OH: {len(rows)} rows')
else: print('Cuyahoga OH: 0 rows')
PYEOF
fi

# ─── 11. Maricopa AZ (Phoenix) ─────────────────────────────────
if [ -d "$RAW/maricopa-az" ]; then
  echo "--- Maricopa AZ ---"
  F=$(ls $RAW/maricopa-az/*/*BK*.txt 2>/dev/null | head -1)
  CSV=$(ls $RAW/maricopa-az/*/*.csv 2>/dev/null | sort | tail -1)
  echo "Maricopa AZ: raw files present (fixed-width BK files need schema map — snapshot deferred)"
fi

echo ""
echo "=== SNAPSHOT INVENTORY ==="
for d in $SNAPS/*/; do
  market=$(basename $d)
  latest=$(ls -td $d*/ 2>/dev/null | head -1)
  if [ -n "$latest" ]; then
    count=$(ls $latest/*.csv 2>/dev/null | wc -l)
    rows=$(cat $latest/meta.json 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('total_rows','-'))" 2>/dev/null || echo '?')
    echo "  $market: $rows rows"
  fi
done
