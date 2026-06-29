# LeadCurate Pricing Audit — For External Review

> Share this with Manus (or any AI) for a pricing audit and second opinion. Self-contained — does NOT require the reader to have the rest of the repo.
>
> **Suggested prompt to paste with this file:**
> "Audit this pricing structure. Tell me: (1) which option captures the most value for the least friction, (2) what's mispriced based on the competitor data shown, (3) what's missing or unclear from a buyer's standpoint, (4) which structure scales cleanly from Phase 1 manual sales to Phase 3 subscriptions. Be direct, no fluff."

---

## 1 — Business overview

**LeadCurate sells curated motivated-seller property data** to real estate wholesalers, fix-and-flippers, and buy-and-hold landlords. The product is filtered, scored, source-attributed county records — NOT raw aggregated dumps.

**Operator:** Derrick McDonald, solo. LeadCurate LLC (NC, Mecklenburg County).
**Stage:** Pre-revenue. Phase 1 of locked plan = first 5–10 paying customers via manual outreach (no subscriptions yet).
**Inventory today:** 22 counties pulled, ~80M raw records, 9 markets ready to sell (8 are Tax-Delinquent lane, 1 is Permit Burnout, 1 is High-Balance Delinquent).
**About to expand:** every sellable market will offer EVERY lane on demand (probate, tax delinquent, code violations, pre-foreclosure, active permits, owner records, high equity, absentee). Build is in progress (Codex handoff issued 2026-06-29).

**Differentiators (locked):**
- Velocity scoring — surface motivation density, not just distress signal
- Capped buyer access — 1–3 seats per market keeps records "warm" (no list shared with the whole city)
- Branded delivery (HTML preview + XLSX + CSV)
- Source-attributed (every row traces back to its county filing)
- Direct competitors: PropStream, BatchLeads, ListSource, DealMachine, PropertyRadar (the "stale aggregator" tier) AND All The Leads, US Lead List, Foreclosures Daily (the "fresh court-scrape" tier)

---

## 2 — Currently locked pricing (CLAUDE.md §3, locked 2026-06-23)

Customer NEVER sees "Tier 1/2/3/4" labels — that's internal. They see ONE recommended tier matched from their intake answers.

| # | Brand name | Price | Cadence | Trigger logic | Buyer fit |
|---|---|---|---|---|---|
| **1** | Imminent Auction Hot Sheet | $397 launch (first 5 buyers) / $497 standard | One-time per sheet | Verified auction date in next 30 days; score forced 95–100 | Fast-moving wholesalers who can contract this week |
| **2** | Fresh Triggers Feed | $197/week launch / $297/week standard | Weekly subscription (the ONLY recurring tier) | New court filing or code violation in last 7 days; score forced 92 | Daily cold callers, first-mover plays |
| **3** | The Breaking Point | $249 one-time (monthly refresh option) | One-time | Debt > 5% of property value OR debt growing YoY (tax OR municipal — HOA/water/code) | Buy-and-hold + flippers wanting highest-conversion subset |
| **4** | Curated Distress List | $99 first 5 buyers / $149 standard (monthly refresh option) | One-time | Standard source filter (Tax Delinquent, Absentee, Probate, High Equity) | Everyone — foundational entry product |

**Brand voice constraints (locked, do not violate):**
- Premium positioning. PropStream is the cheap recycled-list option; LeadCurate is the curated/scored/limited-access alternative.
- BANNED words in customer-facing copy: cheap, cheaper, affordable, save, savings, less you pay, starting at just, value pricing, you'll spend less.
- Frame around fit, quality, accuracy, freshness, urgency, exclusivity.
- Never apologize for price.

---

## 3 — New strategic capability (in build now)

> Today, our 9 sellable markets are mostly single-lane (Tax Delinquent). Within the next 1–2 weeks every sellable market will offer EVERY lane available, scraped + scored + delivered together.

**The 8 lanes per market:**
1. Tax Delinquent
2. Probate (court records — heir contact info, before MLS listing)
3. Code Violations (city/county code enforcement portals)
4. Pre-Foreclosure / NOD (county recorder filings)
5. Active Permits (renovation distress — permit pulled but stalled)
6. Owner Records (active homeowner data, county assessor)
7. High Equity (computed — debt low relative to property value)
8. Absentee (owner mailing address ≠ property address)

**Implication:** instead of selling "one lane in one market," we can now sell "all distress signals in one market, scored together." That's a meaningfully different product.

---

## 4 — Competitor data (verified directionally)

### Tier A — Premium "court-scrape" competitors (direct peers)

| Company | Price | Structure |
|---|---|---|
| **US Lead List** (Inheritance) | ~$400 / 250 inherited leads ($1.60/lead) | Hard cap 3 investors/county |
| **All The Leads** (Probate) | $249–$1,099+/month | Population-tiered subscription; updates every 30 days |
| **Foreclosures Daily / Probates Daily** | $150–$600+/month | 3/6/12-month commitments; daily or weekly court harvest |
| **Indie local scrapers** (forums) | $150 (Basic) – $300 (Pro) per month | Single region, single lane usually |

### Tier B — Bulk "stale" aggregators (NOT our category)

