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

Update this whenever you discover, refresh, or fix a county URL. **Backfill status 2026-07-08:** York SC, Cabarrus NC, Lancaster SC, Gaston NC, Duval FL, Davidson TN, Tarrant TX, Maricopa AZ, Jefferson KY code-violations, Shelby TN, and Hamilton TN are now documented below. Keep adding new counties here as they are solved.

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
- **Cabarrus NC (Concord/Kannapolis) -- Tier 1 ArcGIS REST**:
  - Layer URL: `https://location.cabarruscounty.us/arcgisservices/rest/services/OpenData/Tax_Parcels/MapServer/1`
  - Public hub: `https://gis-cabarrus.opendata.arcgis.com/`
  - Working method: `scripts/leadcurate/arcgis_property_pull.py --market cabarrus-nc --limit 8000`
  - Query filter used: `AcctName1 is not null and AcctNumber is not null`
  - Key fields: `PIN14`, `AcctName1`, `AcctName2`, `MailAddr1`, `MailCity`, `MailState`, `MailZipCode`, `MarketValue`, `BuildingValue`, `LandValue`, `CALCULATED_ACREAGE`.
- **Gaston NC (Gastonia) -- Tier 1 ArcGIS REST**:
  - Layer URL: `https://gis.gastoncountync.gov/publicgis/rest/services/PublicGIS/Parcels/MapServer/11`
  - Layer index page: `https://gis.gastoncountync.gov/publicgis/rest/services/PublicGIS/Parcels/MapServer/layers`
  - Working method: `scripts/leadcurate/arcgis_property_pull.py --market gaston-nc --limit 8000`
  - Query filter used: `JAN1_NAME1 is not null and AKPAR is not null`
  - Key fields: `AKPAR`, `JAN1_NAME1`, `JAN1_NAME2`, `WHOLE_ADDRESS`, `CURR_ADDR1`, `CURR_CITY`, `CURR_STATE`, `CURR_ZIPCODE`, `FMV_TOTAL`, `FMV_IMPRV`, `FMV_LAND`, `CALCAC`.

### SC

- **York SC (Rock Hill/Fort Mill/Tega Cay) -- Tier 1 ArcGIS REST**:
  - Layer URL: `https://services1.arcgis.com/2AGLxyiJoNiVHKwq/arcgis/rest/services/Parcels/FeatureServer/0`
  - County GIS download page: `https://www.yorkcountysc.gov/239/GIS-Data-Download`
  - Working method: `scripts/leadcurate/arcgis_property_pull.py --market york-sc --limit 8000`
  - Key fields: `ParcelID`, `Owner1`, `Owner2`, `PropertyAddress`, `MailAddr1`, `MailCity`, `MailState`, `MailZip`, `AprTotVal`, `AprBldgVal`, `AprLandVal`, `deededacres`.
- **Lancaster SC (Indian Land/Lancaster) -- Tier 1 ArcGIS REST**:
  - Layer URL: `https://services3.arcgis.com/rJcpRneDUBgTeCT3/arcgis/rest/services/SDE_County_Parcels_Patriot_View/FeatureServer/0`
  - Public hub page: `https://lancaster-launch-lancogis.hub.arcgis.com/pages/2f49a6ade70a4197bcdaeb3202cedbf7`
  - Working method: `scripts/leadcurate/arcgis_property_pull.py --market lancaster-sc --limit 8000`
  - Query filter used: `Owner1 is not null and ParcelID is not null and TotalValue is not null`
  - Key fields: `ParcelID`, `Owner1`, `Owner2`, `StreetNum`, `StreetName`, `BillingAddress`, `City`, `State`, `Zip`, `TotalValue`, `TotalBuildingBalue`, `TotalLandValue`, `TotalAcres`.

### TN

