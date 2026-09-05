#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re, sys, time, urllib.parse, urllib.request
from datetime import datetime, timezone

SB_URL=os.getenv('LEADCURATE_SUPABASE_URL','https://jdmlsraqioigbukspduo.supabase.co')
SB_KEY=os.getenv('LEADCURATE_SUPABASE_KEY','sb_publishable_ASWvbGMQAzrSJ_-DLwiGtQ_ABaYOTE4')
KEYWORDS=['tax delinquent list','absentee list','motivated seller list','motivated seller leads','need a list','need leads','looking for leads','looking for a list','probate list','foreclosure list','code violation list','skip trace','distressed list']
MARKETS={
 'Atlanta GA':['atlanta','fulton','cobb','dekalb'], 'Charlotte NC':['charlotte','mecklenburg'], 'Raleigh NC':['raleigh','wake'],
 'Houston TX':['houston','harris'], 'Louisville KY':['louisville','jefferson ky'], 'Birmingham AL':['birmingham','jefferson al'],
 'Memphis TN':['memphis','shelby'], 'Cleveland OH':['cleveland','cuyahoga'], 'Indianapolis IN':['indianapolis','marion'],
 'Dallas TX':['dallas','tarrant'], 'Phoenix AZ':['phoenix','maricopa'], 'Buffalo NY':['buffalo','erie'],
 'Greensboro NC':['greensboro','guilford'], 'Greenville SC':['greenville'], 'Charleston SC':['charleston'],
 'Lexington KY':['lexington','fayette'], 'Fort Wayne IN':['fort wayne','allen'], 'NYC':['nyc','new york'],
}
def now_iso(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00','Z')
def norm(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def keyword_hit(text):
    low=text.lower()
    for k in KEYWORDS:
        if k in low: return k
    return ''
def market_hit(text):
    low=text.lower()
    for market, aliases in MARKETS.items():
        if any(a in low for a in aliases): return market
    return ''
def dm_template(row):
    market=row.get('market') or '[market]'
    return f"Saw your post about {row.get('keyword') or 'lead data'} in {market}. I run LeadCurate — we build fresh county-record lead lists for real estate investors. If you tell me list type + market, I can quote the right pull and send a redacted sample."
def post_rows(rows, dry_run=False):
    if dry_run:
        print(json.dumps(rows, indent=2)); return 0
    if not rows:
        print('No matching scout prospects found.'); return 0
    url=SB_URL.rstrip()+'/rest/v1/scout_prospects?on_conflict=source,external_id'
    data=json.dumps(rows).encode()
    req=urllib.request.Request(url, data=data, method='POST', headers={
        'apikey':SB_KEY, 'Authorization':'Bearer '+SB_KEY, 'Content-Type':'application/json',
        'Prefer':'resolution=ignore-duplicates,return=representation'
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        body=r.read().decode()
        print('HTTP', r.status, body[:2000])
    return 0
def activity(title, body):
    payload={'event_type':'conf:status','source':'lead-scout','title':title,'body':body,'target':'claude'}
    req=urllib.request.Request(SB_URL.rstrip()+'/rest/v1/activity_feed', data=json.dumps(payload).encode(), method='POST', headers={
        'apikey':SB_KEY, 'Authorization':'Bearer '+SB_KEY, 'Content-Type':'application/json', 'Prefer':'return=minimal'
    })
    try: urllib.request.urlopen(req, timeout=15).read()
    except Exception as e: print('activity post failed:', e, file=sys.stderr)
