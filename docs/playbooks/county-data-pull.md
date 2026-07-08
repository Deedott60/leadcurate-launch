# LeadCurate County Data Pull — Playbook (canonical, repo-tracked)

> **This is the canonical copy.** It lives in the git repo so Claude, Codex, and Danny/Hermes can all read AND write it — the old copy at `C:\Users\lenovo\.claude\skills\leadcurate-county-data-pull\SKILL.md` was local-only to one machine and neither Codex nor Danny could ever reach it. That's why counties kept getting re-solved from scratch. Don't let that happen again: this file is the one that matters now.

Use this any time LeadCurate needs to (a) refresh existing market data, (b) add a new county, or (c) turn raw downloads into a sellable Discovery Snapshot.

The business: LeadCurate sells curated, limited-seat property data slices to real-estate investors. This playbook is the **data layer** only.

## MAINTENANCE RULE — read first, update after

**Every time you successfully pull a new county, fix a broken URL, or work around a new blocker — APPEND it to the relevant section of this file before ending the session, then commit + push.** That is the explicit operator instruction. The value of this file is its accuracy; stale entries make it worse than nothing.

The same rule applies to processing patterns. If you build a Discovery Snapshot for a new lane (probate, code violation, etc.), document the column mapping in "Processing patterns" so the next session doesn't re-derive it.

### Also keep in sync

Two other living documents track related state:
1. `docs/leadcurate-data-inventory-audit.md` + `docs/data-audit/index.html` — partner-facing market/lane summary.
2. `docs/CURRENT-HANDOFF.md` — active task state (separate from this playbook, which is the durable reference).

## VPS infrastructure

- Host: `srv1564456` at `76.13.25.117` (Hostinger Ubuntu 24.04, 2 vCPU / 7.8 GB RAM / 96 GB disk)
- SSH alias: `leadcurate-vps` (config in `~/.ssh/config`, key `~/.ssh/leadcurate_vps_ed25519`)
- Connect with: `ssh leadcurate-vps`
- Docker 29 + Compose v5 preinstalled, nothing else
- Folder layout: `/opt/leadcurate/{raw_imports,processed,scripts,logs}/`
  - Each market gets its own subfolder under raw_imports (e.g. `mecklenburg-nc/`)
  - Within each market, dated subfolders for each pull (e.g. `2026-06-18/`)
  - Processed Discovery Snapshots go under `/opt/leadcurate/processed/{market}/{date}/`

## PowerShell ↔ SSH ↔ bash quoting — the lesson learned the hard way

PowerShell mangles bash heredocs, parens, brackets, `$` substitution, and ampersand chars on its way to SSH. The pattern that **always works**:

1. Write the bash/python script as a local file using the Write tool.
2. `scp` it to the VPS: `scp -o BatchMode=yes <local> leadcurate-vps:/opt/leadcurate/scripts/<name>.sh`
3. Execute via SSH: `ssh -o BatchMode=yes leadcurate-vps "chmod +x /opt/leadcurate/scripts/<name>.sh && bash /opt/leadcurate/scripts/<name>.sh"`

**Avoid:** `ssh leadcurate-vps "long inline bash with $variables, parens, brackets, |"`. It will silently mangle. Quick one-liners only.

