---
name: leadcurate-b2b-lanes
description: Build and sell LeadCurate's two B2B data lanes in ANY covered market — Asset Locator (lien/judgment × parcel cross-reference for collection attorneys) and Code Violations (active-violation building lists for restoration contractors). Covers data requirements, the build recipe, sample-page pattern, compliance framing, and market-rate pricing. Trigger when Derrick says "run asset locator for [market]", "build the violations list for [market]", "new B2B market", or names either lane.
metadata:
  type: business-workflow
  version: 2026-07-06
  scope: leadcurate
---

# LeadCurate B2B Lanes — Repeatable Recipe

Two proven lanes, first shipped 2026-07-06. Same engine as the investor product; only the buyer and sales surface change. Live reference samples:
- Asset Locator: `leadcurate.com/sample-deliveries/charlotte-asset-locator-2026-07-06/`
- Code Violations: `leadcurate.com/sample-deliveries/nyc-code-violations-2026-07-06/`

## Lane A — Asset Locator (collection attorneys / judgment recovery)

**What it is:** cross-reference a debtor-side file (liens, judgments, delinquencies) against the county parcel-owner file → "which debtors verifiably own real property, worth what, linked to the deeds record."

**Data required (both must exist for the market):**
1. Debtor-side: filed liens / judgment liens / tax-delinquent list
2. Parcel-side: county parcel file WITH owner names + assessed values

**Markets ready TODAY (verified on VPS 2026-07-06):**
- Mecklenburg NC — DONE (lien-data.csv × parcel-lookup; 843 matches, $73.9M top-100)
- Guilford NC — tax-delinquent 10.5K × parcels 222K
- Wake NC — daily delinquent × parcels 436K
- Jefferson KY — lien-holder-final-orders × parcels 293K
- Cuyahoga OH — check tax-parcels 527K for delinquency flags (single-file join possible)

**Build recipe:**
1. Join on owner name (normalize: upper, strip punctuation/suffixes) or parcel ID where present.
2. Enrich matches with: assessed total/building/land value, year built, sqft, mailing address, out-of-state flag, deeds/GIS record URL.
3. Score: value desc + out-of-state bonus + repeat-lien bonus.
4. Output standard triple: full CSV / 25-row redacted preview (names → `J*** S***`) / meta JSON → `/opt/leadcurate/processed/{market}/{date}/`.
5. Codex is generalizing this as `scripts/leadcurate/asset_locator.py` (assigned 2026-07-06).

**Compliance framing (NON-NEGOTIABLE, in every artifact):** "post-judgment asset identification and enforcement of existing legal claims." NEVER creditworthiness, eligibility, debtor screening, or anything FCRA-adjacent. No SSNs/DOBs/bank data/phones. Use-restriction clause in terms. Source URL + pull date on every row.

**Market pricing (researched 2026-07-06):** competitors charge PER-DEBTOR — US Asset Records $195 public / $295 certified per report; PI firms $250–400/report; TLOxp/Accurint are subscription-gated. LeadCurate bulk file at $499–1,500 is far below per-match market rate → headroom to charge $1,000–2,500 for a custom book cross-reference. Derrick locks final numbers.

## Lane B — Code Violations / Permits (restoration, facade, masonry, mechanical contractors)

**What it is:** active code-violation or repair-permit buildings, grouped by property, scored by severity + volume + recency → "buildings legally required to hire your trade."

**Data required:** municipal violation feed (or permit feed) with property address + violation type + status/dates. Owner name optional (contractors door-knock/mail).

**Markets ready TODAY:**
- NYC — DONE (`scripts/leadcurate/process_nyc_dob_restoration.py`; 184,181 active / 54,513 buildings). Cut by borough+class for orders.
- Jefferson KY (Louisville) — property-maintenance-violations 17.7K + PVA-ENRICHED version at `raw_imports/jefferson-ky/2026-07-04/property-maintenance-violations-enriched.csv` (Codex built 07-04) — closest to sellable
- Harris TX (Houston) — permits.txt on VPS; the existing "Permit Burnout" investor sample re-markets to contractors as-is

**Build recipe:** filter to ACTIVE/open + relevant classes (hazardous, structural, facade, boiler, work-without-permit) + issued ≤6y → group by building → score = class weight + recency bonus, sum per building → standard triple output. Clone the NYC script and swap the classifier.

**Market pricing (researched 2026-07-06):** Dodge construction leads start $300/user/mo; HBW sells permit-data subscriptions; generic RE leads $20+/lead; usleadlist sells code-violation lists retail. LeadCurate one-time cuts $149–499 and $249/mo borough-subscription are inside market range. Derrick locks final numbers.

## Sales surface pattern (both lanes)

1. Sample page under `docs/sample-deliveries/{market-lane-date}/` — cream/navy/emerald brand ONLY, redacted preview rows (REAL rows from the file — verify every number against the VPS before publishing), compliance box, CTA → intake.
2. Card added to `docs/sample-deliveries/index.html`.
3. Outreach scripts per buyer type → `docs/outreach/` (pattern: `b2b-lanes-2026-07-06.md`).
4. Delivery is EMAIL-ONLY via send-delivery after payment. Never a hosted customer page.
5. Log prospect in dashboard pipeline; post activity to Conference Room.

## Rules that bind here
- Premium voice: never "cheap"/"save"/savings framing.
- Verify every published number against the actual VPS file in-session (verification-discipline rule — inventing table rows from memory happened once and was caught).
- Pricing suggestions only; Derrick decides.
