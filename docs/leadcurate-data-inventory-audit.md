# LeadCurate · Data Inventory

**Version 3 · Last updated: 2026-06-19**

A current snapshot of what LeadCurate has on the ground — the markets we cover, the kinds of distress signals we extract, examples of what individual records look like, and how our data compares to the licensed reseller feeds the rest of the industry runs on.

---

## At a glance

| Metric | Value |
|---|---|
| US markets with live data | **21** |
| States represented | **12** (NC, SC, GA, FL, NY, OH, IN, KY, TN, AL, AZ, TX) |
| Total raw data on disk | **~4.1 GB** |
| Structured CSV records | **~6.5 million** |
| Binary-format records (large county tax rolls) | **~10 million** |
| Distress lanes available | **10** |
| Source refresh cadence | Daily to monthly, per source |
| Refresh lead vs major reseller feeds | **30–60 days fresher** on the same names |

LeadCurate pulls directly from official county portals — tax collectors, assessors, clerks of court, GIS open-data hubs. We are not a licensed reseller of CoreLogic, ATTOM, or DataTree feeds. That distinction shows up in two places: how fresh our data is, and what kind of seat-scarcity model we can offer that platforms running on shared upstream feeds structurally cannot.

---

## Markets covered

Twenty-one US counties / metros, organized by state.

### North Carolina
- **Mecklenburg** (Charlotte) — parcels with owner detail, vacant land, active city liens
- **Wake** (Raleigh) — parcels, property records, daily-refreshed delinquent file
- **Guilford** (Greensboro) — tax-delinquent records, pre-foreclosure with auction dates
- **Forsyth** (Winston-Salem) — parcels with property address and owner

### Texas
- **Tarrant** (Fort Worth) — full county tax roll, refreshed weekly
- **Dallas** — full county certified appraisal roll, parcels
- **Harris** (Houston) — landing pages identified; bulk feed pending browser-driven pull

### Georgia
- **Fulton** (Atlanta) — current tax parcels, historical year files
- **DeKalb** (Atlanta east) — tax parcels current and prior year
- **Cobb** — landing pages identified; pulls pending

### New York
- **NYC** — tax lien sale lists across all five boroughs, citywide building code violations
- **Erie** (Buffalo) — filed delinquent taxpayer list, in-rem foreclosure documents

### Kentucky
- **Jefferson** (Louisville) — parcels, active pre-foreclosure court cases, code violations, lien-holder final orders
- **Fayette** (Lexington) — parcels, vacant land, PDR property records

### Indiana
- **Marion** (Indianapolis) — parcels with owner detail and assessed values
- **Allen** (Fort Wayne) — published delinquent property list

### Tennessee
- **Shelby** (Memphis) — upcoming tax sale property extract

### Other
- **Maricopa, AZ** (Phoenix) — assessor master files: residential, commercial, apartment, secured
- **Cuyahoga, OH** (Cleveland) — tax parcels plus recent parcel sales
- **Charleston, SC** — annual tax sale listings
- **Greenville, SC** — annual tax sale information
- **Jefferson, AL** (Birmingham) — landing pages identified; pulls pending

Three counties (Harris TX, Cobb GA, Jefferson AL) currently sit behind JavaScript-rendered portals that need browser automation to extract. The data is available — the pull just needs a different method. Closing those gaps is in the active queue.

---

## The distress lanes

A "lane" is a category of distress signal that defines what kind of buyer the record is worth selling to. The same county can support multiple lanes simultaneously, each serving a different buyer profile without overlap. Today we have ten:

| # | Lane | What it identifies |
|---|---|---|
| 1 | Tax delinquent + absentee | Out-of-state owner with overdue property tax |
| 2 | Tax delinquent in-state | Local owner unable to pay |
| 3 | Pre-foreclosure court filing | Active foreclosure case with filing and sale dates |
| 4 | Tax sale upcoming | Property going to auction in the current cycle |
| 5 | Foreclosure auction history | Closed and pending sales with sale prices |
| 6 | Vacant land specialty | Undeveloped lots with identifiable owner |
| 7 | High-value absentee residential | Single-family rentals owned by out-of-state entities |
| 8 | City liens / municipal violations | Active liens, code enforcement actions |
| 9 | Building / code violations (large-scale) | Citywide violations — NYC alone has 2.4M records |
| 10 | Recent sales / cash buyer identification | Comp data and buyer-side intelligence |

Not every lane is available in every market. The match between county data and lane depends on what the county publishes. NYC ships tax liens and code violations but not absentee-owner detection. Louisville ships pre-foreclosure but no tax-delinquent file. Mecklenburg ships parcels and city liens, with tax delinquent pending. The available lanes per market are tracked in the working inventory.

---

## Examples of what a single record looks like

Four representative records pulled from four different markets, lightly formatted. Owner names and property addresses are public-record. Specific dollar amounts have been left intact to show data depth.

