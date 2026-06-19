# LeadCurate · Sample Customer Deliveries

This folder contains **redacted, partner-pitch-safe samples** of what a paying County Seat customer actually receives each month. These are NOT the live customer-deliverable files — those stay on the LeadCurate VPS and ship only to paying buyers. What's here is enough to show a potential partner the structure, freshness, lane segmentation, and quality without exposing live owner names from the full lists.

## Two sample packages

### `louisville-ky/` — 3-lane Louisville (Jefferson County, KY) seat package

- `README.txt` — branded cover sheet the customer opens first
- `manifest.json` — machine-readable index
- `combined-top25.csv` — the strongest 25 records across all 3 lanes in one consolidated view (for triage)
- `lanes/pre-foreclosure/` — 100 active foreclosure court cases with action filed date, sale date, days-to-sale countdown (25-row redacted preview included here)
- `lanes/code-violations/` — 100 open building/property maintenance violations including vacant lots and vacant structures
- `lanes/lien-holder-orders/` — 100 final lien orders with citation amounts, hearing dates, out-of-state owner flags

### `charlotte-nc/` — 3-lane Charlotte (Mecklenburg County, NC) seat package

- `README.txt` — same branded cover sheet
- `manifest.json` — machine-readable index
- `combined-top25.csv` — best 25 across all 3 lanes
- `lanes/open-city-liens/` — 100 active city liens including institutional REI fund-owned properties
- `lanes/vacant-land-specialty/` — 100 vacant lots, **100% out-of-state owners**, sorted by acreage × value
- `lanes/high-value-absentee/` — 100 high-value single-family homes owned by out-of-state entities (BAF, SFR JV funds etc.)

## What you're seeing here vs. what the customer gets

| File type | Shown here? | What's different |
|---|---|---|
| `README.txt` | ✓ Identical | Exact cover sheet the customer opens |
| `manifest.json` | ✓ Identical | Same delivery summary |
| `combined-top25.csv` | ✓ Identical | Same triage list |
| `*-preview.csv` | ✓ Included | 25-row redacted version — names blurred to `J*** S****` style |
| `*-meta.json` | ✓ Identical | Same source-URL + provenance + stats |
| **Full lane `.csv`** | **✗ Not shown** | The customer-delivery file with 100 unblurred owner names + addresses lives only on the LeadCurate VPS at `/opt/leadcurate/packages/{pkg-id}/lanes/{lane}/` |

## Refreshness

Both packages were generated on **2026-06-19** from data pulled directly from official county portals on **2026-06-18 / 2026-06-19**. Source URLs are in each lane's `meta.json`. Compare to PropStream / BatchLeads which run on 30–90 day refresh cycles through ATTOM/CoreLogic intermediaries.

## How LeadCurate ships this

The live customer flow:
1. Customer pays for a County Seat (monthly subscription via Stripe)
2. On the delivery date, the LeadCurate VPS auto-builds the package folder (`build_customer_packages.py`)
3. Folder is zipped and emailed to the customer (or signed-URL link)
4. Customer opens the zip → reads `README.txt` first → triages from `combined-top25.csv` → works each lane's full CSV in rank order
5. Excluded/worked records are flagged in the LeadCurate DB so they don't return in next month's batch

## Pricing (for context)

These are samples of the **County Seat tier**: $497/month. Includes 3 lanes per county, 100 records per lane, monthly refresh. Operator Seat ($1,197) gets biweekly delivery or 2 counties. Exclusive Territory ($1,997+) blocks competing seats in the county.

---

*LeadCurate — better data, no hype, your execution closes the deal.*
