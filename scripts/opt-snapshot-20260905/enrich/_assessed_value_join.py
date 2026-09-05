#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, re, sys
from pathlib import Path
csv.field_size_limit(sys.maxsize)
PARCEL_COLUMNS=['parcel_id','parcel','apn','pin','pin_num','pin10','realid','reid','parcelid','parcel id','lowparcelid','tax parcel id','taxparcelid']
VALUE_COLUMNS=['assessed_value','total_value_assd','totassess','total assessed ($)','tot_assess','tot assessed','market_value','appraised_value','totappr','tot appr','tot appraised ($)','tot_appr','taxable_value']
def clean_header(h): return h.replace('\ufeff','').strip()
def norm_name(h): return re.sub(r'[^a-z0-9]+',' ',clean_header(h).lower()).strip()
def norm_parcel(v): return re.sub(r'[^a-z0-9]','',str(v or '').lower())
def money(v):
    raw=str(v or '').strip()
    if not raw: return ''
    cleaned=re.sub(r'[$,\s]','',raw)
    try:
        n=float(cleaned); return str(int(n)) if n.is_integer() else str(n)
    except ValueError: return raw
def find_col(headers,candidates):
    by={norm_name(h):h for h in headers}; compact={norm_name(h).replace(' ',''):h for h in headers}
    for c in candidates:
        nc=norm_name(c)
        if nc in by: return by[nc]
        if nc.replace(' ','') in compact: return compact[nc.replace(' ','')]
    return None
def load_lookup(path, parcel_col, value_col):
    if not path.exists(): raise SystemExit(f'FATAL: lookup file not found: {path}')
    with path.open(encoding='utf-8-sig', errors='replace', newline='') as fp:
        reader=csv.DictReader(fp); headers=reader.fieldnames or []
        parcel_col=parcel_col or find_col(headers, PARCEL_COLUMNS)
        value_col=value_col or find_col(headers, VALUE_COLUMNS)
        if not parcel_col: raise SystemExit(f'FATAL: no parcel column found in lookup {path}')
        if not value_col: raise SystemExit(f'FATAL: no assessed/appraised value column found in lookup {path}')
        lookup={}
        for row in reader:
            key=norm_parcel(row.get(parcel_col)); val=money(row.get(value_col))
            if key and val: lookup.setdefault(key,val)
    print(f'Loaded {len(lookup):,} assessed values from {path} ({parcel_col} -> {value_col})', file=sys.stderr)
    return lookup
def enrich(input_path, output_path, lookup_path, parcel_col, lookup_parcel_col, lookup_value_col):
    lookup=load_lookup(lookup_path, lookup_parcel_col, lookup_value_col)
    with input_path.open(encoding='utf-8-sig', errors='replace', newline='') as fp:
        reader=csv.DictReader(fp); headers=reader.fieldnames or []
        source_parcel=parcel_col or find_col(headers, PARCEL_COLUMNS)
        if not source_parcel: raise SystemExit(f'FATAL: no parcel column found in input {input_path}')
        out_fields=list(headers)
        if 'assessed_value' not in out_fields: out_fields.append('assessed_value')
        rows=[]; matched=0
        for row in reader:
            if not money(row.get('assessed_value')):
                val=lookup.get(norm_parcel(row.get(source_parcel)))
                if val:
                    row['assessed_value']=val; matched+=1
            rows.append(row)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8', newline='') as fp:
        writer=csv.DictWriter(fp, fieldnames=out_fields); writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {len(rows):,} rows to {output_path}; filled assessed_value for {matched:,}', file=sys.stderr)
    return 0
def main(default_lookup=None):
    ap=argparse.ArgumentParser(); ap.add_argument('input_csv'); ap.add_argument('output_csv')
    ap.add_argument('--lookup', default=default_lookup); ap.add_argument('--parcel-col'); ap.add_argument('--lookup-parcel-col'); ap.add_argument('--lookup-value-col')
    args=ap.parse_args()
    if not args.lookup: raise SystemExit('FATAL: --lookup is required for this market')
    return enrich(Path(args.input_csv),Path(args.output_csv),Path(args.lookup),args.parcel_col,args.lookup_parcel_col,args.lookup_value_col)