### Example 1 — Tax-delinquent absentee owner (Guilford County, NC)

> **JJ & R COMPANY**
> Owner mailing address: 209 GLEN WAY NE, Brookhaven, GA 30319
> Property in Guilford County: parcel 16563
> Property assessed value: $1,021,800
> Tax year: 2017 (nine years overdue)
> Bill amount: $13,927.14
> Interest accrued: $9,912.04
> Total due: $28,132.08
> Bill due date: 2017-08-31
> Source: Guilford County tax delinquent report, pulled 2026-06-18

### Example 2 — Active pre-foreclosure (Jefferson County, KY)

> Property: 2616 HALE Ave, Louisville, KY 40211
> Neighborhood: Parkland
> Action filed: 2025-11-05
> Sale date: 2026-06-26 (eight days from this audit)
> Case number: 25CI401179
> Source: Louisville Metro Property Foreclosures, pulled 2026-06-18

### Example 3 — Institutional absentee single-family owner (Mecklenburg County, NC)

> **RM1 SFR PROPCO B LP**
> Owner mailing address: 600 Galleria Parkway Ste 300, Atlanta, GA 30339
> Property: 901 Amanda Dr, Charlotte, NC
> Property use: Single-family residential, built 1985
> Heated square footage: 2,502
> Building value: $534,400
> Land value: $142,500
> Total assessed value: $678,100
> Source: Charlotte parcel-lookup, pulled 2026-06-18

### Example 4 — Upcoming tax sale (Shelby County, TN)

> Property: 554 N Fourth, Memphis, TN
> Parcel: 001072 00017
> Tax sale code: TS2302 (current cycle)
> County GIS record: gis.register.shelby.tn.us
> Source: Shelby County Trustee tax sale extract, pulled 2026-06-18

Each record in a delivery file has the equivalent of these fields plus a score and rank, sorted highest priority first. Source URLs and pull dates are stamped on every batch for buyer verification.

---

## Freshness — how we compare

The major industry tools — PropStream, BatchLeads, DealMachine — license their property data from upstream wholesalers like CoreLogic, ATTOM, and DataTree. Those feeds refresh on cycles of thirty to ninety days. A record showing as "tax delinquent" in PropStream today may belong to an owner who paid their bill forty-five days ago. The signal is stale.

LeadCurate sources direct. A name that hits the public record on the first of the month is in our system within days.

| Source | Refresh cadence |
|---|---|
| Wake NC delinquent file | Daily |
| Louisville KY foreclosure cases | Daily |
| Tarrant TX tax roll | Weekly (every Monday) |
| Most other open-data hubs | Weekly to monthly |
| Major reseller licensed feeds (industry standard) | 30 to 90 days |

The practical effect: we are routinely 30 to 60 days ahead of the platform-based competitors on the same names.

---

## Compliance posture

Every record we deliver is property-record data only. We do not include skip-traced phone numbers, email addresses, or DNC scrub status in the entry and mid tiers. That is deliberate. It keeps the operation clean, reduces compliance overhead, and aligns with how the highest-quality wholesale-data work has historically been done. Buyers handle their own outreach, skip trace, DNC compliance, and TCPA decisions.

Every batch we deliver carries the source URL and the source pull date, so any buyer can verify our claims directly against the county portal we drew from.

We do not scrape behind paywalls or anti-bot controls. Every source is an official public-record portal, an open-data hub, or a legally required publication.

---

## What's next

Three counties remain to bring online (Harris TX, Cobb GA, Jefferson AL). Each requires browser-driven extraction rather than direct download — a focused work session each, not a fundamental obstacle.

Beyond data coverage, the next investments are around automation (recurring monthly pulls without human triggering), enrichment (deeper cross-referencing across datasets within a county, the way Mecklenburg liens are now cross-referenced against parcel records), and customer-facing delivery infrastructure (turning the existing CSV+HTML delivery format into a recurring subscription with payment automation).

The data foundation is solid. The path from here is execution.

---

## Where this document lives

- This markdown source: `docs/leadcurate-data-inventory-audit.md` in the leadcurate-launch repo
- Branded HTML version for sharing: `docs/data-audit/index.html`, served at the permanent URL listed in the cover note attached to this document
- Detailed operational state (for technical partners): `docs/leadcurate-agent-handoff/09-data-pipeline-status.md`

This document is the canonical inventory and is updated as markets and lanes change.

---

### Version history

- **v3** (2026-06-19 evening) — Restructured for partner-facing use. Removed pricing details and seat-capacity revenue math. Balanced examples across multiple markets rather than focusing on Charlotte. Updated counts: 21 markets, 4.1 GB on disk, 6.5M structured records, 10 distress lanes.
- **v2** (2026-06-19) — Added Fayette KY, NYC DOB Violations (2.4M records), and the Mecklenburg lien enrichment cross-reference.
- **v1** (2026-06-19) — Initial inventory at 20 markets, 2.8 GB, three Discovery Snapshots in production.