| Company | Price | Why we don't compete |
|---|---|---|
| **PropStream / BatchLeads** | $97–$297+/month | Up to 10K pulls/month BUT 30–90 days lag behind county filings; every wholesaler in the city has the same list |

**Market floor for "fresh court-scrape premium tier" = $150/month.**
**Market ceiling for non-enterprise single-county product ≈ $1,000/month exclusive.**
**Premium tier per-lead price range = $0.50 – $1.60.**

---

## 5 — Three pricing structures to audit

### Option A — Keep locked 4-tier, add multi-lane bundling (lowest risk)

Keep the existing 4 tiers exactly as locked. Add a NEW SKU:

- **All-Lanes Bundle (single market):** $397 one-time / $597 with monthly refresh
  - Customer gets ALL 8 lanes for one market, scored together, deduplicated
  - Sits between Tier 3 ($249) and Tier 1 ($497) — single-market, all-source
  - Slot replaces or augments Tier 3 ("The Breaking Point") which is debt-only

**Pros:** preserves locked brand names + tier picker; only one new SKU; tested first sales price ($99–$149 Tier 4) stays intact.
**Cons:** still 5 SKUs; doesn't fully reflect the "every lane available" capability in the framing.

### Option B — Three subscription tiers (Gemini direction; matches court-scrape competitor norm)

| Tier | Price | What's included | Buyer |
|---|---|---|---|
| **Single-Category Feed** | $150/month | One lane, one county, weekly drop | Niche operator (e.g. "I only buy probate") |
| **Multi-Lane Metro** | $500/month | ALL 8 lanes, one major metro, weekly | Active acquisitions team |
| **Exclusive Territory** | $1,000/month | ALL lanes, one metro, capped to 1 buyer (or 3 max), daily refresh | Enterprise wholesaler / fund |

**Pros:** matches competitor floor + ceiling; recurring revenue from day one; clean three-bucket comparison; full new capability reflected.
**Cons:** conflicts with locked Phase 1 = "one-time sales only" rule; requires subscription billing infra (Phase 3); harder first close (commit to month vs. one drop).

### Option C — Modular: pick markets + pick lanes (most flexible, most complex)

Pricing formula: **Base($X) + per-market($Y) + per-lane($Z) + exclusivity multiplier(1.0x / 2.0x / 5.0x)**

Example: 1 market × 4 lanes × shared access = $50 + $100 + (4 × $40) × 1.0 = **$310 one-time**
Example: 1 market × 8 lanes × exclusive = $50 + $100 + (8 × $40) × 5.0 = **$2,350/month**

**Pros:** captures the most value; customer pays for exactly what they use; the same engine handles single-lane entry buyers and exclusive enterprise.
**Cons:** intake gets harder (need a configurator); harder to talk about in ads; risk of "calculator pricing" feeling un-premium.

---

## 6 — Constraints and considerations

- **Phase 1 (today–first 5 sales) = manual one-time sales only.** Subscription billing not set up. Cash App / Zelle / Stripe TBD.
- **Phase 3 (after 5 customers + ops hub built) = subscriptions OK.**
- **Capped buyer access** is a real differentiator we want priced in. Specific cap pattern from US Lead List (3 investors max per county) is industry-validated.
- **Branding/voice:** premium tone is locked. No "cheap" language ever.
- **Brand currently has 0 customers.** First sale credibility is fragile — selling a $1,000/mo subscription cold is harder than selling a $149 one-time list.
- **9 markets ready, ~80M records pulled, capacity to expand to any US county on demand.**

---

## 7 — Specific questions for the auditor

1. **Floor pricing:** is $99–$149 Tier 4 (entry) defensible against the $150/mo competitor floor, or are we leaving money on the table by anchoring below it? Should the entry price LEAD with $149 instead of $99?
2. **Bundle pricing:** if all 8 lanes per market is now real, what's the right "all-lanes single-market one-time" number? Gut check: $397? $497? $697? Higher?
3. **Subscription readiness:** at Phase 1 (0 customers), is it better to (a) sell one-time only, (b) sell one-time + offer optional monthly refresh add-on, or (c) push straight to monthly subscription like All The Leads does?
4. **Exclusivity premium:** what multiplier on top of standard price for "1-buyer exclusive territory"? 2x? 3x? 5x?
5. **Tier picker vs. modular:** does the locked "operator picks ONE tier from intake answers and customer sees ONE offer" model survive when we add multi-lane bundles, or does it collapse and we need a configurator?
6. **Stage gating:** which structure can start TODAY for manual sales AND survive the transition to Phase 3 subscriptions without rebrand confusion?
7. **Naming:** "Tier 1/2/3/4" + brand names (Imminent Auction Hot Sheet / Fresh Triggers Feed / The Breaking Point / Curated Distress List) — do these still work if the product is now "all lanes one market"?
8. **Anything missing?** What pricing pattern from the competitor set is NOT captured in any of the three options above?

---

## 8 — Decision framework (what a good answer looks like)

The audit should converge on:
- ONE recommended structure (A, B, C, or a hybrid)
- Specific dollar numbers for each SKU
- A migration path from Phase 1 (manual one-time) → Phase 3 (subscriptions) without scrapping brand names
- Specific call-outs of what to test in the first 5 sales (one price hypothesis to validate)