- **Hamilton TN (Chattanooga) -- Tier 3 official county downloads**:
  - Landing page: `https://www.hamiltontn.gov/DownloadRecords.aspx`
  - Assessor CSV zip: `https://www.hamiltontn.gov/_downloadsAssessor/AssessorExportCSV.zip`
  - Assessor building export zip: `https://www.hamiltontn.gov/_downloadsAssessor/AssessorBuildingExport.zip`
  - Layout PDF: `https://www.hamiltontn.gov/_downloadsAssessor/AssessorExtractLayout.pdf`
  - Discovery method used 2026-07-08: searched for `Hamilton County TN property assessor GIS parcels`, opened the official Hamilton County Assessor page, followed the `download the raw data` link to Download Records, then read the page's live hrefs with PowerShell instead of guessing filenames. Verified the page listed the Assessor CSV as last updated `7/4/2026`. Downloaded the CSV zip on VPS into `/opt/leadcurate/raw_imports/hamilton-tn/2026-07-04/` and extracted `AssessorExport.csv`.
  - Processing notes: the CSV has no header row. Column names come from `AssessorExtractLayout.pdf` pages 5-6. Registered in `scripts/leadcurate/process_verified_vacant.py` as `hamilton-tn`. Hamilton `CALC_ACRES` values above 1,000 can be square-foot-like, so the config normalizes those by dividing by 43,560 before scoring.
  - Verified production run 2026-07-08: 168,952 source rows, 21,654 verified-vacant candidates, 2,729 absentee/out-of-state, top 250 exported to `/opt/leadcurate/processed/hamilton-tn/2026-07-08/`.
- **Davidson TN (Nashville) -- Tier 1 ArcGIS REST**:
  - Layer URL: `https://services2.arcgis.com/HdTo6HJqh92wn4D8/arcgis/rest/services/Parcels_view/FeatureServer/0`
  - Public hub page: `https://datanashvillegov-nashville.hub.arcgis.com/datasets/fa26cd9326c446179be059e00449cb1f_0/about`
  - Working method: `scripts/leadcurate/arcgis_property_pull.py --market davidson-tn --limit 8000`
  - Key fields: `STANPAR`, `Owner`, `PropAddr`, `PropCity`, `PropZip`, `OwnAddr1`, `OwnCity`, `OwnState`, `OwnZip`, `TotlAppr`, `ImprAppr`, `LandAppr`, `Acres`.
- **Bradley TN (Cleveland) -- Tier 3 Tennessee Comptroller TPAD**:
  - Source URL: `https://assessment.cot.tn.gov/TPAD`
  - Search endpoint: `POST https://assessment.cot.tn.gov/TPAD/Search/GetSearchResults`
  - Jurisdiction code: `006`
  - Working method: `scripts/leadcurate/pull_tpad_land.py --market bradley-tn --workers 3 --sleep 0.1`, then `scripts/leadcurate/process_verified_vacant.py --market bradley-tn --top 250`.
  - Discovery method used 2026-07-08: opened TPAD search assets, found `Search/GetSearchResults` in `SearchResultsDatatable.js`, verified Bradley jurisdiction `006`, pulled land-heavy property classes 10 Farm, 11 Agricultural, 12 Forest, and 13 Open Space, then fetched each official TPAD parcel detail page for owner mailing, land market value, improvement value, appraisal, deed acreage, buildings, utilities, sale date, and vacant/improved status.
  - Verified production run 2026-07-08: 2,603 TPAD land-class rows pulled with 0 detail errors; 33 verified-vacant candidates after the same six-check processor.
- **Marion TN (Jasper/South Pittsburg/Sequatchie Valley) -- Tier 3 Tennessee Comptroller TPAD**:
  - Source URL: `https://assessment.cot.tn.gov/TPAD`
  - Search endpoint: `POST https://assessment.cot.tn.gov/TPAD/Search/GetSearchResults`
  - Jurisdiction code: `058`
  - Working method: `scripts/leadcurate/pull_tpad_land.py --market marion-tn --workers 3 --sleep 0.1`, then `scripts/leadcurate/process_verified_vacant.py --market marion-tn --top 250`.
  - Discovery method used 2026-07-08: same TPAD endpoint pattern as Bradley, with Marion jurisdiction `058`, property classes 10 Farm, 11 Agricultural, 12 Forest, and 13 Open Space. Detail pages expose owner mailing, land/improvement/appraisal values, deed acreage, building count, utilities, sale date, and vacant/improved status.
  - Verified production run 2026-07-08: 2,306 TPAD land-class rows pulled with 0 detail errors; 238 verified-vacant candidates after the same six-check processor.

### TX

