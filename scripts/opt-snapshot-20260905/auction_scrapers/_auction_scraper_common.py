#!/usr/bin/env python3
from __future__ import annotations
import argparse, asyncio, csv, os, re, sys
from datetime import datetime
from pathlib import Path

DATE_RE = re.compile(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b', re.I)
PARCEL_RE = re.compile(r'\b(?:parcel(?:\s*(?:id|#|number|no\.))?|pin|apn)\s*[:#-]?\s*([A-Z0-9][A-Z0-9.\-]{4,})\b', re.I)

def parse_args(market: str, default_url: str, default_out: str):
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default=os.getenv(f'{market.upper().replace("-", "_")}_AUCTION_URL', default_url))
    ap.add_argument('--out', default=default_out)
    ap.add_argument('--market', default=market)
    return ap.parse_args()

def rows_from_text(text: str, url: str, market: str):
    rows=[]
    for raw in text.splitlines():
        line=' '.join(raw.split())
        if not line: continue
        d=DATE_RE.search(line)
        if not d: continue
        p=PARCEL_RE.search(line)
        rows.append({
            'market': market,
            'parcel_id': p.group(1) if p else '',
            'auction_date': d.group(0),
            'source_url': url,
            'raw_text': line[:500],
            'scraped_at': datetime.utcnow().replace(microsecond=0).isoformat()+'Z',
        })
    return rows

async def scrape(url: str, market: str):
    try:
        from playwright.async_api import async_playwright
    except Exception as exc:
        raise SystemExit('FATAL: Python Playwright is required. Install with: python3 -m pip install playwright && python3 -m playwright install chromium') from exc
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until='networkidle', timeout=60000)
        text = await page.locator('body').inner_text(timeout=30000)
        await browser.close()
    return rows_from_text(text, url, market)

def write_rows(rows, out_path: str):
    p=Path(out_path); p.parent.mkdir(parents=True, exist_ok=True)
    fields=['market','parcel_id','auction_date','source_url','raw_text','scraped_at']
    with p.open('w', encoding='utf-8', newline='') as fp:
        writer=csv.DictWriter(fp, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    print(f'Wrote {len(rows):,} auction rows to {p}', file=sys.stderr)

def main(market: str, default_url: str, default_out: str):
    args=parse_args(market, default_url, default_out)
    rows=asyncio.run(scrape(args.url, args.market))
    write_rows(rows, args.out)
    return 0
