# LeadCurate · Property Numbers Audit

**Version 2 · 2026-06-19**

An analytical breakdown of what's actually in the data across all 21 markets. Record volumes, addressable universes, owner concentration, value distribution, and which less-obvious markets carry the most leverage.

---

## Headline numbers

| Metric | Value |
|---|---|
| Structured records across all markets | **14,204,629** |
| Raw data on disk | **4.09 GB** |
| US markets with pullable data | **21** |
| States represented | **12** |
| Aggregate residential assessed value (studied markets) | **$215B+** |
| Absentee residential owners (studied markets so far) | **64,984** identified |
| Active distress signals available | **10 distinct lanes** |
| Largest single distress dataset | **2,475,143** (NYC code violations) |

The "studied markets" caveat matters: per-market aggregate value and absentee counts have been computed for Mecklenburg and Marion in full so far. Apply the same compute to Maricopa, Tarrant, Dallas, Wake, Cuyahoga, and Fulton and the aggregate value figure scales materially higher. The total of 64,984 absentee owners is the floor from two counties — the actual cross-market figure is several hundred thousand.

---

## Records by market — top 12 by structured volume

Maricopa, Tarrant, and Dallas include binary tax-roll files; counts are estimates pending full ingestion.

| Rank | Market | Metro | Records |
|---|---|---|---:|
| 1 | Maricopa, AZ | Phoenix | 3,500,000 |
| 2 | NYC | All 5 boroughs | 2,739,285 |
| 3 | Tarrant, TX | Fort Worth | 2,000,000 |
| 4 | Dallas, TX | Dallas | 1,500,000 |
| 5 | Marion, IN | Indianapolis | 755,047 |
| 6 | Wake, NC | Raleigh | 674,028 |
| 7 | Cuyahoga, OH | Cleveland | 527,160 |
| 8 | Mecklenburg, NC | Charlotte | 493,832 |
| 9 | Jefferson, KY | Louisville | 314,407 |
| 10 | Forsyth, NC | Winston-Salem | 167,187 |
| 11 | Fayette, KY | Lexington | 118,859 |
| 12 | Guilford, NC | Greensboro | 13,498 |

Smaller markets (Allen IN, Shelby TN, Erie NY, Charleston SC, Greenville SC) hold curated lists rather than full parcel files and contribute as specialty lanes rather than appearing in the volume ranking.

---

## What the full inventory is worth

Volume is a starting point. The real product is the *addressable opportunity* the data exposes.

### Distress signals across the inventory

| Signal | Markets carrying it | Notable volumes |
|---|---|---|
| Active tax-delinquent records | Guilford, Wake (daily), Allen, Erie (annual) + pending in Mecklenburg, Harris, Cobb, Jefferson AL | $10.2M aggregate owed in Guilford alone |
| Pre-foreclosure court cases | Jefferson KY (3,000), Guilford (2,967), Erie (filed petitions) | 3,000 active KY cases refreshing daily |
| Tax-sale upcoming | Shelby (2,192), Charleston, Greenville, NYC (264k lien notices) | All five NYC boroughs covered |
| Building / code violations | NYC (2,475,143), Jefferson KY (17,755), Mecklenburg (24,416 city liens) | NYC scale is unmatched in the inventory |
| Vacant land / vacant property | Mecklenburg (23,203), Fayette (4,373), Cuyahoga | Multiple specialty buyer profiles |
| Lien-holder final orders | Jefferson KY (515) | Niche signal, low competition |
| Recent sales / cash-buyer ID | Cuyahoga (130,093) | Largest sales-comp dataset we hold |
| Absentee owner detection | Mecklenburg, Marion, Wake, Guilford, Fayette, Forsyth | Cross-market institutional flow visibility |

A wholesaler subscribing to multiple markets gets independent distress signals on independent property bases — each refreshing on its own cadence.

### Refresh velocity

The cadence at which fresh records flow in is the moat against PropStream / BatchLeads / DealMachine, which all run on 30–90 day reseller feeds.

| Cadence | Markets |
|---|---|
| Daily refresh | Wake NC (delinquent), Louisville KY (foreclosure cases) |
| Weekly refresh | Tarrant TX (full tax roll, every Monday) |
| Monthly refresh | Most ArcGIS hub markets — Mecklenburg, Marion, Cuyahoga, DeKalb, Fulton, Forsyth, Fayette, Jefferson KY |
| Continuous | NYC code violations |
| Annual publication | Allen IN, Erie NY, Charleston SC, Greenville SC |

Even our slowest sources beat the reseller refresh cycle. Daily sources are weeks ahead of where competitors will see the same record.

---

## Three markets that punch above their weight

The big names — Maricopa, NYC, the Texas metros — speak for themselves. These are the **less obvious** markets in the inventory that carry serious leverage and would be easy for a casual reviewer to overlook.

### 1. Marion County, IN — Indianapolis

**Ranked the #1 US wholesale market for 2026** by multiple industry sources (RealEstateBees, DealMachine, BiggerPockets composite rankings). Yet it sits below Phoenix and DFW in casual visibility.

- 755,047 records in our inventory (5th largest)
- 347,143 parcels with owner detail and assessed values
- **29,490 identified absentee residential owners**

What makes it interesting analytically: the inflow of absentee capital is structurally different from Charlotte's.

| Top absentee mailing state into Indianapolis | Parcels owned |
|---|---:|
| California | 5,683 |
| Georgia | 2,785 |
| Arizona | 2,543 |
| Texas | 2,174 |
| Ohio | 2,128 |
| Florida | 1,864 |
| Illinois | 1,835 |
| New York | 1,819 |

