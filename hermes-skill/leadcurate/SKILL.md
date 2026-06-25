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

- **Colors:** emerald #15803d (primary) · emerald-dark #14532d · emerald-light #22c55e · cream #faf7f2 (background) · cream-2 #f3eddf · dark #0f172a (text) · slate #475569 (secondary text) · line #e2dccf (borders)
- **Accent colors per tier:** crimson #991b1b (Tier 1 Hot Sheet) · gold #b45309 (Tier 2 Fresh Triggers) · emerald (Tier 3 Breaking Point) · blue #1d4ed8 (Tier 4 Curated)
- **Fonts:** Inter 400/500/600/700 (body) · Playfair Display 600/700 (display/headings)
- **Border-radius:** 16-22px for cards · 8-10px for inputs/buttons · 999px for pills
- **Type sizing:** h1 `clamp(32px,5vw,46px)` · h2 `clamp(24px,3vw,32px)` · body 16-18px

## Reference files (READ THESE before building any LeadCurate artifact)

When asked to build/edit/style anything LeadCurate, fetch these files from the repo (https://github.com/Deedott60/leadcurate-launch/) and match the patterns exactly. Never invent a new visual system.

| If you're building... | Read this file as reference |
|---|---|
| Intake form / sign-up form | `docs/intake/index.html` — fieldsets, pill multi-select, "why we ask" notes per section |
| Quote / pricing page | `docs/quote-template/index.html` — single tier per page, URL params, single Confirm button |
| Customer-facing packages overview | `docs/packages/index.html` — 4 tier cards, NO pricing, audit-style |
| Internal tier reference | `docs/tiers/index.html` — has pricing, scoring rules, decision matrix |
| Analytical audit / data report | `docs/system-audit/index.html`, `docs/property-numbers/index.html` — headline metrics, bar charts, heat-shaded distribution, ranked tables |
| Branded delivery report | `docs/customer-deliveries/` folder — multi-tab structure |
| Email template / outreach message | `docs/OUTREACH-PLAYBOOK.md` |
| Dashboard / operator UI | `docs/command/index.html` — sidebar nav, card system |

## Component patterns (always use these — never reinvent)

- **Card:** white bg, `border:1px solid #e2dccf`, `border-radius:16-22px`, `padding:24-32px`, optional `border-left:4px solid <tier-color>`
- **Tier tag pill:** font-size 11px, letter-spacing 0.12em, uppercase, padding 5px 12px, border-radius 999px, color matches tier
- **Headline metric block:** dark bg #0f172a, emerald-2 #22c55e label, white value in Playfair, gray-400 #94a3b8 note
- **Bar chart row:** 130-170px label / 1fr bar track / 90px value, bar fill emerald with hot/cool variants (gold/light-green)
- **Pitch quote box:** dark bg, italic white text, key phrases in non-italic white strong
- **CTA button (primary):** emerald bg, white text, padding 16px 32px, border-radius 999px, font-weight 700

## Voice + tone patterns

- **Lede paragraph:** confident, factual, premium. No exclamations.
- **Section eyebrows:** 11-12px uppercase, letter-spacing 0.12-0.18em, emerald color
- **Numbers:** always verified, never rounded ambiguously. "10,472" not "10K+". "Varies by market" never "small list."
- **CTA copy:** action verb + outcome. "Get a custom quote →" not "Click here." "Confirm selection →" not "Submit."
- **Trust line at footer:** what they get, what they don't get (no spam, no newsletter), no apology for price.

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
