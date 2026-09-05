#!/usr/bin/env python3
"""Jefferson AL eringcapture.jccal.org — v2 with modal-closer."""
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
                    responses.append({
                        "url": resp.url, "method": resp.request.method,
                        "status": resp.status, "size": len(body) if body else 0,
                        "body": body,
                    })
            except Exception:
                pass

        page.on("response", lambda r: asyncio.create_task(on_response(r)))

        print("=== Loading eringcapture.jccal.org ===")
        await page.goto("https://eringcapture.jccal.org/", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(4000)

        # STEP 1: Kill the modal overlay
        print("\n=== Closing modal overlay ===")
        closed_modal = False
        for sel in ["#overlay button:has-text('Close')", "button:has-text('Close')", "text=Close", "#overlay [aria-label=Close]"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.click(timeout=5000)
                    await page.wait_for_timeout(1500)
                    print(f"  closed via {sel}")
                    closed_modal = True
                    break
            except Exception as e:
                print(f"  {sel} -> {e}")
        if not closed_modal:
            # Nuke it via JS
            try:
                await page.evaluate("""() => {
                    const overlay = document.querySelector('#overlay');
                    if (overlay) overlay.remove();
                    document.body.style.overflow = 'auto';
                }""")
                print("  removed overlay via JS")
            except Exception as e:
                print(f"  JS remove failed: {e}")

        await page.wait_for_timeout(1500)
        await page.screenshot(path=str(OUT / "v2_01_after_modal_close.png"), full_page=True)

        # STEP 2: Click "Delinquent Search"
        print("\n=== Clicking Delinquent Search ===")
        responses.clear()
        clicked = False
        for sel in ["text=Delinquent Search", "a:has-text('Delinquent Search')", "button:has-text('Delinquent Search')", "text=Delinquent"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.click(timeout=10000)
                    print(f"  clicked via {sel}")
                    clicked = True
                    break
            except Exception as e:
                print(f"  {sel} -> {e}")
        await page.wait_for_timeout(6000)
        print(f"  url now: {page.url}")
        print(f"  XHR after Delinquent Search click: {len(responses)}")
        await page.screenshot(path=str(OUT / "v2_02_delinquent_page.png"), full_page=True)
        (OUT / "v2_02_delinquent_html.html").write_text(await page.content(), encoding="utf-8")

        # STEP 3: Look for a search form, try to submit empty or wildcard to get full results
        print("\n=== Looking for search controls ===")
        inputs = await page.query_selector_all("input, select, button")
        for inp in inputs[:30]:
            try:
                t = await inp.evaluate("el => ({tag:el.tagName, type:el.type||'', name:el.name||'', id:el.id||'', placeholder:el.placeholder||'', text:el.innerText||'' }) ")
                if any([t["name"], t["id"], t["placeholder"], t["text"]]):
                    print(f"  {t}")
            except Exception:
                pass

        # Try clicking a "Search" / "Submit" button to trigger results load
        print("\n=== Triggering search ===")
        responses.clear()
        for sel in ["button:has-text('Search')", "input[type=submit]", "button[type=submit]", "button.search-btn"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.click(timeout=8000)
                    print(f"  clicked submit via {sel}")
                    break
            except Exception as e:
                print(f"  {sel} -> {e}")
        await page.wait_for_timeout(8000)
        print(f"  XHR after submit: {len(responses)}")
        await page.screenshot(path=str(OUT / "v2_03_after_search.png"), full_page=True)
        (OUT / "v2_03_search_html.html").write_text(await page.content(), encoding="utf-8")

        # Save the meaningful XHR responses (filter analytics noise)
        meaningful = [r for r in responses if not any(n in r["url"] for n in (
            "googletagmanager", "google-analytics", "google.com/g/", "citibot",
            "audioeye", "facebook", "GetTenantAssets", "GetTheme"
        ))]
        (OUT / "v2_xhr_responses.json").write_text(
            json.dumps([{**r, "body": (r["body"][:5000] if r["body"] else None)} for r in meaningful],
                       indent=2, default=str), encoding="utf-8")
        print(f"\n=== {len(meaningful)} meaningful XHR captured ===")
        for r in meaningful[:25]:
            print(f"  {r['status']} {r['method']} {r['url'][:140]} ({r['size']}B)")

        await browser.close()


asyncio.run(main())
