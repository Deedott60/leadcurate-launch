# JS Blocker Bypass — Field Playbook (canonical, repo-tracked)

> **This is the canonical copy.** It lives in the git repo so Claude, Codex, and Danny/Hermes can all read AND write it — the old copy at `C:\Users\lenovo\.claude\skills\leadcurate-js-blocker-bypass\SKILL.md` was local-only to one machine.

**Hard rule:** never claim a list is complete unless the row count came back from a real call this session. Page shells with placeholder narrative are NOT data.

## When to use this

Trigger when a county source returns one of these symptoms:

- `curl` gets 200 but file is < 50 KB and contains words like "loading…", "data table will appear", "JavaScript is required"
- The page text is legal narrative or instructions but has no `<table>` rows
- Direct file URL guesses 404 for every reasonable filename pattern
- Page works fine when opened in a browser but Playwright/curl gets nothing

## The 4 blocker patterns (in order of frequency)

### Pattern 1 — Static page, file linked from JS-rendered button

**Looks like:** Page shell loads, then JS injects a `<a download>` link.
**Examples hit:** Harris HCAD (cracked via Chrome MCP `read_page`), Allen IN XLSX.
**Fix:** Use Playwright `page.content()` AFTER `wait_for_load_state("networkidle")`, then grep the rendered HTML for download links. Or use `read_page` in Chrome MCP.

```python
async with async_playwright() as pw:
    browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
    page = await (await browser.new_context(ignore_https_errors=True)).new_page()
    await page.goto(url, wait_until="networkidle", timeout=60000)
    html = await page.content()
    # Now grep html for href patterns ending in .pdf/.xlsx/.zip
```

### Pattern 2 — SPA with REST/GraphQL API (Capture CAMA, ArcGIS portals, custom React)

**Looks like:** Page is a React/Vue/Angular shell. Data loads via `fetch()` to a separate API host.
**Examples hit:** Jefferson AL (`jeffersonexpress.capturecama.com` + AWS Cognito), eringcapture portal.
**Fix:** Use Playwright network capture to find the API host, then replay the calls server-side with proper headers.

```python
api_calls = []
page.on("request", lambda req: api_calls.append({
    "method": req.method, "url": req.url, "headers": req.headers, "post_data": req.post_data
}) if req.resource_type in ("xhr", "fetch") else None)

await page.goto(url, wait_until="networkidle")
await page.click("text=Search")  # or whatever the button is
await page.wait_for_timeout(5000)
# api_calls now contains every XHR — find the one returning the parcel list
```

**Key insight:** API hosts are often reusable. Once you know a vendor (Capture CAMA = `*.capturecama.com`, Tyler = `*.tylertech.com`, GovTech = `*.govtechcdn.com`), the SAME pattern works for every county on that vendor.

### Pattern 3 — ASP.NET WebForms postback (county dot-net sites)

**Looks like:** Page has a `<form>` with `__VIEWSTATE` + `__EVENTVALIDATION` hidden fields. Search button triggers a POST that re-renders the WHOLE page.
**Examples hit:** Forsyth NC (ncptscloud), older Wake County forms.
**Fix:** Use `requests.Session()` to preserve `__VIEWSTATE` between calls.

```python
import requests
from bs4 import BeautifulSoup
s = requests.Session()
r = s.get(search_page_url)
soup = BeautifulSoup(r.text, "html.parser")
form_data = {tag["name"]: tag.get("value", "") for tag in soup.select("input[type=hidden]")}
form_data["searchTextBox"] = "your query"
form_data["searchButton"] = "Search"
r2 = s.post(search_page_url, data=form_data)
# r2.text now contains the rendered results table
```

### Pattern 4 — Cloudflare / Akamai / PerimeterX bot protection

**Looks like:** curl gets a 200 with a "Just a moment…" page, or 403 with "challenge required".
**Examples hit:** None in LeadCurate scope yet. Common on attorney-general lien databases.
**Fix:** Playwright handles most challenges automatically because it's a real browser. If still blocked, use `playwright-stealth` plugin or pivot to a different data source.

```python
# pip install playwright-stealth
from playwright_stealth import stealth_async
await stealth_async(page)
await page.goto(url)
```

## Decision tree

```
County data not coming back as expected?
├── Is the HTML < 50 KB AND mentions "loading" or "JavaScript required"?
│   ├── YES → JS blocker — go to Playwright (Pattern 1 or 2)
│   └── NO  → Probably wrong URL — check sitemap.xml, search by year
│
├── Does the rendered page have a <table> after networkidle?
│   ├── YES → It's there, just JS-rendered. Extract via page.query_selector_all("tr")
│   └── NO  → API-driven. Capture XHR calls and replay (Pattern 2)
│
└── Does the response contain "challenge" / "Cloudflare" / "Just a moment"?
    └── YES → Bot protection (Pattern 4). Try playwright-stealth.
```

## Speed vs. cost — when to escalate

1. **Try `curl` first** (1 second, free). Works for ArcGIS Hub, Socrata, direct file links.
2. **Try `WebFetch` second** (3 seconds, free) — better than curl at finding download links inside marketing copy because it reads the rendered text.
3. **Try `Playwright` third** (10–30 seconds, free) — solves ~90% of remaining cases. THIS IS THE DURABLE FIX.
4. **Try Chrome MCP fourth** (variable, requires user's browser + domain allowlist) — only when Playwright can't reach the site due to IP-based blocks (rare).
5. **Last resort: paid scraping API** — Firecrawl, Browserless, ScrapingBee. ~$50–100/mo. Use only if 1–4 all fail AND the source is critical.

## What's installed on the VPS

- **Playwright 1.60.0** at `/usr/local/lib/python3.12/dist-packages/playwright`
- **Chromium browser** binary via `playwright install chromium`
- **Run with:** `python3 -c "from playwright.async_api import async_playwright; ..."`
- **Always pass:** `args=["--no-sandbox", "--disable-dev-shm-usage", "--ignore-certificate-errors"]` (the VPS has no GUI and lots of county sites have broken certs)

## Per-county overrides (append as we crack them)

| County | Vendor / pattern | Working approach |
|---|---|---|
| Harris TX (Houston) | Static HTML with JS-injected zip links | Chrome MCP `read_page` → curl from VPS |
| Cobb GA | Static page, link to revize CDN | curl with double-`Delinquent/Delinquent/` path on `cms9files.revize.com/cobbcounty/` |
| Jefferson AL | **Capture CAMA SPA + AWS Cognito** | Playwright → capture XHR to `jeffersonexpress.capturecama.com` → replay POSTs |
| Forsyth NC | ASP.NET WebForms | `requests.Session` with VIEWSTATE preservation |
| Mecklenburg NC | ArcGIS Hub | DCAT catalog discovery, direct CSV download (no JS) |
| Wake NC | Socrata SODA API | Direct JSON pull, no JS needed |

## Anti-pattern — what NOT to do

- ❌ Don't use Gemini Flash to parse property data. It triggers PII safety filters and refuses ~30% of legitimate property records. Use Claude Haiku, DeepSeek V3, or local Ollama instead.
- ❌ Don't run Playwright in headed mode on the VPS (no display). Always `headless=True`.
- ❌ Don't keep retrying the same broken URL with different paths — read the sitemap.xml first; it lists every page the CMS knows about.
- ❌ Don't fake user-agents to look like Googlebot. Some sites special-case Googlebot and serve garbage. Use a normal Chrome UA.

## Maintenance rule

When you crack a new pattern, ADD a row to the per-county table above before ending the session, then commit and push. The patterns repeat across counties — every documented win compounds.
