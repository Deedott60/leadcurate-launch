#!/usr/bin/env python3
from scout_common import *
from html.parser import HTMLParser

URLS=['https://www.biggerpockets.com/forums']

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self._href=None; self._buf=[]
    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self._href=dict(attrs).get('href'); self._buf=[]
    def handle_data(self, data):
        if self._href is not None: self._buf.append(data)
    def handle_endtag(self, tag):
        if tag == 'a' and self._href is not None:
            text=norm(' '.join(self._buf))
            if text: self.links.append({'text':text,'href':urllib.parse.urljoin('https://www.biggerpockets.com', self._href)})
            self._href=None; self._buf=[]

def fetch_links_static(url):
    req=urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 LeadCurateScout/1.0'})
    with urllib.request.urlopen(req, timeout=30) as r:
        html=r.read().decode('utf-8','replace')
    parser=LinkParser(); parser.feed(html)
    return parser.links[:250]

def fetch_links_playwright(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        page=browser.new_page(user_agent='LeadCurateScout/1.0')
        page.goto(url, wait_until='networkidle', timeout=60000)
        links=page.locator('a').evaluate_all("els => els.slice(0,250).map(a => ({text:a.innerText, href:a.href}))")
        browser.close()
        return links

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--dry-run', action='store_true'); args=ap.parse_args(); rows=[]
    use_playwright=True
    try:
        import playwright  # noqa
    except Exception:
        use_playwright=False
        print('WARN: playwright unavailable; using static BiggerPockets HTML fallback', file=sys.stderr)
    for url in URLS:
        try:
            if use_playwright:
                try:
                    links=fetch_links_playwright(url)
                except Exception as e:
                    print(f'WARN BiggerPockets Playwright {url}: {e}; trying static fallback', file=sys.stderr)
                    links=fetch_links_static(url)
            else:
                links=fetch_links_static(url)
        except Exception as e:
            print(f'WARN BiggerPockets {url}: {e}', file=sys.stderr); continue
        for item in links:
            title=norm(item.get('text'))
            href=item.get('href') or url
            if len(title) < 12: continue
            kw=keyword_hit(title); market=market_hit(title)
            # BiggerPockets' forum index contains a lot of city/filter navigation links.
            # Require an actual intent keyword so menus do not become false leads.
            if not kw: continue
            ext='bp-'+str(abs(hash(href)))
            row={'source':'biggerpockets','source_url':href,'external_id':ext,'market':market,'keyword':kw,
                 'title':title[:300],'preview':title[:1000],'author':'','posted_at':None,'status':'new','metadata':{'seed_url':url,'fetch':'playwright' if use_playwright else 'static'}}
            row['suggested_dm']=dm_template(row); rows.append(row)
    activity('Lead Scout BiggerPockets run complete', f'Found {len(rows)} BiggerPockets scout prospects')
    return post_rows(rows, args.dry_run)
if __name__=='__main__': raise SystemExit(main())
