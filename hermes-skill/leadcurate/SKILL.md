---
name: leadcurate
description: Current state of the LeadCurate business. Read first whenever any task mentions LeadCurate, intake form, quotes, audits, tiers, county data, wholesaling, REI lead lists, or motivated seller data.
metadata:
  type: project
  version: 2026-06-25
  owner: Derrick McDonald (dmcdonald5649@gmail.com)
---

# LeadCurate — Current State (2026-06-25)

## What it is

LeadCurate sells curated motivated-seller property data to real-estate wholesalers, flippers, and buy-and-hold investors. The product is filtered/scored county records — not raw dumps like PropStream. Differentiator is **velocity scoring** (when motivation peaks) plus **capped buyer access per market** so records stay warm.

Founder/Operator: Derrick McDonald (NOT Daniel, NOT Derek). Solo. Phase 1 launch.

## Current inventory (verified 2026-06-25)

**~80 million raw records on VPS** across 22 counties in 12 states. Sellable today:

| Market | Records ready | Lane |
|---|---|---|
| Wake NC (Raleigh) | 10,472 | Tax Delinquent |
| Cobb GA (Atlanta NW) | 5,678 | Tax Delinquent |
| Guilford NC (Greensboro) | 5,000 | Tax Delinquent |
| Marion IN (Indianapolis) | 5,000 | Tax Delinquent |
| DeKalb GA (Atlanta E) | 5,000 | Tax Delinquent |
| Forsyth NC (Winston-Salem) | 5,000 | Tax Delinquent |
| Fulton GA (Atlanta) | 5,000 | Owner Records |
| Harris TX (Houston) | 1,500 | Active Permit Burnout |
| Jefferson AL (Birmingham) | 21 | High-Balance Delinquent |

13 more markets in raw form, processing pending.

## The 4-Tier Product System (LOCKED 2026-06-23)

Every record gets classified into one of four tiers. Customer NEVER sees "Tier 1/2/3/4" labels — that's internal. They see the tier name and feel the urgency.

### Tier 1 — Imminent Auction Hot Sheet
- **Price:** $397 launch (first 5 buyers) → $497 standard
- **Cadence:** One-time per sheet (NOT subscription — auctions are episodic)
- **Trigger:** verified auction date in next 30 days, score forced 95-100
- **Buyer:** fast-moving wholesalers who can contract this week

### Tier 2 — Fresh Triggers Feed
- **Price:** $197/week launch → $297/week standard
- **Cadence:** Weekly subscription (the ONLY recurring tier)
- **Trigger:** new court filing or code violation in last 7 days, score forced 92
- **Buyer:** daily cold callers, first-mover advantage

### Tier 3 — The Breaking Point
- **Price:** $249 one-time
- **Cadence:** one-time with monthly refresh option
- **Trigger:** debt > 5% of property value OR debt growing YoY (tax OR municipal — HOA, water, code)
- **Buyer:** buy-and-hold + flippers wanting highest-conversion subset

### Tier 4 — Curated Distress List
- **Price:** $99 first 5 buyers → $149 standard
- **Cadence:** one-time with monthly refresh option
- **Trigger:** standard source filter (Tax Delinquent, Absentee, Probate, High Equity)
- **Buyer:** everyone — the foundational entry product

## Customer-facing pages

| Page | URL | What it is |
|---|---|---|
| Intake form | https://deedott60.github.io/leadcurate-launch/intake/ | Public, anyone can fill out |
| Packages overview | https://deedott60.github.io/leadcurate-launch/packages/ | Send after intake, NO pricing visible |
| Personalized quote | https://deedott60.github.io/leadcurate-launch/quote-template/?buyer=X&market=Y&tier=Z | Built per-prospect, single Confirm button |
| Tier reference | https://deedott60.github.io/leadcurate-launch/tiers/ | INTERNAL ONLY — operator reference |

## Brand voice rules (LOCKED — NEVER violate)

**Premium positioning.** PropStream is the cheap recycled-list option. LeadCurate is the curated, scored, limited-access alternative.

### BANNED in customer-facing copy:
- "cheap" / "cheaper" / "affordable"
- "save" / "savings" / "save money"
- "less you pay" / "won't pay for"
- "starting at just $X"
- Any "value pricing" framing
- Any "you'll spend less" angle

