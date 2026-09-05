#!/usr/bin/env python3
"""Jefferson AL v3 — click burger menu first, then Delinquent Search."""
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

        # Close modal
        try:
            close_btn = await page.query_selector("#overlay button:has-text('Close')")
            if close_btn:
                await close_btn.click()
                await page.wait_for_timeout(1200)
                print("  modal closed")
        except Exception:
            pass
        # Belt and suspenders: remove overlay via JS too
        await page.evaluate("""() => {
            const o = document.querySelector('#overlay');
            if (o) o.remove();
            document.body.style.overflow = 'auto';
        }""")

        # Click burger menu to open nav
        print("\n=== Opening hamburger menu ===")
        for sel in ["#burgerIcon", "button#burgerIcon", "[id*=burger]"]:
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.click(timeout=5000)
                    print(f"  clicked {sel}")
                    await page.wait_for_timeout(1500)
                    break
            except Exception as e:
                print(f"  {sel} -> {e}")

        await page.screenshot(path=str(OUT / "v3_01_menu_open.png"), full_page=True)

        # Now click Delinquent Search from the open menu
        print("\n=== Clicking Delinquent Search (menu open) ===")
        responses.clear()
        clicked = False
        for sel in [
            "text=Delinquent Search",
            "a:has-text('Delinquent Search')",
            "li:has-text('Delinquent Search')",
            "[href*=delinquent]",
            "text=Delinquent",
        ]:
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.click(timeout=10000)
                    print(f"  clicked via {sel}")
                    clicked = True
                    break
            except Exception as e:
                print(f"  {sel} -> {str(e)[:120]}")

        await page.wait_for_timeout(8000)
        print(f"  url now: {page.url}")
        print(f"  XHR after click: {len(responses)}")
        await page.screenshot(path=str(OUT / "v3_02_delinquent_page.png"), full_page=True)
        (OUT / "v3_02_delinquent.html").write_text(await page.content(), encoding="utf-8")

        # Look for inputs/buttons on this page
        print("\n=== Page controls now: ===")
        inputs = await page.query_selector_all("input, select, button, a")
        for inp in inputs[:50]:
            try:
                t = await inp.evaluate(
                    "el => ({tag:el.tagName, type:el.type||'', name:el.name||'', id:el.id||'', placeholder:el.placeholder||'', text:(el.innerText||'').slice(0,60), href:el.href||''})"
                )
                if any([t["name"], t["id"], t["placeholder"], t["text"], t["href"]]):
                    print(f"  {t['tag']}#{t['id']} type={t['type']} name={t['name']} ph={t['placeholder']!r} text={t['text']!r}")
            except Exception:
                pass

        # Try a wildcard / blank search
        print("\n=== Trying blank search to load full results ===")
        responses.clear()
        for sel in [
            "button:has-text('Search')",
            "input[type=submit]",
            "button[type=submit]",
            "button:has-text('Submit')",
        ]:
            try:
                el = await page.query_selector(sel)
                if el:
                    await el.click(timeout=8000)
                    print(f"  clicked submit via {sel}")
                    break
            except Exception as e:
                print(f"  {sel} -> {str(e)[:120]}")
        await page.wait_for_timeout(8000)
        print(f"  XHR after submit: {len(responses)}")
        await page.screenshot(path=str(OUT / "v3_03_after_search.png"), full_page=True)
        (OUT / "v3_03_search_html.html").write_text(await page.content(), encoding="utf-8")

        # Filter noise and dump
        meaningful = [r for r in responses if not any(n in r["url"] for n in (
            "googletagmanager", "google-analytics", "google.com/g/", "citibot",
            "audioeye", "facebook"
        ))]
        (OUT / "v3_xhr_responses.json").write_text(
            json.dumps([{**r, "body": (r["body"][:5000] if r["body"] else None)} for r in meaningful],
                       indent=2, default=str), encoding="utf-8")
        print(f"\n=== {len(meaningful)} meaningful XHR ===")
        for r in meaningful[:25]:
            print(f"  {r['status']} {r['method']} {r['url'][:140]} ({r['size']}B)")

        await browser.close()


asyncio.run(main())
