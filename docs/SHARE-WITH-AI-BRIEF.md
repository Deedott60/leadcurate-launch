# LeadCurate — Shareable Brief

> Paste this entire document into Gemini / ChatGPT / any AI chat to get feedback.
> Last updated: 2026-06-23

---

## What is LeadCurate?

A data service that pulls property records directly from county tax & court sources, scores them for owner motivation, and sells curated motivated-seller lists to real-estate wholesalers, fix-and-flip investors, and buy-and-hold landlords.

Direct competitors: PropStream, BatchLeads, ListSource, DealMachine, PropertyRadar.

Founder: Derrick McDonald. Solo operator, Phase 1 launch.

---

## Current inventory (verified)

- **22 counties pulled** across 11 states
- **14.2M structured records** in the warehouse
- **9 markets** processed into sellable batches ready today
- **13 markets** in processing / cleanup

Active markets ready to sell:
| Market | Records | Lane |
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

---

## The differentiator (vs PropStream/BatchLeads)

PropStream sells static lists — "here's everyone who owes back taxes." Recycled, sold to thousands of wholesalers, records get burned out.

LeadCurate tracks **data velocity and trigger urgency** — when distress is *accelerating*, when an *auction date* is scheduled, when a *fresh filing* hits the court. Same raw data, but scored for *when motivation peaks*, not just *whether it exists*.

We also cap buyer access per county to 1–3 seats so records stay warm.

---

## The 4-Tier Product System

Every record gets classified into one of four tiers based on urgency, scored 0–100.

### Tier 1 — Hot Sheet ($497/week)
- **Trigger:** auction or tax sale scheduled in next 30 days
- **Volume:** 10–100 records weekly
- **Scoring rule:** auction in <14 days → score = 99. auction in <30 days → score = 95.
- **Buyer:** fast-moving wholesalers who can contract this week

### Tier 2 — Fresh Triggers ($297/week)
- **Trigger:** brand-new court filing or code violation in last 7 days
- **Volume:** 50–300 records weekly
- **Scoring rule:** record in current pull AND NOT in prior pull → score = 92, "Fresh Trigger" tag
- **Buyer:** daily cold callers, first-mover advantage

### Tier 3 — Breaking Point ($249 one-time)
- **Trigger:** delinquent balance > 5% of property assessed value, OR debt growing YoY
- **Volume:** 500–2,000 records, monthly refresh
- **Scoring rule:** debt/value ratio > 0.05 → score += 20, "Breaking Point" tag
- **Buyer:** buy-and-hold + flippers wanting highest-conversion subset

### Tier 4 — Curated Distress List ($149 one-time)
- **Trigger:** standard source-based filter (Tax Delinquent, Absentee, Probate, etc.)
- **Volume:** 5K–10K records, monthly refresh
- **Scoring rule:** base score = 50, weighted by debt amount + entity ownership
- **Buyer:** everyone — baseline product, the default starting point

---

## Workflow (today)

1. **Prospect inquiry** — branded intake form at deedott60.github.io/leadcurate-launch/intake/ captures market, list type, urgency, volume, contact
2. **Auto-pipeline** — database trigger auto-creates a prospect record from the intake row
3. **Personalized quote** — operator dashboard has a "Send a quote" tool that builds a per-buyer URL like `/quote-template/?buyer=John&market=Cobb&tier=breakingpoint` — prospect sees one clean offer with a Confirm button
4. **Payment + delivery** — Cash App / Zelle / Stripe → branded XLSX shipped within 24 hours

Automation infrastructure exists (database triggers, conference room for agent coordination, real-time sync) but full end-to-end automation (Twilio SMS, n8n workflows, Stripe webhook → auto-deliver) is Phase 2.

---

## Tech stack (high-level, not for public)

- Cloud database with row-level security for customer data
- Dedicated processing infrastructure for 24/7 data pulls + 9.2 GB raw inventory
- Static frontend hosting for intake form, dashboard, quote template, brand pages
- Tri-agent automation: orchestration agent (strategy), engineering agent (code/security), data-ops agent (24/7 pulls)
- All four tiers run through a unified scoring/classifier module

---

## Pricing positioning

| Competitor | Price | What they sell |
|---|---|---|
| PropStream | $99/mo | Unlimited static lists, shared with thousands |
| BatchLeads | $99/mo | Same as above |
| ListSource | $0.10–0.40/record | Bulk dumps, recycled |
| DealMachine | $99/mo | App-based driving-for-dollars + lists |
| **LeadCurate Tier 4** | $149 one-time | Curated, scored, limited buyers per market |
| **LeadCurate Tier 3** | $249 one-time | Pre-filtered to breaking-point subset |
| **LeadCurate Tier 2** | $297/week | Fresh triggers only, weekly |
| **LeadCurate Tier 1** | $497/week | Auction-imminent hot sheet, weekly |

Justification for premium: time-sensitive data, limited buyer access (records stay warm), pre-scored saves the buyer hours, branded delivery, direct-from-county freshness.

---

## What I want feedback on

Specifically:
1. Is the 4-tier framework defensible vs PropStream's "unlimited for $99" model?
2. Is the pricing right? Too high, too low, or right per tier?
3. Is the quote flow (one offer per prospect, no menu, single Confirm button) the right sales approach for wholesalers?
4. Where would you tighten the message, the product, or the pitch?

---

## The 30-second sales pitch (the one I use)

"We don't just look at how long a property has been on a list — we track its velocity. Someone owing $500 for three years isn't motivated. But our system flags the exact moment that debt hits a breaking point, or when the county officially schedules an auction date. You're not calling someone who's casually behind on taxes — you're calling someone who realizes they're about to lose their house next month. That's why our data closes deals while standard software lists just sit there."

---

## End of brief

Paste the above into Gemini and ask: *"Review this entire business model and give me your honest critique."*