### USE INSTEAD:
- Frame around *fit, quality, accuracy, freshness, urgency, exclusivity*
- Customer should feel matched to the *right* tier, not the *cheapest* option
- Never apologize for price

### Examples:
- ❌ "the less you pay for stuff you won't use"
- ✅ "the sharper we can match you to the tier that fits"
- ❌ "starting at just $149"
- ✅ "entry tier: $149 — built for your first list"

## Visual brand kit

- **Colors:** emerald #15803d (primary) · cream #faf7f2 (background) · dark #0f172a (text)
- **Accent colors per tier:** crimson #991b1b (Tier 1) · gold #b45309 (Tier 2) · emerald (Tier 3) · blue #1d4ed8 (Tier 4)
- **Fonts:** Inter (body) · Playfair Display (display/headings)
- **Style references:** /docs/tiers/, /docs/packages/, /docs/quote-template/, /docs/system-audit/ — all use the same component system

## Customer flow (current, 2026-06-25)

1. Prospect fills intake form → submission to dmcdonald5649@gmail.com (will be domain email soon) + Supabase auto-creates prospect record
2. Derrick (or Hermes/Codex when fully wired) reviews intake, picks the right tier, builds a personalized quote URL
3. Sends URL to prospect — they see ONE clean offer with Confirm button
4. Prospect confirms with name + phone → email to Derrick
5. Derrick sends payment instructions (Cash App / Zelle / Stripe)
6. After payment → branded XLSX delivered within 24 hours

## Agents and roles

- **Claude (orchestrator):** strategy, code edits, dashboard updates, brand decisions, quote logic. Working in C:\Users\lenovo\Documents\Leadcurate\leadcurate-launch on Derrick's machine
- **Codex:** VPS infrastructure, Supabase security, scraping infrastructure, data pipeline plumbing. Codex receives tasks via /docs/codex-handoff-*.md files in the repo
- **Hermes (Danny, on VPS):** 24/7 ops — runs scrapers, monitors Conference Room, executes tasks posted to activity_feed targeting hermes
- **Derrick:** business decisions, pricing, sales, customer relationships

## Conference Room protocol

To talk to other agents, INSERT into `activity_feed`:
```sql
INSERT INTO activity_feed (event_type, source, title, body, target)
VALUES ('conf:role', 'hermes', '<task title>', '<task body>', '<target agent>');
```

Targets: `claude`, `codex`, `hermes`, `derrick`, `all`

Event types: `conf:role` (task), `conf:done` (completion), `conf:status` (progress), `conf:blocker` (need help)

## What Hermes specifically helps with for LeadCurate

When Derrick or another agent asks Hermes for help:
1. Pulling fresh data from a county source — there's a working catalog in /opt/leadcurate/scripts/ and a leadcurate-county-data-pull skill
2. Running snapshot processors — pattern: process raw → normalize → score → tier-classify → write CSV + meta.json
3. Running the tier classifier on a market: `python3 /opt/leadcurate/scripts/tier_classifier.py <snapshot.csv>`
4. Watching for new intake submissions and pinging Claude with priority info
5. Building branded delivery XLSX packages for paid orders

## Don't do these things

- Never insert test data into prospects, leads, intake_requests, messages tables
- Never touch the landing page `/site/` without Derrick's approval
- Never change pricing or make business decisions — that's Derrick's call
- Never use "Daniel" or "Derek" — his name is Derrick (D-E-R-R-I-C-K)
- Never apologize for price in customer copy
- Never tell Derrick a system is "broken" without SSH-verifying current state first

## Stale info to overwrite

If you have older context that says any of these — they are WRONG:
- "Hermes brain offline" — VERIFIED WORKING with OpenAI + Gemini keys set, brain v0.15.1
- "14.2M records total" — actual count is ~80M raw records as of 2026-06-25
- "Tier prices are $297/$497/week subscriptions" — restructured 2026-06-23, see 4-tier section above
- "Quote uses A/B/C menu" — replaced with one-tier-per-quote, single Confirm
- "Customer chooses tier" — operator decides based on intake answers, customer sees one recommendation