- **Tarrant TX (Fort Worth) — Tier 3 weekly zip**: `https://www.tarrantcountytx.gov/content/dam/main/tax/tax-rolls/2026/TaxRoll{YYYYMMDD}.zip` — created weekly on Fridays, available the following Monday. Contains `Master.dat` + `Rec.DAT` fixed-width files. Working method: save as `/opt/leadcurate/raw_imports/tarrant-tx/<date>/tax-roll.zip`, then run `scripts/leadcurate/extract_tarrant_tx.py --zip <zip> --output-dir /opt/leadcurate/raw_imports/tarrant-tx/<date> --limit 10000`. Extractor joins account IDs from `Rec.DAT` receivables to owner/address rows in `Master.dat` and writes `tax-roll-extracted.csv`.
- **Dallas TX — Tier 3 DCAD ViewPDFs.aspx**:
  - Official source page: `https://dallascad.org/DataProducts.aspx`
  - Freshest enriched appraisal file: `https://www.dallascad.org/ViewPDFs.aspx?id=%5C%5CDCAD.ORG%5CWEB%5CWEBDATA%5CWEBFORMS%5CDATA+PRODUCTS%5CDCAD2026_CURRENT.ZIP&type=3`
  - Discovery method: open the official DCAD Data Products page and follow the first link under **Current and Prior Appraisal data for all accounts**. On 2026-07-15 that link was `2026 Data Files with Proposed Values`; the DCAD home page reported `Appraisal Data Updated: 7/14/2026`. Do not reuse a prior-year filename when this current-year link exists.
  - Working method: download as `/opt/leadcurate/raw_imports/dallas-tx/<date>/DCAD2026_CURRENT.ZIP`, run `scripts/leadcurate/extract_dallas_tx.py` to join the account, owner, address, appraisal, land, residential, commercial, multi-owner, exemption, and transfer tables into one row per account, then run `scripts/leadcurate/process_investor_lanes.py --market dallas-tx`. The processor auto-discovers the newest dated canonical file unless `--source` is supplied.
  - 2026 schema note: `APPLIED_STD_EXEMPT.CSV` no longer contains `CIRCUIT_BK_FLG`. The extractor treats that field as optional and preserves the rest of the exemption data instead of failing or fabricating a value.
  - Verified fresh run 2026-07-16 UTC: 760,654 real-property accounts, 760,654 unique canonical parcels, 140 official source columns, zero duplicate parcels. Supported lane counts are 39,123 tired landlords, 24,308 office/industrial/multifamily, 32,382 out-of-state owners, and 36,386 verified-vacant parcels. All four full files have zero duplicate parcel IDs and file-matched metadata.
  - Current pre-foreclosure source: `https://www.dallascounty.org/government/county-clerk/recording/foreclosures.php`. The County Clerk posts current substitute-trustee foreclosure notices and directs notices filed on or after February 24, 2026 to `https://dallas.tx.publicsearch.us/`, searchable under Foreclosure by sale date or city.
  - Current tax-foreclosure source: `https://www.dallascounty.org/departments/tax/sheriff-sales.php`, with the county tax-foreclosure resale page at `https://www.dallascounty.org/departments/pubworks/property-division.php`. These sources publish current sheriff tax-sale and struck-off property paths. They are separate from DCAD and must be pulled close to delivery; do not substitute assessed value for actual delinquency or claim a count before the current notices are parsed and matched.
- **Harris TX (Houston) — BLOCKED**: HCAD bulk zips at `http://pdata.hcad.org/data/cama/2026/Real_acct_owner.zip` return HTTP 200 with HTML redirect page (56 KB) instead of actual zip. The pdata page is JS-rendered. **Chrome MCP escalation required.** Codebook: `https://hcad.org/assets/uploads/pdf/pdataCodebook.pdf` lists the expected filenames.

### GA

- **Fulton GA (Atlanta) — Tier 1 ArcGIS** at `gisdata.fultoncountyga.gov`. 26 relevant property/tax datasets. Notable:
  - Tax Parcels 2025: `https://gisdata.fultoncountyga.gov/api/download/v1/items/ee82525ee33b49778055622c3a3cf534/csv?layers=0` (171k rows)
- **DeKalb GA — Tier 1 ArcGIS** at `dcgis-dekalbgis.hub.arcgis.com` (alias: `dekalbinsights-dekalbgis.opendata.arcgis.com`):
  - Tax Parcels 2025: `https://dcgis-dekalbgis.hub.arcgis.com/api/download/v1/items/7aa40e4967744cb0abadd6cb0dc23c97/csv?layers=0` (246k rows)
  - Tax Parcels 2024: `https://dcgis-dekalbgis.hub.arcgis.com/api/download/v1/items/5966b70b6f344154a803caa18aa4d98d/csv?layers=1` (246k rows)