When you do need a one-liner from PowerShell, escape `$` with backtick: `` `$DATE ``. Never use User-Agent strings with spaces or parens — use `Mozilla/5.0` or `LeadCurate-1.0` plain.

## Data source tiers — in priority order

For a new county, attempt these in order. Most counties resolve at Tier 1 or Tier 2.

### Tier 1 — ArcGIS Open Data Hub (best)
Many counties publish via ArcGIS Hub with a standard DCAT catalog at:
```
https://{HUB_HOSTNAME}/api/feed/dcat-us/1.1.json
```

Common hub hostname patterns to probe (~60% hit rate):
- `data-{countyname}.opendata.arcgis.com`
- `{countyname}gis.opendata.arcgis.com`
- `gis-{countyname}.opendata.arcgis.com`
- `{countyname}.hub.arcgis.com`
- `data.{cityname}.gov`
- `data.{countyname}{stateabbr}.gov`
- `open-data-hub-{countygis}.hub.arcgis.com` (Guilford pattern)
- `dcgis-{countyname}gis.hub.arcgis.com` (DeKalb pattern)
- `data-{countyname}.opendata.arcgis.com` (Cuyahoga pattern)
- `{cityname}-{countygis}.opendata.arcgis.com` (varied)

Once you find a working hub, every dataset has a direct download URL:
```
https://{HUB_HOSTNAME}/api/download/v1/items/{ITEM_ID}/csv?layers={N}
```
Also supports `xlsx`, `geojson`, `kml`, `shapefile`, `featureCollection`, `geoPackage`, `sqlite`, `filegdb`.

**Quirk**: ArcGIS Hub generates CSVs on-demand. First request may return HTTP 202 with `{"message":"Up to date download file is being generated. Please check back again later.","status":"Pending"}`. Wait 30-60 seconds and retry.

### Tier 2 — Socrata Open Data
NYC and Charlotte (mecklenburg-nc) use Socrata. Catalog query:
```
https://{HOST}/api/catalog/v1?q={KEYWORD}&limit=20
```
Direct CSV bulk export:
```
https://{HOST}/api/views/{DATASET_ID}/rows.csv?accessType=DOWNLOAD
```
JSON API:
```
https://{HOST}/resource/{DATASET_ID}.json?$limit=50000
```

### Tier 3 — Direct county-published downloads
County tax collector / trustee / assessor sites often publish daily or weekly CSV/XLSX/ZIP at predictable URLs. **Always check the linked-from page for the most current URL pattern**; counties rotate filenames.

### Tier 4 — Annual / one-off PDF publications
County clerks of court and trustees publish in-rem foreclosure petitions, delinquent advertisements, and tax sale lists as PDFs. Less convenient but legally required publications.

### Tier 5 — Chrome MCP browser drive
JS-rendered SPAs and ASP.NET postback forms. Use `mcp__Claude_in_Chrome__*` tools when Tiers 1-4 fail. See `docs/playbooks/js-blocker-bypass.md` for the full playbook.

### Tier 6 — Phone or public records request
Last resort. Some counties only publish in newspapers and require a phone call or FOIA-style request. Free, legally backed, takes 1-7 days.

## Working URL catalog

Update this whenever you discover, refresh, or fix a county URL. **Section below was last fully verified 2026-06-19 — counties solved 2026-06-25 through 2026-07-07 (York SC, Cabarrus NC, Lancaster SC, Gaston NC, Duval FL, Davidson TN, Tarrant TX blocker clear, Maricopa AZ, Shelby TN universal-key expansion, Jefferson KY code violations) were never appended here. Codex: backfill those entries from your own session work — see `docs/CURRENT-HANDOFF.md`.**

### NC

- **Mecklenburg NC (Charlotte) — Tier 2 Socrata**: `data.charlottenc.gov`. Catalog has parcel-lookup, vacant-land, lien-data (Financial Management System). DCAT at `https://data.charlottenc.gov/api/feed/dcat-us/1.1.json`.
- **Wake NC (Raleigh) — Tier 3 direct + Tier 1 ArcGIS**:
  - Daily-refreshed delinquent file: `https://services.wake.gov/collection_extracts/Real_Estate_Delq853_{MMDDYYYY}.xlsx` (use yesterday's date if today's 404s)
  - Daily-refreshed full tax bill zip: `https://services.wake.gov/collection_extracts/Real_Estate_Full853_{MMDDYYYY}.zip`
  - ArcGIS hub: `data.wakegov.com` (Parcels 436k, Property 237k)
- **Guilford NC (Greensboro) — Tier 1 ArcGIS** at `open-data-hub-guilfordgis.hub.arcgis.com`:
  - Tax Delinquent Report CSV: `https://open-data-hub-guilfordgis.hub.arcgis.com/api/download/v1/items/cd3e1ae082b0406aa12ca6bbfbe1b741/csv?layers=0` (10.5k rows)
  - Parcel Foreclosure CSV: `https://open-data-hub-guilfordgis.hub.arcgis.com/api/download/v1/items/861c637e817f4faf93323984483a2d9e/csv?layers=0` (3k rows incl. AuctionDate/Time/Location)
- **Forsyth NC (Winston-Salem) — Tier 1 ArcGIS** at `mapforsyth.org`:
  - Parcels Hosted CSV: `https://www.mapforsyth.org/api/download/v1/items/fd915221da64453aad7989b05f06707e/csv?layers=0` (167k rows incl. CURRENTOWNERNAME, PROPERTYADDRESS)
  - **Async generation**: expect HTTP 202 first time, retry after 30-60s.
