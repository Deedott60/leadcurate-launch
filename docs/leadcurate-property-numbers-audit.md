# LeadCurate · Property Numbers Audit

**Version 1 · 2026-06-19**

An analytical breakdown of what's actually in the data. Record volumes, addressable universes, owner concentration, value distribution, and the high-priority subsets that would surface at the top of a ranked batch.

---

## Headline numbers

| Metric | Value |
|---|---|
| Structured records across all markets | **14,204,629** |
| Raw data on disk | **4.09 GB** |
| US markets with pullable data | **21** |
| States represented | **12** |
| Mecklenburg residential aggregate assessed value | **$215.4 billion** |
| Guilford NC tax-delinquent aggregate owed | **$10.2 million** |
| NYC citywide building code violations | **2,475,143** |
| Charlotte high-value absentee owners ($200k+) | **33,013** addressable today |

---

## Records by market — top 12

Sorted by structured record count. Maricopa and Tarrant include binary tax-roll files; counts are estimates pending full ingestion.

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

Smaller markets (Allen IN, Shelby TN, Erie NY, Charleston SC, Greenville SC) hold curated lists rather than full parcel files and don't appear in the volume ranking — they contribute as specialty lanes.

---

## Mecklenburg County — full distribution

The deepest single-county breakdown we have. The Charlotte parcel file is large enough to study the underlying buyer market in detail.

### Property type breakdown
- **Total parcels:** 446,213
- **Residential parcels** (single-family, townhouse, condo): **363,735**
- Non-residential balance: 82,478 (commercial, multifamily, vacant, mixed-use, exempt)

### Residential value distribution
- Under $100k: 1,591
- $100k–250k: 47,645
- **$250k–500k: 211,875** ← middle market, largest single segment
- $500k–1M: 79,338
- Over $1M: 23,282

Aggregate residential assessed value: **$215,428,789,831**.

### Absentee owners (mailing address out of NC)
- Residential parcels with out-of-state owners: **35,494**
- High-value ($200k+) subset: **33,013** ← this is the addressable target for premium absentee products

### Where Charlotte absentee capital comes from (top 15 mailing states)

| Rank | State | Residential parcels owned absentee |
|---|---|---:|
| 1 | AZ | 9,947 |
| 2 | CA | 5,769 |
| 3 | TX | 3,221 |
| 4 | GA | 3,094 |
| 5 | SC | 2,842 |
| 6 | NY | 2,380 |
| 7 | FL | 1,828 |
| 8 | VA | 930 |
| 9 | NJ | 880 |
| 10 | MD | 430 |
| 11 | DC | 384 |
| 12 | CT | 382 |
| 13 | PA | 376 |
| 14 | NV | 306 |
| 15 | OH | 305 |

Arizona dominates Charlotte absentee ownership — a strong signal that the institutional SFR funds (HPA BORROWER, SFR JV-1, BAF ASSETS, RM1 SFR PROPCO etc.) headquartered in Phoenix and Scottsdale concentrate Charlotte exposure heavily.

### Active distress signals in Mecklenburg
- City liens (open + active): 24,416
- Vacant land parcels: 23,203
- Tax delinquent (pending — needs browser-driven pull): ~41,000 (per county news release)

---

## Marion County, IN (Indianapolis) — absentee concentration

A useful counterpoint to Mecklenburg. Same parcel-file scale.

- Total parcels: 347,143
- Absentee residential owners (mailing address out of IN): **29,490**

### Top mailing states sending capital to Indianapolis

| Rank | State | Absentee parcels |
|---|---|---:|
| 1 | CA | 5,683 |
| 2 | GA | 2,785 |
| 3 | AZ | 2,543 |
| 4 | TX | 2,174 |
| 5 | OH | 2,128 |
| 6 | FL | 1,864 |
| 7 | IL | 1,835 |
| 8 | NY | 1,819 |
| 9 | NV | 1,020 |
| 10 | CO | 568 |

Notable: California sends nearly **twice as much absentee ownership** to Indianapolis as Arizona does — different institutional flows than Charlotte sees.

---

## Guilford County, NC — chronic tax delinquency

Smaller market, but the deepest distress signal we currently have processed for an entire dataset.

- Total tax-delinquent records: **10,531**
- Aggregate amount owed across all delinquent records: **$10,194,687** (ten million dollars in unpaid tax debt across one mid-size NC county)
- Records with out-of-state owners: 1,043

### Tax year distribution — recurring delinquency

| Tax year | Records still delinquent |
|---|---:|
| 2025 | 4,062 |
| 2024 | 1,677 |
| 2023 | 1,024 |
| 2022 | 789 |
| 2021 | 648 |
| 2020 | 531 |
| 2019 | 509 |
| 2018 | 472 |

The records carrying multi-year delinquency (2018–2022 = 2,949 records) represent **chronic distress**, not transient. These are the highest-priority records in the ranked output because the owner has demonstrated multi-year inability to clear the bill.