- **Cobb GA — BLOCKED**: monthly delinquent PDFs at `cms9files.revize.com/cobbcounty/Property/Delinquent/...` — URL pattern changed since cached examples. Page at `https://www.cobbtax.gov/property/delinquent_taxes/index.php` lists current paths but loads via JS. **Chrome MCP escalation.**
- **Walker GA (LaFayette/Chickamauga) -- PARTIAL / BLOCKED for verified-vacant comparison**:
  - Official assessor landing page: `https://www.qpublic.net/ga/walker/`
  - Official record search link from that page: `https://qpublic.schneidercorp.com/Application.aspx?App=WalkerCountyGA&Layer=Parcels&PageType=Search`
  - Blocker confirmed 2026-07-08: the Schneider qPublic app returns Cloudflare block pages to direct HTTP from the VPS. Local Playwright could not be used because local browser network was denied in the Node REPL environment.
  - Partial alternate source found: `https://services.arcgis.com/UnTXoPXBYERF0OH6/arcgis/rest/services/Walker_Parcels_2026LLLT/FeatureServer/4` has 7,811 parcel features with `Parcel_No`, `ownerName`, `parcelAddress`, `ownerAddress`, `totalacres`, and `qPub_Link`.
  - Why it is not enough: the reachable ArcGIS layer does not expose land value, building/improvement value, total appraisal, building count, or vacant/improved status. Do not run it through `process_verified_vacant.py` by fabricating values. Exact same-pipeline verified-vacant output needs qPublic browser access, a bulk assessor export, or a public-records request.

### FL

- **Duval FL (Jacksonville) -- Tier 1 ArcGIS REST via regional parcel layer**:
  - Layer URL: `https://maps.clayutility.org/server/rest/services/ParcelsHybridv2_LGIM/MapServer/14`
  - Working method: `scripts/leadcurate/arcgis_property_pull.py --market duval-fl --limit 8000`
  - Notes: this source is the ArcGIS parcel layer registered in `scrape_dispatcher.py` for Jacksonville/Duval individual-homeowner pulls. It exposes parcel ID, owner, location address parts, city, ZIP, and acreage.
  - Key fields: `RE`, `LNAME`, `LOC_ST_NO`, `LOC_ST_DIR`, `LOC_ST_NAM`, `LOC_ST_TYP`, `LOC_ST_UNI`, `LOC_CITY`, `LOC_ZIP`, `ACRES`.

### MI

