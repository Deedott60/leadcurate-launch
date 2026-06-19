# 09 — Data Pipeline Status & Codex Handoff

> Written 2026-06-19 by the Claude session that built the data layer.
> This is meant for the next agent — Claude *or* Codex — picking up the data work.

## What exists right now

**A Hostinger VPS at `srv1564456` / `76.13.25.117` (Ubuntu 24.04, 2 vCPU / 7.8 GB RAM / 96 GB disk).**
Docker 29 + Compose v5 are installed. Nothing else is running yet — no n8n, no nginx app, no Caddy.

Folder layout in use:

```
/opt/leadcurate/
├── raw_imports/              # downloaded source data, one folder per market
│   ├── mecklenburg-nc/2026-06-18/
│   ├── wake-nc/2026-06-18/
│   └── ...
├── processed/                # filtered/scored Discovery Snapshots ready to sell
│   ├── guilford-nc/2026-06-18/{full csv, preview csv, meta json}
│   ├── jefferson-ky/2026-06-18/
│   └── shelby-tn/2026-06-18/
├── scripts/                  # all pull and processing scripts that worked
└── logs/
```

## What's pulled — 20 of 24 target markets, ~2.8 GB total

CSV-form with verified row counts:

| Market | Largest dataset | Rows |
|---|---|---|
| Mecklenburg NC (Charlotte) | parcel-lookup | 632,459 |
| Cuyahoga OH (Cleveland) | tax-parcels | 527,161 |
| Wake NC (Raleigh) | parcels | 436,430 |
| Marion IN (Indianapolis) | hhc-parcel-owner | 407,905 |
| Jefferson KY (Louisville) | parcels | 293,138 |
| NYC (all 5 boroughs) | tax-lien sale list | 264,143 |
| DeKalb GA | tax-parcels-2025 | 246,609 |
| Wake NC (Raleigh) | property | 237,600 |
| Fulton GA (Atlanta) | tax-parcels-2025 | 171,031 |
| Forsyth NC (Winston-Salem) | parcels-hosted | 167,188 |
| Cuyahoga OH | parcel-sales-2021-present | 130,093 |
| Mecklenburg NC | lien-data | 24,417 |
| Mecklenburg NC | vacant-land | 23,204 |
| Jefferson KY | property-maintenance-violations | 17,756 |
| Guilford NC (Greensboro) | tax-delinquent-report | 10,532 |
| Jefferson KY | property-foreclosures (premium) | 3,001 |
| Guilford NC | parcel-foreclosure (w/ auction dates) | 2,968 |
| Shelby TN (Memphis) | tax-sale-extract | 2,192 |
| Jefferson KY | lien-holder-final-orders | 516 |

Binary archives:
- **Tarrant TX (Fort Worth)** — weekly tax roll zip 306 MB → 5.7 GB uncompressed (Master.dat + Rec.DAT, fixed-width files, FULL DFW county)
- **Dallas TX** — 2025 REAL_PROPERTY_CERT_APPR_ROLL.zip 118 MB → 2.4 GB DAT file + 100 MB PARCEL2025.zip
- **Maricopa AZ (Phoenix)** — secured/residential/commercial/apartment master text files, ~1.4 GB uncompressed total

PDF / Excel form (need parsing or OCR):
- Erie NY (Buffalo) — 13 MB of filed in-rem foreclosure PDFs incl. 5 MB delinquent taxpayer list
- Charleston SC — 6 tax-sale listing PDFs (1.7 MB)
- Greenville SC — tax sale info PDF + 3.6 MB HTML app
- Allen IN (Fort Wayne) — 662 KB Excel (file extension was `.pdf` from the server but content is `.xlsx`)

Catalog-only (datasets identified, not downloaded):
- Fayette KY (Lexington) — 4 property datasets in `data.lexingtonky.gov` DCAT

## What's NOT pulled — 3 markets currently blocked

