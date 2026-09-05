#!/usr/bin/env python3
"""Jefferson AL v4 — click 'Download Delinquent List' and capture the file."""
import asyncio
import json
import os
from pathlib import Path

OUT = Path("/opt/leadcurate/raw_imports/jefferson-al") / os.popen("date -u +%Y-%m-%d").read().strip()
OUT.mkdir(parents=True, exist_ok=True)


async def main():
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--ignore-certificate-errors"],
        )
        ctx = await browser.new_context(
            ignore_https_errors=True,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1400, "height": 900},
            accept_downloads=True,
        )
        page = await ctx.new_page()
        responses = []

        async def on_response(resp):
            try:
                if resp.request.resource_type in ("xhr", "fetch"):
                    body = None
                    try:
                        body = await resp.text()
                    except Exception:
                        pass
                    responses.append({"url": resp.url, "method": resp.request.method, "status": resp.status, "size": len(body) if body else 0, "body": body})
            except Exception:
                pass

        page.on("response", lambda r: asyncio.create_task(on_response(r)))

        print("=== Navigate to DelqSearch ===")
        await page.goto("https://eringcapture.jccal.org/", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(3500)
        # close modal
        try:
            await (await page.query_selector("#overlay button:has-text('Close')")).click()
            await page.wait_for_timeout(800)
        except Exception:
            pass
        await page.evaluate("() => { const o=document.querySelector('#overlay'); if(o)o.remove(); }")
        # open burger menu
        try:
            await (await page.query_selector("#burgerIcon")).click()
            await page.wait_for_timeout(1200)
        except Exception:
            pass
        # click Delinquent Search
        try:
            await page.click("text=Delinquent Search", timeout=10000)
        except Exception as e:
            print(f"  delinq click err: {e}")
        await page.wait_for_timeout(5000)
        print(f"  url now: {page.url}")
        await page.screenshot(path=str(OUT / "v4_01_delqsearch.png"), full_page=True)

        # Try to select "Show All" in the search-type dropdown
        print("\n=== Setting search type to Show All ===")
        try:
            selects = await page.query_selector_all("select")
            print(f"  found {len(selects)} select(s)")
            if selects:
                # Try set first select to "Show All"
                await selects[0].select_option(label="Show All")
                await page.wait_for_timeout(500)
                print("  set first select -> Show All")
        except Exception as e:
            print(f"  show all err: {e}")

        # Now click "Download Delinquent List"
        print("\n=== Clicking 'Download Delinquent List' ===")
        responses.clear()
        download = None
        try:
            async with page.expect_download(timeout=60000) as dl_info:
                await page.click("button:has-text('Download Delinquent List')", timeout=10000)
                print("  click sent, waiting for download...")
            download = await dl_info.value
            save_path = OUT / (download.suggested_filename or "jefferson-al-delinquent.dat")
            await download.save_as(str(save_path))
            print(f"  ✓ Downloaded: {save_path} ({save_path.stat().st_size:,} bytes)")
        except Exception as e:
            print(f"  download err: {e}")
            # Maybe it's not a download but an inline action — capture XHRs
            await page.wait_for_timeout(8000)

        await page.screenshot(path=str(OUT / "v4_02_after_download.png"), full_page=True)

        # Also try clicking Search to load all visible results, then scrape table
        print("\n=== Trying Search button to load results table ===")
        responses.clear()
        try:
            await page.click("#btnSearch", timeout=8000)
            print("  clicked #btnSearch")
            await page.wait_for_timeout(6000)
        except Exception as e:
            print(f"  search err: {e}")

        # Capture results table from the page
        print("\n=== Scraping visible table ===")
        scraped_rows = []
        try:
            tables = await page.query_selector_all("table")
            for ti, t in enumerate(tables):
                trs = await t.query_selector_all("tr")
                print(f"  table[{ti}]: {len(trs)} rows")
                for tr in trs:
                    cells = await tr.query_selector_all("td, th")
                    row = [(await c.inner_text()).strip() for c in cells]
                    if row:
                        scraped_rows.append(row)
        except Exception as e:
            print(f"  scrape err: {e}")

        if scraped_rows:
            import csv as csvlib
            scrape_csv = OUT / "v4_scraped_table.csv"
            with open(scrape_csv, "w", newline="", encoding="utf-8") as fp:
                w = csvlib.writer(fp)
                w.writerows(scraped_rows)
            print(f"  wrote scraped: {scrape_csv} ({len(scraped_rows)} rows)")
            print("  first 3 rows:")
            for r in scraped_rows[:3]:
                print(f"    {r}")

        # Save XHRs
        meaningful = [r for r in responses if not any(n in r["url"] for n in (
            "googletagmanager", "google-analytics", "google.com/g/", "citibot", "audioeye", "facebook"
        ))]
        (OUT / "v4_xhr.json").write_text(
            json.dumps([{**r, "body": (r["body"][:8000] if r["body"] else None)} for r in meaningful],
                       indent=2, default=str), encoding="utf-8")
        print(f"\n=== {len(meaningful)} meaningful XHR ===")
        for r in meaningful[:20]:
            print(f"  {r['status']} {r['method']} {r['url'][:140]} ({r['size']}B)")

        await browser.close()


asyncio.run(main())
