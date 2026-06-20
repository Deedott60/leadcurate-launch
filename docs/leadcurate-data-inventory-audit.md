# LeadCurate · Data Inventory Audit

**Version 2 · Last updated: 2026-06-19 (evening)**

> A premium county property-data operation built for serious real estate investors. This document is the canonical inventory of LeadCurate's live data assets — markets covered, distress lanes available, seat capacity per county, freshness posture, and example products already in production.

---

## Executive summary

| Metric | Value | Change from v1 |
|---|---|---|
| US markets with live data | **21** of 24 targeted | +1 (Fayette KY added) |
| Total raw data on VPS | **~4.1 GB** | +1.3 GB |
| CSV rows across markets | **~6.5 million** | +2.5M (NYC DOB violations) |
| Binary-format records | **~10 million** | (Tarrant, Dallas, Maricopa unchanged) |
| Distinct distress lanes available | **10** — tax delinquent, absentee, pre-foreclosure, foreclosure auction, vacant property, vacant land, city liens, **code violations (now NYC-wide)**, lien-holder final orders, recent sales / cash buyer ID | +1 (NYC DOB code violations as standalone lane) |
| Finished Discovery Snapshots ready to ship | **6** + **2 customer-delivery packages** | Charlotte + Louisville packages bundled |
| Pull cadence | Daily (Wake NC, Jefferson KY foreclosures), weekly (Tarrant TX), monthly (most ArcGIS hubs) | Same |
| Refresh-vs-PropStream advantage | **30–60 days fresher** on the same names | Same |
| **NEW: Charlotte enriched liens** | 843 enriched · top 100 ranked · **73 out-of-state · $73.9M aggregate property value** | new this round |
| **NEW: NYC DOB code violations** | **2,475,144 records (711 MB)** across all 5 boroughs | new this round |

LeadCurate sources directly from official county portals — not licensed reseller feeds. That gives the business two structural advantages over PropStream / BatchLeads / DealMachine: (a) **freshness** — county data hits LeadCurate within hours of being published, vs. 30–90 days for the licensors; (b) **scarcity by design** — limited seats per county per lane create artificial scarcity competitors cannot offer because their business models require unlimited seats.

---

## Markets covered

20 markets confirmed with live, downloadable property/distress data on the VPS at `/opt/leadcurate/raw_imports/`.

### Tier S — flagship markets with high investor demand + clean automation