### Top mailing states for Guilford absentee delinquents
VA 124 · FL 121 · GA 102 · SC 94 · TX 93 · NY 75 · MD 61 · CA 46 · KY 40 · DC 35

---

## Jefferson County, KY (Louisville) — court-stage distress

The court-filing data captures the late-stage distress wave separately from the tax-stage wave.

| Signal | Records |
|---|---:|
| Total parcels (base) | 293,137 |
| Active foreclosure court cases | **3,000** |
| Open code violations | **17,755** |
| Lien-holder final orders (live) | 515 |

A wholesaler subscribing to Jefferson KY sees three independent distress signals on the same property base, each refreshing daily.

---

## NYC — scale at metro level

| Signal | Records |
|---|---:|
| Tax lien sale notices, all 5 boroughs | 264,142 |
| DOB building code violations citywide | **2,475,143** |

### Tax lien notices by borough

| Borough | Code | Notices |
|---|---|---:|
| Queens | 3 | 108,013 |
| Brooklyn | 4 | 71,674 |
| Manhattan | 2 | 39,488 |
| Bronx | 1 | 24,219 |
| Staten Island | 5 | 20,748 |

Queens carries the highest tax-lien notice volume of any NYC borough — useful targeting intel for wholesalers segmenting NYC sub-markets.

---

## Cuyahoga County, OH (Cleveland) — comp data depth

| Signal | Records |
|---|---:|
| Tax parcels (full county) | 527,160 |
| Parcel sales 2021–present | **130,093** |

The recent-sales file is the largest single source we have for cash-buyer identification across our markets. 130k sales over four years in one county is enough for serious comp-driven targeting.

---

## Top-priority delivered subsets

When we filter and rank, here's what surfaces at the top of each currently-built ranked batch:

| Market | Lane | Universe | Top N | Top-N statistic |
|---|---|---:|---:|---|
| Guilford NC | Tax-delinquent absentee | 1,043 | 100 | $700,860 total due across top 100 · 21 states represented in mailing |
| Louisville KY | Pre-foreclosure | 259 | 100 | 6 sales upcoming, 50 recent past, 44 filed-only · top neighborhood Parkland (20) |
| Memphis TN | Tax sale current cycle | 2,186 | 200 | 1,522 in TS2302 (current cycle), 670 in prior cycle |
| Charlotte NC | Enriched city liens | 843 | 100 | **73 of 100 out-of-state owners · $73.9M aggregate property value** |
| Charlotte NC | Vacant land specialty | 15,273 | 100 | All 100 out-of-state owners · institutional LLCs dominate top 10 |
| Charlotte NC | High-value absentee SF | 47,151 | 100 | All 100 out-of-state · institutional SFR funds (HPA, SFR JV, BAF, RM1) at the top |

---

## What's growing fastest

Datasets that refresh on tight cycles add fresh records every pull. Approximate inflow rates:

| Market | Source | Refresh | Approximate new records / month |
|---|---|---|---:|
| Wake NC | Delinquent file | Daily | ~150–400 |
| Louisville KY | Foreclosure court cases | Daily | ~80–200 |
| Tarrant TX | Tax roll | Weekly | ~5,000–15,000 |
| Guilford NC | Tax delinquent | Monthly | ~300–1,000 |
| NYC | Code violations | Continuous | ~10,000–25,000 |

NYC code violations is the highest-velocity stream by an order of magnitude. Wake NC and Louisville KY are the steadiest deal-pipeline daily refreshes.

---

## Three counties still to pull

For data-completeness context. These are not blockers to current products — they're the next priority additions to expand coverage.

- **Harris TX (Houston)** — full county tax roll, ~1.5M records estimated, pending browser-driven extraction
- **Cobb GA (Atlanta NW)** — monthly delinquent tax PDF, pending parser
- **Jefferson AL (Birmingham)** — delinquent parcels file, pending React-app extraction

Closing those three brings the market count from 21 to 24 and adds an estimated 2–3 million additional structured records.

---

## Footnotes on method

- "Residential" parcels filtered by Property_Use containing single-family, townhouse, or condo.
- "Absentee" defined as mailing-address state ≠ property state.
- "High-value" threshold = $200,000 total assessed value (parcel-lookup files use county-published assessed value, not market value — market values typically run 10–30% higher).
- Aggregate values use county-published assessed values. Real market exposure is higher.
- Maricopa, Tarrant, and Dallas record counts are estimated from the binary tax-roll files pending full ingestion. NYC, Marion, Mecklenburg, Wake, Cuyahoga, Jefferson KY, Forsyth, Fulton, DeKalb, Guilford, Fayette, and Shelby counts are exact from structured CSV files.

---

*This document is updated whenever new markets are pulled or distribution data shifts materially.*