- **Wayne County MI with Detroit breakout -- Tier 1 official county bulk plus City of Detroit ArcGIS**:
  - Wayne County annual assessment page: `https://www.waynecountymi.gov/Government/Departments/Management-Budget/Assessment-Equalization/Annual-Assessment-Data`
  - 2026 county package: `https://www.waynecountymi.gov/files/assets/mainsite/v/1/management-amp-budget/documents/2026-wayne-county-assessments-names-addresses-legal.zip`
  - Detroit current parcels: `https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/parcel_file_current/FeatureServer/0`
  - Detroit 2026 tentative assessment: `https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/tentative_assessment_roll_2026/FeatureServer/0`
  - Detroit blight tickets: `https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/blight_tickets/FeatureServer/0`
  - Official 2026 tax-foreclosure page: `https://www.waynecountymi.gov/Government/Elected-Officials/Treasurer/Property-Tax-Information/Forfeited-Property-List-with-Interested-Parties`
  - Official 2026 tax-foreclosure PDF: `https://www.waynecountymi.gov/files/assets/mainsite/v/1/treasurer/property-amp-taxes/documents/2026_wayne_county_delinquent_tax_liens.pdf`
  - Sheriff mortgage-sale context: `https://www.sheriffconnect.com/court-services/`
  - Discovery method used 2026-07-16: inspected the official county annual-data page and package URL, then used Playwright because Wayne's Akamai layer blocks direct scripted downloads. The archive's `VALUES.TXT`, `NAMES.TXT`, and `LEGALS.TXT` use the published BS&A fixed-width export layout at `https://www.bsasoftware.com/Portals/0/Support/Legacy%20Application/Assessing-Equalization/exp_gen.pdf`. Detroit's official ArcGIS services were inspected for current row counts, field definitions, edit timestamps, and paginated query support. The official tax page exposed the 2026 publication PDF, which was parsed with Ghostscript and matched to current parcel keys.
  - Working method: run `scripts/leadcurate/pull_wayne_mi.py` for the Akamai-protected assessment ZIP and tax PDF; run `build_wayne_mi_canonical.py` to stream and join the fixed-width package; run `pull_detroit_open_data.py` for current Detroit parcels, the 2026 assessment, and filtered blight tickets; run `build_wayne_mi_hybrid.py` to replace annual Detroit rows with the fresher city feed; then run `process_investor_lanes.py --market wayne-mi`, `process_wayne_mi_tax_foreclosure.py`, `process_detroit_blight_pressure.py`, and `build_wayne_mi_intelligence.py`.
  - Verified 2026-07-16: the hybrid universe contains 820,726 unique parcels, including 377,830 unique Detroit parcels and 442,896 outer-Wayne parcels. The four property lanes contain 43,784 tired landlords, 29,516 office/industrial/multifamily opportunities, 24,912 out-of-state-owner parcels, and 37,940 verified-vacant parcels. The official 2026 tax publication matched 36,327 parcels. Every full lane file has one row per parcel and zero duplicates.
  - Detroit vacant-field rule: `total_square_footage` in the current Detroit parcel service is parcel area, not building floor area. Use `total_floor_area` for the building-area check. Treating lot square footage as a building suppresses valid vacant parcels.
  - Legal-source rule: the tax PDF is a November 2025 publication snapshot for parcels subject to foreclosure in 2026. It warns that paid or resolved parcels can remain, so verify the live Treasurer balance at delivery. The Sheriff says it has no property information before a mortgage sale; do not publish a pre-foreclosure count without a current legal-notice source.
  - Tenure rule: Detroit's current service supports historical sale-date analysis. The outer-Wayne annual bulk file's populated transfer dates are overwhelmingly recent, so it does not support a verified 10-year tired-landlord cut outside Detroit. Mark that scope unavailable instead of inferring tenure.
  - Seventh lane: filter Detroit blight tickets to `amt_balance_due > 0 AND disposition LIKE 'Responsible%' AND parcel_id IS NOT NULL`, aggregate to one parcel, match to the current parcel universe, and exclude public owners. Verified output is 82,746 private-owner parcels with zero duplicates. A blight balance is not a tax balance, equity figure, or proof of seller intent.

### Other states

- **Massachusetts statewide -- Tier 1 official MassGIS ArcGIS REST**:
  - Standardized property-tax parcels: `https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Property_Tax_Parcels/FeatureServer/0`
  - Official municipality/county crosswalk: `https://services1.arcgis.com/hGdibHYSPO59RG1h/arcgis/rest/services/Massachusetts_Municipalities/FeatureServer/1`
  - Discovery method used 2026-07-15: located the MassGIS standardized statewide property-tax parcel product, inspected the live ArcGIS layer metadata to verify its owner, mailing, use-code, value, lot-size, sale, building, and unit fields, then joined `TOWN_ID` to the official 351-municipality layer for county names and FIPS codes.
  - Working method: run `scripts/leadcurate/pull_massgis_statewide.py` using non-overlapping `OBJECTID` ranges, then `scripts/leadcurate/process_investor_lanes.py --market massachusetts-statewide` and `scripts/leadcurate/build_statewide_lane_rollup.py`. The range pull avoids ArcGIS offset rescans and deduplicates on municipality plus parcel identifier.
  - Verified 2026-07-16: fetched all 2,558,878 source rows, retained 2,558,583 unique parcels after collapsing 295 duplicates, and matched all 351 municipalities. Supported lane counts: 367,228 tired landlords; 59,602 office/industrial/multifamily; 115,764 out-of-state owners; 60,876 verified-vacant parcels. Rollups contain 14 counties and 351 municipalities, with every count computed from the canonical file.
  - Current statewide foreclosure and tax-lien filing source: `https://www.mass.gov/lists/land-court-masscourts-reports`. The official Land Court reports list new Servicemember, Tax Lien, and Miscellaneous cases from the latest three-month window and update nightly. Each entry includes case number, filed date, city, street, and party names. Case details are verified through `https://www.masscourts.org/` using the official search instructions at `https://www.mass.gov/info-details/instructions-for-using-the-land-court-public-access-site`.
  - Scope rule: MassGIS does not contain foreclosure or municipal tax-title status. Pull the fresh Land Court reports, then match addresses and municipalities to the statewide property file. For tax debt before a Land Court filing, use the selected municipality's collector or treasurer record. Never represent a statewide assessor value as proof of delinquency.