- **Gaston NC, Cabarrus NC — NOT YET DOCUMENTED**: solved by Codex 2026-07-04, working URLs never appended. Backfill needed.

### SC

- **York SC, Lancaster SC — NOT YET DOCUMENTED**: solved by Codex 2026-07-04, working URLs never appended. Backfill needed.

### TX

- **Tarrant TX (Fort Worth) — Tier 3 weekly zip**: `https://www.tarrantcountytx.gov/content/dam/main/tax/tax-rolls/2026/TaxRoll{YYYYMMDD}.zip` — created weekly on Fridays, available the following Monday. Contains Master.dat (2 GB) + Rec.DAT (3.7 GB) fixed-width files. **~2M records.** (Codex cleared a blocker here 2026-07-04 — 4,915 rows extracted; exact fix not documented, backfill needed.)
- **Dallas TX — Tier 3 DCAD ViewPDFs.aspx**:
  - Real Property Roll 2025: `https://www.dallascad.org/ViewPDFs.aspx?type=3&id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CDATA%20PRODUCTS%5C2025_REAL_PROPERTY_CERT_APPR_ROLL.zip` (118 MB → 2.4 GB uncompressed)
  - Parcel 2025: `https://www.dallascad.org/ViewPDFs.aspx?type=3&id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CGIS%20PRODUCTS%5CPARCEL2025.zip`
  - Pattern uses URL-encoded Windows UNC path. Replace year in URL for older rolls.
- **Harris TX (Houston) — BLOCKED**: HCAD bulk zips at `http://pdata.hcad.org/data/cama/2026/Real_acct_owner.zip` return HTTP 200 with HTML redirect page (56 KB) instead of actual zip. The pdata page is JS-rendered. **Chrome MCP escalation required.** Codebook: `https://hcad.org/assets/uploads/pdf/pdataCodebook.pdf` lists the expected filenames.

### GA

- **Fulton GA (Atlanta) — Tier 1 ArcGIS** at `gisdata.fultoncountyga.gov`. 26 relevant property/tax datasets. Notable:
  - Tax Parcels 2025: `https://gisdata.fultoncountyga.gov/api/download/v1/items/ee82525ee33b49778055622c3a3cf534/csv?layers=0` (171k rows)
- **DeKalb GA — Tier 1 ArcGIS** at `dcgis-dekalbgis.hub.arcgis.com` (alias: `dekalbinsights-dekalbgis.opendata.arcgis.com`):
  - Tax Parcels 2025: `https://dcgis-dekalbgis.hub.arcgis.com/api/download/v1/items/7aa40e4967744cb0abadd6cb0dc23c97/csv?layers=0` (246k rows)
  - Tax Parcels 2024: `https://dcgis-dekalbgis.hub.arcgis.com/api/download/v1/items/5966b70b6f344154a803caa18aa4d98d/csv?layers=1` (246k rows)
- **Cobb GA — BLOCKED**: monthly delinquent PDFs at `cms9files.revize.com/cobbcounty/Property/Delinquent/...` — URL pattern changed since cached examples. Page at `https://www.cobbtax.gov/property/delinquent_taxes/index.php` lists current paths but loads via JS. **Chrome MCP escalation.**

### Other states

- **Maricopa AZ (Phoenix) — Tier 1 ArcGIS + ArcGIS Online items**: data sales page at `https://www.mcassessor.maricopa.gov/page/data_sales/` links 17 datasets. **Master files come from ArcGIS Online item API** (binary zip):
  - Secured Master: `https://www.arcgis.com/sharing/rest/content/items/936bbba512bf4c368618cc6e79e64668/data` (108 MB → 483 MB, contains BK100-BK500 text files)
  - Residential Master: `https://www.arcgis.com/sharing/rest/content/items/e22983d41d91490d90965544b718a120/data` (58 MB → 364 MB)
  - Commercial Master: `https://www.arcgis.com/sharing/rest/content/items/12ce08cf4d264f9d97bb7ef4d6eb9944/data` (21 MB → 525 MB)
  - Apartment Master: `https://www.arcgis.com/sharing/rest/content/items/0b5770a1b73f4637b8f92f088465890b/data` (343 KB)
  - (Codex reported "10,000 rows" pulled 2026-07-04 — confirm this used the master files above or a different endpoint; backfill.)