| Market | State | Metro | Volume / signal | Source class | Cadence |
|---|---|---|---|---|---|
| **Mecklenburg** | NC | Charlotte | 632k parcels + 24k city liens + 23k vacant land + delinquent slice | Socrata Open Data | Monthly |
| **Wake** | NC | Raleigh | 436k parcels + 237k property + daily-refreshed delinquent | Direct download | **Daily** |
| **Tarrant** | TX | Fort Worth (DFW) | 5.7 GB binary tax roll, full DFW county | Direct weekly zip | **Weekly** |
| **Harris** | TX | Houston | landing pages only — Chrome MCP escalation pending | HCAD bulk zip URLs blocked by JS | TBD |
| **Maricopa** | AZ | Phoenix | 4 master files: residential, commercial, apartment, secured | ArcGIS Online direct items | Monthly |
| **Marion** | IN | Indianapolis (#1 wholesale market 2026) | 347k + 408k parcels w/ owner + assessed values | ArcGIS Hub | Monthly |

### Tier A — strong secondary markets

| Market | State | Metro | Volume / signal | Source class | Cadence |
|---|---|---|---|---|---|
| **Cuyahoga** | OH | Cleveland | 527k tax parcels + 130k recent sales (2021–present) | ArcGIS Hub | Monthly |
| **Jefferson KY** | KY | Louisville | 293k parcels + 3k pre-foreclosure + 18k code violations + 516 lien-holder final orders | ArcGIS Hub | Monthly |
| **Fulton** | GA | Atlanta | 171k tax parcels 2025 + 30k current + 27k base | ArcGIS Hub | Monthly |
| **DeKalb** | GA | Atlanta east | 246k tax parcels 2025 + 246k 2024 | ArcGIS Hub | Monthly |
| **Forsyth** | NC | Winston-Salem | 167k parcels with owner + property address | MapForsyth Hub | Monthly |
| **NYC** | NY | All 5 boroughs | 264k tax lien sale notices | Socrata Open Data | Monthly |
| **Dallas** | TX | Dallas | 2.4 GB binary REAL_PROPERTY_CERT_APPR_ROLL + 100 MB PARCEL2025 | DCAD ViewPDFs.aspx | Annual |
| **Shelby** | TN | Memphis | 2,192 upcoming tax-sale properties — **scarcity asset** (S3 URL most competitors don't know) | Direct S3 CSV | Per sale |
| **Guilford** | NC | Greensboro | 10.5k tax delinquent + 3k pre-foreclosure with auction dates/times/locations | ArcGIS Hub | Monthly |

### Tier B — supplementary / specialty markets

| Market | State | Metro | Notes |
|---|---|---|---|
| **Allen** | IN | Fort Wayne | 662 KB Excel delinquent property list (auditor-published) |
| **Erie** | NY | Buffalo | 5 MB filed delinquent taxpayer list + 8 supporting in-rem foreclosure PDFs |
| **Charleston** | SC | Charleston | 6 tax-sale listing PDFs (RP + MH) |
| **Greenville** | SC | Greenville | Tax-sale info PDF + HTML app |
| **Fayette** | KY | Lexington | DCAT catalog — 4 property datasets identified, downloads queued |

### Markets pending Chrome MCP / browser automation

3 counties currently require browser drive (their data is locked behind JavaScript-rendered SPAs). Tools and target URLs are documented; pulling them is a 30–60 minute task per county once Chrome MCP is wired up:

- **Harris TX** (Houston) — HCAD `pdata` zip URLs return HTML redirect; actual link is JS-rendered
- **Cobb GA** — monthly delinquent PDFs hosted on rotating-filename CDN; current path picked by JS
- **Jefferson AL** (Birmingham) — `eringcapture.jccal.org` is a React SPA, all content client-rendered

---

## Distress lanes available

A "lane" is a category of distress signal that defines who a record is worth selling to. The same county can support **multiple lanes simultaneously**, each lane sold to a different buyer profile without overlap.

| # | Lane | What it identifies | Primary buyer profile | Markets where we have it |
|---|---|---|---|---|
| 1 | **Tax-delinquent + absentee** | Out-of-state owner with overdue property tax | Wholesalers, fix-and-flippers | Guilford NC, Mecklenburg NC, Wake NC, Forsyth NC, Marion IN, Maricopa AZ |
| 2 | **Tax-delinquent in-state** | Local owner who can't pay property tax | Local wholesalers | All NC, TX, GA, OH, IN, NY markets |
| 3 | **Pre-foreclosure court filing** | Active foreclosure case w/ filing date + sale date | Wholesalers, hard money lenders | Jefferson KY (3k cases), Guilford NC (3k w/ auction dates) |
| 4 | **Tax-sale upcoming** | Property going to auction in current sale cycle | Tax-lien investors, cash buyers | Shelby TN, Charleston SC, Erie NY, Allen IN |
| 5 | **Vacant land specialty** | Undeveloped lots w/ identifiable owner | Land developers, buy-and-hold | Mecklenburg NC (23k), Cuyahoga, Fulton GA |
| 6 | **High-value absentee** | Single-family rentals owned by out-of-state entities | Mid-market flippers, REI funds | Mecklenburg NC (47k qualified), Marion IN, Wake NC, all NC/TX/AZ markets |
| 7 | **City liens / code violations** | Active municipal liens on a property | Wholesalers chasing distress | Mecklenburg NC (4k open liens), Jefferson KY (18k violations + 516 lien orders) |
| 8 | **Recent sales / cash buyers** | Comp data + buyer identification | Wholesalers building cash-buyer lists | Cuyahoga OH (130k since 2021) |
| 9 | **Lien-holder final orders** | Municipal lien holders w/ final-order status | Specialty buyers, tax-lien funds | Jefferson KY (516 records) |

---

## Case study — Mecklenburg County NC (3 lanes, 1 county)

Charlotte alone supports at least 3 distinct sellable products from the data we already have on disk. Each goes to a different buyer profile. None overlap.

### Lane A — Open City Liens (`mecklenburg-nc-open-city-liens-2026-06-19.csv`)

- **Source universe:** 24,417 lien records → 4,025 active (not paid) → top 100 ranked
- **Score signal:** lien status weight + invoice recency
- **Top record example:**
  - TREVA WOODS TWNHSE ASSOC at 8002 CHARTER OAK LN, lien filed 2023-06-07
- **Buyer profile:** wholesalers chasing distress, particularly properties with active filed liens
- **Price tier:** mid ($59–79)

### Lane B — Vacant Land Specialty (`mecklenburg-nc-vacant-land-specialty-2026-06-19.csv`)

- **Source universe:** 23,204 vacant parcels → 15,273 qualified (≥0.1 acre, identifiable owner) → top 100
- **Score signal:** acreage × land value × absentee bonus
- **Top 100 are 100% out-of-state owners.** Examples:
  - **ULM II NORTH CAROLINA LLC from Ligonier, PA** owns 9.5 acres in Ballantyne worth **$7.8M**
  - **STEELE CREEK OWNER LLC from Coconut Grove, FL** owns 22.6 acres in Steele Creek
  - **YFP TIMBER LLC from Fort Mill, SC** owns 7 acres on Hamilton Rd, $474k assessed
- **Buyer profile:** land developers, build-to-rent operators, specialty wholesalers
- **Price tier:** premium ($99+) — rare specialty data

### Lane C — High-Value Absentee Single-Family (`mecklenburg-nc-high-value-absentee-2026-06-19.csv`)

- **Source universe:** 446,213 parcels scanned → 47,151 qualified (residential + absentee + $200k+) → top 100
- **Score signal:** property value × out-of-state bonus × older-home rehab bonus
- **Top 100 are 100% out-of-state owners.** Examples:
  - **RM1 SFR PROPCO B LP from Atlanta, GA** owns 901 AMANDA DR Charlotte, $678,100 single-family (1985)
  - **ANNE CARR GILMAN WOOD from Austin, TX** owns 4300 KUYKENDALL RD Charlotte, $602,600 single-family (1956)
  - **JASON WIESELMAN from Mineola, NY** owns 5308 SUNNINGDALE DR Charlotte, $835,700 single-family (1989)
- **Buyer profile:** mid-market flippers, BRRRR investors, institutional dispositions
- **Price tier:** premium ($99+)

**Three products from one county. Three different buyers. Zero overlap. No competitor in the wholesale-data lane offers this lane-by-lane segmentation today.**

---

## Seat capacity — how many customers each county can support

Capacity is set by available distress volume per lane, not by aggregate parcel count. Math: a County Seat = 100–200 scored records/month. We can support 1 seat per ~1,000 qualified records to keep batches fresh and unique each month.

| Market | Lanes | Estimated total seats supportable |
|---|---|---|
| Mecklenburg NC | Liens + Vacant Land + Absentee + Tax-delinquent | **~50 seats** across all lanes |
| Wake NC | Absentee + Tax-delinquent + Foreclosure | ~35 |
| Tarrant TX | Tax-delinquent + Absentee + Probate (when added) | ~80 (largest county we have) |
| Maricopa AZ | Absentee + Vacant + Tax-delinquent | ~60 |
| Marion IN | Tax-delinquent + Absentee | ~40 |
| Jefferson KY | Pre-foreclosure + Code violations + Lien orders + Absentee | ~25 |
| Cuyahoga OH | Tax-delinquent + Sales comps + Absentee | ~40 |
| Fulton + DeKalb GA combined | Absentee + Tax | ~50 |
| NYC (5 boroughs) | Tax-lien specifically | ~30 |
| Forsyth NC | Absentee + Vacant | ~15 |
| Shelby TN | Tax-sale upcoming only | ~10 |
| Guilford NC | Pre-foreclosure + Absentee | ~10 |
| Smaller markets combined | Mix | ~25 |

**Total supportable seats today across markets: ~470.**

At $497/mo per County Seat (entry-tier monthly subscription), the addressable revenue with current data is **~$233,590/mo** at full capacity — without adding any markets. Realistic 12-month ramp targets 5–7 customers ($3k/mo founder survival), then 20 customers ($10k/mo), then 50+ ($25k+/mo).

---

## Freshness posture (vs. competitors)

Where competitors get their data and how often it refreshes:

- **PropStream / BatchLeads / DealMachine** license from **ATTOM / CoreLogic / DataTree**, which refresh feeds on **30–90 day cycles**.
- A "tax delinquent" record in PropStream today could be someone who paid 60 days ago — the underlying feed hasn't refreshed yet. The signal is stale.

LeadCurate refresh by market:

| Market | Refresh source | Cadence |
|---|---|---|
| Wake NC | `services.wake.gov` direct file | **Daily** |
| Tarrant TX | `tarrantcountytx.gov` weekly zip | **Weekly (Monday)** |
| Jefferson KY foreclosures | `data.louisvilleky.gov` ArcGIS | **Daily** |
| Most other ArcGIS hubs | Per-hub schedules | Weekly to monthly |
| Annual publications (Erie NY, Charleston SC) | County-published | Annual |

**Sales line:** *"A tax-delinquent record appears in Guilford County June 15. LeadCurate ships it to the buyer June 16. PropStream shows it August 15. We're 60 days ahead of the same name."*

---

## Compliance posture

Built into every Discovery Snapshot:

1. **No skip-trace contact data in entry/mid tiers** → zero TCPA exposure, 100% margin on data delivery, complies with TCPA without requiring DNC scrub on our side.
2. **Source URL and source pull date** stamped in metadata of every product → buyer can verify our claims.
3. **Compliance note** in every metadata file: *"Property-record data only. Buyer is responsible for owner contact lookup, skip trace, DNC compliance, TCPA, and outreach decisions."*
4. **No CAPTCHA bypass, no anti-bot evasion, no scraping behind paywalls** — every source is an official public-record portal, an open-data hub, or a legally required publication.
5. **Assignment lock** (per business plan) — records assigned to one customer during their billing cycle are held back from other buyers' batches.

---

## Discovery Snapshots in production

Currently shippable as `.csv` (full) + `.csv` (25-row redacted preview for sales) + `.json` (metadata):

| Snapshot | Market | Lane | Rows | Suggested price |
|---|---|---|---|---|
| guilford-nc-absentee-tax-delinquent | Greensboro NC | Tax-delinquent absentee | 100 | $79 one-time |
| jefferson-ky-pre-foreclosure | Louisville KY | Pre-foreclosure court cases | 100 | $99 one-time |
| shelby-tn-tax-sale | Memphis TN | Upcoming tax sale | 200 | $39 one-time (entry tier) |
| mecklenburg-nc-open-city-liens | Charlotte NC | Active city liens | 100 | $69 one-time |
| mecklenburg-nc-vacant-land-specialty | Charlotte NC | Specialty vacant land | 100 | $99 one-time |
| mecklenburg-nc-high-value-absentee | Charlotte NC | Institutional absentee SF | 100 | $99 one-time |

---

## Update procedure

This audit file is the **source of truth** for partner conversations, internal planning, and onboarding new agents/operators. It MUST stay current.

### When to update

- After every new market is pulled (add to Markets Covered)
- After every new lane is added (add to Distress Lanes)
- After every new Discovery Snapshot is built (add to Discovery Snapshots in Production)
- After blockers are cracked (move counties from "pending" to active tier)
- After seat counts change materially

### How to update

1. Pull the latest from VPS: `ssh leadcurate-vps "du -sh /opt/leadcurate/raw_imports/*" `
2. Edit this file: `docs/leadcurate-data-inventory-audit.md`
3. Bump the version number and last-updated date at the top
4. Append a one-line entry to the **Update log** below
5. Commit + push to GitHub
6. The skill at `~/.claude/skills/leadcurate-county-data-pull/SKILL.md` should be updated in the same session

### Update log

- **2026-06-19** — v1 created. 20 markets, 6 Discovery Snapshots in production. Mecklenburg multi-lane showcase added.
- **2026-06-19 (evening)** — **v2**. Fayette KY added (4 datasets pulled). NYC DOB Violations 2.4M records pulled (711 MB). Charlotte city liens cross-referenced with parcel-lookup to enrich with property value, year built, mailing state, absentee flag — 843 enriched, top 100 ranked, 73 out-of-state, $73.9M aggregate property value. Additional parcel datasets pulled for Guilford, Charlotte, Marion IN, Fulton GA. Total VPS grew 2.8 GB → 4.1 GB. Customer-delivery XLSX + HTML packages built for Louisville KY and Charlotte NC.

---

## Where everything lives

- **Raw data**: `/opt/leadcurate/raw_imports/{market}/{YYYY-MM-DD}/` on the Hostinger VPS
- **Processed snapshots**: `/opt/leadcurate/processed/{market}/{YYYY-MM-DD}/`
- **Scripts**: `/opt/leadcurate/scripts/` (pull scripts numbered `pull_round{N}.sh`, processors named `process_{market}.py`)
- **Pipeline status doc (for Codex / other agents)**: `docs/leadcurate-agent-handoff/09-data-pipeline-status.md`
- **Skill (Claude)**: `~/.claude/skills/leadcurate-county-data-pull/SKILL.md`

Anyone — Claude session, Codex run, or human operator — can pick up where the last session left off by reading this audit + the pipeline status doc.

---

*LeadCurate — better data, no hype, your execution closes the deal.*
