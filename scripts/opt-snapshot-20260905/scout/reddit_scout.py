#!/usr/bin/env python3
from scout_common import *
import xml.etree.ElementTree as ET

SUBREDDITS=['wholesaling','realestateinvesting','realestate']

def fetch_json(url):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 LeadCurateScout/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def fetch_rss(sub, limit):
    url=f'https://www.reddit.com/r/{sub}/new.rss'
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 LeadCurateScout/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        xml=r.read()
    root=ET.fromstring(xml)
    ns={'a':'http://www.w3.org/2005/Atom'}
    rows=[]
    for entry in root.findall('a:entry', ns)[:limit]:
        title=norm(entry.findtext('a:title','',ns))
        content=norm(entry.findtext('a:content','',ns))
        href=''
        for link in entry.findall('a:link', ns):
            if link.attrib.get('rel') == 'alternate' or not href:
                href=link.attrib.get('href','')
        ext=entry.findtext('a:id','',ns).rsplit('/',1)[-1] or str(abs(hash(href)))
        author_el=entry.find('a:author/a:name', ns)
        author=author_el.text if author_el is not None else ''
        posted=entry.findtext('a:updated','',ns) or None
        combined=f'{title} {content}'
        kw=keyword_hit(combined); market=market_hit(combined)
        if not kw: continue
        row={'source':'reddit','source_url':href,'external_id':ext,'market':market,'keyword':kw,
             'title':title[:300],'preview':content[:1000],'author':author,'posted_at':posted,
             'status':'new','metadata':{'subreddit':sub,'fetch':'rss'}}
        row['suggested_dm']=dm_template(row); rows.append(row)
    return rows

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dry-run', action='store_true'); ap.add_argument('--limit', type=int, default=50)
    args=ap.parse_args(); rows=[]
    for sub in SUBREDDITS:
        json_url=f'https://www.reddit.com/r/{sub}/new.json?limit={args.limit}'
        try:
            data=fetch_json(json_url)
            for child in data.get('data',{}).get('children',[]):
                d=child.get('data',{})
                title=norm(d.get('title')); text=norm((d.get('selftext') or '')[:1200]); combined=f'{title} {text}'
                kw=keyword_hit(combined); market=market_hit(combined)
                if not kw: continue
                row={'source':'reddit','source_url':'https://www.reddit.com'+d.get('permalink',''), 'external_id':d.get('id'),
                     'market':market, 'keyword':kw, 'title':title[:300], 'preview':text[:1000], 'author':d.get('author'),
                     'posted_at':datetime.fromtimestamp(float(d.get('created_utc',0)), timezone.utc).isoformat().replace('+00:00','Z'),
                     'status':'new','metadata':{'subreddit':sub,'score':d.get('score'),'num_comments':d.get('num_comments'),'fetch':'json'}}
                row['suggested_dm']=dm_template(row); rows.append(row)
        except Exception as e:
            print(f'WARN reddit JSON {sub}: {e}; trying RSS fallback', file=sys.stderr)
            try:
                rows.extend(fetch_rss(sub, args.limit))
            except Exception as rss_e:
                print(f'WARN reddit RSS {sub}: {rss_e}', file=sys.stderr)
        time.sleep(1)
    activity('Lead Scout Reddit run complete', f'Found {len(rows)} Reddit scout prospects')
    return post_rows(rows, args.dry_run)
if __name__=='__main__': raise SystemExit(main())