- **Marion IN (Indianapolis) — Tier 1 ArcGIS** at `data.indy.gov`:
  - Parcels w/ Owner + Assessed Values: `https://data.indy.gov/api/download/v1/items/0d28e222479743baa97f8f4456da7bb4/csv?layers=10` (347k rows)
  - HHC Parcel Owner: `https://data.indy.gov/api/download/v1/items/1dbe42c87bf24d5780bee61907bcbfc2/csv?layers=1` (408k rows)
- **Jefferson KY (Louisville) — Tier 1 ArcGIS** at `data.louisvilleky.gov`:
  - Property Foreclosures (premium): `https://data.louisvilleky.gov/api/download/v1/items/62c648120ab44b7794f8b484884efaa9/csv?layers=0` (3k court cases w/ Action_Filed, Sale_Date, Sale_Price, Purchaser)
  - Parcels: `https://data.louisvilleky.gov/api/download/v1/items/47085b87ac754d60942ea324a3b0f54f/csv?layers=1` (293k)
  - Lien Holder Final Orders: `https://data.louisvilleky.gov/api/download/v1/items/8f25a99a0e2347cc871a203ca325ab5e/csv?layers=0` (516)
  - Property Maintenance Violations: `https://data.louisvilleky.gov/api/download/v1/items/1fd891c3301c4c4581b86c338468fbe4/csv?layers=0` (17.7k) — used for the "18 live lookups" code-violations enrichment Codex ran 2026-07-04, PVA enrichment method not documented, backfill.
- **Cuyahoga OH (Cleveland) — Tier 1 ArcGIS** at `data-cuyahoga.opendata.arcgis.com`:
  - Tax Parcels: `https://data-cuyahoga.opendata.arcgis.com/api/download/v1/items/ffaaa1651d5540419469375d680f3245/csv?layers=0` (527k)
  - Parcel Sales 2021-Present: `https://data-cuyahoga.opendata.arcgis.com/api/download/v1/items/234b606bf7304a9f93bcc9e00afb28fc/csv?layers=0` (130k)
- **Shelby TN (Memphis) — Tier 3 direct S3 CSV — SCARCITY ASSET**: `https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv` (2.2k rows: parcel + alt parcel + street + tax sale code + GIS register URL). Found embedded in `https://www.shelbycountytrustee.com/191/Tax-Sale-Schedule`. **Most competitors don't know this URL exists.** Expanded 2026-07-04 into a 79-column "universal parcel key" via Memphis's Register GIS system — see `docs/shelby-memphis-universal-key.md` and `shelby_universal_key.py` for the full method (this one WAS documented, just not folded back into this catalog).
- **NYC (all 5 boroughs) — Tier 2 Socrata**: Tax Lien Sale Lists at `https://data.cityofnewyork.us/api/views/9rz4-mjek/rows.csv?accessType=DOWNLOAD` (264k rows: borough/block/lot/cycle/zip). Dataset id `9rz4-mjek`. Also DOB violations dataset (2.47M rows) used for the NYC Code Violations B2B lane — see `scripts/leadcurate/process_nyc_dob_restoration.py`.
- **Charleston SC — Tier 4 PDF publications**: `https://www.charlestoncounty.org/departments/delinquent-tax/files/{YEAR}-RP-Tax-Sale-Listing.pdf` and `MH-Tax-Sale-Listing.pdf`. PDFs only — need OCR/parse to convert.
- **Greenville SC — Tier 4 PDF**: `https://www.greenvillecounty.org/TaxCollector/pdf/taxsaleinfo.pdf` and HTML app at `https://www.greenvillecounty.org/appsAS400/taxsale/` (3.6 MB HTML).
- **Allen IN (Fort Wayne) — Tier 3 direct Excel disguised as PDF**: `https://www.allencounty.in.gov/DocumentCenter/View/11377/2025-Delinquent-Property` — Content is `.xlsx` (Microsoft Excel 2007+), rename file after download.
- **Erie NY (Buffalo) — Tier 4 PDF publications**: `https://www3.erie.gov/ecrpts/sites/www3.erie.gov.ecrpts/files/2026-05/filed-list-of-delinquent-taxes-9691950.1.pdf` (5 MB filed delinquent list). Filename includes a generated number — check `https://www3.erie.gov/ecrpts/auction-foreclosure-information` for current.
- **Fayette KY (Lexington) — Tier 1 ArcGIS** at `data.lexingtonky.gov` (4 property datasets in DCAT — catalog pulled, datasets not yet downloaded).
- **Jefferson AL (Birmingham) — BLOCKED**: `eringcapture.jccal.org` is a React SPA returning ~830 bytes of shell HTML. **Chrome MCP escalation required.**
- **Duval FL (Jacksonville), Davidson TN (Nashville) — NOT YET DOCUMENTED**: both were "previously zero-data," solved by Codex 2026-07-04 (3,000 rows each). Backfill needed.
- **Hamilton TN (Chattanooga) — IN PROGRESS 2026-07-08**: real buyer waiting, see `docs/CURRENT-HANDOFF.md` item 1. Append the working URL here once solved.