These need browser automation (Chrome MCP if Claude, Playwright/Selenium if Codex):

1. **Harris TX (Houston)** — HCAD bulk zips return HTML redirect (56 KB) instead of the actual zip. The pdata page rendering is JS-driven. Codebook is at `https://hcad.org/assets/uploads/pdf/pdataCodebook.pdf` and lists the expected files: `Real_acct_owner.zip`, `Real_acct_history.zip`, `Real_building_land.zip`, `Real_jur_exempt.zip`, `Real_pp_files.zip`, `Real_subdivision.zip`, `Real_neighborhood_code.zip`.
2. **Cobb GA** — monthly delinquent PDFs hosted at `cms9files.revize.com/cobbcounty/Property/Delinquent/` with rotating dated filenames the JS page picks at runtime.
3. **Jefferson AL (Birmingham)** — `eringcapture.jccal.org` is a React SPA. Direct HTTP returns ~830 bytes of shell HTML. Search forms must be driven by a browser.

If Codex picks these up: each needs to visit the page, wait for JS to load, then either capture the rendered download href or submit the search form and scrape the result table.

## URL catalog — what's confirmed to work

(Full catalog is also kept in the Claude session's skill at `~/.claude/skills/leadcurate-county-data-pull/SKILL.md` and gets updated as new patterns are discovered.)

### Direct CSV / XLSX / ZIP

- Wake NC daily delinquent: `https://services.wake.gov/collection_extracts/Real_Estate_Delq853_{MMDDYYYY}.xlsx` — refreshed daily, fall back to yesterday's date if today 404s.
- Wake NC weekly full tax bill: `https://services.wake.gov/collection_extracts/Real_Estate_Full853_{MMDDYYYY}.zip`
- Tarrant TX weekly tax roll: `https://www.tarrantcountytx.gov/content/dam/main/tax/tax-rolls/2026/TaxRoll{YYYYMMDD}.zip` — produced Fridays, available Mondays.
- Dallas DCAD bulk roll: `https://www.dallascad.org/ViewPDFs.aspx?type=3&id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CDATA%20PRODUCTS%5C{YYYY}_REAL_PROPERTY_CERT_APPR_ROLL.zip`
- Shelby TN tax sale (scarcity asset — most competitors don't know this URL): `https://scgpublic.s3.amazonaws.com/TaxSaleExtract.csv`
- NYC tax lien (all 5 boroughs): `https://data.cityofnewyork.us/api/views/9rz4-mjek/rows.csv?accessType=DOWNLOAD`

### ArcGIS Open Data Hubs (CSV via standard API)

Pattern: `https://{HUB}/api/download/v1/items/{ITEM_ID}/csv?layers={N}`

- Mecklenburg/Charlotte: `data.charlottenc.gov`
- Wake: `data.wakegov.com`
- Guilford: `open-data-hub-guilfordgis.hub.arcgis.com`
- Forsyth: `www.mapforsyth.org`
- Marion IN: `data.indy.gov`
- Jefferson KY: `data.louisvilleky.gov`
- Cuyahoga: `data-cuyahoga.opendata.arcgis.com`
- Fulton GA: `gisdata.fultoncountyga.gov`
- DeKalb GA: `dcgis-dekalbgis.hub.arcgis.com`
- Maricopa AZ: `data-maricopa.opendata.arcgis.com` (parcels)
- Fayette KY: `data.lexingtonky.gov`

DCAT catalog at each hub: `https://{HUB}/api/feed/dcat-us/1.1.json` — lists every dataset with download URL.

**Quirk:** First request to a CSV may return HTTP 202 with a "still generating" JSON message. Wait 30–60 s and retry.

### ArcGIS Online direct item downloads (binary zip)

Pattern: `https://www.arcgis.com/sharing/rest/content/items/{ITEM_ID}/data`

Used for the Maricopa AZ master files (Secured/Residential/Commercial/Apartment).

## Processing pipeline (built and proven)

Three Python processors live in `/opt/leadcurate/scripts/`:

- `process_guilford.py` — tax-delinquent absentee lane
- `process_jefferson_ky_v2.py` — pre-foreclosure lane (v2 because v1 had a date-parser bug; see lesson below)
- `process_shelby_tn.py` — tax-sale entry-tier lane

Each follows the same pattern:

1. Load source CSV with `csv.DictReader`, `utf-8-sig` encoding (strips BOM)
2. Apply lane filter
3. Score on urgency + amount + freshness
4. Sort desc, take top N
5. Write three artifacts: full snapshot CSV, 25-row redacted preview CSV (owner names blurred to `J*** S****`), JSON metadata

Output goes to `/opt/leadcurate/processed/{market}/{date}/`.

## Lessons learned (so Codex doesn't repeat them)

### PowerShell ↔ SSH ↔ bash quoting

PowerShell mangles inline bash if you have:
- parentheses in strings (especially User-Agent like `"Mozilla/5.0 (X11; ...)"`)
- ampersands in URLs (`...?q=foo&limit=6`)
- square brackets in regex (`grep -oE 'href="[^"]+"'`)
- `$VAR` substitution (need backtick escape: `` `$VAR ``)
- heredocs (`@'...'@` mangles silently)

**The pattern that always works**: Write the bash/python script as a local file → `scp` to VPS → `ssh` runs `bash /path/to/script.sh`. Avoid inline `ssh leadcurate-vps "complex bash"`.

If Codex uses Python or Node for orchestration, this is moot — but the lesson is: use file-based scripts, not inline.

### Date parsing

Several county datasets ship dates with time + timezone: `2024/07/12 04:00:00+00`. A naive parser fails silently and you get score=0 for every row. Strip the TZ first:

```python
import re
s = re.sub(r"[+-]\d{2}:?\d{0,2}$", "", s).strip()
```

Then try multiple formats:
`"%Y/%m/%d %H:%M:%S"`, `"%Y-%m-%d %H:%M:%S"`, `"%Y/%m/%d"`, `"%Y-%m-%d"`, `"%m/%d/%Y"`

### Empty fields in active records

Louisville's Property Foreclosures CSV has `Sale_Price` populated only AFTER the sale completes. For active court cases (the ones we want), it's empty. Score on `days_to_sale` and `days_since_filed` instead of price.

### ArcGIS Hub async generation

The first call to `/api/download/v1/items/{ID}/csv?layers={N}` may return HTTP 202 with:

```json
{"message":"Up to date download file is being generated. Please check back again later.","status":"Pending"}
```

Sleep 30–60 s and retry; the second call gets the actual CSV.

### "PDF" content type ≠ PDF format

Allen County IN's "2025-Delinquent-Property" endpoint advertises as PDF but the actual bytes are an `.xlsx`. Always run `file` against downloaded files before parsing; rename if needed.

## What's next, regardless of which agent picks this up

1. **Build Discovery Snapshots** for the 17 markets we have raw data but no processed product yet. Pattern is in `/opt/leadcurate/scripts/process_*.py`. Each takes ~20 min once the lane is defined.
2. **Schedule recurring pulls** via cron on the VPS — Wake daily, Tarrant weekly, the ArcGIS hubs monthly.
3. **Crack the 3 blockers** (Harris TX, Cobb GA, Jefferson AL) with browser automation.
4. **Wire intake → Stripe → Supabase** so the snapshots can actually convert to revenue.

## Coordination notes

- The Claude session writes its session memory at `~/.claude/projects/.../memory/project_leadcurate.md` (not in this repo). Most "what was decided and why" lives there.
- The processing scripts on the VPS are the source of truth for transforms — not anything in this repo.
- If Codex makes pulls or processes data, **please update this doc with what worked** so the next agent isn't re-deriving. The instruction the user gave Claude was identical: keep the catalog fresh, document blockers as they get cracked.