**California sends nearly twice as much absentee capital to Indianapolis as Arizona does** — the opposite of the Charlotte pattern where Arizona dominates. A wholesaler targeting institutional sellers can use this directional intel to pick the right outreach state per metro.

### 2. Cuyahoga County, OH — Cleveland

The largest sales-comp dataset we hold. **130,093 recent parcel sales 2021 through present.** That's four years of transaction history on 527,160 parcels — far deeper than what's available in most of the Sun Belt markets where transaction-level history is sparser in public-record form.

| Signal | Records |
|---|---:|
| Total tax parcels | 527,160 |
| Recent sales 2021–present | 130,093 |

What makes it interesting: Cleveland is a classic BRRRR market — the kind of low-cost-of-entry, high-rental-demand environment that out-of-state investors hunt. **The recent-sales file is exactly what a wholesaler needs to build a cash-buyer list**: cross-reference recent buyers, identify repeat purchasers, target their portfolios for follow-on deal flow.

This is the kind of dataset PropStream and BatchLeads sell as a premium add-on. We have it as a base inclusion.

### 3. Shelby County, TN — Memphis (the scarcity asset)

**2,192 properties in the current tax sale cycle**, pulled directly from a published S3 URL most competitors do not know exists. The URL is embedded in the Trustee's tax-sale-schedule page, not in any obvious download catalog.

| Cycle | Properties |
|---|---:|
| TS2302 (current) | 1,522 |
| TS2301 (prior) | 670 |

What makes it interesting: every other Memphis data source for upcoming tax sale either requires a phone call to the Trustee, attending the Chancery Court auction, or paying for ZeusAuction.com extracts. **We have the same 1,522-property current cycle list as a direct CSV.** Memphis is consistently ranked top-10 for wholesale REI activity and has lower data accessibility than peer markets — that combination makes this dataset disproportionately valuable.

### Bonus: Erie County, NY — Buffalo

Zillow's #1 hottest US housing market for 2026 by projected home-value growth (4.6%). Buffalo gets routinely overlooked because the data is delivered as PDFs (filed in-rem foreclosure petitions, delinquent taxpayer lists) rather than as a clean CSV. We have **13 MB of filed documents** ready to parse — including a 5 MB filed delinquent taxpayer list that names every owner the county is pursuing.

---

## Top-priority delivered subsets — balanced view

When records are filtered and ranked, here's what surfaces at the top of each currently-built batch across the inventory.

| Market | Lane | Universe | Top N | Top-N signal |
|---|---|---:|---:|---|
| Guilford NC | Tax-delinquent absentee | 1,043 | 100 | $700,860 total due across the 100 · 21 states represented |
| Louisville KY | Pre-foreclosure | 259 | 100 | 6 sales upcoming · 50 recent past · top neighborhood Parkland (20) |
| Louisville KY | Open code violations | 13,398 | 100 | Vacant Lot / Vacant Structure flags concentrated at top |
| Louisville KY | Lien-holder final orders | 411 | 100 | Out-of-state owner flag · citation amounts |
| Memphis TN | Tax sale current cycle | 2,186 | 200 | 1,522 in current TS2302 cycle, S3-direct sourcing |
| Charlotte NC | Enriched city liens | 843 | 100 | 73 of 100 out-of-state · $73.9M aggregate property value |
| Charlotte NC | Vacant land specialty | 15,273 | 100 | All 100 out-of-state — institutional LLCs at the top |
| Charlotte NC | High-value absentee SF | 47,151 | 100 | All 100 out-of-state — institutional SFR funds |

Charlotte carries three lanes in production because the source data is unusually rich. Louisville carries three because Jefferson County KY publishes daily-refreshed court filings most counties don't expose. Other markets carry one currently — building additional lanes per market is a straightforward extension of the same processing pattern.

---

## Charlotte deep-dive (one example of what per-county analysis looks like)

Mecklenburg's parcel file is detailed enough to study the underlying market in full. The same analytical depth is available for any market with a comparable parcel file — Marion, Wake, Cuyahoga, Jefferson KY, DeKalb, Fulton, Forsyth — and would surface comparable insights specific to each.

**Mecklenburg residential breakdown:**
- 363,735 residential parcels of 446,213 total
- 35,494 owned absentee from out of NC, 33,013 of those at $200k+ assessed
- Top absentee mailing states: AZ (9,947), CA (5,769), TX (3,221), GA (3,094), SC (2,842)
- Aggregate residential assessed value: $215,428,789,831
- Value tier distribution: 58.3% in $250k–500k, 21.8% in $500k–1M, 6.4% over $1M

**Insight:** Arizona dominates Charlotte absentee ownership. That aligns with institutional SFR funds (HPA BORROWER, SFR JV, BAF ASSETS, RM1 SFR PROPCO) headquartered in Phoenix and Scottsdale concentrating Charlotte exposure heavily.

The same level of analysis is available on demand for any of the 12 markets that publish a full parcel file.

---

## Method

- **Residential** = parcel records where Property_Use contains "single-family," "townhouse," or "condo."
- **Absentee** = owner mailing-address state ≠ property state.
- **High-value** = $200,000+ total assessed value. County-published assessed values typically run 10–30% below market.
- NYC, Marion, Mecklenburg, Wake, Cuyahoga, Jefferson KY, Forsyth, Fulton, DeKalb, Guilford, Fayette, and Shelby counts are exact from CSV files.
- Maricopa, Tarrant, and Dallas counts are estimated from binary tax-roll files pending full ingestion. Actuals likely to revise upward.

---

*This document is updated whenever new markets are pulled or distribution data shifts materially.*