## Processing patterns (Discovery Snapshot pipeline)

For raw → sellable. Three example processors live at:
- `/opt/leadcurate/scripts/process_guilford.py` — tax-delinquent absentee lane
- `/opt/leadcurate/scripts/process_jefferson_ky_v2.py` — pre-foreclosure lane
- `/opt/leadcurate/scripts/process_shelby_tn.py` — tax-sale entry lane

### Standard pipeline

1. Load source CSV with `csv.DictReader`, `utf-8-sig` encoding to strip BOM
2. Apply lane filter (e.g. `MAIL_STATE != 'NC'` for absentee)
3. Compute score from urgency + amount-owed + freshness
4. Sort descending by score, take top N (100 for premium, 200 for entry)
5. Write three artifacts to `/opt/leadcurate/processed/{market}/{date}/`:
   - `{market}-{lane}-{date}.csv` — full snapshot
   - `{market}-{lane}-{date}-preview.csv` — 25 rows, owner names redacted to `J*** S****` for sales
   - `{market}-{lane}-{date}-meta.json` — product name, source URL, row counts, score range, geographic breakdown, compliance note

### Lane → score formula reference

| Lane | Inputs | Formula sketch |
|---|---|---|
| `tax_delinquent_absentee` | TOTAL_DUE_AMOUNT, PROP_ASSESS_VALUE, TAX_YEAR | `min(100, due/100) + min(50, assess/10000) + min(30, age*10)` |
| `pre_foreclosure` | Sale_Date, Action_Filed | `max(0, 90 - days_to_sale) if upcoming else max(0, 30+days_to_sale)` + filing recency bonus |
| `tax_sale_upcoming` | Tax Sale code, has_address | most-recent-code=60, has-street-number=30, has-GIS-url=10 |
| `individual_owner_occupant` | Owner name (not entity), mailing addr matches property | filter: !is_entity(name) AND first_token(mail)==first_token(property) |
| `individual_absentee_oos` | Owner name (not entity), mailing state != property state | filter: !is_entity(name) AND mail_state != property_state |

### Entity detection regex (re-used across markets)

For separating individual humans from LLCs/corps/trusts/REITs in any market's owner-name field:

```python
ENTITY_PATTERNS = [
    r"\bLLC\b", r"\bL L C\b", r"\bL\.L\.C\.\b",
    r"\bINC\b", r"\bINCORPORATED\b", r"\bCORP\b", r"\bCORPORATION\b",
    r"\bCOMPANY\b", r"\bCO\b",
    r"\bTRUST\b", r"\bTRUSTEE\b", r"\bTRUSTEES\b",
    r"\bPARTNERSHIP\b", r"\bLP\b", r"\bL\.P\.\b",
    r"\bPROPERTIES\b", r"\bPROPERTY\b", r"\bPROPCO\b",
    r"\bHOLDINGS\b", r"\bGROUP\b",
    r"\bASSOC\b", r"\bASSOCIATION\b",
    r"\bASSET\b", r"\bASSETS\b",
    r"\bINVESTMENT\b", r"\bINVESTMENTS\b",
    r"\bENTERPRISE\b", r"\bENTERPRISES\b",
    r"\bCHURCH\b", r"\bMINISTRIES\b", r"\bMINISTRY\b",
    r"\bCITY OF\b", r"\bCOUNTY OF\b", r"\bDEPARTMENT\b",
    r"\bAUTHORITY\b", r"\bDISTRICT\b",
    r"\bUNIVERSITY\b", r"\bCOLLEGE\b", r"\bSCHOOL\b",
    r"\bBANK\b", r"\bMORTGAGE\b", r"\bFOUNDATION\b",
    r"\bSFR\b", r"\bBORROWER\b", r"\bREIT\b", r"\bFUND\b",
    r"\bHOA\b", r"\bHOMEOWNERS\b", r"\bCONDOMINIUM\b",
    r"\bDEVELOPMENT\b", r"\bDEVELOPMENTS\b", r"\bDEVELOPER\b",
    r"\bREALTY\b", r"\bRENTALS\b", r"\bLEASING\b",
]
```