- **Cook County IL (Chicago) -- Tier 2 official Cook County Socrata**:
  - Current parcel universe: `https://datacatalog.cookcountyil.gov/resource/pabr-t5kh.csv`
  - Current parcel/owner addresses: `https://datacatalog.cookcountyil.gov/resource/3723-97qp.csv`
  - Current assessed values: `https://datacatalog.cookcountyil.gov/resource/uzyt-m557.csv`
  - Current single/multifamily characteristics: `https://datacatalog.cookcountyil.gov/resource/x54s-btds.csv`
  - Parcel sales: `https://datacatalog.cookcountyil.gov/resource/wvhk-k5uv.csv`
  - Latest commercial valuation fields: `https://datacatalog.cookcountyil.gov/resource/csik-bsws.csv`
  - Official 2021 parcel geometry used only for acreage: `https://datacatalog.cookcountyil.gov/resource/77tz-riq7.csv` with SoQL `area(the_geom)`.
  - Discovery method used 2026-07-15: searched the official Cook County Data Catalog, inspected each dataset's API metadata and live maximum tax year, verified 2026 current parcel/address/value/characteristic coverage, and followed the Assessor's official class-code reference linked from the dataset metadata. The pull retains all published fields, aggregates improvement cards, and keeps the latest recorded sale per PIN.
  - Working method: run `scripts/leadcurate/pull_cook_il.py`, which saves compressed raw snapshots and joins them into one row per zero-padded 14-digit PIN, then run `scripts/leadcurate/process_investor_lanes.py --market cook-il`.
  - Verified 2026-07-16: 1,863,530 current parcels, 309 canonical source fields, and zero duplicate PINs. The current-universe guard removed 85,509 historical/enrichment-only PINs before export. Supported lane counts: 84,800 tired landlords; 181,075 office/industrial/multifamily; 61,559 out-of-state owners; 2,918 verified-vacant parcels. All lane meta counts match the full CSVs.
  - Current pre-foreclosure source: `https://app.cookcountyclerkofcourt.org/case-search/`, the official Clerk of the Circuit Court case search. Mortgage foreclosures are filed in the Chancery Division's Mortgage Foreclosure Section. Current cases must be matched back to the property PIN or address; the public Recorder dataset `4f2q-h3b7` ends in March 2015 and must not be sold as current.
  - Current delinquent-tax source: `https://www.cookcountytreasurer.com/annualtaxsale.aspx`. The Treasurer states that the next Annual Tax Sale is anticipated in December 2026 and provides current PIN-level eligibility searches. Full electronic delinquency lists are sold through the county's tax-sale site; source cost requires Derrick's approval and should be included in fulfillment pricing. The old public catalog dataset `55ju-2fs9` is stale and must not be used.

### Supporting market-direction sources

These sources support a buyer's territory-ordering decision. They do not replace parcel, court, or tax evidence and must never be used to label an individual property distressed or likely to appreciate.

- **Dallas NorthEnd / Goldman Sachs campus**:
  - City of Dallas Economic Development: `https://www.dallasecodev.org/m/newsflash/home/detail/1154`
  - Goldman Sachs project release: `https://www.goldmansachs.com/pressroom/press-releases/2023/goldman-sachs-breaks-ground-on-dallas-campus-at-northend`
  - Verified facts used 2026-07-16: minimum $390 million in real-property improvements, $90 million in business-property improvements, 5,000 permanent jobs created or retained, and late-2027 expected construction completion.
  - Discovery method: searched the official City of Dallas economic-development archive, matched the project to the company's official release, and reconciled the investment, employment, location, and completion claims before use.
- **South Chicago Illinois Quantum and Microelectronics Park**:
  - State commitment announcement: `https://dceo.illinois.gov/news/press-release.30472.html`
  - 2025 groundbreaking confirmation: `https://cmap.illinois.gov/news-updates/illinois-quantum-park-groundbreaking-chicagoland/`
  - Current site/status context: `https://epa.illinois.gov/topics/community-relations/sites/iqmp.html`
  - Verified facts used 2026-07-16: minimum $1.09 billion PsiQuantum company investment, at least 154 full-time jobs, separate $500 million Illinois campus commitment, and 2025 groundbreaking.
  - Discovery method: searched State of Illinois economic-development releases, confirmed the project stage through the Chicago Metropolitan Agency for Planning, and checked the Illinois EPA project page for current site context.
