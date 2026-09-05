import sys, csv
sys.path.insert(0, '.')
import process_verified_vacant as pvv
from collections import Counter

cfg = pvv.MARKETS['hamilton-tn']

rows = []
with open('/opt/leadcurate/raw_imports/hamilton-tn/2026-07-04/AssessorExport.csv', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f, fieldnames=cfg.get("csv_fields"))
    for row in reader:
        ok, rec = pvv.qualifies(row, cfg)
        if ok:
            ms = pvv.clean(rec["mail_state"]).upper()
            rec['is_absentee_owner'] = 'yes' if ms not in ("", cfg["state"]) else 'no'
            rows.append(rec)

print('total qualifying', len(rows))
absentee = [r for r in rows if r['is_absentee_owner'] == 'yes']
print('absentee total', len(absentee))
priority = [r for r in absentee if r['land_value'] <= 150000]
print('priority (absentee + land value <= 150k)', len(priority))
muni = Counter(r['municipality'] for r in rows)
print('municipality full universe', dict(muni.most_common(15)))
acreage_1_5 = sum(1 for r in rows if 1 <= r['total_acreage'] <= 5)
print('spot check acreage 1-5', acreage_1_5)