**Result across 4 markets (Mecklenburg, Marion, Forsyth, Cuyahoga):** consistently 76–85% of residential parcels are individual-owned. The institutional SFR funds are the loud minority. The Individual Owner Lane is the largest unrealized lane in the inventory.

**Owner-occupant detection gotcha:** matching mailing address to property address requires both fields to contain the house number. In Mecklenburg, Mailing_Address and Location both do. In Marion (`OWNERADDRESS` + `FULL_STNAME`), Forsyth (`MAILINGADDRESS1` + `PROPERTYADDRESS`), and Cuyahoga (`mail_addr` + `parcel_addr`), the field formats differ enough that naive first-token match fails. Fix per-market by normalizing both addresses through the same parser before comparing.

### Date parsing gotcha

Several county datasets include time + timezone: `2024/07/12 04:00:00+00`. Use:
```python
s = re.sub(r"[+-]\d{2}:?\d{0,2}$", "", s).strip()
# then try formats: "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y"
```

## What's NOT in a Discovery Snapshot (yet)

By design, the entry/mid tiers ship **no contact data** (no phone, no email). Reasons:
- Zero skip-trace cost → 100% margin
- Zero DNC scrub liability → compliant by default
- Buyer either uses PropStream Pro's included skip credits or buys contact upsell at $20-40

When you add a premium tier later that includes phone/email, also add:
1. Skip-trace provider call (BatchData recommended)
2. DNC scrub (FTC SAN free for ≤5 area codes, or PossibleNOW)
3. State-DNC handling for states beyond federal (FL, TX, TN, MS, WY, etc.)

## Known blockers — promote to Chrome MCP when needed

- **Harris TX HCAD** — pdata zips return 56 KB HTML redirect; the actual download link is rendered by JS on `https://hcad.org/hcad-online-services/pdata/`. Drive Chrome there, click the zip link, capture the resulting Set-Cookie + actual URL.
- **Cobb GA** — delinquent PDFs hosted at `cms9files.revize.com/cobbcounty/Property/Delinquent/` with rotating dated filenames. The cobbtax.gov page lists current PDF via JS. Chrome MCP to inspect the live href.
- **Jefferson AL** — `eringcapture.jccal.org` is a React SPA. Chrome MCP to drive the search form and extract the resulting list.

If you crack any of these, **update this file**.

## File / script naming conventions

- Pull scripts: `/opt/leadcurate/scripts/pull_round{N}.sh` (each session increments)
- Processors: `/opt/leadcurate/scripts/process_{market}.py`
- Raw data: `/opt/leadcurate/raw_imports/{market-stateabbr}/{YYYY-MM-DD}/{descriptive-name}.{ext}`
- Processed: `/opt/leadcurate/processed/{market-stateabbr}/{YYYY-MM-DD}/{market}-{lane}-{date}.csv`

Market identifiers use lowercase county + state abbreviation, dash-separated: `mecklenburg-nc`, `tarrant-tx`, `nyc` (special-case for NYC).

## When asked to pull data for a new county

1. Check this catalog first — if it's listed, run the documented URL.
2. If not listed, probe Tier 1 hostnames in order. Try 4-6 patterns.
3. If Tier 1 fails, search for `{county} {state} tax delinquent property list download` and inspect landing pages.
4. If nothing works after ~30 min of probing, ask the operator before escalating to Chrome MCP (it requires extension setup).
5. **After success, append the working URL pattern to this file, commit, and push.**