- **Massachusetts local job direction**:
  - Official April 2026 local labor report: `https://www.mass.gov/news/unemployment-and-job-estimates-in-local-labor-markets-for-april-2026`
  - Verified facts used 2026-07-16: April 2025 to April 2026 job gains of 4.1% in Barnstable, 0.4% in Worcester, and 0.3% in Springfield.
  - Discovery method: searched current Mass.gov labor and economic-development releases and used the state's own year-over-year local labor-market comparison. This is a labor-direction signal, not a capital-investment claim.

- **Maricopa AZ (Phoenix) — Tier 1 ArcGIS + ArcGIS Online items**: data sales page at `https://www.mcassessor.maricopa.gov/page/data_sales/` links 17 datasets. **Master files come from ArcGIS Online item API** (binary zip):
  - Secured Master: `https://www.arcgis.com/sharing/rest/content/items/936bbba512bf4c368618cc6e79e64668/data` (108 MB → 483 MB, contains BK100-BK500 text files)
  - Residential Master: `https://www.arcgis.com/sharing/rest/content/items/e22983d41d91490d90965544b718a120/data` (58 MB → 364 MB)
  - Commercial Master: `https://www.arcgis.com/sharing/rest/content/items/12ce08cf4d264f9d97bb7ef4d6eb9944/data` (21 MB → 525 MB)
  - Apartment Master: `https://www.arcgis.com/sharing/rest/content/items/0b5770a1b73f4637b8f92f088465890b/data` (343 KB)
  - Working method: save the master zips under `/opt/leadcurate/raw_imports/maricopa-az/<date>/` as `secured-master.zip`, `residential-master.zip`, and optionally `commercial-master.zip`, then run `scripts/leadcurate/extract_maricopa_az.py --raw-dir /opt/leadcurate/raw_imports/maricopa-az/<date> --output-dir /opt/leadcurate/raw_imports/maricopa-az/<date> --limit 10000`. Extractor reads `Data/Residential_Master.txt` and `Data/Secured_Master*` pipe-delimited files and writes `parcels-extracted.csv`.
- **Marion IN (Indianapolis) — Tier 1 ArcGIS** at `data.indy.gov`:
  - Parcels w/ Owner + Assessed Values: `https://data.indy.gov/api/download/v1/items/0d28e222479743baa97f8f4456da7bb4/csv?layers=10` (347k rows)
  - HHC Parcel Owner: `https://data.indy.gov/api/download/v1/items/1dbe42c87bf24d5780bee61907bcbfc2/csv?layers=1` (408k rows)
- **Jefferson KY (Louisville) — Tier 1 ArcGIS** at `data.louisvilleky.gov`:
  - Property Foreclosures (premium): `https://data.louisvilleky.gov/api/download/v1/items/62c648120ab44b7794f8b484884efaa9/csv?layers=0` (3k court cases w/ Action_Filed, Sale_Date, Sale_Price, Purchaser)
  - Parcels: `https://data.louisvilleky.gov/api/download/v1/items/47085b87ac754d60942ea324a3b0f54f/csv?layers=1` (293k)
  - Lien Holder Final Orders: `https://data.louisvilleky.gov/api/download/v1/items/8f25a99a0e2347cc871a203ca325ab5e/csv?layers=0` (516)
  - Property Maintenance Violations: `https://data.louisvilleky.gov/api/download/v1/items/1fd891c3301c4c4581b86c338468fbe4/csv?layers=0` (17.7k)
  - Code-violations enrichment method: store the violations CSV as `/opt/leadcurate/raw_imports/jefferson-ky/<date>/property-maintenance-violations.csv`, then run `scripts/leadcurate/enrich_jefferson_ky_code_violations.py --limit 1000`. The script queries `https://jeffersonpva.ky.gov/property-search/property-listings/?psfldParcelId=<PARCEL_ID>&searchType=ParcelSearch`, parses the PVA detail page for owner and assessed value, and writes `property-maintenance-violations-enriched.csv`.
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
